#!/usr/bin/env python3
"""
Fusion Controller Runner
Launch the fusion controller with various modes
"""

import sys
import os
import argparse
import logging
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from control.fusion_controller import FusionController

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fusion Controller")
    parser.add_argument('--mode', choices=['cycle', 'continuous', 'evaluate', 'status', 'force'],
                       default='cycle', help='Controller mode')
    parser.add_argument('--interval', type=int, default=56,
                       help='Cycle interval in hours for continuous mode')
    parser.add_argument('--models', type=int, default=3,
                       help='Number of models per fusion')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup before running')
    parser.add_argument('--health-check', action='store_true',
                       help='Run health check before starting')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("🔬 Fusion Controller")
    print("=" * 40)
    
    controller = FusionController()
    
    # Run health check if requested
    if args.health_check:
        print("🏥 Running system health check...")
        health = controller.validate_system_health()
        
        if not health['overall_healthy']:
            print("❌ System health check failed:")
            for issue in health['issues']:
                print(f"  - {issue}")
            
            if input("\nContinue anyway? (y/N): ").lower() != 'y':
                sys.exit(1)
        else:
            print("✅ System health check passed")
    
    # Create backup if requested
    if args.backup:
        print("💾 Creating backup...")
        if controller.backup_fusion_data():
            print("✅ Backup created successfully")
        else:
            print("❌ Backup failed")
    
    # Run based on mode
    if args.mode == 'cycle':
        print("🔄 Running single fusion cycle...")
        result = controller.run_fusion_cycle()
        
        if result['success']:
            print("✅ Fusion cycle completed successfully")
            print(f"   - Duration: {result['duration_seconds']:.1f}s")
            print(f"   - Models evaluated: {result['models_evaluated']}")
            print(f"   - Models selected: {result['models_selected']}")
            print(f"   - Hybrid created: {result['hybrid_created']}")
        else:
            print("❌ Fusion cycle failed")
            print(f"   - Error: {result['error']}")
            sys.exit(1)
    
    elif args.mode == 'force':
        print("🔥 Force-running fusion cycle...")
        result = controller.force_fusion_cycle()
        
        if result['success']:
            print("✅ Force fusion completed successfully")
        else:
            print("❌ Force fusion failed")
            print(f"   - Error: {result['error']}")
            sys.exit(1)
    
    elif args.mode == 'continuous':
        print(f"🔄 Starting continuous fusion (every {args.interval}h)...")
        
        # Update configuration
        controller.fusion_control['cycle_interval_hours'] = args.interval
        controller.fusion_control['models_per_fusion'] = args.models
        
        try:
            controller.start_continuous_fusion()
            
            print("✅ Continuous fusion started")
            print("Press Ctrl+C to stop...")
            
            # Keep main thread alive
            while True:
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping continuous fusion...")
            logger.info("Continuous fusion stopped by user")
    
    elif args.mode == 'evaluate':
        print("🔍 Running model evaluation...")
        result = controller.run_evaluation_only()
        
        if result['success']:
            print("✅ Model evaluation completed")
            print(f"   - Models evaluated: {result['models_evaluated']}")
            print(f"   - Top models: {[m['name'] for m in result['top_models']]}")
            
            # Show detailed report
            if input("\nShow detailed report? (y/N): ").lower() == 'y':
                print("\n" + "=" * 60)
                print(result['evaluation_report'])
        else:
            print("❌ Model evaluation failed")
            print(f"   - Error: {result['error']}")
            sys.exit(1)
    
    elif args.mode == 'status':
        print("📊 Getting controller status...")
        
        status = controller.get_controller_status()
        health = controller.validate_system_health()
        
        print("\nCONTROLLER STATUS:")
        print(f"  Active: {status['controller_active']}")
        print(f"  Cycle count: {status['cycle_count']}")
        print(f"  Last cycle: {status['last_cycle_time'] or 'Never'}")
        print(f"  Next cycle: {status['next_cycle_in_hours']}h")
        print(f"  History count: {status['fusion_history_count']}")
        
        print("\nSYSTEM HEALTH:")
        print(f"  Overall: {'✅ Healthy' if health['overall_healthy'] else '❌ Issues'}")
        print(f"  Server online: {'✅' if health['server_online'] else '❌'}")
        print(f"  Models available: {'✅' if health['models_available'] else '❌'}")
        print(f"  Fusion enabled: {'✅' if health['fusion_enabled'] else '❌'}")
        print(f"  Constraints valid: {'✅' if health['constraints_valid'] else '❌'}")
        
        if health['issues']:
            print("\nISSUES:")
            for issue in health['issues']:
                print(f"  - {issue}")
        
        # Show recent cycles
        if status['recent_cycles']:
            print("\nRECENT CYCLES:")
            for cycle in status['recent_cycles'][-3:]:
                success = "✅" if cycle['success'] else "❌"
                print(f"  {success} {cycle['timestamp'][:19]} - {cycle.get('hybrid_created', 'Failed')}")

if __name__ == "__main__":
    main() 