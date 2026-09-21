#!/usr/bin/env python3
"""
Global Load Balancer with Intelligent Traffic Routing
Multi-cloud load balancing with geographic optimization and health monitoring
"""

import asyncio
import json
import logging
import aiohttp
import numpy as np
import geoip2.database
import maxminddb
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import boto3
from collections import defaultdict
import hashlib
import random
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

class RoutingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    GEOGRAPHIC = "geographic"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"

@dataclass
class BackendServer:
    """Backend server configuration"""
    id: str
    hostname: str
    ip_address: str
    port: int
    region: str
    country: str
    city: str
    weight: float
    max_connections: int
    current_connections: int
    health_status: HealthStatus
    response_time: float
    throughput: float
    error_rate: float
    last_health_check: datetime
    ssl_enabled: bool
    ssl_certificate: str
    capabilities: List[str]

@dataclass
class TrafficMetrics:
    """Traffic routing metrics"""
    timestamp: datetime
    source_ip: str
    source_country: str
    target_server: str
    response_time: float
    status_code: int
    bytes_sent: int
    bytes_received: int
    routing_strategy: str
    request_type: str

@dataclass
class GeoLocation:
    """Geographic location data"""
    country: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    asn: str
    organization: str

class HealthChecker:
    """Health checking for backend servers"""

    def __init__(self, config: Dict):
        self.config = config
        self.check_interval = config.get('health_check_interval', 30)
        self.timeout = config.get('health_check_timeout', 5)
        self.retries = config.get('health_check_retries', 3)
        self.unhealthy_threshold = config.get('unhealthy_threshold', 3)
        self.healthy_threshold = config.get('healthy_threshold', 2)

        self.health_status = defaultdict(dict)
        self.consecutive_failures = defaultdict(int)
        self.consecutive_successes = defaultdict(int)

    async def check_server_health(self, server: BackendServer) -> HealthStatus:
        """Perform health check on a server"""
        url = f"http{'s' if server.ssl_enabled else ''}://{server.hostname}:{server.port}/health"

        for attempt in range(self.retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    start_time = asyncio.get_event_loop().time()
                    async with session.get(url) as response:
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                        if response.status == 200:
                            # Parse health check response
                            try:
                                health_data = await response.json()
                                if health_data.get('status') == 'healthy':
                                    self.consecutive_successes[server.id] += 1
                                    self.consecutive_failures[server.id] = 0

                                    if self.consecutive_successes[server.id] >= self.healthy_threshold:
                                        return HealthStatus.HEALTHY
                                    else:
                                        return HealthStatus.DEGRADED
                                else:
                                    raise Exception(f"Health check returned unhealthy status: {health_data.get('status')}")
                            except:
                                # Simple HTTP 200 response is good enough
                                self.consecutive_successes[server.id] += 1
                                self.consecutive_failures[server.id] = 0

                                if self.consecutive_successes[server.id] >= self.healthy_threshold:
                                    return HealthStatus.HEALTHY
                                else:
                                    return HealthStatus.DEGRADED
                        else:
                            raise Exception(f"HTTP {response.status}")

            except Exception as e:
                logger.warning(f"Health check failed for {server.id} (attempt {attempt + 1}): {e}")
                self.consecutive_failures[server.id] += 1
                self.consecutive_successes[server.id] = 0

                if self.consecutive_failures[server.id] >= self.unhealthy_threshold:
                    return HealthStatus.UNHEALTHY

        return HealthStatus.UNHEALTHY

    async def run_health_checks(self, servers: List[BackendServer]) -> Dict[str, HealthStatus]:
        """Run health checks on all servers"""
        tasks = [self.check_server_health(server) for server in servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_status = {}
        for server, result in zip(servers, results):
            if isinstance(result, Exception):
                health_status[server.id] = HealthStatus.UNHEALTHY
            else:
                health_status[server.id] = result

        return health_status

class GeoIPResolver:
    """GeoIP location resolver"""

    def __init__(self, geoip_db_path: str = "data/GeoLite2-City.mmdb"):
        self.geoip_db_path = geoip_db_path
        try:
            self.reader = geoip2.database.Reader(geoip_db_path)
        except FileNotFoundError:
            logger.warning(f"GeoIP database not found at {geoip_db_path}")
            self.reader = None

    def resolve_location(self, ip_address: str) -> Optional[GeoLocation]:
        """Resolve IP address to geographic location"""
        if not self.reader:
            return None

        try:
            response = self.reader.city(ip_address)
            return GeoLocation(
                country=response.country.iso_code or "Unknown",
                region=response.subdivisions.most_specific.iso_code or "Unknown",
                city=response.city.name or "Unknown",
                latitude=response.location.latitude or 0.0,
                longitude=response.location.longitude or 0.0,
                timezone=response.location.time_zone or "UTC",
                asn=response.traits.autonomous_system_number or "Unknown",
                organization=response.traits.autonomous_system_organization or "Unknown"
            )
        except Exception as e:
            logger.warning(f"Failed to resolve location for {ip_address}: {e}")
            return None

    def calculate_distance(self, loc1: GeoLocation, loc2: GeoLocation) -> float:
        """Calculate distance between two geographic locations (in km)"""
        if not loc1 or not loc2:
            return float('inf')

        # Haversine formula
        R = 6371  # Earth radius in km

        lat1, lon1 = np.radians(loc1.latitude), np.radians(loc1.longitude)
        lat2, lon2 = np.radians(loc2.latitude), np.radians(loc2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))

        return R * c

class LoadBalancingAlgorithms:
    """Load balancing algorithms implementation"""

    @staticmethod
    def round_robin(servers: List[BackendServer], request_data: Dict) -> Optional[BackendServer]:
        """Round-robin load balancing"""
        if not servers:
            return None

        # Get current index from request data
        current_index = request_data.get('round_robin_index', 0)
        server = servers[current_index % len(servers)]
        request_data['round_robin_index'] = current_index + 1

        return server

    @staticmethod
    def least_connections(servers: List[BackendServer], request_data: Dict) -> Optional[BackendServer]:
        """Least connections load balancing"""
        if not servers:
            return None

        return min(servers, key=lambda s: s.current_connections)

    @staticmethod
    def weighted_round_robin(servers: List[BackendServer], request_data: Dict) -> Optional[BackendServer]:
        """Weighted round-robin load balancing"""
        if not servers:
            return None

        weights = [s.weight for s in servers]
        total_weight = sum(weights)

        if total_weight == 0:
            return servers[0]

        # Get current weight from request data
        current_weight = request_data.get('weighted_current_weight', 0)
        best_server = None
        best_weight_diff = float('inf')

        for i, server in enumerate(servers):
            weight_diff = weights[i] - current_weight
            if weight_diff > 0 and weight_diff < best_weight_diff:
                best_weight_diff = weight_diff
                best_server = server

        if best_server is None:
            # Start new round
            best_server = servers[0]
            current_weight = 0

        current_weight += 1
        request_data['weighted_current_weight'] = current_weight

        return best_server

    @staticmethod
    def geographic(servers: List[BackendServer], request_data: Dict,
                   geo_resolver: GeoIPResolver) -> Optional[BackendServer]:
        """Geographic load balancing"""
        if not servers:
            return None

        client_location = request_data.get('client_location')
        if not client_location:
            return LoadBalancingAlgorithms.round_robin(servers, request_data)

        # Find servers in the same country or region
        same_country = [s for s in servers if s.country == client_location.country]
        if same_country:
            # Choose the closest server in the same country
            server_locations = [(s, GeoLocation(
                country=s.country, region=s.region, city=s.city,
                latitude=0, longitude=0, timezone="", asn="", organization=""
            )) for s in same_country]

            closest_server = min(
                server_locations,
                key=lambda x: geo_resolver.calculate_distance(client_location, x[1])
            )[0]
            return closest_server

        # Fallback to nearest server
        server_locations = [(s, GeoLocation(
            country=s.country, region=s.region, city=s.city,
            latitude=0, longitude=0, timezone="", asn="", organization=""
        )) for s in servers]

        closest_server = min(
            server_locations,
            key=lambda x: geo_resolver.calculate_distance(client_location, x[1])
        )[0]

        return closest_server

    @staticmethod
    def response_time(servers: List[BackendServer], request_data: Dict) -> Optional[BackendServer]:
        """Response time-based load balancing"""
        if not servers:
            return None

        # Filter healthy servers with recent response time data
        healthy_servers = [
            s for s in servers
            if s.health_status == HealthStatus.HEALTHY and s.response_time > 0
        ]

        if not healthy_servers:
            return LoadBalancingAlgorithms.round_robin(servers, request_data)

        return min(healthy_servers, key=lambda s: s.response_time)

    @staticmethod
    def throughput(servers: List[BackendServer], request_data: Dict) -> Optional[BackendServer]:
        """Throughput-based load balancing"""
        if not servers:
            return None

        # Filter healthy servers with throughput data
        healthy_servers = [
            s for s in servers
            if s.health_status == HealthStatus.HEALTHY and s.throughput > 0
        ]

        if not healthy_servers:
            return LoadBalancingAlgorithms.round_robin(servers, request_data)

        return max(healthy_servers, key=lambda s: s.throughput)

class GlobalLoadBalancer:
    """Main global load balancer system"""

    def __init__(self, config_path: str = "config/load_balancer_config.json"):
        self.config = self._load_config(config_path)
        self.redis_client = redis.Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            decode_responses=True
        )

        self.servers = self._load_servers()
        self.health_checker = HealthChecker(self.config.get('health_check', {}))
        self.geo_resolver = GeoIPResolver(self.config.get('geoip_db_path'))
        self.algorithms = LoadBalancingAlgorithms()

        # Routing state
        self.routing_state = {}
        self.traffic_metrics = defaultdict(list)

        # Start health checking
        asyncio.create_task(self._run_health_checks())

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'redis_host': 'localhost',
                'redis_port': 6379,
                'geoip_db_path': 'data/GeoLite2-City.mmdb',
                'default_strategy': 'least_connections',
                'health_check': {
                    'interval': 30,
                    'timeout': 5,
                    'retries': 3
                },
                'servers': []
            }

    def _load_servers(self) -> List[BackendServer]:
        """Load backend server configuration"""
        servers = []

        for server_config in self.config.get('servers', []):
            server = BackendServer(
                id=server_config['id'],
                hostname=server_config['hostname'],
                ip_address=server_config['ip_address'],
                port=server_config['port'],
                region=server_config['region'],
                country=server_config['country'],
                city=server_config['city'],
                weight=server_config.get('weight', 1.0),
                max_connections=server_config.get('max_connections', 1000),
                current_connections=0,
                health_status=HealthStatus.HEALTHY,
                response_time=0.0,
                throughput=0.0,
                error_rate=0.0,
                last_health_check=datetime.utcnow(),
                ssl_enabled=server_config.get('ssl_enabled', False),
                ssl_certificate=server_config.get('ssl_certificate', ''),
                capabilities=server_config.get('capabilities', [])
            )
            servers.append(server)

        return servers

    async def route_request(self, client_ip: str, request_path: str,
                          request_headers: Dict, strategy: Optional[str] = None) -> Optional[BackendServer]:
        """Route a request to the optimal backend server"""
        strategy = strategy or self.config.get('default_strategy', 'least_connections')

        # Resolve client location
        client_location = self.geo_resolver.resolve_location(client_ip)

        # Prepare routing data
        request_data = {
            'client_ip': client_ip,
            'client_location': client_location,
            'request_path': request_path,
            'request_headers': request_headers,
            'timestamp': datetime.utcnow()
        }

        # Initialize routing state for this client if needed
        client_key = hashlib.md5(client_ip.encode()).hexdigest()[:16]
        if client_key not in self.routing_state:
            self.routing_state[client_key] = {
                'round_robin_index': 0,
                'weighted_current_weight': 0,
                'last_server': None
            }

        request_data.update(self.routing_state[client_key])

        # Get healthy servers
        healthy_servers = [
            s for s in self.servers
            if s.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_servers:
            logger.error("No healthy servers available")
            return None

        # Apply routing algorithm
        algorithm_map = {
            'round_robin': self.algorithms.round_robin,
            'least_connections': self.algorithms.least_connections,
            'weighted_round_robin': self.algorithms.weighted_round_robin,
            'geographic': lambda servers, data: self.algorithms.geographic(servers, data, self.geo_resolver),
            'response_time': self.algorithms.response_time,
            'throughput': self.algorithms.throughput
        }

        if strategy not in algorithm_map:
            strategy = 'least_connections'

        selected_server = algorithm_map[strategy](healthy_servers, request_data)

        if selected_server:
            # Update routing state
            self.routing_state[client_key].update({
                'round_robin_index': request_data.get('round_robin_index', 0),
                'weighted_current_weight': request_data.get('weighted_current_weight', 0),
                'last_server': selected_server.id
            })

            # Increment connection count
            selected_server.current_connections += 1

            # Log routing decision
            await self._log_routing_event(client_ip, selected_server, strategy, client_location)

        return selected_server

    async def release_connection(self, server_id: str):
        """Release a connection from a server"""
        for server in self.servers:
            if server.id == server_id:
                server.current_connections = max(0, server.current_connections - 1)
                break

    async def update_server_metrics(self, server_id: str, response_time: float,
                                  status_code: int, bytes_sent: int, bytes_received: int):
        """Update server performance metrics"""
        for server in self.servers:
            if server.id == server_id:
                # Update response time (exponential moving average)
                alpha = 0.1
                server.response_time = alpha * response_time + (1 - alpha) * server.response_time

                # Update error rate
                if status_code >= 400:
                    server.error_rate = min(100, server.error_rate + 0.1)
                else:
                    server.error_rate = max(0, server.error_rate - 0.05)

                # Update throughput (bytes per second)
                if response_time > 0:
                    throughput = (bytes_sent + bytes_received) / (response_time / 1000)
                    server.throughput = 0.9 * server.throughput + 0.1 * throughput

                break

    async def _run_health_checks(self):
        """Run continuous health checks"""
        while True:
            try:
                # Run health checks
                health_results = await self.health_checker.run_health_checks(self.servers)

                # Update server health status
                for server in self.servers:
                    server.health_status = health_results.get(server.id, HealthStatus.UNHEALTHY)
                    server.last_health_check = datetime.utcnow()

                # Log unhealthy servers
                unhealthy_servers = [s for s in self.servers if s.health_status == HealthStatus.UNHEALTHY]
                if unhealthy_servers:
                    logger.warning(f"Unhealthy servers detected: {[s.id for s in unhealthy_servers]}")

                # Update Redis with health status
                health_data = {s.id: s.health_status.value for s in self.servers}
                self.redis_client.setex('server_health', 300, json.dumps(health_data))

                # Wait for next health check
                await asyncio.sleep(self.health_checker.check_interval)

            except Exception as e:
                logger.error(f"Error in health checking: {e}")
                await asyncio.sleep(10)

    async def _log_routing_event(self, client_ip: str, server: BackendServer,
                                strategy: str, location: Optional[GeoLocation]):
        """Log routing event for analytics"""
        try:
            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'client_ip': client_ip,
                'client_country': location.country if location else 'Unknown',
                'server_id': server.id,
                'server_region': server.region,
                'strategy': strategy,
                'server_connections': server.current_connections,
                'server_response_time': server.response_time
            }

            # Store in Redis
            self.redis_client.lpush('routing_events', json.dumps(event_data))
            self.redis_client.ltrim('routing_events', 0, 10000)  # Keep last 10k events

        except Exception as e:
            logger.error(f"Error logging routing event: {e}")

    async def get_load_balancing_stats(self) -> Dict:
        """Get load balancing statistics"""
        stats = {
            'total_servers': len(self.servers),
            'healthy_servers': len([s for s in self.servers if s.health_status == HealthStatus.HEALTHY]),
            'degraded_servers': len([s for s in self.servers if s.health_status == HealthStatus.DEGRADED]),
            'unhealthy_servers': len([s for s in self.servers if s.health_status == HealthStatus.UNHEALTHY]),
            'total_connections': sum(s.current_connections for s in self.servers),
            'servers': []
        }

        for server in self.servers:
            server_stats = {
                'id': server.id,
                'hostname': server.hostname,
                'region': server.region,
                'health_status': server.health_status.value,
                'current_connections': server.current_connections,
                'max_connections': server.max_connections,
                'response_time': server.response_time,
                'throughput': server.throughput,
                'error_rate': server.error_rate,
                'utilization': (server.current_connections / server.max_connections) * 100
            }
            stats['servers'].append(server_stats)

        return stats

    async def add_server(self, server_config: Dict) -> bool:
        """Add a new backend server"""
        try:
            server = BackendServer(
                id=server_config['id'],
                hostname=server_config['hostname'],
                ip_address=server_config['ip_address'],
                port=server_config['port'],
                region=server_config['region'],
                country=server_config['country'],
                city=server_config['city'],
                weight=server_config.get('weight', 1.0),
                max_connections=server_config.get('max_connections', 1000),
                current_connections=0,
                health_status=HealthStatus.HEALTHY,
                response_time=0.0,
                throughput=0.0,
                error_rate=0.0,
                last_health_check=datetime.utcnow(),
                ssl_enabled=server_config.get('ssl_enabled', False),
                ssl_certificate=server_config.get('ssl_certificate', ''),
                capabilities=server_config.get('capabilities', [])
            )

            self.servers.append(server)
            logger.info(f"Added new server: {server.id}")
            return True

        except Exception as e:
            logger.error(f"Error adding server: {e}")
            return False

    async def remove_server(self, server_id: str) -> bool:
        """Remove a backend server"""
        try:
            server = next((s for s in self.servers if s.id == server_id), None)
            if server:
                # Wait for connections to drain
                if server.current_connections > 0:
                    logger.info(f"Draining connections from {server_id}...")
                    await asyncio.sleep(30)

                self.servers.remove(server)
                logger.info(f"Removed server: {server_id}")
                return True
            else:
                logger.warning(f"Server not found: {server_id}")
                return False

        except Exception as e:
            logger.error(f"Error removing server: {e}")
            return False

    async def configure_failover(self, primary_region: str, backup_regions: List[str]) -> bool:
        """Configure automatic failover between regions"""
        try:
            failover_config = {
                'primary_region': primary_region,
                'backup_regions': backup_regions,
                'enabled': True,
                'timestamp': datetime.utcnow().isoformat()
            }

            self.redis_client.setex('failover_config', 86400, json.dumps(failover_config))
            logger.info(f"Configured failover: {primary_region} -> {backup_regions}")
            return True

        except Exception as e:
            logger.error(f"Error configuring failover: {e}")
            return False

    async def get_traffic_analytics(self, time_range: int = 3600) -> Dict:
        """Get traffic analytics for the specified time range"""
        try:
            # Get recent routing events
            events = self.redis_client.lrange('routing_events', 0, 1000)

            analytics = {
                'total_requests': len(events),
                'requests_by_country': defaultdict(int),
                'requests_by_region': defaultdict(int),
                'requests_by_server': defaultdict(int),
                'strategy_usage': defaultdict(int),
                'average_response_time': 0.0,
                'error_rate': 0.0
            }

            response_times = []
            errors = 0

            cutoff_time = datetime.utcnow() - timedelta(seconds=time_range)

            for event_data in events:
                event = json.loads(event_data)
                event_time = datetime.fromisoformat(event['timestamp'])

                if event_time >= cutoff_time:
                    analytics['requests_by_country'][event['client_country']] += 1
                    analytics['requests_by_region'][event['server_region']] += 1
                    analytics['requests_by_server'][event['server_id']] += 1
                    analytics['strategy_usage'][event['strategy']] += 1

                    if 'response_time' in event:
                        response_times.append(event['response_time'])

                    # Simple error detection (this would need real implementation)
                    if event.get('status_code', 200) >= 400:
                        errors += 1

            if response_times:
                analytics['average_response_time'] = statistics.mean(response_times)

            if analytics['total_requests'] > 0:
                analytics['error_rate'] = (errors / analytics['total_requests']) * 100

            return analytics

        except Exception as e:
            logger.error(f"Error getting traffic analytics: {e}")
            return {}

async def main():
    """Main entry point"""
    load_balancer = GlobalLoadBalancer()

    # Example usage
    while True:
        try:
            # Simulate some requests
            client_ip = "192.168.1.100"
            request_path = "/api/workflows"
            request_headers = {"User-Agent": "DMLogn8n-Client"}

            server = await load_balancer.route_request(
                client_ip, request_path, request_headers, "least_connections"
            )

            if server:
                print(f"Routed request to: {server.id} ({server.region})")

                # Simulate response
                await asyncio.sleep(0.1)
                await load_balancer.update_server_metrics(
                    server.id, 150, 200, 1024, 2048
                )
                await load_balancer.release_connection(server.id)

            await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutting down load balancer")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())