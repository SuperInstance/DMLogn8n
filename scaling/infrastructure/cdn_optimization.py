#!/usr/bin/env python3
"""
Global CDN and Edge Computing Optimization System
Multi-CDN management, edge caching, geographic content distribution, and performance optimization
"""

import asyncio
import json
import logging
import aiohttp
import hashlib
import time
import gzip
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import boto3
import cloudflare
from collections import defaultdict
import statistics
import geoip2.database
import maxminddb
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CDNProvider(Enum):
    CLOUDFLARE = "cloudflare"
    AWS_CLOUDFRONT = "aws_cloudfront"
    AKAMAI = "akamai"
    FASTLY = "fastly"
    AZURE_CDN = "azure_cdn"
    GOOGLE_CDN = "google_cdn"

class CachePolicy(Enum):
    TTL_BASED = "ttl_based"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    BYPASS = "bypass"
    DYNAMIC = "dynamic"
    STATIC = "static"

class CompressionType(Enum):
    NONE = "none"
    GZIP = "gzip"
    BROTLI = "brotli"
    AUTO = "auto"

@dataclass
class CDNNode:
    """CDN edge node configuration"""
    node_id: str
    provider: CDNProvider
    region: str
    country: str
    city: str
    latitude: float
    longitude: float
    capacity: float
    current_load: float
    cache_size: int
    cache_hit_rate: float
    response_time: float
    bandwidth_mbps: float
    is_active: bool
    supported_features: List[str]
    endpoints: List[str]

@dataclass
class CachedContent:
    """Cached content metadata"""
    content_id: str
    url: str
    content_type: str
    content_size: int
    compressed_size: int
    cache_policy: CachePolicy
    ttl: int
    created_at: datetime
    last_accessed: datetime
    access_count: int
    edge_nodes: Set[str]
    compression_type: CompressionType
    etag: str
    last_modified: datetime

@dataclass
class ContentOptimization:
    """Content optimization settings"""
    minify_html: bool
    minify_css: bool
    minify_js: bool
    optimize_images: bool
    webp_conversion: bool
    lazy_loading: bool
    resource_hints: bool
    compression: CompressionType
    cache_control: str

@dataclass
class CDNMetrics:
    """CDN performance metrics"""
    timestamp: datetime
    node_id: str
    request_count: int
    cache_hits: int
    cache_misses: int
    bytes_served: int
    avg_response_time: float
    error_count: int
    bandwidth_utilization: float
    cpu_utilization: float

