#!/usr/bin/env python3
"""
DMLogn8n Service Registry - Global Service Discovery and Registration
Central registry for all platform services with automatic discovery
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import aiofiles
import aiofiles.os
from pathlib import Path
import socket
import aiohttp

class ServiceType(Enum):
    PLATFORM_SERVICE = "platform_service"
    API_SERVICE = "api_service"
    WORKFLOW_SERVICE = "workflow_service"
    DATABASE_SERVICE = "database_service"
    EXTERNAL_SERVICE = "external_service"
    WORKER_SERVICE = "worker_service"

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

@dataclass
class ServiceEndpoint:
    host: str
    port: int
    protocol: str = "http"
    path: str = ""
    health_check_path: str = "/health"
    weight: int = 1
    tags: List[str] = field(default_factory=list)

@dataclass
class ServiceRegistration:
    id: str
    name: str
    service_type: ServiceType
    version: str
    endpoints: List[ServiceEndpoint]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    health_check_interval: int = 30
    heartbeat_interval: int = 10
    ttl: int = 60
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    status: ServiceStatus = ServiceStatus.HEALTHY

@dataclass
class ServiceQuery:
    service_type: Optional[ServiceType] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ServiceStatus] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    healthy_only: bool = True

class ServiceRegistry:
    """
    Global service registry with automatic discovery and health monitoring
    """

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.logger = logging.getLogger('ServiceRegistry')
        self.services: Dict[str, ServiceRegistration] = {}
        self.service_watchers: Dict[str, List[Callable]] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        self.registry_file = "/home/activeloguser/DMLogn8n/data/service_registry.json"
        self.metrics = {
            'total_services': 0,
            'healthy_services': 0,
            'unhealthy_services': 0,
            'registrations': 0,
            'deregistrations': 0,
            'heartbeats_received': 0,
            'health_checks_performed': 0
        }

    async def initialize(self):
        """Initialize the service registry"""
        self.logger.info("Initializing Service Registry...")

        # Ensure data directory exists
        await aiofiles.os.makedirs(Path(self.registry_file).parent, exist_ok=True)

        # Load existing registry
        await self._load_registry()

        # Start background tasks
        self.running = True
        asyncio.create_task(self._cleanup_expired_services())

        self.logger.info("Service Registry initialized")

    async def register_service(
        self,
        name: str,
        service_type: str,
        host: str = "localhost",
        ports: List[int] = None,
        version: str = "1.0.0",
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        service_id: str = None,
        **kwargs
    ) -> str:
        """
        Register a new service
        """
        if service_id is None:
            service_id = str(uuid.uuid4())

        # Create endpoints
        endpoints = []
        if ports:
            for port in ports:
                endpoint = ServiceEndpoint(
                    host=host,
                    port=port,
                    **kwargs
                )
                endpoints.append(endpoint)

        # Create registration
        registration = ServiceRegistration(
            id=service_id,
            name=name,
            service_type=ServiceType(service_type),
            version=version,
            endpoints=endpoints,
            metadata=metadata or {},
            tags=tags or [],
            registered_at=time.time(),
            last_heartbeat=time.time()
        )

        # Add to registry
        self.services[service_id] = registration
        self.metrics['total_services'] += 1
        self.metrics['registrations'] += 1

        # Start health monitoring
        await self._start_service_monitoring(service_id)

        # Save registry
        await self._save_registry()

        # Notify watchers
        await self._notify_watchers('registered', registration)

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("service.registered", {
                "service_id": service_id,
                "name": name,
                "service_type": service_type,
                "host": host,
                "ports": ports
            })

        self.logger.info(f"Service registered: {name} ({service_id})")
        return service_id

    async def deregister_service(self, service_id: str):
        """Deregister a service"""
        if service_id not in self.services:
            return False

        service = self.services[service_id]

        # Stop monitoring
        await self._stop_service_monitoring(service_id)

        # Remove from registry
        del self.services[service_id]
        self.metrics['total_services'] -= 1
        self.metrics['deregistrations'] += 1

        # Save registry
        await self._save_registry()

        # Notify watchers
        await self._notify_watchers('deregistered', service)

        # Publish event
        if self.event_bus:
            await self.event_bus.publish("service.deregistered", {
                "service_id": service_id,
                "name": service.name
            })

        self.logger.info(f"Service deregistered: {service.name} ({service_id})")
        return True

    async def update_service_heartbeat(self, service_id: str, status: ServiceStatus = None):
        """Update service heartbeat"""
        if service_id not in self.services:
            return False

        service = self.services[service_id]
        service.last_heartbeat = time.time()

        if status:
            old_status = service.status
            service.status = status

            # Notify on status change
            if old_status != status:
                await self._notify_watchers('status_changed', service)

                if self.event_bus:
                    await self.event_bus.publish("service.status_changed", {
                        "service_id": service_id,
                        "name": service.name,
                        "old_status": old_status.value,
                        "new_status": status.value
                    })

        self.metrics['heartbeats_received'] += 1
        return True

    async def discover_services(self, query: ServiceQuery = None) -> List[ServiceRegistration]:
        """
        Discover services based on query criteria
        """
        if query is None:
            query = ServiceQuery()

        results = []
        current_time = time.time()

        for service in self.services.values():
            # Check if service is expired
            if current_time - service.last_heartbeat > service.ttl:
                continue

            # Apply filters
            if query.service_type and service.service_type != query.service_type:
                continue

            if query.name and query.name.lower() not in service.name.lower():
                continue

            if query.tags and not any(tag in service.tags for tag in query.tags):
                continue

            if query.status and service.status != query.status:
                continue

            if query.healthy_only and service.status not in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                continue

            # Apply metadata filters
            if query.metadata_filters:
                if not all(service.metadata.get(k) == v for k, v in query.metadata_filters.items()):
                    continue

            results.append(service)

        return results

    async def get_service_endpoints(self, service_name: str, healthy_only: bool = True) -> List[ServiceEndpoint]:
        """Get endpoints for a specific service"""
        query = ServiceQuery(
            name=service_name,
            healthy_only=healthy_only,
            status=ServiceStatus.HEALTHY if healthy_only else None
        )

        services = await self.discover_services(query)
        endpoints = []

        for service in services:
            endpoints.extend(service.endpoints)

        return endpoints

    async def get_load_balanced_endpoint(self, service_name: str, strategy: str = "round_robin") -> Optional[ServiceEndpoint]:
        """
        Get a load-balanced endpoint for a service
        """
        endpoints = await self.get_service_endpoints(service_name)

        if not endpoints:
            return None

        if strategy == "round_robin":
            # Simple round-robin based on current time
            index = int(time.time()) % len(endpoints)
            return endpoints[index]
        elif strategy == "weighted":
            # Weighted random selection
            total_weight = sum(ep.weight for ep in endpoints)
            if total_weight == 0:
                return endpoints[0]

            import random
            r = random.uniform(0, total_weight)
            current_weight = 0

            for endpoint in endpoints:
                current_weight += endpoint.weight
                if r <= current_weight:
                    return endpoint

        return endpoints[0]

    def watch_services(self, callback: Callable, query: ServiceQuery = None) -> str:
        """
        Watch for service changes
        """
        watcher_id = str(uuid.uuid4())

        if watcher_id not in self.service_watchers:
            self.service_watchers[watcher_id] = []

        self.service_watchers[watcher_id].append({
            'callback': callback,
            'query': query
        })

        return watcher_id

    def stop_watching(self, watcher_id: str):
        """Stop watching services"""
        if watcher_id in self.service_watchers:
            del self.service_watchers[watcher_id]

    async def _start_service_monitoring(self, service_id: str):
        """Start health monitoring for a service"""
        service = self.services[service_id]

        # Start heartbeat monitoring
        if service.heartbeat_interval > 0:
            self.heartbeat_tasks[service_id] = asyncio.create_task(
                self._monitor_heartbeat(service_id)
            )

        # Start health checks
        if service.health_check_interval > 0:
            self.health_check_tasks[service_id] = asyncio.create_task(
                self._monitor_service_health(service_id)
            )

    async def _stop_service_monitoring(self, service_id: str):
        """Stop health monitoring for a service"""
        # Cancel heartbeat task
        if service_id in self.heartbeat_tasks:
            self.heartbeat_tasks[service_id].cancel()
            del self.heartbeat_tasks[service_id]

        # Cancel health check task
        if service_id in self.health_check_tasks:
            self.health_check_tasks[service_id].cancel()
            del self.health_check_tasks[service_id]

    async def _monitor_heartbeat(self, service_id: str):
        """Monitor service heartbeats"""
        while self.running:
            try:
                service = self.services[service_id]
                current_time = time.time()

                # Check if heartbeat is expired
                if current_time - service.last_heartbeat > service.ttl:
                    if service.status != ServiceStatus.OFFLINE:
                        await self.update_service_heartbeat(service_id, ServiceStatus.OFFLINE)
                        self.logger.warning(f"Service {service.name} heartbeat expired")

                await asyncio.sleep(service.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring heartbeat for {service_id}: {e}")
                await asyncio.sleep(5)

    async def _monitor_service_health(self, service_id: str):
        """Perform active health checks"""
        while self.running:
            try:
                service = self.services[service_id]

                # Perform health check for each endpoint
                healthy_endpoints = 0
                total_endpoints = len(service.endpoints)

                for endpoint in service.endpoints:
                    if await self._check_endpoint_health(endpoint):
                        healthy_endpoints += 1

                # Determine service status
                if healthy_endpoints == 0:
                    new_status = ServiceStatus.UNHEALTHY
                elif healthy_endpoints < total_endpoints:
                    new_status = ServiceStatus.DEGRADED
                else:
                    new_status = ServiceStatus.HEALTHY

                if service.status != new_status:
                    await self.update_service_heartbeat(service_id, new_status)

                # Update metrics
                self.metrics['health_checks_performed'] += 1
                self._update_service_metrics()

                await asyncio.sleep(service.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error performing health check for {service_id}: {e}")
                await asyncio.sleep(10)

    async def _check_endpoint_health(self, endpoint: ServiceEndpoint) -> bool:
        """Check health of a single endpoint"""
        try:
            url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}{endpoint.health_check_path}"

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _cleanup_expired_services(self):
        """Clean up expired services"""
        while self.running:
            try:
                current_time = time.time()
                expired_services = []

                for service_id, service in self.services.items():
                    if current_time - service.last_heartbeat > service.ttl * 2:
                        expired_services.append(service_id)

                for service_id in expired_services:
                    await self.deregister_service(service_id)
                    self.logger.info(f"Cleaned up expired service: {service_id}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error cleaning up expired services: {e}")
                await asyncio.sleep(60)

    async def _notify_watchers(self, event_type: str, service: ServiceRegistration):
        """Notify all watchers of service changes"""
        for watcher_callbacks in self.service_watchers.values():
            for watcher_info in watcher_callbacks:
                try:
                    query = watcher_info['query']

                    # Check if service matches watcher's query
                    if self._service_matches_query(service, query):
                        await watcher_info['callback'](event_type, service)

                except Exception as e:
                    self.logger.error(f"Error notifying watcher: {e}")

    def _service_matches_query(self, service: ServiceRegistration, query: ServiceQuery) -> bool:
        """Check if service matches query criteria"""
        if query.service_type and service.service_type != query.service_type:
            return False

        if query.name and query.name.lower() not in service.name.lower():
            return False

        if query.tags and not any(tag in service.tags for tag in query.tags):
            return False

        if query.status and service.status != query.status:
            return False

        if query.metadata_filters:
            if not all(service.metadata.get(k) == v for k, v in query.metadata_filters.items()):
                return False

        return True

    def _update_service_metrics(self):
        """Update service metrics"""
        self.metrics['healthy_services'] = sum(
            1 for s in self.services.values()
            if s.status == ServiceStatus.HEALTHY
        )
        self.metrics['unhealthy_services'] = sum(
            1 for s in self.services.values()
            if s.status == ServiceStatus.UNHEALTHY
        )

    async def _load_registry(self):
        """Load registry from file"""
        try:
            if await aiofiles.os.path.exists(self.registry_file):
                async with aiofiles.open(self.registry_file, 'r') as f:
                    data = json.loads(await f.read())

                for service_data in data.get('services', []):
                    service = ServiceRegistration(**service_data)
                    self.services[service.id] = service

                    # Restart monitoring for loaded services
                    if self.running:
                        await self._start_service_monitoring(service.id)

                self.logger.info(f"Loaded {len(self.services)} services from registry")

        except Exception as e:
            self.logger.error(f"Error loading registry: {e}")

    async def _save_registry(self):
        """Save registry to file"""
        try:
            data = {
                'services': [asdict(service) for service in self.services.values()],
                'last_updated': time.time(),
                'metrics': self.metrics
            }

            async with aiofiles.open(self.registry_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))

        except Exception as e:
            self.logger.error(f"Error saving registry: {e}")

    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status and metrics"""
        self._update_service_metrics()

        return {
            'metrics': self.metrics,
            'total_services': len(self.services),
            'services_by_type': {
                st.value: len([s for s in self.services.values() if s.service_type == st])
                for st in ServiceType
            },
            'services_by_status': {
                ss.value: len([s for s in self.services.values() if s.status == ss])
                for ss in ServiceStatus
            },
            'watchers': len(self.service_watchers),
            'monitoring_tasks': {
                'heartbeat': len(self.heartbeat_tasks),
                'health_checks': len(self.health_check_tasks)
            }
        }

    async def shutdown(self):
        """Shutdown the service registry"""
        self.logger.info("Shutting down Service Registry...")

        self.running = False

        # Cancel all monitoring tasks
        for task in list(self.heartbeat_tasks.values()) + list(self.health_check_tasks.values()):
            task.cancel()

        # Wait for tasks to complete
        if self.heartbeat_tasks or self.health_check_tasks:
            await asyncio.gather(
                *list(self.heartbeat_tasks.values()) + list(self.health_check_tasks.values()),
                return_exceptions=True
            )

        # Save final registry state
        await self._save_registry()

        self.logger.info("Service Registry shutdown complete")

