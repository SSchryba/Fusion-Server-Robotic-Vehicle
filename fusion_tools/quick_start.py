#!/usr/bin/env python3
"""
Quick Start Script for Fusion Tools Suite
Demonstrates all functionality and helps with initial setup
"""

import os
import sys
import time
import argparse
import subprocess
from typing import List, Dict
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader
from control.fusion_controller import FusionController
from control.model_evaluator import ModelEvaluator

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step: int, title: str):
    """Print a formatted step"""
    print(f"\n{step}. {title}")
    print("-" * 40)

def check_prerequisites() -> bool:
    """Check if all prerequisites are met"""
    print_header("CHECKING PREREQUISITES")
    
    all_good = True
    
    # Check Python version
    print_step(1, "Checking Python version")
    if sys.version_info >= (3, 8):
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    else:
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} is not supported (need 3.8+)")
        all_good = False
    
    # Check if fusion server is running
    print_step(2, "Checking fusion server")
    try:
        client = FusionAPIClient()
        health = client.get_server_health()
        if health.get('status') == 'ok':
            print("✅ Fusion server is running and healthy")
        else:
            print("❌ Fusion server is not healthy")
            all_good = False
    except Exception as e:
        print(f"❌ Cannot connect to fusion server: {e}")
        print("   Make sure the fusion server is running on http://localhost:8000")
        all_good = False
    
    # Check if Ollama is running
    print_step(3, "Checking Ollama service")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
        else:
            print("❌ Ollama service is not responding")
            all_good = False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running on http://localhost:11434")
        all_good = False
    
    # Check dependencies
    print_step(4, "Checking dependencies")
    missing_deps = []
    required_deps = ['requests', 'pyyaml', 'rich', 'fastapi', 'uvicorn', 'schedule']
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (missing)")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("   Run: pip install -r requirements.txt")
        all_good = False
    
    return all_good

