"""
Job Logger for Autonomous AI Agent Framework

Comprehensive logging and tracking of quantum computing and HPC jobs
with performance metrics, success rates, and detailed analytics.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Types of jobs that can be logged"""
    QUANTUM_CIRCUIT = "quantum_circuit"
    QUANTUM_ALGORITHM = "quantum_algorithm"
    QUANTUM_SIMULATION = "quantum_simulation"
    HPC_BATCH = "hpc_batch"
    HPC_INTERACTIVE = "hpc_interactive"
    HPC_MPI = "hpc_mpi"
    HYBRID_QUANTUM_HPC = "hybrid_quantum_hpc"


class JobPlatform(Enum):
    """Platforms where jobs can be executed"""
    QISKIT_SIMULATOR = "qiskit_simulator"
    QISKIT_IBM = "qiskit_ibm"
    CIRQ_SIMULATOR = "cirq_simulator"
    CIRQ_GOOGLE = "cirq_google"
    PENNYLANE = "pennylane"
    DWAVE = "dwave"
    MIT_SUPERCLOUD = "mit_supercloud"
    TACC_STAMPEDE2 = "tacc_stampede2"
    NERSC_CORI = "nersc_cori"
    CUSTOM_HPC = "custom_hpc"


@dataclass
class JobRecord:
    """Comprehensive record of a job execution"""
    # Basic identification
    job_id: str
    external_job_id: Optional[str]  # Scheduler job ID or quantum job ID
    job_type: JobType
    platform: JobPlatform
    
    # Timing information
    created_at: datetime
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Job specification
    description: str = ""
    code_snippet: str = ""
    parameters: Dict[str, Any] = None
    resource_requirements: Dict[str, Any] = None
    
    # Execution results
    status: str = "created"  # created, submitted, running, completed, failed, cancelled
    success: bool = False
    output: Optional[str] = None
    error_message: Optional[str] = None
    
    # Performance metrics
    queue_time_seconds: Optional[float] = None
    execution_time_seconds: Optional[float] = None
    total_time_seconds: Optional[float] = None
    
    # Platform-specific metrics
    quantum_metrics: Optional[Dict[str, Any]] = None  # shots, qubits, fidelity, etc.
    hpc_metrics: Optional[Dict[str, Any]] = None      # nodes, cpus, memory, etc.
    
    # Cost and resource usage
    cost_estimate: Optional[float] = None
    resource_usage: Optional[Dict[str, Any]] = None
    
    # Quality metrics
    correctness_score: Optional[float] = None
    performance_score: Optional[float] = None
    efficiency_score: Optional[float] = None
    
    # Metadata
    tags: List[str] = None
    user_notes: str = ""
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.resource_requirements is None:
            self.resource_requirements = {}
        if self.tags is None:
            self.tags = []
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'job_type': self.job_type.value,
            'platform': self.platform.value,
            'created_at': self.created_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobRecord':
        """Create from dictionary."""
        # Convert enum fields
        data['job_type'] = JobType(data['job_type'])
        data['platform'] = JobPlatform(data['platform'])
        
        # Convert datetime fields
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('submitted_at'):
            data['submitted_at'] = datetime.fromisoformat(data['submitted_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
            
        return cls(**data)


class JobLogger:
    """
    Comprehensive job logging system for quantum and HPC jobs
    with analytics, performance tracking, and reporting capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the job logger.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Storage configuration
        self.data_dir = Path("quantum_agent/memory")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.data_dir / "job_log.json"
        self.analytics_file = self.data_dir / "job_analytics.json"
        
        # Job tracking
        self.active_jobs: Dict[str, JobRecord] = {}
        self.job_history: List[JobRecord] = []
        
        # Analytics tracking
        self.platform_stats: Dict[str, Dict[str, Any]] = {}
        self.performance_trends: List[Dict[str, Any]] = []
        
        # Load existing data
        self._load_job_history()
        self._load_analytics()
        
        logger.info("Job Logger initialized")
        
    def _load_job_history(self):
        """Load existing job history from file."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    
                self.job_history = [JobRecord.from_dict(job_data) for job_data in data.get('jobs', [])]
                
                logger.info(f"Loaded {len(self.job_history)} job records from history")
                
        except Exception as e:
            logger.warning(f"Failed to load job history: {e}")
            self.job_history = []
            
    def _load_analytics(self):
        """Load existing analytics data."""
        try:
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r') as f:
                    data = json.load(f)
                    
                self.platform_stats = data.get('platform_stats', {})
                self.performance_trends = data.get('performance_trends', [])
                
                logger.info("Loaded analytics data")
                
        except Exception as e:
            logger.warning(f"Failed to load analytics: {e}")
            self.platform_stats = {}
            self.performance_trends = []
            
    def create_job(self, 
                   job_type: JobType,
                   platform: JobPlatform,
                   description: str,
                   code_snippet: str = "",
                   parameters: Optional[Dict[str, Any]] = None,
                   resource_requirements: Optional[Dict[str, Any]] = None,
                   tags: Optional[List[str]] = None) -> str:
        """
        Create a new job record.
        
        Args:
            job_type: Type of job
            platform: Target platform
            description: Job description
            code_snippet: Code or script content
            parameters: Job parameters
            resource_requirements: Resource requirements
            tags: Optional tags for categorization
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        job_record = JobRecord(
            job_id=job_id,
            external_job_id=None,
            job_type=job_type,
            platform=platform,
            created_at=datetime.now(),
            description=description,
            code_snippet=code_snippet,
            parameters=parameters or {},
            resource_requirements=resource_requirements or {},
            tags=tags or []
        )
        
        self.active_jobs[job_id] = job_record
        
        logger.info(f"Created job record: {job_id} ({job_type.value} on {platform.value})")
        
        return job_id
        
    def update_job_status(self, 
                         job_id: str,
                         status: str,
                         external_job_id: Optional[str] = None,
                         **kwargs) -> bool:
        """
        Update job status and timing information.
        
        Args:
            job_id: Job ID
            status: New status
            external_job_id: External job ID (scheduler/quantum job ID)
            **kwargs: Additional fields to update
            
        Returns:
            True if successful, False if job not found
        """
        job = self.active_jobs.get(job_id)
        if not job:
            # Check if job is in history
            for historical_job in self.job_history:
                if historical_job.job_id == job_id:
                    job = historical_job
                    break
                    
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return False
            
        # Update status
        old_status = job.status
        job.status = status
        
        if external_job_id:
            job.external_job_id = external_job_id
            
        # Update timing based on status
        now = datetime.now()
        
        if status == "submitted" and not job.submitted_at:
            job.submitted_at = now
        elif status == "running" and not job.started_at:
            job.started_at = now
            if job.submitted_at:
                job.queue_time_seconds = (now - job.submitted_at).total_seconds()
        elif status in ["completed", "failed", "cancelled"] and not job.completed_at:
            job.completed_at = now
            if job.started_at:
                job.execution_time_seconds = (now - job.started_at).total_seconds()
            if job.submitted_at:
                job.total_time_seconds = (now - job.submitted_at).total_seconds()
                
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
                
        logger.info(f"Updated job {job_id}: {old_status} -> {status}")
        
        # If job is completed, move to history
        if status in ["completed", "failed", "cancelled"] and job_id in self.active_jobs:
            self.job_history.append(self.active_jobs[job_id])
            del self.active_jobs[job_id]
            
            # Update analytics
            self._update_analytics(job)
            
            # Save data
            self._save_job_history()
            self._save_analytics()
            
        return True
        
    def log_quantum_job(self,
                       platform: JobPlatform,
                       circuit_code: str,
                       shots: int = 1024,
                       qubits: int = 1,
                       result: Optional[Dict[str, Any]] = None,
                       success: bool = True,
                       error: Optional[str] = None,
                       execution_time: Optional[float] = None) -> str:
        """
        Log a quantum computing job.
        
        Args:
            platform: Quantum platform used
            circuit_code: Quantum circuit code
            shots: Number of shots
            qubits: Number of qubits
            result: Execution result
            success: Whether job succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
            
        Returns:
            Job ID
        """
        # Determine job type based on code content
        code_lower = circuit_code.lower()
        if 'algorithm' in code_lower or 'vqe' in code_lower or 'qaoa' in code_lower:
            job_type = JobType.QUANTUM_ALGORITHM
        elif 'simulator' in str(platform).lower():
            job_type = JobType.QUANTUM_SIMULATION
        else:
            job_type = JobType.QUANTUM_CIRCUIT
            
        # Create job record
        job_id = self.create_job(
            job_type=job_type,
            platform=platform,
            description=f"Quantum job: {shots} shots, {qubits} qubits",
            code_snippet=circuit_code,
            parameters={
                'shots': shots,
                'qubits': qubits
            },
            resource_requirements={
                'qubits': qubits,
                'shots': shots
            },
            tags=['quantum', str(platform).split('.')[-1]]
        )
        
        # Update with results
        quantum_metrics = {
            'shots': shots,
            'qubits': qubits,
            'backend': str(platform).split('.')[-1]
        }
        
        if result:
            quantum_metrics.update({
                'result_type': type(result).__name__,
                'result_size': len(str(result))
            })
            
            # Extract quantum-specific metrics
            if isinstance(result, dict):
                if 'counts' in result:
                    quantum_metrics['measurement_counts'] = len(result['counts'])
                if 'fidelity' in result:
                    quantum_metrics['fidelity'] = result['fidelity']
                if 'backend_name' in result:
                    quantum_metrics['actual_backend'] = result['backend_name']
                    
        self.update_job_status(
            job_id,
            "completed" if success else "failed",
            success=success,
            output=json.dumps(result) if result else None,
            error_message=error,
            execution_time_seconds=execution_time,
            quantum_metrics=quantum_metrics
        )
        
        return job_id
        
    def log_hpc_job(self,
                   platform: JobPlatform,
                   job_script: str,
                   scheduler_job_id: Optional[str] = None,
                   nodes: int = 1,
                   cpus: int = 1,
                   memory_gb: int = 4,
                   walltime_hours: int = 1,
                   result: Optional[Dict[str, Any]] = None,
                   success: bool = True,
                   error: Optional[str] = None,
                   execution_time: Optional[float] = None) -> str:
        """
        Log an HPC job.
        
        Args:
            platform: HPC platform used
            job_script: Job script content
            scheduler_job_id: Scheduler job ID
            nodes: Number of nodes
            cpus: Number of CPUs
            memory_gb: Memory in GB
            walltime_hours: Walltime in hours
            result: Execution result
            success: Whether job succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
            
        Returns:
            Job ID
        """
        # Determine job type based on script content
        script_lower = job_script.lower()
        if 'mpirun' in script_lower or 'mpiexec' in script_lower:
            job_type = JobType.HPC_MPI
        elif 'interactive' in script_lower:
            job_type = JobType.HPC_INTERACTIVE
        else:
            job_type = JobType.HPC_BATCH
            
        # Create job record
        job_id = self.create_job(
            job_type=job_type,
            platform=platform,
            description=f"HPC job: {nodes} nodes, {cpus} CPUs, {memory_gb}GB RAM",
            code_snippet=job_script,
            parameters={
                'nodes': nodes,
                'cpus': cpus,
                'memory_gb': memory_gb,
                'walltime_hours': walltime_hours
            },
            resource_requirements={
                'nodes': nodes,
                'cpus_per_node': cpus,
                'memory_gb': memory_gb,
                'walltime_hours': walltime_hours
            },
            tags=['hpc', str(platform).split('.')[-1]]
        )
        
        # Update with results
        hpc_metrics = {
            'nodes': nodes,
            'cpus': cpus,
            'memory_gb': memory_gb,
            'walltime_hours': walltime_hours,
            'cluster': str(platform).split('.')[-1]
        }
        
        if result:
            hpc_metrics.update({
                'exit_code': result.get('return_code', 0),
                'output_size': len(result.get('output', '')),
                'error_size': len(result.get('error', ''))
            })
            
        self.update_job_status(
            job_id,
            "completed" if success else "failed",
            external_job_id=scheduler_job_id,
            success=success,
            output=result.get('output') if result else None,
            error_message=error or (result.get('error') if result else None),
            execution_time_seconds=execution_time,
            hpc_metrics=hpc_metrics
        )
        
        return job_id
        
    def _update_analytics(self, job: JobRecord):
        """Update analytics with completed job data."""
        platform_key = job.platform.value
        
        if platform_key not in self.platform_stats:
            self.platform_stats[platform_key] = {
                'total_jobs': 0,
                'successful_jobs': 0,
                'failed_jobs': 0,
                'total_execution_time': 0.0,
                'average_execution_time': 0.0,
                'job_types': {},
                'last_updated': datetime.now().isoformat()
            }
            
        stats = self.platform_stats[platform_key]
        
        # Update basic counts
        stats['total_jobs'] += 1
        if job.success:
            stats['successful_jobs'] += 1
        else:
            stats['failed_jobs'] += 1
            
        # Update execution time
        if job.execution_time_seconds:
            stats['total_execution_time'] += job.execution_time_seconds
            stats['average_execution_time'] = stats['total_execution_time'] / stats['total_jobs']
            
        # Update job type counts
        job_type_key = job.job_type.value
        if job_type_key not in stats['job_types']:
            stats['job_types'][job_type_key] = 0
        stats['job_types'][job_type_key] += 1
        
        stats['last_updated'] = datetime.now().isoformat()
        
        # Add to performance trends
        trend_entry = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform_key,
            'job_type': job_type_key,
            'success': job.success,
            'execution_time': job.execution_time_seconds,
            'queue_time': job.queue_time_seconds,
            'total_time': job.total_time_seconds
        }
        
        self.performance_trends.append(trend_entry)
        
        # Limit trend history
        if len(self.performance_trends) > 1000:
            self.performance_trends = self.performance_trends[-1000:]
            
    def _save_job_history(self):
        """Save job history to file."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_jobs': len(self.job_history),
                'jobs': [job.to_dict() for job in self.job_history]
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save job history: {e}")
            
    def _save_analytics(self):
        """Save analytics data to file."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'platform_stats': self.platform_stats,
                'performance_trends': self.performance_trends
            }
            
            with open(self.analytics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}")
            
    def get_job_stats(self, platform: Optional[JobPlatform] = None, 
                     days: int = 30) -> Dict[str, Any]:
        """
        Get job statistics.
        
        Args:
            platform: Optional platform filter
            days: Number of days to include
            
        Returns:
            Dictionary with job statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter jobs
        relevant_jobs = []
        for job in self.job_history:
            if job.created_at > cutoff_date:
                if platform is None or job.platform == platform:
                    relevant_jobs.append(job)
                    
        if not relevant_jobs:
            return {'total_jobs': 0, 'period_days': days}
            
        # Calculate statistics
        successful_jobs = [j for j in relevant_jobs if j.success]
        failed_jobs = [j for j in relevant_jobs if not j.success]
        
        # Execution times
        exec_times = [j.execution_time_seconds for j in relevant_jobs if j.execution_time_seconds]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Queue times
        queue_times = [j.queue_time_seconds for j in relevant_jobs if j.queue_time_seconds]
        avg_queue_time = sum(queue_times) / len(queue_times) if queue_times else 0
        
        # Platform distribution
        platform_dist = {}
        for job in relevant_jobs:
            platform_key = job.platform.value
            platform_dist[platform_key] = platform_dist.get(platform_key, 0) + 1
            
        # Job type distribution
        job_type_dist = {}
        for job in relevant_jobs:
            job_type_key = job.job_type.value
            job_type_dist[job_type_key] = job_type_dist.get(job_type_key, 0) + 1
            
        return {
            'period_days': days,
            'total_jobs': len(relevant_jobs),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': len(failed_jobs),
            'success_rate': len(successful_jobs) / len(relevant_jobs),
            'average_execution_time': avg_exec_time,
            'average_queue_time': avg_queue_time,
            'platform_distribution': platform_dist,
            'job_type_distribution': job_type_dist,
            'active_jobs': len(self.active_jobs)
        }
        
    def get_platform_performance(self, platform: JobPlatform, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for a specific platform."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        platform_jobs = [
            job for job in self.job_history
            if job.platform == platform and job.created_at > cutoff_date
        ]
        
        if not platform_jobs:
            return {'platform': platform.value, 'no_data': True}
            
        successful = [j for j in platform_jobs if j.success]
        
        # Calculate metrics
        success_rate = len(successful) / len(platform_jobs)
        
        exec_times = [j.execution_time_seconds for j in platform_jobs if j.execution_time_seconds]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Resource efficiency (for quantum jobs)
        quantum_jobs = [j for j in platform_jobs if j.quantum_metrics]
        avg_qubits = 0
        avg_shots = 0
        
        if quantum_jobs:
            qubits = [j.quantum_metrics.get('qubits', 0) for j in quantum_jobs]
            shots = [j.quantum_metrics.get('shots', 0) for j in quantum_jobs]
            avg_qubits = sum(qubits) / len(qubits) if qubits else 0
            avg_shots = sum(shots) / len(shots) if shots else 0
            
        return {
            'platform': platform.value,
            'period_days': days,
            'total_jobs': len(platform_jobs),
            'success_rate': success_rate,
            'average_execution_time': avg_exec_time,
            'quantum_metrics': {
                'average_qubits': avg_qubits,
                'average_shots': avg_shots,
                'quantum_jobs': len(quantum_jobs)
            } if quantum_jobs else None
        }
        
    def export_job_data(self, output_path: str, days: Optional[int] = None) -> Dict[str, Any]:
        """Export job data for analysis."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days) if days else None
            
            export_jobs = []
            for job in self.job_history:
                if cutoff_date is None or job.created_at > cutoff_date:
                    export_jobs.append(job.to_dict())
                    
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_jobs': len(export_jobs),
                'period_days': days,
                'platform_stats': self.platform_stats,
                'jobs': export_jobs
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_path': output_path,
                'exported_jobs': len(export_jobs),
                'file_size_mb': os.path.getsize(output_path) / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"Failed to export job data: {e}")
            return {'success': False, 'error': str(e)} 