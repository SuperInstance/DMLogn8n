"""
Memory Consolidation Engine
============================

Intelligent memory consolidation system that transfers memories between tiers,
extracts patterns, and manages the importance-based consolidation process.
"""

import math
import heapq
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

from ..core.memory_base import MemoryBase, MemoryType, MemoryImportance, MemoryStatus
from ..memory_types.working_memory import WorkingMemory
from ..memory_types.episodic_memory import EpisodicMemory
from ..memory_types.semantic_memory import SemanticMemory
from ..retrieval.vector_store import VectorStore


logger = logging.getLogger(__name__)


class ConsolidationCandidate:
    """Represents a memory candidate for consolidation"""

    def __init__(self, memory: MemoryBase, consolidation_score: float, reason: str = ""):
        self.memory = memory
        self.consolidation_score = consolidation_score
        self.reason = reason
        self.timestamp = datetime.now()

    def __lt__(self, other):
        # Higher scores should be consolidated first
        return self.consolidation_score > other.consolidation_score


class PatternExtractor:
    """Extracts patterns from groups of similar memories"""

    def __init__(self):
        self.pattern_cache: Dict[str, Dict] = {}

    def extract_patterns_from_memories(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Extract patterns from a group of episodic memories"""
        if len(memories) < 3:  # Need at least 3 memories to find patterns
            return []

        patterns = []

        # Extract temporal patterns
        temporal_patterns = self._find_temporal_patterns(memories)
        patterns.extend(temporal_patterns)

        # Extract contextual patterns
        contextual_patterns = self._find_contextual_patterns(memories)
        patterns.extend(contextual_patterns)

        # Extract emotional patterns
        emotional_patterns = self._find_emotional_patterns(memories)
        patterns.extend(emotional_patterns)

        # Extract behavioral patterns
        behavioral_patterns = self._find_behavioral_patterns(memories)
        patterns.extend(behavioral_patterns)

        return patterns

    def _find_temporal_patterns(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Find patterns in the timing of memories"""
        patterns = []

        # Group memories by time of day
        time_groups = defaultdict(list)
        for memory in memories:
            hour = memory.timestamp.hour
            time_groups[hour].append(memory)

        # Look for patterns in specific times
        for hour, group in time_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "temporal",
                    "description": f"Events frequently occur around {hour:02d}:00",
                    "confidence": min(len(group) / 10.0, 1.0),
                    "supporting_memories": [m.id for m in group],
                    "time_context": {"hour": hour}
                })

        return patterns

    def _find_contextual_patterns(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Find patterns in the context of memories"""
        patterns = []

        # Location patterns
        location_groups = defaultdict(list)
        for memory in memories:
            if memory.metadata.location:
                location_groups[memory.metadata.location].append(memory)

        for location, group in location_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "contextual",
                    "description": f"Events frequently occur at {location}",
                    "confidence": min(len(group) / 8.0, 1.0),
                    "supporting_memories": [m.id for m in group],
                    "context": {"location": location}
                })

        # Participant patterns
        participant_groups = defaultdict(list)
        for memory in memories:
            for participant in memory.metadata.participants:
                participant_groups[participant].append(memory)

        for participant, group in participant_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "social",
                    "description": f"Frequent interactions with {participant}",
                    "confidence": min(len(group) / 8.0, 1.0),
                    "supporting_memories": [m.id for m in group],
                    "context": {"participant": participant}
                })

        return patterns

    def _find_emotional_patterns(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Find patterns in emotional responses"""
        patterns = []

        # Group by emotional valence
        emotional_groups = defaultdict(list)
        for memory in memories:
            valence_category = self._categorize_valence(memory.metadata.emotional_valence)
            emotional_groups[valence_category].append(memory)

        for category, group in emotional_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "emotional",
                    "description": f"Frequent {category} emotional experiences",
                    "confidence": min(len(group) / 8.0, 1.0),
                    "supporting_memories": [m.id for m in group],
                    "context": {"emotional_category": category}
                })

        return patterns

    def _find_behavioral_patterns(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Find patterns in behaviors and actions"""
        patterns = []

        # Extract action words from memories
        action_groups = defaultdict(list)
        for memory in memories:
            actions = self._extract_actions(memory.content.primary_content)
            for action in actions:
                action_groups[action].append(memory)

        for action, group in action_groups.items():
            if len(group) >= 3:
                patterns.append({
                    "type": "behavioral",
                    "description": f"Frequently performs action: {action}",
                    "confidence": min(len(group) / 8.0, 1.0),
                    "supporting_memories": [m.id for m in group],
                    "context": {"action": action}
                })

        return patterns

    def _categorize_valence(self, valence: float) -> str:
        """Categorize emotional valence"""
        if valence > 0.5:
            return "positive"
        elif valence < -0.5:
            return "negative"
        else:
            return "neutral"

    def _extract_actions(self, text: str) -> List[str]:
        """Extract action words from text"""
        action_words = ['fought', 'ran', 'talked', 'helped', 'explored', 'discovered', 'hid', 'attacked', 'defended', 'negotiated', 'traded', 'traveled', 'searched', 'found']
        text_lower = text.lower()
        return [word for word in action_words if word in text_lower]


class ConsolidationEngine:
    """
    Main consolidation engine that manages memory transfer between tiers
    and pattern extraction from consolidated memories.
    """

    def __init__(self, character_level: int = 1):
        self.character_level = character_level

        # Consolidation thresholds based on level
        self.consolidation_threshold = self._get_consolidation_threshold(character_level)
        self.working_memory_capacity = self._get_working_memory_capacity(character_level)
        self.total_memory_capacity = self._get_total_memory_capacity(character_level)

        # Components
        self.pattern_extractor = PatternExtractor()
        self.vector_store = None  # Will be set by MemoryManager

        # Consolidation state
        self.consolidation_queue: List[ConsolidationCandidate] = []
        self.last_consolidation_time = datetime.now()
        self.consolidation_history: List[Dict[str, Any]] = []

        # Statistics
        self.total_consolidations = 0
        self.successful_consolidations = 0
        self.patterns_extracted = 0

    def set_vector_store(self, vector_store: VectorStore) -> None:
        """Set the vector store for similarity-based consolidation"""
        self.vector_store = vector_store

    def evaluate_consolidation_candidates(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> List[ConsolidationCandidate]:
        """Evaluate memories for consolidation potential"""
        candidates = []

        # Evaluate working memory candidates
        working_candidates = self._evaluate_working_memory_candidates(working_memory)
        candidates.extend(working_candidates)

        # Evaluate episodic memory candidates
        episodic_candidates = self._evaluate_episodic_memory_candidates(episodic_memories)
        candidates.extend(episodic_candidates)

        # Evaluate semantic memory candidates (for refinement)
        semantic_candidates = self._evaluate_semantic_memory_candidates(semantic_memories)
        candidates.extend(semantic_candidates)

        # Sort by consolidation score
        candidates.sort(reverse=True)

        return candidates

    def consolidate_working_to_episodic(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory]
    ) -> Dict[str, Any]:
        """Consolidate working memory items to episodic memory"""
        consolidation_results = {
            "type": "working_to_episodic",
            "consolidated_count": 0,
            "new_episodic_memories": [],
            "failed_consolidations": []
        }

        # Get candidates from working memory
        candidates = working_memory.consolidate_to_episodic(
            min_importance=6.0
        )

        for memory in candidates:
            try:
                # Create episodic memory from working memory
                episodic_memory = EpisodicMemory(
                    content=memory.content.primary_content,
                    importance=memory.importance,
                    emotional_valence=memory.metadata.emotional_valence,
                    arousal=memory.metadata.arousal,
                    location=memory.metadata.location,
                    participants=memory.metadata.participants,
                    context=memory.metadata.context,
                    source_memory_ids=[memory.id]
                )

                # Mark original memory as consolidated
                memory.status = MemoryStatus.CONSOLIDATED

                # Add to episodic memories
                episodic_memories.append(episodic_memory)

                # Update vector store if available
                if self.vector_store:
                    self.vector_store.add_memory(episodic_memory)

                consolidation_results["new_episodic_memories"].append(episodic_memory.id)
                consolidation_results["consolidated_count"] += 1

                logger.debug(f"Consolidated working memory {memory.id} to episodic {episodic_memory.id}")

            except Exception as e:
                consolidation_results["failed_consolidations"].append({
                    "memory_id": memory.id,
                    "error": str(e)
                })
                logger.error(f"Failed to consolidate working memory {memory.id}: {e}")

        self.last_consolidation_time = datetime.now()
        return consolidation_results

    def consolidate_episodic_to_semantic(
        self,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> Dict[str, Any]:
        """Consolidate episodic memories to semantic memory"""
        consolidation_results = {
            "type": "episodic_to_semantic",
            "consolidated_count": 0,
            "new_semantic_memories": [],
            "patterns_extracted": [],
            "failed_consolidations": []
        }

        # Find similar episodic memories for pattern extraction
        if self.vector_store:
            memory_clusters = self.vector_store.find_memory_clusters(
                MemoryType.EPISODIC,
                min_cluster_size=3,
                max_clusters=5
            )
        else:
            # Fallback to simple clustering
            memory_clusters = self._simple_cluster_episodic_memories(episodic_memories)

        for cluster in memory_clusters:
            try:
                # Get actual memory objects
                cluster_memories = [
                    mem for mem in episodic_memories
                    if mem.id in [m["memory_id"] for m in cluster["memories"]]
                ]

                if len(cluster_memories) < 3:
                    continue

                # Extract patterns from the cluster
                patterns = self.pattern_extractor.extract_patterns_from_memories(cluster_memories)

                # Create semantic memory from patterns
                for pattern in patterns:
                    semantic_memory = self._create_semantic_memory_from_pattern(
                        pattern, cluster_memories
                    )

                    # Mark source memories as consolidated
                    for mem in cluster_memories:
                        mem.status = MemoryStatus.CONSOLIDATED
                        mem.metadata.consolidation_count += 1

                    # Add to semantic memories
                    semantic_memories.append(semantic_memory)

                    # Update vector store
                    if self.vector_store:
                        self.vector_store.add_memory(semantic_memory)

                    consolidation_results["new_semantic_memories"].append(semantic_memory.id)
                    consolidation_results["patterns_extracted"].append(pattern)
                    consolidation_results["consolidated_count"] += 1
                    self.patterns_extracted += 1

            except Exception as e:
                consolidation_results["failed_consolidations"].append({
                    "cluster_id": cluster.get("cluster_id", "unknown"),
                    "error": str(e)
                })
                logger.error(f"Failed to consolidate episodic cluster: {e}")

        self.last_consolidation_time = datetime.now()
        return consolidation_results

    def run_consolidation_cycle(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> Dict[str, Any]:
        """Run a complete consolidation cycle"""
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "character_level": self.character_level,
            "working_to_episodic": {},
            "episodic_to_semantic": {},
            "total_consolidated": 0,
            "success": True
        }

        try:
            # Check if consolidation should run
            if not self._should_run_consolidation():
                cycle_results["skipped"] = True
                cycle_results["reason"] = "Consolidation threshold not met"
                return cycle_results

            logger.info(f"Starting consolidation cycle for level {self.character_level}")

            # Phase 1: Working to Episodic
            working_results = self.consolidate_working_to_episodic(
                working_memory, episodic_memories
            )
            cycle_results["working_to_episodic"] = working_results

            # Phase 2: Episodic to Semantic
            semantic_results = self.consolidate_episodic_to_semantic(
                episodic_memories, semantic_memories
            )
            cycle_results["episodic_to_semantic"] = semantic_results

            # Calculate totals
            cycle_results["total_consolidated"] = (
                working_results["consolidated_count"] +
                semantic_results["consolidated_count"]
            )

            # Update statistics
            self.total_consolidations += 1
            self.successful_consolidations += 1

            # Record in history
            self.consolidation_history.append(cycle_results)

            logger.info(f"Consolidation cycle completed: {cycle_results['total_consolidated']} memories consolidated")

        except Exception as e:
            cycle_results["success"] = False
            cycle_results["error"] = str(e)
            logger.error(f"Consolidation cycle failed: {e}")

        return cycle_results

    def update_character_level(self, new_level: int) -> None:
        """Update consolidation parameters based on new character level"""
        self.character_level = new_level
        self.consolidation_threshold = self._get_consolidation_threshold(new_level)
        self.working_memory_capacity = self._get_working_memory_capacity(new_level)
        self.total_memory_capacity = self._get_total_memory_capacity(new_level)

        logger.info(f"Updated consolidation parameters for level {new_level}")

    def get_consolidation_statistics(self) -> Dict[str, Any]:
        """Get consolidation system statistics"""
        return {
            "character_level": self.character_level,
            "consolidation_threshold": self.consolidation_threshold,
            "working_memory_capacity": self.working_memory_capacity,
            "total_memory_capacity": self.total_memory_capacity,
            "total_consolidations": self.total_consolidations,
            "successful_consolidations": self.successful_consolidations,
            "success_rate": self.successful_consolidations / max(self.total_consolidations, 1),
            "patterns_extracted": self.patterns_extracted,
            "last_consolidation": self.last_consolidation_time.isoformat(),
            "consolidation_queue_size": len(self.consolidation_queue),
            "recent_history": self.consolidation_history[-5:]  # Last 5 cycles
        }

    def _evaluate_working_memory_candidates(self, working_memory: WorkingMemory) -> List[ConsolidationCandidate]:
        """Evaluate working memory items for consolidation"""
        candidates = []

        for item in working_memory.items.values():
            memory = item.memory

            # Check if memory is ready for consolidation
            if not memory.can_consolidate():
                continue

            # Calculate consolidation score
            score = self._calculate_consolidation_score(memory, "working_to_episodic")
            reason = f"Working memory item with importance {memory.importance:.1f}"

            candidates.append(ConsolidationCandidate(memory, score, reason))

        return candidates

    def _evaluate_episodic_memory_candidates(self, episodic_memories: List[EpisodicMemory]) -> List[ConsolidationCandidate]:
        """Evaluate episodic memories for consolidation"""
        candidates = []

        for memory in episodic_memories:
            if memory.status != MemoryStatus.ACTIVE:
                continue

            if not memory.can_consolidate():
                continue

            # Check for similar memories (pattern potential)
            similar_count = self._count_similar_memories(memory, episodic_memories)

            if similar_count >= 2:  # Found at least 2 similar memories
                score = self._calculate_consolidation_score(memory, "episodic_to_semantic")
                score *= (1 + similar_count * 0.2)  # Boost for pattern potential

                reason = f"Episodic memory with {similar_count} similar memories"
                candidates.append(ConsolidationCandidate(memory, score, reason))

        return candidates

    def _evaluate_semantic_memory_candidates(self, semantic_memories: List[SemanticMemory]) -> List[ConsolidationCandidate]:
        """Evaluate semantic memories for refinement/abstraction"""
        candidates = []

        for memory in semantic_memories:
            # Semantic memories are typically not consolidated further,
            # but can be refined or abstracted

            if memory.validation_count >= 5 and memory.confidence > 0.8:
                # High-confidence, validated memory could be abstracted
                score = self._calculate_consolidation_score(memory, "semantic_refinement")
                reason = "High-confidence semantic memory ready for abstraction"

                candidates.append(ConsolidationCandidate(memory, score, reason))

        return candidates

    def _calculate_consolidation_score(self, memory: MemoryBase, consolidation_type: str) -> float:
        """Calculate consolidation score for a memory"""
        base_score = memory.importance

        # Access frequency boost
        access_boost = min(memory.metadata.access_count * 0.1, 1.0)

        # Age factor (older memories are more ready for consolidation)
        age_days = (datetime.now() - memory.creation_time).days
        age_boost = min(age_days / 30.0, 1.0)  # Max boost after 30 days

        # Type-specific factors
        type_boost = 1.0
        if consolidation_type == "working_to_episodic":
            type_boost = 1.2  # Encourage working memory consolidation
        elif consolidation_type == "episodic_to_semantic":
            type_boost = 1.5  # Higher priority for pattern extraction
        elif consolidation_type == "semantic_refinement":
            type_boost = 0.8  # Lower priority for semantic refinement

        # Emotional intensity boost
        emotional_boost = abs(memory.metadata.emotional_valence) * 0.3

        # Consolidation count penalty (already consolidated memories)
        consolidation_penalty = memory.metadata.consolidation_count * 0.1

        total_score = (
            base_score +
            access_boost +
            age_boost +
            emotional_boost -
            consolidation_penalty
        ) * type_boost

        return max(0, total_score)

    def _count_similar_memories(self, memory: EpisodicMemory, all_memories: List[EpisodicMemory]) -> int:
        """Count memories similar to the given memory"""
        similar_count = 0

        for other in all_memories:
            if other.id == memory.id:
                continue

            similarity = memory.calculate_similarity_to(other)
            if similarity > 0.7:  # Similarity threshold
                similar_count += 1

        return similar_count

    def _create_semantic_memory_from_pattern(
        self,
        pattern: Dict[str, Any],
        source_memories: List[EpisodicMemory]
    ) -> SemanticMemory:
        """Create a semantic memory from extracted pattern"""
        # Generate semantic content from pattern
        content = f"Learned pattern: {pattern['description']}"
        if pattern["confidence"] > 0.7:
            content += f" (High confidence: {pattern['confidence']:.2f})"

        # Create semantic memory
        semantic_memory = SemanticMemory(
            content=content,
            concept=f"pattern_{pattern['type']}",
            pattern_type="generalization",
            source_memory_ids=[m.id for m in source_memories],
            confidence=pattern["confidence"],
            importance=min(7.0 + len(source_memories) * 0.2, 10.0)
        )

        # Add pattern as learned pattern
        from ..memory_types.semantic_memory import LearnedPattern
        learned_pattern = LearnedPattern(
            pattern_id=f"pattern_{datetime.now().timestamp()}",
            description=pattern["description"],
            trigger_conditions=pattern.get("context", {}),
            typical_outcomes=[],
            success_rate=0.0,
            frequency=len(source_memories),
            confidence=pattern["confidence"],
            source_memory_ids=[m.id for m in source_memories]
        )
        semantic_memory.add_learned_pattern(learned_pattern)

        return semantic_memory

    def _simple_cluster_episodic_memories(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Simple clustering fallback when vector store is not available"""
        clusters = []

        # Group by location
        location_groups = defaultdict(list)
        for memory in memories:
            if memory.metadata.location:
                location_groups[memory.metadata.location].append(memory)

        for location, group in location_groups.items():
            if len(group) >= 3:
                clusters.append({
                    "cluster_id": len(clusters),
                    "size": len(group),
                    "memories": [{"memory_id": m.id} for m in group]
                })

        return clusters

    def _should_run_consolidation(self) -> bool:
        """Check if consolidation should run based on time and threshold"""
        # Time-based check (at least 1 hour since last consolidation)
        time_since_last = datetime.now() - self.last_consolidation_time
        if time_since_last < timedelta(hours=1):
            return False

        # Check if we have enough candidates in queue
        return len(self.consolidation_queue) >= 3

    def _get_consolidation_threshold(self, level: int) -> float:
        """Get consolidation threshold for character level"""
        if level <= 4:
            return 100.0
        elif level <= 10:
            return 200.0
        elif level <= 16:
            return 400.0
        else:
            return 800.0

    def _get_working_memory_capacity(self, level: int) -> int:
        """Get working memory capacity for character level"""
        if level <= 4:
            return 5
        elif level <= 10:
            return 10
        elif level <= 16:
            return 15
        else:
            return 25

    def _get_total_memory_capacity(self, level: int) -> int:
        """Get total memory capacity for character level"""
        if level <= 4:
            return 50
        elif level <= 10:
            return 200
        elif level <= 16:
            return 500
        else:
            return 1000