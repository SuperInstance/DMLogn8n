#!/usr/bin/env python3
"""
Event Collector
Collects analytics events from various sources and formats
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import aiofiles
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import redis
from contextlib import asynccontextmanager

from ..analytics_engine import AnalyticsEvent, AnalyticsConfig


@dataclass
class EventSource:
    """Configuration for an event source"""
    source_id: str
    source_type: str  # 'kafka', 'redis', 'http', 'file'
    connection_config: Dict[str, Any]
    event_schema: Dict[str, Any]
    enabled: bool = True


class EventCollector:
    """Collects events from multiple sources"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.sources = {}
        self.consumers = {}
        self.producers = {}

        # Redis connection for buffering
        self.redis_client = redis.from_url(config.redis_url)

    def _setup_logging(self) -> logging.Logger:
        """Setup event collector logging"""
        logger = logging.getLogger("event_collector")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def add_source(self, source: EventSource):
        """Add a new event source"""
        self.sources[source.source_id] = source
        self.logger.info(f"Added event source: {source.source_id}")

    async def start_collection(self):
        """Start collecting from all sources"""
        self.logger.info("Starting event collection...")

        for source_id, source in self.sources.items():
            if source.enabled:
                try:
                    if source.source_type == 'kafka':
                        await self._start_kafka_consumer(source)
                    elif source.source_type == 'redis':
                        await self._start_redis_consumer(source)
                    elif source.source_type == 'http':
                        await self._start_http_consumer(source)
                    elif source.source_type == 'file':
                        await self._start_file_consumer(source)
                except Exception as e:
                    self.logger.error(f"Failed to start consumer for {source_id}: {e}")

    async def stop_collection(self):
        """Stop all event collection"""
        self.logger.info("Stopping event collection...")

        for consumer in self.consumers.values():
            try:
                if hasattr(consumer, 'close'):
                    consumer.close()
            except Exception as e:
                self.logger.error(f"Error closing consumer: {e}")

        for producer in self.producers.values():
            try:
                if hasattr(producer, 'close'):
                    producer.close()
            except Exception as e:
                self.logger.error(f"Error closing producer: {e}")

    async def collect_kafka_events(self, topic: str, group_id: str) -> List[AnalyticsEvent]:
        """Collect events from Kafka topic"""
        events = []

        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.config.kafka_bootstrap_servers.split(','),
                group_id=group_id,
                auto_offset_reset='latest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )

            # Poll for messages
            message_batch = consumer.poll(timeout_ms=1000)

            for topic_partition, messages in message_batch.items():
                for message in messages:
                    try:
                        event = await self._parse_event(message.value, 'kafka')
                        if event:
                            events.append(event)
                    except Exception as e:
                        self.logger.error(f"Error parsing Kafka message: {e}")

        except KafkaError as e:
            self.logger.error(f"Kafka error: {e}")
        except Exception as e:
            self.logger.error(f"Error collecting from Kafka: {e}")

        return events

    async def collect_redis_events(self, pattern: str = "analytics:*") -> List[AnalyticsEvent]:
        """Collect events from Redis streams"""
        events = []

        try:
            # Get all matching streams
            streams = self.redis_client.scan_iter(match=pattern)

            for stream_key in streams:
                # Read from stream
                stream_data = self.redis_client.xread(
                    {stream_key: '0-0'},
                    count=100,
                    block=100
                )

                for stream, messages in stream_data:
                    for message_id, fields in messages:
                        try:
                            event = await self._parse_event(fields, 'redis')
                            if event:
                                events.append(event)
                        except Exception as e:
                            self.logger.error(f"Error parsing Redis message: {e}")

        except Exception as e:
            self.logger.error(f"Error collecting from Redis: {e}")

        return events

    async def collect_http_events(self, endpoint: str, auth: Dict[str, str] = None) -> List[AnalyticsEvent]:
        """Collect events from HTTP endpoint"""
        events = []

        try:
            headers = {}
            if auth:
                headers['Authorization'] = f"{auth.get('type', 'Bearer')} {auth.get('token', '')}"

            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        if isinstance(data, list):
                            for item in data:
                                event = await self._parse_event(item, 'http')
                                if event:
                                    events.append(event)
                        else:
                            event = await self._parse_event(data, 'http')
                            if event:
                                events.append(event)
                    else:
                        self.logger.warning(f"HTTP endpoint returned status {response.status}")

        except Exception as e:
            self.logger.error(f"Error collecting from HTTP endpoint: {e}")

        return events

    async def collect_file_events(self, file_path: str, format: str = 'json') -> List[AnalyticsEvent]:
        """Collect events from file"""
        events = []

        try:
            async with aiofiles.open(file_path, 'r') as file:
                if format == 'json':
                    content = await file.read()
                    data = json.loads(content)

                    if isinstance(data, list):
                        for item in data:
                            event = await self._parse_event(item, 'file')
                            if event:
                                events.append(event)
                    else:
                        event = await self._parse_event(data, 'file')
                        if event:
                            events.append(event)
                elif format == 'ndjson':
                    async for line in file:
                        line = line.strip()
                        if line:
                            item = json.loads(line)
                            event = await self._parse_event(item, 'file')
                            if event:
                                events.append(event)

        except Exception as e:
            self.logger.error(f"Error collecting from file {file_path}: {e}")

        return events

    async def _parse_event(self, raw_event: Dict[str, Any], source: str) -> Optional[AnalyticsEvent]:
        """Parse raw event into AnalyticsEvent"""
        try:
            # Validate required fields
            required_fields = ['event_type', 'user_id', 'session_id']
            for field in required_fields:
                if field not in raw_event:
                    self.logger.warning(f"Missing required field '{field}' in event from {source}")
                    return None

            # Generate event ID if not provided
            event_id = raw_event.get('event_id') or f"{source}_{datetime.utcnow().timestamp()}_{hash(str(raw_event))}"

            # Parse timestamp
            timestamp_str = raw_event.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()

            # Extract properties (all other fields)
            properties = {k: v for k, v in raw_event.items()
                         if k not in ['event_id', 'event_type', 'user_id', 'session_id', 'timestamp', 'source', 'version']}

            event = AnalyticsEvent(
                event_id=event_id,
                event_type=raw_event['event_type'],
                user_id=raw_event['user_id'],
                session_id=raw_event['session_id'],
                timestamp=timestamp,
                properties=properties,
                source=source,
                version=raw_event.get('version', '1.0')
            )

            # Validate against schema if available
            if source in self.sources:
                schema = self.sources[source].event_schema
                if not self._validate_event_schema(event, schema):
                    self.logger.warning(f"Event schema validation failed for {event.event_id}")
                    return None

            return event

        except Exception as e:
            self.logger.error(f"Error parsing event from {source}: {e}")
            return None

    def _validate_event_schema(self, event: AnalyticsEvent, schema: Dict[str, Any]) -> bool:
        """Validate event against schema"""
        try:
            # Basic validation - could be extended with JSON Schema
            if 'required_properties' in schema:
                for prop in schema['required_properties']:
                    if prop not in event.properties:
                        return False

            if 'property_types' in schema:
                for prop, expected_type in schema['property_types'].items():
                    if prop in event.properties:
                        if not isinstance(event.properties[prop], expected_type):
                            return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating event schema: {e}")
            return False

    async def _start_kafka_consumer(self, source: EventSource):
        """Start Kafka consumer for a source"""
        config = source.connection_config

        consumer = KafkaConsumer(
            config['topic'],
            bootstrap_servers=self.config.kafka_bootstrap_servers.split(','),
            group_id=config.get('group_id', f'analytics_{source.source_id}'),
            auto_offset_reset=config.get('auto_offset_reset', 'latest'),
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        self.consumers[source.source_id] = consumer

        # Start consuming in background
        asyncio.create_task(self._kafka_consumer_loop(source, consumer))

    async def _start_redis_consumer(self, source: EventSource):
        """Start Redis consumer for a source"""
        config = source.connection_config
        pattern = config.get('pattern', 'analytics:*')

        # Start consuming in background
        asyncio.create_task(self._redis_consumer_loop(source, pattern))

    async def _start_http_consumer(self, source: EventSource):
        """Start HTTP consumer for a source"""
        config = source.connection_config
        interval = config.get('interval', 60)  # seconds

        # Start polling in background
        asyncio.create_task(self._http_consumer_loop(source, interval))

    async def _start_file_consumer(self, source: EventSource):
        """Start file consumer for a source"""
        config = source.connection_config
        interval = config.get('interval', 30)  # seconds

        # Start watching file in background
        asyncio.create_task(self._file_consumer_loop(source, interval))

    async def _kafka_consumer_loop(self, source: EventSource, consumer):
        """Kafka consumer loop"""
        self.logger.info(f"Starting Kafka consumer for {source.source_id}")

        while True:
            try:
                message_batch = consumer.poll(timeout_ms=1000)

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        event = await self._parse_event(message.value, 'kafka')
                        if event:
                            await self._store_event(event)

                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in Kafka consumer loop: {e}")
                await asyncio.sleep(5)

    async def _redis_consumer_loop(self, source: EventSource, pattern):
        """Redis consumer loop"""
        self.logger.info(f"Starting Redis consumer for {source.source_id}")

        while True:
            try:
                events = await self.collect_redis_events(pattern)
                for event in events:
                    await self._store_event(event)

                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in Redis consumer loop: {e}")
                await asyncio.sleep(5)

    async def _http_consumer_loop(self, source: EventSource, interval):
        """HTTP consumer loop"""
        self.logger.info(f"Starting HTTP consumer for {source.source_id}")
        config = source.connection_config

        while True:
            try:
                events = await self.collect_http_events(
                    config['endpoint'],
                    config.get('auth')
                )
                for event in events:
                    await self._store_event(event)

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in HTTP consumer loop: {e}")
                await asyncio.sleep(60)

    async def _file_consumer_loop(self, source: EventSource, interval):
        """File consumer loop"""
        self.logger.info(f"Starting file consumer for {source.source_id}")
        config = source.connection_config

        while True:
            try:
                events = await self.collect_file_events(
                    config['file_path'],
                    config.get('format', 'json')
                )
                for event in events:
                    await self._store_event(event)

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in file consumer loop: {e}")
                await asyncio.sleep(60)

    async def _store_event(self, event: AnalyticsEvent):
        """Store collected event"""
        try:
            # Store in Redis buffer for processing
            buffer_key = "analytics:event_buffer"
            await self.redis_client.lpush(buffer_key, json.dumps(event.__dict__))

            # Trim buffer to prevent unlimited growth
            await self.redis_client.ltrim(buffer_key, 0, 10000)

        except Exception as e:
            self.logger.error(f"Error storing event: {e}")

    def get_source_status(self) -> Dict[str, Any]:
        """Get status of all event sources"""
        status = {}

        for source_id, source in self.sources.items():
            status[source_id] = {
                'source_type': source.source_type,
                'enabled': source.enabled,
                'connected': source_id in self.consumers,
                'last_event_time': self._get_last_event_time(source_id)
            }

        return status

    def _get_last_event_time(self, source_id: str) -> Optional[datetime]:
        """Get last event time for a source"""
        try:
            key = f"analytics:source:last_event:{source_id}"
            timestamp = self.redis_client.get(key)
            if timestamp:
                return datetime.fromisoformat(timestamp.decode('utf-8'))
        except Exception:
            pass
        return None