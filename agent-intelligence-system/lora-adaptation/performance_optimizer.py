#!/usr/bin/env python3
"""
Performance Optimization and Resource Management for LoRA Adaptation System
Optimizes computational resources, model loading, and training efficiency
"""

import asyncio
import json
import logging
import time
import gc
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import torch
import numpy as np
from contextlib import contextmanager

# Import our modules
from error_handling import get_logger, safe_execute, log_performance

# Configure logging
logger = get_logger("performance_optimizer")

@dataclass
class ResourceLimits:
    """Resource usage limits"""
    max_memory_mb: int = 4096
    max_gpu_memory_mb: int = 6144
    max_cpu_percent: int = 80
    max_disk_usage_percent: int = 90
    max_concurrent_operations: int = 5

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    operation: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    gpu_memory_before_mb: float
    gpu_memory_after_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str]

class ModelCache:
    """Efficient model caching with LRU eviction"""

    def __init__(self, max_size: int = 5, max_memory_mb: int = 2048):
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.cache = OrderedDict()
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_usage_mb": 0.0
        }
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get model from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                self.cache_stats["misses"] += 1
                logger.debug(f"Cache miss for key: {key}")
                return None

    def put(self, key: str, value: Any, size_mb: float) -> bool:
        """Put model in cache"""
        with self.lock:
            # Check if we need to evict
            while (len(self.cache) >= self.max_size or
                   self.cache_stats["memory_usage_mb"] + size_mb > self.max_memory_mb):
                if not self._evict_least_recently_used():
                    logger.warning("Cannot cache model: cache full and cannot evict")
                    return False

            self.cache[key] = value
            self.cache_stats["memory_usage_mb"] += size_mb
            logger.debug(f"Cached model: {key}, size: {size_mb:.1f}MB")
            return True

    def _evict_least_recently_used(self) -> bool:
        """Evict least recently used item"""
        if not self.cache:
            return False

        oldest_key = next(iter(self.cache))
        oldest_value = self.cache.pop(oldest_key)

        # Estimate memory freed (rough estimation)
        estimated_size = self.cache_stats["memory_usage_mb"] / len(self.cache)
        self.cache_stats["memory_usage_mb"] -= estimated_size
        self.cache_stats["evictions"] += 1

        logger.debug(f"Evicted from cache: {oldest_key}")
        return True

    def clear(self):
        """Clear all cached items"""
        with self.lock:
            self.cache.clear()
            self.cache_stats["memory_usage_mb"] = 0.0
            logger.info("Model cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "memory_usage_mb": self.cache_stats["memory_usage_mb"],
                "max_memory_mb": self.max_memory_mb,
                "hit_rate": hit_rate,
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "evictions": self.cache_stats["evictions"]
            }

class BatchProcessor:
    """Efficient batch processing for operations"""

    def __init__(self, max_batch_size: int = 32, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.pending_operations = defaultdict(list)
        self.batch_locks = defaultdict(threading.Lock)
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def submit_batch_operation(self, operation_type: str, data: Any,
                                   process_function: Callable) -> Any:
        """Submit operation for batch processing"""
        future = asyncio.Future()

        # Add to pending operations
        with self.batch_locks[operation_type]:
            self.pending_operations[operation_type].append((data, process_function, future))

            # Check if we should process the batch
            if len(self.pending_operations[operation_type]) >= self.max_batch_size:
                asyncio.create_task(self._process_batch(operation_type))
            else:
                # Set timeout to process batch anyway
                asyncio.create_task(self._process_batch_with_delay(operation_type))

        return await future

    async def _process_batch_with_delay(self, operation_type: str):
        """Process batch after delay"""
        await asyncio.sleep(self.max_wait_time)
        await self._process_batch(operation_type)

    async def _process_batch(self, operation_type: str):
        """Process a batch of operations"""
        with self.batch_locks[operation_type]:
            if not self.pending_operations[operation_type]:
                return

            # Get batch
            batch = self.pending_operations[operation_type][:self.max_batch_size]
            self.pending_operations[operation_type] = self.pending_operations[operation_type][self.max_batch_size:]

        if not batch:
            return

        try:
            # Extract data and functions
            data_list = [item[0] for item in batch]
            process_functions = [item[1] for item in batch]
            futures = [item[2] for item in batch]

            # Process in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._process_batch_sync,
                data_list,
                process_functions
            )

            # Set results
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)

            logger.debug(f"Processed batch of {len(batch)} operations for {operation_type}")

        except Exception as e:
            # Set error for all futures in batch
            for _, _, future in batch:
                if not future.done():
                    future.set_exception(e)

            logger.error(f"Batch processing failed for {operation_type}: {str(e)}")

    def _process_batch_sync(self, data_list: List[Any], process_functions: List[Callable]) -> List[Any]:
        """Process batch synchronously"""
        results = []
        for data, process_func in zip(data_list, process_functions):
            try:
                result = process_func(data)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results

