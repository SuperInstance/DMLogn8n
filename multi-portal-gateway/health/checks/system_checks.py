"""
System-Level Health Checks

Implements health checks for system-level resources like CPU, memory,
disk I/O, network interfaces, and overall system performance.
"""

import asyncio
import psutil
import logging
import platform
import socket
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..health_service import HealthCheckResult, HealthStatus

class SystemChecker:
    """System-level health checker"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.hostname = socket.gethostname()
        self.platform_info = self._get_platform_info()

    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }

    async def check_health(self, check_id: str) -> HealthCheckResult:
        """Check health of a specific system component"""
        check_method = getattr(self, f"_check_{check_id.replace('-', '_')}", None)

        if check_method:
            return await check_method()
        else:
            return HealthCheckResult(
                check_id=check_id,
                check_name=f"System Check: {check_id}",
                level="system",
                status=HealthStatus.UNKNOWN,
                message=f"Unknown system check: {check_id}"
            )

    async def _check_cpu_usage(self) -> HealthCheckResult:
        """Check CPU usage and performance"""
        start_time = datetime.now()

        try:
            # Get CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None

            # Get per-CPU usage
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # Calculate CPU health score
            score = 100.0

            if cpu_percent > 95:
                score -= 40
            elif cpu_percent > 85:
                score -= 25
            elif cpu_percent > 75:
                score -= 10

            # Check load average
            if load_avg:
                load_1min, load_5min, load_15min = load_avg
                if load_1min > cpu_count * 2:
                    score -= 30
                elif load_1min > cpu_count * 1.5:
                    score -= 15
                elif load_1min > cpu_count:
                    score -= 5

            # Check CPU frequency throttling
            if cpu_freq:
                current_freq = cpu_freq.current
                max_freq = cpu_freq.max
                if max_freq > 0:
                    freq_percentage = (current_freq / max_freq) * 100
                    if freq_percentage < 80:
                        score -= 20

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="cpu-usage",
                check_name="CPU Usage Check",
                level="system",
                status=status,
                message=f"CPU usage: {cpu_percent:.1f}% - Score: {score:.1f}%",
                details={
                    "cpu_count": cpu_count,
                    "cpu_usage_percent": round(cpu_percent, 2),
                    "cpu_per_core": [round(u, 2) for u in cpu_per_core],
                    "load_average": list(load_avg) if load_avg else None,
                    "cpu_frequency": {
                        "current_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                        "min_mhz": round(cpu_freq.min, 2) if cpu_freq else None,
                        "max_mhz": round(cpu_freq.max, 2) if cpu_freq else None
                    }
                },
                metrics={
                    "score": score,
                    "cpu_usage": cpu_percent,
                    "load_average_1min": load_avg[0] if load_avg else None,
                    "cpu_frequency_current": cpu_freq.current if cpu_freq else None
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"CPU usage check failed: {e}")
            return HealthCheckResult(
                check_id="cpu-usage",
                check_name="CPU Usage Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"CPU check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage and performance"""
        start_time = datetime.now()

        try:
            # Get memory metrics
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()

            # Calculate memory health score
            score = 100.0

            # Virtual memory scoring
            if virtual_memory.percent > 95:
                score -= 40
            elif virtual_memory.percent > 85:
                score -= 25
            elif virtual_memory.percent > 75:
                score -= 10

            # Swap memory scoring (high swap usage is bad)
            if swap_memory.percent > 50:
                score -= 30
            elif swap_memory.percent > 25:
                score -= 15
            elif swap_memory.percent > 10:
                score -= 5

            # Available memory check
            available_gb = virtual_memory.available / (1024**3)
            if available_gb < 1:  # Less than 1GB available
                score -= 20
            elif available_gb < 2:  # Less than 2GB available
                score -= 10

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="memory-usage",
                check_name="Memory Usage Check",
                level="system",
                status=status,
                message=f"Memory usage: {virtual_memory.percent:.1f}% - Score: {score:.1f}%",
                details={
                    "virtual_memory": {
                        "total_gb": round(virtual_memory.total / (1024**3), 2),
                        "available_gb": round(virtual_memory.available / (1024**3), 2),
                        "used_gb": round(virtual_memory.used / (1024**3), 2),
                        "percent": round(virtual_memory.percent, 2)
                    },
                    "swap_memory": {
                        "total_gb": round(swap_memory.total / (1024**3), 2),
                        "used_gb": round(swap_memory.used / (1024**3), 2),
                        "percent": round(swap_memory.percent, 2)
                    }
                },
                metrics={
                    "score": score,
                    "memory_usage_percent": virtual_memory.percent,
                    "swap_usage_percent": swap_memory.percent,
                    "available_memory_gb": available_gb
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Memory usage check failed: {e}")
            return HealthCheckResult(
                check_id="memory-usage",
                check_name="Memory Usage Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"Memory check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_disk_io(self) -> HealthCheckResult:
        """Check disk I/O performance"""
        start_time = datetime.now()

        try:
            # Get disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_partitions = psutil.disk_partitions()

            # Get I/O stats for each partition
            partition_stats = []
            total_score = 0

            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    device = partition.device

                    # Get disk I/O stats for this device
                    try:
                        io_stats = psutil.disk_io_counters(perdisk=True)
                        device_io = io_stats.get(device.replace('/dev/', ''), {})
                    except:
                        device_io = {}

                    # Calculate I/O score
                    device_score = 100.0

                    # Check disk usage
                    usage_percent = (usage.used / usage.total) * 100
                    if usage_percent > 95:
                        device_score -= 30
                    elif usage_percent > 90:
                        device_score -= 15
                    elif usage_percent > 80:
                        device_score -= 5

                    # Check I/O activity (simple heuristic)
                    if device_io:
                        read_bytes = device_io.read_bytes
                        write_bytes = device_io.write_bytes

                        # High I/O activity can indicate performance issues
                        if read_bytes > 1024**7 or write_bytes > 1024**7:  # >128MB
                            device_score -= 10

                    partition_stats.append({
                        "device": device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": round(usage_percent, 2),
                        "score": device_score,
                        "io_stats": {
                            "read_bytes": device_io.get("read_bytes", 0),
                            "write_bytes": device_io.get("write_bytes", 0),
                            "read_count": device_io.get("read_count", 0),
                            "write_count": device_io.get("write_count", 0)
                        } if device_io else {}
                    })

                    total_score += device_score

                except Exception as e:
                    self.logger.warning(f"Failed to check partition {partition.mountpoint}: {e}")

            # Calculate overall score
            overall_score = total_score / len(partition_stats) if partition_stats else 100.0

            # Determine status
            if overall_score >= 85:
                status = HealthStatus.HEALTHY
            elif overall_score >= 70:
                status = HealthStatus.WARNING
            elif overall_score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="disk-io",
                check_name="Disk I/O Check",
                level="system",
                status=status,
                message=f"Disk I/O check completed - Score: {overall_score:.1f}%",
                details={
                    "partitions": partition_stats,
                    "total_partitions": len(partition_stats),
                    "overall_io_stats": {
                        "read_bytes": disk_io.read_bytes if disk_io else 0,
                        "write_bytes": disk_io.write_bytes if disk_io else 0,
                        "read_count": disk_io.read_count if disk_io else 0,
                        "write_count": disk_io.write_count if disk_io else 0
                    } if disk_io else {}
                },
                metrics={
                    "score": overall_score,
                    "partitions_checked": len(partition_stats)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Disk I/O check failed: {e}")
            return HealthCheckResult(
                check_id="disk-io",
                check_name="Disk I/O Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"Disk I/O check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_network_interfaces(self) -> HealthCheckResult:
        """Check network interface status and performance"""
        start_time = datetime.now()

        try:
            # Get network interface stats
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            interface_stats = []
            total_score = 0
            active_interfaces = 0

            for interface_name, stats in net_io.items():
                try:
                    # Get interface addresses and status
                    addresses = net_if_addrs.get(interface_name, [])
                    if_stats = net_if_stats.get(interface_name)

                    if not if_stats or not if_stats.isup:
                        continue  # Skip inactive interfaces

                    active_interfaces += 1

                    # Calculate interface score
                    interface_score = 100.0

                    # Check for high error rates
                    total_packets = stats.packets_sent + stats.packets_recv
                    error_packets = stats.errin + stats.errout
                    drop_packets = stats.dropin + stats.dropout

                    if total_packets > 0:
                        error_rate = (error_packets / total_packets) * 100
                        drop_rate = (drop_packets / total_packets) * 100

                        if error_rate > 1:
                            interface_score -= 30
                        elif error_rate > 0.1:
                            interface_score -= 10

                        if drop_rate > 0.5:
                            interface_score -= 20
                        elif drop_rate > 0.1:
                            interface_score -= 5

                    # Check for high traffic (potential bottleneck)
                    bytes_sent_mb = stats.bytes_sent / (1024**2)
                    bytes_recv_mb = stats.bytes_recv / (1024**2)

                    if bytes_sent_mb > 1024 or bytes_recv_mb > 1024:  # >1GB
                        interface_score -= 5

                    # Get IP addresses
                    ip_addresses = []
                    for addr in addresses:
                        if addr.family == socket.AF_INET:
                            ip_addresses.append(addr.address)

                    interface_stats.append({
                        "name": interface_name,
                        "is_up": if_stats.isup if if_stats else False,
                        "speed": if_stats.speed if if_stats else 0,
                        "mtu": if_stats.mtu if if_stats else 0,
                        "ip_addresses": ip_addresses,
                        "stats": {
                            "bytes_sent": stats.bytes_sent,
                            "bytes_recv": stats.bytes_recv,
                            "packets_sent": stats.packets_sent,
                            "packets_recv": stats.packets_recv,
                            "error_in": stats.errin,
                            "error_out": stats.errout,
                            "drop_in": stats.dropin,
                            "drop_out": stats.dropout
                        },
                        "score": interface_score
                    })

                    total_score += interface_score

                except Exception as e:
                    self.logger.warning(f"Failed to check interface {interface_name}: {e}")

            # Calculate overall score
            overall_score = total_score / active_interfaces if active_interfaces > 0 else 100.0

            # Determine status
            if overall_score >= 85:
                status = HealthStatus.HEALTHY
            elif overall_score >= 70:
                status = HealthStatus.WARNING
            elif overall_score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="network-interfaces",
                check_name="Network Interfaces Check",
                level="system",
                status=status,
                message=f"Network interfaces check completed - Score: {overall_score:.1f}%",
                details={
                    "interfaces": interface_stats,
                    "active_interfaces": active_interfaces,
                    "hostname": self.hostname
                },
                metrics={
                    "score": overall_score,
                    "active_interfaces": active_interfaces
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Network interfaces check failed: {e}")
            return HealthCheckResult(
                check_id="network-interfaces",
                check_name="Network Interfaces Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"Network interfaces check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_system_processes(self) -> HealthCheckResult:
        """Check system process health"""
        start_time = datetime.now()

        try:
            # Get process information
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']))

            # Filter and analyze processes
            total_processes = len(processes)
            running_processes = len([p for p in processes if p.info['status'] == 'running'])
            sleeping_processes = len([p for p in processes if p.info['status'] == 'sleeping'])
            zombie_processes = len([p for p in processes if p.info['status'] == 'zombie'])

            # Find top CPU and memory consumers
            cpu_processes = sorted(processes, key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:10]
            memory_processes = sorted(processes, key=lambda p: p.info['memory_percent'] or 0, reverse=True)[:10]

            # Calculate health score
            score = 100.0

            # Check for zombie processes
            if zombie_processes > 10:
                score -= 30
            elif zombie_processes > 5:
                score -= 15
            elif zombie_processes > 0:
                score -= 5

            # Check total process count
            if total_processes > 500:
                score -= 20
            elif total_processes > 300:
                score -= 10

            # Check for high CPU processes
            high_cpu_processes = [p for p in cpu_processes if (p.info['cpu_percent'] or 0) > 80]
            if len(high_cpu_processes) > 3:
                score -= 25
            elif len(high_cpu_processes) > 1:
                score -= 10

            # Check for high memory processes
            high_memory_processes = [p for p in memory_processes if (p.info['memory_percent'] or 0) > 50]
            if len(high_memory_processes) > 2:
                score -= 25
            elif len(high_memory_processes) > 1:
                score -= 10

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="system-processes",
                check_name="System Processes Check",
                level="system",
                status=status,
                message=f"System processes check completed - Score: {score:.1f}%",
                details={
                    "total_processes": total_processes,
                    "running_processes": running_processes,
                    "sleeping_processes": sleeping_processes,
                    "zombie_processes": zombie_processes,
                    "top_cpu_processes": [
                        {
                            "pid": p.info['pid'],
                            "name": p.info['name'],
                            "cpu_percent": p.info['cpu_percent']
                        }
                        for p in cpu_processes[:5]
                    ],
                    "top_memory_processes": [
                        {
                            "pid": p.info['pid'],
                            "name": p.info['name'],
                            "memory_percent": p.info['memory_percent']
                        }
                        for p in memory_processes[:5]
                    ]
                },
                metrics={
                    "score": score,
                    "total_processes": total_processes,
                    "zombie_processes": zombie_processes,
                    "high_cpu_processes": len(high_cpu_processes),
                    "high_memory_processes": len(high_memory_processes)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"System processes check failed: {e}")
            return HealthCheckResult(
                check_id="system-processes",
                check_name="System Processes Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"System processes check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_system_temperature(self) -> HealthCheckResult:
        """Check system temperature if available"""
        start_time = datetime.now()

        try:
            # Try to get temperature sensors
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
            else:
                temps = None

            if not temps:
                return HealthCheckResult(
                    check_id="system-temperature",
                    check_name="System Temperature Check",
                    level="system",
                    status=HealthStatus.UNKNOWN,
                    message="Temperature sensors not available",
                    timestamp=start_time,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )

            temperature_readings = []
            total_score = 0
            sensor_count = 0

            for name, entries in temps.items():
                for entry in entries:
                    current_temp = entry.current
                    high_temp = entry.high or 80  # Default high threshold
                    critical_temp = entry.critical or 90  # Default critical threshold

                    # Calculate temperature score
                    sensor_score = 100.0

                    if current_temp >= critical_temp:
                        sensor_score = 0
                    elif current_temp >= high_temp:
                        sensor_score = 30
                    elif current_temp >= (high_temp * 0.9):
                        sensor_score = 60
                    elif current_temp >= (high_temp * 0.8):
                        sensor_score = 80

                    temperature_readings.append({
                        "sensor_name": name,
                        "label": entry.label or "Unknown",
                        "current_temp_celsius": round(current_temp, 1),
                        "high_temp_celsius": high_temp,
                        "critical_temp_celsius": critical_temp,
                        "score": sensor_score
                    })

                    total_score += sensor_score
                    sensor_count += 1

            # Calculate overall score
            overall_score = total_score / sensor_count if sensor_count > 0 else 100.0

            # Determine status
            if overall_score >= 85:
                status = HealthStatus.HEALTHY
            elif overall_score >= 70:
                status = HealthStatus.WARNING
            elif overall_score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="system-temperature",
                check_name="System Temperature Check",
                level="system",
                status=status,
                message=f"System temperature check completed - Score: {overall_score:.1f}%",
                details={
                    "temperature_readings": temperature_readings,
                    "sensor_count": sensor_count,
                    "highest_temp": max([r["current_temp_celsius"] for r in temperature_readings]) if temperature_readings else None
                },
                metrics={
                    "score": overall_score,
                    "sensor_count": sensor_count,
                    "highest_temperature": max([r["current_temp_celsius"] for r in temperature_readings]) if temperature_readings else None
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"System temperature check failed: {e}")
            return HealthCheckResult(
                check_id="system-temperature",
                check_name="System Temperature Check",
                level="system",
                status=HealthStatus.UNKNOWN,
                message=f"Temperature check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_docker_health(self) -> HealthCheckResult:
        """Check Docker daemon and container health"""
        start_time = datetime.now()

        try:
            # Check if Docker is available and running
            try:
                # Check Docker daemon
                result = await asyncio.create_subprocess_exec(
                    'docker', 'info',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    return HealthCheckResult(
                        check_id="docker-health",
                        check_name="Docker Health Check",
                        level="system",
                        status=HealthStatus.CRITICAL,
                        message="Docker daemon is not running or accessible",
                        details={"error": stderr.decode()},
                        timestamp=start_time,
                        duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )

                docker_info = stdout.decode()

                # Get container information
                result = await asyncio.create_subprocess_exec(
                    'docker', 'ps', '-a', '--format', 'json',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()

                containers_data = stdout.decode().strip().split('\n') if stdout.decode().strip() else []
                containers = []

                total_containers = 0
                running_containers = 0
                stopped_containers = 0
                unhealthy_containers = 0

                for container_line in containers_data:
                    if container_line:
                        try:
                            import json
                            container = json.loads(container_line)
                            containers.append(container)
                            total_containers += 1

                            if container.get('State') == 'running':
                                running_containers += 1
                            else:
                                stopped_containers += 1

                            # Check health status if available
                            if 'Health' in container and container['Health'] != 'healthy':
                                unhealthy_containers += 1

                        except json.JSONDecodeError:
                            continue

                # Calculate health score
                score = 100.0

                if unhealthy_containers > 0:
                    score -= (unhealthy_containers * 20)

                if total_containers > 0:
                    stopped_ratio = stopped_containers / total_containers
                    if stopped_ratio > 0.5:
                        score -= 30
                    elif stopped_ratio > 0.2:
                        score -= 15

                # Determine status
                if score >= 85:
                    status = HealthStatus.HEALTHY
                elif score >= 70:
                    status = HealthStatus.WARNING
                elif score >= 50:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.CRITICAL

                return HealthCheckResult(
                    check_id="docker-health",
                    check_name="Docker Health Check",
                    level="system",
                    status=status,
                    message=f"Docker health check completed - Score: {score:.1f}%",
                    details={
                        "total_containers": total_containers,
                        "running_containers": running_containers,
                        "stopped_containers": stopped_containers,
                        "unhealthy_containers": unhealthy_containers,
                        "containers": containers[:10]  # Limit to first 10 for brevity
                    },
                    metrics={
                        "score": score,
                        "total_containers": total_containers,
                        "running_containers": running_containers,
                        "unhealthy_containers": unhealthy_containers
                    },
                    timestamp=start_time,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )

            except FileNotFoundError:
                return HealthCheckResult(
                    check_id="docker-health",
                    check_name="Docker Health Check",
                    level="system",
                    status=HealthStatus.UNKNOWN,
                    message="Docker is not installed on this system",
                    timestamp=start_time,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )

        except Exception as e:
            self.logger.error(f"Docker health check failed: {e}")
            return HealthCheckResult(
                check_id="docker-health",
                check_name="Docker Health Check",
                level="system",
                status=HealthStatus.CRITICAL,
                message=f"Docker health check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )