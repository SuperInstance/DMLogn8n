"""
Advanced NPC Behavior System for DMLogn8n
Implements complex NPC AI with behavior trees, daily routines, and relationships
"""

import random
import json
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
import math

class NPCRole(Enum):
    """NPC roles with different behavioral patterns"""
    VILLAGER = "villager"
    MERCHANT = "merchant"
    GUARD = "guard"
    HEALER = "healer"
    SCHOLAR = "scholar"
    BLACKSMITH = "blacksmith"
    INNKEEPER = "innkeeper"
    THIEF = "thief"
    NOBLE = "noble"
    WIZARD = "wizard"
    CLERIC = "cleric"
    RANGER = "ranger"
    BARD = "bard"
    CHILD = "child"
    ELDER = "elder"

class Mood(Enum):
    """NPC emotional states affecting behavior"""
    HAPPY = "happy"
    CONTENT = "content"
    NEUTRAL = "neutral"
    WORRIED = "worried"
    ANGRY = "angry"
    SAD = "sad"
    EXCITED = "excited"
    FEARFUL = "fearful"
    CONFIDENT = "confident"
    SUSPICIOUS = "suspicious"

class RelationshipType(Enum):
    """Types of relationships between NPCs"""
    FRIEND = "friend"
    FAMILY = "family"
    ROMANTIC = "romantic"
    RIVAL = "rival"
    ENEMY = "enemy"
    MENTOR = "mentor"
    STUDENT = "student"
    COLLEAGUE = "colleague"
    CUSTOMER = "customer"
    STRANGER = "stranger"

class Activity(Enum):
    """Daily activities for NPCs"""
    SLEEPING = "sleeping"
    WORKING = "working"
    EATING = "eating"
    SOCIALIZING = "socializing"
    SHOPPING = "shopping"
    TRAVELING = "traveling"
    WORSHIP = "worship"
    TRAINING = "training"
    READING = "reading"
    CRAFTING = "crafting"
    GUARDING = "guarding"
    ENTERTAINING = "entertaining"
    EXPLORING = "exploring"

@dataclass
class ScheduleEntry:
    """Single entry in NPC's daily schedule"""
    start_time: time
    end_time: time
    activity: Activity
    location: str
    priority: int = 1  # 1-5, higher = more important
    flexibility: float = 0.1  # How flexible this schedule is (0.0 = rigid, 1.0 = very flexible)

@dataclass
class Relationship:
    """Relationship between NPCs"""
    target_id: str
    relationship_type: RelationshipType
    strength: float  # -100 to 100
    trust_level: float  # 0 to 100
    last_interaction: Optional[datetime] = None
    shared_memories: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)

@dataclass
class Memory:
    """NPC memory with emotional impact"""
    event_id: str
    description: str
    timestamp: datetime
    emotional_impact: float  # -100 to 100
    importance: float  # 0 to 100
    associated_npcs: List[str] = field(default_factory=list)
    associated_locations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

class BehaviorNode:
    """Base class for behavior tree nodes"""

    def __init__(self, name: str):
        self.name = name
        self.parent = None
        self.children = []
        self.status = "READY"  # READY, RUNNING, SUCCESS, FAILURE

    def add_child(self, child: 'BehaviorNode'):
        """Add child node"""
        self.children.append(child)
        child.parent = self

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Execute the behavior node"""
        raise NotImplementedError

class SequenceNode(BehaviorNode):
    """Sequence node - executes children in order until one fails"""

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Execute all children in sequence"""
        for child in self.children:
            result = child.execute(npc, context)
            if result == "FAILURE":
                self.status = "FAILURE"
                return "FAILURE"
            elif result == "RUNNING":
                self.status = "RUNNING"
                return "RUNNING"

        self.status = "SUCCESS"
        return "SUCCESS"

