#!/usr/bin/env python3
"""
Async Processor - Advanced Asynchronous Operations Optimization
Optimizes async operations for maximum throughput and minimal latency
"""

import asyncio
import time
import threading
import queue
import heapq
from typing import Dict, List, Any, Optional, Callable, Coroutine, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict, deque
import logging
import weakref
from functools import wraps
import inspect
from enum import Enum

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0    # Real-time critical tasks
    HIGH = 1        # High priority user tasks
    NORMAL = 2      # Normal priority tasks
    LOW = 3         # Background tasks
    MAINTENANCE = 4 # Maintenance tasks

@dataclass
class AsyncTask:
    """Represents an asynchronous task with metadata"""
    id: str
    coro: Coroutine
    priority: TaskPriority
    created_time: float
    timeout: Optional[float] = None
    callback: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value < other.priority.value

@dataclass
class TaskMetrics:
    """Metrics for task execution"""
    task_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    queue_wait_time: float = 0.0

class AsyncProcessor:
    """Advanced async task processor with optimization strategies"""

    def __init__(self, max_workers: int = 50, enable_monitoring: bool = True):
        self.max_workers = max_workers
        self.enable_monitoring = enable_monitoring

        # Task queues by priority
        self.task_queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }

        # Active tasks tracking
        self.active_tasks: Dict[str, AsyncTask] = {}
        self.pending_tasks: Dict[str, AsyncTask] = {}
        self.completed_tasks: Dict[str, TaskMetrics] = {}

        # Worker management
        self.workers: List[asyncio.Task] = []
        self.running = False

        # Performance metrics
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time_ms': 0.0,
            'tasks_per_second': 0.0,
            'queue_sizes': {priority: 0 for priority in TaskPriority},
            'worker_utilization': 0.0
        }

        # Batch processing
        self.batch_processors: Dict[str, List[AsyncTask]] = defaultdict(list)
        self.batch_timeout = 0.01  # 10ms batch window
        self.max_batch_size = 10

        # Task dependencies
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.waiting_for_deps: Dict[str, AsyncTask] = {}

        # Load balancing
        self.worker_loads: List[int] = [0] * max_workers
        self.load_balancer_index = 0

        # Event loop optimization
        self.custom_loop = None
        self.loop_optimizations_enabled = True

        # Setup logging
        self.logger = logging.getLogger("AsyncProcessor")

    async def start(self):
        """Start the async processor"""
        if self.running:
            return

        self.running = True

        # Create optimized event loop if needed
        if self.loop_optimizations_enabled:
            await self._setup_optimized_loop()

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)

        # Start background tasks
        if self.enable_monitoring:
            asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._metrics_collection_loop())

        # Start batch processor
        asyncio.create_task(self._batch_processor_loop())

        # Start dependency resolver
        asyncio.create_task(self._dependency_resolver_loop())

        self.logger.info(f"AsyncProcessor started with {self.max_workers} workers")

    async def stop(self):
        """Stop the async processor"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.logger.info("AsyncProcessor stopped")

    async def _setup_optimized_loop(self):
        """Setup optimized event loop"""
        # Configure loop for better performance
        loop = asyncio.get_running_loop()

        # Optimize loop policies
        if hasattr(loop, 'set_debug'):
            loop.set_debug(False)  # Disable debug for performance

        # Set loop policies for better I/O handling
        if hasattr(asyncio, 'DefaultEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

        self.custom_loop = loop

    async def submit_task(self, coro: Coroutine, priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None, callback: Optional[Callable] = None,
                         task_id: Optional[str] = None, dependencies: Optional[List[str]] = None,
                         max_retries: int = 3, **metadata) -> str:
        """Submit a task for processing"""
        task_id = task_id or f"task_{int(time.time() * 1000000)}_{id(coro)}"

        task = AsyncTask(
            id=task_id,
            coro=coro,
            priority=priority,
            created_time=time.time(),
            timeout=timeout,
            callback=callback,
            dependencies=dependencies or [],
            max_retries=max_retries,
            metadata=metadata
        )

        # Check dependencies
        if dependencies:
            if await self._check_dependencies(task):
                await self._enqueue_task(task)
            else:
                self.waiting_for_deps[task_id] = task
        else:
            await self._enqueue_task(task)

        self.metrics['total_tasks'] += 1
        return task_id

    async def _enqueue_task(self, task: AsyncTask):
        """Enqueue task in appropriate priority queue"""
        self.pending_tasks[task.id] = task
        await self.task_queues[task.priority].put(task)
        self.metrics['queue_sizes'][task.priority] += 1

    async def _check_dependencies(self, task: AsyncTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            elif not self.completed_tasks[dep_id].success:
                return False
        return True

    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing tasks"""
        worker_index = int(worker_name.split('-')[1])

        while self.running:
            try:
                # Get task from highest priority queue that has tasks
                task = await self._get_next_task()
                if not task:
                    await asyncio.sleep(0.001)  # Brief pause
                    continue

                # Track task
                self.active_tasks[task.id] = task
                self.pending_tasks.pop(task.id, None)
                self.worker_loads[worker_index] += 1

                # Execute task
                await self._execute_task(task, worker_index)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}")

    async def _get_next_task(self) -> Optional[AsyncTask]:
        """Get next task based on priority"""
        # Check queues in priority order
        for priority in sorted(TaskPriority, key=lambda p: p.value):
            try:
                queue = self.task_queues[priority]
                if not queue.empty():
                    task = queue.get_nowait()
                    self.metrics['queue_sizes'][priority] -= 1
                    return task
            except asyncio.QueueEmpty:
                continue
        return None

    async def _execute_task(self, task: AsyncTask, worker_index: int):
        """Execute a single task"""
        start_time = time.time()
        queue_wait_time = start_time - task.created_time

        metrics = TaskMetrics(
            task_id=task.id,
            start_time=start_time,
            queue_wait_time=queue_wait_time,
            retry_count=task.retry_count
        )

        try:
            # Execute with timeout
            if task.timeout:
                result = await asyncio.wait_for(task.coro, timeout=task.timeout)
            else:
                result = await task.coro

            # Task completed successfully
            end_time = time.time()
            metrics.end_time = end_time
            metrics.duration_ms = (end_time - start_time) * 1000
            metrics.success = True

            self.completed_tasks[task.id] = metrics
            self.metrics['completed_tasks'] += 1

            # Call callback if provided
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(result)
                    else:
                        task.callback(result)
                except Exception as e:
                    self.logger.error(f"Task callback error: {e}")

            # Check for dependent tasks
            await self._resolve_dependent_tasks(task.id)

        except asyncio.TimeoutError:
            metrics.end_time = time.time()
            metrics.duration_ms = (metrics.end_time - start_time) * 1000
            metrics.success = False
            metrics.error_message = "Task timeout"

            self.completed_tasks[task.id] = metrics
            self.metrics['failed_tasks'] += 1
            self.logger.warning(f"Task {task.id} timed out")

        except Exception as e:
            metrics.end_time = time.time()
            metrics.duration_ms = (metrics.end_time - start_time) * 1000
            metrics.success = False
            metrics.error_message = str(e)

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                await self._enqueue_task(task)
                self.logger.warning(f"Retrying task {task.id} (attempt {task.retry_count})")
            else:
                self.completed_tasks[task.id] = metrics
                self.metrics['failed_tasks'] += 1
                self.logger.error(f"Task {task.id} failed permanently: {e}")

        finally:
            self.active_tasks.pop(task.id, None)
            self.worker_loads[worker_index] -= 1

    async def _resolve_dependent_tasks(self, completed_task_id: str):
        """Resolve tasks that were waiting for this task"""
        dependent_tasks = [
            task for task in self.waiting_for_deps.values()
            if completed_task_id in task.dependencies
        ]

        for task in dependent_tasks:
            if await self._check_dependencies(task):
                await self._enqueue_task(task)
                self.waiting_for_deps.pop(task.id, None)

    async def _dependency_resolver_loop(self):
        """Background loop to resolve task dependencies"""
        while self.running:
            try:
                # Check waiting tasks
                ready_tasks = []
                for task_id, task in list(self.waiting_for_deps.items()):
                    if await self._check_dependencies(task):
                        ready_tasks.append(task)

                # Enqueue ready tasks
                for task in ready_tasks:
                    await self._enqueue_task(task)
                    self.waiting_for_deps.pop(task.id, None)

                await asyncio.sleep(0.01)  # Check every 10ms

            except Exception as e:
                self.logger.error(f"Dependency resolver error: {e}")

    async def _batch_processor_loop(self):
        """Background loop for batch processing similar tasks"""
        while self.running:
            try:
                # Collect tasks for batch processing
                current_time = time.time()
                batch_tasks = []

                # Look for batchable tasks
                for priority_batch in self.batch_processors.values():
                    if len(priority_batch) >= self.max_batch_size:
                        batch_tasks.extend(priority_batch[:self.max_batch_size])
                        priority_batch[:self.max_batch_size] = []
                        break

                if batch_tasks:
                    await self._process_batch(batch_tasks)

                await asyncio.sleep(self.batch_timeout)

            except Exception as e:
                self.logger.error(f"Batch processor error: {e}")

    async def _process_batch(self, tasks: List[AsyncTask]):
        """Process a batch of tasks together"""
        if not tasks:
            return

        try:
            # Execute tasks concurrently
            start_time = time.time()
            await asyncio.gather(*[task.coro for task in tasks], return_exceptions=True)
            duration = time.time() - start_time

            self.logger.debug(f"Processed batch of {len(tasks)} tasks in {duration:.3f}s")

        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Check for long-running tasks
                current_time = time.time()
                for task in list(self.active_tasks.values()):
                    runtime = current_time - task.created_time
                    if task.timeout and runtime > task.timeout:
                        self.logger.warning(f"Task {task.id} exceeded timeout: {runtime:.2f}s")

                # Monitor queue sizes
                total_queued = sum(self.metrics['queue_sizes'].values())
                if total_queued > self.max_workers * 10:
                    self.logger.warning(f"High queue size: {total_queued} tasks")

                await asyncio.sleep(1.0)  # Monitor every second

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")

    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        while self.running:
            try:
                await self._update_metrics()
                await asyncio.sleep(5.0)  # Update every 5 seconds

            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")

    async def _update_metrics(self):
        """Update performance metrics"""
        total_completed = self.metrics['completed_tasks'] + self.metrics['failed_tasks']

        if total_completed > 0:
            # Calculate average execution time
            total_time = sum(m.duration_ms for m in self.completed_tasks.values() if m.duration_ms)
            self.metrics['avg_execution_time_ms'] = total_time / len(self.completed_tasks)

            # Calculate tasks per second
            time_window = 60.0  # Last 60 seconds
            recent_tasks = [
                m for m in self.completed_tasks.values()
                if m.end_time and (time.time() - m.end_time) < time_window
            ]
            self.metrics['tasks_per_second'] = len(recent_tasks) / time_window

        # Calculate worker utilization
        active_workers = sum(1 for load in self.worker_loads if load > 0)
        self.metrics['worker_utilization'] = (active_workers / self.max_workers) * 100

    def optimize_function(self, func: Callable, priority: TaskPriority = TaskPriority.NORMAL):
        """Decorator to optimize function execution"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                # Submit as async task
                return await self.submit_task(
                    func(*args, **kwargs),
                    priority=priority
                )
            else:
                # Execute in thread pool
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Execute in thread pool for sync functions
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            finally:
                loop.close()

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    async def execute_parallel(self, tasks: List[Coroutine],
                             max_concurrency: Optional[int] = None) -> List[Any]:
        """Execute multiple tasks in parallel with controlled concurrency"""
        max_concurrency = max_concurrency or self.max_workers
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(coro):
            async with semaphore:
                return await coro

        return await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

    async def execute_with_timeout(self, coro: Coroutine, timeout: float) -> Any:
        """Execute task with timeout and optimized error handling"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Task timed out after {timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"Task execution error: {e}")
            raise

    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        return {
            **self.metrics,
            'active_tasks': len(self.active_tasks),
            'pending_tasks': len(self.pending_tasks),
            'waiting_for_deps': len(self.waiting_for_deps),
            'worker_loads': self.worker_loads.copy(),
            'queue_details': {
                priority.name: queue.qsize()
                for priority, queue in self.task_queues.items()
            }
        }

    def get_task_details(self, task_id: str) -> Optional[Dict]:
        """Get detailed information about a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'status': 'active',
                'task': task,
                'runtime': time.time() - task.created_time
            }

        # Check pending tasks
        if task_id in self.pending_tasks:
            task = self.pending_tasks[task_id]
            return {
                'status': 'pending',
                'task': task,
                'queue_time': time.time() - task.created_time
            }

        # Check completed tasks
        if task_id in self.completed_tasks:
            metrics = self.completed_tasks[task_id]
            return {
                'status': 'completed' if metrics.success else 'failed',
                'metrics': metrics
            }

        return None

# Global async processor instance
async_processor = AsyncProcessor()

# Convenience decorators
def optimize_async(priority: TaskPriority = TaskPriority.NORMAL):
    """Decorator to optimize async function execution"""
    return async_processor.optimize_function(priority=priority)

def high_priority_async(func: Callable) -> Callable:
    """Decorator for high-priority async functions"""
    return async_processor.optimize_function(func, TaskPriority.HIGH)

def critical_async(func: Callable) -> Callable:
    """Decorator for critical async functions"""
    return async_processor.optimize_function(func, TaskPriority.CRITICAL)

# Utility functions
async def run_optimized(coro: Coroutine, priority: TaskPriority = TaskPriority.NORMAL) -> Any:
    """Run coroutine with optimized processing"""
    return await async_processor.submit_task(coro, priority=priority)

async def parallel_execute(tasks: List[Coroutine], max_concurrency: Optional[int] = None) -> List[Any]:
    """Execute tasks in parallel with optimized concurrency"""
    return await async_processor.execute_parallel(tasks, max_concurrency)