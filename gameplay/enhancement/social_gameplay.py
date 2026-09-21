#!/usr/bin/env python3
"""
Enhanced Social Gameplay System for DMLogn8n
Provides deep social interactions, cooperation mechanics, and community building
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class RelationshipType(Enum):
    FRIEND = "friend"
    RIVAL = "rival"
    MENTOR = "mentor"
    STUDENT = "student"
    ALLY = "ally"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    FAMILY = "family"
    ROMANTIC = "romantic"

class InteractionType(Enum):
    CONVERSATION = "conversation"
    GIFT = "gift"
    HELP = "help"
    TRADE = "trade"
    PARTY = "party"
    QUEST = "quest"
    COMPETITION = "competition"
    MENTORING = "mentoring"
    CELEBRATION = "celebration"

class SocialStatus(Enum):
    OUTCAST = "outcast"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    GOOD_FRIEND = "good_friend"
    BEST_FRIEND = "best_friend"
    CONFIDANT = "confidant"
    LEGEND = "legend"

class GroupType(Enum):
    GUILD = "guild"
    PARTY = "party"
    CLAN = "clan"
    ALLIANCE = "alliance"
    COMMUNITY = "community"
    CIRCLE = "circle"

class ActivityType(Enum):
    DUNGEON = "dungeon"
    RAID = "raid"
    PVP = "pvp"
    CRAFTING = "crafting"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    TRADING = "trading"
    TEACHING = "teaching"

@dataclass
class Personality:
    """Character personality traits"""
    openness: float = 0.5  # 0-1
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    honor: float = 0.5
    ambition: float = 0.5
    compassion: float = 0.5

@dataclass
class Relationship:
    """Relationship between two characters"""
    character1_id: str
    character2_id: str
    relationship_type: RelationshipType
    level: int = 0  # -100 to 100
    trust: float = 0.5  # 0-1
    respect: float = 0.5  # 0-1
    shared_experiences: List[str] = field(default_factory=list)
    secrets_known: List[str] = field(default_factory=list)
    favors_owed: Dict[str, int] = field(default_factory=dict)
    last_interaction: float = field(default_factory=time.time)

@dataclass
class SocialInteraction:
    """Social interaction between characters"""
    id: str
    initiator_id: str
    target_id: str
    interaction_type: InteractionType
    description: str
    relationship_change: float = 0.0
    trust_change: float = 0.0
    respect_change: float = 0.0
    social_xp_reward: int = 0
    requirements: Dict[str, Any] = field(default_factory=dict)
    consequences: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class Group:
    """Social group (guild, party, etc.)"""
    id: str
    name: str
    description: str
    group_type: GroupType
    leader_id: str
    members: Set[str] = field(default_factory=set)
    level: int = 1
    experience: int = 0
    reputation: int = 0
    permissions: Dict[str, Set[str]] = field(default_factory=dict)
    shared_storage: Dict[str, int] = field(default_factory=dict)
    group_quests: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

@dataclass
class CooperativeActivity:
    """Activity requiring multiple participants"""
    id: str
    name: str
    description: str
    activity_type: ActivityType
    min_participants: int = 2
    max_participants: int = 4
    duration: int = 3600  # seconds
    requirements: Dict[str, Any] = field(default_factory=dict)
    rewards: Dict[str, Any] = field(default_factory=dict)
    coordination_bonus: float = 1.1
    roles: Dict[str, List[str]] = field(default_factory=dict)  # role -> list of player IDs

class ReputationSystem:
    """Reputation and faction management"""

    def __init__(self):
        self.factions: Dict[str, Dict[str, Any]] = {}
        self.player_reputation: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.reputation_events: List[Dict] = []
        self.reputation_thresholds = {
            "hated": -5000,
            "hostile": -1000,
            "unfriendly": -500,
            "neutral": 0,
            "friendly": 500,
            "honored": 2000,
            "revered": 5000,
            "exalted": 10000
        }

    def add_faction(self, faction_id: str, name: str, description: str, allies: List[str] = None, enemies: List[str] = None):
        """Add a new faction"""
        self.factions[faction_id] = {
            "name": name,
            "description": description,
            "allies": allies or [],
            "enemies": enemies or [],
            "quests": [],
            "rewards": {}
        }

    def change_reputation(self, player_id: str, faction_id: str, amount: int, reason: str = ""):
        """Change player reputation with faction"""
        old_rep = self.player_reputation[player_id][faction_id]
        new_rep = old_rep + amount

        # Apply reputation gains with diminishing returns
        if amount > 0 and new_rep > 5000:
            amount = int(amount * 0.5)  # Half reputation gains after honored
            new_rep = old_rep + amount

        self.player_reputation[player_id][faction_id] = new_rep

        # Apply faction relationships
        if faction_id in self.factions:
            faction = self.factions[faction_id]
            # Allies get fraction of reputation change
            for ally in faction["allies"]:
                self.player_reputation[player_id][ally] += int(amount * 0.25)
            # Enemies get opposite reputation change
            for enemy in faction["enemies"]:
                self.player_reputation[player_id][enemy] -= int(amount * 0.25)

        self.reputation_events.append({
            "player_id": player_id,
            "faction_id": faction_id,
            "change": amount,
            "reason": reason,
            "timestamp": time.time()
        })

    def get_reputation_level(self, player_id: str, faction_id: str) -> str:
        """Get reputation level string"""
        rep = self.player_reputation[player_id][faction_id]

        for level, threshold in sorted(self.reputation_thresholds.items(), key=lambda x: x[1], reverse=True):
            if rep >= threshold:
                return level

        return "hated"

    def get_reputation_bonuses(self, player_id: str) -> Dict[str, float]:
        """Get reputation-based bonuses"""
        bonuses = {}
        for faction_id, reputation in self.player_reputation[player_id].items():
            level = self.get_reputation_level(player_id, faction_id)
            if level in ["friendly", "honored", "revered", "exalted"]:
                bonus_multiplier = 1.0 + (reputation / 10000) * 0.2  # Up to 20% bonus
                bonuses[faction_id] = bonus_multiplier

        return bonuses

class SocialGameplaySystem:
    """Main social gameplay system"""

    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}
        self.personalities: Dict[str, Personality] = {}
        self.groups: Dict[str, Group] = {}
        self.activities: Dict[str, CooperativeActivity] = {}
        self.interactions: Dict[str, SocialInteraction] = {}
        self.reputation_system = ReputationSystem()
        self.social_xp: Dict[str, int] = defaultdict(int)
        self.social_level: Dict[str, int] = defaultdict(int)
        self friendship_networks: Dict[str, Set[str]] = defaultdict(set)
        self.analytics = SocialAnalytics()

        # Social gameplay parameters
        self.relationship_decay_rate = 0.001  # Per hour
        self.max_relationships_per_character = 50
        self.group_size_limits = {
            GroupType.PARTY: 4,
            GroupType.GUILD: 100,
            GroupType.CLAN: 50,
            GroupType.ALLIANCE: 500,
            GroupType.COMMUNITY: 1000,
            GroupType.CIRCLE: 10
        }
        self.cooperation_bonus_multiplier = 1.15
        self.friendship_bonus_threshold = 50

        self._initialize_default_factions()
        self._initialize_default_activities()

    def _initialize_default_factions(self):
        """Initialize default factions"""
        factions = [
            ("merchants_guild", "Merchants Guild", "Powerful trade organization"),
            ("warriors_council", "Warriors Council", "Elite fighters and tacticians"),
            ("mages_circle", "Mages Circle", "Mysterious magic users"),
            ("thieves_syndicate", "Thieves Syndicate", "Underground network"),
            ("nobility", "Nobility", "Ruling class and aristocrats"),
            ("common_folk", "Common Folk", "General population"),
        ]

        for faction_id, name, description in factions:
            self.reputation_system.add_faction(faction_id, name, description)

    def _initialize_default_activities(self):
        """Initialize default cooperative activities"""
        activities = [
            CooperativeActivity(
                id="dungeon_party",
                name="Dungeon Exploration",
                description="Explore dangerous dungeons together",
                activity_type=ActivityType.DUNGEON,
                min_participants=2,
                max_participants=4,
                duration=3600,
                rewards={"experience": 500, "gold": 200, "reputation": {"group": 10}},
                roles={"tank": [], "healer": [], "damage": []}
            ),
            CooperativeActivity(
                id="guild_feast",
                name="Guild Feast",
                description="Social gathering for guild members",
                activity_type=ActivityType.SOCIAL,
                min_participants=5,
                max_participants=50,
                duration=7200,
                rewards={"social_xp": 100, "relationship_bonus": 5},
                coordination_bonus=1.2
            ),
            CooperativeActivity(
                id="crafting_collaboration",
                name="Collaborative Crafting",
                description="Work together on complex crafting projects",
                activity_type=ActivityType.CRAFTING,
                min_participants=2,
                max_participants=6,
                duration=1800,
                rewards={"crafting_xp": 150, "rare_materials": 3}
            )
        ]

        for activity in activities:
            self.activities[activity.id] = activity

    def create_character_profile(self, character_id: str, personality: Personality = None) -> bool:
        """Create social profile for character"""
        if character_id in self.personalities:
            return False

        if personality is None:
            personality = Personality(
                openness=random.random(),
                conscientiousness=random.random(),
                extraversion=random.random(),
                agreeableness=random.random(),
                neuroticism=random.random(),
                honor=random.random(),
                ambition=random.random(),
                compassion=random.random()
            )

        self.personalities[character_id] = personality
        self.social_xp[character_id] = 0
        self.social_level[character_id] = 1

        self.analytics.record_character_creation(character_id)
        return True

    def create_relationship(self, char1_id: str, char2_id: str, relationship_type: RelationshipType) -> bool:
        """Create relationship between characters"""
        if char1_id == char2_id:
            return False

        relationship_key = f"{min(char1_id, char2_id)}_{max(char1_id, char2_id)}"

        if relationship_key in self.relationships:
            return False

        relationship = Relationship(
            character1_id=char1_id,
            character2_id=char2_id,
            relationship_type=relationship_type,
            level=self._calculate_initial_relationship_level(char1_id, char2_id, relationship_type)
        )

        self.relationships[relationship_key] = relationship

        # Update friendship networks
        if relationship_type == RelationshipType.FRIEND:
            self.friendship_networks[char1_id].add(char2_id)
            self.friendship_networks[char2_id].add(char1_id)

        self.analytics.record_relationship_creation(relationship_key, relationship_type.value)
        return True

    def _calculate_initial_relationship_level(self, char1_id: str, char2_id: str, relationship_type: RelationshipType) -> int:
        """Calculate initial relationship level based on personalities"""
        if char1_id not in self.personalities or char2_id not in self.personalities:
            return 0

        p1 = self.personalities[char1_id]
        p2 = self.personalities[char2_id]

        # Personality compatibility
        compatibility = 0
        compatibility += (1 - abs(p1.openness - p2.openness)) * 10
        compatibility += (1 - abs(p1.agreeableness - p2.agreeableness)) * 15
        compatibility += (1 - abs(p1.extraversion - p2.extraversion)) * 10

        # Base level for relationship type
        base_levels = {
            RelationshipType.FRIEND: 30,
            RelationshipType.RIVAL: -20,
            RelationshipType.ALLY: 40,
            RelationshipType.ENEMY: -40,
            RelationshipType.NEUTRAL: 0,
            RelationshipType.MENTOR: 20,
            RelationshipType.STUDENT: 20,
            RelationshipType.ROMANTIC: 25,
            RelationshipType.FAMILY: 60
        }

        return int(base_levels.get(relationship_type, 0) + compatibility)

    def interact(self, initiator_id: str, target_id: str, interaction_type: InteractionType, description: str) -> Tuple[bool, str]:
        """Perform social interaction"""
        if initiator_id not in self.personalities or target_id not in self.personalities:
            return False, "One or both characters not found"

        # Create or get relationship
        relationship_key = f"{min(initiator_id, target_id)}_{max(initiator_id, target_id)}"
        if relationship_key not in self.relationships:
            # Create neutral relationship
            self.create_relationship(initiator_id, target_id, RelationshipType.NEUTRAL)

        relationship = self.relationships[relationship_key]

        # Calculate interaction effects
        effects = self._calculate_interaction_effects(initiator_id, target_id, interaction_type, relationship)

        # Apply effects to relationship
        relationship.level += effects["relationship_change"]
        relationship.level = max(-100, min(100, relationship.level))  # Clamp between -100 and 100
        relationship.trust = max(0, min(1, relationship.trust + effects["trust_change"]))
        relationship.respect = max(0, min(1, relationship.respect + effects["respect_change"]))
        relationship.last_interaction = time.time()

        # Update relationship type if needed
        self._update_relationship_type(relationship)

        # Award social XP
        social_xp = effects["social_xp_reward"]
        self.award_social_xp(initiator_id, social_xp)
        if interaction_type in [InteractionType.CONVERSATION, InteractionType.HELP]:
            self.award_social_xp(target_id, social_xp // 2)

        # Record interaction
        interaction = SocialInteraction(
            id=f"interaction_{int(time.time())}_{random.randint(1000, 9999)}",
            initiator_id=initiator_id,
            target_id=target_id,
            interaction_type=interaction_type,
            description=description,
            **effects
        )
        self.interactions[interaction.id] = interaction

        self.analytics.record_interaction(interaction)

        return True, f"Interaction successful. Relationship changed by {effects['relationship_change']}"

    def _calculate_interaction_effects(self, initiator_id: str, target_id: str, interaction_type: InteractionType, relationship: Relationship) -> Dict[str, float]:
        """Calculate effects of social interaction"""
        initiator = self.personalities[initiator_id]
        target = self.personalities[target_id]

        base_effects = {
            InteractionType.CONVERSATION: {"relationship": 2, "trust": 0.02, "respect": 0.01, "xp": 10},
            InteractionType.GIFT: {"relationship": 5, "trust": 0.05, "respect": 0.02, "xp": 15},
            InteractionType.HELP: {"relationship": 8, "trust": 0.08, "respect": 0.05, "xp": 25},
            InteractionType.TRADE: {"relationship": 1, "trust": 0.01, "respect": 0.01, "xp": 5},
            InteractionType.PARTY: {"relationship": 3, "trust": 0.03, "respect": 0.02, "xp": 20},
            InteractionType.QUEST: {"relationship": 10, "trust": 0.1, "respect": 0.08, "xp": 30},
            InteractionType.COMPETITION: {"relationship": -2, "trust": -0.01, "respect": 0.03, "xp": 15},
            InteractionType.MENTORING: {"relationship": 6, "trust": 0.06, "respect": 0.1, "xp": 25},
            InteractionType.CELEBRATION: {"relationship": 4, "trust": 0.04, "respect": 0.03, "xp": 20}
        }

        effect = base_effects.get(interaction_type, {"relationship": 0, "trust": 0, "respect": 0, "xp": 0})

        # Personality modifiers
        personality_modifier = 1.0

        # Extraverts get more from social interactions
        if interaction_type in [InteractionType.PARTY, InteractionType.CONVERSATION, InteractionType.CELEBRATION]:
            personality_modifier *= (0.8 + initiator.extraversion * 0.4)

        # Agreeable people give better relationship boosts
        personality_modifier *= (0.9 + initiator.agreeableness * 0.2)

        # Current relationship affects gains
        if relationship.level > 50:  # Good relationships get diminishing returns
            personality_modifier *= 0.8
        elif relationship.level < -50:  # Bad relationships have harder time improving
            personality_modifier *= 0.6

        return {
            "relationship_change": effect["relationship"] * personality_modifier,
            "trust_change": effect["trust"] * personality_modifier,
            "respect_change": effect["respect"] * personality_modifier,
            "social_xp_reward": int(effect["xp"] * personality_modifier)
        }

    def _update_relationship_type(self, relationship: Relationship):
        """Update relationship type based on level"""
        level = relationship.level

        if level >= 75:
            if relationship.relationship_type not in [RelationshipType.FAMILY, RelationshipType.ROMANTIC]:
                relationship.relationship_type = RelationshipType.BEST_FRIEND
        elif level >= 50:
            if relationship.relationship_type not in [RelationshipType.FAMILY, RelationshipType.ROMANTIC, RelationshipType.BEST_FRIEND]:
                relationship.relationship_type = RelationshipType.GOOD_FRIEND
        elif level >= 25:
            relationship.relationship_type = RelationshipType.FRIEND
        elif level <= -75:
            relationship.relationship_type = RelationshipType.ENEMY
        elif level <= -50:
            relationship.relationship_type = RelationshipType.RIVAL
        elif level <= -25:
            relationship.relationship_type = RelationshipType.NEUTRAL

    def create_group(self, group_id: str, name: str, group_type: GroupType, leader_id: str, description: str = "") -> bool:
        """Create a new social group"""
        if group_id in self.groups:
            return False

        if leader_id not in self.personalities:
            return False

        group = Group(
            id=group_id,
            name=name,
            description=description,
            group_type=group_type,
            leader_id=leader_id,
            members={leader_id}
        )

        # Set basic permissions
        group.permissions[leader_id] = {"invite", "kick", "promote", "demote", "manage"}

        self.groups[group_id] = group

        self.analytics.record_group_creation(group_id, group_type.value)
        return True

    def join_group(self, player_id: str, group_id: str, invited_by: str = None) -> Tuple[bool, str]:
        """Join a social group"""
        if group_id not in self.groups:
            return False, "Group not found"

        if player_id not in self.personalities:
            return False, "Player not found"

        group = self.groups[group_id]
        max_size = self.group_size_limits.get(group.group_type, 10)

        if len(group.members) >= max_size:
            return False, f"Group is full (max {max_size} members)"

        # Check if joining requires invitation
        if group.group_type in [GroupType.GUILD, GroupType.CLAN, GroupType.ALLIANCE]:
            if not invited_by or invited_by not in group.members:
                return False, "Invitation required"

        group.members.add(player_id)
        group.permissions[player_id] = set()  # Basic member permissions

        self.analytics.record_group_join(player_id, group_id)
        return True, f"Joined {group.name}"

    def leave_group(self, player_id: str, group_id: str) -> Tuple[bool, str]:
        """Leave a social group"""
        if group_id not in self.groups:
            return False, "Group not found"

        group = self.groups[group_id]

        if player_id not in group.members:
            return False, "Not a member of this group"

        # Leader can't leave if others remain
        if player_id == group.leader_id and len(group.members) > 1:
            return False, "Leader must transfer leadership before leaving"

        group.members.remove(player_id)
        group.permissions.pop(player_id, None)

        # Remove group if empty
        if len(group.members) == 0:
            del self.groups[group_id]

        self.analytics.record_group_leave(player_id, group_id)
        return True, f"Left {group.name}"

    def start_cooperative_activity(self, activity_id: str, initiator_id: str, participants: List[str]) -> Tuple[bool, str]:
        """Start a cooperative activity"""
        if activity_id not in self.activities:
            return False, "Activity not found"

        activity = self.activities[activity_id]

        # Check requirements
        if len(participants) < activity.min_participants:
            return False, f"Need at least {activity.min_participants} participants"

        if len(participants) > activity.max_participants:
            return False, f"Maximum {activity.max_participants} participants allowed"

        # Check if all participants are available
        for participant in participants:
            if participant not in self.personalities:
                return False, f"Participant {participant} not found"

        # Calculate cooperation bonus based on relationships
        cooperation_bonus = 1.0
        relationship_count = 0

        for i, p1 in enumerate(participants):
            for p2 in participants[i+1:]:
                relationship_key = f"{min(p1, p2)}_{max(p1, p2)}"
                if relationship_key in self.relationships:
                    relationship = self.relationships[relationship_key]
                    if relationship.level > 0:
                        cooperation_bonus += (relationship.level / 100) * 0.1
                        relationship_count += 1

        # Apply coordination bonus
        cooperation_bonus *= activity.coordination_bonus

        # Create activity instance
        activity_instance = {
            "activity_id": activity_id,
            "participants": participants,
            "initiator": initiator_id,
            "start_time": time.time(),
            "cooperation_bonus": cooperation_bonus,
            "relationship_count": relationship_count
        }

        # Award social XP for cooperation
        base_xp = 50
        for participant in participants:
            xp_award = int(base_xp * cooperation_bonus)
            self.award_social_xp(participant, xp_award)

        self.analytics.record_activity_start(activity_id, participants, cooperation_bonus)
        return True, f"Started {activity.name} with cooperation bonus {cooperation_bonus:.2f}"

    def award_social_xp(self, player_id: str, amount: int):
        """Award social experience points"""
        self.social_xp[player_id] += amount

        # Check for level up
        current_level = self.social_level[player_id]
        required_xp = self.calculate_social_xp_requirement(current_level + 1)

        if self.social_xp[player_id] >= required_xp:
            self.social_level[player_id] += 1
            self.social_xp[player_id] -= required_xp

            # Unlock new social abilities
            self._unlock_social_abilities(player_id, self.social_level[player_id])

            self.analytics.record_social_level_up(player_id, self.social_level[player_id])

    def calculate_social_xp_requirement(self, level: int) -> int:
        """Calculate XP required for social level"""
        return int(100 * math.pow(1.3, level - 1))

    def _unlock_social_abilities(self, player_id: str, level: int):
        """Unlock new social abilities at certain levels"""
        abilities = {
            5: "group_invitation",
            10: "guild_creation",
            15: "alliance_formation",
            20: "community_leadership",
            25: "legendary_influence"
        }

        if level in abilities:
            # Grant ability (would integrate with other systems)
            pass

    def get_social_status(self, player_id: str) -> SocialStatus:
        """Get player's social status based on relationships and reputation"""
        total_relationships = 0
        positive_relationships = 0
        strong_relationships = 0

        for relationship_key, relationship in self.relationships.items():
            if player_id in [relationship.character1_id, relationship.character2_id]:
                total_relationships += 1
                if relationship.level > 0:
                    positive_relationships += 1
                if relationship.level > 50:
                    strong_relationships += 1

        # Calculate social score
        social_score = (self.social_level[player_id] * 10 +
                       positive_relationships * 5 +
                       strong_relationships * 10 +
                       len(self.friendship_networks[player_id]) * 3)

        # Determine status
        if social_score >= 200:
            return SocialStatus.LEGEND
        elif social_score >= 150:
            return SocialStatus.CONFIDANT
        elif social_score >= 100:
            return SocialStatus.BEST_FRIEND
        elif social_score >= 70:
            return SocialStatus.GOOD_FRIEND
        elif social_score >= 40:
            return SocialStatus.FRIEND
        elif social_score >= 20:
            return SocialStatus.ACQUAINTANCE
        elif social_score >= 5:
            return SocialStatus.STRANGER
        else:
            return SocialStatus.OUTCAST

    def get_social_recommendations(self, player_id: str) -> List[Dict[str, Any]]:
        """Get social activity recommendations for player"""
        recommendations = []

        # Relationship recommendations
        for relationship_key, relationship in self.relationships.items():
            if player_id in [relationship.character1_id, relationship.character2_id]:
                if relationship.level > 30 and relationship.level < 50:
                    other_id = relationship.character2_id if relationship.character1_id == player_id else relationship.character1_id
                    recommendations.append({
                        "type": "strengthen_relationship",
                        "target": other_id,
                        "description": f"Strengthen bond with {other_id}",
                        "priority": "medium"
                    })

        # Group activity recommendations
        if self.social_level[player_id] >= 5:
            recommendations.append({
                "type": "join_group",
                "description": "Consider joining a guild or community",
                "priority": "high"
            })

        # Cooperative activity recommendations
        for activity_id, activity in self.activities.items():
            if activity.min_participants <= 4:  # Small group activities
                recommendations.append({
                    "type": "cooperative_activity",
                    "activity_id": activity_id,
                    "description": f"Try {activity.name} with friends",
                    "priority": "medium"
                })

        return recommendations[:5]  # Return top 5 recommendations

    def decay_relationships(self):
        """Apply relationship decay over time"""
        current_time = time.time()
        decay_threshold = 3600  # 1 hour

        for relationship_key, relationship in self.relationships.items():
            time_since_interaction = current_time - relationship.last_interaction

            if time_since_interaction > decay_threshold:
                hours_passed = time_since_interaction / 3600
                decay_amount = self.relationship_decay_rate * hours_passed

                # Don't decay very strong relationships as quickly
                if relationship.level > 75:
                    decay_amount *= 0.5
                elif relationship.level > 50:
                    decay_amount *= 0.7

                relationship.level = max(-100, relationship.level - decay_amount)

