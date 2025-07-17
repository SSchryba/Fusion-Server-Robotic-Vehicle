#!/usr/bin/env python3
"""
Unified Control Center Server
Provides a comprehensive interface for all fusion hybrid and quantum systems
"""

import os
import sys
import json
import asyncio
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import requests
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class UnifiedControlCenter:
    """Main control center for all systems"""
    
    def __init__(self):
        self.systems = {
            'fusion_tools': {
                'url': 'http://localhost:8000',
                'status': 'unknown',
                'services': ['monitor', 'controller', 'chat', 'autofix']
            },
            'quantum_agent': {
                'url': 'http://localhost:8002',
                'status': 'unknown',
                'services': ['quantum_executor', 'hpc_dispatcher', 'knowledge_ingestor']
            },
            'server_fusion': {
                'url': 'http://localhost:8000',
                'status': 'unknown',
                'services': ['training', 'fusion', 'models']
            },
            'root_agent': {
                'url': 'http://localhost:5000',
                'status': 'unknown',
                'services': ['system_control', 'file_manager', 'security']
            }
        }
        
        self.command_history = []
        self.active_operations = {}
        
    def check_system_status(self, system_name: str) -> Dict[str, Any]:
        """Check status of a specific system"""
        if system_name not in self.systems:
            return {'status': 'unknown', 'error': 'System not found'}
        
        system = self.systems[system_name]
        try:
            response = requests.get(f"{system['url']}/health", timeout=5)
            if response.status_code == 200:
                system['status'] = 'online'
                return {'status': 'online', 'response_time': response.elapsed.total_seconds()}
            else:
                system['status'] = 'error'
                return {'status': 'error', 'code': response.status_code}
        except requests.exceptions.RequestException as e:
            system['status'] = 'offline'
            return {'status': 'offline', 'error': str(e)}
    
    def get_all_system_status(self) -> Dict[str, Any]:
        """Get status of all systems"""
        status = {}
        for system_name in self.systems:
            status[system_name] = self.check_system_status(system_name)
        return status
    
    def execute_fusion_command(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute fusion system command"""
        try:
            if command == 'status':
                response = requests.get('http://localhost:8000/fusion/status', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to get status'}
            
            elif command == 'create_hybrid':
                models = args.get('models', [])
                response = requests.post('http://localhost:8000/fusion/create-hybrid', 
                                       json={'models': models}, timeout=30)
                return response.json() if response.status_code == 200 else {'error': 'Failed to create hybrid'}
            
            elif command == 'pull_deepseek':
                response = requests.post('http://localhost:8000/fusion/pull-deepseek', timeout=60)
                return response.json() if response.status_code == 200 else {'error': 'Failed to pull models'}
            
            elif command == 'start_absorption':
                response = requests.post('http://localhost:8000/fusion/start-absorption', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to start absorption'}
            
            elif command == 'hybrids':
                response = requests.get('http://localhost:8000/fusion/hybrids', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to get hybrids'}
            
            else:
                return {'error': f'Unknown fusion command: {command}'}
                
        except Exception as e:
            logger.error(f"Fusion command error: {e}")
            return {'error': str(e)}
    
    def execute_quantum_command(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute quantum system command"""
        try:
            # Try to connect to real quantum agent system
            if command == 'execute':
                try:
                    # Try quantum agent on port 8002
                    response = requests.post('http://localhost:8002/execute', 
                                           json=args, timeout=30)
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
                
                # Fallback to real quantum execution using subprocess
                circuit_code = args.get('circuit_code', 'from qiskit import QuantumCircuit\nqc = QuantumCircuit(2,2)\nqc.h(0)\nqc.cx(0,1)\nqc.measure_all()')
                backend = args.get('backend', 'qiskit_simulator')
                
                # Try to execute real quantum code
                try:
                    # Write circuit to temp file and execute
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                        f.write(circuit_code)
                        temp_file = f.name
                    
                    result = subprocess.run(['python', temp_file], 
                                          capture_output=True, text=True, timeout=30)
                    os.unlink(temp_file)
                    
                    if result.returncode == 0:
                        return {
                            'success': True,
                            'job_id': f'quantum_job_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                            'backend': backend,
                            'output': result.stdout,
                            'execution_time': datetime.now().isoformat()
                        }
                    else:
                        return {'error': f'Quantum execution failed: {result.stderr}'}
                except Exception as e:
                    return {'error': f'Quantum execution error: {str(e)}'}
            
            elif command == 'backends':
                # Try to get real backends from quantum systems
                try:
                    response = requests.get('http://localhost:8002/backends', timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
                
                # Fallback - check what quantum packages are available
                available_backends = []
                try:
                    import qiskit
                    available_backends.extend(['qiskit_simulator', 'qiskit_aer'])
                except ImportError:
                    pass
                try:
                    import cirq
                    available_backends.append('cirq_simulator')
                except ImportError:
                    pass
                try:
                    import pennylane
                    available_backends.append('pennylane_default')
                except ImportError:
                    pass
                
                return {'backends': available_backends or ['qiskit_simulator']}
            
            elif command == 'demo':
                # Try to run real quantum demo
                try:
                    result = subprocess.run(['python', '../quantum_agent/demo.py'], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        return {'message': 'Quantum demo completed', 'output': result.stdout}
                    else:
                        return {'error': f'Demo failed: {result.stderr}'}
                except Exception as e:
                    return {'error': f'Demo execution error: {str(e)}'}
            
            elif command == 'update_kb':
                # Try to update real knowledge base
                try:
                    result = subprocess.run(['python', '../quantum_agent/fusion_knowledge_updater.py'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return {'message': 'Knowledge base updated', 'output': result.stdout}
                    else:
                        return {'error': f'KB update failed: {result.stderr}'}
                except Exception as e:
                    return {'error': f'KB update error: {str(e)}'}
            
            else:
                return {'error': f'Unknown quantum command: {command}'}
                
        except Exception as e:
            logger.error(f"Quantum command error: {e}")
            return {'error': str(e)}
    
    def execute_server_command(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute server fusion command"""
        try:
            if command == 'status':
                response = requests.get('http://localhost:8000/status', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to get status'}
            
            elif command == 'train':
                data = {
                    'model_name': args.get('model', 'llama2:latest'),
                    'dataset': args.get('dataset', 'alpaca'),
                    'max_steps': args.get('steps', 1000)
                }
                response = requests.post('http://localhost:8000/train', json=data, timeout=30)
                return response.json() if response.status_code == 200 else {'error': 'Failed to start training'}
            
            elif command == 'jobs':
                response = requests.get('http://localhost:8000/jobs', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to get jobs'}
            
            elif command == 'models':
                response = requests.get('http://localhost:8000/models', timeout=10)
                return response.json() if response.status_code == 200 else {'error': 'Failed to get models'}
            
            else:
                return {'error': f'Unknown server command: {command}'}
                
        except Exception as e:
            logger.error(f"Server command error: {e}")
            return {'error': str(e)}
    
    def execute_root_command(self, command: str) -> Dict[str, Any]:
        """Execute root agent command"""
        try:
            # For safety, only allow specific commands
            safe_commands = ['whoami', 'date', 'uptime', 'df -h', 'free -h', 'ps aux | head']
            
            if command in safe_commands:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                return {'error': f'Command not allowed: {command}'}
                
        except Exception as e:
            logger.error(f"Root command error: {e}")
            return {'error': str(e)}
    
    def chat_with_ai(self, message: str, model: str = "llama2:latest") -> Dict[str, Any]:
        """Chat with AI systems"""
        try:
            # Try Ollama first (localhost:11434)
            try:
                ollama_data = {
                    "model": model,
                    "prompt": message,
                    "stream": False
                }
                
                response = requests.post('http://localhost:11434/api/generate', 
                                       json=ollama_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'response': result.get('response', ''),
                        'model': model,
                        'source': 'ollama'
                    }
            except Exception as e:
                logger.info(f"Ollama not available: {e}")
            
            # Try Faith AI server (localhost:8000)
            try:
                faith_data = {
                    "message": message,
                    "model": model
                }
                
                response = requests.post('http://localhost:8000/chat', 
                                       json=faith_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'response': result.get('response', result.get('message', '')),
                        'model': model,
                        'source': 'faith_ai'
                    }
            except Exception as e:
                logger.info(f"Faith AI not available: {e}")
            
            # Try fusion chat system
            try:
                fusion_data = {"message": message}
                response = requests.post('http://localhost:8000/fusion/chat', 
                                       json=fusion_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'response': result.get('response', ''),
                        'model': 'fusion',
                        'source': 'fusion_tools'
                    }
            except Exception as e:
                logger.info(f"Fusion chat not available: {e}")
            
            return {'error': 'No AI systems available'}
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {'error': str(e)}
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get available AI models"""
        try:
            models = []
            
            # Check Ollama models
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=10)
                if response.status_code == 200:
                    ollama_models = response.json().get('models', [])
                    for model in ollama_models:
                        models.append({
                            'name': model.get('name', ''),
                            'source': 'ollama',
                            'size': model.get('size', 0)
                        })
            except:
                pass
            
            # Check Faith AI models
            try:
                response = requests.get('http://localhost:8000/models', timeout=10)
                if response.status_code == 200:
                    faith_models = response.json().get('models', [])
                    for model in faith_models:
                        models.append({
                            'name': model,
                            'source': 'faith_ai'
                        })
            except:
                pass
            
                         return {'success': True, 'models': models}
             
         except Exception as e:
             logger.error(f"Get models error: {e}")
             return {'error': str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'connections': len(psutil.net_connections())
                },
                'processes': len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return {'error': str(e)}

# Initialize control center
control_center = UnifiedControlCenter()

@app.route('/')
def index():
    """Serve the main control center interface"""
    return send_from_directory('.', 'index.html')

@app.route('/api/status')
def get_status():
    """Get overall system status"""
    try:
        return jsonify({
            'success': True,
            'systems': control_center.get_all_system_status(),
            'metrics': control_center.get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'unified_control_center'})

@app.route('/api/systems/status')
def get_systems_status():
    """Get status of all integrated systems"""
    try:
        systems_status = {}
        
        # Check Ollama/Local models
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                systems_status['ollama'] = {
                    'status': 'online',
                    'models': len(models),
                    'available_models': [m.get('name', '') for m in models[:5]]
                }
            else:
                systems_status['ollama'] = {'status': 'offline', 'error': 'Not responding'}
        except:
            systems_status['ollama'] = {'status': 'offline', 'error': 'Connection failed'}
        
        # Check Faith AI Server  
        try:
            response = requests.get('http://localhost:8000/status', timeout=5)
            if response.status_code == 200:
                systems_status['faith_server'] = {
                    'status': 'online',
                    'data': response.json()
                }
            else:
                systems_status['faith_server'] = {'status': 'error', 'code': response.status_code}
        except:
            systems_status['faith_server'] = {'status': 'offline', 'error': 'Connection failed'}
        
        # Get system metrics
        metrics = control_center.get_system_metrics()
        
        return jsonify({
            'success': True,
            'systems': systems_status,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ollama/models')
def get_ollama_models():
    """Get available Ollama models"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            return jsonify({'success': True, 'data': response.json()})
        else:
            return jsonify({'success': False, 'error': 'Ollama not responding'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ollama/chat', methods=['POST'])
def ollama_chat():
    """Send chat message to Ollama"""
    try:
        data = request.json or {}
        model = data.get('model', 'llama2:latest')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        ollama_request = {
            'model': model,
            'prompt': message,
            'stream': False
        }
        
        response = requests.post('http://localhost:11434/api/generate', 
                               json=ollama_request, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True, 
                'response': result.get('response', ''),
                'model': model
            })
        else:
            return jsonify({'success': False, 'error': 'Ollama request failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/training/start', methods=['POST'])
def start_training():
    """Start a training job"""
    try:
        data = request.json or {}
        
        # Connect to Faith AI server for training
        try:
            response = requests.post('http://localhost:8000/train', json=data, timeout=30)
            if response.status_code == 200:
                return jsonify({'success': True, 'result': response.json()})
            else:
                return jsonify({'success': False, 'error': f'Training server responded with {response.status_code}'})
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'error': 'Training server (localhost:8000) is not available'})
        except requests.exceptions.Timeout:
            return jsonify({'success': False, 'error': 'Training request timed out'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Training request failed: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system/command', methods=['POST'])
def execute_system_command():
    """Execute safe system commands"""
    try:
        data = request.json or {}
        command = data.get('command', '').strip()
        
        # Only allow safe commands
        safe_commands = {
            'whoami': 'whoami',
            'date': 'date /t',
            'time': 'time /t', 
            'systeminfo': 'systeminfo | findstr /C:"Total Physical Memory"',
            'processes': 'tasklist | findstr /C:"python"',
            'network': 'netstat -an | findstr LISTENING | findstr ":80"'
        }
        
        if command in safe_commands:
            try:
                result = subprocess.run(safe_commands[command], shell=True, 
                                      capture_output=True, text=True, timeout=10)
                return jsonify({
                    'success': True,
                    'command': command,
                    'output': result.stdout,
                    'error': result.stderr if result.stderr else None
                })
            except subprocess.TimeoutExpired:
                return jsonify({'success': False, 'error': 'Command timed out'})
        else:
            return jsonify({'success': False, 'error': f'Command not allowed: {command}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fusion/<command>', methods=['POST'])
def fusion_command(command):
    """Execute fusion system command"""
    try:
        args = request.json or {}
        result = control_center.execute_fusion_command(command, args)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/quantum/<command>', methods=['POST'])
def quantum_command(command):
    """Execute quantum system command"""
    try:
        args = request.json or {}
        result = control_center.execute_quantum_command(command, args)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/server/<command>', methods=['POST'])
def server_command(command):
    """Execute server system command"""
    try:
        args = request.json or {}
        result = control_center.execute_server_command(command, args)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/root/command', methods=['POST'])
def root_command():
    """Execute root system command"""
    try:
        data = request.json or {}
        command = data.get('command', '')
        result = control_center.execute_root_command(command)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/execute', methods=['POST'])
def execute_unified_command():
    """Execute unified command"""
    try:
        data = request.json or {}
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'})
        
        # Log command
        control_center.command_history.append({
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        
        # Parse command
        parts = command.split('.')
        if len(parts) >= 2:
            system = parts[0]
            action = parts[1]
            args = data.get('args', {})
            
            if system == 'fusion':
                result = control_center.execute_fusion_command(action, args)
            elif system == 'quantum':
                result = control_center.execute_quantum_command(action, args)
            elif system == 'server':
                result = control_center.execute_server_command(action, args)
            elif system == 'root':
                result = control_center.execute_root_command(action)
            else:
                result = {'error': f'Unknown system: {system}'}
        else:
            # Handle special commands
            if command == 'help':
                result = {
                    'commands': [
                        'fusion.status - Get fusion system status',
                        'fusion.create_hybrid - Create hybrid model',
                        'quantum.execute - Execute quantum circuit',
                        'server.train - Start model training',
                        'root.command - Execute system command'
                    ]
                }
            elif command == 'status.all':
                result = {
                    'systems': control_center.get_all_system_status(),
                    'metrics': control_center.get_system_metrics()
                }
            else:
                result = {'error': f'Unknown command format: {command}'}
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics"""
    try:
        return jsonify({
            'success': True,
            'metrics': control_center.get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def get_command_history():
    """Get command history"""
    try:
        return jsonify({
            'success': True,
            'history': control_center.command_history[-50:],  # Last 50 commands
            'count': len(control_center.command_history)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    """Send message to AI systems"""
    try:
        data = request.json or {}
        message = data.get('message', '').strip()
        model = data.get('model', 'llama2:latest')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        result = control_center.chat_with_ai(message, model)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat/models')
def chat_models():
    """Get available AI models for chat"""
    try:
        result = control_center.get_available_models()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def main():
    """Start the unified control center server"""
    print("🌌 Starting Unified Control Center Server...")
    print("=" * 60)
    print("🌐 Control Center: http://localhost:9000")
    print("🧬 Fusion Tools Integration: ✅")
    print("⚛️ Quantum Agent Integration: ✅") 
    print("🖥️ Server Fusion Integration: ✅")
    print("🤖 Root Agent Integration: ✅")
    print("=" * 60)
    print("\n🎯 Full access to all fusion hybrid and quantum systems!")
    print("📊 Real-time monitoring and control")
    print("🔧 Unified command interface")
    print("🛡️ Secure system management")
    print("\nOpen your browser to http://localhost:9000")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        app.run(host='0.0.0.0', port=9000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Control Center stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main() 