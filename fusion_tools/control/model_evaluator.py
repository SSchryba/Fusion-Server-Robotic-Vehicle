#!/usr/bin/env python3
"""
Model Evaluator for Fusion System
Evaluates model performance and selects top performers for fusion
"""

import logging
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

@dataclass
class ModelEvaluation:
    """Model evaluation results"""
    model_name: str
    overall_score: float
    capability_scores: Dict[str, float]
    performance_metrics: Dict[str, float]
    meets_constraints: bool
    recommendation: str  # 'include', 'exclude', 'deprioritize'
    reasons: List[str]

class ModelEvaluator:
    """Evaluates models for fusion eligibility and ranking"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        self.constraints = self.config.model_constraints
        self.requirements = self.config.capability_requirements
        self.evaluation_criteria = self.config.evaluation_criteria
        self.priority_models = self.config.priority_models
        
    def evaluate_model(self, model_name: str) -> ModelEvaluation:
        """Evaluate a single model"""
        logger.info(f"Evaluating model: {model_name}")
        
        # Get model performance data
        performance_data = self.api_client.evaluate_model_performance(model_name)
        
        # Calculate capability scores
        capability_scores = self._calculate_capability_scores(performance_data)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(performance_data, capability_scores)
        
        # Check constraints
        meets_constraints, constraint_reasons = self._check_constraints(performance_data)
        
        # Generate recommendation
        recommendation, reasons = self._generate_recommendation(
            model_name, performance_data, capability_scores, meets_constraints
        )
        
        return ModelEvaluation(
            model_name=model_name,
            overall_score=overall_score,
            capability_scores=capability_scores,
            performance_metrics=performance_data,
            meets_constraints=meets_constraints,
            recommendation=recommendation,
            reasons=reasons + constraint_reasons
        )
    
    def evaluate_all_models(self) -> List[ModelEvaluation]:
        """Evaluate all available models"""
        models = self.api_client.get_available_models()
        evaluations = []
        
        logger.info(f"Evaluating {len(models)} models")
        
        for model in models:
            try:
                evaluation = self.evaluate_model(model)
                evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"Failed to evaluate model {model}: {e}")
        
        return evaluations
    
    def select_top_models(self, evaluations: List[ModelEvaluation], count: int = 3) -> List[ModelEvaluation]:
        """Select top performing models for fusion"""
        # Filter out excluded models
        eligible_models = [e for e in evaluations if e.recommendation != 'exclude']
        
        # Sort by priority and score
        def sort_key(evaluation: ModelEvaluation) -> Tuple[int, float]:
            # Priority boost for priority models
            priority_boost = 1.0 if evaluation.model_name in self.priority_models else 0.0
            
            # Penalty for deprioritized models
            depriority_penalty = -0.5 if evaluation.recommendation == 'deprioritize' else 0.0
            
            # Final score
            final_score = evaluation.overall_score + priority_boost + depriority_penalty
            
            return (1 if evaluation.meets_constraints else 0, final_score)
        
        # Sort by constraints first, then by score
        eligible_models.sort(key=sort_key, reverse=True)
        
        # Select top models ensuring diversity
        selected_models = self._ensure_diversity(eligible_models, count)
        
        logger.info(f"Selected {len(selected_models)} top models for fusion")
        for model in selected_models:
            logger.info(f"  - {model.model_name}: {model.overall_score:.2f}")
        
        return selected_models
    
    def _calculate_capability_scores(self, performance_data: Dict) -> Dict[str, float]:
        """Calculate capability scores based on performance data"""
        capabilities = performance_data.get('capabilities', {})
        
        # Normalize and validate capability scores
        normalized_scores = {}
        for capability, score in capabilities.items():
            # Ensure score is between 0 and 10
            normalized_score = max(0, min(10, score))
            normalized_scores[capability] = normalized_score
        
        return normalized_scores
    
    def _calculate_overall_score(self, performance_data: Dict, capability_scores: Dict[str, float]) -> float:
        """Calculate overall model score based on multiple criteria"""
        
        # Performance component (40%)
        performance_score = performance_data.get('overall_score', 0)
        performance_component = performance_score * self.evaluation_criteria.get('performance_weight', 0.4)
        
        # Capability component (30%)
        capability_component = 0
        if capability_scores:
            avg_capability = sum(capability_scores.values()) / len(capability_scores)
            capability_component = avg_capability * self.evaluation_criteria.get('capability_weight', 0.3)
        
        # Efficiency component (20%)
        response_time = performance_data.get('response_time', 10)
        efficiency_score = max(0, 10 - response_time)  # Lower response time = higher efficiency
        efficiency_component = efficiency_score * self.evaluation_criteria.get('efficiency_weight', 0.2)
        
        # Reliability component (10%)
        error_rate = performance_data.get('error_rate', 0.1)
        hallucination_rate = performance_data.get('hallucination_rate', 0.1)
        reliability_score = max(0, 10 - (error_rate * 50 + hallucination_rate * 50))
        reliability_component = reliability_score * self.evaluation_criteria.get('reliability_weight', 0.1)
        
        # Total score
        total_score = performance_component + capability_component + efficiency_component + reliability_component
        
        return round(total_score, 2)
    
    def _check_constraints(self, performance_data: Dict) -> Tuple[bool, List[str]]:
        """Check if model meets all constraints"""
        reasons = []
        meets_constraints = True
        
        # Check capability threshold
        overall_score = performance_data.get('overall_score', 0)
        if overall_score < self.constraints.min_capability_threshold:
            meets_constraints = False
            reasons.append(f"Overall score {overall_score} below threshold {self.constraints.min_capability_threshold}")
        
        # Check hallucination rate
        hallucination_rate = performance_data.get('hallucination_rate', 0)
        if hallucination_rate > self.constraints.max_hallucination_rate:
            meets_constraints = False
            reasons.append(f"Hallucination rate {hallucination_rate} above limit {self.constraints.max_hallucination_rate}")
        
        # Check parameter size (simplified check)
        model_name = performance_data.get('model', '')
        if not self._check_parameter_size(model_name):
            meets_constraints = False
            reasons.append(f"Model size exceeds limit {self.constraints.max_parameter_size}")
        
        # Check disqualification rules
        rule_action = self.config_loader.evaluate_model_against_rules(performance_data)
        if rule_action == 'remove':
            meets_constraints = False
            reasons.append("Model violates disqualification rules")
        
        return meets_constraints, reasons
    
    def _check_parameter_size(self, model_name: str) -> bool:
        """Check if model size is within limits"""
        max_size = self.constraints.max_parameter_size.upper()
        
        # Extract size from model name
        size_indicators = ['70B', '33B', '13B', '7B', '6.7B', '2B', '1B']
        
        max_size_value = self._parse_size(max_size)
        
        for indicator in size_indicators:
            if indicator in model_name.upper():
                model_size_value = self._parse_size(indicator)
                return model_size_value <= max_size_value
        
        # If no size indicator found, assume it's within limits
        return True
    
    def _parse_size(self, size_str: str) -> float:
        """Parse size string to numeric value"""
        size_str = size_str.upper().replace('B', '')
        try:
            return float(size_str)
        except ValueError:
            return 0.0
    
    def _generate_recommendation(self, model_name: str, performance_data: Dict, 
                                capability_scores: Dict[str, float], meets_constraints: bool) -> Tuple[str, List[str]]:
        """Generate recommendation for model inclusion"""
        reasons = []
        
        # Check disqualification rules first
        rule_action = self.config_loader.evaluate_model_against_rules(performance_data)
        if rule_action == 'remove':
            return 'exclude', ['Model violates disqualification rules']
        elif rule_action == 'deprioritize':
            reasons.append('Model flagged for deprioritization')
        
        # Check if model meets basic constraints
        if not meets_constraints:
            return 'exclude', reasons + ['Model does not meet basic constraints']
        
        # Check capability requirements
        for capability, min_score in self.requirements.items():
            if capability in capability_scores:
                if capability_scores[capability] < min_score:
                    reasons.append(f"Low {capability} score: {capability_scores[capability]}")
        
        # Priority models get preference
        if model_name in self.priority_models:
            reasons.append('Priority model')
            return 'include', reasons
        
        # Check overall performance
        overall_score = performance_data.get('overall_score', 0)
        if overall_score >= 8.0:
            reasons.append('High overall performance')
            return 'include', reasons
        elif overall_score >= 6.0:
            reasons.append('Adequate performance')
            return 'include' if rule_action != 'deprioritize' else 'deprioritize', reasons
        else:
            reasons.append('Low overall performance')
            return 'deprioritize', reasons
    
    def _ensure_diversity(self, models: List[ModelEvaluation], count: int) -> List[ModelEvaluation]:
        """Ensure diversity in selected models"""
        if len(models) <= count:
            return models
        
        selected = []
        model_families = {}
        
        # Group by model family
        for model in models:
            family = model.model_name.split(':')[0]
            if family not in model_families:
                model_families[family] = []
            model_families[family].append(model)
        
        # Select one from each family first
        for family, family_models in model_families.items():
            if len(selected) >= count:
                break
            # Select best from this family
            best_model = max(family_models, key=lambda m: m.overall_score)
            selected.append(best_model)
        
        # Fill remaining slots with highest scores
        remaining_models = [m for m in models if m not in selected]
        remaining_needed = count - len(selected)
        
        if remaining_needed > 0:
            remaining_models.sort(key=lambda m: m.overall_score, reverse=True)
            selected.extend(remaining_models[:remaining_needed])
        
        return selected[:count]
    
    def generate_evaluation_report(self, evaluations: List[ModelEvaluation]) -> str:
        """Generate a comprehensive evaluation report"""
        report = []
        report.append("🔍 MODEL EVALUATION REPORT")
        report.append("=" * 50)
        
        # Summary statistics
        total_models = len(evaluations)
        eligible_models = len([e for e in evaluations if e.recommendation == 'include'])
        excluded_models = len([e for e in evaluations if e.recommendation == 'exclude'])
        
        report.append(f"\nSUMMARY:")
        report.append(f"Total Models Evaluated: {total_models}")
        report.append(f"Eligible for Fusion: {eligible_models}")
        report.append(f"Excluded: {excluded_models}")
        
        # Top performers
        top_models = sorted(evaluations, key=lambda e: e.overall_score, reverse=True)[:5]
        report.append(f"\nTOP PERFORMERS:")
        for i, model in enumerate(top_models, 1):
            report.append(f"{i}. {model.model_name}: {model.overall_score:.2f}")
        
        # Detailed evaluations
        report.append(f"\nDETAILED EVALUATIONS:")
        for evaluation in sorted(evaluations, key=lambda e: e.overall_score, reverse=True):
            report.append(f"\n📊 {evaluation.model_name}")
            report.append(f"   Overall Score: {evaluation.overall_score:.2f}")
            report.append(f"   Recommendation: {evaluation.recommendation}")
            report.append(f"   Meets Constraints: {evaluation.meets_constraints}")
            
            if evaluation.capability_scores:
                report.append(f"   Capabilities:")
                for capability, score in evaluation.capability_scores.items():
                    report.append(f"     - {capability}: {score:.1f}")
            
            if evaluation.reasons:
                report.append(f"   Reasons: {', '.join(evaluation.reasons)}")
        
        return "\n".join(report)

def main():
    """Main entry point for testing"""
    evaluator = ModelEvaluator()
    
    # Evaluate all models
    evaluations = evaluator.evaluate_all_models()
    
    # Select top models
    top_models = evaluator.select_top_models(evaluations, 3)
    
    # Generate report
    report = evaluator.generate_evaluation_report(evaluations)
    print(report)
    
    print(f"\nSelected for fusion: {[m.model_name for m in top_models]}")

if __name__ == "__main__":
    main() 