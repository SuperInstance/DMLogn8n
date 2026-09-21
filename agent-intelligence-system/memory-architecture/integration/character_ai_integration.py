"""
Character AI System Integration
================================

Integration layer for connecting the hierarchical memory architecture
with the existing character AI system in DMlogn8n.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

# Import memory system components
from ..core.memory_manager import MemoryManager
from ..core.memory_base import MemoryType

# Import existing DMlogn8n components (assuming they exist)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../../source_code/backend'))
    from memory_system import MemoryConsolidationEngine, Memory, MemoryType as ExistingMemoryType
    DMLOGN8N_AVAILABLE = True
except ImportError:
    DMLOGN8N_AVAILABLE = False
    logging.warning("DMlogn8n backend not found, running in standalone mode")

logger = logging.getLogger(__name__)


class CharacterAIIntegration:
    """
    Integration layer that bridges the new hierarchical memory architecture
    with the existing character AI system in DMlogn8n.
    """

    def __init__(
        self,
        character_id: str,
        character_level: int = 1,
        data_directory: str = "./data/character_ai_integration",
        enable_migration: bool = True
    ):
        self.character_id = character_id
        self.character_level = character_level
        self.data_directory = data_directory
        self.enable_migration = enable_migration

        # Initialize new memory manager
        self.memory_manager = MemoryManager(
            character_id=character_id,
            character_level=character_level,
            data_directory=data_directory,
            enable_vector_store=True,
            enable_dashboard=True
        )

        # Legacy system integration
        self.legacy_memory_engine = None
        self.legacy_memories: List[Any] = []

        # Initialize legacy system if available
        if DMLOGN8N_AVAILABLE:
            self._initialize_legacy_integration()

        # Migration status
        self.migration_completed = False
        self.migration_stats = {
            "total_legacy_memories": 0,
            "migrated_memories": 0,
            "failed_migrations": 0
        }

        # Character context cache
        self.context_cache: Dict[str, Any] = {}
        self.context_cache_expiry = 300  # 5 minutes

        logger.info(f"Character AI Integration initialized for {character_id}")

    def _initialize_legacy_integration(self) -> None:
        """Initialize integration with legacy memory system"""
        try:
            # Initialize legacy memory engine
            self.legacy_memory_engine = MemoryConsolidationEngine(self.character_id)

            # Load existing memories
            if self.legacy_memory_engine.memories:
                self.legacy_memories = list(self.legacy_memory_engine.memories.values())
                logger.info(f"Loaded {len(self.legacy_memories)} legacy memories")

                # Auto-migrate if enabled
                if self.enable_migration:
                    self._migrate_legacy_memories()

        except Exception as e:
            logger.error(f"Failed to initialize legacy integration: {e}")

    def _migrate_legacy_memories(self) -> None:
        """Migrate memories from legacy system to new architecture"""
        if not self.legacy_memories:
            return

        logger.info(f"Starting migration of {len(self.legacy_memories)} legacy memories")

        self.migration_stats["total_legacy_memories"] = len(self.legacy_memories)

        for legacy_memory in self.legacy_memories:
            try:
                # Convert legacy memory to new format
                new_memory = self._convert_legacy_memory(legacy_memory)
                if new_memory:
                    # Route to appropriate memory type
                    self.memory_manager._route_memory(new_memory)

                    # Add to vector store
                    if self.memory_manager.vector_store:
                        self.memory_manager.vector_store.add_memory(new_memory)

                    self.migration_stats["migrated_memories"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate legacy memory {legacy_memory.id}: {e}")
                self.migration_stats["failed_migrations"] += 1

        self.migration_completed = True
        logger.info(f"Migration completed: {self.migration_stats['migrated_memories']} migrated, {self.migration_stats['failed_migrations']} failed")

    def _convert_legacy_memory(self, legacy_memory: Any) -> Optional[Any]:
        """Convert legacy memory to new architecture format"""
        try:
            # Map legacy memory type to new type
            legacy_type = legacy_memory.memory_type.value if hasattr(legacy_memory.memory_type, 'value') else str(legacy_memory.memory_type)

            if legacy_type == "working":
                # Convert to working memory item
                from ..memory_types.episodic_memory import EpisodicMemory
                return EpisodicMemory(
                    content=legacy_memory.content,
                    importance=legacy_memory.importance,
                    emotional_valence=legacy_memory.emotional_valence,
                    location=legacy_memory.location,
                    participants=legacy_memory.participants,
                    context={"migrated_from_legacy": True}
                )

            elif legacy_type == "episodic":
                # Convert to episodic memory
                from ..memory_types.episodic_memory import EpisodicMemory
                return EpisodicMemory(
                    content=legacy_memory.content,
                    importance=legacy_memory.importance,
                    emotional_valence=legacy_memory.emotional_valence,
                    location=legacy_memory.location,
                    participants=legacy_memory.participants,
                    timestamp=legacy_memory.timestamp if hasattr(legacy_memory, 'timestamp') else datetime.now(),
                    context={"migrated_from_legacy": True}
                )

            elif legacy_type == "semantic":
                # Convert to semantic memory
                from ..memory_types.semantic_memory import SemanticMemory
                return SemanticMemory(
                    content=legacy_memory.content,
                    importance=legacy_memory.importance,
                    confidence=legacy_memory.metadata.confidence if hasattr(legacy_memory.metadata, 'confidence') else 0.8,
                    source="migration"
                )

            else:
                # Default to episodic for unknown types
                from ..memory_types.episodic_memory import EpisodicMemory
                return EpisodicMemory(
                    content=legacy_memory.content,
                    importance=legacy_memory.importance,
                    context={"migrated_from_legacy": True, "original_type": legacy_type}
                )

        except Exception as e:
            logger.error(f"Error converting legacy memory {legacy_memory.id}: {e}")
            return None

    def process_character_experience(
        self,
        experience_description: str,
        emotional_valence: float = 0.0,
        importance: float = 5.0,
        location: str = "",
        participants: List[str] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a character experience and store it in memory.
        This is the main entry point for character AI to interact with the memory system.
        """
        try:
            # Add to memory system
            memory = self.memory_manager.add_memory(
                content=experience_description,
                memory_type=MemoryType.EPISODIC,
                importance=importance,
                emotional_valence=emotional_valence,
                location=location,
                participants=participants or [],
                context=context or {},
                source="character_experience"
            )

            # Also update legacy system if available
            if self.legacy_memory_engine and not self.migration_completed:
                self._add_to_legacy_system(experience_description, importance, emotional_valence, location, participants)

            # Update context cache
            self._update_context_cache()

            return {
                "success": True,
                "memory_id": memory.id,
                "memory_type": memory.type.value,
                "importance": memory.importance
            }

        except Exception as e:
            logger.error(f"Failed to process character experience: {e}")
            return {"success": False, "error": str(e)}

    def get_character_context(
        self,
        include_working: bool = True,
        include_episodic: bool = True,
        include_semantic: bool = True,
        max_total: int = 20
    ) -> Dict[str, Any]:
        """
        Get current character context for AI decision making.
        Returns relevant memories formatted for AI consumption.
        """
        try:
            # Check cache first
            cache_key = f"context_{include_working}_{include_episodic}_{include_semantic}_{max_total}"
            if cache_key in self.context_cache:
                cached_data = self.context_cache[cache_key]
                if (datetime.now() - datetime.fromisoformat(cached_data["timestamp"])).seconds < self.context_cache_expiry:
                    return cached_data["context"]

            # Get context memories
            context_memories = self.memory_manager.get_context_memories(
                max_working=5 if include_working else 0,
                max_episodic=10 if include_episodic else 0,
                max_semantic=5 if include_semantic else 0
            )

            # Format for AI consumption
            formatted_context = {
                "character_id": self.character_id,
                "character_level": self.character_level,
                "timestamp": datetime.now().isoformat(),
                "memories": {
                    "working": self._format_memories_for_ai(context_memories["working"]),
                    "episodic": self._format_memories_for_ai(context_memories["episodic"]),
                    "semantic": self._format_memories_for_ai(context_memories["semantic"])
                },
                "summary": self._generate_context_summary(context_memories)
            }

            # Update cache
            self.context_cache[cache_key] = {
                "timestamp": datetime.now().isoformat(),
                "context": formatted_context
            }

            return formatted_context

        except Exception as e:
            logger.error(f"Failed to get character context: {e}")
            return {"error": str(e)}

    def retrieve_relevant_memories(
        self,
        query: str,
        max_results: int = 10,
        memory_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to a query or situation.
        Used by character AI to inform decision making.
        """
        try:
            # Convert string memory types to enum
            if memory_types:
                type_mapping = {
                    "working": MemoryType.WORKING,
                    "episodic": MemoryType.EPISODIC,
                    "semantic": MemoryType.SEMANTIC
                }
                enum_types = [type_mapping.get(t, MemoryType.EPISODIC) for t in memory_types]
            else:
                enum_types = [MemoryType.EPISODIC, MemoryType.SEMANTIC]

            # Search memories
            results = self.memory_manager.retrieve_memories(
                query=query,
                memory_types=enum_types,
                max_results=max_results
            )

            # Format for AI consumption
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "memory_id": result["memory_id"],
                    "type": result["memory_type"],
                    "content": result["document"],
                    "relevance": result.get("similarity_score", 0),
                    "importance": result["metadata"].get("importance", 0),
                    "emotional_valence": result["metadata"].get("emotional_valence", 0),
                    "context": result["metadata"]
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to retrieve relevant memories: {e}")
            return []

    def process_character_dialogue(
        self,
        dialogue: str,
        speaker: str,
        emotional_tone: str = "neutral",
        importance: float = 4.0,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process character dialogue and store as memory.
        Handles conversational memories with speaker information.
        """
        try:
            # Determine emotional valence from tone
            valence_mapping = {
                "very_positive": 0.8,
                "positive": 0.5,
                "neutral": 0.0,
                "negative": -0.5,
                "very_negative": -0.8
            }
            emotional_valence = valence_mapping.get(emotional_tone.lower(), 0.0)

            # Format dialogue content
            dialogue_content = f"Dialogue with {speaker}: '{dialogue}'"

            # Add as episodic memory
            memory = self.memory_manager.add_memory(
                content=dialogue_content,
                memory_type=MemoryType.EPISODIC,
                importance=importance,
                emotional_valence=emotional_valence,
                participants=[speaker],
                context={
                    "type": "dialogue",
                    "speaker": speaker,
                    "tone": emotional_tone,
                    **(context or {})
                },
                tags=["dialogue", "conversation"],
                source="character_dialogue"
            )

            return {
                "success": True,
                "memory_id": memory.id,
                "speaker": speaker,
                "tone": emotional_tone
            }

        except Exception as e:
            logger.error(f"Failed to process character dialogue: {e}")
            return {"success": False, "error": str(e)}

    def trigger_character_reflection(self, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger character reflection on recent experiences.
        Used to process learning from completed sessions or significant events.
        """
        try:
            # Perform reflection
            reflection_results = self.memory_manager.reflect_on_experiences()

            # Generate character-specific insights
            insights = self._generate_character_insights(reflection_results, session_context)

            return {
                "reflection_completed": True,
                "insights_generated": len(insights),
                "insights": insights,
                "reflection_details": reflection_results
            }

        except Exception as e:
            logger.error(f"Failed to trigger character reflection: {e}")
            return {"success": False, "error": str(e)}

    def update_character_level(self, new_level: int) -> Dict[str, Any]:
        """
        Update character level and adjust memory system parameters.
        Called when character levels up in the game.
        """
        try:
            old_level = self.character_level

            # Update memory manager
            self.memory_manager.update_character_level(new_level)

            self.character_level = new_level

            # Create level-up memory
            level_up_content = f"Leveled up from level {old_level} to level {new_level}! Gained new memory capacity and cognitive abilities."
            self.memory_manager.add_memory(
                content=level_up_content,
                memory_type=MemoryType.EPISODIC,
                importance=9.0,
                emotional_valence=0.8,
                context={
                    "type": "level_up",
                    "old_level": old_level,
                    "new_level": new_level
                },
                tags=["milestone", "level_up"],
                source="system_event"
            )

            return {
                "success": True,
                "old_level": old_level,
                "new_level": new_level,
                "new_capacity": self.memory_manager.capacity_config.total_memories
            }

        except Exception as e:
            logger.error(f"Failed to update character level: {e}")
            return {"success": False, "error": str(e)}

    def get_character_memory_dashboard(self) -> Optional[str]:
        """Generate HTML dashboard for character memory system"""
        return self.memory_manager.generate_dashboard_html()

    def get_memory_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the memory system"""
        try:
            status = {
                "character_id": self.character_id,
                "character_level": self.character_level,
                "memory_stats": self.memory_manager.get_memory_statistics(),
                "migration_status": {
                    "completed": self.migration_completed,
                    "stats": self.migration_stats
                },
                "legacy_integration": {
                    "available": DMLOGN8N_AVAILABLE,
                    "legacy_memories_count": len(self.legacy_memories) if self.legacy_memories else 0
                },
                "dashboard_available": self.memory_manager.dashboard is not None
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get memory system status: {e}")
            return {"error": str(e)}

    def _add_to_legacy_system(
        self,
        content: str,
        importance: float,
        emotional_valence: float,
        location: str,
        participants: List[str]
    ) -> None:
        """Add memory to legacy system for compatibility"""
        try:
            if self.legacy_memory_engine:
                # Map to legacy memory type
                legacy_memory = self.legacy_memory_engine.store_memory(
                    content=content,
                    importance=importance,
                    emotional_valence=emotional_valence,
                    participants=participants,
                    location=location
                )
                logger.debug(f"Added memory to legacy system: {legacy_memory.id}")
        except Exception as e:
            logger.error(f"Failed to add to legacy system: {e}")

    def _format_memories_for_ai(self, memories: List[Any]) -> List[Dict[str, Any]]:
        """Format memories for AI consumption"""
        formatted = []
        for memory in memories:
            formatted.append({
                "id": memory.id,
                "content": memory.content.primary_content,
                "importance": memory.importance,
                "type": memory.type.value,
                "emotional_valence": getattr(memory.metadata, 'emotional_valence', 0),
                "tags": memory.metadata.tags,
                "access_count": memory.metadata.access_count,
                "age_hours": (datetime.now() - memory.creation_time).total_seconds() / 3600
            })
        return formatted

    def _generate_context_summary(self, context_memories: Dict[str, List[Any]]) -> str:
        """Generate a summary of current context"""
        summary_parts = []

        if context_memories["working"]:
            summary_parts.append(f"Currently thinking about {len(context_memories['working'])} items")

        if context_memories["episodic"]:
            recent_count = len(context_memories["episodic"])
            summary_parts.append(f"Remembering {recent_count} recent experiences")

        if context_memories["semantic"]:
            concepts_count = len(context_memories["semantic"])
            summary_parts.append(f"Accessing {concepts_count} learned concepts")

        return "; ".join(summary_parts) if summary_parts else "No specific context available"

    def _generate_character_insights(
        self,
        reflection_results: Dict[str, Any],
        session_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate character-specific insights from reflection"""
        insights = []

        # Basic insight generation
        if reflection_results.get("insights_generated", 0) > 0:
            insights.append({
                "type": "learning",
                "description": "I've learned something new from my recent experiences",
                "importance": 7.0
            })

        if reflection_results.get("importance_updates", 0) > 0:
            insights.append({
                "type": "prioritization",
                "description": "Some memories have become more important to me",
                "importance": 6.0
            })

        # Context-specific insights
        if session_context:
            if session_context.get("combat_occurred"):
                insights.append({
                    "type": "combat_learning",
                    "description": "I've gained combat experience that will help me in future battles",
                    "importance": 8.0
                })

            if session_context.get("social_interaction"):
                insights.append({
                    "type": "social_learning",
                    "description": "My recent social interactions have taught me more about dealing with others",
                    "importance": 7.5
                })

        return insights

    def _update_context_cache(self) -> None:
        """Update context cache (clear expired entries)"""
        current_time = datetime.now()
        expired_keys = []

        for key, cached_data in self.context_cache.items():
            if isinstance(cached_data, dict) and "timestamp" in cached_data:
                cache_time = datetime.fromisoformat(cached_data["timestamp"])
                if (current_time - cache_time).seconds > self.context_cache_expiry:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.context_cache[key]