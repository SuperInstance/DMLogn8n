"""
Advanced Features Examples for Progressive Skill Development System

This module demonstrates advanced features including skill trees,
unlock systems, visualization, and complex interactions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, List

from core.skill import Skill, SkillCategory, MasteryLevel, SynergyBonus, SpecialAbility
from core.skill_progression import SkillProgression
from systems.skill_unlock_system import SkillUnlockSystem, SkillTree, UnlockRequirement, RequirementType, SkillNode
from visualization.skill_tree_visualizer import SkillTreeVisualizer, VisualizationOptions, VisualizationFormat
from categories.combat_skills import CombatSkills
from categories.magic_skills import MagicSkills


class AdvancedFeaturesExample:
    """Demonstrates advanced features of the skill development system"""

    def __init__(self):
        self.agent_id = "advanced_agent"
        self.progression = SkillProgression(self.agent_id)
        self.unlock_system = SkillUnlockSystem()
        self.visualizer = SkillTreeVisualizer()

    def run_all_examples(self):
        """Run all advanced feature examples"""
        print("🚀 Progressive Skill Development System - Advanced Features")
        print("=" * 60)

        self.example_1_skill_trees()
        self.example_2_skill_synergies()
        self.example_3_performance_comparison()
        self.example_4_visualization()
        self.example_5_complex_scenarios()

    def example_1_skill_trees(self):
        """Example 1: Creating and managing skill trees"""
        print("\n🌳 Example 1: Skill Trees")
        print("-" * 25)

        # Create a combat skill tree
        combat_tree = self._create_combat_skill_tree()

        print(f"Created skill tree: {combat_tree.name}")
        print(f"Description: {combat_tree.description}")
        print(f"Total skills: {len(combat_tree.nodes)}")
        print(f"Root skills: {combat_tree.root_nodes}")

        # Show skill relationships
        for node_name, node in combat_tree.nodes.items():
            print(f"\nSkill: {node_name}")
            print(f"  Prerequisites: {[req.description for req in node.requirements]}")
            print(f"  Children: {node.child_nodes}")
            print(f"  Unlocked: {node.unlocked}")

        # Check for unlocks
        unlocks = combat_tree.check_unlocks(self.progression)
        print(f"\nAvailable unlocks: {unlocks}")

        # Add to unlock system
        self.unlock_system.add_skill_tree(combat_tree)

    def example_2_skill_synergies(self):
        """Example 2: Skill synergies and combinations"""
        print("\n🔗 Example 2: Skill Synergies")
        print("-" * 30)

        # Create skills with synergies
        weapon_mastery = CombatSkills.create_weapon_mastery()
        targeting_precision = CombatSkills.create_targeting_precision()
        spell_combos = MagicSkills.create_spell_combos()

        self.progression.add_skill(weapon_mastery)
        self.progression.add_skill(targeting_precision)
        self.progression.add_skill(spell_combos)

        # Show synergy information
        print("Synergy Analysis:")
        for skill_name, skill in self.progression.skills.items():
            print(f"\n{skill_name} Synergies:")
            for synergy in skill.synergies:
                print(f"  With {synergy.skill_name}: {synergy.description}")
                print(f"    Type: {synergy.bonus_type}, Value: {synergy.bonus_value}")

        # Calculate synergy bonuses
        synergistic_skills = {
            "Weapon Mastery": weapon_mastery,
            "Targeting Precision": targeting_precision
        }

        synergy_bonuses = targeting_precision.get_synergy_bonuses(synergistic_skills)
        print(f"\nSynergy bonuses for Targeting Precision: {synergy_bonuses}")

        # Simulate combined skill usage
        print(f"\nSimulating combined skill usage:")
        success_chance = targeting_precision.calculate_success_chance(
            difficulty=0.7,
            synergistic_skills=synergistic_skills
        )
        print(f"Targeting Precision success chance with synergies: {success_chance:.1%}")

    def example_3_performance_comparison(self):
        """Example 3: Performance comparison between skills"""
        print("\n📊 Example 3: Performance Comparison")
        print("-" * 35)

        # Create and progress two skills differently
        skill1 = CombatSkills.create_weapon_mastery()
        skill2 = MagicSkills.create_spell_selection()

        # Progress skill1 more than skill2
        self._progress_skill(skill1, successful_uses=15, total_xp=200)
        self._progress_skill(skill2, successful_uses=8, total_xp=100)

        # Compare skills
        from analyzers.performance_analyzer import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer()

        comparison = analyzer.compare_skills(skill1, skill2)
        print(f"Comparison: {comparison.subject_a} vs {comparison.subject_b}")
        print(f"Winner: {comparison.winner}")
        print(f"Summary: {comparison.analysis_summary}")
        print("Recommendations:")
        for rec in comparison.recommendations:
            print(f"  • {rec}")

        # Show detailed metrics
        print(f"\nDetailed Metrics:")
        for metric, (val_a, val_b) in comparison.metrics_comparison.items():
            print(f"  {metric}: {comparison.subject_a}={val_a:.1f}, {comparison.subject_b}={val_b:.1f}")

    def example_4_visualization(self):
        """Example 4: Skill tree visualization"""
        print("\n🎨 Example 4: Skill Tree Visualization")
        print("-" * 36)

        # Create a skill tree
        combat_tree = self._create_combat_skill_tree()

        # Generate different visualization formats
        formats = [VisualizationFormat.JSON, VisualizationFormat.MERMAID, VisualizationFormat.ASCII]

        for fmt in formats:
            print(f"\nGenerating {fmt.name} visualization...")

            options = VisualizationOptions(
                format=fmt,
                show_connections=True,
                show_labels=True,
                show_progress_bars=True
            )

            try:
                viz_data = self.visualizer.visualize_tree(combat_tree, self.progression, options)

                if fmt == VisualizationFormat.JSON:
                    print(f"  Generated JSON with {viz_data['nodes_count']} nodes")
                    # Show first node as example
                    if viz_data['nodes']:
                        print(f"  Example node: {viz_data['nodes'][0]['name']}")
                elif fmt == VisualizationFormat.MERMAID:
                    print(f"  Generated Mermaid diagram:")
                    # Show first few lines
                    lines = viz_data['content'].split('\n')[:5]
                    for line in lines:
                        print(f"    {line}")
                    print("    ...")
                elif fmt == VisualizationFormat.ASCII:
                    print(f"  ASCII Tree:")
                    # Show first few lines
                    lines = viz_data['content'].split('\n')[:8]
                    for line in lines:
                        print(f"    {line}")
                    if len(lines) < len(viz_data['content'].split('\n')):
                        print("    ...")

                print(f"  ✅ Successfully generated {fmt.name} visualization")

            except Exception as e:
                print(f"  ❌ Error generating {fmt.name}: {e}")

    def example_5_complex_scenarios(self):
        """Example 5: Complex skill development scenarios"""
        print("\n🎭 Example 5: Complex Scenarios")
        print("-" * 32)

        # Scenario 1: Party with different specializations
        print("\nScenario 1: Balanced Party Development")
        party_skills = self._create_balanced_party()
        self._analyze_party_capabilities(party_skills)

        # Scenario 2: Skill unlock progression
        print("\nScenario 2: Progressive Skill Unlocking")
        self._simulate_unlock_progression()

        # Scenario 3: Adaptive difficulty
        print("\nScenario 3: Adaptive Difficulty Scaling")
        self._demonstrate_adaptive_difficulty()

    def _create_combat_skill_tree(self) -> SkillTree:
        """Create a combat-focused skill tree"""
        tree = SkillTree("Combat Mastery", "Tree for developing combat expertise")

        # Create skills
        weapon_mastery = CombatSkills.create_weapon_mastery()
        targeting = CombatSkills.create_targeting_precision()
        positioning = CombatSkills.create_positional_awareness()
        tactical_retreat = CombatSkills.create_tactical_retreat()
        flanking = CombatSkills.create_flanking_manuvers()
        critical_strike = CombatSkills.create_critical_strike()

        # Add nodes with prerequisites
        tree.add_skill_node(weapon_mastery, [], is_root=True, position=(0, 0))

        tree.add_skill_node(targeting, [], is_root=True, position=(200, 0))

        tree.add_skill_node(positioning, [], is_root=True, position=(100, -100))

        tree.add_skill_node(flanking, [
            UnlockRequirement(RequirementType.SKILL_LEVEL, "Weapon Mastery:APPRENTICE")
        ], position=(100, 100))

        tree.add_skill_node(tactical_retreat, [
            UnlockRequirement(RequirementType.SKILL_LEVEL, "Positional Awareness:APPRENTICE")
        ], position=(0, 200))

        tree.add_skill_node(critical_strike, [
            UnlockRequirement(RequirementType.SKILL_LEVEL, "Targeting Precision:JOURNEYMAN"),
            UnlockRequirement(RequirementType.SKILL_LEVEL, "Weapon Mastery:JOURNEYMAN")
        ], position=(200, 100))

        # Add skills to progression
        for skill in [weapon_mastery, targeting, positioning, flanking, tactical_retreat, critical_strike]:
            self.progression.add_skill(skill)

        return tree

    def _progress_skill(self, skill: Skill, successful_uses: int, total_xp: int):
        """Helper method to progress a skill"""
        skill.add_experience(total_xp)
        skill.successful_uses = successful_uses
        skill.total_uses = successful_uses + (successful_uses // 3)  # Add some failures

    def _create_balanced_party(self) -> Dict[str, SkillProgression]:
        """Create a party with different specializations"""
        party = {}

        # Fighter (Combat focused)
        fighter_progression = SkillProgression("fighter")
        combat_skills = CombatSkills.create_all_combat_skills()[:5]  # Top 5 combat skills
        for skill in combat_skills:
            fighter_progression.add_skill(skill)
            self._progress_skill(skill, successful_uses=20, total_xp=300)
        party["Fighter"] = fighter_progression

        # Wizard (Magic focused)
        wizard_progression = SkillProgression("wizard")
        magic_skills = MagicSkills.create_all_magic_skills()[:5]
        for skill in magic_skills:
            wizard_progression.add_skill(skill)
            self._progress_skill(skill, successful_uses=15, total_xp=250)
        party["Wizard"] = wizard_progression

        # Rogue (Exploration focused)
        rogue_progression = SkillProgression("rogue")
        from categories.exploration_skills import ExplorationSkills
        exploration_skills = ExplorationSkills.create_all_exploration_skills()[:5]
        for skill in exploration_skills:
            rogue_progression.add_skill(skill)
            self._progress_skill(skill, successful_uses=18, total_xp=280)
        party["Rogue"] = rogue_progression

        return party

    def _analyze_party_capabilities(self, party_skills: Dict[str, SkillProgression]):
        """Analyze party capabilities"""
        print("Party Analysis:")
        for member, progression in party_skills.items():
            stats = progression.get_development_stats()
            print(f"\n{member}:")
            print(f"  Total skills: {stats.total_skills_learned}")
            print(f"  Master skills: {stats.master_level_skills}")
            print(f"  Total XP: {stats.total_xp_earned}")
            print(f"  Primary focus: {stats.most_developed_category.value}")
            print(f"  Favorite skill: {stats.favorite_skill}")

    def _simulate_unlock_progression(self):
        """Simulate progressive skill unlocking"""
        tree = self._create_combat_skill_tree()

        print(f"Starting with {len([s for s in self.progression.skills.values() if s.total_xp == 0])} unprogressed skills")

        # Progress root skills first
        for root_name in tree.root_nodes:
            if root_name in self.progression.skills:
                skill = self.progression.skills[root_name]
                skill.add_experience(50)  # Apprentice level
                print(f"Progressed {root_name} to {skill.current_level.name}")

        # Check for unlocks
        unlocks = tree.check_unlocks(self.progression)
        print(f"New unlocks available: {unlocks}")

        # Continue progression
        for skill_name in unlocks:
            if skill_name in self.progression.skills:
                skill = self.progression.skills[skill_name]
                skill.add_experience(100)
                tree.unlock_skill(skill_name)
                print(f"Unlocked and progressed {skill_name}")

    def _demonstrate_adaptive_difficulty(self):
        """Demonstrate adaptive difficulty based on skill level"""
        skill = self.progression.get_skill("Weapon Mastery")
        if not skill:
            skill = CombatSkills.create_weapon_mastery()
            self.progression.add_skill(skill)

        print(f"Adaptive difficulty for {skill.name}:")

        for level in [MasteryLevel.NOVICE, MasteryLevel.APPRENTICE, MasteryLevel.JOURNEYMAN, MasteryLevel.EXPERT]:
            skill.current_level = level

            from calculators.experience_calculator import ExperienceCalculator, XPContext
            calc = ExperienceCalculator()

            # Calculate DC based on skill level
            base_difficulty = 0.3 + (level.value * 0.15)
            context = XPContext(
                base_difficulty=base_difficulty,
                actual_difficulty=base_difficulty,
                is_combat=True
            )

            xp, _ = calc.calculate_experience(skill, success=True, context=context)
            success_chance = skill.calculate_success_chance(base_difficulty)

            print(f"  {level.name}:")
            print(f"    Recommended difficulty: {base_difficulty:.2f}")
            print(f"    Success chance: {success_chance:.1%}")
            print(f"    XP reward: {xp}")


def main():
    """Run advanced features examples"""
    example = AdvancedFeaturesExample()
    example.run_all_examples()


if __name__ == "__main__":
    main()