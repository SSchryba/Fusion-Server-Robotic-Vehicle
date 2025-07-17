#!/usr/bin/env python3
"""
AutoFix Server Launcher
Launch the self-correcting code generation and validation server
"""

import sys
import os
import argparse
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autofix_server import AutoFixServer

def main():
    parser = argparse.ArgumentParser(description="AutoFix Server Launcher")
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8003, help='Port number (default: 8003)')
    parser.add_argument('--kb-file', default='piraz_os_kb.json', help='Knowledge base file path')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--dev', action='store_true', help='Run in development mode with auto-reload')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 AutoFix Server")
    print("=" * 40)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Knowledge Base: {args.kb_file}")
    print(f"Log Level: {args.log_level}")
    print(f"Development Mode: {args.dev}")
    print("=" * 40)
    
    # Create and run server
    server = AutoFixServer()
    
    try:
        if args.dev:
            import uvicorn
            uvicorn.run(
                "autofix_server:AutoFixServer().app",
                host=args.host,
                port=args.port,
                reload=True,
                log_level=args.log_level.lower()
            )
        else:
            server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AutoFix server...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 