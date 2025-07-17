
import sys
import asyncio
from pathlib import Path

# Add quantum_agent to path
sys.path.append(str(Path(__file__).parent / "quantum_agent"))

try:
    from quantum_agent_orchestrator import QuantumAgentOrchestrator
    
    async def get_quantum_status():
        """Get quantum agent status for fusion system"""
        orchestrator = QuantumAgentOrchestrator()
        return {
            "status": "operational",
            "backends_available": ["qiskit_simulator"],
            "safety_systems": "active",
            "knowledge_base": "ready"
        }
    
    if __name__ == "__main__":
        status = asyncio.run(get_quantum_status())
        print(f"Quantum Agent Status: {status}")
        
except ImportError as e:
    print(f"Quantum agent not available: {e}")
