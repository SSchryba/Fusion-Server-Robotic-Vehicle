"""
Main Autonomous Agent for Autonomous AI Agent Framework

Orchestrates all components including planning, execution, criticism,
observation, memory, and safety systems to create a complete
autonomous AI agent.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import signal
import sys

from .config_manager import ConfigManager
from .directive import DirectiveManager
from ..memory.vector_store import VectorMemory
from ..modules.planner import TaskPlanner, ExecutionPlan, Task, TaskStatus
from ..modules.executor import TaskExecutor, ExecutionResult, ExecutionMode
from ..modules.critic import TaskCritic, CriticEvaluation
from ..modules.observer import TaskObserver, EventType
from ..actions.action_system import ActionSystem
from ..safeguards.safety_manager import SafetyManager

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """
    Main autonomous agent that coordinates all subsystems
    to achieve goals independently with adaptive feedback loops.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the autonomous agent.
        
        Args:
            config_path: Path to configuration file
        """
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.agent_config = self.config_manager.agent_config
        
        # Agent state
        self.running = False
        self.start_time = None
        self.current_goal = None
        self.active_plan = None
        
        # Initialize core components
        self._initialize_components()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info(f"Autonomous Agent '{self.agent_config.name}' initialized")
        
    def _initialize_components(self):
        """Initialize all agent components."""
        try:
            # Core systems
            self.directive_manager = DirectiveManager(self.config_manager)
            self.memory_system = VectorMemory(self.config_manager)
            
            # Safety and actions
            self.safety_manager = SafetyManager(self.config_manager)
            self.action_system = ActionSystem(self.config_manager, self.safety_manager)
            
            # Processing modules
            self.planner = TaskPlanner(
                self.config_manager, 
                self.directive_manager, 
                self.memory_system
            )
            self.executor = TaskExecutor(
                self.config_manager,
                self.directive_manager,
                self.action_system,
                self.memory_system
            )
            self.critic = TaskCritic(
                self.config_manager,
                self.directive_manager,
                self.memory_system
            )
            self.observer = TaskObserver(
                self.config_manager,
                self.memory_system
            )
            
            # Register event handlers
            self._setup_event_handlers()
            
            logger.info("All agent components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent components: {e}")
            raise
            
    def _setup_event_handlers(self):
        """Setup event handlers for component interactions."""
        # Task lifecycle events
        self.observer.register_event_handler(
            EventType.TASK_COMPLETED,
            self._handle_task_completed
        )
        
        self.observer.register_event_handler(
            EventType.TASK_FAILED,
            self._handle_task_failed
        )
        
        self.observer.register_event_handler(
            EventType.ERROR_OCCURRED,
            self._handle_error_occurred
        )
        
        self.observer.register_event_handler(
            EventType.DIRECTIVE_VIOLATION,
            self._handle_directive_violation
        )
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def start(self):
        """Start the autonomous agent."""
        if self.running:
            logger.warning("Agent is already running")
            return
            
        logger.info("Starting autonomous agent...")
        
        try:
            self.running = True
            self.start_time = datetime.now()
            
            # Record agent start event
            self.observer.observe_event(EventType.AGENT_STARTED, 'AutonomousAgent')
            
            # Store startup memory
            self.memory_system.store_memory(
                content=f"Agent startup at {self.start_time.isoformat()}",
                memory_type='agent_lifecycle',
                metadata={
                    'event': 'startup',
                    'agent_name': self.agent_config.name,
                    'version': self.agent_config.version
                },
                importance=0.8
            )
            
            logger.info(f"Agent '{self.agent_config.name}' started successfully")
            
            # Start background tasks
            await self._start_background_tasks()
            
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the autonomous agent gracefully."""
        if not self.running:
            logger.warning("Agent is not running")
            return
            
        logger.info("Stopping autonomous agent...")
        
        try:
            self.running = False
            
            # Cancel active plan if any
            if self.active_plan:
                await self._cancel_active_plan()
                
            # Record agent stop event
            self.observer.observe_event(EventType.AGENT_STOPPED, 'AutonomousAgent')
            
            # Store shutdown memory
            uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            self.memory_system.store_memory(
                content=f"Agent shutdown after {uptime:.1f} seconds uptime",
                memory_type='agent_lifecycle',
                metadata={
                    'event': 'shutdown',
                    'uptime_seconds': uptime,
                    'graceful': True
                },
                importance=0.8
            )
            
            # Cleanup resources
            self.action_system.cleanup()
            
            logger.info("Agent stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during agent shutdown: {e}")
            
    async def pursue_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pursue a high-level goal autonomously.
        
        Args:
            goal: Goal description
            context: Additional context for goal achievement
            
        Returns:
            Dictionary with goal pursuit results
        """
        if not self.running:
            return {'success': False, 'error': 'Agent is not running'}
            
        logger.info(f"Pursuing goal: {goal}")
        
        try:
            self.current_goal = goal
            start_time = datetime.now()
            
            # Create execution plan
            plan = self.planner.create_plan(goal, context)
            self.active_plan = plan
            
            # Observe plan creation
            self.observer.observe_plan_lifecycle(plan, 'created')
            
            # Execute plan with adaptive feedback
            execution_results = await self._execute_plan_adaptively(plan)
            
            # Evaluate overall goal achievement
            goal_evaluation = await self._evaluate_goal_achievement(goal, plan, execution_results)
            
            # Store goal pursuit memory
            pursuit_time = (datetime.now() - start_time).total_seconds()
            self.memory_system.store_memory(
                content=f"Goal pursuit: {goal}",
                memory_type='goal_pursuit',
                metadata={
                    'goal': goal,
                    'success': goal_evaluation['success'],
                    'plan_id': plan.id,
                    'execution_time': pursuit_time,
                    'task_count': len(plan.tasks),
                    'context': context or {}
                },
                importance=0.9 if goal_evaluation['success'] else 0.7
            )
            
            # Clear current state
            self.current_goal = None
            self.active_plan = None
            
            return goal_evaluation
            
        except Exception as e:
            logger.error(f"Goal pursuit failed: {e}")
            self.observer.observe_error('AutonomousAgent', e, {'goal': goal})
            
            return {
                'success': False,
                'error': str(e),
                'goal': goal
            }
            
    async def _execute_plan_adaptively(self, plan: ExecutionPlan) -> List[ExecutionResult]:
        """Execute plan with adaptive feedback and replanning."""
        all_results = []
        max_replanning_attempts = 3
        replanning_count = 0
        
        while not plan.is_complete() and replanning_count < max_replanning_attempts:
            # Get ready tasks
            ready_tasks = plan.get_ready_tasks()
            
            if not ready_tasks:
                if plan.has_failed_tasks():
                    # Attempt replanning for failed tasks
                    failed_tasks = [t for t in plan.tasks if t.status == TaskStatus.FAILED]
                    
                    if replanning_count < max_replanning_attempts:
                        logger.info(f"Replanning due to {len(failed_tasks)} failed tasks")
                        
                        for failed_task in failed_tasks[:2]:  # Limit replanning scope
                            alternative_tasks = self.planner.replan_task(
                                plan.id, 
                                failed_task.id, 
                                failed_task.error or "Task execution failed"
                            )
                            
                            if alternative_tasks:
                                logger.info(f"Created {len(alternative_tasks)} alternative tasks")
                                
                        replanning_count += 1
                        continue
                    else:
                        logger.warning("Maximum replanning attempts reached")
                        break
                else:
                    # No ready tasks and no failures - plan may be complete
                    break
                    
            # Execute ready tasks
            if ready_tasks:
                # Choose execution mode based on task dependencies
                execution_mode = ExecutionMode.PARALLEL if len(ready_tasks) > 1 else ExecutionMode.SEQUENTIAL
                
                # Execute tasks
                execution_results = await self.executor.execute_tasks(ready_tasks, execution_mode)
                all_results.extend(execution_results)
                
                # Process results and provide feedback
                for i, result in enumerate(execution_results):
                    task = ready_tasks[i]
                    
                    # Update task status in planner
                    if result.success:
                        self.planner.update_task_status(plan.id, task.id, TaskStatus.COMPLETED, result.result)
                    else:
                        self.planner.update_task_status(plan.id, task.id, TaskStatus.FAILED, error=result.error)
                        
                    # Observe execution result
                    self.observer.observe_execution_result(task, result)
                    
                    # Get critic evaluation
                    evaluation = self.critic.evaluate_task_execution(task, result)
                    self.observer.observe_evaluation(task, evaluation)
                    
                    # Learn from execution
                    if evaluation.overall_score < 0.5:
                        logger.warning(f"Poor task performance: {task.title} (score: {evaluation.overall_score:.2f})")
                        
                        # Consider adaptive improvements
                        await self._adapt_based_on_criticism(task, result, evaluation)
                        
        # Observe plan completion
        self.observer.observe_plan_lifecycle(plan, 'completed')
        
        return all_results
        
    async def _adapt_based_on_criticism(self, task: Task, result: ExecutionResult, evaluation: CriticEvaluation):
        """Adapt behavior based on critic evaluation."""
        try:
            # Store learning experience
            self.memory_system.store_memory(
                content=f"Learning from poor performance: {task.title}",
                memory_type='learning_experience',
                metadata={
                    'task_id': task.id,
                    'task_type': task.action_type,
                    'score': evaluation.overall_score,
                    'feedback': evaluation.feedback,
                    'recommendations': evaluation.recommendations,
                    'error': result.error
                },
                importance=0.8
            )
            
            # Apply immediate adaptations
            for recommendation in evaluation.recommendations:
                if 'timeout' in recommendation.lower():
                    # Increase timeout for similar tasks
                    task.estimated_duration = int((task.estimated_duration or 120) * 1.5)
                elif 'retry' in recommendation.lower():
                    # Increase retry count for similar tasks
                    task.max_retries = min(task.max_retries + 1, 5)
                elif 'validation' in recommendation.lower():
                    # Add validation step for similar tasks
                    pass  # Could add validation tasks dynamically
                    
        except Exception as e:
            logger.warning(f"Failed to adapt based on criticism: {e}")
            
    async def _evaluate_goal_achievement(self, goal: str, plan: ExecutionPlan, 
                                       execution_results: List[ExecutionResult]) -> Dict[str, Any]:
        """Evaluate whether the goal was achieved."""
        # Basic success metrics
        total_tasks = len(plan.tasks)
        successful_tasks = sum(1 for result in execution_results if result.success)
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Overall success determination
        goal_achieved = success_rate >= 0.7 and not plan.has_failed_tasks()
        
        # Calculate performance metrics
        total_time = sum(result.execution_time for result in execution_results)
        average_score = 0.0
        
        # Get critic evaluations for scoring
        evaluations = self.critic.evaluations[-len(execution_results):] if execution_results else []
        if evaluations:
            average_score = sum(eval.overall_score for eval in evaluations) / len(evaluations)
            
        return {
            'success': goal_achieved,
            'goal': goal,
            'plan_id': plan.id,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': success_rate,
            'total_execution_time': total_time,
            'average_performance_score': average_score,
            'execution_results': [
                {
                    'task_id': result.task_id,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'error': result.error
                }
                for result in execution_results
            ]
        }
        
    async def _cancel_active_plan(self):
        """Cancel the currently active plan."""
        if self.active_plan:
            # Cancel any running tasks
            for task in self.active_plan.tasks:
                if task.status == TaskStatus.IN_PROGRESS:
                    task.status = TaskStatus.CANCELLED
                    
            self.active_plan.status = "cancelled"
            logger.info(f"Cancelled active plan: {self.active_plan.id}")
            
    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks."""
        # Start resource monitoring
        asyncio.create_task(self._resource_monitoring_loop())
        
        # Start performance monitoring
        asyncio.create_task(self._performance_monitoring_loop())
        
    async def _resource_monitoring_loop(self):
        """Background resource monitoring."""
        while self.running:
            try:
                # Monitor system resources
                resource_status = await self.safety_manager.monitor_resources()
                
                if resource_status.get('anomaly_detected'):
                    logger.warning(f"Resource anomalies detected: {resource_status['anomalies']}")
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
                
    async def _performance_monitoring_loop(self):
        """Background performance monitoring."""
        while self.running:
            try:
                # Collect performance metrics
                metrics = self.observer.collect_performance_metrics()
                
                # Check for performance issues
                if metrics.success_rate < 0.5:
                    logger.warning(f"Low success rate detected: {metrics.success_rate:.2%}")
                    
                if metrics.average_task_time > 300:  # 5 minutes
                    logger.warning(f"High average task time: {metrics.average_task_time:.1f}s")
                    
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(300)
                
    async def _handle_task_completed(self, event):
        """Handle task completion events."""
        # Could implement learning or adaptation logic here
        pass
        
    async def _handle_task_failed(self, event):
        """Handle task failure events."""
        task_id = event.data.get('task_id')
        logger.warning(f"Task failed: {task_id}")
        
        # Could implement failure analysis and recovery logic here
        
    async def _handle_error_occurred(self, event):
        """Handle error events."""
        error_type = event.data.get('error_type')
        error_message = event.data.get('error_message')
        
        logger.error(f"System error: {error_type} - {error_message}")
        
        # Could implement error recovery logic here
        
    async def _handle_directive_violation(self, event):
        """Handle directive violation events."""
        logger.critical(f"Directive violation detected: {event.data}")
        
        # Could implement violation response logic here
        
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'running': self.running,
            'uptime_seconds': uptime,
            'agent_name': self.agent_config.name,
            'version': self.agent_config.version,
            'current_goal': self.current_goal,
            'active_plan_id': self.active_plan.id if self.active_plan else None,
            'directive_stats': self.directive_manager.get_evaluation_stats(),
            'memory_stats': self.memory_system.get_memory_stats(),
            'planning_stats': self.planner.get_planning_stats(),
            'execution_stats': self.executor.get_execution_stats(),
            'safety_status': self.safety_manager.get_safety_status(),
            'performance_summary': self.observer.get_performance_summary(24)
        }
        
    def get_agent_insights(self) -> Dict[str, Any]:
        """Get insights about agent performance and learning."""
        return {
            'performance_trends': self.critic.get_performance_trends(7),
            'improvement_areas': self.critic.identify_improvement_areas(),
            'recent_violations': [v.to_dict() for v in self.safety_manager.get_recent_violations(24)],
            'event_statistics': self.observer.get_event_statistics(24),
            'activity_report': self.observer.generate_activity_report(24)
        }
        
    async def pursue_goal_with_learning(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pursue a goal with enhanced learning and adaptation.
        
        This method extends basic goal pursuit with additional learning capabilities.
        """
        # Learn from similar past goals
        similar_goals = self.memory_system.retrieve_memories(
            goal, 
            limit=3, 
            memory_types=['goal_pursuit']
        )
        
        if similar_goals:
            logger.info(f"Found {len(similar_goals)} similar past goals for learning")
            
            # Extract lessons from past attempts
            for memory in similar_goals:
                past_data = memory.metadata
                if not past_data.get('success', False):
                    # Learn from past failures
                    logger.info(f"Learning from past failure: {memory.content}")
                    
        # Pursue the goal
        result = await self.pursue_goal(goal, context)
        
        # Enhanced post-goal analysis
        if not result['success']:
            # Analyze failure patterns
            failure_analysis = await self._analyze_goal_failure(goal, result)
            result['failure_analysis'] = failure_analysis
            
        return result
        
    async def _analyze_goal_failure(self, goal: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze goal failure to extract learning insights."""
        try:
            # Get failed execution results
            failed_executions = [
                er for er in result.get('execution_results', [])
                if not er['success']
            ]
            
            # Identify common failure patterns
            failure_patterns = {}
            for execution in failed_executions:
                error = execution.get('error', 'Unknown error')
                # Simple pattern matching - could be enhanced with ML
                if 'timeout' in error.lower():
                    failure_patterns['timeout_issues'] = failure_patterns.get('timeout_issues', 0) + 1
                elif 'permission' in error.lower():
                    failure_patterns['permission_issues'] = failure_patterns.get('permission_issues', 0) + 1
                elif 'not found' in error.lower():
                    failure_patterns['resource_issues'] = failure_patterns.get('resource_issues', 0) + 1
                    
            return {
                'total_failures': len(failed_executions),
                'failure_patterns': failure_patterns,
                'recommendations': self._generate_failure_recommendations(failure_patterns)
            }
            
        except Exception as e:
            logger.error(f"Failure analysis error: {e}")
            return {'error': str(e)}
            
    def _generate_failure_recommendations(self, failure_patterns: Dict[str, int]) -> List[str]:
        """Generate recommendations based on failure patterns."""
        recommendations = []
        
        if failure_patterns.get('timeout_issues', 0) > 0:
            recommendations.append("Consider increasing timeout values for similar tasks")
            
        if failure_patterns.get('permission_issues', 0) > 0:
            recommendations.append("Review permission requirements and safety configurations")
            
        if failure_patterns.get('resource_issues', 0) > 0:
            recommendations.append("Validate resource availability before task execution")
            
        return recommendations 