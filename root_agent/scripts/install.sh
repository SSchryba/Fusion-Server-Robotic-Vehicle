#!/bin/bash
# Root Agent Installation Script
# ⚠️  WARNING: This installs a root-level system agent with full access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/root_agent"
SERVICE_NAME="aiagent"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_FILE="/var/log/aiagent.log"

echo -e "${RED}⚠️  ROOT AGENT INSTALLATION${NC}"
echo "============================================="
echo "This will install a root-level autonomous AI agent"
echo "with full system access. Only proceed if you"
echo "understand the security implications."
echo "============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   echo "Usage: sudo ./install.sh"
   exit 1
fi

# Confirm installation
read -p "Do you want to proceed with installation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

echo -e "${YELLOW}🔧 Installing Root Agent...${NC}"

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install psutil pathlib2 typing-extensions
else
    echo -e "${RED}❌ pip3 not found. Please install Python 3 and pip3${NC}"
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/config"

# Copy agent files
echo "Copying agent files..."
cp -r ../agent.py "$INSTALL_DIR/"
cp -r ../requirements.txt "$INSTALL_DIR/"
cp -r ../demo.py "$INSTALL_DIR/"

# Set permissions
echo "Setting permissions..."
chmod +x "$INSTALL_DIR/agent.py"
chmod +x "$INSTALL_DIR/demo.py"
chown -R root:root "$INSTALL_DIR"

# Install systemd service
echo "Installing systemd service..."
cp ../aiagent.service "$SERVICE_FILE"

# Create log file
echo "Creating log file..."
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service
echo "Enabling service..."
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo
echo "🚀 Usage:"
echo "  Start service:    sudo systemctl start $SERVICE_NAME"
echo "  Stop service:     sudo systemctl stop $SERVICE_NAME"
echo "  Service status:   sudo systemctl status $SERVICE_NAME"
echo "  View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "  Run demo:         sudo python3 $INSTALL_DIR/demo.py"
echo
echo "📁 Files installed to: $INSTALL_DIR"
echo "📄 Service file: $SERVICE_FILE"
echo "📋 Log file: $LOG_FILE"
echo
echo -e "${RED}⚠️  SECURITY WARNING:${NC}"
echo "This agent has full root access to your system."
echo "Monitor its activities and use with extreme caution."
echo
echo "To uninstall:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo systemctl disable $SERVICE_NAME"
echo "  sudo rm $SERVICE_FILE"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo rm $LOG_FILE"
echo "  sudo systemctl daemon-reload" 