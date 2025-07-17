#!/usr/bin/env python3
"""
Fusion System Auto-Repair Tool
Automatically detects and fixes common system issues
"""

import os
import sys
import json
import subprocess
import requests
import time
from pathlib import Path

class FusionAutoRepair:
    """Automated system repair and optimization"""
    
    def __init__(self):
        self.server_dir = Path("c:/Users/sschr/Desktop/server")
        self.python_exe = "C:/Users/sschr/Desktop/server/.venv/Scripts/python.exe"
        self.base_url = "http://localhost:9000"
        
    def check_python_environment(self):
        """Check if Python environment is properly configured"""
        print("🐍 Checking Python environment...")
        
        venv_path = self.server_dir / ".venv"
        if not venv_path.exists():
            print("❌ Virtual environment not found")
            return False
        
        if not Path(self.python_exe).exists():
            print("❌ Python executable not found")
            return False
        
        print("✅ Python environment OK")
        return True
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print("📦 Checking dependencies...")
        
        required_packages = [
            "fastapi", "uvicorn", "requests", "psutil", 
            "yaml", "transformers", "torch"
        ]
        
        try:
            result = subprocess.run([
                self.python_exe, "-c", 
                f"import {'; import '.join(required_packages)}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All dependencies installed")
                return True
            else:
                print(f"❌ Missing dependencies: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error checking dependencies: {e}")
            return False
    
    def check_services(self):
        """Check if services are running"""
        print("🔧 Checking services...")
        
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                print("✅ Main service running")
                return True
            else:
                print(f"❌ Service error: {r.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service not responding: {e}")
            return False
    
    def repair_dependencies(self):
        """Install missing dependencies"""
        print("🔧 Repairing dependencies...")
        
        try:
            subprocess.run([
                self.python_exe, "-m", "pip", "install", "-r", 
                str(self.server_dir / "requirements.txt")
            ], check=True)
            print("✅ Dependencies repaired")
            return True
        except Exception as e:
            print(f"❌ Failed to repair dependencies: {e}")
            return False
    
    def restart_services(self):
        """Restart system services"""
        print("🔄 Restarting services...")
        
        try:
            # Start main service
            subprocess.Popen([
                self.python_exe, str(self.server_dir / "main.py")
            ], cwd=self.server_dir)
            
            # Wait a moment for startup
            time.sleep(5)
            
            # Check if it's running
            if self.check_services():
                print("✅ Services restarted successfully")
                return True
            else:
                print("❌ Failed to restart services")
                return False
        except Exception as e:
            print(f"❌ Error restarting services: {e}")
            return False
    
    def repair_fusion_config(self):
        """Repair fusion configuration if corrupted"""
        print("🧬 Checking fusion configuration...")
        
        config_path = self.server_dir / "models" / "hybrid_models" / "hybrid-fusion-v1.json"
        
        if not config_path.exists():
            print("❌ Fusion config missing, creating default...")
            self.create_default_fusion_config(config_path)
            return True
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate config structure
            required_keys = ['name', 'ensemble_config', 'fusion_params']
            if all(key in config for key in required_keys):
                print("✅ Fusion configuration OK")
                return True
            else:
                print("❌ Invalid fusion config, repairing...")
                self.create_default_fusion_config(config_path)
                return True
                
        except Exception as e:
            print(f"❌ Corrupted fusion config, recreating: {e}")
            self.create_default_fusion_config(config_path)
            return True
    
    def create_default_fusion_config(self, config_path):
        """Create default fusion configuration"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "name": "hybrid-fusion-v1",
            "ensemble_config": {
                "models": [
                    {
                        "name": "deepseek-coder:latest",
                        "weight": 1.5,
                        "domain": "reasoning",
                        "normalized_weight": 0.294,
                        "strengths": ["deep_reasoning", "code_generation", "math"]
                    },
                    {
                        "name": "mistral:latest", 
                        "weight": 1.2,
                        "domain": "instruction",
                        "normalized_weight": 0.235,
                        "strengths": ["following_instructions", "reasoning", "general"]
                    },
                    {
                        "name": "codellama:latest",
                        "weight": 1.3,
                        "domain": "coding", 
                        "normalized_weight": 0.255,
                        "strengths": ["programming", "debugging", "architecture"]
                    },
                    {
                        "name": "llama2:latest",
                        "weight": 1.1,
                        "domain": "general",
                        "normalized_weight": 0.216,
                        "strengths": ["conversation", "knowledge", "reasoning"]
                    }
                ],
                "fusion_strategy": "dynamic_routing",
                "created_at": "2025-07-16T19:45:00.000000",
                "version": 1
            },
            "fusion_params": {
                "total_parameters": 1999999999,
                "combined_capabilities": [
                    "reasoning", "conversation", "debugging", "knowledge",
                    "deep_reasoning", "general", "code_generation", 
                    "following_instructions", "programming", "architecture", "math"
                ],
                "fusion_method": "weighted_average",
                "source_models": 4
            },
            "created_at": "2025-07-16T19:45:00.000000",
            "last_updated": "2025-07-16T19:45:00.000000",
            "updated_by": "auto_repair"
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print("✅ Default fusion configuration created")
    
    def run_full_repair(self):
        """Run complete system repair"""
        print("🔧 FUSION SYSTEM AUTO-REPAIR")
        print("=" * 50)
        
        repairs_needed = []
        
        # Check all systems
        if not self.check_python_environment():
            repairs_needed.append("python_env")
        
        if not self.check_dependencies():
            repairs_needed.append("dependencies")
        
        if not self.check_services():
            repairs_needed.append("services")
        
        self.repair_fusion_config()
        
        # Perform repairs
        if "dependencies" in repairs_needed:
            self.repair_dependencies()
        
        if "services" in repairs_needed:
            self.restart_services()
        
        # Final check
        print("\n🔍 Final system check...")
        if self.check_services():
            print("\n🎉 System repair completed successfully!")
            print("🚀 All systems operational")
            return True
        else:
            print("\n❌ Some issues remain - manual intervention may be required")
            return False

def main():
    """Main repair function"""
    repair_tool = FusionAutoRepair()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        print("🔍 SYSTEM HEALTH CHECK")
        print("=" * 30)
        repair_tool.check_python_environment()
        repair_tool.check_dependencies()
        repair_tool.check_services()
        repair_tool.repair_fusion_config()
    else:
        repair_tool.run_full_repair()

if __name__ == "__main__":
    main()
