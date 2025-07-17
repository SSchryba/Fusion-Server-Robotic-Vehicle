#!/usr/bin/env python3
"""
Root-Level Autonomous AI Agent
⚠️  WARNING: This agent has full system access and can cause permanent damage
Only use on systems you own and understand the risks
"""

import os
import sys
import subprocess
import logging
import time
import json
import shutil
import signal
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import psutil
import platform

# Configure logging
LOG_FILE = "/var/log/aiagent.log" if platform.system() == "Linux" else "logs/aiagent.log"

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RootSystemAgent:
    """Root-level system agent with full filesystem and execution access"""
    
    def __init__(self):
        self.is_running = False
        self.start_time = datetime.now()
        self.operations_log = []
        self.validate_root_access()
        self.setup_security_limits()
        
    def validate_root_access(self):
        """Validate that the agent has root/administrator privileges"""
        self.has_admin = False
        
        if platform.system() == "Linux":
            if os.geteuid() == 0:
                self.has_admin = True
                logger.info("Root privileges confirmed")
            else:
                logger.warning("Running without root privileges - some features limited")
        elif platform.system() == "Windows":
            try:
                import ctypes
                if ctypes.windll.shell32.IsUserAnAdmin():
                    self.has_admin = True
                    logger.info("Administrator privileges confirmed")
                else:
                    logger.warning("Running without administrator privileges - some features limited")
            except Exception as e:
                logger.warning(f"Could not verify admin privileges: {e}")
                
        # Don't exit - allow limited operation without admin privileges
    
    def setup_security_limits(self):
        """Setup security limits and safeguards"""
        self.dangerous_paths = {
            "/boot", "/dev", "/proc", "/sys", 
            "C:\\Windows\\System32", "C:\\Windows\\Boot"
        }
        self.protected_files = {
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
            "C:\\Windows\\System32\\config\\SAM"
        }
        self.max_operations_per_minute = 100
        self.operation_count = 0
        self.last_reset_time = time.time()
        
    def rate_limit_check(self) -> bool:
        """Check if operation is within rate limits"""
        current_time = time.time()
        if current_time - self.last_reset_time >= 60:
            self.operation_count = 0
            self.last_reset_time = current_time
        
        if self.operation_count >= self.max_operations_per_minute:
            logger.warning("⚠️ Rate limit exceeded. Blocking operation.")
            return False
        
        self.operation_count += 1
        return True
    
    def log_operation(self, operation: str, path: str = "", result: str = "success"):
        """Log all operations for auditing"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "path": path,
            "result": result
        }
        self.operations_log.append(log_entry)
        logger.info(f"Operation: {operation} on {path} - {result}")
    
    def run_cmd(self, cmd: str) -> str:
        """Execute arbitrary shell commands with logging and validation"""
        if not self.rate_limit_check():
            return "ERROR: Rate limit exceeded"
        
        # Basic command validation
        dangerous_commands = ["rm -rf /", "format", "del /f /s /q C:\\", "mkfs"]
        if any(danger in cmd.lower() for danger in dangerous_commands):
            self.log_operation("BLOCKED_COMMAND", cmd, "blocked_dangerous")
            return "ERROR: Dangerous command blocked"
        
        try:
            logger.info(f"Executing command: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout if result.returncode == 0 else result.stderr
            self.log_operation("SHELL_EXECUTE", cmd, "success" if result.returncode == 0 else "error")
            
            return output
            
        except subprocess.TimeoutExpired:
            self.log_operation("SHELL_EXECUTE", cmd, "timeout")
            return "ERROR: Command timed out"
        except Exception as e:
            self.log_operation("SHELL_EXECUTE", cmd, f"error: {str(e)}")
            return f"ERROR: {str(e)}"
    
    def read_file(self, path: str) -> str:
        """Read file contents with full filesystem access"""
        if not self.rate_limit_check():
            return "ERROR: Rate limit exceeded"
        
        try:
            file_path = Path(path)
            if not file_path.exists():
                self.log_operation("READ_FILE", path, "file_not_found")
                return "ERROR: File not found"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.log_operation("READ_FILE", path, "success")
            return content
            
        except PermissionError:
            self.log_operation("READ_FILE", path, "permission_denied")
            return "ERROR: Permission denied"
        except Exception as e:
            self.log_operation("READ_FILE", path, f"error: {str(e)}")
            return f"ERROR: {str(e)}"
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to file with full filesystem access"""
        if not self.rate_limit_check():
            return False
        
        # Check if path is protected
        if path in self.protected_files:
            self.log_operation("WRITE_FILE", path, "blocked_protected")
            logger.warning(f"⚠️ Blocked write to protected file: {path}")
            return False
        
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_operation("WRITE_FILE", path, "success")
            return True
            
        except Exception as e:
            self.log_operation("WRITE_FILE", path, f"error: {str(e)}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete file or directory with validation"""
        if not self.rate_limit_check():
            return False
        
        # Check if path is protected
        if path in self.protected_files or any(danger in path for danger in self.dangerous_paths):
            self.log_operation("DELETE_FILE", path, "blocked_protected")
            logger.warning(f"⚠️ Blocked deletion of protected path: {path}")
            return False
        
        try:
            file_path = Path(path)
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                self.log_operation("DELETE_FILE", path, "not_found")
                return False
            
            self.log_operation("DELETE_FILE", path, "success")
            return True
            
        except Exception as e:
            self.log_operation("DELETE_FILE", path, f"error: {str(e)}")
            return False
    
    def modify_config(self, path: str, new_contents: str) -> bool:
        """Modify configuration files with backup"""
        if not self.rate_limit_check():
            return False
        
        try:
            file_path = Path(path)
            
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{int(time.time())}")
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Write new contents
            success = self.write_file(path, new_contents)
            if success:
                self.log_operation("MODIFY_CONFIG", path, "success")
            
            return success
            
        except Exception as e:
            self.log_operation("MODIFY_CONFIG", path, f"error: {str(e)}")
            return False
    
    def list_filesystem(self, root_path: str = "/", max_depth: int = 3) -> Dict[str, Any]:
        """Recursively list filesystem with depth control"""
        if not self.rate_limit_check():
            return {"error": "Rate limit exceeded"}
        
        def scan_directory(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {"truncated": True}
            
            try:
                items = {"files": [], "directories": [], "special": []}
                
                for item in path.iterdir():
                    try:
                        if item.is_file():
                            items["files"].append({
                                "name": item.name,
                                "size": item.stat().st_size,
                                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                            })
                        elif item.is_dir():
                            subdir_info = {
                                "name": item.name,
                                "path": str(item)
                            }
                            if current_depth < max_depth:
                                subdir_info["contents"] = scan_directory(item, current_depth + 1)
                            items["directories"].append(subdir_info)
                        else:
                            items["special"].append({
                                "name": item.name,
                                "type": "symlink" if item.is_symlink() else "other"
                            })
                    except PermissionError:
                        continue
                    except Exception:
                        continue
                
                return items
                
            except PermissionError:
                return {"error": "Permission denied"}
            except Exception as e:
                return {"error": str(e)}
        
        try:
            root = Path(root_path)
            result = scan_directory(root)
            self.log_operation("LIST_FILESYSTEM", root_path, "success")
            return result
            
        except Exception as e:
            self.log_operation("LIST_FILESYSTEM", root_path, f"error: {str(e)}")
            return {"error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                "system": {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "architecture": platform.architecture(),
                    "processor": platform.processor(),
                    "hostname": platform.node()
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent_used": psutil.virtual_memory().percent
                },
                "disk": {
                    "partitions": [
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "usage": self._safe_disk_usage(partition.mountpoint)
                        }
                        for partition in psutil.disk_partitions()
                    ]
                },
                "network": {
                    "interfaces": dict(psutil.net_if_addrs()),
                    "connections": len(psutil.net_connections())
                },
                "processes": len(psutil.pids()),
                "agent": {
                    "uptime": str(datetime.now() - self.start_time),
                    "operations_count": len(self.operations_log),
                    "status": "running" if self.is_running else "stopped"
                }
            }
            
            self.log_operation("GET_SYSTEM_INFO", "", "success")
            return info
            
        except Exception as e:
            self.log_operation("GET_SYSTEM_INFO", "", f"error: {str(e)}")
            return {"error": str(e)}
    
    def wipe_logs(self, log_directory: str = "/var/log") -> bool:
        """Wipe logs from specified directory with safety checks"""
        if not self.rate_limit_check():
            return False
        
        try:
            log_path = Path(log_directory)
            if not log_path.exists():
                self.log_operation("WIPE_LOGS", log_directory, "directory_not_found")
                return False
            
            # Safety check - don't wipe system-critical logs
            critical_logs = {"auth.log", "syslog", "kern.log", "boot.log"}
            
            wiped_count = 0
            for log_file in log_path.glob("*.log"):
                if log_file.name not in critical_logs:
                    try:
                        log_file.unlink()
                        wiped_count += 1
                    except Exception as e:
                        logger.warning(f"Could not wipe {log_file}: {e}")
            
            self.log_operation("WIPE_LOGS", log_directory, f"wiped_{wiped_count}_files")
            return True
            
        except Exception as e:
            self.log_operation("WIPE_LOGS", log_directory, f"error: {str(e)}")
            return False
    
    def detect_removable_drives(self) -> List[Dict[str, Any]]:
        """Detect removable drives and encrypted volumes"""
        try:
            removable_drives = []
            
            for partition in psutil.disk_partitions():
                drive_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "removable": False,
                    "encrypted": False
                }
                
                # Check if removable (Linux)
                if platform.system() == "Linux":
                    if "/media" in partition.mountpoint or "/mnt" in partition.mountpoint:
                        drive_info["removable"] = True
                    
                    # Check for encrypted volumes (LUKS)
                    if "dm-crypt" in partition.fstype or "luks" in partition.fstype.lower():
                        drive_info["encrypted"] = True
                
                # Check if removable (Windows)
                elif platform.system() == "Windows":
                    try:
                        import ctypes
                        drive_type = ctypes.windll.kernel32.GetDriveTypeW(partition.device)
                        if drive_type == 2:  # DRIVE_REMOVABLE
                            drive_info["removable"] = True
                    except:
                        pass
                
                removable_drives.append(drive_info)
            
            self.log_operation("DETECT_REMOVABLE_DRIVES", "", "success")
            return removable_drives
            
        except Exception as e:
            self.log_operation("DETECT_REMOVABLE_DRIVES", "", f"error: {str(e)}")
            return []
    
    def start_background_service(self):
        """Start the agent as a background service"""
        self.is_running = True
        logger.info("🚀 Root Agent started as background service")
        
        try:
            while self.is_running:
                # Perform periodic system monitoring
                self.monitor_system()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Agent interrupted by user")
        finally:
            self.stop_service()
    
    def monitor_system(self):
        """Perform periodic system monitoring"""
        try:
            # Check system resources
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                logger.warning(f"⚠️ High memory usage: {memory_percent}%")
            
            # Check disk space
            for partition in psutil.disk_partitions():
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    percent_used = (disk_usage.used / disk_usage.total) * 100
                    if percent_used > 90:
                        logger.warning(f"⚠️ High disk usage on {partition.mountpoint}: {percent_used:.1f}%")
                except:
                    continue
            
            # Log operation count
            if len(self.operations_log) % 100 == 0 and len(self.operations_log) > 0:
                logger.info(f"📊 Total operations performed: {len(self.operations_log)}")
            
        except Exception as e:
            logger.error(f"Error in system monitoring: {e}")
    
    def stop_service(self):
        """Stop the background service"""
        self.is_running = False
        logger.info("🛑 Root Agent service stopped")
    
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_service()
        sys.exit(0)
    
    def _safe_disk_usage(self, mountpoint: str) -> Dict[str, Any]:
        """Safely get disk usage, handling inaccessible drives"""
        try:
            usage = psutil.disk_usage(mountpoint)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free
            }
        except (OSError, PermissionError):
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "error": "inaccessible"
            }

def main():
    """Main entry point for the root agent"""
    agent = RootSystemAgent()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, agent.signal_handler)
    signal.signal(signal.SIGTERM, agent.signal_handler)
    
    # Start as background service
    agent.start_background_service()

if __name__ == "__main__":
    main()