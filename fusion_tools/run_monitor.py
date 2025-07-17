#!/usr/bin/env python3
"""
Fusion Status Monitor Runner
Launch the terminal-based or web-based fusion status monitor
"""

import sys
import os
import argparse
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor.status_monitor import FusionStatusMonitor

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fusion Status Monitor")
    parser.add_argument('--mode', choices=['terminal', 'web'], default='terminal',
                       help='Monitor mode (terminal or web)')
    parser.add_argument('--refresh', type=int, default=5,
                       help='Refresh interval in seconds')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host for web mode')
    parser.add_argument('--port', type=int, default=8002,
                       help='Port for web mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.mode == 'terminal':
        print("🚀 Starting Fusion Status Monitor (Terminal Mode)")
        print("=" * 50)
        
        monitor = FusionStatusMonitor()
        monitor.run()
        
    elif args.mode == 'web':
        print("🌐 Starting Fusion Status Monitor (Web Mode)")
        print(f"📡 Server will be available at http://{args.host}:{args.port}")
        print("=" * 50)
        
        # TODO: Implement web monitor
        from monitor.web_monitor import WebMonitor
        web_monitor = WebMonitor()
        web_monitor.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 