def demo_configuration():
    """Demonstrate configuration loading"""
    print_header("CONFIGURATION DEMO")
    
    try:
        config_loader = ConfigLoader()
        config = config_loader.get_fusion_config()
        
        print_step(1, "Configuration loaded successfully")
        print(f"✅ Fusion server: {config.host}:{config.port}")
        print(f"✅ Model constraints: {config.model_constraints.max_parameter_size} max size")
        print(f"✅ Capability threshold: {config.model_constraints.min_capability_threshold}")
        print(f"✅ Priority models: {len(config.priority_models)} configured")
        
        print_step(2, "Sample configuration values")
        print(f"   - Fusion interval: {config.fusion_control.get('cycle_interval_hours', 56)} hours")
        print(f"   - Models per fusion: {config.fusion_control.get('models_per_fusion', 3)}")
        print(f"   - Chat model: {config.chat.get('default_model', 'hybrid-fusion-v1')}")
        print(f"   - Max message length: {config.chat.get('max_message_length', 4096)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def demo_model_evaluation():
    """Demonstrate model evaluation"""
    print_header("MODEL EVALUATION DEMO")
    
    try:
        evaluator = ModelEvaluator()
        
        print_step(1, "Getting available models")
        client = FusionAPIClient()
        models = client.get_available_models()
        
        if not models:
            print("❌ No models available")
            return False
        
        print(f"✅ Found {len(models)} models: {', '.join(models[:5])}")
        if len(models) > 5:
            print(f"   ... and {len(models) - 5} more")
        
        print_step(2, "Evaluating models")
        evaluations = evaluator.evaluate_all_models()
        
        if not evaluations:
            print("❌ No evaluations completed")
            return False
        
        print(f"✅ Evaluated {len(evaluations)} models")
        
        print_step(3, "Top performing models")
        top_models = evaluator.select_top_models(evaluations, 3)
        
        for i, model in enumerate(top_models, 1):
            print(f"   {i}. {model.model_name}")
            print(f"      Score: {model.overall_score:.2f}")
            print(f"      Recommendation: {model.recommendation}")
            print(f"      Constraints: {'✅' if model.meets_constraints else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model evaluation error: {e}")
        return False

def demo_fusion_cycle():
    """Demonstrate a fusion cycle"""
    print_header("FUSION CYCLE DEMO")
    
    try:
        controller = FusionController()
        
        print_step(1, "Validating system health")
        health = controller.validate_system_health()
        
        if not health['overall_healthy']:
            print("❌ System health check failed:")
            for issue in health['issues']:
                print(f"   - {issue}")
            return False
        
        print("✅ System health check passed")
        
        print_step(2, "Running fusion cycle")
        print("   This may take a few minutes...")
        
        result = controller.run_fusion_cycle()
        
        if result['success']:
            print("✅ Fusion cycle completed successfully!")
            print(f"   - Duration: {result['duration_seconds']:.1f} seconds")
            print(f"   - Models evaluated: {result['models_evaluated']}")
            print(f"   - Models selected: {result['models_selected']}")
            print(f"   - Hybrid created: {result['hybrid_created']}")
            print(f"   - Selected models: {', '.join(result['selected_models'])}")
            
            return True
        else:
            print(f"❌ Fusion cycle failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Fusion cycle error: {e}")
        return False

def demo_chat_interface():
    """Demonstrate chat interface setup"""
    print_header("CHAT INTERFACE DEMO")
    
    print_step(1, "Testing chat server components")
    
    try:
        from chat.backend.chat_server import ChatServer
        
        print("✅ Chat server components loaded successfully")
        
        print_step(2, "Chat server features")
        print("   - Real-time WebSocket communication")
        print("   - Model selection (hybrid and standard)")
        print("   - Conversation history")
        print("   - Performance metrics")
        print("   - Modern web interface")
        
        print_step(3, "Starting chat server")
        print("   To start the chat interface, run:")
        print("   python run_chat.py")
        print("   Then open http://localhost:8001 in your browser")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat interface error: {e}")
        return False

def run_interactive_demo():
    """Run interactive demo"""
    print_header("INTERACTIVE DEMO")
    
    demos = [
        ("Configuration", demo_configuration),
        ("Model Evaluation", demo_model_evaluation),
        ("Fusion Cycle", demo_fusion_cycle),
        ("Chat Interface", demo_chat_interface)
    ]
    
    for name, demo_func in demos:
        print(f"\n🎯 Running {name} demo...")
        
        try:
            success = demo_func()
            if success:
                print(f"✅ {name} demo completed successfully")
            else:
                print(f"❌ {name} demo failed")
                
                if input(f"\nContinue with remaining demos? (y/N): ").lower() != 'y':
                    break
                    
        except KeyboardInterrupt:
            print(f"\n⏹️  {name} demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ {name} demo error: {e}")

def show_usage_examples():
    """Show usage examples for all tools"""
    print_header("USAGE EXAMPLES")
    
    examples = [
        ("Fusion Status Monitor", [
            "python run_monitor.py",
            "python run_monitor.py --refresh 10",
            "python run_monitor.py --log-level DEBUG"
        ]),
        ("Fusion Controller", [
            "python run_controller.py --mode cycle",
            "python run_controller.py --mode continuous --interval 24",
            "python run_controller.py --mode evaluate",
            "python run_controller.py --mode status --health-check"
        ]),
        ("Chat Interface", [
            "python run_chat.py",
            "python run_chat.py --port 8001",
            "python run_chat.py --fusion-host localhost --fusion-port 8000"
        ])
    ]
    
    for tool_name, commands in examples:
        print(f"\n📘 {tool_name}:")
        for cmd in commands:
            print(f"   {cmd}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fusion Tools Quick Start")
    parser.add_argument('--mode', choices=['check', 'demo', 'examples', 'full'], 
                       default='full', help='Run mode')
    parser.add_argument('--skip-checks', action='store_true', 
                       help='Skip prerequisite checks')
    
    args = parser.parse_args()
    
    print_header("FUSION TOOLS SUITE - QUICK START")
    print("Welcome to the Fusion Tools Suite!")
    print("This script will help you get started with all the tools.")
    
    if args.mode in ['check', 'full'] and not args.skip_checks:
        if not check_prerequisites():
            print("\n❌ Prerequisites not met. Please fix the issues above.")
            return 1
    
    if args.mode in ['demo', 'full']:
        run_interactive_demo()
    
    if args.mode in ['examples', 'full']:
        show_usage_examples()
    
    print_header("QUICK START COMPLETE")
    print("🎉 You're all set to use the Fusion Tools Suite!")
    print("\nNext steps:")
    print("1. Start the status monitor: python run_monitor.py")
    print("2. Start the controller: python run_controller.py --mode continuous")
    print("3. Start the chat interface: python run_chat.py")
    print("4. Open http://localhost:8001 for the chat interface")
    print("\nFor more information, see the README.md file.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 