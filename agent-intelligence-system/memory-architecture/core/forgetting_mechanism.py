"""
Forgetting Mechanism for Memory Management
==========================================

Intelligent forgetting system that manages memory capacity by selectively
forgetting less important memories while preserving valuable knowledge.
"""

import math
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .memory_base import MemoryBase, MemoryType, MemoryImportance, MemoryStatus
from ..memory_types.working_memory import WorkingMemory
from ..memory_types.episodic_memory import EpisodicMemory
from ..memory_types.semantic_memory import SemanticMemory


logger = logging.getLogger(__name__)


class ForgettingStrategy:
    """Base class for forgetting strategies"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select memories to forget based on strategy"""
        raise NotImplementedError("Subclasses must implement select_memories_to_forget")


class ImportanceBasedForgetting(ForgettingStrategy):
    """Forget memories with lowest importance scores"""

    def __init__(self):
        super().__init__(
            "importance_based",
            "Forget memories with lowest importance scores"
        )

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select memories with lowest importance for forgetting"""
        # Sort by importance (ascending)
        sorted_memories = sorted(memories, key=lambda m: m.importance)

        # Select lowest importance memories
        to_forget = sorted_memories[:forget_count]

        logger.debug(f"Importance-based forgetting: selected {len(to_forget)} memories")
        return to_forget


class RecencyBasedForgetting(ForgettingStrategy):
    """Forget oldest memories first"""

    def __init__(self):
        super().__init__(
            "recency_based",
            "Forget oldest memories first"
        )

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select oldest memories for forgetting"""
        # Sort by creation time (ascending)
        sorted_memories = sorted(memories, key=lambda m: m.creation_time)

        # Select oldest memories
        to_forget = sorted_memories[:forget_count]

        logger.debug(f"Recency-based forgetting: selected {len(to_forget)} memories")
        return to_forget


class AccessBasedForgetting(ForgettingStrategy):
    """Forget memories with lowest access frequency"""

    def __init__(self):
        super().__init__(
            "access_based",
            "Forget memories with lowest access frequency"
        )

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select memories with lowest access frequency for forgetting"""
        # Sort by access count (ascending), then by last accessed time
        sorted_memories = sorted(
            memories,
            key=lambda m: (
                m.metadata.access_count,
                m.metadata.last_accessed or datetime.min
            )
        )

        # Select least accessed memories
        to_forget = sorted_memories[:forget_count]

        logger.debug(f"Access-based forgetting: selected {len(to_forget)} memories")
        return to_forget


class CompositeForgetting(ForgettingStrategy):
    """Combine multiple factors for intelligent forgetting"""

    def __init__(self, weights: Dict[str, float] = None):
        default_weights = {
            "importance": 0.4,
            "recency": 0.3,
            "access_frequency": 0.2,
            "emotional_impact": 0.1
        }
        self.weights = weights or default_weights

        super().__init__(
            "composite",
            f"Intelligent forgetting with weights: {self.weights}"
        )

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select memories using composite scoring"""
        scored_memories = []

        for memory in memories:
            score = self._calculate_forgetting_score(memory)
            scored_memories.append((score, memory))

        # Sort by score (ascending - lower scores are forgotten first)
        scored_memories.sort(key=lambda x: x[0])

        # Select memories with lowest scores
        to_forget = [memory for _, memory in scored_memories[:forget_count]]

        logger.debug(f"Composite forgetting: selected {len(to_forget)} memories")
        return to_forget

    def _calculate_forgetting_score(self, memory: MemoryBase) -> float:
        """Calculate forgetting score (lower = more likely to be forgotten)"""
        # Importance factor (lower importance = lower score)
        importance_score = memory.importance

        # Recency factor (older = lower score)
        days_old = (datetime.now() - memory.creation_time).days
        recency_score = math.exp(-days_old / 30.0)  # 30-day decay

        # Access frequency factor (less accessed = lower score)
        access_score = min(memory.metadata.access_count / 10.0, 1.0)

        # Emotional impact factor (less emotional = lower score)
        emotional_score = abs(memory.metadata.emotional_valence)

        # Composite score
        total_score = (
            self.weights["importance"] * importance_score +
            self.weights["recency"] * recency_score +
            self.weights["access_frequency"] * access_score +
            self.weights["emotional_impact"] * emotional_score
        )

        return total_score