class SocialAnalytics:
    """Analytics for social gameplay system"""

    def __init__(self):
        self.interaction_stats = defaultdict(int)
        self.relationship_stats = defaultdict(int)
        self.group_stats = defaultdict(int)
        self.activity_stats = defaultdict(int)
        self.player_progression = defaultdict(list)

    def record_character_creation(self, character_id: str):
        """Record new character creation"""
        self.player_progression[character_id].append({
            "event": "creation",
            "timestamp": time.time()
        })

    def record_relationship_creation(self, relationship_key: str, relationship_type: str):
        """Record relationship creation"""
        self.relationship_stats[f"created_{relationship_type}"] += 1

    def record_interaction(self, interaction: SocialInteraction):
        """Record social interaction"""
        self.interaction_stats[f"{interaction.interaction_type.value}"] += 1

    def record_group_creation(self, group_id: str, group_type: str):
        """Record group creation"""
        self.group_stats[f"created_{group_type}"] += 1

    def record_group_join(self, player_id: str, group_id: str):
        """Record group membership"""
        self.group_stats["joins"] += 1

    def record_group_leave(self, player_id: str, group_id: str):
        """Record group leave"""
        self.group_stats["leaves"] += 1

    def record_activity_start(self, activity_id: str, participants: List[str], cooperation_bonus: float):
        """Record cooperative activity"""
        self.activity_stats[f"{activity_id}_starts"] += 1
        self.activity_stats[f"{activity_id}_avg_bonus"] = (
            self.activity_stats.get(f"{activity_id}_avg_bonus", 0) + cooperation_bonus
        ) / 2

    def record_social_level_up(self, player_id: str, level: int):
        """Record social level progression"""
        self.player_progression[player_id].append({
            "event": "level_up",
            "level": level,
            "timestamp": time.time()
        })

    def get_social_summary(self) -> Dict[str, Any]:
        """Get social analytics summary"""
        total_interactions = sum(self.interaction_stats.values())
        total_relationships = sum(self.relationship_stats.values())

        return {
            "total_interactions": total_interactions,
            "interaction_types": dict(self.interaction_stats),
            "total_relationships": total_relationships,
            "relationship_types": dict(self.relationship_stats),
            "group_activity": dict(self.group_stats),
            "cooperative_activities": dict(self.activity_stats),
            "most_popular_interaction": max(self.interaction_stats.items(), key=lambda x: x[1]) if self.interaction_stats else None,
            "most_common_relationship": max(self.relationship_stats.items(), key=lambda x: x[1]) if self.relationship_stats else None
        }

