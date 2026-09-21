"""
Basic Usage Examples for Progressive Skill Development System

This module demonstrates fundamental usage of the skill development system
including skill creation, experience tracking, and progression.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.skill import Skill, SkillCategory, MasteryLevel
from core.skill_progression import SkillProgression
from calculators.experience_calculator import ExperienceCalculator, XPContext
from analyzers.performance_analyzer import PerformanceAnalyzer
from categories.combat_skills import CombatSkills
from categories.social_skills import SocialSkills


class BasicUsageExample:
    """Demonstrates basic usage of the skill development system"""

    def __init__(self):
        self.agent_id = "example_agent"
        self.progression = SkillProgression(self.agent_id)
        self.xp_calculator = ExperienceCalculator()
        self.analyzer = PerformanceAnalyzer()

    def run_all_examples(self):
        """Run all basic usage examples"""
        print("🎮 Progressive Skill Development System - Basic Usage Examples")
        print("=" * 60)

        self.example_1_create_skills()
        self.example_2_track_progression()
        self.example_3_calculate_experience()
        self.example_4_analyze_performance()
        self.example_5_skill_mastery_progression()

    def example_1_create_skills(self):
        """Example 1: Creating skills and adding them to progression"""
        print("\n📚 Example 1: Creating Skills")
        print("-" * 30)

        # Create some combat and social skills
        weapon_mastery = CombatSkills.create_weapon_mastery()
        persuasion = SocialSkills.create_persuasion()

        print(f"Created skill: {weapon_mastery.name}")
        print(f"  Category: {weapon_mastery.category.value}")
        print(f"  Description: {weapon_mastery.description}")
        print(f"  Starting level: {weapon_mastery.current_level.name}")
        print(f"  Special abilities: {[ability.name for ability in weapon_mastery.special_abilities]}")

        print(f"\nCreated skill: {persuasion.name}")
        print(f"  Category: {persuasion.category.value}")
        print(f"  Synergies: {[synergy.skill_name for synergy in persuasion.synergies]}")

        # Add skills to progression
        self.progression.add_skill(weapon_mastery)
        self.progression.add_skill(persuasion)

        print(f"\n✅ Added {len(self.progression.skills)} skills to progression system")

    def example_2_track_progression(self):
        """Example 2: Tracking skill progression"""
        print("\n📈 Example 2: Tracking Skill Progression")
        print("-" * 35)

        # Get a skill from progression
        weapon_skill = self.progression.get_skill("Weapon Mastery")
        if weapon_skill:
            print(f"Skill: {weapon_skill.name}")
            print(f"  Current level: {weapon_skill.current_level.name}")
            print(f"  Total XP: {weapon_skill.total_xp}")
            print(f"  XP to next level: {weapon_skill.xp_to_next_level}")
            print(f"  Success rate: {weapon_skill.success_rate:.1f}%")
            print(f"  Total uses: {weapon_skill.total_uses}")

        # Get overall progression statistics
        stats = self.progression.get_development_stats()
        print(f"\n📊 Overall Progression Stats:")
        print(f"  Total skills: {stats.total_skills_learned}")
        print(f"  Master-level skills: {stats.master_level_skills}")
        print(f"  Total XP earned: {stats.total_xp_earned}")
        print(f"  Development rate: {stats.development_rate:.1f} XP/day")
        print(f"  Favorite skill: {stats.favorite_skill}")

    def example_3_calculate_experience(self):
        """Example 3: Experience calculation with multipliers"""
        print("\n⚡ Example 3: Experience Calculation")
        print("-" * 35)

        # Get skill and create context
        weapon_skill = self.progression.get_skill("Weapon Mastery")
        if not weapon_skill:
            return

        # Create context for skill usage
        context = XPContext(
            base_difficulty=0.6,
            actual_difficulty=0.7,
            is_first_use=False,
            is_critical_success=False,
            time_of_day=datetime.now().time(),
            is_combat=True,
            enemy_level=3
        )

        # Calculate experience for successful use
        xp_gained, breakdown = self.xp_calculator.calculate_experience(
            weapon_skill, success=True, context=context
        )

        print(f"Skill Usage: {weapon_skill.name} (Success)")
        print(f"  Base XP: {breakdown['base_xp']}")
        print(f"  Total XP: {breakdown['total_xp']}")
        print(f"  Modifiers applied:")
        for modifier, description in breakdown['modifiers'].items():
            print(f"    {modifier}: {description}")

        # Calculate experience for critical success
        context_critical = XPContext(
            base_difficulty=0.6,
            actual_difficulty=0.8,
            is_critical_success=True,
            is_combat=True,
            enemy_level=5
        )

        xp_critical, breakdown_critical = self.xp_calculator.calculate_experience(
            weapon_skill, success=True, context=context_critical
        )

        print(f"\nSkill Usage: {weapon_skill.name} (Critical Success)")
        print(f"  Total XP: {breakdown_critical['total_xp']} (vs {xp_gained} normal)")
        print(f"  Critical bonus: +{breakdown_critical['total_xp'] - xp_gained} XP")

    def example_4_analyze_performance(self):
        """Example 4: Performance analysis"""
        print("\n📊 Example 4: Performance Analysis")
        print("-" * 32)

        # Get a skill
        weapon_skill = self.progression.get_skill("Weapon Mastery")
        if not weapon_skill:
            return

        # Simulate some skill usage for analysis
        self._simulate_skill_usage(weapon_skill, uses=10)

        # Analyze performance
        metrics = self.analyzer.analyze_skill_performance(weapon_skill, self.progression)

        print(f"Performance Analysis for {metrics.skill_name}:")
        print(f"  Total uses: {metrics.total_uses}")
        print(f"  Success rate: {metrics.success_rate:.1f}%")
        print(f"  Critical success rate: {metrics.critical_success_rate:.1f}%")
        print(f"  Average difficulty: {metrics.average_difficulty:.2f}")
        print(f"  Average XP per use: {metrics.average_xp_per_use:.1f}")
        print(f"  Usage frequency: {metrics.usage_frequency:.2f} uses/day")
        print(f"  Effectiveness score: {metrics.effectiveness_score:.1f}/100")
        print(f"  Performance tier: {metrics.performance_tier.name}")
        print(f"  Trend: {metrics.trend_direction.name}")

        # Get detailed effectiveness analysis
        effectiveness = self.analyzer.analyze_skill_effectiveness(weapon_skill, self.progression)
        print(f"\nStrengths: {effectiveness.strengths}")
        print(f"Weaknesses: {effectiveness.weaknesses}")
        print(f"Improvement areas: {effectiveness.improvement_areas}")

    def example_5_skill_mastery_progression(self):
        """Example 5: Skill mastery progression"""
        print("\n🏆 Example 5: Skill Mastery Progression")
        print("-" * 40)

        # Get a skill
        persuasion_skill = self.progression.get_skill("Persuasion")
        if not persuasion_skill:
            return

        print(f"Progressing {persuasion_skill.name} through mastery levels:")
        print(f"Starting level: {persuasion_skill.current_level.name} ({persuasion_skill.total_xp} XP)")

        # Simulate progression through levels
        target_xp_values = [25, 100, 400, 1600]  # XP thresholds for each level

        for target_xp in target_xp_values:
            # Add enough XP to reach next level
            xp_to_add = target_xp - persuasion_skill.total_xp
            if xp_to_add > 0:
                level_up = persuasion_skill.add_experience(xp_to_add)

                if level_up:
                    print(f"  🎯 Level Up! {persuasion_skill.current_level.name} ({persuasion_skill.total_xp} XP)")
                    print(f"     Bonus dice: {persuasion_skill.current_level.bonus_dice}")
                    print(f"     XP multiplier: {persuasion_skill.current_level.multiplier}x")

                    # Show unlocked abilities
                    active_abilities = persuasion_skill.get_active_abilities()
                    if active_abilities:
                        print(f"     Unlocked abilities: {[ability.name for ability in active_abilities]}")

        print(f"\nFinal status: {persuasion_skill.current_level.name} ({persuasion_skill.total_xp} XP)")

    def _simulate_skill_usage(self, skill: Skill, uses: int):
        """Simulate skill usage for testing purposes"""
        import random
        from datetime import datetime, timedelta

        for i in range(uses):
            # Simulate varying success rates based on mastery
            success_chance = 0.3 + (skill.current_level.value * 0.1)
            success = random.random() < success_chance
            critical = success and random.random() < 0.1

            difficulty = random.uniform(0.3, 0.9)
            xp = int(10 + (difficulty * 20))

            # Create context
            context = XPContext(
                base_difficulty=0.5,
                actual_difficulty=difficulty,
                is_critical_success=critical,
                is_combat=skill.category == SkillCategory.COMBAT,
                is_social=skill.category == SkillCategory.SOCIAL
            )

            # Calculate and record XP
            xp_gained, _ = self.xp_calculator.calculate_experience(skill, success, context)
            skill.record_usage(success, difficulty, f"Test usage {i+1}", xp_gained, critical)


def main():
    """Run basic usage examples"""
    example = BasicUsageExample()
    example.run_all_examples()


if __name__ == "__main__":
    main()