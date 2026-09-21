#!/usr/bin/env python3
"""
Messaging Utilities - Common utility functions and classes for the messaging system.

This module provides utility functions including:
- Message serialization and deserialization
- Message validation and verification
- Topic and routing key utilities
- Configuration helpers
- Error handling utilities
- Performance monitoring helpers
- Testing utilities
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import gzip
import snappy
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import yaml
import aiofiles
from pathlib import Path

from .message_broker import Message, MessageType, MessagePriority, MessageEncoding

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    MSGPACK = "msgpack"
    PICKLE = "pickle"
    AVRO = "avro"
    PROTOBUF = "protobuf"


class CompressionType(Enum):
    """Supported compression types."""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class ValidationResult:
    """Message validation result."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageSerializer:
    """
    Utility class for message serialization and deserialization.
    """

    def __init__(self,
                 default_format: SerializationFormat = SerializationFormat.JSON,
                 default_compression: CompressionType = CompressionType.NONE,
                 compression_threshold: int = 1024):
        self.default_format = default_format
        self.default_compression = default_compression
        self.compression_threshold = compression_threshold

    def serialize(self, message: Message,
                  format: Optional[SerializationFormat] = None,
                  compression: Optional[CompressionType] = None) -> bytes:
        """
        Serialize a message to bytes.

        Args:
            message: The message to serialize
            format: Serialization format (uses default if None)
            compression: Compression type (uses default if None)

        Returns:
            Serialized message as bytes
        """
        format = format or self.default_format
        compression = compression or self.default_compression

        try:
            # Convert message to dict
            message_dict = message.to_dict()

            # Serialize based on format
            if format == SerializationFormat.JSON:
                data = json.dumps(message_dict).encode('utf-8')
            elif format == SerializationFormat.MSGPACK:
                import msgpack
                data = msgpack.packb(message_dict)
            elif format == SerializationFormat.PICKLE:
                import pickle
                data = pickle.dumps(message_dict)
            else:
                raise ValueError(f"Unsupported serialization format: {format}")

            # Apply compression if needed
            if compression != CompressionType.NONE and len(data) > self.compression_threshold:
                data = self._compress_data(data, compression)

            return data

        except Exception as e:
            raise ValueError(f"Failed to serialize message: {str(e)}")

    def deserialize(self, data: bytes,
                    format: Optional[SerializationFormat] = None,
                    compression: Optional[CompressionType] = None) -> Message:
        """
        Deserialize bytes to a message.

        Args:
            data: Serialized data
            format: Serialization format (uses default if None)
            compression: Compression type (uses default if None)

        Returns:
            Deserialized message
        """
        format = format or self.default_format
        compression = compression or self.default_compression

        try:
            # Decompress if needed
            if compression != CompressionType.NONE:
                data = self._decompress_data(data, compression)

            # Deserialize based on format
            if format == SerializationFormat.JSON:
                message_dict = json.loads(data.decode('utf-8'))
            elif format == SerializationFormat.MSGPACK:
                import msgpack
                message_dict = msgpack.unpackb(data, raw=False)
            elif format == SerializationFormat.PICKLE:
                import pickle
                message_dict = pickle.loads(data)
            else:
                raise ValueError(f"Unsupported serialization format: {format}")

            # Convert dict to Message
            return Message.from_dict(message_dict)

        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {str(e)}")

    def _compress_data(self, data: bytes, compression: CompressionType) -> bytes:
        """Compress data using specified compression type."""
        if compression == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression == CompressionType.SNAPPY:
            return snappy.compress(data)
        elif compression == CompressionType.LZ4:
            import lz4.frame
            return lz4.frame.compress(data)
        elif compression == CompressionType.ZSTD:
            import zstandard as zstd
            compressor = zstd.ZstdCompressor()
            return compressor.compress(data)
        else:
            return data

    def _decompress_data(self, data: bytes, compression: CompressionType) -> bytes:
        """Decompress data using specified compression type."""
        if compression == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression == CompressionType.SNAPPY:
            return snappy.decompress(data)
        elif compression == CompressionType.LZ4:
            import lz4.frame
            return lz4.frame.decompress(data)
        elif compression == CompressionType.ZSTD:
            import zstandard as zstd
            decompressor = zstd.ZstdDecompressor()
            return decompressor.decompress(data)
        else:
            return data


