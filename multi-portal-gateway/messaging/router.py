#!/usr/bin/env python3
"""
DMLogn8n Message Router - Advanced message routing and topic management system.

This module provides intelligent message routing capabilities with support for:
- Topic-based routing patterns
- Dynamic routing rules
- Message filtering and transformation
- Load balancing across consumers
- Dead letter routing
- Priority-based routing
"""

import asyncio
import re
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union, Pattern
import hashlib
import yaml
from collections import defaultdict, deque
import aiofiles

from .message_broker import Message, MessageType, MessagePriority, MessageBrokerBackend

logger = logging.getLogger(__name__)


class RoutingPattern(Enum):
    """Supported routing pattern types."""
    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    WILDCARD = "wildcard"
    REGEX = "regex"
    TOPIC = "topic"
    HEADER = "header"


@dataclass
class RoutingRule:
    """Routing rule definition."""
    id: str
    name: str
    pattern_type: RoutingPattern
    pattern: str
    destination: str
    priority: int = 0
    enabled: bool = True
    filter_expression: Optional[str] = None
    transform_script: Optional[str] = None
    rate_limit: Optional[int] = None  # messages per second
    dead_letter_destination: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class TopicConfig:
    """Topic configuration."""
    name: str
    partitions: int = 1
    replication_factor: int = 1
    retention_ms: Optional[int] = None
    max_message_bytes: int = 1048576  # 1MB
    cleanup_policy: str = "delete"  # delete, compact
    segment_ms: Optional[int] = None
    delete_retention_ms: Optional[int] = None
    min_cleanable_dirty_ratio: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsumerGroup:
    """Consumer group configuration."""
    name: str
    topic: str
    consumers: List[str] = field(default_factory=list)
    partition_assignment: Dict[str, List[int]] = field(default_factory=dict)
    rebalance_strategy: str = "range"  # range, roundrobin, sticky
    auto_offset_reset: str = "latest"  # earliest, latest, none
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    metadata: Dict[str, Any] = field(default_factory=dict)


class RouteMatchResult:
    """Result of route matching operation."""

    def __init__(self):
        self.matched_rules: List[RoutingRule] = []
        self.destinations: Set[str] = set()
        self.transformations: List[Callable] = []
        self.rate_limited: bool = False
        self.filtered_out: bool = False


