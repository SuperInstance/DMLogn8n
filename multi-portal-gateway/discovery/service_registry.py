#!/usr/bin/env python3
"""
Service Registry for DMLogn8n Multi-Agent Platform

This module provides comprehensive service registration and discovery including:
- Automatic service registration and deregistration
- Service metadata management
- Service dependency tracking
- Service topology mapping
- Service lifecycle management
"""

import asyncio
import json
import logging
import uuid
import socket
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import consul.aio
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Service types in DMLogn8n platform"""
    API_GATEWAY = "api-gateway"
    AGENT_SERVICE = "agent-service"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKGROUND_WORKER = "background-worker"
    MONITORING = "monitoring"
    CACHE = "cache"
    MESSAGE_QUEUE = "message-queue"
    STORAGE = "storage"
    AUTH_SERVICE = "auth-service"

class ServiceStatus(Enum):
    """Service status values"""
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    DRAINING = "draining"
    TERMINATING = "terminating"

@dataclass
class ServiceMetadata:
    """Service metadata structure"""
    service_id: str
    service_name: str
    service_type: ServiceType
    version: str
    description: str
    owner: str
    team: str
    environment: str  # dev, staging, prod
    region: str
    availability_zone: str
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    host: str
    port: int
    protocol: str = "http"
    path: str = "/"
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    is_public: bool = False

@dataclass
class HealthCheck:
    """Health check configuration"""
    interval: str = "10s"
    timeout: str = "3s"
    deregister_critical_service_after: str = "30s"
    success_before_passing: int = 3
    failures_before_critical: int = 3
    check_type: str = "http"  # http, tcp, script, grpc

@dataclass
class ServiceRegistration:
    """Complete service registration data"""
    metadata: ServiceMetadata
    endpoint: ServiceEndpoint
    health_check: HealthCheck
    ttl: Optional[str] = None
    enable_tag_override: bool = False
    connect: Optional[Dict[str, Any]] = None
    proxy: Optional[Dict[str, Any]] = None

class ServiceRegistry:
    """
    Service registry for managing DMLogn8n platform services
    """

    def __init__(self, consul_manager):
        self.consul_manager = consul_manager
        self.consul = consul_manager.consul
        self.registered_services = {}
        self.service_dependencies = {}
        self.service_topology = {}
        self.watchers = {}
        self._shutdown = False

    async def register_service(self, registration: ServiceRegistration) -> bool:
        """Register a new service with Consul"""
        try:
            service_id = registration.metadata.service_id

            # Prepare service registration data
            service_data = {
                'ID': service_id,
                'Name': registration.metadata.service_name,
                'Tags': self._build_service_tags(registration),
                'Address': registration.endpoint.host,
                'Port': registration.endpoint.port,
                'Meta': self._build_service_metadata(registration),
                'EnableTagOverride': registration.enable_tag_override,
                'Check': self._build_health_check(registration)
            }

            # Add Connect configuration if provided
            if registration.connect:
                service_data['Connect'] = registration.connect

            # Add Proxy configuration if provided
            if registration.proxy:
                service_data['Proxy'] = registration.proxy

            # Register with Consul
            success = await self.consul.agent.service.register(**service_data)

            if success:
                # Store registration locally
                self.registered_services[service_id] = registration

                # Update service topology
                await self._update_service_topology(registration)

                # Update dependency tracking
                await self._update_dependencies(registration)

                # Store extended metadata in KV store
                await self._store_extended_metadata(registration)

                # Start monitoring the service
                asyncio.create_task(self._monitor_service(service_id))

                logger.info(f"Service registered successfully: {service_id}")
                return True
            else:
                logger.error(f"Failed to register service: {service_id}")
                return False

        except Exception as e:
            logger.error(f"Service registration error: {e}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul"""
        try:
            # Deregister from Consul
            await self.consul.agent.service.deregister(service_id)

            # Remove from local registry
            if service_id in self.registered_services:
                del self.registered_services[service_id]

            # Update topology
            await self._remove_from_topology(service_id)

            # Clean up metadata
            await self._cleanup_metadata(service_id)

            logger.info(f"Service deregistered: {service_id}")
            return True

        except Exception as e:
            logger.error(f"Service deregistration error: {e}")
            return False

    async def discover_services(self,
                              service_name: Optional[str] = None,
                              service_type: Optional[ServiceType] = None,
                              tags: Optional[List[str]] = None,
                              healthy_only: bool = True,
                              passing_only: bool = True) -> List[Dict[str, Any]]:
        """Discover services based on criteria"""
        try:
            services = []

            if service_name:
                # Get specific service
                index, data = await self.consul.health.service(
                    service_name,
                    passing=passing_only
                )
                services.extend(data)
            else:
                # Get all services
                _, all_services = await self.consul.health.state('any')

                for service in all_services:
                    if not healthy_only or service['Status'] == 'passing':
                        # Get full service details
                        index, service_data = await self.consul.health.service(
                            service['ServiceID'],
                            passing=passing_only
                        )
                        services.extend(service_data)

            # Filter by service type
            if service_type:
                services = [
                    s for s in services
                    if self._get_service_type_from_tags(s) == service_type.value
                ]

            # Filter by tags
            if tags:
                services = [
                    s for s in services
                    if all(tag in s['Service']['Tags'] for tag in tags)
                ]

            # Add extended metadata
            for service in services:
                await self._add_extended_metadata(service)

            return services

        except Exception as e:
            logger.error(f"Service discovery error: {e}")
            return []

    async def get_service_details(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific service"""
        try:
            # Get service health
            index, health_data = await self.consul.health.service(service_id)

            if not health_data:
                return None

            service = health_data[0]

            # Add extended metadata
            await self._add_extended_metadata(service)

            # Add dependency information
            service['dependencies'] = await self._get_service_dependencies(service_id)

            # Add dependent services
            service['dependents'] = await self._get_dependent_services(service_id)

            return service

        except Exception as e:
            logger.error(f"Failed to get service details: {e}")
            return None

    async def update_service_metadata(self, service_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Update service metadata"""
        try:
            if service_id not in self.registered_services:
                logger.error(f"Service not found: {service_id}")
                return False

            registration = self.registered_services[service_id]

            # Update metadata
            for key, value in metadata_updates.items():
                if hasattr(registration.metadata, key):
                    setattr(registration.metadata, key, value)

            # Store updated metadata
            await self._store_extended_metadata(registration)

            logger.info(f"Updated metadata for service: {service_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update service metadata: {e}")
            return False

    async def set_service_maintenance(self, service_id: str, reason: str, enabled: bool = True) -> bool:
        """Enable or disable maintenance mode for a service"""
        try:
            if enabled:
                await self.consul.agent.service.maintenance(service_id, reason, enabled=True)
                logger.info(f"Maintenance mode enabled for service: {service_id}")
            else:
                await self.consul.agent.service.maintenance(service_id, enabled=False)
                logger.info(f"Maintenance mode disabled for service: {service_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to set maintenance mode: {e}")
            return False

    async def get_service_topology(self) -> Dict[str, Any]:
        """Get complete service topology and dependency map"""
        try:
            topology = {
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'dependencies': {},
                'clusters': {},
                'critical_paths': []
            }

            # Get all services
            all_services = await self.discover_services()

            # Build service nodes
            for service in all_services:
                service_id = service['Service']['ID']
                topology['services'][service_id] = {
                    'name': service['Service']['Service'],
                    'type': self._get_service_type_from_tags(service),
                    'status': service['Checks'][0]['Status'],
                    'metadata': service.get('extended_metadata', {}),
                    'endpoint': {
                        'host': service['Service']['Address'],
                        'port': service['Service']['Port']
                    }
                }

            # Build dependency graph
            for service_id, service_data in topology['services'].items():
                dependencies = await self._get_service_dependencies(service_id)
                topology['dependencies'][service_id] = dependencies

            # Identify clusters (services with similar dependencies)
            topology['clusters'] = self._identify_service_clusters(topology)

            # Find critical paths
            topology['critical_paths'] = self._find_critical_paths(topology)

            return topology

        except Exception as e:
            logger.error(f"Failed to get service topology: {e}")
            return {}

    async def watch_service_changes(self, callback):
        """Watch for service changes and notify via callback"""
        try:
            index = None

            while not self._shutdown:
                try:
                    # Use blocking query to watch for changes
                    index, services = await self.consul.health.service(
                        index=index,
                        wait='30s'
                    )

                    # Notify callback of changes
                    if callback:
                        await callback(services)

                except Exception as e:
                    logger.error(f"Service watch error: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Failed to watch service changes: {e}")

    def _build_service_tags(self, registration: ServiceRegistration) -> List[str]:
        """Build list of tags for service registration"""
        tags = [
            f"service-type:{registration.metadata.service_type.value}",
            f"version:{registration.metadata.version}",
            f"environment:{registration.metadata.environment}",
            f"region:{registration.metadata.region}",
            f"team:{registration.metadata.team}",
            f"owner:{registration.metadata.owner}"
        ]

        # Add capabilities as tags
        tags.extend([f"capability:{cap}" for cap in registration.metadata.capabilities])

        # Add custom tags
        tags.extend(registration.metadata.tags)

        return tags

    def _build_service_metadata(self, registration: ServiceRegistration) -> Dict[str, str]:
        """Build metadata dictionary for service registration"""
        metadata = {
            'service_id': registration.metadata.service_id,
            'service_type': registration.metadata.service_type.value,
            'version': registration.metadata.version,
            'description': registration.metadata.description,
            'owner': registration.metadata.owner,
            'team': registration.metadata.team,
            'environment': registration.metadata.environment,
            'region': registration.metadata.region,
            'availability_zone': registration.metadata.availability_zone,
            'registered_at': datetime.now().isoformat()
        }

        # Add custom attributes
        for key, value in registration.metadata.custom_attributes.items():
            metadata[f"custom_{key}"] = str(value)

        return metadata

    def _build_health_check(self, registration: ServiceRegistration) -> Dict[str, Any]:
        """Build health check configuration"""
        health_url = f"{registration.endpoint.protocol}://{registration.endpoint.host}:{registration.endpoint.port}{registration.endpoint.health_endpoint}"

        check = {
            'HTTP': health_url,
            'Interval': registration.health_check.interval,
            'Timeout': registration.health_check.timeout,
            'DeregisterCriticalServiceAfter': registration.health_check.deregister_critical_service_after,
            'SuccessBeforePassing': registration.health_check.success_before_passing,
            'FailuresBeforeCritical': registration.health_check.failures_before_critical
        }

        return check

    async def _store_extended_metadata(self, registration: ServiceRegistration):
        """Store extended metadata in Consul KV store"""
        try:
            kv_path = f"dmlogn8n/services/{registration.metadata.service_id}/metadata"

            metadata = {
                'metadata': asdict(registration.metadata),
                'endpoint': asdict(registration.endpoint),
                'health_check': asdict(registration.health_check),
                'registered_at': datetime.now().isoformat()
            }

            await self.consul.kv.put(kv_path, json.dumps(metadata))

        except Exception as e:
            logger.error(f"Failed to store extended metadata: {e}")

    async def _add_extended_metadata(self, service: Dict[str, Any]):
        """Add extended metadata to service data"""
        try:
            service_id = service['Service']['ID']
            kv_path = f"dmlogn8n/services/{service_id}/metadata"

            _, data = await self.consul.kv.get(kv_path)
            if data:
                metadata = json.loads(data['Value'].decode('utf-8'))
                service['extended_metadata'] = metadata

        except Exception as e:
            logger.error(f"Failed to add extended metadata: {e}")

    async def _update_service_topology(self, registration: ServiceRegistration):
        """Update service topology with new service"""
        try:
            service_id = registration.metadata.service_id

            # Update topology data
            self.service_topology[service_id] = {
                'service_type': registration.metadata.service_type.value,
                'dependencies': registration.metadata.dependencies,
                'registered_at': datetime.now().isoformat()
            }

            # Store topology in KV
            topology_path = "dmlogn8n/topology/current"
            await self.consul.kv.put(
                topology_path,
                json.dumps(self.service_topology)
            )

        except Exception as e:
            logger.error(f"Failed to update service topology: {e}")

    async def _update_dependencies(self, registration: ServiceRegistration):
        """Update service dependency tracking"""
        try:
            service_id = registration.metadata.service_id

            # Update dependency mappings
            for dependency in registration.metadata.dependencies:
                if dependency not in self.service_dependencies:
                    self.service_dependencies[dependency] = []

                if service_id not in self.service_dependencies[dependency]:
                    self.service_dependencies[dependency].append(service_id)

            # Store dependencies in KV
            deps_path = f"dmlogn8n/dependencies/{service_id}"
            await self.consul.kv.put(
                deps_path,
                json.dumps(registration.metadata.dependencies)
            )

        except Exception as e:
            logger.error(f"Failed to update dependencies: {e}")

    async def _get_service_dependencies(self, service_id: str) -> List[str]:
        """Get dependencies for a service"""
        try:
            deps_path = f"dmlogn8n/dependencies/{service_id}"
            _, data = await self.consul.kv.get(deps_path)

            if data:
                return json.loads(data['Value'].decode('utf-8'))

            return []

        except Exception as e:
            logger.error(f"Failed to get service dependencies: {e}")
            return []

    async def _get_dependent_services(self, service_id: str) -> List[str]:
        """Get services that depend on this service"""
        try:
            # Check dependency mappings
            return self.service_dependencies.get(service_id, [])

        except Exception as e:
            logger.error(f"Failed to get dependent services: {e}")
            return []

    async def _remove_from_topology(self, service_id: str):
        """Remove service from topology"""
        try:
            if service_id in self.service_topology:
                del self.service_topology[service_id]

            # Update KV store
            topology_path = "dmlogn8n/topology/current"
            await self.consul.kv.put(
                topology_path,
                json.dumps(self.service_topology)
            )

        except Exception as e:
            logger.error(f"Failed to remove from topology: {e}")

    async def _cleanup_metadata(self, service_id: str):
        """Clean up service metadata"""
        try:
            # Remove extended metadata
            metadata_path = f"dmlogn8n/services/{service_id}"
            await self.consul.kv.delete(metadata_path, recurse=True)

            # Remove dependencies
            deps_path = f"dmlogn8n/dependencies/{service_id}"
            await self.consul.kv.delete(deps_path)

        except Exception as e:
            logger.error(f"Failed to cleanup metadata: {e}")

    async def _monitor_service(self, service_id: str):
        """Monitor service health and status"""
        while not self._shutdown and service_id in self.registered_services:
            try:
                # Get service health
                index, health_data = await self.consul.health.service(service_id)

                if health_data:
                    service = health_data[0]
                    status = service['Checks'][0]['Status']

                    # Log status changes
                    current_status = getattr(self.registered_services[service_id], '_last_status', None)
                    if current_status != status:
                        logger.info(f"Service {service_id} status changed: {current_status} -> {status}")
                        setattr(self.registered_services[service_id], '_last_status', status)

                        # Emit status change event
                        await self.consul_manager.emit_event(
                            'service_status_change',
                            {
                                'service_id': service_id,
                                'old_status': current_status,
                                'new_status': status,
                                'timestamp': datetime.now().isoformat()
                            }
                        )

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Service monitoring error for {service_id}: {e}")
                await asyncio.sleep(10)

    def _get_service_type_from_tags(self, service: Dict[str, Any]) -> str:
        """Extract service type from service tags"""
        tags = service['Service']['Tags']
        for tag in tags:
            if tag.startswith('service-type:'):
                return tag.split(':', 1)[1]
        return 'unknown'

    def _identify_service_clusters(self, topology: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify service clusters based on common dependencies"""
        clusters = {}
        dependency_groups = {}

        # Group services by their dependency sets
        for service_id, dependencies in topology['dependencies'].items():
            deps_key = '|'.join(sorted(dependencies))
            if deps_key not in dependency_groups:
                dependency_groups[deps_key] = []
            dependency_groups[deps_key].append(service_id)

        # Create clusters
        for i, (deps_key, services) in enumerate(dependency_groups.items()):
            if len(services) > 1:
                clusters[f'cluster_{i+1}'] = {
                    'services': services,
                    'shared_dependencies': deps_key.split('|') if deps_key else []
                }

        return clusters

    def _find_critical_paths(self, topology: Dict[str, Any]) -> List[List[str]]:
        """Find critical paths in service dependency graph"""
        critical_paths = []

        # Find services with many dependents
        for service_id, dependents in topology['dependencies'].items():
            if len(dependents) >= 3:  # Arbitrary threshold
                critical_paths.append({
                    'type': 'hub_service',
                    'service': service_id,
                    'dependents': dependents,
                    'impact_score': len(dependents)
                })

        return critical_paths

    async def shutdown(self):
        """Shutdown service registry"""
        self._shutdown = True

        # Deregister all services
        for service_id in list(self.registered_services.keys()):
            await self.deregister_service(service_id)

        logger.info("Service registry shutdown completed")

# Export main classes
__all__ = [
    'ServiceRegistry',
    'ServiceRegistration',
    'ServiceMetadata',
    'ServiceEndpoint',
    'HealthCheck',
    'ServiceType',
    'ServiceStatus'
]