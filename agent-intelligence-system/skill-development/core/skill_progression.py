"""
Skill Progression tracking and management for DMlogn8n

This module handles the overall progression of multiple skills,
including cross-skill interactions and mastery development.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .skill import Skill, SkillCategory, MasteryLevel, SkillUsageRecord


@dataclass
class ProgressionMilestone:
    """Represents a milestone in skill development"""
    name: str
    description: str
    required_skills: Dict[str, MasteryLevel]
    total_xp_requirement: int
    rewards: List[str]
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None


@dataclass
class SkillDevelopmentStats:
    """Statistics about overall skill development"""
    total_skills_learned: int
    master_level_skills: int
    total_xp_earned: int
    most_developed_category: SkillCategory
    development_rate: float  # XP per day
    favorite_skill: str
    improvement_areas: List[str]


class SkillProgression:
    """
    Manages the progression of multiple skills for an agent

    This class coordinates the development of multiple skills,
    tracks milestones, and provides analytics about overall
    skill development patterns.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.skills: Dict[str, Skill] = {}
        self.milestones: List[ProgressionMilestone] = []
        self.start_date = datetime.now()
        self.last_activity = datetime.now()

        # Development tracking
        self.daily_xp_history: Dict[str, int] = defaultdict(int)
        self.category_focus: Dict[SkillCategory, float] = defaultdict(float)
        self.skill_combinations: Dict[Tuple[str, str], int] = defaultdict(int)

        # Performance analytics
        self.learning_patterns: Dict[str, Any] = {}
        self.development_velocity: List[float] = []

    def add_skill(self, skill: Skill) -> None:
        """Add a new skill to track"""
        self.skills[skill.name] = skill
        self._update_category_focus(skill)

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self.skills.get(skill_name)

    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """Get all skills in a specific category"""
        return [skill for skill in self.skills.values() if skill.category == category]

    def get_mastered_skills(self) -> List[Skill]:
        """Get all skills at master level"""
        return [skill for skill in self.skills.values() if skill.current_level == MasteryLevel.MASTER]

    def record_skill_usage(
        self,
        skill_name: str,
        success: bool,
        difficulty: float,
        context: str,
        xp_gained: int,
        critical_success: bool = False,
        related_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Record usage of a skill and handle cross-skill interactions

        Args:
            skill_name: Name of the primary skill used
            success: Whether the skill use was successful
            difficulty: Difficulty of the skill check
            context: Description of the usage context
            xp_gained: Base experience gained
            critical_success: Whether this was a critical success
            related_skills: Other skills used in combination

        Returns:
            Dict with results including XP gained and level changes
        """
        if skill_name not in self.skills:
            raise ValueError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]

        # Calculate synergy bonuses
        synergistic_skills = {
            name: self.skills[name] for name in (related_skills or [])
            if name in self.skills
        }

        synergy_bonuses = skill.get_synergy_bonuses(synergistic_skills)

        # Adjust XP based on synergies
        bonus_xp = 0
        if 'xp' in synergy_bonuses:
            bonus_xp = int(xp_gained * synergy_bonuses['xp'])

        # Record the usage
        level_up = skill.record_usage(
            success=success,
            difficulty=difficulty,
            context=context,
            xp_gained=xp_gained,
            critical_success=critical_success
        )

        # Track skill combinations
        if related_skills:
            for related in related_skills:
                if related in self.skills:
                    combo_key = tuple(sorted([skill_name, related]))
                    self.skill_combinations[combo_key] += 1

        # Update daily XP tracking
        today = datetime.now().strftime('%Y-%m-%d')
        total_xp = xp_gained + bonus_xp
        self.daily_xp_history[today] += total_xp

        # Update activity tracking
        self.last_activity = datetime.now()

        # Check for milestone unlocks
        new_milestones = self._check_milestones()

        # Update category focus
        self._update_category_focus(skill)

        return {
            'skill_name': skill_name,
            'base_xp': xp_gained,
            'bonus_xp': bonus_xp,
            'total_xp': total_xp,
            'level_up': level_up,
            'new_level': skill.current_level.name,
            'synergy_bonuses': synergy_bonuses,
            'milestones_unlocked': new_milestones
        }

    def get_development_stats(self) -> SkillDevelopmentStats:
        """Get comprehensive development statistics"""
        total_xp = sum(skill.total_xp for skill in self.skills.values())
        master_skills = self.get_mastered_skills()

        # Calculate development rate (XP per day)
        days_active = max(1, (datetime.now() - self.start_date).days)
        development_rate = total_xp / days_active

        # Find most developed category
        category_xp = defaultdict(int)
        for skill in self.skills.values():
            category_xp[skill.category] += skill.total_xp

        most_developed_category = max(category_xp, key=category_xp.get) if category_xp else SkillCategory.COMBAT

        # Find favorite skill (most used)
        favorite_skill = max(self.skills, key=lambda s: self.skills[s].total_uses) if self.skills else "None"

        # Identify improvement areas (skills with low success rates)
        improvement_areas = [
            skill.name for skill in self.skills.values()
            if skill.total_uses > 5 and skill.success_rate < 40
        ]

        return SkillDevelopmentStats(
            total_skills_learned=len(self.skills),
            master_level_skills=len(master_skills),
            total_xp_earned=total_xp,
            most_developed_category=most_developed_category,
            development_rate=development_rate,
            favorite_skill=favorite_skill,
            improvement_areas=improvement_areas
        )

    def get_learning_velocity(self, days: int = 7) -> List[float]:
        """Calculate learning velocity over recent days"""
        velocity = []
        end_date = datetime.now()

        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_xp = self.daily_xp_history.get(date, 0)
            velocity.append(daily_xp)

        return list(reversed(velocity))  # Chronological order

    def get_skill_synergies(self) -> Dict[str, Dict[str, float]]:
        """Get calculated synergy values between all skills"""
        synergies = {}

        for skill_name, skill in self.skills.items():
            skill_synergies = {}
            for synergy in skill.synergies:
                if synergy.skill_name in self.skills:
                    ally_skill = self.skills[synergy.skill_name]
                    bonus_value = synergy.bonus_value * (ally_skill.total_xp / 1000.0)
                    skill_synergies[synergy.skill_name] = {
                        'bonus_type': synergy.bonus_type,
                        'bonus_value': bonus_value,
                        'description': synergy.description
                    }
            synergies[skill_name] = skill_synergies

        return synergies

    def get_recommended_skills(self) -> List[Tuple[str, float]]:
        """
        Recommend skills to develop based on current patterns

        Returns:
            List of (skill_name, recommendation_score) tuples
        """
        recommendations = []

        # Analyze skill combinations
        for (skill1, skill2), frequency in self.skill_combinations.items():
            if frequency > 3:  # Frequently used combination
                # Look for skills that would complement this combo
                for skill_name, skill in self.skills.items():
                    if skill_name not in [skill1, skill2]:
                        score = self._calculate_recommendation_score(skill, [skill1, skill2])
                        if score > 0.3:
                            recommendations.append((skill_name, score))

        # Sort by recommendation score
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return recommendations[:5]  # Top 5 recommendations

    def add_milestone(self, milestone: ProgressionMilestone) -> None:
        """Add a new milestone to track"""
        self.milestones.append(milestone)

    def check_milestone_progress(self, milestone_name: str) -> float:
        """
        Check progress towards a specific milestone

        Returns:
            float: Progress percentage (0.0 to 1.0)
        """
        milestone = next((m for m in self.milestones if m.name == milestone_name), None)
        if not milestone:
            return 0.0

        # Check skill requirements
        skill_progress = 0.0
        for skill_name, required_level in milestone.required_skills.items():
            if skill_name in self.skills:
                current_level = self.skills[skill_name].current_level
                required_index = list(MasteryLevel).index(required_level)
                current_index = list(MasteryLevel).index(current_level)
                skill_progress += min(1.0, current_index / required_index)
            else:
                skill_progress += 0.0

        skill_progress /= len(milestone.required_skills) if milestone.required_skills else 1

        # Check XP requirement
        total_xp = sum(skill.total_xp for skill in self.skills.values())
        xp_progress = min(1.0, total_xp / milestone.total_xp_requirement)

        # Overall progress (weighted average)
        overall_progress = (skill_progress * 0.7) + (xp_progress * 0.3)

        return overall_progress

    def get_unlocked_milestones(self) -> List[ProgressionMilestone]:
        """Get all unlocked milestones"""
        return [m for m in self.milestones if m.unlocked]

    def get_milestone_rewards(self) -> List[str]:
        """Get all rewards from unlocked milestones"""
        rewards = []
        for milestone in self.milestones:
            if milestone.unlocked:
                rewards.extend(milestone.rewards)
        return rewards

    def get_skill_development_timeline(self, skill_name: str) -> Dict[str, Any]:
        """Get development timeline for a specific skill"""
        if skill_name not in self.skills:
            return {}

        skill = self.skills[skill_name]
        timeline = {
            'skill_name': skill_name,
            'category': skill.category.value,
            'total_xp': skill.total_xp,
            'current_level': skill.current_level.name,
            'usage_history': [],
            'level_progression': []
        }

        # Process usage history
        for usage in skill.usage_history:
            timeline['usage_history'].append({
                'timestamp': usage.timestamp.isoformat(),
                'success': usage.success,
                'difficulty': usage.difficulty,
                'context': usage.context,
                'xp_gained': usage.xp_gained,
                'bonus_xp': usage.bonus_xp,
                'critical_success': usage.critical_success
            })

        # Calculate level progression points
        cumulative_xp = 0
        for usage in skill.usage_history:
            cumulative_xp += usage.xp_gained + usage.bonus_xp
            # Check if this usage triggered a level up
            # (This is simplified - in practice, you'd track the exact level-up moments)
            if cumulative_xp >= MasteryLevel.APPRENTICE.xp_threshold and len(timeline['level_progression']) == 0:
                timeline['level_progression'].append({
                    'level': 'APPRENTICE',
                    'timestamp': usage.timestamp.isoformat(),
                    'total_xp': cumulative_xp
                })
            elif cumulative_xp >= MasteryLevel.JOURNEYMAN.xp_threshold and len(timeline['level_progression']) == 1:
                timeline['level_progression'].append({
                    'level': 'JOURNEYMAN',
                    'timestamp': usage.timestamp.isoformat(),
                    'total_xp': cumulative_xp
                })
            elif cumulative_xp >= MasteryLevel.EXPERT.xp_threshold and len(timeline['level_progression']) == 2:
                timeline['level_progression'].append({
                    'level': 'EXPERT',
                    'timestamp': usage.timestamp.isoformat(),
                    'total_xp': cumulative_xp
                })
            elif cumulative_xp >= MasteryLevel.MASTER.xp_threshold and len(timeline['level_progression']) == 3:
                timeline['level_progression'].append({
                    'level': 'MASTER',
                    'timestamp': usage.timestamp.isoformat(),
                    'total_xp': cumulative_xp
                })

        return timeline

    def _update_category_focus(self, skill: Skill) -> None:
        """Update category focus based on skill usage"""
        if skill.total_uses > 0:
            self.category_focus[skill.category] += skill.total_xp

    def _check_milestones(self) -> List[ProgressionMilestone]:
        """Check and unlock any eligible milestones"""
        new_milestones = []

        for milestone in self.milestones:
            if not milestone.unlocked:
                progress = self.check_milestone_progress(milestone.name)
                if progress >= 1.0:
                    milestone.unlocked = True
                    milestone.unlocked_at = datetime.now()
                    new_milestones.append(milestone)

        return new_milestones

    def _calculate_recommendation_score(
        self,
        skill: Skill,
        related_skills: List[str]
    ) -> float:
        """Calculate recommendation score for a skill based on related skills"""
        score = 0.0

        # Check synergies with related skills
        for synergy in skill.synergies:
            if synergy.skill_name in related_skills:
                score += 0.4

        # Check if skill complements the category balance
        category_skills = self.get_skills_by_category(skill.category)
        if len(category_skills) < 3:  # Underdeveloped category
            score += 0.3

        # Check if skill has prerequisites that are met
        prerequisites_met = all(
            req_skill in self.skills and self.skills[req_skill].current_level >= req_level
            for req_skill, req_level in skill.prerequisites
        )
        if prerequisites_met:
            score += 0.3

        return min(1.0, score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert progression to dictionary for serialization"""
        return {
            'agent_id': self.agent_id,
            'skills': {name: skill.to_dict() for name, skill in self.skills.items()},
            'milestones': [
                {
                    'name': m.name,
                    'description': m.description,
                    'required_skills': {s: l.name for s, l in m.required_skills.items()},
                    'total_xp_requirement': m.total_xp_requirement,
                    'rewards': m.rewards,
                    'unlocked': m.unlocked,
                    'unlocked_at': m.unlocked_at.isoformat() if m.unlocked_at else None
                } for m in self.milestones
            ],
            'start_date': self.start_date.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'daily_xp_history': dict(self.daily_xp_history),
            'category_focus': {c.value: v for c, v in self.category_focus.items()},
            'skill_combinations': {
                f"{k[0]}+{k[1]}": v for k, v in self.skill_combinations.items()
            }
        }

    def __str__(self) -> str:
        stats = self.get_development_stats()
        return f"SkillProgression for {self.agent_id}: {stats.total_skills_learned} skills, {stats.total_xp_earned} total XP"