#!/usr/bin/env python3
"""
DMLogn8n Guild Manager - Comprehensive Guild Management System

Handles guild creation, management, progression systems, hierarchies, halls,
storage, group objectives, and guild-based social interactions.

Features:
- Guild creation and customization
- Hierarchical rank systems with permissions
- Guild halls and shared spaces
- Guild storage and resource management
- Group objectives and achievements
- Guild progression and unlockable abilities
- Guild-based reputation and influence
- Member management and recruitment
- Guild politics and diplomacy
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import math

class GuildRole(Enum):
    """Guild member roles with hierarchical permissions"""
    GUILDMASTER = "guildmaster"
    OFFICER = "officer"
    VETERAN = "veteran"
    MEMBER = "member"
    RECRUIT = "recruit"
    HONORED = "honored"  # Special role for retired leaders

class GuildType(Enum):
    """Types of guilds with different focuses"""
    ADVENTURE = "adventure"      # Exploration and questing focus
    TRADE = "trade"             # Commerce and crafting focus
    ACADEMIC = "academic"       # Knowledge and research focus
    MILITARY = "military"       # Combat and conquest focus
    SOCIAL = "social"           # Community and events focus
    RELIGIOUS = "religious"     # Faith and philosophical focus
    ARTISAN = "artisan"         # Crafting and creation focus
    MERCENARY = "mercenary"     # Contract and hire focus

class GuildActivityType(Enum):
    """Types of guild activities for progression"""
    QUESTING = "questing"
    RAIDING = "raiding"
    CRAFTING = "crafting"
    TRADING = "trading"
    RESEARCH = "research"
    SOCIAL_EVENTS = "social_events"
    PVP = "pvp"
    EXPLORATION = "exploration"
    TEACHING = "teaching"
    DIPLOMACY = "diplomacy"

@dataclass
class GuildRank:
    """Guild rank with permissions and benefits"""
    title: str
    role: GuildRole
    permissions: List[str]
    benefits: Dict[str, Any]
    requirements: Dict[str, Any]
    color: str = "#FFFFFF"
    symbol: str = "⬤"

@dataclass
class GuildMember:
    """Guild member information"""
    player_id: str
    name: str
    role: GuildRole
    joined_date: datetime
    contribution_points: int = 0
    activity_score: float = 0.0
    last_active: datetime = None
    bio: str = ""
    titles: List[str] = None
    custom_permissions: List[str] = None

    def __post_init__(self):
        if self.titles is None:
            self.titles = []
        if self.custom_permissions is None:
            self.custom_permissions = []
        if self.last_active is None:
            self.last_active = datetime.now()

@dataclass
classGuildHall:
    """Guild hall with upgrades and features"""
    name: str
    level: int = 1
    features: List[str] = None
    decorations: Dict[str, Any] = None
    storage_capacity: int = 1000
    max_members: int = 50
    upkeep_cost: float = 100.0

    def __post_init__(self):
        if self.features is None:
            self.features = ["basic_hall", "meeting_room"]
        if self.decorations is None:
            self.decorations = {}

@dataclass
class GuildObjective:
    """Guild objective or goal"""
    id: str
    title: str
    description: str
    type: str
    requirements: Dict[str, Any]
    rewards: Dict[str, Any]
    progress: Dict[str, float] = None
    deadline: Optional[datetime] = None
    created_by: str = ""
    status: str = "active"  # active, completed, failed

    def __post_init__(self):
        if self.progress is None:
            self.progress = {}

@dataclass
class GuildAlliance:
    """Guild alliance or treaty"""
    id: str
    guild_id: str
    allied_guild_id: str
    type: str  # alliance, non_aggression, trade, military
    terms: Dict[str, Any]
    benefits: List[str]
    obligations: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "active"

class GuildManager:
    """Main guild management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Guild storage
        self.guilds: Dict[str, Dict] = {}
        self.guild_members: Dict[str, Dict[str, GuildMember]] = {}
        self.guild_halls: Dict[str, GuildHall] = {}
        self.guild_objectives: Dict[str, List[GuildObjective]] = {}
        self.guild_alliances: Dict[str, List[GuildAlliance]] = {}

        # System caches
        self.guild_ranks: Dict[GuildRole, GuildRank] = self._initialize_guild_ranks()
        self.guild_progression_cache: Dict[str, Dict] = {}
        self.active_guild_activities: Dict[str, List[Dict]] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_guilds_per_player": 1,
            "min_members_to_create": 5,
            "guild_creation_cost": 1000,
            "guild_name_min_length": 3,
            "guild_name_max_length": 30,
            "guild_description_max_length": 500,
            "max_alliances_per_guild": 5,
            "guild_objective_limit": 10,
            "contribution_decay_rate": 0.01,  # Daily decay
            "activity_decay_days": 30,
            "rank_permission_levels": {
                GuildRole.GUILDMASTER: 100,
                GuildRole.OFFICER: 80,
                GuildRole.VETERAN: 60,
                GuildRole.MEMBER: 40,
                GuildRole.RECRUIT: 20,
                GuildRole.HONORED: 90
            }
        }

    def _initialize_guild_ranks(self) -> Dict[GuildRole, GuildRank]:
        """Initialize default guild ranks with permissions"""
        return {
            GuildRole.GUILDMASTER: GuildRank(
                title="Guild Master",
                role=GuildRole.GUILDMASTER,
                permissions=[
                    "guild_disband", "guild_rename", "rank_create", "rank_modify",
                    "member_promote", "member_demote", "member_kick", "invite_all",
                    "guild_bank_withdraw", "guild_bank_deposit", "alliance_create",
                    "alliance_break", "objective_create", "objective_modify",
                    "hall_upgrade", "hall_decorate", "guild_settings", "guild_diplomacy"
                ],
                benefits={
                    "bank_access": "unlimited",
                    "hall_access": "all_areas",
                    "reputation_bonus": 2.0,
                    "storage_bonus": 1.5
                },
                requirements={"reputation": 1000, "time_in_guild": 0},
                color="#FFD700",
                symbol="👑"
            ),
            GuildRole.OFFICER: GuildRank(
                title="Officer",
                role=GuildRole.OFFICER,
                permissions=[
                    "member_promote", "member_demote", "member_kick", "invite_members",
                    "guild_bank_deposit", "guild_bank_withdraw_limited", "objective_create",
                    "hall_upgrade", "hall_decorate", "guild_settings_limited"
                ],
                benefits={
                    "bank_access": "limited",
                    "hall_access": "all_areas",
                    "reputation_bonus": 1.5,
                    "storage_bonus": 1.25
                },
                requirements={"reputation": 500, "time_in_guild": 30},
                color="#C0C0C0",
                symbol="⭐"
            ),
            GuildRole.VETERAN: GuildRank(
                title="Veteran",
                role=GuildRole.VETERAN,
                permissions=[
                    "invite_members", "guild_bank_deposit", "objective_suggest",
                    "hall_decorate_limited"
                ],
                benefits={
                    "bank_access": "deposit_only",
                    "hall_access": "main_areas",
                    "reputation_bonus": 1.25,
                    "storage_bonus": 1.15
                },
                requirements={"reputation": 300, "time_in_guild": 60},
                color="#CD7F32",
                symbol="🛡️"
            ),
            GuildRole.MEMBER: GuildRank(
                title="Member",
                role=GuildRole.MEMBER,
                permissions=[
                    "guild_bank_deposit", "hall_access_basic", "objective_participate"
                ],
                benefits={
                    "bank_access": "deposit_only",
                    "hall_access": "public_areas",
                    "reputation_bonus": 1.0,
                    "storage_bonus": 1.0
                },
                requirements={"reputation": 100, "time_in_guild": 7},
                color="#00FF00",
                symbol="⬤"
            ),
            GuildRole.RECRUIT: GuildRank(
                title="Recruit",
                role=GuildRole.RECRUIT,
                permissions=["hall_access_basic", "objective_participate_limited"],
                benefits={
                    "bank_access": "none",
                    "hall_access": "entrance_only",
                    "reputation_bonus": 0.8,
                    "storage_bonus": 0.5
                },
                requirements={"reputation": 0, "time_in_guild": 0},
                color="#808080",
                symbol="○"
            ),
            GuildRole.HONORED: GuildRank(
                title="Honored",
                role=GuildRole.HONORED,
                permissions=[
                    "guild_bank_deposit", "hall_access_all", "objective_suggest",
                    "member_mentor", "guild_history_access"
                ],
                benefits={
                    "bank_access": "deposit_only",
                    "hall_access": "all_areas",
                    "reputation_bonus": 1.75,
                    "storage_bonus": 1.3
                },
                requirements={"reputation": 800, "time_in_guild": 180, "special_recognition": True},
                color="#FF69B4",
                symbol="✨"
            )
        }

    async def create_guild(self, creator_id: str, guild_data: Dict) -> Dict:
        """Create a new guild"""
        try:
            # Validate guild creation requirements
            validation_result = await self._validate_guild_creation(creator_id, guild_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Generate unique guild ID
            guild_id = str(uuid.uuid4())

            # Create guild structure
            guild = {
                "id": guild_id,
                "name": guild_data["name"],
                "description": guild_data.get("description", ""),
                "type": guild_data.get("type", GuildType.ADVENTURE.value),
                "founded_date": datetime.now().isoformat(),
                "founder_id": creator_id,
                "master_id": creator_id,
                "level": 1,
                "experience": 0,
                "reputation": 0,
                "funds": 0.0,
                "settings": {
                    "invite_only": guild_data.get("invite_only", False),
                    "min_level_requirement": guild_data.get("min_level", 1),
                    "auto_promote_veteran": guild_data.get("auto_promote", True),
                    "allow_alliances": guild_data.get("allow_alliances", True),
                    "public_recruitment": guild_data.get("public_recruitment", True)
                },
                "custom_ranks": {},
                "statistics": {
                    "total_members": 1,
                    "total_contribution": 0,
                    "quests_completed": 0,
                    "raids_completed": 0,
                    "alliances_active": 0,
                    "wars_won": 0,
                    "achievements_unlocked": []
                },
                "progression": {
                    "current_level": 1,
                    "experience_to_next": 1000,
                    "total_experience_earned": 0,
                    "milestones_reached": [],
                    "unlocked_features": ["basic_guild", "guild_chat"]
                },
                "diplomacy": {
                    "allied_guilds": [],
                    "enemy_guilds": [],
                    "neutral_guilds": [],
                    "trade_partners": []
                }
            }

            # Create guild hall
            guild_hall = GuildHall(
                name=f"{guild['name']} Headquarters",
                level=1,
                features=["basic_hall", "meeting_room", "storage_basic"],
                max_members=50
            )

            # Add creator as guild master
            guild_member = GuildMember(
                player_id=creator_id,
                name=guild_data.get("creator_name", "Guild Master"),
                role=GuildRole.GUILDMASTER,
                joined_date=datetime.now(),
                contribution_points=0,
                activity_score=100.0
            )

            # Store all data
            self.guilds[guild_id] = guild
            self.guild_members[guild_id] = {creator_id: guild_member}
            self.guild_halls[guild_id] = guild_hall
            self.guild_objectives[guild_id] = []
            self.guild_alliances[guild_id] = []

            # Initialize progression cache
            self.guild_progression_cache[guild_id] = {
                "last_calculated": datetime.now(),
                "daily_activity": {},
                "weekly_progress": {},
                "monthly_stats": {}
            }

            self.logger.info(f"Guild '{guild['name']}' created by {creator_id}")

            return {
                "success": True,
                "guild_id": guild_id,
                "guild": guild,
                "message": f"Guild '{guild['name']}' has been founded!"
            }

        except Exception as e:
            self.logger.error(f"Error creating guild: {e}")
            return {"success": False, "error": str(e)}

    async def _validate_guild_creation(self, creator_id: str, guild_data: Dict) -> Dict:
        """Validate guild creation requirements"""
        try:
            # Check if creator is already in a guild
            existing_guilds = await self._get_player_guilds(creator_id)
            if len(existing_guilds) >= self.config["max_guilds_per_player"]:
                return {"valid": False, "error": "Already at maximum guild limit"}

            # Validate guild name
            name = guild_data.get("name", "").strip()
            if len(name) < self.config["guild_name_min_length"]:
                return {"valid": False, "error": "Guild name too short"}
            if len(name) > self.config["guild_name_max_length"]:
                return {"valid": False, "error": "Guild name too long"}

            # Check for name conflicts
            for guild in self.guilds.values():
                if guild["name"].lower() == name.lower():
                    return {"valid": False, "error": "Guild name already taken"}

            # Validate creator requirements (level, reputation, etc.)
            player_info = await self._get_player_info(creator_id)
            if not player_info:
                return {"valid": False, "error": "Player not found"}

            if player_info.get("level", 1) < 10:
                return {"valid": False, "error": "Player must be at least level 10 to create a guild"}

            if player_info.get("reputation", 0) < 100:
                return {"valid": False, "error": "Insufficient reputation to create a guild"}

            # Check funds
            if player_info.get("gold", 0) < self.config["guild_creation_cost"]:
                return {"valid": False, "error": "Insufficient funds to create a guild"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating guild creation: {e}")
            return {"valid": False, "error": str(e)}

    async def join_guild(self, player_id: str, guild_id: str, inviter_id: Optional[str] = None) -> Dict:
        """Join an existing guild"""
        try:
            # Validate guild exists and is accepting members
            if guild_id not in self.guilds:
                return {"success": False, "error": "Guild not found"}

            guild = self.guilds[guild_id]

            # Check if player is already in a guild
            existing_guilds = await self._get_player_guilds(player_id)
            if guild_id in existing_guilds:
                return {"success": False, "error": "Already a member of this guild"}

            if len(existing_guilds) >= self.config["max_guilds_per_player"]:
                return {"success": False, "error": "Already at maximum guild limit"}

            # Check guild capacity
            current_members = len(self.guild_members.get(guild_id, {}))
            max_members = self.guild_halls[guild_id].max_members
            if current_members >= max_members:
                return {"success": False, "error": "Guild is at maximum capacity"}

            # Check if invitation is required
            if guild["settings"]["invite_only"] and not inviter_id:
                return {"success": False, "error": "Guild requires invitation to join"}

            # Validate invitation if provided
            if inviter_id:
                inviter_valid = await self._validate_invitation(inviter_id, guild_id, player_id)
                if not inviter_valid:
                    return {"success": False, "error": "Invalid invitation"}

            # Check player requirements
            player_info = await self._get_player_info(player_id)
            if player_info.get("level", 1) < guild["settings"]["min_level_requirement"]:
                return {"success": False, "error": "Does not meet minimum level requirement"}

            # Create guild member
            guild_member = GuildMember(
                player_id=player_id,
                name=player_info.get("name", "Unknown"),
                role=GuildRole.RECRUIT,
                joined_date=datetime.now(),
                contribution_points=0,
                activity_score=50.0
            )

            # Add to guild
            self.guild_members[guild_id][player_id] = guild_member

            # Update guild statistics
            guild["statistics"]["total_members"] += 1

            # Create welcome notification
            await self._send_guild_notification(
                guild_id,
                "new_member",
                f"{guild_member.name} has joined the guild!",
                {"player_id": player_id, "role": GuildRole.RECRUIT.value}
            )

            self.logger.info(f"Player {player_id} joined guild {guild_id}")

            return {
                "success": True,
                "guild_id": guild_id,
                "role": GuildRole.RECRUIT.value,
                "message": f"Welcome to {guild['name']}!"
            }

        except Exception as e:
            self.logger.error(f"Error joining guild: {e}")
            return {"success": False, "error": str(e)}

    async def leave_guild(self, player_id: str, guild_id: str, reason: str = "") -> Dict:
        """Leave a guild"""
        try:
            if guild_id not in self.guild_members:
                return {"success": False, "error": "Guild not found"}

            if player_id not in self.guild_members[guild_id]:
                return {"success": False, "error": "Not a member of this guild"}

            member = self.guild_members[guild_id][player_id]

            # Check if guild master (special handling required)
            if member.role == GuildRole.GUILDMASTER:
                # Check if there are other officers to transfer leadership to
                officers = [
                    m for m in self.guild_members[guild_id].values()
                    if m.role in [GuildRole.OFFICER, GuildRole.VETERAN] and m.player_id != player_id
                ]

                if not officers:
                    return {
                        "success": False,
                        "error": "Cannot leave guild as master without transferring leadership"
                    }

            # Remove from guild
            del self.guild_members[guild_id][player_id]

            # Update guild statistics
            self.guilds[guild_id]["statistics"]["total_members"] -= 1

            # Create departure notification
            await self._send_guild_notification(
                guild_id,
                "member_left",
                f"{member.name} has left the guild" + (f": {reason}" if reason else ""),
                {"player_id": player_id, "reason": reason}
            )

            self.logger.info(f"Player {player_id} left guild {guild_id}")

            return {
                "success": True,
                "message": f"You have left {self.guilds[guild_id]['name']}"
            }

        except Exception as e:
            self.logger.error(f"Error leaving guild: {e}")
            return {"success": False, "error": str(e)}

    async def promote_member(self, leader_id: str, guild_id: str, target_id: str, new_role: GuildRole) -> Dict:
        """Promote a guild member"""
        try:
            # Validate permissions
            if not await self._has_permission(leader_id, guild_id, "member_promote"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guild_members:
                return {"success": False, "error": "Guild not found"}

            if target_id not in self.guild_members[guild_id]:
                return {"success": False, "error": "Target member not found"}

            # Get role hierarchy
            leader_role = self.guild_members[guild_id][leader_id].role
            target_member = self.guild_members[guild_id][target_id]

            # Validate promotion is allowed
            if not self._can_promote_to(leader_role, target_member.role, new_role):
                return {"success": False, "error": "Cannot promote to this level"}

            # Check promotion requirements
            promotion_valid = await self._validate_promotion_requirements(target_id, new_role)
            if not promotion_valid["valid"]:
                return {"success": False, "error": promotion_valid["error"]}

            # Update member role
            old_role = target_member.role
            target_member.role = new_role

            # Create promotion notification
            await self._send_guild_notification(
                guild_id,
                "member_promoted",
                f"{target_member.name} has been promoted to {self.guild_ranks[new_role].title}!",
                {"player_id": target_id, "old_role": old_role.value, "new_role": new_role.value}
            )

            self.logger.info(f"Player {target_id} promoted to {new_role.value} in guild {guild_id}")

            return {
                "success": True,
                "player_id": target_id,
                "old_role": old_role.value,
                "new_role": new_role.value,
                "message": f"{target_member.name} promoted to {self.guild_ranks[new_role].title}"
            }

        except Exception as e:
            self.logger.error(f"Error promoting member: {e}")
            return {"success": False, "error": str(e)}

    async def demote_member(self, leader_id: str, guild_id: str, target_id: str, new_role: GuildRole) -> Dict:
        """Demote a guild member"""
        try:
            # Validate permissions
            if not await self._has_permission(leader_id, guild_id, "member_demote"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guild_members:
                return {"success": False, "error": "Guild not found"}

            if target_id not in self.guild_members[guild_id]:
                return {"success": False, "error": "Target member not found"}

            # Get role hierarchy
            leader_role = self.guild_members[guild_id][leader_id].role
            target_member = self.guild_members[guild_id][target_id]

            # Validate demotion is allowed
            if not self._can_demote_to(leader_role, target_member.role, new_role):
                return {"success": False, "error": "Cannot demote to this level"}

            # Update member role
            old_role = target_member.role
            target_member.role = new_role

            # Create demotion notification
            await self._send_guild_notification(
                guild_id,
                "member_demoted",
                f"{target_member.name} has been demoted to {self.guild_ranks[new_role].title}",
                {"player_id": target_id, "old_role": old_role.value, "new_role": new_role.value}
            )

            self.logger.info(f"Player {target_id} demoted to {new_role.value} in guild {guild_id}")

            return {
                "success": True,
                "player_id": target_id,
                "old_role": old_role.value,
                "new_role": new_role.value,
                "message": f"{target_member.name} demoted to {self.guild_ranks[new_role].title}"
            }

        except Exception as e:
            self.logger.error(f"Error demoting member: {e}")
            return {"success": False, "error": str(e)}

    async def kick_member(self, leader_id: str, guild_id: str, target_id: str, reason: str = "") -> Dict:
        """Kick a member from the guild"""
        try:
            # Validate permissions
            if not await self._has_permission(leader_id, guild_id, "member_kick"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guild_members:
                return {"success": False, "error": "Guild not found"}

            if target_id not in self.guild_members[guild_id]:
                return {"success": False, "error": "Target member not found"}

            # Get role hierarchy
            leader_role = self.guild_members[guild_id][leader_id].role
            target_member = self.guild_members[guild_id][target_id]

            # Cannot kick equal or higher rank members
            if not self._can_kick_member(leader_role, target_member.role):
                return {"success": False, "error": "Cannot kick member of equal or higher rank"}

            # Remove member from guild
            del self.guild_members[guild_id][target_id]

            # Update guild statistics
            self.guilds[guild_id]["statistics"]["total_members"] -= 1

            # Create kick notification
            await self._send_guild_notification(
                guild_id,
                "member_kicked",
                f"{target_member.name} has been removed from the guild" + (f": {reason}" if reason else ""),
                {"player_id": target_id, "reason": reason, "kicked_by": leader_id}
            )

            self.logger.info(f"Player {target_id} kicked from guild {guild_id} by {leader_id}")

            return {
                "success": True,
                "player_id": target_id,
                "message": f"{target_member.name} has been removed from the guild"
            }

        except Exception as e:
            self.logger.error(f"Error kicking member: {e}")
            return {"success": False, "error": str(e)}

    async def transfer_leadership(self, current_leader_id: str, guild_id: str, new_leader_id: str) -> Dict:
        """Transfer guild leadership to another member"""
        try:
            if guild_id not in self.guild_members:
                return {"success": False, "error": "Guild not found"}

            # Validate current leader
            current_member = self.guild_members[guild_id].get(current_leader_id)
            if not current_member or current_member.role != GuildRole.GUILDMASTER:
                return {"success": False, "error": "Only guild master can transfer leadership"}

            # Validate new leader
            new_member = self.guild_members[guild_id].get(new_leader_id)
            if not new_member:
                return {"success": False, "error": "Target member not found"}

            # Transfer leadership
            old_master_role = current_member.role
            new_master_role = GuildRole.GUILDMASTER

            current_member.role = GuildRole.HONORED  # Honor former master
            new_member.role = new_master_role

            # Update guild master ID
            self.guilds[guild_id]["master_id"] = new_leader_id

            # Create leadership transfer notification
            await self._send_guild_notification(
                guild_id,
                "leadership_transferred",
                f"Leadership has been transferred from {current_member.name} to {new_member.name}",
                {
                    "old_master": current_leader_id,
                    "new_master": new_leader_id,
                    "old_master_name": current_member.name,
                    "new_master_name": new_member.name
                }
            )

            self.logger.info(f"Leadership of guild {guild_id} transferred from {current_leader_id} to {new_leader_id}")

            return {
                "success": True,
                "old_master": current_leader_id,
                "new_master": new_leader_id,
                "message": f"Leadership transferred to {new_member.name}"
            }

        except Exception as e:
            self.logger.error(f"Error transferring leadership: {e}")
            return {"success": False, "error": str(e)}

    async def create_guild_objective(self, creator_id: str, guild_id: str, objective_data: Dict) -> Dict:
        """Create a new guild objective"""
        try:
            # Validate permissions
            if not await self._has_permission(creator_id, guild_id, "objective_create"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guilds:
                return {"success": False, "error": "Guild not found"}

            # Check objective limit
            if len(self.guild_objectives.get(guild_id, [])) >= self.config["guild_objective_limit"]:
                return {"success": False, "error": "Maximum objectives limit reached"}

            # Create objective
            objective_id = str(uuid.uuid4())
            objective = GuildObjective(
                id=objective_id,
                title=objective_data["title"],
                description=objective_data.get("description", ""),
                type=objective_data.get("type", "general"),
                requirements=objective_data.get("requirements", {}),
                rewards=objective_data.get("rewards", {}),
                deadline=datetime.fromisoformat(objective_data["deadline"]) if objective_data.get("deadline") else None,
                created_by=creator_id,
                status="active"
            )

            # Initialize progress based on requirements
            for req_key, req_value in objective.requirements.items():
                objective.progress[req_key] = 0.0

            # Add to guild objectives
            if guild_id not in self.guild_objectives:
                self.guild_objectives[guild_id] = []
            self.guild_objectives[guild_id].append(objective)

            # Create objective notification
            await self._send_guild_notification(
                guild_id,
                "new_objective",
                f"New Guild Objective: {objective.title}",
                {"objective_id": objective_id, "type": objective.type, "deadline": objective.deadline}
            )

            self.logger.info(f"Guild objective '{objective.title}' created for guild {guild_id}")

            return {
                "success": True,
                "objective_id": objective_id,
                "objective": asdict(objective),
                "message": f"Guild objective '{objective.title}' created"
            }

        except Exception as e:
            self.logger.error(f"Error creating guild objective: {e}")
            return {"success": False, "error": str(e)}

    async def update_objective_progress(self, player_id: str, guild_id: str, objective_id: str, progress_data: Dict) -> Dict:
        """Update progress on a guild objective"""
        try:
            if guild_id not in self.guild_objectives:
                return {"success": False, "error": "Guild objectives not found"}

            # Find objective
            objective = None
            for obj in self.guild_objectives[guild_id]:
                if obj.id == objective_id:
                    objective = obj
                    break

            if not objective:
                return {"success": False, "error": "Objective not found"}

            if objective.status != "active":
                return {"success": False, "error": "Objective is not active"}

            # Update progress
            updated = False
            for key, value in progress_data.items():
                if key in objective.progress:
                    objective.progress[key] = min(objective.progress[key] + value, objective.requirements.get(key, 0))
                    updated = True

            if not updated:
                return {"success": False, "error": "No valid progress updates"}

            # Check if objective is completed
            completed = all(
                objective.progress[key] >= objective.requirements.get(key, 0)
                for key in objective.requirements
            )

            if completed:
                objective.status = "completed"

                # Distribute rewards
                await self._distribute_objective_rewards(guild_id, objective)

                # Create completion notification
                await self._send_guild_notification(
                    guild_id,
                    "objective_completed",
                    f"Guild Objective Completed: {objective.title}!",
                    {"objective_id": objective_id, "rewards": objective.rewards}
                )

                self.logger.info(f"Guild objective '{objective.title}' completed for guild {guild_id}")

            return {
                "success": True,
                "objective_id": objective_id,
                "progress": objective.progress,
                "completed": completed,
                "message": "Objective progress updated" + (" - Objective completed!" if completed else "")
            }

        except Exception as e:
            self.logger.error(f"Error updating objective progress: {e}")
            return {"success": False, "error": str(e)}

    async def upgrade_guild_hall(self, leader_id: str, guild_id: str, upgrade_type: str) -> Dict:
        """Upgrade the guild hall"""
        try:
            # Validate permissions
            if not await self._has_permission(leader_id, guild_id, "hall_upgrade"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guild_halls:
                return {"success": False, "error": "Guild hall not found"}

            guild_hall = self.guild_halls[guild_id]
            guild = self.guilds[guild_id]

            # Calculate upgrade cost and requirements
            upgrade_info = await self._get_hall_upgrade_info(upgrade_type, guild_hall.level)
            if not upgrade_info:
                return {"success": False, "error": "Invalid upgrade type"}

            # Check if guild can afford upgrade
            if guild["funds"] < upgrade_info["cost"]:
                return {"success": False, "error": "Insufficient guild funds"}

            # Check requirements
            for req, value in upgrade_info["requirements"].items():
                if req == "guild_level" and guild["level"] < value:
                    return {"success": False, "error": f"Guild must be level {value} to purchase this upgrade"}
                elif req == "member_count" and len(self.guild_members[guild_id]) < value:
                    return {"success": False, "error": f"Requires {value} members to purchase this upgrade"}

            # Apply upgrade
            guild["funds"] -= upgrade_info["cost"]

            if upgrade_type == "level":
                guild_hall.level += 1
                guild_hall.max_members += 10
                guild_hall.storage_capacity += 500
                guild_hall.upkeep_cost *= 1.2

                # Unlock new features
                new_features = await self._get_unlocked_hall_features(guild_hall.level)
                guild_hall.features.extend(new_features)

            elif upgrade_type == "storage":
                guild_hall.storage_capacity += upgrade_info["capacity_bonus"]

            elif upgrade_type == "member_capacity":
                guild_hall.max_members += upgrade_info["member_bonus"]

            # Create upgrade notification
            await self._send_guild_notification(
                guild_id,
                "hall_upgraded",
                f"Guild Hall upgraded: {upgrade_info['name']}",
                {"upgrade_type": upgrade_type, "cost": upgrade_info["cost"], "new_level": guild_hall.level}
            )

            self.logger.info(f"Guild hall upgraded for guild {guild_id}: {upgrade_type}")

            return {
                "success": True,
                "upgrade_type": upgrade_type,
                "new_level": guild_hall.level,
                "cost": upgrade_info["cost"],
                "message": f"Guild Hall successfully upgraded!"
            }

        except Exception as e:
            self.logger.error(f"Error upgrading guild hall: {e}")
            return {"success": False, "error": str(e)}

    async def create_alliance(self, creator_id: str, guild_id: str, target_guild_id: str, alliance_data: Dict) -> Dict:
        """Create an alliance with another guild"""
        try:
            # Validate permissions
            if not await self._has_permission(creator_id, guild_id, "alliance_create"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guilds or target_guild_id not in self.guilds:
                return {"success": False, "error": "One or both guilds not found"}

            # Check alliance limit
            if len(self.guild_alliances.get(guild_id, [])) >= self.config["max_alliances_per_guild"]:
                return {"success": False, "error": "Maximum alliance limit reached"}

            # Check for existing alliance
            for alliance in self.guild_alliances.get(guild_id, []):
                if alliance.allied_guild_id == target_guild_id and alliance.status == "active":
                    return {"success": False, "error": "Alliance already exists"}

            # Create alliance
            alliance_id = str(uuid.uuid4())
            alliance = GuildAlliance(
                id=alliance_id,
                guild_id=guild_id,
                allied_guild_id=target_guild_id,
                type=alliance_data.get("type", "alliance"),
                terms=alliance_data.get("terms", {}),
                benefits=alliance_data.get("benefits", []),
                obligations=alliance_data.get("obligations", []),
                start_date=datetime.now(),
                end_date=datetime.fromisoformat(alliance_data["end_date"]) if alliance_data.get("end_date") else None,
                status="pending"  # Requires approval from target guild
            )

            # Add to alliance lists
            if guild_id not in self.guild_alliances:
                self.guild_alliances[guild_id] = []
            self.guild_alliances[guild_id].append(alliance)

            if target_guild_id not in self.guild_alliances:
                self.guild_alliances[target_guild_id] = []

            # Create mirrored alliance for target guild
            mirrored_alliance = GuildAlliance(
                id=alliance_id,
                guild_id=target_guild_id,
                allied_guild_id=guild_id,
                type=alliance.type,
                terms=alliance.terms,
                benefits=alliance.benefits,
                obligations=alliance.obligations,
                start_date= alliance.start_date,
                end_date= alliance.end_date,
                status="pending_approval"
            )
            self.guild_alliances[target_guild_id].append(mirrored_alliance)

            # Send alliance request notification to target guild
            await self._send_guild_notification(
                target_guild_id,
                "alliance_request",
                f"Alliance request from {self.guilds[guild_id]['name']}",
                {
                    "alliance_id": alliance_id,
                    "requesting_guild": guild_id,
                    "alliance_type": alliance.type,
                    "terms": alliance.terms
                }
            )

            self.logger.info(f"Alliance request created between guilds {guild_id} and {target_guild_id}")

            return {
                "success": True,
                "alliance_id": alliance_id,
                "status": "pending",
                "message": f"Alliance request sent to {self.guilds[target_guild_id]['name']}"
            }

        except Exception as e:
            self.logger.error(f"Error creating alliance: {e}")
            return {"success": False, "error": str(e)}

    async def respond_to_alliance_request(self, responder_id: str, guild_id: str, alliance_id: str, response: str) -> Dict:
        """Respond to an alliance request"""
        try:
            # Validate permissions
            if not await self._has_permission(responder_id, guild_id, "alliance_respond"):
                return {"success": False, "error": "Insufficient permissions"}

            if guild_id not in self.guild_alliances:
                return {"success": False, "error": "Guild alliances not found"}

            # Find alliance
            alliance = None
            for a in self.guild_alliances[guild_id]:
                if a.id == alliance_id:
                    alliance = a
                    break

            if not alliance:
                return {"success": False, "error": "Alliance request not found"}

            if alliance.status not in ["pending_approval"]:
                return {"success": False, "error": "Alliance request is not pending"}

            # Update alliance status
            if response == "accept":
                alliance.status = "active"

                # Update mirrored alliance
                for guild_alliances in self.guild_alliances.values():
                    for a in guild_alliances:
                        if a.id == alliance_id:
                            a.status = "active"
                            break

                # Update guild diplomacy
                self.guilds[guild_id]["diplomacy"]["allied_guilds"].append(alliance.allied_guild_id)
                self.guilds[alliance.allied_guild_id]["diplomacy"]["allied_guilds"].append(guild_id)

                message = f"Alliance accepted with {self.guilds[alliance.allied_guild_id]['name']}!"

            elif response == "reject":
                alliance.status = "rejected"

                # Update mirrored alliance
                for guild_alliances in self.guild_alliances.values():
                    for a in guild_alliances:
                        if a.id == alliance_id:
                            a.status = "rejected"
                            break

                message = f"Alliance request from {self.guilds[alliance.allied_guild_id]['name']} rejected"

            else:
                return {"success": False, "error": "Invalid response"}

            # Notify both guilds
            await self._send_guild_notification(
                guild_id,
                "alliance_response",
                message,
                {"alliance_id": alliance_id, "response": response, "target_guild": alliance.allied_guild_id}
            )

            await self._send_guild_notification(
                alliance.allied_guild_id,
                "alliance_response",
                f"Alliance {response} by {self.guilds[guild_id]['name']}",
                {"alliance_id": alliance_id, "response": response, "responder_guild": guild_id}
            )

            self.logger.info(f"Alliance {response} between guilds {guild_id} and {alliance.allied_guild_id}")

            return {
                "success": True,
                "alliance_id": alliance_id,
                "response": response,
                "message": message
            }

        except Exception as e:
            self.logger.error(f"Error responding to alliance request: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_guild_progression(self, guild_id: str) -> Dict:
        """Calculate guild progression and level up if applicable"""
        try:
            if guild_id not in self.guilds:
                return {"success": False, "error": "Guild not found"}

            guild = self.guilds[guild_id]
            current_level = guild["level"]
            current_exp = guild["experience"]
            exp_to_next = guild["progression"]["experience_to_next"]

            # Check for level up
            if current_exp >= exp_to_next:
                # Level up
                new_level = current_level + 1
                guild["level"] = new_level
                guild["experience"] -= exp_to_next
                guild["progression"]["experience_to_next"] = self._calculate_exp_for_level(new_level + 1)

                # Unlock new features
                new_features = await self._get_unlocked_guild_features(new_level)
                guild["progression"]["unlocked_features"].extend(new_features)

                # Add milestone
                milestone = {
                    "type": "level_up",
                    "level": new_level,
                    "timestamp": datetime.now().isoformat(),
                    "features_unlocked": new_features
                }
                guild["progression"]["milestones_reached"].append(milestone)

                # Create level up notification
                await self._send_guild_notification(
                    guild_id,
                    "guild_level_up",
                    f"Guild has reached Level {new_level}!",
                    {
                        "new_level": new_level,
                        "features_unlocked": new_features,
                        "exp_to_next": guild["progression"]["experience_to_next"]
                    }
                )

                self.logger.info(f"Guild {guild_id} leveled up to {new_level}")

                return {
                    "success": True,
                    "leveled_up": True,
                    "new_level": new_level,
                    "features_unlocked": new_features,
                    "message": f"Guild has reached Level {new_level}!"
                }

            # Calculate progression percentage
            progression_percentage = (current_exp / exp_to_next) * 100

            return {
                "success": True,
                "leveled_up": False,
                "current_level": current_level,
                "current_exp": current_exp,
                "exp_to_next": exp_to_next,
                "progression_percentage": progression_percentage
            }

        except Exception as e:
            self.logger.error(f"Error calculating guild progression: {e}")
            return {"success": False, "error": str(e)}

    async def award_guild_experience(self, guild_id: str, amount: int, source: str, source_details: Dict = None) -> Dict:
        """Award experience to a guild"""
        try:
            if guild_id not in self.guilds:
                return {"success": False, "error": "Guild not found"}

            guild = self.guilds[guild_id]

            # Add experience
            guild["experience"] += amount
            guild["progression"]["total_experience_earned"] += amount

            # Log activity
            activity = {
                "type": "experience_gained",
                "amount": amount,
                "source": source,
                "details": source_details or {},
                "timestamp": datetime.now().isoformat()
            }

            if guild_id not in self.active_guild_activities:
                self.active_guild_activities[guild_id] = []
            self.active_guild_activities[guild_id].append(activity)

            # Check for level up
            progression_result = await self.calculate_guild_progression(guild_id)

            # Create experience notification
            await self._send_guild_notification(
                guild_id,
                "experience_gained",
                f"Guild gained {amount} experience from {source}",
                {"amount": amount, "source": source, "total": guild["experience"]}
            )

            self.logger.info(f"Guild {guild_id} gained {amount} experience from {source}")

            return {
                "success": True,
                "amount": amount,
                "total_experience": guild["experience"],
                "leveled_up": progression_result.get("leveled_up", False),
                "message": f"Awarded {amount} experience to guild"
            }

        except Exception as e:
            self.logger.error(f"Error awarding guild experience: {e}")
            return {"success": False, "error": str(e)}

    async def get_guild_info(self, guild_id: str, viewer_id: Optional[str] = None) -> Dict:
        """Get comprehensive guild information"""
        try:
            if guild_id not in self.guilds:
                return {"success": False, "error": "Guild not found"}

            guild = self.guilds[guild_id]
            guild_hall = self.guild_halls.get(guild_id)
            members = self.guild_members.get(guild_id, {})
            objectives = self.guild_objectives.get(guild_id, [])
            alliances = self.guild_alliances.get(guild_id, [])

            # Check viewing permissions
            is_member = viewer_id in members if viewer_id else False

            # Prepare guild data
            guild_info = {
                "id": guild["id"],
                "name": guild["name"],
                "description": guild["description"],
                "type": guild["type"],
                "level": guild["level"],
                "experience": guild["experience"],
                "reputation": guild["reputation"],
                "founded_date": guild["founded_date"],
                "member_count": len(members),
                "statistics": guild["statistics"],
                "progression": guild["progression"],
                "public_recruitment": guild["settings"]["public_recruitment"],
                "min_level_requirement": guild["settings"]["min_level_requirement"]
            }

            # Add additional info for members
            if is_member:
                guild_info.update({
                    "funds": guild["funds"],
                    "settings": guild["settings"],
                    "diplomacy": guild["diplomacy"],
                    "hall": {
                        "name": guild_hall.name if guild_hall else "",
                        "level": guild_hall.level if guild_hall else 1,
                        "features": guild_hall.features if guild_hall else [],
                        "max_members": guild_hall.max_members if guild_hall else 50,
                        "storage_capacity": guild_hall.storage_capacity if guild_hall else 1000
                    },
                    "members": {
                        player_id: {
                            "name": member.name,
                            "role": member.role.value,
                            "joined_date": member.joined_date.isoformat(),
                            "contribution_points": member.contribution_points,
                            "activity_score": member.activity_score,
                            "last_active": member.last_active.isoformat(),
                            "titles": member.titles
                        }
                        for player_id, member in members.items()
                    },
                    "objectives": [asdict(obj) for obj in objectives if obj.status == "active"],
                    "completed_objectives": [asdict(obj) for obj in objectives if obj.status == "completed"],
                    "alliances": [asdict(alliance) for alliance in alliances if alliance.status == "active"],
                    "recent_activities": self.active_guild_activities.get(guild_id, [])[-10:]
                })

                # Add viewer's specific info
                if viewer_id and viewer_id in members:
                    viewer_member = members[viewer_id]
                    guild_info["viewer_info"] = {
                        "role": viewer_member.role.value,
                        "contribution_points": viewer_member.contribution_points,
                        "permissions": self.guild_ranks[viewer_member.role].permissions,
                        "benefits": self.guild_ranks[viewer_member.role].benefits,
                        "joined_date": viewer_member.joined_date.isoformat()
                    }

            return {
                "success": True,
                "guild": guild_info,
                "is_member": is_member
            }

        except Exception as e:
            self.logger.error(f"Error getting guild info: {e}")
            return {"success": False, "error": str(e)}

    async def get_guild_leaderboard(self, sort_by: str = "level", limit: int = 50) -> Dict:
        """Get guild leaderboard"""
        try:
            guilds_data = []

            for guild_id, guild in self.guilds.items():
                members = self.guild_members.get(guild_id, {})

                guild_data = {
                    "id": guild_id,
                    "name": guild["name"],
                    "type": guild["type"],
                    "level": guild["level"],
                    "experience": guild["experience"],
                    "reputation": guild["reputation"],
                    "member_count": len(members),
                    "founded_date": guild["founded_date"],
                    "total_contribution": sum(m.contribution_points for m in members.values()),
                    "average_activity": sum(m.activity_score for m in members.values()) / len(members) if members else 0,
                    "statistics": guild["statistics"]
                }

                guilds_data.append(guild_data)

            # Sort guilds
            reverse_sort = sort_by in ["level", "experience", "reputation", "member_count", "total_contribution", "average_activity"]
            guilds_data.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse_sort)

            # Apply limit
            leaderboard = guilds_data[:limit]

            return {
                "success": True,
                "leaderboard": leaderboard,
                "sort_by": sort_by,
                "total_guilds": len(guilds_data)
            }

        except Exception as e:
            self.logger.error(f"Error getting guild leaderboard: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    def _can_promote_to(self, leader_role: GuildRole, target_role: GuildRole, new_role: GuildRole) -> bool:
        """Check if leader can promote target to new role"""
        leader_level = self.config["rank_permission_levels"][leader_role]
        target_level = self.config["rank_permission_levels"][target_role]
        new_level = self.config["rank_permission_levels"][new_role]

        # Leader must be higher level than target
        # New level must be higher than current target level
        # Leader must be high enough to grant new level
        return (leader_level > target_level and
                new_level > target_level and
                leader_level >= new_level)

    def _can_demote_to(self, leader_role: GuildRole, target_role: GuildRole, new_role: GuildRole) -> bool:
        """Check if leader can demote target to new role"""
        leader_level = self.config["rank_permission_levels"][leader_role]
        target_level = self.config["rank_permission_levels"][target_role]
        new_level = self.config["rank_permission_levels"][new_role]

        # Leader must be higher level than target
        # New level must be lower than current target level
        # Leader must be high enough to assign new level
        return (leader_level > target_level and
                new_level < target_level and
                leader_level >= new_level)

    def _can_kick_member(self, leader_role: GuildRole, target_role: GuildRole) -> bool:
        """Check if leader can kick target member"""
        leader_level = self.config["rank_permission_levels"][leader_role]
        target_level = self.config["rank_permission_levels"][target_role]

        # Can only kick lower level members
        return leader_level > target_level

    def _calculate_exp_for_level(self, level: int) -> int:
        """Calculate experience required for a specific level"""
        # Exponential growth: base * (1.5 ^ (level - 1))
        base_exp = 1000
        return int(base_exp * (1.5 ** (level - 1)))

    async def _get_player_info(self, player_id: str) -> Optional[Dict]:
        """Get player information from database"""
        # This would integrate with your player database
        # For now, return mock data
        return {
            "id": player_id,
            "name": f"Player_{player_id[:8]}",
            "level": 15,
            "reputation": 500,
            "gold": 2000
        }

    async def _get_player_guilds(self, player_id: str) -> List[str]:
        """Get list of guilds player belongs to"""
        guilds = []
        for guild_id, members in self.guild_members.items():
            if player_id in members:
                guilds.append(guild_id)
        return guilds

    async def _has_permission(self, player_id: str, guild_id: str, permission: str) -> bool:
        """Check if player has specific permission in guild"""
        if guild_id not in self.guild_members:
            return False

        if player_id not in self.guild_members[guild_id]:
            return False

        member = self.guild_members[guild_id][player_id]
        role_permissions = self.guild_ranks[member.role].permissions

        return permission in role_permissions or permission in member.custom_permissions

    async def _validate_invitation(self, inviter_id: str, guild_id: str, target_id: str) -> bool:
        """Validate that inviter can invite target to guild"""
        return await self._has_permission(inviter_id, guild_id, "invite_members")

    async def _validate_promotion_requirements(self, player_id: str, new_role: GuildRole) -> Dict:
        """Validate if player meets requirements for promotion"""
        rank_info = self.guild_ranks[new_role]
        player_info = await self._get_player_info(player_id)

        if not player_info:
            return {"valid": False, "error": "Player not found"}

        # Check reputation requirement
        if player_info.get("reputation", 0) < rank_info.requirements.get("reputation", 0):
            return {"valid": False, "error": "Insufficient reputation"}

        # Check time requirement (would need to track join time)
        # This is simplified - in practice you'd track actual join time

        return {"valid": True}

    async def _get_hall_upgrade_info(self, upgrade_type: str, current_level: int) -> Optional[Dict]:
        """Get information about hall upgrade"""
        upgrades = {
            "level": {
                "name": "Hall Level Upgrade",
                "cost": 5000 * current_level,
                "requirements": {"guild_level": current_level}
            },
            "storage": {
                "name": "Storage Expansion",
                "cost": 2000,
                "capacity_bonus": 1000,
                "requirements": {"guild_level": 5}
            },
            "member_capacity": {
                "name": "Member Capacity Increase",
                "cost": 3000,
                "member_bonus": 10,
                "requirements": {"member_count": 30}
            }
        }

        return upgrades.get(upgrade_type)

    async def _get_unlocked_hall_features(self, level: int) -> List[str]:
        """Get features unlocked at specific hall level"""
        feature_map = {
            1: ["basic_hall", "meeting_room", "storage_basic"],
            2: ["crafting_stations"],
            3: ["training_area"],
            4: ["library"],
            5: ["vault", "embassy"],
            6: ["arena"],
            7: ["temple"],
            8: ["marketplace"],
            9: ["war_room"],
            10: ["grand_hall", "all_features"]
        }

        features = []
        for lvl, feats in feature_map.items():
            if level >= lvl:
                features.extend(feats)

        return features

    async def _get_unlocked_guild_features(self, level: int) -> List[str]:
        """Get features unlocked at specific guild level"""
        feature_map = {
            1: ["basic_guild", "guild_chat"],
            2: ["guild_storage"],
            3: ["guild_objectives"],
            4: ["guild_bank"],
            5: ["alliance_system"],
            6: ["guild_halls_advanced"],
            7: ["guild_quests"],
            8: ["guild_pvp"],
            9: ["guild_events"],
            10: ["guild_master_powers"]
        }

        features = []
        for lvl, feats in feature_map.items():
            if level >= lvl:
                features.extend(feats)

        return features

    async def _distribute_objective_rewards(self, guild_id: str, objective: GuildObjective):
        """Distribute rewards for completed objective"""
        if guild_id not in self.guild_members:
            return

        guild = self.guilds[guild_id]

        # Add guild rewards
        if "guild_experience" in objective.rewards:
            await self.award_guild_experience(
                guild_id,
                objective.rewards["guild_experience"],
                "objective_completion",
                {"objective_id": objective.id}
            )

        if "guild_funds" in objective.rewards:
            guild["funds"] += objective.rewards["guild_funds"]

        # Distribute member rewards based on contribution
        total_contribution = sum(
            self.guild_members[guild_id][pid].contribution_points
            for pid in self.guild_members[guild_id]
        )

        if total_contribution > 0:
            for member_id, member in self.guild_members[guild_id].items():
                contribution_ratio = member.contribution_points / total_contribution

                if "member_experience" in objective.rewards:
                    # Award experience proportional to contribution
                    member_exp = int(objective.rewards["member_experience"] * contribution_ratio)
                    # This would integrate with your player experience system

                if "member_gold" in objective.rewards:
                    # Award gold proportional to contribution
                    member_gold = int(objective.rewards["member_gold"] * contribution_ratio)
                    # This would integrate with your player currency system

    async def _send_guild_notification(self, guild_id: str, notification_type: str, message: str, data: Dict):
        """Send notification to guild members"""
        # This would integrate with your notification system
        # For now, just log the notification
        self.logger.info(f"Guild {guild_id} notification [{notification_type}]: {message}")

        # Store notification for guild members to retrieve
        if guild_id not in self.guilds:
            return

        notification = {
            "type": notification_type,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "guild_id": guild_id
        }

        # This would be stored in your notification database
        # and pushed to connected guild members

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Activity decay task
        self._background_tasks.append(
            asyncio.create_task(self._activity_decay_task())
        )

        # Contribution decay task
        self._background_tasks.append(
            asyncio.create_task(self._contribution_decay_task())
        )

        # Guild statistics update task
        self._background_tasks.append(
            asyncio.create_task(self._statistics_update_task())
        )

    async def stop_background_tasks(self):
        """Stop background maintenance tasks"""
        self._running = False

        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()

    async def _activity_decay_task(self):
        """Periodically decay member activity scores"""
        while self._running:
            try:
                for guild_id, members in self.guild_members.items():
                    for member in members.values():
                        # Decay activity score for inactive members
                        days_inactive = (datetime.now() - member.last_active).days

                        if days_inactive > 7:
                            decay_rate = min(0.1 * (days_inactive - 7), 0.5)
                            member.activity_score = max(0, member.activity_score - decay_rate)

                await asyncio.sleep(86400)  # Run daily

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in activity decay task: {e}")
                await asyncio.sleep(3600)  # Retry in an hour

    async def _contribution_decay_task(self):
        """Periodically decay contribution points"""
        while self._running:
            try:
                for guild_id, members in self.guild_members.items():
                    for member in members.values():
                        # Apply daily decay
                        decay = int(member.contribution_points * self.config["contribution_decay_rate"])
                        member.contribution_points = max(0, member.contribution_points - decay)

                await asyncio.sleep(86400)  # Run daily

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in contribution decay task: {e}")
                await asyncio.sleep(3600)  # Retry in an hour

    async def _statistics_update_task(self):
        """Update guild statistics periodically"""
        while self._running:
            try:
                for guild_id, guild in self.guilds.items():
                    if guild_id in self.guild_members:
                        members = self.guild_members[guild_id]

                        # Update statistics
                        guild["statistics"]["total_contribution"] = sum(
                            m.contribution_points for m in members.values()
                        )

                        guild["statistics"]["average_activity"] = sum(
                            m.activity_score for m in members.values()
                        ) / len(members) if members else 0

                await asyncio.sleep(3600)  # Run hourly

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in statistics update task: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

# Usage example and initialization
if __name__ == "__main__":
    async def main():
        # Initialize guild manager
        guild_manager = GuildManager()

        # Start background tasks
        await guild_manager.start_background_tasks()

        # Example usage
        print("Creating guild...")
        result = await guild_manager.create_guild("player123", {
            "name": "Dragon Slayers",
            "description": "We hunt dragons and protect the realm",
            "type": "adventure",
            "creator_name": "DragonMaster"
        })
        print(result)

        if result["success"]:
            guild_id = result["guild_id"]

            # Get guild info
            info = await guild_manager.get_guild_info(guild_id)
            print(f"Guild created: {info['guild']['name']}")

            # Add some members
            await guild_manager.join_guild("player456", guild_id, "player123")
            await guild_manager.join_guild("player789", guild_id, "player123")

            # Create guild objective
            await guild_manager.create_guild_objective("player123", guild_id, {
                "title": "Defeat the Red Dragon",
                "description": "Work together to defeat the ancient red dragon",
                "type": "raid",
                "requirements": {"dragon_kills": 1},
                "rewards": {"guild_experience": 500, "guild_funds": 1000}
            })

            # Award some experience
            await guild_manager.award_guild_experience(guild_id, 250, "quest_completion")

            # Get leaderboard
            leaderboard = await guild_manager.get_guild_leaderboard()
            print(f"Total guilds: {leaderboard['total_guilds']}")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await guild_manager.stop_background_tasks()

    asyncio.run(main())