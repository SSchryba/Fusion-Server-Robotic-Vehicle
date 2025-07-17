#!/usr/bin/env python3
"""
Safe Services Scanner
Read-only analysis of running processes to identify potentially idle services
"""

import psutil
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

class SafeServicesScanner:
    """Safe, read-only process and service scanner"""
    
    def __init__(self, log_file: str = "logs/services_scan.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Define known critical system processes
        self.critical_processes = {
            # Windows system processes
            'system', 'registry', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
            'services.exe', 'lsass.exe', 'svchost.exe', 'dwm.exe', 'explorer.exe',
            'ntoskrnl.exe', 'kernel32.dll', 'ntdll.dll',
            
            # Windows security and drivers
            'antimalware', 'defender', 'security', 'driver', 'audio', 'display',
            'network', 'ethernet', 'wifi', 'bluetooth', 'usb', 'power',
            
            # Linux system processes (for cross-platform compatibility)
            'init', 'kthreadd', 'systemd', 'kernel', 'dbus', 'NetworkManager',
            'pulseaudio', 'gdm', 'gnome', 'kde', 'xorg', 'wayland'
        }
        
        # Define known AI server processes (keep these running)
        self.ai_server_processes = {
            'fusion', 'quantum', 'root_agent', 'budee', 'control_server',
            'ollama', 'llama', 'mistral', 'deepseek', 'codellama',
            'python.exe', 'node.exe', 'uvicorn', 'fastapi', 'flask'
        }
        
        # Define development tools (keep these running)
        self.development_processes = {
            'cursor', 'code', 'vscode', 'git', 'github', 'python', 'node',
            'npm', 'pip', 'conda', 'docker', 'chrome', 'firefox', 'edge'
        }
    
    def is_critical_process(self, process_name: str, cmdline: str) -> bool:
        """Check if process is critical to system operation"""
        name_lower = process_name.lower()
        cmd_lower = cmdline.lower()
        
        # Check against critical process patterns
        for critical in self.critical_processes:
            if critical in name_lower or critical in cmd_lower:
                return True
        
        return False
    
    def is_ai_server_process(self, process_name: str, cmdline: str) -> bool:
        """Check if process is part of AI server infrastructure"""
        name_lower = process_name.lower()
        cmd_lower = cmdline.lower()
        
        # Check against AI server patterns
        for ai_pattern in self.ai_server_processes:
            if ai_pattern in name_lower or ai_pattern in cmd_lower:
                return True
        
        return False
    
    def is_development_process(self, process_name: str, cmdline: str) -> bool:
        """Check if process is a development tool"""
        name_lower = process_name.lower()
        cmd_lower = cmdline.lower()
        
        # Check against development tool patterns
        for dev_pattern in self.development_processes:
            if dev_pattern in name_lower or dev_pattern in cmd_lower:
                return True
        
        return False
    
    def _get_memory_mb(self, memory_info) -> int:
        """Safely extract memory usage in MB"""
        if not memory_info:
            return 0
        
        # Handle both dict and pmem object
        if hasattr(memory_info, 'rss'):
            return memory_info.rss // 1024 // 1024
        elif isinstance(memory_info, dict) and 'rss' in memory_info:
            return memory_info['rss'] // 1024 // 1024
        else:
            return 0
    
    def analyze_process(self, proc: psutil.Process) -> Dict[str, Any]:
        """Analyze a single process safely"""
        try:
            info = proc.as_dict(attrs=[
                'pid', 'name', 'exe', 'cmdline', 'create_time',
                'cpu_percent', 'memory_percent', 'memory_info',
                'status', 'username', 'cwd'
            ])
            
            # Safe defaults for missing info
            name = info.get('name', 'unknown')
            cmdline = ' '.join(info.get('cmdline') or [])
            
            # Classify the process
            is_critical = self.is_critical_process(name, cmdline)
            is_ai = self.is_ai_server_process(name, cmdline)
            is_dev = self.is_development_process(name, cmdline)
            
            # Calculate resource usage
            cpu_percent = info.get('cpu_percent', 0) or 0
            mem_percent = info.get('memory_percent', 0) or 0
            
            # Determine if potentially idle
            is_idle = (
                cpu_percent < 0.1 and 
                mem_percent < 0.5 and 
                not is_critical and 
                not is_ai and 
                not is_dev
            )
            
            analysis = {
                "pid": info.get('pid'),
                "name": name,
                "exe": info.get('exe'),
                "cmdline": cmdline[:200],  # Truncate long command lines
                "create_time": info.get('create_time'),
                "cpu_percent": cpu_percent,
                "memory_percent": mem_percent,
                "memory_mb": self._get_memory_mb(info.get('memory_info')),
                "status": info.get('status'),
                "username": info.get('username'),
                "classification": {
                    "is_critical": is_critical,
                    "is_ai_server": is_ai,
                    "is_development": is_dev,
                    "is_potentially_idle": is_idle
                },
                "recommendation": self.get_process_recommendation(
                    is_critical, is_ai, is_dev, is_idle, cpu_percent, mem_percent
                )
            }
            
            return analysis
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def get_process_recommendation(self, is_critical: bool, is_ai: bool, 
                                 is_dev: bool, is_idle: bool, 
                                 cpu: float, mem: float) -> Dict[str, str]:
        """Get recommendation for process management"""
        if is_critical:
            return {
                "action": "keep",
                "reason": "Critical system process",
                "priority": "high"
            }
        elif is_ai:
            return {
                "action": "keep",
                "reason": "AI server infrastructure",
                "priority": "high"
            }
        elif is_dev:
            return {
                "action": "keep",
                "reason": "Development tool",
                "priority": "medium"
            }
        elif is_idle and cpu < 0.01 and mem < 0.1:
            return {
                "action": "investigate",
                "reason": "Very low resource usage - may be idle",
                "priority": "low"
            }
        elif is_idle:
            return {
                "action": "monitor",
                "reason": "Low resource usage - monitor for activity",
                "priority": "low"
            }
        else:
            return {
                "action": "keep",
                "reason": "Active process with normal resource usage",
                "priority": "medium"
            }
    
    def scan_all_processes(self) -> Dict[str, Any]:
        """Scan all running processes"""
        scan_start = time.time()
        processes = []
        
        print("🔍 Scanning running processes...")
        
        for proc in psutil.process_iter():
            analysis = self.analyze_process(proc)
            if analysis:
                processes.append(analysis)
        
        scan_duration = time.time() - scan_start
        
        # Categorize processes
        critical_processes = [p for p in processes if p['classification']['is_critical']]
        ai_processes = [p for p in processes if p['classification']['is_ai_server']]
        dev_processes = [p for p in processes if p['classification']['is_development']]
        idle_processes = [p for p in processes if p['classification']['is_potentially_idle']]
        
        # Calculate statistics
        total_cpu = sum(p['cpu_percent'] for p in processes)
        total_memory = sum(p['memory_mb'] for p in processes)
        
        results = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": scan_duration,
                "total_processes": len(processes)
            },
            "statistics": {
                "critical_count": len(critical_processes),
                "ai_server_count": len(ai_processes),
                "development_count": len(dev_processes),
                "potentially_idle_count": len(idle_processes),
                "total_cpu_percent": total_cpu,
                "total_memory_mb": total_memory
            },
            "process_categories": {
                "critical_processes": critical_processes,
                "ai_server_processes": ai_processes,
                "development_processes": dev_processes,
                "potentially_idle_processes": idle_processes
            },
            "all_processes": processes
        }
        
        return results
    
    def generate_report(self, scan_results: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        stats = scan_results['statistics']
        
        report = []
        report.append("📊 SAFE SERVICES SCAN REPORT")
        report.append("=" * 50)
        report.append(f"Scan Time: {scan_results['scan_info']['timestamp']}")
        report.append(f"Duration: {scan_results['scan_info']['duration_seconds']:.2f} seconds")
        report.append(f"Total Processes: {scan_results['scan_info']['total_processes']}")
        report.append("")
        
        # Statistics
        report.append("📈 Process Categories:")
        report.append(f"  🔒 Critical System: {stats['critical_count']}")
        report.append(f"  🤖 AI Servers: {stats['ai_server_count']}")
        report.append(f"  💻 Development: {stats['development_count']}")
        report.append(f"  😴 Potentially Idle: {stats['potentially_idle_count']}")
        report.append("")
        
        # Resource usage
        report.append(f"🔥 Total CPU Usage: {stats['total_cpu_percent']:.1f}%")
        report.append(f"🧠 Total Memory Usage: {stats['total_memory_mb']:,} MB")
        report.append("")
        
        # Potentially idle processes
        if scan_results['process_categories']['potentially_idle_processes']:
            report.append("😴 Potentially Idle Processes (Investigation Candidates):")
            for proc in sorted(
                scan_results['process_categories']['potentially_idle_processes'],
                key=lambda x: x['memory_mb'], reverse=True
            )[:10]:  # Top 10 by memory
                report.append(f"  • {proc['name']} (PID: {proc['pid']}) - "
                            f"CPU: {proc['cpu_percent']:.1f}%, "
                            f"Memory: {proc['memory_mb']} MB")
                report.append(f"    Recommendation: {proc['recommendation']['action']} - "
                            f"{proc['recommendation']['reason']}")
        else:
            report.append("✅ No potentially idle processes detected")
        
        report.append("")
        report.append("⚠️  NOTE: This is a READ-ONLY scan. No processes were modified.")
        report.append("🔧 To take action on any process, manual user confirmation is required.")
        
        return "\n".join(report)
    
    def save_results(self, scan_results: Dict[str, Any]) -> None:
        """Save scan results to JSON file"""
        try:
            # Read existing data
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"scan_history": []}
            
            # Add new scan
            data["scan_history"].append(scan_results)
            
            # Keep only last 20 scans
            data["scan_history"] = data["scan_history"][-20:]
            data["last_scan"] = scan_results['scan_info']['timestamp']
            
            # Save to file
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"📄 Results saved to: {self.log_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save results: {e}")
    
    def user_confirm(self, message: str) -> bool:
        """User confirmation pattern for any actions"""
        response = input(f"❓ {message} (y/N): ").lower().strip()
        return response in ['y', 'yes']

