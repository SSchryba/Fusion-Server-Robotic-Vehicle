#!/usr/bin/env python3
"""
BUD-EE Emotion Engine
Emotional state management and response coordination system
"""

import time
import threading
import logging
import random
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionType(Enum):
    """Core emotion types"""
    NEUTRAL = "neutral"
    EXCITED = "excited"
    HAPPY = "happy"
    CURIOUS = "curious"
    FEAR = "fear"
    ANXIOUS = "anxious"
    DISAPPOINTED = "disappointed"
    SAD = "sad"
    LONELY = "lonely"
    FRUSTRATED = "frustrated"
    SURPRISED = "surprised"
    CONFIDENT = "confident"
    PLAYFUL = "playful"
    ALERT = "alert"

class EmotionTrigger(Enum):
    """Emotion trigger sources"""
    HUMAN_DETECTED = "human_detected"
    HUMAN_INTERACTION = "human_interaction"
    NO_RESPONSE = "no_response"
    POSITIVE_FEEDBACK = "positive_feedback"
    SUDDEN_MOVEMENT = "sudden_movement"
    LOUD_SOUND = "loud_sound"
    LOW_BATTERY = "low_battery"
    SYSTEM_ERROR = "system_error"
    SUCCESSFUL_TASK = "successful_task"
    NEW_ENVIRONMENT = "new_environment"
    EXTENDED_ISOLATION = "extended_isolation"
    GESTURE_DETECTED = "gesture_detected"

@dataclass
class EmotionState:
    """Current emotion state"""
    primary_emotion: EmotionType
    intensity: float  # 0.0 to 1.0
    duration: float  # seconds
    start_time: float
    triggers: List[EmotionTrigger]
    secondary_emotions: List[EmotionType]

@dataclass
class EmotionEvent:
    """Emotion change event"""
    timestamp: float
    previous_emotion: EmotionType
    new_emotion: EmotionType
    trigger: EmotionTrigger
    intensity: float
    context: Dict[str, Any]

class EmotionEngine:
    """Manages BUD-EE's emotional state and responses"""
    
    def __init__(self, websocket_client=None):
        # External controllers
        self.websocket_client = websocket_client
        self.audio_controller = None
        self.interaction_controller = None
        self.mimic_controller = None
        
        # Current emotional state
        self.current_state = EmotionState(
            primary_emotion=EmotionType.NEUTRAL,
            intensity=0.5,
            duration=0.0,
            start_time=time.time(),
            triggers=[],
            secondary_emotions=[]
        )
        
        # Emotion history and patterns
        self.emotion_history = []
        self.emotion_patterns = {}
        self.baseline_emotion = EmotionType.NEUTRAL
        
        # Emotion configuration
        self.emotion_persistence = {
            EmotionType.EXCITED: 30.0,      # seconds
            EmotionType.HAPPY: 45.0,
            EmotionType.FEAR: 60.0,
            EmotionType.DISAPPOINTED: 40.0,
            EmotionType.LONELY: 120.0,
            EmotionType.CURIOUS: 20.0,
            EmotionType.SURPRISED: 10.0,
            EmotionType.PLAYFUL: 60.0,
            EmotionType.FRUSTRATED: 30.0,
            EmotionType.CONFIDENT: 90.0,
            EmotionType.ALERT: 15.0
        }
        
        # Emotion transition rules
        self.emotion_transitions = {
            EmotionType.NEUTRAL: {
                EmotionTrigger.HUMAN_DETECTED: EmotionType.CURIOUS,
                EmotionTrigger.LOUD_SOUND: EmotionType.ALERT,
                EmotionTrigger.NEW_ENVIRONMENT: EmotionType.CURIOUS,
                EmotionTrigger.EXTENDED_ISOLATION: EmotionType.LONELY
            },
            EmotionType.CURIOUS: {
                EmotionTrigger.HUMAN_INTERACTION: EmotionType.EXCITED,
                EmotionTrigger.NO_RESPONSE: EmotionType.DISAPPOINTED,
                EmotionTrigger.POSITIVE_FEEDBACK: EmotionType.HAPPY,
                EmotionTrigger.SUDDEN_MOVEMENT: EmotionType.SURPRISED
            },
            EmotionType.EXCITED: {
                EmotionTrigger.POSITIVE_FEEDBACK: EmotionType.HAPPY,
                EmotionTrigger.NO_RESPONSE: EmotionType.DISAPPOINTED,
                EmotionTrigger.SUCCESSFUL_TASK: EmotionType.CONFIDENT
            },
            EmotionType.HAPPY: {
                EmotionTrigger.HUMAN_INTERACTION: EmotionType.PLAYFUL,
                EmotionTrigger.NO_RESPONSE: EmotionType.NEUTRAL,
                EmotionTrigger.GESTURE_DETECTED: EmotionType.EXCITED
            },
            EmotionType.DISAPPOINTED: {
                EmotionTrigger.HUMAN_INTERACTION: EmotionType.HOPEFUL,
                EmotionTrigger.EXTENDED_ISOLATION: EmotionType.LONELY,
                EmotionTrigger.SUCCESSFUL_TASK: EmotionType.NEUTRAL
            },
            EmotionType.FEAR: {
                EmotionTrigger.POSITIVE_FEEDBACK: EmotionType.NEUTRAL,
                EmotionTrigger.HUMAN_INTERACTION: EmotionType.ANXIOUS,
                EmotionTrigger.SUCCESSFUL_TASK: EmotionType.CONFIDENT
            },
            EmotionType.LONELY: {
                EmotionTrigger.HUMAN_DETECTED: EmotionType.EXCITED,
                EmotionTrigger.HUMAN_INTERACTION: EmotionType.HAPPY,
                EmotionTrigger.GESTURE_DETECTED: EmotionType.HOPEFUL
            }
        }
        
        # Emotion behavioral responses
        self.emotion_behaviors = {
            EmotionType.EXCITED: {
                "audio": ["excited", "happy"],
                "movement": "energetic",
                "mimic_intensity": 1.5,
                "interaction_eagerness": 1.0
            },
            EmotionType.HAPPY: {
                "audio": ["greeting", "excited"],
                "movement": "welcoming",
                "mimic_intensity": 1.2,
                "interaction_eagerness": 0.8
            },
            EmotionType.CURIOUS: {
                "audio": ["greeting", "acknowledgment"],
                "movement": "investigative",
                "mimic_intensity": 1.0,
                "interaction_eagerness": 0.9
            },
            EmotionType.FEAR: {
                "audio": ["fear", "nervous"],
                "movement": "defensive",
                "mimic_intensity": 0.3,
                "interaction_eagerness": 0.2
            },
            EmotionType.DISAPPOINTED: {
                "audio": ["disappointed", "sad"],
                "movement": "withdrawn",
                "mimic_intensity": 0.5,
                "interaction_eagerness": 0.3
            },
            EmotionType.LONELY: {
                "audio": ["lonely", "searching"],
                "movement": "seeking",
                "mimic_intensity": 0.7,
                "interaction_eagerness": 1.2
            },
            EmotionType.PLAYFUL: {
                "audio": ["excited", "greeting"],
                "movement": "playful",
                "mimic_intensity": 1.8,
                "interaction_eagerness": 1.0
            },
            EmotionType.CONFIDENT: {
                "audio": ["success", "acknowledgment"],
                "movement": "assured",
                "mimic_intensity": 1.1,
                "interaction_eagerness": 0.7
            }
        }
        
        # Decay and update timers
        self.emotion_update_thread = None
        self.running = False
        
        # Context tracking
        self.recent_triggers = []
        self.interaction_count = 0
        self.last_human_interaction = 0
        self.system_uptime_start = time.time()
        
        # Load persistent emotion data if available
        self.data_file = Path("emotion_data.json")
        self.load_emotion_data()
        
        logger.info("Emotion Engine initialized")
    
    def set_controllers(self, audio=None, interaction=None, mimic=None, websocket=None):
        """Set external controller references"""
        if audio:
            self.audio_controller = audio
        if interaction:
            self.interaction_controller = interaction
        if mimic:
            self.mimic_controller = mimic
        if websocket:
            self.websocket_client = websocket
    
    def set_emotion(self, emotion: EmotionType, intensity: float = 0.8, 
                   duration: float = None, trigger: EmotionTrigger = None):
        """Set the current emotion state"""
        
        if isinstance(emotion, str):
            try:
                emotion = EmotionType(emotion.lower())
            except ValueError:
                logger.warning(f"Unknown emotion: {emotion}")
                return
        
        # Use default duration if not specified
        if duration is None:
            duration = self.emotion_persistence.get(emotion, 30.0)
        
        # Clamp intensity
        intensity = max(0.0, min(1.0, intensity))
        
        # Record emotion change event
        previous_emotion = self.current_state.primary_emotion
        
        emotion_event = EmotionEvent(
            timestamp=time.time(),
            previous_emotion=previous_emotion,
            new_emotion=emotion,
            trigger=trigger or EmotionTrigger.SYSTEM_ERROR,
            intensity=intensity,
            context=self._get_current_context()
        )
        
        self.emotion_history.append(emotion_event)
        
        # Update current state
        self.current_state = EmotionState(
            primary_emotion=emotion,
            intensity=intensity,
            duration=duration,
            start_time=time.time(),
            triggers=[trigger] if trigger else [],
            secondary_emotions=[]
        )
        
        logger.info(f"Emotion changed: {previous_emotion.value} → {emotion.value} "
                   f"(intensity: {intensity:.1f}, duration: {duration:.1f}s)")
        
        # Trigger behavioral responses
        self._trigger_emotion_responses(emotion, intensity)
        
        # Notify external systems
        self._broadcast_emotion_change(emotion, intensity, duration)
        
        # Limit history size
        if len(self.emotion_history) > 200:
            self.emotion_history = self.emotion_history[-150:]
    
    def trigger_emotion(self, trigger: EmotionTrigger, context: Dict[str, Any] = None):
        """Trigger an emotion based on an external event"""
        
        current_emotion = self.current_state.primary_emotion
        intensity_modifier = 1.0
        
        # Add to recent triggers
        self.recent_triggers.append({
            "trigger": trigger,
            "timestamp": time.time(),
            "context": context or {}
        })
        
        # Keep only recent triggers (last 5 minutes)
        cutoff_time = time.time() - 300
        self.recent_triggers = [t for t in self.recent_triggers 
                              if t["timestamp"] > cutoff_time]
        
        # Determine new emotion based on transition rules
        new_emotion = current_emotion
        
        if current_emotion in self.emotion_transitions:
            transitions = self.emotion_transitions[current_emotion]
            if trigger in transitions:
                new_emotion = transitions[trigger]
        
        # Apply context modifiers
        if context:
            intensity_modifier = self._calculate_intensity_modifier(trigger, context)
        
        # Calculate new intensity
        base_intensity = 0.7
        new_intensity = min(1.0, base_intensity * intensity_modifier)
        
        # Apply emotion if it's different or intensity is significantly different
        if (new_emotion != current_emotion or 
            abs(new_intensity - self.current_state.intensity) > 0.3):
            
            self.set_emotion(new_emotion, new_intensity, trigger=trigger)
        
        logger.info(f"Emotion trigger: {trigger.value} → {new_emotion.value}")
    
    def _calculate_intensity_modifier(self, trigger: EmotionTrigger, context: Dict[str, Any]) -> float:
        """Calculate intensity modifier based on context"""
        modifier = 1.0
        
        # Recent trigger frequency
        recent_same_triggers = [t for t in self.recent_triggers 
                              if t["trigger"] == trigger]
        
        if len(recent_same_triggers) > 3:
            modifier *= 0.7  # Reduce intensity for repeated triggers
        
        # Time-based modifiers
        time_since_last_interaction = time.time() - self.last_human_interaction
        
        if trigger == EmotionTrigger.HUMAN_DETECTED:
            if time_since_last_interaction > 300:  # 5 minutes
                modifier *= 1.5  # More excited after isolation
        
        elif trigger == EmotionTrigger.NO_RESPONSE:
            if time_since_last_interaction < 60:  # Recent interaction
                modifier *= 1.3  # More disappointed if recently engaged
        
        # Context-specific modifiers
        if "confidence" in context:
            confidence = context["confidence"]
            modifier *= (0.5 + confidence)  # Higher confidence = stronger emotion
        
        if "interaction_count" in context:
            count = context["interaction_count"]
            if count > 5:
                modifier *= 1.2  # More emotional with repeated interactions
        
        return max(0.3, min(2.0, modifier))
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current system context for emotion analysis"""
        return {
            "uptime": time.time() - self.system_uptime_start,
            "interaction_count": self.interaction_count,
            "time_since_last_interaction": time.time() - self.last_human_interaction,
            "recent_trigger_count": len(self.recent_triggers),
            "current_intensity": self.current_state.intensity
        }
    
    def _trigger_emotion_responses(self, emotion: EmotionType, intensity: float):
        """Trigger behavioral responses based on emotion"""
        
        if emotion not in self.emotion_behaviors:
            return
        
        behaviors = self.emotion_behaviors[emotion]
        
        # Audio response
        if self.audio_controller and "audio" in behaviors:
            audio_categories = behaviors["audio"]
            category = random.choice(audio_categories)
            volume = 0.3 + (intensity * 0.7)  # Scale volume with intensity
            self.audio_controller.play_emotion_sound(category, volume)
        
        # Mimic system response
        if self.mimic_controller and "mimic_intensity" in behaviors:
            mimic_intensity = behaviors["mimic_intensity"] * intensity
            self.mimic_controller.set_mimic_intensity(mimic_intensity)
        
        # Interaction system response
        if self.interaction_controller and "interaction_eagerness" in behaviors:
            eagerness = behaviors["interaction_eagerness"]
            # This would modify interaction parameters
            # self.interaction_controller.set_eagerness(eagerness)
    
    def _broadcast_emotion_change(self, emotion: EmotionType, intensity: float, duration: float):
        """Broadcast emotion change to external systems"""
        
        if self.websocket_client:
            # Send emotion update to server
            emotion_data = {
                "emotion": emotion.value,
                "intensity": intensity,
                "duration": duration,
                "timestamp": time.time()
            }
            
            # This would be called asynchronously in real implementation
            # asyncio.create_task(self.websocket_client.send_emotion_update(emotion_data))
    
    def update_emotion_decay(self):
        """Update emotion decay over time"""
        current_time = time.time()
        elapsed = current_time - self.current_state.start_time
        
        # Check if emotion should decay
        if elapsed >= self.current_state.duration:
            # Decay to neutral or baseline emotion
            if self.current_state.primary_emotion != self.baseline_emotion:
                decay_intensity = max(0.3, self.current_state.intensity * 0.7)
                self.set_emotion(self.baseline_emotion, decay_intensity, 
                               trigger=EmotionTrigger.SYSTEM_ERROR)  # Natural decay
        
        # Handle isolation detection
        time_since_interaction = current_time - self.last_human_interaction
        if time_since_interaction > 600 and self.current_state.primary_emotion != EmotionType.LONELY:  # 10 minutes
            self.trigger_emotion(EmotionTrigger.EXTENDED_ISOLATION)
    
    def start_emotion_updates(self):
        """Start the emotion update thread"""
        self.running = True
        self.emotion_update_thread = threading.Thread(
            target=self._emotion_update_loop, 
            daemon=True
        )
        self.emotion_update_thread.start()
        logger.info("Emotion update thread started")
    
    def _emotion_update_loop(self):
        """Emotion update loop"""
        while self.running:
            try:
                self.update_emotion_decay()
                time.sleep(5.0)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Emotion update error: {e}")
                time.sleep(1.0)
    
    def stop_emotion_updates(self):
        """Stop the emotion update thread"""
        self.running = False
        if self.emotion_update_thread:
            self.emotion_update_thread.join(timeout=2.0)
        logger.info("Emotion updates stopped")
    
    def on_human_detected(self, confidence: float = 0.8):
        """Called when human is detected"""
        self.trigger_emotion(EmotionTrigger.HUMAN_DETECTED, {
            "confidence": confidence,
            "timestamp": time.time()
        })
    
    def on_human_interaction(self, interaction_type: str = "general"):
        """Called when human interaction occurs"""
        self.last_human_interaction = time.time()
        self.interaction_count += 1
        
        self.trigger_emotion(EmotionTrigger.HUMAN_INTERACTION, {
            "interaction_type": interaction_type,
            "interaction_count": self.interaction_count
        })
    
    def on_positive_feedback(self, feedback_strength: float = 1.0):
        """Called when positive feedback is received"""
        self.trigger_emotion(EmotionTrigger.POSITIVE_FEEDBACK, {
            "strength": feedback_strength
        })
    
    def on_no_response(self, attempt_count: int = 1):
        """Called when no human response is received"""
        self.trigger_emotion(EmotionTrigger.NO_RESPONSE, {
            "attempt_count": attempt_count
        })
    
    def on_gesture_detected(self, gesture_type: str):
        """Called when human gesture is detected"""
        self.trigger_emotion(EmotionTrigger.GESTURE_DETECTED, {
            "gesture_type": gesture_type
        })
    
    def on_successful_task(self, task_type: str):
        """Called when a task is completed successfully"""
        self.trigger_emotion(EmotionTrigger.SUCCESSFUL_TASK, {
            "task_type": task_type
        })
    
    def on_system_error(self, error_type: str, severity: str = "medium"):
        """Called when system error occurs"""
        if severity == "high":
            self.trigger_emotion(EmotionTrigger.SYSTEM_ERROR, {
                "error_type": error_type,
                "severity": severity
            })
    
    def get_current_emotion(self) -> Dict[str, Any]:
        """Get current emotion state"""
        return {
            "emotion": self.current_state.primary_emotion.value,
            "intensity": self.current_state.intensity,
            "duration_remaining": max(0, self.current_state.duration - 
                                    (time.time() - self.current_state.start_time)),
            "triggers": [t.value for t in self.current_state.triggers],
            "uptime": time.time() - self.system_uptime_start
        }
    
    def get_emotion_stats(self) -> Dict[str, Any]:
        """Get emotion system statistics"""
        recent_emotions = [e for e in self.emotion_history 
                          if time.time() - e.timestamp < 3600]  # Last hour
        
        emotion_counts = {}
        for event in recent_emotions:
            emotion = event.new_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        trigger_counts = {}
        for trigger_data in self.recent_triggers:
            trigger = trigger_data["trigger"].value
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        return {
            "current_emotion": self.get_current_emotion(),
            "total_emotion_changes": len(self.emotion_history),
            "recent_emotion_changes": len(recent_emotions),
            "emotion_distribution": emotion_counts,
            "trigger_distribution": trigger_counts,
            "interaction_count": self.interaction_count,
            "baseline_emotion": self.baseline_emotion.value,
            "running": self.running
        }
    
    def save_emotion_data(self):
        """Save emotion data to file"""
        try:
            data = {
                "interaction_count": self.interaction_count,
                "last_human_interaction": self.last_human_interaction,
                "baseline_emotion": self.baseline_emotion.value,
                "emotion_patterns": self.emotion_patterns,
                "recent_emotions": [
                    {
                        "emotion": e.new_emotion.value,
                        "timestamp": e.timestamp,
                        "intensity": e.intensity
                    }
                    for e in self.emotion_history[-50:]  # Last 50 emotions
                ]
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Emotion data saved")
            
        except Exception as e:
            logger.error(f"Save emotion data error: {e}")
    
    def load_emotion_data(self):
        """Load emotion data from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                self.interaction_count = data.get("interaction_count", 0)
                self.last_human_interaction = data.get("last_human_interaction", 0)
                
                baseline_str = data.get("baseline_emotion", "neutral")
                try:
                    self.baseline_emotion = EmotionType(baseline_str)
                except ValueError:
                    self.baseline_emotion = EmotionType.NEUTRAL
                
                self.emotion_patterns = data.get("emotion_patterns", {})
                
                logger.info("Emotion data loaded")
            
        except Exception as e:
            logger.error(f"Load emotion data error: {e}")
    
    def cleanup(self):
        """Clean up emotion engine"""
        self.stop_emotion_updates()
        self.save_emotion_data()
        logger.info("Emotion Engine cleaned up")

def main():
    """Test function for emotion engine"""
    try:
        engine = EmotionEngine()
        
        print("🎭 BUD-EE Emotion Engine Test")
        print("=" * 40)
        
        # Start emotion updates
        engine.start_emotion_updates()
        
        # Simulate some interactions
        print("Simulating emotion triggers...")
        
        engine.on_human_detected(0.9)
        time.sleep(2)
        
        engine.on_human_interaction("greeting")
        time.sleep(1)
        
        engine.on_positive_feedback(0.8)
        time.sleep(2)
        
        engine.on_no_response(1)
        time.sleep(1)
        
        engine.on_gesture_detected("wave")
        time.sleep(1)
        
        # Show current state
        current = engine.get_current_emotion()
        print(f"\nCurrent Emotion: {current}")
        
        # Show stats
        stats = engine.get_emotion_stats()
        print(f"\nEmotion Stats: {stats}")
        
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        if 'engine' in locals():
            engine.cleanup()

if __name__ == "__main__":
    main() 