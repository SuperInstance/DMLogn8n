#!/usr/bin/env python3
"""
High-Performance Async Request Handler
Advanced async processing for non-blocking API operations
"""

import asyncio
import time
import logging
import inspect
import functools
import traceback
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Awaitable, TypeVar, Generic
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles
import aiohttp
import aioredis
from fastapi import Request, Response, HTTPException
from fastapi.concurrency import run_in_threadpool
import uvloop
import orjson
import weakref

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class TaskPriority(Enum):
    """Task priorities for async execution"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    REALTIME = 5

class TaskType(Enum):
    """Types of async tasks"""
    IO_BOUND = "io_bound"
    CPU_BOUND = "cpu_bound"
    MIXED = "mixed"
    DATABASE = "database"
    NETWORK = "network"
    FILE = "file"

@dataclass
class AsyncConfig:
    """Configuration for async handler"""
    # Event loop settings
    use_uvloop: bool = True
    max_event_loop_workers: int = 1000
    event_loop_policy: str = "uvloop"

    # Thread pool settings
    max_thread_workers: int = 50
    max_process_workers: int = 10
    thread_pool_queue_size: int = 1000

    # Task queue settings
    max_queue_size: int = 10000
    priority_queue_enabled: bool = True
    queue_timeout_seconds: int = 60

    # Performance settings
    enable_task_cancellation: bool = True
    enable_task_timeout: bool = True
    default_task_timeout: int = 30
    enable_task_retry: bool = True
    max_retries: int = 3

    # Memory management
    enable_memory_monitoring: bool = True
    memory_threshold_mb: int = 512
    gc_threshold_ratio: float = 0.8

    # Advanced features
    enable_task_deduplication: bool = True
    enable_batching: bool = True
    batch_size: int = 10
    batch_timeout_ms: int = 100

@dataclass
class AsyncTask:
    """Async task with metadata"""
    id: str
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    priority: TaskPriority
    task_type: TaskType
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    future: Optional[asyncio.Future] = None
    callback: Optional[Callable] = None

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()

@dataclass
class TaskResult:
    """Result of async task execution"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0
    retry_count: int = 0
    memory_usage_mb: float = 0

