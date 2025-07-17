#!/usr/bin/env python3
"""
Test the WalletHunter functionality in GodMode

This script verifies that the wallet hunting capabilities are working properly
after implementing the hunt_wallet method.
"""

import logging
import json
import sys
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestWalletHunter")

# Import the GodMode component
try:
    from god_mode import get_god_mode
except ImportError as e:
    logger.error(f"Error importing god_mode: {e}")
    sys.exit(1)

try:
    from crypto_balance_scraper import CryptoBalanceScraper
except ImportError as e:
    logger.error(f"Error importing crypto_balance_scraper: {e}")
    sys.exit(1)

def test_wallet_hunter():
    """Test the WalletHunter functionality"""
    # Get the GodMode instance
    god_mode = get_god_mode()
    
    # Check if WalletHunter is enabled
    if not god_mode.wallet_hunter_enabled:
        logger.info("Enabling Wallet Hunter...")
        god_mode.activate_wallet_hunter()
    
    # Test hunting for wallets on different chains
    chains = ['ethereum', 'bitcoin', 'litecoin', 'polkadot']
    
    logger.info("Testing direct wallet hunting:")
    for chain in chains:
        # Test direct hunt_wallet call
        result = god_mode.wallet_hunter.hunt_wallet(
            chain=chain, 
            block_height=12345, 
            scan_id=f"test_{chain}_001"
        )
        
        if result:
            logger.info(f"Successfully hunted {chain} wallet: {result['address']}")
        else:
            logger.error(f"Failed to hunt {chain} wallet")
    
    # Now test through the crypto_balance_scraper
    logger.info("\nTesting wallet hunting through crypto_balance_scraper:")
    scraper = CryptoBalanceScraper()
    
    # Test scraping wallets
    for chain in chains:
        logger.info(f"Scraping {chain} wallets...")
        wallets = scraper.scrape_wallets(chain, count=2)
        
        if wallets:
            logger.info(f"Found {len(wallets)} {chain} wallets:")
            for wallet in wallets:
                logger.info(f"  {wallet['address']} - Balance: {wallet['balance']}")
        else:
            logger.error(f"Failed to scrape {chain} wallets")
    
    logger.info("\nWallet hunter test completed!")

if __name__ == "__main__":
    test_wallet_hunter()