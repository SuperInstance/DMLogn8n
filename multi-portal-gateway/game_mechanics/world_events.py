"""
Dynamic World Events System for DMLogn8n
Implements world-shaping events with cascading consequences and long-term impacts
"""

import random
import math
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

class EventType(Enum):
    """Types of world events"""
    NATURAL_DISASTER = "natural_disaster"
    POLITICAL = "political"
    ECONOMIC = "economic"
    MILITARY = "military"
    MAGICAL = "magical"
    RELIGIOUS = "religious"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    SUPERNATURAL = "supernatural"
    TECHNOLOGICAL = "technological"

class EventSeverity(Enum):
    """Severity levels of events"""
    MINOR = 1
    MODERATE = 2
    MAJOR = 3
    SEVERE = 4
    CATASTROPHIC = 5
    APOCALYPTIC = 6

class EventDuration(Enum):
    """Duration categories for events"""
    MOMENTARY = "momentary"    # A few hours
    BRIEF = "brief"           # A few days
    SHORT = "short"           # 1-2 weeks
    MEDIUM = "medium"         # 1-3 months
    LONG = "long"             # 3-12 months
    PERMANENT = "permanent"   # Permanent change

class EventScope(Enum):
    """Geographic scope of events"""
    LOCAL = "local"           # Single location
    REGIONAL = "regional"     # Small region
    NATIONAL = "national"     # Entire nation
    CONTINENTAL = "continental"  # Continent
    GLOBAL = "global"         # Entire world
    DIMENSIONAL = "dimensional"  # Multiple dimensions

class TriggerType(Enum):
    """Event trigger conditions"""
    TIME_BASED = "time_based"
    PLAYER_ACTION = "player_action"
    WORLD_STATE = "world_state"
    RANDOM_CHANCE = "random_chance"
    CHAIN_REACTION = "chain_reaction"
    SEASONAL = "seasonal"
    CONDITIONAL = "conditional"
    THRESHOLD = "threshold"

@dataclass
class EventTrigger:
    """Conditions that trigger an event"""
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    probability: float = 1.0
    cooldown: Optional[timedelta] = None
    last_triggered: Optional[datetime] = None

@dataclass
class EventConsequence:
    """Individual consequence of an event"""
    consequence_type: str
    target: str  # What is affected
    effect: Dict[str, Any]
    delay: timedelta = field(default_factory=timedelta)
    duration: Optional[timedelta] = None
    permanent: bool = False
    cascading: bool = False

@dataclass
class EventChoice:
    """Player choice during an event"""
    id: str
    description: str
    requirements: Dict[str, Any]
    consequences: List[EventConsequence]
    success_chance: float = 1.0
    hidden: bool = False
    requires_skill: Optional[str] = None
    requires_item: Optional[str] = None

@dataclass
class WorldEvent:
    """Complete world event definition"""
    id: str
    name: str
    description: str
    event_type: EventType
    severity: EventSeverity
    duration: EventDuration
    scope: EventScope

    # Timing and triggers
    triggers: List[EventTrigger] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_phase: int = 0
    phases: List[Dict[str, Any]] = field(default_factory=list)

    # Geography and targets
    affected_locations: List[str] = field(default_factory=list)
    affected_factions: List[str] = field(default_factory=list)
    affected_characters: List[str] = field(default_factory=list)

    # Consequences and choices
    immediate_consequences: List[EventConsequence] = field(default_factory=list)
    delayed_consequences: List[EventConsequence] = field(default_factory=list)
    player_choices: List[EventChoice] = field(default_factory=list)

    # Event properties
    visible: bool = True
    preventable: bool = False
    repeatable: bool = False
    chain_events: List[str] = field(default_factory=list)

    # Dynamic state
    active: bool = False
    completed: bool = False
    player_choices_made: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

class EventChain:
    """Chain of related events"""

    def __init__(self, chain_id: str, name: str):
        self.chain_id = chain_id
        self.name = name
        self.events: List[str] = field(default_factory=list)  # Event IDs
        self.current_index: int = 0
        self.completed: bool = False
        self.branches: Dict[str, List[str]] = field(default_factory=dict)  # choice_id -> [event_ids]

    def add_event(self, event_id: str):
        """Add event to chain"""
        if event_id not in self.events:
            self.events.append(event_id)

    def get_next_event(self) -> Optional[str]:
        """Get next event in chain"""
        if self.current_index < len(self.events):
            return self.events[self.current_index]
        return None

    def advance_chain(self):
        """Advance to next event in chain"""
        self.current_index += 1
        if self.current_index >= len(self.events):
            self.completed = True

