#!/usr/bin/env python3
"""
Test script to demonstrate model fusion capabilities
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
    
    # 2. Get available models
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
    
    # 3. Create hybrid model
    print("\n3. Creating hybrid model...")
    fusion_models = ['codellama:latest', 'mistral:latest', 'phi:latest']
    r = requests.post(f"{BASE_URL}/fusion/create-hybrid", json=fusion_models)
    if r.status_code == 200:
        result = r.json()
        print("✅ Hybrid model created successfully!")
        print(f"   - Name: {result['hybrid_name']}")
        print(f"   - Source models: {result['source_models']}")
        print(f"   - Fusion strategy: {result['ensemble_config']['fusion_strategy']}")
        
        # Show model weights
        print(f"   - Model weights:")
        for model_info in result['ensemble_config']['models']:
            print(f"     * {model_info['name']}: {model_info['normalized_weight']:.3f} (domain: {model_info['domain']})")
    else:
        print("❌ Failed to create hybrid model")
        print(f"   Error: {r.text}")
    
    # 4. Get hybrid models
    print("\n4. Listing hybrid models...")
    r = requests.get(f"{BASE_URL}/fusion/hybrids")
    if r.status_code == 200:
        hybrids = r.json()
        print(f"✅ Found {hybrids['count']} hybrid models:")
        for hybrid in hybrids['hybrids']:
            print(f"   - {hybrid['name']} (created: {hybrid['created_at']})")
            print(f"     Parameters: {hybrid['fusion_params']['total_parameters']:,}")
            print(f"     Capabilities: {hybrid['fusion_params']['combined_capabilities']}")
    else:
        print("❌ Could not get hybrid models")
    
    # 5. Test standalone fusion engine
    print("\n5. Testing standalone fusion engine...")
    try:
        from server.model_fusion import ModelFusionEngine
        engine = ModelFusionEngine()
        
        # Test model analysis
        test_model = "deepseek-coder:latest"
        capabilities = engine.analyze_model_capabilities(test_model)
        print(f"✅ Model analysis for {test_model}:")
        print(f"   - Domain: {capabilities['domain']}")
        print(f"   - Size: {capabilities['size']}")
        print(f"   - Strengths: {capabilities['strengths']}")
        print(f"   - Fusion weight: {capabilities['fusion_weight']}")
        
        # Test model selection
        available_models = ['codellama:latest', 'mistral:latest', 'phi:latest', 'llama2:latest', 'gemma:2b']
        selected = engine.select_diverse_models(available_models, 3)
        print(f"✅ Diverse model selection (3 from {len(available_models)}):")
        print(f"   Selected: {selected}")
        
    except Exception as e:
        print(f"❌ Standalone engine test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🚀 Model Fusion System Test Complete!")

if __name__ == "__main__":
    test_fusion_system() 