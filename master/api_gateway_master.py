#!/usr/bin/env python3
"""
DMLogn8n Master API Gateway - Central API Gateway with Load Balancing
Central API gateway for all services with routing, authentication, and load balancing
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import aiofiles
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
from pathlib import Path
import hashlib
import hmac
import base64
from urllib.parse import urlparse, parse_qs
import statistics
import jwt

class RouteType(Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    STATIC = "static"
    PROXY = "proxy"
    REDIRECT = "redirect"

class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    RANDOM = "random"

class AuthType(Enum):
    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    BASIC = "basic"

@dataclass
class ServiceEndpoint:
    host: str
    port: int
    protocol: str = "http"
    path: str = ""
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    healthy: bool = True
    last_health_check: float = field(default_factory=time.time)
    response_times: List[float] = field(default_factory=list)
    total_requests: int = 0
    failed_requests: int = 0

@dataclass
class Route:
    id: str
    path: str
    method: str = "*"
    service_name: str
    endpoints: List[ServiceEndpoint] = field(default_factory=list)
    route_type: RouteType = RouteType.HTTP
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    auth_required: bool = False
    auth_type: AuthType = AuthType.NONE
    rate_limit: Optional[int] = None
    timeout: int = 30
    retry_attempts: int = 0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    middleware: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    strip_path: bool = False
    rewrite_path: Optional[str] = None
    enabled: bool = True

@dataclass
class APIKey:
    key_id: str
    key_hash: str
    name: str
    permissions: List[str]
    rate_limit: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    last_used: Optional[float] = None

@dataclass
class RateLimitInfo:
    requests: int = 0
    window_start: float = field(default_factory=time.time)
    blocked: bool = False
    block_expires: Optional[float] = None

@dataclass
class RequestMetrics:
    timestamp: float
    method: str
    path: str
    status_code: int
    response_time: float
    service_name: str
    endpoint_used: str
    user_agent: str
    ip_address: str

class MasterAPIGateway:
    """
    Central API gateway with advanced routing, load balancing, and security features
    """

    def __init__(self, event_bus=None, service_registry=None, config_manager=None):
        self.event_bus = event_bus
        self.service_registry = service_registry
        self.config_manager = config_manager
        self.logger = logging.getLogger('MasterAPIGateway')

        # Routing
        self.routes: Dict[str, Route] = {}
        self.route_index: Dict[str, List[str]] = {}  # path -> route_ids

        # Load balancing
        self.endpoint_counters: Dict[str, int] = {}  # For round-robin
        self.connection_tracking: Dict[str, int] = {}  # For least connections

        # Authentication
        self.api_keys: Dict[str, APIKey] = {}
        self.jwt_secret: Optional[str] = None

        # Rate limiting
        self.rate_limits: Dict[str, RateLimitInfo] = {}

        # Circuit breaking
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Metrics
        self.request_metrics: List[RequestMetrics] = []
        self.metrics_history_size = 10000

        # HTTP session
        self.http_session: Optional[ClientSession] = None

        # Middleware
        self.middleware_functions: Dict[str, Callable] = {}

        # Configuration
        self.gateway_port = 8000
        self.gateway_host = "0.0.0.0"
        self.health_check_interval = 30
        self.metrics_retention_hours = 24

        # State
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.running = False

        # Background tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics_cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the API gateway"""
        self.logger.info("Initializing Master API Gateway...")

        # Load configuration
        await self._load_configuration()

        # Initialize HTTP session
        timeout = ClientTimeout(total=60)
        self.http_session = ClientSession(timeout=timeout)

        # Register default middleware
        await self._register_default_middleware()

        # Create web application
        self.app = web.Application(middlewares=[self._middleware_handler])
        await self._setup_routes()

        # Load API keys
        await self._load_api_keys()

        # Initialize JWT secret
        await self._initialize_jwt()

        self.logger.info("Master API Gateway initialized")

    async def start(self):
        """Start the API gateway"""
        self.logger.info(f"Starting API Gateway on {self.gateway_host}:{self.gateway_port}")

        # Create and configure runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Create TCP site
        self.site = web.TCPSite(self.runner, self.gateway_host, self.gateway_port)
        await self.site.start()

        self.running = True

        # Start background tasks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.metrics_cleanup_task = asyncio.create_task(self._metrics_cleanup_loop())

        self.logger.info(f"API Gateway started successfully on port {self.gateway_port}")

        # Publish startup event
        if self.event_bus:
            await self.event_bus.publish("api_gateway.started", {
                'port': self.gateway_port,
                'routes_count': len(self.routes),
                'endpoints_count': sum(len(route.endpoints) for route in self.routes.values())
            })

    async def stop(self):
        """Stop the API gateway"""
        self.logger.info("Stopping API Gateway...")

        self.running = False

        # Stop background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.metrics_cleanup_task:
            self.metrics_cleanup_task.cancel()

        # Stop HTTP site
        if self.site:
            await self.site.stop()

        # Cleanup runner
        if self.runner:
            await self.runner.cleanup()

        # Close HTTP session
        if self.http_session:
            await self.http_session.close()

        self.logger.info("API Gateway stopped")

    async def add_route(self, route: Route) -> str:
        """Add a new route"""
        self.routes[route.id] = route

        # Update route index
        if route.path not in self.route_index:
            self.route_index[route.path] = []
        self.route_index[route.path].append(route.id)

        # Initialize endpoint counters
        for endpoint in route.endpoints:
            endpoint_key = f"{route.id}:{endpoint.host}:{endpoint.port}"
            if endpoint_key not in self.endpoint_counters:
                self.endpoint_counters[endpoint_key] = 0

        self.logger.info(f"Added route: {route.method} {route.path} -> {route.service_name}")
        return route.id

    async def remove_route(self, route_id: str):
        """Remove a route"""
        if route_id in self.routes:
            route = self.routes[route_id]

            # Remove from route index
            if route.path in self.route_index:
                self.route_index[route.path] = [
                    rid for rid in self.route_index[route.path] if rid != route_id
                ]
                if not self.route_index[route.path]:
                    del self.route_index[route.path]

            # Remove circuit breakers
            if route_id in self.circuit_breakers:
                del self.circuit_breakers[route_id]

            del self.routes[route_id]
            self.logger.info(f"Removed route: {route_id}")

    async def add_endpoint_to_route(self, route_id: str, endpoint: ServiceEndpoint):
        """Add endpoint to existing route"""
        if route_id in self.routes:
            self.routes[route_id].endpoints.append(endpoint)
            endpoint_key = f"{route_id}:{endpoint.host}:{endpoint.port}"
            self.endpoint_counters[endpoint_key] = 0
            self.logger.info(f"Added endpoint to route {route_id}: {endpoint.host}:{endpoint.port}")

    async def generate_api_key(self, name: str, permissions: List[str], rate_limit: int = None, expires_hours: int = None) -> Dict[str, str]:
        """Generate a new API key"""
        key_id = str(uuid.uuid4())
        raw_key = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip('=')

        # Create hash of the key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Set expiration
        expires_at = None
        if expires_hours:
            expires_at = time.time() + (expires_hours * 3600)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_at=expires_at
        )

        self.api_keys[key_id] = api_key
        await self._save_api_keys()

        self.logger.info(f"Generated API key: {name} ({key_id})")
        return {
            'key_id': key_id,
            'api_key': raw_key,
            'name': name,
            'permissions': permissions
        }

    def _setup_routes(self):
        """Setup HTTP routes for the gateway"""
        # Main handler for all requests
        self.app.router.add_route('*', '/{path:.*}', self._request_handler)

        # Gateway management endpoints
        self.app.router.add_get('/gateway/health', self._health_check)
        self.app.router.add_get('/gateway/metrics', self._get_metrics)
        self.app.router.add_get('/gateway/routes', self._list_routes)
        self.app.router.add_get('/gateway/status', self._get_status)

    async def _middleware_handler(self, request: web.Request, handler: Callable):
        """Global middleware handler"""
        start_time = time.time()

        try:
            # Apply global middleware
            request = await self._apply_global_middleware(request)

            # Process request
            response = await handler(request)

            # Add gateway headers
            response.headers['X-Gateway-Request-ID'] = str(uuid.uuid4())
            response.headers['X-Gateway-Response-Time'] = f"{(time.time() - start_time) * 1000:.2f}ms"

            return response

        except web.HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Middleware error: {e}")
            return web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    async def _request_handler(self, request: web.Request):
        """Main request handler"""
        try:
            # Find matching route
            route = await self._find_matching_route(request)
            if not route:
                return web.json_response(
                    {'error': 'Route not found'},
                    status=404
                )

            # Check if route is enabled
            if not route.enabled:
                return web.json_response(
                    {'error': 'Route disabled'},
                    status=503
                )

            # Authentication
            auth_result = await self._authenticate_request(request, route)
            if not auth_result['success']:
                return web.json_response(
                    {'error': auth_result['message']},
                    status=auth_result['status']
                )

            # Rate limiting
            rate_limit_result = await self._check_rate_limit(request, route)
            if not rate_limit_result['allowed']:
                return web.json_response(
                    {'error': 'Rate limit exceeded'},
                    status=429
                )

            # Circuit breaker check
            if await self._is_circuit_breaker_open(route.id):
                return web.json_response(
                    {'error': 'Service temporarily unavailable'},
                    status=503
                )

            # Select endpoint
            endpoint = await self._select_endpoint(route)
            if not endpoint:
                return web.json_response(
                    {'error': 'No available endpoints'},
                    status=503
                )

            # Proxy request
            response = await self._proxy_request(request, route, endpoint)

            # Update metrics
            await self._update_metrics(request, response, route, endpoint)

            # Update circuit breaker
            await self._update_circuit_breaker(route.id, response.status)

            return response

        except Exception as e:
            self.logger.error(f"Request handler error: {e}")
            return web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    async def _find_matching_route(self, request: web.Request) -> Optional[Route]:
        """Find matching route for request"""
        path = request.path
        method = request.method

        # Try exact match first
        if path in self.route_index:
            for route_id in self.route_index[path]:
                route = self.routes[route_id]
                if route.method == '*' or route.method == method:
                    return route

        # Try pattern matching
        for route_path, route_ids in self.route_index.items():
            if self._path_matches(path, route_path):
                for route_id in route_ids:
                    route = self.routes[route_id]
                    if route.method == '*' or route.method == method:
                        return route

        return None

    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """Check if request path matches route pattern"""
        # Simple pattern matching - could be enhanced with regex
        if '*' in route_path:
            route_parts = route_path.split('/')
            request_parts = request_path.split('/')

            if len(route_parts) != len(request_parts):
                return False

            for route_part, request_part in zip(route_parts, request_parts):
                if route_part != '*' and route_part != request_part:
                    return False

            return True
        else:
            return request_path == route_path

    async def _authenticate_request(self, request: web.Request, route: Route) -> Dict[str, Any]:
        """Authenticate request based on route requirements"""
        if not route.auth_required:
            return {'success': True}

        auth_header = request.headers.get('Authorization', '')

        if route.auth_type == AuthType.API_KEY:
            return await self._authenticate_api_key(request, route)
        elif route.auth_type == AuthType.JWT:
            return await self._authenticate_jwt(request, route)
        elif route.auth_type == AuthType.BASIC:
            return await self._authenticate_basic(request, route)
        else:
            return {'success': False, 'message': 'Unsupported auth type', 'status': 401}

    async def _authenticate_api_key(self, request: web.Request, route: Route) -> Dict[str, Any]:
        """Authenticate using API key"""
        api_key = request.headers.get('X-API-Key', '')
        if not api_key:
            api_key = request.query.get('api_key', '')

        if not api_key:
            return {'success': False, 'message': 'API key required', 'status': 401}

        # Hash the provided key and compare
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        for stored_key in self.api_keys.values():
            if hmac.compare_digest(stored_key.key_hash, key_hash):
                # Check expiration
                if stored_key.expires_at and time.time() > stored_key.expires_at:
                    return {'success': False, 'message': 'API key expired', 'status': 401}

                # Update last used
                stored_key.last_used = time.time()

                # Check permissions (simplified)
                if stored_key.permissions:
                    # Permission checking logic here
                    pass

                return {'success': True, 'api_key': stored_key}

        return {'success': False, 'message': 'Invalid API key', 'status': 401}

    async def _authenticate_jwt(self, request: web.Request, route: Route) -> Dict[str, Any]:
        """Authenticate using JWT"""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {'success': False, 'message': 'JWT token required', 'status': 401}

        token = auth_header[7:]  # Remove 'Bearer '

        try:
            if not self.jwt_secret:
                return {'success': False, 'message': 'JWT not configured', 'status': 500}

            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return {'success': True, 'payload': payload}

        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'JWT token expired', 'status': 401}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid JWT token', 'status': 401}

    async def _authenticate_basic(self, request: web.Request, route: Route) -> Dict[str, Any]:
        """Authenticate using basic auth"""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            return {'success': False, 'message': 'Basic auth required', 'status': 401}

        try:
            import base64
            credentials = base64.b64decode(auth_header[6:]).decode()
            username, password = credentials.split(':', 1)

            # Basic validation - in production, use proper authentication
            if username == 'admin' and password == 'password':
                return {'success': True, 'username': username}
            else:
                return {'success': False, 'message': 'Invalid credentials', 'status': 401}

        except Exception:
            return {'success': False, 'message': 'Invalid auth format', 'status': 401}

    async def _check_rate_limit(self, request: web.Request, route: Route) -> Dict[str, Any]:
        """Check rate limiting"""
        if not route.rate_limit:
            return {'allowed': True}

        client_ip = self._get_client_ip(request)
        rate_limit_key = f"{route.id}:{client_ip}"

        current_time = time.time()

        if rate_limit_key not in self.rate_limits:
            self.rate_limits[rate_limit_key] = RateLimitInfo()

        rate_info = self.rate_limits[rate_limit_key]

        # Check if blocked
        if rate_info.blocked and rate_info.block_expires and current_time < rate_info.block_expires:
            return {'allowed': False, 'retry_after': int(rate_info.block_expires - current_time)}

        # Reset window if expired
        if current_time - rate_info.window_start > 60:  # 1 minute window
            rate_info.requests = 0
            rate_info.window_start = current_time
            rate_info.blocked = False
            rate_info.block_expires = None

        # Check limit
        if rate_info.requests >= route.rate_limit:
            rate_info.blocked = True
            rate_info.block_expires = current_time + 300  # Block for 5 minutes
            return {'allowed': False, 'retry_after': 300}

        rate_info.requests += 1
        return {'allowed': True}

    def _get_client_ip(self, request: web.Request) -> str:
        """Get client IP address"""
        # Check for proxy headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.remote or 'unknown'

    async def _select_endpoint(self, route: Route) -> Optional[ServiceEndpoint]:
        """Select endpoint using load balancing strategy"""
        healthy_endpoints = [ep for ep in route.endpoints if ep.healthy]

        if not healthy_endpoints:
            return None

        if route.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_selection(route, healthy_endpoints)
        elif route.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_endpoints)
        elif route.load_balance_strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(route, healthy_endpoints)
        elif route.load_balance_strategy == LoadBalanceStrategy.IP_HASH:
            return self._ip_hash_selection(healthy_endpoints)
        elif route.load_balance_strategy == LoadBalanceStrategy.RANDOM:
            return self._random_selection(healthy_endpoints)
        else:
            return healthy_endpoints[0]

    def _round_robin_selection(self, route: Route, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Round-robin endpoint selection"""
        if route.id not in self.endpoint_counters:
            self.endpoint_counters[route.id] = 0

        index = self.endpoint_counters[route.id] % len(endpoints)
        self.endpoint_counters[route.id] += 1
        return endpoints[index]

    def _least_connections_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Least connections endpoint selection"""
        return min(endpoints, key=lambda ep: ep.current_connections)

    def _weighted_round_robin_selection(self, route: Route, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Weighted round-robin endpoint selection"""
        # Create weighted list
        weighted_endpoints = []
        for endpoint in endpoints:
            weighted_endpoints.extend([endpoint] * endpoint.weight)

        if route.id not in self.endpoint_counters:
            self.endpoint_counters[route.id] = 0

        index = self.endpoint_counters[route.id] % len(weighted_endpoints)
        self.endpoint_counters[route.id] += 1
        return weighted_endpoints[index]

    def _ip_hash_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """IP hash endpoint selection"""
        # This would need the client IP - simplified for now
        import random
        return random.choice(endpoints)

    def _random_selection(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Random endpoint selection"""
        import random
        return random.choice(endpoints)

    async def _proxy_request(self, request: web.Request, route: Route, endpoint: ServiceEndpoint) -> web.Response:
        """Proxy request to selected endpoint"""
        start_time = time.time()

        try:
            # Build target URL
            target_url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}"
            if route.strip_path:
                # Strip the route path from request path
                path = request.path[len(route.path):]
                if not path.startswith('/'):
                    path = '/' + path
            elif route.rewrite_path:
                # Rewrite the path
                path = route.rewrite_path
            else:
                path = request.path

            target_url += path

            # Add query parameters
            if request.query_string:
                target_url += f"?{request.query_string}"

            # Copy headers
            headers = dict(request.headers)
            headers.pop('Host', None)  # Remove Host header

            # Add custom headers
            headers.update(route.headers)

            # Add query parameters
            params = dict(request.query)
            params.update(route.query_params)

            # Increment connection count
            endpoint.current_connections += 1

            try:
                # Make the request
                async with self.http_session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    data=await request.read(),
                    timeout=route.timeout
                ) as response:
                    # Read response body
                    body = await response.read()

                    # Update endpoint metrics
                    response_time = time.time() - start_time
                    endpoint.response_times.append(response_time)
                    if len(endpoint.response_times) > 100:
                        endpoint.response_times = endpoint.response_times[-100:]
                    endpoint.total_requests += 1

                    if response.status >= 400:
                        endpoint.failed_requests += 1

                    # Create response
                    resp = web.Response(
                        body=body,
                        status=response.status,
                        headers=dict(response.headers)
                    )

                    # Add gateway headers
                    resp.headers['X-Gateway-Endpoint'] = f"{endpoint.host}:{endpoint.port}"
                    resp.headers['X-Gateway-Service'] = route.service_name

                    return resp

            finally:
                # Decrement connection count
                endpoint.current_connections -= 1

        except asyncio.TimeoutError:
            endpoint.failed_requests += 1
            return web.json_response(
                {'error': 'Gateway timeout'},
                status=504
            )
        except Exception as e:
            endpoint.failed_requests += 1
            self.logger.error(f"Proxy error: {e}")
            return web.json_response(
                {'error': 'Service unavailable'},
                status=502
            )

    async def _update_metrics(self, request: web.Request, response: web.Response, route: Route, endpoint: ServiceEndpoint):
        """Update request metrics"""
        metric = RequestMetrics(
            timestamp=time.time(),
            method=request.method,
            path=request.path,
            status_code=response.status,
            response_time=float(response.headers.get('X-Gateway-Response-Time', '0')),
            service_name=route.service_name,
            endpoint_used=f"{endpoint.host}:{endpoint.port}",
            user_agent=request.headers.get('User-Agent', ''),
            ip_address=self._get_client_ip(request)
        )

        self.request_metrics.append(metric)

        # Keep only recent metrics
        if len(self.request_metrics) > self.metrics_history_size:
            self.request_metrics = self.request_metrics[-self.metrics_history_size:]

        # Publish metric event
        if self.event_bus:
            await self.event_bus.publish("api_gateway.request", {
                'method': request.method,
                'path': request.path,
                'status_code': response.status,
                'response_time': metric.response_time,
                'service_name': route.service_name
            })

    async def _is_circuit_breaker_open(self, route_id: str) -> bool:
        """Check if circuit breaker is open for route"""
        if route_id not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[route_id]

        if breaker['state'] == 'open':
            # Check if timeout has passed
            if time.time() - breaker['opened_at'] > breaker['timeout']:
                breaker['state'] = 'half_open'
                return False
            return True

        return False

    async def _update_circuit_breaker(self, route_id: str, status_code: int):
        """Update circuit breaker state"""
        if route_id not in self.circuit_breakers:
            route = self.routes.get(route_id)
            if route:
                self.circuit_breakers[route_id] = {
                    'state': 'closed',
                    'failures': 0,
                    'threshold': route.circuit_breaker_threshold,
                    'timeout': route.circuit_breaker_timeout,
                    'opened_at': 0
                }
            else:
                return

        breaker = self.circuit_breakers[route_id]

        if status_code >= 500:
            breaker['failures'] += 1

            # Check if threshold reached
            if breaker['failures'] >= breaker['threshold'] and breaker['state'] == 'closed':
                breaker['state'] = 'open'
                breaker['opened_at'] = time.time()
                self.logger.warning(f"Circuit breaker opened for route {route_id}")

        elif breaker['state'] == 'half_open':
            if status_code < 500:
                breaker['state'] = 'closed'
                breaker['failures'] = 0
                self.logger.info(f"Circuit breaker closed for route {route_id}")

    async def _health_check_loop(self):
        """Periodic health check for endpoints"""
        while self.running:
            try:
                for route in self.routes.values():
                    for endpoint in route.endpoints:
                        await self._check_endpoint_health(route, endpoint)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)

    async def _check_endpoint_health(self, route: Route, endpoint: ServiceEndpoint):
        """Check health of individual endpoint"""
        try:
            health_url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}/health"

            async with self.http_session.get(health_url, timeout=5) as response:
                was_healthy = endpoint.healthy
                endpoint.healthy = response.status == 200
                endpoint.last_health_check = time.time()

                if was_healthy and not endpoint.healthy:
                    self.logger.warning(f"Endpoint {endpoint.host}:{endpoint.port} became unhealthy")
                elif not was_healthy and endpoint.healthy:
                    self.logger.info(f"Endpoint {endpoint.host}:{endpoint.port} became healthy")

        except Exception as e:
            endpoint.healthy = False
            endpoint.last_health_check = time.time()
            self.logger.debug(f"Health check failed for {endpoint.host}:{endpoint.port}: {e}")

    async def _metrics_cleanup_loop(self):
        """Cleanup old metrics"""
        while self.running:
            try:
                cutoff_time = time.time() - (self.metrics_retention_hours * 3600)
                self.request_metrics = [
                    m for m in self.request_metrics if m.timestamp > cutoff_time
                ]
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                self.logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _apply_global_middleware(self, request: web.Request) -> web.Request:
        """Apply global middleware to request"""
        # Add CORS headers if needed
        request.headers['X-Gateway-Timestamp'] = str(time.time())
        return request

    async def _load_configuration(self):
        """Load gateway configuration"""
        if self.config_manager:
            self.gateway_port = await self.config_manager.get('api_gateway.port', 8000)
            self.gateway_host = await self.config_manager.get('api_gateway.host', '0.0.0.0')
            self.health_check_interval = await self.config_manager.get('api_gateway.health_check_interval', 30)

    async def _load_api_keys(self):
        """Load API keys from storage"""
        # This would load from a secure storage
        pass

    async def _save_api_keys(self):
        """Save API keys to storage"""
        # This would save to a secure storage
        pass

    async def _initialize_jwt(self):
        """Initialize JWT secret"""
        if self.config_manager:
            self.jwt_secret = await self.config_manager.get('api_gateway.jwt_secret')

    async def _register_default_middleware(self):
        """Register default middleware functions"""
        # Add CORS middleware
        self.middleware_functions['cors'] = self._cors_middleware

    async def _cors_middleware(self, request: web.Request, handler: Callable):
        """CORS middleware"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    # Management endpoints
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0',
            'routes': len(self.routes),
            'endpoints': sum(len(route.endpoints) for route in self.routes.values())
        })

    async def _get_metrics(self, request: web.Request) -> web.Response:
        """Get gateway metrics"""
        recent_metrics = [m for m in self.request_metrics if time.time() - m.timestamp < 3600]

        if recent_metrics:
            avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
            requests_per_minute = len(recent_metrics) / 60
            error_rate = sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics)
        else:
            avg_response_time = 0
            requests_per_minute = 0
            error_rate = 0

        return web.json_response({
            'total_requests': len(self.request_metrics),
            'recent_requests': len(recent_metrics),
            'average_response_time': avg_response_time,
            'requests_per_minute': requests_per_minute,
            'error_rate': error_rate,
            'active_routes': sum(1 for route in self.routes.values() if route.enabled),
            'healthy_endpoints': sum(
                sum(1 for ep in route.endpoints if ep.healthy)
                for route in self.routes.values()
            )
        })

    async def _list_routes(self, request: web.Request) -> web.Response:
        """List all routes"""
        routes_data = []
        for route in self.routes.values():
            routes_data.append({
                'id': route.id,
                'path': route.path,
                'method': route.method,
                'service_name': route.service_name,
                'endpoints': [
                    {
                        'host': ep.host,
                        'port': ep.port,
                        'healthy': ep.healthy,
                        'current_connections': ep.current_connections
                    }
                    for ep in route.endpoints
                ],
                'enabled': route.enabled,
                'auth_required': route.auth_required
            })

        return web.json_response({'routes': routes_data})

    async def _get_status(self, request: web.Request) -> web.Response:
        """Get gateway status"""
        return web.json_response({
            'running': self.running,
            'uptime': time.time() - (self.request_metrics[0].timestamp if self.request_metrics else time.time()),
            'total_routes': len(self.routes),
            'active_endpoints': sum(
                sum(1 for ep in route.endpoints if ep.healthy)
                for route in self.routes.values()
            ),
            'circuit_breakers': {
                route_id: breaker['state']
                for route_id, breaker in self.circuit_breakers.items()
            }
        })

    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        return {
            'running': self.running,
            'port': self.gateway_port,
            'host': self.gateway_host,
            'total_routes': len(self.routes),
            'enabled_routes': sum(1 for route in self.routes.values() if route.enabled),
            'total_endpoints': sum(len(route.endpoints) for route in self.routes.values()),
            'healthy_endpoints': sum(
                sum(1 for ep in route.endpoints if ep.healthy)
                for route in self.routes.values()
            ),
            'total_requests': len(self.request_metrics),
            'api_keys': len(self.api_keys),
            'circuit_breakers': len(self.circuit_breakers),
            'middleware_functions': len(self.middleware_functions)
        }