class WorldEventManager:
    """Manages all world events and their consequences"""

    def __init__(self):
        self.events: Dict[str, WorldEvent] = {}
        self.event_templates: Dict[str, Dict[str, Any]] = {}
        self.active_events: List[WorldEvent] = field(default_factory=list)
        self.event_history: List[WorldEvent] = field(default_factory=list)
        self.event_chains: Dict[str, EventChain] = field(default_factory=dict)

        # World state tracking
        self.world_state: Dict[str, Any] = {}
        self.event_probability_modifiers: Dict[str, float] = {}
        self.global_event_cooldowns: Dict[str, datetime] = {}

        # Configuration
        self.base_event_frequency: float = 0.1  # 10% chance per day
        self.max_concurrent_events: int = 5
        self.cascade_depth_limit: int = 3

        self._initialize_event_templates()

    def _initialize_event_templates(self):
        """Initialize predefined event templates"""
        # Natural disasters
        self.event_templates["earthquake"] = {
            "name": "Great Earthquake",
            "description": "A massive earthquake shakes the region, causing widespread destruction.",
            "event_type": EventType.NATURAL_DISASTER,
            "severity": EventSeverity.MAJOR,
            "duration": EventDuration.BRIEF,
            "scope": EventScope.REGIONAL,
            "immediate_consequences": [
                {
                    "consequence_type": "building_damage",
                    "target": "region_buildings",
                    "effect": {"damage_percent": 0.3}
                },
                {
                    "consequence_type": "casualties",
                    "target": "population",
                    "effect": {"casualty_percent": 0.05}
                },
                {
                    "consequence_type": "economic_disruption",
                    "target": "trade",
                    "effect": {"disruption_days": 7}
                }
            ],
            "delayed_consequences": [
                {
                    "consequence_type": "rebuilding",
                    "target": "construction",
                    "effect": {"demand_multiplier": 2.0},
                    "delay": timedelta(days=1),
                    "duration": timedelta(days=30)
                },
                {
                    "consequence_type": "migration",
                    "target": "population",
                    "effect": {"migration_rate": 0.02},
                    "delay": timedelta(days=7),
                    "duration": timedelta(days=90)
                }
            ]
        }

        # Political events
        self.event_templates["political_uprising"] = {
            "name": "Popular Uprising",
            "description": "Citizens rise up against the current government demanding reforms.",
            "event_type": EventType.POLITICAL,
            "severity": EventSeverity.MAJOR,
            "duration": EventDuration.MEDIUM,
            "scope": EventScope.NATIONAL,
            "immediate_consequences": [
                {
                    "consequence_type": "civil_unrest",
                    "target": "social_order",
                    "effect": {"unrest_level": 0.7}
                },
                {
                    "consequence_type": "government_response",
                    "target": "military",
                    "effect": {"deployment_level": 0.8}
                }
            ],
            "player_choices": [
                {
                    "id": "support_rebels",
                    "description": "Support the uprising and fight for change",
                    "requirements": {"reputation": {"rebel_faction": 50}},
                    "consequences": [
                        {
                            "consequence_type": "faction_relationship",
                            "target": "rebel_faction",
                            "effect": {"relationship_change": 30}
                        },
                        {
                            "consequence_type": "faction_relationship",
                            "target": "government",
                            "effect": {"relationship_change": -50}
                        }
                    ]
                },
                {
                    "id": "support_government",
                    "description": "Support the government in maintaining order",
                    "requirements": {"reputation": {"government": 50}},
                    "consequences": [
                        {
                            "consequence_type": "faction_relationship",
                            "target": "government",
                            "effect": {"relationship_change": 30}
                        },
                        {
                            "consequence_type": "faction_relationship",
                            "target": "rebel_faction",
                            "effect": {"relationship_change": -50}
                        }
                    ]
                },
                {
                    "id": "mediate",
                    "description": "Attempt to mediate a peaceful resolution",
                    "requirements": {"skill": {"diplomacy": 50}},
                    "consequences": [
                        {
                            "consequence_type": "peaceful_resolution",
                            "target": "conflict",
                            "effect": {"success_chance": 0.6}
                        }
                    ]
                }
            ]
        }

        # Magical events
        self.event_templates["magical_surge"] = {
            "name": "Arcane Surge",
            "description": "A massive surge of magical energy sweeps across the land, causing wild magic effects.",
            "event_type": EventType.MAGICAL,
            "severity": EventSeverity.MAJOR,
            "duration": EventDuration.SHORT,
            "scope": EventScope.CONTINENTAL,
            "immediate_consequences": [
                {
                    "consequence_type": "wild_magic",
                    "target": "magic_users",
                    "effect": {"power_multiplier": 1.5, "instability": 0.8}
                },
                {
                    "consequence_type": "magical_creatures",
                    "target": "wildlife",
                    "effect": {"mutation_rate": 0.3}
                },
                {
                    "consequence_type": "rifts",
                    "target": "planar_boundaries",
                    "effect": {"stability": -0.5}
                }
            ],
            "delayed_consequences": [
                {
                    "consequence_type": "magical_research",
                    "target": "scholars",
                    "effect": {"research_speed": 2.0},
                    "delay": timedelta(days=3),
                    "duration": timedelta(days=14)
                }
            ]
        }

        # Economic events
        self.event_templates["market_crash"] = {
            "name": "Economic Collapse",
            "description": "The market experiences a catastrophic collapse, affecting trade and commerce.",
            "event_type": EventType.ECONOMIC,
            "severity": EventSeverity.SEVERE,
            "duration": EventDuration.MEDIUM,
            "scope": EventScope.NATIONAL,
            "immediate_consequences": [
                {
                    "consequence_type": "price_crash",
                    "target": "goods",
                    "effect": {"price_multiplier": 0.3}
                },
                {
                    "consequence_type": "business_failures",
                    "target": "merchants",
                    "effect": {"failure_rate": 0.4}
                },
                {
                    "consequence_type": "unemployment",
                    "target": "workers",
                    "effect": {"unemployment_rate": 0.3}
                }
            ],
            "delayed_consequences": [
                {
                    "consequence_type": "economic_recovery",
                    "target": "economy",
                    "effect": {"recovery_speed": 0.5},
                    "delay": timedelta(days=30),
                    "duration": timedelta(days=180)
                },
                {
                    "consequence_type": "social_unrest",
                    "target": "population",
                    "effect": {"unrest_level": 0.6},
                    "delay": timedelta(days=7),
                    "duration": timedelta(days=60)
                }
            ]
        }

        # Supernatural events
        self.event_templates["divine_intervention"] = {
            "name": "Divine Intervention",
            "description": "A divine being manifests and directly interferes with mortal affairs.",
            "event_type": EventType.SUPERNATURAL,
            "severity": EventSeverity.CATASTROPHIC,
            "duration": EventDuration.MOMENTARY,
            "scope": EventScope.GLOBAL,
            "immediate_consequences": [
                {
                    "consequence_type": "divine_blessing",
                    "target": "followers",
                    "effect": {"blessing_strength": 2.0}
                },
                {
                    "consequence_type": "divine_anger",
                    "target": "enemies",
                    "effect": {"curse_strength": -2.0}
                },
                {
                    "consequence_type": "miracle",
                    "target": "reality",
                    "effect": {"miracle_type": "resurrection"}
                }
            ],
            "permanent": True
        }

        # Environmental events
        self.event_templates["plague"] = {
            "name": "Deadly Plague",
            "description": "A mysterious plague spreads through the population, causing widespread illness.",
            "event_type": EventType.ENVIRONMENTAL,
            "severity": EventSeverity.SEVERE,
            "duration": EventDuration.MEDIUM,
            "scope": EventScope.REGIONAL,
            "immediate_consequences": [
                {
                    "consequence_type": "disease_spread",
                    "target": "population",
                    "effect": {"infection_rate": 0.4, "mortality_rate": 0.2}
                },
                {
                    "consequence_type": "quarantine",
                    "target": "travel",
                    "effect": {"restriction_level": 0.9}
                },
                {
                    "consequence_type": "medical_crisis",
                    "target": "healers",
                    "effect": {"overwhelmed": True}
                }
            ],
            "player_choices": [
                {
                    "id": "help_medical",
                    "description": "Assist healers in treating the sick",
                    "requirements": {"skill": {"healing": 30}},
                    "consequences": [
                        {
                            "consequence_type": "reduce_mortality",
                            "target": "population",
                            "effect": {"mortality_reduction": 0.1}
                        }
                    ]
                },
                {
                    "id": "find_cure",
                    "description": "Search for a cure to the plague",
                    "requirements": {"skill": {"alchemy": 50, "knowledge": 40}},
                    "consequences": [
                        {
                            "consequence_type": "cure_discovery",
                            "target": "plague",
                            "effect": {"cure_chance": 0.3}
                        }
                    ]
                }
            ]
        }

    def create_event(self, template_name: str, **kwargs) -> Optional[WorldEvent]:
        """Create event from template"""
        template = self.event_templates.get(template_name)
        if not template:
            return None

        event = WorldEvent(
            id=str(uuid.uuid4()),
            name=template["name"],
            description=template["description"],
            event_type=template["event_type"],
            severity=template["severity"],
            duration=template["duration"],
            scope=template["scope"],
            **kwargs
        )

        # Convert template consequences
        for cons_data in template.get("immediate_consequences", []):
            consequence = EventConsequence(**cons_data)
            event.immediate_consequences.append(consequence)

        for cons_data in template.get("delayed_consequences", []):
            consequence = EventConsequence(**cons_data)
            event.delayed_consequences.append(consequence)

        # Convert player choices
        for choice_data in template.get("player_choices", []):
            choice = EventChoice(**choice_data)
            event.player_choices.append(choice)

        self.events[event.id] = event
        return event

    def trigger_event(self, event_id: str, location: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None) -> bool:
        """Trigger a world event"""
        event = self.events.get(event_id)
        if not event or event.active:
            return False

        # Set location if provided
        if location:
            event.affected_locations.append(location)

        # Apply context variables
        if context:
            event.variables.update(context)

        # Activate event
        event.active = True
        event.start_time = datetime.now()
        event.end_time = self._calculate_end_time(event)

        # Add to active events
        self.active_events.append(event)

        # Apply immediate consequences
        self._apply_consequences(event.immediate_consequences, event)

        # Schedule delayed consequences
        self._schedule_delayed_consequences(event)

        return True

    def _calculate_end_time(self, event: WorldEvent) -> datetime:
        """Calculate when event should end"""
        duration_map = {
            EventDuration.MOMENTARY: timedelta(hours=1),
            EventDuration.BRIEF: timedelta(days=3),
            EventDuration.SHORT: timedelta(weeks=2),
            EventDuration.MEDIUM: timedelta(months=2),
            EventDuration.LONG: timedelta(months=6),
            EventDuration.PERMANENT: timedelta(days=365 * 100)  # 100 years
        }

        duration = duration_map.get(event.duration, timedelta(days=1))
        return datetime.now() + duration

    def _apply_consequences(self, consequences: List[EventConsequence],
                           event: WorldEvent):
        """Apply event consequences to world state"""
        for consequence in consequences:
            if consequence.delay.total_seconds() == 0:
                self._apply_single_consequence(consequence, event)

    def _schedule_delayed_consequences(self, event: WorldEvent):
        """Schedule delayed consequences for future application"""
        # In a real implementation, this would schedule the consequences
        # For now, we'll note that they need to be applied later
        for consequence in event.delayed_consequences:
            pass  # Would be scheduled by a task system

    def _apply_single_consequence(self, consequence: EventConsequence,
                                 event: WorldEvent):
        """Apply a single consequence to the world"""
        consequence_type = consequence.consequence_type
        target = consequence.target
        effect = consequence.effect

        # Apply different types of consequences
        if consequence_type == "building_damage":
            self._apply_building_damage(target, effect, event)
        elif consequence_type == "casualties":
            self._apply_casualties(target, effect, event)
        elif consequence_type == "economic_disruption":
            self._apply_economic_disruption(target, effect, event)
        elif consequence_type == "faction_relationship":
            self._apply_faction_relationship_change(target, effect, event)
        elif consequence_type == "wild_magic":
            self._apply_wild_magic(target, effect, event)
        elif consequence_type == "price_crash":
            self._apply_price_crash(target, effect, event)
        elif consequence_type == "disease_spread":
            self._apply_disease_spread(target, effect, event)

        # Store consequence in world state
        state_key = f"event_{event.id}_{consequence_type}"
        self.world_state[state_key] = {
            "applied_at": datetime.now(),
            "effect": effect,
            "duration": consequence.duration,
            "permanent": consequence.permanent
        }

    def _apply_building_damage(self, target: str, effect: Dict[str, Any],
                              event: WorldEvent):
        """Apply building damage consequence"""
        damage_percent = effect.get("damage_percent", 0.0)
        for location in event.affected_locations:
            # Update building integrity in location
            state_key = f"{location}_building_integrity"
            current_integrity = self.world_state.get(state_key, 100.0)
            new_integrity = max(0, current_integrity * (1 - damage_percent))
            self.world_state[state_key] = new_integrity

    def _apply_casualties(self, target: str, effect: Dict[str, Any],
                         event: WorldEvent):
        """Apply casualties consequence"""
        casualty_percent = effect.get("casualty_percent", 0.0)
        for location in event.affected_locations:
            # Update population in location
            state_key = f"{location}_population"
            current_pop = self.world_state.get(state_key, 1000)
            casualties = int(current_pop * casualty_percent)
            self.world_state[state_key] = current_pop - casualties

    def _apply_economic_disruption(self, target: str, effect: Dict[str, Any],
                                  event: WorldEvent):
        """Apply economic disruption consequence"""
        disruption_days = effect.get("disruption_days", 0)
        state_key = "trade_disruption"
        current_disruption = self.world_state.get(state_key, 0)
        self.world_state[state_key] = max(current_disruption, disruption_days)

    def _apply_faction_relationship_change(self, target: str, effect: Dict[str, Any],
                                         event: WorldEvent):
        """Apply faction relationship change"""
        relationship_change = effect.get("relationship_change", 0)
        state_key = f"faction_relationship_{target}"
        current_relationship = self.world_state.get(state_key, 0)
        self.world_state[state_key] = max(-100, min(100, current_relationship + relationship_change))

    def _apply_wild_magic(self, target: str, effect: Dict[str, Any],
                         event: WorldEvent):
        """Apply wild magic consequence"""
        power_multiplier = effect.get("power_multiplier", 1.0)
        instability = effect.get("instability", 0.0)

        self.world_state["wild_magic_active"] = True
        self.world_state["magic_power_multiplier"] = power_multiplier
        self.world_state["magic_instability"] = instability

    def _apply_price_crash(self, target: str, effect: Dict[str, Any],
                          event: WorldEvent):
        """Apply price crash consequence"""
        price_multiplier = effect.get("price_multiplier", 1.0)
        self.world_state["economic_crash_active"] = True
        self.world_state["price_multiplier"] = price_multiplier

    def _apply_disease_spread(self, target: str, effect: Dict[str, Any],
                             event: WorldEvent):
        """Apply disease spread consequence"""
        infection_rate = effect.get("infection_rate", 0.0)
        mortality_rate = effect.get("mortality_rate", 0.0)

        self.world_state["plague_active"] = True
        self.world_state["plague_infection_rate"] = infection_rate
        self.world_state["plague_mortality_rate"] = mortality_rate

    def make_player_choice(self, event_id: str, choice_id: str,
                          player_context: Dict[str, Any]) -> bool:
        """Process player choice for an event"""
        event = self.events.get(event_id)
        if not event or not event.active:
            return False

        # Find the choice
        choice = None
        for c in event.player_choices:
            if c.id == choice_id:
                choice = c
                break

        if not choice:
            return False

        # Check requirements
        if not self._check_choice_requirements(choice, player_context):
            return False

        # Calculate success
        success = random.random() < choice.success_chance

        # Apply consequences
        if success:
            self._apply_consequences(choice.consequences, event)

        # Record choice
        event.player_choices_made.append(choice_id)

        return True

    def _check_choice_requirements(self, choice: EventChoice,
                                 player_context: Dict[str, Any]) -> bool:
        """Check if player meets choice requirements"""
        requirements = choice.requirements

        # Check skill requirements
        if "skill" in requirements:
            for skill, required_level in requirements["skill"].items():
                player_skill = player_context.get("skills", {}).get(skill, 0)
                if player_skill < required_level:
                    return False

        # Check reputation requirements
        if "reputation" in requirements:
            for faction, required_rep in requirements["reputation"].items():
                player_rep = player_context.get("reputation", {}).get(faction, 0)
                if player_rep < required_rep:
                    return False

        # Check item requirements
        if choice.requires_item:
            inventory = player_context.get("inventory", [])
            if choice.requires_item not in inventory:
                return False

        return True

    def update_events(self):
        """Update all active events and process expired ones"""
        current_time = datetime.now()
        expired_events = []

        for event in self.active_events:
            # Check if event should end
            if event.end_time and current_time >= event.end_time:
                expired_events.append(event)
                continue

            # Update event phases
            self._update_event_phases(event)

            # Apply delayed consequences that are due
            self._apply_due_consequences(event, current_time)

        # Remove expired events
        for event in expired_events:
            event.active = False
            event.completed = True
            self.active_events.remove(event)
            self.event_history.append(event)

            # Trigger chain events
            self._trigger_chain_events(event)

        # Check for random events
        self._check_random_events(current_time)

    def _update_event_phases(self, event: WorldEvent):
        """Update event through its phases"""
        if not event.phases:
            return

        current_time = datetime.now()
        if event.start_time:
            elapsed = current_time - event.start_time

            for i, phase in enumerate(event.phases):
                if i == event.current_phase:
                    phase_duration = phase.get("duration", timedelta(days=1))
                    if elapsed >= phase_duration:
                        event.current_phase += 1
                        # Apply phase-specific consequences
                        if "consequences" in phase:
                            self._apply_consequences(phase["consequences"], event)

    def _apply_due_consequences(self, event: WorldEvent, current_time: datetime):
        """Apply delayed consequences that are due"""
        for consequence in event.delayed_consequences:
            if event.start_time:
                trigger_time = event.start_time + consequence.delay
                if current_time >= trigger_time:
                    # Check if consequence should still be active
                    if not consequence.duration or current_time <= trigger_time + consequence.duration:
                        self._apply_single_consequence(consequence, event)

    def _trigger_chain_events(self, completed_event: WorldEvent):
        """Trigger events that chain from completed event"""
        for chain_event_id in completed_event.chain_events:
            if chain_event_id in self.events:
                self.trigger_event(chain_event_id)

    def _check_random_events(self, current_time: datetime):
        """Check for random event triggers"""
        if len(self.active_events) >= self.max_concurrent_events:
            return

        if random.random() < self.base_event_frequency:
            # Select random event template
            template_name = random.choice(list(self.event_templates.keys()))

            # Check cooldowns
            if self._is_event_on_cooldown(template_name, current_time):
                return

            # Create and trigger event
            event = self.create_event(template_name)
            if event:
                # Select random location
                locations = ["capital_city", "riverdale", "crossroads", "mountain_pass"]
                location = random.choice(locations)

                self.trigger_event(event.id, location)

                # Set cooldown
                self.global_event_cooldowns[template_name] = current_time + timedelta(days=7)

    def _is_event_on_cooldown(self, template_name: str, current_time: datetime) -> bool:
        """Check if event type is on cooldown"""
        last_triggered = self.global_event_cooldowns.get(template_name)
        if last_triggered:
            cooldown_period = timedelta(days=7)
            return current_time < last_triggered + cooldown_period
        return False

    def create_event_chain(self, chain_id: str, name: str,
                          event_template_names: List[str]) -> EventChain:
        """Create a chain of related events"""
        chain = EventChain(chain_id, name)

        for template_name in event_template_names:
            event = self.create_event(template_name)
            if event:
                chain.add_event(event.id)
                # Add chain trigger
                if len(chain.events) > 1:
                    # Previous event triggers this one
                    prev_event_id = chain.events[-2]
                    self.events[prev_event_id].chain_events.append(event.id)

        self.event_chains[chain_id] = chain
        return chain

    def trigger_event_chain(self, chain_id: str, **kwargs):
        """Trigger an event chain"""
        chain = self.event_chains.get(chain_id)
        if not chain:
            return False

        first_event_id = chain.get_next_event()
        if first_event_id:
            return self.trigger_event(first_event_id, **kwargs)

        return False

    def get_active_events_for_location(self, location: str) -> List[WorldEvent]:
        """Get all active events affecting a location"""
        return [event for event in self.active_events
                if not event.affected_locations or location in event.affected_locations]

    def get_event_history(self, limit: int = 50) -> List[WorldEvent]:
        """Get recent event history"""
        return self.event_history[-limit:]

    def get_world_state_summary(self) -> Dict[str, Any]:
        """Get summary of current world state"""
        active_disasters = [e for e in self.active_events if e.event_type == EventType.NATURAL_DISASTER]
        active_crises = [e for e in self.active_events if e.severity.value >= EventSeverity.SEVERE.value]
        magical_phenomena = [e for e in self.active_events if e.event_type == EventType.MAGICAL]

        return {
            "active_events": len(self.active_events),
            "event_types": {
                event_type.value: len([e for e in self.active_events if e.event_type == event_type])
                for event_type in EventType
            },
            "severity_distribution": {
                severity.value: len([e for e in self.active_events if e.severity == severity])
                for severity in EventSeverity
            },
            "active_disasters": len(active_disasters),
            "active_crises": len(active_crises),
            "magical_phenomena": len(magical_phenomena),
            "recent_events": len([e for e in self.event_history
                                 if (datetime.now() - e.end_time).days < 30]),
            "world_state_variables": len(self.world_state),
            "active_chains": len([c for c in self.event_chains.values() if not c.completed])
        }

