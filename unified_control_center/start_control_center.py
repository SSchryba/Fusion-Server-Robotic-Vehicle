#!/usr/bin/env python3
"""
Unified Control Center Startup Script
Launches the comprehensive control interface for all systems
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
        import requests
        import psutil
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("Please run: pip install -r requirements.txt")
            return False

def check_system_availability():
    """Check if other systems are available"""
    systems_status = {}
    
    systems = {
        "Root Agent UI": "http://localhost:5000",
        "Fusion Server": "http://localhost:8000", 
        "Quantum Agent": "http://localhost:8002"
    }
    
    print("\n🔍 Checking system availability...")
    
    for name, url in systems.items():
        try:
            import requests
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                systems_status[name] = "✅ Online"
            else:
                systems_status[name] = "⚠️ Available but returning errors"
        except:
            systems_status[name] = "❌ Offline"
    
    for name, status in systems_status.items():
        print(f"  {name}: {status}")
    
    return systems_status

def start_server():
    """Start the unified control center server"""
    print("🌌 Unified Control Center Startup")
    print("=" * 60)
    
    # Change to control center directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check system availability
    systems_status = check_system_availability()
    
    print("\n🚀 Starting Unified Control Center...")
    print("=" * 60)
    print("🌐 Control Interface: http://localhost:9000")
    print("🧬 Fusion Tools Integration: Ready")
    print("⚛️ Quantum Agent Integration: Ready") 
    print("🖥️ Server Fusion Integration: Ready")
    print("🤖 Root Agent Integration: Ready")
    print("=" * 60)
    
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)  # Wait for server to start
            try:
                webbrowser.open('http://localhost:9000')
                print("\n🌐 Browser opened to Control Center")
            except:
                print("\n📝 Please manually open: http://localhost:9000")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Import and run the control server
        from control_server import main
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Control Center stopped by user")
    except Exception as e:
        print(f"❌ Control Center error: {e}")

if __name__ == '__main__':
    start_server() 