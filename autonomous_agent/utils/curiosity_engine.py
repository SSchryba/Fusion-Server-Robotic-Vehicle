"""
Curiosity Engine for Autonomous AI Agent Framework

Implements curiosity-driven exploration, novelty detection,
and automatic subgoal generation to enhance agent learning.
"""

import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NoveltyLevel(Enum):
    """Levels of novelty for experiences"""
    ROUTINE = "routine"        # 0.0-0.3
    FAMILIAR = "familiar"      # 0.3-0.5
    INTERESTING = "interesting"  # 0.5-0.7
    NOVEL = "novel"           # 0.7-0.9
    UNPRECEDENTED = "unprecedented"  # 0.9-1.0


@dataclass
class ExplorationTarget:
    """Represents a target for curious exploration"""
    id: str
    description: str
    novelty_score: float
    information_gain_potential: float
    uncertainty_level: float
    exploration_priority: float
    created_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    last_attempted: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'novelty_score': self.novelty_score,
            'information_gain_potential': self.information_gain_potential,
            'uncertainty_level': self.uncertainty_level,
            'exploration_priority': self.exploration_priority,
            'created_at': self.created_at.isoformat(),
            'attempts': self.attempts,
            'last_attempted': self.last_attempted.isoformat() if self.last_attempted else None
        }


@dataclass
class CuriosityInsight:
    """Represents an insight discovered through curiosity"""
    insight_type: str
    description: str
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'insight_type': self.insight_type,
            'description': self.description,
            'confidence': self.confidence,
            'supporting_evidence': self.supporting_evidence,
            'discovered_at': self.discovered_at.isoformat()
        }


