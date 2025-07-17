"""
DriftChain Integration Module

This module integrates the DriftChain implementation with the core blockchain system.
It sets up event handlers and ensures DriftChain operations are properly synchronized
with the main blockchain operations.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from drift_chain import get_drift_chain
import blockchain_monitor
from fluxion import register_event_handler, emit_event
import database
import eth_wallet_vacuum

# Configure logging
logger = logging.getLogger(__name__)

def initialize_drift_chain() -> None:
    """
    Initialize the DriftChain integration and set up event handlers.
    """
    logger.info("Initializing DriftChain integration")
    
    # Register event handlers to update DriftChain when main blockchain events occur
    register_event_handler("block_added", _handle_block_added)
    register_event_handler("document_created", _handle_document_created)
    register_event_handler("document_updated", _handle_document_updated)
    register_event_handler("document_merged", _handle_document_merged)
    
    # Start the background task to periodically check DriftChain status
    _schedule_drift_chain_background_tasks()
    
    logger.info("DriftChain integration initialized")

def _handle_block_added(event_data: Dict[str, Any]) -> None:
    """
    Handle the block_added event by adding corresponding data to the DriftChain.
    
    Args:
        event_data: Details about the block that was added to the main blockchain
    """
    if event_data.get('source') == 'drift_chain':
        # Skip if the event originated from DriftChain to avoid circular updates
        return
    
    drift_data = {
        "block_reference": {
            "index": event_data.get("index"),
            "hash": event_data.get("hash"),
            "timestamp": event_data.get("timestamp")
        },
        "event_type": "block_added",
        "drift_timestamp": time.time()
    }
    
    drift_chain = get_drift_chain()
    new_block = drift_chain.add_block(drift_data)
    
    if new_block:
        logger.info(f"Added DriftChain block referencing main blockchain block {event_data.get('index')}")
        # Record the event
        database.save_drift_chain_event({
            "event_type": "block_added",
            "main_chain_block": event_data.get("index"),
            "drift_chain_block": new_block.index,
            "timestamp": new_block.timestamp,
            "status": "success"
        })
    else:
        logger.warning(f"Failed to add DriftChain block (vacuum mode active) for main blockchain block {event_data.get('index')}")
        # Record the failed attempt
        database.save_drift_chain_event({
            "event_type": "block_attempt_failed",
            "main_chain_block": event_data.get("index"),
            "reason": "vacuum_mode",
            "timestamp": time.time(),
            "status": "failed"
        })

def _handle_document_created(event_data: Dict[str, Any]) -> None:
    """
    Handle document_created event by recording it in DriftChain.
    
    Args:
        event_data: Information about the document that was created
    """
    drift_data = {
        "document_reference": {
            "id": event_data.get("document_id"),
            "author": event_data.get("author"),
            "timestamp": event_data.get("timestamp")
        },
        "event_type": "document_created",
        "drift_timestamp": time.time()
    }
    
    drift_chain = get_drift_chain()
    new_block = drift_chain.add_block(drift_data)
    
    if new_block:
        logger.info(f"Recorded document creation in DriftChain: {event_data.get('document_id')}")
        # Update blockchain monitoring
        blockchain_monitor.record_drift_chain_operation("document_created")

def _handle_document_updated(event_data: Dict[str, Any]) -> None:
    """
    Handle document_updated event by recording it in DriftChain.
    
    Args:
        event_data: Information about the document update
    """
    drift_data = {
        "document_reference": {
            "id": event_data.get("document_id"),
            "version": event_data.get("version", 0) + 1,
            "author": event_data.get("author"),
            "timestamp": event_data.get("timestamp")
        },
        "event_type": "document_updated",
        "drift_timestamp": time.time()
    }
    
    drift_chain = get_drift_chain()
    drift_chain.add_block(drift_data)
    logger.info(f"Recorded document update in DriftChain: {event_data.get('document_id')}")

def _handle_document_merged(event_data: Dict[str, Any]) -> None:
    """
    Handle document_merged event by recording it in DriftChain.
    
    Args:
        event_data: Information about the document merge
    """
    drift_data = {
        "document_reference": {
            "id": event_data.get("document_id"),
            "merged_from": event_data.get("external_source", "unknown"),
            "strategy": event_data.get("strategy", "default"),
            "author": event_data.get("author"),
            "timestamp": event_data.get("timestamp")
        },
        "event_type": "document_merged",
        "drift_timestamp": time.time()
    }
    
    drift_chain = get_drift_chain()
    drift_chain.add_block(drift_data)
    logger.info(f"Recorded document merge in DriftChain: {event_data.get('document_id')}")

def get_drift_chain_status() -> Dict[str, Any]:
    """
    Get the current status of the DriftChain.
    
    Returns:
        Dictionary with DriftChain status information
    """
    drift_chain = get_drift_chain()
    chain_data = drift_chain.get_chain_data()
    
    # Calculate human-readable vacuum release time
    vacuum_release_time = datetime.fromtimestamp(chain_data['vacuum_release_time']).strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate time until vacuum collapse
    time_until_release = max(0, chain_data['vacuum_release_time'] - time.time())
    days = int(time_until_release / 86400)
    hours = int((time_until_release % 86400) / 3600)
    minutes = int((time_until_release % 3600) / 60)
    
    return {
        "chain_length": chain_data['length'],
        "vacuum_mode": chain_data['vacuum_mode'],
        "vacuum_release_time": vacuum_release_time,
        "time_until_release": f"{days} days, {hours} hours, {minutes} minutes",
        "is_valid": chain_data['valid'],
        "last_block_time": datetime.fromtimestamp(chain_data['last_block_time']).strftime('%Y-%m-%d %H:%M:%S'),
        "genesis_time": datetime.fromtimestamp(chain_data['genesis_time']).strftime('%Y-%m-%d %H:%M:%S'),
    }
    
def get_drift_chain_blocks() -> Dict[str, Any]:
    """
    Get all blocks in the DriftChain.
    
    Returns:
        Dictionary with blocks and related metadata
    """
    drift_chain = get_drift_chain()
    blocks = [block.to_dict() for block in drift_chain.chain]
    
    # Include event type and metadata for each block if available
    for block in blocks:
        if 'data' in block and block['data']:
            # Extract event type if it exists
            if isinstance(block['data'], dict) and 'event_type' in block['data']:
                block['event_type'] = block['data']['event_type']
            else:
                block['event_type'] = "unknown"
    
    return {
        "blocks": blocks,
        "count": len(blocks),
        "vacuum_mode": drift_chain.vacuum_mode
    }

def add_drift_chain_block(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Manually add a block to the DriftChain.
    
    Args:
        data: Data to store in the block
        
    Returns:
        Block data if successful, None if in vacuum mode
    """
    drift_chain = get_drift_chain()
    
    # Add custom metadata
    data['manual_addition'] = True
    data['addition_timestamp'] = time.time()
    
    new_block = drift_chain.add_block(data)
    
    if new_block:
        logger.info(f"Manually added block to DriftChain: {new_block.index}")
        return new_block.to_dict()
    else:
        logger.warning("Failed to add block to DriftChain (vacuum mode active)")
        return None

