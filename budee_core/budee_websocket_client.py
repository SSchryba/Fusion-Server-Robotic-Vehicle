#!/usr/bin/env python3
"""
BUD-EE WebSocket Client
Persistent WebSocket connection to Fusion server for AI communication
"""

import asyncio
import websockets
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    EMOTION = "emotion"
    SERVO = "servo"
    MOTOR = "motor_cmd"
    SOUND = "sound"
    STATUS = "status"
    HEARTBEAT = "heartbeat"
    CHAT = "chat"
    SENSOR_DATA = "sensor_data"
    COMMAND = "command"

@dataclass
class VehicleStatus:
    """Current vehicle status"""
    battery_level: float
    system_temp: float
    position: Dict[str, float]
    servo_angle: int
    motor_speed: int
    camera_active: bool
    emotion_state: str
    interaction_count: int
    uptime: float

@dataclass
class SensorData:
    """Sensor data packet"""
    timestamp: float
    camera_detections: List[Dict]
    audio_level: float
    motion_detected: bool
    proximity_cm: float
    ambient_light: float

class BudeeWebSocketClient:
    """WebSocket client for BUD-EE vehicle communication"""
    
    def __init__(self, server_url: str = "ws://localhost:8000/ws/vehicle"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.running = False
        
        # Connection settings
        self.reconnect_interval = 5.0  # seconds
        self.max_reconnect_attempts = -1  # Infinite
        self.heartbeat_interval = 30.0  # seconds
        self.ping_timeout = 10.0
        
        # Message handling
        self.message_handlers = {}
        self.message_queue = []
        self.response_callbacks = {}
        
        # Status and data
        self.vehicle_status = VehicleStatus(
            battery_level=100.0,
            system_temp=35.0,
            position={"x": 0.0, "y": 0.0, "heading": 0.0},
            servo_angle=0,
            motor_speed=0,
            camera_active=True,
            emotion_state="neutral",
            interaction_count=0,
            uptime=0.0
        )
        
        # External controller references
        self.audio_controller = None
        self.motor_controller = None
        self.emotion_controller = None
        self.interaction_controller = None
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_start_time = 0
        self.last_heartbeat = 0
        
        # Register default message handlers
        self._register_default_handlers()
        
        logger.info(f"WebSocket client initialized for {server_url}")
    
    def set_controllers(self, audio=None, motor=None, emotion=None, interaction=None):
        """Set external controller references"""
        if audio:
            self.audio_controller = audio
        if motor:
            self.motor_controller = motor
        if emotion:
            self.emotion_controller = emotion
        if interaction:
            self.interaction_controller = interaction
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler(MessageType.EMOTION, self._handle_emotion_message)
        self.register_handler(MessageType.SERVO, self._handle_servo_message)
        self.register_handler(MessageType.MOTOR, self._handle_motor_message)
        self.register_handler(MessageType.SOUND, self._handle_sound_message)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat_message)
        self.register_handler(MessageType.CHAT, self._handle_chat_message)
        self.register_handler(MessageType.COMMAND, self._handle_command_message)
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler for a specific message type"""
        self.message_handlers[message_type.value] = handler
        logger.info(f"Registered handler for {message_type.value}")
    
    async def connect(self) -> bool:
        """Establish WebSocket connection"""
        try:
            logger.info(f"Connecting to {self.server_url}...")
            
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=self.ping_timeout,
                ping_timeout=self.ping_timeout,
                close_timeout=10
            )
            
            self.connected = True
            self.connection_start_time = time.time()
            
            logger.info("WebSocket connection established")
            
            # Send initial status
            await self.send_status_update()
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        
        self.connected = False
        self.websocket = None
        logger.info("WebSocket disconnected")
    
    async def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """Send a message to the server"""
        if not self.connected or not self.websocket:
            logger.warning("Cannot send message - not connected")
            return False
        
        try:
            message = {
                "type": message_type.value,
                "timestamp": time.time(),
                "data": data
            }
            
            await self.websocket.send(json.dumps(message))
            self.messages_sent += 1
            
            logger.debug(f"Sent {message_type.value} message")
            return True
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            self.connected = False
            return False
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the server"""
        if not self.connected or not self.websocket:
            return None
        
        try:
            message_str = await self.websocket.recv()
            message = json.loads(message_str)
            
            self.messages_received += 1
            logger.debug(f"Received message: {message.get('type', 'unknown')}")
            
            return message
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by server")
            self.connected = False
            return None
        except Exception as e:
            logger.error(f"Receive message error: {e}")
            return None
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message"""
        try:
            message_type = message.get("type")
            data = message.get("data", {})
            
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(data)
            else:
                logger.warning(f"No handler for message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _handle_emotion_message(self, data: Dict[str, Any]):
        """Handle emotion state change"""
        emotion = data.get("emotion", "neutral")
        intensity = data.get("intensity", 1.0)
        duration = data.get("duration", 0.0)
        
        logger.info(f"Emotion change: {emotion} (intensity: {intensity})")
        
        # Update vehicle status
        self.vehicle_status.emotion_state = emotion
        
        # Pass to emotion controller
        if self.emotion_controller:
            self.emotion_controller.set_emotion(emotion, intensity, duration)
        
        # Trigger interaction response if available
        if self.interaction_controller:
            self.interaction_controller.on_ai_response("", emotion)
    
    async def _handle_servo_message(self, data: Dict[str, Any]):
        """Handle servo control command"""
        command = data.get("command", "center")
        angle = data.get("angle", 0)
        duration = data.get("duration", 0.0)
        
        logger.info(f"Servo command: {command} angle={angle}")
        
        if self.motor_controller:
            if command == "tilt_left":
                self.motor_controller.set_steering(-abs(angle))
            elif command == "tilt_right":
                self.motor_controller.set_steering(abs(angle))
            elif command == "center":
                self.motor_controller.set_steering(0)
            elif command == "set_angle":
                self.motor_controller.set_steering(angle)
        
        # Update status
        self.vehicle_status.servo_angle = angle
        
        # Auto-center after duration
        if duration > 0:
            def reset_servo():
                if self.motor_controller:
                    self.motor_controller.set_steering(0)
                self.vehicle_status.servo_angle = 0
            
            threading.Timer(duration, reset_servo).start()
    
    async def _handle_motor_message(self, data: Dict[str, Any]):
        """Handle motor control command"""
        forward = data.get("forward", False)
        reverse = data.get("reverse", False)
        speed = data.get("speed", 0)
        duration = data.get("duration", 0.0)
        
        logger.info(f"Motor command: forward={forward}, reverse={reverse}, speed={speed}")
        
        if self.motor_controller:
            if forward:
                self.motor_controller.move_forward(speed, duration)
            elif reverse:
                self.motor_controller.move_backward(speed, duration)
            else:
                self.motor_controller.stop_motors()
        
        # Update status
        self.vehicle_status.motor_speed = speed if (forward or reverse) else 0
    
    async def _handle_sound_message(self, data: Dict[str, Any]):
        """Handle audio playback command"""
        filename = data.get("filename", "")
        category = data.get("category", "")
        volume = data.get("volume", 0.8)
        text = data.get("text", "")  # For TTS
        
        logger.info(f"Audio command: file={filename}, text='{text[:30]}...'")
        
        if self.audio_controller:
            if text:
                # Text-to-speech
                self.audio_controller.play_tts_with_fan(text)
            elif filename:
                # Sound file
                self.audio_controller.play_sound(filename, category, volume)
            elif category:
                # Emotion sound
                self.audio_controller.play_emotion_sound(category, volume)
    
    async def _handle_heartbeat_message(self, data: Dict[str, Any]):
        """Handle heartbeat from server"""
        self.last_heartbeat = time.time()
        server_time = data.get("timestamp", 0)
        
        # Send heartbeat response
        await self.send_message(MessageType.HEARTBEAT, {
            "timestamp": time.time(),
            "status": "alive",
            "uptime": time.time() - self.connection_start_time
        })
    
    async def _handle_chat_message(self, data: Dict[str, Any]):
        """Handle chat message from AI"""
        message = data.get("message", "")
        emotion = data.get("emotion", "neutral")
        
        logger.info(f"AI Chat: '{message[:50]}...' (emotion: {emotion})")
        
        # Trigger interaction ritual
        if self.interaction_controller:
            self.interaction_controller.on_ai_response(message, emotion)
        
        # Play TTS if audio controller available
        if self.audio_controller and message:
            self.audio_controller.play_tts_with_fan(message)
    
    async def _handle_command_message(self, data: Dict[str, Any]):
        """Handle general command"""
        command = data.get("command", "")
        parameters = data.get("parameters", {})
        
        logger.info(f"Command: {command} with params: {parameters}")
        
        if command == "status_request":
            await self.send_status_update()
        elif command == "emergency_stop":
            self._emergency_stop()
        elif command == "calibrate":
            # Trigger calibration routine
            pass
        elif command == "reset_position":
            self.vehicle_status.position = {"x": 0.0, "y": 0.0, "heading": 0.0}
    
    def _emergency_stop(self):
        """Emergency stop all systems"""
        logger.warning("Emergency stop activated")
        
        if self.motor_controller:
            self.motor_controller.stop_all()
        
        if self.audio_controller:
            self.audio_controller.stop_all_audio()
        
        if self.interaction_controller:
            self.interaction_controller.emergency_stop()
    
    async def send_status_update(self):
        """Send current vehicle status to server"""
        self.vehicle_status.uptime = time.time() - self.connection_start_time
        
        await self.send_message(MessageType.STATUS, asdict(self.vehicle_status))
    
    async def send_sensor_data(self, sensor_data: SensorData):
        """Send sensor data to server"""
        await self.send_message(MessageType.SENSOR_DATA, asdict(sensor_data))
    
    async def send_chat_response(self, message: str, emotion: str = "neutral"):
        """Send chat response to server"""
        await self.send_message(MessageType.CHAT, {
            "message": message,
            "emotion": emotion,
            "timestamp": time.time()
        })
    
    async def message_loop(self):
        """Main message processing loop"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(
                    self.receive_message(), 
                    timeout=self.ping_timeout
                )
                
                if message:
                    await self.handle_message(message)
                
            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except Exception as e:
                logger.error(f"Message loop error: {e}")
                self.connected = False
                break
    
    async def heartbeat_loop(self):
        """Heartbeat loop"""
        while self.running:
            if self.connected:
                await self.send_message(MessageType.HEARTBEAT, {
                    "timestamp": time.time(),
                    "status": "alive"
                })
            
            await asyncio.sleep(self.heartbeat_interval)
    
    async def run_client(self):
        """Run the WebSocket client with auto-reconnect"""
        self.running = True
        reconnect_attempts = 0
        
        logger.info("Starting WebSocket client...")
        
        while self.running:
            try:
                # Connect to server
                if await self.connect():
                    reconnect_attempts = 0
                    
                    # Start message and heartbeat loops
                    message_task = asyncio.create_task(self.message_loop())
                    heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                    
                    # Wait for either task to complete (connection lost)
                    done, pending = await asyncio.wait(
                        [message_task, heartbeat_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel remaining tasks
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                
                # Connection lost or failed
                await self.disconnect()
                
                if self.running:
                    reconnect_attempts += 1
                    if self.max_reconnect_attempts > 0 and reconnect_attempts > self.max_reconnect_attempts:
                        logger.error("Max reconnection attempts reached")
                        break
                    
                    logger.info(f"Reconnecting in {self.reconnect_interval}s (attempt {reconnect_attempts})")
                    await asyncio.sleep(self.reconnect_interval)
                
            except KeyboardInterrupt:
                logger.info("Client interrupted by user")
                break
            except Exception as e:
                logger.error(f"Client error: {e}")
                await asyncio.sleep(self.reconnect_interval)
        
        await self.disconnect()
        logger.info("WebSocket client stopped")
    
    def stop(self):
        """Stop the WebSocket client"""
        self.running = False
        logger.info("Stopping WebSocket client...")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "connected": self.connected,
            "server_url": self.server_url,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "uptime": time.time() - self.connection_start_time if self.connected else 0,
            "last_heartbeat": self.last_heartbeat,
            "vehicle_status": asdict(self.vehicle_status)
        }

def signal_handler(signum, frame, client):
    """Handle shutdown signals"""
    print("\nShutting down WebSocket client...")
    client.stop()

async def main():
    """Main function for testing"""
    # Create client
    client = BudeeWebSocketClient()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, client))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, client))
    
    try:
        # Run client
        await client.run_client()
    except KeyboardInterrupt:
        print("\nClient interrupted")
    finally:
        client.stop()

if __name__ == "__main__":
    print("🌐 BUD-EE WebSocket Client")
    print("=" * 40)
    print("Connecting to Fusion server...")
    print("Press Ctrl+C to stop")
    
    asyncio.run(main()) 