"""
Task Planner for Autonomous AI Agent Framework

Breaks down high-level goals into actionable subtasks,
manages task dependencies, and creates execution plans.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task status values"""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a single task in the execution plan"""
    id: str
    title: str
    description: str
    action_type: str  # 'system_command', 'api_call', 'file_operation', etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    estimated_duration: Optional[int] = None  # seconds
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'action_type': self.action_type,
            'parameters': self.parameters,
            'priority': self.priority.value,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'estimated_duration': self.estimated_duration,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            action_type=data['action_type'],
            parameters=data.get('parameters', {}),
            priority=TaskPriority(data.get('priority', 'medium')),
            status=TaskStatus(data.get('status', 'pending')),
            dependencies=data.get('dependencies', []),
            estimated_duration=data.get('estimated_duration'),
            max_retries=data.get('max_retries', 3),
            retry_count=data.get('retry_count', 0),
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            result=data.get('result'),
            error=data.get('error'),
            tags=data.get('tags', [])
        )


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan"""
    id: str
    goal: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "planning"  # planning, ready, executing, completed, failed
    estimated_total_duration: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready_tasks = []
        completed_task_ids = {t.id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            dependencies_met = all(dep_id in completed_task_ids for dep_id in task.dependencies)
            
            if dependencies_met:
                task.status = TaskStatus.READY
                ready_tasks.append(task)
                
        return ready_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED] for task in self.tasks)
    
    def has_failed_tasks(self) -> bool:
        """Check if any tasks have failed."""
        return any(task.status == TaskStatus.FAILED for task in self.tasks)


