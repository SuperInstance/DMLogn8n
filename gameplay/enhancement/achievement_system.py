#!/usr/bin/env python3
"""
Comprehensive Achievement and Badge System for DMLogn8n
Provides meaningful player recognition and progression goals
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class AchievementCategory(Enum):
    COMBAT = "combat"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    CRAFTING = "crafting"
    QUESTING = "questing"
    COLLECTION = "collection"
    ECONOMY = "economy"
    LEADERSHIP = "leadership"
    KNOWLEDGE = "knowledge"
    COMMUNITY = "community"

class AchievementType(Enum):
    PROGRESSION = "progression"  # Reach certain levels/skills
    ACCUMULATION = "accumulation"  # Collect X items/Kill Y enemies
    COMPLETION = "completion"  # Complete all quests in area
    MASTERY = "mastery"  # Master a skill/system
    CHALLENGE = "challenge"  # Complete difficult task
    SOCIAL = "social"  # Social accomplishments
    TIME_BASED = "time_based"  # Achievements over time
    FIRST_TIME = "first_time"  # First time doing something
    STREAK = "streak"  # Consecutive accomplishments
    WORLD_EVENT = "world_event"  # Event-related achievements
    SECRETS = "secrets"  # Hidden/discovery achievements

class AchievementDifficulty(Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class BadgeType(Enum):
    PARTICIPATION = "participation"
    VICTORY = "victory"
    MASTERY = "mastery"
    RANKING = "ranking"
    SPECIAL = "special"
    COMMUNITY = "community"
    DEVELOPER = "developer"
    CONTRIBUTOR = "contributor"

class RarityTier(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

@dataclass
class AchievementCondition:
    """Condition for achievement completion"""
    type: str  # stat_value, item_count, quest_complete, etc.
    target: str  # What to track
    operator: str  # =, >=, <=
    value: Any  # Target value
    time_limit: Optional[int] = None  # seconds
    required: bool = True

@dataclass
class AchievementReward:
    """Reward for completing achievement"""
    type: str  # experience, gold, items, title, badge, stats
    value: Any
    rarity: RarityTier = RarityTier.COMMON
    hidden: bool = False

@dataclass
class Achievement:
    """Achievement definition"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    achievement_type: AchievementType
    difficulty: AchievementDifficulty
    points: int = 10
    icon: str = ""
    hidden: bool = False
    secret: bool = False
    prerequisites: List[str] = field(default_factory=list)
    conditions: List[AchievementCondition] = field(default_factory=list)
    rewards: List[AchievementReward] = field(default_factory=list)
    progress_tracking: Dict[str, Any] = field(default_factory=dict)
    time_limit: Optional[int] = None  # seconds
    repeatable: bool = False
    category_progression: Optional[str] = None  # Parent achievement for progression
    tags: Set[str] = field(default_factory=set)

@dataclass
class Badge:
    """Badge definition"""
    id: str
    name: str
    description: str
    badge_type: BadgeType
    rarity: RarityTier
    icon: str = ""
    hidden: bool = False
    limited_edition: bool = False
    expiration_date: Optional[float] = None
    awarded_by: Optional[str] = None  # system, player, guild, etc.
    display_priority: int = 0  # Higher = more prominent display
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AchievementProgress:
    """Player's progress on an achievement"""
    achievement_id: str
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    current_progress: Dict[str, Any] = field(default_factory=dict)
    completed_conditions: Set[str] = field(default_factory=set)
    attempts: int = 0
    best_attempt: Dict[str, Any] = field(default_factory=dict)
    milestones_reached: List[str] = field(default_factory=list)

@dataclass
class PlayerAchievements:
    """Container for player's achievement data"""
    player_id: str
    total_points: int = 0
    completed_achievements: Set[str] = field(default_factory=set)
    in_progress_achievements: Dict[str, AchievementProgress] = field(default_factory=dict)
    badges: Set[str] = field(default_factory=set)
    achievement_streaks: Dict[str, int] = field(default_factory=dict)
    categories_progress: Dict[AchievementCategory, int] = field(default_factory=lambda: {cat: 0 for cat in AchievementCategory})
    last_achievement_date: Optional[float] = None
    rare_achievements: Set[str] = field(default_factory=set)
    secret_discoveries: Set[str] = field(default_factory=set)

