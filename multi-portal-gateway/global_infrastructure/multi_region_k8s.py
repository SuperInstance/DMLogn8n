#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure - Multi-Region Kubernetes Orchestration
Provides Kubernetes Federation management across global regions
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import yaml
from pathlib import Path

import aiohttp
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class ClusterStatus(Enum):
    """Kubernetes cluster status"""
    READY = "ready"
    NOT_READY = "not_ready"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"

class DeploymentStrategy(Enum):
    """Deployment strategies"""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    A_B_TESTING = "a_b_testing"

class ResourceType(Enum):
    """Kubernetes resource types"""
    DEPLOYMENT = "deployment"
    SERVICE = "service"
    INGRESS = "ingress"
    CONFIGMAP = "configmap"
    SECRET = "secret"
    STATEFULSET = "statefulset"
    DAEMONSET = "daemonset"

@dataclass
class K8sCluster:
    """Kubernetes cluster configuration"""
    name: str
    region: str
    provider: str
    endpoint: str
    kubeconfig_path: str
    status: ClusterStatus
    node_count: int
    max_pods: int
    current_pods: int
    cpu_capacity: int
    memory_capacity_gb: int
    storage_capacity_gb: int
    labels: Dict[str, str]
    taints: Dict[str, str]
    version: str
    created_at: float
    last_health_check: float

@dataclass
class FederatedResource:
    """Federated Kubernetes resource"""
    name: str
    namespace: str
    resource_type: ResourceType
    clusters: List[str]
    placement_policy: str
    replicas_per_cluster: Dict[str, int]
    resource_limits: Dict[str, Any]
    labels: Dict[str, str]
    annotations: Dict[str, str]

@dataclass
class DeploymentPlan:
    """Deployment plan for federated resources"""
    name: str
    resources: List[FederatedResource]
    strategy: DeploymentStrategy
    target_clusters: List[str]
    rollback_enabled: bool
    health_checks: Dict[str, str]
    rollout_duration: int
    traffic_splitting: Dict[str, float]

