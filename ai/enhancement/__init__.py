"""
AI Enhancement System - Advanced AI Agent Enhancement Suite

This package provides comprehensive AI agent enhancement capabilities including:
- Conversation optimization for better dialogue quality
- Behavior refinement for personality consistency
- Response acceleration for faster performance
- Context management for better memory handling
- Emotional enhancement for nuanced responses
- Creativity boosting for innovative problem-solving
- Learning acceleration for rapid adaptation
- Quality validation for output assurance

Author: AI Enhancement System
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Enhancement System"

# Import main classes
from .conversation_optimizer import ConversationOptimizer, ConversationStyle, ConversationMetrics
from .behavior_refiner import BehaviorRefiner, PersonalityProfile, BehaviorMetrics
from .response_accelerator import ResponseAccelerator, OptimizationStrategy, PerformanceMetrics
from .context_manager import ContextManager, ContextType, ContextEntry
from .emotion_enhancer import EmotionEnhancer, EmotionType, EmotionalTone, EmotionalResponse
from .creativity_booster import CreativityBooster, CreativityTechnique, CreativeIdea
from .learning_accelerator import LearningAccelerator, LearningType, LearningMetrics
from .quality_validator import QualityValidator, QualityDimension, ValidationResult

# Import integration class
from .enhancement_manager import EnhancementManager

# Export all main classes
__all__ = [
    # Core enhancement classes
    'ConversationOptimizer',
    'BehaviorRefiner',
    'ResponseAccelerator',
    'ContextManager',
    'EmotionEnhancer',
    'CreativityBooster',
    'LearningAccelerator',
    'QualityValidator',

    # Integration
    'EnhancementManager',

    # Enums and data classes
    'ConversationStyle',
    'ConversationMetrics',
    'PersonalityProfile',
    'BehaviorMetrics',
    'OptimizationStrategy',
    'PerformanceMetrics',
    'ContextType',
    'ContextEntry',
    'EmotionType',
    'EmotionalTone',
    'EmotionalResponse',
    'CreativityTechnique',
    'CreativeIdea',
    'LearningType',
    'LearningMetrics',
    'QualityDimension',
    'ValidationResult'
]