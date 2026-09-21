#!/usr/bin/env python3
"""
Advanced Request Batch Processing System
Optimizes API performance through intelligent request batching
"""

import asyncio
import time
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, TypeVar, Generic
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import uuid
import weakref
from concurrent.futures import ThreadPoolExecutor
import aioredis
import orjson
from fastapi import Request, Response, HTTPException
import numpy as np

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class BatchStrategy(Enum):
    """Batch processing strategies"""
    TIME_BASED = "time_based"
    SIZE_BASED = "size_based"
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"
    HYBRID = "hybrid"

class BatchType(Enum):
    """Types of batch operations"""
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    CACHE_OPERATION = "cache_operation"
    COMPUTATION = "computation"

class BatchPriority(Enum):
    """Batch processing priorities"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    # Batch size settings
    default_batch_size: int = 10
    max_batch_size: int = 100
    min_batch_size: int = 2

    # Timing settings
    batch_timeout_ms: int = 100  # Maximum wait time for batch
    batch_interval_ms: int = 50   # Interval for processing batches
    max_wait_time_ms: int = 1000  # Maximum time to wait for any request

    # Queue settings
    max_queue_size: int = 10000
    queue_priority_enabled: bool = True

    # Performance settings
    enable_parallel_batches: bool = True
    max_concurrent_batches: int = 5
    enable_batch_caching: bool = True
    enable_batch_compression: bool = True

    # Adaptive settings
    enable_adaptive_batching: bool = True
    adaptive_window_size: int = 100
    performance_threshold_ms: float = 50.0

    # Error handling
    enable_batch_retry: bool = True
    max_batch_retries: int = 3
    partial_success_enabled: bool = True

    # Memory management
    max_memory_mb: int = 512
    gc_batch_size: int = 50

@dataclass
class BatchItem:
    """Individual item in a batch"""
    id: str
    request_id: str
    data: Any
    callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    timeout: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Batch:
    """Batch of items to be processed together"""
    id: str
    batch_type: BatchType
    items: List[BatchItem]
    priority: BatchPriority
    strategy: BatchStrategy
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    processing_time: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def age(self) -> float:
        return time.time() - self.created_at

class BatchQueue:
    """Priority queue for batch items"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[BatchPriority, deque] = {
            priority: deque() for priority in BatchPriority
        }
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)
        self.total_items = 0

    async def put(self, item: BatchItem, priority: BatchPriority = BatchPriority.NORMAL) -> bool:
        """Add item to queue"""
        async with self.not_empty:
            if self.total_items >= self.max_size:
                return False

            self.queues[priority].append(item)
            self.total_items += 1
            self.not_empty.notify()
            return True

    async def get(self, priority: Optional[BatchPriority] = None) -> Optional[BatchItem]:
        """Get item from queue"""
        async with self.not_empty:
            while self.total_items == 0:
                await self.not_empty.wait()

            if priority:
                if self.queues[priority]:
                    item = self.queues[priority].popleft()
                    self.total_items -= 1
                    return item
            else:
                # Get highest priority item
                for p in sorted(BatchPriority, key=lambda x: x.value, reverse=True):
                    if self.queues[p]:
                        item = self.queues[p].popleft()
                        self.total_items -= 1
                        return item

            return None

    async def get_batch(self, batch_size: int, max_wait_ms: int = 50) -> List[BatchItem]:
        """Get batch of items"""
        batch = []
        start_time = time.time()
        max_wait_seconds = max_wait_ms / 1000

        while len(batch) < batch_size:
            remaining_time = max_wait_seconds - (time.time() - start_time)
            if remaining_time <= 0:
                break

            try:
                item = await asyncio.wait_for(
                    self.get(),
                    timeout=remaining_time
                )
                if item:
                    batch.append(item)
            except asyncio.TimeoutError:
                break

        return batch

    async def size(self) -> int:
        """Get queue size"""
        async with self.lock:
            return self.total_items

