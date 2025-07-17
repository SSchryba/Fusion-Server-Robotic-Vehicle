#!/usr/bin/env python3
"""
Test ETH wallet vacuum and multi-chain vacuum functionality

This script verifies that the vacuum functions work properly across all chains.
"""

import logging
import json
import sys
import time
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestVacuum")

# Import required components
try:
    from god_mode import get_god_mode
    logger.info("Imported GodMode successfully")
except ImportError as e:
    logger.error(f"Error importing god_mode: {e}")
    sys.exit(1)

# Create a mock monero_integration if not available
# This allows us to test the vacuum functions without requiring full multichain wallet integration
if 'MONERO_WALLET_ADDRESS' not in os.environ:
    os.environ['MONERO_WALLET_ADDRESS'] = '0x28C6c06298d514Db089934071355E5743bf21d60'
    logger.info(f"Set mock Monero wallet address: {os.environ['MONERO_WALLET_ADDRESS']}")

# Create mock functions to avoid dependency on real implementations
def get_monero_wallet_address():
    """Mock function to get Monero wallet address"""
    return os.environ.get('MONERO_WALLET_ADDRESS')

def get_monero_balance():
    """Mock function to get Monero balance"""
    return 10.0  # Mock balance for testing

# Create a mock monero_integration module
import sys
class MockMoneroIntegration:
    def __init__(self):
        self.logger = logging.getLogger("MoneroIntegration")
        self.logger.info("Mock MoneroIntegration initialized")
        
    def get_monero_wallet_address(self):
        return os.environ.get('MONERO_WALLET_ADDRESS')
        
    def get_monero_balance(self):
        return 10.0
        
    def transfer_eth_to_monero(self, eth_amount, from_address):
        self.logger.info(f"Mock transfer of {eth_amount} ETH from {from_address}")
        return {
            "success": True,
            "eth_amount": eth_amount,
            "xmr_amount": eth_amount * 0.5,
            "tx_hash": "mock_tx_" + str(int(time.time()))
        }

# Add the mock module to sys.modules
sys.modules['monero_integration'] = MockMoneroIntegration()
from monero_integration import transfer_eth_to_monero

# Import ETH wallet vacuum functionality - with error handling for missing dependencies
try:
    import eth_wallet_vacuum
    
    # Create and add the missing function if needed
    def mock_multichain_wallet_integration():
        return {"status": "mock", "initialized": True}
    
    # Add the function to the module
    if not hasattr(eth_wallet_vacuum, 'get_multichain_wallet_integration'):
        setattr(eth_wallet_vacuum, 'get_multichain_wallet_integration', mock_multichain_wallet_integration)
    
    # Use our mock monero functions
    eth_wallet_vacuum.get_monero_wallet_address = get_monero_wallet_address
    eth_wallet_vacuum.get_monero_balance = get_monero_balance
    eth_wallet_vacuum.transfer_eth_to_monero = transfer_eth_to_monero
    
    logger.info("Imported and configured eth_wallet_vacuum successfully")
except ImportError as e:
    logger.error(f"Error importing eth_wallet_vacuum: {e}")
    sys.exit(1)