class SelectorNode(BehaviorNode):
    """Selector node - executes children until one succeeds"""

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Execute children until one succeeds"""
        for child in self.children:
            result = child.execute(npc, context)
            if result == "SUCCESS":
                self.status = "SUCCESS"
                return "SUCCESS"
            elif result == "RUNNING":
                self.status = "RUNNING"
                return "RUNNING"

        self.status = "FAILURE"
        return "FAILURE"

class ParallelNode(BehaviorNode):
    """Parallel node - executes all children simultaneously"""

    def __init__(self, name: str, success_threshold: int = 1):
        super().__init__(name)
        self.success_threshold = success_threshold  # Number of children that must succeed

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Execute all children in parallel"""
        successes = 0
        failures = 0
        running = 0

        for child in self.children:
            result = child.execute(npc, context)
            if result == "SUCCESS":
                successes += 1
            elif result == "FAILURE":
                failures += 1
            else:
                running += 1

        if successes >= self.success_threshold:
            self.status = "SUCCESS"
            return "SUCCESS"
        elif failures > len(self.children) - self.success_threshold:
            self.status = "FAILURE"
            return "FAILURE"
        else:
            self.status = "RUNNING"
            return "RUNNING"

class ConditionNode(BehaviorNode):
    """Condition node - checks a condition"""

    def __init__(self, name: str, condition: Callable[['NPC', Dict[str, Any]], bool]):
        super().__init__(name)
        self.condition = condition

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Check the condition"""
        if self.condition(npc, context):
            self.status = "SUCCESS"
            return "SUCCESS"
        else:
            self.status = "FAILURE"
            return "FAILURE"

class ActionNode(BehaviorNode):
    """Action node - performs an action"""

    def __init__(self, name: str, action: Callable[['NPC', Dict[str, Any]], str]):
        super().__init__(name)
        self.action = action

    def execute(self, npc: 'NPC', context: Dict[str, Any]) -> str:
        """Perform the action"""
        result = self.action(npc, context)
        self.status = result
        return result

@dataclass
class NPC:
    """Complete NPC with advanced behavior system"""

    # Basic information
    id: str
    name: str
    role: NPCRole
    level: int = 1
    age: int = 25

    # Personality traits (0-100)
    personality: Dict[str, float] = field(default_factory=lambda: {
        "friendliness": 50,
        "curiosity": 50,
        "bravery": 50,
        "honesty": 50,
        "greed": 50,
        "ambition": 50,
        "patience": 50,
        "humor": 50,
        "intelligence": 50,
        "spirituality": 50
    })

    # Current state
    current_mood: Mood = Mood.NEUTRAL
    current_location: str = "home"
    current_activity: Activity = Activity.SLEEPING
    health: float = 100.0
    energy: float = 100.0
    hunger: float = 50.0
    happiness: float = 50.0

    # Schedule and routines
    daily_schedule: List[ScheduleEntry] = field(default_factory=list)
    current_schedule_index: int = 0

    # Relationships and social network
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    family_members: List[str] = field(default_factory=list)
    friends: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)

    # Memory and knowledge
    memories: List[Memory] = field(default_factory=list)
    knowledge: Dict[str, Any] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)

    # Behavior and AI
    behavior_tree: Optional[BehaviorNode] = None
    current_goal: Optional[str] = None
    goals: List[str] = field(default_factory=list)

    # Economic and inventory
    gold: int = 0
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    shop_inventory: List[Dict[str, Any]] = field(default_factory=list) if role == NPCRole.MERCHANT else field(default_factory=list)

    # Quests and interactions
    available_quests: List[str] = field(default_factory=list)
    active_quests: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)

    # Dialogue and personality
    dialogue_patterns: Dict[str, List[str]] = field(default_factory=dict)
    voice_tone: str = "neutral"
    speech_patterns: List[str] = field(default_factory=list)

    # Dynamic state
    last_update: datetime = field(default_factory=datetime.now)
    decision_history: List[Dict[str, Any]] = field(default_factory=list)
    current_emotion: float = 0.0  # -100 to 100
    stress_level: float = 0.0  # 0 to 100

    def update(self, current_time: datetime, world_context: Dict[str, Any]):
        """Update NPC state"""
        # Update needs
        self._update_needs(current_time)

        # Update mood based on needs
        self._update_mood()

        # Check and follow schedule
        self._follow_schedule(current_time)

        # Execute behavior tree
        if self.behavior_tree:
            self.behavior_tree.execute(self, world_context)

        # Process relationships
        self._process_relationships(current_time)

        # Memory decay and processing
        self._process_memories(current_time)

        self.last_update = current_time

    def _update_needs(self, current_time: datetime):
        """Update basic needs over time"""
        time_delta = (current_time - self.last_update).total_seconds() / 3600  # Convert to hours

        # Energy decreases with activity and time
        if self.current_activity in [Activity.WORKING, Activity.TRAINING, Activity.TRAVELING]:
            self.energy = max(0, self.energy - time_delta * 5)
        elif self.current_activity == Activity.SLEEPING:
            self.energy = min(100, self.energy + time_delta * 15)
        else:
            self.energy = max(0, self.energy - time_delta * 1)

        # Hunger increases over time
        self.hunger = min(100, self.hunger + time_delta * 3)

        # Health regeneration (slow)
        if self.energy > 50:
            self.health = min(100, self.health + time_delta * 0.5)

    def _update_mood(self):
        """Update mood based on current state"""
        mood_factors = {
            "energy": self.energy / 100,
            "hunger": (100 - self.hunger) / 100,  # Less hunger = better mood
            "health": self.health / 100,
            "happiness": self.happiness / 100,
            "stress": (100 - self.stress_level) / 100
        }

        mood_score = sum(mood_factors.values()) / len(mood_factors)

        # Map mood score to Mood enum
        if mood_score > 0.8:
            self.current_mood = Mood.HAPPY
        elif mood_score > 0.6:
            self.current_mood = Mood.CONTENT
        elif mood_score > 0.4:
            self.current_mood = Mood.NEUTRAL
        elif mood_score > 0.2:
            self.current_mood = Mood.WORRIED
        else:
            self.current_mood = Mood.SAD

    def _follow_schedule(self, current_time: datetime):
        """Follow daily schedule"""
        current_hour = current_time.time()

        # Find current schedule entry
        for i, entry in enumerate(self.daily_schedule):
            if entry.start_time <= current_hour < entry.end_time:
                if i != self.current_schedule_index:
                    self.current_schedule_index = i
                    self.current_activity = entry.activity
                    self.current_location = entry.location
                break

    def _process_relationships(self, current_time: datetime):
        """Process relationship maintenance and development"""
        for npc_id, relationship in self.relationships.items():
            # Relationship decay over time
            if relationship.last_interaction:
                time_since_interaction = current_time - relationship.last_interaction
                days_since = time_since_interaction.days

                if days_since > 7:  # After a week, relationships start to decay
                    decay_rate = 0.1 * (days_since - 7)
                    relationship.strength = max(-100, relationship.strength - decay_rate)
                    relationship.trust_level = max(0, relationship.trust_level - decay_rate * 0.5)

    def _process_memories(self, current_time: datetime):
        """Process memory decay and importance"""
        # Memory decay over time
        for memory in self.memories:
            age_days = (current_time - memory.timestamp).days
            if age_days > 30:  # Memories older than 30 days start to fade
                decay_factor = 0.01 * (age_days - 30)
                memory.importance = max(0, memory.importance - decay_factor)
                memory.emotional_impact *= (1 - decay_factor * 0.1)

    def add_memory(self, event_id: str, description: str, emotional_impact: float,
                   importance: float, associated_npcs: List[str] = None,
                   associated_locations: List[str] = None, tags: List[str] = None):
        """Add a new memory to the NPC"""
        memory = Memory(
            event_id=event_id,
            description=description,
            timestamp=datetime.now(),
            emotional_impact=emotional_impact,
            importance=importance,
            associated_npcs=associated_npcs or [],
            associated_locations=associated_locations or [],
            tags=tags or []
        )
        self.memories.append(memory)

        # Update mood based on emotional impact
        self.current_emotion = max(-100, min(100, self.current_emotion + emotional_impact * 0.1))

        # Keep only important memories (limit memory count)
        if len(self.memories) > 100:
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            self.memories = self.memories[:100]

    def get_relationship(self, npc_id: str) -> Optional[Relationship]:
        """Get relationship with another NPC"""
        return self.relationships.get(npc_id)

    def set_relationship(self, npc_id: str, relationship_type: RelationshipType,
                        strength: float, trust_level: float):
        """Set or update relationship with another NPC"""
        relationship = Relationship(
            target_id=npc_id,
            relationship_type=relationship_type,
            strength=strength,
            trust_level=trust_level,
            last_interaction=datetime.now()
        )
        self.relationships[npc_id] = relationship

        # Update relationship lists
        self._update_relationship_lists()

    def _update_relationship_lists(self):
        """Update relationship category lists"""
        self.friends = [npc_id for npc_id, rel in self.relationships.items()
                       if rel.relationship_type == RelationshipType.FRIEND and rel.strength > 30]
        self.enemies = [npc_id for npc_id, rel in self.relationships.items()
                       if rel.relationship_type == RelationshipType.ENEMY or rel.strength < -30]
        self.family_members = [npc_id for npc_id, rel in self.relationships.items()
                             if rel.relationship_type == RelationshipType.FAMILY]

    def generate_dialogue(self, context: Dict[str, Any]) -> str:
        """Generate dialogue based on current state and context"""
        # Base dialogue patterns for mood
        mood_dialogues = {
            Mood.HAPPY: [
                "Wonderful day, isn't it?",
                "I'm feeling quite cheerful today!",
                "Life has been good to me lately."
            ],
            Mood.CONTENT: [
                "Just another peaceful day.",
                "Things are going well, thank you.",
                "Can't complain about the weather."
            ],
            Mood.NEUTRAL: [
                "Hello there.",
                "How can I help you?",
                "What brings you here?"
            ],
            Mood.WORRIED: [
                "I've had better days...",
                "Something troubles my mind.",
                "I hope things improve soon."
            ],
            Mood.ANGRY: [
                "What do you want?",
                "I'm not in the mood for talk.",
                "Leave me be."
            ],
            Mood.SAD: [
                "...excuse me...",
                "I'd rather be alone right now.",
                "It's been difficult lately."
            ]
        }

        # Role-specific dialogue
        role_dialogues = {
            NPCRole.MERCHANT: [
                "Looking to buy or sell something?",
                "I have the finest goods in town!",
                "Business has been {business_status}."
            ],
            NPCRole.GUARD: [
                "Stay safe out there.",
                "Report any suspicious activity.",
                "The town is {safety_status}."
            ],
            NPCRole.HEALER: [
                "Are you feeling well?",
                "Health is the greatest wealth.",
                "I can help with {ailment}."
            ],
            NPCRole.SCHOLAR: [
                "Knowledge is power, you know.",
                "Have you read about {topic}?",
                "I've been studying {subject}."
            ]
        }

        # Select appropriate dialogue
        mood_options = mood_dialogues.get(self.current_mood, mood_dialogues[Mood.NEUTRAL])
        role_options = role_dialogues.get(self.role, [])

        if role_options and random.random() < 0.7:
            dialogue = random.choice(role_options)
        else:
            dialogue = random.choice(mood_options)

        # Fill in context variables
        if "{business_status}" in dialogue:
            business_status = "good" if self.gold > 100 else "slow"
            dialogue = dialogue.replace("{business_status}", business_status)

        if "{safety_status}" in dialogue:
            safety_status = "safe" if self.current_mood in [Mood.HAPPY, Mood.CONTENT] else "concerning"
            dialogue = dialogue.replace("{safety_status}", safety_status)

        return dialogue

class NPCBehaviorTreeBuilder:
    """Builder for creating NPC behavior trees"""

    @staticmethod
    def create_villager_behavior() -> BehaviorNode:
        """Create behavior tree for villager NPC"""

        # Root selector
        root = SelectorNode("Villager Root")

        # Emergency conditions
        emergency_sequence = SequenceNode("Emergency Response")
        emergency_sequence.add_child(ConditionNode("Check Health",
            lambda npc, ctx: npc.health < 30))
        emergency_sequence.add_child(ActionNode("Seek Help",
            lambda npc, ctx: "seeking_healer"))

        # Hunger management
        hunger_sequence = SequenceNode("Hunger Management")
        hunger_sequence.add_child(ConditionNode("Check Hunger",
            lambda npc, ctx: npc.hunger > 80))
        hunger_sequence.add_child(ActionNode("Find Food",
            lambda npc, ctx: "finding_food"))

        # Social interaction
        social_sequence = SequenceNode("Social Behavior")
        social_sequence.add_child(ConditionNode("Feel Social",
            lambda npc, ctx: npc.personality["friendliness"] > 60 and npc.energy > 50))
        social_sequence.add_child(ActionNode("Socialize",
            lambda npc, ctx: "socializing"))

        # Default behavior
        default_action = ActionNode("Default Activity",
            lambda npc, ctx: "default_activity")

        # Build tree
        root.add_child(emergency_sequence)
        root.add_child(hunger_sequence)
        root.add_child(social_sequence)
        root.add_child(default_action)

        return root

    @staticmethod
    def create_merchant_behavior() -> BehaviorNode:
        """Create behavior tree for merchant NPC"""

        root = SelectorNode("Merchant Root")

        # Shop management
        shop_sequence = SequenceNode("Shop Management")
        shop_sequence.add_child(ConditionNode("Shop Hours",
            lambda npc, ctx: 8 <= datetime.now().hour <= 18))
        shop_sequence.add_child(ActionNode("Tend Shop",
            lambda npc, ctx: "tending_shop"))

        # Inventory management
        inventory_sequence = SequenceNode("Inventory Management")
        inventory_sequence.add_child(ConditionNode("Low Stock",
            lambda npc, ctx: len(npc.shop_inventory) < 5))
        inventory_sequence.add_child(ActionNode("Restock",
            lambda npc, ctx: "restocking"))

        # Business development
        business_sequence = SequenceNode("Business Development")
        business_sequence.add_child(ConditionNode("Ambitious",
            lambda npc, ctx: npc.personality["ambition"] > 70))
        business_sequence.add_child(ActionNode("Seek Opportunities",
            lambda npc, ctx: "seeking_business"))

        root.add_child(shop_sequence)
        root.add_child(inventory_sequence)
        root.add_child(business_sequence)
        root.add_child(ActionNode("Personal Time",
            lambda npc, ctx: "personal_time"))

        return root

    @staticmethod
    def create_guard_behavior() -> BehaviorNode:
        """Create behavior tree for guard NPC"""

        root = SelectorNode("Guard Root")

        # Threat response
        threat_sequence = SequenceNode("Threat Response")
        threat_sequence.add_child(ConditionNode("Threat Detected",
            lambda npc, ctx: ctx.get("threat_level", 0) > 5))
        threat_sequence.add_child(ActionNode("Respond to Threat",
            lambda npc, ctx: "responding_to_threat"))

        # Patrol duty
        patrol_sequence = SequenceNode("Patrol Duty")
        patrol_sequence.add_child(ConditionNode("On Duty",
            lambda npc, ctx: npc.current_activity == Activity.GUARDING))
        patrol_sequence.add_child(ActionNode("Patrol",
            lambda npc, ctx: "patrolling"))

        # Investigation
        investigate_sequence = SequenceNode("Investigation")
        investigate_sequence.add_child(ConditionNode("Suspicious Activity",
            lambda npc, ctx: ctx.get("suspicious_activity", False)))
        investigate_sequence.add_child(ActionNode("Investigate",
            lambda npc, ctx: "investigating"))

        root.add_child(threat_sequence)
        root.add_child(patrol_sequence)
        root.add_child(investigate_sequence)
        root.add_child(ActionNode("Stand Ready",
            lambda npc, ctx: "standing_ready"))

        return root

class NPCManager:
    """Manages all NPCs in the game world"""

    def __init__(self):
        self.npcs: Dict[str, NPC] = {}
        self.behavior_tree_builder = NPCBehaviorTreeBuilder()
        self.global_events: List[Dict[str, Any]] = []

    def create_npc(self, name: str, role: NPCRole, location: str, **kwargs) -> NPC:
        """Create a new NPC"""
        npc_id = str(uuid.uuid4())

        # Set default schedule based on role
        schedule = self._generate_default_schedule(role)

        # Create behavior tree based on role
        behavior_tree = self._create_behavior_tree(role)

        # Set personality based on role
        personality = self._generate_personality(role)

        npc = NPC(
            id=npc_id,
            name=name,
            role=role,
            current_location=location,
            daily_schedule=schedule,
            behavior_tree=behavior_tree,
            personality=personality,
            **kwargs
        )

        self.npcs[npc_id] = npc
        return npc

    def _generate_default_schedule(self, role: NPCRole) -> List[ScheduleEntry]:
        """Generate default daily schedule based on role"""
        schedules = {
            NPCRole.VILLAGER: [
                ScheduleEntry(time(6, 0), time(8, 0), Activity.WORKING, "farm"),
                ScheduleEntry(time(12, 0), time(13, 0), Activity.EATING, "home"),
                ScheduleEntry(time(13, 0), time(18, 0), Activity.WORKING, "farm"),
                ScheduleEntry(time(18, 0), time(20, 0), Activity.EATING, "home"),
                ScheduleEntry(time(20, 0), time(22, 0), Activity.SOCIALIZING, "tavern"),
                ScheduleEntry(time(22, 0), time(6, 0), Activity.SLEEPING, "home")
            ],
            NPCRole.MERCHANT: [
                ScheduleEntry(time(7, 0), time(8, 0), Activity.EATING, "home"),
                ScheduleEntry(time(8, 0), time(18, 0), Activity.WORKING, "shop"),
                ScheduleEntry(time(18, 0), time(19, 0), Activity.EATING, "home"),
                ScheduleEntry(time(19, 0), time(22, 0), Activity.SOCIALIZING, "tavern"),
                ScheduleEntry(time(22, 0), time(7, 0), Activity.SLEEPING, "home")
            ],
            NPCRole.GUARD: [
                ScheduleEntry(time(6, 0), time(7, 0), Activity.EATING, "barracks"),
                ScheduleEntry(time(7, 0), time(13, 0), Activity.GUARDING, "town_gate"),
                ScheduleEntry(time(13, 0), time(14, 0), Activity.EATING, "barracks"),
                ScheduleEntry(time(14, 0), time(20, 0), Activity.GUARDING, "town_gate"),
                ScheduleEntry(time(20, 0), time(22, 0), Activity.TRAINING, "training_ground"),
                ScheduleEntry(time(22, 0), time(6, 0), Activity.SLEEPING, "barracks")
            ],
            NPCRole.HEALER: [
                ScheduleEntry(time(7, 0), time(8, 0), Activity.EATING, "home"),
                ScheduleEntry(time(8, 0), time(12, 0), Activity.WORKING, "clinic"),
                ScheduleEntry(time(12, 0), time(13, 0), Activity.EATING, "home"),
                ScheduleEntry(time(13, 0), time(18, 0), Activity.WORKING, "clinic"),
                ScheduleEntry(time(18, 0), time(20, 0), Activity.READING, "library"),
                ScheduleEntry(time(20, 0), time(22, 0), Activity.WORSHIP, "temple"),
                ScheduleEntry(time(22, 0), time(7, 0), Activity.SLEEPING, "home")
            ]
        }

        return schedules.get(role, schedules[NPCRole.VILLAGER])

    def _create_behavior_tree(self, role: NPCRole) -> BehaviorNode:
        """Create appropriate behavior tree for role"""
        if role == NPCRole.VILLAGER:
            return self.behavior_tree_builder.create_villager_behavior()
        elif role == NPCRole.MERCHANT:
            return self.behavior_tree_builder.create_merchant_behavior()
        elif role == NPCRole.GUARD:
            return self.behavior_tree_builder.create_guard_behavior()
        else:
            return self.behavior_tree_builder.create_villager_behavior()

    def _generate_personality(self, role: NPCRole) -> Dict[str, float]:
        """Generate personality traits based on role"""
        personalities = {
            NPCRole.VILLAGER: {
                "friendliness": 60,
                "curiosity": 40,
                "bravery": 50,
                "honesty": 70,
                "greed": 30,
                "ambition": 40,
                "patience": 60,
                "humor": 50,
                "intelligence": 50,
                "spirituality": 60
            },
            NPCRole.MERCHANT: {
                "friendliness": 70,
                "curiosity": 60,
                "bravery": 40,
                "honesty": 50,
                "greed": 70,
                "ambition": 80,
                "patience": 70,
                "humor": 60,
                "intelligence": 60,
                "spirituality": 40
            },
            NPCRole.GUARD: {
                "friendliness": 40,
                "curiosity": 30,
                "bravery": 80,
                "honesty": 80,
                "greed": 20,
                "ambition": 50,
                "patience": 60,
                "humor": 40,
                "intelligence": 50,
                "spirituality": 50
            },
            NPCRole.HEALER: {
                "friendliness": 80,
                "curiosity": 60,
                "bravery": 50,
                "honesty": 90,
                "greed": 10,
                "ambition": 40,
                "patience": 80,
                "humor": 50,
                "intelligence": 70,
                "spirituality": 80
            },
            NPCRole.SCHOLAR: {
                "friendliness": 50,
                "curiosity": 90,
                "bravery": 30,
                "honesty": 80,
                "greed": 20,
                "ambition": 70,
                "patience": 80,
                "humor": 40,
                "intelligence": 90,
                "spirituality": 60
            }
        }

        base_personality = personalities.get(role, personalities[NPCRole.VILLAGER])

        # Add some randomness
        return {trait: max(0, min(100, value + random.randint(-10, 10)))
                for trait, value in base_personality.items()}

    def update_all_npcs(self, current_time: datetime, world_context: Dict[str, Any]):
        """Update all NPCs"""
        for npc in self.npcs.values():
            npc.update(current_time, world_context)

    def get_npcs_at_location(self, location: str) -> List[NPC]:
        """Get all NPCs at a specific location"""
        return [npc for npc in self.npcs.values() if npc.current_location == location]

    def get_npcs_by_role(self, role: NPCRole) -> List[NPC]:
        """Get all NPCs with a specific role"""
        return [npc for npc in self.npcs.values() if npc.role == role]

    def create_relationship(self, npc1_id: str, npc2_id: str,
                          relationship_type: RelationshipType,
                          strength: float, trust_level: float):
        """Create relationship between two NPCs"""
        if npc1_id in self.npcs and npc2_id in self.npcs:
            self.npcs[npc1_id].set_relationship(npc2_id, relationship_type, strength, trust_level)
            self.npcs[npc2_id].set_relationship(npc1_id, relationship_type, strength, trust_level)

    def spread_rumor(self, rumor: str, source_npc_id: str, importance: float = 50):
        """Spread rumor through NPC social network"""
        source_npc = self.npcs.get(source_npc_id)
        if not source_npc:
            return

        # NPCs spread rumors to their friends
        for friend_id in source_npc.friends:
            friend = self.npcs.get(friend_id)
            if friend and random.random() < 0.7:  # 70% chance to spread
                friend.add_memory(
                    event_id=f"rumor_{datetime.now().timestamp()}",
                    description=f"Heard a rumor: {rumor}",
                    emotional_impact=random.uniform(-10, 10),
                    importance=importance,
                    associated_npcs=[source_npc_id],
                    tags=["rumor", "social"]
                )

    def handle_global_event(self, event: Dict[str, Any]):
        """Handle global events affecting NPCs"""
        self.global_events.append(event)

        # NPCs react to global events based on their personality and role
        for npc in self.npcs.values():
            impact = self._calculate_event_impact(npc, event)
            if impact != 0:
                npc.add_memory(
                    event_id=event.get("id", f"event_{datetime.now().timestamp()}"),
                    description=event.get("description", "Something important happened"),
                    emotional_impact=impact,
                    importance=event.get("importance", 50),
                    tags=["global_event", event.get("type", "unknown")]
                )

    def _calculate_event_impact(self, npc: NPC, event: Dict[str, Any]) -> float:
        """Calculate how much a global event impacts an NPC"""
        base_impact = event.get("base_impact", 0)

        # Modify based on personality
        if event.get("type") == "conflict":
            if npc.personality["bravery"] > 70:
                base_impact *= 1.5
            if npc.personality["bravery"] < 30:
                base_impact *= 2.0  # Fear amplifies impact
        elif event.get("type") == "economic":
            if npc.role == NPCRole.MERCHANT:
                base_impact *= 2.0
            if npc.personality["greed"] > 70:
                base_impact *= 1.3
        elif event.get("type") == "social":
            if npc.personality["friendliness"] > 70:
                base_impact *= 1.5

        return base_impact

    def generate_world_state_report(self) -> Dict[str, Any]:
        """Generate comprehensive world state report"""
        mood_distribution = {}
        role_distribution = {}
        location_distribution = {}
        activity_distribution = {}

        for npc in self.npcs.values():
            # Count moods
            mood = npc.current_mood.value
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1

            # Count roles
            role = npc.role.value
            role_distribution[role] = role_distribution.get(role, 0) + 1

            # Count locations
            location = npc.current_location
            location_distribution[location] = location_distribution.get(location, 0) + 1

            # Count activities
            activity = npc.current_activity.value
            activity_distribution[activity] = activity_distribution.get(activity, 0) + 1

        return {
            "total_npcs": len(self.npcs),
            "mood_distribution": mood_distribution,
            "role_distribution": role_distribution,
            "location_distribution": location_distribution,
            "activity_distribution": activity_distribution,
            "average_happiness": sum(npc.happiness for npc in self.npcs.values()) / len(self.npcs) if self.npcs else 0,
            "average_energy": sum(npc.energy for npc in self.npcs.values()) / len(self.npcs) if self.npcs else 0,
            "recent_global_events": len([e for e in self.global_events
                                       if (datetime.now() - datetime.fromisoformat(e.get("timestamp", "1970-01-01"))).days < 1])
        }

# Example usage and testing
if __name__ == "__main__":
    manager = NPCManager()

    # Create some NPCs
    merchant = manager.create_npc("Thomas Blackwood", NPCRole.MERCHANT, "shop")
    guard = manager.create_npc("Captain Marcus", NPCRole.GUARD, "town_gate")
    healer = manager.create_npc(" Sister Mary", NPCRole.HEALER, "clinic")

    # Create relationships
    manager.create_relationship(merchant.id, guard.id, RelationshipType.FRIEND, 60, 70)
    manager.create_relationship(healer.id, merchant.id, RelationshipType.CUSTOMER, 40, 80)

    # Simulate world update
    current_time = datetime.now()
    world_context = {"threat_level": 2, "suspicious_activity": False}

    manager.update_all_npcs(current_time, world_context)

    # Generate dialogues
    print(f"{merchant.name}: {merchant.generate_dialogue({})}")
    print(f"{guard.name}: {guard.generate_dialogue({})}")
    print(f"{healer.name}: {healer.generate_dialogue({})}")

    # Handle global event
    manager.handle_global_event({
        "id": "festival_announced",
        "type": "social",
        "description": "Annual harvest festival announced",
        "base_impact": 20,
        "importance": 60
    })

    # Generate world report
    report = manager.generate_world_state_report()
    print(f"\nWorld State Report:")
    print(f"Total NPCs: {report['total_npcs']}")
    print(f"Average Happiness: {report['average_happiness']:.1f}")
    print(f"Mood Distribution: {report['mood_distribution']}")
    print(f"Activity Distribution: {report['activity_distribution']}")