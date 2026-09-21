#!/usr/bin/env python3
"""
Automatic Database Performance Tuning System
Intelligent automatic tuning for PostgreSQL, MongoDB, Redis with real-time optimization.
"""

import asyncio
import json
import time
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import statistics
import numpy as np

import psycopg2
import psycopg2.extras
import pymongo
from asyncpg import create_pool
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TuningCategory(Enum):
    QUERY_PERFORMANCE = "query_performance"
    MEMORY_OPTIMIZATION = "memory_optimization"
    DISK_IO = "disk_io"
    CONNECTION_MANAGEMENT = "connection_management"
    CONFIGURATION = "configuration"
    WORKLOAD_BALANCING = "workload_balancing"
    RESOURCE_ALLOCATION = "resource_allocation"

class TuningAction(Enum):
    INCREASE_WORK_MEM = "increase_work_mem"
    INCREASE_SHARED_BUFFERS = "increase_shared_buffers"
    ADAPTER_EFFECTIVE_CACHE_SIZE = "adjust_effective_cache_size"
    OPTIMIZE_CHECKPOINT_SEGMENTS = "optimize_checkpoint_segments"
    TUNE_RANDOM_PAGE_COST = "tune_random_page_cost"
    ADJUST_CONNECTION_LIMITS = "adjust_connection_limits"
    ENABLE_PARALLEL_QUERIES = "enable_parallel_queries"
    OPTIMIZE_WAL_SETTINGS = "optimize_wal_settings"
    TUNE_MONGODB_CACHE_SIZE = "tune_mongodb_cache_size"
    ADJUST_REDIS_MAXMEMORY = "adjust_redis_maxmemory"

@dataclass
class PerformanceMetric:
    name: str
    current_value: float
    target_value: float
    threshold_min: float
    threshold_max: float
    unit: str
    category: TuningCategory
    timestamp: datetime
    impact_score: float  # 0-1, higher means more impact on performance

@dataclass
class TuningRecommendation:
    action: TuningAction
    current_value: Any
    recommended_value: Any
    expected_improvement: float  # Percentage improvement expected
    confidence: float  # 0-1 confidence in recommendation
    reason: str
    category: TuningCategory
    effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    requires_restart: bool
    estimated_downtime_minutes: float

@dataclass
class TuningResult:
    recommendation: TuningRecommendation
    applied: bool
    actual_improvement: float
    new_value: Any
    error_message: Optional[str]
    applied_at: datetime
    rollback_available: bool

@dataclass
class DatabaseConfiguration:
    database_type: str
    version: str
    current_settings: Dict[str, Any]
    hardware_specs: Dict[str, Any]
    workload_profile: Dict[str, Any]

