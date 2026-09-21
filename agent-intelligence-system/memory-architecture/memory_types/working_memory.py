"""
Working Memory Implementation
==============================

Working memory represents the agent's current conscious thoughts and immediate context.
It has very limited capacity and high volatility, mimicking human working memory constraints.
"""

import heapq
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
import math

from ..core.memory_base import MemoryBase, MemoryType, MemoryContent, MemoryMetadata


class WorkingMemoryItem:
    """Item in working memory with activation tracking"""

    def __init__(self, memory: MemoryBase, activation: float = 1.0):
        self.memory = memory
        self.activation = activation  # 0-1, how active this item is
        self.last_activated = datetime.now()
        self.decay_rate = 0.1  # How quickly activation decays

    def update_activation(self, delta_time: float) -> None:
        """Update activation based on time decay"""
        decay = self.decay_rate * delta_time
        self.activation = max(0, self.activation - decay)
        self.last_activated = datetime.now()

    def boost_activation(self, boost: float = 0.3) -> None:
        """Boost activation (e.g., when accessed)"""
        self.activation = min(1.0, self.activation + boost)
        self.last_activated = datetime.now()

    def get_priority_score(self) -> float:
        """Calculate priority score for retention"""
        # Combine activation, importance, and recency
        recency_bonus = 1.0 / (1.0 + (datetime.now() - self.last_activated).total_seconds() / 60.0)
        return self.activation * 0.6 + (self.memory.importance / 10.0) * 0.3 + recency_bonus * 0.1


class WorkingMemory:
    """
    Working Memory System with limited capacity and activation-based retention.
    Mimics human working memory with ~7±2 item capacity and rapid decay.
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.items: Dict[str, WorkingMemoryItem] = OrderedDict()
        self.last_update = datetime.now()

        # Working memory parameters
        self.base_decay_rate = 0.05  # Per second
        self.activation_threshold = 0.1  # Minimum activation to stay in working memory
        self.max_activation = 1.0

        # Statistics
        self.total_items_added = 0
        self.total_items_evicted = 0
        self.average_activation = 0.0

    def add_memory(self, memory: MemoryBase, initial_activation: float = 1.0) -> bool:
        """
        Add a memory to working memory. Returns False if memory is rejected.
        """
        # Check if memory is already in working memory
        if memory.id in self.items:
            self.items[memory.id].boost_activation(initial_activation)
            return True

        # Make space if needed
        if len(self.items) >= self.capacity:
            if not self._evict_weakest():
                return False  # Could not evict any item

        # Add new item
        item = WorkingMemoryItem(memory, initial_activation)
        self.items[memory.id] = item
        self.total_items_added += 1

        # Record access in original memory
        memory.access()

        return True

    def get_memory(self, memory_id: str) -> Optional[MemoryBase]:
        """Retrieve a memory from working memory"""
        if memory_id in self.items:
            item = self.items[memory_id]
            item.boost_activation()
            return item.memory
        return None

    def retrieve_by_relevance(self, query: str, max_results: int = 5) -> List[Tuple[MemoryBase, float]]:
        """
        Retrieve memories by relevance to query, considering activation.
        """
        self._update_activations()  # Update decay before retrieval

        results = []
        for item in self.items.values():
            if item.activation < self.activation_threshold:
                continue

            # Calculate relevance score
            relevance = item.memory.calculate_retrieval_score(query, {})
            # Weight by activation
            combined_score = relevance * item.activation * 0.7 + item.memory.importance / 10.0 * 0.3
            results.append((item.memory, combined_score))

        # Sort by combined score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def get_active_context(self, max_items: int = None) -> List[MemoryBase]:
        """
        Get currently active memories as context.
        """
        if max_items is None:
            max_items = self.capacity

        self._update_activations()

        # Sort by activation
        active_items = [(item.activation, item.memory) for item in self.items.values()
                       if item.activation >= self.activation_threshold]
        active_items.sort(reverse=True)

        return [memory for _, memory in active_items[:max_items]]

    def update_activations(self) -> None:
        """Force update of all activation levels"""
        self._update_activations()

    def clear(self) -> None:
        """Clear all items from working memory"""
        self.items.clear()
        self.last_update = datetime.now()

    def _update_activations(self) -> None:
        """Update activation levels based on time decay"""
        current_time = datetime.now()
        delta_seconds = (current_time - self.last_update).total_seconds()

        items_to_remove = []

        for memory_id, item in self.items.items():
            item.update_activation(delta_seconds)

            # Mark for removal if activation is too low
            if item.activation < self.activation_threshold:
                items_to_remove.append(memory_id)

        # Remove low-activation items
        for memory_id in items_to_remove:
            del self.items[memory_id]
            self.total_items_evicted += 1

        # Calculate average activation
        if self.items:
            self.average_activation = sum(item.activation for item in self.items.values()) / len(self.items)
        else:
            self.average_activation = 0.0

        self.last_update = current_time

    def _evict_weakest(self) -> bool:
        """Evict the weakest memory to make space"""
        if not self.items:
            return False

        # Find the weakest item
        weakest_id = min(self.items.keys(), key=lambda mid: self.items[mid].get_priority_score())

        # Evict it
        del self.items[weakest_id]
        self.total_items_evicted += 1
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get working memory statistics"""
        self._update_activations()

        return {
            "capacity": self.capacity,
            "current_items": len(self.items),
            "utilization": len(self.items) / self.capacity,
            "average_activation": self.average_activation,
            "total_items_added": self.total_items_added,
            "total_items_evicted": self.total_items_evicted,
            "average_item_lifetime": self._calculate_average_lifetime(),
            "activation_distribution": self._get_activation_distribution()
        }

    def _calculate_average_lifetime(self) -> float:
        """Calculate average lifetime of items in working memory (in seconds)"""
        if not self.items or self.total_items_evicted == 0:
            return 0.0

        # This is a simplified calculation
        return 60.0  # Placeholder - would need actual timing data

    def _get_activation_distribution(self) -> Dict[str, int]:
        """Get distribution of activation levels"""
        distribution = {"high": 0, "medium": 0, "low": 0}

        for item in self.items.values():
            if item.activation > 0.7:
                distribution["high"] += 1
            elif item.activation > 0.3:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def consolidate_to_episodic(self, min_importance: float = 5.0) -> List[MemoryBase]:
        """
        Get memories ready for consolidation to episodic memory.
        """
        candidates = []

        for item in self.items.values():
            memory = item.memory

            # Check if memory meets consolidation criteria
            if (memory.importance >= min_importance and
                memory.metadata.access_count >= 1 and
                item.activation < 0.5):  # No longer highly active

                candidates.append(memory)

        return candidates

    def set_contextual_focus(self, context_type: str, boost_factor: float = 0.3) -> None:
        """
        Boost activation of memories related to specific context.
        """
        for item in self.items.values():
            memory = item.memory

            # Check if memory is relevant to context
            if context_type in memory.metadata.tags or \
               context_type.lower() in memory.content.primary_content.lower():
                item.boost_activation(boost_factor)

    def decay_all(self, decay_factor: float = 0.8) -> None:
        """
        Apply global decay to all items (e.g., during sleep or distraction).
        """
        for item in self.items.values():
            item.activation *= decay_factor

        # Remove items that fell below threshold
        items_to_remove = [mid for mid, item in self.items.items()
                          if item.activation < self.activation_threshold]

        for memory_id in items_to_remove:
            del self.items[memory_id]
            self.total_items_evicted += 1

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, memory_id: str) -> bool:
        return memory_id in self.items

    def __iter__(self):
        return iter(item.memory for item in self.items.values())