class MessageValidator:
    """
    Utility class for message validation.
    """

    def __init__(self):
        self.validation_rules: Dict[str, List[Callable]] = {}
        self._register_default_rules()

    def validate(self, message: Message) -> ValidationResult:
        """
        Validate a message against all rules.

        Args:
            message: The message to validate

        Returns:
            ValidationResult with validation results
        """
        result = ValidationResult(is_valid=True)

        try:
            # Basic structural validation
            self._validate_basic_structure(message, result)

            # Type-specific validation
            self._validate_message_type(message, result)

            # Priority validation
            self._validate_priority(message, result)

            # Payload validation
            self._validate_payload(message, result)

            # Headers validation
            self._validate_headers(message, result)

            # Custom validation rules
            self._apply_custom_rules(message, result)

        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")

        return result

    def _validate_basic_structure(self, message: Message, result: ValidationResult):
        """Validate basic message structure."""
        if not message.id:
            result.is_valid = False
            result.errors.append("Message ID is required")

        if not message.type:
            result.is_valid = False
            result.errors.append("Message type is required")

        if not message.topic:
            result.is_valid = False
            result.errors.append("Message topic is required")

        if message.timestamp <= 0:
            result.is_valid = False
            result.errors.append("Valid timestamp is required")

    def _validate_message_type(self, message: Message, result: ValidationResult):
        """Validate message type."""
        try:
            if isinstance(message.type, str):
                MessageType(message.type)
            else:
                # Already an enum
                pass
        except ValueError:
            result.errors.append(f"Invalid message type: {message.type}")

    def _validate_priority(self, message: Message, result: ValidationResult):
        """Validate message priority."""
        try:
            if isinstance(message.priority, str):
                MessagePriority(message.priority)
            else:
                # Already an enum
                pass
        except ValueError:
            result.errors.append(f"Invalid message priority: {message.priority}")

    def _validate_payload(self, message: Message, result: ValidationResult):
        """Validate message payload."""
        if not isinstance(message.payload, dict):
            result.errors.append("Payload must be a dictionary")

        # Size validation
        payload_size = len(str(message.payload))
        if payload_size > 1048576:  # 1MB
            result.warnings.append(f"Large payload size: {payload_size} bytes")

    def _validate_headers(self, message: Message, result: ValidationResult):
        """Validate message headers."""
        if not isinstance(message.headers, dict):
            result.errors.append("Headers must be a dictionary")

        # Check for required headers based on message type
        if message.type == MessageType.AGENT_COMMUNICATION:
            required_headers = ["sender_id"]
            for header in required_headers:
                if header not in message.headers:
                    result.errors.append(f"Required header missing for {message.type.value}: {header}")

    def _apply_custom_rules(self, message: Message, result: ValidationResult):
        """Apply custom validation rules."""
        message_type_key = message.type.value if isinstance(message.type, MessageType) else message.type

        if message_type_key in self.validation_rules:
            for rule in self.validation_rules[message_type_key]:
                try:
                    rule_result = rule(message)
                    if isinstance(rule_result, ValidationResult):
                        if not rule_result.is_valid:
                            result.is_valid = False
                        result.errors.extend(rule_result.errors)
                        result.warnings.extend(rule_result.warnings)
                    elif not rule_result:
                        result.is_valid = False
                        result.errors.append(f"Custom validation failed for rule {rule.__name__}")
                except Exception as e:
                    result.warnings.append(f"Custom validation rule error: {str(e)}")

    def add_validation_rule(self, message_type: str, rule: Callable):
        """Add a custom validation rule for a message type."""
        if message_type not in self.validation_rules:
            self.validation_rules[message_type] = []
        self.validation_rules[message_type].append(rule)

    def _register_default_rules(self):
        """Register default validation rules."""
        # Agent communication validation
        def validate_agent_communication(message: Message) -> ValidationResult:
            result = ValidationResult(is_valid=True)
            if message.type == MessageType.AGENT_COMMUNICATION:
                sender_id = message.headers.get("sender_id")
                if not sender_id:
                    result.is_valid = False
                    result.errors.append("sender_id header is required for agent communication")
                elif not isinstance(sender_id, str) or len(sender_id.strip()) == 0:
                    result.is_valid = False
                    result.errors.append("sender_id must be a non-empty string")
            return result

        self.add_validation_rule("agent_communication", validate_agent_communication)

        # Game state validation
        def validate_game_state(message: Message) -> ValidationResult:
            result = ValidationResult(is_valid=True)
            if message.type == MessageType.GAME_STATE_UPDATE:
                if "game_id" not in message.payload:
                    result.is_valid = False
                    result.errors.append("game_id is required in payload for game state updates")
                if "session_id" not in message.payload:
                    result.warnings.append("session_id missing from game state update")
            return result

        self.add_validation_rule("game_state_update", validate_game_state)


