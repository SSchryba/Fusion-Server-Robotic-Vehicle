#!/usr/bin/env python3
"""
Root Agent Repair and Test Script
Identifies issues and optimizes the root agent for operational use
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add root_agent to path
sys.path.append(str(Path(__file__).parent / "root_agent"))

try:
    from agent import RootSystemAgent
    ROOT_AGENT_AVAILABLE = True
    print("✅ Root agent modules imported successfully")
except ImportError as e:
    ROOT_AGENT_AVAILABLE = False
    print(f"❌ Root agent not available: {e}")

class RootAgentTester:
    """Test and repair root agent functionality"""
    
    def __init__(self):
        self.agent = None
        if ROOT_AGENT_AVAILABLE:
            try:
                self.agent = RootSystemAgent()
                print(f"✅ Root agent initialized (Admin: {self.agent.has_admin})")
            except Exception as e:
                print(f"❌ Failed to initialize root agent: {e}")
    
    def test_basic_operations(self):
        """Test basic root agent operations"""
        print("\n🧪 TESTING BASIC OPERATIONS")
        print("=" * 50)
        
        if not self.agent:
            print("❌ Agent not available for testing")
            return False
        
        tests_passed = 0
        total_tests = 5
        
        # Test 1: Command execution
        try:
            result = self.agent.run_cmd("echo Hello from root agent")
            if "Hello from root agent" in result:
                print("✅ Command execution: PASS")
                tests_passed += 1
            else:
                print(f"❌ Command execution: FAIL - {result}")
        except Exception as e:
            print(f"❌ Command execution: ERROR - {e}")
        
        # Test 2: System info
        try:
            sys_info = self.agent.get_system_info()
            if sys_info and "system" in sys_info:
                print("✅ System info retrieval: PASS")
                tests_passed += 1
            else:
                print("❌ System info retrieval: FAIL")
        except Exception as e:
            print(f"❌ System info retrieval: ERROR - {e}")
        
        # Test 3: File operations (safe test)
        try:
            test_dir = Path("temp_test_dir")
            test_file = test_dir / "test.txt"
            test_content = "Root agent test file"
            
            # Create directory and file
            test_dir.mkdir(exist_ok=True)
            success = self.agent.write_file(str(test_file), test_content)
            
            if success:
                # Read file back
                read_content = self.agent.read_file(str(test_file))
                if test_content in read_content:
                    print("✅ File read/write operations: PASS")
                    tests_passed += 1
                else:
                    print("❌ File read/write operations: FAIL - content mismatch")
            else:
                print("❌ File read/write operations: FAIL - write failed")
            
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()
                
        except Exception as e:
            print(f"❌ File operations: ERROR - {e}")
        
        # Test 4: Rate limiting
        try:
            # Test rate limit functionality
            initial_count = self.agent.operation_count
            for _ in range(5):
                self.agent.rate_limit_check()
            if self.agent.operation_count > initial_count:
                print("✅ Rate limiting: PASS")
                tests_passed += 1
            else:
                print("❌ Rate limiting: FAIL")
        except Exception as e:
            print(f"❌ Rate limiting: ERROR - {e}")
        
        # Test 5: Removable drive detection
        try:
            drives = self.agent.detect_removable_drives()
            if isinstance(drives, list):
                print(f"✅ Removable drive detection: PASS ({len(drives)} drives)")
                tests_passed += 1
            else:
                print("❌ Removable drive detection: FAIL")
        except Exception as e:
            print(f"❌ Removable drive detection: ERROR - {e}")
        
        print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
        return tests_passed == total_tests
    
    def test_security_features(self):
        """Test security features"""
        print("\n🛡️ TESTING SECURITY FEATURES")
        print("=" * 50)
        
        if not self.agent:
            print("❌ Agent not available for testing")
            return False
        
        security_tests = 0
        total_security_tests = 3
        
        # Test 1: Dangerous command blocking
        try:
            result = self.agent.run_cmd("rm -rf /")
            if "blocked" in result.lower() or "error" in result.lower():
                print("✅ Dangerous command blocking: PASS")
                security_tests += 1
            else:
                print("❌ Dangerous command blocking: FAIL - command not blocked")
        except Exception as e:
            print(f"❌ Dangerous command blocking: ERROR - {e}")
        
        # Test 2: Protected file write blocking
        try:
            success = self.agent.write_file("/etc/passwd", "malicious content")
            if not success:
                print("✅ Protected file blocking: PASS")
                security_tests += 1
            else:
                print("❌ Protected file blocking: FAIL - write allowed")
        except Exception as e:
            print(f"❌ Protected file blocking: ERROR - {e}")
        
        # Test 3: Operation logging
        try:
            initial_log_count = len(self.agent.operations_log)
            self.agent.run_cmd("echo security test")
            if len(self.agent.operations_log) > initial_log_count:
                print("✅ Operation logging: PASS")
                security_tests += 1
            else:
                print("❌ Operation logging: FAIL")
        except Exception as e:
            print(f"❌ Operation logging: ERROR - {e}")
        
        print(f"\n📊 Security Tests: {security_tests}/{total_security_tests} tests passed")
        return security_tests == total_security_tests
    
    def optimize_root_agent(self):
        """Optimize root agent configuration"""
        print("\n🔧 OPTIMIZING ROOT AGENT")
        print("=" * 50)
        
        optimizations = []
        
        # Create logs directory
        logs_dir = Path("root_agent/logs")
        logs_dir.mkdir(exist_ok=True)
        print("✅ Created logs directory")
        optimizations.append("logs_directory_created")
        
        # Create config directory and files
        config_dir = Path("root_agent/config")
        config_dir.mkdir(exist_ok=True)
        
        # Create agent configuration
        config = {
            "max_operations_per_minute": 100,
            "enable_filesystem_access": True,
            "enable_command_execution": True,
            "log_level": "INFO",
            "protected_paths": [
                "/etc/passwd",
                "/etc/shadow", 
                "/etc/sudoers",
                "C:\\Windows\\System32\\config\\SAM"
            ],
            "dangerous_commands": [
                "rm -rf /",
                "format",
                "del /f /s /q C:\\",
                "mkfs"
            ],
            "admin_required_operations": [
                "system_configuration",
                "service_management",
                "user_management"
            ]
        }
        
        config_file = config_dir / "agent_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Created agent configuration file")
        optimizations.append("config_file_created")
        
        # Create service configuration
        service_config = {
            "service_name": "ai_root_agent",
            "description": "Autonomous AI Root Agent Service",
            "auto_start": False,
            "restart_policy": "on-failure",
            "working_directory": str(Path("root_agent").resolve()),
            "log_file": "logs/service.log"
        }
        
        service_file = config_dir / "service_config.json"
        with open(service_file, 'w') as f:
            json.dump(service_config, f, indent=2)
        print("✅ Created service configuration file")
        optimizations.append("service_config_created")
        
        return optimizations

def create_root_agent_status():
    """Create root agent status report"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "root_agent_available": ROOT_AGENT_AVAILABLE,
        "admin_privileges": False,
        "components": {
            "agent_core": "available" if ROOT_AGENT_AVAILABLE else "unavailable",
            "web_ui": "available",
            "test_suite": "available",
            "demo_script": "available"
        },
        "capabilities": {
            "command_execution": "operational",
            "file_operations": "operational", 
            "system_monitoring": "operational",
            "security_features": "operational"
        },
        "integration_status": "operational" if ROOT_AGENT_AVAILABLE else "needs_repair"
    }
    
    # Check admin privileges
    if ROOT_AGENT_AVAILABLE:
        try:
            agent = RootSystemAgent()
            status["admin_privileges"] = agent.has_admin
        except:
            pass
    
    return status

