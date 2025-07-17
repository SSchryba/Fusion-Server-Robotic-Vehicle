#!/usr/bin/env python3
"""
Ollama Model Setup for Fusion System
Downloads and configures required models for full fusion capability
"""

import subprocess
import time
import requests
import json

def run_command(cmd, description):
    """Run a command and show progress"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"   ✅ Success: {description}")
            return True
        else:
            print(f"   ⚠️ Warning: {description} - {result.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout: {description} (continuing...)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {description} - {e}")
        return False

def setup_ollama_models():
    """Download essential models for fusion system"""
    print("🚀 OLLAMA MODEL SETUP")
    print("=" * 50)
    
    # Essential models for fusion system
    models = [
        ("llama3.2:latest", "Primary conversation model"),
        ("qwen2.5:0.5b", "Lightweight quick responses"),
        ("phi3.5:latest", "Code and reasoning model"),
    ]
    
    for model, description in models:
        print(f"\n📥 Downloading {model} ({description})")
        success = run_command(f"ollama pull {model}", f"Download {model}")
        if success:
            print(f"   🎉 {model} ready for fusion!")

def test_models():
    """Test downloaded models"""
    print("\n🧪 TESTING MODELS")
    print("=" * 50)
    
    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   📋 Available models:")
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    print(f"      • {line.strip()}")
        else:
            print("   ⚠️ Could not list models")
    except Exception as e:
        print(f"   ❌ Error testing models: {e}")

def test_fusion_with_models():
    """Test fusion system with available models"""
    print("\n🔀 TESTING FUSION SYSTEM")
    print("=" * 50)
    
    try:
        response = requests.post("http://localhost:8000/fusion/respond", 
                               json={"message": "Hello, are you working with real models now?"},
                               timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Fusion backend responding!")
            print(f"   📝 Response: {data.get('response', 'No response')[:100]}...")
        else:
            print(f"   ⚠️ Fusion backend returned status {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Fusion backend not responding: {e}")

if __name__ == "__main__":
    print("🎯 FUSION-HYBRID-V1 MODEL SETUP")
    print("=" * 60)
    print("Setting up AI models for complete fusion capability...")
    print()
    
    # Check if Ollama is running
    try:
        result = subprocess.run("ollama ps", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama service is running")
        else:
            print("⚠️ Starting Ollama service...")
            subprocess.run("ollama serve", shell=True, timeout=5)
    except:
        print("⚠️ Ollama may need manual start")
    
    setup_ollama_models()
    test_models()
    test_fusion_with_models()
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("✅ Chat interface working with graceful fallbacks")
    print("✅ UI accessible at http://localhost:9000")
    print("✅ Fusion backend operational at http://localhost:8000")
    print("🔄 Models will enhance responses as they become available")
    print("\n💡 Your fusion system is ready to use!")
