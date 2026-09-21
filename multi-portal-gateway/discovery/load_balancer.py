#!/usr/bin/env python3
"""
Load Balancer for DMLogn8n Multi-Agent Platform

This module provides comprehensive load balancing capabilities including:
- Multiple load balancing algorithms
- Health-aware service selection
- Circuit breaker pattern
- Request routing and distribution
- Performance metrics collection
- Adaptive load balancing
"""

import asyncio
import json
import logging
import random
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import consul.aio
import aiohttp
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"
    HEALTH_AWARE = "health_aware"
    ADAPTIVE = "adaptive"

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class ServiceInstance:
    """Service instance for load balancing"""
    service_id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    response_times: List[float] = field(default_factory=list)
    success_rate: float = 1.0
    failure_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    health_status: str = "passing"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: LoadBalancingAlgorithm
    service_name: str
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    max_response_time_ms: float = 5000
    enable_sticky_sessions: bool = False
    session_cookie_name: str = "lb_session"
    adaptive_learning_rate: float = 0.1
    metrics_retention_hours: int = 24

@dataclass
class CircuitBreaker:
    """Circuit breaker for service instance"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime = field(default_factory=datetime.now)
    success_count: int = 0
    next_attempt_time: datetime = field(default_factory=datetime.now)

@dataclass
class RoutingMetrics:
    """Routing metrics collection"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0
    requests_per_instance: Dict[str, int] = field(default_factory=dict)
    instance_response_times: Dict[str, List[float]] = field(default_factory=dict)
    circuit_breaker_activations: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

