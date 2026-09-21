"""
Character Profile definition
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class CharacterProfile:
    """Character profile containing all essential information"""
    name: str
    character_class: str
    race: str
    level: int = 1
    background: str = ""
    # Core attributes (D&D style)
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Background traits
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""
    personality_traits: str = ""