# Example usage and testing
if __name__ == "__main__":
    # Create world event manager
    event_manager = WorldEventManager()

    print("=== WORLD EVENT MANAGER INITIALIZED ===")
    print(f"Available Templates: {len(event_manager.event_templates)}")

    # Create and trigger some events
    print("\n=== TRIGGERING EVENTS ===")

    # Trigger an earthquake
    earthquake = event_manager.create_event("earthquake")
    if earthquake:
        success = event_manager.trigger_event(earthquake.id, "capital_city")
        print(f"Earthquake triggered: {success}")

    # Trigger a magical surge
    magical_surge = event_manager.create_event("magical_surge")
    if magical_surge:
        success = event_manager.trigger_event(magical_surge.id)
        print(f"Magical surge triggered: {success}")

    # Create a political uprising with player choices
    uprising = event_manager.create_event("political_uprising")
    if uprising:
        success = event_manager.trigger_event(uprising.id, "riverdale")
        print(f"Political uprising triggered: {success}")

        # Simulate player making a choice
        player_context = {
            "skills": {"diplomacy": 60},
            "reputation": {"government": 30, "rebel_faction": 40},
            "inventory": ["diplomatic_ring"]
        }

        choice_success = event_manager.make_player_choice(
            uprising.id, "mediate", player_context
        )
        print(f"Player choice successful: {choice_success}")

    # Create an event chain
    print(f"\n=== EVENT CHAIN ===")
    plague_chain = event_manager.create_event_chain(
        "plague_chain",
        "The Great Plague",
        ["plague", "market_crash", "political_uprising"]
    )
    print(f"Created event chain: {plague_chain.name} with {len(plague_chain.events)} events")

    # Trigger the chain
    chain_success = event_manager.trigger_event_chain("plague_chain", "crossroads")
    print(f"Event chain triggered: {chain_success}")

    # Simulate a few days of updates
    print(f"\n=== SIMULATING TIME ===")
    for day in range(5):
        event_manager.update_events()
        active_count = len(event_manager.active_events)
        print(f"Day {day + 1}: {active_count} active events")

        if day == 2:
            # Trigger another event
            market_crash = event_manager.create_event("market_crash")
            if market_crash:
                event_manager.trigger_event(market_crash.id, "capital_city")
                print("  Market crash triggered!")

    # Show world state summary
    print(f"\n=== WORLD STATE SUMMARY ===")
    summary = event_manager.get_world_state_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    # Show active events
    print(f"\n=== ACTIVE EVENTS ===")
    for event in event_manager.active_events:
        print(f"- {event.name} ({event.event_type.value}, {event.severity.value})")
        print(f"  Description: {event.description}")
        print(f"  Locations: {event.affected_locations}")
        if event.player_choices:
            print(f"  Player Choices: {len(event.player_choices)} available")

    # Show recent event history
    print(f"\n=== RECENT EVENT HISTORY ===")
    history = event_manager.get_event_history(5)
    for event in history:
        status = "Completed" if event.completed else "Active"
        print(f"- {event.name}: {status}")

    # Show world state changes
    print(f"\n=== WORLD STATE CHANGES ===")
    interesting_states = [
        key for key in event_manager.world_state.keys()
        if any(term in key for term in ["event_", "plague", "magic", "economic"])
    ]
    for state_key in interesting_states[:10]:
        value = event_manager.world_state[state_key]
        if isinstance(value, dict) and "applied_at" in value:
            print(f"- {state_key}: Applied at {value['applied_at']}")
        else:
            print(f"- {state_key}: {value}")