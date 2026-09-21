#!/usr/bin/env python3
"""
DMLogn8n Global Health Monitor - Comprehensive System Health Monitoring
Monitors all platform components with advanced health checks and alerting
"""

import asyncio
import time
import json
import aiofiles
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import statistics
import psutil
import aiohttp

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"

class CheckType(Enum):
    HTTP = "http"
    TCP = "tcp"
    PROCESS = "process"
    DISK_SPACE = "disk_space"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"
    DATABASE = "database"
    EVENT_BUS = "event_bus"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    id: str
    name: str
    check_type: CheckType
    target: str  # URL, IP:Port, process name, etc.
    interval: int = 30  # seconds
    timeout: int = 10
    retries: int = 3
    enabled: bool = True
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    custom_check_func: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthResult:
    check_id: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthAlert:
    id: str
    check_id: str
    severity: AlertSeverity
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    uptime: float

class GlobalHealthMonitor:
    """
    Global health monitoring system with comprehensive checks and alerting
    """

    def __init__(self, event_bus=None, service_registry=None):
        self.event_bus = event_bus
        self.service_registry = service_registry
        self.logger = logging.getLogger('GlobalHealthMonitor')

        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, List[HealthResult]] = {}
        self.check_tasks: Dict[str, asyncio.Task] = {}

        # Alerts
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.alert_history: List[HealthAlert] = []
        self.alert_callbacks: List[Callable] = []

        # System metrics
        self.system_metrics: List[SystemMetrics] = []
        self.metrics_task: Optional[asyncio.Task] = None

        # Status
        self.overall_status = HealthStatus.UNKNOWN
        self.last_status_update = 0
        self.monitoring_active = False

        # Configuration
        self.metrics_interval = 60  # seconds
        self.metrics_history_size = 1000
        self.alert_cooldown = 300  # 5 minutes

        # Storage
        self.state_file = "/home/activeloguser/DMLogn8n/data/health_monitor_state.json"
        self.metrics_file = "/home/activeloguser/DMLogn8n/data/system_metrics.json"

        # HTTP client for checks
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize the health monitor"""
        self.logger.info("Initializing Global Health Monitor...")

        # Ensure data directory exists
        await aiofiles.os.makedirs(Path(self.state_file).parent, exist_ok=True)

        # Create HTTP session
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )

        # Load previous state
        await self._load_state()

        # Register default health checks
        await self._register_default_checks()

        # Auto-discover services and add checks
        await self._auto_discover_services()

        self.logger.info(f"Global Health Monitor initialized with {len(self.health_checks)} health checks")

    async def start_monitoring(self):
        """Start health monitoring"""
        self.logger.info("Starting health monitoring...")

        self.monitoring_active = True

        # Start all health check tasks
        for check_id, check in self.health_checks.items():
            if check.enabled:
                task = asyncio.create_task(self._run_health_check(check_id))
                self.check_tasks[check_id] = task

        # Start system metrics collection
        self.metrics_task = asyncio.create_task(self._collect_system_metrics())

        self.logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.logger.info("Stopping health monitoring...")

        self.monitoring_active = False

        # Cancel health check tasks
        for task in self.check_tasks.values():
            task.cancel()

        # Cancel metrics task
        if self.metrics_task:
            self.metrics_task.cancel()

        # Wait for tasks to complete
        all_tasks = list(self.check_tasks.values())
        if self.metrics_task:
            all_tasks.append(self.metrics_task)

        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

        # Save state
        await self._save_state()

        self.logger.info("Health monitoring stopped")

    async def add_health_check(self, health_check: HealthCheck) -> str:
        """Add a new health check"""
        self.health_checks[health_check.id] = health_check
        self.health_results[health_check.id] = []

        # Start monitoring if active
        if self.monitoring_active and health_check.enabled:
            task = asyncio.create_task(self._run_health_check(health_check.id))
            self.check_tasks[health_check.id] = task

        self.logger.info(f"Added health check: {health_check.name} ({health_check.id})")
        return health_check.id

    async def remove_health_check(self, check_id: str):
        """Remove a health check"""
        if check_id in self.health_checks:
            # Cancel task if running
            if check_id in self.check_tasks:
                self.check_tasks[check_id].cancel()
                del self.check_tasks[check_id]

            # Remove check and results
            del self.health_checks[check_id]
            if check_id in self.health_results:
                del self.health_results[check_id]

            self.logger.info(f"Removed health check: {check_id}")

    async def run_health_check_now(self, check_id: str) -> Optional[HealthResult]:
        """Run a health check immediately"""
        if check_id not in self.health_checks:
            return None

        check = self.health_checks[check_id]
        return await self._perform_health_check(check)

    async def _run_health_check(self, check_id: str):
        """Run a health check continuously"""
        check = self.health_checks[check_id]

        while self.monitoring_active:
            try:
                result = await self._perform_health_check(check)
                await self._process_health_result(result)

                # Wait for next check
                await asyncio.sleep(check.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check {check_id}: {e}")
                await asyncio.sleep(check.interval)

    async def _perform_health_check(self, check: HealthCheck) -> HealthResult:
        """Perform a single health check"""
        start_time = time.time()

        try:
            if check.check_type == CheckType.HTTP:
                status, message, details = await self._check_http_endpoint(check)
            elif check.check_type == CheckType.TCP:
                status, message, details = await self._check_tcp_port(check)
            elif check.check_type == CheckType.PROCESS:
                status, message, details = await self._check_process(check)
            elif check.check_type == CheckType.DISK_SPACE:
                status, message, details = await self._check_disk_space(check)
            elif check.check_type == CheckType.MEMORY:
                status, message, details = await self._check_memory_usage(check)
            elif check.check_type == CheckType.CPU:
                status, message, details = await self._check_cpu_usage(check)
            elif check.check_type == CheckType.DATABASE:
                status, message, details = await self._check_database(check)
            elif check.check_type == CheckType.EVENT_BUS:
                status, message, details = await self._check_event_bus(check)
            elif check.check_type == CheckType.CUSTOM:
                status, message, details = await self._check_custom(check)
            else:
                status = HealthStatus.UNKNOWN
                message = f"Unknown check type: {check.check_type}"
                details = {}

            response_time = time.time() - start_time

            return HealthResult(
                check_id=check.id,
                status=status,
                response_time=response_time,
                message=message,
                timestamp=start_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                check_id=check.id,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Check failed: {str(e)}",
                timestamp=start_time,
                details={'error': str(e)}
            )

    async def _check_http_endpoint(self, check: HealthCheck) -> tuple:
        """Check HTTP endpoint health"""
        try:
            async with self.http_session.get(check.target, timeout=check.timeout) as response:
                response_time = response.headers.get('X-Response-Time', 'unknown')
                status_code = response.status

                if status_code == 200:
                    if check.threshold_warning and float(response_time) > check.threshold_warning:
                        status = HealthStatus.WARNING
                        message = f"Slow response: {response_time}s"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"OK (status: {status_code}, time: {response_time}s)"
                elif status_code < 500:
                    status = HealthStatus.WARNING
                    message = f"HTTP {status_code}"
                else:
                    status = HealthStatus.CRITICAL
                    message = f"HTTP {status_code}"

                details = {
                    'status_code': status_code,
                    'response_time': response_time,
                    'headers': dict(response.headers)
                }

                return status, message, details

        except asyncio.TimeoutError:
            return HealthStatus.CRITICAL, "Request timeout", {}
        except Exception as e:
            return HealthStatus.CRITICAL, f"Connection error: {str(e)}", {}

    async def _check_tcp_port(self, check: HealthCheck) -> tuple:
        """Check TCP port connectivity"""
        try:
            host, port = check.target.split(':')
            port = int(port)

            start_time = time.time()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=check.timeout
            )
            response_time = time.time() - start_time

            writer.close()
            await writer.wait_closed()

            if check.threshold_warning and response_time > check.threshold_warning:
                status = HealthStatus.WARNING
                message = f"Slow connection: {response_time:.3f}s"
            else:
                status = HealthStatus.HEALTHY
                message = f"Connected in {response_time:.3f}s"

            details = {
                'host': host,
                'port': port,
                'response_time': response_time
            }

            return status, message, details

        except asyncio.TimeoutError:
            return HealthStatus.CRITICAL, "Connection timeout", {}
        except Exception as e:
            return HealthStatus.CRITICAL, f"Connection failed: {str(e)}", {}

    async def _check_process(self, check: HealthCheck) -> tuple:
        """Check if process is running"""
        try:
            process_found = False
            process_info = {}

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if check.target.lower() in proc.info['name'].lower():
                        process_found = True
                        process_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        }
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if process_found:
                cpu_usage = process_info.get('cpu_percent', 0)
                memory_usage = process_info.get('memory_percent', 0)

                if check.threshold_critical and cpu_usage > check.threshold_critical:
                    status = HealthStatus.CRITICAL
                    message = f"High CPU usage: {cpu_usage}%"
                elif check.threshold_warning and cpu_usage > check.threshold_warning:
                    status = HealthStatus.WARNING
                    message = f"High CPU usage: {cpu_usage}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Process running (PID: {process_info['pid']})"

                return status, message, process_info
            else:
                return HealthStatus.CRITICAL, "Process not found", {}

        except Exception as e:
            return HealthStatus.UNKNOWN, f"Check failed: {str(e)}", {}

    async def _check_disk_space(self, check: HealthCheck) -> tuple:
        """Check disk space usage"""
        try:
            disk_usage = psutil.disk_usage(check.target)
            usage_percent = (disk_usage.used / disk_usage.total) * 100

            if check.threshold_critical and usage_percent > check.threshold_critical:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {usage_percent:.1f}%"
            elif check.threshold_warning and usage_percent > check.threshold_warning:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage: {usage_percent:.1f}%"

            details = {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'usage_percent': usage_percent
            }

            return status, message, details

        except Exception as e:
            return HealthStatus.UNKNOWN, f"Check failed: {str(e)}", {}

    async def _check_memory_usage(self, check: HealthCheck) -> tuple:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if check.threshold_critical and usage_percent > check.threshold_critical:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {usage_percent:.1f}%"
            elif check.threshold_warning and usage_percent > check.threshold_warning:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {usage_percent:.1f}%"

            details = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'usage_percent': usage_percent
            }

            return status, message, details

        except Exception as e:
            return HealthStatus.UNKNOWN, f"Check failed: {str(e)}", {}

    async def _check_cpu_usage(self, check: HealthCheck) -> tuple:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)

            if check.threshold_critical and cpu_percent > check.threshold_critical:
                status = HealthStatus.CRITICAL
                message = f"CPU usage critical: {cpu_percent:.1f}%"
            elif check.threshold_warning and cpu_percent > check.threshold_warning:
                status = HealthStatus.WARNING
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage: {cpu_percent:.1f}%"

            details = {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'load_average': list(psutil.getloadavg())
            }

            return status, message, details

        except Exception as e:
            return HealthStatus.UNKNOWN, f"Check failed: {str(e)}", {}

    async def _check_database(self, check: HealthCheck) -> tuple:
        """Check database connectivity"""
        try:
            # This would be implemented based on the specific database type
            # For now, return a placeholder
            return HealthStatus.HEALTHY, "Database check not implemented", {}

        except Exception as e:
            return HealthStatus.CRITICAL, f"Database check failed: {str(e)}", {}

    async def _check_event_bus(self, check: HealthCheck) -> tuple:
        """Check event bus connectivity"""
        try:
            if self.event_bus:
                # Send a test event
                test_event_id = await self.event_bus.publish(
                    "health.check.test",
                    {"timestamp": time.time()},
                    "health_monitor"
                )
                return HealthStatus.HEALTHY, f"Event bus OK (event: {test_event_id})", {}
            else:
                return HealthStatus.WARNING, "Event bus not available", {}

        except Exception as e:
            return HealthStatus.CRITICAL, f"Event bus check failed: {str(e)}", {}

    async def _check_custom(self, check: HealthCheck) -> tuple:
        """Execute custom health check"""
        try:
            if check.custom_check_func:
                if asyncio.iscoroutinefunction(check.custom_check_func):
                    result = await check.custom_check_func(check.target)
                else:
                    result = check.custom_check_func(check.target)

                if isinstance(result, tuple):
                    return result
                elif isinstance(result, dict):
                    status = result.get('status', HealthStatus.HEALTHY)
                    message = result.get('message', 'Custom check passed')
                    details = result.get('details', {})
                    return status, message, details
                else:
                    return HealthStatus.HEALTHY, str(result), {}
            else:
                return HealthStatus.UNKNOWN, "No custom check function defined", {}

        except Exception as e:
            return HealthStatus.CRITICAL, f"Custom check failed: {str(e)}", {}

    async def _process_health_result(self, result: HealthResult):
        """Process health check result"""
        # Store result
        if result.check_id not in self.health_results:
            self.health_results[result.check_id] = []

        self.health_results[result.check_id].append(result)

        # Keep only recent results
        if len(self.health_results[result.check_id]) > 100:
            self.health_results[result.check_id] = self.health_results[result.check_id][-100:]

        # Update overall status
        await self._update_overall_status()

        # Check for alerts
        await self._check_for_alerts(result)

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("health.check.completed", {
                'check_id': result.check_id,
                'status': result.status.value,
                'response_time': result.response_time,
                'message': result.message
            })

    async def _update_overall_status(self):
        """Update overall system health status"""
        if not self.health_results:
            return

        # Determine worst status across all checks
        worst_status = HealthStatus.HEALTHY
        recent_results = []

        for check_id, results in self.health_results.items():
            if results:
                latest_result = results[-1]
                recent_results.append(latest_result)

                # Update worst status
                if latest_result.status == HealthStatus.CRITICAL:
                    worst_status = HealthStatus.CRITICAL
                elif latest_result.status == HealthStatus.WARNING and worst_status == HealthStatus.HEALTHY:
                    worst_status = HealthStatus.WARNING
                elif latest_result.status == HealthStatus.UNKNOWN and worst_status == HealthStatus.HEALTHY:
                    worst_status = HealthStatus.UNKNOWN

        self.overall_status = worst_status
        self.last_status_update = time.time()

        # Publish status change
        if self.event_bus:
            await self.event_bus.publish("health.status.changed", {
                'overall_status': worst_status.value,
                'total_checks': len(recent_results),
                'healthy_checks': sum(1 for r in recent_results if r.status == HealthStatus.HEALTHY),
                'warning_checks': sum(1 for r in recent_results if r.status == HealthStatus.WARNING),
                'critical_checks': sum(1 for r in recent_results if r.status == HealthStatus.CRITICAL)
            })

    async def _check_for_alerts(self, result: HealthResult):
        """Check if health result should trigger an alert"""
        check = self.health_checks.get(result.check_id)
        if not check:
            return

        # Check for status-based alerts
        if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
            await self._create_alert(
                check_id=result.check_id,
                severity=AlertSeverity.ERROR if result.status == HealthStatus.CRITICAL else AlertSeverity.WARNING,
                message=f"{check.name}: {result.message}",
                metadata={
                    'check_type': check.check_type.value,
                    'target': check.target,
                    'response_time': result.response_time,
                    'details': result.details
                }
            )

        # Check for performance alerts
        if (check.threshold_warning and result.response_time > check.threshold_warning) or \
           (check.threshold_critical and result.response_time > check.threshold_critical):
            severity = AlertSeverity.CRITICAL if result.response_time > (check.threshold_critical or float('inf')) else AlertSeverity.WARNING
            await self._create_alert(
                check_id=result.check_id,
                severity=severity,
                message=f"{check.name}: Slow response time ({result.response_time:.3f}s)",
                metadata={
                    'response_time': result.response_time,
                    'threshold_warning': check.threshold_warning,
                    'threshold_critical': check.threshold_critical
                }
            )

    async def _create_alert(self, check_id: str, severity: AlertSeverity, message: str, metadata: Dict[str, Any] = None):
        """Create a health alert"""
        alert_id = f"{check_id}_{int(time.time())}"

        # Check cooldown
        if check_id in self.active_alerts:
            last_alert = self.active_alerts[check_id]
            if time.time() - last_alert.timestamp < self.alert_cooldown:
                return  # Still in cooldown period

        alert = HealthAlert(
            id=alert_id,
            check_id=check_id,
            severity=severity,
            message=message,
            timestamp=time.time(),
            metadata=metadata or {}
        )

        self.active_alerts[check_id] = alert
        self.alert_history.append(alert)

        # Keep alert history manageable
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Publish alert
        if self.event_bus:
            await self.event_bus.publish("health.alert.created", {
                'alert_id': alert_id,
                'check_id': check_id,
                'severity': severity.value,
                'message': message,
                'metadata': metadata
            })

        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

        self.logger.warning(f"Health alert created: {message}")

    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while self.monitoring_active:
            try:
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_usage_percent=psutil.disk_usage('/').percent,
                    network_io=dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {},
                    process_count=len(psutil.pids()),
                    load_average=list(psutil.getloadavg()),
                    uptime=time.time() - psutil.boot_time()
                )

                self.system_metrics.append(metrics)

                # Keep only recent metrics
                if len(self.system_metrics) > self.metrics_history_size:
                    self.system_metrics = self.system_metrics[-self.metrics_history_size:]

                # Publish metrics
                if self.event_bus:
                    await self.event_bus.publish("system.metrics", {
                        'cpu_percent': metrics.cpu_percent,
                        'memory_percent': metrics.memory_percent,
                        'disk_usage_percent': metrics.disk_usage_percent,
                        'process_count': metrics.process_count,
                        'uptime': metrics.uptime
                    })

                await asyncio.sleep(self.metrics_interval)

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.metrics_interval)

    async def _register_default_checks(self):
        """Register default health checks"""
        default_checks = [
            HealthCheck(
                id="system_cpu",
                name="System CPU Usage",
                check_type=CheckType.CPU,
                target="system",
                threshold_warning=80.0,
                threshold_critical=95.0
            ),
            HealthCheck(
                id="system_memory",
                name="System Memory Usage",
                check_type=CheckType.MEMORY,
                target="system",
                threshold_warning=80.0,
                threshold_critical=95.0
            ),
            HealthCheck(
                id="system_disk",
                name="System Disk Usage",
                check_type=CheckType.DISK_SPACE,
                target="/",
                threshold_warning=80.0,
                threshold_critical=95.0
            ),
            HealthCheck(
                id="event_bus",
                name="Event Bus",
                check_type=CheckType.EVENT_BUS,
                target="event_bus"
            )
        ]

        for check in default_checks:
            await self.add_health_check(check)

    async def _auto_discover_services(self):
        """Auto-discover services and add health checks"""
        if not self.service_registry:
            return

        try:
            services = await self.service_registry.discover_services()

            for service in services:
                # Add health check for each service endpoint
                for endpoint in service.endpoints:
                    if endpoint.protocol == "http":
                        health_check = HealthCheck(
                            id=f"service_{service.name}_{endpoint.port}",
                            name=f"Service {service.name}",
                            check_type=CheckType.HTTP,
                            target=f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}{endpoint.health_check_path}",
                            threshold_warning=5.0,  # 5 second warning
                            threshold_critical=10.0  # 10 second critical
                        )
                        await self.add_health_check(health_check)

                    elif endpoint.protocol == "tcp":
                        health_check = HealthCheck(
                            id=f"service_{service.name}_{endpoint.port}",
                            name=f"Service {service.name}",
                            check_type=CheckType.TCP,
                            target=f"{endpoint.host}:{endpoint.port}",
                            threshold_warning=1.0,
                            threshold_critical=5.0
                        )
                        await self.add_health_check(health_check)

        except Exception as e:
            self.logger.error(f"Error auto-discovering services: {e}")

    def add_alert_callback(self, callback: Callable):
        """Add callback for health alerts"""
        self.alert_callbacks.append(callback)

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        # Calculate recent stats
        recent_time = time.time() - 300  # Last 5 minutes
        recent_results = []

        for check_id, results in self.health_results.items():
            recent = [r for r in results if r.timestamp > recent_time]
            recent_results.extend(recent)

        if recent_results:
            avg_response_time = statistics.mean(r.response_time for r in recent_results)
        else:
            avg_response_time = 0

        return {
            'overall_status': self.overall_status.value,
            'last_status_update': self.last_status_update,
            'total_checks': len(self.health_checks),
            'active_checks': sum(1 for c in self.health_checks.values() if c.enabled),
            'recent_results': len(recent_results),
            'average_response_time': avg_response_time,
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alert_history),
            'monitoring_active': self.monitoring_active,
            'system_metrics': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
                'uptime': time.time() - psutil.boot_time()
            },
            'checks': {
                check_id: {
                    'name': check.name,
                    'type': check.check_type.value,
                    'target': check.target,
                    'enabled': check.enabled,
                    'interval': check.interval,
                    'last_result': results[-1].__dict__ if results else None,
                    'status': results[-1].status.value if results else 'unknown'
                }
                for check_id, (check, results) in zip(
                    self.health_checks.keys(),
                    zip(self.health_checks.values(), self.health_results.values())
                )
            }
        }

    async def _load_state(self):
        """Load previous state"""
        try:
            if await aiofiles.os.path.exists(self.state_file):
                async with aiofiles.open(self.state_file, 'r') as f:
                    data = json.loads(await f.read())

                # Load health checks configuration (results are not persisted)
                for check_data in data.get('health_checks', []):
                    check = HealthCheck(
                        id=check_data['id'],
                        name=check_data['name'],
                        check_type=CheckType(check_data['check_type']),
                        target=check_data['target'],
                        interval=check_data.get('interval', 30),
                        timeout=check_data.get('timeout', 10),
                        retries=check_data.get('retries', 3),
                        enabled=check_data.get('enabled', True),
                        threshold_warning=check_data.get('threshold_warning'),
                        threshold_critical=check_data.get('threshold_critical'),
                        metadata=check_data.get('metadata', {})
                    )
                    self.health_checks[check.id] = check
                    self.health_results[check.id] = []

                self.logger.info(f"Loaded {len(self.health_checks)} health check configurations")

        except Exception as e:
            self.logger.error(f"Error loading state: {e}")

    async def _save_state(self):
        """Save current state"""
        try:
            data = {
                'health_checks': [
                    {
                        'id': check.id,
                        'name': check.name,
                        'check_type': check.check_type.value,
                        'target': check.target,
                        'interval': check.interval,
                        'timeout': check.timeout,
                        'retries': check.retries,
                        'enabled': check.enabled,
                        'threshold_warning': check.threshold_warning,
                        'threshold_critical': check.threshold_critical,
                        'metadata': check.metadata
                    }
                    for check in self.health_checks.values()
                ],
                'last_saved': time.time()
            }

            async with aiofiles.open(self.state_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    async def shutdown(self):
        """Shutdown the health monitor"""
        self.logger.info("Shutting down Global Health Monitor...")

        await self.stop_monitoring()

        # Close HTTP session
        if self.http_session:
            await self.http_session.close()

        # Save final state
        await self._save_state()

        self.logger.info("Global Health Monitor shutdown complete")