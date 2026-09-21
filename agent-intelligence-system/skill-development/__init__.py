"""
Progressive Skill Development System for DMlogn8n

This system implements a comprehensive skill development framework where agents
develop expertise through experience, with skill trees, experience tracking,
and adaptive difficulty evolution.

Key Features:
- Skill specialization framework with experience tracking
- Skill tree progression with unlockable abilities
- Experience calculation with multipliers
- Performance analytics and effectiveness measurement
- Integration with D&D 5e rule system
- Skill synergy bonuses and mastery levels
"""

from .core.skill import Skill, SkillCategory, MasteryLevel
from .core.skill_progression import SkillProgression
from .calculators.experience_calculator import ExperienceCalculator
from .systems.skill_unlock_system import SkillUnlockSystem
from .analyzers.performance_analyzer import PerformanceAnalyzer
from .visualization.skill_tree_visualizer import SkillTreeVisualizer
from .integration.dnd5e_integration import DND5EIntegration, SkillToAbilityMapping

__version__ = "1.0.0"
__author__ = "DMlogn8n AI System"

__all__ = [
    "Skill",
    "SkillCategory",
    "MasteryLevel",
    "SkillProgression",
    "ExperienceCalculator",
    "SkillUnlockSystem",
    "PerformanceAnalyzer",
    "SkillTreeVisualizer",
    "DND5EIntegration",
    "SkillToAbilityMapping"
]