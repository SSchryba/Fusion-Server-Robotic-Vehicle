#!/usr/bin/env python3
"""
Fusion Controller
Orchestrates the complete fusion process including model evaluation, selection, and fusion
"""

import logging
import time
import schedule
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from threading import Thread
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader
from control.model_evaluator import ModelEvaluator

logger = logging.getLogger(__name__)

class FusionController:
    """Main controller for the fusion system"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        self.model_evaluator = ModelEvaluator()
        self.fusion_control = self.config.fusion_control
        
        self.last_cycle_time = None
        self.cycle_count = 0
        self.fusion_history = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def run_fusion_cycle(self) -> Dict:
        """Run a complete fusion cycle"""
        logger.info("🚀 Starting fusion cycle")
        cycle_start = datetime.now()
        
        try:
            # Step 1: Pull DeepSeek models
            logger.info("📥 Pulling DeepSeek models...")
            deepseek_success = self.api_client.pull_deepseek_models()
            if not deepseek_success:
                logger.warning("Failed to pull DeepSeek models, continuing with available models")
            
            # Small delay to allow models to be available
            time.sleep(10)
            
            # Step 2: Evaluate all models
            logger.info("🔍 Evaluating model capabilities...")
            evaluations = self.model_evaluator.evaluate_all_models()
            
            if not evaluations:
                logger.error("No models available for evaluation")
                return {"success": False, "error": "No models available"}
            
            # Step 3: Select top performers
            models_per_fusion = self.fusion_control.get('models_per_fusion', 3)
            logger.info(f"🎯 Selecting top {models_per_fusion} models...")
            
            top_models = self.model_evaluator.select_top_models(evaluations, models_per_fusion)
            
            if len(top_models) < 2:
                logger.error("Not enough suitable models for fusion")
                return {"success": False, "error": "Insufficient suitable models"}
            
            # Step 4: Create hybrid model
            logger.info("🧬 Creating hybrid model...")
            model_names = [model.model_name for model in top_models]
            
            hybrid_result = self.api_client.create_hybrid(model_names)
            if not hybrid_result:
                logger.error("Failed to create hybrid model")
                return {"success": False, "error": "Hybrid creation failed"}
            
            # Step 5: Start absorption cycle
            logger.info("🔄 Starting absorption cycle...")
            absorption_success = self.api_client.start_absorption()
            if not absorption_success:
                logger.warning("Failed to start absorption cycle")
            
            # Record cycle results
            cycle_result = {
                "success": True,
                "timestamp": cycle_start.isoformat(),
                "duration_seconds": (datetime.now() - cycle_start).total_seconds(),
                "models_evaluated": len(evaluations),
                "models_selected": len(top_models),
                "selected_models": model_names,
                "hybrid_created": hybrid_result.get('hybrid_name', 'unknown'),
                "deepseek_pull_success": deepseek_success,
                "absorption_started": absorption_success
            }
            
            self.fusion_history.append(cycle_result)
            self.cycle_count += 1
            self.last_cycle_time = cycle_start
            
            logger.info(f"✅ Fusion cycle completed successfully in {cycle_result['duration_seconds']:.1f}s")
            logger.info(f"   - Hybrid created: {hybrid_result.get('hybrid_name', 'unknown')}")
            logger.info(f"   - Models used: {', '.join(model_names)}")
            
            return cycle_result
            
        except Exception as e:
            logger.error(f"❌ Fusion cycle failed: {e}")
            return {"success": False, "error": str(e), "timestamp": cycle_start.isoformat()}
    
    def run_evaluation_only(self) -> Dict:
        """Run model evaluation without fusion (for testing)"""
        logger.info("🔍 Running model evaluation only...")
        
        try:
            evaluations = self.model_evaluator.evaluate_all_models()
            
            if not evaluations:
                return {"success": False, "error": "No models available"}
            
            # Generate evaluation report
            report = self.model_evaluator.generate_evaluation_report(evaluations)
            
            # Select top models
            top_models = self.model_evaluator.select_top_models(evaluations, 3)
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "models_evaluated": len(evaluations),
                "top_models": [
                    {
                        "name": model.model_name,
                        "score": model.overall_score,
                        "recommendation": model.recommendation,
                        "capabilities": model.capability_scores
                    } for model in top_models
                ],
                "evaluation_report": report
            }
            
            logger.info(f"✅ Evaluation completed - {len(evaluations)} models evaluated")
            return result
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_periodic_fusion(self):
        """Schedule periodic fusion cycles"""
        interval_hours = self.fusion_control.get('cycle_interval_hours', 56)
        
        logger.info(f"📅 Scheduling fusion cycles every {interval_hours} hours")
        
        # Schedule the job
        schedule.every(interval_hours).hours.do(self.run_fusion_cycle)
        
        # Run immediately for first cycle
        logger.info("🚀 Running initial fusion cycle...")
        self.run_fusion_cycle()
        
        # Start scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_continuous_fusion(self):
        """Start continuous fusion in background thread"""
        logger.info("🔄 Starting continuous fusion controller...")
        
        def fusion_thread():
            try:
                self.schedule_periodic_fusion()
            except Exception as e:
                logger.error(f"Continuous fusion thread failed: {e}")
        
        # Start in background thread
        thread = Thread(target=fusion_thread, daemon=True)
        thread.start()
        
        logger.info("✅ Continuous fusion controller started")
        return thread
    
    def get_controller_status(self) -> Dict:
        """Get current controller status"""
        return {
            "controller_active": True,
            "cycle_count": self.cycle_count,
            "last_cycle_time": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "next_cycle_in_hours": self.fusion_control.get('cycle_interval_hours', 56),
            "fusion_history_count": len(self.fusion_history),
            "recent_cycles": self.fusion_history[-5:] if self.fusion_history else []
        }
    
    def get_fusion_history(self, limit: int = 10) -> List[Dict]:
        """Get fusion history"""
        return self.fusion_history[-limit:] if self.fusion_history else []
    
    def force_fusion_cycle(self) -> Dict:
        """Force a fusion cycle to run immediately"""
        logger.info("🔥 Force-running fusion cycle...")
        return self.run_fusion_cycle()
    
    def backup_fusion_data(self) -> bool:
        """Backup fusion history and configurations"""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "cycle_count": self.cycle_count,
                "fusion_history": self.fusion_history,
                "controller_status": self.get_controller_status(),
                "configuration": self.config_loader._config
            }
            
            backup_file = f"fusion_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"✅ Backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def validate_system_health(self) -> Dict:
        """Validate system health before fusion"""
        health_check = {
            "server_online": False,
            "models_available": False,
            "fusion_enabled": False,
            "constraints_valid": False,
            "issues": []
        }
        
        try:
            # Check server health
            server_health = self.api_client.get_server_health()
            health_check["server_online"] = server_health.get('status') == 'ok'
            
            if not health_check["server_online"]:
                health_check["issues"].append("Server is not responding")
            
            # Check available models
            models = self.api_client.get_available_models()
            health_check["models_available"] = len(models) >= 2
            
            if not health_check["models_available"]:
                health_check["issues"].append(f"Insufficient models available: {len(models)}")
            
            # Check fusion system status
            fusion_status = self.api_client.get_fusion_status()
            health_check["fusion_enabled"] = fusion_status.fusion_enabled if fusion_status else False
            
            if not health_check["fusion_enabled"]:
                health_check["issues"].append("Fusion system is disabled")
            
            # Validate constraints
            constraints = self.config.model_constraints
            health_check["constraints_valid"] = all([
                0 < constraints.min_capability_threshold <= 10,
                0 < constraints.max_hallucination_rate <= 1,
                constraints.max_parameter_size in ['1B', '2B', '7B', '13B', '33B', '70B']
            ])
            
            if not health_check["constraints_valid"]:
                health_check["issues"].append("Invalid model constraints configuration")
            
        except Exception as e:
            health_check["issues"].append(f"Health check failed: {e}")
        
        health_check["overall_healthy"] = len(health_check["issues"]) == 0
        
        return health_check

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fusion Controller")
    parser.add_argument('--mode', choices=['cycle', 'continuous', 'evaluate', 'status'], 
                       default='cycle', help='Operation mode')
    parser.add_argument('--force', action='store_true', help='Force immediate fusion cycle')
    
    args = parser.parse_args()
    
    controller = FusionController()
    
    if args.mode == 'cycle' or args.force:
        result = controller.run_fusion_cycle()
        print(json.dumps(result, indent=2))
        
    elif args.mode == 'continuous':
        controller.start_continuous_fusion()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("👋 Stopping continuous fusion controller...")
            
    elif args.mode == 'evaluate':
        result = controller.run_evaluation_only()
        print(json.dumps(result, indent=2))
        
    elif args.mode == 'status':
        status = controller.get_controller_status()
        health = controller.validate_system_health()
        
        print("FUSION CONTROLLER STATUS")
        print("=" * 40)
        print(json.dumps(status, indent=2))
        print("\nSYSTEM HEALTH")
        print("=" * 40)
        print(json.dumps(health, indent=2))

if __name__ == "__main__":
    main() 