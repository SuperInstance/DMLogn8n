#!/usr/bin/env python3
"""
DMLogn8n Collaboration Tools - Shared Objectives and Group Activities System

Handles shared quests, collaborative dungeons, group achievements, cooperative crafting,
resource sharing, coordinated events, and team-based objectives.

Features:
- Shared quest and objective management
- Collaborative dungeon and raid systems
- Group achievement tracking
- Cooperative crafting and resource pooling
- Team-based objectives and goals
- Shared resource management
- Collaborative building and construction
- Coordinated event participation
- Team progress tracking
- Shared reward distribution
- Cross-team collaboration tools
"""

import asyncio
import json
import logging
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import random
from collections import defaultdict, deque

class CollaborationType(Enum):
    """Types of collaborative activities"""
    SHARED_QUEST = "shared_quest"
    DUNGEON_RUN = "dungeon_run"
    RAID = "raid"
    WORLD_BOSS = "world_boss"
    COLLABORATIVE_CRAFTING = "collaborative_crafting"
    RESOURCE_GATHERING = "resource_gathering"
    BUILDING_PROJECT = "building_project"
    COMMUNITY_EVENT = "community_event"
    RESEARCH_PROJECT = "research_project"
    EXPLORATION_EXPEDITION = "exploration_expedition"
    TRADE_CARAVAN = "trade_caravan"
    DEFENSE_OPERATION = "defense_operation"
    COMPETITION = "competition"

class ObjectiveType(Enum):
    """Types of objectives within collaborations"""
    COLLECT = "collect"
    KILL = "kill"
    EXPLORE = "explore"
    CRAFT = "craft"
    DELIVER = "deliver"
    DEFEND = "defend"
    ESCORT = "escort"
    SOLVE = "solve"
    DISCOVER = "discover"
    BUILD = "build"
    TEACH = "teach"
    COORDINATE = "coordinate"

class ContributionType(Enum):
    """Types of contributions to collaborations"""
    TIME = "time"
    RESOURCES = "resources"
    SKILL = "skill"
    LEADERSHIP = "leadership"
    COMBAT = "combat"
    CRAFTING = "crafting"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    STRATEGY = "strategy"
    SUPPORT = "support"
    INNOVATION = "innovation"

class RewardDistribution(Enum):
    """Reward distribution methods"""
    EQUAL = "equal"
    CONTRIBUTION_BASED = "contribution_based"
    ROLE_BASED = "role_based"
    RANDOM = "random"
    LEADER_CHOICE = "leader_choice"
    VOTE = "vote"
    NEED_BASED = "need_based"
    PERFORMANCE_BASED = "performance_based"

class CollaborationStatus(Enum):
    """Status of collaborative activities"""
    PLANNING = "planning"
    RECRUITING = "recruiting"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"

@dataclass
class CollaborationObjective:
    """Objective within a collaboration"""
    id: str
    title: str
    description: str
    objective_type: ObjectiveType
    required_amount: int
    current_progress: int = 0
    assigned_to: List[str] = field(default_factory=list)
    difficulty: str = "normal"  # easy, normal, hard, expert, legendary
    priority: int = 1  # 1-5
    dependencies: List[str] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False
    completed_by: List[str] = field(default_factory=list)
    completion_date: Optional[datetime] = None

@dataclass
class CollaborationContribution:
    """Contribution by a participant"""
    id: str
    participant_id: str
    contribution_type: ContributionType
    amount: float
    description: str
    timestamp: datetime
    objective_id: Optional[str] = None
    quality: float = 1.0  # 0.0 to 1.0
    impact: float = 1.0  # Multiplier for contribution value
    verified: bool = False
    verified_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Collaboration:
    """Main collaboration activity"""
    id: str
    title: str
    description: str
    collaboration_type: CollaborationType
    creator_id: str
    leader_id: str
    participants: Dict[str, Dict] = field(default_factory=dict)  # participant_id -> role, join_date, etc.
    objectives: List[CollaborationObjective] = field(default_factory=list)
    contributions: List[CollaborationContribution] = field(default_factory=list)
    status: CollaborationStatus = CollaborationStatus.PLANNING
    created_date: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)  # Shared resources pool
    rewards: Dict[str, Any] = field(default_factory=dict)
    reward_distribution: RewardDistribution = RewardDistribution.EQUAL
    tags: List[str] = field(default_factory=list)
    progress_percentage: float = 0.0

@dataclass
class ResourcePool:
    """Shared resource pool for collaboration"""
    id: str
    collaboration_id: str
    resource_type: str
    current_amount: int = 0
    target_amount: int = 0
    contributions: Dict[str, int] = field(default_factory=dict)  # participant_id -> amount
    withdrawals: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TeamRole:
    """Role within a collaboration team"""
    id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    benefits: Dict[str, Any] = field(default_factory=dict)
    max_assignments: int = -1  # -1 for unlimited

@dataclass
class CollaborationTemplate:
    """Template for creating collaborations"""
    id: str
    name: str
    collaboration_type: CollaborationType
    description: str
    default_objectives: List[Dict] = field(default_factory=list)
    default_roles: List[Dict] = field(default_factory=list)
    required_participants: int = 2
    max_participants: int = 10
    estimated_duration: int = 60  # minutes
    difficulty: str = "normal"
    required_resources: Dict[str, int] = field(default_factory=dict)
    common_rewards: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

