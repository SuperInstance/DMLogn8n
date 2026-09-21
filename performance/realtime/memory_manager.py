#!/usr/bin/env python3
"""
Memory Manager - Advanced Memory Optimization and Garbage Collection
Optimizes memory usage, prevents leaks, and ensures efficient garbage collection
"""

import gc
import sys
import time
import threading
import weakref
import psutil
import tracemalloc
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import resource
from enum import Enum
import numpy as np
from functools import wraps
import asyncio

class MemoryPressureLevel(Enum):
    """Memory pressure levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    process_memory_mb: float
    process_memory_percent: float
    gc_count: int
    gc_time_ms: float
    objects_count: int
    memory_pressure: MemoryPressureLevel
    timestamp: float

@dataclass
class MemoryPool:
    """Memory pool for efficient allocation"""
    pool_name: str
    initial_size_mb: float
    max_size_mb: float
    allocated_blocks: List[Dict] = field(default_factory=list)
    free_blocks: List[Dict] = field(default_factory=list)
    total_allocated_mb: float = 0.0
    fragmentation_ratio: float = 0.0

@dataclass
class MemoryLeak:
    """Memory leak detection information"""
    object_type: str
    object_id: int
    size_bytes: int
    creation_time: float
    last_seen: float
    ref_count: int
    traceback: List[str] = field(default_factory=list)

class MemoryManager:
    """Advanced memory management and optimization system"""

    def __init__(self, enable_monitoring: bool = True, gc_tuning: bool = True):
        self.enable_monitoring = enable_monitoring
        self.gc_tuning = gc_tuning

        # Memory monitoring
        self.process = psutil.Process()
        self.metrics_history: deque = deque(maxlen=1000)
        self.memory_pools: Dict[str, MemoryPool] = {}

        # Garbage collection optimization
        self.gc_stats = {
            'collections_count': 0,
            'collected_objects': 0,
            'collection_time_ms': 0.0,
            'uncollectable_objects': 0
        }

        # Memory leak detection
        self.object_tracker: Dict[int, Dict] = {}
        self.leaked_objects: List[MemoryLeak] = []
        self.weak_references: Dict[int, weakref.ref] = {}
        self.monitoring_enabled_objects: Set[int] = set()

        # Memory pressure handling
        self.memory_callbacks: List[Callable] = []
        self.memory_pressure_handlers: Dict[MemoryPressureLevel, List[Callable]] = defaultdict(list)

        # Optimization settings
        self.max_memory_mb = 1024.0  # 1GB default limit
        self.gc_thresholds = [700, 100, 10]  # Custom GC thresholds
        self.allocated_objects = defaultdict(int)
        self.deallocated_objects = defaultdict(int)

        # Background tasks
        self.running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.gc_thread: Optional[threading.Thread] = None

        # Setup logging
        self.logger = logging.getLogger("MemoryManager")

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize memory manager"""
        # Start memory tracing
        if self.enable_monitoring:
            tracemalloc.start()

        # Configure garbage collection
        if self.gc_tuning:
            self._configure_garbage_collection()

        # Create default memory pools
        self._create_default_pools()

        # Start background monitoring
        if self.enable_monitoring:
            self._start_monitoring()

    def _configure_garbage_collection(self):
        """Configure garbage collection for optimal performance"""
        # Set custom thresholds
        gc.set_threshold(*self.gc_thresholds)

        # Enable GC debug mode
        gc.set_debug(gc.DEBUG_STATS)

        # Pre-allocate GC objects
        gc.collect()

    def _create_default_pools(self):
        """Create default memory pools"""
        pools = [
            ("small_objects", 50.0, 200.0),    # Small objects pool (50-200MB)
            ("medium_objects", 100.0, 400.0),  # Medium objects pool (100-400MB)
            ("large_objects", 200.0, 800.0),   # Large objects pool (200-800MB)
            ("temp_objects", 50.0, 150.0),     # Temporary objects pool (50-150MB)
        ]

        for name, initial, max_size in pools:
            self.memory_pools[name] = MemoryPool(
                pool_name=name,
                initial_size_mb=initial,
                max_size_mb=max_size
            )

    def _start_monitoring(self):
        """Start background memory monitoring"""
        self.running = True

        # Memory monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryMonitor",
            daemon=True
        )
        self.monitoring_thread.start()

        # Garbage collection optimization thread
        self.gc_thread = threading.Thread(
            target=self._gc_optimization_loop,
            name="GCOptimizer",
            daemon=True
        )
        self.gc_thread.start()

    def allocate_from_pool(self, pool_name: str, size_mb: float,
                          data: Any = None) -> Optional[Dict]:
        """Allocate memory from a specific pool"""
        pool = self.memory_pools.get(pool_name)
        if not pool:
            self.logger.error(f"Memory pool {pool_name} not found")
            return None

        # Check if allocation fits
        if pool.total_allocated_mb + size_mb > pool.max_size_mb:
            self.logger.warning(f"Pool {pool_name} exceeded max size")
            # Try to free some memory
            self._free_pool_memory(pool, size_mb)

        # Find suitable block or create new one
        block = self._find_suitable_block(pool, size_mb)
        if block:
            block['in_use'] = True
            block['data'] = data
            block['last_used'] = time.time()
            pool.total_allocated_mb += size_mb
            return block

        # Create new block
        new_block = {
            'id': f"{pool_name}_{len(pool.allocated_blocks)}",
            'size_mb': size_mb,
            'in_use': True,
            'data': data,
            'created_time': time.time(),
            'last_used': time.time()
        }

        pool.allocated_blocks.append(new_block)
        pool.total_allocated_mb += size_mb

        return new_block

    def deallocate_to_pool(self, pool_name: str, block_id: str):
        """Deallocate memory block back to pool"""
        pool = self.memory_pools.get(pool_name)
        if not pool:
            return

        # Find block
        for block in pool.allocated_blocks:
            if block['id'] == block_id:
                block['in_use'] = False
                block['data'] = None
                pool.total_allocated_mb -= block['size_mb']
                pool.free_blocks.append(block)
                break

    def _find_suitable_block(self, pool: MemoryPool, size_mb: float) -> Optional[Dict]:
        """Find suitable block in pool (best-fit algorithm)"""
        suitable_blocks = [
            block for block in pool.free_blocks
            if block['size_mb'] >= size_mb
        ]

        if not suitable_blocks:
            return None

        # Best-fit: smallest block that fits
        best_block = min(suitable_blocks, key=lambda b: b['size_mb'])
        pool.free_blocks.remove(best_block)
        return best_block

    def _free_pool_memory(self, pool: MemoryPool, needed_mb: float):
        """Free memory from pool to make space"""
        # Sort blocks by last used time (LRU)
        freeable_blocks = [
            block for block in pool.allocated_blocks
            if not block['in_use']
        ]

        freeable_blocks.sort(key=lambda b: b['last_used'])

        freed_mb = 0.0
        for block in freeable_blocks:
            if freed_mb >= needed_mb:
                break

            pool.allocated_blocks.remove(block)
            pool.total_allocated_mb -= block['size_mb']
            freed_mb += block['size_mb']

    def track_object(self, obj: Any, tag: str = "default") -> int:
        """Track object for memory leak detection"""
        obj_id = id(obj)

        # Get traceback
        try:
            import traceback
            tb = traceback.format_stack(limit=5)
        except:
            tb = []

        self.object_tracker[obj_id] = {
            'object': weakref.ref(obj, self._object_finalized),
            'type': type(obj).__name__,
            'size': sys.getsizeof(obj),
            'creation_time': time.time(),
            'last_seen': time.time(),
            'tag': tag,
            'traceback': tb
        }

        self.monitoring_enabled_objects.add(obj_id)
        return obj_id

    def _object_finalized(self, weak_ref: weakref.ref):
        """Called when tracked object is garbage collected"""
        # Find object ID
        obj_id = None
        for oid, info in self.object_tracker.items():
            if info['object'] is weak_ref:
                obj_id = oid
                break

        if obj_id:
            self.monitoring_enabled_objects.discard(obj_id)
            # Keep record for analysis
            self.deallocated_objects[self.object_tracker[obj_id]['type']] += 1

    def detect_memory_leaks(self) -> List[MemoryLeak]:
        """Detect potential memory leaks"""
        current_time = time.time()
        leaks = []

        for obj_id, info in self.object_tracker.items():
            if obj_id in self.monitoring_enabled_objects:
                obj = info['object']()
                if obj is not None:
                    # Check if object has been alive too long
                    age = current_time - info['creation_time']
                    if age > 300:  # 5 minutes threshold
                        leak = MemoryLeak(
                            object_type=info['type'],
                            object_id=obj_id,
                            size_bytes=info['size'],
                            creation_time=info['creation_time'],
                            last_seen=current_time,
                            ref_count=sys.getrefcount(obj),
                            traceback=info['traceback']
                        )
                        leaks.append(leak)

        self.leaked_objects.extend(leaks)
        return leaks

    def force_garbage_collection(self) -> Dict:
        """Force garbage collection and return statistics"""
        start_time = time.time()

        # Collect all generations
        collected = gc.collect()
        collection_time = (time.time() - start_time) * 1000

        # Update statistics
        self.gc_stats['collections_count'] += 1
        self.gc_stats['collected_objects'] += collected
        self.gc_stats['collection_time_ms'] += collection_time
        self.gc_stats['uncollectable_objects'] += len(gc.garbage)

        stats = {
            'collected_objects': collected,
            'collection_time_ms': collection_time,
            'uncollectable_objects': len(gc.garbage),
            'generation_counts': [gc.count() for gen in range(3)],
            'memory_freed_mb': self._calculate_memory_freed()
        }

        self.logger.info(f"Garbage collection completed: {collected} objects, {collection_time:.2f}ms")
        return stats

    def _calculate_memory_freed(self) -> float:
        """Calculate memory freed by garbage collection"""
        # This is simplified - would track memory before/after GC
        return 0.0

    def _monitoring_loop(self):
        """Background memory monitoring loop"""
        while self.running:
            try:
                # Collect memory metrics
                metrics = self._collect_memory_metrics()
                self.metrics_history.append(metrics)

                # Check memory pressure
                self._handle_memory_pressure(metrics)

                # Detect memory leaks periodically
                if len(self.metrics_history) % 60 == 0:  # Every minute
                    leaks = self.detect_memory_leaks()
                    if leaks:
                        self.logger.warning(f"Detected {len(leaks)} potential memory leaks")

                # Optimize memory pools
                self._optimize_memory_pools()

                time.sleep(1)  # Monitor every second

            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")

    def _gc_optimization_loop(self):
        """Background garbage collection optimization loop"""
        while self.running:
            try:
                # Check GC thresholds
                memory_info = self._collect_memory_metrics()

                # Trigger GC based on memory pressure
                if memory_info.memory_pressure == MemoryPressureLevel.HIGH:
                    self.force_garbage_collection()
                elif memory_info.memory_pressure == MemoryPressureLevel.MEDIUM:
                    # Collect only generation 0
                    collected = gc.collect(0)
                    if collected > 1000:
                        self.logger.info(f"Generation 0 GC collected {collected} objects")

                # Optimize GC thresholds
                self._optimize_gc_thresholds()

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.error(f"GC optimization error: {e}")

    def _collect_memory_metrics(self) -> MemoryMetrics:
        """Collect current memory metrics"""
        # System memory
        memory = psutil.virtual_memory()

        # Process memory
        process_memory = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        # GC statistics
        gc_count = sum(gc.count())
        gc_time = self.gc_stats['collection_time_ms']

        # Object count
        object_count = len(gc.get_objects())

        # Memory pressure assessment
        memory_pressure = self._assess_memory_pressure(memory_percent)

        metrics = MemoryMetrics(
            total_memory_mb=memory.total / (1024 * 1024),
            used_memory_mb=memory.used / (1024 * 1024),
            available_memory_mb=memory.available / (1024 * 1024),
            process_memory_mb=process_memory.rss / (1024 * 1024),
            process_memory_percent=memory_percent,
            gc_count=gc_count,
            gc_time_ms=gc_time,
            objects_count=object_count,
            memory_pressure=memory_pressure,
            timestamp=time.time()
        )

        return metrics

    def _assess_memory_pressure(self, memory_percent: float) -> MemoryPressureLevel:
        """Assess current memory pressure level"""
        if memory_percent < 50:
            return MemoryPressureLevel.LOW
        elif memory_percent < 75:
            return MemoryPressureLevel.MEDIUM
        elif memory_percent < 90:
            return MemoryPressureLevel.HIGH
        else:
            return MemoryPressureLevel.CRITICAL

    def _handle_memory_pressure(self, metrics: MemoryMetrics):
        """Handle memory pressure situations"""
        pressure = metrics.memory_pressure

        # Call registered handlers
        for handler in self.memory_pressure_handlers[pressure]:
            try:
                handler(metrics)
            except Exception as e:
                self.logger.error(f"Memory pressure handler error: {e}")

        # Default handling
        if pressure == MemoryPressureLevel.HIGH:
            self.force_garbage_collection()
            self._cleanup_temporary_objects()
        elif pressure == MemoryPressureLevel.CRITICAL:
            self.force_garbage_collection()
            self._emergency_memory_cleanup()

    def _cleanup_temporary_objects(self):
        """Clean up temporary objects and pools"""
        # Clear temp pool
        temp_pool = self.memory_pools.get("temp_objects")
        if temp_pool:
            temp_pool.allocated_blocks.clear()
            temp_pool.free_blocks.clear()
            temp_pool.total_allocated_mb = 0.0

    def _emergency_memory_cleanup(self):
        """Emergency memory cleanup for critical situations"""
        # Force multiple GC collections
        for _ in range(3):
            gc.collect()

        # Clear caches
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()

        # Clear all memory pools
        for pool in self.memory_pools.values():
            pool.allocated_blocks.clear()
            pool.free_blocks.clear()
            pool.total_allocated_mb = 0.0

    def _optimize_memory_pools(self):
        """Optimize memory pool usage"""
        for pool_name, pool in self.memory_pools.items():
            # Calculate fragmentation
            if pool.allocated_blocks:
                total_size = sum(b['size_mb'] for b in pool.allocated_blocks)
                used_size = sum(b['size_mb'] for b in pool.allocated_blocks if b['in_use'])
                if total_size > 0:
                    pool.fragmentation_ratio = (total_size - used_size) / total_size

            # Defragment if needed
            if pool.fragmentation_ratio > 0.3:  # 30% fragmentation
                self._defragment_pool(pool)

    def _defragment_pool(self, pool: MemoryPool):
        """Defragment memory pool"""
        # Simple defragmentation - consolidate free blocks
        pool.free_blocks.sort(key=lambda b: b['size_mb'], reverse=True)

        # Merge adjacent free blocks (simplified)
        i = 0
        while i < len(pool.free_blocks) - 1:
            if pool.free_blocks[i]['size_mb'] == pool.free_blocks[i + 1]['size_mb']:
                # Merge blocks
                pool.free_blocks[i]['size_mb'] += pool.free_blocks[i + 1]['size_mb']
                del pool.free_blocks[i + 1]
            else:
                i += 1

        pool.fragmentation_ratio *= 0.5  # Reduce fragmentation metric

    def _optimize_gc_thresholds(self):
        """Optimize garbage collection thresholds based on usage patterns"""
        if len(self.metrics_history) < 10:
            return

        recent_metrics = list(self.metrics_history)[-10:]

        # Calculate average object count growth
        object_counts = [m.objects_count for m in recent_metrics]
        if len(object_counts) > 1:
            growth_rate = (object_counts[-1] - object_counts[0]) / len(object_counts)

            # Adjust thresholds based on growth rate
            if growth_rate > 1000:  # Fast growth
                self.gc_thresholds = [500, 50, 5]
            elif growth_rate < 100:  # Slow growth
                self.gc_thresholds = [1000, 200, 20]

            gc.set_threshold(*self.gc_thresholds)

    def get_memory_report(self) -> Dict:
        """Generate comprehensive memory report"""
        current_metrics = self._collect_memory_metrics()

        report = {
            'current_metrics': {
                'total_memory_mb': current_metrics.total_memory_mb,
                'used_memory_mb': current_metrics.used_memory_mb,
                'process_memory_mb': current_metrics.process_memory_mb,
                'process_memory_percent': current_metrics.process_memory_percent,
                'objects_count': current_metrics.objects_count,
                'memory_pressure': current_metrics.memory_pressure.value
            },
            'garbage_collection': self.gc_stats.copy(),
            'memory_pools': {},
            'leak_detection': {
                'tracked_objects': len(self.monitoring_enabled_objects),
                'potential_leaks': len(self.leaked_objects),
                'leaked_objects': [
                    {
                        'type': leak.object_type,
                        'size_bytes': leak.size_bytes,
                        'age_seconds': time.time() - leak.creation_time,
                        'ref_count': leak.ref_count
                    }
                    for leak in self.leaked_objects[-10:]  # Last 10 leaks
                ]
            }
        }

        # Add pool information
        for pool_name, pool in self.memory_pools.items():
            report['memory_pools'][pool_name] = {
                'allocated_blocks': len(pool.allocated_blocks),
                'free_blocks': len(pool.free_blocks),
                'total_allocated_mb': pool.total_allocated_mb,
                'max_size_mb': pool.max_size_mb,
                'fragmentation_ratio': pool.fragmentation_ratio,
                'utilization_percent': (pool.total_allocated_mb / pool.max_size_mb) * 100
            }

        # Add trends
        if len(self.metrics_history) > 1:
            recent_metrics = list(self.metrics_history)[-10:]
            memory_trend = [
                m.process_memory_mb for m in recent_metrics
            ]
            report['trends'] = {
                'memory_trend_mb': memory_trend,
                'memory_growth_rate': (memory_trend[-1] - memory_trend[0]) / len(memory_trend) if len(memory_trend) > 1 else 0,
                'avg_objects': sum(m.objects_count for m in recent_metrics) / len(recent_metrics)
            }

        return report

    def register_memory_pressure_handler(self, level: MemoryPressureLevel, handler: Callable):
        """Register handler for memory pressure events"""
        self.memory_pressure_handlers[level].append(handler)

    def optimize_array_allocation(self, shape: tuple, dtype: str = 'float64') -> np.ndarray:
        """Optimize numpy array allocation"""
        # Use appropriate dtype for memory efficiency
        if dtype == 'float64':
            # Check if we can use float32
            dtype = 'float32' if shape else 'float64'

        # Pre-allocate array
        try:
            arr = np.empty(shape, dtype=dtype)
            return arr
        except MemoryError:
            # Try to free memory and retry
            self.force_garbage_collection()
            arr = np.empty(shape, dtype=dtype)
            return arr

    def shutdown(self):
        """Shutdown memory manager"""
        self.running = False

        # Wait for threads
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.gc_thread:
            self.gc_thread.join(timeout=5)

        # Final cleanup
        self.force_garbage_collection()

        # Stop memory tracing
        if self.enable_monitoring and tracemalloc.is_tracing():
            tracemalloc.stop()

        self.logger.info("Memory manager shutdown complete")

