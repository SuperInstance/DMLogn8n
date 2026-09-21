#!/usr/bin/env python3
"""
RabbitMQ Backend - RabbitMQ implementation for message broker backend.

This module provides RabbitMQ-specific implementation including:
- Connection management and connection pooling
- Exchange and queue management
- Message publishing and consuming
- Dead letter queue handling
- Publisher confirms and consumer acknowledgments
- Automatic reconnection and error handling
"""

import asyncio
import json
import logging
import time
import ssl
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from aio_pika.pool import Pool

from ..message_broker import (
    MessageBrokerBackend, Message, QueueConfig, ExchangeConfig, ConsumerConfig,
    ConnectionError, PublishError, ConsumeError
)

logger = logging.getLogger(__name__)


class RabbitMQExchangeType(Enum):
    """RabbitMQ exchange types."""
    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"
    HEADERS = "headers"


@dataclass
class RabbitMQConfig:
    """RabbitMQ connection configuration."""
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    ssl_enabled: bool = False
    ssl_context: Optional[ssl.SSLContext] = None
    heartbeat: int = 600
    connection_timeout: int = 30
    retry_delay: int = 5
    max_retries: int = 10
    client_properties: Dict[str, str] = None
    blocked_connection_timeout: int = 300
    publisher_confirms: bool = True
    frame_max: int = 131072
    heartbeat_timeout: int = 600


