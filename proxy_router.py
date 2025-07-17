"""
Proxy Router Module

This module implements a socket-based proxy router that can intercept 
and route network activity for enhanced security and monitoring.
"""

import socket
import threading
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class ProxyRouter:
    """
    Socket-based proxy router for network activity interception and routing.
    Integrates with blockchain for secure logging of all network activity.
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        """
        Initialize the proxy router.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.activity_log = []
        self.blockchain_integration = False
        self.connections = {}
        
    def handle_client_request(self, client_socket: socket.socket, client_addr: Tuple[str, int]) -> None:
        """
        Handle incoming client requests.
        
        Args:
            client_socket: Client socket connection
            client_addr: Client address tuple (host, port)
        """
        request = b""
        client_socket.setblocking(False)
        
        # Connection ID for tracking
        connection_id = f"{client_addr[0]}:{client_addr[1]}_{int(time.time())}"
        self.connections[connection_id] = {
            "start_time": time.time(),
            "client_addr": client_addr,
            "bytes_received": 0,
            "bytes_sent": 0,
            "status": "active"
        }
        
        # Try to receive data from the client
        start_time = time.time()
        while time.time() - start_time < 5:  # 5 second timeout
            try:
                data = client_socket.recv(1024)
                if data:
                    request += data
                    self.connections[connection_id]["bytes_received"] += len(data)
                else:
                    break
            except (BlockingIOError, socket.error):
                # No data available yet
                time.sleep(0.1)
                continue
        
        if not request:
            logger.warning(f"Empty request from {client_addr[0]}:{client_addr[1]}")
            client_socket.close()
            self.connections[connection_id]["status"] = "closed_empty"
            return

        # Log the incoming request
        try:
            request_text = request.decode('utf-8')
            logger.info(f"Received request from {client_addr[0]}:{client_addr[1]}:\n{request_text[:200]}...")
        except UnicodeDecodeError:
            logger.info(f"Received binary request from {client_addr[0]}:{client_addr[1]}, size: {len(request)} bytes")
            request_text = f"[Binary data of {len(request)} bytes]"
            
        # Record activity
        activity = {
            "connection_id": connection_id,
            "timestamp": time.time(),
            "client_ip": client_addr[0],
            "client_port": client_addr[1],
            "request_size": len(request),
            "request_hash": hashlib.sha256(request).hexdigest(),
            "request_type": "HTTP" if request.startswith(b'GET') or request.startswith(b'POST') else "Unknown"
        }
        
        # Parse the request to get the target
        try:
            first_line = request.split(b'\n')[0]
            url = first_line.split(b' ')[1]
            
            target_hostname = url.split(b'/')[2] if url.startswith(b'http') else url.split(b'/')[0]
            target_hostname = target_hostname.decode('utf-8')
            target_port = 80  # Default to HTTP port
            
            activity["target_host"] = target_hostname
            activity["target_port"] = target_port
            
        except IndexError:
            logger.error(f"Could not parse request: {request_text[:100]}...")
            client_socket.close()
            self.connections[connection_id]["status"] = "error_parsing"
            return
        
        # Forward the request to the target
        try:
            # Create a socket to connect to the target
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.connect((target_hostname, target_port))
            
            # Send the request to the target
            proxy_socket.sendall(request)
            activity["forwarded_at"] = time.time()
            logger.info(f"Forwarded request to {target_hostname}:{target_port}")
            
            # Receive the response from the target
            response = b''
            proxy_socket.setblocking(False)
            
            response_start_time = time.time()
            while time.time() - response_start_time < 10:  # 10 second timeout
                try:
                    data = proxy_socket.recv(1024)
                    if data:
                        response += data
                        self.connections[connection_id]["bytes_sent"] += len(data)
                    else:
                        break
                except (BlockingIOError, socket.error):
                    # No data available yet
                    time.sleep(0.1)
                    continue
            
            # Send the response back to the client
            client_socket.sendall(response)
            
            # Update activity log
            activity["response_size"] = len(response)
            activity["response_time"] = time.time() - activity["forwarded_at"]
            activity["response_hash"] = hashlib.sha256(response).hexdigest()
            activity["status"] = "completed"
            
            logger.info(f"Sent response to {client_addr[0]}:{client_addr[1]}, size: {len(response)} bytes")
            self.connections[connection_id]["status"] = "completed"
            
            # Close the target connection
            proxy_socket.close()
            
        except socket.error as e:
            logger.error(f"Socket error: {e}")
            activity["error"] = str(e)
            activity["status"] = "error"
            self.connections[connection_id]["status"] = "error"
        finally:
            # Close the client connection
            client_socket.close()
            activity["end_time"] = time.time()
            self.activity_log.append(activity)
            
            # Log to blockchain if integration is enabled
            if self.blockchain_integration:
                self.log_to_blockchain(activity)
    
    def start(self) -> None:
        """Start the proxy router server."""
        if self.running:
            logger.warning("Proxy router already running")
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            logger.info(f"Proxy router listening on {self.host}:{self.port}")
            self.running = True
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    logger.info(f"Accepted connection from {client_addr[0]}:{client_addr[1]}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client_request,
                        args=(client_socket, client_addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error accepting connection: {e}")
                    else:
                        break
                        
        except socket.error as e:
            logger.error(f"Socket error starting server: {e}")
            self.running = False
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
                
    def stop(self) -> None:
        """Stop the proxy router server."""
        logger.info("Stopping proxy router")
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except socket.error as e:
                logger.error(f"Error closing server socket: {e}")
                
            self.server_socket = None
            
        logger.info("Proxy router stopped")
    
    def enable_blockchain_integration(self, blockchain) -> None:
        """
        Enable integration with blockchain for secure activity logging.
        
        Args:
            blockchain: Blockchain instance to use for logging
        """
        self.blockchain = blockchain
        self.blockchain_integration = True
        logger.info("Blockchain integration enabled for proxy router")
    
    def log_to_blockchain(self, activity: Dict[str, Any]) -> None:
        """
        Log activity to the blockchain for secure, immutable storage.
        Also emits real-time updates via WebSocket.
        
        Args:
            activity: Activity data to log
        """
        # Emit real-time update via WebSocket
        try:
            # Import here to avoid circular imports
            from app import emit_proxy_activity
            emit_proxy_activity(activity)
            logger.debug(f"Activity emitted via WebSocket: {activity.get('connection_id')}")
        except (ImportError, AttributeError) as e:
            logger.debug(f"WebSocket emission not available: {e}")
        except Exception as e:
            logger.error(f"Error emitting activity via WebSocket: {e}")
            
        # Log to blockchain if available
        if not hasattr(self, 'blockchain'):
            logger.error("Cannot log to blockchain: blockchain not set")
            return
            
        try:
            # Create a document for this activity
            document_id = f"proxy_activity_{activity['connection_id']}"
            
            # Store sensitive information securely
            from pycamo_integration import secure_data

            # Secure the document with Pycamo
            secured_activity = secure_data(activity, 'network_activity')
            
            # Create blockchain document
            self.blockchain.create_document(
                document_id=document_id,
                content={
                    "title": f"Network Activity: {activity['client_ip']} to {activity.get('target_host', 'unknown')}",
                    "activity_data": secured_activity,
                    "sensitive": True,
                    "timestamp": activity["timestamp"]
                },
                author="proxy_router"
            )
            
            logger.info(f"Activity logged to blockchain with ID: {document_id}")
            
        except Exception as e:
            logger.error(f"Error logging to blockchain: {e}")
            
    def get_activity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of proxy router activity.
        
        Returns:
            Dictionary with activity statistics
        """
        if not self.activity_log:
            return {
                "status": "active" if self.running else "stopped",
                "connections": 0,
                "total_bytes_received": 0,
                "total_bytes_sent": 0,
                "active_connections": 0,
                "timestamp": time.time()
            }
            
        total_bytes_received = sum(a.get("request_size", 0) for a in self.activity_log)
        total_bytes_sent = sum(a.get("response_size", 0) for a in self.activity_log)
        active_connections = sum(1 for c in self.connections.values() if c["status"] == "active")
        
        return {
            "status": "active" if self.running else "stopped",
            "connections": len(self.activity_log),
            "total_bytes_received": total_bytes_received,
            "total_bytes_sent": total_bytes_sent,
            "active_connections": active_connections,
            "timestamp": time.time()
        }


# Global proxy router instance
proxy_router = None

def initialize_proxy_router(host: str = '127.0.0.1', port: int = 8080, blockchain = None) -> ProxyRouter:
    """
    Initialize and start the global proxy router.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        blockchain: Optional blockchain instance for integration
        
    Returns:
        Initialized ProxyRouter instance
    """
    global proxy_router
    
    if proxy_router is not None and proxy_router.running:
        logger.warning("Proxy router already running, stopping existing instance")
        proxy_router.stop()
        
    proxy_router = ProxyRouter(host, port)
    
    if blockchain:
        proxy_router.enable_blockchain_integration(blockchain)
        
    # Start the proxy in a background thread
    proxy_thread = threading.Thread(target=proxy_router.start)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    return proxy_router

def get_proxy_router() -> Optional[ProxyRouter]:
    """
    Get the global proxy router instance.
    
    Returns:
        ProxyRouter instance or None if not initialized
    """
    return proxy_router

def start_proxy_server(host: str = '127.0.0.1', port: int = 8080) -> None:
    """
    Start the proxy server directly.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
    """
    router = ProxyRouter(host, port)
    router.start()


# Create a standalone function that can be called externally
def run_proxy_server_standalone():
    """Run the proxy server as a standalone application."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the proxy server
    return start_proxy_server(host='0.0.0.0', port=8080)