#!/usr/bin/env python3
"""
FastAPI Server for AI Training Management and Monitoring
Provides REST API endpoints for training control and system monitoring
"""

import asyncio
import json
import logging
import os
import psutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_DIR = Path(os.environ.get('PROJECT_DIR', os.path.expanduser('~/faith-server')))
LOGS_DIR = PROJECT_DIR / 'logs'
MODELS_DIR = PROJECT_DIR / 'models'
OLLAMA_URL = "http://localhost:11434"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(
    title="AI Training Server",
    description="24/7 AI Model Training and Management API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TrainingRequest(BaseModel):
    model_name: str
    dataset: str
    max_steps: int = 1000
    learning_rate: float = 2e-4
    save_steps: int = 250

class SystemMetrics(BaseModel):
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    gpu_metrics: Optional[List[Dict[str, Any]]] = None
    active_processes: int
    uptime_hours: float

class TrainingJob(BaseModel):
    id: str
    model_name: str
    dataset: str
    status: str  # running, completed, failed, queued
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress: float = 0.0
    current_step: int = 0
    max_steps: int = 1000
    loss: Optional[float] = None
    output_dir: Optional[str] = None

class ServerStatus(BaseModel):
    status: str  # running, stopped, error
    uptime_seconds: float
    active_training_jobs: int
    total_completed_jobs: int
    total_failed_jobs: int
    available_models: int
    system_health: str  # healthy, warning, critical

# Global state
training_jobs: Dict[str, TrainingJob] = {}
server_start_time = time.time()
job_counter = 0

# Utility functions
def get_gpu_metrics() -> List[Dict[str, Any]]:
    """Get GPU metrics if available"""
    try:
        import torch
        if not torch.cuda.is_available():
            return []
        
        gpu_metrics = []
        for i in range(torch.cuda.device_count()):
            try:
                props = torch.cuda.get_device_properties(i)
                memory_used = torch.cuda.memory_allocated(i)
                memory_total = torch.cuda.max_memory_allocated(i)
                
                gpu_metrics.append({
                    "gpu_id": i,
                    "name": props.name,
                    "memory_used_gb": memory_used / 1024**3,
                    "memory_total_gb": memory_total / 1024**3,
                    "memory_percent": (memory_used / memory_total * 100) if memory_total > 0 else 0,
                    "temperature": None,  # Would need nvidia-ml-py for this
                    "utilization": None   # Would need nvidia-ml-py for this
                })
            except Exception as e:
                logger.warning(f"Could not get metrics for GPU {i}: {e}")
        
        return gpu_metrics
    except ImportError:
        return []

def get_system_metrics() -> SystemMetrics:
    """Get current system metrics"""
    # CPU and memory
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Disk usage
    disk_usage = psutil.disk_usage(str(PROJECT_DIR))
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    
    # GPU metrics
    gpu_metrics = get_gpu_metrics()
    
    # Active processes
    active_processes = len([p for p in psutil.process_iter() if p.is_running()])
    
    # Uptime
    uptime_hours = (time.time() - server_start_time) / 3600
    
    return SystemMetrics(
        timestamp=datetime.now().isoformat(),
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        disk_usage_percent=disk_percent,
        gpu_metrics=gpu_metrics,
        active_processes=active_processes,
        uptime_hours=uptime_hours
    )

def check_ollama_status() -> bool:
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/version", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_models() -> List[str]:
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except:
        return []

def generate_job_id() -> str:
    """Generate unique job ID"""
    global job_counter
    job_counter += 1
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{job_counter:03d}"

async def run_training_job(job_id: str, request: TrainingRequest):
    """Run training job in background"""
    job = training_jobs[job_id]
    job.status = "running"
    job.start_time = datetime.now().isoformat()
    
    # Create output directory
    output_dir = MODELS_DIR / f"{job_id}_{request.model_name.replace(':', '_')}_{request.dataset}"
    output_dir.mkdir(parents=True, exist_ok=True)
    job.output_dir = str(output_dir)
    
    try:
        # Prepare production training command
        cmd = [
            "python", str(PROJECT_DIR / "server" / "train_model.py"),
            "--model", request.model_name,
            "--dataset", request.dataset,
            "--output_dir", str(output_dir),
            "--max_steps", str(request.max_steps),
            "--save_steps", str(request.save_steps),
            "--learning_rate", str(request.learning_rate)
        ]
        
        # Run training
        logger.info(f"Starting training job {job_id}: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJECT_DIR)
        )
        
        # Monitor progress
        log_file = LOGS_DIR / f"training_{job_id}.log"
        with open(log_file, 'w') as f:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode().strip()
                f.write(line_str + '\n')
                f.flush()
                
                # Parse progress from logs
                if "step" in line_str.lower() and "/" in line_str:
                    try:
                        # Extract step information
                        parts = line_str.split()
                        for i, part in enumerate(parts):
                            if part.lower().startswith("step") and i + 1 < len(parts):
                                step_info = parts[i + 1]
                                if "/" in step_info:
                                    current, total = step_info.split("/")
                                    job.current_step = int(current)
                                    job.progress = (int(current) / int(total)) * 100
                                    break
                    except:
                        pass
                
                # Extract loss if available
                if "loss" in line_str.lower():
                    try:
                        import re
                        loss_match = re.search(r'loss[:\s]+([0-9.]+)', line_str.lower())
                        if loss_match:
                            job.loss = float(loss_match.group(1))
                    except:
                        pass
        
        # Wait for completion
        await process.wait()
        
        if process.returncode == 0:
            job.status = "completed"
            job.progress = 100.0
            logger.info(f"Training job {job_id} completed successfully")
        else:
            job.status = "failed"
            logger.error(f"Training job {job_id} failed with return code {process.returncode}")
    
    except Exception as e:
        job.status = "failed"
        logger.error(f"Training job {job_id} failed with exception: {e}")
    
    finally:
        job.end_time = datetime.now().isoformat()

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Training Server", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    metrics = get_system_metrics()
    ollama_running = check_ollama_status()
    
    # Determine health status
    health_status = "healthy"
    if metrics.cpu_percent > 90 or metrics.memory_percent > 90:
        health_status = "warning"
    if metrics.disk_usage_percent > 95 or not ollama_running:
        health_status = "critical"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "health": health_status,
        "ollama_running": ollama_running,
        "system_metrics": metrics
    }

