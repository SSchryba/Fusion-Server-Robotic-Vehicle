#!/usr/bin/env python3
"""
Installation script for Multi-Blockchain Wallet in Python

This script sets up the Multi-Blockchain Wallet and installs required dependencies
"""

import os
import sys
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command):
    """Run a shell command and log the output"""
    logger.info(f"Running: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    
    if stdout:
        logger.info(stdout.decode())
    if stderr:
        logger.error(stderr.decode())
        
    return process.returncode

def install_dependencies():
    """Install required Python packages"""
    logger.info("Installing required dependencies...")
    
    # Required packages
    packages = [
        "web3",
        "python-dotenv",
        "cryptography",
        "bit",
        "eth-account",
    ]
    
    # Install packages
    result = run_command(f"{sys.executable} -m pip install {' '.join(packages)}")
    
    if result != 0:
        logger.error("Failed to install dependencies")
        return False
        
    logger.info("Dependencies installed successfully")
    return True

def setup_multichain_wallet():
    """Set up the Multi-Blockchain Wallet from the repository"""
    wallet_repo_path = "./Multi-Blockchain-Wallet-in-Python"
    
    # Check if repository exists
    if not os.path.exists(wallet_repo_path):
        logger.info("Cloning Multi-Blockchain Wallet repository...")
        result = run_command(f"git clone https://github.com/fischlerben/Multi-Blockchain-Wallet-in-Python.git")
        
        if result != 0:
            logger.error("Failed to clone repository")
            return False
    
    # Setup HD-Wallet-Derive
    wallet_derive_path = f"{wallet_repo_path}/wallet/hd-wallet-derive"
    if not os.path.exists(wallet_derive_path):
        logger.info("Setting up HD-Wallet-Derive...")
        
        # Change directory to wallet folder
        os.chdir(f"{wallet_repo_path}/wallet")
        
        # Clone hd-wallet-derive
        result = run_command("git clone https://github.com/dan-da/hd-wallet-derive")
        
        if result != 0:
            logger.error("Failed to clone hd-wallet-derive")
            return False
            
        # Install hd-wallet-derive
        os.chdir("hd-wallet-derive")
        result = run_command("php -r \"readfile('https://getcomposer.org/installer');\" | php")
        
        if result != 0:
            logger.error("Failed to download composer")
            return False
            
        result = run_command("php composer.phar install")
        
        if result != 0:
            logger.error("Failed to install composer dependencies")
            return False
            
        # Change back to project root
        os.chdir("../../..")
    
    # Create symlink
    derive_symlink = f"{wallet_repo_path}/wallet/derive"
    if not os.path.exists(derive_symlink):
        logger.info("Creating symlink for derive...")
        
        # Change directory to wallet folder
        os.chdir(f"{wallet_repo_path}/wallet")
        
        # Create symlink
        if os.name == 'posix':  # Unix/Linux/Mac
            result = run_command(f"ln -s {wallet_derive_path}/hd-wallet-derive.php derive")
        else:  # Windows
            result = run_command(f"mklink derive {wallet_derive_path}\\hd-wallet-derive.php")
            
        if result != 0:
            logger.error("Failed to create symlink")
            return False
            
        # Change back to project root
        os.chdir("../..")
    
    logger.info("Multi-Blockchain Wallet setup completed successfully")
    return True

def create_mnemonic_env():
    """Create .env file with mnemonic if it doesn't exist"""
    if not os.path.exists(".env"):
        logger.info("Creating .env file with mnemonic...")
        
        with open(".env", "w") as f:
            f.write('MNEMONIC="eager exercise miss ivory brief despair ranch brief common glide all manual"\n')
        
        logger.info(".env file created successfully")
    else:
        logger.info(".env file already exists")
    
    return True

def main():
    """Main installation function"""
    logger.info("Starting Multi-Blockchain Wallet installation...")
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        return 1
    
    # Setup multichain wallet
    if not setup_multichain_wallet():
        logger.error("Failed to setup multichain wallet")
        return 1
    
    # Create .env file with mnemonic
    if not create_mnemonic_env():
        logger.error("Failed to create .env file")
        return 1
    
    logger.info("Installation completed successfully!")
    logger.info("You can now use the Multi-Blockchain Wallet to store your crypto assets.")
    return 0

if __name__ == "__main__":
    sys.exit(main())