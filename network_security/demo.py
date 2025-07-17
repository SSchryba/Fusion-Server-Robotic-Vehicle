"""
Network Security System Demo

Comprehensive demonstration of the network security monitoring and response system,
including traffic capture, anomaly detection, and automated incident response.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from network_security.security_orchestrator import SecurityOrchestrator
from network_security.netsniffer import NetSniffer, AttackType, TrafficType
from network_security.anomaly_detector import NetworkAnomalyDetector
from network_security.network_actions import NetworkActionEngine, ActionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NetworkSecurityDemo:
    """Comprehensive demonstration of network security system capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        # Configuration for demo
        self.config = {
            'sniffer': {
                'interface': 'any',
                'capture_duration': 30,  # Short duration for demo
                'packet_count_limit': 1000,
                'capture_file_rotation': False
            },
            'detector': {
                'anomaly_threshold': 0.6,  # Lower threshold for demo
                'detection_methods': ['statistical', 'behavioral'],
                'model_update_interval': 300
            },
            'response': {
                'auto_response_enabled': True,
                'response_threshold': 0.7,
                'dry_run': True  # Safe mode for demo
            }
        }
        
        # Initialize orchestrator
        self.orchestrator = SecurityOrchestrator(self.config)
        
        # Demo state
        self.demo_incidents = []
        self.demo_responses = []
        
    async def run_full_demo(self):
        """Run comprehensive network security demo."""
        print("🛡️  Network Security Monitoring System Demo")
        print("=" * 60)
        
        try:
            # Check prerequisites
            print("\n1. 🔍 Checking Prerequisites...")
            await self.check_prerequisites()
            
            # Start security orchestrator
            print("\n2. 🚀 Starting Security Orchestrator...")
            await self.orchestrator.start()
            print("✅ Security orchestrator started successfully")
            
            # Demo traffic monitoring
            print("\n3. 📡 Traffic Monitoring Demonstration")
            await self.demo_traffic_monitoring()
            
            # Demo anomaly detection
            print("\n4. 🔍 Anomaly Detection Demonstration")
            await self.demo_anomaly_detection()
            
            # Demo incident response
            print("\n5. 🚨 Incident Response Demonstration")
            await self.demo_incident_response()
            
            # Demo network actions
            print("\n6. ⚡ Network Actions Demonstration")
            await self.demo_network_actions()
            
            # Show system status
            print("\n7. 📊 System Status and Metrics")
            await self.show_system_status()
            
            # Generate reports
            print("\n8. 📋 Report Generation")
            await self.generate_reports()
            
            print("\n✅ Demo completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.error(f"Demo error: {e}")
            
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            await self.orchestrator.stop()
            print("✅ Cleanup completed")
            
    async def check_prerequisites(self):
        """Check system prerequisites."""
        print("   🔧 Checking system capabilities...")
        
        # Check if running as root/admin (required for packet capture)
        if os.geteuid() != 0:
            print("   ⚠️  Warning: Not running as root - packet capture may be limited")
        else:
            print("   ✅ Running with appropriate privileges")
            
        # Check for required tools
        tools_to_check = ['tcpdump', 'iptables', 'ss']
        
        for tool in tools_to_check:
            try:
                process = await asyncio.create_subprocess_exec(
                    'which', tool,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    print(f"   ✅ {tool} available")
                else:
                    print(f"   ⚠️  {tool} not found - some features may be limited")
                    
            except Exception as e:
                print(f"   ⚠️  Could not check {tool}: {e}")
                
        # Check Python libraries
        required_libs = ['scapy', 'sklearn', 'pandas', 'numpy']
        
        for lib in required_libs:
            try:
                __import__(lib)
                print(f"   ✅ {lib} available")
            except ImportError:
                print(f"   ⚠️  {lib} not available - some features may be limited")
                
    async def demo_traffic_monitoring(self):
        """Demonstrate traffic monitoring capabilities."""
        print("\n   📡 Network Traffic Monitoring")
        
        # Get sniffer status
        sniffer_status = self.orchestrator.sniffer.get_status()
        print(f"   📊 Interface: {sniffer_status.get('interface', 'unknown')}")
        print(f"   📊 Capture running: {sniffer_status.get('capture_process_running', False)}")
        print(f"   📊 Packet buffer size: {sniffer_status.get('packet_buffer_size', 0)}")
        
        # Show recent packet analysis
        print("\n   🔸 Recent Packet Analysis")
        
        # Wait for some packets to be captured
        await asyncio.sleep(5)
        
        # Show packet statistics
        packet_buffer = self.orchestrator.sniffer.packet_buffer
        if packet_buffer:
            print(f"   📈 Packets captured: {len(packet_buffer)}")
            
            # Analyze protocols
            protocols = {}
            for packet in packet_buffer[-50:]:  # Last 50 packets
                protocol = packet.protocol
                protocols[protocol] = protocols.get(protocol, 0) + 1
                
            print("   📊 Protocol distribution:")
            for protocol, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True):
                print(f"      {protocol}: {count}")
                
            # Show source IP distribution
            src_ips = {}
            for packet in packet_buffer[-50:]:
                src_ip = packet.src_ip
                src_ips[src_ip] = src_ips.get(src_ip, 0) + 1
                
            print("   📊 Top source IPs:")
            for src_ip, count in sorted(src_ips.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {src_ip}: {count}")
                
        else:
            print("   ℹ️  No packets captured yet")
            
    async def demo_anomaly_detection(self):
        """Demonstrate anomaly detection capabilities."""
        print("\n   🔍 Anomaly Detection Engine")
        
        # Get detector status
        detector_status = self.orchestrator.anomaly_detector.get_detection_stats()
        print(f"   📊 Packets analyzed: {detector_status.get('total_packets_analyzed', 0)}")
        print(f"   📊 Anomalies detected: {detector_status.get('anomalies_detected', 0)}")
        print(f"   📊 Active profiles: {detector_status.get('active_profiles', 0)}")
        
        # Show recent anomalies
        print("\n   🔸 Recent Anomalies")
        
        recent_anomalies = self.orchestrator.sniffer.get_recent_anomalies(5)
        if recent_anomalies:
            for i, anomaly in enumerate(recent_anomalies, 1):
                print(f"   {i}. {anomaly['attack_type']}: {anomaly['description']}")
                print(f"      Severity: {anomaly['severity']:.2f} | Source: {anomaly['src_ip']}")
                
        else:
            print("   ℹ️  No anomalies detected yet")
            
        # Show network profiles
        print("\n   🔸 Network Behavior Profiles")
        
        profiles = self.orchestrator.anomaly_detector.get_network_profiles()
        if profiles:
            print(f"   📊 Active profiles: {len(profiles)}")
            
            for profile in profiles[:3]:  # Show first 3 profiles
                print(f"   Profile: {profile['src_ip']} -> {profile['dst_ip']}")
                print(f"      Avg packet size: {profile['avg_packet_size']:.1f} bytes")
                print(f"      Typical ports: {profile['typical_ports'][:5]}")
                
        else:
            print("   ℹ️  No network profiles created yet")
            
    async def demo_incident_response(self):
        """Demonstrate incident response capabilities."""
        print("\n   🚨 Security Incident Response")
        
        # Get orchestrator status
        status = self.orchestrator.get_status()
        print(f"   📊 Active incidents: {status.get('active_incidents', 0)}")
        print(f"   📊 Total incidents: {status.get('total_incidents', 0)}")
        print(f"   📊 Blocked IPs: {status.get('blocked_ips', 0)}")
        
        # Show recent incidents
        print("\n   🔸 Recent Security Incidents")
        
        recent_incidents = self.orchestrator.get_recent_incidents(5)
        if recent_incidents:
            for i, incident in enumerate(recent_incidents, 1):
                print(f"   {i}. {incident['title']}")
                print(f"      Severity: {incident['severity']} | Type: {incident['attack_type']}")
                print(f"      Source: {incident['source_ip']} -> Target: {incident['target_ip']}")
                print(f"      Actions: {len(incident['response_actions'])}")
                
        else:
            print("   ℹ️  No security incidents recorded yet")
            
        # Show incident summary
        print("\n   🔸 Incident Summary (Last 24 Hours)")
        
        summary = self.orchestrator.get_incident_summary(24)
        print(f"   📈 Total incidents: {summary['total_incidents']}")
        print(f"   📈 By severity: {summary['incidents_by_severity']}")
        print(f"   📈 By attack type: {summary['incidents_by_attack_type']}")
        
        # Simulate creating a test incident
        print("\n   🔸 Simulating Security Incident")
        
        try:
            # Create a mock traffic anomaly
            from network_security.netsniffer import TrafficAnomaly
            import uuid
            
            mock_anomaly = TrafficAnomaly(
                anomaly_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                src_ip="192.168.1.100",
                dst_ip="192.168.1.10",
                attack_type=AttackType.PORT_SCAN,
                traffic_type=TrafficType.SUSPICIOUS,
                frequency=50,
                severity=0.8,
                description="Simulated port scan attack for demo"
            )
            
            # Process the anomaly
            await self.orchestrator._handle_traffic_anomaly(mock_anomaly)
            print("   ✅ Simulated incident created and processed")
            
        except Exception as e:
            print(f"   ⚠️  Error simulating incident: {e}")
            
    async def demo_network_actions(self):
        """Demonstrate network action capabilities."""
        print("\n   ⚡ Automated Network Actions")
        
        # Create action engine for demo
        action_config = {
            'dry_run': True,  # Safe mode
            'max_concurrent_actions': 5,
            'firewall_type': 'iptables'
        }
        
        action_engine = NetworkActionEngine(action_config)
        await action_engine.start()
        
        try:
            # Show action engine status
            action_status = action_engine.get_status()
            print(f"   📊 Action engine running: {action_status['running']}")
            print(f"   📊 Dry run mode: {action_status['dry_run']}")
            print(f"   📊 Active actions: {action_status['active_actions']}")
            
            # Demonstrate different action types
            print("\n   🔸 Queuing Network Actions")
            
            # Queue firewall block action
            action_id1 = await action_engine.queue_action(
                ActionType.FIREWALL_BLOCK,
                "192.168.1.100",
                target_port=22,
                duration_seconds=300
            )
            print(f"   ✅ Queued firewall block action: {action_id1}")
            
            # Queue traffic shaping action
            action_id2 = await action_engine.queue_action(
                ActionType.TRAFFIC_SHAPING,
                "192.168.1.101",
                parameters={'bandwidth_limit': '100kbit', 'interface': 'eth0'}
            )
            print(f"   ✅ Queued traffic shaping action: {action_id2}")
            
            # Queue quarantine action
            action_id3 = await action_engine.queue_action(
                ActionType.QUARANTINE_VLAN,
                "192.168.1.102",
                duration_seconds=600
            )
            print(f"   ✅ Queued quarantine action: {action_id3}")
            
            # Wait for actions to process
            await asyncio.sleep(2)
            
            # Show action results
            print("\n   🔸 Action Results")
            
            recent_actions = action_engine.get_recent_actions(5)
            for action in recent_actions:
                print(f"   {action['action_type']}: {action['target_ip']}")
                print(f"      Status: {action['status']} | Success: {action['success']}")
                
            # Show action statistics
            stats = action_engine.get_action_stats()
            print(f"\n   📊 Action Statistics:")
            print(f"   📈 Total queued: {stats['total_actions_queued']}")
            print(f"   📈 Total executed: {stats['total_actions_executed']}")
            print(f"   📈 Success rate: {stats['success_rate']:.2%}")
            
        finally:
            await action_engine.stop()
            
    async def show_system_status(self):
        """Show comprehensive system status."""
        print("\n   📊 System Status and Metrics")
        
        # Get overall status
        status = self.orchestrator.get_status()
        
        print(f"   🟢 System running: {status['running']}")
        print(f"   ⏱️  Uptime: {status['uptime_seconds']:.0f} seconds")
        
        # Show component status
        print("\n   🔸 Component Status")
        
        sniffer_status = status.get('sniffer_status', {})
        print(f"   📡 NetSniffer: {'Running' if sniffer_status.get('running') else 'Stopped'}")
        print(f"      Packets buffered: {sniffer_status.get('packet_buffer_size', 0)}")
        print(f"      Anomalies detected: {sniffer_status.get('anomaly_buffer_size', 0)}")
        
        detector_status = status.get('detector_status', {})
        print(f"   🔍 Anomaly Detector: {'Running' if detector_status.get('running') else 'Stopped'}")
        print(f"      Packets analyzed: {detector_status.get('total_packets_analyzed', 0)}")
        print(f"      Anomalies found: {detector_status.get('anomalies_detected', 0)}")
        
        # Show security metrics
        print("\n   🔸 Security Metrics")
        
        metrics = status.get('metrics', {})
        print(f"   📈 Total incidents: {metrics.get('total_incidents_created', 0)}")
        print(f"   📈 False positive rate: {metrics.get('false_positive_rate', 0.0):.2%}")
        print(f"   📈 Detection accuracy: {metrics.get('detection_accuracy', 0.0):.2%}")
        print(f"   📈 Avg response time: {metrics.get('average_response_time', 0.0):.2f}s")
        
        # Show blocked IPs
        print(f"\n   🚫 Blocked IPs: {status.get('blocked_ips', 0)}")
        print(f"   🚦 Rate limited IPs: {status.get('rate_limited_ips', 0)}")
        
    async def generate_reports(self):
        """Generate demo reports."""
        print("\n   📋 Generating Reports")
        
        try:
            # Export security data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate security report
            security_report_file = f"network_security/reports/demo_security_report_{timestamp}.json"
            security_export = self.orchestrator.export_security_data(security_report_file)
            
            if security_export['success']:
                print(f"   ✅ Security report: {security_export['output_file']}")
                print(f"      Incidents: {security_export['incidents_exported']}")
                print(f"      Blocked IPs: {security_export['blocked_ips_exported']}")
            else:
                print(f"   ❌ Security report failed: {security_export['error']}")
                
            # Generate anomaly detection report
            detection_report_file = f"network_security/reports/demo_detection_report_{timestamp}.json"
            detection_export = self.orchestrator.anomaly_detector.export_detection_data(detection_report_file)
            
            if detection_export['success']:
                print(f"   ✅ Detection report: {detection_export['output_file']}")
                print(f"      Profiles: {detection_export['profiles_exported']}")
                print(f"      Packets: {detection_export['packets_exported']}")
            else:
                print(f"   ❌ Detection report failed: {detection_export['error']}")
                
            # Generate traffic analysis report
            anomaly_report_file = f"network_security/reports/demo_anomaly_report_{timestamp}.json"
            anomaly_export = self.orchestrator.sniffer.export_anomalies(anomaly_report_file)
            
            if anomaly_export['success']:
                print(f"   ✅ Anomaly report: {anomaly_export['output_file']}")
                print(f"      Anomalies: {anomaly_export['exported_count']}")
            else:
                print(f"   ❌ Anomaly report failed: {anomaly_export['error']}")
                
        except Exception as e:
            print(f"   ❌ Report generation failed: {e}")
            
    def add_demo_callbacks(self):
        """Add demo-specific callbacks."""
        async def demo_incident_callback(incident):
            """Handle demo incidents."""
            self.demo_incidents.append(incident)
            print(f"   🚨 Demo incident: {incident.title}")
            
        async def demo_response_callback(incident, action):
            """Handle demo responses."""
            self.demo_responses.append((incident, action))
            print(f"   ⚡ Demo response: {action.value} for {incident.source_ip}")
            
        self.orchestrator.add_incident_callback(demo_incident_callback)
        self.orchestrator.add_response_callback(demo_response_callback)


async def main():
    """Main demo function."""
    print("🌟 Starting Network Security System Demo...")
    print("This demonstrates comprehensive network security monitoring and response.")
    print("Note: Some features may require root privileges or specific network tools.\n")
    
    # Create and run demo
    demo = NetworkSecurityDemo()
    demo.add_demo_callbacks()
    await demo.run_full_demo()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 