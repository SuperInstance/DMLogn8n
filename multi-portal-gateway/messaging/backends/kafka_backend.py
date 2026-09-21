#!/usr/bin/env python3
"""
Kafka Backend - Apache Kafka implementation for message broker backend.

This module provides Kafka-specific implementation including:
- Kafka producer and consumer management
- Topic management and configuration
- Partition management and load balancing
- Consumer group coordination
- Offset management and commits
- Schema registry integration
- High availability and fault tolerance
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaTimeoutError

from ..message_broker import (
    MessageBrokerBackend, Message, QueueConfig, ExchangeConfig, ConsumerConfig,
    ConnectionError, PublishError, ConsumeError
)

logger = logging.getLogger(__name__)


class KafkaCompressionType(Enum):
    """Kafka compression types."""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"


class KafkaAcksConfig(Enum):
    """Kafka acknowledgment configurations."""
    NONE = 0
    LEADER = 1
    ALL = -1


@dataclass
class KafkaConfig:
    """Kafka connection configuration."""
    bootstrap_servers: List[str] = None
    client_id: str = "dmlogn8n-client"
    group_id: str = "dmlogn8n-group"
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_context: Optional[Any] = None
    compression_type: KafkaCompressionType = KafkaCompressionType.NONE
    acks: KafkaAcksConfig = KafkaAcksConfig.LEADER
    retries: int = 3
    retry_backoff_ms: int = 100
    batch_size: int = 16384
    linger_ms: int = 0
    buffer_memory: int = 33554432
    max_request_size: int = 1048576
    request_timeout_ms: int = 30000
    delivery_timeout_ms: int = 120000
    enable_idempotence: bool = False
    max_in_flight_requests_per_connection: int = 5
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    consumer_timeout_ms: int = 100
    partition_assignment_strategy: List[str] = None
    metadata_max_age_ms: int = 300000
    reconnect_backoff_ms: int = 50
    reconnect_backoff_max_ms: int = 1000
    retry_backoff_max_ms: int = 1000
    topic_auto_create: bool = True
    topic_auto_create_partitions: int = 1
    topic_auto_create_replication_factor: int = 1
    topic_auto_create_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.bootstrap_servers is None:
            self.bootstrap_servers = ["localhost:9092"]
        if self.partition_assignment_strategy is None:
            self.partition_assignment_strategy = ["RangeAssignor", "RoundRobinAssignor"]
        if self.topic_auto_create_config is None:
            self.topic_auto_create_config = {}


class KafkaBackend(MessageBrokerBackend):
    """
    Apache Kafka implementation of message broker backend.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.kafka_config = KafkaConfig(**config.get('kafka', {}))
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {}
        self.topics: Dict[str, Dict[str, Any]] = {}
        self.partitions: Dict[str, List[int]] = {}
        self.consumer_groups: Dict[str, List[str]] = {}  # group_id -> consumer_ids
        self._connection_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection to Kafka cluster."""
        async with self._connection_lock:
            if self.is_connected:
                return

            try:
                await self._create_producer()
                await self._test_connection()
                self.is_connected = True
                logger.info(f"Connected to Kafka cluster at {self.kafka_config.bootstrap_servers}")

            except Exception as e:
                logger.error(f"Failed to connect to Kafka: {str(e)}")
                raise ConnectionError(f"Kafka connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close connection to Kafka cluster."""
        try:
            # Stop all consumers
            for consumer_id in list(self.consumers.keys()):
                await self._stop_consumer(consumer_id)

            # Close producer
            if self.producer:
                await self.producer.stop()
                self.producer = None

            self.is_connected = False
            logger.info("Disconnected from Kafka")

        except Exception as e:
            logger.error(f"Error disconnecting from Kafka: {str(e)}")

    async def _create_producer(self):
        """Create Kafka producer."""
        producer_config = {
            "bootstrap_servers": self.kafka_config.bootstrap_servers,
            "client_id": self.kafka_config.client_id,
            "compression_type": self.kafka_config.compression_type.value,
            "acks": self.kafka_config.acks.value,
            "retries": self.kafka_config.retries,
            "retry_backoff_ms": self.kafka_config.retry_backoff_ms,
            "batch_size": self.kafka_config.batch_size,
            "linger_ms": self.kafka_config.linger_ms,
            "buffer_memory": self.kafka_config.buffer_memory,
            "max_request_size": self.kafka_config.max_request_size,
            "request_timeout_ms": self.kafka_config.request_timeout_ms,
            "delivery_timeout_ms": self.kafka_config.delivery_timeout_ms,
            "enable_idempotence": self.kafka_config.enable_idempotence,
            "max_in_flight_requests_per_connection": self.kafka_config.max_in_flight_requests_per_connection,
            "security_protocol": self.kafka_config.security_protocol,
        }

        # Add SASL configuration if provided
        if self.kafka_config.sasl_mechanism:
            producer_config.update({
                "sasl_mechanism": self.kafka_config.sasl_mechanism,
                "sasl_plain_username": self.kafka_config.sasl_username,
                "sasl_plain_password": self.kafka_config.sasl_password,
            })

        # Add SSL configuration if provided
        if self.kafka_config.ssl_context:
            producer_config["ssl_context"] = self.kafka_config.ssl_context

        self.producer = AIOKafkaProducer(**producer_config)
        await self.producer.start()

    async def _test_connection(self):
        """Test Kafka connection by getting cluster metadata."""
        if not self.producer:
            raise ConnectionError("Producer not initialized")

        # Get cluster metadata to test connection
        await self.producer.client._api.get_cluster_metadata()

    async def publish(self, message: Message, routing_key: str = "") -> bool:
        """
        Publish a message to Kafka topic.

        Args:
            message: The message to publish
            routing_key: The routing key (used as topic name)

        Returns:
            bool: True if published successfully
        """
        if not self.is_connected or not self.producer:
            raise ConnectionError("Not connected to Kafka")

        try:
            topic = routing_key or message.topic

            # Ensure topic exists
            await self._ensure_topic_exists(topic)

            # Prepare message key and value
            key = message.headers.get("key", message.id).encode('utf-8')
            value = self._serialize_message(message)

            # Prepare headers
            headers = [
                (k.encode('utf-8'), v.encode('utf-8') if v is not None else b'')
                for k, v in {
                    "message_id": message.id,
                    "message_type": message.type.value,
                    "priority": str(message.priority.value),
                    "timestamp": str(message.timestamp),
                    "source": message.source or "",
                    "destination": message.destination or "",
                    "correlation_id": message.correlation_id or "",
                    "reply_to": message.reply_to or ""
                }.items()
            ]

            # Add custom headers
            for k, v in message.headers.items():
                headers.append((k.encode('utf-8'), str(v).encode('utf-8')))

            # Send message
            await self.producer.send_and_wait(
                topic=topic,
                value=value,
                key=key,
                headers=headers,
                partition=message.headers.get("partition")
            )

            logger.debug(f"Published message {message.id} to topic {topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message {message.id}: {str(e)}")
            raise PublishError(f"Kafka publish failed: {str(e)}")

    async def consume(self, queue_config: ConsumerConfig, handler: callable) -> None:
        """
        Start consuming messages from Kafka topic.

        Args:
            queue_config: Consumer configuration
            handler: Message handler function
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Kafka")

        try:
            topic = queue_config.queue
            consumer_id = queue_config.consumer_tag or f"consumer_{uuid.uuid4()}"

            # Ensure topic exists
            await self._ensure_topic_exists(topic)

            # Create consumer
            consumer = await self._create_consumer(topic, queue_config)
            self.consumers[consumer_id] = consumer

            # Start consumer task
            consumer_task = asyncio.create_task(
                self._consume_loop(consumer_id, consumer, handler)
            )
            self.consumer_tasks[consumer_id] = consumer_task

            logger.info(f"Started consuming from topic {topic} with consumer {consumer_id}")

        except Exception as e:
            logger.error(f"Failed to start consuming from topic {queue_config.queue}: {str(e)}")
            raise ConsumeError(f"Kafka consume failed: {str(e)}")

    async def _create_consumer(self, topic: str, queue_config: ConsumerConfig) -> AIOKafkaConsumer:
        """Create Kafka consumer."""
        consumer_config = {
            "bootstrap_servers": self.kafka_config.bootstrap_servers,
            "client_id": f"{self.kafka_config.client_id}-{queue_config.consumer_tag}",
            "group_id": queue_config.consumer_tag or self.kafka_config.group_id,
            "auto_offset_reset": self.kafka_config.auto_offset_reset,
            "enable_auto_commit": queue_config.auto_ack if queue_config.auto_ack is not None else self.kafka_config.enable_auto_commit,
            "auto_commit_interval_ms": self.kafka_config.auto_commit_interval_ms,
            "max_poll_records": queue_config.prefetch_count if queue_config.prefetch_count else self.kafka_config.max_poll_records,
            "max_poll_interval_ms": self.kafka_config.max_poll_interval_ms,
            "session_timeout_ms": self.kafka_config.session_timeout_ms,
            "heartbeat_interval_ms": self.kafka_config.heartbeat_interval_ms,
            "consumer_timeout_ms": self.kafka_config.consumer_timeout_ms,
            "partition_assignment_strategy": self.kafka_config.partition_assignment_strategy,
            "metadata_max_age_ms": self.kafka_config.metadata_max_age_ms,
            "security_protocol": self.kafka_config.security_protocol,
        }

        # Add SASL configuration if provided
        if self.kafka_config.sasl_mechanism:
            consumer_config.update({
                "sasl_mechanism": self.kafka_config.sasl_mechanism,
                "sasl_plain_username": self.kafka_config.sasl_username,
                "sasl_plain_password": self.kafka_config.sasl_password,
            })

        # Add SSL configuration if provided
        if self.kafka_config.ssl_context:
            consumer_config["ssl_context"] = self.kafka_config.ssl_context

        consumer = AIOKafkaConsumer(topic, **consumer_config)
        await consumer.start()

        return consumer

    async def _consume_loop(self, consumer_id: str, consumer: AIOKafkaConsumer, handler: callable):
        """Main consumer loop."""
        try:
            async for message in consumer:
                try:
                    # Convert Kafka message to our Message format
                    dm_message = self._deserialize_message(message)
                    dm_message.delivery_tag = str(message.offset)
                    dm_message.consumer_tag = consumer_id

                    # Call handler
                    if asyncio.iscoroutinefunction(handler):
                        await handler(dm_message)
                    else:
                        # Run in thread pool for sync handlers
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, handler, dm_message)

                except Exception as e:
                    logger.error(f"Error processing message from topic {message.topic}: {str(e)}")
                    # Continue processing other messages

        except Exception as e:
            logger.error(f"Error in consumer loop for {consumer_id}: {str(e)}")

    async def _ensure_topic_exists(self, topic: str):
        """Ensure topic exists, create if auto-create is enabled."""
        if topic in self.topics:
            return

        if self.kafka_config.topic_auto_create:
            try:
                # Create topic with default configuration
                admin_client = self.producer.client._client
                await admin_client.create_topics([
                    {
                        "topic": topic,
                        "num_partitions": self.kafka_config.topic_auto_create_partitions,
                        "replication_factor": self.kafka_config.topic_auto_create_replication_factor,
                        "config_entries": [
                            {"key": k, "value": str(v)}
                            for k, v in self.kafka_config.topic_auto_create_config.items()
                        ]
                    }
                ])

                self.topics[topic] = {
                    "partitions": self.kafka_config.topic_auto_create_partitions,
                    "replication_factor": self.kafka_config.topic_auto_create_replication_factor,
                    "created_at": time.time()
                }

                logger.info(f"Created topic: {topic}")

            except Exception as e:
                if "TOPIC_ALREADY_EXISTS" not in str(e):
                    logger.warning(f"Failed to create topic {topic}: {str(e)}")

        # Get topic metadata
        try:
            cluster_metadata = await self.producer.client._api.get_cluster_metadata()
            for topic_metadata in cluster_metadata.topics:
                if topic_metadata.topic == topic:
                    self.topics[topic] = {
                        "partitions": len(topic_metadata.partitions),
                        "partition_ids": [p.partition_id for p in topic_metadata.partitions],
                        "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0,
                        "metadata": topic_metadata
                    }
                    break
        except Exception as e:
            logger.error(f"Failed to get metadata for topic {topic}: {str(e)}")

    async def declare_queue(self, queue_config: QueueConfig) -> bool:
        """Declare a topic in Kafka."""
        try:
            topic = queue_config.name
            await self._ensure_topic_exists(topic)

            # Update topic configuration if needed
            if topic in self.topics:
                # Store queue-specific configuration
                self.topics[topic].update({
                    "queue_config": queue_config,
                    "updated_at": time.time()
                })

            logger.debug(f"Declared topic: {queue_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to declare topic {queue_config.name}: {str(e)}")
            return False

    async def declare_exchange(self, exchange_config: ExchangeConfig) -> bool:
        """Declare an exchange (not directly applicable to Kafka)."""
        # In Kafka, exchanges are simulated with topic naming conventions
        logger.info(f"Exchange declaration not applicable to Kafka: {exchange_config.name}")
        return True

    async def bind_queue(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind queue to exchange (not directly applicable to Kafka)."""
        # In Kafka, this would be handled by topic naming conventions
        logger.info(f"Queue binding not applicable to Kafka: {queue} -> {exchange}")
        return True

    async def ack_message(self, delivery_tag: str) -> None:
        """Acknowledge a message."""
        # In Kafka, acknowledgments are typically handled automatically
        # or through consumer commits if auto-commit is disabled
        pass

    async def nack_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """Negative acknowledgment of a message."""
        # In Kafka, this would typically involve seeking to a previous offset
        # or letting the message be reprocessed after session timeout
        pass

    async def get_queue_info(self, queue: str) -> Dict[str, Any]:
        """Get information about a topic."""
        try:
            if queue not in self.topics:
                await self._ensure_topic_exists(queue)

            topic_info = self.topics.get(queue, {})

            return {
                "name": queue,
                "partitions": topic_info.get("partitions", 0),
                "partition_ids": topic_info.get("partition_ids", []),
                "replication_factor": topic_info.get("replication_factor", 0),
                "created_at": topic_info.get("created_at"),
                "updated_at": topic_info.get("updated_at")
            }
        except Exception as e:
            logger.error(f"Failed to get topic info for {queue}: {str(e)}")
            return {}

    def _serialize_message(self, message: Message) -> bytes:
        """Serialize message to bytes."""
        try:
            return json.dumps(message.to_dict()).encode('utf-8')
        except Exception as e:
            logger.error(f"Failed to serialize message {message.id}: {str(e)}")
            raise

    def _deserialize_message(self, kafka_message) -> Message:
        """Deserialize Kafka message to our Message format."""
        try:
            message_data = json.loads(kafka_message.value.decode('utf-8'))
            message = Message.from_dict(message_data)

            # Add Kafka-specific headers
            if kafka_message.headers:
                kafka_headers = {}
                for key, value in kafka_message.headers:
                    kafka_headers[key.decode('utf-8')] = value.decode('utf-8')
                message.headers.update(kafka_headers)

            # Add metadata
            message.headers.update({
                "kafka_topic": kafka_message.topic,
                "kafka_partition": kafka_message.partition,
                "kafka_offset": kafka_message.offset,
                "kafka_timestamp": kafka_message.timestamp,
                "kafka_key": kafka_message.key.decode('utf-8') if kafka_message.key else None
            })

            return message

        except Exception as e:
            logger.error(f"Failed to deserialize message: {str(e)}")
            # Return a basic message structure
            return Message(
                id=str(uuid.uuid4()),
                headers={
                    "kafka_topic": kafka_message.topic,
                    "kafka_partition": kafka_message.partition,
                    "kafka_offset": kafka_message.offset,
                    "error": "Failed to deserialize message",
                    "original_body": kafka_message.value.decode('utf-8', errors='ignore')
                },
                payload={"error": "Failed to deserialize message"}
            )

    async def _stop_consumer(self, consumer_id: str):
        """Stop a consumer."""
        try:
            if consumer_id in self.consumer_tasks:
                task = self.consumer_tasks[consumer_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.consumer_tasks[consumer_id]

            if consumer_id in self.consumers:
                consumer = self.consumers[consumer_id]
                await consumer.stop()
                del self.consumers[consumer_id]

            logger.info(f"Stopped consumer: {consumer_id}")

        except Exception as e:
            logger.error(f"Error stopping consumer {consumer_id}: {str(e)}")

    async def create_topic(self, topic_name: str, num_partitions: int = 1,
                          replication_factor: int = 1, config: Dict[str, Any] = None) -> bool:
        """Create a new topic."""
        try:
            admin_client = self.producer.client._client
            topic_config = config or {}

            await admin_client.create_topics([{
                "topic": topic_name,
                "num_partitions": num_partitions,
                "replication_factor": replication_factor,
                "config_entries": [
                    {"key": k, "value": str(v)}
                    for k, v in topic_config.items()
                ]
            }])

            self.topics[topic_name] = {
                "partitions": num_partitions,
                "replication_factor": replication_factor,
                "config": topic_config,
                "created_at": time.time()
            }

            logger.info(f"Created topic: {topic_name}")
            return True

        except Exception as e:
            if "TOPIC_ALREADY_EXISTS" in str(e):
                logger.info(f"Topic {topic_name} already exists")
                return True
            logger.error(f"Failed to create topic {topic_name}: {str(e)}")
            return False

    async def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic."""
        try:
            admin_client = self.producer.client._client
            await admin_client.delete_topics([topic_name])

            if topic_name in self.topics:
                del self.topics[topic_name]

            logger.info(f"Deleted topic: {topic_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete topic {topic_name}: {str(e)}")
            return False

    async def get_topic_partitions(self, topic_name: str) -> List[int]:
        """Get partition IDs for a topic."""
        try:
            if topic_name not in self.topics:
                await self._ensure_topic_exists(topic_name)

            return self.topics.get(topic_name, {}).get("partition_ids", [])
        except Exception as e:
            logger.error(f"Failed to get partitions for topic {topic_name}: {str(e)}")
            return []

    async def get_consumer_group_info(self, group_id: str) -> Dict[str, Any]:
        """Get consumer group information."""
        try:
            # This would require admin client access to describe consumer groups
            # For now, return basic info
            return {
                "group_id": group_id,
                "consumers": self.consumer_groups.get(group_id, [])
            }
        except Exception as e:
            logger.error(f"Failed to get consumer group info for {group_id}: {str(e)}")
            return {}

    async def get_consumer_offsets(self, group_id: str, topic: str) -> Dict[int, int]:
        """Get consumer group offsets for a topic."""
        try:
            # This would require admin client access to consumer group offsets
            # For now, return empty dict
            return {}
        except Exception as e:
            logger.error(f"Failed to get consumer offsets for {group_id}/{topic}: {str(e)}")
            return {}

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "bootstrap_servers": self.kafka_config.bootstrap_servers,
            "client_id": self.kafka_config.client_id,
            "group_id": self.kafka_config.group_id,
            "is_connected": self.is_connected,
            "security_protocol": self.kafka_config.security_protocol,
            "compression_type": self.kafka_config.compression_type.value,
            "acks": self.kafka_config.acks.value,
            "consumers_count": len(self.consumers),
            "topics_count": len(self.topics)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Kafka connection."""
        health_status = {
            "status": "healthy" if self.is_connected else "unhealthy",
            "connected": self.is_connected,
            "connection_info": self.get_connection_info(),
            "timestamp": time.time()
        }

        if self.is_connected:
            try:
                # Test Kafka connection
                start_time = time.time()
                cluster_metadata = await self.producer.client._api.get_cluster_metadata()
                response_time = time.time() - start_time

                health_status["connection_test"] = "passed"
                health_status["response_time"] = response_time
                health_status["cluster_info"] = {
                    "brokers": len(cluster_metadata.brokers),
                    "topics": len(cluster_metadata.topics),
                    "controller_id": cluster_metadata.controller_id
                }

            except Exception as e:
                health_status["connection_test"] = "failed"
                health_status["error"] = str(e)

        return health_status


# Export main classes
__all__ = [
    'KafkaBackend',
    'KafkaConfig',
    'KafkaCompressionType',
    'KafkaAcksConfig'
]