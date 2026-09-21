#!/usr/bin/env python3
"""
Data Aggregator
Advanced data aggregation and rollup capabilities for analytics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import redis
from enum import Enum

from ..analytics_engine import AnalyticsConfig


class AggregationType(Enum):
    """Types of aggregations"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    RATE = "rate"
    RATIO = "ratio"


class TimeGranularity(Enum):
    """Time granularity levels"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class AggregationRule:
    """Aggregation rule definition"""
    rule_id: str
    name: str
    source_table: str
    metric_column: str
    aggregation_type: AggregationType
    dimensions: List[str]
    filters: Dict[str, Any]
    time_column: str
    granularity: TimeGranularity
    enabled: bool = True


@dataclass
class AggregationResult:
    """Result of an aggregation operation"""
    rule_id: str
    time_period: str
    dimensions: Dict[str, Any]
    value: Union[int, float, str]
    sample_size: int
    confidence_interval: Optional[Tuple[float, float]] = None


class DataAggregator:
    """Advanced data aggregation engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Aggregation state
        self.aggregation_rules = {}
        self.aggregation_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Initialize database tables
        self._initialize_tables()

        # Initialize default aggregation rules
        self._initialize_default_rules()

    def _setup_logging(self) -> logging.Logger:
        """Setup data aggregator logging"""
        logger = logging.getLogger("data_aggregator")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for aggregations"""
        try:
            # Create aggregated_metrics table
            create_metrics_table = """
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id SERIAL PRIMARY KEY,
                rule_id VARCHAR(100) NOT NULL,
                time_period VARCHAR(20) NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                dimensions TEXT,
                metric_value DECIMAL(20,4),
                sample_size INTEGER,
                confidence_interval TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rule_id, time_period, period_start, period_end, dimensions)
            );
            """

            # Create aggregation_rules table
            create_rules_table = """
            CREATE TABLE IF NOT EXISTS aggregation_rules (
                rule_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                source_table VARCHAR(100) NOT NULL,
                metric_column VARCHAR(100) NOT NULL,
                aggregation_type VARCHAR(20) NOT NULL,
                dimensions TEXT,
                filters TEXT,
                time_column VARCHAR(100) NOT NULL,
                granularity VARCHAR(20) NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create materialized views for common aggregations
            create_user_metrics_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS user_metrics_hourly AS
            SELECT
                DATE_TRUNC('hour', start_time) as hour,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_sessions,
                AVG(duration) as avg_session_duration,
                SUM(page_views) as total_page_views
            FROM user_sessions
            GROUP BY DATE_TRUNC('hour', start_time);
            """

            create_event_metrics_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS event_metrics_hourly AS
            SELECT
                DATE_TRUNC('hour', timestamp) as hour,
                event_type,
                COUNT(*) as event_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM events
            GROUP BY DATE_TRUNC('hour', timestamp), event_type;
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_rule_period ON aggregated_metrics(rule_id, time_period);",
                "CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_time ON aggregated_metrics(period_start, period_end);",
                "CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_dimensions ON aggregated_metrics(dimensions);",
                "CREATE INDEX IF NOT EXISTS idx_user_metrics_hourly_hour ON user_metrics_hourly(hour);",
                "CREATE INDEX IF NOT EXISTS idx_event_metrics_hourly_hour ON event_metrics_hourly(hour);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_metrics_table))
                conn.execute(text(create_rules_table))
                conn.execute(text(create_user_metrics_view))
                conn.execute(text(create_event_metrics_view))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Aggregation tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing aggregation tables: {e}")

    def _initialize_default_rules(self):
        """Initialize default aggregation rules"""
        default_rules = [
            AggregationRule(
                rule_id="daily_active_users",
                name="Daily Active Users",
                source_table="user_sessions",
                metric_column="user_id",
                aggregation_type=AggregationType.DISTINCT_COUNT,
                dimensions=[],
                filters={},
                time_column="start_time",
                granularity=TimeGranularity.DAY
            ),
            AggregationRule(
                rule_id="hourly_page_views",
                name="Hourly Page Views",
                source_table="user_sessions",
                metric_column="page_views",
                aggregation_type=AggregationType.SUM,
                dimensions=["device_info->>'device_type'"],
                filters={},
                time_column="start_time",
                granularity=TimeGranularity.HOUR
            ),
            AggregationRule(
                rule_id="daily_revenue",
                name="Daily Revenue",
                source_table="transactions",
                metric_column="amount",
                aggregation_type=AggregationType.SUM,
                dimensions=["transaction_type"],
                filters={"status": "completed"},
                time_column="created_at",
                granularity=TimeGranularity.DAY
            ),
            AggregationRule(
                rule_id="weekly_retention",
                name="Weekly User Retention",
                source_table="user_sessions",
                metric_column="user_id",
                aggregation_type=AggregationType.DISTINCT_COUNT,
                dimensions=["cohort_week"],
                filters={},
                time_column="start_time",
                granularity=TimeGranularity.WEEK
            ),
            AggregationRule(
                rule_id="monthly_feature_adoption",
                name="Monthly Feature Adoption",
                source_table="events",
                metric_column="user_id",
                aggregation_type=AggregationType.DISTINCT_COUNT,
                dimensions=["event_type"],
                filters={"event_type": ["character_created", "session_completed", "social_interaction"]},
                time_column="timestamp",
                granularity=TimeGranularity.MONTH
            )
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: AggregationRule):
        """Add an aggregation rule"""
        try:
            # Store in database
            query = text("""
                INSERT INTO aggregation_rules (
                    rule_id, name, source_table, metric_column, aggregation_type,
                    dimensions, filters, time_column, granularity, enabled
                ) VALUES (
                    :rule_id, :name, :source_table, :metric_column, :aggregation_type,
                    :dimensions, :filters, :time_column, :granularity, :enabled
                )
                ON CONFLICT (rule_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    source_table = EXCLUDED.source_table,
                    metric_column = EXCLUDED.metric_column,
                    aggregation_type = EXCLUDED.aggregation_type,
                    dimensions = EXCLUDED.dimensions,
                    filters = EXCLUDED.filters,
                    time_column = EXCLUDED.time_column,
                    granularity = EXCLUDED.granularity,
                    enabled = EXCLUDED.enabled,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'source_table': rule.source_table,
                    'metric_column': rule.metric_column,
                    'aggregation_type': rule.aggregation_type.value,
                    'dimensions': json.dumps(rule.dimensions),
                    'filters': json.dumps(rule.filters),
                    'time_column': rule.time_column,
                    'granularity': rule.granularity.value,
                    'enabled': rule.enabled
                })
                conn.commit()

            self.aggregation_rules[rule.rule_id] = rule
            self.logger.info(f"Added aggregation rule: {rule.name}")

        except Exception as e:
            self.logger.error(f"Error adding aggregation rule: {e}")

    async def execute_aggregation(self, rule_id: str,
                                start_time: datetime,
                                end_time: datetime,
                                force_refresh: bool = False) -> List[AggregationResult]:
        """Execute aggregation for a specific rule"""
        try:
            rule = self.aggregation_rules.get(rule_id)
            if not rule:
                raise ValueError(f"Aggregation rule not found: {rule_id}")

            # Check cache first
            cache_key = f"aggregation:{rule_id}:{start_time.isoformat()}:{end_time.isoformat()}"
            if not force_refresh:
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    cached_data = json.loads(cached_result)
                    return [AggregationResult(**item) for item in cached_data]

            # Execute aggregation
            results = await self._execute_rule_aggregation(rule, start_time, end_time)

            # Cache results
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps([asdict(result) for result in results], default=str)
            )

            # Store in database
            await self._store_aggregation_results(results)

            self.logger.info(f"Executed aggregation {rule_id}: {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"Error executing aggregation {rule_id}: {e}")
            raise

    async def _execute_rule_aggregation(self, rule: AggregationRule,
                                      start_time: datetime,
                                      end_time: datetime) -> List[AggregationResult]:
        """Execute aggregation for a specific rule"""
        try:
            # Build SQL query based on rule
            query = self._build_aggregation_query(rule, start_time, end_time)

            with self.db_engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()

            results = []
            for row in rows:
                # Parse dimensions
                dimensions = {}
                if rule.dimensions:
                    for dim in rule.dimensions:
                        if dim in row._fields:
                            dimensions[dim] = getattr(row, dim.replace('->>', '_').replace('.', '_'))

                # Get value and sample size
                value = getattr(row, 'metric_value')
                sample_size = getattr(row, 'sample_size', 0)

                # Calculate confidence interval for statistical aggregates
                confidence_interval = None
                if rule.aggregation_type in [AggregationType.AVERAGE, AggregationType.RATE]:
                    confidence_interval = self._calculate_confidence_interval(
                        value, sample_size, 0.95
                    )

                result = AggregationResult(
                    rule_id=rule.rule_id,
                    time_period=rule.granularity.value,
                    dimensions=dimensions,
                    value=value,
                    sample_size=sample_size,
                    confidence_interval=confidence_interval
                )
                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Error executing rule aggregation: {e}")
            raise

    def _build_aggregation_query(self, rule: AggregationRule,
                              start_time: datetime,
                              end_time: datetime) -> str:
        """Build SQL query for aggregation"""
        try:
            # Base query parts
            select_parts = []
            group_by_parts = []

            # Time grouping
            if rule.granularity == TimeGranularity.MINUTE:
                time_trunc = "DATE_TRUNC('minute', {})".format(rule.time_column)
            elif rule.granularity == TimeGranularity.HOUR:
                time_trunc = "DATE_TRUNC('hour', {})".format(rule.time_column)
            elif rule.granularity == TimeGranularity.DAY:
                time_trunc = "DATE_TRUNC('day', {})".format(rule.time_column)
            elif rule.granularity == TimeGranularity.WEEK:
                time_trunc = "DATE_TRUNC('week', {})".format(rule.time_column)
            elif rule.granularity == TimeGranularity.MONTH:
                time_trunc = "DATE_TRUNC('month', {})".format(rule.time_column)
            else:
                time_trunc = "DATE_TRUNC('day', {})".format(rule.time_column)

            # Build aggregation function
            if rule.aggregation_type == AggregationType.SUM:
                agg_func = f"SUM({rule.metric_column})"
            elif rule.aggregation_type == AggregationType.AVERAGE:
                agg_func = f"AVG({rule.metric_column})"
            elif rule.aggregation_type == AggregationType.COUNT:
                agg_func = f"COUNT({rule.metric_column})"
            elif rule.aggregation_type == AggregationType.DISTINCT_COUNT:
                agg_func = f"COUNT(DISTINCT {rule.metric_column})"
            elif rule.aggregation_type == AggregationType.MIN:
                agg_func = f"MIN({rule.metric_column})"
            elif rule.aggregation_type == AggregationType.MAX:
                agg_func = f"MAX({rule.metric_column})"
            elif rule.aggregation_type == AggregationType.MEDIAN:
                agg_func = f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {rule.metric_column})"
            else:
                agg_func = f"COUNT({rule.metric_column})"

            select_parts.append(f"{agg_func} as metric_value")

            # Add sample size
            if rule.aggregation_type in [AggregationType.AVERAGE, AggregationType.RATE]:
                select_parts.append(f"COUNT({rule.metric_column}) as sample_size")

            # Add dimensions
            if rule.dimensions:
                for dim in rule.dimensions:
                    # Handle JSON column access
                    if '->' in dim:
                        select_parts.append(f"{dim} as {dim.replace('->>', '_').replace('.', '_')}")
                        group_by_parts.append(dim)
                    else:
                        select_parts.append(dim)
                        group_by_parts.append(dim)

            # Build WHERE clause
            where_conditions = [
                f"{rule.time_column} >= '{start_time.isoformat()}'",
                f"{rule.time_column} <= '{end_time.isoformat()}'"
            ]

            # Add filters
            for column, value in rule.filters.items():
                if isinstance(value, list):
                    where_conditions.append(f"{column} IN ({', '.join([f"'{v}'" for v in value])})")
                elif isinstance(value, dict):
                    # Handle range filters
                    if 'min' in value:
                        where_conditions.append(f"{column} >= {value['min']}")
                    if 'max' in value:
                        where_conditions.append(f"{column} <= {value['max']}")
                else:
                    where_conditions.append(f"{column} = '{value}'")

            # Build complete query
            query = f"""
                SELECT {', '.join(select_parts)}
                FROM {rule.source_table}
                WHERE {' AND '.join(where_conditions)}
            """

            if group_by_parts:
                query += f" GROUP BY {', '.join(group_by_parts)}"

            query += " ORDER BY metric_value DESC"

            return query

        except Exception as e:
            self.logger.error(f"Error building aggregation query: {e}")
            raise

    def _calculate_confidence_interval(self, mean: float, sample_size: int,
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for mean"""
        try:
            if sample_size < 2:
                return None

            # Standard error calculation (simplified)
            # In practice, you'd use proper statistical libraries
            z_score = 1.96 if confidence_level == 0.95 else 1.645  # For 90%
            standard_error = abs(mean) / np.sqrt(sample_size) if sample_size > 0 else 0
            margin_of_error = z_score * standard_error

            return (mean - margin_of_error, mean + margin_of_error)

        except Exception:
            return None

    async def _store_aggregation_results(self, results: List[AggregationResult]):
        """Store aggregation results in database"""
        try:
            query = text("""
                INSERT INTO aggregated_metrics (
                    rule_id, time_period, period_start, period_end,
                    dimensions, metric_value, sample_size, confidence_interval
                ) VALUES (
                    :rule_id, :time_period, :period_start, :period_end,
                    :dimensions, :metric_value, :sample_size, :confidence_interval
                )
                ON CONFLICT (rule_id, time_period, period_start, period_end, dimensions)
                DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    sample_size = EXCLUDED.sample_size,
                    confidence_interval = EXCLUDED.confidence_interval
            """)

            with self.db_engine.connect() as conn:
                for result in results:
                    conn.execute(query, {
                        'rule_id': result.rule_id,
                        'time_period': result.time_period,
                        'period_start': datetime.utcnow(),  # Would calculate from rule
                        'period_end': datetime.utcnow(),    # Would calculate from rule
                        'dimensions': json.dumps(result.dimensions),
                        'metric_value': result.value,
                        'sample_size': result.sample_size,
                        'confidence_interval': json.dumps(result.confidence_interval) if result.confidence_interval else None
                    })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing aggregation results: {e}")

    async def get_aggregated_data(self, rule_id: str,
                                 start_time: datetime,
                                 end_time: datetime,
                                 dimensions: List[str] = None) -> List[Dict[str, Any]]:
        """Get aggregated data for a rule"""
        try:
            query = text("""
                SELECT * FROM aggregated_metrics
                WHERE rule_id = :rule_id
                AND period_start >= :start_time
                AND period_end <= :end_time
                ORDER BY period_start ASC
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'rule_id': rule_id,
                    'start_time': start_time,
                    'end_time': end_time
                })
                rows = result.fetchall()

            data = []
            for row in rows:
                item = {
                    'rule_id': row.rule_id,
                    'time_period': row.time_period,
                    'period_start': row.period_start.isoformat(),
                    'period_end': row.period_end.isoformat(),
                    'metric_value': float(row.metric_value),
                    'sample_size': row.sample_size
                }

                # Parse dimensions
                if row.dimensions:
                    item['dimensions'] = json.loads(row.dimensions)

                # Parse confidence interval
                if row.confidence_interval:
                    item['confidence_interval'] = json.loads(row.confidence_interval)

                data.append(item)

            return data

        except Exception as e:
            self.logger.error(f"Error getting aggregated data: {e}")
            return []

    async def get_time_series_data(self, rule_id: str,
                                 start_time: datetime,
                                 end_time: datetime,
                                 granularity: TimeGranularity = TimeGranularity.DAY) -> List[Dict[str, Any]]:
        """Get time series data for a rule"""
        try:
            # Get aggregated data
            data = await self.get_aggregated_data(rule_id, start_time, end_time)

            # Group by time period
            time_series = defaultdict(list)
            for item in data:
                period_key = item['period_start'][:10]  # Extract date
                time_series[period_key].append(item)

            # Aggregate multiple values per period
            result = []
            for period, items in sorted(time_series.items()):
                total_value = sum(item['metric_value'] for item in items)
                total_samples = sum(item['sample_size'] for item in items)

                result.append({
                    'period': period,
                    'value': total_value,
                    'sample_size': total_samples,
                    'item_count': len(items)
                })

            return result

        except Exception as e:
            self.logger.error(f"Error getting time series data: {e}")
            return []

    async def get_dimension_breakdown(self, rule_id: str,
                                   start_time: datetime,
                                   end_time: datetime,
                                   dimension: str) -> List[Dict[str, Any]]:
        """Get breakdown by dimension"""
        try:
            data = await self.get_aggregated_data(rule_id, start_time, end_time)

            # Group by dimension value
            dimension_groups = defaultdict(lambda: {'value': 0, 'sample_size': 0})
            for item in data:
                if 'dimensions' in item and dimension in item['dimensions']:
                    dim_value = item['dimensions'][dimension]
                    dimension_groups[dim_value]['value'] += item['metric_value']
                    dimension_groups[dim_value]['sample_size'] += item['sample_size']

            # Convert to list and sort
            result = []
            for dim_value, metrics in dimension_groups.items():
                result.append({
                    dimension: dim_value,
                    'value': metrics['value'],
                    'sample_size': metrics['sample_size']
                })

            return sorted(result, key=lambda x: x['value'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error getting dimension breakdown: {e}")
            return []

    async def get_comparison_data(self, rule_id: str,
                                current_period: Tuple[datetime, datetime],
                                previous_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get comparison between current and previous periods"""
        try:
            # Get data for both periods
            current_data = await self.get_aggregated_data(
                rule_id, current_period[0], current_period[1]
            )
            previous_data = await self.get_aggregated_data(
                rule_id, previous_period[0], previous_period[1]
            )

            # Calculate totals
            current_total = sum(item['metric_value'] for item in current_data)
            previous_total = sum(item['metric_value'] for item in previous_data)

            # Calculate change
            absolute_change = current_total - previous_total
            relative_change = (absolute_change / previous_total) if previous_total > 0 else 0

            return {
                'current_period': {
                    'start': current_period[0].isoformat(),
                    'end': current_period[1].isoformat(),
                    'total': current_total,
                    'data_points': len(current_data)
                },
                'previous_period': {
                    'start': previous_period[0].isoformat(),
                    'end': previous_period[1].isoformat(),
                    'total': previous_total,
                    'data_points': len(previous_data)
                },
                'change': {
                    'absolute': absolute_change,
                    'relative': relative_change,
                    'percentage': relative_change * 100
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting comparison data: {e}")
            return {}

    async def refresh_materialized_views(self):
        """Refresh materialized views for faster queries"""
        try:
            views = ['user_metrics_hourly', 'event_metrics_hourly']

            for view in views:
                query = text(f"REFRESH MATERIALIZED VIEW {view}")
                with self.db_engine.connect() as conn:
                    conn.execute(query)
                    conn.commit()

                self.logger.info(f"Refreshed materialized view: {view}")

        except Exception as e:
            self.logger.error(f"Error refreshing materialized views: {e}")

    async def get_top_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing metrics"""
        try:
            query = text("""
                SELECT
                    rule_id,
                    time_period,
                    AVG(metric_value) as avg_value,
                    COUNT(*) as data_points
                FROM aggregated_metrics
                WHERE period_start >= NOW() - INTERVAL '7 days'
                GROUP BY rule_id, time_period
                ORDER BY avg_value DESC
                LIMIT :limit
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'limit': limit})
                rows = result.fetchall()

            metrics = []
            for row in rows:
                rule = self.aggregation_rules.get(row.rule_id)
                metrics.append({
                    'rule_id': row.rule_id,
                    'rule_name': rule.name if rule else row.rule_id,
                    'time_period': row.time_period,
                    'avg_value': float(row.avg_value),
                    'data_points': row.data_points
                })

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting top metrics: {e}")
            return []

    async def get_anomaly_detection(self, rule_id: str,
                                  start_time: datetime,
                                  end_time: datetime,
                                  threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in aggregated data"""
        try:
            # Get time series data
            data = await self.get_time_series_data(rule_id, start_time, end_time)

            if len(data) < 3:
                return []

            # Calculate statistics
            values = [item['value'] for item in data]
            mean = np.mean(values)
            std = np.std(values)

            # Detect anomalies (values beyond threshold standard deviations)
            anomalies = []
            for item in data:
                z_score = abs((item['value'] - mean) / std) if std > 0 else 0
                if z_score > threshold:
                    anomalies.append({
                        'period': item['period'],
                        'value': item['value'],
                        'expected_range': [mean - threshold * std, mean + threshold * std],
                        'z_score': z_score,
                        'severity': 'high' if z_score > 3 else 'medium'
                    })

            return anomalies

        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return []

    async def run_all_aggregations(self, start_time: datetime = None,
                                 end_time: datetime = None):
        """Run all enabled aggregation rules"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(days=1)
            if end_time is None:
                end_time = datetime.utcnow()

            self.logger.info(f"Running all aggregations from {start_time} to {end_time}")

            tasks = []
            for rule_id, rule in self.aggregation_rules.items():
                if rule.enabled:
                    task = self.execute_aggregation(rule_id, start_time, end_time)
                    tasks.append(task)

            # Run aggregations concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful

            self.logger.info(f"Aggregations completed: {successful} successful, {failed} failed")

            # Refresh materialized views
            await self.refresh_materialized_views()

            return {
                'total_rules': len(self.aggregation_rules),
                'successful': successful,
                'failed': failed,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error running all aggregations: {e}")
            raise

    def get_rules(self) -> Dict[str, AggregationRule]:
        """Get all aggregation rules"""
        return self.aggregation_rules.copy()

    def update_rule(self, rule_id: str, **kwargs):
        """Update an aggregation rule"""
        try:
            if rule_id not in self.aggregation_rules:
                raise ValueError(f"Rule not found: {rule_id}")

            rule = self.aggregation_rules[rule_id]

            # Update rule attributes
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            # Update in database
            self.add_rule(rule)  # Reuse add_rule for UPSERT

            self.logger.info(f"Updated aggregation rule: {rule_id}")

        except Exception as e:
            self.logger.error(f"Error updating aggregation rule: {e}")
            raise

    def delete_rule(self, rule_id: str):
        """Delete an aggregation rule"""
        try:
            if rule_id not in self.aggregation_rules:
                raise ValueError(f"Rule not found: {rule_id}")

            # Delete from database
            query = text("DELETE FROM aggregation_rules WHERE rule_id = :rule_id")
            with self.db_engine.connect() as conn:
                conn.execute(query, {'rule_id': rule_id})
                conn.commit()

            # Remove from memory
            del self.aggregation_rules[rule_id]

            self.logger.info(f"Deleted aggregation rule: {rule_id}")

        except Exception as e:
            self.logger.error(f"Error deleting aggregation rule: {e}")
            raise