class EdgeCacheManager:
    """Edge cache management system"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.local_cache = {}
        self.cache_stats = defaultdict(int)
        self.cache_policies = self._load_cache_policies()

    def _load_cache_policies(self) -> Dict[str, Dict]:
        """Load cache policies for different content types"""
        return {
            'static': {
                'css': {'ttl': 86400, 'policy': CachePolicy.STATIC},
                'js': {'ttl': 86400, 'policy': CachePolicy.STATIC},
                'images': {'ttl': 604800, 'policy': CachePolicy.STATIC},
                'fonts': {'ttl': 604800, 'policy': CachePolicy.STATIC},
                'favicon': {'ttl': 86400, 'policy': CachePolicy.STATIC}
            },
            'dynamic': {
                'html': {'ttl': 3600, 'policy': CachePolicy.DYNAMIC},
                'json': {'ttl': 300, 'policy': CachePolicy.DYNAMIC},
                'api': {'ttl': 60, 'policy': CachePolicy.DYNAMIC}
            }
        }

    async def get_cached_content(self, content_id: str, node_id: str) -> Optional[bytes]:
        """Get cached content from edge node"""
        try:
            # Check local cache first
            cache_key = f"edge_cache:{node_id}:{content_id}"
            cached_data = self.redis.get(cache_key)

            if cached_data:
                self.cache_stats[f'{node_id}:hits'] += 1
                return cached_data
            else:
                self.cache_stats[f'{node_id}:misses'] += 1
                return None

        except Exception as e:
            logger.error(f"Error getting cached content {content_id} from {node_id}: {e}")
            return None

    async def cache_content(self, content_id: str, content: bytes, node_id: str,
                          ttl: int, content_type: str) -> bool:
        """Cache content on edge node"""
        try:
            cache_key = f"edge_cache:{node_id}:{content_id}"

            # Compress content if beneficial
            compressed_content = await self._compress_content(content, content_type)

            # Store with TTL
            self.redis.setex(cache_key, ttl, compressed_content)

            # Store metadata
            metadata = {
                'content_id': content_id,
                'content_type': content_type,
                'original_size': len(content),
                'compressed_size': len(compressed_content),
                'cached_at': datetime.utcnow().isoformat(),
                'node_id': node_id,
                'ttl': ttl
            }

            metadata_key = f"edge_metadata:{node_id}:{content_id}"
            self.redis.setex(metadata_key, ttl, json.dumps(metadata))

            return True

        except Exception as e:
            logger.error(f"Error caching content {content_id} on {node_id}: {e}")
            return False

    async def _compress_content(self, content: bytes, content_type: str) -> bytes:
        """Compress content if beneficial"""
        # Don't compress already compressed content
        if content_type in ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'application/zip']:
            return content

        # Compress if size reduction is significant
        compressed = gzip.compress(content)
        if len(compressed) < len(content) * 0.8:
            return compressed

        return content

    async def invalidate_cache(self, content_id: str, node_id: str = None) -> bool:
        """Invalidate cached content"""
        try:
            if node_id:
                # Invalidate on specific node
                cache_key = f"edge_cache:{node_id}:{content_id}"
                metadata_key = f"edge_metadata:{node_id}:{content_id}"
                self.redis.delete(cache_key, metadata_key)
            else:
                # Invalidate on all nodes
                pattern = f"edge_cache:*:{content_id}"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)

                pattern = f"edge_metadata:*:{content_id}"
                metadata_keys = self.redis.keys(pattern)
                if metadata_keys:
                    self.redis.delete(*metadata_keys)

            return True

        except Exception as e:
            logger.error(f"Error invalidating cache for {content_id}: {e}")
            return False

    def get_cache_stats(self, node_id: str = None) -> Dict[str, Any]:
        """Get cache statistics"""
        if node_id:
            hits = self.cache_stats.get(f'{node_id}:hits', 0)
            misses = self.cache_stats.get(f'{node_id}:misses', 0)
            total = hits + misses

            return {
                'hits': hits,
                'misses': misses,
                'total_requests': total,
                'hit_rate': (hits / total * 100) if total > 0 else 0
            }
        else:
            # Aggregate stats across all nodes
            total_hits = sum(v for k, v in self.cache_stats.items() if k.endswith(':hits'))
            total_misses = sum(v for k, v in self.cache_stats.items() if k.endswith(':misses'))
            total = total_hits + total_misses

            return {
                'total_hits': total_hits,
                'total_misses': total_misses,
                'total_requests': total,
                'overall_hit_rate': (total_hits / total * 100) if total > 0 else 0,
                'node_stats': {k: self.get_cache_stats(k.split(':')[0])
                             for k in set(k.split(':')[0] for k in self.cache_stats.keys())}
            }

class ContentOptimizer:
    """Content optimization and transformation"""

    def __init__(self):
        self.optimization_rules = self._load_optimization_rules()

    def _load_optimization_rules(self) -> Dict[str, ContentOptimization]:
        """Load content optimization rules"""
        return {
            'html': ContentOptimization(
                minify_html=True,
                minify_css=True,
                minify_js=True,
                optimize_images=False,
                webp_conversion=False,
                lazy_loading=True,
                resource_hints=True,
                compression=CompressionType.GZIP,
                cache_control="public, max-age=3600"
            ),
            'css': ContentOptimization(
                minify_html=False,
                minify_css=True,
                minify_js=False,
                optimize_images=False,
                webp_conversion=False,
                lazy_loading=False,
                resource_hints=False,
                compression=CompressionType.GZIP,
                cache_control="public, max-age=86400"
            ),
            'js': ContentOptimization(
                minify_html=False,
                minify_css=False,
                minify_js=True,
                optimize_images=False,
                webp_conversion=False,
                lazy_loading=False,
                resource_hints=False,
                compression=CompressionType.GZIP,
                cache_control="public, max-age=86400"
            ),
            'image': ContentOptimization(
                minify_html=False,
                minify_css=False,
                minify_js=False,
                optimize_images=True,
                webp_conversion=True,
                lazy_loading=True,
                resource_hints=False,
                compression=CompressionType.NONE,
                cache_control="public, max-age=604800"
            )
        }

    async def optimize_content(self, content: bytes, content_type: str,
                             optimization: ContentOptimization = None) -> Tuple[bytes, Dict[str, Any]]:
        """Optimize content based on type and rules"""
        if optimization is None:
            # Get default optimization for content type
            content_category = self._get_content_category(content_type)
            optimization = self.optimization_rules.get(content_category)

        if not optimization:
            return content, {'optimized': False, 'original_size': len(content)}

        optimized_content = content
        optimization_info = {
            'optimized': False,
            'original_size': len(content),
            'optimizations_applied': []
        }

        # Apply minification
        if content_type.startswith('text/') and optimization.minify_html:
            try:
                # Simple minification (in production, use proper minifiers)
                if content_type == 'text/html':
                    optimized_content = self._minify_html(optimized_content.decode()).encode()
                    optimization_info['optimizations_applied'].append('html_minified')
                elif content_type == 'text/css':
                    optimized_content = self._minify_css(optimized_content.decode()).encode()
                    optimization_info['optimizations_applied'].append('css_minified')
                elif content_type == 'application/javascript':
                    optimized_content = self._minify_js(optimized_content.decode()).encode()
                    optimization_info['optimizations_applied'].append('js_minified')

            except Exception as e:
                logger.warning(f"Content minification failed: {e}")

        # Apply compression
        if optimization.compression != CompressionType.NONE:
            if optimization.compression == CompressionType.GZIP:
                compressed = gzip.compress(optimized_content)
                if len(compressed) < len(optimized_content):
                    optimized_content = compressed
                    optimization_info['optimizations_applied'].append('gzip_compressed')
            elif optimization.compression == CompressionType.AUTO:
                # Auto-compress if beneficial
                compressed = gzip.compress(optimized_content)
                if len(compressed) < len(optimized_content) * 0.8:
                    optimized_content = compressed
                    optimization_info['optimizations_applied'].append('auto_compressed')

        optimization_info['final_size'] = len(optimized_content)
        optimization_info['compression_ratio'] = len(optimized_content) / len(content)
        optimization_info['optimized'] = len(optimized_content) < len(content)

        return optimized_content, optimization_info

    def _get_content_category(self, content_type: str) -> str:
        """Get content category for optimization rules"""
        if content_type.startswith('text/html'):
            return 'html'
        elif content_type == 'text/css':
            return 'css'
        elif content_type in ['application/javascript', 'text/javascript']:
            return 'js'
        elif content_type.startswith('image/'):
            return 'image'
        else:
            return 'other'

    def _minify_html(self, html: str) -> str:
        """Simple HTML minification"""
        import re
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        # Remove whitespace between tags
        html = re.sub(r'>\s+<', '><', html)
        # Remove multiple spaces
        html = re.sub(r'\s+', ' ', html)
        return html.strip()

    def _minify_css(self, css: str) -> str:
        """Simple CSS minification"""
        import re
        # Remove comments
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
        # Remove whitespace
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r';\s*}', '}', css)
        return css.strip()

    def _minify_js(self, js: str) -> str:
        """Simple JavaScript minification"""
        import re
        # Remove comments
        js = re.sub(r'//.*?\n', '\n', js)
        js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
        # Remove whitespace (careful with JavaScript)
        js = re.sub(r'\s+', ' ', js)
        return js.strip()

class GeoDNSRouter:
    """Geographic DNS routing for optimal CDN node selection"""

    def __init__(self, geoip_db_path: str = "data/GeoLite2-City.mmdb"):
        self.geoip_db_path = geoip_db_path
        try:
            self.reader = geoip2.database.Reader(geoip_db_path)
        except FileNotFoundError:
            logger.warning(f"GeoIP database not found at {geoip_db_path}")
            self.reader = None

        self.routing_table = {}
        self.performance_history = defaultdict(list)

    def get_client_location(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get client geographic location"""
        if not self.reader:
            return None

        try:
            response = self.reader.city(ip_address)
            return {
                'country': response.country.iso_code or "Unknown",
                'region': response.subdivisions.most_specific.iso_code or "Unknown",
                'city': response.city.name or "Unknown",
                'latitude': response.location.latitude or 0.0,
                'longitude': response.location.longitude or 0.0,
                'timezone': response.location.time_zone or "UTC"
            }
        except Exception as e:
            logger.warning(f"Failed to resolve location for {ip_address}: {e}")
            return None

    def select_optimal_node(self, client_ip: str, available_nodes: List[CDNNode],
                          content_type: str = None) -> CDNNode:
        """Select optimal CDN node based on geography and performance"""
        client_location = self.get_client_location(client_ip)

        if not client_location:
            # Fallback to random selection
            return random.choice(available_nodes)

        # Score nodes based on multiple factors
        scored_nodes = []
        for node in available_nodes:
            score = self._calculate_node_score(node, client_location, content_type)
            scored_nodes.append((node, score))

        # Select node with highest score
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        return scored_nodes[0][0]

    def _calculate_node_score(self, node: CDNNode, client_location: Dict[str, Any],
                            content_type: str = None) -> float:
        """Calculate score for a node based on various factors"""
        score = 0.0

        # Geographic distance (closer is better)
        if node.latitude != 0 and node.longitude != 0:
            distance = self._calculate_distance(
                client_location['latitude'], client_location['longitude'],
                node.latitude, node.longitude
            )
            # Convert distance to score (0-100, closer is higher)
            distance_score = max(0, 100 - (distance / 100))  # 100km per point penalty
            score += distance_score * 0.4

        # Load factor (less loaded is better)
        load_score = (1 - node.current_load) * 100
        score += load_score * 0.3

        # Cache hit rate (higher is better)
        cache_score = node.cache_hit_rate * 100
        score += cache_score * 0.2

        # Response time (lower is better)
        response_score = max(0, 100 - node.response_time)  # 1ms per point penalty
        score += response_score * 0.1

        return score

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two geographic points (km)"""
        import math

        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def update_node_performance(self, node_id: str, response_time: float, success: bool):
        """Update node performance history"""
        self.performance_history[node_id].append({
            'timestamp': datetime.utcnow(),
            'response_time': response_time,
            'success': success
        })

        # Keep only last 100 records
        if len(self.performance_history[node_id]) > 100:
            self.performance_history[node_id] = self.performance_history[node_id][-100:]

class CDNOptimizationSystem:
    """Main CDN optimization system"""

    def __init__(self, config_path: str = "config/cdn_config.json"):
        self.config = self._load_config(config_path)
        self.redis_client = redis.Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            decode_responses=True
        )

        self.cdn_nodes = self._load_cdn_nodes()
        self.cache_manager = EdgeCacheManager(self.redis_client)
        self.content_optimizer = ContentOptimizer()
        self.geo_router = GeoDNSRouter(self.config.get('geoip_db_path'))

        # Initialize CDN provider clients
        self.cdn_clients = self._initialize_cdn_clients()

        # Start background tasks
        asyncio.create_task(self._monitor_cdn_performance())
        asyncio.create_task(self._optimize_cache_distribution())
        asyncio.create_task(self._cleanup_expired_content())

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
                'default_ttl': 3600,
                'max_cache_size': 1024 * 1024 * 1024,  # 1GB
                'optimization_interval': 300,
                'cleanup_interval': 3600
            }

    def _load_cdn_nodes(self) -> List[CDNNode]:
        """Load CDN node configurations"""
        nodes = []

        # Default CDN nodes (in production, load from configuration)
        default_nodes = [
            {
                'node_id': 'cf_east_us',
                'provider': CDNProvider.CLOUDFLARE,
                'region': 'us-east-1',
                'country': 'US',
                'city': 'New York',
                'latitude': 40.7128,
                'longitude': -74.0060,
                'capacity': 0.3,
                'current_load': 0.1,
                'cache_size': 500 * 1024 * 1024,  # 500MB
                'cache_hit_rate': 0.85,
                'response_time': 45.0,
                'bandwidth_mbps': 1000,
                'is_active': True,
                'supported_features': ['gzip', 'brotli', 'http2', 'ipv6'],
                'endpoints': ['https://cdn.dmlogn8n.com', 'https://static.dmlogn8n.com']
            },
            {
                'node_id': 'cf_west_us',
                'provider': CDNProvider.CLOUDFLARE,
                'region': 'us-west-2',
                'country': 'US',
                'city': 'San Francisco',
                'latitude': 37.7749,
                'longitude': -122.4194,
                'capacity': 0.25,
                'current_load': 0.15,
                'cache_size': 400 * 1024 * 1024,  # 400MB
                'cache_hit_rate': 0.82,
                'response_time': 50.0,
                'bandwidth_mbps': 800,
                'is_active': True,
                'supported_features': ['gzip', 'brotli', 'http2', 'ipv6'],
                'endpoints': ['https://cdn-west.dmlogn8n.com']
            },
            {
                'node_id': 'aws_europe',
                'provider': CDNProvider.AWS_CLOUDFRONT,
                'region': 'eu-west-1',
                'country': 'IE',
                'city': 'Dublin',
                'latitude': 53.3498,
                'longitude': -6.2603,
                'capacity': 0.2,
                'current_load': 0.08,
                'cache_size': 300 * 1024 * 1024,  # 300MB
                'cache_hit_rate': 0.88,
                'response_time': 35.0,
                'bandwidth_mbps': 600,
                'is_active': True,
                'supported_features': ['gzip', 'http2', 'ipv6'],
                'endpoints': ['https://cdn-eu.dmlogn8n.com']
            }
        ]

        for node_config in default_nodes:
            node = CDNNode(**node_config)
            nodes.append(node)

        return nodes

    def _initialize_cdn_clients(self) -> Dict[CDNProvider, Any]:
        """Initialize CDN provider clients"""
        clients = {}

        try:
            # Cloudflare client
            if self.config.get('cloudflare_api_token'):
                clients[CDNProvider.CLOUDFLARE] = cloudflare.Cloudflare(
                    api_token=self.config['cloudflare_api_token']
                )
        except Exception as e:
            logger.warning(f"Failed to initialize Cloudflare client: {e}")

        try:
            # AWS CloudFront client
            if self.config.get('aws_access_key') and self.config.get('aws_secret_key'):
                clients[CDNProvider.AWS_CLOUDFRONT] = boto3.client(
                    'cloudfront',
                    aws_access_key_id=self.config['aws_access_key'],
                    aws_secret_access_key=self.config['aws_secret_key']
                )
        except Exception as e:
            logger.warning(f"Failed to initialize AWS CloudFront client: {e}")

        return clients

    async def serve_content(self, client_ip: str, request_path: str,
                          headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Serve content through optimal CDN node"""
        start_time = time.time()

        # Generate content ID
        content_id = hashlib.md5(f"{request_path}{headers or {}}".encode()).hexdigest()

        # Determine content type
        content_type = self._determine_content_type(request_path)

        # Select optimal CDN node
        available_nodes = [n for n in self.cdn_nodes if n.is_active]
        optimal_node = self.geo_router.select_optimal_node(client_ip, available_nodes, content_type)

        # Try to get from edge cache
        cached_content = await self.cache_manager.get_cached_content(content_id, optimal_node.node_id)

        if cached_content:
            # Cache hit
            response_time = time.time() - start_time
            self.geo_router.update_node_performance(optimal_node.node_id, response_time * 1000, True)

            return {
                'success': True,
                'content': cached_content,
                'content_type': content_type,
                'cache_hit': True,
                'cdn_node': optimal_node.node_id,
                'response_time': response_time,
                'headers': {
                    'X-Cache': 'HIT',
                    'X-CDN-Node': optimal_node.node_id,
                    'X-Response-Time': f"{response_time:.3f}"
                }
            }

        # Cache miss - fetch from origin and cache
        try:
            # Fetch from origin server
            origin_content = await self._fetch_from_origin(request_path, headers)

            if origin_content['success']:
                content = origin_content['content']
                original_content_type = origin_content.get('content_type', content_type)

                # Optimize content
                optimized_content, optimization_info = await self.content_optimizer.optimize_content(
                    content, original_content_type
                )

                # Cache on edge node
                ttl = self._determine_ttl(request_path, original_content_type)
                await self.cache_manager.cache_content(
                    content_id, optimized_content, optimal_node.node_id, ttl, original_content_type
                )

                response_time = time.time() - start_time
                self.geo_router.update_node_performance(optimal_node.node_id, response_time * 1000, True)

                return {
                    'success': True,
                    'content': optimized_content,
                    'content_type': original_content_type,
                    'cache_hit': False,
                    'cdn_node': optimal_node.node_id,
                    'response_time': response_time,
                    'optimization_info': optimization_info,
                    'headers': {
                        'X-Cache': 'MISS',
                        'X-CDN-Node': optimal_node.node_id,
                        'X-Response-Time': f"{response_time:.3f}",
                        'Cache-Control': f"max-age={ttl}"
                    }
                }
            else:
                # Origin fetch failed
                response_time = time.time() - start_time
                return {
                    'success': False,
                    'error': 'Origin fetch failed',
                    'cdn_node': optimal_node.node_id,
                    'response_time': response_time,
                    'status_code': origin_content.get('status_code', 502)
                }

        except Exception as e:
            logger.error(f"Error serving content {request_path}: {e}")
            response_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'cdn_node': optimal_node.node_id,
                'response_time': response_time
            }

    def _determine_content_type(self, request_path: str) -> str:
        """Determine content type from file path"""
        content_type, _ = mimetypes.guess_type(request_path)
        return content_type or 'application/octet-stream'

    def _determine_ttl(self, request_path: str, content_type: str) -> int:
        """Determine TTL for content based on type and path"""
        if content_type.startswith('image/'):
            return 604800  # 7 days
        elif content_type in ['text/css', 'application/javascript']:
            return 86400  # 1 day
        elif content_type.startswith('text/html'):
            return 3600  # 1 hour
        elif 'api' in request_path:
            return 300  # 5 minutes
        else:
            return 3600  # 1 hour default

    async def _fetch_from_origin(self, request_path: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Fetch content from origin server"""
        try:
            origin_url = f"http://localhost:8080{request_path}"  # Default origin

            async with aiohttp.ClientSession() as session:
                async with session.get(origin_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('Content-Type', 'application/octet-stream')

                        return {
                            'success': True,
                            'content': content,
                            'content_type': content_type,
                            'status_code': response.status
                        }
                    else:
                        return {
                            'success': False,
                            'status_code': response.status,
                            'error': f"HTTP {response.status}"
                        }

        except Exception as e:
            logger.error(f"Error fetching from origin: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def invalidate_content(self, request_path: str, node_id: str = None) -> bool:
        """Invalidate content across CDN"""
        try:
            content_id = hashlib.md5(request_path.encode()).hexdigest()
            return await self.cache_manager.invalidate_cache(content_id, node_id)

        except Exception as e:
            logger.error(f"Error invalidating content {request_path}: {e}")
            return False

    async def purge_all_cache(self) -> bool:
        """Purge all cached content"""
        try:
            # Clear Redis cache
            pattern = "edge_cache:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)

            pattern = "edge_metadata:*"
            metadata_keys = self.redis_client.keys(pattern)
            if metadata_keys:
                self.redis_client.delete(*metadata_keys)

            logger.info("Purged all cached content")
            return True

        except Exception as e:
            logger.error(f"Error purging cache: {e}")
            return False

    async def _monitor_cdn_performance(self):
        """Monitor CDN node performance"""
        while True:
            try:
                for node in self.cdn_nodes:
                    if not node.is_active:
                        continue

                    # Simulate performance metrics (in production, get from CDN APIs)
                    node.current_load = min(1.0, node.current_load + random.uniform(-0.1, 0.1))
                    node.cache_hit_rate = max(0.5, min(1.0, node.cache_hit_rate + random.uniform(-0.05, 0.05)))
                    node.response_time = max(10, node.response_time + random.uniform(-5, 5))

                    # Record metrics
                    metrics = CDNMetrics(
                        timestamp=datetime.utcnow(),
                        node_id=node.node_id,
                        request_count=random.randint(100, 1000),
                        cache_hits=int(random.randint(100, 1000) * node.cache_hit_rate),
                        cache_misses=int(random.randint(100, 1000) * (1 - node.cache_hit_rate)),
                        bytes_served=random.randint(1000000, 10000000),
                        avg_response_time=node.response_time,
                        error_count=random.randint(0, 5),
                        bandwidth_utilization=node.current_load,
                        cpu_utilization=random.uniform(0.2, 0.8)
                    )

                    # Store metrics in Redis
                    metrics_key = f"cdn_metrics:{node.node_id}:{int(time.time())}"
                    self.redis_client.setex(metrics_key, 86400, json.dumps(asdict(metrics), default=str))

                await asyncio.sleep(60)  # Monitor every minute

            except Exception as e:
                logger.error(f"Error in CDN performance monitoring: {e}")
                await asyncio.sleep(30)

    async def _optimize_cache_distribution(self):
        """Optimize cache distribution across nodes"""
        while True:
            try:
                # Analyze cache hit rates and redistribute popular content
                cache_stats = self.cache_manager.get_cache_stats()

                for node_id, stats in cache_stats.get('node_stats', {}).items():
                    if stats['hit_rate'] < 70:  # Low hit rate
                        logger.info(f"Low cache hit rate on {node_id}: {stats['hit_rate']:.1f}%")
                        # TODO: Implement cache warming/preloading logic

                await asyncio.sleep(self.config.get('optimization_interval', 300))

            except Exception as e:
                logger.error(f"Error in cache optimization: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_content(self):
        """Clean up expired cached content"""
        while True:
            try:
                # Redis automatically handles TTL, but we can do additional cleanup
                logger.info("Running cache cleanup")
                # TODO: Implement additional cleanup logic

                await asyncio.sleep(self.config.get('cleanup_interval', 3600))

            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(300)

    async def get_cdn_stats(self) -> Dict[str, Any]:
        """Get comprehensive CDN statistics"""
        stats = {
            'total_nodes': len(self.cdn_nodes),
            'active_nodes': len([n for n in self.cdn_nodes if n.is_active]),
            'nodes': [],
            'cache_stats': self.cache_manager.get_cache_stats(),
            'geo_routing_stats': {}
        }

        for node in self.cdn_nodes:
            node_stats = {
                'id': node.node_id,
                'provider': node.provider.value,
                'region': node.region,
                'country': node.country,
                'city': node.city,
                'is_active': node.is_active,
                'current_load': node.current_load,
                'cache_hit_rate': node.cache_hit_rate,
                'response_time': node.response_time,
                'bandwidth_mbps': node.bandwidth_mbps,
                'capacity': node.capacity
            }
            stats['nodes'].append(node_stats)

        # Get recent performance metrics
        for node in self.cdn_nodes:
            if node.is_active:
                # Get last hour of metrics
                end_time = int(time.time())
                start_time = end_time - 3600

                metrics = []
                for ts in range(start_time, end_time, 60):
                    metrics_key = f"cdn_metrics:{node.node_id}:{ts}"
                    metric_data = self.redis_client.get(metrics_key)
                    if metric_data:
                        metrics.append(json.loads(metric_data))

                if metrics:
                    avg_response_time = statistics.mean(m['avg_response_time'] for m in metrics)
                    total_requests = sum(m['request_count'] for m in metrics)
                    total_bytes = sum(m['bytes_served'] for m in metrics)
                    avg_hit_rate = statistics.mean(m['cache_hits'] / max(1, m['request_count']) * 100 for m in metrics)

                    stats['geo_routing_stats'][node.node_id] = {
                        'avg_response_time': avg_response_time,
                        'total_requests': total_requests,
                        'total_bytes_served': total_bytes,
                        'avg_cache_hit_rate': avg_hit_rate
                    }

        return stats

async def main():
    """Main entry point"""
    cdn_system = CDNOptimizationSystem()

    # Example usage
    while True:
        try:
            # Simulate client requests
            client_ip = "192.168.1.100"
            request_path = "/static/css/styles.css"

            result = await cdn_system.serve_content(client_ip, request_path)
            print(f"Request result: {result['success']}, Cache hit: {result.get('cache_hit', False)}")

            await asyncio.sleep(2)

        except KeyboardInterrupt:
            logger.info("Shutting down CDN system")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())