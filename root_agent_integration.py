#!/usr/bin/env python3
"""
Root Agent Integration for Fusion System
Creates secure integration between root agent and fusion system
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add root_agent to path
sys.path.append(str(Path(__file__).parent / "root_agent"))

try:
    from agent import RootSystemAgent
    ROOT_AGENT_AVAILABLE = True
except ImportError:
    ROOT_AGENT_AVAILABLE = False

class RootAgentFusionInterface:
    """Secure interface between root agent and fusion system"""
    
    def __init__(self):
        self.agent = None
        self.security_mode = "restricted"  # Default to restricted mode
        if ROOT_AGENT_AVAILABLE:
            try:
                self.agent = RootSystemAgent()
            except Exception as e:
                print(f"Failed to initialize root agent: {e}")
    
    async def get_root_agent_status(self) -> Dict[str, Any]:
        """Get root agent status for fusion system"""
        if not ROOT_AGENT_AVAILABLE or not self.agent:
            return {
                "available": False,
                "error": "Root agent not available"
            }
        
        return {
            "available": True,
            "status": "operational",
            "admin_privileges": self.agent.has_admin,
            "security_mode": self.security_mode,
            "operations_count": len(self.agent.operations_log),
            "uptime": str(datetime.now() - self.agent.start_time)
        }
    
    async def execute_safe_command(self, command: str) -> Dict[str, Any]:
        """Execute command with safety restrictions"""
        if not ROOT_AGENT_AVAILABLE or not self.agent:
            return {
                "success": False,
                "error": "Root agent not available"
            }
        
        # Additional safety checks for fusion integration
        forbidden_patterns = [
            "rm -rf", "del /f", "format", "mkfs", 
            "shutdown", "reboot", "halt", "poweroff",
            "passwd", "sudo", "su -"
        ]
        
        if any(pattern in command.lower() for pattern in forbidden_patterns):
            return {
                "success": False,
                "error": "Command blocked by fusion safety restrictions"
            }
        
        try:
            result = self.agent.run_cmd(command)
            return {
                "success": True,
                "output": result,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {e}"
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics via root agent"""
        if not ROOT_AGENT_AVAILABLE or not self.agent:
            return {
                "success": False,
                "error": "Root agent not available"
            }
        
        try:
            sys_info = self.agent.get_system_info()
            return {
                "success": True,
                "metrics": sys_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get system metrics: {e}"
            }
    
    async def scan_filesystem(self, path: str = ".", max_depth: int = 2) -> Dict[str, Any]:
        """Scan filesystem with safety limits"""
        if not ROOT_AGENT_AVAILABLE or not self.agent:
            return {
                "success": False,
                "error": "Root agent not available"
            }
        
        # Restrict dangerous paths
        dangerous_paths = ["/etc", "/sys", "/proc", "C:\\Windows\\System32"]
        if any(danger in path for danger in dangerous_paths):
            return {
                "success": False,
                "error": "Path access restricted for security"
            }
        
        try:
            result = self.agent.list_filesystem(path, max_depth)
            return {
                "success": True,
                "filesystem": result,
                "path": path
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Filesystem scan failed: {e}"
            }

# Global root agent interface
root_interface = RootAgentFusionInterface()

async def main():
    """Test root agent fusion interface"""
    print("🔗 Root Agent Fusion Interface Test")
    print("=" * 40)
    
    # Test status
    status = await root_interface.get_root_agent_status()
    print(f"Status: {status}")
    
    # Test safe command
    if status.get('available'):
        cmd_result = await root_interface.execute_safe_command("echo Fusion integration test")
        print(f"Command test: {cmd_result.get('success', False)}")
        
        # Test system metrics
        metrics = await root_interface.get_system_metrics()
        print(f"Metrics available: {metrics.get('success', False)}")

if __name__ == "__main__":
    asyncio.run(main())