class AdaptiveForgetting(ForgettingStrategy):
    """Adaptive forgetting that learns from memory performance"""

    def __init__(self):
        super().__init__(
            "adaptive",
            "Adaptive forgetting that learns from memory performance"
        )
        self.memory_performance: Dict[str, Dict[str, float]] = {}
        self.decay_rates: Dict[MemoryType, float] = {
            MemoryType.WORKING: 0.8,
            MemoryType.EPISODIC: 0.9,
            MemoryType.SEMANTIC: 0.95
        }

    def select_memories_to_forget(
        self,
        memories: List[MemoryBase],
        capacity_limit: int,
        forget_count: int
    ) -> List[MemoryBase]:
        """Select memories using adaptive scoring"""
        scored_memories = []

        for memory in memories:
            score = self._calculate_adaptive_score(memory)
            scored_memories.append((score, memory))

        # Sort by score (ascending)
        scored_memories.sort(key=lambda x: x[0])

        # Select memories with lowest scores
        to_forget = [memory for _, memory in scored_memories[:forget_count]]

        logger.debug(f"Adaptive forgetting: selected {len(to_forget)} memories")
        return to_forget

    def _calculate_adaptive_score(self, memory: MemoryBase) -> float:
        """Calculate adaptive forgetting score"""
        base_score = memory.importance

        # Type-specific decay
        type_decay = self.decay_rates.get(memory.type, 0.9)

        # Performance-based adjustment
        performance_adjustment = self.memory_performance.get(memory.id, {}).get("success_rate", 1.0)

        # Adaptive score
        adaptive_score = base_score * type_decay * performance_adjustment

        return adaptive_score

    def update_memory_performance(self, memory_id: str, success: bool) -> None:
        """Update performance tracking for a memory"""
        if memory_id not in self.memory_performance:
            self.memory_performance[memory_id] = {
                "total_accesses": 0,
                "successful_accesses": 0,
                "success_rate": 1.0
            }

        perf = self.memory_performance[memory_id]
        perf["total_accesses"] += 1

        if success:
            perf["successful_accesses"] += 1

        perf["success_rate"] = perf["successful_accesses"] / perf["total_accesses"]


