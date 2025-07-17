#!/usr/bin/env python3
"""
BUD-EE Interaction Ritual System
Handles emotional engagement patterns and response behaviors
"""

import time
import threading
import logging
import random
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pigpio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionState(Enum):
    """Current interaction state"""
    IDLE = "idle"
    ENGAGING = "engaging" 
    WAITING_RESPONSE = "waiting_response"
    DISAPPOINTED = "disappointed"
    EXCITED = "excited"
    DEPARTING = "departing"

@dataclass
class InteractionEvent:
    """Single interaction event"""
    event_type: str
    timestamp: float
    human_detected: bool
    response_received: bool
    audio_played: str = ""
    movement_executed: str = ""

class InteractionRitual:
    """Manages BUD-EE's interaction patterns and emotional responses"""
    
    def __init__(self, audio_controller=None, motor_controller=None):
        # Hardware controllers (injected dependencies)
        self.audio_controller = audio_controller
        self.motor_controller = motor_controller
        
        # GPIO setup for fan control
        self.pi = pigpio.pi()
        if not self.pi.connected:
            logger.warning("Failed to connect to pigpio - fan control disabled")
            self.pi = None
        
        self.FAN_PIN = 20
        if self.pi:
            self.pi.set_mode(self.FAN_PIN, pigpio.OUTPUT)
            self.pi.write(self.FAN_PIN, 0)
        
        # Interaction state
        self.current_state = InteractionState.IDLE
        self.interaction_history = []
        self.attempt_count = 0
        self.max_attempts = 3
        self.response_timeout = 10.0  # seconds
        self.last_interaction_time = 0
        
        # Timing parameters
        self.engagement_delay = 2.0  # seconds before engaging
        self.response_wait_time = 8.0  # seconds to wait for human response
        self.disappointment_delay = 3.0  # seconds before showing disappointment
        
        # Movement patterns
        self.engagement_movements = [
            {"action": "forward", "distance": 0.15, "speed": 25},  # 6 inches forward
            {"action": "wiggle", "count": 2, "speed": 30},
            {"action": "tilt", "angle": 15, "duration": 1.0}
        ]
        
        self.excitement_movements = [
            {"action": "wiggle", "count": 3, "speed": 40},
            {"action": "forward", "distance": 0.1, "speed": 35},
            {"action": "circle", "direction": "right", "angle": 45}
        ]
        
        # Audio patterns
        self.audio_patterns = {
            "greeting": ["hello.wav", "hi_there.wav", "greetings.wav"],
            "excited": ["trill.wav", "happy_beep.wav", "excitement.wav"],
            "disappointed": ["sad_beep.wav", "disappointment.wav", "low_bloop.wav"],
            "fear": ["whimper.wav", "nervous.wav", "retreat.wav"],
            "lonely": ["lonely_call.wav", "low_bloop.wav", "searching.wav"],
            "departure": ["goodbye.wav", "asta_la_vista.wav", "see_you_later.wav"]
        }
        
        # Behavioral flags
        self.running = False
        self.fan_active = False
        self.interaction_thread = None
        
        logger.info("Interaction Ritual system initialized")
    
    def set_controllers(self, audio_controller=None, motor_controller=None):
        """Set external controllers for audio and motor functions"""
        if audio_controller:
            self.audio_controller = audio_controller
        if motor_controller:
            self.motor_controller = motor_controller
    
    def control_fan(self, state: bool, duration: float = 0.0):
        """Control cooling fan state"""
        if not self.pi:
            return
        
        try:
            self.pi.write(self.FAN_PIN, 1 if state else 0)
            self.fan_active = state
            
            if state and duration > 0:
                # Schedule fan turn-off
                threading.Timer(duration, lambda: self.control_fan(False)).start()
            
            logger.info(f"Fan {'ON' if state else 'OFF'}" + (f" for {duration}s" if duration > 0 else ""))
            
        except Exception as e:
            logger.error(f"Fan control error: {e}")
    
    def play_audio_with_fan(self, audio_file: str, category: str = "general"):
        """Play audio while controlling fan synchronization"""
        try:
            # Turn on fan with audio
            self.control_fan(True)
            
            # Play audio through controller
            if self.audio_controller:
                self.audio_controller.play_sound(audio_file)
            else:
                logger.warning(f"Audio controller not available, would play: {audio_file}")
            
            # Keep fan on during audio playback (estimate 2-5 seconds)
            audio_duration = 3.0  # Default estimate
            threading.Timer(audio_duration, lambda: self.control_fan(False)).start()
            
            logger.info(f"Played audio: {audio_file} with fan sync")
            
        except Exception as e:
            logger.error(f"Audio with fan error: {e}")
            self.control_fan(False)
    
    def execute_movement(self, movement: Dict):
        """Execute a movement command"""
        try:
            if not self.motor_controller:
                logger.warning(f"Motor controller not available, would execute: {movement}")
                return
            
            action = movement["action"]
            
            if action == "forward":
                distance = movement.get("distance", 0.1)  # meters
                speed = movement.get("speed", 30)
                duration = distance / 0.05  # Estimate: 5cm per second at normal speed
                self.motor_controller.move_forward(speed, duration)
                
            elif action == "backward":
                distance = movement.get("distance", 0.1)
                speed = movement.get("speed", 25)
                duration = distance / 0.05
                self.motor_controller.move_backward(speed, duration)
                
            elif action == "wiggle":
                count = movement.get("count", 2)
                speed = movement.get("speed", 30)
                self.execute_wiggle(count, speed)
                
            elif action == "tilt":
                angle = movement.get("angle", 15)
                duration = movement.get("duration", 1.0)
                self.execute_tilt(angle, duration)
                
            elif action == "circle":
                direction = movement.get("direction", "right")
                angle = movement.get("angle", 90)
                self.execute_circle(direction, angle)
                
            elif action == "u_turn":
                direction = movement.get("direction", "right")
                self.execute_u_turn(direction)
            
            logger.info(f"Executed movement: {movement}")
            
        except Exception as e:
            logger.error(f"Movement execution error: {e}")
    
    def execute_wiggle(self, count: int, speed: int):
        """Execute wiggle movement (left-right steering)"""
        if not self.motor_controller:
            return
        
        for i in range(count):
            # Wiggle left
            self.motor_controller.set_steering(-20)
            time.sleep(0.3)
            
            # Wiggle right  
            self.motor_controller.set_steering(20)
            time.sleep(0.3)
            
            # Center
            self.motor_controller.set_steering(0)
            time.sleep(0.2)
    
    def execute_tilt(self, angle: int, duration: float):
        """Execute tilt movement (steering hold)"""
        if not self.motor_controller:
            return
        
        self.motor_controller.set_steering(angle)
        time.sleep(duration)
        self.motor_controller.set_steering(0)
    
    def execute_circle(self, direction: str, angle: int):
        """Execute circular movement"""
        if not self.motor_controller:
            return
        
        steering_angle = 25 if direction == "right" else -25
        self.motor_controller.set_steering(steering_angle)
        
        # Move forward while turning for partial circle
        duration = angle / 90.0 * 2.0  # Rough estimate
        self.motor_controller.move_forward(25, duration)
        
        self.motor_controller.set_steering(0)
    
    def execute_u_turn(self, direction: str):
        """Execute U-turn maneuver"""
        if not self.motor_controller:
            return
        
        steering_angle = 30 if direction == "right" else -30
        
        # Full lock steering
        self.motor_controller.set_steering(steering_angle)
        
        # Move forward while turning for ~180 degrees
        self.motor_controller.move_forward(20, 4.0)
        
        # Center steering
        self.motor_controller.set_steering(0)
    
    def select_audio(self, category: str) -> str:
        """Select random audio from category"""
        if category in self.audio_patterns:
            return random.choice(self.audio_patterns[category])
        return "default_beep.wav"
    
    def on_ai_response(self, response_text: str, emotion: str = "neutral"):
        """Called when AI generates a verbal response"""
        logger.info(f"AI Response: {response_text[:50]}... (emotion: {emotion})")
        
        # Record interaction event
        event = InteractionEvent(
            event_type="ai_response",
            timestamp=time.time(),
            human_detected=True,
            response_received=False,
            audio_played=response_text[:30] + "..."
        )
        self.interaction_history.append(event)
        
        # Start engagement ritual
        self.start_engagement_ritual(emotion)
    
    def start_engagement_ritual(self, emotion: str = "neutral"):
        """Start the engagement ritual sequence"""
        if self.current_state == InteractionState.ENGAGING:
            return  # Already engaging
        
        self.current_state = InteractionState.ENGAGING
        self.attempt_count = 0
        
        # Start engagement thread
        self.interaction_thread = threading.Thread(
            target=self._engagement_sequence,
            args=(emotion,),
            daemon=True
        )
        self.interaction_thread.start()
    
    def _engagement_sequence(self, emotion: str):
        """Execute the full engagement sequence"""
        try:
            logger.info(f"Starting engagement ritual with emotion: {emotion}")
            
            # Phase 1: Initial engagement
            self._perform_initial_engagement(emotion)
            
            # Phase 2: Wait for response
            self._wait_for_response()
            
            # Phase 3: Handle outcome
            self._handle_response_outcome()
            
        except Exception as e:
            logger.error(f"Engagement sequence error: {e}")
        finally:
            self.current_state = InteractionState.IDLE
    
    def _perform_initial_engagement(self, emotion: str):
        """Perform initial engagement actions"""
        # Fan activation with audio response
        self.control_fan(True, duration=2.0)
        
        # Small forward movement (attention prompt)
        engagement_move = {"action": "forward", "distance": 0.08, "speed": 25}
        self.execute_movement(engagement_move)
        
        # Emotional expression through movement
        if emotion == "excited":
            self.execute_movement({"action": "wiggle", "count": 2, "speed": 35})
            audio_file = self.select_audio("excited")
        elif emotion == "fear":
            audio_file = self.select_audio("fear")
            # No additional movement for fear
        else:
            # Neutral greeting
            self.execute_movement({"action": "tilt", "angle": 10, "duration": 0.8})
            audio_file = self.select_audio("greeting")
        
        # Play engagement audio
        time.sleep(0.5)  # Brief pause
        self.play_audio_with_fan(audio_file)
        
        logger.info("Initial engagement completed")
    
    def _wait_for_response(self):
        """Wait for human response"""
        self.current_state = InteractionState.WAITING_RESPONSE
        self.last_interaction_time = time.time()
        
        # Wait for response (this would be integrated with speech recognition)
        response_received = self._check_for_response()
        
        if response_received:
            self._handle_positive_response()
        else:
            self._handle_no_response()
    
    def _check_for_response(self) -> bool:
        """Check if human response was received (placeholder)"""
        # This would integrate with speech recognition system
        # For now, simulate random response
        wait_time = 0
        check_interval = 0.5
        
        while wait_time < self.response_wait_time:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Placeholder: Random chance of response (would be actual speech detection)
            if random.random() < 0.3:  # 30% chance per check
                logger.info("Human response detected!")
                return True
        
        logger.info("No human response detected")
        return False
    
    def _handle_positive_response(self):
        """Handle positive human response"""
        self.current_state = InteractionState.EXCITED
        
        # Excited response
        audio_file = self.select_audio("excited")
        self.play_audio_with_fan(audio_file)
        
        # Excitement movement
        excitement_move = random.choice(self.excitement_movements)
        self.execute_movement(excitement_move)
        
        # Reset attempt counter
        self.attempt_count = 0
        
        logger.info("Positive response handled")
    
    def _handle_no_response(self):
        """Handle lack of human response"""
        self.attempt_count += 1
        
        if self.attempt_count < self.max_attempts:
            # Try again with different approach
            logger.info(f"No response - attempt {self.attempt_count}/{self.max_attempts}")
            
            # Slightly different engagement
            time.sleep(1.0)
            self.execute_movement({"action": "tilt", "angle": -15, "duration": 1.0})
            
            audio_file = self.select_audio("lonely")
            self.play_audio_with_fan(audio_file)
            
            # Try again
            self._wait_for_response()
            
        else:
            # Give up and execute disappointment sequence
            self._execute_disappointment_sequence()
    
    def _handle_response_outcome(self):
        """Final handling based on interaction outcome"""
        if self.attempt_count >= self.max_attempts:
            self._execute_disappointment_sequence()
        else:
            # Successful interaction - return to ready state
            self.current_state = InteractionState.IDLE
            logger.info("Interaction completed successfully")
    
    def _execute_disappointment_sequence(self):
        """Execute the disappointment and departure sequence"""
        self.current_state = InteractionState.DISAPPOINTED
        
        logger.info("Executing disappointment sequence")
        
        # Play disappointed sound
        time.sleep(self.disappointment_delay)
        disappointed_audio = self.select_audio("disappointed")
        self.play_audio_with_fan(disappointed_audio)
        
        # Slow reverse
        time.sleep(1.0)
        self.execute_movement({"action": "backward", "distance": 0.12, "speed": 20})
        
        # Dramatic pause
        time.sleep(2.0)
        
        # Aggressive U-turn
        self.current_state = InteractionState.DEPARTING
        self.execute_movement({"action": "u_turn", "direction": "right"})
        
        # Final declaration
        time.sleep(1.0)
        departure_audio = self.select_audio("departure")
        self.play_audio_with_fan(departure_audio)
        
        # Move away
        self.execute_movement({"action": "forward", "distance": 0.2, "speed": 40})
        
        # Reset state
        self.attempt_count = 0
        self.current_state = InteractionState.IDLE
        
        logger.info("Disappointment sequence completed")
    
    def on_human_detected(self, detection_confidence: float = 0.8):
        """Called when human is detected by vision system"""
        current_time = time.time()
        
        # Avoid rapid repeated triggers
        if current_time - self.last_interaction_time < 5.0:
            return
        
        logger.info(f"Human detected with confidence: {detection_confidence}")
        
        # Record detection event
        event = InteractionEvent(
            event_type="human_detected",
            timestamp=current_time,
            human_detected=True,
            response_received=False
        )
        self.interaction_history.append(event)
        
        self.last_interaction_time = current_time
    
    def on_human_gesture(self, gesture_type: str):
        """Called when human gesture is detected"""
        logger.info(f"Human gesture detected: {gesture_type}")
        
        if gesture_type == "wave":
            # Excited response to wave
            self.execute_movement({"action": "wiggle", "count": 3, "speed": 40})
            audio_file = self.select_audio("excited")
            self.play_audio_with_fan(audio_file)
        
        elif gesture_type == "hand_raise":
            # Acknowledging response
            self.execute_movement({"action": "tilt", "angle": 20, "duration": 1.5})
            audio_file = self.select_audio("greeting")
            self.play_audio_with_fan(audio_file)
    
    def emergency_stop(self):
        """Emergency stop all interaction activities"""
        logger.warning("Emergency stop activated")
        
        self.running = False
        self.current_state = InteractionState.IDLE
        
        # Stop fan
        self.control_fan(False)
        
        # Stop any ongoing movements
        if self.motor_controller:
            self.motor_controller.stop_all()
        
        # Join interaction thread if running
        if self.interaction_thread and self.interaction_thread.is_alive():
            self.interaction_thread.join(timeout=2.0)
    
    def get_interaction_stats(self) -> Dict:
        """Get interaction statistics"""
        total_interactions = len(self.interaction_history)
        recent_interactions = [e for e in self.interaction_history 
                             if time.time() - e.timestamp < 300]  # Last 5 minutes
        
        return {
            "total_interactions": total_interactions,
            "recent_interactions": len(recent_interactions),
            "current_state": self.current_state.value,
            "attempt_count": self.attempt_count,
            "fan_active": self.fan_active,
            "last_interaction": self.last_interaction_time
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.emergency_stop()
        
        if self.pi:
            self.pi.stop()
        
        logger.info("Interaction Ritual system cleaned up")

def main():
    """Test function for interaction ritual"""
    try:
        ritual = InteractionRitual()
        
        print("🤖 BUD-EE Interaction Ritual Test")
        print("=" * 40)
        
        # Simulate AI response
        print("Simulating AI response...")
        ritual.on_ai_response("Hello there! How are you doing today?", "excited")
        
        # Wait for sequence to complete
        time.sleep(15)
        
        # Show stats
        stats = ritual.get_interaction_stats()
        print(f"\nInteraction Stats: {stats}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        if 'ritual' in locals():
            ritual.cleanup()

if __name__ == "__main__":
    main() 