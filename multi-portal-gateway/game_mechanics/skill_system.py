"""
Comprehensive Skill System for DMLogn8n
Implements skill progression with branching paths and specialization options
"""

import random
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

class SkillCategory(Enum):
    """Main skill categories"""
    COMBAT = "combat"
    MAGIC = "magic"
    STEALTH = "stealth"
    SOCIAL = "social"
    CRAFTING = "crafting"
    SURVIVAL = "survival"
    KNOWLEDGE = "knowledge"
    FAITH = "faith"

class SkillType(Enum):
    """Types of skills"""
    ACTIVE = "active"  # Requires activation
    PASSIVE = "passive"  # Always active
    TOGGLE = "toggle"  # Can be turned on/off
    REACTIVE = "reactive"  # Triggers under conditions
    CHANNELED = "channeled"  # Requires concentration

class MasteryLevel(Enum):
    """Skill mastery levels"""
    NOVICE = 1
    APPRENTICE = 2
    JOURNEYMAN = 3
    EXPERT = 4
    MASTER = 5
    GRANDMASTER = 6
    LEGENDARY = 7
    MYTHIC = 8

class SkillAttribute(Enum):
    """Primary attributes for skills"""
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"
    CONSTITUTION = "constitution"
    PERCEPTION = "perception"
    LUCK = "luck"

@dataclass
class SkillPrerequisite:
    """Skill prerequisite"""
    skill_id: str
    required_level: int
    optional: bool = False

@dataclass
class SkillEffect:
    """Individual skill effect"""
    effect_type: str
    value: float
    scaling: Optional[str] = None  # Attribute that scales this effect
    condition: Optional[str] = None  # Condition for effect to apply
    duration: Optional[int] = None  # Duration in rounds/seconds
    target: str = "self"  # Target of effect

@dataclass
class Skill:
    """Complete skill definition"""
    id: str
    name: str
    description: str
    category: SkillCategory
    skill_type: SkillType
    primary_attribute: SkillAttribute
    secondary_attributes: List[SkillAttribute]

    # Progression
    max_level: int = 100
    base_cost: int = 10
    cost_scaling: float = 1.15
    experience_multiplier: float = 1.0

    # Requirements and unlocks
    prerequisites: List[SkillPrerequisite] = field(default_factory=list)
    unlocks_skills: List[str] = field(default_factory=list)
    required_level: int = 1

    # Effects at different levels
    effects: Dict[int, List[SkillEffect]] = field(default_factory=dict)

    # Usage mechanics
    mana_cost: int = 0
    cooldown: int = 0
    cast_time: float = 1.0
    range: float = 1.0
    area_of_effect: float = 0.0

    # Special properties
    can_crit: bool = False
    can_miss: bool = True
    stacks: bool = False
    max_stacks: int = 1

    # Learning and mastery
    mastery_requirement: MasteryLevel = MasteryLevel.NOVICE
    hidden: bool = False
    requires_training: bool = False
    requires_equipment: Optional[str] = None

@dataclass
class SkillProgress:
    """Individual skill progress for a character"""
    skill_id: str
    current_level: int = 0
    experience: int = 0
    experience_to_next: int = 100
    total_experience: int = 0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    masteries: List[MasteryLevel] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)

    def add_experience(self, amount: int) -> bool:
        """Add experience and check for level up"""
        self.experience += amount
        self.total_experience += amount
        self.usage_count += 1
        self.last_used = datetime.now()

        leveled_up = False
        while self.experience >= self.experience_to_next and self.current_level < 100:
            self.experience -= self.experience_to_next
            self.current_level += 1
            self.experience_to_next = self._calculate_exp_to_next()
            leveled_up = True

        return leveled_up

    def _calculate_exp_to_next(self) -> int:
        """Calculate experience needed for next level"""
        return int(100 * (1.1 ** self.current_level))

@dataclass
class SkillSpecialization:
    """Skill specialization path"""
    id: str
    name: str
    description: str
    skill_id: str
    required_level: int
    effects: List[SkillEffect]
    unlocks_abilities: List[str] = field(default_factory=list)
    mutually_exclusive: List[str] = field(default_factory=list)

