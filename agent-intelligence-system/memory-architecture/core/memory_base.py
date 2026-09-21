"""
Memory Base Classes and Data Structures
========================================

Core abstractions and data structures for the hierarchical memory system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import uuid
import hashlib


class MemoryType(Enum):
    """Memory classification types"""
    WORKING = "working"          # Current active thoughts
    EPISODIC = "episodic"        # Specific events and experiences
    SEMANTIC = "semantic"        # General knowledge and patterns
    PROCEDURAL = "procedural"    # Skills and learned behaviors


class MemoryImportance(Enum):
    """Importance levels for memory prioritization"""
    TRIVIAL = 1.0        # Easily forgotten
    ROUTINE = 3.0        # Daily experiences
    NOTABLE = 6.0        # Worth remembering
    SIGNIFICANT = 8.0    # Life events
    CORE = 10.0          # Identity-defining


class MemoryStatus(Enum):
    """Memory lifecycle status"""
    ACTIVE = "active"                    # Currently accessible
    CONSOLIDATING = "consolidating"      # Being transferred to long-term
    ARCHIVED = "archived"               # Long-term storage
    FADING = "fading"                  # Losing importance
    FORGOTTEN = "forgotten"            # No longer accessible


@dataclass
class MemoryMetadata:
    """Rich metadata for memory objects"""
    emotional_valence: float = 0.0        # -1 (negative) to +1 (positive)
    arousal: float = 0.0                  # 0 (calm) to 1 (excited)
    confidence: float = 1.0               # 0 (uncertain) to 1 (certain)
    participants: List[str] = field(default_factory=list)
    location: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    source: str = "experience"             # "experience", "reflection", "consolidation"

    # Temporal information
    creation_time: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    # Consolidation tracking
    consolidation_score: float = 0.0      # Importance for consolidation
    consolidation_count: int = 0         # Times consolidated
    source_memory_ids: List[str] = field(default_factory=list)

    # Network relationships
    related_memory_ids: List[str] = field(default_factory=list)
    contradictory_memory_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "emotional_valence": self.emotional_valence,
            "arousal": self.arousal,
            "confidence": self.confidence,
            "participants": self.participants,
            "location": self.location,
            "context": self.context,
            "tags": self.tags,
            "source": self.source,
            "creation_time": self.creation_time.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "consolidation_score": self.consolidation_score,
            "consolidation_count": self.consolidation_count,
            "source_memory_ids": self.source_memory_ids,
            "related_memory_ids": self.related_memory_ids,
            "contradictory_memory_ids": self.contradictory_memory_ids
        }


@dataclass
class MemoryContent:
    """Structured memory content"""
    primary_content: str                  # Main memory text
    summary: str = ""                     # Brief description
    key_concepts: List[str] = field(default_factory=list)
    extracted_patterns: List[str] = field(default_factory=list)

    # Multimodal content support
    images: List[str] = field(default_factory=list)
    audio: List[str] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)

    def get_text_for_embedding(self) -> str:
        """Get text representation for embedding generation"""
        parts = [self.primary_content]
        if self.summary:
            parts.append(self.summary)
        if self.key_concepts:
            parts.append(" ".join(self.key_concepts))
        if self.extracted_patterns:
            parts.append(" ".join(self.extracted_patterns))
        return " ".join(parts)


class MemoryBase(ABC):
    """Abstract base class for all memory types"""

    def __init__(
        self,
        content: Union[str, MemoryContent],
        memory_type: MemoryType,
        importance: float = 5.0,
        metadata: Optional[MemoryMetadata] = None,
        memory_id: Optional[str] = None
    ):
        # Generate unique ID if not provided
        if memory_id is None:
            content_hash = hashlib.md5(
                f"{content if isinstance(content, str) else content.primary_content}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            memory_id = f"{memory_type.value}_{content_hash}"

        self.id = memory_id
        self.type = memory_type
        self.status = MemoryStatus.ACTIVE

        # Handle content
        if isinstance(content, str):
            self.content = MemoryContent(primary_content=content)
        else:
            self.content = content

        # Set importance
        self.importance = min(max(importance, 1.0), 10.0)

        # Initialize metadata
        self.metadata = metadata or MemoryMetadata()

        # Tracking
        self.creation_time = datetime.now()
        self.modification_time = self.creation_time
        self.version = 1

    @abstractmethod
    def get_capacity_requirement(self) -> int:
        """Return capacity requirement for this memory"""
        pass

    @abstractmethod
    def calculate_retrieval_score(self, query: str, context: Dict[str, Any]) -> float:
        """Calculate retrieval relevance score for given query"""
        pass

    @abstractmethod
    def can_consolidate(self) -> bool:
        """Check if memory can be consolidated to higher tier"""
        pass

    def access(self) -> None:
        """Record memory access"""
        self.metadata.last_accessed = datetime.now()
        self.metadata.access_count += 1

        # Boost importance slightly on access
        self.importance = min(self.importance * 1.02, 10.0)

    def update_content(self, new_content: str, reason: str = "") -> None:
        """Update memory content with tracking"""
        old_content = self.content.primary_content
        self.content.primary_content = new_content
        self.modification_time = datetime.now()
        self.version += 1

        # Log change in context
        self.metadata.context["last_update"] = {
            "timestamp": self.modification_time.isoformat(),
            "reason": reason,
            "old_content_length": len(old_content),
            "new_content_length": len(new_content)
        }

    def add_relationship(self, other_memory_id: str, relationship_type: str = "related") -> None:
        """Add relationship to another memory"""
        if relationship_type == "related":
            if other_memory_id not in self.metadata.related_memory_ids:
                self.metadata.related_memory_ids.append(other_memory_id)
        elif relationship_type == "contradictory":
            if other_memory_id not in self.metadata.contradictory_memory_ids:
                self.metadata.contradictory_memory_ids.append(other_memory_id)

    def decay_importance(self, decay_factor: float = 0.99) -> None:
        """Apply time-based importance decay"""
        days_since_access = 0
        if self.metadata.last_accessed:
            days_since_access = (datetime.now() - self.metadata.last_accessed).days
        else:
            days_since_access = (datetime.now() - self.creation_time).days

        # Apply exponential decay
        decayed_importance = self.importance * (decay_factor ** days_since_access)
        self.importance = max(decayed_importance, 1.0)  # Minimum importance

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary for storage"""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "importance": self.importance,
            "content": {
                "primary_content": self.content.primary_content,
                "summary": self.content.summary,
                "key_concepts": self.content.key_concepts,
                "extracted_patterns": self.content.extracted_patterns,
                "structured_data": self.content.structured_data
            },
            "metadata": self.metadata.to_dict(),
            "creation_time": self.creation_time.isoformat(),
            "modification_time": self.modification_time.isoformat(),
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryBase':
        """Recreate memory from dictionary"""
        # This would be implemented by subclasses
        raise NotImplementedError("Subclasses must implement from_dict")

    def __str__(self) -> str:
        return f"Memory[{self.id}] {self.type.value} (importance: {self.importance:.1f})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class LevelCapacity:
    """Memory capacity configuration based on character level"""
    level: int
    total_memories: int
    working_memory_capacity: int
    consolidation_threshold: float

    @classmethod
    def get_capacity_for_level(cls, level: int) -> 'LevelCapacity':
        """Get capacity configuration for given level"""
        if level <= 4:
            return cls(
                level=level,
                total_memories=50,
                working_memory_capacity=5,
                consolidation_threshold=100.0
            )
        elif level <= 10:
            return cls(
                level=level,
                total_memories=200,
                working_memory_capacity=10,
                consolidation_threshold=200.0
            )
        elif level <= 16:
            return cls(
                level=level,
                total_memories=500,
                working_memory_capacity=15,
                consolidation_threshold=400.0
            )
        else:  # level 17-20
            return cls(
                level=level,
                total_memories=1000,
                working_memory_capacity=25,
                consolidation_threshold=800.0
            )


@dataclass
class MemoryStats:
    """Memory system statistics"""
    total_memories: int = 0
    memories_by_type: Dict[MemoryType, int] = field(default_factory=dict)
    memories_by_status: Dict[MemoryStatus, int] = field(default_factory=dict)
    average_importance: float = 0.0
    total_consolidation_score: float = 0.0
    access_frequency: float = 0.0
    age_distribution: Dict[str, int] = field(default_factory=dict)

    def calculate_health_score(self) -> float:
        """Calculate overall memory system health (0-1)"""
        # Balance between types
        type_balance = min(len(self.memories_by_type) / len(MemoryType), 1.0)

        # Average importance
        importance_health = min(self.average_importance / 6.0, 1.0)

        # Access frequency
        access_health = min(self.access_frequency / 10.0, 1.0)

        # Consolidation readiness
        consolidation_health = min(self.total_consolidation_score / 500.0, 1.0)

        # Weighted average
        return (type_balance * 0.2 + importance_health * 0.3 +
                access_health * 0.25 + consolidation_health * 0.25)