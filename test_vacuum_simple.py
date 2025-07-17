#!/usr/bin/env python3
"""
Simple Test for ETH Wallet Vacuum and Multi-Chain Vacuum Functionality

This script performs a basic test of the vacuum functions without relying on
detailed wallet balance information.
"""

import os
import sys
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimpleVacuumTest")

# Check environment
if not os.environ.get('MONERO_WALLET_ADDRESS'):
    os.environ['MONERO_WALLET_ADDRESS'] = '0x28C6c06298d514Db089934071355E5743bf21d60'
    logger.info(f"Set MONERO_WALLET_ADDRESS to: {os.environ['MONERO_WALLET_ADDRESS']}")

# Import the functions we want to test
try:
    from eth_wallet_vacuum import vacuum_wallets, vacuum_all_blockchains
    logger.info("Successfully imported vacuum functions")
except ImportError as e:
    logger.error(f"Error importing vacuum functions: {e}")
    sys.exit(1)

def test_eth_vacuum():
    """
    Test the ETH wallet vacuum functionality.
    """
    logger.info("\n=== Testing ETH Wallet Vacuum ===")
    
    try:
        # Run the vacuum operation
        result = vacuum_wallets()
        
        # Check if we got a valid result
        if isinstance(result, dict):
            logger.info("ETH wallet vacuum executed successfully")
            
            # Log basic statistics
            wallets = result.get('wallets', [])
            transfers = result.get('monero_transfers', [])
            
            logger.info(f"Wallets processed: {len(wallets)}")
            logger.info(f"Monero transfers: {len(transfers)}")
            
            # Print first few wallets
            if wallets:
                logger.info("\nWallets processed (first 3):")
                for i, wallet in enumerate(wallets[:3]):
                    logger.info(f"  {wallet}")
            
            # Print first few transfers
            if transfers:
                logger.info("\nTransfers (first 3):")
                for i, transfer in enumerate(transfers[:3]):
                    logger.info(f"  {transfer}")
            
            return True
        else:
            logger.error(f"Unexpected result type: {type(result)}")
            return False
    
    except Exception as e:
        logger.error(f"Error in ETH wallet vacuum: {e}")
        return False

def test_all_chains_vacuum():
    """
    Test the multi-chain vacuum functionality.
    """
    logger.info("\n=== Testing Multi-Chain Vacuum ===")
    
    try:
        # Run the all chains vacuum
        result = vacuum_all_blockchains()
        
        # Check if we got a valid result
        if isinstance(result, dict):
            logger.info("Multi-chain vacuum executed successfully")
            
            # Log chains processed
            chains = result.get('chains', {})
            logger.info(f"Chains processed: {len(chains)}")
            
            # Print chains and stats
            if chains:
                logger.info("\nChain statistics:")
                for chain_name, chain_data in chains.items():
                    summary = chain_data.get('summary', {})
                    logger.info(f"  Chain: {chain_name}")
                    logger.info(f"    Wallets: {summary.get('wallet_count', 0)}")
                    logger.info(f"    Transactions: {summary.get('transaction_count', 0)}")
            
            # Print transfer summary
            monero_transfers = result.get('monero_transfers', {})
            logger.info("\nMonero transfer summary:")
            logger.info(f"  Total XMR: {monero_transfers.get('total_xmr_value', 0):.6f}")
            logger.info(f"  Successful transfers: {monero_transfers.get('successful_transfers', 0)}")
            
            return True
        else:
            logger.error(f"Unexpected result type: {type(result)}")
            return False
    
    except Exception as e:
        logger.error(f"Error in multi-chain vacuum: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting simplified vacuum tests...")
    
    # Test ETH vacuum
    eth_result = test_eth_vacuum()
    
    # Test multi-chain vacuum
    mc_result = test_all_chains_vacuum()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"ETH wallet vacuum: {'PASSED' if eth_result else 'FAILED'}")
    logger.info(f"Multi-chain vacuum: {'PASSED' if mc_result else 'FAILED'}")
    
    # Exit with appropriate code
    if eth_result and mc_result:
        logger.info("All tests PASSED!")
        sys.exit(0)
    else:
        logger.warning("Some tests FAILED!")
        sys.exit(1)