#!/usr/bin/env python3
"""
Root Agent Web UI Server (Simplified)
Provides a friendly web interface for the root agent without logging dependencies
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple command execution without agent dependency
def safe_execute_command(command):
    """Execute command safely with basic security checks"""
    # Basic security - block dangerous commands
    dangerous_commands = ['rm -rf /', 'del /f /s /q C:\\', 'format', 'mkfs', 'dd if=']
    
    for dangerous in dangerous_commands:
        if dangerous.lower() in command.lower():
            return {"success": False, "error": f"Blocked dangerous command: {command}"}
    
    try:
        # Execute command
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip()}
        else:
            return {"success": False, "error": result.stderr.strip() or "Command failed"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def safe_read_file(file_path):
    """Read file safely"""
    try:
        # Basic security - check for protected paths
        protected_paths = ['/etc/', 'C:\\Windows\\System32\\', '/proc/', '/sys/']
        
        for protected in protected_paths:
            if protected in file_path:
                return {"success": False, "error": f"Access to protected path blocked: {file_path}"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"success": True, "content": content}
        
    except FileNotFoundError:
        return {"success": False, "error": "File not found"}
    except PermissionError:
        return {"success": False, "error": "Permission denied"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def safe_write_file(file_path, content):
    """Write file safely"""
    try:
        # Basic security - check for protected paths
        protected_paths = ['/etc/', 'C:\\Windows\\System32\\', '/proc/', '/sys/']
        
        for protected in protected_paths:
            if protected in file_path:
                return {"success": False, "error": f"Write to protected path blocked: {file_path}"}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "message": "File written successfully"}
        
    except PermissionError:
        return {"success": False, "error": "Permission denied"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_system_info():
    """Get basic system information"""
    try:
        import platform
        import psutil
        
        info = {
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage('/').total if os.name != 'nt' else psutil.disk_usage('C:\\').total,
                "used": psutil.disk_usage('/').used if os.name != 'nt' else psutil.disk_usage('C:\\').used,
                "free": psutil.disk_usage('/').free if os.name != 'nt' else psutil.disk_usage('C:\\').free,
            }
        }
        
        return {"success": True, "data": info}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    """Serve the main UI"""
    return send_from_directory('.', 'index.html')

@app.route('/api/command', methods=['POST'])
def execute_command():
    """Execute a system command"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'error': 'No command provided'})
    
    result = safe_execute_command(command)
    return jsonify(result)

@app.route('/api/read_file', methods=['POST'])
def read_file():
    """Read a file"""
    data = request.get_json()
    path = data.get('path', '').strip()
    
    if not path:
        return jsonify({'success': False, 'error': 'No file path provided'})
    
    result = safe_read_file(path)
    return jsonify(result)

@app.route('/api/write_file', methods=['POST'])
def write_file():
    """Write to a file"""
    data = request.get_json()
    path = data.get('path', '').strip()
    content = data.get('content', '')
    
    if not path:
        return jsonify({'success': False, 'error': 'No file path provided'})
    
    result = safe_write_file(path, content)
    return jsonify(result)

@app.route('/api/system_info', methods=['POST'])
def system_info():
    """Get system information"""
    result = get_system_info()
    return jsonify(result)

@app.route('/api/list_directory', methods=['POST'])
def list_directory():
    """List directory contents"""
    data = request.get_json()
    path = data.get('path', '').strip()
    
    if not path:
        return jsonify({'success': False, 'error': 'No directory path provided'})
    
    try:
        if not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Directory not found'})
        
        if not os.path.isdir(path):
            return jsonify({'success': False, 'error': 'Path is not a directory'})
        
        files = []
        directories = []
        
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append({
                    "name": item,
                    "type": "directory",
                    "size": 0
                })
            else:
                try:
                    size = os.path.getsize(item_path)
                except:
                    size = 0
                files.append({
                    "name": item,
                    "type": "file",
                    "size": size
                })
        
        return jsonify({
            'success': True, 
            'data': {
                'path': path,
                'directories': directories,
                'files': files,
                'total_items': len(directories) + len(files)
            }
        })
        
    except PermissionError:
        return jsonify({'success': False, 'error': 'Permission denied'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/detect_drives', methods=['POST'])
def detect_drives():
    """Detect drives"""
    try:
        import psutil
        
        drives = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drives.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free
                })
            except PermissionError:
                # This can happen on Windows for system partitions
                drives.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": 0,
                    "used": 0,
                    "free": 0
                })
        
        return jsonify({'success': True, 'data': drives})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent status"""
    status = {
        'online': True,
        'operations_count': 0,
        'version': 'Simple Web UI v1.0'
    }
    return jsonify({'success': True, 'data': status})

def main():
    """Start the web server"""
    print("🚀 Starting Root Agent Web UI (Simple Version)...")
    print("=" * 60)
    print("🌐 Web Interface: http://localhost:5000")
    print("🤖 Agent Status: Online (Simplified Mode)")
    print("🔒 Security: Basic protection active")
    print("📋 Logging: Console only")
    print("=" * 60)
    print("\n✅ All systems ready!")
    print("🎉 Open your browser to http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main() 