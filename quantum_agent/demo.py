"""
Quantum Agent Demo Script

Demonstrates all capabilities of the quantum computing and supercomputing
integration system for the Autonomous AI Agent Framework.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import sys
import os

# Add quantum_agent to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quantum_agent_orchestrator import QuantumAgentOrchestrator
from quantum_executor import QuantumBackend
from job_logger import JobType, JobPlatform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuantumAgentDemo:
    """Comprehensive demonstration of quantum agent capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.orchestrator = QuantumAgentOrchestrator()
        
    async def run_full_demo(self):
        """Run the complete quantum agent demonstration."""
        print("🚀 Quantum Agent Framework Demo")
        print("=" * 50)
        
        try:
            # Start the orchestrator
            print("\n1. 🔧 Starting Quantum Agent Orchestrator...")
            await self.orchestrator.start()
            print("✅ Orchestrator started successfully")
            
            # Demo quantum computing capabilities
            print("\n2. ⚛️  Quantum Computing Demonstrations")
            await self.demo_quantum_computing()
            
            # Demo HPC capabilities
            print("\n3. 🖥️  HPC/Supercomputing Demonstrations")
            await self.demo_hpc_computing()
            
            # Demo knowledge management
            print("\n4. 🧠 Knowledge Management Demonstrations")
            await self.demo_knowledge_management()
            
            # Demo fusion integration
            print("\n5. 🔗 Fusion System Integration")
            await self.demo_fusion_integration()
            
            # Demo safety and monitoring
            print("\n6. 🛡️  Safety and Monitoring Demonstrations")
            await self.demo_safety_monitoring()
            
            # Show comprehensive status
            print("\n7. 📊 Comprehensive Status Report")
            await self.show_status_report()
            
            print("\n✅ Demo completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.error(f"Demo error: {e}")
            
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            await self.orchestrator.stop()
            print("✅ Cleanup completed")
            
    async def demo_quantum_computing(self):
        """Demonstrate quantum computing capabilities."""
        print("\n   📡 Quantum Circuit Execution")
        
        # Demo 1: Simple quantum circuit on simulator
        print("\n   🔸 Demo 1: Bell State Circuit (Simulator)")
        
        bell_circuit_code = """
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister

# Create Bell state circuit
qr = QuantumRegister(2, 'q')
cr = ClassicalRegister(2, 'c')
circuit = QuantumCircuit(qr, cr)

# Create Bell state
circuit.h(qr[0])  # Hadamard gate
circuit.cx(qr[0], qr[1])  # CNOT gate

# Measure
circuit.measure(qr, cr)
"""
        
        result = await self.orchestrator.execute_quantum_job(
            backend=QuantumBackend.QISKIT_SIMULATOR,
            circuit_code=bell_circuit_code,
            parameters={'shots': 1024, 'qubits': 2},
            description="Bell state demonstration"
        )
        
        print(f"     Result: {'✅ Success' if result['success'] else '❌ Failed'}")
        if result['success']:
            print(f"     Execution time: {result.get('execution_time', 0):.3f}s")
            print(f"     Job ID: {result['job_id']}")
        else:
            print(f"     Error: {result.get('error', 'Unknown')}")
            
        # Demo 2: Quantum algorithm simulation
        print("\n   🔸 Demo 2: Quantum Phase Estimation")
        
        qpe_circuit_code = """
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
import numpy as np

# Quantum Phase Estimation circuit
qr = QuantumRegister(4, 'q')  # 3 counting qubits + 1 eigenstate
cr = ClassicalRegister(3, 'c')  # Measure counting qubits
circuit = QuantumCircuit(qr, cr)

# Initialize eigenstate |1⟩
circuit.x(qr[3])

# Apply Hadamard to counting qubits
for i in range(3):
    circuit.h(qr[i])

# Controlled unitary operations (simplified)
circuit.cp(np.pi/4, qr[0], qr[3])  # Control-phase
circuit.cp(np.pi/2, qr[1], qr[3])
circuit.cp(np.pi, qr[2], qr[3])

# Inverse QFT on counting qubits (simplified)
circuit.h(qr[2])
circuit.cp(-np.pi/2, qr[1], qr[2])
circuit.h(qr[1])
circuit.cp(-np.pi/4, qr[0], qr[2])
circuit.cp(-np.pi/2, qr[0], qr[1])
circuit.h(qr[0])

# Swap qubits
circuit.swap(qr[0], qr[2])

# Measure
circuit.measure(qr[:3], cr)
"""
        
        result = await self.orchestrator.execute_quantum_job(
            backend=QuantumBackend.QISKIT_SIMULATOR,
            circuit_code=qpe_circuit_code,
            parameters={'shots': 2048, 'qubits': 4},
            description="Quantum Phase Estimation algorithm"
        )
        
        print(f"     Result: {'✅ Success' if result['success'] else '❌ Failed'}")
        if result['success']:
            print(f"     Execution time: {result.get('execution_time', 0):.3f}s")
        else:
            print(f"     Error: {result.get('error', 'Unknown')}")
            
        # Demo 3: Try IBM Quantum hardware (if available)
        print("\n   🔸 Demo 3: IBM Quantum Hardware Attempt")
        
        simple_circuit = """
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister

# Simple single-qubit circuit for hardware
qr = QuantumRegister(1, 'q')
cr = ClassicalRegister(1, 'c')
circuit = QuantumCircuit(qr, cr)

# X gate followed by measurement
circuit.x(qr[0])
circuit.measure(qr, cr)
"""
        
        result = await self.orchestrator.execute_quantum_job(
            backend=QuantumBackend.QISKIT_IBM,
            circuit_code=simple_circuit,
            parameters={'shots': 100, 'qubits': 1},
            description="Hardware test circuit"
        )
        
        print(f"     Result: {'✅ Success' if result['success'] else '❌ Failed (Expected if no IBM access)'}")
        if not result['success']:
            print(f"     Note: {result.get('error', 'IBM Quantum access not configured')}")
            
    async def demo_hpc_computing(self):
        """Demonstrate HPC/supercomputing capabilities."""
        print("\n   🖥️  HPC Job Execution")
        
        # Demo 1: Simple computational job
        print("\n   🔸 Demo 1: Python Scientific Computing Job")
        
        python_job_script = """#!/bin/bash
#SBATCH --job-name=quantum_demo
#SBATCH --output=demo_%j.out

# Load Python module
module load python/3.9

# Run scientific computation
python3 << EOF
import numpy as np
import time

print("Starting quantum simulation...")

# Simulate a quantum system evolution
def simulate_quantum_evolution(n_qubits, n_steps):
    # Initialize random state vector
    state = np.random.complex128(2**n_qubits)
    state = state / np.linalg.norm(state)
    
    # Random Hamiltonian
    H = np.random.hermitian(2**n_qubits)
    
    # Time evolution
    dt = 0.1
    for step in range(n_steps):
        # U = exp(-i * H * dt)
        U = np.linalg.matrix_power(np.eye(2**n_qubits) - 1j * H * dt, 1)
        state = U @ state
        
        if step % 10 == 0:
            print(f"Step {step}: |state|^2 = {np.real(np.vdot(state, state)):.6f}")
    
    return state

# Run simulation
start_time = time.time()
final_state = simulate_quantum_evolution(3, 50)
end_time = time.time()

print(f"Simulation completed in {end_time - start_time:.3f} seconds")
print(f"Final state norm: {np.linalg.norm(final_state):.6f}")
EOF
"""
        
        # Try to execute on available cluster (will likely fail in demo environment)
        result = await self.orchestrator.execute_hpc_job(
            cluster_name="mit_supercloud",  # This will likely fail
            job_script=python_job_script,
            job_type="batch",
            nodes=1,
            cpus_per_task=4,
            memory_gb=8,
            walltime_hours=1,
            description="Quantum simulation on HPC"
        )
        
        print(f"     Result: {'✅ Success' if result['success'] else '❌ Failed (Expected in demo)'}")
        if not result['success']:
            print(f"     Note: {result.get('error', 'HPC cluster not accessible in demo')}")
            
        # Demo 2: MPI parallel job
        print("\n   🔸 Demo 2: MPI Parallel Computation")
        
        mpi_job_script = """#!/bin/bash
#SBATCH --job-name=mpi_quantum_demo
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4

# Load MPI module
module load openmpi/4.1

# Run MPI job
mpirun -np 8 python3 << EOF
from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

print(f"Rank {rank} of {size} starting quantum computation...")

# Simulate distributed quantum computation
n_qubits_local = 2
local_state = np.random.complex128(2**n_qubits_local)
local_state = local_state / np.linalg.norm(local_state)

# Perform local computation
for i in range(100):
    # Random unitary operation
    U = np.random.random((2**n_qubits_local, 2**n_qubits_local)) + 1j * np.random.random((2**n_qubits_local, 2**n_qubits_local))
    U, _ = np.linalg.qr(U)  # Make unitary
    local_state = U @ local_state

# Gather results
all_states = comm.gather(local_state, root=0)

if rank == 0:
    print(f"Collected {len(all_states)} local quantum states")
    total_norm = sum(np.linalg.norm(state) for state in all_states)
    print(f"Total system norm: {total_norm:.6f}")

print(f"Rank {rank} computation completed")
EOF
"""
        
        result = await self.orchestrator.execute_hpc_job(
            cluster_name="tacc_stampede2",
            job_script=mpi_job_script,
            job_type="mpi",
            nodes=2,
            cpus_per_task=4,
            memory_gb=16,
            walltime_hours=2,
            description="MPI quantum computation"
        )
        
        print(f"     Result: {'✅ Success' if result['success'] else '❌ Failed (Expected in demo)'}")
        if not result['success']:
            print(f"     Note: {result.get('error', 'HPC cluster not accessible')}")
            
    async def demo_knowledge_management(self):
        """Demonstrate knowledge management capabilities."""
        print("\n   🧠 Quantum Knowledge Management")
        
        # Demo 1: Knowledge base status
        print("\n   🔸 Demo 1: Knowledge Base Status")
        
        kb_stats = self.orchestrator.knowledge_ingestor.get_knowledge_stats()
        print(f"     📚 Total documents: {kb_stats['total_documents']}")
        print(f"     📝 Total words: {kb_stats['total_words']}")
        print(f"     🔗 Processed URLs: {kb_stats['processed_urls']}")
        print(f"     📊 Source distribution: {kb_stats['source_distribution']}")
        
        # Demo 2: Knowledge search
        print("\n   🔸 Demo 2: Knowledge Search")
        
        search_queries = [
            "quantum circuit optimization",
            "CNOT gate implementation",
            "quantum error correction",
            "variational quantum eigensolvers"
        ]
        
        for query in search_queries:
            results = self.orchestrator.knowledge_ingestor.search_knowledge(query, limit=3)
            print(f"     🔍 Query: '{query}' -> {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:2]):
                    content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                    print(f"       {i+1}. {result['metadata']['source']}: {content_preview}")
                    
        # Demo 3: Knowledge export
        print("\n   🔸 Demo 3: Knowledge Export for Fusion")
        
        export_path = "quantum_agent/memory/demo_embeddings.json"
        export_result = self.orchestrator.knowledge_ingestor.export_embeddings(export_path)
        
        if export_result['success']:
            print(f"     ✅ Exported {export_result['exported_count']} embeddings")
            print(f"     📁 File size: {export_result['file_size_mb']:.2f} MB")
        else:
            print(f"     ❌ Export failed: {export_result['error']}")
            
    async def demo_fusion_integration(self):
        """Demonstrate fusion system integration."""
        print("\n   🔗 Model Fusion Integration")
        
        # Demo 1: Fusion status
        print("\n   🔸 Demo 1: Fusion System Status")
        
        try:
            fusion_status = await self.orchestrator.fusion_updater.get_fusion_status()
            print(f"     🔧 Fusion server: {self.orchestrator.fusion_updater.fusion_server_url}")
            
            if 'error' in fusion_status:
                print(f"     ❌ Status: {fusion_status['error']}")
            else:
                print(f"     ✅ Fusion system accessible")
                
        except Exception as e:
            print(f"     ❌ Fusion status check failed: {e}")
            
        # Demo 2: Knowledge injection
        print("\n   🔸 Demo 2: Quantum Knowledge Injection")
        
        # Create sample knowledge data
        sample_knowledge = {
            "quantum_concepts": ["superposition", "entanglement", "measurement"],
            "algorithms": ["VQE", "QAOA", "Grover"],
            "hardware": ["IBM", "Google", "Rigetti"],
            "embeddings_preview": "Quantum knowledge embeddings for model fusion"
        }
        
        injection_result = await self.orchestrator.fusion_updater.inject_quantum_knowledge(
            "sample_quantum_knowledge",
            knowledge_data=sample_knowledge
        )
        
        print(f"     Result: {'✅ Success' if injection_result['success'] else '❌ Failed'}")
        if not injection_result['success']:
            print(f"     Note: {injection_result.get('error', 'Fusion server not accessible')}")
            
        # Demo 3: Weight updates
        print("\n   🔸 Demo 3: Performance-Based Weight Updates")
        
        # Simulate performance metrics
        performance_metrics = {
            'deepseek-coder': 0.85,  # High performance for quantum code
            'codellama': 0.78,       # Good performance
            'phu': 0.72,            # Decent performance
            'mistral-7b': 0.65      # Lower performance
        }
        
        job_success_rates = {
            'quantum_total': 0.82,
            'hpc_total': 0.76
        }
        
        weight_update_result = await self.orchestrator.fusion_updater.update_fusion_weights(
            performance_metrics,
            job_success_rates
        )
        
        print(f"     Result: {'✅ Success' if weight_update_result['success'] else '❌ Failed'}")
        if not weight_update_result['success']:
            print(f"     Note: {weight_update_result.get('error', 'Fusion server not accessible')}")
            
    async def demo_safety_monitoring(self):
        """Demonstrate safety and monitoring capabilities."""
        print("\n   🛡️  Safety and Security Monitoring")
        
        # Demo 1: Safety validation
        print("\n   🔸 Demo 1: Safety Validation")
        
        # Test safe quantum code
        safe_code = """
from qiskit import QuantumCircuit
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()
"""
        
        safety_result = self.orchestrator.safeguards.validate_quantum_operation(
            "qiskit_simulator",
            safe_code,
            {'shots': 1024, 'qubits': 2}
        )
        
        print(f"     Safe code validation: {'✅ Passed' if safety_result['safe'] else '❌ Failed'}")
        
        # Test unsafe quantum code
        unsafe_code = """
import os
os.system('rm -rf /')  # Dangerous!
from qiskit import QuantumCircuit
circuit = QuantumCircuit(100, 100)  # Too many qubits
"""
        
        safety_result = self.orchestrator.safeguards.validate_quantum_operation(
            "qiskit_ibm",
            unsafe_code,
            {'shots': 10000, 'qubits': 100}
        )
        
        print(f"     Unsafe code validation: {'❌ Blocked' if not safety_result['safe'] else '✅ Unexpectedly passed'}")
        if not safety_result['safe']:
            print(f"     Blocked reasons: {safety_result['blocked_reasons'][:2]}")
            
        # Demo 2: Security status
        print("\n   🔸 Demo 2: Security Status Overview")
        
        security_status = self.orchestrator.safeguards.get_security_status()
        print(f"     📊 Total incidents: {security_status['total_incidents']}")
        print(f"     ⚠️  Recent incidents (24h): {security_status['recent_incidents_24h']}")
        print(f"     🚫 Blocked operations: {security_status['blocked_operations']}")
        print(f"     🎯 Rate limit status: {len(security_status['rate_limit_status'])} monitored operations")
        
        # Demo 3: Resource monitoring
        print("\n   🔸 Demo 3: Resource Limits")
        
        quantum_limits = security_status['quantum_limits']
        hpc_limits = security_status['hpc_limits']
        
        print(f"     ⚛️  Quantum limits:")
        print(f"       Max qubits (public): {quantum_limits['max_qubits_public']}")
        print(f"       Max shots (public): {quantum_limits['max_shots_public']}")
        
        print(f"     🖥️  HPC limits:")
        print(f"       Max jobs/hour: {hpc_limits['max_jobs_per_hour']}")
        print(f"       Max walltime: {hpc_limits['max_walltime_hours']} hours")
        print(f"       Max nodes/job: {hpc_limits['max_nodes_per_job']}")
        
    async def show_status_report(self):
        """Show comprehensive status report."""
        print("\n   📊 Comprehensive Agent Status")
        
        # Get full status
        status = self.orchestrator.get_agent_status()
        
        print(f"\n   🟢 Agent Running: {status['running']}")
        print(f"   ⏱️  Uptime: {status['uptime_seconds']:.0f} seconds")
        
        # Performance metrics
        perf = status['performance_metrics']
        print(f"\n   📈 Performance Metrics:")
        print(f"     Quantum success rate: {perf['quantum_success_rate']:.2%}")
        print(f"     HPC success rate: {perf['hpc_success_rate']:.2%}")
        print(f"     Avg quantum time: {perf['average_quantum_time']:.3f}s")
        print(f"     Total jobs executed: {perf['total_jobs_executed']}")
        
        # Component status
        print(f"\n   🔧 Component Status:")
        
        # Quantum executor
        qe_status = status['quantum_executor_status']
        print(f"     Quantum backends available: {sum([qe_status['qiskit_available'], qe_status['cirq_available'], qe_status['pennylane_available'], qe_status['dwave_available']])}")
        print(f"     Active quantum jobs: {qe_status['active_jobs']}")
        
        # HPC dispatcher
        hpc_status = status['hpc_dispatcher_status']
        print(f"     HPC clusters configured: {hpc_status['total_clusters']}")
        print(f"     Active HPC jobs: {hpc_status['active_jobs']}")
        
        # Knowledge base
        kb_status = status['knowledge_base_stats']
        print(f"     Knowledge documents: {kb_status['total_documents']}")
        print(f"     Knowledge words: {kb_status['total_words']}")
        
        # Security
        sec_status = status['security_status']
        print(f"     Security incidents: {sec_status['total_incidents']}")
        print(f"     Blocked operations: {sec_status['blocked_operations']}")
        
        # Generate comprehensive report
        print(f"\n   📋 Generating Comprehensive Report...")
        
        report = self.orchestrator.get_comprehensive_report()
        report_path = f"quantum_agent/memory/demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import json
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
                
            print(f"     ✅ Report saved to: {report_path}")
            print(f"     📄 Report contains {len(report)} sections")
            
        except Exception as e:
            print(f"     ❌ Failed to save report: {e}")


async def main():
    """Main demo function."""
    demo = QuantumAgentDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    print("🌟 Starting Quantum Agent Framework Demo...")
    print("This demonstrates quantum computing and HPC integration capabilities.")
    print("Note: Some features may fail if external services are not configured.\n")
    
    # Run the demo
    asyncio.run(main()) 