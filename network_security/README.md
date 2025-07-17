# Network Security Monitoring System

A comprehensive network security monitoring and automated response system that provides real-time traffic analysis, anomaly detection, and incident response capabilities. This system integrates multiple detection methods and automated response actions to provide robust network security monitoring.

## 🛡️ Features

### 📡 Network Traffic Monitoring (NetSniffer)
- **Multi-Tool Integration**: tcpdump, scapy, and pyshark for comprehensive packet capture
- **Real-Time Analysis**: Live traffic monitoring with configurable capture intervals
- **Protocol Support**: TCP, UDP, ICMP, DNS, and custom protocol analysis
- **Pattern Detection**: Automated detection of port scans, brute force, DDoS, and DNS tunneling
- **Flexible Filtering**: Configurable capture filters and packet analysis rules

### 🔍 Advanced Anomaly Detection
- **Multi-Method Detection**: Statistical, machine learning, and behavioral analysis
- **Machine Learning Models**: Isolation Forest, DBSCAN clustering, Random Forest classification
- **Behavioral Profiling**: Network behavior baselines and deviation detection
- **Feature Engineering**: Packet size, rate, port diversity, protocol distribution analysis
- **Adaptive Learning**: Continuous model updates based on network patterns

### 🚨 Security Orchestration
- **Incident Management**: Automated security incident creation and tracking
- **Severity Classification**: Multi-level alert system (INFO, WARNING, ERROR, CRITICAL)
- **Response Coordination**: Automated response action determination and execution
- **Integration Ready**: SIEM, SOAR, and external API integration capabilities

### ⚡ Automated Response Actions
- **Firewall Integration**: Automatic IP blocking via iptables, pf, or Windows Firewall
- **Traffic Shaping**: Bandwidth limiting and traffic control using tc (Linux)
- **Network Quarantine**: VLAN-based host isolation and quarantine
- **Connection Management**: TCP connection reset and session termination
- **External Notifications**: SIEM alerts, admin notifications, and API calls

### 🔒 Security & Safety
- **Dry Run Mode**: Safe testing without actual network changes
- **Rate Limiting**: Prevents excessive automated actions
- **Audit Trail**: Comprehensive logging of all actions and incidents
- **Rollback Capabilities**: Automatic cleanup of temporary security measures

## 🏗️ Architecture

```
network_security/
├── netsniffer.py              # Traffic capture and analysis
├── anomaly_detector.py        # ML-based anomaly detection
├── security_orchestrator.py   # Main coordination system
├── network_actions.py         # Automated response actions
├── demo.py                    # Comprehensive demonstration
├── requirements.txt           # Python dependencies
└── README.md                  # This file

Data Storage:
├── logs/                      # System logs and traces
├── reports/                   # Generated reports and analytics
├── captures/                  # Packet capture files
├── incidents/                 # Security incident records
├── actions/                   # Response action logs
├── models/                    # ML model storage
└── profiles/                  # Network behavior profiles
```

## 🔧 Installation

### Prerequisites

- **Python 3.8+**
- **Root/Administrator privileges** (for packet capture)
- **Network tools**: tcpdump, iptables/pf, ss
- **Optional**: tc (traffic control) for bandwidth limiting

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tcpdump iptables iproute2 net-tools

# CentOS/RHEL
sudo yum install tcpdump iptables iproute net-tools

# macOS
brew install tcpdump
```

### Python Environment

```bash
# Create virtual environment
python -m venv network_security_env
source network_security_env/bin/activate  # Linux/Mac
# network_security_env\Scripts\activate   # Windows

# Install dependencies
cd network_security
pip install -r requirements.txt
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from network_security import SecurityOrchestrator

