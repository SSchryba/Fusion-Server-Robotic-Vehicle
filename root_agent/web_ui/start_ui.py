#!/usr/bin/env python3
"""
Root Agent Web UI Startup Script
Easy launcher for the web interface
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
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

def start_server():
    """Start the web server"""
    print("🚀 Starting Root Agent Web UI...")
    print("=" * 50)
    
    # Change to web_ui directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start the server
    try:
        # Open browser after a short delay
        import threading
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open('http://localhost:5000')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Import and run the app
        from app import main
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    start_server() 