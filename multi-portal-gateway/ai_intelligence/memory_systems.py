#!/usr/bin/env python3
"""
Advanced Memory Systems for DMLogn8n AI Agents

This module implements sophisticated memory systems that mimic human memory processes
including working memory, episodic memory, semantic memory, and procedural memory.
The system includes forgetting mechanisms, memory consolidation, and efficient
retrieval processes.

Key Features:
- Working memory with limited capacity and rapid decay
- Episodic memory for personal experiences and events
- Semantic memory for facts and general knowledge
- Procedural memory for skills and procedures
- Memory consolidation during rest periods
- Adaptive forgetting mechanisms
- Context-dependent retrieval
- Memory interference and priming effects
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
import pickle
import hashlib
from collections import defaultdict, deque
import math
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory in the system"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryStrength(Enum):
    """Strength levels for memories"""
    VERY_WEAK = 0.1
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    VERY_STRONG = 1.0

class ForgettingCurve(Enum):
    """Types of forgetting curves"""
    EXPONENTIAL = "exponential"
    POWER = "power"
    LOGARITHMIC = "logarithmic"
    LINEAR = "linear"

@dataclass
class MemoryTrace:
    """Represents a single memory trace"""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    strength: float = 0.5
    importance: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    associations: Set[str] = field(default_factory=set)
    forgetting_curve: ForgettingCurve = ForgettingCurve.EXPONENTIAL
    decay_rate: float = 0.1
    consolidation_level: float = 0.0
    retrieval_cues: List[str] = field(default_factory=list)

@dataclass
class EpisodicMemory(MemoryTrace):
    """Episodic memory with temporal and spatial context"""
    event_sequence: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    duration: Optional[timedelta] = None
    emotional_valence: float = 0.0
    emotional_arousal: float = 0.0
    outcome: Optional[str] = None

@dataclass
class SemanticMemory(MemoryTrace):
    """Semantic memory for facts and knowledge"""
    category: str = ""
    subcategory: str = ""
    definition: str = ""
    examples: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.5
    source_reliability: float = 0.5

@dataclass
class ProceduralMemory(MemoryTrace):
    """Procedural memory for skills and procedures"""
    skill_name: str = ""
    steps: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    practice_count: int = 0
    mastery_level: float = 0.0
    error_rate: float = 1.0
    execution_time: Optional[float] = None

@dataclass
class WorkingMemoryItem:
    """Item in working memory with limited duration"""
    content: Any
    timestamp: datetime
    decay_rate: float = 0.5
    importance: float = 0.5
    position: int = 0
    refreshed: bool = False

class MemoryEncoder(nn.Module):
    """Neural network for encoding memories into vector representations"""

    def __init__(self, input_dim: int = 512, hidden_dim: int = 256, output_dim: int = 128):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Encoding layers
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh()
        )

        # Context encoding
        self.context_encoder = nn.Sequential(
            nn.Linear(64, 32),  # Context vector size
            nn.ReLU(),
            nn.Linear(32, output_dim),
            nn.Tanh()
        )

        # Attention for multi-modal encoding
        self.attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=8,
            batch_first=True
        )

    def forward(self, content_embedding, context_embedding):
        """Encode memory content and context"""
        # Encode content
        content_encoded = self.encoder(content_embedding)

        # Encode context
        context_encoded = self.context_encoder(context_embedding)

        # Apply attention
        combined = torch.stack([content_encoded, context_encoded], dim=1)
        attended, _ = self.attention(combined, combined, combined)

        # Return combined representation
        return attended.mean(dim=1)

class MemoryRetriever(nn.Module):
    """Neural network for efficient memory retrieval"""

    def __init__(self, embedding_dim: int = 128, num_memories: int = 10000):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_memories = num_memories

        # Query processing
        self.query_processor = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim)
        )

        # Memory database (simulated)
        self.memory_embeddings = nn.Parameter(
            torch.randn(num_memories, embedding_dim) * 0.1
        )

        # Retrieval scoring
        self.scoring_network = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, query_embedding, memory_indices=None):
        """Retrieve memories based on query"""
        # Process query
        processed_query = self.query_processor(query_embedding)

        if memory_indices is None:
            # Retrieve from all memories
            memory_embeddings = self.memory_embeddings
        else:
            # Retrieve from specific memories
            memory_embeddings = self.memory_embeddings[memory_indices]

        # Calculate similarities
        similarities = F.cosine_similarity(
            processed_query.unsqueeze(1),
            memory_embeddings.unsqueeze(0),
            dim=-1
        )

        # Score retrieval
        query_expanded = processed_query.unsqueeze(1).expand(-1, memory_embeddings.size(0), -1)
        combined = torch.cat([query_expanded, memory_embeddings.unsqueeze(0)], dim=-1)
        scores = self.scoring_network(combined).squeeze(-1)

        # Combine similarity and scores
        final_scores = similarities * scores

        return final_scores, similarities

class ForgettingMechanism:
    """Handles memory forgetting and decay processes"""

    def __init__(self, default_curve: ForgettingCurve = ForgettingCurve.EXPONENTIAL):
        self.default_curve = default_curve
        self.curve_parameters = {
            ForgettingCurve.EXPONENTIAL: {'rate': 0.1, 'offset': 0.0},
            ForgettingCurve.POWER: {'exponent': 0.5, 'coefficient': 1.0},
            ForgettingCurve.LOGARITHMIC: {'base': 2.0, 'coefficient': 1.0},
            ForgettingCurve.LINEAR: {'rate': 0.05, 'minimum': 0.1}
        }

    def calculate_decay(self, memory: MemoryTrace, time_elapsed: timedelta) -> float:
        """Calculate memory strength decay based on forgetting curve"""
        hours_elapsed = time_elapsed.total_seconds() / 3600

        if memory.forgetting_curve == ForgettingCurve.EXPONENTIAL:
            params = self.curve_parameters[ForgettingCurve.EXPONENTIAL]
            decay = math.exp(-params['rate'] * hours_elapsed) + params['offset']

        elif memory.forgetting_curve == ForgettingCurve.POWER:
            params = self.curve_parameters[ForgettingCurve.POWER]
            decay = params['coefficient'] / (hours_elapsed ** params['exponent'] + 1)

        elif memory.forgetting_curve == ForgettingCurve.LOGARITHMIC:
            params = self.curve_parameters[ForgettingCurve.LOGARITHMIC]
            decay = params['coefficient'] / math.log(hours_elapsed + params['base'])

        elif memory.forgetting_curve == ForgettingCurve.LINEAR:
            params = self.curve_parameters[ForgettingCurve.LINEAR]
            decay = max(1.0 - params['rate'] * hours_elapsed, params['minimum'])

        else:
            decay = 0.5  # Default

        return max(decay, 0.01)  # Minimum strength

    def apply_forgetting(self, memory: MemoryTrace):
        """Apply forgetting to a memory"""
        if memory.last_accessed:
            time_elapsed = datetime.now() - memory.last_accessed
        else:
            time_elapsed = datetime.now() - memory.timestamp

        decay_factor = self.calculate_decay(memory, time_elapsed)
        memory.strength *= decay_factor

        # Additional factors affecting forgetting
        if memory.importance > 0.7:
            memory.strength *= 1.2  # Important memories decay slower

        if memory.access_count > 5:
            memory.strength *= 1.1  # Frequently accessed memories decay slower

        memory.strength = min(memory.strength, 1.0)

class ConsolidationSystem:
    """Handles memory consolidation processes"""

    def __init__(self, consolidation_interval: int = 60):
        self.consolidation_interval = consolidation_interval
        self.consolidation_queue = deque(maxlen=100)
        self.last_consolidation = datetime.now()

    def queue_for_consolidation(self, memory: MemoryTrace):
        """Queue a memory for consolidation"""
        self.consolidation_queue.append(memory)

    def process_consolidation(self) -> List[MemoryTrace]:
        """Process memory consolidation"""
        consolidated = []
        current_time = datetime.now()

        if (current_time - self.last_consolidation).seconds >= self.consolidation_interval:
            while self.consolidation_queue:
                memory = self.consolidation_queue.popleft()

                # Strengthen memory through consolidation
                memory.consolidation_level = min(memory.consolidation_level + 0.1, 1.0)
                memory.strength = min(memory.strength * 1.1, 1.0)
                memory.decay_rate *= 0.95  # Slower decay after consolidation

                # Strengthen associations
                for associated_id in memory.associations:
                    # This would update associated memories in a real system
                    pass

                consolidated.append(memory)

            self.last_consolidation = current_time

        return consolidated

class MemorySystem:
    """
    Advanced Memory System for AI Agents

    This class implements a comprehensive memory system with multiple memory types,
    forgetting mechanisms, consolidation processes, and efficient retrieval.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Initialize neural networks
        self.memory_encoder = MemoryEncoder()
        self.memory_retriever = MemoryRetriever()

        # Memory stores
        self.working_memory = deque(maxlen=self.config['working_memory_capacity'])
        self.episodic_memories = {}  # id -> EpisodicMemory
        self.semantic_memories = {}  # id -> SemanticMemory
        self.procedural_memories = {}  # id -> ProceduralMemory

        # Memory systems
        self.forgetting_mechanism = ForgettingMechanism()
        self.consolidation_system = ConsolidationSystem()

        # Memory management
        self.memory_counter = 0
        self.memory_index = defaultdict(set)  # tags -> memory ids
        self.associations = defaultdict(set)  # memory_id -> associated memory ids

        # Performance metrics
        self.metrics = {
            'total_memories': 0,
            'working_memory_usage': 0,
            'retrieval_accuracy': 0.0,
            'consolidation_efficiency': 0.0,
            'forgetting_rate': 0.0,
            'memory_access_frequency': 0.0
        }

        # Threading
        self.processing_lock = threading.Lock()
        self.background_tasks = set()

        logger.info(f"Memory System initialized for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration for memory system"""
        return {
            'working_memory_capacity': 7,
            'episodic_memory_capacity': 10000,
            'semantic_memory_capacity': 5000,
            'procedural_memory_capacity': 1000,
            'consolidation_interval': 60,
            'forgetting_check_interval': 300,  # 5 minutes
            'retrieval_threshold': 0.3,
            'minimum_memory_strength': 0.01,
            'max_associations_per_memory': 10,
            'enable_spaced_repetition': True,
            'enable_context_dependent_retrieval': True
        }

    def add_working_memory(self, content: Any, importance: float = 0.5) -> str:
        """Add item to working memory"""
        with self.processing_lock:
            memory_id = f"wm_{self.memory_counter}"
            self.memory_counter += 1

            item = WorkingMemoryItem(
                content=content,
                timestamp=datetime.now(),
                importance=importance,
                position=len(self.working_memory)
            )

            self.working_memory.append(item)
            self.metrics['working_memory_usage'] = len(self.working_memory)

            logger.debug(f"Added to working memory: {memory_id}")
            return memory_id

    def add_episodic_memory(self, content: Any, context: Dict[str, Any],
                           emotional_valence: float = 0.0,
                           emotional_arousal: float = 0.0) -> str:
        """Add episodic memory"""
        with self.processing_lock:
            memory_id = f"ep_{self.memory_counter}"
            self.memory_counter += 1

            memory = EpisodicMemory(
                id=memory_id,
                content=content,
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now(),
                context=context,
                emotional_valence=emotional_valence,
                emotional_arousal=emotional_arousal,
                strength=0.5 + emotional_arousal * 0.3,  # Emotional arousal strengthens memory
                importance=context.get('importance', 0.5)
            )

            # Extract participants and location from context
            if 'participants' in context:
                memory.participants = context['participants']
            if 'location' in context:
                memory.location = context['location']

            self.episodic_memories[memory_id] = memory
            self._index_memory(memory)
            self.consolidation_system.queue_for_consolidation(memory)

            self.metrics['total_memories'] += 1

            logger.debug(f"Added episodic memory: {memory_id}")
            return memory_id

    def add_semantic_memory(self, content: Any, category: str, definition: str = "",
                          confidence: float = 0.5, source: str = "") -> str:
        """Add semantic memory"""
        with self.processing_lock:
            memory_id = f"sm_{self.memory_counter}"
            self.memory_counter += 1

            memory = SemanticMemory(
                id=memory_id,
                content=content,
                memory_type=MemoryType.SEMANTIC,
                timestamp=datetime.now(),
                category=category,
                definition=definition,
                confidence=confidence,
                strength=confidence,
                importance=0.5 + confidence * 0.3
            )

            # Add category tag
            memory.tags.add(category)
            if source:
                memory.tags.add(f"source:{source}")

            self.semantic_memories[memory_id] = memory
            self._index_memory(memory)
            self.consolidation_system.queue_for_consolidation(memory)

            self.metrics['total_memories'] += 1

            logger.debug(f"Added semantic memory: {memory_id}")
            return memory_id

    def add_procedural_memory(self, skill_name: str, steps: List[str],
                            conditions: List[str] = None, outcomes: List[str] = None) -> str:
        """Add procedural memory"""
        with self.processing_lock:
            memory_id = f"pm_{self.memory_counter}"
            self.memory_counter += 1

            memory = ProceduralMemory(
                id=memory_id,
                content={'skill_name': skill_name, 'steps': steps},
                memory_type=MemoryType.PROCEDURAL,
                timestamp=datetime.now(),
                skill_name=skill_name,
                steps=steps,
                conditions=conditions or [],
                outcomes=outcomes or [],
                mastery_level=0.1,
                strength=0.3,
                importance=0.6
            )

            # Add skill tag
            memory.tags.add(f"skill:{skill_name}")

            self.procedural_memories[memory_id] = memory
            self._index_memory(memory)

            self.metrics['total_memories'] += 1

            logger.debug(f"Added procedural memory: {memory_id}")
            return memory_id

    def _index_memory(self, memory: MemoryTrace):
        """Index memory for efficient retrieval"""
        # Index by tags
        for tag in memory.tags:
            self.memory_index[tag].add(memory.id)

        # Index by content type
        content_type = type(memory.content).__name__
        self.memory_index[f"type:{content_type}"].add(memory.id)

        # Index by timestamp (hour, day, month)
        timestamp = memory.timestamp
        self.memory_index[f"hour:{timestamp.hour}"].add(memory.id)
        self.memory_index[f"day:{timestamp.day}"].add(memory.id)
        self.memory_index[f"month:{timestamp.month}"].add(memory.id)

    def retrieve_working_memory(self, query: Any = None) -> List[WorkingMemoryItem]:
        """Retrieve items from working memory"""
        # Apply decay to working memory items
        current_time = datetime.now()
        retained_items = []

        for item in self.working_memory:
            time_elapsed = (current_time - item.timestamp).total_seconds()
            decay_factor = math.exp(-item.decay_rate * time_elapsed / 60)  # Per minute

            if decay_factor * item.importance > 0.1:  # Retention threshold
                item.decay_rate *= 0.95  # Slow down decay with access
                retained_items.append(item)

        # Refresh working memory with retained items
        self.working_memory = deque(retained_items, maxlen=self.config['working_memory_capacity'])
        self.metrics['working_memory_usage'] = len(self.working_memory)

        if query is None:
            return list(self.working_memory)

        # Filter by query if provided
        query_str = str(query).lower()
        filtered = []
        for item in self.working_memory:
            if query_str in str(item.content).lower():
                filtered.append(item)

        return filtered

    def retrieve_episodic_memories(self, query: Any = None, context: Dict = None,
                                 limit: int = 10) -> List[EpisodicMemory]:
        """Retrieve episodic memories"""
        candidates = []

        if query is None:
            # Return most recent/strength memories
            candidates = list(self.episodic_memories.values())
        else:
            # Search by content and context
            query_str = str(query).lower()
            for memory in self.episodic_memories.values():
                if (query_str in str(memory.content).lower() or
                    any(query_str in str(v).lower() for v in memory.context.values())):
                    candidates.append(memory)

        # Sort by strength and recency
        candidates.sort(key=lambda m: (m.strength, m.timestamp), reverse=True)

        # Apply context filtering if provided
        if context:
            filtered = []
            for memory in candidates[:limit]:
                context_match = True
                for key, value in context.items():
                    if key in memory.context and memory.context[key] != value:
                        context_match = False
                        break
                if context_match:
                    filtered.append(memory)
            candidates = filtered

        # Update access statistics
        for memory in candidates[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        return candidates[:limit]

    def retrieve_semantic_memories(self, query: Any = None, category: str = None,
                                 limit: int = 10) -> List[SemanticMemory]:
        """Retrieve semantic memories"""
        candidates = []

        if query is None:
            # Return by category if specified, otherwise return strongest
            if category:
                candidates = [m for m in self.semantic_memories.values() if m.category == category]
            else:
                candidates = list(self.semantic_memories.values())
        else:
            # Search by content and category
            query_str = str(query).lower()
            for memory in self.semantic_memories.values():
                if (query_str in str(memory.content).lower() or
                    query_str in memory.category.lower() or
                    query_str in memory.definition.lower()):
                    candidates.append(memory)

        # Sort by confidence and strength
        candidates.sort(key=lambda m: (m.confidence, m.strength), reverse=True)

        # Update access statistics
        for memory in candidates[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        return candidates[:limit]

    def retrieve_procedural_memories(self, skill_name: str = None, limit: int = 10) -> List[ProceduralMemory]:
        """Retrieve procedural memories"""
        candidates = []

        if skill_name is None:
            candidates = list(self.procedural_memories.values())
        else:
            # Search by skill name
            skill_name_lower = skill_name.lower()
            for memory in self.procedural_memories.values():
                if skill_name_lower in memory.skill_name.lower():
                    candidates.append(memory)

        # Sort by mastery level and strength
        candidates.sort(key=lambda m: (m.mastery_level, m.strength), reverse=True)

        # Update access statistics
        for memory in candidates[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        return candidates[:limit]

    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                       limit: int = 20) -> List[MemoryTrace]:
        """Search across all memory types"""
        if memory_types is None:
            memory_types = [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]

        results = []
        query_lower = query.lower()

        if MemoryType.EPISODIC in memory_types:
            for memory in self.episodic_memories.values():
                if self._matches_query(memory, query_lower):
                    results.append(memory)

        if MemoryType.SEMANTIC in memory_types:
            for memory in self.semantic_memories.values():
                if self._matches_query(memory, query_lower):
                    results.append(memory)

        if MemoryType.PROCEDURAL in memory_types:
            for memory in self.procedural_memories.values():
                if self._matches_query(memory, query_lower):
                    results.append(memory)

        # Sort by relevance score
        results.sort(key=lambda m: self._calculate_relevance(m, query_lower), reverse=True)

        return results[:limit]

    def _matches_query(self, memory: MemoryTrace, query: str) -> bool:
        """Check if memory matches query"""
        content_match = query in str(memory.content).lower()

        # Check context match for episodic memories
        context_match = False
        if isinstance(memory, EpisodicMemory):
            context_match = any(
                query in str(value).lower()
                for value in memory.context.values()
            )

        # Check tags
        tag_match = any(query in tag.lower() for tag in memory.tags)

        return content_match or context_match or tag_match

    def _calculate_relevance(self, memory: MemoryTrace, query: str) -> float:
        """Calculate relevance score for memory"""
        relevance = 0.0

        # Content relevance
        content_str = str(memory.content).lower()
        content_words = content_str.split()
        query_words = query.split()

        for word in query_words:
            if word in content_words:
                relevance += 0.3

        # Strength and recency
        relevance += memory.strength * 0.2

        # Importance
        relevance += memory.importance * 0.2

        # Access frequency (recent access)
        if memory.last_accessed:
            days_since_access = (datetime.now() - memory.last_accessed).days
            recency_score = math.exp(-days_since_access / 30)  # 30-day decay
            relevance += recency_score * 0.1

        # Type-specific relevance
        if isinstance(memory, SemanticMemory):
            if memory.confidence > 0.7:
                relevance += 0.2
        elif isinstance(memory, EpisodicMemory):
            if memory.emotional_arousal > 0.5:
                relevance += 0.2
        elif isinstance(memory, ProceduralMemory):
            if memory.mastery_level > 0.5:
                relevance += 0.2

        return min(relevance, 1.0)

    def create_association(self, memory_id1: str, memory_id2: str, strength: float = 0.5):
        """Create association between two memories"""
        with self.processing_lock:
            # Find memories
            memory1 = self._get_memory_by_id(memory_id1)
            memory2 = self._get_memory_by_id(memory_id2)

            if memory1 and memory2:
                memory1.associations.add(memory_id2)
                memory2.associations.add(memory_id1)

                self.associations[memory_id1].add(memory_id2)
                self.associations[memory_id2].add(memory_id1)

                logger.debug(f"Created association between {memory_id1} and {memory_id2}")

    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryTrace]:
        """Get memory by ID across all memory types"""
        if memory_id.startswith('ep_'):
            return self.episodic_memories.get(memory_id)
        elif memory_id.startswith('sm_'):
            return self.semantic_memories.get(memory_id)
        elif memory_id.startswith('pm_'):
            return self.procedural_memories.get(memory_id)
        return None

    def practice_procedural_memory(self, memory_id: str, success: bool = True,
                                 execution_time: float = None):
        """Practice a procedural memory to improve mastery"""
        memory = self.procedural_memories.get(memory_id)
        if not memory:
            return

        memory.practice_count += 1
        memory.last_accessed = datetime.now()

        if success:
            # Improve mastery and reduce error rate
            memory.mastery_level = min(memory.mastery_level + 0.05, 1.0)
            memory.error_rate = max(memory.error_rate - 0.02, 0.0)
            memory.strength = min(memory.strength + 0.1, 1.0)
        else:
            # Failure reduces mastery slightly
            memory.mastery_level = max(memory.mastery_level - 0.02, 0.1)
            memory.error_rate = min(memory.error_rate + 0.05, 1.0)

        if execution_time is not None:
            if memory.execution_time is None:
                memory.execution_time = execution_time
            else:
                # Update execution time with moving average
                memory.execution_time = (memory.execution_time * 0.8 + execution_time * 0.2)

    def apply_forgetting(self):
        """Apply forgetting to all memories"""
        with self.processing_lock:
            all_memories = []

            # Collect all memories
            all_memories.extend(self.episodic_memories.values())
            all_memories.extend(self.semantic_memories.values())
            all_memories.extend(self.procedural_memories.values())

            # Apply forgetting
            forgotten_count = 0
            for memory in all_memories:
                original_strength = memory.strength
                self.forgetting_mechanism.apply_forgetting(memory)

                if memory.strength < self.config['minimum_memory_strength']:
                    # Mark for deletion
                    if memory.id in self.episodic_memories:
                        del self.episodic_memories[memory.id]
                    elif memory.id in self.semantic_memories:
                        del self.semantic_memories[memory.id]
                    elif memory.id in self.procedural_memories:
                        del self.procedural_memories[memory.id]
                    forgotten_count += 1

            if forgotten_count > 0:
                self.metrics['total_memories'] -= forgotten_count
                logger.info(f"Forgotten {forgotten_count} weak memories")

    def process_consolidation(self):
        """Process memory consolidation"""
        consolidated = self.consolidation_system.process_consolidation()
        if consolidated:
            logger.info(f"Consolidated {len(consolidated)} memories")
            self.metrics['consolidation_efficiency'] = len(consolidated)

    def update_metrics(self):
        """Update performance metrics"""
        total_memories = (len(self.episodic_memories) +
                         len(self.semantic_memories) +
                         len(self.procedural_memories))
        self.metrics['total_memories'] = total_memories
        self.metrics['working_memory_usage'] = len(self.working_memory)

        # Calculate memory access frequency
        all_memories = []
        all_memories.extend(self.episodic_memories.values())
        all_memories.extend(self.semantic_memories.values())
        all_memories.extend(self.procedural_memories.values())

        if all_memories:
            avg_access_count = sum(m.access_count for m in all_memories) / len(all_memories)
            self.metrics['memory_access_frequency'] = avg_access_count

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory system summary"""
        return {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'memory_counts': {
                'working': len(self.working_memory),
                'episodic': len(self.episodic_memories),
                'semantic': len(self.semantic_memories),
                'procedural': len(self.procedural_memories),
                'total': self.metrics['total_memories']
            },
            'performance_metrics': self.metrics,
            'consolidation_queue_size': len(self.consolidation_system.consolidation_queue),
            'association_count': len(self.associations),
            'working_memory_items': [
                {
                    'content': str(item.content)[:100],
                    'age_seconds': (datetime.now() - item.timestamp).total_seconds(),
                    'importance': item.importance
                }
                for item in list(self.working_memory)[-3:]  # Last 3 items
            ]
        }

    def save_memories(self, filepath: str):
        """Save memory system to file"""
        with self.processing_lock:
            memory_data = {
                'agent_id': self.agent_id,
                'config': self.config,
                'episodic_memories': {
                    k: self._serialize_memory(v) for k, v in self.episodic_memories.items()
                },
                'semantic_memories': {
                    k: self._serialize_memory(v) for k, v in self.semantic_memories.items()
                },
                'procedural_memories': {
                    k: self._serialize_memory(v) for k, v in self.procedural_memories.items()
                },
                'working_memory': [
                    {
                        'content': item.content,
                        'timestamp': item.timestamp.isoformat(),
                        'importance': item.importance
                    }
                    for item in self.working_memory
                ],
                'associations': dict(self.associations),
                'memory_index': dict(self.memory_index),
                'memory_counter': self.memory_counter,
                'metrics': self.metrics,
                'timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'wb') as f:
                pickle.dump(memory_data, f)

            logger.info(f"Memories saved to {filepath}")

    def load_memories(self, filepath: str):
        """Load memory system from file"""
        try:
            with open(filepath, 'rb') as f:
                memory_data = pickle.load(f)

            self.agent_id = memory_data['agent_id']
            self.config = memory_data['config']
            self.memory_counter = memory_data['memory_counter']
            self.metrics = memory_data['metrics']

            # Load episodic memories
            self.episodic_memories = {}
            for k, v in memory_data['episodic_memories'].items():
                self.episodic_memories[k] = self._deserialize_episodic_memory(v)

            # Load semantic memories
            self.semantic_memories = {}
            for k, v in memory_data['semantic_memories'].items():
                self.semantic_memories[k] = self._deserialize_semantic_memory(v)

            # Load procedural memories
            self.procedural_memories = {}
            for k, v in memory_data['procedural_memories'].items():
                self.procedural_memories[k] = self._deserialize_procedural_memory(v)

            # Load working memory
            self.working_memory = deque(
                [WorkingMemoryItem(
                    content=item['content'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    importance=item['importance']
                ) for item in memory_data['working_memory']],
                maxlen=self.config['working_memory_capacity']
            )

            # Load associations and index
            self.associations = defaultdict(set, memory_data['associations'])
            self.memory_index = defaultdict(set, memory_data['memory_index'])

            logger.info(f"Memories loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading memories: {e}")

    def _serialize_memory(self, memory: MemoryTrace) -> Dict:
        """Serialize memory to dictionary"""
        data = {
            'id': memory.id,
            'content': memory.content,
            'memory_type': memory.memory_type.value,
            'timestamp': memory.timestamp.isoformat(),
            'access_count': memory.access_count,
            'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
            'strength': memory.strength,
            'importance': memory.importance,
            'context': memory.context,
            'tags': list(memory.tags),
            'associations': list(memory.associations),
            'forgetting_curve': memory.forgetting_curve.value,
            'decay_rate': memory.decay_rate,
            'consolidation_level': memory.consolidation_level,
            'retrieval_cues': memory.retrieval_cues
        }

        # Add type-specific fields
        if isinstance(memory, EpisodicMemory):
            data.update({
                'event_sequence': memory.event_sequence,
                'participants': memory.participants,
                'location': memory.location,
                'duration': memory.duration.total_seconds() if memory.duration else None,
                'emotional_valence': memory.emotional_valence,
                'emotional_arousal': memory.emotional_arousal,
                'outcome': memory.outcome
            })
        elif isinstance(memory, SemanticMemory):
            data.update({
                'category': memory.category,
                'subcategory': memory.subcategory,
                'definition': memory.definition,
                'examples': memory.examples,
                'relationships': memory.relationships,
                'confidence': memory.confidence,
                'source_reliability': memory.source_reliability
            })
        elif isinstance(memory, ProceduralMemory):
            data.update({
                'skill_name': memory.skill_name,
                'steps': memory.steps,
                'conditions': memory.conditions,
                'outcomes': memory.outcomes,
                'practice_count': memory.practice_count,
                'mastery_level': memory.mastery_level,
                'error_rate': memory.error_rate,
                'execution_time': memory.execution_time
            })

        return data

    def _deserialize_episodic_memory(self, data: Dict) -> EpisodicMemory:
        """Deserialize episodic memory from dictionary"""
        return EpisodicMemory(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            access_count=data['access_count'],
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data['last_accessed'] else None,
            strength=data['strength'],
            importance=data['importance'],
            context=data['context'],
            tags=set(data['tags']),
            associations=set(data['associations']),
            forgetting_curve=ForgettingCurve(data['forgetting_curve']),
            decay_rate=data['decay_rate'],
            consolidation_level=data['consolidation_level'],
            retrieval_cues=data['retrieval_cues'],
            event_sequence=data['event_sequence'],
            participants=data['participants'],
            location=data['location'],
            duration=timedelta(seconds=data['duration']) if data['duration'] else None,
            emotional_valence=data['emotional_valence'],
            emotional_arousal=data['emotional_arousal'],
            outcome=data['outcome']
        )

    def _deserialize_semantic_memory(self, data: Dict) -> SemanticMemory:
        """Deserialize semantic memory from dictionary"""
        return SemanticMemory(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            access_count=data['access_count'],
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data['last_accessed'] else None,
            strength=data['strength'],
            importance=data['importance'],
            context=data['context'],
            tags=set(data['tags']),
            associations=set(data['associations']),
            forgetting_curve=ForgettingCurve(data['forgetting_curve']),
            decay_rate=data['decay_rate'],
            consolidation_level=data['consolidation_level'],
            retrieval_cues=data['retrieval_cues'],
            category=data['category'],
            subcategory=data['subcategory'],
            definition=data['definition'],
            examples=data['examples'],
            relationships=data['relationships'],
            confidence=data['confidence'],
            source_reliability=data['source_reliability']
        )

    def _deserialize_procedural_memory(self, data: Dict) -> ProceduralMemory:
        """Deserialize procedural memory from dictionary"""
        return ProceduralMemory(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            access_count=data['access_count'],
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data['last_accessed'] else None,
            strength=data['strength'],
            importance=data['importance'],
            context=data['context'],
            tags=set(data['tags']),
            associations=set(data['associations']),
            forgetting_curve=ForgettingCurve(data['forgetting_curve']),
            decay_rate=data['decay_rate'],
            consolidation_level=data['consolidation_level'],
            retrieval_cues=data['retrieval_cues'],
            skill_name=data['skill_name'],
            steps=data['steps'],
            conditions=data['conditions'],
            outcomes=data['outcomes'],
            practice_count=data['practice_count'],
            mastery_level=data['mastery_level'],
            error_rate=data['error_rate'],
            execution_time=data['execution_time']
        )

    async def start_maintenance_tasks(self):
        """Start background maintenance tasks"""
        async def forgetting_task():
            while True:
                try:
                    self.apply_forgetting()
                    self.process_consolidation()
                    self.update_metrics()
                    await asyncio.sleep(self.config['forgetting_check_interval'])
                except Exception as e:
                    logger.error(f"Error in forgetting task: {e}")
                    await asyncio.sleep(60)

        task = asyncio.create_task(forgetting_task())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        logger.info("Started memory maintenance tasks")

    def stop_maintenance_tasks(self):
        """Stop background maintenance tasks"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()
        logger.info("Stopped memory maintenance tasks")

# Utility functions for integration
async def create_memory_system(agent_id: str, config: Optional[Dict] = None) -> MemorySystem:
    """Factory function to create and initialize memory system"""
    system = MemorySystem(agent_id, config)
    await system.start_maintenance_tasks()
    return system

def benchmark_memory_performance(memory_system: MemorySystem,
                               test_data: List[Dict]) -> Dict:
    """Benchmark memory system performance"""
    import time

    start_time = time.time()

    # Test memory addition
    addition_times = []
    for data in test_data:
        add_start = time.time()
        if data['type'] == 'episodic':
            memory_system.add_episodic_memory(
                data['content'], data['context'],
                data.get('emotional_valence', 0),
                data.get('emotional_arousal', 0)
            )
        elif data['type'] == 'semantic':
            memory_system.add_semantic_memory(
                data['content'], data['category'],
                data.get('definition', ''),
                data.get('confidence', 0.5)
            )
        elif data['type'] == 'procedural':
            memory_system.add_procedural_memory(
                data['skill_name'], data['steps'],
                data.get('conditions', []),
                data.get('outcomes', [])
            )
        addition_times.append(time.time() - add_start)

    # Test memory retrieval
    retrieval_times = []
    for _ in range(10):
        retrieve_start = time.time()
        memory_system.retrieve_episodic_memories(limit=5)
        memory_system.retrieve_semantic_memories(limit=5)
        retrieval_times.append(time.time() - retrieve_start)

    total_time = time.time() - start_time

    return {
        'total_test_time': total_time,
        'average_addition_time': np.mean(addition_times),
        'average_retrieval_time': np.mean(retrieval_times),
        'memories_added': len(test_data),
        'addition_rate': len(test_data) / total_time,
        'final_memory_count': memory_system.metrics['total_memories'],
        'performance_metrics': memory_system.metrics
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create memory system
        config = {
            'working_memory_capacity': 7,
            'episodic_memory_capacity': 1000,
            'semantic_memory_capacity': 500,
            'procedural_memory_capacity': 100
        }

        memory_system = await create_memory_system("test_agent", config)

        # Add test memories
        working_id = memory_system.add_working_memory("Current task: debug the system", importance=0.8)

        episodic_id = memory_system.add_episodic_memory(
            content="Had a conversation with a user about AI ethics",
            context={
                'participants': ['user', 'assistant'],
                'location': 'chat_room',
                'importance': 0.7
            },
            emotional_valence=0.3,
            emotional_arousal=0.6
        )

        semantic_id = memory_system.add_semantic_memory(
            content="Python is a high-level programming language",
            category="programming",
            definition="A general-purpose programming language",
            confidence=0.9
        )

        procedural_id = memory_system.add_procedural_memory(
            skill_name="debug_code",
            steps=["identify_error", "analyze_stack_trace", "implement_fix", "test_solution"],
            conditions=["error_detected"],
            outcomes=["bug_resolved"]
        )

        # Create associations
        memory_system.create_association(episodic_id, semantic_id, strength=0.6)

        # Test retrieval
        working_memories = memory_system.retrieve_working_memory()
        episodic_memories = memory_system.retrieve_episodic_memories(limit=5)
        semantic_memories = memory_system.retrieve_semantic_memories(limit=5)
        procedural_memories = memory_system.retrieve_procedural_memories(limit=5)

        print("Working memory items:", len(working_memories))
        print("Episodic memories:", len(episodic_memories))
        print("Semantic memories:", len(semantic_memories))
        print("Procedural memories:", len(procedural_memories))

        # Test search
        search_results = memory_system.search_memories("Python", limit=10)
        print(f"Search results for 'Python': {len(search_results)}")

        # Get memory summary
        summary = memory_system.get_memory_summary()
        print("\nMemory system summary:")
        print(json.dumps(summary, indent=2, default=str))

        # Practice procedural memory
        memory_system.practice_procedural_memory(procedural_id, success=True, execution_time=45.2)

        # Save and load
        memory_system.save_memories("/tmp/test_memories.pkl")

    asyncio.run(main())