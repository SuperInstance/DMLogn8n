"""
API Gateway with Rate Limiting, Load Balancing, and Service Discovery
Central entry point for all microservices
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import redis
import jwt
import hashlib
import uuid
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import circuitbreaker
import tenacity
from consul import Consul, Check
import etcd3

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    service_name: str
    host: str
    port: int
    protocol: str = "http"
    path_prefix: str = ""
    weight: int = 1
    max_connections: int = 100
    timeout: float = 30.0
    retry_count: int = 3
    status: ServiceStatus = ServiceStatus.HEALTHY
    health_check_path: str = "/health"
    health_check_interval: int = 30
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    max_failures: int = 3


@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    name: str
    limit: int  # requests per window
    window: int  # seconds
    scope: str  # global, ip, user, api_key
    burst: int = 0  # burst capacity


@dataclass
class RouteConfig:
    """Route configuration"""
    path: str
    methods: List[str]
    service_name: str
    rewrite_path: Optional[str] = None
    auth_required: bool = True
    rate_limit_rules: List[RateLimitRule] = field(default_factory=list)
    timeout: Optional[float] = None
    retry_policy: Optional[Dict] = None
    headers_to_add: Dict[str, str] = field(default_factory=dict)
    headers_to_remove: List[str] = field(default_factory=list)
    circuit_breaker: Optional[Dict] = None


class APIGateway:
    """High-performance API Gateway"""

    def __init__(self):
        self.app = FastAPI(
            title="DMLogn8n API Gateway",
            description="Scalable API Gateway for Multi-Agent D&D System",
            version="1.0.0"
        )

        # Service registry
        self.services: Dict[str, List[ServiceEndpoint]] = defaultdict(list)
        self.service_weights: Dict[str, List[int]] = defaultdict(list)

        # Routing
        self.routes: Dict[str, RouteConfig] = {}

        # Rate limiting
        self.rate_limiters: Dict[str, Dict] = defaultdict(dict)
        self.redis_client: Optional[redis.Redis] = None

        # Circuit breakers
        self.circuit_breakers: Dict[str, circuitbreaker.CircuitBreaker] = {}

        # Service discovery
        self.consul_client: Optional[Consul] = None
        self.etcd_client: Optional[etcd3.Etcd3Client] = None

        # Metrics
        self.metrics = {
            "requests_total": Counter(
                "gateway_requests_total",
                "Total requests through gateway",
                ["method", "service", "status"]
            ),
            "request_duration": Histogram(
                "gateway_request_duration_seconds",
                "Request duration through gateway",
                ["method", "service"]
            ),
            "active_connections": Gauge(
                "gateway_active_connections",
                "Active connections",
                ["service"]
            ),
            "rate_limited": Counter(
                "gateway_rate_limited_total",
                "Total rate limited requests",
                ["rule"]
            ),
            "circuit_breaker_state": Gauge(
                "gateway_circuit_breaker_state",
                "Circuit breaker state (0=closed, 1=open, 2=half-open)",
                ["service"]
            )
        }

        # Connection pools
        self.connection_pools: Dict[str, aiohttp.ClientSession] = {}

        # Configuration
        self.config = {
            "default_timeout": 30.0,
            "max_request_size": 10 * 1024 * 1024,  # 10MB
            "enable_compression": True,
            "enable_cors": True,
            "cors_origins": ["*"],
            "cors_methods": ["*"],
            "cors_headers": ["*"],
            "health_check_interval": 30,
            "service_discovery": "consul",  # consul, etcd, static
            "load_balancing": "round_robin"  # round_robin, weighted, least_connections
        }

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS
        if self.config["enable_cors"]:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config["cors_origins"],
                allow_credentials=True,
                allow_methods=self.config["cors_methods"],
                allow_headers=self.config["cors_headers"]
            )

        # Compression
        if self.config["enable_compression"]:
            self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Custom middleware
        @self.app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response

        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            # Check rate limits before processing
            if not await self._check_rate_limits(request):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            return await call_next(request)

    def _setup_routes(self):
        """Setup API gateway routes"""
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": await self._get_service_health()
            }

        # Metrics endpoint
        @self.app.get("/metrics")
        async def metrics():
            return Response(generate_latest(), media_type="text/plain")

        # Routes configuration
        @self.app.get("/gateway/routes")
        async def list_routes():
            return {
                "routes": [
                    {
                        "path": route.path,
                        "methods": route.methods,
                        "service": route.service_name,
                        "auth_required": route.auth_required
                    }
                    for route in self.routes.values()
                ]
            }

        # Service discovery
        @self.app.post("/gateway/services/register")
        async def register_service(request: Request):
            data = await request.json()
            await self._register_service(data)
            return {"status": "registered"}

        @self.app.delete("/gateway/services/{service_name}")
        async def unregister_service(service_name: str):
            await self._unregister_service(service_name)
            return {"status": "unregistered"}

        # Proxy routes (catch-all)
        @self.app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def proxy_request(request: Request, path: str):
            return await self._proxy_request(request, path)

    async def initialize(self):
        """Initialize the API gateway"""
        logger.info("Initializing API Gateway")

        # Initialize Redis
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            db=3
        )

        # Initialize service discovery
        if self.config["service_discovery"] == "consul":
            self.consul_client = Consul(host='localhost', port=8500)
            await self._init_consul_service_discovery()
        elif self.config["service_discovery"] == "etcd":
            self.etcd_client = etcd3.client()
            await self._init_etcd_service_discovery()

        # Register default routes
        await self._register_default_routes()

        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._service_discovery_loop())
        asyncio.create_task(self._metrics_collection_loop())

        logger.info("API Gateway initialized")

    async def _register_default_routes(self):
        """Register default service routes"""
        default_routes = [
            RouteConfig(
                path="/api/v1/auth",
                methods=["POST", "GET"],
                service_name="auth_service",
                auth_required=False,
                rate_limit_rules=[
                    RateLimitRule("auth_requests", 10, 60, "ip", 20)
                ]
            ),
            RouteConfig(
                path="/api/v1/agents",
                methods=["GET", "POST", "PUT", "DELETE"],
                service_name="agent_service",
                auth_required=True,
                rate_limit_rules=[
                    RateLimitRule("agent_operations", 100, 60, "user", 150)
                ]
            ),
            RouteConfig(
                path="/api/v1/dialogues",
                methods=["GET", "POST"],
                service_name="dialogue_service",
                auth_required=True,
                rate_limit_rules=[
                    RateLimitRule("dialogue_generation", 50, 60, "user", 75)
                ]
            ),
            RouteConfig(
                path="/api/v1/combat",
                methods=["GET", "POST", "PUT"],
                service_name="combat_service",
                auth_required=True,
                rate_limit_rules=[
                    RateLimitRule("combat_operations", 200, 60, "user", 250)
                ]
            ),
            RouteConfig(
                path="/api/v1/world",
                methods=["GET", "POST"],
                service_name="world_service",
                auth_required=True,
                rate_limit_rules=[
                    RateLimitRule("world_operations", 1000, 60, "user", 1200)
                ]
            ),
            RouteConfig(
                path="/api/v1/metrics",
                methods=["GET"],
                service_name="metrics_service",
                auth_required=True,
                rate_limit_rules=[
                    RateLimitRule("metrics_access", 200, 60, "user", 250)
                ]
            )
        ]

        for route in default_routes:
            self.routes[route.path] = route

    async def _register_service(self, service_data: Dict[str, Any]):
        """Register a new service"""
        endpoint = ServiceEndpoint(
            service_name=service_data["service_name"],
            host=service_data["host"],
            port=service_data["port"],
            protocol=service_data.get("protocol", "http"),
            path_prefix=service_data.get("path_prefix", ""),
            weight=service_data.get("weight", 1),
            max_connections=service_data.get("max_connections", 100),
            timeout=service_data.get("timeout", 30.0),
            health_check_path=service_data.get("health_check_path", "/health"),
            health_check_interval=service_data.get("health_check_interval", 30)
        )

        self.services[endpoint.service_name].append(endpoint)

        # Create connection pool if not exists
        if endpoint.service_name not in self.connection_pools:
            connector = aiohttp.TCPConnector(
                limit=endpoint.max_connections,
                limit_per_host=endpoint.max_connections // 2
            )
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            self.connection_pools[endpoint.service_name] = session

        # Register in service discovery
        if self.consul_client:
            self.consul_client.agent.service.register(
                name=endpoint.service_name,
                service_id=f"{endpoint.service_name}-{endpoint.host}:{endpoint.port}",
                address=endpoint.host,
                port=endpoint.port,
                check=Check.http(
                    f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}{endpoint.health_check_path}",
                    interval=f"{endpoint.health_check_interval}s",
                    timeout="10s"
                )
            )

        logger.info(f"Service registered: {endpoint.service_name} at {endpoint.host}:{endpoint.port}")

    async def _unregister_service(self, service_name: str):
        """Unregister a service"""
        if service_name in self.services:
            del self.services[service_name]

        if service_name in self.connection_pools:
            await self.connection_pools[service_name].close()
            del self.connection_pools[service_name]

        if self.consul_client:
            self.consul_client.agent.service.deregister(service_name)

        logger.info(f"Service unregistered: {service_name}")

    async def _proxy_request(self, request: Request, path: str) -> JSONResponse:
        """Proxy request to appropriate service"""
        start_time = time.time()

        try:
            # Find matching route
            route = self._find_route(path, request.method)
            if not route:
                raise HTTPException(status_code=404, detail="Route not found")

            # Check authentication
            if route.auth_required:
                await self._authenticate_request(request)

            # Select service endpoint
            endpoint = await self._select_endpoint(route.service_name)
            if not endpoint:
                raise HTTPException(status_code=503, detail="Service unavailable")

            # Build target URL
            target_url = self._build_target_url(endpoint, route, path)

            # Prepare headers
            headers = self._prepare_headers(request, route)

            # Get request body
            body = await request.body()

            # Make request with circuit breaker
            breaker = self._get_circuit_breaker(route.service_name)

            @breaker
            async def make_request():
                session = self.connection_pools[route.service_name]
                return await session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body if body else None,
                    params=request.query_params
                )

            # Execute request with retry
            response = await self._execute_with_retry(make_request, route.retry_policy)

            # Process response
            response_data = await response.json() if response.content_type == "application/json" else await response.text()

            # Update metrics
            self._update_metrics(request, route, response, start_time)

            return JSONResponse(
                status_code=response.status,
                content=response_data,
                headers={
                    "X-Service": route.service_name,
                    "X-Service-Endpoint": f"{endpoint.host}:{endpoint.port}"
                }
            )

        except Exception as e:
            logger.error(f"Proxy request error: {e}")
            self._update_metrics(request, route, None, start_time, error=True)
            raise HTTPException(status_code=500, detail=str(e))

    def _find_route(self, path: str, method: str) -> Optional[RouteConfig]:
        """Find matching route for path and method"""
        # Sort routes by path length (longest first)
        sorted_routes = sorted(
            self.routes.values(),
            key=lambda r: len(r.path),
            reverse=True
        )

        for route in sorted_routes:
            if path.startswith(route.path) and method in route.methods:
                return route

        return None

    async def _select_endpoint(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Select service endpoint using load balancing"""
        endpoints = [
            e for e in self.services.get(service_name, [])
            if e.status == ServiceStatus.HEALTHY
        ]

        if not endpoints:
            return None

        if self.config["load_balancing"] == "round_robin":
            # Simple round-robin
            endpoint = endpoints[0]
            # Move to end of list
            self.services[service_name].remove(endpoint)
            self.services[service_name].append(endpoint)

        elif self.config["load_balancing"] == "weighted":
            # Weighted random selection
            total_weight = sum(e.weight for e in endpoints)
            if total_weight == 0:
                return endpoints[0]

            rand = random.random() * total_weight
            current = 0
            for endpoint in endpoints:
                current += endpoint.weight
                if rand <= current:
                    return endpoint

        elif self.config["load_balancing"] == "least_connections":
            # Least connections
            endpoint = min(endpoints, key=lambda e: e.max_connections)

        else:
            return endpoints[0]

        return endpoint

    def _build_target_url(self,
                         endpoint: ServiceEndpoint,
                         route: RouteConfig,
                         path: str) -> str:
        """Build target URL for service"""
        base_url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}"
        service_path = endpoint.path_prefix

        # Remove route prefix from path
        if path.startswith(route.path):
            service_path = path[len(route.path):]
        else:
            service_path = path

        # Apply rewrite rule if exists
        if route.rewrite_path:
            service_path = route.rewrite_path

        return f"{base_url}{service_path}"

    def _prepare_headers(self, request: Request, route: RouteConfig) -> Dict[str, str]:
        """Prepare headers for forwarded request"""
        headers = dict(request.headers)

        # Remove hop-by-hop headers
        for header in ["host", "connection", "keep-alive", "proxy-authenticate",
                       "proxy-authorization", "te", "trailers", "transfer-encoding"]:
            headers.pop(header, None)

        # Add custom headers
        for key, value in route.headers_to_add.items():
            headers[key] = value

        # Add forwarding headers
        headers["X-Forwarded-For"] = request.client.host
        headers["X-Forwarded-Proto"] = request.url.scheme
        headers["X-Forwarded-Host"] = request.url.hostname

        # Remove specified headers
        for header in route.headers_to_remove:
            headers.pop(header, None)

        return headers

    async def _execute_with_retry(self,
                                request_func: Callable,
                                retry_policy: Optional[Dict]) -> Any:
        """Execute request with retry policy"""
        if not retry_policy:
            return await request_func()

        max_retries = retry_policy.get("max_retries", 3)
        backoff_factor = retry_policy.get("backoff_factor", 1)
        max_delay = retry_policy.get("max_delay", 30)

        for attempt in range(max_retries + 1):
            try:
                return await request_func()
            except Exception as e:
                if attempt == max_retries:
                    raise

                delay = min(backoff_factor * (2 ** attempt), max_delay)
                await asyncio.sleep(delay)

    def _get_circuit_breaker(self, service_name: str) -> circuitbreaker.CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = circuitbreaker.CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30,
                expected_exception=Exception
            )
        return self.circuit_breakers[service_name]

    async def _check_rate_limits(self, request: Request) -> bool:
        """Check if request passes rate limits"""
        client_ip = request.client.host
        user_id = request.headers.get("X-User-ID")
        api_key = request.headers.get("X-API-Key")

        # Find applicable rate limit rules
        rules = []
        for route in self.routes.values():
            if request.url.path.startswith(route.path):
                rules.extend(route.rate_limit_rules)

        # Check each rule
        for rule in rules:
            if not await self._check_rate_limit_rule(rule, client_ip, user_id, api_key):
                self.metrics["rate_limited"].labels(rule=rule.name).inc()
                return False

        return True

    async def _check_rate_limit_rule(self,
                                    rule: RateLimitRule,
                                    client_ip: str,
                                    user_id: Optional[str],
                                    api_key: Optional[str]) -> bool:
        """Check individual rate limit rule"""
        # Determine scope key
        if rule.scope == "ip":
            key = f"rate_limit:{rule.name}:ip:{client_ip}"
        elif rule.scope == "user" and user_id:
            key = f"rate_limit:{rule.name}:user:{user_id}"
        elif rule.scope == "api_key" and api_key:
            key = f"rate_limit:{rule.name}:api:{api_key}"
        else:
            key = f"rate_limit:{rule.name}:global"

        # Check Redis
        if self.redis_client:
            current = self.redis_client.get(key)
            if current and int(current) >= rule.limit:
                return False

            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule.window)
            results = pipe.execute()

            return results[0] <= rule.limit

        # Fallback to in-memory
        now = time.time()
        if key not in self.rate_limiters:
            self.rate_limiters[key] = {"count": 0, "reset_time": now + rule.window}

        if now > self.rate_limiters[key]["reset_time"]:
            self.rate_limiters[key] = {"count": 0, "reset_time": now + rule.window}

        if self.rate_limiters[key]["count"] >= rule.limit:
            return False

        self.rate_limiters[key]["count"] += 1
        return True

    async def _authenticate_request(self, request: Request) -> None:
        """Authenticate request"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authorization scheme")

            # Verify JWT token (would integrate with auth service)
            payload = jwt.decode(
                token,
                "your-jwt-secret",
                algorithms=["HS256"]
            )

            # Add user info to headers
            request.headers["X-User-ID"] = payload.get("sub")
            request.headers["X-User-Role"] = payload.get("role")

        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    def _update_metrics(self,
                       request: Request,
                       route: RouteConfig,
                       response: Optional[Any],
                       start_time: float,
                       error: bool = False):
        """Update request metrics"""
        status = 500 if error else response.status if response else 500
        duration = time.time() - start_time

        self.metrics["requests_total"].labels(
            method=request.method,
            service=route.service_name,
            status=str(status)
        ).inc()

        self.metrics["request_duration"].labels(
            method=request.method,
            service=route.service_name
        ).observe(duration)

        # Update circuit breaker state
        if route.service_name in self.circuit_breakers:
            breaker = self.circuit_breakers[route.service_name]
            state = 0 if breaker.closed else 1 if breaker.open else 2
            self.metrics["circuit_breaker_state"].labels(
                service=route.service_name
            ).set(state)

    async def _health_check_loop(self):
        """Periodic health check for services"""
        while True:
            try:
                for service_name, endpoints in self.services.items():
                    for endpoint in endpoints:
                        await self._check_service_health(endpoint)

                await asyncio.sleep(self.config["health_check_interval"])

            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)

    async def _check_service_health(self, endpoint: ServiceEndpoint):
        """Check health of individual service endpoint"""
        try:
            health_url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}{endpoint.health_check_path}"
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))

            async with session.get(health_url) as response:
                if response.status == 200:
                    endpoint.status = ServiceStatus.HEALTHY
                    endpoint.consecutive_failures = 0
                else:
                    endpoint.consecutive_failures += 1
                    if endpoint.consecutive_failures >= endpoint.max_failures:
                        endpoint.status = ServiceStatus.UNHEALTHY

            await session.close()

        except Exception as e:
            logger.error(f"Health check failed for {endpoint.service_name}: {e}")
            endpoint.consecutive_failures += 1
            if endpoint.consecutive_failures >= endpoint.max_failures:
                endpoint.status = ServiceStatus.UNHEALTHY

        endpoint.last_health_check = datetime.now()

    async def _service_discovery_loop(self):
        """Service discovery synchronization"""
        while True:
            try:
                if self.consul_client:
                    await self._sync_consul_services()
                elif self.etcd_client:
                    await self._sync_etcd_services()

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Service discovery loop error: {e}")
                await asyncio.sleep(5)

    async def _sync_consul_services(self):
        """Synchronize services with Consul"""
        services = self.consul_client.agent.services()

        for service_id, service in services.items():
            if service['Service'] not in self.services:
                # Register discovered service
                await self._register_service({
                    "service_name": service['Service'],
                    "host": service['Address'],
                    "port": service['Port'],
                    "protocol": "http"
                })

    async def _sync_etcd_services(self):
        """Synchronize services with etcd"""
        services = self.etcd_client.get_prefix("/services/")

        for value, metadata in services:
            try:
                service_data = json.loads(value.decode('utf-8'))
                if service_data['service_name'] not in self.services:
                    await self._register_service(service_data)
            except:
                pass

    async def _metrics_collection_loop(self):
        """Collect and export metrics"""
        while True:
            try:
                # Collect custom metrics
                for service_name in self.services:
                    active_connections = len([
                        e for e in self.services[service_name]
                        if e.status == ServiceStatus.HEALTHY
                    ])
                    self.metrics["active_connections"].labels(
                        service=service_name
                    ).set(active_connections)

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)

    async def _get_service_health(self) -> Dict[str, str]:
        """Get health status of all services"""
        health_status = {}
        for service_name, endpoints in self.services.items():
            healthy = any(e.status == ServiceStatus.HEALTHY for e in endpoints)
            health_status[service_name] = "healthy" if healthy else "unhealthy"
        return health_status

    async def close(self):
        """Close gateway connections"""
        # Close connection pools
        for session in self.connection_pools.values():
            await session.close()

        # Close Redis
        if self.redis_client:
            self.redis_client.close()


# Initialize gateway
gateway = APIGateway()