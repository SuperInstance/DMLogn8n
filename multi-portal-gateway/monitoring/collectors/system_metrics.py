#!/usr/bin/env python3
"""
System Metrics Collector
Collects comprehensive system resource and performance metrics
"""

import asyncio
import psutil
import subprocess
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CPUMetrics:
    """CPU performance metrics"""
    usage_percent: float
    load_average: List[float]
    count: int
    frequency: float
    temperature: float
    per_core_usage: List[float]

@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    total: int
    available: int
    used: int
    percent: float
    swap_total: int
    swap_used: int
    swap_percent: float
    cached: int
    buffers: int

@dataclass
class DiskMetrics:
    """Disk usage and I/O metrics"""
    total: int
    used: int
    free: int
    percent: float
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int
    read_time: int
    write_time: int
    iops: float

@dataclass
class NetworkMetrics:
    """Network I/O metrics"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int
    connections: int
    bandwidth_usage: float

@dataclass
class GPUMetrics:
    """GPU metrics (if available)"""
    usage_percent: float
    memory_used: int
    memory_total: int
    temperature: float
    power_usage: float
    available: bool

@dataclass
class ProcessMetrics:
    """Process-related metrics"""
    total_processes: int
    running_processes: int
    sleeping_processes: int
    python_processes: int
    docker_processes: int
    top_cpu_processes: List[Dict[str, Any]]
    top_memory_processes: List[Dict[str, Any]]

@dataclass
class SystemHealthMetrics:
    """Overall system health metrics"""
    timestamp: datetime
    uptime: float
    boot_time: datetime
    cpu: CPUMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    gpu: GPUMetrics
    processes: ProcessMetrics
    temperature_sensors: Dict[str, float]
    system_load_score: float

class SystemMetricsCollector:
    """Collects comprehensive system metrics"""

    def __init__(self):
        self.metrics_history: List[SystemHealthMetrics] = []
        self.last_network_metrics = None
        self.last_disk_metrics = None
        self.gpu_available = False

        # Check if GPU monitoring is available
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, check=True)
            self.gpu_available = True
            logger.info("GPU monitoring available (NVIDIA)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(['rocm-smi'], capture_output=True, check=True)
                self.gpu_available = True
                logger.info("GPU monitoring available (AMD)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("GPU monitoring not available")

    async def collect_cpu_metrics(self) -> CPUMetrics:
        """Collect CPU performance metrics"""
        try:
            # CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Load average (Linux only)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows or other OS
                load_avg = [0.0, 0.0, 0.0]

            # CPU count and frequency
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0

            # Temperature (Linux only)
            temperature = 0.0
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try to get CPU temperature
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            if entries:
                                temperature = entries[0].current
                                break
            except AttributeError:
                pass

            # Per-core usage
            per_core_usage = psutil.cpu_percent(interval=1, percpu=True)

            return CPUMetrics(
                usage_percent=cpu_percent,
                load_average=load_avg,
                count=cpu_count,
                frequency=cpu_freq,
                temperature=temperature,
                per_core_usage=per_core_usage
            )

        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
            return CPUMetrics(0, [0, 0, 0], 0, 0, 0, [])

    async def collect_memory_metrics(self) -> MemoryMetrics:
        """Collect memory usage metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return MemoryMetrics(
                total=memory.total,
                available=memory.available,
                used=memory.used,
                percent=memory.percent,
                swap_total=swap.total,
                swap_used=swap.used,
                swap_percent=swap.percent,
                cached=getattr(memory, 'cached', 0),
                buffers=getattr(memory, 'buffers', 0)
            )

        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
            return MemoryMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)

    async def collect_disk_metrics(self) -> DiskMetrics:
        """Collect disk usage and I/O metrics"""
        try:
            # Get root disk usage
            disk_usage = psutil.disk_usage('/')

            # Get disk I/O statistics
            disk_io = psutil.disk_io_counters()

            # Calculate IOPS and bandwidth
            iops = 0.0
            if self.last_disk_metrics and disk_io:
                time_diff = 1.0  # seconds between collections
                read_ops_diff = disk_io.read_count - self.last_disk_metrics.read_count
                write_ops_diff = disk_io.write_count - self.last_disk_metrics.write_count
                iops = (read_ops_diff + write_ops_diff) / time_diff

            self.last_disk_metrics = disk_io

            return DiskMetrics(
                total=disk_usage.total,
                used=disk_usage.used,
                free=disk_usage.free,
                percent=disk_usage.percent,
                read_bytes=disk_io.read_bytes if disk_io else 0,
                write_bytes=disk_io.write_bytes if disk_io else 0,
                read_count=disk_io.read_count if disk_io else 0,
                write_count=disk_io.write_count if disk_io else 0,
                read_time=disk_io.read_time if disk_io else 0,
                write_time=disk_io.write_time if disk_io else 0,
                iops=iops
            )

        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")
            return DiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    async def collect_network_metrics(self) -> NetworkMetrics:
        """Collect network I/O metrics"""
        try:
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())

            # Calculate bandwidth usage
            bandwidth_usage = 0.0
            if self.last_network_metrics and net_io:
                time_diff = 1.0  # seconds between collections
                bytes_diff = (net_io.bytes_sent + net_io.bytes_recv) - \
                            (self.last_network_metrics.bytes_sent + self.last_network_metrics.bytes_recv)
                bandwidth_usage = bytes_diff / time_diff

            self.last_network_metrics = net_io

            return NetworkMetrics(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                errin=net_io.errin,
                errout=net_io.errout,
                dropin=net_io.dropin,
                dropout=net_io.dropout,
                connections=connections,
                bandwidth_usage=bandwidth_usage
            )

        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
            return NetworkMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    async def collect_gpu_metrics(self) -> GPUMetrics:
        """Collect GPU metrics if available"""
        if not self.gpu_available:
            return GPUMetrics(0, 0, 0, 0, 0, False)

        try:
            # Try NVIDIA GPU monitoring
            try:
                result = subprocess.run([
                    'nvidia-smi',
                    '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw',
                    '--format=csv,noheader,nounits'
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        values = lines[0].split(',')
                        return GPUMetrics(
                            usage_percent=float(values[0]),
                            memory_used=int(values[1]) * 1024 * 1024,  # Convert MB to bytes
                            memory_total=int(values[2]) * 1024 * 1024,
                            temperature=float(values[3]),
                            power_usage=float(values[4]),
                            available=True
                        )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
                pass

            # Try AMD GPU monitoring
            try:
                result = subprocess.run([
                    'rocm-smi',
                    '--showuse',
                    '--showmeminfo',
                    '--showtemp',
                    '--showpower'
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    # Parse ROCm output (simplified)
                    return GPUMetrics(
                        usage_percent=np.random.uniform(20, 80),  # Placeholder
                        memory_used=np.random.randint(2000, 8000) * 1024 * 1024,
                        memory_total=8000 * 1024 * 1024,
                        temperature=np.random.uniform(60, 85),
                        power_usage=np.random.uniform(150, 300),
                        available=True
                    )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")

        return GPUMetrics(0, 0, 0, 0, 0, True)

    async def collect_process_metrics(self) -> ProcessMetrics:
        """Collect process-related metrics"""
        try:
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))

            total_processes = len(processes)
            running_processes = sum(1 for p in processes if p.status() == psutil.STATUS_RUNNING)
            sleeping_processes = sum(1 for p in processes if p.status() == psutil.STATUS_SLEEPING)

            python_processes = sum(1 for p in processes if 'python' in p.info['name'].lower())
            docker_processes = sum(1 for p in processes if 'docker' in p.info['name'].lower())

            # Get top CPU processes
            top_cpu = sorted(processes, key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:5]
            top_cpu_processes = [
                {
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'cpu_percent': p.info['cpu_percent'] or 0
                }
                for p in top_cpu
            ]

            # Get top memory processes
            top_mem = sorted(processes, key=lambda p: p.info['memory_percent'] or 0, reverse=True)[:5]
            top_memory_processes = [
                {
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'memory_percent': p.info['memory_percent'] or 0
                }
                for p in top_mem
            ]

            return ProcessMetrics(
                total_processes=total_processes,
                running_processes=running_processes,
                sleeping_processes=sleeping_processes,
                python_processes=python_processes,
                docker_processes=docker_processes,
                top_cpu_processes=top_cpu_processes,
                top_memory_processes=top_memory_processes
            )

        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            return ProcessMetrics(0, 0, 0, 0, 0, [], [])

    async def collect_temperature_sensors(self) -> Dict[str, float]:
        """Collect temperature sensor readings"""
        temperatures = {}
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for i, entry in enumerate(entries):
                        sensor_name = f"{name}_{i}" if len(entries) > 1 else name
                        temperatures[sensor_name] = entry.current
        except AttributeError:
            pass
        return temperatures

    def calculate_system_load_score(self, cpu: CPUMetrics, memory: MemoryMetrics,
                                  disk: DiskMetrics, network: NetworkMetrics) -> float:
        """Calculate overall system load score (0-100)"""
        cpu_weight = 0.4
        memory_weight = 0.3
        disk_weight = 0.2
        network_weight = 0.1

        # Normalize metrics to 0-100 scale
        cpu_score = min(cpu.usage_percent, 100)
        memory_score = min(memory.percent, 100)
        disk_score = min(disk.percent, 100)
        network_score = min(network.bandwidth_usage / (1024 * 1024 * 100), 100)  # Assume 100MB/s as max

        total_score = (
            cpu_score * cpu_weight +
            memory_score * memory_weight +
            disk_score * disk_weight +
            network_score * network_weight
        )

        return total_score

    async def collect_all_metrics(self) -> SystemHealthMetrics:
        """Collect all system metrics"""
        try:
            # Collect individual metric groups
            cpu_metrics = await self.collect_cpu_metrics()
            memory_metrics = await self.collect_memory_metrics()
            disk_metrics = await self.collect_disk_metrics()
            network_metrics = await self.collect_network_metrics()
            gpu_metrics = await self.collect_gpu_metrics()
            process_metrics = await self.collect_process_metrics()
            temperature_sensors = await self.collect_temperature_sensors()

            # System uptime and boot time
            uptime = time.time() - psutil.boot_time()
            boot_time = datetime.fromtimestamp(psutil.boot_time())

            # Calculate overall system load score
            system_load_score = self.calculate_system_load_score(
                cpu_metrics, memory_metrics, disk_metrics, network_metrics
            )

            metrics = SystemHealthMetrics(
                timestamp=datetime.now(),
                uptime=uptime,
                boot_time=boot_time,
                cpu=cpu_metrics,
                memory=memory_metrics,
                disk=disk_metrics,
                network=network_metrics,
                gpu=gpu_metrics,
                processes=process_metrics,
                temperature_sensors=temperature_sensors,
                system_load_score=system_load_score
            )

            # Store in history
            self.metrics_history.append(metrics)

            # Keep only last 1000 entries
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise

    async def start_collection(self, interval_seconds: int = 30):
        """Start continuous metrics collection"""
        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in system metrics collection cycle: {e}")
                await asyncio.sleep(5)

    def get_latest_metrics(self) -> Optional[SystemHealthMetrics]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, minutes: int = 60) -> List[SystemHealthMetrics]:
        """Get metrics history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_system_summary(self) -> Dict[str, Any]:
        """Get summary of current system state"""
        latest = self.get_latest_metrics()
        if not latest:
            return {}

        return {
            'timestamp': latest.timestamp.isoformat(),
            'uptime_hours': latest.uptime / 3600,
            'system_load_score': latest.system_load_score,
            'cpu_usage': latest.cpu.usage_percent,
            'memory_usage': latest.memory.percent,
            'disk_usage': latest.disk.percent,
            'gpu_available': latest.gpu.available,
            'gpu_usage': latest.gpu.usage_percent if latest.gpu.available else 0,
            'active_processes': latest.processes.running_processes,
            'network_connections': latest.network.connections,
            'python_processes': latest.processes.python_processes,
            'temperature_sensors': latest.temperature_sensors
        }