"""
Character Memory System - Vector-based Personal Memory
Each character has their own memory system with working, episodic, and semantic memory
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    WORKING = "working"      # Current session (seconds to minutes)
    EPISODIC = "episodic"  # Recent experiences (hours to days)
    SEMANTIC = "semantic"     # Long-term knowledge (days to years)
    PROCEDURAL = "procedural"  # Skills and habits (permanent)

class Memory:
    """Individual memory entry"""

    def __init__(self, content: str, memory_type: MemoryType,
                 emotional_valence: float = 0.0, importance: float = 5.0,
                 tags: List[str] = None, related_memories: List[str] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.memory_type = memory_type
        self.emotional_valence = emotional_valence  # -1.0 (negative) to 1.0 (positive)
        self.importance = importance  # 1.0 (low) to 10.0 (critical)
        self.tags = tags or []
        self.related_memories = related_memories or []
        self.timestamp = datetime.utcnow()
        self.access_count = 1
        self.last_accessed = self.timestamp

class CharacterMemorySystem:
    """Manages personal memory for a single character"""

    def __init__(self, character_id: str, vector_db_host: str,
                 api_key: str):
        self.character_id = character_id
        self.vector_db_host = vector_db_host
        self.api_key = api_key
        self.working_memory: List[Memory] = []
        self.episodic_memory: List[Memory] = []
        self.semantic_memory: List[Memory] = []
        self.procedural_memory: Dict[str, float] = {}  # skill_name -> proficiency
        self.memory_decay = {
            MemoryType.WORKING: timedelta(hours=1),      # 1 hour
            MemoryType.EPISODIC: timedelta(days=7),      # 1 week
            MemoryType.SEMANTIC: timedelta(days=90),      # 3 months
        }
        self.last_consolidation = None
        self.personality_traits = {
            "aggression": 0.5,
            "curiosity": 0.5,
            "risk_tolerance": 0.5,
            "sociality": 0.5,
            "creativity": 0.5
        }

    async def initialize(self):
        """Initialize memory system"""
        logger.info(f"Initializing memory system for {self.character_id}")
        await self.load_long_term_memory()
        await self.load_procedural_memory()

    async def store_experience(self, content: str, emotional_valence: float = 0.0,
                           importance: float = 5.0, tags: List[str] = None,
                           memory_type: MemoryType = EPISODIC):
        """Store an experience in memory"""
        memory = Memory(
            content=content,
            emotional_valence=emotional_valence,
            importance=importance,
            tags=tags,
            memory_type=memory_type
        )

        # Store in appropriate memory tier
        if memory_type == MemoryType.WORKING:
            self.working_memory.append(memory)
            # Keep only last 50 items
            if len(self.working_memory) > 50:
                self.working_memory = self.working_memory[-50:]
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append(memory)
            # Keep only last 200 experiences
            if len(self.episodic_memory) > 200:
                self.episodic_memory = self.episodic_memory[-200:]
        else:
            self.semantic_memory.append(memory)

        # Update personality traits based on experience
        await self.update_personality_from_experience(memory)

        # Add to vector database for search
        await self.store_in_vector_db(memory)

        logger.info(f"Stored experience for {self.character_id}: {memory.memory_type.value}")

    async def recall_relevant(self, query: str, context: Dict = None,
                        limit: int = 10, min_importance: float = 3.0) -> List[Memory]:
        """Recall memories relevant to query"""
        relevant_memories = []

        # Search in working memory first (most recent)
        working_matches = [
            mem for mem in self.working_memory
            if self._memory_matches_query(mem, query)
        ]
        relevant_memories.extend(working_matches[:5])

        # Then search episodic memory
        episodic_matches = [
            mem for mem in self.episodic_memory
            if (mem.importance >= min_importance and
                self._memory_matches_query(mem, query))
        ]
        relevant_memories.extend(episodic_matches[:3])

        # Finally search semantic memory
        semantic_matches = [
            mem for mem in self.semantic_memory
            if (mem.importance >= min_importance and
                self._memory_matches_query(mem, query))
        ]
        relevant_memories.extend(semantic_matches[:2])

        # Sort by relevance and return
        relevant_memories.sort(key=lambda m: self._calculate_relevance(m, query), reverse=True)
        return relevant_memories[:limit]

    def _memory_matches_query(self, memory: Memory, query: str) -> bool:
        """Check if memory matches query"""
        query_words = set(query.lower().split())
        memory_words = set(memory.content.lower().split())

        # Calculate Jaccard similarity
        intersection = query_words.intersection(memory_words)
        union = query_words.union(memory_words)
        return len(intersection) / len(union) > 0.2  # 20% overlap

    def _calculate_relevance(self, memory: Memory, query: str) -> float:
        """Calculate relevance score for memory sorting"""
        # Time decay
        days_old = (datetime.utcnow() - memory.timestamp).days
        time_factor = max(0.1, 1.0 - (days_old / 365))

        # Importance boost
        importance_factor = memory.importance / 10.0

        # Emotional relevance
        if memory.emotional_valence > 0.5:
            emotion_factor = 1.2
        elif memory.emotional_valence < -0.5:
            emotion_factor = 0.8
        else:
            emotion_factor = 1.0

        # Tag matching
        tag_boost = len(memory.tags or []) * 0.1

        return time_factor * importance_factor * emotion_factor + tag_boost

    async def update_personality_from_experience(self, memory: Memory):
        """Update personality traits based on new experience"""
        # Slowly adapt personality based on experiences
        if "combat" in memory.content.lower():
            # Combat experiences
            self.personality_traits["aggression"] += 0.01
            self.personality_traits["risk_tolerance"] -= 0.005
        elif "social" in memory.content.lower():
            # Social experiences
            self.personality_traits["sociality"] += 0.01
            self.personality_traits["aggression"] -= 0.005

        # Clamp traits to reasonable bounds
        for trait in self.personality_traits:
            self.personality_traits[trait] = max(0.0, min(1.0, self.personality_traits[trait]))

    async def consolidate_memories(self):
        """Consolidate and organize memories"""
        if not self.last_consolidation or \
           datetime.utcnow() - self.last_consolidation > timedelta(hours=24):
            return

        logger.info(f"Consolidating memories for {self.character_id}")

        # Process episodic memories
        await self.consolidate_episodic_memories()

        # Update procedural memory
        await self.update_procedural_from_experiences()

        # Clear old memories based on decay
        await self.apply_memory_decay()

        self.last_consolidation = datetime.utcnow()

    async def consolidate_episodic_memories(self):
        """Group episodic memories into themes"""
        # Group by tags or content similarity
        themes = {}
        for memory in self.episodic_memory:
            key = " ".join(memory.tags or [])[:2]  # Use first two tags as theme key
            if key not in themes:
                themes[key] = []
            themes[key].append(memory)

        # Create summary memories for each theme
        for theme_key, theme_memories in themes.items():
            if len(theme_memories) >= 3:
                summary = self.create_theme_summary(theme_key, theme_memories)
                summary_memory = Memory(
                    content=f"Theme: {theme_key}. Summary: {summary}",
                    memory_type=MemoryType.SEMANTIC,
                    importance=7.0,
                    tags=[theme_key, "summary", "consolidated"]
                )
                self.semantic_memory.append(summary_memory)

    def create_theme_summary(self, theme: str, memories: List[Memory]) -> str:
        """Create summary of memories for a theme"""
        # Extract key information from memories
        actions = []
        outcomes = []
        emotions = []

        for memory in memories:
            if "attack" in memory.content.lower():
                actions.append("Combat encounter")
                outcomes.append(memory.content)
            elif "talk" in memory.content.lower():
                actions.append("Social interaction")
                outcomes.append(memory.content)
            emotions.append(memory.emotional_valence)

        # Generate summary
        avg_emotion = np.mean(emotions) if emotions else 0.0
        return f"Experienced {len(set(actions))} different types of interactions. {' and '.join(set(actions[:3]))}... Outcomes ranged from {'positive' if avg_emotion > 0 else 'mixed'}."

    async def update_procedural_from_experiences(self):
        """Update procedural skills from experiences"""
        skill_progress = {}

        # Analyze episodic memories for skill usage
        for memory in self.episodic_memory:
            if "skill_check" in memory.content.lower():
                # Extract skill type
                for skill in ["persuasion", "intimidation", "deception", "perception", "stealth", "acrobatics"]:
                    if skill in memory.content.lower():
                        current = self.procedural_memory.get(skill, 0.5)
                        # Increment based on success/failure
                        if "success" in memory.content.lower():
                            new_value = min(1.0, current + 0.05)
                        else:
                            new_value = max(0.1, current - 0.02)
                        skill_progress[skill] = new_value

        # Update procedural memory
        for skill, value in skill_progress.items():
            self.procedural_memory[skill] = value

    async def apply_memory_decay(self):
        """Apply time-based decay to memories"""
        now = datetime.utcnow()

        # Decay working memory
        self.working_memory = [
            mem for mem in self.working_memory
            if now - mem.timestamp < self.memory_decay[MemoryType.WORKING]
        ]

        # Decay episodic memory
        self.episodic_memory = [
            mem for mem in self.episodic_memory
            if now - mem.timestamp < self.memory_decay[MemoryType.EPISODIC]
        ]

        # Decay semantic memory slowly
        self.semantic_memory = [
            mem for mem in self.semantic_memory
            if now - mem.timestamp < self.memory_decay[MemoryType.SEMANTIC]
        ]

        logger.info(f"Applied memory decay for {self.character_id}")

    async def store_in_vector_db(self, memory: Memory):
        """Store memory embedding in vector database"""
        # This would integrate with Qdrant or other vector DB
        # For now, just log
        logger.info(f"Would store in vector DB: {memory.content[:100]}...")

    async def get_memory_summary(self) -> Dict:
        """Get comprehensive summary of character's memory"""
        return {
            "working_memory_count": len(self.working_memory),
            "episodic_memory_count": len(self.episodic_memory),
            "semantic_memory_count": len(self.semantic_memory),
            "personality_traits": self.personality_traits,
            "last_consolidation": self.last_consolidation.isoformat() if self.last_consolidation else None,
            "strongest_theme": self.find_dominant_theme()
        }

    def find_dominant_theme(self) -> Optional[str]:
        """Find the most common theme in semantic memory"""
        theme_counts = {}
        for memory in self.semantic_memory:
            for tag in memory.tags or []:
                theme_counts[tag] = theme_counts.get(tag, 0) + 1

        if theme_counts:
            return max(theme_counts, key=theme_counts.get)
        return None

class MemoryManager:
    """Manages memory systems for all characters"""

    def __init__(self):
        self.character_memories: Dict[str, CharacterMemorySystem] = {}

    async def get_character_memory(self, character_id: str) -> CharacterMemorySystem:
        """Get or create memory system for character"""
        if character_id not in self.character_memories:
            # Create new memory system
            from config.settings import get_memory_config
            config = get_memory_config()
            memory_system = CharacterMemorySystem(character_id, config['vector_db_host'], config['api_key'])
            await memory_system.initialize()
            self.character_memories[character_id] = memory_system
            logger.info(f"Created new memory system for {character_id}")

        return self.character_memories[character_id]

    async def get_all_character_memories(self) -> Dict[str, Dict]:
        """Get memory summaries for all characters"""
        summaries = {}
        for character_id, memory_system in self.character_memories.items():
            summaries[character_id] = await memory_system.get_memory_summary()
        return summaries