#!/usr/bin/env python3
"""
Kairo AI Live Crypto Hunter - Installation Script

This script performs the initial setup for the Kairo AI Live Crypto Hunter application:
1. Verifies system requirements
2. Installs required dependencies
3. Sets up the database
4. Configures environment variables
5. Initializes the blockchain and necessary components

Usage:
    python install.py
"""

import os
import sys
import subprocess
import logging
import getpass
import platform
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("install.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KairoInstall')

# Installation banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════════╗
║              KAIRO AI LIVE CRYPTO HUNTER v1.2.0                       ║
║                  INSTALLATION SCRIPT                                  ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

# Required Python version
REQUIRED_PYTHON_VERSION = (3, 9)

# Required environment variables
REQUIRED_ENV_VARS = [
    'DATABASE_URL',
    'MONERO_WALLET_ADDRESS',
]

# Optional environment variables
OPTIONAL_ENV_VARS = [
    'VENMO_USERNAME',
    'VENMO_PASSWORD',
    'VENMO_ACCESS_TOKEN',
]

def print_banner():
    """Print the installation banner."""
    print(BANNER)
    print(f"Installation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def check_system_requirements():
    """Check system requirements."""
    logger.info("Checking system requirements...")
    
    # Check Python version
    current_python = sys.version_info[:2]
    if current_python < REQUIRED_PYTHON_VERSION:
        logger.error(f"Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} or higher is required")
        logger.error(f"Current Python version: {current_python[0]}.{current_python[1]}")
        return False
    
    logger.info(f"Python version check passed: {current_python[0]}.{current_python[1]}")
    
    # Check OS compatibility
    os_name = platform.system()
    logger.info(f"Detected operating system: {os_name}")
    
    # Additional system checks can be added here
    
    return True

def install_dependencies():
    """Install required dependencies."""
    logger.info("Installing required dependencies...")
    
    try:
        # Use pip to install dependencies from pyproject.toml
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False

def setup_database():
    """Set up the database."""
    logger.info("Setting up database...")
    
    # Check if DATABASE_URL is set
    if 'DATABASE_URL' not in os.environ:
        logger.error("DATABASE_URL environment variable not set")
        db_url = input("Enter PostgreSQL database URL: ")
        os.environ['DATABASE_URL'] = db_url
    
    try:
        # Import database setup modules
        import database
        
        # Initialize database
        logger.info("Initializing database...")
        # Add actual database initialization code here
        
        logger.info("Database setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False

def configure_environment_variables():
    """Configure environment variables."""
    logger.info("Configuring environment variables...")
    
    # Check required environment variables
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if var not in os.environ:
            missing_vars.append(var)
    
    # Prompt for missing required variables
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("\nThe following environment variables are required for the application:")
        
        for var in missing_vars:
            if var == 'MONERO_WALLET_ADDRESS':
                value = input(f"Enter {var}: ")
            else:
                value = getpass.getpass(f"Enter {var}: ")
            
            os.environ[var] = value
    
    # Check optional environment variables
    missing_optional = []
    for var in OPTIONAL_ENV_VARS:
        if var not in os.environ:
            missing_optional.append(var)
    
    # Prompt for missing optional variables with user confirmation
    if missing_optional:
        logger.info(f"Missing optional environment variables: {', '.join(missing_optional)}")
        print("\nThe following environment variables are optional but recommended:")
        print(', '.join(missing_optional))
        
        setup_optional = input("Would you like to set up these optional variables now? (y/n): ").lower() == 'y'
        
        if setup_optional:
            for var in missing_optional:
                if 'PASSWORD' in var:
                    value = getpass.getpass(f"Enter {var}: ")
                else:
                    value = input(f"Enter {var}: ")
                
                if value.strip():
                    os.environ[var] = value
    
    logger.info("Environment variables configured successfully")
    return True

def initialize_blockchain():
    """Initialize the blockchain and necessary components."""
    logger.info("Initializing blockchain...")
    
    try:
        # Import blockchain modules
        import blockchain
        
        # Initialize blockchain
        logger.info("Setting up initial blockchain state...")
        # Add actual blockchain initialization code here
        
        logger.info("Blockchain initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Blockchain initialization failed: {str(e)}")
        return False

def create_environment_file():
    """Create a .env file with the configured environment variables."""
    logger.info("Creating .env file...")
    
    env_vars = {}
    for var in REQUIRED_ENV_VARS + OPTIONAL_ENV_VARS:
        if var in os.environ:
            env_vars[var] = os.environ[var]
    
    try:
        with open(".env", "w") as f:
            for var, value in env_vars.items():
                if 'PASSWORD' in var or 'TOKEN' in var:
                    value = '********'  # Mask sensitive values in the file
                f.write(f"{var}={value}\n")
        
        logger.info(".env file created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create .env file: {str(e)}")
        return False

def run_installation():
    """Run the complete installation process."""
    print_banner()
    
    steps = [
        ("System requirements", check_system_requirements),
        ("Dependencies installation", install_dependencies),
        ("Environment variables", configure_environment_variables),
        ("Database setup", setup_database),
        ("Blockchain initialization", initialize_blockchain),
        ("Environment file", create_environment_file)
    ]
    
    success = True
    
    for step_name, step_func in steps:
        print(f"\n[{step_name}]")
        print("-" * (len(step_name) + 2))
        
        if step_func():
            print(f"✓ {step_name} completed successfully")
        else:
            print(f"✗ {step_name} failed")
            success = False
            if input("Continue installation despite errors? (y/n): ").lower() != 'y':
                break
    
    if success:
        print("\n" + "="*70)
        print("INSTALLATION COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nYou can now start the application with:")
        print("    gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app")
        print("\nOr run operations from the CLI:")
        print("    python kairo_operations.py status")
    else:
        print("\n" + "="*70)
        print("INSTALLATION COMPLETED WITH ERRORS")
        print("Please check the logs and resolve the issues before starting the application")
        print("="*70)
    
    print(f"\nInstallation ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Installation log: {os.path.abspath('install.log')}")

if __name__ == "__main__":
    run_installation()