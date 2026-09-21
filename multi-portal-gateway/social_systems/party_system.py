#!/usr/bin/env python3
"""
DMLogn8n Party System - Comprehensive Party Formation and Collaboration

Handles party formation, leadership mechanics, collaboration tools, shared objectives,
party chat, loot distribution, and group-based gameplay mechanics.

Features:
- Party creation and management
- Leadership and permission systems
- Party chat and coordination
- Loot distribution systems
- Shared quests and objectives
- Party buffs and synergies
- Dynamic party scaling
- Party achievements and rewards
- Cross-guild party formation
- Voice chat integration
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import math

class PartyRole(Enum):
    """Party member roles"""
    LEADER = "leader"
    TANK = "tank"
    HEALER = "healer"
    DPS = "dps"
    SUPPORT = "support"
    MEMBER = "member"
    GUEST = "guest"

class LootDistribution(Enum):
    """Loot distribution methods"""
    FREE_FOR_ALL = "free_for_all"
    NEED_BEFORE_GREED = "need_before_greed"
    ROUND_ROBIN = "round_robin"
    MASTER_LOOTER = "master_looter"
    GROUP_LOOT = "group_loot"
    PERSONAL_LOOT = "personal_loot"

class PartyType(Enum):
    """Types of parties with different focuses"""
    ADVENTURE = "adventure"      # Standard adventuring party
    DUNGEON = "dungeon"          # Dungeon crawling party
    RAID = "raid"               # Large raid group
    PVP = "pvp"                 # Player vs party
    EXPLORATION = "exploration" # Exploration and discovery
    SOCIAL = "social"           # Social gathering
    TRAINING = "training"       # Training and practice
    BOSS_HUNT = "boss_hunt"     # Boss hunting party

class PartyStatus(Enum):
    """Party status states"""
    FORMING = "forming"
    ACTIVE = "active"
    IN_COMBAT = "in_combat"
    RESTING = "resting"
    TRAVELING = "traveling"
    DISBANDING = "disbanding"
    INACTIVE = "inactive"

@dataclass
class PartyMember:
    """Party member information"""
    player_id: str
    name: str
    role: PartyRole
    level: int
    class_type: str
    joined_date: datetime
    ready_status: bool = False
    health_percentage: float = 100.0
    mana_percentage: float = 100.0
    position: Tuple[float, float] = (0.0, 0.0)
    buffs: List[str] = field(default_factory=list)
    debuffs: List[str] = field(default_factory=list)
    contribution_score: int = 0
    is_online: bool = True
    voice_chat_enabled: bool = False
    afk_status: bool = False
    custom_status: str = ""

@dataclass
class PartyLootRule:
    """Loot distribution rule"""
    item_type: str
    distribution_method: LootDistribution
    min_item_quality: str = "common"
    priority_classes: List[str] = field(default_factory=list)
    special_conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PartyQuest:
    """Shared party quest"""
    quest_id: str
    title: str
    description: str
    objectives: List[Dict]
    progress: Dict[str, int] = field(default_factory=dict)
    started_date: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    difficulty: str = "normal"
    required_level: int = 1
    shared_rewards: bool = True
    status: str = "active"

@dataclass
class PartyBuff:
    """Party-wide buff from member synergy"""
    buff_id: str
    name: str
    description: str
    effect_type: str
    value: float
    duration: Optional[float] = None
    source_member: str = ""
    requirements: List[str] = field(default_factory=list)
    stacks: int = 1
    max_stacks: int = 1

@dataclass
class PartyAchievement:
    """Party achievement"""
    achievement_id: str
    title: str
    description: str
    requirements: Dict[str, Any]
    progress: Dict[str, float] = field(default_factory=dict)
    unlocked_date: Optional[datetime] = None
    rewards: Dict[str, Any] = field(default_factory=dict)
    rarity: str = "common"

class PartySystem:
    """Main party management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Party storage
        self.parties: Dict[str, Dict] = {}
        self.party_members: Dict[str, Dict[str, PartyMember]] = {}
        self.party_quests: Dict[str, List[PartyQuest]] = {}
        self.party_buffs: Dict[str, List[PartyBuff]] = {}
        self.party_achievements: Dict[str, List[PartyAchievement]] = {}
        self.party_invitations: Dict[str, List[Dict]] = {}

        # Active party instances
        self.active_party_sessions: Dict[str, Dict] = {}

        # System caches
        self.party_synergy_cache: Dict[str, List[PartyBuff]] = {}
        self.loot_distribution_cache: Dict[str, Dict] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_party_size": 6,
            "max_raid_size": 40,
            "party_disband_timeout": 300,  # 5 minutes
            "invitation_timeout": 60,  # 1 minute
            "ready_check_timeout": 30,  # 30 seconds
            "auto_disband_empty": True,
            "auto_promote_on_leave": True,
            "allow_cross_guild": True,
            "default_loot_method": LootDistribution.NEED_BEFORE_GREED.value,
            "min_level_difference": 10,  # Max level difference in party
            "party_chat_range": 100,  # Distance for proximity chat
            "buff_synergy_range": 50,  # Range for buff synergies
            "shared_quest_range": 200  # Range for shared quest progress
        }

    async def create_party(self, leader_id: str, party_data: Dict) -> Dict:
        """Create a new party"""
        try:
            # Validate party creation
            validation_result = await self._validate_party_creation(leader_id, party_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Generate unique party ID
            party_id = str(uuid.uuid4())

            # Get leader information
            leader_info = await self._get_player_info(leader_id)
            if not leader_info:
                return {"success": False, "error": "Leader not found"}

            # Create party structure
            party = {
                "id": party_id,
                "name": party_data.get("name", f"{leader_info['name']}'s Party"),
                "description": party_data.get("description", ""),
                "type": party_data.get("type", PartyType.ADVENTURE.value),
                "leader_id": leader_id,
                "created_date": datetime.now().isoformat(),
                "status": PartyStatus.FORMING.value,
                "settings": {
                    "loot_method": party_data.get("loot_method", self.config["default_loot_method"]),
                    "loot_threshold": party_data.get("loot_threshold", "uncommon"),
                    "allow_invites": party_data.get("allow_invites", True),
                    "require_ready_check": party_data.get("require_ready_check", False),
                    "auto_accept_ready": party_data.get("auto_accept_ready", False),
                    "voice_chat_enabled": party_data.get("voice_chat_enabled", False),
                    "min_level": party_data.get("min_level", 1),
                    "max_level": party_data.get("max_level", None),
                    "level_range": party_data.get("level_range", self.config["min_level_difference"]),
                    "cross_guild_allowed": party_data.get("cross_guild_allowed", self.config["allow_cross_guild"])
                },
                "statistics": {
                    "quests_completed": 0,
                    "monsters_defeated": 0,
                    "total_loot_value": 0,
                    "experience_gained": 0,
                    "achievements_unlocked": 0,
                    "time_played": 0,
                    "members_joined": 1,
                    "members_left": 0
                },
                "activity_log": [],
                "disband_timer": None
            }

            # Create leader as party member
            leader_member = PartyMember(
                player_id=leader_id,
                name=leader_info["name"],
                role=PartyRole.LEADER,
                level=leader_info["level"],
                class_type=leader_info["class"],
                joined_date=datetime.now(),
                is_online=True
            )

            # Store party data
            self.parties[party_id] = party
            self.party_members[party_id] = {leader_id: leader_member}
            self.party_quests[party_id] = []
            self.party_buffs[party_id] = []
            self.party_achievements[party_id] = []
            self.party_invitations[party_id] = []

            # Create initial party session
            self.active_party_sessions[party_id] = {
                "current_location": None,
                "last_activity": datetime.now(),
                "combat_state": False,
                "ready_check_active": False,
                "voice_chat_channel": None,
                "shared_vision": False
            }

            # Add activity log entry
            await self._add_party_activity(party_id, "party_created", f"Party created by {leader_member.name}")

            self.logger.info(f"Party '{party['name']}' created by {leader_id}")

            return {
                "success": True,
                "party_id": party_id,
                "party": party,
                "message": f"Party '{party['name']}' has been created!"
            }

        except Exception as e:
            self.logger.error(f"Error creating party: {e}")
            return {"success": False, "error": str(e)}

    async def invite_to_party(self, inviter_id: str, party_id: str, target_id: str, message: str = "") -> Dict:
        """Invite a player to join a party"""
        try:
            # Validate party and inviter
            if party_id not in self.parties:
                return {"success": False, "error": "Party not found"}

            party = self.parties[party_id]
            inviter_member = self.party_members[party_id].get(inviter_id)

            if not inviter_member:
                return {"success": False, "error": "Inviter not in party"}

            # Check invite permissions
            if not await self._can_invite(inviter_member, party):
                return {"success": False, "error": "No permission to invite"}

            # Check party capacity
            current_size = len(self.party_members[party_id])
            max_size = self.config["max_raid_size"] if party["type"] == PartyType.RAID.value else self.config["max_party_size"]

            if current_size >= max_size:
                return {"success": False, "error": "Party is full"}

            # Check if target is already in a party
            if await self._get_player_party(target_id):
                return {"success": False, "error": "Target is already in a party"}

            # Check level requirements
            target_info = await self._get_player_info(target_id)
            if not target_info:
                return {"success": False, "error": "Target player not found"}

            if not await self._meets_level_requirements(target_info, party):
                return {"success": False, "error": "Target does not meet level requirements"}

            # Check for existing invitation
            existing_invitation = None
            for inv in self.party_invitations[party_id]:
                if inv["target_id"] == target_id and inv["status"] == "pending":
                    existing_invitation = inv
                    break

            if existing_invitation:
                return {"success": False, "error": "Invitation already sent"}

            # Create invitation
            invitation_id = str(uuid.uuid4())
            invitation = {
                "id": invitation_id,
                "inviter_id": inviter_id,
                "inviter_name": inviter_member.name,
                "target_id": target_id,
                "target_name": target_info["name"],
                "party_id": party_id,
                "party_name": party["name"],
                "message": message,
                "created_date": datetime.now(),
                "expires_date": datetime.now() + timedelta(seconds=self.config["invitation_timeout"]),
                "status": "pending"
            }

            # Store invitation
            self.party_invitations[party_id].append(invitation)

            # Send invitation to target player
            await self._send_party_invitation(target_id, invitation)

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "invitation_sent",
                f"{inviter_member.name} invited {target_info['name']}",
                {"inviter": inviter_id, "target": target_id}
            )

            # Schedule invitation expiration
            asyncio.create_task(self._expire_invitation(invitation_id, party_id))

            self.logger.info(f"Party invitation sent from {inviter_id} to {target_id} for party {party_id}")

            return {
                "success": True,
                "invitation_id": invitation_id,
                "message": f"Invitation sent to {target_info['name']}"
            }

        except Exception as e:
            self.logger.error(f"Error sending party invitation: {e}")
            return {"success": False, "error": str(e)}

    async def accept_invitation(self, player_id: str, invitation_id: str) -> Dict:
        """Accept a party invitation"""
        try:
            # Find invitation
            invitation = None
            party_id = None

            for pid, invitations in self.party_invitations.items():
                for inv in invitations:
                    if inv["id"] == invitation_id and inv["target_id"] == player_id:
                        invitation = inv
                        party_id = pid
                        break

            if not invitation:
                return {"success": False, "error": "Invitation not found"}

            if invitation["status"] != "pending":
                return {"success": False, "error": "Invitation no longer valid"}

            # Check if invitation has expired
            if datetime.now() > invitation["expires_date"]:
                invitation["status"] = "expired"
                return {"success": False, "error": "Invitation has expired"}

            # Get player and party info
            player_info = await self._get_player_info(player_id)
            party = self.parties[party_id]

            if not player_info:
                return {"success": False, "error": "Player not found"}

            # Check if still eligible to join
            if await self._get_player_party(player_id):
                return {"success": False, "error": "Already in a party"}

            # Check party capacity again
            current_size = len(self.party_members[party_id])
            max_size = self.config["max_raid_size"] if party["type"] == PartyType.RAID.value else self.config["max_party_size"]

            if current_size >= max_size:
                invitation["status"] = "party_full"
                return {"success": False, "error": "Party is now full"}

            # Add player to party
            party_member = PartyMember(
                player_id=player_id,
                name=player_info["name"],
                role=PartyRole.MEMBER,
                level=player_info["level"],
                class_type=player_info["class"],
                joined_date=datetime.now(),
                is_online=True
            )

            self.party_members[party_id][player_id] = party_member

            # Update invitation status
            invitation["status"] = "accepted"
            invitation["responded_date"] = datetime.now()

            # Update party statistics
            party["statistics"]["members_joined"] += 1

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "member_joined",
                f"{party_member.name} joined the party",
                {"player_id": player_id, "invited_by": invitation["inviter_id"]}
            )

            # Update party status if forming
            if party["status"] == PartyStatus.FORMING.value and len(self.party_members[party_id]) >= 2:
                party["status"] = PartyStatus.ACTIVE.value
                await self._add_party_activity(party_id, "party_active", "Party is now active")

            # Send notifications
            await self._send_party_notification(party_id, "member_joined", f"{party_member.name} has joined the party!")

            # Calculate party synergies
            await self._calculate_party_synergies(party_id)

            self.logger.info(f"Player {player_id} accepted invitation to party {party_id}")

            return {
                "success": True,
                "party_id": party_id,
                "party": party,
                "role": PartyRole.MEMBER.value,
                "message": f"Joined {party['name']}"
            }

        except Exception as e:
            self.logger.error(f"Error accepting party invitation: {e}")
            return {"success": False, "error": str(e)}

    async def decline_invitation(self, player_id: str, invitation_id: str, reason: str = "") -> Dict:
        """Decline a party invitation"""
        try:
            # Find invitation
            invitation = None
            party_id = None

            for pid, invitations in self.party_invitations.items():
                for inv in invitations:
                    if inv["id"] == invitation_id and inv["target_id"] == player_id:
                        invitation = inv
                        party_id = pid
                        break

            if not invitation:
                return {"success": False, "error": "Invitation not found"}

            if invitation["status"] != "pending":
                return {"success": False, "error": "Invitation no longer valid"}

            # Update invitation status
            invitation["status"] = "declined"
            invitation["responded_date"] = datetime.now()
            invitation["decline_reason"] = reason

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "invitation_declined",
                f"{invitation['target_name']} declined the invitation" + (f": {reason}" if reason else ""),
                {"player_id": player_id, "reason": reason}
            )

            # Send notification to party leader
            await self._send_party_notification(
                party_id,
                "invitation_declined",
                f"{invitation['target_name']} declined the party invitation" + (f": {reason}" if reason else "")
            )

            self.logger.info(f"Player {player_id} declined invitation to party {party_id}")

            return {
                "success": True,
                "message": "Invitation declined"
            }

        except Exception as e:
            self.logger.error(f"Error declining party invitation: {e}")
            return {"success": False, "error": str(e)}

    async def leave_party(self, player_id: str, party_id: str, reason: str = "") -> Dict:
        """Leave a party"""
        try:
            if party_id not in self.party_members:
                return {"success": False, "error": "Party not found"}

            if player_id not in self.party_members[party_id]:
                return {"success": False, "error": "Not a member of this party"}

            party = self.parties[party_id]
            member = self.party_members[party_id][player_id]

            # Handle leader leaving
            if member.role == PartyRole.LEADER:
                return await self._handle_leader_leaving(player_id, party_id, reason)

            # Remove member from party
            del self.party_members[party_id][player_id]

            # Update party statistics
            party["statistics"]["members_left"] += 1

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "member_left",
                f"{member.name} left the party" + (f": {reason}" if reason else ""),
                {"player_id": player_id, "reason": reason}
            )

            # Recalculate party synergies
            await self._calculate_party_synergies(party_id)

            # Check if party should disband
            remaining_members = len(self.party_members[party_id])
            if remaining_members <= 1 and self.config["auto_disband_empty"]:
                await self._disband_party(party_id, "insufficient_members")
                return {
                    "success": True,
                    "party_disbanded": True,
                    "message": f"Left party. Party disbanded due to insufficient members."
                }

            # Send notifications
            await self._send_party_notification(
                party_id,
                "member_left",
                f"{member.name} has left the party" + (f": {reason}" if reason else "")
            )

            self.logger.info(f"Player {player_id} left party {party_id}")

            return {
                "success": True,
                "message": f"You have left {party['name']}"
            }

        except Exception as e:
            self.logger.error(f"Error leaving party: {e}")
            return {"success": False, "error": str(e)}

    async def kick_member(self, leader_id: str, party_id: str, target_id: str, reason: str = "") -> Dict:
        """Kick a member from the party"""
        try:
            # Validate permissions
            if not await self._can_kick_member(leader_id, party_id):
                return {"success": False, "error": "No permission to kick members"}

            if party_id not in self.party_members:
                return {"success": False, "error": "Party not found"}

            if target_id not in self.party_members[party_id]:
                return {"success": False, "error": "Target member not found"}

            if target_id == leader_id:
                return {"success": False, "error": "Cannot kick yourself"}

            party = self.parties[party_id]
            target_member = self.party_members[party_id][target_id]
            leader_member = self.party_members[party_id][leader_id]

            # Remove member from party
            del self.party_members[party_id][target_id]

            # Update party statistics
            party["statistics"]["members_left"] += 1

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "member_kicked",
                f"{target_member.name} was kicked by {leader_member.name}" + (f": {reason}" if reason else ""),
                {"kicker_id": leader_id, "target_id": target_id, "reason": reason}
            )

            # Recalculate party synergies
            await self._calculate_party_synergies(party_id)

            # Send notifications
            await self._send_party_notification(
                party_id,
                "member_kicked",
                f"{target_member.name} has been removed from the party" + (f": {reason}" if reason else "")
            )

            # Send private notification to kicked member
            await self._send_private_notification(
                target_id,
                "kicked_from_party",
                f"You have been removed from {party['name']}" + (f": {reason}" if reason else "")
            )

            # Check if party should disband
            remaining_members = len(self.party_members[party_id])
            if remaining_members <= 1 and self.config["auto_disband_empty"]:
                await self._disband_party(party_id, "insufficient_members")

            self.logger.info(f"Player {target_id} kicked from party {party_id} by {leader_id}")

            return {
                "success": True,
                "message": f"{target_member.name} has been removed from the party"
            }

        except Exception as e:
            self.logger.error(f"Error kicking party member: {e}")
            return {"success": False, "error": str(e)}

    async def promote_member(self, leader_id: str, party_id: str, target_id: str, new_role: PartyRole) -> Dict:
        """Promote a party member to a new role"""
        try:
            # Validate permissions
            if not await self._can_promote_member(leader_id, party_id):
                return {"success": False, "error": "No permission to promote members"}

            if party_id not in self.party_members:
                return {"success": False, "error": "Party not found"}

            if target_id not in self.party_members[party_id]:
                return {"success": False, "error": "Target member not found"}

            party = self.parties[party_id]
            target_member = self.party_members[party_id][target_id]
            leader_member = self.party_members[party_id][leader_id]

            # Validate promotion
            if not self._can_promote_to_role(leader_member.role, target_member.role, new_role):
                return {"success": False, "error": "Cannot promote to this role"}

            # Handle leadership transfer
            if new_role == PartyRole.LEADER:
                return await self._transfer_leadership(leader_id, party_id, target_id)

            # Update member role
            old_role = target_member.role
            target_member.role = new_role

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "member_promoted",
                f"{target_member.name} promoted to {new_role.value}",
                {"player_id": target_id, "old_role": old_role.value, "new_role": new_role.value}
            )

            # Send notifications
            await self._send_party_notification(
                party_id,
                "member_promoted",
                f"{target_member.name} has been promoted to {new_role.value}!"
            )

            self.logger.info(f"Player {target_id} promoted to {new_role.value} in party {party_id}")

            return {
                "success": True,
                "player_id": target_id,
                "old_role": old_role.value,
                "new_role": new_role.value,
                "message": f"{target_member.name} promoted to {new_role.value}"
            }

        except Exception as e:
            self.logger.error(f"Error promoting party member: {e}")
            return {"success": False, "error": str(e)}

    async def start_ready_check(self, initiator_id: str, party_id: str, timeout: int = None) -> Dict:
        """Start a ready check for the party"""
        try:
            # Validate permissions
            if not await self._can_start_ready_check(initiator_id, party_id):
                return {"success": False, "error": "No permission to start ready check"}

            if party_id not in self.active_party_sessions:
                return {"success": False, "error": "Party session not found"}

            session = self.active_party_sessions[party_id]

            if session["ready_check_active"]:
                return {"success": False, "error": "Ready check already in progress"}

            # Start ready check
            session["ready_check_active"] = True
            session["ready_check_initiator"] = initiator_id
            session["ready_check_start_time"] = datetime.now()
            session["ready_check_timeout"] = timeout or self.config["ready_check_timeout"]
            session["ready_check_responses"] = {}

            # Reset all member ready status
            for member in self.party_members[party_id].values():
                member.ready_status = False

            # Send ready check notification
            await self._send_party_notification(
                party_id,
                "ready_check_started",
                f"Ready check started by {self.party_members[party_id][initiator_id].name}!",
                {"timeout": session["ready_check_timeout"]}
            )

            # Schedule ready check timeout
            asyncio.create_task(self._ready_check_timeout(party_id))

            self.logger.info(f"Ready check started for party {party_id} by {initiator_id}")

            return {
                "success": True,
                "timeout": session["ready_check_timeout"],
                "message": "Ready check started"
            }

        except Exception as e:
            self.logger.error(f"Error starting ready check: {e}")
            return {"success": False, "error": str(e)}

    async def respond_ready_check(self, player_id: str, party_id: str, ready: bool) -> Dict:
        """Respond to a ready check"""
        try:
            if party_id not in self.active_party_sessions:
                return {"success": False, "error": "Party session not found"}

            session = self.active_party_sessions[party_id]

            if not session["ready_check_active"]:
                return {"success": False, "error": "No ready check in progress"}

            if player_id not in self.party_members[party_id]:
                return {"success": False, "error": "Not a member of this party"}

            # Record response
            member = self.party_members[party_id][player_id]
            member.ready_status = ready
            session["ready_check_responses"][player_id] = {
                "ready": ready,
                "timestamp": datetime.now(),
                "name": member.name
            }

            # Send response notification
            await self._send_party_notification(
                party_id,
                "ready_check_response",
                f"{member.name} is {'ready' if ready else 'not ready'}!",
                {"player_id": player_id, "ready": ready}
            )

            # Check if all have responded
            total_members = len(self.party_members[party_id])
            responses_count = len(session["ready_check_responses"])

            if responses_count >= total_members:
                await self._complete_ready_check(party_id)

            self.logger.info(f"Player {player_id} responded {'ready' if ready else 'not ready'} to ready check in party {party_id}")

            return {
                "success": True,
                "ready": ready,
                "responses_count": responses_count,
                "total_members": total_members
            }

        except Exception as e:
            self.logger.error(f"Error responding to ready check: {e}")
            return {"success": False, "error": str(e)}

    async def add_party_quest(self, party_id: str, quest_data: Dict) -> Dict:
        """Add a shared quest to the party"""
        try:
            if party_id not in self.parties:
                return {"success": False, "error": "Party not found"}

            # Check quest limit
            if len(self.party_quests[party_id]) >= 10:
                return {"success": False, "error": "Maximum active quests reached"}

            # Create quest
            quest = PartyQuest(
                quest_id=str(uuid.uuid4()),
                title=quest_data["title"],
                description=quest_data.get("description", ""),
                objectives=quest_data.get("objectives", []),
                difficulty=quest_data.get("difficulty", "normal"),
                required_level=quest_data.get("required_level", 1),
                shared_rewards=quest_data.get("shared_rewards", True),
                deadline=datetime.fromisoformat(quest_data["deadline"]) if quest_data.get("deadline") else None
            )

            # Initialize progress
            for objective in quest.objectives:
                quest.progress[objective["id"]] = 0

            # Add to party quests
            self.party_quests[party_id].append(quest)

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "quest_added",
                f"Quest added: {quest.title}",
                {"quest_id": quest.quest_id, "difficulty": quest.difficulty}
            )

            # Send notification
            await self._send_party_notification(
                party_id,
                "quest_added",
                f"New party quest: {quest.title}",
                {"quest_id": quest.quest_id, "objectives": len(quest.objectives)}
            )

            self.logger.info(f"Party quest '{quest.title}' added to party {party_id}")

            return {
                "success": True,
                "quest_id": quest.quest_id,
                "quest": asdict(quest),
                "message": f"Quest '{quest.title}' added to party"
            }

        except Exception as e:
            self.logger.error(f"Error adding party quest: {e}")
            return {"success": False, "error": str(e)}

    async def update_quest_progress(self, player_id: str, party_id: str, quest_id: str, progress_updates: Dict) -> Dict:
        """Update progress on a party quest"""
        try:
            if party_id not in self.party_quests:
                return {"success": False, "error": "Party quests not found"}

            # Find quest
            quest = None
            for q in self.party_quests[party_id]:
                if q.quest_id == quest_id:
                    quest = q
                    break

            if not quest:
                return {"success": False, "error": "Quest not found"}

            if quest.status != "active":
                return {"success": False, "error": "Quest is not active"}

            # Check if player is in range for shared progress
            if not await self._is_in_quest_range(player_id, party_id):
                return {"success": False, "error": "Too far from party for shared quest progress"}

            # Update progress
            updated = False
            for objective_id, amount in progress_updates.items():
                if objective_id in quest.progress:
                    # Find objective requirement
                    requirement = None
                    for obj in quest.objectives:
                        if obj["id"] == objective_id:
                            requirement = obj.get("required", 0)
                            break

                    if requirement:
                        quest.progress[objective_id] = min(quest.progress[objective_id] + amount, requirement)
                        updated = True

            if not updated:
                return {"success": False, "error": "No valid progress updates"}

            # Check if quest is completed
            completed = all(
                quest.progress[obj["id"]] >= obj.get("required", 0)
                for obj in quest.objectives
            )

            if completed:
                quest.status = "completed"
                quest.unlocked_date = datetime.now()

                # Distribute rewards
                await self._distribute_quest_rewards(party_id, quest)

                # Send completion notification
                await self._send_party_notification(
                    party_id,
                    "quest_completed",
                    f"Party quest completed: {quest.title}!",
                    {"quest_id": quest_id, "rewards": quest.rewards}
                )

                self.logger.info(f"Party quest '{quest.title}' completed for party {party_id}")

            return {
                "success": True,
                "quest_id": quest_id,
                "progress": quest.progress,
                "completed": completed,
                "message": "Quest progress updated" + (" - Quest completed!" if completed else "")
            }

        except Exception as e:
            self.logger.error(f"Error updating quest progress: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_party_synergies(self, party_id: str) -> Dict:
        """Calculate and apply party synergies based on member composition"""
        try:
            if party_id not in self.party_members:
                return {"success": False, "error": "Party not found"}

            members = list(self.party_members[party_id].values())
            if len(members) < 2:
                return {"success": True, "synergies": [], "message": "Insufficient members for synergies"}

            # Clear existing synergies
            self.party_buffs[party_id] = []

            # Calculate synergies based on class composition
            synergies = []

            # Class-based synergies
            class_counts = {}
            for member in members:
                class_counts[member.class_type] = class_counts.get(member.class_type, 0) + 1

            # Check for specific class combinations
            if class_counts.get("Warrior", 0) >= 2:
                synergies.append(PartyBuff(
                    buff_id="warrior_bond",
                    name="Warrior's Bond",
                    description="Multiple warriors increase party defense",
                    effect_type="defense",
                    value=0.1 * class_counts["Warrior"],
                    source_member="synergy",
                    requirements=["2x Warrior"]
                ))

            if class_counts.get("Mage", 0) >= 2:
                synergies.append(PartyBuff(
                    buff_id="arcane_synergy",
                    name="Arcane Synergy",
                    description="Multiple mages increase spell power",
                    effect_type="spell_power",
                    value=0.15 * class_counts["Mage"],
                    source_member="synergy",
                    requirements=["2x Mage"]
                ))

            # Role-based synergies
            tank_count = sum(1 for m in members if m.role == PartyRole.TANK)
            healer_count = sum(1 for m in members if m.role == PartyRole.HEALER)

            if tank_count >= 1 and healer_count >= 1:
                synergies.append(PartyBuff(
                    buff_id="balanced_team",
                    name="Balanced Team",
                    description="Tank and healer presence increases party stability",
                    effect_type="health_regeneration",
                    value=0.05,
                    source_member="synergy",
                    requirements=["1x Tank", "1x Healer"]
                ))

            # Size-based synergies
            party_size = len(members)
            if party_size >= 4:
                synergies.append(PartyBuff(
                    buff_id="full_party",
                    name="Full Party",
                    description="Complete party gains experience bonus",
                    effect_type="experience_bonus",
                    value=0.1,
                    source_member="synergy",
                    requirements=["4+ members"]
                ))

            # Store synergies
            self.party_buffs[party_id] = synergies

            # Add activity log entry
            if synergies:
                await self._add_party_activity(
                    party_id,
                    "synergies_calculated",
                    f"Party synergies updated: {len(synergies)} active synergies",
                    {"synergy_count": len(synergies)}
                )

            self.logger.info(f"Calculated {len(synergies)} synergies for party {party_id}")

            return {
                "success": True,
                "synergies": [asdict(synergy) for synergy in synergies],
                "message": f"Updated party synergies: {len(synergies)} active"
            }

        except Exception as e:
            self.logger.error(f"Error calculating party synergies: {e}")
            return {"success": False, "error": str(e)}

    async def distribute_loot(self, party_id: str, loot_data: List[Dict]) -> Dict:
        """Distribute loot among party members"""
        try:
            if party_id not in self.parties:
                return {"success": False, "error": "Party not found"}

            party = self.parties[party_id]
            members = list(self.party_members[party_id].values())
            loot_method = LootDistribution(party["settings"]["loot_method"])

            distribution_results = []

            for item in loot_data:
                item_result = await self._distribute_single_item(party_id, item, members, loot_method)
                distribution_results.append(item_result)

            # Update party statistics
            total_value = sum(item.get("value", 0) for item in loot_data)
            party["statistics"]["total_loot_value"] += total_value

            # Add activity log entry
            await self._add_party_activity(
                party_id,
                "loot_distributed",
                f"Loot distributed using {loot_method.value} method",
                {"item_count": len(loot_data), "total_value": total_value, "method": loot_method.value}
            )

            self.logger.info(f"Distributed {len(loot_data)} items to party {party_id} using {loot_method.value}")

            return {
                "success": True,
                "distribution_results": distribution_results,
                "method": loot_method.value,
                "message": f"Distributed {len(loot_data)} items to party members"
            }

        except Exception as e:
            self.logger.error(f"Error distributing loot: {e}")
            return {"success": False, "error": str(e)}

    async def get_party_info(self, party_id: str, viewer_id: Optional[str] = None) -> Dict:
        """Get comprehensive party information"""
        try:
            if party_id not in self.parties:
                return {"success": False, "error": "Party not found"}

            party = self.parties[party_id]
            members = self.party_members.get(party_id, {})
            quests = self.party_quests.get(party_id, [])
            buffs = self.party_buffs.get(party_id, [])
            achievements = self.party_achievements.get(party_id, [])
            session = self.active_party_sessions.get(party_id, {})

            # Check viewing permissions
            is_member = viewer_id in members if viewer_id else False

            # Prepare party data
            party_info = {
                "id": party["id"],
                "name": party["name"],
                "description": party["description"],
                "type": party["type"],
                "status": party["status"],
                "leader_id": party["leader_id"],
                "created_date": party["created_date"],
                "member_count": len(members),
                "statistics": party["statistics"],
                "settings": party["settings"]
            }

            # Add member info (limited for non-members)
            if is_member:
                party_info["members"] = {
                    player_id: {
                        "name": member.name,
                        "role": member.role.value,
                        "level": member.level,
                        "class_type": member.class_type,
                        "health_percentage": member.health_percentage,
                        "mana_percentage": member.mana_percentage,
                        "ready_status": member.ready_status,
                        "is_online": member.is_online,
                        "afk_status": member.afk_status,
                        "custom_status": member.custom_status,
                        "joined_date": member.joined_date.isoformat(),
                        "contribution_score": member.contribution_score
                    }
                    for player_id, member in members.items()
                }

                party_info.update({
                    "quests": [asdict(quest) for quest in quests if quest.status == "active"],
                    "completed_quests": [asdict(quest) for quest in quests if quest.status == "completed"],
                    "buffs": [asdict(buff) for buff in buffs],
                    "achievements": [asdict(achievement) for achievement in achievements],
                    "session": {
                        "ready_check_active": session.get("ready_check_active", False),
                        "voice_chat_enabled": session.get("voice_chat_enabled", False),
                        "combat_state": session.get("combat_state", False),
                        "last_activity": session.get("last_activity").isoformat() if session.get("last_activity") else None
                    },
                    "activity_log": party["activity_log"][-20:]  # Last 20 activities
                })

                # Add viewer's specific info
                if viewer_id and viewer_id in members:
                    viewer_member = members[viewer_id]
                    party_info["viewer_info"] = {
                        "role": viewer_member.role.value,
                        "can_invite": await self._can_invite(viewer_member, party),
                        "can_kick": await self._can_kick_member(viewer_id, party_id),
                        "can_promote": await self._can_promote_member(viewer_id, party_id),
                        "can_ready_check": await self._can_start_ready_check(viewer_id, party_id)
                    }

            return {
                "success": True,
                "party": party_info,
                "is_member": is_member
            }

        except Exception as e:
            self.logger.error(f"Error getting party info: {e}")
            return {"success": False, "error": str(e)}

    async def get_player_party(self, player_id: str) -> Optional[Dict]:
        """Get the party a player is currently in"""
        for party_id, members in self.party_members.items():
            if player_id in members:
                return await self.get_party_info(party_id, player_id)
        return None

    # Helper methods

    async def _validate_party_creation(self, leader_id: str, party_data: Dict) -> Dict:
        """Validate party creation requirements"""
        try:
            # Check if leader is already in a party
            existing_party = await self._get_player_party(leader_id)
            if existing_party:
                return {"valid": False, "error": "Already in a party"}

            # Get leader info
            leader_info = await self._get_player_info(leader_id)
            if not leader_info:
                return {"valid": False, "error": "Leader not found"}

            # Validate party type
            party_type = party_data.get("type", PartyType.ADVENTURE.value)
            if party_type not in [t.value for t in PartyType]:
                return {"valid": False, "error": "Invalid party type"}

            # Validate loot method
            loot_method = party_data.get("loot_method", self.config["default_loot_method"])
            if loot_method not in [m.value for m in LootDistribution]:
                return {"valid": False, "error": "Invalid loot method"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating party creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _get_player_info(self, player_id: str) -> Optional[Dict]:
        """Get player information from database"""
        # This would integrate with your player database
        # For now, return mock data
        return {
            "id": player_id,
            "name": f"Player_{player_id[:8]}",
            "level": 15,
            "class": random.choice(["Warrior", "Mage", "Rogue", "Cleric", "Ranger"]),
            "guild_id": None
        }

    async def _get_player_party(self, player_id: str) -> Optional[str]:
        """Get the party ID a player is currently in"""
        for party_id, members in self.party_members.items():
            if player_id in members:
                return party_id
        return None

    async def _can_invite(self, member: PartyMember, party: Dict) -> bool:
        """Check if member can invite others to party"""
        return (member.role in [PartyRole.LEADER, PartyRole.OFFICER] or
                party["settings"]["allow_invites"])

    async def _can_kick_member(self, kicker_id: str, party_id: str) -> bool:
        """Check if player can kick members from party"""
        if party_id not in self.party_members:
            return False

        kicker = self.party_members[party_id].get(kicker_id)
        return kicker and kicker.role in [PartyRole.LEADER, PartyRole.OFFICER]

    async def _can_promote_member(self, promoter_id: str, party_id: str) -> bool:
        """Check if player can promote members"""
        if party_id not in self.party_members:
            return False

        promoter = self.party_members[party_id].get(promoter_id)
        return promoter and promoter.role == PartyRole.LEADER

    async def _can_start_ready_check(self, initiator_id: str, party_id: str) -> bool:
        """Check if player can start ready check"""
        if party_id not in self.party_members:
            return False

        initiator = self.party_members[party_id].get(initiator_id)
        return initiator is not None  # Any member can start ready check

    def _can_promote_to_role(self, leader_role: PartyRole, target_role: PartyRole, new_role: PartyRole) -> bool:
        """Check if leader can promote target to new role"""
        # Only leaders can promote, and only to certain roles
        if leader_role != PartyRole.LEADER:
            return False

        # Cannot promote to leader (that's handled separately)
        if new_role == PartyRole.LEADER:
            return False

        # Cannot promote someone equal or higher rank
        role_hierarchy = {
            PartyRole.LEADER: 5,
            PartyRole.OFFICER: 4,
            PartyRole.TANK: 3,
            PartyRole.HEALER: 3,
            PartyRole.DPS: 2,
            PartyRole.SUPPORT: 2,
            PartyRole.MEMBER: 1,
            PartyRole.GUEST: 0
        }

        target_level = role_hierarchy.get(target_role, 0)
        new_level = role_hierarchy.get(new_role, 0)

        return new_level > target_level

    async def _meets_level_requirements(self, player_info: Dict, party: Dict) -> bool:
        """Check if player meets party level requirements"""
        player_level = player_info.get("level", 1)
        min_level = party["settings"]["min_level"]
        max_level = party["settings"]["max_level"]
        level_range = party["settings"]["level_range"]

        # Check minimum level
        if player_level < min_level:
            return False

        # Check maximum level (if set)
        if max_level and player_level > max_level:
            return False

        # Check level range (if leader level is known)
        leader_info = await self._get_player_info(party["leader_id"])
        if leader_info and level_range:
            level_diff = abs(player_level - leader_info["level"])
            if level_diff > level_range:
                return False

        return True

    async def _handle_leader_leaving(self, leader_id: str, party_id: str, reason: str) -> Dict:
        """Handle the case when party leader leaves"""
        party = self.parties[party_id]
        members = self.party_members[party_id]

        # Find eligible successor
        eligible_members = [
            (pid, member) for pid, member in members.items()
            if pid != leader_id and member.role != PartyRole.GUEST
        ]

        if not eligible_members:
            # No eligible successors, disband party
            await self._disband_party(party_id, "leader_left_no_successor")
            return {
                "success": True,
                "party_disbanded": True,
                "message": "Party disbanded as leader left and no successor available"
            }

        # Promote the member with highest role or seniority
        successor_id, successor = max(
            eligible_members,
            key=lambda x: (
                # Prefer higher roles
                [PartyRole.OFFICER, PartyRole.TANK, PartyRole.HEALER, PartyRole.DPS, PartyRole.SUPPORT, PartyRole.MEMBER].index(x[1].role),
                # Then by join date (earlier = more senior)
                x[1].joined_date
            )
        )

        # Transfer leadership
        return await self._transfer_leadership(leader_id, party_id, successor_id, reason)

    async def _transfer_leadership(self, current_leader_id: str, party_id: str, new_leader_id: str, reason: str = "") -> Dict:
        """Transfer party leadership to another member"""
        party = self.parties[party_id]
        current_leader = self.party_members[party_id][current_leader_id]
        new_leader = self.party_members[party_id][new_leader_id]

        # Transfer leadership
        current_leader.role = PartyRole.MEMBER
        new_leader.role = PartyRole.LEADER
        party["leader_id"] = new_leader_id

        # Add activity log entry
        await self._add_party_activity(
            party_id,
            "leadership_transferred",
            f"Leadership transferred from {current_leader.name} to {new_leader.name}" + (f": {reason}" if reason else ""),
            {"old_leader": current_leader_id, "new_leader": new_leader_id, "reason": reason}
        )

        # Send notifications
        await self._send_party_notification(
            party_id,
            "leadership_transferred",
            f"Leadership transferred to {new_leader.name}!"
        )

        self.logger.info(f"Leadership of party {party_id} transferred from {current_leader_id} to {new_leader_id}")

        return {
            "success": True,
            "old_leader": current_leader_id,
            "new_leader": new_leader_id,
            "message": f"Leadership transferred to {new_leader.name}"
        }

    async def _disband_party(self, party_id: str, reason: str):
        """Disband a party"""
        if party_id not in self.parties:
            return

        party = self.parties[party_id]
        members = list(self.party_members[party_id].keys())

        # Add final activity log entry
        await self._add_party_activity(
            party_id,
            "party_disbanded",
            f"Party disbanded: {reason}",
            {"reason": reason, "member_count": len(members)}
        )

        # Send notification to all members
        await self._send_party_notification(
            party_id,
            "party_disbanded",
            f"Party {party['name']} has been disbanded: {reason}"
        )

        # Clean up all party data
        del self.parties[party_id]
        del self.party_members[party_id]
        del self.party_quests[party_id]
        del self.party_buffs[party_id]
        del self.party_achievements[party_id]
        del self.party_invitations[party_id]

        if party_id in self.active_party_sessions:
            del self.active_party_sessions[party_id]

        self.logger.info(f"Party {party_id} disbanded: {reason}")

    async def _calculate_party_synergies(self, party_id: str):
        """Calculate party synergies (wrapper)"""
        await self.calculate_party_synergies(party_id)

    async def _complete_ready_check(self, party_id: str):
        """Complete a ready check"""
        if party_id not in self.active_party_sessions:
            return

        session = self.active_party_sessions[party_id]
        members = self.party_members[party_id]

        # Count ready responses
        ready_count = sum(1 for response in session["ready_check_responses"].values() if response["ready"])
        total_count = len(members)

        # Determine result
        all_ready = ready_count == total_count
        not_ready_members = [
            response["name"] for response in session["ready_check_responses"].values()
            if not response["ready"]
        ]

        # Reset ready check
        session["ready_check_active"] = False
        session["ready_check_responses"] = {}

        # Reset member ready status
        for member in members.values():
            member.ready_status = False

        # Send result notification
        if all_ready:
            await self._send_party_notification(
                party_id,
                "ready_check_complete",
                "Everyone is ready! The party can proceed."
            )
        else:
            await self._send_party_notification(
                party_id,
                "ready_check_complete",
                f"Ready check complete. Not ready: {', '.join(not_ready_members)}"
            )

        # Add activity log entry
        await self._add_party_activity(
            party_id,
            "ready_check_complete",
            f"Ready check complete: {ready_count}/{total_count} ready",
            {"ready_count": ready_count, "total_count": total_count, "all_ready": all_ready}
        )

    async def _ready_check_timeout(self, party_id: str):
        """Handle ready check timeout"""
        try:
            await asyncio.sleep(self.config["ready_check_timeout"])

            if party_id in self.active_party_sessions:
                session = self.active_party_sessions[party_id]
                if session["ready_check_active"]:
                    await self._complete_ready_check(party_id)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in ready check timeout: {e}")

    async def _expire_invitation(self, invitation_id: str, party_id: str):
        """Expire a party invitation"""
        try:
            await asyncio.sleep(self.config["invitation_timeout"])

            if party_id in self.party_invitations:
                for invitation in self.party_invitations[party_id]:
                    if invitation["id"] == invitation_id and invitation["status"] == "pending":
                        invitation["status"] = "expired"
                        break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error expiring invitation: {e}")

    async def _distribute_single_item(self, party_id: str, item: Dict, members: List[PartyMember], method: LootDistribution) -> Dict:
        """Distribute a single item to party members"""
        if method == LootDistribution.FREE_FOR_ALL:
            # Random distribution
            winner = random.choice(members)
            return {
                "item_id": item["id"],
                "winner_id": winner.player_id,
                "winner_name": winner.name,
                "method": method.value,
                "reason": "Random roll"
            }

        elif method == LootDistribution.ROUND_ROBIN:
            # Simple round robin (would need to track history)
            winner = members[len(self.loot_distribution_cache.get(party_id, {}).get("round_robin_count", 0)) % len(members)]

            # Update cache
            if party_id not in self.loot_distribution_cache:
                self.loot_distribution_cache[party_id] = {}
            self.loot_distribution_cache[party_id]["round_robin_count"] = self.loot_distribution_cache[party_id].get("round_robin_count", 0) + 1

            return {
                "item_id": item["id"],
                "winner_id": winner.player_id,
                "winner_name": winner.name,
                "method": method.value,
                "reason": "Round robin distribution"
            }

        elif method == LootDistribution.NEED_BEFORE_GREED:
            # Need/greed system (simplified)
            # For now, random distribution with preference based on class suitability
            suitable_members = []
            for member in members:
                # Simple class suitability check
                if self._is_item_suitable_for_class(item, member.class_type):
                    suitable_members.append(member)

            if suitable_members:
                winner = random.choice(suitable_members)
                reason = "Need roll (class suitable)"
            else:
                winner = random.choice(members)
                reason = "Greed roll (no class preference)"

            return {
                "item_id": item["id"],
                "winner_id": winner.player_id,
                "winner_name": winner.name,
                "method": method.value,
                "reason": reason
            }

        elif method == LootDistribution.MASTER_LOOTER:
            # Leader gets to decide (for now, assign to leader)
            leader = next((m for m in members if m.role == PartyRole.LEADER), members[0])
            return {
                "item_id": item["id"],
                "winner_id": leader.player_id,
                "winner_name": leader.name,
                "method": method.value,
                "reason": "Master looter assignment"
            }

        elif method == LootDistribution.PERSONAL_LOOT:
            # Everyone gets their own copy (not implemented here)
            return {
                "item_id": item["id"],
                "method": method.value,
                "reason": "Personal loot - everyone receives copy",
                "recipients": [{"player_id": m.player_id, "name": m.name} for m in members]
            }

        else:  # GROUP_LOOT
            # Give to highest contributor or random
            winner = max(members, key=lambda m: m.contribution_score)
            return {
                "item_id": item["id"],
                "winner_id": winner.player_id,
                "winner_name": winner.name,
                "method": method.value,
                "reason": "Highest contribution"
            }

    def _is_item_suitable_for_class(self, item: Dict, class_type: str) -> bool:
        """Check if item is suitable for a class"""
        # Simple implementation - would be more sophisticated
        item_type = item.get("type", "").lower()
        class_type = class_type.lower()

        # Basic class-item associations
        if class_type in ["warrior", "paladin"] and item_type in ["sword", "axe", "armor", "shield"]:
            return True
        elif class_type in ["mage", "wizard"] and item_type in ["staff", "robe", "wand"]:
            return True
        elif class_type in ["rogue", "assassin"] and item_type in ["dagger", "leather", "bow"]:
            return True
        elif class_type in ["cleric", "priest"] and item_type in ["mace", "hammer", "holy_symbol"]:
            return True

        return False

    async def _is_in_quest_range(self, player_id: str, party_id: str) -> bool:
        """Check if player is in range for shared quest progress"""
        # This would check actual game world positions
        # For now, assume they're in range
        return True

    async def _distribute_quest_rewards(self, party_id: str, quest: PartyQuest):
        """Distribute quest rewards to party members"""
        if not quest.shared_rewards:
            return

        # This would integrate with your reward system
        # For now, just log the distribution
        self.logger.info(f"Distributed quest rewards for '{quest.title}' to party {party_id}")

    async def _add_party_activity(self, party_id: str, activity_type: str, description: str, data: Dict = None):
        """Add an activity log entry"""
        if party_id not in self.parties:
            return

        activity = {
            "type": activity_type,
            "description": description,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }

        self.parties[party_id]["activity_log"].append(activity)

        # Keep only last 100 activities
        if len(self.parties[party_id]["activity_log"]) > 100:
            self.parties[party_id]["activity_log"] = self.parties[party_id]["activity_log"][-100:]

    async def _send_party_notification(self, party_id: str, notification_type: str, message: str, data: Dict = None):
        """Send notification to all party members"""
        # This would integrate with your notification system
        # For now, just log the notification
        self.logger.info(f"Party {party_id} notification [{notification_type}]: {message}")

        # Store notification for party members to retrieve
        notification = {
            "type": notification_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "party_id": party_id
        }

        # This would be stored in your notification database
        # and pushed to connected party members

    async def _send_private_notification(self, player_id: str, notification_type: str, message: str, data: Dict = None):
        """Send private notification to a player"""
        # This would integrate with your notification system
        self.logger.info(f"Private notification to {player_id} [{notification_type}]: {message}")

    async def _send_party_invitation(self, player_id: str, invitation: Dict):
        """Send party invitation to a player"""
        # This would integrate with your notification/messaging system
        self.logger.info(f"Party invitation sent to {player_id}: {invitation['party_name']}")

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Party cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._party_cleanup_task())
        )

        # Activity timeout task
        self._background_tasks.append(
            asyncio.create_task(self._activity_timeout_task())
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

    async def _party_cleanup_task(self):
        """Periodically clean up inactive parties"""
        while self._running:
            try:
                current_time = datetime.now()

                for party_id, party in list(self.parties.items()):
                    if party_id in self.active_party_sessions:
                        session = self.active_party_sessions[party_id]
                        last_activity = session.get("last_activity", current_time)

                        # Check if party has been inactive too long
                        if (current_time - last_activity).total_seconds() > self.config["party_disband_timeout"]:
                            if len(self.party_members.get(party_id, {})) == 0:
                                await self._disband_party(party_id, "inactivity_timeout")

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in party cleanup task: {e}")
                await asyncio.sleep(60)

    async def _activity_timeout_task(self):
        """Update party activity and handle timeouts"""
        while self._running:
            try:
                current_time = datetime.now()

                for party_id, session in self.active_party_sessions.items():
                    # Update last activity if members are active
                    if party_id in self.party_members:
                        for member in self.party_members[party_id].values():
                            if member.is_online and not member.afk_status:
                                session["last_activity"] = current_time
                                break

                await asyncio.sleep(300)  # Check every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in activity timeout task: {e}")
                await asyncio.sleep(300)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize party system
        party_system = PartySystem()

        # Start background tasks
        await party_system.start_background_tasks()

        # Example usage
        print("Creating party...")
        result = await party_system.create_party("player123", {
            "name": "Dragon Slayers",
            "description": "We hunt dragons together",
            "type": "adventure",
            "loot_method": "need_before_greed"
        })
        print(result)

        if result["success"]:
            party_id = result["party_id"]

            # Add some members
            await party_system.invite_to_party("player123", party_id, "player456")
            await party_system.invite_to_party("player123", party_id, "player789")

            # Start ready check
            await party_system.start_ready_check("player123", party_id)

            # Add party quest
            await party_system.add_party_quest(party_id, {
                "title": "Defeat the Dragon Lord",
                "description": "Work together to defeat the ancient dragon lord",
                "objectives": [
                    {"id": "dragon_defeated", "description": "Defeat the Dragon Lord", "required": 1}
                ],
                "difficulty": "hard",
                "required_level": 15
            })

            # Calculate synergies
            synergies = await party_system.calculate_party_synergies(party_id)
            print(f"Party synergies: {len(synergies['synergies'])} active")

            # Get party info
            info = await party_system.get_party_info(party_id)
            print(f"Party '{info['party']['name']}' has {info['party']['member_count']} members")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await party_system.stop_background_tasks()

    asyncio.run(main())