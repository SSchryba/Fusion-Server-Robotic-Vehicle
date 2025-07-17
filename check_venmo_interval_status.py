#!/usr/bin/env python
"""
Check Venmo Interval Transfer Status

This script checks the status of the automated Venmo interval transfers
that run every 3.65 hours with $1000 USD intervals.
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from activity_scheduler import get_activity_scheduler
from venmo_integration import get_venmo_integration, get_venmo_godmode_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_interval_transfers_status():
    """
    Check the status of the Venmo interval transfers.
    """
    logger.info("Checking Venmo interval transfer status...")
    
    # Get the activity scheduler
    scheduler = get_activity_scheduler()
    
    # Get scheduler status with last run times
    scheduler_status = scheduler.get_status()
    
    # Extract Venmo interval transfer status from the scheduler
    last_transfer_time = scheduler_status.get('last_run_times', {}).get('venmo_interval_transfer', None)
    last_completed_time = scheduler_status.get('last_run_times', {}).get('venmo_interval_transfer_completed', None)
    
    # Initialize next_transfer_dt to None
    next_transfer_dt = None
    
    if last_transfer_time:
        # Convert timestamp to datetime
        last_transfer_dt = datetime.fromtimestamp(last_transfer_time)
        logger.info(f"Last Venmo interval transfer started: {last_transfer_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate next scheduled transfer
        next_transfer_dt = last_transfer_dt + timedelta(hours=3.65)
        logger.info(f"Next Venmo interval transfer scheduled: {next_transfer_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate time until next transfer
        now = datetime.now()
        time_until_next = next_transfer_dt - now
        hours, remainder = divmod(time_until_next.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if time_until_next.total_seconds() > 0:
            logger.info(f"Time until next transfer: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")
        else:
            logger.info("Next transfer is overdue. Check scheduler status.")
    else:
        logger.warning("No Venmo interval transfers have been run yet.")
    
    # Get Venmo API status
    venmo = get_venmo_integration()
    venmo_status = venmo.get_integration_status()
    
    # Get GodMode status
    godmode_status = get_venmo_godmode_status()
    
    # Display Venmo status
    if venmo_status.get('authenticated', False):
        logger.info("✅ Venmo API: Authenticated")
        logger.info(f"  - Account: {venmo_status.get('username', 'unknown')}")
        
        # If balance is available, show it
        balance = venmo_status.get('balance')
        if balance:
            logger.info(f"  - Balance: ${balance:.2f}")
    else:
        logger.info("❌ Venmo API: Not authenticated")
        logger.info(f"  - Error: {venmo_status.get('error', 'Unknown error')}")
        logger.info(f"  - ETH Fallback Enabled: {venmo_status.get('fallback_enabled', False)}")
    
    # Display GodMode status
    if godmode_status.get('enabled', False):
        logger.info("✅ GodMode protocol: Enabled")
        
        # If last activation time is available, show it
        last_activation = godmode_status.get('last_activation_time')
        if last_activation:
            last_activation_dt = datetime.fromtimestamp(last_activation)
            logger.info(f"  - Last activated: {last_activation_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info(f"  - Authentication level: {godmode_status.get('auth_level', 'unknown')}")
    else:
        logger.info("❌ GodMode protocol: Disabled")
    
    # Check for existing result files
    result_files = [f for f in os.listdir('.') if f.startswith('venmo_transfer_results_') and f.endswith('.json')]
    result_files.sort(reverse=True)  # Most recent first
    
    if result_files:
        logger.info(f"Found {len(result_files)} transfer result files:")
        
        # Show details of the most recent transfer
        most_recent = result_files[0]
        logger.info(f"Most recent transfer result: {most_recent}")
        
        try:
            with open(most_recent, 'r') as f:
                result_data = json.load(f)
                
            # Display summary information
            successful = result_data.get('successful_transfers', 0)
            failed = result_data.get('failed_transfers', 0)
            total_eth = result_data.get('total_eth_transferred', 0)
            total_usd = result_data.get('total_usd_value', 0)
            
            logger.info(f"  - Timestamp: {result_data.get('execution_timestamp', 'unknown')}")
            logger.info(f"  - Successful transfers: {successful}")
            logger.info(f"  - Failed transfers: {failed}")
            logger.info(f"  - Total ETH transferred: {total_eth}")
            logger.info(f"  - Total USD value: ${total_usd:.2f}")
            
            target_amount = result_data.get('target_usd_amount', 0)
            target_reached = result_data.get('target_usd_reached', False)
            logger.info(f"  - Target USD amount: ${target_amount:.2f}")
            logger.info(f"  - Target reached: {'Yes' if target_reached else 'No'}")
            
        except Exception as e:
            logger.error(f"Error reading result file: {e}")
    else:
        logger.info("No transfer result files found.")
    
    # Make sure to safely handle None for next_transfer_dt
    next_transfer_timestamp = None
    if next_transfer_dt is not None and last_transfer_time is not None:
        next_transfer_timestamp = next_transfer_dt.timestamp()

    return {
        'last_transfer_time': last_transfer_time,
        'next_transfer_time': next_transfer_timestamp,
        'venmo_status': venmo_status,
        'godmode_status': godmode_status,
        'result_files': result_files
    }

if __name__ == "__main__":
    check_interval_transfers_status()