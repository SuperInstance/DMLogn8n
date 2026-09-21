#!/usr/bin/env python3
"""
DMLogn8n Community Events - Dynamic Social Events and Gatherings System

Handles dynamic events, tournaments, seasonal celebrations, community gatherings,
world events, automated event generation, and social event management.

Features:
- Dynamic event generation and scheduling
- Tournament and competition systems
- Seasonal and holiday events
- Community gathering management
- World event coordination
- Event participation tracking
- Reward distribution systems
- Event leaderboards and rankings
- Social event discovery
- Event creation tools
- Cross-server event synchronization
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

class EventType(Enum):
    """Types of community events"""
    TOURNAMENT = "tournament"
    SEASONAL = "seasonal"
    HOLIDAY = "holiday"
    WORLD_EVENT = "world_event"
    COMMUNITY_GATHERING = "community_gathering"
    QUEST_EVENT = "quest_event"
    COMPETITION = "competition"
    SOCIAL_EVENT = "social_event"
    CELEBRATION = "celebration"
    FESTIVAL = "festival"
    RAID_EVENT = "raid_event"
    PVP_EVENT = "pvp_event"
    CRAFTING_EVENT = "crafting_event"
    EXPLORATION_EVENT = "exploration_event"
    CHARITY_EVENT = "charity_event"
    LEARNING_EVENT = "learning_event"

class EventStatus(Enum):
    """Status of events"""
    PLANNED = "planned"
    ANNOUNCED = "announced"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    PREPARING = "preparing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    SUSPENDED = "suspended"

class EventFrequency(Enum):
    """Event frequency patterns"""
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ParticipationType(Enum):
    """Types of event participation"""
    INDIVIDUAL = "individual"
    TEAM = "team"
    GUILD = "guild"
    PARTY = "party"
    FACTION = "faction"
    SERVER = "server"
    CROSS_SERVER = "cross_server"
    COMMUNITY = "community"

class RewardType(Enum):
    """Types of event rewards"""
    EXPERIENCE = "experience"
    CURRENCY = "currency"
    ITEMS = "items"
    TITLES = "titles"
    ACHIEVEMENTS = "achievements"
    COSMETICS = "cosmetics"
    BONUSES = "bonuses"
    ACCESS = "access"
    RECOGNITION = "recognition"

@dataclass
class EventObjective:
    """Objective within an event"""
    id: str
    title: str
    description: str
    objective_type: str
    required_amount: int = 1
    points_value: int = 10
    difficulty: str = "normal"
    time_limit: Optional[int] = None  # seconds
    optional: bool = False
    hidden: bool = False
    prerequisites: List[str] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EventParticipation:
    """Record of event participation"""
    id: str
    event_id: str
    participant_id: str
    participation_type: ParticipationType
    registration_date: datetime
    team_id: Optional[str] = None
    status: str = "registered"  # registered, active, completed, dropped, disqualified
    score: float = 0.0
    rank: Optional[int] = None
    objectives_completed: List[str] = field(default_factory=list)
    contributions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EventReward:
    """Reward structure for event"""
    id: str
    reward_type: RewardType
    value: Union[int, float, str, Dict]
    description: str
    requirement_type: str  # participation, completion, rank, objective, points
    requirement_value: Any
    quantity: int = 1
    distribution_method: str = "automatic"  # automatic, manual, claim
    expires_date: Optional[datetime] = None

@dataclass
class CommunityEvent:
    """Main community event structure"""
    id: str
    name: str
    description: str
    event_type: EventType
    frequency: EventFrequency
    status: EventStatus
    creator_id: str
    organizer_ids: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    location: Dict[str, Any] = field(default_factory=dict)
    max_participants: Optional[int] = None
    min_participants: int = 1
    participation_types: List[ParticipationType] = field(default_factory=list)
    objectives: List[EventObjective] = field(default_factory=list)
    rewards: List[EventReward] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

@dataclass
class EventSchedule:
    """Schedule for recurring events"""
    id: str
    event_template_id: str
    frequency: EventFrequency
    schedule_pattern: Dict[str, Any]  # Cron-like pattern
    next_occurrence: datetime
    max_occurrences: Optional[int] = None
    occurrences_created: int = 0
    active: bool = True
    created_date: datetime = field(default_factory=datetime.now)

@dataclass
class EventLeaderboard:
    """Leaderboard for event rankings"""
    id: str
    event_id: str
    leaderboard_type: str  # individual, team, guild
    entries: List[Dict] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    auto_update: bool = True
    max_entries: int = 100

class CommunityEventManager:
    """Main community event management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.events: Dict[str, CommunityEvent] = {}
        self.event_templates: Dict[str, CommunityEvent] = {}
        self.schedules: Dict[str, EventSchedule] = {}
        self.participations: Dict[str, List[EventParticipation]] = defaultdict(list)
        self.leaderboards: Dict[str, EventLeaderboard] = {}

        # Event tracking
        self.active_events: Set[str] = set()
        self.upcoming_events: Set[str] = set()
        self.event_categories: Dict[str, List[str]] = defaultdict(list)

        # Statistics and analytics
        self.event_stats: Dict[str, Dict] = {}
        self.participant_stats: Dict[str, Dict] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_events_per_day": 10,
            "max_participants_per_event": 1000,
            "registration_advance_days": 7,
            "event_duration_hours": 2,
            "leaderboard_update_interval": 300,  # 5 minutes
            "schedule_check_interval": 300,  # 5 minutes
            "cleanup_completed_days": 30,
            "auto_reward_distribution": True,
            "notification_advance_hours": 24,
            "reminder_intervals": [24, 6, 1],  # hours before event
            "min_event_duration_minutes": 30,
            "max_event_duration_hours": 24,
            "default_participant_limit": 100,
            "auto_generate_events": True,
            "seasonal_event_templates": True,
            "cross_server_events": False
        }

    async def create_event(self, creator_id: str, event_data: Dict) -> Dict:
        """Create a new community event"""
        try:
            # Validate event creation
            validation_result = await self._validate_event_creation(creator_id, event_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Generate event ID
            event_id = str(uuid.uuid4())

            # Parse dates
            start_date = datetime.fromisoformat(event_data["start_date"]) if event_data.get("start_date") else None
            end_date = datetime.fromisoformat(event_data["end_date"]) if event_data.get("end_date") else None
            registration_start = datetime.fromisoformat(event_data["registration_start"]) if event_data.get("registration_start") else None
            registration_end = datetime.fromisoformat(event_data["registration_end"]) if event_data.get("registration_end") else None

            # Create event
            event = CommunityEvent(
                id=event_id,
                name=event_data["name"],
                description=event_data.get("description", ""),
                event_type=EventType(event_data["type"]),
                frequency=EventFrequency(event_data.get("frequency", "one_time")),
                status=EventStatus.PLANNED,
                creator_id=creator_id,
                organizer_ids=event_data.get("organizer_ids", [creator_id]),
                start_date=start_date,
                end_date=end_date,
                registration_start=registration_start,
                registration_end=registration_end,
                location=event_data.get("location", {}),
                max_participants=event_data.get("max_participants"),
                min_participants=event_data.get("min_participants", 1),
                participation_types=[ParticipationType(pt) for pt in event_data.get("participation_types", ["individual"])],
                rules=event_data.get("rules", []),
                tags=event_data.get("tags", []),
                settings=event_data.get("settings", {}),
                metadata=event_data.get("metadata", {})
            )

            # Add objectives
            for obj_data in event_data.get("objectives", []):
                objective = EventObjective(
                    id=str(uuid.uuid4()),
                    title=obj_data["title"],
                    description=obj_data.get("description", ""),
                    objective_type=obj_data["type"],
                    required_amount=obj_data.get("required_amount", 1),
                    points_value=obj_data.get("points_value", 10),
                    difficulty=obj_data.get("difficulty", "normal"),
                    time_limit=obj_data.get("time_limit"),
                    optional=obj_data.get("optional", False),
                    hidden=obj_data.get("hidden", False),
                    prerequisites=obj_data.get("prerequisites", []),
                    rewards=obj_data.get("rewards", {})
                )
                event.objectives.append(objective)

            # Add rewards
            for reward_data in event_data.get("rewards", []):
                reward = EventReward(
                    id=str(uuid.uuid4()),
                    reward_type=RewardType(reward_data["type"]),
                    value=reward_data["value"],
                    description=reward_data.get("description", ""),
                    requirement_type=reward_data.get("requirement_type", "participation"),
                    requirement_value=reward_data.get("requirement_value"),
                    quantity=reward_data.get("quantity", 1),
                    distribution_method=reward_data.get("distribution_method", "automatic")
                )
                event.rewards.append(reward)

            # Store event
            self.events[event_id] = event

            # Create leaderboard
            leaderboard = EventLeaderboard(
                id=str(uuid.uuid4()),
                event_id=event_id,
                leaderboard_type="individual"
            )
            self.leaderboards[event_id] = leaderboard

            # Initialize stats
            self.event_stats[event_id] = {
                "created_date": datetime.now(),
                "views": 0,
                "registrations": 0,
                "participants": 0,
                "completion_rate": 0.0,
                "average_rating": 0.0
            }

            # Add to categories
            for tag in event.tags:
                self.event_categories[tag].append(event_id)

            # Schedule automatic status updates
            if event.start_date:
                await self._schedule_event_status_updates(event_id)

            self.logger.info(f"Event '{event.name}' created by {creator_id}")

            return {
                "success": True,
                "event_id": event_id,
                "event": asdict(event),
                "message": f"Event '{event.name}' created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating event: {e}")
            return {"success": False, "error": str(e)}

    async def register_for_event(self, user_id: str, event_id: str, participation_type: ParticipationType,
                               team_id: str = None) -> Dict:
        """Register a user for an event"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            event = self.events[event_id]

            # Check registration requirements
            if not await self._can_register_for_event(user_id, event):
                return {"success": False, "error": "Cannot register for this event"}

            # Check if already registered
            for participation in self.participations[event_id]:
                if participation.participant_id == user_id:
                    return {"success": False, "error": "Already registered for this event"}

            # Check participant limit
            if event.max_participants:
                current_participants = len([p for p in self.participations[event_id] if p.status in ["registered", "active"]])
                if current_participants >= event.max_participants:
                    return {"success": False, "error": "Event is full"}

            # Create participation record
            participation = EventParticipation(
                id=str(uuid.uuid4()),
                event_id=event_id,
                participant_id=user_id,
                participation_type=participation_type,
                registration_date=datetime.now(),
                team_id=team_id
            )

            # Add to participations
            self.participations[event_id].append(participation)

            # Update stats
            self.event_stats[event_id]["registrations"] += 1

            self.logger.info(f"User {user_id} registered for event {event_id}")

            return {
                "success": True,
                "participation_id": participation.id,
                "message": f"Successfully registered for '{event.name}'"
            }

        except Exception as e:
            self.logger.error(f"Error registering for event: {e}")
            return {"success": False, "error": str(e)}

    async def start_event(self, event_id: str, initiator_id: str = None) -> Dict:
        """Start an event"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            event = self.events[event_id]

            # Check if event can be started
            if not await self._can_start_event(event, initiator_id):
                return {"success": False, "error": "Cannot start this event"}

            # Update event status
            event.status = EventStatus.ACTIVE
            event.start_date = event.start_date or datetime.now()
            if not event.end_date:
                duration = timedelta(hours=self.config["event_duration_hours"])
                event.end_date = event.start_date + duration

            # Move to active events
            self.active_events.add(event_id)
            self.upcoming_events.discard(event_id)

            # Initialize active participants
            active_participants = [p for p in self.participations[event_id] if p.status == "registered"]
            for participation in active_participants:
                participation.status = "active"

            # Update stats
            self.event_stats[event_id]["participants"] = len(active_participants)

            # Send notifications
            await self._send_event_notification(event_id, "event_started", f"Event '{event.name}' has started!")

            self.logger.info(f"Event {event_id} started")

            return {
                "success": True,
                "event_id": event_id,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "active_participants": len(active_participants),
                "message": f"Event '{event.name}' has started!"
            }

        except Exception as e:
            self.logger.error(f"Error starting event: {e}")
            return {"success": False, "error": str(e)}

    async def complete_objective(self, user_id: str, event_id: str, objective_id: str, progress: int = 1) -> Dict:
        """Complete an event objective for a user"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            event = self.events[event_id]

            # Find objective
            objective = None
            for obj in event.objectives:
                if obj.id == objective_id:
                    objective = obj
                    break

            if not objective:
                return {"success": False, "error": "Objective not found"}

            # Check if event is active
            if event.status != EventStatus.ACTIVE:
                return {"success": False, "error": "Event is not active"}

            # Find user participation
            participation = None
            for p in self.participations[event_id]:
                if p.participant_id == user_id and p.status == "active":
                    participation = p
                    break

            if not participation:
                return {"success": False, "error": "Not actively participating in this event"}

            # Check if objective already completed
            if objective_id in participation.objectives_completed:
                return {"success": False, "error": "Objective already completed"}

            # Update progress (simplified - in practice would track partial progress)
            if progress >= objective.required_amount:
                # Mark objective as completed
                participation.objectives_completed.append(objective_id)
                participation.score += objective.points_value

                # Update leaderboard
                await self._update_leaderboard(event_id, user_id, participation.score)

                # Award immediate rewards if any
                if objective.rewards:
                    await self._award_objective_rewards(user_id, objective.rewards)

                self.logger.info(f"User {user_id} completed objective {objective_id} in event {event_id}")

                return {
                    "success": True,
                    "objective_id": objective_id,
                    "points_awarded": objective.points_value,
                    "total_score": participation.score,
                    "message": f"Objective '{objective.title}' completed!"
                }
            else:
                return {
                    "success": False,
                    "error": "Objective requirements not met"
                }

        except Exception as e:
            self.logger.error(f"Error completing objective: {e}")
            return {"success": False, "error": str(e)}

    async def end_event(self, event_id: str, initiator_id: str = None) -> Dict:
        """End an event and calculate results"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            event = self.events[event_id]

            # Check if event can be ended
            if not await self._can_end_event(event, initiator_id):
                return {"success": False, "error": "Cannot end this event"}

            # Update event status
            event.status = EventStatus.COMPLETED
            event.end_date = event.end_date or datetime.now()

            # Move from active events
            self.active_events.discard(event_id)

            # Calculate final results
            results = await self._calculate_event_results(event_id)

            # Distribute rewards
            if self.config["auto_reward_distribution"]:
                await self._distribute_event_rewards(event_id)

            # Generate completion report
            await self._generate_event_report(event_id)

            # Update participant stats
            await self._update_participant_stats(event_id)

            # Send notifications
            await self._send_event_notification(event_id, "event_ended", f"Event '{event.name}' has ended!")

            self.logger.info(f"Event {event_id} ended")

            return {
                "success": True,
                "event_id": event_id,
                "results": results,
                "message": f"Event '{event.name}' has ended successfully"
            }

        except Exception as e:
            self.logger.error(f"Error ending event: {e}")
            return {"success": False, "error": str(e)}

    async def create_event_template(self, creator_id: str, template_data: Dict) -> Dict:
        """Create an event template"""
        try:
            # Validate template creation
            validation_result = await self._validate_template_creation(creator_id, template_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Create template
            template = CommunityEvent(
                id=str(uuid.uuid4()),
                name=template_data["name"],
                description=template_data.get("description", ""),
                event_type=EventType(template_data["type"]),
                frequency=EventFrequency(template_data.get("frequency", "one_time")),
                status=EventStatus.PLANNED,
                creator_id=creator_id,
                organizer_ids=template_data.get("organizer_ids", []),
                participation_types=[ParticipationType(pt) for pt in template_data.get("participation_types", ["individual"])],
                rules=template_data.get("rules", []),
                tags=template_data.get("tags", []),
                settings=template_data.get("settings", {}),
                metadata={"is_template": True, **template_data.get("metadata", {})}
            )

            # Add template objectives
            for obj_data in template_data.get("objectives", []):
                objective = EventObjective(
                    id=str(uuid.uuid4()),
                    title=obj_data["title"],
                    description=obj_data.get("description", ""),
                    objective_type=obj_data["type"],
                    required_amount=obj_data.get("required_amount", 1),
                    points_value=obj_data.get("points_value", 10),
                    difficulty=obj_data.get("difficulty", "normal"),
                    optional=obj_data.get("optional", False),
                    hidden=obj_data.get("hidden", False)
                )
                template.objectives.append(objective)

            # Add template rewards
            for reward_data in template_data.get("rewards", []):
                reward = EventReward(
                    id=str(uuid.uuid4()),
                    reward_type=RewardType(reward_data["type"]),
                    value=reward_data["value"],
                    description=reward_data.get("description", ""),
                    requirement_type=reward_data.get("requirement_type", "participation"),
                    requirement_value=reward_data.get("requirement_value"),
                    quantity=reward_data.get("quantity", 1)
                )
                template.rewards.append(reward)

            # Store template
            self.event_templates[template.id] = template

            self.logger.info(f"Event template '{template.name}' created by {creator_id}")

            return {
                "success": True,
                "template_id": template.id,
                "template": asdict(template),
                "message": f"Event template '{template.name}' created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating event template: {e}")
            return {"success": False, "error": str(e)}

    async def create_recurring_event_schedule(self, creator_id: str, schedule_data: Dict) -> Dict:
        """Create a schedule for recurring events"""
        try:
            # Validate schedule creation
            validation_result = await self._validate_schedule_creation(creator_id, schedule_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Calculate next occurrence
            next_occurrence = await self._calculate_next_occurrence(schedule_data)

            # Create schedule
            schedule = EventSchedule(
                id=str(uuid.uuid4()),
                event_template_id=schedule_data["event_template_id"],
                frequency=EventFrequency(schedule_data["frequency"]),
                schedule_pattern=schedule_data["schedule_pattern"],
                next_occurrence=next_occurrence,
                max_occurrences=schedule_data.get("max_occurrences"),
                active=schedule_data.get("active", True)
            )

            # Store schedule
            self.schedules[schedule.id] = schedule

            self.logger.info(f"Recurring event schedule created: {schedule.id}")

            return {
                "success": True,
                "schedule_id": schedule.id,
                "next_occurrence": next_occurrence.isoformat(),
                "message": "Recurring event schedule created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating event schedule: {e}")
            return {"success": False, "error": str(e)}

    async def get_event_info(self, event_id: str, user_id: str = None) -> Dict:
        """Get detailed information about an event"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            event = self.events[event_id]

            # Prepare event data
            event_data = {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "type": event.event_type.value,
                "frequency": event.frequency.value,
                "status": event.status.value,
                "creator_id": event.creator_id,
                "organizer_ids": event.organizer_ids,
                "start_date": event.start_date.isoformat() if event.start_date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "registration_start": event.registration_start.isoformat() if event.registration_start else None,
                "registration_end": event.registration_end.isoformat() if event.registration_end else None,
                "location": event.location,
                "max_participants": event.max_participants,
                "min_participants": event.min_participants,
                "participation_types": [pt.value for pt in event.participation_types],
                "rules": event.rules,
                "tags": event.tags,
                "created_date": event.created_date.isoformat(),
                "last_modified": event.last_modified.isoformat()
            }

            # Add statistics
            if event_id in self.event_stats:
                event_data["statistics"] = self.event_stats[event_id]

            # Add objectives
            event_data["objectives"] = [asdict(obj) for obj in event.objectives if not obj.hidden]

            # Add rewards
            event_data["rewards"] = [asdict(reward) for reward in event.rewards]

            # Add participation info for registered users
            if user_id:
                participation = None
                for p in self.participations[event_id]:
                    if p.participant_id == user_id:
                        participation = p
                        break

                if participation:
                    event_data["user_participation"] = {
                        "participation_id": participation.id,
                        "status": participation.status,
                        "score": participation.score,
                        "rank": participation.rank,
                        "objectives_completed": participation.objectives_completed,
                        "team_id": participation.team_id
                    }

                # Check if user can register
                event_data["can_register"] = await self._can_register_for_event(user_id, event)

            # Add leaderboard if event is active or completed
            if event.status in [EventStatus.ACTIVE, EventStatus.COMPLETED]:
                if event_id in self.leaderboards:
                    leaderboard = self.leaderboards[event_id]
                    event_data["leaderboard"] = {
                        "entries": leaderboard.entries[:10],  # Top 10
                        "total_entries": len(leaderboard.entries),
                        "last_updated": leaderboard.last_updated.isoformat()
                    }

            return {
                "success": True,
                "event": event_data
            }

        except Exception as e:
            self.logger.error(f"Error getting event info: {e}")
            return {"success": False, "error": str(e)}

    async def get_upcoming_events(self, user_id: str = None, event_type: Optional[EventType] = None,
                                limit: int = 20) -> Dict:
        """Get upcoming events"""
        try:
            upcoming_events = []
            current_time = datetime.now()

            for event in self.events.values():
                # Filter by status
                if event.status not in [EventStatus.PLANNED, EventStatus.ANNOUNCED, EventStatus.REGISTRATION_OPEN]:
                    continue

                # Filter by type
                if event_type and event.event_type != event_type:
                    continue

                # Check if event has start date
                if not event.start_date:
                    continue

                # Check if event is in the future
                if event.start_date <= current_time:
                    continue

                # Check if user can participate (if user_id provided)
                if user_id and not await self._can_participate_in_event(user_id, event):
                    continue

                # Prepare event summary
                event_summary = {
                    "id": event.id,
                    "name": event.name,
                    "type": event.event_type.value,
                    "status": event.status.value,
                    "start_date": event.start_date.isoformat(),
                    "end_date": event.end_date.isoformat() if event.end_date else None,
                    "registration_end": event.registration_end.isoformat() if event.registration_end else None,
                    "location": event.location,
                    "participant_count": len([p for p in self.participations[event.id] if p.status == "registered"]),
                    "max_participants": event.max_participants,
                    "tags": event.tags
                }
                upcoming_events.append(event_summary)

            # Sort by start date (earliest first)
            upcoming_events.sort(key=lambda x: x["start_date"])

            # Apply limit
            upcoming_events = upcoming_events[:limit]

            return {
                "success": True,
                "events": upcoming_events,
                "total_count": len(upcoming_events)
            }

        except Exception as e:
            self.logger.error(f"Error getting upcoming events: {e}")
            return {"success": False, "error": str(e)}

    async def get_active_events(self, user_id: str = None, limit: int = 10) -> Dict:
        """Get currently active events"""
        try:
            active_events = []

            for event_id in self.active_events:
                if event_id not in self.events:
                    continue

                event = self.events[event_id]

                # Check if user can participate (if user_id provided)
                if user_id and not await self._can_participate_in_event(user_id, event):
                    continue

                # Prepare event summary
                participant_count = len([p for p in self.participations[event_id] if p.status == "active"])
                event_summary = {
                    "id": event.id,
                    "name": event.name,
                    "type": event.event_type.value,
                    "status": event.status.value,
                    "start_date": event.start_date.isoformat() if event.start_date else None,
                    "end_date": event.end_date.isoformat() if event.end_date else None,
                    "location": event.location,
                    "participant_count": participant_count,
                    "max_participants": event.max_participants,
                    "progress_percentage": await self._calculate_event_progress(event_id),
                    "tags": event.tags
                }
                active_events.append(event_summary)

            # Sort by end date (soonest ending first)
            active_events.sort(key=lambda x: x["end_date"] or "9999-12-31")

            # Apply limit
            active_events = active_events[:limit]

            return {
                "success": True,
                "events": active_events,
                "total_count": len(active_events)
            }

        except Exception as e:
            self.logger.error(f"Error getting active events: {e}")
            return {"success": False, "error": str(e)}

    async def get_event_leaderboard(self, event_id: str, user_id: str = None, limit: int = 50) -> Dict:
        """Get event leaderboard"""
        try:
            if event_id not in self.events:
                return {"success": False, "error": "Event not found"}

            if event_id not in self.leaderboards:
                return {"success": False, "error": "Leaderboard not available"}

            event = self.events[event_id]
            leaderboard = self.leaderboards[event_id]

            # Check if user can view leaderboard
            if user_id and not await self._can_view_leaderboard(user_id, event):
                return {"success": False, "error": "No permission to view leaderboard"}

            # Update leaderboard if needed
            if leaderboard.auto_update:
                await self._update_leaderboard(event_id)

            # Prepare entries
            entries = leaderboard.entries[:limit]

            # Find user's rank if provided
            user_rank = None
            if user_id:
                for i, entry in enumerate(leaderboard.entries):
                    if entry["participant_id"] == user_id:
                        user_rank = i + 1
                        break

            return {
                "success": True,
                "event_id": event_id,
                "event_name": event.name,
                "entries": entries,
                "user_rank": user_rank,
                "total_entries": len(leaderboard.entries),
                "last_updated": leaderboard.last_updated.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting event leaderboard: {e}")
            return {"success": False, "error": str(e)}

    async def auto_generate_seasonal_events(self):
        """Automatically generate seasonal events"""
        try:
            current_date = datetime.now()
            season = self._get_current_season(current_date)

            # Get seasonal templates
            seasonal_templates = [
                template for template in self.event_templates.values()
                if season in template.tags and template.metadata.get("auto_generate", False)
            ]

            for template in seasonal_templates:
                # Check if event already exists for this season
                existing_events = [
                    event for event in self.events.values()
                    if (event.event_type == template.event_type and
                        season in event.tags and
                        event.start_date and
                        self._get_current_season(event.start_date) == season)
                ]

                if not existing_events:
                    # Create event from template
                    event_data = {
                        "name": f"{season.title()} {template.name}",
                        "description": template.description,
                        "type": template.event_type.value,
                        "frequency": "one_time",
                        "participation_types": [pt.value for pt in template.participation_types],
                        "objectives": [asdict(obj) for obj in template.objectives],
                        "rewards": [asdict(reward) for reward in template.rewards],
                        "rules": template.rules,
                        "tags": template.tags + [season, "auto_generated"],
                        "start_date": (current_date + timedelta(days=random.randint(1, 7))).isoformat(),
                        "end_date": (current_date + timedelta(days=random.randint(8, 14))).isoformat(),
                        "registration_start": current_date.isoformat(),
                        "max_participants": template.settings.get("max_participants", 100)
                    }

                    result = await self.create_event("system", event_data)
                    if result["success"]:
                        self.logger.info(f"Auto-generated seasonal event: {result['event_id']}")

        except Exception as e:
            self.logger.error(f"Error auto-generating seasonal events: {e}")

    # Helper methods

    async def _validate_event_creation(self, creator_id: str, event_data: Dict) -> Dict:
        """Validate event creation requirements"""
        try:
            # Check required fields
            if not event_data.get("name"):
                return {"valid": False, "error": "Event name is required"}

            if not event_data.get("type"):
                return {"valid": False, "error": "Event type is required"}

            # Validate event type
            try:
                EventType(event_data["type"])
            except ValueError:
                return {"valid": False, "error": "Invalid event type"}

            # Validate dates
            if event_data.get("start_date"):
                start_date = datetime.fromisoformat(event_data["start_date"])
                if start_date <= datetime.now():
                    return {"valid": False, "error": "Start date must be in the future"}

            if event_data.get("end_date") and event_data.get("start_date"):
                start_date = datetime.fromisoformat(event_data["start_date"])
                end_date = datetime.fromisoformat(event_data["end_date"])
                if end_date <= start_date:
                    return {"valid": False, "error": "End date must be after start date"}

            # Validate participant limits
            min_participants = event_data.get("min_participants", 1)
            max_participants = event_data.get("max_participants")
            if max_participants and min_participants > max_participants:
                return {"valid": False, "error": "Minimum participants cannot exceed maximum"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating event creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _validate_template_creation(self, creator_id: str, template_data: Dict) -> Dict:
        """Validate event template creation"""
        # Similar to event validation but more lenient
        return {"valid": True}  # Simplified

    async def _validate_schedule_creation(self, creator_id: str, schedule_data: Dict) -> Dict:
        """Validate recurring event schedule creation"""
        try:
            if not schedule_data.get("event_template_id"):
                return {"valid": False, "error": "Event template ID is required"}

            if not schedule_data.get("frequency"):
                return {"valid": False, "error": "Frequency is required"}

            if not schedule_data.get("schedule_pattern"):
                return {"valid": False, "error": "Schedule pattern is required"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating schedule creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _can_register_for_event(self, user_id: str, event: CommunityEvent) -> bool:
        """Check if user can register for event"""
        # Check registration window
        current_time = datetime.now()

        if event.registration_start and current_time < event.registration_start:
            return False

        if event.registration_end and current_time > event.registration_end:
            return False

        # Check if user meets requirements
        # This would integrate with your player system
        return True

    async def _can_start_event(self, event: CommunityEvent, initiator_id: str = None) -> bool:
        """Check if event can be started"""
        # Only creators, organizers, or system can start events
        if initiator_id and initiator_id not in [event.creator_id] + event.organizer_ids:
            return False

        # Check if enough participants
        current_participants = len([p for p in self.participations[event.id] if p.status == "registered"])
        if current_participants < event.min_participants:
            return False

        # Check if registration period is over
        if event.registration_end and datetime.now() < event.registration_end:
            return False

        return True

    async def _can_end_event(self, event: CommunityEvent, initiator_id: str = None) -> bool:
        """Check if event can be ended"""
        # Only creators, organizers, or system can end events
        if initiator_id and initiator_id not in [event.creator_id] + event.organizer_ids:
            return False

        # Event must be active
        if event.status != EventStatus.ACTIVE:
            return False

        return True

    async def _can_participate_in_event(self, user_id: str, event: CommunityEvent) -> bool:
        """Check if user can participate in event"""
        # Check if user meets level requirements, etc.
        return True  # Simplified

    async def _can_view_leaderboard(self, user_id: str, event: CommunityEvent) -> bool:
        """Check if user can view event leaderboard"""
        # Most leaderboards are public, but some might be restricted
        return True  # Simplified

    async def _update_leaderboard(self, event_id: str, user_id: str = None, score: float = 0):
        """Update event leaderboard"""
        if event_id not in self.leaderboards:
            return

        leaderboard = self.leaderboards[event_id]

        # Update specific user score if provided
        if user_id:
            await self._update_participant_score(leaderboard, user_id, score)
        else:
            # Recalculate entire leaderboard
            await self._recalculate_leaderboard(event_id)

        leaderboard.last_updated = datetime.now()

    async def _update_participant_score(self, leaderboard: EventLeaderboard, user_id: str, score: float):
        """Update individual participant score on leaderboard"""
        # Find existing entry
        for entry in leaderboard.entries:
            if entry["participant_id"] == user_id:
                entry["score"] = score
                break
        else:
            # Add new entry
            leaderboard.entries.append({
                "participant_id": user_id,
                "score": score,
                "rank": 0  # Will be calculated below
            })

        # Sort and update ranks
        leaderboard.entries.sort(key=lambda x: x["score"], reverse=True)
        for i, entry in enumerate(leaderboard.entries):
            entry["rank"] = i + 1

        # Limit entries
        if len(leaderboard.entries) > leaderboard.max_entries:
            leaderboard.entries = leaderboard.entries[:leaderboard.max_entries]

    async def _recalculate_leaderboard(self, event_id: str):
        """Recalculate entire leaderboard from participations"""
        if event_id not in self.participations:
            return

        leaderboard = self.leaderboards[event_id]
        scores = {}

        # Calculate scores from all participations
        for participation in self.participations[event_id]:
            if participation.status == "active":
                scores[participation.participant_id] = participation.score

        # Create sorted entries
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        leaderboard.entries = [
            {
                "participant_id": participant_id,
                "score": score,
                "rank": i + 1
            }
            for i, (participant_id, score) in enumerate(sorted_scores)
        ]

        # Limit entries
        if len(leaderboard.entries) > leaderboard.max_entries:
            leaderboard.entries = leaderboard.entries[:leaderboard.max_entries]

    async def _calculate_event_results(self, event_id: str) -> Dict:
        """Calculate final event results"""
        participations = self.participations.get(event_id, [])

        results = {
            "total_participants": len(participations),
            "completed_participants": len([p for p in participations if p.status == "active"]),
            "average_score": 0.0,
            "top_scores": [],
            "objectives_completion": {}
        }

        if participations:
            total_score = sum(p.score for p in participations)
            results["average_score"] = total_score / len(participations)

            # Top scores
            sorted_participations = sorted(participations, key=lambda x: x.score, reverse=True)
            results["top_scores"] = [
                {
                    "participant_id": p.participant_id,
                    "score": p.score,
                    "objectives_completed": len(p.objectives_completed)
                }
                for p in sorted_participations[:10]
            ]

        return results

    async def _distribute_event_rewards(self, event_id: str):
        """Distribute rewards to event participants"""
        event = self.events[event_id]
        participations = self.participations.get(event_id, [])

        for participation in participations:
            if participation.status != "active":
                continue

            # Check participation rewards
            for reward in event.rewards:
                if await self._meets_reward_requirement(participation, reward):
                    await self._award_reward_to_participant(participation.participant_id, reward)

    async def _meets_reward_requirement(self, participation: EventParticipation, reward: EventReward) -> bool:
        """Check if participant meets reward requirements"""
        if reward.requirement_type == "participation":
            return True
        elif reward.requirement_type == "completion":
            return len(participation.objectives_completed) > 0
        elif reward.requirement_type == "rank":
            return participation.rank and participation.rank <= reward.requirement_value
        elif reward.requirement_type == "points":
            return participation.score >= reward.requirement_value
        elif reward.requirement_type == "objective":
            return reward.requirement_value in participation.objectives_completed

        return False

    async def _award_reward_to_participant(self, participant_id: str, reward: EventReward):
        """Award reward to participant"""
        # This would integrate with your reward system
        self.logger.info(f"Awarded reward {reward.id} to participant {participant_id}")

    async def _award_objective_rewards(self, participant_id: str, rewards: Dict):
        """Award objective completion rewards"""
        # This would integrate with your reward system
        pass

    async def _generate_event_report(self, event_id: str):
        """Generate event completion report"""
        event = self.events[event_id]
        results = await self._calculate_event_results(event_id)

        report = {
            "event_id": event_id,
            "event_name": event.name,
            "event_type": event.event_type.value,
            "completion_date": event.end_date.isoformat() if event.end_date else None,
            "duration_hours": (event.end_date - event.start_date).total_seconds() / 3600 if event.start_date and event.end_date else 0,
            "results": results
        }

        # Store report (would go to database in production)
        self.logger.info(f"Event report generated for {event_id}: {report}")

    async def _update_participant_stats(self, event_id: str):
        """Update statistics for event participants"""
        participations = self.participations.get(event_id, [])

        for participation in participations:
            if participation.participant_id not in self.participant_stats:
                self.participant_stats[participation.participant_id] = {
                    "events_participated": 0,
                    "events_completed": 0,
                    "total_score": 0.0,
                    "average_score": 0.0,
                    "best_rank": None
                }

            stats = self.participant_stats[participation.participant_id]
            stats["events_participated"] += 1
            stats["total_score"] += participation.score

            if participation.status == "active":
                stats["events_completed"] += 1

            if participation.rank and (stats["best_rank"] is None or participation.rank < stats["best_rank"]):
                stats["best_rank"] = participation.rank

            # Calculate average score
            total_events = stats["events_participated"]
            if total_events > 0:
                stats["average_score"] = stats["total_score"] / total_events

    async def _calculate_next_occurrence(self, schedule_data: Dict) -> datetime:
        """Calculate next occurrence for recurring event"""
        # Simplified calculation - would use proper cron parsing in production
        base_date = datetime.now()
        frequency = schedule_data["frequency"]

        if frequency == "daily":
            return base_date + timedelta(days=1)
        elif frequency == "weekly":
            return base_date + timedelta(weeks=1)
        elif frequency == "monthly":
            return base_date + timedelta(days=30)
        elif frequency == "yearly":
            return base_date + timedelta(days=365)
        else:
            return base_date + timedelta(days=1)

    def _get_current_season(self, date: datetime) -> str:
        """Get current season based on date"""
        month = date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    async def _calculate_event_progress(self, event_id: str) -> float:
        """Calculate event progress percentage"""
        if event_id not in self.events:
            return 0.0

        event = self.events[event_id]
        if not event.start_date or not event.end_date:
            return 0.0

        current_time = datetime.now()
        total_duration = (event.end_date - event.start_date).total_seconds()
        elapsed = (current_time - event.start_date).total_seconds()

        if elapsed <= 0:
            return 0.0
        elif elapsed >= total_duration:
            return 100.0
        else:
            return (elapsed / total_duration) * 100

    async def _schedule_event_status_updates(self, event_id: str):
        """Schedule automatic status updates for event"""
        # This would set up timers for status changes
        pass

    async def _send_event_notification(self, event_id: str, notification_type: str, message: str):
        """Send notification to event participants"""
        # This would integrate with your notification system
        self.logger.info(f"Event notification for {event_id}: {message}")

    # Background task methods

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Schedule check task
        self._background_tasks.append(
            asyncio.create_task(self._schedule_check_task())
        )

        # Leaderboard update task
        self._background_tasks.append(
            asyncio.create_task(self._leaderboard_update_task())
        )

        # Auto-generate seasonal events
        self._background_tasks.append(
            asyncio.create_task(self._seasonal_event_generation_task())
        )

        # Event status management
        self._background_tasks.append(
            asyncio.create_task(self._event_status_management_task())
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

    async def _schedule_check_task(self):
        """Check and create scheduled events"""
        while self._running:
            try:
                current_time = datetime.now()

                for schedule in list(self.schedules.values()):
                    if not schedule.active:
                        continue

                    # Check if it's time to create the event
                    if current_time >= schedule.next_occurrence:
                        # Create event from template
                        if schedule.event_template_id in self.event_templates:
                            template = self.event_templates[schedule.event_template_id]
                            event_data = {
                                "name": template.name,
                                "description": template.description,
                                "type": template.event_type.value,
                                "frequency": "one_time",
                                "participation_types": [pt.value for pt in template.participation_types],
                                "objectives": [asdict(obj) for obj in template.objectives],
                                "rewards": [asdict(reward) for reward in template.rewards],
                                "rules": template.rules,
                                "tags": template.tags,
                                "start_date": schedule.next_occurrence.isoformat(),
                                "end_date": (schedule.next_occurrence + timedelta(hours=2)).isoformat()
                            }

                            result = await self.create_event("system", event_data)
                            if result["success"]:
                                self.logger.info(f"Created scheduled event: {result['event_id']}")

                        # Update schedule
                        schedule.occurrences_created += 1
                        schedule.next_occurrence = await self._calculate_next_occurrence({
                            "frequency": schedule.frequency.value,
                            "schedule_pattern": schedule.schedule_pattern
                        })

                        # Check max occurrences
                        if schedule.max_occurrences and schedule.occurrences_created >= schedule.max_occurrences:
                            schedule.active = False

                await asyncio.sleep(self.config["schedule_check_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in schedule check task: {e}")
                await asyncio.sleep(60)

    async def _leaderboard_update_task(self):
        """Update event leaderboards"""
        while self._running:
            try:
                for event_id, leaderboard in self.leaderboards.items():
                    if leaderboard.auto_update and event_id in self.active_events:
                        await self._recalculate_leaderboard(event_id)

                await asyncio.sleep(self.config["leaderboard_update_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in leaderboard update task: {e}")
                await asyncio.sleep(60)

    async def _seasonal_event_generation_task(self):
        """Auto-generate seasonal events"""
        while self._running:
            try:
                if self.config["auto_generate_events"]:
                    await self.auto_generate_seasonal_events()

                # Run daily check
                await asyncio.sleep(86400)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in seasonal event generation task: {e}")
                await asyncio.sleep(3600)

    async def _event_status_management_task(self):
        """Manage automatic event status changes"""
        while self._running:
            try:
                current_time = datetime.now()

                for event in self.events.values():
                    # Check registration opening
                    if (event.status == EventStatus.PLANNED and
                        event.registration_start and
                        current_time >= event.registration_start):
                        event.status = EventStatus.REGISTRATION_OPEN
                        self.upcoming_events.add(event.id)
                        await self._send_event_notification(
                            event.id, "registration_open", f"Registration for '{event.name}' is now open!"
                        )

                    # Check registration closing
                    elif (event.status == EventStatus.REGISTRATION_OPEN and
                          event.registration_end and
                          current_time >= event.registration_end):
                        event.status = EventStatus.PREPARING

                    # Check event start
                    elif (event.status in [EventStatus.ANNOUNCED, EventStatus.PREPARING] and
                          event.start_date and
                          current_time >= event.start_date):
                        await self.start_event(event.id)

                    # Check event end
                    elif (event.status == EventStatus.ACTIVE and
                          event.end_date and
                          current_time >= event.end_date):
                        await self.end_event(event.id)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in event status management task: {e}")
                await asyncio.sleep(300)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize community event manager
        event_manager = CommunityEventManager()

        # Start background tasks
        await event_manager.start_background_tasks()

        # Create an event template
        template = await event_manager.create_event_template("admin", {
            "name": "Dragon Hunt Tournament",
            "description": "Competitive tournament to hunt the most dragons",
            "type": "tournament",
            "frequency": "one_time",
            "participation_types": ["individual", "team"],
            "objectives": [
                {
                    "title": "Hunt Dragons",
                    "type": "kill",
                    "required_amount": 10,
                    "points_value": 100,
                    "difficulty": "hard"
                },
                {
                    "title": "Collect Dragon Scales",
                    "type": "collect",
                    "required_amount": 50,
                    "points_value": 50,
                    "difficulty": "normal"
                }
            ],
            "rewards": [
                {
                    "type": "items",
                    "value": {"item_id": "dragon_slayer_sword", "quantity": 1},
                    "description": "Dragon Slayer Sword",
                    "requirement_type": "rank",
                    "requirement_value": 1
                }
            ],
            "rules": ["No cheating", "Respect other participants"],
            "tags": ["tournament", "combat", "dragons"]
        })
        print(f"Event template created: {template['template_id']}")

        # Create an event from the template
        event = await event_manager.create_event("admin", {
            "name": "Weekend Dragon Hunt",
            "description": "Weekend tournament for dragon hunters",
            "type": "tournament",
            "frequency": "one_time",
            "start_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=2, hours=4)).isoformat(),
            "registration_start": datetime.now().isoformat(),
            "registration_end": (datetime.now() + timedelta(days=1, hours=23)).isoformat(),
            "max_participants": 100,
            "participation_types": ["individual"],
            "objectives": [
                {
                    "title": "Defeat Dragons",
                    "type": "kill",
                    "required_amount": 5,
                    "points_value": 50
                }
            ],
            "rewards": [
                {
                    "type": "experience",
                    "value": 1000,
                    "description": "Participation experience",
                    "requirement_type": "participation"
                }
            ],
            "tags": ["weekend", "tournament", "combat"]
        })
        print(f"Event created: {event['event_id']}")

        if event["success"]:
            event_id = event["event_id"]

            # Register participants
            await event_manager.register_for_event("player1", event_id, ParticipationType.INDIVIDUAL)
            await event_manager.register_for_event("player2", event_id, ParticipationType.INDIVIDUAL)
            await event_manager.register_for_event("player3", event_id, ParticipationType.INDIVIDUAL)

            # Start the event
            await event_manager.start_event(event_id)

            # Complete some objectives
            await event_manager.complete_objective("player1", event_id,
                event_manager.events[event_id].objectives[0].id, 3)
            await event_manager.complete_objective("player2", event_id,
                event_manager.events[event_id].objectives[0].id, 5)

            # Get event info
            info = await event_manager.get_event_info(event_id, "player1")
            print(f"Event progress: {info['event'].get('progress_percentage', 0):.1f}%")

            # Get leaderboard
            leaderboard = await event_manager.get_event_leaderboard(event_id)
            print(f"Leaderboard entries: {leaderboard['total_entries']}")

            # End the event
            await event_manager.end_event(event_id)

        # Get upcoming events
        upcoming = await event_manager.get_upcoming_events("player1")
        print(f"Upcoming events: {upcoming['total_count']}")

        # Get active events
        active = await event_manager.get_active_events("player1")
        print(f"Active events: {active['total_count']}")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await event_manager.stop_background_tasks()

    asyncio.run(main())