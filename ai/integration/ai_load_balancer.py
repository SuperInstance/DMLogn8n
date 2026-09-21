#!/usr/bin/env python3
"""
Advanced AI Load Balancer - Intelligent load balancing across AI services
Provides optimal resource allocation, cost optimization, and performance management
"""

import asyncio
import time
import json
import logging
import numpy as np
import aiohttp
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import random
import statistics

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    ADAPTIVE = "adaptive"
    GEOGRAPHIC = "geographic"

class ProviderStatus(Enum):
    """AI provider status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

@dataclass
class AIProvider:
    """AI provider configuration"""
    name: str
    endpoint: str
    api_key: Optional[str] = None
    max_concurrent_requests: int = 100
    cost_per_1k_tokens: float = 0.01
    average_response_time: float = 0.5
    quality_score: float = 0.8
    reliability_score: float = 0.9
    weight: float = 1.0
    geographic_region: str = "us-east-1"
    supported_models: List[str] = None
    status: ProviderStatus = ProviderStatus.HEALTHY
    rate_limit_per_minute: int = 1000

@dataclass
class LoadBalancingConfig:
    """Configuration for load balancing"""
    providers: List[AIProvider]
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE
    health_check_interval: float = 30.0  # seconds
    health_check_timeout: float = 5.0
    circuit_breaker_threshold: int = 5  # consecutive failures
    circuit_breaker_timeout: float = 60.0  # seconds
    enable_cost_optimization: bool = True
    enable_quality_optimization: bool = True
    enable_geographic_routing: bool = False
    user_region: str = "us-east-1"
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: float = 30.0

@dataclass
class Request:
    """Incoming request to be load balanced"""
    request_id: str
    model: str
    prompt: str
    context: Optional[Dict[str, Any]] = None
    priority: int = 1
    user_id: Optional[str] = None
    user_region: Optional[str] = None
    max_cost: Optional[float] = None
    min_quality: Optional[float] = None
    created_at: datetime = None

@dataclass
class LoadBalancedResponse:
    """Response from load balanced request"""
    request_id: str
    provider: str
    response: Any
    response_time: float
    cost: float
    quality_score: float
    success: bool
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ProviderMetrics:
    """Performance metrics for a provider"""
    provider_name: str
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_cost: float = 0.0
    average_quality_score: float = 0.0
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_opened_at: Optional[datetime] = None

class AILoadBalancer:
    """Advanced AI load balancer with intelligent routing"""

    def __init__(self, config: LoadBalancingConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=20)

        # Provider management
        self.providers: Dict[str, AIProvider] = {p.name: p for p in config.providers}
        self.provider_metrics: Dict[str, ProviderMetrics] = {
            p.name: ProviderMetrics(provider_name=p.name) for p in config.providers
        }

        # Load balancing state
        self.round_robin_index = 0
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests: Dict[str, Request] = {}

        # Circuit breaker state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {
            p.name: {
                "open": False,
                "opened_at": None,
                "failure_count": 0
            } for p in config.providers
        }

        # Health monitoring
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics_collection_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.request_history: deque = deque(maxlen=10000)
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_response_time": 0.0,
            "total_cost": 0.0,
            "cost_savings": 0.0
        }

        logger.info(f"AILoadBalancer initialized with {len(self.providers)} providers")

    async def start(self):
        """Start the load balancer"""
        # Start health checks
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Start metrics collection
        self.metrics_collection_task = asyncio.create_task(self._metrics_collection_loop())

        logger.info("Load balancer started")

    async def stop(self):
        """Stop the load balancer"""
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.metrics_collection_task:
            self.metrics_collection_task.cancel()

        self.executor.shutdown(wait=True)
        logger.info("Load balancer stopped")

    async def execute_request(self, request: Request) -> LoadBalancedResponse:
        """Execute a load balanced request"""
        try:
            request.created_at = datetime.now()
            self.active_requests[request.request_id] = request

            # Select provider based on strategy
            provider = await self._select_provider(request)
            if not provider:
                raise Exception("No available providers")

            # Execute request with retries
            response = await self._execute_with_retry(request, provider)

            # Update metrics
            self._update_provider_metrics(provider.name, response)
            self._update_performance_stats(response)

            # Record in history
            self.request_history.append({
                "request_id": request.request_id,
                "provider": provider.name,
                "response_time": response.response_time,
                "cost": response.cost,
                "success": response.success,
                "timestamp": datetime.now()
            })

            return response

        except Exception as e:
            logger.error(f"Load balanced request failed: {e}")
            raise
        finally:
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]

    async def _select_provider(self, request: Request) -> Optional[AIProvider]:
        """Select provider based on configured strategy"""
        available_providers = [
            provider for provider in self.providers.values()
            if self._is_provider_available(provider, request)
        ]

        if not available_providers:
            logger.warning("No available providers")
            return None

        if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available_providers)
        elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(available_providers)
        elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(available_providers)
        elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(available_providers)
        elif self.config.strategy == LoadBalancingStrategy.COST_OPTIMIZED:
            return self._cost_optimized_selection(available_providers, request)
        elif self.config.strategy == LoadBalancingStrategy.QUALITY_OPTIMIZED:
            return self._quality_optimized_selection(available_providers, request)
        elif self.config.strategy == LoadBalancingStrategy.GEOGRAPHIC:
            return self._geographic_selection(available_providers, request)
        elif self.config.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._adaptive_selection(available_providers, request)
        else:
            return available_providers[0]

    def _is_provider_available(self, provider: AIProvider, request: Request) -> bool:
        """Check if provider is available for the request"""
        # Check status
        if provider.status != ProviderStatus.HEALTHY:
            return False

        # Check circuit breaker
        circuit_breaker = self.circuit_breakers[provider.name]
        if circuit_breaker["open"]:
            # Check if circuit breaker should be closed
            if (circuit_breaker["opened_at"] and
                datetime.now() - circuit_breaker["opened_at"] > timedelta(seconds=self.config.circuit_breaker_timeout)):
                circuit_breaker["open"] = False
                circuit_breaker["opened_at"] = None
                circuit_breaker["failure_count"] = 0
                logger.info(f"Circuit breaker closed for {provider.name}")
            else:
                return False

        # Check model support
        if provider.supported_models and request.model not in provider.supported_models:
            return False

        # Check concurrent request limit
        metrics = self.provider_metrics[provider.name]
        if metrics.active_connections >= provider.max_concurrent_requests:
            return False

        # Check user requirements
        if request.max_cost and provider.cost_per_1k_tokens > request.max_cost:
            return False

        if request.min_quality and provider.quality_score < request.min_quality:
            return False

        return True

    def _round_robin_selection(self, providers: List[AIProvider]) -> AIProvider:
        """Round robin provider selection"""
        provider = providers[self.round_robin_index % len(providers)]
        self.round_robin_index += 1
        return provider

    def _weighted_round_robin_selection(self, providers: List[AIProvider]) -> AIProvider:
        """Weighted round robin provider selection"""
        total_weight = sum(p.weight for p in providers)
        if total_weight == 0:
            return providers[0]

        # Create weighted list
        weighted_providers = []
        for provider in providers:
            weight = int(provider.weight * 10)  # Scale up for integer weights
            weighted_providers.extend([provider] * weight)

        provider = weighted_providers[self.round_robin_index % len(weighted_providers)]
        self.round_robin_index += 1
        return provider

    def _least_connections_selection(self, providers: List[AIProvider]) -> AIProvider:
        """Select provider with least active connections"""
        return min(providers, key=lambda p: self.provider_metrics[p.name].active_connections)

    def _least_response_time_selection(self, providers: List[AIProvider]) -> AIProvider:
        """Select provider with lowest average response time"""
        return min(providers, key=lambda p: self.provider_metrics[p.name].average_response_time)

    def _cost_optimized_selection(self, providers: List[AIProvider], request: Request) -> AIProvider:
        """Select provider based on cost optimization"""
        # Filter providers within cost constraints
        affordable_providers = [
            p for p in providers
            if not request.max_cost or p.cost_per_1k_tokens <= request.max_cost
        ]

        if not affordable_providers:
            # If no affordable providers, select cheapest
            return min(providers, key=lambda p: p.cost_per_1k_tokens)

        # Among affordable providers, select cheapest
        return min(affordable_providers, key=lambda p: p.cost_per_1k_tokens)

    def _quality_optimized_selection(self, providers: List[AIProvider], request: Request) -> AIProvider:
        """Select provider based on quality optimization"""
        # Filter providers meeting quality requirements
        qualified_providers = [
            p for p in providers
            if not request.min_quality or p.quality_score >= request.min_quality
        ]

        if not qualified_providers:
            # If no qualified providers, select highest quality
            return max(providers, key=lambda p: p.quality_score)

        # Among qualified providers, select highest quality
        return max(qualified_providers, key=lambda p: p.quality_score)

    def _geographic_selection(self, providers: List[AIProvider], request: Request) -> AIProvider:
        """Select provider based on geographic proximity"""
        user_region = request.user_region or self.config.user_region

        # Find providers in same region
        local_providers = [
            p for p in providers
            if p.geographic_region == user_region
        ]

        if local_providers:
            # Among local providers, use least connections
            return min(local_providers, key=lambda p: self.provider_metrics[p.name].active_connections)

        # Fallback to any provider
        return providers[0]

    def _adaptive_selection(self, providers: List[AIProvider], request: Request) -> AIProvider:
        """Adaptive provider selection based on multiple factors"""
        def calculate_provider_score(provider: AIProvider) -> float:
            metrics = self.provider_metrics[provider.name]

            # Response time score (lower is better)
            time_score = 1.0 / (metrics.average_response_time + 0.1)

            # Success rate score
            success_rate = (
                metrics.successful_requests / metrics.total_requests
                if metrics.total_requests > 0 else 1.0
            )

            # Cost score (lower cost is better)
            cost_score = 1.0 / (provider.cost_per_1k_tokens + 0.001)

            # Load score (lower load is better)
            load_score = 1.0 / (metrics.active_connections + 1)

            # Quality score
            quality_score = provider.quality_score

            # Weight the scores
            total_score = (
                time_score * 0.3 +
                success_rate * 0.3 +
                cost_score * 0.2 +
                load_score * 0.1 +
                quality_score * 0.1
            )

            return total_score

        return max(providers, key=calculate_provider_score)

    async def _execute_with_retry(self, request: Request, provider: AIProvider) -> LoadBalancedResponse:
        """Execute request with retry logic"""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Check if provider is still available
                if not self._is_provider_available(provider, request):
                    # Select different provider
                    new_provider = await self._select_provider(request)
                    if not new_provider:
                        raise Exception("No available providers for retry")
                    provider = new_provider

                # Execute request
                response = await self._execute_request(request, provider)
                response.retry_count = attempt

                # Reset failure count on success
                self.circuit_breakers[provider.name]["failure_count"] = 0

                return response

            except Exception as e:
                last_exception = e
                logger.warning(f"Request to {provider.name} failed (attempt {attempt + 1}): {e}")

                # Update circuit breaker
                self.circuit_breakers[provider.name]["failure_count"] += 1
                if (self.circuit_breakers[provider.name]["failure_count"] >=
                    self.config.circuit_breaker_threshold):
                    self.circuit_breakers[provider.name]["open"] = True
                    self.circuit_breakers[provider.name]["opened_at"] = datetime.now()
                    logger.warning(f"Circuit breaker opened for {provider.name}")

                # Wait before retry
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        # All retries failed
        return LoadBalancedResponse(
            request_id=request.request_id,
            provider=provider.name,
            response=None,
            response_time=0.0,
            cost=0.0,
            quality_score=0.0,
            success=False,
            retry_count=self.config.max_retries,
            metadata={"error": str(last_exception)}
        )

    async def _execute_request(self, request: Request, provider: AIProvider) -> LoadBalancedResponse:
        """Execute request to specific provider"""
        start_time = time.time()
        metrics = self.provider_metrics[provider.name]
        metrics.active_connections += 1

        try:
            # Simulate API call (in real implementation, this would make actual HTTP request)
            await asyncio.sleep(provider.average_response_time * random.uniform(0.8, 1.2))

            # Simulate response
            response_text = f"Response from {provider.name} for model {request.model}: {request.prompt[:50]}..."

            # Calculate cost (simplified)
            estimated_tokens = len(request.prompt.split()) + 50  # Estimate input + output tokens
            cost = (estimated_tokens / 1000) * provider.cost_per_1k_tokens

            # Simulate quality score
            quality_score = provider.quality_score * random.uniform(0.9, 1.1)
            quality_score = min(1.0, max(0.0, quality_score))

            response_time = time.time() - start_time

            return LoadBalancedResponse(
                request_id=request.request_id,
                provider=provider.name,
                response={"content": response_text, "model": request.model},
                response_time=response_time,
                cost=cost,
                quality_score=quality_score,
                success=True,
                metadata={
                    "estimated_tokens": estimated_tokens,
                    "provider_region": provider.geographic_region
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            raise e
        finally:
            metrics.active_connections -= 1

    def _update_provider_metrics(self, provider_name: str, response: LoadBalancedResponse):
        """Update provider performance metrics"""
        metrics = self.provider_metrics[provider_name]
        metrics.total_requests += 1

        if response.success:
            metrics.successful_requests += 1

            # Update average response time
            metrics.average_response_time = (
                (metrics.average_response_time * (metrics.total_requests - 1) + response.response_time) /
                metrics.total_requests
            )

            # Update average quality score
            metrics.average_quality_score = (
                (metrics.average_quality_score * (metrics.successful_requests - 1) + response.quality_score) /
                metrics.successful_requests
            )

            # Update total cost
            metrics.total_cost += response.cost
        else:
            metrics.failed_requests += 1

    def _update_performance_stats(self, response: LoadBalancedResponse):
        """Update overall performance statistics"""
        self.performance_stats["total_requests"] += 1

        if response.success:
            self.performance_stats["successful_requests"] += 1

            # Update average response time
            total = self.performance_stats["total_requests"]
            current_avg = self.performance_stats["average_response_time"]
            new_avg = (current_avg * (total - 1) + response.response_time) / total
            self.performance_stats["average_response_time"] = new_avg

            # Update total cost
            self.performance_stats["total_cost"] += response.cost

            # Calculate cost savings (compared to most expensive provider)
            most_expensive = max(p.cost_per_1k_tokens for p in self.providers.values())
            if response.provider in self.providers:
                provider_cost = self.providers[response.provider].cost_per_1k_tokens
                if provider_cost < most_expensive:
                    savings = (most_expensive - provider_cost) / most_expensive
                    self.performance_stats["cost_savings"] += savings * response.cost

    async def _health_check_loop(self):
        """Periodic health check loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)

    async def _perform_health_checks(self):
        """Perform health checks on all providers"""
        tasks = [
            self._check_provider_health(provider)
            for provider in self.providers.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            provider_name = list(self.providers.keys())[i]
            metrics = self.provider_metrics[provider_name]
            metrics.last_health_check = datetime.now()

            if isinstance(result, Exception):
                logger.warning(f"Health check failed for {provider_name}: {result}")
                self.providers[provider_name].status = ProviderStatus.UNHEALTHY
            else:
                self.providers[provider_name].status = result

    async def _check_provider_health(self, provider: AIProvider) -> ProviderStatus:
        """Check health of a specific provider"""
        try:
            # Simulate health check (in real implementation, this would make actual health check request)
            await asyncio.sleep(0.1)

            # Simulate random health status
            if random.random() < 0.95:  # 95% chance of being healthy
                return ProviderStatus.HEALTHY
            else:
                return ProviderStatus.DEGRADED

        except Exception as e:
            logger.error(f"Health check error for {provider.name}: {e}")
            return ProviderStatus.UNHEALTHY

    async def _metrics_collection_loop(self):
        """Periodic metrics collection"""
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(60)  # Collect metrics every minute
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)

    async def _collect_metrics(self):
        """Collect and aggregate metrics"""
        # This would collect various metrics like request rates, error rates, etc.
        # For now, we'll just log current stats
        stats = self.get_performance_stats()
        logger.debug(f"Current stats: {stats}")

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for provider_name, provider in self.providers.items():
            metrics = self.provider_metrics[provider_name]
            circuit_breaker = self.circuit_breakers[provider_name]

            status[provider_name] = {
                "status": provider.status.value,
                "active_connections": metrics.active_connections,
                "total_requests": metrics.total_requests,
                "success_rate": (
                    metrics.successful_requests / metrics.total_requests
                    if metrics.total_requests > 0 else 0.0
                ),
                "average_response_time": metrics.average_response_time,
                "average_quality_score": metrics.average_quality_score,
                "total_cost": metrics.total_cost,
                "circuit_breaker_open": circuit_breaker["open"],
                "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None
            }

        return status

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        total_requests = self.performance_stats["total_requests"]
        success_rate = (
            self.performance_stats["successful_requests"] / total_requests
            if total_requests > 0 else 0.0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": self.performance_stats["successful_requests"],
            "success_rate": success_rate,
            "average_response_time": self.performance_stats["average_response_time"],
            "total_cost": self.performance_stats["total_cost"],
            "cost_savings": self.performance_stats["cost_savings"],
            "active_requests": len(self.active_requests),
            "providers_count": len(self.providers),
            "healthy_providers": len([
                p for p in self.providers.values() if p.status == ProviderStatus.HEALTHY
            ])
        }

    def get_request_distribution(self) -> Dict[str, int]:
        """Get request distribution across providers"""
        distribution = defaultdict(int)
        for request_record in self.request_history:
            distribution[request_record["provider"]] += 1
        return dict(distribution)

    async def reset_circuit_breaker(self, provider_name: str) -> bool:
        """Manually reset circuit breaker for a provider"""
        if provider_name in self.circuit_breakers:
            self.circuit_breakers[provider_name]["open"] = False
            self.circuit_breakers[provider_name]["opened_at"] = None
            self.circuit_breakers[provider_name]["failure_count"] = 0
            logger.info(f"Circuit breaker manually reset for {provider_name}")
            return True
        return False

    async def set_provider_maintenance(self, provider_name: str, maintenance: bool) -> bool:
        """Set provider maintenance mode"""
        if provider_name in self.providers:
            if maintenance:
                self.providers[provider_name].status = ProviderStatus.MAINTENANCE
            else:
                self.providers[provider_name].status = ProviderStatus.HEALTHY
            logger.info(f"Provider {provider_name} maintenance mode: {maintenance}")
            return True
        return False

    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis and optimization recommendations"""
        provider_costs = {}
        for provider_name, metrics in self.provider_metrics.items():
            if metrics.total_requests > 0:
                avg_cost_per_request = metrics.total_cost / metrics.total_requests
                provider_costs[provider_name] = {
                    "total_cost": metrics.total_cost,
                    "avg_cost_per_request": avg_cost_per_request,
                    "requests": metrics.total_requests
                }

        # Find most cost-effective provider
        if provider_costs:
            most_cost_effective = min(
                provider_costs.items(),
                key=lambda x: x[1]["avg_cost_per_request"]
            )[0]
        else:
            most_cost_effective = None

        return {
            "provider_costs": provider_costs,
            "most_cost_effective": most_cost_effective,
            "total_spend": self.performance_stats["total_cost"],
            "estimated_savings": self.performance_stats["cost_savings"]
        }

# Example usage
async def demonstrate_load_balancer():
    """Demonstrate load balancer functionality"""
    # Configure providers
    providers = [
        AIProvider(
            name="openai-gpt4",
            endpoint="https://api.openai.com/v1",
            cost_per_1k_tokens=0.03,
            average_response_time=0.8,
            quality_score=0.9,
            weight=1.0,
            supported_models=["gpt-4", "gpt-4-turbo"]
        ),
        AIProvider(
            name="anthropic-claude",
            endpoint="https://api.anthropic.com/v1",
            cost_per_1k_tokens=0.015,
            average_response_time=0.6,
            quality_score=0.85,
            weight=0.8,
            supported_models=["claude-3-sonnet", "claude-3-haiku"]
        ),
        AIProvider(
            name="local-llama",
            endpoint="http://localhost:8080",
            cost_per_1k_tokens=0.001,
            average_response_time=1.2,
            quality_score=0.75,
            weight=0.5,
            supported_models=["llama-2", "llama-3"]
        )
    ]

    config = LoadBalancingConfig(
        providers=providers,
        strategy=LoadBalancingStrategy.ADAPTIVE,
        enable_cost_optimization=True,
        enable_quality_optimization=True
    )

    # Create and start load balancer
    load_balancer = AILoadBalancer(config)
    await load_balancer.start()

    # Execute some test requests
    for i in range(10):
        request = Request(
            request_id=f"test_req_{i}",
            model="gpt-4",
            prompt=f"Test request {i}: Explain AI load balancing",
            priority=1,
            max_cost=0.05,
            min_quality=0.8
        )

        response = await load_balancer.execute_request(request)
        print(f"Request {i}: {response.provider} - {response.response_time:.3f}s - ${response.cost:.4f} - Quality: {response.quality_score:.2f}")

    # Get statistics
    stats = load_balancer.get_performance_stats()
    print(f"\nPerformance Stats: {stats}")

    provider_status = load_balancer.get_provider_status()
    print(f"\nProvider Status: {provider_status}")

    cost_analysis = load_balancer.get_cost_analysis()
    print(f"\nCost Analysis: {cost_analysis}")

    await load_balancer.stop()

if __name__ == "__main__":
    asyncio.run(demonstrate_load_balancer())