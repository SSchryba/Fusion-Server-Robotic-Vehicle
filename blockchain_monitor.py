import os
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BlockchainMonitor:
    """
    Hunter-Gatherer style monitoring for blockchain activities.
    
    This class monitors blockchain activities and maintains statistics on:
    - Block creation rates
    - Transaction volumes
    - Document operations
    - Broadcast activities
    - System performance metrics
    """
    
    def __init__(self):
        """Initialize the blockchain monitoring system."""
        self.data_dir = os.path.join(os.getcwd(), 'blockchain_stats')
        self._ensure_data_dir()
        
        # Initialize storage for metrics
        self.metrics = {
            'blocks': {
                'total': 0,
                'creation_times': [],
                'avg_mining_time': 0,
                'last_24h': 0
            },
            'documents': {
                'total': 0,
                'created': 0,
                'updated': 0,
                'merged': 0,
                'last_24h': {
                    'created': 0,
                    'updated': 0,
                    'merged': 0
                }
            },
            'broadcasts': {
                'total': 0,
                'ledger': 0,
                'transaction': 0,
                'other': 0,
                'last_24h': 0
            },
            'system': {
                'uptime': 0,
                'validation_success_rate': 100.0,
                'sync_success_rate': 100.0
            }
        }
        
        # Initialize event tracking
        self.events = []
        self.start_time = time.time()
        
        logger.info("Blockchain monitoring initialized")
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created blockchain stats directory at {self.data_dir}")
    
    def track_block_added(self, block_data: Dict[str, Any]):
        """
        Track when a new block is added to the chain.
        
        Args:
            block_data: Data about the newly added block
        """
        self.metrics['blocks']['total'] += 1
        
        # Calculate mining time if possible
        if len(self.metrics['blocks']['creation_times']) > 0:
            last_time = self.metrics['blocks']['creation_times'][-1]
            mining_time = block_data.get('timestamp', time.time()) - last_time
            
            # Update average mining time
            current_avg = self.metrics['blocks']['avg_mining_time']
            count = len(self.metrics['blocks']['creation_times'])
            self.metrics['blocks']['avg_mining_time'] = (current_avg * count + mining_time) / (count + 1)
        
        # Add this block's timestamp
        self.metrics['blocks']['creation_times'].append(block_data.get('timestamp', time.time()))
        
        # Track recent blocks
        if time.time() - block_data.get('timestamp', time.time()) < 86400:  # 24 hours
            self.metrics['blocks']['last_24h'] += 1
        
        # Record event
        self._record_event('block_added', block_data)
        
        # Save metrics
        self._save_metrics()
        
        logger.info(f"Tracked new block: #{block_data.get('index', '?')}")
    
    def track_document_operation(self, operation: str, document_data: Dict[str, Any]):
        """
        Track document operations (create, update, merge).
        
        Args:
            operation: Type of operation ('created', 'updated', 'merged')
            document_data: Data about the document operation
        """
        self.metrics['documents']['total'] += 1
        
        # Track specific operation
        if operation in ['created', 'updated', 'merged']:
            self.metrics['documents'][operation] += 1
            
            # Track recent operations
            if time.time() - document_data.get('timestamp', time.time()) < 86400:  # 24 hours
                self.metrics['documents']['last_24h'][operation] += 1
        
        # Record event
        self._record_event(f'document_{operation}', document_data)
        
        # Save metrics
        self._save_metrics()
        
        logger.info(f"Tracked document {operation}: {document_data.get('id', '?')}")
    
    def track_broadcast(self, broadcast_type: str, broadcast_data: Dict[str, Any]):
        """
        Track broadcast activities.
        
        Args:
            broadcast_type: Type of broadcast ('ledger', 'transaction', etc.)
            broadcast_data: Data about the broadcast
        """
        self.metrics['broadcasts']['total'] += 1
        
        # Track specific broadcast type
        if broadcast_type in ['ledger', 'transaction']:
            self.metrics['broadcasts'][broadcast_type] += 1
        else:
            self.metrics['broadcasts']['other'] += 1
            
        # Track recent broadcasts
        if time.time() - broadcast_data.get('timestamp', time.time()) < 86400:  # 24 hours
            self.metrics['broadcasts']['last_24h'] += 1
        
        # Record event
        self._record_event(f'broadcast_{broadcast_type}', broadcast_data)
        
        # Save metrics
        self._save_metrics()
        
        logger.info(f"Tracked {broadcast_type} broadcast: {broadcast_data.get('id', '?')}")
    
    def update_system_metrics(self, validation_success: bool = True, sync_success: bool = True):
        """
        Update system-level metrics.
        
        Args:
            validation_success: Whether blockchain validation was successful
            sync_success: Whether blockchain synchronization was successful
        """
        # Update uptime
        self.metrics['system']['uptime'] = time.time() - self.start_time
        
        # Update success rates (with exponential smoothing)
        alpha = 0.1  # Smoothing factor
        if not validation_success:
            self.metrics['system']['validation_success_rate'] = (
                (1 - alpha) * self.metrics['system']['validation_success_rate']
            )
        
        if not sync_success:
            self.metrics['system']['sync_success_rate'] = (
                (1 - alpha) * self.metrics['system']['sync_success_rate']
            )
        
        # Save metrics
        self._save_metrics()
        
        logger.info("Updated system metrics")
    
    def _record_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Record an event in the event timeline.
        
        Args:
            event_type: Type of event
            event_data: Data about the event
        """
        event = {
            'type': event_type,
            'timestamp': time.time(),
            'data': event_data
        }
        
        self.events.append(event)
        
        # Keep only the last 1000 events
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current blockchain metrics.
        
        Returns:
            Dictionary of all tracked metrics
        """
        return {
            'metrics': self.metrics,
            'timestamp': time.time(),
            'formatted_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent blockchain events, optionally filtered by type.
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional filter for event type
            
        Returns:
            List of events, newest first
        """
        if event_type:
            filtered_events = [e for e in self.events if e['type'] == event_type]
            return sorted(filtered_events, key=lambda e: e['timestamp'], reverse=True)[:limit]
        else:
            return sorted(self.events, key=lambda e: e['timestamp'], reverse=True)[:limit]
    
    def _save_metrics(self):
        """Save the current metrics to a file."""
        try:
            metrics_file = os.path.join(self.data_dir, 'metrics.json')
            with open(metrics_file, 'w') as f:
                json.dump(self.get_metrics(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def load_metrics(self) -> bool:
        """
        Load metrics from the saved file.
        
        Returns:
            True if metrics were loaded successfully, False otherwise
        """
        try:
            metrics_file = os.path.join(self.data_dir, 'metrics.json')
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    if 'metrics' in data:
                        self.metrics = data['metrics']
                        logger.info("Loaded metrics from file")
                        return True
            return False
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of blockchain activity.
        
        Returns:
            Report dictionary with detailed metrics and analysis
        """
        metrics = self.get_metrics()
        
        # Add derived metrics
        if len(self.metrics['blocks']['creation_times']) >= 2:
            blocks_last_hour = len([t for t in self.metrics['blocks']['creation_times'] 
                                   if time.time() - t < 3600])
            
            blocks_per_hour = blocks_last_hour if blocks_last_hour > 0 else (
                self.metrics['blocks']['total'] / 
                ((time.time() - self.start_time) / 3600) if time.time() > self.start_time else 0
            )
        else:
            blocks_per_hour = 0
        
        report = {
            'summary': {
                'total_blocks': self.metrics['blocks']['total'],
                'total_documents': self.metrics['documents']['total'],
                'total_broadcasts': self.metrics['broadcasts']['total'],
                'uptime_hours': round(self.metrics['system']['uptime'] / 3600, 2),
                'blocks_per_hour': round(blocks_per_hour, 2),
                'avg_mining_time_seconds': round(self.metrics['blocks']['avg_mining_time'], 2)
            },
            'recent_activity': {
                'blocks_24h': self.metrics['blocks']['last_24h'],
                'documents_24h': sum(self.metrics['documents']['last_24h'].values()),
                'broadcasts_24h': self.metrics['broadcasts']['last_24h']
            },
            'health': {
                'validation_success_rate': self.metrics['system']['validation_success_rate'],
                'sync_success_rate': self.metrics['system']['sync_success_rate']
            },
            'detailed_metrics': metrics['metrics'],
            'timestamp': metrics['timestamp'],
            'formatted_time': metrics['formatted_time']
        }
        
        # Save report
        try:
            report_file = os.path.join(self.data_dir, 'latest_report.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        return report

# Create a global instance
blockchain_monitor = BlockchainMonitor()

# Module-level functions
def record_drift_chain_operation(operation_data):
    """
    Record a DriftChain operation in the monitoring system.
    
    Args:
        operation_data: Details about the DriftChain operation
                        Can be a string operation name or a dictionary with more details
    """
    if isinstance(operation_data, str):
        # Convert string operation name to the expected dictionary format
        operation_data = {
            'operation': operation_data,
            'timestamp': time.time()
        }
    
    # Ensure operation_data has necessary fields
    if 'operation' not in operation_data:
        logger.warning("Missing 'operation' field in DriftChain operation data")
        operation_data['operation'] = 'unknown'
    
    if 'timestamp' not in operation_data:
        operation_data['timestamp'] = time.time()
    
    # Record the event using the global monitor instance
    event_data = {
        'type': 'drift_chain',
        'operation': operation_data['operation'],
        'timestamp': operation_data['timestamp'],
        'metadata': operation_data.get('metadata', {})
    }
    
    blockchain_monitor._record_event('drift_chain_operation', event_data)
    
    # Update specific metrics based on operation type
    if operation_data['operation'] == 'vacuum_release':
        logger.info("DriftChain vacuum mode released - Updating monitoring metrics")
    elif operation_data['operation'] == 'vacuum_cycle':
        logger.info("DriftChain vacuum mode cycled - Updating monitoring metrics")
    
    # Update system metrics to include DriftChain activity
    try:
        blockchain_monitor.update_system_metrics()
    except Exception as e:
        logger.error(f"Error updating system metrics after DriftChain operation: {e}")
    
    return True