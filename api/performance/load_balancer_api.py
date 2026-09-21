#!/usr/bin/env python3
"""
Intelligent API Load Balancing System
Advanced load balancing with health checks and failover
"""

import asyncio
import time
import json
import logging
import hashlib
import random
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import uuid
import aiohttp
import aioredis
import numpy as np
from fastapi import Request, Response, HTTPException
import orjson
import consul
import dns.resolver

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    HASH_BASED = "hash_based"
    RANDOM = "random"
    PREDICTIVE = "predictive"
    ADAPTIVE = "adaptive"

class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    UNKNOWN = "unknown"

class ServerType(Enum):
    """Types of backend servers"""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    GRPC = "grpc"
    WEBSOCKET = "websocket"

@dataclass
class ServerConfig:
    """Configuration for a backend server"""
    id: str
    host: str
    port: int
    protocol: ServerType
    weight: int = 1
    max_connections: int = 1000
    timeout: float = 30.0
    health_check_path: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: float = 5.0
    health_check_retries: int = 3
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def url(self) -> str:
        """Get server URL"""
        protocol_str = self.protocol.value
        if self.protocol in [ServerType.HTTP, ServerType.WEBSOCKET]:
            return f"{protocol_str}://{self.host}:{self.port}"
        else:
            return f"{protocol_str}://{self.host}:{self.port}"

