#!/usr/bin/env python3
"""
DMLogn8n Message Broker - Main abstraction layer for multi-backend messaging system.

This module provides a unified interface for message queue operations across
different backends (RabbitMQ, Redis Streams, Apache Kafka) with support for
message routing, persistence, error handling, and real-time streaming.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from pathlib import Path
import yaml
import aiofiles
from cryptography.fernet import Fernet
import snappy
from circuit_breaker import CircuitBreaker, CircuitBreakerError

# Type hints
T = TypeVar('T')
MessageHandler = Callable[['Message'], Any]
AsyncMessageHandler = Callable[['Message'], Any]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for different system components."""
    AGENT_COMMUNICATION = "agent_communication"
    GAME_STATE_UPDATE = "game_state_update"
    DIALOGUE_MESSAGE = "dialogue_message"
    COMBAT_EVENT = "combat_event"
    WORLD_SIMULATION = "world_simulation"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    AI_MODEL_REQUEST = "ai_model_request"
    AI_MODEL_RESPONSE = "ai_model_response"
    HEARTBEAT = "heartbeat"
    DEAD_LETTER = "dead_letter"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageEncoding(Enum):
    """Supported message encoding formats."""
    JSON = "json"
    AVRO = "avro"
    PROTOBUF = "protobuf"


