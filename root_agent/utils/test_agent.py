#!/usr/bin/env python3
"""
Root Agent Test Suite
Verifies all agent functions work correctly
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import RootSystemAgent

class AgentTester:
    """Test suite for root agent functionality"""
    
    def __init__(self):
        self.agent = RootSystemAgent()
        self.test_results = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="root_agent_test_"))
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} {test_name}: {message}")
    
    def test_basic_functionality(self):
        """Test basic agent functionality"""
        print("\n🧪 Testing Basic Functionality")
        print("-" * 40)
        
        # Test command execution
        try:
            result = self.agent.run_cmd("echo 'test command'")
            success = "test command" in result
            self.log_test("Command Execution", success, f"Output: {result.strip()}")
        except Exception as e:
            self.log_test("Command Execution", False, f"Error: {e}")
        
        # Test system info
        try:
            sys_info = self.agent.get_system_info()
            success = "system" in sys_info and "memory" in sys_info
            platform = sys_info.get("system", {}).get("platform", "Unknown")
            self.log_test("System Info", success, f"Platform: {platform}")
        except Exception as e:
            self.log_test("System Info", False, f"Error: {e}")
    
    def test_file_operations(self):
        """Test file operations"""
        print("\n📁 Testing File Operations")
        print("-" * 40)
        
        test_file = self.temp_dir / "test_file.txt"
        test_content = "This is a test file content"
        
        # Test file writing
        try:
            success = self.agent.write_file(str(test_file), test_content)
            self.log_test("File Writing", success, f"File: {test_file}")
        except Exception as e:
            self.log_test("File Writing", False, f"Error: {e}")
            return
        
        # Test file reading
        try:
            content = self.agent.read_file(str(test_file))
            success = content == test_content
            self.log_test("File Reading", success, f"Content match: {success}")
        except Exception as e:
            self.log_test("File Reading", False, f"Error: {e}")
        
        # Test config modification
        try:
            config_file = self.temp_dir / "config.txt"
            success = self.agent.modify_config(str(config_file), "config=value")
            self.log_test("Config Modification", success, f"Config file: {config_file}")
        except Exception as e:
            self.log_test("Config Modification", False, f"Error: {e}")
        
        # Test directory listing
        try:
            fs_info = self.agent.list_filesystem(str(self.temp_dir), max_depth=1)
            success = "files" in fs_info
            file_count = len(fs_info.get("files", []))
            self.log_test("Directory Listing", success, f"Found {file_count} files")
        except Exception as e:
            self.log_test("Directory Listing", False, f"Error: {e}")
    
    def test_security_features(self):
        """Test security features"""
        print("\n🔒 Testing Security Features")
        print("-" * 40)
        
        # Test dangerous command blocking
        try:
            result = self.agent.run_cmd("rm -rf /")
            success = "ERROR" in result and "blocked" in result.lower()
            self.log_test("Dangerous Command Block", success, "Blocked rm -rf /")
        except Exception as e:
            self.log_test("Dangerous Command Block", False, f"Error: {e}")
        
        # Test protected file blocking
        try:
            result = self.agent.write_file("/etc/shadow", "malicious content")
            success = not result  # Should return False
            self.log_test("Protected File Block", success, "Blocked /etc/shadow write")
        except Exception as e:
            self.log_test("Protected File Block", False, f"Error: {e}")
        
        # Test rate limiting (simulate fast requests)
        try:
            # Reset rate limit counter
            self.agent.operation_count = 0
            
            # Perform many operations quickly
            blocked_count = 0
            for i in range(105):  # Exceed limit of 100
                result = self.agent.run_cmd("echo 'rate test'")
                if "Rate limit" in result:
                    blocked_count += 1
                    break
            
            success = blocked_count > 0
            self.log_test("Rate Limiting", success, f"Blocked after {100-blocked_count} operations")
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Error: {e}")
    
    def test_system_monitoring(self):
        """Test system monitoring features"""
        print("\n📊 Testing System Monitoring")
        print("-" * 40)
        
        # Test removable drive detection
        try:
            drives = self.agent.detect_removable_drives()
            success = isinstance(drives, list)
            drive_count = len(drives)
            self.log_test("Drive Detection", success, f"Found {drive_count} drives")
        except Exception as e:
            self.log_test("Drive Detection", False, f"Error: {e}")
        
        # Test log wiping (safe test)
        try:
            # Create test log directory
            test_log_dir = self.temp_dir / "test_logs"
            test_log_dir.mkdir()
            
            # Create test log files
            for i in range(3):
                log_file = test_log_dir / f"test{i}.log"
                log_file.write_text(f"Test log {i}")
            
            # Test log wiping
            success = self.agent.wipe_logs(str(test_log_dir))
            remaining_logs = list(test_log_dir.glob("*.log"))
            
            self.log_test("Log Wiping", success, f"Wiped logs, {len(remaining_logs)} remaining")
        except Exception as e:
            self.log_test("Log Wiping", False, f"Error: {e}")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling")
        print("-" * 40)
        
        # Test non-existent file reading
        try:
            result = self.agent.read_file("/nonexistent/file.txt")
            success = "ERROR" in result
            self.log_test("Non-existent File", success, "Properly handled missing file")
        except Exception as e:
            self.log_test("Non-existent File", False, f"Error: {e}")
        
        # Test invalid command
        try:
            result = self.agent.run_cmd("invalid_command_xyz_123")
            success = "ERROR" in result or "command not found" in result.lower()
            self.log_test("Invalid Command", success, "Properly handled invalid command")
        except Exception as e:
            self.log_test("Invalid Command", False, f"Error: {e}")
        
        # Test permission denied simulation
        try:
            result = self.agent.delete_file("/sys/kernel")
            success = not result  # Should fail
            self.log_test("Permission Handling", success, "Properly handled permission issues")
        except Exception as e:
            self.log_test("Permission Handling", False, f"Error: {e}")
    
    def cleanup(self):
        """Clean up test files"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"\n🧹 Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Could not clean up test directory: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🤖 ROOT AGENT TEST SUITE")
        print("=" * 50)
        
        try:
            self.test_basic_functionality()
            self.test_file_operations()
            self.test_security_features()
            self.test_system_monitoring()
            self.test_error_handling()
            
            # Print summary
            print("\n📊 TEST SUMMARY")
            print("=" * 50)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["success"])
            failed_tests = total_tests - passed_tests
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests} ✅")
            print(f"Failed: {failed_tests} ❌")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests > 0:
                print("\n❌ Failed Tests:")
                for result in self.test_results:
                    if not result["success"]:
                        print(f"  • {result['test']}: {result['message']}")
            
            print(f"\n🔍 Operations Logged: {len(self.agent.operations_log)}")
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
        finally:
            self.cleanup()

def main():
    """Main test function"""
    if os.name == 'posix' and os.geteuid() != 0:
        print("⚠️ Warning: Some tests may fail without root privileges")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    tester = AgentTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 