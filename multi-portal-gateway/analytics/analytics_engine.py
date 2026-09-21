#!/usr/bin/env python3
"""
DMLogn8n Analytics Engine
Main analytics processing engine for real-time and batch analytics
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import aiohttp
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

# Import analytics components
from collectors.event_collector import EventCollector
from collectors.user_tracker import UserTracker
from collectors.business_metrics import BusinessMetricsCollector
from processors.stream_processor import StreamProcessor
from processors.batch_processor import BatchProcessor
from processors.aggregator import DataAggregator
from ml.predictor import PredictiveAnalytics
from ml.clustering import UserClustering
from ml.churn_prediction import ChurnPredictor
from reporting.dashboard_generator import DashboardGenerator
from reporting.report_builder import ReportBuilder
from funnel_analyzer import FunnelAnalyzer
from cohort_analyzer import CohortAnalyzer


@dataclass
class AnalyticsConfig:
    """Analytics engine configuration"""
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql://user:pass@localhost/dmlogn8n_analytics"
    kafka_bootstrap_servers: str = "localhost:9092"
    batch_size: int = 1000
    stream_buffer_size: int = 10000
    retention_days: int = 90
    ml_model_update_interval: int = 3600  # 1 hour
    dashboard_refresh_interval: int = 300  # 5 minutes


@dataclass
class AnalyticsEvent:
    """Standard analytics event structure"""
    event_id: str
    event_type: str
    user_id: str
    session_id: str
    timestamp: datetime
    properties: Dict[str, Any]
    source: str
    version: str = "1.0"


class AnalyticsEngine:
    """Main analytics processing engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Initialize connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Initialize components
        self.event_collector = EventCollector(config)
        self.user_tracker = UserTracker(config)
        self.business_metrics = BusinessMetricsCollector(config)
        self.stream_processor = StreamProcessor(config)
        self.batch_processor = BatchProcessor(config)
        self.data_aggregator = DataAggregator(config)
        self.predictor = PredictiveAnalytics(config)
        self.clustering = UserClustering(config)
        self.churn_predictor = ChurnPredictor(config)
        self.dashboard_generator = DashboardGenerator(config)
        self.report_builder = ReportBuilder(config)
        self.funnel_analyzer = FunnelAnalyzer(config)
        self.cohort_analyzer = CohortAnalyzer(config)

        # Runtime state
        self.is_running = False
        self.event_buffer = deque(maxlen=config.stream_buffer_size)
        self.metrics_cache = {}
        self.last_ml_update = time.time()

        self.logger.info("Analytics Engine initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup analytics engine logging"""
        logger = logging.getLogger("analytics_engine")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def start(self):
        """Start the analytics engine"""
        self.logger.info("Starting Analytics Engine...")
        self.is_running = True

        # Start background tasks
        tasks = [
            self._process_events_stream(),
            self._run_batch_processing(),
            self._update_ml_models(),
            self._refresh_dashboards(),
            self._cleanup_old_data(),
            self._monitor_system_health()
        ]

        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop the analytics engine"""
        self.logger.info("Stopping Analytics Engine...")
        self.is_running = False

        # Flush remaining events
        await self._flush_event_buffer()

        # Close connections
        self.redis_client.close()
        self.db_session.close()

        self.logger.info("Analytics Engine stopped")

    async def track_event(self, event: AnalyticsEvent):
        """Track a new analytics event"""
        try:
            # Add to buffer for stream processing
            self.event_buffer.append(event)

            # Store in Redis for real-time queries
            await self._store_event_redis(event)

            # Update real-time metrics
            await self._update_real_time_metrics(event)

            self.logger.debug(f"Event tracked: {event.event_type} for user {event.user_id}")

        except Exception as e:
            self.logger.error(f"Error tracking event: {e}")
            raise

    async def get_user_analytics(self, user_id: str,
                               time_range: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific user"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_range

            # Get user behavior data
            behavior_data = await self.user_tracker.get_user_behavior(
                user_id, start_time, end_time
            )

            # Get user predictions
            predictions = await self.predictor.get_user_predictions(user_id)

            # Get churn risk
            churn_risk = await self.churn_predictor.predict_churn_risk(user_id)

            # Get user segment
            segment = await self.clustering.get_user_segment(user_id)

            # Get session history
            sessions = await self.user_tracker.get_user_sessions(user_id, time_range)

            return {
                'user_id': user_id,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'behavior': behavior_data,
                'predictions': predictions,
                'churn_risk': churn_risk,
                'segment': segment,
                'sessions': sessions,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting user analytics: {e}")
            raise

    async def get_business_metrics(self, time_range: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Get business KPIs and metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_range

            # Get core business metrics
            metrics = await self.business_metrics.get_business_metrics(start_time, end_time)

            # Get funnel analysis
            funnel_data = await self.funnel_analyzer.get_funnel_analysis(time_range)

            # Get cohort analysis
            cohort_data = await self.cohort_analyzer.get_cohort_analysis(time_range)

            # Get system performance metrics
            performance_metrics = await self._get_performance_metrics(time_range)

            return {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'business_metrics': metrics,
                'funnel_analysis': funnel_data,
                'cohort_analysis': cohort_data,
                'performance_metrics': performance_metrics,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting business metrics: {e}")
            raise

    async def generate_dashboard(self, dashboard_type: str,
                               filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate analytics dashboard"""
        try:
            return await self.dashboard_generator.generate_dashboard(
                dashboard_type, filters or {}
            )
        except Exception as e:
            self.logger.error(f"Error generating dashboard: {e}")
            raise

    async def generate_report(self, report_type: str,
                            time_range: timedelta = timedelta(days=30),
                            format: str = "json") -> Dict[str, Any]:
        """Generate automated analytics report"""
        try:
            return await self.report_builder.build_report(
                report_type, time_range, format
            )
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            raise

    # Private methods

    async def _process_events_stream(self):
        """Process events in real-time stream"""
        self.logger.info("Starting event stream processing...")

        while self.is_running:
            try:
                if self.event_buffer:
                    # Process batch of events
                    events = []
                    for _ in range(min(self.config.batch_size, len(self.event_buffer))):
                        events.append(self.event_buffer.popleft())

                    if events:
                        await self.stream_processor.process_events(events)

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                self.logger.error(f"Error in event stream processing: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _run_batch_processing(self):
        """Run batch processing tasks"""
        self.logger.info("Starting batch processing...")

        while self.is_running:
            try:
                # Run batch processing every hour
                await self.batch_processor.process_batch()
                await asyncio.sleep(3600)

            except Exception as e:
                self.logger.error(f"Error in batch processing: {e}")
                await asyncio.sleep(300)  # Back off on error

    async def _update_ml_models(self):
        """Update machine learning models"""
        self.logger.info("Starting ML model updates...")

        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_ml_update >= self.config.ml_model_update_interval:

                    # Update all ML models
                    await self.predictor.update_models()
                    await self.clustering.update_clusters()
                    await self.churn_predictor.update_model()

                    self.last_ml_update = current_time
                    self.logger.info("ML models updated successfully")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error updating ML models: {e}")
                await asyncio.sleep(1800)  # Back off on error

    async def _refresh_dashboards(self):
        """Refresh dashboard caches"""
        self.logger.info("Starting dashboard refresh...")

        while self.is_running:
            try:
                await self.dashboard_generator.refresh_all_dashboards()
                await asyncio.sleep(self.config.dashboard_refresh_interval)

            except Exception as e:
                self.logger.error(f"Error refreshing dashboards: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_data(self):
        """Clean up old analytics data"""
        self.logger.info("Starting data cleanup...")

        while self.is_running:
            try:
                # Run cleanup daily
                cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
                await self._cleanup_events_before(cutoff_date)
                await asyncio.sleep(86400)  # 24 hours

            except Exception as e:
                self.logger.error(f"Error in data cleanup: {e}")
                await asyncio.sleep(3600)

    async def _monitor_system_health(self):
        """Monitor analytics system health"""
        self.logger.info("Starting system health monitoring...")

        while self.is_running:
            try:
                health_metrics = await self._get_health_metrics()

                # Check for issues
                if health_metrics['error_rate'] > 0.05:  # 5% error rate threshold
                    self.logger.warning(f"High error rate detected: {health_metrics['error_rate']}")

                if health_metrics['memory_usage'] > 0.85:  # 85% memory usage threshold
                    self.logger.warning(f"High memory usage detected: {health_metrics['memory_usage']}")

                # Store health metrics
                await self._store_health_metrics(health_metrics)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(300)

    async def _store_event_redis(self, event: AnalyticsEvent):
        """Store event in Redis for real-time access"""
        key = f"analytics:events:{event.event_type}:{event.timestamp.strftime('%Y%m%d')}"
        await self.redis_client.lpush(key, json.dumps(asdict(event)))
        await self.redis_client.expire(key, 86400)  # Expire after 24 hours

    async def _update_real_time_metrics(self, event: AnalyticsEvent):
        """Update real-time metrics counters"""
        # Update event counters
        counter_key = f"analytics:counters:{event.event_type}"
        await self.redis_client.incr(counter_key)
        await self.redis_client.expire(counter_key, 86400)

        # Update user activity
        user_key = f"analytics:users:active:{datetime.utcnow().strftime('%Y%m%d')}"
        await self.redis_client.sadd(user_key, event.user_id)
        await self.redis_client.expire(user_key, 86400)

    async def _flush_event_buffer(self):
        """Flush remaining events in buffer"""
        if self.event_buffer:
            events = list(self.event_buffer)
            self.event_buffer.clear()
            await self.stream_processor.process_events(events)

    async def _get_performance_metrics(self, time_range: timedelta) -> Dict[str, Any]:
        """Get system performance metrics"""
        # Implementation would collect system performance data
        return {
            'avg_response_time': 150,  # ms
            'error_rate': 0.01,  # 1%
            'throughput': 1000,  # events per second
            'uptime': 0.9999  # 99.99%
        }

    async def _cleanup_events_before(self, cutoff_date: datetime):
        """Clean up events older than cutoff date"""
        # Implementation would clean up old data from database
        pass

    async def _get_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'error_rate': 0.01,
            'memory_usage': 0.65,
            'cpu_usage': 0.45,
            'queue_size': len(self.event_buffer),
            'active_connections': 100
        }

    async def _store_health_metrics(self, metrics: Dict[str, Any]):
        """Store health metrics"""
        key = f"analytics:health:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        await self.redis_client.set(key, json.dumps(metrics), ex=86400)


# Analytics engine factory
def create_analytics_engine(config: AnalyticsConfig = None) -> AnalyticsEngine:
    """Create analytics engine instance"""
    if config is None:
        config = AnalyticsConfig()
    return AnalyticsEngine(config)


# Example usage
async def main():
    """Example usage of the analytics engine"""
    config = AnalyticsConfig()
    engine = create_analytics_engine(config)

    try:
        await engine.start()
    except KeyboardInterrupt:
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())