class CuriosityEngine:
    """
    Implements curiosity-driven behavior to enhance agent learning
    through novelty detection and autonomous exploration.
    """
    
    def __init__(self, config_manager, memory_system, directive_manager):
        """
        Initialize the curiosity engine.
        
        Args:
            config_manager: Configuration manager instance
            memory_system: Memory system for storing discoveries
            directive_manager: Directive manager for goal alignment
        """
        self.config_manager = config_manager
        self.memory_system = memory_system
        self.directive_manager = directive_manager
        
        # Curiosity configuration
        self.curiosity_config = config_manager.get_section('curiosity')
        self.enabled = self.curiosity_config.get('enabled', True)
        self.novelty_threshold = self.curiosity_config.get('novelty_threshold', 0.6)
        self.exploration_rate = self.curiosity_config.get('exploration_rate', 0.1)
        
        # Scoring configuration
        scoring = self.curiosity_config.get('scoring', {})
        self.scoring_weights = {
            'information_gain': scoring.get('information_gain_weight', 0.4),
            'uncertainty': scoring.get('uncertainty_weight', 0.3),
            'diversity': scoring.get('diversity_weight', 0.3)
        }
        
        # Subgoal generation
        subgoal_config = self.curiosity_config.get('subgoal_generation', {})
        self.max_subgoals = subgoal_config.get('max_subgoals', 5)
        self.creativity_factor = subgoal_config.get('creativity_factor', 0.7)
        
        # State tracking
        self.exploration_targets: List[ExplorationTarget] = []
        self.discovered_insights: List[CuriosityInsight] = []
        self.experience_history: List[Dict[str, Any]] = []
        
        # Knowledge tracking
        self.knowledge_domains: Dict[str, float] = {}  # Domain -> familiarity score
        self.pattern_library: Dict[str, List[str]] = {}  # Pattern type -> instances
        
        logger.info(f"Curiosity Engine initialized - Enabled: {self.enabled}")
        
    def calculate_novelty_score(self, experience: Dict[str, Any]) -> float:
        """
        Calculate novelty score for an experience.
        
        Args:
            experience: Experience data to evaluate
            
        Returns:
            Novelty score between 0.0 and 1.0
        """
        if not self.enabled:
            return 0.0
            
        try:
            # Extract key features from experience
            experience_type = experience.get('type', 'unknown')
            content = experience.get('content', '')
            context = experience.get('context', {})
            
            # Find similar experiences in memory
            similar_memories = self.memory_system.retrieve_memories(
                content, 
                limit=10,
                memory_types=['experience', 'observation', 'learning_experience']
            )
            
            # Calculate similarity-based novelty
            similarity_novelty = self._calculate_similarity_novelty(experience, similar_memories)
            
            # Calculate domain novelty
            domain_novelty = self._calculate_domain_novelty(experience_type)
            
            # Calculate pattern novelty
            pattern_novelty = self._calculate_pattern_novelty(experience)
            
            # Combine novelty scores
            overall_novelty = (
                similarity_novelty * 0.5 +
                domain_novelty * 0.3 +
                pattern_novelty * 0.2
            )
            
            # Store experience for future comparisons
            self.experience_history.append({
                'experience': experience,
                'novelty_score': overall_novelty,
                'timestamp': datetime.now().isoformat()
            })
            
            # Limit history size
            if len(self.experience_history) > 1000:
                self.experience_history = self.experience_history[-1000:]
                
            return min(1.0, max(0.0, overall_novelty))
            
        except Exception as e:
            logger.error(f"Novelty calculation failed: {e}")
            return 0.5  # Default to moderate novelty
            
    def _calculate_similarity_novelty(self, experience: Dict[str, Any], 
                                    similar_memories: List) -> float:
        """Calculate novelty based on similarity to past experiences."""
        if not similar_memories:
            return 1.0  # Completely novel if no similar memories
            
        # Calculate average similarity
        similarities = []
        for memory in similar_memories:
            # Simple text-based similarity (could be enhanced with embeddings)
            similarity = self._calculate_text_similarity(
                experience.get('content', ''),
                memory.content
            )
            similarities.append(similarity)
            
        avg_similarity = sum(similarities) / len(similarities)
        
        # Novelty is inverse of similarity
        return 1.0 - avg_similarity
        
    def _calculate_domain_novelty(self, experience_type: str) -> float:
        """Calculate novelty based on domain familiarity."""
        domain_familiarity = self.knowledge_domains.get(experience_type, 0.0)
        
        # Update domain familiarity
        self.knowledge_domains[experience_type] = min(1.0, domain_familiarity + 0.1)
        
        # Novelty decreases with familiarity
        return 1.0 - domain_familiarity
        
    def _calculate_pattern_novelty(self, experience: Dict[str, Any]) -> float:
        """Calculate novelty based on pattern recognition."""
        # Extract patterns from experience
        patterns = self._extract_patterns(experience)
        
        novelty_scores = []
        for pattern_type, pattern_value in patterns.items():
            if pattern_type not in self.pattern_library:
                self.pattern_library[pattern_type] = []
                
            # Check if pattern is known
            if pattern_value in self.pattern_library[pattern_type]:
                novelty_scores.append(0.2)  # Known pattern
            else:
                novelty_scores.append(0.8)  # Novel pattern
                self.pattern_library[pattern_type].append(pattern_value)
                
        return sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.5
        
    def _extract_patterns(self, experience: Dict[str, Any]) -> Dict[str, str]:
        """Extract recognizable patterns from experience."""
        patterns = {}
        
        content = experience.get('content', '').lower()
        
        # Simple pattern recognition
        if 'error' in content:
            patterns['error_type'] = 'error_occurrence'
        if 'success' in content:
            patterns['outcome_type'] = 'success_outcome'
        if 'time' in content or 'duration' in content:
            patterns['temporal_type'] = 'time_related'
        if any(word in content for word in ['file', 'directory', 'path']):
            patterns['resource_type'] = 'file_system'
        if any(word in content for word in ['api', 'request', 'response']):
            patterns['interaction_type'] = 'api_interaction'
            
        return patterns
        
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        if not text1 or not text2:
            return 0.0
            
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
        
    def identify_exploration_targets(self, current_context: Dict[str, Any]) -> List[ExplorationTarget]:
        """
        Identify interesting targets for exploration based on current context.
        
        Args:
            current_context: Current agent context and state
            
        Returns:
            List of exploration targets ranked by interest
        """
        if not self.enabled:
            return []
            
        try:
            targets = []
            
            # Generate targets based on different strategies
            targets.extend(self._generate_knowledge_gap_targets(current_context))
            targets.extend(self._generate_uncertainty_targets(current_context))
            targets.extend(self._generate_diversity_targets(current_context))
            targets.extend(self._generate_creative_targets(current_context))
            
            # Score and rank targets
            for target in targets:
                target.exploration_priority = self._calculate_exploration_priority(target)
                
            # Sort by priority and limit
            targets.sort(key=lambda t: t.exploration_priority, reverse=True)
            self.exploration_targets = targets[:self.max_subgoals]
            
            logger.info(f"Identified {len(self.exploration_targets)} exploration targets")
            
            return self.exploration_targets
            
        except Exception as e:
            logger.error(f"Target identification failed: {e}")
            return []
            
    def _generate_knowledge_gap_targets(self, context: Dict[str, Any]) -> List[ExplorationTarget]:
        """Generate targets to fill knowledge gaps."""
        targets = []
        
        # Identify domains with low familiarity
        for domain, familiarity in self.knowledge_domains.items():
            if familiarity < 0.5:  # Low familiarity threshold
                target = ExplorationTarget(
                    id=f"knowledge_gap_{domain}_{len(targets)}",
                    description=f"Explore {domain} domain to increase familiarity",
                    novelty_score=1.0 - familiarity,
                    information_gain_potential=0.8,
                    uncertainty_level=familiarity,
                    exploration_priority=0.0  # Will be calculated later
                )
                targets.append(target)
                
        return targets
        
    def _generate_uncertainty_targets(self, context: Dict[str, Any]) -> List[ExplorationTarget]:
        """Generate targets based on areas of high uncertainty."""
        targets = []
        
        # Look for recent failures or low-confidence experiences
        recent_memories = self.memory_system.get_recent_memories(hours=24, limit=20)
        
        for memory in recent_memories:
            if memory.metadata.get('success') is False:
                target = ExplorationTarget(
                    id=f"uncertainty_{memory.id}",
                    description=f"Investigate failure: {memory.content[:50]}...",
                    novelty_score=0.6,
                    information_gain_potential=0.9,
                    uncertainty_level=0.8,
                    exploration_priority=0.0
                )
                targets.append(target)
                
        return targets[:3]  # Limit uncertainty targets
        
    def _generate_diversity_targets(self, context: Dict[str, Any]) -> List[ExplorationTarget]:
        """Generate targets to increase experience diversity."""
        targets = []
        
        # Identify underexplored action types
        action_counts = {}
        for experience in self.experience_history[-50:]:  # Recent experiences
            action_type = experience['experience'].get('type', 'unknown')
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
        # Find rare action types
        if action_counts:
            min_count = min(action_counts.values())
            rare_actions = [action for action, count in action_counts.items() 
                          if count == min_count]
            
            for action in rare_actions[:2]:  # Limit diversity targets
                target = ExplorationTarget(
                    id=f"diversity_{action}_{len(targets)}",
                    description=f"Explore underused action type: {action}",
                    novelty_score=0.7,
                    information_gain_potential=0.6,
                    uncertainty_level=0.5,
                    exploration_priority=0.0
                )
                targets.append(target)
                
        return targets
        
    def _generate_creative_targets(self, context: Dict[str, Any]) -> List[ExplorationTarget]:
        """Generate creative/experimental targets."""
        targets = []
        
        # Random creative ideas based on creativity factor
        if random.random() < self.creativity_factor:
            creative_ideas = [
                "Experiment with combining different action types",
                "Explore edge cases in familiar operations",
                "Test unusual parameter combinations",
                "Investigate system behavior under different conditions",
                "Try alternative approaches to routine tasks"
            ]
            
            selected_idea = random.choice(creative_ideas)
            target = ExplorationTarget(
                id=f"creative_{len(targets)}_{datetime.now().strftime('%H%M%S')}",
                description=selected_idea,
                novelty_score=0.9,
                information_gain_potential=0.5,
                uncertainty_level=0.7,
                exploration_priority=0.0
            )
            targets.append(target)
            
        return targets
        
    def _calculate_exploration_priority(self, target: ExplorationTarget) -> float:
        """Calculate exploration priority for a target."""
        # Combine scoring factors
        priority = (
            target.novelty_score * self.scoring_weights['information_gain'] +
            target.information_gain_potential * self.scoring_weights['uncertainty'] +
            target.uncertainty_level * self.scoring_weights['diversity']
        )
        
        # Apply penalties for repeated attempts
        if target.attempts > 0:
            priority *= (0.8 ** target.attempts)  # Exponential decay
            
        # Apply recency bonus/penalty
        if target.last_attempted:
            hours_since = (datetime.now() - target.last_attempted).total_seconds() / 3600
            if hours_since < 1:
                priority *= 0.5  # Recent attempt penalty
            elif hours_since > 24:
                priority *= 1.2  # Old attempt bonus
                
        return priority
        
    def generate_curious_subgoals(self, main_goal: str, 
                                 current_plan: Dict[str, Any]) -> List[str]:
        """
        Generate curious subgoals to explore alongside the main goal.
        
        Args:
            main_goal: The primary goal being pursued
            current_plan: Current execution plan
            
        Returns:
            List of curious subgoal descriptions
        """
        if not self.enabled:
            return []
            
        try:
            subgoals = []
            
            # Analyze main goal for exploration opportunities
            goal_novelty = self.calculate_novelty_score({
                'type': 'goal',
                'content': main_goal,
                'context': current_plan
            })
            
            if goal_novelty > self.novelty_threshold:
                # Generate exploration subgoals for novel goals
                subgoals.extend(self._generate_goal_exploration_subgoals(main_goal))
                
            # Add general curiosity subgoals
            targets = self.identify_exploration_targets({'main_goal': main_goal})
            for target in targets[:3]:  # Limit to top 3
                subgoals.append(f"CURIOUS: {target.description}")
                
            return subgoals[:self.max_subgoals]
            
        except Exception as e:
            logger.error(f"Subgoal generation failed: {e}")
            return []
            
    def _generate_goal_exploration_subgoals(self, main_goal: str) -> List[str]:
        """Generate exploration subgoals related to the main goal."""
        subgoals = []
        
        goal_words = main_goal.lower().split()
        
        # Generate related exploration goals
        if 'analyze' in goal_words:
            subgoals.append("CURIOUS: Explore alternative analysis methods")
        if 'create' in goal_words:
            subgoals.append("CURIOUS: Investigate creative variations")
        if 'optimize' in goal_words:
            subgoals.append("CURIOUS: Test edge case optimizations")
        if 'automate' in goal_words:
            subgoals.append("CURIOUS: Explore automation failure modes")
            
        return subgoals
        
    def record_exploration_result(self, target_id: str, success: bool, 
                                 result_data: Dict[str, Any]):
        """
        Record the result of an exploration attempt.
        
        Args:
            target_id: ID of the exploration target
            success: Whether the exploration was successful
            result_data: Data from the exploration
        """
        try:
            # Find the target
            target = None
            for t in self.exploration_targets:
                if t.id == target_id:
                    target = t
                    break
                    
            if not target:
                logger.warning(f"Exploration target not found: {target_id}")
                return
                
            # Update target
            target.attempts += 1
            target.last_attempted = datetime.now()
            
            # Calculate information gain
            information_gained = self._calculate_information_gain(result_data, success)
            
            # Store exploration memory
            self.memory_system.store_memory(
                content=f"Curiosity exploration: {target.description}",
                memory_type='curiosity_exploration',
                metadata={
                    'target_id': target_id,
                    'target_description': target.description,
                    'success': success,
                    'information_gain': information_gained,
                    'result_data': result_data
                },
                importance=0.7 + (information_gained * 0.3)
            )
            
            # Generate insights if significant
            if information_gained > 0.7:
                insight = self._generate_insight(target, result_data, success)
                if insight:
                    self.discovered_insights.append(insight)
                    
            logger.info(f"Recorded exploration result: {target_id} - Success: {success}")
            
        except Exception as e:
            logger.error(f"Failed to record exploration result: {e}")
            
    def _calculate_information_gain(self, result_data: Dict[str, Any], 
                                  success: bool) -> float:
        """Calculate how much information was gained from exploration."""
        # Simple heuristic - could be enhanced with more sophisticated methods
        base_gain = 0.5 if success else 0.3
        
        # More gain for unexpected results
        if 'unexpected' in str(result_data).lower():
            base_gain += 0.2
            
        # More gain for errors with useful information
        if not success and result_data.get('error'):
            base_gain += 0.1
            
        # More gain for novel patterns
        if result_data.get('novel_patterns'):
            base_gain += 0.2
            
        return min(1.0, base_gain)
        
    def _generate_insight(self, target: ExplorationTarget, result_data: Dict[str, Any], 
                         success: bool) -> Optional[CuriosityInsight]:
        """Generate an insight from exploration results."""
        try:
            if success:
                insight_type = "successful_exploration"
                description = f"Successful exploration of {target.description} revealed useful patterns"
            else:
                insight_type = "failure_pattern"
                description = f"Failed exploration of {target.description} revealed limitation patterns"
                
            insight = CuriosityInsight(
                insight_type=insight_type,
                description=description,
                confidence=0.8,
                supporting_evidence=[str(result_data)]
            )
            
            return insight
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return None
            
    def get_curiosity_stats(self) -> Dict[str, Any]:
        """Get curiosity engine statistics."""
        return {
            'enabled': self.enabled,
            'novelty_threshold': self.novelty_threshold,
            'exploration_rate': self.exploration_rate,
            'total_experiences': len(self.experience_history),
            'active_targets': len(self.exploration_targets),
            'discovered_insights': len(self.discovered_insights),
            'knowledge_domains': len(self.knowledge_domains),
            'pattern_types': len(self.pattern_library),
            'recent_novelty_scores': [
                exp.get('novelty_score', 0) 
                for exp in self.experience_history[-10:]
            ]
        }
        
    def get_learning_insights(self) -> List[Dict[str, Any]]:
        """Get insights discovered through curiosity."""
        return [insight.to_dict() for insight in self.discovered_insights[-10:]]
        
    def suggest_exploration_goal(self) -> Optional[str]:
        """Suggest a goal for curious exploration."""
        if not self.enabled or not self.exploration_targets:
            return None
            
        # Get highest priority unexplored target
        for target in self.exploration_targets:
            if target.attempts == 0:
                return target.description
                
        # If all explored, suggest re-exploring with highest information gain
        best_target = max(self.exploration_targets, 
                         key=lambda t: t.information_gain_potential)
        return f"Re-explore: {best_target.description}" 