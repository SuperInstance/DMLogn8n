"""
Advanced Asynchronous Programming Patterns
Cutting-edge async implementation with coroutines, streams,
backpressure handling, and reactive programming patterns.

This module implements:
- Advanced coroutine patterns and scheduling
- Stream processing with backpressure control
- Reactive programming with observables
- Async context managers and resources
- Concurrent execution with coordination
- Rate limiting and throttling mechanisms
- Async generator pipelines
- Event-driven architectures with pub/sub
"""

import asyncio
import time
import queue
import heapq
import weakref
import inspect
from abc import ABC, abstractmethod
from typing import (
    Dict, List, Optional, Any, Callable, Union,
    TypeVar, Generic, AsyncGenerator, Awaitable,
    Iterator, Tuple, Set, AsyncContextManager,
    Protocol, runtime_checkable
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog
from concurrent.futures import ThreadPoolExecutor
import prometheus_client as prom
from contextlib import asynccontextmanager
import random

# Configure structured logging
logger = structlog.get_logger()

# Type variables
T = TypeVar('T')
U = TypeVar('U')
R = TypeVar('R')

class BackpressureStrategy(Enum):
    """Backpressure handling strategies"""
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    BUFFER = "buffer"
    BLOCK = "block"
    THROTTLE = "throttle"
    EXPONENTIAL_BACKOFF = "exponential_backoff"

class SchedulerType(Enum):
    """Coroutine scheduler types"""
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    FAIR = "fair"
    LOTTERY = "lottery"
    REALTIME = "realtime"

@dataclass
class TaskMetrics:
    """Task execution metrics"""
    task_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    wait_time: float = 0.0
    retry_count: int = 0
    priority: int = 0
    status: str = "pending"

@dataclass
class StreamMetrics:
    """Stream processing metrics"""
    items_processed: int = 0
    items_dropped: int = 0
    buffer_size: int = 0
    processing_rate: float = 0.0
    backpressure_events: int = 0
    average_latency: float = 0.0

class AsyncSemaphore:
    """Enhanced async semaphore with metrics and fairness"""

    def __init__(self, value: int, fair: bool = True):
        self._value = value
        self._waiters: List[asyncio.Future] = []
        self._fair = fair
        self._acquired_count = 0
        self._total_requests = 0

        # Metrics
        self.semaphore_acquires = prom.Counter('async_semaphore_acquires_total',
                                              'Semaphore acquires', ['status'])
        self.semaphore_queue_size = prom.Gauge('async_semaphore_queue_size',
                                              'Current semaphore queue size')

    async def acquire(self) -> bool:
        """Acquire semaphore"""
        self._total_requests += 1
        self.semaphore_queue_size.set(len(self._waiters))

        if self._value > 0:
            self._value -= 1
            self._acquired_count += 1
            self.semaphore_acquires.labels(status='immediate').inc()
            return True

        if self._fair:
            # Fair scheduling: FIFO queue
            fut = asyncio.Future()
            self._waiters.append(fut)
        else:
            # Unfair: create future and insert randomly
            fut = asyncio.Future()
            insert_pos = random.randint(0, len(self._waiters))
            self._waiters.insert(insert_pos, fut)

        try:
            await fut
            self._acquired_count += 1
            self.semaphore_acquires.labels(status='queued').inc()
            return True
        finally:
            self.semaphore_queue_size.set(len(self._waiters))

    def release(self):
        """Release semaphore"""
        if self._waiters:
            # Wake up next waiter
            waiter = self._waiters.pop(0)
            waiter.set_result(True)
        else:
            self._value += 1

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __len__(self):
        return self._value

class BackpressureController:
    """Advanced backpressure controller with multiple strategies"""

    def __init__(self, max_buffer_size: int = 1000,
                 strategy: BackpressureStrategy = BackpressureStrategy.BUFFER):
        self.max_buffer_size = max_buffer_size
        self.strategy = strategy
        self.buffer: deque = deque(maxlen=max_buffer_size)
        self.metrics = StreamMetrics()
        self.dropped_items: deque = deque(maxlen=1000)
        self.throttle_delay = 0.1  # Initial throttle delay
        self.backpressure_active = False

        # Metrics
        self.backpressure_active_gauge = prom.Gauge('backpressure_active',
                                                   'Backpressure active status')
        self.buffer_size_gauge = prom.Gauge('backpressure_buffer_size',
                                           'Backpressure buffer size')

    async def add_item(self, item: Any) -> bool:
        """Add item with backpressure control"""
        self.metrics.buffer_size = len(self.buffer)
        self.buffer_size_gauge.set(self.metrics.buffer_size)

        # Check if backpressure should be applied
        if len(self.buffer) >= self.max_buffer_size * 0.8:
            self.backpressure_active = True
            self.metrics.backpressure_events += 1
            self.backpressure_active_gauge.set(1)

        if self.strategy == BackpressureStrategy.DROP_OLDEST:
            return await self._handle_drop_oldest(item)
        elif self.strategy == BackpressureStrategy.DROP_NEWEST:
            return await self._handle_drop_newest(item)
        elif self.strategy == BackpressureStrategy.BUFFER:
            return await self._handle_buffer(item)
        elif self.strategy == BackpressureStrategy.BLOCK:
            return await self._handle_block(item)
        elif self.strategy == BackpressureStrategy.THROTTLE:
            return await self._handle_throttle(item)
        elif self.strategy == BackpressureStrategy.EXPONENTIAL_BACKOFF:
            return await self._handle_exponential_backoff(item)
        else:
            return await self._handle_buffer(item)

    async def get_item(self) -> Optional[Any]:
        """Get item from buffer"""
        if not self.buffer:
            return None

        item = self.buffer.popleft()
        self.metrics.items_processed += 1
        self.metrics.buffer_size = len(self.buffer)
        self.buffer_size_gauge.set(self.metrics.buffer_size)

        # Reset backpressure if buffer is getting empty
        if len(self.buffer) < self.max_buffer_size * 0.3:
            self.backpressure_active = False
            self.backpressure_active_gauge.set(0)

        return item

    async def _handle_drop_oldest(self, item: Any) -> bool:
        """Drop oldest item strategy"""
        if len(self.buffer) >= self.max_buffer_size:
            dropped = self.buffer.popleft()
            self.dropped_items.append(dropped)
            self.metrics.items_dropped += 1

        self.buffer.append(item)
        return True

    async def _handle_drop_newest(self, item: Any) -> bool:
        """Drop newest item strategy"""
        if len(self.buffer) >= self.max_buffer_size:
            self.metrics.items_dropped += 1
            return False  # Drop the new item

        self.buffer.append(item)
        return True

    async def _handle_buffer(self, item: Any) -> bool:
        """Buffer strategy with overflow handling"""
        try:
            self.buffer.append(item)
            return True
        except IndexError:
            # Buffer full
            self.metrics.items_dropped += 1
            return False

    async def _handle_block(self, item: Any) -> bool:
        """Block strategy - wait for space"""
        while len(self.buffer) >= self.max_buffer_size:
            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

        self.buffer.append(item)
        return True

    async def _handle_throttle(self, item: Any) -> bool:
        """Throttle strategy - delay addition"""
        if self.backpressure_active:
            await asyncio.sleep(self.throttle_delay)
            # Increase throttle delay
            self.throttle_delay = min(self.throttle_delay * 1.1, 1.0)
        else:
            # Decrease throttle delay
            self.throttle_delay = max(self.throttle_delay * 0.9, 0.01)

        return await self._handle_buffer(item)

    async def _handle_exponential_backoff(self, item: Any) -> bool:
        """Exponential backoff strategy"""
        if self.backpressure_active:
            # Exponential backoff
            delay = min(0.1 * (2 ** len(self.buffer) / self.max_buffer_size), 5.0)
            await asyncio.sleep(delay)

        return await self._handle_buffer(item)

class AsyncStream(Generic[T]):
    """Advanced async stream with processing pipeline"""

    def __init__(self, source: AsyncGenerator[T, None],
                 backpressure: Optional[BackpressureController] = None):
        self.source = source
        self.backpressure = backpressure or BackpressureController()
        self.transformers: List[Callable[[T], Awaitable[U]]] = []
        self.filters: List[Callable[[T], bool]] = []
        self.buffer_size = 100
        self.metrics = StreamMetrics()
        self.running = False
        self.processing_task: Optional[asyncio.Task] = None

    def map(self, func: Callable[[T], Awaitable[U]]) -> 'AsyncStream[U]':
        """Apply async transformation function"""
        new_stream = AsyncStream(self.source, self.backpressure)
        new_stream.transformers = self.transformers + [func]
        new_stream.filters = self.filters
        return new_stream

    def filter(self, predicate: Callable[[T], bool]) -> 'AsyncStream[T]':
        """Apply filter function"""
        new_stream = AsyncStream(self.source, self.backpressure)
        new_stream.transformers = self.transformers
        new_stream.filters = self.filters + [predicate]
        return new_stream

    def buffer(self, size: int) -> 'AsyncStream[List[T]]':
        """Buffer items into batches"""
        async def buffer_transformer(items: List[T]) -> List[List[T]]:
            # Split into chunks of size
            chunks = [items[i:i + size] for i in range(0, len(items), size)]
            return chunks

        return self.map(buffer_transformer)

    def throttle(self, rate: float) -> 'AsyncStream[T]':
        """Throttle stream to specified rate (items per second)"""
        async def throttler(item: T) -> T:
            await asyncio.sleep(1.0 / rate)
            return item

        return self.map(throttler)

    async def consume(self, consumer: Callable[[T], Awaitable[None]]) -> None:
        """Consume stream with provided consumer function"""
        async for item in self:
            await consumer(item)

    async def collect(self, limit: Optional[int] = None) -> List[T]:
        """Collect items from stream"""
        items = []
        count = 0

        async for item in self:
            items.append(item)
            count += 1
            if limit and count >= limit:
                break

        return items

    async def start_processing(self) -> None:
        """Start background processing"""
        if self.running:
            return

        self.running = True
        self.processing_task = asyncio.create_task(self._process_stream())

    async def stop_processing(self) -> None:
        """Stop background processing"""
        self.running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

    async def _process_stream(self):
        """Internal stream processing loop"""
        try:
            async for item in self.source:
                if not self.running:
                    break

                # Apply filters
                if not all(predicate(item) for predicate in self.filters):
                    continue

                # Apply transformers
                processed_item = item
                for transformer in self.transformers:
                    processed_item = await transformer(processed_item)

                # Add to backpressure controller
                await self.backpressure.add_item(processed_item)

        except Exception as e:
            logger.error("Stream processing error", error=str(e))

    def __aiter__(self) -> AsyncGenerator[T, None]:
        """Async iterator interface"""
        return self._stream_generator()

    async def _stream_generator(self) -> AsyncGenerator[T, None]:
        """Generate items from stream"""
        while self.running or len(self.backpressure.buffer) > 0:
            item = await self.backpressure.get_item()
            if item is not None:
                yield item
            else:
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

class Observable(Generic[T]):
    """Reactive programming observable implementation"""

    def __init__(self):
        self.observers: List['Observer[T]'] = []
        self.is_completed = False
        self.error: Optional[Exception] = None
        self.last_value: Optional[T] = None

    def subscribe(self, observer: 'Observer[T]') -> 'Subscription':
        """Subscribe observer to observable"""
        self.observers.append(observer)

        # Send last value if available (hot observable behavior)
        if self.last_value is not None:
            observer.on_next(self.last_value)

        if self.is_completed:
            observer.on_completed()
        elif self.error:
            observer.on_error(self.error)

        return Subscription(self, observer)

    async def next(self, value: T):
        """Emit next value"""
        self.last_value = value

        for observer in self.observers[:]:  # Copy list to avoid modification during iteration
            try:
                if inspect.iscoroutinefunction(observer.on_next):
                    await observer.on_next(value)
                else:
                    observer.on_next(value)
            except Exception as e:
                logger.error("Observer error", error=str(e))

    async def error(self, error: Exception):
        """Emit error"""
        self.error = error
        self.is_completed = True

        for observer in self.observers[:]:
            try:
                if inspect.iscoroutinefunction(observer.on_error):
                    await observer.on_error(error)
                else:
                    observer.on_error(error)
            except Exception as e:
                logger.error("Observer error handling", error=str(e))

    async def complete(self):
        """Complete observable"""
        self.is_completed = True

        for observer in self.observers[:]:
            try:
                if inspect.iscoroutinefunction(observer.on_completed):
                    await observer.on_completed()
                else:
                    observer.on_completed()
            except Exception as e:
                logger.error("Observer completion error", error=str(e))

    def map(self, func: Callable[[T], U]) -> 'Observable[U]':
        """Map observable values"""
        mapped = Observable[U]()

        async def observer_wrapper(value: T):
            try:
                mapped_value = func(value)
                await mapped.next(mapped_value)
            except Exception as e:
                await mapped.error(e)

        self.subscribe(Observer(on_next=observer_wrapper))
        return mapped

    def filter(self, predicate: Callable[[T], bool]) -> 'Observable[T]':
        """Filter observable values"""
        filtered = Observable[T]()

        async def observer_wrapper(value: T):
            try:
                if predicate(value):
                    await filtered.next(value)
            except Exception as e:
                await filtered.error(e)

        self.subscribe(Observer(on_next=observer_wrapper))
        return filtered

    def throttle(self, duration: float) -> 'Observable[T]':
        """Throttle observable emissions"""
        throttled = Observable[T]()
        last_emission = 0

        async def observer_wrapper(value: T):
            nonlocal last_emission
            now = time.time()
            if now - last_emission >= duration:
                last_emission = now
                await throttled.next(value)

        self.subscribe(Observer(on_next=observer_wrapper))
        return throttled

class Observer(Generic[T]):
    """Observer for reactive programming"""

    def __init__(self,
                 on_next: Optional[Callable[[T], Union[None, Awaitable[None]]]] = None,
                 on_error: Optional[Callable[[Exception], Union[None, Awaitable[None]]]] = None,
                 on_completed: Optional[Callable[[], Union[None, Awaitable[None]]]] = None):
        self.on_next = on_next or (lambda x: None)
        self.on_error = on_error or (lambda e: None)
        self.on_completed = on_completed or (lambda: None)

class Subscription:
    """Subscription handle for observable"""

    def __init__(self, observable: Observable, observer: Observer):
        self.observable = observable
        self.observer = observer
        self.is_subscribed = True

    def unsubscribe(self):
        """Unsubscribe from observable"""
        if self.is_subscribed and self.observer in self.observable.observers:
            self.observable.observers.remove(self.observer)
        self.is_subscribed = False

class CoroutineScheduler:
    """Advanced coroutine scheduler with multiple strategies"""

    def __init__(self, scheduler_type: SchedulerType = SchedulerType.FAIR,
                 max_workers: int = 100):
        self.scheduler_type = scheduler_type
        self.max_workers = max_workers
        self.task_queue: List[Tuple[int, asyncio.Task, Dict[str, Any]]] = []
        self.running_tasks: Set[asyncio.Task] = set()
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False

        # Metrics
        self.scheduler_tasks_submitted = prom.Counter('scheduler_tasks_submitted_total',
                                                     'Tasks submitted to scheduler')
        self.scheduler_tasks_completed = prom.Counter('scheduler_tasks_completed_total',
                                                     'Tasks completed by scheduler')
        self.scheduler_active_tasks = prom.Gauge('scheduler_active_tasks',
                                               'Currently active tasks')

    async def start(self):
        """Start scheduler"""
        self.running = True
        asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop scheduler"""
        self.running = False
        self.executor.shutdown(wait=True)

    async def submit(self, coro: Awaitable[T],
                    priority: int = 0,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit coroutine to scheduler"""
        task_id = str(uuid.uuid4())
        metrics = TaskMetrics(
            task_id=task_id,
            created_at=datetime.utcnow(),
            priority=priority
        )
        self.task_metrics[task_id] = metrics

        if self.scheduler_type == SchedulerType.PRIORITY:
            # Priority queue
            heapq.heappush(self.task_queue, (-priority, asyncio.create_task(coro), metadata or {}))
        elif self.scheduler_type == SchedulerType.ROUND_ROBIN:
            # Round-robin
            self.task_queue.append((priority, asyncio.create_task(coro), metadata or {}))
        else:
            # Default to priority
            heapq.heappush(self.task_queue, (-priority, asyncio.create_task(coro), metadata or {}))

        self.scheduler_tasks_submitted.inc()
        return task_id

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Clean up completed tasks
                completed_tasks = [task for task in self.running_tasks if task.done()]
                for task in completed_tasks:
                    self.running_tasks.remove(task)
                    self.scheduler_tasks_completed.inc()

                # Check if we can schedule more tasks
                if len(self.running_tasks) < self.max_workers and self.task_queue:
                    if self.scheduler_type in [SchedulerType.PRIORITY, SchedulerType.ROUND_ROBIN]:
                        priority, task, metadata = heapq.heappop(self.task_queue) if self.scheduler_type == SchedulerType.PRIORITY else self.task_queue.pop(0)
                    else:
                        # Fair scheduling
                        _, task, metadata = self.task_queue.pop(0)

                    # Update task metrics
                    task_id = metadata.get('task_id')
                    if task_id and task_id in self.task_metrics:
                        self.task_metrics[task_id].started_at = datetime.utcnow()

                    # Add to running tasks
                    self.running_tasks.add(task)

                    # Schedule task completion
                    task.add_done_callback(lambda t: self._task_completed(t, metadata))

                self.scheduler_active_tasks.set(len(self.running_tasks))
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error("Scheduler loop error", error=str(e))
                await asyncio.sleep(0.1)

    def _task_completed(self, task: asyncio.Task, metadata: Dict[str, Any]):
        """Handle task completion"""
        task_id = metadata.get('task_id')
        if task_id and task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            metrics.completed_at = datetime.utcnow()
            metrics.execution_time = (metrics.completed_at - metrics.started_at).total_seconds()
            metrics.status = "completed" if not task.exception() else "failed"

            if task.exception():
                logger.error("Scheduled task failed",
                           task_id=task_id,
                           error=str(task.exception()))

class AsyncResourceManager:
    """Async resource manager with pooling and lifecycle management"""

    def __init__(self, factory: Callable[[], AsyncContextManager[T]],
                 max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self.available: List[T] = []
        self.in_use: Set[T] = set()
        self.semaphore = asyncio.Semaphore(max_size)
        self.waiters: List[asyncio.Future] = []

    async def acquire(self) -> T:
        """Acquire resource from pool"""
        await self.semaphore.acquire()

        if self.available:
            resource = self.available.pop()
        else:
            # Create new resource
            resource_cm = self.factory()
            resource = await resource_cm.__aenter__()

        self.in_use.add(resource)
        return resource

    async def release(self, resource: T):
        """Release resource back to pool"""
        if resource in self.in_use:
            self.in_use.remove(resource)
            self.available.append(resource)
            self.semaphore.release()

            # Notify waiters
            if self.waiters:
                waiter = self.waiters.pop(0)
                waiter.set_result(True)

    async def cleanup(self):
        """Cleanup all resources"""
        # Close all available resources
        for resource in self.available:
            try:
                await self._close_resource(resource)
            except Exception as e:
                logger.error("Resource cleanup error", error=str(e))

        # Wait for in-use resources to be returned
        while self.in_use:
            await asyncio.sleep(0.1)

    async def _close_resource(self, resource: T):
        """Close individual resource"""
        # This would depend on the specific resource type
        if hasattr(resource, 'close'):
            await resource.close()
        elif hasattr(resource, 'aclose'):
            await resource.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

class AsyncEventBus:
    """Advanced async event bus with pub/sub and routing"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.wildcard_subscribers: List[Callable] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing = False
        self.metrics = defaultdict(int)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to specific event type"""
        self.subscribers[event_type].append(handler)

    def subscribe_wildcard(self, handler: Callable) -> None:
        """Subscribe to all events"""
        self.wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish event"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow(),
            'id': str(uuid.uuid4())
        }

        await self.event_queue.put(event)
        self.metrics[f'events_published_{event_type}'] += 1

    async def start_processing(self) -> None:
        """Start event processing"""
        if not self.processing:
            self.processing = True
            asyncio.create_task(self._process_events())

    async def stop_processing(self) -> None:
        """Stop event processing"""
        self.processing = False

    async def _process_events(self) -> None:
        """Process events from queue"""
        while self.processing:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                await self._handle_event(event)
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Event processing error", error=str(e))

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle single event"""
        event_type = event['type']
        handlers = self.subscribers.get(event_type, [])
        all_handlers = handlers + self.wildcard_subscribers

        # Execute all handlers concurrently
        tasks = []
        for handler in all_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    task = asyncio.create_task(handler(event))
                else:
                    task = asyncio.create_task(asyncio.to_thread(handler, event))
                tasks.append(task)
            except Exception as e:
                logger.error("Event handler error", event_type=event_type, error=str(e))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.metrics[f'events_processed_{event_type}'] += 1

class RateLimiter:
    """Advanced rate limiter with multiple algorithms"""

    def __init__(self, max_requests: int, time_window: float,
                 algorithm: str = "token_bucket"):
        self.max_requests = max_requests
        self.time_window = time_window
        self.algorithm = algorithm

        if algorithm == "token_bucket":
            self.tokens = max_requests
            self.last_refill = time.time()
            self.token_lock = asyncio.Lock()
        elif algorithm == "sliding_window":
            self.requests = deque()
        elif algorithm == "fixed_window":
            self.request_count = 0
            self.window_start = time.time()
            self.window_lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire permission to proceed"""
        if self.algorithm == "token_bucket":
            return await self._token_bucket_acquire(tokens)
        elif self.algorithm == "sliding_window":
            return await self._sliding_window_acquire()
        elif self.algorithm == "fixed_window":
            return await self._fixed_window_acquire()
        return True

    async def _token_bucket_acquire(self, tokens: int) -> bool:
        """Token bucket algorithm"""
        async with self.token_lock:
            now = time.time()
            elapsed = now - self.last_refill

            # Refill tokens
            refill_rate = self.max_requests / self.time_window
            self.tokens = min(self.max_requests, self.tokens + elapsed * refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def _sliding_window_acquire(self) -> bool:
        """Sliding window algorithm"""
        now = time.time()
        cutoff = now - self.time_window

        # Remove old requests
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    async def _fixed_window_acquire(self) -> bool:
        """Fixed window algorithm"""
        async with self.window_lock:
            now = time.time()
            elapsed = now - self.window_start

            if elapsed >= self.time_window:
                # Reset window
                self.request_count = 0
                self.window_start = now

            if self.request_count < self.max_requests:
                self.request_count += 1
                return True
            return False

# Initialize async patterns system
async def initialize_async_system() -> Dict[str, Any]:
    """Initialize complete async patterns architecture"""

    # Initialize scheduler
    scheduler = CoroutineScheduler(scheduler_type=SchedulerType.FAIR)
    await scheduler.start()

    # Initialize event bus
    event_bus = AsyncEventBus()
    await event_bus.start_processing()

    logger.info("Async patterns system initialized")

    return {
        "scheduler": scheduler,
        "event_bus": event_bus
    }

# Export main classes and functions
__all__ = [
    'AsyncSemaphore',
    'BackpressureController',
    'AsyncStream',
    'Observable',
    'Observer',
    'Subscription',
    'CoroutineScheduler',
    'AsyncResourceManager',
    'AsyncEventBus',
    'RateLimiter',
    'BackpressureStrategy',
    'SchedulerType',
    'initialize_async_system'
]