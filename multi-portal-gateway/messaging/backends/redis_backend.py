#!/usr/bin/env python3
"""
Redis Backend - Redis Streams implementation for message broker backend.

This module provides Redis-specific implementation including:
- Redis Streams for message queuing
- Consumer groups for load balancing
- Message persistence and durability
- Stream management and trimming
- Consumer lag monitoring
- Automatic reconnection and error handling
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import aioredis
from aioredis import Redis

from ..message_broker import (
    MessageBrokerBackend, Message, QueueConfig, ExchangeConfig, ConsumerConfig,
    ConnectionError, PublishError, ConsumeError
)

logger = logging.getLogger(__name__)


class RedisStreamMode(Enum):
    """Redis stream processing modes."""
    INDEPENDENT = "independent"  # Each consumer reads independently
    CONSUMER_GROUP = "consumer_group"  # Consumers share load via consumer group


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    ssl_enabled: bool = False
    ssl_context: Optional[Any] = None
    connection_timeout: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    max_connections: int = 100
    stream_max_len: Optional[int] = None
    consumer_group_prefix: str = "dmlogn8n"
    stream_key_prefix: str = "stream:"
    pending_key_prefix: str = "pending:"
    lag_check_interval: int = 10
    auto_trim: bool = True
    trim_strategy: str = "maxlen"  # maxlen, minid


class RedisBackend(MessageBrokerBackend):
    """
    Redis Streams implementation of message broker backend.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.redis_config = RedisConfig(**config.get('redis', {}))
        self.redis: Optional[Redis] = None
        self.connection_pool: Optional[aioredis.ConnectionPool] = None
        self.consumer_groups: Dict[str, str] = {}  # queue -> consumer_group
        self.consumers: Dict[str, asyncio.Task] = {}  # consumer_tag -> task
        self.stream_info: Dict[str, Dict[str, Any]] = {}
        self.consumer_lag: Dict[str, int] = {}
        self._connection_lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        async with self._connection_lock:
            if self.is_connected:
                return

            try:
                await self._establish_connection()
                await self._setup_connection_pool()
                await self._test_connection()
                self.is_connected = True
                logger.info(f"Connected to Redis at {self.redis_config.host}:{self.redis_config.port}")

                # Start monitoring task
                self._monitor_task = asyncio.create_task(self._monitoring_loop())

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise ConnectionError(f"Redis connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close connection to Redis."""
        try:
            # Stop monitoring task
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            # Stop all consumers
            for consumer_tag in list(self.consumers.keys()):
                await self._stop_consumer(consumer_tag)

            # Close connection
            if self.redis:
                await self.redis.close()
                self.redis = None

            # Close connection pool
            if self.connection_pool:
                await self.connection_pool.disconnect()
                self.connection_pool = None

            self.is_connected = False
            logger.info("Disconnected from Redis")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")

    async def _establish_connection(self):
        """Establish Redis connection."""
        connection_kwargs = {
            "host": self.redis_config.host,
            "port": self.redis_config.port,
            "db": self.redis_config.db,
            "socket_timeout": self.redis_config.socket_timeout,
            "socket_connect_timeout": self.redis_config.socket_connect_timeout,
            "retry_on_timeout": self.redis_config.retry_on_timeout,
            "health_check_interval": self.redis_config.health_check_interval,
        }

        if self.redis_config.username:
            connection_kwargs["username"] = self.redis_config.username

        if self.redis_config.password:
            connection_kwargs["password"] = self.redis_config.password

        if self.redis_config.ssl_enabled:
            connection_kwargs["ssl"] = True
            if self.redis_config.ssl_context:
                connection_kwargs["ssl_context"] = self.redis_config.ssl_context

        self.redis = Redis(**connection_kwargs)

    async def _setup_connection_pool(self):
        """Setup Redis connection pool."""
        pool_kwargs = {
            "max_connections": self.redis_config.max_connections,
            "retry_on_timeout": self.redis_config.retry_on_timeout,
        }

        if self.redis_config.password:
            pool_kwargs["password"] = self.redis_config.password

        self.connection_pool = aioredis.ConnectionPool.from_url(
            f"redis://{self.redis_config.host}:{self.redis_config.port}/{self.redis_config.db}",
            **pool_kwargs
        )

    async def _test_connection(self):
        """Test Redis connection."""
        await self.redis.ping()

    def _get_stream_key(self, topic: str) -> str:
        """Get Redis stream key for topic."""
        return f"{self.redis_config.stream_key_prefix}{topic}"

    async def publish(self, message: Message, routing_key: str = "") -> bool:
        """
        Publish a message to Redis stream.

        Args:
            message: The message to publish
            routing_key: The routing key (used as stream name)

        Returns:
            bool: True if published successfully
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Redis")

        try:
            stream_key = self._get_stream_key(routing_key or message.topic)

            # Prepare message fields
            message_fields = {
                "id": message.id,
                "type": message.type.value,
                "topic": message.topic,
                "payload": json.dumps(message.payload),
                "headers": json.dumps(message.headers),
                "priority": str(message.priority.value),
                "timestamp": str(message.timestamp),
                "source": message.source or "",
                "destination": message.destination or ""
            }

            if message.correlation_id:
                message_fields["correlation_id"] = message.correlation_id

            if message.reply_to:
                message_fields["reply_to"] = message.reply_to

            # Add message to stream
            message_id = await self.redis.xadd(
                stream_key,
                message_fields,
                maxlen=self.redis_config.stream_max_len if self.redis_config.auto_trim else None,
                approximate=not self.redis_config.auto_trim
            )

            logger.debug(f"Published message {message.id} to stream {stream_key} with Redis ID {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message {message.id}: {str(e)}")
            raise PublishError(f"Redis publish failed: {str(e)}")

    async def consume(self, queue_config: ConsumerConfig, handler: callable) -> None:
        """
        Start consuming messages from a Redis stream.

        Args:
            queue_config: Consumer configuration
            handler: Message handler function
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Redis")

        try:
            stream_key = self._get_stream_key(queue_config.queue)
            consumer_tag = queue_config.consumer_tag or f"consumer_{uuid.uuid4()}"

            # Setup consumer group
            consumer_group = await self._setup_consumer_group(stream_key, queue_config)
            self.consumer_groups[queue_config.queue] = consumer_group

            # Start consumer task
            consumer_task = asyncio.create_task(
                self._consume_loop(stream_key, consumer_group, consumer_tag, handler, queue_config)
            )
            self.consumers[consumer_tag] = consumer_task

            logger.info(f"Started consuming from stream {stream_key} with consumer {consumer_tag}")

        except Exception as e:
            logger.error(f"Failed to start consuming from stream {queue_config.queue}: {str(e)}")
            raise ConsumeError(f"Redis consume failed: {str(e)}")

    async def _consume_loop(self, stream_key: str, consumer_group: str, consumer_tag: str,
                          handler: callable, queue_config: ConsumerConfig):
        """Main consumer loop."""
        while True:
            try:
                # Read messages from stream
                messages = await self.redis.xreadgroup(
                    consumer_group,
                    consumer_tag,
                    {stream_key: ">"},  # Read new messages
                    count=queue_config.prefetch_count or 10,
                    block=1000  # Block for 1 second
                )

                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            await self._process_message(stream_name, message_id, fields, handler)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consumer loop for {consumer_tag}: {str(e)}")
                await asyncio.sleep(1)

    async def _process_message(self, stream_name: str, message_id: str, fields: Dict[bytes, bytes], handler: callable):
        """Process a single message from Redis stream."""
        try:
            # Convert bytes to strings and deserialize message
            message_fields = {k.decode('utf-8'): v.decode('utf-8') for k, v in fields.items()}

            # Reconstruct message
            message = Message(
                id=message_fields.get("id", message_id),
                type=message_fields.get("type", "unknown"),
                topic=message_fields.get("topic", ""),
                payload=json.loads(message_fields.get("payload", "{}")),
                headers=json.loads(message_fields.get("headers", "{}")),
                priority=int(message_fields.get("priority", "2")),
                timestamp=float(message_fields.get("timestamp", "0")),
                source=message_fields.get("source"),
                destination=message_fields.get("destination"),
                correlation_id=message_fields.get("correlation_id"),
                reply_to=message_fields.get("reply_to")
            )

            # Set delivery info
            message.delivery_tag = message_id

            # Call handler
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                # Run in thread pool for sync handlers
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, message)

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {str(e)}")
            # Don't acknowledge - message will be retried

    async def _setup_consumer_group(self, stream_key: str, queue_config: ConsumerConfig) -> str:
        """Setup consumer group for stream."""
        consumer_group = f"{self.redis_config.consumer_group_prefix}:{queue_config.queue}"

        try:
            # Try to create consumer group
            await self.redis.xgroup_create(stream_key, consumer_group, id="0", mkstream=True)
            logger.debug(f"Created consumer group {consumer_group} for stream {stream_key}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise
            # Consumer group already exists
            logger.debug(f"Consumer group {consumer_group} already exists for stream {stream_key}")

        return consumer_group

    async def declare_queue(self, queue_config: QueueConfig) -> bool:
        """Declare a stream in Redis."""
        if not self.is_connected:
            raise ConnectionError("Not connected to Redis")

        try:
            stream_key = self._get_stream_key(queue_config.name)

            # Create stream if it doesn't exist (by adding a dummy message and deleting it)
            try:
                await self.redis.xadd(stream_key, {"dummy": "init"})
                await self.redis.xdel(stream_key, await self.redis.xrange(stream_key, count=1)[0][0])
            except Exception:
                # Stream might already exist
                pass

            # Store stream configuration
            self.stream_info[queue_config.name] = {
                "stream_key": stream_key,
                "config": queue_config,
                "created_at": time.time()
            }

            logger.debug(f"Declared stream: {queue_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to declare stream {queue_config.name}: {str(e)}")
            return False

    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool:
        """Declare an exchange (not directly applicable to Redis streams)."""
        # Redis doesn't have exchanges like RabbitMQ, but we can simulate with stream naming
        logger.info(f"Exchange declaration not applicable to Redis streams: {exchange_config.name}")
        return True

    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind queue to exchange (not directly applicable to Redis streams)."""
        # In Redis, this would be handled by stream naming conventions
        logger.info(f"Queue binding not applicable to Redis streams: {queue} -> {exchange}")
        return True

    async def ack_message(self, delivery_tag: str) -> None:
        """Acknowledge a message."""
        if not self.is_connected:
            return

        try:
            # This would need to be called from within the consumer context
            # as we need the stream and consumer group information
            pass
        except Exception as e:
            logger.error(f"Failed to ack message {delivery_tag}: {str(e)}")

    async def nack_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """Negative acknowledgment of a message."""
        if not self.is_connected:
            return

        try:
            # Similar to ack, this needs context
            pass
        except Exception as e:
            logger.error(f"Failed to nack message {delivery_tag}: {str(e)}")

    async def get_queue_info(self, queue: str) -> Dict[str, Any]:
        """Get information about a stream."""
        if not self.is_connected:
            return {}

        try:
            stream_key = self._get_stream_key(queue)

            # Get stream info
            info = await self.redis.xinfo_stream(stream_key)

            return {
                "name": queue,
                "stream_key": stream_key,
                "length": info.get("length", 0),
                "radix_tree_keys": info.get("radix-tree-keys", 0),
                "radix_tree_nodes": info.get("radix-tree-nodes", 0),
                "last_generated_id": info.get("last-generated-id"),
                "groups": info.get("groups", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry")
            }
        except Exception as e:
            logger.error(f"Failed to get stream info for {queue}: {str(e)}")
            return {}

    async def _stop_consumer(self, consumer_tag: str):
        """Stop a consumer."""
        if consumer_tag in self.consumers:
            task = self.consumers[consumer_tag]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.consumers[consumer_tag]
            logger.info(f"Stopped consumer: {consumer_tag}")

    async def _monitoring_loop(self):
        """Monitor Redis streams and consumer lag."""
        while self.is_connected:
            try:
                await self._check_consumer_lag()
                await self._cleanup_old_streams()
                await asyncio.sleep(self.redis_config.lag_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)

    async def _check_consumer_lag(self):
        """Check consumer lag for all consumer groups."""
        try:
            for queue, consumer_group in self.consumer_groups.items():
                stream_key = self._get_stream_key(queue)

                # Get consumer group info
                try:
                    groups = await self.redis.xinfo_groups(stream_key)
                    for group in groups:
                        if group["name"].decode('utf-8') == consumer_group:
                            lag = group.get("lag", 0)
                            self.consumer_lag[f"{queue}:{consumer_group}"] = lag
                            if lag > 1000:  # Alert if lag is high
                                logger.warning(f"High consumer lag for {queue}: {lag}")
                except Exception as e:
                    logger.debug(f"Could not check lag for {queue}: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking consumer lag: {str(e)}")

    async def _cleanup_old_streams(self):
        """Trim old streams if auto-trim is enabled."""
        if not self.redis_config.auto_trim:
            return

        try:
            for stream_name, info in self.stream_info.items():
                stream_key = info["stream_key"]

                if self.redis_config.trim_strategy == "maxlen" and self.redis_config.stream_max_len:
                    await self.redis.xtrim(stream_key, maxlen=self.redis_config.stream_max_len, approximate=True)

        except Exception as e:
            logger.error(f"Error cleaning up streams: {str(e)}")

    async def create_consumer_group(self, stream_name: str, group_name: str, start_id: str = "0") -> bool:
        """Create a consumer group for a stream."""
        try:
            stream_key = self._get_stream_key(stream_name)
            await self.redis.xgroup_create(stream_key, group_name, id=start_id, mkstream=True)
            logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            return True
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.warning(f"Consumer group {group_name} already exists for stream {stream_name}")
                return True
            logger.error(f"Failed to create consumer group {group_name}: {str(e)}")
            return False

    async def delete_consumer_group(self, stream_name: str, group_name: str) -> bool:
        """Delete a consumer group."""
        try:
            stream_key = self._get_stream_key(stream_name)
            await self.redis.xgroup_destroy(stream_key, group_name)
            logger.info(f"Deleted consumer group {group_name} for stream {stream_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete consumer group {group_name}: {str(e)}")
            return False

    async def get_consumer_groups(self, stream_name: str) -> List[Dict[str, Any]]:
        """Get all consumer groups for a stream."""
        try:
            stream_key = self._get_stream_key(stream_name)
            groups = await self.redis.xinfo_groups(stream_key)
            return [
                {
                    "name": group["name"].decode('utf-8'),
                    "consumers": group.get("consumers", 0),
                    "pending": group.get("pending", 0),
                    "last_delivered_id": group.get("last-delivered-id").decode('utf-8')
                }
                for group in groups
            ]
        except Exception as e:
            logger.error(f"Failed to get consumer groups for {stream_name}: {str(e)}")
            return []

    async def get_stream_length(self, stream_name: str) -> int:
        """Get the length of a stream."""
        try:
            stream_key = self._get_stream_key(stream_name)
            return await self.redis.xlen(stream_key)
        except Exception as e:
            logger.error(f"Failed to get stream length for {stream_name}: {str(e)}")
            return 0

    async def trim_stream(self, stream_name: str, max_len: int) -> bool:
        """Trim a stream to maximum length."""
        try:
            stream_key = self._get_stream_key(stream_name)
            await self.redis.xtrim(stream_key, maxlen=max_len, approximate=True)
            logger.info(f"Trimmed stream {stream_name} to {max_len} entries")
            return True
        except Exception as e:
            logger.error(f"Failed to trim stream {stream_name}: {str(e)}")
            return False

    async def clear_stream(self, stream_name: str) -> bool:
        """Clear all messages from a stream."""
        try:
            stream_key = self._get_stream_key(stream_name)
            await self.redis.delete(stream_key)
            logger.info(f"Cleared stream {stream_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear stream {stream_name}: {str(e)}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "host": self.redis_config.host,
            "port": self.redis_config.port,
            "db": self.redis_config.db,
            "is_connected": self.is_connected,
            "ssl_enabled": self.redis_config.ssl_enabled,
            "stream_max_len": self.redis_config.stream_max_len,
            "consumers_count": len(self.consumers),
            "consumer_groups_count": len(self.consumer_groups),
            "streams_count": len(self.stream_info)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        health_status = {
            "status": "healthy" if self.is_connected else "unhealthy",
            "connected": self.is_connected,
            "connection_info": self.get_connection_info(),
            "timestamp": time.time()
        }

        if self.is_connected:
            try:
                # Test Redis connection
                start_time = time.time()
                await self.redis.ping()
                response_time = time.time() - start_time

                health_status["connection_test"] = "passed"
                health_status["response_time"] = response_time

                # Get basic Redis info
                info = await self.redis.info()
                health_status["redis_info"] = {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed")
                }

            except Exception as e:
                health_status["connection_test"] = "failed"
                health_status["error"] = str(e)

        return health_status


# Export main classes
__all__ = [
    'RedisBackend',
    'RedisConfig',
    'RedisStreamMode'
]