#!/usr/bin/env python3
"""
BUD-EE Main Controller
Integrates all subsystems for complete autonomous AI vehicle operation
"""

import asyncio
import signal
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional

# Import all BUD-EE modules
from vision_motor_fusion import VisionMotorFusion
from calibration_routine import BudeeCalibrationSystem
from interaction_ritual import InteractionRitual
from mimic_engine import MimicEngine
from audio_control import AudioControl
from budee_websocket_client import BudeeWebSocketClient
from emotion_engine import EmotionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BudeeSystem:
    """Main BUD-EE system coordinator"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # System state
        self.running = False
        self.startup_complete = False
        self.emergency_stopped = False
        
        # Initialize subsystems
        self.audio_controller = None
        self.emotion_engine = None
        self.interaction_ritual = None
        self.mimic_engine = None
        self.vision_motor = None
        self.websocket_client = None
        
        # System threads
        self.vision_thread = None
        self.mimic_thread = None
        self.websocket_thread = None
        
        logger.info("BUD-EE System initializing...")
    
    async def initialize_systems(self):
        """Initialize all BUD-EE subsystems"""
        try:
            logger.info("🤖 Initializing BUD-EE subsystems...")
            
            # 1. Audio Control (foundational)
            logger.info("Initializing Audio Control...")
            self.audio_controller = AudioControl()
            
            # 2. Emotion Engine (core personality)
            logger.info("Initializing Emotion Engine...")
            self.emotion_engine = EmotionEngine()
            
            # 3. Interaction Ritual (behavior patterns)
            logger.info("Initializing Interaction Ritual...")
            self.interaction_ritual = InteractionRitual(
                audio_controller=self.audio_controller
            )
            
            # 4. Mimic Engine (gesture response)
            logger.info("Initializing Mimic Engine...")
            self.mimic_engine = MimicEngine(
                interaction_controller=self.interaction_ritual
            )
            
            # 5. Vision Motor Fusion (core navigation)
            logger.info("Initializing Vision Motor Fusion...")
            self.vision_motor = VisionMotorFusion()
            
            # 6. WebSocket Client (server communication)
            server_url = self.config.get('server_url', 'ws://localhost:8000/ws/vehicle')
            logger.info(f"Initializing WebSocket Client for {server_url}...")
            self.websocket_client = BudeeWebSocketClient(server_url)
            
            # Cross-link all systems
            self._link_systems()
            
            # Start emotion engine updates
            self.emotion_engine.start_emotion_updates()
            
            logger.info("✅ All BUD-EE subsystems initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def _link_systems(self):
        """Cross-link all subsystems for integrated operation"""
        logger.info("🔗 Linking subsystems...")
        
        # Set up cross-references
        self.emotion_engine.set_controllers(
            audio=self.audio_controller,
            interaction=self.interaction_ritual,
            mimic=self.mimic_engine,
            websocket=self.websocket_client
        )
        
        self.interaction_ritual.set_controllers(
            audio_controller=self.audio_controller,
            motor_controller=self.vision_motor
        )
        
        self.mimic_engine.set_controllers(
            motor_controller=self.vision_motor,
            interaction_controller=self.interaction_ritual
        )
        
        self.websocket_client.set_controllers(
            audio=self.audio_controller,
            motor=self.vision_motor,
            emotion=self.emotion_engine,
            interaction=self.interaction_ritual
        )
        
        # Set up event handlers
        self._setup_event_handlers()
        
        logger.info("✅ System linking complete")
    
    def _setup_event_handlers(self):
        """Set up inter-system event handlers"""
        
        # Vision system → Emotion system
        def on_human_detected(detection):
            if hasattr(detection, 'confidence'):
                self.emotion_engine.on_human_detected(detection.confidence)
        
        # Mimic system → Emotion system  
        def on_gesture_detected(gesture_type):
            self.emotion_engine.on_gesture_detected(gesture_type.value)
        
        # Interaction system → Emotion system
        def on_interaction_event(event_type, success=True):
            if event_type == "positive_response" and success:
                self.emotion_engine.on_positive_feedback()
            elif event_type == "no_response":
                self.emotion_engine.on_no_response()
        
        logger.info("Event handlers configured")
    
    async def start_system(self):
        """Start the complete BUD-EE system"""
        try:
            self.running = True
            logger.info("🚀 Starting BUD-EE System...")
            
            # Welcome message
            if self.audio_controller:
                self.audio_controller.play_emotion_sound("greeting")
            
            # Start vision motor fusion in thread
            self.vision_thread = threading.Thread(
                target=self._run_vision_system,
                daemon=True
            )
            self.vision_thread.start()
            
            # Start mimic engine in thread
            self.mimic_thread = threading.Thread(
                target=self._run_mimic_system,
                daemon=True
            )
            self.mimic_thread.start()
            
            # Start WebSocket client
            self.websocket_thread = threading.Thread(
                target=self._run_websocket_system,
                daemon=True
            )
            self.websocket_thread.start()
            
            # Set initial emotion
            self.emotion_engine.set_emotion("curious", 0.7)
            
            self.startup_complete = True
            logger.info("🎯 BUD-EE System fully operational!")
            
            # Play startup sound
            if self.audio_controller:
                self.audio_controller.play_emotion_sound("success")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            await self.shutdown()
            return False
    
    def _run_vision_system(self):
        """Run vision motor fusion system in thread"""
        try:
            if self.vision_motor:
                self.vision_motor.run_vision_loop(display=False)
        except Exception as e:
            logger.error(f"Vision system error: {e}")
    
    def _run_mimic_system(self):
        """Run mimic engine in thread"""
        try:
            if self.mimic_engine:
                self.mimic_engine.run_mimic_loop(display=False)
        except Exception as e:
            logger.error(f"Mimic system error: {e}")
    
    def _run_websocket_system(self):
        """Run WebSocket client in thread"""
        try:
            if self.websocket_client:
                asyncio.run(self.websocket_client.run_client())
        except Exception as e:
            logger.error(f"WebSocket system error: {e}")
    
    async def run_main_loop(self):
        """Main system loop"""
        logger.info("🔄 Starting main system loop...")
        
        loop_count = 0
        status_interval = 60  # Status update every minute
        
        try:
            while self.running and not self.emergency_stopped:
                loop_count += 1
                
                # Periodic status updates
                if loop_count % status_interval == 0:
                    await self._system_status_update()
                
                # Check system health
                if loop_count % 10 == 0:
                    self._check_system_health()
                
                # Small delay
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            logger.info("Main loop interrupted by user")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            await self.shutdown()
    
    async def _system_status_update(self):
        """Periodic system status update"""
        try:
            stats = self.get_system_stats()
            logger.info(f"System Status: Uptime={stats['uptime']:.1f}s, "
                       f"Emotion={stats['emotion']['emotion']}, "
                       f"Interactions={stats['interactions']}")
            
            # Send status to server
            if self.websocket_client and self.websocket_client.connected:
                await self.websocket_client.send_status_update()
                
        except Exception as e:
            logger.error(f"Status update error: {e}")
    
    def _check_system_health(self):
        """Check health of all subsystems"""
        issues = []
        
        if not self.vision_thread or not self.vision_thread.is_alive():
            issues.append("Vision system not running")
        
        if not self.mimic_thread or not self.mimic_thread.is_alive():
            issues.append("Mimic system not running")
        
        if not self.emotion_engine or not self.emotion_engine.running:
            issues.append("Emotion engine not running")
        
        if issues:
            logger.warning(f"System health issues: {', '.join(issues)}")
            if self.emotion_engine:
                self.emotion_engine.on_system_error("health_check", "medium")
    
    def emergency_stop(self):
        """Emergency stop all systems"""
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")
        
        self.emergency_stopped = True
        self.running = False
        
        # Stop all movement
        if self.vision_motor:
            self.vision_motor.stop()
        
        # Stop all audio
        if self.audio_controller:
            self.audio_controller.stop_all_audio()
        
        # Stop interaction rituals
        if self.interaction_ritual:
            self.interaction_ritual.emergency_stop()
        
        # Play emergency sound
        if self.audio_controller:
            self.audio_controller.play_emotion_sound("alert")
        
        logger.warning("Emergency stop completed")
    
    async def shutdown(self):
        """Graceful system shutdown"""
        logger.info("🛑 Shutting down BUD-EE System...")
        
        self.running = False
        
        # Play goodbye sound
        if self.audio_controller and not self.emergency_stopped:
            self.audio_controller.play_emotion_sound("departure")
            time.sleep(2)  # Allow sound to play
        
        # Stop all subsystems
        if self.emotion_engine:
            self.emotion_engine.cleanup()
        
        if self.vision_motor:
            self.vision_motor.stop()
        
        if self.mimic_engine:
            self.mimic_engine.stop()
        
        if self.interaction_ritual:
            self.interaction_ritual.cleanup()
        
        if self.websocket_client:
            self.websocket_client.stop()
        
        if self.audio_controller:
            self.audio_controller.cleanup()
        
        # Wait for threads to finish
        threads = [self.vision_thread, self.mimic_thread, self.websocket_thread]
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=3.0)
        
        logger.info("✅ BUD-EE System shutdown complete")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            "startup_complete": self.startup_complete,
            "running": self.running,
            "emergency_stopped": self.emergency_stopped,
            "uptime": time.time() - getattr(self, 'start_time', time.time())
        }
        
        # Add subsystem stats
        if self.emotion_engine:
            stats["emotion"] = self.emotion_engine.get_current_emotion()
        
        if self.interaction_ritual:
            stats["interactions"] = self.interaction_ritual.get_interaction_stats()["total_interactions"]
        
        if self.mimic_engine:
            stats["gestures"] = self.mimic_engine.get_gesture_stats()["total_gestures"]
        
        if self.audio_controller:
            stats["audio"] = self.audio_controller.get_audio_stats()
        
        if self.websocket_client:
            stats["websocket"] = self.websocket_client.get_connection_stats()
        
        return stats

async def main():
    """Main entry point"""
    print("🤖 BUD-EE - Autonomous Emotional AI Vehicle")
    print("=" * 60)
    print("Initializing systems...")
    
    # Configuration
    config = {
        "server_url": "ws://localhost:8000/ws/vehicle",
        "debug_mode": False,
        "calibration_required": False
    }
    
    # Check for calibration
    calibration_file = Path("budee_calibration_map.json")
    if not calibration_file.exists():
        print("⚠️  No calibration found!")
        response = input("Run calibration routine? (Y/n): ").lower()
        
        if response != 'n':
            print("🔧 Running calibration routine...")
            try:
                calibrator = BudeeCalibrationSystem()
                calibrator.run_full_calibration()
                print("✅ Calibration completed")
            except Exception as e:
                print(f"❌ Calibration failed: {e}")
                return
    
    # Create and initialize system
    budee = BudeeSystem(config)
    budee.start_time = time.time()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print("\n🛑 Shutdown signal received...")
        asyncio.create_task(budee.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize all systems
        if await budee.initialize_systems():
            # Start the system
            if await budee.start_system():
                # Run main loop
                await budee.run_main_loop()
            else:
                print("❌ Failed to start system")
        else:
            print("❌ Failed to initialize systems")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ System error: {e}")
        budee.emergency_stop()
    finally:
        await budee.shutdown()

if __name__ == "__main__":
    print("Starting BUD-EE system...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    asyncio.run(main()) 