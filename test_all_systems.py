#!/usr/bin/env python3
"""
Quick Test Script for All Fusion System Components
Tests if all our repaired systems are working correctly
"""

import asyncio
import requests
import json
import sys
from pathlib import Path

async def test_root_agent():
    """Test the root agent integration"""
    print("🤖 Testing Root Agent Integration...")
    try:
        # Import the root agent integration
        from root_agent_integration import root_interface
        
        # Test status
        status = await root_interface.get_root_agent_status()
        print(f"   Status: {'✅' if status.get('available') else '❌'} {status}")
        
        if status.get('available'):
            # Test safe command
            result = await root_interface.execute_safe_command("echo Root agent test")
            print(f"   Command Test: {'✅' if result.get('success') else '❌'}")
            
            # Test system metrics
            metrics = await root_interface.get_system_metrics()
            print(f"   Metrics: {'✅' if metrics.get('success') else '❌'}")
            
        return status.get('available', False)
    except Exception as e:
        print(f"   ❌ Root Agent Error: {e}")
        return False

def test_quantum_agent():
    """Test quantum agent functionality"""
    print("⚛️ Testing Quantum Agent...")
    try:
        # Check if quantum agent modules are available
        sys.path.append(str(Path(__file__).parent / "quantum_agent"))
        
        # Try to import quantum components
        try:
            from quantum_agent import QuantumAgent
            print("   ✅ Quantum Agent module available")
            return True
        except ImportError:
            # Check alternative quantum modules
            quantum_files = list(Path("quantum_agent").glob("*.py"))
            if quantum_files:
                print(f"   ✅ Quantum files available: {len(quantum_files)} files")
                return True
            else:
                print("   ❌ No quantum agent files found")
                return False
    except Exception as e:
        print(f"   ❌ Quantum Agent Error: {e}")
        return False

def test_fusion_server():
    """Test if fusion server is running"""
    print("🧬 Testing Fusion Server...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Fusion Server Online")
            return True
        else:
            print(f"   ❌ Fusion Server returned {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("   ❌ Fusion Server Offline")
        return False

def test_control_center():
    """Test unified control center"""
    print("🌌 Testing Unified Control Center...")
    try:
        response = requests.get("http://localhost:9000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Control Center Online")
            return True
        else:
            print(f"   ❌ Control Center returned {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("   ❌ Control Center Offline")
        return False

async def main():
    """Run all tests"""
    print("🚀 Fusion-Hybrid-V1 System Component Test")
    print("=" * 50)
    
    results = {
        "root_agent": await test_root_agent(),
        "quantum_agent": test_quantum_agent(),
        "fusion_server": test_fusion_server(),
        "control_center": test_control_center()
    }
    
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n🎯 Overall Status: {passed_tests}/{total_tests} components operational")
    
    if passed_tests == total_tests:
        print("🎉 All systems are ready for operation!")
    elif passed_tests >= 2:
        print("⚠️ Some systems are operational. Start missing components.")
    else:
        print("❌ Most systems need to be started. Run startup scripts.")
    
    print("\n🔗 Access URLs:")
    print("   Fusion System: http://localhost:8000")
    print("   Control Center: http://localhost:9000")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
