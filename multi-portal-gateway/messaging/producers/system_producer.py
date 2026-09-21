#!/usr/bin/env python3
"""
System Producer - Handles system event and monitoring messages.

This producer manages messages for system operations including:
- System alerts and notifications
- Performance monitoring
- Health checks
- Configuration updates
- Security events
- Resource management
- Logging and audit events
"""

import asyncio
import json
import logging
import time
import psutil
import socket
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from ..message_broker import (
    Message, MessageType, MessagePriority, MessageBroker,
    QueueConfig, ExchangeConfig, ConsumerConfig
)

logger = logging.getLogger(__name__)


class SystemEventType(Enum):
    """System event types."""
    ALERT = "alert"
    HEALTH_CHECK = "health_check"
    PERFORMANCE_METRIC = "performance_metric"
    RESOURCE_USAGE = "resource_usage"
    SECURITY_EVENT = "security_event"
    CONFIGURATION_CHANGE = "configuration_change"
    SERVICE_STATUS = "service_status"
    ERROR_REPORT = "error_report"
    AUDIT_LOG = "audit_log"
    BACKUP_OPERATION = "backup_operation"
    MAINTENANCE_EVENT = "maintenance_event"
    DEPLOYMENT_EVENT = "deployment_event"
    SCALING_EVENT = "scaling_event"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ServiceStatus(Enum):
    """Service status types."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


@dataclass
class SystemInfo:
    """System information structure."""
    hostname: str
    ip_address: str
    os_type: str
    os_version: str
    cpu_count: int
    memory_total: int
    disk_total: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_percent: float
    disk_used: int
    disk_free: int
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class SystemEvent:
    """System event structure."""
    event_id: str
    event_type: SystemEventType
    source: str
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    affected_services: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[float] = None


@dataclass
class ServiceInfo:
    """Service information structure."""
    service_id: str
    name: str
    version: str
    status: ServiceStatus
    endpoint: Optional[str] = None
    health_check_url: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_health_check: float = field(default_factory=time.time)
    uptime: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemProducer:
    """
    Producer for system events and monitoring messages.
    """

    def __init__(self, message_broker: MessageBroker, node_id: Optional[str] = None):
        self.broker = message_broker
        self.node_id = node_id or socket.gethostname()
        self.system_info = self._collect_system_info()
        self.services: Dict[str, ServiceInfo] = {}
        self.active_alerts: Dict[str, SystemEvent] = {}
        self.metrics_buffer: List[ResourceMetrics] = []
        self.monitoring_enabled = True
        self.monitoring_interval = 30.0  # seconds
        self.max_metrics_buffer = 1000
        self.stats = {
            'alerts_sent': 0,
            'health_checks_sent': 0,
            'metrics_sent': 0,
            'security_events_sent': 0,
            'config_changes_sent': 0,
            'errors': 0
        }

    def _collect_system_info(self) -> SystemInfo:
        """Collect system information."""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)

            return SystemInfo(
                hostname=hostname,
                ip_address=ip_address,
                os_type=psutil.POSIX if hasattr(psutil, 'POSIX') else 'unknown',
                os_version=psutil.os_version().get('release', 'unknown') if hasattr(psutil, 'os_version') else 'unknown',
                cpu_count=psutil.cpu_count(),
                memory_total=psutil.virtual_memory().total,
                disk_total=psutil.disk_usage('/').total
            )
        except Exception as e:
            logger.error(f"Failed to collect system info: {str(e)}")
            return SystemInfo(
                hostname="unknown",
                ip_address="0.0.0.0",
                os_type="unknown",
                os_version="unknown",
                cpu_count=0,
                memory_total=0,
                disk_total=0
            )

    async def initialize(self):
        """Initialize the system producer."""
        try:
            # Declare system exchange
            exchange_config = ExchangeConfig(
                name="system.exchange",
                type="topic",
                durable=True
            )
            await self.broker.declare_exchange(exchange_config)

            # Declare system queues
            queues = [
                ("system.alerts", "system.alert.#"),
                ("system.health", "system.health.#"),
                ("system.metrics", "system.metrics.#"),
                ("system.security", "system.security.#"),
                ("system.config", "system.config.#"),
                ("system.audit", "system.audit.#")
            ]

            for queue_name, routing_pattern in queues:
                queue_config = QueueConfig(
                    name=queue_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": 86400000,  # 24 hours TTL
                        "x-max-length": 10000      # Max 10000 messages
                    }
                )
                await self.broker.declare_queue(queue_config)
                await self.broker.bind_queue(queue_name, exchange_config.name, routing_pattern)

            # Start monitoring task
            if self.monitoring_enabled:
                asyncio.create_task(self._monitoring_loop())

            # Send startup event
            await self.publish_startup_event()

            logger.info(f"Initialized system producer for node {self.node_id}")

        except Exception as e:
            logger.error(f"Failed to initialize system producer: {str(e)}")
            raise

    async def publish_alert(self, event: SystemEvent) -> bool:
        """
        Publish a system alert.

        Args:
            event: System event to publish as alert

        Returns:
            bool: True if alert published successfully
        """
        try:
            # Store active alert
            if event.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                self.active_alerts[event.event_id] = event

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic=f"system.alert.{event.severity.value}",
                payload={
                    "event": event.__dict__,
                    "system_info": self.system_info.__dict__,
                    "node_id": self.node_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "source": event.source,
                    "category": event.category,
                    "node_id": self.node_id
                },
                priority=self._severity_to_priority(event.severity),
                source="system_monitor",
                expiration=3600000  # 1 hour TTL for alerts
            )

            success = await self.broker.publish(message, f"system.alert.{event.severity.value}")

            if success:
                self.stats['alerts_sent'] += 1
                logger.warning(f"Published {event.severity.value} alert: {event.message}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish alert {event.event_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_health_check(self, service_id: str, status: ServiceStatus,
                                 details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish a health check event.

        Args:
            service_id: ID of the service
            status: Service status
            details: Additional health check details

        Returns:
            bool: True if health check published successfully
        """
        try:
            event_id = f"health_{service_id}_{int(time.time())}"

            event = SystemEvent(
                event_id=event_id,
                event_type=SystemEventType.HEALTH_CHECK,
                source=f"service:{service_id}",
                severity=AlertSeverity.INFO if status == ServiceStatus.RUNNING else AlertSeverity.WARNING,
                message=f"Service {service_id} status: {status.value}",
                details=details or {},
                category="health",
                tags=["health_check", service_id],
                affected_services=[service_id]
            )

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic=f"system.health.{status.value}",
                payload={
                    "event": event.__dict__,
                    "service_id": service_id,
                    "status": status.value,
                    "details": details or {},
                    "node_id": self.node_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "service_id": service_id,
                    "status": status.value,
                    "node_id": self.node_id
                },
                priority=MessagePriority.NORMAL,
                source="health_monitor"
            )

            success = await self.broker.publish(message, f"system.health.{status.value}")

            if success:
                self.stats['health_checks_sent'] += 1
                logger.debug(f"Published health check for {service_id}: {status.value}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish health check for {service_id}: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_metrics(self, metrics: ResourceMetrics) -> bool:
        """
        Publish resource usage metrics.

        Args:
            metrics: Resource metrics to publish

        Returns:
            bool: True if metrics published successfully
        """
        try:
            # Add to buffer
            self.metrics_buffer.append(metrics)

            # Trim buffer if needed
            if len(self.metrics_buffer) > self.max_metrics_buffer:
                self.metrics_buffer = self.metrics_buffer[-self.max_metrics_buffer:]

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic="system.metrics.resource",
                payload={
                    "metrics": metrics.__dict__,
                    "node_id": self.node_id
                },
                headers={
                    "metrics_type": "resource",
                    "node_id": self.node_id
                },
                priority=MessagePriority.LOW,
                source="metrics_collector"
            )

            success = await self.broker.publish(message, "system.metrics.resource")

            if success:
                self.stats['metrics_sent'] += 1
                logger.debug(f"Published resource metrics for node {self.node_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish metrics: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_security_event(self, event_data: Dict[str, Any],
                                   severity: AlertSeverity = AlertSeverity.WARNING) -> bool:
        """
        Publish a security event.

        Args:
            event_data: Security event data
            severity: Event severity

        Returns:
            bool: True if security event published successfully
        """
        try:
            event_id = f"security_{int(time.time() * 1000)}"

            event = SystemEvent(
                event_id=event_id,
                event_type=SystemEventType.SECURITY_EVENT,
                source="security_monitor",
                severity=severity,
                message=event_data.get("message", "Security event detected"),
                details=event_data,
                category="security",
                tags=["security", event_data.get("type", "unknown")]
            )

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic=f"system.security.{severity.value}",
                payload={
                    "event": event.__dict__,
                    "security_data": event_data,
                    "node_id": self.node_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "security_type": event_data.get("type", "unknown"),
                    "severity": severity.value,
                    "node_id": self.node_id
                },
                priority=self._severity_to_priority(severity),
                source="security_monitor"
            )

            success = await self.broker.publish(message, f"system.security.{severity.value}")

            if success:
                self.stats['security_events_sent'] += 1
                logger.warning(f"Published security event: {event.message}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish security event: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_config_change(self, config_data: Dict[str, Any],
                                  changed_by: str = "system") -> bool:
        """
        Publish a configuration change event.

        Args:
            config_data: Configuration change data
            changed_by: Who made the change

        Returns:
            bool: True if config change published successfully
        """
        try:
            event_id = f"config_change_{int(time.time() * 1000)}"

            event = SystemEvent(
                event_id=event_id,
                event_type=SystemEventType.CONFIGURATION_CHANGE,
                source="config_manager",
                severity=AlertSeverity.INFO,
                message=f"Configuration changed by {changed_by}",
                details={
                    "config_changes": config_data,
                    "changed_by": changed_by
                },
                category="configuration",
                tags=["config", "change"]
            )

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic="system.config.change",
                payload={
                    "event": event.__dict__,
                    "config_data": config_data,
                    "changed_by": changed_by,
                    "node_id": self.node_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "changed_by": changed_by,
                    "node_id": self.node_id
                },
                priority=MessagePriority.NORMAL,
                source="config_manager"
            )

            success = await self.broker.publish(message, "system.config.change")

            if success:
                self.stats['config_changes_sent'] += 1
                logger.info(f"Published configuration change by {changed_by}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish config change: {str(e)}")
            self.stats['errors'] += 1
            return False

    async def publish_error_report(self, error_data: Dict[str, Any],
                                 severity: AlertSeverity = AlertSeverity.ERROR) -> bool:
        """
        Publish an error report.

        Args:
            error_data: Error report data
            severity: Error severity

        Returns:
            bool: True if error report published successfully
        """
        try:
            event_id = f"error_{int(time.time() * 1000)}"

            event = SystemEvent(
                event_id=event_id,
                event_type=SystemEventType.ERROR_REPORT,
                source=error_data.get("source", "unknown"),
                severity=severity,
                message=error_data.get("message", "Error occurred"),
                details=error_data,
                category="error",
                tags=["error", error_data.get("type", "unknown")]
            )

            message = Message(
                type=MessageType.SYSTEM_ALERT,
                topic=f"system.alert.{severity.value}",
                payload={
                    "event": event.__dict__,
                    "error_data": error_data,
                    "node_id": self.node_id
                },
                headers={
                    "event_type": event.event_type.value,
                    "error_type": error_data.get("type", "unknown"),
                    "severity": severity.value,
                    "node_id": self.node_id
                },
                priority=self._severity_to_priority(severity),
                source="error_handler"
            )

            success = await self.broker.publish(message, f"system.alert.{severity.value}")

            if success:
                logger.error(f"Published error report: {event.message}")

            return success

        except Exception as e:
            logger.error(f"Failed to publish error report: {str(e)}")
            return False

    async def register_service(self, service_info: ServiceInfo) -> bool:
        """
        Register a service with the system producer.

        Args:
            service_info: Service information

        Returns:
            bool: True if service registered successfully
        """
        try:
            self.services[service_info.service_id] = service_info

            # Publish service registration event
            await self.publish_health_check(
                service_id=service_info.service_id,
                status=service_info.status,
                details={
                    "action": "register",
                    "service_info": service_info.__dict__
                }
            )

            logger.info(f"Registered service: {service_info.service_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {service_info.service_id}: {str(e)}")
            return False

    async def unregister_service(self, service_id: str) -> bool:
        """
        Unregister a service from the system producer.

        Args:
            service_id: ID of the service to unregister

        Returns:
            bool: True if service unregistered successfully
        """
        try:
            if service_id in self.services:
                service_info = self.services[service_id]
                del self.services[service_id]

                # Publish service unregistration event
                await self.publish_health_check(
                    service_id=service_id,
                    status=ServiceStatus.STOPPED,
                    details={
                        "action": "unregister",
                        "service_info": service_info.__dict__
                    }
                )

                logger.info(f"Unregistered service: {service_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unregister service {service_id}: {str(e)}")
            return False

    async def _monitoring_loop(self):
        """Main monitoring loop for collecting metrics."""
        while self.monitoring_enabled:
            try:
                # Collect resource metrics
                metrics = self._collect_resource_metrics()
                await self.publish_metrics(metrics)

                # Check for critical resource usage
                if metrics.cpu_percent > 90:
                    await self.publish_alert(SystemEvent(
                        event_id=f"cpu_alert_{int(time.time())}",
                        event_type=SystemEventType.ALERT,
                        source="resource_monitor",
                        severity=AlertSeverity.CRITICAL,
                        message=f"High CPU usage: {metrics.cpu_percent}%",
                        details={"cpu_percent": metrics.cpu_percent},
                        category="resources",
                        tags=["cpu", "high_usage"]
                    ))

                if metrics.memory_percent > 90:
                    await self.publish_alert(SystemEvent(
                        event_id=f"memory_alert_{int(time.time())}",
                        event_type=SystemEventType.ALERT,
                        source="resource_monitor",
                        severity=AlertSeverity.CRITICAL,
                        message=f"High memory usage: {metrics.memory_percent}%",
                        details={"memory_percent": metrics.memory_percent},
                        category="resources",
                        tags=["memory", "high_usage"]
                    ))

                if metrics.disk_percent > 90:
                    await self.publish_alert(SystemEvent(
                        event_id=f"disk_alert_{int(time.time())}",
                        event_type=SystemEventType.ALERT,
                        source="resource_monitor",
                        severity=AlertSeverity.CRITICAL,
                        message=f"High disk usage: {metrics.disk_percent}%",
                        details={"disk_percent": metrics.disk_percent},
                        category="resources",
                        tags=["disk", "high_usage"]
                    ))

                # Health check for registered services
                for service_id, service_info in self.services.items():
                    if service_info.health_check_url:
                        await self._check_service_health(service_id, service_info)

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retrying

    def _collect_resource_metrics(self) -> ResourceMetrics:
        """Collect current resource usage metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            process_count = len(psutil.pids())

            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                load_avg = list(psutil.getloadavg())

            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_available=memory.available,
                disk_percent=disk.percent,
                disk_used=disk.used,
                disk_free=disk.free,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                load_average=load_avg
            )
        except Exception as e:
            logger.error(f"Failed to collect resource metrics: {str(e)}")
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used=0,
                memory_available=0,
                disk_percent=0.0,
                disk_used=0,
                disk_free=0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                process_count=0
            )

    async def _check_service_health(self, service_id: str, service_info: ServiceInfo):
        """Check health of a specific service."""
        try:
            # Simple health check - in a real implementation, this would
            # make HTTP requests or other health check mechanisms
            # For now, we'll just update the timestamp
            service_info.last_health_check = time.time()

            await self.publish_health_check(
                service_id=service_id,
                status=service_info.status,
                details={
                    "uptime": service_info.uptime,
                    "last_check": service_info.last_health_check,
                    "metrics": service_info.metrics
                }
            )

        except Exception as e:
            logger.error(f"Failed to check health for service {service_id}: {str(e)}")

    async def publish_startup_event(self):
        """Publish system startup event."""
        event = SystemEvent(
            event_id=f"startup_{int(time.time())}",
            event_type=SystemEventType.SERVICE_STATUS,
            source="system_producer",
            severity=AlertSeverity.INFO,
            message=f"System producer started on node {self.node_id}",
            details={
                "system_info": self.system_info.__dict__,
                "monitoring_enabled": self.monitoring_enabled,
                "monitoring_interval": self.monitoring_interval
            },
            category="system",
            tags=["startup", "system"]
        )

        await self.publish_alert(event)

    def _severity_to_priority(self, severity: AlertSeverity) -> MessagePriority:
        """Convert alert severity to message priority."""
        severity_map = {
            AlertSeverity.INFO: MessagePriority.LOW,
            AlertSeverity.WARNING: MessagePriority.NORMAL,
            AlertSeverity.ERROR: MessagePriority.HIGH,
            AlertSeverity.CRITICAL: MessagePriority.HIGH,
            AlertSeverity.EMERGENCY: MessagePriority.CRITICAL
        }
        return severity_map.get(severity, MessagePriority.NORMAL)

    def get_stats(self) -> Dict[str, Any]:
        """Get producer statistics."""
        return {
            **self.stats,
            'node_id': self.node_id,
            'services_count': len(self.services),
            'active_alerts': len(self.active_alerts),
            'metrics_buffer_size': len(self.metrics_buffer),
            'monitoring_enabled': self.monitoring_enabled,
            'system_info': self.system_info.__dict__
        }

    async def shutdown(self):
        """Shutdown the system producer gracefully."""
        try:
            self.monitoring_enabled = False

            # Publish shutdown event
            event = SystemEvent(
                event_id=f"shutdown_{int(time.time())}",
                event_type=SystemEventType.SERVICE_STATUS,
                source="system_producer",
                severity=AlertSeverity.INFO,
                message=f"System producer shutting down on node {self.node_id}",
                details={
                    "final_stats": self.get_stats()
                },
                category="system",
                tags=["shutdown", "system"]
            )

            await self.publish_alert(event)

            # Clear data
            self.services.clear()
            self.active_alerts.clear()
            self.metrics_buffer.clear()

            logger.info(f"System producer for node {self.node_id} shutdown complete")

        except Exception as e:
            logger.error(f"Error during system producer shutdown: {str(e)}")


# Export main classes
__all__ = [
    'SystemProducer',
    'SystemEvent',
    'SystemInfo',
    'ResourceMetrics',
    'ServiceInfo',
    'SystemEventType',
    'AlertSeverity',
    'ServiceStatus'
]