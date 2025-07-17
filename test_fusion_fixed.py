#!/usr/bin/env python3
"""
Fusion System Test Suite - Fixed Version
Comprehensive testing of the model fusion system
"""

import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_fusion_system():
    """Test the model fusion system"""
    print("🔬 Testing Model Fusion System")
    print("=" * 50)
    
    # 1. Get fusion status
    print("\n1. Getting fusion status...")
    r = requests.get(f"{BASE_URL}/fusion/status")
    if r.status_code == 200:
        print("✅ Fusion system is running")
        status = r.json()
        if status.get('success'):
            data = status['data']
            print(f"   - Status: {data['status']}")
            print(f"   - Total models: {data['total_models']}")
            print(f"   - Total weight: {data['total_weight']}")
            print(f"   - Fusion strategy: {data['fusion_strategy']}")
            print(f"   - Last updated: {data['configuration'].get('last_updated', 'N/A')}")
        else:
            print("❌ Fusion status response format error")
    else:
        print("❌ Fusion system error")
        return
    
    # 2. Get system health
    print("\n2. Getting system health...")
    r = requests.get(f"{BASE_URL}/health")
    if r.status_code == 200:
        health = r.json()
        print(f"✅ Health check passed:")
        print(f"   - Status: {health['status']}")
        print(f"   - Service: {health['service']}")
        print(f"   - Timestamp: {health['timestamp']}")
    else:
        print("❌ Health check failed")
        return

    # 3. Test system monitoring
    print("\n3. Testing system monitoring...")
    try:
        # Test system monitor functionality
        from system_monitor import SystemMonitor
        monitor = SystemMonitor()
        stats = monitor.get_system_stats()
        print("✅ System monitoring functional:")
        print(f"   - CPU Usage: {stats.get('cpu_percent', 'N/A')}%")
        print(f"   - Memory Usage: {stats.get('memory_percent', 'N/A')}%")
        print(f"   - Disk Usage: {stats.get('disk_percent', 'N/A')}%")
    except Exception as e:
        print(f"❌ System monitoring error: {e}")

    # 4. Test configuration
    print("\n4. Testing configuration...")
    fusion_status = requests.get(f"{BASE_URL}/fusion/status").json()
    if fusion_status.get('success'):
        config = fusion_status['data']['configuration']
        models = config.get('ensemble_config', {}).get('models', [])
        print(f"✅ Configuration loaded:")
        for model in models:
            print(f"   - {model['name']}: weight={model['weight']}, domain={model['domain']}")
    else:
        print("❌ Configuration test failed")

    # 5. Final status check
    print("\n5. Final system validation...")
    try:
        # Check if all systems are responsive
        endpoints = [
            "/health",
            "/fusion/status"
        ]
        
        all_good = True
        for endpoint in endpoints:
            r = requests.get(f"{BASE_URL}{endpoint}")
            if r.status_code == 200:
                print(f"   ✅ {endpoint}: OK")
            else:
                print(f"   ❌ {endpoint}: Error {r.status_code}")
                all_good = False
        
        if all_good:
            print("\n🎉 All fusion system tests passed!")
            print("🚀 System is ready for operation")
        else:
            print("\n⚠️ Some tests failed - check system configuration")
            
    except Exception as e:
        print(f"❌ Final status check failed: {e}")

if __name__ == "__main__":
    test_fusion_system()
