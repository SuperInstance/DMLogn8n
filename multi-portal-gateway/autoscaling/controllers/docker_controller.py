#!/usr/bin/env python3
"""
Docker Scaling Controller for DMLogn8n Auto-Scaling
Manages scaling of Docker Compose and standalone Docker containers
"""

import asyncio
import logging
import json
import yaml
import subprocess
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import docker
    from docker.errors import DockerException, NotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("Docker client not available. Install with: pip install docker")

@dataclass
class DockerService:
    name: str
    project: str
    image: str
    replicas: int
    running_replicas: int
    cpu_limit: str
    memory_limit: str
    ports: List[str]
    environment: Dict[str, str]
    networks: List[str]
    status: str

@dataclass
class ContainerMetrics:
    container_id: str
    name: str
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    network_rx_mb: float
    network_tx_mb: float
    created_at: datetime

class DockerController:
    """
    Controller for managing Docker-based scaling
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('docker_controller')

        if not DOCKER_AVAILABLE:
            self.logger.error("Docker client not available")
            raise ImportError("Docker client not available")

        # Initialize Docker client
        self._initialize_docker_client()

        # Configuration
        self.compose_file = config.get('compose_file', '/home/activeloguser/DMLogn8n/docker-compose.yml')
        self.project_name = config.get('project_name', 'dmlogn8n')
        self.scaling_timeout = config.get('scaling_timeout', 300)  # 5 minutes

        # Service configurations
        self.service_configs = self._load_service_configs()

        # Track scaling operations
        self.scaling_operations: Dict[str, Dict[str, Any]] = {}

    def _initialize_docker_client(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def _load_service_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load Docker service configurations"""
        try:
            configs = {
                'combat-engine': {
                    'service_name': 'combat-engine',
                    'image': 'dmlogn8n/combat-engine:latest',
                    'min_replicas': 1,
                    'max_replicas': 6,
                    'cpu_limit': '1.0',
                    'memory_limit': '2g',
                    'ports': ['8083:8083'],
                    'environment': {
                        'ENV': 'production',
                        'LOG_LEVEL': 'info'
                    },
                    'networks': ['dmlogn8n-network']
                },
                'ai-model-inference': {
                    'service_name': 'ai-model-inference',
                    'image': 'dmlogn8n/ai-model-inference:latest',
                    'min_replicas': 2,
                    'max_replicas': 8,
                    'cpu_limit': '2.0',
                    'memory_limit': '4g',
                    'ports': ['8085:8085'],
                    'environment': {
                        'ENV': 'production',
                        'MODEL_PATH': '/models',
                        'GPU_ENABLED': 'true'
                    },
                    'networks': ['dmlogn8n-network']
                },
                'websocket-gateway': {
                    'service_name': 'websocket-gateway',
                    'image': 'dmlogn8n/websocket-gateway:latest',
                    'min_replicas': 2,
                    'max_replicas': 10,
                    'cpu_limit': '0.5',
                    'memory_limit': '512m',
                    'ports': ['8086:8086'],
                    'environment': {
                        'ENV': 'production',
                        'MAX_CONNECTIONS': '10000'
                    },
                    'networks': ['dmlogn8n-network']
                }
            }

            # Try to load from compose file
            if Path(self.compose_file).exists():
                compose_config = self._load_compose_file()
                if compose_config:
                    # Merge with default configs
                    for service_name, service_config in compose_config.get('services', {}).items():
                        if service_name in configs:
                            # Update existing config
                            configs[service_name].update({
                                'image': service_config.get('image', configs[service_name]['image']),
                                'ports': service_config.get('ports', configs[service_name]['ports']),
                                'environment': {**configs[service_name]['environment'], **service_config.get('environment', {})},
                                'networks': service_config.get('networks', configs[service_name]['networks'])
                            })
                        else:
                            # Add new service config
                            configs[service_name] = {
                                'service_name': service_name,
                                'image': service_config.get('image', ''),
                                'min_replicas': 1,
                                'max_replicas': 5,
                                'cpu_limit': '1.0',
                                'memory_limit': '1g',
                                'ports': service_config.get('ports', []),
                                'environment': service_config.get('environment', {}),
                                'networks': service_config.get('networks', [])
                            }

            return configs

        except Exception as e:
            self.logger.error(f"Error loading service configs: {e}")
            return {}

    def _load_compose_file(self) -> Optional[Dict[str, Any]]:
        """Load Docker Compose configuration"""
        try:
            with open(self.compose_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Could not load compose file {self.compose_file}: {e}")
            return None

    async def get_instance_count(self, service_id: str) -> int:
        """Get current instance count for a service"""
        try:
            service_config = self.service_configs.get(service_id)
            if not service_config:
                self.logger.error(f"No service config found for: {service_id}")
                return 0

            service_name = service_config['service_name']

            # Get running containers for this service
            containers = self.docker_client.containers.list(
                filters={
                    'label': f'com.docker.compose.service={service_name}',
                    'status': 'running'
                }
            )

            return len(containers)

        except Exception as e:
            self.logger.error(f"Error getting instance count for {service_id}: {e}")
            return 0

    async def scale_up(self, service_id: str, desired_instances: int) -> bool:
        """Scale up a service"""
        try:
            current_instances = await self.get_instance_count(service_id)
            if desired_instances <= current_instances:
                self.logger.info(f"Service {service_id} already has {current_instances} instances")
                return True

            service_config = self.service_configs.get(service_id)
            if not service_config:
                self.logger.error(f"No service config found for: {service_id}")
                return False

            # Check against max replicas
            max_replicas = service_config.get('max_replicas', 5)
            if desired_instances > max_replicas:
                desired_instances = max_replicas
                self.logger.warning(f"Limited scaling to max replicas: {max_replicas}")

            success = await self._scale_service(service_id, desired_instances)
            if success:
                self.logger.info(f"Scaled up {service_id} to {desired_instances} instances")
                await self._log_scaling_event(service_id, current_instances, desired_instances, 'scale_up')

            return success

        except Exception as e:
            self.logger.error(f"Error scaling up {service_id}: {e}")
            return False

    async def scale_down(self, service_id: str, desired_instances: int) -> bool:
        """Scale down a service"""
        try:
            current_instances = await self.get_instance_count(service_id)
            if desired_instances >= current_instances:
                self.logger.info(f"Service {service_id} already has {current_instances} instances")
                return True

            service_config = self.service_configs.get(service_id)
            if not service_config:
                self.logger.error(f"No service config found for: {service_id}")
                return False

            # Check against min replicas
            min_replicas = service_config.get('min_replicas', 1)
            if desired_instances < min_replicas:
                desired_instances = min_replicas
                self.logger.warning(f"Limited scaling to min replicas: {min_replicas}")

            success = await self._scale_service(service_id, desired_instances)
            if success:
                self.logger.info(f"Scaled down {service_id} to {desired_instances} instances")
                await self._log_scaling_event(service_id, current_instances, desired_instances, 'scale_down')

            return success

        except Exception as e:
            self.logger.error(f"Error scaling down {service_id}: {e}")
            return False

    async def _scale_service(self, service_id: str, replicas: int) -> bool:
        """Perform the actual scaling operation"""
        try:
            service_config = self.service_configs.get(service_id)
            service_name = service_config['service_name']

            # Try to use Docker Compose first
            if Path(self.compose_file).exists():
                success = await self._scale_with_compose(service_name, replicas)
                if success:
                    return True

            # Fall back to manual container management
            return await self._scale_containers_manually(service_id, replicas)

        except Exception as e:
            self.logger.error(f"Error scaling service {service_id}: {e}")
            return False

    async def _scale_with_compose(self, service_name: str, replicas: int) -> bool:
        """Scale service using Docker Compose"""
        try:
            # Use docker-compose to scale the service
            cmd = [
                'docker-compose',
                '-f', self.compose_file,
                '-p', self.project_name,
                'up', '-d', '--scale', f'{service_name}={replicas}'
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.logger.info(f"Docker Compose scaling successful for {service_name}")
                return True
            else:
                self.logger.error(f"Docker Compose scaling failed for {service_name}: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"Error scaling with Docker Compose: {e}")
            return False

    async def _scale_containers_manually(self, service_id: str, replicas: int) -> bool:
        """Scale containers manually"""
        try:
            service_config = self.service_configs[service_id]
            current_containers = self._get_service_containers(service_id)

            # Scale up
            if len(current_containers) < replicas:
                containers_to_add = replicas - len(current_containers)
                for i in range(containers_to_add):
                    await self._create_container(service_config, len(current_containers) + i + 1)

            # Scale down
            elif len(current_containers) > replicas:
                containers_to_remove = len(current_containers) - replicas
                for i in range(containers_to_remove):
                    await self._remove_container(current_containers[-(i + 1)])

            # Wait for containers to be ready
            return await self._wait_for_containers_ready(service_id, replicas)

        except Exception as e:
            self.logger.error(f"Error scaling containers manually: {e}")
            return False

    def _get_service_containers(self, service_id: str) -> List[Any]:
        """Get containers for a service"""
        try:
            service_config = self.service_configs[service_id]
            service_name = service_config['service_name']

            containers = self.docker_client.containers.list(
                all=True,
                filters={
                    'label': f'service={service_id}',
                    'label': f'project={self.project_name}'
                }
            )

            return containers

        except Exception as e:
            self.logger.error(f"Error getting service containers: {e}")
            return []

    async def _create_container(self, service_config: Dict[str, Any], instance_number: int):
        """Create a new container"""
        try:
            service_name = service_config['service_name']
            container_name = f"{self.project_name}_{service_name}_{instance_number}"

            # Parse ports
            port_bindings = {}
            for port_mapping in service_config.get('ports', []):
                if ':' in port_mapping:
                    host_port, container_port = port_mapping.split(':')
                    port_bindings[int(container_port)] = int(host_port)

            # Parse resource limits
            cpu_limit = service_config.get('cpu_limit', '1.0')
            memory_limit = service_config.get('memory_limit', '1g')

            # Convert CPU limit to nano CPUs
            if cpu_limit.endswith('.0'):
                nano_cpus = int(float(cpu_limit) * 1e9)
            else:
                nano_cpus = int(float(cpu_limit) * 1e9)

            # Convert memory limit to bytes
            if memory_limit.endswith('g'):
                mem_limit = int(memory_limit[:-1]) * 1024 * 1024 * 1024
            elif memory_limit.endswith('m'):
                mem_limit = int(memory_limit[:-1]) * 1024 * 1024
            else:
                mem_limit = int(memory_limit)

            container = self.docker_client.containers.run(
                service_config['image'],
                name=container_name,
                detach=True,
                ports=port_bindings,
                environment=service_config.get('environment', {}),
                network_mode=service_config.get('networks', ['bridge'])[0] if service_config.get('networks') else None,
                labels={
                    'service': service_config['service_name'],
                    'project': self.project_name,
                    'managed_by': 'dmlogn8n-autoscaler'
                },
                nano_cpus=nano_cpus,
                mem_limit=mem_limit
            )

            self.logger.info(f"Created container: {container_name}")

        except Exception as e:
            self.logger.error(f"Error creating container: {e}")
            raise

    async def _remove_container(self, container: Any):
        """Remove a container"""
        try:
            container.stop()
            container.remove()
            self.logger.info(f"Removed container: {container.name}")
        except Exception as e:
            self.logger.error(f"Error removing container: {e}")

    async def _wait_for_containers_ready(self, service_id: str, expected_count: int, timeout: int = 300) -> bool:
        """Wait for containers to be ready"""
        try:
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                running_containers = self.docker_client.containers.list(
                    filters={
                        'label': f'service={service_id}',
                        'label': f'project={self.project_name}',
                        'status': 'running'
                    }
                )

                if len(running_containers) >= expected_count:
                    self.logger.info(f"All containers ready for service: {service_id}")
                    return True

                await asyncio.sleep(5)

            self.logger.error(f"Timeout waiting for containers to be ready for {service_id}")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for containers ready: {e}")
            return False

    async def get_container_metrics(self, service_id: str) -> List[ContainerMetrics]:
        """Get metrics for all containers of a service"""
        try:
            containers = self._get_service_containers(service_id)
            metrics = []

            for container in containers:
                try:
                    # Get container stats
                    stats = container.stats(stream=False)

                    # Calculate CPU percentage
                    cpu_usage = self._calculate_cpu_percent(stats)

                    # Calculate memory usage
                    memory_stats = stats.get('memory_stats', {})
                    memory_usage = memory_stats.get('usage', 0) / (1024 * 1024)  # MB
                    memory_limit = memory_stats.get('limit', 0) / (1024 * 1024)  # MB

                    # Calculate network stats
                    networks = stats.get('networks', {})
                    network_rx = sum(net.get('rx_bytes', 0) for net in networks.values()) / (1024 * 1024)  # MB
                    network_tx = sum(net.get('tx_bytes', 0) for net in networks.values()) / (1024 * 1024)  # MB

                    container_metrics = ContainerMetrics(
                        container_id=container.id,
                        name=container.name,
                        status=container.status,
                        cpu_percent=cpu_usage,
                        memory_usage_mb=memory_usage,
                        memory_limit_mb=memory_limit,
                        network_rx_mb=network_rx,
                        network_tx_mb=network_tx,
                        created_at=datetime.now()
                    )

                    metrics.append(container_metrics)

                except Exception as e:
                    self.logger.warning(f"Error getting metrics for container {container.name}: {e}")

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting container metrics for {service_id}: {e}")
            return []

    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})

            cpu_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            precpu_usage = precpu_stats.get('cpu_usage', {}).get('total_usage', 0)

            system_usage = cpu_stats.get('system_cpu_usage', 0)
            presystem_usage = precpu_stats.get('system_cpu_usage', 0)

            cpu_count = cpu_stats.get('online_cpus', 1)

            if system_usage > presystem_usage and cpu_usage > precpu_usage:
                cpu_delta = cpu_usage - precpu_usage
                system_delta = system_usage - presystem_usage
                return (cpu_delta / system_delta) * cpu_count * 100.0

            return 0.0

        except Exception:
            return 0.0

    async def get_service_logs(self, service_id: str, lines: int = 100) -> str:
        """Get logs for a service"""
        try:
            containers = self._get_service_containers(service_id)
            logs = []

            for container in containers:
                try:
                    container_logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
                    logs.append(f"=== Container: {container.name} ===\n{container_logs}")
                except Exception as e:
                    self.logger.warning(f"Error getting logs for container {container.name}: {e}")

            return '\n\n'.join(logs)

        except Exception as e:
            self.logger.error(f"Error getting service logs for {service_id}: {e}")
            return ""

    async def restart_service(self, service_id: str) -> bool:
        """Restart a service"""
        try:
            service_config = self.service_configs.get(service_id)
            if not service_config:
                self.logger.error(f"No service config found for: {service_id}")
                return False

            # Get current instance count
            current_instances = await self.get_instance_count(service_id)

            # Stop all containers
            containers = self._get_service_containers(service_id)
            for container in containers:
                try:
                    container.stop()
                    container.remove()
                except Exception as e:
                    self.logger.warning(f"Error stopping container {container.name}: {e}")

            # Start new containers
            success = await self._scale_service(service_id, current_instances)

            if success:
                self.logger.info(f"Restarted service: {service_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error restarting service {service_id}: {e}")
            return False

    async def get_system_info(self) -> Dict[str, Any]:
        """Get Docker system information"""
        try:
            info = self.docker_client.info()
            version = self.docker_client.version()

            return {
                'version': version.get('Version', 'Unknown'),
                'api_version': version.get('ApiVersion', 'Unknown'),
                'total_containers': info.get('Containers', 0),
                'running_containers': info.get('ContainersRunning', 0),
                'paused_containers': info.get('ContainersPaused', 0),
                'stopped_containers': info.get('ContainersStopped', 0),
                'total_images': info.get('Images', 0),
                'server_version': info.get('ServerVersion', 'Unknown'),
                'memory_total': info.get('MemTotal', 0),
                'cpu_count': info.get('NCPU', 0)
            }

        except Exception as e:
            self.logger.error(f"Error getting Docker system info: {e}")
            return {}

    async def _log_scaling_event(self, service_id: str, old_instances: int, new_instances: int, action: str):
        """Log scaling event"""
        try:
            event = {
                'service_id': service_id,
                'old_instances': old_instances,
                'new_instances': new_instances,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'controller': 'docker'
            }

            # This would typically be stored in a database or logging system
            self.logger.info(f"Scaling event: {event}")

        except Exception as e:
            self.logger.error(f"Error logging scaling event: {e}")

    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get detailed status of a service"""
        try:
            service_config = self.service_configs.get(service_id)
            if not service_config:
                return {'service_id': service_id, 'status': 'Not configured'}

            containers = self._get_service_containers(service_id)
            running_containers = [c for c in containers if c.status == 'running']

            status = {
                'service_id': service_id,
                'service_name': service_config['service_name'],
                'image': service_config['image'],
                'total_containers': len(containers),
                'running_containers': len(running_containers),
                'desired_containers': service_config.get('min_replicas', 1),
                'status': 'Running' if len(running_containers) > 0 else 'Stopped',
                'container_names': [c.name for c in containers],
                'container_statuses': {c.name: c.status for c in containers}
            }

            return status

        except Exception as e:
            self.logger.error(f"Error getting service status for {service_id}: {e}")
            return {'service_id': service_id, 'status': f'Error: {str(e)}'}