class MultiRegionK8sOrchestrator:
    """Multi-region Kubernetes orchestration system"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.clusters: Dict[str, K8sCluster] = {}
        self.federated_resources: Dict[str, FederatedResource] = {}
        self.cluster_clients: Dict[str, client.ApiClient] = {}
        self.deployment_plans: Dict[str, DeploymentPlan] = {}
        self.session = None

        # Load configuration if provided
        if config_path:
            self._load_configuration(config_path)
        else:
            self._initialize_default_clusters()

    def _initialize_default_clusters(self):
        """Initialize default Kubernetes clusters"""
        default_clusters = [
            K8sCluster(
                name="dmlogn8n-us-east",
                region="us-east-1",
                provider="aws",
                endpoint="https://EKS_US_EAST_ENDPOINT",
                kubeconfig_path="/path/to/us-east-kubeconfig",
                status=ClusterStatus.READY,
                node_count=5,
                max_pods=110,
                current_pods=45,
                cpu_capacity=20,
                memory_capacity_gb=80,
                storage_capacity_gb=1000,
                labels={"region": "us-east", "environment": "production"},
                taints={},
                version="1.28.0",
                created_at=time.time() - 86400 * 30,
                last_health_check=time.time()
            ),
            K8sCluster(
                name="dmlogn8n-eu-west",
                region="eu-west-1",
                provider="aws",
                endpoint="https://EKS_EU_WEST_ENDPOINT",
                kubeconfig_path="/path/to/eu-west-kubeconfig",
                status=ClusterStatus.READY,
                node_count=4,
                max_pods=88,
                current_pods=38,
                cpu_capacity=16,
                memory_capacity_gb=64,
                storage_capacity_gb=800,
                labels={"region": "eu-west", "environment": "production"},
                taints={},
                version="1.28.0",
                created_at=time.time() - 86400 * 25,
                last_health_check=time.time()
            ),
            K8sCluster(
                name="dmlogn8n-ap-southeast",
                region="ap-southeast-1",
                provider="aws",
                endpoint="https://EKS_AP_SOUTHEAST_ENDPOINT",
                kubeconfig_path="/path/to/ap-southeast-kubeconfig",
                status=ClusterStatus.READY,
                node_count=3,
                max_pods=66,
                current_pods=28,
                cpu_capacity=12,
                memory_capacity_gb=48,
                storage_capacity_gb=600,
                labels={"region": "ap-southeast", "environment": "production"},
                taints={},
                version="1.27.5",
                created_at=time.time() - 86400 * 20,
                last_health_check=time.time()
            )
        ]

        for cluster in default_clusters:
            self.clusters[cluster.name] = cluster

    async def initialize(self):
        """Initialize the orchestrator"""
        self.session = aiohttp.ClientSession()

        # Initialize Kubernetes clients for each cluster
        for cluster_name, cluster in self.clusters.items():
            try:
                await self._initialize_cluster_client(cluster)
            except Exception as e:
                self.logger.error(f"Failed to initialize client for cluster {cluster_name}: {e}")

        # Start health monitoring
        asyncio.create_task(self._health_monitoring_loop())

    async def _initialize_cluster_client(self, cluster: K8sCluster):
        """Initialize Kubernetes client for a cluster"""
        try:
            # Load kubeconfig for the cluster
            if Path(cluster.kubeconfig_path).exists():
                kubernetes.config.load_kube_config(config_file=cluster.kubeconfig_path)
            else:
                # Use in-cluster configuration if running in Kubernetes
                kubernetes.config.load_incluster_config()

            # Create API client
            api_client = kubernetes.client.ApiClient()
            self.cluster_clients[cluster.name] = api_client

            self.logger.info(f"Initialized Kubernetes client for cluster {cluster.name}")

        except Exception as e:
            self.logger.error(f"Error initializing cluster client for {cluster.name}: {e}")
            raise

    async def add_cluster(self, cluster: K8sCluster) -> bool:
        """Add a new cluster to the federation"""
        try:
            # Validate cluster connectivity
            if await self._validate_cluster_connectivity(cluster):
                self.clusters[cluster.name] = cluster
                await self._initialize_cluster_client(cluster)
                self.logger.info(f"Successfully added cluster {cluster.name}")
                return True
            else:
                self.logger.error(f"Failed to validate connectivity for cluster {cluster.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error adding cluster {cluster.name}: {e}")
            return False

    async def remove_cluster(self, cluster_name: str) -> bool:
        """Remove a cluster from the federation"""
        try:
            if cluster_name in self.clusters:
                # Drain resources from cluster before removal
                await self._drain_cluster(cluster_name)

                # Remove from federation
                del self.clusters[cluster_name]
                if cluster_name in self.cluster_clients:
                    del self.cluster_clients[cluster_name]

                self.logger.info(f"Successfully removed cluster {cluster_name}")
                return True
            else:
                self.logger.warning(f"Cluster {cluster_name} not found")
                return False

        except Exception as e:
            self.logger.error(f"Error removing cluster {cluster_name}: {e}")
            return False

    async def _validate_cluster_connectivity(self, cluster: K8sCluster) -> bool:
        """Validate connectivity to a Kubernetes cluster"""
        try:
            # Create temporary API client
            kubernetes.config.load_kube_config(config_file=cluster.kubeconfig_path)
            api_client = kubernetes.client.ApiClient()
            v1 = client.CoreV1Api(api_client)

            # Test connectivity by listing nodes
            nodes = v1.list_node()
            cluster.node_count = len(nodes.items)

            # Test API server connectivity
            version = v1.get_code()
            cluster.version = version.git_version

            api_client.close()
            return True

        except Exception as e:
            self.logger.error(f"Cluster connectivity validation failed for {cluster.name}: {e}")
            return False

    async def _drain_cluster(self, cluster_name: str):
        """Drain resources from a cluster"""
        try:
            if cluster_name not in self.cluster_clients:
                return

            api_client = self.cluster_clients[cluster_name]
            apps_v1 = client.AppsV1Api(api_client)

            # Scale down all deployments to 0
            deployments = apps_v1.list_deployment_for_all_namespaces()
            for deployment in deployments.items:
                if deployment.spec.replicas > 0:
                    # Scale down gradually
                    current_replicas = deployment.spec.replicas
                    while current_replicas > 0:
                        new_replicas = max(0, current_replicas // 2)
                        deployment.spec.replicas = new_replicas
                        apps_v1.patch_namespaced_deployment(
                            name=deployment.metadata.name,
                            namespace=deployment.metadata.namespace,
                            body=deployment
                        )
                        current_replicas = new_replicas
                        await asyncio.sleep(10)

            self.logger.info(f"Successfully drained cluster {cluster_name}")

        except Exception as e:
            self.logger.error(f"Error draining cluster {cluster_name}: {e}")

    async def create_federated_resource(self, resource: FederatedResource) -> bool:
        """Create a federated resource across multiple clusters"""
        try:
            self.federated_resources[f"{resource.namespace}/{resource.name}"] = resource

            # Deploy to target clusters
            deployment_tasks = []
            for cluster_name in resource.clusters:
                if cluster_name in self.cluster_clients:
                    deployment_tasks.append(
                        self._deploy_resource_to_cluster(cluster_name, resource)
                    )

            results = await asyncio.gather(*deployment_tasks, return_exceptions=True)

            success_count = sum(1 for r in results if not isinstance(r, Exception))
            if success_count == len(resource.clusters):
                self.logger.info(f"Successfully deployed federated resource {resource.name}")
                return True
            else:
                self.logger.warning(f"Partial deployment for {resource.name}: {success_count}/{len(resource.clusters)} clusters")
                return False

        except Exception as e:
            self.logger.error(f"Error creating federated resource {resource.name}: {e}")
            return False

    async def _deploy_resource_to_cluster(self, cluster_name: str,
                                        resource: FederatedResource) -> bool:
        """Deploy a resource to a specific cluster"""
        try:
            api_client = self.cluster_clients[cluster_name]

            if resource.resource_type == ResourceType.DEPLOYMENT:
                return await self._create_deployment(api_client, cluster_name, resource)
            elif resource.resource_type == ResourceType.SERVICE:
                return await self._create_service(api_client, cluster_name, resource)
            elif resource.resource_type == ResourceType.CONFIGMAP:
                return await self._create_configmap(api_client, cluster_name, resource)
            elif resource.resource_type == ResourceType.SECRET:
                return await self._create_secret(api_client, cluster_name, resource)

            return True

        except Exception as e:
            self.logger.error(f"Error deploying {resource.name} to cluster {cluster_name}: {e}")
            return False

    async def _create_deployment(self, api_client: client.ApiClient,
                               cluster_name: str, resource: FederatedResource) -> bool:
        """Create a deployment in a cluster"""
        try:
            apps_v1 = client.AppsV1Api(api_client)

            # Get replica count for this cluster
            replicas = resource.replicas_per_cluster.get(cluster_name, 1)

            # Create deployment manifest
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=resource.name,
                    namespace=resource.namespace,
                    labels=resource.labels,
                    annotations=resource.annotations
                ),
                spec=client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": resource.name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": resource.name, **resource.labels}
                        ),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=resource.name,
                                    image="nginx:latest",  # Default image
                                    ports=[client.V1ContainerPort(container_port=80)],
                                    resources=client.V1ResourceRequirements(
                                        requests=resource.resource_limits.get("requests", {}),
                                        limits=resource.resource_limits.get("limits", {})
                                    )
                                )
                            ]
                        )
                    )
                )
            )

            apps_v1.create_namespaced_deployment(
                namespace=resource.namespace,
                body=deployment
            )

            self.logger.info(f"Created deployment {resource.name} in cluster {cluster_name}")
            return True

        except ApiException as e:
            if e.status == 409:
                # Deployment already exists, update it
                return await self._update_deployment(api_client, cluster_name, resource)
            else:
                raise

    async def _update_deployment(self, api_client: client.ApiClient,
                               cluster_name: str, resource: FederatedResource) -> bool:
        """Update an existing deployment"""
        try:
            apps_v1 = client.AppsV1Api(api_client)
            replicas = resource.replicas_per_cluster.get(cluster_name, 1)

            # Get existing deployment
            existing = apps_v1.read_namespaced_deployment(
                name=resource.name,
                namespace=resource.namespace
            )

            # Update replica count
            existing.spec.replicas = replicas
            existing.metadata.labels.update(resource.labels)
            existing.metadata.annotations.update(resource.annotations)

            apps_v1.patch_namespaced_deployment(
                name=resource.name,
                namespace=resource.namespace,
                body=existing
            )

            self.logger.info(f"Updated deployment {resource.name} in cluster {cluster_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating deployment {resource.name} in cluster {cluster_name}: {e}")
            return False

    async def _create_service(self, api_client: client.ApiClient,
                            cluster_name: str, resource: FederatedResource) -> bool:
        """Create a service in a cluster"""
        try:
            v1 = client.CoreV1Api(api_client)

            service = client.V1Service(
                metadata=client.V1ObjectMeta(
                    name=resource.name,
                    namespace=resource.namespace,
                    labels=resource.labels,
                    annotations=resource.annotations
                ),
                spec=client.V1ServiceSpec(
                    selector={"app": resource.name},
                    ports=[client.V1ServicePort(
                        port=80,
                        target_port=80,
                        protocol="TCP"
                    )],
                    type="ClusterIP"
                )
            )

            v1.create_namespaced_service(
                namespace=resource.namespace,
                body=service
            )

            self.logger.info(f"Created service {resource.name} in cluster {cluster_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating service {resource.name} in cluster {cluster_name}: {e}")
            return False

    async def _create_configmap(self, api_client: client.ApiClient,
                              cluster_name: str, resource: FederatedResource) -> bool:
        """Create a configmap in a cluster"""
        try:
            v1 = client.CoreV1Api(api_client)

            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=resource.name,
                    namespace=resource.namespace,
                    labels=resource.labels,
                    annotations=resource.annotations
                ),
                data=resource.resource_limits.get("data", {})
            )

            v1.create_namespaced_config_map(
                namespace=resource.namespace,
                body=configmap
            )

            self.logger.info(f"Created configmap {resource.name} in cluster {cluster_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating configmap {resource.name} in cluster {cluster_name}: {e}")
            return False

    async def _create_secret(self, api_client: client.ApiClient,
                           cluster_name: str, resource: FederatedResource) -> bool:
        """Create a secret in a cluster"""
        try:
            v1 = client.CoreV1Api(api_client)

            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=resource.name,
                    namespace=resource.namespace,
                    labels=resource.labels,
                    annotations=resource.annotations
                ),
                data=resource.resource_limits.get("data", {}),
                type="Opaque"
            )

            v1.create_namespaced_secret(
                namespace=resource.namespace,
                body=secret
            )

            self.logger.info(f"Created secret {resource.name} in cluster {cluster_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating secret {resource.name} in cluster {cluster_name}: {e}")
            return False

    async def execute_deployment_plan(self, plan: DeploymentPlan) -> bool:
        """Execute a deployment plan with specific strategy"""
        try:
            self.deployment_plans[plan.name] = plan

            if plan.strategy == DeploymentStrategy.ROLLING:
                return await self._execute_rolling_deployment(plan)
            elif plan.strategy == DeploymentStrategy.BLUE_GREEN:
                return await self._execute_blue_green_deployment(plan)
            elif plan.strategy == DeploymentStrategy.CANARY:
                return await self._execute_canary_deployment(plan)
            elif plan.strategy == DeploymentStrategy.A_B_TESTING:
                return await self._execute_ab_testing_deployment(plan)

            return False

        except Exception as e:
            self.logger.error(f"Error executing deployment plan {plan.name}: {e}")
            return False

    async def _execute_rolling_deployment(self, plan: DeploymentPlan) -> bool:
        """Execute rolling deployment strategy"""
        try:
            # Deploy resources to all clusters gradually
            for resource in plan.resources:
                # Deploy to first cluster
                first_cluster = resource.clusters[0]
                if await self._deploy_resource_to_cluster(first_cluster, resource):
                    self.logger.info(f"Deployed {resource.name} to {first_cluster}")

                    # Wait for health check
                    await asyncio.sleep(plan.health_checks.get(resource.name, 30))

                    # Deploy to remaining clusters
                    for cluster in resource.clusters[1:]:
                        await self._deploy_resource_to_cluster(cluster, resource)
                        self.logger.info(f"Deployed {resource.name} to {cluster}")

            self.logger.info(f"Rolling deployment {plan.name} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in rolling deployment {plan.name}: {e}")
            if plan.rollback_enabled:
                await self._rollback_deployment(plan)
            return False

    async def _execute_blue_green_deployment(self, plan: DeploymentPlan) -> bool:
        """Execute blue-green deployment strategy"""
        try:
            # Create green environment
            green_resources = []
            for resource in plan.resources:
                green_resource = FederatedResource(
                    name=f"{resource.name}-green",
                    namespace=resource.namespace,
                    resource_type=resource.resource_type,
                    clusters=resource.clusters,
                    placement_policy=resource.placement_policy,
                    replicas_per_cluster=resource.replicas_per_cluster,
                    resource_limits=resource.resource_limits,
                    labels={**resource.labels, "version": "green"},
                    annotations=resource.annotations
                )
                green_resources.append(green_resource)

            # Deploy green environment
            for resource in green_resources:
                await self.create_federated_resource(resource)

            # Wait for green to be healthy
            await asyncio.sleep(plan.rollout_duration)

            # Switch traffic to green (simplified - would involve DNS/ingress updates)
            self.logger.info(f"Switching traffic to green environment for {plan.name}")

            # Clean up blue environment
            for resource in plan.resources:
                await self.delete_federated_resource(f"{resource.namespace}/{resource.name}")

            self.logger.info(f"Blue-green deployment {plan.name} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in blue-green deployment {plan.name}: {e}")
            if plan.rollback_enabled:
                await self._rollback_deployment(plan)
            return False

    async def _execute_canary_deployment(self, plan: DeploymentPlan) -> bool:
        """Execute canary deployment strategy"""
        try:
            # Start with small percentage of traffic to new version
            canary_percentage = 0.1

            while canary_percentage <= 1.0:
                # Deploy canary with current percentage
                for resource in plan.resources:
                    canary_resource = FederatedResource(
                        name=f"{resource.name}-canary",
                        namespace=resource.namespace,
                        resource_type=resource.resource_type,
                        clusters=resource.clusters[:1],  # Start with one cluster
                        placement_policy=resource.placement_policy,
                        replicas_per_cluster={c: int(r * canary_percentage)
                                            for c, r in resource.replicas_per_cluster.items()},
                        resource_limits=resource.resource_limits,
                        labels={**resource.labels, "version": "canary"},
                        annotations=resource.annotations
                    )
                    await self.create_federated_resource(canary_resource)

                # Wait and monitor
                await asyncio.sleep(plan.rollout_duration // 4)

                # Gradually increase canary percentage
                canary_percentage = min(1.0, canary_percentage + 0.2)

            # Replace old version
            for resource in plan.resources:
                await self.delete_federated_resource(f"{resource.namespace}/{resource.name}")
                # Rename canary to final version
                await self._rename_federated_resource(
                    f"{resource.namespace}/{resource.name}-canary",
                    resource.name
                )

            self.logger.info(f"Canary deployment {plan.name} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in canary deployment {plan.name}: {e}")
            if plan.rollback_enabled:
                await self._rollback_deployment(plan)
            return False

    async def _execute_ab_testing_deployment(self, plan: DeploymentPlan) -> bool:
        """Execute A/B testing deployment strategy"""
        try:
            # Deploy both versions A and B
            for resource in plan.resources:
                # Version A
                resource_a = FederatedResource(
                    name=f"{resource.name}-a",
                    namespace=resource.namespace,
                    resource_type=resource.resource_type,
                    clusters=resource.clusters[:len(resource.clusters)//2],
                    placement_policy=resource.placement_policy,
                    replicas_per_cluster=resource.replicas_per_cluster,
                    resource_limits=resource.resource_limits,
                    labels={**resource.labels, "version": "a"},
                    annotations=resource.annotations
                )

                # Version B
                resource_b = FederatedResource(
                    name=f"{resource.name}-b",
                    namespace=resource.namespace,
                    resource_type=resource.resource_type,
                    clusters=resource.clusters[len(resource.clusters)//2:],
                    placement_policy=resource.placement_policy,
                    replicas_per_cluster=resource.replicas_per_cluster,
                    resource_limits=resource.resource_limits,
                    labels={**resource.labels, "version": "b"},
                    annotations=resource.annotations
                )

                await self.create_federated_resource(resource_a)
                await self.create_federated_resource(resource_b)

            # Route traffic according to plan's traffic splitting
            self.logger.info(f"A/B testing deployment {plan.name} with traffic splitting: {plan.traffic_splitting}")

            self.logger.info(f"A/B testing deployment {plan.name} completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in A/B testing deployment {plan.name}: {e}")
            if plan.rollback_enabled:
                await self._rollback_deployment(plan)
            return False

    async def _rollback_deployment(self, plan: DeploymentPlan):
        """Rollback a failed deployment"""
        try:
            self.logger.info(f"Rolling back deployment plan {plan.name}")

            # Delete all resources created by the plan
            for resource in plan.resources:
                await self.delete_federated_resource(f"{resource.namespace}/{resource.name}")

            self.logger.info(f"Rollback of deployment plan {plan.name} completed")

        except Exception as e:
            self.logger.error(f"Error during rollback of {plan.name}: {e}")

    async def delete_federated_resource(self, resource_key: str) -> bool:
        """Delete a federated resource from all clusters"""
        try:
            if resource_key not in self.federated_resources:
                return False

            resource = self.federated_resources[resource_key]

            # Delete from all clusters
            deletion_tasks = []
            for cluster_name in resource.clusters:
                if cluster_name in self.cluster_clients:
                    deletion_tasks.append(
                        self._delete_resource_from_cluster(cluster_name, resource)
                    )

            await asyncio.gather(*deletion_tasks, return_exceptions=True)

            # Remove from federated resources
            del self.federated_resources[resource_key]

            self.logger.info(f"Deleted federated resource {resource_key}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting federated resource {resource_key}: {e}")
            return False

    async def _delete_resource_from_cluster(self, cluster_name: str,
                                          resource: FederatedResource) -> bool:
        """Delete a resource from a specific cluster"""
        try:
            api_client = self.cluster_clients[cluster_name]

            if resource.resource_type == ResourceType.DEPLOYMENT:
                apps_v1 = client.AppsV1Api(api_client)
                apps_v1.delete_namespaced_deployment(
                    name=resource.name,
                    namespace=resource.namespace
                )
            elif resource.resource_type == ResourceType.SERVICE:
                v1 = client.CoreV1Api(api_client)
                v1.delete_namespaced_service(
                    name=resource.name,
                    namespace=resource.namespace
                )
            elif resource.resource_type == ResourceType.CONFIGMAP:
                v1 = client.CoreV1Api(api_client)
                v1.delete_namespaced_config_map(
                    name=resource.name,
                    namespace=resource.namespace
                )
            elif resource.resource_type == ResourceType.SECRET:
                v1 = client.CoreV1Api(api_client)
                v1.delete_namespaced_secret(
                    name=resource.name,
                    namespace=resource.namespace
                )

            self.logger.info(f"Deleted {resource.name} from cluster {cluster_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting {resource.name} from cluster {cluster_name}: {e}")
            return False

    async def _rename_federated_resource(self, old_key: str, new_name: str):
        """Rename a federated resource"""
        try:
            if old_key not in self.federated_resources:
                return

            old_resource = self.federated_resources[old_key]
            new_resource = FederatedResource(
                name=new_name,
                namespace=old_resource.namespace,
                resource_type=old_resource.resource_type,
                clusters=old_resource.clusters,
                placement_policy=old_resource.placement_policy,
                replicas_per_cluster=old_resource.replicas_per_cluster,
                resource_limits=old_resource.resource_limits,
                labels=old_resource.labels,
                annotations=old_resource.annotations
            )

            # Delete old resource and create new one
            await self.delete_federated_resource(old_key)
            await self.create_federated_resource(new_resource)

        except Exception as e:
            self.logger.error(f"Error renaming federated resource {old_key}: {e}")

    async def _health_monitoring_loop(self):
        """Continuous health monitoring of all clusters"""
        while True:
            try:
                health_tasks = []
                for cluster_name, cluster in self.clusters.items():
                    health_tasks.append(self._check_cluster_health(cluster_name))

                await asyncio.gather(*health_tasks, return_exceptions=True)
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _check_cluster_health(self, cluster_name: str) -> bool:
        """Check health of a specific cluster"""
        try:
            if cluster_name not in self.cluster_clients:
                self.clusters[cluster_name].status = ClusterStatus.FAILED
                return False

            api_client = self.cluster_clients[cluster_name]
            v1 = client.CoreV1Api(api_client)

            # Check API server connectivity
            v1.get_api_resources()

            # Check node status
            nodes = v1.list_node()
            ready_nodes = sum(1 for node in nodes.items
                            if any(condition.type == "Ready" and condition.status == "True"
                                 for condition in node.status.conditions))

            total_nodes = len(nodes.items)
            if ready_nodes == total_nodes and total_nodes > 0:
                self.clusters[cluster_name].status = ClusterStatus.READY
            elif ready_nodes > total_nodes // 2:
                self.clusters[cluster_name].status = ClusterStatus.DEGRADED
            else:
                self.clusters[cluster_name].status = ClusterStatus.NOT_READY

            self.clusters[cluster_name].last_health_check = time.time()
            self.clusters[cluster_name].node_count = total_nodes

            return self.clusters[cluster_name].status == ClusterStatus.READY

        except Exception as e:
            self.logger.error(f"Health check failed for cluster {cluster_name}: {e}")
            self.clusters[cluster_name].status = ClusterStatus.FAILED
            return False

    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Get metrics for all clusters"""
        metrics = {
            'total_clusters': len(self.clusters),
            'ready_clusters': sum(1 for c in self.clusters.values() if c.status == ClusterStatus.READY),
            'degraded_clusters': sum(1 for c in self.clusters.values() if c.status == ClusterStatus.DEGRADED),
            'failed_clusters': sum(1 for c in self.clusters.values() if c.status == ClusterStatus.FAILED),
            'total_nodes': sum(c.node_count for c in self.clusters.values()),
            'total_cpu_capacity': sum(c.cpu_capacity for c in self.clusters.values()),
            'total_memory_capacity_gb': sum(c.memory_capacity_gb for c in self.clusters.values()),
            'clusters': {}
        }

        for cluster_name, cluster in self.clusters.items():
            metrics['clusters'][cluster_name] = {
                'region': cluster.region,
                'provider': cluster.provider,
                'status': cluster.status.value,
                'nodes': cluster.node_count,
                'cpu_capacity': cluster.cpu_capacity,
                'memory_capacity_gb': cluster.memory_capacity_gb,
                'current_pods': cluster.current_pods,
                'max_pods': cluster.max_pods,
                'version': cluster.version,
                'last_health_check': cluster.last_health_check
            }

        return metrics

    def get_federated_resources_status(self) -> Dict[str, Any]:
        """Get status of all federated resources"""
        status = {
            'total_resources': len(self.federated_resources),
            'resources': {}
        }

        for resource_key, resource in self.federated_resources.items():
            status['resources'][resource_key] = {
                'name': resource.name,
                'namespace': resource.namespace,
                'type': resource.resource_type.value,
                'clusters': resource.clusters,
                'placement_policy': resource.placement_policy,
                'replicas_per_cluster': resource.replicas_per_cluster
            }

        return status

    def _load_configuration(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Load clusters
            if 'clusters' in config:
                for cluster_config in config['clusters']:
                    cluster = K8sCluster(**cluster_config)
                    self.clusters[cluster.name] = cluster

            # Load federated resources
            if 'federated_resources' in config:
                for resource_config in config['federated_resources']:
                    resource_config['resource_type'] = ResourceType(resource_config['resource_type'])
                    resource = FederatedResource(**resource_config)
                    self.federated_resources[f"{resource.namespace}/{resource.name}"] = resource

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

    def save_configuration(self, config_path: str):
        """Save current configuration to file"""
        config = {
            'clusters': [asdict(cluster) for cluster in self.clusters.values()],
            'federated_resources': [
                {**asdict(resource), 'resource_type': resource.resource_type.value}
                for resource in self.federated_resources.values()
            ]
        }

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

        # Close Kubernetes clients
        for api_client in self.cluster_clients.values():
            api_client.close()


async def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)

    orchestrator = MultiRegionK8sOrchestrator()
    await orchestrator.initialize()

    # Create a sample federated deployment
    sample_resource = FederatedResource(
        name="dmlogn8n-web",
        namespace="default",
        resource_type=ResourceType.DEPLOYMENT,
        clusters=["dmlogn8n-us-east", "dmlogn8n-eu-west"],
        placement_policy="spread",
        replicas_per_cluster={"dmlogn8n-us-east": 3, "dmlogn8n-eu-west": 2},
        resource_limits={
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"}
        },
        labels={"app": "dmlogn8n-web", "tier": "frontend"},
        annotations={"deployment.kubernetes.io/revision": "1"}
    )

    print("Creating federated resource...")
    success = await orchestrator.create_federated_resource(sample_resource)
    print(f"Federated resource creation: {'Success' if success else 'Failed'}")

    # Get metrics
    metrics = orchestrator.get_cluster_metrics()
    print(f"\nCluster Metrics:")
    print(f"  Total Clusters: {metrics['total_clusters']}")
    print(f"  Ready Clusters: {metrics['ready_clusters']}")
    print(f"  Total Nodes: {metrics['total_nodes']}")
    print(f"  Total CPU Capacity: {metrics['total_cpu_capacity']} cores")
    print(f"  Total Memory: {metrics['total_memory_capacity_gb']} GB")

    await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())