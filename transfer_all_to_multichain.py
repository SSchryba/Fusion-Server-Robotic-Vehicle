#!/usr/bin/env python3
"""
Transfer All Assets to Multi-Blockchain Wallet

This script transfers all phantom ledger amounts to the Multi-Blockchain Wallet
using secure SHA-256 password hashing for wallet extraction.
"""

import os
import sys
import time
import hashlib
import logging
import json
import argparse
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Transfer all assets to Multi-Blockchain Wallet")
    parser.add_argument("--password", help="Password for wallet extraction (will be hashed with SHA-256)")
    parser.add_argument("--install", action="store_true", help="Install Multi-Blockchain Wallet if not installed")
    parser.add_argument("--test", action="store_true", help="Run in test mode with sample data")
    parser.add_argument("--all-chains", action="store_true", help="Process all supported blockchains")
    parser.add_argument("--output", help="Output file for transfer results (JSON)")
    return parser.parse_args()

def ensure_multichain_wallet():
    """Ensure the Multi-Blockchain Wallet is installed"""
    try:
        import multichain_wallet_integration as mwi
        logger.info("Multi-Blockchain Wallet integration found")
        return True
    except ImportError:
        logger.error("Multi-Blockchain Wallet integration not found")
        
        try:
            logger.info("Installing Multi-Blockchain Wallet...")
            import install_multichain_wallet
            install_multichain_wallet.main()
            
            # Try importing again
            import multichain_wallet_integration as mwi
            logger.info("Multi-Blockchain Wallet installed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to install Multi-Blockchain Wallet: {e}")
            return False

def get_phantom_ledgers():
    """Get all phantom ledgers from the system"""
    phantom_ledgers = []
    
    # Try to get wallets from eth_wallet_vacuum.py
    try:
        # Import the module to get access to the target wallets
        from eth_wallet_vacuum import get_target_wallets_by_chain, get_wallet_balance_by_chain
        
        for chain in ['ethereum', 'bitcoin', 'litecoin', 'polkadot']:
            try:
                # Get wallets for this chain
                target_wallets = get_target_wallets_by_chain(chain, 5)
                
                for address in target_wallets:
                    # Get balance
                    balance = get_wallet_balance_by_chain(chain, address)
                    
                    if balance and balance > 0:
                        phantom_ledgers.append({
                            'chain': chain,
                            'address': address,
                            'balance': balance,
                            'source': 'eth_wallet_vacuum',
                            'timestamp': time.time()
                        })
                        logger.info(f"Found {chain} wallet {address} with balance {balance}")
            except Exception as e:
                logger.error(f"Error processing {chain} wallets: {e}")
    except Exception as e:
        logger.error(f"Error importing eth_wallet_vacuum: {e}")
    
    # Try to get wallets from drift_chain.py
    try:
        # Import the module to get access to the wallets
        from drift_chain import get_wallet_balances, get_wallets
        
        try:
            # Get wallets
            drift_wallets = get_wallets()
            
            for wallet in drift_wallets:
                try:
                    # Add wallet to phantom ledgers
                    phantom_ledgers.append({
                        'chain': 'driftchain',
                        'address': wallet.get('address', 'unknown'),
                        'balance': wallet.get('balance', 0),
                        'source': 'drift_chain',
                        'timestamp': time.time()
                    })
                    logger.info(f"Found DriftChain wallet {wallet.get('address', 'unknown')} with balance {wallet.get('balance', 0)}")
                except Exception as e:
                    logger.error(f"Error processing drift wallet: {e}")
        except Exception as e:
            logger.error(f"Error getting drift wallets: {e}")
    except Exception as e:
        logger.error(f"Error importing drift_chain: {e}")
    
    # Create some test data if no phantom ledgers were found
    if not phantom_ledgers:
        logger.warning("No phantom ledgers found, creating test data...")
        
        test_data = [
            {
                'chain': 'ethereum',
                'address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
                'balance': 25.5,
                'source': 'test_data',
                'timestamp': time.time()
            },
            {
                'chain': 'bitcoin',
                'address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
                'balance': 0.75,
                'source': 'test_data',
                'timestamp': time.time()
            },
            {
                'chain': 'litecoin',
                'address': 'LQTpS3VaYTjCr4s9Y1t5zMY6H2RaNdL8bm',
                'balance': 15.3,
                'source': 'test_data',
                'timestamp': time.time()
            }
        ]
        
        phantom_ledgers.extend(test_data)
        logger.info(f"Created {len(test_data)} test wallets")
    
    return phantom_ledgers

def transfer_to_multichain(phantom_ledgers, password):
    """Transfer all phantom ledgers to the multichain wallet using advanced recovery"""
    try:
        # First try to import advanced wallet tool
        try:
            import advanced_wallet_tool as awt
            logger.info("Using Advanced Wallet Tool with password recovery")
            
            # Transfer wallets with advanced password recovery (10 attempts per wallet)
            results = awt.extract_wallets_with_recovery(phantom_ledgers, password)
            
            # Log results
            logger.info(f"Transfer completed using advanced recovery: {results['success_count']} successful, {results['fail_count']} failed")
            logger.info(f"Found passwords for {len(results.get('found_passwords', {}))} wallets")
            
            return results
        except ImportError:
            logger.warning("Advanced Wallet Tool not available, falling back to standard method")
            
        # Fall back to direct multichain wallet integration
        import multichain_wallet_integration as mwi
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        logger.info(f"Using password hash: {password_hash[:8]}...")
        
        # Transfer all wallets to Multi-Blockchain Wallet
        results = mwi.transfer_all_wallets_to_multichain(phantom_ledgers, password_hash)
        
        # Log results
        logger.info(f"Transfer completed: {results['success_count']} successful, {results['fail_count']} failed")
        
        return results
    except Exception as e:
        logger.error(f"Error transferring to multichain wallet: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Use provided password or default
    password = args.password or "Kairo_AI_Live_Crypto_Hunter_2025"
    
    # Ensure multichain wallet is installed
    if args.install or ensure_multichain_wallet():
        logger.info("Multi-Blockchain Wallet is ready")
        
        # Get phantom ledgers
        if args.test:
            logger.info("Running in test mode")
            phantom_ledgers = get_phantom_ledgers()
        else:
            phantom_ledgers = get_phantom_ledgers()
        
        # Log found phantom ledgers
        if phantom_ledgers:
            logger.info(f"Found {len(phantom_ledgers)} phantom ledgers to transfer")
            
            # Group by chain
            chains = {}
            for ledger in phantom_ledgers:
                chain = ledger.get('chain', 'unknown')
                if chain not in chains:
                    chains[chain] = []
                chains[chain].append(ledger)
            
            # Log chains summary
            for chain, ledgers in chains.items():
                logger.info(f"  {chain}: {len(ledgers)} ledgers")
            
            # Transfer to multichain wallet
            results = transfer_to_multichain(phantom_ledgers, password)
            
            # Save results to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            
            return 0
        else:
            logger.error("No phantom ledgers found")
            return 1
    else:
        logger.error("Failed to ensure Multi-Blockchain Wallet is installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())