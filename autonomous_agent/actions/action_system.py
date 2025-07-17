"""
Action System for Autonomous AI Agent Framework

Provides sandboxed execution of OS commands, API calls, file operations,
and other actions with proper safety checks and monitoring.
"""

import os
import asyncio
import subprocess
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import tempfile
import json
import aiohttp
import shutil
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)


class ActionSystem:
    """
    Secure action execution system with sandboxing and safety checks.
    """
    
    def __init__(self, config_manager, safety_manager):
        """
        Initialize the action system.
        
        Args:
            config_manager: Configuration manager instance
            safety_manager: Safety manager for validation
        """
        self.config_manager = config_manager
        self.safety_manager = safety_manager
        
        # Action configuration
        self.action_config = config_manager.get_section('actions')
        self.enabled = self.action_config.get('enabled', True)
        self.sandbox_mode = self.action_config.get('sandbox_mode', True)
        self.max_action_time = self.action_config.get('max_action_time', 60)
        
        # Allowed and restricted operations
        self.allowed_commands = set(self.action_config.get('allowed_commands', [
            'ls', 'pwd', 'cat', 'echo', 'curl', 'python', 'pip'
        ]))
        self.restricted_paths = set(self.action_config.get('restricted_paths', [
            '/etc', '/sys', '/proc', '/root'
        ]))
        
        # API configuration
        self.api_config = self.action_config.get('api_endpoints', {})
        self.max_requests_per_minute = self.api_config.get('max_requests_per_minute', 60)
        self.api_timeout = self.api_config.get('timeout_seconds', 30)
        
        # Working directory setup
        self.sandbox_dir = Path(tempfile.mkdtemp(prefix='agent_sandbox_'))
        self.sandbox_dir.chmod(0o755)
        
        # Action tracking
        self.action_history: List[Dict[str, Any]] = []
        self.active_processes: Dict[str, subprocess.Popen] = {}
        
        logger.info(f"Action System initialized - Sandbox: {self.sandbox_mode}, Dir: {self.sandbox_dir}")
        
    async def execute_command(self, command: str, 
                             working_directory: Optional[str] = None,
                             timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a system command with safety checks.
        
        Args:
            command: Command to execute
            working_directory: Working directory for command
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        if not self.enabled:
            return {'success': False, 'error': 'Action system is disabled'}
            
        start_time = datetime.now()
        
        try:
            # Safety validation
            safety_check = await self.safety_manager.validate_action(
                'system_command', 
                {'command': command, 'working_directory': working_directory}
            )
            
            if not safety_check.get('allowed', False):
                return {
                    'success': False,
                    'error': f"Command blocked by safety manager: {safety_check.get('reason', 'Unknown')}"
                }
                
            # Validate command
            validation_result = self._validate_command(command)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Command validation failed: {validation_result['reason']}"
                }
                
            # Setup execution environment
            exec_dir = self._get_execution_directory(working_directory)
            exec_timeout = timeout or self.max_action_time
            
            # Execute command
            result = await self._execute_subprocess(command, exec_dir, exec_timeout)
            
            # Log action
            self._log_action('system_command', {
                'command': command,
                'working_directory': str(exec_dir),
                'success': result['success'],
                'execution_time': (datetime.now() - start_time).total_seconds()
            })
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': f"Command execution failed: {str(e)}",
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
            
            self._log_action('system_command', {
                'command': command,
                'error': str(e),
                'success': False
            })
            
            return error_result
            
    def _validate_command(self, command: str) -> Dict[str, Any]:
        """Validate command against allowed operations."""
        command_parts = command.strip().split()
        if not command_parts:
            return {'valid': False, 'reason': 'Empty command'}
            
        base_command = command_parts[0]
        
        # Check if command is in allowed list
        if base_command not in self.allowed_commands:
            return {'valid': False, 'reason': f'Command not allowed: {base_command}'}
            
        # Check for dangerous patterns
        dangerous_patterns = [
            'rm -rf', 'chmod 777', 'sudo', 'su -', '>/dev/', 'mkfs',
            'dd if=', 'format', 'fdisk', 'kill -9', 'killall'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return {'valid': False, 'reason': f'Dangerous pattern detected: {pattern}'}
                
        # Check for path restrictions
        for restricted_path in self.restricted_paths:
            if restricted_path in command:
                return {'valid': False, 'reason': f'Restricted path access: {restricted_path}'}
                
        return {'valid': True, 'reason': 'Command validated'}
        
    def _get_execution_directory(self, working_directory: Optional[str]) -> Path:
        """Get safe execution directory."""
        if working_directory and not self.sandbox_mode:
            # Validate the directory is safe
            work_path = Path(working_directory).resolve()
            
            # Check if it's within allowed paths
            for restricted in self.restricted_paths:
                if str(work_path).startswith(restricted):
                    logger.warning(f"Restricted path access attempted: {work_path}")
                    return self.sandbox_dir
                    
            if work_path.exists() and work_path.is_dir():
                return work_path
                
        return self.sandbox_dir
        
    async def _execute_subprocess(self, command: str, working_dir: Path, 
                                 timeout: int) -> Dict[str, Any]:
        """Execute subprocess with proper error handling."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024  # 1MB limit for output
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    'success': process.returncode == 0,
                    'output': stdout.decode('utf-8', errors='replace'),
                    'error': stderr.decode('utf-8', errors='replace'),
                    'exit_code': process.returncode
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'success': False,
                    'error': f'Command timed out after {timeout} seconds',
                    'exit_code': -1
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to execute command: {str(e)}',
                'exit_code': -1
            }
            
    async def execute_file_operation(self, operation: str, file_path: str,
                                    content: Optional[str] = None,
                                    parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute file operations safely.
        
        Args:
            operation: Type of operation (read, write, copy, delete, etc.)
            file_path: Target file path
            content: Content for write operations
            parameters: Additional parameters
            
        Returns:
            Dictionary with operation results
        """
        if not self.enabled:
            return {'success': False, 'error': 'Action system is disabled'}
            
        start_time = datetime.now()
        
        try:
            # Safety validation
            safety_check = await self.safety_manager.validate_action(
                'file_operation',
                {'operation': operation, 'file_path': file_path}
            )
            
            if not safety_check.get('allowed', False):
                return {
                    'success': False,
                    'error': f"File operation blocked: {safety_check.get('reason', 'Unknown')}"
                }
                
            # Validate file path
            file_path_obj = self._validate_file_path(file_path)
            if not file_path_obj:
                return {'success': False, 'error': 'Invalid or restricted file path'}
                
            # Execute operation
            result = await self._execute_file_operation(operation, file_path_obj, content, parameters)
            
            # Log action
            self._log_action('file_operation', {
                'operation': operation,
                'file_path': str(file_path_obj),
                'success': result['success'],
                'execution_time': (datetime.now() - start_time).total_seconds()
            })
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': f"File operation failed: {str(e)}",
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
            
            self._log_action('file_operation', {
                'operation': operation,
                'file_path': file_path,
                'error': str(e),
                'success': False
            })
            
            return error_result
            
    def _validate_file_path(self, file_path: str) -> Optional[Path]:
        """Validate and resolve file path safely."""
        try:
            path_obj = Path(file_path)
            
            # If in sandbox mode, ensure path is within sandbox
            if self.sandbox_mode:
                # Make path relative to sandbox
                if path_obj.is_absolute():
                    # Strip leading slash and make relative to sandbox
                    relative_path = str(path_obj).lstrip('/')
                    path_obj = self.sandbox_dir / relative_path
                else:
                    path_obj = self.sandbox_dir / path_obj
                    
            # Resolve path and check restrictions
            resolved_path = path_obj.resolve()
            
            # Check against restricted paths
            for restricted in self.restricted_paths:
                if str(resolved_path).startswith(restricted):
                    logger.warning(f"Attempted access to restricted path: {resolved_path}")
                    return None
                    
            return resolved_path
            
        except Exception as e:
            logger.warning(f"File path validation failed: {e}")
            return None
            
    async def _execute_file_operation(self, operation: str, file_path: Path,
                                     content: Optional[str] = None,
                                     parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute specific file operation."""
        try:
            if operation == 'read':
                if not file_path.exists():
                    return {'success': False, 'error': 'File does not exist'}
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    
                return {
                    'success': True,
                    'content': file_content,
                    'size': len(file_content),
                    'file_path': str(file_path)
                }
                
            elif operation == 'write':
                if content is None:
                    return {'success': False, 'error': 'No content provided for write operation'}
                    
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                return {
                    'success': True,
                    'bytes_written': len(content.encode('utf-8')),
                    'file_path': str(file_path)
                }
                
            elif operation == 'append':
                if content is None:
                    return {'success': False, 'error': 'No content provided for append operation'}
                    
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                    
                return {
                    'success': True,
                    'bytes_appended': len(content.encode('utf-8')),
                    'file_path': str(file_path)
                }
                
            elif operation == 'copy':
                source_path = parameters.get('source_path') if parameters else None
                if not source_path:
                    return {'success': False, 'error': 'Source path required for copy operation'}
                    
                source_path_obj = self._validate_file_path(source_path)
                if not source_path_obj or not source_path_obj.exists():
                    return {'success': False, 'error': 'Invalid or non-existent source path'}
                    
                file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path_obj, file_path)
                
                return {
                    'success': True,
                    'source_path': str(source_path_obj),
                    'destination_path': str(file_path)
                }
                
            elif operation == 'delete':
                if not file_path.exists():
                    return {'success': False, 'error': 'File does not exist'}
                    
                file_path.unlink()
                
                return {
                    'success': True,
                    'deleted_path': str(file_path)
                }
                
            elif operation == 'list':
                if not file_path.exists():
                    return {'success': False, 'error': 'Directory does not exist'}
                    
                if not file_path.is_dir():
                    return {'success': False, 'error': 'Path is not a directory'}
                    
                files = []
                for item in file_path.iterdir():
                    files.append({
                        'name': item.name,
                        'is_file': item.is_file(),
                        'is_dir': item.is_dir(),
                        'size': item.stat().st_size if item.is_file() else 0,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                    
                return {
                    'success': True,
                    'directory': str(file_path),
                    'files': files,
                    'count': len(files)
                }
                
            else:
                return {'success': False, 'error': f'Unsupported file operation: {operation}'}
                
        except Exception as e:
            return {'success': False, 'error': f'File operation failed: {str(e)}'}
            
    async def execute_api_call(self, method: str, url: str,
                              headers: Optional[Dict[str, str]] = None,
                              data: Optional[Union[Dict, str]] = None,
                              timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute API call with safety checks.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Target URL
            headers: HTTP headers
            data: Request data
            timeout: Request timeout
            
        Returns:
            Dictionary with API response
        """
        if not self.enabled:
            return {'success': False, 'error': 'Action system is disabled'}
            
        start_time = datetime.now()
        
        try:
            # Safety validation
            safety_check = await self.safety_manager.validate_action(
                'api_call',
                {'method': method, 'url': url, 'data': data}
            )
            
            if not safety_check.get('allowed', False):
                return {
                    'success': False,
                    'error': f"API call blocked: {safety_check.get('reason', 'Unknown')}"
                }
                
            # Validate URL
            if not self._validate_url(url):
                return {'success': False, 'error': 'Invalid or restricted URL'}
                
            # Execute API call
            result = await self._execute_http_request(method, url, headers, data, timeout)
            
            # Log action
            self._log_action('api_call', {
                'method': method,
                'url': url,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'execution_time': (datetime.now() - start_time).total_seconds()
            })
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': f"API call failed: {str(e)}",
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
            
            self._log_action('api_call', {
                'method': method,
                'url': url,
                'error': str(e),
                'success': False
            })
            
            return error_result
            
    def _validate_url(self, url: str) -> bool:
        """Validate URL for security."""
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Block internal/local addresses
        blocked_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            '192.168.', '10.', '172.16.', '172.17.', '172.18.',
            '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
            '172.29.', '172.30.', '172.31.'
        ]
        
        url_lower = url.lower()
        for blocked in blocked_hosts:
            if blocked in url_lower:
                if 'localhost:8000' not in url_lower:  # Allow local fusion server
                    return False
                    
        return True
        
    async def _execute_http_request(self, method: str, url: str,
                                   headers: Optional[Dict[str, str]] = None,
                                   data: Optional[Union[Dict, str]] = None,
                                   timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute HTTP request."""
        request_timeout = timeout or self.api_timeout
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=request_timeout)) as session:
                # Prepare request parameters
                kwargs = {}
                if headers:
                    kwargs['headers'] = headers
                    
                if data:
                    if isinstance(data, dict):
                        kwargs['json'] = data
                    else:
                        kwargs['data'] = data
                        
                # Make request
                async with session.request(method.upper(), url, **kwargs) as response:
                    response_text = await response.text()
                    
                    # Try to parse as JSON
                    try:
                        response_data = await response.json()
                    except:
                        response_data = response_text
                        
                    return {
                        'success': 200 <= response.status < 300,
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'data': response_data,
                        'text': response_text,
                        'url': str(response.url)
                    }
                    
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': f'Request timed out after {request_timeout} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HTTP request failed: {str(e)}'
            }
            
    async def validate_file_access(self, file_path: str) -> Dict[str, Any]:
        """Validate file access permissions."""
        try:
            path_obj = self._validate_file_path(file_path)
            if not path_obj:
                return {'success': False, 'error': 'Invalid file path'}
                
            result = {
                'success': True,
                'file_path': str(path_obj),
                'exists': path_obj.exists(),
                'is_file': path_obj.is_file() if path_obj.exists() else None,
                'is_directory': path_obj.is_dir() if path_obj.exists() else None,
                'readable': os.access(path_obj, os.R_OK) if path_obj.exists() else None,
                'writable': os.access(path_obj, os.W_OK) if path_obj.exists() else None,
                'parent_writable': os.access(path_obj.parent, os.W_OK) if path_obj.parent.exists() else None
            }
            
            if path_obj.exists():
                stat = path_obj.stat()
                result.update({
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'permissions': oct(stat.st_mode)[-3:]
                })
                
            return result
            
        except Exception as e:
            return {'success': False, 'error': f'File validation failed: {str(e)}'}
            
    async def validate_api_endpoint(self, url: str) -> Dict[str, Any]:
        """Validate API endpoint accessibility."""
        try:
            if not self._validate_url(url):
                return {'success': False, 'error': 'Invalid URL'}
                
            # Simple HEAD request to check accessibility
            result = await self._execute_http_request('HEAD', url, timeout=10)
            
            return {
                'success': result['success'],
                'url': url,
                'accessible': result['success'],
                'status_code': result.get('status_code'),
                'error': result.get('error')
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Endpoint validation failed: {str(e)}'}
            
    def _log_action(self, action_type: str, action_data: Dict[str, Any]):
        """Log action execution for monitoring."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'data': action_data
        }
        
        self.action_history.append(log_entry)
        
        # Limit history size
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]
            
        logger.info(f"Action executed: {action_type} - Success: {action_data.get('success', 'unknown')}")
        
    def get_action_stats(self) -> Dict[str, Any]:
        """Get action execution statistics."""
        if not self.action_history:
            return {'total_actions': 0}
            
        total_actions = len(self.action_history)
        successful_actions = sum(1 for action in self.action_history if action['data'].get('success'))
        
        # Count by type
        action_types = {}
        for action in self.action_history:
            action_type = action['action_type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
            
        return {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': successful_actions / total_actions,
            'action_types': action_types,
            'sandbox_mode': self.sandbox_mode,
            'sandbox_directory': str(self.sandbox_dir) if self.sandbox_mode else None
        }
        
    def cleanup(self):
        """Cleanup action system resources."""
        try:
            # Kill any active processes
            for process_id, process in self.active_processes.items():
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                        
            self.active_processes.clear()
            
            # Clean up sandbox directory
            if self.sandbox_mode and self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
                
            logger.info("Action system cleanup completed")
            
        except Exception as e:
            logger.warning(f"Action system cleanup failed: {e}") 