def main():
    """Main scanning function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Safe Services Scanner")
    parser.add_argument('--format', choices=['json', 'report'], default='report',
                       help='Output format')
    parser.add_argument('--log-file', default='logs/services_scan.json',
                       help='Log file path')
    parser.add_argument('--save', action='store_true',
                       help='Save results to log file')
    
    args = parser.parse_args()
    
    scanner = SafeServicesScanner(log_file=args.log_file)
    
    # Perform scan
    scan_results = scanner.scan_all_processes()
    
    # Output results
    if args.format == 'json':
        print(json.dumps(scan_results, indent=2))
    else:
        report = scanner.generate_report(scan_results)
        print(report)
    
    # Save results if requested
    if args.save:
        scanner.save_results(scan_results)
    
    # Check for potentially problematic processes
    idle_count = scan_results['statistics']['potentially_idle_count']
    if idle_count > 0:
        print(f"\n⚠️  Found {idle_count} potentially idle processes.")
        print("💡 Run with --save to log results for further analysis.")
        
        if scanner.user_confirm("Would you like to see detailed recommendations?"):
            print("\n📋 Detailed Recommendations:")
            for proc in scan_results['process_categories']['potentially_idle_processes'][:5]:
                print(f"• {proc['name']}: {proc['recommendation']['action']} "
                      f"({proc['recommendation']['reason']})")

if __name__ == "__main__":
    main() 