@dataclass
class Message:
    """Message data structure with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AGENT_COMMUNICATION
    topic: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    expiration: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    encoding: MessageEncoding = MessageEncoding.JSON
    compressed: bool = False
    encrypted: bool = False
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    consumer_tag: Optional[str] = None
    delivery_tag: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            'id': self.id,
            'type': self.type.value,
            'topic': self.topic,
            'payload': self.payload,
            'headers': self.headers,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'expiration': self.expiration,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'encoding': self.encoding.value,
            'compressed': self.compressed,
            'encrypted': self.encrypted,
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'consumer_tag': self.consumer_tag,
            'delivery_tag': self.delivery_tag,
            'source': self.source,
            'destination': self.destination
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        msg = cls()
        msg.id = data.get('id', str(uuid.uuid4()))
        msg.type = MessageType(data.get('type', MessageType.AGENT_COMMUNICATION.value))
        msg.topic = data.get('topic', '')
        msg.payload = data.get('payload', {})
        msg.headers = data.get('headers', {})
        msg.priority = MessagePriority(data.get('priority', MessagePriority.NORMAL.value))
        msg.timestamp = data.get('timestamp', time.time())
        msg.expiration = data.get('expiration')
        msg.retry_count = data.get('retry_count', 0)
        msg.max_retries = data.get('max_retries', 3)
        msg.encoding = MessageEncoding(data.get('encoding', MessageEncoding.JSON.value))
        msg.compressed = data.get('compressed', False)
        msg.encrypted = data.get('encrypted', False)
        msg.correlation_id = data.get('correlation_id')
        msg.reply_to = data.get('reply_to')
        msg.consumer_tag = data.get('consumer_tag')
        msg.delivery_tag = data.get('delivery_tag')
        msg.source = data.get('source')
        msg.destination = data.get('destination')
        return msg


@dataclass
class QueueConfig:
    """Queue configuration parameters."""
    name: str
    durable: bool = True
    auto_delete: bool = False
    exclusive: bool = False
    max_length: Optional[int] = None
    message_ttl: Optional[int] = None
    dead_letter_exchange: Optional[str] = None
    dead_letter_routing_key: Optional[str] = None
    priority: bool = False
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExchangeConfig:
    """Exchange configuration parameters."""
    name: str
    type: str = "topic"  # direct, topic, fanout, headers
    durable: bool = True
    auto_delete: bool = False
    internal: bool = False
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsumerConfig:
    """Consumer configuration parameters."""
    queue: str
    prefetch_count: int = 10
    auto_ack: bool = False
    exclusive: bool = False
    consumer_tag: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)


class MessageBrokerError(Exception):
    """Base exception for message broker errors."""
    pass


class ConnectionError(MessageBrokerError):
    """Connection-related errors."""
    pass


class PublishError(MessageBrokerError):
    """Message publishing errors."""
    pass


class ConsumeError(MessageBrokerError):
    """Message consumption errors."""
    pass


class SerializationError(MessageBrokerError):
    """Message serialization/deserialization errors."""
    pass


class MessageBrokerBackend(ABC):
    """Abstract base class for message broker backends."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.is_connected = False
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=ConnectionError
        )

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass

    @abstractmethod
    async def publish(self, message: Message, routing_key: str = "") -> bool:
        """Publish a message to the broker."""
        pass

    @abstractmethod
    async def consume(self, queue_config: ConsumerConfig, handler: AsyncMessageHandler) -> None:
        """Start consuming messages from a queue."""
        pass

    @abstractmethod
    async def declare_queue(self, queue_config: QueueConfig) -> bool:
        """Declare a queue."""
        pass

    @abstractmethod
    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool:
        """Declare an exchange."""
        pass

    @abstractmethod
    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind a queue to an exchange with a routing key."""
        pass

    @abstractmethod
    async def ack_message(self, delivery_tag: str) -> None:
        """Acknowledge a message."""
        pass

    @abstractmethod
    async def nack_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """Negative acknowledgment of a message."""
        pass

    @abstractmethod
    async def get_queue_info(self, queue: str) -> Dict[str, Any]:
        """Get information about a queue."""
        pass


class MessageSerializer:
    """Handles message serialization and deserialization."""

    def __init__(self, encryption_key: Optional[bytes] = None):
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def serialize(self, message: Message) -> bytes:
        """Serialize a message to bytes."""
        try:
            # Convert message to JSON
            data = message.to_dict()
            json_data = json.dumps(data).encode('utf-8')

            # Compress if enabled
            if message.compressed:
                json_data = snappy.compress(json_data)

            # Encrypt if enabled
            if message.encrypted and self.cipher:
                json_data = self.cipher.encrypt(json_data)

            return json_data

        except Exception as e:
            raise SerializationError(f"Failed to serialize message {message.id}: {str(e)}")

    def deserialize(self, data: bytes, message: Message) -> Message:
        """Deserialize bytes to a message."""
        try:
            # Decrypt if enabled
            if message.encrypted and self.cipher:
                data = self.cipher.decrypt(data)

            # Decompress if enabled
            if message.compressed:
                data = snappy.decompress(data)

            # Parse JSON
            json_data = json.loads(data.decode('utf-8'))
            return Message.from_dict(json_data)

        except Exception as e:
            raise SerializationError(f"Failed to deserialize message: {str(e)}")


class MessageBroker:
    """
    Main message broker class that provides a unified interface for
    message operations across different backends.
    """

    def __init__(self, backend_type: str, config_path: str, encryption_key: Optional[bytes] = None):
        self.backend_type = backend_type
        self.config_path = config_path
        self.serializer = MessageSerializer(encryption_key)
        self.backend: Optional[MessageBrokerBackend] = None
        self.config: Dict[str, Any] = {}
        self.producers: Dict[str, Any] = {}
        self.consumers: Dict[str, Any] = {}
        self.metrics = {
            'messages_published': 0,
            'messages_consumed': 0,
            'messages_failed': 0,
            'publish_rate': 0.0,
            'consume_rate': 0.0,
            'error_rate': 0.0
        }
        self._last_metrics_update = time.time()

        # Initialize backend
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the appropriate backend based on type."""
        if self.backend_type == "rabbitmq":
            from .backends.rabbitmq_backend import RabbitMQBackend
            self.backend = RabbitMQBackend(self.config)
        elif self.backend_type == "redis":
            from .backends.redis_backend import RedisBackend
            self.backend = RedisBackend(self.config)
        elif self.backend_type == "kafka":
            from .backends.kafka_backend import KafkaBackend
            self.backend = KafkaBackend(self.config)
        else:
            raise ValueError(f"Unsupported backend type: {self.backend_type}")

    async def load_config(self):
        """Load configuration from file."""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                content = await f.read()
                self.config = yaml.safe_load(content)

            # Reinitialize backend with loaded config
            self._initialize_backend()

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {str(e)}")
            raise

    async def connect(self):
        """Connect to the message broker."""
        if not self.config:
            await self.load_config()

        try:
            await self.backend.connect()
            logger.info(f"Connected to {self.backend_type} message broker")
        except Exception as e:
            logger.error(f"Failed to connect to {self.backend_type}: {str(e)}")
            raise ConnectionError(f"Connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from the message broker."""
        if self.backend:
            await self.backend.disconnect()
            logger.info(f"Disconnected from {self.backend_type} message broker")

    async def publish(self, message: Message, routing_key: str = "") -> bool:
        """
        Publish a message to the broker.

        Args:
            message: The message to publish
            routing_key: The routing key for message routing

        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            # Serialize message
            serialized_data = self.serializer.serialize(message)

            # Use circuit breaker for publishing
            with self.backend.circuit_breaker:
                success = await self.backend.publish(message, routing_key)
                if success:
                    self.metrics['messages_published'] += 1
                    self._update_metrics()
                    return True
                else:
                    self.metrics['messages_failed'] += 1
                    return False

        except CircuitBreakerError:
            logger.error("Circuit breaker is open - cannot publish message")
            self.metrics['messages_failed'] += 1
            return False

        except Exception as e:
            logger.error(f"Failed to publish message {message.id}: {str(e)}")
            self.metrics['messages_failed'] += 1
            return False

    async def consume(self, queue_config: ConsumerConfig, handler: AsyncMessageHandler):
        """
        Start consuming messages from a queue.

        Args:
            queue_config: Consumer configuration
            handler: Async message handler function
        """
        try:
            await self.backend.consume(queue_config, handler)
            logger.info(f"Started consuming from queue: {queue_config.queue}")
        except Exception as e:
            logger.error(f"Failed to start consuming from {queue_config.queue}: {str(e)}")
            raise ConsumeError(f"Consume failed: {str(e)}")

    async def declare_queue(self, queue_config: QueueConfig) -> bool:
        """Declare a queue."""
        try:
            return await self.backend.declare_queue(queue_config)
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_config.name}: {str(e)}")
            return False

    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool:
        """Declare an exchange."""
        try:
            return await self.backend.declare_exchange(exchange_config)
        except Exception as e:
            logger.error(f"Failed to declare exchange {exchange_config.name}: {str(e)}")
            return False

    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind a queue to an exchange with a routing key."""
        try:
            return await self.backend.bind_queue(queue, exchange, routing_key)
        except Exception as e:
            logger.error(f"Failed to bind queue {queue} to {exchange}: {str(e)}")
            return False

    async def ack_message(self, delivery_tag: str):
        """Acknowledge a message."""
        await self.backend.ack_message(delivery_tag)
        self.metrics['messages_consumed'] += 1
        self._update_metrics()

    async def nack_message(self, delivery_tag: str, requeue: bool = False):
        """Negative acknowledgment of a message."""
        await self.backend.nack_message(delivery_tag, requeue)

    def _update_metrics(self):
        """Update rate-based metrics."""
        now = time.time()
        time_diff = now - self._last_metrics_update

        if time_diff > 0:
            # Calculate rates (messages per second)
            if self.metrics['messages_published'] > 0:
                self.metrics['publish_rate'] = self.metrics['messages_published'] / time_diff

            if self.metrics['messages_consumed'] > 0:
                self.metrics['consume_rate'] = self.metrics['messages_consumed'] / time_diff

            if self.metrics['messages_failed'] > 0:
                total_messages = self.metrics['messages_published'] + self.metrics['messages_consumed']
                if total_messages > 0:
                    self.metrics['error_rate'] = self.metrics['messages_failed'] / total_messages

        self._last_metrics_update = now

    def get_metrics(self) -> Dict[str, Any]:
        """Get current broker metrics."""
        self._update_metrics()
        return self.metrics.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the broker."""
        health_status = {
            'backend': self.backend_type,
            'connected': self.backend.is_connected if self.backend else False,
            'circuit_breaker_open': self.backend.circuit_breaker.open if self.backend else True,
            'metrics': self.get_metrics(),
            'timestamp': time.time()
        }

        # Test connectivity if connected
        if health_status['connected']:
            try:
                # Try to get queue info as a connectivity test
                info = await self.backend.get_queue_info("health_check_queue")
                health_status['connectivity_test'] = 'passed'
            except:
                health_status['connectivity_test'] = 'failed'

        return health_status


# Circuit breaker implementation
class CircuitBreaker:
    """Circuit breaker for resilience patterns."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def __enter__(self):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.expected_exception):
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
        else:
            self.failure_count = 0
            self.state = 'CLOSED'

    @property
    def open(self) -> bool:
        return self.state == 'OPEN'


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Export main classes
__all__ = [
    'MessageBroker',
    'Message',
    'MessageType',
    'MessagePriority',
    'MessageEncoding',
    'QueueConfig',
    'ExchangeConfig',
    'ConsumerConfig',
    'MessageBrokerError',
    'ConnectionError',
    'PublishError',
    'ConsumeError',
    'SerializationError'
]