async def basic_monitoring():
    # Configuration
    config = {
        'sniffer': {
            'interface': 'eth0',
            'capture_duration': 300,  # 5 minutes
            'anomaly_threshold': 0.7
        },
        'response': {
            'auto_response_enabled': True,
            'dry_run': False  # Set to True for testing
        }
    }
    
    # Initialize and start
    orchestrator = SecurityOrchestrator(config)
    await orchestrator.start()
    
    # Monitor for incidents
    try:
        while True:
            status = orchestrator.get_status()
            print(f"Active incidents: {status['active_incidents']}")
            print(f"Blocked IPs: {status['blocked_ips']}")
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        
    finally:
        await orchestrator.stop()

# Run monitoring
asyncio.run(basic_monitoring())
```

### Advanced Configuration

```python
# Comprehensive configuration
config = {
    'sniffer': {
        'interface': 'any',
        'capture_filter': 'not port 22',  # Exclude SSH
        'capture_duration': 600,
        'packet_count_limit': 50000,
        'analysis_batch_size': 1000
    },
    'detector': {
        'detection_methods': ['statistical', 'machine_learning', 'behavioral'],
        'anomaly_threshold': 0.8,
        'confidence_threshold': 0.7,
        'model_update_interval': 1800,
        'feature_window_size': 200
    },
    'response': {
        'auto_response_enabled': True,
        'response_threshold': 0.75,
        'max_concurrent_actions': 15,
        'dry_run': False
    },
    'actions': {
        'firewall_type': 'iptables',
        'default_action_timeout': 600,
        'quarantine_vlan': 999,
        'bandwidth_limit': '1mbit'
    }
}

orchestrator = SecurityOrchestrator(config)
```

## 📊 Running the Demo

Execute the comprehensive demonstration:

```bash
# Run as root for full capabilities
sudo python demo.py

# Or run with limited capabilities
python demo.py
```

The demo showcases:
1. 🔍 **Prerequisites Check**: System capabilities and tool availability
2. 🚀 **System Startup**: Component initialization and configuration
3. 📡 **Traffic Monitoring**: Real-time packet capture and analysis
4. 🔍 **Anomaly Detection**: ML-based threat detection
5. 🚨 **Incident Response**: Automated security incident management
6. ⚡ **Network Actions**: Automated response demonstrations
7. 📊 **Status Reporting**: Comprehensive system metrics
8. 📋 **Report Generation**: Security analytics and summaries

## 🔧 Configuration

### Environment Variables

```bash
# Network interface
NETWORK_INTERFACE=eth0

# Capture settings
CAPTURE_DURATION=300
PACKET_LIMIT=10000

# Detection thresholds
ANOMALY_THRESHOLD=0.7
RESPONSE_THRESHOLD=0.8

# Safety settings
DRY_RUN=true
MAX_CONCURRENT_ACTIONS=10

# External integrations
SIEM_URL=https://siem.company.com/api
SLACK_WEBHOOK=https://hooks.slack.com/services/xxx
```

### Configuration Files

```yaml
# config.yaml
network_security:
  sniffer:
    interface: "eth0"
    capture_duration: 300
    anomaly_threshold: 0.7
  
  detector:
    detection_methods:
      - statistical
      - machine_learning
      - behavioral
    model_update_interval: 1800
  
  response:
    auto_response_enabled: true
    dry_run: false
    actions:
      - firewall_block
      - rate_limit
      - quarantine
  
  integrations:
    siem:
      url: "https://siem.company.com/api"
      api_key: "your_api_key"
    
    slack:
      webhook: "https://hooks.slack.com/services/xxx"