class DatabasePerformanceTuner:
    """Automatic database performance tuning system"""

    def __init__(self, database_type: str, connection_params: Dict[str, Any]):
        self.database_type = database_type.lower()
        self.connection_params = connection_params

        # Performance tracking
        self.metrics_history = defaultdict(deque)
        self.performance_baseline = {}
        self.tuning_history = []
        self.active_recommendations = []

        # Configuration
        self.tuning_enabled = True
        self.auto_apply_safe_changes = True
        self.min_confidence_threshold = 0.7
        self.max_risk_level = "medium"
        self.monitoring_interval = 60  # seconds

        # Background tasks
        self.monitoring_task = None
        self.analysis_task = None
        self.tuning_task = None

        # Shutdown flag
        self._shutdown = False

        # Database-specific configurations
        self.db_config = None

    async def initialize(self) -> bool:
        """Initialize the performance tuner"""

        try:
            logger.info(f"Initializing performance tuner for {self.database_type}")

            # Get database configuration
            self.db_config = await self._get_database_configuration()

            # Establish performance baseline
            await self._establish_baseline()

            # Start background tasks
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.analysis_task = asyncio.create_task(self._analysis_loop())
            self.tuning_task = asyncio.create_task(self._tuning_loop())

            logger.info(f"Performance tuner initialized for {self.database_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize performance tuner: {e}")
            return False

    async def _get_database_configuration(self) -> DatabaseConfiguration:
        """Get current database configuration"""

        if self.database_type == 'postgresql':
            return await self._get_postgresql_configuration()
        elif self.database_type == 'mongodb':
            return await self._get_mongodb_configuration()
        elif self.database_type == 'redis':
            return await self._get_redis_configuration()
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    async def _get_postgresql_configuration(self) -> DatabaseConfiguration:
        """Get PostgreSQL configuration"""

        conn = await create_pool(**self.connection_params)

        async with conn.acquire() as connection:
            # Get version
            version = await connection.fetchval("SELECT version()")

            # Get configuration parameters
            settings_query = """
            SELECT name, setting, unit, short_desc
            FROM pg_settings
            WHERE name IN (
                'shared_buffers', 'work_mem', 'effective_cache_size',
                'maintenance_work_mem', 'checkpoint_completion_target',
                'random_page_cost', 'effective_io_concurrency',
                'max_connections', 'shared_preload_libraries',
                'max_parallel_workers', 'max_parallel_workers_per_gather'
            )
            """

            settings = await connection.fetch(settings_query)
            current_settings = {row['name']: row['setting'] for row in settings}

            # Get hardware info
            hardware_info = await self._get_postgresql_hardware_info(connection)

            # Analyze workload profile
            workload_profile = await self._analyze_postgresql_workload(connection)

        return DatabaseConfiguration(
            database_type='postgresql',
            version=version,
            current_settings=current_settings,
            hardware_specs=hardware_info,
            workload_profile=workload_profile
        )

    async def _get_mongodb_configuration(self) -> DatabaseConfiguration:
        """Get MongoDB configuration"""

        client = pymongo.MongoClient(**self.connection_params)
        admin_db = client.admin

        # Get server status
        server_status = admin_db.command("serverStatus")
        version = server_status['version']

        # Get configuration
        config = admin_db.command("getCmdLineOpts")

        # Get hardware info
        host_info = admin_db.command("hostInfo")
        hardware_info = {
            'cpu_count': host_info['system']['numCores'],
            'memory_mb': host_info['system']['memSizeMB']
        }

        # Analyze workload
        workload_profile = await self._analyze_mongodb_workload(client)

        return DatabaseConfiguration(
            database_type='mongodb',
            version=version,
            current_settings=config.get('parsed', {}),
            hardware_specs=hardware_info,
            workload_profile=workload_profile
        )

    async def _get_redis_configuration(self) -> DatabaseConfiguration:
        """Get Redis configuration"""

        redis_client = redis.Redis(**self.connection_params)

        # Get info
        info = redis_client.info()
        version = info['redis_version']

        # Get config
        config = redis_client.config_get('*')

        # Hardware info
        hardware_info = {
            'memory_bytes': info['used_memory'],
            'max_memory': info.get('maxmemory', 0),
            'cpu_count': info.get('process_id', 1)  # Simplified
        }

        # Workload profile
        workload_profile = await self._analyze_redis_workload(redis_client)

        return DatabaseConfiguration(
            database_type='redis',
            version=version,
            current_settings=config,
            hardware_specs=hardware_info,
            workload_profile=workload_profile
        )

    async def _establish_baseline(self) -> None:
        """Establish performance baseline"""

        logger.info("Establishing performance baseline")

        baseline_metrics = await self._collect_current_metrics()

        for metric in baseline_metrics:
            self.performance_baseline[metric.name] = metric.current_value
            self.metrics_history[metric.name].append(metric)

    async def _collect_current_metrics(self) -> List[PerformanceMetric]:
        """Collect current performance metrics"""

        if self.database_type == 'postgresql':
            return await self._collect_postgresql_metrics()
        elif self.database_type == 'mongodb':
            return await self._collect_mongodb_metrics()
        elif self.database_type == 'redis':
            return await self._collect_redis_metrics()
        else:
            return []

    async def _collect_postgresql_metrics(self) -> List[PerformanceMetric]:
        """Collect PostgreSQL performance metrics"""

        conn = await create_pool(**self.connection_params)
        metrics = []

        async with conn.acquire() as connection:
            # Query performance metrics
            queries = {
                'avg_query_time': """
                    SELECT round(EXTRACT(EPOCH FROM (avg_total_time - avg_plan_time)))::float
                    FROM pg_stat_statements
                """,
                'cache_hit_ratio': """
                    SELECT round(sum(blks_hit)::float / (sum(blks_hit) + sum(blks_read)), 4) * 100
                    FROM pg_stat_database
                """,
                'active_connections': "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
                'transactions_per_second': """
                    SELECT round(xact_commit + xact_rollback)
                    FROM pg_stat_database WHERE datname = current_database()
                """,
                'database_size_mb': """
                    SELECT round(pg_database_size(current_database()) / 1024.0 / 1024.0)
                """,
                'index_usage_ratio': """
                    SELECT round(sum(idx_scan)::float / NULLIF(sum(idx_scan + seq_scan), 0), 4) * 100
                    FROM pg_stat_user_tables
                """
            }

            for name, query in queries.items():
                try:
                    value = await connection.fetchval(query)
                    if value is not None:
                        metric = PerformanceMetric(
                            name=name,
                            current_value=float(value),
                            target_value=self._get_target_value(name),
                            threshold_min=self._get_threshold_min(name),
                            threshold_max=self._get_threshold_max(name),
                            unit=self._get_unit(name),
                            category=self._get_category(name),
                            timestamp=datetime.now(),
                            impact_score=self._calculate_impact_score(name, float(value))
                        )
                        metrics.append(metric)
                except Exception as e:
                    logger.debug(f"Failed to collect metric {name}: {e}")

        return metrics

    async def _collect_mongodb_metrics(self) -> List[PerformanceMetric]:
        """Collect MongoDB performance metrics"""

        client = pymongo.MongoClient(**self.connection_params)
        admin_db = client.admin
        metrics = []

        try:
            # Get server status
            server_status = admin_db.command("serverStatus")

            # Extract metrics
            metric_data = {
                'operations_per_second': server_status.get('opcounters', {}).get('insert', 0) / 60,  # Simplified
                'query_executors_per_sec': server_status.get('metrics', {}).get('query', {}).get('executor', {}).get('scannedObjectsPerSecond', 0),
                'cache_hit_ratio': server_status.get('wiredTiger', {}).get('block-manager', {}).get('blocks read', 0) / max(1, server_status.get('wiredTiger', {}).get('block-manager', {}).get('blocks read', 1) + server_status.get('wiredTiger', {}).get('block-manager', {}).get('blocks read from cache', 1)) * 100,
                'connections_current': server_status.get('connections', {}).get('current', 0),
                'memory_usage_mb': server_status.get('mem', {}).get('resident', 0),
                'page_faults_per_sec': server_status.get('extra_info', {}).get('page_faults', 0)
            }

            for name, value in metric_data.items():
                metric = PerformanceMetric(
                    name=name,
                    current_value=float(value),
                    target_value=self._get_target_value(name),
                    threshold_min=self._get_threshold_min(name),
                    threshold_max=self._get_threshold_max(name),
                    unit=self._get_unit(name),
                    category=self._get_category(name),
                    timestamp=datetime.now(),
                    impact_score=self._calculate_impact_score(name, float(value))
                )
                metrics.append(metric)

        except Exception as e:
            logger.error(f"Failed to collect MongoDB metrics: {e}")

        return metrics

    async def _collect_redis_metrics(self) -> List[PerformanceMetric]:
        """Collect Redis performance metrics"""

        redis_client = redis.Redis(**self.connection_params)
        metrics = []

        try:
            info = redis_client.info()

            metric_data = {
                'operations_per_second': info.get('instantaneous_ops_per_sec', 0),
                'memory_usage_mb': info.get('used_memory', 0) / (1024 * 1024),
                'hit_ratio': (info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))) * 100,
                'connected_clients': info.get('connected_clients', 0),
                'expired_keys_per_sec': info.get('expired_keys', 0) / 60,  # Simplified
                'evicted_keys_per_sec': info.get('evicted_keys', 0) / 60
            }

            for name, value in metric_data.items():
                metric = PerformanceMetric(
                    name=name,
                    current_value=float(value),
                    target_value=self._get_target_value(name),
                    threshold_min=self._get_threshold_min(name),
                    threshold_max=self._get_threshold_max(name),
                    unit=self._get_unit(name),
                    category=self._get_category(name),
                    timestamp=datetime.now(),
                    impact_score=self._calculate_impact_score(name, float(value))
                )
                metrics.append(metric)

        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")

        return metrics

    async def analyze_performance(self) -> List[TuningRecommendation]:
        """Analyze performance and generate tuning recommendations"""

        recommendations = []
        current_metrics = await self._collect_current_metrics()

        for metric in current_metrics:
            metric_recommendations = await self._analyze_metric(metric)
            recommendations.extend(metric_recommendations)

        # Filter and prioritize recommendations
        filtered_recommendations = self._filter_recommendations(recommendations)
        prioritized_recommendations = self._prioritize_recommendations(filtered_recommendations)

        return prioritized_recommendations

    async def _analyze_metric(self, metric: PerformanceMetric) -> List[TuningRecommendation]:
        """Analyze individual metric and generate recommendations"""

        recommendations = []

        # Check if metric is outside threshold
        if metric.current_value < metric.threshold_min or metric.current_value > metric.threshold_max:
            # Generate specific recommendations based on metric type
            if self.database_type == 'postgresql':
                recommendations.extend(await self._analyze_postgresql_metric(metric))
            elif self.database_type == 'mongodb':
                recommendations.extend(await self._analyze_mongodb_metric(metric))
            elif self.database_type == 'redis':
                recommendations.extend(await self._analyze_redis_metric(metric))

        return recommendations

    async def _analyze_postgresql_metric(self, metric: PerformanceMetric) -> List[TuningRecommendation]:
        """Analyze PostgreSQL metric"""

        recommendations = []

        if metric.name == 'cache_hit_ratio' and metric.current_value < 95:
            recommendations.append(TuningRecommendation(
                action=TuningAction.INCREASE_SHARED_BUFFERS,
                current_value=self.db_config.current_settings.get('shared_buffers', '128MB'),
                recommended_value=self._calculate_optimal_shared_buffers(),
                expected_improvement=min((95 - metric.current_value) / 10, 15),
                confidence=0.8,
                reason=f"Low cache hit ratio ({metric.current_value:.1f}%). Increasing shared_buffers should improve performance.",
                category=TuningCategory.MEMORY_OPTIMIZATION,
                effort="low",
                risk_level="low",
                requires_restart=True,
                estimated_downtime_minutes=2.0
            ))

        if metric.name == 'avg_query_time' and metric.current_value > 100:
            recommendations.append(TuningRecommendation(
                action=TuningAction.INCREASE_WORK_MEM,
                current_value=self.db_config.current_settings.get('work_mem', '4MB'),
                recommended_value=self._calculate_optimal_work_mem(),
                expected_improvement=min((metric.current_value - 100) / metric.current_value * 30, 25),
                confidence=0.7,
                reason=f"High average query time ({metric.current_value:.1f}ms). Increasing work_mem can reduce disk sorts.",
                category=TuningCategory.QUERY_PERFORMANCE,
                effort="low",
                risk_level="low",
                requires_restart=False,
                estimated_downtime_minutes=0.0
            ))

        if metric.name == 'active_connections' and metric.current_value > self.db_config.current_settings.get('max_connections', 100) * 0.8:
            recommendations.append(TuningRecommendation(
                action=TuningAction.ADJUST_CONNECTION_LIMITS,
                current_value=self.db_config.current_settings.get('max_connections', 100),
                recommended_value=int(metric.current_value * 1.2),
                expected_improvement=10,
                confidence=0.9,
                reason=f"High connection usage ({metric.current_value}/{self.db_config.current_settings.get('max_connections', 100)}). Consider increasing max_connections or using connection pooling.",
                category=TuningCategory.CONNECTION_MANAGEMENT,
                effort="medium",
                risk_level="medium",
                requires_restart=True,
                estimated_downtime_minutes=2.0
            ))

        if metric.name == 'index_usage_ratio' and metric.current_value < 90:
            recommendations.append(TuningRecommendation(
                action=TuningAction.TUNE_RANDOM_PAGE_COST,
                current_value=self.db_config.current_settings.get('random_page_cost', '4.0'),
                recommended_value='1.1',
                expected_improvement=15,
                confidence=0.6,
                reason=f"Low index usage ratio ({metric.current_value:.1f}%). Lowering random_page_cost can encourage index usage.",
                category=TuningCategory.QUERY_PERFORMANCE,
                effort="low",
                risk_level="low",
                requires_restart=False,
                estimated_downtime_minutes=0.0
            ))

        return recommendations

    async def _analyze_mongodb_metric(self, metric: PerformanceMetric) -> List[TuningRecommendation]:
        """Analyze MongoDB metric"""

        recommendations = []

        if metric.name == 'cache_hit_ratio' and metric.current_value < 90:
            recommendations.append(TuningRecommendation(
                action=TuningAction.TUNE_MONGODB_CACHE_SIZE,
                current_value="Current cache size",
                recommended_value="Increased cache size",
                expected_improvement=min((90 - metric.current_value) / 10, 20),
                confidence=0.8,
                reason=f"Low cache hit ratio ({metric.current_value:.1f}%). Increasing WiredTiger cache size should improve performance.",
                category=TuningCategory.MEMORY_OPTIMIZATION,
                effort="medium",
                risk_level="medium",
                requires_restart=True,
                estimated_downtime_minutes=3.0
            ))

        if metric.name == 'connections_current' and metric.current_value > 80:
            recommendations.append(TuningRecommendation(
                action=TuningAction.ADJUST_CONNECTION_LIMITS,
                current_value="Current connection limit",
                recommended_value="Increased connection limit",
                expected_improvement=15,
                confidence=0.8,
                reason=f"High connection usage ({metric.current_value}). Consider increasing connection limits.",
                category=TuningCategory.CONNECTION_MANAGEMENT,
                effort="low",
                risk_level="low",
                requires_restart=False,
                estimated_downtime_minutes=0.0
            ))

        return recommendations

    async def _analyze_redis_metric(self, metric: PerformanceMetric) -> List[TuningRecommendation]:
        """Analyze Redis metric"""

        recommendations = []

        if metric.name == 'memory_usage_mb' and metric.current_value > self.db_config.hardware_specs.get('max_memory', 1024) * 0.9:
            recommendations.append(TuningRecommendation(
                action=TuningAction.ADJUST_REDIS_MAXMEMORY,
                current_value=self.db_config.current_settings.get('maxmemory', '0'),
                recommended_value=int(self.db_config.hardware_specs.get('memory_bytes', 0) * 0.8),
                expected_improvement=25,
                confidence=0.9,
                reason=f"High memory usage ({metric.current_value:.1f}MB). Configure maxmemory and eviction policy.",
                category=TuningCategory.MEMORY_OPTIMIZATION,
                effort="low",
                risk_level="medium",
                requires_restart=False,
                estimated_downtime_minutes=0.0
            ))

        if metric.name == 'hit_ratio' and metric.current_value < 85:
            recommendations.append(TuningRecommendation(
                action=TuningAction.ADJUST_REDIS_MAXMEMORY,
                current_value=self.db_config.current_settings.get('maxmemory', '0'),
                recommended_value=int(metric.current_value * 1.2 * 1024 * 1024),  # 20% increase
                expected_improvement=min((85 - metric.current_value) / 10, 30),
                confidence=0.7,
                reason=f"Low hit ratio ({metric.current_value:.1f}%). Increasing memory may improve cache performance.",
                category=TuningCategory.MEMORY_OPTIMIZATION,
                effort="low",
                risk_level="low",
                requires_restart=False,
                estimated_downtime_minutes=0.0
            ))

        return recommendations

    async def apply_tuning_recommendation(self, recommendation: TuningRecommendation) -> TuningResult:
        """Apply a tuning recommendation"""

        if not self.tuning_enabled:
            raise RuntimeError("Tuning is disabled")

        # Check if recommendation is safe to apply automatically
        if recommendation.risk_level == "high" and not self.auto_apply_safe_changes:
            raise ValueError("High-risk changes require manual approval")

        try:
            result = await self._execute_tuning_action(recommendation)

            # Record the change
            self.tuning_history.append(result)

            # Update baseline if change was successful
            if result.applied:
                await self._establish_baseline()

            return result

        except Exception as e:
            error_result = TuningResult(
                recommendation=recommendation,
                applied=False,
                actual_improvement=0.0,
                new_value=None,
                error_message=str(e),
                applied_at=datetime.now(),
                rollback_available=False
            )
            return error_result

    async def _execute_tuning_action(self, recommendation: TuningRecommendation) -> TuningResult:
        """Execute the actual tuning action"""

        if self.database_type == 'postgresql':
            return await self._execute_postgresql_tuning(recommendation)
        elif self.database_type == 'mongodb':
            return await self._execute_mongodb_tuning(recommendation)
        elif self.database_type == 'redis':
            return await self._execute_redis_tuning(recommendation)
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    async def _execute_postgresql_tuning(self, recommendation: TuningRecommendation) -> TuningResult:
        """Execute PostgreSQL tuning action"""

        conn = await create_pool(**self.connection_params)

        try:
            async with conn.acquire() as connection:
                if recommendation.action == TuningAction.INCREASE_WORK_MEM:
                    await connection.execute(f"ALTER SYSTEM SET work_mem = '{recommendation.recommended_value}'")
                    if not recommendation.requires_restart:
                        await connection.execute("SELECT pg_reload_conf()")

                elif recommendation.action == TuningAction.INCREASE_SHARED_BUFFERS:
                    await connection.execute(f"ALTER SYSTEM SET shared_buffers = '{recommendation.recommended_value}'")
                    await connection.execute("SELECT pg_reload_conf()")

                elif recommendation.action == TuningAction.ADJUST_CONNECTION_LIMITS:
                    await connection.execute(f"ALTER SYSTEM SET max_connections = {recommendation.recommended_value}")
                    await connection.execute("SELECT pg_reload_conf()")

                elif recommendation.action == TuningAction.TUNE_RANDOM_PAGE_COST:
                    await connection.execute(f"ALTER SYSTEM SET random_page_cost = {recommendation.recommended_value}")
                    if not recommendation.requires_restart:
                        await connection.execute("SELECT pg_reload_conf()")

                return TuningResult(
                    recommendation=recommendation,
                    applied=True,
                    actual_improvement=0.0,  # Would be measured after implementation
                    new_value=recommendation.recommended_value,
                    error_message=None,
                    applied_at=datetime.now(),
                    rollback_available=True
                )

        except Exception as e:
            return TuningResult(
                recommendation=recommendation,
                applied=False,
                actual_improvement=0.0,
                new_value=None,
                error_message=str(e),
                applied_at=datetime.now(),
                rollback_available=False
            )

    async def _execute_mongodb_tuning(self, recommendation: TuningRecommendation) -> TuningResult:
        """Execute MongoDB tuning action"""

        client = pymongo.MongoClient(**self.connection_params)
        admin_db = client.admin

        try:
            if recommendation.action == TuningAction.TUNE_MONGODB_CACHE_SIZE:
                # MongoDB cache size is typically set at startup
                # This would require a restart
                config = {"wiredTiger": {"engineConfig": {"cacheSizeGB": recommendation.recommended_value}}}
                admin_db.command("setParameter", 1, config)

            return TuningResult(
                recommendation=recommendation,
                applied=True,
                actual_improvement=0.0,
                new_value=recommendation.recommended_value,
                error_message=None,
                applied_at=datetime.now(),
                rollback_available=True
            )

        except Exception as e:
            return TuningResult(
                recommendation=recommendation,
                applied=False,
                actual_improvement=0.0,
                new_value=None,
                error_message=str(e),
                applied_at=datetime.now(),
                rollback_available=False
            )

    async def _execute_redis_tuning(self, recommendation: TuningRecommendation) -> TuningResult:
        """Execute Redis tuning action"""

        redis_client = redis.Redis(**self.connection_params)

        try:
            if recommendation.action == TuningAction.ADJUST_REDIS_MAXMEMORY:
                redis_client.config_set("maxmemory", recommendation.recommended_value)

            return TuningResult(
                recommendation=recommendation,
                applied=True,
                actual_improvement=0.0,
                new_value=recommendation.recommended_value,
                error_message=None,
                applied_at=datetime.now(),
                rollback_available=True
            )

        except Exception as e:
            return TuningResult(
                recommendation=recommendation,
                applied=False,
                actual_improvement=0.0,
                new_value=None,
                error_message=str(e),
                applied_at=datetime.now(),
                rollback_available=False
            )

    def _filter_recommendations(self, recommendations: List[TuningRecommendation]) -> List[TuningRecommendation]:
        """Filter recommendations based on confidence and risk"""

        filtered = []

        for rec in recommendations:
            if (rec.confidence >= self.min_confidence_threshold and
                self._is_acceptable_risk(rec.risk_level)):
                filtered.append(rec)

        return filtered

    def _prioritize_recommendations(self, recommendations: List[TuningRecommendation]) -> List[TuningRecommendation]:
        """Prioritize recommendations by expected improvement and effort"""

        def priority_score(rec):
            # Higher score for higher expected improvement and lower effort
            effort_score = {"low": 3, "medium": 2, "high": 1}[rec.effort]
            return rec.expected_improvement * effort_score * rec.confidence

        return sorted(recommendations, key=priority_score, reverse=True)

    def _is_acceptable_risk(self, risk_level: str) -> bool:
        """Check if risk level is acceptable"""

        risk_scores = {"low": 1, "medium": 2, "high": 3}
        current_risk = risk_scores.get(self.max_risk_level, 2)
        recommendation_risk = risk_scores.get(risk_level, 3)

        return recommendation_risk <= current_risk

    # Helper methods for configuration and calculations
    def _get_target_value(self, metric_name: str) -> float:
        """Get target value for metric"""
        targets = {
            'cache_hit_ratio': 95.0,
            'avg_query_time': 100.0,
            'active_connections': 50.0,
            'index_usage_ratio': 95.0,
            'hit_ratio': 90.0,
            'memory_usage_mb': 80.0  # Percentage of available memory
        }
        return targets.get(metric_name, 0.0)

    def _get_threshold_min(self, metric_name: str) -> float:
        """Get minimum threshold for metric"""
        thresholds = {
            'cache_hit_ratio': 90.0,
            'avg_query_time': 0.0,
            'active_connections': 0.0,
            'index_usage_ratio': 80.0,
            'hit_ratio': 85.0,
            'memory_usage_mb': 0.0
        }
        return thresholds.get(metric_name, 0.0)

    def _get_threshold_max(self, metric_name: str) -> float:
        """Get maximum threshold for metric"""
        thresholds = {
            'cache_hit_ratio': 100.0,
            'avg_query_time': 500.0,
            'active_connections': 100.0,
            'index_usage_ratio': 100.0,
            'hit_ratio': 100.0,
            'memory_usage_mb': 90.0  # Percentage of available memory
        }
        return thresholds.get(metric_name, 100.0)

    def _get_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        units = {
            'cache_hit_ratio': '%',
            'avg_query_time': 'ms',
            'active_connections': 'count',
            'index_usage_ratio': '%',
            'hit_ratio': '%',
            'memory_usage_mb': 'MB'
        }
        return units.get(metric_name, '')

    def _get_category(self, metric_name: str) -> TuningCategory:
        """Get category for metric"""
        categories = {
            'cache_hit_ratio': TuningCategory.MEMORY_OPTIMIZATION,
            'avg_query_time': TuningCategory.QUERY_PERFORMANCE,
            'active_connections': TuningCategory.CONNECTION_MANAGEMENT,
            'index_usage_ratio': TuningCategory.QUERY_PERFORMANCE,
            'hit_ratio': TuningCategory.MEMORY_OPTIMIZATION,
            'memory_usage_mb': TuningCategory.MEMORY_OPTIMIZATION
        }
        return categories.get(metric_name, TuningCategory.CONFIGURATION)

    def _calculate_impact_score(self, metric_name: str, value: float) -> float:
        """Calculate impact score for metric"""
        # Simplified impact calculation
        if metric_name == 'avg_query_time':
            return min(value / 1000, 1.0)  # Higher impact for slower queries
        elif metric_name == 'cache_hit_ratio':
            return max(0, (100 - value) / 100)  # Higher impact for lower hit ratios
        elif metric_name == 'active_connections':
            return min(value / 100, 1.0)  # Higher impact for more connections
        else:
            return 0.5  # Default medium impact

    def _calculate_optimal_shared_buffers(self) -> str:
        """Calculate optimal shared_buffers setting"""
        # Rule of thumb: 25% of RAM, but not more than 8GB on most systems
        ram_gb = self.db_config.hardware_specs.get('memory_mb', 4096) / 1024
        optimal_gb = min(ram_gb * 0.25, 8)
        return f"{int(optimal_gb * 1024)}MB"

    def _calculate_optimal_work_mem(self) -> str:
        """Calculate optimal work_mem setting"""
        # Rule of thumb: (RAM - shared_buffers) / max_connections / 4
        ram_mb = self.db_config.hardware_specs.get('memory_mb', 4096)
        shared_buffers_mb = 1024  # Default assumption
        max_connections = int(self.db_config.current_settings.get('max_connections', 100))
        optimal_mb = max(4, int((ram_mb - shared_buffers_mb) / max_connections / 4))
        return f"{optimal_mb}MB"

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(self.monitoring_interval)

                # Collect current metrics
                current_metrics = await self._collect_current_metrics()

                # Store metrics in history
                for metric in current_metrics:
                    self.metrics_history[metric.name].append(metric)
                    # Keep only last 100 measurements
                    if len(self.metrics_history[metric.name]) > 100:
                        self.metrics_history[metric.name].popleft()

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

    async def _analysis_loop(self) -> None:
        """Background analysis loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                # Generate recommendations
                recommendations = await self.analyze_performance()

                # Update active recommendations
                self.active_recommendations = recommendations

                if recommendations:
                    logger.info(f"Generated {len(recommendations)} tuning recommendations")

                    # Auto-apply safe changes if enabled
                    if self.auto_apply_safe_changes:
                        for rec in recommendations:
                            if (rec.risk_level == "low" and
                                rec.confidence >= 0.8 and
                                rec.effort == "low"):
                                try:
                                    result = await self.apply_tuning_recommendation(rec)
                                    if result.applied:
                                        logger.info(f"Auto-applied tuning: {rec.action.value}")
                                except Exception as e:
                                    logger.error(f"Failed to auto-apply tuning: {e}")

            except Exception as e:
                logger.error(f"Analysis loop error: {e}")

    async def _tuning_loop(self) -> None:
        """Background tuning loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(600)  # Check every 10 minutes

                # Evaluate active recommendations
                if self.active_recommendations:
                    # This would implement more sophisticated tuning logic
                    pass

            except Exception as e:
                logger.error(f"Tuning loop error: {e}")

    async def _get_postgresql_hardware_info(self, connection) -> Dict[str, Any]:
        """Get PostgreSQL hardware information"""
        return {
            'cpu_count': 4,  # Simplified
            'memory_mb': 8192,  # Simplified
            'disk_space_gb': 500  # Simplified
        }

    async def _analyze_postgresql_workload(self, connection) -> Dict[str, Any]:
        """Analyze PostgreSQL workload profile"""
        return {
            'read_write_ratio': 0.7,
            'avg_query_complexity': 'medium',
            'peak_hour_traffic': True
        }

    async def _analyze_mongodb_workload(self, client) -> Dict[str, Any]:
        """Analyze MongoDB workload profile"""
        return {
            'read_write_ratio': 0.6,
            'document_size_avg': 1024,
            'query_complexity': 'medium'
        }

    async def _analyze_redis_workload(self, redis_client) -> Dict[str, Any]:
        """Analyze Redis workload profile"""
        return {
            'key_count': redis_client.dbsize(),
            'avg_key_size': 100,
            'operations_pattern': 'mixed'
        }

    def get_tuning_report(self) -> Dict[str, Any]:
        """Get comprehensive tuning report"""

        return {
            'database_type': self.database_type,
            'database_version': self.db_config.version if self.db_config else 'Unknown',
            'active_recommendations': [asdict(rec) for rec in self.active_recommendations],
            'tuning_history': [asdict(result) for result in self.tuning_history[-10:]],  # Last 10 changes
            'performance_baseline': self.performance_baseline,
            'current_metrics': {
                name: list(metrics)[-1].current_value if metrics else 0
                for name, metrics in self.metrics_history.items()
            },
            'tuning_enabled': self.tuning_enabled,
            'auto_apply_enabled': self.auto_apply_safe_changes
        }

    async def close(self) -> None:
        """Close the performance tuner"""

        logger.info("Closing performance tuner")

        self._shutdown = True

        # Cancel background tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.analysis_task:
            self.analysis_task.cancel()
        if self.tuning_task:
            self.tuning_task.cancel()

        logger.info("Performance tuner closed")

