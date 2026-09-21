"""
Memory Manager - Central Orchestration
=======================================

Central memory management system that orchestrates all memory components.
Provides a unified interface for the hierarchical memory architecture.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

from .memory_base import MemoryBase, MemoryType, MemoryStatus, LevelCapacity
from ..memory_types.working_memory import WorkingMemory
from ..memory_types.episodic_memory import EpisodicMemory
from ..memory_types.semantic_memory import SemanticMemory
from ..consolidation.consolidation_engine import ConsolidationEngine
from ..core.forgetting_mechanism import ForgettingMechanism, CompositeForgetting
from ..retrieval.vector_store import VectorStore
from ..dashboard.memory_dashboard import MemoryDashboard


logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory management system that coordinates all memory components.
    Implements the hierarchical memory architecture with intelligent consolidation
    and capacity management.
    """

    def __init__(
        self,
        character_id: str,
        character_level: int = 1,
        data_directory: str = "./data/memory_system",
        enable_vector_store: bool = True,
        enable_dashboard: bool = True
    ):
        self.character_id = character_id
        self.character_level = character_level
        self.data_directory = data_directory
        self.creation_time = datetime.now()

        # Initialize capacity configuration
        self.capacity_config = LevelCapacity.get_capacity_for_level(character_level)

        # Initialize memory components
        self.working_memory = WorkingMemory(capacity=self.capacity_config.working_memory_capacity)
        self.episodic_memories: List[EpisodicMemory] = []
        self.semantic_memories: List[SemanticMemory] = []

        # Initialize systems
        self.consolidation_engine = ConsolidationEngine(character_level)
        self.forgetting_mechanism = ForgettingMechanism(character_level, CompositeForgetting())

        # Initialize vector store
        self.vector_store = None
        if enable_vector_store:
            self.vector_store = VectorStore(persist_directory=f"{data_directory}/vector_store")
            self.consolidation_engine.set_vector_store(self.vector_store)

        # Initialize dashboard
        self.dashboard = None
        if enable_dashboard:
            self.dashboard = MemoryDashboard(character_id)

        # Memory management settings
        self.auto_consolidation = True
        self.auto_forgetting = True
        self.consolidation_interval = timedelta(hours=1)
        self.last_consolidation_time = datetime.now()

        # Statistics and tracking
        self.total_memories_created = 0
        self.memory_operations: List[Dict[str, Any]] = []

        logger.info(f"Memory Manager initialized for character {character_id} at level {character_level}")

    def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 5.0,
        emotional_valence: float = 0.0,
        arousal: float = 0.0,
        location: str = "",
        participants: List[str] = None,
        context: Dict[str, Any] = None,
        tags: List[str] = None,
        source: str = "experience"
    ) -> MemoryBase:
        """
        Add a new memory to the system.
        Automatically routes to appropriate memory type and manages capacity.
        """
        try:
            # Create memory based on type
            memory = self._create_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_valence=emotional_valence,
                arousal=arousal,
                location=location,
                participants=participants,
                context=context,
                tags=tags,
                source=source
            )

            # Route memory to appropriate storage
            self._route_memory(memory)

            # Update vector store
            if self.vector_store:
                self.vector_store.add_memory(memory)

            # Update statistics
            self.total_memories_created += 1
            self._record_operation("add_memory", {
                "memory_id": memory.id,
                "memory_type": memory_type.value,
                "importance": importance
            })

            # Log activity
            if self.dashboard:
                self.dashboard.log_activity(
                    "memory_added",
                    f"Added {memory_type.value} memory",
                    {"memory_id": memory.id, "importance": importance}
                )

            # Trigger auto processes
            if self.auto_consolidation:
                self._check_auto_consolidation()

            if self.auto_forgetting:
                self._check_auto_forgetting()

            logger.debug(f"Added {memory_type.value} memory: {memory.id}")
            return memory

        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise

    def retrieve_memories(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        max_results: int = 10,
        similarity_threshold: float = 0.3,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories based on query and filters.
        Combines working memory, vector search, and semantic matching.
        """
        try:
            if memory_types is None:
                memory_types = [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC]

            all_results = []

            # Search working memory
            if MemoryType.WORKING in memory_types:
                working_results = self._search_working_memory(query, max_results)
                all_results.extend(working_results)

            # Search vector store (episodic and semantic)
            if self.vector_store and (MemoryType.EPISODIC in memory_types or MemoryType.SEMANTIC in memory_types):
                vector_types = [t for t in memory_types if t in [MemoryType.EPISODIC, MemoryType.SEMANTIC]]
                vector_results = self.vector_store.search_similar_memories(
                    query=query,
                    memory_types=vector_types,
                    max_results=max_results,
                    similarity_threshold=similarity_threshold,
                    filters=filters
                )
                all_results.extend(vector_results)

            # Sort and return top results
            all_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            final_results = all_results[:max_results]

            # Record access for all retrieved memories
            self._record_memory_access(final_results)

            logger.debug(f"Retrieved {len(final_results)} memories for query: {query[:50]}...")
            return final_results

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    def get_context_memories(
        self,
        max_working: int = 5,
        max_episodic: int = 10,
        max_semantic: int = 5
    ) -> Dict[str, List[MemoryBase]]:
        """
        Get current context memories for decision making.
        Returns active working memory and relevant memories from other types.
        """
        try:
            context = {
                "working": [],
                "episodic": [],
                "semantic": []
            }

            # Working memory (most active items)
            working_items = self.working_memory.get_active_context(max_working)
            context["working"] = working_items

            # Recent episodic memories
            recent_episodic = sorted(
                [m for m in self.episodic_memories if m.status == MemoryStatus.ACTIVE],
                key=lambda m: m.metadata.last_accessed or m.creation_time,
                reverse=True
            )[:max_episodic]
            context["episodic"] = recent_episodic

            # High-importance semantic memories
            important_semantic = sorted(
                [m for m in self.semantic_memories if m.status == MemoryStatus.ACTIVE],
                key=lambda m: m.importance * m.confidence,
                reverse=True
            )[:max_semantic]
            context["semantic"] = important_semantic

            return context

        except Exception as e:
            logger.error(f"Failed to get context memories: {e}")
            return {"working": [], "episodic": [], "semantic": []}

    def reflect_on_experiences(self, session_memories: List[str] = None) -> Dict[str, Any]:
        """
        Perform reflection on recent experiences.
        Creates insights and updates memory importance based on reflection.
        """
        try:
            reflection_results = {
                "timestamp": datetime.now().isoformat(),
                "insights_generated": 0,
                "importance_updates": 0,
                "new_connections": 0
            }

            # Get memories to reflect on
            if session_memories:
                memories_to_reflect = []
                for memory_id in session_memories:
                    memory = self._find_memory_by_id(memory_id)
                    if memory:
                        memories_to_reflect.append(memory)
            else:
                # Use recent memories
                recent_cutoff = datetime.now() - timedelta(hours=24)
                memories_to_reflect = [
                    m for m in self.episodic_memories
                    if (m.status == MemoryStatus.ACTIVE and
                        (m.metadata.last_accessed or m.creation_time) > recent_cutoff)
                ]

            if not memories_to_reflect:
                reflection_results["message"] = "No recent memories to reflect on"
                return reflection_results

            # Analyze patterns and generate insights
            insights = self._generate_reflection_insights(memories_to_reflect)
            reflection_results["insights_generated"] = len(insights)

            # Create semantic memories for important insights
            for insight in insights:
                if insight["importance"] > 7.0:
                    semantic_memory = SemanticMemory(
                        content=insight["description"],
                        concept=f"insight_{insight['type']}",
                        pattern_type="reflection",
                        source_memory_ids=[m.id for m in insight["source_memories"]],
                        confidence=insight["confidence"],
                        importance=insight["importance"]
                    )
                    self.semantic_memories.append(semantic_memory)

                    if self.vector_store:
                        self.vector_store.add_memory(semantic_memory)

                    reflection_results["new_connections"] += 1

            # Update importance based on reflection
            for memory in memories_to_reflect:
                old_importance = memory.importance
                memory.importance = min(memory.importance * 1.1, 10.0)  # 10% boost
                if memory.importance != old_importance:
                    reflection_results["importance_updates"] += 1

            # Log reflection
            if self.dashboard:
                self.dashboard.log_activity(
                    "reflection",
                    f"Reflected on {len(memories_to_reflect)} memories",
                    {"insights": len(insights), "importance_updates": reflection_results["importance_updates"]}
                )

            logger.info(f"Reflection completed: {len(insights)} insights generated")
            return reflection_results

        except Exception as e:
            logger.error(f"Failed to perform reflection: {e}")
            return {"error": str(e)}

    def run_consolidation_cycle(self) -> Dict[str, Any]:
        """Manually trigger a consolidation cycle"""
        try:
            logger.info("Manual consolidation cycle triggered")
            results = self.consolidation_engine.run_consolidation_cycle(
                self.working_memory,
                self.episodic_memories,
                self.semantic_memories
            )

            # Log consolidation
            if self.dashboard:
                self.dashboard.log_activity(
                    "consolidation",
                    f"Consolidation cycle completed",
                    {"total_consolidated": results["total_consolidated"]}
                )

            return results

        except Exception as e:
            logger.error(f"Consolidation cycle failed: {e}")
            return {"error": str(e)}

    def run_forgetting_cycle(self) -> Dict[str, Any]:
        """Manually trigger a forgetting cycle"""
        try:
            logger.info("Manual forgetting cycle triggered")
            results = self.forgetting_mechanism.manage_capacity(
                self.working_memory,
                self.episodic_memories,
                self.semantic_memories
            )

            # Clean up vector store
            if self.vector_store:
                for memory_info in results["forgotten_memories"]:
                    self.vector_store.delete_memory(memory_info.id)

            # Log forgetting
            if self.dashboard:
                self.dashboard.log_activity(
                    "forgetting",
                    f"Forgetting cycle completed",
                    {"memories_forgotten": len(results["forgotten_memories"])}
                )

            return results

        except Exception as e:
            logger.error(f"Forgetting cycle failed: {e}")
            return {"error": str(e)}

    def update_character_level(self, new_level: int) -> None:
        """Update system parameters for new character level"""
        try:
            old_level = self.character_level
            self.character_level = new_level

            # Update capacity configuration
            self.capacity_config = LevelCapacity.get_capacity_for_level(new_level)

            # Update working memory capacity
            self.working_memory.capacity = self.capacity_config.working_memory_capacity

            # Update consolidation engine
            self.consolidation_engine.update_character_level(new_level)

            # Update forgetting mechanism
            self.forgetting_mechanism.update_character_level(new_level)

            # Log level change
            if self.dashboard:
                self.dashboard.log_activity(
                    "level_up",
                    f"Character leveled up from {old_level} to {new_level}",
                    {"old_level": old_level, "new_level": new_level}
                )

            logger.info(f"Character level updated: {old_level} -> {new_level}")

        except Exception as e:
            logger.error(f"Failed to update character level: {e}")

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        try:
            stats = {
                "character_id": self.character_id,
                "character_level": self.character_level,
                "system_info": {
                    "creation_time": self.creation_time.isoformat(),
                    "total_memories_created": self.total_memories_created,
                    "auto_consolidation": self.auto_consolidation,
                    "auto_forgetting": self.auto_forgetting
                },
                "capacity_config": {
                    "total_capacity": self.capacity_config.total_memories,
                    "working_memory": self.capacity_config.working_memory_capacity,
                    "consolidation_threshold": self.capacity_config.consolidation_threshold
                },
                "memory_counts": {
                    "working": len(self.working_memory),
                    "episodic": len([m for m in self.episodic_memories if m.status == MemoryStatus.ACTIVE]),
                    "semantic": len([m for m in self.semantic_memories if m.status == MemoryStatus.ACTIVE])
                },
                "consolidation_stats": self.consolidation_engine.get_consolidation_statistics(),
                "forgetting_stats": self.forgetting_mechanism.get_forgetting_statistics()
            }

            # Add vector store stats if available
            if self.vector_store:
                stats["vector_store_stats"] = self.vector_store.get_memory_statistics()

            return stats

        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}

    def generate_dashboard_html(self) -> Optional[str]:
        """Generate HTML dashboard"""
        if not self.dashboard:
            return None

        try:
            dashboard_data = self.dashboard.generate_dashboard_data(
                self.working_memory,
                self.episodic_memories,
                self.semantic_memories,
                self.consolidation_engine,
                self.forgetting_mechanism
            )

            return self.dashboard.generate_html_dashboard(dashboard_data)

        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            return None

    def _create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float,
        emotional_valence: float,
        arousal: float,
        location: str,
        participants: List[str],
        context: Dict[str, Any],
        tags: List[str],
        source: str
    ) -> MemoryBase:
        """Create a memory object based on type"""
        if memory_type == MemoryType.WORKING:
            # Working memories are created differently
            from ..memory_types.working_memory import WorkingMemoryItem
            return None  # Working memories are added directly

        elif memory_type == MemoryType.EPISODIC:
            return EpisodicMemory(
                content=content,
                importance=importance,
                emotional_valence=emotional_valence,
                arousal=arousal,
                location=location,
                participants=participants,
                context=context or {}
            )

        elif memory_type == MemoryType.SEMANTIC:
            return SemanticMemory(
                content=content,
                importance=importance,
                confidence=0.8,
                source="manual"
            )

        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

    def _route_memory(self, memory: MemoryBase) -> None:
        """Route memory to appropriate storage"""
        if memory.type == MemoryType.WORKING:
            # Add to working memory
            self.working_memory.add_memory(memory)

        elif memory.type == MemoryType.EPISODIC:
            self.episodic_memories.append(memory)

        elif memory.type == MemoryType.SEMANTIC:
            self.semantic_memories.append(memory)

        else:
            logger.warning(f"Unknown memory type for routing: {memory.type}")

    def _search_working_memory(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search working memory for relevant items"""
        results = self.working_memory.retrieve_by_relevance(query, max_results)

        return [{
            "memory_id": result[0].id,
            "memory_type": MemoryType.WORKING.value,
            "document": result[0].content.primary_content,
            "similarity_score": result[1],
            "metadata": {
                "importance": result[0].importance,
                "activation": self.working_memory.items[result[0].id].activation if result[0].id in self.working_memory.items else 0
            }
        } for result in results]

    def _record_memory_access(self, memories: List[Dict[str, Any]]) -> None:
        """Record access for retrieved memories"""
        for memory_result in memories:
            memory_id = memory_result.get("memory_id")
            if memory_id:
                memory = self._find_memory_by_id(memory_id)
                if memory:
                    memory.access()

    def _find_memory_by_id(self, memory_id: str) -> Optional[MemoryBase]:
        """Find memory by ID across all memory types"""
        # Check working memory
        if memory_id in self.working_memory.items:
            return self.working_memory.items[memory_id].memory

        # Check episodic memories
        for memory in self.episodic_memories:
            if memory.id == memory_id:
                return memory

        # Check semantic memories
        for memory in self.semantic_memories:
            if memory.id == memory_id:
                return memory

        return None

    def _generate_reflection_insights(self, memories: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """Generate insights from reflection on memories"""
        insights = []

        # Look for patterns in emotions
        emotions = [m.metadata.emotional_valence for m in memories]
        avg_emotion = sum(emotions) / len(emotions) if emotions else 0

        if abs(avg_emotion) > 0.6:
            insights.append({
                "type": "emotional_pattern",
                "description": f"Strong emotional pattern detected: {'positive' if avg_emotion > 0 else 'negative'} experiences",
                "importance": 6.0 + abs(avg_emotion) * 2,
                "confidence": 0.8,
                "source_memories": memories
            })

        # Look for location patterns
        locations = [m.metadata.location for m in memories if m.metadata.location]
        location_counts = {}
        for location in locations:
            location_counts[location] = location_counts.get(location, 0) + 1

        if location_counts:
            most_common_location = max(location_counts, key=location_counts.get)
            if location_counts[most_common_location] >= 2:
                insights.append({
                    "type": "location_pattern",
                    "description": f"Frequent experiences at {most_common_location}",
                    "importance": 5.0 + location_counts[most_common_location],
                    "confidence": 0.7,
                    "source_memories": [m for m in memories if m.metadata.location == most_common_location]
                })

        # Look for participant patterns
        all_participants = []
        for memory in memories:
            all_participants.extend(memory.metadata.participants)

        participant_counts = {}
        for participant in all_participants:
            participant_counts[participant] = participant_counts.get(participant, 0) + 1

        if participant_counts:
            most_frequent = max(participant_counts, key=participant_counts.get)
            if participant_counts[most_frequent] >= 2:
                insights.append({
                    "type": "social_pattern",
                    "description": f"Frequent interactions with {most_frequent}",
                    "importance": 5.5 + participant_counts[most_frequent] * 0.5,
                    "confidence": 0.75,
                    "source_memories": [m for m in memories if most_frequent in m.metadata.participants]
                })

        return insights

    def _check_auto_consolidation(self) -> None:
        """Check if automatic consolidation should run"""
        time_since_last = datetime.now() - self.last_consolidation_time
        if time_since_last >= self.consolidation_interval:
            try:
                self.run_consolidation_cycle()
                self.last_consolidation_time = datetime.now()
            except Exception as e:
                logger.error(f"Auto-consolidation failed: {e}")

    def _check_auto_forgetting(self) -> None:
        """Check if automatic forgetting should run"""
        # Simple capacity check
        total_usage = len(self.working_memory) + len(self.episodic_memories) + len(self.semantic_memories)
        if total_usage > self.capacity_config.total_memories * 0.9:
            try:
                self.run_forgetting_cycle()
            except Exception as e:
                logger.error(f"Auto-forgetting failed: {e}")

    def _record_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Record a memory system operation"""
        operation_record = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }

        self.memory_operations.append(operation_record)

        # Keep only recent operations
        if len(self.memory_operations) > 1000:
            self.memory_operations = self.memory_operations[-1000:]