"""
Autonomous AI Agent Framework

A modular, self-directing AI agent system with persistent memory,
adaptive planning, and autonomous execution capabilities.
"""

__version__ = "1.0.0"
__author__ = "AI Engineer"
__description__ = "Autonomous AI Agent Framework with Adaptive Feedback Loops"

from .core.agent import AutonomousAgent
from .core.directive import DirectiveManager
from .memory.vector_store import VectorMemory
from .modules.planner import TaskPlanner
from .modules.executor import TaskExecutor
from .modules.critic import TaskCritic
from .modules.observer import TaskObserver
from .actions.action_system import ActionSystem
from .safeguards.safety_manager import SafetyManager

__all__ = [
    "AutonomousAgent",
    "DirectiveManager", 
    "VectorMemory",
    "TaskPlanner",
    "TaskExecutor", 
    "TaskCritic",
    "TaskObserver",
    "ActionSystem",
    "SafetyManager"
] 