class ForgettingMechanism:
    """
    Main forgetting mechanism that manages memory capacity by intelligent forgetting.
    """

    def __init__(
        self,
        character_level: int = 1,
        strategy: ForgettingStrategy = None
    ):
        self.character_level = character_level

        # Capacity limits based on level
        self.capacity_limits = self._get_capacity_limits(character_level)

        # Forgetting strategy
        self.strategy = strategy or CompositeForgetting()

        # Forgetting history
        self.forgetting_history: List[Dict[str, Any]] = []

        # Protection rules (memories that should not be forgotten)
        self.protection_rules = self._initialize_protection_rules()

        # Statistics
        self.total_forgotten = 0
        self.forgetting_by_type = defaultdict(int)
        self.forgetting_by_importance = defaultdict(int)

    def manage_capacity(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> Dict[str, Any]:
        """Manage memory capacity by forgetting memories if needed"""
        capacity_results = {
            "timestamp": datetime.now().isoformat(),
            "capacity_before": {},
            "capacity_after": {},
            "forgotten_memories": [],
            "protection_applied": [],
            "strategy_used": self.strategy.name
        }

        try:
            # Check current capacity usage
            capacity_before = self._calculate_current_capacity(
                working_memory, episodic_memories, semantic_memories
            )
            capacity_results["capacity_before"] = capacity_before

            # Check if forgetting is needed
            forgetting_needed = self._check_forgetting_needed(capacity_before)

            if not forgetting_needed:
                logger.debug("No forgetting needed - within capacity limits")
                return capacity_results

            logger.info(f"Starting capacity management - forgetting needed")

            # Apply forgetting to each memory type
            forgetting_results = {}

            # Working memory
            working_results = self._forget_working_memories(working_memory)
            forgetting_results["working"] = working_results

            # Episodic memory
            episodic_results = self._forget_episodic_memories(episodic_memories)
            forgetting_results["episodic"] = episodic_results

            # Semantic memory (least likely to be forgotten)
            semantic_results = self._forget_semantic_memories(semantic_memories)
            forgetting_results["semantic"] = semantic_results

            # Combine results
            all_forgotten = []
            for mem_type, results in forgetting_results.items():
                all_forgotten.extend(results.get("forgotten", []))
                capacity_results["forgotten_memories"].extend(results.get("forgotten", []))

            # Calculate capacity after forgetting
            capacity_after = self._calculate_current_capacity(
                working_memory, episodic_memories, semantic_memories
            )
            capacity_results["capacity_after"] = capacity_after

            # Update statistics
            self.total_forgotten += len(all_forgotten)
            for memory in all_forgotten:
                self.forgetting_by_type[memory.type.value] += 1
                self.forgetting_by_importance[int(memory.importance)] += 1

            # Record in history
            self.forgetting_history.append(capacity_results)

            logger.info(f"Capacity management completed - forgot {len(all_forgotten)} memories")

        except Exception as e:
            logger.error(f"Capacity management failed: {e}")
            capacity_results["error"] = str(e)

        return capacity_results

    def add_protection_rule(self, rule_name: str, condition: Dict[str, Any]) -> None:
        """Add a rule to protect certain memories from forgetting"""
        self.protection_rules[rule_name] = condition
        logger.debug(f"Added protection rule: {rule_name}")

    def remove_protection_rule(self, rule_name: str) -> None:
        """Remove a protection rule"""
        if rule_name in self.protection_rules:
            del self.protection_rules[rule_name]
            logger.debug(f"Removed protection rule: {rule_name}")

    def is_memory_protected(self, memory: MemoryBase) -> bool:
        """Check if a memory is protected from forgetting"""
        for rule_name, condition in self.protection_rules.items():
            if self._evaluate_protection_condition(memory, condition):
                return True
        return False

    def set_strategy(self, strategy: ForgettingStrategy) -> None:
        """Change the forgetting strategy"""
        self.strategy = strategy
        logger.info(f"Changed forgetting strategy to: {strategy.name}")

    def get_forgetting_statistics(self) -> Dict[str, Any]:
        """Get forgetting mechanism statistics"""
        return {
            "character_level": self.character_level,
            "capacity_limits": self.capacity_limits,
            "strategy": self.strategy.name,
            "strategy_description": self.strategy.description,
            "total_forgotten": self.total_forgotten,
            "forgetting_by_type": dict(self.forgetting_by_type),
            "forgetting_by_importance": dict(self.forgetting_by_importance),
            "protection_rules": list(self.protection_rules.keys()),
            "recent_history": self.forgetting_history[-10:]  # Last 10 operations
        }

    def _calculate_current_capacity(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> Dict[str, Any]:
        """Calculate current memory usage"""
        working_usage = len(working_memory)
        episodic_usage = len(episodic_memories)
        semantic_usage = len(semantic_memories)

        total_usage = working_usage + episodic_usage + semantic_usage

        return {
            "working": {
                "current": working_usage,
                "limit": self.capacity_limits["working"],
                "utilization": working_usage / self.capacity_limits["working"]
            },
            "episodic": {
                "current": episodic_usage,
                "limit": self.capacity_limits["episodic"],
                "utilization": episodic_usage / self.capacity_limits["episodic"]
            },
            "semantic": {
                "current": semantic_usage,
                "limit": self.capacity_limits["semantic"],
                "utilization": semantic_usage / self.capacity_limits["semantic"]
            },
            "total": {
                "current": total_usage,
                "limit": self.capacity_limits["total"],
                "utilization": total_usage / self.capacity_limits["total"]
            }
        }

    def _check_forgetting_needed(self, capacity_info: Dict[str, Any]) -> bool:
        """Check if forgetting is needed based on capacity"""
        # Check if any memory type exceeds 80% capacity
        threshold = 0.8

        for mem_type in ["working", "episodic", "semantic"]:
            utilization = capacity_info[mem_type]["utilization"]
            if utilization > threshold:
                logger.debug(f"Forgetting needed for {mem_type}: {utilization:.1%} utilization")
                return True

        # Check total capacity
        total_utilization = capacity_info["total"]["utilization"]
        if total_utilization > threshold:
            logger.debug(f"Forgetting needed for total: {total_utilization:.1%} utilization")
            return True

        return False

    def _forget_working_memories(self, working_memory: WorkingMemory) -> Dict[str, Any]:
        """Forget memories from working memory"""
        results = {"forgotten": [], "protected": []}

        # Get all working memory items
        all_items = list(working_memory.items.values())
        memories = [item.memory for item in all_items]

        # Filter out protected memories
        candidates = [m for m in memories if not self.is_memory_protected(m)]
        protected = [m for m in memories if self.is_memory_protected(m)]
        results["protected"] = protected

        # Calculate how many to forget
        current_count = len(memories)
        limit = self.capacity_limits["working"]

        if current_count <= limit:
            return results

        forget_count = current_count - limit
        forget_count = min(forget_count, len(candidates))

        if forget_count <= 0:
            return results

        # Select memories to forget
        to_forget = self.strategy.select_memories_to_forget(
            candidates, limit, forget_count
        )

        # Remove from working memory
        for memory in to_forget:
            if memory.id in working_memory.items:
                del working_memory.items[memory.id]
                memory.status = MemoryStatus.FORGOTTEN
                results["forgotten"].append(memory)

        logger.debug(f"Forgot {len(to_forget)} working memories")
        return results

    def _forget_episodic_memories(self, episodic_memories: List[EpisodicMemory]) -> Dict[str, Any]:
        """Forget episodic memories"""
        results = {"forgotten": [], "protected": []}

        # Filter out protected memories
        candidates = [m for m in episodic_memories if m.status == MemoryStatus.ACTIVE]
        candidates = [m for m in candidates if not self.is_memory_protected(m)]
        protected = [m for m in episodic_memories if self.is_memory_protected(m)]
        results["protected"] = protected

        # Calculate how many to forget
        current_count = len([m for m in episodic_memories if m.status == MemoryStatus.ACTIVE])
        limit = self.capacity_limits["episodic"]

        if current_count <= limit:
            return results

        forget_count = current_count - limit
        forget_count = min(forget_count, len(candidates))

        if forget_count <= 0:
            return results

        # Select memories to forget
        to_forget = self.strategy.select_memories_to_forget(
            candidates, limit, forget_count
        )

        # Mark as forgotten
        for memory in to_forget:
            memory.status = MemoryStatus.FORGOTTEN
            results["forgotten"].append(memory)

        logger.debug(f"Forgot {len(to_forget)} episodic memories")
        return results

    def _forget_semantic_memories(self, semantic_memories: List[SemanticMemory]) -> Dict[str, Any]:
        """Forget semantic memories (rare, only if absolutely necessary)"""
        results = {"forgotten": [], "protected": []}

        # Semantic memories are rarely forgotten - only if severely over capacity
        current_count = len([m for m in semantic_memories if m.status == MemoryStatus.ACTIVE])
        limit = self.capacity_limits["semantic"]

        # Only forget if > 95% capacity
        if current_count <= limit * 0.95:
            return results

        # Filter candidates (only low-importance, low-confidence memories)
        candidates = [
            m for m in semantic_memories
            if (m.status == MemoryStatus.ACTIVE and
                m.importance < 5.0 and
                m.confidence < 0.5 and
                not self.is_memory_protected(m))
        ]

        protected = [m for m in semantic_memories if self.is_memory_protected(m)]
        results["protected"] = protected

        forget_count = min(5, len(candidates))  # Max 5 semantic memories at once

        if forget_count <= 0:
            return results

        # Select memories to forget
        to_forget = self.strategy.select_memories_to_forget(
            candidates, limit, forget_count
        )

        # Mark as forgotten
        for memory in to_forget:
            memory.status = MemoryStatus.FORGOTTEN
            results["forgotten"].append(memory)

        logger.debug(f"Forgot {len(to_forget)} semantic memories")
        return results

    def _evaluate_protection_condition(self, memory: MemoryBase, condition: Dict[str, Any]) -> bool:
        """Evaluate if a memory matches a protection condition"""
        for key, value in condition.items():
            if key == "importance":
                if memory.importance < value:
                    return False
            elif key == "memory_type":
                if memory.type.value != value:
                    return False
            elif key == "tags":
                if not any(tag in memory.metadata.tags for tag in value):
                    return False
            elif key == "source":
                if memory.metadata.source != value:
                    return False
            elif key == "age_days":
                age = (datetime.now() - memory.creation_time).days
                if age > value:
                    return False

        return True

    def _initialize_protection_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default protection rules"""
        return {
            "high_importance": {
                "importance": 9.0
            },
            "temporal_landmarks": {
                "tags": ["temporal_landmark"]
            },
            "recent_important": {
                "importance": 7.0,
                "age_days": 1
            },
            "core_concepts": {
                "memory_type": "semantic",
                "importance": 8.0
            }
        }

    def _get_capacity_limits(self, level: int) -> Dict[str, int]:
        """Get capacity limits based on character level"""
        # Working memory capacity
        if level <= 4:
            working = 5
        elif level <= 10:
            working = 10
        elif level <= 16:
            working = 15
        else:
            working = 25

        # Total memory capacity
        if level <= 4:
            total = 50
        elif level <= 10:
            total = 200
        elif level <= 16:
            total = 500
        else:
            total = 1000

        # Allocate capacity between types
        semantic = int(total * 0.3)  # 30% for semantic
        episodic = int(total * 0.5)  # 50% for episodic
        working = min(working, int(total * 0.2))  # 20% for working memory

        return {
            "working": working,
            "episodic": episodic,
            "semantic": semantic,
            "total": total
        }

    def update_character_level(self, new_level: int) -> None:
        """Update capacity limits based on new character level"""
        self.character_level = new_level
        self.capacity_limits = self._get_capacity_limits(new_level)
        logger.info(f"Updated capacity limits for level {new_level}")