def trigger_vacuum_release() -> Dict[str, Any]:
    """
    Trigger an immediate release of the DriftChain vacuum mode.
    This will allow blocks to be added to the DriftChain without waiting for the
    normal vacuum release time.
    
    Returns:
        Dictionary with updated vacuum status
    """
    drift_chain = get_drift_chain()
    
    # Save the old vacuum status for the event log
    old_status = {
        'vacuum_mode': drift_chain.vacuum_mode,
        'vacuum_release_time': drift_chain.vacuum_release_time,
    }
    
    # Force vacuum mode off
    drift_chain.vacuum_mode = False
    drift_chain.vacuum_release_time = time.time()
    
    logger.info("DriftChain vacuum mode manually released")
    
    # Record the event in the database
    event_data = {
        'event_type': 'vacuum_release',
        'status': 'success',
        'details': {
            'old_vacuum_mode': old_status['vacuum_mode'],
            'old_release_time': old_status['vacuum_release_time'],
            'new_vacuum_mode': drift_chain.vacuum_mode,
            'new_release_time': drift_chain.vacuum_release_time,
            'manual_trigger': True
        }
    }
    
    try:
        database.save_drift_chain_event(event_data)
    except Exception as e:
        logger.error(f"Error saving vacuum release event: {e}")
    
    # Emit event for other components to react to
    emit_event('drift_chain_vacuum_released', event_data)
    
    try:
        blockchain_monitor.record_drift_chain_operation({
            'operation': 'vacuum_release',
            'timestamp': time.time(),
            'metadata': event_data['details']
        })
    except Exception as e:
        logger.error(f"Error recording vacuum release in monitor: {e}")
    
    # Perform ETH wallet vacuum operation after vacuum release
    logger.info("Initiating ETH wallet vacuum after vacuum release")
    try:
        wallet_vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain({
            'operation': 'vacuum_release',
            'vacuum_mode': drift_chain.vacuum_mode,
            'timestamp': time.time()
        })
        
        # Record vacuum results in database
        database.save_drift_chain_event({
            'event_type': 'eth_wallet_vacuum',
            'status': 'success',
            'details': {
                'triggered_by': 'vacuum_release',
                'wallets_scanned': len(wallet_vacuum_results.get('eth_wallets', {}).get('wallets', [])),
                'timestamp': time.time()
            }
        })
        
        logger.info(f"ETH wallet vacuum completed, scanned {len(wallet_vacuum_results.get('eth_wallets', {}).get('wallets', []))} wallets")
    except Exception as e:
        logger.error(f"Error during ETH wallet vacuum: {e}")
        database.save_drift_chain_event({
            'event_type': 'eth_wallet_vacuum',
            'status': 'failed',
            'details': {
                'triggered_by': 'vacuum_release',
                'error': str(e),
                'timestamp': time.time()
            }
        })
    
    return {
        'vacuum_mode': drift_chain.vacuum_mode,
        'vacuum_release_time': drift_chain.vacuum_release_time,
        'status': 'success'
    }

