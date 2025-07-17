"""
NetSniffer - Network Traffic Monitoring and Analysis Module

Captures network traffic using tcpdump and analyzes packets with scapy/pyshark
to detect anomalies, extract metadata, and generate security intelligence.
"""

import asyncio
import logging
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import re
import hashlib
from pathlib import Path

# Packet analysis imports
try:
    import scapy.all as scapy
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.layers.dns import DNS, DNSQR, DNSRR
    from scapy.layers.l2 import Ether, ARP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    PYSHARK_AVAILABLE = False

# System monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Network utilities
try:
    import netaddr
    NETADDR_AVAILABLE = True
except ImportError:
    NETADDR_AVAILABLE = False

logger = logging.getLogger(__name__)


class TrafficType(Enum):
    """Types of network traffic patterns"""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    UNKNOWN = "unknown"


class AttackType(Enum):
    """Types of network attacks"""
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    DNS_TUNNELING = "dns_tunneling"
    EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    MALWARE_C2 = "malware_c2"
    UNKNOWN_ATTACK = "unknown_attack"


@dataclass
class PacketMetadata:
    """Metadata extracted from network packets"""
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: str = "unknown"
    packet_size: int = 0
    tcp_flags: Optional[List[str]] = None
    dns_query: Optional[str] = None
    dns_response: Optional[str] = None
    payload_hash: Optional[str] = None
    
    def __post_init__(self):
        if self.tcp_flags is None:
            self.tcp_flags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'tcp_flags': self.tcp_flags
        }


@dataclass
class TrafficAnomaly:
    """Detected network traffic anomaly"""
    anomaly_id: str
    timestamp: datetime
    src_ip: str
    dst_ip: str
    attack_type: AttackType
    traffic_type: TrafficType
    frequency: int
    severity: float  # 0.0 to 1.0
    description: str
    evidence: List[PacketMetadata] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'anomaly_id': self.anomaly_id,
            'timestamp': self.timestamp.isoformat(),
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'attack_type': self.attack_type.value,
            'traffic_type': self.traffic_type.value,
            'frequency': self.frequency,
            'severity': self.severity,
            'description': self.description,
            'evidence_count': len(self.evidence),
            'metadata': self.metadata
        }


