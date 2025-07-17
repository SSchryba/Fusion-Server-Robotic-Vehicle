# Quantum Agent Framework

A comprehensive quantum computing and supercomputing integration system for the Autonomous AI Agent Framework. This system enables autonomous execution of quantum circuits, HPC batch jobs, knowledge management, and model fusion integration.

## 🚀 Features

### 🔬 Quantum Computing
- **Multi-Backend Support**: Qiskit (IBM), Cirq (Google), PennyLane, D-Wave Ocean SDK
- **Hardware & Simulation**: Execute on real quantum hardware or high-performance simulators
- **Circuit Optimization**: Automatic transpilation and optimization for target backends
- **Job Management**: Comprehensive tracking of quantum job execution and results

### 🖥️ High-Performance Computing
- **Multi-Cluster Support**: MIT SuperCloud, TACC, NERSC, custom HPC systems
- **Job Schedulers**: SLURM, PBS, SGE, direct execution
- **Resource Management**: Node allocation, CPU/memory optimization, walltime management
- **SSH Integration**: Secure remote job submission via SSH/paramiko

### 🧠 Knowledge Management
- **Documentation Ingestion**: Automated scraping from Qiskit, Cirq, PennyLane, D-Wave docs
- **Vector Database**: ChromaDB and FAISS integration for semantic search
- **Embedding Generation**: Sentence transformers for knowledge representation
- **Smart Retrieval**: Context-aware knowledge lookup for job optimization

### 🔗 Model Fusion Integration
- **Weight Optimization**: Performance-based model weight adjustments
- **Knowledge Injection**: Domain-specific quantum knowledge into fusion system
- **Continuous Learning**: Adaptive fusion weights based on job success rates
- **API Integration**: RESTful integration with existing fusion servers

### 🛡️ Safety & Security
- **Resource Limits**: Configurable limits for qubits, shots, compute resources
- **Code Validation**: Pattern detection for dangerous operations
- **Rate Limiting**: Prevent resource abuse with time-based limits
- **Incident Tracking**: Comprehensive security incident logging and management

## 📁 System Architecture

```
quantum_agent/
├── quantum_executor.py          # Quantum circuit execution (Qiskit, Cirq, PennyLane, D-Wave)
├── supercomputer_dispatcher.py  # HPC job submission (SLURM, PBS, SSH)
├── quantum_knowledge_ingestor.py # Documentation scraping and processing
├── fusion_knowledge_updater.py  # Model fusion integration
├── job_logger.py                # Comprehensive job tracking and analytics
├── safeguard.py                 # Safety and security systems
├── quantum_agent_orchestrator.py # Main coordination system
├── demo.py                      # Comprehensive demonstration script
├── requirements.txt             # Python dependencies
├── .env.template               # Environment configuration template
└── memory/                     # Data storage directory
    ├── job_log.json           # Job execution history
    ├── quantum_kb.faiss       # Vector database index
    └── quantum_knowledge_raw.json # Raw knowledge data
```

## 🔧 Installation

### 1. Prerequisites

```bash
# Python 3.8+
python --version

# Virtual environment (recommended)
python -m venv quantum_agent_env
source quantum_agent_env/bin/activate  # Linux/Mac
# quantum_agent_env\Scripts\activate   # Windows
```

### 2. Install Dependencies

```bash
cd quantum_agent
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your credentials
nano .env
```

Required configurations:
- **IBM Quantum**: `IBMQ_API_TOKEN`, `IBMQ_HUB`, `IBMQ_GROUP`, `IBMQ_PROJECT`
- **D-Wave**: `DWAVE_API_TOKEN`, `DWAVE_SOLVER`
- **HPC Clusters**: SSH credentials and hostnames
- **Fusion Server**: `FUSION_SERVER_URL`, `FUSION_API_KEY`

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from quantum_agent_orchestrator import QuantumAgentOrchestrator
from quantum_executor import QuantumBackend

async def quantum_example():
    # Initialize orchestrator
    orchestrator = QuantumAgentOrchestrator()
    await orchestrator.start()
    
    # Execute quantum circuit
    circuit_code = """
from qiskit import QuantumCircuit
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()
"""
    
    result = await orchestrator.execute_quantum_job(
        backend=QuantumBackend.QISKIT_SIMULATOR,
        circuit_code=circuit_code,
        parameters={'shots': 1024, 'qubits': 2},
        description="Bell state circuit"
    )
    
    print(f"Success: {result['success']}")
    print(f"Result: {result['result']}")
    
    await orchestrator.stop()

# Run example
asyncio.run(quantum_example())
```

### HPC Job Example

```python
async def hpc_example():
    orchestrator = QuantumAgentOrchestrator()
    await orchestrator.start()
    
    job_script = """#!/bin/bash
#SBATCH --job-name=quantum_simulation
module load python/3.9
python3 -c "
import numpy as np
print('Running quantum simulation...')
state = np.random.complex128(8)
print(f'Final state norm: {np.linalg.norm(state)}')
"
"""
    
    result = await orchestrator.execute_hpc_job(
        cluster_name="mit_supercloud",
        job_script=job_script,
        nodes=1,
        cpus_per_task=4,
        memory_gb=8,
        walltime_hours=1,
        description="Quantum state simulation"
    )
    
    print(f"HPC Job Success: {result['success']}")
    
    await orchestrator.stop()

asyncio.run(hpc_example())
```

## 🔬 Advanced Features

### Knowledge Management

```python
# Initialize knowledge base
await orchestrator.update_knowledge_base()

# Search quantum knowledge
results = orchestrator.knowledge_ingestor.search_knowledge(
    "quantum error correction", 
    limit=5
)

