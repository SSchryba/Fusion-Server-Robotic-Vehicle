#!/usr/bin/env python3
"""
Test the Advanced Wallet Tool

This script tests the advanced wallet tool's ability to recover wallet passwords
and extract wallets to the multi-blockchain wallet.
"""

import os
import time
import json
import logging
import hashlib
import argparse
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test Advanced Wallet Tool")
    parser.add_argument("--password", help="Known password to try first")
    parser.add_argument("--wallets", type=int, default=3, help="Number of test wallets to create")
    parser.add_argument("--chain", default="ethereum", help="Blockchain to use (ethereum, bitcoin, etc.)")
    parser.add_argument("--time-limit", type=int, default=60, help="Time limit in seconds for each wallet")
    parser.add_argument("--output", help="Output file for results (JSON)")
    return parser.parse_args()

def create_test_wallets(count: int, chain: str) -> List[Dict[str, Any]]:
    """Create test wallet data for testing recovery"""
    wallets = []
    
    # Some predefined test addresses
    ethereum_addresses = [
        '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
        '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111',
        '0xD3F81260a44A1df7A7269CF66Abd9c7e4f7CA2C9',
        '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        '0x2170Ed0880ac9A755fd29B2688956BD959F933F8'
    ]
    
    bitcoin_addresses = [
        'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
        '3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5',
        'bc1q32pnvz5c8lj2pn8v0e3cgs8mfr5yz7mu40qu9w',
        '1BoatSLRHtKNngkdXEeobR76b53LETtpyT',
        'bc1q3h2h0yme9dqeq7h0jvuhcd3hy5q082vuw5870k'
    ]
    
    # Get addresses based on chain
    if chain == 'ethereum':
        addresses = ethereum_addresses
    elif chain == 'bitcoin':
        addresses = bitcoin_addresses
    else:
        # Generate random addresses for other chains
        addresses = [f"{chain}_addr_{i}" for i in range(count)]
    
    # Create wallet data
    for i in range(min(count, len(addresses))):
        address = addresses[i]
        
        wallet_data = {
            'chain': chain,
            'address': address,
            'balance': 10.0 + i * 2.5,  # Random balance
            'transactions': [
                {
                    'hash': hashlib.sha256(f"tx_{address}_{j}".encode()).hexdigest(),
                    'value': 1.0 + j * 0.5,
                    'timestamp': time.time() - j * 86400  # j days ago
                } for j in range(3)  # 3 transactions per wallet
            ]
        }
        
        wallets.append(wallet_data)
    
    return wallets

def test_wallet_tool(wallets: List[Dict[str, Any]], known_password: Optional[str] = None, time_limit: int = 60) -> Dict[str, Any]:
    """Test the advanced wallet tool with given wallets"""
    try:
        # Import the advanced wallet tool
        import advanced_wallet_tool as awt
        
        # Modify the time limit in the extract_wallet method
        tool = awt.get_wallet_tool()
        
        # Test extraction with wallet recovery
        logger.info(f"Starting wallet recovery test with {len(wallets)} wallets")
        logger.info(f"Time limit per wallet: {time_limit} seconds")
        
        if known_password:
            logger.info(f"Using known password hint: {known_password}")
        
        # Start the extraction process
        start_time = time.time()
        results = awt.extract_wallets_with_recovery(wallets, known_password)
        total_time = time.time() - start_time
        
        # Add summary
        results['total_time'] = total_time
        results['wallets_tested'] = len(wallets)
        results['time_per_wallet'] = total_time / len(wallets) if wallets else 0
        
        logger.info(f"Test completed in {total_time:.1f} seconds")
        logger.info(f"Success rate: {results['success_rate'] * 100:.1f}%")
        
        return results
    except Exception as e:
        logger.error(f"Error testing wallet tool: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Create test wallets
    wallets = create_test_wallets(args.wallets, args.chain)
    logger.info(f"Created {len(wallets)} test wallets for {args.chain}")
    
    # Test the wallet tool
    results = test_wallet_tool(wallets, args.password, args.time_limit)
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    else:
        # Print results summary
        print("\nResults Summary:")
        print(f"Wallets tested: {results.get('wallets_tested', 0)}")
        print(f"Success count: {results.get('success_count', 0)}")
        print(f"Fail count: {results.get('fail_count', 0)}")
        print(f"Success rate: {results.get('success_rate', 0) * 100:.1f}%")
        print(f"Total time: {results.get('total_time', 0):.1f} seconds")
        print(f"Average time per wallet: {results.get('time_per_wallet', 0):.1f} seconds")
        
        # Print found passwords
        print("\nFound Passwords:")
        for address, password in results.get('found_passwords', {}).items():
            print(f"  {address}: {password}")
    
    return 0

if __name__ == "__main__":
    main()