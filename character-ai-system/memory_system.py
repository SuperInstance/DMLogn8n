"""
Memory & Learning System
Short-term memory, long-term memory, relationship tracking, and pattern recognition
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random

from character_profile import CharacterProfile


class MemoryType(Enum):
    """Types of memories"""
    COMBAT = "combat"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    ITEM = "item"
    LOCATION = "location"
    PERSON = "person"
    SKILL = "skill"
    TRAUMA = "trauma"
    SUCCESS = "success"
    FAILURE = "failure"


class MemoryImportance(Enum):
    """Importance levels for memories"""
    TRIVIAL = 1
    MINOR = 2
    MODERATE = 3
    SIGNIFICANT = 4
    CRITICAL = 5
    LIFE_CHANGING = 6


@dataclass
class Memory:
    """Individual memory entry"""
    id: str
    type: MemoryType
    importance: MemoryImportance
    content: Dict[str, Any]
    timestamp: datetime
    emotional_impact: float  # 0-1 scale
    associated_entities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    decay_rate: float = 0.1  # How quickly memory fades
    recall_count: int = 0
    last_recalled: Optional[datetime] = None


@dataclass
class Relationship:
    """Relationship with another character"""
    character_name: str
    relationship_score: float  # -1 to 1 scale
    trust_level: float  # 0-1 scale
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    known_traits: Dict[str, Any] = field(default_factory=dict)
    last_interaction: Optional[datetime] = None
    relationship_type: str = "neutral"  # enemy, ally, friend, rival, etc.


@dataclass
class Pattern:
    """Recognized pattern for learning"""
    pattern_type: str
    conditions: Dict[str, Any]
    outcomes: List[Dict[str, Any]]
    success_rate: float
    confidence: float
    last_used: Optional[datetime] = None
    usage_count: int = 0


class MemorySystem:
    """Comprehensive memory and learning system"""

    def __init__(self, character_profile: CharacterProfile):
        self.profile = character_profile

        # Memory storage
        self.short_term_memory: List[Memory] = []
        self.long_term_memory: List[Memory] = []
        self.working_memory: Dict[str, Any] = {}  # Current active thoughts

        # Relationship tracking
        self.relationships: Dict[str, Relationship] = {}

        # Knowledge bases
        self.location_knowledge: Dict[str, Dict[str, Any]] = {}
        self.item_knowledge: Dict[str, Dict[str, Any]] = {}
        self.person_knowledge: Dict[str, Dict[str, Any]] = {}

        # Pattern recognition
        self.recognized_patterns: List[Pattern] = []
        self.strategic_patterns: Dict[str, List[Pattern]] = {}

        # Learning parameters
        self.memory_capacity = 1000  # Maximum long-term memories
        self.short_term_capacity = 20  # Maximum short-term memories
        self.decay_factor = 0.1  # Memory decay rate
        self.consolidation_threshold = 0.7  # Importance threshold for long-term storage

        # Personality influences on memory
        self.memory_bias = self._calculate_memory_bias()

    def _calculate_memory_bias(self) -> Dict[str, float]:
        """Calculate memory biases based on character attributes"""
        biases = {
            "emotional_weight": 0.5,
            "detail_retention": 0.5,
            "social_memory": 0.5,
            "combat_memory": 0.5,
            "trauma_retention": 0.5
        }

        # Intelligence affects detail retention
        int_modifier = (self.profile.intelligence - 10) / 10
        biases["detail_retention"] += int_modifier * 0.1

        # Wisdom affects pattern recognition
        wis_modifier = (self.profile.wisdom - 10) / 10
        biases["pattern_recognition"] = 0.5 + wis_modifier * 0.1

        # Charisma affects social memory
        cha_modifier = (self.profile.charisma - 10) / 10
        biases["social_memory"] += cha_modifier * 0.1

        # Class influences
        if self.profile.character_class in ["Wizard", "Sage"]:
            biases["detail_retention"] += 0.2
        elif self.profile.character_class in ["Bard", "Cleric"]:
            biases["social_memory"] += 0.2
        elif self.profile.character_class in ["Fighter", "Barbarian"]:
            biases["combat_memory"] += 0.2

        return biases

    def add_memory(self, memory_type: MemoryType, content: Dict[str, Any],
                   importance: MemoryImportance = MemoryImportance.MODERATE,
                   emotional_impact: float = 0.5, tags: List[str] = None) -> str:
        """Add a new memory to the system"""
        memory_id = f"mem_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        memory = Memory(
            id=memory_id,
            type=memory_type,
            importance=importance,
            content=content,
            timestamp=datetime.now(),
            emotional_impact=emotional_impact * self.memory_bias["emotional_weight"],
            associated_entities=content.get("entities", []),
            tags=tags or [],
            decay_rate=self._calculate_decay_rate(importance)
        )

        # Add to appropriate memory store
        if importance.value >= self.consolidation_threshold:
            self._add_to_long_term_memory(memory)
        else:
            self._add_to_short_term_memory(memory)

        # Update knowledge bases
        self._update_knowledge_bases(memory)

        return memory_id

    def _calculate_decay_rate(self, importance: MemoryImportance) -> float:
        """Calculate memory decay rate based on importance"""
        base_decay = 0.1
        importance_factor = (6 - importance.value) * 0.02
        return base_decay + importance_factor

    def _add_to_short_term_memory(self, memory: Memory) -> None:
        """Add memory to short-term storage"""
        self.short_term_memory.append(memory)

        # Maintain capacity limit
        if len(self.short_term_memory) > self.short_term_capacity:
            # Remove oldest/least important memory
            self.short_term_memory.sort(key=lambda m: (m.importance.value, m.timestamp))
            self.short_term_memory.pop(0)

    def _add_to_long_term_memory(self, memory: Memory) -> None:
        """Add memory to long-term storage"""
        self.long_term_memory.append(memory)

        # Maintain capacity limit
        if len(self.long_term_memory) > self.memory_capacity:
            self._decay_long_term_memories()

    def _decay_long_term_memories(self) -> None:
        """Remove or weaken old long-term memories"""
        # Sort by importance and recency
        self.long_term_memory.sort(
            key=lambda m: (m.importance.value, m.timestamp, m.recall_count),
            reverse=True
        )

        # Keep only the most important memories
        if len(self.long_term_memory) > self.memory_capacity:
            excess = len(self.long_term_memory) - self.memory_capacity
            self.long_term_memory = self.long_term_memory[:-excess]

        # Apply decay to remaining memories
        for memory in self.long_term_memory:
            days_old = (datetime.now() - memory.timestamp).days
            if days_old > 30:  # Start decaying after a month
                decay_amount = memory.decay_rate * (days_old / 30)
                memory.emotional_impact = max(0.1, memory.emotional_impact - decay_amount)

    def get_relevant_memories(self, context: Dict[str, Any], limit: int = 5) -> List[Memory]:
        """Get memories relevant to current context"""
        relevant_memories = []

        # Search through all memory stores
        all_memories = self.short_term_memory + self.long_term_memory

        for memory in all_memories:
            relevance_score = self._calculate_relevance(memory, context)
            if relevance_score > 0.3:  # Relevance threshold
                memory.relevance_score = relevance_score
                relevant_memories.append(memory)

        # Sort by relevance and return top memories
        relevant_memories.sort(key=lambda m: m.relevance_score, reverse=True)
        return relevant_memories[:limit]

    def _calculate_relevance(self, memory: Memory, context: Dict[str, Any]) -> float:
        """Calculate relevance score of memory to context"""
        relevance = 0.0

        # Type relevance
        context_type = context.get("type", "")
        if memory.type.value in context_type:
            relevance += 0.5

        # Entity overlap
        context_entities = set(context.get("entities", []))
        memory_entities = set(memory.associated_entities)
        entity_overlap = len(context_entities & memory_entities)
        if entity_overlap > 0:
            relevance += entity_overlap * 0.2

        # Tag matching
        context_tags = set(context.get("tags", []))
        memory_tags = set(memory.tags)
        tag_overlap = len(context_tags & memory_tags)
        if tag_overlap > 0:
            relevance += tag_overlap * 0.1

        # Time recency bonus
        days_old = (datetime.now() - memory.timestamp).days
        if days_old < 1:
            relevance += 0.3
        elif days_old < 7:
            relevance += 0.2
        elif days_old < 30:
            relevance += 0.1

        # Recall frequency bonus
        relevance += min(0.2, memory.recall_count * 0.05)

        return min(1.0, relevance)

    def update_relationship(self, character_name: str, interaction: Dict[str, Any]) -> None:
        """Update relationship with another character"""
        if character_name not in self.relationships:
            self.relationships[character_name] = Relationship(
                character_name=character_name,
                relationship_score=0.0,
                trust_level=0.5
            )

        relationship = self.relationships[character_name]

        # Record interaction
        interaction_record = {
            "timestamp": datetime.now(),
            "type": interaction.get("type", "unknown"),
            "outcome": interaction.get("outcome", "neutral"),
            "emotional_impact": interaction.get("emotional_impact", 0.0)
        }
        relationship.interaction_history.append(interaction_record)

        # Update relationship score based on interaction
        outcome = interaction.get("outcome", "neutral")
        if outcome == "positive":
            relationship.relationship_score += 0.1
            relationship.trust_level += 0.1
        elif outcome == "negative":
            relationship.relationship_score -= 0.15
            relationship.trust_level -= 0.1
        elif outcome == "very_positive":
            relationship.relationship_score += 0.25
            relationship.trust_level += 0.2
        elif outcome == "very_negative":
            relationship.relationship_score -= 0.3
            relationship.trust_level -= 0.2

        # Clamp values
        relationship.relationship_score = max(-1.0, min(1.0, relationship.relationship_score))
        relationship.trust_level = max(0.0, min(1.0, relationship.trust_level))

        # Update relationship type
        if relationship.relationship_score > 0.7:
            relationship.relationship_type = "friend"
        elif relationship.relationship_score > 0.3:
            relationship.relationship_type = "ally"
        elif relationship.relationship_score < -0.7:
            relationship.relationship_type = "enemy"
        elif relationship.relationship_score < -0.3:
            relationship.relationship_type = "rival"
        else:
            relationship.relationship_type = "neutral"

        relationship.last_interaction = datetime.now()

        # Keep interaction history manageable
        if len(relationship.interaction_history) > 20:
            relationship.interaction_history = relationship.interaction_history[-20:]

    def get_relationship_change(self, character_name: str) -> Dict[str, Any]:
        """Get recent changes in relationship"""
        if character_name not in self.relationships:
            return {"status": "no_relationship"}

        relationship = self.relationships[character_name]
        recent_interactions = relationship.interaction_history[-5:] if relationship.interaction_history else []

        return {
            "character": character_name,
            "relationship_score": relationship.relationship_score,
            "trust_level": relationship.trust_level,
            "relationship_type": relationship.relationship_type,
            "recent_interactions": len(recent_interactions),
            "last_interaction": relationship.last_interaction
        }

    def record_decision(self, decision_record: Dict[str, Any]) -> None:
        """Record a decision for learning"""
        memory_content = {
            "decision": decision_record["decision"],
            "state": decision_record["state"],
            "outcome": "pending"
        }

        self.add_memory(
            memory_type=MemoryType.COMBAT if decision_record["state"].combat_status else MemoryType.SKILL,
            content=memory_content,
            importance=MemoryImportance.MODERATE,
            tags=["decision"]
        )

    def record_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Record the outcome of an action for learning"""
        memory_content = {
            "action": action,
            "outcome": outcome,
            "success": outcome.get("success", False),
            "effectiveness": outcome.get("effectiveness", 0.5)
        }

        # Determine memory importance based on outcome
        if outcome.get("success", False) and outcome.get("effectiveness", 0) > 0.8:
            importance = MemoryImportance.SIGNIFICANT
        elif not outcome.get("success", False) and outcome.get("traumatic", False):
            importance = MemoryImportance.CRITICAL
        else:
            importance = MemoryImportance.MODERATE

        self.add_memory(
            memory_type=MemoryType.SUCCESS if outcome.get("success", False) else MemoryType.FAILURE,
            content=memory_content,
            importance=importance,
            emotional_impact=outcome.get("emotional_impact", 0.5),
            tags=["outcome", action]
        )

        # Update patterns
        self._update_patterns(action, outcome)

    def _update_patterns(self, action: str, outcome: Dict[str, Any]) -> None:
        """Update recognized patterns based on new outcome"""
        # Find similar existing patterns
        similar_patterns = self._find_similar_patterns(action, outcome)

        if similar_patterns:
            # Update existing patterns
            for pattern in similar_patterns:
                pattern.outcomes.append(outcome)
                pattern.usage_count += 1
                pattern.last_used = datetime.now()
                pattern.success_rate = sum(1 for o in pattern.outcomes if o.get("success", False)) / len(pattern.outcomes)
        else:
            # Create new pattern if enough data
            if len(self._get_recent_similar_actions(action, outcome)) >= 3:
                new_pattern = Pattern(
                    pattern_type=action,
                    conditions=outcome.get("situation", {}),
                    outcomes=[outcome],
                    success_rate=1.0 if outcome.get("success", False) else 0.0,
                    confidence=0.3,
                    last_used=datetime.now(),
                    usage_count=1
                )
                self.recognized_patterns.append(new_pattern)

    def _find_similar_patterns(self, action: str, outcome: Dict[str, Any]) -> List[Pattern]:
        """Find patterns similar to current action and outcome"""
        similar_patterns = []
        situation = outcome.get("situation", {})

        for pattern in self.recognized_patterns:
            if pattern.pattern_type == action:
                similarity = self._calculate_pattern_similarity(pattern.conditions, situation)
                if similarity > 0.6:
                    similar_patterns.append(pattern)

        return similar_patterns

    def _calculate_pattern_similarity(self, conditions1: Dict[str, Any], conditions2: Dict[str, Any]) -> float:
        """Calculate similarity between two condition dictionaries"""
        if not conditions1 or not conditions2:
            return 0.0

        common_keys = set(conditions1.keys()) & set(conditions2.keys())
        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            if conditions1[key] == conditions2[key]:
                matches += 1

        return matches / len(common_keys)

    def _get_recent_similar_actions(self, action: str, outcome: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recent similar actions and outcomes"""
        recent_memories = [m for m in self.long_term_memory if action in str(m.content)]
        return [m.content for m in recent_memories[-10:]]

    def _update_knowledge_bases(self, memory: Memory) -> None:
        """Update specific knowledge bases based on memory type"""
        if memory.type == MemoryType.LOCATION:
            location_name = memory.content.get("name", "unknown")
            self.location_knowledge[location_name] = memory.content

        elif memory.type == MemoryType.ITEM:
            item_name = memory.content.get("name", "unknown")
            self.item_knowledge[item_name] = memory.content

        elif memory.type == MemoryType.PERSON:
            person_name = memory.content.get("name", "unknown")
            self.person_knowledge[person_name] = memory.content

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of memory system status"""
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_memory),
            "relationships_count": len(self.relationships),
            "patterns_count": len(self.recognized_patterns),
            "location_knowledge": len(self.location_knowledge),
            "item_knowledge": len(self.item_knowledge),
            "person_knowledge": len(self.person_knowledge)
        }

    def get_relevant_patterns(self, situation: Dict[str, Any]) -> List[Pattern]:
        """Get patterns relevant to current situation"""
        relevant_patterns = []

        for pattern in self.recognized_patterns:
            similarity = self._calculate_pattern_similarity(pattern.conditions, situation)
            if similarity > 0.5 and pattern.success_rate > 0.6:
                pattern.relevance = similarity
                relevant_patterns.append(pattern)

        # Sort by success rate and relevance
        relevant_patterns.sort(key=lambda p: (p.success_rate, p.relevance), reverse=True)
        return relevant_patterns[:5]

    def consolidate_memories(self) -> None:
        """Consolidate short-term memories into long-term storage"""
        for memory in self.short_term_memory[:]:  # Copy list to avoid modification during iteration
            if memory.importance.value >= self.consolidation_threshold:
                self.short_term_memory.remove(memory)
                self._add_to_long_term_memory(memory)
            elif (datetime.now() - memory.timestamp).hours > 24:  # Older than a day
                # Check if memory should be kept based on recall frequency
                if memory.recall_count < 2:
                    self.short_term_memory.remove(memory)
                else:
                    # Promote to long-term due to frequent recall
                    self.short_term_memory.remove(memory)
                    self._add_to_long_term_memory(memory)

    def recall_memory(self, memory_id: str) -> Optional[Memory]:
        """Recall a specific memory and update its stats"""
        # Search in short-term memory first
        for memory in self.short_term_memory:
            if memory.id == memory_id:
                memory.recall_count += 1
                memory.last_recalled = datetime.now()
                return memory

        # Search in long-term memory
        for memory in self.long_term_memory:
            if memory.id == memory_id:
                memory.recall_count += 1
                memory.last_recalled = datetime.now()
                return memory

        return None