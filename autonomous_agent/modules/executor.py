"""
Task Executor for Autonomous AI Agent Framework

Executes planned tasks with proper error handling,
retry logic, and action system integration.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback

from .planner import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Task execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCH = "batch"


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    logs: List[str] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []


class TaskExecutor:
    """
    Executes tasks from execution plans with proper error handling,
    retry logic, and integration with action systems.
    """
    
    def __init__(self, config_manager, directive_manager, action_system, memory_system):
        """
        Initialize the task executor.
        
        Args:
            config_manager: Configuration manager instance
            directive_manager: Directive manager for action validation
            action_system: Action system for performing actions
            memory_system: Memory system for storing execution results
        """
        self.config_manager = config_manager
        self.directive_manager = directive_manager
        self.action_system = action_system
        self.memory_system = memory_system
        
        # Execution configuration
        self.executor_config = config_manager.get_section('modules').get('executor', {})
        self.max_retries = self.executor_config.get('max_retries', 3)
        self.retry_delay = self.executor_config.get('retry_delay_seconds', 5)
        self.parallel_execution = self.executor_config.get('parallel_execution', False)
        
        # Execution state
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        logger.info("Task Executor initialized")
        
    def _register_default_handlers(self):
        """Register default action handlers."""
        self.action_handlers.update({
            'system_command': self._execute_system_command,
            'file_operation': self._execute_file_operation,
            'api_call': self._execute_api_call,
            'validation': self._execute_validation,
            'analysis': self._execute_analysis,
            'data_processing': self._execute_data_processing,
            'planning': self._execute_planning,
            'execution': self._execute_general_action,
            'verification': self._execute_verification,
            'testing': self._execute_testing,
            'report_generation': self._execute_report_generation
        })
        
    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a custom action handler."""
        self.action_handlers[action_type] = handler
        logger.info(f"Registered custom handler for action type: {action_type}")
        
    async def execute_task(self, task: Task) -> ExecutionResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()
        result = ExecutionResult(task_id=task.id, success=False)
        
        try:
            logger.info(f"Starting execution of task: {task.id} ({task.title})")
            
            # Validate task against directive
            directive_eval = self.directive_manager.evaluate_action(
                f"Execute task: {task.title}",
                action_type=task.action_type,
                context=task.parameters
            )
            
            if not directive_eval['allowed']:
                result.error = f"Task blocked by directive: {directive_eval['violations']}"
                result.logs.append(f"Directive validation failed: {directive_eval['violations']}")
                return result
                
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Execute with retries
            execution_success = False
            for attempt in range(task.max_retries + 1):
                try:
                    result.retry_count = attempt
                    
                    # Get handler for task type
                    handler = self.action_handlers.get(task.action_type, self._execute_general_action)
                    
                    # Execute the task
                    task_result = await handler(task)
                    
                    if task_result and task_result.get('success', False):
                        result.success = True
                        result.result = task_result
                        execution_success = True
                        break
                    else:
                        error_msg = task_result.get('error', 'Unknown error') if task_result else 'No result'
                        result.logs.append(f"Attempt {attempt + 1} failed: {error_msg}")
                        
                        if attempt < task.max_retries:
                            await asyncio.sleep(self.retry_delay)
                        else:
                            result.error = f"Task failed after {task.max_retries + 1} attempts: {error_msg}"
                            
                except Exception as e:
                    error_msg = f"Exception in attempt {attempt + 1}: {str(e)}"
                    result.logs.append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < task.max_retries:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        result.error = f"Task failed with exception: {str(e)}"
                        
            # Update task status based on result
            if execution_success:
                task.status = TaskStatus.COMPLETED
                task.result = result.result
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error
                
            task.completed_at = datetime.now()
            
        except Exception as e:
            result.error = f"Critical error in task execution: {str(e)}"
            result.logs.append(f"Critical error: {traceback.format_exc()}")
            task.status = TaskStatus.FAILED
            task.error = result.error
            task.completed_at = datetime.now()
            
        finally:
            # Calculate execution time
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
            # Store execution result
            self.execution_history.append(result)
            self._store_execution_memory(task, result)
            
            logger.info(f"Task {task.id} completed: {'SUCCESS' if result.success else 'FAILED'} "
                       f"({result.execution_time:.2f}s)")
            
        return result
        
    async def execute_tasks(self, tasks: List[Task], mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> List[ExecutionResult]:
        """
        Execute multiple tasks.
        
        Args:
            tasks: List of tasks to execute
            mode: Execution mode (sequential, parallel, batch)
            
        Returns:
            List of execution results
        """
        logger.info(f"Executing {len(tasks)} tasks in {mode.value} mode")
        
        if mode == ExecutionMode.SEQUENTIAL:
            return await self._execute_sequential(tasks)
        elif mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(tasks)
        elif mode == ExecutionMode.BATCH:
            return await self._execute_batch(tasks)
        else:
            raise ValueError(f"Unsupported execution mode: {mode}")
            
    async def _execute_sequential(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Execute tasks sequentially."""
        results = []
        
        for task in tasks:
            if task.status != TaskStatus.READY:
                logger.warning(f"Skipping task {task.id} - not ready (status: {task.status.value})")
                continue
                
            result = await self.execute_task(task)
            results.append(result)
            
            # Stop if task failed and it's critical
            if not result.success and task.priority == TaskPriority.CRITICAL:
                logger.error(f"Critical task {task.id} failed - stopping execution")
                break
                
        return results
        
    async def _execute_parallel(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Execute tasks in parallel."""
        ready_tasks = [task for task in tasks if task.status == TaskStatus.READY]
        
        if not ready_tasks:
            logger.warning("No ready tasks for parallel execution")
            return []
            
        # Create execution coroutines
        execution_tasks = [self.execute_task(task) for task in ready_tasks]
        
        # Execute in parallel
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ExecutionResult(
                    task_id=ready_tasks[i].id,
                    success=False,
                    error=f"Exception during parallel execution: {str(result)}"
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
                
        return final_results
        
    async def _execute_batch(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Execute tasks in batches."""
        batch_size = self.config_manager.get('agent.max_concurrent_tasks', 3)
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            ready_batch = [task for task in batch if task.status == TaskStatus.READY]
            
            if ready_batch:
                batch_results = await self._execute_parallel(ready_batch)
                results.extend(batch_results)
                
        return results
        
    async def _execute_system_command(self, task: Task) -> Dict[str, Any]:
        """Execute a system command task."""
        try:
            command = task.parameters.get('command')
            if not command:
                return {'success': False, 'error': 'No command specified'}
                
            # Use action system to execute command
            result = await self.action_system.execute_command(
                command, 
                task.parameters.get('working_directory'),
                task.parameters.get('timeout', 60)
            )
            
            return {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error'),
                'exit_code': result.get('exit_code', -1)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"System command execution failed: {str(e)}"}
            
    async def _execute_file_operation(self, task: Task) -> Dict[str, Any]:
        """Execute a file operation task."""
        try:
            operation = task.parameters.get('operation')  # read, write, copy, delete, etc.
            file_path = task.parameters.get('file_path')
            
            if not operation or not file_path:
                return {'success': False, 'error': 'Missing operation or file_path'}
                
            result = await self.action_system.execute_file_operation(
                operation,
                file_path,
                task.parameters.get('content'),
                task.parameters
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f"File operation failed: {str(e)}"}
            
    async def _execute_api_call(self, task: Task) -> Dict[str, Any]:
        """Execute an API call task."""
        try:
            url = task.parameters.get('url')
            method = task.parameters.get('method', 'GET')
            headers = task.parameters.get('headers', {})
            data = task.parameters.get('data')
            
            if not url:
                return {'success': False, 'error': 'No URL specified'}
                
            result = await self.action_system.execute_api_call(
                method, url, headers, data, task.parameters.get('timeout', 30)
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': f"API call failed: {str(e)}"}
            
    async def _execute_validation(self, task: Task) -> Dict[str, Any]:
        """Execute a validation task."""
        try:
            validation_type = task.parameters.get('validation_type', 'general')
            target = task.parameters.get('target')
            
            if validation_type == 'file_operation':
                # Validate file paths and permissions
                file_path = task.parameters.get('file_path')
                if not file_path:
                    return {'success': False, 'error': 'No file path to validate'}
                    
                # Check if file exists, readable, writable, etc.
                validation_result = await self.action_system.validate_file_access(file_path)
                return validation_result
                
            elif validation_type == 'api_endpoint':
                # Validate API endpoint accessibility
                url = task.parameters.get('url')
                if not url:
                    return {'success': False, 'error': 'No URL to validate'}
                    
                validation_result = await self.action_system.validate_api_endpoint(url)
                return validation_result
                
            else:
                # General validation
                return {'success': True, 'message': 'Validation completed', 'validation_type': validation_type}
                
        except Exception as e:
            return {'success': False, 'error': f"Validation failed: {str(e)}"}
            
    async def _execute_analysis(self, task: Task) -> Dict[str, Any]:
        """Execute an analysis task."""
        try:
            analysis_type = task.parameters.get('analysis_type', 'general')
            data_source = task.parameters.get('data_source')
            
            # Placeholder for analysis logic
            analysis_result = {
                'analysis_type': analysis_type,
                'data_source': data_source,
                'results': {
                    'summary': f"Analysis of {data_source} completed",
                    'findings': ['Finding 1', 'Finding 2'],
                    'recommendations': ['Recommendation 1', 'Recommendation 2']
                },
                'metadata': {
                    'analyzed_at': datetime.now().isoformat(),
                    'analysis_duration': 'simulated'
                }
            }
            
            return {'success': True, 'analysis_result': analysis_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Analysis failed: {str(e)}"}
            
    async def _execute_data_processing(self, task: Task) -> Dict[str, Any]:
        """Execute a data processing task."""
        try:
            processing_type = task.parameters.get('processing_type', 'general')
            input_data = task.parameters.get('input_data')
            
            # Placeholder for data processing logic
            processed_result = {
                'processing_type': processing_type,
                'input_size': len(str(input_data)) if input_data else 0,
                'output_data': f"Processed: {processing_type}",
                'metrics': {
                    'processing_time': 'simulated',
                    'records_processed': 'simulated'
                }
            }
            
            return {'success': True, 'processed_result': processed_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Data processing failed: {str(e)}"}
            
    async def _execute_planning(self, task: Task) -> Dict[str, Any]:
        """Execute a planning task."""
        try:
            planning_goal = task.parameters.get('goal', task.description)
            
            # Create a planning result
            planning_result = {
                'goal': planning_goal,
                'plan_created': True,
                'steps': [
                    'Step 1: Analyze requirements',
                    'Step 2: Design approach',
                    'Step 3: Implement solution'
                ],
                'estimated_effort': 'medium',
                'risks': ['Risk 1', 'Risk 2'],
                'success_criteria': ['Criteria 1', 'Criteria 2']
            }
            
            return {'success': True, 'planning_result': planning_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Planning failed: {str(e)}"}
            
    async def _execute_verification(self, task: Task) -> Dict[str, Any]:
        """Execute a verification task."""
        try:
            verification_type = task.parameters.get('verification_type', 'general')
            target = task.parameters.get('target')
            
            # Placeholder verification logic
            verification_result = {
                'verification_type': verification_type,
                'target': target,
                'verified': True,
                'checks_passed': ['Check 1', 'Check 2'],
                'checks_failed': [],
                'confidence': 0.95
            }
            
            return {'success': True, 'verification_result': verification_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Verification failed: {str(e)}"}
            
    async def _execute_testing(self, task: Task) -> Dict[str, Any]:
        """Execute a testing task."""
        try:
            test_type = task.parameters.get('test_type', 'general')
            test_target = task.parameters.get('target')
            
            # Placeholder testing logic
            test_result = {
                'test_type': test_type,
                'target': test_target,
                'tests_run': 5,
                'tests_passed': 4,
                'tests_failed': 1,
                'test_results': [
                    {'name': 'Test 1', 'status': 'passed'},
                    {'name': 'Test 2', 'status': 'passed'},
                    {'name': 'Test 3', 'status': 'failed', 'error': 'Sample error'},
                    {'name': 'Test 4', 'status': 'passed'},
                    {'name': 'Test 5', 'status': 'passed'}
                ]
            }
            
            return {'success': True, 'test_result': test_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Testing failed: {str(e)}"}
            
    async def _execute_report_generation(self, task: Task) -> Dict[str, Any]:
        """Execute a report generation task."""
        try:
            report_type = task.parameters.get('report_type', 'general')
            data_source = task.parameters.get('data_source')
            format_type = task.parameters.get('format', 'text')
            
            # Generate report content
            report_content = f"""
# {report_type.title()} Report

## Summary
This report was generated automatically based on {data_source}.

## Key Findings
- Finding 1: Analysis completed successfully
- Finding 2: No critical issues identified
- Finding 3: Recommendations provided

## Recommendations
1. Continue monitoring
2. Implement suggested improvements
3. Schedule regular reviews

## Generated: {datetime.now().isoformat()}
"""
            
            report_result = {
                'report_type': report_type,
                'format': format_type,
                'content': report_content,
                'length': len(report_content),
                'sections': ['Summary', 'Key Findings', 'Recommendations']
            }
            
            return {'success': True, 'report_result': report_result}
            
        except Exception as e:
            return {'success': False, 'error': f"Report generation failed: {str(e)}"}
            
    async def _execute_general_action(self, task: Task) -> Dict[str, Any]:
        """Execute a general action task."""
        try:
            # General execution placeholder
            action_result = {
                'action_type': task.action_type,
                'title': task.title,
                'description': task.description,
                'parameters': task.parameters,
                'executed': True,
                'message': f"Successfully executed {task.action_type} action"
            }
            
            return {'success': True, 'action_result': action_result}
            
        except Exception as e:
            return {'success': False, 'error': f"General action failed: {str(e)}"}
            
    def _store_execution_memory(self, task: Task, result: ExecutionResult):
        """Store execution experience in memory."""
        try:
            memory_content = f"Executed task: {task.title} - {'SUCCESS' if result.success else 'FAILED'}"
            
            metadata = {
                'task_id': task.id,
                'task_type': task.action_type,
                'success': result.success,
                'execution_time': result.execution_time,
                'retry_count': result.retry_count,
                'task_priority': task.priority.value,
                'task_parameters': task.parameters
            }
            
            if result.error:
                metadata['error'] = result.error
                
            if result.result:
                metadata['result_summary'] = str(result.result)[:500]  # Truncate large results
                
            self.memory_system.store_memory(
                content=memory_content,
                memory_type='execution_experience',
                metadata=metadata,
                importance=0.8 if result.success else 0.9  # Failed executions are more important to remember
            )
            
        except Exception as e:
            logger.warning(f"Failed to store execution memory: {e}")
            
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {'total_executions': 0}
            
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for result in self.execution_history if result.success)
        total_time = sum(result.execution_time for result in self.execution_history)
        total_retries = sum(result.retry_count for result in self.execution_history)
        
        # Get recent executions (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_executions = [
            result for result in self.execution_history 
            if datetime.now() - timedelta(seconds=result.execution_time) > recent_cutoff
        ]
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions,
            'average_execution_time': total_time / total_executions,
            'total_retries': total_retries,
            'recent_executions_24h': len(recent_executions),
            'active_executions': len(self.active_executions)
        }
        
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task execution."""
        if task_id in self.active_executions:
            task = self.active_executions[task_id]
            task.cancel()
            del self.active_executions[task_id]
            logger.info(f"Cancelled task execution: {task_id}")
            return True
        return False
        
    def get_active_tasks(self) -> List[str]:
        """Get list of currently executing task IDs."""
        return list(self.active_executions.keys()) 