```

## 🔍 Detection Methods

### Statistical Analysis
- **Z-Score Analysis**: Packet size and rate deviation detection
- **Protocol Distribution**: Unusual protocol usage patterns
- **Time-based Analysis**: Off-hours activity detection
- **Port Analysis**: Unusual port access patterns

### Machine Learning
- **Isolation Forest**: Unsupervised anomaly detection
- **DBSCAN Clustering**: Behavioral pattern clustering
- **Random Forest**: Supervised attack classification
- **Feature Engineering**: Advanced packet feature extraction

### Behavioral Analysis
- **Connection Patterns**: Unusual connection sequences
- **Traffic Profiling**: Baseline behavior establishment
- **Temporal Analysis**: Time-based behavioral patterns
- **Frequency Analysis**: Rate-based anomaly detection

## ⚡ Response Actions

### Firewall Integration
```python
# Automatic IP blocking
await action_engine.queue_action(
    ActionType.FIREWALL_BLOCK,
    target_ip="192.168.1.100",
    target_port=22,
    duration_seconds=3600
)
```

### Traffic Control
```python
# Bandwidth limiting
await action_engine.queue_action(
    ActionType.TRAFFIC_SHAPING,
    target_ip="192.168.1.101",
    parameters={'bandwidth_limit': '100kbit'}
)
```

### Network Quarantine
```python
# VLAN isolation
await action_engine.queue_action(
    ActionType.QUARANTINE_VLAN,
    target_ip="192.168.1.102",
    duration_seconds=7200
)
```

## 📊 Monitoring & Analytics

### Real-Time Metrics
- **Packet Analysis Rate**: Packets processed per second
- **Anomaly Detection Rate**: Anomalies detected per hour
- **Response Time**: Average incident response time
- **Success Rate**: Response action success percentage

### Security Dashboards
- **Incident Timeline**: Chronological incident visualization
- **Attack Type Distribution**: Categorized threat analysis
- **Network Behavior**: Traffic pattern analysis
- **Response Effectiveness**: Action success tracking

### Reporting
```python
# Generate comprehensive report
report = orchestrator.get_comprehensive_report()

# Export security data
orchestrator.export_security_data('security_report.json')

# Get recent incidents
incidents = orchestrator.get_recent_incidents(limit=20)
```

## 🔗 Integration

### SIEM Integration
```python
# Configure SIEM integration
siem_config = {
    'url': 'https://siem.company.com/api',
    'api_key': 'your_api_key',
    'format': 'json'
}

# Automatic SIEM notifications
orchestrator.add_incident_callback(send_to_siem)
```

### API Integration
```python
# External API notifications
async def notify_external_api(incident):
    async with aiohttp.ClientSession() as session:
        payload = {
            'alert_type': incident.attack_type.value,
            'severity': incident.severity.value,
            'source_ip': incident.source_ip,
            'timestamp': incident.timestamp.isoformat()
        }
        
        await session.post(
            'https://api.security-platform.com/alerts',
            json=payload,
            headers={'Authorization': f'Bearer {api_token}'}
        )
```

### Webhook Integration
```python
# Slack/Teams notifications
async def send_slack_alert(incident):
    webhook_url = "https://hooks.slack.com/services/xxx"
    
    message = {
        "text": f"🚨 Security Alert: {incident.title}",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Source IP", "value": incident.source_ip},
                {"title": "Attack Type", "value": incident.attack_type.value},
                {"title": "Severity", "value": incident.severity.value}
            ]
        }]
    }
    
    await send_webhook(webhook_url, message)
```

## 🛠️ Advanced Features

### Custom Detection Rules
```python
# Define custom anomaly detection
async def custom_threat_detector(packet):
    # Custom logic for specific threats
    if packet.dst_port in [1433, 3306, 5432]:  # Database ports
        if packet.src_ip not in trusted_ips:
            return AnomalyScore(
                score=0.8,
                confidence=0.9,
                method=AnomalyDetectionMethod.CUSTOM,
                explanation="Unauthorized database access attempt"
            )
    
    return None

# Register custom detector
orchestrator.anomaly_detector.add_custom_detector(custom_threat_detector)
```

### Response Automation
```python
# Custom response actions
async def custom_response_handler(incident):
    if incident.attack_type == AttackType.BRUTE_FORCE:
        # Block IP for 24 hours
        await action_engine.queue_action(
            ActionType.FIREWALL_BLOCK,
            incident.source_ip,
            duration_seconds=86400
        )
        
        # Notify security team
        await send_email_alert(incident)
        
        # Update threat intelligence
        await update_threat_feeds(incident.source_ip)