@dataclass
class ServerStats:
    """Server statistics"""
    server_id: str
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: float = 0.0
    last_health_check: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_rate: float = 0.0

    def update_response_time(self, response_time: float):
        """Update response time statistics"""
        self.response_times.append(response_time)
        if self.response_times:
            self.avg_response_time = sum(self.response_times) / len(self.response_times)

    def update_request_stats(self, success: bool):
        """Update request statistics"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests

@dataclass
class LoadBalancingConfig:
    """Configuration for load balancer"""
    # Algorithm settings
    algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN
    enable_sticky_sessions: bool = False
    session_cookie_name: str = "LB_SESSION"
    session_timeout: int = 3600  # seconds

    # Health check settings
    enable_health_checks: bool = True
    health_check_interval: int = 30
    health_check_timeout: float = 5.0
    health_check_retries: int = 3
    unhealthy_threshold: int = 3
    healthy_threshold: int = 2

    # Failover settings
    enable_failover: bool = True
    failover_timeout: float = 10.0
    max_failover_attempts: int = 3
    circuit_breaker_threshold: float = 0.5  # 50% error rate
    circuit_breaker_timeout: int = 60  # seconds

    # Performance settings
    enable_connection_pooling: bool = True
    max_connections_per_server: int = 100
    connection_timeout: float = 5.0
    read_timeout: float = 30.0
    keepalive_timeout: float = 30.0

    # Discovery settings
    enable_service_discovery: bool = True
    discovery_type: str = "consul"  # consul, dns, static
    consul_url: str = "http://localhost:8500"
    service_name: str = "api-service"
    dns_domain: str = "service.local"

    # Advanced settings
    enable_predictive_scaling: bool = True
    enable_adaptive_routing: bool = True
    enable_geo_routing: bool = False
    enable_content_based_routing: bool = True

class HealthChecker:
    """Advanced health checking system"""

    def __init__(self, config: LoadBalancingConfig):
        self.config = config
        self.health_status: Dict[str, HealthStatus] = {}
        self.health_history: Dict[str, List[bool]] = defaultdict(list)
        self.check_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start health checking"""
        if self.config.enable_health_checks:
            self.check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self):
        """Stop health checking"""
        if self.check_task:
            self.check_task.cancel()

    async def check_server_health(self, server: ServerConfig) -> bool:
        """Check individual server health"""
        try:
            if server.protocol in [ServerType.HTTP, ServerType.HTTPS]:
                return await self._check_http_health(server)
            elif server.protocol == ServerType.TCP:
                return await self._check_tcp_health(server)
            else:
                return True  # Assume healthy for unsupported protocols

        except Exception as e:
            logger.error(f"Health check error for {server.id}: {e}")
            return False

    async def _check_http_health(self, server: ServerConfig) -> bool:
        """Check HTTP server health"""
        url = f"{server.url}{server.health_check_path}"
        timeout = aiohttp.ClientTimeout(total=server.health_check_timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                return response.status < 500

    async def _check_tcp_health(self, server: ServerConfig) -> bool:
        """Check TCP server health"""
        try:
            future = asyncio.open_connection(server.host, server.port)
            reader, writer = await asyncio.wait_for(future, timeout=server.health_check_timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    async def _health_check_loop(self):
        """Main health checking loop"""
        while True:
            try:
                # This would need access to server list
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)

    def update_health_status(self, server_id: str, healthy: bool):
        """Update health status for a server"""
        self.health_history[server_id].append(healthy)
        if len(self.health_history[server_id]) > 10:
            self.health_history[server_id] = self.health_history[server_id][-10:]

        recent_checks = self.health_history[server_id][-self.config.healthy_threshold:]
        if len(recent_checks) >= self.config.healthy_threshold:
            if all(recent_checks):
                self.health_status[server_id] = HealthStatus.HEALTHY
            elif sum(recent_checks) < self.config.unhealthy_threshold:
                self.health_status[server_id] = HealthStatus.UNHEALTHY
            else:
                self.health_status[server_id] = HealthStatus.UNKNOWN

class ServiceDiscovery:
    """Service discovery integration"""

    def __init__(self, config: LoadBalancingConfig):
        self.config = config
        self.consul_client = None
        self.discovery_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize service discovery"""
        if self.config.discovery_type == "consul":
            self.consul_client = consul.Consul(
                host=self.config.consul_url.split(':')[1].strip('//'),
                port=int(self.config.consul_url.split(':')[2]),
                timeout=5
            )

        if self.config.enable_service_discovery:
            self.discovery_task = asyncio.create_task(self._discovery_loop())

    async def stop(self):
        """Stop service discovery"""
        if self.discovery_task:
            self.discovery_task.cancel()

    async def discover_servers(self) -> List[ServerConfig]:
        """Discover backend servers"""
        if self.config.discovery_type == "consul":
            return await self._discover_consul_servers()
        elif self.config.discovery_type == "dns":
            return await self._discover_dns_servers()
        else:
            return []  # Static configuration

    async def _discover_consul_servers(self) -> List[ServerConfig]:
        """Discover servers via Consul"""
        if not self.consul_client:
            return []

        try:
            _, services = self.consul_client.health.service(
                self.config.service_name,
                passing=True
            )

            servers = []
            for service in services:
                server_config = ServerConfig(
                    id=service['Service']['ID'],
                    host=service['Service']['Address'],
                    port=service['Service']['Port'],
                    protocol=ServerType.HTTP,
                    weight=service['Service'].get('Meta', {}).get('weight', 1)
                )
                servers.append(server_config)

            return servers

        except Exception as e:
            logger.error(f"Consul discovery error: {e}")
            return []

    async def _discover_dns_servers(self) -> List[ServerConfig]:
        """Discover servers via DNS"""
        try:
            answers = dns.resolver.resolve(self.config.dns_domain, 'A')
            servers = []
            for answer in answers:
                server_config = ServerConfig(
                    id=str(answer),
                    host=str(answer),
                    port=80,
                    protocol=ServerType.HTTP
                )
                servers.append(server_config)

            return servers

        except Exception as e:
            logger.error(f"DNS discovery error: {e}")
            return []

    async def _discovery_loop(self):
        """Service discovery loop"""
        while True:
            try:
                # Server discovery would be handled by the main load balancer
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
                await asyncio.sleep(10)

class LoadBalancingAlgorithms:
    """Load balancing algorithm implementations"""

    @staticmethod
    def round_robin(servers: List[ServerConfig], stats: Dict[str, ServerStats]) -> Optional[ServerConfig]:
        """Round robin algorithm"""
        if not servers:
            return None

        # Use a simple round-robin counter (would need to be stored in the class)
        return servers[0]  # Simplified

    @staticmethod
    def weighted_round_robin(servers: List[ServerConfig], stats: Dict[str, ServerStats]) -> Optional[ServerConfig]:
        """Weighted round robin algorithm"""
        if not servers:
            return None

        total_weight = sum(server.weight for server in servers)
        if total_weight == 0:
            return servers[0]

        # Select server based on weight
        rand = random.uniform(0, total_weight)
        current_weight = 0

        for server in servers:
            current_weight += server.weight
            if rand <= current_weight:
                return server

        return servers[0]

    @staticmethod
    def least_connections(servers: List[ServerConfig], stats: Dict[str, ServerStats]) -> Optional[ServerConfig]:
        """Least connections algorithm"""
        if not servers:
            return None

        min_connections = float('inf')
        selected_server = None

        for server in servers:
            server_stats = stats.get(server.id, ServerStats(server.id))
            if server_stats.active_connections < min_connections:
                min_connections = server_stats.active_connections
                selected_server = server

        return selected_server

    @staticmethod
    def least_response_time(servers: List[ServerConfig], stats: Dict[str, ServerStats]) -> Optional[ServerConfig]:
        """Least response time algorithm"""
        if not servers:
            return None

        min_response_time = float('inf')
        selected_server = None

        for server in servers:
            server_stats = stats.get(server.id, ServerStats(server.id))
            if server_stats.avg_response_time < min_response_time:
                min_response_time = server_stats.avg_response_time
                selected_server = server

        return selected_server

    @staticmethod
    def hash_based(servers: List[ServerConfig], stats: Dict[str, ServerStats],
                   request: Request) -> Optional[ServerConfig]:
        """Hash-based algorithm for session affinity"""
        if not servers:
            return None

        # Use client IP or session ID for hashing
        hash_key = request.client.host if request.client else "default"
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        server_index = hash_value % len(servers)
        return servers[server_index]

    @staticmethod
    def random(servers: List[ServerConfig], stats: Dict[str, ServerStats]) -> Optional[ServerConfig]:
        """Random selection algorithm"""
        if not servers:
            return None

        return random.choice(servers)

class LoadBalancer:
    """Intelligent load balancer with advanced features"""

    def __init__(self, config: LoadBalancingConfig = None):
        self.config = config or LoadBalancingConfig()
        self.servers: List[ServerConfig] = []
        self.server_stats: Dict[str, ServerStats] = {}
        self.health_checker = HealthChecker(self.config)
        self.service_discovery = ServiceDiscovery(self.config)

        # Algorithm mapping
        self.algorithms = {
            LoadBalancingAlgorithm.ROUND_ROBIN: LoadBalancingAlgorithms.round_robin,
            LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN: LoadBalancingAlgorithms.weighted_round_robin,
            LoadBalancingAlgorithm.LEAST_CONNECTIONS: LoadBalancingAlgorithms.least_connections,
            LoadBalancingAlgorithm.LEAST_RESPONSE_TIME: LoadBalancingAlgorithms.least_response_time,
            LoadBalancingAlgorithm.HASH_BASED: LoadBalancingAlgorithms.hash_based,
            LoadBalancingAlgorithm.RANDOM: LoadBalancingAlgorithms.random
        }

        # Load balancer state
        self.current_index = 0
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Connection pooling
        self.connection_pools: Dict[str, aiohttp.ClientSession] = {}

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'active_connections': 0,
            'avg_response_time': 0.0
        }

    async def initialize(self):
        """Initialize load balancer"""
        await self.service_discovery.initialize()
        await self.health_checker.start()

        # Discover initial servers
        discovered_servers = await self.service_discover_servers()
        if discovered_servers:
            self.servers.extend(discovered_servers)
            for server in discovered_servers:
                self.server_stats[server.id] = ServerStats(server.id)

    async def shutdown(self):
        """Shutdown load balancer"""
        await self.service_discovery.stop()
        await self.health_checker.stop()

        # Close connection pools
        for pool in self.connection_pools.values():
            await pool.close()

    def add_server(self, server: ServerConfig):
        """Add backend server"""
        self.servers.append(server)
        self.server_stats[server.id] = ServerStats(server.id)

    def remove_server(self, server_id: str):
        """Remove backend server"""
        self.servers = [s for s in self.servers if s.id != server_id]
        self.server_stats.pop(server_id, None)
        self.circuit_breakers.pop(server_id, None)

        # Close connection pool
        if server_id in self.connection_pools:
            asyncio.create_task(self.connection_pools[server_id].close())

    async def service_discover_servers(self):
        """Discover servers from service discovery"""
        return await self.service_discovery.discover_servers()

    async def select_server(self, request: Request) -> Optional[ServerConfig]:
        """Select best server for request"""
        # Filter healthy servers
        healthy_servers = [
            server for server in self.servers
            if server.enabled and self._is_server_healthy(server.id)
        ]

        if not healthy_servers:
            logger.warning("No healthy servers available")
            return None

        # Apply load balancing algorithm
        algorithm = self.algorithms.get(self.config.algorithm)
        if not algorithm:
            algorithm = LoadBalancingAlgorithms.round_robin

        selected_server = None

        if self.config.algorithm == LoadBalancingAlgorithm.HASH_BASED:
            selected_server = algorithm(healthy_servers, self.server_stats, request)
        else:
            selected_server = algorithm(healthy_servers, self.server_stats)

        # Check circuit breaker
        if self._is_circuit_breaker_open(selected_server.id):
            # Try another server
            healthy_servers_without_selected = [
                s for s in healthy_servers if s.id != selected_server.id
            ]
            if healthy_servers_without_selected:
                selected_server = algorithm(healthy_servers_without_selected, self.server_stats)
            else:
                return None

        return selected_server

    async def forward_request(self, request: Request, server: ServerConfig) -> Response:
        """Forward request to selected server"""
        server_stats = self.server_stats.get(server.id)
        if not server_stats:
            raise HTTPException(status_code=503, detail="Server not found")

        start_time = time.perf_counter()
        server_stats.active_connections += 1
        server_stats.last_request_time = start_time

        try:
            # Get or create connection pool
            session = await self._get_connection_pool(server)

            # Build target URL
            target_url = f"{server.url}{request.url.path}"
            if request.url.query:
                target_url += f"?{request.url.query}"

            # Forward request
            headers = dict(request.headers)
            headers.pop('host', None)  # Remove original host header

            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=await request.body(),
                timeout=aiohttp.ClientTimeout(total=server.timeout)
            ) as response:
                # Read response
                content = await response.read()
                response_time = time.perf_counter() - start_time

                # Update statistics
                server_stats.update_response_time(response_time)
                server_stats.update_request_stats(response.status < 400)
                self.stats['total_requests'] += 1
                if response.status < 400:
                    self.stats['successful_requests'] += 1
                else:
                    self.stats['failed_requests'] += 1

                # Update circuit breaker
                self._update_circuit_breaker(server.id, response.status < 400)

                return Response(
                    content=content,
                    status_code=response.status,
                    headers=dict(response.headers)
                )

        except Exception as e:
            server_stats.update_request_stats(False)
            self.stats['failed_requests'] += 1
            self._update_circuit_breaker(server.id, False)
            raise HTTPException(status_code=502, detail=f"Upstream server error: {str(e)}")

        finally:
            server_stats.active_connections -= 1

    async def _get_connection_pool(self, server: ServerConfig) -> aiohttp.ClientSession:
        """Get or create connection pool for server"""
        if server.id not in self.connection_pools:
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections_per_server,
                limit_per_host=self.config.max_connections_per_server,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=self.config.keepalive_timeout,
                enable_cleanup_closed=True
            )

            timeout = aiohttp.ClientTimeout(
                total=server.timeout,
                connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout
            )

            self.connection_pools[server.id] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

        return self.connection_pools[server.id]

    def _is_server_healthy(self, server_id: str) -> bool:
        """Check if server is healthy"""
        health_status = self.health_checker.health_status.get(server_id)
        return health_status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]

    def _is_circuit_breaker_open(self, server_id: str) -> bool:
        """Check if circuit breaker is open"""
        breaker = self.circuit_breakers.get(server_id)
        if not breaker:
            return False

        if breaker['state'] == 'open':
            # Check if timeout has passed
            if time.time() - breaker['opened_at'] > self.config.circuit_breaker_timeout:
                breaker['state'] = 'half_open'
                return False
            return True

        return False

    def _update_circuit_breaker(self, server_id: str, success: bool):
        """Update circuit breaker state"""
        if server_id not in self.circuit_breakers:
            self.circuit_breakers[server_id] = {
                'state': 'closed',
                'failures': 0,
                'opened_at': 0
            }

        breaker = self.circuit_breakers[server_id]
        server_stats = self.server_stats.get(server_id)

        if success:
            if breaker['state'] == 'half_open':
                breaker['state'] = 'closed'
            breaker['failures'] = 0
        else:
            breaker['failures'] += 1

            # Check if we should open the circuit breaker
            error_rate = server_stats.error_rate if server_stats else 0
            if (error_rate >= self.config.circuit_breaker_threshold or
                breaker['failures'] >= 5):
                breaker['state'] = 'open'
                breaker['opened_at'] = time.time()

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming request with load balancing"""
        try:
            # Select server
            server = await self.select_server(request)
            if not server:
                raise HTTPException(status_code=503, detail="No available servers")

            # Forward request
            return await self.forward_request(request, server)

        except Exception as e:
            logger.error(f"Load balancing error: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")

    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        server_stats = {}
        for server_id, stats in self.server_stats.items():
            server_stats[server_id] = asdict(stats)

        return {
            'load_balancer_stats': self.stats,
            'server_stats': server_stats,
            'servers': [asdict(server) for server in self.servers],
            'circuit_breakers': self.circuit_breakers,
            'health_status': {
                server_id: status.value
                for server_id, status in self.health_checker.health_status.items()
            }
        }

# FastAPI integration
class LoadBalancingMiddleware:
    """FastAPI middleware for load balancing"""

    def __init__(self, app, load_balancer: LoadBalancer):
        self.app = app
        self.load_balancer = load_balancer

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object
        request = Request(scope, receive)

        try:
            # Handle request through load balancer
            response = await self.load_balancer.handle_request(request)

            # Send response
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": response.raw_headers,
            })

            await send({
                "type": "http.response.body",
                "body": response.body,
            })

        except Exception as e:
            await send({
                "type": "http.response.start",
                "status": 503,
                "headers": [(b"content-type", b"application/json")],
            })

            await send({
                "type": "http.response.body",
                "body": orjson.dumps({"error": str(e)}),
            })

