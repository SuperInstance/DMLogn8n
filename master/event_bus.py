#!/usr/bin/env python3
"""
DMLogn8n Event Bus - Central Event System
High-performance event-driven communication for all components
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import aiofiles
import weakref
from pathlib import Path
import threading
from collections import defaultdict, deque

class EventType(Enum):
    SYSTEM = "system"
    SERVICE = "service"
    WORKFLOW = "workflow"
    DATA = "data"
    USER = "user"
    HEALTH = "health"
    ERROR = "error"
    METRICS = "metrics"

class EventPriority(Enum):
    CRITICAL = 1    # System failures, security alerts
    HIGH = 2        # Service state changes, user actions
    NORMAL = 3      # Workflow events, data processing
    LOW = 4         # Metrics, logs, debugging
    BULK = 5        # Batch operations, analytics

@dataclass
class Event:
    id: str
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    ttl: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

@dataclass
class EventSubscription:
    id: str
    event_pattern: str
    callback: Callable
    filter_func: Optional[Callable] = None
    priority: EventPriority = EventPriority.NORMAL
    async_callback: bool = True
    max_queue_size: int = 1000
    created_at: float = field(default_factory=time.time)
    events_processed: int = 0
    last_processed: Optional[float] = None

@dataclass
class EventMetrics:
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_priority: Dict[str, int] = field(default_factory=dict)
    processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    failed_events: int = 0
    dropped_events: int = 0
    active_subscriptions: int = 0
    queue_sizes: Dict[str, int] = field(default_factory=dict)

class EventBus:
    """
    High-performance event bus with subscription management and filtering
    """

    def __init__(self, persistence_file: str = None):
        self.persistence_file = persistence_file or "/home/activeloguser/DMLogn8n/data/event_bus.json"
        self.logger = logging.getLogger('EventBus')

        # Core storage
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_history: deque = deque(maxlen=10000)  # Keep last 10K events
        self.dead_letter_queue: deque = deque(maxlen=1000)

        # Performance tracking
        self.metrics = EventMetrics()

        # Processing queues by priority
        self.queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }

        # Pattern matching cache
        self.pattern_cache: Dict[str, Set[str]] = {}

        # Background tasks
        self.processor_tasks: List[asyncio.Task] = []
        self.persistence_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Event correlation tracking
        self.correlation_contexts: Dict[str, Dict[str, Any]] = {}

        # Shutdown flag
        self.running = False

        # Thread safety
        self._subscription_lock = asyncio.Lock()
        self._event_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the event bus"""
        self.logger.info("Initializing Event Bus...")

        # Ensure data directory exists
        await aiofiles.os.makedirs(Path(self.persistence_file).parent, exist_ok=True)

        # Load persistent subscriptions
        await self._load_subscriptions()

        # Start background processors
        self.running = True
        await self._start_processors()

        self.logger.info("Event Bus initialized")

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        tags: List[str] = None,
        **kwargs
    ) -> str:
        """
        Publish an event to the bus
        """
        event_id = str(uuid.uuid4())

        # Create event
        event = Event(
            id=event_id,
            event_type=event_type,
            data=data,
            source=source,
            priority=priority,
            correlation_id=correlation_id,
            causation_id=causation_id,
            tags=set(tags or []),
            **kwargs
        )

        # Add to history
        async with self._event_lock:
            self.event_history.append(event)

        # Add to appropriate priority queue
        await self.queues[priority].put(event)

        # Update metrics
        self._update_event_metrics(event)

        # Handle correlation context
        if correlation_id:
            await self._update_correlation_context(correlation_id, event)

        self.logger.debug(f"Published event: {event_type} ({event_id}) from {source}")
        return event_id

    async def subscribe(
        self,
        event_pattern: str,
        callback: Callable,
        filter_func: Optional[Callable] = None,
        priority: EventPriority = EventPriority.NORMAL,
        max_queue_size: int = 1000,
        **kwargs
    ) -> str:
        """
        Subscribe to events matching a pattern
        """
        subscription_id = str(uuid.uuid4())

        # Check if callback is async
        async_callback = asyncio.iscoroutinefunction(callback)

        subscription = EventSubscription(
            id=subscription_id,
            event_pattern=event_pattern,
            callback=callback,
            filter_func=filter_func,
            priority=priority,
            async_callback=async_callback,
            max_queue_size=max_queue_size,
            **kwargs
        )

        async with self._subscription_lock:
            self.subscriptions[subscription_id] = subscription
            self.metrics.active_subscriptions += 1

        # Clear pattern cache
        self.pattern_cache.clear()

        self.logger.info(f"Created subscription: {subscription_id} for pattern '{event_pattern}'")
        return subscription_id

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        async with self._subscription_lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                self.metrics.active_subscriptions -= 1
                self.pattern_cache.clear()
                self.logger.info(f"Removed subscription: {subscription_id}")
                return True
        return False

    async def publish_and_wait(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str,
        timeout: float = 5.0,
        **kwargs
    ) -> List[Any]:
        """
        Publish event and wait for all subscribers to process it
        """
        event_id = await self.publish(event_type, data, source, **kwargs)

        # Wait for processing
        start_time = time.time()
        processed_subscriptions = set()

        while time.time() - start_time < timeout:
            # Check which subscriptions have processed the event
            for sub_id, subscription in self.subscriptions.items():
                if sub_id not in processed_subscriptions:
                    if self._matches_pattern(event_type, subscription.event_pattern):
                        # This subscription should have received the event
                        # In a real implementation, we'd track this more precisely
                        processed_subscriptions.add(sub_id)

            if len(processed_subscriptions) > 0:
                break

            await asyncio.sleep(0.1)

        return []  # Would return results from subscribers

    async def get_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get events from history with filtering"""
        events = []

        for event in reversed(self.event_history):
            if len(events) >= limit:
                break

            if event_type and not self._matches_pattern(event.event_type, event_type):
                continue

            if source and event.source != source:
                continue

            if since and event.timestamp < since:
                continue

            events.append(event)

        return events

    async def start_correlation(
        self,
        correlation_id: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Start a new correlation context"""
        self.correlation_contexts[correlation_id] = {
            'started_at': time.time(),
            'events': [],
            'context': context or {}
        }

        # Publish correlation start event
        await self.publish(
            "correlation.started",
            {
                'correlation_id': correlation_id,
                'context': context
            },
            "event_bus"
        )

        return correlation_id

    async def end_correlation(self, correlation_id: str):
        """End a correlation context"""
        if correlation_id in self.correlation_contexts:
            context = self.correlation_contexts[correlation_id]
            context['ended_at'] = time.time()
            context['duration'] = context['ended_at'] - context['started_at']

            # Publish correlation end event
            await self.publish(
                "correlation.ended",
                {
                    'correlation_id': correlation_id,
                    'duration': context['duration'],
                    'event_count': len(context['events'])
                },
                "event_bus"
            )

            # Clean up after a delay
            asyncio.create_task(self._cleanup_correlation(correlation_id, delay=300))

    async def _start_processors(self):
        """Start background event processors"""
        # Start one processor per priority level
        for priority in EventPriority:
            task = asyncio.create_task(self._process_events(priority))
            self.processor_tasks.append(task)

        # Start background tasks
        self.persistence_task = asyncio.create_task(self._persist_events())
        self.metrics_task = asyncio.create_task(self._collect_metrics())
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data())

    async def _process_events(self, priority: EventPriority):
        """Process events for a specific priority level"""
        queue = self.queues[priority]
        self.logger.info(f"Started event processor for priority: {priority.name}")

        while self.running:
            try:
                # Get event from queue
                event = await queue.get()

                # Process event
                await self._handle_event(event)

                # Update queue metrics
                self.metrics.queue_sizes[priority.value] = queue.qsize()

            except Exception as e:
                self.logger.error(f"Error processing events for priority {priority}: {e}")
                await asyncio.sleep(1)

    async def _handle_event(self, event: Event):
        """Handle a single event"""
        start_time = time.time()

        try:
            # Get matching subscriptions
            matching_subscriptions = await self._get_matching_subscriptions(event)

            # Process each subscription
            for subscription in matching_subscriptions:
                try:
                    await self._deliver_event(event, subscription)
                    subscription.events_processed += 1
                    subscription.last_processed = time.time()
                except Exception as e:
                    self.logger.error(f"Error delivering event {event.id} to subscription {subscription.id}: {e}")
                    self.metrics.failed_events += 1

                    # Add to dead letter queue
                    self.dead_letter_queue.append({
                        'event': event,
                        'subscription_id': subscription.id,
                        'error': str(e),
                        'timestamp': time.time()
                    })

            # Update processing time metrics
            processing_time = time.time() - start_time
            self.metrics.processing_times.append(processing_time)

        except Exception as e:
            self.logger.error(f"Error handling event {event.id}: {e}")
            self.metrics.failed_events += 1

    async def _get_matching_subscriptions(self, event: Event) -> List[EventSubscription]:
        """Get subscriptions that match the event"""
        matching = []

        for subscription in self.subscriptions.values():
            if self._matches_pattern(event.event_type, subscription.event_pattern):
                # Apply filter function if present
                if subscription.filter_func:
                    try:
                        if subscription.filter_func(event):
                            matching.append(subscription)
                    except Exception as e:
                        self.logger.error(f"Error in filter function for subscription {subscription.id}: {e}")
                else:
                    matching.append(subscription)

        # Sort by priority
        matching.sort(key=lambda s: s.priority.value)
        return matching

    async def _deliver_event(self, event: Event, subscription: EventSubscription):
        """Deliver event to a subscription"""
        if subscription.async_callback:
            await subscription.callback(event)
        else:
            # Run sync callback in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, subscription.callback, event)

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern"""
        # Use cache for pattern matching
        cache_key = f"{pattern}:{event_type}"
        if cache_key in self.pattern_cache:
            return event_type in self.pattern_cache[cache_key]

        # Simple pattern matching (wildcards)
        import fnmatch
        matches = fnmatch.fnmatch(event_type, pattern)

        # Cache result
        if pattern not in self.pattern_cache:
            self.pattern_cache[pattern] = set()
        if matches:
            self.pattern_cache[pattern].add(event_type)

        return matches

    def _update_event_metrics(self, event: Event):
        """Update event metrics"""
        self.metrics.total_events += 1

        # Count by type
        if event.event_type not in self.metrics.events_by_type:
            self.metrics.events_by_type[event.event_type] = 0
        self.metrics.events_by_type[event.event_type] += 1

        # Count by priority
        priority_name = event.priority.value
        if priority_name not in self.metrics.events_by_priority:
            self.metrics.events_by_priority[priority_name] = 0
        self.metrics.events_by_priority[priority_name] += 1

    async def _update_correlation_context(self, correlation_id: str, event: Event):
        """Update correlation context with event"""
        if correlation_id in self.correlation_contexts:
            self.correlation_contexts[correlation_id]['events'].append({
                'event_id': event.id,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'source': event.source
            })

    async def _persist_events(self):
        """Periodically persist event history"""
        self.logger.info("Starting event persistence task")

        while self.running:
            try:
                # Get recent events to persist
                recent_events = list(self.event_history)[-100:]  # Last 100 events

                data = {
                    'events': [
                        {
                            'id': e.id,
                            'event_type': e.event_type,
                            'data': e.data,
                            'source': e.source,
                            'timestamp': e.timestamp,
                            'priority': e.priority.value,
                            'correlation_id': e.correlation_id,
                            'tags': list(e.tags)
                        }
                        for e in recent_events
                    ],
                    'dead_letter_events': [
                        {
                            'event': {
                                'id': e['event'].id,
                                'event_type': e['event'].event_type,
                                'timestamp': e['timestamp']
                            },
                            'subscription_id': e['subscription_id'],
                            'error': e['error']
                        }
                        for e in self.dead_letter_queue
                    ],
                    'last_updated': time.time()
                }

                async with aiofiles.open(self.persistence_file, 'w') as f:
                    await f.write(json.dumps(data, indent=2))

                await asyncio.sleep(300)  # Persist every 5 minutes

            except Exception as e:
                self.logger.error(f"Error persisting events: {e}")
                await asyncio.sleep(60)

    async def _collect_metrics(self):
        """Collect and publish metrics"""
        while self.running:
            try:
                # Calculate average processing time
                if self.metrics.processing_times:
                    avg_time = sum(self.metrics.processing_times) / len(self.metrics.processing_times)
                else:
                    avg_time = 0

                metrics_data = {
                    'total_events': self.metrics.total_events,
                    'events_by_type': dict(self.metrics.events_by_type),
                    'events_by_priority': dict(self.metrics.events_by_priority),
                    'average_processing_time': avg_time,
                    'failed_events': self.metrics.failed_events,
                    'dropped_events': self.metrics.dropped_events,
                    'active_subscriptions': self.metrics.active_subscriptions,
                    'queue_sizes': dict(self.metrics.queue_sizes),
                    'dead_letter_queue_size': len(self.dead_letter_queue),
                    'correlation_contexts': len(self.correlation_contexts),
                    'timestamp': time.time()
                }

                # Publish metrics event
                await self.publish(
                    "event_bus.metrics",
                    metrics_data,
                    "event_bus",
                    priority=EventPriority.LOW
                )

                await asyncio.sleep(60)  # Every minute

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_data(self):
        """Clean up old data"""
        while self.running:
            try:
                current_time = time.time()

                # Clean up dead letter queue (older than 1 hour)
                cutoff_time = current_time - 3600
                while (self.dead_letter_queue and
                       self.dead_letter_queue[0]['timestamp'] < cutoff_time):
                    self.dead_letter_queue.popleft()
                    self.metrics.dropped_events += 1

                # Clean up correlation contexts (older than 1 hour)
                expired_correlations = [
                    cid for cid, ctx in self.correlation_contexts.items()
                    if current_time - ctx.get('started_at', 0) > 3600
                ]

                for correlation_id in expired_correlations:
                    del self.correlation_contexts[correlation_id]

                await asyncio.sleep(300)  # Every 5 minutes

            except Exception as e:
                self.logger.error(f"Error cleaning up old data: {e}")
                await asyncio.sleep(60)

    async def _cleanup_correlation(self, correlation_id: str, delay: float = 300):
        """Clean up correlation context after delay"""
        await asyncio.sleep(delay)
        if correlation_id in self.correlation_contexts:
            del self.correlation_contexts[correlation_id]

    async def _load_subscriptions(self):
        """Load persistent subscriptions"""
        try:
            if await aiofiles.os.path.exists(self.persistence_file):
                async with aiofiles.open(self.persistence_file, 'r') as f:
                    data = json.loads(await f.read())

                # Load subscriptions would be implemented here
                # For now, we start fresh each time
                self.logger.info("Event bus persistence file found, starting fresh subscriptions")

        except Exception as e:
            self.logger.error(f"Error loading subscriptions: {e}")

    def get_bus_status(self) -> Dict[str, Any]:
        """Get comprehensive event bus status"""
        return {
            'metrics': {
                'total_events': self.metrics.total_events,
                'events_by_type': dict(self.metrics.events_by_type),
                'events_by_priority': dict(self.metrics.events_by_priority),
                'failed_events': self.metrics.failed_events,
                'dropped_events': self.metrics.dropped_events,
                'active_subscriptions': self.metrics.active_subscriptions,
                'queue_sizes': dict(self.metrics.queue_sizes)
            },
            'subscriptions': len(self.subscriptions),
            'event_history_size': len(self.event_history),
            'dead_letter_queue_size': len(self.dead_letter_queue),
            'correlation_contexts': len(self.correlation_contexts),
            'pattern_cache_size': len(self.pattern_cache),
            'processor_tasks': len(self.processor_tasks),
            'running': self.running
        }

    async def shutdown(self):
        """Shutdown the event bus"""
        self.logger.info("Shutting down Event Bus...")

        self.running = False

        # Cancel processor tasks
        for task in self.processor_tasks:
            task.cancel()

        # Cancel background tasks
        for task in [self.persistence_task, self.metrics_task, self.cleanup_task]:
            if task:
                task.cancel()

        # Wait for all tasks to complete
        all_tasks = self.processor_tasks + [t for t in [self.persistence_task, self.metrics_task, self.cleanup_task] if t]
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

        # Final persistence
        await self._persist_events()

        self.logger.info("Event Bus shutdown complete")

# Event Bus Client
class EventBusClient:
    """Client for interacting with the event bus"""

    def __init__(self, bus_url: str = "ws://localhost:6380/events"):
        self.bus_url = bus_url
        self.websocket = None
        self.subscriptions = {}

    async def connect(self):
        """Connect to the event bus"""
        import websockets
        self.websocket = await websockets.connect(self.bus_url)

    async def disconnect(self):
        """Disconnect from the event bus"""
        if self.websocket:
            await self.websocket.close()

    async def publish(self, event_type: str, data: Dict[str, Any], source: str, **kwargs):
        """Publish an event"""
        if not self.websocket:
            raise RuntimeError("Not connected to event bus")

        message = {
            'type': 'publish',
            'event_type': event_type,
            'data': data,
            'source': source,
            **kwargs
        }

        await self.websocket.send(json.dumps(message))

    async def subscribe(self, event_pattern: str, callback: Callable):
        """Subscribe to events"""
        if not self.websocket:
            raise RuntimeError("Not connected to event bus")

        subscription_id = str(uuid.uuid4())
        self.subscriptions[subscription_id] = callback

        message = {
            'type': 'subscribe',
            'subscription_id': subscription_id,
            'event_pattern': event_pattern
        }

        await self.websocket.send(json.dumps(message))
        return subscription_id

    async def listen(self):
        """Listen for events"""
        if not self.websocket:
            raise RuntimeError("Not connected to event bus")

        async for message in self.websocket:
            try:
                data = json.loads(message)
                if data['type'] == 'event':
                    subscription_id = data['subscription_id']
                    if subscription_id in self.subscriptions:
                        await self.subscriptions[subscription_id](data['event'])
            except Exception as e:
                print(f"Error processing event: {e}")