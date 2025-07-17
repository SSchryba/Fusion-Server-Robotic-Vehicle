#!/usr/bin/env python3
"""
Simple test for the GodMode wallet hunting functionality
"""

import sys
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import GodMode
try:
    from god_mode import get_god_mode
except ImportError as e:
    print(f"Error importing god_mode: {e}")
    sys.exit(1)

def test_hunt_wallet():
    """Test the hunt_wallet function in GodMode"""
    print("Testing wallet hunting functionality...")
    
    # Get GodMode instance
    gm = get_god_mode()
    
    # Make sure wallet hunter is enabled
    gm.activate_wallet_hunter()
    
    # Try to hunt ethereum wallet
    chain = "ethereum"
    block_height = 12345
    scan_id = f"test_{int(time.time())}"
    
    print(f"Hunting for {chain} wallet with scan_id: {scan_id}")
    
    # Execute the hunt_wallet function
    result = gm.wallet_hunter.hunt_wallet(
        chain=chain,
        block_height=block_height,
        scan_id=scan_id
    )
    
    # Print the result
    if result:
        print("Success! Found wallet:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("Failed to hunt wallet. Make sure wallet_hunter is enabled.")

if __name__ == "__main__":
    test_hunt_wallet()