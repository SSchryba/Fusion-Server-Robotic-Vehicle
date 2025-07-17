"""
Task Observer for Autonomous AI Agent Framework

Monitors agent activities, logs outcomes, collects metrics,
and provides observability into agent behavior and performance.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid

from .planner import Task, TaskStatus, ExecutionPlan
from .executor import ExecutionResult
from .critic import CriticEvaluation

logger = logging.getLogger(__name__)


class ObservationLevel(Enum):
    """Observation detail levels"""
    MINIMAL = "minimal"      # Basic status changes only
    NORMAL = "normal"        # Standard monitoring
    DETAILED = "detailed"    # Comprehensive monitoring
    DEBUG = "debug"         # Maximum detail for debugging


class EventType(Enum):
    """Types of events to observe"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    PLAN_CREATED = "plan_created"
    PLAN_COMPLETED = "plan_completed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EVALUATION_COMPLETED = "evaluation_completed"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    ERROR_OCCURRED = "error_occurred"
    DIRECTIVE_VIOLATION = "directive_violation"
    MEMORY_STORED = "memory_stored"
    ACTION_EXECUTED = "action_executed"


@dataclass
class ObservationEvent:
    """Represents an observed event"""
    id: str
    event_type: EventType
    timestamp: datetime
    source: str  # Component that generated the event
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObservationEvent':
        """Create event from dictionary."""
        return cls(
            id=data['id'],
            event_type=EventType(data['event_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data.get('data', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class PerformanceMetrics:
    """Performance metrics collected over time"""
    timestamp: datetime
    agent_uptime: float  # seconds
    memory_usage: float  # MB
    cpu_usage: float     # percentage
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_task_time: float
    success_rate: float
    memory_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


class TaskObserver:
    """
    Observes and logs agent activities for monitoring,
    debugging, and performance analysis.
    """
    
    def __init__(self, config_manager, memory_system):
        """
        Initialize the task observer.
        
        Args:
            config_manager: Configuration manager instance
            memory_system: Memory system for storing observations
        """
        self.config_manager = config_manager
        self.memory_system = memory_system
        
        # Observer configuration
        self.observer_config = config_manager.get_section('modules').get('observer', {})
        self.enabled = self.observer_config.get('enabled', True)
        self.detailed_logging = self.observer_config.get('detailed_logging', True)
        self.metrics_collection = self.observer_config.get('metrics_collection', True)
        
        # Observation settings
        self.observation_level = ObservationLevel.NORMAL
        self.log_directory = Path(config_manager.get('storage.logs_directory', './logs'))
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Event storage
        self.events: List[ObservationEvent] = []
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.max_events_memory = 1000
        
        # Metrics tracking
        self.metrics_history: List[PerformanceMetrics] = []
        self.start_time = datetime.now()
        
        # Task tracking
        self.task_registry: Dict[str, Task] = {}
        self.execution_tracking: Dict[str, Dict[str, Any]] = {}
        
        # Setup logging
        self._setup_logging()
        
        if self.enabled:
            logger.info("Task Observer initialized and monitoring started")
        else:
            logger.info("Task Observer initialized but monitoring is disabled")
            
    def _setup_logging(self):
        """Setup file logging for observations."""
        try:
            # Create observation log file
            log_file = self.log_directory / f"agent_observations_{datetime.now().strftime('%Y%m%d')}.log"
            
            # Setup file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add to logger
            obs_logger = logging.getLogger('observer')
            obs_logger.addHandler(file_handler)
            obs_logger.setLevel(logging.INFO)
            
            self.obs_logger = obs_logger
            
        except Exception as e:
            logger.warning(f"Failed to setup observation logging: {e}")
            self.obs_logger = logger
            
    def set_observation_level(self, level: ObservationLevel):
        """Set the observation detail level."""
        self.observation_level = level
        logger.info(f"Observation level set to: {level.value}")
        
    def register_event_handler(self, event_type: EventType, handler: Callable):
        """Register a handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type.value}")
        
    def observe_event(self, event_type: EventType, source: str, 
                     data: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Record an observation event."""
        if not self.enabled:
            return
            
        event = ObservationEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            data=data or {},
            metadata=metadata or {}
        )
        
        # Store event
        self.events.append(event)
        
        # Limit memory usage
        if len(self.events) > self.max_events_memory:
            self.events = self.events[-self.max_events_memory:]
            
        # Log event based on observation level
        self._log_event(event)
        
        # Store in persistent memory
        self._store_event_memory(event)
        
        # Trigger event handlers
        self._trigger_event_handlers(event)
        
    def _log_event(self, event: ObservationEvent):
        """Log event based on observation level."""
        if self.observation_level == ObservationLevel.MINIMAL:
            if event.event_type in [EventType.TASK_COMPLETED, EventType.TASK_FAILED, 
                                  EventType.PLAN_COMPLETED, EventType.ERROR_OCCURRED]:
                self.obs_logger.info(f"[{event.event_type.value}] {event.source}")
                
        elif self.observation_level == ObservationLevel.NORMAL:
            if event.event_type not in [EventType.MEMORY_STORED]:  # Skip noisy events
                self.obs_logger.info(f"[{event.event_type.value}] {event.source}: {event.data}")
                
        elif self.observation_level in [ObservationLevel.DETAILED, ObservationLevel.DEBUG]:
            event_str = json.dumps(event.to_dict(), indent=2 if self.observation_level == ObservationLevel.DEBUG else None)
            self.obs_logger.info(f"Event: {event_str}")
            
    def _store_event_memory(self, event: ObservationEvent):
        """Store event in persistent memory."""
        try:
            if self.detailed_logging:
                memory_content = f"Agent event: {event.event_type.value} from {event.source}"
                
                self.memory_system.store_memory(
                    content=memory_content,
                    memory_type='observation_event',
                    metadata={
                        'event_id': event.id,
                        'event_type': event.event_type.value,
                        'source': event.source,
                        'event_data': event.data,
                        'timestamp': event.timestamp.isoformat()
                    },
                    importance=self._calculate_event_importance(event)
                )
                
        except Exception as e:
            logger.warning(f"Failed to store event memory: {e}")
            
    def _calculate_event_importance(self, event: ObservationEvent) -> float:
        """Calculate importance score for an event."""
        importance_map = {
            EventType.ERROR_OCCURRED: 0.9,
            EventType.DIRECTIVE_VIOLATION: 0.9,
            EventType.TASK_FAILED: 0.8,
            EventType.PLAN_COMPLETED: 0.7,
            EventType.EVALUATION_COMPLETED: 0.6,
            EventType.TASK_COMPLETED: 0.5,
            EventType.TASK_STARTED: 0.3,
            EventType.MEMORY_STORED: 0.2
        }
        
        return importance_map.get(event.event_type, 0.4)
        
    def _trigger_event_handlers(self, event: ObservationEvent):
        """Trigger registered event handlers."""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                asyncio.create_task(handler(event) if asyncio.iscoroutinefunction(handler) else handler(event))
            except Exception as e:
                logger.warning(f"Event handler failed for {event.event_type.value}: {e}")
                
    def observe_task_lifecycle(self, task: Task, status_change: str, 
                              additional_data: Optional[Dict[str, Any]] = None):
        """Observe task lifecycle events."""
        self.task_registry[task.id] = task
        
        event_type_map = {
            'created': EventType.TASK_CREATED,
            'started': EventType.TASK_STARTED,
            'completed': EventType.TASK_COMPLETED,
            'failed': EventType.TASK_FAILED,
            'cancelled': EventType.TASK_CANCELLED
        }
        
        event_type = event_type_map.get(status_change, EventType.TASK_STARTED)
        
        data = {
            'task_id': task.id,
            'task_title': task.title,
            'task_type': task.action_type,
            'priority': task.priority.value,
            'status': task.status.value
        }
        
        if additional_data:
            data.update(additional_data)
            
        self.observe_event(event_type, 'TaskPlanner', data)
        
    def observe_execution_result(self, task: Task, execution_result: ExecutionResult):
        """Observe task execution results."""
        data = {
            'task_id': task.id,
            'success': execution_result.success,
            'execution_time': execution_result.execution_time,
            'retry_count': execution_result.retry_count
        }
        
        if execution_result.error:
            data['error'] = execution_result.error
            
        if execution_result.result:
            data['result_size'] = len(str(execution_result.result))
            
        self.observe_event(EventType.EXECUTION_COMPLETED, 'TaskExecutor', data)
        
    def observe_evaluation(self, task: Task, evaluation: CriticEvaluation):
        """Observe task evaluation results."""
        data = {
            'task_id': task.id,
            'overall_score': evaluation.overall_score,
            'score_level': evaluation.score_level.value,
            'criteria_scores': evaluation.criteria_scores
        }
        
        self.observe_event(EventType.EVALUATION_COMPLETED, 'TaskCritic', data)
        
    def observe_plan_lifecycle(self, plan: ExecutionPlan, status_change: str):
        """Observe execution plan lifecycle."""
        event_type = EventType.PLAN_CREATED if status_change == 'created' else EventType.PLAN_COMPLETED
        
        data = {
            'plan_id': plan.id,
            'goal': plan.goal,
            'task_count': len(plan.tasks),
            'status': plan.status
        }
        
        if plan.estimated_total_duration:
            data['estimated_duration'] = plan.estimated_total_duration
            
        self.observe_event(event_type, 'TaskPlanner', data)
        
    def observe_error(self, source: str, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Observe error occurrences."""
        data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.observe_event(EventType.ERROR_OCCURRED, source, data)
        
    def observe_action_execution(self, action_type: str, success: bool, 
                                duration: float, additional_data: Optional[Dict[str, Any]] = None):
        """Observe action execution."""
        data = {
            'action_type': action_type,
            'success': success,
            'duration': duration
        }
        
        if additional_data:
            data.update(additional_data)
            
        self.observe_event(EventType.ACTION_EXECUTED, 'ActionSystem', data)
        
    def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            import psutil
            
            # System metrics
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            cpu_usage = psutil.Process().cpu_percent()
            
        except ImportError:
            memory_usage = 0.0
            cpu_usage = 0.0
            
        # Agent uptime
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Task metrics
        completed_tasks = len([t for t in self.task_registry.values() 
                             if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.task_registry.values() 
                          if t.status == TaskStatus.FAILED])
        active_tasks = len([t for t in self.task_registry.values() 
                          if t.status == TaskStatus.IN_PROGRESS])
        
        # Calculate average task time
        completed_with_times = [t for t in self.task_registry.values() 
                              if t.status == TaskStatus.COMPLETED and t.started_at and t.completed_at]
        
        if completed_with_times:
            avg_task_time = sum((t.completed_at - t.started_at).total_seconds() 
                              for t in completed_with_times) / len(completed_with_times)
        else:
            avg_task_time = 0.0
            
        # Success rate
        total_finished = completed_tasks + failed_tasks
        success_rate = completed_tasks / total_finished if total_finished > 0 else 0.0
        
        # Memory count
        memory_stats = self.memory_system.get_memory_stats()
        memory_count = memory_stats.get('total_memories', 0)
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            agent_uptime=uptime,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            average_task_time=avg_task_time,
            success_rate=success_rate,
            memory_count=memory_count
        )
        
        if self.metrics_collection:
            self.metrics_history.append(metrics)
            
            # Limit metrics history
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
                
        return metrics
        
    def get_events(self, event_type: Optional[EventType] = None, 
                  source: Optional[str] = None, 
                  since: Optional[datetime] = None,
                  limit: int = 100) -> List[ObservationEvent]:
        """Get events with optional filtering."""
        filtered_events = self.events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
            
        if source:
            filtered_events = [e for e in filtered_events if e.source == source]
            
        if since:
            filtered_events = [e for e in filtered_events if e.timestamp > since]
            
        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        return filtered_events[:limit]
        
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {'message': 'No recent metrics available'}
            
        # Calculate averages
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        
        latest_metrics = recent_metrics[-1]
        
        return {
            'period_hours': hours,
            'current_uptime': latest_metrics.agent_uptime,
            'average_memory_usage_mb': avg_memory,
            'average_cpu_usage_percent': avg_cpu,
            'active_tasks': latest_metrics.active_tasks,
            'completed_tasks': latest_metrics.completed_tasks,
            'failed_tasks': latest_metrics.failed_tasks,
            'success_rate': latest_metrics.success_rate,
            'average_task_time': latest_metrics.average_task_time,
            'total_memories': latest_metrics.memory_count,
            'metrics_collected': len(recent_metrics)
        }
        
    def get_event_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get event statistics for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp > cutoff]
        
        if not recent_events:
            return {'message': 'No recent events'}
            
        # Count events by type
        event_counts = {}
        for event in recent_events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
        # Count events by source
        source_counts = {}
        for event in recent_events:
            source = event.source
            source_counts[source] = source_counts.get(source, 0) + 1
            
        return {
            'period_hours': hours,
            'total_events': len(recent_events),
            'events_by_type': event_counts,
            'events_by_source': source_counts,
            'events_per_hour': len(recent_events) / hours
        }
        
    def generate_activity_report(self, hours: int = 24) -> str:
        """Generate a human-readable activity report."""
        performance = self.get_performance_summary(hours)
        event_stats = self.get_event_statistics(hours)
        
        report_lines = [
            f"Agent Activity Report - Last {hours} Hours",
            "=" * 50,
            "",
            "Performance Summary:",
            f"  Uptime: {performance.get('current_uptime', 0):.0f} seconds",
            f"  Memory Usage: {performance.get('average_memory_usage_mb', 0):.1f} MB",
            f"  CPU Usage: {performance.get('average_cpu_usage_percent', 0):.1f}%",
            f"  Active Tasks: {performance.get('active_tasks', 0)}",
            f"  Completed Tasks: {performance.get('completed_tasks', 0)}",
            f"  Failed Tasks: {performance.get('failed_tasks', 0)}",
            f"  Success Rate: {performance.get('success_rate', 0):.1%}",
            f"  Average Task Time: {performance.get('average_task_time', 0):.1f}s",
            "",
            "Event Summary:",
            f"  Total Events: {event_stats.get('total_events', 0)}",
            f"  Events per Hour: {event_stats.get('events_per_hour', 0):.1f}",
            ""
        ]
        
        # Add event breakdown
        events_by_type = event_stats.get('events_by_type', {})
        if events_by_type:
            report_lines.append("Events by Type:")
            for event_type, count in events_by_type.items():
                report_lines.append(f"  {event_type}: {count}")
            report_lines.append("")
            
        return "\n".join(report_lines)
        
    def export_observations(self, filepath: str, hours: Optional[int] = None):
        """Export observations to a file."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours) if hours else None
            events_to_export = self.get_events(since=cutoff, limit=10000)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(events_to_export),
                'time_period_hours': hours,
                'events': [event.to_dict() for event in events_to_export]
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Exported {len(events_to_export)} observations to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export observations: {e}")
            raise 