```

### Machine Learning Tuning
```python
# Custom ML model configuration
detector_config = {
    'isolation_forest': {
        'contamination': 0.1,
        'n_estimators': 200,
        'max_samples': 'auto'
    },
    'dbscan': {
        'eps': 0.3,
        'min_samples': 10
    },
    'feature_engineering': {
        'packet_size_bins': 20,
        'time_window_minutes': 5,
        'protocol_encoding': 'one_hot'
    }
}
```

## 🔒 Security Considerations

### Deployment Security
- **Network Segmentation**: Deploy on dedicated monitoring network
- **Access Control**: Restrict system access to authorized personnel
- **Encrypted Communications**: Use TLS for all external communications
- **Log Security**: Secure and tamper-proof logging

### Operational Security
- **Regular Updates**: Keep detection models and rules current
- **False Positive Management**: Regular tuning to minimize false alerts
- **Incident Response**: Documented response procedures
- **Compliance**: Ensure regulatory compliance (GDPR, HIPAA, etc.)

## 📈 Performance Tuning

### Optimization Settings
```python
# High-performance configuration
config = {
    'sniffer': {
        'analysis_batch_size': 5000,
        'max_packet_history': 50000,
        'capture_file_rotation': True
    },
    'detector': {
        'model_update_interval': 3600,
        'feature_window_size': 1000,
        'parallel_processing': True
    },
    'response': {
        'max_concurrent_actions': 50,
        'action_timeout': 30
    }
}
```

### Resource Management
- **Memory**: Monitor packet buffer sizes and model memory usage
- **CPU**: Optimize detection algorithms and parallel processing
- **Storage**: Implement log rotation and data archiving
- **Network**: Minimize monitoring impact on network performance

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests
python -m pytest tests/unit/

# Run with coverage
python -m pytest tests/unit/ --cov=network_security
```

### Integration Tests
```bash
# Run integration tests
python -m pytest tests/integration/

# Run specific test suites
python -m pytest tests/integration/test_anomaly_detection.py
```

### Performance Tests
```bash
# Run performance benchmarks
python -m pytest tests/performance/

# Load testing
python tests/performance/load_test.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Packet Capture Fails**
   ```bash
   # Check interface
   ip link show
   
   # Verify permissions
   sudo tcpdump -i eth0 -c 10
   
   # Check firewall rules
   sudo iptables -L
   ```

2. **High False Positive Rate**
   ```python
   # Adjust thresholds
   config['detector']['anomaly_threshold'] = 0.9
   config['detector']['confidence_threshold'] = 0.8
   
   # Retrain models
   await orchestrator.anomaly_detector.update_models()
   ```

3. **Response Actions Fail**
   ```bash
   # Check iptables
   sudo iptables -L -n
   
   # Verify tc availability
   tc qdisc show
   
   # Check permissions
   sudo -l
   ```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable dry run mode
config['response']['dry_run'] = True

# Increase verbosity
config['debug'] = True
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code quality checks
flake8 network_security/
black network_security/
mypy network_security/

# Run all tests
pytest
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Complete API documentation in `docs/`
- **Examples**: Additional examples in `examples/`
- **Issues**: Report bugs and request features via GitHub issues
- **Discussions**: Join community discussions for questions and ideas

## 🗺️ Roadmap

### Version 2.0
- **Deep Learning**: Advanced neural network-based detection
- **Cloud Integration**: AWS/Azure/GCP security service integration
- **Container Security**: Docker and Kubernetes monitoring
- **Threat Intelligence**: External threat feed integration

### Version 3.0
- **Zero Trust**: Zero-trust architecture support
- **AI/ML Ops**: Automated model training and deployment
- **Distributed Monitoring**: Multi-node deployment support
- **Advanced Visualization**: Real-time security dashboards

---

**The Network Security Monitoring System provides enterprise-grade network security monitoring and automated incident response capabilities, enabling organizations to detect, analyze, and respond to network threats in real-time.** 