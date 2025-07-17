"""
Quantum Agent Orchestrator for Autonomous AI Agent Framework

Main orchestrator that coordinates quantum computing, HPC operations,
knowledge management, and fusion system integration.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

try:
    # Try relative imports first (when used as module)
    from .quantum_executor import QuantumExecutor, QuantumBackend
    from .supercomputer_dispatcher import SupercomputerDispatcher, JobScheduler
    from .quantum_knowledge_ingestor import QuantumKnowledgeIngestor
    from .fusion_knowledge_updater import FusionKnowledgeUpdater
    from .job_logger import JobLogger, JobType, JobPlatform
    from .safeguard import QuantumSafeguards
except ImportError:
    # Fall back to absolute imports (when run directly)
    from quantum_executor import QuantumExecutor, QuantumBackend
    from supercomputer_dispatcher import SupercomputerDispatcher, JobScheduler
    from quantum_knowledge_ingestor import QuantumKnowledgeIngestor
    from fusion_knowledge_updater import FusionKnowledgeUpdater
    from job_logger import JobLogger, JobType, JobPlatform
    from safeguard import QuantumSafeguards

logger = logging.getLogger(__name__)


class QuantumAgentOrchestrator:
    """
    Main orchestrator for quantum computing and HPC operations.
    Integrates all quantum agent components for autonomous operation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the quantum agent orchestrator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.safeguards = QuantumSafeguards(config)
        self.job_logger = JobLogger(config)
        self.quantum_executor = QuantumExecutor(config)
        self.hpc_dispatcher = SupercomputerDispatcher(config)
        self.knowledge_ingestor = QuantumKnowledgeIngestor(config)
        self.fusion_updater = FusionKnowledgeUpdater(config)
        
        # Agent state
        self.running = False
        self.start_time = None
        
        # Performance tracking
        self.performance_metrics = {
            'quantum_success_rate': 0.0,
            'hpc_success_rate': 0.0,
            'average_quantum_time': 0.0,
            'average_hpc_time': 0.0,
            'total_jobs_executed': 0
        }
        
        logger.info("Quantum Agent Orchestrator initialized")
        
    async def start(self):
        """Start the quantum agent orchestrator."""
        if self.running:
            logger.warning("Quantum agent is already running")
            return
            
        logger.info("Starting Quantum Agent Orchestrator...")
        
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # Initial knowledge ingestion (if not already done)
            await self._initialize_knowledge_base()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Quantum Agent Orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start quantum agent: {e}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the quantum agent orchestrator."""
        if not self.running:
            logger.warning("Quantum agent is not running")
            return
            
        logger.info("Stopping Quantum Agent Orchestrator...")
        
        try:
            self.running = False
            
            # Cleanup HPC connections
            self.hpc_dispatcher.cleanup_connections()
            
            logger.info("Quantum Agent Orchestrator stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during quantum agent shutdown: {e}")
            
    async def execute_quantum_job(self,
                                 backend: QuantumBackend,
                                 circuit_code: str,
                                 parameters: Optional[Dict[str, Any]] = None,
                                 description: str = "Quantum job") -> Dict[str, Any]:
        """
        Execute a quantum computing job with full safety and logging.
        
        Args:
            backend: Target quantum backend
            circuit_code: Quantum circuit code
            parameters: Job parameters
            description: Job description
            
        Returns:
            Dictionary with execution results
        """
        try:
            logger.info(f"Executing quantum job on {backend.value}")
            
            # Safety validation
            safety_result = self.safeguards.validate_quantum_operation(
                backend.value,
                circuit_code,
                parameters or {}
            )
            
            if not safety_result['safe']:
                return {
                    'success': False,
                    'error': f"Safety validation failed: {safety_result['blocked_reasons']}",
                    'safety_issues': safety_result
                }
                
            # Create job log entry
            job_id = self.job_logger.create_job(
                job_type=JobType.QUANTUM_CIRCUIT,
                platform=JobPlatform(backend.value),
                description=description,
                code_snippet=circuit_code,
                parameters=parameters or {}
            )
            
            # Update job status
            self.job_logger.update_job_status(job_id, "submitted")
            
            # Execute quantum job
            execution_result = await self.quantum_executor.run_on_quantum_backend(
                circuit_code=circuit_code,
                backend=backend,
                parameters=parameters,
                shots=parameters.get('shots', 1024) if parameters else 1024
            )
            
            # Log results
            logger_job_id = self.job_logger.log_quantum_job(
                platform=JobPlatform(backend.value),
                circuit_code=circuit_code,
                shots=parameters.get('shots', 1024) if parameters else 1024,
                qubits=parameters.get('qubits', 1) if parameters else 1,
                result=execution_result.get('result'),
                success=execution_result['success'],
                error=execution_result.get('error'),
                execution_time=execution_result.get('execution_time')
            )
            
            # Update performance metrics
            self._update_performance_metrics('quantum', execution_result)
            
            # Return comprehensive result
            return {
                'success': execution_result['success'],
                'job_id': job_id,
                'logger_job_id': logger_job_id,
                'backend': backend.value,
                'result': execution_result.get('result'),
                'execution_time': execution_result.get('execution_time'),
                'error': execution_result.get('error'),
                'safety_warnings': safety_result.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"Quantum job execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'backend': backend.value
            }
            
    async def execute_hpc_job(self,
                             cluster_name: str,
                             job_script: str,
                             job_type: str = "batch",
                             nodes: int = 1,
                             cpus_per_task: int = 1,
                             memory_gb: int = 4,
                             walltime_hours: int = 1,
                             description: str = "HPC job") -> Dict[str, Any]:
        """
        Execute an HPC job with full safety and logging.
        
        Args:
            cluster_name: Target HPC cluster
            job_script: Job script content
            job_type: Type of job
            nodes: Number of nodes
            cpus_per_task: CPUs per task
            memory_gb: Memory in GB
            walltime_hours: Wall time in hours
            description: Job description
            
        Returns:
            Dictionary with execution results
        """
        try:
            logger.info(f"Executing HPC job on {cluster_name}")
            
            # Safety validation
            safety_result = self.safeguards.validate_hpc_operation(
                cluster_name,
                job_script,
                {
                    'nodes': nodes,
                    'cpus_per_task': cpus_per_task,
                    'memory_gb': memory_gb,
                    'walltime_hours': walltime_hours
                }
            )
            
            if not safety_result['safe']:
                return {
                    'success': False,
                    'error': f"Safety validation failed: {safety_result['blocked_reasons']}",
                    'safety_issues': safety_result
                }
                
            # Create job log entry
            job_id = self.job_logger.create_job(
                job_type=JobType.HPC_BATCH if job_type == "batch" else JobType.HPC_MPI,
                platform=JobPlatform(cluster_name.upper()),
                description=description,
                code_snippet=job_script,
                parameters={
                    'nodes': nodes,
                    'cpus_per_task': cpus_per_task,
                    'memory_gb': memory_gb,
                    'walltime_hours': walltime_hours
                }
            )
            
            # Update job status
            self.job_logger.update_job_status(job_id, "submitted")
            
            # Execute HPC job
            execution_result = await self.hpc_dispatcher.run_on_supercomputer(
                cluster_name=cluster_name,
                job_script=job_script,
                job_type=job_type,
                nodes=nodes,
                cpus_per_task=cpus_per_task,
                memory_gb=memory_gb,
                walltime_hours=walltime_hours
            )
            
            # Log results
            logger_job_id = self.job_logger.log_hpc_job(
                platform=JobPlatform(cluster_name.upper()),
                job_script=job_script,
                scheduler_job_id=execution_result.get('scheduler_job_id'),
                nodes=nodes,
                cpus=cpus_per_task,
                memory_gb=memory_gb,
                walltime_hours=walltime_hours,
                result=execution_result.get('result'),
                success=execution_result['success'],
                error=execution_result.get('error'),
                execution_time=execution_result.get('execution_time')
            )
            
            # Update performance metrics
            self._update_performance_metrics('hpc', execution_result)
            
            # Return comprehensive result
            return {
                'success': execution_result['success'],
                'job_id': job_id,
                'logger_job_id': logger_job_id,
                'cluster': cluster_name,
                'scheduler_job_id': execution_result.get('scheduler_job_id'),
                'result': execution_result.get('result'),
                'execution_time': execution_result.get('execution_time'),
                'error': execution_result.get('error'),
                'safety_warnings': safety_result.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"HPC job execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'cluster': cluster_name
            }
            
    async def update_knowledge_base(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update the quantum knowledge base and inject into fusion system.
        
        Args:
            sources: Optional list of sources to update
            
        Returns:
            Dictionary with update results
        """
        try:
            logger.info("Updating quantum knowledge base...")
            
            # Ingest quantum documentation
            if sources:
                # Selective update for specific sources
                ingestion_result = {'total_processed': 0, 'sources': {}}
                for source in sources:
                    if source in self.knowledge_ingestor.quantum_sources:
                        source_config = self.knowledge_ingestor.quantum_sources[source]
                        source_result = await self.knowledge_ingestor._ingest_source(source, source_config)
                        ingestion_result['sources'][source] = source_result
                        ingestion_result['total_processed'] += source_result['processed_count']
            else:
                # Full knowledge base update
                ingestion_result = await self.knowledge_ingestor.ingest_all_sources()
                
            # Export knowledge for fusion
            knowledge_package_path = "quantum_agent/memory/quantum_knowledge_package.json"
            package_result = self.fusion_updater.create_quantum_knowledge_package(
                self.knowledge_ingestor.document_chunks,
                knowledge_package_path
            )
            
            # Inject into fusion system
            if package_result['success']:
                fusion_result = await self.fusion_updater.inject_quantum_knowledge(
                    knowledge_package_path
                )
            else:
                fusion_result = {'success': False, 'error': 'Knowledge package creation failed'}
                
            return {
                'success': True,
                'ingestion_result': ingestion_result,
                'package_result': package_result,
                'fusion_result': fusion_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Knowledge base update failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def _initialize_knowledge_base(self):
        """Initialize quantum knowledge base if not already done."""
        try:
            # Check if knowledge base exists
            kb_stats = self.knowledge_ingestor.get_knowledge_stats()
            
            if kb_stats['total_documents'] == 0:
                logger.info("Initializing quantum knowledge base...")
                await self.update_knowledge_base()
            else:
                logger.info(f"Knowledge base already initialized with {kb_stats['total_documents']} documents")
                
        except Exception as e:
            logger.warning(f"Failed to initialize knowledge base: {e}")
            
    async def _start_background_tasks(self):
        """Start background monitoring tasks."""
        # Performance monitoring
        asyncio.create_task(self._performance_monitoring_loop())
        
        # Periodic knowledge updates
        asyncio.create_task(self._periodic_knowledge_update_loop())
        
    async def _performance_monitoring_loop(self):
        """Background performance monitoring."""
        while self.running:
            try:
                # Update performance metrics
                await self._calculate_performance_metrics()
                
                # Update fusion weights based on performance
                if self.performance_metrics['total_jobs_executed'] > 10:
                    await self._update_fusion_weights()
                    
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(300)
                
    async def _periodic_knowledge_update_loop(self):
        """Background knowledge base updates."""
        while self.running:
            try:
                # Update knowledge base every 24 hours
                await asyncio.sleep(86400)  # 24 hours
                
                logger.info("Performing periodic knowledge base update...")
                await self.update_knowledge_base()
                
            except Exception as e:
                logger.error(f"Periodic knowledge update error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
                
    def _update_performance_metrics(self, job_type: str, result: Dict[str, Any]):
        """Update performance metrics with job result."""
        self.performance_metrics['total_jobs_executed'] += 1
        
        if job_type == 'quantum':
            # Update quantum metrics
            current_rate = self.performance_metrics['quantum_success_rate']
            total_quantum_jobs = getattr(self, '_quantum_job_count', 0) + 1
            setattr(self, '_quantum_job_count', total_quantum_jobs)
            
            if result['success']:
                new_rate = ((current_rate * (total_quantum_jobs - 1)) + 1) / total_quantum_jobs
            else:
                new_rate = (current_rate * (total_quantum_jobs - 1)) / total_quantum_jobs
                
            self.performance_metrics['quantum_success_rate'] = new_rate
            
            if result.get('execution_time'):
                current_avg = self.performance_metrics['average_quantum_time']
                new_avg = ((current_avg * (total_quantum_jobs - 1)) + result['execution_time']) / total_quantum_jobs
                self.performance_metrics['average_quantum_time'] = new_avg
                
        elif job_type == 'hpc':
            # Update HPC metrics
            current_rate = self.performance_metrics['hpc_success_rate']
            total_hpc_jobs = getattr(self, '_hpc_job_count', 0) + 1
            setattr(self, '_hpc_job_count', total_hpc_jobs)
            
            if result['success']:
                new_rate = ((current_rate * (total_hpc_jobs - 1)) + 1) / total_hpc_jobs
            else:
                new_rate = (current_rate * (total_hpc_jobs - 1)) / total_hpc_jobs
                
            self.performance_metrics['hpc_success_rate'] = new_rate
            
            if result.get('execution_time'):
                current_avg = self.performance_metrics['average_hpc_time']
                new_avg = ((current_avg * (total_hpc_jobs - 1)) + result['execution_time']) / total_hpc_jobs
                self.performance_metrics['average_hpc_time'] = new_avg
                
    async def _calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics."""
        try:
            # Get job statistics
            quantum_stats = self.quantum_executor.get_job_stats()
            hpc_stats = self.hpc_dispatcher.get_job_stats()
            
            # Update performance metrics
            if quantum_stats['total_jobs'] > 0:
                self.performance_metrics['quantum_success_rate'] = quantum_stats['success_rate']
                self.performance_metrics['average_quantum_time'] = quantum_stats['average_execution_time']
                
            if hpc_stats['total_jobs'] > 0:
                self.performance_metrics['hpc_success_rate'] = hpc_stats['success_rate']
                
        except Exception as e:
            logger.warning(f"Failed to calculate performance metrics: {e}")
            
    async def _update_fusion_weights(self):
        """Update fusion system weights based on performance."""
        try:
            # Get model performance metrics
            model_metrics = {}
            
            # For now, use overall success rates
            model_metrics['deepseek-coder'] = self.performance_metrics['quantum_success_rate']
            model_metrics['codellama'] = (self.performance_metrics['quantum_success_rate'] + 
                                        self.performance_metrics['hpc_success_rate']) / 2
            model_metrics['phu'] = self.performance_metrics['hpc_success_rate']
            
            # Get job success rates by backend
            job_success_rates = {
                'quantum_total': self.performance_metrics['quantum_success_rate'],
                'hpc_total': self.performance_metrics['hpc_success_rate']
            }
            
            # Update fusion weights
            await self.fusion_updater.update_fusion_weights(
                model_metrics,
                job_success_rates
            )
            
        except Exception as e:
            logger.warning(f"Failed to update fusion weights: {e}")
            
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'running': self.running,
            'uptime_seconds': uptime,
            'performance_metrics': self.performance_metrics,
            'quantum_executor_status': self.quantum_executor.get_backend_status(),
            'hpc_dispatcher_status': self.hpc_dispatcher.get_cluster_status(),
            'knowledge_base_stats': self.knowledge_ingestor.get_knowledge_stats(),
            'fusion_integration_stats': self.fusion_updater.get_fusion_integration_stats(),
            'job_logger_stats': self.job_logger.get_job_stats(),
            'security_status': self.safeguards.get_security_status()
        }
        
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive agent report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'agent_status': self.get_agent_status(),
            'recent_jobs': self.job_logger.get_job_history(20),
            'security_incidents': self.safeguards.get_recent_incidents(24),
            'knowledge_insights': self.knowledge_ingestor.get_knowledge_stats(),
            'fusion_updates': self.fusion_updater.get_update_history(10)
        } 