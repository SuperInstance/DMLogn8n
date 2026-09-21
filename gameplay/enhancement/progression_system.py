#!/usr/bin/env python3
"""
Meaningful Character Progression System for DMLogn8n
Provides deep character development with visible growth and rewards
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class ProgressionType(Enum):
    EXPERIENCE = "experience"
    SKILL_BASED = "skill_based"
    SOCIAL = "social"
    ACHIEVEMENT = "achievement"
    MASTERY = "mastery"
    LEGACY = "legacy"

class AttributeType(Enum):
    STRENGTH = "strength"
    AGILITY = "agility"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"
    CONSTITUTION = "constitution"
    DEXTERITY = "dexterity"
    LUCK = "luck"

class ClassType(Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ROGUE = "rogue"
    CLERIC = "cleric"
    RANGER = "ranger"
    PALADIN = "paladin"
    NECROMANCER = "necromancer"
    BARD = "bard"
    MONK = "monk"
    DRUID = "druid"

class SpecializationType(Enum):
    COMBAT = "combat"
    MAGIC = "magic"
    STEALTH = "stealth"
    SUPPORT = "support"
    LEADERSHIP = "leadership"
    CRAFTING = "crafting"
    EXPLORATION = "exploration"
    DIPLOMACY = "diplomacy"

@dataclass
class Attribute:
    """Character attribute"""
    type: AttributeType
    base_value: int = 10
    current_value: int = 10
    bonuses: Dict[str, int] = field(default_factory=dict)  # equipment, buffs, etc.
    experience: int = 0
    level: int = 1

@dataclass
class StatProgression:
    """Stat progression data"""
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    stamina: int = 100
    max_stamina: int = 100
    attack_power: int = 10
    defense: int = 8
    magic_power: int = 8
    magic_resistance: int = 5
    critical_chance: float = 0.05
    critical_damage: float = 1.5
    dodge_chance: float = 0.10
    accuracy: float = 0.85
    movement_speed: float = 1.0

@dataclass
class LevelReward:
    """Reward given at specific level"""
    level: int
    attribute_points: int = 0
    skill_points: int = 0
    new_abilities: List[str] = field(default_factory=list)
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    unlock_features: List[str] = field(default_factory=list)

@dataclass
class Milestone:
    """Character progression milestone"""
    id: str
    name: str
    description: str
    requirement: Dict[str, Any]
    rewards: Dict[str, Any]
    completed: bool = False
    completed_at: Optional[float] = None

@dataclass
class CharacterClass:
    """Character class definition"""
    name: str
    description: str
    primary_attributes: List[AttributeType]
    secondary_attributes: List[AttributeType]
    starting_stats: StatProgression
    level_rewards: List[LevelReward]
    specializations_available: List[SpecializationType]
    class_abilities: List[str]

@dataclass
class Specialization:
    """Character specialization"""
    name: str
    description: str
    required_level: int
    attribute_requirements: Dict[AttributeType, int] = field(default_factory=dict)
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    unique_abilities: List[str] = field(default_factory=list)
    progression_modifiers: Dict[str, float] = field(default_factory=dict)

@dataclass
class CharacterProgress:
    """Complete character progression data"""
    character_id: str
    level: int = 1
    experience: int = 0
    total_experience: int = 0
    class_type: Optional[ClassType] = None
    specialization: Optional[Specialization] = None
    attributes: Dict[AttributeType, Attribute] = field(default_factory=dict)
    stats: StatProgression = field(default_factory=StatProgression)
    unspent_attribute_points: int = 0
    unspent_skill_points: int = 0
    milestones_completed: List[str] = field(default_factory=list)
    title: str = "Novice"
    renown: int = 0
    legacy_points: int = 0

class ProgressionSystem:
    """Main character progression system"""

    def __init__(self):
        self.character_progress: Dict[str, CharacterProgress] = {}
        self.classes: Dict[ClassType, CharacterClass] = {}
        self.specializations: Dict[str, Specialization] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.level_progression: Dict[int, LevelReward] = {}
        self.exponential_growth_factor = 1.15
        self.attribute_point_per_level = 2
        self.skill_point_per_level = 1
        self.max_level = 100
        self.analytics = ProgressionAnalytics()

        self._initialize_classes()
        self._initialize_specializations()
        self._initialize_milestones()
        self._initialize_level_progression()

    def _initialize_classes(self):
        """Initialize character classes"""
        classes = [
            CharacterClass(
                name="Warrior",
                description="Master of combat and physical prowess",
                primary_attributes=[AttributeType.STRENGTH, AttributeType.CONSTITUTION],
                secondary_attributes=[AttributeType.DEXTERITY],
                starting_stats=StatProgression(
                    health=150, max_health=150,
                    attack_power=15, defense=12,
                    critical_chance=0.08
                ),
                specializations_available=[SpecializationType.COMBAT, SpecializationType.LEADERSHIP],
                class_abilities=["power_strike", "defensive_stance", "battle_cry"]
            ),
            CharacterClass(
                name="Mage",
                description="Wielder of arcane powers",
                primary_attributes=[AttributeType.INTELLIGENCE, AttributeType.WISDOM],
                secondary_attributes=[AttributeType.CONSTITUTION],
                starting_stats=StatProgression(
                    mana=100, max_mana=100,
                    magic_power=20, magic_resistance=10,
                    critical_chance=0.06
                ),
                specializations_available=[SpecializationType.MAGIC, SpecializationType.SUPPORT],
                class_abilities=["fireball", "mana_shield", "arcane_missiles"]
            ),
            CharacterClass(
                name="Rogue",
                description="Master of stealth and precision",
                primary_attributes=[AttributeType.AGILITY, AttributeType.DEXTERITY],
                secondary_attributes=[AttributeType.LUCK],
                starting_stats=StatProgression(
                    attack_power=12, defense=6,
                    dodge_chance=0.20, critical_chance=0.15,
                    critical_damage=2.0
                ),
                specializations_available=[SpecializationType.STEALTH, SpecializationType.EXPLORATION],
                class_abilities=["stealth", "backstab", "evasion"]
            )
        ]

        for class_data in classes:
            self.classes[ClassType[class_data.name.upper()]] = class_data

    def _initialize_specializations(self):
        """Initialize specializations"""
        specializations = [
            Specialization(
                name="Berserker",
                description="Unleash inner rage in combat",
                required_level=20,
                attribute_requirements={AttributeType.STRENGTH: 30},
                stat_bonuses={"attack_power": 20, "critical_chance": 0.1},
                unique_abilities=["berserker_rage", "blood_fury"],
                progression_modifiers={"combat_xp": 1.2, "damage_taken": 1.1}
            ),
            Specialization(
                name="Elemental Master",
                description="Control the forces of nature",
                required_level=25,
                attribute_requirements={AttributeType.INTELLIGENCE: 40},
                stat_bonuses={"magic_power": 30, "mana": 50},
                unique_abilities=["elemental_mastery", "summon_elemental"],
                progression_modifiers={"magic_xp": 1.3, "spell_cost": 0.9}
            ),
            Specialization(
                name="Assassin",
                description="Silent and deadly killer",
                required_level=22,
                attribute_requirements={AttributeType.AGILITY: 35, AttributeType.DEXTERITY: 30},
                stat_bonuses={"critical_chance": 0.2, "critical_damage": 0.5},
                unique_abilities=["assassinate", "shadow_step"],
                progression_modifiers={"stealth_xp": 1.4, "poison_damage": 1.3}
            )
        ]

        for spec in specializations:
            self.specializations[spec.name] = spec

    def _initialize_milestones(self):
        """Initialize progression milestones"""
        milestones = [
            Milestone(
                id="first_victory",
                name="First Victory",
                description="Win your first combat encounter",
                requirement={"combat_wins": 1},
                rewards={"attribute_points": 2, "title": "Victor"}
            ),
            Milestone(
                id="social_butterfly",
                name="Social Butterfly",
                description="Make 10 friends",
                requirement={"friends_count": 10},
                rewards={"skill_points": 3, "social_xp": 100}
            ),
            Milestone(
                id="master_crafter",
                name="Master Crafter",
                description="Reach level 50 in any crafting skill",
                requirement={"crafting_skill_level": 50},
                rewards={"unique_recipe": "master_work", "crafting_bonus": 1.2}
            ),
            Milestone(
                id="legendary_hero",
                name="Legendary Hero",
                description="Reach level 50",
                requirement={"level": 50},
                rewards={"legendary_item": True, "title": "Legendary", "renown": 1000}
            )
        ]

        for milestone in milestones:
            self.milestones[milestone.id] = milestone

    def _initialize_level_progression(self):
        """Initialize level progression rewards"""
        # Common rewards every 5 levels
        for level in range(5, self.max_level + 1, 5):
            self.level_progression[level] = LevelReward(
                level=level,
                attribute_points=self.attribute_point_per_level * 2,
                skill_points=self.skill_point_per_level * 2,
                stat_bonuses={
                    "health": level * 10,
                    "attack_power": level * 2,
                    "defense": level * 1
                }
            )

        # Special milestone levels
        milestone_rewards = {
            10: LevelReward(level=10, attribute_points=5, new_abilities=["class_ability_1"]),
            20: LevelReward(level=20, attribute_points=8, new_abilities=["class_ability_2"], unlock_features=["specialization"]),
            30: LevelReward(level=30, attribute_points=10, new_abilities=["ultimate_ability"]),
            50: LevelReward(level=50, attribute_points=20, title="Hero", unlock_features=["legacy_system"]),
            75: LevelReward(level=75, attribute_points=30, title="Master"),
            100: LevelReward(level=100, attribute_points=50, title="Legend", legacy_points=10)
        }

        self.level_progression.update(milestone_rewards)

    def create_character(self, character_id: str, class_type: ClassType) -> CharacterProgress:
        """Create new character progression"""
        if character_id in self.character_progress:
            return self.character_progress[character_id]

        class_data = self.classes[class_type]

        # Initialize attributes
        attributes = {}
        for attr_type in AttributeType:
            base_value = 10
            if attr_type in class_data.primary_attributes:
                base_value = 15
            elif attr_type in class_data.secondary_attributes:
                base_value = 12

            attributes[attr_type] = Attribute(
                type=attr_type,
                base_value=base_value,
                current_value=base_value
            )

        # Create character progress
        progress = CharacterProgress(
            character_id=character_id,
            level=1,
            class_type=class_type,
            attributes=attributes,
            stats=class_data.starting_stats,
            unspent_attribute_points=5,  # Starting points
            unspent_skill_points=3
        )

        self.character_progress[character_id] = progress
        self.analytics.record_character_creation(character_id, class_type.value)

        return progress

    def add_experience(self, character_id: str, amount: int, source: str = "") -> Tuple[bool, List[str]]:
        """Add experience to character"""
        if character_id not in self.character_progress:
            return False, []

        progress = self.character_progress[character_id]
        progress.experience += amount
        progress.total_experience += amount

        # Apply specialization modifiers
        if progress.specialization:
            modifiers = progress.specialization.progression_modifiers
            if f"{source}_xp" in modifiers:
                amount = int(amount * modifiers[f"{source}_xp"])

        level_ups = []
        while self.can_level_up(character_id):
            new_level = self.level_up(character_id)
            level_ups.append(f"Reached level {new_level}!")

        # Check milestones
        milestone_completions = self.check_milestones(character_id)
        level_ups.extend(milestone_completions)

        self.analytics.record_experience_gain(character_id, amount, source)
        return True, level_ups

    def can_level_up(self, character_id: str) -> bool:
        """Check if character can level up"""
        if character_id not in self.character_progress:
            return False

        progress = self.character_progress[character_id]
        required_xp = self.calculate_experience_required(progress.level + 1)
        return progress.experience >= required_xp

    def level_up(self, character_id: str) -> int:
        """Level up character"""
        if character_id not in self.character_progress:
            return -1

        progress = self.character_progress[character_id]
        required_xp = self.calculate_experience_required(progress.level + 1)

        if progress.experience < required_xp:
            return progress.level

        # Deduct experience and increase level
        progress.experience -= required_xp
        progress.level += 1

        # Apply level rewards
        if progress.level in self.level_progression:
            reward = self.level_progression[progress.level]
            self.apply_level_reward(character_id, reward)

        # Apply default level rewards
        default_reward = LevelReward(
            level=progress.level,
            attribute_points=self.attribute_point_per_level,
            skill_points=self.skill_point_per_level,
            stat_bonuses={
                "health": 10,
                "max_health": 10,
                "mana": 5,
                "max_mana": 5,
                "attack_power": 2,
                "defense": 1
            }
        )
        self.apply_level_reward(character_id, default_reward)

        # Update title based on level
        progress.title = self.get_level_title(progress.level)

        self.analytics.record_level_up(character_id, progress.level)
        return progress.level

    def apply_level_reward(self, character_id: str, reward: LevelReward):
        """Apply level reward to character"""
        progress = self.character_progress[character_id]

        progress.unspent_attribute_points += reward.attribute_points
        progress.unspent_skill_points += reward.skill_points

        # Apply stat bonuses
        for stat, bonus in reward.stat_bonuses.items():
            if hasattr(progress.stats, stat):
                current_value = getattr(progress.stats, stat)
                setattr(progress.stats, stat, current_value + bonus)

        # Grant new abilities (would integrate with skill system)
        # Grant unlock features

    def calculate_experience_required(self, level: int) -> int:
        """Calculate experience required for level"""
        if level <= 1:
            return 0

        base_xp = 100
        return int(base_xp * math.pow(self.exponential_growth_factor, level - 2))

    def spend_attribute_point(self, character_id: str, attribute_type: AttributeType) -> Tuple[bool, str]:
        """Spend attribute point"""
        if character_id not in self.character_progress:
            return False, "Character not found"

        progress = self.character_progress[character_id]

        if progress.unspent_attribute_points <= 0:
            return False, "No attribute points available"

        if attribute_type not in progress.attributes:
            return False, "Invalid attribute type"

        # Increase attribute
        attribute = progress.attributes[attribute_type]
        attribute.current_value += 1
        attribute.level += 1

        progress.unspent_attribute_points -= 1

        # Apply attribute effects to stats
        self.apply_attribute_effects(character_id, attribute_type, 1)

        self.analytics.record_attribute_point_spend(character_id, attribute_type.value)

        return True, f"Increased {attribute_type.value} to {attribute.current_value}"

    def apply_attribute_effects(self, character_id: str, attribute_type: AttributeType, amount: int):
        """Apply attribute changes to character stats"""
        progress = self.character_progress[character_id]

        # Attribute to stat mappings
        attribute_effects = {
            AttributeType.STRENGTH: {"attack_power": 2, "health": 5},
            AttributeType.CONSTITUTION: {"health": 10, "max_health": 10, "defense": 1},
            AttributeType.AGILITY: {"dodge_chance": 0.02, "movement_speed": 0.05},
            AttributeType.DEXTERITY: {"accuracy": 0.02, "critical_chance": 0.01},
            AttributeType.INTELLIGENCE: {"magic_power": 3, "mana": 8, "max_mana": 8},
            AttributeType.WISDOM: {"magic_resistance": 2, "mana": 5, "max_mana": 5},
            AttributeType.CHARISMA: {"social_xp_bonus": 0.1},  # Would affect social XP
            AttributeType.LUCK: {"critical_chance": 0.01, "item_find_bonus": 0.05}
        }

        if attribute_type in attribute_effects:
            effects = attribute_effects[attribute_type]
            for stat, effect in effects.items():
                if hasattr(progress.stats, stat):
                    current_value = getattr(progress.stats, stat)
                    if isinstance(current_value, float):
                        setattr(progress.stats, stat, current_value + (effect * amount))
                    else:
                        setattr(progress.stats, stat, current_value + int(effect * amount))

    def choose_specialization(self, character_id: str, specialization_name: str) -> Tuple[bool, str]:
        """Choose character specialization"""
        if character_id not in self.character_progress:
            return False, "Character not found"

        if specialization_name not in self.specializations:
            return False, "Specialization not found"

        progress = self.character_progress[character_id]
        specialization = self.specializations[specialization_name]

        # Check requirements
        if progress.level < specialization.required_level:
            return False, f"Level {specialization.required_level} required"

        for attr_type, required_value in specialization.attribute_requirements.items():
            if attr_type not in progress.attributes:
                return False, f"Missing attribute: {attr_type}"

            if progress.attributes[attr_type].current_value < required_value:
                return False, f"{attr_type.value} {required_value} required"

        # Apply specialization
        progress.specialization = specialization

        # Apply stat bonuses
        for stat, bonus in specialization.stat_bonuses.items():
            if hasattr(progress.stats, stat):
                current_value = getattr(progress.stats, stat)
                if isinstance(current_value, float):
                    setattr(progress.stats, stat, current_value + bonus)
                else:
                    setattr(progress.stats, stat, current_value + int(bonus))

        self.analytics.record_specialization_choice(character_id, specialization_name)

        return True, f"Specialized in {specialization_name}"

    def check_milestones(self, character_id: str) -> List[str]:
        """Check and complete milestones"""
        if character_id not in self.character_progress:
            return []

        progress = self.character_progress[character_id]
        completions = []

        for milestone_id, milestone in self.milestones.items():
            if milestone.completed or milestone_id in progress.milestones_completed:
                continue

            if self.check_milestone_requirements(character_id, milestone.requirement):
                self.complete_milestone(character_id, milestone_id)
                completions.append(f"Milestone completed: {milestone.name}")

        return completions

    def check_milestone_requirements(self, character_id: str, requirements: Dict[str, Any]) -> bool:
        """Check if character meets milestone requirements"""
        progress = self.character_progress[character_id]

        for requirement, value in requirements.items():
            if requirement == "level":
                if progress.level < value:
                    return False
            elif requirement == "combat_wins":
                # Would check combat statistics
                pass
            elif requirement == "friends_count":
                # Would check social relationships
                pass
            elif requirement == "crafting_skill_level":
                # Would check crafting skills
                pass

        return True

    def complete_milestone(self, character_id: str, milestone_id: str):
        """Complete milestone and grant rewards"""
        progress = self.character_progress[character_id]
        milestone = self.milestones[milestone_id]

        milestone.completed = True
        milestone.completed_at = time.time()
        progress.milestones_completed.append(milestone_id)

        # Apply rewards
        for reward_type, reward_value in milestone.rewards.items():
            if reward_type == "attribute_points":
                progress.unspent_attribute_points += reward_value
            elif reward_type == "skill_points":
                progress.unspent_skill_points += reward_value
            elif reward_type == "title":
                progress.title = reward_value
            elif reward_type == "renown":
                progress.renown += reward_value

        self.analytics.record_milestone_completion(character_id, milestone_id)

    def get_level_title(self, level: int) -> str:
        """Get title based on level"""
        titles = {
            1: "Novice",
            5: "Apprentice",
            10: "Adept",
            15: "Expert",
            20: "Master",
            25: "Grandmaster",
            30: "Champion",
            35: "Hero",
            40: "Legend",
            45: "Mythic",
            50: "Eternal",
            60: "Transcendent",
            75: "Divine",
            100: "Immortal"
        }

        for level_threshold, title in sorted(titles.items(), reverse=True):
            if level >= level_threshold:
                return title

        return "Novice"

    def calculate_character_power(self, character_id: str) -> float:
        """Calculate total character power score"""
        if character_id not in self.character_progress:
            return 0.0

        progress = self.character_progress[character_id]

        # Base power from level
        level_power = progress.level * 100

        # Power from attributes
        attribute_power = sum(attr.current_value * 10 for attr in progress.attributes.values())

        # Power from stats
        stats = progress.stats
        stat_power = (
            stats.health * 0.5 +
            stats.attack_power * 2 +
            stats.defense * 1.5 +
            stats.magic_power * 2 +
            stats.magic_resistance * 1
        )

        # Power from equipment (placeholder)
        equipment_power = 0

        # Power from specialization
        specialization_power = 0
        if progress.specialization:
            specialization_power = progress.level * 50

        # Power from milestones
        milestone_power = len(progress.milestones_completed) * 25

        total_power = level_power + attribute_power + stat_power + equipment_power + specialization_power + milestone_power
        return total_power

    def get_progression_summary(self, character_id: str) -> Dict[str, Any]:
        """Get comprehensive progression summary"""
        if character_id not in self.character_progress:
            return {"error": "Character not found"}

        progress = self.character_progress[character_id]

        return {
            "character_id": character_id,
            "level": progress.level,
            "experience": progress.experience,
            "experience_to_next": self.calculate_experience_required(progress.level + 1),
            "total_experience": progress.total_experience,
            "class": progress.class_type.name if progress.class_type else None,
            "specialization": progress.specialization.name if progress.specialization else None,
            "title": progress.title,
            "attributes": {
                attr_type.value: {
                    "value": attr.current_value,
                    "level": attr.level,
                    "experience": attr.experience
                }
                for attr_type, attr in progress.attributes.items()
            },
            "stats": {
                "health": progress.stats.health,
                "max_health": progress.stats.max_health,
                "mana": progress.stats.mana,
                "max_mana": progress.stats.max_mana,
                "attack_power": progress.stats.attack_power,
                "defense": progress.stats.defense,
                "magic_power": progress.stats.magic_power,
                "critical_chance": progress.stats.critical_chance,
                "dodge_chance": progress.stats.dodge_chance
            },
            "unspent_points": {
                "attributes": progress.unspent_attribute_points,
                "skills": progress.unspent_skill_points
            },
            "milestones": {
                "completed": len(progress.milestones_completed),
                "total": len(self.milestones)
            },
            "character_power": self.calculate_character_power(character_id),
            "renown": progress.renown,
            "legacy_points": progress.legacy_points
        }

class ProgressionAnalytics:
    """Analytics for progression system balance"""

    def __init__(self):
        self.character_data = {}
        self.level_distribution = defaultdict(int)
        self.class_distribution = defaultdict(int)
        self.specialization_distribution = defaultdict(int)
        self.attribute_spending = defaultdict(lambda: defaultdict(int))
        self.progression_rates = defaultdict(list)
        self.milestone_completion = defaultdict(int)

    def record_character_creation(self, character_id: str, class_type: str):
        """Record new character creation"""
        self.character_data[character_id] = {
            "created_at": time.time(),
            "class": class_type,
            "level_history": [1],
            "attribute_spending": defaultdict(int)
        }
        self.class_distribution[class_type] += 1

    def record_experience_gain(self, character_id: str, amount: int, source: str):
        """Record experience gain"""
        if character_id in self.character_data:
            self.character_data[character_id]["total_xp_gained"] = \
                self.character_data[character_id].get("total_xp_gained", 0) + amount

    def record_level_up(self, character_id: str, level: int):
        """Record level up"""
        if character_id in self.character_data:
            self.character_data[character_id]["level_history"].append(level)
            self.level_distribution[level] += 1

            # Calculate progression rate
            created_at = self.character_data[character_id]["created_at"]
            time_to_level = time.time() - created_at
            self.progression_rates[level].append(time_to_level)

    def record_attribute_point_spend(self, character_id: str, attribute_type: str):
        """Record attribute point spending"""
        if character_id in self.character_data:
            self.character_data[character_id]["attribute_spending"][attribute_type] += 1
        self.attribute_spending[attribute_type] += 1

    def record_specialization_choice(self, character_id: str, specialization_name: str):
        """Record specialization choice"""
        self.specialization_distribution[specialization_name] += 1

    def record_milestone_completion(self, character_id: str, milestone_id: str):
        """Record milestone completion"""
        self.milestone_completion[milestone_id] += 1

    def get_progression_insights(self) -> Dict[str, Any]:
        """Get insights about progression balance"""
        total_characters = len(self.character_data)
        if total_characters == 0:
            return {"total_characters": 0}

        avg_level = sum(len(data.get("level_history", [])) for data in self.character_data.values()) / total_characters

        return {
            "total_characters": total_characters,
            "average_level": avg_level,
            "class_popularity": dict(self.class_distribution),
            "most_popular_attributes": max(self.attribute_spending.items(), key=lambda x: x[1]) if self.attribute_spending else None,
            "average_time_to_level": {
                level: sum(times) / len(times) if times else 0
                for level, times in self.progression_rates.items()
            }[:10]  # First 10 levels
        }

# Utility functions for progression balance
def calculate_optimal_progression_curve(target_level: int, target_time_hours: float) -> Dict[int, int]:
    """Calculate optimal XP curve for target progression speed"""
    total_hours = target_time_hours
    levels = list(range(1, target_level + 1))

    # Exponential curve with slower progression at higher levels
    xp_per_level = {}
    remaining_percentage = 1.0

    for level in levels[1:]:  # Skip level 1
        if level == target_level:
            xp_per_level[level] = int(1000 * remaining_percentage)
        else:
            # Higher levels require more percentage of total XP
            level_percentage = (level / target_level) ** 1.5
            curve_percentage = level_percentage / sum((i / target_level) ** 1.5 for i in range(1, target_level + 1))
            xp = int(1000 * curve_percentage)
            xp_per_level[level] = xp
            remaining_percentage -= curve_percentage / 1000

    return xp_per_level

def analyze_attribute_balance(character_data: Dict) -> Dict[str, Any]:
    """Analyze attribute distribution for balance"""
    if not character_data:
        return {}

    attribute_totals = defaultdict(int)
    character_count = len(character_data)

    for data in character_data.values():
        for attr, points in data.get("attribute_spending", {}).items():
            attribute_totals[attr] += points

    attribute_averages = {attr: total / character_count for attr, total in attribute_totals.items()}
    most_popular = max(attribute_averages.items(), key=lambda x: x[1]) if attribute_averages else None
    least_popular = min(attribute_averages.items(), key=lambda x: x[1]) if attribute_averages else None

    return {
        "attribute_averages": attribute_averages,
        "most_popular": most_popular,
        "least_popular": least_popular,
        "balance_ratio": least_popular[1] / most_popular[1] if most_popular and most_popular[1] > 0 else 0
    }

# Export main classes
__all__ = [
    'ProgressionSystem',
    'CharacterProgress',
    'CharacterClass',
    'Specialization',
    'Milestone',
    'ProgressionAnalytics',
    'calculate_optimal_progression_curve',
    'analyze_attribute_balance'
]