class SkillTree:
    """Skill tree structure for visualization and dependencies"""

    def __init__(self, name: str, category: SkillCategory):
        self.name = name
        self.category = category
        self.skills: Dict[str, Skill] = {}
        self.connections: Dict[str, List[str]] = {}  # skill_id -> [connected_skill_ids]
        self.tiers: Dict[int, List[str]] = {}  # tier -> [skill_ids]
        self.specializations: Dict[str, List[SkillSpecialization]] = {}

    def add_skill(self, skill: Skill, tier: int):
        """Add skill to tree at specific tier"""
        self.skills[skill.id] = skill
        if tier not in self.tiers:
            self.tiers[tier] = []
        self.tiers[tier].append(skill.id)

    def add_connection(self, from_skill: str, to_skill: str):
        """Add connection between skills"""
        if from_skill not in self.connections:
            self.connections[from_skill] = []
        self.connections[from_skill].append(to_skill)

    def add_specialization(self, skill_id: str, specialization: SkillSpecialization):
        """Add specialization to skill"""
        if skill_id not in self.specializations:
            self.specializations[skill_id] = []
        self.specializations[skill_id].append(specialization)

    def get_available_skills(self, known_skills: Dict[str, SkillProgress],
                            player_level: int) -> List[Skill]:
        """Get skills that can be learned"""
        available = []

        for skill_id, skill in self.skills.items():
            if skill_id in known_skills:
                continue

            if skill.required_level > player_level:
                continue

            # Check prerequisites
            can_learn = True
            for prereq in skill.prerequisites:
                if not prereq.optional:
                    if prereq.skill_id not in known_skills:
                        can_learn = False
                        break
                    elif known_skills[prereq.skill_id].current_level < prereq.required_level:
                        can_learn = False
                        break

            if can_learn:
                available.append(skill)

        return available

class CharacterSkills:
    """Character's skill collection and progress"""

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.skills: Dict[str, SkillProgress] = {}
        self.skill_points: int = 0
        self.total_skill_points_earned: int = 0
        self.mastered_skills: List[str] = []
        self.favorite_skills: List[str] = []
        self.skill_combinations: List[Dict[str, Any]] = []
        self.learning_bonus: float = 1.0

    def learn_skill(self, skill: Skill, spend_points: bool = True) -> bool:
        """Learn a new skill"""
        if skill.id in self.skills:
            return False

        if spend_points and self.skill_points <= 0:
            return False

        # Check prerequisites
        for prereq in skill.prerequisites:
            if not prereq.optional:
                if prereq.skill_id not in self.skills:
                    return False
                elif self.skills[prereq.skill_id].current_level < prereq.required_level:
                    return False

        # Learn skill
        self.skills[skill.id] = SkillProgress(skill_id=skill.id)

        if spend_points:
            self.skill_points -= 1

        return True

    def upgrade_skill(self, skill_id: str, levels: int = 1) -> bool:
        """Upgrade skill level"""
        if skill_id not in self.skills:
            return False

        progress = self.skills[skill_id]
        cost = self._calculate_upgrade_cost(skill_id, progress.current_level, levels)

        if self.skill_points < cost:
            return False

        progress.current_level += levels
        self.skill_points -= cost

        return True

    def _calculate_upgrade_cost(self, skill_id: str, current_level: int, levels: int) -> int:
        """Calculate cost to upgrade skill"""
        skill = self._get_skill_by_id(skill_id)
        if not skill:
            return 0

        total_cost = 0
        for i in range(levels):
            level = current_level + i + 1
            cost = int(skill.base_cost * (skill.cost_scaling ** (level - 1)))
            total_cost += cost

        return int(total_cost * self.learning_bonus)

    def _get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """Get skill definition by ID (would interface with skill registry)"""
        # This would interface with a global skill registry
        return None

    def add_skill_experience(self, skill_id: str, amount: int) -> bool:
        """Add experience to a skill"""
        if skill_id not in self.skills:
            return False

        amount = int(amount * self.learning_bonus)
        return self.skills[skill_id].add_experience(amount)

    def get_skill_level(self, skill_id: str) -> int:
        """Get current level of skill"""
        return self.skills.get(skill_id, SkillProgress(skill_id)).current_level

    def get_total_skill_level(self) -> int:
        """Get total sum of all skill levels"""
        return sum(progress.current_level for progress in self.skills.values())

    def get_mastered_skills(self) -> List[str]:
        """Get list of mastered skills (level 100)"""
        return [skill_id for skill_id, progress in self.skills.items()
                if progress.current_level >= 100]

    def get_specialized_skills(self) -> Dict[str, List[str]]:
        """Get skill specializations"""
        return {skill_id: progress.specializations
                for skill_id, progress in self.skills.items()
                if progress.specializations}

