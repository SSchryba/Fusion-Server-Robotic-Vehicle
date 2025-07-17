#!/usr/bin/env python3
"""
Configuration Loader for Fusion Tools
Handles loading and parsing YAML configuration files
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModelConstraints:
    """Model constraints configuration"""
    max_parameter_size: str
    min_capability_threshold: float
    max_hallucination_rate: float

@dataclass
class FusionConfig:
    """Main fusion configuration"""
    host: str
    port: int
    timeout: int
    model_constraints: ModelConstraints
    capability_requirements: Dict[str, float]
    evaluation_criteria: Dict[str, float]
    fusion_control: Dict[str, Any]
    monitor: Dict[str, Any]
    chat: Dict[str, Any]
    disqualification_rules: List[Dict[str, str]]
    priority_models: List[str]

class ConfigLoader:
    """Loads and manages configuration from YAML files"""
    
    def __init__(self, config_path: str = "fusion_tools/config/fusion_config.yaml"):
        self.config_path = Path(config_path)
        self._config = None
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                self._create_default_config()
                return
            
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration if none exists"""
        self._config = {
            'fusion_server': {
                'host': 'localhost',
                'port': 8000,
                'timeout': 30
            },
            'model_constraints': {
                'max_parameter_size': '13B',
                'min_capability_threshold': 7.5,
                'max_hallucination_rate': 0.20
            },
            'capability_requirements': {
                'deep_reasoning': 7.5,
                'code_generation': 7.0,
                'math': 6.5,
                'following_instructions': 8.0,
                'general': 6.0
            },
            'evaluation_criteria': {
                'performance_weight': 0.4,
                'capability_weight': 0.3,
                'efficiency_weight': 0.2,
                'reliability_weight': 0.1
            },
            'fusion_control': {
                'cycle_interval_hours': 56,
                'models_per_fusion': 3,
                'max_concurrent_fusions': 2,
                'backup_interval_hours': 12
            },
            'monitor': {
                'refresh_interval': 5,
                'display_history': 10,
                'log_level': 'INFO'
            },
            'chat': {
                'default_model': 'hybrid-fusion-v1',
                'max_message_length': 4096,
                'response_timeout': 60,
                'enable_history': True,
                'max_history_size': 100
            },
            'disqualification_rules': [
                {'condition': 'hallucination_rate > 0.25', 'action': 'remove'},
                {'condition': 'response_time > 30', 'action': 'deprioritize'},
                {'condition': 'capability_score < 6.0', 'action': 'remove'},
                {'condition': 'error_rate > 0.15', 'action': 'remove'}
            ],
            'priority_models': [
                'deepseek-coder:latest',
                'deepseek-math:latest',
                'deepseek-v2:latest',
                'mistral:latest',
                'codellama:latest'
            ]
        }
    
    def get_fusion_config(self) -> FusionConfig:
        """Get structured fusion configuration"""
        if not self._config:
            self.load_config()
        
        server_config = self._config.get('fusion_server', {})
        constraints_config = self._config.get('model_constraints', {})
        
        model_constraints = ModelConstraints(
            max_parameter_size=constraints_config.get('max_parameter_size', '13B'),
            min_capability_threshold=constraints_config.get('min_capability_threshold', 7.5),
            max_hallucination_rate=constraints_config.get('max_hallucination_rate', 0.20)
        )
        
        return FusionConfig(
            host=server_config.get('host', 'localhost'),
            port=server_config.get('port', 8000),
            timeout=server_config.get('timeout', 30),
            model_constraints=model_constraints,
            capability_requirements=self._config.get('capability_requirements', {}),
            evaluation_criteria=self._config.get('evaluation_criteria', {}),
            fusion_control=self._config.get('fusion_control', {}),
            monitor=self._config.get('monitor', {}),
            chat=self._config.get('chat', {}),
            disqualification_rules=self._config.get('disqualification_rules', []),
            priority_models=self._config.get('priority_models', [])
        )
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self._config.get('fusion_server', {})
    
    def get_model_constraints(self) -> Dict[str, Any]:
        """Get model constraints"""
        return self._config.get('model_constraints', {})
    
    def get_monitor_config(self) -> Dict[str, Any]:
        """Get monitor configuration"""
        return self._config.get('monitor', {})
    
    def get_chat_config(self) -> Dict[str, Any]:
        """Get chat configuration"""
        return self._config.get('chat', {})
    
    def get_fusion_control_config(self) -> Dict[str, Any]:
        """Get fusion control configuration"""
        return self._config.get('fusion_control', {})
    
    def get_priority_models(self) -> List[str]:
        """Get priority models list"""
        return self._config.get('priority_models', [])
    
    def get_disqualification_rules(self) -> List[Dict[str, str]]:
        """Get disqualification rules"""
        return self._config.get('disqualification_rules', [])
    
    def evaluate_model_against_rules(self, model_performance: Dict[str, Any]) -> str:
        """Evaluate model against disqualification rules"""
        rules = self.get_disqualification_rules()
        
        for rule in rules:
            condition = rule.get('condition', '')
            action = rule.get('action', 'remove')
            
            try:
                # Simple evaluation of conditions (in production, use a proper parser)
                if self._evaluate_condition(condition, model_performance):
                    return action
            except Exception as e:
                logger.warning(f"Failed to evaluate rule '{condition}': {e}")
        
        return 'keep'
    
    def _evaluate_condition(self, condition: str, model_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition against model data"""
        # Simple condition evaluation - in production, use a proper expression parser
        
        # Replace model data keys in condition
        eval_condition = condition
        for key, value in model_data.items():
            eval_condition = eval_condition.replace(key, str(value))
        
        # Replace capability_score with overall_score if present
        if 'capability_score' in eval_condition and 'overall_score' in model_data:
            eval_condition = eval_condition.replace('capability_score', str(model_data['overall_score']))
        
        # Evaluate the condition (WARNING: eval is dangerous in production!)
        # In a real implementation, use a proper expression parser
        try:
            return eval(eval_condition)
        except:
            return False
    
    def save_config(self, config_updates: Dict[str, Any]) -> bool:
        """Save configuration updates"""
        try:
            if self._config:
                self._config.update(config_updates)
                
                with open(self.config_path, 'w') as f:
                    yaml.dump(self._config, f, default_flow_style=False)
                
                logger.info(f"Configuration saved to {self.config_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False 