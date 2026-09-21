"""
Test suite for the core skill system components
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from core.skill import Skill, SkillCategory, MasteryLevel, SynergyBonus, SpecialAbility
from core.skill_progression import SkillProgression


class TestSkillSystem(unittest.TestCase):
    """Test cases for the core skill system"""

    def setUp(self):
        """Set up test fixtures"""
        self.skill = Skill(
            name="Test Skill",
            category=SkillCategory.COMBAT,
            description="A test skill for unit testing",
            base_difficulty=0.5
        )
        self.progression = SkillProgression("test_agent")

    def test_skill_creation(self):
        """Test skill creation and basic properties"""
        self.assertEqual(self.skill.name, "Test Skill")
        self.assertEqual(self.skill.category, SkillCategory.COMBAT)
        self.assertEqual(self.skill.current_level, MasteryLevel.NOVICE)
        self.assertEqual(self.skill.total_xp, 0)
        self.assertEqual(self.skill.success_rate, 0.0)

    def test_mastery_levels(self):
        """Test mastery level progression"""
        # Test initial state
        self.assertEqual(self.skill.current_level, MasteryLevel.NOVICE)
        self.assertEqual(self.skill.current_level.xp_threshold, 0)

        # Test progression to Apprentice
        self.skill.add_experience(25)
        self.assertEqual(self.skill.current_level, MasteryLevel.APPRENTICE)

        # Test progression to Journeyman
        self.skill.add_experience(75)  # Total 100
        self.assertEqual(self.skill.current_level, MasteryLevel.JOURNEYMAN)

        # Test progression to Expert
        self.skill.add_experience(300)  # Total 400
        self.assertEqual(self.skill.current_level, MasteryLevel.EXPERT)

        # Test progression to Master
        self.skill.add_experience(1200)  # Total 1600
        self.assertEqual(self.skill.current_level, MasteryLevel.MASTER)

    def test_xp_calculation(self):
        """Test XP calculation and thresholds"""
        # Test XP to next level
        self.assertEqual(self.skill.xp_to_next_level, 25)  # Novice -> Apprentice

        self.skill.add_experience(10)
        self.assertEqual(self.skill.xp_to_next_level, 15)  # 25 - 10 = 15

        self.skill.add_experience(15)  # Total 25
        self.assertEqual(self.skill.current_level, MasteryLevel.APPRENTICE)
        self.assertEqual(self.skill.xp_to_next_level, 75)  # 100 - 25 = 75

    def test_skill_usage_recording(self):
        """Test skill usage recording"""
        # Record successful usage
        level_up = self.skill.record_usage(
            success=True,
            difficulty=0.6,
            context="Test usage",
            xp_gained=15
        )
        self.assertEqual(self.skill.total_uses, 1)
        self.assertEqual(self.skill.successful_uses, 1)
        self.assertEqual(self.skill.success_rate, 100.0)
        self.assertEqual(self.skill.total_xp, 15)

        # Record failed usage
        self.skill.record_usage(
            success=False,
            difficulty=0.8,
            context="Test failure",
            xp_gained=5
        )
        self.assertEqual(self.skill.total_uses, 2)
        self.assertEqual(self.skill.successful_uses, 1)
        self.assertEqual(self.skill.success_rate, 50.0)
        self.assertEqual(self.skill.total_xp, 20)

    def test_critical_successes(self):
        """Test critical success handling"""
        # Record critical success
        self.skill.record_usage(
            success=True,
            difficulty=0.7,
            context="Critical hit",
            xp_gained=20,
            critical_success=True
        )
        self.assertEqual(self.skill.critical_successes, 1)
        self.assertEqual(self.skill.critical_success_rate, 100.0)

        # Record normal success
        self.skill.record_usage(
            success=True,
            difficulty=0.5,
            context="Normal hit",
            xp_gained=15
        )
        self.assertEqual(self.skill.critical_successes, 1)
        self.assertEqual(self.skill.critical_success_rate, 50.0)  # 1/2 = 50%

    def test_success_chance_calculation(self):
        """Test success chance calculation"""
        # Base chance without synergies
        chance = self.skill.calculate_success_chance(0.5)
        self.assertGreater(chance, 0.4)  # Should be around 50%
        self.assertLess(chance, 0.6)

        # Higher difficulty should reduce chance
        high_difficulty_chance = self.skill.calculate_success_chance(0.9)
        lower_difficulty_chance = self.skill.calculate_success_chance(0.1)
        self.assertLess(high_difficulty_chance, lower_difficulty_chance)

    def test_synergy_bonuses(self):
        """Test synergy bonus calculation"""
        # Create skill with synergies
        synergy_skill = Skill(
            name="Synergy Skill",
            category=SkillCategory.COMBAT,
            description="A skill that synergizes",
            synergies=[
                SynergyBonus(
                    skill_name="Test Skill",
                    bonus_type="success_chance",
                    bonus_value=0.2,
                    description="Test synergy"
                )
            ]
        )

        # Test with synergistic skill
        synergistic_skills = {"Synergy Skill": synergy_skill}
        chance_with_synergy = self.skill.calculate_success_chance(
            0.5,
            synergistic_skills
        )

        # Synergy should increase chance
        base_chance = self.skill.calculate_success_chance(0.5)
        self.assertGreater(chance_with_synergy, base_chance)

    def test_special_abilities(self):
        """Test special ability system"""
        # Create skill with special abilities
        skilled_ability = Skill(
            name="Skilled Ability",
            category=SkillCategory.COMBAT,
            description="Skill with abilities",
            special_abilities=[
                SpecialAbility(
                    name="Test Ability",
                    description="A test special ability",
                    required_level=MasteryLevel.JOURNEYMAN,
                    effect_type="passive",
                    effect_value="Test effect"
                )
            ]
        )

        # Should have no active abilities at start
        self.assertEqual(len(skilled_ability.get_active_abilities()), 0)

        # Progress to Journeyman
        skilled_ability.add_experience(100)  # Journeyman level
        self.assertEqual(skilled_ability.current_level, MasteryLevel.JOURNEYMAN)

        # Should unlock the ability
        self.assertEqual(len(skilled_ability.get_active_abilities()), 1)
        ability = skilled_ability.get_active_abilities()[0]
        self.assertEqual(ability.name, "Test Ability")

    def test_temporary_bonuses(self):
        """Test temporary bonus system"""
        # Add temporary bonus
        self.skill.apply_temporary_bonus(0.2, 5)  # 20% bonus for 5 minutes
        self.assertEqual(self.skill.temporary_bonus, 0.2)

        # Chance should be affected by temporary bonus
        chance_with_bonus = self.skill.calculate_success_chance(0.5)
        chance_without_bonus = self.skill.calculate_success_chance(0.5)

        # Temporarily clear bonus to compare
        self.skill.temporary_bonus = 0.0
        chance_without = self.skill.calculate_success_chance(0.5)

        self.skill.temporary_bonus = 0.2
        chance_with = self.skill.calculate_success_chance(0.5)

        self.assertGreater(chance_with, chance_without)

    def test_skill_progression(self):
        """Test skill progression system"""
        # Add skill to progression
        self.progression.add_skill(self.skill)
        self.assertEqual(len(self.progression.skills), 1)
        self.assertEqual(self.progression.get_skill("Test Skill"), self.skill)

        # Record usage through progression
        result = self.progression.record_skill_usage(
            skill_name="Test Skill",
            success=True,
            difficulty=0.6,
            context="Progression test",
            xp_gained=20
        )

        # Check result
        self.assertIn('skill_name', result)
        self.assertIn('total_xp', result)
        self.assertEqual(result['skill_name'], "Test Skill")
        self.assertGreater(result['total_xp'], 0)

    def test_skill_serialization(self):
        """Test skill serialization and deserialization"""
        # Progress the skill
        self.skill.add_experience(50)
        self.skill.record_usage(True, 0.7, "Serialization test", 25)

        # Serialize to dict
        skill_dict = self.skill.to_dict()
        self.assertIn('name', skill_dict)
        self.assertIn('total_xp', skill_dict)
        self.assertIn('current_level', skill_dict)

        # Deserialize from dict
        restored_skill = Skill.from_dict(skill_dict)
        self.assertEqual(restored_skill.name, self.skill.name)
        self.assertEqual(restored_skill.total_xp, self.skill.total_xp)
        self.assertEqual(restored_skill.current_level, self.skill.current_level)

    def test_performance_metrics(self):
        """Test performance metric calculations"""
        # Add some usage data
        for i in range(10):
            success = i < 7  # 7 successes, 3 failures
            critical = i == 5  # 1 critical success
            xp = 15 + (i * 2)
            self.skill.record_usage(success, 0.6, f"Test {i}", xp, critical)

        # Check metrics
        self.assertEqual(self.skill.total_uses, 10)
        self.assertEqual(self.skill.successful_uses, 7)
        self.assertEqual(self.skill.critical_successes, 1)
        self.assertEqual(self.skill.success_rate, 70.0)
        self.assertEqual(self.skill.critical_success_rate, 10.0)

    def test_cooldown_system(self):
        """Test ability cooldown system"""
        # Create skill with ability that has cooldown
        cooldown_skill = Skill(
            name="Cooldown Skill",
            category=SkillCategory.COMBAT,
            description="Skill with cooldown ability",
            special_abilities=[
                SpecialAbility(
                    name="Cooldown Ability",
                    description="Ability with cooldown",
                    required_level=MasteryLevel.APPRENTICE,
                    effect_type="active",
                    effect_value="Test effect",
                    cooldown=3
                )
            ]
        )

        # Progress to unlock ability
        cooldown_skill.add_experience(25)
        cooldown_skill.update_cooldown()

        # Use ability
        success = cooldown_skill.use_ability("Cooldown Ability")
        self.assertTrue(success)
        self.assertEqual(cooldown_skill.cooldown_remaining, 3)

        # Should not be able to use while on cooldown
        success = cooldown_skill.use_ability("Cooldown Ability")
        self.assertFalse(success)

        # Update cooldown
        cooldown_skill.update_cooldown()
        self.assertEqual(cooldown_skill.cooldown_remaining, 2)

        # Update until cooldown expires
        for _ in range(2):
            cooldown_skill.update_cooldown()
        self.assertEqual(cooldown_skill.cooldown_remaining, 0)

        # Should be usable again
        success = cooldown_skill.use_ability("Cooldown Ability")
        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()