@app.get("/status", response_model=ServerStatus)
async def get_server_status():
    """Get server status"""
    uptime = time.time() - server_start_time
    active_jobs = len([j for j in training_jobs.values() if j.status == "running"])
    completed_jobs = len([j for j in training_jobs.values() if j.status == "completed"])
    failed_jobs = len([j for j in training_jobs.values() if j.status == "failed"])
    
    metrics = get_system_metrics()
    health = "healthy"
    if metrics.cpu_percent > 90 or metrics.memory_percent > 90:
        health = "warning"
    if metrics.disk_usage_percent > 95:
        health = "critical"
    
    return ServerStatus(
        status="running",
        uptime_seconds=uptime,
        active_training_jobs=active_jobs,
        total_completed_jobs=completed_jobs,
        total_failed_jobs=failed_jobs,
        available_models=len(get_available_models()),
        system_health=health
    )

@app.get("/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get system metrics"""
    return get_system_metrics()

@app.get("/models")
async def get_models():
    """Get available models"""
    models = get_available_models()
    return {"models": models, "count": len(models)}

@app.post("/train", response_model=Dict[str, str])
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start a new training job"""
    # Validate model exists
    available_models = get_available_models()
    if request.model_name not in available_models:
        raise HTTPException(
            status_code=400, 
            detail=f"Model {request.model_name} not available. Available models: {available_models}"
        )
    
    # Create job
    job_id = generate_job_id()
    job = TrainingJob(
        id=job_id,
        model_name=request.model_name,
        dataset=request.dataset,
        status="queued",
        max_steps=request.max_steps
    )
    
    training_jobs[job_id] = job
    
    # Start training in background
    background_tasks.add_task(run_training_job, job_id, request)
    
    return {"job_id": job_id, "status": "queued", "message": "Training job started"}

@app.get("/jobs")
async def get_jobs():
    """Get all training jobs"""
    return {"jobs": list(training_jobs.values()), "total": len(training_jobs)}

@app.get("/jobs/{job_id}", response_model=TrainingJob)
async def get_job(job_id: str):
    """Get specific training job"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return training_jobs[job_id]

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a training job"""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = training_jobs[job_id]
    if job.status == "running":
        # Try to kill the process (simplified - in production, you'd track PIDs)
        try:
            subprocess.run(["pkill", "-f", f"train_model.py.*{job_id}"])
            job.status = "cancelled"
            job.end_time = datetime.now().isoformat()
            return {"message": "Job cancelled"}
        except:
            raise HTTPException(status_code=500, detail="Failed to cancel job")
    else:
        raise HTTPException(status_code=400, detail="Job is not running")

@app.get("/logs/{job_id}")
async def get_job_logs(job_id: str):
    """Get training job logs"""
    log_file = LOGS_DIR / f"training_{job_id}.log"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    return FileResponse(log_file, media_type="text/plain")

@app.get("/logs")
async def get_server_logs():
    """Get server logs"""
    log_file = LOGS_DIR / "training_server.log"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Server log file not found")
    
    return FileResponse(log_file, media_type="text/plain")

@app.post("/ollama/pull")
async def pull_model(model_name: str):
    """Pull a new model via Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            return {"message": f"Model {model_name} pulled successfully"}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to pull model: {response.text}"
            )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama request failed: {str(e)}")

