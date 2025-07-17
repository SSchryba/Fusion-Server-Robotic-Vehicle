#!/bin/bash
# BUD-EE System Startup Script
# Starts the complete autonomous emotional AI vehicle system

echo "🤖 BUD-EE Autonomous Emotional AI Vehicle"
echo "=========================================="

# Check if running as root (needed for GPIO)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script needs to run with sudo for GPIO access"
    echo "Restarting with sudo..."
    sudo "$0" "$@"
    exit
fi

# Check if pigpio daemon is running
if ! systemctl is-active --quiet pigpiod; then
    echo "🔧 Starting pigpio daemon..."
    systemctl start pigpiod
    sleep 2
fi

# Check for virtual environment
if [ ! -d "budee_env" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv budee_env
fi

# Activate virtual environment
source budee_env/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check for calibration file
if [ ! -f "budee_calibration_map.json" ]; then
    echo "⚠️  No calibration found!"
    read -p "Run calibration routine? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "🔧 Running calibration..."
        python3 calibration_routine.py
    fi
fi

# Create sounds directory if it doesn't exist
mkdir -p sounds

# Set proper permissions
chmod +x *.py

echo "🚀 Starting BUD-EE System..."
echo "Press Ctrl+C to stop"
echo "----------------------------------"

# Start the main system
python3 budee_main.py

echo "🛑 BUD-EE System stopped" 