class TaskPlanner:
    """
    Plans and organizes tasks to achieve high-level goals.
    Uses heuristics and patterns to break down complex objectives.
    """
    
    def __init__(self, config_manager, directive_manager, memory_system):
        """
        Initialize the task planner.
        
        Args:
            config_manager: Configuration manager instance
            directive_manager: Directive manager for goal alignment
            memory_system: Memory system for learning from past plans
        """
        self.config_manager = config_manager
        self.directive_manager = directive_manager
        self.memory_system = memory_system
        
        # Planning configuration
        self.planning_config = config_manager.get_section('modules').get('planner', {})
        self.max_subtasks = self.planning_config.get('max_subtasks', 10)
        self.planning_timeout = self.planning_config.get('planning_timeout', 60)
        self.use_llm = self.planning_config.get('use_llm', True)
        
        # Active plans
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.planning_patterns: Dict[str, List[str]] = {}
        
        # Load planning patterns from memory
        self._load_planning_patterns()
        
        logger.info("Task Planner initialized")
        
    def _load_planning_patterns(self):
        """Load successful planning patterns from memory."""
        try:
            pattern_memories = self.memory_system.get_memories_by_type('planning_pattern', limit=50)
            
            for memory in pattern_memories:
                pattern_data = memory.metadata.get('pattern_data', {})
                goal_type = pattern_data.get('goal_type', 'general')
                
                if goal_type not in self.planning_patterns:
                    self.planning_patterns[goal_type] = []
                    
                self.planning_patterns[goal_type].append(memory.content)
                
            logger.info(f"Loaded {len(pattern_memories)} planning patterns")
            
        except Exception as e:
            logger.warning(f"Failed to load planning patterns: {e}")
            
    def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create an execution plan for the given goal.
        
        Args:
            goal: High-level goal description
            context: Additional context for planning
            
        Returns:
            ExecutionPlan with tasks to achieve the goal
        """
        logger.info(f"Creating plan for goal: {goal}")
        
        # Create plan instance
        plan_id = str(uuid.uuid4())
        plan = ExecutionPlan(
            id=plan_id,
            goal=goal,
            description=f"Plan to achieve: {goal}",
            tags=self._extract_tags_from_goal(goal)
        )
        
        try:
            # Check directive alignment
            directive_eval = self.directive_manager.evaluate_action(
                f"Create plan for: {goal}",
                action_type="planning",
                context=context
            )
            
            if not directive_eval['allowed']:
                raise ValueError(f"Goal conflicts with directive: {directive_eval['violations']}")
                
            # Decompose goal into tasks
            tasks = self._decompose_goal(goal, context)
            
            # Add dependencies and ordering
            tasks = self._add_task_dependencies(tasks)
            
            # Estimate durations
            tasks = self._estimate_task_durations(tasks)
            
            # Optimize task order
            tasks = self._optimize_task_order(tasks)
            
            # Add tasks to plan
            plan.tasks = tasks
            plan.estimated_total_duration = sum(
                task.estimated_duration or 0 for task in tasks
            )
            plan.status = "ready"
            
            # Store plan
            self.active_plans[plan_id] = plan
            
            # Save planning experience to memory
            self._save_planning_experience(plan, goal, context)
            
            logger.info(f"Created plan with {len(tasks)} tasks")
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            plan.status = "failed"
            raise
            
    def _extract_tags_from_goal(self, goal: str) -> List[str]:
        """Extract relevant tags from goal description."""
        tags = []
        goal_lower = goal.lower()
        
        # Common goal categories
        if any(word in goal_lower for word in ['file', 'document', 'text']):
            tags.append('file_operation')
        if any(word in goal_lower for word in ['analyze', 'research', 'study']):
            tags.append('analysis')
        if any(word in goal_lower for word in ['create', 'generate', 'build']):
            tags.append('creation')
        if any(word in goal_lower for word in ['api', 'request', 'endpoint']):
            tags.append('api_operation')
        if any(word in goal_lower for word in ['data', 'information', 'collect']):
            tags.append('data_processing')
        if any(word in goal_lower for word in ['automate', 'schedule', 'recurring']):
            tags.append('automation')
            
        return tags
        
    def _decompose_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Decompose a high-level goal into actionable tasks."""
        tasks = []
        
        # Try to use learned patterns first
        pattern_tasks = self._apply_learned_patterns(goal, context)
        if pattern_tasks:
            tasks.extend(pattern_tasks)
        else:
            # Use heuristic decomposition
            tasks = self._heuristic_decomposition(goal, context)
            
        # Ensure we don't exceed max subtasks
        if len(tasks) > self.max_subtasks:
            tasks = self._consolidate_tasks(tasks)
            
        return tasks
        
    def _apply_learned_patterns(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Apply learned planning patterns to decompose the goal."""
        tasks = []
        
        # Find similar goals in memory
        similar_plans = self.memory_system.retrieve_memories(
            goal, 
            limit=5, 
            memory_types=['planning_experience']
        )
        
        if similar_plans:
            # Use the most similar successful plan as a template
            best_plan_memory = similar_plans[0]
            plan_data = best_plan_memory.metadata.get('plan_data', {})
            
            if plan_data and plan_data.get('success', False):
                template_tasks = plan_data.get('tasks', [])
                
                for i, template_task in enumerate(template_tasks):
                    task = Task(
                        id=str(uuid.uuid4()),
                        title=self._adapt_task_title(template_task.get('title', ''), goal),
                        description=self._adapt_task_description(template_task.get('description', ''), goal),
                        action_type=template_task.get('action_type', 'general'),
                        parameters=self._adapt_task_parameters(template_task.get('parameters', {}), context),
                        priority=TaskPriority(template_task.get('priority', 'medium')),
                        estimated_duration=template_task.get('estimated_duration'),
                        tags=['pattern_based']
                    )
                    tasks.append(task)
                    
                logger.info(f"Applied learned pattern with {len(tasks)} tasks")
                
        return tasks
        
    def _heuristic_decomposition(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Use heuristic rules to decompose a goal into tasks."""
        tasks = []
        goal_lower = goal.lower()
        
        # File operation goals
        if any(word in goal_lower for word in ['create file', 'write file', 'generate file']):
            tasks.extend(self._create_file_operation_tasks(goal, context))
            
        # Analysis goals
        elif any(word in goal_lower for word in ['analyze', 'research', 'study', 'investigate']):
            tasks.extend(self._create_analysis_tasks(goal, context))
            
        # API interaction goals
        elif any(word in goal_lower for word in ['api', 'request', 'endpoint', 'call']):
            tasks.extend(self._create_api_tasks(goal, context))
            
        # Data processing goals
        elif any(word in goal_lower for word in ['process data', 'transform', 'convert']):
            tasks.extend(self._create_data_processing_tasks(goal, context))
            
        # Automation goals
        elif any(word in goal_lower for word in ['automate', 'schedule', 'monitor']):
            tasks.extend(self._create_automation_tasks(goal, context))
            
        # General goal decomposition
        else:
            tasks.extend(self._create_general_tasks(goal, context))
            
        return tasks
        
    def _create_file_operation_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create tasks for file operations."""
        tasks = []
        
        # Validation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Validate File Operation Parameters",
            description="Validate file paths, permissions, and requirements",
            action_type="validation",
            parameters={"validation_type": "file_operation"},
            priority=TaskPriority.HIGH,
            estimated_duration=30
        ))
        
        # Main file operation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Execute File Operation",
            description=f"Perform the file operation: {goal}",
            action_type="file_operation",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=60,
            dependencies=[tasks[0].id]
        ))
        
        # Verification task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Verify File Operation",
            description="Verify the file operation was successful",
            action_type="verification",
            parameters={"verification_type": "file_operation"},
            priority=TaskPriority.MEDIUM,
            estimated_duration=30,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _create_analysis_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create tasks for analysis goals."""
        tasks = []
        
        # Data gathering task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Gather Information",
            description="Collect relevant data and information for analysis",
            action_type="data_gathering",
            parameters=context or {},
            priority=TaskPriority.HIGH,
            estimated_duration=300
        ))
        
        # Analysis task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Perform Analysis",
            description=f"Analyze the gathered data: {goal}",
            action_type="analysis",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=600,
            dependencies=[tasks[0].id]
        ))
        
        # Report generation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Generate Report",
            description="Compile analysis results into a report",
            action_type="report_generation",
            parameters={"format": "text"},
            priority=TaskPriority.LOW,
            estimated_duration=180,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _create_api_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create tasks for API interactions."""
        tasks = []
        
        # API validation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Validate API Parameters",
            description="Validate API endpoint, authentication, and parameters",
            action_type="api_validation",
            parameters=context or {},
            priority=TaskPriority.HIGH,
            estimated_duration=60
        ))
        
        # API call task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Execute API Call",
            description=f"Make the API call: {goal}",
            action_type="api_call",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=120,
            dependencies=[tasks[0].id]
        ))
        
        # Response processing task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Process API Response",
            description="Process and validate the API response",
            action_type="response_processing",
            parameters={},
            priority=TaskPriority.MEDIUM,
            estimated_duration=90,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _create_data_processing_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create tasks for data processing goals."""
        tasks = []
        
        # Data validation
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Validate Input Data",
            description="Validate the structure and quality of input data",
            action_type="data_validation",
            parameters=context or {},
            priority=TaskPriority.HIGH,
            estimated_duration=120
        ))
        
        # Data processing
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Process Data",
            description=f"Process the data: {goal}",
            action_type="data_processing",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=300,
            dependencies=[tasks[0].id]
        ))
        
        # Output validation
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Validate Output",
            description="Validate the processed data output",
            action_type="output_validation",
            parameters={},
            priority=TaskPriority.MEDIUM,
            estimated_duration=90,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _create_automation_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create tasks for automation goals."""
        tasks = []
        
        # Setup task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Setup Automation",
            description="Configure automation parameters and triggers",
            action_type="automation_setup",
            parameters=context or {},
            priority=TaskPriority.HIGH,
            estimated_duration=180
        ))
        
        # Implementation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Implement Automation",
            description=f"Implement the automation: {goal}",
            action_type="automation_implementation",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=300,
            dependencies=[tasks[0].id]
        ))
        
        # Testing task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Test Automation",
            description="Test the automation to ensure it works correctly",
            action_type="automation_testing",
            parameters={},
            priority=TaskPriority.HIGH,
            estimated_duration=150,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _create_general_tasks(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Create generic tasks for unspecified goals."""
        tasks = []
        
        # Planning task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Plan Approach",
            description=f"Plan the approach to achieve: {goal}",
            action_type="planning",
            parameters=context or {},
            priority=TaskPriority.HIGH,
            estimated_duration=120
        ))
        
        # Execution task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Execute Plan",
            description=f"Execute the planned approach: {goal}",
            action_type="execution",
            parameters=context or {},
            priority=TaskPriority.MEDIUM,
            estimated_duration=300,
            dependencies=[tasks[0].id]
        ))
        
        # Validation task
        tasks.append(Task(
            id=str(uuid.uuid4()),
            title="Validate Results",
            description="Validate that the goal was achieved",
            action_type="validation",
            parameters={"validation_type": "goal_achievement"},
            priority=TaskPriority.MEDIUM,
            estimated_duration=90,
            dependencies=[tasks[1].id]
        ))
        
        return tasks
        
    def _adapt_task_title(self, template_title: str, goal: str) -> str:
        """Adapt a template task title to the current goal."""
        # Simple adaptation - replace generic terms with goal-specific ones
        adapted = template_title
        
        # Extract key terms from goal
        goal_words = goal.lower().split()
        if goal_words:
            main_action = goal_words[0]
            adapted = adapted.replace("execute", main_action).replace("perform", main_action)
            
        return adapted
        
    def _adapt_task_description(self, template_desc: str, goal: str) -> str:
        """Adapt a template task description to the current goal."""
        return f"{template_desc} (adapted for: {goal})"
        
    def _adapt_task_parameters(self, template_params: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Adapt template parameters with current context."""
        adapted_params = template_params.copy()
        
        if context:
            adapted_params.update(context)
            
        return adapted_params
        
    def _add_task_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Add dependencies between tasks based on their types and requirements."""
        # Simple dependency logic - validation before execution, execution before verification
        for i, task in enumerate(tasks):
            if task.action_type in ['validation', 'setup', 'planning']:
                # These should typically run first
                continue
            elif task.action_type in ['execution', 'api_call', 'file_operation', 'analysis']:
                # These depend on validation/setup tasks
                for j, prev_task in enumerate(tasks[:i]):
                    if prev_task.action_type in ['validation', 'setup', 'planning']:
                        if prev_task.id not in task.dependencies:
                            task.dependencies.append(prev_task.id)
            elif task.action_type in ['verification', 'testing', 'report_generation']:
                # These depend on execution tasks
                for j, prev_task in enumerate(tasks[:i]):
                    if prev_task.action_type in ['execution', 'api_call', 'file_operation', 'analysis']:
                        if prev_task.id not in task.dependencies:
                            task.dependencies.append(prev_task.id)
                            
        return tasks
        
    def _estimate_task_durations(self, tasks: List[Task]) -> List[Task]:
        """Estimate task durations based on type and complexity."""
        duration_estimates = {
            'validation': 60,
            'planning': 120,
            'setup': 180,
            'file_operation': 90,
            'api_call': 120,
            'analysis': 300,
            'data_processing': 240,
            'execution': 180,
            'verification': 60,
            'testing': 150,
            'report_generation': 120
        }
        
        for task in tasks:
            if task.estimated_duration is None:
                base_duration = duration_estimates.get(task.action_type, 120)
                
                # Adjust based on complexity indicators
                complexity_factor = 1.0
                if any(word in task.description.lower() for word in ['complex', 'detailed', 'comprehensive']):
                    complexity_factor = 1.5
                elif any(word in task.description.lower() for word in ['simple', 'basic', 'quick']):
                    complexity_factor = 0.7
                    
                task.estimated_duration = int(base_duration * complexity_factor)
                
        return tasks
        
    def _optimize_task_order(self, tasks: List[Task]) -> List[Task]:
        """Optimize task ordering for efficiency."""
        # Sort by priority and dependencies
        def sort_key(task):
            priority_weights = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }
            return (priority_weights[task.priority], -len(task.dependencies))
            
        return sorted(tasks, key=sort_key, reverse=True)
        
    def _consolidate_tasks(self, tasks: List[Task]) -> List[Task]:
        """Consolidate tasks when there are too many."""
        if len(tasks) <= self.max_subtasks:
            return tasks
            
        # Group similar tasks
        task_groups = {}
        for task in tasks:
            group_key = task.action_type
            if group_key not in task_groups:
                task_groups[group_key] = []
            task_groups[group_key].append(task)
            
        consolidated = []
        for group_type, group_tasks in task_groups.items():
            if len(group_tasks) > 1:
                # Create a consolidated task
                consolidated_task = Task(
                    id=str(uuid.uuid4()),
                    title=f"Consolidated {group_type.replace('_', ' ').title()}",
                    description=f"Execute multiple {group_type} operations",
                    action_type=group_type,
                    parameters={'subtasks': [t.to_dict() for t in group_tasks]},
                    priority=max(t.priority for t in group_tasks),
                    estimated_duration=sum(t.estimated_duration or 0 for t in group_tasks)
                )
                consolidated.append(consolidated_task)
            else:
                consolidated.extend(group_tasks)
                
        return consolidated[:self.max_subtasks]
        
    def _save_planning_experience(self, plan: ExecutionPlan, goal: str, 
                                 context: Optional[Dict[str, Any]] = None):
        """Save planning experience to memory for future learning."""
        try:
            experience_data = {
                'goal': goal,
                'plan_id': plan.id,
                'task_count': len(plan.tasks),
                'estimated_duration': plan.estimated_total_duration,
                'goal_tags': plan.tags,
                'context': context or {},
                'tasks': [task.to_dict() for task in plan.tasks]
            }
            
            self.memory_system.store_memory(
                content=f"Planning experience for goal: {goal}",
                memory_type='planning_experience',
                metadata={
                    'goal': goal,
                    'plan_data': experience_data
                },
                importance=0.7
            )
            
        except Exception as e:
            logger.warning(f"Failed to save planning experience: {e}")
            
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get a plan by ID."""
        return self.active_plans.get(plan_id)
        
    def update_task_status(self, plan_id: str, task_id: str, status: TaskStatus, 
                          result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update the status of a task in a plan."""
        plan = self.active_plans.get(plan_id)
        if not plan:
            logger.warning(f"Plan not found: {plan_id}")
            return
            
        task = plan.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return
            
        old_status = task.status
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
            
        if result:
            task.result = result
        if error:
            task.error = error
            
        logger.info(f"Task {task_id} status: {old_status.value} -> {status.value}")
        
        # Update plan status if needed
        if plan.is_complete():
            plan.status = "completed"
        elif plan.has_failed_tasks():
            plan.status = "failed"
            
    def replan_task(self, plan_id: str, task_id: str, reason: str) -> List[Task]:
        """Replan a failed task with alternative approaches."""
        plan = self.active_plans.get(plan_id)
        if not plan:
            logger.warning(f"Plan not found for replanning: {plan_id}")
            return []
            
        failed_task = plan.get_task_by_id(task_id)
        if not failed_task:
            logger.warning(f"Task not found for replanning: {task_id}")
            return []
            
        logger.info(f"Replanning failed task: {task_id} (reason: {reason})")
        
        # Create alternative tasks
        alternative_tasks = self._create_alternative_tasks(failed_task, reason)
        
        # Add to plan
        plan.tasks.extend(alternative_tasks)
        
        # Update dependencies
        for task in plan.tasks:
            if failed_task.id in task.dependencies:
                task.dependencies.remove(failed_task.id)
                # Add dependency on the last alternative task
                if alternative_tasks:
                    task.dependencies.append(alternative_tasks[-1].id)
                    
        # Mark original task as cancelled
        failed_task.status = TaskStatus.CANCELLED
        
        return alternative_tasks
        
    def _create_alternative_tasks(self, failed_task: Task, reason: str) -> List[Task]:
        """Create alternative tasks for a failed task."""
        alternatives = []
        
        # Create a safer version of the same task
        safe_task = Task(
            id=str(uuid.uuid4()),
            title=f"Safe Alternative: {failed_task.title}",
            description=f"Alternative approach for: {failed_task.description}",
            action_type=failed_task.action_type,
            parameters={**failed_task.parameters, 'safe_mode': True},
            priority=failed_task.priority,
            estimated_duration=failed_task.estimated_duration,
            tags=failed_task.tags + ['alternative', 'safe_mode']
        )
        alternatives.append(safe_task)
        
        return alternatives
        
    def get_planning_stats(self) -> Dict[str, Any]:
        """Get statistics about planning performance."""
        total_plans = len(self.active_plans)
        completed_plans = sum(1 for p in self.active_plans.values() if p.status == "completed")
        failed_plans = sum(1 for p in self.active_plans.values() if p.status == "failed")
        
        total_tasks = sum(len(p.tasks) for p in self.active_plans.values())
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == TaskStatus.COMPLETED)
            for p in self.active_plans.values()
        )
        
        return {
            'total_plans': total_plans,
            'completed_plans': completed_plans,
            'failed_plans': failed_plans,
            'success_rate': completed_plans / total_plans if total_plans > 0 else 0,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'planning_patterns': len(self.planning_patterns)
        } 