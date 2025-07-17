"""
Safety Manager for Autonomous AI Agent Framework

Implements rate limiting, permission checks, resource monitoring,
and other safety mechanisms to ensure safe agent operation.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import psutil
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyViolationType(Enum):
    """Types of safety violations"""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    DANGEROUS_ACTION = "dangerous_action"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class SafetyViolation:
    """Represents a safety violation"""
    violation_type: SafetyViolationType
    action_type: str
    description: str
    risk_level: RiskLevel
    timestamp: datetime = field(default_factory=datetime.now)
    action_data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            'violation_type': self.violation_type.value,
            'action_type': self.action_type,
            'description': self.description,
            'risk_level': self.risk_level.value,
            'timestamp': self.timestamp.isoformat(),
            'action_data': self.action_data,
            'resolved': self.resolved
        }


@dataclass
class RateLimitBucket:
    """Rate limiting bucket"""
    max_count: int
    window_seconds: int
    actions: deque = field(default_factory=deque)
    
    def can_perform_action(self) -> bool:
        """Check if action can be performed within rate limit."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old actions
        while self.actions and self.actions[0] < cutoff:
            self.actions.popleft()
            
        return len(self.actions) < self.max_count
        
    def record_action(self):
        """Record an action in the bucket."""
        self.actions.append(datetime.now())


