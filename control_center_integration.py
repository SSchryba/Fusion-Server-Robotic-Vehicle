#!/usr/bin/env python3
"""
Control Center Integration
Provides secure hooks for the Unified Control Center dashboard
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Import our monitoring modules
from system_monitor import SystemMonitor
from safe_services_scan import SafeServicesScanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminCommandLogger:
    """Secure logging of administrative commands and interactions"""
    
    def __init__(self, log_file: str = "logs/admin_commands.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Initialize log structure if it doesn't exist
        if not self.log_file.exists():
            self._initialize_log()
    
    def _initialize_log(self):
        """Initialize admin command log structure"""
        initial_data = {
            "log_info": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "description": "Administrative command and interaction log for AI Control Center"
            },
            "admin_sessions": [],
            "command_history": [],
            "security_events": [],
            "system_changes": []
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    def log_command(self, command: str, user: str, result: Dict[str, Any], 
                   command_type: str = "system") -> None:
        """Log an administrative command execution"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            command_entry = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "user": user,
                "command_type": command_type,
                "result": result,
                "success": result.get('success', False),
                "session_id": self._get_current_session_id()
            }
            
            data["command_history"].append(command_entry)
            
            # Keep only last 1000 commands
            data["command_history"] = data["command_history"][-1000:]
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log command: {e}")
    
    def log_security_event(self, event_type: str, description: str, 
                          severity: str = "info") -> None:
        """Log a security-related event"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            security_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "description": description,
                "severity": severity,
                "session_id": self._get_current_session_id()
            }
            
            data["security_events"].append(security_entry)
            
            # Keep only last 500 security events
            data["security_events"] = data["security_events"][-500:]
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def start_session(self, user: str) -> str:
        """Start a new admin session"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            session_id = f"session_{int(time.time())}"
            session_entry = {
                "session_id": session_id,
                "user": user,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "commands_executed": 0,
                "active": True
            }
            
            data["admin_sessions"].append(session_entry)
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return "session_error"
    
    def end_session(self, session_id: str) -> None:
        """End an admin session"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            for session in data["admin_sessions"]:
                if session["session_id"] == session_id:
                    session["end_time"] = datetime.now().isoformat()
                    session["active"] = False
                    break
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def _get_current_session_id(self) -> str:
        """Get the current active session ID"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            
            for session in reversed(data["admin_sessions"]):
                if session.get("active", False):
                    return session["session_id"]
            
            return "no_session"
            
        except Exception as e:
            return "error_session"

