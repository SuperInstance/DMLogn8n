#!/usr/bin/env python3
"""
Health Checker for DMLogn8n Multi-Agent Platform

This module provides comprehensive health checking capabilities including:
- Custom health checks for different service types
- Health check scheduling and execution
- Health metric collection and aggregation
- Health alerting and notification
- Health trend analysis
"""

import asyncio
import json
import logging
import time
import psutil
import aiohttp
import socket
import subprocess
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import consul.aio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status values"""
    PASSING = "passing"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class CheckType(Enum):
    """Health check types"""
    HTTP = "http"
    TCP = "tcp"
    GRPC = "grpc"
    SCRIPT = "script"
    TTL = "ttl"
    CUSTOM = "custom"

@dataclass
class HealthCheckDefinition:
    """Health check definition"""
    check_id: str
    name: str
    service_id: str
    check_type: CheckType
    target: str  # URL, host:port, script path, etc.
    interval: int = 10  # seconds
    timeout: int = 3   # seconds
    deregister_after: int = 30  # seconds
    success_threshold: int = 3
    failure_threshold: int = 3
    headers: Dict[str, str] = None
    expected_status: int = 200
    expected_response: str = None
    script_args: List[str] = None
    custom_checker: Optional[Callable] = None
    metadata: Dict[str, Any] = None

@dataclass
class HealthCheckResult:
    """Health check result"""
    check_id: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any] = None
    output: str = None

@dataclass
class HealthMetrics:
    """Health metrics aggregation"""
    check_id: str
    service_id: str
    total_checks: int
    passing_checks: int
    warning_checks: int
    critical_checks: int
    avg_response_time: float
    last_check: datetime
    uptime_percentage: float
    trend: str  # improving, degrading, stable

class HealthChecker:
    """
    Comprehensive health checking system for DMLogn8n services
    """

    def __init__(self, consul_manager):
        self.consul_manager = consul_manager
        self.consul = consul_manager.consul
        self.check_definitions = {}
        self.active_checks = {}
        self.check_history = {}
        self.health_metrics = {}
        self.alert_handlers = {}
        self._shutdown = False
        self._check_tasks = {}

    async def register_check(self, check_def: HealthCheckDefinition) -> bool:
        """Register a new health check"""
        try:
            self.check_definitions[check_def.check_id] = check_def

            # Register with Consul
            consul_check = self._build_consul_check(check_def)
            await self.consul.agent.check.register(consul_check)

            # Start check execution
            if not self._shutdown:
                task = asyncio.create_task(self._execute_check_loop(check_def.check_id))
                self._check_tasks[check_def.check_id] = task

            logger.info(f"Health check registered: {check_def.check_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register health check: {e}")
            return False

    async def deregister_check(self, check_id: str) -> bool:
        """Deregister a health check"""
        try:
            # Stop check execution
            if check_id in self._check_tasks:
                self._check_tasks[check_id].cancel()
                del self._check_tasks[check_id]

            # Deregister from Consul
            await self.consul.agent.check.deregister(check_id)

            # Clean up local data
            if check_id in self.check_definitions:
                del self.check_definitions[check_id]

            if check_id in self.check_history:
                del self.check_history[check_id]

            if check_id in self.health_metrics:
                del self.health_metrics[check_id]

            logger.info(f"Health check deregistered: {check_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to deregister health check: {e}")
            return False

    async def execute_check(self, check_id: str) -> HealthCheckResult:
        """Execute a specific health check immediately"""
        try:
            if check_id not in self.check_definitions:
                return HealthCheckResult(
                    check_id=check_id,
                    status=HealthStatus.UNKNOWN,
                    message="Check definition not found",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )

            check_def = self.check_definitions[check_id]
            start_time = time.time()

            # Execute check based on type
            if check_def.check_type == CheckType.HTTP:
                result = await self._execute_http_check(check_def)
            elif check_def.check_type == CheckType.TCP:
                result = await self._execute_tcp_check(check_def)
            elif check_def.check_type == CheckType.SCRIPT:
                result = await self._execute_script_check(check_def)
            elif check_def.check_type == CheckType.CUSTOM:
                result = await self._execute_custom_check(check_def)
            else:
                result = HealthCheckResult(
                    check_id=check_id,
                    status=HealthStatus.UNKNOWN,
                    message=f"Unsupported check type: {check_def.check_type.value}",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )

            # Calculate response time
            result.response_time_ms = (time.time() - start_time) * 1000

            # Store result
            await self._store_check_result(result)

            # Update metrics
            await self._update_metrics(result)

            # Check for alerts
            await self._check_alerts(result)

            # Update Consul check status
            await self._update_consul_check(result)

            return result

        except Exception as e:
            logger.error(f"Check execution error: {e}")
            result = HealthCheckResult(
                check_id=check_id,
                status=HealthStatus.CRITICAL,
                message=f"Check execution failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )
            await self._store_check_result(result)
            return result

    async def get_service_health(self, service_id: str) -> Dict[str, Any]:
        """Get comprehensive health status for a service"""
        try:
            # Get service checks from Consul
            _, checks = await self.consul.health.checks(service_id)

            service_health = {
                'service_id': service_id,
                'overall_status': 'passing',
                'checks': [],
                'metrics': {},
                'timestamp': datetime.now().isoformat()
            }

            # Process each check
            for check in checks:
                check_id = check['CheckID']
                check_data = {
                    'check_id': check_id,
                    'name': check['Name'],
                    'status': check['Status'],
                    'output': check.get('Output', ''),
                    'service_id': check.get('ServiceID', ''),
                    'registered_at': check.get('RegistrationTime', '')
                }

                # Add metrics if available
                if check_id in self.health_metrics:
                    check_data['metrics'] = asdict(self.health_metrics[check_id])

                service_health['checks'].append(check_data)

                # Update overall status
                if check['Status'] == 'critical':
                    service_health['overall_status'] = 'critical'
                elif check['Status'] == 'warning' and service_health['overall_status'] == 'passing':
                    service_health['overall_status'] = 'warning'

            # Calculate service metrics
            service_health['metrics'] = self._calculate_service_metrics(service_health['checks'])

            return service_health

        except Exception as e:
            logger.error(f"Failed to get service health: {e}")
            return {}

    async def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health status"""
        try:
            cluster_health = {
                'timestamp': datetime.now().isoformat(),
                'total_services': 0,
                'healthy_services': 0,
                'warning_services': 0,
                'critical_services': 0,
                'total_checks': 0,
                'passing_checks': 0,
                'warning_checks': 0,
                'critical_checks': 0,
                'services': {},
                'summary': {}
            }

            # Get all services
            _, services = await self.consul.catalog.services()

            for service_name in services:
                service_health = await self.get_service_health(service_name)
                cluster_health['services'][service_name] = service_health

                # Update counters
                cluster_health['total_services'] += 1
                status = service_health.get('overall_status', 'unknown')

                if status == 'passing':
                    cluster_health['healthy_services'] += 1
                elif status == 'warning':
                    cluster_health['warning_services'] += 1
                elif status == 'critical':
                    cluster_health['critical_services'] += 1

                # Count checks
                for check in service_health.get('checks', []):
                    cluster_health['total_checks'] += 1
                    check_status = check.get('status', 'unknown')
                    if check_status == 'passing':
                        cluster_health['passing_checks'] += 1
                    elif check_status == 'warning':
                        cluster_health['warning_checks'] += 1
                    elif check_status == 'critical':
                        cluster_health['critical_checks'] += 1

            # Calculate summary
            if cluster_health['total_services'] > 0:
                cluster_health['summary']['health_score'] = (
                    cluster_health['healthy_services'] / cluster_health['total_services']
                ) * 100

            return cluster_health

        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            return {}

    async def register_alert_handler(self, handler: Callable):
        """Register health alert handler"""
        handler_id = f"handler_{int(time.time())}"
        self.alert_handlers[handler_id] = handler
        return handler_id

    async def _execute_check_loop(self, check_id: str):
        """Execute health check in a loop"""
        while not self._shutdown and check_id in self.check_definitions:
            try:
                await self.execute_check(check_id)

                # Wait for next interval
                check_def = self.check_definitions[check_id]
                await asyncio.sleep(check_def.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Check loop error for {check_id}: {e}")
                await asyncio.sleep(5)

    async def _execute_http_check(self, check_def: HealthCheckDefinition) -> HealthCheckResult:
        """Execute HTTP health check"""
        try:
            headers = check_def.headers or {}
            timeout = aiohttp.ClientTimeout(total=check_def.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(check_def.target, headers=headers) as response:
                    status_code = response.status
                    response_text = await response.text()

                    if status_code == check_def.expected_status:
                        status = HealthStatus.PASSING
                        message = f"HTTP {status_code} OK"

                        # Check expected response if provided
                        if check_def.expected_response and check_def.expected_response not in response_text:
                            status = HealthStatus.WARNING
                            message = f"HTTP {status_code} but unexpected response content"
                    else:
                        status = HealthStatus.CRITICAL
                        message = f"HTTP {status_code} (expected {check_def.expected_status})"

                    return HealthCheckResult(
                        check_id=check_def.check_id,
                        status=status,
                        message=message,
                        timestamp=datetime.now(),
                        response_time_ms=0,  # Will be set by caller
                        output=response_text[:500]  # Limit output size
                    )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"HTTP check timeout after {check_def.timeout}s",
                timestamp=datetime.now(),
                response_time_ms=0
            )
        except Exception as e:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"HTTP check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )

    async def _execute_tcp_check(self, check_def: HealthCheckDefinition) -> HealthCheckResult:
        """Execute TCP health check"""
        try:
            host, port = check_def.target.split(':')
            port = int(port)

            start_time = time.time()

            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(check_def.timeout)

            result = sock.connect_ex((host, port))
            sock.close()

            response_time = (time.time() - start_time) * 1000

            if result == 0:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.PASSING,
                    message=f"TCP connection successful to {host}:{port}",
                    timestamp=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.CRITICAL,
                    message=f"TCP connection failed to {host}:{port}",
                    timestamp=datetime.now(),
                    response_time_ms=response_time
                )

        except Exception as e:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"TCP check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )

    async def _execute_script_check(self, check_def: HealthCheckDefinition) -> HealthCheckResult:
        """Execute script health check"""
        try:
            cmd = [check_def.target]
            if check_def.script_args:
                cmd.extend(check_def.script_args)

            start_time = time.time()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=check_def.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.CRITICAL,
                    message=f"Script check timeout after {check_def.timeout}s",
                    timestamp=datetime.now(),
                    response_time_ms=check_def.timeout * 1000
                )

            response_time = (time.time() - start_time) * 1000
            return_code = process.returncode

            output = stdout.decode('utf-8').strip() if stdout else ""
            error_output = stderr.decode('utf-8').strip() if stderr else ""

            if return_code == 0:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.PASSING,
                    message="Script executed successfully",
                    timestamp=datetime.now(),
                    response_time_ms=response_time,
                    output=output
                )
            else:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.CRITICAL,
                    message=f"Script failed with return code {return_code}: {error_output}",
                    timestamp=datetime.now(),
                    response_time_ms=response_time,
                    output=output + "\n" + error_output
                )

        except Exception as e:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"Script check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )

    async def _execute_custom_check(self, check_def: HealthCheckDefinition) -> HealthCheckResult:
        """Execute custom health check"""
        try:
            if not check_def.custom_checker:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.CRITICAL,
                    message="Custom checker not provided",
                    timestamp=datetime.now(),
                    response_time_ms=0
                )

            # Call custom checker
            result = await check_def.custom_checker(check_def)

            if isinstance(result, HealthCheckResult):
                return result
            else:
                return HealthCheckResult(
                    check_id=check_def.check_id,
                    status=HealthStatus.PASSING,
                    message=str(result),
                    timestamp=datetime.now(),
                    response_time_ms=0
                )

        except Exception as e:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"Custom check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )

    def _build_consul_check(self, check_def: HealthCheckDefinition) -> Dict[str, Any]:
        """Build Consul check definition"""
        consul_check = {
            'ID': check_def.check_id,
            'Name': check_def.name,
            'ServiceID': check_def.service_id,
            'DeregisterCriticalServiceAfter': f"{check_def.deregister_after}s"
        }

        if check_def.check_type == CheckType.HTTP:
            consul_check['HTTP'] = check_def.target
            consul_check['Method'] = 'GET'
            consul_check['Interval'] = f"{check_def.interval}s"
            consul_check['Timeout'] = f"{check_def.timeout}s"

        elif check_def.check_type == CheckType.TCP:
            consul_check['TCP'] = check_def.target
            consul_check['Interval'] = f"{check_def.interval}s"
            consul_check['Timeout'] = f"{check_def.timeout}s"

        elif check_def.check_type == CheckType.SCRIPT:
            consul_check['Args'] = [check_def.target] + (check_def.script_args or [])
            consul_check['Interval'] = f"{check_def.interval}s"
            consul_check['Timeout'] = f"{check_def.timeout}s"

        elif check_def.check_type == CheckType.TTL:
            consul_check['TTL'] = f"{check_def.interval}s"

        return consul_check

    async def _store_check_result(self, result: HealthCheckResult):
        """Store check result in history"""
        try:
            check_id = result.check_id

            if check_id not in self.check_history:
                self.check_history[check_id] = []

            # Add result to history
            self.check_history[check_id].append(result)

            # Keep only last 100 results
            if len(self.check_history[check_id]) > 100:
                self.check_history[check_id] = self.check_history[check_id][-100:]

            # Store in Consul KV for persistence
            history_path = f"dmlogn8n/health/history/{check_id}"
            history_data = [asdict(r) for r in self.check_history[check_id][-10]]  # Last 10 results

            await self.consul.kv.put(
                history_path,
                json.dumps(history_data, default=str)
            )

        except Exception as e:
            logger.error(f"Failed to store check result: {e}")

    async def _update_metrics(self, result: HealthCheckResult):
        """Update health metrics for a check"""
        try:
            check_id = result.check_id

            if check_id not in self.health_metrics:
                self.health_metrics[check_id] = HealthMetrics(
                    check_id=check_id,
                    service_id=self.check_definitions[check_id].service_id,
                    total_checks=0,
                    passing_checks=0,
                    warning_checks=0,
                    critical_checks=0,
                    avg_response_time=0,
                    last_check=result.timestamp,
                    uptime_percentage=0,
                    trend='stable'
                )

            metrics = self.health_metrics[check_id]
            metrics.total_checks += 1

            if result.status == HealthStatus.PASSING:
                metrics.passing_checks += 1
            elif result.status == HealthStatus.WARNING:
                metrics.warning_checks += 1
            elif result.status == HealthStatus.CRITICAL:
                metrics.critical_checks += 1

            # Update average response time
            total_response_time = (
                metrics.avg_response_time * (metrics.total_checks - 1) +
                result.response_time_ms
            )
            metrics.avg_response_time = total_response_time / metrics.total_checks

            # Update uptime percentage
            metrics.uptime_percentage = (metrics.passing_checks / metrics.total_checks) * 100

            # Calculate trend
            metrics.trend = self._calculate_trend(check_id)

            metrics.last_check = result.timestamp

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")

    def _calculate_trend(self, check_id: str) -> str:
        """Calculate health trend based on recent history"""
        try:
            if check_id not in self.check_history or len(self.check_history[check_id]) < 5:
                return 'stable'

            recent_checks = self.check_history[check_id][-5:]
            status_changes = 0

            for i in range(1, len(recent_checks)):
                if recent_checks[i].status != recent_checks[i-1].status:
                    status_changes += 1

            if status_changes >= 3:
                return 'unstable'
            elif recent_checks[-1].status == HealthStatus.PASSING:
                if status_changes <= 1:
                    return 'improving'
            elif recent_checks[-1].status == HealthStatus.CRITICAL:
                if status_changes <= 1:
                    return 'degrading'

            return 'stable'

        except Exception:
            return 'stable'

    async def _check_alerts(self, result: HealthCheckResult):
        """Check if alerts should be triggered"""
        try:
            check_id = result.check_id

            # Alert on critical status
            if result.status == HealthStatus.CRITICAL:
                await self._trigger_alert('critical', result)

            # Alert on consecutive failures
            if check_id in self.check_history and len(self.check_history[check_id]) >= 3:
                recent_checks = self.check_history[check_id][-3:]
                if all(check.status == HealthStatus.CRITICAL for check in recent_checks):
                    await self._trigger_alert('consecutive_failures', result)

            # Alert on status degradation
            if check_id in self.health_metrics:
                metrics = self.health_metrics[check_id]
                if metrics.trend == 'degrading':
                    await self._trigger_alert('degradation', result)

        except Exception as e:
            logger.error(f"Alert check error: {e}")

    async def _trigger_alert(self, alert_type: str, result: HealthCheckResult):
        """Trigger health alert"""
        try:
            alert_data = {
                'type': alert_type,
                'check_id': result.check_id,
                'service_id': self.check_definitions[result.check_id].service_id,
                'status': result.status.value,
                'message': result.message,
                'timestamp': result.timestamp.isoformat(),
                'response_time_ms': result.response_time_ms
            }

            # Call all alert handlers
            for handler_id, handler in self.alert_handlers.items():
                try:
                    await handler(alert_data)
                except Exception as e:
                    logger.error(f"Alert handler error {handler_id}: {e}")

            # Emit Consul event
            await self.consul_manager.emit_event('health_alert', alert_data)

            logger.warning(f"Health alert triggered: {alert_type} for {result.check_id}")

        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")

    async def _update_consul_check(self, result: HealthCheckResult):
        """Update check status in Consul"""
        try:
            check_id = result.check_id

            if result.status == HealthStatus.PASSING:
                await self.consul.agent.check.pass(check_id, result.message)
            elif result.status == HealthStatus.WARNING:
                await self.consul.agent.check.warn(check_id, result.message)
            elif result.status == HealthStatus.CRITICAL:
                await self.consul.agent.check.fail(check_id, result.message)

        except Exception as e:
            logger.error(f"Failed to update Consul check: {e}")

    def _calculate_service_metrics(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate service-level health metrics"""
        total_checks = len(checks)
        if total_checks == 0:
            return {}

        passing = sum(1 for check in checks if check['status'] == 'passing')
        warning = sum(1 for check in checks if check['status'] == 'warning')
        critical = sum(1 for check in checks if check['status'] == 'critical')

        # Calculate average response time
        response_times = []
        for check in checks:
            if 'metrics' in check and check['metrics'].get('avg_response_time'):
                response_times.append(check['metrics']['avg_response_time'])

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            'total_checks': total_checks,
            'passing_checks': passing,
            'warning_checks': warning,
            'critical_checks': critical,
            'health_score': (passing / total_checks) * 100,
            'avg_response_time': avg_response_time
        }

    async def create_system_health_check(self) -> str:
        """Create system-wide health check"""
        try:
            check_def = HealthCheckDefinition(
                check_id="system_health",
                name="System Health Check",
                service_id="system",
                check_type=CheckType.CUSTOM,
                target="internal",
                interval=30,
                timeout=10,
                custom_checker=self._system_health_checker
            )

            await self.register_check(check_def)
            return check_def.check_id

        except Exception as e:
            logger.error(f"Failed to create system health check: {e}")
            return ""

    async def _system_health_checker(self, check_def: HealthCheckDefinition) -> HealthCheckResult:
        """System health checker implementation"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Check disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Check Consul connectivity
            try:
                await self.consul.status.leader()
                consul_healthy = True
            except:
                consul_healthy = False

            # Determine overall status
            if not consul_healthy:
                status = HealthStatus.CRITICAL
                message = "Consul connectivity lost"
            elif cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.WARNING
                message = f"High resource usage - CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%"
            else:
                status = HealthStatus.PASSING
                message = f"System healthy - CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%"

            return HealthCheckResult(
                check_id=check_def.check_id,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=0,
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'consul_healthy': consul_healthy
                }
            )

        except Exception as e:
            return HealthCheckResult(
                check_id=check_def.check_id,
                status=HealthStatus.CRITICAL,
                message=f"System health check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=0
            )

    async def shutdown(self):
        """Shutdown health checker"""
        self._shutdown = True

        # Cancel all check tasks
        for task in self._check_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self._check_tasks:
            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)

        logger.info("Health checker shutdown completed")

# Export main classes
__all__ = [
    'HealthChecker',
    'HealthCheckDefinition',
    'HealthCheckResult',
    'HealthMetrics',
    'HealthStatus',
    'CheckType'
]