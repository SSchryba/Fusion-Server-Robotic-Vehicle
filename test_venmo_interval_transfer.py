#!/usr/bin/env python
"""
Test Venmo Interval Transfer

This script tests the automated Venmo interval transfer functionality
that transfers funds in $1000 USD intervals every 3.65 hours.
"""

import time
import logging
import json
import argparse
from venmo_integration import transfer_assets_in_intervals
from blockchain_connector import record_blockchain_event
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_interval_transfer(amount_usd=1000.0, save_results=True):
    """
    Test the Venmo interval transfer with the specified USD amount.
    
    Args:
        amount_usd: Amount in USD to transfer in this interval
        save_results: Whether to save results to a file
        
    Returns:
        Transfer results dictionary
    """
    logger.info(f"TESTING: Venmo interval transfer with ${amount_usd} USD")
    
    # Calculate next scheduled transfer time (for logging purposes)
    next_scheduled = datetime.now() + timedelta(hours=3.65)
    logger.info(f"Next scheduled transfer would be at: {next_scheduled.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the transfer
    start_time = time.time()
    results = transfer_assets_in_intervals(amount_usd=amount_usd)
    end_time = time.time()
    
    # Log transfer duration
    duration = end_time - start_time
    logger.info(f"Transfer process completed in {duration:.2f} seconds")
    
    # Add timestamp to results for reference
    results['execution_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results['duration_seconds'] = duration
    
    # Record execution in blockchain for transparency
    record_blockchain_event({
        'type': 'venmo_interval_transfer_test',
        'timestamp': time.time(),
        'amount_usd': amount_usd,
        'execution_timestamp': results['execution_timestamp'],
        'duration': duration,
        'successful_transfers': results.get('successful_transfers', 0)
    })
    
    # Save results to file if requested
    if save_results:
        # Create filename with timestamp
        filename = f"venmo_transfer_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results to file: {e}")
    
    # Display summary information
    if results.get('successful_transfers', 0) > 0:
        logger.info("✅ Transfer Summary:")
        logger.info(f"  - Successful transfers: {results.get('successful_transfers', 0)}")
        logger.info(f"  - Total ETH transferred: {results.get('total_eth_transferred', 0)}")
        logger.info(f"  - Total USD value: ${results.get('total_usd_value', 0):.2f}")
        logger.info(f"  - USD target reached: {'Yes' if results.get('target_usd_reached', False) else 'No'}")
        logger.info(f"  - Success rate: {results.get('success_rate', 0):.1f}%")
    else:
        if 'critical_error' in results:
            logger.error(f"❌ Critical error: {results.get('critical_error')}")
        else:
            logger.warning("⚠️ No successful transfers - possibly no available funds")
            
        # Print errors if any
        errors = results.get('errors', [])
        if errors:
            logger.error(f"Transfer errors ({len(errors)}):")
            for i, error in enumerate(errors[:5]):  # Show max 5 errors
                wallet = error.get('wallet', 'unknown')
                err_msg = error.get('error', 'Unknown error')
                logger.error(f"  {i+1}. {wallet}: {err_msg}")
            
            if len(errors) > 5:
                logger.error(f"  ... and {len(errors) - 5} more errors.")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Venmo interval transfer functionality")
    parser.add_argument('--amount', type=float, default=1000.0, 
                        help="Amount in USD to transfer (default: $1000)")
    parser.add_argument('--no-save', action='store_true',
                        help="Don't save results to a file")
    
    args = parser.parse_args()
    
    # Run the test
    test_interval_transfer(amount_usd=args.amount, save_results=not args.no_save)