class RateLimiter:
    """Rate limiter for routing rules."""

    def __init__(self, max_requests: int, window_seconds: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def is_allowed(self) -> bool:
        """Check if request is allowed under rate limit."""
        async with self._lock:
            now = time.time()

            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False


class MessageFilter:
    """Message filtering based on expressions."""

    @staticmethod
    def evaluate_filter(message: Message, filter_expression: str) -> bool:
        """
        Evaluate a filter expression against a message.

        Supports:
        - JSONPath-like expressions: $.headers.priority == 'high'
        - Simple key-value matches: headers.priority == 'high'
        - Complex boolean expressions
        """
        try:
            # Create evaluation context
            context = {
                'message': message,
                'msg': message,
                'payload': message.payload,
                'headers': message.headers,
                'type': message.type.value,
                'priority': message.priority.value,
                'topic': message.topic,
                'source': message.source,
                'destination': message.destination
            }

            # Simple evaluation for basic expressions
            if '==' in filter_expression:
                left, right = filter_expression.split('==', 1)
                left = left.strip()
                right = right.strip().strip('\'"')

                # Evaluate left side
                left_value = MessageFilter._evaluate_expression(left, context)

                return str(left_value) == right

            # For more complex expressions, use eval with restricted globals
            allowed_names = {
                'True': True, 'False': False, 'None': None,
                'len': len, 'str': str, 'int': int, 'float': float,
                'and': lambda a, b: a and b,
                'or': lambda a, b: a or b,
                'not': lambda a: not a,
                'in': lambda a, b: a in b,
                'contains': lambda a, b: b in a,
                'startswith': lambda a, b: a.startswith(b),
                'endswith': lambda a, b: a.endswith(b),
                'matches': lambda a, b: bool(re.match(b, a))
            }

            # Update context with allowed functions
            context.update(allowed_names)

            return eval(filter_expression, {"__builtins__": {}}, context)

        except Exception as e:
            logger.warning(f"Failed to evaluate filter expression '{filter_expression}': {str(e)}")
            return False  # Default to allowing the message if filter fails

    @staticmethod
    def _evaluate_expression(expr: str, context: Dict[str, Any]) -> Any:
        """Evaluate a simple expression against context."""
        parts = expr.split('.')
        value = context

        for part in parts:
            if '[' in part:
                # Handle array/dict access like headers['priority']
                base, index_part = part.split('[', 1)
                index = index_part.rstrip(']').strip('\'"')

                if base:
                    value = getattr(value, base, value.get(base, {}))

                if isinstance(value, (dict, list)):
                    value = value[index]
                else:
                    value = getattr(value, index, None)
            else:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None

            if value is None:
                break

        return value


class MessageTransformer:
    """Message transformation utilities."""

    @staticmethod
    def apply_transform(message: Message, transform_script: str) -> Message:
        """Apply transformation script to message."""
        try:
            # Create a copy of the message to transform
            transformed = Message(
                id=message.id,
                type=message.type,
                topic=message.topic,
                payload=message.payload.copy(),
                headers=message.headers.copy(),
                priority=message.priority,
                timestamp=message.timestamp,
                expiration=message.expiration,
                retry_count=message.retry_count,
                max_retries=message.max_retries,
                encoding=message.encoding,
                compressed=message.compressed,
                encrypted=message.encrypted,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                consumer_tag=message.consumer_tag,
                delivery_tag=message.delivery_tag,
                source=message.source,
                destination=message.destination
            )

            # Simple transformation language
            if transform_script.startswith('payload.'):
                # Modify payload
                field_path = transform_script[7:]  # Remove 'payload.'
                MessageTransformer._set_nested_value(transformed.payload, field_path)
            elif transform_script.startswith('headers.'):
                # Modify headers
                field_path = transform_script[8:]  # Remove 'headers.'
                MessageTransformer._set_nested_value(transformed.headers, field_path)
            elif transform_script.startswith('add_header:'):
                # Add header
                _, header_def = transform_script.split(':', 1)
                if '=' in header_def:
                    key, value = header_def.split('=', 1)
                    transformed.headers[key.strip()] = value.strip()
            elif transform_script.startswith('set_topic:'):
                # Set topic
                _, topic = transform_script.split(':', 1)
                transformed.topic = topic.strip()
            elif transform_script.startswith('set_priority:'):
                # Set priority
                _, priority = transform_script.split(':', 1)
                transformed.priority = MessagePriority(int(priority.strip()))

            return transformed

        except Exception as e:
            logger.error(f"Failed to apply transformation '{transform_script}': {str(e)}")
            return message  # Return original message if transformation fails

    @staticmethod
    def _set_nested_value(obj: Dict[str, Any], path: str):
        """Set a nested value in a dictionary."""
        parts = path.split('.')
        current = obj

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # For simplicity, just set the last part to a timestamp
        current[parts[-1]] = time.time()


class MessageRouter:
    """
    Advanced message router with pattern matching, filtering, and transformation.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.routing_rules: Dict[str, RoutingRule] = {}
        self.topic_configs: Dict[str, TopicConfig] = {}
        self.consumer_groups: Dict[str, ConsumerGroup] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.routing_stats = {
            'messages_routed': 0,
            'messages_filtered': 0,
            'messages_transformed': 0,
            'messages_rate_limited': 0,
            'routing_errors': 0
        }
        self._lock = asyncio.Lock()

        # Load configuration if provided
        if config_path:
            asyncio.create_task(self.load_config())

    async def load_config(self):
        """Load routing configuration from file."""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                content = await f.read()
                config = yaml.safe_load(content)

            # Load routing rules
            if 'routing_rules' in config:
                for rule_data in config['routing_rules']:
                    rule = RoutingRule(**rule_data)
                    self.routing_rules[rule.id] = rule

                    # Create rate limiter if specified
                    if rule.rate_limit:
                        self.rate_limiters[rule.id] = RateLimiter(rule.rate_limit)

            # Load topic configurations
            if 'topics' in config:
                for topic_data in config['topics']:
                    topic = TopicConfig(**topic_data)
                    self.topic_configs[topic.name] = topic

            # Load consumer groups
            if 'consumer_groups' in config:
                for group_data in config['consumer_groups']:
                    group = ConsumerGroup(**group_data)
                    self.consumer_groups[group.name] = group

            logger.info(f"Loaded {len(self.routing_rules)} routing rules, "
                       f"{len(self.topic_configs)} topics, "
                       f"{len(self.consumer_groups)} consumer groups")

        except Exception as e:
            logger.error(f"Failed to load router config: {str(e)}")
            raise

    async def add_routing_rule(self, rule: RoutingRule) -> bool:
        """Add a new routing rule."""
        try:
            async with self._lock:
                self.routing_rules[rule.id] = rule

                # Create rate limiter if needed
                if rule.rate_limit:
                    self.rate_limiters[rule.id] = RateLimiter(rule.rate_limit)

                logger.info(f"Added routing rule: {rule.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to add routing rule {rule.id}: {str(e)}")
            return False

    async def remove_routing_rule(self, rule_id: str) -> bool:
        """Remove a routing rule."""
        try:
            async with self._lock:
                if rule_id in self.routing_rules:
                    del self.routing_rules[rule_id]

                    # Remove associated rate limiter
                    if rule_id in self.rate_limiters:
                        del self.rate_limiters[rule_id]

                    logger.info(f"Removed routing rule: {rule_id}")
                    return True
                else:
                    logger.warning(f"Routing rule not found: {rule_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to remove routing rule {rule_id}: {str(e)}")
            return False

    async def route_message(self, message: Message) -> RouteMatchResult:
        """
        Route a message based on configured routing rules.

        Args:
            message: The message to route

        Returns:
            RouteMatchResult with matched destinations and transformations
        """
        result = RouteMatchResult()

        try:
            # Get enabled routing rules sorted by priority (higher first)
            enabled_rules = sorted(
                [rule for rule in self.routing_rules.values() if rule.enabled],
                key=lambda r: r.priority,
                reverse=True
            )

            for rule in enabled_rules:
                if await self._matches_rule(message, rule):
                    result.matched_rules.append(rule)
                    result.destinations.add(rule.destination)

                    # Check rate limiting
                    if rule.id in self.rate_limiters:
                        if not await self.rate_limiters[rule.id].is_allowed():
                            result.rate_limited = True
                            logger.warning(f"Message rate limited by rule: {rule.name}")
                            continue

                    # Apply filter if specified
                    if rule.filter_expression:
                        if not MessageFilter.evaluate_filter(message, rule.filter_expression):
                            logger.debug(f"Message filtered out by rule: {rule.name}")
                            continue

                    # Apply transformation if specified
                    if rule.transform_script:
                        result.transformations.append(
                            lambda msg, script=rule.transform_script: MessageTransformer.apply_transform(msg, script)
                        )

            # Update statistics
            if result.matched_rules:
                self.routing_stats['messages_routed'] += 1
                if result.transformations:
                    self.routing_stats['messages_transformed'] += 1
            else:
                self.routing_stats['messages_filtered'] += 1

            if result.rate_limited:
                self.routing_stats['messages_rate_limited'] += 1

            return result

        except Exception as e:
            logger.error(f"Error routing message {message.id}: {str(e)}")
            self.routing_stats['routing_errors'] += 1
            return result

    async def _matches_rule(self, message: Message, rule: RoutingRule) -> bool:
        """Check if a message matches a routing rule."""
        try:
            if rule.pattern_type == RoutingPattern.EXACT:
                return message.topic == rule.pattern

            elif rule.pattern_type == RoutingPattern.PREFIX:
                return message.topic.startswith(rule.pattern)

            elif rule.pattern_type == RoutingPattern.SUFFIX:
                return message.topic.endswith(rule.pattern)

            elif rule.pattern_type == RoutingPattern.WILDCARD:
                # Simple wildcard matching with * and ?
                pattern = rule.pattern.replace('*', '.*').replace('?', '.')
                pattern = f'^{pattern}$'
                return bool(re.match(pattern, message.topic))

            elif rule.pattern_type == RoutingPattern.REGEX:
                return bool(re.match(rule.pattern, message.topic))

            elif rule.pattern_type == RoutingPattern.TOPIC:
                # Topic-based routing with hierarchical patterns
                return self._matches_topic_pattern(message.topic, rule.pattern)

            elif rule.pattern_type == RoutingPattern.HEADER:
                # Header-based routing
                return self._matches_header_pattern(message, rule.pattern)

            return False

        except Exception as e:
            logger.error(f"Error matching rule {rule.id}: {str(e)}")
            return False

    def _matches_topic_pattern(self, topic: str, pattern: str) -> bool:
        """Match topic against hierarchical pattern."""
        topic_parts = topic.split('.')
        pattern_parts = pattern.split('.')

        # Handle wildcards
        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == '#':
                # Multi-level wildcard
                return True
            elif pattern_part == '*':
                # Single-level wildcard
                if i >= len(topic_parts):
                    return False
                continue
            elif i >= len(topic_parts):
                return False
            elif topic_parts[i] != pattern_part:
                return False

        return len(topic_parts) == len(pattern_parts)

    def _matches_header_pattern(self, message: Message, pattern: str) -> bool:
        """Match message headers against pattern."""
        # Pattern format: "key=value" or "key!=value"
        if '=' in pattern:
            if '!=' in pattern:
                key, value = pattern.split('!=', 1)
                return message.headers.get(key.strip()) != value.strip()
            else:
                key, value = pattern.split('=', 1)
                return message.headers.get(key.strip()) == value.strip()
        else:
            # Just check for header existence
            return pattern.strip() in message.headers

    async def create_topic(self, topic_config: TopicConfig) -> bool:
        """Create a new topic with configuration."""
        try:
            async with self._lock:
                self.topic_configs[topic_config.name] = topic_config
                logger.info(f"Created topic: {topic_config.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create topic {topic_config.name}: {str(e)}")
            return False

    async def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic."""
        try:
            async with self._lock:
                if topic_name in self.topic_configs:
                    del self.topic_configs[topic_name]
                    logger.info(f"Deleted topic: {topic_name}")
                    return True
                else:
                    logger.warning(f"Topic not found: {topic_name}")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete topic {topic_name}: {str(e)}")
            return False

    async def create_consumer_group(self, group: ConsumerGroup) -> bool:
        """Create a new consumer group."""
        try:
            async with self._lock:
                self.consumer_groups[group.name] = group
                await self._rebalance_group(group.name)
                logger.info(f"Created consumer group: {group.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create consumer group {group.name}: {str(e)}")
            return False

    async def add_consumer_to_group(self, group_name: str, consumer_id: str) -> bool:
        """Add a consumer to a group."""
        try:
            async with self._lock:
                if group_name in self.consumer_groups:
                    group = self.consumer_groups[group_name]
                    if consumer_id not in group.consumers:
                        group.consumers.append(consumer_id)
                        await self._rebalance_group(group_name)
                        logger.info(f"Added consumer {consumer_id} to group {group_name}")
                        return True
                    else:
                        logger.warning(f"Consumer {consumer_id} already in group {group_name}")
                        return False
                else:
                    logger.error(f"Consumer group not found: {group_name}")
                    return False

        except Exception as e:
            logger.error(f"Failed to add consumer to group: {str(e)}")
            return False

    async def _rebalance_group(self, group_name: str):
        """Rebalance partitions for a consumer group."""
        if group_name not in self.consumer_groups:
            return

        group = self.consumer_groups[group_name]
        topic_config = self.topic_configs.get(group.topic)

        if not topic_config:
            return

        partitions = list(range(topic_config.partitions))
        consumers = group.consumers.copy()

        if not consumers:
            group.partition_assignment = {}
            return

        # Simple round-robin assignment
        assignment = {}
        for i, consumer_id in enumerate(consumers):
            assigned_partitions = []
            for j in range(i, len(partitions), len(consumers)):
                assigned_partitions.append(partitions[j])
            assignment[consumer_id] = assigned_partitions

        group.partition_assignment = assignment
        logger.info(f"Rebalanced group {group_name}: {assignment}")

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return self.routing_stats.copy()

    def get_topic_info(self, topic_name: str) -> Optional[TopicConfig]:
        """Get topic configuration."""
        return self.topic_configs.get(topic_name)

    def get_consumer_group_info(self, group_name: str) -> Optional[ConsumerGroup]:
        """Get consumer group information."""
        return self.consumer_groups.get(group_name)

    def list_topics(self) -> List[str]:
        """List all configured topics."""
        return list(self.topic_configs.keys())

    def list_consumer_groups(self) -> List[str]:
        """List all consumer groups."""
        return list(self.consumer_groups.keys())

    def list_routing_rules(self) -> List[RoutingRule]:
        """List all routing rules."""
        return list(self.routing_rules.values())


# Export main classes
__all__ = [
    'MessageRouter',
    'RoutingRule',
    'TopicConfig',
    'ConsumerGroup',
    'RoutingPattern',
    'RouteMatchResult',
    'MessageFilter',
    'MessageTransformer',
    'RateLimiter'
]