"""
Supercomputer Dispatcher for Autonomous AI Agent Framework

Submits and manages batch jobs on supercomputing clusters using SLURM,
PBS, or direct MPI execution via secure SSH connections.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import tempfile
import json
import re
import traceback

try:
    import paramiko
    from scp import SCPClient
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    import fabric
    from fabric import Connection
    FABRIC_AVAILABLE = True
except ImportError:
    FABRIC_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class JobScheduler(Enum):
    """Supported job schedulers"""
    SLURM = "slurm"
    PBS = "pbs"
    SGE = "sge"
    DIRECT = "direct"  # Direct execution without scheduler


class JobStatus(Enum):
    """Job status values"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class HPCCluster:
    """Represents an HPC cluster configuration"""
    name: str
    hostname: str
    username: str
    key_path: str
    scheduler: JobScheduler
    max_nodes: int = 1
    max_walltime_hours: int = 24
    default_partition: Optional[str] = None
    modules_to_load: List[str] = None
    
    def __post_init__(self):
        if self.modules_to_load is None:
            self.modules_to_load = []


@dataclass
class HPCJob:
    """Represents an HPC job"""
    job_id: str
    cluster_name: str
    scheduler_job_id: Optional[str] = None
    job_script: str = ""
    job_type: str = "batch"  # batch, interactive, mpi
    nodes: int = 1
    cpus_per_task: int = 1
    memory_gb: int = 4
    walltime_hours: int = 1
    partition: Optional[str] = None
    working_directory: str = "."
    output_file: Optional[str] = None
    error_file: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'status': self.status.value,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class SupercomputerDispatcher:
    """
    Manages job submission and execution on supercomputing clusters
    using various job schedulers and secure SSH connections.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the supercomputer dispatcher.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Safety limits
        self.max_jobs_per_hour = int(os.getenv('MAX_SLURM_JOBS_PER_HOUR', 10))
        self.max_walltime_hours = int(os.getenv('MAX_HPC_WALLTIME_HOURS', 24))
        
        # Job tracking
        self.active_jobs: Dict[str, HPCJob] = {}
        self.job_history: List[HPCJob] = []
        self.job_submission_times: List[datetime] = []
        
        # Cluster configurations
        self.clusters: Dict[str, HPCCluster] = {}
        self._initialize_clusters()
        
        # SSH connections cache
        self.connections: Dict[str, Any] = {}
        
        logger.info("Supercomputer Dispatcher initialized")
        
    def _initialize_clusters(self):
        """Initialize HPC cluster configurations."""
        # MIT SuperCloud
        mit_host = os.getenv('MIT_SUPERCLOUD_HOST')
        mit_user = os.getenv('MIT_SUPERCLOUD_USERNAME')
        mit_key = os.getenv('MIT_SUPERCLOUD_KEY_PATH')
        
        if mit_host and mit_user and mit_key:
            self.clusters['mit_supercloud'] = HPCCluster(
                name='mit_supercloud',
                hostname=mit_host,
                username=mit_user,
                key_path=mit_key,
                scheduler=JobScheduler.SLURM,
                max_nodes=16,
                max_walltime_hours=24,
                modules_to_load=['python/3.9', 'openmpi/4.1']
            )
            
        # TACC Stampede2
        tacc_host = os.getenv('TACC_HOST')
        tacc_user = os.getenv('TACC_USERNAME')
        tacc_key = os.getenv('TACC_KEY_PATH')
        
        if tacc_host and tacc_user and tacc_key:
            self.clusters['tacc_stampede2'] = HPCCluster(
                name='tacc_stampede2',
                hostname=tacc_host,
                username=tacc_user,
                key_path=tacc_key,
                scheduler=JobScheduler.SLURM,
                max_nodes=256,
                max_walltime_hours=48,
                default_partition='skx-normal',
                modules_to_load=['python3', 'impi']
            )
            
        # NERSC Cori
        nersc_host = os.getenv('NERSC_HOST')
        nersc_user = os.getenv('NERSC_USERNAME')
        nersc_key = os.getenv('NERSC_KEY_PATH')
        
        if nersc_host and nersc_user and nersc_key:
            self.clusters['nersc_cori'] = HPCCluster(
                name='nersc_cori',
                hostname=nersc_host,
                username=nersc_user,
                key_path=nersc_key,
                scheduler=JobScheduler.SLURM,
                max_nodes=64,
                max_walltime_hours=24,
                modules_to_load=['python', 'cray-mpich']
            )
            
        # Custom HPC cluster
        custom_host = os.getenv('CUSTOM_HPC_HOST')
        custom_user = os.getenv('CUSTOM_HPC_USERNAME')
        custom_key = os.getenv('CUSTOM_HPC_KEY_PATH')
        
        if custom_host and custom_user and custom_key:
            self.clusters['custom_hpc'] = HPCCluster(
                name='custom_hpc',
                hostname=custom_host,
                username=custom_user,
                key_path=custom_key,
                scheduler=JobScheduler.SLURM,
                max_nodes=32,
                max_walltime_hours=24,
                modules_to_load=['python', 'openmpi']
            )
            
        logger.info(f"Initialized {len(self.clusters)} HPC cluster configurations")
        
    async def run_on_supercomputer(self,
                                  cluster_name: str,
                                  job_script: str,
                                  job_type: str = "batch",
                                  nodes: int = 1,
                                  cpus_per_task: int = 1,
                                  memory_gb: int = 4,
                                  walltime_hours: int = 1,
                                  partition: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit and execute a job on a supercomputer.
        
        Args:
            cluster_name: Name of target cluster
            job_script: Job script content or command
            job_type: Type of job (batch, interactive, mpi)
            nodes: Number of nodes to request
            cpus_per_task: CPUs per task
            memory_gb: Memory in GB
            walltime_hours: Wall time in hours
            partition: Specific partition/queue
            
        Returns:
            Dictionary with job results
        """
        if not PARAMIKO_AVAILABLE:
            raise ImportError("Paramiko is required for SSH connections")
            
        # Safety checks
        safety_result = self._safety_check(cluster_name, nodes, walltime_hours, job_script)
        if not safety_result['safe']:
            raise ValueError(f"Safety check failed: {safety_result['reason']}")
            
        # Get cluster configuration
        if cluster_name not in self.clusters:
            raise ValueError(f"Unknown cluster: {cluster_name}")
            
        cluster = self.clusters[cluster_name]
        
        # Create job record
        job_id = f"hpc_{cluster_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        job = HPCJob(
            job_id=job_id,
            cluster_name=cluster_name,
            job_script=job_script,
            job_type=job_type,
            nodes=min(nodes, cluster.max_nodes),
            cpus_per_task=cpus_per_task,
            memory_gb=memory_gb,
            walltime_hours=min(walltime_hours, cluster.max_walltime_hours),
            partition=partition or cluster.default_partition,
            submitted_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job
        
        try:
            logger.info(f"Submitting HPC job {job_id} to {cluster_name}")
            
            # Connect to cluster
            connection = await self._get_connection(cluster)
            
            # Submit job based on scheduler type
            if cluster.scheduler == JobScheduler.SLURM:
                result = await self._submit_slurm_job(connection, cluster, job)
            elif cluster.scheduler == JobScheduler.PBS:
                result = await self._submit_pbs_job(connection, cluster, job)
            elif cluster.scheduler == JobScheduler.DIRECT:
                result = await self._execute_direct_job(connection, cluster, job)
            else:
                raise ValueError(f"Unsupported scheduler: {cluster.scheduler}")
                
            # Update job with results
            job.status = JobStatus.COMPLETED if result['success'] else JobStatus.FAILED
            job.completed_at = datetime.now()
            job.result = result
            
            if not result['success']:
                job.error = result.get('error', 'Unknown error')
                
            logger.info(f"HPC job {job_id} {'completed' if result['success'] else 'failed'}")
            
            return {
                'success': result['success'],
                'job_id': job_id,
                'cluster': cluster_name,
                'scheduler_job_id': job.scheduler_job_id,
                'result': result,
                'execution_time': (job.completed_at - job.submitted_at).total_seconds()
            }
            
        except Exception as e:
            # Update job with failure
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error = str(e)
            
            logger.error(f"HPC job {job_id} failed: {e}")
            
            return {
                'success': False,
                'job_id': job_id,
                'cluster': cluster_name,
                'error': str(e)
            }
            
        finally:
            # Move to history
            if job_id in self.active_jobs:
                self.job_history.append(self.active_jobs[job_id])
                del self.active_jobs[job_id]
                
                # Limit history size
                if len(self.job_history) > 1000:
                    self.job_history = self.job_history[-1000:]
                    
    def _safety_check(self, cluster_name: str, nodes: int, walltime_hours: int, 
                     job_script: str) -> Dict[str, Any]:
        """Perform safety checks on job parameters."""
        try:
            # Check rate limiting
            now = datetime.now()
            recent_submissions = [
                t for t in self.job_submission_times
                if (now - t).total_seconds() < 3600  # Last hour
            ]
            
            if len(recent_submissions) >= self.max_jobs_per_hour:
                return {
                    'safe': False,
                    'reason': f'Job rate limit exceeded: {len(recent_submissions)}/{self.max_jobs_per_hour} per hour'
                }
                
            # Check walltime
            if walltime_hours > self.max_walltime_hours:
                return {
                    'safe': False,
                    'reason': f'Walltime ({walltime_hours}h) exceeds limit ({self.max_walltime_hours}h)'
                }
                
            # Check for dangerous patterns in job script
            dangerous_patterns = [
                'rm -rf /',
                'format',
                'mkfs',
                'dd if=/dev/zero',
                'fork()',
                'while true',
                'sudo',
                'su -'
            ]
            
            script_lower = job_script.lower()
            for pattern in dangerous_patterns:
                if pattern in script_lower:
                    return {
                        'safe': False,
                        'reason': f'Dangerous pattern detected: {pattern}'
                    }
                    
            # Record submission time
            self.job_submission_times.append(now)
            
            # Clean old submission times
            cutoff = now - timedelta(hours=1)
            self.job_submission_times = [
                t for t in self.job_submission_times if t > cutoff
            ]
            
            return {'safe': True, 'reason': 'Safety checks passed'}
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {'safe': False, 'reason': f'Safety check error: {str(e)}'}
            
    async def _get_connection(self, cluster: HPCCluster):
        """Get or create SSH connection to cluster."""
        if cluster.name in self.connections:
            connection = self.connections[cluster.name]
            # Test connection
            try:
                connection.run('echo "test"', hide=True)
                return connection
            except:
                # Connection failed, create new one
                pass
                
        # Create new connection
        try:
            if FABRIC_AVAILABLE:
                # Use Fabric for easier connection management
                connection = Connection(
                    host=cluster.hostname,
                    user=cluster.username,
                    connect_kwargs={"key_filename": cluster.key_path}
                )
                connection.open()
                self.connections[cluster.name] = connection
                return connection
            else:
                # Use paramiko directly
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    hostname=cluster.hostname,
                    username=cluster.username,
                    key_filename=cluster.key_path
                )
                self.connections[cluster.name] = ssh
                return ssh
                
        except Exception as e:
            logger.error(f"Failed to connect to {cluster.name}: {e}")
            raise
            
    async def _submit_slurm_job(self, connection, cluster: HPCCluster, job: HPCJob) -> Dict[str, Any]:
        """Submit job using SLURM scheduler."""
        try:
            # Generate SLURM script
            slurm_script = self._generate_slurm_script(cluster, job)
            
            # Write script to temporary file on cluster
            script_path = f"/tmp/job_{job.job_id}.sh"
            
            if FABRIC_AVAILABLE:
                # Use Fabric
                connection.put(io.StringIO(slurm_script), script_path)
                connection.run(f"chmod +x {script_path}")
                
                # Submit job
                result = connection.run(f"sbatch {script_path}", hide=True)
                output = result.stdout.strip()
                
                # Parse job ID
                match = re.search(r'Submitted batch job (\d+)', output)
                if match:
                    job.scheduler_job_id = match.group(1)
                    
                # Wait for job completion (simplified - would be more sophisticated in production)
                await self._wait_for_slurm_job(connection, job.scheduler_job_id)
                
                # Get job output
                job_output = connection.run(f"cat slurm-{job.scheduler_job_id}.out", hide=True, warn=True)
                job_error = connection.run(f"cat slurm-{job.scheduler_job_id}.err", hide=True, warn=True)
                
                # Cleanup
                connection.run(f"rm -f {script_path} slurm-{job.scheduler_job_id}.out slurm-{job.scheduler_job_id}.err", warn=True)
                
                return {
                    'success': True,
                    'scheduler_job_id': job.scheduler_job_id,
                    'output': job_output.stdout if job_output.ok else '',
                    'error': job_error.stdout if job_error.ok else '',
                    'scheduler': 'slurm'
                }
                
            else:
                # Use paramiko directly
                sftp = connection.open_sftp()
                with sftp.file(script_path, 'w') as f:
                    f.write(slurm_script)
                sftp.close()
                
                # Submit job
                stdin, stdout, stderr = connection.exec_command(f"sbatch {script_path}")
                output = stdout.read().decode().strip()
                
                # Parse job ID
                match = re.search(r'Submitted batch job (\d+)', output)
                if match:
                    job.scheduler_job_id = match.group(1)
                    
                    # Wait for completion (simplified)
                    await asyncio.sleep(30)  # Wait a bit for job to complete
                    
                    # Get output
                    stdin, stdout, stderr = connection.exec_command(f"cat slurm-{job.scheduler_job_id}.out")
                    job_output = stdout.read().decode()
                    
                    return {
                        'success': True,
                        'scheduler_job_id': job.scheduler_job_id,
                        'output': job_output,
                        'scheduler': 'slurm'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to submit SLURM job: {output}'
                    }
                    
        except Exception as e:
            logger.error(f"SLURM job submission failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _generate_slurm_script(self, cluster: HPCCluster, job: HPCJob) -> str:
        """Generate SLURM batch script."""
        script_lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name={job.job_id}",
            f"#SBATCH --nodes={job.nodes}",
            f"#SBATCH --ntasks-per-node={job.cpus_per_task}",
            f"#SBATCH --mem={job.memory_gb}GB",
            f"#SBATCH --time={job.walltime_hours:02d}:00:00",
            f"#SBATCH --output=slurm-%j.out",
            f"#SBATCH --error=slurm-%j.err"
        ]
        
        if job.partition:
            script_lines.append(f"#SBATCH --partition={job.partition}")
            
        script_lines.extend([
            "",
            "# Load modules"
        ])
        
        for module in cluster.modules_to_load:
            script_lines.append(f"module load {module}")
            
        script_lines.extend([
            "",
            "# Change to working directory",
            f"cd {job.working_directory}",
            "",
            "# Execute job",
            job.job_script
        ])
        
        return "\n".join(script_lines)
        
    async def _wait_for_slurm_job(self, connection, job_id: str, timeout_minutes: int = 30):
        """Wait for SLURM job to complete."""
        if not job_id:
            return
            
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            try:
                if FABRIC_AVAILABLE:
                    result = connection.run(f"squeue -j {job_id}", hide=True, warn=True)
                    if result.return_code != 0 or job_id not in result.stdout:
                        # Job finished
                        break
                else:
                    stdin, stdout, stderr = connection.exec_command(f"squeue -j {job_id}")
                    output = stdout.read().decode()
                    if job_id not in output:
                        # Job finished
                        break
                        
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.warning(f"Error checking job status: {e}")
                break
                
    async def _submit_pbs_job(self, connection, cluster: HPCCluster, job: HPCJob) -> Dict[str, Any]:
        """Submit job using PBS scheduler."""
        # Similar to SLURM but using qsub
        try:
            pbs_script = self._generate_pbs_script(cluster, job)
            script_path = f"/tmp/job_{job.job_id}.pbs"
            
            if FABRIC_AVAILABLE:
                connection.put(io.StringIO(pbs_script), script_path)
                result = connection.run(f"qsub {script_path}", hide=True)
                job.scheduler_job_id = result.stdout.strip()
                
                return {
                    'success': True,
                    'scheduler_job_id': job.scheduler_job_id,
                    'scheduler': 'pbs'
                }
            else:
                # Paramiko implementation
                return {'success': False, 'error': 'PBS support requires Fabric'}
                
        except Exception as e:
            logger.error(f"PBS job submission failed: {e}")
            return {'success': False, 'error': str(e)}
            
    def _generate_pbs_script(self, cluster: HPCCluster, job: HPCJob) -> str:
        """Generate PBS batch script."""
        script_lines = [
            "#!/bin/bash",
            f"#PBS -N {job.job_id}",
            f"#PBS -l nodes={job.nodes}:ppn={job.cpus_per_task}",
            f"#PBS -l mem={job.memory_gb}gb",
            f"#PBS -l walltime={job.walltime_hours:02d}:00:00",
            "#PBS -o $PBS_JOBID.out",
            "#PBS -e $PBS_JOBID.err"
        ]
        
        if job.partition:
            script_lines.append(f"#PBS -q {job.partition}")
            
        script_lines.extend([
            "",
            "cd $PBS_O_WORKDIR",
            "",
            job.job_script
        ])
        
        return "\n".join(script_lines)
        
    async def _execute_direct_job(self, connection, cluster: HPCCluster, job: HPCJob) -> Dict[str, Any]:
        """Execute job directly without scheduler."""
        try:
            if FABRIC_AVAILABLE:
                result = connection.run(job.job_script, hide=True, warn=True)
                return {
                    'success': result.return_code == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.return_code != 0 else '',
                    'return_code': result.return_code
                }
            else:
                stdin, stdout, stderr = connection.exec_command(job.job_script)
                output = stdout.read().decode()
                error = stderr.read().decode()
                return_code = stdout.channel.recv_exit_status()
                
                return {
                    'success': return_code == 0,
                    'output': output,
                    'error': error if return_code != 0 else '',
                    'return_code': return_code
                }
                
        except Exception as e:
            logger.error(f"Direct job execution failed: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get status of all configured clusters."""
        status = {
            'total_clusters': len(self.clusters),
            'active_jobs': len(self.active_jobs),
            'total_jobs_executed': len(self.job_history),
            'clusters': {}
        }
        
        for name, cluster in self.clusters.items():
            cluster_status = {
                'hostname': cluster.hostname,
                'scheduler': cluster.scheduler.value,
                'max_nodes': cluster.max_nodes,
                'connected': name in self.connections
            }
            status['clusters'][name] = cluster_status
            
        return status
        
    def get_job_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent job execution history."""
        recent_jobs = self.job_history[-limit:] if self.job_history else []
        return [job.to_dict() for job in recent_jobs]
        
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        if not self.job_history:
            return {'total_jobs': 0}
            
        successful_jobs = [job for job in self.job_history if job.status == JobStatus.COMPLETED]
        failed_jobs = [job for job in self.job_history if job.status == JobStatus.FAILED]
        
        # Cluster usage statistics
        cluster_usage = {}
        for job in self.job_history:
            cluster = job.cluster_name
            cluster_usage[cluster] = cluster_usage.get(cluster, 0) + 1
            
        return {
            'total_jobs': len(self.job_history),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': len(failed_jobs),
            'success_rate': len(successful_jobs) / len(self.job_history),
            'cluster_usage': cluster_usage,
            'active_jobs': len(self.active_jobs),
            'recent_submissions_per_hour': len([
                t for t in self.job_submission_times
                if (datetime.now() - t).total_seconds() < 3600
            ])
        }
        
    def cleanup_connections(self):
        """Clean up SSH connections."""
        for name, connection in self.connections.items():
            try:
                if FABRIC_AVAILABLE and hasattr(connection, 'close'):
                    connection.close()
                elif hasattr(connection, 'close'):
                    connection.close()
                logger.info(f"Closed connection to {name}")
            except:
                pass
                
        self.connections.clear() 