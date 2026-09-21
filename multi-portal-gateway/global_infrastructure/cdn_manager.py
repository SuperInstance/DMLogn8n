#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure - CDN and Edge Computing Manager
Manages global CDN distribution, edge computing, and content optimization
"""

import asyncio
import json
import logging
import time
import hashlib
import mimetypes
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from pathlib import Path

import aiohttp
import aiofiles
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError
import cloudflare
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

class CDNProvider(Enum):
    """Supported CDN providers"""
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    AWS_CLOUDFRONT = "aws_cloudfront"
    FASTLY = "fastly"
    AZURE_CDN = "azure_cdn"
    GOOGLE_CDN = "google_cdn"

class EdgeFunctionType(Enum):
    """Types of edge computing functions"""
    IMAGE_OPTIMIZATION = "image_optimization"
    VIDEO_TRANSCODING = "video_transcoding"
    API_GATEWAY = "api_gateway"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    CUSTOM_LOGIC = "custom_logic"

class CachePolicy(Enum):
    """Cache policies for CDN"""
    NO_CACHE = "no-cache"
    STATIC_CONTENT = "static-content"
    DYNAMIC_CONTENT = "dynamic-content"
    API_RESPONSES = "api-responses"
    PERSONALIZED = "personalized"

@dataclass
class CDNZone:
    """CDN zone configuration"""
    name: str
    domain: str
    provider: CDNProvider
    origin_servers: List[str]
    cache_policy: CachePolicy
    edge_locations: List[str]
    ssl_enabled: bool
    ddos_protection: bool
    waf_enabled: bool
    compression_enabled: bool
    minify_enabled: bool
    created_at: float
    last_updated: float

@dataclass
class EdgeNode:
    """Edge computing node"""
    id: str
    region: str
    provider: CDNProvider
    location: str
    latitude: float
    longitude: float
    capacity: int
    current_load: float
    supported_functions: List[EdgeFunctionType]
    status: str
    last_health_check: float

@dataclass
class CDNResource:
    """CDN resource configuration"""
    url: str
    content_type: str
    size_bytes: int
    cache_ttl: int
    compressed: bool
    optimized: bool
    edge_locations_cached: List[str]
    hits: int
    misses: int
    last_accessed: float
    etag: str

@dataclass
class EdgeFunction:
    """Edge computing function"""
    name: str
    function_type: EdgeFunctionType
    code: str
    runtime: str
    memory_mb: int
    timeout_ms: int
    max_concurrency: int
    triggers: List[str]
    enabled: bool
    deployment_status: str
    created_at: float
    updated_at: float

class CDNManager:
    """Global CDN and edge computing management system"""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.zones: Dict[str, CDNZone] = {}
        self.edge_nodes: Dict[str, EdgeNode] = {}
        self.resources: Dict[str, CDNResource] = {}
        self.edge_functions: Dict[str, EdgeFunction] = {}
        self.session = None
        self.cache_stats = {
            'total_hits': 0,
            'total_misses': 0,
            'bandwidth_saved_gb': 0,
            'total_requests': 0
        }

        # Provider clients
        self.cloudflare_client = None
        self.aws_cf_client = None
        self.fastly_client = None

        # Initialize configuration
        if config_path:
            self._load_configuration(config_path)
        else:
            self._initialize_default_configuration()

    def _initialize_default_configuration(self):
        """Initialize default CDN configuration"""
        # Default zones
        default_zones = [
            CDNZone(
                name="dmlogn8n-primary",
                domain="cdn.dmlogn8n.com",
                provider=CDNProvider.CLOUDFLARE,
                origin_servers=["origin.dmlogn8n.com"],
                cache_policy=CachePolicy.STATIC_CONTENT,
                edge_locations=["us-east", "us-west", "eu-west", "ap-southeast"],
                ssl_enabled=True,
                ddos_protection=True,
                waf_enabled=True,
                compression_enabled=True,
                minify_enabled=True,
                created_at=time.time(),
                last_updated=time.time()
            ),
            CDNZone(
                name="dmlogn8n-api",
                domain="api.dmlogn8n.com",
                provider=CDNProvider.AWS_CLOUDFRONT,
                origin_servers=["api-origin.dmlogn8n.com"],
                cache_policy=CachePolicy.API_RESPONSES,
                edge_locations=["us-east", "eu-west", "ap-southeast"],
                ssl_enabled=True,
                ddos_protection=True,
                waf_enabled=False,
                compression_enabled=True,
                minify_enabled=False,
                created_at=time.time(),
                last_updated=time.time()
            )
        ]

        for zone in default_zones:
            self.zones[zone.name] = zone

        # Default edge nodes
        default_edge_nodes = [
            EdgeNode(
                id="cf-ams",
                region="eu-west",
                provider=CDNProvider.CLOUDFLARE,
                location="Amsterdam, NL",
                latitude=52.3676,
                longitude=4.9041,
                capacity=10000,
                current_load=0.3,
                supported_functions=[
                    EdgeFunctionType.IMAGE_OPTIMIZATION,
                    EdgeFunctionType.RATE_LIMITING,
                    EdgeFunctionType.AUTHENTICATION
                ],
                status="active",
                last_health_check=time.time()
            ),
            EdgeNode(
                id="cf-sfo",
                region="us-west",
                provider=CDNProvider.CLOUDFLARE,
                location="San Francisco, CA",
                latitude=37.7749,
                longitude=-122.4194,
                capacity=8000,
                current_load=0.4,
                supported_functions=[
                    EdgeFunctionType.IMAGE_OPTIMIZATION,
                    EdgeFunctionType.VIDEO_TRANSCODING,
                    EdgeFunctionType.API_GATEWAY
                ],
                status="active",
                last_health_check=time.time()
            ),
            EdgeNode(
                id="cf-sin",
                region="ap-southeast",
                provider=CDNProvider.CLOUDFLARE,
                location="Singapore",
                latitude=1.3521,
                longitude=103.8198,
                capacity=6000,
                current_load=0.35,
                supported_functions=[
                    EdgeFunctionType.IMAGE_OPTIMIZATION,
                    EdgeFunctionType.RATE_LIMITING,
                    EdgeFunctionType.API_GATEWAY
                ],
                status="active",
                last_health_check=time.time()
            )
        ]

        for node in default_edge_nodes:
            self.edge_nodes[node.id] = node

    async def initialize(self):
        """Initialize the CDN manager"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Initialize provider clients
        await self._initialize_provider_clients()

        # Start health monitoring
        asyncio.create_task(self._health_monitoring_loop())

        # Start metrics collection
        asyncio.create_task(self._metrics_collection_loop())

    async def _initialize_provider_clients(self):
        """Initialize CDN provider clients"""
        try:
            # Initialize Cloudflare client
            # In production, these would be loaded from environment variables
            # self.cloudflare_client = cloudflare.CloudFlare(email=..., key=...)

            # Initialize AWS CloudFront client
            # self.aws_cf_client = boto3.client('cloudfront')

            # Initialize Fastly client
            # self.fastly_client = fastly.Fastly(api_key=...)

            self.logger.info("CDN provider clients initialized")

        except Exception as e:
            self.logger.error(f"Error initializing CDN provider clients: {e}")

    async def create_zone(self, zone: CDNZone) -> bool:
        """Create a new CDN zone"""
        try:
            # Create zone based on provider
            if zone.provider == CDNProvider.CLOUDFLARE:
                success = await self._create_cloudflare_zone(zone)
            elif zone.provider == CDNProvider.AWS_CLOUDFRONT:
                success = await self._create_cloudfront_distribution(zone)
            else:
                success = await self._create_generic_zone(zone)

            if success:
                self.zones[zone.name] = zone
                self.logger.info(f"Successfully created CDN zone {zone.name}")
                return True
            else:
                self.logger.error(f"Failed to create CDN zone {zone.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating CDN zone {zone.name}: {e}")
            return False

    async def _create_cloudflare_zone(self, zone: CDNZone) -> bool:
        """Create Cloudflare zone"""
        try:
            # Simulate Cloudflare API call
            # In production: zone_data = self.cloudflare_client.zones.create(...)

            # Create DNS records for origin servers
            for origin in zone.origin_servers:
                # Simulate DNS record creation
                pass

            # Configure caching settings
            await self._configure_cloudflare_cache(zone)

            # Enable security features
            if zone.ddos_protection:
                await self._enable_cloudflare_ddos(zone)
            if zone.waf_enabled:
                await self._enable_cloudflare_waf(zone)

            return True

        except Exception as e:
            self.logger.error(f"Error creating Cloudflare zone: {e}")
            return False

    async def _create_cloudfront_distribution(self, zone: CDNZone) -> bool:
        """Create AWS CloudFront distribution"""
        try:
            # Simulate CloudFront API call
            # In production: response = self.aws_cf_client.create_distribution(...)

            # Configure origin
            origin_config = {
                'Id': zone.origin_servers[0],
                'DomainName': zone.origin_servers[0],
                'CustomOriginConfig': {
                    'HTTPPort': 80,
                    'HTTPSPort': 443,
                    'OriginProtocolPolicy': 'https-only'
                }
            }

            # Configure cache behavior
            cache_behavior = {
                'TargetOriginId': zone.origin_servers[0],
                'ViewerProtocolPolicy': 'redirect-to-https',
                'Compress': zone.compression_enabled,
                'MinTTL': zone.cache_policy.value == 'static-content' and 86400 or 0
            }

            return True

        except Exception as e:
            self.logger.error(f"Error creating CloudFront distribution: {e}")
            return False

    async def _create_generic_zone(self, zone: CDNZone) -> bool:
        """Create zone for generic CDN provider"""
        # Generic implementation
        return True

    async def upload_content(self, zone_name: str, file_path: str,
                           cache_ttl: int = 86400) -> Optional[str]:
        """Upload content to CDN"""
        try:
            if zone_name not in self.zones:
                raise ValueError(f"Zone {zone_name} not found")

            zone = self.zones[zone_name]

            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()

            # Generate unique key
            file_name = Path(file_path).name
            content_hash = hashlib.md5(content).hexdigest()
            cdn_key = f"{file_name}_{content_hash}"

            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)

            # Compress if enabled and applicable
            if zone.compression_enabled and content_type in [
                'text/html', 'text/css', 'application/javascript',
                'text/plain', 'application/json', 'text/xml'
            ]:
                content = await self._compress_content(content)
                compressed = True
            else:
                compressed = False

            # Upload to CDN provider
            cdn_url = await self._upload_to_provider(zone, cdn_key, content, content_type)

            if cdn_url:
                # Track resource
                resource = CDNResource(
                    url=cdn_url,
                    content_type=content_type,
                    size_bytes=len(content),
                    cache_ttl=cache_ttl,
                    compressed=compressed,
                    optimized=await self._should_optimize(content_type),
                    edge_locations_cached=[],
                    hits=0,
                    misses=0,
                    last_accessed=time.time(),
                    etag=content_hash
                )
                self.resources[cdn_key] = resource

                # Invalidate cache if needed
                if cache_ttl == 0:
                    await self.invalidate_cache(zone_name, [cdn_url])

                self.logger.info(f"Uploaded content to CDN: {cdn_url}")
                return cdn_url

            return None

        except Exception as e:
            self.logger.error(f"Error uploading content to CDN: {e}")
            return None

    async def _upload_to_provider(self, zone: CDNZone, key: str,
                                content: bytes, content_type: str) -> Optional[str]:
        """Upload content to specific CDN provider"""
        try:
            if zone.provider == CDNProvider.AWS_CLOUDFRONT:
                return await self._upload_to_s3(zone, key, content, content_type)
            elif zone.provider == CDNProvider.CLOUDFLARE:
                return await self._upload_to_cloudflare(zone, key, content, content_type)
            else:
                return await self._upload_generic(zone, key, content, content_type)

        except Exception as e:
            self.logger.error(f"Error uploading to provider {zone.provider}: {e}")
            return None

    async def _upload_to_s3(self, zone: CDNZone, key: str,
                          content: bytes, content_type: str) -> Optional[str]:
        """Upload content to S3 for CloudFront"""
        try:
            # Simulate S3 upload
            # In production: s3_client.put_object(Bucket=..., Key=key, Body=content, ContentType=content_type)

            cdn_url = f"https://{zone.domain}/{key}"
            return cdn_url

        except Exception as e:
            self.logger.error(f"Error uploading to S3: {e}")
            return None

    async def _upload_to_cloudflare(self, zone: CDNZone, key: str,
                                  content: bytes, content_type: str) -> Optional[str]:
        """Upload content to Cloudflare"""
        try:
            # Simulate Cloudflare upload
            cdn_url = f"https://{zone.domain}/{key}"
            return cdn_url

        except Exception as e:
            self.logger.error(f"Error uploading to Cloudflare: {e}")
            return None

    async def _upload_generic(self, zone: CDNZone, key: str,
                            content: bytes, content_type: str) -> Optional[str]:
        """Generic upload implementation"""
        cdn_url = f"https://{zone.domain}/{key}"
        return cdn_url

    async def _compress_content(self, content: bytes) -> bytes:
        """Compress content using gzip"""
        try:
            import gzip
            return gzip.compress(content)
        except Exception as e:
            self.logger.error(f"Error compressing content: {e}")
            return content

    async def _should_optimize(self, content_type: str) -> bool:
        """Check if content should be optimized"""
        optimizable_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm', 'video/ogg'
        ]
        return content_type in optimizable_types

    async def create_edge_function(self, function: EdgeFunction) -> bool:
        """Create an edge computing function"""
        try:
            # Deploy function based on type
            if function.function_type == EdgeFunctionType.IMAGE_OPTIMIZATION:
                success = await self._create_image_optimization_function(function)
            elif function.function_type == EdgeFunctionType.RATE_LIMITING:
                success = await self._create_rate_limiting_function(function)
            elif function.function_type == EdgeFunctionType.API_GATEWAY:
                success = await self._create_api_gateway_function(function)
            else:
                success = await self._create_custom_function(function)

            if success:
                self.edge_functions[function.name] = function
                self.logger.info(f"Successfully created edge function {function.name}")
                return True
            else:
                self.logger.error(f"Failed to create edge function {function.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating edge function {function.name}: {e}")
            return False

    async def _create_image_optimization_function(self, function: EdgeFunction):
        """Create image optimization edge function"""
        # Default image optimization code
        default_code = '''
        async function handleRequest(request) {
            const url = new URL(request.url);
            const imageParam = url.searchParams.get('format');

            if (imageParam) {
                // Transform image based on format parameter
                return new Response("Optimized image", {
                    headers: { 'Content-Type': 'image/webp' }
                });
            }

            return fetch(request);
        }
        '''
        function.code = default_code
        return True

    async def _create_rate_limiting_function(self, function: EdgeFunction):
        """Create rate limiting edge function"""
        default_code = '''
        async function handleRequest(request) {
            const clientIP = request.headers.get('CF-Connecting-IP');
            const rateLimitKey = `rate_limit_${clientIP}`;

            // Implement rate limiting logic
            const limit = 100; // requests per minute
            const current = await KV.get(rateLimitKey) || 0;

            if (current >= limit) {
                return new Response("Rate limit exceeded", { status: 429 });
            }

            await KV.put(rateLimitKey, parseInt(current) + 1, { expirationTtl: 60 });
            return fetch(request);
        }
        '''
        function.code = default_code
        return True

    async def _create_api_gateway_function(self, function: EdgeFunction):
        """Create API gateway edge function"""
        default_code = '''
        async function handleRequest(request) {
            const url = new URL(request.url);
            const path = url.pathname;

            // Route to appropriate backend service
            if (path.startsWith('/api/')) {
                const backendUrl = `https://api-origin.dmlogn8n.com${path}${url.search}`;
                const response = await fetch(backendUrl, request);
                return response;
            }

            return new Response("Not Found", { status: 404 });
        }
        '''
        function.code = default_code
        return True

    async def _create_custom_function(self, function: EdgeFunction):
        """Create custom edge function"""
        # Use provided code
        return True

    async def invalidate_cache(self, zone_name: str, paths: List[str]) -> bool:
        """Invalidate CDN cache for specific paths"""
        try:
            if zone_name not in self.zones:
                raise ValueError(f"Zone {zone_name} not found")

            zone = self.zones[zone_name]

            if zone.provider == CDNProvider.AWS_CLOUDFRONT:
                return await self._invalidate_cloudfront_cache(zone, paths)
            elif zone.provider == CDNProvider.CLOUDFLARE:
                return await self._invalidate_cloudflare_cache(zone, paths)
            else:
                return await self._invalidate_generic_cache(zone, paths)

        except Exception as e:
            self.logger.error(f"Error invalidating cache for zone {zone_name}: {e}")
            return False

    async def _invalidate_cloudfront_cache(self, zone: CDNZone, paths: List[str]) -> bool:
        """Invalidate CloudFront cache"""
        try:
            # Simulate CloudFront invalidation
            # In production: self.aws_cf_client.create_invalidation(...)

            self.logger.info(f"Invalidated CloudFront cache for {len(paths)} paths")
            return True

        except Exception as e:
            self.logger.error(f"Error invalidating CloudFront cache: {e}")
            return False

    async def _invalidate_cloudflare_cache(self, zone: CDNZone, paths: List[str]) -> bool:
        """Invalidate Cloudflare cache"""
        try:
            # Simulate Cloudflare cache purge
            # In production: self.cloudflare_client.zones.purge_cache(...)

            self.logger.info(f"Invalidated Cloudflare cache for {len(paths)} paths")
            return True

        except Exception as e:
            self.logger.error(f"Error invalidating Cloudflare cache: {e}")
            return False

    async def _invalidate_generic_cache(self, zone: CDNZone, paths: List[str]) -> bool:
        """Generic cache invalidation"""
        return True

    async def get_edge_location_for_request(self, client_ip: str,
                                          user_agent: str) -> Optional[EdgeNode]:
        """Get optimal edge location for a request"""
        try:
            # Get client location (simplified)
            # In production, use GeoIP database

            # Find closest edge node with capacity
            available_nodes = [
                node for node in self.edge_nodes.values()
                if node.status == "active" and node.current_load < 0.8
            ]

            if not available_nodes:
                return None

            # For simplicity, return the first available node
            # In production, calculate actual geographic distance
            return available_nodes[0]

        except Exception as e:
            self.logger.error(f"Error getting edge location: {e}")
            return None

    async def get_cdn_metrics(self) -> Dict[str, Any]:
        """Get CDN performance metrics"""
        metrics = {
            'cache_stats': self.cache_stats.copy(),
            'zones': {},
            'edge_nodes': {},
            'resources': {
                'total': len(self.resources),
                'total_size_gb': sum(r.size_bytes for r in self.resources.values()) / (1024**3),
                'cached_locations': len(set(location for r in self.resources.values() for location in r.edge_locations_cached))
            },
            'functions': {
                'total': len(self.edge_functions),
                'active': sum(1 for f in self.edge_functions.values() if f.enabled)
            }
        }

        # Zone metrics
        for zone_name, zone in self.zones.items():
            zone_resources = [r for r in self.resources.values() if zone.domain in r.url]
            metrics['zones'][zone_name] = {
                'domain': zone.domain,
                'provider': zone.provider.value,
                'resources': len(zone_resources),
                'cache_policy': zone.cache_policy.value,
                'security_features': {
                    'ssl': zone.ssl_enabled,
                    'ddos': zone.ddos_protection,
                    'waf': zone.waf_enabled
                }
            }

        # Edge node metrics
        for node_id, node in self.edge_nodes.items():
            metrics['edge_nodes'][node_id] = {
                'region': node.region,
                'provider': node.provider.value,
                'location': node.location,
                'load_percentage': node.current_load * 100,
                'capacity': node.capacity,
                'supported_functions': [f.value for f in node.supported_functions],
                'status': node.status
            }

        return metrics

    async def _health_monitoring_loop(self):
        """Continuous health monitoring of edge nodes"""
        while True:
            try:
                health_tasks = []
                for node_id, node in self.edge_nodes.items():
                    health_tasks.append(self._check_edge_node_health(node_id))

                await asyncio.gather(*health_tasks, return_exceptions=True)
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _check_edge_node_health(self, node_id: str) -> bool:
        """Check health of a specific edge node"""
        try:
            node = self.edge_nodes[node_id]

            # Simulate health check
            # In production, make actual HTTP requests to edge node

            # Update status based on health check
            node.status = "active"  # or "degraded", "failed"
            node.last_health_check = time.time()

            return node.status == "active"

        except Exception as e:
            self.logger.error(f"Health check failed for edge node {node_id}: {e}")
            self.edge_nodes[node_id].status = "failed"
            return False

    async def _metrics_collection_loop(self):
        """Continuous metrics collection"""
        while True:
            try:
                # Simulate metrics collection from CDN providers
                await self._collect_provider_metrics()
                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)

    async def _collect_provider_metrics(self):
        """Collect metrics from CDN providers"""
        try:
            # Simulate metrics collection
            # In production, make actual API calls to provider APIs

            # Update cache statistics
            for resource in self.resources.values():
                # Simulate random hits/misses
                if random.random() < 0.8:  # 80% cache hit rate
                    resource.hits += 1
                    self.cache_stats['total_hits'] += 1
                else:
                    resource.misses += 1
                    self.cache_stats['total_misses'] += 1

                resource.last_accessed = time.time()
                self.cache_stats['total_requests'] += 1

            # Calculate bandwidth saved (simplified)
            bandwidth_saved = self.cache_stats['total_hits'] * 0.5  # Assume 0.5MB saved per hit
            self.cache_stats['bandwidth_saved_gb'] = bandwidth_saved / (1024**3)

        except Exception as e:
            self.logger.error(f"Error collecting provider metrics: {e}")

    async def optimize_delivery(self, zone_name: str) -> Dict[str, Any]:
        """Optimize content delivery for a zone"""
        try:
            if zone_name not in self.zones:
                raise ValueError(f"Zone {zone_name} not found")

            zone = self.zones[zone_name]
            optimizations = []

            # Analyze cache performance
            zone_resources = [r for r in self.resources.values() if zone.domain in r.url]

            # Find underperforming resources
            for resource in zone_resources:
                hit_rate = resource.hits / (resource.hits + resource.misses) if (resource.hits + resource.misses) > 0 else 0

                if hit_rate < 0.5:  # Low cache hit rate
                    optimizations.append({
                        'type': 'increase_cache_ttl',
                        'resource': resource.url,
                        'current_hit_rate': hit_rate,
                        'recommendation': 'Increase cache TTL for better performance'
                    })

                if resource.size_bytes > 1024 * 1024 and not resource.compressed:  # > 1MB and not compressed
                    optimizations.append({
                        'type': 'enable_compression',
                        'resource': resource.url,
                        'size_mb': resource.size_bytes / (1024 * 1024),
                        'recommendation': 'Enable compression to reduce bandwidth'
                    })

            # Check edge node load
            overloaded_nodes = [
                node for node in self.edge_nodes.values()
                if node.current_load > 0.8
            ]

            if overloaded_nodes:
                optimizations.append({
                    'type': 'scale_edge_nodes',
                    'nodes': [node.id for node in overloaded_nodes],
                    'recommendation': 'Scale up edge nodes in high-load regions'
                })

            return {
                'zone': zone_name,
                'optimizations': optimizations,
                'total_resources': len(zone_resources),
                'average_hit_rate': sum(r.hits / (r.hits + r.misses) if (r.hits + r.misses) > 0 else 0 for r in zone_resources) / len(zone_resources) if zone_resources else 0
            }

        except Exception as e:
            self.logger.error(f"Error optimizing delivery for zone {zone_name}: {e}")
            return {'error': str(e)}

    def _load_configuration(self, config_path: str):
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load zones
            if 'zones' in config:
                for zone_config in config['zones']:
                    zone_config['provider'] = CDNProvider(zone_config['provider'])
                    zone_config['cache_policy'] = CachePolicy(zone_config['cache_policy'])
                    zone = CDNZone(**zone_config)
                    self.zones[zone.name] = zone

            # Load edge nodes
            if 'edge_nodes' in config:
                for node_config in config['edge_nodes']:
                    node_config['provider'] = CDNProvider(node_config['provider'])
                    node_config['supported_functions'] = [
                        EdgeFunctionType(f) for f in node_config['supported_functions']
                    ]
                    node = EdgeNode(**node_config)
                    self.edge_nodes[node.id] = node

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")

    def save_configuration(self, config_path: str):
        """Save current configuration to file"""
        config = {
            'zones': [
                {
                    **asdict(zone),
                    'provider': zone.provider.value,
                    'cache_policy': zone.cache_policy.value
                }
                for zone in self.zones.values()
            ],
            'edge_nodes': [
                {
                    **asdict(node),
                    'provider': node.provider.value,
                    'supported_functions': [f.value for f in node.supported_functions]
                }
                for node in self.edge_nodes.values()
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


async def main():
    """Main function for testing"""
    logging.basicConfig(level=logging.INFO)
    import random

    cdn_manager = CDNManager()
    await cdn_manager.initialize()

    # Create a sample zone
    sample_zone = CDNZone(
        name="test-zone",
        domain="test.dmlogn8n.com",
        provider=CDNProvider.CLOUDFLARE,
        origin_servers=["origin.dmlogn8n.com"],
        cache_policy=CachePolicy.STATIC_CONTENT,
        edge_locations=["us-east", "eu-west"],
        ssl_enabled=True,
        ddos_protection=True,
        waf_enabled=False,
        compression_enabled=True,
        minify_enabled=True,
        created_at=time.time(),
        last_updated=time.time()
    )

    print("Creating CDN zone...")
    success = await cdn_manager.create_zone(sample_zone)
    print(f"Zone creation: {'Success' if success else 'Failed'}")

    # Create an edge function
    sample_function = EdgeFunction(
        name="image-optimizer",
        function_type=EdgeFunctionType.IMAGE_OPTIMIZATION,
        code="// Function code",
        runtime="javascript",
        memory_mb=128,
        timeout_ms=5000,
        max_concurrency=100,
        triggers=["image/*"],
        enabled=True,
        deployment_status="deployed",
        created_at=time.time(),
        updated_at=time.time()
    )

    print("Creating edge function...")
    success = await cdn_manager.create_edge_function(sample_function)
    print(f"Function creation: {'Success' if success else 'Failed'}")

    # Get metrics
    metrics = await cdn_manager.get_cdn_metrics()
    print(f"\nCDN Metrics:")
    print(f"  Total Zones: {len(metrics['zones'])}")
    print(f"  Total Edge Nodes: {len(metrics['edge_nodes'])}")
    print(f"  Total Resources: {metrics['resources']['total']}")
    print(f"  Total Functions: {metrics['functions']['total']}")
    print(f"  Cache Hit Rate: {metrics['cache_stats']['total_hits'] / max(1, metrics['cache_stats']['total_requests']) * 100:.1f}%")

    await cdn_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())