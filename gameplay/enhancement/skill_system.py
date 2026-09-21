#!/usr/bin/env python3
"""
Deep Skill Progression System for DMLogn8n
Provides branching skill trees and meaningful character development
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class SkillCategory(Enum):
    COMBAT = "combat"
    MAGIC = "magic"
    SOCIAL = "social"
    CRAFTING = "crafting"
    STEALTH = "stealth"
    SUPPORT = "support"
    LEADERSHIP = "leadership"
    KNOWLEDGE = "knowledge"

class SkillType(Enum):
    ACTIVE = "active"
    PASSIVE = "passive"
    ULTIMATE = "ultimate"
    TRIGGER = "trigger"

class SkillRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class MasteryLevel(Enum):
    NOVICE = "novice"
    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    EXPERT = "expert"
    MASTER = "master"
    GRANDMASTER = "grandmaster"

@dataclass
class SkillPrerequisite:
    """Skill learning prerequisite"""
    skill_id: str
    min_level: int = 1
    category_level: Optional[int] = None
    character_level: Optional[int] = None

@dataclass
class SkillEffect:
    """Effect of a skill"""
    type: str  # damage, heal, buff, debuff, utility
    value: float
    duration: Optional[int] = None
    target: str = "enemy"  # enemy, ally, self, area
    scaling: Optional[str] = None  # stat to scale with

@dataclass
class Skill:
    """Individual skill definition"""
    id: str
    name: str
    description: str
    category: SkillCategory
    type: SkillType
    rarity: SkillRarity
    max_level: int = 10
    base_cost: int = 100
    cooldown: int = 0
    range: int = 1
    effects: List[SkillEffect] = field(default_factory=list)
    prerequisites: List[SkillPrerequisite] = field(default_factory=list)
    scaling_factor: float = 1.0
    mastery_bonus: float = 1.2

@dataclass
class SkillNode:
    """Node in skill tree"""
    skill: Skill
    unlocked: bool = False
    current_level: int = 0
    experience: int = 0
    mastery_level: MasteryLevel = MasteryLevel.NOVICE
    connections: List[str] = field(default_factory=list)  # Connected node IDs

@dataclass
class CharacterSkills:
    """Character's skill data"""
    character_id: str
    skill_points: int = 0
    total_spent: int = 0
    category_levels: Dict[SkillCategory, int] = field(default_factory=lambda: {cat: 0 for cat in SkillCategory})
    learned_skills: Dict[str, SkillNode] = field(default_factory=dict)
    mastery_bonuses: Dict[MasteryLevel, float] = field(default_factory=dict)
    skill_combinations: Set[str] = field(default_factory=set)