def cycle_vacuum_mode(sync_with_datastream: bool = True, vacuum_days: int = 1) -> Dict[str, Any]:
    """
    Cycle the DriftChain vacuum mode based on data stream activity.
    
    This function toggles the vacuum mode state and synchronizes with data stream
    activities. When sync_with_datastream is True, the function will analyze recent
    data stream activity and adjust the vacuum cycle dynamically based on activity levels.
    
    Args:
        sync_with_datastream: Whether to sync vacuum cycling with data stream activity
        vacuum_days: Number of days for vacuum mode if re-enabled (ignored if sync_with_datastream is True)
    
    Returns:
        Dictionary with updated vacuum status and sync metrics
    """
    drift_chain = get_drift_chain()
    
    # Save the current state for event logging
    current_state = {
        'vacuum_mode': drift_chain.vacuum_mode,
        'vacuum_release_time': drift_chain.vacuum_release_time,
    }
    
    # Get data stream activity metrics to determine optimal vacuum cycling
    stream_activity = {}
    if sync_with_datastream:
        # Calculate activity from proxy router and blockchain
        try:
            # Count recent proxy router activities
            session = database.get_session()
            recent_hours = 24
            cutoff_time = datetime.utcnow() - timedelta(hours=recent_hours)
            
            # Get proxy activity count
            proxy_count = session.query(database.ProxyActivity).filter(
                database.ProxyActivity.timestamp > cutoff_time
            ).count()
            
            # Get block additions in the last day
            block_count = session.query(database.Block).filter(
                database.Block.timestamp > cutoff_time.timestamp()
            ).count()
            
            # Get document operations count
            doc_count = session.query(database.Document).filter(
                database.Document.created_at > cutoff_time.timestamp()
            ).count()
            
            # Calculate total stream activity volume
            stream_activity = {
                'proxy_activities': proxy_count,
                'new_blocks': block_count,
                'document_operations': doc_count,
                'total_activity': proxy_count + block_count + doc_count
            }
            
            # Determine vacuum days based on activity level
            activity_level = stream_activity['total_activity']
            if activity_level > 100:
                vacuum_days = 0  # 12 hours for high activity (set to 0 for now, we'll convert to hours later)
            elif activity_level > 50:
                vacuum_days = 1  # 1 day for medium activity
            elif activity_level > 10:
                vacuum_days = 2  # 2 days for low activity
            else:
                vacuum_days = 3  # 3 days for very low activity
                
            session.close()
        except Exception as e:
            logger.error(f"Error analyzing data stream activity: {e}")
            # Default to 1 day if analysis fails
            vacuum_days = 1
    
    # Toggle vacuum mode
    if drift_chain.vacuum_mode:
        # If in vacuum mode, release it
        drift_chain.vacuum_mode = False
        drift_chain.vacuum_release_time = time.time()
        logger.info("DriftChain vacuum mode released through cycling")
    else:
        # If not in vacuum mode, enable it
        drift_chain.vacuum_mode = True
        drift_chain.vacuum_release_time = time.time() + (vacuum_days * 86400)  # days in seconds
        logger.info(f"DriftChain vacuum mode enabled through cycling for {vacuum_days} days")
    
    # Record the event in the database
    event_data = {
        'event_type': 'vacuum_cycle',
        'status': 'success',
        'details': {
            'old_vacuum_mode': current_state['vacuum_mode'],
            'old_release_time': current_state['vacuum_release_time'],
            'new_vacuum_mode': drift_chain.vacuum_mode,
            'new_release_time': drift_chain.vacuum_release_time,
            'sync_with_datastream': sync_with_datastream,
            'vacuum_days': vacuum_days,
            'stream_activity': stream_activity
        }
    }
    
    try:
        database.save_drift_chain_event(event_data)
    except Exception as e:
        logger.error(f"Error saving vacuum cycle event: {e}")
    
    # Emit event for other components to react to
    emit_event('drift_chain_vacuum_cycled', event_data)
    
    try:
        blockchain_monitor.record_drift_chain_operation({
            'operation': 'vacuum_cycle',
            'timestamp': time.time(),
            'metadata': {
                'new_state': drift_chain.vacuum_mode,
                'sync_with_datastream': sync_with_datastream,
                'activity_metrics': stream_activity
            }
        })
    except Exception as e:
        logger.error(f"Error recording vacuum cycle in monitor: {e}")
    
    # Run ETH wallet vacuum process if vacuum mode was disabled (released)
    if not drift_chain.vacuum_mode:
        logger.info("Initiating ETH wallet vacuum after vacuum cycle release")
        try:
            wallet_vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain({
                'operation': 'vacuum_cycle',
                'vacuum_mode': drift_chain.vacuum_mode,
                'vacuum_days': vacuum_days,
                'timestamp': time.time()
            })
            
            # Record vacuum results in database
            database.save_drift_chain_event({
                'event_type': 'eth_wallet_vacuum',
                'status': 'success',
                'details': {
                    'triggered_by': 'vacuum_cycle',
                    'wallets_scanned': len(wallet_vacuum_results.get('eth_wallets', {}).get('wallets', [])),
                    'timestamp': time.time()
                }
            })
            
            logger.info(f"ETH wallet vacuum completed after cycle, scanned {len(wallet_vacuum_results.get('eth_wallets', {}).get('wallets', []))} wallets")
        except Exception as e:
            logger.error(f"Error during ETH wallet vacuum after cycle: {e}")
            database.save_drift_chain_event({
                'event_type': 'eth_wallet_vacuum',
                'status': 'failed',
                'details': {
                    'triggered_by': 'vacuum_cycle',
                    'error': str(e),
                    'timestamp': time.time()
                }
            })
    
    return {
        'vacuum_mode': drift_chain.vacuum_mode,
        'vacuum_release_time': drift_chain.vacuum_release_time,
        'vacuum_days': vacuum_days,
        'sync_with_datastream': sync_with_datastream,
        'stream_activity': stream_activity,
        'status': 'success'
    }

def _schedule_drift_chain_background_tasks() -> None:
    """
    Schedule DriftChain maintenance tasks to run in the background.
    """
    # These tasks should be scheduled using the existing scheduler
    # For now we'll just validate on a periodic basis
    drift_chain = get_drift_chain()
    is_valid = drift_chain.is_valid()
    
    if is_valid:
        logger.info(f"DriftChain validation successful. Chain length: {len(drift_chain.chain)}")
    else:
        logger.error(f"DriftChain validation failed. Chain length: {len(drift_chain.chain)}")
        
        # Emit an error event to be handled by the main system
        emit_event("error_occurred", {
            "source": "drift_chain",
            "error_type": "validation_failed",
            "timestamp": time.time(),
            "details": "DriftChain integrity check failed"
        })