#!/usr/bin/env python3
"""
DMLogn8n Data Flow Manager - Central Data Coordination
Manages data flow between all systems with routing and transformation
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import aiofiles
import hashlib
import pickle
from pathlib import Path
import asyncio
from collections import defaultdict, deque

class DataType(Enum):
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"
    STREAM = "stream"
    WORKFLOW = "workflow"
    METRICS = "metrics"
    LOGS = "logs"
    EVENTS = "events"

class FlowPriority(Enum):
    CRITICAL = 1    # Real-time data (health checks, alerts)
    HIGH = 2        # User requests, API calls
    NORMAL = 3      # Workflow data, processing
    LOW = 4         # Batch jobs, analytics
    BACKGROUND = 5  # Cleanup, maintenance

class FlowStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class DataPacket:
    id: str
    data: Any
    data_type: DataType
    source: str
    destination: Optional[str]
    priority: FlowPriority
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    ttl: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class FlowRule:
    id: str
    name: str
    source_pattern: str
    destination: str
    transformation: Optional[str] = None
    filter_condition: Optional[str] = None
    priority: FlowPriority = FlowPriority.NORMAL
    enabled: bool = True
    rate_limit: Optional[int] = None
    batch_size: Optional[int] = None

@dataclass
class DataStream:
    id: str
    name: str
    source: str
    data_type: DataType
    buffer_size: int = 1000
    current_size: int = 0
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    consumers: List[str] = field(default_factory=list)

class DataFlowManager:
    """
    Central data flow manager with routing, transformation, and monitoring
    """

    def __init__(self, event_bus=None, service_registry=None):
        self.event_bus = event_bus
        self.service_registry = service_registry
        self.logger = logging.getLogger('DataFlowManager')

        # Core components
        self.active_flows: Dict[str, FlowStatus] = {}
        self.flow_rules: Dict[str, FlowRule] = {}
        self.data_streams: Dict[str, DataStream] = {}
        self.transformers: Dict[str, Callable] = {}
        self.filters: Dict[str, Callable] = {}

        # Queues and buffers
        self.priority_queues: Dict[FlowPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in FlowPriority
        }
        self.routing_table: Dict[str, List[str]] = defaultdict(list)

        # Performance tracking
        self.flow_metrics = {
            'packets_processed': 0,
            'packets_failed': 0,
            'packets_dropped': 0,
            'total_bytes_transferred': 0,
            'average_processing_time': 0.0,
            'active_streams': 0,
            'total_transformations': 0,
            'total_filters_applied': 0
        }

        # Rate limiting
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque())

        # Background tasks
        self.processor_task = None
        self.cleanup_task = None
        self.metrics_task = None
        self.running = False

        # Storage
        self.flow_persistence_file = "/home/activeloguser/DMLogn8n/data/flow_persistence.json"

    async def initialize(self):
        """Initialize the data flow manager"""
        self.logger.info("Initializing Data Flow Manager...")

        # Ensure data directory exists
        await aiofiles.os.makedirs(Path(self.flow_persistence_file).parent, exist_ok=True)

        # Load flow rules and configuration
        await self._load_configuration()

        # Register default transformers
        self._register_default_transformers()

        # Register default filters
        self._register_default_filters()

        # Start background processing
        self.running = True
        self.processor_task = asyncio.create_task(self._process_data_flows())
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_data())
        self.metrics_task = asyncio.create_task(self._collect_metrics())

        self.logger.info("Data Flow Manager initialized")

    async def create_data_packet(
        self,
        data: Any,
        source: str,
        destination: Optional[str] = None,
        data_type: DataType = DataType.JSON,
        priority: FlowPriority = FlowPriority.NORMAL,
        **kwargs
    ) -> str:
        """Create and queue a data packet"""
        packet_id = str(uuid.uuid4())

        packet = DataPacket(
            id=packet_id,
            data=data,
            data_type=data_type,
            source=source,
            destination=destination,
            priority=priority,
            **kwargs
        )

        # Serialize data if needed
        if data_type == DataType.JSON and isinstance(data, (dict, list)):
            packet.data = json.dumps(data)

        # Add to appropriate priority queue
        await self.priority_queues[priority].put(packet)
        self.active_flows[packet_id] = FlowStatus.PENDING

        # Update metrics
        self.flow_metrics['packets_processed'] += 1

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("data.packet.created", {
                "packet_id": packet_id,
                "source": source,
                "destination": destination,
                "data_type": data_type.value,
                "priority": priority.value
            })

        self.logger.debug(f"Created data packet: {packet_id} from {source}")
        return packet_id

    async def send_to_stream(
        self,
        stream_name: str,
        data: Any,
        source: str,
        data_type: DataType = DataType.JSON
    ) -> bool:
        """Send data to a named stream"""
        if stream_name not in self.data_streams:
            # Create stream if it doesn't exist
            await self.create_stream(stream_name, source, data_type)

        stream = self.data_streams[stream_name]

        # Check buffer capacity
        if stream.current_size >= stream.buffer_size:
            self.logger.warning(f"Stream {stream_name} buffer full, dropping oldest data")
            # Remove oldest item (FIFO)
            stream.consumers.pop(0) if stream.consumers else None
            stream.current_size -= 1

        # Add data to stream
        packet_id = await self.create_data_packet(
            data=data,
            source=source,
            destination=f"stream:{stream_name}",
            data_type=data_type
        )

        stream.consumers.append(packet_id)
        stream.current_size += 1
        stream.last_activity = time.time()

        return True

    async def subscribe_to_stream(
        self,
        stream_name: str,
        callback: Callable[[DataPacket], None]
    ) -> str:
        """Subscribe to a data stream"""
        if stream_name not in self.data_streams:
            raise ValueError(f"Stream {stream_name} does not exist")

        subscription_id = str(uuid.uuid4())

        # Store subscription (simplified - in production would use pub/sub)
        if not hasattr(self, 'stream_subscriptions'):
            self.stream_subscriptions = {}

        if stream_name not in self.stream_subscriptions:
            self.stream_subscriptions[stream_name] = {}

        self.stream_subscriptions[stream_name][subscription_id] = callback

        self.logger.info(f"Subscribed to stream {stream_name} with ID {subscription_id}")
        return subscription_id

    async def unsubscribe_from_stream(self, stream_name: str, subscription_id: str):
        """Unsubscribe from a data stream"""
        if hasattr(self, 'stream_subscriptions') and stream_name in self.stream_subscriptions:
            if subscription_id in self.stream_subscriptions[stream_name]:
                del self.stream_subscriptions[stream_name][subscription_id]
                self.logger.info(f"Unsubscribed from stream {stream_name}")

    async def create_flow_rule(
        self,
        name: str,
        source_pattern: str,
        destination: str,
        transformation: Optional[str] = None,
        filter_condition: Optional[str] = None,
        priority: FlowPriority = FlowPriority.NORMAL,
        **kwargs
    ) -> str:
        """Create a new flow rule"""
        rule_id = str(uuid.uuid4())

        rule = FlowRule(
            id=rule_id,
            name=name,
            source_pattern=source_pattern,
            destination=destination,
            transformation=transformation,
            filter_condition=filter_condition,
            priority=priority,
            **kwargs
        )

        self.flow_rules[rule_id] = rule
        await self._save_flow_rules()

        # Update routing table
        self._update_routing_table()

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("flow.rule.created", {
                "rule_id": rule_id,
                "name": name,
                "source_pattern": source_pattern,
                "destination": destination
            })

        self.logger.info(f"Created flow rule: {name} ({rule_id})")
        return rule_id

    async def create_stream(
        self,
        name: str,
        source: str,
        data_type: DataType,
        buffer_size: int = 1000
    ) -> str:
        """Create a new data stream"""
        stream_id = str(uuid.uuid4())

        stream = DataStream(
            id=stream_id,
            name=name,
            source=source,
            data_type=data_type,
            buffer_size=buffer_size
        )

        self.data_streams[name] = stream
        self.flow_metrics['active_streams'] += 1

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("data.stream.created", {
                "stream_id": stream_id,
                "name": name,
                "source": source,
                "data_type": data_type.value
            })

        self.logger.info(f"Created data stream: {name} ({stream_id})")
        return stream_id

    async def _process_data_flows(self):
        """Main data processing loop"""
        self.logger.info("Starting data flow processing...")

        while self.running:
            try:
                # Process queues in priority order
                for priority in FlowPriority:
                    queue = self.priority_queues[priority]

                    # Process multiple items per priority level
                    for _ in range(min(10, queue.qsize())):
                        try:
                            packet = queue.get_nowait()
                            await self._process_packet(packet)
                        except asyncio.QueueEmpty:
                            break

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                self.logger.error(f"Error in data flow processing: {e}")
                await asyncio.sleep(1)

    async def _process_packet(self, packet: DataPacket):
        """Process a single data packet"""
        start_time = time.time()

        try:
            self.active_flows[packet.id] = FlowStatus.ACTIVE

            # Apply routing rules
            destinations = await self._route_packet(packet)

            # Process for each destination
            for destination in destinations:
                await self._deliver_packet(packet, destination)

            # Update metrics
            processing_time = time.time() - start_time
            self._update_processing_metrics(processing_time)

            self.active_flows[packet.id] = FlowStatus.COMPLETED

            # Publish event
            if self.event_bus:
                await self.event_bus.publish("data.packet.processed", {
                    "packet_id": packet.id,
                    "processing_time": processing_time,
                    "destinations": destinations
                })

        except Exception as e:
            self.logger.error(f"Error processing packet {packet.id}: {e}")
            self.active_flows[packet.id] = FlowStatus.FAILED
            self.flow_metrics['packets_failed'] += 1

            # Retry logic
            if packet.retry_count < packet.max_retries:
                packet.retry_count += 1
                await asyncio.sleep(packet.retry_count * 2)  # Exponential backoff
                await self.priority_queues[packet.priority].put(packet)
                self.logger.info(f"Retrying packet {packet.id} (attempt {packet.retry_count})")
            else:
                self.flow_metrics['packets_dropped'] += 1
                self.logger.error(f"Packet {packet.id} failed after {packet.max_retries} retries")

    async def _route_packet(self, packet: DataPacket) -> List[str]:
        """Route packet based on flow rules"""
        destinations = []

        # Direct destination
        if packet.destination:
            destinations.append(packet.destination)

        # Apply flow rules
        for rule in self.flow_rules.values():
            if not rule.enabled:
                continue

            if self._matches_pattern(packet.source, rule.source_pattern):
                # Check rate limit
                if rule.rate_limit and not self._check_rate_limit(rule.id, rule.rate_limit):
                    continue

                # Apply filter
                if rule.filter_condition:
                    if not self._apply_filter(packet, rule.filter_condition):
                        continue

                destinations.append(rule.destination)

        return list(set(destinations))  # Remove duplicates

    async def _deliver_packet(self, packet: DataPacket, destination: str):
        """Deliver packet to destination"""
        try:
            # Handle stream delivery
            if destination.startswith("stream:"):
                stream_name = destination[7:]  # Remove "stream:" prefix
                await self._deliver_to_stream(packet, stream_name)
                return

            # Apply transformation if needed
            transformed_packet = await self._apply_transformations(packet, destination)

            # Get destination service info
            if self.service_registry:
                service_endpoints = await self.service_registry.get_service_endpoints(destination)
                if service_endpoints:
                    endpoint = service_endpoints[0]  # Use first available endpoint
                    await self._send_to_endpoint(transformed_packet, endpoint)
                else:
                    self.logger.warning(f"No endpoints found for service: {destination}")

        except Exception as e:
            self.logger.error(f"Error delivering packet {packet.id} to {destination}: {e}")
            raise

    async def _deliver_to_stream(self, packet: DataPacket, stream_name: str):
        """Deliver packet to stream consumers"""
        if not hasattr(self, 'stream_subscriptions') or stream_name not in self.stream_subscriptions:
            return

        for subscription_id, callback in self.stream_subscriptions[stream_name].items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(packet)
                else:
                    callback(packet)
            except Exception as e:
                self.logger.error(f"Error calling stream callback {subscription_id}: {e}")

    async def _apply_transformations(self, packet: DataPacket, destination: str) -> DataPacket:
        """Apply data transformations"""
        # Find applicable transformation rules
        for rule in self.flow_rules.values():
            if rule.destination == destination and rule.transformation:
                if self._matches_pattern(packet.source, rule.source_pattern):
                    packet = await self._transform_data(packet, rule.transformation)
                    break

        return packet

    async def _transform_data(self, packet: DataPacket, transformation: str) -> DataPacket:
        """Apply data transformation"""
        if transformation not in self.transformers:
            self.logger.warning(f"Unknown transformation: {transformation}")
            return packet

        try:
            transformer = self.transformers[transformation]
            transformed_data = await self._call_transformer(packet, transformer)

            # Create new packet with transformed data
            new_packet = DataPacket(
                id=packet.id,
                data=transformed_data,
                data_type=packet.data_type,
                source=packet.source,
                destination=packet.destination,
                priority=packet.priority,
                timestamp=packet.timestamp,
                metadata={**packet.metadata, "transformed": True, "transformation": transformation},
                headers=packet.headers,
                ttl=packet.ttl
            )

            self.flow_metrics['total_transformations'] += 1
            return new_packet

        except Exception as e:
            self.logger.error(f"Error applying transformation {transformation}: {e}")
            return packet

    async def _call_transformer(self, packet: DataPacket, transformer: Callable) -> Any:
        """Call transformer function"""
        if asyncio.iscoroutinefunction(transformer):
            return await transformer(packet.data, packet.metadata)
        else:
            return transformer(packet.data, packet.metadata)

    def _apply_filter(self, packet: DataPacket, filter_condition: str) -> bool:
        """Apply filter condition"""
        if filter_condition not in self.filters:
            self.logger.warning(f"Unknown filter: {filter_condition}")
            return True

        try:
            filter_func = self.filters[filter_condition]
            result = filter_func(packet.data, packet.metadata)
            self.flow_metrics['total_filters_applied'] += 1
            return result
        except Exception as e:
            self.logger.error(f"Error applying filter {filter_condition}: {e}")
            return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Simple pattern matching (wildcards supported)"""
        import fnmatch
        return fnmatch.fnmatch(text.lower(), pattern.lower())

    def _check_rate_limit(self, rule_id: str, limit: int) -> bool:
        """Check rate limiting"""
        current_time = time.time()
        rate_limiter = self.rate_limiters[rule_id]

        # Remove old entries (older than 1 minute)
        while rate_limiter and current_time - rate_limiter[0] > 60:
            rate_limiter.popleft()

        # Check if under limit
        return len(rate_limiter) < limit

    async def _send_to_endpoint(self, packet: DataPacket, endpoint):
        """Send packet to service endpoint"""
        # This would implement actual HTTP/protocol communication
        # For now, just log the delivery
        self.logger.debug(f"Delivering packet {packet.id} to {endpoint.host}:{endpoint.port}")

        # Update metrics
        data_size = len(str(packet.data).encode()) if isinstance(packet.data, str) else 0
        self.flow_metrics['total_bytes_transferred'] += data_size

    async def _cleanup_expired_data(self):
        """Clean up expired data packets and streams"""
        while self.running:
            try:
                current_time = time.time()

                # Clean up expired packets
                for packet_id, status in list(self.active_flows.items()):
                    # This is a simplified cleanup - would need packet TTL tracking
                    pass

                # Clean up inactive streams
                inactive_streams = [
                    name for name, stream in self.data_streams.items()
                    if current_time - stream.last_activity > 3600  # 1 hour
                ]

                for stream_name in inactive_streams:
                    del self.data_streams[stream_name]
                    self.flow_metrics['active_streams'] -= 1
                    self.logger.info(f"Cleaned up inactive stream: {stream_name}")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def _collect_metrics(self):
        """Collect and report metrics"""
        while self.running:
            try:
                # Calculate queue sizes
                queue_sizes = {
                    priority.value: queue.qsize()
                    for priority, queue in self.priority_queues.items()
                }

                metrics = {
                    'flow_metrics': self.flow_metrics,
                    'queue_sizes': queue_sizes,
                    'active_flows': len(self.active_flows),
                    'flow_rules': len(self.flow_rules),
                    'data_streams': len(self.data_streams),
                    'timestamp': time.time()
                }

                # Publish metrics
                if self.event_bus:
                    await self.event_bus.publish("data.flow.metrics", metrics)

                await asyncio.sleep(60)  # Report every minute

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)

    def _update_processing_metrics(self, processing_time: float):
        """Update processing time metrics"""
        total_packets = self.flow_metrics['packets_processed']
        if total_packets > 0:
            # Calculate exponential moving average
            alpha = 0.1  # Smoothing factor
            current_avg = self.flow_metrics['average_processing_time']
            new_avg = (alpha * processing_time) + ((1 - alpha) * current_avg)
            self.flow_metrics['average_processing_time'] = new_avg

    def _update_routing_table(self):
        """Update routing table based on flow rules"""
        self.routing_table.clear()

        for rule in self.flow_rules.values():
            if rule.enabled:
                self.routing_table[rule.source_pattern].append(rule.destination)

    def _register_default_transformers(self):
        """Register default data transformers"""
        # JSON transformer
        self.transformers['json_to_string'] = lambda data, meta: json.dumps(data) if isinstance(data, (dict, list)) else str(data)

        # Uppercase transformer
        self.transformers['uppercase'] = lambda data, meta: data.upper() if isinstance(data, str) else data

        # Timestamp transformer
        async def add_timestamp(data, meta):
            if isinstance(data, dict):
                data['processed_at'] = time.time()
            return data
        self.transformers['add_timestamp'] = add_timestamp

    def _register_default_filters(self):
        """Register default data filters"""
        # Filter out empty data
        self.filters['not_empty'] = lambda data, meta: bool(data)

        # Size filter
        self.filters['max_size_1mb'] = lambda data, meta: len(str(data).encode()) < 1024 * 1024

    async def _load_configuration(self):
        """Load flow configuration from file"""
        try:
            if await aiofiles.os.path.exists(self.flow_persistence_file):
                async with aiofiles.open(self.flow_persistence_file, 'r') as f:
                    data = json.loads(await f.read())

                # Load flow rules
                for rule_data in data.get('flow_rules', []):
                    rule = FlowRule(**rule_data)
                    self.flow_rules[rule.id] = rule

                self._update_routing_table()
                self.logger.info(f"Loaded {len(self.flow_rules)} flow rules")

        except Exception as e:
            self.logger.error(f"Error loading flow configuration: {e}")

    async def _save_flow_rules(self):
        """Save flow rules to file"""
        try:
            data = {
                'flow_rules': [
                    {
                        'id': rule.id,
                        'name': rule.name,
                        'source_pattern': rule.source_pattern,
                        'destination': rule.destination,
                        'transformation': rule.transformation,
                        'filter_condition': rule.filter_condition,
                        'priority': rule.priority.value,
                        'enabled': rule.enabled,
                        'rate_limit': rule.rate_limit,
                        'batch_size': rule.batch_size
                    }
                    for rule in self.flow_rules.values()
                ],
                'last_updated': time.time()
            }

            async with aiofiles.open(self.flow_persistence_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            self.logger.error(f"Error saving flow rules: {e}")

    def get_flow_status(self) -> Dict[str, Any]:
        """Get comprehensive flow status"""
        return {
            'metrics': self.flow_metrics,
            'active_flows': {
                status.value: sum(1 for s in self.active_flows.values() if s == status)
                for status in FlowStatus
            },
            'flow_rules': len(self.flow_rules),
            'data_streams': len(self.data_streams),
            'queue_sizes': {
                priority.value: queue.qsize()
                for priority, queue in self.priority_queues.items()
            },
            'routing_entries': sum(len(routes) for routes in self.routing_table.values()),
            'transformers': len(self.transformers),
            'filters': len(self.filters)
        }

    async def shutdown(self):
        """Shutdown the data flow manager"""
        self.logger.info("Shutting down Data Flow Manager...")

        self.running = False

        # Cancel background tasks
        if self.processor_task:
            self.processor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()

        # Wait for tasks to complete
        tasks = [t for t in [self.processor_task, self.cleanup_task, self.metrics_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Save flow rules
        await self._save_flow_rules()

        self.logger.info("Data Flow Manager shutdown complete")