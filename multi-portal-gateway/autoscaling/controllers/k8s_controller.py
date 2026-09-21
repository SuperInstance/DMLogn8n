#!/usr/bin/env python3
"""
Kubernetes Scaling Controller for DMLogn8n Auto-Scaling
Manages scaling of Kubernetes deployments and resources
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

try:
    from kubernetes import client, config, watch
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False
    print("Kubernetes client not available. Install with: pip install kubernetes")

@dataclass
class KubernetesResource:
    name: str
    namespace: str
    kind: str  # Deployment, StatefulSet, DaemonSet
    replicas: int
    ready_replicas: int
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    labels: Dict[str, str]
    annotations: Dict[str, str]

@dataclass
class HPAConfig:
    name: str
    target_resource: str
    min_replicas: int
    max_replicas: int
    target_cpu_utilization: Optional[int]
    target_memory_utilization: Optional[int]
    metrics: List[Dict[str, Any]]

class KubernetesController:
    """
    Controller for managing Kubernetes-based scaling
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('k8s_controller')

        if not KUBERNETES_AVAILABLE:
            self.logger.error("Kubernetes client not available")
            raise ImportError("Kubernetes client not available")

        # Initialize Kubernetes clients
        self._initialize_kubernetes_clients()

        # Configuration
        self.namespace = config.get('namespace', 'dmlogn8n')
        self.default_labels = config.get('default_labels', {'app': 'dmlogn8n'})
        self.scaling_timeout = config.get('scaling_timeout', 300)  # 5 minutes

        # Resource configurations
        self.resource_configs = self._load_resource_configs()

        # HPA configurations
        self.hpa_configs = self._load_hpa_configs()

    def _initialize_kubernetes_clients(self):
        """Initialize Kubernetes API clients"""
        try:
            # Try to load in-cluster config first
            try:
                config.load_incluster_config()
                self.logger.info("Loaded in-cluster Kubernetes config")
            except config.ConfigException:
                # Fall back to kubeconfig
                config.load_kube_config()
                self.logger.info("Loaded kubeconfig Kubernetes config")

            # Initialize API clients
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v1 = client.AutoscalingV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()
            self.custom_api = client.CustomObjectsApi()

            self.logger.info("Kubernetes clients initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes clients: {e}")
            raise

    def _load_resource_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load Kubernetes resource configurations"""
        try:
            configs = {
                'api-gateway': {
                    'deployment': 'api-gateway',
                    'namespace': self.namespace,
                    'min_replicas': 2,
                    'max_replicas': 10,
                    'cpu_request': '500m',
                    'cpu_limit': '1000m',
                    'memory_request': '512Mi',
                    'memory_limit': '1Gi'
                },
                'character-portal': {
                    'deployment': 'character-portal',
                    'namespace': self.namespace,
                    'min_replicas': 3,
                    'max_replicas': 15,
                    'cpu_request': '500m',
                    'cpu_limit': '1000m',
                    'memory_request': '1Gi',
                    'memory_limit': '2Gi'
                },
                'dialogue-system': {
                    'deployment': 'dialogue-system',
                    'namespace': self.namespace,
                    'min_replicas': 2,
                    'max_replicas': 8,
                    'cpu_request': '1000m',
                    'cpu_limit': '2000m',
                    'memory_request': '2Gi',
                    'memory_limit': '4Gi'
                },
                'combat-engine': {
                    'deployment': 'combat-engine',
                    'namespace': self.namespace,
                    'min_replicas': 1,
                    'max_replicas': 6,
                    'cpu_request': '1000m',
                    'cpu_limit': '2000m',
                    'memory_request': '1Gi',
                    'memory_limit': '2Gi'
                },
                'world-simulation': {
                    'statefulset': 'world-simulation',
                    'namespace': self.namespace,
                    'min_replicas': 1,
                    'max_replicas': 5,
                    'cpu_request': '2000m',
                    'cpu_limit': '4000m',
                    'memory_request': '4Gi',
                    'memory_limit': '8Gi'
                }
            }

            return configs

        except Exception as e:
            self.logger.error(f"Error loading resource configs: {e}")
            return {}

    def _load_hpa_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load HPA configurations"""
        try:
            configs = {
                'api-gateway': {
                    'name': 'api-gateway-hpa',
                    'target': 'api-gateway',
                    'min_replicas': 2,
                    'max_replicas': 10,
                    'metrics': [
                        {
                            'type': 'Resource',
                            'resource': {
                                'name': 'cpu',
                                'target': {
                                    'type': 'Utilization',
                                    'averageUtilization': 70
                                }
                            }
                        },
                        {
                            'type': 'Resource',
                            'resource': {
                                'name': 'memory',
                                'target': {
                                    'type': 'Utilization',
                                    'averageUtilization': 80
                                }
                            }
                        }
                    ]
                },
                'character-portal': {
                    'name': 'character-portal-hpa',
                    'target': 'character-portal',
                    'min_replicas': 3,
                    'max_replicas': 15,
                    'metrics': [
                        {
                            'type': 'Resource',
                            'resource': {
                                'name': 'cpu',
                                'target': {
                                    'type': 'Utilization',
                                    'averageUtilization': 60
                                }
                            }
                        }
                    ]
                }
            }

            return configs

        except Exception as e:
            self.logger.error(f"Error loading HPA configs: {e}")
            return {}

    async def get_instance_count(self, service_id: str) -> int:
        """Get current instance count for a service"""
        try:
            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                self.logger.error(f"No resource config found for service: {service_id}")
                return 0

            namespace = resource_config['namespace']

            # Check if it's a Deployment
            if 'deployment' in resource_config:
                deployment_name = resource_config['deployment']
                try:
                    deployment = self.apps_v1.read_namespaced_deployment(
                        name=deployment_name,
                        namespace=namespace
                    )
                    return deployment.spec.replicas or 0
                except ApiException as e:
                    self.logger.error(f"Error reading deployment {deployment_name}: {e}")
                    return 0

            # Check if it's a StatefulSet
            elif 'statefulset' in resource_config:
                statefulset_name = resource_config['statefulset']
                try:
                    statefulset = self.apps_v1.read_namespaced_stateful_set(
                        name=statefulset_name,
                        namespace=namespace
                    )
                    return statefulset.spec.replicas or 0
                except ApiException as e:
                    self.logger.error(f"Error reading statefulset {statefulset_name}: {e}")
                    return 0

            else:
                self.logger.error(f"Unknown resource type for service: {service_id}")
                return 0

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

            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                self.logger.error(f"No resource config found for service: {service_id}")
                return False

            # Check against max replicas
            max_replicas = resource_config.get('max_replicas', 10)
            if desired_instances > max_replicas:
                desired_instances = max_replicas
                self.logger.warning(f"Limited scaling to max replicas: {max_replicas}")

            success = await self._scale_resource(service_id, desired_instances)
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

            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                self.logger.error(f"No resource config found for service: {service_id}")
                return False

            # Check against min replicas
            min_replicas = resource_config.get('min_replicas', 1)
            if desired_instances < min_replicas:
                desired_instances = min_replicas
                self.logger.warning(f"Limited scaling to min replicas: {min_replicas}")

            success = await self._scale_resource(service_id, desired_instances)
            if success:
                self.logger.info(f"Scaled down {service_id} to {desired_instances} instances")
                await self._log_scaling_event(service_id, current_instances, desired_instances, 'scale_down')

            return success

        except Exception as e:
            self.logger.error(f"Error scaling down {service_id}: {e}")
            return False

    async def _scale_resource(self, service_id: str, replicas: int) -> bool:
        """Perform the actual scaling operation"""
        try:
            resource_config = self.resource_configs.get(service_id)
            namespace = resource_config['namespace']

            # Scale Deployment
            if 'deployment' in resource_config:
                deployment_name = resource_config['deployment']

                # Get current deployment
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )

                # Update replicas
                deployment.spec.replicas = replicas

                # Apply the update
                self.apps_v1.patch_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace,
                    body=deployment
                )

                # Wait for scaling to complete
                return await self._wait_for_deployment_scaling(deployment_name, namespace, replicas)

            # Scale StatefulSet
            elif 'statefulset' in resource_config:
                statefulset_name = resource_config['statefulset']

                # Get current statefulset
                statefulset = self.apps_v1.read_namespaced_stateful_set(
                    name=statefulset_name,
                    namespace=namespace
                )

                # Update replicas
                statefulset.spec.replicas = replicas

                # Apply the update
                self.apps_v1.patch_namespaced_stateful_set(
                    name=statefulset_name,
                    namespace=namespace,
                    body=statefulset
                )

                # Wait for scaling to complete
                return await self._wait_for_statefulset_scaling(statefulset_name, namespace, replicas)

            else:
                self.logger.error(f"Unknown resource type for service: {service_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error scaling resource {service_id}: {e}")
            return False

    async def _wait_for_deployment_scaling(self, deployment_name: str, namespace: str, desired_replicas: int, timeout: int = 300) -> bool:
        """Wait for deployment scaling to complete"""
        try:
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )

                ready_replicas = deployment.status.ready_replicas or 0
                if ready_replicas >= desired_replicas:
                    self.logger.info(f"Deployment {deployment_name} scaled successfully to {desired_replicas} replicas")
                    return True

                await asyncio.sleep(5)

            self.logger.error(f"Timeout waiting for deployment {deployment_name} to scale")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for deployment scaling: {e}")
            return False

    async def _wait_for_statefulset_scaling(self, statefulset_name: str, namespace: str, desired_replicas: int, timeout: int = 300) -> bool:
        """Wait for StatefulSet scaling to complete"""
        try:
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                statefulset = self.apps_v1.read_namespaced_stateful_set(
                    name=statefulset_name,
                    namespace=namespace
                )

                ready_replicas = statefulset.status.ready_replicas or 0
                if ready_replicas >= desired_replicas:
                    self.logger.info(f"StatefulSet {statefulset_name} scaled successfully to {desired_replicas} replicas")
                    return True

                await asyncio.sleep(5)

            self.logger.error(f"Timeout waiting for StatefulSet {statefulset_name} to scale")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for StatefulSet scaling: {e}")
            return False

    async def get_resource_metrics(self, service_id: str) -> Dict[str, Any]:
        """Get resource metrics for a service"""
        try:
            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                return {}

            namespace = resource_config['namespace']

            # Get pods for the service
            pods = await self._get_service_pods(service_id, namespace)

            if not pods:
                return {}

            # Calculate metrics
            total_cpu = 0
            total_memory = 0
            ready_count = 0

            for pod in pods:
                if pod.status.phase == 'Running':
                    ready_count += 1

                    # Get CPU and memory usage from metrics API
                    try:
                        # This would typically use the metrics server
                        # For now, return mock data
                        cpu_usage = 100  # millicores
                        memory_usage = 256 * 1024 * 1024  # bytes
                        total_cpu += cpu_usage
                        total_memory += memory_usage
                    except Exception:
                        pass

            return {
                'total_replicas': len(pods),
                'ready_replicas': ready_count,
                'cpu_usage_millicores': total_cpu,
                'memory_usage_bytes': total_memory,
                'average_cpu_per_pod': total_cpu / len(pods) if pods else 0,
                'average_memory_per_pod': total_memory / len(pods) if pods else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting resource metrics for {service_id}: {e}")
            return {}

    async def _get_service_pods(self, service_id: str, namespace: str) -> List[Any]:
        """Get pods for a service"""
        try:
            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                return []

            # Build label selector
            labels = self.default_labels.copy()
            labels['service'] = service_id

            label_selector = ','.join([f"{k}={v}" for k, v in labels.items()])

            # Get pods
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )

            return pods.items

        except Exception as e:
            self.logger.error(f"Error getting pods for {service_id}: {e}")
            return []

    async def create_hpa(self, service_id: str, hpa_config: Dict[str, Any]) -> bool:
        """Create Horizontal Pod Autoscaler"""
        try:
            if service_id not in self.hpa_configs:
                self.logger.error(f"No HPA config found for service: {service_id}")
                return False

            config = self.hpa_configs[service_id]
            namespace = self.resource_configs[service_id]['namespace']

            # Create HPA manifest
            hpa_manifest = {
                'apiVersion': 'autoscaling/v2',
                'kind': 'HorizontalPodAutoscaler',
                'metadata': {
                    'name': config['name'],
                    'namespace': namespace,
                    'labels': self.default_labels
                },
                'spec': {
                    'scaleTargetRef': {
                        'apiVersion': 'apps/v1',
                        'kind': 'Deployment',
                        'name': config['target']
                    },
                    'minReplicas': config['min_replicas'],
                    'maxReplicas': config['max_replicas'],
                    'metrics': config['metrics']
                }
            }

            # Apply HPA
            try:
                self.autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                    namespace=namespace,
                    body=hpa_manifest
                )
                self.logger.info(f"Created HPA for service: {service_id}")
                return True

            except ApiException as e:
                if e.status == 409:
                    # HPA already exists, update it
                    self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(
                        name=config['name'],
                        namespace=namespace,
                        body=hpa_manifest
                    )
                    self.logger.info(f"Updated HPA for service: {service_id}")
                    return True
                else:
                    raise

        except Exception as e:
            self.logger.error(f"Error creating HPA for {service_id}: {e}")
            return False

    async def update_hpa(self, service_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing HPA"""
        try:
            if service_id not in self.hpa_configs:
                self.logger.error(f"No HPA config found for service: {service_id}")
                return False

            config = self.hpa_configs[service_id]
            namespace = self.resource_configs[service_id]['namespace']

            # Get current HPA
            hpa = self.autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(
                name=config['name'],
                namespace=namespace
            )

            # Update configuration
            if 'min_replicas' in updates:
                hpa.spec.min_replicas = updates['min_replicas']
            if 'max_replicas' in updates:
                hpa.spec.max_replicas = updates['max_replicas']
            if 'metrics' in updates:
                hpa.spec.metrics = updates['metrics']

            # Apply update
            self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(
                name=config['name'],
                namespace=namespace,
                body=hpa
            )

            self.logger.info(f"Updated HPA for service: {service_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating HPA for {service_id}: {e}")
            return False

    async def delete_hpa(self, service_id: str) -> bool:
        """Delete HPA for a service"""
        try:
            if service_id not in self.hpa_configs:
                self.logger.error(f"No HPA config found for service: {service_id}")
                return False

            config = self.hpa_configs[service_id]
            namespace = self.resource_configs[service_id]['namespace']

            self.autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=config['name'],
                namespace=namespace
            )

            self.logger.info(f"Deleted HPA for service: {service_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting HPA for {service_id}: {e}")
            return False

    async def get_cluster_resources(self) -> Dict[str, Any]:
        """Get overall cluster resource information"""
        try:
            # Get nodes
            nodes = self.core_v1.list_node()

            total_cpu = 0
            total_memory = 0
            allocatable_cpu = 0
            allocatable_memory = 0

            for node in nodes.items:
                if node.status.allocatable:
                    cpu_str = node.status.allocatable.get('cpu', '0')
                    memory_str = node.status.allocatable.get('memory', '0Ki')

                    # Parse CPU (convert millicores to cores)
                    if cpu_str.endswith('m'):
                        cpu_cores = int(cpu_str[:-1]) / 1000
                    else:
                        cpu_cores = float(cpu_str)
                    total_cpu += cpu_cores
                    allocatable_cpu += cpu_cores

                    # Parse memory
                    if memory_str.endswith('Ki'):
                        memory_bytes = int(memory_str[:-2]) * 1024
                    elif memory_str.endswith('Mi'):
                        memory_bytes = int(memory_str[:-2]) * 1024 * 1024
                    elif memory_str.endswith('Gi'):
                        memory_bytes = int(memory_str[:-2]) * 1024 * 1024 * 1024
                    else:
                        memory_bytes = int(memory_str)
                    total_memory += memory_bytes
                    allocatable_memory += memory_bytes

            return {
                'total_nodes': len(nodes.items),
                'total_cpu_cores': total_cpu,
                'total_memory_bytes': total_memory,
                'allocatable_cpu_cores': allocatable_cpu,
                'allocatable_memory_bytes': allocatable_memory
            }

        except Exception as e:
            self.logger.error(f"Error getting cluster resources: {e}")
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
                'controller': 'kubernetes'
            }

            # This would typically be stored in a database or logging system
            self.logger.info(f"Scaling event: {event}")

        except Exception as e:
            self.logger.error(f"Error logging scaling event: {e}")

    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get detailed status of a service"""
        try:
            resource_config = self.resource_configs.get(service_id)
            if not resource_config:
                return {}

            namespace = resource_config['namespace']
            status = {
                'service_id': service_id,
                'namespace': namespace,
                'resource_type': None,
                'resource_name': None,
                'desired_replicas': 0,
                'current_replicas': 0,
                'ready_replicas': 0,
                'status': 'Unknown'
            }

            # Check Deployment
            if 'deployment' in resource_config:
                deployment_name = resource_config['deployment']
                try:
                    deployment = self.apps_v1.read_namespaced_deployment(
                        name=deployment_name,
                        namespace=namespace
                    )
                    status.update({
                        'resource_type': 'Deployment',
                        'resource_name': deployment_name,
                        'desired_replicas': deployment.spec.replicas or 0,
                        'current_replicas': deployment.status.replicas or 0,
                        'ready_replicas': deployment.status.ready_replicas or 0,
                        'status': 'Ready' if (deployment.status.ready_replicas or 0) >= (deployment.spec.replicas or 0) else 'NotReady'
                    })
                except ApiException as e:
                    status['status'] = f'Error: {e.reason}'

            # Check StatefulSet
            elif 'statefulset' in resource_config:
                statefulset_name = resource_config['statefulset']
                try:
                    statefulset = self.apps_v1.read_namespaced_stateful_set(
                        name=statefulset_name,
                        namespace=namespace
                    )
                    status.update({
                        'resource_type': 'StatefulSet',
                        'resource_name': statefulset_name,
                        'desired_replicas': statefulset.spec.replicas or 0,
                        'current_replicas': statefulset.status.replicas or 0,
                        'ready_replicas': statefulset.status.ready_replicas or 0,
                        'status': 'Ready' if (statefulset.status.ready_replicas or 0) >= (statefulset.spec.replicas or 0) else 'NotReady'
                    })
                except ApiException as e:
                    status['status'] = f'Error: {e.reason}'

            return status

        except Exception as e:
            self.logger.error(f"Error getting service status for {service_id}: {e}")
            return {'service_id': service_id, 'status': f'Error: {str(e)}'}