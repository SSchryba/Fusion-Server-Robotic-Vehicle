#!/usr/bin/env python3
"""
Root Agent Demo Script
Demonstrates all capabilities of the root-level autonomous agent
⚠️  WARNING: This demo performs actual system operations
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import RootSystemAgent

def print_banner():
    """Print demo banner"""
    print("="*60)
    print("🤖 ROOT-LEVEL AUTONOMOUS AI AGENT DEMO")
    print("="*60)
    print("⚠️  WARNING: This agent has full system access!")
    print("Only proceed if you understand the risks.")
    print("="*60)

def demo_basic_operations(agent):
    """Demonstrate basic agent operations"""
    print("\n🔧 1. BASIC OPERATIONS")
    print("-" * 30)
    
    # Test command execution
    print("Testing command execution...")
    result = agent.run_cmd("echo 'Hello from root agent'")
    print(f"Command result: {result.strip()}")
    
    # Test system info
    print("\nGetting system information...")
    sys_info = agent.get_system_info()
    print(f"System: {sys_info['system']['platform']} {sys_info['system']['platform_version']}")
    print(f"Memory: {sys_info['memory']['percent_used']:.1f}% used")
    print(f"Processes: {sys_info['processes']}")

def demo_filesystem_operations(agent):
    """Demonstrate filesystem operations"""
    print("\n📁 2. FILESYSTEM OPERATIONS")
    print("-" * 30)
    
    # Create test directory
    test_dir = Path("test_root_agent")
    test_file = test_dir / "test_file.txt"
    
    print("Creating test directory and file...")
    test_dir.mkdir(exist_ok=True)
    
    # Test file writing
    test_content = f"Test file created by root agent at {datetime.now()}"
    success = agent.write_file(str(test_file), test_content)
    print(f"File write: {'✅ Success' if success else '❌ Failed'}")
    
    # Test file reading
    if success:
        content = agent.read_file(str(test_file))
        print(f"File read: {content[:50]}...")
    
    # Test directory listing
    print("\nListing current directory...")
    fs_info = agent.list_filesystem(".", max_depth=1)
    if "files" in fs_info:
        print(f"Found {len(fs_info['files'])} files and {len(fs_info['directories'])} directories")
    
    # Test config modification (safe example)
    config_file = test_dir / "config.json"
    config_data = {
        "agent_name": "root_agent",
        "version": "1.0.0",
        "created": datetime.now().isoformat()
    }
    
    print("\nModifying configuration file...")
    success = agent.modify_config(str(config_file), json.dumps(config_data, indent=2))
    print(f"Config modification: {'✅ Success' if success else '❌ Failed'}")
    
    # Clean up
    print("\nCleaning up test files...")
    cleanup_success = agent.delete_file(str(test_dir))
    print(f"Cleanup: {'✅ Success' if cleanup_success else '❌ Failed'}")

def demo_system_monitoring(agent):
    """Demonstrate system monitoring capabilities"""
    print("\n📊 3. SYSTEM MONITORING")
    print("-" * 30)
    
    # Get removable drives
    print("Detecting removable drives...")
    drives = agent.detect_removable_drives()
    
    removable_count = sum(1 for drive in drives if drive.get("removable", False))
    encrypted_count = sum(1 for drive in drives if drive.get("encrypted", False))
    
    print(f"Found {len(drives)} total drives")
    print(f"Removable drives: {removable_count}")
    print(f"Encrypted volumes: {encrypted_count}")
    
    # Display drive information
    for drive in drives[:3]:  # Show first 3 drives
        print(f"  📱 {drive['device']} ({drive['fstype']}) -> {drive['mountpoint']}")
        if drive.get("removable"):
            print("    🔌 Removable")
        if drive.get("encrypted"):
            print("    🔒 Encrypted")

def demo_security_features(agent):
    """Demonstrate security features"""
    print("\n🔒 4. SECURITY FEATURES")
    print("-" * 30)
    
    # Test rate limiting
    print("Testing rate limiting...")
    fast_commands = ["echo 'test'"] * 5
    
    start_time = time.time()
    for i, cmd in enumerate(fast_commands):
        result = agent.run_cmd(cmd)
        if "Rate limit" in result:
            print(f"Rate limit triggered at command {i+1}")
            break
    
    # Test blocked operations
    print("\nTesting security blocks...")
    
    # Try to access protected file
    protected_content = agent.read_file("/etc/shadow")
    if "ERROR" in protected_content:
        print("✅ Protected file access properly blocked")
    
    # Try dangerous command
    dangerous_result = agent.run_cmd("rm -rf /")
    if "ERROR" in dangerous_result:
        print("✅ Dangerous command properly blocked")
    
    # Show operations log
    print(f"\nOperations logged: {len(agent.operations_log)}")
    if agent.operations_log:
        latest_op = agent.operations_log[-1]
        print(f"Latest operation: {latest_op['operation']} on {latest_op['path']} -> {latest_op['result']}")

def demo_advanced_features(agent):
    """Demonstrate advanced features"""
    print("\n🚀 5. ADVANCED FEATURES")
    print("-" * 30)
    
    # Test log management (safe example)
    test_log_dir = Path("test_logs")
    test_log_dir.mkdir(exist_ok=True)
    
    # Create test log files
    for i in range(3):
        log_file = test_log_dir / f"test{i}.log"
        with open(log_file, 'w') as f:
            f.write(f"Test log {i}\n")
    
    print("Created test log files...")
    
    # Test log wiping
    wipe_success = agent.wipe_logs(str(test_log_dir))
    print(f"Log wiping: {'✅ Success' if wipe_success else '❌ Failed'}")
    
    # Clean up
    try:
        test_log_dir.rmdir()
    except:
        pass
    
    # Show agent statistics
    print("\nAgent Statistics:")
    uptime = datetime.now() - agent.start_time
    print(f"  Uptime: {uptime}")
    print(f"  Total operations: {len(agent.operations_log)}")
    print(f"  Success rate: {sum(1 for op in agent.operations_log if op['result'] == 'success') / len(agent.operations_log) * 100:.1f}%")

def main():
    """Main demo function"""
    print_banner()
    
    # Check if running as root
    if os.name == 'posix' and os.geteuid() != 0:
        print("⚠️  This demo requires root privileges for full functionality.")
        print("Run with: sudo python3 demo.py")
        
        # Ask user if they want to continue with limited functionality
        response = input("\nContinue with limited functionality? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Initialize agent
    print("\n🚀 Initializing Root Agent...")
    try:
        agent = RootSystemAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Run demos
    try:
        demo_basic_operations(agent)
        demo_filesystem_operations(agent)
        demo_system_monitoring(agent)
        demo_security_features(agent)
        demo_advanced_features(agent)
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("📊 Summary:")
        print(f"  • Total operations performed: {len(agent.operations_log)}")
        print(f"  • Agent uptime: {datetime.now() - agent.start_time}")
        print(f"  • Security blocks triggered: {sum(1 for op in agent.operations_log if 'blocked' in op['result'])}")
        print("\n⚠️  Remember: This agent has full system access.")
        print("Use responsibly and only on systems you own.")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    finally:
        print("\n👋 Demo finished.")

if __name__ == "__main__":
    main() 