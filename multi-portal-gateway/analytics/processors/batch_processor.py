#!/usr/bin/env python3
"""
Batch Processor
Batch processing for large-scale analytics data aggregation and analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import redis
from concurrent.futures import ThreadPoolExecutor
import math

from ..analytics_engine import AnalyticsConfig


@dataclass
class BatchJob:
    """Batch job configuration"""
    job_id: str
    job_name: str
    job_type: str  # 'aggregation', 'reporting', 'ml_training', 'cleanup'
    schedule: str  # cron expression or interval
    parameters: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed'


@dataclass
class BatchResult:
    """Batch job execution result"""
    job_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    records_processed: int
    records_generated: int
    errors: List[str]
    metrics: Dict[str, Any]


class BatchProcessor:
    """Batch processing engine for analytics data"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Batch processing state
        self.is_running = False
        self.active_jobs = {}
        self.job_history = []
        self.max_concurrent_jobs = 3
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize database tables
        self._initialize_tables()

        # Initialize default batch jobs
        self._initialize_default_jobs()

    def _setup_logging(self) -> logging.Logger:
        """Setup batch processor logging"""
        logger = logging.getLogger("batch_processor")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for batch processing"""
        try:
            # Create batch_jobs table
            create_jobs_table = """
            CREATE TABLE IF NOT EXISTS batch_jobs (
                job_id VARCHAR(100) PRIMARY KEY,
                job_name VARCHAR(200) NOT NULL,
                job_type VARCHAR(50) NOT NULL,
                schedule VARCHAR(100),
                parameters TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create batch_results table
            create_results_table = """
            CREATE TABLE IF NOT EXISTS batch_results (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                records_processed INTEGER DEFAULT 0,
                records_generated INTEGER DEFAULT 0,
                errors TEXT,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES batch_jobs(job_id)
            );
            """

            # Create batch_aggregates table
            create_aggregates_table = """
            CREATE TABLE IF NOT EXISTS batch_aggregates (
                id SERIAL PRIMARY KEY,
                aggregate_type VARCHAR(50) NOT NULL,
                time_period VARCHAR(20) NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                dimensions TEXT,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(aggregate_type, time_period, period_start, period_end)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON batch_jobs(status);",
                "CREATE INDEX IF NOT EXISTS idx_jobs_next_run ON batch_jobs(next_run);",
                "CREATE INDEX IF NOT EXISTS idx_results_job_id ON batch_results(job_id);",
                "CREATE INDEX IF NOT EXISTS idx_aggregates_type_period ON batch_aggregates(aggregate_type, time_period);",
                "CREATE INDEX IF NOT EXISTS idx_aggregates_period ON batch_aggregates(period_start, period_end);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_jobs_table))
                conn.execute(text(create_results_table))
                conn.execute(text(create_aggregates_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Batch processing tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing batch processing tables: {e}")

    def _initialize_default_jobs(self):
        """Initialize default batch jobs"""
        default_jobs = [
            BatchJob(
                job_id="daily_aggregation",
                job_name="Daily Metrics Aggregation",
                job_type="aggregation",
                schedule="0 2 * * *",  # 2 AM daily
                parameters={
                    'time_window': '24h',
                    'aggregations': ['user_metrics', 'event_metrics', 'revenue_metrics']
                }
            ),
            BatchJob(
                job_id="weekly_report",
                job_name="Weekly Analytics Report",
                job_type="reporting",
                schedule="0 6 * * 1",  # 6 AM every Monday
                parameters={
                    'report_type': 'weekly_summary',
                    'recipients': ['analytics@company.com'],
                    'format': 'pdf'
                }
            ),
            BatchJob(
                job_id="user_segmentation",
                job_name="User Segmentation Update",
                job_type="ml_training",
                schedule="0 3 * * 0",  # 3 AM every Sunday
                parameters={
                    'model_type': 'clustering',
                    'features': ['engagement', 'recency', 'frequency', 'monetary']
                }
            ),
            BatchJob(
                job_id="data_cleanup",
                job_name="Data Cleanup and Archive",
                job_type="cleanup",
                schedule="0 1 * * *",  # 1 AM daily
                parameters={
                    'retention_days': 90,
                    'archive_old_data': True
                }
            ),
            BatchJob(
                job_id="hourly_rollup",
                job_name="Hourly Metrics Rollup",
                job_type="aggregation",
                schedule="0 * * * *",  # Every hour
                parameters={
                    'time_window': '1h',
                    'aggregations': ['realtime_metrics', 'performance_metrics']
                }
            )
        ]

        for job in default_jobs:
            self.add_job(job)

    def add_job(self, job: BatchJob):
        """Add a batch job"""
        try:
            # Store in database
            query = text("""
                INSERT INTO batch_jobs (
                    job_id, job_name, job_type, schedule, parameters, enabled
                ) VALUES (
                    :job_id, :job_name, :job_type, :schedule, :parameters, :enabled
                )
                ON CONFLICT (job_id) DO UPDATE SET
                    job_name = EXCLUDED.job_name,
                    job_type = EXCLUDED.job_type,
                    schedule = EXCLUDED.schedule,
                    parameters = EXCLUDED.parameters,
                    enabled = EXCLUDED.enabled,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': job.job_id,
                    'job_name': job.job_name,
                    'job_type': job.job_type,
                    'schedule': job.schedule,
                    'parameters': json.dumps(job.parameters),
                    'enabled': job.enabled
                })
                conn.commit()

            self.active_jobs[job.job_id] = job
            self.logger.info(f"Added batch job: {job.job_name}")

        except Exception as e:
            self.logger.error(f"Error adding batch job: {e}")

    async def process_batch(self):
        """Main batch processing loop"""
        self.logger.info("Starting batch processing...")

        while self.is_running:
            try:
                # Check for scheduled jobs
                scheduled_jobs = await self._get_scheduled_jobs()

                # Run jobs up to concurrency limit
                running_count = len([j for j in self.active_jobs.values() if j.status == 'running'])
                available_slots = self.max_concurrent_jobs - running_count

                for job in scheduled_jobs[:available_slots]:
                    if job.enabled and job.status != 'running':
                        await self._execute_job(job)

                # Clean up completed jobs
                await self._cleanup_completed_jobs()

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(300)  # Back off on error

    async def _get_scheduled_jobs(self) -> List[BatchJob]:
        """Get jobs that are scheduled to run"""
        try:
            current_time = datetime.utcnow()

            query = text("""
                SELECT * FROM batch_jobs
                WHERE enabled = TRUE
                AND next_run <= :current_time
                AND status != 'running'
                ORDER BY next_run ASC
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'current_time': current_time})
                rows = result.fetchall()

            jobs = []
            for row in rows:
                job = BatchJob(
                    job_id=row.job_id,
                    job_name=row.job_name,
                    job_type=row.job_type,
                    schedule=row.schedule,
                    parameters=json.loads(row.parameters) if row.parameters else {},
                    enabled=row.enabled,
                    last_run=row.last_run,
                    next_run=row.next_run,
                    status=row.status
                )
                jobs.append(job)

            return jobs

        except Exception as e:
            self.logger.error(f"Error getting scheduled jobs: {e}")
            return []

    async def _execute_job(self, job: BatchJob):
        """Execute a batch job"""
        self.logger.info(f"Executing batch job: {job.job_name}")

        job.status = 'running'
        result = BatchResult(
            job_id=job.job_id,
            status='running',
            start_time=datetime.utcnow(),
            end_time=None,
            records_processed=0,
            records_generated=0,
            errors=[],
            metrics={}
        )

        try:
            # Update job status
            await self._update_job_status(job)

            # Execute based on job type
            if job.job_type == 'aggregation':
                await self._execute_aggregation_job(job, result)
            elif job.job_type == 'reporting':
                await self._execute_reporting_job(job, result)
            elif job.job_type == 'ml_training':
                await self._execute_ml_training_job(job, result)
            elif job.job_type == 'cleanup':
                await self._execute_cleanup_job(job, result)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

            # Mark as completed
            result.status = 'completed'
            result.end_time = datetime.utcnow()

            self.logger.info(f"Batch job completed: {job.job_name}")

        except Exception as e:
            result.status = 'failed'
            result.end_time = datetime.utcnow()
            result.errors.append(str(e))
            self.logger.error(f"Batch job failed: {job.job_name} - {e}")

        finally:
            # Store result and update job
            await self._store_job_result(result)
            await self._update_job_after_execution(job, result)

    async def _execute_aggregation_job(self, job: BatchJob, result: BatchResult):
        """Execute aggregation job"""
        try:
            parameters = job.parameters
            time_window = parameters.get('time_window', '24h')
            aggregations = parameters.get('aggregations', [])

            # Calculate time range
            end_time = datetime.utcnow()
            start_time = self._parse_time_window(time_window, end_time)

            for agg_type in aggregations:
                try:
                    if agg_type == 'user_metrics':
                        await self._aggregate_user_metrics(start_time, end_time, result)
                    elif agg_type == 'event_metrics':
                        await self._aggregate_event_metrics(start_time, end_time, result)
                    elif agg_type == 'revenue_metrics':
                        await self._aggregate_revenue_metrics(start_time, end_time, result)
                    elif agg_type == 'realtime_metrics':
                        await self._aggregate_realtime_metrics(start_time, end_time, result)
                    elif agg_type == 'performance_metrics':
                        await self._aggregate_performance_metrics(start_time, end_time, result)

                except Exception as e:
                    result.errors.append(f"Error in {agg_type} aggregation: {e}")

            result.metrics['aggregation_types'] = aggregations
            result.metrics['time_window'] = time_window

        except Exception as e:
            raise Exception(f"Aggregation job failed: {e}")

    async def _execute_reporting_job(self, job: BatchJob, result: BatchResult):
        """Execute reporting job"""
        try:
            parameters = job.parameters
            report_type = parameters.get('report_type')
            recipients = parameters.get('recipients', [])
            format_type = parameters.get('format', 'pdf')

            # Generate report based on type
            if report_type == 'weekly_summary':
                report_data = await self._generate_weekly_summary()
            elif report_type == 'monthly_dashboard':
                report_data = await self._generate_monthly_dashboard()
            elif report_type == 'user_behavior_report':
                report_data = await self._generate_user_behavior_report()
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            # Send report
            await self._send_report(report_data, recipients, format_type)

            result.records_generated = 1
            result.metrics['report_type'] = report_type
            result.metrics['recipients'] = recipients
            result.metrics['format'] = format_type

        except Exception as e:
            raise Exception(f"Reporting job failed: {e}")

    async def _execute_ml_training_job(self, job: BatchJob, result: BatchResult):
        """Execute ML training job"""
        try:
            parameters = job.parameters
            model_type = parameters.get('model_type')
            features = parameters.get('features', [])

            # Get training data
            training_data = await self._get_ml_training_data(model_type, features)

            # Train model (mock implementation)
            if model_type == 'clustering':
                model_result = await self._train_clustering_model(training_data)
            elif model_type == 'churn_prediction':
                model_result = await self._train_churn_model(training_data)
            elif model_type == 'recommendation':
                model_result = await self._train_recommendation_model(training_data)
            else:
                raise ValueError(f"Unknown model type: {model_type}")

            result.records_processed = len(training_data)
            result.records_generated = 1
            result.metrics['model_type'] = model_type
            result.metrics['model_performance'] = model_result

        except Exception as e:
            raise Exception(f"ML training job failed: {e}")

    async def _execute_cleanup_job(self, job: BatchJob, result: BatchResult):
        """Execute cleanup job"""
        try:
            parameters = job.parameters
            retention_days = parameters.get('retention_days', 90)
            archive_old_data = parameters.get('archive_old_data', True)

            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Clean up old events
            events_deleted = await self._cleanup_old_events(cutoff_date)
            result.records_processed += events_deleted

            # Clean up old sessions
            sessions_deleted = await self._cleanup_old_sessions(cutoff_date)
            result.records_processed += sessions_deleted

            # Archive data if requested
            if archive_old_data:
                archived_records = await self._archive_old_data(cutoff_date)
                result.records_generated = archived_records

            result.metrics['retention_days'] = retention_days
            result.metrics['cutoff_date'] = cutoff_date.isoformat()

        except Exception as e:
            raise Exception(f"Cleanup job failed: {e}")

    # Aggregation methods

    async def _aggregate_user_metrics(self, start_time: datetime, end_time: datetime, result: BatchResult):
        """Aggregate user metrics"""
        try:
            query = text("""
                INSERT INTO batch_aggregates (
                    aggregate_type, time_period, period_start, period_end, dimensions, metrics
                ) VALUES (
                    'user_metrics', 'hourly', :start_time, :end_time,
                    :dimensions, :metrics
                )
                ON CONFLICT (aggregate_type, time_period, period_start, period_end) DO UPDATE SET
                    metrics = EXCLUDED.metrics
            """)

            # Calculate user metrics
            with self.db_engine.connect() as conn:
                # Get active users
                active_users_query = text("""
                    SELECT
                        COUNT(DISTINCT user_id) as active_users,
                        AVG(duration) as avg_session_duration,
                        COUNT(*) as total_sessions
                    FROM user_sessions
                    WHERE start_time >= :start_time AND start_time <= :end_time
                """)

                user_result = conn.execute(active_users_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                user_data = user_result.fetchone()

                # Get new users
                new_users_query = text("""
                    SELECT COUNT(DISTINCT user_id) as new_users
                    FROM user_sessions
                    WHERE start_time >= :start_time AND start_time <= :end_time
                    AND user_id NOT IN (
                        SELECT DISTINCT user_id
                        FROM user_sessions
                        WHERE start_time < :start_time
                    )
                """)

                new_users_result = conn.execute(new_users_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                new_users_data = new_users_result.fetchone()

                metrics = {
                    'active_users': user_data.active_users or 0,
                    'new_users': new_users_data.new_users or 0,
                    'avg_session_duration': float(user_data.avg_session_duration or 0),
                    'total_sessions': user_data.total_sessions or 0
                }

                conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'dimensions': json.dumps({}),
                    'metrics': json.dumps(metrics)
                })
                conn.commit()

            result.records_generated += 1
            self.logger.debug(f"User metrics aggregated for {start_time} to {end_time}")

        except Exception as e:
            self.logger.error(f"Error aggregating user metrics: {e}")
            raise

    async def _aggregate_event_metrics(self, start_time: datetime, end_time: datetime, result: BatchResult):
        """Aggregate event metrics"""
        try:
            # Mock implementation - would typically query events table
            metrics = {
                'total_events': 10000,
                'unique_users': 1500,
                'top_events': {
                    'page_view': 6000,
                    'dialogue_interaction': 2000,
                    'combat_participation': 1000,
                    'social_interaction': 1000
                }
            }

            # Store in database
            query = text("""
                INSERT INTO batch_aggregates (
                    aggregate_type, time_period, period_start, period_end, dimensions, metrics
                ) VALUES (
                    'event_metrics', 'hourly', :start_time, :end_time,
                    :dimensions, :metrics
                )
                ON CONFLICT (aggregate_type, time_period, period_start, period_end) DO UPDATE SET
                    metrics = EXCLUDED.metrics
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'dimensions': json.dumps({}),
                    'metrics': json.dumps(metrics)
                })
                conn.commit()

            result.records_generated += 1

        except Exception as e:
            self.logger.error(f"Error aggregating event metrics: {e}")
            raise

    async def _aggregate_revenue_metrics(self, start_time: datetime, end_time: datetime, result: BatchResult):
        """Aggregate revenue metrics"""
        try:
            # Mock implementation
            metrics = {
                'total_revenue': 2500.00,
                'subscription_revenue': 2000.00,
                'one_time_revenue': 500.00,
                'paying_users': 85,
                'conversion_rate': 0.15
            }

            # Store in database
            query = text("""
                INSERT INTO batch_aggregates (
                    aggregate_type, time_period, period_start, period_end, dimensions, metrics
                ) VALUES (
                    'revenue_metrics', 'hourly', :start_time, :end_time,
                    :dimensions, :metrics
                )
                ON CONFLICT (aggregate_type, time_period, period_start, period_end) DO UPDATE SET
                    metrics = EXCLUDED.metrics
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'dimensions': json.dumps({}),
                    'metrics': json.dumps(metrics)
                })
                conn.commit()

            result.records_generated += 1

        except Exception as e:
            self.logger.error(f"Error aggregating revenue metrics: {e}")
            raise

    async def _aggregate_realtime_metrics(self, start_time: datetime, end_time: datetime, result: BatchResult):
        """Aggregate real-time metrics"""
        try:
            # Get real-time metrics from Redis
            current_metrics = await self._get_realtime_metrics_from_redis(start_time, end_time)

            # Store in database
            query = text("""
                INSERT INTO batch_aggregates (
                    aggregate_type, time_period, period_start, period_end, dimensions, metrics
                ) VALUES (
                    'realtime_metrics', 'hourly', :start_time, :end_time,
                    :dimensions, :metrics
                )
                ON CONFLICT (aggregate_type, time_period, period_start, period_end) DO UPDATE SET
                    metrics = EXCLUDED.metrics
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'dimensions': json.dumps({}),
                    'metrics': json.dumps(current_metrics)
                })
                conn.commit()

            result.records_generated += 1

        except Exception as e:
            self.logger.error(f"Error aggregating real-time metrics: {e}")
            raise

    async def _aggregate_performance_metrics(self, start_time: datetime, end_time: datetime, result: BatchResult):
        """Aggregate performance metrics"""
        try:
            # Mock implementation
            metrics = {
                'avg_response_time': 150,
                'error_rate': 0.01,
                'uptime': 0.9995,
                'throughput': 1200,
                'database_performance': {
                    'query_time': 25,
                    'connections': 45
                }
            }

            # Store in database
            query = text("""
                INSERT INTO batch_aggregates (
                    aggregate_type, time_period, period_start, period_end, dimensions, metrics
                ) VALUES (
                    'performance_metrics', 'hourly', :start_time, :end_time,
                    :dimensions, :metrics
                )
                ON CONFLICT (aggregate_type, time_period, period_start, period_end) DO UPDATE SET
                    metrics = EXCLUDED.metrics
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time,
                    'dimensions': json.dumps({}),
                    'metrics': json.dumps(metrics)
                })
                conn.commit()

            result.records_generated += 1

        except Exception as e:
            self.logger.error(f"Error aggregating performance metrics: {e}")
            raise

    # Reporting methods

    async def _generate_weekly_summary(self) -> Dict[str, Any]:
        """Generate weekly summary report"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)

            # Get aggregated data for the week
            query = text("""
                SELECT * FROM batch_aggregates
                WHERE aggregate_type = 'user_metrics'
                AND period_start >= :start_time AND period_end <= :end_time
                ORDER BY period_start ASC
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                rows = result.fetchall()

            # Process data into report format
            report_data = {
                'report_type': 'weekly_summary',
                'period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'summary': {
                    'total_active_users': 0,
                    'total_new_users': 0,
                    'avg_session_duration': 0,
                    'total_sessions': 0
                },
                'daily_breakdown': []
            }

            for row in rows:
                metrics = json.loads(row.metrics)
                report_data['summary']['total_active_users'] += metrics['active_users']
                report_data['summary']['total_new_users'] += metrics['new_users']
                report_data['summary']['total_sessions'] += metrics['total_sessions']

                report_data['daily_breakdown'].append({
                    'date': row.period_start.isoformat(),
                    'metrics': metrics
                })

            # Calculate averages
            if report_data['summary']['total_sessions'] > 0:
                report_data['summary']['avg_session_duration'] = (
                    sum(day['metrics']['avg_session_duration'] for day in report_data['daily_breakdown']) /
                    len(report_data['daily_breakdown'])
                )

            return report_data

        except Exception as e:
            self.logger.error(f"Error generating weekly summary: {e}")
            raise

    async def _generate_monthly_dashboard(self) -> Dict[str, Any]:
        """Generate monthly dashboard report"""
        # Mock implementation
        return {
            'report_type': 'monthly_dashboard',
            'period': {
                'start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'end': datetime.utcnow().isoformat()
            },
            'kpis': {
                'total_users': 15000,
                'active_users': 8500,
                'revenue': 25000,
                'conversion_rate': 0.12
            }
        }

    async def _generate_user_behavior_report(self) -> Dict[str, Any]:
        """Generate user behavior report"""
        # Mock implementation
        return {
            'report_type': 'user_behavior_report',
            'insights': {
                'top_features': ['dialogue_system', 'character_creation', 'social_features'],
                'avg_session_length': 1800,
                'retention_rate': 0.75
            }
        }

    async def _send_report(self, report_data: Dict[str, Any], recipients: List[str], format_type: str):
        """Send report to recipients"""
        try:
            # Mock email sending implementation
            self.logger.info(f"Sending {format_type} report to {len(recipients)} recipients")
            # In practice, would use email service, Slack integration, etc.
        except Exception as e:
            self.logger.error(f"Error sending report: {e}")
            raise

    # ML training methods

    async def _get_ml_training_data(self, model_type: str, features: List[str]) -> pd.DataFrame:
        """Get training data for ML models"""
        # Mock implementation
        return pd.DataFrame({
            'user_id': range(1000),
            'engagement_score': np.random.random(1000),
            'recency_days': np.random.randint(1, 90, 1000),
            'frequency': np.random.randint(1, 100, 1000),
            'monetary_value': np.random.uniform(0, 500, 1000)
        })

    async def _train_clustering_model(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train clustering model"""
        # Mock implementation
        return {
            'model_type': 'kmeans',
            'num_clusters': 5,
            'silhouette_score': 0.65,
            'training_samples': len(training_data)
        }

    async def _train_churn_model(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train churn prediction model"""
        # Mock implementation
        return {
            'model_type': 'random_forest',
            'accuracy': 0.82,
            'precision': 0.79,
            'recall': 0.76,
            'training_samples': len(training_data)
        }

    async def _train_recommendation_model(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train recommendation model"""
        # Mock implementation
        return {
            'model_type': 'collaborative_filtering',
            'rmse': 0.23,
            'coverage': 0.87,
            'training_samples': len(training_data)
        }

    # Cleanup methods

    async def _cleanup_old_events(self, cutoff_date: datetime) -> int:
        """Clean up old events"""
        # Mock implementation
        return 50000

    async def _cleanup_old_sessions(self, cutoff_date: datetime) -> int:
        """Clean up old sessions"""
        try:
            query = text("""
                DELETE FROM user_sessions
                WHERE start_time < :cutoff_date
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'cutoff_date': cutoff_date})
                conn.commit()

                return result.rowcount

        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0

    async def _archive_old_data(self, cutoff_date: datetime) -> int:
        """Archive old data"""
        # Mock implementation
        return 25000

    # Helper methods

    def _parse_time_window(self, time_window: str, end_time: datetime) -> datetime:
        """Parse time window string and calculate start time"""
        if time_window.endswith('h'):
            hours = int(time_window[:-1])
            return end_time - timedelta(hours=hours)
        elif time_window.endswith('d'):
            days = int(time_window[:-1])
            return end_time - timedelta(days=days)
        elif time_window.endswith('m'):
            minutes = int(time_window[:-1])
            return end_time - timedelta(minutes=minutes)
        else:
            raise ValueError(f"Invalid time window format: {time_window}")

    async def _get_realtime_metrics_from_redis(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get real-time metrics from Redis"""
        try:
            metrics = {
                'total_events': 0,
                'active_users': 0,
                'avg_response_time': 0
            }

            # Get metrics for each minute in the range
            current_time = start_time
            while current_time <= end_time:
                minute_key = current_time.strftime('%Y%m%d%H%M')
                metrics_key = f"analytics:metrics:{minute_key}"

                minute_metrics = await self.redis_client.hgetall(metrics_key)
                if minute_metrics:
                    metrics['total_events'] += int(minute_metrics.get(b'total_events', 0))

                current_time += timedelta(minutes=1)

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting real-time metrics from Redis: {e}")
            return {}

    async def _update_job_status(self, job: BatchJob):
        """Update job status in database"""
        try:
            query = text("""
                UPDATE batch_jobs
                SET status = :status,
                    last_run = :last_run,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': job.job_id,
                    'status': job.status,
                    'last_run': datetime.utcnow()
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")

    async def _store_job_result(self, result: BatchResult):
        """Store job execution result"""
        try:
            query = text("""
                INSERT INTO batch_results (
                    job_id, status, start_time, end_time,
                    records_processed, records_generated, errors, metrics
                ) VALUES (
                    :job_id, :status, :start_time, :end_time,
                    :records_processed, :records_generated, :errors, :metrics
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': result.job_id,
                    'status': result.status,
                    'start_time': result.start_time,
                    'end_time': result.end_time,
                    'records_processed': result.records_processed,
                    'records_generated': result.records_generated,
                    'errors': json.dumps(result.errors),
                    'metrics': json.dumps(result.metrics)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing job result: {e}")

    async def _update_job_after_execution(self, job: BatchJob, result: BatchResult):
        """Update job after execution"""
        try:
            # Calculate next run time (simplified - in practice would parse cron expression)
            if job.schedule.startswith('0 * * * *'):  # Hourly
                next_run = datetime.utcnow() + timedelta(hours=1)
            elif job.schedule.startswith('0 2 * * *'):  # Daily at 2 AM
                next_run = datetime.utcnow().replace(hour=2, minute=0, second=0) + timedelta(days=1)
            else:
                next_run = datetime.utcnow() + timedelta(hours=1)  # Default to hourly

            query = text("""
                UPDATE batch_jobs
                SET status = :status,
                    next_run = :next_run,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': job.job_id,
                    'status': 'pending',
                    'next_run': next_run
                })
                conn.commit()

            # Update in-memory job
            job.status = 'pending'
            job.next_run = next_run
            self.active_jobs[job.job_id] = job

        except Exception as e:
            self.logger.error(f"Error updating job after execution: {e}")

    async def _cleanup_completed_jobs(self):
        """Clean up completed job history"""
        try:
            # Keep only last 100 job results per job
            query = text("""
                DELETE FROM batch_results
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY job_id ORDER BY created_at DESC
                        ) as rn
                        FROM batch_results
                    ) t
                    WHERE rn <= 100
                )
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query)
                conn.commit()

                if result.rowcount > 0:
                    self.logger.debug(f"Cleaned up {result.rowcount} old job results")

        except Exception as e:
            self.logger.error(f"Error cleaning up completed jobs: {e}")

    async def start(self):
        """Start the batch processor"""
        self.logger.info("Starting Batch Processor...")
        self.is_running = True
        await self.process_batch()

    async def stop(self):
        """Stop the batch processor"""
        self.logger.info("Stopping Batch Processor...")
        self.is_running = False
        self.executor.shutdown(wait=True)
        self.logger.info("Batch Processor stopped")

    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get status of a specific job"""
        return self.active_jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, BatchJob]:
        """Get all jobs"""
        return self.active_jobs.copy()