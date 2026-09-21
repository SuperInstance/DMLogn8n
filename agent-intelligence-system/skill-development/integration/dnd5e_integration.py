"""
D&D 5e Integration for DMlogn8n Skill Development System

This module provides integration between the progressive skill development system
and the D&D 5th Edition rule system, including ability score mappings,
skill check calculations, and character sheet integration.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..core.skill import Skill, SkillCategory, MasteryLevel
from ..core.skill_progression import SkillProgression
from ..calculators.experience_calculator import ExperienceCalculator, XPContext


class DND5EAbility(Enum):
    """D&D 5e ability scores"""
    STRENGTH = "Strength"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    CHARISMA = "Charisma"


class DND5ESkill(Enum):
    """D&D 5e official skills"""
    ACROBATICS = "Acrobatics"
    ANIMAL_HANDLING = "Animal Handling"
    ARCANA = "Arcana"
    ATHLETICS = "Athletics"
    DECEPTION = "Deception"
    HISTORY = "History"
    INSIGHT = "Insight"
    INTIMIDATION = "Intimidation"
    INVESTIGATION = "Investigation"
    MEDICINE = "Medicine"
    NATURE = "Nature"
    PERCEPTION = "Perception"
    PERFORMANCE = "Performance"
    PERSUASION = "Persuasion"
    RELIGION = "Religion"
    SLEIGHT_OF_HAND = "Sleight of Hand"
    STEALTH = "Stealth"
    SURVIVAL = "Survival"


@dataclass
class SkillToAbilityMapping:
    """Maps D&D 5e skills to their primary abilities"""
    skill: DND5ESkill
    ability: DND5EAbility
    can_be_expert: bool = True
    requires_training: bool = True

    def get_ability_modifier(self, ability_scores: Dict[DND5EAbility, int]) -> int:
        """Calculate ability modifier"""
        score = ability_scores.get(self.ability, 10)
        return (score - 10) // 2


@dataclass
class DND5ECharacter:
    """D&D 5e character sheet integration"""
    name: str
    level: int
    class_name: str
    ability_scores: Dict[DND5EAbility, int]
    proficiency_bonus: int
    skill_proficiencies: List[DND5ESkill]
    skill_expertise: List[DND5ESkill]
    race: str = ""
    background: str = ""
    equipment: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)

    def get_skill_modifier(self, skill: DND5ESkill, ability_scores: Dict[DND5EAbility, int],
                          proficiency_bonus: int, skill_proficiencies: List[DND5ESkill],
                          skill_expertise: List[DND5ESkill]) -> int:
        """Calculate total skill modifier"""
        mapping = DND5EIntegration.get_skill_mapping(skill)
        ability_mod = mapping.get_ability_modifier(ability_scores)

        if skill in skill_expertise:
            return ability_mod + (proficiency_bonus * 2)
        elif skill in skill_proficiencies:
            return ability_mod + proficiency_bonus
        else:
            return ability_mod

    def get_passive_perception(self, ability_scores: Dict[DND5EAbility, int],
                              proficiency_bonus: int, skill_proficiencies: List[DND5ESkill],
                              skill_expertise: List[DND5ESkill]) -> int:
        """Calculate passive perception score"""
        perception_mod = self.get_skill_modifier(
            DND5ESkill.PERCEPTION, ability_scores, proficiency_bonus,
            skill_proficiencies, skill_expertise
        )
        return 10 + perception_mod


class DND5EIntegration:
    """
    Integration layer for D&D 5e rules and progressive skill development

    This class provides methods to convert between D&D 5e mechanics
    and the progressive skill development system.
    """

    # D&D 5e skill to ability mappings
    SKILL_MAPPINGS = {
        DND5ESkill.ACROBATICS: SkillToAbilityMapping(DND5ESkill.ACROBATICS, DND5EAbility.DEXTERITY),
        DND5ESkill.ANIMAL_HANDLING: SkillToAbilityMapping(DND5ESkill.ANIMAL_HANDLING, DND5EAbility.WISDOM),
        DND5ESkill.ARCANA: SkillToAbilityMapping(DND5ESkill.ARCANA, DND5EAbility.INTELLIGENCE),
        DND5ESkill.ATHLETICS: SkillToAbilityMapping(DND5ESkill.ATHLETICS, DND5EAbility.STRENGTH),
        DND5ESkill.DECEPTION: SkillToAbilityMapping(DND5ESkill.DECEPTION, DND5EAbility.CHARISMA),
        DND5ESkill.HISTORY: SkillToAbilityMapping(DND5ESkill.HISTORY, DND5EAbility.INTELLIGENCE),
        DND5ESkill.INSIGHT: SkillToAbilityMapping(DND5ESkill.INSIGHT, DND5EAbility.WISDOM),
        DND5ESkill.INTIMIDATION: SkillToAbilityMapping(DND5ESkill.INTIMIDATION, DND5EAbility.CHARISMA),
        DND5ESkill.INVESTIGATION: SkillToAbilityMapping(DND5ESkill.INVESTIGATION, DND5EAbility.INTELLIGENCE),
        DND5ESkill.MEDICINE: SkillToAbilityMapping(DND5ESkill.MEDICINE, DND5EAbility.WISDOM),
        DND5ESkill.NATURE: SkillToAbilityMapping(DND5ESkill.NATURE, DND5EAbility.INTELLIGENCE),
        DND5ESkill.PERCEPTION: SkillToAbilityMapping(DND5ESkill.PERCEPTION, DND5EAbility.WISDOM),
        DND5ESkill.PERFORMANCE: SkillToAbilityMapping(DND5ESkill.PERFORMANCE, DND5EAbility.CHARISMA),
        DND5ESkill.PERSUASION: SkillToAbilityMapping(DND5ESkill.PERSUASION, DND5EAbility.CHARISMA),
        DND5ESkill.RELIGION: SkillToAbilityMapping(DND5ESkill.RELIGION, DND5EAbility.INTELLIGENCE),
        DND5ESkill.SLEIGHT_OF_HAND: SkillToAbilityMapping(DND5ESkill.SLEIGHT_OF_HAND, DND5EAbility.DEXTERITY),
        DND5ESkill.STEALTH: SkillToAbilityMapping(DND5ESkill.STEALTH, DND5EAbility.DEXTERITY),
        DND5ESkill.SURVIVAL: SkillToAbilityMapping(DND5ESkill.SURVIVAL, DND5EAbility.WISDOM),
    }

    # Progression system skill to D&D 5e skill mappings
    PROGRESSION_TO_DND_MAPPINGS = {
        # Combat Skills
        "Weapon Mastery": DND5ESkill.ATHLETICS,
        "Targeting Precision": DND5ESkill.ATHLETICS,
        "Positional Awareness": DND5ESkill.ACROBATICS,
        "Combat Timing": DND5ESkill.ATHLETICS,
        "Defensive Stance": DND5ESkill.ATHLETICS,

        # Social Skills
        "Persuasion": DND5ESkill.PERSUASION,
        "Deception": DND5ESkill.DECEPTION,
        "Intimidation": DND5ESkill.INTIMIDATION,
        "Performance": DND5ESkill.PERFORMANCE,
        "Empathy": DND5ESkill.INSIGHT,
        "Leadership": DND5ESkill.PERSUASION,

        # Exploration Skills
        "Perception": DND5ESkill.PERCEPTION,
        "Investigation": DND5ESkill.INVESTIGATION,
        "Stealth": DND5ESkill.STEALTH,
        "Survival": DND5ESkill.SURVIVAL,
        "Tracking": DND5ESkill.SURVIVAL,
        "Natural Knowledge": DND5ESkill.NATURE,

        # Magic Skills
        "Magical Theory": DND5ESkill.ARCANA,
        "Ritual Magic": DND5ESkill.ARCANA,

        # Strategic Skills
        "Tactical Planning": DND5ESkill.INVESTIGATION,
        "Risk Assessment": DND5ESkill.INSIGHT,
    }

    @classmethod
    def get_skill_mapping(cls, skill: DND5ESkill) -> SkillToAbilityMapping:
        """Get skill to ability mapping"""
        return cls.SKILL_MAPPINGS[skill]

    @classmethod
    def map_progression_skill_to_dnd(cls, skill_name: str) -> Optional[DND5ESkill]:
        """Map progression system skill to D&D 5e skill"""
        return cls.PROGRESSION_TO_DND_MAPPINGS.get(skill_name)

    @classmethod
    def calculate_dnd_difficulty_class(cls, skill: Skill, character: DND5ECharacter) -> int:
        """
        Calculate appropriate D&D 5e Difficulty Class for skill check

        Args:
            skill: The progressive skill being used
            character: The D&D character attempting the check

        Returns:
            int: Appropriate DC for the skill check
        """
        base_dc = 10

        # Adjust based on skill mastery level
        mastery_adjustments = {
            MasteryLevel.NOVICE: 5,
            MasteryLevel.APPRENTICE: 8,
            MasteryLevel.JOURNEYMAN: 12,
            MasteryLevel.EXPERT: 15,
            MasteryLevel.MASTER: 18
        }

        dc = base_dc + mastery_adjustments.get(skill.current_level, 10)

        # Adjust based on character level
        level_adjustment = (character.level - 1) // 2
        dc += level_adjustment

        # Cap between 5 and 30
        return max(5, min(30, dc))

    @classmethod
    def convert_mastery_to_proficiency(cls, mastery_level: MasteryLevel) -> Tuple[bool, bool]:
        """
        Convert mastery level to D&D 5e proficiency status

        Returns:
            Tuple of (is_proficient, is_expert)
        """
        proficiency_map = {
            MasteryLevel.NOVICE: (False, False),
            MasteryLevel.APPRENTICE: (True, False),
            MasteryLevel.JOURNEYMAN: (True, False),
            MasteryLevel.EXPERT: (True, True),
            MasteryLevel.MASTER: (True, True)
        }

        return proficiency_map.get(mastery_level, (False, False))

    @classmethod
    def calculate_skill_check_bonus(cls, skill: Skill, character: DND5ECharacter) -> int:
        """
        Calculate total bonus for D&D 5e skill check based on progressive skill

        Args:
            skill: The progressive skill
            character: The D&D character

        Returns:
            int: Total skill check bonus
        """
        # Map to D&D 5e skill
        dnd_skill = cls.map_progression_skill_to_dnd(skill.name)
        if not dnd_skill:
            # For unmapped skills, use basic ability score
            if skill.category == SkillCategory.COMBAT:
                ability_mod = (character.ability_scores.get(DND5EAbility.STRENGTH, 10) - 10) // 2
            elif skill.category == SkillCategory.SOCIAL:
                ability_mod = (character.ability_scores.get(DND5EAbility.CHARISMA, 10) - 10) // 2
            elif skill.category == SkillCategory.MAGIC:
                ability_mod = (character.ability_scores.get(DND5EAbility.INTELLIGENCE, 10) - 10) // 2
            elif skill.category == SkillCategory.EXPLORATION:
                ability_mod = (character.ability_scores.get(DND5EAbility.WISDOM, 10) - 10) // 2
            else:
                ability_mod = (character.ability_scores.get(DND5EAbility.INTELLIGENCE, 10) - 10) // 2
        else:
            mapping = cls.get_skill_mapping(dnd_skill)
            ability_mod = mapping.get_ability_modifier(character.ability_scores)

        # Add proficiency based on mastery level
        is_proficient, is_expert = cls.convert_mastery_to_proficiency(skill.current_level)

        if is_expert:
            proficiency_bonus = character.proficiency_bonus * 2
        elif is_proficient:
            proficiency_bonus = character.proficiency_bonus
        else:
            proficiency_bonus = 0

        # Add mastery bonus
        mastery_bonus = skill.current_level.bonus_dice

        return ability_mod + proficiency_bonus + mastery_bonus

    @classmethod
    def roll_skill_check(cls, skill: Skill, character: DND5ECharacter,
                        advantage: bool = False, disadvantage: bool = False) -> Dict[str, Any]:
        """
        Perform D&D 5e style skill check using progressive skill system

        Args:
            skill: The progressive skill being used
            character: The D&D character
            advantage: Whether to roll with advantage
            disadvantage: Whether to roll with disadvantage

        Returns:
            Dict with roll results
        """
        import random

        # Calculate bonus
        bonus = cls.calculate_skill_check_bonus(skill, character)

        # Roll dice
        if advantage and disadvantage:
            # Advantage and disadvantage cancel out
            d20_roll = random.randint(1, 20)
            rolls = [d20_roll]
        elif advantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            d20_roll = max(roll1, roll2)
            rolls = [roll1, roll2]
        elif disadvantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            d20_roll = min(roll1, roll2)
            rolls = [roll1, roll2]
        else:
            d20_roll = random.randint(1, 20)
            rolls = [d20_roll]

        # Check for critical success/failure
        critical_success = d20_roll == 20
        critical_failure = d20_roll == 1

        total = d20_roll + bonus

        return {
            'd20_rolls': rolls,
            'bonus': bonus,
            'total': total,
            'critical_success': critical_success,
            'critical_failure': critical_failure,
            'skill_name': skill.name,
            'mastery_level': skill.current_level.name
        }

    @classmethod
    def create_character_from_progression(cls, progression: SkillProgression,
                                         name: str, level: int, character_class: str,
                                         ability_scores: Dict[DND5EAbility, int]) -> DND5ECharacter:
        """
        Create D&D 5e character based on skill progression

        Args:
            progression: Skill progression data
            name: Character name
            level: Character level
            character_class: D&D class
            ability_scores: Ability scores

        Returns:
            DND5ECharacter object
        """
        # Calculate proficiency bonus
        proficiency_bonus = 1 + ((level - 1) // 4)

        # Determine skill proficiencies based on mastery levels
        skill_proficiencies = []
        skill_expertise = []

        for skill_name, skill in progression.skills.items():
            dnd_skill = cls.map_progression_skill_to_dnd(skill_name)
            if dnd_skill:
                is_proficient, is_expert = cls.convert_mastery_to_proficiency(skill.current_level)

                if is_proficient:
                    skill_proficiencies.append(dnd_skill)
                if is_expert:
                    skill_expertise.append(dnd_skill)

        return DND5ECharacter(
            name=name,
            level=level,
            class_name=character_class,
            ability_scores=ability_scores,
            proficiency_bonus=proficiency_bonus,
            skill_proficiencies=skill_proficiencies,
            skill_expertise=skill_expertise
        )

    @classmethod
    def integrate_with_combat(cls, skill: Skill, combat_type: str) -> Dict[str, Any]:
        """
        Integrate progressive combat skills with D&D 5e combat mechanics

        Args:
            skill: The combat skill
            combat_type: Type of combat interaction

        Returns:
            Dict with combat integration data
        """
        integration_data = {
            'skill_name': skill.name,
            'mastery_level': skill.current_level.name,
            'combat_modifiers': {}
        }

        if skill.category == SkillCategory.COMBAT:
            if "Weapon Mastery" in skill.name:
                integration_data['combat_modifiers']['attack_bonus'] = skill.current_level.bonus_dice
                integration_data['combat_modifiers']['damage_bonus'] = skill.current_level.bonus_dice

            elif "Targeting Precision" in skill.name:
                integration_data['combat_modifiers']['attack_bonus'] = skill.current_level.bonus_dice
                integration_data['combat_modifiers']['critical_range'] = 20 - (skill.current_level.bonus_dice // 2)

            elif "Defensive Stance" in skill.name:
                integration_data['combat_modifiers']['ac_bonus'] = skill.current_level.bonus_dice
                integration_data['combat_modifiers']['saves_advantage'] = True if skill.current_level.value >= 3 else False

        return integration_data

    @classmethod
    def generate_character_sheet_export(cls, progression: SkillProgression,
                                      character: DND5ECharacter) -> Dict[str, Any]:
        """
        Generate D&D 5e character sheet data from progression system

        Args:
            progression: Skill progression data
            character: D&D character

        Returns:
            Dict with character sheet data
        """
        sheet_data = {
            'character_info': {
                'name': character.name,
                'level': character.level,
                'class': character.class_name,
                'race': character.race,
                'background': character.background
            },
            'ability_scores': {
                ability.value: score for ability, score in character.ability_scores.items()
            },
            'proficiency_bonus': character.proficiency_bonus,
            'skills': {},
            'progressive_skills': {},
            'features': character.features
        }

        # Add D&D 5e skills
        for skill in DND5ESkill:
            modifier = character.get_skill_modifier(
                skill, character.ability_scores, character.proficiency_bonus,
                character.skill_proficiencies, character.skill_expertise
            )

            proficiency_status = "None"
            if skill in character.skill_expertise:
                proficiency_status = "Expert"
            elif skill in character.skill_proficiencies:
                proficiency_status = "Proficient"

            sheet_data['skills'][skill.value] = {
                'modifier': modifier,
                'proficiency': proficiency_status
            }

        # Add progressive skills
        for skill_name, skill in progression.skills.items():
            sheet_data['progressive_skills'][skill_name] = {
                'mastery_level': skill.current_level.name,
                'total_xp': skill.total_xp,
                'success_rate': skill.success_rate,
                'special_abilities': [ability.name for ability in skill.get_active_abilities()]
            }

        return sheet_data

    @classmethod
    def calculate_encounter_difficulty(cls, party_skills: Dict[str, SkillProgression],
                                     encounter_challenge: str) -> Dict[str, Any]:
        """
        Calculate encounter difficulty based on party's progressive skills

        Args:
            party_skills: Dictionary of character progressions
            encounter_challenge: Encounter difficulty rating

        Returns:
            Dict with difficulty analysis
        """
        difficulty_analysis = {
            'encounter_challenge': encounter_challenge,
            'party_capabilities': {},
            'recommended_level': 1,
            'adjustments': []
        }

        # Analyze party capabilities
        total_combat_xp = 0
        total_social_xp = 0
        total_exploration_xp = 0
        total_magic_xp = 0
        total_strategic_xp = 0

        for character_name, progression in party_skills.items():
            character_stats = {
                'combat_xp': 0,
                'social_xp': 0,
                'exploration_xp': 0,
                'magic_xp': 0,
                'strategic_xp': 0,
                'total_xp': 0,
                'master_skills': []
            }

            for skill in progression.skills.values():
                character_stats['total_xp'] += skill.total_xp

                if skill.category == SkillCategory.COMBAT:
                    character_stats['combat_xp'] += skill.total_xp
                elif skill.category == SkillCategory.SOCIAL:
                    character_stats['social_xp'] += skill.total_xp
                elif skill.category == SkillCategory.EXPLORATION:
                    character_stats['exploration_xp'] += skill.total_xp
                elif skill.category == SkillCategory.MAGIC:
                    character_stats['magic_xp'] += skill.total_xp
                elif skill.category == SkillCategory.STRATEGIC:
                    character_stats['strategic_xp'] += skill.total_xp

                if skill.current_level == MasteryLevel.MASTER:
                    character_stats['master_skills'].append(skill.name)

            total_combat_xp += character_stats['combat_xp']
            total_social_xp += character_stats['social_xp']
            total_exploration_xp += character_stats['exploration_xp']
            total_magic_xp += character_stats['magic_xp']
            total_strategic_xp += character_stats['strategic_xp']

            difficulty_analysis['party_capabilities'][character_name] = character_stats

        # Calculate recommended party level based on total XP
        total_party_xp = total_combat_xp + total_social_xp + total_exploration_xp + total_magic_xp + total_strategic_xp
        avg_xp_per_character = total_party_xp / max(1, len(party_skills))

        # Rough level estimation (500 XP per level average)
        estimated_level = max(1, min(20, int(avg_xp_per_character / 500)))
        difficulty_analysis['recommended_level'] = estimated_level

        # Generate encounter adjustments
        if total_combat_xp < total_social_xp + total_exploration_xp:
            difficulty_analysis['adjustments'].append("Party seems more focused on social/exploration - consider reducing combat difficulty")

        if total_magic_xp > total_combat_xp:
            difficulty_analysis['adjustments'].append("Party has strong magical capabilities - include magic-resistant enemies")

        if total_strategic_xp > avg_xp_per_character:
            difficulty_analysis['adjustments'].append("Party is highly strategic - include complex tactical challenges")

        return difficulty_analysis