class AchievementSystem:
    """Main achievement and badge system"""

    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.badges: Dict[str, Badge] = {}
        self.player_achievements: Dict[str, PlayerAchievements] = {}
        self.achievement_chains: Dict[str, List[str]] = defaultdict(list)
        self.global_statistics: Dict[str, Any] = defaultdict(int)
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.progress_trackers: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.analytics = AchievementAnalytics()

        # Achievement system parameters
        self.points_per_difficulty = {
            AchievementDifficulty.TRIVIAL: 5,
            AchievementDifficulty.EASY: 10,
            AchievementDifficulty.NORMAL: 25,
            AchievementDifficulty.HARD: 50,
            AchievementDifficulty.EXPERT: 100,
            AchievementDifficulty.LEGENDARY: 200,
            AchievementDifficulty.MYTHIC: 500
        }
        self.completion_notification_delay = 1.0  # seconds
        self.secret_discovery_chance = 0.01  # 1% chance to reveal secret achievements
        self.badge_display_limit = 20  # Maximum badges to display prominently

        self._initialize_default_achievements()
        self._initialize_default_badges()
        self._initialize_achievement_chains()

    def _initialize_default_achievements(self):
        """Initialize default achievement set"""
        achievements = [
            # Combat Achievements
            Achievement(
                id="first_kill",
                name="First Blood",
                description="Defeat your first enemy",
                category=AchievementCategory.COMBAT,
                achievement_type=AchievementType.FIRST_TIME,
                difficulty=AchievementDifficulty.TRIVIAL,
                points=5,
                conditions=[
                    AchievementCondition("stat_value", "enemies_defeated", ">=", 1)
                ],
                rewards=[
                    AchievementReward("experience", 100, RarityTier.COMMON),
                    AchievementReward("title", "Warrior", RarityTier.COMMON)
                ]
            ),
            Achievement(
                id="monster_hunter",
                name="Monster Hunter",
                description="Defeat 100 enemies",
                category=AchievementCategory.COMBAT,
                achievement_type=AchievementType.ACCUMULATION,
                difficulty=AchievementDifficulty.NORMAL,
                points=25,
                conditions=[
                    AchievementCondition("stat_value", "enemies_defeated", ">=", 100)
                ],
                rewards=[
                    AchievementReward("experience", 500, RarityTier.UNCOMMON),
                    AchievementReward("items", ["monster_hunter_sword"], RarityTier.UNCOMMON)
                ]
            ),
            Achievement(
                id="dragon_slayer",
                name="Dragon Slayer",
                description="Defeat a legendary dragon",
                category=AchievementCategory.COMBAT,
                achievement_type=AchievementType.CHALLENGE,
                difficulty=AchievementDifficulty.LEGENDARY,
                points=200,
                conditions=[
                    AchievementCondition("specific_kill", "legendary_dragon", "=", 1)
                ],
                rewards=[
                    AchievementReward("experience", 5000, RarityTier.LEGENDARY),
                    AchievementReward("title", "Dragon Slayer", RarityTier.LEGENDARY),
                    AchievementReward("items", ["dragon_scale_armor"], RarityTier.LEGENDARY)
                ],
                tags={"boss", "legendary"}
            ),
            # Exploration Achievements
            Achievement(
                id="explorer",
                name="Explorer",
                description="Discover 10 unique locations",
                category=AchievementCategory.EXPLORATION,
                achievement_type=AchievementType.ACCUMULATION,
                difficulty=AchievementDifficulty.EASY,
                points=10,
                conditions=[
                    AchievementCondition("stat_value", "locations_discovered", ">=", 10)
                ],
                rewards=[
                    AchievementReward("experience", 200, RarityTier.COMMON),
                    AchievementReward("items", ["explorer_compass"], RarityTier.COMMON)
                ]
            ),
            # Social Achievements
            Achievement(
                id="friendly",
                name="Friendly",
                description="Make 5 friends",
                category=AchievementCategory.SOCIAL,
                achievement_type=AchievementType.ACCUMULATION,
                difficulty=AchievementDifficulty.EASY,
                points=10,
                conditions=[
                    AchievementCondition("stat_value", "friends_count", ">=", 5)
                ],
                rewards=[
                    AchievementReward("social_xp", 150, RarityTier.COMMON),
                    AchievementReward("title", "Friendly", RarityTier.COMMON)
                ]
            ),
            # Crafting Achievements
            Achievement(
                id="apprentice_crafter",
                name="Apprentice Crafter",
                description="Craft 50 items",
                category=AchievementCategory.CRAFTING,
                achievement_type=AchievementType.ACCUMULATION,
                difficulty=AchievementDifficulty.NORMAL,
                points=25,
                conditions=[
                    AchievementCondition("stat_value", "items_crafted", ">=", 50)
                ],
                rewards=[
                    AchievementReward("crafting_xp", 200, RarityTier.UNCOMMON),
                    AchievementReward("recipe", "advanced_crafting", RarityTier.UNCOMMON)
                ]
            ),
            # Secret Achievements
            Achievement(
                id="secret_finder",
                name="Secret Finder",
                description="Discover a hidden secret",
                category=AchievementCategory.SECRETS,
                achievement_type=AchievementType.FIRST_TIME,
                difficulty=AchievementDifficulty.HARD,
                points=50,
                secret=True,
                hidden=True,
                conditions=[
                    AchievementCondition("secret_discovery", "hidden_area_1", "=", 1)
                ],
                rewards=[
                    AchievementReward("experience", 1000, RarityTier.RARE),
                    AchievementReward("title", "Seeker of Truth", RarityTier.RARE),
                    AchievementReward("badge", "secret_finder", RarityTier.RARE)
                ]
            )
        ]

        for achievement in achievements:
            self.achievements[achievement.id] = achievement

    def _initialize_default_badges(self):
        """Initialize default badges"""
        badges = [
            Badge(
                id="beta_tester",
                name="Beta Tester",
                description="Participated in beta testing",
                badge_type=BadgeType.SPECIAL,
                rarity=RarityTier.EPIC,
                hidden=False,
                limited_edition=True,
                awarded_by="system",
                display_priority=100
            ),
            Badge(
                id="founder",
                name="Founder",
                description="Early supporter of the game",
                badge_type=BadgeType.SPECIAL,
                rarity=RarityTier.LEGENDARY,
                hidden=False,
                limited_edition=True,
                awarded_by="system",
                display_priority=200
            ),
            Badge(
                id="community_hero",
                name="Community Hero",
                description="Recognized for helping the community",
                badge_type=BadgeType.COMMUNITY,
                rarity=RarityTier.RARE,
                display_priority=80
            ),
            Badge(
                id="master_achiever",
                name="Master Achiever",
                description="Completed 100 achievements",
                badge_type=BadgeType.MASTERY,
                rarity=RarityTier.EPIC,
                display_priority=90
            )
        ]

        for badge in badges:
            self.badges[badge.id] = badge

    def _initialize_achievement_chains(self):
        """Initialize achievement progression chains"""
        self.achievement_chains["combat_progression"] = [
            "first_kill", "monster_hunter", "dragon_slayer"
        ]
        self.achievement_chains["exploration_progression"] = [
            "explorer", "cartographer", "world_traveler"
        ]

    def create_player_profile(self, player_id: str) -> PlayerAchievements:
        """Create achievement profile for new player"""
        if player_id in self.player_achievements:
            return self.player_achievements[player_id]

        profile = PlayerAchievements(player_id=player_id)
        self.player_achievements[player_id] = profile

        # Auto-start some achievements
        for achievement_id, achievement in self.achievements.items():
            if achievement.achievement_type == AchievementType.FIRST_TIME:
                self.start_achievement(player_id, achievement_id)

        self.analytics.record_player_creation(player_id)
        return profile

    def start_achievement(self, player_id: str, achievement_id: str) -> bool:
        """Start tracking an achievement for a player"""
        if player_id not in self.player_achievements:
            self.create_player_profile(player_id)

        if achievement_id not in self.achievements:
            return False

        profile = self.player_achievements[player_id]
        achievement = self.achievements[achievement_id]

        # Check if already completed
        if achievement_id in profile.completed_achievements:
            return False

        # Check prerequisites
        if not self.check_achievement_prerequisites(player_id, achievement):
            return False

        # Initialize progress
        if achievement_id not in profile.in_progress_achievements:
            progress = AchievementProgress(
                achievement_id=achievement_id,
                started_at=time.time()
            )

            # Initialize progress tracking for each condition
            for condition in achievement.conditions:
                if condition.type in ["stat_value", "item_count", "accumulation"]:
                    progress.current_progress[condition.target] = 0

            profile.in_progress_achievements[achievement_id] = progress

        return True

    def check_achievement_prerequisites(self, player_id: str, achievement: Achievement) -> bool:
        """Check if player meets achievement prerequisites"""
        profile = self.player_achievements[player_id]

        for prereq_id in achievement.prerequisites:
            if prereq_id not in profile.completed_achievements:
                return False

        return True

    def update_progress(self, player_id: str, stat_type: str, target: str, value: Any, context: Dict[str, Any] = None) -> List[str]:
        """Update progress and check for completed achievements"""
        completed_achievements = []

        if player_id not in self.player_achievements:
            self.create_player_profile(player_id)

        profile = self.player_achievements[player_id]

        # Update global statistics
        self.global_statistics[f"{stat_type}_{target}"] += 1

        # Check all active achievements
        for achievement_id, progress in profile.in_progress_achievements.items():
            if achievement_id in profile.completed_achievements:
                continue

            achievement = self.achievements[achievement_id]

            # Check each condition
            for condition in achievement.conditions:
                if self.check_condition(condition, stat_type, target, value):
                    # Update progress
                    if condition.target not in progress.current_progress:
                        progress.current_progress[condition.target] = 0

                    if condition.type in ["stat_value", "accumulation"]:
                        if isinstance(value, (int, float)):
                            progress.current_progress[condition.target] += value
                        else:
                            progress.current_progress[condition.target] = 1
                    else:
                        progress.current_progress[condition.target] = value

                    # Check if condition is met
                    if self.evaluate_condition(condition, progress.current_progress.get(condition.target, 0)):
                        progress.completed_conditions.add(f"{condition.type}_{condition.target}")

                        # Check for milestone rewards
                        self.check_milestone_rewards(player_id, achievement, progress)

            # Check if achievement is completed
            if self.is_achievement_completed(achievement, progress):
                self.complete_achievement(player_id, achievement_id)
                completed_achievements.append(achievement_id)

                # Check for chain progression
                self.check_achievement_chain(player_id, achievement_id)

        # Check for new achievements to start
        self.check_new_achievements(player_id, stat_type, target)

        # Chance to reveal secret achievements
        if random.random() < self.secret_discovery_chance:
            self.reveal_random_secret_achievement(player_id)

        self.analytics.record_progress_update(player_id, stat_type, target, value, len(completed_achievements))

        return completed_achievements

    def check_condition(self, condition: AchievementCondition, stat_type: str, target: str, value: Any) -> bool:
        """Check if update matches condition"""
        if condition.type != stat_type:
            return False

        if condition.target != target:
            return False

        return True

    def evaluate_condition(self, condition: AchievementCondition, current_value: Any) -> bool:
        """Evaluate if condition is met"""
        if condition.operator == "=":
            return current_value == condition.value
        elif condition.operator == ">=":
            return current_value >= condition.value
        elif condition.operator == "<=":
            return current_value <= condition.value
        elif condition.operator == ">":
            return current_value > condition.value
        elif condition.operator == "<":
            return current_value < condition.value

        return False

    def is_achievement_completed(self, achievement: Achievement, progress: AchievementProgress) -> bool:
        """Check if all required conditions are completed"""
        required_conditions = [c for c in achievement.conditions if c.required]
        completed_count = 0

        for condition in required_conditions:
            condition_key = f"{condition.type}_{condition.target}"
            if condition_key in progress.completed_conditions:
                completed_count += 1

        return completed_count >= len(required_conditions)

    def complete_achievement(self, player_id: str, achievement_id: str) -> Tuple[bool, str]:
        """Complete an achievement and grant rewards"""
        if player_id not in self.player_achievements:
            return False, "Player not found"

        if achievement_id not in self.achievements:
            return False, "Achievement not found"

        profile = self.player_achievements[player_id]
        achievement = self.achievements[achievement_id]

        # Mark as completed
        profile.completed_achievements.add(achievement_id)
        profile.total_points += achievement.points
        profile.categories_progress[achievement.category] += 1
        profile.last_achievement_date = time.time()

        # Remove from in-progress
        profile.in_progress_achievements.pop(achievement_id, None)

        # Track rare achievements
        if achievement.difficulty in [AchievementDifficulty.LEGENDARY, AchievementDifficulty.MYTHIC]:
            profile.rare_achievements.add(achievement_id)

        # Track secret discoveries
        if achievement.secret:
            profile.secret_discoveries.add(achievement_id)

        # Grant rewards
        rewards_granted = []
        for reward in achievement.rewards:
            granted = self.grant_reward(player_id, reward)
            if granted:
                rewards_granted.append(granted)

        # Update achievement streaks
        self.update_achievement_streaks(player_id)

        self.analytics.record_achievement_complete(player_id, achievement_id, achievement.points)

        return True, f"Achievement '{achievement.name}' completed! Rewards: {', '.join(rewards_granted)}"

    def grant_reward(self, player_id: str, reward: AchievementReward) -> Optional[str]:
        """Grant achievement reward to player"""
        # This would integrate with other game systems
        # For now, just return the reward description
        if reward.type == "experience":
            return f"{reward.value} XP"
        elif reward.type == "gold":
            return f"{reward.value} gold"
        elif reward.type == "title":
            return f"Title: {reward.value}"
        elif reward.type == "items":
            return f"Items: {', '.join(reward.value)}"
        elif reward.type == "badge":
            self.award_badge(player_id, reward.value)
            return f"Badge: {reward.value}"

        return None

    def award_badge(self, player_id: str, badge_id: str) -> bool:
        """Award a badge to a player"""
        if player_id not in self.player_achievements:
            return False

        if badge_id not in self.badges:
            return False

        profile = self.player_achievements[player_id]
        profile.badges.add(badge_id)

        self.analytics.record_badge_award(player_id, badge_id)
        return True

    def check_milestone_rewards(self, player_id: str, achievement: Achievement, progress: AchievementProgress):
        """Check and award milestone progress rewards"""
        if "milestones" not in achievement.progress_tracking:
            return

        milestones = achievement.progress_tracking["milestones"]
        for milestone_name, milestone_value in milestones.items():
            if milestone_name not in progress.milestones_reached:
                # Check if milestone is reached
                for condition in achievement.conditions:
                    current = progress.current_progress.get(condition.target, 0)
                    if current >= milestone_value:
                        progress.milestones_reached.append(milestone_name)
                        # Grant milestone reward
                        self.grant_milestone_reward(player_id, achievement, milestone_name)

    def grant_milestone_reward(self, player_id: str, achievement: Achievement, milestone_name: str):
        """Grant milestone reward"""
        # This would grant intermediate rewards for long achievements
        pass

    def update_achievement_streaks(self, player_id: str):
        """Update achievement completion streaks"""
        profile = self.player_achievements[player_id]
        current_time = time.time()

        if profile.last_achievement_date:
            time_diff = current_time - profile.last_achievement_date
            # If completed within 24 hours, increment streak
            if time_diff < 86400:  # 24 hours
                profile.achievement_streaks["daily"] = profile.achievement_streaks.get("daily", 0) + 1
            else:
                profile.achievement_streaks["daily"] = 1

    def check_achievement_chain(self, player_id: str, completed_achievement_id: str):
        """Check and start next achievement in chain"""
        for chain_name, chain_achievements in self.achievement_chains.items():
            if completed_achievement_id in chain_achievements:
                # Find next achievement in chain
                current_index = chain_achievements.index(completed_achievement_id)
                if current_index < len(chain_achievements) - 1:
                    next_achievement_id = chain_achievements[current_index + 1]
                    self.start_achievement(player_id, next_achievement_id)

    def check_new_achievements(self, player_id: str, stat_type: str, target: str):
        """Check if new achievements should be started"""
        profile = self.player_achievements[player_id]

        for achievement_id, achievement in self.achievements.items():
            # Skip if already started or completed
            if achievement_id in profile.in_progress_achievements or achievement_id in profile.completed_achievements:
                continue

            # Check if this achievement should start based on the stat update
            for condition in achievement.conditions:
                if condition.type == stat_type and condition.target == target:
                    if self.check_achievement_prerequisites(player_id, achievement):
                        self.start_achievement(player_id, achievement_id)
                        break

    def reveal_random_secret_achievement(self, player_id: str):
        """Chance to reveal a secret achievement"""
        profile = self.player_achievements[player_id]
        secret_achievements = [a for a in self.achievements.values() if a.secret and a.id not in profile.completed_achievements]

        if secret_achievements:
            secret_achievement = random.choice(secret_achievements)
            self.start_achievement(player_id, secret_achievement.id)

    def get_player_progress(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive achievement progress for player"""
        if player_id not in self.player_achievements:
            return {"error": "Player not found"}

        profile = self.player_achievements[player_id]

        return {
            "player_id": player_id,
            "total_points": profile.total_points,
            "completed_achievements": len(profile.completed_achievements),
            "in_progress_achievements": len(profile.in_progress_achievements),
            "badges_earned": len(profile.badges),
            "categories_progress": {cat.value: count for cat, count in profile.categories_progress.items()},
            "rare_achievements": len(profile.rare_achievements),
            "secret_discoveries": len(profile.secret_discoveries),
            "achievement_streaks": dict(profile.achievement_streaks),
            "recent_achievements": [
                {
                    "id": achievement_id,
                    "name": self.achievements[achievement_id].name,
                    "completed_at": profile.last_achievement_date
                }
                for achievement_id in list(profile.completed_achievements)[-5:]  # Last 5
            ],
            "current_progress": {
                achievement_id: {
                    "name": self.achievements[achievement_id].name,
                    "progress": progress.current_progress,
                    "conditions_completed": len(progress.completed_conditions),
                    "total_conditions": len([c for c in self.achievements[achievement_id].conditions if c.required])
                }
                for achievement_id, progress in profile.in_progress_achievements.items()
            }
        }

    def get_achievement_recommendations(self, player_id: str) -> List[Dict[str, Any]]:
        """Get achievement recommendations for player"""
        if player_id not in self.player_achievements:
            return []

        profile = self.player_achievements[player_id]
        recommendations = []

        # Recommend achievements that are close to completion
        for achievement_id, progress in profile.in_progress_achievements.items():
            achievement = self.achievements[achievement_id]
            required_conditions = [c for c in achievement.conditions if c.required]
            completed_conditions = len(progress.completed_conditions)

            if completed_conditions > 0 and completed_conditions < len(required_conditions):
                completion_percentage = (completed_conditions / len(required_conditions)) * 100
                if completion_percentage >= 50:  # At least 50% complete
                    recommendations.append({
                        "achievement_id": achievement_id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "completion_percentage": completion_percentage,
                        "priority": "high",
                        "category": achievement.category.value
                    })

        # Recommend new achievements to start
        for achievement in self.achievements.values():
            if (achievement.id not in profile.completed_achievements and
                achievement.id not in profile.in_progress_achievements and
                self.check_achievement_prerequisites(player_id, achievement)):

                recommendations.append({
                    "achievement_id": achievement.id,
                    "name": achievement.name,
                    "description": achievement.description,
                    "difficulty": achievement.difficulty.value,
                    "priority": "medium",
                    "category": achievement.category.value
                })

        # Sort by priority and completion percentage
        recommendations.sort(key=lambda x: (
            0 if x.get("priority") == "high" else 1,
            -x.get("completion_percentage", 0)
        ))

        return recommendations[:10]  # Return top 10 recommendations

    def get_leaderboard(self, category: Optional[AchievementCategory] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get achievement leaderboard"""
        leaderboard = []

        for player_id, profile in self.player_achievements.items():
            points = profile.total_points

            # Filter by category if specified
            if category:
                points = profile.categories_progress.get(category, 0) * 10  # Rough point conversion

            leaderboard.append({
                "player_id": player_id,
                "points": points,
                "achievements_completed": len(profile.completed_achievements),
                "badges_earned": len(profile.badges),
                "rare_achievements": len(profile.rare_achievements)
            })

        # Sort by points
        leaderboard.sort(key=lambda x: x["points"], reverse=True)

        return leaderboard[:limit]

    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global achievement statistics"""
        total_achievements = len(self.achievements)
        total_completions = sum(len(profile.completed_achievements) for profile in self.player_achievements.values())

        # Most completed achievements
        achievement_completion_counts = defaultdict(int)
        for profile in self.player_achievements.values():
            for achievement_id in profile.completed_achievements:
                achievement_completion_counts[achievement_id] += 1

        most_completed = sorted(achievement_completion_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Category popularity
        category_counts = defaultdict(int)
        for profile in self.player_achievements.values():
            for category, count in profile.categories_progress.items():
                category_counts[category.value] += count

        return {
            "total_achievements": total_achievements,
            "total_players": len(self.player_achievements),
            "total_completions": total_completions,
            "average_completions_per_player": total_completions / len(self.player_achievements) if self.player_achievements else 0,
            "most_completed_achievements": [
                {"achievement_id": aid, "name": self.achievements[aid].name, "count": count}
                for aid, count in most_completed
            ],
            "category_popularity": dict(category_counts),
            "rarest_achievements": [
                {"achievement_id": aid, "name": self.achievements[aid].name, "count": count}
                for aid, count in sorted(achievement_completion_counts.items(), key=lambda x: x[1])[:10]
            ]
        }

class AchievementAnalytics:
    """Analytics for achievement system balance and engagement"""

    def __init__(self):
        self.player_data = {}
        self.completion_times = defaultdict(list)
        self.difficulty_distribution = defaultdict(int)
        self.category_popularity = defaultdict(int)
        self.reward_effectiveness = defaultdict(list)
        self.achievement_chains = defaultdict(list)

    def record_player_creation(self, player_id: str):
        """Record new player creation"""
        self.player_data[player_id] = {
            "created_at": time.time(),
            "achievements_completed": [],
            "completion_times": {},
            "streak_data": []
        }

    def record_progress_update(self, player_id: str, stat_type: str, target: str, value: Any, completions: int):
        """Record progress updates"""
        if player_id in self.player_data:
            self.player_data[player_id]["last_activity"] = time.time()

    def record_achievement_complete(self, player_id: str, achievement_id: str, points: int):
        """Record achievement completion"""
        if player_id in self.player_data:
            self.player_data[player_id]["achievements_completed"].append({
                "achievement_id": achievement_id,
                "points": points,
                "timestamp": time.time()
            })

        # Record completion time
        if player_id in self.player_data and "created_at" in self.player_data[player_id]:
            completion_time = time.time() - self.player_data[player_id]["created_at"]
            self.completion_times[achievement_id].append(completion_time)

    def record_badge_award(self, player_id: str, badge_id: str):
        """Record badge awarding"""
        pass  # Could track badge earning patterns

    def get_engagement_insights(self) -> Dict[str, Any]:
        """Get achievement engagement insights"""
        if not self.player_data:
            return {"total_players": 0}

        total_players = len(self.player_data)
        active_players = len([p for p in self.player_data.values() if "last_activity" in p])

        # Calculate average achievements per player
        achievements_per_player = []
        for player_data in self.player_data.values():
            achievements_per_player.append(len(player_data["achievements_completed"]))

        avg_achievements = sum(achievements_per_player) / len(achievements_per_player) if achievements_per_player else 0

        return {
            "total_players": total_players,
            "active_players": active_players,
            "average_achievements_per_player": avg_achievements,
            "most_engaged_players": sorted(
                [(player_id, len(data["achievements_completed"])) for player_id, data in self.player_data.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# Utility functions for achievement balance
def calculate_achievement_difficulty_curve(base_points: int, completion_rate: float, target_completion_rate: float = 0.3) -> int:
    """Calculate appropriate points based on completion rate"""
    if completion_rate == 0:
        return base_points * 3  # Very hard achievement

    # If completion rate is higher than target, reduce points
    if completion_rate > target_completion_rate:
        reduction_factor = target_completion_rate / completion_rate
        return int(base_points * reduction_factor)
    else:
        # If completion rate is lower than target, increase points
        increase_factor = target_completion_rate / completion_rate if completion_rate > 0 else 2
        return int(base_points * increase_factor)

def analyze_achievement_flow(achievements: List[Achievement]) -> Dict[str, Any]:
    """Analyze achievement flow and prerequisites"""
    prerequisite_counts = defaultdict(int)
    category_distribution = defaultdict(int)
    difficulty_distribution = defaultdict(int)

    for achievement in achievements:
        category_distribution[achievement.category.value] += 1
        difficulty_distribution[achievement.difficulty.value] += 1
        prerequisite_counts[len(achievement.prerequisites)] += 1

    # Find potential bottlenecks (achievements that are prerequisites for many others)
        pass

    return {
        "total_achievements": len(achievements),
        "category_distribution": dict(category_distribution),
        "difficulty_distribution": dict(difficulty_distribution),
        "prerequisite_distribution": dict(prerequisite_counts),
        "average_prerequisites": sum(len(a.prerequisites) for a in achievements) / len(achievements) if achievements else 0
    }

# Export main classes
__all__ = [
    'AchievementSystem',
    'Achievement',
    'Badge',
    'PlayerAchievements',
    'AchievementProgress',
    'AchievementAnalytics',
    'calculate_achievement_difficulty_curve',
    'analyze_achievement_flow'
]