#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure - Intelligent DNS Routing and Failover
Provides intelligent DNS routing, geographic load balancing, and automatic failover
"""

import asyncio
import json
import logging
import time
import socket
import random
import ipaddress
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from urllib.parse import urlparse
import aiohttp
import aiofiles
import dns.resolver
import dns.message
import dns.rdatatype
import dns.rdataclass
from geoip2 import database
from geoip2.errors import AddressNotFoundError

class DNSProvider(Enum):
    """Supported DNS providers"""
    ROUTE53 = "route53"
    CLOUDFLARE = "cloudflare"
    GOOGLE_CLOUD_DNS = "google_cloud_dns"
    AZURE_DNS = "azure_dns"
    POWERDNS = "powerdns"
    BIND = "bind"

class RoutingPolicy(Enum):
    """DNS routing policies"""
    SIMPLE = "simple"
    WEIGHTED = "weighted"
    LATENCY = "latency"
    GEOGRAPHIC = "geographic"
    FAILOVER = "failover"
    MULTIVALUE = "multivalue"

class HealthCheckType(Enum):
    """Health check types"""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    ICMP = "icmp"

class RecordType(Enum):
    """DNS record types"""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    SRV = "SRV"
    PTR = "PTR"

@dataclass
class DNSRecord:
    """DNS record configuration"""
    name: str
    record_type: RecordType
    value: str
    ttl: int
    weight: int = 1
    health_check_enabled: bool = False
    health_check_path: str = "/"
    health_check_port: int = 80
    region: str = "global"
    country_codes: List[str] = None
    failover_priority: int = 1
    created_at: float
    updated_at: float

@dataclass
class DNSZone:
    """DNS zone configuration"""
    name: str
    provider: DNSProvider
    routing_policy: RoutingPolicy
    nameservers: List[str]
    records: List[DNSRecord]
    health_check_enabled: bool
    health_check_interval: int
    failover_enabled: bool
    geo_routing_enabled: bool
    created_at: float
    updated_at: float

@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    target: str
    check_type: HealthCheckType
    path: str
    port: int
    timeout: int
    interval: int
    failure_threshold: int
    success_threshold: int
    enabled: bool

@dataclass
class GeoTarget:
    """Geographic target configuration"""
    country_code: str
    region: str
    endpoint: str
    weight: int
    health_check: str
    failover_priority: int

@dataclass
class RoutingRule:
    """DNS routing rule"""
    name: str
    condition: Dict[str, Any]
    targets: List[GeoTarget]
    default_target: Optional[str]
    weight: int
    enabled: bool

@dataclass
class DNSQuery:
    """DNS query information"""
    client_ip: str
    query_name: str
    query_type: str
    client_country: str
    client_region: str
    timestamp: float
    response: Optional[str]
    response_time: float

class GlobalDNSManager:
    """Global intelligent DNS management system"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.zones: Dict[str, DNSZone] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.routing_rules: Dict[str, RoutingRule] = {}
        self.query_history: List[DNSQuery] = []
        self.health_status: Dict[str, bool] = {}
        self.session = None
        self.geoip_reader = None

        # DNS provider clients
        self.route53_client = None
        self.cloudflare_client = None
        self.google_dns_client = None

        # Performance metrics
        self.query_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_response_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # DNS cache
        self.dns_cache: Dict[str, Tuple[str, float]] = {}  # (response, timestamp)

        # Initialize configuration
        if config_path:
            self._load_configuration(config_path)
        else:
            self._initialize_default_configuration()

    def _initialize_default_configuration(self):
        """Initialize default DNS configuration"""
        # Default zones
        default_zones = [
            DNSZone(
                name="dmlogn8n.com",
                provider=DNSProvider.ROUTE53,
                routing_policy=RoutingPolicy.LATENCY,
                nameservers=["ns-1.dmlogn8n.com", "ns-2.dmlogn8n.com"],
                records=[
                    DNSRecord(
                        name="www",
                        record_type=RecordType.A,
                        value="1.2.3.4",
                        ttl=300,
                        weight=1,
                        health_check_enabled=True,
                        health_check_path="/health",
                        health_check_port=80,
                        region="us-east-1",
                        country_codes=["US", "CA"],
                        failover_priority=1,
                        created_at=time.time(),
                        updated_at=time.time()
                    ),
                    DNSRecord(
                        name="www",
                        record_type=RecordType.A,
                        value="5.6.7.8",
                        ttl=300,
                        weight=1,
                        health_check_enabled=True,
                        health_check_path="/health",
                        health_check_port=80,
                        region="eu-west-1",
                        country_codes=["GB", "DE", "FR"],
                        failover_priority=2,
                        created_at=time.time(),
                        updated_at=time.time()
                    ),
                    DNSRecord(
                        name="www",
                        record_type=RecordType.A,
                        value="9.10.11.12",
                        ttl=300,
                        weight=1,
                        health_check_enabled=True,
                        health_check_path="/health",
                        health_check_port=80,
                        region="ap-southeast-1",
                        country_codes=["SG", "MY", "TH"],
                        failover_priority=3,
                        created_at=time.time(),
                        updated_at=time.time()
                    )
                ],
                health_check_enabled=True,
                health_check_interval=30,
                failover_enabled=True,
                geo_routing_enabled=True,
                created_at=time.time(),
                updated_at=time.time()
            ),
            DNSZone(
                name="api.dmlogn8n.com",
                provider=DNSProvider.CLOUDFLARE,
                routing_policy=RoutingPolicy.FAILOVER,
                nameservers=["ns-1.cloudflare.com", "ns-2.cloudflare.com"],
                records=[
                    DNSRecord(
                        name="@",
                        record_type=RecordType.A,
                        value="13.14.15.16",
                        ttl=60,
                        weight=1,
                        health_check_enabled=True,
                        health_check_path="/api/health",
                        health_check_port=443,
                        region="us-east-1",
                        failover_priority=1,
                        created_at=time.time(),
                        updated_at=time.time()
                    ),
                    DNSRecord(
                        name="@",
                        record_type=RecordType.A,
                        value="17.18.19.20",
                        ttl=60,
                        weight=1,
                        health_check_enabled=True,
                        health_check_path="/api/health",
                        health_check_port=443,
                        region="eu-west-1",
                        failover_priority=2,
                        created_at=time.time(),
                        updated_at=time.time()
                    )
                ],
                health_check_enabled=True,
                health_check_interval=60,
                failover_enabled=True,
                geo_routing_enabled=False,
                created_at=time.time(),
                updated_at=time.time()
            )
        ]

        for zone in default_zones:
            self.zones[zone.name] = zone

        # Default health checks
        default_health_checks = [
            HealthCheck(
                name="www-us-east-health",
                target="1.2.3.4",
                check_type=HealthCheckType.HTTP,
                path="/health",
                port=80,
                timeout=5,
                interval=30,
                failure_threshold=3,
                success_threshold=2,
                enabled=True
            ),
            HealthCheck(
                name="www-eu-west-health",
                target="5.6.7.8",
                check_type=HealthCheckType.HTTP,
                path="/health",
                port=80,
                timeout=5,
                interval=30,
                failure_threshold=3,
                success_threshold=2,
                enabled=True
            ),
            HealthCheck(
                name="www-ap-southeast-health",
                target="9.10.11.12",
                check_type=HealthCheckType.HTTP,
                path="/health",
                port=80,
                timeout=5,
                interval=30,
                failure_threshold=3,
                success_threshold=2,
                enabled=True
            )
        ]

        for health_check in default_health_checks:
            self.health_checks[health_check.name] = health_check

        # Initialize health status
        for health_check_name in self.health_checks:
            self.health_status[health_check_name] = True

    async def initialize(self):
        """Initialize the DNS manager"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Initialize GeoIP database
        try:
            self.geoip_reader = database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
        except Exception as e:
            self.logger.warning(f"Could not load GeoIP database: {e}")

        # Initialize DNS provider clients
        await self._initialize_provider_clients()

        # Start monitoring loops
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._dns_cache_cleanup_loop())
        asyncio.create_task(self._metrics_collection_loop())

    async def _initialize_provider_clients(self):
        """Initialize DNS provider clients"""
        try:
            # Initialize Route53 client
            # In production, these would use proper AWS credentials
            # import boto3
            # self.route53_client = boto3.client('route53')

            # Initialize Cloudflare client
            # import CloudFlare
            # self.cloudflare_client = CloudFlare.CloudFlare(email=..., key=...)

            # Initialize Google Cloud DNS client
            # from google.cloud import dns
            # self.google_dns_client = dns.Client()

            self.logger.info("DNS provider clients initialized")

        except Exception as e:
            self.logger.error(f"Error initializing DNS provider clients: {e}")

    async def resolve_query(self, query_name: str, client_ip: str,
                          record_type: str = "A") -> Optional[str]:
        """Resolve DNS query with intelligent routing"""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"{query_name}:{client_ip}:{record_type}"
            if cache_key in self.dns_cache:
                response, timestamp = self.dns_cache[cache_key]
                if time.time() - timestamp < 300:  # 5 minute cache
                    self.query_stats['cache_hits'] += 1
                    return response

            self.query_stats['cache_misses'] += 1

            # Get client location
            client_country, client_region = await self._get_client_location(client_ip)

            # Find matching zone
            zone = self._find_zone_for_query(query_name)
            if not zone:
                self.query_stats['failed_queries'] += 1
                return None

            # Resolve based on routing policy
            if zone.routing_policy == RoutingPolicy.SIMPLE:
                response = await self._resolve_simple(zone, query_name, record_type)
            elif zone.routing_policy == RoutingPolicy.WEIGHTED:
                response = await self._resolve_weighted(zone, query_name, record_type)
            elif zone.routing_policy == RoutingPolicy.LATENCY:
                response = await self._resolve_latency(zone, query_name, client_ip, record_type)
            elif zone.routing_policy == RoutingPolicy.GEOGRAPHIC:
                response = await self._resolve_geographic(zone, query_name, client_country, record_type)
            elif zone.routing_policy == RoutingPolicy.FAILOVER:
                response = await self._resolve_failover(zone, query_name, record_type)
            elif zone.routing_policy == RoutingPolicy.MULTIVALUE:
                response = await self._resolve_multivalue(zone, query_name, record_type)
            else:
                response = await self._resolve_simple(zone, query_name, record_type)

            # Cache response
            if response:
                self.dns_cache[cache_key] = (response, time.time())

            # Record query
            query_time = time.time() - start_time
            self._record_query(query_name, client_ip, record_type, client_country, client_region, response, query_time)

            # Update stats
            self.query_stats['total_queries'] += 1
            if response:
                self.query_stats['successful_queries'] += 1
            else:
                self.query_stats['failed_queries'] += 1

            # Update average response time
            self.query_stats['average_response_time'] = (
                (self.query_stats['average_response_time'] * (self.query_stats['total_queries'] - 1) + query_time) /
                self.query_stats['total_queries']
            )

            return response

        except Exception as e:
            self.logger.error(f"Error resolving DNS query {query_name}: {e}")
            self.query_stats['failed_queries'] += 1
            return None

    async def _get_client_location(self, client_ip: str) -> Tuple[str, str]:
        """Get client location from IP address"""
        try:
            if self.geoip_reader:
                response = self.geoip_reader.country(client_ip)
                return response.country.iso_code, response.continent.code
            else:
                # Fallback to IP geolocation API
                async with self.session.get(f"http://ip-api.com/json/{client_ip}") as api_response:
                    if api_response.status == 200:
                        data = await api_response.json()
                        return data.get('countryCode', 'US'), data.get('continent', 'NA')
        except Exception as e:
            self.logger.error(f"Error getting client location for {client_ip}: {e}")

        return "US", "NA"  # Default to US/North America

    def _find_zone_for_query(self, query_name: str) -> Optional[DNSZone]:
        """Find the DNS zone that handles this query"""
        for zone in self.zones.values():
            if query_name.endswith(zone.name):
                return zone
        return None

    async def _resolve_simple(self, zone: DNSZone, query_name: str,
                            record_type: str) -> Optional[str]:
        """Simple DNS resolution"""
        try:
            # Find first matching record
            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        return record.value
            return None
        except Exception as e:
            self.logger.error(f"Error in simple resolution: {e}")
            return None

    async def _resolve_weighted(self, zone: DNSZone, query_name: str,
                              record_type: str) -> Optional[str]:
        """Weighted DNS resolution"""
        try:
            matching_records = []
            total_weight = 0

            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        matching_records.append(record)
                        total_weight += record.weight

            if not matching_records:
                return None

            # Select record based on weight
            random_weight = random.uniform(0, total_weight)
            current_weight = 0

            for record in matching_records:
                current_weight += record.weight
                if random_weight <= current_weight:
                    return record.value

            return matching_records[0].value

        except Exception as e:
            self.logger.error(f"Error in weighted resolution: {e}")
            return None

    async def _resolve_latency(self, zone: DNSZone, query_name: str,
                             client_ip: str, record_type: str) -> Optional[str]:
        """Latency-based DNS resolution"""
        try:
            matching_records = []

            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        # Estimate latency based on geography (simplified)
                        latency = await self._estimate_latency(client_ip, record.value, record.region)
                        matching_records.append((record, latency))

            if not matching_records:
                return None

            # Return record with lowest latency
            matching_records.sort(key=lambda x: x[1])
            return matching_records[0][0].value

        except Exception as e:
            self.logger.error(f"Error in latency-based resolution: {e}")
            return None

    async def _resolve_geographic(self, zone: DNSZone, query_name: str,
                                client_country: str, record_type: str) -> Optional[str]:
        """Geographic DNS resolution"""
        try:
            # First try to find exact country match
            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        if record.country_codes and client_country in record.country_codes:
                            return record.value

            # Fallback to regional matching
            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        return record.value

            return None

        except Exception as e:
            self.logger.error(f"Error in geographic resolution: {e}")
            return None

    async def _resolve_failover(self, zone: DNSZone, query_name: str,
                              record_type: str) -> Optional[str]:
        """Failover DNS resolution"""
        try:
            # Sort records by failover priority
            matching_records = [
                record for record in zone.records
                if self._record_matches_query(record, query_name, record_type)
            ]

            matching_records.sort(key=lambda r: r.failover_priority)

            for record in matching_records:
                if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                    return record.value

            return None

        except Exception as e:
            self.logger.error(f"Error in failover resolution: {e}")
            return None

    async def _resolve_multivalue(self, zone: DNSZone, query_name: str,
                                record_type: str) -> Optional[str]:
        """Multi-value DNS resolution"""
        try:
            matching_records = []

            for record in zone.records:
                if self._record_matches_query(record, query_name, record_type):
                    if not record.health_check_enabled or self.health_status.get(self._get_health_check_name(record), True):
                        matching_records.append(record.value)

            if not matching_records:
                return None

            # Return all healthy records (simplified - would return multiple values in real DNS)
            return random.choice(matching_records)

        except Exception as e:
            self.logger.error(f"Error in multivalue resolution: {e}")
            return None

    def _record_matches_query(self, record: DNSRecord, query_name: str,
                            record_type: str) -> bool:
        """Check if a DNS record matches the query"""
        # Extract record name from query
        if query_name.endswith('.'):
            query_name = query_name[:-1]

        # Check record type
        if record.record_type.value != record_type:
            return False

        # Check name match
        if record.name == "@":
            return query_name == record.zone_name
        else:
            expected_name = f"{record.name}.{record.zone_name}"
            return query_name == expected_name or query_name == f"{record.name}"

    def _get_health_check_name(self, record: DNSRecord) -> str:
        """Get health check name for a record"""
        return f"{record.name}-{record.region}-health"

    async def _estimate_latency(self, client_ip: str, target_ip: str,
                              target_region: str) -> float:
        """Estimate network latency (simplified)"""
        try:
            # In production, use actual network measurements or latency database
            # For now, use geographic distance as proxy

            # Get client location coordinates (simplified)
            client_lat, client_lon = self._get_ip_coordinates(client_ip)
            target_lat, target_lon = self._get_region_coordinates(target_region)

            # Calculate distance
            distance = ((target_lat - client_lat) ** 2 + (target_lon - client_lon) ** 2) ** 0.5

            # Estimate latency (rough approximation)
            latency_ms = distance * 10  # Simplified calculation

            return latency_ms

        except Exception as e:
            self.logger.error(f"Error estimating latency: {e}")
            return 100.0  # Default latency

    def _get_ip_coordinates(self, ip: str) -> Tuple[float, float]:
        """Get approximate coordinates for an IP (simplified)"""
        # In production, use proper GeoIP database
        ip_ranges = {
            'US': (39.8283, -98.5795),
            'GB': (55.3781, -3.4360),
            'DE': (51.1657, 10.4515),
            'SG': (1.3521, 103.8198),
            'JP': (36.2048, 138.2529)
        }

        # Simplified IP to country mapping
        if ip.startswith('8.') or ip.startswith('1.') or ip.startswith('208.'):
            return ip_ranges['US']
        elif ip.startswith('5.') or ip.startswith('93.'):
            return ip_ranges['DE']
        elif ip.startswith('103.'):
            return ip_ranges['SG']
        else:
            return ip_ranges['US']  # Default

    def _get_region_coordinates(self, region: str) -> Tuple[float, float]:
        """Get coordinates for AWS regions"""
        region_coords = {
            'us-east-1': (39.0458, -77.6413),
            'us-west-2': (45.5152, -122.6784),
            'eu-west-1': (53.3498, -6.2603),
            'eu-central-1': (52.5200, 13.4050),
            'ap-southeast-1': (1.3521, 103.8198),
            'ap-northeast-1': (35.6762, 139.6503)
        }
        return region_coords.get(region, (0, 0))

    def _record_query(self, query_name: str, client_ip: str, record_type: str,
                     client_country: str, client_region: str, response: Optional[str],
                     response_time: float):
        """Record DNS query for analytics"""
        query = DNSQuery(
            client_ip=client_ip,
            query_name=query_name,
            query_type=record_type,
            client_country=client_country,
            client_region=client_region,
            timestamp=time.time(),
            response=response,
            response_time=response_time
        )

        self.query_history.append(query)

        # Keep only recent queries (last 10000)
        if len(self.query_history) > 10000:
            self.query_history = self.query_history[-10000:]

    async def create_zone(self, zone: DNSZone) -> bool:
        """Create a new DNS zone"""
        try:
            # Create zone with provider
            if zone.provider == DNSProvider.ROUTE53:
                success = await self._create_route53_zone(zone)
            elif zone.provider == DNSProvider.CLOUDFLARE:
                success = await self._create_cloudflare_zone(zone)
            else:
                success = await self._create_generic_zone(zone)

            if success:
                self.zones[zone.name] = zone
                self.logger.info(f"Created DNS zone: {zone.name}")
                return True
            else:
                self.logger.error(f"Failed to create DNS zone: {zone.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating DNS zone {zone.name}: {e}")
            return False

    async def _create_route53_zone(self, zone: DNSZone) -> bool:
        """Create Route53 hosted zone"""
        try:
            # Simulate Route53 API call
            # In production: response = self.route53_client.create_hosted_zone(...)

            # Create records
            for record in zone.records:
                await self._create_route53_record(zone, record)

            return True

        except Exception as e:
            self.logger.error(f"Error creating Route53 zone: {e}")
            return False

    async def _create_cloudflare_zone(self, zone: DNSZone) -> bool:
        """Create Cloudflare zone"""
        try:
            # Simulate Cloudflare API call
            # In production: zone_data = self.cloudflare_client.zones.post(...)

            # Create records
            for record in zone.records:
                await self._create_cloudflare_record(zone, record)

            return True

        except Exception as e:
            self.logger.error(f"Error creating Cloudflare zone: {e}")
            return False

    async def _create_generic_zone(self, zone: DNSZone) -> bool:
        """Create zone for generic DNS provider"""
        return True

    async def _create_route53_record(self, zone: DNSZone, record: DNSRecord):
        """Create Route53 record"""
        # Simulate record creation
        pass

    async def _create_cloudflare_record(self, zone: DNSZone, record: DNSRecord):
        """Create Cloudflare record"""
        # Simulate record creation
        pass

    async def update_record(self, zone_name: str, record_name: str,
                          new_value: str) -> bool:
        """Update a DNS record"""
        try:
            if zone_name not in self.zones:
                return False

            zone = self.zones[zone_name]

            for record in zone.records:
                if record.name == record_name:
                    old_value = record.value
                    record.value = new_value
                    record.updated_at = time.time()

                    # Update with provider
                    await self._update_record_with_provider(zone, record)

                    self.logger.info(f"Updated DNS record {record_name} in zone {zone_name}: {old_value} -> {new_value}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error updating DNS record {record_name} in zone {zone_name}: {e}")
            return False

    async def _update_record_with_provider(self, zone: DNSZone, record: DNSRecord):
        """Update record with DNS provider"""
        try:
            if zone.provider == DNSProvider.ROUTE53:
                await self._update_route53_record(zone, record)
            elif zone.provider == DNSProvider.CLOUDFLARE:
                await self._update_cloudflare_record(zone, record)

        except Exception as e:
            self.logger.error(f"Error updating record with provider: {e}")

    async def _update_route53_record(self, zone: DNSZone, record: DNSRecord):
        """Update Route53 record"""
        # Simulate record update
        pass

    async def _update_cloudflare_record(self, zone: DNSZone, record: DNSRecord):
        """Update Cloudflare record"""
        # Simulate record update
        pass

    async def _health_check_loop(self):
        """Continuous health checking of DNS targets"""
        while True:
            try:
                for health_check_name, health_check in self.health_checks.items():
                    if health_check.enabled:
                        is_healthy = await self._perform_health_check(health_check)
                        self.health_status[health_check_name] = is_healthy

                        if not is_healthy:
                            self.logger.warning(f"Health check failed: {health_check_name}")

                await asyncio.sleep(health_check.interval)  # Check based on configured interval

            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)

    async def _perform_health_check(self, health_check: HealthCheck) -> bool:
        """Perform a health check"""
        try:
            if health_check.check_type == HealthCheckType.HTTP:
                return await self._http_health_check(health_check)
            elif health_check.check_type == HealthCheckType.HTTPS:
                return await self._https_health_check(health_check)
            elif health_check.check_type == HealthCheckType.TCP:
                return await self._tcp_health_check(health_check)
            elif health_check.check_type == HealthCheckType.ICMP:
                return await self._icmp_health_check(health_check)

            return False

        except Exception as e:
            self.logger.error(f"Error performing health check {health_check.name}: {e}")
            return False

    async def _http_health_check(self, health_check: HealthCheck) -> bool:
        """Perform HTTP health check"""
        try:
            url = f"http://{health_check.target}:{health_check.port}{health_check.path}"
            async with self.session.get(url, timeout=health_check.timeout) as response:
                return response.status == 200
        except Exception:
            return False

    async def _https_health_check(self, health_check: HealthCheck) -> bool:
        """Perform HTTPS health check"""
        try:
            url = f"https://{health_check.target}:{health_check.port}{health_check.path}"
            async with self.session.get(url, timeout=health_check.timeout) as response:
                return response.status == 200
        except Exception:
            return False

    async def _tcp_health_check(self, health_check: HealthCheck) -> bool:
        """Perform TCP health check"""
        try:
            # Simulate TCP health check
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(health_check.target, health_check.port),
                timeout=health_check.timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _icmp_health_check(self, health_check: HealthCheck) -> bool:
        """Perform ICMP health check (ping)"""
        try:
            # Simulate ICMP ping
            # In production, use proper ping implementation
            return True
        except Exception:
            return False

    async def _dns_cache_cleanup_loop(self):
        """Clean up expired DNS cache entries"""
        while True:
            try:
                current_time = time.time()
                expired_keys = [
                    key for key, (response, timestamp) in self.dns_cache.items()
                    if current_time - timestamp > 300  # 5 minutes
                ]

                for key in expired_keys:
                    del self.dns_cache[key]

                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired DNS cache entries")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in DNS cache cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _metrics_collection_loop(self):
        """Collect DNS performance metrics"""
        while True:
            try:
                # Calculate additional metrics
                await self._collect_advanced_metrics()
                await asyncio.sleep(300)  # Collect every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(300)

    async def _collect_advanced_metrics(self):
        """Collect advanced DNS metrics"""
        try:
            # Query distribution by country
            country_distribution = {}
            for query in self.query_history[-1000:]:  # Last 1000 queries
                country = query.client_country
                country_distribution[country] = country_distribution.get(country, 0) + 1

            # Response time distribution
            response_times = [q.response_time for q in self.query_history[-1000:] if q.response_time]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                self.query_stats['average_response_time'] = avg_response_time

        except Exception as e:
            self.logger.error(f"Error collecting advanced metrics: {e}")

    async def get_dns_metrics(self) -> Dict[str, Any]:
        """Get DNS performance and usage metrics"""
        metrics = {
            'query_stats': self.query_stats.copy(),
            'zones': {
                'total': len(self.zones),
                'by_provider': {},
                'by_routing_policy': {}
            },
            'health_checks': {
                'total': len(self.health_checks),
                'healthy': sum(1 for status in self.health_status.values() if status),
                'unhealthy': sum(1 for status in self.health_status.values() if not status)
            },
            'cache': {
                'entries': len(self.dns_cache),
                'hit_rate': self.query_stats['cache_hits'] / max(1, self.query_stats['cache_hits'] + self.query_stats['cache_misses']) * 100
            },
            'top_queries': [],
            'geographic_distribution': {}
        }

        # Zone distribution
        for zone in self.zones.values():
            provider = zone.provider.value
            policy = zone.routing_policy.value

            metrics['zones']['by_provider'][provider] = metrics['zones']['by_provider'].get(provider, 0) + 1
            metrics['zones']['by_routing_policy'][policy] = metrics['zones']['by_routing_policy'].get(policy, 0) + 1

        # Top queries
        query_counts = {}
        for query in self.query_history[-1000:]:
            query_name = query.query_name
            query_counts[query_name] = query_counts.get(query_name, 0) + 1

        metrics['top_queries'] = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Geographic distribution
        country_counts = {}
        for query in self.query_history[-1000:]:
            country = query.client_country
            country_counts[country] = country_counts.get(country, 0) + 1

        metrics['geographic_distribution'] = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return metrics

    def _load_configuration(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load zones
            if 'zones' in config:
                for zone_config in config['zones']:
                    zone_config['provider'] = DNSProvider(zone_config['provider'])
                    zone_config['routing_policy'] = RoutingPolicy(zone_config['routing_policy'])
                    zone_config['records'] = [
                        DNSRecord(**record_config) for record_config in zone_config['records']
                    ]
                    zone = DNSZone(**zone_config)
                    self.zones[zone.name] = zone

            # Load health checks
            if 'health_checks' in config:
                for health_check_config in config['health_checks']:
                    health_check_config['check_type'] = HealthCheckType(health_check_config['check_type'])
                    health_check = HealthCheck(**health_check_config)
                    self.health_checks[health_check.name] = health_check

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

    def save_configuration(self, config_path: str):
        """Save current configuration to file"""
        config = {
            'zones': [
                {
                    **asdict(zone),
                    'provider': zone.provider.value,
                    'routing_policy': zone.routing_policy.value,
                    'records': [asdict(record) for record in zone.records]
                }
                for zone in self.zones.values()
            ],
            'health_checks': [
                {
                    **asdict(health_check),
                    'check_type': health_check.check_type.value
                }
                for health_check in self.health_checks.values()
            ]
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

        if self.geoip_reader:
            self.geoip_reader.close()


async def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)

    dns_manager = GlobalDNSManager()
    await dns_manager.initialize()

    # Test DNS resolution
    test_queries = [
        ("www.dmlogn8n.com", "8.8.8.8"),
        ("www.dmlogn8n.com", "93.184.216.34"),  # European IP
        ("www.dmlogn8n.com", "103.21.244.0"),   # Singapore IP
        ("api.dmlogn8n.com", "8.8.8.8")
    ]

    print("Testing DNS resolution:")
    for query_name, client_ip in test_queries:
        result = await dns_manager.resolve_query(query_name, client_ip)
        print(f"  {query_name} from {client_ip} -> {result}")

    # Get metrics
    metrics = await dns_manager.get_dns_metrics()
    print(f"\nDNS Metrics:")
    print(f"  Total Queries: {metrics['query_stats']['total_queries']}")
    print(f"  Success Rate: {metrics['query_stats']['successful_queries'] / max(1, metrics['query_stats']['total_queries']) * 100:.1f}%")
    print(f"  Average Response Time: {metrics['query_stats']['average_response_time']:.3f}s")
    print(f"  Cache Hit Rate: {metrics['cache']['hit_rate']:.1f}%")
    print(f"  Healthy Targets: {metrics['health_checks']['healthy']}/{metrics['health_checks']['total']}")

    await dns_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())