#!/usr/bin/env python3
"""
Fusion System Status Dashboard
Real-time status monitoring and system overview
"""

import requests
import json
import time
import os
from datetime import datetime
from system_monitor import SystemMonitor

class FusionStatusDashboard:
    """Comprehensive status dashboard for the fusion system"""
    
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url
        self.monitor = SystemMonitor()
    
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "fusion_system": self.get_fusion_status(),
            "system_resources": self.get_resource_status(),
            "services": self.get_services_status(),
            "health": self.get_health_status()
        }
        return status
    
    def get_fusion_status(self):
        """Get fusion system status"""
        try:
            r = requests.get(f"{self.base_url}/fusion/status", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    config = data['data']['configuration']
                    return {
                        "status": "online",
                        "total_models": data['data']['total_models'],
                        "fusion_strategy": data['data']['fusion_strategy'],
                        "last_updated": config.get('last_updated', 'Unknown'),
                        "models": [
                            {
                                "name": model['name'],
                                "weight": model['weight'],
                                "domain": model['domain'],
                                "normalized_weight": model['normalized_weight']
                            }
                            for model in config.get('ensemble_config', {}).get('models', [])
                        ]
                    }
            return {"status": "error", "message": "API error"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def get_resource_status(self):
        """Get system resource status"""
        try:
            stats = self.monitor.get_system_stats()
            return {
                "cpu_usage": stats["cpu_percent"],
                "memory_usage": stats["memory_percent"],
                "disk_usage": stats["disk_percent"],
                "status": "good" if stats["cpu_percent"] < 80 and stats["memory_usage"] < 90 else "warning"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_services_status(self):
        """Get service status"""
        services = {
            "fusion_ui": {"url": f"{self.base_url}/health", "name": "Fusion Control UI"},
            "fusion_api": {"url": f"{self.base_url}/fusion/status", "name": "Fusion API"},
        }
        
        status = {}
        for service_id, service_info in services.items():
            try:
                r = requests.get(service_info["url"], timeout=3)
                status[service_id] = {
                    "name": service_info["name"],
                    "status": "online" if r.status_code == 200 else "error",
                    "response_time": r.elapsed.total_seconds() if hasattr(r, 'elapsed') else 0
                }
            except Exception as e:
                status[service_id] = {
                    "name": service_info["name"],
                    "status": "offline",
                    "error": str(e)
                }
        
        return status
    
    def get_health_status(self):
        """Get overall health status"""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                return r.json()
            return {"status": "error", "message": "Health check failed"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def print_status_dashboard(self):
        """Print a beautiful status dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        
        status = self.get_system_status()
        
        print("🌟 FUSION-HYBRID-V1 SYSTEM STATUS DASHBOARD")
        print("=" * 70)
        print(f"🕒 Last Update: {status['timestamp']}")
        print()
        
        # Fusion System Status
        fusion = status['fusion_system']
        if fusion['status'] == 'online':
            print(f"🧬 FUSION SYSTEM: ✅ ONLINE")
            print(f"   📊 Total Models: {fusion['total_models']}")
            print(f"   🔄 Strategy: {fusion['fusion_strategy']}")
            print(f"   📝 Last Updated: {fusion['last_updated']}")
            print(f"   🤖 Active Models:")
            for model in fusion['models']:
                print(f"      • {model['name']} ({model['domain']}) - Weight: {model['weight']}")
        else:
            print(f"🧬 FUSION SYSTEM: ❌ {fusion['status'].upper()}")
            if 'error' in fusion:
                print(f"   ⚠️ Error: {fusion['error']}")
        
        print()
        
        # System Resources
        resources = status['system_resources']
        if resources['status'] == 'good':
            status_icon = "✅"
        elif resources['status'] == 'warning':
            status_icon = "⚠️"
        else:
            status_icon = "❌"
        
        print(f"💻 SYSTEM RESOURCES: {status_icon}")
        print(f"   🔥 CPU Usage: {resources.get('cpu_usage', 'N/A')}%")
        print(f"   🧠 Memory Usage: {resources.get('memory_usage', 'N/A')}%")
        print(f"   💾 Disk Usage: {resources.get('disk_usage', 'N/A')}%")
        print()
        
        # Services Status
        print("🔧 SERVICES STATUS:")
        services = status['services']
        for service_id, service_info in services.items():
            if service_info['status'] == 'online':
                icon = "✅"
                details = f"({service_info.get('response_time', 0):.3f}s)"
            elif service_info['status'] == 'error':
                icon = "⚠️"
                details = "(errors)"
            else:
                icon = "❌"
                details = "(offline)"
            
            print(f"   {icon} {service_info['name']}: {service_info['status'].upper()} {details}")
        
        print()
        
        # Overall Health
        health = status['health']
        if health.get('status') == 'healthy':
            print("❤️ OVERALL HEALTH: ✅ HEALTHY")
        else:
            print("❤️ OVERALL HEALTH: ❌ ISSUES DETECTED")
        
        print("\n" + "=" * 70)
        print("🌐 Web Interface: http://localhost:9000")
        print("📊 API Status: http://localhost:9000/fusion/status")
        print("❤️ Health Check: http://localhost:9000/health")
        print("=" * 70)
    
    def run_continuous_dashboard(self, refresh_interval=5):
        """Run continuous dashboard updates"""
        print("🚀 Starting Fusion System Status Dashboard...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.print_status_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fusion System Status Dashboard")
    parser.add_argument('--url', default='http://localhost:9000', help='Base URL for the fusion system')
    parser.add_argument('--refresh', type=int, default=5, help='Refresh interval in seconds')
    parser.add_argument('--once', action='store_true', help='Show status once and exit')
    
    args = parser.parse_args()
    
    dashboard = FusionStatusDashboard(args.url)
    
    if args.once:
        dashboard.print_status_dashboard()
    else:
        dashboard.run_continuous_dashboard(args.refresh)

if __name__ == "__main__":
    main()