class ResourceManager:
    """Advanced resource management and optimization"""

    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.model_cache = ModelCache()
        self.batch_processor = BatchProcessor()
        self.performance_history = []
        self.resource_monitor_active = False
        self.optimization_suggestions = []

        # Performance tracking
        self.operation_metrics = defaultdict(list)
        self.resource_snapshots = []

        # Start resource monitoring
        self._start_resource_monitoring()

        logger.info("Resource Manager initialized")

    def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        self.resource_monitor_active = True
        # In production, this would run in a background thread
        # For now, we'll call monitoring manually

    async def monitor_resources(self) -> Dict[str, Any]:
        """Monitor current resource usage"""
        try:
            # System resources
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')

            # GPU resources
            gpu_info = {}
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu_info[f"gpu_{i}"] = {
                        "allocated_mb": torch.cuda.memory_allocated(i) / 1024 / 1024,
                        "cached_mb": torch.cuda.memory_reserved(i) / 1024 / 1024,
                        "utilization_percent": torch.cuda.utilization(i) if hasattr(torch.cuda, 'utilization') else 0,
                        "temperature": torch.cuda.temperature(i) if hasattr(torch.cuda, 'temperature') else None
                    }

            snapshot = {
                "timestamp": datetime.now(),
                "memory": {
                    "total_mb": memory.total / 1024 / 1024,
                    "used_mb": memory.used / 1024 / 1024,
                    "percent": memory.percent,
                    "available_mb": memory.available / 1024 / 1024
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "disk": {
                    "total_mb": disk.total / 1024 / 1024,
                    "used_mb": disk.used / 1024 / 1024,
                    "percent": (disk.used / disk.total) * 100,
                    "free_mb": disk.free / 1024 / 1024
                },
                "gpu": gpu_info,
                "cache_stats": self.model_cache.get_stats()
            }

            # Store snapshot
            self.resource_snapshots.append(snapshot)
            if len(self.resource_snapshots) > 1000:  # Keep last 1000 snapshots
                self.resource_snapshots = self.resource_snapshots[-1000:]

            # Check for resource issues
            issues = self._check_resource_issues(snapshot)
            if issues:
                for issue in issues:
                    logger.warning(f"Resource issue: {issue}")
                    await self._handle_resource_issue(issue, snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Resource monitoring failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now()}

    def _check_resource_issues(self, snapshot: Dict[str, Any]) -> List[str]:
        """Check for resource issues"""
        issues = []

        # Memory issues
        if snapshot["memory"]["percent"] > self.limits.max_memory_mb / 50:  # Rough conversion
            issues.append(f"High memory usage: {snapshot['memory']['percent']:.1f}%")

        # CPU issues
        if snapshot["cpu"]["percent"] > self.limits.max_cpu_percent:
            issues.append(f"High CPU usage: {snapshot['cpu']['percent']:.1f}%")

        # Disk issues
        if snapshot["disk"]["percent"] > self.limits.max_disk_usage_percent:
            issues.append(f"Low disk space: {snapshot['disk']['percent']:.1f}% used")

        # GPU issues
        for gpu_id, gpu_data in snapshot.get("gpu", {}).items():
            usage_percent = (gpu_data["allocated_mb"] / 6144) * 100  # Assume 6GB GPUs
            if usage_percent > 90:
                issues.append(f"High GPU memory usage on {gpu_id}: {usage_percent:.1f}%")

        return issues

    async def _handle_resource_issue(self, issue: str, snapshot: Dict[str, Any]):
        """Handle resource issues automatically"""
        try:
            if "memory" in issue.lower():
                # Memory pressure
                await self._optimize_memory_usage()
            elif "gpu" in issue.lower():
                # GPU memory pressure
                await self._optimize_gpu_memory()
            elif "cpu" in issue.lower():
                # CPU pressure
                await self._optimize_cpu_usage()

        except Exception as e:
            logger.error(f"Failed to handle resource issue: {str(e)}")

    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        # Clear model cache
        self.model_cache.clear()

        # Force garbage collection
        gc.collect()

        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Memory optimization completed")

    async def _optimize_gpu_memory(self):
        """Optimize GPU memory usage"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.info("GPU memory optimization completed")

    async def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        # Reduce batch processing
        self.batch_processor.max_batch_size = max(8, self.batch_processor.max_batch_size // 2)

        logger.info(f"Reduced batch size to {self.batch_processor.max_batch_size} for CPU optimization")

    @contextmanager
    def performance_tracking(self, operation_name: str):
        """Context manager for performance tracking"""
        start_time = datetime.now()

        # Get initial resource state
        memory_before = psutil.virtual_memory().used / 1024 / 1024
        gpu_memory_before = 0
        if torch.cuda.is_available():
            gpu_memory_before = torch.cuda.memory_allocated() / 1024 / 1024

        cpu_before = psutil.cpu_percent()

        try:
            yield
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Get final resource state
            memory_after = psutil.virtual_memory().used / 1024 / 1024
            gpu_memory_after = 0
            if torch.cuda.is_available():
                gpu_memory_after = torch.cuda.memory_allocated() / 1024 / 1024

            cpu_after = psutil.cpu_percent()

            # Create metrics
            metrics = PerformanceMetrics(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                memory_before_mb=memory_before,
                memory_after_mb=memory_after,
                gpu_memory_before_mb=gpu_memory_before,
                gpu_memory_after_mb=gpu_memory_after,
                cpu_usage_percent=(cpu_before + cpu_after) / 2,
                success=success,
                error_message=error_message
            )

            # Store metrics
            self.operation_metrics[operation_name].append(metrics)

            # Keep only recent metrics
            if len(self.operation_metrics[operation_name]) > 1000:
                self.operation_metrics[operation_name] = self.operation_metrics[operation_name][-1000:]

            # Log performance
            log_performance(
                "resource_manager",
                operation_name,
                duration_ms,
                {
                    "success": success,
                    "memory_delta_mb": memory_after - memory_before,
                    "gpu_memory_delta_mb": gpu_memory_after - gpu_memory_before
                }
            )

    def get_performance_analysis(self, operation_name: str = None,
                               hours: int = 24) -> Dict[str, Any]:
        """Get performance analysis for operations"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            if operation_name:
                operations = self.operation_metrics.get(operation_name, [])
            else:
                # Flatten all operations
                operations = []
                for ops in self.operation_metrics.values():
                    operations.extend(ops)

            # Filter by time
            recent_operations = [op for op in operations if op.start_time > cutoff_time]

            if not recent_operations:
                return {"error": "No operations found in specified time period"}

            # Calculate statistics
            durations = [op.duration_ms for op in recent_operations]
            success_rate = sum(1 for op in recent_operations if op.success) / len(recent_operations)

            memory_deltas = [op.memory_after_mb - op.memory_before_mb for op in recent_operations]

            analysis = {
                "operation_name": operation_name or "all",
                "period_hours": hours,
                "total_operations": len(recent_operations),
                "success_rate": success_rate,
                "duration_stats": {
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "avg_ms": np.mean(durations),
                    "median_ms": np.median(durations),
                    "std_ms": np.std(durations)
                },
                "memory_stats": {
                    "avg_delta_mb": np.mean(memory_deltas),
                    "max_delta_mb": max(memory_deltas),
                    "min_delta_mb": min(memory_deltas)
                }
            }

            # Identify performance issues
            performance_issues = []

            if np.mean(durations) > 5000:  # 5 seconds
                performance_issues.append("High average operation duration")

            if success_rate < 0.9:
                performance_issues.append(f"Low success rate: {success_rate:.1%}")

            if np.mean(memory_deltas) > 100:  # 100MB average increase
                performance_issues.append("High memory usage growth")

            analysis["performance_issues"] = performance_issues

            # Generate optimization suggestions
            analysis["optimization_suggestions"] = self._generate_optimization_suggestions(
                operation_name, analysis
            )

            return analysis

        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            return {"error": str(e)}

    def _generate_optimization_suggestions(self, operation_name: str,
                                         analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on performance analysis"""
        suggestions = []

        # Duration-based suggestions
        avg_duration = analysis["duration_stats"]["avg_ms"]
        if avg_duration > 3000:  # 3 seconds
            suggestions.append("Consider increasing batch processing efficiency")
            suggestions.append("Optimize model loading and caching")
            suggestions.append("Consider using smaller models for faster inference")

        # Memory-based suggestions
        avg_memory_delta = analysis["memory_stats"]["avg_delta_mb"]
        if avg_memory_delta > 50:  # 50MB
            suggestions.append("Implement more aggressive memory cleanup")
            suggestions.append("Consider model quantization")
            suggestions.append("Optimize data structures to reduce memory footprint")

        # Success rate suggestions
        if analysis["success_rate"] < 0.95:
            suggestions.append("Review error handling and retry mechanisms")
            suggestions.append("Implement better resource monitoring")
            suggestions.append("Consider circuit breaker patterns for failing operations")

        # General suggestions
        if not suggestions:
            suggestions.append("Performance is within acceptable ranges")
            suggestions.append("Continue monitoring for optimization opportunities")

        return suggestions

    async def optimize_system(self) -> Dict[str, Any]:
        """Perform comprehensive system optimization"""
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "actions_performed": [],
                "resources_freed": {},
                "performance_improvements": {}
            }

            # Get current resource state
            before_snapshot = await self.monitor_resources()

            # Memory optimization
            memory_before = before_snapshot["memory"]["used_mb"]
            await self._optimize_memory_usage()
            after_snapshot = await self.monitor_resources()
            memory_freed = memory_before - after_snapshot["memory"]["used_mb"]

            if memory_freed > 10:  # More than 10MB freed
                optimization_results["actions_performed"].append("Memory optimization")
                optimization_results["resources_freed"]["memory_mb"] = memory_freed

            # GPU memory optimization
            if torch.cuda.is_available():
                gpu_before = sum(gpu["allocated_mb"] for gpu in before_snapshot.get("gpu", {}).values())
                await self._optimize_gpu_memory()
                gpu_after = sum(gpu["allocated_mb"] for gpu in after_snapshot.get("gpu", {}).values())
                gpu_freed = gpu_before - gpu_after

                if gpu_freed > 10:
                    optimization_results["actions_performed"].append("GPU memory optimization")
                    optimization_results["resources_freed"]["gpu_memory_mb"] = gpu_freed

            # Cache optimization
            cache_stats_before = before_snapshot["cache_stats"]
            if cache_stats_before["hit_rate"] < 0.5:  # Low hit rate
                # Clear and reset cache
                self.model_cache.clear()
                optimization_results["actions_performed"].append("Cache optimization")

            # Performance analysis
            performance_analysis = self.get_performance_analysis(hours=1)
            if "optimization_suggestions" in performance_analysis:
                optimization_results["optimization_suggestions"] = performance_analysis["optimization_suggestions"]

            logger.info(f"System optimization completed: {len(optimization_results['actions_performed'])} actions performed")
            return optimization_results

        except Exception as e:
            logger.error(f"System optimization failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_resource_efficiency_report(self) -> Dict[str, Any]:
        """Generate comprehensive resource efficiency report"""
        try:
            current_snapshot = asyncio.run(self.monitor_resources())

            report = {
                "timestamp": datetime.now().isoformat(),
                "current_resources": current_snapshot,
                "cache_efficiency": self.model_cache.get_stats(),
                "performance_summary": {},
                "efficiency_score": 0.0,
                "recommendations": []
            }

            # Calculate efficiency score
            memory_efficiency = 1.0 - (current_snapshot["memory"]["percent"] / 100)
            cpu_efficiency = 1.0 - (current_snapshot["cpu"]["percent"] / 100)
            cache_efficiency = self.model_cache.get_stats()["hit_rate"]

            report["efficiency_score"] = (memory_efficiency + cpu_efficiency + cache_efficiency) / 3

            # Generate recommendations
            if memory_efficiency < 0.7:
                report["recommendations"].append("Memory usage is high, consider optimization")

            if cpu_efficiency < 0.7:
                report["recommendations"].append("CPU usage is high, consider load balancing")

            if cache_efficiency < 0.5:
                report["recommendations"].append("Cache hit rate is low, review caching strategy")

            if report["efficiency_score"] > 0.8:
                report["recommendations"].append("System is running efficiently")

            return report

        except Exception as e:
            logger.error(f"Failed to generate efficiency report: {str(e)}")
            return {"error": str(e)}

# Global resource manager instance
resource_manager = ResourceManager()

# Decorator for performance optimization
@safe_execute(component="performance_optimizer")
def optimize_performance(operation_name: str = None):
    """Decorator for automatic performance optimization"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            with resource_manager.performance_tracking(op_name):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            with resource_manager.performance_tracking(op_name):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Utility functions
async def get_cached_model(model_key: str, load_function: Callable,
                          size_estimate_mb: float = 100) -> Any:
    """Get model from cache or load and cache it"""
    cached_model = resource_manager.model_cache.get(model_key)
    if cached_model is not None:
        return cached_model

    # Load model
    model = await load_function()

    # Cache if possible
    resource_manager.model_cache.put(model_key, model, size_estimate_mb)

    return model

async def optimize_resources_if_needed():
    """Optimize resources if usage is high"""
    snapshot = await resource_manager.monitor_resources()

    # Check if optimization is needed
    if (snapshot["memory"]["percent"] > 85 or
        snapshot["cpu"]["percent"] > 85 or
        any(gpu["allocated_mb"] > 5500 for gpu in snapshot.get("gpu", {}).values())):

        await resource_manager.optimize_system()
        return True

    return False

# Main execution for testing
if __name__ == "__main__":
    async def main():
        # Test resource monitoring
        snapshot = await resource_manager.monitor_resources()
        print(f"Resource snapshot: {json.dumps(snapshot, indent=2, default=str)}")

        # Test performance tracking
        @optimize_performance("test_operation")
        async def test_operation():
            await asyncio.sleep(0.1)
            return "Operation completed"

        result = await test_operation()
        print(f"Test result: {result}")

        # Test performance analysis
        analysis = resource_manager.get_performance_analysis()
        print(f"Performance analysis: {json.dumps(analysis, indent=2)}")

        # Test system optimization
        optimization = await resource_manager.optimize_system()
        print(f"Optimization results: {json.dumps(optimization, indent=2)}")

        # Test efficiency report
        report = resource_manager.get_resource_efficiency_report()
        print(f"Efficiency report: {json.dumps(report, indent=2)}")

    asyncio.run(main())