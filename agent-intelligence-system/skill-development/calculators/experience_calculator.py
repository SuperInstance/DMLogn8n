"""
Experience Calculator with multipliers for DMlogn8n

This module handles complex experience calculations with various multipliers,
bonuses, and special conditions to make skill progression engaging and balanced.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, time
import math

from ..core.skill import Skill, SkillCategory, MasteryLevel


class XPModifierType(Enum):
    """Types of XP modifiers"""
    BASE_MULTIPLIER = auto()
    SUCCESS_BONUS = auto()
    CRITICAL_BONUS = auto()
    DIFFICULTY_BONUS = auto()
    STREAK_BONUS = auto()
    FIRST_TIME_BONUS = auto()
    CATEGORY_BONUS = auto()
    MASTERY_BONUS = auto()
    TIME_BONUS = auto()
    SYNERGY_BONUS = auto()
    SITUATIONAL_BONUS = auto()


@dataclass
class XPModifier:
    """Represents a single XP modifier"""
    name: str
    type: XPModifierType
    value: float  # Multiplier or flat bonus
    description: str
    is_multiplier: bool = True
    condition: Optional[str] = None  # Condition for applying this modifier
    expires_at: Optional[datetime] = None


@dataclass
class XPContext:
    """Context information for XP calculation"""
    base_difficulty: float = 0.5
    actual_difficulty: float = 0.5
    is_first_use: bool = False
    is_critical_success: bool = False
    time_of_day: Optional[time] = None
    environment: Optional[str] = None
    related_skills: List[str] = field(default_factory=list)
    party_size: int = 1
    enemy_level: Optional[int] = None
    is_combat: bool = False
    is_social: bool = False
    is_exploration: bool = False
    weather_conditions: Optional[str] = None
    equipment_bonus: float = 0.0
    status_effects: List[str] = field(default_factory=list)


class ExperienceCalculator:
    """
    Advanced experience calculation system with multiple multipliers

    This class implements a sophisticated experience calculation system that
    considers various factors to create engaging and balanced progression.
    """

    def __init__(self):
        self.base_xp_table = self._create_base_xp_table()
        self.modifiers: Dict[str, XPModifier] = {}
        self.streak_tracker: Dict[str, int] = {}
        self.daily_usage: Dict[str, int] = {}
        self.weekly_usage: Dict[str, int] = {}
        self.last_reset_date = datetime.now().date()

        # Initialize default modifiers
        self._initialize_default_modifiers()

    def calculate_experience(
        self,
        skill: Skill,
        success: bool,
        context: XPContext,
        custom_modifiers: Optional[List[XPModifier]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate experience gained from skill usage

        Args:
            skill: The skill being used
            success: Whether the skill use was successful
            context: Context information for the calculation
            custom_modifiers: Additional modifiers to apply

        Returns:
            Tuple of (total_xp, calculation_breakdown)
        """
        # Reset daily/weekly counters if needed
        self._check_and_reset_counters()

        # Track usage
        self._track_usage(skill.name)

        # Start with base XP
        base_xp = self._get_base_xp(skill, context, success)
        total_xp = base_xp

        # Apply all modifiers
        breakdown = {
            'base_xp': base_xp,
            'modifiers': {},
            'total_xp': total_xp
        }

        # Get applicable modifiers
        applicable_modifiers = self._get_applicable_modifiers(
            skill, success, context, custom_modifiers
        )

        # Apply multipliers first
        multiplier_total = 1.0
        for modifier in applicable_modifiers:
            if modifier.is_multiplier:
                multiplier_total *= modifier.value
                breakdown['modifiers'][modifier.name] = f"* {modifier.value:.2f}"

        total_xp = int(base_xp * multiplier_total)

        # Apply flat bonuses
        flat_bonus_total = 0
        for modifier in applicable_modifiers:
            if not modifier.is_multiplier:
                flat_bonus_total += int(modifier.value)
                breakdown['modifiers'][modifier.name] = f"+ {int(modifier.value)}"

        total_xp += flat_bonus_total

        # Apply minimum and maximum caps
        min_xp = 1 if success else 0
        max_xp = self._calculate_max_xp(skill, context)
        total_xp = max(min_xp, min(max_xp, total_xp))

        breakdown['total_xp'] = total_xp
        breakdown['final_multiplier'] = multiplier_total
        breakdown['flat_bonus'] = flat_bonus_total
        breakdown['capped'] = total_xp != int(base_xp * multiplier_total + flat_bonus_total)

        return total_xp, breakdown

    def add_modifier(self, modifier: XPModifier) -> None:
        """Add a new XP modifier"""
        self.modifiers[modifier.name] = modifier

    def remove_modifier(self, modifier_name: str) -> bool:
        """Remove an XP modifier"""
        if modifier_name in self.modifiers:
            del self.modifiers[modifier_name]
            return True
        return False

    def get_active_modifiers(self) -> List[XPModifier]:
        """Get all currently active modifiers"""
        now = datetime.now()
        return [
            modifier for modifier in self.modifiers.values()
            if modifier.expires_at is None or modifier.expires_at > now
        ]

    def get_skill_streak(self, skill_name: str) -> int:
        """Get current success streak for a skill"""
        return self.streak_tracker.get(skill_name, 0)

    def get_daily_usage_count(self, skill_name: str) -> int:
        """Get daily usage count for a skill"""
        return self.daily_usage.get(skill_name, 0)

    def get_weekly_usage_count(self, skill_name: str) -> int:
        """Get weekly usage count for a skill"""
        return self.weekly_usage.get(skill_name, 0)

    def _create_base_xp_table(self) -> Dict[Tuple[bool, float], int]:
        """Create base XP table based on success and difficulty"""
        table = {}

        # Success cases
        for difficulty in [0.1, 0.3, 0.5, 0.7, 0.9]:
            base_xp = int(10 + (difficulty * 40))  # 10-50 XP base
            table[(True, difficulty)] = base_xp

        # Failure cases (reduced XP)
        for difficulty in [0.1, 0.3, 0.5, 0.7, 0.9]:
            base_xp = int(2 + (difficulty * 8))  # 2-10 XP on failure
            table[(False, difficulty)] = base_xp

        return table

    def _initialize_default_modifiers(self) -> None:
        """Initialize default XP modifiers"""
        # Success modifiers
        self.add_modifier(XPModifier(
            name="Success Bonus",
            type=XPModifierType.SUCCESS_BONUS,
            value=1.5,
            description="50% bonus for successful skill use",
            is_multiplier=True,
            condition="success == True"
        ))

        # Critical success modifier
        self.add_modifier(XPModifier(
            name="Critical Success",
            type=XPModifierType.CRITICAL_BONUS,
            value=2.0,
            description="Double XP for critical successes",
            is_multiplier=True,
            condition="critical_success == True"
        ))

        # First time use bonus
        self.add_modifier(XPModifier(
            name="First Discovery",
            type=XPModifierType.FIRST_TIME_BONUS,
            value=20,
            description="Bonus XP for first time using a skill",
            is_multiplier=False,
            condition="first_use == True"
        ))

        # Streak bonuses
        self.add_modifier(XPModifier(
            name="Hot Streak 3",
            type=XPModifierType.STREAK_BONUS,
            value=1.2,
            description="20% bonus for 3+ consecutive successes",
            is_multiplier=True,
            condition="streak >= 3"
        ))

        self.add_modifier(XPModifier(
            name="Hot Streak 5",
            type=XPModifierType.STREAK_BONUS,
            value=1.5,
            description="50% bonus for 5+ consecutive successes",
            is_multiplier=True,
            condition="streak >= 5"
        ))

        self.add_modifier(XPModifier(
            name="Hot Streak 10",
            type=XPModifierType.STREAK_BONUS,
            value=2.0,
            description="Double XP for 10+ consecutive successes",
            is_multiplier=True,
            condition="streak >= 10"
        ))

        # Mastery bonuses
        self.add_modifier(XPModifier(
            name="Apprentice Bonus",
            type=XPModifierType.MASTERY_BONUS,
            value=1.1,
            description="10% bonus at Apprentice level",
            is_multiplier=True,
            condition="level == APPRENTICE"
        ))

        self.add_modifier(XPModifier(
            name="Journeyman Bonus",
            type=XPModifierType.MASTERY_BONUS,
            value=1.25,
            description="25% bonus at Journeyman level",
            is_multiplier=True,
            condition="level == JOURNEYMAN"
        ))

        self.add_modifier(XPModifier(
            name="Expert Bonus",
            type=XPModifierType.MASTERY_BONUS,
            value=1.5,
            description="50% bonus at Expert level",
            is_multiplier=True,
            condition="level == EXPERT"
        ))

        self.add_modifier(XPModifier(
            name="Master Bonus",
            type=XPModifierType.MASTERY_BONUS,
            value=2.0,
            description="Double XP at Master level",
            is_multiplier=True,
            condition="level == MASTER"
        ))

        # Time-based modifiers
        self.add_modifier(XPModifier(
            name="Night Owl",
            type=XPModifierType.TIME_BONUS,
            value=1.1,
            description="10% bonus for late night skill use",
            is_multiplier=True,
            condition="time >= 22:00 or time <= 04:00"
        ))

        self.add_modifier(XPModifier(
            name="Early Bird",
            type=XPModifierType.TIME_BONUS,
            value=1.1,
            description="10% bonus for early morning skill use",
            is_multiplier=True,
            condition="time >= 05:00 and time <= 07:00"
        ))

        # Category-specific bonuses
        self.add_modifier(XPModifier(
            name="Combat Training",
            type=XPModifierType.CATEGORY_BONUS,
            value=1.2,
            description="20% bonus for combat skills in actual combat",
            is_multiplier=True,
            condition="category == COMBAT and is_combat == True"
        ))

        self.add_modifier(XPModifier(
            name="Social Butterfly",
            type=XPModifierType.CATEGORY_BONUS,
            value=1.3,
            description="30% bonus for social skills with NPCs",
            is_multiplier=True,
            condition="category == SOCIAL and is_social == True"
        ))

        self.add_modifier(XPModifier(
            name="Explorer's Spirit",
            type=XPModifierType.CATEGORY_BONUS,
            value=1.25,
            description="25% bonus for exploration skills in new areas",
            is_multiplier=True,
            condition="category == EXPLORATION and is_exploration == True"
        ))

        # Difficulty bonuses
        self.add_modifier(XPModifier(
            name="Underdog",
            type=XPModifierType.DIFFICULTY_BONUS,
            value=1.5,
            description="50% bonus when succeeding against high difficulty",
            is_multiplier=True,
            condition="success == True and difficulty >= 0.8"
        ))

        self.add_modifier(XPModifier(
            name="Learning from Failure",
            type=XPModifierType.DIFFICULTY_BONUS,
            value=1.3,
            description="30% bonus when failing at high difficulty (still learning)",
            is_multiplier=True,
            condition="success == False and difficulty >= 0.7"
        ))

    def _get_base_xp(self, skill: Skill, context: XPContext, success: bool) -> int:
        """Get base XP from lookup table"""
        # Round difficulty to nearest table value
        difficulty_rounded = round(context.actual_difficulty * 10) / 10
        difficulty_rounded = max(0.1, min(0.9, difficulty_rounded))

        return self.base_xp_table.get((success, difficulty_rounded), 10)

    def _get_applicable_modifiers(
        self,
        skill: Skill,
        success: bool,
        context: XPContext,
        custom_modifiers: Optional[List[XPModifier]]
    ) -> List[XPModifier]:
        """Get all modifiers that apply to this situation"""
        applicable = []

        # Check default modifiers
        for modifier in self.get_active_modifiers():
            if self._check_modifier_condition(modifier, skill, success, context):
                applicable.append(modifier)

        # Add custom modifiers
        if custom_modifiers:
            applicable.extend(custom_modifiers)

        return applicable

    def _check_modifier_condition(
        self,
        modifier: XPModifier,
        skill: Skill,
        success: bool,
        context: XPContext
    ) -> bool:
        """Check if a modifier's condition is met"""
        if not modifier.condition:
            return True

        # Parse simple conditions
        condition = modifier.condition.lower()

        # Success conditions
        if "success == true" in condition and not success:
            return False
        if "success == false" in condition and success:
            return False

        # Critical success conditions
        if "critical_success == true" in condition and not context.is_critical_success:
            return False

        # First use conditions
        if "first_use == true" in condition and not context.is_first_use:
            return False

        # Streak conditions
        if "streak >=" in condition:
            try:
                required_streak = int(condition.split("streak >=")[1].strip())
                current_streak = self.get_skill_streak(skill.name)
                if current_streak < required_streak:
                    return False
            except (ValueError, IndexError):
                pass

        # Level conditions
        if "level ==" in condition:
            try:
                level_name = condition.split("level ==")[1].strip()
                required_level = MasteryLevel[level_name]
                if skill.current_level != required_level:
                    return False
            except (ValueError, KeyError):
                pass

        # Category conditions
        if "category ==" in condition:
            try:
                category_name = condition.split("category ==")[1].strip()
                required_category = SkillCategory[category_name]
                if skill.category != required_category:
                    return False
            except (ValueError, KeyError):
                pass

        # Time conditions
        if context.time_of_day and "time >=" in condition:
            try:
                time_str = condition.split("time >=")[1].strip()
                required_time = time.fromisoformat(time_str)
                if context.time_of_day < required_time:
                    return False
            except ValueError:
                pass

        # Context conditions
        if "is_combat == true" in condition and not context.is_combat:
            return False
        if "is_social == true" in condition and not context.is_social:
            return False
        if "is_exploration == true" in condition and not context.is_exploration:
            return False

        return True

    def _track_usage(self, skill_name: str) -> None:
        """Track skill usage for streak calculation"""
        # Update daily usage
        self.daily_usage[skill_name] = self.daily_usage.get(skill_name, 0) + 1
        self.weekly_usage[skill_name] = self.weekly_usage.get(skill_name, 0) + 1

    def _check_and_reset_counters(self) -> None:
        """Reset daily/weekly counters if needed"""
        today = datetime.now().date()

        # Reset daily counter if it's a new day
        if today > self.last_reset_date:
            self.daily_usage.clear()
            self.last_reset_date = today

        # Reset weekly counter if it's a new week (Monday)
        if today.weekday() == 0 and today > self.last_reset_date:
            self.weekly_usage.clear()

    def _calculate_max_xp(self, skill: Skill, context: XPContext) -> int:
        """Calculate maximum XP cap for this situation"""
        base_cap = 100  # Base cap

        # Adjust cap based on mastery level
        level_multiplier = skill.current_level.multiplier
        adjusted_cap = int(base_cap * level_multiplier)

        # Adjust cap based on difficulty
        difficulty_multiplier = 1.0 + (context.actual_difficulty * 0.5)
        adjusted_cap = int(adjusted_cap * difficulty_multiplier)

        # Special situation bonuses
        if context.is_critical_success:
            adjusted_cap = int(adjusted_cap * 1.5)

        return adjusted_cap

    def update_streak(self, skill_name: str, success: bool) -> None:
        """Update success streak for a skill"""
        if success:
            self.streak_tracker[skill_name] = self.streak_tracker.get(skill_name, 0) + 1
        else:
            self.streak_tracker[skill_name] = 0

    def get_calculation_summary(self) -> Dict[str, Any]:
        """Get summary of calculation system state"""
        return {
            'active_modifiers': len(self.get_active_modifiers()),
            'total_modifiers': len(self.modifiers),
            'skills_with_streaks': len(self.streak_tracker),
            'daily_active_skills': len(self.daily_usage),
            'weekly_active_skills': len(self.weekly_usage),
            'last_reset': self.last_reset_date.isoformat()
        }