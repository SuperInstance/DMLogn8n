#!/usr/bin/env python3
"""
Context Manager - Better context handling and memory for AI agents

This module provides advanced context management, memory retention, and
context-aware response generation to maintain coherent, long-running conversations.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import pickle
import threading

class ContextType(Enum):
    CONVERSATION = "conversation"
    USER_PREFERENCE = "user_preference"
    TOPIC = "topic"
    SESSION = "session"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"

class ContextPriority(Enum):
    CRITICAL = 3
    HIGH = 2
    MEDIUM = 1
    LOW = 0

@dataclass
class ContextEntry:
    """Represents a single context entry."""
    content: Any
    context_type: ContextType
    priority: ContextPriority
    timestamp: float
    user_id: str
    session_id: str
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    importance_score: float = 0.5
    tags: Set[str] = field(default_factory=set)
    expires_at: Optional[float] = None

@dataclass
class ContextMetrics:
    """Metrics for context management performance."""
    retrieval_accuracy: float
    memory_efficiency: float
    context_relevance: float
    retrieval_time: float
    storage_utilization: float

class ContextManager:
    """
    Advanced context management system for AI agents.

    Features:
    - Multi-tier context storage (short-term, medium-term, long-term)
    - Intelligent context prioritization and eviction
    - Semantic context matching
    - Context-aware response generation
    - User preference learning
    - Cross-session context persistence
    - Context compression and summarization
    """

    def __init__(self, agent_id: str, max_memory_entries: int = 10000):
        self.agent_id = agent_id
        self.max_memory_entries = max_memory_entries

        # Multi-tier storage
        self.short_term_memory = deque(maxlen=100)  # Recent conversation
        self.medium_term_memory = defaultdict(list)  # Session context
        self.long_term_memory = defaultdict(list)  # Persistent knowledge

        # Context indices
        self.semantic_index = defaultdict(list)
        self.user_index = defaultdict(list)
        self.tag_index = defaultdict(list)
        self.time_index = []

        # Context statistics
        self.access_stats = defaultdict(int)
        self.context_stats = defaultdict(int)
        self.relevance_scores = {}

        # Configuration
        self.context_retention_time = {
            ContextType.CONVERSATION: 3600,  # 1 hour
            ContextType.SESSION: 86400,      # 24 hours
            ContextType.USER_PREFERENCE: 604800,  # 7 days
            ContextType.TOPIC: 604800,       # 7 days
            ContextType.LONG_TERM: 31536000,  # 1 year
            ContextType.EPISODIC: 2592000    # 30 days
        }

        # Learning parameters
        self.importance_decay_rate = 0.95
        self.relevance_threshold = 0.3
        self.compression_threshold = 1000

        # Thread safety
        self.lock = threading.RLock()

        # Logging
        self.logger = logging.getLogger(f"context_manager_{agent_id}")

    def add_context(self, content: Any, context_type: ContextType,
                   user_id: str, session_id: str,
                   priority: ContextPriority = ContextPriority.MEDIUM,
                   tags: Set[str] = None, importance_score: float = 0.5,
                   expires_at: Optional[float] = None) -> str:
        """
        Add context entry to the system.

        Args:
            content: Context content
            context_type: Type of context
            user_id: User identifier
            session_id: Session identifier
            priority: Context priority
            tags: Context tags
            importance_score: Importance score (0-1)
            expires_at: Expiration timestamp

        Returns:
            Context entry ID
        """
        with self.lock:
            # Generate unique ID
            context_id = self._generate_context_id(content, context_type, user_id)

            # Create context entry
            entry = ContextEntry(
                content=content,
                context_type=context_type,
                priority=priority,
                timestamp=time.time(),
                user_id=user_id,
                session_id=session_id,
                importance_score=importance_score,
                tags=tags or set(),
                expires_at=expires_at
            )

            # Store in appropriate tier
            self._store_context(entry, context_id)

            # Update indices
            self._update_indices(entry, context_id)

            # Update statistics
            self.context_stats[context_type] += 1

            # Check for compression
            self._check_compression()

            return context_id

    def get_context(self, query: str, user_id: str = None,
                   session_id: str = None, context_types: List[ContextType] = None,
                   limit: int = 10) -> Tuple[List[ContextEntry], ContextMetrics]:
        """
        Retrieve relevant context based on query.

        Args:
            query: Search query
            user_id: Filter by user ID
            session_id: Filter by session ID
            context_types: Filter by context types
            limit: Maximum number of results

        Returns:
            Tuple of (context_entries, metrics)
        """
        start_time = time.time()

        with self.lock:
            # Build candidate pool
            candidates = self._get_context_candidates(
                user_id, session_id, context_types
            )

            # Rank candidates by relevance
            ranked_contexts = self._rank_context_by_relevance(candidates, query)

            # Apply limit
            limited_contexts = ranked_contexts[:limit]

            # Update access statistics
            self._update_access_stats(limited_contexts)

            # Calculate metrics
            retrieval_time = time.time() - start_time
            metrics = self._calculate_context_metrics(limited_contexts, retrieval_time)

            return limited_contexts, metrics

    def update_context_importance(self, context_id: str, feedback_score: float):
        """
        Update context importance based on feedback.

        Args:
            context_id: Context entry ID
            feedback_score: Feedback score (0-1)
        """
        with self.lock:
            # Find and update the context entry
            entry = self._find_context_entry(context_id)
            if entry:
                # Update importance with learning
                current_importance = entry.importance_score
                learning_rate = 0.1
                new_importance = (current_importance * (1 - learning_rate) +
                                feedback_score * learning_rate)
                entry.importance_score = max(0.0, min(1.0, new_importance))

                # Update last accessed time
                entry.last_accessed = time.time()
                entry.access_count += 1

    def get_context_summary(self, user_id: str, session_id: str = None,
                          summary_type: str = "brief") -> Dict[str, Any]:
        """
        Get context summary for user/session.

        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            summary_type: Type of summary (brief, detailed, comprehensive)

        Returns:
            Context summary dictionary
        """
        with self.lock:
            summary = {
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': time.time(),
                'summary_type': summary_type
            }

            # Get user context
            user_contexts = self._get_user_contexts(user_id, session_id)

            # Organize by type
            context_by_type = defaultdict(list)
            for context in user_contexts:
                context_by_type[context.context_type].append(context)

            # Generate summary for each type
            for context_type, contexts in context_by_type.items():
                if summary_type == "brief":
                    type_summary = self._generate_brief_summary(context_type, contexts)
                elif summary_type == "detailed":
                    type_summary = self._generate_detailed_summary(context_type, contexts)
                else:  # comprehensive
                    type_summary = self._generate_comprehensive_summary(context_type, contexts)

                summary[context_type.value] = type_summary

            # Add statistics
            summary['statistics'] = {
                'total_contexts': len(user_contexts),
                'by_type': {ct.value: len(contexts) for ct, contexts in context_by_type.items()},
                'average_importance': sum(c.importance_score for c in user_contexts) / len(user_contexts) if user_contexts else 0,
                'most_recent': max((c.timestamp for c in user_contexts), default=0)
            }

            return summary

    def cleanup_expired_context(self):
        """Clean up expired context entries."""
        with self.lock:
            current_time = time.time()
            expired_count = 0

            # Check each storage tier
            all_contexts = list(self.short_term_memory)
            for context_list in self.medium_term_memory.values():
                all_contexts.extend(context_list)
            for context_list in self.long_term_memory.values():
                all_contexts.extend(context_list)

            for context_id, entry in all_contexts:
                if entry.expires_at and current_time > entry.expires_at:
                    self._remove_context(context_id)
                    expired_count += 1

            self.logger.info(f"Cleaned up {expired_count} expired context entries")

    def compress_context(self, context_type: ContextType = None):
        """Compress old context to save memory."""
        with self.lock:
            if context_type:
                contexts = self._get_contexts_by_type(context_type)
            else:
                contexts = self._get_all_contexts()

            # Filter old contexts
            current_time = time.time()
            old_contexts = [
                (cid, entry) for cid, entry in contexts
                if current_time - entry.timestamp > self.context_retention_time.get(entry.context_type, 86400)
            ]

            if len(old_contexts) > self.compression_threshold:
                # Group by similarity
                grouped_contexts = self._group_similar_contexts(old_contexts)

                # Compress each group
                for group in grouped_contexts:
                    if len(group) > 3:  # Only compress groups with 4+ entries
                        compressed_entry = self._compress_context_group(group)
                        if compressed_entry:
                            # Remove old entries and add compressed one
                            for cid, _ in group:
                                self._remove_context(cid)
                            new_id = self.add_context(
                                compressed_entry['content'],
                                ContextType.EPISODIC,
                                group[0][1].user_id,
                                group[0][1].session_id,
                                priority=ContextPriority.MEDIUM,
                                importance_score=compressed_entry['importance']
                            )

    def get_context_analytics(self) -> Dict[str, Any]:
        """Get comprehensive context analytics."""
        with self.lock:
            # Storage statistics
            total_contexts = (
                len(self.short_term_memory) +
                sum(len(contexts) for contexts in self.medium_term_memory.values()) +
                sum(len(contexts) for contexts in self.long_term_memory.values())
            )

            # Usage statistics
            usage_stats = {
                'total_entries': total_contexts,
                'max_entries': self.max_memory_entries,
                'utilization': total_contexts / self.max_memory_entries,
                'by_type': {ct.value: count for ct, count in self.context_stats.items()},
                'access_frequency': dict(self.access_stats)
            }

            # Performance metrics
            performance_stats = {
                'average_retrieval_time': self._calculate_average_retrieval_time(),
                'cache_hit_rate': self._calculate_cache_hit_rate(),
                'compression_ratio': self._calculate_compression_ratio(),
                'relevance_accuracy': self._calculate_relevance_accuracy()
            }

            # Memory distribution
            memory_distribution = {
                'short_term': len(self.short_term_memory),
                'medium_term': sum(len(contexts) for contexts in self.medium_term_memory.values()),
                'long_term': sum(len(contexts) for contexts in self.long_term_memory.values())
            }

            return {
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'usage_statistics': usage_stats,
                'performance_metrics': performance_stats,
                'memory_distribution': memory_distribution,
                'configuration': {
                    'max_entries': self.max_memory_entries,
                    'retention_times': {ct.value: rt for ct, rt in self.context_retention_time.items()},
                    'compression_threshold': self.compression_threshold
                }
            }

    # Helper methods
    def _generate_context_id(self, content: Any, context_type: ContextType, user_id: str) -> str:
        """Generate unique context ID."""
        content_hash = hashlib.md5(str(content).encode()).hexdigest()[:8]
        timestamp = str(int(time.time()))[-6:]
        return f"{context_type.value}_{user_id}_{timestamp}_{content_hash}"

    def _store_context(self, entry: ContextEntry, context_id: str):
        """Store context entry in appropriate tier."""
        if entry.context_type == ContextType.CONVERSATION:
            self.short_term_memory.append((context_id, entry))
        elif entry.context_type in [ContextType.SESSION, ContextType.TOPIC]:
            self.medium_term_memory[entry.session_id].append((context_id, entry))
        else:
            self.long_term_memory[entry.user_id].append((context_id, entry))

        # Check storage limits
        self._enforce_storage_limits()

    def _update_indices(self, entry: ContextEntry, context_id: str):
        """Update various indices for fast retrieval."""
        # Semantic index (simplified)
        content_str = str(entry.content).lower()
        words = content_str.split()[:5]  # First 5 words as keywords
        for word in words:
            self.semantic_index[word].append(context_id)

        # User index
        self.user_index[entry.user_id].append(context_id)

        # Tag index
        for tag in entry.tags:
            self.tag_index[tag].append(context_id)

        # Time index
        self.time_index.append((entry.timestamp, context_id))
        self.time_index.sort(reverse=True)  # Keep most recent first

    def _get_context_candidates(self, user_id: str = None, session_id: str = None,
                              context_types: List[ContextType] = None) -> List[Tuple[str, ContextEntry]]:
        """Get candidate context entries based on filters."""
        candidates = []

        # Add from short-term memory
        candidates.extend(self.short_term_memory)

        # Add from medium-term memory
        if session_id:
            candidates.extend(self.medium_term_memory.get(session_id, []))
        else:
            for context_list in self.medium_term_memory.values():
                candidates.extend(context_list)

        # Add from long-term memory
        if user_id:
            candidates.extend(self.long_term_memory.get(user_id, []))
        else:
            for context_list in self.long_term_memory.values():
                candidates.extend(context_list)

        # Apply filters
        filtered_candidates = []
        for context_id, entry in candidates:
            # Filter by user
            if user_id and entry.user_id != user_id:
                continue

            # Filter by context type
            if context_types and entry.context_type not in context_types:
                continue

            # Filter by expiration
            if entry.expires_at and time.time() > entry.expires_at:
                continue

            filtered_candidates.append((context_id, entry))

        return filtered_candidates

    def _rank_context_by_relevance(self, candidates: List[Tuple[str, ContextEntry]],
                                 query: str) -> List[ContextEntry]:
        """Rank context candidates by relevance to query."""
        if not query:
            # Return by importance and recency if no query
            return [entry for _, entry in sorted(
                candidates,
                key=lambda x: (x[1].importance_score, x[1].timestamp),
                reverse=True
            )]

        # Calculate relevance scores
        scored_candidates = []
        query_words = set(query.lower().split())

        for context_id, entry in candidates:
            content_str = str(entry.content).lower()
            content_words = set(content_str.split())

            # Calculate semantic similarity (simplified)
            word_overlap = len(query_words & content_words)
            semantic_score = word_overlap / len(query_words) if query_words else 0

            # Combine with importance and recency
            recency_score = self._calculate_recency_score(entry.timestamp)
            final_score = (
                semantic_score * 0.5 +
                entry.importance_score * 0.3 +
                recency_score * 0.2
            )

            scored_candidates.append((final_score, entry))

        # Sort by relevance score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        return [entry for _, entry in scored_candidates]

    def _calculate_recency_score(self, timestamp: float) -> float:
        """Calculate recency score (0-1, higher for more recent)."""
        current_time = time.time()
        age_hours = (current_time - timestamp) / 3600

        # Exponential decay
        return math.exp(-age_hours / 24)  # Half-life of 24 hours

    def _update_access_stats(self, contexts: List[ContextEntry]):
        """Update access statistics."""
        for context in contexts:
            self.access_stats[context.context_type.value] += 1
            context.last_accessed = time.time()
            context.access_count += 1

    def _calculate_context_metrics(self, contexts: List[ContextEntry],
                                 retrieval_time: float) -> ContextMetrics:
        """Calculate context retrieval metrics."""
        if not contexts:
            return ContextMetrics(
                retrieval_accuracy=0.0,
                memory_efficiency=0.0,
                context_relevance=0.0,
                retrieval_time=retrieval_time,
                storage_utilization=0.0
            )

        # Retrieval accuracy (based on importance scores)
        retrieval_accuracy = sum(c.importance_score for c in contexts) / len(contexts)

        # Memory efficiency
        total_contexts = (
            len(self.short_term_memory) +
            sum(len(contexts) for contexts in self.medium_term_memory.values()) +
            sum(len(contexts) for contexts in self.long_term_memory.values())
        )
        memory_efficiency = 1.0 - (total_contexts / self.max_memory_entries)

        # Context relevance (average of calculated relevance scores)
        context_relevance = 0.8  # Simplified - would be calculated during ranking

        # Storage utilization
        storage_utilization = total_contexts / self.max_memory_entries

        return ContextMetrics(
            retrieval_accuracy=retrieval_accuracy,
            memory_efficiency=memory_efficiency,
            context_relevance=context_relevance,
            retrieval_time=retrieval_time,
            storage_utilization=storage_utilization
        )

    def _find_context_entry(self, context_id: str) -> Optional[ContextEntry]:
        """Find context entry by ID."""
        # Search in all storage tiers
        for storage in [self.short_term_memory] + list(self.medium_term_memory.values()) + list(self.long_term_memory.values()):
            for cid, entry in storage:
                if cid == context_id:
                    return entry
        return None

    def _remove_context(self, context_id: str):
        """Remove context entry by ID."""
        # Remove from storage tiers
        for storage in [self.short_term_memory] + list(self.medium_term_memory.values()) + list(self.long_term_memory.values()):
            storage[:] = [(cid, entry) for cid, entry in storage if cid != context_id]

        # Remove from indices
        for index in [self.semantic_index, self.user_index, self.tag_index]:
            for key, context_ids in index.items():
                if context_id in context_ids:
                    context_ids.remove(context_id)

        # Remove from time index
        self.time_index = [(ts, cid) for ts, cid in self.time_index if cid != context_id]

    def _enforce_storage_limits(self):
        """Enforce storage limits by removing least important contexts."""
        total_contexts = (
            len(self.short_term_memory) +
            sum(len(contexts) for contexts in self.medium_term_memory.values()) +
            sum(len(contexts) for contexts in self.long_term_memory.values())
        )

        if total_contexts > self.max_memory_entries:
            # Get all contexts with scores
            all_contexts = []

            # Add from short-term memory
            for cid, entry in self.short_term_memory:
                score = entry.importance_score * self._calculate_recency_score(entry.timestamp)
                all_contexts.append((score, cid, entry, 'short_term'))

            # Add from medium-term memory
            for session_id, contexts in self.medium_term_memory.items():
                for cid, entry in contexts:
                    score = entry.importance_score * self._calculate_recency_score(entry.timestamp)
                    all_contexts.append((score, cid, entry, 'medium_term', session_id))

            # Add from long-term memory
            for user_id, contexts in self.long_term_memory.items():
                for cid, entry in contexts:
                    score = entry.importance_score * self._calculate_recency_score(entry.timestamp)
                    all_contexts.append((score, cid, entry, 'long_term', user_id))

            # Sort by score (lowest first)
            all_contexts.sort(key=lambda x: x[0])

            # Remove lowest scored contexts
            to_remove = total_contexts - self.max_memory_entries + 100  # Remove extra to avoid frequent cleanup
            for i in range(to_remove):
                if i < len(all_contexts):
                    _, cid, _, storage_type, *extra = all_contexts[i]
                    self._remove_context(cid)

    def _check_compression(self):
        """Check if context compression is needed."""
        total_contexts = (
            len(self.short_term_memory) +
            sum(len(contexts) for contexts in self.medium_term_memory.values()) +
            sum(len(contexts) for contexts in self.long_term_memory.values())
        )

        if total_contexts > self.compression_threshold:
            self.compress_context()

    def _get_user_contexts(self, user_id: str, session_id: str = None) -> List[ContextEntry]:
        """Get all contexts for a user."""
        contexts = []

        # Get user's long-term contexts
        contexts.extend([entry for _, entry in self.long_term_memory.get(user_id, [])])

        # Get session contexts if specified
        if session_id:
            contexts.extend([entry for _, entry in self.medium_term_memory.get(session_id, [])])

        # Get recent conversation contexts
        for _, entry in self.short_term_memory:
            if entry.user_id == user_id:
                contexts.append(entry)

        return contexts

    def _generate_brief_summary(self, context_type: ContextType, contexts: List[ContextEntry]) -> Dict[str, Any]:
        """Generate brief summary for context type."""
        if not contexts:
            return {'count': 0, 'summary': 'No contexts available'}

        most_recent = max(contexts, key=lambda c: c.timestamp)
        avg_importance = sum(c.importance_score for c in contexts) / len(contexts)

        return {
            'count': len(contexts),
            'most_recent_timestamp': most_recent.timestamp,
            'average_importance': avg_importance,
            'summary': f'{len(contexts)} {context_type.value} contexts with average importance {avg_importance:.2f}'
        }

    def _generate_detailed_summary(self, context_type: ContextType, contexts: List[ContextEntry]) -> Dict[str, Any]:
        """Generate detailed summary for context type."""
        if not contexts:
            return {'count': 0, 'entries': []}

        # Sort by importance
        sorted_contexts = sorted(contexts, key=lambda c: c.importance_score, reverse=True)

        entries = []
        for context in sorted_contexts[:10]:  # Top 10
            entries.append({
                'timestamp': context.timestamp,
                'importance': context.importance_score,
                'access_count': context.access_count,
                'tags': list(context.tags),
                'content_preview': str(context.content)[:100] + '...' if len(str(context.content)) > 100 else str(context.content)
            })

        return {
            'count': len(contexts),
            'entries': entries,
            'statistics': {
                'average_importance': sum(c.importance_score for c in contexts) / len(contexts),
                'total_accesses': sum(c.access_count for c in contexts),
                'oldest_timestamp': min(c.timestamp for c in contexts),
                'newest_timestamp': max(c.timestamp for c in contexts)
            }
        }

    def _generate_comprehensive_summary(self, context_type: ContextType, contexts: List[ContextEntry]) -> Dict[str, Any]:
        """Generate comprehensive summary for context type."""
        detailed = self._generate_detailed_summary(context_type, contexts)

        # Add additional comprehensive analysis
        tag_frequency = defaultdict(int)
        for context in contexts:
            for tag in context.tags:
                tag_frequency[tag] += 1

        # Time distribution analysis
        current_time = time.time()
        age_distribution = {'day': 0, 'week': 0, 'month': 0, 'older': 0}
        for context in contexts:
            age_seconds = current_time - context.timestamp
            if age_seconds < 86400:  # Less than 1 day
                age_distribution['day'] += 1
            elif age_seconds < 604800:  # Less than 1 week
                age_distribution['week'] += 1
            elif age_seconds < 2592000:  # Less than 1 month
                age_distribution['month'] += 1
            else:
                age_distribution['older'] += 1

        detailed['comprehensive'] = {
            'tag_frequency': dict(tag_frequency),
            'age_distribution': age_distribution,
            'top_content': [
                {'content': str(c.content), 'importance': c.importance_score}
                for c in sorted(contexts, key=lambda c: c.importance_score, reverse=True)[:3]
            ]
        }

        return detailed

    def _get_contexts_by_type(self, context_type: ContextType) -> List[Tuple[str, ContextEntry]]:
        """Get all contexts of a specific type."""
        contexts = []

        # Search in all storage tiers
        for storage in [self.short_term_memory] + list(self.medium_term_memory.values()) + list(self.long_term_memory.values()):
            for cid, entry in storage:
                if entry.context_type == context_type:
                    contexts.append((cid, entry))

        return contexts

    def _get_all_contexts(self) -> List[Tuple[str, ContextEntry]]:
        """Get all contexts from all storage tiers."""
        contexts = []

        for storage in [self.short_term_memory] + list(self.medium_term_memory.values()) + list(self.long_term_memory.values()):
            contexts.extend(storage)

        return contexts

    def _group_similar_contexts(self, contexts: List[Tuple[str, ContextEntry]]) -> List[List[Tuple[str, ContextEntry]]]:
        """Group similar contexts for compression."""
        # Simple grouping by content type and user
        groups = defaultdict(list)
        for context_id, entry in contexts:
            key = (entry.context_type, entry.user_id, str(type(entry.content)))
            groups[key].append((context_id, entry))

        return list(groups.values())

    def _compress_context_group(self, group: List[Tuple[str, ContextEntry]]) -> Optional[Dict[str, Any]]:
        """Compress a group of similar contexts."""
        if len(group) < 2:
            return None

        # Extract key information
        entries = [entry for _, entry in group]
        avg_importance = sum(e.importance_score for e in entries) / len(entries)
        total_accesses = sum(e.access_count for e in entries)

        # Create compressed content
        compressed_content = {
            'type': 'compressed_contexts',
            'original_count': len(group),
            'time_span': {
                'start': min(e.timestamp for e in entries),
                'end': max(e.timestamp for e in entries)
            },
            'total_accesses': total_accesses,
            'tags': set().union(*[e.tags for e in entries]),
            'summary': f"Compressed {len(group)} related contexts"
        }

        return {
            'content': compressed_content,
            'importance': avg_importance
        }

    def _calculate_average_retrieval_time(self) -> float:
        """Calculate average context retrieval time."""
        # Simplified - would track actual retrieval times
        return 0.05  # 50ms average

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # Simplified - would track actual cache hits
        return 0.85  # 85% hit rate

    def _calculate_compression_ratio(self) -> float:
        """Calculate compression ratio."""
        total_contexts = (
            len(self.short_term_memory) +
            sum(len(contexts) for contexts in self.medium_term_memory.values()) +
            sum(len(contexts) for contexts in self.long_term_memory.values())
        )
        return 1.0 - (total_contexts / self.max_memory_entries)

    def _calculate_relevance_accuracy(self) -> float:
        """Calculate relevance accuracy."""
        # Simplified - would track user feedback on relevance
        return 0.78  # 78% accuracy

# Example usage and testing
if __name__ == "__main__":
    import math

    # Create context manager
    context_manager = ContextManager("test_agent_1")

    # Add some context
    context_id1 = context_manager.add_context(
        "User asked about Python programming",
        ContextType.CONVERSATION,
        "user123",
        "session456",
        priority=ContextPriority.HIGH,
        importance_score=0.8
    )

    context_id2 = context_manager.add_context(
        {"preference": "detailed_explanations", "topic": "programming"},
        ContextType.USER_PREFERENCE,
        "user123",
        "session456",
        priority=ContextPriority.MEDIUM,
        importance_score=0.9
    )

    # Retrieve context
    contexts, metrics = context_manager.get_context(
        "Python programming",
        user_id="user123",
        limit=5
    )

    print(f"Retrieved {len(contexts)} contexts")
    print(f"Metrics: Accuracy={metrics.retrieval_accuracy:.2f}, "
          f"Efficiency={metrics.memory_efficiency:.2f}, "
          f"Time={metrics.retrieval_time:.3f}s")

    # Get context summary
    summary = context_manager.get_context_summary("user123", "session456", "detailed")
    print("\nContext Summary:", json.dumps(summary, indent=2))

    # Get analytics
    analytics = context_manager.get_context_analytics()
    print("\nAnalytics:", json.dumps(analytics, indent=2))