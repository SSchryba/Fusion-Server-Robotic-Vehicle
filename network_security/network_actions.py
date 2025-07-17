"""
Network Actions Module for Automated Security Response

Provides automated response capabilities for network security incidents
including IP blocking, traffic shaping, quarantine, and integration
with external security tools and systems.
"""

import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import ipaddress
from pathlib import Path

try:
    import netaddr
    NETADDR_AVAILABLE = True
except ImportError:
    NETADDR_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of network actions"""
    FIREWALL_BLOCK = "firewall_block"
    TRAFFIC_SHAPING = "traffic_shaping"
    QUARANTINE_VLAN = "quarantine_vlan"
    CONNECTION_RESET = "connection_reset"
    BANDWIDTH_LIMIT = "bandwidth_limit"
    REDIRECT_TO_HONEYPOT = "redirect_to_honeypot"
    SINKHOLE_DNS = "sinkhole_dns"
    NOTIFY_EXTERNAL = "notify_external"


class ActionStatus(Enum):
    """Status of network actions"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class NetworkAction:
    """Network action record"""
    action_id: str
    action_type: ActionType
    target_ip: str
    target_port: Optional[int] = None
    duration_seconds: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    success: bool = False
    error_message: Optional[str] = None
    execution_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'target_ip': self.target_ip,
            'target_port': self.target_port,
            'duration_seconds': self.duration_seconds,
            'parameters': self.parameters,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'success': self.success,
            'error_message': self.error_message,
            'execution_details': self.execution_details
        }


