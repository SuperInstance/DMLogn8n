"""
Core Skill Class with progression tracking for DMlogn8n

This module defines the fundamental Skill class and related enums that form
the foundation of the progressive skill development system.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


class SkillCategory(Enum):
    """Categories of skills in D&D 5e system"""
    COMBAT = "Combat"
    SOCIAL = "Social"
    EXPLORATION = "Exploration"
    MAGIC = "Magic"
    STRATEGIC = "Strategic"


class MasteryLevel(Enum):
    """Mastery levels with increasing proficiency"""
    NOVICE = auto()      # 0-25 XP: Basic understanding
    APPRENTICE = auto()  # 25-100 XP: Can use reliably
    JOURNEYMAN = auto()  # 100-400 XP: Skilled practitioner
    EXPERT = auto()      # 400-1600 XP: Master level
    MASTER = auto()      # 1600+ XP: True mastery

    @property
    def xp_threshold(self) -> int:
        """XP required to reach this level"""
        thresholds = {
            MasteryLevel.NOVICE: 0,
            MasteryLevel.APPRENTICE: 25,
            MasteryLevel.JOURNEYMAN: 100,
            MasteryLevel.EXPERT: 400,
            MasteryLevel.MASTER: 1600
        }
        return thresholds[self]

    @property
    def multiplier(self) -> float:
        """XP multiplier for this mastery level"""
        multipliers = {
            MasteryLevel.NOVICE: 1.0,
            MasteryLevel.APPRENTICE: 1.1,
            MasteryLevel.JOURNEYMAN: 1.25,
            MasteryLevel.EXPERT: 1.5,
            MasteryLevel.MASTER: 2.0
        }
        return multipliers[self]

    @property
    def bonus_dice(self) -> int:
        """Bonus dice granted at this level"""
        bonuses = {
            MasteryLevel.NOVICE: 0,
            MasteryLevel.APPRENTICE: 0,
            MasteryLevel.JOURNEYMAN: 1,
            MasteryLevel.EXPERT: 2,
            MasteryLevel.MASTER: 3
        }
        return bonuses[self]


@dataclass
class SkillUsageRecord:
    """Records a single usage of a skill"""
    timestamp: datetime
    success: bool
    difficulty: float  # 0.0 to 1.0
    context: str
    xp_gained: int
    bonus_xp: int = 0
    critical_success: bool = False


@dataclass
class SkillPrerequisite:
    """Represents a prerequisite for unlocking or advancing a skill"""
    skill_name: str
    required_level: MasteryLevel
    required_xp: Optional[int] = None


@dataclass
class SynergyBonus:
    """Represents a synergy bonus between skills"""
    skill_name: str
    bonus_type: str  # 'xp', 'success_chance', 'critical_chance'
    bonus_value: float
    description: str


@dataclass
class SpecialAbility:
    """Special ability unlocked at certain mastery levels"""
    name: str
    description: str
    required_level: MasteryLevel
    effect_type: str  # 'passive', 'active', 'triggered'
    effect_value: Any
    cooldown: Optional[int] = None  # in rounds or uses


class Skill:
    """
    Core Skill class with comprehensive progression tracking

    This class manages all aspects of skill development including:
    - Experience tracking and calculation
    - Mastery level progression
    - Usage history and performance analytics
    - Synergy bonuses and special abilities
    - Integration with D&D 5e mechanics
    """

    def __init__(
        self,
        name: str,
        category: SkillCategory,
        description: str,
        base_difficulty: float = 0.5,
        dnd_skill: Optional[str] = None,
        prerequisites: Optional[List[SkillPrerequisite]] = None,
        synergies: Optional[List[SynergyBonus]] = None,
        special_abilities: Optional[List[SpecialAbility]] = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.base_difficulty = base_difficulty
        self.dnd_skill = dnd_skill  # D&D 5e skill name if applicable

        # Progression tracking
        self.total_xp = 0
        self.current_level = MasteryLevel.NOVICE
        self.usage_history: List[SkillUsageRecord] = []
        self.last_used: Optional[datetime] = None

        # Configuration
        self.prerequisites = prerequisites or []
        self.synergies = synergies or []
        self.special_abilities = special_abilities or []
        self.unlocked_abilities: Set[str] = set()

        # Performance metrics
        self.total_uses = 0
        self.successful_uses = 0
        self.critical_successes = 0
        self.average_difficulty = 0.0

        # State tracking
        self.is_active = True
        self.cooldown_remaining = 0
        self.temporary_bonus = 0.0
        self.temporary_bonus_expiry: Optional[datetime] = None

    @property
    def current_xp_for_level(self) -> int:
        """XP earned at current mastery level"""
        return max(0, self.total_xp - self.current_level.xp_threshold)

    @property
    def xp_to_next_level(self) -> int:
        """XP needed to reach next mastery level"""
        if self.current_level == MasteryLevel.MASTER:
            return 0

        # Find next level's threshold
        levels = list(MasteryLevel)
        current_index = levels.index(self.current_level)
        next_level = levels[current_index + 1]
        return next_level.xp_threshold - self.total_xp

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_uses == 0:
            return 0.0
        return (self.successful_uses / self.total_uses) * 100.0

    @property
    def critical_success_rate(self) -> float:
        """Calculate critical success rate"""
        if self.total_uses == 0:
            return 0.0
        return (self.critical_successes / self.total_uses) * 100.0

    @property
    def effective_level(self) -> int:
        """Calculate effective level including bonuses"""
        base_level = list(MasteryLevel).index(self.current_level) + 1
        return base_level + self.current_level.bonus_dice

    def add_experience(self, xp: int, bonus_xp: int = 0, context: str = "") -> bool:
        """
        Add experience to this skill

        Args:
            xp: Base experience gained
            bonus_xp: Bonus experience from multipliers
            context: Description of how XP was gained

        Returns:
            bool: True if mastery level increased
        """
        old_level = self.current_level
        total_xp_gained = xp + bonus_xp
        self.total_xp += total_xp_gained

        # Check for mastery level advancement
        new_level = self._calculate_mastery_level()
        level_up = new_level != old_level

        if level_up:
            self.current_level = new_level
            self._unlock_level_abilities()

        # Update performance metrics
        self._update_performance_metrics()

        return level_up

    def record_usage(
        self,
        success: bool,
        difficulty: float,
        context: str,
        xp_gained: int,
        critical_success: bool = False
    ) -> bool:
        """
        Record a usage of this skill

        Args:
            success: Whether the skill use was successful
            difficulty: Difficulty of the skill check (0.0 to 1.0)
            context: Description of the usage context
            xp_gained: Experience gained from this usage
            critical_success: Whether this was a critical success

        Returns:
            bool: True if mastery level increased
        """
        # Create usage record
        record = SkillUsageRecord(
            timestamp=datetime.now(),
            success=success,
            difficulty=difficulty,
            context=context,
            xp_gained=xp_gained,
            critical_success=critical_success
        )

        self.usage_history.append(record)
        self.last_used = record.timestamp
        self.total_uses += 1

        if success:
            self.successful_uses += 1
        if critical_success:
            self.critical_successes += 1

        # Add experience
        bonus_xp = self._calculate_bonus_xp(xp_gained, success, critical_success)
        return self.add_experience(xp_gained, bonus_xp, context)

    def calculate_success_chance(
        self,
        difficulty: float,
        synergistic_skills: Optional[Dict[str, 'Skill']] = None
    ) -> float:
        """
        Calculate success chance for this skill check

        Args:
            difficulty: Difficulty of the skill check (0.0 to 1.0)
            synergistic_skills: Other skills that might provide bonuses

        Returns:
            float: Success chance (0.0 to 1.0)
        """
        base_chance = 0.5  # 50% base chance

        # Skill mastery bonus
        mastery_bonus = self.current_level.multiplier - 1.0
        base_chance += mastery_bonus * 0.3  # Max 30% from mastery

        # Experience-based bonus
        xp_bonus = min(0.2, self.total_xp / 2000.0)  # Max 20% from XP
        base_chance += xp_bonus

        # Difficulty adjustment
        base_chance -= (difficulty - 0.5) * 0.6  # Difficulty modifier

        # Synergy bonuses
        if synergistic_skills:
            for synergy in self.synergies:
                if synergy.skill_name in synergistic_skills:
                    ally_skill = synergistic_skills[synergy.skill_name]
                    synergy_value = synergy.bonus_value * (ally_skill.total_xp / 1000.0)
                    if synergy.bonus_type == 'success_chance':
                        base_chance += synergy_value

        # Temporary bonuses
        if self.temporary_bonus_expiry and datetime.now() < self.temporary_bonus_expiry:
            base_chance += self.temporary_bonus

        # Clamp to valid range
        return max(0.05, min(0.95, base_chance))

    def apply_temporary_bonus(
        self,
        bonus: float,
        duration_minutes: int = 10
    ) -> None:
        """Apply a temporary bonus to this skill"""
        self.temporary_bonus = bonus
        from datetime import timedelta
        self.temporary_bonus_expiry = datetime.now() + timedelta(minutes=duration_minutes)

    def get_active_abilities(self) -> List[SpecialAbility]:
        """Get all currently unlocked special abilities"""
        return [
            ability for ability in self.special_abilities
            if ability.name in self.unlocked_abilities
        ]

    def can_use_ability(self, ability_name: str) -> bool:
        """Check if a special ability can be used"""
        if self.cooldown_remaining > 0:
            return False

        for ability in self.get_active_abilities():
            if ability.name == ability_name:
                return True

        return False

    def use_ability(self, ability_name: str) -> bool:
        """
        Use a special ability

        Args:
            ability_name: Name of the ability to use

        Returns:
            bool: True if ability was used successfully
        """
        if not self.can_use_ability(ability_name):
            return False

        for ability in self.get_active_abilities():
            if ability.name == ability_name:
                if ability.cooldown:
                    self.cooldown_remaining = ability.cooldown
                return True

        return False

    def update_cooldown(self) -> None:
        """Update cooldown counters (call each round/turn)"""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # Check for expired temporary bonuses
        if self.temporary_bonus_expiry and datetime.now() >= self.temporary_bonus_expiry:
            self.temporary_bonus = 0.0
            self.temporary_bonus_expiry = None

    def get_synergy_bonuses(
        self,
        other_skills: Dict[str, 'Skill']
    ) -> Dict[str, float]:
        """Calculate synergy bonuses from other skills"""
        bonuses = {}

        for synergy in self.synergies:
            if synergy.skill_name in other_skills:
                ally_skill = other_skills[synergy.skill_name]
                bonus_value = synergy.bonus_value * (ally_skill.total_xp / 1000.0)
                bonuses[synergy.bonus_type] = bonuses.get(synergy.bonus_type, 0) + bonus_value

        return bonuses

    def get_recent_performance(self, num_uses: int = 10) -> Dict[str, float]:
        """Get performance metrics from recent uses"""
        recent_uses = self.usage_history[-num_uses:] if self.usage_history else []

        if not recent_uses:
            return {
                'success_rate': 0.0,
                'average_difficulty': 0.0,
                'average_xp_per_use': 0.0,
                'critical_rate': 0.0
            }

        successes = sum(1 for use in recent_uses if use.success)
        criticals = sum(1 for use in recent_uses if use.critical_success)
        total_xp = sum(use.xp_gained + use.bonus_xp for use in recent_uses)
        avg_difficulty = sum(use.difficulty for use in recent_uses) / len(recent_uses)

        return {
            'success_rate': (successes / len(recent_uses)) * 100.0,
            'average_difficulty': avg_difficulty,
            'average_xp_per_use': total_xp / len(recent_uses),
            'critical_rate': (criticals / len(recent_uses)) * 100.0
        }

    def _calculate_mastery_level(self) -> MasteryLevel:
        """Calculate mastery level based on total XP"""
        levels = list(MasteryLevel)
        for level in reversed(levels):
            if self.total_xp >= level.xp_threshold:
                return level
        return MasteryLevel.NOVICE

    def _calculate_bonus_xp(
        self,
        base_xp: int,
        success: bool,
        critical_success: bool
    ) -> int:
        """Calculate bonus XP from various sources"""
        bonus = 0

        # Success bonus
        if success:
            bonus += int(base_xp * 0.2)

        # Critical success bonus
        if critical_success:
            bonus += int(base_xp * 0.5)

        # Mastery level multiplier
        bonus = int(bonus * self.current_level.multiplier)

        return bonus

    def _unlock_level_abilities(self) -> None:
        """Unlock abilities available at current mastery level"""
        for ability in self.special_abilities:
            if ability.required_level == self.current_level:
                self.unlocked_abilities.add(ability.name)

    def _update_performance_metrics(self) -> None:
        """Update internal performance metrics"""
        if self.usage_history:
            self.average_difficulty = sum(use.difficulty for use in self.usage_history) / len(self.usage_history)

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary for serialization"""
        return {
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'base_difficulty': self.base_difficulty,
            'dnd_skill': self.dnd_skill,
            'total_xp': self.total_xp,
            'current_level': self.current_level.name,
            'total_uses': self.total_uses,
            'successful_uses': self.successful_uses,
            'critical_successes': self.critical_successes,
            'success_rate': self.success_rate,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'unlocked_abilities': list(self.unlocked_abilities),
            'is_active': self.is_active,
            'synergies': [
                {
                    'skill_name': s.skill_name,
                    'bonus_type': s.bonus_type,
                    'bonus_value': s.bonus_value,
                    'description': s.description
                } for s in self.synergies
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        """Create skill from dictionary"""
        # Reconstruct enums
        category = SkillCategory(data['category'])
        current_level = MasteryLevel[data['current_level']]

        # Create skill instance
        skill = cls(
            name=data['name'],
            category=category,
            description=data['description'],
            base_difficulty=data['base_difficulty'],
            dnd_skill=data.get('dnd_skill')
        )

        # Restore state
        skill.total_xp = data['total_xp']
        skill.current_level = current_level
        skill.total_uses = data['total_uses']
        skill.successful_uses = data['successful_uses']
        skill.critical_successes = data['critical_successes']
        skill.unlocked_abilities = set(data['unlocked_abilities'])
        skill.is_active = data['is_active']

        if data['last_used']:
            from datetime import datetime
            skill.last_used = datetime.fromisoformat(data['last_used'])

        return skill

    def __str__(self) -> str:
        return f"{self.name} ({self.category.value}) - {self.current_level.name} - {self.total_xp} XP"

    def __repr__(self) -> str:
        return f"Skill(name='{self.name}', level={self.current_level.name}, xp={self.total_xp})"