"""
Fusion Knowledge Updater for Autonomous AI Agent Framework

Integrates quantum computing knowledge into the model fusion system
by updating absorption parameters and injecting domain-specific knowledge.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    import aiohttp
    import requests
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class FusionKnowledgeUpdater:
    """
    Updates the model fusion system with quantum computing knowledge
    and adjusts fusion weights based on domain expertise.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the fusion knowledge updater.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Fusion server configuration
        self.fusion_server_url = os.getenv('FUSION_SERVER_URL', 'http://localhost:8000')
        self.api_key = os.getenv('FUSION_API_KEY')
        
        # Knowledge update tracking
        self.update_history: List[Dict[str, Any]] = []
        
        # Quantum domain model priorities
        self.quantum_model_priorities = {
            'deepseek-coder': {
                'priority': 1.0,
                'specialization': 'quantum_programming',
                'weight_boost': 0.3
            },
            'codellama': {
                'priority': 0.8,
                'specialization': 'algorithm_implementation',
                'weight_boost': 0.2
            },
            'phu': {
                'priority': 0.6,
                'specialization': 'mathematical_reasoning',
                'weight_boost': 0.15
            },
            'mistral-7b': {
                'priority': 0.4,
                'specialization': 'general_quantum_knowledge',
                'weight_boost': 0.1
            }
        }
        
        logger.info("Fusion Knowledge Updater initialized")
        
    async def inject_quantum_knowledge(self, 
                                      knowledge_source: str,
                                      knowledge_data: Optional[Dict[str, Any]] = None,
                                      weight_adjustments: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Inject quantum computing knowledge into the fusion system.
        
        Args:
            knowledge_source: Source of knowledge (file path or identifier)
            knowledge_data: Optional direct knowledge data
            weight_adjustments: Optional manual weight adjustments
            
        Returns:
            Dictionary with injection results
        """
        if not HTTP_AVAILABLE:
            raise ImportError("HTTP libraries required for fusion server communication")
            
        try:
            logger.info(f"Injecting quantum knowledge: {knowledge_source}")
            
            # Prepare knowledge injection payload
            injection_payload = {
                "timestamp": datetime.now().isoformat(),
                "knowledge_source": knowledge_source,
                "domain": "quantum_computing",
                "priority_area": "quantum_execution",
                "model_adjustments": self._calculate_model_adjustments(weight_adjustments),
                "fusion_parameters": self._get_quantum_fusion_parameters()
            }
            
            # Add knowledge data if provided
            if knowledge_data:
                injection_payload["extra_knowledge"] = knowledge_data
            elif knowledge_source.endswith('.json'):
                # Load knowledge from file
                try:
                    with open(knowledge_source, 'r') as f:
                        injection_payload["extra_knowledge"] = json.load(f)
                except FileNotFoundError:
                    logger.warning(f"Knowledge file not found: {knowledge_source}")
                    
            # Send to fusion server
            result = await self._send_fusion_request('/fusion/start-absorption', injection_payload)
            
            # Record update
            update_record = {
                'timestamp': datetime.now().isoformat(),
                'knowledge_source': knowledge_source,
                'success': result.get('success', False),
                'fusion_response': result,
                'model_adjustments': injection_payload["model_adjustments"]
            }
            
            self.update_history.append(update_record)
            
            # Limit history size
            if len(self.update_history) > 100:
                self.update_history = self.update_history[-100:]
                
            if result.get('success'):
                logger.info("Quantum knowledge injection successful")
            else:
                logger.error(f"Quantum knowledge injection failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to inject quantum knowledge: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    def _calculate_model_adjustments(self, manual_adjustments: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Calculate model weight adjustments for quantum domain."""
        adjustments = {
            "models": [],
            "weight_modifiers": {},
            "capability_boosts": {},
            "specialization_areas": ["quantum_circuits", "quantum_algorithms", "quantum_hardware"]
        }
        
        # Apply quantum domain priorities
        for model_name, config in self.quantum_model_priorities.items():
            model_adjustment = {
                "name": model_name,
                "priority_multiplier": config['priority'],
                "specialization": config['specialization'],
                "weight_boost": config['weight_boost']
            }
            
            # Apply manual adjustments if provided
            if manual_adjustments and model_name in manual_adjustments:
                model_adjustment["weight_boost"] += manual_adjustments[model_name]
                
            adjustments["models"].append(model_adjustment)
            adjustments["weight_modifiers"][model_name] = model_adjustment["weight_boost"]
            
        # Set capability boosts for quantum domain
        adjustments["capability_boosts"] = {
            "quantum_circuit_generation": 1.5,
            "quantum_algorithm_design": 1.4,
            "quantum_error_correction": 1.3,
            "quantum_optimization": 1.2,
            "quantum_simulation": 1.1
        }
        
        return adjustments
        
    def _get_quantum_fusion_parameters(self) -> Dict[str, Any]:
        """Get fusion parameters optimized for quantum computing."""
        return {
            "fusion_strategy": "weighted_specialization",
            "quantum_weights": {
                "code_correctness": 0.35,
                "quantum_domain_knowledge": 0.30,
                "mathematical_accuracy": 0.20,
                "implementation_efficiency": 0.15
            },
            "learning_rate": 0.02,
            "convergence_threshold": 0.85,
            "max_fusion_iterations": 50,
            "preserve_quantum_expertise": True,
            "quantum_validation_enabled": True
        }
        
    async def update_fusion_weights(self, 
                                   performance_metrics: Dict[str, float],
                                   job_success_rates: Dict[str, float]) -> Dict[str, Any]:
        """
        Update fusion weights based on quantum job performance.
        
        Args:
            performance_metrics: Performance metrics by model
            job_success_rates: Job success rates by quantum backend
            
        Returns:
            Dictionary with weight update results
        """
        try:
            logger.info("Updating fusion weights based on quantum performance")
            
            # Calculate weight adjustments based on performance
            weight_updates = {}
            
            for model_name, success_rate in performance_metrics.items():
                if model_name in self.quantum_model_priorities:
                    base_weight = self.quantum_model_priorities[model_name]['weight_boost']
                    
                    # Adjust weight based on success rate
                    if success_rate > 0.8:
                        # High success rate - increase weight
                        weight_updates[model_name] = base_weight * 1.2
                    elif success_rate > 0.6:
                        # Good success rate - maintain weight
                        weight_updates[model_name] = base_weight
                    elif success_rate > 0.4:
                        # Poor success rate - reduce weight
                        weight_updates[model_name] = base_weight * 0.8
                    else:
                        # Very poor success rate - significant reduction
                        weight_updates[model_name] = base_weight * 0.5
                        
            # Prepare weight update payload
            update_payload = {
                "timestamp": datetime.now().isoformat(),
                "update_type": "performance_based",
                "weight_updates": weight_updates,
                "performance_metrics": performance_metrics,
                "job_success_rates": job_success_rates,
                "adjustment_reason": "quantum_job_performance_optimization"
            }
            
            # Send weight updates to fusion server
            result = await self._send_fusion_request('/fusion/update-weights', update_payload)
            
            # Record update
            update_record = {
                'timestamp': datetime.now().isoformat(),
                'update_type': 'weight_adjustment',
                'weight_updates': weight_updates,
                'success': result.get('success', False),
                'performance_basis': performance_metrics
            }
            
            self.update_history.append(update_record)
            
            if result.get('success'):
                logger.info("Fusion weight update successful")
            else:
                logger.error(f"Fusion weight update failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to update fusion weights: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def schedule_periodic_updates(self, 
                                       knowledge_source: str,
                                       interval_hours: int = 24) -> Dict[str, Any]:
        """
        Schedule periodic knowledge updates.
        
        Args:
            knowledge_source: Source of knowledge to update
            interval_hours: Update interval in hours
            
        Returns:
            Dictionary with scheduling results
        """
        try:
            logger.info(f"Scheduling periodic knowledge updates every {interval_hours} hours")
            
            schedule_payload = {
                "timestamp": datetime.now().isoformat(),
                "schedule_type": "periodic_knowledge_update",
                "knowledge_source": knowledge_source,
                "interval_hours": interval_hours,
                "domain": "quantum_computing",
                "auto_weight_adjustment": True,
                "performance_monitoring": True
            }
            
            # Send scheduling request to fusion server
            result = await self._send_fusion_request('/fusion/schedule-update', schedule_payload)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule periodic updates: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def _send_fusion_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to fusion server."""
        try:
            url = f"{self.fusion_server_url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
                
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'response': result,
                            'status_code': response.status
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {error_text}',
                            'status_code': response.status
                        }
                        
        except aiohttp.ClientError as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'status_code': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'status_code': None
            }
            
    async def get_fusion_status(self) -> Dict[str, Any]:
        """Get current fusion system status."""
        try:
            result = await self._send_fusion_request('/fusion/status', {})
            
            if result['success']:
                return result['response']
            else:
                return {
                    'error': 'Failed to get fusion status',
                    'details': result['error']
                }
                
        except Exception as e:
            logger.error(f"Failed to get fusion status: {e}")
            return {
                'error': str(e),
                'fusion_server_url': self.fusion_server_url
            }
            
    def create_quantum_knowledge_package(self, 
                                        knowledge_chunks: List[Dict[str, Any]],
                                        output_path: str) -> Dict[str, Any]:
        """
        Create a knowledge package for fusion injection.
        
        Args:
            knowledge_chunks: List of knowledge chunks from ingestor
            output_path: Path to save the knowledge package
            
        Returns:
            Dictionary with package creation results
        """
        try:
            logger.info(f"Creating quantum knowledge package: {output_path}")
            
            # Organize knowledge by source and type
            organized_knowledge = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "domain": "quantum_computing",
                    "total_chunks": len(knowledge_chunks),
                    "version": "1.0"
                },
                "knowledge_sources": {},
                "embeddings": [],
                "fusion_hints": self._generate_fusion_hints(knowledge_chunks)
            }
            
            # Organize chunks by source
            for chunk in knowledge_chunks:
                source = chunk.get('source', 'unknown')
                if source not in organized_knowledge["knowledge_sources"]:
                    organized_knowledge["knowledge_sources"][source] = {
                        "chunks": [],
                        "doc_types": set(),
                        "total_words": 0
                    }
                    
                organized_knowledge["knowledge_sources"][source]["chunks"].append({
                    "id": chunk.get('id'),
                    "title": chunk.get('title'),
                    "content": chunk.get('content'),
                    "doc_type": chunk.get('doc_type'),
                    "metadata": chunk.get('metadata', {})
                })
                
                organized_knowledge["knowledge_sources"][source]["doc_types"].add(chunk.get('doc_type', 'unknown'))
                organized_knowledge["knowledge_sources"][source]["total_words"] += len(chunk.get('content', '').split())
                
                # Add embedding if available
                if chunk.get('embedding'):
                    organized_knowledge["embeddings"].append({
                        "chunk_id": chunk.get('id'),
                        "embedding": chunk.get('embedding'),
                        "source": source,
                        "doc_type": chunk.get('doc_type')
                    })
                    
            # Convert sets to lists for JSON serialization
            for source_data in organized_knowledge["knowledge_sources"].values():
                source_data["doc_types"] = list(source_data["doc_types"])
                
            # Save knowledge package
            with open(output_path, 'w') as f:
                json.dump(organized_knowledge, f, indent=2)
                
            package_stats = {
                'success': True,
                'output_path': output_path,
                'total_chunks': len(knowledge_chunks),
                'sources': list(organized_knowledge["knowledge_sources"].keys()),
                'embeddings_count': len(organized_knowledge["embeddings"]),
                'file_size_mb': os.path.getsize(output_path) / 1024 / 1024
            }
            
            logger.info(f"Quantum knowledge package created: {package_stats}")
            
            return package_stats
            
        except Exception as e:
            logger.error(f"Failed to create knowledge package: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _generate_fusion_hints(self, knowledge_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate hints for the fusion system about knowledge utilization."""
        hints = {
            "quantum_concepts": [],
            "programming_patterns": [],
            "error_patterns": [],
            "optimization_techniques": [],
            "hardware_considerations": []
        }
        
        # Analyze chunks for common patterns
        for chunk in knowledge_chunks:
            content = chunk.get('content', '').lower()
            
            # Identify quantum concepts
            quantum_keywords = ['qubit', 'quantum gate', 'superposition', 'entanglement', 'measurement']
            for keyword in quantum_keywords:
                if keyword in content and keyword not in hints["quantum_concepts"]:
                    hints["quantum_concepts"].append(keyword)
                    
            # Identify programming patterns
            if chunk.get('doc_type') == 'example' or 'example' in content:
                if 'quantumcircuit' in content:
                    hints["programming_patterns"].append("qiskit_circuit_construction")
                if 'cirq.circuit' in content:
                    hints["programming_patterns"].append("cirq_circuit_construction")
                if '@qml.qnode' in content:
                    hints["programming_patterns"].append("pennylane_qnode_pattern")
                    
            # Identify error patterns
            error_keywords = ['error', 'noise', 'decoherence', 'mitigation']
            for keyword in error_keywords:
                if keyword in content and f"quantum_{keyword}" not in hints["error_patterns"]:
                    hints["error_patterns"].append(f"quantum_{keyword}")
                    
        return hints
        
    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent update history."""
        return self.update_history[-limit:] if self.update_history else []
        
    def get_fusion_integration_stats(self) -> Dict[str, Any]:
        """Get statistics about fusion integration."""
        if not self.update_history:
            return {'total_updates': 0}
            
        successful_updates = [u for u in self.update_history if u.get('success')]
        failed_updates = [u for u in self.update_history if not u.get('success')]
        
        update_types = {}
        for update in self.update_history:
            update_type = update.get('update_type', 'knowledge_injection')
            update_types[update_type] = update_types.get(update_type, 0) + 1
            
        return {
            'total_updates': len(self.update_history),
            'successful_updates': len(successful_updates),
            'failed_updates': len(failed_updates),
            'success_rate': len(successful_updates) / len(self.update_history),
            'update_types': update_types,
            'fusion_server_url': self.fusion_server_url,
            'model_priorities': self.quantum_model_priorities
        } 