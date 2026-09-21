#!/usr/bin/env python3
"""
Advanced Concurrency Manager for DMLogn8n Platform
Thread management, lock-free algorithms, async/await optimization, and parallelization
"""

import asyncio
import concurrent.futures
import contextvars
import ctypes
import fcntl
import functools
import inspect
import json
import logging
import multiprocessing as mp
import os
import queue
import signal
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, TypeVar, Generic
import uuid

# Lock-free and concurrent data structures
try:
    import async_timeout
    ASYNC_TIMEOUT_AVAILABLE = True
except ImportError:
    ASYNC_TIMEOUT_AVAILABLE = False

try:
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
    CONCURRENT_AVAILABLE = True
except ImportError:
    CONCURRENT_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class ConcurrencyType(Enum):
    """Concurrency execution types"""
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"
    ASYNC_POOL = "async_pool"
    LOCK_FREE = "lock_free"
    ACTOR_MODEL = "actor_model"
    COROUTINE = "coroutine"
    HYBRID = "hybrid"

class SynchronizationStrategy(Enum):
    """Synchronization strategies"""
    LOCK_BASED = "lock_based"
    LOCK_FREE = "lock_free"
    WAIT_FREE = "wait_free"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    SOFTWARE_TRANSACTIONAL_MEMORY = "stm"

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    CONSISTENT_HASH = "consistent_hash"

@dataclass
class TaskMetrics:
    """Task execution metrics"""
    task_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_ms: float
    worker_id: str
    concurrency_type: ConcurrencyType
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class WorkerMetrics:
    """Worker performance metrics"""
    worker_id: str
    worker_type: ConcurrencyType
    created_at: datetime
    tasks_completed: int
    tasks_failed: int
    total_execution_time: float
    avg_execution_time: float
    current_load: int
    max_capacity: int
    memory_usage_mb: float
    cpu_usage_percent: float
    last_activity: datetime

@dataclass
class PoolConfig:
    """Thread/process pool configuration"""
    pool_type: ConcurrencyType
    min_workers: int = 1
    max_workers: int = 10
    queue_size: int = 1000
    worker_timeout: float = 30.0
    task_timeout: float = 300.0
    max_retries: int = 3
    retry_backoff: float = 1.0
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    affinity_enabled: bool = False
    priority_levels: int = 3

