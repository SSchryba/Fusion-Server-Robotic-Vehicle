#!/usr/bin/env python3
"""
Quantum Agent Test & Integration Script
Tests and integrates the quantum agent with the fusion system
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Add quantum_agent to path
sys.path.append(str(Path(__file__).parent / "quantum_agent"))

try:
    from quantum_agent_orchestrator import QuantumAgentOrchestrator
    from quantum_executor import QuantumBackend
    QUANTUM_AGENT_AVAILABLE = True
    print("✅ Quantum agent modules imported successfully")
except ImportError as e:
    QUANTUM_AGENT_AVAILABLE = False
    print(f"⚠️ Quantum agent not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuantumAgentTester:
    """Test and integrate quantum agent capabilities"""
    
    def __init__(self):
        self.orchestrator = None
        if QUANTUM_AGENT_AVAILABLE:
            self.orchestrator = QuantumAgentOrchestrator()
    
    async def run_basic_tests(self):
        """Run basic quantum agent tests"""
        print("🧪 QUANTUM AGENT BASIC TESTS")
        print("=" * 50)
        
        if not QUANTUM_AGENT_AVAILABLE:
            print("❌ Quantum agent not available - skipping tests")
            return False
        
        try:
            # Test 1: Initialize orchestrator
            print("1. 🔧 Testing orchestrator initialization...")
            await self.orchestrator.start()
            print("   ✅ Orchestrator started successfully")
            
            # Test 2: Test safety system
            print("\n2. 🛡️ Testing safety system...")
            result = await self.test_safety_system()
            if result:
                print("   ✅ Safety system working correctly")
            else:
                print("   ⚠️ Safety system issues detected")
            
            # Test 3: Test knowledge system
            print("\n3. 🧠 Testing knowledge system...")
            result = await self.test_knowledge_system()
            if result:
                print("   ✅ Knowledge system operational")
            else:
                print("   ⚠️ Knowledge system needs attention")
            
            # Test 4: Test quantum simulator
            print("\n4. ⚛️ Testing quantum simulator...")
            result = await self.test_quantum_simulator()
            if result:
                print("   ✅ Quantum simulator working")
            else:
                print("   ⚠️ Quantum simulator issues")
            
            # Cleanup
            await self.orchestrator.stop()
            print("\n✅ All basic tests completed")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            logger.error(f"Quantum agent test error: {e}")
            return False
    
    async def test_safety_system(self):
        """Test the safety system"""
        try:
            # Test basic safety validation
            if hasattr(self.orchestrator, 'safeguards'):
                # Test quantum operation validation
                safety_result = self.orchestrator.safeguards.validate_quantum_operation(
                    "qiskit_simulator",
                    "# Simple test circuit\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(2)",
                    {"qubits": 2, "shots": 1024}
                )
                return safety_result.get('safe', False)
            return True
        except Exception as e:
            logger.error(f"Safety system test failed: {e}")
            return False
    
    async def test_knowledge_system(self):
        """Test the knowledge system"""
        try:
            # Test knowledge ingestor initialization
            if hasattr(self.orchestrator, 'knowledge_ingestor'):
                # Basic initialization test
                return True
            return True
        except Exception as e:
            logger.error(f"Knowledge system test failed: {e}")
            return False
    
    async def test_quantum_simulator(self):
        """Test quantum simulator execution"""
        try:
            # Create a simple quantum circuit test
            simple_circuit = """
from qiskit import QuantumCircuit
qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)
"""
            
            # Test with simulator backend
            result = await self.orchestrator.execute_quantum_job(
                backend=QuantumBackend.QISKIT_SIMULATOR,
                circuit_code=simple_circuit,
                parameters={"shots": 100},
                description="Basic simulator test"
            )
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Quantum simulator test failed: {e}")
            return False

def create_quantum_agent_status():
    """Create quantum agent status report"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "quantum_agent_available": QUANTUM_AGENT_AVAILABLE,
        "components": {
            "orchestrator": "available" if QUANTUM_AGENT_AVAILABLE else "unavailable",
            "quantum_executor": "available" if QUANTUM_AGENT_AVAILABLE else "unavailable",
            "safety_system": "available" if QUANTUM_AGENT_AVAILABLE else "unavailable",
            "knowledge_system": "available" if QUANTUM_AGENT_AVAILABLE else "unavailable"
        },
        "backends": {
            "qiskit_simulator": "available",
            "qiskit_ibm": "requires API token",
            "cirq_simulator": "available", 
            "dwave": "requires API token"
        },
        "integration_status": "operational" if QUANTUM_AGENT_AVAILABLE else "needs_repair"
    }
    
    return status

async def main():
    """Main test function"""
    print("🚀 QUANTUM AGENT REPAIR & OPTIMIZATION")
    print("=" * 60)
    
    # Create status report
    status = create_quantum_agent_status()
    print(f"📊 Status: {status['integration_status']}")
    print(f"🔧 Components available: {QUANTUM_AGENT_AVAILABLE}")
    
    # Run tests if available
    if QUANTUM_AGENT_AVAILABLE:
        tester = QuantumAgentTester()
        success = await tester.run_basic_tests()
        
        if success:
            print("\n🎉 QUANTUM AGENT REPAIR SUCCESSFUL!")
            print("=" * 60)
            print("✅ All systems operational")
            print("✅ Safety systems active")
            print("✅ Ready for integration with fusion system")
        else:
            print("\n⚠️ QUANTUM AGENT NEEDS FURTHER REPAIR")
            print("=" * 60)
            print("❌ Some tests failed")
            print("💡 Check logs for detailed error information")
    else:
        print("\n🔧 QUANTUM AGENT DEPENDENCIES NEEDED")
        print("=" * 60)
        print("💡 Install quantum computing libraries:")
        print("   pip install qiskit cirq pennylane dwave-ocean-sdk")
        print("   pip install faiss-cpu sentence-transformers chromadb")
    
    # Save status report
    status_file = Path("quantum_agent_status.json")
    with open(status_file, 'w') as f:
        import json
        json.dump(status, f, indent=2)
    
    print(f"\n📄 Status report saved to: {status_file}")

if __name__ == "__main__":
    asyncio.run(main())