# Management API
class LoadBalancingAPI:
    """API for managing load balancer"""

    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer

    def register_routes(self, app):
        """Register management endpoints"""

        @app.get("/lb/servers")
        async def get_servers():
            """Get all servers"""
            return {
                'servers': [asdict(server) for server in self.load_balancer.servers]
            }

        @app.post("/lb/servers")
        async def add_server(server: ServerConfig):
            """Add new server"""
            self.load_balancer.add_server(server)
            return {'status': 'added', 'server_id': server.id}

        @app.delete("/lb/servers/{server_id}")
        async def remove_server(server_id: str):
            """Remove server"""
            self.load_balancer.remove_server(server_id)
            return {'status': 'removed', 'server_id': server_id}

        @app.get("/lb/stats")
        async def get_stats():
            """Get load balancer statistics"""
            return self.load_balancer.get_stats()

        @app.post("/lb/discover")
        async def discover_servers():
            """Trigger server discovery"""
            servers = await self.load_balancer.service_discover_servers()
            for server in servers:
                self.load_balancer.add_server(server)
            return {
                'status': 'discovered',
                'servers_added': len(servers)
            }

        @app.post("/lb/algorithm")
        async def set_algorithm(algorithm: LoadBalancingAlgorithm):
            """Set load balancing algorithm"""
            self.load_balancer.config.algorithm = algorithm
            return {'status': 'updated', 'algorithm': algorithm.value}

if __name__ == "__main__":
    # Example usage
    async def main():
        config = LoadBalancingConfig()
        load_balancer = LoadBalancer(config)

        # Add some test servers
        server1 = ServerConfig(
            id="server1",
            host="localhost",
            port=8001,
            protocol=ServerType.HTTP,
            weight=1
        )

        server2 = ServerConfig(
            id="server2",
            host="localhost",
            port=8002,
            protocol=ServerType.HTTP,
            weight=2
        )

        load_balancer.add_server(server1)
        load_balancer.add_server(server2)

        await load_balancer.initialize()

        print("Load balancer stats:", load_balancer.get_stats())

        await load_balancer.shutdown()

    asyncio.run(main())