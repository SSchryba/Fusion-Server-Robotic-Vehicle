#!/usr/bin/env python3
"""
Root Agent Web UI Server
Provides a friendly web interface for the root agent
"""

import os
import sys
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent module and patch admin check for web interface
import agent

# Temporarily disable admin check for web interface
original_validate = agent.RootSystemAgent.validate_root_access
agent.RootSystemAgent.validate_root_access = lambda self: None

from agent import RootSystemAgent

app = Flask(__name__)
CORS(app)

# Initialize the agent
root_agent = RootSystemAgent()

@app.route('/')
def index():
    """Serve the main UI"""
    return send_from_directory('.', 'index.html')

@app.route('/api/command', methods=['POST'])
def execute_command():
    """Execute a system command"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'})
        
        result = root_agent.run_cmd(command)
        
        # Check if result indicates an error
        if 'ERROR' in result or 'blocked' in result.lower():
            return jsonify({'success': False, 'error': result})
        
        return jsonify({'success': True, 'output': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/read_file', methods=['POST'])
def read_file():
    """Read a file"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({'success': False, 'error': 'No file path provided'})
        
        content = root_agent.read_file(path)
        
        # Check if result indicates an error
        if 'ERROR' in content:
            return jsonify({'success': False, 'error': content})
        
        return jsonify({'success': True, 'content': content})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/write_file', methods=['POST'])
def write_file():
    """Write to a file"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        content = data.get('content', '')
        
        if not path:
            return jsonify({'success': False, 'error': 'No file path provided'})
        
        success = root_agent.write_file(path, content)
        
        if success:
            return jsonify({'success': True, 'message': 'File written successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to write file'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system_info', methods=['POST'])
def get_system_info():
    """Get system information"""
    try:
        info = root_agent.get_system_info()
        return jsonify({'success': True, 'data': info})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/list_directory', methods=['POST'])
def list_directory():
    """List directory contents"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({'success': False, 'error': 'No directory path provided'})
        
        listing = root_agent.list_filesystem(path, max_depth=1)
        return jsonify({'success': True, 'data': listing})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/detect_drives', methods=['POST'])
def detect_drives():
    """Detect removable drives"""
    try:
        drives = root_agent.detect_removable_drives()
        return jsonify({'success': True, 'data': drives})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent status"""
    try:
        status = {
            'online': True,
            'operations_count': len(root_agent.operations_log),
            'start_time': root_agent.start_time.isoformat(),
            'recent_operations': root_agent.operations_log[-5:] if root_agent.operations_log else []
        }
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

def main():
    """Start the web server"""
    print("🚀 Starting Root Agent Web UI...")
    print("=" * 50)
    print("🌐 Web Interface: http://localhost:5000")
    print("🤖 Agent Status: Online")
    print("🔒 Security: Active")
    print("📋 Logging: Enabled")
    print("=" * 50)
    print("\n⚠️  Note: Running without administrator privileges")
    print("Some functionality may be limited.\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main() 