class LockFreeQueue(Generic[T]):
    """Lock-free queue implementation using atomic operations"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer = [None] * max_size
        self._head = mp.Value('i', 0)
        self._tail = mp.Value('i', 0)
        self._size = mp.Value('i', 0)

    def put(self, item: T) -> bool:
        """Add item to queue (non-blocking)"""
        with self._size.get_lock():
            if self._size.value >= self.max_size:
                return False

            with self._tail.get_lock():
                self.buffer[self._tail.value % self.max_size] = item
                self._tail.value += 1
                self._size.value += 1
                return True

    def get(self) -> Optional[T]:
        """Get item from queue (non-blocking)"""
        with self._size.get_lock():
            if self._size.value <= 0:
                return None

            with self._head.get_lock():
                item = self.buffer[self._head.value % self.max_size]
                self._head.value += 1
                self._size.value -= 1
                return item

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._size.value == 0

    def full(self) -> bool:
        """Check if queue is full"""
        return self._size.value >= self.max_size

class Worker(Generic[T, R]):
    """Generic worker implementation"""

    def __init__(self, worker_id: str, worker_type: ConcurrencyType):
        self.worker_id = worker_id
        self.worker_type = worker_type
        self.task_queue = asyncio.Queue() if worker_type == ConcurrencyType.ASYNC_POOL else queue.Queue()
        self.running = False
        self.metrics = WorkerMetrics(
            worker_id=worker_id,
            worker_type=worker_type,
            created_at=datetime.now(),
            tasks_completed=0,
            tasks_failed=0,
            total_execution_time=0.0,
            avg_execution_time=0.0,
            current_load=0,
            max_capacity=1,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            last_activity=datetime.now()
        )
        self.processing_lock = threading.Lock()

    async def start(self):
        """Start worker processing loop"""
        self.running = True
        if self.worker_type == ConcurrencyType.ASYNC_POOL:
            asyncio.create_task(self._async_processing_loop())
        else:
            thread = threading.Thread(target=self._sync_processing_loop, daemon=True)
            thread.start()

    async def _async_processing_loop(self):
        """Async task processing loop"""
        while self.running:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                await self._process_async_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in async processing loop: {e}")

    def _sync_processing_loop(self):
        """Sync task processing loop"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1.0)
                self._process_sync_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in sync processing loop: {e}")

    async def _process_async_task(self, task: Dict[str, Any]):
        """Process async task"""
        start_time = time.time()
        task_id = task['task_id']
        func = task['func']
        args = task['args']
        kwargs = task['kwargs']
        future = task['future']

        try:
            with self.processing_lock:
                self.metrics.current_load += 1
                self.metrics.last_activity = datetime.now()

            # Execute task
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

            execution_time = (time.time() - start_time) * 1000

            # Update metrics
            with self.processing_lock:
                self.metrics.tasks_completed += 1
                self.metrics.total_execution_time += execution_time
                self.metrics.avg_execution_time = (
                    self.metrics.total_execution_time / self.metrics.tasks_completed
                )
                self.metrics.current_load -= 1

            # Set result
            future.set_result(result)

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            with self.processing_lock:
                self.metrics.tasks_failed += 1
                self.metrics.current_load -= 1

            future.set_exception(e)

    def _process_sync_task(self, task: Dict[str, Any]):
        """Process sync task"""
        start_time = time.time()
        task_id = task['task_id']
        func = task['func']
        args = task['args']
        kwargs = task['kwargs']
        future = task['future']

        try:
            with self.processing_lock:
                self.metrics.current_load += 1
                self.metrics.last_activity = datetime.now()

            # Execute task
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Update metrics
            with self.processing_lock:
                self.metrics.tasks_completed += 1
                self.metrics.total_execution_time += execution_time
                self.metrics.avg_execution_time = (
                    self.metrics.total_execution_time / self.metrics.tasks_completed
                )
                self.metrics.current_load -= 1

            # Set result
            future.set_result(result)

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            with self.processing_lock:
                self.metrics.tasks_failed += 1
                self.metrics.current_load -= 1

            future.set_exception(e)

    def submit_task(self, task: Dict[str, Any]) -> bool:
        """Submit task to worker"""
        if not self.running:
            return False

        try:
            if self.worker_type == ConcurrencyType.ASYNC_POOL:
                # For async workers, this should be called from async context
                asyncio.create_task(self.task_queue.put(task))
            else:
                self.task_queue.put_nowait(task)
            return True
        except (queue.Full, asyncio.QueueFull):
            return False

    def stop(self):
        """Stop worker"""
        self.running = False

