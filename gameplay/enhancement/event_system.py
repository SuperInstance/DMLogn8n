#!/usr/bin/env python3
"""
Dynamic World Event System for DMLogn8n
Provides engaging community activities and dynamic world changes
"""

import json
import math
import random
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

class EventType(Enum):
    WORLD_BOSS = "world_boss"
    INVASION = "invasion"
    FESTIVAL = "festival"
    DISASTER = "disaster"
    DISCOVERY = "discovery"
    MERCHANT_ARRIVAL = "merchant_arrival"
    TOURNAMENT = "tournament"
    DUNGEON_RIFT = "dungeon_rift"
    CELESTIAL_EVENT = "celestial_event"
    COMMUNITY_BUILD = "community_build"
    MYSTERY_QUEST = "mystery_quest"
    SEASON_CHANGE = "season_change"

class EventStatus(Enum):
    ANNOUNCED = "announced"
    PREPARING = "preparing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EventRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class ParticipationType(Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    GUILD = "guild"
    SERVER_WIDE = "server_wide"

class ImpactType(Enum):
    TEMPORARY = "temporary"  # Lasts for event duration
    SHORT_TERM = "short_term"  # Hours to days
    LONG_TERM = "long_term"  # Days to weeks
    PERMANENT = "permanent"  # Permanent world change

@dataclass
class EventReward:
    """Reward for event participation"""
    type: str  # experience, gold, items, titles, cosmetics
    value: Any
    rarity: str = "common"
    participation_requirement: float = 0.1  # Minimum participation percentage
    individual: bool = True
    distributed: bool = False

@dataclass
class EventObjective:
    """Objective for world events"""
    id: str
    description: str
    type: str  # defeat, collect, explore, protect, achieve
    target: str
    required_quantity: int = 1
    current_progress: int = 0
    contribution_tracking: bool = True
    rewards: List[EventReward] = field(default_factory=list)

@dataclass
class WorldEvent:
    """Dynamic world event definition"""
    id: str
    name: str
    description: str
    event_type: EventType
    rarity: EventRarity
    duration: int  # seconds
    preparation_time: int = 300  # seconds
    min_participants: int = 1
    max_participants: Optional[int] = None
    participation_type: ParticipationType = ParticipationType.SERVER_WIDE
    objectives: List[EventObjective] = field(default_factory=list)
    rewards: List[EventReward] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    world_impacts: List[Dict[str, Any]] = field(default_factory=list)
    repeatable: bool = False
    cooldown_period: int = 0  # seconds
    location_requirements: List[str] = field(default_factory=list)
    schedule_constraints: Dict[str, Any] = field(default_factory=dict)
    auto_start: bool = False

@dataclass
class EventInstance:
    """Active instance of a world event"""
    event_id: str
    instance_id: str
    status: EventStatus = EventStatus.ANNOUNCED
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    participants: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    objectives_progress: Dict[str, int] = field(default_factory=dict)
    world_state_changes: Dict[str, Any] = field(default_factory=dict)
    participation_data: Dict[str, float] = field(default_factory=dict)
    rewards_distributed: bool = False
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EventSchedule:
    """Scheduled event configuration"""
    event_id: str
    schedule_pattern: str  # daily, weekly, monthly, custom
    schedule_times: List[str]  # Times in HH:MM format
    days_of_week: Optional[List[int]] = None  # 0-6 (Sunday-Saturday)
    date_specific: Optional[List[str]] = None  # YYYY-MM-DD format
    seasonal_requirement: Optional[str] = None
    player_count_threshold: Optional[int] = None
    enabled: bool = True

