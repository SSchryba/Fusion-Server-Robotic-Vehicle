"""
Configuration Manager for Autonomous AI Agent Framework

Handles loading, validation, and management of configuration settings
including environment variable overrides and dynamic updates.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Main agent configuration"""
    name: str = "AutonomousAgent"
    version: str = "1.0.0"
    log_level: str = "INFO"
    max_concurrent_tasks: int = 3
    task_timeout_seconds: int = 300


@dataclass
class DirectiveConfig:
    """Directive configuration"""
    primary: str = ""
    constraints: list = field(default_factory=list)
    goals: list = field(default_factory=list)


@dataclass
class MemoryConfig:
    """Memory system configuration"""
    provider: str = "chromadb"
    collection_name: str = "agent_memory"
    max_memories: int = 10000
    similarity_threshold: float = 0.7
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    persistence_enabled: bool = True
    persistence_path: str = "./data/memory"
    backup_interval_hours: int = 24


@dataclass
class SafetyConfig:
    """Safety and safeguards configuration"""
    enabled: bool = True
    actions_per_minute: int = 30
    api_calls_per_minute: int = 60
    memory_writes_per_minute: int = 120
    track_resource_usage: bool = True
    alert_on_anomalies: bool = True
    log_all_actions: bool = True
    require_approval_for: list = field(default_factory=lambda: [
        "file_write", "system_command", "api_post_request", "data_deletion"
    ])


class ConfigManager:
    """
    Manages configuration loading, validation, and runtime updates
    for the autonomous agent framework.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = Path(config_path) if config_path else self._find_config_file()
        self.config: Dict[str, Any] = {}
        self.agent_config: Optional[AgentConfig] = None
        self.directive_config: Optional[DirectiveConfig] = None
        self.memory_config: Optional[MemoryConfig] = None
        self.safety_config: Optional[SafetyConfig] = None
        
        self._load_config()
        self._apply_env_overrides()
        self._validate_config()
        
    def _find_config_file(self) -> Path:
        """Find the configuration file in standard locations."""
        possible_paths = [
            Path("./config/agent_config.yaml"),
            Path("./config/default_config.yaml"),
            Path("./autonomous_agent/config/default_config.yaml"),
            Path("../config/default_config.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found config file: {path}")
                return path
                
        # Create default path if none found
        default_path = Path("./config/agent_config.yaml")
        logger.warning(f"No config file found, will create default at: {default_path}")
        return default_path
        
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self.config = self._get_default_config()
                self._save_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
            
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'AGENT_NAME': ['agent', 'name'],
            'AGENT_LOG_LEVEL': ['agent', 'log_level'],
            'AGENT_MAX_TASKS': ['agent', 'max_concurrent_tasks'],
            'MEMORY_PROVIDER': ['memory', 'provider'],
            'MEMORY_PATH': ['memory', 'persistence', 'path'],
            'SAFETY_ENABLED': ['safety', 'enabled'],
            'LLM_API_KEY': ['llm', 'api_key'],
            'LLM_PROVIDER': ['llm', 'provider'],
            'LLM_MODEL': ['llm', 'model'],
            'DEBUG_ENABLED': ['debug', 'enabled']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_config(config_path, self._convert_env_value(env_value))
                logger.info(f"Applied environment override: {env_var}")
                
    def _set_nested_config(self, path: list, value: Any):
        """Set a nested configuration value."""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
        
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
            
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value  # Return as string
            
    def _validate_config(self):
        """Validate and create typed configuration objects."""
        try:
            # Agent configuration
            agent_data = self.config.get('agent', {})
            self.agent_config = AgentConfig(**agent_data)
            
            # Directive configuration
            directive_data = self.config.get('directive', {})
            self.directive_config = DirectiveConfig(**directive_data)
            
            # Memory configuration
            memory_data = self.config.get('memory', {})
            persistence_data = memory_data.get('persistence', {})
            memory_config_data = {
                **memory_data,
                'persistence_enabled': persistence_data.get('enabled', True),
                'persistence_path': persistence_data.get('path', './data/memory'),
                'backup_interval_hours': persistence_data.get('backup_interval_hours', 24)
            }
            # Remove nested persistence to avoid duplicate keys
            memory_config_data.pop('persistence', None)
            self.memory_config = MemoryConfig(**memory_config_data)
            
            # Safety configuration
            safety_data = self.config.get('safety', {})
            rate_limits = safety_data.get('rate_limits', {})
            monitoring = safety_data.get('monitoring', {})
            permissions = safety_data.get('permissions', {})
            
            safety_config_data = {
                'enabled': safety_data.get('enabled', True),
                'actions_per_minute': rate_limits.get('actions_per_minute', 30),
                'api_calls_per_minute': rate_limits.get('api_calls_per_minute', 60),
                'memory_writes_per_minute': rate_limits.get('memory_writes_per_minute', 120),
                'track_resource_usage': monitoring.get('track_resource_usage', True),
                'alert_on_anomalies': monitoring.get('alert_on_anomalies', True),
                'log_all_actions': monitoring.get('log_all_actions', True),
                'require_approval_for': permissions.get('require_approval_for', [])
            }
            self.safety_config = SafetyConfig(**safety_config_data)
            
            logger.info("Configuration validation completed successfully")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigurationError(f"Invalid configuration: {e}")
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            'agent': {
                'name': 'AutonomousAgent',
                'version': '1.0.0',
                'log_level': 'INFO',
                'max_concurrent_tasks': 3,
                'task_timeout_seconds': 300
            },
            'directive': {
                'primary': 'I am an autonomous AI agent designed to help users achieve their goals efficiently and safely.',
                'constraints': [
                    'Never cause harm to users or systems',
                    'Respect privacy and data security',
                    'Operate within defined resource limits'
                ],
                'goals': [
                    'Maximize user productivity and satisfaction',
                    'Learn and adapt from experiences',
                    'Maintain system stability and security'
                ]
            },
            'memory': {
                'provider': 'chromadb',
                'collection_name': 'agent_memory',
                'max_memories': 10000,
                'similarity_threshold': 0.7,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                'persistence': {
                    'enabled': True,
                    'path': './data/memory',
                    'backup_interval_hours': 24
                }
            },
            'safety': {
                'enabled': True,
                'rate_limits': {
                    'actions_per_minute': 30,
                    'api_calls_per_minute': 60,
                    'memory_writes_per_minute': 120
                },
                'monitoring': {
                    'track_resource_usage': True,
                    'alert_on_anomalies': True,
                    'log_all_actions': True
                },
                'permissions': {
                    'require_approval_for': [
                        'file_write', 'system_command', 'api_post_request'
                    ]
                }
            }
        }
        
    def _save_default_config(self):
        """Save default configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            logger.info(f"Saved default configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save default config: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key path (e.g., 'agent.name').
        
        Args:
            key: Dot-separated key path
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """
        Set a configuration value by key path.
        
        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        logger.info(f"Updated configuration: {key} = {value}")
        
    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
            
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
        self._apply_env_overrides()
        self._validate_config()
        logger.info("Configuration reloaded")
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (e.g., 'agent', 'memory')
            
        Returns:
            Section dictionary
        """
        return self.config.get(section, {})
        
    def update_section(self, section: str, updates: Dict[str, Any]):
        """
        Update an entire configuration section.
        
        Args:
            section: Section name
            updates: Updates to apply
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section].update(updates)
        logger.info(f"Updated configuration section: {section}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()
        
    def to_json(self) -> str:
        """Return configuration as JSON string."""
        return json.dumps(self.config, indent=2)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass 