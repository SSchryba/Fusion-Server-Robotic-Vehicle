#!/usr/bin/env python3
"""
BUD-EE Audio Control System
Manages speaker output, fan synchronization, and emotion-based audio
"""

import os
import time
import subprocess
import threading
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import pigpio

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available, using subprocess for audio")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioMethod(Enum):
    """Audio playback methods"""
    PYGAME = "pygame"
    APLAY = "aplay"
    OMXPLAYER = "omxplayer"
    SUBPROCESS = "subprocess"

@dataclass
class AudioEvent:
    """Audio playback event"""
    filename: str
    category: str
    start_time: float
    duration: float = 0.0
    volume: float = 1.0
    fan_sync: bool = True
    completed: bool = False

class AudioControl:
    """Audio control system with fan synchronization"""
    
    def __init__(self, sounds_directory: str = "sounds"):
        self.sounds_directory = Path(sounds_directory)
        self.sounds_directory.mkdir(exist_ok=True)
        
        # GPIO setup for fan control
        self.pi = pigpio.pi()
        if not self.pi.connected:
            logger.warning("Failed to connect to pigpio - fan control disabled")
            self.pi = None
        
        self.FAN_PIN = 20
        if self.pi:
            self.pi.set_mode(self.FAN_PIN, pigpio.OUTPUT)
            self.pi.write(self.FAN_PIN, 0)
        
        # Audio configuration
        self.audio_method = self._detect_audio_method()
        self.default_volume = 0.8
        self.fan_sync_enabled = True
        
        # Initialize pygame if available
        if self.audio_method == AudioMethod.PYGAME and PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                logger.info("pygame mixer initialized")
            except Exception as e:
                logger.error(f"pygame mixer init error: {e}")
                self.audio_method = AudioMethod.APLAY
        
        # Audio event tracking
        self.audio_history = []
        self.current_audio = None
        self.fan_active = False
        
        # Emotion-based audio categories
        self.emotion_sounds = {
            "excited": ["trill.wav", "happy_beep.wav", "excitement.wav", "cheer.wav"],
            "fear": ["whimper.wav", "nervous.wav", "retreat.wav", "scared_beep.wav"],
            "lonely": ["lonely_call.wav", "low_bloop.wav", "searching.wav", "sad_tone.wav"],
            "greeting": ["hello.wav", "hi_there.wav", "greetings.wav", "welcome.wav"],
            "disappointed": ["sad_beep.wav", "disappointment.wav", "low_bloop.wav", "sigh.wav"],
            "departure": ["goodbye.wav", "asta_la_vista.wav", "see_you_later.wav", "farewell.wav"],
            "acknowledgment": ["beep.wav", "acknowledge.wav", "understood.wav", "yes_beep.wav"],
            "alert": ["alert.wav", "attention.wav", "notification.wav", "ping.wav"],
            "error": ["error_beep.wav", "problem.wav", "malfunction.wav", "warning.wav"],
            "success": ["success.wav", "complete.wav", "done.wav", "achievement.wav"]
        }
        
        # Generate default sounds if they don't exist
        self._ensure_default_sounds()
        
        logger.info(f"Audio Control initialized with method: {self.audio_method.value}")
    
    def _detect_audio_method(self) -> AudioMethod:
        """Detect the best available audio playback method"""
        if PYGAME_AVAILABLE:
            return AudioMethod.PYGAME
        
        # Check for aplay (ALSA)
        try:
            subprocess.run(['aplay', '--version'], 
                         capture_output=True, check=True, timeout=2)
            return AudioMethod.APLAY
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for omxplayer (Raspberry Pi)
        try:
            subprocess.run(['omxplayer', '--version'], 
                         capture_output=True, check=True, timeout=2)
            return AudioMethod.OMXPLAYER
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return AudioMethod.SUBPROCESS
    
    def _ensure_default_sounds(self):
        """Create default sound files if they don't exist"""
        # This would normally load actual sound files
        # For now, we'll create placeholder files
        for category, sounds in self.emotion_sounds.items():
            for sound in sounds:
                sound_path = self.sounds_directory / sound
                if not sound_path.exists():
                    # Create placeholder file
                    sound_path.touch()
        
        logger.info(f"Ensured {len(self.emotion_sounds)} sound categories exist")
    
    def control_fan(self, state: bool, duration: float = 0.0):
        """Control cooling fan state"""
        if not self.pi:
            logger.debug(f"Fan control simulated: {'ON' if state else 'OFF'}")
            return
        
        try:
            self.pi.write(self.FAN_PIN, 1 if state else 0)
            self.fan_active = state
            
            if state and duration > 0:
                # Schedule fan turn-off
                threading.Timer(duration, lambda: self.control_fan(False)).start()
            
            logger.debug(f"Fan {'ON' if state else 'OFF'}" + 
                        (f" for {duration}s" if duration > 0 else ""))
            
        except Exception as e:
            logger.error(f"Fan control error: {e}")
    
    def get_sound_path(self, filename: str, category: str = "") -> Optional[Path]:
        """Get full path to sound file"""
        # Try direct filename first
        sound_path = self.sounds_directory / filename
        if sound_path.exists():
            return sound_path
        
        # Try with category prefix
        if category:
            category_filename = f"{category}_{filename}"
            sound_path = self.sounds_directory / category_filename
            if sound_path.exists():
                return sound_path
        
        # Try to find any file with similar name
        for existing_file in self.sounds_directory.glob("*.wav"):
            if filename.lower() in existing_file.name.lower():
                return existing_file
        
        logger.warning(f"Sound file not found: {filename}")
        return None
    
    def estimate_audio_duration(self, sound_path: Path) -> float:
        """Estimate audio duration (simplified)"""
        try:
            # Use file size as rough estimate (very crude)
            file_size = sound_path.stat().st_size
            # Assume roughly 44.1kHz, 16-bit, stereo
            estimated_duration = max(1.0, file_size / (44100 * 2 * 2))
            return min(estimated_duration, 10.0)  # Cap at 10 seconds
        except:
            return 3.0  # Default duration
    
    def play_sound_pygame(self, sound_path: Path, volume: float = 1.0) -> float:
        """Play sound using pygame"""
        try:
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(volume)
            channel = sound.play()
            
            # Wait for completion or timeout
            duration = 0
            while channel.get_busy() and duration < 10:
                time.sleep(0.1)
                duration += 0.1
            
            return duration
            
        except Exception as e:
            logger.error(f"pygame sound error: {e}")
            return 0.0
    
    def play_sound_aplay(self, sound_path: Path, volume: float = 1.0) -> float:
        """Play sound using aplay"""
        try:
            # Calculate volume parameter for aplay (if supported)
            volume_percent = int(volume * 100)
            
            cmd = ['aplay', str(sound_path)]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            duration = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"aplay error: {result.stderr.decode()}")
                return 0.0
            
            return duration
            
        except subprocess.TimeoutExpired:
            logger.warning("aplay timeout")
            return 0.0
        except Exception as e:
            logger.error(f"aplay error: {e}")
            return 0.0
    
    def play_sound_omxplayer(self, sound_path: Path, volume: float = 1.0) -> float:
        """Play sound using omxplayer"""
        try:
            # omxplayer volume is in millibels (dB * 100)
            volume_mb = int((volume - 1.0) * 2000)  # Convert to dB range
            
            cmd = ['omxplayer', '--vol', str(volume_mb), str(sound_path)]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            duration = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"omxplayer error: {result.stderr.decode()}")
                return 0.0
            
            return duration
            
        except subprocess.TimeoutExpired:
            logger.warning("omxplayer timeout")
            return 0.0
        except Exception as e:
            logger.error(f"omxplayer error: {e}")
            return 0.0
    
    def play_sound(self, filename: str, category: str = "", volume: float = None, 
                   fan_sync: bool = None) -> bool:
        """Play a sound file with optional fan synchronization"""
        
        if volume is None:
            volume = self.default_volume
        
        if fan_sync is None:
            fan_sync = self.fan_sync_enabled
        
        # Get sound file path
        sound_path = self.get_sound_path(filename, category)
        if not sound_path:
            logger.error(f"Cannot play sound: {filename}")
            return False
        
        # Start fan if synchronized
        if fan_sync:
            self.control_fan(True)
        
        try:
            start_time = time.time()
            duration = 0.0
            
            # Play audio based on selected method
            if self.audio_method == AudioMethod.PYGAME:
                duration = self.play_sound_pygame(sound_path, volume)
            elif self.audio_method == AudioMethod.APLAY:
                duration = self.play_sound_aplay(sound_path, volume)
            elif self.audio_method == AudioMethod.OMXPLAYER:
                duration = self.play_sound_omxplayer(sound_path, volume)
            else:
                # Fallback - estimate duration and simulate
                duration = self.estimate_audio_duration(sound_path)
                time.sleep(duration)
            
            # Create audio event record
            audio_event = AudioEvent(
                filename=filename,
                category=category,
                start_time=start_time,
                duration=duration,
                volume=volume,
                fan_sync=fan_sync,
                completed=True
            )
            
            self.audio_history.append(audio_event)
            
            # Limit history size
            if len(self.audio_history) > 100:
                self.audio_history.pop(0)
            
            logger.info(f"Played sound: {filename} ({duration:.1f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Sound playback error: {e}")
            return False
        finally:
            # Turn off fan after playback
            if fan_sync:
                self.control_fan(False)
    
    def play_emotion_sound(self, emotion: str, volume: float = None) -> bool:
        """Play a random sound from an emotion category"""
        if emotion not in self.emotion_sounds:
            logger.warning(f"Unknown emotion category: {emotion}")
            return False
        
        # Select random sound from category
        import random
        sound_options = self.emotion_sounds[emotion]
        selected_sound = random.choice(sound_options)
        
        return self.play_sound(selected_sound, category=emotion, volume=volume)
    
    def play_sequence(self, sound_sequence: List[Dict[str, Any]], 
                     delay_between: float = 0.5) -> bool:
        """Play a sequence of sounds with delays"""
        try:
            for i, sound_info in enumerate(sound_sequence):
                filename = sound_info.get("filename", "")
                category = sound_info.get("category", "")
                volume = sound_info.get("volume", self.default_volume)
                
                if i > 0:  # Add delay between sounds
                    time.sleep(delay_between)
                
                success = self.play_sound(filename, category, volume)
                if not success:
                    logger.warning(f"Failed to play sound {i+1} in sequence: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Sound sequence error: {e}")
            return False
    
    def play_tts_with_fan(self, text: str, voice: str = "espeak") -> bool:
        """Play text-to-speech with fan synchronization"""
        try:
            # Start fan
            if self.fan_sync_enabled:
                self.control_fan(True)
            
            if voice == "espeak":
                # Use espeak for TTS
                cmd = ['espeak', '-s', '150', '-v', 'en+f3', text]
                
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, timeout=15)
                duration = time.time() - start_time
                
                if result.returncode != 0:
                    logger.error(f"espeak error: {result.stderr.decode()}")
                    return False
            
            else:
                # Fallback - simulate TTS duration
                duration = len(text) * 0.1  # Rough estimate
                time.sleep(duration)
            
            # Create audio event
            audio_event = AudioEvent(
                filename=f"TTS: {text[:30]}...",
                category="tts",
                start_time=start_time,
                duration=duration,
                volume=self.default_volume,
                fan_sync=True,
                completed=True
            )
            
            self.audio_history.append(audio_event)
            
            logger.info(f"Played TTS: '{text[:50]}...' ({duration:.1f}s)")
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("TTS timeout")
            return False
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
        finally:
            # Turn off fan
            if self.fan_sync_enabled:
                self.control_fan(False)
    
    def stop_all_audio(self):
        """Stop all audio playback"""
        try:
            if self.audio_method == AudioMethod.PYGAME and PYGAME_AVAILABLE:
                pygame.mixer.stop()
            
            # Kill any running audio processes
            subprocess.run(['pkill', '-f', 'aplay'], capture_output=True)
            subprocess.run(['pkill', '-f', 'omxplayer'], capture_output=True)
            subprocess.run(['pkill', '-f', 'espeak'], capture_output=True)
            
            # Turn off fan
            self.control_fan(False)
            
            logger.info("All audio stopped")
            
        except Exception as e:
            logger.error(f"Stop audio error: {e}")
    
    def set_volume(self, volume: float):
        """Set default volume (0.0 to 1.0)"""
        self.default_volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to {self.default_volume:.1f}")
    
    def set_fan_sync(self, enabled: bool):
        """Enable or disable fan synchronization"""
        self.fan_sync_enabled = enabled
        logger.info(f"Fan sync {'enabled' if enabled else 'disabled'}")
    
    def get_audio_stats(self) -> Dict[str, Any]:
        """Get audio system statistics"""
        recent_events = [e for e in self.audio_history 
                        if time.time() - e.start_time < 300]  # Last 5 minutes
        
        category_counts = {}
        for event in recent_events:
            category_counts[event.category] = category_counts.get(event.category, 0) + 1
        
        return {
            "audio_method": self.audio_method.value,
            "total_events": len(self.audio_history),
            "recent_events": len(recent_events),
            "category_counts": category_counts,
            "default_volume": self.default_volume,
            "fan_sync_enabled": self.fan_sync_enabled,
            "fan_active": self.fan_active,
            "sounds_directory": str(self.sounds_directory),
            "available_emotions": list(self.emotion_sounds.keys())
        }
    
    def test_audio_system(self):
        """Test the audio system with various sounds"""
        print("🔊 Testing BUD-EE Audio System")
        print("=" * 40)
        
        # Test basic playback
        print("Testing basic audio playback...")
        success = self.play_emotion_sound("greeting")
        print(f"Basic playback: {'✅' if success else '❌'}")
        
        time.sleep(1)
        
        # Test emotion sounds
        print("\nTesting emotion sounds...")
        for emotion in ["excited", "disappointed", "alert"]:
            print(f"  Testing {emotion}...")
            success = self.play_emotion_sound(emotion, volume=0.6)
            time.sleep(0.5)
        
        # Test TTS
        print("\nTesting text-to-speech...")
        success = self.play_tts_with_fan("Hello, I am BUD-EE!")
        print(f"TTS: {'✅' if success else '❌'}")
        
        # Show stats
        stats = self.get_audio_stats()
        print(f"\nAudio Stats: {stats}")
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_all_audio()
        
        if PYGAME_AVAILABLE and self.audio_method == AudioMethod.PYGAME:
            try:
                pygame.mixer.quit()
            except:
                pass
        
        if self.pi:
            self.pi.stop()
        
        logger.info("Audio Control cleaned up")

def main():
    """Test function for audio control"""
    try:
        audio = AudioControl()
        
        # Run audio system test
        audio.test_audio_system()
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        if 'audio' in locals():
            audio.cleanup()

if __name__ == "__main__":
    main() 