class TopicManager:
    """
    Utility class for topic management and routing.
    """

    def __init__(self):
        self.topic_patterns: Dict[str, str] = {}
        self.routing_rules: Dict[str, List[str]] = {}
        self._register_default_patterns()

    def generate_topic(self, base_topic: str, **kwargs) -> str:
        """
        Generate a topic name based on a base topic and parameters.

        Args:
            base_topic: The base topic name
            **kwargs: Additional parameters for topic generation

        Returns:
            Generated topic name
        """
        if not kwargs:
            return base_topic

        parts = [base_topic]
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f"{key}={value}")

        return ".".join(parts)

    def parse_topic(self, topic: str) -> Dict[str, str]:
        """
        Parse a topic name into its components.

        Args:
            topic: The topic name to parse

        Returns:
            Dictionary of topic components
        """
        parts = topic.split(".")
        result = {"base": parts[0]}

        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                result[key] = value
            else:
                result.setdefault("extra_parts", []).append(part)

        return result

    def match_pattern(self, topic: str, pattern: str) -> bool:
        """
        Check if a topic matches a pattern.

        Args:
            topic: The topic to check
            pattern: The pattern (supports * and # wildcards)

        Returns:
            True if topic matches pattern
        """
        # Simple pattern matching
        if pattern == "#":
            return True

        topic_parts = topic.split(".")
        pattern_parts = pattern.split(".")

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == "#":
                return True
            elif pattern_part == "*":
                if i >= len(topic_parts):
                    return False
                continue
            elif i >= len(topic_parts):
                return False
            elif topic_parts[i] != pattern_part:
                return False

        return len(topic_parts) == len(pattern_parts)

    def get_routing_destinations(self, topic: str) -> List[str]:
        """
        Get routing destinations for a topic based on routing rules.

        Args:
            topic: The topic to route

        Returns:
            List of destination topics
        """
        destinations = []

        for pattern, dest_topics in self.routing_rules.items():
            if self.match_pattern(topic, pattern):
                for dest_topic in dest_topics:
                    # Substitute variables in destination topic
                    topic_vars = self.parse_topic(topic)
                    resolved_topic = self._resolve_topic_template(dest_topic, topic_vars)
                    destinations.append(resolved_topic)

        return destinations

    def _resolve_topic_template(self, template: str, variables: Dict[str, str]) -> str:
        """Resolve topic template with variables."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"${{{key}}}", value)
        return result

    def add_routing_rule(self, pattern: str, destinations: List[str]):
        """Add a routing rule."""
        self.routing_rules[pattern] = destinations

    def _register_default_patterns(self):
        """Register default topic patterns."""
        # Agent communication patterns
        self.topic_patterns["agent_direct"] = "agent.direct.{agent_id}"
        self.topic_patterns["agent_group"] = "agent.group.{group_id}"
        self.topic_patterns["agent_broadcast"] = "agent.broadcast"

        # Game event patterns
        self.topic_patterns["game_events"] = "game.events.{game_id}"
        self.topic_patterns["game_state"] = "game.state.{game_id}"

        # System event patterns
        self.topic_patterns["system_alerts"] = "system.alerts.{severity}"
        self.topic_patterns["system_metrics"] = "system.metrics.{category}"
        self.topic_patterns["system_health"] = "system.health.{component}"

        # Default routing rules
        self.add_routing_rule("agent.direct.*", ["agent.direct.${agent_id}"])
        self.add_routing_rule("agent.group.*", ["agent.group.${group_id}"])
        self.add_routing_rule("system.alerts.*", ["system.alerts", "system.monitoring"])
        self.add_routing_rule("game.events.*", ["game.events.${game_id}", "game.monitoring"])


class ConfigurationLoader:
    """
    Utility class for loading and managing configuration.
    """

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        self.configs: Dict[str, Any] = {}
        self.watchers: Dict[str, asyncio.Task] = {}

    async def load_config(self, config_name: str, backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_name: Name of the configuration file (without extension)
            backend: Backend name (optional, for backend-specific configs)

        Returns:
            Loaded configuration dictionary
        """
        if backend:
            config_file = self.config_dir / f"{backend}.yaml"
            config_key = f"{backend}_{config_name}"
        else:
            config_file = self.config_dir / f"{config_name}.yaml"
            config_key = config_name

        try:
            async with aiofiles.open(config_file, 'r') as f:
                content = await f.read()
                config = yaml.safe_load(content)
                self.configs[config_key] = config
                return config

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file {config_file}: {str(e)}")
            raise

    def get_config(self, config_name: str, backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Get loaded configuration.

        Args:
            config_name: Name of the configuration
            backend: Backend name (optional)

        Returns:
            Configuration dictionary
        """
        config_key = f"{backend}_{config_name}" if backend else config_name
        return self.configs.get(config_key, {})

    async def reload_config(self, config_name: str, backend: Optional[str] = None) -> Dict[str, Any]:
        """Reload configuration from file."""
        return await self.load_config(config_name, backend)

    async def watch_config(self, config_name: str, callback: Callable, backend: Optional[str] = None):
        """
        Watch for configuration changes.

        Args:
            config_name: Name of the configuration to watch
            callback: Callback function to call on changes
            backend: Backend name (optional)
        """
        # This is a simplified implementation
        # In production, you'd use file system watchers
        config_key = f"{backend}_{config_name}" if backend else config_name

        async def watch_loop():
            last_modified = 0
            config_file = self.config_dir / f"{config_name}.yaml"

            while True:
                try:
                    current_modified = config_file.stat().st_mtime
                    if current_modified > last_modified:
                        new_config = await self.reload_config(config_name, backend)
                        await callback(new_config)
                        last_modified = current_modified
                except Exception as e:
                    logger.error(f"Error watching config {config_name}: {str(e)}")

                await asyncio.sleep(5)  # Check every 5 seconds

        task = asyncio.create_task(watch_loop())
        self.watchers[config_key] = task

    async def stop_watching(self, config_name: str, backend: Optional[str] = None):
        """Stop watching a configuration."""
        config_key = f"{backend}_{config_name}" if backend else config_name
        if config_key in self.watchers:
            self.watchers[config_key].cancel()
            del self.watchers[config_key]


class PerformanceMonitor:
    """
    Utility class for performance monitoring.
    """

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self.start_times: Dict[str, float] = {}

    def start_timer(self, name: str) -> str:
        """
        Start a performance timer.

        Args:
            name: Name of the timer

        Returns:
            Timer ID
        """
        timer_id = f"{name}_{time.time()}_{uuid.uuid4().hex[:8]}"
        self.start_times[timer_id] = time.time()
        return timer_id

    def end_timer(self, timer_id: str) -> float:
        """
        End a performance timer and record the duration.

        Args:
            timer_id: Timer ID returned by start_timer

        Returns:
            Duration in seconds
        """
        if timer_id not in self.start_times:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0

        duration = time.time() - self.start_times[timer_id]
        name = timer_id.rsplit('_', 2)[0]

        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration)

        del self.start_times[timer_id]
        return duration

    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter."""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

    def get_metrics_summary(self, name: str) -> Dict[str, float]:
        """
        Get summary statistics for a metric.

        Args:
            name: Name of the metric

        Returns:
            Dictionary with summary statistics
        """
        if name not in self.metrics or not self.metrics[name]:
            return {}

        values = self.metrics[name]
        return {
            "count": len(values),
            "total": sum(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "last": values[-1]
        }

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, 0)

    def reset_metrics(self, name: Optional[str] = None):
        """Reset metrics."""
        if name:
            if name in self.metrics:
                self.metrics[name].clear()
            if name in self.counters:
                self.counters[name] = 0
        else:
            self.metrics.clear()
            self.counters.clear()

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics and counters."""
        result = {}

        for name in self.metrics:
            result[name] = self.get_metrics_summary(name)

        for name, value in self.counters.items():
            result[name] = {"counter": value}

        return result


class MessageHasher:
    """
    Utility class for message hashing and deduplication.
    """

    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm

    def hash_message(self, message: Message) -> str:
        """
        Generate a hash for a message.

        Args:
            message: The message to hash

        Returns:
            Hexadecimal hash string
        """
        # Create hash content from message fields
        hash_content = {
            "type": message.type.value if hasattr(message.type, 'value') else message.type,
            "topic": message.topic,
            "payload": message.payload,
            "headers": sorted(message.headers.items())
        }

        # Convert to JSON string
        content_str = json.dumps(hash_content, sort_keys=True)

        # Generate hash
        if self.algorithm == "md5":
            return hashlib.md5(content_str.encode()).hexdigest()
        elif self.algorithm == "sha1":
            return hashlib.sha1(content_str.encode()).hexdigest()
        elif self.algorithm == "sha256":
            return hashlib.sha256(content_str.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.algorithm}")

    def create_message_id(self, message: Message) -> str:
        """
        Create a deterministic message ID based on content.

        Args:
            message: The message

        Returns:
            Message ID string
        """
        return self.hash_message(message)[:16]  # Use first 16 characters

    def is_duplicate(self, message: Message, seen_hashes: set) -> bool:
        """
        Check if message is a duplicate based on hash.

        Args:
            message: The message to check
            seen_hashes: Set of previously seen hashes

        Returns:
            True if message is a duplicate
        """
        message_hash = self.hash_message(message)
        return message_hash in seen_hashes


# Context manager for performance monitoring
class TimedOperation:
    """Context manager for timing operations."""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.timer_id = None

    def __enter__(self):
        self.timer_id = self.monitor.start_timer(self.operation_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            duration = self.monitor.end_timer(self.timer_id)
            logger.debug(f"Operation {self.operation_name} took {duration:.3f} seconds")


# Global instances
default_serializer = MessageSerializer()
default_validator = MessageValidator()
default_topic_manager = TopicManager()
default_performance_monitor = PerformanceMonitor()
default_config_loader = ConfigurationLoader()
default_message_hasher = MessageHasher()


# Export main classes and instances
__all__ = [
    'SerializationFormat',
    'CompressionType',
    'ValidationResult',
    'MessageSerializer',
    'MessageValidator',
    'TopicManager',
    'ConfigurationLoader',
    'PerformanceMonitor',
    'MessageHasher',
    'TimedOperation',
    'default_serializer',
    'default_validator',
    'default_topic_manager',
    'default_performance_monitor',
    'default_config_loader',
    'default_message_hasher'
]