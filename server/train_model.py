#!/usr/bin/env python3
"""
Enhanced AI Model Training Script
Supports fine-tuning of multiple LLM architectures on various datasets
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, AutoConfig,
    Trainer, TrainingArguments, DataCollatorForLanguageModeling,
    EarlyStoppingCallback, get_linear_schedule_with_warmup
)
from datasets import load_dataset, Dataset, concatenate_datasets
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
import bitsandbytes as bnb
import psutil
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor system resources during training"""
    
    def __init__(self, max_memory_percent=85, max_gpu_memory_percent=90):
        self.max_memory_percent = max_memory_percent
        self.max_gpu_memory_percent = max_gpu_memory_percent
    
    def check_resources(self) -> bool:
        """Check if resources are available for training"""
        # Check CPU memory
        memory = psutil.virtual_memory()
        if memory.percent > self.max_memory_percent:
            logger.warning(f"Memory usage too high: {memory.percent}%")
            return False
        
        # Check GPU memory if available
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_memory = torch.cuda.memory_allocated(i) / torch.cuda.max_memory_allocated(i) * 100
                if gpu_memory > self.max_gpu_memory_percent:
                    logger.warning(f"GPU {i} memory usage too high: {gpu_memory:.1f}%")
                    return False
        
        return True
    
    def log_resource_usage(self):
        """Log current resource usage"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        log_msg = f"Resources - CPU: {cpu_percent}%, RAM: {memory.percent}%"
        
        if torch.cuda.is_available():
            gpu_info = []
            for i in range(torch.cuda.device_count()):
                gpu_mem_used = torch.cuda.memory_allocated(i) / 1024**3
                gpu_mem_total = torch.cuda.max_memory_allocated(i) / 1024**3
                gpu_util = torch.cuda.utilization(i) if hasattr(torch.cuda, 'utilization') else 0
                gpu_info.append(f"GPU{i}: {gpu_util}%, {gpu_mem_used:.1f}/{gpu_mem_total:.1f}GB")
            log_msg += f", {', '.join(gpu_info)}"
        
        logger.info(log_msg)

class DatasetManager:
    """Manage training datasets for different tasks"""
    
    DATASET_CONFIGS = {
        'alpaca': {
            'name': 'tatsu-lab/alpaca',
            'text_column': 'text',
            'format_func': 'format_alpaca'
        },
        'dolly': {
            'name': 'databricks/databricks-dolly-15k',
            'text_column': 'text',
            'format_func': 'format_dolly'
        },
        'oasst1': {
            'name': 'OpenAssistant/oasst1',
            'text_column': 'text',
            'format_func': 'format_oasst1'
        },
        'code_alpaca': {
            'name': 'lucasmccabe-lmi/CodeAlpaca-20k',
            'text_column': 'text',
            'format_func': 'format_code_alpaca'
        },
        'math_qa': {
            'name': 'math_qa',
            'text_column': 'text',
            'format_func': 'format_math_qa'
        },
        'gsm8k': {
            'name': 'gsm8k',
            'subset': 'main',
            'text_column': 'text',
            'format_func': 'format_gsm8k'
        }
    }
    
    @staticmethod
    def format_alpaca(example):
        """Format Alpaca dataset example"""
        if example.get('input', '').strip():
            return f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
        else:
            return f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"
    
    @staticmethod
    def format_dolly(example):
        """Format Dolly dataset example"""
        context = f"\n\nContext: {example['context']}" if example.get('context') else ""
        return f"### Instruction:\n{example['instruction']}{context}\n\n### Response:\n{example['response']}"
    
    @staticmethod
    def format_oasst1(example):
        """Format OASST1 dataset example"""
        return f"### Human:\n{example.get('text', '')}\n\n### Assistant:\n{example.get('response', '')}"
    
    @staticmethod
    def format_code_alpaca(example):
        """Format Code Alpaca dataset example"""
        return f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example.get('input', '')}\n\n### Response:\n{example['output']}"
    
    @staticmethod
    def format_math_qa(example):
        """Format Math QA dataset example"""
        return f"### Question:\n{example['Problem']}\n\n### Answer:\n{example['Rationale']} {example['correct']}"
    
    @staticmethod
    def format_gsm8k(example):
        """Format GSM8K dataset example"""
        return f"### Problem:\n{example['question']}\n\n### Solution:\n{example['answer']}"
    
    def load_dataset_by_name(self, dataset_name: str, max_samples: int = 10000) -> Dataset:
        """Load and format dataset by name"""
        if dataset_name not in self.DATASET_CONFIGS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        config = self.DATASET_CONFIGS[dataset_name]
        logger.info(f"Loading dataset: {dataset_name}")
        
        try:
            if 'subset' in config:
                dataset = load_dataset(config['name'], config['subset'], split='train')
            else:
                dataset = load_dataset(config['name'], split='train')
            
            # Limit dataset size
            if len(dataset) > max_samples:
                dataset = dataset.select(range(max_samples))
            
            # Format the dataset
            format_func = getattr(self, config['format_func'])
            dataset = dataset.map(lambda x: {'text': format_func(x)})
            
            logger.info(f"Loaded {len(dataset)} samples from {dataset_name}")
            return dataset
        
        except Exception as e:
            logger.error(f"Failed to load dataset {dataset_name}: {e}")
            # Return a dummy dataset to continue training
            return Dataset.from_dict({'text': [f"### Instruction:\nSample training text for {dataset_name}\n\n### Response:\nThis is a placeholder response."]})

class ModelTrainer:
    """Enhanced model trainer with LoRA fine-tuning and resource management"""
    
    def __init__(self, model_name: str, output_dir: str, max_length: int = 2048):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_length = max_length
        self.resource_monitor = ResourceMonitor()
        self.dataset_manager = DatasetManager()
        
        # Initialize model and tokenizer
        self._load_model_and_tokenizer()
    
    def _load_model_and_tokenizer(self):
        """Load model and tokenizer with appropriate configurations"""
        logger.info(f"Loading model: {self.model_name}")
        
        try:
            # Map Ollama model names to HuggingFace models (using open models)
            model_mapping = {
                "llama2:latest": "huggyllama/llama-7b",
                "llama2:7b": "huggyllama/llama-7b", 
                "llama2:13b": "huggyllama/llama-13b",
                "mistral:latest": "mistralai/Mistral-7B-v0.1",
                "mistral:7b": "mistralai/Mistral-7B-v0.1",
                "gemma:2b": "microsoft/DialoGPT-small",  # Fallback for now
                "gemma:7b": "microsoft/DialoGPT-medium",
                "phi:latest": "microsoft/DialoGPT-small",
                "codellama:latest": "microsoft/DialoGPT-small",  # Fallback for code
                "codellama:7b": "microsoft/DialoGPT-small",
                "codellama:13b": "microsoft/DialoGPT-medium"
            }
            
            # Use mapped model or fallback to a working model
            hf_model_name = model_mapping.get(self.model_name, "microsoft/DialoGPT-small")
            logger.info(f"Using HuggingFace model: {hf_model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                hf_model_name,
                trust_remote_code=True,
                padding_side="right"
            )
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Configure model loading based on available resources
            device_map = "auto" if torch.cuda.is_available() else None
            
            # Use 4-bit quantization for large models to save memory
            use_4bit = torch.cuda.is_available() and self._should_use_quantization()
            
            if use_4bit:
                from transformers import BitsAndBytesConfig
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    hf_model_name,
                    quantization_config=bnb_config,
                    device_map=device_map,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    hf_model_name,
                    device_map=device_map,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
            
            # Prepare model for training
            if use_4bit:
                self.model = prepare_model_for_kbit_training(self.model)
            
            # Configure LoRA
            self._setup_lora()
            
            logger.info(f"Model loaded successfully. Parameters: {self.model.num_parameters():,}")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
    
    def _should_use_quantization(self) -> bool:
        """Determine if 4-bit quantization should be used based on model size"""
        # For CPU-only training, disable quantization
        if not torch.cuda.is_available():
            return False
            
        # Use quantization for larger models
        large_models = ["llama2:13b", "llama2:70b", "codellama:13b", "mixtral:8x7b"]
        return self.model_name in large_models
    
    def _setup_lora(self):
        """Setup LoRA configuration for efficient fine-tuning"""
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # Rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            bias="none",
        )
        
        self.model = get_peft_model(self.model, lora_config)
        logger.info(f"LoRA setup complete. Trainable parameters: {self.model.num_parameters():,}")
    
    def prepare_dataset(self, dataset_name: str, max_samples: int = 10000) -> DataLoader:
        """Prepare dataset for training"""
        logger.info(f"Preparing dataset: {dataset_name}")
        
        # Load dataset
        dataset = self.dataset_manager.load_dataset_by_name(dataset_name, max_samples)
        
        # Tokenize dataset
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples['text'],
                truncation=True,
                padding=False,
                max_length=self.max_length,
                return_tensors=None
            )
            tokenized['labels'] = tokenized['input_ids'].copy()
            return tokenized
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset
    
    def train(self, dataset_name: str, max_steps: int = 1000, save_steps: int = 250,
              eval_steps: int = 500, logging_steps: int = 50, learning_rate: float = 2e-4):
        """Train the model with specified parameters"""
        logger.info(f"Starting training: {self.model_name} on {dataset_name}")
        
        # Check initial resources
        if not self.resource_monitor.check_resources():
            logger.error("Insufficient resources to start training")
            return False
        
        try:
            # Prepare dataset
            train_dataset = self.prepare_dataset(dataset_name)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.output_dir),
                overwrite_output_dir=True,
                num_train_epochs=1,
                max_steps=max_steps,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=4,
                learning_rate=learning_rate,
                lr_scheduler_type="cosine",
                warmup_steps=50,
                logging_steps=logging_steps,
                save_steps=save_steps,
                eval_steps=eval_steps,
                save_total_limit=3,
                fp16=torch.cuda.is_available(),
                dataloader_pin_memory=False,
                remove_unused_columns=False,
                report_to=None,  # Disable wandb/tensorboard
                load_best_model_at_end=False,
                metric_for_best_model="loss",
                greater_is_better=False,
            )
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,
            )
            
            # Create trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                data_collator=data_collator,
                tokenizer=self.tokenizer,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # Start training
            start_time = time.time()
            logger.info("Training started...")
            
            # Log initial resource usage
            self.resource_monitor.log_resource_usage()
            
            trainer.train()
            
            # Save final model
            trainer.save_model()
            self.tokenizer.save_pretrained(self.output_dir)
            
            training_time = time.time() - start_time
            logger.info(f"Training completed in {training_time:.2f} seconds")
            
            # Log final resource usage
            self.resource_monitor.log_resource_usage()
            
            # Save training metadata
            metadata = {
                'model_name': self.model_name,
                'dataset': dataset_name,
                'training_time': training_time,
                'max_steps': max_steps,
                'final_step': trainer.state.global_step,
                'final_loss': trainer.state.log_history[-1].get('train_loss', 0) if trainer.state.log_history else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.output_dir / 'training_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
        
        finally:
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

def main():
    parser = argparse.ArgumentParser(description='Train LLM models on various datasets')
    parser.add_argument('--model', required=True, help='Model name or path')
    parser.add_argument('--dataset', required=True, help='Dataset name')
    parser.add_argument('--output_dir', required=True, help='Output directory for trained model')
    parser.add_argument('--max_steps', type=int, default=1000, help='Maximum training steps')
    parser.add_argument('--save_steps', type=int, default=250, help='Save model every N steps')
    parser.add_argument('--eval_steps', type=int, default=500, help='Evaluate every N steps')
    parser.add_argument('--logging_steps', type=int, default=50, help='Log every N steps')
    parser.add_argument('--learning_rate', type=float, default=2e-4, help='Learning rate')
    parser.add_argument('--max_length', type=int, default=2048, help='Maximum sequence length')
    parser.add_argument('--max_samples', type=int, default=10000, help='Maximum dataset samples')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = ModelTrainer(
        model_name=args.model,
        output_dir=args.output_dir,
        max_length=args.max_length
    )
    
    # Start training
    success = trainer.train(
        dataset_name=args.dataset,
        max_steps=args.max_steps,
        save_steps=args.save_steps,
        eval_steps=args.eval_steps,
        logging_steps=args.logging_steps,
        learning_rate=args.learning_rate
    )
    
    if success:
        logger.info("Training completed successfully")
        sys.exit(0)
    else:
        logger.error("Training failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 