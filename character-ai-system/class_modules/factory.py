"""
Class AI Factory
Creates appropriate class-specific AI modules based on character class
"""

from typing import Type, Dict, List

from .base_class_ai import BaseClassAI
from .fighter_ai import FighterAI
from .rogue_ai import RogueAI
from .wizard_ai import WizardAI
from .cleric_ai import ClericAI
from .barbarian_ai import BarbarianAI
from .bard_ai import BardAI
from .druid_ai import DruidAI
from .monk_ai import MonkAI
from .paladin_ai import PaladinAI
from .ranger_ai import RangerAI
from .sorcerer_ai import SorcererAI
from .warlock_ai import WarlockAI

from character_profile import CharacterProfile


class ClassAIFactory:
    """Factory for creating class-specific AI modules"""

    _class_ai_map: Dict[str, Type[BaseClassAI]] = {
        "Fighter": FighterAI,
        "Rogue": RogueAI,
        "Wizard": WizardAI,
        "Cleric": ClericAI,
        "Barbarian": BarbarianAI,
        "Bard": BardAI,
        "Druid": DruidAI,
        "Monk": MonkAI,
        "Paladin": PaladinAI,
        "Ranger": RangerAI,
        "Sorcerer": SorcererAI,
        "Warlock": WarlockAI,
    }

    @classmethod
    def create_class_ai(cls, character_class: str, character_profile: CharacterProfile) -> BaseClassAI:
        """Create appropriate class AI module"""
        # Normalize class name
        normalized_class = character_class.strip().title()

        # Get appropriate AI class
        ai_class = cls._class_ai_map.get(normalized_class)

        if ai_class is None:
            # Default to Fighter AI if class not found
            print(f"Warning: Class '{character_class}' not found, using Fighter AI as default")
            ai_class = FighterAI

        # Create and return AI instance
        return ai_class(character_profile)

    @classmethod
    def get_supported_classes(cls) -> List[str]:
        """Get list of supported character classes"""
        return list(cls._class_ai_map.keys())

    @classmethod
    def register_class_ai(cls, character_class: str, ai_class: Type[BaseClassAI]) -> None:
        """Register a new class AI type"""
        cls._class_ai_map[character_class] = ai_class