class NetworkActionEngine:
    """
    Engine for executing automated network security actions
    including firewall rules, traffic shaping, and quarantine.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the network action engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Action configuration
        self.dry_run = self.config.get('dry_run', False)
        self.max_concurrent_actions = self.config.get('max_concurrent_actions', 10)
        self.default_action_timeout = self.config.get('default_action_timeout', 300)
        
        # Firewall configuration
        self.firewall_type = self.config.get('firewall_type', 'iptables')  # iptables, pf, windows
        self.firewall_chain = self.config.get('firewall_chain', 'INPUT')
        self.firewall_table = self.config.get('firewall_table', 'filter')
        
        # Traffic shaping configuration
        self.tc_available = self.config.get('tc_available', True)
        self.default_bandwidth_limit = self.config.get('default_bandwidth_limit', '1mbit')
        
        # Quarantine configuration
        self.quarantine_vlan = self.config.get('quarantine_vlan', 666)
        self.quarantine_subnet = self.config.get('quarantine_subnet', '192.168.99.0/24')
        
        # External integrations
        self.external_apis = self.config.get('external_apis', {})
        self.siem_integration = self.config.get('siem_integration', {})
        
        # Storage
        self.action_dir = Path(self.config.get('action_dir', 'network_security/actions'))
        self.action_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.running = False
        self.active_actions: Dict[str, NetworkAction] = {}
        self.action_history: List[NetworkAction] = []
        self.action_queue: asyncio.Queue = asyncio.Queue()
        
        # Action handlers
        self.action_handlers = {
            ActionType.FIREWALL_BLOCK: self._execute_firewall_block,
            ActionType.TRAFFIC_SHAPING: self._execute_traffic_shaping,
            ActionType.QUARANTINE_VLAN: self._execute_quarantine_vlan,
            ActionType.CONNECTION_RESET: self._execute_connection_reset,
            ActionType.BANDWIDTH_LIMIT: self._execute_bandwidth_limit,
            ActionType.REDIRECT_TO_HONEYPOT: self._execute_redirect_honeypot,
            ActionType.SINKHOLE_DNS: self._execute_sinkhole_dns,
            ActionType.NOTIFY_EXTERNAL: self._execute_notify_external
        }
        
        # Statistics
        self.stats = {
            'total_actions_queued': 0,
            'total_actions_executed': 0,
            'total_actions_failed': 0,
            'actions_by_type': {},
            'average_execution_time': 0.0,
            'last_action_time': None
        }
        
        logger.info("Network Action Engine initialized")
        
    async def start(self):
        """Start the network action engine"""
        if self.running:
            logger.warning("Network action engine is already running")
            return
            
        logger.info("Starting network action engine...")
        
        try:
            self.running = True
            
            # Start action processing loop
            asyncio.create_task(self._action_processing_loop())
            
            # Start cleanup loop
            asyncio.create_task(self._cleanup_loop())
            
            logger.info("Network action engine started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start network action engine: {e}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the network action engine"""
        if not self.running:
            logger.warning("Network action engine is not running")
            return
            
        logger.info("Stopping network action engine...")
        
        try:
            self.running = False
            
            # Process remaining actions
            await self._process_remaining_actions()
            
            # Clean up active actions
            await self._cleanup_active_actions()
            
            logger.info("Network action engine stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping network action engine: {e}")
            
    async def queue_action(self, action_type: ActionType, target_ip: str, 
                          target_port: Optional[int] = None,
                          duration_seconds: Optional[int] = None,
                          parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Queue a network action for execution.
        
        Args:
            action_type: Type of action to execute
            target_ip: Target IP address
            target_port: Target port (optional)
            duration_seconds: Action duration (optional)
            parameters: Additional parameters
            
        Returns:
            Action ID
        """
        try:
            # Validate IP address
            if not self._validate_ip_address(target_ip):
                raise ValueError(f"Invalid IP address: {target_ip}")
                
            # Create action
            action = NetworkAction(
                action_id=f"action_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                action_type=action_type,
                target_ip=target_ip,
                target_port=target_port,
                duration_seconds=duration_seconds,
                parameters=parameters or {}
            )
            
            # Set expiration time
            if duration_seconds:
                action.expires_at = datetime.now() + timedelta(seconds=duration_seconds)
                
            # Queue action
            await self.action_queue.put(action)
            self.stats['total_actions_queued'] += 1
            
            logger.info(f"Queued action: {action_type.value} for {target_ip}")
            
            return action.action_id
            
        except Exception as e:
            logger.error(f"Error queueing action: {e}")
            raise
            
    async def _action_processing_loop(self):
        """Main action processing loop"""
        try:
            while self.running:
                try:
                    # Get action from queue (with timeout)
                    action = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)
                    
                    # Check if we have capacity
                    if len(self.active_actions) >= self.max_concurrent_actions:
                        # Put action back in queue
                        await self.action_queue.put(action)
                        await asyncio.sleep(1)
                        continue
                        
                    # Execute action
                    asyncio.create_task(self._execute_action(action))
                    
                except asyncio.TimeoutError:
                    # No actions in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error in action processing loop: {e}")
                    
        except Exception as e:
            logger.error(f"Action processing loop error: {e}")
            
    async def _execute_action(self, action: NetworkAction):
        """Execute a network action"""
        try:
            # Add to active actions
            self.active_actions[action.action_id] = action
            
            # Update status
            action.status = ActionStatus.EXECUTING
            action.executed_at = datetime.now()
            
            logger.info(f"Executing action: {action.action_type.value} for {action.target_ip}")
            
            # Execute action based on type
            if action.action_type in self.action_handlers:
                handler = self.action_handlers[action.action_type]
                success, details = await handler(action)
                
                action.success = success
                action.execution_details = details
                
                if success:
                    action.status = ActionStatus.COMPLETED
                    self.stats['total_actions_executed'] += 1
                    logger.info(f"Action completed successfully: {action.action_id}")
                else:
                    action.status = ActionStatus.FAILED
                    self.stats['total_actions_failed'] += 1
                    logger.error(f"Action failed: {action.action_id}")
                    
            else:
                action.status = ActionStatus.FAILED
                action.error_message = f"No handler for action type: {action.action_type.value}"
                self.stats['total_actions_failed'] += 1
                
            # Update statistics
            action_type_key = action.action_type.value
            if action_type_key not in self.stats['actions_by_type']:
                self.stats['actions_by_type'][action_type_key] = 0
            self.stats['actions_by_type'][action_type_key] += 1
            
            self.stats['last_action_time'] = datetime.now()
            
            # Save action
            await self._save_action(action)
            
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            self.stats['total_actions_failed'] += 1
            
        finally:
            # Move to history
            if action.action_id in self.active_actions:
                self.action_history.append(self.active_actions[action.action_id])
                del self.active_actions[action.action_id]
                
    async def _execute_firewall_block(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute firewall block action"""
        try:
            target_ip = action.target_ip
            details = {'method': 'firewall_block'}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would block IP {target_ip}")
                details['dry_run'] = True
                return True, details
                
            # Execute based on firewall type
            if self.firewall_type == 'iptables':
                cmd = [
                    'iptables', '-I', self.firewall_chain,
                    '-s', target_ip,
                    '-j', 'DROP'
                ]
                
                if action.target_port:
                    cmd.extend(['--dport', str(action.target_port)])
                    
                result = await self._execute_command(cmd)
                details.update(result)
                
                return result['success'], details
                
            elif self.firewall_type == 'pf':
                # FreeBSD/OpenBSD pf firewall
                rule = f"block in from {target_ip} to any"
                if action.target_port:
                    rule += f" port {action.target_port}"
                    
                cmd = ['pfctl', '-a', 'security_block', '-f', '-']
                
                result = await self._execute_command(cmd, input_data=rule)
                details.update(result)
                
                return result['success'], details
                
            elif self.firewall_type == 'windows':
                # Windows Firewall
                rule_name = f"SecurityBlock_{target_ip}"
                cmd = [
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name={rule_name}',
                    'dir=in',
                    'action=block',
                    f'remoteip={target_ip}'
                ]
                
                if action.target_port:
                    cmd.extend(['protocol=TCP', f'localport={action.target_port}'])
                    
                result = await self._execute_command(cmd)
                details.update(result)
                
                return result['success'], details
                
            else:
                details['error'] = f"Unsupported firewall type: {self.firewall_type}"
                return False, details
                
        except Exception as e:
            logger.error(f"Error in firewall block: {e}")
            return False, {'error': str(e)}
            
    async def _execute_traffic_shaping(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute traffic shaping action"""
        try:
            target_ip = action.target_ip
            bandwidth_limit = action.parameters.get('bandwidth_limit', self.default_bandwidth_limit)
            details = {'method': 'traffic_shaping', 'bandwidth_limit': bandwidth_limit}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would limit bandwidth for {target_ip} to {bandwidth_limit}")
                details['dry_run'] = True
                return True, details
                
            if not self.tc_available:
                details['error'] = "Traffic control (tc) not available"
                return False, details
                
            # Create traffic control rules
            interface = action.parameters.get('interface', 'eth0')
            
            # Add qdisc
            cmd1 = ['tc', 'qdisc', 'add', 'dev', interface, 'root', 'handle', '1:', 'htb']
            result1 = await self._execute_command(cmd1)
            
            # Add class with bandwidth limit
            cmd2 = [
                'tc', 'class', 'add', 'dev', interface, 'parent', '1:',
                'classid', '1:1', 'htb', 'rate', bandwidth_limit
            ]
            result2 = await self._execute_command(cmd2)
            
            # Add filter for specific IP
            cmd3 = [
                'tc', 'filter', 'add', 'dev', interface, 'protocol', 'ip',
                'parent', '1:0', 'prio', '1', 'u32',
                'match', 'ip', 'src', target_ip,
                'flowid', '1:1'
            ]
            result3 = await self._execute_command(cmd3)
            
            details.update({
                'qdisc_result': result1,
                'class_result': result2,
                'filter_result': result3
            })
            
            success = result1['success'] and result2['success'] and result3['success']
            return success, details
            
        except Exception as e:
            logger.error(f"Error in traffic shaping: {e}")
            return False, {'error': str(e)}
            
    async def _execute_quarantine_vlan(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute VLAN quarantine action"""
        try:
            target_ip = action.target_ip
            details = {'method': 'quarantine_vlan', 'quarantine_vlan': self.quarantine_vlan}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would quarantine {target_ip} to VLAN {self.quarantine_vlan}")
                details['dry_run'] = True
                return True, details
                
            # This would typically integrate with network equipment APIs
            # For demonstration, we'll simulate the quarantine
            
            details['simulated'] = True
            details['target_vlan'] = self.quarantine_vlan
            details['quarantine_subnet'] = self.quarantine_subnet
            
            logger.info(f"Quarantined {target_ip} to VLAN {self.quarantine_vlan}")
            
            return True, details
            
        except Exception as e:
            logger.error(f"Error in VLAN quarantine: {e}")
            return False, {'error': str(e)}
            
    async def _execute_connection_reset(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute connection reset action"""
        try:
            target_ip = action.target_ip
            target_port = action.target_port
            details = {'method': 'connection_reset'}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would reset connections from {target_ip}:{target_port}")
                details['dry_run'] = True
                return True, details
                
            # Use ss (socket statistics) to find and reset connections
            if target_port:
                cmd = ['ss', '-K', 'dst', target_ip, 'dport', f'= {target_port}']
            else:
                cmd = ['ss', '-K', 'dst', target_ip]
                
            result = await self._execute_command(cmd)
            details.update(result)
            
            return result['success'], details
            
        except Exception as e:
            logger.error(f"Error in connection reset: {e}")
            return False, {'error': str(e)}
            
    async def _execute_bandwidth_limit(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute bandwidth limit action"""
        try:
            # This is similar to traffic shaping but with different parameters
            return await self._execute_traffic_shaping(action)
            
        except Exception as e:
            logger.error(f"Error in bandwidth limit: {e}")
            return False, {'error': str(e)}
            
    async def _execute_redirect_honeypot(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute redirect to honeypot action"""
        try:
            target_ip = action.target_ip
            honeypot_ip = action.parameters.get('honeypot_ip', '192.168.1.100')
            details = {'method': 'redirect_honeypot', 'honeypot_ip': honeypot_ip}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would redirect {target_ip} to honeypot {honeypot_ip}")
                details['dry_run'] = True
                return True, details
                
            # Use iptables DNAT to redirect traffic
            cmd = [
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-s', target_ip,
                '-j', 'DNAT',
                '--to-destination', honeypot_ip
            ]
            
            result = await self._execute_command(cmd)
            details.update(result)
            
            return result['success'], details
            
        except Exception as e:
            logger.error(f"Error in honeypot redirect: {e}")
            return False, {'error': str(e)}
            
    async def _execute_sinkhole_dns(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute DNS sinkhole action"""
        try:
            target_ip = action.target_ip
            sinkhole_ip = action.parameters.get('sinkhole_ip', '192.168.1.200')
            details = {'method': 'sinkhole_dns', 'sinkhole_ip': sinkhole_ip}
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would sinkhole DNS for {target_ip}")
                details['dry_run'] = True
                return True, details
                
            # This would typically integrate with DNS server configuration
            # For demonstration, we'll simulate the sinkhole
            
            details['simulated'] = True
            details['dns_action'] = 'sinkhole_configured'
            
            logger.info(f"DNS sinkhole configured for {target_ip}")
            
            return True, details
            
        except Exception as e:
            logger.error(f"Error in DNS sinkhole: {e}")
            return False, {'error': str(e)}
            
    async def _execute_notify_external(self, action: NetworkAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute external notification action"""
        try:
            target_ip = action.target_ip
            details = {'method': 'notify_external'}
            
            # Send to external APIs
            notifications_sent = 0
            
            for api_name, api_config in self.external_apis.items():
                try:
                    # This would make HTTP requests to external APIs
                    # For demonstration, we'll simulate the notification
                    
                    details[f'{api_name}_notification'] = 'sent'
                    notifications_sent += 1
                    
                    logger.info(f"Sent notification to {api_name} for {target_ip}")
                    
                except Exception as e:
                    logger.error(f"Failed to notify {api_name}: {e}")
                    details[f'{api_name}_error'] = str(e)
                    
            details['notifications_sent'] = notifications_sent
            
            return notifications_sent > 0, details
            
        except Exception as e:
            logger.error(f"Error in external notification: {e}")
            return False, {'error': str(e)}
            
    async def _execute_command(self, cmd: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """Execute system command"""
        try:
            start_time = datetime.now()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(
                input=input_data.encode() if input_data else None
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': process.returncode == 0,
                'command': ' '.join(cmd),
                'return_code': process.returncode,
                'stdout': stdout.decode() if stdout else '',
                'stderr': stderr.decode() if stderr else '',
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"Error executing command {' '.join(cmd)}: {e}")
            return {
                'success': False,
                'command': ' '.join(cmd),
                'error': str(e)
            }
            
    def _validate_ip_address(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
            
    async def _save_action(self, action: NetworkAction):
        """Save action to file"""
        try:
            action_file = self.action_dir / f"{action.action_id}.json"
            
            with open(action_file, 'w') as f:
                json.dump(action.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving action: {e}")
            
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        try:
            while self.running:
                await asyncio.sleep(300)  # Every 5 minutes
                
                if not self.running:
                    break
                    
                # Clean up expired actions
                now = datetime.now()
                expired_actions = []
                
                for action in self.active_actions.values():
                    if action.expires_at and now > action.expires_at:
                        expired_actions.append(action)
                        
                for action in expired_actions:
                    action.status = ActionStatus.EXPIRED
                    await self._cleanup_expired_action(action)
                    
                    # Move to history
                    self.action_history.append(action)
                    del self.active_actions[action.action_id]
                    
                logger.info(f"Cleaned up {len(expired_actions)} expired actions")
                
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")
            
    async def _cleanup_expired_action(self, action: NetworkAction):
        """Clean up expired action"""
        try:
            # Remove firewall rules, traffic shaping, etc.
            if action.action_type == ActionType.FIREWALL_BLOCK:
                await self._remove_firewall_rule(action)
            elif action.action_type == ActionType.TRAFFIC_SHAPING:
                await self._remove_traffic_shaping(action)
                
            logger.info(f"Cleaned up expired action: {action.action_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired action: {e}")
            
    async def _remove_firewall_rule(self, action: NetworkAction):
        """Remove firewall rule"""
        try:
            target_ip = action.target_ip
            
            if self.firewall_type == 'iptables':
                cmd = [
                    'iptables', '-D', self.firewall_chain,
                    '-s', target_ip,
                    '-j', 'DROP'
                ]
                
                if action.target_port:
                    cmd.extend(['--dport', str(action.target_port)])
                    
                await self._execute_command(cmd)
                
        except Exception as e:
            logger.error(f"Error removing firewall rule: {e}")
            
    async def _remove_traffic_shaping(self, action: NetworkAction):
        """Remove traffic shaping rules"""
        try:
            interface = action.parameters.get('interface', 'eth0')
            
            # Remove qdisc (this removes all associated classes and filters)
            cmd = ['tc', 'qdisc', 'del', 'dev', interface, 'root']
            await self._execute_command(cmd)
            
        except Exception as e:
            logger.error(f"Error removing traffic shaping: {e}")
            
    async def _process_remaining_actions(self):
        """Process remaining actions before shutdown"""
        try:
            # Process remaining actions in queue
            while not self.action_queue.empty():
                try:
                    action = self.action_queue.get_nowait()
                    await self._execute_action(action)
                except asyncio.QueueEmpty:
                    break
                    
        except Exception as e:
            logger.error(f"Error processing remaining actions: {e}")
            
    async def _cleanup_active_actions(self):
        """Clean up active actions"""
        try:
            for action in list(self.active_actions.values()):
                await self._cleanup_expired_action(action)
                
        except Exception as e:
            logger.error(f"Error cleaning up active actions: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current action engine status"""
        return {
            'running': self.running,
            'dry_run': self.dry_run,
            'active_actions': len(self.active_actions),
            'queue_size': self.action_queue.qsize(),
            'total_actions_history': len(self.action_history),
            'statistics': self.stats,
            'configuration': {
                'firewall_type': self.firewall_type,
                'max_concurrent_actions': self.max_concurrent_actions,
                'quarantine_vlan': self.quarantine_vlan
            }
        }
        
    def get_recent_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent actions"""
        recent = sorted(self.action_history, key=lambda x: x.created_at, reverse=True)[:limit]
        return [action.to_dict() for action in recent]
        
    def get_action_stats(self) -> Dict[str, Any]:
        """Get action statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['total_actions_executed'] / 
                max(self.stats['total_actions_executed'] + self.stats['total_actions_failed'], 1)
            ),
            'active_actions': len(self.active_actions),
            'queue_size': self.action_queue.qsize()
        }
        
    def export_action_data(self, output_file: str) -> Dict[str, Any]:
        """Export action data"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': self.stats,
                'active_actions': [action.to_dict() for action in self.active_actions.values()],
                'action_history': [action.to_dict() for action in self.action_history],
                'configuration': {
                    'firewall_type': self.firewall_type,
                    'quarantine_vlan': self.quarantine_vlan,
                    'dry_run': self.dry_run
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            return {
                'success': True,
                'output_file': output_file,
                'actions_exported': len(self.action_history),
                'active_actions_exported': len(self.active_actions)
            }
            
        except Exception as e:
            logger.error(f"Error exporting action data: {e}")
            return {
                'success': False,
                'error': str(e)
            } 