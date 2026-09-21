#!/usr/bin/env python3
"""
Advanced Resource Optimizer for DMLogn8n Platform
Dynamic CPU, memory, and GPU resource allocation and optimization
"""

import asyncio
import gc
import logging
import math
import os
import psutil
import signal
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# GPU libraries (optional)
try:
    import GPUtil
    import torch
    import nvidia_ml_py3 as nvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Resource types for optimization"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"

class OptimizationStrategy(Enum):
    """Optimization strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

@dataclass
class ResourceLimits:
    """Resource limits configuration"""
    cpu_min_percent: float = 10.0
    cpu_max_percent: float = 90.0
    memory_min_percent: float = 10.0
    memory_max_percent: float = 85.0
    disk_io_max_mb_per_sec: float = 100.0
    network_io_max_mb_per_sec: float = 50.0
    gpu_min_memory_percent: float = 10.0
    gpu_max_memory_percent: float = 90.0

@dataclass
class ResourceUsage:
    """Current resource usage snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_recv_mb: float
    network_io_sent_mb: float
    gpu_usage: List[Dict[str, float]] = field(default_factory=list)
    process_count: int
    thread_count: int
    load_average: float = 0.0

@dataclass
class ResourceAllocation:
    """Resource allocation configuration"""
    cpu_cores: int
    memory_gb: float
    gpu_count: int = 0
    gpu_memory_gb: float = 0.0
    priority: int = 0
    max_processes: int = 100
    max_threads_per_process: int = 50

