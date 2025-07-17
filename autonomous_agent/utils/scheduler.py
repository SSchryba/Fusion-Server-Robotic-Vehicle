"""
Agent Scheduler for Autonomous AI Agent Framework

Manages background tasks, periodic evaluations, and automated triggers
for continuous agent operation and self-improvement.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import inspect

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduled tasks"""
    INTERVAL = "interval"      # Run every X seconds
    CRON = "cron"             # Run at specific times
    TRIGGER = "trigger"       # Run when condition is met
    ONE_TIME = "one_time"     # Run once at specified time


@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    id: str
    name: str
    function: Callable
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    trigger_condition: Optional[Callable] = None
    scheduled_time: Optional[datetime] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'interval_seconds': self.interval_seconds,
            'cron_expression': self.cron_expression,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'max_runs': self.max_runs,
            'timeout_seconds': self.timeout_seconds,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat()
        }


class AgentScheduler:
    """
    Manages scheduled tasks and background operations for the autonomous agent.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the agent scheduler.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        
        # Scheduler configuration
        self.scheduler_config = config_manager.get_section('scheduler')
        self.enabled = self.scheduler_config.get('enabled', True)
        self.check_interval = self.scheduler_config.get('check_interval_seconds', 30)
        self.max_pending_tasks = self.scheduler_config.get('max_pending_tasks', 100)
        
        # Trigger configuration
        triggers = self.scheduler_config.get('triggers', {})
        self.failure_retry_delay = triggers.get('failure_retry_delay', 300)
        self.goal_reassessment_interval = triggers.get('goal_reassessment_interval', 3600)
        self.memory_cleanup_interval = triggers.get('memory_cleanup_interval', 86400)
        
        # Task management
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Task execution tracking
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Register default tasks
        self._register_default_tasks()
        
        logger.info(f"Agent Scheduler initialized - Enabled: {self.enabled}")
        
    def _register_default_tasks(self):
        """Register default scheduled tasks."""
        # Goal reassessment task
        self.schedule_interval_task(
            "goal_reassessment",
            "Periodic goal and directive reassessment",
            self._reassess_goals,
            self.goal_reassessment_interval
        )
        
        # Memory cleanup task
        self.schedule_interval_task(
            "memory_cleanup",
            "Clean up old and low-importance memories",
            self._cleanup_memory,
            self.memory_cleanup_interval
        )
        
        # Performance monitoring task
        self.schedule_interval_task(
            "performance_monitoring",
            "Monitor agent performance metrics",
            self._monitor_performance,
            300  # Every 5 minutes
        )
        
        # Health check task
        self.schedule_interval_task(
            "health_check",
            "Check agent component health",
            self._health_check,
            600  # Every 10 minutes
        )
        
    async def start(self):
        """Start the scheduler."""
        if not self.enabled:
            logger.info("Scheduler is disabled")
            return
            
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting agent scheduler...")
        self.running = True
        
        # Start the main scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Agent scheduler started successfully")
        
    async def stop(self):
        """Stop the scheduler gracefully."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
            
        logger.info("Stopping agent scheduler...")
        self.running = False
        
        # Cancel scheduler task
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
                
        # Cancel active executions
        for task_id, execution_task in list(self.active_executions.items()):
            logger.info(f"Cancelling active task: {task_id}")
            execution_task.cancel()
            try:
                await execution_task
            except asyncio.CancelledError:
                pass
                
        self.active_executions.clear()
        
        logger.info("Agent scheduler stopped")
        
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def _check_and_execute_tasks(self):
        """Check for tasks ready to execute and run them."""
        now = datetime.now()
        
        for task in list(self.tasks.values()):
            if not task.enabled:
                continue
                
            if task.id in self.active_executions:
                continue  # Already running
                
            should_run = False
            
            # Check if task should run
            if task.schedule_type == ScheduleType.INTERVAL:
                if task.next_run is None or now >= task.next_run:
                    should_run = True
                    
            elif task.schedule_type == ScheduleType.ONE_TIME:
                if task.scheduled_time and now >= task.scheduled_time:
                    should_run = True
                    
            elif task.schedule_type == ScheduleType.TRIGGER:
                if task.trigger_condition and await self._evaluate_trigger(task.trigger_condition):
                    should_run = True
                    
            elif task.schedule_type == ScheduleType.CRON:
                # Simplified cron - would need full cron parser for production
                if task.next_run is None or now >= task.next_run:
                    should_run = True
                    
            # Execute task if ready
            if should_run:
                # Check max runs
                if task.max_runs and task.run_count >= task.max_runs:
                    logger.info(f"Task {task.id} reached max runs ({task.max_runs})")
                    task.enabled = False
                    continue
                    
                # Execute task
                execution_task = asyncio.create_task(self._execute_task(task))
                self.active_executions[task.id] = execution_task
                
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing scheduled task: {task.name}")
            
            # Update task state
            task.last_run = start_time
            task.run_count += 1
            
            # Calculate next run time
            if task.schedule_type == ScheduleType.INTERVAL and task.interval_seconds:
                task.next_run = start_time + timedelta(seconds=task.interval_seconds)
            elif task.schedule_type == ScheduleType.ONE_TIME:
                task.enabled = False  # Disable one-time tasks after execution
                
            # Execute the task function
            if inspect.iscoroutinefunction(task.function):
                result = await asyncio.wait_for(task.function(), timeout=task.timeout_seconds)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(task.function), 
                    timeout=task.timeout_seconds
                )
                
            # Record successful execution
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.execution_history.append({
                'task_id': task.id,
                'task_name': task.name,
                'start_time': start_time.isoformat(),
                'execution_time': execution_time,
                'success': True,
                'result': str(result)[:500] if result else None
            })
            
            # Reset retry count on success
            task.retry_count = 0
            
            logger.info(f"Task {task.name} completed successfully in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task.name} timed out after {task.timeout_seconds}s")
            await self._handle_task_failure(task, "Timeout")
            
        except asyncio.CancelledError:
            logger.info(f"Task {task.name} was cancelled")
            raise
            
        except Exception as e:
            logger.error(f"Task {task.name} failed: {str(e)}")
            await self._handle_task_failure(task, str(e))
            
        finally:
            # Remove from active executions
            if task.id in self.active_executions:
                del self.active_executions[task.id]
                
    async def _handle_task_failure(self, task: ScheduledTask, error: str):
        """Handle task execution failure."""
        execution_time = (datetime.now() - task.last_run).total_seconds() if task.last_run else 0
        
        # Record failed execution
        self.execution_history.append({
            'task_id': task.id,
            'task_name': task.name,
            'start_time': task.last_run.isoformat() if task.last_run else None,
            'execution_time': execution_time,
            'success': False,
            'error': error
        })
        
        # Handle retries
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Schedule retry
            retry_delay = self.failure_retry_delay * task.retry_count  # Exponential backoff
            task.next_run = datetime.now() + timedelta(seconds=retry_delay)
            logger.info(f"Task {task.name} will retry in {retry_delay}s (attempt {task.retry_count}/{task.max_retries})")
        else:
            # Max retries exceeded
            logger.error(f"Task {task.name} failed after {task.max_retries} retries - disabling")
            task.enabled = False
            
    async def _evaluate_trigger(self, trigger_condition: Callable) -> bool:
        """Evaluate a trigger condition."""
        try:
            if inspect.iscoroutinefunction(trigger_condition):
                return await trigger_condition()
            else:
                return trigger_condition()
        except Exception as e:
            logger.error(f"Trigger evaluation failed: {e}")
            return False
            
    def schedule_interval_task(self, task_id: str, name: str, function: Callable,
                              interval_seconds: int, enabled: bool = True) -> ScheduledTask:
        """
        Schedule a task to run at regular intervals.
        
        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            function: Function to execute
            interval_seconds: Interval between executions
            enabled: Whether task is enabled
            
        Returns:
            ScheduledTask instance
        """
        task = ScheduledTask(
            id=task_id,
            name=name,
            function=function,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
            enabled=enabled,
            next_run=datetime.now() + timedelta(seconds=interval_seconds)
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled interval task: {name} (every {interval_seconds}s)")
        
        return task
        
    def schedule_one_time_task(self, task_id: str, name: str, function: Callable,
                              scheduled_time: datetime) -> ScheduledTask:
        """
        Schedule a task to run once at a specific time.
        
        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            function: Function to execute
            scheduled_time: When to execute the task
            
        Returns:
            ScheduledTask instance
        """
        task = ScheduledTask(
            id=task_id,
            name=name,
            function=function,
            schedule_type=ScheduleType.ONE_TIME,
            scheduled_time=scheduled_time
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled one-time task: {name} at {scheduled_time}")
        
        return task
        
    def schedule_trigger_task(self, task_id: str, name: str, function: Callable,
                             trigger_condition: Callable) -> ScheduledTask:
        """
        Schedule a task to run when a condition is met.
        
        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            function: Function to execute
            trigger_condition: Condition function that returns bool
            
        Returns:
            ScheduledTask instance
        """
        task = ScheduledTask(
            id=task_id,
            name=name,
            function=function,
            schedule_type=ScheduleType.TRIGGER,
            trigger_condition=trigger_condition
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled trigger task: {name}")
        
        return task
        
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.enabled = False
            
            # Cancel if currently running
            if task_id in self.active_executions:
                self.active_executions[task_id].cancel()
                
            logger.info(f"Cancelled task: {task.name}")
            return True
            
        return False
        
    def remove_task(self, task_id: str) -> bool:
        """Remove a task completely."""
        if task_id in self.tasks:
            self.cancel_task(task_id)
            del self.tasks[task_id]
            logger.info(f"Removed task: {task_id}")
            return True
            
        return False
        
    # Default scheduled task implementations
    async def _reassess_goals(self):
        """Reassess agent goals and directives."""
        logger.info("Performing goal reassessment...")
        
        # This would integrate with the directive manager and memory system
        # to evaluate current goals and suggest improvements
        
        # Placeholder implementation
        return {"reassessment": "completed", "timestamp": datetime.now().isoformat()}
        
    async def _cleanup_memory(self):
        """Clean up old and low-importance memories."""
        logger.info("Performing memory cleanup...")
        
        # This would integrate with the memory system to remove
        # old or low-importance memories
        
        # Placeholder implementation
        return {"cleanup": "completed", "timestamp": datetime.now().isoformat()}
        
    async def _monitor_performance(self):
        """Monitor agent performance metrics."""
        logger.info("Monitoring performance...")
        
        # This would collect and analyze performance metrics
        # from all agent components
        
        # Placeholder implementation
        return {"monitoring": "completed", "timestamp": datetime.now().isoformat()}
        
    async def _health_check(self):
        """Check health of agent components."""
        logger.info("Performing health check...")
        
        # This would check the status of all agent components
        # and report any issues
        
        # Placeholder implementation
        return {"health": "all_systems_operational", "timestamp": datetime.now().isoformat()}
        
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        active_tasks = [task for task in self.tasks.values() if task.enabled]
        recent_executions = self.execution_history[-20:] if self.execution_history else []
        
        return {
            'running': self.running,
            'enabled': self.enabled,
            'total_tasks': len(self.tasks),
            'active_tasks': len(active_tasks),
            'executing_tasks': len(self.active_executions),
            'recent_executions': len(recent_executions),
            'check_interval_seconds': self.check_interval,
            'tasks': [task.to_dict() for task in active_tasks]
        }
        
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:] if self.execution_history else [] 