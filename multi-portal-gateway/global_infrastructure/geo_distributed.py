#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure - Geographic Distribution and Latency Optimization
Provides intelligent geographic routing and latency optimization for global deployment
"""

import asyncio
import json
import logging
import math
import random
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import aiohttp
import aiofiles
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import maxminddb
import numpy as np

class RegionType(Enum):
    """Types of geographical regions"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    EDGE = "edge"
    CACHE = "cache"

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ORACLE = "oracle"
    DIGITAL_OCEAN = "digital_ocean"

@dataclass
class GeoRegion:
    """Geographic region configuration"""
    name: str
    code: str
    latitude: float
    longitude: float
    provider: CloudProvider
    region_type: RegionType
    capacity: int
    current_load: float
    latency_threshold: float
    data_sovereignty: List[str]
    endpoint: str
    health_check_url: str
    priority: int = 1

@dataclass
class UserLocation:
    """User location information"""
    ip_address: str
    country: str
    city: str
    latitude: float
    longitude: float
    asn: str
    timezone: str

@dataclass
class LatencyMetrics:
    """Latency metrics between regions"""
    source_region: str
    target_region: str
    latency_ms: float
    bandwidth_mbps: float
    reliability: float
    last_updated: float

class GeographicDistributor:
    """Intelligent geographic distribution system"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.regions: Dict[str, GeoRegion] = {}
        self.latency_matrix: Dict[Tuple[str, str], LatencyMetrics] = {}
        self.user_cache: Dict[str, UserLocation] = {}
        self.geoip_reader = None
        self.session = None
        self.load_balancer_weights: Dict[str, float] = {}

        # Initialize regions
        self._initialize_default_regions()

        # Load configuration if provided
        if config_path:
            self._load_configuration(config_path)

    def _initialize_default_regions(self):
        """Initialize default global regions"""
        default_regions = [
            # North America
            GeoRegion(
                name="US East",
                code="us-east-1",
                latitude=40.7128,
                longitude=-74.0060,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=10000,
                current_load=0.3,
                latency_threshold=100.0,
                data_sovereignty=["US"],
                endpoint="https://us-east.dmlogn8n.com",
                health_check_url="https://us-east.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="US West",
                code="us-west-2",
                latitude=37.7749,
                longitude=-122.4194,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=8000,
                current_load=0.4,
                latency_threshold=120.0,
                data_sovereignty=["US"],
                endpoint="https://us-west.dmlogn8n.com",
                health_check_url="https://us-west.dmlogn8n.com/health",
                priority=2
            ),
            GeoRegion(
                name="Canada Central",
                code="ca-central-1",
                latitude=43.6532,
                longitude=-79.3832,
                provider=CloudProvider.AWS,
                region_type=RegionType.SECONDARY,
                capacity=5000,
                current_load=0.2,
                latency_threshold=150.0,
                data_sovereignty=["CA"],
                endpoint="https://ca-central.dmlogn8n.com",
                health_check_url="https://ca-central.dmlogn8n.com/health",
                priority=3
            ),

            # Europe
            GeoRegion(
                name="EU West",
                code="eu-west-1",
                latitude=51.5074,
                longitude=-0.1278,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=9000,
                current_load=0.35,
                latency_threshold=80.0,
                data_sovereignty=["GB", "DE", "FR"],
                endpoint="https://eu-west.dmlogn8n.com",
                health_check_url="https://eu-west.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="EU Central",
                code="eu-central-1",
                latitude=52.5200,
                longitude=13.4050,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=8500,
                current_load=0.3,
                latency_threshold=75.0,
                data_sovereignty=["DE", "AT", "CH"],
                endpoint="https://eu-central.dmlogn8n.com",
                health_check_url="https://eu-central.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="EU North",
                code="eu-north-1",
                latitude=59.3293,
                longitude=18.0686,
                provider=CloudProvider.AWS,
                region_type=RegionType.SECONDARY,
                capacity=6000,
                current_load=0.25,
                latency_threshold=100.0,
                data_sovereignty=["SE", "NO", "FI", "DK"],
                endpoint="https://eu-north.dmlogn8n.com",
                health_check_url="https://eu-north.dmlogn8n.com/health",
                priority=2
            ),

            # Asia Pacific
            GeoRegion(
                name="APAC Southeast",
                code="ap-southeast-1",
                latitude=1.3521,
                longitude=103.8198,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=7500,
                current_load=0.45,
                latency_threshold=120.0,
                data_sovereignty=["SG", "MY", "TH"],
                endpoint="https://ap-southeast.dmlogn8n.com",
                health_check_url="https://ap-southeast.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="APAC East",
                code="ap-northeast-1",
                latitude=35.6762,
                longitude=139.6503,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=8000,
                current_load=0.4,
                latency_threshold=100.0,
                data_sovereignty=["JP"],
                endpoint="https://ap-northeast.dmlogn8n.com",
                health_check_url="https://ap-northeast.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="APAC South",
                code="ap-south-1",
                latitude=19.0760,
                longitude=72.8777,
                provider=CloudProvider.AWS,
                region_type=RegionType.PRIMARY,
                capacity=7000,
                current_load=0.35,
                latency_threshold=150.0,
                data_sovereignty=["IN"],
                endpoint="https://ap-south.dmlogn8n.com",
                health_check_url="https://ap-south.dmlogn8n.com/health",
                priority=1
            ),
            GeoRegion(
                name="Australia",
                code="ap-southeast-2",
                latitude=-33.8688,
                longitude=151.2093,
                provider=CloudProvider.AWS,
                region_type=RegionType.SECONDARY,
                capacity=5500,
                current_load=0.3,
                latency_threshold=180.0,
                data_sovereignty=["AU", "NZ"],
                endpoint="https://au.dmlogn8n.com",
                health_check_url="https://au.dmlogn8n.com/health",
                priority=2
            ),

            # Latin America
            GeoRegion(
                name="South America East",
                code="sa-east-1",
                latitude=-23.5505,
                longitude=-46.6333,
                provider=CloudProvider.AWS,
                region_type=RegionType.SECONDARY,
                capacity=5000,
                current_load=0.3,
                latency_threshold=200.0,
                data_sovereignty=["BR", "AR", "UY"],
                endpoint="https://sa-east.dmlogn8n.com",
                health_check_url="https://sa-east.dmlogn8n.com/health",
                priority=2
            ),

            # Middle East & Africa
            GeoRegion(
                name="Middle East",
                code="me-south-1",
                latitude=25.2048,
                longitude=55.2708,
                provider=CloudProvider.AWS,
                region_type=RegionType.EDGE,
                capacity=4000,
                current_load=0.25,
                latency_threshold=250.0,
                data_sovereignty=["AE", "SA", "QA"],
                endpoint="https://me-south.dmlogn8n.com",
                health_check_url="https://me-south.dmlogn8n.com/health",
                priority=3
            ),
            GeoRegion(
                name="Africa",
                code="af-south-1",
                latitude=-26.2041,
                longitude=28.0473,
                provider=CloudProvider.AWS,
                region_type=RegionType.EDGE,
                capacity=3000,
                current_load=0.2,
                latency_threshold=300.0,
                data_sovereignty=["ZA", "KE", "NG"],
                endpoint="https://af-south.dmlogn8n.com",
                health_check_url="https://af-south.dmlogn8n.com/health",
                priority=3
            )
        ]

        for region in default_regions:
            self.regions[region.code] = region

    async def initialize(self):
        """Initialize the geographic distributor"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Load GeoIP database
        try:
            self.geoip_reader = maxminddb.open_database('/usr/share/GeoIP/GeoLite2-City.mmdb')
        except Exception as e:
            self.logger.warning(f"Could not load GeoIP database: {e}")

        # Initialize latency matrix
        await self._build_latency_matrix()

        # Initialize load balancer weights
        self._update_load_balancer_weights()

    async def _build_latency_matrix(self):
        """Build latency matrix between regions"""
        tasks = []
        for source_code, source_region in self.regions.items():
            for target_code, target_region in self.regions.items():
                if source_code != target_code:
                    tasks.append(self._measure_latency(source_region, target_region))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, LatencyMetrics):
                self.latency_matrix[(result.source_region, result.target_region)] = result

    async def _measure_latency(self, source: GeoRegion, target: GeoRegion) -> LatencyMetrics:
        """Measure latency between two regions"""
        try:
            # Calculate geographic distance as baseline
            distance = geodesic(
                (source.latitude, source.longitude),
                (target.latitude, target.longitude)
            ).kilometers

            # Estimate latency based on distance (speed of light in fiber ~ 2/3 c)
            baseline_latency = (distance / 200000) * 1000  # Convert to milliseconds

            # Add realistic variance based on region types
            if source.region_type == RegionType.PRIMARY and target.region_type == RegionType.PRIMARY:
                latency_multiplier = 1.2
            elif source.region_type == RegionType.EDGE or target.region_type == RegionType.EDGE:
                latency_multiplier = 1.8
            else:
                latency_multiplier = 1.5

            estimated_latency = baseline_latency * latency_multiplier

            # Add network jitter
            jitter = random.uniform(0.8, 1.2)
            final_latency = estimated_latency * jitter

            # Estimate bandwidth based on region capabilities
            bandwidth = min(source.capacity, target.capacity) / 100 * random.uniform(0.7, 1.0)

            # Calculate reliability based on region types and distance
            base_reliability = 0.99 if source.region_type == RegionType.PRIMARY else 0.95
            distance_factor = max(0.9, 1.0 - (distance / 20000))
            reliability = base_reliability * distance_factor

            return LatencyMetrics(
                source_region=source.code,
                target_region=target.code,
                latency_ms=final_latency,
                bandwidth_mbps=bandwidth,
                reliability=reliability,
                last_updated=time.time()
            )

        except Exception as e:
            self.logger.error(f"Error measuring latency between {source.code} and {target.code}: {e}")
            # Return default high-latency metrics
            return LatencyMetrics(
                source_region=source.code,
                target_region=target.code,
                latency_ms=1000.0,
                bandwidth_mbps=10.0,
                reliability=0.9,
                last_updated=time.time()
            )

    def _update_load_balancer_weights(self):
        """Update load balancer weights based on region capacity and load"""
        for region_code, region in self.regions.items():
            # Calculate available capacity
            available_capacity = region.capacity * (1 - region.current_load)

            # Consider region priority and reliability
            priority_factor = 1.0 / region.priority
            reliability_factor = 0.95 if region.region_type == RegionType.PRIMARY else 0.85

            # Calculate weight
            weight = available_capacity * priority_factor * reliability_factor
            self.load_balancer_weights[region_code] = weight

    async def get_user_location(self, ip_address: str) -> Optional[UserLocation]:
        """Get user location from IP address"""
        # Check cache first
        if ip_address in self.user_cache:
            cached_location = self.user_cache[ip_address]
            # Cache for 1 hour
            if time.time() - cached_location.last_updated < 3600:
                return cached_location

        try:
            if self.geoip_reader:
                response = self.geoip_reader.get(ip_address)
                if response:
                    location = UserLocation(
                        ip_address=ip_address,
                        country=response.get('country', {}).get('iso_code', 'Unknown'),
                        city=response.get('city', {}).get('names', {}).get('en', 'Unknown'),
                        latitude=response.get('location', {}).get('latitude', 0.0),
                        longitude=response.get('location', {}).get('longitude', 0.0),
                        asn=response.get('autonomous_system_number', ''),
                        timezone=response.get('location', {}).get('time_zone', 'UTC')
                    )
                    location.last_updated = time.time()
                    self.user_cache[ip_address] = location
                    return location
            else:
                # Fallback to external API
                async with self.session.get(f"http://ip-api.com/json/{ip_address}") as response:
                    if response.status == 200:
                        data = await response.json()
                        location = UserLocation(
                            ip_address=ip_address,
                            country=data.get('countryCode', 'Unknown'),
                            city=data.get('city', 'Unknown'),
                            latitude=data.get('lat', 0.0),
                            longitude=data.get('lon', 0.0),
                            asn=data.get('as', ''),
                            timezone=data.get('timezone', 'UTC')
                        )
                        location.last_updated = time.time()
                        self.user_cache[ip_address] = location
                        return location
        except Exception as e:
            self.logger.error(f"Error getting location for IP {ip_address}: {e}")

        return None

    async def find_optimal_region(self, user_location: UserLocation,
                                preferred_regions: List[str] = None) -> Optional[GeoRegion]:
        """Find the optimal region for a user based on location and preferences"""
        candidate_regions = []

        # Filter regions based on preferences and availability
        for region_code, region in self.regions.items():
            # Check if region has capacity
            if region.current_load >= 0.9:
                continue

            # Check data sovereignty requirements
            if user_location.country not in region.data_sovereignty:
                # For regions with strict data sovereignty, skip
                if region.region_type == RegionType.PRIMARY:
                    continue

            # Check preferred regions
            if preferred_regions and region_code not in preferred_regions:
                continue

            candidate_regions.append(region)

        if not candidate_regions:
            # Fallback to any available region
            candidate_regions = [r for r in self.regions.values() if r.current_load < 0.9]
            if not candidate_regions:
                return None

        # Calculate scores for each candidate region
        scored_regions = []
        for region in candidate_regions:
            score = await self._calculate_region_score(user_location, region)
            scored_regions.append((score, region))

        # Sort by score (higher is better) and return the best
        scored_regions.sort(key=lambda x: x[0], reverse=True)
        return scored_regions[0][1]

    async def _calculate_region_score(self, user_location: UserLocation,
                                    region: GeoRegion) -> float:
        """Calculate score for a region based on multiple factors"""
        # Distance factor (closer is better)
        distance = geodesic(
            (user_location.latitude, user_location.longitude),
            (region.latitude, region.longitude)
        ).kilometers

        # Normalize distance score (0-1, closer to 1 is better)
        max_distance = 20000  # Maximum reasonable distance
        distance_score = max(0, 1 - (distance / max_distance))

        # Load factor (less load is better)
        load_score = 1 - region.current_load

        # Capacity factor (more capacity is better)
        capacity_score = min(1, region.capacity / 10000)

        # Reliability factor
        reliability_score = 0.95 if region.region_type == RegionType.PRIMARY else 0.85

        # Priority factor
        priority_score = 1.0 / region.priority

        # Data sovereignty factor
        sovereignty_score = 1.0 if user_location.country in region.data_sovereignty else 0.7

        # Combine scores with weights
        total_score = (
            distance_score * 0.3 +
            load_score * 0.2 +
            capacity_score * 0.15 +
            reliability_score * 0.15 +
            priority_score * 0.1 +
            sovereignty_score * 0.1
        )

        return total_score

    async def route_request(self, ip_address: str,
                          preferred_regions: List[str] = None) -> Optional[str]:
        """Route a request to the optimal region"""
        user_location = await self.get_user_location(ip_address)
        if not user_location:
            # Fallback to least loaded primary region
            primary_regions = [r for r in self.regions.values()
                             if r.region_type == RegionType.PRIMARY and r.current_load < 0.9]
            if primary_regions:
                return min(primary_regions, key=lambda r: r.current_load).endpoint

        optimal_region = await self.find_optimal_region(user_location, preferred_regions)
        if optimal_region:
            # Update region load
            optimal_region.current_load = min(0.95, optimal_region.current_load + 0.001)
            self._update_load_balancer_weights()
            return optimal_region.endpoint

        return None

    async def health_check_all_regions(self) -> Dict[str, bool]:
        """Perform health checks on all regions"""
        health_status = {}
        tasks = []

        for region_code, region in self.regions.items():
            tasks.append(self._check_region_health(region))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (region_code, region) in enumerate(self.regions.items()):
            if isinstance(results[i], bool):
                health_status[region_code] = results[i]
                if not results[i]:
                    self.logger.warning(f"Region {region_code} is unhealthy")
            else:
                health_status[region_code] = False
                self.logger.error(f"Health check failed for region {region_code}: {results[i]}")

        return health_status

    async def _check_region_health(self, region: GeoRegion) -> bool:
        """Check health of a specific region"""
        try:
            async with self.session.get(region.health_check_url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('status') == 'healthy'
                return False
        except Exception as e:
            self.logger.error(f"Health check failed for region {region.code}: {e}")
            return False

    def get_regional_performance_metrics(self) -> Dict:
        """Get performance metrics for all regions"""
        metrics = {
            'total_regions': len(self.regions),
            'healthy_regions': 0,
            'total_capacity': 0,
            'total_load': 0,
            'regions': {}
        }

        for region_code, region in self.regions.items():
            region_metrics = {
                'name': region.name,
                'type': region.region_type.value,
                'provider': region.provider.value,
                'capacity': region.capacity,
                'current_load': region.current_load,
                'available_capacity': region.capacity * (1 - region.current_load),
                'load_percentage': region.current_load * 100,
                'data_sovereignty': region.data_sovereignty,
                'priority': region.priority
            }

            # Add latency information if available
            latency_to_region = []
            for (source, target), latency_info in self.latency_matrix.items():
                if target == region_code:
                    latency_to_region.append({
                        'source': source,
                        'latency_ms': latency_info.latency_ms,
                        'bandwidth_mbps': latency_info.bandwidth_mbps,
                        'reliability': latency_info.reliability
                    })

            if latency_to_region:
                region_metrics['average_latency'] = sum(l['latency_ms'] for l in latency_to_region) / len(latency_to_region)
                region_metrics['latency_connections'] = latency_to_region

            metrics['regions'][region_code] = region_metrics
            metrics['total_capacity'] += region.capacity
            metrics['total_load'] += region.current_load

        metrics['average_load'] = metrics['total_load'] / len(self.regions) if self.regions else 0
        metrics['total_available_capacity'] = metrics['total_capacity'] * (1 - metrics['average_load'])

        return metrics

    async def update_region_load(self, region_code: str, load_delta: float):
        """Update load for a specific region"""
        if region_code in self.regions:
            region = self.regions[region_code]
            region.current_load = max(0, min(0.95, region.current_load + load_delta))
            self._update_load_balancer_weights()

    def get_regions_by_type(self, region_type: RegionType) -> List[GeoRegion]:
        """Get regions filtered by type"""
        return [r for r in self.regions.values() if r.region_type == region_type]

    def get_regions_by_provider(self, provider: CloudProvider) -> List[GeoRegion]:
        """Get regions filtered by cloud provider"""
        return [r for r in self.regions.values() if r.provider == provider]

    def get_regions_by_country(self, country_code: str) -> List[GeoRegion]:
        """Get regions that can serve a specific country based on data sovereignty"""
        return [r for r in self.regions.values() if country_code in r.data_sovereignty]

    async def simulate_global_load(self, requests_per_minute: int,
                                 duration_minutes: int = 10):
        """Simulate global load for testing purposes"""
        print(f"Simulating {requests_per_minute} requests/minute for {duration_minutes} minutes")

        # Sample IP addresses from different regions
        sample_ips = [
            '8.8.8.8',        # US
            '1.1.1.1',        # US
            '208.67.222.222', # US
            '9.9.9.9',        # US
            '149.112.112.112', # US
            '8.8.4.4',        # US
            '1.0.0.1',        # Australia
            '208.67.220.220', # US
            '94.140.14.14',   # Germany
            '94.140.15.15',   # Germany
        ]

        start_time = time.time()
        total_requests = 0

        while time.time() - start_time < duration_minutes * 60:
            # Generate requests
            requests_in_batch = requests_per_minute // 10  # Process in batches every 6 seconds

            for _ in range(requests_in_batch):
                ip = random.choice(sample_ips)
                endpoint = await self.route_request(ip)
                if endpoint:
                    total_requests += 1

                    # Random load decrease (requests completing)
                    if random.random() < 0.3:
                        await self.update_region_load(
                            endpoint.split('.')[0].split('//')[1].split('-')[0],
                            -0.001
                        )

            # Wait before next batch
            await asyncio.sleep(6)

            # Print metrics every minute
            if int(time.time() - start_time) % 60 < 6:
                metrics = self.get_regional_performance_metrics()
                print(f"Minute {int((time.time() - start_time) / 60) + 1}: "
                      f"Avg Load: {metrics['average_load']:.2%}, "
                      f"Total Requests: {total_requests}")

        print(f"Simulation complete. Total requests processed: {total_requests}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.geoip_reader:
            self.geoip_reader.close()

    def _load_configuration(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load custom regions
            if 'regions' in config:
                for region_config in config['regions']:
                    region = GeoRegion(**region_config)
                    self.regions[region.code] = region

            # Load latency matrix if available
            if 'latency_matrix' in config:
                for latency_config in config['latency_matrix']:
                    metrics = LatencyMetrics(**latency_config)
                    self.latency_matrix[(metrics.source_region, metrics.target_region)] = metrics

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

    def save_configuration(self, config_path: str):
        """Save current configuration to file"""
        config = {
            'regions': [asdict(region) for region in self.regions.values()],
            'latency_matrix': [asdict(metrics) for metrics in self.latency_matrix.values()]
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")


async def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)

    distributor = GeographicDistributor()
    await distributor.initialize()

    # Test routing
    test_ips = ['8.8.8.8', '1.1.1.1', '94.140.14.14']

    print("Testing geographic routing:")
    for ip in test_ips:
        user_location = await distributor.get_user_location(ip)
        if user_location:
            print(f"IP {ip}: {user_location.city}, {user_location.country}")

            endpoint = await distributor.route_request(ip)
            print(f"  Routed to: {endpoint}")

        print()

    # Get performance metrics
    metrics = distributor.get_regional_performance_metrics()
    print(f"Global Performance Metrics:")
    print(f"  Total Regions: {metrics['total_regions']}")
    print(f"  Total Capacity: {metrics['total_capacity']}")
    print(f"  Average Load: {metrics['average_load']:.2%}")
    print(f"  Available Capacity: {metrics['total_available_capacity']:.0f}")

    # Health check
    health_status = await distributor.health_check_all_regions()
    healthy_count = sum(1 for status in health_status.values() if status)
    print(f"Healthy Regions: {healthy_count}/{len(health_status)}")

    await distributor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())