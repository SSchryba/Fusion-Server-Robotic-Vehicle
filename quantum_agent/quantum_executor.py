"""
Quantum Executor for Autonomous AI Agent Framework

Executes quantum circuits and algorithms on various quantum backends
including Qiskit (IBM), Cirq (Google), PennyLane, and D-Wave Ocean SDK.
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import traceback

# Quantum computing imports (with optional imports for graceful degradation)
try:
    import qiskit
    from qiskit import QuantumCircuit, transpile, execute
    from qiskit.providers.ibmq import IBMQ
    from qiskit_ibm_runtime import QiskitRuntimeService, Session, Estimator, Sampler
    from qiskit_ibm_provider import IBMProvider
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    
try:
    import cirq
    import cirq_google
    CIRQ_AVAILABLE = True
except ImportError:
    CIRQ_AVAILABLE = False
    
try:
    import pennylane as qml
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False
    
try:
    from dwave.system import DWaveSampler, EmbeddingComposite
    from dwave.cloud import Client
    import dimod
    DWAVE_AVAILABLE = True
except ImportError:
    DWAVE_AVAILABLE = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class QuantumBackend(Enum):
    """Supported quantum backends"""
    QISKIT_SIMULATOR = "qiskit_simulator"
    QISKIT_IBM = "qiskit_ibm"
    CIRQ_SIMULATOR = "cirq_simulator"
    CIRQ_GOOGLE = "cirq_google"
    PENNYLANE_DEFAULT = "pennylane_default"
    PENNYLANE_LIGHTNING = "pennylane_lightning"
    DWAVE_SIMULATOR = "dwave_simulator"
    DWAVE_QUANTUM = "dwave_quantum"


@dataclass
class QuantumJob:
    """Represents a quantum computing job"""
    job_id: str
    backend: QuantumBackend
    circuit_code: str
    parameters: Dict[str, Any]
    created_at: datetime
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    shots: int = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'backend': self.backend.value,
            'created_at': self.created_at.isoformat()
        }


class QuantumExecutor:
    """
    Executes quantum circuits on various quantum computing backends
    with comprehensive error handling and result logging.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the quantum executor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Safety limits
        self.max_qubits_public = int(os.getenv('MAX_QUBITS_PUBLIC', 20))
        self.max_shots_public = int(os.getenv('MAX_SHOTS_PUBLIC', 8192))
        
        # Backend connections
        self.qiskit_service = None
        self.ibm_provider = None
        self.dwave_client = None
        
        # Job tracking
        self.active_jobs: Dict[str, QuantumJob] = {}
        self.job_history: List[QuantumJob] = []
        
        # Initialize backends
        self._initialize_backends()
        
        logger.info("Quantum Executor initialized")
        
    def _initialize_backends(self):
        """Initialize quantum backend connections."""
        try:
            # Initialize IBM Qiskit
            if QISKIT_AVAILABLE:
                self._initialize_qiskit()
                
            # Initialize D-Wave
            if DWAVE_AVAILABLE:
                self._initialize_dwave()
                
            logger.info("Quantum backends initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize quantum backends: {e}")
            
    def _initialize_qiskit(self):
        """Initialize IBM Qiskit backend."""
        try:
            token = os.getenv('IBMQ_API_TOKEN')
            if token:
                # Use new IBM Quantum Platform
                self.qiskit_service = QiskitRuntimeService(
                    channel="ibm_quantum",
                    token=token
                )
                
                # Also try the legacy provider for compatibility
                try:
                    self.ibm_provider = IBMProvider(token=token)
                except Exception:
                    pass
                    
                logger.info("IBM Qiskit backend initialized")
            else:
                logger.warning("IBMQ_API_TOKEN not found - IBM backends unavailable")
                
        except Exception as e:
            logger.error(f"Failed to initialize Qiskit: {e}")
            
    def _initialize_dwave(self):
        """Initialize D-Wave backend."""
        try:
            token = os.getenv('DWAVE_API_TOKEN')
            if token:
                self.dwave_client = Client.from_config(token=token)
                logger.info("D-Wave backend initialized")
            else:
                logger.warning("DWAVE_API_TOKEN not found - D-Wave backends unavailable")
                
        except Exception as e:
            logger.error(f"Failed to initialize D-Wave: {e}")
            
    async def run_on_quantum_backend(self, 
                                   circuit_code: str,
                                   backend: QuantumBackend,
                                   parameters: Optional[Dict[str, Any]] = None,
                                   shots: int = 1024) -> Dict[str, Any]:
        """
        Execute quantum code on specified backend.
        
        Args:
            circuit_code: Quantum circuit code to execute
            backend: Target quantum backend
            parameters: Additional parameters for execution
            shots: Number of shots for measurement
            
        Returns:
            Dictionary with execution results
        """
        job_id = f"quantum_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        # Create job record
        job = QuantumJob(
            job_id=job_id,
            backend=backend,
            circuit_code=circuit_code,
            parameters=parameters or {},
            created_at=start_time,
            shots=min(shots, self.max_shots_public)
        )
        
        self.active_jobs[job_id] = job
        
        try:
            logger.info(f"Executing quantum job {job_id} on {backend.value}")
            
            # Safety checks
            safety_result = self._safety_check(circuit_code, backend, shots)
            if not safety_result['safe']:
                raise ValueError(f"Safety check failed: {safety_result['reason']}")
                
            # Route to appropriate backend
            if backend in [QuantumBackend.QISKIT_SIMULATOR, QuantumBackend.QISKIT_IBM]:
                result = await self._execute_qiskit(circuit_code, backend, parameters, job.shots)
            elif backend in [QuantumBackend.CIRQ_SIMULATOR, QuantumBackend.CIRQ_GOOGLE]:
                result = await self._execute_cirq(circuit_code, backend, parameters, job.shots)
            elif backend in [QuantumBackend.PENNYLANE_DEFAULT, QuantumBackend.PENNYLANE_LIGHTNING]:
                result = await self._execute_pennylane(circuit_code, backend, parameters, job.shots)
            elif backend in [QuantumBackend.DWAVE_SIMULATOR, QuantumBackend.DWAVE_QUANTUM]:
                result = await self._execute_dwave(circuit_code, backend, parameters)
            else:
                raise ValueError(f"Unsupported backend: {backend}")
                
            # Update job with success
            execution_time = (datetime.now() - start_time).total_seconds()
            job.status = "completed"
            job.result = result
            job.execution_time = execution_time
            
            logger.info(f"Quantum job {job_id} completed successfully in {execution_time:.2f}s")
            
            return {
                'success': True,
                'job_id': job_id,
                'backend': backend.value,
                'result': result,
                'execution_time': execution_time,
                'shots': job.shots
            }
            
        except Exception as e:
            # Update job with failure
            execution_time = (datetime.now() - start_time).total_seconds()
            job.status = "failed"
            job.error = str(e)
            job.execution_time = execution_time
            
            logger.error(f"Quantum job {job_id} failed: {e}")
            
            return {
                'success': False,
                'job_id': job_id,
                'backend': backend.value,
                'error': str(e),
                'execution_time': execution_time
            }
            
        finally:
            # Move to history
            if job_id in self.active_jobs:
                self.job_history.append(self.active_jobs[job_id])
                del self.active_jobs[job_id]
                
                # Limit history size
                if len(self.job_history) > 1000:
                    self.job_history = self.job_history[-1000:]
                    
    def _safety_check(self, circuit_code: str, backend: QuantumBackend, shots: int) -> Dict[str, Any]:
        """Perform safety checks on quantum code."""
        try:
            # Check shots limit
            if shots > self.max_shots_public:
                return {
                    'safe': False,
                    'reason': f'Shots ({shots}) exceeds limit ({self.max_shots_public})'
                }
                
            # Basic code safety checks
            dangerous_patterns = [
                'import os',
                'import sys', 
                'subprocess',
                'eval(',
                'exec(',
                '__import__',
                'open(',
                'file('
            ]
            
            code_lower = circuit_code.lower()
            for pattern in dangerous_patterns:
                if pattern in code_lower:
                    return {
                        'safe': False,
                        'reason': f'Dangerous pattern detected: {pattern}'
                    }
                    
            # Check qubit count for Qiskit circuits
            if 'QuantumCircuit(' in circuit_code:
                try:
                    # Simple regex to extract qubit count - would need more robust parsing
                    import re
                    match = re.search(r'QuantumCircuit\((\d+)', circuit_code)
                    if match:
                        qubits = int(match.group(1))
                        if qubits > self.max_qubits_public:
                            return {
                                'safe': False,
                                'reason': f'Qubit count ({qubits}) exceeds limit ({self.max_qubits_public})'
                            }
                except:
                    pass  # If parsing fails, allow execution
                    
            return {'safe': True, 'reason': 'Safety checks passed'}
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {'safe': False, 'reason': f'Safety check error: {str(e)}'}
            
    async def _execute_qiskit(self, circuit_code: str, backend: QuantumBackend,
                             parameters: Dict[str, Any], shots: int) -> Dict[str, Any]:
        """Execute Qiskit quantum circuit."""
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is not available")
            
        try:
            # Create local namespace for circuit execution
            local_vars = {
                'qiskit': qiskit,
                'QuantumCircuit': QuantumCircuit,
                'transpile': transpile,
                'execute': execute
            }
            
            # Execute circuit code to get circuit object
            exec(circuit_code, local_vars)
            
            # Get the circuit (assume it's stored in 'circuit' variable)
            circuit = local_vars.get('circuit')
            if circuit is None:
                raise ValueError("Circuit code must define a 'circuit' variable")
                
            if backend == QuantumBackend.QISKIT_SIMULATOR:
                # Use Aer simulator
                from qiskit import Aer
                simulator = Aer.get_backend('qasm_simulator')
                job = execute(circuit, simulator, shots=shots)
                result = job.result()
                counts = result.get_counts(circuit)
                
                return {
                    'type': 'simulation',
                    'counts': counts,
                    'backend': 'qasm_simulator',
                    'shots': shots
                }
                
            elif backend == QuantumBackend.QISKIT_IBM:
                if not self.qiskit_service:
                    raise ValueError("IBM Quantum service not initialized")
                    
                # Get available backends
                backends = self.qiskit_service.backends()
                available_backends = [b for b in backends if b.configuration().n_qubits >= circuit.num_qubits]
                
                if not available_backends:
                    raise ValueError("No suitable IBM backends available")
                    
                # Select best available backend
                selected_backend = min(available_backends, key=lambda b: b.status().pending_jobs)
                
                # Transpile circuit
                transpiled_circuit = transpile(circuit, selected_backend)
                
                # Execute with runtime service
                with Session(service=self.qiskit_service, backend=selected_backend) as session:
                    sampler = Sampler(session=session)
                    job = sampler.run([transpiled_circuit], shots=shots)
                    result = job.result()
                    
                return {
                    'type': 'hardware',
                    'backend_name': selected_backend.name,
                    'job_id': job.job_id(),
                    'result': result.quasi_dists[0].binary_probabilities(),
                    'shots': shots
                }
                
        except Exception as e:
            logger.error(f"Qiskit execution failed: {e}")
            raise
            
    async def _execute_cirq(self, circuit_code: str, backend: QuantumBackend,
                           parameters: Dict[str, Any], shots: int) -> Dict[str, Any]:
        """Execute Cirq quantum circuit."""
        if not CIRQ_AVAILABLE:
            raise ImportError("Cirq is not available")
            
        try:
            # Create local namespace for circuit execution
            local_vars = {
                'cirq': cirq,
                'np': __import__('numpy')
            }
            
            # Execute circuit code
            exec(circuit_code, local_vars)
            
            # Get the circuit and qubits
            circuit = local_vars.get('circuit')
            if circuit is None:
                raise ValueError("Circuit code must define a 'circuit' variable")
                
            if backend == QuantumBackend.CIRQ_SIMULATOR:
                # Use Cirq simulator
                simulator = cirq.Simulator()
                result = simulator.run(circuit, repetitions=shots)
                
                return {
                    'type': 'simulation',
                    'measurements': str(result),
                    'backend': 'cirq_simulator',
                    'shots': shots
                }
                
            elif backend == QuantumBackend.CIRQ_GOOGLE:
                # Google Quantum hardware (if available)
                try:
                    # This would require Google Cloud credentials and access
                    project_id = os.getenv('GOOGLE_QUANTUM_PROJECT_ID')
                    if not project_id:
                        raise ValueError("Google Quantum project ID not configured")
                        
                    # Use Google's quantum processor
                    engine = cirq_google.Engine(project_id=project_id)
                    processor = engine.get_processor('rainbow')  # Example processor
                    
                    job = processor.run(circuit, repetitions=shots)
                    result = job.results()[0]
                    
                    return {
                        'type': 'hardware',
                        'backend': 'google_quantum',
                        'measurements': str(result),
                        'shots': shots
                    }
                    
                except Exception as e:
                    logger.warning(f"Google Quantum hardware unavailable: {e}")
                    # Fall back to simulator
                    return await self._execute_cirq(circuit_code, QuantumBackend.CIRQ_SIMULATOR, parameters, shots)
                    
        except Exception as e:
            logger.error(f"Cirq execution failed: {e}")
            raise
            
    async def _execute_pennylane(self, circuit_code: str, backend: QuantumBackend,
                                parameters: Dict[str, Any], shots: int) -> Dict[str, Any]:
        """Execute PennyLane quantum circuit."""
        if not PENNYLANE_AVAILABLE:
            raise ImportError("PennyLane is not available")
            
        try:
            # Create local namespace for circuit execution
            local_vars = {
                'qml': qml,
                'np': __import__('numpy')
            }
            
            # Set up device based on backend
            if backend == QuantumBackend.PENNYLANE_DEFAULT:
                device_name = 'default.qubit'
            elif backend == QuantumBackend.PENNYLANE_LIGHTNING:
                device_name = 'lightning.qubit'
            else:
                device_name = 'default.qubit'
                
            # Execute circuit code (should define a QNode)
            exec(circuit_code, local_vars)
            
            # Get the QNode or circuit function
            qnode = local_vars.get('qnode') or local_vars.get('circuit_func')
            if qnode is None:
                raise ValueError("Circuit code must define a 'qnode' or 'circuit_func' variable")
                
            # Execute the QNode
            result = qnode(**parameters)
            
            return {
                'type': 'simulation',
                'result': result.tolist() if hasattr(result, 'tolist') else result,
                'backend': device_name,
                'shots': shots
            }
            
        except Exception as e:
            logger.error(f"PennyLane execution failed: {e}")
            raise
            
    async def _execute_dwave(self, circuit_code: str, backend: QuantumBackend,
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute D-Wave quantum annealing problem."""
        if not DWAVE_AVAILABLE:
            raise ImportError("D-Wave Ocean SDK is not available")
            
        try:
            # Create local namespace for problem execution
            local_vars = {
                'dimod': dimod,
                'DWaveSampler': DWaveSampler,
                'EmbeddingComposite': EmbeddingComposite
            }
            
            # Execute problem code
            exec(circuit_code, local_vars)
            
            # Get the problem (BQM or similar)
            bqm = local_vars.get('bqm') or local_vars.get('problem')
            if bqm is None:
                raise ValueError("D-Wave code must define a 'bqm' or 'problem' variable")
                
            if backend == QuantumBackend.DWAVE_SIMULATOR:
                # Use simulated annealing
                sampler = dimod.SimulatedAnnealingSampler()
                response = sampler.sample(bqm, num_reads=100)
                
                return {
                    'type': 'simulation',
                    'samples': response.data_vectors['sample'],
                    'energies': response.data_vectors['energy'],
                    'backend': 'simulated_annealing'
                }
                
            elif backend == QuantumBackend.DWAVE_QUANTUM:
                if not self.dwave_client:
                    raise ValueError("D-Wave client not initialized")
                    
                # Use D-Wave quantum annealer
                sampler = EmbeddingComposite(DWaveSampler())
                response = sampler.sample(bqm, num_reads=100)
                
                return {
                    'type': 'hardware',
                    'samples': response.data_vectors['sample'],
                    'energies': response.data_vectors['energy'],
                    'backend': 'dwave_quantum',
                    'solver': sampler.child.solver.name
                }
                
        except Exception as e:
            logger.error(f"D-Wave execution failed: {e}")
            raise
            
    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all quantum backends."""
        status = {
            'qiskit_available': QISKIT_AVAILABLE,
            'cirq_available': CIRQ_AVAILABLE,
            'pennylane_available': PENNYLANE_AVAILABLE,
            'dwave_available': DWAVE_AVAILABLE,
            'active_jobs': len(self.active_jobs),
            'total_jobs_executed': len(self.job_history)
        }
        
        # Add backend-specific status
        if QISKIT_AVAILABLE and self.qiskit_service:
            try:
                backends = self.qiskit_service.backends()
                status['ibm_backends_available'] = len(backends)
            except:
                status['ibm_backends_available'] = 0
                
        if DWAVE_AVAILABLE and self.dwave_client:
            try:
                status['dwave_connected'] = True
            except:
                status['dwave_connected'] = False
                
        return status
        
    def get_job_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent job execution history."""
        recent_jobs = self.job_history[-limit:] if self.job_history else []
        return [job.to_dict() for job in recent_jobs]
        
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        if not self.job_history:
            return {'total_jobs': 0}
            
        successful_jobs = [job for job in self.job_history if job.status == 'completed']
        failed_jobs = [job for job in self.job_history if job.status == 'failed']
        
        # Backend usage statistics
        backend_usage = {}
        for job in self.job_history:
            backend = job.backend.value
            backend_usage[backend] = backend_usage.get(backend, 0) + 1
            
        # Average execution time
        exec_times = [job.execution_time for job in self.job_history if job.execution_time]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        return {
            'total_jobs': len(self.job_history),
            'successful_jobs': len(successful_jobs),
            'failed_jobs': len(failed_jobs),
            'success_rate': len(successful_jobs) / len(self.job_history),
            'average_execution_time': avg_exec_time,
            'backend_usage': backend_usage,
            'active_jobs': len(self.active_jobs)
        } 