class SkillTree:
    """Skill tree structure"""

    def __init__(self):
        self.nodes: Dict[str, SkillNode] = {}
        self.root_nodes: List[str] = []
        self.category_trees: Dict[SkillCategory, List[str]] = defaultdict(list)

    def add_skill(self, skill: Skill, connections: List[str] = None):
        """Add skill to tree"""
        node = SkillNode(skill=skill)
        if connections:
            node.connections = connections

        self.nodes[skill.id] = node
        self.category_trees[skill.category].append(skill.id)

        # Check if this is a root node (no prerequisites)
        if not skill.prerequisites:
            self.root_nodes.append(skill.id)

    def get_available_skills(self, character_skills: CharacterSkills) -> List[SkillNode]:
        """Get skills available to learn"""
        available = []

        for node_id, node in self.nodes.items():
            if node.unlocked:
                continue

            # Check prerequisites
            can_learn = True
            for prereq in node.skill.prerequisites:
                if prereq.skill_id not in character_skills.learned_skills:
                    can_learn = False
                    break

                learned_node = character_skills.learned_skills[prereq.skill_id]
                if learned_node.current_level < prereq.min_level:
                    can_learn = False
                    break

                if prereq.category_level and character_skills.category_levels[node.skill.category] < prereq.category_level:
                    can_learn = False
                    break

                if prereq.character_level and character_skills.total_spent < prereq.character_level:
                    can_learn = False
                    break

            if can_learn:
                available.append(node)

        return available

    def get_upgrade_path(self, skill_id: str) -> List[str]:
        """Get upgrade path for a skill"""
        if skill_id not in self.nodes:
            return []

        path = [skill_id]
        visited = set()
        queue = [skill_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            node = self.nodes[current]
            for connection in node.connections:
                if connection not in visited:
                    path.append(connection)
                    queue.append(connection)

        return path

class SkillSystem:
    """Main skill progression system"""

    def __init__(self):
        self.skill_trees: Dict[str, SkillTree] = {}
        self.skills: Dict[str, Skill] = {}
        self.character_skills: Dict[str, CharacterSkills] = {}
        self.global_unlocks: Set[str] = set()
        self.analytics = SkillAnalytics()

        # Progression parameters
        self.exponential_cost_factor = 1.5
        self.category_level_bonus = 10
        self.mastery_thresholds = {
            MasteryLevel.NOVICE: 0,
            MasteryLevel.APPRENTICE: 25,
            MasteryLevel.JOURNEYMAN: 50,
            MasteryLevel.EXPERT: 100,
            MasteryLevel.MASTER: 200,
            MasteryLevel.GRANDMASTER: 400
        }
        self.synergy_bonus = 1.15

        self._initialize_default_skills()

    def _initialize_default_skills(self):
        """Initialize default skill set"""
        default_skills = [
            # Combat Skills
            Skill("sword_strike", "Sword Strike", "Basic sword attack", SkillCategory.COMBAT, SkillType.ACTIVE, SkillRarity.COMMON,
                 effects=[SkillEffect("damage", 15, target="enemy", scaling="attack")]),

            Skill("shield_bash", "Shield Bash", "Stunning shield attack", SkillCategory.COMBAT, SkillType.ACTIVE, SkillRarity.UNCOMMON,
                 cooldown=2, effects=[SkillEffect("damage", 10, target="enemy"), SkillEffect("stun", 1, duration=2, target="enemy")]),

            Skill("berserker_rage", "Berserker Rage", "Increase damage at cost of defense", SkillCategory.COMBAT, SkillType.ACTIVE, SkillRarity.RARE,
                 cooldown=5, effects=[SkillEffect("buff", 50, duration=5, target="self"), SkillEffect("debuff", 25, duration=5, target="self")]),

            # Magic Skills
            Skill("fireball", "Fireball", "Launch a fireball at enemies", SkillCategory.MAGIC, SkillType.ACTIVE, SkillRarity.COMMON,
                 range=3, cooldown=1, effects=[SkillEffect("damage", 20, target="enemy", scaling="magic")]),

            Skill("heal", "Heal", "Restore health to allies", SkillCategory.MAGIC, SkillType.ACTIVE, SkillRarity.COMMON,
                 effects=[SkillEffect("heal", 25, target="ally", scaling="magic")]),

            Skill("arcane_power", "Arcane Power", "Increase magical abilities", SkillCategory.MAGIC, SkillType.PASSIVE, SkillRarity.UNCOMMON,
                 effects=[SkillEffect("buff", 20, target="self")]),

            # Social Skills
            Skill("persuade", "Persuade", "Convince others to see your point of view", SkillCategory.SOCIAL, SkillType.ACTIVE, SkillRarity.COMMON,
                 effects=[SkillEffect("utility", 1, target="other")]),

            Skill("leadership", "Leadership", "Inspire allies to perform better", SkillCategory.SOCIAL, SkillType.PASSIVE, SkillRarity.RARE,
                 effects=[SkillEffect("buff", 15, target="area")]),

            Skill("intimidate", "Intimidate", "Force enemies to back down", SkillCategory.SOCIAL, SkillType.ACTIVE, SkillRarity.UNCOMMON,
                 effects=[SkillEffect("debuff", 30, duration=3, target="enemy")]),
        ]

        for skill in default_skills:
            self.skills[skill.id] = skill

        # Create skill tree
        main_tree = SkillTree()
        for skill in default_skills:
            main_tree.add_skill(skill)

        self.skill_trees["main"] = main_tree

    def create_character_skills(self, character_id: str) -> CharacterSkills:
        """Create skill data for new character"""
        character_skills = CharacterSkills(character_id=character_id)

        # Give starting skill points
        character_skills.skill_points = 5

        # Initialize mastery bonuses
        for mastery in MasteryLevel:
            character_skills.mastery_bonuses[mastery] = 1.0

        self.character_skills[character_id] = character_skills
        self.analytics.record_character_creation(character_id)

        return character_skills

    def learn_skill(self, character_id: str, skill_id: str) -> Tuple[bool, str]:
        """Learn a new skill"""
        if character_id not in self.character_skills:
            return False, "Character not found"

        if skill_id not in self.skills:
            return False, "Skill not found"

        character_skills = self.character_skills[character_id]
        skill = self.skills[skill_id]

        # Check if already learned
        if skill_id in character_skills.learned_skills:
            return False, "Skill already learned"

        # Check skill points
        cost = self.calculate_learn_cost(skill, character_skills)
        if character_skills.skill_points < cost:
            return False, f"Not enough skill points (need {cost}, have {character_skills.skill_points})"

        # Get available skills
        available_skills = []
        for tree in self.skill_trees.values():
            available_skills.extend(tree.get_available_skills(character_skills))

        skill_node = None
        for node in available_skills:
            if node.skill.id == skill_id:
                skill_node = node
                break

        if not skill_node:
            return False, "Skill prerequisites not met"

        # Learn the skill
        character_skills.skill_points -= cost
        character_skills.total_spent += cost

        skill_node.unlocked = True
        skill_node.current_level = 1
        character_skills.learned_skills[skill_id] = skill_node

        # Update category level
        character_skills.category_levels[skill.category] += 1

        self.analytics.record_skill_learn(character_id, skill_id, cost)

        return True, f"Learned {skill.name}"

    def upgrade_skill(self, character_id: str, skill_id: str) -> Tuple[bool, str]:
        """Upgrade an existing skill"""
        if character_id not in self.character_skills:
            return False, "Character not found"

        character_skills = self.character_skills[character_id]

        if skill_id not in character_skills.learned_skills:
            return False, "Skill not learned"

        skill_node = character_skills.learned_skills[skill_id]
        skill = skill_node.skill

        if skill_node.current_level >= skill.max_level:
            return False, "Skill already at max level"

        cost = self.calculate_upgrade_cost(skill, skill_node.current_level)
        if character_skills.skill_points < cost:
            return False, f"Not enough skill points (need {cost}, have {character_skills.skill_points})"

        # Upgrade the skill
        character_skills.skill_points -= cost
        character_skills.total_spent += cost

        skill_node.current_level += 1
        skill_node.experience = 0

        # Check for mastery level upgrade
        self.check_mastery_upgrade(skill_node)

        self.analytics.record_skill_upgrade(character_id, skill_id, skill_node.current_level, cost)

        return True, f"Upgraded {skill.name} to level {skill_node.current_level}"

    def check_mastery_upgrade(self, skill_node: SkillNode):
        """Check and apply mastery level upgrades"""
        for mastery, threshold in self.mastery_thresholds.items():
            if skill_node.experience >= threshold and mastery.value > skill_node.mastery_level.value:
                skill_node.mastery_level = mastery
                # Apply mastery bonus
                bonus_multiplier = 1.0 + (mastery.value * 0.05)
                skill_node.skill.mastery_bonus = bonus_multiplier

    def add_skill_experience(self, character_id: str, skill_id: str, experience: int) -> Tuple[bool, str]:
        """Add experience to a skill"""
        if character_id not in self.character_skills:
            return False, "Character not found"

        character_skills = self.character_skills[character_id]

        if skill_id not in character_skills.learned_skills:
            return False, "Skill not learned"

        skill_node = character_skills.learned_skills[skill_id]
        skill_node.experience += experience

        # Check for mastery level upgrade
        old_mastery = skill_node.mastery_level
        self.check_mastery_upgrade(skill_node)

        result_message = f"Added {experience} experience to {skill.name}"
        if skill_node.mastery_level != old_mastery:
            result_message += f" - Mastery level increased to {skill_node.mastery_level.value}"

        self.analytics.record_skill_experience(character_id, skill_id, experience)

        return True, result_message

    def calculate_learn_cost(self, skill: Skill, character_skills: CharacterSkills) -> int:
        """Calculate cost to learn a skill"""
        base_cost = skill.base_cost

        # Apply category level discount
        category_discount = 1.0 - (character_skills.category_levels[skill.category] * 0.02)
        category_discount = max(0.5, category_discount)  # Max 50% discount

        # Apply rarity multiplier
        rarity_multiplier = {
            SkillRarity.COMMON: 1.0,
            SkillRarity.UNCOMMON: 1.5,
            SkillRarity.RARE: 2.0,
            SkillRarity.EPIC: 3.0,
            SkillRarity.LEGENDARY: 5.0
        }[skill.rarity]

        cost = int(base_cost * category_discount * rarity_multiplier)
        return max(1, cost)

    def calculate_upgrade_cost(self, skill: Skill, current_level: int) -> int:
        """Calculate cost to upgrade a skill"""
        base_cost = skill.base_cost
        level_multiplier = math.pow(self.exponential_cost_factor, current_level)

        cost = int(base_cost * level_multiplier)
        return max(1, cost)

    def get_skill_power(self, character_id: str, skill_id: str) -> float:
        """Calculate effective power of a skill for a character"""
        if character_id not in self.character_skills:
            return 0.0

        character_skills = self.character_skills[character_id]

        if skill_id not in character_skills.learned_skills:
            return 0.0

        skill_node = character_skills.learned_skills[skill_id]
        skill = skill_node.skill

        # Base power from skill level
        base_power = skill_node.current_level

        # Apply mastery bonus
        mastery_power = base_power * skill.mastery_bonus

        # Apply category bonus
        category_bonus = 1.0 + (character_skills.category_levels[skill.category] * 0.05)

        # Apply synergy bonus
        synergy_count = len(character_skills.skill_combinations)
        synergy_bonus = math.pow(self.synergy_bonus, min(synergy_count, 5))

        total_power = mastery_power * category_bonus * synergy_bonus
        return total_power

    def create_skill_combination(self, character_id: str, skill_ids: List[str]) -> Tuple[bool, str]:
        """Create a skill combination for bonus effects"""
        if character_id not in self.character_skills:
            return False, "Character not found"

        character_skills = self.character_skills[character_id]

        # Check if all skills are learned
        for skill_id in skill_ids:
            if skill_id not in character_skills.learned_skills:
                return False, f"Skill {skill_id} not learned"

        # Check if skills are from different categories
        categories = set()
        for skill_id in skill_ids:
            skill = self.skills[skill_id]
            categories.add(skill.category)

        if len(categories) < 2:
            return False, "Skills must be from different categories"

        # Create combination identifier
        combo_id = "_".join(sorted(skill_ids))
        character_skills.skill_combinations.add(combo_id)

        # Award synergy bonus
        for skill_id in skill_ids:
            self.add_skill_experience(character_id, skill_id, 50)

        self.analytics.record_skill_combination(character_id, skill_ids)

        return True, f"Created skill combination: {combo_id}"

    def get_character_skill_summary(self, character_id: str) -> Dict[str, Any]:
        """Get summary of character's skills"""
        if character_id not in self.character_skills:
            return {"error": "Character not found"}

        character_skills = self.character_skills[character_id]

        summary = {
            "character_id": character_id,
            "skill_points": character_skills.skill_points,
            "total_spent": character_skills.total_spent,
            "category_levels": {cat.value: level for cat, level in character_skills.category_levels.items()},
            "learned_skills": {},
            "skill_combinations": list(character_skills.skill_combinations),
            "mastery_levels": {}
        }

        for skill_id, skill_node in character_skills.learned_skills.items():
            summary["learned_skills"][skill_id] = {
                "name": skill_node.skill.name,
                "level": skill_node.current_level,
                "experience": skill_node.experience,
                "mastery": skill_node.mastery_level.value,
                "power": self.get_skill_power(character_id, skill_id)
            }

        mastery_counts = defaultdict(int)
        for skill_node in character_skills.learned_skills.values():
            mastery_counts[skill_node.mastery_level.value] += 1

        summary["mastery_levels"] = dict(mastery_counts)

        return summary

    def award_skill_points(self, character_id: str, points: int, reason: str = "") -> Tuple[bool, str]:
        """Award skill points to a character"""
        if character_id not in self.character_skills:
            return False, "Character not found"

        character_skills = self.character_skills[character_id]
        character_skills.skill_points += points

        message = f"Awarded {points} skill points"
        if reason:
            message += f" for {reason}"

        self.analytics.record_skill_points_awarded(character_id, points, reason)

        return True, message

class SkillAnalytics:
    """Analytics for skill progression balance"""

    def __init__(self):
        self.character_data = {}
        self.skill_popularity = defaultdict(int)
        self.category_popularity = defaultdict(int)
        self.mastery_distribution = defaultdict(int)
        self.combination_frequency = defaultdict(int)

    def record_character_creation(self, character_id: str):
        """Record new character creation"""
        self.character_data[character_id] = {
            "created_at": time.time(),
            "skills_learned": [],
            "skills_upgraded": [],
            "combinations_created": []
        }

    def record_skill_learn(self, character_id: str, skill_id: str, cost: int):
        """Record skill learning"""
        if character_id in self.character_data:
            self.character_data[character_id]["skills_learned"].append({
                "skill_id": skill_id,
                "cost": cost,
                "timestamp": time.time()
            })

        self.skill_popularity[skill_id] += 1

    def record_skill_upgrade(self, character_id: str, skill_id: str, level: int, cost: int):
        """Record skill upgrade"""
        if character_id in self.character_data:
            self.character_data[character_id]["skills_upgraded"].append({
                "skill_id": skill_id,
                "level": level,
                "cost": cost,
                "timestamp": time.time()
            })

    def record_skill_experience(self, character_id: str, skill_id: str, experience: int):
        """Record skill experience gain"""
        pass  # Could be implemented for detailed tracking

    def record_skill_combination(self, character_id: str, skill_ids: List[str]):
        """Record skill combination creation"""
        if character_id in self.character_data:
            self.character_data[character_id]["combinations_created"].append({
                "skills": skill_ids,
                "timestamp": time.time()
            })

        combo_id = "_".join(sorted(skill_ids))
        self.combination_frequency[combo_id] += 1

    def record_skill_points_awarded(self, character_id: str, points: int, reason: str):
        """Record skill points awarded"""
        pass  # Could be implemented for balance tracking

    def get_popularity_analysis(self) -> Dict[str, Any]:
        """Get skill popularity analysis"""
        total_skills = sum(self.skill_popularity.values())
        if total_skills == 0:
            return {"total_skills": 0}

        popularity_percentages = {
            skill_id: (count / total_skills) * 100
            for skill_id, count in self.skill_popularity.items()
        }

        return {
            "total_skills": total_skills,
            "popularity_percentages": popularity_percentages,
            "most_popular": max(popularity_percentages.items(), key=lambda x: x[1]),
            "least_popular": min(popularity_percentages.items(), key=lambda x: x[1])
        }

# Utility functions for skill balance
def calculate_skill_power_curve(base_power: int, max_level: int, scaling_factor: float = 1.5) -> List[float]:
    """Calculate power curve for skill progression"""
    return [base_power * math.pow(scaling_factor, level - 1) for level in range(1, max_level + 1)]

def analyze_skill_tree_balance(skill_tree: SkillTree) -> Dict[str, Any]:
    """Analyze skill tree for balance issues"""
    analysis = {
        "total_skills": len(skill_tree.nodes),
        "category_distribution": defaultdict(int),
        "rarity_distribution": defaultdict(int),
        "depth_analysis": {},
        "prerequisite_complexity": []
    }

    for node in skill_tree.nodes.values():
        skill = node.skill
        analysis["category_distribution"][skill.category.value] += 1
        analysis["rarity_distribution"][skill.rarity.value] += 1

        # Analyze prerequisite complexity
        analysis["prerequisite_complexity"].append(len(skill.prerequisites))

    # Calculate averages
    if analysis["prerequisite_complexity"]:
        avg_prereqs = sum(analysis["prerequisite_complexity"]) / len(analysis["prerequisite_complexity"])
        analysis["average_prerequisites"] = avg_prereqs

    return analysis

# Export main classes
__all__ = [
    'SkillSystem',
    'Skill',
    'SkillNode',
    'SkillTree',
    'CharacterSkills',
    'SkillAnalytics',
    'calculate_skill_power_curve',
    'analyze_skill_tree_balance'
]