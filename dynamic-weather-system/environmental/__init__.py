"""
Environmental Impact System

This module handles the effects of weather on gameplay mechanics,
including movement, combat, exploration, and environmental interactions.
"""

from .impact_calculator import EnvironmentalImpactCalculator
from .movement_effects import MovementEffects
from .combat_modifiers import CombatModifiers
from .spell_effects import SpellEffects
from .creature_behavior import CreatureBehavior
from .terrain_effects import TerrainEffects
from .visibility_system import VisibilitySystem

__all__ = [
    "EnvironmentalImpactCalculator",
    "MovementEffects",
    "CombatModifiers",
    "SpellEffects",
    "CreatureBehavior",
    "TerrainEffects",
    "VisibilitySystem"
]