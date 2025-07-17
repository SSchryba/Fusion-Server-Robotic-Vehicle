#!/usr/bin/env python3
"""
Fusion-Hybrid-V1 Complete System Startup
Starts all fusion, quantum, and root agent components
"""

import subprocess
import sys
import time
import os
import threading
import webbrowser
from pathlib import Path

def start_server(command, description, cwd=None, delay=0):
    """Start a server process"""
    if delay:
        time.sleep(delay)
    
    print(f"🚀 Starting {description}...")
    
    try:
        if cwd:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
        else:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
        
        print(f"✅ {description} started successfully (PID: {process.pid})")
        return process
    
    except Exception as e:
        print(f"❌ Failed to start {description}: {e}")
        return None

def main():
    """Start all system components"""
    print("🌌 Fusion-Hybrid-V1 Complete System Startup")
    print("=" * 60)
    
    processes = []
    
    # 1. Start Main Fusion Server (Backend)
    processes.append(start_server(
        "python main.py",
        "Main Fusion Server (Backend)",
        delay=0
    ))
    
    # 2. Start Unified Control Center
    processes.append(start_server(
        "python control_server.py",
        "Unified Control Center",
        cwd="unified_control_center",
        delay=2
    ))
    
    # 3. Start Quantum Agent Integration
    processes.append(start_server(
        "python quantum_integration.py",
        "Quantum Agent Integration",
        delay=4
    ))
    
    # 4. Start Root Agent Integration
    processes.append(start_server(
        "python root_agent_integration.py",
        "Root Agent Integration",
        delay=6
    ))
    
    # Wait for servers to start
    time.sleep(10)
    
    print("\n🌐 Opening Control Interfaces...")
    print("=" * 60)
    
    # Open browsers to control interfaces
    urls = [
        ("http://localhost:8000", "Main Fusion Interface"),
        ("http://localhost:9000", "Unified Control Center"),
    ]
    
    for url, name in urls:
        try:
            webbrowser.open(url)
            print(f"🔗 Opened {name}: {url}")
        except:
            print(f"📝 Please manually open {name}: {url}")
    
    print("\n🎯 All Systems Operational!")
    print("=" * 60)
    print("🧬 Fusion System: http://localhost:8000")
    print("🌌 Control Center: http://localhost:9000")
    print("⚛️ Quantum Agent: Available")
    print("🤖 Root Agent: Available")
    print("=" * 60)
    print("\n✨ Your complete AI fusion system is now running!")
    print("Press Ctrl+C to stop all services")
    
    try:
        # Keep the main script running
        while True:
            time.sleep(10)
            # Check if processes are still running
            running_count = sum(1 for p in processes if p and p.poll() is None)
            print(f"📊 Status: {running_count}/{len([p for p in processes if p])} services running")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for process in processes:
            if process and process.poll() is None:
                process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
