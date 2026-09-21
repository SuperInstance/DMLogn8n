"""
Parallel Metrics Collection and Analytics System
Real-time monitoring for all parallel systems
"""

import asyncio
import aiohttp
import psutil
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import uuid
import json
import time
import threading
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, start_http_server
import redis
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metric_type: str = "gauge"  # gauge, counter, histogram


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    active_agents: int
    tasks_processed: int
    dialogues_generated: int
    combats_active: int
    world_events: int
    api_requests: int
    error_rate: float
    response_time: float
    throughput: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CustomMetric:
    """Custom metric definition"""
    name: str
    description: str
    metric_type: str
    labels: List[str] = field(default_factory=list)
    aggregation: str = "avg"  # avg, sum, min, max, p95, p99


class ParallelMetricsSystem:
    """Parallel metrics collection and analytics system"""

    def __init__(self,
                 collection_interval: float = 0.1,  # 100ms
                 retention_hours: int = 24,
                 enable_prometheus: bool = True,
                 enable_influxdb: bool = True,
                 enable_redis: bool = True):

        self.collection_interval = collection_interval
        self.retention_hours = retention_hours

        # Metric storage
        self.metrics_buffer: deque = deque(maxlen=100000)
        self.system_metrics: deque = deque(maxlen=10000)
        self.application_metrics: deque = deque(maxlen=10000)
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=5000))

        # Custom metric definitions
        self.metric_definitions: Dict[str, CustomMetric] = {}

        # Parallel collectors
        self.collectors: Dict[str, asyncio.Task] = {}
        self.aggregators: Dict[str, asyncio.Task] = {}
        self.analyzers: List[asyncio.Task] = []

        # Thread pools for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        self.process_pool = ThreadPoolExecutor(max_workers=10)

        # External connections
        self.redis_client: Optional[redis.Redis] = None
        self.influx_client: Optional[InfluxDBClient] = None
        self.prometheus_registry: Optional[CollectorRegistry] = None

        # Prometheus metrics
        self.prometheus_metrics: Dict[str, Any] = {}

        # Real-time analytics
        self.analytics_cache = {}
        self.alert_thresholds = {}
        self.active_alerts = {}

        # Performance tracking
        self.collection_stats = {
            "metrics_collected": 0,
            "collections_per_second": 0.0,
            "average_collection_time": 0.0,
            "buffer_utilization": 0.0,
            "error_count": 0
        }

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()

        self.is_running = False

    async def initialize(self):
        """Initialize the metrics system"""
        logger.info("Initializing parallel metrics system")

        # Initialize external connections
        if enable_prometheus:
            await self._initialize_prometheus()

        if enable_influxdb:
            await self._initialize_influxdb()

        if enable_redis:
            await self._initialize_redis()

        # Register default metrics
        await self._register_default_metrics()

        # Start collectors
        await self._start_collectors()

        # Start aggregators
        await self._start_aggregators()

        # Start analyzers
        await self._start_analyzers()

        # Start real-time processors
        await self._start_realtime_processors()

        self.is_running = True
        logger.info("Parallel metrics system initialized")

    async def _initialize_prometheus(self):
        """Initialize Prometheus metrics"""
        self.prometheus_registry = CollectorRegistry()

        # Create default Prometheus metrics
        self.prometheus_metrics = {
            "cpu_usage": Gauge("system_cpu_usage_percent", "CPU usage percentage", registry=self.prometheus_registry),
            "memory_usage": Gauge("system_memory_usage_percent", "Memory usage percentage", registry=self.prometheus_registry),
            "active_agents": Gauge("agents_active_total", "Number of active agents", registry=self.prometheus_registry),
            "tasks_processed": Counter("tasks_processed_total", "Total tasks processed", registry=self.prometheus_registry),
            "response_time": Histogram("request_duration_seconds", "Request duration", registry=self.prometheus_registry),
            "error_rate": Gauge("error_rate", "Error rate percentage", registry=self.prometheus_registry)
        }

        # Start Prometheus HTTP server
        start_http_server(9091, registry=self.prometheus_registry)

    async def _initialize_influxdb(self):
        """Initialize InfluxDB connection"""
        try:
            self.influx_client = InfluxDBClient(
                url="http://localhost:8086",
                token="your-token",
                org="dmlogn8n"
            )
            logger.info("InfluxDB connection established")
        except Exception as e:
            logger.warning(f"InfluxDB connection failed: {e}")

    async def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")

    async def _register_default_metrics(self):
        """Register default custom metrics"""
        default_metrics = [
            CustomMetric(
                name="agent_decision_time",
                description="Time for agent to make decision",
                metric_type="histogram",
                labels=["agent_type", "decision_complexity"]
            ),
            CustomMetric(
                name="dialogue_sentiment_score",
                description="Sentiment score of generated dialogue",
                metric_type="gauge",
                labels=["character_id", "emotion"]
            ),
            CustomMetric(
                name="combat_damage_per_second",
                description="DPS in combat encounters",
                metric_type="gauge",
                labels=["encounter_id", "team"]
            ),
            CustomMetric(
                name="world_simulation_fps",
                description="Frames per second for world simulation",
                metric_type="gauge"
            ),
            CustomMetric(
                name="code_generation_success_rate",
                description="Success rate of code generation",
                metric_type="gauge",
                labels=["model_type"]
            )
        ]

        for metric in default_metrics:
            self.metric_definitions[metric.name] = metric

    async def _start_collectors(self):
        """Start metric collectors"""
        # System metrics collector
        task = asyncio.create_task(self._system_metrics_collector())
        self.collectors["system"] = task
        self.background_tasks.add(task)

        # Application metrics collector
        task = asyncio.create_task(self._application_metrics_collector())
        self.collectors["application"] = task
        self.background_tasks.add(task)

        # Parallel collectors for different components
        components = ["agents", "dialogue", "combat", "world", "code_generation"]
        for component in components:
            task = asyncio.create_task(self._component_metrics_collector(component))
            self.collectors[component] = task
            self.background_tasks.add(task)

    async def _start_aggregators(self):
        """Start metric aggregators"""
        # Real-time aggregator
        task = asyncio.create_task(self._realtime_aggregator())
        self.aggregators["realtime"] = task
        self.background_tasks.add(task)

        # Time-window aggregators
        windows = ["1m", "5m", "15m", "1h"]
        for window in windows:
            task = asyncio.create_task(self._time_window_aggregator(window))
            self.aggregators[window] = task
            self.background_tasks.add(task)

    async def _start_analyzers(self):
        """Start metric analyzers"""
        # Anomaly detection
        task = asyncio.create_task(self._anomaly_detector())
        self.analyzers.append(task)
        self.background_tasks.add(task)

        # Trend analysis
        task = asyncio.create_task(self._trend_analyzer())
        self.analyzers.append(task)
        self.background_tasks.add(task)

        # Performance analyzer
        task = asyncio.create_task(self._performance_analyzer())
        self.analyzers.append(task)
        self.background_tasks.add(task)

    async def _start_realtime_processors(self):
        """Start real-time metric processors"""
        # Alert processor
        task = asyncio.create_task(self._alert_processor())
        self.background_tasks.add(task)

        # Cache processor
        task = asyncio.create_task(self._cache_processor())
        self.background_tasks.add(task)

        # Export processor
        task = asyncio.create_task(self._export_processor())
        self.background_tasks.add(task)

        # Cleanup processor
        task = asyncio.create_task(self._cleanup_processor())
        self.background_tasks.add(task)

    async def _system_metrics_collector(self):
        """Collect system metrics in parallel"""
        while self.is_running:
            try:
                start_time = time.time()

                # Collect system metrics in parallel
                tasks = [
                    self.thread_pool.submit(psutil.cpu_percent),
                    self.thread_pool.submit(psutil.virtual_memory).percent,
                    self.thread_pool.submit(psutil.disk_usage('/').percent),
                    self.thread_pool.submit(psutil.net_io_counters),
                    self.thread_pool.submit(len(psutil.pids())),
                    self.thread_pool.submit(threading.active_count())
                ]

                # Wait for all collections
                results = []
                for task in tasks:
                    try:
                        results.append(task.result(timeout=0.1))
                    except Exception as e:
                        logger.error(f"System metric collection error: {e}")
                        results.append(0)

                # Create metrics
                cpu_percent = results[0]
                memory_percent = results[1]
                disk_usage = results[2]
                net_io = results[3]
                process_count = results[4]
                thread_count = results[5]

                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_usage=disk_usage,
                    network_io={
                        "bytes_sent": net_io.bytes_sent if net_io else 0,
                        "bytes_recv": net_io.bytes_recv if net_io else 0
                    },
                    process_count=process_count,
                    thread_count=thread_count
                )

                # Store metrics
                self.system_metrics.append(metrics)

                # Update Prometheus
                if self.prometheus_metrics.get("cpu_usage"):
                    self.prometheus_metrics["cpu_usage"].set(cpu_percent)
                if self.prometheus_metrics.get("memory_usage"):
                    self.prometheus_metrics["memory_usage"].set(memory_percent)

                # Store in Redis for real-time access
                if self.redis_client:
                    await self._store_in_redis("system", {
                        "cpu": cpu_percent,
                        "memory": memory_percent,
                        "disk": disk_usage,
                        "processes": process_count,
                        "threads": thread_count
                    })

                # Update collection stats
                collection_time = time.time() - start_time
                self._update_collection_stats(collection_time)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"System metrics collector error: {e}")
                self.collection_stats["error_count"] += 1
                await asyncio.sleep(self.collection_interval)

    async def _application_metrics_collector(self):
        """Collect application-specific metrics"""
        while self.is_running:
            try:
                # Collect from various application components
                metrics_data = await self._collect_application_data()

                metrics = ApplicationMetrics(
                    active_agents=metrics_data.get("active_agents", 0),
                    tasks_processed=metrics_data.get("tasks_processed", 0),
                    dialogues_generated=metrics_data.get("dialogues_generated", 0),
                    combats_active=metrics_data.get("combats_active", 0),
                    world_events=metrics_data.get("world_events", 0),
                    api_requests=metrics_data.get("api_requests", 0),
                    error_rate=metrics_data.get("error_rate", 0.0),
                    response_time=metrics_data.get("response_time", 0.0),
                    throughput=metrics_data.get("throughput", 0.0)
                )

                self.application_metrics.append(metrics)

                # Update Prometheus
                if self.prometheus_metrics.get("active_agents"):
                    self.prometheus_metrics["active_agents"].set(metrics.active_agents)
                if self.prometheus_metrics.get("error_rate"):
                    self.prometheus_metrics["error_rate"].set(metrics.error_rate)

                # Store in InfluxDB
                if self.influx_client:
                    await self._store_in_influxdb("application", metrics)

                await asyncio.sleep(self.collection_interval * 10)  # Collect less frequently

            except Exception as e:
                logger.error(f"Application metrics collector error: {e}")
                await asyncio.sleep(self.collection_interval * 10)

    async def _component_metrics_collector(self, component: str):
        """Collect metrics from specific component"""
        while self.is_running:
            try:
                # Collect component-specific metrics
                metrics = await self._collect_component_metrics(component)

                for metric in metrics:
                    # Store in component-specific buffer
                    await self.record_metric(
                        name=f"{component}_{metric['name']}",
                        value=metric['value'],
                        labels=metric.get('labels', {}),
                        metric_type=metric.get('type', 'gauge')
                    )

                await asyncio.sleep(self.collection_interval * 5)

            except Exception as e:
                logger.error(f"Component {component} metrics collector error: {e}")
                await asyncio.sleep(self.collection_interval * 5)

    async def _realtime_aggregator(self):
        """Aggregate metrics in real-time"""
        while self.is_running:
            try:
                # Calculate real-time aggregates
                if len(self.metrics_buffer) > 0:
                    # Get recent metrics
                    recent_metrics = list(self.metrics_buffer)[-1000:]

                    # Calculate aggregates by metric name
                    aggregates = {}
                    for metric in recent_metrics:
                        name = metric.name
                        if name not in aggregates:
                            aggregates[name] = []

                        aggregates[name].append(metric.value)

                    # Calculate statistics
                    realtime_stats = {}
                    for name, values in aggregates.items():
                        if values:
                            realtime_stats[name] = {
                                "avg": np.mean(values),
                                "min": np.min(values),
                                "max": np.max(values),
                                "p95": np.percentile(values, 95),
                                "p99": np.percentile(values, 99),
                                "count": len(values)
                            }

                    # Cache for quick access
                    self.analytics_cache["realtime"] = realtime_stats

                await asyncio.sleep(0.5)  # Update every 500ms

            except Exception as e:
                logger.error(f"Realtime aggregator error: {e}")
                await asyncio.sleep(0.5)

    async def _time_window_aggregator(self, window: str):
        """Aggregate metrics over time windows"""
        while self.is_running:
            try:
                # Parse window (e.g., "1m", "5m", "15m", "1h")
                window_seconds = self._parse_window(window)
                cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

                # Get metrics in window
                window_metrics = [
                    m for m in self.metrics_buffer
                    if m.timestamp > cutoff_time
                ]

                if window_metrics:
                    # Calculate aggregates
                    aggregates = {}
                    for metric in window_metrics:
                        name = metric.name
                        if name not in aggregates:
                            aggregates[name] = []

                        aggregates[name].append(metric.value)

                    # Store window aggregates
                    window_stats = {}
                    for name, values in aggregates.items():
                        if values:
                            definition = self.metric_definitions.get(name)
                            if definition:
                                agg_func = definition.aggregation
                                if agg_func == "avg":
                                    window_stats[name] = np.mean(values)
                                elif agg_func == "sum":
                                    window_stats[name] = np.sum(values)
                                elif agg_func == "min":
                                    window_stats[name] = np.min(values)
                                elif agg_func == "max":
                                    window_stats[name] = np.max(values)
                                elif agg_func == "p95":
                                    window_stats[name] = np.percentile(values, 95)
                                elif agg_func == "p99":
                                    window_stats[name] = np.percentile(values, 99)
                            else:
                                window_stats[name] = {
                                    "avg": np.mean(values),
                                    "count": len(values)
                                }

                    # Store in cache
                    self.analytics_cache[f"window_{window}"] = window_stats

                    # Store in Redis
                    if self.redis_client:
                        await self.redis_client.hset(
                            f"aggregates:{window}",
                            mapping={k: str(v) for k, v in window_stats.items()}
                        )

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Time window {window} aggregator error: {e}")
                await asyncio.sleep(60)

    async def _anomaly_detector(self):
        """Detect anomalies in metrics"""
        while self.is_running:
            try:
                # Get recent metrics for anomaly detection
                recent_metrics = list(self.metrics_buffer)[-10000:]

                # Group by metric name
                metric_groups = defaultdict(list)
                for metric in recent_metrics:
                    metric_groups[metric.name].append(metric.value)

                # Detect anomalies using statistical methods
                anomalies = []
                for name, values in metric_groups.items():
                    if len(values) > 100:
                        # Calculate Z-scores
                        mean = np.mean(values)
                        std = np.std(values)

                        if std > 0:
                            recent_values = values[-10:]  # Last 10 values
                            for i, value in enumerate(recent_values):
                                z_score = abs((value - mean) / std)
                                if z_score > 3:  # 3-sigma rule
                                    anomalies.append({
                                        "metric": name,
                                        "value": value,
                                        "z_score": z_score,
                                        "timestamp": datetime.now()
                                    })

                # Store anomalies
                if anomalies:
                    if self.redis_client:
                        await self.redis_client.lpush(
                            "anomalies",
                            *[json.dumps(a) for a in anomalies]
                        )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Anomaly detector error: {e}")
                await asyncio.sleep(10)

    async def _trend_analyzer(self):
        """Analyze trends in metrics"""
        while self.is_running:
            try:
                # Analyze trends for key metrics
                key_metrics = [
                    "cpu_usage",
                    "memory_usage",
                    "active_agents",
                    "tasks_processed",
                    "response_time"
                ]

                trends = {}
                for metric_name in key_metrics:
                    # Get historical data
                    historical_metrics = [
                        m for m in self.metrics_buffer
                        if m.name == metric_name
                    ]

                    if len(historical_metrics) > 100:
                        # Calculate trend using linear regression
                        values = [m.value for m in historical_metrics]
                        times = list(range(len(values)))

                        # Simple linear regression
                        n = len(values)
                        sum_x = sum(times)
                        sum_y = sum(values)
                        sum_xy = sum(x * y for x, y in zip(times, values))
                        sum_x2 = sum(x * x for x in times)

                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

                        trends[metric_name] = {
                            "slope": slope,
                            "direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                            "change_rate": abs(slope)
                        }

                # Store trends
                self.analytics_cache["trends"] = trends

                await asyncio.sleep(60)  # Analyze every minute

            except Exception as e:
                logger.error(f"Trend analyzer error: {e}")
                await asyncio.sleep(60)

    async def _performance_analyzer(self):
        """Analyze system performance"""
        while self.is_running:
            try:
                # Collect performance data
                if len(self.system_metrics) > 0:
                    recent_system = list(self.system_metrics)[-60:]  # Last 60 samples

                    # Calculate averages
                    avg_cpu = np.mean([m.cpu_percent for m in recent_system])
                    avg_memory = np.mean([m.memory_percent for m in recent_system])

                    # Determine performance score
                    cpu_score = max(0, 100 - avg_cpu)
                    memory_score = max(0, 100 - avg_memory)
                    overall_score = (cpu_score + memory_score) / 2

                    performance_report = {
                        "score": overall_score,
                        "cpu_score": cpu_score,
                        "memory_score": memory_score,
                        "cpu_utilization": avg_cpu,
                        "memory_utilization": avg_memory,
                        "recommendation": self._generate_performance_recommendation(overall_score)
                    }

                    # Store performance report
                    self.analytics_cache["performance"] = performance_report

                    # Store in Redis
                    if self.redis_client:
                        await self.redis_client.hset(
                            "performance",
                            mapping={k: str(v) for k, v in performance_report.items()}
                        )

                await asyncio.sleep(30)  # Analyze every 30 seconds

            except Exception as e:
                logger.error(f"Performance analyzer error: {e}")
                await asyncio.sleep(30)

    async def _alert_processor(self):
        """Process metric alerts"""
        while self.is_running:
            try:
                # Check alert thresholds
                alerts = []

                # Check CPU alert
                if len(self.system_metrics) > 0:
                    latest_cpu = self.system_metrics[-1].cpu_percent
                    if latest_cpu > 90:
                        alerts.append({
                            "type": "cpu_high",
                            "message": f"CPU usage is {latest_cpu:.1f}%",
                            "severity": "warning"
                        })

                # Check memory alert
                latest_memory = self.system_metrics[-1].memory_percent
                if latest_memory > 90:
                    alerts.append({
                        "type": "memory_high",
                        "message": f"Memory usage is {latest_memory:.1f}%",
                        "severity": "warning"
                    })

                # Check error rate
                if len(self.application_metrics) > 0:
                    latest_error_rate = self.application_metrics[-1].error_rate
                    if latest_error_rate > 5:
                        alerts.append({
                            "type": "error_rate_high",
                            "message": f"Error rate is {latest_error_rate:.1f}%",
                            "severity": "critical"
                        })

                # Process alerts
                for alert in alerts:
                    alert_id = f"{alert['type']}_{int(time.time())}"
                    self.active_alerts[alert_id] = alert

                    # Store in Redis
                    if self.redis_client:
                        await self.redis_client.hset(
                            "alerts",
                            mapping={alert_id: json.dumps(alert)}
                        )

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Alert processor error: {e}")
                await asyncio.sleep(5)

    async def _cache_processor(self):
        """Process metric caches"""
        while self.is_running:
            try:
                # Update cache statistics
                self.collection_stats["buffer_utilization"] = len(self.metrics_buffer) / self.metrics_buffer.maxlen

                # Optimize cache
                if len(self.analytics_cache) > 1000:
                    # Remove old entries
                    cutoff = datetime.now() - timedelta(hours=1)
                    # Implementation would remove old cached data

                await asyncio.sleep(60)  # Process every minute

            except Exception as e:
                logger.error(f"Cache processor error: {e}")
                await asyncio.sleep(60)

    async def _export_processor(self):
        """Export metrics to external systems"""
        while self.is_running:
            try:
                # Export to external monitoring systems
                # This would integrate with tools like Grafana, DataDog, etc.

                await asyncio.sleep(300)  # Export every 5 minutes

            except Exception as e:
                logger.error(f"Export processor error: {e}")
                await asyncio.sleep(300)

    async def _cleanup_processor(self):
        """Clean up old metrics"""
        while self.is_running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

                # Clean up old metrics from buffers
                # deques handle this automatically with maxlen

                # Clean up old alerts
                old_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if datetime.now() - datetime.fromisoformat(alert.get("timestamp", "1970-01-01")) > timedelta(hours=1)
                ]

                for alert_id in old_alerts:
                    del self.active_alerts[alert_id]

                await asyncio.sleep(3600)  # Cleanup every hour

            except Exception as e:
                logger.error(f"Cleanup processor error: {e}")
                await asyncio.sleep(3600)

    async def record_metric(self,
                           name: str,
                           value: float,
                           labels: Optional[Dict[str, str]] = None,
                           metric_type: str = "gauge"):
        """Record a custom metric"""
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=metric_type
        )

        self.metrics_buffer.append(metric)

        # Store in custom metric buffer
        self.custom_metrics[name].append(metric)

        # Update Prometheus if applicable
        prometheus_metric = self.prometheus_metrics.get(name)
        if prometheus_metric:
            if metric_type == "gauge":
                prometheus_metric.set(value)
            elif metric_type == "counter":
                prometheus_metric.inc(value)

        self.collection_stats["metrics_collected"] += 1

    async def get_metrics(self,
                         metric_names: Optional[List[str]] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics with optional filtering"""
        # Filter metrics
        filtered_metrics = list(self.metrics_buffer)

        if metric_names:
            filtered_metrics = [m for m in filtered_metrics if m.name in metric_names]

        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_time]

        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_time]

        # Group by name
        result = defaultdict(list)
        for metric in filtered_metrics:
            result[metric.name].append({
                "value": metric.value,
                "labels": metric.labels,
                "timestamp": metric.timestamp.isoformat()
            })

        return dict(result)

    async def get_analytics(self, analysis_type: str = "realtime") -> Dict[str, Any]:
        """Get analytics data"""
        return self.analytics_cache.get(analysis_type, {})

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        if len(self.system_metrics) > 0:
            latest_system = self.system_metrics[-1]
        else:
            latest_system = SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                disk_usage=0,
                network_io={},
                process_count=0,
                thread_count=0
            )

        if len(self.application_metrics) > 0:
            latest_app = self.application_metrics[-1]
        else:
            latest_app = ApplicationMetrics(
                active_agents=0,
                tasks_processed=0,
                dialogues_generated=0,
                combats_active=0,
                world_events=0,
                api_requests=0,
                error_rate=0.0,
                response_time=0.0,
                throughput=0.0
            )

        return {
            "system": {
                "cpu_percent": latest_system.cpu_percent,
                "memory_percent": latest_system.memory_percent,
                "disk_usage": latest_system.disk_usage,
                "process_count": latest_system.process_count,
                "thread_count": latest_system.thread_count
            },
            "application": {
                "active_agents": latest_app.active_agents,
                "tasks_processed": latest_app.tasks_processed,
                "dialogues_generated": latest_app.dialogues_generated,
                "combats_active": latest_app.combats_active,
                "error_rate": latest_app.error_rate,
                "response_time": latest_app.response_time,
                "throughput": latest_app.throughput
            },
            "collection_stats": self.collection_stats,
            "active_alerts": len(self.active_alerts),
            "performance": self.analytics_cache.get("performance", {})
        }

    async def _collect_application_data(self) -> Dict[str, Any]:
        """Collect data from application components"""
        # This would connect to other system components
        # For now, simulate data
        return {
            "active_agents": random.randint(100, 500),
            "tasks_processed": random.randint(1000, 10000),
            "dialogues_generated": random.randint(50, 200),
            "combats_active": random.randint(5, 20),
            "world_events": random.randint(100, 500),
            "api_requests": random.randint(500, 2000),
            "error_rate": random.uniform(0, 5),
            "response_time": random.uniform(50, 500),
            "throughput": random.uniform(100, 1000)
        }

    async def _collect_component_metrics(self, component: str) -> List[Dict[str, Any]]:
        """Collect metrics from specific component"""
        # Simulate component metrics
        return [
            {
                "name": "processing_time",
                "value": random.uniform(10, 100),
                "type": "histogram"
            },
            {
                "name": "queue_size",
                "value": random.randint(0, 100),
                "type": "gauge"
            }
        ]

    async def _store_in_redis(self, key: str, data: Dict[str, Any]):
        """Store data in Redis"""
        try:
            await self.redis_client.hset(
                f"metrics:{key}",
                mapping={k: str(v) for k, v in data.items()}
            )
            await self.redis_client.expire(f"metrics:{key}", 3600)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Redis storage error: {e}")

    async def _store_in_influxdb(self, measurement: str, data: Any):
        """Store data in InfluxDB"""
        try:
            write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)

            point = Point(measurement)
            if hasattr(data, 'cpu_percent'):
                point.field("cpu", data.cpu_percent)
                point.field("memory", data.memory_percent)
                point.field("active_agents", data.active_agents)
                point.field("tasks_processed", data.tasks_processed)

            write_api.write(bucket="dmlogn8n", record=point)
        except Exception as e:
            logger.error(f"InfluxDB storage error: {e}")

    def _parse_window(self, window: str) -> int:
        """Parse time window string to seconds"""
        if window.endswith('m'):
            return int(window[:-1]) * 60
        elif window.endswith('h'):
            return int(window[:-1]) * 3600
        else:
            return 60  # Default to 1 minute

    def _update_collection_stats(self, collection_time: float):
        """Update collection statistics"""
        total_collections = self.collection_stats["metrics_collected"]
        if total_collections > 0:
            self.collection_stats["average_collection_time"] = (
                (self.collection_stats["average_collection_time"] * (total_collections - 1) + collection_time) /
                total_collections
            )
        self.collection_stats["collections_per_second"] = total_collections / max(1, time.time())

    def _generate_performance_recommendation(self, score: float) -> str:
        """Generate performance recommendation based on score"""
        if score > 80:
            return "System performing optimally"
        elif score > 60:
            return "System performing adequately"
        elif score > 40:
            return "Consider optimizing resource usage"
        else:
            return "System needs immediate optimization"

    async def register_custom_metric(self, metric: CustomMetric):
        """Register a custom metric definition"""
        self.metric_definitions[metric.name] = metric

        # Create Prometheus metric if applicable
        if self.prometheus_registry:
            if metric.metric_type == "gauge":
                prom_metric = Gauge(
                    metric.name,
                    metric.description,
                    labelnames=metric.labels,
                    registry=self.prometheus_registry
                )
            elif metric.metric_type == "counter":
                prom_metric = Counter(
                    metric.name,
                    metric.description,
                    labelnames=metric.labels,
                    registry=self.prometheus_registry
                )
            elif metric.metric_type == "histogram":
                prom_metric = Histogram(
                    metric.name,
                    metric.description,
                    labelnames=metric.labels,
                    registry=self.prometheus_registry
                )

            self.prometheus_metrics[metric.name] = prom_metric

    async def shutdown(self):
        """Shutdown the metrics system"""
        logger.info("Shutting down parallel metrics system")

        self.is_running = False

        # Cancel all tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Close connections
        if self.redis_client:
            self.redis_client.close()

        if self.influx_client:
            self.influx_client.close()

        # Shutdown thread pools
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        logger.info("Parallel metrics system shutdown complete")


# Test function
async def test_metrics_system():
    """Test the metrics system"""
    metrics = ParallelMetricsSystem(
        collection_interval=0.1,
        retention_hours=1
    )

    await metrics.initialize()

    # Record some custom metrics
    for i in range(100):
        await metrics.record_metric(
            name="test_metric",
            value=random.uniform(0, 100),
            labels={"source": "test"},
            metric_type="gauge"
        )
        await asyncio.sleep(0.01)

    # Wait for collection
    await asyncio.sleep(2)

    # Get system status
    status = await metrics.get_system_status()
    print(f"System CPU: {status['system']['cpu_percent']:.1f}%")
    print(f"Active agents: {status['application']['active_agents']}")
    print(f"Metrics collected: {status['collection_stats']['metrics_collected']}")

    # Get analytics
    analytics = await metrics.get_analytics("realtime")
    print(f"Realtime analytics: {len(analytics)} metrics")

    await metrics.shutdown()


if __name__ == "__main__":
    asyncio.run(test_metrics_system())