"""
Integration Examples for D&D 5e System

This module demonstrates integration between the progressive skill development
system and D&D 5e mechanics, including character creation, skill checks,
and combat integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict
from integration.dnd5e_integration import (
    DND5EIntegration, DND5ECharacter, DND5EAbility, DND5ESkill
)
from core.skill_progression import SkillProgression
from categories.combat_skills import CombatSkills
from categories.social_skills import SocialSkills
from calculators.experience_calculator import ExperienceCalculator, XPContext


class IntegrationExamples:
    """Demonstrates D&D 5e integration features"""

    def __init__(self):
        self.agent_id = "integration_agent"
        self.progression = SkillProgression(self.agent_id)
        self.xp_calculator = ExperienceCalculator()

    def run_all_examples(self):
        """Run all integration examples"""
        print("🎲 Progressive Skill Development System - D&D 5e Integration")
        print("=" * 65)

        self.example_1_character_creation()
        self.example_2_skill_checks()
        self.example_3_combat_integration()
        self.example_4_character_sheet_export()
        self.example_5_encounter_difficulty()

    def example_1_character_creation(self):
        """Example 1: Creating D&D 5e character from progression"""
        print("\n👤 Example 1: Character Creation from Progression")
        print("-" * 45)

        # Create some skills for the character
        skills_to_add = [
            CombatSkills.create_weapon_mastery(),
            CombatSkills.create_targeting_precision(),
            SocialSkills.create_persuasion(),
            SocialSkills.create_intimidation()
        ]

        for skill in skills_to_add:
            self.progression.add_skill(skill)
            # Progress some skills
            skill.add_experience(150 if "Mastery" in skill.name else 100)

        # Define ability scores
        ability_scores = {
            DND5EAbility.STRENGTH: 16,
            DND5EAbility.DEXTERITY: 14,
            DND5EAbility.CONSTITUTION: 15,
            DND5EAbility.INTELLIGENCE: 12,
            DND5EAbility.WISDOM: 13,
            DND5EAbility.CHARISMA: 14
        }

        # Create D&D 5e character
        character = DND5EIntegration.create_character_from_progression(
            progression=self.progression,
            name="Aldric the Brave",
            level=5,
            character_class="Fighter",
            ability_scores=ability_scores
        )

        print(f"Created D&D 5e Character: {character.name}")
        print(f"  Level {character.level} {character.class_name}")
        print(f"  Proficiency Bonus: +{character.proficiency_bonus}")
        print(f"  Ability Scores:")
        for ability, score in character.ability_scores.items():
            modifier = (score - 10) // 2
            print(f"    {ability.value}: {score} ({modifier:+d})")

        print(f"  Skill Proficiencies:")
        for skill in character.skill_proficiencies:
            modifier = character.get_skill_modifier(
                skill, character.ability_scores, character.proficiency_bonus,
                character.skill_proficiencies, character.skill_expertise
            )
            status = "Expert" if skill in character.skill_expertise else "Proficient"
            print(f"    {skill.value}: {modifier:+d} ({status})")

        print(f"  Total skills from progression: {len(character.skill_proficiencies)}")

    def example_2_skill_checks(self):
        """Example 2: D&D 5e style skill checks with progressive skills"""
        print("\n🎯 Example 2: Progressive Skill Checks")
        print("-" * 35)

        # Get a character
        ability_scores = {
            DND5EAbility.STRENGTH: 16,
            DND5EAbility.DEXTERITY: 14,
            DND5EAbility.CONSTITUTION: 15,
            DND5EAbility.INTELLIGENCE: 12,
            DND5EAbility.WISDOM: 13,
            DND5EAbility.CHARISMA: 14
        }

        character = DND5ECharacter(
            name="Test Character",
            level=3,
            class_name="Fighter",
            ability_scores=ability_scores,
            proficiency_bonus=2,
            skill_proficiencies=[DND5ESkill.ATHLETICS, DND5ESkill.INTIMIDATION],
            skill_expertise=[]
        )

        # Get a progressive skill
        weapon_mastery = self.progression.get_skill("Weapon Mastery")
        if not weapon_mastery:
            weapon_mastery = CombatSkills.create_weapon_mastery()
            self.progression.add_skill(weapon_mastery)
            weapon_mastery.add_experience(200)  # Journeyman level

        print(f"Testing skill checks with {weapon_mastery.name} ({weapon_mastery.current_level.name}):")

        # Perform several skill checks
        for i in range(5):
            result = DND5EIntegration.roll_skill_check(
                skill=weapon_mastery,
                character=character,
                advantage=i == 2,  # Third roll with advantage
                disadvantage=i == 4  # Fifth roll with disadvantage
            )

            roll_desc = "Normal"
            if result['advantage'] and result['disadvantage']:
                roll_desc = "Normal (adv/disadv cancel)"
            elif result['advantage']:
                roll_desc = "Advantage"
            elif result['disadvantage']:
                roll_desc = "Disadvantage"

            print(f"  Roll {i+1} ({roll_desc}):")
            print(f"    Dice: {result['d20_rolls']}")
            print(f"    Bonus: +{result['bonus']}")
            print(f"    Total: {result['total']}")

            if result['critical_success']:
                print(f"    🎉 CRITICAL SUCCESS!")
            elif result['critical_failure']:
                print(f"    💀 CRITICAL FAILURE!")

            # Calculate DC for this skill level
            dc = DND5EIntegration.calculate_dnd_difficulty_class(weapon_mastery, character)
            success = result['total'] >= dc
            print(f"    DC {dc}: {'✅ Success' if success else '❌ Failure'}")

    def example_3_combat_integration(self):
        """Example 3: Combat integration with progressive skills"""
        print("\n⚔️ Example 3: Combat Integration")
        print("-" * 30)

        # Create character
        ability_scores = {
            DND5EAbility.STRENGTH: 18,
            DND5EAbility.DEXTERITY: 14,
            DND5EAbility.CONSTITUTION: 16,
            DND5EAbility.INTELLIGENCE: 10,
            DND5EAbility.WISDOM: 12,
            DND5EAbility.CHARISMA: 13
        }

        fighter = DND5ECharacter(
            name="Gorok Ironforge",
            level=6,
            class_name="Fighter",
            ability_scores=ability_scores,
            proficiency_bonus=3,
            skill_proficiencies=[DND5ESkill.ATHLETICS, DND5ESkill.INTIMIDATION],
            skill_expertise=[DND5ESkill.ATHLETICS]
        )

        # Get combat skills
        weapon_mastery = self.progression.get_skill("Weapon Mastery")
        if not weapon_mastery:
            weapon_mastery = CombatSkills.create_weapon_mastery()
            self.progression.add_skill(weapon_mastery)
            weapon_mastery.add_experience(500)  # Expert level

        targeting = self.progression.get_skill("Targeting Precision")
        if not targeting:
            targeting = CombatSkills.create_targeting_precision()
            self.progression.add_skill(targeting)
            targeting.add_experience(300)  # Journeyman level

        print(f"Combat Integration for {fighter.name}:")
        print(f"  Character Level: {fighter.level}")
        print(f"  Strength: {fighter.ability_scores[DND5EAbility.STRENGTH]} (+{(fighter.ability_scores[DND5EAbility.STRENGTH] - 10) // 2})")

        # Show combat modifiers for each skill
        for skill_name, skill in [("Weapon Mastery", weapon_mastery), ("Targeting Precision", targeting)]:
            integration = DND5EIntegration.integrate_with_combat(skill, "melee_combat")
            print(f"\n  {skill_name} ({skill.current_level.name}):")
            print(f"    Skill bonus: +{DND5EIntegration.calculate_skill_check_bonus(skill, fighter)}")
            if integration['combat_modifiers']:
                for mod_type, value in integration['combat_modifiers'].items():
                    print(f"    {mod_type}: {value}")

        # Simulate combat round
        print(f"\nSimulated Combat Round:")
        weapon_result = DND5EIntegration.roll_skill_check(weapon_mastery, fighter)
        targeting_result = DND5EIntegration.roll_skill_check(targeting, fighter)

        print(f"  Weapon Attack: {weapon_result['total']} vs AC 16 {'✅ Hit' if weapon_result['total'] >= 16 else '❌ Miss'}")
        print(f"  Called Shot: {targeting_result['total']} vs DC 14 {'✅ Success' if targeting_result['total'] >= 14 else '❌ Failure'}")

    def example_4_character_sheet_export(self):
        """Example 4: Exporting character sheet data"""
        print("\n📄 Example 4: Character Sheet Export")
        print("-" * 33)

        # Create a well-developed character
        ability_scores = {
            DND5EAbility.STRENGTH: 17,
            DND5EAbility.DEXTERITY: 15,
            DND5EAbility.CONSTITUTION: 16,
            DND5EAbility.INTELLIGENCE: 14,
            DND5EAbility.WISDOM: 13,
            DND5EAbility.CHARISMA: 15
        }

        character = DND5ECharacter(
            name="Lyra Starweaver",
            level=8,
            character_class="Bard",
            ability_scores=ability_scores,
            proficiency_bonus=3,
            skill_proficiencies=[
                DND5ESkill.PERSUASION, DND5ESkill.DECEPTION, DND5ESkill.STEALTH,
                DND5ESkill.PERCEPTION, DND5ESkill.INVESTIGATION
            ],
            skill_expertise=[DND5ESkill.PERSUASION, DND5ESkill.DECEPTION],
            race="Half-Elf",
            background="Entertainer"
        )

        # Add some progression skills
        skills_to_add = [
            SocialSkills.create_persuasion(),
            SocialSkills.create_deception(),
            SocialSkills.create_performance(),
            CombatSkills.create_weapon_mastery()
        ]

        for skill in skills_to_add:
            self.progression.add_skill(skill)
            skill.add_experience(400)  # Expert level

        # Export character sheet
        sheet_data = DND5EIntegration.generate_character_sheet_export(
            self.progression, character
        )

        print(f"Character Sheet Export for {sheet_data['character_info']['name']}:")
        print(f"  Level {sheet_data['character_info']['level']} {sheet_data['character_info']['class']}")
        print(f"  Race: {sheet_data['character_info']['race']}")
        print(f"  Background: {sheet_data['character_info']['background']}")
        print(f"  Proficiency Bonus: +{sheet_data['proficiency_bonus']}")

        print(f"\nAbility Scores:")
        for ability, score in sheet_data['ability_scores'].items():
            modifier = (score - 10) // 2
            print(f"  {ability}: {score} ({modifier:+d})")

        print(f"\nKey Skills:")
        important_skills = [DND5ESkill.PERSUASION, DND5ESkill.DECEPTION, DND5ESkill.PERFORMANCE]
        for skill in important_skills:
            if skill.value in sheet_data['skills']:
                skill_data = sheet_data['skills'][skill.value]
                print(f"  {skill.value}: {skill_data['modifier']:+d} ({skill_data['proficiency']})")

        print(f"\nProgressive Skills:")
        for skill_name, skill_data in sheet_data['progressive_skills'].items():
            print(f"  {skill_name}:")
            print(f"    Mastery: {skill_data['mastery_level']}")
            print(f"    XP: {skill_data['total_xp']}")
            print(f"    Success Rate: {skill_data['success_rate']:.1f}%")

    def example_5_encounter_difficulty(self):
        """Example 5: Encounter difficulty calculation"""
        print("\n🐉 Example 5: Encounter Difficulty Analysis")
        print("-" * 42)

        # Create party with different skill progressions
        party = self._create_diverse_party()

        # Analyze encounter difficulty
        encounter_types = ["goblin_ambush", "dragon_encounter", "social_negotiation", "dungeon_puzzle"]

        for encounter in encounter_types:
            analysis = DND5EIntegration.calculate_encounter_difficulty(party, encounter)

            print(f"\nEncounter: {analysis['encounter_challenge'].replace('_', ' ').title()}")
            print(f"  Recommended party level: {analysis['recommended_level']}")
            print(f"  Adjustments:")
            for adjustment in analysis['adjustments']:
                print(f"    • {adjustment}")

        # Show party capabilities summary
        print(f"\nParty Capabilities Summary:")
        for member_name, capabilities in analysis['party_capabilities'].items():
            print(f"  {member_name}:")
            print(f"    Total XP: {capabilities['total_xp']}")
            print(f"    Strongest category: {max(capabilities, key=lambda k: capabilities[k] if k != 'total_xp' and k != 'master_skills' else 0)}")
            print(f"    Master skills: {len(capabilities['master_skills'])}")

    def _create_diverse_party(self) -> Dict[str, SkillProgression]:
        """Create a diverse party for testing"""
        party = {}

        # Fighter - Combat focused
        fighter_progression = SkillProgression("Fighter")
        combat_skills = CombatSkills.create_all_combat_skills()[:6]
        for skill in combat_skills:
            fighter_progression.add_skill(skill)
            skill.add_experience(300 + hash(skill.name) % 200)  # Variable progression
        party["Fighter"] = fighter_progression

        # Wizard - Magic focused
        wizard_progression = SkillProgression("Wizard")
        from categories.magic_skills import MagicSkills
        magic_skills = MagicSkills.create_all_magic_skills()[:6]
        for skill in magic_skills:
            wizard_progression.add_skill(skill)
            skill.add_experience(350 + hash(skill.name) % 150)
        party["Wizard"] = wizard_progression

        # Rogue - Exploration focused
        rogue_progression = SkillProgression("Rogue")
        from categories.exploration_skills import ExplorationSkills
        exploration_skills = ExplorationSkills.create_all_exploration_skills()[:6]
        for skill in exploration_skills:
            rogue_progression.add_skill(skill)
            skill.add_experience(280 + hash(skill.name) % 220)
        party["Rogue"] = rogue_progression

        # Bard - Social focused
        bard_progression = SkillProgression("Bard")
        social_skills = SocialSkills.create_all_social_skills()[:6]
        for skill in social_skills:
            bard_progression.add_skill(skill)
            skill.add_experience(320 + hash(skill.name) % 180)
        party["Bard"] = bard_progression

        return party


def main():
    """Run integration examples"""
    example = IntegrationExamples()
    example.run_all_examples()


if __name__ == "__main__":
    main()