class LoadBalancer:
    """
    Advanced load balancer for DMLogn8n services
    """

    def __init__(self, consul_manager):
        self.consul_manager = consul_manager
        self.consul = consul_manager.consul
        self.service_instances = {}
        self.circuit_breakers = {}
        self.load_balancer_configs = {}
        self.routing_metrics = {}
        self.round_robin_counters = {}
        self.weighted_counters = {}
        self.adaptive_weights = {}
        self.session_affinity = {}
        self._shutdown = False
        self._health_check_tasks = {}

    async def register_load_balancer(self, config: LoadBalancerConfig) -> bool:
        """Register a new load balancer for a service"""
        try:
            service_name = config.service_name
            self.load_balancer_configs[service_name] = config

            # Initialize metrics
            self.routing_metrics[service_name] = RoutingMetrics()

            # Initialize counters
            self.round_robin_counters[service_name] = 0
            self.weighted_counters[service_name] = {}

            # Start health monitoring
            self._health_check_tasks[service_name] = asyncio.create_task(
                self._monitor_service_health(service_name)
            )

            # Discover initial service instances
            await self._discover_service_instances(service_name)

            logger.info(f"Load balancer registered for service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register load balancer: {e}")
            return False

    async def deregister_load_balancer(self, service_name: str) -> bool:
        """Deregister load balancer for a service"""
        try:
            # Stop health monitoring
            if service_name in self._health_check_tasks:
                self._health_check_tasks[service_name].cancel()
                del self._health_check_tasks[service_name]

            # Clean up data
            if service_name in self.service_instances:
                del self.service_instances[service_name]

            if service_name in self.circuit_breakers:
                del self.circuit_breakers[service_name]

            if service_name in self.load_balancer_configs:
                del self.load_balancer_configs[service_name]

            if service_name in self.routing_metrics:
                del self.routing_metrics[service_name]

            if service_name in self.round_robin_counters:
                del self.round_robin_counters[service_name]

            if service_name in self.weighted_counters:
                del self.weighted_counters[service_name]

            if service_name in self.adaptive_weights:
                del self.adaptive_weights[service_name]

            logger.info(f"Load balancer deregistered for service: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to deregister load balancer: {e}")
            return False

    async def select_instance(self,
                            service_name: str,
                            client_ip: Optional[str] = None,
                            session_id: Optional[str] = None) -> Optional[ServiceInstance]:
        """Select best service instance using configured algorithm"""
        try:
            if service_name not in self.service_instances:
                logger.warning(f"No instances found for service: {service_name}")
                return None

            instances = list(self.service_instances[service_name].values())
            healthy_instances = [inst for inst in instances if self._is_instance_healthy(inst)]

            if not healthy_instances:
                logger.warning(f"No healthy instances for service: {service_name}")
                return None

            config = self.load_balancer_configs.get(service_name)
            if not config:
                # Default to round robin
                config = LoadBalancerConfig(
                    algorithm=LoadBalancingAlgorithm.ROUND_ROBIN,
                    service_name=service_name
                )

            # Check for session affinity
            if config.enable_sticky_sessions:
                sticky_instance = await self._get_sticky_instance(service_name, client_ip, session_id)
                if sticky_instance and self._is_instance_healthy(sticky_instance):
                    return sticky_instance

            # Select instance based on algorithm
            if config.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return self._select_round_robin(service_name, healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return self._select_weighted_round_robin(service_name, healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return self._select_least_connections(healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.WEIGHTED_LEAST_CONNECTIONS:
                return self._select_weighted_least_connections(healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.IP_HASH:
                return self._select_ip_hash(healthy_instances, client_ip)
            elif config.algorithm == LoadBalancingAlgorithm.RANDOM:
                return self._select_random(healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
                return self._select_least_response_time(healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.HEALTH_AWARE:
                return self._select_health_aware(healthy_instances)
            elif config.algorithm == LoadBalancingAlgorithm.ADAPTIVE:
                return self._select_adaptive(service_name, healthy_instances)
            else:
                return self._select_round_robin(service_name, healthy_instances)

        except Exception as e:
            logger.error(f"Instance selection error: {e}")
            return None

    async def route_request(self,
                          service_name: str,
                          request_path: str,
                          method: str = "GET",
                          headers: Optional[Dict[str, str]] = None,
                          body: Optional[str] = None,
                          client_ip: Optional[str] = None,
                          session_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """Route request to selected service instance"""
        try:
            start_time = time.time()

            # Select instance
            instance = await self.select_instance(service_name, client_ip, session_id)
            if not instance:
                return False, {"error": "No healthy instances available"}, ""

            # Build target URL
            target_url = f"http://{instance.host}:{instance.port}{request_path}"

            # Make request
            response_time, success, response_data = await self._make_request(
                target_url, method, headers, body
            )

            # Update metrics
            await self._update_metrics(service_name, instance, success, response_time)

            # Update sticky session if enabled
            if success and self.load_balancer_configs.get(service_name, {}).get('enable_sticky_sessions'):
                await self._update_sticky_session(service_name, client_ip, session_id, instance)

            return success, response_data, ""

        except Exception as e:
            logger.error(f"Request routing error: {e}")
            return False, {"error": str(e)}, ""

    async def get_load_balancer_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get load balancer metrics for a service"""
        try:
            if service_name not in self.routing_metrics:
                return {}

            metrics = self.routing_metrics[service_name]
            instances = self.service_instances.get(service_name, {})

            # Calculate additional metrics
            total_response_times = []
            for instance in instances.values():
                if instance.response_times:
                    total_response_times.extend(instance.response_times[-100:])  # Last 100

            avg_response_time = statistics.mean(total_response_times) if total_response_times else 0
            p95_response_time = statistics.quantiles(total_response_times, n=20)[18] if len(total_response_times) >= 20 else 0

            return {
                'service_name': service_name,
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'success_rate': (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0,
                'avg_response_time': avg_response_time,
                'p95_response_time': p95_response_time,
                'active_instances': len([inst for inst in instances.values() if self._is_instance_healthy(inst)]),
                'total_instances': len(instances),
                'circuit_breaker_activations': metrics.circuit_breaker_activations,
                'algorithm': self.load_balancer_configs.get(service_name, {}).get('algorithm', {}).value,
                'last_updated': metrics.last_updated.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get load balancer metrics: {e}")
            return {}

    async def _discover_service_instances(self, service_name: str):
        """Discover service instances from Consul"""
        try:
            _, services = await self.consul.health.service(service_name, passing=True)

            instances = {}
            for service in services:
                service_id = service['Service']['ID']
                host = service['Service']['Address']
                port = service['Service']['Port']

                # Get service metadata
                metadata = service['Service'].get('Meta', {})
                weight = int(metadata.get('lb_weight', 1))
                max_connections = int(metadata.get('max_connections', 100))

                instance = ServiceInstance(
                    service_id=service_id,
                    host=host,
                    port=port,
                    weight=weight,
                    max_connections=max_connections,
                    metadata=metadata
                )

                instances[service_id] = instance

                # Initialize circuit breaker
                if service_id not in self.circuit_breakers:
                    self.circuit_breakers[service_id] = CircuitBreaker()

            self.service_instances[service_name] = instances
            logger.info(f"Discovered {len(instances)} instances for service: {service_name}")

        except Exception as e:
            logger.error(f"Service discovery error: {e}")

    async def _monitor_service_health(self, service_name: str):
        """Monitor service health and update instances"""
        while not self._shutdown:
            try:
                await self._discover_service_instances(service_name)
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(10)

    def _is_instance_healthy(self, instance: ServiceInstance) -> bool:
        """Check if instance is healthy"""
        try:
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(instance.service_id)
            if not circuit_breaker:
                return True

            if circuit_breaker.state == CircuitState.OPEN:
                # Check if timeout has passed
                if datetime.now() >= circuit_breaker.next_attempt_time:
                    circuit_breaker.state = CircuitState.HALF_OPEN
                    return True
                return False

            # Check connection limit
            if instance.current_connections >= instance.max_connections:
                return False

            # Check success rate
            if instance.success_rate < 0.5:  # Less than 50% success rate
                return False

            return True

        except Exception:
            return False

    def _select_round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin selection"""
        counter = self.round_robin_counters[service_name]
        selected_instance = instances[counter % len(instances)]
        self.round_robin_counters[service_name] = (counter + 1) % len(instances)
        return selected_instance

    def _select_weighted_round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round robin selection"""
        if service_name not in self.weighted_counters:
            self.weighted_counters[service_name] = {inst.service_id: 0 for inst in instances}

        counters = self.weighted_counters[service_name]
        total_weight = sum(inst.weight for inst in instances)

        # Select instance based on weights
        weighted_index = sum(counters[inst.service_id] for inst in instances) % total_weight
        current_weight = 0

        for instance in instances:
            current_weight += instance.weight
            if weighted_index < current_weight:
                counters[instance.service_id] += 1
                return instance

        # Fallback to first instance
        return instances[0]

    def _select_least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection"""
        return min(instances, key=lambda inst: inst.current_connections)

    def _select_weighted_least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted least connections selection"""
        def weighted_score(instance):
            # Score = current_connections / weight
            return instance.current_connections / max(instance.weight, 1)

        return min(instances, key=weighted_score)

    def _select_ip_hash(self, instances: List[ServiceInstance], client_ip: Optional[str]) -> ServiceInstance:
        """IP hash selection"""
        if not client_ip:
            return random.choice(instances)

        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(instances)
        return instances[index]

    def _select_random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection"""
        return random.choice(instances)

    def _select_least_response_time(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least response time selection"""
        def avg_response_time(instance):
            if not instance.response_times:
                return float('inf')
            return statistics.mean(instance.response_times[-10:])  # Last 10 requests

        return min(instances, key=avg_response_time)

    def _select_health_aware(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Health-aware selection"""
        def health_score(instance):
            score = 0

            # Success rate (40% weight)
            score += instance.success_rate * 0.4

            # Recent response times (30% weight)
            if instance.response_times:
                avg_time = statistics.mean(instance.response_times[-5:])
                score += max(0, (1 - avg_time / 5000)) * 0.3  # Normalize against 5s

            # Connection utilization (20% weight)
            utilization = instance.current_connections / instance.max_connections
            score += (1 - utilization) * 0.2

            # Circuit breaker status (10% weight)
            circuit_breaker = self.circuit_breakers.get(instance.service_id)
            if circuit_breaker and circuit_breaker.state == CircuitState.CLOSED:
                score += 0.1

            return score

        return max(instances, key=health_score)

    def _select_adaptive(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Adaptive selection using machine learning"""
        if service_name not in self.adaptive_weights:
            # Initialize weights
            self.adaptive_weights[service_name] = {
                inst.service_id: 1.0 for inst in instances
            }

        weights = self.adaptive_weights[service_name]
        config = self.load_balancer_configs.get(service_name)

        def adaptive_score(instance):
            base_score = weights.get(instance.service_id, 1.0)

            # Adjust based on recent performance
            if instance.response_times:
                recent_avg = statistics.mean(instance.response_times[-5:])
                performance_factor = max(0.1, 1 - (recent_avg / 5000))
                base_score *= performance_factor

            # Adjust based on success rate
            base_score *= instance.success_rate

            # Adjust based on current load
            load_factor = 1 - (instance.current_connections / instance.max_connections)
            base_score *= max(0.1, load_factor)

            return base_score

        selected_instance = max(instances, key=adaptive_score)

        # Update weights based on learning
        await self._update_adaptive_weights(service_name, selected_instance, config)

        return selected_instance

    async def _update_adaptive_weights(self, service_name: str, selected_instance: ServiceInstance, config: Optional[LoadBalancerConfig]):
        """Update adaptive weights based on performance"""
        try:
            if not config:
                return

            learning_rate = config.adaptive_learning_rate
            weights = self.adaptive_weights[service_name]

            # Reward selected instance if performing well
            if selected_instance.success_rate > 0.9 and selected_instance.response_times:
                recent_avg = statistics.mean(selected_instance.response_times[-5:])
                if recent_avg < 1000:  # Less than 1 second
                    weights[selected_instance.service_id] *= (1 + learning_rate)

            # Penalize poorly performing instances
            for instance in self.service_instances.get(service_name, {}).values():
                if instance.success_rate < 0.5:
                    weights[instance.service_id] *= (1 - learning_rate)

            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                for service_id in weights:
                    weights[service_id] /= total_weight

        except Exception as e:
            logger.error(f"Adaptive weight update error: {e}")

    async def _make_request(self, url: str, method: str, headers: Optional[Dict[str, str]], body: Optional[str]) -> Tuple[float, bool, Dict[str, Any]]:
        """Make HTTP request to service instance"""
        try:
            start_time = time.time()

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, headers=headers, data=body) as response:
                    response_time = (time.time() - start_time) * 1000
                    success = 200 <= response.status < 400

                    try:
                        response_data = await response.json()
                    except:
                        response_text = await response.text()
                        response_data = {"status": response.status, "text": response_text}

                    return response_time, success, response_data

        except asyncio.TimeoutError:
            return 5000, False, {"error": "Request timeout"}
        except Exception as e:
            return 5000, False, {"error": str(e)}

    async def _update_metrics(self, service_name: str, instance: ServiceInstance, success: bool, response_time: float):
        """Update routing metrics"""
        try:
            metrics = self.routing_metrics[service_name]
            metrics.total_requests += 1

            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

            # Update instance metrics
            instance.response_times.append(response_time)
            if len(instance.response_times) > 100:  # Keep last 100
                instance.response_times = instance.response_times[-100:]

            # Update requests per instance
            if instance.service_id not in metrics.requests_per_instance:
                metrics.requests_per_instance[instance.service_id] = 0
            metrics.requests_per_instance[instance.service_id] += 1

            # Update instance response times
            if instance.service_id not in metrics.instance_response_times:
                metrics.instance_response_times[instance.service_id] = []
            metrics.instance_response_times[instance.service_id].append(response_time)

            # Update instance success rate
            instance_success_count = metrics.requests_per_instance.get(instance.service_id, 0)
            if success:
                instance.success_rate = (instance.success_rate * (instance_success_count - 1) + 1) / instance_success_count
            else:
                instance.success_rate = (instance.success_rate * (instance_success_count - 1)) / instance_success_count

            # Update circuit breaker
            await self._update_circuit_breaker(instance, success)

            metrics.last_updated = datetime.now()

        except Exception as e:
            logger.error(f"Metrics update error: {e}")

    async def _update_circuit_breaker(self, instance: ServiceInstance, success: bool):
        """Update circuit breaker state"""
        try:
            circuit_breaker = self.circuit_breakers.get(instance.service_id)
            if not circuit_breaker:
                return

            if success:
                circuit_breaker.success_count += 1
                circuit_breaker.failure_count = max(0, circuit_breaker.failure_count - 1)

                if circuit_breaker.state == CircuitState.HALF_OPEN:
                    if circuit_breaker.success_count >= 3:  # 3 successful requests
                        circuit_breaker.state = CircuitState.CLOSED
                        circuit_breaker.failure_count = 0
                        logger.info(f"Circuit breaker closed for instance: {instance.service_id}")
            else:
                circuit_breaker.failure_count += 1
                circuit_breaker.last_failure_time = datetime.now()

                if circuit_breaker.state == CircuitState.CLOSED:
                    config = self.load_balancer_configs.get(instance.service_id)
                    threshold = config.circuit_breaker_threshold if config else 5

                    if circuit_breaker.failure_count >= threshold:
                        circuit_breaker.state = CircuitState.OPEN
                        circuit_breaker.next_attempt_time = datetime.now() + timedelta(seconds=60)
                        logger.warning(f"Circuit breaker opened for instance: {instance.service_id}")

                elif circuit_breaker.state == CircuitState.HALF_OPEN:
                    circuit_breaker.state = CircuitState.OPEN
                    circuit_breaker.next_attempt_time = datetime.now() + timedelta(seconds=60)
                    logger.warning(f"Circuit breaker re-opened for instance: {instance.service_id}")

        except Exception as e:
            logger.error(f"Circuit breaker update error: {e}")

    async def _get_sticky_instance(self, service_name: str, client_ip: Optional[str], session_id: Optional[str]) -> Optional[ServiceInstance]:
        """Get sticky session instance"""
        try:
            if not self.load_balancer_configs.get(service_name, {}).get('enable_sticky_sessions'):
                return None

            session_key = session_id or client_ip
            if not session_key:
                return None

            if service_name not in self.session_affinity:
                return None

            instance_id = self.session_affinity[service_name].get(session_key)
            if instance_id and instance_id in self.service_instances.get(service_name, {}):
                return self.service_instances[service_name][instance_id]

            return None

        except Exception:
            return None

    async def _update_sticky_session(self, service_name: str, client_ip: Optional[str], session_id: Optional[str], instance: ServiceInstance):
        """Update sticky session mapping"""
        try:
            session_key = session_id or client_ip
            if not session_key:
                return

            if service_name not in self.session_affinity:
                self.session_affinity[service_name] = {}

            self.session_affinity[service_name][session_key] = instance.service_id

        except Exception as e:
            logger.error(f"Sticky session update error: {e}")

    async def shutdown(self):
        """Shutdown load balancer"""
        self._shutdown = False

        # Cancel health monitoring tasks
        for task in self._health_check_tasks.values():
            task.cancel()

        if self._health_check_tasks:
            await asyncio.gather(*self._health_check_tasks.values(), return_exceptions=True)

        logger.info("Load balancer shutdown completed")

# Export main classes
__all__ = [
    'LoadBalancer',
    'LoadBalancerConfig',
    'ServiceInstance',
    'CircuitBreaker',
    'RoutingMetrics',
    'LoadBalancingAlgorithm',
    'CircuitState'
]