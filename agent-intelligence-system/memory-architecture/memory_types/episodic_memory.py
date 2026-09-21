"""
Episodic Memory Implementation
================================

Episodic memory stores specific events and experiences with rich temporal and contextual information.
This mirrors human episodic memory which captures "what, where, when" information about personal experiences.
"""

import math
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import re

from ..core.memory_base import MemoryBase, MemoryType, MemoryContent, MemoryMetadata


class EpisodicMemory(MemoryBase):
    """
    Episodic memory for specific events and experiences.
    Rich with temporal, spatial, and emotional context.
    """

    def __init__(
        self,
        content: str,
        timestamp: Optional[datetime] = None,
        location: str = "",
        participants: List[str] = None,
        emotional_valence: float = 0.0,
        arousal: float = 0.0,
        importance: float = 5.0,
        context: Dict[str, Any] = None,
        **kwargs
    ):
        # Create rich metadata for episodic memory
        metadata = MemoryMetadata(
            emotional_valence=emotional_valence,
            arousal=arousal,
            participants=participants or [],
            location=location,
            context=context or {},
            source="experience"
        )

        # Create structured content
        memory_content = MemoryContent(
            primary_content=content,
            summary=self._generate_summary(content),
            key_concepts=self._extract_key_concepts(content),
            extracted_patterns=[]
        )

        super().__init__(memory_content, MemoryType.EPISODIC, importance, metadata, **kwargs)

        # Episodic-specific fields
        self.timestamp = timestamp or datetime.now()
        self.event_duration = context.get("duration", 0) if context else 0  # Duration in minutes
        self.event_type = context.get("event_type", "general") if context else "general"

        # Temporal landmarks (significant time markers)
        self.is_temporal_landmark = False
        self.landmark_type = None
        self.landmark_importance = 0.0

        # Episode clustering
        self.episode_cluster_id = None
        self.similar_episodes: List[str] = []

        # Consolidation tracking
        self.consolidation_candidates: List[str] = []
        self.consolidation_attempts = 0
        self.last_consolidation_attempt = None

    def get_capacity_requirement(self) -> int:
        """Return capacity requirement based on content complexity"""
        base_requirement = 10

        # Add requirements for rich content
        content_length = len(self.content.primary_content)
        length_requirement = max(1, content_length // 100)

        context_requirement = len(self.metadata.context) * 2
        participant_requirement = len(self.metadata.participants) * 3

        return base_requirement + length_requirement + context_requirement + participant_requirement

    def calculate_retrieval_score(self, query: str, context: Dict[str, Any]) -> float:
        """Calculate retrieval relevance score with episodic factors"""
        base_score = self._calculate_text_similarity(query)

        # Temporal relevance boost
        if "time_range" in context:
            time_boost = self._calculate_temporal_relevance(context["time_range"])
            base_score *= (1.0 + time_boost * 0.3)

        # Location relevance boost
        if "location" in context and self.metadata.location:
            location_boost = self._calculate_location_relevance(context["location"])
            base_score *= (1.0 + location_boost * 0.2)

        # Participant relevance boost
        if "participants" in context:
            participant_boost = self._calculate_participant_relevance(context["participants"])
            base_score *= (1.0 + participant_boost * 0.2)

        # Emotional relevance boost
        if "emotional_context" in context:
            emotional_boost = self._calculate_emotional_relevance(context["emotional_context"])
            base_score *= (1.0 + emotional_boost * 0.1)

        # Recency decay
        days_old = (datetime.now() - self.timestamp).days
        recency_factor = math.exp(-days_old / 30.0)  # 30-day half-life
        base_score *= recency_factor

        # Importance boost
        importance_factor = self.importance / 10.0
        base_score *= (0.7 + 0.3 * importance_factor)

        return min(base_score, 1.0)

    def can_consolidate(self) -> bool:
        """Check if memory can be consolidated to semantic memory"""
        # Must be old enough (at least 24 hours)
        if (datetime.now() - self.timestamp).total_seconds() < 86400:
            return False

        # Must have sufficient importance
        if self.importance < 6.0:
            return False

        # Must have been accessed multiple times
        if self.metadata.access_count < 2:
            return False

        # Should not be already consolidated
        if self.status.value in ["consolidated", "archived"]:
            return False

        return True

    def mark_as_temporal_landmark(self, landmark_type: str, importance_boost: float = 2.0) -> None:
        """Mark this memory as a temporal landmark"""
        self.is_temporal_landmark = True
        self.landmark_type = landmark_type
        self.landmark_importance = importance_boost
        self.importance = min(self.importance + importance_boost, 10.0)

        # Add landmark tag
        if "temporal_landmark" not in self.metadata.tags:
            self.metadata.tags.append("temporal_landmark")
        if landmark_type not in self.metadata.tags:
            self.metadata.tags.append(landmark_type)

    def calculate_similarity_to(self, other_memory: 'EpisodicMemory') -> float:
        """Calculate similarity to another episodic memory"""
        if not isinstance(other_memory, EpisodicMemory):
            return 0.0

        # Content similarity
        content_sim = self._calculate_text_similarity(other_memory.content.primary_content)

        # Temporal proximity
        time_diff = abs((self.timestamp - other_memory.timestamp).total_seconds())
        time_sim = math.exp(-time_diff / (7 * 24 * 3600))  # 7-day scale

        # Location similarity
        location_sim = 0.0
        if self.metadata.location and other_memory.metadata.location:
            if self.metadata.location.lower() == other_memory.metadata.location.lower():
                location_sim = 1.0
            elif any(word in self.metadata.location.lower()
                    for word in other_memory.metadata.location.lower().split()):
                location_sim = 0.5

        # Participant overlap
        participants1 = set(self.metadata.participants)
        participants2 = set(other_memory.metadata.participants)
        if participants1 and participants2:
            participant_sim = len(participants1 & participants2) / len(participants1 | participants2)
        else:
            participant_sim = 0.0

        # Emotional similarity
        emotional_sim = 1.0 - abs(self.metadata.emotional_valence - other_memory.metadata.emotional_valence)

        # Weighted combination
        total_weight = 0.4 + 0.2 + 0.2 + 0.1 + 0.1
        weighted_sim = (
            content_sim * 0.4 +
            time_sim * 0.2 +
            location_sim * 0.2 +
            participant_sim * 0.1 +
            emotional_sim * 0.1
        ) / total_weight

        return weighted_sim

    def extract_narrative_elements(self) -> Dict[str, Any]:
        """Extract narrative elements from this episodic memory"""
        content = self.content.primary_content.lower()

        # Identify story components
        elements = {
            "setting": self.metadata.location,
            "characters": self.metadata.participants.copy(),
            "conflict": self._extract_conflict(content),
            "resolution": self._extract_resolution(content),
            "emotional_arc": self.metadata.emotional_valence,
            "key_events": self._extract_key_events(content),
            "themes": self._extract_themes(content)
        }

        return elements

    def update_consolidation_score(self, cluster_size: int = 1) -> None:
        """Update consolidation score based on clustering"""
        base_score = self.importance

        # Boost for similar memories (patterns)
        cluster_boost = min(cluster_size * 0.5, 2.0)

        # Boost for access frequency
        access_boost = min(self.metadata.access_count * 0.1, 1.0)

        # Temporal landmark boost
        landmark_boost = self.landmark_importance if self.is_temporal_landmark else 0.0

        # Emotional intensity boost
        emotional_boost = abs(self.metadata.emotional_valence) * 0.5

        self.metadata.consolidation_score = base_score + cluster_boost + access_boost + landmark_boost + emotional_boost

    def _generate_summary(self, content: str) -> str:
        """Generate a brief summary of the content"""
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return content[:100] + "..." if len(content) > 100 else content

        # Return first sentence or first 100 characters
        first_sentence = sentences[0]
        if len(first_sentence) > 100:
            return first_sentence[:100] + "..."
        return first_sentence

    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())

        # Filter out common words
        common_words = {'that', 'this', 'with', 'from', 'they', 'have', 'been', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'after', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'still', 'back', 'through', 'much', 'before', 'well', 'where', 'should', 'years', 'those', 'being', 'under', 'between', 'both', 'however', 'because', 'same', 'again', 'around', 'these', 'many', 'most', 'such', 'going', 'might', 'against', 'while', 'without', 'place', 'again', 'around', 'however', 'every', 'little', 'world', 'very', 'after', 'being', 'only', 'thought', 'where', 'could', 'would', 'make', 'like', 'through', 'back', 'years', 'come', 'people', 'take', 'before', 'good', 'same', 'through', 'just', 'tell', 'know', 'where', 'much', 'well', 'get', 'them', 'make', 'like', 'time', 'very', 'when', 'come', 'here', 'from', 'word', 'also', 'have', 'what', 'your', 'will', 'about', 'which', 'their', 'said', 'each', 'that', 'with', 'this', 'were', 'been', 'they', 'his', 'her', 'she', 'him', 'had', 'not', 'but', 'for', 'are', 'was', 'you', 'can', 'has', 'him', 'old', 'see', 'now', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}

        # Count word frequencies
        word_freq = defaultdict(int)
        for word in words:
            if word not in common_words:
                word_freq[word] += 1

        # Return top 5 most frequent words
        return [word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]

    def _calculate_text_similarity(self, query: str) -> float:
        """Calculate text similarity using simple word overlap"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        content_words = set(re.findall(r'\b\w+\b', self.content.primary_content.lower()))

        if not query_words or not content_words:
            return 0.0

        intersection = len(query_words & content_words)
        union = len(query_words | content_words)

        return intersection / union if union > 0 else 0.0

    def _calculate_temporal_relevance(self, time_range: Dict[str, datetime]) -> float:
        """Calculate temporal relevance to given time range"""
        start_time = time_range.get("start")
        end_time = time_range.get("end")

        if not start_time or not end_time:
            return 0.0

        if start_time <= self.timestamp <= end_time:
            return 1.0  # Perfect match

        # Calculate distance from range
        if self.timestamp < start_time:
            distance = (start_time - self.timestamp).total_seconds()
        else:
            distance = (self.timestamp - end_time).total_seconds()

        # Exponential decay based on distance
        return math.exp(-distance / (7 * 24 * 3600))  # 7-day scale

    def _calculate_location_relevance(self, query_location: str) -> float:
        """Calculate location relevance"""
        if not self.metadata.location or not query_location:
            return 0.0

        if self.metadata.location.lower() == query_location.lower():
            return 1.0

        # Partial match
        query_words = set(query_location.lower().split())
        location_words = set(self.metadata.location.lower().split())

        if query_words & location_words:
            return 0.5

        return 0.0

    def _calculate_participant_relevance(self, query_participants: List[str]) -> float:
        """Calculate participant relevance"""
        if not query_participants or not self.metadata.participants:
            return 0.0

        query_set = set(p.lower() for p in query_participants)
        memory_set = set(p.lower() for p in self.metadata.participants)

        if not query_set or not memory_set:
            return 0.0

        intersection = len(query_set & memory_set)
        union = len(query_set | memory_set)

        return intersection / union if union > 0 else 0.0

    def _calculate_emotional_relevance(self, emotional_context: Dict[str, float]) -> float:
        """Calculate emotional relevance"""
        target_valence = emotional_context.get("valence", 0.0)
        target_arousal = emotional_context.get("arousal", 0.0)

        valence_diff = abs(self.metadata.emotional_valence - target_valence)
        arousal_diff = abs(self.metadata.arousal - target_arousal)

        # Inverse of difference (closer = higher relevance)
        valence_sim = 1.0 - valence_diff
        arousal_sim = 1.0 - arousal_diff

        return (valence_sim + arousal_sim) / 2.0

    def _extract_conflict(self, content: str) -> str:
        """Extract conflict from content"""
        conflict_keywords = ['fight', 'battle', 'argue', 'dispute', 'conflict', 'struggle', 'against', 'enemy', 'danger', 'threat']

        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in conflict_keywords):
                return sentence.strip()[:100]

        return "No explicit conflict identified"

    def _extract_resolution(self, content: str) -> str:
        """Extract resolution from content"""
        resolution_keywords = ['solved', 'resolved', 'finished', 'completed', 'won', 'success', 'achieved', 'decided', 'concluded']

        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in resolution_keywords):
                return sentence.strip()[:100]

        return "Resolution not explicitly stated"

    def _extract_key_events(self, content: str) -> List[str]:
        """Extract key events from content"""
        # Simple event extraction based on action verbs
        action_verbs = ['went', 'said', 'did', 'took', 'made', 'found', 'saw', 'fought', 'helped', 'discovered', 'escaped', 'arrived', 'left']

        events = []
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence = sentence.strip()
            if any(verb in sentence.lower() for verb in action_verbs):
                events.append(sentence[:80] + "..." if len(sentence) > 80 else sentence)

        return events[:3]  # Return top 3 events

    def _extract_themes(self, content: str) -> List[str]:
        """Extract themes from content"""
        theme_keywords = {
            'friendship': ['friend', 'friendship', 'together', 'helped', 'supported'],
            'conflict': ['fight', 'battle', 'argue', 'enemy', 'against'],
            'discovery': ['found', 'discovered', 'learned', 'realized', 'uncovered'],
            'journey': ['traveled', 'journey', 'went', 'arrived', 'left'],
            'mystery': ['mystery', 'unknown', 'secret', 'hidden', 'puzzle'],
            'danger': ['danger', 'threat', 'risk', 'dangerous', 'unsafe']
        }

        content_lower = content.lower()
        identified_themes = []

        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                identified_themes.append(theme)

        return identified_themes

    @classmethod
    def create_from_experience(
        cls,
        experience_description: str,
        location: str = "",
        participants: List[str] = None,
        emotional_valence: float = 0.0,
        arousal: float = 0.0,
        event_type: str = "general",
        context: Dict[str, Any] = None
    ) -> 'EpisodicMemory':
        """Factory method to create episodic memory from experience"""
        if context is None:
            context = {}

        context.update({
            "event_type": event_type,
            "participants": participants or [],
            "location": location
        })

        return cls(
            content=experience_description,
            location=location,
            participants=participants,
            emotional_valence=emotional_valence,
            arousal=arousal,
            context=context
        )