# Utility functions for social balance
def calculate_social_influence(player_level: int, social_level: int, network_size: int) -> float:
    """Calculate player's social influence score"""
    level_factor = (player_level + social_level) / 2
    network_factor = math.log(network_size + 1, 10)
    return level_factor * network_factor

def analyze_network_health(relationships: Dict[str, Relationship]) -> Dict[str, Any]:
    """Analyze health of social network"""
    if not relationships:
        return {"health": 0, "metrics": {}}

    total_relationships = len(relationships)
    positive_relationships = sum(1 for r in relationships.values() if r.level > 0)
    strong_relationships = sum(1 for r in relationships.values() if r.level > 50)
    average_level = sum(r.level for r in relationships.values()) / total_relationships
    average_trust = sum(r.trust for r in relationships.values()) / total_relationships

    health_score = (positive_relationships / total_relationships) * 50 + \
                   (strong_relationships / total_relationships) * 30 + \
                   (average_level + 50) / 100 * 15 + \
                   average_trust * 5

    return {
        "health": min(100, health_score),
        "metrics": {
            "total_relationships": total_relationships,
            "positive_ratio": positive_relationships / total_relationships,
            "strong_ratio": strong_relationships / total_relationships,
            "average_level": average_level,
            "average_trust": average_trust
        }
    }

# Export main classes
__all__ = [
    'SocialGameplaySystem',
    'Relationship',
    'SocialInteraction',
    'Group',
    'CooperativeActivity',
    'ReputationSystem',
    'SocialAnalytics',
    'calculate_social_influence',
    'analyze_network_health'
]