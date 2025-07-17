"""
Safeguards for Autonomous AI Agent Framework

Comprehensive safety system for quantum computing and HPC operations
with resource limits, security checks, and incident management.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Severity levels for security incidents"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafeguardViolationType(Enum):
    """Types of safeguard violations"""
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_THREAT = "security_threat"
    RATE_LIMIT = "rate_limit"
    UNSAFE_CODE = "unsafe_code"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DANGEROUS_OPERATION = "dangerous_operation"


@dataclass
class SecurityIncident:
    """Security incident record"""
    incident_id: str
    violation_type: SafeguardViolationType
    severity: IncidentSeverity
    description: str
    platform: str
    code_snippet: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'incident_id': self.incident_id,
            'violation_type': self.violation_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'platform': self.platform,
            'code_snippet': self.code_snippet,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes
        }


class QuantumSafeguards:
    """
    Comprehensive safeguards system for quantum computing and HPC operations.
    Prevents resource abuse, security threats, and unsafe operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the safeguards system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Load safety limits from environment
        self.quantum_limits = {
            'max_qubits_public': int(os.getenv('MAX_QUBITS_PUBLIC', 20)),
            'max_shots_public': int(os.getenv('MAX_SHOTS_PUBLIC', 8192)),
            'max_circuit_depth': 1000,
            'max_gate_count': 10000
        }
        
        self.hpc_limits = {
            'max_jobs_per_hour': int(os.getenv('MAX_SLURM_JOBS_PER_HOUR', 10)),
            'max_walltime_hours': int(os.getenv('MAX_HPC_WALLTIME_HOURS', 24)),
            'max_nodes_per_job': 64,
            'max_memory_gb': 512,
            'max_cpus_per_job': 1024
        }
        
        # Rate limiting
        self.rate_limits = {
            'quantum_jobs_per_hour': 50,
            'hpc_jobs_per_hour': 20,
            'api_calls_per_minute': 100,
            'data_transfer_mb_per_hour': 1000
        }
        
        # Tracking structures
        self.incidents: List[SecurityIncident] = []
        self.blocked_operations: Set[str] = set()
        self.rate_tracking: Dict[str, deque] = defaultdict(deque)
        
        # Dangerous patterns
        self.dangerous_quantum_patterns = [
            # Dangerous quantum operations
            r'quantum_info\.random_state',  # Potential state injection
            r'\.save\s*\(',                # File operations in quantum code
            r'subprocess\.',               # System calls
            r'os\.',                      # OS operations
            r'eval\s*\(',                 # Code evaluation
            r'exec\s*\(',                 # Code execution
            r'__import__',                # Dynamic imports
            r'while\s+True',              # Infinite loops
            r'for\s+\w+\s+in\s+range\s*\(\s*\d{6,}\)',  # Large loops
        ]
        
        self.dangerous_hpc_patterns = [
            # Destructive operations
            r'rm\s+-rf\s+/',              # Recursive delete from root
            r'format\s+[a-z]:\s*',        # Disk formatting
            r'mkfs\.',                    # File system creation
            r'dd\s+if=/dev/zero',         # Disk wiping
            r'shred\s+',                  # Secure deletion
            
            # Privilege escalation
            r'sudo\s+',                   # Sudo usage
            r'su\s+-',                    # User switching
            r'chmod\s+777',               # Dangerous permissions
            r'chown\s+root',              # Ownership changes
            
            # Network attacks
            r'nc\s+-l',                   # Netcat listener
            r'nmap\s+',                   # Network scanning
            r'wireshark',                 # Packet capture
            r'tcpdump',                   # Traffic monitoring
            
            # System modification
            r'/etc/passwd',               # Password file
            r'/etc/shadow',               # Shadow file
            r'registry\s+edit',           # Windows registry
            r'msconfig',                  # System configuration
            
            # Fork bombs and resource exhaustion
            r':\(\)\{.*:\|:&\};:',        # Classic bash fork bomb
            r'while\s*\(\s*1\s*\)',       # Infinite C loop
            r'for\s*\(\s*;\s*;\s*\)',     # Infinite C for loop
        ]
        
        # Resource monitoring thresholds
        self.resource_thresholds = {
            'cpu_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'network_usage_mbps': 100
        }
        
        logger.info("Quantum Safeguards initialized")
        
    def validate_quantum_operation(self, 
                                  platform: str,
                                  code: str,
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a quantum computing operation.
        
        Args:
            platform: Target quantum platform
            code: Quantum circuit code
            parameters: Operation parameters
            
        Returns:
            Validation result with safety assessment
        """
        validation_result = {
            'safe': True,
            'warnings': [],
            'errors': [],
            'blocked_reasons': []
        }
        
        try:
            # Check rate limits
            rate_check = self._check_rate_limit('quantum_jobs', self.rate_limits['quantum_jobs_per_hour'])
            if not rate_check['allowed']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(f"Rate limit exceeded: {rate_check['reason']}")
                
            # Check quantum-specific limits
            qubits = parameters.get('qubits', 0)
            shots = parameters.get('shots', 1024)
            
            if qubits > self.quantum_limits['max_qubits_public']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"Qubit count ({qubits}) exceeds limit ({self.quantum_limits['max_qubits_public']})"
                )
                
            if shots > self.quantum_limits['max_shots_public']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"Shot count ({shots}) exceeds limit ({self.quantum_limits['max_shots_public']})"
                )
                
            # Check for dangerous code patterns
            dangerous_patterns = self._scan_for_dangerous_patterns(code, self.dangerous_quantum_patterns)
            if dangerous_patterns:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].extend([
                    f"Dangerous pattern detected: {pattern}" for pattern in dangerous_patterns
                ])
                
            # Platform-specific checks
            if 'ibm' in platform.lower() and not self._validate_ibm_quantum_access():
                validation_result['warnings'].append("IBM Quantum access validation failed")
                
            # Check for resource exhaustion patterns
            resource_issues = self._check_quantum_resource_usage(code, parameters)
            if resource_issues:
                validation_result['warnings'].extend(resource_issues)
                
            # Log validation
            if not validation_result['safe']:
                self._log_security_incident(
                    SafeguardViolationType.UNSAFE_CODE,
                    IncidentSeverity.MEDIUM,
                    f"Quantum operation blocked on {platform}",
                    platform,
                    code,
                    parameters
                )
                
        except Exception as e:
            logger.error(f"Quantum validation error: {e}")
            validation_result['safe'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            
        return validation_result
        
    def validate_hpc_operation(self,
                              cluster: str,
                              job_script: str,
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an HPC operation.
        
        Args:
            cluster: Target HPC cluster
            job_script: Job script content
            parameters: Job parameters
            
        Returns:
            Validation result with safety assessment
        """
        validation_result = {
            'safe': True,
            'warnings': [],
            'errors': [],
            'blocked_reasons': []
        }
        
        try:
            # Check rate limits
            rate_check = self._check_rate_limit('hpc_jobs', self.rate_limits['hpc_jobs_per_hour'])
            if not rate_check['allowed']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(f"Rate limit exceeded: {rate_check['reason']}")
                
            # Check HPC resource limits
            nodes = parameters.get('nodes', 1)
            cpus = parameters.get('cpus_per_task', 1)
            memory_gb = parameters.get('memory_gb', 4)
            walltime_hours = parameters.get('walltime_hours', 1)
            
            if nodes > self.hpc_limits['max_nodes_per_job']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"Node count ({nodes}) exceeds limit ({self.hpc_limits['max_nodes_per_job']})"
                )
                
            if cpus > self.hpc_limits['max_cpus_per_job']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"CPU count ({cpus}) exceeds limit ({self.hpc_limits['max_cpus_per_job']})"
                )
                
            if memory_gb > self.hpc_limits['max_memory_gb']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"Memory ({memory_gb}GB) exceeds limit ({self.hpc_limits['max_memory_gb']}GB)"
                )
                
            if walltime_hours > self.hpc_limits['max_walltime_hours']:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].append(
                    f"Walltime ({walltime_hours}h) exceeds limit ({self.hpc_limits['max_walltime_hours']}h)"
                )
                
            # Check for dangerous script patterns
            dangerous_patterns = self._scan_for_dangerous_patterns(job_script, self.dangerous_hpc_patterns)
            if dangerous_patterns:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].extend([
                    f"Dangerous pattern detected: {pattern}" for pattern in dangerous_patterns
                ])
                
            # Check for privilege escalation attempts
            privilege_issues = self._check_privilege_escalation(job_script)
            if privilege_issues:
                validation_result['safe'] = False
                validation_result['blocked_reasons'].extend(privilege_issues)
                
            # Check for resource exhaustion patterns
            resource_issues = self._check_hpc_resource_exhaustion(job_script)
            if resource_issues:
                validation_result['warnings'].extend(resource_issues)
                
            # Log validation
            if not validation_result['safe']:
                self._log_security_incident(
                    SafeguardViolationType.UNSAFE_CODE,
                    IncidentSeverity.HIGH,
                    f"HPC operation blocked on {cluster}",
                    cluster,
                    job_script,
                    parameters
                )
                
        except Exception as e:
            logger.error(f"HPC validation error: {e}")
            validation_result['safe'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            
        return validation_result
        
    def _check_rate_limit(self, operation_type: str, limit_per_hour: int) -> Dict[str, Any]:
        """Check if operation is within rate limits."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        while self.rate_tracking[operation_type] and self.rate_tracking[operation_type][0] < hour_ago:
            self.rate_tracking[operation_type].popleft()
            
        # Check current count
        current_count = len(self.rate_tracking[operation_type])
        
        if current_count >= limit_per_hour:
            return {
                'allowed': False,
                'reason': f'{operation_type} rate limit exceeded: {current_count}/{limit_per_hour} per hour'
            }
            
        # Record this operation
        self.rate_tracking[operation_type].append(now)
        
        return {
            'allowed': True,
            'current_count': current_count + 1,
            'limit': limit_per_hour
        }
        
    def _scan_for_dangerous_patterns(self, code: str, patterns: List[str]) -> List[str]:
        """Scan code for dangerous patterns."""
        detected_patterns = []
        
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                detected_patterns.append(pattern)
                
        return detected_patterns
        
    def _check_privilege_escalation(self, script: str) -> List[str]:
        """Check for privilege escalation attempts."""
        issues = []
        
        # Check for common privilege escalation patterns
        escalation_patterns = [
            (r'sudo\s+', 'sudo usage detected'),
            (r'su\s+-', 'user switching detected'),
            (r'chmod\s+[4-7][7-7][7-7]', 'dangerous file permissions'),
            (r'chown\s+root', 'ownership change to root'),
            (r'setuid', 'setuid usage detected'),
            (r'/etc/sudoers', 'sudoers file modification attempt')
        ]
        
        for pattern, description in escalation_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append(description)
                
        return issues
        
    def _check_quantum_resource_usage(self, code: str, parameters: Dict[str, Any]) -> List[str]:
        """Check for quantum resource usage issues."""
        warnings = []
        
        # Check for potentially expensive operations
        if 'optimization' in code.lower() and parameters.get('shots', 0) > 1000:
            warnings.append("High shot count with optimization may be resource intensive")
            
        # Check for nested loops that could create large circuits
        nested_loop_pattern = r'for.*for.*'
        if re.search(nested_loop_pattern, code, re.MULTILINE):
            warnings.append("Nested loops detected - potential circuit complexity explosion")
            
        # Check for unbounded ranges
        large_range_pattern = r'range\s*\(\s*\d{4,}\s*\)'
        if re.search(large_range_pattern, code):
            warnings.append("Large range detected - potential resource exhaustion")
            
        return warnings
        
    def _check_hpc_resource_exhaustion(self, script: str) -> List[str]:
        """Check for HPC resource exhaustion patterns."""
        warnings = []
        
        # Check for potential fork bombs
        fork_patterns = [
            r'while\s*true.*do.*done',
            r'for\s*\(\s*;\s*;\s*\)',
            r':\(\)\{.*:\|:&\};:',
        ]
        
        for pattern in fork_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                warnings.append("Potential resource exhaustion pattern detected")
                break
                
        # Check for large file operations
        if re.search(r'dd\s+.*bs=\d*[MG]', script, re.IGNORECASE):
            warnings.append("Large file operation detected")
            
        # Check for network operations that might be excessive
        if re.search(r'wget.*-r|curl.*-O.*\*', script, re.IGNORECASE):
            warnings.append("Potentially excessive network operation detected")
            
        return warnings
        
    def _validate_ibm_quantum_access(self) -> bool:
        """Validate IBM Quantum access credentials."""
        try:
            ibm_token = os.getenv('IBMQ_API_TOKEN')
            return ibm_token is not None and len(ibm_token) > 10
        except:
            return False
            
    def _log_security_incident(self,
                              violation_type: SafeguardViolationType,
                              severity: IncidentSeverity,
                              description: str,
                              platform: str,
                              code: str = "",
                              parameters: Dict[str, Any] = None):
        """Log a security incident."""
        incident = SecurityIncident(
            incident_id=f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.incidents)}",
            violation_type=violation_type,
            severity=severity,
            description=description,
            platform=platform,
            code_snippet=code[:500] if code else "",  # Limit code snippet size
            parameters=parameters or {}
        )
        
        self.incidents.append(incident)
        
        # Limit incident history
        if len(self.incidents) > 1000:
            self.incidents = self.incidents[-1000:]
            
        # Log based on severity
        if severity == IncidentSeverity.CRITICAL:
            logger.critical(f"CRITICAL SECURITY INCIDENT: {description}")
        elif severity == IncidentSeverity.HIGH:
            logger.error(f"HIGH SECURITY INCIDENT: {description}")
        elif severity == IncidentSeverity.MEDIUM:
            logger.warning(f"MEDIUM SECURITY INCIDENT: {description}")
        else:
            logger.info(f"LOW SECURITY INCIDENT: {description}")
            
    def block_operation(self, operation_id: str, reason: str):
        """Block a specific operation."""
        self.blocked_operations.add(operation_id)
        logger.warning(f"Blocked operation {operation_id}: {reason}")
        
    def unblock_operation(self, operation_id: str):
        """Unblock a previously blocked operation."""
        if operation_id in self.blocked_operations:
            self.blocked_operations.remove(operation_id)
            logger.info(f"Unblocked operation {operation_id}")
            
    def is_operation_blocked(self, operation_id: str) -> bool:
        """Check if an operation is blocked."""
        return operation_id in self.blocked_operations
        
    def resolve_incident(self, incident_id: str, resolution_notes: str = ""):
        """Resolve a security incident."""
        for incident in self.incidents:
            if incident.incident_id == incident_id:
                incident.resolved = True
                incident.resolution_notes = resolution_notes
                logger.info(f"Resolved incident {incident_id}: {resolution_notes}")
                return True
                
        return False
        
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        recent_incidents = [
            inc for inc in self.incidents
            if inc.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        unresolved_incidents = [inc for inc in self.incidents if not inc.resolved]
        
        # Count incidents by severity
        severity_counts = {}
        for incident in recent_incidents:
            severity = incident.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
        # Rate limit status
        rate_status = {}
        for operation_type, timestamps in self.rate_tracking.items():
            rate_status[operation_type] = {
                'current_count': len(timestamps),
                'limit': self.rate_limits.get(f"{operation_type}_per_hour", 0)
            }
            
        return {
            'total_incidents': len(self.incidents),
            'recent_incidents_24h': len(recent_incidents),
            'unresolved_incidents': len(unresolved_incidents),
            'severity_distribution': severity_counts,
            'blocked_operations': len(self.blocked_operations),
            'rate_limit_status': rate_status,
            'quantum_limits': self.quantum_limits,
            'hpc_limits': self.hpc_limits
        }
        
    def get_recent_incidents(self, hours: int = 24, severity: Optional[IncidentSeverity] = None) -> List[Dict[str, Any]]:
        """Get recent security incidents."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_incidents = [
            inc for inc in self.incidents
            if inc.timestamp > cutoff
        ]
        
        if severity:
            recent_incidents = [
                inc for inc in recent_incidents
                if inc.severity == severity
            ]
            
        return [incident.to_dict() for incident in recent_incidents]
        
    def export_incident_log(self, output_path: str) -> Dict[str, Any]:
        """Export incident log for analysis."""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_incidents': len(self.incidents),
                'incidents': [incident.to_dict() for incident in self.incidents],
                'blocked_operations': list(self.blocked_operations),
                'safeguard_config': {
                    'quantum_limits': self.quantum_limits,
                    'hpc_limits': self.hpc_limits,
                    'rate_limits': self.rate_limits
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_path': output_path,
                'exported_incidents': len(self.incidents),
                'file_size_mb': os.path.getsize(output_path) / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"Failed to export incident log: {e}")
            return {'success': False, 'error': str(e)}
            
    def update_limits(self, new_limits: Dict[str, Dict[str, Any]]):
        """Update safety limits."""
        if 'quantum_limits' in new_limits:
            self.quantum_limits.update(new_limits['quantum_limits'])
            
        if 'hpc_limits' in new_limits:
            self.hpc_limits.update(new_limits['hpc_limits'])
            
        if 'rate_limits' in new_limits:
            self.rate_limits.update(new_limits['rate_limits'])
            
        logger.info("Safety limits updated")
        
    def get_safeguard_stats(self) -> Dict[str, Any]:
        """Get comprehensive safeguard statistics."""
        return {
            'incidents': {
                'total': len(self.incidents),
                'unresolved': len([i for i in self.incidents if not i.resolved]),
                'by_severity': {
                    sev.value: len([i for i in self.incidents if i.severity == sev])
                    for sev in IncidentSeverity
                },
                'by_violation_type': {
                    vt.value: len([i for i in self.incidents if i.violation_type == vt])
                    for vt in SafeguardViolationType
                }
            },
            'blocked_operations': len(self.blocked_operations),
            'rate_limiting': {
                operation: len(timestamps)
                for operation, timestamps in self.rate_tracking.items()
            },
            'limits': {
                'quantum': self.quantum_limits,
                'hpc': self.hpc_limits,
                'rate': self.rate_limits
            }
        } 