class RabbitMQBackend(MessageBrokerBackend):
    """
    RabbitMQ implementation of message broker backend.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rabbit_config = RabbitMQConfig(**config.get('rabbitmq', {}))
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.connection_pool: Optional[Pool] = None
        self.consumer_tags: Dict[str, str] = {}
        self.exchanges: Dict[str, aio_pika.Exchange] = {}
        self.queues: Dict[str, aio_pika.Queue] = {}
        self._connection_lock = asyncio.Lock()
        self._channel_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        async with self._connection_lock:
            if self.is_connected:
                return

            try:
                await self._establish_connection()
                await self._establish_channel()
                await self._setup_connection_pool()
                self.is_connected = True
                logger.info(f"Connected to RabbitMQ at {self.rabbit_config.host}:{self.rabbit_config.port}")

            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                raise ConnectionError(f"RabbitMQ connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        try:
            # Close all consumers
            for queue_name, consumer_tag in self.consumer_tags.items():
                try:
                    if self.channel and consumer_tag:
                        await self.channel.basic_cancel(consumer_tag)
                except Exception as e:
                    logger.warning(f"Error cancelling consumer for {queue_name}: {str(e)}")

            self.consumer_tags.clear()

            # Close channel
            if self.channel:
                await self.channel.close()
                self.channel = None

            # Close connection
            if self.connection:
                await self.connection.close()
                self.connection = None

            # Close connection pool
            if self.connection_pool:
                await self.connection_pool.close()
                self.connection_pool = None

            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")

        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {str(e)}")

    async def _establish_connection(self):
        """Establish robust connection to RabbitMQ."""
        url = self._build_connection_url()

        for attempt in range(self.rabbit_config.max_retries):
            try:
                self.connection = await aio_pika.connect_robust(
                    url,
                    heartbeat=self.rabbit_config.heartbeat,
                    blocked_connection_timeout=self.rabbit_config.blocked_connection_timeout,
                    timeout=self.rabbit_config.connection_timeout,
                    client_properties=self.rabbit_config.client_properties or {
                        "service": "DMLogn8n",
                        "version": "1.0.0"
                    }
                )
                return

            except Exception as e:
                if attempt == self.rabbit_config.max_retries - 1:
                    raise
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(self.rabbit_config.retry_delay)

    async def _establish_channel(self):
        """Establish and configure channel."""
        if not self.connection:
            raise ConnectionError("No connection available")

        self.channel = await self.connection.channel(
            frame_max=self.rabbit_config.frame_max,
            publisher_confirms=self.rabbit_config.publisher_confirms
        )

        # Set QoS for consumers
        await self.channel.set_qos(prefetch_count=100)

    async def _setup_connection_pool(self):
        """Setup connection pool for better performance."""
        if not self.connection:
            raise ConnectionError("No connection available for pool setup")

        async def get_connection():
            if not self.connection or self.connection.is_closed:
                await self._establish_connection()
            return self.connection

        self.connection_pool = Pool(get_connection, max_size=10)

    def _build_connection_url(self) -> str:
        """Build RabbitMQ connection URL."""
        protocol = "amqps" if self.rabbit_config.ssl_enabled else "amqp"

        auth = ""
        if self.rabbit_config.username and self.rabbit_config.password:
            auth = f"{self.rabbit_config.username}:{self.rabbit_config.password}@"

        url = f"{protocol}://{auth}{self.rabbit_config.host}:{self.rabbit_config.port}{self.rabbit_config.virtual_host}"
        return url

    async def publish(self, message: Message, routing_key: str = "") -> bool:
        """
        Publish a message to RabbitMQ.

        Args:
            message: The message to publish
            routing_key: The routing key for message routing

        Returns:
            bool: True if published successfully
        """
        if not self.is_connected or not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")

        try:
            # Get or create exchange
            exchange_name = message.headers.get("exchange", "default")
            exchange = await self._get_or_create_exchange(exchange_name, "topic")

            # Prepare message properties
            message_properties = aio_pika.Message(
                body=self._serialize_message(message),
                headers={
                    **message.headers,
                    "message_id": message.id,
                    "message_type": message.type.value,
                    "priority": message.priority.value,
                    "timestamp": message.timestamp,
                    "source": message.source,
                    "destination": message.destination
                },
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT if message.expiration else aio_pika.DeliveryMode.NOT_PERSISTENT,
                priority=message.priority.value,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                expiration=str(int(message.expiration * 1000)) if message.expiration else None,
                message_id=message.id,
                timestamp=message.timestamp
            )

            # Publish message
            if self.rabbit_config.publisher_confirms:
                # Wait for publisher confirmation
                await exchange.publish(message_properties, routing_key or message.topic)
            else:
                # Fire and forget
                await exchange.publish(message_properties, routing_key or message.topic, mandatory=False)

            logger.debug(f"Published message {message.id} to exchange {exchange_name} with routing key {routing_key or message.topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message {message.id}: {str(e)}")
            raise PublishError(f"RabbitMQ publish failed: {str(e)}")

    async def consume(self, queue_config: ConsumerConfig, handler: callable) -> None:
        """
        Start consuming messages from a queue.

        Args:
            queue_config: Consumer configuration
            handler: Message handler function
        """
        if not self.is_connected or not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")

        try:
            # Get or create queue
            queue = await self._get_or_create_queue(queue_config.queue)

            # Start consuming
            async def message_processor(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        # Convert RabbitMQ message to our Message format
                        dm_message = self._deserialize_message(message)
                        dm_message.delivery_tag = message.delivery_tag
                        dm_message.consumer_tag = message.consumer_tag

                        # Call handler
                        if asyncio.iscoroutinefunction(handler):
                            await handler(dm_message)
                        else:
                            # Run in thread pool for sync handlers
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, handler, dm_message)

                    except Exception as e:
                        logger.error(f"Error processing message {message.message_id}: {str(e)}")
                        # Message will be automatically requeued or sent to DLQ based on queue configuration

            # Start consumer
            consumer_tag = await queue.consume(message_processor)
            self.consumer_tags[queue_config.queue] = consumer_tag

            logger.info(f"Started consuming from queue {queue_config.queue} with consumer tag {consumer_tag}")

        except Exception as e:
            logger.error(f"Failed to start consuming from queue {queue_config.queue}: {str(e)}")
            raise ConsumeError(f"RabbitMQ consume failed: {str(e)}")

    async def declare_queue(self, queue_config: QueueConfig) -> bool:
        """Declare a queue in RabbitMQ."""
        if not self.is_connected or not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")

        try:
            # Build queue arguments
            arguments = {}

            if queue_config.message_ttl:
                arguments["x-message-ttl"] = queue_config.message_ttl

            if queue_config.max_length:
                arguments["x-max-length"] = queue_config.max_length

            if queue_config.dead_letter_exchange:
                arguments["x-dead-letter-exchange"] = queue_config.dead_letter_exchange

            if queue_config.dead_letter_routing_key:
                arguments["x-dead-letter-routing-key"] = queue_config.dead_letter_routing_key

            if queue_config.priority:
                arguments["x-max-priority"] = 10

            # Add custom arguments
            arguments.update(queue_config.arguments)

            # Declare queue
            queue = await self.channel.declare_queue(
                queue_config.name,
                durable=queue_config.durable,
                exclusive=queue_config.exclusive,
                auto_delete=queue_config.auto_delete,
                arguments=arguments if arguments else None
            )

            self.queues[queue_config.name] = queue
            logger.debug(f"Declared queue: {queue_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to declare queue {queue_config.name}: {str(e)}")
            return False

    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool:
        """Declare an exchange in RabbitMQ."""
        if not self.is_connected or not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")

        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                exchange_config.name,
                type=exchange_config.type,
                durable=exchange_config.durable,
                auto_delete=exchange_config.auto_delete,
                internal=exchange_config.internal,
                arguments=exchange_config.arguments if exchange_config.arguments else None
            )

            self.exchanges[exchange_config.name] = exchange
            logger.debug(f"Declared exchange: {exchange_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to declare exchange {exchange_config.name}: {str(e)}")
            return False

    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind a queue to an exchange with a routing key."""
        if not self.is_connected or not self.channel:
            raise ConnectionError("Not connected to RabbitMQ")

        try:
            queue_obj = await self._get_or_create_queue(queue)
            exchange_obj = await self._get_or_create_exchange(exchange, "topic")

            await queue_obj.bind(exchange_obj, routing_key)
            logger.debug(f"Bound queue {queue} to exchange {exchange} with routing key {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to bind queue {queue} to exchange {exchange}: {str(e)}")
            return False

    async def ack_message(self, delivery_tag: str) -> None:
        """Acknowledge a message."""
        if not self.channel:
            return

        try:
            await self.channel.basic_ack(delivery_tag)
        except Exception as e:
            logger.error(f"Failed to ack message {delivery_tag}: {str(e)}")

    async def nack_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """Negative acknowledgment of a message."""
        if not self.channel:
            return

        try:
            await self.channel.basic_nack(delivery_tag, requeue=requeue)
        except Exception as e:
            logger.error(f"Failed to nack message {delivery_tag}: {str(e)}")

    async def get_queue_info(self, queue: str) -> Dict[str, Any]:
        """Get information about a queue."""
        if not self.channel:
            return {}

        try:
            # This would require using RabbitMQ management API or channel.queue_declare with passive=True
            # For now, return basic info
            return {
                "name": queue,
                "exists": queue in self.queues
            }
        except Exception as e:
            logger.error(f"Failed to get queue info for {queue}: {str(e)}")
            return {}

    async def _get_or_create_queue(self, queue_name: str) -> aio_pika.Queue:
        """Get existing queue or create default one."""
        if queue_name in self.queues:
            return self.queues[queue_name]

        # Declare default queue
        queue_config = QueueConfig(name=queue_name)
        await self.declare_queue(queue_config)
        return self.queues[queue_name]

    async def _get_or_create_exchange(self, exchange_name: str, exchange_type: str = "topic") -> aio_pika.Exchange:
        """Get existing exchange or create default one."""
        if exchange_name in self.exchanges:
            return self.exchanges[exchange_name]

        # Declare default exchange
        exchange_config = ExchangeConfig(name=exchange_name, type=exchange_type)
        await self.declare_exchange(exchange_config)
        return self.exchanges[exchange_name]

    def _serialize_message(self, message: Message) -> bytes:
        """Serialize message to bytes."""
        try:
            return json.dumps(message.to_dict()).encode('utf-8')
        except Exception as e:
            logger.error(f"Failed to serialize message {message.id}: {str(e)}")
            raise

    def _deserialize_message(self, rabbit_message: aio_pika.IncomingMessage) -> Message:
        """Deserialize RabbitMQ message to our Message format."""
        try:
            message_data = json.loads(rabbit_message.body.decode('utf-8'))
            message = Message.from_dict(message_data)
            message.headers.update(rabbit_message.headers or {})
            return message
        except Exception as e:
            logger.error(f"Failed to deserialize message: {str(e)}")
            # Return a basic message structure
            return Message(
                id=rabbit_message.message_id or str(uuid.uuid4()),
                headers=rabbit_message.headers or {},
                payload={"error": "Failed to deserialize message", "original_body": rabbit_message.body.decode('utf-8', errors='ignore')}
            )

    async def setup_dead_letter_infrastructure(self):
        """Setup dead letter exchange and queues."""
        try:
            # Declare dead letter exchange
            dlx_config = ExchangeConfig(
                name="dead.letter.exchange",
                type="topic",
                durable=True
            )
            await self.declare_exchange(dlx_config)

            # Declare dead letter queue
            dlq_config = QueueConfig(
                name="dead.letter.queue",
                durable=True,
                arguments={
                    "x-message-ttl": 604800000  # 7 days
                }
            )
            await self.declare_queue(dlq_config)

            # Bind dead letter queue
            await self.bind_queue("dead.letter.queue", "dead.letter.exchange", "#")

            logger.info("Dead letter infrastructure setup complete")

        except Exception as e:
            logger.error(f"Failed to setup dead letter infrastructure: {str(e)}")

    async def create_exchange_with_queues(self, exchange_name: str, exchange_type: str = "topic",
                                       queue_bindings: Dict[str, List[str]] = None) -> bool:
        """
        Create exchange and bind multiple queues.

        Args:
            exchange_name: Name of the exchange
            exchange_type: Type of exchange
            queue_bindings: Dictionary of queue names to routing keys

        Returns:
            bool: True if successful
        """
        try:
            # Declare exchange
            exchange_config = ExchangeConfig(name=exchange_name, type=exchange_type)
            await self.declare_exchange(exchange_config)

            # Create and bind queues
            if queue_bindings:
                for queue_name, routing_keys in queue_bindings.items():
                    # Declare queue
                    queue_config = QueueConfig(name=queue_name)
                    await self.declare_queue(queue_config)

                    # Bind queue to exchange with each routing key
                    for routing_key in routing_keys:
                        await self.bind_queue(queue_name, exchange_name, routing_key)

            logger.info(f"Created exchange {exchange_name} with {len(queue_bindings or {})} queues")
            return True

        except Exception as e:
            logger.error(f"Failed to create exchange with queues: {str(e)}")
            return False

    async def purge_queue(self, queue_name: str) -> bool:
        """Purge all messages from a queue."""
        try:
            queue = await self._get_or_create_queue(queue_name)
            await queue.purge()
            logger.info(f"Purged queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {str(e)}")
            return False

    async def delete_queue(self, queue_name: str, if_unused: bool = False, if_empty: bool = False) -> bool:
        """Delete a queue."""
        try:
            if queue_name in self.queues:
                queue = self.queues[queue_name]
                await queue.delete(if_unused=if_unused, if_empty=if_empty)
                del self.queues[queue_name]
                logger.info(f"Deleted queue: {queue_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete queue {queue_name}: {str(e)}")
            return False

    async def delete_exchange(self, exchange_name: str, if_unused: bool = False) -> bool:
        """Delete an exchange."""
        try:
            if exchange_name in self.exchanges:
                exchange = self.exchanges[exchange_name]
                await exchange.delete(if_unused=if_unused)
                del self.exchanges[exchange_name]
                logger.info(f"Deleted exchange: {exchange_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete exchange {exchange_name}: {str(e)}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "host": self.rabbit_config.host,
            "port": self.rabbit_config.port,
            "virtual_host": self.rabbit_config.virtual_host,
            "is_connected": self.is_connected,
            "ssl_enabled": self.rabbit_config.ssl_enabled,
            "publisher_confirms": self.rabbit_config.publisher_confirms,
            "exchanges_count": len(self.exchanges),
            "queues_count": len(self.queues),
            "consumers_count": len(self.consumer_tags)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on RabbitMQ connection."""
        health_status = {
            "status": "healthy" if self.is_connected else "unhealthy",
            "connected": self.is_connected,
            "connection_info": self.get_connection_info(),
            "timestamp": time.time()
        }

        if self.is_connected and self.connection:
            try:
                # Try to perform a simple operation
                await self.channel.channel_open()
                health_status["connection_test"] = "passed"
            except Exception as e:
                health_status["connection_test"] = "failed"
                health_status["error"] = str(e)

        return health_status


# Import uuid for message ID generation
import uuid

# Export main class
__all__ = [
    'RabbitMQBackend',
    'RabbitMQConfig',
    'RabbitMQExchangeType'
]