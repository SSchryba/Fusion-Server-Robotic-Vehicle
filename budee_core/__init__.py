#!/usr/bin/env python3
"""
BUD-EE Core Package
Autonomous Emotional AI Vehicle System

This package provides a complete framework for building an emotionally intelligent,
physically embodied AI vehicle that can interact naturally with humans through
vision, gesture recognition, emotional responses, and motor control.

Main Components:
- VisionMotorFusion: Real-time object tracking and navigation
- EmotionEngine: Dynamic emotional state management
- InteractionRitual: Complex behavioral engagement patterns
- MimicEngine: Human gesture detection and mirroring
- AudioControl: Synchronized speech and sound effects
- BudeeWebSocketClient: Server communication
- CalibrationSystem: Auto-calibration routines

Usage:
    from budee_core import BudeeSystem
    
    budee = BudeeSystem()
    await budee.initialize_systems()
    await budee.start_system()
    await budee.run_main_loop()
"""

__version__ = "1.0.0"
__author__ = "BUD-EE Development Team"
__license__ = "MIT"

# Core system imports
from .budee_main import BudeeSystem
from .vision_motor_fusion import VisionMotorFusion
from .emotion_engine import EmotionEngine, EmotionType, EmotionTrigger
from .interaction_ritual import InteractionRitual, InteractionState
from .mimic_engine import MimicEngine, GestureType
from .audio_control import AudioControl, AudioMethod
from .budee_websocket_client import BudeeWebSocketClient, MessageType
from .calibration_routine import BudeeCalibrationSystem

# Package information
__all__ = [
    "BudeeSystem",
    "VisionMotorFusion", 
    "EmotionEngine",
    "EmotionType",
    "EmotionTrigger",
    "InteractionRitual",
    "InteractionState",
    "MimicEngine",
    "GestureType",
    "AudioControl",
    "AudioMethod",
    "BudeeWebSocketClient",
    "MessageType",
    "BudeeCalibrationSystem"
] 