class EventSystem:
    """Dynamic world event management system"""

    def __init__(self):
        self.events: Dict[str, WorldEvent] = {}
        self.event_instances: Dict[str, EventInstance] = {}
        self.active_events: Dict[str, EventInstance] = {}
        self.event_history: List[Dict] = []
        self.event_schedule: Dict[str, EventSchedule] = {}
        self.world_state: Dict[str, Any] = {}
        self.player_participation: Dict[str, List[str]] = defaultdict(list)
        self.event_generators: Dict[EventType, Callable] = {}
        self.running = False
        self.analytics = EventAnalytics()

        # Event system parameters
        self.max_concurrent_events = 3
        self.participation_decay_rate = 0.1  # Per hour
        self.event_success_threshold = 0.7  # 70% of objectives required for success
        self.reward_scaling_factor = 1.2
        self.community_bonus_threshold = 0.5  # 50% participation triggers community bonus

        self._initialize_default_events()
        self._initialize_event_generators()

    def _initialize_default_events(self):
        """Initialize default world events"""
        events = [
            WorldEvent(
                id="dragon_attack",
                name="Dragon Attack",
                description="A mighty dragon attacks the town!",
                event_type=EventType.WORLD_BOSS,
                rarity=EventRarity.RARE,
                duration=3600,  # 1 hour
                preparation_time=600,  # 10 minutes
                min_participants=10,
                max_participants=50,
                objectives=[
                    EventObjective(
                        id="defeat_dragon",
                        description="Defeat the dragon before it destroys the town",
                        type="defeat",
                        target="ancient_dragon",
                        required_quantity=1,
                        rewards=[
                            EventReward("experience", 5000, "epic"),
                            EventReward("items", ["dragon_scale", "gold_coin"], "rare")
                        ]
                    ),
                    EventObjective(
                        id="protect_civilians",
                        description="Protect the townspeople from dragon attacks",
                        type="protect",
                        target="civilian",
                        required_quantity=50,
                        current_progress=50,  # Start with all safe
                        rewards=[
                            EventReward("reputation", {"town": 100}, "uncommon")
                        ]
                    )
                ],
                rewards=[
                    EventReward("titles", "Dragon Slayer", "legendary", 0.3),
                    EventReward("experience", 2000, "rare"),
                    EventReward("gold", 1000, "uncommon")
                ],
                world_impacts=[
                    {"type": ImpactType.SHORT_TERM, "effect": "dragon_fear", "duration": 86400},
                    {"type": ImpactType.LONG_TERM, "effect": "town_gratitude", "duration": 604800}
                ],
                cooldown_period=604800,  # 1 week
                location_requirements=["town_center", "mountain_pass"]
            ),
            WorldEvent(
                id="harvest_festival",
                name="Harvest Festival",
                description="Annual celebration of the bountiful harvest",
                event_type=EventType.FESTIVAL,
                rarity=EventRarity.COMMON,
                duration=7200,  # 2 hours
                preparation_time=1800,  # 30 minutes
                min_participants=5,
                participation_type=ParticipationType.SERVER_WIDE,
                objectives=[
                    EventObjective(
                        id="collect_harvest",
                        description="Collect harvest crops for the festival",
                        type="collect",
                        target="harvest_crop",
                        required_quantity=500,
                        rewards=[
                            EventReward("experience", 500, "common"),
                            EventReward("items", ["festival_token"], "common")
                        ]
                    ),
                    EventObjective(
                        id="festival_games",
                        description="Participate in festival games",
                        type="achieve",
                        target="game_win",
                        required_quantity=100,
                        rewards=[
                            EventReward("social_xp", 200, "common")
                        ]
                    )
                ],
                rewards=[
                    EventReward("cosmetics", ["harvest_crown", "festival_outfit"], "uncommon"),
                    EventReward("experience", 1000, "common"),
                    EventReward("reputation", {"farmers": 50}, "common")
                ],
                repeatable=True,
                cooldown_period=1209600,  # 2 weeks
                schedule_constraints={"season": "autumn"}
            ),
            WorldEvent(
                id="mysterious_rift",
                name="Mysterious Rift",
                description="A strange dimensional rift has opened",
                event_type=EventType.DUNGEON_RIFT,
                rarity=EventRarity.EPIC,
                duration=1800,  # 30 minutes
                preparation_time=300,  # 5 minutes
                min_participants=5,
                max_participants=20,
                objectives=[
                    EventObjective(
                        id="seal_rift",
                        description="Seal the rift before it expands",
                        type="achieve",
                        target="ritual_complete",
                        required_quantity=1,
                        rewards=[
                            EventReward("experience", 3000, "epic"),
                            EventReward("items", ["rift_shard", "essence_chaos"], "rare")
                        ]
                    )
                ],
                rewards=[
                    EventReward("titles", "Rift Sealer", "epic", 0.2),
                    EventReward("experience", 1500, "rare"),
                    EventReward("permanent_stats", {"magic_power": 5}, "rare")
                ],
                world_impacts=[
                    {"type": ImpactType.TEMPORARY, "effect": "chaotic_energy", "duration": 1800},
                    {"type": ImpactType.SHORT_TERM, "effect": "rift_aftermath", "duration": 3600}
                ]
            )
        ]

        for event in events:
            self.events[event.id] = event

    def _initialize_event_generators(self):
        """Initialize dynamic event generators"""
        self.event_generators = {
            EventType.INVASION: self.generate_invasion_event,
            EventType.MERCHANT_ARRIVAL: self.generate_merchant_event,
            EventType.DISCOVERY: self.generate_discovery_event,
            EventType.COMMUNITY_BUILD: self.generate_community_event
        }

    def start_event_system(self):
        """Start the event system background processing"""
        if self.running:
            return

        self.running = True
        # In a real implementation, this would start background tasks
        # For now, we'll just mark it as running
        self.analytics.record_system_start()

    def stop_event_system(self):
        """Stop the event system"""
        self.running = False
        # Complete all active events
        for instance_id in list(self.active_events.keys()):
            self.complete_event(instance_id, force=True)

        self.analytics.record_system_stop()

    def schedule_event(self, event_id: str, schedule_config: EventSchedule) -> bool:
        """Schedule an event to run automatically"""
        if event_id not in self.events:
            return False

        self.event_schedule[event_id] = schedule_config
        return True

    def announce_event(self, event_id: str, delay: int = 0) -> Optional[str]:
        """Announce and prepare a world event"""
        if event_id not in self.events:
            return None

        # Check if event can be started
        if not self.can_start_event(event_id):
            return None

        event = self.events[event_id]
        instance_id = f"{event_id}_{int(time.time())}_{random.randint(1000, 9999)}"

        # Create event instance
        instance = EventInstance(
            event_id=event_id,
            instance_id=instance_id,
            status=EventStatus.ANNOUNCED,
            start_time=time.time() + delay + event.preparation_time,
            end_time=time.time() + delay + event.preparation_time + event.duration
        )

        # Initialize objectives progress
        for objective in event.objectives:
            instance.objectives_progress[objective.id] = objective.current_progress

        self.event_instances[instance_id] = instance

        # Start preparation timer (would be async in real implementation)
        if delay == 0:
            self.start_event_instance(instance_id)

        return instance_id

    def can_start_event(self, event_id: str) -> bool:
        """Check if event can be started"""
        if event_id not in self.events:
            return False

        event = self.events[event_id]

        # Check cooldown
        if self.is_event_on_cooldown(event_id):
            return False

        # Check concurrent event limit
        if len(self.active_events) >= self.max_concurrent_events:
            return False

        # Check player count threshold
        if event.requirements.get("min_players_online", 0) > self.get_online_player_count():
            return False

        # Check schedule constraints
        if not self.meets_schedule_constraints(event):
            return False

        return True

    def is_event_on_cooldown(self, event_id: str) -> bool:
        """Check if event is on cooldown"""
        if event_id not in self.events:
            return True

        event = self.events[event_id]
        if event.cooldown_period == 0:
            return False

        # Check recent event history
        current_time = time.time()
        for history_event in self.event_history:
            if (history_event["event_id"] == event_id and
                current_time - history_event["end_time"] < event.cooldown_period):
                return True

        return False

    def meets_schedule_constraints(self, event: WorldEvent) -> bool:
        """Check if event meets schedule constraints"""
        constraints = event.schedule_constraints

        # Check time of day
        if "time_range" in constraints:
            current_hour = time.localtime().tm_hour
            start_hour, end_hour = constraints["time_range"]
            if not (start_hour <= current_hour <= end_hour):
                return False

        # Check season
        if "season" in constraints:
            current_season = self.get_current_season()
            if current_season != constraints["season"]:
                return False

        # Check day of week
        if "days_of_week" in constraints:
            current_day = time.localtime().tm_wday
            if current_day not in constraints["days_of_week"]:
                return False

        return True

    def start_event_instance(self, instance_id: str):
        """Start an event instance"""
        if instance_id not in self.event_instances:
            return

        instance = self.event_instances[instance_id]
        event = self.events[instance.event_id]

        instance.status = EventStatus.ACTIVE
        instance.start_time = time.time()
        self.active_events[instance_id] = instance

        # Apply world impacts
        self.apply_world_impacts(event, ImpactType.TEMPORARY)

        # Generate dynamic content if needed
        if event.event_type in self.event_generators:
            self.event_generators[event.event_type](instance)

        self.analytics.record_event_start(instance_id, instance.event_id)

    def join_event(self, player_id: str, instance_id: str) -> Tuple[bool, str]:
        """Player joins an event"""
        if instance_id not in self.active_events:
            return False, "Event not found or not active"

        instance = self.active_events[instance_id]
        event = self.events[instance.event_id]

        # Check participation limits
        if event.max_participants and len(instance.participants) >= event.max_participants:
            return False, "Event is full"

        # Check requirements
        if not self.meets_event_requirements(player_id, event):
            return False, "Does not meet event requirements"

        # Add participant
        instance.participants[player_id] = {
            "join_time": time.time(),
            "contribution": 0,
            "objectives_completed": [],
            "participation_score": 0.0
        }

        self.player_participation[player_id].append(instance_id)

        self.analytics.record_event_join(player_id, instance_id)
        return True, f"Joined {event.name}"

    def meets_event_requirements(self, player_id: str, event: WorldEvent) -> bool:
        """Check if player meets event requirements"""
        # This would integrate with other game systems
        # For now, return True as placeholder
        return True

    def contribute_to_event(self, player_id: str, instance_id: str, objective_id: str, contribution: int) -> Tuple[bool, str]:
        """Player contributes to event objective"""
        if instance_id not in self.active_events:
            return False, "Event not active"

        instance = self.active_events[instance_id]

        if player_id not in instance.participants:
            return False, "Not participating in event"

        if objective_id not in instance.objectives_progress:
            return False, "Invalid objective"

        # Update progress
        old_progress = instance.objectives_progress[objective_id]
        instance.objectives_progress[objective_id] += contribution
        instance.participants[player_id]["contribution"] += contribution

        # Update participant score
        self.update_participation_score(instance, player_id)

        self.analytics.record_event_contribution(player_id, instance_id, objective_id, contribution)

        return True, f"Contributed {contribution} to objective"

    def update_participation_score(self, instance: EventInstance, player_id: str):
        """Update player's participation score"""
        participant = instance.participants[player_id]
        total_contribution = participant["contribution"]
        time_participated = time.time() - participant["join_time"]

        # Calculate participation score based on contribution and time
        base_score = total_contribution / 100  # Normalize
        time_bonus = min(time_participated / 3600, 1.0) * 0.5  # Up to 50% bonus for time

        participant["participation_score"] = base_score + time_bonus

    def complete_event(self, instance_id: str, force: bool = False) -> Tuple[bool, str]:
        """Complete an event instance"""
        if instance_id not in self.active_events and not force:
            return False, "Event not active"

        instance = self.event_instances.get(instance_id)
        if not instance:
            return False, "Event instance not found"

        event = self.events[instance.event_id]
        instance.status = EventStatus.COMPLETED
        instance.end_time = time.time()

        # Calculate success
        success = self.calculate_event_success(instance)
        total_participants = len(instance.participants)

        # Calculate community participation rate
        max_possible_participants = event.max_participants or self.get_server_player_count()
        participation_rate = total_participants / max_possible_participants

        # Apply world impacts
        if success:
            for impact in event.world_impacts:
                if impact["type"] != ImpactType.TEMPORARY:
                    self.apply_world_impacts(event, impact["type"])

        # Distribute rewards
        self.distribute_event_rewards(instance, success, participation_rate)

        # Move to history
        self.active_events.pop(instance_id, None)
        self.event_history.append({
            "instance_id": instance_id,
            "event_id": instance.event_id,
            "start_time": instance.start_time,
            "end_time": instance.end_time,
            "success": success,
            "participants": total_participants,
            "participation_rate": participation_rate
        })

        # Apply cooldown
        if event.cooldown_period > 0:
            self.set_event_cooldown(instance.event_id, event.cooldown_period)

        self.analytics.record_event_complete(instance_id, success, total_participants, participation_rate)

        return True, f"Event {event.name} completed {'successfully' if success else 'unsuccessfully'}"

    def calculate_event_success(self, instance: EventInstance) -> bool:
        """Calculate if event was successful"""
        event = self.events[instance.event_id]
        objectives_completed = 0
        total_objectives = len(event.objectives)

        for objective in event.objectives:
            if instance.objectives_progress.get(objective.id, 0) >= objective.required_quantity:
                objectives_completed += 1

        success_rate = objectives_completed / total_objectives if total_objectives > 0 else 0
        return success_rate >= self.event_success_threshold

    def distribute_event_rewards(self, instance: EventInstance, success: bool, participation_rate: float):
        """Distribute rewards to participants"""
        event = self.events[instance.event_id]

        if instance.rewards_distributed:
            return

        # Sort participants by contribution
        sorted_participants = sorted(
            instance.participants.items(),
            key=lambda x: x[1]["participation_score"],
            reverse=True
        )

        for player_id, participant_data in sorted_participants:
            participation_score = participant_data["participation_score"]

            # Calculate reward multiplier
            base_multiplier = participation_score
            if success:
                base_multiplier *= 1.5  # Success bonus
            if participation_rate > self.community_bonus_threshold:
                base_multiplier *= 1.2  # Community bonus

            # Distribute rewards
            for reward in event.rewards:
                if participation_score >= reward.participation_requirement:
                    self.grant_event_reward(player_id, reward, base_multiplier)

            # Distribute objective-specific rewards
            for objective in event.objectives:
                if objective.id in participant_data["objectives_completed"]:
                    for reward in objective.rewards:
                        self.grant_event_reward(player_id, reward, base_multiplier)

        instance.rewards_distributed = True

    def grant_event_reward(self, player_id: str, reward: EventReward, multiplier: float):
        """Grant reward to player"""
        # This would integrate with other game systems
        # For now, just record the reward
        self.analytics.record_reward_grant(player_id, reward.type, reward.value, multiplier)

    def apply_world_impacts(self, event: WorldEvent, impact_type: ImpactType):
        """Apply world impacts from event"""
        for impact in event.world_impacts:
            if impact["type"] == impact_type:
                effect_name = impact["effect"]
                duration = impact.get("duration", 0)

                # Apply effect to world state
                self.world_state[effect_name] = {
                    "source_event": event.id,
                    "start_time": time.time(),
                    "duration": duration,
                    "active": True
                }

    def generate_dynamic_event(self, event_type: EventType) -> Optional[str]:
        """Generate a dynamic event"""
        if event_type not in self.event_generators:
            return None

        # Create dynamic event
        event_id = f"dynamic_{event_type.value}_{int(time.time())}"
        dynamic_event = self.event_generators[event_type](None)  # None creates template

        if dynamic_event:
            self.events[event_id] = dynamic_event
            return self.announce_event(event_id)

        return None

    def generate_invasion_event(self, template_data: Any = None) -> WorldEvent:
        """Generate invasion event"""
        enemy_types = ["goblins", "bandits", "undead", "demons", "aliens"]
        enemy_type = random.choice(enemy_types)

        return WorldEvent(
            id=f"invasion_{enemy_type}_{int(time.time())}",
            name=f"{enemy_type.title()} Invasion",
            description=f"A massive {enemy_type} force is invading!",
            event_type=EventType.INVASION,
            rarity=EventRarity.UNCOMMON,
            duration=1800,  # 30 minutes
            preparation_time=300,  # 5 minutes
            min_participants=5,
            objectives=[
                EventObjective(
                    id="defend_town",
                    description=f"Defend the town from {enemy_type}",
                    type="defeat",
                    target=f"{enemy_type}_warrior",
                    required_quantity=random.randint(20, 50)
                )
            ],
            rewards=[
                EventReward("experience", 1000, "uncommon"),
                EventReward("reputation", {"town": 30}, "common")
            ]
        )

    def generate_merchant_event(self, template_data: Any = None) -> WorldEvent:
        """Generate merchant arrival event"""
        merchant_types = ["rare_goods", "black_market", "magical_artifacts", "exotic_spices"]
        merchant_type = random.choice(merchant_types)

        return WorldEvent(
            id=f"merchant_{merchant_type}_{int(time.time())}",
            name=f"Special Merchant: {merchant_type.replace('_', ' ').title()}",
            description="A special merchant has arrived with rare goods!",
            event_type=EventType.MERCHANT_ARRIVAL,
            rarity=EventRarity.COMMON,
            duration=3600,  # 1 hour
            preparation_time=600,  # 10 minutes
            min_participants=1,
            objectives=[
                EventObjective(
                    id="visit_merchant",
                    description="Visit the special merchant",
                    type="achieve",
                    target="merchant_visit",
                    required_quantity=1
                )
            ],
            rewards=[
                EventReward("items", [f"special_item_{merchant_type}"], "uncommon")
            ]
        )

    def generate_discovery_event(self, template_data: Any = None) -> WorldEvent:
        """Generate discovery event"""
        discovery_types = ["ancient_ruins", "hidden_cave", "mysterious_shrine", "lost_library"]
        discovery_type = random.choice(discovery_types)

        return WorldEvent(
            id=f"discovery_{discovery_type}_{int(time.time())}",
            name=f"Discovery: {discovery_type.replace('_', ' ').title()}",
            description=f"Players have discovered {discovery_type.replace('_', ' ')}!",
            event_type=EventType.DISCOVERY,
            rarity=EventRarity.RARE,
            duration=7200,  # 2 hours
            preparation_time=900,  # 15 minutes
            min_participants=3,
            objectives=[
                EventObjective(
                    id="explore_discovery",
                    description=f"Explore the {discovery_type.replace('_', ' ')}",
                    type="explore",
                    target=discovery_type,
                    required_quantity=1
                )
            ],
            rewards=[
                EventReward("experience", 1500, "rare"),
                EventReward("reputation", {"explorers": 50}, "uncommon"),
                EventReward("titles", f"Explorer of {discovery_type.replace('_', ' ').title()}", "rare", 0.1)
            ]
        )

    def generate_community_event(self, template_data: Any = None) -> WorldEvent:
        """Generate community building event"""
        project_types = ["town_wall", "fountain", "park", "library", "hospital"]
        project_type = random.choice(project_types)

        return WorldEvent(
            id=f"community_{project_type}_{int(time.time())}",
            name=f"Community Project: {project_type.replace('_', ' ').title()}",
            description=f"Help build a {project_type.replace('_', ' ')} for the community!",
            event_type=EventType.COMMUNITY_BUILD,
            rarity=EventRarity.UNCOMMON,
            duration=86400,  # 24 hours
            preparation_time=1800,  # 30 minutes
            min_participants=5,
            objectives=[
                EventObjective(
                    id="gather_materials",
                    description=f"Gather materials for {project_type}",
                    type="collect",
                    target="building_material",
                    required_quantity=random.randint(100, 300)
                ),
                EventObjective(
                    id="construction_work",
                    description=f"Help with {project_type} construction",
                    type="achieve",
                    target="construction_progress",
                    required_quantity=100
                )
            ],
            rewards=[
                EventReward("experience", 800, "uncommon"),
                EventReward("reputation", {"town": 40}, "common"),
                EventReward("cosmetics", [f"community_builder_badge"], "uncommon")
            ],
            world_impacts=[
                {"type": ImpactType.PERMANENT, "effect": f"{project_type}_built", "duration": 0}
            ]
        )

    # Placeholder methods for integration
    def get_online_player_count(self) -> int:
        """Get current online player count (placeholder)"""
        return 50

    def get_server_player_count(self) -> int:
        """Get total server player count (placeholder)"""
        return 100

    def get_current_season(self) -> str:
        """Get current season (placeholder)"""
        return "spring"

    def set_event_cooldown(self, event_id: str, duration: int):
        """Set event cooldown (placeholder)"""
        pass

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get list of active events"""
        active_events = []
        for instance_id, instance in self.active_events.items():
            event = self.events[instance.event_id]
            active_events.append({
                "instance_id": instance_id,
                "event_id": instance.event_id,
                "name": event.name,
                "description": event.description,
                "type": event.event_type.value,
                "participants": len(instance.participants),
                "time_remaining": max(0, (instance.end_time or 0) - time.time()),
                "objectives": [
                    {
                        "id": obj.id,
                        "description": obj.description,
                        "progress": instance.objectives_progress.get(obj.id, 0),
                        "required": obj.required_quantity
                    }
                    for obj in event.objectives
                ]
            })
        return active_events

class EventAnalytics:
    """Analytics for event system performance and engagement"""

    def __init__(self):
        self.event_stats = defaultdict(lambda: {
            "times_started": 0,
            "times_completed": 0,
            "success_rate": 0,
            "total_participants": 0,
            "average_participation": 0,
            "participation_rates": []
        })
        self.player_engagement = defaultdict(list)
        self.reward_distribution = defaultdict(int)
        self.system_metrics = {
            "start_time": None,
            "total_events_run": 0,
            "total_participation_hours": 0
        }

    def record_system_start(self):
        """Record event system start"""
        self.system_metrics["start_time"] = time.time()

    def record_system_stop(self):
        """Record event system stop"""
        if self.system_metrics["start_time"]:
            uptime = time.time() - self.system_metrics["start_time"]
            self.system_metrics["uptime"] = uptime

    def record_event_start(self, instance_id: str, event_id: str):
        """Record event start"""
        self.event_stats[event_id]["times_started"] += 1
        self.system_metrics["total_events_run"] += 1

    def record_event_join(self, player_id: str, instance_id: str):
        """Record player joining event"""
        self.player_engagement[player_id].append({
            "action": "join",
            "instance_id": instance_id,
            "timestamp": time.time()
        })

    def record_event_contribution(self, player_id: str, instance_id: str, objective_id: str, amount: int):
        """Record player contribution to event"""
        self.player_engagement[player_id].append({
            "action": "contribute",
            "instance_id": instance_id,
            "objective_id": objective_id,
            "amount": amount,
            "timestamp": time.time()
        })

    def record_event_complete(self, instance_id: str, success: bool, participants: int, participation_rate: float):
        """Record event completion"""
        # Extract event_id from instance_id (before first underscore)
        event_id = instance_id.split('_')[0] if '_' in instance_id else instance_id

        stats = self.event_stats[event_id]
        stats["times_completed"] += 1
        stats["total_participants"] += participants
        stats["participation_rates"].append(participation_rate)

        # Update success rate
        if stats["times_started"] > 0:
            stats["success_rate"] = stats["times_completed"] / stats["times_started"]

        # Update average participation
        stats["average_participation"] = stats["total_participants"] / stats["times_completed"]

    def record_reward_grant(self, player_id: str, reward_type: str, reward_value: Any, multiplier: float):
        """Record reward distribution"""
        self.reward_distribution[f"{reward_type}_{reward_value}"] += 1

    def get_event_performance(self, event_id: str) -> Dict[str, Any]:
        """Get performance metrics for specific event"""
        if event_id not in self.event_stats:
            return {"error": "Event not found"}

        stats = self.event_stats[event_id]
        participation_rates = stats["participation_rates"]

        return {
            "event_id": event_id,
            "times_started": stats["times_started"],
            "times_completed": stats["times_completed"],
            "success_rate": stats["success_rate"],
            "average_participants": stats["average_participation"],
            "average_participation_rate": sum(participation_rates) / len(participation_rates) if participation_rates else 0,
            "engagement_score": (stats["success_rate"] * stats["average_participation_rate"]) if stats["success_rate"] and stats["average_participation_rate"] else 0
        }

    def get_system_overview(self) -> Dict[str, Any]:
        """Get overall system performance"""
        total_events = sum(stats["times_started"] for stats in self.event_stats.values())
        total_completions = sum(stats["times_completed"] for stats in self.event_stats.values())
        overall_success_rate = total_completions / total_events if total_events > 0 else 0

        return {
            "total_events_run": total_events,
            "total_completions": total_completions,
            "overall_success_rate": overall_success_rate,
            "system_uptime": self.system_metrics.get("uptime", 0),
            "most_popular_events": sorted(
                [(event_id, stats["total_participants"]) for event_id, stats in self.event_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "highest_success_rate": sorted(
                [(event_id, stats["success_rate"]) for event_id, stats in self.event_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

# Utility functions for event balance
def calculate_event_difficulty(event: WorldEvent, participant_count: int) -> float:
    """Calculate dynamic difficulty based on participant count"""
    base_difficulty = {
        EventRarity.COMMON: 1.0,
        EventRarity.UNCOMMON: 1.2,
        EventRarity.RARE: 1.5,
        EventRarity.EPIC: 2.0,
        EventRarity.LEGENDARY: 3.0
    }[event.rarity]

    # Scale difficulty with participant count (more participants = slightly harder)
    participant_modifier = 1.0 + (participant_count / 100) * 0.2

    return base_difficulty * participant_modifier

def optimize_event_schedule(events: List[WorldEvent], player_patterns: Dict[str, Any]) -> Dict[str, List[str]]:
    """Optimize event scheduling based on player activity patterns"""
    peak_hours = player_patterns.get("peak_hours", [19, 20, 21])  # 7-9 PM default
    optimal_schedule = {}

    for event in events:
        if event.event_type in [EventType.WORLD_BOSS, EventType.INVASION]:
            # Schedule major events during peak hours
            optimal_schedule[event.event_type.value] = [f"{hour}:00" for hour in peak_hours]
        elif event.event_type == EventType.FESTIVAL:
            # Schedule festivals for weekends
            optimal_schedule[event.event_type.value] = ["Saturday 14:00", "Sunday 14:00"]
        else:
            # Schedule other events throughout the day
            optimal_schedule[event.event_type.value] = ["10:00", "16:00", "22:00"]

    return optimal_schedule

# Export main classes
__all__ = [
    'EventSystem',
    'WorldEvent',
    'EventInstance',
    'EventSchedule',
    'EventAnalytics',
    'calculate_event_difficulty',
    'optimize_event_schedule'
]