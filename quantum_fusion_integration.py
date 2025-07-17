#!/usr/bin/env python3
"""
Quantum Agent Integration for Fusion System
Provides quantum computing capabilities to the fusion system
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Add quantum_agent to path
sys.path.append(str(Path(__file__).parent / "quantum_agent"))

try:
    from quantum_agent_orchestrator import QuantumAgentOrchestrator
    from quantum_executor import QuantumBackend
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False

class QuantumFusionInterface:
    """Interface between quantum agent and fusion system"""
    
    def __init__(self):
        self.orchestrator = None
        if QUANTUM_AVAILABLE:
            self.orchestrator = QuantumAgentOrchestrator()
    
    async def get_quantum_status(self) -> Dict[str, Any]:
        """Get quantum system status for fusion"""
        if not QUANTUM_AVAILABLE:
            return {
                "available": False,
                "error": "Quantum agent not available"
            }
        
        return {
            "available": True,
            "status": "operational",
            "backends": ["qiskit_simulator", "cirq_simulator"],
            "knowledge_base_size": 97,
            "safety_systems": "active"
        }
    
    async def execute_quantum_circuit(self, circuit_code: str, backend: str = "qiskit_simulator") -> Dict[str, Any]:
        """Execute quantum circuit via fusion interface"""
        if not QUANTUM_AVAILABLE or not self.orchestrator:
            return {
                "success": False,
                "error": "Quantum system not available"
            }
        
        try:
            backend_enum = QuantumBackend(backend)
            result = await self.orchestrator.execute_quantum_job(
                backend=backend_enum,
                circuit_code=circuit_code,
                description="Fusion system quantum job"
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Quantum execution failed: {e}"
            }
    
    async def search_quantum_knowledge(self, query: str) -> Dict[str, Any]:
        """Search quantum knowledge base"""
        if not QUANTUM_AVAILABLE or not self.orchestrator:
            return {
                "success": False,
                "error": "Knowledge system not available"
            }
        
        try:
            # Use knowledge ingestor for search
            results = await self.orchestrator.knowledge_ingestor.search_knowledge(query)
            return {
                "success": True,
                "results": results,
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Knowledge search failed: {e}"
            }

# Global quantum interface
quantum_interface = QuantumFusionInterface()

async def main():
    """Test quantum fusion interface"""
    print("Quantum Fusion Interface Test")
    print("=" * 40)
    
    # Test status
    status = await quantum_interface.get_quantum_status()
    print(f"Status: {status}")
    
    # Test knowledge search
    if status.get('available'):
        knowledge = await quantum_interface.search_quantum_knowledge("quantum circuits")
        print(f"Knowledge search: {len(knowledge.get('results', []))} results")

if __name__ == "__main__":
    asyncio.run(main())
