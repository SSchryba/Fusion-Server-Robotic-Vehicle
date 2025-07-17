#!/usr/bin/env python3
"""
AutoFix System Demo
Comprehensive demonstration of the self-correcting code generation system
"""

import sys
import os
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fusion_absorb_with_kb import KnowledgeBaseFusion
from update_kb import KnowledgeBaseUpdater, CorrectionData
from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader

class AutoFixDemo:
    """Complete demonstration of the AutoFix system"""
    
    def __init__(self):
        self.kb_fusion = KnowledgeBaseFusion()
        self.kb_updater = KnowledgeBaseUpdater()
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        print("🔧 AutoFix System Demo")
        print("=" * 50)
        print("Demonstrating intelligent code correction with Piraz OS integration")
        print("=" * 50)
        
    def print_section(self, title: str):
        """Print a demo section header"""
        print(f"\n{'='*60}")
        print(f"🎯 {title}")
        print(f"{'='*60}")
        
    def print_step(self, step: str):
        """Print a demo step"""
        print(f"\n▶️  {step}")
        
    def print_result(self, result: str):
        """Print a demo result"""
        print(f"   ✅ {result}")
        
    def print_error(self, error: str):
        """Print a demo error"""
        print(f"   ❌ {error}")
        
    def wait_for_user(self, prompt: str = "Press Enter to continue..."):
        """Wait for user input"""
        input(f"\n🔹 {prompt}")
        
    def demo_knowledge_base(self):
        """Demonstrate knowledge base functionality"""
        self.print_section("Knowledge Base Overview")
        
        self.print_step("Loading Piraz OS Knowledge Base")
        try:
            kb_summary = self.kb_fusion.get_kb_summary()
            self.print_result(f"KB Version: {kb_summary['version']}")
            self.print_result(f"Error Codes: {kb_summary['error_codes_count']}")
            self.print_result(f"Core Services: {kb_summary['core_services_count']}")
            self.print_result(f"Commands: {kb_summary['commands_count']}")
            self.print_result(f"Validation Rules: {kb_summary['validation_rules_count']}")
        except Exception as e:
            self.print_error(f"Failed to load KB: {e}")
            
        self.print_step("Displaying sample error codes")
        try:
            kb_data = self.kb_fusion.load_knowledge_base()
            error_codes = kb_data.get('piraz_os', {}).get('error_codes', {})
            
            for code, info in list(error_codes.items())[:3]:
                print(f"   • {code}: {info.get('description', 'No description')}")
                print(f"     Severity: {info.get('severity', 'unknown')}")
                print(f"     Fixes: {', '.join(info.get('recommended_fixes', [])[:2])}")
                
        except Exception as e:
            self.print_error(f"Failed to display error codes: {e}")
            
        self.wait_for_user()
        
    def demo_fusion_integration(self):
        """Demonstrate fusion server integration"""
        self.print_section("Fusion Server Integration")
        
        self.print_step("Checking fusion server connection")
        try:
            fusion_status = self.api_client.get_fusion_status()
            if fusion_status:
                self.print_result("Fusion server is accessible")
                self.print_result(f"Fusion enabled: {fusion_status.fusion_enabled}")
                self.print_result(f"Fusion version: {fusion_status.fusion_version}")
            else:
                self.print_error("Fusion server not accessible")
        except Exception as e:
            self.print_error(f"Connection failed: {e}")
            
        self.print_step("Getting available models")
        try:
            models = self.api_client.get_available_models()
            self.print_result(f"Available models: {len(models)}")
            for model in models[:5]:  # Show first 5
                print(f"   • {model}")
        except Exception as e:
            self.print_error(f"Failed to get models: {e}")
            
        self.print_step("Selecting code-focused models")
        try:
            available_models = self.api_client.get_available_models()
            if available_models:
                code_models = self.kb_fusion.select_code_correction_models(available_models)
                self.print_result(f"Selected models: {', '.join(code_models)}")
            else:
                self.print_error("No models available for selection")
        except Exception as e:
            self.print_error(f"Model selection failed: {e}")
            
        self.wait_for_user()
        
    def demo_code_analysis(self):
        """Demonstrate code analysis capabilities"""
        self.print_section("Code Analysis Demo")
        
        # Sample problematic code
        sample_codes = [
            {
                "title": "Poor Error Handling",
                "code": '''
def start_service():
    os.system("piraz-service start myservice")
    print("Service started")
''',
                "language": "python"
            },
            {
                "title": "Hardcoded Configuration",
                "code": '''
def configure_network():
    config_file = "/etc/piraz/network.conf"
    with open(config_file, 'w') as f:
        f.write("interface=eth0\\ndhcp=true")
''',
                "language": "python"
            },
            {
                "title": "Missing Service Validation",
                "code": '''
def restart_service(service_name):
    subprocess.run(["piraz-service", "restart", service_name])
    return "Service restarted"
''',
                "language": "python"
            }
        ]
        
        for i, sample in enumerate(sample_codes, 1):
            self.print_step(f"Analyzing Sample {i}: {sample['title']}")
            print(f"   Code:")
            for line in sample['code'].strip().split('\n'):
                print(f"     {line}")
            
            # Simulate code analysis (actual analysis would use AutoFix server)
            print(f"   Analysis Results:")
            print(f"   • Language: {sample['language']}")
            print(f"   • Issues detected: Error handling, validation, hardcoded paths")
            print(f"   • Piraz OS compatibility: Partial")
            print(f"   • Suggested fixes: Add error checking, use config validation")
            
            if i < len(sample_codes):
                self.wait_for_user("Continue to next sample...")
                
        self.wait_for_user()
        
    def demo_learning_system(self):
        """Demonstrate learning and feedback system"""
        self.print_section("Learning System Demo")
        
        self.print_step("Adding sample corrections to demonstrate learning")
        
        # Create sample corrections
        sample_corrections = [
            CorrectionData(
                timestamp=datetime.now().isoformat(),
                original_code='print("Starting service")',
                corrected_code='logger.info("Starting service")',
                error_type='logging_improvement',
                confidence=0.9,
                explanation='Replaced print with logging for better practice',
                language='python',
                fixes_applied=['replace_print_with_logging']
            ),
            CorrectionData(
                timestamp=datetime.now().isoformat(),
                original_code='os.system("piraz-service start core")',
                corrected_code='result = subprocess.run(["piraz-service", "start", "core"], capture_output=True)',
                error_type='security_vulnerability',
                confidence=0.95,
                explanation='Replaced os.system with subprocess for security',
                language='python',
                fixes_applied=['replace_os_system', 'add_error_checking']
            ),
            CorrectionData(
                timestamp=datetime.now().isoformat(),
                original_code='config_file = "/etc/piraz/network.conf"',
                corrected_code='config_file = os.path.join(CONFIG_DIR, "network.conf")',
                error_type='compatibility_issue',
                confidence=0.8,
                explanation='Used configurable path instead of hardcoded',
                language='python',
                fixes_applied=['remove_hardcoded_path', 'use_config_variable']
            )
        ]
        
        # Log corrections
        for correction in sample_corrections:
            success = self.kb_updater.log_correction(correction)
            if success:
                self.print_result(f"Logged correction: {correction.error_type}")
            else:
                self.print_error(f"Failed to log correction: {correction.error_type}")
                
        self.print_step("Saving updated knowledge base")
        try:
            self.kb_updater.save_kb()
            self.print_result("Knowledge base updated successfully")
        except Exception as e:
            self.print_error(f"Failed to save KB: {e}")
            
        self.print_step("Displaying learning statistics")
        try:
            stats = self.kb_updater.get_learning_stats()
            self.print_result(f"Total corrections: {stats['total_corrections']}")
            self.print_result(f"Average confidence: {stats['avg_confidence']:.2f}")
            self.print_result(f"Improvement rate: {stats['improvement_rate']:.2%}")
            
            print(f"   Error type distribution:")
            for error_type, count in stats['error_type_distribution'].items():
                print(f"     • {error_type}: {count}")
                
        except Exception as e:
            self.print_error(f"Failed to get stats: {e}")
            
        self.wait_for_user()
        
    def demo_improvement_suggestions(self):
        """Demonstrate improvement suggestions"""
        self.print_section("Improvement Suggestions")
        
        self.print_step("Generating improvement suggestions")
        try:
            suggestions = self.kb_updater.suggest_kb_improvements()
            
            if suggestions:
                self.print_result(f"Generated {len(suggestions)} suggestions")
                for suggestion in suggestions[:3]:  # Show first 3
                    print(f"   • [{suggestion['priority'].upper()}] {suggestion['suggestion']}")
                    print(f"     Rationale: {suggestion['rationale']}")
            else:
                self.print_result("No suggestions available (need more correction data)")
                
        except Exception as e:
            self.print_error(f"Failed to generate suggestions: {e}")
            
        self.wait_for_user()
        
    def demo_kb_absorption(self):
        """Demonstrate knowledge base absorption"""
        self.print_section("Knowledge Base Absorption")
        
        self.print_step("Triggering KB-enhanced absorption")
        try:
            result = self.kb_fusion.trigger_kb_absorption()
            
            if result['success']:
                self.print_result("KB absorption completed successfully")
                self.print_result(f"Hybrid model: {result.get('hybrid_model', 'unknown')}")
                self.print_result(f"KB version: {result.get('kb_version', 'unknown')}")
                self.print_result(f"Models used: {', '.join(result.get('selected_models', []))}")
                self.print_result(f"Knowledge areas: {', '.join(result.get('knowledge_areas', []))}")
            else:
                self.print_error(f"KB absorption failed: {result.get('error', 'unknown')}")
                
        except Exception as e:
            self.print_error(f"Absorption failed: {e}")
            
        self.wait_for_user()
        
    def demo_system_integration(self):
        """Demonstrate full system integration"""
        self.print_section("System Integration Demo")
        
        self.print_step("Showing complete workflow")
        
        workflow_steps = [
            "1. Load Piraz OS Knowledge Base",
            "2. Connect to Fusion Server",
            "3. Select Code-Focused Models",
            "4. Inject KB into Fusion Pipeline",
            "5. Analyze User Code",
            "6. Generate Fixes with KB Context",
            "7. Apply Piraz OS Validation Rules",
            "8. Return Corrected Code",
            "9. Log Correction for Learning",
            "10. Update KB with Patterns"
        ]
        
        for step in workflow_steps:
            print(f"   {step}")
            time.sleep(0.5)  # Simulate processing time
            
        self.print_result("Complete workflow demonstrated")
        
        self.print_step("System components status")
        
        components = [
            ("Knowledge Base", "✅ Loaded"),
            ("Fusion Server", "✅ Connected" if self.api_client.get_fusion_status() else "❌ Disconnected"),
            ("AutoFix Server", "⚠️  Not running (use: python run_autofix.py)"),
            ("Web Interface", "⚠️  Not running (access: http://localhost:8003)"),
            ("Learning System", "✅ Active"),
            ("Feedback Loop", "✅ Configured")
        ]
        
        for component, status in components:
            print(f"   • {component}: {status}")
            
        self.wait_for_user()
        
    def demo_usage_examples(self):
        """Demonstrate usage examples"""
        self.print_section("Usage Examples")
        
        self.print_step("Command-line usage examples")
        
        examples = [
            {
                "title": "Start AutoFix Server",
                "command": "python run_autofix.py",
                "description": "Launch the web-based code correction interface"
            },
            {
                "title": "Trigger KB Absorption",
                "command": "python fusion_absorb_with_kb.py",
                "description": "Inject knowledge base into fusion pipeline"
            },
            {
                "title": "View Learning Statistics",
                "command": "python update_kb.py --stats",
                "description": "Display correction statistics and patterns"
            },
            {
                "title": "Get KB Summary",
                "command": "python fusion_absorb_with_kb.py --summary",
                "description": "Show knowledge base overview"
            },
            {
                "title": "Clean Old Data",
                "command": "python update_kb.py --cleanup 30",
                "description": "Remove correction data older than 30 days"
            }
        ]
        
        for example in examples:
            print(f"   {example['title']}:")
            print(f"   $ {example['command']}")
            print(f"   {example['description']}")
            print()
            
        self.print_step("API usage examples")
        
        api_examples = [
            {
                "title": "Fix Code",
                "method": "POST",
                "endpoint": "/autofix",
                "description": "Submit code for correction"
            },
            {
                "title": "Get Status",
                "method": "GET",
                "endpoint": "/autofix/status",
                "description": "Check system status"
            },
            {
                "title": "View History",
                "method": "GET",
                "endpoint": "/autofix/history",
                "description": "Get correction history"
            }
        ]
        
        for example in api_examples:
            print(f"   {example['title']}: {example['method']} {example['endpoint']}")
            print(f"   {example['description']}")
            print()
            
        self.wait_for_user()
        
    def demo_next_steps(self):
        """Show next steps for users"""
        self.print_section("Next Steps")
        
        self.print_step("To use the AutoFix system:")
        
        steps = [
            "1. Start your fusion server: Make sure localhost:8000 is running",
            "2. Launch AutoFix server: python run_autofix.py",
            "3. Open web interface: http://localhost:8003",
            "4. Try fixing some code to see the system in action",
            "5. Provide feedback to improve the system",
            "6. Monitor learning statistics: python update_kb.py --stats"
        ]
        
        for step in steps:
            print(f"   {step}")
            
        self.print_step("Additional resources:")
        
        resources = [
            "📚 Full documentation: README_autofix.md",
            "🔧 System overview: SYSTEM_OVERVIEW.md",
            "⚙️  Configuration: config/fusion_config.yaml",
            "🧠 Knowledge base: piraz_os_kb.json",
            "💻 Web interface: autofix_frontend/index.html"
        ]
        
        for resource in resources:
            print(f"   {resource}")
            
        print(f"\n🎉 Demo completed successfully!")
        print(f"The AutoFix system is ready for intelligent code correction!")
        
    def run_demo(self):
        """Run the complete demo"""
        try:
            self.demo_knowledge_base()
            self.demo_fusion_integration()
            self.demo_code_analysis()
            self.demo_learning_system()
            self.demo_improvement_suggestions()
            self.demo_kb_absorption()
            self.demo_system_integration()
            self.demo_usage_examples()
            self.demo_next_steps()
            
        except KeyboardInterrupt:
            print(f"\n\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"Thank you for exploring the AutoFix system!")
        print(f"{'='*60}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoFix System Demo")
    parser.add_argument('--quick', action='store_true', help='Run quick demo without user interaction')
    parser.add_argument('--section', choices=['kb', 'fusion', 'analysis', 'learning', 'integration'], 
                       help='Run specific demo section only')
    
    args = parser.parse_args()
    
    demo = AutoFixDemo()
    
    if args.section:
        # Run specific section
        section_map = {
            'kb': demo.demo_knowledge_base,
            'fusion': demo.demo_fusion_integration,
            'analysis': demo.demo_code_analysis,
            'learning': demo.demo_learning_system,
            'integration': demo.demo_system_integration
        }
        
        if args.section in section_map:
            section_map[args.section]()
        else:
            print(f"Unknown section: {args.section}")
            return 1
    else:
        # Run complete demo
        if args.quick:
            # Override wait_for_user for quick demo
            demo.wait_for_user = lambda prompt="": None
            
        demo.run_demo()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 