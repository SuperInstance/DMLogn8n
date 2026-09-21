"""
Skill Unlock System with prerequisites for DMlogn8n

This module manages the unlocking of skills based on prerequisites,
experience requirements, and other conditions.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..core.skill import Skill, SkillCategory, MasteryLevel
from ..core.skill_progression import SkillProgression


class RequirementType(Enum):
    """Types of unlock requirements"""
    SKILL_LEVEL = auto()
    TOTAL_XP = auto()
    MASTERY_COUNT = auto()
    CATEGORY_XP = auto()
    QUEST_COMPLETE = auto()
    LEVEL_REACHED = auto()
    ACHIEVEMENT = auto()
    TIME_PLAYED = auto()
    COMBAT_VICTORIES = auto()
    SOCIAL_SUCCESSES = auto()
    MAGIC_SPELLS_LEARNED = auto()
    CUSTOM = auto()


class RequirementOperator(Enum):
    """Operators for combining requirements"""
    AND = auto()
    OR = auto()


@dataclass
class UnlockRequirement:
    """Represents a single requirement for unlocking a skill"""
    type: RequirementType
    value: Union[str, int, float, dict]
    operator: Optional[str] = None  # ">=", "==", "<=", etc.
    description: str = ""
    optional: bool = False

    def check_requirement(self, progression: SkillProgression, context: Optional[Dict] = None) -> bool:
        """Check if this requirement is met"""
        context = context or {}

        if self.type == RequirementType.SKILL_LEVEL:
            skill_name, required_level = self.value.split(":")
            skill = progression.get_skill(skill_name)
            if not skill:
                return False
            return skill.current_level.name >= required_level

        elif self.type == RequirementType.TOTAL_XP:
            total_xp = sum(skill.total_xp for skill in progression.skills.values())
            return self._compare_values(total_xp, self.value)

        elif self.type == RequirementType.MASTERY_COUNT:
            master_count = len(progression.get_mastered_skills())
            return self._compare_values(master_count, self.value)

        elif self.type == RequirementType.CATEGORY_XP:
            category_name, required_xp = self.value.split(":")
            category = SkillCategory[category_name]
            category_xp = sum(
                skill.total_xp for skill in progression.skills.values()
                if skill.category == category
            )
            return category_xp >= int(required_xp)

        elif self.type == RequirementType.QUEST_COMPLETE:
            return context.get('completed_quests', set()).issuperset({self.value})

        elif self.type == RequirementType.LEVEL_REACHED:
            return context.get('character_level', 1) >= self.value

        elif self.type == RequirementType.ACHIEVEMENT:
            return context.get('achievements', set()).issuperset({self.value})

        elif self.type == RequirementType.TIME_PLAYED:
            # Convert hours to seconds for comparison
            played_seconds = context.get('time_played_seconds', 0)
            required_seconds = self.value * 3600
            return played_seconds >= required_seconds

        elif self.type == RequirementType.COMBAT_VICTORIES:
            return context.get('combat_victories', 0) >= self.value

        elif self.type == RequirementType.SOCIAL_SUCCESSES:
            return context.get('social_successes', 0) >= self.value

        elif self.type == RequirementType.MAGIC_SPELLS_LEARNED:
            return context.get('spells_learned', 0) >= self.value

        elif self.type == RequirementType.CUSTOM:
            # Custom logic would be implemented via a callback function
            return context.get('custom_checks', {}).get(self.value, False)

        return False

    def _compare_values(self, actual: Union[int, float], required: Union[int, float]) -> bool:
        """Compare actual value with required value using operator"""
        if not self.operator:
            return actual >= required

        if self.operator == ">=":
            return actual >= required
        elif self.operator == "==":
            return actual == required
        elif self.operator == "<=":
            return actual <= required
        elif self.operator == ">":
            return actual > required
        elif self.operator == "<":
            return actual < required

        return actual >= required


@dataclass
class SkillNode:
    """A node in the skill tree representing a skill"""
    skill: Skill
    requirements: List[UnlockRequirement]
    requirement_operator: RequirementOperator = RequirementOperator.AND
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    parent_nodes: List[str] = field(default_factory=list)
    child_nodes: List[str] = field(default_factory=list)
    position: Tuple[int, int] = (0, 0)  # (x, y) position in tree
    is_root: bool = False

    def check_unlock(self, progression: SkillProgression, context: Optional[Dict] = None) -> bool:
        """Check if this skill node can be unlocked"""
        if self.unlocked:
            return True

        # Check if all requirements are met
        if self.requirement_operator == RequirementOperator.AND:
            all_met = all(
                req.check_requirement(progression, context) or req.optional
                for req in self.requirements
            )
            if not all_met:
                return False
        else:  # OR
            any_met = any(
                req.check_requirement(progression, context)
                for req in self.requirements
            )
            if not any_met:
                return False

        # Check if parent nodes are unlocked (if any)
        for parent_name in self.parent_nodes:
            # This would be handled by the SkillTree class
            pass

        return True

    def get_progress_percentage(self, progression: SkillProgression, context: Optional[Dict] = None) -> float:
        """Get percentage progress towards unlocking this skill"""
        if self.unlocked:
            return 100.0

        if not self.requirements:
            return 0.0

        if self.requirement_operator == RequirementOperator.AND:
            met_count = sum(
                1 for req in self.requirements
                if req.check_requirement(progression, context) or req.optional
            )
            return (met_count / len(self.requirements)) * 100.0
        else:  # OR
            # For OR requirements, return the highest individual progress
            return max(
                100.0 if req.check_requirement(progression, context) else 0.0
                for req in self.requirements
            )


class SkillTree:
    """Manages the skill tree structure and unlocking logic"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: Dict[str, SkillNode] = {}
        self.root_nodes: List[str] = []
        self.unlock_history: List[Tuple[str, datetime]] = []

    def add_skill_node(
        self,
        skill: Skill,
        requirements: List[UnlockRequirement],
        requirement_operator: RequirementOperator = RequirementOperator.AND,
        parent_nodes: Optional[List[str]] = None,
        position: Tuple[int, int] = (0, 0),
        is_root: bool = False
    ) -> None:
        """Add a skill node to the tree"""
        node = SkillNode(
            skill=skill,
            requirements=requirements,
            requirement_operator=requirement_operator,
            parent_nodes=parent_nodes or [],
            position=position,
            is_root=is_root
        )

        self.nodes[skill.name] = node

        if is_root:
            self.root_nodes.append(skill.name)

        # Update parent-child relationships
        if parent_nodes:
            for parent_name in parent_nodes:
                if parent_name in self.nodes:
                    self.nodes[parent_name].child_nodes.append(skill.name)

    def check_unlocks(self, progression: SkillProgression, context: Optional[Dict] = None) -> List[str]:
        """
        Check for and unlock any eligible skills

        Returns:
            List of newly unlocked skill names
        """
        newly_unlocked = []

        for node_name, node in self.nodes.items():
            if not node.unlocked:
                # Check if parent nodes are unlocked
                parents_unlocked = all(
                    self.nodes[parent].unlocked if parent in self.nodes else True
                    for parent in node.parent_nodes
                )

                if parents_unlocked and node.check_unlock(progression, context):
                    self.unlock_skill(node_name)
                    newly_unlocked.append(node_name)

        return newly_unlocked

    def unlock_skill(self, skill_name: str) -> bool:
        """
        Manually unlock a skill

        Returns:
            bool: True if skill was unlocked successfully
        """
        if skill_name not in self.nodes:
            return False

        node = self.nodes[skill_name]
        if node.unlocked:
            return False

        node.unlocked = True
        node.unlocked_at = datetime.now()
        self.unlock_history.append((skill_name, node.unlocked_at))

        return True

    def is_skill_unlocked(self, skill_name: str) -> bool:
        """Check if a skill is unlocked"""
        return self.nodes.get(skill_name, SkillNode(None, [])).unlocked

    def get_unlockable_skills(self, progression: SkillProgression, context: Optional[Dict] = None) -> List[str]:
        """Get list of skills that can be unlocked but aren't yet"""
        unlockable = []

        for node_name, node in self.nodes.items():
            if not node.unlocked and node.check_unlock(progression, context):
                unlockable.append(node_name)

        return unlockable

    def get_skill_requirements(self, skill_name: str) -> List[UnlockRequirement]:
        """Get requirements for a specific skill"""
        if skill_name in self.nodes:
            return self.nodes[skill_name].requirements
        return []

    def get_skill_progress(self, skill_name: str, progression: SkillProgression, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get detailed progress information for a skill"""
        if skill_name not in self.nodes:
            return {}

        node = self.nodes[skill_name]
        requirements_progress = []

        for req in node.requirements:
            progress = {
                'description': req.description,
                'met': req.check_requirement(progression, context),
                'optional': req.optional,
                'type': req.type.name,
                'value': req.value
            }
            requirements_progress.append(progress)

        return {
            'skill_name': skill_name,
            'unlocked': node.unlocked,
            'unlocked_at': node.unlocked_at.isoformat() if node.unlocked_at else None,
            'progress_percentage': node.get_progress_percentage(progression, context),
            'requirements': requirements_progress,
            'requirement_operator': node.requirement_operator.name,
            'parent_nodes': node.parent_nodes,
            'child_nodes': node.child_nodes
        }

    def get_tree_structure(self) -> Dict[str, Any]:
        """Get the complete tree structure for visualization"""
        structure = {
            'name': self.name,
            'description': self.description,
            'nodes': {},
            'connections': []
        }

        for node_name, node in self.nodes.items():
            structure['nodes'][node_name] = {
                'skill_name': node.skill.name if node.skill else node_name,
                'category': node.skill.category.value if node.skill else 'UNKNOWN',
                'position': node.position,
                'unlocked': node.unlocked,
                'is_root': node.is_root,
                'progress': 0.0  # This would be calculated with progression data
            }

            # Add connections to children
            for child_name in node.child_nodes:
                structure['connections'].append({
                    'from': node_name,
                    'to': child_name
                })

        return structure

    def get_unlock_path(self, skill_name: str) -> List[str]:
        """
        Get the path of skills needed to unlock a specific skill

        Returns:
            List of skill names in unlock order
        """
        if skill_name not in self.nodes:
            return []

        path = []
        visited = set()

        def dfs(node_name: str) -> None:
            if node_name in visited or node_name not in self.nodes:
                return

            visited.add(node_name)
            node = self.nodes[node_name]

            # Add parents first
            for parent_name in node.parent_nodes:
                dfs(parent_name)

            # Add this node
            path.append(node_name)

        dfs(skill_name)
        return path

    def get_prerequisite_summary(self, skill_name: str, progression: SkillProgression, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get a human-readable summary of prerequisites for a skill"""
        if skill_name not in self.nodes:
            return {'error': f'Skill {skill_name} not found in tree'}

        node = self.nodes[skill_name]
        requirements_summary = []

        for req in node.requirements:
            is_met = req.check_requirement(progression, context)
            requirements_summary.append({
                'description': req.description,
                'met': is_met,
                'type': req.type.name,
                'value': req.value,
                'optional': req.optional
            })

        return {
            'skill_name': skill_name,
            'can_unlock': node.check_unlock(progression, context),
            'progress_percentage': node.get_progress_percentage(progression, context),
            'requirements': requirements_summary,
            'requirement_operator': node.requirement_operator.name,
            'parent_skills': [
                f"{parent} ({'Unlocked' if self.nodes[parent].unlocked else 'Locked'})"
                for parent in node.parent_nodes
                if parent in self.nodes
            ]
        }


class SkillUnlockSystem:
    """
    Main system for managing skill unlocking across multiple skill trees

    This system coordinates multiple skill trees, handles unlock checking,
    and provides analytics about the unlocking progress.
    """

    def __init__(self):
        self.skill_trees: Dict[str, SkillTree] = {}
        self.global_unlock_history: List[Tuple[str, str, datetime]] = []  # (tree_name, skill_name, timestamp)
        self.unlock_callbacks: List[callable] = []

    def add_skill_tree(self, skill_tree: SkillTree) -> None:
        """Add a skill tree to the system"""
        self.skill_trees[skill_tree.name] = skill_tree

    def remove_skill_tree(self, tree_name: str) -> bool:
        """Remove a skill tree from the system"""
        if tree_name in self.skill_trees:
            del self.skill_trees[tree_name]
            return True
        return False

    def check_all_unlocks(self, progression: SkillProgression, context: Optional[Dict] = None) -> Dict[str, List[str]]:
        """
        Check for unlocks across all skill trees

        Returns:
            Dict mapping tree names to lists of newly unlocked skills
        """
        results = {}

        for tree_name, tree in self.skill_trees.items():
            newly_unlocked = tree.check_unlocks(progression, context)
            if newly_unlocked:
                results[tree_name] = newly_unlocked

                # Add to global history
                for skill_name in newly_unlocked:
                    self.global_unlock_history.append((tree_name, skill_name, datetime.now()))

                    # Trigger callbacks
                    for callback in self.unlock_callbacks:
                        try:
                            callback(tree_name, skill_name, progression)
                        except Exception as e:
                            print(f"Error in unlock callback: {e}")

        return results

    def get_all_unlockable_skills(self, progression: SkillProgression, context: Optional[Dict] = None) -> Dict[str, List[str]]:
        """Get all unlockable skills across all trees"""
        unlockable = {}

        for tree_name, tree in self.skill_trees.items():
            unlockable[tree_name] = tree.get_unlockable_skills(progression, context)

        return unlockable

    def get_unlock_summary(self, progression: SkillProgression, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Get comprehensive unlock summary across all trees"""
        summary = {
            'total_trees': len(self.skill_trees),
            'total_skills': sum(len(tree.nodes) for tree in self.skill_trees.values()),
            'unlocked_skills': 0,
            'unlockable_skills': 0,
            'trees': {}
        }

        for tree_name, tree in self.skill_trees.items():
            unlocked_count = sum(1 for node in tree.nodes.values() if node.unlocked)
            unlockable_count = len(tree.get_unlockable_skills(progression, context))

            summary['unlocked_skills'] += unlocked_count
            summary['unlockable_skills'] += unlockable_count

            summary['trees'][tree_name] = {
                'total_skills': len(tree.nodes),
                'unlocked_skills': unlocked_count,
                'unlockable_skills': unlockable_count,
                'unlock_percentage': (unlocked_count / len(tree.nodes) * 100.0) if tree.nodes else 0
            }

        summary['overall_unlock_percentage'] = (
            summary['unlocked_skills'] / summary['total_skills'] * 100.0
            if summary['total_skills'] > 0 else 0
        )

        return summary

    def register_unlock_callback(self, callback: callable) -> None:
        """Register a callback to be called when a skill is unlocked"""
        self.unlock_callbacks.append(callback)

    def get_recent_unlocks(self, hours: int = 24) -> List[Tuple[str, str, datetime]]:
        """Get recent unlocks within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            (tree, skill, timestamp) for tree, skill, timestamp in self.global_unlock_history
            if timestamp >= cutoff_time
        ]

    def find_skill_tree(self, skill_name: str) -> Optional[str]:
        """Find which tree contains a specific skill"""
        for tree_name, tree in self.skill_trees.items():
            if skill_name in tree.nodes:
                return tree_name
        return None

    def export_tree_data(self, tree_name: str) -> Optional[Dict[str, Any]]:
        """Export tree data for external use"""
        if tree_name not in self.skill_trees:
            return None

        tree = self.skill_trees[tree_name]
        return {
            'tree_structure': tree.get_tree_structure(),
            'unlock_history': [
                (skill, timestamp.isoformat()) for skill, timestamp in tree.unlock_history
            ]
        }