class PriorityTaskQueue:
    """Priority-based task queue for async execution"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[TaskPriority, deque] = {
            priority: deque() for priority in TaskPriority
        }
        self.task_count = 0
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)

    async def put(self, task: AsyncTask) -> bool:
        """Add task to queue"""
        async with self.not_empty:
            if self.task_count >= self.max_size:
                return False  # Queue full

            self.queues[task.priority].append(task)
            self.task_count += 1
            self.not_empty.notify()
            return True

    async def get(self) -> Optional[AsyncTask]:
        """Get highest priority task"""
        async with self.not_empty:
            while self.task_count == 0:
                await self.not_empty.wait()

            # Get highest priority non-empty queue
            for priority in sorted(TaskPriority, key=lambda x: x.value, reverse=True):
                if self.queues[priority]:
                    task = self.queues[priority].popleft()
                    self.task_count -= 1
                    return task

            return None

    async def size(self) -> int:
        """Get queue size"""
        async with self.lock:
            return self.task_count

    async def empty(self) -> bool:
        """Check if queue is empty"""
        async with self.lock:
            return self.task_count == 0

class TaskScheduler:
    """Advanced task scheduler for async operations"""

    def __init__(self, config: AsyncConfig):
        self.config = config
        self.task_queue = PriorityTaskQueue(config.max_queue_size)
        self.running_tasks: Dict[str, AsyncTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}

        # Thread and process pools
        self.thread_executor = ThreadPoolExecutor(
            max_workers=config.max_thread_workers,
            thread_name_prefix="async_handler"
        )
        self.process_executor = ProcessPoolExecutor(
            max_workers=config.max_process_workers
        )

        # Task deduplication
        self.task_hashes: Dict[str, str] = {}  # hash -> task_id
        self.pending_tasks: Dict[str, AsyncTask] = {}

        # Batching
        self.batch_queues: Dict[str, List[AsyncTask]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}

        # Statistics
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "queue_size": 0,
            "running_tasks": 0
        }

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def start(self):
        """Start task scheduler"""
        self.running = True

        # Start worker tasks
        num_workers = min(self.config.max_event_loop_workers, asyncio.get_event_loop()._max_workers)
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        # Start monitoring task
        monitor = asyncio.create_task(self._monitor())
        self.workers.append(monitor)

    async def stop(self):
        """Stop task scheduler"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Shutdown executors
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)

    async def submit_task(self, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL,
                         task_type: TaskType = TaskType.MIXED, timeout: Optional[float] = None,
                         max_retries: int = 3, callback: Optional[Callable] = None, **kwargs) -> str:
        """Submit task for async execution"""
        import uuid
        task_id = str(uuid.uuid4())

        task = AsyncTask(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            task_type=task_type,
            timeout=timeout or self.config.default_task_timeout,
            max_retries=max_retries,
            callback=callback
        )

        # Check for task deduplication
        if self.config.enable_task_deduplication:
            task_hash = self._generate_task_hash(task)
            if task_hash in self.task_hashes:
                existing_task_id = self.task_hashes[task_hash]
                if existing_task_id in self.pending_tasks:
                    # Return existing task's future
                    return existing_task_id

            self.task_hashes[task_hash] = task_id
            self.pending_tasks[task_id] = task

        # Check for batching
        if self.config.enable_batching and task_type == TaskType.DATABASE:
            return await self._handle_batching(task)

        # Add to queue
        success = await self.task_queue.put(task)
        if not success:
            raise HTTPException(status_code=503, detail="Task queue full")

        self.stats["tasks_submitted"] += 1
        return task_id

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        return self.completed_tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel running task"""
        task = self.running_tasks.get(task_id)
        if task and task.future:
            task.future.cancel()
            return True
        return False

    async def _worker(self, worker_name: str):
        """Worker task for processing queued tasks"""
        logger.info(f"Worker {worker_name} started")

        while self.running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                if task is None:
                    continue

                # Execute task
                await self._execute_task(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")

        logger.info(f"Worker {worker_name} stopped")

    async def _execute_task(self, task: AsyncTask):
        """Execute individual task"""
        task.started_at = time.time()
        self.running_tasks[task.id] = task

        try:
            # Choose execution method based on task type
            if task.task_type == TaskType.CPU_BOUND:
                result = await self._execute_cpu_bound(task)
            elif task.task_type == TaskType.IO_BOUND:
                result = await self._execute_io_bound(task)
            else:
                result = await self._execute_async(task)

            # Create successful result
            task_result = TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                execution_time=time.time() - task.started_at,
                retry_count=task.retry_count
            )

        except Exception as e:
            # Handle task failure
            if task.retry_count < task.max_retries and self.config.enable_task_retry:
                # Retry task
                task.retry_count += 1
                await self.task_queue.put(task)
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
                return

            # Create failure result
            task_result = TaskResult(
                task_id=task.id,
                success=False,
                error=e,
                execution_time=time.time() - task.started_at,
                retry_count=task.retry_count
            )

        finally:
            # Cleanup
            task.completed_at = time.time()
            del self.running_tasks[task.id]
            if task.id in self.pending_tasks:
                del self.pending_tasks[task.id]

            # Remove from deduplication
            task_hash = self._generate_task_hash(task)
            self.task_hashes.pop(task_hash, None)

            # Store result
            self.completed_tasks[task.id] = task_result

            # Update statistics
            self._update_stats(task_result)

            # Call callback if provided
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task_result)
                    else:
                        await run_in_threadpool(task.callback, task_result)
                except Exception as e:
                    logger.error(f"Task callback error: {e}")

    async def _execute_async(self, task: AsyncTask) -> Any:
        """Execute async task"""
        if asyncio.iscoroutinefunction(task.func):
            # Native async function
            if self.config.enable_task_timeout:
                return await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                return await task.func(*task.args, **task.kwargs)
        else:
            # Sync function, run in thread pool
            if self.config.enable_task_timeout:
                return await asyncio.wait_for(
                    run_in_threadpool(task.func, *task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                return await run_in_threadpool(task.func, *task.args, **task.kwargs)

    async def _execute_io_bound(self, task: AsyncTask) -> Any:
        """Execute I/O bound task"""
        return await self._execute_async(task)

    async def _execute_cpu_bound(self, task: AsyncTask) -> Any:
        """Execute CPU bound task in process pool"""
        loop = asyncio.get_event_loop()

        if self.config.enable_task_timeout:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    self.process_executor,
                    functools.partial(task.func, *task.args, **task.kwargs)
                ),
                timeout=task.timeout
            )
        else:
            return await loop.run_in_executor(
                self.process_executor,
                functools.partial(task.func, *task.args, **task.kwargs)
            )

    async def _handle_batching(self, task: AsyncTask) -> str:
        """Handle task batching"""
        # Create batch key based on function and similar arguments
        batch_key = f"{task.func.__name__}_{task.task_type.value}"

        # Add to batch queue
        self.batch_queues[batch_key].append(task)

        # Set batch timer if not already running
        if batch_key not in self.batch_timers:
            self.batch_timers[batch_key] = asyncio.create_task(
                self._batch_timer(batch_key)
            )

        # Check if batch is ready
        if len(self.batch_queues[batch_key]) >= self.config.batch_size:
            await self._process_batch(batch_key)

        return task.id

    async def _batch_timer(self, batch_key: str):
        """Batch timer for processing batches"""
        await asyncio.sleep(self.config.batch_timeout_ms / 1000)
        if batch_key in self.batch_queues and self.batch_queues[batch_key]:
            await self._process_batch(batch_key)

    async def _process_batch(self, batch_key: str):
        """Process batch of tasks"""
        if batch_key not in self.batch_queues:
            return

        tasks = self.batch_queues[batch_key].copy()
        self.batch_queues[batch_key].clear()

        # Cancel timer
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]

        if not tasks:
            return

        # Execute batch
        try:
            # Group similar tasks and execute together
            results = await self._execute_batch(tasks)

            # Update task results
            for task, result in zip(tasks, results):
                task_result = TaskResult(
                    task_id=task.id,
                    success=True,
                    result=result,
                    execution_time=0.001,  # Batch execution is fast
                    retry_count=task.retry_count
                )
                self.completed_tasks[task.id] = task_result

                # Call callback
                if task.callback:
                    try:
                        if asyncio.iscoroutinefunction(task.callback):
                            await task.callback(task_result)
                        else:
                            await run_in_threadpool(task.callback, task_result)
                    except Exception as e:
                        logger.error(f"Batch task callback error: {e}")

        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            # Handle batch failure
            for task in tasks:
                task_result = TaskResult(
                    task_id=task.id,
                    success=False,
                    error=e,
                    execution_time=0.001,
                    retry_count=task.retry_count
                )
                self.completed_tasks[task.id] = task_result

    async def _execute_batch(self, tasks: List[AsyncTask]) -> List[Any]:
        """Execute batch of tasks together"""
        # This is a simplified implementation
        # In practice, you'd want to optimize based on the specific operations
        results = []
        for task in tasks:
            try:
                result = await self._execute_async(task)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def _generate_task_hash(self, task: AsyncTask) -> str:
        """Generate hash for task deduplication"""
        import hashlib
        hash_data = f"{task.func.__name__}_{task.args}_{task.kwargs}"
        return hashlib.md5(hash_data.encode()).hexdigest()

    def _update_stats(self, result: TaskResult):
        """Update scheduler statistics"""
        if result.success:
            self.stats["tasks_completed"] += 1
        else:
            self.stats["tasks_failed"] += 1

        self.stats["total_execution_time"] += result.execution_time
        total_tasks = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        if total_tasks > 0:
            self.stats["average_execution_time"] = self.stats["total_execution_time"] / total_tasks

    async def _monitor(self):
        """Monitor scheduler performance"""
        while self.running:
            try:
                # Update queue size
                self.stats["queue_size"] = await self.task_queue.size()
                self.stats["running_tasks"] = len(self.running_tasks)

                # Memory monitoring
                if self.config.enable_memory_monitoring:
                    await self._check_memory_usage()

                # Cleanup old completed tasks
                await self._cleanup_completed_tasks()

                await asyncio.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"Monitor error: {e}")

    async def _check_memory_usage(self):
        """Check memory usage and trigger cleanup if needed"""
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb > self.config.memory_threshold_mb:
            logger.warning(f"High memory usage: {memory_mb:.1f}MB")
            # Trigger garbage collection
            import gc
            gc.collect()

    async def _cleanup_completed_tasks(self):
        """Clean up old completed tasks"""
        current_time = time.time()
        cutoff_time = current_time - 300  # Keep last 5 minutes

        to_remove = []
        for task_id, result in self.completed_tasks.items():
            # Remove old successful tasks
            if result.success and result.execution_time < 0.1:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.completed_tasks[task_id]

        # Keep at most 1000 completed tasks
        if len(self.completed_tasks) > 1000:
            oldest_tasks = sorted(
                self.completed_tasks.items(),
                key=lambda x: x[1].execution_time
            )[:500]
            for task_id, _ in oldest_tasks:
                del self.completed_tasks[task_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return self.stats.copy()

class AsyncRequestHandler:
    """High-performance async request handler"""

    def __init__(self, config: AsyncConfig = None):
        self.config = config or AsyncConfig()
        self.scheduler = TaskScheduler(self.config)
        self.request_handlers: Dict[str, Callable] = {}

    async def initialize(self):
        """Initialize async handler"""
        # Set event loop policy if specified
        if self.config.use_uvloop and self.config.event_loop_policy == "uvloop":
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        await self.scheduler.start()

    async def shutdown(self):
        """Shutdown async handler"""
        await self.scheduler.stop()

    def register_handler(self, path: str, handler: Callable):
        """Register async request handler"""
        self.request_handlers[path] = handler

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request asynchronously"""
        path = request.url.path

        if path not in self.request_handlers:
            raise HTTPException(status_code=404, detail="Handler not found")

        handler = self.request_handlers[path]

        try:
            # Submit task for execution
            task_id = await self.scheduler.submit_task(
                handler,
                request,
                priority=TaskPriority.HIGH,
                task_type=TaskType.MIXED
            )

            # Wait for task completion
            start_time = time.time()
            while True:
                result = await self.scheduler.get_task_result(task_id)
                if result:
                    break

                # Check for timeout
                if time.time() - start_time > self.config.default_task_timeout:
                    await self.scheduler.cancel_task(task_id)
                    raise HTTPException(status_code=504, detail="Request timeout")

                await asyncio.sleep(0.001)  # Small delay to prevent busy waiting

            if result.success:
                if isinstance(result.result, Response):
                    return result.result
                else:
                    return Response(content=result.result)
            else:
                raise HTTPException(status_code=500, detail=str(result.error))

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def submit_background_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit background task"""
        return await self.scheduler.submit_task(
            func,
            *args,
            priority=TaskPriority.LOW,
            task_type=TaskType.MIXED,
            **kwargs
        )

    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status"""
        return await self.scheduler.get_task_result(task_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            "scheduler": self.scheduler.get_stats(),
            "registered_handlers": list(self.request_handlers.keys())
        }

