"""
Security Orchestrator for Network Security Monitoring System

Main coordination system that integrates NetSniffer, anomaly detection,
automated response actions, and incident management for comprehensive
network security monitoring and response.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import uuid

from netsniffer import NetSniffer, PacketMetadata, TrafficAnomaly, AttackType, TrafficType
from anomaly_detector import NetworkAnomalyDetector, AnomalyScore, ThreatLevel

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResponseAction(Enum):
    """Automated response actions"""
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    ALERT_ADMIN = "alert_admin"
    LOG_INCIDENT = "log_incident"
    DEEP_INSPECT = "deep_inspect"
    NOTIFY_SIEM = "notify_siem"


@dataclass
class SecurityIncident:
    """Security incident record"""
    incident_id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    source_ip: str
    target_ip: str
    attack_type: AttackType
    traffic_type: TrafficType
    
    # Evidence
    anomaly_score: Optional[AnomalyScore] = None
    traffic_anomaly: Optional[TrafficAnomaly] = None
    raw_packets: List[PacketMetadata] = field(default_factory=list)
    
    # Response
    response_actions: List[ResponseAction] = field(default_factory=list)
    response_status: str = "pending"
    response_timestamp: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    analyst_notes: str = ""
    false_positive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'incident_id': self.incident_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'source_ip': self.source_ip,
            'target_ip': self.target_ip,
            'attack_type': self.attack_type.value,
            'traffic_type': self.traffic_type.value,
            'anomaly_score': self.anomaly_score.to_dict() if self.anomaly_score else None,
            'traffic_anomaly': self.traffic_anomaly.to_dict() if self.traffic_anomaly else None,
            'raw_packet_count': len(self.raw_packets),
            'response_actions': [action.value for action in self.response_actions],
            'response_status': self.response_status,
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None,
            'tags': self.tags,
            'analyst_notes': self.analyst_notes,
            'false_positive': self.false_positive
        }


@dataclass
class SecurityMetrics:
    """Security monitoring metrics"""
    total_packets_analyzed: int = 0
    total_anomalies_detected: int = 0
    total_incidents_created: int = 0
    incidents_by_severity: Dict[str, int] = field(default_factory=dict)
    response_actions_taken: Dict[str, int] = field(default_factory=dict)
    false_positive_rate: float = 0.0
    detection_accuracy: float = 0.0
    average_response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_packets_analyzed': self.total_packets_analyzed,
            'total_anomalies_detected': self.total_anomalies_detected,
            'total_incidents_created': self.total_incidents_created,
            'incidents_by_severity': self.incidents_by_severity,
            'response_actions_taken': self.response_actions_taken,
            'false_positive_rate': self.false_positive_rate,
            'detection_accuracy': self.detection_accuracy,
            'average_response_time': self.average_response_time
        }


class SecurityOrchestrator:
    """
    Main security orchestrator that coordinates all network security components
    including traffic monitoring, anomaly detection, and automated response.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the security orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Component configuration
        self.sniffer_config = self.config.get('sniffer', {})
        self.detector_config = self.config.get('detector', {})
        self.response_config = self.config.get('response', {})
        
        # Initialize components
        self.sniffer = NetSniffer(self.sniffer_config)
        self.anomaly_detector = NetworkAnomalyDetector(self.detector_config)
        
        # Response configuration
        self.auto_response_enabled = self.config.get('auto_response_enabled', True)
        self.response_threshold = self.config.get('response_threshold', 0.8)
        self.incident_retention_days = self.config.get('incident_retention_days', 30)
        
        # Storage paths
        self.incident_dir = Path(self.config.get('incident_dir', 'network_security/incidents'))
        self.report_dir = Path(self.config.get('report_dir', 'network_security/reports'))
        
        # Create directories
        self.incident_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.running = False
        self.start_time = None
        
        # Incident tracking
        self.active_incidents: Dict[str, SecurityIncident] = {}
        self.incident_history: List[SecurityIncident] = []
        self.blocked_ips: set = set()
        self.rate_limited_ips: Dict[str, datetime] = {}
        
        # Metrics
        self.metrics = SecurityMetrics()
        
        # Callback functions
        self.incident_callbacks: List[Callable] = []
        self.response_callbacks: List[Callable] = []
        
        # Response actions mapping
        self.response_handlers = {
            ResponseAction.BLOCK_IP: self._block_ip,
            ResponseAction.RATE_LIMIT: self._rate_limit_ip,
            ResponseAction.QUARANTINE: self._quarantine_host,
            ResponseAction.ALERT_ADMIN: self._alert_admin,
            ResponseAction.LOG_INCIDENT: self._log_incident,
            ResponseAction.DEEP_INSPECT: self._deep_inspect,
            ResponseAction.NOTIFY_SIEM: self._notify_siem
        }
        
        # Set up component callbacks
        self.sniffer.add_anomaly_callback(self._handle_traffic_anomaly)
        self.sniffer.add_packet_callback(self._handle_packet)
        
        logger.info("Security Orchestrator initialized")
        
    def add_incident_callback(self, callback: Callable[[SecurityIncident], None]):
        """Add callback for incident creation"""
        self.incident_callbacks.append(callback)
        
    def add_response_callback(self, callback: Callable[[SecurityIncident, ResponseAction], None]):
        """Add callback for response actions"""
        self.response_callbacks.append(callback)
        
    async def start(self):
        """Start the security orchestrator"""
        if self.running:
            logger.warning("Security orchestrator is already running")
            return
            
        logger.info("Starting security orchestrator...")
        
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # Start components
            await self.sniffer.start_capture()
            await self.anomaly_detector.start()
            
            # Start background tasks
            asyncio.create_task(self._incident_management_loop())
            asyncio.create_task(self._metrics_collection_loop())
            asyncio.create_task(self._cleanup_loop())
            
            logger.info("Security orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start security orchestrator: {e}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the security orchestrator"""
        if not self.running:
            logger.warning("Security orchestrator is not running")
            return
            
        logger.info("Stopping security orchestrator...")
        
        try:
            self.running = False
            
            # Stop components
            await self.sniffer.stop_capture()
            await self.anomaly_detector.stop()
            
            # Process remaining incidents
            await self._process_remaining_incidents()
            
            # Generate final reports
            await self._generate_final_reports()
            
            logger.info("Security orchestrator stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping security orchestrator: {e}")
            
    async def _handle_packet(self, packet: PacketMetadata):
        """Handle incoming packet for analysis"""
        try:
            self.metrics.total_packets_analyzed += 1
            
            # Analyze packet for anomalies
            anomaly_score = await self.anomaly_detector.analyze_packet(packet)
            
            if anomaly_score and anomaly_score.score >= self.response_threshold:
                # Create incident from anomaly
                incident = await self._create_incident_from_anomaly(packet, anomaly_score)
                
                if incident:
                    await self._process_incident(incident)
                    
        except Exception as e:
            logger.error(f"Error handling packet: {e}")
            
    async def _handle_traffic_anomaly(self, traffic_anomaly: TrafficAnomaly):
        """Handle traffic anomaly from NetSniffer"""
        try:
            self.metrics.total_anomalies_detected += 1
            
            # Create incident from traffic anomaly
            incident = await self._create_incident_from_traffic_anomaly(traffic_anomaly)
            
            if incident:
                await self._process_incident(incident)
                
        except Exception as e:
            logger.error(f"Error handling traffic anomaly: {e}")
            
    async def _create_incident_from_anomaly(self, packet: PacketMetadata, anomaly_score: AnomalyScore) -> Optional[SecurityIncident]:
        """Create security incident from packet anomaly"""
        try:
            # Determine severity based on anomaly score
            if anomaly_score.score >= 0.9:
                severity = AlertSeverity.CRITICAL
            elif anomaly_score.score >= 0.7:
                severity = AlertSeverity.ERROR
            elif anomaly_score.score >= 0.5:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
                
            # Determine attack type from anomaly
            attack_type = self._classify_attack_type(anomaly_score)
            
            # Create incident
            incident = SecurityIncident(
                incident_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                severity=severity,
                title=f"Network Anomaly Detected: {attack_type.value}",
                description=f"Anomaly detected with score {anomaly_score.score:.3f}: {anomaly_score.explanation}",
                source_ip=packet.src_ip,
                target_ip=packet.dst_ip,
                attack_type=attack_type,
                traffic_type=TrafficType.SUSPICIOUS,
                anomaly_score=anomaly_score,
                raw_packets=[packet]
            )
            
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident from anomaly: {e}")
            return None
            
    async def _create_incident_from_traffic_anomaly(self, traffic_anomaly: TrafficAnomaly) -> Optional[SecurityIncident]:
        """Create security incident from traffic anomaly"""
        try:
            # Map traffic anomaly severity to alert severity
            severity_mapping = {
                TrafficType.NORMAL: AlertSeverity.INFO,
                TrafficType.SUSPICIOUS: AlertSeverity.WARNING,
                TrafficType.MALICIOUS: AlertSeverity.ERROR
            }
            
            if traffic_anomaly.severity >= 0.9:
                severity = AlertSeverity.CRITICAL
            else:
                severity = severity_mapping.get(traffic_anomaly.traffic_type, AlertSeverity.WARNING)
                
            # Create incident
            incident = SecurityIncident(
                incident_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                severity=severity,
                title=f"Traffic Anomaly: {traffic_anomaly.attack_type.value}",
                description=traffic_anomaly.description,
                source_ip=traffic_anomaly.src_ip,
                target_ip=traffic_anomaly.dst_ip,
                attack_type=traffic_anomaly.attack_type,
                traffic_type=traffic_anomaly.traffic_type,
                traffic_anomaly=traffic_anomaly,
                raw_packets=traffic_anomaly.evidence
            )
            
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident from traffic anomaly: {e}")
            return None
            
    def _classify_attack_type(self, anomaly_score: AnomalyScore) -> AttackType:
        """Classify attack type from anomaly score"""
        try:
            # Analyze contributing factors to determine attack type
            factors = [factor.lower() for factor in anomaly_score.contributing_factors]
            
            if any('port' in factor and 'scan' in factor for factor in factors):
                return AttackType.PORT_SCAN
            elif any('brute' in factor for factor in factors):
                return AttackType.BRUTE_FORCE
            elif any('ddos' in factor for factor in factors):
                return AttackType.DDoS
            elif any('dns' in factor for factor in factors):
                return AttackType.DNS_TUNNELING
            elif any('lateral' in factor for factor in factors):
                return AttackType.LATERAL_MOVEMENT
            elif any('exfiltration' in factor for factor in factors):
                return AttackType.EXFILTRATION
            elif any('malware' in factor or 'c2' in factor for factor in factors):
                return AttackType.MALWARE_C2
            else:
                return AttackType.UNKNOWN_ATTACK
                
        except Exception as e:
            logger.error(f"Error classifying attack type: {e}")
            return AttackType.UNKNOWN_ATTACK
            
    async def _process_incident(self, incident: SecurityIncident):
        """Process a security incident"""
        try:
            # Add to active incidents
            self.active_incidents[incident.incident_id] = incident
            self.metrics.total_incidents_created += 1
            
            # Update severity metrics
            severity_key = incident.severity.value
            if severity_key not in self.metrics.incidents_by_severity:
                self.metrics.incidents_by_severity[severity_key] = 0
            self.metrics.incidents_by_severity[severity_key] += 1
            
            # Log incident
            logger.warning(f"Security incident created: {incident.title} "
                         f"(ID: {incident.incident_id}, Severity: {incident.severity.value})")
            
            # Call incident callbacks
            for callback in self.incident_callbacks:
                try:
                    await callback(incident)
                except Exception as e:
                    logger.error(f"Error in incident callback: {e}")
                    
            # Determine response actions
            response_actions = self._determine_response_actions(incident)
            
            # Execute response actions if auto-response is enabled
            if self.auto_response_enabled and response_actions:
                await self._execute_response_actions(incident, response_actions)
                
            # Save incident to file
            await self._save_incident(incident)
            
        except Exception as e:
            logger.error(f"Error processing incident: {e}")
            
    def _determine_response_actions(self, incident: SecurityIncident) -> List[ResponseAction]:
        """Determine appropriate response actions for incident"""
        try:
            actions = []
            
            # Always log incidents
            actions.append(ResponseAction.LOG_INCIDENT)
            
            # Response based on severity
            if incident.severity == AlertSeverity.CRITICAL:
                actions.extend([
                    ResponseAction.BLOCK_IP,
                    ResponseAction.ALERT_ADMIN,
                    ResponseAction.NOTIFY_SIEM,
                    ResponseAction.DEEP_INSPECT
                ])
            elif incident.severity == AlertSeverity.ERROR:
                actions.extend([
                    ResponseAction.RATE_LIMIT,
                    ResponseAction.ALERT_ADMIN,
                    ResponseAction.NOTIFY_SIEM
                ])
            elif incident.severity == AlertSeverity.WARNING:
                actions.extend([
                    ResponseAction.RATE_LIMIT,
                    ResponseAction.NOTIFY_SIEM
                ])
                
            # Response based on attack type
            if incident.attack_type == AttackType.PORT_SCAN:
                actions.append(ResponseAction.BLOCK_IP)
            elif incident.attack_type == AttackType.BRUTE_FORCE:
                actions.extend([ResponseAction.BLOCK_IP, ResponseAction.ALERT_ADMIN])
            elif incident.attack_type == AttackType.DDoS:
                actions.extend([ResponseAction.BLOCK_IP, ResponseAction.RATE_LIMIT])
            elif incident.attack_type == AttackType.DNS_TUNNELING:
                actions.extend([ResponseAction.DEEP_INSPECT, ResponseAction.QUARANTINE])
            elif incident.attack_type == AttackType.MALWARE_C2:
                actions.extend([ResponseAction.QUARANTINE, ResponseAction.ALERT_ADMIN])
                
            # Remove duplicates
            return list(set(actions))
            
        except Exception as e:
            logger.error(f"Error determining response actions: {e}")
            return [ResponseAction.LOG_INCIDENT]
            
    async def _execute_response_actions(self, incident: SecurityIncident, actions: List[ResponseAction]):
        """Execute response actions for incident"""
        try:
            executed_actions = []
            
            for action in actions:
                try:
                    if action in self.response_handlers:
                        success = await self.response_handlers[action](incident)
                        
                        if success:
                            executed_actions.append(action)
                            
                            # Update metrics
                            action_key = action.value
                            if action_key not in self.metrics.response_actions_taken:
                                self.metrics.response_actions_taken[action_key] = 0
                            self.metrics.response_actions_taken[action_key] += 1
                            
                            logger.info(f"Executed response action: {action.value} for incident {incident.incident_id}")
                            
                            # Call response callbacks
                            for callback in self.response_callbacks:
                                try:
                                    await callback(incident, action)
                                except Exception as e:
                                    logger.error(f"Error in response callback: {e}")
                                    
                except Exception as e:
                    logger.error(f"Error executing response action {action.value}: {e}")
                    
            # Update incident with executed actions
            incident.response_actions = executed_actions
            incident.response_status = "completed" if executed_actions else "failed"
            incident.response_timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"Error executing response actions: {e}")
            
    async def _block_ip(self, incident: SecurityIncident) -> bool:
        """Block source IP address"""
        try:
            source_ip = incident.source_ip
            
            # Add to blocked IPs
            self.blocked_ips.add(source_ip)
            
            logger.warning(f"Blocked IP address: {source_ip}")
            
            # In a real implementation, this would interact with firewall/router
            # For now, we just track blocked IPs
            
            return True
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
            return False
            
    async def _rate_limit_ip(self, incident: SecurityIncident) -> bool:
        """Rate limit source IP address"""
        try:
            source_ip = incident.source_ip
            
            # Add to rate limited IPs (expires after 1 hour)
            self.rate_limited_ips[source_ip] = datetime.now() + timedelta(hours=1)
            
            logger.warning(f"Rate limited IP address: {source_ip}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error rate limiting IP: {e}")
            return False
            
    async def _quarantine_host(self, incident: SecurityIncident) -> bool:
        """Quarantine host"""
        try:
            source_ip = incident.source_ip
            
            # Add to quarantined hosts
            # In a real implementation, this would move host to quarantine VLAN
            
            logger.warning(f"Quarantined host: {source_ip}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error quarantining host: {e}")
            return False
            
    async def _alert_admin(self, incident: SecurityIncident) -> bool:
        """Alert administrator"""
        try:
            # In a real implementation, this would send email/SMS/Slack notification
            logger.critical(f"ADMIN ALERT: {incident.title} - {incident.description}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error alerting admin: {e}")
            return False
            
    async def _log_incident(self, incident: SecurityIncident) -> bool:
        """Log incident to file"""
        try:
            # This is handled by _save_incident
            return True
            
        except Exception as e:
            logger.error(f"Error logging incident: {e}")
            return False
            
    async def _deep_inspect(self, incident: SecurityIncident) -> bool:
        """Perform deep packet inspection"""
        try:
            # In a real implementation, this would trigger DPI analysis
            logger.info(f"Deep inspection triggered for incident: {incident.incident_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in deep inspection: {e}")
            return False
            
    async def _notify_siem(self, incident: SecurityIncident) -> bool:
        """Notify SIEM system"""
        try:
            # In a real implementation, this would send to SIEM via syslog/API
            logger.info(f"SIEM notification sent for incident: {incident.incident_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying SIEM: {e}")
            return False
            
    async def _save_incident(self, incident: SecurityIncident):
        """Save incident to file"""
        try:
            incident_file = self.incident_dir / f"{incident.incident_id}.json"
            
            with open(incident_file, 'w') as f:
                json.dump(incident.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving incident: {e}")
            
    async def _incident_management_loop(self):
        """Background incident management loop"""
        try:
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
                if not self.running:
                    break
                    
                # Move completed incidents to history
                completed_incidents = [
                    incident for incident in self.active_incidents.values()
                    if incident.response_status in ["completed", "failed"]
                ]
                
                for incident in completed_incidents:
                    self.incident_history.append(incident)
                    del self.active_incidents[incident.incident_id]
                    
                # Clean up old rate limits
                now = datetime.now()
                expired_ips = [
                    ip for ip, expiry in self.rate_limited_ips.items()
                    if now > expiry
                ]
                
                for ip in expired_ips:
                    del self.rate_limited_ips[ip]
                    
        except Exception as e:
            logger.error(f"Error in incident management loop: {e}")
            
    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        try:
            while self.running:
                await asyncio.sleep(300)  # Every 5 minutes
                
                if not self.running:
                    break
                    
                # Calculate metrics
                await self._calculate_metrics()
                
        except Exception as e:
            logger.error(f"Error in metrics collection loop: {e}")
            
    async def _calculate_metrics(self):
        """Calculate security metrics"""
        try:
            # Calculate false positive rate
            total_incidents = len(self.incident_history)
            if total_incidents > 0:
                false_positives = len([i for i in self.incident_history if i.false_positive])
                self.metrics.false_positive_rate = false_positives / total_incidents
                
            # Calculate detection accuracy
            detector_stats = self.anomaly_detector.get_detection_stats()
            self.metrics.detection_accuracy = detector_stats.get('model_accuracy', 0.0)
            
            # Calculate average response time
            response_times = []
            for incident in self.incident_history:
                if incident.response_timestamp:
                    response_time = (incident.response_timestamp - incident.timestamp).total_seconds()
                    response_times.append(response_time)
                    
            if response_times:
                self.metrics.average_response_time = sum(response_times) / len(response_times)
                
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        try:
            while self.running:
                await asyncio.sleep(3600)  # Every hour
                
                if not self.running:
                    break
                    
                # Clean up old incidents
                cutoff_date = datetime.now() - timedelta(days=self.incident_retention_days)
                
                self.incident_history = [
                    incident for incident in self.incident_history
                    if incident.timestamp > cutoff_date
                ]
                
                logger.info(f"Cleaned up old incidents older than {self.incident_retention_days} days")
                
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")
            
    async def _process_remaining_incidents(self):
        """Process remaining incidents before shutdown"""
        try:
            # Move active incidents to history
            for incident in self.active_incidents.values():
                self.incident_history.append(incident)
                
            self.active_incidents.clear()
            
        except Exception as e:
            logger.error(f"Error processing remaining incidents: {e}")
            
    async def _generate_final_reports(self):
        """Generate final security reports"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate incident summary report
            incident_report = {
                'timestamp': datetime.now().isoformat(),
                'total_incidents': len(self.incident_history),
                'incidents_by_severity': self.metrics.incidents_by_severity,
                'response_actions_taken': self.metrics.response_actions_taken,
                'blocked_ips': list(self.blocked_ips),
                'rate_limited_ips': list(self.rate_limited_ips.keys()),
                'metrics': self.metrics.to_dict(),
                'recent_incidents': [
                    incident.to_dict() for incident in 
                    sorted(self.incident_history, key=lambda x: x.timestamp, reverse=True)[:20]
                ]
            }
            
            report_file = self.report_dir / f"security_summary_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(incident_report, f, indent=2)
                
            logger.info(f"Final security report generated: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating final reports: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current security orchestrator status"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'running': self.running,
            'uptime_seconds': uptime,
            'active_incidents': len(self.active_incidents),
            'total_incidents': len(self.incident_history),
            'blocked_ips': len(self.blocked_ips),
            'rate_limited_ips': len(self.rate_limited_ips),
            'metrics': self.metrics.to_dict(),
            'sniffer_status': self.sniffer.get_status(),
            'detector_status': self.anomaly_detector.get_detection_stats()
        }
        
    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent security incidents"""
        recent = sorted(self.incident_history, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [incident.to_dict() for incident in recent]
        
    def get_incident_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get incident summary for specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_incidents = [i for i in self.incident_history if i.timestamp > cutoff]
        
        severity_counts = {}
        attack_type_counts = {}
        
        for incident in recent_incidents:
            # Count by severity
            severity = incident.severity.value
            if severity not in severity_counts:
                severity_counts[severity] = 0
            severity_counts[severity] += 1
            
            # Count by attack type
            attack_type = incident.attack_type.value
            if attack_type not in attack_type_counts:
                attack_type_counts[attack_type] = 0
            attack_type_counts[attack_type] += 1
            
        return {
            'time_period_hours': hours,
            'total_incidents': len(recent_incidents),
            'incidents_by_severity': severity_counts,
            'incidents_by_attack_type': attack_type_counts,
            'active_incidents': len(self.active_incidents),
            'blocked_ips': len(self.blocked_ips),
            'rate_limited_ips': len(self.rate_limited_ips)
        }
        
    def export_security_data(self, output_file: str) -> Dict[str, Any]:
        """Export security data"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'incidents': [incident.to_dict() for incident in self.incident_history],
                'metrics': self.metrics.to_dict(),
                'blocked_ips': list(self.blocked_ips),
                'rate_limited_ips': {ip: expiry.isoformat() for ip, expiry in self.rate_limited_ips.items()},
                'sniffer_status': self.sniffer.get_status(),
                'detector_stats': self.anomaly_detector.get_detection_stats()
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_file': output_file,
                'incidents_exported': len(self.incident_history),
                'blocked_ips_exported': len(self.blocked_ips)
            }
            
        except Exception as e:
            logger.error(f"Error exporting security data: {e}")
            return {
                'success': False,
                'error': str(e)
            } 