class NetSniffer:
    """
    Network traffic sniffer and analyzer using tcpdump, scapy, and pyshark.
    Captures packets, extracts metadata, and detects anomalies in real-time.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NetSniffer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Capture configuration
        self.interface = self.config.get('interface', 'any')
        self.capture_filter = self.config.get('capture_filter', '')
        self.capture_duration = self.config.get('capture_duration', 60)  # seconds
        self.packet_count_limit = self.config.get('packet_count_limit', 10000)
        self.capture_file_rotation = self.config.get('capture_file_rotation', True)
        
        # Analysis configuration
        self.analysis_batch_size = self.config.get('analysis_batch_size', 1000)
        self.anomaly_threshold = self.config.get('anomaly_threshold', 0.7)
        self.max_packet_history = self.config.get('max_packet_history', 100000)
        
        # Storage paths
        self.capture_dir = Path(self.config.get('capture_dir', 'network_security/captures'))
        self.log_dir = Path(self.config.get('log_dir', 'network_security/logs'))
        self.report_dir = Path(self.config.get('report_dir', 'network_security/reports'))
        
        # Create directories
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.running = False
        self.capture_process = None
        self.packet_buffer: List[PacketMetadata] = []
        self.anomaly_buffer: List[TrafficAnomaly] = []
        
        # Traffic analysis patterns
        self.suspicious_ports = {22, 23, 3389, 445, 135, 139, 1433, 3306, 5432}
        self.common_ports = {80, 443, 53, 25, 110, 143, 993, 995}
        self.high_ports = set(range(1024, 65536))
        
        # Attack detection thresholds
        self.port_scan_threshold = self.config.get('port_scan_threshold', 20)
        self.brute_force_threshold = self.config.get('brute_force_threshold', 10)
        self.ddos_threshold = self.config.get('ddos_threshold', 100)
        self.dns_tunnel_threshold = self.config.get('dns_tunnel_threshold', 50)
        
        # Callback functions
        self.anomaly_callbacks: List[Callable] = []
        self.packet_callbacks: List[Callable] = []
        
        logger.info(f"NetSniffer initialized for interface: {self.interface}")
        
    def add_anomaly_callback(self, callback: Callable[[TrafficAnomaly], None]):
        """Add callback function for anomaly detection"""
        self.anomaly_callbacks.append(callback)
        
    def add_packet_callback(self, callback: Callable[[PacketMetadata], None]):
        """Add callback function for packet processing"""
        self.packet_callbacks.append(callback)
        
    async def start_capture(self):
        """Start network traffic capture"""
        if self.running:
            logger.warning("NetSniffer is already running")
            return
            
        if not SCAPY_AVAILABLE and not PYSHARK_AVAILABLE:
            raise ImportError("Neither scapy nor pyshark is available for packet analysis")
            
        logger.info("Starting network traffic capture...")
        
        try:
            self.running = True
            
            # Start tcpdump capture process
            await self._start_tcpdump_capture()
            
            # Start packet analysis loop
            asyncio.create_task(self._packet_analysis_loop())
            
            # Start anomaly detection loop
            asyncio.create_task(self._anomaly_detection_loop())
            
            logger.info("NetSniffer started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start NetSniffer: {e}")
            self.running = False
            raise
            
    async def stop_capture(self):
        """Stop network traffic capture"""
        if not self.running:
            logger.warning("NetSniffer is not running")
            return
            
        logger.info("Stopping network traffic capture...")
        
        try:
            self.running = False
            
            # Stop tcpdump process
            if self.capture_process:
                self.capture_process.terminate()
                await asyncio.sleep(1)
                if self.capture_process.poll() is None:
                    self.capture_process.kill()
                    
            # Process remaining packets
            await self._process_remaining_packets()
            
            # Generate final report
            await self._generate_capture_report()
            
            logger.info("NetSniffer stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping NetSniffer: {e}")
            
    async def _start_tcpdump_capture(self):
        """Start tcpdump capture process"""
        try:
            # Generate capture filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            capture_file = self.capture_dir / f"capture_{timestamp}.pcap"
            
            # Build tcpdump command
            cmd = [
                'tcpdump',
                '-i', self.interface,
                '-w', str(capture_file),
                '-s', '0',  # Capture full packets
                '-n',  # Don't resolve hostnames
                '-q',  # Quiet mode
            ]
            
            # Add capture filter if specified
            if self.capture_filter:
                cmd.append(self.capture_filter)
                
            # Add packet count limit
            if self.packet_count_limit:
                cmd.extend(['-c', str(self.packet_count_limit)])
                
            logger.info(f"Starting tcpdump: {' '.join(cmd)}")
            
            # Start tcpdump process
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor tcpdump process
            asyncio.create_task(self._monitor_tcpdump_process(capture_file))
            
        except Exception as e:
            logger.error(f"Failed to start tcpdump: {e}")
            raise
            
    async def _monitor_tcpdump_process(self, capture_file: Path):
        """Monitor tcpdump process and handle file rotation"""
        try:
            start_time = datetime.now()
            
            while self.running:
                # Check if tcpdump is still running
                if self.capture_process.poll() is not None:
                    # Process exited, read output
                    stdout, stderr = self.capture_process.communicate()
                    if stderr:
                        logger.warning(f"tcpdump stderr: {stderr}")
                        
                    # Process captured packets
                    if capture_file.exists():
                        await self._process_pcap_file(capture_file)
                        
                    # Start new capture if file rotation is enabled
                    if self.capture_file_rotation and self.running:
                        logger.info("Rotating capture file...")
                        await self._start_tcpdump_capture()
                        
                    break
                    
                # Check if capture duration exceeded
                if (datetime.now() - start_time).total_seconds() > self.capture_duration:
                    logger.info("Capture duration exceeded, rotating file...")
                    self.capture_process.terminate()
                    await asyncio.sleep(1)
                    
                    # Process current file
                    if capture_file.exists():
                        await self._process_pcap_file(capture_file)
                        
                    # Start new capture
                    if self.running:
                        await self._start_tcpdump_capture()
                        
                    break
                    
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error monitoring tcpdump process: {e}")
            
    async def _process_pcap_file(self, pcap_file: Path):
        """Process captured pcap file using scapy or pyshark"""
        try:
            logger.info(f"Processing pcap file: {pcap_file}")
            
            if SCAPY_AVAILABLE:
                await self._process_with_scapy(pcap_file)
            elif PYSHARK_AVAILABLE:
                await self._process_with_pyshark(pcap_file)
            else:
                logger.error("No packet analysis library available")
                
        except Exception as e:
            logger.error(f"Error processing pcap file: {e}")
            
    async def _process_with_scapy(self, pcap_file: Path):
        """Process pcap file using scapy"""
        try:
            # Read packets from file
            packets = scapy.rdpcap(str(pcap_file))
            
            logger.info(f"Processing {len(packets)} packets with scapy")
            
            # Process packets in batches
            for i in range(0, len(packets), self.analysis_batch_size):
                batch = packets[i:i + self.analysis_batch_size]
                
                for packet in batch:
                    metadata = self._extract_metadata_scapy(packet)
                    if metadata:
                        await self._process_packet_metadata(metadata)
                        
                # Allow other tasks to run
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Error processing with scapy: {e}")
            
    def _extract_metadata_scapy(self, packet) -> Optional[PacketMetadata]:
        """Extract metadata from scapy packet"""
        try:
            if not packet.haslayer(IP):
                return None
                
            ip_layer = packet[IP]
            timestamp = datetime.fromtimestamp(packet.time)
            
            metadata = PacketMetadata(
                timestamp=timestamp,
                src_ip=ip_layer.src,
                dst_ip=ip_layer.dst,
                protocol=ip_layer.proto,
                packet_size=len(packet)
            )
            
            # Extract TCP information
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                metadata.src_port = tcp_layer.sport
                metadata.dst_port = tcp_layer.dport
                metadata.protocol = "TCP"
                
                # Extract TCP flags
                flags = []
                if tcp_layer.flags.S:
                    flags.append("SYN")
                if tcp_layer.flags.A:
                    flags.append("ACK")
                if tcp_layer.flags.F:
                    flags.append("FIN")
                if tcp_layer.flags.R:
                    flags.append("RST")
                if tcp_layer.flags.P:
                    flags.append("PSH")
                if tcp_layer.flags.U:
                    flags.append("URG")
                    
                metadata.tcp_flags = flags
                
            # Extract UDP information
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                metadata.src_port = udp_layer.sport
                metadata.dst_port = udp_layer.dport
                metadata.protocol = "UDP"
                
            # Extract DNS information
            if packet.haslayer(DNS):
                dns_layer = packet[DNS]
                
                # DNS query
                if dns_layer.qr == 0 and dns_layer.qd:
                    metadata.dns_query = dns_layer.qd.qname.decode('utf-8', errors='ignore')
                    
                # DNS response
                elif dns_layer.qr == 1 and dns_layer.an:
                    metadata.dns_response = dns_layer.an.rdata
                    
            # Extract ICMP information
            elif packet.haslayer(ICMP):
                metadata.protocol = "ICMP"
                
            # Generate payload hash
            if packet.payload:
                payload_bytes = bytes(packet.payload)
                metadata.payload_hash = hashlib.md5(payload_bytes).hexdigest()
                
            return metadata
            
        except Exception as e:
            logger.debug(f"Error extracting metadata from packet: {e}")
            return None
            
    async def _process_with_pyshark(self, pcap_file: Path):
        """Process pcap file using pyshark"""
        try:
            # Open pcap file
            cap = pyshark.FileCapture(str(pcap_file))
            
            packet_count = 0
            batch = []
            
            for packet in cap:
                metadata = self._extract_metadata_pyshark(packet)
                if metadata:
                    batch.append(metadata)
                    
                packet_count += 1
                
                # Process batch
                if len(batch) >= self.analysis_batch_size:
                    for meta in batch:
                        await self._process_packet_metadata(meta)
                    batch = []
                    
                    # Allow other tasks to run
                    await asyncio.sleep(0.001)
                    
            # Process remaining packets
            for meta in batch:
                await self._process_packet_metadata(meta)
                
            cap.close()
            
            logger.info(f"Processed {packet_count} packets with pyshark")
            
        except Exception as e:
            logger.error(f"Error processing with pyshark: {e}")
            
    def _extract_metadata_pyshark(self, packet) -> Optional[PacketMetadata]:
        """Extract metadata from pyshark packet"""
        try:
            if not hasattr(packet, 'ip'):
                return None
                
            timestamp = datetime.fromtimestamp(float(packet.sniff_timestamp))
            
            metadata = PacketMetadata(
                timestamp=timestamp,
                src_ip=packet.ip.src,
                dst_ip=packet.ip.dst,
                protocol=packet.ip.proto,
                packet_size=int(packet.length)
            )
            
            # Extract TCP information
            if hasattr(packet, 'tcp'):
                metadata.src_port = int(packet.tcp.srcport)
                metadata.dst_port = int(packet.tcp.dstport)
                metadata.protocol = "TCP"
                
                # Extract TCP flags
                flags = []
                if hasattr(packet.tcp, 'flags_syn') and packet.tcp.flags_syn == '1':
                    flags.append("SYN")
                if hasattr(packet.tcp, 'flags_ack') and packet.tcp.flags_ack == '1':
                    flags.append("ACK")
                if hasattr(packet.tcp, 'flags_fin') and packet.tcp.flags_fin == '1':
                    flags.append("FIN")
                if hasattr(packet.tcp, 'flags_reset') and packet.tcp.flags_reset == '1':
                    flags.append("RST")
                if hasattr(packet.tcp, 'flags_push') and packet.tcp.flags_push == '1':
                    flags.append("PSH")
                if hasattr(packet.tcp, 'flags_urg') and packet.tcp.flags_urg == '1':
                    flags.append("URG")
                    
                metadata.tcp_flags = flags
                
            # Extract UDP information
            elif hasattr(packet, 'udp'):
                metadata.src_port = int(packet.udp.srcport)
                metadata.dst_port = int(packet.udp.dstport)
                metadata.protocol = "UDP"
                
            # Extract DNS information
            if hasattr(packet, 'dns'):
                if hasattr(packet.dns, 'qry_name'):
                    metadata.dns_query = packet.dns.qry_name
                if hasattr(packet.dns, 'a'):
                    metadata.dns_response = packet.dns.a
                    
            # Extract ICMP information
            elif hasattr(packet, 'icmp'):
                metadata.protocol = "ICMP"
                
            return metadata
            
        except Exception as e:
            logger.debug(f"Error extracting metadata from pyshark packet: {e}")
            return None
            
    async def _process_packet_metadata(self, metadata: PacketMetadata):
        """Process extracted packet metadata"""
        try:
            # Add to packet buffer
            self.packet_buffer.append(metadata)
            
            # Limit buffer size
            if len(self.packet_buffer) > self.max_packet_history:
                self.packet_buffer = self.packet_buffer[-self.max_packet_history:]
                
            # Call packet callbacks
            for callback in self.packet_callbacks:
                try:
                    await callback(metadata)
                except Exception as e:
                    logger.error(f"Error in packet callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing packet metadata: {e}")
            
    async def _packet_analysis_loop(self):
        """Main packet analysis loop"""
        try:
            while self.running:
                if self.packet_buffer:
                    # Analyze recent packets for patterns
                    recent_packets = self.packet_buffer[-self.analysis_batch_size:]
                    
                    # Detect anomalies
                    anomalies = self._detect_anomalies(recent_packets)
                    
                    # Process detected anomalies
                    for anomaly in anomalies:
                        await self._process_anomaly(anomaly)
                        
                await asyncio.sleep(5)  # Analysis interval
                
        except Exception as e:
            logger.error(f"Error in packet analysis loop: {e}")
            
    def _detect_anomalies(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect anomalies in packet metadata"""
        anomalies = []
        
        try:
            # Port scan detection
            port_scan_anomalies = self._detect_port_scans(packets)
            anomalies.extend(port_scan_anomalies)
            
            # Brute force detection
            brute_force_anomalies = self._detect_brute_force(packets)
            anomalies.extend(brute_force_anomalies)
            
            # DDoS detection
            ddos_anomalies = self._detect_ddos(packets)
            anomalies.extend(ddos_anomalies)
            
            # DNS tunneling detection
            dns_tunnel_anomalies = self._detect_dns_tunneling(packets)
            anomalies.extend(dns_tunnel_anomalies)
            
            # Suspicious protocol usage
            protocol_anomalies = self._detect_protocol_anomalies(packets)
            anomalies.extend(protocol_anomalies)
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            
        return anomalies
        
    def _detect_port_scans(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect port scanning activities"""
        anomalies = []
        
        try:
            # Group packets by source IP
            src_connections = {}
            
            for packet in packets:
                if packet.protocol == "TCP" and "SYN" in packet.tcp_flags:
                    src_ip = packet.src_ip
                    dst_ip = packet.dst_ip
                    dst_port = packet.dst_port
                    
                    if src_ip not in src_connections:
                        src_connections[src_ip] = {}
                    if dst_ip not in src_connections[src_ip]:
                        src_connections[src_ip][dst_ip] = set()
                        
                    src_connections[src_ip][dst_ip].add(dst_port)
                    
            # Check for port scan patterns
            for src_ip, targets in src_connections.items():
                for dst_ip, ports in targets.items():
                    if len(ports) > self.port_scan_threshold:
                        # Generate anomaly
                        anomaly = TrafficAnomaly(
                            anomaly_id=f"port_scan_{src_ip}_{dst_ip}_{datetime.now().timestamp()}",
                            timestamp=datetime.now(),
                            src_ip=src_ip,
                            dst_ip=dst_ip,
                            attack_type=AttackType.PORT_SCAN,
                            traffic_type=TrafficType.MALICIOUS,
                            frequency=len(ports),
                            severity=min(len(ports) / 100.0, 1.0),
                            description=f"Port scan detected: {len(ports)} ports scanned",
                            metadata={
                                'scanned_ports': list(ports),
                                'scan_duration': 'unknown'
                            }
                        )
                        
                        # Add evidence packets
                        evidence = [p for p in packets if p.src_ip == src_ip and p.dst_ip == dst_ip]
                        anomaly.evidence = evidence[:10]  # Limit evidence
                        
                        anomalies.append(anomaly)
                        
        except Exception as e:
            logger.error(f"Error detecting port scans: {e}")
            
        return anomalies
        
    def _detect_brute_force(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect brute force attacks"""
        anomalies = []
        
        try:
            # Group SSH, RDP, and other authentication attempts
            auth_attempts = {}
            
            for packet in packets:
                if packet.dst_port in self.suspicious_ports:
                    key = (packet.src_ip, packet.dst_ip, packet.dst_port)
                    if key not in auth_attempts:
                        auth_attempts[key] = []
                    auth_attempts[key].append(packet)
                    
            # Check for brute force patterns
            for (src_ip, dst_ip, dst_port), attempts in auth_attempts.items():
                if len(attempts) > self.brute_force_threshold:
                    # Determine attack type based on port
                    if dst_port == 22:
                        attack_description = "SSH brute force"
                    elif dst_port == 3389:
                        attack_description = "RDP brute force"
                    elif dst_port in {445, 139}:
                        attack_description = "SMB brute force"
                    else:
                        attack_description = f"Brute force on port {dst_port}"
                        
                    anomaly = TrafficAnomaly(
                        anomaly_id=f"brute_force_{src_ip}_{dst_ip}_{dst_port}_{datetime.now().timestamp()}",
                        timestamp=datetime.now(),
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                        attack_type=AttackType.BRUTE_FORCE,
                        traffic_type=TrafficType.MALICIOUS,
                        frequency=len(attempts),
                        severity=min(len(attempts) / 50.0, 1.0),
                        description=attack_description,
                        metadata={
                            'target_port': dst_port,
                            'attempt_count': len(attempts),
                            'duration': 'unknown'
                        }
                    )
                    
                    anomaly.evidence = attempts[:10]
                    anomalies.append(anomaly)
                    
        except Exception as e:
            logger.error(f"Error detecting brute force: {e}")
            
        return anomalies
        
    def _detect_ddos(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect DDoS attacks"""
        anomalies = []
        
        try:
            # Group packets by destination IP
            dst_traffic = {}
            
            for packet in packets:
                dst_ip = packet.dst_ip
                if dst_ip not in dst_traffic:
                    dst_traffic[dst_ip] = []
                dst_traffic[dst_ip].append(packet)
                
            # Check for DDoS patterns
            for dst_ip, traffic in dst_traffic.items():
                if len(traffic) > self.ddos_threshold:
                    # Count unique source IPs
                    src_ips = set(p.src_ip for p in traffic)
                    
                    if len(src_ips) > 5:  # Multiple sources
                        anomaly = TrafficAnomaly(
                            anomaly_id=f"ddos_{dst_ip}_{datetime.now().timestamp()}",
                            timestamp=datetime.now(),
                            src_ip="multiple",
                            dst_ip=dst_ip,
                            attack_type=AttackType.DDoS,
                            traffic_type=TrafficType.MALICIOUS,
                            frequency=len(traffic),
                            severity=min(len(traffic) / 1000.0, 1.0),
                            description=f"DDoS attack detected: {len(traffic)} packets from {len(src_ips)} sources",
                            metadata={
                                'source_count': len(src_ips),
                                'packet_count': len(traffic),
                                'top_sources': list(src_ips)[:10]
                            }
                        )
                        
                        anomaly.evidence = traffic[:10]
                        anomalies.append(anomaly)
                        
        except Exception as e:
            logger.error(f"Error detecting DDoS: {e}")
            
        return anomalies
        
    def _detect_dns_tunneling(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect DNS tunneling activities"""
        anomalies = []
        
        try:
            # Group DNS queries by source IP
            dns_queries = {}
            
            for packet in packets:
                if packet.protocol == "UDP" and packet.dst_port == 53 and packet.dns_query:
                    src_ip = packet.src_ip
                    if src_ip not in dns_queries:
                        dns_queries[src_ip] = []
                    dns_queries[src_ip].append(packet)
                    
            # Check for DNS tunneling patterns
            for src_ip, queries in dns_queries.items():
                if len(queries) > self.dns_tunnel_threshold:
                    # Analyze query patterns
                    query_lengths = [len(q.dns_query) for q in queries if q.dns_query]
                    avg_length = sum(query_lengths) / len(query_lengths) if query_lengths else 0
                    
                    # Long or frequent queries might indicate tunneling
                    if avg_length > 50 or len(queries) > 100:
                        anomaly = TrafficAnomaly(
                            anomaly_id=f"dns_tunnel_{src_ip}_{datetime.now().timestamp()}",
                            timestamp=datetime.now(),
                            src_ip=src_ip,
                            dst_ip="dns_servers",
                            attack_type=AttackType.DNS_TUNNELING,
                            traffic_type=TrafficType.SUSPICIOUS,
                            frequency=len(queries),
                            severity=min((len(queries) + avg_length) / 200.0, 1.0),
                            description=f"Possible DNS tunneling: {len(queries)} queries, avg length {avg_length:.1f}",
                            metadata={
                                'query_count': len(queries),
                                'average_length': avg_length,
                                'max_length': max(query_lengths) if query_lengths else 0
                            }
                        )
                        
                        anomaly.evidence = queries[:10]
                        anomalies.append(anomaly)
                        
        except Exception as e:
            logger.error(f"Error detecting DNS tunneling: {e}")
            
        return anomalies
        
    def _detect_protocol_anomalies(self, packets: List[PacketMetadata]) -> List[TrafficAnomaly]:
        """Detect suspicious protocol usage"""
        anomalies = []
        
        try:
            # Group packets by protocol and port
            protocol_stats = {}
            
            for packet in packets:
                if packet.dst_port:
                    key = (packet.protocol, packet.dst_port)
                    if key not in protocol_stats:
                        protocol_stats[key] = []
                    protocol_stats[key].append(packet)
                    
            # Check for suspicious patterns
            for (protocol, port), traffic in protocol_stats.items():
                # High traffic on unusual ports
                if port not in self.common_ports and len(traffic) > 50:
                    src_ips = set(p.src_ip for p in traffic)
                    
                    if len(src_ips) == 1:  # Single source
                        anomaly = TrafficAnomaly(
                            anomaly_id=f"protocol_anomaly_{protocol}_{port}_{datetime.now().timestamp()}",
                            timestamp=datetime.now(),
                            src_ip=list(src_ips)[0],
                            dst_ip="multiple",
                            attack_type=AttackType.UNKNOWN_ATTACK,
                            traffic_type=TrafficType.SUSPICIOUS,
                            frequency=len(traffic),
                            severity=min(len(traffic) / 100.0, 1.0),
                            description=f"Unusual {protocol} traffic on port {port}",
                            metadata={
                                'protocol': protocol,
                                'port': port,
                                'packet_count': len(traffic)
                            }
                        )
                        
                        anomaly.evidence = traffic[:10]
                        anomalies.append(anomaly)
                        
        except Exception as e:
            logger.error(f"Error detecting protocol anomalies: {e}")
            
        return anomalies
        
    async def _process_anomaly(self, anomaly: TrafficAnomaly):
        """Process detected anomaly"""
        try:
            # Add to anomaly buffer
            self.anomaly_buffer.append(anomaly)
            
            # Log anomaly
            logger.warning(f"Anomaly detected: {anomaly.description} "
                         f"(severity: {anomaly.severity:.2f})")
            
            # Call anomaly callbacks
            for callback in self.anomaly_callbacks:
                try:
                    await callback(anomaly)
                except Exception as e:
                    logger.error(f"Error in anomaly callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing anomaly: {e}")
            
    async def _anomaly_detection_loop(self):
        """Main anomaly detection loop"""
        try:
            while self.running:
                # Generate summary report
                if self.anomaly_buffer:
                    await self._generate_anomaly_summary()
                    
                await asyncio.sleep(30)  # Summary interval
                
        except Exception as e:
            logger.error(f"Error in anomaly detection loop: {e}")
            
    async def _generate_anomaly_summary(self):
        """Generate anomaly summary report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_file = self.report_dir / f"anomaly_summary_{timestamp}.json"
            
            # Create summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_anomalies': len(self.anomaly_buffer),
                'anomalies_by_type': {},
                'anomalies_by_severity': {'low': 0, 'medium': 0, 'high': 0},
                'top_sources': {},
                'top_targets': {},
                'recent_anomalies': []
            }
            
            # Analyze anomalies
            for anomaly in self.anomaly_buffer:
                # Count by type
                attack_type = anomaly.attack_type.value
                if attack_type not in summary['anomalies_by_type']:
                    summary['anomalies_by_type'][attack_type] = 0
                summary['anomalies_by_type'][attack_type] += 1
                
                # Count by severity
                if anomaly.severity < 0.3:
                    summary['anomalies_by_severity']['low'] += 1
                elif anomaly.severity < 0.7:
                    summary['anomalies_by_severity']['medium'] += 1
                else:
                    summary['anomalies_by_severity']['high'] += 1
                    
                # Track top sources and targets
                if anomaly.src_ip not in summary['top_sources']:
                    summary['top_sources'][anomaly.src_ip] = 0
                summary['top_sources'][anomaly.src_ip] += 1
                
                if anomaly.dst_ip not in summary['top_targets']:
                    summary['top_targets'][anomaly.dst_ip] = 0
                summary['top_targets'][anomaly.dst_ip] += 1
                
            # Add recent anomalies
            recent_anomalies = sorted(self.anomaly_buffer, key=lambda x: x.timestamp, reverse=True)[:10]
            summary['recent_anomalies'] = [anomaly.to_dict() for anomaly in recent_anomalies]
            
            # Save summary
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Anomaly summary generated: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating anomaly summary: {e}")
            
    async def _process_remaining_packets(self):
        """Process any remaining packets before shutdown"""
        try:
            if self.packet_buffer:
                logger.info(f"Processing {len(self.packet_buffer)} remaining packets")
                
                # Final anomaly detection
                anomalies = self._detect_anomalies(self.packet_buffer)
                
                for anomaly in anomalies:
                    await self._process_anomaly(anomaly)
                    
        except Exception as e:
            logger.error(f"Error processing remaining packets: {e}")
            
    async def _generate_capture_report(self):
        """Generate final capture report"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.report_dir / f"capture_report_{timestamp}.json"
            
            # Create report
            report = {
                'timestamp': datetime.now().isoformat(),
                'capture_duration': 'unknown',
                'total_packets': len(self.packet_buffer),
                'total_anomalies': len(self.anomaly_buffer),
                'packet_summary': self._generate_packet_summary(),
                'anomaly_summary': [anomaly.to_dict() for anomaly in self.anomaly_buffer],
                'statistics': self._generate_statistics()
            }
            
            # Save report
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Capture report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating capture report: {e}")
            
    def _generate_packet_summary(self) -> Dict[str, Any]:
        """Generate packet summary statistics"""
        try:
            if not self.packet_buffer:
                return {}
                
            # Protocol distribution
            protocols = {}
            for packet in self.packet_buffer:
                protocol = packet.protocol
                if protocol not in protocols:
                    protocols[protocol] = 0
                protocols[protocol] += 1
                
            # Port distribution
            ports = {}
            for packet in self.packet_buffer:
                if packet.dst_port:
                    port = packet.dst_port
                    if port not in ports:
                        ports[port] = 0
                    ports[port] += 1
                    
            # Source/destination IPs
            src_ips = set(p.src_ip for p in self.packet_buffer)
            dst_ips = set(p.dst_ip for p in self.packet_buffer)
            
            return {
                'protocol_distribution': protocols,
                'top_ports': dict(sorted(ports.items(), key=lambda x: x[1], reverse=True)[:10]),
                'unique_src_ips': len(src_ips),
                'unique_dst_ips': len(dst_ips),
                'total_packets': len(self.packet_buffer)
            }
            
        except Exception as e:
            logger.error(f"Error generating packet summary: {e}")
            return {}
            
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate capture statistics"""
        try:
            return {
                'capture_interface': self.interface,
                'capture_filter': self.capture_filter,
                'analysis_batch_size': self.analysis_batch_size,
                'anomaly_threshold': self.anomaly_threshold,
                'thresholds': {
                    'port_scan': self.port_scan_threshold,
                    'brute_force': self.brute_force_threshold,
                    'ddos': self.ddos_threshold,
                    'dns_tunnel': self.dns_tunnel_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            return {}
            
    def get_status(self) -> Dict[str, Any]:
        """Get current NetSniffer status"""
        return {
            'running': self.running,
            'interface': self.interface,
            'packet_buffer_size': len(self.packet_buffer),
            'anomaly_buffer_size': len(self.anomaly_buffer),
            'capture_process_running': self.capture_process is not None and self.capture_process.poll() is None,
            'callback_count': {
                'packet_callbacks': len(self.packet_callbacks),
                'anomaly_callbacks': len(self.anomaly_callbacks)
            }
        }
        
    def get_recent_anomalies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent anomalies"""
        recent = sorted(self.anomaly_buffer, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [anomaly.to_dict() for anomaly in recent]
        
    def export_anomalies(self, output_file: str) -> Dict[str, Any]:
        """Export anomalies to JSON file"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_anomalies': len(self.anomaly_buffer),
                'anomalies': [anomaly.to_dict() for anomaly in self.anomaly_buffer]
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_file': output_file,
                'exported_count': len(self.anomaly_buffer)
            }
            
        except Exception as e:
            logger.error(f"Error exporting anomalies: {e}")
            return {
                'success': False,
                'error': str(e)
            } 