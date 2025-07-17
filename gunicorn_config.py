"""
Gunicorn configuration for Flask-SocketIO application
"""

import multiprocessing

# Bind to all interfaces
bind = "0.0.0.0:5000"

# Use a worker class compatible with Socket.IO
worker_class = "eventlet"

# Number of worker processes
workers = 1  # For WebSockets with Socket.IO, use only 1 worker

# Reuse port and reload on code changes
reuse_port = True
reload = True

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Keep worker timeout high for long-lived WebSocket connections
timeout = 120