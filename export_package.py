#!/usr/bin/env python3
"""
Export Package Script

This script creates a production-ready export package of the Kairo AI Live Crypto Hunter
with all simulation code removed and only production functionality included.

Usage:
    python export_package.py [output_dir]
"""

import os
import sys
import shutil
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExportPackage')

# Production files to include in the export
PRODUCTION_FILES = [
    # Core blockchain files
    'blockchain.py',
    'blockchain_connector.py',
    'blockchain_monitor.py',
    'blockchain_wallet_util.py',
    
    # Main application files
    'main.py',
    'app.py',
    'database.py',
    'models.py',
    
    # Core functionality
    'drift_chain.py',
    'drift_chain_integration.py',
    'drift_chain_routes.py',
    'eth_wallet_vacuum.py',
    'eth_bruteforce_router.py',
    
    # Activity coordination
    'activity_coordinator.py',
    'activity_scheduler.py',
    'entropy_coordinator.py',
    
    # Continuous processing
    'fluxion.py',
    
    # Integration modules
    'monero_integration.py',
    'venmo_integration.py',
    'pycamo_integration.py',
    
    # Operations and utilities
    'kairo_operations.py',
    'secure_wallet_manager.py',
    'proxy_router.py',
    
    # Data validation
    'data_authenticity_validator.py',
    'sovereign_ledger.py',
    'sovereign_ledger_dao.py',
    
    # Web and utilities
    'web_scraper.py',
    'broadcast_message.py',
    'broadcast_genesis.py',
    'broadcast_transaction.py',
    
    # Configuration
    'gunicorn_config.py',
    'pyproject.toml',
    '.replit',
    
    # Keys (if they exist and are needed)
    'private_key.pem',
    'public_key.pem',
    
    # Documentation files
    'README.md',
    'permission_report.json',
]

# Directories to include
PRODUCTION_DIRS = [
    'templates',
    'static',
    'blockchain_stats',
    'dark_kairo_drift_machine',
    'gh_scanner',
]

def create_export_package(output_dir=None):
    """
    Create a production-ready export package with no simulation code.
    
    Args:
        output_dir: Output directory for the export (default: kairo_export_[timestamp])
    """
    # Create timestamp for export folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Set output directory
    if not output_dir:
        output_dir = f"kairo_export_{timestamp}"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created export directory: {output_dir}")
    
    # Copy production files
    files_copied = 0
    for filename in PRODUCTION_FILES:
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join(output_dir, filename))
            files_copied += 1
            logger.info(f"Copied file: {filename}")
        else:
            logger.warning(f"File not found: {filename}")
    
    # Copy production directories
    dirs_copied = 0
    for dirname in PRODUCTION_DIRS:
        if os.path.exists(dirname) and os.path.isdir(dirname):
            dest_dir = os.path.join(output_dir, dirname)
            shutil.copytree(dirname, dest_dir)
            dirs_copied += 1
            logger.info(f"Copied directory: {dirname}")
        else:
            logger.warning(f"Directory not found: {dirname}")
    
    # Create export metadata
    metadata = {
        "name": "Kairo AI Live Crypto Hunter",
        "version": "1.2.0",
        "export_timestamp": timestamp,
        "files_included": files_copied,
        "directories_included": dirs_copied,
        "production_ready": True,
    }
    
    # Write metadata file
    with open(os.path.join(output_dir, "export_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Export completed: {files_copied} files and {dirs_copied} directories copied")
    logger.info(f"Export package created at: {os.path.abspath(output_dir)}")
    
    return os.path.abspath(output_dir)

if __name__ == "__main__":
    # Get output directory from command line if provided
    output_dir = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Create export package
    export_path = create_export_package(output_dir)
    
    print("\n" + "="*70)
    print(f"EXPORT PACKAGE CREATED: {export_path}")
    print("="*70)