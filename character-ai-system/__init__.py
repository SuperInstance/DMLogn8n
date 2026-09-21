"""
Character AI System - Core Engine
Based on AgentDnDengine research for intelligent, personality-driven characters
"""

from character_ai import CharacterAI
from personality_engine import PersonalityEngine
from decision_maker import StrategicDecisionMaker
from memory_system import MemorySystem
from dialogue_generator import DialogueGenerator
from class_modules import ClassAIFactory

__version__ = "1.0.0"
__all__ = [
    "CharacterAI",
    "PersonalityEngine",
    "StrategicDecisionMaker",
    "MemorySystem",
    "DialogueGenerator",
    "ClassAIFactory"
]