# Decorators for easy async handling
def async_handler(priority: TaskPriority = TaskPriority.NORMAL,
                  task_type: TaskType = TaskType.MIXED,
                  timeout: Optional[float] = None):
    """Decorator for async request handlers"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need integration with the async handler
            return await func(*args, **kwargs)
        wrapper._async_metadata = {
            "priority": priority,
            "task_type": task_type,
            "timeout": timeout
        }
        return wrapper
    return decorator

def background_task(priority: TaskPriority = TaskPriority.LOW):
    """Decorator for background tasks"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need integration with the async handler
            return await func(*args, **kwargs)
        wrapper._background_metadata = {
            "priority": priority
        }
        return wrapper
    return decorator

# FastAPI integration
class AsyncHandlerMiddleware:
    """FastAPI middleware for async request handling"""

    def __init__(self, app, handler: AsyncRequestHandler):
        self.app = app
        self.handler = handler

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object
        request = Request(scope, receive)

        # Handle request asynchronously
        try:
            response = await self.handler.handle_request(request)

            # Send response
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": response.raw_headers,
            })

            await send({
                "type": "http.response.body",
                "body": response.body,
            })

        except Exception as e:
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"application/json")],
            })

            await send({
                "type": "http.response.body",
                "body": orjson.dumps({"error": str(e)}),
            })

if __name__ == "__main__":
    # Example usage
    async def main():
        config = AsyncConfig()
        handler = AsyncRequestHandler(config)
        await handler.initialize()

        # Register a handler
        @async_handler(priority=TaskPriority.HIGH, task_type=TaskType.IO_BOUND)
        async def example_handler(request: Request):
            await asyncio.sleep(0.1)  # Simulate async work
            return {"message": "Async response", "timestamp": time.time()}

        handler.register_handler("/api/async", example_handler)

        # Submit background task
        task_id = await handler.submit_background_task(
            lambda: print("Background task completed")
        )

        print("Handler stats:", handler.get_stats())

        await handler.shutdown()

    asyncio.run(main())