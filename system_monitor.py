#!/usr/bin/env python3
"""
System Resource Monitor
Safe monitoring of CPU, memory, disk, and network usage for AI development environment
"""

import psutil
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class SystemMonitor:
    """Safe system resource monitoring"""
    
    def __init__(self, log_file: str = "logs/system_metrics.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU usage information"""
        return {
            "usage_percent": psutil.cpu_percent(interval=1),
            "usage_per_core": psutil.cpu_percent(interval=1, percpu=True),
            "core_count": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information"""
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "virtual": {
                "total": virtual.total,
                "available": virtual.available,
                "used": virtual.used,
                "free": virtual.free,
                "percent": virtual.percent
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            }
        }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        disk_usage = {}
        
        # Get all disk partitions
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.device] = {
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0
                }
            except PermissionError:
                # Skip partitions we can't access
                continue
        
        # Disk I/O statistics
        try:
            io_stats = psutil.disk_io_counters()
            disk_io = io_stats._asdict() if io_stats else {}
        except:
            disk_io = {}
        
        return {
            "usage": disk_usage,
            "io_stats": disk_io
        }
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network usage information"""
        try:
            net_io = psutil.net_io_counters()
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            
            return {
                "total": net_io._asdict() if net_io else {},
                "per_interface": {
                    interface: stats._asdict() 
                    for interface, stats in net_io_per_nic.items()
                }
            }
        except:
            return {"total": {}, "per_interface": {}}
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get basic process information"""
        process_count = len(psutil.pids())
        
        # Get top 5 CPU-consuming processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        top_processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
        
        return {
            "total_count": process_count,
            "top_cpu_consumers": top_processes
        }
    
    def get_ai_services_status(self) -> Dict[str, Any]:
        """Check status of known AI services"""
        ai_services = {
            "fusion_tools": {"port": 8000, "status": "unknown"},
            "unified_control": {"port": 9000, "status": "unknown"},
            "quantum_agent": {"port": 8002, "status": "unknown"},
            "root_agent": {"port": 5000, "status": "unknown"},
            "budee_vehicle": {"port": None, "status": "unknown"}
        }
        
        # Check for known AI processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                
                if 'fusion' in name or 'fusion' in cmdline:
                    ai_services["fusion_tools"]["status"] = "running"
                elif 'control' in name or 'control_server' in cmdline:
                    ai_services["unified_control"]["status"] = "running"
                elif 'quantum' in name or 'quantum' in cmdline:
                    ai_services["quantum_agent"]["status"] = "running"
                elif 'root_agent' in name or 'root_agent' in cmdline:
                    ai_services["root_agent"]["status"] = "running"
                elif 'budee' in name or 'budee' in cmdline:
                    ai_services["budee_vehicle"]["status"] = "running"
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check quantum agent specifically
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path.cwd() / "quantum_agent"))
            from quantum_agent_orchestrator import QuantumAgentOrchestrator
            ai_services["quantum_agent"]["status"] = "available"
        except ImportError:
            ai_services["quantum_agent"]["status"] = "not installed"
        
        # Check root agent specifically
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path.cwd() / "root_agent"))
            from agent import RootSystemAgent
            ai_services["root_agent"]["status"] = "available"
        except ImportError:
            ai_services["root_agent"]["status"] = "not installed"
        
        return ai_services
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        timestamp = datetime.now()
        
        metrics = {
            "timestamp": timestamp.isoformat(),
            "unix_timestamp": timestamp.timestamp(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "processes": self.get_process_info(),
            "ai_services": self.get_ai_services_status(),
            "system_info": {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        }
        
        return metrics
    
    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics to JSON file"""
        try:
            # Read existing log
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"metrics_history": []}
            
            # Add new metrics
            log_data["metrics_history"].append(metrics)
            
            # Keep only last 100 entries
            log_data["metrics_history"] = log_data["metrics_history"][-100:]
            log_data["last_updated"] = metrics["timestamp"]
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not log metrics: {e}")
    
    def monitor_once(self, output_format: str = "json") -> None:
        """Collect and display metrics once"""
        metrics = self.collect_metrics()
        
        if output_format == "json":
            print(json.dumps(metrics, indent=2))
        elif output_format == "summary":
            self.print_summary(metrics)
        
        # Log to file
        self.log_metrics(metrics)
    
    def print_summary(self, metrics: Dict[str, Any]) -> None:
        """Print human-readable summary"""
        print("🖥️  SYSTEM RESOURCE MONITOR")
        print("=" * 50)
        print(f"Timestamp: {metrics['timestamp']}")
        print(f"Uptime: {metrics['system_info']['uptime_seconds']:.0f} seconds")
        print()
        
        # CPU
        cpu = metrics['cpu']
        print(f"🔥 CPU: {cpu['usage_percent']:.1f}% | Cores: {cpu['core_count']} physical, {cpu['logical_cores']} logical")
        
        # Memory
        mem = metrics['memory']['virtual']
        print(f"🧠 Memory: {mem['percent']:.1f}% used ({mem['used']//1024//1024//1024:.1f}GB / {mem['total']//1024//1024//1024:.1f}GB)")
        
        # Disk
        print("💾 Disk Usage:")
        for device, info in metrics['disk']['usage'].items():
            print(f"   {device}: {info['percent']:.1f}% used ({info['free']//1024//1024//1024:.1f}GB free)")
        
        # AI Services
        print("🤖 AI Services:")
        for service, info in metrics['ai_services'].items():
            status_icon = "✅" if info['status'] == "running" else "⏸️"
            print(f"   {status_icon} {service}: {info['status']}")
        
        print()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get simplified system statistics for API usage"""
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()
        
        return {
            "cpu_percent": cpu_info["usage_percent"],
            "memory_percent": memory_info["virtual"]["percent"],
            "disk_percent": list(disk_info["usage"].values())[0]["percent"] if disk_info["usage"] else 0,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="System Resource Monitor")
    parser.add_argument('--format', choices=['json', 'summary'], default='json',
                       help='Output format')
    parser.add_argument('--log-file', default='logs/system_metrics.json',
                       help='Log file path')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously (every 30 seconds)')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(log_file=args.log_file)
    
    if args.continuous:
        print("Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                monitor.monitor_once(args.format)
                if args.format == "summary":
                    print("\n" + "="*50)
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        monitor.monitor_once(args.format)

if __name__ == "__main__":
    main()