class ConcurrencyManager:
    """Advanced concurrency management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.pools = {}
        self.workers = {}
        self.task_metrics = deque(maxlen=self.config.get('history_size', 10000))
        self.active_tasks = {}
        self.load_balancers = {}

        # Concurrency settings
        self.auto_scaling = self.config.get('auto_scaling', True)
        self.load_balancing = self.config.get('load_balancing', True)
        self.deadlock_detection = self.config.get('deadlock_detection', True)
        self.performance_monitoring = self.config.get('performance_monitoring', True)

        # Thread affinity settings
        self.cpu_affinity_enabled = self.config.get('cpu_affinity_enabled', False)
        self.num_cpus = os.cpu_count() or 1

        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        # Initialize default pools
        self._initialize_default_pools()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'history_size': 10000,
            'auto_scaling': True,
            'load_balancing': True,
            'deadlock_detection': True,
            'performance_monitoring': True,
            'cpu_affinity_enabled': False,
            'default_pool_size': min(32, (os.cpu_count() or 1) * 4),
            'max_pool_size': min(100, (os.cpu_count() or 1) * 10),
            'monitoring_interval': 60.0,
            'scaling_interval': 30.0,
            'task_timeout': 300.0,
            'worker_timeout': 30.0,
            'max_retries': 3,
            'retry_backoff': 1.0
        }

    def _initialize_default_pools(self):
        """Initialize default thread and process pools"""
        # Thread pool for I/O bound tasks
        thread_pool_config = PoolConfig(
            pool_type=ConcurrencyType.THREAD_POOL,
            min_workers=2,
            max_workers=self.config.get('default_pool_size', 32),
            queue_size=1000,
            load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        self.create_pool("default_thread", thread_pool_config)

        # Process pool for CPU bound tasks
        process_pool_config = PoolConfig(
            pool_type=ConcurrencyType.PROCESS_POOL,
            min_workers=1,
            max_workers=min(self.config.get('default_pool_size', 32), os.cpu_count() or 1),
            queue_size=100,
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN
        )
        self.create_pool("default_process", process_pool_config)

        # Async pool for coroutine tasks
        async_pool_config = PoolConfig(
            pool_type=ConcurrencyType.ASYNC_POOL,
            min_workers=10,
            max_workers=self.config.get('default_pool_size', 32),
            queue_size=1000,
            load_balancing=LoadBalancingStrategy.LEAST_RESPONSE_TIME
        )
        self.create_pool("default_async", async_pool_config)

    def create_pool(self, pool_name: str, config: PoolConfig) -> bool:
        """Create worker pool"""
        if pool_name in self.pools:
            logger.warning(f"Pool {pool_name} already exists")
            return False

        try:
            pool_info = {
                'config': config,
                'workers': [],
                'task_queue': asyncio.Queue() if config.pool_type == ConcurrencyType.ASYNC_POOL else queue.Queue(),
                'created_at': datetime.now(),
                'tasks_submitted': 0,
                'tasks_completed': 0,
                'tasks_failed': 0
            }

            # Create initial workers
            for i in range(config.min_workers):
                worker_id = f"{pool_name}_worker_{i}"
                worker = Worker(worker_id, config.pool_type)
                self.workers[worker_id] = worker
                pool_info['workers'].append(worker_id)

                # Start worker
                if config.pool_type == ConcurrencyType.ASYNC_POOL:
                    asyncio.create_task(worker.start())
                else:
                    worker.start()

                # Set CPU affinity if enabled
                if self.cpu_affinity_enabled and config.pool_type == ConcurrencyType.PROCESS_POOL:
                    self._set_cpu_affinity(worker_id, i % self.num_cpus)

            self.pools[pool_name] = pool_info

            # Initialize load balancer
            self.load_balancers[pool_name] = LoadBalancer(
                config.load_balancing,
                [self.workers[worker_id] for worker_id in pool_info['workers']]
            )

            logger.info(f"Created pool {pool_name} with {config.min_workers} workers")
            return True

        except Exception as e:
            logger.error(f"Failed to create pool {pool_name}: {e}")
            return False

    def _set_cpu_affinity(self, worker_id: str, cpu_id: int):
        """Set CPU affinity for worker process"""
        try:
            # This is a simplified implementation
            # In practice, you'd need to handle process-specific affinity
            pid = os.getpid()
            os.sched_setaffinity(pid, {cpu_id})
            logger.debug(f"Set CPU affinity for {worker_id} to CPU {cpu_id}")
        except Exception as e:
            logger.warning(f"Failed to set CPU affinity: {e}")

    async def submit_task(self, func: Callable, args: Tuple = (), kwargs: Dict = None,
                         pool_name: str = "default_async", priority: int = 0,
                         timeout: Optional[float] = None) -> asyncio.Future:
        """Submit task for execution"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} not found")

        kwargs = kwargs or {}
        pool_info = self.pools[pool_name]
        config = pool_info['config']

        # Generate task ID
        task_id = str(uuid.uuid4())
        task_timeout = timeout or config.task_timeout

        # Create task
        task = {
            'task_id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'priority': priority,
            'timeout': task_timeout,
            'future': asyncio.Future(),
            'submitted_at': datetime.now(),
            'pool_name': pool_name
        }

        # Select worker using load balancer
        load_balancer = self.load_balancers[pool_name]
        worker = load_balancer.select_worker()

        if worker is None:
            # No available workers, try to scale up if auto-scaling enabled
            if self.auto_scaling and len(pool_info['workers']) < config.max_workers:
                await self._scale_up_pool(pool_name)
                worker = load_balancer.select_worker()

        if worker is None:
            task['future'].set_exception(RuntimeError("No available workers"))
            return task['future']

        # Submit task to worker
        if worker.submit_task(task):
            self.active_tasks[task_id] = task
            pool_info['tasks_submitted'] += 1

            # Add timeout handling
            if task_timeout > 0:
                asyncio.create_task(self._handle_task_timeout(task_id, task_timeout))

            return task['future']
        else:
            task['future'].set_exception(RuntimeError("Worker queue full"))
            return task['future']

    async def _handle_task_timeout(self, task_id: str, timeout: float):
        """Handle task timeout"""
        try:
            await asyncio.sleep(timeout)
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if not task['future'].done():
                    task['future'].set_exception(asyncio.TimeoutError(f"Task timed out after {timeout}s"))
                    del self.active_tasks[task_id]
        except asyncio.CancelledError:
            pass

    async def _scale_up_pool(self, pool_name: str):
        """Scale up worker pool"""
        if pool_name not in self.pools:
            return

        pool_info = self.pools[pool_name]
        config = pool_info['config']

        if len(pool_info['workers']) >= config.max_workers:
            return

        try:
            # Create new worker
            worker_index = len(pool_info['workers'])
            worker_id = f"{pool_name}_worker_{worker_index}"
            worker = Worker(worker_id, config.pool_type)
            self.workers[worker_id] = worker
            pool_info['workers'].append(worker_id)

            # Start worker
            if config.pool_type == ConcurrencyType.ASYNC_POOL:
                await worker.start()
            else:
                worker.start()

            # Update load balancer
            self.load_balancers[pool_name].add_worker(worker)

            logger.info(f"Scaled up pool {pool_name}: added worker {worker_id}")

        except Exception as e:
            logger.error(f"Failed to scale up pool {pool_name}: {e}")

    async def _scale_down_pool(self, pool_name: str):
        """Scale down worker pool"""
        if pool_name not in self.pools:
            return

        pool_info = self.pools[pool_name]
        config = pool_info['config']

        if len(pool_info['workers']) <= config.min_workers:
            return

        try:
            # Find least loaded worker
            load_balancer = self.load_balancers[pool_name]
            worker = load_balancer.remove_least_loaded_worker()

            if worker:
                worker.stop()
                pool_info['workers'].remove(worker.worker_id)
                del self.workers[worker.worker_id]

                logger.info(f"Scaled down pool {pool_name}: removed worker {worker.worker_id}")

        except Exception as e:
            logger.error(f"Failed to scale down pool {pool_name}: {e}")

    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            logger.warning("Concurrency monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Concurrency monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Concurrency monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Monitor worker performance
                self._monitor_worker_performance()

                # Auto-scaling decisions
                if self.auto_scaling:
                    self._make_scaling_decisions()

                # Deadlock detection
                if self.deadlock_detection:
                    self._detect_deadlocks()

                time.sleep(self.config.get('monitoring_interval', 60.0))

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

    def _monitor_worker_performance(self):
        """Monitor worker performance metrics"""
        for worker_id, worker in self.workers.items():
            try:
                # Update worker metrics
                with worker.processing_lock:
                    # Calculate CPU and memory usage (simplified)
                    worker.metrics.memory_usage_mb = 0  # Would need actual memory monitoring
                    worker.metrics.cpu_usage_percent = 0  # Would need actual CPU monitoring

                    # Log performance warnings
                    if worker.metrics.tasks_failed > 0:
                        failure_rate = worker.metrics.tasks_failed / (
                            worker.metrics.tasks_completed + worker.metrics.tasks_failed
                        )
                        if failure_rate > 0.1:  # 10% failure rate
                            logger.warning(f"High failure rate for {worker_id}: {failure_rate:.2%}")

            except Exception as e:
                logger.error(f"Error monitoring worker {worker_id}: {e}")

    def _make_scaling_decisions(self):
        """Make auto-scaling decisions"""
        for pool_name, pool_info in self.pools.items():
            config = pool_info['config']
            current_workers = len(pool_info['workers'])

            # Scale up if high load
            avg_load = np.mean([
                self.workers[worker_id].metrics.current_load
                for worker_id in pool_info['workers']
            ]) if pool_info['workers'] else 0

            if avg_load > 0.8 and current_workers < config.max_workers:
                # Schedule scale up
                asyncio.create_task(self._scale_up_pool(pool_name))

            # Scale down if low load
            elif avg_load < 0.2 and current_workers > config.min_workers:
                # Schedule scale down
                asyncio.create_task(self._scale_down_pool(pool_name))

    def _detect_deadlocks(self):
        """Simple deadlock detection (placeholder)"""
        # This would implement actual deadlock detection logic
        # For now, just log very long-running tasks
        current_time = datetime.now()
        for task_id, task in self.active_tasks.items():
            running_time = (current_time - task['submitted_at']).total_seconds()
            if running_time > self.config.get('task_timeout', 300.0) * 2:
                logger.warning(f"Potential deadlock: task {task_id} running for {running_time:.1f}s")

    def get_pool_status(self, pool_name: str = None) -> Dict[str, Any]:
        """Get pool status information"""
        if pool_name:
            if pool_name not in self.pools:
                return {"error": f"Pool {pool_name} not found"}

            pool_info = self.pools[pool_name]
            config = pool_info['config']

            worker_metrics = []
            for worker_id in pool_info['workers']:
                worker = self.workers[worker_id]
                worker_metrics.append({
                    'worker_id': worker_id,
                    'current_load': worker.metrics.current_load,
                    'tasks_completed': worker.metrics.tasks_completed,
                    'tasks_failed': worker.metrics.tasks_failed,
                    'avg_execution_time': worker.metrics.avg_execution_time
                })

            return {
                'pool_name': pool_name,
                'config': {
                    'pool_type': config.pool_type.value,
                    'min_workers': config.min_workers,
                    'max_workers': config.max_workers,
                    'queue_size': config.queue_size
                },
                'current_workers': len(pool_info['workers']),
                'tasks_submitted': pool_info['tasks_submitted'],
                'tasks_completed': pool_info['tasks_completed'],
                'tasks_failed': pool_info['tasks_failed'],
                'workers': worker_metrics
            }
        else:
            # Return status for all pools
            status = {}
            for name in self.pools.keys():
                status[name] = self.get_pool_status(name)
            return status

    def get_performance_report(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if time_window is None:
            time_window = timedelta(hours=24)

        cutoff_time = datetime.now() - time_window
        recent_tasks = [m for m in self.task_metrics if m.timestamp >= cutoff_time]

        if not recent_tasks:
            return {"error": "No task data available for specified time window"}

        # Calculate statistics
        execution_times = [m.execution_time_ms for m in recent_tasks]
        concurrency_types = defaultdict(list)
        worker_types = defaultdict(list)

        for task in recent_tasks:
            concurrency_types[task.concurrency_type.value].append(task)
            worker_types[task.worker_id].append(task)

        report = {
            'time_window': str(time_window),
            'total_tasks': len(recent_tasks),
            'successful_tasks': len([t for t in recent_tasks if t.success]),
            'failed_tasks': len([t for t in recent_tasks if not t.success]),
            'performance_stats': {
                'avg_execution_time_ms': np.mean(execution_times),
                'median_execution_time_ms': np.median(execution_times),
                'max_execution_time_ms': np.max(execution_times),
                'min_execution_time_ms': np.min(execution_times),
                'std_execution_time_ms': np.std(execution_times)
            },
            'concurrency_type_stats': {
                ctype.value: {
                    'task_count': len(tasks),
                    'avg_execution_time_ms': np.mean([t.execution_time_ms for t in tasks]),
                    'success_rate': len([t for t in tasks if t.success]) / len(tasks)
                }
                for ctype, tasks in concurrency_types.items()
            },
            'pool_stats': {}
        }

        # Pool statistics
        for pool_name, pool_info in self.pools.items():
            pool_tasks = [t for t in recent_tasks if any(w in t.worker_id for w in pool_info['workers'])]
            if pool_tasks:
                report['pool_stats'][pool_name] = {
                    'task_count': len(pool_tasks),
                    'avg_execution_time_ms': np.mean([t.execution_time_ms for t in pool_tasks]),
                    'success_rate': len([t for t in pool_tasks if t.success]) / len(pool_tasks),
                    'current_workers': len(pool_info['workers'])
                }

        # Add recommendations
        report['recommendations'] = self._generate_concurrency_recommendations(recent_tasks)

        return report

    def _generate_concurrency_recommendations(self, tasks: List[TaskMetrics]) -> List[str]:
        """Generate concurrency optimization recommendations"""
        recommendations = []

        if not tasks:
            return recommendations

        # Analyze execution times
        execution_times = [t.execution_time_ms for t in tasks]
        avg_time = np.mean(execution_times)

        if avg_time > 1000:  # 1 second
            recommendations.append("Consider breaking down long-running tasks into smaller subtasks")

        # Analyze failure rates
        failure_rate = len([t for t in tasks if not t.success]) / len(tasks)
        if failure_rate > 0.1:  # 10% failure rate
            recommendations.append("High task failure rate detected. Review error handling and retry logic")

        # Analyze concurrency types
        thread_tasks = [t for t in tasks if t.concurrency_type == ConcurrencyType.THREAD_POOL]
        process_tasks = [t for t in tasks if t.concurrency_type == ConcurrencyType.PROCESS_POOL]

        if thread_tasks and process_tasks:
            thread_avg = np.mean([t.execution_time_ms for t in thread_tasks])
            process_avg = np.mean([t.execution_time_ms for t in process_tasks])

            if thread_avg > process_avg * 2:
                recommendations.append("Consider moving CPU-intensive tasks from thread pool to process pool")

        # Pool utilization
        for pool_name, pool_info in self.pools.items():
            if pool_info['tasks_submitted'] > 0:
                success_rate = pool_info['tasks_completed'] / pool_info['tasks_submitted']
                if success_rate < 0.9:
                    recommendations.append(f"Pool {pool_name} has low success rate. Consider increasing timeouts or resources")

        return recommendations

    async def shutdown_pool(self, pool_name: str, wait_for_completion: bool = True):
        """Shutdown specific pool"""
        if pool_name not in self.pools:
            logger.warning(f"Pool {pool_name} not found")
            return

        pool_info = self.pools[pool_name]

        logger.info(f"Shutting down pool {pool_name}")

        # Stop all workers
        for worker_id in pool_info['workers']:
            if worker_id in self.workers:
                self.workers[worker_id].stop()

        # Wait for tasks to complete if requested
        if wait_for_completion:
            # Wait for active tasks to complete
            for task_id, task in list(self.active_tasks.items()):
                if task['pool_name'] == pool_name:
                    try:
                        await asyncio.wait_for(task['future'], timeout=30.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Task {task_id} did not complete during shutdown")
                    finally:
                        del self.active_tasks[task_id]

        # Clean up
        del self.pools[pool_name]
        if pool_name in self.load_balancers:
            del self.load_balancers[pool_name]

        logger.info(f"Pool {pool_name} shutdown complete")

    async def shutdown_all(self, wait_for_completion: bool = True):
        """Shutdown all pools and workers"""
        logger.info("Shutting down all concurrency pools")

        # Stop monitoring
        self.stop_monitoring()

        # Shutdown all pools
        for pool_name in list(self.pools.keys()):
            await self.shutdown_pool(pool_name, wait_for_completion)

        # Clean up remaining tasks
        for task_id in list(self.active_tasks.keys()):
            task = self.active_tasks[task_id]
            if not task['future'].done():
                task['future'].cancel()
            del self.active_tasks[task_id]

        logger.info("All concurrency pools shutdown complete")

class LoadBalancer:
    """Load balancer for distributing tasks across workers"""

    def __init__(self, strategy: LoadBalancingStrategy, workers: List[Worker]):
        self.strategy = strategy
        self.workers = workers
        self.current_index = 0
        self.response_times = defaultdict(float)

    def select_worker(self) -> Optional[Worker]:
        """Select best worker based on strategy"""
        if not self.workers:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select()
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select()
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select()
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select()
        else:
            return self._round_robin_select()

    def _round_robin_select(self) -> Worker:
        """Round-robin selection"""
        worker = self.workers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.workers)
        return worker

    def _least_connections_select(self) -> Worker:
        """Select worker with least current load"""
        return min(self.workers, key=lambda w: w.metrics.current_load)

    def _least_response_time_select(self) -> Worker:
        """Select worker with best response time"""
        available_workers = [w for w in self.workers if w.metrics.current_load < w.metrics.max_capacity]
        if not available_workers:
            return self._least_connections_select()

        return min(available_workers, key=lambda w: w.metrics.avg_execution_time)

    def _weighted_round_robin_select(self) -> Worker:
        """Weighted round-robin based on performance"""
        # Simple implementation: weight by success rate
        weights = []
        for worker in self.workers:
            total_tasks = worker.metrics.tasks_completed + worker.metrics.tasks_failed
            if total_tasks > 0:
                success_rate = worker.metrics.tasks_completed / total_tasks
                weights.append(max(0.1, success_rate))  # Minimum weight of 0.1
            else:
                weights.append(1.0)

        # Select based on weights
        total_weight = sum(weights)
        if total_weight == 0:
            return self._round_robin_select()

        import random
        rand_val = random.uniform(0, total_weight)
        current_weight = 0

        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_val <= current_weight:
                return self.workers[i]

        return self.workers[0]

    def add_worker(self, worker: Worker):
        """Add worker to load balancer"""
        self.workers.append(worker)

    def remove_worker(self) -> Optional[Worker]:
        """Remove least loaded worker"""
        if not self.workers:
            return None

        worker = self._least_connections_select()
        self.workers.remove(worker)
        return worker

    def remove_least_loaded_worker(self) -> Optional[Worker]:
        """Remove least loaded worker"""
        return self.remove_worker()

# Concurrency decorators
def thread_pool(pool_name: str = "default_thread", priority: int = 0):
    """Decorator for thread pool execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get global concurrency manager (would need to be implemented)
            # For now, just run in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run directly
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def process_pool(pool_name: str = "default_process", priority: int = 0):
    """Decorator for process pool execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get global concurrency manager and submit to process pool
            # This is a simplified implementation
            loop = asyncio.get_event_loop()
            with concurrent.futures.ProcessPoolExecutor() as executor:
                return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))

        return async_wrapper

    return decorator