# Global memory manager instance
memory_manager = MemoryManager()

# Decorators for memory optimization
def memory_efficient(max_size_mb: float = 10.0):
    """Decorator for memory-efficient functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check memory before execution
            metrics = memory_manager._collect_memory_metrics()
            if metrics.process_memory_mb > max_size_mb:
                memory_manager.force_garbage_collection()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Clean up after execution
                if len(gc.garbage) > 0:
                    gc.collect()

        return wrapper
    return decorator

def track_memory(tag: str = "function"):
    """Decorator to track memory usage of functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Track before
            before_metrics = memory_manager._collect_memory_metrics()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Track after
                after_metrics = memory_manager._collect_memory_metrics()
                execution_time = time.time() - start_time
                memory_delta = after_metrics.process_memory_mb - before_metrics.process_memory_mb

                logging.info(f"Memory tracking [{tag}]: "
                           f"Delta: {memory_delta:.2f}MB, "
                           f"Time: {execution_time:.3f}s, "
                           f"Objects: {after_metrics.objects_count - before_metrics.objects_count}")

                return result

            except Exception as e:
                logging.error(f"Memory tracking error in {func.__name__}: {e}")
                raise

        return wrapper
    return decorator

# Utility functions
def get_memory_usage() -> Dict:
    """Get current memory usage statistics"""
    return memory_manager.get_memory_report()

def cleanup_memory():
    """Force garbage collection and memory cleanup"""
    return memory_manager.force_garbage_collection()

def optimize_memory():
    """Optimize memory usage"""
    memory_manager.force_garbage_collection()
    memory_manager._optimize_memory_pools()