# Service Registry Client
class ServiceRegistryClient:
    """Client for interacting with the service registry"""

    def __init__(self, registry_url: str = "http://localhost:6381"):
        self.registry_url = registry_url
        self.session = None
        self.service_id = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def register(
        self,
        name: str,
        service_type: str,
        host: str = "localhost",
        ports: List[int] = None,
        **kwargs
    ) -> str:
        """Register this service"""
        async with self.session.post(
            f"{self.registry_url}/register",
            json={
                "name": name,
                "service_type": service_type,
                "host": host,
                "ports": ports or [],
                **kwargs
            }
        ) as response:
            data = await response.json()
            self.service_id = data.get('service_id')
            return self.service_id

    async def heartbeat(self, status: str = "healthy"):
        """Send heartbeat"""
        if not self.service_id:
            return False

        async with self.session.post(
            f"{self.registry_url}/heartbeat/{self.service_id}",
            json={"status": status}
        ) as response:
            return response.status == 200

    async def deregister(self):
        """Deregister this service"""
        if not self.service_id:
            return False

        async with self.session.delete(
            f"{self.registry_url}/deregister/{self.service_id}"
        ) as response:
            return response.status == 200

    async def discover(self, service_name: str = None, **kwargs) -> List[Dict]:
        """Discover services"""
        params = {}
        if service_name:
            params['name'] = service_name
        params.update(kwargs)

        async with self.session.get(
            f"{self.registry_url}/discover",
            params=params
        ) as response:
            data = await response.json()
            return data.get('services', [])