def async_task(pool_name: str = "default_async", priority: int = 0, timeout: Optional[float] = None):
    """Decorator for async task execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Execute async function
            return await func(*args, **kwargs)

        return async_wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize concurrency manager
        manager = ConcurrencyManager({
            'auto_scaling': True,
            'performance_monitoring': True,
            'default_pool_size': 4
        })

        # Start monitoring
        manager.start_monitoring()

        try:
            # Example tasks
            @thread_pool()
            def cpu_intensive_task(n: int) -> int:
                """CPU intensive task"""
                result = sum(i * i for i in range(n))
                time.sleep(0.1)  # Simulate work
                return result

            @async_task()
            async def io_intensive_task(delay: float) -> str:
                """I/O intensive task"""
                await asyncio.sleep(delay)
                return f"Completed after {delay}s"

            # Submit tasks
            tasks = []
            for i in range(10):
                # Submit CPU intensive task to thread pool
                task1 = manager.submit_task(
                    cpu_intensive_task,
                    args=(10000,),
                    pool_name="default_thread"
                )
                tasks.append(task1)

                # Submit I/O intensive task to async pool
                task2 = manager.submit_task(
                    io_intensive_task,
                    args=(0.1,),
                    pool_name="default_async"
                )
                tasks.append(task2)

            # Wait for results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            print(f"Completed {len([r for r in results if not isinstance(r, Exception)])} tasks successfully")

            # Get pool status
            status = manager.get_pool_status()
            print(f"Pool status: {json.dumps(status, indent=2, default=str)}")

            # Get performance report
            report = manager.get_performance_report()
            print(f"Performance report: {json.dumps(report, indent=2, default=str)}")

            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Cleanup
            await manager.shutdown_all()

    # Run example
    asyncio.run(main())