class BatchProcessor:
    """Advanced batch processor for optimizing API operations"""

    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.queues: Dict[BatchType, BatchQueue] = {
            batch_type: BatchQueue(self.config.max_queue_size)
            for batch_type in BatchType
        }

        # Active batches
        self.active_batches: Dict[str, Batch] = {}
        self.completed_batches: Dict[str, Batch] = {}

        # Batch processors
        self.processors: Dict[BatchType, Callable] = {}

        # Performance tracking
        self.performance_history: Dict[BatchType, List[float]] = defaultdict(list)
        self.adaptive_configs: Dict[BatchType, Dict[str, float]] = {}

        # Batching strategies
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.batch_accumulators: Dict[BatchType, List[BatchItem]] = defaultdict(list)

        # Statistics
        self.stats = {
            "total_items_processed": 0,
            "total_batches_processed": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "queue_sizes": {bt.value: 0 for bt in BatchType},
            "active_batches": 0,
            "success_rate": 0.0
        }

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.running = False

        # Thread pool for CPU-intensive batch processing
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def start(self):
        """Start batch processor"""
        self.running = True

        # Start batch processors for each type
        for batch_type in BatchType:
            processor = asyncio.create_task(self._batch_worker(batch_type))
            self.background_tasks.append(processor)

        # Start performance monitor
        monitor = asyncio.create_task(self._performance_monitor())
        self.background_tasks.append(monitor)

        # Start cleanup task
        cleanup = asyncio.create_task(self._cleanup_worker())
        self.background_tasks.append(cleanup)

    async def stop(self):
        """Stop batch processor"""
        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Shutdown executor
        self.executor.shutdown(wait=True)

    def register_processor(self, batch_type: BatchType, processor: Callable):
        """Register batch processor function"""
        self.processors[batch_type] = processor

    async def submit_item(self, item_data: Any, batch_type: BatchType,
                         priority: BatchPriority = BatchPriority.NORMAL,
                         callback: Optional[Callable] = None,
                         timeout: Optional[float] = None,
                         metadata: Dict[str, Any] = None) -> str:
        """Submit item for batch processing"""
        item_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        item = BatchItem(
            id=item_id,
            request_id=request_id,
            data=item_data,
            callback=callback,
            timeout=timeout,
            metadata=metadata or {}
        )

        # Add to appropriate queue
        queue = self.queues[batch_type]
        success = await queue.put(item, priority)

        if not success:
            raise HTTPException(status_code=503, detail="Batch queue full")

        # Trigger batch processing if needed
        await self._check_batch_ready(batch_type)

        return request_id

    async def submit_batch(self, items: List[Any], batch_type: BatchType,
                          priority: BatchPriority = BatchPriority.NORMAL,
                          callbacks: Optional[List[Callable]] = None) -> str:
        """Submit multiple items as a batch"""
        if len(items) > self.config.max_batch_size:
            raise ValueError(f"Batch size exceeds maximum: {len(items)} > {self.config.max_batch_size}")

        batch_id = str(uuid.uuid4())

        batch_items = []
        for i, item_data in enumerate(items):
            callback = callbacks[i] if callbacks and i < len(callbacks) else None

            batch_item = BatchItem(
                id=str(uuid.uuid4()),
                request_id=batch_id,
                data=item_data,
                callback=callback
            )
            batch_items.append(batch_item)

        # Create batch
        batch = Batch(
            id=batch_id,
            batch_type=batch_type,
            items=batch_items,
            priority=priority,
            strategy=BatchStrategy.SIZE_BASED
        )

        # Process batch immediately
        await self._process_batch(batch)

        return batch_id

    async def get_item_result(self, request_id: str) -> Optional[Any]:
        """Get result for a specific item request"""
        # This would need implementation to track individual results
        pass

    async def _check_batch_ready(self, batch_type: BatchType):
        """Check if batch is ready for processing"""
        queue = self.queues[batch_type]

        if self.config.enable_adaptive_batching:
            await self._adaptive_batch_check(batch_type)
        else:
            await self._standard_batch_check(batch_type)

    async def _standard_batch_check(self, batch_type: BatchType):
        """Standard batch size and timing check"""
        queue_size = await queue.size()
        optimal_batch_size = self._get_optimal_batch_size(batch_type)

        if queue_size >= optimal_batch_size:
            # Create batch immediately
            items = await queue.get_batch(optimal_batch_size)
            if items:
                await self._create_and_process_batch(items, batch_type)
        else:
            # Set timer for batch processing
            if batch_type not in self.batch_timers:
                self.batch_timers[batch_type] = asyncio.create_task(
                    self._batch_timer(batch_type)
                )

    async def _adaptive_batch_check(self, batch_type: BatchType):
        """Adaptive batch checking based on performance"""
        queue_size = await self.queues[batch_type].size()

        # Get adaptive configuration
        adaptive_config = self.adaptive_configs.get(batch_type, {})
        optimal_size = adaptive_config.get('optimal_size', self.config.default_batch_size)
        optimal_timeout = adaptive_config.get('optimal_timeout', self.config.batch_timeout_ms)

        if queue_size >= optimal_size:
            items = await self.queues[batch_type].get_batch(optimal_size)
            if items:
                await self._create_and_process_batch(items, batch_type)
        elif not self.batch_timers.get(batch_type):
            # Set adaptive timer
            self.batch_timers[batch_type] = asyncio.create_task(
                self._adaptive_batch_timer(batch_type, optimal_timeout)
            )

    async def _create_and_process_batch(self, items: List[BatchItem], batch_type: BatchType):
        """Create and process batch from items"""
        if not items:
            return

        batch_id = str(uuid.uuid4())

        # Determine priority from items
        priority_counts = defaultdict(int)
        for item in items:
            # Priority would be determined from item metadata or default
            priority_counts[BatchPriority.NORMAL] += 1

        batch_priority = max(priority_counts.keys(), key=lambda x: priority_counts[x])

        batch = Batch(
            id=batch_id,
            batch_type=batch_type,
            items=items,
            priority=batch_priority,
            strategy=BatchStrategy.SIZE_BASED
        )

        await self._process_batch(batch)

    async def _process_batch(self, batch: Batch):
        """Process a batch of items"""
        if batch.id in self.active_batches:
            return  # Already processing

        self.active_batches[batch.id] = batch
        batch.started_at = time.time()

        try:
            # Get processor for batch type
            processor = self.processors.get(batch.batch_type)
            if not processor:
                raise ValueError(f"No processor registered for batch type: {batch.batch_type}")

            # Process batch
            start_time = time.perf_counter()

            if asyncio.iscoroutinefunction(processor):
                results = await processor(batch.items)
            else:
                # Run in thread pool for CPU-intensive processing
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    self.executor,
                    processor,
                    batch.items
                )

            processing_time = time.perf_counter() - start_time
            batch.processing_time = processing_time

            # Handle results
            await self._handle_batch_results(batch, results)

            # Update performance history
            self.performance_history[batch.batch_type].append(processing_time)
            if len(self.performance_history[batch.batch_type]) > self.config.adaptive_window_size:
                self.performance_history[batch.batch_type] = self.performance_history[batch.batch_type][-self.config.adaptive_window_size:]

            # Update adaptive configuration
            if self.config.enable_adaptive_batching:
                await self._update_adaptive_config(batch.batch_type, processing_time)

            # Move to completed batches
            self.completed_batches[batch.id] = batch
            del self.active_batches[batch.id]

            # Update statistics
            self._update_stats(batch, True)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")

            # Handle batch failure
            await self._handle_batch_failure(batch, e)

            # Retry if enabled
            if self.config.enable_batch_retry and batch.retry_count < batch.max_retries:
                batch.retry_count += 1
                await asyncio.sleep(0.1 * batch.retry_count)  # Exponential backoff
                await self._process_batch(batch)
            else:
                # Move to completed batches
                self.completed_batches[batch.id] = batch
                del self.active_batches[batch.id]
                self._update_stats(batch, False)

    async def _handle_batch_results(self, batch: Batch, results: Any):
        """Handle results from batch processing"""
        batch.completed_at = time.time()

        # Call individual item callbacks
        if isinstance(results, (list, tuple)):
            for i, item in enumerate(batch.items):
                if i < len(results) and item.callback:
                    try:
                        if asyncio.iscoroutinefunction(item.callback):
                            await item.callback(results[i], None)
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                self.executor,
                                item.callback,
                                results[i],
                                None
                            )
                    except Exception as e:
                        logger.error(f"Item callback error: {e}")
        else:
            # Single result for all items
            for item in batch.items:
                if item.callback:
                    try:
                        if asyncio.iscoroutinefunction(item.callback):
                            await item.callback(results, None)
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                self.executor,
                                item.callback,
                                results,
                                None
                            )
                    except Exception as e:
                        logger.error(f"Item callback error: {e}")

    async def _handle_batch_failure(self, batch: Batch, error: Exception):
        """Handle batch processing failure"""
        batch.completed_at = time.time()

        # Call item callbacks with error
        for item in batch.items:
            if item.callback:
                try:
                    if asyncio.iscoroutinefunction(item.callback):
                        await item.callback(None, error)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            self.executor,
                            item.callback,
                            None,
                            error
                        )
                except Exception as e:
                    logger.error(f"Item error callback error: {e}")

    async def _batch_timer(self, batch_type: BatchType):
        """Timer for batch processing"""
        await asyncio.sleep(self.config.batch_timeout_ms / 1000)

        try:
            queue = self.queues[batch_type]
            items = await queue.get_batch(self.config.min_batch_size)
            if items:
                await self._create_and_process_batch(items, batch_type)
        finally:
            self.batch_timers.pop(batch_type, None)

    async def _adaptive_batch_timer(self, batch_type: BatchType, timeout_ms: int):
        """Adaptive timer for batch processing"""
        await asyncio.sleep(timeout_ms / 1000)

        try:
            queue = self.queues[batch_type]
            optimal_size = self._get_optimal_batch_size(batch_type)
            items = await queue.get_batch(optimal_size)
            if items:
                await self._create_and_process_batch(items, batch_type)
        finally:
            self.batch_timers.pop(batch_type, None)

    async def _batch_worker(self, batch_type: BatchType):
        """Background worker for processing batches"""
        while self.running:
            try:
                await self._check_batch_ready(batch_type)
                await asyncio.sleep(self.config.batch_interval_ms / 1000)
            except Exception as e:
                logger.error(f"Batch worker error for {batch_type}: {e}")

    async def _performance_monitor(self):
        """Monitor batch processing performance"""
        while self.running:
            try:
                # Update queue sizes
                for batch_type in BatchType:
                    self.stats["queue_sizes"][batch_type.value] = await self.queues[batch_type].size()

                self.stats["active_batches"] = len(self.active_batches)

                # Calculate success rate
                total_batches = len(self.completed_batches)
                if total_batches > 0:
                    successful_batches = sum(
                        1 for batch in self.completed_batches.values()
                        if batch.processing_time > 0
                    )
                    self.stats["success_rate"] = successful_batches / total_batches

                await asyncio.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"Performance monitor error: {e}")

    async def _cleanup_worker(self):
        """Cleanup old completed batches"""
        while self.running:
            try:
                current_time = time.time()
                cutoff_time = current_time - 300  # Keep last 5 minutes

                # Remove old completed batches
                to_remove = [
                    batch_id for batch_id, batch in self.completed_batches.items()
                    if batch.completed_at and batch.completed_at < cutoff_time
                ]

                for batch_id in to_remove:
                    del self.completed_batches[batch_id]

                # Keep maximum of 1000 completed batches
                if len(self.completed_batches) > 1000:
                    oldest_batches = sorted(
                        self.completed_batches.items(),
                        key=lambda x: x[1].completed_at or 0
                    )[:500]
                    for batch_id, _ in oldest_batches:
                        del self.completed_batches[batch_id]

                await asyncio.sleep(60)  # Cleanup every minute

            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")

    def _get_optimal_batch_size(self, batch_type: BatchType) -> int:
        """Get optimal batch size based on performance history"""
        if not self.config.enable_adaptive_batching:
            return self.config.default_batch_size

        history = self.performance_history.get(batch_type, [])
        if len(history) < 10:
            return self.config.default_batch_size

        # Analyze performance vs batch size
        avg_processing_time = sum(history) / len(history)

        if avg_processing_time < self.config.performance_threshold_ms / 1000:
            # Performance is good, increase batch size
            return min(self.config.max_batch_size, int(self.config.default_batch_size * 1.5))
        else:
            # Performance is poor, decrease batch size
            return max(self.config.min_batch_size, int(self.config.default_batch_size * 0.8))

    async def _update_adaptive_config(self, batch_type: BatchType, processing_time: float):
        """Update adaptive configuration based on performance"""
        if batch_type not in self.adaptive_configs:
            self.adaptive_configs[batch_type] = {}

        config = self.adaptive_configs[batch_type]
        history = self.performance_history.get(batch_type, [])

        if len(history) >= 5:
            recent_avg = sum(history[-5:]) / 5

            # Adjust optimal batch size
            current_size = config.get('optimal_size', self.config.default_batch_size)
            if recent_avg < self.config.performance_threshold_ms / 1000:
                # Good performance, increase size
                config['optimal_size'] = min(self.config.max_batch_size, current_size + 2)
            else:
                # Poor performance, decrease size
                config['optimal_size'] = max(self.config.min_batch_size, current_size - 1)

            # Adjust timeout
            current_timeout = config.get('optimal_timeout', self.config.batch_timeout_ms)
            if recent_avg < self.config.performance_threshold_ms / 1000:
                # Can wait longer for better batching
                config['optimal_timeout'] = min(500, current_timeout + 10)
            else:
                # Need faster processing
                config['optimal_timeout'] = max(10, current_timeout - 10)

    def _update_stats(self, batch: Batch, success: bool):
        """Update processing statistics"""
        self.stats["total_items_processed"] += batch.size
        self.stats["total_batches_processed"] += 1

        if success:
            total_batches = self.stats["total_batches_processed"]
            self.stats["average_batch_size"] = (
                (self.stats["average_batch_size"] * (total_batches - 1) + batch.size) / total_batches
            )
            self.stats["average_processing_time"] = (
                (self.stats["average_processing_time"] * (total_batches - 1) + batch.processing_time) / total_batches
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics"""
        return {
            **self.stats,
            "adaptive_configs": self.adaptive_configs,
            "performance_history": {
                bt.value: history[-10:]  # Last 10 entries
                for bt, history in self.performance_history.items()
            }
        }

# Built-in batch processors
class DatabaseBatchProcessor:
    """Database batch processor for read/write operations"""

    def __init__(self, db_connection):
        self.db = db_connection

    async def process_read_batch(self, items: List[BatchItem]) -> List[Any]:
        """Process database read batch"""
        query = "SELECT * FROM table WHERE id IN %s"
        ids = [item.data.get('id') for item in items]

        # Execute batch query
        result = await self.db.fetch(query, (tuple(ids),))

        # Map results back to items
        id_to_result = {row['id']: row for row in result}
        return [id_to_result.get(item.data.get('id')) for item in items]

    async def process_write_batch(self, items: List[BatchItem]) -> List[Any]:
        """Process database write batch"""
        # Batch insert/update logic
        values = [(item.data.get('id'), item.data.get('value')) for item in items]

        query = "INSERT INTO table (id, value) VALUES %s ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value"
        await self.db.executemany(query, values)

        return [True] * len(items)

class APIBatchProcessor:
    """Batch processor for external API calls"""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def process_api_batch(self, items: List[BatchItem]) -> List[Any]:
        """Process external API calls in batch"""
        # Example: Bulk API call
        urls = [item.data.get('url') for item in items]

        # Make concurrent requests
        tasks = [self.session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for response in responses:
            if isinstance(response, Exception):
                results.append(None)
            else:
                try:
                    data = await response.json()
                    results.append(data)
                except:
                    results.append(None)

        return results

# FastAPI integration
class BatchMiddleware:
    """FastAPI middleware for batch processing"""

    def __init__(self, app, processor: BatchProcessor, batch_endpoints: List[str] = None):
        self.app = app
        self.processor = processor
        self.batch_endpoints = batch_endpoints or []

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check if this is a batch endpoint
        # This would need more sophisticated implementation
        await self.app(scope, receive, send)

# Decorators for batch processing
def batch_processor(batch_type: BatchType, priority: BatchPriority = BatchPriority.NORMAL):
    """Decorator for batch processing functions"""
    def decorator(func: Callable) -> Callable:
        func._batch_metadata = {
            "batch_type": batch_type,
            "priority": priority
        }
        return func
    return decorator

if __name__ == "__main__":
    # Example usage
    async def main():
        config = BatchConfig()
        processor = BatchProcessor(config)

        # Register a database processor
        db_processor = DatabaseBatchProcessor(None)  # Would pass actual DB connection
        processor.register_processor(BatchType.DATABASE_READ, db_processor.process_read_batch)
        processor.register_processor(BatchType.DATABASE_WRITE, db_processor.process_write_batch)

        await processor.start()

        # Submit some items for batch processing
        request_ids = []
        for i in range(5):
            request_id = await processor.submit_item(
                {"id": i, "data": f"item_{i}"},
                BatchType.DATABASE_READ
            )
            request_ids.append(request_id)

        print(f"Submitted {len(request_ids)} items for batch processing")

        # Wait a bit for processing
        await asyncio.sleep(1)

        print("Processor stats:", processor.get_stats())

        await processor.stop()

    asyncio.run(main())