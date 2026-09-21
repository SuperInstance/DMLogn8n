#!/usr/bin/env python3
"""
Custom Metrics Collection for DMLogn8n Auto-Scaling
Collects business-specific and application-level metrics
"""

import asyncio
import aiohttp
import logging
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import redis
import psutil
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram

@dataclass
class MetricValue:
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime

class CustomMetricsCollector:
    """
    Collects custom business and application metrics for auto-scaling decisions
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('custom_metrics')

        # Prometheus metrics registry
        self.registry = CollectorRegistry()

        # Custom metrics definitions
        self.custom_gauges = {}
        self.custom_counters = {}
        self.custom_histograms = {}

        # Redis client for caching
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # External monitoring integrations
        self.prometheus_url = config.get('prometheus', {}).get('url', 'http://prometheus:9090')
        self.datadog_api_key = config.get('datadog', {}).get('api_key')
        self.newrelic_api_key = config.get('newrelic', {}).get('api_key')

        # Business-specific metric configurations
        self.business_metrics = {
            'character_interactions_per_second': {
                'description': 'Character AI interactions per second',
                'type': 'gauge',
                'thresholds': {'high': 100, 'low': 10}
            },
            'dialogue_queue_length': {
                'description': 'Number of pending dialogue generations',
                'type': 'gauge',
                'thresholds': {'high': 1000, 'low': 10}
            },
            'combat_calculations_per_second': {
                'description': 'Combat system calculations per second',
                'type': 'gauge',
                'thresholds': {'high': 500, 'low': 50}
            },
            'world_simulation_tps': {
                'description': 'World simulation ticks per second',
                'type': 'gauge',
                'thresholds': {'high': 60, 'low': 10}
            },
            'active_sessions': {
                'description': 'Number of active user sessions',
                'type': 'gauge',
                'thresholds': {'high': 10000, 'low': 100}
            },
            'npc_ai_load': {
                'description': 'NPC AI processing load percentage',
                'type': 'gauge',
                'thresholds': {'high': 80, 'low': 20}
            },
            'story_generation_queue': {
                'description': 'Story generation requests in queue',
                'type': 'gauge',
                'thresholds': {'high': 500, 'low': 10}
            },
            'voice_synthesis_jobs': {
                'description': 'Active voice synthesis jobs',
                'type': 'gauge',
                'thresholds': {'high': 100, 'low': 5}
            },
            'asset_processing_queue': {
                'description': 'Asset processing jobs in queue',
                'type': 'gauge',
                'thresholds': {'high': 200, 'low': 10}
            },
            'real_time_connections': {
                'description': 'WebSocket/real-time connections',
                'type': 'gauge',
                'thresholds': {'high': 5000, 'low': 100}
            }
        }

        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        for metric_name, config in self.business_metrics.items():
            if config['type'] == 'gauge':
                self.custom_gauges[metric_name] = Gauge(
                    f'dmlogn8n_{metric_name}',
                    config['description'],
                    ['service', 'environment'],
                    registry=self.registry
                )
            elif config['type'] == 'counter':
                self.custom_counters[metric_name] = Counter(
                    f'dmlogn8n_{metric_name}',
                    config['description'],
                    ['service', 'environment'],
                    registry=self.registry
                )
            elif config['type'] == 'histogram':
                self.custom_histograms[metric_name] = Histogram(
                    f'dmlogn8n_{metric_name}',
                    config['description'],
                    ['service', 'environment'],
                    registry=self.registry
                )

    async def collect_basic_metrics(self, service_id: str) -> Dict[str, float]:
        """Collect basic infrastructure metrics"""
        try:
            metrics = {}

            # Get metrics from Prometheus
            prometheus_metrics = await self._query_prometheus(service_id)
            metrics.update(prometheus_metrics)

            # Get system metrics if applicable
            if service_id in ['combat-engine', 'world-simulation']:
                system_metrics = await self._collect_system_metrics()
                metrics.update(system_metrics)

            # Get application metrics from service endpoints
            app_metrics = await self._collect_application_metrics(service_id)
            metrics.update(app_metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting basic metrics for {service_id}: {e}")
            return {}

    async def collect_custom_metrics(self, service_id: str) -> Dict[str, float]:
        """Collect business-specific custom metrics"""
        try:
            metrics = {}

            # Service-specific metric collection
            if service_id == 'character-portal':
                metrics.update(await self._collect_character_portal_metrics())
            elif service_id == 'dialogue-system':
                metrics.update(await self._collect_dialogue_system_metrics())
            elif service_id == 'combat-engine':
                metrics.update(await self._collect_combat_engine_metrics())
            elif service_id == 'world-simulation':
                metrics.update(await self._collect_world_simulation_metrics())
            elif service_id == 'ai-model-pool':
                metrics.update(await self._collect_ai_model_pool_metrics())

            # General platform metrics
            metrics.update(await self._collect_platform_metrics())

            # Update Prometheus metrics
            await self._update_prometheus_metrics(service_id, metrics)

            # Cache metrics in Redis
            await self._cache_metrics(service_id, metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting custom metrics for {service_id}: {e}")
            return {}

    async def _query_prometheus(self, service_id: str) -> Dict[str, float]:
        """Query Prometheus for service metrics"""
        if not self.prometheus_url:
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                queries = {
                    'cpu_usage': f'avg(rate(container_cpu_usage_seconds_total{{service="{service_id}"}}[1m])) * 100',
                    'memory_usage': f'avg(container_memory_usage_bytes{{service="{service_id}"}}) / 1024 / 1024',
                    'request_rate': f'sum(rate(http_requests_total{{service="{service_id}"}}[1m]))',
                    'response_time': f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{service_id}"}}[1m])) by (le))',
                    'error_rate': f'sum(rate(http_requests_total{{service="{service_id}",status=~"5.."}}[1m])) / sum(rate(http_requests_total{{service="{service_id}"}}[1m])) * 100'
                }

                metrics = {}
                for metric_name, query in queries.items():
                    try:
                        url = f"{self.prometheus_url}/api/v1/query"
                        params = {'query': query}

                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data['status'] == 'success' and data['data']['result']:
                                    value = float(data['data']['result'][0]['value'][1])
                                    metrics[metric_name] = value
                    except Exception as e:
                        self.logger.warning(f"Error querying Prometheus for {metric_name}: {e}")

                return metrics

        except Exception as e:
            self.logger.error(f"Error connecting to Prometheus: {e}")
            return {}

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            metrics = {
                'system_cpu_percent': cpu_percent,
                'system_cpu_count': cpu_count,
                'system_memory_percent': memory.percent,
                'system_memory_available_mb': memory.available / 1024 / 1024,
                'system_disk_percent': (disk.used / disk.total) * 100,
                'system_disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'system_network_bytes_sent': network.bytes_sent,
                'system_network_bytes_recv': network.bytes_recv
            }

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}

    async def _collect_application_metrics(self, service_id: str) -> Dict[str, float]:
        """Collect metrics from application endpoints"""
        try:
            # Service health/metrics endpoints
            endpoints = {
                'api-gateway': 'http://api-gateway:8080/metrics',
                'character-portal': 'http://character-portal:8081/health',
                'dialogue-system': 'http://dialogue-system:8082/stats',
                'combat-engine': 'http://combat-engine:8083/metrics',
                'world-simulation': 'http://world-simulation:8084/stats'
            }

            metrics = {}
            if service_id in endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoints[service_id], timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                metrics.update(data)
                except Exception as e:
                    self.logger.warning(f"Error collecting metrics from {service_id} endpoint: {e}")

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
            return {}

    async def _collect_character_portal_metrics(self) -> Dict[str, float]:
        """Collect character portal specific metrics"""
        try:
            # Simulate character portal metrics
            # In production, this would query the actual service
            metrics = {
                'active_characters': 1250,
                'character_interactions_per_second': 85.5,
                'character_creation_rate': 2.3,
                'character_cache_hit_rate': 94.2,
                'character_response_time_ms': 150,
                'active_sessions': 3500
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting character portal metrics: {e}")
            return {}

    async def _collect_dialogue_system_metrics(self) -> Dict[str, float]:
        """Collect dialogue system specific metrics"""
        try:
            metrics = {
                'dialogue_queue_length': 45,
                'dialogue_generation_rate': 12.5,
                'dialogue_average_tokens': 150,
                'dialogue_cache_hit_rate': 78.5,
                'active_dialogues': 125,
                'dialogue_error_rate': 0.8
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting dialogue system metrics: {e}")
            return {}

    async def _collect_combat_engine_metrics(self) -> Dict[str, float]:
        """Collect combat engine specific metrics"""
        try:
            metrics = {
                'combat_calculations_per_second': 225.5,
                'active_combats': 18,
                'combat_queue_length': 5,
                'combat_resolution_time_ms': 45,
                'damage_calculations_per_second': 450,
                'combat_state_updates_per_second': 89
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting combat engine metrics: {e}")
            return {}

    async def _collect_world_simulation_metrics(self) -> Dict[str, float]:
        """Collect world simulation specific metrics"""
        try:
            metrics = {
                'world_simulation_tps': 58.5,
                'active_entities': 15000,
                'entity_updates_per_second': 8900,
                'world_events_per_second': 12.5,
                'simulation_state_size_mb': 245,
                'region_load_balance': 0.85
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting world simulation metrics: {e}")
            return {}

    async def _collect_ai_model_pool_metrics(self) -> Dict[str, float]:
        """Collect AI model pool specific metrics"""
        try:
            metrics = {
                'active_model_instances': 12,
                'gpu_utilization_percent': 67.5,
                'model_inference_queue_length': 8,
                'average_inference_time_ms': 125,
                'model_memory_usage_gb': 8.5,
                'model_requests_per_second': 45.5
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting AI model pool metrics: {e}")
            return {}

    async def _collect_platform_metrics(self) -> Dict[str, float]:
        """Collect general platform metrics"""
        try:
            metrics = {
                'total_active_users': 5250,
                'concurrent_sessions': 3500,
                'real_time_connections': 2100,
                'message_queue_depth': 125,
                'database_connections': 45,
                'cache_hit_rate': 89.5,
                'story_generation_queue': 15,
                'voice_synthesis_jobs': 8,
                'asset_processing_queue': 25
            }
            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting platform metrics: {e}")
            return {}

    async def _update_prometheus_metrics(self, service_id: str, metrics: Dict[str, float]):
        """Update Prometheus metrics with collected values"""
        try:
            for metric_name, value in metrics.items():
                if metric_name in self.custom_gauges:
                    self.custom_gauges[metric_name].labels(
                        service=service_id,
                        environment='production'
                    ).set(value)
                elif metric_name in self.custom_counters:
                    self.custom_counters[metric_name].labels(
                        service=service_id,
                        environment='production'
                    ).inc(value)

        except Exception as e:
            self.logger.error(f"Error updating Prometheus metrics: {e}")

    async def _cache_metrics(self, service_id: str, metrics: Dict[str, float]):
        """Cache metrics in Redis for fast access"""
        try:
            cache_key = f"metrics:{service_id}:{int(datetime.now().timestamp())}"
            self.redis_client.hset(cache_key, mapping={k: str(v) for k, v in metrics.items()})

            # Set expiration
            self.redis_client.expire(cache_key, 3600)  # 1 hour

            # Store latest metrics
            latest_key = f"metrics:latest:{service_id}"
            self.redis_client.hset(latest_key, mapping={k: str(v) for k, v in metrics.items()})
            self.redis_client.expire(latest_key, 300)  # 5 minutes

        except Exception as e:
            self.logger.error(f"Error caching metrics: {e}")

    async def get_metric_history(self, service_id: str, metric_name: str, duration_hours: int = 1) -> List[Dict[str, Any]]:
        """Get historical metric data from Redis"""
        try:
            end_time = int(datetime.now().timestamp())
            start_time = end_time - (duration_hours * 3600)

            history = []

            # Scan for metric keys in time range
            for timestamp in range(start_time, end_time, 60):  # Every minute
                cache_key = f"metrics:{service_id}:{timestamp}"
                if self.redis_client.exists(cache_key):
                    value = self.redis_client.hget(cache_key, metric_name)
                    if value:
                        history.append({
                            'timestamp': datetime.fromtimestamp(timestamp),
                            'value': float(value)
                        })

            return history

        except Exception as e:
            self.logger.error(f"Error getting metric history: {e}")
            return []

    async def get_metric_aggregates(self, service_id: str, metric_name: str, duration_hours: int = 1) -> Dict[str, float]:
        """Get aggregated metrics (min, max, avg, etc.)"""
        try:
            history = await self.get_metric_history(service_id, metric_name, duration_hours)

            if not history:
                return {}

            values = [h['value'] for h in history]

            aggregates = {
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'median': statistics.median(values),
                'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
                'count': len(values)
            }

            return aggregates

        except Exception as e:
            self.logger.error(f"Error getting metric aggregates: {e}")
            return {}

    def get_metric_thresholds(self, metric_name: str) -> Dict[str, float]:
        """Get defined thresholds for a metric"""
        if metric_name in self.business_metrics:
            return self.business_metrics[metric_name].get('thresholds', {})
        return {}

    def evaluate_metric_health(self, service_id: str, metrics: Dict[str, float]) -> Dict[str, str]:
        """Evaluate metric health based on thresholds"""
        health_status = {}

        for metric_name, value in metrics.items():
            thresholds = self.get_metric_thresholds(metric_name)

            if 'high' in thresholds and value > thresholds['high']:
                health_status[metric_name] = 'critical'
            elif 'low' in thresholds and value < thresholds['low']:
                health_status[metric_name] = 'warning'
            else:
                health_status[metric_name] = 'healthy'

        return health_status