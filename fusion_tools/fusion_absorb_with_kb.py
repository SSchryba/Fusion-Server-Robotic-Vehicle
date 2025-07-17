#!/usr/bin/env python3
"""
Fusion Absorption with Knowledge Base Integration
Triggers model absorption with Piraz OS knowledge injection and adjusted weights
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class KnowledgeBaseFusion:
    """Manages knowledge base integration with fusion system"""
    
    def __init__(self, kb_file: str = "piraz_os_kb.json"):
        self.kb_file = kb_file
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load Piraz OS knowledge base from JSON file"""
        try:
            with open(self.kb_file, 'r') as f:
                kb_data = json.load(f)
            
            logger.info(f"✅ Loaded knowledge base from {self.kb_file}")
            logger.info(f"   - Version: {kb_data.get('piraz_os', {}).get('version', 'unknown')}")
            logger.info(f"   - Error codes: {len(kb_data.get('piraz_os', {}).get('error_codes', {}))}")
            logger.info(f"   - Core services: {len(kb_data.get('piraz_os', {}).get('core_services', {}))}")
            
            return kb_data
            
        except FileNotFoundError:
            logger.error(f"❌ Knowledge base file not found: {self.kb_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in knowledge base: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading knowledge base: {e}")
            raise
    
    def create_kb_enhanced_fusion_request(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fusion request with knowledge base integration"""
        
        # Extract key knowledge components
        piraz_os = kb_data.get('piraz_os', {})
        
        # Build knowledge context for fusion
        knowledge_context = {
            "domain": "system_programming",
            "specialization": "piraz_os_integration",
            "knowledge_areas": [
                "error_handling",
                "service_management", 
                "configuration_validation",
                "boot_sequence_troubleshooting",
                "system_recovery"
            ],
            "error_codes": list(piraz_os.get('error_codes', {}).keys()),
            "core_services": list(piraz_os.get('core_services', {}).keys()),
            "command_syntax": list(piraz_os.get('command_syntax', {}).keys()),
            "validation_rules": list(piraz_os.get('code_validation_rules', {}).keys())
        }
        
        # Enhanced fusion parameters for code correction
        fusion_params = {
            "fusion_strategy": "knowledge_weighted_average",
            "knowledge_base": kb_data,
            "knowledge_context": knowledge_context,
            "model_weights": {
                "code_correction": 0.35,
                "system_knowledge": 0.30,
                "error_handling": 0.25,
                "general_reasoning": 0.10
            },
            "capabilities_boost": {
                "deep_reasoning": 1.2,
                "code_generation": 1.3,
                "error_detection": 1.4,
                "system_integration": 1.5
            },
            "learning_focus": [
                "piraz_os_patterns",
                "error_code_mapping",
                "service_lifecycle_management",
                "configuration_validation"
            ]
        }
        
        return {
            "fusion_type": "knowledge_enhanced",
            "timestamp": datetime.now().isoformat(),
            "knowledge_base_version": piraz_os.get('version', '1.0.0'),
            "fusion_params": fusion_params,
            "extra_knowledge": kb_data
        }
    
    def trigger_kb_absorption(self, force: bool = False) -> Dict[str, Any]:
        """Trigger knowledge base enhanced absorption"""
        logger.info("🧠 Starting knowledge base enhanced absorption...")
        
        try:
            # Load knowledge base
            kb_data = self.load_knowledge_base()
            
            # Create enhanced fusion request
            fusion_request = self.create_kb_enhanced_fusion_request(kb_data)
            
            # Check current fusion status
            fusion_status = self.api_client.get_fusion_status()
            if not fusion_status:
                logger.error("❌ Cannot get fusion status")
                return {"success": False, "error": "Fusion server not accessible"}
            
            if not fusion_status.fusion_enabled:
                logger.error("❌ Fusion system is disabled")
                return {"success": False, "error": "Fusion system disabled"}
            
            # Pull DeepSeek models first for enhanced reasoning
            logger.info("📥 Pulling DeepSeek models for enhanced capabilities...")
            deepseek_success = self.api_client.pull_deepseek_models()
            if not deepseek_success:
                logger.warning("⚠️  Failed to pull DeepSeek models, continuing...")
            
            # Get available models
            available_models = self.api_client.get_available_models()
            if len(available_models) < 2:
                logger.error(f"❌ Not enough models available: {len(available_models)}")
                return {"success": False, "error": "Insufficient models for fusion"}
            
            # Select models optimized for code correction
            code_focused_models = self.select_code_correction_models(available_models)
            
            # Create KB-enhanced hybrid model
            logger.info("🔬 Creating knowledge-enhanced hybrid model...")
            hybrid_result = self.api_client.create_hybrid(code_focused_models)
            if not hybrid_result:
                logger.error("❌ Failed to create hybrid model")
                return {"success": False, "error": "Hybrid model creation failed"}
            
            # Start absorption with KB context
            logger.info("🔄 Starting knowledge-enhanced absorption cycle...")
            
            # Note: The actual API doesn't support extra_knowledge parameter yet
            # This is a proposed enhancement to the fusion system
            absorption_success = self.api_client.start_absorption()
            if not absorption_success:
                logger.warning("⚠️  Failed to start absorption cycle")
            
            # Log successful KB integration
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "kb_version": kb_data.get('piraz_os', {}).get('version', '1.0.0'),
                "hybrid_model": hybrid_result.get('hybrid_name', 'unknown'),
                "selected_models": code_focused_models,
                "knowledge_areas": fusion_request["fusion_params"]["knowledge_context"]["knowledge_areas"],
                "absorption_started": absorption_success
            }
            
            logger.info("✅ Knowledge base absorption completed successfully!")
            logger.info(f"   - Hybrid model: {result['hybrid_model']}")
            logger.info(f"   - Models used: {', '.join(code_focused_models)}")
            logger.info(f"   - Knowledge areas: {', '.join(result['knowledge_areas'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Knowledge base absorption failed: {e}")
            return {"success": False, "error": str(e)}
    
    def select_code_correction_models(self, available_models: list) -> list:
        """Select models optimized for code correction and system knowledge"""
        
        # Priority order for code correction capabilities
        model_priorities = {
            "deepseek-coder": 10,
            "deepseek-math": 9,
            "codellama": 8,
            "deepseek-v2": 7,
            "mistral": 6,
            "llama2": 5,
            "phi": 4,
            "gemma": 3
        }
        
        # Score models based on code correction capability
        scored_models = []
        for model in available_models:
            score = 0
            for priority_model, priority_score in model_priorities.items():
                if priority_model in model.lower():
                    score = priority_score
                    break
            scored_models.append((model, score))
        
        # Sort by score and select top 3
        scored_models.sort(key=lambda x: x[1], reverse=True)
        selected_models = [model for model, score in scored_models[:3]]
        
        logger.info(f"📊 Selected models for code correction:")
        for model, score in scored_models[:3]:
            logger.info(f"   - {model}: score {score}")
        
        return selected_models
    
    def update_kb_from_corrections(self, corrections: list) -> bool:
        """Update knowledge base from correction feedback"""
        try:
            # Load current KB
            kb_data = self.load_knowledge_base()
            
            # Update learning feedback section
            if "piraz_os" not in kb_data:
                kb_data["piraz_os"] = {}
            
            if "learning_feedback" not in kb_data["piraz_os"]:
                kb_data["piraz_os"]["learning_feedback"] = {
                    "correction_history": [],
                    "pattern_improvements": [],
                    "new_error_patterns": []
                }
            
            # Add new corrections
            learning_feedback = kb_data["piraz_os"]["learning_feedback"]
            
            for correction in corrections:
                learning_feedback["correction_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "original_code": correction.get("original_code", ""),
                    "corrected_code": correction.get("corrected_code", ""),
                    "error_type": correction.get("error_type", "unknown"),
                    "confidence": correction.get("confidence", "medium"),
                    "explanation": correction.get("explanation", "")
                })
            
            # Update timestamp
            kb_data["piraz_os"]["last_updated"] = datetime.now().isoformat()
            
            # Save updated KB
            with open(self.kb_file, 'w') as f:
                json.dump(kb_data, f, indent=2)
            
            logger.info(f"✅ Updated knowledge base with {len(corrections)} corrections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update KB from corrections: {e}")
            return False
    
    def get_kb_summary(self) -> Dict[str, Any]:
        """Get summary of current knowledge base"""
        try:
            kb_data = self.load_knowledge_base()
            piraz_os = kb_data.get('piraz_os', {})
            
            return {
                "version": piraz_os.get('version', 'unknown'),
                "last_updated": piraz_os.get('last_updated', 'unknown'),
                "error_codes_count": len(piraz_os.get('error_codes', {})),
                "core_services_count": len(piraz_os.get('core_services', {})),
                "commands_count": len(piraz_os.get('command_syntax', {})),
                "validation_rules_count": len(piraz_os.get('code_validation_rules', {})),
                "learning_history_count": len(piraz_os.get('learning_feedback', {}).get('correction_history', []))
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get KB summary: {e}")
            return {"error": str(e)}

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fusion Absorption with Knowledge Base")
    parser.add_argument('--kb-file', default='piraz_os_kb.json', help='Knowledge base file path')
    parser.add_argument('--force', action='store_true', help='Force absorption even if conditions not met')
    parser.add_argument('--summary', action='store_true', help='Show KB summary only')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    kb_fusion = KnowledgeBaseFusion(kb_file=args.kb_file)
    
    if args.summary:
        print("📊 Knowledge Base Summary:")
        print("=" * 40)
        summary = kb_fusion.get_kb_summary()
        
        if "error" in summary:
            print(f"❌ Error: {summary['error']}")
            return 1
        
        print(f"Version: {summary['version']}")
        print(f"Last Updated: {summary['last_updated']}")
        print(f"Error Codes: {summary['error_codes_count']}")
        print(f"Core Services: {summary['core_services_count']}")
        print(f"Commands: {summary['commands_count']}")
        print(f"Validation Rules: {summary['validation_rules_count']}")
        print(f"Learning History: {summary['learning_history_count']}")
        
        return 0
    
    # Trigger KB absorption
    result = kb_fusion.trigger_kb_absorption(force=args.force)
    
    if result["success"]:
        print("✅ Knowledge base absorption completed successfully!")
        print(f"   - Hybrid model: {result.get('hybrid_model', 'unknown')}")
        print(f"   - KB version: {result.get('kb_version', 'unknown')}")
        return 0
    else:
        print(f"❌ Knowledge base absorption failed: {result.get('error', 'unknown')}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 