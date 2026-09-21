"""
Class-specific AI modules
Each class has unique behavioral patterns and decision-making logic
"""

from .base_class_ai import BaseClassAI
from .factory import ClassAIFactory

__all__ = ["BaseClassAI", "ClassAIFactory"]