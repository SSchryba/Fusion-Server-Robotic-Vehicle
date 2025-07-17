import os
import subprocess
import json
from datetime import datetime

tools_log_path = os.path.join(os.path.dirname(__file__), 'tools_log.json')

def log_install(tool_name, step, status, details=None):
    log = {}
    if os.path.exists(tools_log_path):
        with open(tools_log_path) as f:
            log = json.load(f)
    if tool_name not in log:
        log[tool_name] = {}
    if 'install_log' not in log[tool_name]:
        log[tool_name]['install_log'] = []
    log[tool_name]['install_log'].append({
        'step': step,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    with open(tools_log_path, 'w') as f:
        json.dump(log, f, indent=2)

def install_tool(tool_path):
    tool_name = os.path.basename(tool_path.rstrip('/'))
    # 1. requirements.txt
    req_path = os.path.join(tool_path, 'requirements.txt')
    if os.path.exists(req_path):
        try:
            subprocess.run(['pip', 'install', '-r', req_path], check=True)
            log_install(tool_name, 'requirements.txt', 'success')
        except Exception as e:
            log_install(tool_name, 'requirements.txt', 'fail', str(e))
            raise
    # 2. setup.py
    setup_path = os.path.join(tool_path, 'setup.py')
    if os.path.exists(setup_path):
        # Block dangerous install scripts
        with open(setup_path) as f:
            if 'os.system' in f.read() or 'subprocess' in f.read():
                log_install(tool_name, 'setup.py', 'blocked', 'Dangerous commands detected')
                raise Exception('Blocked dangerous setup.py')
        try:
            subprocess.run(['python', setup_path, 'install'], check=True)
            log_install(tool_name, 'setup.py', 'success')
        except Exception as e:
            log_install(tool_name, 'setup.py', 'fail', str(e))
            raise
    # 3. pip install .
    try:
        subprocess.run(['pip', 'install', tool_path], check=True)
        log_install(tool_name, 'pip install .', 'success')
    except Exception as e:
        log_install(tool_name, 'pip install .', 'fail', str(e))
        raise
    return True 