class ResourceOptimizer:
    """Advanced resource optimization and management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.limits = ResourceLimits(**self.config.get('limits', {}))
        self.strategy = OptimizationStrategy(self.config.get('strategy', 'balanced'))

        # Resource monitoring
        self.usage_history = deque(maxlen=self.config.get('history_size', 1000))
        self.allocation_history = deque(maxlen=100)

        # Optimization state
        self.optimization_active = False
        self.optimization_thread = None
        self.current_allocation = None

        # Process management
        self.managed_processes = {}
        self.process_pool = None
        self.thread_pool = None

        # GPU management
        self.gpu_devices = []
        self.gpu_manager = None
        if GPU_AVAILABLE:
            self._initialize_gpu_management()

        # Performance tuning
        self.tuning_profiles = self._load_tuning_profiles()
        self.active_tuning = None

        # Resource quotas
        self.quotas = self.config.get('quotas', {})

        # Optimization callbacks
        self.optimization_callbacks = []

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'strategy': 'balanced',
            'history_size': 1000,
            'optimization_interval': 30.0,
            'monitoring_interval': 5.0,
            'auto_tuning': True,
            'process_management': True,
            'gpu_optimization': GPU_AVAILABLE,
            'limits': {
                'cpu_min_percent': 10.0,
                'cpu_max_percent': 90.0,
                'memory_min_percent': 10.0,
                'memory_max_percent': 85.0,
                'disk_io_max_mb_per_sec': 100.0,
                'network_io_max_mb_per_sec': 50.0
            },
            'quotas': {
                'max_cpu_cores': None,
                'max_memory_gb': None,
                'max_gpu_count': None
            },
            'tuning_profiles': {
                'web_server': {'cpu_priority': 0.7, 'memory_priority': 0.6},
                'ai_inference': {'cpu_priority': 0.8, 'memory_priority': 0.9, 'gpu_priority': 1.0},
                'data_processing': {'cpu_priority': 0.9, 'memory_priority': 0.8, 'io_priority': 0.7}
            }
        }

    def _initialize_gpu_management(self):
        """Initialize GPU management if available"""
        try:
            if GPU_AVAILABLE:
                # Initialize NVML for detailed GPU monitoring
                nvml.nvmlInit()
                device_count = nvml.nvmlDeviceGetCount()

                for i in range(device_count):
                    handle = nvml.nvmlDeviceGetHandleByIndex(i)
                    name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)

                    self.gpu_devices.append({
                        'id': i,
                        'name': name,
                        'handle': handle,
                        'total_memory_gb': memory_info.total / 1024 / 1024 / 1024,
                        'utilization': 0.0,
                        'memory_used': 0.0,
                        'temperature': 0.0,
                        'power_usage': 0.0
                    })

                logger.info(f"Initialized {len(self.gpu_devices)} GPU devices")

                # Initialize PyTorch if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        except Exception as e:
            logger.warning(f"Failed to initialize GPU management: {e}")
            self.gpu_devices = []

    def _load_tuning_profiles(self) -> Dict[str, Dict[str, float]]:
        """Load performance tuning profiles"""
        return self.config.get('tuning_profiles', {})

    def start_optimization(self):
        """Start resource optimization"""
        if self.optimization_active:
            logger.warning("Resource optimization is already active")
            return

        self.optimization_active = True
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()

        # Initialize resource pools
        self._initialize_resource_pools()

        logger.info("Resource optimization started")

    def stop_optimization(self):
        """Stop resource optimization"""
        self.optimization_active = False

        if self.optimization_thread:
            self.optimization_thread.join(timeout=10)

        # Cleanup resource pools
        self._cleanup_resource_pools()

        logger.info("Resource optimization stopped")

    def _initialize_resource_pools(self):
        """Initialize process and thread pools"""
        # Determine optimal pool sizes based on system resources
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024

        max_workers = min(cpu_count, math.floor(memory_gb / 2))  # 2GB per worker minimum

        self.thread_pool = ThreadPoolExecutor(
            max_workers=max_workers * 2,
            thread_name_prefix="ResourceOpt"
        )

        self.process_pool = ProcessPoolExecutor(
            max_workers=max_workers,
        )

        logger.info(f"Initialized resource pools: {max_workers} processes, {max_workers * 2} threads")

    def _cleanup_resource_pools(self):
        """Cleanup resource pools"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)

        if self.process_pool:
            self.process_pool.shutdown(wait=True)

    def _optimization_loop(self):
        """Main optimization loop"""
        last_optimization = time.time()

        while self.optimization_active:
            try:
                # Collect current resource usage
                usage = self._collect_resource_usage()
                self.usage_history.append(usage)

                # Check if optimization is needed
                current_time = time.time()
                if current_time - last_optimization >= self.config.get('optimization_interval', 30.0):
                    self._perform_optimization()
                    last_optimization = current_time

                # Apply continuous tuning
                if self.config.get('auto_tuning'):
                    self._apply_continuous_tuning(usage)

                time.sleep(self.config.get('monitoring_interval', 5.0))

            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                time.sleep(10)

    def _collect_resource_usage(self) -> ResourceUsage:
        """Collect current resource usage"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1.0)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_available_gb = memory.available / 1024 / 1024 / 1024

        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / 1024 / 1024 if disk_io else 0
        disk_io_write_mb = disk_io.write_bytes / 1024 / 1024 if disk_io else 0

        # Network I/O metrics
        network_io = psutil.net_io_counters()
        network_io_recv_mb = network_io.bytes_recv / 1024 / 1024 if network_io else 0
        network_io_sent_mb = network_io.bytes_sent / 1024 / 1024 if network_io else 0

        # Process metrics
        process_count = len(psutil.pids())
        current_process = psutil.Process()
        thread_count = current_process.num_threads()

        # GPU metrics
        gpu_usage = []
        if GPU_AVAILABLE and self.gpu_devices:
            gpu_usage = self._collect_gpu_usage()

        return ResourceUsage(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_gb=memory_available_gb,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_recv_mb=network_io_recv_mb,
            network_io_sent_mb=network_io_sent_mb,
            gpu_usage=gpu_usage,
            process_count=process_count,
            thread_count=thread_count,
            load_average=load_avg
        )

    def _collect_gpu_usage(self) -> List[Dict[str, float]]:
        """Collect GPU usage metrics"""
        gpu_usage = []

        try:
            if GPU_AVAILABLE:
                for gpu in self.gpu_devices:
                    handle = gpu['handle']

                    # Get utilization
                    utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = utilization.gpu

                    # Get memory usage
                    memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_used = (memory_info.used / memory_info.total) * 100

                    # Get temperature
                    try:
                        temperature = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                    except:
                        temperature = 0.0

                    # Get power usage
                    try:
                        power_usage = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    except:
                        power_usage = 0.0

                    gpu_usage.append({
                        'gpu_id': gpu['id'],
                        'utilization': gpu_util,
                        'memory_usage': memory_used,
                        'temperature': temperature,
                        'power_usage': power_usage
                    })
        except Exception as e:
            logger.warning(f"Error collecting GPU usage: {e}")

        return gpu_usage

    def _perform_optimization(self):
        """Perform comprehensive resource optimization"""
        if not self.usage_history:
            return

        # Analyze recent usage patterns
        recent_usage = list(self.usage_history)[-10:]

        # Identify optimization opportunities
        optimizations = self._identify_optimization_opportunities(recent_usage)

        # Apply optimizations
        for optimization in optimizations:
            self._apply_optimization(optimization)

    def _identify_optimization_opportunities(self, usage_data: List[ResourceUsage]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities based on usage data"""
        optimizations = []

        if not usage_data:
            return optimizations

        # Calculate averages
        avg_cpu = np.mean([u.cpu_percent for u in usage_data])
        avg_memory = np.mean([u.memory_percent for u in usage_data])
        avg_disk_io = np.mean([u.disk_io_read_mb + u.disk_io_write_mb for u in usage_data])
        avg_network_io = np.mean([u.network_io_recv_mb + u.network_io_sent_mb for u in usage_data])

        # CPU optimization opportunities
        if avg_cpu > self.limits.cpu_max_percent:
            optimizations.append({
                'type': 'cpu_optimization',
                'severity': 'high',
                'current_usage': avg_cpu,
                'threshold': self.limits.cpu_max_percent,
                'actions': ['reduce_process_priority', 'optimize_cpu_intensive_tasks', 'scale_horizontal']
            })
        elif avg_cpu > self.limits.cpu_max_percent * 0.8:
            optimizations.append({
                'type': 'cpu_optimization',
                'severity': 'medium',
                'current_usage': avg_cpu,
                'threshold': self.limits.cpu_max_percent,
                'actions': ['optimize_cpu_intensive_tasks']
            })

        # Memory optimization opportunities
        if avg_memory > self.limits.memory_max_percent:
            optimizations.append({
                'type': 'memory_optimization',
                'severity': 'high',
                'current_usage': avg_memory,
                'threshold': self.limits.memory_max_percent,
                'actions': ['force_garbage_collection', 'reduce_cache_sizes', 'optimize_memory_usage']
            })
        elif avg_memory > self.limits.memory_max_percent * 0.8:
            optimizations.append({
                'type': 'memory_optimization',
                'severity': 'medium',
                'current_usage': avg_memory,
                'threshold': self.limits.memory_max_percent,
                'actions': ['garbage_collection', 'reduce_cache_sizes']
            })

        # Disk I/O optimization opportunities
        if avg_disk_io > self.limits.disk_io_max_mb_per_sec:
            optimizations.append({
                'type': 'disk_io_optimization',
                'severity': 'high',
                'current_usage': avg_disk_io,
                'threshold': self.limits.disk_io_max_mb_per_sec,
                'actions': ['optimize_disk_operations', 'increase_caching', 'batch_io_operations']
            })

        # Network I/O optimization opportunities
        if avg_network_io > self.limits.network_io_max_mb_per_sec:
            optimizations.append({
                'type': 'network_io_optimization',
                'severity': 'high',
                'current_usage': avg_network_io,
                'threshold': self.limits.network_io_max_mb_per_sec,
                'actions': ['optimize_network_operations', 'enable_compression', 'batch_requests']
            })

        # GPU optimization opportunities
        if GPU_AVAILABLE and self.gpu_devices:
            for gpu_usage in usage_data[-1].gpu_usage:
                if gpu_usage['utilization'] > self.limits.gpu_max_memory_percent:
                    optimizations.append({
                        'type': 'gpu_optimization',
                        'severity': 'medium',
                        'gpu_id': gpu_usage['gpu_id'],
                        'current_usage': gpu_usage['utilization'],
                        'threshold': self.limits.gpu_max_memory_percent,
                        'actions': ['optimize_gpu_memory', 'batch_gpu_operations']
                    })

        return optimizations

    def _apply_optimization(self, optimization: Dict[str, Any]):
        """Apply optimization strategies"""
        logger.info(f"Applying optimization: {optimization['type']}")

        for action in optimization['actions']:
            try:
                if action == 'force_garbage_collection':
                    self._force_garbage_collection()
                elif action == 'reduce_process_priority':
                    self._reduce_process_priority()
                elif action == 'reduce_cache_sizes':
                    self._reduce_cache_sizes()
                elif action == 'optimize_cpu_intensive_tasks':
                    self._optimize_cpu_intensive_tasks()
                elif action == 'optimize_memory_usage':
                    self._optimize_memory_usage()
                elif action == 'optimize_disk_operations':
                    self._optimize_disk_operations()
                elif action == 'optimize_network_operations':
                    self._optimize_network_operations()
                elif action == 'optimize_gpu_memory':
                    self._optimize_gpu_memory(optimization.get('gpu_id'))
                elif action == 'batch_io_operations':
                    self._batch_io_operations()
                elif action == 'batch_gpu_operations':
                    self._batch_gpu_operations()
                elif action == 'enable_compression':
                    self._enable_compression()
                elif action == 'increase_caching':
                    self._increase_caching()
                elif action == 'scale_horizontal':
                    self._scale_horizontal()

            except Exception as e:
                logger.error(f"Failed to apply optimization action '{action}': {e}")

        # Log optimization
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'optimization': optimization,
            'status': 'applied'
        })

    def _force_garbage_collection(self):
        """Force garbage collection to free memory"""
        logger.info("Forcing garbage collection")

        # Collect garbage multiple times
        for generation in range(3):
            collected = gc.collect()
            logger.debug(f"Garbage collection generation {generation}: collected {collected} objects")

    def _reduce_process_priority(self):
        """Reduce priority of non-essential processes"""
        logger.info("Reducing process priorities")

        try:
            current_process = psutil.Process()

            # Set nice level (lower priority = higher nice value)
            current_process.nice(10)  # Lower priority

            # Set I/O priority
            if hasattr(current_process, 'ionice'):
                current_process.ionice(psutil.IOPRIO_CLASS_BE, value=7)  # Lowest I/O priority

        except Exception as e:
            logger.error(f"Failed to reduce process priority: {e}")

    def _reduce_cache_sizes(self):
        """Reduce cache sizes to free memory"""
        logger.info("Reducing cache sizes")

        # Trigger callbacks for cache reduction
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'reduce_cache', 'reason': 'high_memory_usage'})
            except Exception as e:
                logger.error(f"Cache reduction callback failed: {e}")

    def _optimize_cpu_intensive_tasks(self):
        """Optimize CPU-intensive tasks"""
        logger.info("Optimizing CPU-intensive tasks")

        # Trigger callbacks for CPU optimization
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'optimize_cpu', 'reason': 'high_cpu_usage'})
            except Exception as e:
                logger.error(f"CPU optimization callback failed: {e}")

    def _optimize_memory_usage(self):
        """Optimize memory usage patterns"""
        logger.info("Optimizing memory usage")

        # Clear GPU memory if available
        if GPU_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _optimize_disk_operations(self):
        """Optimize disk operations"""
        logger.info("Optimizing disk operations")

        # Trigger callbacks for disk optimization
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'optimize_disk', 'reason': 'high_disk_io'})
            except Exception as e:
                logger.error(f"Disk optimization callback failed: {e}")

    def _optimize_network_operations(self):
        """Optimize network operations"""
        logger.info("Optimizing network operations")

        # Trigger callbacks for network optimization
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'optimize_network', 'reason': 'high_network_io'})
            except Exception as e:
                logger.error(f"Network optimization callback failed: {e}")

    def _optimize_gpu_memory(self, gpu_id: int = None):
        """Optimize GPU memory usage"""
        if not GPU_AVAILABLE:
            return

        logger.info(f"Optimizing GPU memory (GPU {gpu_id if gpu_id else 'all'})")

        try:
            if torch.cuda.is_available():
                # Clear GPU cache
                torch.cuda.empty_cache()

                # Reset GPU memory stats
                torch.cuda.reset_peak_memory_stats()

                if gpu_id is not None:
                    torch.cuda.set_device(gpu_id)
                    torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to optimize GPU memory: {e}")

    def _batch_io_operations(self):
        """Batch I/O operations for better efficiency"""
        logger.info("Enabling I/O batching")

        # This would integrate with application-specific I/O batching
        pass

    def _batch_gpu_operations(self):
        """Batch GPU operations for better efficiency"""
        logger.info("Enabling GPU operation batching")

        # This would integrate with application-specific GPU batching
        pass

    def _enable_compression(self):
        """Enable data compression for network operations"""
        logger.info("Enabling compression")

        # Trigger callbacks for compression
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'enable_compression', 'reason': 'high_network_io'})
            except Exception as e:
                logger.error(f"Compression callback failed: {e}")

    def _increase_caching(self):
        """Increase caching to reduce I/O operations"""
        logger.info("Increasing caching")

        # Trigger callbacks for cache increase
        for callback in self.optimization_callbacks:
            try:
                callback({'type': 'increase_cache', 'reason': 'high_disk_io'})
            except Exception as e:
                logger.error(f"Cache increase callback failed: {e}")

    def _scale_horizontal(self):
        """Scale horizontally by distributing load"""
        logger.info("Triggering horizontal scaling")

        # This would integrate with orchestration systems like Kubernetes
        pass

    def _apply_continuous_tuning(self, usage: ResourceUsage):
        """Apply continuous performance tuning"""
        if self.active_tuning:
            profile = self.tuning_profiles.get(self.active_tuning)
            if profile:
                self._apply_tuning_profile(profile, usage)

    def _apply_tuning_profile(self, profile: Dict[str, float], usage: ResourceUsage):
        """Apply a specific tuning profile"""
        # CPU tuning
        if 'cpu_priority' in profile:
            cpu_target = profile['cpu_priority'] * 100
            if usage.cpu_percent > cpu_target:
                self._reduce_process_priority()

        # Memory tuning
        if 'memory_priority' in profile:
            memory_target = profile['memory_priority'] * 100
            if usage.memory_percent > memory_target:
                self._force_garbage_collection()

        # GPU tuning
        if 'gpu_priority' in profile and usage.gpu_usage:
            gpu_target = profile['gpu_priority'] * 100
            for gpu in usage.gpu_usage:
                if gpu['utilization'] > gpu_target:
                    self._optimize_gpu_memory(gpu['gpu_id'])

    def allocate_resources(self, request: Dict[str, Any]) -> ResourceAllocation:
        """Allocate resources for a specific task or service"""
        # Check current availability
        current_usage = self._collect_resource_usage()

        # Calculate available resources
        available_cpu = max(0, 100 - current_usage.cpu_percent)
        available_memory = current_usage.memory_available_gb
        available_gpus = len([g for g in current_usage.gpu_usage if g['utilization'] < 50])

        # Apply quotas
        max_cpu = self.quotas.get('max_cpu_cores', psutil.cpu_count())
        max_memory = self.quotas.get('max_memory_gb', psutil.virtual_memory().total / 1024 / 1024 / 1024)
        max_gpus = self.quotas.get('max_gpu_count', len(self.gpu_devices))

        # Calculate allocation
        cpu_cores = min(request.get('cpu_cores', 1),
                       max_cpu,
                       int(available_cpu / 100 * psutil.cpu_count()))

        memory_gb = min(request.get('memory_gb', 1.0),
                       max_memory,
                       available_memory * 0.8)  # Leave 20% buffer

        gpu_count = min(request.get('gpu_count', 0),
                       max_gpus,
                       available_gpus)

        allocation = ResourceAllocation(
            cpu_cores=max(1, cpu_cores),
            memory_gb=max(0.5, memory_gb),
            gpu_count=gpu_count,
            priority=request.get('priority', 0),
            max_processes=request.get('max_processes', 50),
            max_threads_per_process=request.get('max_threads_per_process', 10)
        )

        self.current_allocation = allocation
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'allocation': allocation,
            'request': request
        })

        return allocation

    def release_resources(self, allocation_id: str):
        """Release allocated resources"""
        logger.info(f"Releasing resources for allocation {allocation_id}")

        # This would clean up any resources allocated to the specific allocation
        pass

    def add_optimization_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for optimization events"""
        self.optimization_callbacks.append(callback)

    def remove_optimization_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove optimization callback"""
        if callback in self.optimization_callbacks:
            self.optimization_callbacks.remove(callback)

    def set_tuning_profile(self, profile_name: str):
        """Set active tuning profile"""
        if profile_name in self.tuning_profiles:
            self.active_tuning = profile_name
            logger.info(f"Set tuning profile to: {profile_name}")
        else:
            logger.warning(f"Unknown tuning profile: {profile_name}")

    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status and recommendations"""
        if not self.usage_history:
            return {"error": "No usage data available"}

        current_usage = self.usage_history[-1]

        # Calculate statistics
        recent_usage = list(self.usage_history)[-60:]  # Last 60 samples

        status = {
            'timestamp': current_usage.timestamp.isoformat(),
            'current_usage': {
                'cpu_percent': current_usage.cpu_percent,
                'memory_percent': current_usage.memory_percent,
                'memory_available_gb': current_usage.memory_available_gb,
                'disk_io_mb_per_sec': current_usage.disk_io_read_mb + current_usage.disk_io_write_mb,
                'network_io_mb_per_sec': current_usage.network_io_recv_mb + current_usage.network_io_sent_mb,
                'process_count': current_usage.process_count,
                'thread_count': current_usage.thread_count,
                'load_average': current_usage.load_average
            },
            'gpu_usage': current_usage.gpu_usage,
            'limits': {
                'cpu_max_percent': self.limits.cpu_max_percent,
                'memory_max_percent': self.limits.memory_max_percent,
                'disk_io_max_mb_per_sec': self.limits.disk_io_max_mb_per_sec,
                'network_io_max_mb_per_sec': self.limits.network_io_max_mb_per_sec
            },
            'optimization_status': {
                'active': self.optimization_active,
                'strategy': self.strategy.value,
                'active_tuning': self.active_tuning,
                'last_optimization': self.allocation_history[-1]['timestamp'].isoformat() if self.allocation_history else None
            },
            'quotas': self.quotas,
            'current_allocation': self.current_allocation.__dict__ if self.current_allocation else None
        }

        # Add recommendations
        status['recommendations'] = self._generate_status_recommendations(current_usage)

        return status

    def _generate_status_recommendations(self, usage: ResourceUsage) -> List[str]:
        """Generate recommendations based on current status"""
        recommendations = []

        if usage.cpu_percent > self.limits.cpu_max_percent * 0.8:
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")

        if usage.memory_percent > self.limits.memory_max_percent * 0.8:
            recommendations.append("Monitor memory usage and consider optimization or scaling")

        if usage.disk_io_read_mb + usage.disk_io_write_mb > self.limits.disk_io_max_mb_per_sec * 0.8:
            recommendations.append("Consider implementing caching or optimizing disk operations")

        if usage.network_io_recv_mb + usage.network_io_sent_mb > self.limits.network_io_max_mb_per_sec * 0.8:
            recommendations.append("Consider implementing compression or request batching")

        if usage.gpu_usage:
            for gpu in usage.gpu_usage:
                if gpu['utilization'] > self.limits.gpu_max_memory_percent * 0.8:
                    recommendations.append(f"Consider optimizing GPU memory usage for GPU {gpu['gpu_id']}")

        if usage.process_count > 1000:
            recommendations.append("High process count detected - consider process cleanup")

        if usage.thread_count > 500:
            recommendations.append("High thread count detected - consider thread pool optimization")

        return recommendations

# Resource allocation decorator
def allocate_resources(optimizer: ResourceOptimizer, **resource_request):
    """Decorator for resource allocation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Allocate resources
            allocation = optimizer.allocate_resources(resource_request)

            try:
                # Execute function with allocated resources
                result = func(*args, **kwargs)
                return result
            finally:
                # Release resources
                optimizer.release_resources(str(id(allocation)))

        return wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    # Initialize resource optimizer
    optimizer = ResourceOptimizer({
        'strategy': 'balanced',
        'auto_tuning': True,
        'limits': {
            'cpu_max_percent': 80.0,
            'memory_max_percent': 85.0
        }
    })

    # Start optimization
    optimizer.start_optimization()

    # Example function with resource allocation
    @allocate_resources(optimizer, cpu_cores=2, memory_gb=4.0)
    def cpu_intensive_task():
        """Example CPU-intensive task"""
        result = sum(i * i for i in range(1000000))
        return result

    # Run example task
    result = cpu_intensive_task()
    print(f"Task result: {result}")

    # Get resource status
    status = optimizer.get_resource_status()
    print(f"Resource status: {json.dumps(status, indent=2, default=str)}")

    # Run for a while to see optimization in action
    time.sleep(60)

    # Stop optimization
    optimizer.stop_optimization()