import subprocess
import time
import os
import requests
from datetime import datetime

def is_port_open(port):
    try:
        response = requests.get(f'http://localhost:{port}', timeout=2)
        return True
    except:
        return False

def start_backend():
    print(f"[{datetime.now()}] Starting backend...")
    subprocess.Popen(['python', 'fusion_respond.py'], 
                     cwd=r'C:\Users\sschr\Desktop\server',
                     stdout=open('logs/backend.log', 'a'),
                     stderr=subprocess.STDOUT)

def start_ui():
    print(f"[{datetime.now()}] Starting UI...")
    subprocess.Popen(['python', 'root_agent/web_ui/start_ui.py'], 
                     cwd=r'C:\Users\sschr\Desktop\server',
                     stdout=open('logs/ui.log', 'a'),
                     stderr=subprocess.STDOUT)

def main():
    os.chdir(r'C:\Users\sschr\Desktop\server')
    
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('root_agent/web_ui/logs', exist_ok=True)
    
    print("Fusion-Hybrid-V1 Service Monitor Started")
    print("Monitoring backend (8000) and UI (5000)...")
    
    while True:
        # Check backend
        if not is_port_open(8000):
            print(f"[{datetime.now()}] Backend is down, restarting...")
            start_backend()
            time.sleep(10)  # Give it time to start
        
        # Check UI
        if not is_port_open(5000):
            print(f"[{datetime.now()}] UI is down, restarting...")
            start_ui()
            time.sleep(10)  # Give it time to start
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == '__main__':
    main() 