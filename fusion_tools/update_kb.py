#!/usr/bin/env python3
"""
Knowledge Base Update System
Logs corrections and updates the KB with learning feedback for continuous improvement
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fusion_absorb_with_kb import KnowledgeBaseFusion

logger = logging.getLogger(__name__)

@dataclass
class CorrectionData:
    """Data class for correction information"""
    timestamp: str
    original_code: str
    corrected_code: str
    error_type: str
    confidence: float
    explanation: str
    language: str
    user_feedback: Optional[str] = None
    rating: Optional[int] = None
    piraz_compatibility: bool = True
    fixes_applied: List[str] = None
    
    def __post_init__(self):
        if self.fixes_applied is None:
            self.fixes_applied = []

class KnowledgeBaseUpdater:
    """Manages knowledge base updates and learning feedback"""
    
    def __init__(self, kb_file: str = "piraz_os_kb.json"):
        self.kb_file = kb_file
        self.kb_fusion = KnowledgeBaseFusion(kb_file=kb_file)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Load current KB
        self.load_kb()
        
    def load_kb(self):
        """Load current knowledge base"""
        try:
            self.kb_data = self.kb_fusion.load_knowledge_base()
            self.piraz_os = self.kb_data.get('piraz_os', {})
            
            # Ensure learning feedback structure exists
            if 'learning_feedback' not in self.piraz_os:
                self.piraz_os['learning_feedback'] = {
                    'correction_history': [],
                    'pattern_improvements': [],
                    'new_error_patterns': [],
                    'common_mistakes': {},
                    'performance_metrics': {
                        'total_corrections': 0,
                        'successful_fixes': 0,
                        'average_confidence': 0.0,
                        'improvement_rate': 0.0
                    }
                }
                self.save_kb()
            
            logger.info(f"✅ Knowledge base loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load knowledge base: {e}")
            raise
    
    def save_kb(self):
        """Save knowledge base to file"""
        try:
            self.kb_data['piraz_os']['last_updated'] = datetime.now().isoformat()
            
            with open(self.kb_file, 'w') as f:
                json.dump(self.kb_data, f, indent=2)
            
            logger.info(f"✅ Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to save knowledge base: {e}")
            raise
    
    def log_correction(self, correction: CorrectionData) -> bool:
        """Log a single correction to the knowledge base"""
        try:
            learning_feedback = self.piraz_os['learning_feedback']
            
            # Add to correction history
            correction_dict = asdict(correction)
            learning_feedback['correction_history'].append(correction_dict)
            
            # Update performance metrics
            self.update_performance_metrics(correction)
            
            # Analyze for patterns
            self.analyze_correction_patterns(correction)
            
            # Update common mistakes
            self.update_common_mistakes(correction)
            
            # Keep history limited to last 1000 entries
            if len(learning_feedback['correction_history']) > 1000:
                learning_feedback['correction_history'] = learning_feedback['correction_history'][-1000:]
            
            logger.info(f"✅ Logged correction: {correction.error_type} (confidence: {correction.confidence})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log correction: {e}")
            return False
    
    def update_performance_metrics(self, correction: CorrectionData):
        """Update performance metrics based on correction"""
        metrics = self.piraz_os['learning_feedback']['performance_metrics']
        
        # Update total corrections
        metrics['total_corrections'] += 1
        
        # Update successful fixes (based on confidence and user feedback)
        if correction.confidence > 0.7:
            metrics['successful_fixes'] += 1
        
        # Update average confidence
        history = self.piraz_os['learning_feedback']['correction_history']
        if history:
            confidences = [c.get('confidence', 0) for c in history]
            metrics['average_confidence'] = sum(confidences) / len(confidences)
        
        # Calculate improvement rate (successful fixes / total corrections)
        if metrics['total_corrections'] > 0:
            metrics['improvement_rate'] = metrics['successful_fixes'] / metrics['total_corrections']
    
    def analyze_correction_patterns(self, correction: CorrectionData):
        """Analyze correction for patterns and learning opportunities"""
        try:
            pattern_improvements = self.piraz_os['learning_feedback']['pattern_improvements']
            
            # Check for new error patterns
            if correction.error_type not in [p.get('error_type') for p in pattern_improvements]:
                new_pattern = {
                    'error_type': correction.error_type,
                    'first_seen': correction.timestamp,
                    'frequency': 1,
                    'avg_confidence': correction.confidence,
                    'common_fixes': correction.fixes_applied[:3],  # Top 3 fixes
                    'languages': [correction.language],
                    'example_code': correction.original_code[:200] + "..." if len(correction.original_code) > 200 else correction.original_code
                }
                pattern_improvements.append(new_pattern)
            else:
                # Update existing pattern
                for pattern in pattern_improvements:
                    if pattern['error_type'] == correction.error_type:
                        pattern['frequency'] += 1
                        pattern['avg_confidence'] = (pattern['avg_confidence'] + correction.confidence) / 2
                        
                        # Update common fixes
                        for fix in correction.fixes_applied:
                            if fix not in pattern['common_fixes']:
                                pattern['common_fixes'].append(fix)
                        
                        # Update languages
                        if correction.language not in pattern['languages']:
                            pattern['languages'].append(correction.language)
                        
                        break
            
            # Keep only top 50 patterns
            pattern_improvements.sort(key=lambda x: x['frequency'], reverse=True)
            self.piraz_os['learning_feedback']['pattern_improvements'] = pattern_improvements[:50]
            
        except Exception as e:
            logger.error(f"❌ Error analyzing correction patterns: {e}")
    
    def update_common_mistakes(self, correction: CorrectionData):
        """Update common mistakes tracking"""
        try:
            common_mistakes = self.piraz_os['learning_feedback']['common_mistakes']
            
            # Extract mistake patterns from original code
            if correction.original_code:
                mistake_key = f"{correction.language}_{correction.error_type}"
                
                if mistake_key not in common_mistakes:
                    common_mistakes[mistake_key] = {
                        'error_type': correction.error_type,
                        'language': correction.language,
                        'count': 1,
                        'avg_confidence': correction.confidence,
                        'last_seen': correction.timestamp,
                        'typical_fixes': correction.fixes_applied[:3]
                    }
                else:
                    mistake = common_mistakes[mistake_key]
                    mistake['count'] += 1
                    mistake['avg_confidence'] = (mistake['avg_confidence'] + correction.confidence) / 2
                    mistake['last_seen'] = correction.timestamp
                    
                    # Update typical fixes
                    for fix in correction.fixes_applied:
                        if fix not in mistake['typical_fixes']:
                            mistake['typical_fixes'].append(fix)
                    
                    # Keep only top 5 fixes
                    mistake['typical_fixes'] = mistake['typical_fixes'][:5]
            
        except Exception as e:
            logger.error(f"❌ Error updating common mistakes: {e}")
    
    def batch_update_corrections(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update knowledge base with multiple corrections"""
        try:
            successful_updates = 0
            failed_updates = 0
            
            for correction_data in corrections:
                try:
                    # Convert dict to CorrectionData
                    correction = CorrectionData(
                        timestamp=correction_data.get('timestamp', datetime.now().isoformat()),
                        original_code=correction_data.get('original_code', ''),
                        corrected_code=correction_data.get('corrected_code', ''),
                        error_type=correction_data.get('error_type', 'unknown'),
                        confidence=correction_data.get('confidence', 0.5),
                        explanation=correction_data.get('explanation', ''),
                        language=correction_data.get('language', 'python'),
                        user_feedback=correction_data.get('user_feedback'),
                        rating=correction_data.get('rating'),
                        piraz_compatibility=correction_data.get('piraz_compatibility', True),
                        fixes_applied=correction_data.get('fixes_applied', [])
                    )
                    
                    if self.log_correction(correction):
                        successful_updates += 1
                    else:
                        failed_updates += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing correction: {e}")
                    failed_updates += 1
            
            # Save updated KB
            self.save_kb()
            
            result = {
                'successful_updates': successful_updates,
                'failed_updates': failed_updates,
                'total_corrections': len(corrections),
                'kb_version': self.piraz_os.get('version', '1.0.0'),
                'last_updated': self.piraz_os.get('last_updated')
            }
            
            logger.info(f"✅ Batch update completed: {successful_updates} successful, {failed_updates} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            return {'error': str(e)}
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics and insights"""
        try:
            learning_feedback = self.piraz_os.get('learning_feedback', {})
            
            # Calculate statistics
            correction_history = learning_feedback.get('correction_history', [])
            pattern_improvements = learning_feedback.get('pattern_improvements', [])
            common_mistakes = learning_feedback.get('common_mistakes', {})
            metrics = learning_feedback.get('performance_metrics', {})
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_corrections = [
                c for c in correction_history 
                if datetime.fromisoformat(c.get('timestamp', '1970-01-01')) > recent_cutoff
            ]
            
            # Error type distribution
            error_types = {}
            for correction in correction_history:
                error_type = correction.get('error_type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Language distribution
            languages = {}
            for correction in correction_history:
                language = correction.get('language', 'unknown')
                languages[language] = languages.get(language, 0) + 1
            
            # Top patterns by frequency
            top_patterns = sorted(pattern_improvements, key=lambda x: x.get('frequency', 0), reverse=True)[:10]
            
            return {
                'total_corrections': len(correction_history),
                'recent_corrections_24h': len(recent_corrections),
                'avg_confidence': metrics.get('average_confidence', 0.0),
                'improvement_rate': metrics.get('improvement_rate', 0.0),
                'error_type_distribution': error_types,
                'language_distribution': languages,
                'top_patterns': top_patterns,
                'common_mistakes_count': len(common_mistakes),
                'kb_version': self.piraz_os.get('version', '1.0.0'),
                'last_updated': self.piraz_os.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting learning stats: {e}")
            return {'error': str(e)}
    
    def suggest_kb_improvements(self) -> List[Dict[str, Any]]:
        """Suggest improvements to the knowledge base based on learning data"""
        try:
            suggestions = []
            
            learning_feedback = self.piraz_os.get('learning_feedback', {})
            pattern_improvements = learning_feedback.get('pattern_improvements', [])
            common_mistakes = learning_feedback.get('common_mistakes', {})
            
            # Suggest new error codes based on frequent patterns
            for pattern in pattern_improvements:
                if pattern.get('frequency', 0) > 5:  # Frequent pattern
                    error_code = f"PIRAZ_ERR_{len(self.piraz_os.get('error_codes', {})) + 1:03d}"
                    suggestions.append({
                        'type': 'new_error_code',
                        'priority': 'high',
                        'suggestion': f"Add error code {error_code} for {pattern['error_type']}",
                        'rationale': f"Pattern occurs {pattern['frequency']} times",
                        'proposed_error_code': error_code,
                        'error_type': pattern['error_type'],
                        'frequency': pattern['frequency']
                    })
            
            # Suggest validation rule improvements
            for mistake_key, mistake in common_mistakes.items():
                if mistake.get('count', 0) > 3:  # Common mistake
                    suggestions.append({
                        'type': 'validation_rule_improvement',
                        'priority': 'medium',
                        'suggestion': f"Improve validation for {mistake['error_type']} in {mistake['language']}",
                        'rationale': f"Common mistake ({mistake['count']} occurrences)",
                        'error_type': mistake['error_type'],
                        'language': mistake['language'],
                        'count': mistake['count']
                    })
            
            # Suggest command syntax additions
            if len(pattern_improvements) > 20:  # Significant learning data
                suggestions.append({
                    'type': 'command_syntax_expansion',
                    'priority': 'low',
                    'suggestion': "Consider adding more command syntax examples",
                    'rationale': "Sufficient learning data available to identify common patterns",
                    'data_points': len(pattern_improvements)
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Error generating suggestions: {e}")
            return []
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old correction data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            learning_feedback = self.piraz_os['learning_feedback']
            correction_history = learning_feedback.get('correction_history', [])
            
            # Count old entries
            old_entries = [
                c for c in correction_history 
                if datetime.fromisoformat(c.get('timestamp', '1970-01-01')) < cutoff_date
            ]
            
            # Keep only recent entries
            recent_entries = [
                c for c in correction_history 
                if datetime.fromisoformat(c.get('timestamp', '1970-01-01')) >= cutoff_date
            ]
            
            learning_feedback['correction_history'] = recent_entries
            
            # Save updated KB
            self.save_kb()
            
            result = {
                'removed_entries': len(old_entries),
                'remaining_entries': len(recent_entries),
                'cutoff_date': cutoff_date.isoformat(),
                'cleanup_successful': True
            }
            
            logger.info(f"✅ Cleanup completed: {len(old_entries)} old entries removed")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {'error': str(e), 'cleanup_successful': False}

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Updater")
    parser.add_argument('--kb-file', default='piraz_os_kb.json', help='Knowledge base file path')
    parser.add_argument('--stats', action='store_true', help='Show learning statistics')
    parser.add_argument('--suggestions', action='store_true', help='Show improvement suggestions')
    parser.add_argument('--cleanup', type=int, help='Clean up data older than N days')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    # Commands for testing
    parser.add_argument('--test-correction', action='store_true', help='Add test correction')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = KnowledgeBaseUpdater(kb_file=args.kb_file)
    
    if args.stats:
        print("📊 Learning Statistics:")
        print("=" * 50)
        stats = updater.get_learning_stats()
        
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            return 1
        
        print(f"Total Corrections: {stats['total_corrections']}")
        print(f"Recent Corrections (24h): {stats['recent_corrections_24h']}")
        print(f"Average Confidence: {stats['avg_confidence']:.2f}")
        print(f"Improvement Rate: {stats['improvement_rate']:.2%}")
        print(f"KB Version: {stats['kb_version']}")
        print(f"Last Updated: {stats['last_updated']}")
        
        print("\n🔍 Error Type Distribution:")
        for error_type, count in stats['error_type_distribution'].items():
            print(f"  - {error_type}: {count}")
        
        print("\n💻 Language Distribution:")
        for language, count in stats['language_distribution'].items():
            print(f"  - {language}: {count}")
        
        print("\n📈 Top Patterns:")
        for pattern in stats['top_patterns']:
            print(f"  - {pattern['error_type']}: {pattern['frequency']} occurrences")
        
        return 0
    
    if args.suggestions:
        print("💡 Improvement Suggestions:")
        print("=" * 50)
        suggestions = updater.suggest_kb_improvements()
        
        if not suggestions:
            print("No suggestions available.")
            return 0
        
        for suggestion in suggestions:
            print(f"[{suggestion['priority'].upper()}] {suggestion['suggestion']}")
            print(f"  Rationale: {suggestion['rationale']}")
            print()
        
        return 0
    
    if args.cleanup:
        print(f"🧹 Cleaning up data older than {args.cleanup} days...")
        result = updater.cleanup_old_data(days_old=args.cleanup)
        
        if result.get('cleanup_successful'):
            print(f"✅ Cleanup completed:")
            print(f"  - Removed entries: {result['removed_entries']}")
            print(f"  - Remaining entries: {result['remaining_entries']}")
            print(f"  - Cutoff date: {result['cutoff_date']}")
        else:
            print(f"❌ Cleanup failed: {result.get('error', 'unknown')}")
            return 1
        
        return 0
    
    if args.test_correction:
        print("🧪 Adding test correction...")
        test_correction = CorrectionData(
            timestamp=datetime.now().isoformat(),
            original_code='print("Hello")',
            corrected_code='logger.info("Hello")',
            error_type='logging_improvement',
            confidence=0.9,
            explanation='Replaced print with logging for better practice',
            language='python',
            fixes_applied=['replace_print_with_logging']
        )
        
        success = updater.log_correction(test_correction)
        if success:
            updater.save_kb()
            print("✅ Test correction added successfully")
        else:
            print("❌ Failed to add test correction")
            return 1
        
        return 0
    
    print("Knowledge Base Updater")
    print("Use --help for available options")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 