@app.delete("/cleanup")
async def cleanup_old_files():
    """Cleanup old model files and logs"""
    try:
        # Clean old model files (older than 7 days)
        cutoff_time = time.time() - (7 * 24 * 3600)
        cleaned_models = 0
        for model_dir in MODELS_DIR.iterdir():
            if model_dir.is_dir() and model_dir.stat().st_mtime < cutoff_time:
                subprocess.run(["rm", "-rf", str(model_dir)])
                cleaned_models += 1
        
        # Clean old log files (older than 30 days)
        cutoff_time = time.time() - (30 * 24 * 3600)
        cleaned_logs = 0
        for log_file in LOGS_DIR.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_logs += 1
        
        return {
            "message": "Cleanup completed",
            "cleaned_models": cleaned_models,
            "cleaned_logs": cleaned_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Model Fusion and Hybridization Endpoints
@app.get("/fusion/status")
async def get_fusion_status():
    """Get model fusion system status"""
    try:
        from model_fusion import ModelFusionEngine
        engine = ModelFusionEngine()
        return engine.get_fusion_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fusion status: {str(e)}")

@app.post("/fusion/pull-deepseek")
async def pull_deepseek_models(background_tasks: BackgroundTasks):
    """Pull all DeepSeek models for advanced capabilities"""
    async def pull_models_task():
        try:
            from model_fusion import ModelFusionEngine
            engine = ModelFusionEngine()
            engine.pull_deepseek_models()
        except Exception as e:
            logger.error(f"Failed to pull DeepSeek models: {e}")
    
    background_tasks.add_task(pull_models_task)
    return {"message": "DeepSeek model pulling started in background"}

@app.post("/fusion/create-hybrid")
async def create_hybrid_model(models: List[str] = None):
    """Create a hybrid model from specified models"""
    try:
        from model_fusion import ModelFusionEngine
        engine = ModelFusionEngine()
        
        if not models:
            # Use available models
            available_models = get_available_models()
            if len(available_models) < 2:
                raise HTTPException(status_code=400, detail="Need at least 2 models for fusion")
            models = available_models[:3]  # Use first 3
        
        # Create ensemble and fusion
        ensemble_config = engine.create_model_ensemble(models)
        hybrid_name = engine.simulate_model_fusion(ensemble_config)
        
        return {
            "message": f"Hybrid model '{hybrid_name}' created successfully",
            "hybrid_name": hybrid_name,
            "source_models": models,
            "ensemble_config": ensemble_config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion failed: {str(e)}")

@app.get("/fusion/hybrids")
async def get_hybrid_models():
    """Get list of created hybrid models"""
    try:
        hybrid_dir = Path("models/hybrid_models")
        if not hybrid_dir.exists():
            return {"hybrids": [], "count": 0}
        
        hybrids = []
        for hybrid_file in hybrid_dir.glob("*.json"):
            try:
                with open(hybrid_file, 'r') as f:
                    hybrid_data = json.load(f)
                hybrids.append(hybrid_data)
            except Exception as e:
                logger.error(f"Failed to load hybrid {hybrid_file}: {e}")
        
        return {"hybrids": hybrids, "count": len(hybrids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hybrids: {str(e)}")

@app.post("/fusion/start-absorption")
async def start_continuous_absorption(background_tasks: BackgroundTasks):
    """Start continuous model absorption and fusion"""
    async def absorption_task():
        try:
            from model_fusion import ModelFusionEngine
            engine = ModelFusionEngine()
            engine.continuous_absorption_cycle()
        except Exception as e:
            logger.error(f"Absorption cycle failed: {e}")
    
    background_tasks.add_task(absorption_task)
    return {"message": "Continuous model absorption started"}

@app.get("/fusion/deepseek-models")
async def get_deepseek_models():
    """Get list of DeepSeek models from configuration"""
    try:
        import json
        with open("config/training_config.json", 'r') as f:
            config = json.load(f)
        deepseek_models = config.get('models', {}).get('deepseek_models', [])
        return {"deepseek_models": deepseek_models, "count": len(deepseek_models)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DeepSeek models: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    ) 