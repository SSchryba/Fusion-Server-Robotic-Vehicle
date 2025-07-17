#!/usr/bin/env python3
"""
Fusion Chat Interface Runner
Launch the chat server with web interface
"""

import sys
import os
import argparse
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat.backend.chat_server import ChatServer

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fusion Chat Interface")
    parser.add_argument('--host', default='0.0.0.0',
                       help='Host address')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port number')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--fusion-host', default='localhost',
                       help='Fusion server host')
    parser.add_argument('--fusion-port', type=int, default=8000,
                       help='Fusion server port')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("💬 Fusion Chat Interface")
    print("=" * 40)
    print(f"🌐 Chat server: http://{args.host}:{args.port}")
    print(f"🔗 Fusion server: http://{args.fusion_host}:{args.fusion_port}")
    print("=" * 40)
    
    # Create and run chat server
    server = ChatServer()
    
    # Override fusion server settings if provided
    if args.fusion_host != 'localhost' or args.fusion_port != 8000:
        server.api_client = server.api_client.__class__(
            host=args.fusion_host,
            port=args.fusion_port,
            timeout=server.config.timeout
        )
    
    try:
        # Test connection to fusion server
        health = server.api_client.get_server_health()
        if health.get('status') == 'ok':
            print("✅ Connected to fusion server")
        else:
            print("⚠️  Warning: Fusion server may not be available")
            print("   Chat interface will still work but responses may fail")
        
        # Start the server
        print("\n🚀 Starting chat server...")
        print("📱 Open your browser and navigate to the chat interface")
        print("⏹️  Press Ctrl+C to stop the server")
        
        server.run(host=args.host, port=args.port)
        
    except KeyboardInterrupt:
        print("\n👋 Chat server stopped")
    except Exception as e:
        print(f"❌ Failed to start chat server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 