class ControlCenterDashboard:
    """Main dashboard integration class for the Control Center"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.services_scanner = SafeServicesScanner()
        self.admin_logger = AdminCommandLogger()
        
        # Whitelist of safe commands
        self.safe_commands = {
            'system_info': ['systeminfo', 'wmic', 'tasklist', 'netstat'],
            'process': ['tasklist', 'wmic process'],
            'network': ['netstat', 'ping', 'nslookup'],
            'disk': ['wmic logicaldisk', 'dir'],
            'ai_status': ['python', 'curl', 'powershell']
        }
    
    def user_confirm(self, message: str, command: str = "") -> bool:
        """User confirmation pattern for all administrative actions"""
        print(f"\n🔐 Administrative Action Required")
        print(f"Action: {message}")
        if command:
            print(f"Command: {command}")
        
        response = input(f"❓ Confirm execution? (y/N): ").lower().strip()
        confirmed = response in ['y', 'yes']
        
        # Log the confirmation attempt
        self.admin_logger.log_security_event(
            "user_confirmation",
            f"User {'confirmed' if confirmed else 'denied'}: {message}",
            "info"
        )
        
        return confirmed
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics for dashboard"""
        try:
            metrics = self.system_monitor.collect_metrics()
            
            # Simplify for dashboard consumption
            dashboard_metrics = {
                "timestamp": metrics["timestamp"],
                "cpu_percent": metrics["cpu"]["usage_percent"],
                "memory_percent": metrics["memory"]["virtual"]["percent"],
                "disk_usage": {
                    device: info["percent"] 
                    for device, info in metrics["disk"]["usage"].items()
                },
                "ai_services": metrics["ai_services"],
                "process_count": metrics["processes"]["total_count"],
                "uptime_seconds": metrics["system_info"]["uptime_seconds"]
            }
            
            return {"success": True, "data": dashboard_metrics}
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"success": False, "error": str(e)}
    
    def get_services_snapshot(self) -> Dict[str, Any]:
        """Get current services snapshot for dashboard"""
        try:
            scan_results = self.services_scanner.scan_all_processes()
            
            # Simplify for dashboard consumption
            snapshot = {
                "timestamp": scan_results["scan_info"]["timestamp"],
                "statistics": scan_results["statistics"],
                "ai_processes": len(scan_results["process_categories"]["ai_server_processes"]),
                "idle_processes": len(scan_results["process_categories"]["potentially_idle_processes"]),
                "recommendations": []
            }
            
            # Add top recommendations
            for proc in scan_results["process_categories"]["potentially_idle_processes"][:5]:
                snapshot["recommendations"].append({
                    "name": proc["name"],
                    "pid": proc["pid"],
                    "action": proc["recommendation"]["action"],
                    "reason": proc["recommendation"]["reason"]
                })
            
            return {"success": True, "data": snapshot}
            
        except Exception as e:
            logger.error(f"Failed to get services snapshot: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_safe_command(self, command: str, category: str = "system_info") -> Dict[str, Any]:
        """Execute a whitelisted command with user confirmation"""
        
        # Validate command against whitelist
        command_parts = command.lower().split()
        if not command_parts:
            return {"success": False, "error": "Empty command"}
        
        base_command = command_parts[0]
        is_safe = any(
            any(safe_cmd in base_command for safe_cmd in safe_cmds)
            for safe_cmds in self.safe_commands.values()
        )
        
        if not is_safe:
            self.admin_logger.log_security_event(
                "unsafe_command_blocked",
                f"Blocked unsafe command: {command}",
                "warning"
            )
            return {"success": False, "error": "Command not in safe whitelist"}
        
        # Require user confirmation
        if not self.user_confirm(f"Execute system command", command):
            return {"success": False, "error": "User denied execution"}
        
        try:
            # Execute the command safely
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            execution_result = {
                "success": True,
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout[:2000],  # Limit output size
                "stderr": result.stderr[:1000] if result.stderr else "",
                "execution_time": datetime.now().isoformat()
            }
            
            # Log the command execution
            self.admin_logger.log_command(
                command, 
                "dashboard_user", 
                execution_result,
                category
            )
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            error_result = {"success": False, "error": "Command timed out"}
            self.admin_logger.log_command(command, "dashboard_user", error_result, category)
            return error_result
            
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            self.admin_logger.log_command(command, "dashboard_user", error_result, category)
            return error_result
    
    def get_admin_log_summary(self) -> Dict[str, Any]:
        """Get summary of recent administrative activities"""
        try:
            with open(self.admin_logger.log_file, 'r') as f:
                data = json.load(f)
            
            # Get recent activity
            recent_commands = data["command_history"][-10:]  # Last 10 commands
            recent_security = data["security_events"][-5:]   # Last 5 security events
            active_sessions = [s for s in data["admin_sessions"] if s.get("active", False)]
            
            summary = {
                "recent_commands": recent_commands,
                "recent_security_events": recent_security,
                "active_sessions": active_sessions,
                "total_commands": len(data["command_history"]),
                "total_security_events": len(data["security_events"]),
                "total_sessions": len(data["admin_sessions"])
            }
            
            return {"success": True, "data": summary}
            
        except Exception as e:
            logger.error(f"Failed to get admin log summary: {e}")
            return {"success": False, "error": str(e)}
    
    def dashboard_api_handler(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main API handler for dashboard requests"""
        params = params or {}
        
        try:
            if endpoint == "metrics":
                return self.get_real_time_metrics()
            
            elif endpoint == "services":
                return self.get_services_snapshot()
            
            elif endpoint == "execute":
                command = params.get('command', '')
                category = params.get('category', 'system_info')
                return self.execute_safe_command(command, category)
            
            elif endpoint == "admin_log":
                return self.get_admin_log_summary()
            
            elif endpoint == "fusion_status":
                # Check fusion system status
                return self.execute_safe_command(
                    "curl -s http://localhost:8000/fusion/status", 
                    "ai_status"
                )
            
            elif endpoint == "ai_services":
                metrics = self.get_real_time_metrics()
                if metrics["success"]:
                    return {
                        "success": True,
                        "data": metrics["data"]["ai_services"]
                    }
                return metrics
            
            else:
                return {"success": False, "error": f"Unknown endpoint: {endpoint}"}
                
        except Exception as e:
            logger.error(f"Dashboard API error for {endpoint}: {e}")
            return {"success": False, "error": str(e)}

def create_dashboard_html_integration() -> str:
    """Generate HTML/JavaScript integration code for the dashboard"""
    
    integration_code = '''
    <!-- Control Center Dashboard Integration -->
    <script>
    // Real-time metrics updater
    async function updateDashboardMetrics() {
        try {
            const response = await fetch('/api/dashboard/metrics');
            const data = await response.json();
            
            if (data.success) {
                // Update CPU gauge
                document.getElementById('cpu-usage').textContent = 
                    data.data.cpu_percent.toFixed(1) + '%';
                
                // Update Memory gauge  
                document.getElementById('memory-usage').textContent = 
                    data.data.memory_percent.toFixed(1) + '%';
                
                // Update AI services status
                updateAIServicesStatus(data.data.ai_services);
                
                // Update process count
                document.getElementById('process-count').textContent = 
                    data.data.process_count;
            }
        } catch (error) {
            console.error('Failed to update metrics:', error);
        }
    }
    
    function updateAIServicesStatus(services) {
        for (const [service, info] of Object.entries(services)) {
            const element = document.getElementById(`service-${service}`);
            if (element) {
                element.className = info.status === 'running' ? 
                    'service-status online' : 'service-status offline';
                element.textContent = info.status;
            }
        }
    }
    
    // Secure command execution with confirmation
    async function executeSecureCommand(command, category = 'system_info') {
        const confirmed = confirm(`Execute command: ${command}?`);
        if (!confirmed) return;
        
        try {
            const response = await fetch('/api/dashboard/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command, category})
            });
            
            const result = await response.json();
            displayCommandResult(result);
            
        } catch (error) {
            console.error('Command execution failed:', error);
        }
    }
    
    function displayCommandResult(result) {
        const output = document.getElementById('command-output');
        if (result.success) {
            output.innerHTML = `
                <div class="command-success">
                    <strong>Command:</strong> ${result.command}<br>
                    <strong>Output:</strong><br>
                    <pre>${result.stdout}</pre>
                    ${result.stderr ? `<strong>Errors:</strong><br><pre>${result.stderr}</pre>` : ''}
                </div>
            `;
        } else {
            output.innerHTML = `
                <div class="command-error">
                    <strong>Error:</strong> ${result.error}
                </div>
            `;
        }
    }
    
    // Auto-refresh dashboard every 30 seconds
    setInterval(updateDashboardMetrics, 30000);
    
    // Initial load
    updateDashboardMetrics();
    </script>
    
    <style>
    .service-status.online { color: #4CAF50; }
    .service-status.offline { color: #f44336; }
    .command-success { background: #e8f5e8; padding: 10px; border-radius: 4px; }
    .command-error { background: #ffeaea; padding: 10px; border-radius: 4px; }
    </style>
    '''
    
    return integration_code

# Example usage and testing
def main():
    """Test the control center integration"""
    dashboard = ControlCenterDashboard()
    
    print("🔧 Testing Control Center Integration")
    print("=" * 50)
    
    # Test metrics
    print("📊 Getting real-time metrics...")
    metrics = dashboard.get_real_time_metrics()
    if metrics["success"]:
        print(f"✅ CPU: {metrics['data']['cpu_percent']:.1f}%")
        print(f"✅ Memory: {metrics['data']['memory_percent']:.1f}%")
        print(f"✅ Processes: {metrics['data']['process_count']}")
    
    # Test services scan
    print("\n🔍 Getting services snapshot...")
    services = dashboard.get_services_snapshot()
    if services["success"]:
        print(f"✅ AI Processes: {services['data']['ai_processes']}")
        print(f"✅ Idle Processes: {services['data']['idle_processes']}")
    
    # Test admin log
    print("\n📋 Getting admin log summary...")
    admin_log = dashboard.get_admin_log_summary()
    if admin_log["success"]:
        print(f"✅ Total Commands: {admin_log['data']['total_commands']}")
        print(f"✅ Active Sessions: {len(admin_log['data']['active_sessions'])}")
    
    print("\n✅ Control Center Integration Ready!")
    print("🔗 Use dashboard_api_handler() for web integration")

if __name__ == "__main__":
    main() 