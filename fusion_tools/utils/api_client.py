#!/usr/bin/env python3
"""
API Client for Fusion Server
Handles all communication with the local fusion server
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FusionStatus:
    """Data class for fusion status"""
    fusion_enabled: bool
    fusion_version: int
    total_absorptions: int
    recent_absorptions: List[Dict]
    hybrid_models_created: int
    next_fusion_in_hours: int
    absorption_strategy: str

class FusionAPIClient:
    """Client for interacting with the fusion server API"""
    
    def __init__(self, host: str = "localhost", port: int = 8000, timeout: int = 30):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.session = requests.Session()
        
    def get_fusion_status(self) -> Optional[FusionStatus]:
        """Get current fusion system status"""
        try:
            response = self.session.get(f"{self.base_url}/fusion/status", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            return FusionStatus(
                fusion_enabled=data.get('fusion_enabled', False),
                fusion_version=data.get('fusion_version', 0),
                total_absorptions=data.get('total_absorptions', 0),
                recent_absorptions=data.get('recent_absorptions', []),
                hybrid_models_created=data.get('hybrid_models_created', 0),
                next_fusion_in_hours=data.get('next_fusion_in_hours', 0),
                absorption_strategy=data.get('absorption_strategy', 'unknown')
            )
        except Exception as e:
            logger.error(f"Failed to get fusion status: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = self.session.get(f"{self.base_url}/models", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def get_hybrid_models(self) -> List[Dict]:
        """Get list of created hybrid models"""
        try:
            response = self.session.get(f"{self.base_url}/fusion/hybrids", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get('hybrids', [])
        except Exception as e:
            logger.error(f"Failed to get hybrid models: {e}")
            return []
    
    def pull_deepseek_models(self) -> bool:
        """Pull DeepSeek models"""
        try:
            response = self.session.post(f"{self.base_url}/fusion/pull-deepseek", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull DeepSeek models: {e}")
            return False
    
    def create_hybrid(self, models: List[str]) -> Optional[Dict]:
        """Create a new hybrid model"""
        try:
            response = self.session.post(
                f"{self.base_url}/fusion/create-hybrid",
                json=models,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create hybrid model: {e}")
            return None
    
    def start_absorption(self) -> bool:
        """Start continuous absorption cycle"""
        try:
            response = self.session.post(f"{self.base_url}/fusion/start-absorption", timeout=self.timeout)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to start absorption: {e}")
            return False
    
    def chat_with_model(self, model: str, input_text: str) -> Optional[str]:
        """Send chat message to model"""
        try:
            payload = {
                "model": model,
                "input": input_text
            }
            response = self.session.post(
                f"{self.base_url}/fusion/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get('response', '')
        except Exception as e:
            logger.error(f"Failed to chat with model: {e}")
            return None
    
    def get_server_health(self) -> Dict:
        """Get server health status"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get server health: {e}")
            return {"status": "error", "message": str(e)}
    
    def evaluate_model_performance(self, model_name: str) -> Dict:
        """Evaluate model performance (mock implementation)"""
        # In a real implementation, this would run actual performance tests
        base_scores = {
            "deepseek-coder": {"deep_reasoning": 9.2, "code_generation": 9.5, "math": 8.8},
            "deepseek-math": {"deep_reasoning": 9.0, "code_generation": 7.5, "math": 9.5},
            "mistral": {"deep_reasoning": 8.5, "code_generation": 7.8, "following_instructions": 9.0},
            "codellama": {"deep_reasoning": 8.0, "code_generation": 9.2, "programming": 9.4},
            "llama2": {"deep_reasoning": 7.8, "general": 8.5, "conversation": 8.8},
            "phi": {"deep_reasoning": 7.5, "general": 7.0, "efficiency": 8.5},
            "gemma": {"deep_reasoning": 7.2, "general": 7.8, "efficiency": 8.0}
        }
        
        # Extract base name from model string
        base_name = model_name.split(':')[0].lower()
        for key, scores in base_scores.items():
            if key in base_name:
                return {
                    "model": model_name,
                    "capabilities": scores,
                    "overall_score": sum(scores.values()) / len(scores),
                    "hallucination_rate": 0.05 + (hash(model_name) % 10) / 100,  # Mock rate
                    "response_time": 2.5 + (hash(model_name) % 5),  # Mock response time
                    "error_rate": 0.02 + (hash(model_name) % 5) / 100  # Mock error rate
                }
        
        # Default scores for unknown models
        return {
            "model": model_name,
            "capabilities": {"general": 6.0},
            "overall_score": 6.0,
            "hallucination_rate": 0.15,
            "response_time": 5.0,
            "error_rate": 0.08
        } 