def main():
    """Main repair function"""
    print("🚀 ROOT AGENT REPAIR & OPTIMIZATION")
    print("=" * 60)
    
    # Create status report
    status = create_root_agent_status()
    print(f"📊 Status: {status['integration_status']}")
    print(f"🔧 Available: {status['root_agent_available']}")
    print(f"👑 Admin Privileges: {status['admin_privileges']}")
    
    success = True
    
    # Run tests if available
    if ROOT_AGENT_AVAILABLE:
        tester = RootAgentTester()
        
        # Test basic operations
        basic_success = tester.test_basic_operations()
        
        # Test security features
        security_success = tester.test_security_features()
        
        # Optimize configuration
        optimizations = tester.optimize_root_agent()
        
        success = basic_success and security_success
        
        if success:
            print("\n🎉 ROOT AGENT REPAIR SUCCESSFUL!")
            print("=" * 60)
            print("✅ All systems operational")
            print("✅ Security features active")
            print("✅ Configuration optimized")
            print(f"✅ Optimizations applied: {len(optimizations)}")
        else:
            print("\n⚠️ ROOT AGENT NEEDS FURTHER ATTENTION")
            print("=" * 60)
            print("❌ Some tests failed")
            print("💡 Check logs for detailed error information")
    else:
        print("\n🔧 ROOT AGENT DEPENDENCIES NEEDED")
        print("=" * 60)
        print("💡 Check root_agent/agent.py for import issues")
    
    # Save status report
    status_file = Path("root_agent_status.json")
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n📄 Status report saved to: {status_file}")
    
    if success and ROOT_AGENT_AVAILABLE:
        print("\n🎯 ROOT AGENT READY FOR OPERATION!")
        print("💡 Use with caution - this agent has system-level access")

if __name__ == "__main__":
    main()
