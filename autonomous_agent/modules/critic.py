"""
Task Critic for Autonomous AI Agent Framework

Evaluates task execution results, provides feedback scores,
and identifies areas for improvement in agent performance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math

from .planner import Task, TaskStatus, TaskPriority
from .executor import ExecutionResult

logger = logging.getLogger(__name__)


class CriticScore(Enum):
    """Critic scoring levels"""
    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"           # 0.7-0.89
    FAIR = "fair"           # 0.5-0.69
    POOR = "poor"           # 0.3-0.49
    FAILED = "failed"       # 0.0-0.29


@dataclass
class CriticEvaluation:
    """Evaluation result from the critic"""
    task_id: str
    overall_score: float  # 0.0 to 1.0
    score_level: CriticScore
    criteria_scores: Dict[str, float] = field(default_factory=dict)
    feedback: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary."""
        return {
            'task_id': self.task_id,
            'overall_score': self.overall_score,
            'score_level': self.score_level.value,
            'criteria_scores': self.criteria_scores,
            'feedback': self.feedback,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


class TaskCritic:
    """
    Evaluates task execution results and provides feedback
    for continuous improvement of agent performance.
    """
    
    def __init__(self, config_manager, directive_manager, memory_system):
        """
        Initialize the task critic.
        
        Args:
            config_manager: Configuration manager instance
            directive_manager: Directive manager for goal alignment
            memory_system: Memory system for storing evaluations
        """
        self.config_manager = config_manager
        self.directive_manager = directive_manager
        self.memory_system = memory_system
        
        # Critic configuration
        self.critic_config = config_manager.get_section('modules').get('critic', {})
        self.scoring_model = self.critic_config.get('scoring_model', 'weighted_average')
        self.success_threshold = self.critic_config.get('success_threshold', 0.7)
        self.failure_threshold = self.critic_config.get('failure_threshold', 0.3)
        
        # Evaluation criteria and weights
        self.evaluation_criteria = {
            'success': 0.4,           # Did the task succeed?
            'efficiency': 0.2,        # Was it done efficiently?
            'quality': 0.2,           # Was the result high quality?
            'directive_alignment': 0.1,  # Did it align with directives?
            'learning_value': 0.1     # Did we learn something useful?
        }
        
        # Evaluation history
        self.evaluations: List[CriticEvaluation] = []
        
        # Performance baselines
        self.performance_baselines = self._load_performance_baselines()
        
        logger.info("Task Critic initialized")
        
    def _load_performance_baselines(self) -> Dict[str, float]:
        """Load performance baselines from historical data."""
        try:
            baseline_memories = self.memory_system.get_memories_by_type('performance_baseline', limit=10)
            
            baselines = {}
            for memory in baseline_memories:
                baseline_data = memory.metadata.get('baseline_data', {})
                baselines.update(baseline_data)
                
            # Default baselines if no historical data
            if not baselines:
                baselines = {
                    'average_execution_time': 120.0,  # seconds
                    'success_rate': 0.8,
                    'retry_rate': 0.2,
                    'quality_score': 0.7
                }
                
            logger.info(f"Loaded performance baselines: {baselines}")
            return baselines
            
        except Exception as e:
            logger.warning(f"Failed to load baselines: {e}")
            return {
                'average_execution_time': 120.0,
                'success_rate': 0.8,
                'retry_rate': 0.2,
                'quality_score': 0.7
            }
            
    def evaluate_task_execution(self, task: Task, execution_result: ExecutionResult) -> CriticEvaluation:
        """
        Evaluate a completed task execution.
        
        Args:
            task: The executed task
            execution_result: Result of task execution
            
        Returns:
            CriticEvaluation with scores and feedback
        """
        logger.info(f"Evaluating task execution: {task.id}")
        
        # Calculate individual criteria scores
        criteria_scores = {}
        
        # Success criterion
        criteria_scores['success'] = self._evaluate_success(task, execution_result)
        
        # Efficiency criterion
        criteria_scores['efficiency'] = self._evaluate_efficiency(task, execution_result)
        
        # Quality criterion
        criteria_scores['quality'] = self._evaluate_quality(task, execution_result)
        
        # Directive alignment criterion
        criteria_scores['directive_alignment'] = self._evaluate_directive_alignment(task, execution_result)
        
        # Learning value criterion
        criteria_scores['learning_value'] = self._evaluate_learning_value(task, execution_result)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(criteria_scores)
        
        # Determine score level
        score_level = self._determine_score_level(overall_score)
        
        # Generate feedback and recommendations
        feedback = self._generate_feedback(task, execution_result, criteria_scores)
        recommendations = self._generate_recommendations(task, execution_result, criteria_scores)
        
        # Create evaluation
        evaluation = CriticEvaluation(
            task_id=task.id,
            overall_score=overall_score,
            score_level=score_level,
            criteria_scores=criteria_scores,
            feedback=feedback,
            recommendations=recommendations
        )
        
        # Store evaluation
        self.evaluations.append(evaluation)
        self._store_evaluation_memory(task, execution_result, evaluation)
        
        logger.info(f"Task evaluation completed: {score_level.value} ({overall_score:.2f})")
        
        return evaluation
        
    def _evaluate_success(self, task: Task, execution_result: ExecutionResult) -> float:
        """Evaluate the success criterion."""
        if execution_result.success:
            # Base success score
            score = 1.0
            
            # Reduce score for retries
            if execution_result.retry_count > 0:
                retry_penalty = min(0.3, execution_result.retry_count * 0.1)
                score -= retry_penalty
                
            return max(0.0, score)
        else:
            # Failed task - check if it was a graceful failure
            if execution_result.error and 'graceful' in execution_result.error.lower():
                return 0.2  # Some credit for graceful failure
            return 0.0
            
    def _evaluate_efficiency(self, task: Task, execution_result: ExecutionResult) -> float:
        """Evaluate the efficiency criterion."""
        baseline_time = self.performance_baselines.get('average_execution_time', 120.0)
        actual_time = execution_result.execution_time
        
        # Calculate efficiency based on time comparison
        if actual_time <= baseline_time * 0.5:
            return 1.0  # Very efficient
        elif actual_time <= baseline_time:
            return 0.8  # Good efficiency
        elif actual_time <= baseline_time * 1.5:
            return 0.6  # Fair efficiency
        elif actual_time <= baseline_time * 2.0:
            return 0.4  # Poor efficiency
        else:
            return 0.2  # Very inefficient
            
    def _evaluate_quality(self, task: Task, execution_result: ExecutionResult) -> float:
        """Evaluate the quality criterion."""
        if not execution_result.success:
            return 0.0
            
        result_data = execution_result.result or {}
        
        # Quality indicators
        quality_score = 0.5  # Base score
        
        # Check for comprehensive results
        if isinstance(result_data, dict):
            if len(result_data) >= 3:  # Has multiple result fields
                quality_score += 0.2
                
            # Check for error handling
            if 'error' in result_data or 'errors' in result_data:
                quality_score += 0.1
                
            # Check for metadata/details
            if any(key in result_data for key in ['metadata', 'details', 'summary']):
                quality_score += 0.1
                
            # Check for validation
            if any(key in result_data for key in ['validated', 'verified', 'checks']):
                quality_score += 0.1
                
        return min(1.0, quality_score)
        
    def _evaluate_directive_alignment(self, task: Task, execution_result: ExecutionResult) -> float:
        """Evaluate alignment with directives."""
        try:
            # Get directive evaluation for the task
            directive_eval = self.directive_manager.evaluate_action(
                f"Evaluate completed task: {task.title}",
                action_type=task.action_type,
                context=task.parameters
            )
            
            alignment_score = directive_eval.get('confidence', 0.5)
            
            # Bonus for achieving goals
            goal_alignment = directive_eval.get('goal_alignment_score', 0.5)
            alignment_score = (alignment_score + goal_alignment) / 2
            
            return alignment_score
            
        except Exception as e:
            logger.warning(f"Failed to evaluate directive alignment: {e}")
            return 0.5  # Neutral score if evaluation fails
            
    def _evaluate_learning_value(self, task: Task, execution_result: ExecutionResult) -> float:
        """Evaluate the learning value of the task execution."""
        learning_score = 0.5  # Base score
        
        # Higher value for novel task types
        similar_tasks = self.memory_system.retrieve_memories(
            f"task type: {task.action_type}",
            limit=5,
            memory_types=['execution_experience']
        )
        
        novelty_bonus = max(0.0, 0.3 - len(similar_tasks) * 0.1)
        learning_score += novelty_bonus
        
        # Higher value for tasks that failed (learning from mistakes)
        if not execution_result.success:
            learning_score += 0.2
            
        # Higher value for tasks with rich results
        if execution_result.result and isinstance(execution_result.result, dict):
            if len(execution_result.result) > 3:
                learning_score += 0.1
                
        return min(1.0, learning_score)
        
    def _calculate_overall_score(self, criteria_scores: Dict[str, float]) -> float:
        """Calculate overall score from criteria scores."""
        if self.scoring_model == 'weighted_average':
            total_score = 0.0
            total_weight = 0.0
            
            for criterion, score in criteria_scores.items():
                weight = self.evaluation_criteria.get(criterion, 0.0)
                total_score += score * weight
                total_weight += weight
                
            return total_score / total_weight if total_weight > 0 else 0.0
            
        elif self.scoring_model == 'minimum':
            # Score is limited by the worst criterion
            return min(criteria_scores.values()) if criteria_scores else 0.0
            
        elif self.scoring_model == 'geometric_mean':
            # Geometric mean of all criteria
            if criteria_scores:
                product = 1.0
                for score in criteria_scores.values():
                    product *= max(0.01, score)  # Avoid zero
                return product ** (1.0 / len(criteria_scores))
            return 0.0
            
        else:
            # Default to simple average
            return statistics.mean(criteria_scores.values()) if criteria_scores else 0.0
            
    def _determine_score_level(self, overall_score: float) -> CriticScore:
        """Determine the score level from overall score."""
        if overall_score >= 0.9:
            return CriticScore.EXCELLENT
        elif overall_score >= 0.7:
            return CriticScore.GOOD
        elif overall_score >= 0.5:
            return CriticScore.FAIR
        elif overall_score >= 0.3:
            return CriticScore.POOR
        else:
            return CriticScore.FAILED
            
    def _generate_feedback(self, task: Task, execution_result: ExecutionResult, 
                          criteria_scores: Dict[str, float]) -> List[str]:
        """Generate specific feedback based on evaluation."""
        feedback = []
        
        # Success feedback
        if criteria_scores.get('success', 0) >= 0.8:
            feedback.append("Task completed successfully with minimal issues")
        elif criteria_scores.get('success', 0) >= 0.5:
            feedback.append("Task completed but with some difficulties")
        else:
            feedback.append("Task failed to complete successfully")
            
        # Efficiency feedback
        if criteria_scores.get('efficiency', 0) >= 0.8:
            feedback.append("Task was executed efficiently")
        elif criteria_scores.get('efficiency', 0) < 0.5:
            feedback.append("Task execution was inefficient - took longer than expected")
            
        # Quality feedback
        if criteria_scores.get('quality', 0) >= 0.8:
            feedback.append("High quality results with good detail and validation")
        elif criteria_scores.get('quality', 0) < 0.5:
            feedback.append("Results could be more comprehensive and detailed")
            
        # Retry feedback
        if execution_result.retry_count > 0:
            feedback.append(f"Required {execution_result.retry_count} retries to complete")
            
        # Error feedback
        if execution_result.error:
            feedback.append(f"Error encountered: {execution_result.error}")
            
        return feedback
        
    def _generate_recommendations(self, task: Task, execution_result: ExecutionResult,
                                 criteria_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        # Efficiency recommendations
        if criteria_scores.get('efficiency', 0) < 0.6:
            recommendations.append("Consider optimizing task parameters for better performance")
            recommendations.append("Review task complexity and break down if needed")
            
        # Quality recommendations
        if criteria_scores.get('quality', 0) < 0.6:
            recommendations.append("Add more validation and error checking")
            recommendations.append("Enhance result formatting and detail")
            
        # Success recommendations
        if criteria_scores.get('success', 0) < 0.7:
            recommendations.append("Review task requirements and constraints")
            recommendations.append("Improve error handling and recovery mechanisms")
            
        # Retry recommendations
        if execution_result.retry_count > 1:
            recommendations.append("Investigate root cause of failures to reduce retries")
            recommendations.append("Consider alternative approaches for this task type")
            
        # Directive alignment recommendations
        if criteria_scores.get('directive_alignment', 0) < 0.6:
            recommendations.append("Ensure task aligns better with agent directives")
            recommendations.append("Review goal prioritization and constraints")
            
        return recommendations
        
    def _store_evaluation_memory(self, task: Task, execution_result: ExecutionResult, 
                                evaluation: CriticEvaluation):
        """Store evaluation in memory for learning."""
        try:
            memory_content = f"Task evaluation: {task.title} - {evaluation.score_level.value}"
            
            metadata = {
                'task_id': task.id,
                'task_type': task.action_type,
                'overall_score': evaluation.overall_score,
                'score_level': evaluation.score_level.value,
                'criteria_scores': evaluation.criteria_scores,
                'execution_time': execution_result.execution_time,
                'success': execution_result.success,
                'retry_count': execution_result.retry_count
            }
            
            self.memory_system.store_memory(
                content=memory_content,
                memory_type='task_evaluation',
                metadata=metadata,
                importance=0.8
            )
            
        except Exception as e:
            logger.warning(f"Failed to store evaluation memory: {e}")
            
    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_evaluations = [
            eval for eval in self.evaluations 
            if eval.timestamp > cutoff_date
        ]
        
        if not recent_evaluations:
            return {'message': 'No recent evaluations available'}
            
        # Calculate trends
        scores = [eval.overall_score for eval in recent_evaluations]
        success_rate = sum(1 for eval in recent_evaluations 
                          if eval.overall_score >= self.success_threshold) / len(recent_evaluations)
        
        # Criteria averages
        criteria_averages = {}
        for criterion in self.evaluation_criteria.keys():
            criterion_scores = [eval.criteria_scores.get(criterion, 0) 
                              for eval in recent_evaluations]
            criteria_averages[criterion] = statistics.mean(criterion_scores)
            
        return {
            'period_days': days,
            'total_evaluations': len(recent_evaluations),
            'average_score': statistics.mean(scores),
            'score_std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'success_rate': success_rate,
            'criteria_averages': criteria_averages,
            'score_distribution': {
                'excellent': sum(1 for s in scores if s >= 0.9),
                'good': sum(1 for s in scores if 0.7 <= s < 0.9),
                'fair': sum(1 for s in scores if 0.5 <= s < 0.7),
                'poor': sum(1 for s in scores if 0.3 <= s < 0.5),
                'failed': sum(1 for s in scores if s < 0.3)
            }
        }
        
    def identify_improvement_areas(self) -> List[Dict[str, Any]]:
        """Identify areas where the agent needs improvement."""
        if len(self.evaluations) < 5:
            return [{'area': 'insufficient_data', 'message': 'Need more evaluations for analysis'}]
            
        # Analyze recent evaluations
        recent_evaluations = self.evaluations[-20:]  # Last 20 evaluations
        
        improvement_areas = []
        
        # Check each criterion
        for criterion, weight in self.evaluation_criteria.items():
            scores = [eval.criteria_scores.get(criterion, 0) for eval in recent_evaluations]
            avg_score = statistics.mean(scores)
            
            if avg_score < 0.6:  # Below acceptable threshold
                improvement_areas.append({
                    'area': criterion,
                    'current_score': avg_score,
                    'priority': 'high' if weight > 0.2 else 'medium',
                    'suggestion': f"Focus on improving {criterion.replace('_', ' ')} in task execution"
                })
                
        # Check for patterns in failed tasks
        failed_evals = [eval for eval in recent_evaluations if eval.overall_score < self.failure_threshold]
        if len(failed_evals) > len(recent_evaluations) * 0.3:  # More than 30% failures
            improvement_areas.append({
                'area': 'failure_rate',
                'current_rate': len(failed_evals) / len(recent_evaluations),
                'priority': 'critical',
                'suggestion': 'High failure rate - review task planning and execution strategies'
            })
            
        return improvement_areas
        
    def get_critic_stats(self) -> Dict[str, Any]:
        """Get critic statistics and performance metrics."""
        if not self.evaluations:
            return {'total_evaluations': 0}
            
        total_evaluations = len(self.evaluations)
        scores = [eval.overall_score for eval in self.evaluations]
        
        return {
            'total_evaluations': total_evaluations,
            'average_score': statistics.mean(scores),
            'score_range': {
                'min': min(scores),
                'max': max(scores)
            },
            'success_threshold': self.success_threshold,
            'failure_threshold': self.failure_threshold,
            'scoring_model': self.scoring_model,
            'evaluation_criteria': self.evaluation_criteria,
            'recent_performance': self.get_performance_trends(7)
        } 