"""
Network Security Monitoring System

A comprehensive network security monitoring and response system that provides:
- Real-time traffic capture and analysis with tcpdump/scapy/pyshark
- Advanced anomaly detection using machine learning and statistical analysis
- Automated security incident response and remediation
- Integration with security orchestration and response platforms
"""

__version__ = "1.0.0"
__author__ = "AI Security Engineer"
__description__ = "Network Security Monitoring and Automated Response System"

from .netsniffer import (
    NetSniffer,
    PacketMetadata,
    TrafficAnomaly,
    AttackType,
    TrafficType
)

from .anomaly_detector import (
    NetworkAnomalyDetector,
    AnomalyScore,
    AnomalyDetectionMethod,
    NetworkProfile,
    ThreatLevel
)

from .security_orchestrator import (
    SecurityOrchestrator,
    SecurityIncident,
    AlertSeverity,
    ResponseAction,
    SecurityMetrics
)

from .network_actions import (
    NetworkActionEngine,
    NetworkAction,
    ActionType,
    ActionStatus
)

__all__ = [
    # NetSniffer
    "NetSniffer",
    "PacketMetadata",
    "TrafficAnomaly",
    "AttackType",
    "TrafficType",
    
    # Anomaly Detector
    "NetworkAnomalyDetector",
    "AnomalyScore",
    "AnomalyDetectionMethod",
    "NetworkProfile",
    "ThreatLevel",
    
    # Security Orchestrator
    "SecurityOrchestrator",
    "SecurityIncident",
    "AlertSeverity",
    "ResponseAction",
    "SecurityMetrics",
    
    # Network Actions
    "NetworkActionEngine",
    "NetworkAction",
    "ActionType",
    "ActionStatus"
] 