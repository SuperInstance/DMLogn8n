#!/usr/bin/env python3
"""
Advanced Network Optimizer for DMLogn8n Platform
Network latency optimization, bandwidth management, connection pooling, and protocol optimization
"""

import asyncio
import gzip
import json
import logging
import socket
import ssl
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import hashlib
import zlib
import struct
import weakref

# Network libraries
try:
    import aiohttp
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    import requests.adapters
    from requests.packages.urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Network protocol types"""
    HTTP = "http"
    HTTPS = "https"
    WEBSOCKET = "websocket"
    TCP = "tcp"
    UDP = "udp"
    GRPC = "grpc"

class CompressionType(Enum):
    """Compression algorithms"""
    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "brotli"
    LZ4 = "lz4"
    ZSTD = "zstd"

class OptimizationStrategy(Enum):
    """Network optimization strategies"""
    LATENCY = "latency"          # Prioritize low latency
    THROUGHPUT = "throughput"    # Prioritize high throughput
    BALANCED = "balanced"        # Balance between latency and throughput
    BANDWIDTH = "bandwidth"      # Prioritize bandwidth efficiency

@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    timestamp: datetime
    protocol: ProtocolType
    endpoint: str
    request_size_bytes: int
    response_size_bytes: int
    latency_ms: float
    throughput_mbps: float
    connection_time_ms: float
    dns_lookup_time_ms: float
    ssl_handshake_time_ms: float = 0.0
    compression_ratio: float = 1.0
    error_count: int = 0
    timeout_count: int = 0
    retry_count: int = 0

@dataclass
class ConnectionPool:
    """Connection pool configuration"""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: float = 3600.0
    keep_alive: bool = True
    keep_alive_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.3

@dataclass
class NetworkConfig:
    """Network configuration"""
    protocol: ProtocolType
    host: str
    port: int
    ssl_enabled: bool = False
    ssl_verify: bool = True
    timeout: float = 30.0
    connection_pool: ConnectionPool = field(default_factory=ConnectionPool)
    compression: bool = True
    compression_type: CompressionType = CompressionType.GZIP
    chunk_size: int = 8192
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED

class NetworkOptimizer:
    """Advanced network optimization and performance tuning system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.connections = {}
        self.connection_pools = {}
        self.metrics_history = deque(maxlen=self.config.get('history_size', 10000))
        self.endpoint_stats = defaultdict(list)

        # Optimization settings
        self.auto_compression = self.config.get('auto_compression', True)
        self.connection_pooling = self.config.get('connection_pooling', True)
        self.adaptive_timeout = self.config.get('adaptive_timeout', True)
        self.bandwidth_throttling = self.config.get('bandwidth_throttling', False)

        # Performance thresholds
        self.latency_threshold = self.config.get('latency_threshold', 1000.0)  # ms
        self.throughput_threshold = self.config.get('throughput_threshold', 10.0)  # Mbps
        self.error_rate_threshold = self.config.get('error_rate_threshold', 0.05)  # 5%

        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        # HTTP session pools
        self.http_sessions = {}
        self.async_http_sessions = {}

        # Bandwidth management
        self.bandwidth_limits = {}
        self.current_bandwidth_usage = {}

        # Compression engines
        self.compression_engines = self._initialize_compression_engines()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'history_size': 10000,
            'latency_threshold': 1000.0,  # ms
            'throughput_threshold': 10.0,  # Mbps
            'error_rate_threshold': 0.05,  # 5%
            'auto_compression': True,
            'connection_pooling': True,
            'adaptive_timeout': True,
            'bandwidth_throttling': False,
            'monitoring_interval': 60.0,
            'optimization_interval': 300.0,
            'default_pool_size': 10,
            'max_connections_per_host': 50,
            'compression_threshold': 1024,  # bytes
            'keep_alive_timeout': 30.0,
            'connection_timeout': 10.0,
            'read_timeout': 30.0,
            'max_retries': 3,
            'retry_backoff_factor': 0.3
        }

    def _initialize_compression_engines(self) -> Dict[CompressionType, Callable]:
        """Initialize compression engines"""
        engines = {
            CompressionType.GZIP: self._compress_gzip,
            CompressionType.DEFLATE: self._compress_deflate,
        }

        # Add optional compression engines
        try:
            import brotli
            engines[CompressionType.BROTLI] = self._compress_brotli
        except ImportError:
            logger.debug("Brotli compression not available")

        try:
            import lz4.frame
            engines[CompressionType.LZ4] = self._compress_lz4
        except ImportError:
            logger.debug("LZ4 compression not available")

        try:
            import zstandard as zstd
            engines[CompressionType.ZSTD] = self._compress_zstd
        except ImportError:
            logger.debug("Zstandard compression not available")

        return engines

    def start_monitoring(self):
        """Start network performance monitoring"""
        if self.monitoring_active:
            logger.warning("Network monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Network monitoring started")

    def stop_monitoring(self):
        """Stop network monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Network monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Analyze network performance
                self._analyze_network_performance()

                # Optimize connection pools
                self._optimize_connection_pools()

                # Adjust timeouts based on performance
                if self.adaptive_timeout:
                    self._adjust_timeouts()

                # Check bandwidth usage
                if self.bandwidth_throttling:
                    self._monitor_bandwidth_usage()

                time.sleep(self.config.get('monitoring_interval', 60.0))

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

    async def make_request(self, config: NetworkConfig, method: str = "GET",
                          url: str = None, headers: Dict[str, str] = None,
                          data: Any = None, params: Dict[str, Any] = None) -> Any:
        """Make optimized HTTP request"""
        if url is None:
            url = f"{config.protocol.value}://{config.host}:{config.port}"

        start_time = time.time()
        metrics = NetworkMetrics(
            timestamp=datetime.now(),
            protocol=config.protocol,
            endpoint=url,
            request_size_bytes=len(str(data).encode()) if data else 0,
            response_size_bytes=0,
            latency_ms=0,
            throughput_mbps=0,
            connection_time_ms=0,
            dns_lookup_time_ms=0
        )

        try:
            # Get or create HTTP session
            session = await self._get_http_session(config)

            # Prepare request
            request_headers = headers.copy() if headers else {}

            # Add compression headers
            if config.compression and self.auto_compression:
                request_headers['Accept-Encoding'] = self._get_accept_encoding_header()

            # Compress request data if applicable
            compressed_data = None
            if data and config.compression and self._should_compress_data(data):
                compressed_data = self._compress_data(data, config.compression_type)
                request_headers['Content-Encoding'] = config.compression_type.value
                metrics.request_size_bytes = len(compressed_data)

            # Make request with timing
            connection_start = time.time()

            async with session.request(
                method=method,
                url=url,
                headers=request_headers,
                data=compressed_data or data,
                params=params,
                timeout=aiohttp.ClientTimeout(
                    total=config.timeout,
                    connect=self.config.get('connection_timeout', 10.0),
                    sock_read=self.config.get('read_timeout', 30.0)
                )
            ) as response:

                connection_time = (time.time() - connection_start) * 1000
                metrics.connection_time_ms = connection_time

                # Read response
                content_start = time.time()
                content = await response.read()
                content_time = time.time() - content_start

                # Decompress response if needed
                if response.headers.get('Content-Encoding'):
                    content = self._decompress_data(
                        content,
                        response.headers['Content-Encoding']
                    )

                metrics.response_size_bytes = len(content)
                metrics.latency_ms = (time.time() - start_time) * 1000

                # Calculate throughput
                if content_time > 0:
                    metrics.throughput_mbps = (len(content) * 8) / (content_time * 1024 * 1024)

                # Store metrics
                self.metrics_history.append(metrics)
                self.endpoint_stats[url].append(metrics)

                # Check performance thresholds
                self._check_performance_thresholds(metrics)

                return {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'metrics': metrics
                }

        except asyncio.TimeoutError:
            metrics.timeout_count += 1
            metrics.latency_ms = (time.time() - start_time) * 1000
            self.metrics_history.append(metrics)
            logger.warning(f"Request timeout for {url}")
            raise

        except Exception as e:
            metrics.error_count += 1
            metrics.latency_ms = (time.time() - start_time) * 1000
            self.metrics_history.append(metrics)
            logger.error(f"Request failed for {url}: {e}")
            raise

    async def _get_http_session(self, config: NetworkConfig) -> aiohttp.ClientSession:
        """Get or create HTTP session with optimal configuration"""
        session_key = f"{config.host}:{config.port}"

        if session_key not in self.async_http_sessions:
            # Configure connector
            connector_config = {
                'limit': self.config.get('max_connections_per_host', 50),
                'limit_per_host': config.connection_pool.pool_size,
                'ttl_dns_cache': 300,
                'use_dns_cache': True,
                'keepalive_timeout': config.connection_pool.keep_alive_timeout,
                'enable_cleanup_closed': True,
                'ssl': config.ssl_verify if config.ssl_enabled else False
            }

            if config.protocol == ProtocolType.HTTPS:
                connector_config['ssl'] = ssl.create_default_context()
                if not config.ssl_verify:
                    connector_config['ssl'].check_hostname = False
                    connector_config['ssl'].verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(**connector_config)

            # Configure timeout
            timeout = aiohttp.ClientTimeout(
                total=config.timeout,
                connect=self.config.get('connection_timeout', 10.0),
                sock_read=self.config.get('read_timeout', 30.0)
            )

            # Create session
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'DMLogn8n-NetworkOptimizer/1.0',
                    'Connection': 'keep-alive'
                }
            )

            self.async_http_sessions[session_key] = session

        return self.async_http_sessions[session_key]

    def _get_accept_encoding_header(self) -> str:
        """Get Accept-Encoding header based on available compression"""
        available_encodings = ['gzip', 'deflate']

        if CompressionType.BROTLI in self.compression_engines:
            available_encodings.append('br')
        if CompressionType.LZ4 in self.compression_engines:
            available_encodings.append('lz4')
        if CompressionType.ZSTD in self.compression_engines:
            available_encodings.append('zstd')

        return ', '.join(available_encodings)

    def _should_compress_data(self, data: Any) -> bool:
        """Check if data should be compressed"""
        try:
            data_size = len(str(data).encode())
            return data_size > self.config.get('compression_threshold', 1024)
        except:
            return False

    def _compress_data(self, data: Any, compression_type: CompressionType) -> bytes:
        """Compress data using specified algorithm"""
        if compression_type not in self.compression_engines:
            logger.warning(f"Compression type {compression_type.value} not available, using gzip")
            compression_type = CompressionType.GZIP

        try:
            data_bytes = str(data).encode('utf-8')
            return self.compression_engines[compression_type](data_bytes)
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return str(data).encode('utf-8')

    def _decompress_data(self, data: bytes, encoding: str) -> bytes:
        """Decompress data based on encoding"""
        try:
            if encoding == 'gzip':
                return gzip.decompress(data)
            elif encoding == 'deflate':
                return zlib.decompress(data)
            elif encoding == 'br':
                import brotli
                return brotli.decompress(data)
            elif encoding == 'lz4':
                import lz4.frame
                return lz4.frame.decompress(data)
            elif encoding == 'zstd':
                import zstandard as zstd
                return zstd.decompress(data)
            else:
                return data
        except Exception as e:
            logger.error(f"Decompression failed for {encoding}: {e}")
            return data

    def _compress_gzip(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data)

    def _compress_deflate(self, data: bytes) -> bytes:
        """Compress data using deflate"""
        return zlib.compress(data)

    def _compress_brotli(self, data: bytes) -> bytes:
        """Compress data using brotli"""
        import brotli
        return brotli.compress(data)

    def _compress_lz4(self, data: bytes) -> bytes:
        """Compress data using LZ4"""
        import lz4.frame
        return lz4.frame.compress(data)

    def _compress_zstd(self, data: bytes) -> bytes:
        """Compress data using Zstandard"""
        import zstandard as zstd
        compressor = zstd.ZstdCompressor()
        return compressor.compress(data)

    def _check_performance_thresholds(self, metrics: NetworkMetrics):
        """Check if performance thresholds are exceeded"""
        if metrics.latency_ms > self.latency_threshold:
            logger.warning(f"High latency detected: {metrics.latency_ms:.2f}ms for {metrics.endpoint}")

        if metrics.throughput_mbps < self.throughput_threshold and metrics.response_size_bytes > 0:
            logger.warning(f"Low throughput detected: {metrics.throughput_mbps:.2f}Mbps for {metrics.endpoint}")

        # Check error rate
        recent_metrics = [m for m in self.metrics_history[-100:] if m.endpoint == metrics.endpoint]
        if len(recent_metrics) >= 10:
            error_rate = sum(m.error_count for m in recent_metrics) / len(recent_metrics)
            if error_rate > self.error_rate_threshold:
                logger.warning(f"High error rate detected: {error_rate:.2%} for {metrics.endpoint}")

    def _analyze_network_performance(self):
        """Analyze network performance patterns"""
        if len(self.metrics_history) < 10:
            return

        recent_metrics = list(self.metrics_history)[-100:]

        # Group by endpoint
        endpoint_performance = defaultdict(list)
        for metric in recent_metrics:
            endpoint_performance[metric.endpoint].append(metric)

        # Analyze each endpoint
        for endpoint, metrics in endpoint_performance.items():
            if len(metrics) < 5:
                continue

            latencies = [m.latency_ms for m in metrics]
            throughputs = [m.throughput_mbps for m in metrics if m.throughput_mbps > 0]
            errors = [m.error_count for m in metrics]

            avg_latency = np.mean(latencies)
            avg_throughput = np.mean(throughputs) if throughputs else 0
            error_rate = sum(errors) / len(metrics)

            # Identify performance issues
            if avg_latency > self.latency_threshold:
                logger.warning(f"Endpoint {endpoint} has high average latency: {avg_latency:.2f}ms")

            if avg_throughput < self.throughput_threshold and avg_throughput > 0:
                logger.warning(f"Endpoint {endpoint} has low average throughput: {avg_throughput:.2f}Mbps")

            if error_rate > self.error_rate_threshold:
                logger.warning(f"Endpoint {endpoint} has high error rate: {error_rate:.2%}")

    def _optimize_connection_pools(self):
        """Optimize connection pool sizes based on usage"""
        for endpoint, metrics in self.endpoint_stats.items():
            if len(metrics) < 20:
                continue

            # Analyze connection usage patterns
            recent_metrics = metrics[-20:]
            concurrent_requests = len([m for m in recent_metrics
                                     if (m.timestamp - recent_metrics[0].timestamp).total_seconds() < 1])

            # Adjust pool size if needed
            current_pool_size = self.config.get('default_pool_size', 10)
            optimal_size = min(max(concurrent_requests * 2, 5), 50)  # Between 5 and 50

            if optimal_size != current_pool_size:
                logger.info(f"Recommending pool size adjustment for {endpoint}: {current_pool_size} -> {optimal_size}")

    def _adjust_timeouts(self):
        """Adjust timeouts based on performance patterns"""
        recent_metrics = list(self.metrics_history)[-50:]

        if len(recent_metrics) < 10:
            return

        # Calculate average latency and standard deviation
        latencies = [m.latency_ms for m in recent_metrics]
        avg_latency = np.mean(latencies)
        std_latency = np.std(latencies)

        # Set timeout to average + 3 standard deviations
        recommended_timeout = max(avg_latency + (3 * std_latency), 5000)  # Minimum 5 seconds

        current_timeout = self.config.get('connection_timeout', 10.0) * 1000

        if abs(recommended_timeout - current_timeout) > current_timeout * 0.2:  # 20% difference
            logger.info(f"Recommending timeout adjustment: {current_timeout/1000:.1f}s -> {recommended_timeout/1000:.1f}s")

    def _monitor_bandwidth_usage(self):
        """Monitor and control bandwidth usage"""
        current_time = time.time()
        recent_window = 300  # 5 minutes

        # Calculate recent bandwidth usage per endpoint
        for endpoint, metrics in self.endpoint_stats.items():
            recent_metrics = [m for m in metrics
                            if (current_time - m.timestamp.timestamp()) < recent_window]

            if not recent_metrics:
                continue

            total_bytes = sum(m.response_size_bytes + m.request_size_bytes for m in recent_metrics)
            bandwidth_mbps = (total_bytes * 8) / (recent_window * 1024 * 1024)

            self.current_bandwidth_usage[endpoint] = bandwidth_mbps

            # Check against limits
            if endpoint in self.bandwidth_limits:
                limit = self.bandwidth_limits[endpoint]
                if bandwidth_mbps > limit:
                    logger.warning(f"Bandwidth limit exceeded for {endpoint}: {bandwidth_mbps:.2f}Mbps > {limit:.2f}Mbps")
                    # TODO: Implement throttling mechanism

    def set_bandwidth_limit(self, endpoint: str, limit_mbps: float):
        """Set bandwidth limit for endpoint"""
        self.bandwidth_limits[endpoint] = limit_mbps
        logger.info(f"Set bandwidth limit for {endpoint}: {limit_mbps:.2f}Mbps")

    async def create_websocket_connection(self, config: NetworkConfig) -> Any:
        """Create optimized WebSocket connection"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("WebSockets library not available")

        url = f"ws://{config.host}:{config.port}"
        if config.protocol == ProtocolType.WEBSOCKET and config.ssl_enabled:
            url = f"wss://{config.host}:{config.port}"

        try:
            # Configure WebSocket with optimization
            extra_headers = {
                'User-Agent': 'DMLogn8n-NetworkOptimizer/1.0'
            }

            if config.compression:
                extra_headers['Sec-WebSocket-Extensions'] = 'permessage-deflate'

            websocket = await websockets.connect(
                url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_size=2**20,  # 1MB
                max_queue=32
            )

            logger.info(f"WebSocket connection established: {url}")
            return websocket

        except Exception as e:
            logger.error(f"Failed to create WebSocket connection: {e}")
            raise

    def get_performance_report(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Generate comprehensive network performance report"""
        if time_window is None:
            time_window = timedelta(hours=24)

        cutoff_time = datetime.now() - time_window
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"error": "No network data available for specified time window"}

        # Calculate statistics
        latencies = [m.latency_ms for m in recent_metrics]
        throughputs = [m.throughput_mbps for m in recent_metrics if m.throughput_mbps > 0]
        request_sizes = [m.request_size_bytes for m in recent_metrics]
        response_sizes = [m.response_size_bytes for m in recent_metrics]

        # Protocol statistics
        protocol_stats = defaultdict(int)
        for metric in recent_metrics:
            protocol_stats[metric.protocol.value] += 1

        # Endpoint statistics
        endpoint_stats = {}
        for endpoint, metrics in self.endpoint_stats.items():
            endpoint_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            if endpoint_metrics:
                endpoint_latencies = [m.latency_ms for m in endpoint_metrics]
                endpoint_throughputs = [m.throughput_mbps for m in endpoint_metrics if m.throughput_mbps > 0]

                endpoint_stats[endpoint] = {
                    'request_count': len(endpoint_metrics),
                    'avg_latency_ms': np.mean(endpoint_latencies),
                    'max_latency_ms': np.max(endpoint_latencies),
                    'avg_throughput_mbps': np.mean(endpoint_throughputs) if endpoint_throughputs else 0,
                    'total_bytes': sum(m.request_size_bytes + m.response_size_bytes for m in endpoint_metrics),
                    'error_count': sum(m.error_count for m in endpoint_metrics),
                    'timeout_count': sum(m.timeout_count for m in endpoint_metrics)
                }

        report = {
            'time_window': str(time_window),
            'total_requests': len(recent_metrics),
            'protocol_distribution': dict(protocol_stats),
            'performance_stats': {
                'latency': {
                    'avg_ms': np.mean(latencies),
                    'median_ms': np.median(latencies),
                    'max_ms': np.max(latencies),
                    'min_ms': np.min(latencies),
                    'std_ms': np.std(latencies)
                },
                'throughput': {
                    'avg_mbps': np.mean(throughputs) if throughputs else 0,
                    'max_mbps': np.max(throughputs) if throughputs else 0,
                    'min_mbps': np.min(throughputs) if throughputs else 0
                },
                'data_transfer': {
                    'total_requests_mb': sum(request_sizes) / 1024 / 1024,
                    'total_responses_mb': sum(response_sizes) / 1024 / 1024,
                    'total_bytes': sum(request_sizes + response_sizes for request_sizes, response_sizes in zip(request_sizes, response_sizes))
                }
            },
            'endpoint_performance': endpoint_stats,
            'errors': {
                'total_errors': sum(m.error_count for m in recent_metrics),
                'total_timeouts': sum(m.timeout_count for m in recent_metrics),
                'error_rate': sum(m.error_count for m in recent_metrics) / len(recent_metrics)
            },
            'compression': {
                'enabled': self.auto_compression,
                'available_engines': list(self.compression_engines.keys())
            },
            'optimization_settings': {
                'connection_pooling': self.connection_pooling,
                'adaptive_timeout': self.adaptive_timeout,
                'bandwidth_throttling': self.bandwidth_throttling
            }
        }

        # Add recommendations
        report['recommendations'] = self._generate_network_recommendations(recent_metrics)

        return report

    def _generate_network_recommendations(self, metrics: List[NetworkMetrics]) -> List[str]:
        """Generate network optimization recommendations"""
        recommendations = []

        if not metrics:
            return recommendations

        latencies = [m.latency_ms for m in metrics]
        avg_latency = np.mean(latencies)

        # Latency recommendations
        if avg_latency > self.latency_threshold:
            recommendations.append("Consider implementing HTTP/2 or HTTP/3 for improved latency")
            recommendations.append("Review network routing and consider CDN implementation")

        # Throughput recommendations
        throughputs = [m.throughput_mbps for m in metrics if m.throughput_mbps > 0]
        if throughputs and np.mean(throughputs) < self.throughput_threshold:
            recommendations.append("Consider increasing compression levels or enabling more aggressive compression")
            recommendations.append("Review bandwidth capacity and consider upgrading network infrastructure")

        # Error rate recommendations
        error_rate = sum(m.error_count for m in metrics) / len(metrics)
        if error_rate > self.error_rate_threshold:
            recommendations.append("High error rate detected. Review retry mechanisms and circuit breaker patterns")
            recommendations.append("Consider implementing health checks and failover strategies")

        # Connection pooling recommendations
        if not self.connection_pooling:
            recommendations.append("Enable connection pooling to reduce connection overhead")

        # Compression recommendations
        if not self.auto_compression:
            recommendations.append("Enable compression to reduce bandwidth usage")

        # Bandwidth recommendations
        if self.bandwidth_throttling:
            recommendations.append("Monitor bandwidth usage and adjust limits based on application needs")

        return recommendations

    async def close_connections(self):
        """Close all network connections and sessions"""
        # Close async HTTP sessions
        for session in self.async_http_sessions.values():
            await session.close()
        self.async_http_sessions.clear()

        # Close sync HTTP sessions
        for session in self.http_sessions.values():
            session.close()
        self.http_sessions.clear()

        logger.info("All network connections closed")

    def cleanup_old_metrics(self, days: int = 7):
        """Clean up old performance metrics"""
        cutoff_time = datetime.now() - timedelta(days=days)

        # Clean up metrics history
        self.metrics_history = deque(
            [m for m in self.metrics_history if m.timestamp >= cutoff_time],
            maxlen=self.config.get('history_size', 10000)
        )

        # Clean up endpoint stats
        for endpoint in self.endpoint_stats:
            self.endpoint_stats[endpoint] = [
                m for m in self.endpoint_stats[endpoint] if m.timestamp >= cutoff_time
            ]

        logger.info(f"Cleaned up metrics older than {days} days")

# Network optimization decorator
def optimize_network(optimizer: NetworkOptimizer, config: NetworkConfig):
    """Decorator for network optimization"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract URL from function parameters or use a different approach
            # This is a simplified implementation
            url = kwargs.get('url') or getattr(func, '__url__', None)

            if url:
                method = kwargs.get('method', 'GET')
                result = await optimizer.make_request(config, method, url, kwargs.get('headers'),
                                                   kwargs.get('data'), kwargs.get('params'))
                return result
            else:
                # Fallback to original function
                return await func(*args, **kwargs)

        return async_wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize network optimizer
        optimizer = NetworkOptimizer({
            'auto_compression': True,
            'connection_pooling': True,
            'adaptive_timeout': True
        })

        # Start monitoring
        optimizer.start_monitoring()

        try:
            # Network configuration
            config = NetworkConfig(
                protocol=ProtocolType.HTTPS,
                host="httpbin.org",
                port=443,
                ssl_enabled=True,
                compression=True,
                compression_type=CompressionType.GZIP
            )

            # Make optimized request
            response = await optimizer.make_request(
                config=config,
                method="GET",
                url="https://httpbin.org/get",
                headers={"Accept": "application/json"}
            )

            print(f"Response status: {response['status_code']}")
            print(f"Response size: {len(response['content'])} bytes")
            print(f"Latency: {response['metrics'].latency_ms:.2f}ms")

            # Get performance report
            report = optimizer.get_performance_report()
            print(f"Network performance report: {json.dumps(report, indent=2, default=str)}")

            await asyncio.sleep(10)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Cleanup
            optimizer.stop_monitoring()
            await optimizer.close_connections()

    # Run example
    asyncio.run(main())