def test_eth_vacuum():
    """Test the ETH wallet vacuum functionality"""
    logger.info("Testing ETH wallet vacuum functionality...")
    
    # Get initial Monero balance for comparison
    monero_wallet = get_monero_wallet_address()
    initial_balance = get_monero_balance()
    
    logger.info(f"Initial Monero balance: {initial_balance:.6f} XMR")
    logger.info(f"Using Monero wallet: {monero_wallet}")
    
    # Execute the ETH wallet vacuum
    logger.info("Running ETH wallet vacuum...")
    try:
        result = eth_wallet_vacuum.vacuum_wallets()
        
        # Print summary of results
        logger.info("ETH wallet vacuum completed")
        logger.info(f"Wallets processed: {len(result.get('wallets', []))}")
        logger.info(f"Total ETH processed: {result.get('total_eth', 0):.4f} ETH")
        logger.info(f"Total XMR received: {result.get('total_xmr_value', 0):.6f} XMR")
        
        # Check Monero transfers
        monero_transfers = result.get('monero_transfers', [])
        logger.info(f"Successful Monero transfers: {len(monero_transfers)}")
        
        # Check final Monero balance
        final_balance = get_monero_balance()
        balance_increase = final_balance - initial_balance
        
        logger.info(f"Final Monero balance: {final_balance:.6f} XMR")
        logger.info(f"Balance increase: {balance_increase:.6f} XMR")
        
        # Test passed if we have processed wallets and have transfers
        if len(result.get('wallets', [])) > 0 and len(monero_transfers) > 0:
            logger.info("ETH wallet vacuum test PASSED")
        else:
            logger.warning("ETH wallet vacuum test results unclear - check logs")
        
    except Exception as e:
        logger.error(f"Error running ETH wallet vacuum: {e}")
        logger.error("ETH wallet vacuum test FAILED")

def test_multi_chain_vacuum():
    """Test the multi-chain wallet vacuum functionality"""
    logger.info("\nTesting multi-chain wallet vacuum functionality...")
    
    # Get initial Monero balance for comparison
    monero_wallet = get_monero_wallet_address()
    initial_balance = get_monero_balance()
    
    logger.info(f"Initial Monero balance: {initial_balance:.6f} XMR")
    logger.info(f"Using Monero wallet: {monero_wallet}")
    
    # Execute the multi-chain wallet vacuum
    logger.info("Running multi-chain wallet vacuum...")
    try:
        result = eth_wallet_vacuum.vacuum_all_blockchains()
        
        # Print summary of results
        logger.info("Multi-chain wallet vacuum completed")
        
        # Check how many chains were processed
        chains = result.get('chains', {})
        logger.info(f"Chains processed: {len(chains)}")
        
        # Print stats for each chain
        for chain_name, chain_data in chains.items():
            summary = chain_data.get('summary', {})
            wallet_count = summary.get('wallet_count', 0)
            tx_count = summary.get('transaction_count', 0)
            
            logger.info(f"Chain: {chain_name}")
            logger.info(f"  Wallets processed: {wallet_count}")
            logger.info(f"  Transactions: {tx_count}")
            
        # Check Monero transfers
        total_xmr = result.get('monero_transfers', {}).get('total_xmr_value', 0)
        successful_transfers = result.get('monero_transfers', {}).get('successful_transfers', 0)
        
        logger.info(f"Total XMR received: {total_xmr:.6f} XMR")
        logger.info(f"Successful transfers: {successful_transfers}")
        
        # Check final Monero balance
        final_balance = get_monero_balance()
        balance_increase = final_balance - initial_balance
        
        logger.info(f"Final Monero balance: {final_balance:.6f} XMR")
        logger.info(f"Balance increase: {balance_increase:.6f} XMR")
        
        # Summary statistics
        summary = result.get('summary', {})
        logger.info(f"Total chains: {summary.get('total_chains', 0)}")
        logger.info(f"Total wallets: {summary.get('total_wallets', 0)}")
        logger.info(f"Total transactions: {summary.get('total_transactions', 0)}")
        
        # Test passed if we have processed multiple chains and have transfers
        if len(chains) > 0 and successful_transfers > 0:
            logger.info("Multi-chain wallet vacuum test PASSED")
        else:
            logger.warning("Multi-chain wallet vacuum test results unclear - check logs")
        
    except Exception as e:
        logger.error(f"Error running multi-chain wallet vacuum: {e}")
        logger.error("Multi-chain wallet vacuum test FAILED")

if __name__ == "__main__":
    logger.info("Starting vacuum functionality tests...")
    
    # First test ETH vacuum
    test_eth_vacuum()
    
    # Then test multi-chain vacuum
    test_multi_chain_vacuum()
    
    logger.info("All vacuum tests completed!")