class CollaborationTools:
    """Main collaboration management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.collaborations: Dict[str, Collaboration] = {}
        self.templates: Dict[str, CollaborationTemplate] = {}
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.team_roles: Dict[str, TeamRole] = {}

        # Participant tracking
        self.active_collaborations: Dict[str, Set[str]] = defaultdict(set)  # user_id -> collaboration_ids
        self.collaboration_history: Dict[str, List[str]] = defaultdict(list)  # user_id -> collaboration_ids

        # Analytics and metrics
        self.collaboration_stats: Dict[str, Dict] = {}
        self.participant_stats: Dict[str, Dict] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_collaborations_per_user": 10,
            "max_participants_per_collaboration": 40,
            "max_objectives_per_collaboration": 50,
            "contribution_validation_required": False,
            "auto_complete_objectives": True,
            "progress_update_interval": 60,  # seconds
            "reminder_interval": 3600,  # 1 hour
            "cleanup_completed_days": 30,
            "max_resource_pools_per_collaboration": 20,
            "default_reward_distribution": RewardDistribution.EQUAL.value,
            "contribution_weight_decay": 0.1,  # Daily decay
            "min_participant_rating": 0.0,
            "collaboration_timeout_hours": 168,  # 1 week
            "auto_save_interval": 300,  # 5 minutes
            "team_role_validation": True
        }

    async def create_collaboration(self, creator_id: str, collaboration_data: Dict) -> Dict:
        """Create a new collaboration"""
        try:
            # Validate collaboration creation
            validation_result = await self._validate_collaboration_creation(creator_id, collaboration_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Generate collaboration ID
            collaboration_id = str(uuid.uuid4())

            # Create collaboration
            collaboration = Collaboration(
                id=collaboration_id,
                title=collaboration_data["title"],
                description=collaboration_data.get("description", ""),
                collaboration_type=CollaborationType(collaboration_data["type"]),
                creator_id=creator_id,
                leader_id=creator_id,
                status=CollaborationStatus.PLANNING,
                deadline=datetime.fromisoformat(collaboration_data["deadline"]) if collaboration_data.get("deadline") else None,
                settings=collaboration_data.get("settings", {}),
                rewards=collaboration_data.get("rewards", {}),
                reward_distribution=RewardDistribution(collaboration_data.get("reward_distribution", self.config["default_reward_distribution"])),
                tags=collaboration_data.get("tags", [])
            )

            # Add creator as leader
            collaboration.participants[creator_id] = {
                "role": "leader",
                "join_date": datetime.now(),
                "status": "active",
                "contribution_score": 0.0,
                "permissions": ["lead", "invite", "manage", "complete"]
            }

            # Add objectives if provided
            for obj_data in collaboration_data.get("objectives", []):
                objective = CollaborationObjective(
                    id=str(uuid.uuid4()),
                    title=obj_data["title"],
                    description=obj_data.get("description", ""),
                    objective_type=ObjectiveType(obj_data["type"]),
                    required_amount=obj_data["required_amount"],
                    difficulty=obj_data.get("difficulty", "normal"),
                    priority=obj_data.get("priority", 1),
                    rewards=obj_data.get("rewards", {})
                )
                collaboration.objectives.append(objective)

            # Create resource pools if provided
            for resource_data in collaboration_data.get("resources", {}):
                pool = ResourcePool(
                    id=str(uuid.uuid4()),
                    collaboration_id=collaboration_id,
                    resource_type=resource_data["type"],
                    target_amount=resource_data.get("target_amount", 0)
                )
                self.resource_pools[pool.id] = pool

            # Store collaboration
            self.collaborations[collaboration_id] = collaboration
            self.active_collaborations[creator_id].add(collaboration_id)

            # Initialize stats
            self.collaboration_stats[collaboration_id] = {
                "created_date": datetime.now(),
                "total_contributions": 0,
                "total_participants": 1,
                "objectives_completed": 0,
                "resources_used": 0,
                "last_activity": datetime.now()
            }

            self.logger.info(f"Collaboration '{collaboration.title}' created by {creator_id}")

            return {
                "success": True,
                "collaboration_id": collaboration_id,
                "collaboration": asdict(collaboration),
                "message": f"Collaboration '{collaboration.title}' created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating collaboration: {e}")
            return {"success": False, "error": str(e)}

    async def join_collaboration(self, user_id: str, collaboration_id: str, role: str = "participant") -> Dict:
        """Join a collaboration"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            # Check if collaboration is accepting participants
            if collaboration.status not in [CollaborationStatus.PLANNING, CollaborationStatus.RECRUITING]:
                return {"success": False, "error": "Collaboration is not accepting participants"}

            # Check if user is already a participant
            if user_id in collaboration.participants:
                return {"success": False, "error": "Already a participant"}

            # Check participant limit
            max_participants = collaboration.settings.get("max_participants", self.config["max_participants_per_collaboration"])
            if len(collaboration.participants) >= max_participants:
                return {"success": False, "error": "Collaboration is full"}

            # Check if user meets requirements
            if not await self._meets_collaboration_requirements(user_id, collaboration):
                return {"success": False, "error": "Does not meet collaboration requirements"}

            # Add participant
            collaboration.participants[user_id] = {
                "role": role,
                "join_date": datetime.now(),
                "status": "active",
                "contribution_score": 0.0,
                "permissions": await self._get_default_permissions(role)
            }

            self.active_collaborations[user_id].add(collaboration_id)

            # Update stats
            self.collaboration_stats[collaboration_id]["total_participants"] += 1
            self.collaboration_stats[collaboration_id]["last_activity"] = datetime.now()

            # Update collaboration status if recruiting
            if collaboration.status == CollaborationStatus.RECRUITING:
                if len(collaboration.participants) >= collaboration.settings.get("min_participants", 2):
                    collaboration.status = CollaborationStatus.ACTIVE
                    collaboration.start_date = datetime.now()

            self.logger.info(f"User {user_id} joined collaboration {collaboration_id}")

            return {
                "success": True,
                "collaboration_id": collaboration_id,
                "role": role,
                "message": f"Joined '{collaboration.title}' successfully"
            }

        except Exception as e:
            self.logger.error(f"Error joining collaboration: {e}")
            return {"success": False, "error": str(e)}

    async def leave_collaboration(self, user_id: str, collaboration_id: str, reason: str = "") -> Dict:
        """Leave a collaboration"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            if user_id not in collaboration.participants:
                return {"success": False, "error": "Not a participant"}

            # Check if user is the leader
            if user_id == collaboration.leader_id:
                return await self._transfer_leadership_and_leave(user_id, collaboration_id, reason)

            # Remove participant
            del collaboration.participants[user_id]
            self.active_collaborations[user_id].discard(collaboration_id)
            self.collaboration_history[user_id].append(collaboration_id)

            # Update stats
            self.collaboration_stats[collaboration_id]["total_participants"] -= 1
            self.collaboration_stats[collaboration_id]["last_activity"] = datetime.now()

            # Check if collaboration should be cancelled
            if len(collaboration.participants) < collaboration.settings.get("min_participants", 2):
                if collaboration.status in [CollaborationStatus.ACTIVE, CollaborationStatus.RECRUITING]:
                    collaboration.status = CollaborationStatus.CANCELLED
                    collaboration.end_date = datetime.now()

            self.logger.info(f"User {user_id} left collaboration {collaboration_id}")

            return {
                "success": True,
                "message": f"Left '{collaboration.title}'"
            }

        except Exception as e:
            self.logger.error(f"Error leaving collaboration: {e}")
            return {"success": False, "error": str(e)}

    async def add_contribution(self, user_id: str, collaboration_id: str, contribution_type: ContributionType,
                              amount: float, description: str, objective_id: str = None, metadata: Dict = None) -> Dict:
        """Add a contribution to a collaboration"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            if user_id not in collaboration.participants:
                return {"success": False, "error": "Not a participant"}

            if collaboration.status != CollaborationStatus.ACTIVE:
                return {"success": False, "error": "Collaboration is not active"}

            # Validate contribution
            validation_result = await self._validate_contribution(user_id, collaboration_id, contribution_type, amount)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Create contribution
            contribution = CollaborationContribution(
                id=str(uuid.uuid4()),
                participant_id=user_id,
                contribution_type=contribution_type,
                amount=amount,
                description=description,
                timestamp=datetime.now(),
                objective_id=objective_id,
                metadata=metadata or {}
            )

            # Add to collaboration
            collaboration.contributions.append(contribution)

            # Update participant score
            collaboration.participants[user_id]["contribution_score"] += amount * contribution.impact

            # Update objective progress if specified
            if objective_id:
                await self._update_objective_progress(collaboration_id, objective_id, amount)

            # Update resource pool if applicable
            if contribution_type == ContributionType.RESOURCES:
                await self._update_resource_pool(collaboration_id, contribution)

            # Update stats
            self.collaboration_stats[collaboration_id]["total_contributions"] += 1
            self.collaboration_stats[collaboration_id]["last_activity"] = datetime.now()

            # Update participant stats
            if user_id not in self.participant_stats:
                self.participant_stats[user_id] = {
                    "total_contributions": 0,
                    "total_amount": 0.0,
                    "collaborations_completed": 0,
                    "average_rating": 0.0
                }
            self.participant_stats[user_id]["total_contributions"] += 1
            self.participant_stats[user_id]["total_amount"] += amount

            # Update overall progress
            await self._update_collaboration_progress(collaboration_id)

            # Check for objectives completion
            await self._check_objectives_completion(collaboration_id)

            # Check for collaboration completion
            await self._check_collaboration_completion(collaboration_id)

            self.logger.info(f"Contribution added to {collaboration_id} by {user_id}: {amount} {contribution_type.value}")

            return {
                "success": True,
                "contribution_id": contribution.id,
                "progress_percentage": collaboration.progress_percentage,
                "message": f"Contribution added successfully"
            }

        except Exception as e:
            self.logger.error(f"Error adding contribution: {e}")
            return {"success": False, "error": str(e)}

    async def update_objective(self, user_id: str, collaboration_id: str, objective_id: str,
                             progress_update: int) -> Dict:
        """Update progress on a collaboration objective"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            # Find objective
            objective = None
            for obj in collaboration.objectives:
                if obj.id == objective_id:
                    objective = obj
                    break

            if not objective:
                return {"success": False, "error": "Objective not found"}

            if user_id not in collaboration.participants:
                return {"success": False, "error": "Not a participant"}

            # Check permissions
            if not await self._can_update_objective(user_id, collaboration, objective):
                return {"success": False, "error": "No permission to update this objective"}

            # Update progress
            old_progress = objective.current_progress
            objective.current_progress = min(objective.current_progress + progress_update, objective.required_amount)

            # Add automatic contribution if progress increased
            if objective.current_progress > old_progress:
                contribution = CollaborationContribution(
                    id=str(uuid.uuid4()),
                    participant_id=user_id,
                    contribution_type=ContributionType.TIME,
                    amount=progress_update,
                    description=f"Updated objective: {objective.title}",
                    timestamp=datetime.now(),
                    objective_id=objective_id,
                    quality=1.0
                )
                collaboration.contributions.append(contribution)

            # Check if objective is completed
            if not objective.completed and objective.current_progress >= objective.required_amount:
                objective.completed = True
                objective.completed_by.append(user_id)
                objective.completion_date = datetime.now()

                # Distribute objective rewards
                await self._distribute_objective_rewards(collaboration_id, objective)

                # Update stats
                self.collaboration_stats[collaboration_id]["objectives_completed"] += 1

            # Update overall progress
            await self._update_collaboration_progress(collaboration_id)

            self.logger.info(f"Objective {objective_id} updated by {user_id}: {objective.current_progress}/{objective.required_amount}")

            return {
                "success": True,
                "objective_id": objective_id,
                "current_progress": objective.current_progress,
                "required_progress": objective.required_amount,
                "completed": objective.completed,
                "collaboration_progress": collaboration.progress_percentage
            }

        except Exception as e:
            self.logger.error(f"Error updating objective: {e}")
            return {"success": False, "error": str(e)}

    async def create_template(self, creator_id: str, template_data: Dict) -> Dict:
        """Create a collaboration template"""
        try:
            # Validate template creation
            validation_result = await self._validate_template_creation(creator_id, template_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Create template
            template = CollaborationTemplate(
                id=str(uuid.uuid4()),
                name=template_data["name"],
                collaboration_type=CollaborationType(template_data["type"]),
                description=template_data.get("description", ""),
                default_objectives=template_data.get("objectives", []),
                default_roles=template_data.get("roles", []),
                required_participants=template_data.get("required_participants", 2),
                max_participants=template_data.get("max_participants", 10),
                estimated_duration=template_data.get("estimated_duration", 60),
                difficulty=template_data.get("difficulty", "normal"),
                required_resources=template_data.get("required_resources", {}),
                common_rewards=template_data.get("common_rewards", {}),
                tags=template_data.get("tags", [])
            )

            # Store template
            self.templates[template.id] = template

            self.logger.info(f"Template '{template.name}' created by {creator_id}")

            return {
                "success": True,
                "template_id": template.id,
                "template": asdict(template),
                "message": f"Template '{template.name}' created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating template: {e}")
            return {"success": False, "error": str(e)}

    async def create_from_template(self, creator_id: str, template_id: str, customization: Dict = None) -> Dict:
        """Create a collaboration from a template"""
        try:
            if template_id not in self.templates:
                return {"success": False, "error": "Template not found"}

            template = self.templates[template_id]
            customization = customization or {}

            # Prepare collaboration data from template
            collaboration_data = {
                "title": customization.get("title", template.name),
                "description": customization.get("description", template.description),
                "type": template.collaboration_type.value,
                "objectives": template.default_objectives.copy(),
                "rewards": template.common_rewards.copy(),
                "settings": {
                    "max_participants": customization.get("max_participants", template.max_participants),
                    "min_participants": template.required_participants,
                    "estimated_duration": template.estimated_duration,
                    "difficulty": customization.get("difficulty", template.difficulty)
                },
                "tags": template.tags.copy(),
                "deadline": customization.get("deadline")
            }

            # Customize objectives if provided
            if "objectives" in customization:
                for i, custom_obj in enumerate(customization["objectives"]):
                    if i < len(collaboration_data["objectives"]):
                        collaboration_data["objectives"][i].update(custom_obj)

            # Create collaboration
            result = await self.create_collaboration(creator_id, collaboration_data)

            if result["success"]:
                # Set up roles from template
                collaboration_id = result["collaboration_id"]
                collaboration = self.collaborations[collaboration_id]

                for role_data in template.default_roles:
                    await self._create_team_role(collaboration_id, role_data)

            return result

        except Exception as e:
            self.logger.error(f"Error creating collaboration from template: {e}")
            return {"success": False, "error": str(e)}

    async def get_collaboration_info(self, collaboration_id: str, user_id: str = None) -> Dict:
        """Get detailed information about a collaboration"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            # Check access permissions
            if user_id and user_id not in collaboration.participants:
                if collaboration.status not in [CollaborationStatus.RECRUITING, CollaborationStatus.COMPLETED]:
                    return {"success": False, "error": "No permission to view this collaboration"}

            # Prepare collaboration data
            collab_data = {
                "id": collaboration.id,
                "title": collaboration.title,
                "description": collaboration.description,
                "type": collaboration.collaboration_type.value,
                "status": collaboration.status.value,
                "creator_id": collaboration.creator_id,
                "leader_id": collaboration.leader_id,
                "created_date": collaboration.created_date.isoformat(),
                "start_date": collaboration.start_date.isoformat() if collaboration.start_date else None,
                "end_date": collaboration.end_date.isoformat() if collaboration.end_date else None,
                "deadline": collaboration.deadline.isoformat() if collaboration.deadline else None,
                "progress_percentage": collaboration.progress_percentage,
                "tags": collaboration.tags,
                "participant_count": len(collaboration.participants),
                "objective_count": len(collaboration.objectives),
                "completed_objectives": len([obj for obj in collaboration.objectives if obj.completed])
            }

            # Add detailed information for participants
            if user_id and user_id in collaboration.participants:
                collab_data.update({
                    "objectives": [asdict(obj) for obj in collaboration.objectives],
                    "participants": {
                        pid: {
                            "role": info["role"],
                            "join_date": info["join_date"].isoformat(),
                            "contribution_score": info["contribution_score"],
                            "status": info["status"]
                        }
                        for pid, info in collaboration.participants.items()
                    },
                    "recent_contributions": [
                        asdict(c) for c in collaboration.contributions[-10:]
                    ],
                    "resources": {
                        pool_id: {
                            "type": pool.resource_type,
                            "current_amount": pool.current_amount,
                            "target_amount": pool.target_amount,
                            "last_updated": pool.last_updated.isoformat()
                        }
                        for pool_id, pool in self.resource_pools.items()
                        if pool.collaboration_id == collaboration_id
                    },
                    "rewards": collaboration.rewards,
                    "reward_distribution": collaboration.reward_distribution.value,
                    "settings": collaboration.settings
                })

                # Add user-specific info
                collab_data["user_info"] = {
                    "role": collaboration.participants[user_id]["role"],
                    "permissions": collaboration.participants[user_id]["permissions"],
                    "contribution_score": collaboration.participants[user_id]["contribution_score"]
                }

            return {
                "success": True,
                "collaboration": collab_data
            }

        except Exception as e:
            self.logger.error(f"Error getting collaboration info: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_collaborations(self, user_id: str, status_filter: Optional[CollaborationStatus] = None) -> Dict:
        """Get collaborations for a user"""
        try:
            collaboration_ids = self.active_collaborations.get(user_id, set())
            collaborations = []

            for collab_id in collaboration_ids:
                if collab_id in self.collaborations:
                    collaboration = self.collaborations[collab_id]

                    # Apply status filter if provided
                    if status_filter and collaboration.status != status_filter:
                        continue

                    collab_info = {
                        "id": collaboration.id,
                        "title": collaboration.title,
                        "type": collaboration.collaboration_type.value,
                        "status": collaboration.status.value,
                        "role": collaboration.participants[user_id]["role"],
                        "progress_percentage": collaboration.progress_percentage,
                        "participant_count": len(collaboration.participants),
                        "deadline": collaboration.deadline.isoformat() if collaboration.deadline else None,
                        "created_date": collaboration.created_date.isoformat()
                    }
                    collaborations.append(collab_info)

            # Sort by last activity (most recent first)
            collaborations.sort(
                key=lambda x: self.collaboration_stats[x["id"]]["last_activity"],
                reverse=True
            )

            return {
                "success": True,
                "collaborations": collaborations,
                "total_count": len(collaborations)
            }

        except Exception as e:
            self.logger.error(f"Error getting user collaborations: {e}")
            return {"success": False, "error": str(e)}

    async def get_available_collaborations(self, user_id: str, collaboration_type: Optional[CollaborationType] = None,
                                         limit: int = 20) -> Dict:
        """Get available collaborations for user to join"""
        try:
            available_collaborations = []

            for collaboration in self.collaborations.values():
                # Check if collaboration is accepting participants
                if collaboration.status not in [CollaborationStatus.RECRUITING, CollaborationStatus.PLANNING]:
                    continue

                # Check if user is already a participant
                if user_id in collaboration.participants:
                    continue

                # Check type filter
                if collaboration_type and collaboration.collaboration_type != collaboration_type:
                    continue

                # Check if user meets requirements
                if not await self._meets_collaboration_requirements(user_id, collaboration):
                    continue

                # Check participant limit
                max_participants = collaboration.settings.get("max_participants", self.config["max_participants_per_collaboration"])
                if len(collaboration.participants) >= max_participants:
                    continue

                collab_info = {
                    "id": collaboration.id,
                    "title": collaboration.title,
                    "description": collaboration.description,
                    "type": collaboration.collaboration_type.value,
                    "difficulty": collaboration.settings.get("difficulty", "normal"),
                    "participant_count": len(collaboration.participants),
                    "max_participants": max_participants,
                    "required_participants": collaboration.settings.get("min_participants", 2),
                    "deadline": collaboration.deadline.isoformat() if collaboration.deadline else None,
                    "created_date": collaboration.created_date.isoformat(),
                    "tags": collaboration.tags
                }
                available_collaborations.append(collab_info)

            # Sort by creation date (newest first)
            available_collaborations.sort(
                key=lambda x: x["created_date"],
                reverse=True
            )

            # Apply limit
            available_collaborations = available_collaborations[:limit]

            return {
                "success": True,
                "collaborations": available_collaborations,
                "total_count": len(available_collaborations)
            }

        except Exception as e:
            self.logger.error(f"Error getting available collaborations: {e}")
            return {"success": False, "error": str(e)}

    async def complete_collaboration(self, user_id: str, collaboration_id: str, force: bool = False) -> Dict:
        """Complete a collaboration"""
        try:
            if collaboration_id not in self.collaborations:
                return {"success": False, "error": "Collaboration not found"}

            collaboration = self.collaborations[collaboration_id]

            # Check permissions
            if not await self._can_complete_collaboration(user_id, collaboration):
                return {"success": False, "error": "No permission to complete this collaboration"}

            # Check if collaboration can be completed
            if not force and not await self._can_auto_complete(collaboration):
                return {"success": False, "error": "Collaboration objectives are not yet completed"}

            # Mark as completed
            collaboration.status = CollaborationStatus.COMPLETED
            collaboration.end_date = datetime.now()

            # Calculate final scores and distribute rewards
            await self._finalize_collaboration(collaboration_id)

            # Update participant history
            for participant_id in collaboration.participants:
                self.active_collaborations[participant_id].discard(collaboration_id)
                self.collaboration_history[participant_id].append(collaboration_id)

                # Update participant stats
                if participant_id not in self.participant_stats:
                    self.participant_stats[participant_id] = {
                        "total_contributions": 0,
                        "total_amount": 0.0,
                        "collaborations_completed": 0,
                        "average_rating": 0.0
                    }
                self.participant_stats[participant_id]["collaborations_completed"] += 1

            self.logger.info(f"Collaboration {collaboration_id} completed by {user_id}")

            return {
                "success": True,
                "message": f"Collaboration '{collaboration.title}' completed successfully"
            }

        except Exception as e:
            self.logger.error(f"Error completing collaboration: {e}")
            return {"success": False, "error": str(e)}

    async def get_templates(self, collaboration_type: Optional[CollaborationType] = None) -> Dict:
        """Get available collaboration templates"""
        try:
            templates = []

            for template in self.templates.values():
                # Apply type filter
                if collaboration_type and template.collaboration_type != collaboration_type:
                    continue

                template_info = {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "type": template.collaboration_type.value,
                    "difficulty": template.difficulty,
                    "required_participants": template.required_participants,
                    "max_participants": template.max_participants,
                    "estimated_duration": template.estimated_duration,
                    "tags": template.tags
                }
                templates.append(template_info)

            return {
                "success": True,
                "templates": templates,
                "total_count": len(templates)
            }

        except Exception as e:
            self.logger.error(f"Error getting templates: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    async def _validate_collaboration_creation(self, creator_id: str, collaboration_data: Dict) -> Dict:
        """Validate collaboration creation requirements"""
        try:
            # Check user limits
            active_count = len(self.active_collaborations.get(creator_id, set()))
            if active_count >= self.config["max_collaborations_per_user"]:
                return {"valid": False, "error": "Maximum active collaborations reached"}

            # Validate required fields
            if not collaboration_data.get("title"):
                return {"valid": False, "error": "Title is required"}

            if not collaboration_data.get("type"):
                return {"valid": False, "error": "Type is required"}

            # Validate collaboration type
            try:
                CollaborationType(collaboration_data["type"])
            except ValueError:
                return {"valid": False, "error": "Invalid collaboration type"}

            # Validate deadline if provided
            if collaboration_data.get("deadline"):
                deadline = datetime.fromisoformat(collaboration_data["deadline"])
                if deadline <= datetime.now():
                    return {"valid": False, "error": "Deadline must be in the future"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating collaboration creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _validate_template_creation(self, creator_id: str, template_data: Dict) -> Dict:
        """Validate template creation requirements"""
        try:
            # Validate required fields
            if not template_data.get("name"):
                return {"valid": False, "error": "Name is required"}

            if not template_data.get("type"):
                return {"valid": False, "error": "Type is required"}

            # Validate collaboration type
            try:
                CollaborationType(template_data["type"])
            except ValueError:
                return {"valid": False, "error": "Invalid collaboration type"}

            # Validate participant counts
            if template_data.get("required_participants", 0) < 1:
                return {"valid": False, "error": "Must require at least 1 participant"}

            if (template_data.get("max_participants", 0) <
                template_data.get("required_participants", 1)):
                return {"valid": False, "error": "Max participants must be >= required participants"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating template creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _meets_collaboration_requirements(self, user_id: str, collaboration: Collaboration) -> bool:
        """Check if user meets collaboration requirements"""
        # Check level requirement
        required_level = collaboration.settings.get("required_level", 1)
        user_level = await self._get_user_level(user_id)
        if user_level < required_level:
            return False

        # Check skill requirements
        required_skills = collaboration.settings.get("required_skills", {})
        for skill, required_level in required_skills.items():
            user_skill_level = await self._get_user_skill(user_id, skill)
            if user_skill_level < required_level:
                return False

        # Check reputation requirement
        required_reputation = collaboration.settings.get("required_reputation", 0)
        user_reputation = await self._get_user_reputation(user_id)
        if user_reputation < required_reputation:
            return False

        return True

    async def _validate_contribution(self, user_id: str, collaboration_id: str,
                                   contribution_type: ContributionType, amount: float) -> Dict:
        """Validate a contribution"""
        if amount <= 0:
            return {"valid": False, "error": "Contribution amount must be positive"}

        # Check contribution limits if applicable
        collaboration = self.collaborations[collaboration_id]
        contribution_limits = collaboration.settings.get("contribution_limits", {})

        if contribution_type.value in contribution_limits:
            daily_limit = contribution_limits[contribution_type.value].get("daily", float('inf'))
            user_contributions_today = await self._get_user_contributions_today(user_id, collaboration_id, contribution_type)
            if user_contributions_today + amount > daily_limit:
                return {"valid": False, "error": "Daily contribution limit exceeded"}

        return {"valid": True}

    async def _update_objective_progress(self, collaboration_id: str, objective_id: str, amount: float):
        """Update objective progress from contribution"""
        collaboration = self.collaborations[collaboration_id]

        for objective in collaboration.objectives:
            if objective.id == objective_id:
                old_progress = objective.current_progress
                objective.current_progress = min(objective.current_progress + int(amount), objective.required_amount)

                if not objective.completed and objective.current_progress >= objective.required_amount:
                    objective.completed = True
                    objective.completion_date = datetime.now()
                    self.collaboration_stats[collaboration_id]["objectives_completed"] += 1

                break

    async def _update_resource_pool(self, collaboration_id: str, contribution: CollaborationContribution):
        """Update resource pool from contribution"""
        # Find relevant resource pool
        for pool in self.resource_pools.values():
            if (pool.collaboration_id == collaboration_id and
                pool.resource_type == contribution.metadata.get("resource_type")):
                pool.current_amount += int(contribution.amount)
                pool.contributions[contribution.participant_id] = pool.contributions.get(contribution.participant_id, 0) + int(contribution.amount)
                pool.last_updated = datetime.now()
                break

    async def _update_collaboration_progress(self, collaboration_id: str):
        """Update overall collaboration progress"""
        collaboration = self.collaborations[collaboration_id]

        if not collaboration.objectives:
            collaboration.progress_percentage = 0.0
            return

        total_required = sum(obj.required_amount for obj in collaboration.objectives)
        total_completed = sum(obj.current_progress for obj in collaboration.objectives)

        collaboration.progress_percentage = (total_completed / total_required * 100) if total_required > 0 else 0.0

    async def _check_objectives_completion(self, collaboration_id: str):
        """Check and handle completed objectives"""
        collaboration = self.collaborations[collaboration_id]

        for objective in collaboration.objectives:
            if not objective.completed and objective.current_progress >= objective.required_amount:
                objective.completed = True
                objective.completion_date = datetime.now()
                await self._distribute_objective_rewards(collaboration_id, objective)

    async def _check_collaboration_completion(self, collaboration_id: str):
        """Check if collaboration can be auto-completed"""
        collaboration = self.collaborations[collaboration_id]

        if await self._can_auto_complete(collaboration):
            collaboration.status = CollaborationStatus.COMPLETED
            collaboration.end_date = datetime.now()
            await self._finalize_collaboration(collaboration_id)

    async def _can_auto_complete(self, collaboration: Collaboration) -> bool:
        """Check if collaboration can be automatically completed"""
        if collaboration.status != CollaborationStatus.ACTIVE:
            return False

        # Check if all required objectives are completed
        required_objectives = [obj for obj in collaboration.objectives if obj.priority >= 3]
        if required_objectives and not all(obj.completed for obj in required_objectives):
            return False

        # Check if progress threshold is met
        progress_threshold = collaboration.settings.get("completion_threshold", 100)
        if collaboration.progress_percentage < progress_threshold:
            return False

        return True

    async def _finalize_collaboration(self, collaboration_id: str):
        """Finalize collaboration completion"""
        collaboration = self.collaborations[collaboration_id]

        # Calculate final contributions and distribute rewards
        await self._distribute_final_rewards(collaboration_id)

        # Generate completion report
        await self._generate_completion_report(collaboration_id)

        # Update stats
        self.collaboration_stats[collaboration_id]["completion_date"] = datetime.now()

    async def _distribute_objective_rewards(self, collaboration_id: str, objective: CollaborationObjective):
        """Distribute rewards for completed objective"""
        collaboration = self.collaborations[collaboration_id]

        # Give rewards to participants who contributed to this objective
        for participant_id in collaboration.participants:
            if await self._contributed_to_objective(participant_id, collaboration_id, objective.id):
                await self._award_rewards_to_participant(participant_id, objective.rewards)

    async def _distribute_final_rewards(self, collaboration_id: str):
        """Distribute final rewards based on contribution"""
        collaboration = self.collaborations[collaboration_id]

        if collaboration.reward_distribution == RewardDistribution.EQUAL:
            # Equal distribution to all participants
            for participant_id in collaboration.participants:
                await self._award_rewards_to_participant(participant_id, collaboration.rewards)

        elif collaboration.reward_distribution == RewardDistribution.CONTRIBUTION_BASED:
            # Distribute based on contribution scores
            total_score = sum(info["contribution_score"] for info in collaboration.participants.values())
            if total_score > 0:
                for participant_id, info in collaboration.participants.items():
                    share = info["contribution_score"] / total_score
                    weighted_rewards = await self._calculate_weighted_rewards(collaboration.rewards, share)
                    await self._award_rewards_to_participant(participant_id, weighted_rewards)

        # Add to collaboration history
        for participant_id in collaboration.participants:
            self.collaboration_history[participant_id].append(collaboration_id)

    async def _can_update_objective(self, user_id: str, collaboration: Collaboration, objective: CollaborationObjective) -> bool:
        """Check if user can update objective"""
        participant_info = collaboration.participants.get(user_id, {})
        permissions = participant_info.get("permissions", [])

        return ("manage" in permissions or
                "lead" in permissions or
                user_id == collaboration.leader_id or
                user_id in objective.assigned_to)

    async def _can_complete_collaboration(self, user_id: str, collaboration: Collaboration) -> bool:
        """Check if user can complete collaboration"""
        participant_info = collaboration.participants.get(user_id, {})
        permissions = participant_info.get("permissions", [])

        return ("complete" in permissions or
                "manage" in permissions or
                "lead" in permissions or
                user_id == collaboration.leader_id)

    async def _transfer_leadership_and_leave(self, user_id: str, collaboration_id: str, reason: str) -> Dict:
        """Transfer leadership and leave collaboration"""
        collaboration = self.collaborations[collaboration_id]

        # Find eligible successor
        eligible_participants = [
            (pid, info) for pid, info in collaboration.participants.items()
            if pid != user_id and info.get("role") in ["officer", "veteran", "member"]
        ]

        if not eligible_participants:
            # No eligible successor, cancel collaboration
            collaboration.status = CollaborationStatus.CANCELLED
            collaboration.end_date = datetime.now()

            # Remove all participants
            for participant_id in list(collaboration.participants.keys()):
                if participant_id != user_id:
                    self.active_collaborations[participant_id].discard(collaboration_id)
                    self.collaboration_history[participant_id].append(collaboration_id)

            # Remove leader
            del collaboration.participants[user_id]
            self.active_collaborations[user_id].discard(collaboration_id)
            self.collaboration_history[user_id].append(collaboration_id)

            return {
                "success": True,
                "collaboration_cancelled": True,
                "message": "Collaboration cancelled due to leader leaving with no successor"
            }

        # Transfer leadership to most qualified participant
        successor_id, successor_info = max(
            eligible_participants,
            key=lambda x: (x[1].get("contribution_score", 0), x[1]["join_date"])
        )

        # Transfer leadership
        collaboration.leader_id = successor_id
        successor_info["role"] = "leader"
        successor_info["permissions"] = ["lead", "invite", "manage", "complete"]

        # Remove old leader
        del collaboration.participants[user_id]
        self.active_collaborations[user_id].discard(collaboration_id)
        self.collaboration_history[user_id].append(collaboration_id)

        return {
            "success": True,
            "new_leader": successor_id,
            "message": f"Leadership transferred to {successor_id}"
        }

    async def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for a role"""
        permission_map = {
            "leader": ["lead", "invite", "manage", "complete", "kick"],
            "officer": ["invite", "manage"],
            "veteran": ["invite"],
            "member": [],
            "participant": []
        }
        return permission_map.get(role, [])

    async def _create_team_role(self, collaboration_id: str, role_data: Dict):
        """Create a team role for collaboration"""
        role = TeamRole(
            id=str(uuid.uuid4()),
            name=role_data["name"],
            description=role_data.get("description", ""),
            permissions=role_data.get("permissions", []),
            responsibilities=role_data.get("responsibilities", []),
            requirements=role_data.get("requirements", {}),
            benefits=role_data.get("benefits", {}),
            max_assignments=role_data.get("max_assignments", -1)
        )
        self.team_roles[role.id] = role

    async def _contributed_to_objective(self, participant_id: str, collaboration_id: str, objective_id: str) -> bool:
        """Check if participant contributed to specific objective"""
        collaboration = self.collaborations[collaboration_id]
        for contribution in collaboration.contributions:
            if (contribution.participant_id == participant_id and
                contribution.objective_id == objective_id):
                return True
        return False

    async def _award_rewards_to_participant(self, participant_id: str, rewards: Dict):
        """Award rewards to a participant"""
        # This would integrate with your reward system
        pass

    async def _calculate_weighted_rewards(self, base_rewards: Dict, share: float) -> Dict:
        """Calculate weighted rewards based on share"""
        weighted_rewards = {}
        for reward_type, amount in base_rewards.items():
            if isinstance(amount, (int, float)):
                weighted_rewards[reward_type] = int(amount * share)
            else:
                weighted_rewards[reward_type] = amount
        return weighted_rewards

    async def _generate_completion_report(self, collaboration_id: str):
        """Generate collaboration completion report"""
        collaboration = self.collaborations[collaboration_id]

        report = {
            "collaboration_id": collaboration_id,
            "title": collaboration.title,
            "completion_date": collaboration.end_date.isoformat(),
            "duration_days": (collaboration.end_date - collaboration.start_date).days if collaboration.start_date else 0,
            "final_progress": collaboration.progress_percentage,
            "participants": len(collaboration.participants),
            "objectives_completed": len([obj for obj in collaboration.objectives if obj.completed]),
            "total_objectives": len(collaboration.objectives),
            "total_contributions": len(collaboration.contributions)
        }

        # Store report (would go to database in production)
        self.logger.info(f"Completion report generated for {collaboration_id}: {report}")

    # Mock methods for integration
    async def _get_user_level(self, user_id: str) -> int:
        """Get user level"""
        return 15  # Placeholder

    async def _get_user_skill(self, user_id: str, skill: str) -> int:
        """Get user skill level"""
        return 10  # Placeholder

    async def _get_user_reputation(self, user_id: str) -> int:
        """Get user reputation"""
        return 500  # Placeholder

    async def _get_user_contributions_today(self, user_id: str, collaboration_id: str, contribution_type: ContributionType) -> float:
        """Get user's contributions today"""
        return 0.0  # Placeholder

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Progress update task
        self._background_tasks.append(
            asyncio.create_task(self._progress_update_task())
        )

        # Cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_task())
        )

        # Reminder task
        self._background_tasks.append(
            asyncio.create_task(self._reminder_task())
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

    async def _progress_update_task(self):
        """Periodic progress updates"""
        while self._running:
            try:
                # Update progress for active collaborations
                for collaboration_id, collaboration in self.collaborations.items():
                    if collaboration.status == CollaborationStatus.ACTIVE:
                        await self._update_collaboration_progress(collaboration_id)
                        await self._check_collaboration_completion(collaboration_id)

                await asyncio.sleep(self.config["progress_update_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in progress update task: {e}")
                await asyncio.sleep(60)

    async def _cleanup_task(self):
        """Periodic cleanup of old data"""
        while self._running:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.config["cleanup_completed_days"])

                # Clean up completed collaborations
                for collaboration_id, collaboration in list(self.collaborations.items()):
                    if (collaboration.status == CollaborationStatus.COMPLETED and
                        collaboration.end_date and collaboration.end_date < cutoff_date):
                        del self.collaborations[collaboration_id]

                await asyncio.sleep(86400)  # Daily

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)

    async def _reminder_task(self):
        """Periodic reminder notifications"""
        while self._running:
            try:
                # Send reminders for upcoming deadlines
                for collaboration in self.collaborations.values():
                    if (collaboration.deadline and
                        collaboration.status == CollaborationStatus.ACTIVE):
                        time_remaining = collaboration.deadline - datetime.now()
                        if timedelta(hours=24) <= time_remaining <= timedelta(hours=25):
                            await self._send_deadline_reminder(collaboration)

                await asyncio.sleep(self.config["reminder_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in reminder task: {e}")
                await asyncio.sleep(600)

    async def _send_deadline_reminder(self, collaboration: Collaboration):
        """Send deadline reminder to participants"""
        # This would integrate with your notification system
        self.logger.info(f"Deadline reminder sent for collaboration {collaboration.id}")

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize collaboration tools
        collab_tools = CollaborationTools()

        # Start background tasks
        await collab_tools.start_background_tasks()

        # Create a collaboration template
        template = await collab_tools.create_template("admin", {
            "name": "Dragon Hunt Raid",
            "type": "raid",
            "description": "Cooperative raid to defeat the ancient dragon",
            "objectives": [
                {
                    "title": "Gather Dragon Slaying Equipment",
                    "type": "collect",
                    "required_amount": 10,
                    "difficulty": "hard"
                },
                {
                    "title": "Defeat the Ancient Dragon",
                    "type": "kill",
                    "required_amount": 1,
                    "difficulty": "legendary"
                }
            ],
            "required_participants": 5,
            "max_participants": 20,
            "estimated_duration": 180,
            "difficulty": "hard"
        })
        print(f"Template created: {template['template_id']}")

        # Create collaboration from template
        collab = await collab_tools.create_from_template("player1", template["template_id"], {
            "title": "Weekend Dragon Hunt",
            "deadline": (datetime.now() + timedelta(days=3)).isoformat()
        })
        print(f"Collaboration created: {collab['collaboration_id']}")

        if collab["success"]:
            collaboration_id = collab["collaboration_id"]

            # Add participants
            await collab_tools.join_collaboration("player2", collaboration_id)
            await collab_tools.join_collaboration("player3", collaboration_id)

            # Add contributions
            await collab_tools.add_contribution(
                "player1",
                collaboration_id,
                ContributionType.RESOURCES,
                100.0,
                "Donated rare materials for equipment"
            )

            await collab_tools.add_contribution(
                "player2",
                collaboration_id,
                ContributionType.CRAFTING,
                50.0,
                "Crafted dragon-slaying weapons"
            )

            # Update objective progress
            await collab_tools.update_objective(
                "player2",
                collaboration_id,
                collab_tools.collaborations[collaboration_id].objectives[0].id,
                3
            )

            # Get collaboration info
            info = await collab_tools.get_collaboration_info(collaboration_id, "player1")
            print(f"Collaboration progress: {info['collaboration']['progress_percentage']:.1f}%")

            # Get user collaborations
            user_collabs = await collab_tools.get_user_collaborations("player1")
            print(f"Player1 active collaborations: {user_collabs['total_count']}")

        # Get available collaborations
        available = await collab_tools.get_available_collaborations("player4")
        print(f"Available collaborations: {available['total_count']}")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await collab_tools.stop_background_tasks()

    asyncio.run(main())