class SafetyManager:
    """
    Manages safety mechanisms including rate limiting,
    permission checks, and resource monitoring.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the safety manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        
        # Safety configuration
        self.safety_config = config_manager.get_section('safety')
        self.enabled = self.safety_config.get('enabled', True)
        
        # Rate limiting configuration
        rate_limits = self.safety_config.get('rate_limits', {})
        self.rate_limits = {
            'actions': RateLimitBucket(
                max_count=rate_limits.get('actions_per_minute', 30),
                window_seconds=60
            ),
            'api_calls': RateLimitBucket(
                max_count=rate_limits.get('api_calls_per_minute', 60),
                window_seconds=60
            ),
            'memory_writes': RateLimitBucket(
                max_count=rate_limits.get('memory_writes_per_minute', 120),
                window_seconds=60
            )
        }
        
        # Monitoring configuration
        monitoring = self.safety_config.get('monitoring', {})
        self.track_resource_usage = monitoring.get('track_resource_usage', True)
        self.alert_on_anomalies = monitoring.get('alert_on_anomalies', True)
        self.log_all_actions = monitoring.get('log_all_actions', True)
        
        # Permission configuration
        permissions = self.safety_config.get('permissions', {})
        self.require_approval_for = set(permissions.get('require_approval_for', []))
        
        # Safety state
        self.violations: List[SafetyViolation] = []
        self.resource_baselines: Dict[str, float] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            'cpu_usage': 80.0,      # Percent
            'memory_usage': 1024.0,  # MB
            'disk_usage': 90.0,      # Percent
            'network_activity': 100.0  # MB/min
        }
        
        # Action risk assessment
        self.action_risk_levels = {
            'system_command': RiskLevel.HIGH,
            'file_operation': RiskLevel.MEDIUM,
            'api_call': RiskLevel.LOW,
            'memory_operation': RiskLevel.LOW,
            'planning': RiskLevel.LOW
        }
        
        # Dangerous action patterns
        self.dangerous_patterns = {
            'destructive_commands': [
                'rm -rf', 'del /f', 'format', 'fdisk', 'mkfs',
                'dd if=/dev/zero', 'shred', 'wipe'
            ],
            'privilege_escalation': [
                'sudo', 'su -', 'runas', 'chmod 777', 'chown root'
            ],
            'network_attacks': [
                'nmap', 'nc -l', 'netcat', 'wireshark', 'tcpdump'
            ],
            'system_modification': [
                '/etc/passwd', '/etc/shadow', 'registry edit',
                'services.msc', 'msconfig'
            ]
        }
        
        # Initialize baselines
        if self.track_resource_usage:
            self._initialize_resource_baselines()
            
        logger.info(f"Safety Manager initialized - Enabled: {self.enabled}")
        
    def _initialize_resource_baselines(self):
        """Initialize resource usage baselines."""
        try:
            # Get initial system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            self.resource_baselines = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_info.used / 1024 / 1024,  # MB
                'memory_available': memory_info.available / 1024 / 1024,  # MB
                'disk_usage_percent': disk_info.percent
            }
            
            logger.info(f"Resource baselines initialized: {self.resource_baselines}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize resource baselines: {e}")
            self.resource_baselines = {}
            
    async def validate_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an action against safety policies.
        
        Args:
            action_type: Type of action to validate
            action_data: Action parameters and data
            
        Returns:
            Dictionary with validation results
        """
        if not self.enabled:
            return {'allowed': True, 'reason': 'Safety manager disabled'}
            
        validation_result = {
            'allowed': True,
            'reason': 'Action approved',
            'risk_level': RiskLevel.LOW,
            'warnings': [],
            'requirements': []
        }
        
        try:
            # Check rate limits
            rate_limit_check = self._check_rate_limits(action_type)
            if not rate_limit_check['allowed']:
                validation_result.update(rate_limit_check)
                self._record_violation(
                    SafetyViolationType.RATE_LIMIT_EXCEEDED,
                    action_type,
                    rate_limit_check['reason'],
                    RiskLevel.MEDIUM,
                    action_data
                )
                return validation_result
                
            # Check permissions
            permission_check = self._check_permissions(action_type, action_data)
            if not permission_check['allowed']:
                validation_result.update(permission_check)
                self._record_violation(
                    SafetyViolationType.PERMISSION_DENIED,
                    action_type,
                    permission_check['reason'],
                    RiskLevel.HIGH,
                    action_data
                )
                return validation_result
                
            # Check for dangerous patterns
            danger_check = self._check_dangerous_patterns(action_type, action_data)
            if not danger_check['allowed']:
                validation_result.update(danger_check)
                self._record_violation(
                    SafetyViolationType.DANGEROUS_ACTION,
                    action_type,
                    danger_check['reason'],
                    RiskLevel.CRITICAL,
                    action_data
                )
                return validation_result
                
            # Check resource limits
            resource_check = await self._check_resource_limits()
            if not resource_check['allowed']:
                validation_result.update(resource_check)
                self._record_violation(
                    SafetyViolationType.RESOURCE_LIMIT_EXCEEDED,
                    action_type,
                    resource_check['reason'],
                    RiskLevel.HIGH,
                    action_data
                )
                return validation_result
                
            # Assess risk level
            risk_level = self._assess_action_risk(action_type, action_data)
            validation_result['risk_level'] = risk_level
            
            # Add warnings for medium/high risk actions
            if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
                validation_result['warnings'].append(
                    f"Action has {risk_level.value} risk level - proceed with caution"
                )
                
            # Record successful validation
            if self.log_all_actions:
                self._log_action_validation(action_type, action_data, validation_result)
                
            return validation_result
            
        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            return {
                'allowed': False,
                'reason': f'Safety validation error: {str(e)}',
                'risk_level': RiskLevel.CRITICAL
            }
            
    def _check_rate_limits(self, action_type: str) -> Dict[str, Any]:
        """Check rate limits for action type."""
        # Map action types to rate limit categories
        rate_limit_map = {
            'system_command': 'actions',
            'file_operation': 'actions',
            'api_call': 'api_calls',
            'memory_operation': 'memory_writes'
        }
        
        rate_limit_category = rate_limit_map.get(action_type, 'actions')
        bucket = self.rate_limits.get(rate_limit_category)
        
        if bucket and not bucket.can_perform_action():
            return {
                'allowed': False,
                'reason': f'Rate limit exceeded for {rate_limit_category}: {bucket.max_count}/{bucket.window_seconds}s'
            }
            
        # Record the action if allowed
        if bucket:
            bucket.record_action()
            
        return {'allowed': True, 'reason': 'Rate limit check passed'}
        
    def _check_permissions(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check permissions for action."""
        # Check if action requires approval
        if action_type in self.require_approval_for:
            return {
                'allowed': False,
                'reason': f'Action {action_type} requires manual approval'
            }
            
        # Check specific permission constraints
        if action_type == 'file_operation':
            operation = action_data.get('operation', '')
            file_path = action_data.get('file_path', '')
            
            # Block operations on sensitive files
            sensitive_paths = ['/etc/', '/sys/', '/proc/', '/root/', 'C:\\Windows\\System32\\']
            for sensitive_path in sensitive_paths:
                if sensitive_path in file_path:
                    return {
                        'allowed': False,
                        'reason': f'Access denied to sensitive path: {sensitive_path}'
                    }
                    
            # Block dangerous file operations
            if operation in ['delete', 'format'] and 'important' in file_path.lower():
                return {
                    'allowed': False,
                    'reason': f'Dangerous file operation blocked: {operation} on {file_path}'
                }
                
        elif action_type == 'system_command':
            command = action_data.get('command', '')
            
            # Block commands with dangerous flags
            dangerous_flags = ['--force', '-f', '--recursive', '-r', '--all']
            for flag in dangerous_flags:
                if flag in command and any(dangerous in command for dangerous in ['rm', 'del', 'format']):
                    return {
                        'allowed': False,
                        'reason': f'Dangerous command blocked: {command}'
                    }
                    
        return {'allowed': True, 'reason': 'Permission check passed'}
        
    def _check_dangerous_patterns(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for dangerous patterns in actions."""
        if action_type == 'system_command':
            command = action_data.get('command', '').lower()
            
            for category, patterns in self.dangerous_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in command:
                        return {
                            'allowed': False,
                            'reason': f'Dangerous pattern detected ({category}): {pattern}'
                        }
                        
        elif action_type == 'file_operation':
            file_path = action_data.get('file_path', '').lower()
            operation = action_data.get('operation', '').lower()
            
            # Check for system file manipulation
            system_patterns = ['passwd', 'shadow', 'hosts', 'registry', 'boot.ini']
            for pattern in system_patterns:
                if pattern in file_path and operation in ['write', 'delete', 'modify']:
                    return {
                        'allowed': False,
                        'reason': f'Dangerous system file operation: {operation} on {pattern}'
                    }
                    
        return {'allowed': True, 'reason': 'Dangerous pattern check passed'}
        
    async def _check_resource_limits(self) -> Dict[str, Any]:
        """Check system resource limits."""
        if not self.track_resource_usage:
            return {'allowed': True, 'reason': 'Resource monitoring disabled'}
            
        try:
            # Get current resource usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            # Check CPU usage
            if cpu_percent > self.anomaly_thresholds['cpu_usage']:
                return {
                    'allowed': False,
                    'reason': f'CPU usage too high: {cpu_percent:.1f}% > {self.anomaly_thresholds["cpu_usage"]}%'
                }
                
            # Check memory usage
            memory_usage_mb = memory_info.used / 1024 / 1024
            if memory_usage_mb > self.anomaly_thresholds['memory_usage']:
                return {
                    'allowed': False,
                    'reason': f'Memory usage too high: {memory_usage_mb:.1f}MB > {self.anomaly_thresholds["memory_usage"]}MB'
                }
                
            # Check available memory
            memory_available_mb = memory_info.available / 1024 / 1024
            if memory_available_mb < 100:  # Less than 100MB available
                return {
                    'allowed': False,
                    'reason': f'Insufficient memory available: {memory_available_mb:.1f}MB'
                }
                
            return {'allowed': True, 'reason': 'Resource limits check passed'}
            
        except Exception as e:
            logger.warning(f"Resource limit check failed: {e}")
            return {'allowed': True, 'reason': 'Resource check unavailable'}
            
    def _assess_action_risk(self, action_type: str, action_data: Dict[str, Any]) -> RiskLevel:
        """Assess risk level for an action."""
        base_risk = self.action_risk_levels.get(action_type, RiskLevel.LOW)
        
        # Increase risk based on action specifics
        if action_type == 'system_command':
            command = action_data.get('command', '').lower()
            
            # High-risk commands
            high_risk_commands = ['rm', 'del', 'kill', 'shutdown', 'reboot', 'format']
            if any(cmd in command for cmd in high_risk_commands):
                return RiskLevel.HIGH
                
            # Medium-risk commands
            medium_risk_commands = ['chmod', 'chown', 'mount', 'umount', 'service']
            if any(cmd in command for cmd in medium_risk_commands):
                return RiskLevel.MEDIUM
                
        elif action_type == 'file_operation':
            operation = action_data.get('operation', '')
            file_path = action_data.get('file_path', '')
            
            # High-risk operations
            if operation in ['delete', 'format'] or '/etc/' in file_path:
                return RiskLevel.HIGH
                
            # Medium-risk operations
            if operation in ['write', 'modify'] or any(path in file_path for path in ['/usr/', '/var/', '/opt/']):
                return RiskLevel.MEDIUM
                
        return base_risk
        
    def _record_violation(self, violation_type: SafetyViolationType, action_type: str,
                         description: str, risk_level: RiskLevel, action_data: Dict[str, Any]):
        """Record a safety violation."""
        violation = SafetyViolation(
            violation_type=violation_type,
            action_type=action_type,
            description=description,
            risk_level=risk_level,
            action_data=action_data
        )
        
        self.violations.append(violation)
        
        # Limit violation history
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]
            
        logger.warning(f"Safety violation recorded: {violation_type.value} - {description}")
        
        # Alert on critical violations
        if risk_level == RiskLevel.CRITICAL and self.alert_on_anomalies:
            self._send_alert(violation)
            
    def _send_alert(self, violation: SafetyViolation):
        """Send alert for critical safety violations."""
        alert_message = (
            f"CRITICAL SAFETY VIOLATION: {violation.violation_type.value}\n"
            f"Action: {violation.action_type}\n"
            f"Description: {violation.description}\n"
            f"Time: {violation.timestamp.isoformat()}"
        )
        
        logger.critical(alert_message)
        
        # Here you could integrate with external alerting systems
        # (email, Slack, PagerDuty, etc.)
        
    def _log_action_validation(self, action_type: str, action_data: Dict[str, Any], 
                              validation_result: Dict[str, Any]):
        """Log action validation for audit trail."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'allowed': validation_result['allowed'],
            'risk_level': validation_result['risk_level'].value,
            'reason': validation_result['reason']
        }
        
        logger.info(f"Action validation: {action_type} - {validation_result['allowed']} - {validation_result['reason']}")
        
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status and statistics."""
        recent_violations = [v for v in self.violations 
                           if v.timestamp > datetime.now() - timedelta(hours=24)]
        
        violation_counts = defaultdict(int)
        for violation in recent_violations:
            violation_counts[violation.violation_type.value] += 1
            
        # Rate limit status
        rate_limit_status = {}
        for category, bucket in self.rate_limits.items():
            rate_limit_status[category] = {
                'max_count': bucket.max_count,
                'window_seconds': bucket.window_seconds,
                'current_count': len(bucket.actions),
                'can_perform': bucket.can_perform_action()
            }
            
        return {
            'enabled': self.enabled,
            'total_violations': len(self.violations),
            'recent_violations_24h': len(recent_violations),
            'violation_types': dict(violation_counts),
            'rate_limit_status': rate_limit_status,
            'resource_monitoring': self.track_resource_usage,
            'anomaly_detection': self.alert_on_anomalies,
            'protected_actions': list(self.require_approval_for)
        }
        
    def get_recent_violations(self, hours: int = 24) -> List[SafetyViolation]:
        """Get recent safety violations."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [v for v in self.violations if v.timestamp > cutoff]
        
    def resolve_violation(self, violation_index: int, resolution_note: str = ""):
        """Mark a violation as resolved."""
        if 0 <= violation_index < len(self.violations):
            self.violations[violation_index].resolved = True
            logger.info(f"Violation {violation_index} resolved: {resolution_note}")
            
    def update_rate_limits(self, new_limits: Dict[str, Dict[str, int]]):
        """Update rate limits configuration."""
        for category, limits in new_limits.items():
            if category in self.rate_limits:
                bucket = self.rate_limits[category]
                bucket.max_count = limits.get('max_count', bucket.max_count)
                bucket.window_seconds = limits.get('window_seconds', bucket.window_seconds)
                
        logger.info(f"Rate limits updated: {new_limits}")
        
    def update_anomaly_thresholds(self, new_thresholds: Dict[str, float]):
        """Update anomaly detection thresholds."""
        self.anomaly_thresholds.update(new_thresholds)
        logger.info(f"Anomaly thresholds updated: {new_thresholds}")
        
    def add_dangerous_pattern(self, category: str, pattern: str):
        """Add a new dangerous pattern to detect."""
        if category not in self.dangerous_patterns:
            self.dangerous_patterns[category] = []
            
        if pattern not in self.dangerous_patterns[category]:
            self.dangerous_patterns[category].append(pattern)
            logger.info(f"Added dangerous pattern: {category} - {pattern}")
            
    def remove_dangerous_pattern(self, category: str, pattern: str):
        """Remove a dangerous pattern."""
        if category in self.dangerous_patterns and pattern in self.dangerous_patterns[category]:
            self.dangerous_patterns[category].remove(pattern)
            logger.info(f"Removed dangerous pattern: {category} - {pattern}")
            
    async def monitor_resources(self) -> Dict[str, Any]:
        """Monitor current resource usage."""
        if not self.track_resource_usage:
            return {'monitoring_disabled': True}
            
        try:
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            current_metrics = {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_mb': memory_info.used / 1024 / 1024,
                'memory_available_mb': memory_info.available / 1024 / 1024,
                'memory_percent': memory_info.percent,
                'disk_usage_percent': disk_info.percent,
                'disk_free_gb': disk_info.free / 1024 / 1024 / 1024
            }
            
            # Check for anomalies
            anomalies = []
            if cpu_percent > self.anomaly_thresholds['cpu_usage']:
                anomalies.append(f"High CPU usage: {cpu_percent:.1f}%")
                
            memory_mb = memory_info.used / 1024 / 1024
            if memory_mb > self.anomaly_thresholds['memory_usage']:
                anomalies.append(f"High memory usage: {memory_mb:.1f}MB")
                
            if disk_info.percent > self.anomaly_thresholds['disk_usage']:
                anomalies.append(f"High disk usage: {disk_info.percent:.1f}%")
                
            current_metrics['anomalies'] = anomalies
            current_metrics['anomaly_detected'] = len(anomalies) > 0
            
            # Record anomalies as violations if alerting is enabled
            if anomalies and self.alert_on_anomalies:
                for anomaly in anomalies:
                    self._record_violation(
                        SafetyViolationType.ANOMALY_DETECTED,
                        'resource_monitoring',
                        anomaly,
                        RiskLevel.MEDIUM,
                        current_metrics
                    )
                    
            return current_metrics
            
        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
            return {'error': str(e)} 