# Export knowledge for fusion
export_result = orchestrator.knowledge_ingestor.export_embeddings(
    "quantum_embeddings.json"
)
```

### Fusion Integration

```python
# Inject quantum knowledge
injection_result = await orchestrator.fusion_updater.inject_quantum_knowledge(
    "quantum_knowledge_package.json"
)

# Update model weights based on performance
performance_metrics = {
    'deepseek-coder': 0.85,
    'codellama': 0.78
}

weight_result = await orchestrator.fusion_updater.update_fusion_weights(
    performance_metrics,
    {'quantum_total': 0.82}
)
```

### Safety & Monitoring

```python
# Check safety status
security_status = orchestrator.safeguards.get_security_status()
print(f"Total incidents: {security_status['total_incidents']}")

# Get comprehensive report
report = orchestrator.get_comprehensive_report()
```

## 🎯 Running the Demo

Execute the comprehensive demonstration:

```bash
cd quantum_agent
python demo.py
```

The demo showcases:
1. 🔧 System initialization
2. ⚛️ Quantum computing capabilities
3. 🖥️ HPC job execution
4. 🧠 Knowledge management
5. 🔗 Fusion system integration
6. 🛡️ Safety and monitoring
7. 📊 Status reporting

## 📊 Monitoring & Analytics

### Job Statistics

```python
# Get job statistics
quantum_stats = orchestrator.quantum_executor.get_job_stats()
hpc_stats = orchestrator.hpc_dispatcher.get_job_stats()

print(f"Quantum success rate: {quantum_stats['success_rate']:.2%}")
print(f"HPC success rate: {hpc_stats['success_rate']:.2%}")
```

### Performance Metrics

```python
# Get performance metrics
status = orchestrator.get_agent_status()
metrics = status['performance_metrics']

print(f"Total jobs: {metrics['total_jobs_executed']}")
print(f"Average quantum time: {metrics['average_quantum_time']:.3f}s")
```

### Security Monitoring

```python
# Recent security incidents
incidents = orchestrator.safeguards.get_recent_incidents(hours=24)
print(f"Security incidents (24h): {len(incidents)}")

# Export incident log
export_result = orchestrator.safeguards.export_incident_log(
    "security_incidents.json"
)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `IBMQ_API_TOKEN` | IBM Quantum API token | `your_ibm_token` |
| `DWAVE_API_TOKEN` | D-Wave API token | `your_dwave_token` |
| `MIT_SUPERCLOUD_HOST` | MIT SuperCloud hostname | `txe1-login.mit.edu` |
| `FUSION_SERVER_URL` | Fusion server URL | `http://localhost:8000` |
| `MAX_QUBITS_PUBLIC` | Max qubits for public backends | `20` |
| `MAX_SLURM_JOBS_PER_HOUR` | HPC job rate limit | `10` |

### Safety Limits

```python
# Update safety limits
new_limits = {
    'quantum_limits': {
        'max_qubits_public': 25,
        'max_shots_public': 10000
    },
    'hpc_limits': {
        'max_walltime_hours': 48,
        'max_nodes_per_job': 128
    }
}

orchestrator.safeguards.update_limits(new_limits)
```

## 🔄 Integration with Autonomous Agent

The quantum agent integrates seamlessly with the main autonomous agent framework:

```python
from autonomous_agent.core.agent import AutonomousAgent
from quantum_agent.quantum_agent_orchestrator import QuantumAgentOrchestrator

# Initialize both systems
main_agent = AutonomousAgent()
quantum_agent = QuantumAgentOrchestrator()

# Start both systems
await main_agent.start()
await quantum_agent.start()

# The quantum agent can be used by the main agent for:
# - Quantum algorithm research and development
# - Scientific computing on HPC clusters
# - Technical knowledge acquisition and fusion
# - Performance optimization through specialized hardware
```

## 🛠️ Troubleshooting

### Common Issues

1. **IBM Quantum Connection Failed**
   ```bash
   # Check API token
   echo $IBMQ_API_TOKEN
   
   # Verify network connectivity
   curl -X GET "https://api.quantum-computing.ibm.com/api/Network/runtime/me" \
        -H "X-Qx-Token: $IBMQ_API_TOKEN"
   ```

2. **HPC SSH Connection Failed**
   ```bash
   # Test SSH connectivity
   ssh -i ~/.ssh/id_rsa username@hostname
   
   # Check key permissions
   chmod 600 ~/.ssh/id_rsa
   ```

3. **Knowledge Ingestion Failed**
   ```python
   # Check internet connectivity
   import requests
   response = requests.get("https://qiskit.org/documentation/")
   print(response.status_code)
   ```

4. **Fusion Server Unreachable**
   ```bash
   # Test fusion server
   curl -X GET http://localhost:8000/fusion/status
   ```

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Component-specific logging
logger = logging.getLogger('quantum_agent')
logger.setLevel(logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Code formatting
black quantum_agent/
flake8 quantum_agent/
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Full API documentation available in `docs/`
- **Issues**: Report bugs and request features via GitHub issues
- **Discussions**: Join community discussions for questions and ideas

## 🔮 Future Roadmap

- **Quantum-Classical Hybrid Algorithms**: VQE, QAOA, quantum machine learning
- **Advanced HPC Integration**: Kubernetes, Docker containers, cloud platforms
- **Real-time Monitoring**: WebSocket-based live job monitoring
- **Enhanced Security**: Zero-trust security model, encrypted communications
- **Extended Knowledge Base**: Research papers, patents, quantum software libraries
- **Performance Optimization**: Caching, parallelization, resource prediction

---

**The Quantum Agent Framework enables autonomous AI systems to harness the power of quantum computing and high-performance computing for scientific discovery and technological advancement.** 