class SkillSystem:
    """Main skill system manager"""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.skill_trees: Dict[str, SkillTree] = {}
        self.specializations: Dict[str, SkillSpecialization] = {}
        self.skill_combinations: Dict[str, List[Dict[str, Any]]] = {}
        self.learning_rates: Dict[str, float] = {}

        self._initialize_skills()

    def _initialize_skills(self):
        """Initialize basic skill database"""
        # Combat skills
        self._register_combat_skills()

        # Magic skills
        self._register_magic_skills()

        # Stealth skills
        self._register_stealth_skills()

        # Social skills
        self._register_social_skills()

        # Crafting skills
        self._register_crafting_skills()

        # Survival skills
        self._register_survival_skills()

    def _register_combat_skills(self):
        """Register combat skills"""

        # Sword Mastery
        sword_mastery = Skill(
            id="sword_mastery",
            name="Sword Mastery",
            description="Increases effectiveness with swords and blades",
            category=SkillCategory.COMBAT,
            skill_type=SkillType.PASSIVE,
            primary_attribute=SkillAttribute.DEXTERITY,
            secondary_attributes=[SkillAttribute.STRENGTH],
            effects={
                1: [SkillEffect("weapon_damage", 5, "strength")],
                25: [SkillEffect("weapon_damage", 10, "strength"),
                     SkillEffect("attack_speed", 10, "dexterity")],
                50: [SkillEffect("weapon_damage", 20, "strength"),
                     SkillEffect("critical_chance", 5, "dexterity")],
                75: [SkillEffect("weapon_damage", 35, "strength"),
                     SkillEffect("critical_damage", 25, "strength"),
                     SkillEffect("attack_speed", 20, "dexterity")],
                100: [SkillEffect("weapon_damage", 50, "strength"),
                      SkillEffect("perfect_strike", 100)]
            }
        )
        self.skills[sword_mastery.id] = sword_mastery

        # Shield Wall
        shield_wall = Skill(
            id="shield_wall",
            name="Shield Wall",
            description="Defensive stance that reduces incoming damage",
            category=SkillCategory.COMBAT,
            skill_type=SkillType.TOGGLE,
            primary_attribute=SkillAttribute.CONSTITUTION,
            secondary_attributes=[SkillAttribute.STRENGTH],
            mana_cost=5,
            effects={
                1: [SkillEffect("damage_reduction", 15, "constitution")],
                25: [SkillEffect("damage_reduction", 25, "constitution"),
                     SkillEffect("stun_resistance", 20)],
                50: [SkillEffect("damage_reduction", 35, "constitution"),
                     SkillEffect("stun_resistance", 40),
                     SkillEffect("ally_protection", 10)],
                75: [SkillEffect("damage_reduction", 50, "constitution"),
                     SkillEffect("stun_resistance", 60),
                     SkillEffect("ally_protection", 20),
                     SkillEffect("counter_attack", 15, "strength")],
                100: [SkillEffect("damage_reduction", 75, "constitution"),
                      SkillEffect("immunity", "physical_damage")]
            }
        )
        self.skills[shield_wall.id] = shield_wall

        # Power Strike
        power_strike = Skill(
            id="power_strike",
            name="Power Strike",
            description="Devastating attack that deals massive damage",
            category=SkillCategory.COMBAT,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.STRENGTH,
            secondary_attributes=[SkillAttribute.DEXTERITY],
            mana_cost=20,
            cooldown=3,
            can_crit=True,
            effects={
                1: [SkillEffect("weapon_damage", 150, "strength")],
                25: [SkillEffect("weapon_damage", 200, "strength"),
                     SkillEffect("armor_penetration", 25)],
                50: [SkillEffect("weapon_damage", 275, "strength"),
                     SkillEffect("armor_penetration", 50),
                     SkillEffect("knockback", 100)],
                75: [SkillEffect("weapon_damage", 350, "strength"),
                     SkillEffect("armor_penetration", 75),
                     SkillEffect("knockback", 100),
                     SkillEffect("cleave", 50)],
                100: [SkillEffect("weapon_damage", 500, "strength"),
                      SkillEffect("instant_kill", 5)]
            }
        )
        self.skills[power_strike.id] = power_strike

    def _register_magic_skills(self):
        """Register magic skills"""

        # Fireball
        fireball = Skill(
            id="fireball",
            name="Fireball",
            description="Launches a ball of fire at enemies",
            category=SkillCategory.MAGIC,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.INTELLIGENCE,
            secondary_attributes=[SkillAttribute.WISDOM],
            mana_cost=30,
            cooldown=2,
            range=8.0,
            area_of_effect=2.0,
            can_crit=True,
            effects={
                1: [SkillEffect("fire_damage", 50, "intelligence")],
                25: [SkillEffect("fire_damage", 80, "intelligence"),
                     SkillEffect("burning", 20, "intelligence")],
                50: [SkillEffect("fire_damage", 120, "intelligence"),
                     SkillEffect("burning", 40, "intelligence"),
                     SkillEffect("explosion_radius", 1.0)],
                75: [SkillEffect("fire_damage", 180, "intelligence"),
                     SkillEffect("burning", 60, "intelligence"),
                     SkillEffect("explosion_radius", 2.0),
                     SkillEffect("chain_lightning", 20)],
                100: [SkillEffect("fire_damage", 300, "intelligence"),
                      SkillEffect("inferno", 100, "intelligence")]
            }
        )
        self.skills[fireball.id] = fireball

        # Meditation
        meditation = Skill(
            id="meditation",
            name="Meditation",
            description="Restores mana and clears negative effects",
            category=SkillCategory.MAGIC,
            skill_type=SkillType.CHANNELED,
            primary_attribute=SkillAttribute.WISDOM,
            secondary_attributes=[SkillAttribute.INTELLIGENCE],
            effects={
                1: [SkillEffect("mana_regen", 5, "wisdom")],
                25: [SkillEffect("mana_regen", 10, "wisdom"),
                     SkillEffect("health_regen", 3, "wisdom")],
                50: [SkillEffect("mana_regen", 20, "wisdom"),
                     SkillEffect("health_regen", 8, "wisdom"),
                     SkillEffect("clear_debuffs", 50)],
                75: [SkillEffect("mana_regen", 35, "wisdom"),
                     SkillEffect("health_regen", 15, "wisdom"),
                     SkillEffect("clear_debuffs", 100),
                     SkillEffect("mana_efficiency", 20)],
                100: [SkillEffect("mana_regen", 50, "wisdom"),
                      SkillEffect("health_regen", 25, "wisdom"),
                      SkillEffect("clear_debuffs", 100),
                      SkillEffect("transcendence", 100, "wisdom")]
            }
        )
        self.skills[meditation.id] = meditation

    def _register_stealth_skills(self):
        """Register stealth skills"""

        # Stealth
        stealth = Skill(
            id="stealth",
            name="Stealth",
            description="Become harder to detect and move silently",
            category=SkillCategory.STEALTH,
            skill_type=SkillType.TOGGLE,
            primary_attribute=SkillAttribute.DEXTERITY,
            secondary_attributes=[SkillAttribute.PERCEPTION],
            effects={
                1: [SkillEffect("stealth_level", 25, "dexterity")],
                25: [SkillEffect("stealth_level", 50, "dexterity"),
                     SkillEffect("movement_speed", 15, "dexterity")],
                50: [SkillEffect("stealth_level", 75, "dexterity"),
                     SkillEffect("movement_speed", 30, "dexterity"),
                     SkillEffect("first_strike_bonus", 25)],
                75: [SkillEffect("stealth_level", 100, "dexterity"),
                     SkillEffect("movement_speed", 50, "dexterity"),
                     SkillEffect("first_strike_bonus", 50),
                     SkillEffect("shadow_step", 20)],
                100: [SkillEffect("invisibility", 100, "dexterity")]
            }
        )
        self.skills[stealth.id] = stealth

        # Lockpicking
        lockpicking = Skill(
            id="lockpicking",
            name="Lockpicking",
            description="Open locked doors and containers",
            category=SkillCategory.STEALTH,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.DEXTERITY,
            secondary_attributes=[SkillAttribute.PERCEPTION],
            effects={
                1: [SkillEffect("lock_complexity", 1)],
                25: [SkillEffect("lock_complexity", 2),
                     SkillEffect("trap_disarm", 25)],
                50: [SkillEffect("lock_complexity", 3),
                     SkillEffect("trap_disarm", 50),
                     SkillEffect("speed", 50)],
                75: [SkillEffect("lock_complexity", 4),
                     SkillEffect("trap_disarm", 75),
                     SkillEffect("speed", 100),
                     SkillEffect("magical_locks", 25)],
                100: [SkillEffect("lock_complexity", 5),
                      SkillEffect("trap_disarm", 100),
                      SkillEffect("speed", 200),
                      SkillEffect("magical_locks", 100),
                      SkillEffect("instant_open", 25)]
            }
        )
        self.skills[lockpicking.id] = lockpicking

    def _register_social_skills(self):
        """Register social skills"""

        # Persuasion
        persuasion = Skill(
            id="persuasion",
            name="Persuasion",
            description="Convince others to see your point of view",
            category=SkillCategory.SOCIAL,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.CHARISMA,
            secondary_attributes=[SkillAttribute.INTELLIGENCE],
            effects={
                1: [SkillEffect("persuasion_chance", 15, "charisma")],
                25: [SkillEffect("persuasion_chance", 30, "charisma"),
                     SkillEffect("intimidation", 20, "charisma")],
                50: [SkillEffect("persuasion_chance", 50, "charisma"),
                     SkillEffect("intimidation", 40, "charisma"),
                     SkillEffect("bargaining", 25)],
                75: [SkillEffect("persuasion_chance", 75, "charisma"),
                     SkillEffect("intimidation", 60, "charisma"),
                     SkillEffect("bargaining", 50),
                     SkillEffect("leadership", 30)],
                100: [SkillEffect("persuasion_chance", 100, "charisma"),
                      SkillEffect("charisma_aura", 50, "charisma")]
            }
        )
        self.skills[persuasion.id] = persuasion

    def _register_crafting_skills(self):
        """Register crafting skills"""

        # Blacksmithing
        blacksmithing = Skill(
            id="blacksmithing",
            name="Blacksmithing",
            description="Craft weapons and armor from metal",
            category=SkillCategory.CRAFTING,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.STRENGTH,
            secondary_attributes=[SkillAttribute.INTELLIGENCE],
            effects={
                1: [SkillEffect("craft_tier", 1)],
                25: [SkillEffect("craft_tier", 2),
                     SkillEffect("quality_bonus", 10)],
                50: [SkillEffect("craft_tier", 3),
                     SkillEffect("quality_bonus", 25),
                     SkillEffect("rare_materials", 25)],
                75: [SkillEffect("craft_tier", 4),
                     SkillEffect("quality_bonus", 50),
                     SkillEffect("rare_materials", 50),
                     SkillEffect("masterwork", 20)],
                100: [SkillEffect("craft_tier", 5),
                      SkillEffect("quality_bonus", 100),
                      SkillEffect("rare_materials", 100),
                      SkillEffect("legendary_craft", 25)]
            }
        )
        self.skills[blacksmithing.id] = blacksmithing

    def _register_survival_skills(self):
        """Register survival skills"""

        # Foraging
        foraging = Skill(
            id="foraging",
            name="Foraging",
            description="Find food and resources in the wild",
            category=SkillCategory.SURVIVAL,
            skill_type=SkillType.ACTIVE,
            primary_attribute=SkillAttribute.PERCEPTION,
            secondary_attributes=[SkillAttribute.WISDOM],
            effects={
                1: [SkillEffect("find_food", 25, "perception")],
                25: [SkillEffect("find_food", 50, "perception"),
                     SkillEffect("find_herbs", 25, "wisdom")],
                50: [SkillEffect("find_food", 75, "perception"),
                     SkillEffect("find_herbs", 50, "wisdom"),
                     SkillEffect("rare_ingredients", 20)],
                75: [SkillEffect("find_food", 100, "perception"),
                     SkillEffect("find_herbs", 75, "wisdom"),
                     SkillEffect("rare_ingredients", 50),
                     SkillEffect("tracking", 30)],
                100: [SkillEffect("nature_communion", 100, "wisdom")]
            }
        )
        self.skills[foraging.id] = foraging

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        return self.skills.get(skill_id)

    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """Get all skills in a category"""
        return [skill for skill in self.skills.values() if skill.category == category]

    def get_skills_by_attribute(self, attribute: SkillAttribute) -> List[Skill]:
        """Get skills that use specific attribute"""
        return [skill for skill in self.skills.values()
                if skill.primary_attribute == attribute or attribute in skill.secondary_attributes]

    def calculate_skill_power(self, character_skills: CharacterSkills, skill_id: str) -> float:
        """Calculate effective power of a skill for a character"""
        if skill_id not in character_skills.skills:
            return 0.0

        skill = self.get_skill(skill_id)
        if not skill:
            return 0.0

        progress = character_skills.skills[skill_id]
        base_power = progress.current_level

        # Apply mastery bonuses
        if progress.current_level >= 100:
            base_power *= 2.0
        elif progress.current_level >= 75:
            base_power *= 1.5
        elif progress.current_level >= 50:
            base_power *= 1.25

        # Apply specialization bonuses
        for spec in progress.specializations:
            base_power *= 1.2

        return base_power

    def get_skill_recommendations(self, character_skills: CharacterSkills,
                                 player_class: str, playstyle: str) -> List[Skill]:
        """Get recommended skills for character"""
        recommendations = []

        # Define skill priorities by class and playstyle
        priorities = self._get_skill_priorities(player_class, playstyle)

        for skill_id, priority in priorities.items():
            skill = self.get_skill(skill_id)
            if skill and skill_id not in character_skills.skills:
                # Check if can learn
                can_learn = True
                for prereq in skill.prerequisites:
                    if not prereq.optional:
                        if prereq.skill_id not in character_skills.skills:
                            can_learn = False
                            break
                        elif character_skills.skills[prereq.skill_id].current_level < prereq.required_level:
                            can_learn = False
                            break

                if can_learn:
                    recommendations.append((skill, priority))

        # Sort by priority
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in recommendations]

    def _get_skill_priorities(self, player_class: str, playstyle: str) -> Dict[str, float]:
        """Get skill priorities based on class and playstyle"""
        priorities = {}

        if player_class == "warrior":
            if playstyle == "tank":
                priorities.update({
                    "shield_wall": 10,
                    "sword_mastery": 8,
                    "heavy_armor": 9,
                    "taunt": 10
                })
            elif playstyle == "damage":
                priorities.update({
                    "sword_mastery": 10,
                    "power_strike": 10,
                    "berserker_rage": 9,
                    "weapon_mastery": 8
                })
        elif player_class == "mage":
            if playstyle == "elemental":
                priorities.update({
                    "fireball": 10,
                    "ice_shard": 9,
                    "lightning_bolt": 9,
                    "elemental_mastery": 10
                })
            elif playstyle == "support":
                priorities.update({
                    "meditation": 10,
                    "healing_spells": 10,
                    "buff_spells": 9,
                    "mana_efficiency": 8
                })
        elif player_class == "rogue":
            priorities.update({
                "stealth": 10,
                "backstab": 10,
                "lockpicking": 8,
                "poison": 9
            })

        return priorities

    def check_skill_combination(self, character_skills: CharacterSkills) -> List[Dict[str, Any]]:
        """Check for skill combinations and synergies"""
        combinations = []

        # Define skill combinations
        combination_definitions = [
            {
                "name": "Spell Sword",
                "required_skills": ["sword_mastery", "basic_magic"],
                "bonus_effects": [
                    SkillEffect("magic_damage", 25, "intelligence"),
                    SkillEffect("weapon_damage", 25, "strength")
                ]
            },
            {
                "name": "Shadow Assassin",
                "required_skills": ["stealth", "backstab", "poison"],
                "bonus_effects": [
                    SkillEffect("stealth_damage", 50, "dexterity"),
                    SkillEffect("poison_efficiency", 50)
                ]
            },
            {
                "name": "Battle Mage",
                "required_skills": ["heavy_armor", "combat_magic"],
                "bonus_effects": [
                    SkillEffect("spell_casting_in_armor", 100),
                    SkillEffect("melee_spell_synergy", 30)
                ]
            }
        ]

        for combo in combination_definitions:
            if all(skill_id in character_skills.skills
                   for skill_id in combo["required_skills"]):
                # Calculate combination level based on skill levels
                min_level = min(character_skills.skills[skill_id].current_level
                              for skill_id in combo["required_skills"])

                if min_level >= 50:
                    combinations.append({
                        "name": combo["name"],
                        "level": min_level,
                        "effects": combo["bonus_effects"]
                    })

        return combinations

    def generate_skill_report(self, character_skills: CharacterSkills) -> Dict[str, Any]:
        """Generate comprehensive skill report"""
        total_levels = sum(progress.current_level for progress in character_skills.skills.values())
        mastered_count = len(character_skills.get_mastered_skills())

        # Calculate category distribution
        category_distribution = {}
        for skill_id, progress in character_skills.skills.items():
            skill = self.get_skill(skill_id)
            if skill:
                category = skill.category.value
                category_distribution[category] = category_distribution.get(category, 0) + progress.current_level

        # Find highest skills
        top_skills = sorted(character_skills.skills.items(),
                          key=lambda x: x[1].current_level,
                          reverse=True)[:10]

        # Check combinations
        combinations = self.check_skill_combination(character_skills)

        return {
            "total_levels": total_levels,
            "skill_count": len(character_skills.skills),
            "mastered_skills": mastered_count,
            "skill_points_available": character_skills.skill_points,
            "category_distribution": category_distribution,
            "top_skills": [(skill_id, progress.current_level) for skill_id, progress in top_skills],
            "combinations": combinations,
            "learning_bonus": character_skills.learning_bonus
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize skill system
    skill_system = SkillSystem()

    # Create character skills
    character_skills = CharacterSkills("player_001")
    character_skills.skill_points = 10

    # Learn some skills
    sword_mastery = skill_system.get_skill("sword_mastery")
    if sword_mastery:
        character_skills.learn_skill(sword_mastery)
        character_skills.upgrade_skill("sword_mastery", 5)

    fireball = skill_system.get_skill("fireball")
    if fireball:
        character_skills.learn_skill(fireball)
        character_skills.upgrade_skill("fireball", 3)

    # Add experience through use
    character_skills.add_skill_experience("sword_mastery", 150)
    character_skills.add_skill_experience("fireball", 80)

    # Generate skill report
    report = skill_system.generate_skill_report(character_skills)
    print("=== SKILL REPORT ===")
    print(f"Total Levels: {report['total_levels']}")
    print(f"Skills Learned: {report['skill_count']}")
    print(f"Mastered Skills: {report['mastered_skills']}")
    print(f"Available Points: {report['skill_points_available']}")
    print(f"Category Distribution: {report['category_distribution']}")

    print("\nTop Skills:")
    for skill_id, level in report['top_skills']:
        skill = skill_system.get_skill(skill_id)
        print(f"  {skill.name}: Level {level}")

    print(f"\nSkill Combinations: {len(report['combinations'])}")
    for combo in report['combinations']:
        print(f"  {combo['name']} (Level {combo['level']})")

    # Get recommendations
    recommendations = skill_system.get_skill_recommendations(character_skills, "warrior", "damage")
    print(f"\nRecommended Skills:")
    for skill in recommendations[:5]:
        print(f"  {skill.name}: {skill.description}")

    # Check skill power
    sword_power = skill_system.calculate_skill_power(character_skills, "sword_mastery")
    fireball_power = skill_system.calculate_skill_power(character_skills, "fireball")
    print(f"\nSkill Power:")
    print(f"  Sword Mastery: {sword_power:.1f}")
    print(f"  Fireball: {fireball_power:.1f}")