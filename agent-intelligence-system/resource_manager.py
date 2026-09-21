#!/usr/bin/env python3
"""
DMlogn8n Resource Manager
=========================

Intelligent resource management for learning operations.

Features:
- Dynamic resource allocation
- Load balancing
- GPU management
- Resource monitoring
- Auto-scaling decisions
"""

import asyncio
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ResourceAllocation:
    """Resource allocation tracking."""
    component_id: str
    cpu_allocated: float  # cores
    memory_allocated: int  # MB
    gpu_allocated: bool
    allocated_at: datetime
    priority: int = 1

@dataclass
class ResourcePool:
    """Resource pool with available resources."""
    total_cpu: float = psutil.cpu_count()
    available_cpu: float = psutil.cpu_count()
    total_memory: int = psutil.virtual_memory().total // (1024 * 1024)  # MB
    available_memory: int = psutil.virtual_memory().available // (1024 * 1024)
    gpu_available: bool = True
    gpu_memory_total: int = 8192  # MB
    gpu_memory_available: int = 8192

class ResourceManager:
    """
    Intelligent resource manager for learning operations.

    Manages CPU, memory, and GPU resources across all learning subsystems.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Resource tracking
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.reserved_resources: Set[str] = set()
        self.resource_pool = ResourcePool()
        self.usage_history = []

        # Configuration
        self.max_cpu_usage = config.get('max_cpu_usage', 80.0)
        self.max_memory_usage = config.get('max_memory_usage', 85.0)
        self.check_interval = config.get('resource_check_interval', 5.0)

        # Monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info("ResourceManager initialized")

    async def allocate_resources(
        self,
        component_id: str,
        cpu: float,
        memory: int,
        gpu: bool = False,
        priority: int = 1
    ) -> bool:
        """
        Allocate resources to a component.

        Args:
            component_id: Unique identifier for the component
            cpu: CPU cores required
            memory: Memory in MB required
            gpu: Whether GPU is required
            priority: Allocation priority (higher = more important)

        Returns:
            bool: True if allocation successful
        """
        if not await self.check_availability(cpu, memory, gpu):
            logger.warning(f"Insufficient resources for {component_id}")
            return False

        # Create allocation
        allocation = ResourceAllocation(
            component_id=component_id,
            cpu_allocated=cpu,
            memory_allocated=memory,
            gpu_allocated=gpu,
            allocated_at=datetime.now(),
            priority=priority
        )

        # Update pool
        self.resource_pool.available_cpu -= cpu
        self.resource_pool.available_memory -= memory
        if gpu:
            self.resource_pool.gpu_available = False

        self.allocations[component_id] = allocation

        logger.info(f"Allocated resources to {component_id}: CPU={cpu}, Memory={memory}MB, GPU={gpu}")
        return True

    async def deallocate_resources(self, component_id: str) -> bool:
        """Deallocate resources from a component."""
        if component_id not in self.allocations:
            return False

        allocation = self.allocations[component_id]

        # Return resources to pool
        self.resource_pool.available_cpu += allocation.cpu_allocated
        self.resource_pool.available_memory += allocation.memory_allocated
        if allocation.gpu_allocated:
            self.resource_pool.gpu_available = True

        del self.allocations[component_id]

        logger.info(f"Deallocated resources from {component_id}")
        return True

    async def check_availability(
        self,
        cpu_required: float = 0.1,
        memory_required: int = 100,
        gpu_required: bool = False
    ) -> bool:
        """Check if resources are available."""
        # Get current system usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent

        # Check against thresholds
        if cpu_percent > self.max_cpu_usage:
            return False

        if memory_percent > self.max_memory_usage:
            return False

        # Check specific resource requirements
        if self.resource_pool.available_cpu < cpu_required:
            return False

        if self.resource_pool.available_memory < memory_required:
            return False

        if gpu_required and not self.resource_pool.gpu_available:
            return False

        return True

    async def start_monitoring(self):
        """Start resource monitoring."""
        if self.running:
            return

        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitor_resources())
        logger.info("Resource monitoring started")

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")

    async def _monitor_resources(self):
        """Main resource monitoring loop."""
        while self.running:
            try:
                # Update resource pool
                await self._update_resource_pool()

                # Record usage history
                self.usage_history.append({
                    'timestamp': datetime.now(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'active_allocations': len(self.allocations)
                })

                # Keep only recent history
                if len(self.usage_history) > 1000:
                    self.usage_history = self.usage_history[-1000:]

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.check_interval)

    async def _update_resource_pool(self):
        """Update resource pool with current availability."""
        # Get actual system usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # Calculate available resources
        total_cpu = psutil.cpu_count()
        used_cpu = (cpu_usage / 100.0) * total_cpu
        self.resource_pool.available_cpu = total_cpu - used_cpu - sum(
            alloc.cpu_allocated for alloc in self.allocations.values()
        )

        total_memory = memory.total // (1024 * 1024)  # MB
        used_memory = (memory.percent / 100.0) * total_memory
        self.resource_pool.available_memory = total_memory - used_memory - sum(
            alloc.memory_allocated for alloc in self.allocations.values()
        )

    async def get_allocation_status(self, component_id: str) -> Optional[ResourceAllocation]:
        """Get allocation status for a component."""
        return self.allocations.get(component_id)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'resource_pool': {
                'total_cpu': self.resource_pool.total_cpu,
                'available_cpu': self.resource_pool.available_cpu,
                'total_memory': self.resource_pool.total_memory,
                'available_memory': self.resource_pool.available_memory,
                'gpu_available': self.resource_pool.gpu_available
            },
            'allocations': {
                comp_id: {
                    'cpu': alloc.cpu_allocated,
                    'memory': alloc.memory_allocated,
                    'gpu': alloc.gpu_allocated,
                    'priority': alloc.priority
                }
                for comp_id, alloc in self.allocations.items()
            },
            'system_usage': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'active_allocations': len(self.allocations),
            'monitoring_active': self.running
        }

    async def optimize_allocations(self):
        """Optimize resource allocations based on usage patterns."""
        if len(self.usage_history) < 10:
            return

        # Analyze recent usage patterns
        recent_history = self.usage_history[-100:]

        # Calculate average usage
        avg_cpu = np.mean([h['cpu_percent'] for h in recent_history])
        avg_memory = np.mean([h['memory_percent'] for h in recent_history])

        # Identify underutilized allocations
        for component_id, allocation in list(self.allocations.items()):
            if allocation.priority < 3:  # Only optimize low priority allocations
                # Check if we can reclaim some resources
                if avg_cpu < 50 and allocation.cpu_allocated > 0.5:
                    # Reduce CPU allocation
                    reduction = min(allocation.cpu_allocated * 0.5, allocation.cpu_allocated - 0.1)
                    allocation.cpu_allocated -= reduction
                    self.resource_pool.available_cpu += reduction
                    logger.info(f"Reduced CPU allocation for {component_id} by {reduction}")

                if avg_memory < 60 and allocation.memory_allocated > 200:
                    # Reduce memory allocation
                    reduction = min(allocation.memory_allocated * 0.3, allocation.memory_allocated - 100)
                    allocation.memory_allocated -= reduction
                    self.resource_pool.available_memory += reduction
                    logger.info(f"Reduced memory allocation for {component_id} by {reduction}MB")

    async def force_cleanup(self):
        """Force cleanup of all allocations."""
        logger.warning("Forcing cleanup of all resource allocations")
        self.allocations.clear()
        await self._update_resource_pool()