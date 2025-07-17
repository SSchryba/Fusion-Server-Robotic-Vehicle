"""
Directive Manager for Autonomous AI Agent Framework

Manages the agent's prime directive, goals, constraints, and ensures
all actions align with the core mission and ethical guidelines.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

logger = logging.getLogger(__name__)


class DirectivePriority(Enum):
    """Priority levels for directives and constraints"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Constraint:
    """Represents a constraint on agent behavior"""
    text: str
    priority: DirectivePriority = DirectivePriority.HIGH
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    violation_count: int = 0
    
    
@dataclass
class Goal:
    """Represents an agent goal"""
    text: str
    priority: DirectivePriority = DirectivePriority.MEDIUM
    active: bool = True
    progress: float = 0.0  # 0.0 to 1.0
    target_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_progress_update: datetime = field(default_factory=datetime.now)
    

@dataclass
class DirectiveViolation:
    """Records a directive violation"""
    constraint_text: str
    action_attempted: str
    severity: DirectivePriority
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    

class DirectiveManager:
    """
    Manages the agent's prime directive, constraints, and goals.
    Ensures all agent actions align with its core mission.
    """
    
    def __init__(self, config_manager):
        """
        Initialize the directive manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.directive_config = config_manager.directive_config
        
        # Core directive components
        self.prime_directive: str = self.directive_config.primary
        self.constraints: List[Constraint] = []
        self.goals: List[Goal] = []
        self.violations: List[DirectiveViolation] = []
        
        # Load constraints and goals from config
        self._load_constraints()
        self._load_goals()
        
        # Directive evaluation state
        self.last_evaluation: Optional[datetime] = None
        self.evaluation_history: List[Dict[str, Any]] = []
        
        logger.info("Directive Manager initialized")
        
    def _load_constraints(self):
        """Load constraints from configuration."""
        constraint_texts = self.directive_config.constraints
        for text in constraint_texts:
            constraint = Constraint(
                text=text,
                priority=self._determine_constraint_priority(text)
            )
            self.constraints.append(constraint)
            
        logger.info(f"Loaded {len(self.constraints)} constraints")
        
    def _load_goals(self):
        """Load goals from configuration."""
        goal_texts = self.directive_config.goals
        for text in goal_texts:
            goal = Goal(
                text=text,
                priority=self._determine_goal_priority(text)
            )
            self.goals.append(goal)
            
        logger.info(f"Loaded {len(self.goals)} goals")
        
    def _determine_constraint_priority(self, text: str) -> DirectivePriority:
        """Determine constraint priority based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['harm', 'damage', 'destroy', 'delete', 'security']):
            return DirectivePriority.CRITICAL
        elif any(word in text_lower for word in ['privacy', 'safety', 'unauthorized']):
            return DirectivePriority.HIGH
        elif any(word in text_lower for word in ['resource', 'limit', 'budget']):
            return DirectivePriority.MEDIUM
        else:
            return DirectivePriority.LOW
            
    def _determine_goal_priority(self, text: str) -> DirectivePriority:
        """Determine goal priority based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['productivity', 'efficiency', 'user']):
            return DirectivePriority.HIGH
        elif any(word in text_lower for word in ['learn', 'adapt', 'improve']):
            return DirectivePriority.MEDIUM
        else:
            return DirectivePriority.LOW
            
    def evaluate_action(self, action_description: str, action_type: str = None, 
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate whether a proposed action aligns with the directive.
        
        Args:
            action_description: Description of the proposed action
            action_type: Type of action (e.g., 'system_command', 'api_call')
            context: Additional context about the action
            
        Returns:
            Dictionary with evaluation results
        """
        evaluation_result = {
            'allowed': True,
            'confidence': 1.0,
            'violations': [],
            'concerns': [],
            'recommendations': [],
            'timestamp': datetime.now()
        }
        
        # Check against constraints
        constraint_violations = self._check_constraints(action_description, action_type, context)
        if constraint_violations:
            evaluation_result['violations'].extend(constraint_violations)
            evaluation_result['allowed'] = False
            evaluation_result['confidence'] = 0.0
            
        # Check goal alignment
        goal_alignment = self._check_goal_alignment(action_description, context)
        evaluation_result['goal_alignment_score'] = goal_alignment
        
        # Adjust confidence based on goal alignment
        if evaluation_result['allowed']:
            evaluation_result['confidence'] = min(1.0, goal_alignment + 0.3)
            
        # Generate recommendations
        recommendations = self._generate_recommendations(action_description, evaluation_result)
        evaluation_result['recommendations'] = recommendations
        
        # Log evaluation
        self._log_evaluation(action_description, evaluation_result)
        
        return evaluation_result
        
    def _check_constraints(self, action_description: str, action_type: str = None,
                          context: Dict[str, Any] = None) -> List[str]:
        """Check if action violates any constraints."""
        violations = []
        action_lower = action_description.lower()
        
        for constraint in self.constraints:
            if not constraint.active:
                continue
                
            violation = self._check_single_constraint(constraint, action_description, 
                                                    action_type, context)
            if violation:
                violations.append(violation)
                constraint.violation_count += 1
                
                # Record violation
                directive_violation = DirectiveViolation(
                    constraint_text=constraint.text,
                    action_attempted=action_description,
                    severity=constraint.priority
                )
                self.violations.append(directive_violation)
                
        return violations
        
    def _check_single_constraint(self, constraint: Constraint, action_description: str,
                                action_type: str = None, context: Dict[str, Any] = None) -> Optional[str]:
        """Check if action violates a specific constraint."""
        constraint_lower = constraint.text.lower()
        action_lower = action_description.lower()
        
        # Basic keyword matching for constraint violations
        if 'harm' in constraint_lower and any(word in action_lower for word in 
                                            ['delete', 'remove', 'destroy', 'kill', 'terminate']):
            return f"Action may cause harm: {constraint.text}"
            
        if 'privacy' in constraint_lower and any(word in action_lower for word in 
                                               ['personal', 'private', 'confidential', 'secret']):
            return f"Action may violate privacy: {constraint.text}"
            
        if 'security' in constraint_lower and any(word in action_lower for word in 
                                                ['password', 'key', 'token', 'credential']):
            return f"Action may compromise security: {constraint.text}"
            
        if 'resource' in constraint_lower and action_type in ['system_command', 'file_write']:
            # Check if action might consume excessive resources
            if any(word in action_lower for word in ['infinite', 'unlimited', 'maximum']):
                return f"Action may exceed resource limits: {constraint.text}"
                
        return None
        
    def _check_goal_alignment(self, action_description: str, 
                             context: Dict[str, Any] = None) -> float:
        """Check how well the action aligns with goals."""
        if not self.goals:
            return 0.5  # Neutral if no goals defined
            
        total_score = 0.0
        active_goals = [g for g in self.goals if g.active]
        
        if not active_goals:
            return 0.5
            
        action_lower = action_description.lower()
        
        for goal in active_goals:
            goal_score = self._calculate_goal_alignment_score(goal, action_description)
            
            # Weight by priority
            priority_weights = {
                DirectivePriority.CRITICAL: 1.0,
                DirectivePriority.HIGH: 0.8,
                DirectivePriority.MEDIUM: 0.6,
                DirectivePriority.LOW: 0.4
            }
            
            weighted_score = goal_score * priority_weights.get(goal.priority, 0.5)
            total_score += weighted_score
            
        return min(1.0, total_score / len(active_goals))
        
    def _calculate_goal_alignment_score(self, goal: Goal, action_description: str) -> float:
        """Calculate how well an action aligns with a specific goal."""
        goal_lower = goal.text.lower()
        action_lower = action_description.lower()
        
        # Keyword-based alignment scoring
        alignment_keywords = {
            'productivity': ['automate', 'optimize', 'improve', 'enhance', 'speed'],
            'learn': ['analyze', 'study', 'research', 'experiment', 'test'],
            'user': ['help', 'assist', 'support', 'provide', 'deliver'],
            'security': ['protect', 'secure', 'validate', 'verify', 'check'],
            'stability': ['maintain', 'monitor', 'ensure', 'preserve', 'backup']
        }
        
        score = 0.0
        for goal_concept, keywords in alignment_keywords.items():
            if goal_concept in goal_lower:
                keyword_matches = sum(1 for keyword in keywords if keyword in action_lower)
                score += keyword_matches * 0.2
                
        return min(1.0, score)
        
    def _generate_recommendations(self, action_description: str, 
                                 evaluation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations to improve action alignment."""
        recommendations = []
        
        if not evaluation_result['allowed']:
            recommendations.append("Consider alternative approaches that don't violate constraints")
            recommendations.append("Seek approval before proceeding with restricted actions")
            
        if evaluation_result['goal_alignment_score'] < 0.5:
            recommendations.append("Consider how this action advances primary goals")
            recommendations.append("Add explicit goal-oriented outcomes to the action")
            
        if evaluation_result['confidence'] < 0.7:
            recommendations.append("Gather more context before proceeding")
            recommendations.append("Consider breaking action into smaller, validated steps")
            
        return recommendations
        
    def _log_evaluation(self, action_description: str, evaluation_result: Dict[str, Any]):
        """Log the evaluation for analysis and learning."""
        log_entry = {
            'action': action_description,
            'allowed': evaluation_result['allowed'],
            'confidence': evaluation_result['confidence'],
            'goal_alignment': evaluation_result['goal_alignment_score'],
            'violations_count': len(evaluation_result['violations']),
            'timestamp': evaluation_result['timestamp']
        }
        
        self.evaluation_history.append(log_entry)
        
        # Keep only recent evaluations
        if len(self.evaluation_history) > 1000:
            self.evaluation_history = self.evaluation_history[-1000:]
            
        self.last_evaluation = evaluation_result['timestamp']
        
        logger.info(f"Action evaluation: {action_description[:50]}... "
                   f"Allowed: {evaluation_result['allowed']}, "
                   f"Confidence: {evaluation_result['confidence']:.2f}")
                   
    def add_constraint(self, text: str, priority: DirectivePriority = DirectivePriority.MEDIUM):
        """Add a new constraint."""
        constraint = Constraint(text=text, priority=priority)
        self.constraints.append(constraint)
        logger.info(f"Added new constraint: {text}")
        
    def add_goal(self, text: str, priority: DirectivePriority = DirectivePriority.MEDIUM,
                target_date: Optional[datetime] = None):
        """Add a new goal."""
        goal = Goal(text=text, priority=priority, target_date=target_date)
        self.goals.append(goal)
        logger.info(f"Added new goal: {text}")
        
    def update_goal_progress(self, goal_text: str, progress: float):
        """Update progress on a specific goal."""
        for goal in self.goals:
            if goal.text == goal_text:
                goal.progress = max(0.0, min(1.0, progress))
                goal.last_progress_update = datetime.now()
                logger.info(f"Updated goal progress: {goal_text} -> {progress:.2f}")
                return
                
        logger.warning(f"Goal not found for progress update: {goal_text}")
        
    def get_active_constraints(self) -> List[Constraint]:
        """Get all active constraints."""
        return [c for c in self.constraints if c.active]
        
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return [g for g in self.goals if g.active]
        
    def get_recent_violations(self, hours: int = 24) -> List[DirectiveViolation]:
        """Get recent directive violations."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [v for v in self.violations if v.timestamp > cutoff]
        
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get statistics about directive evaluations."""
        if not self.evaluation_history:
            return {}
            
        recent_evaluations = self.evaluation_history[-100:]  # Last 100 evaluations
        
        allowed_count = sum(1 for e in recent_evaluations if e['allowed'])
        avg_confidence = sum(e['confidence'] for e in recent_evaluations) / len(recent_evaluations)
        avg_goal_alignment = sum(e['goal_alignment'] for e in recent_evaluations) / len(recent_evaluations)
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'recent_evaluations': len(recent_evaluations),
            'approval_rate': allowed_count / len(recent_evaluations) if recent_evaluations else 0,
            'average_confidence': avg_confidence,
            'average_goal_alignment': avg_goal_alignment,
            'total_violations': len(self.violations),
            'recent_violations': len(self.get_recent_violations()),
            'last_evaluation': self.last_evaluation
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert directive state to dictionary."""
        return {
            'prime_directive': self.prime_directive,
            'constraints': [
                {
                    'text': c.text,
                    'priority': c.priority.value,
                    'active': c.active,
                    'violation_count': c.violation_count
                }
                for c in self.constraints
            ],
            'goals': [
                {
                    'text': g.text,
                    'priority': g.priority.value,
                    'active': g.active,
                    'progress': g.progress,
                    'target_date': g.target_date.isoformat() if g.target_date else None
                }
                for g in self.goals
            ],
            'stats': self.get_evaluation_stats()
        } 