# Example usage
async def main():
    """Example usage of the database performance tuner"""

    # PostgreSQL example
    pg_connection_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'test_db'
    }

    tuner = DatabasePerformanceTuner('postgresql', pg_connection_params)

    try:
        # Initialize tuner
        success = await tuner.initialize()
        if success:
            print("Performance tuner initialized successfully")

            # Analyze performance
            recommendations = await tuner.analyze_performance()
            print(f"Generated {len(recommendations)} tuning recommendations")

            # Show top recommendations
            for i, rec in enumerate(recommendations[:3]):
                print(f"\nRecommendation {i+1}:")
                print(f"  Action: {rec.action.value}")
                print(f"  Expected improvement: {rec.expected_improvement:.1f}%")
                print(f"  Reason: {rec.reason}")
                print(f"  Risk level: {rec.risk_level}")
                print(f"  Requires restart: {rec.requires_restart}")

            # Apply a safe recommendation (if any)
            safe_recommendations = [r for r in recommendations if r.risk_level == "low"]
            if safe_recommendations:
                result = await tuner.apply_tuning_recommendation(safe_recommendations[0])
                print(f"\nApplied tuning: {result.applied}")
                if result.error_message:
                    print(f"Error: {result.error_message}")

            # Get tuning report
            report = tuner.get_tuning_report()
            print(f"\nTuning report generated with {len(report['active_recommendations'])} active recommendations")

        else:
            print("Failed to initialize performance tuner")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        await tuner.close()
        print("Performance tuner closed")

if __name__ == "__main__":
    asyncio.run(main())