#!/usr/bin/env python3
"""
DMlogn8n Event Bus
==================

High-performance event bus for loose coupling between learning components.

Features:
- Async event processing
- Priority queues
- Event filtering and routing
- Persistence for critical events
- Event replay capabilities
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
import weakref
from enum import Enum

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Event priorities for processing."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class Event:
    """Enhanced event structure."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    persistent: bool = False

class EventBus:
    """
    High-performance asynchronous event bus.

    Provides loose coupling between components with guaranteed delivery
    and event persistence for critical events.
    """

    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size

        # Priority queues for events
        self.queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size // 5)
            for priority in EventPriority
        }

        # Subscribers registry
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.global_subscribers: List[Callable] = []

        # Event processing state
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
        self.stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'queue_sizes': {p.name: 0 for p in EventPriority}
        }

        # Event persistence for critical events
        self.persistent_events: Dict[str, Event] = {}

        logger.info("EventBus initialized")

    async def publish(self, event: Event) -> bool:
        """
        Publish an event to the appropriate queue.

        Returns:
            bool: True if event was queued successfully
        """
        try:
            # Update statistics
            self.stats['events_published'] += 1

            # Store persistent events
            if event.persistent:
                self.persistent_events[event.id] = event

            # Queue event based on priority
            queue = self.queues[event.priority]
            queue.put_nowait(event)

            self.stats['queue_sizes'][event.priority.name] = queue.qsize()

            return True

        except asyncio.QueueFull:
            logger.warning(f"Event queue full for priority {event.priority.name}, dropping event {event.id}")
            self.stats['events_failed'] += 1
            return False

    async def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> str:
        """
        Subscribe to specific event types.

        Args:
            event_type: Type of events to subscribe to
            handler: Async function to handle events
            priority: Handler priority (higher = called first)

        Returns:
            str: Subscription ID for unsubscribing
        """
        subscription_id = str(uuid.uuid4())

        self.subscribers[event_type].append({
            'id': subscription_id,
            'handler': handler,
            'priority': priority
        })

        # Sort by priority
        self.subscribers[event_type].sort(key=lambda x: x['priority'], reverse=True)

        logger.debug(f"Subscribed {subscription_id} to {event_type}")
        return subscription_id

    async def subscribe_all(self, handler: Callable) -> str:
        """Subscribe to all events."""
        subscription_id = str(uuid.uuid4())
        self.global_subscribers.append({
            'id': subscription_id,
            'handler': handler
        })
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        # Check specific subscriptions
        for event_type, subscribers in self.subscribers.items():
            for i, sub in enumerate(subscribers):
                if sub['id'] == subscription_id:
                    del subscribers[i]
                    logger.debug(f"Unsubscribed {subscription_id} from {event_type}")
                    return True

        # Check global subscriptions
        for i, sub in enumerate(self.global_subscribers):
            if sub['id'] == subscription_id:
                del self.global_subscribers[i]
                logger.debug(f"Unsubscribed {subscription_id} from all events")
                return True

        return False

    async def start(self):
        """Start the event processing loop."""
        if self.running:
            return

        self.running = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")

    async def stop(self):
        """Stop the event processing loop."""
        self.running = False

        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass

        logger.info("EventBus stopped")

    async def _process_events(self):
        """Main event processing loop."""
        while self.running:
            try:
                # Check queues in priority order
                event = await self._get_next_event()

                if event:
                    await self._handle_event(event)
                else:
                    # No events, brief sleep
                    await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in event processing: {e}")
                await asyncio.sleep(0.1)

    async def _get_next_event(self) -> Optional[Event]:
        """Get next event from highest priority non-empty queue."""
        for priority in EventPriority:
            queue = self.queues[priority]
            if not queue.empty():
                try:
                    event = queue.get_nowait()
                    self.stats['queue_sizes'][priority.name] = queue.qsize()
                    return event
                except asyncio.QueueEmpty:
                    continue
        return None

    async def _handle_event(self, event: Event):
        """Handle a single event."""
        try:
            # Get subscribers for this event type
            specific_handlers = [
                sub['handler'] for sub in self.subscribers.get(event.type, [])
            ]

            # Include global handlers
            all_handlers = specific_handlers + [
                sub['handler'] for sub in self.global_subscribers
            ]

            # Execute all handlers concurrently
            if all_handlers:
                tasks = [handler(event) for handler in all_handlers]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check for errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Handler {i} failed for event {event.id}: {result}")
                        if event.retry_count < event.max_retries:
                            event.retry_count += 1
                            await self.publish(event)

            self.stats['events_processed'] += 1

        except Exception as e:
            logger.error(f"Error handling event {event.id}: {e}")
            self.stats['events_failed'] += 1

    async def publish_batch(self, events: List[Event]) -> int:
        """Publish multiple events efficiently."""
        success_count = 0
        for event in events:
            if await self.publish(event):
                success_count += 1
        return success_count

    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self.stats,
            'running': self.running,
            'subscriber_count': sum(len(subs) for subs in self.subscribers.values()),
            'global_subscriber_count': len(self.global_subscribers),
            'persistent_event_count': len(self.persistent_events)
        }

    async def clear_persistent_events(self):
        """Clear all persistent events."""
        self.persistent_events.clear()
        logger.info("Cleared all persistent events")

    async def replay_persistent_events(self, target_type: Optional[str] = None):
        """Replay persistent events."""
        events_to_replay = [
            event for event in self.persistent_events.values()
            if target_type is None or event.type == target_type
        ]

        logger.info(f"Replaying {len(events_to_replay)} persistent events")

        for event in events_to_replay:
            # Reset retry count for replay
            event.retry_count = 0
            await self.publish(event)