#!/usr/bin/env python3
"""
Data Export Module
Export analytics data in various formats (CSV, JSON, PDF, Excel)
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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis
from io import BytesIO, StringIO
import csv
import base64
from pathlib import Path

from ..analytics_engine import AnalyticsConfig


@dataclass
class ExportJob:
    """Export job configuration"""
    job_id: str
    name: str
    data_source: str
    query_params: Dict[str, Any]
    export_format: str  # 'csv', 'json', 'excel', 'pdf'
    filters: Dict[str, Any]
    columns: List[str] = None
    sort_by: str = None
    limit: int = None
    scheduled: bool = False
    recipients: List[str] = None
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed'


@dataclass
class ExportResult:
    """Export job result"""
    job_id: str
    status: str
    file_path: str
    file_size: int
    records_count: int
    download_url: str
    expires_at: datetime
    created_at: datetime
    error_message: str = None


class DataExporter:
    """Data export engine for analytics"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Export configuration
        self.export_dir = Path("/tmp/analytics_exports")
        self.export_dir.mkdir(exist_ok=True)
        self.download_base_url = "https://api.company.com/analytics/downloads"

        # Initialize database tables
        self._initialize_tables()

        # Active export jobs
        self.active_jobs = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup data exporter logging"""
        logger = logging.getLogger("data_exporter")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for export jobs"""
        try:
            # Create export_jobs table
            create_jobs_table = """
            CREATE TABLE IF NOT EXISTS export_jobs (
                job_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                data_source VARCHAR(100) NOT NULL,
                query_params TEXT,
                export_format VARCHAR(20) NOT NULL,
                filters TEXT,
                columns TEXT,
                sort_by VARCHAR(100),
                limit INTEGER,
                scheduled BOOLEAN DEFAULT FALSE,
                recipients TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create export_results table
            create_results_table = """
            CREATE TABLE IF NOT EXISTS export_results (
                job_id VARCHAR(100) PRIMARY KEY,
                status VARCHAR(20) NOT NULL,
                file_path TEXT,
                file_size BIGINT,
                records_count INTEGER,
                download_url TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                error_message TEXT,
                FOREIGN KEY (job_id) REFERENCES export_jobs(job_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);",
                "CREATE INDEX IF NOT EXISTS idx_export_jobs_data_source ON export_jobs(data_source);",
                "CREATE INDEX IF NOT EXISTS idx_export_results_created_at ON export_results(created_at);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_jobs_table))
                conn.execute(text(create_results_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Export tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing export tables: {e}")

    async def create_export_job(self, job: ExportJob) -> str:
        """Create a new export job"""
        try:
            # Store job in database
            query = text("""
                INSERT INTO export_jobs (
                    job_id, name, data_source, query_params, export_format,
                    filters, columns, sort_by, limit, scheduled, recipients, status
                ) VALUES (
                    :job_id, :name, :data_source, :query_params, :export_format,
                    :filters, :columns, :sort_by, :limit, :scheduled, :recipients, :status
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': job.job_id,
                    'name': job.name,
                    'data_source': job.data_source,
                    'query_params': json.dumps(job.query_params),
                    'export_format': job.export_format,
                    'filters': json.dumps(job.filters),
                    'columns': json.dumps(job.columns) if job.columns else None,
                    'sort_by': job.sort_by,
                    'limit': job.limit,
                    'scheduled': job.scheduled,
                    'recipients': json.dumps(job.recipients) if job.recipients else None,
                    'status': job.status
                })
                conn.commit()

            self.active_jobs[job.job_id] = job
            self.logger.info(f"Created export job: {job.name}")

            return job.job_id

        except Exception as e:
            self.logger.error(f"Error creating export job: {e}")
            raise

    async def execute_export(self, job_id: str) -> ExportResult:
        """Execute an export job"""
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                # Load from database
                job = await self._load_job_from_db(job_id)
                if not job:
                    raise ValueError(f"Export job not found: {job_id}")

            self.logger.info(f"Executing export job: {job.name}")

            # Update job status
            job.status = 'running'
            await self._update_job_status(job_id, 'running')

            # Get data based on data source
            data = await self._get_export_data(job)

            if data.empty:
                raise ValueError("No data found for export")

            # Apply filters and sorting
            filtered_data = await self._apply_filters_and_sorting(data, job)

            # Generate export file
            file_path, file_size = await self._generate_export_file(filtered_data, job)

            # Create download URL
            download_url = f"{self.download_base_url}/{Path(file_path).name}"

            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days

            # Create result
            result = ExportResult(
                job_id=job_id,
                status='completed',
                file_path=file_path,
                file_size=file_size,
                records_count=len(filtered_data),
                download_url=download_url,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )

            # Store result
            await self._store_export_result(result)

            # Update job status
            job.status = 'completed'
            await self._update_job_status(job_id, 'completed')

            # Send notifications if recipients specified
            if job.recipients:
                await self._send_export_notification(job, result)

            self.logger.info(f"Export completed: {job.name} ({len(filtered_data)} records)")
            return result

        except Exception as e:
            self.logger.error(f"Error executing export job {job_id}: {e}")

            # Create error result
            result = ExportResult(
                job_id=job_id,
                status='failed',
                file_path="",
                file_size=0,
                records_count=0,
                download_url="",
                expires_at=datetime.utcnow() + timedelta(days=1),
                created_at=datetime.utcnow(),
                error_message=str(e)
            )

            # Store error result
            await self._store_export_result(result)

            # Update job status
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = 'failed'
            await self._update_job_status(job_id, 'failed')

            return result

    async def _get_export_data(self, job: ExportJob) -> pd.DataFrame:
        """Get data for export based on data source"""
        try:
            if job.data_source == "users":
                return await self._get_users_data(job.query_params, job.filters)
            elif job.data_source == "sessions":
                return await self._get_sessions_data(job.query_params, job.filters)
            elif job.data_source == "events":
                return await self._get_events_data(job.query_params, job.filters)
            elif job.data_source == "revenue":
                return await self._get_revenue_data(job.query_params, job.filters)
            elif job.data_source == "engagement":
                return await self._get_engagement_data(job.query_params, job.filters)
            elif job.data_source == "churn_predictions":
                return await self._get_churn_predictions_data(job.query_params, job.filters)
            elif job.data_source == "user_segments":
                return await self._get_user_segments_data(job.query_params, job.filters)
            else:
                raise ValueError(f"Unknown data source: {job.data_source}")

        except Exception as e:
            self.logger.error(f"Error getting export data: {e}")
            return pd.DataFrame()

    async def _get_users_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get users data for export"""
        try:
            # Mock user data
            np.random.seed(42)
            n_users = 1000

            data = {
                'user_id': [f"user_{i:06d}" for i in range(n_users)],
                'created_at': [datetime.utcnow() - timedelta(days=np.random.randint(1, 365)) for _ in range(n_users)],
                'last_active': [datetime.utcnow() - timedelta(hours=np.random.randint(1, 168)) for _ in range(n_users)],
                'total_sessions': np.random.randint(1, 100, n_users),
                'total_revenue': np.random.uniform(0, 500, n_users),
                'engagement_score': np.random.uniform(0, 1, n_users),
                'device_type': np.random.choice(['mobile', 'desktop', 'tablet'], n_users),
                'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE'], n_users),
                'acquisition_source': np.random.choice(['organic', 'social', 'paid', 'referral'], n_users),
                'subscription_status': np.random.choice(['free', 'premium', 'enterprise'], n_users, p=[0.7, 0.25, 0.05])
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting users data: {e}")
            return pd.DataFrame()

    async def _get_sessions_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get sessions data for export"""
        try:
            # Mock session data
            np.random.seed(42)
            n_sessions = 5000

            data = {
                'session_id': [f"session_{i:06d}" for i in range(n_sessions)],
                'user_id': [f"user_{np.random.randint(1, 1000):06d}" for _ in range(n_sessions)],
                'start_time': [datetime.utcnow() - timedelta(hours=np.random.randint(1, 168)) for _ in range(n_sessions)],
                'duration': np.random.randint(60, 3600, n_sessions),
                'page_views': np.random.randint(1, 50, n_sessions),
                'device_type': np.random.choice(['mobile', 'desktop', 'tablet'], n_sessions),
                'browser': np.random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'], n_sessions),
                'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE'], n_sessions),
                'exit_page': np.random.choice(['/home', '/dashboard', '/profile', '/settings'], n_sessions)
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting sessions data: {e}")
            return pd.DataFrame()

    async def _get_events_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get events data for export"""
        try:
            # Mock events data
            np.random.seed(42)
            n_events = 10000

            event_types = ['page_view', 'user_signup', 'feature_used', 'purchase_completed', 'social_interaction']

            data = {
                'event_id': [f"event_{i:06d}" for i in range(n_events)],
                'user_id': [f"user_{np.random.randint(1, 1000):06d}" for _ in range(n_events)],
                'session_id': [f"session_{np.random.randint(1, 5000):06d}" for _ in range(n_events)],
                'event_type': np.random.choice(event_types, n_events),
                'timestamp': [datetime.utcnow() - timedelta(hours=np.random.randint(1, 168)) for _ in range(n_events)],
                'properties': [json.dumps({"feature": f"feature_{np.random.randint(1, 10)}"}) for _ in range(n_events)],
                'device_type': np.random.choice(['mobile', 'desktop', 'tablet'], n_events),
                'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE'], n_events)
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting events data: {e}")
            return pd.DataFrame()

    async def _get_revenue_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get revenue data for export"""
        try:
            # Mock revenue data
            np.random.seed(42)
            n_transactions = 2000

            data = {
                'transaction_id': [f"txn_{i:06d}" for i in range(n_transactions)],
                'user_id': [f"user_{np.random.randint(1, 1000):06d}" for _ in range(n_transactions)],
                'amount': np.random.uniform(5, 200, n_transactions),
                'currency': np.random.choice(['USD', 'EUR', 'GBP'], n_transactions),
                'transaction_type': np.random.choice(['subscription', 'one_time', 'in_app_purchase'], n_transactions),
                'status': np.random.choice(['completed', 'pending', 'failed'], n_transactions, p=[0.9, 0.05, 0.05]),
                'created_at': [datetime.utcnow() - timedelta(days=np.random.randint(1, 90)) for _ in range(n_transactions)],
                'payment_method': np.random.choice(['credit_card', 'paypal', 'bank_transfer'], n_transactions)
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting revenue data: {e}")
            return pd.DataFrame()

    async def _get_engagement_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get engagement data for export"""
        try:
            # Mock engagement data
            np.random.seed(42)
            n_records = 3000

            data = {
                'user_id': [f"user_{i:06d}" for i in range(n_records)],
                'date': [datetime.utcnow().date() - timedelta(days=np.random.randint(1, 30)) for _ in range(n_records)],
                'sessions_count': np.random.randint(1, 10, n_records),
                'total_duration': np.random.randint(300, 7200, n_records),
                'pages_viewed': np.random.randint(5, 100, n_records),
                'features_used': np.random.randint(1, 15, n_records),
                'social_interactions': np.random.randint(0, 50, n_records),
                'engagement_score': np.random.uniform(0, 1, n_records),
                'retention_day': np.random.randint(1, 31, n_records)
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting engagement data: {e}")
            return pd.DataFrame()

    async def _get_churn_predictions_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get churn predictions data for export"""
        try:
            # Mock churn predictions data
            np.random.seed(42)
            n_predictions = 1500

            data = {
                'user_id': [f"user_{i:06d}" for i in range(n_predictions)],
                'churn_probability': np.random.uniform(0, 1, n_predictions),
                'churn_risk_level': np.random.choice(['low', 'medium', 'high', 'critical'], n_predictions),
                'confidence_score': np.random.uniform(0.5, 1.0, n_predictions),
                'predicted_churn_date': [datetime.utcnow() + timedelta(days=np.random.randint(1, 90)) for _ in range(n_predictions)],
                'key_factors': [json.dumps({"factor": f"factor_{np.random.randint(1, 10)}", "importance": np.random.uniform(0.1, 1.0)}) for _ in range(n_predictions)],
                'model_id': np.random.choice(['short_term_churn', 'medium_term_churn', 'long_term_churn'], n_predictions),
                'created_at': datetime.utcnow()
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting churn predictions data: {e}")
            return pd.DataFrame()

    async def _get_user_segments_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> pd.DataFrame:
        """Get user segments data for export"""
        try:
            # Mock user segments data
            np.random.seed(42)
            n_users = 1000

            data = {
                'user_id': [f"user_{i:06d}" for i in range(n_users)],
                'segment_id': np.random.randint(1, 6, n_users),
                'segment_name': np.random.choice(['Highly Engaged', 'Moderately Engaged', 'Low Engagement', 'New Users', 'Power Users', 'At Risk'], n_users),
                'cluster_id': np.random.randint(1, 5, n_users),
                'confidence_score': np.random.uniform(0.6, 1.0, n_users),
                'assigned_at': [datetime.utcnow() - timedelta(days=np.random.randint(1, 30)) for _ in range(n_users)],
                'model_id': np.random.choice(['engagement_based', 'value_based', 'behavioral'], n_users),
                'segment_characteristics': [json.dumps({"engagement": np.random.uniform(0, 1), "value": np.random.uniform(0, 1000)}) for _ in range(n_users)]
            }

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting user segments data: {e}")
            return pd.DataFrame()

    async def _apply_filters_and_sorting(self, data: pd.DataFrame, job: ExportJob) -> pd.DataFrame:
        """Apply filters and sorting to data"""
        try:
            filtered_data = data.copy()

            # Apply column selection
            if job.columns:
                available_columns = [col for col in job.columns if col in filtered_data.columns]
                if available_columns:
                    filtered_data = filtered_data[available_columns]

            # Apply filters
            for filter_key, filter_value in job.filters.items():
                if filter_key in filtered_data.columns:
                    if isinstance(filter_value, list):
                        filtered_data = filtered_data[filtered_data[filter_key].isin(filter_value)]
                    elif isinstance(filter_value, dict):
                        # Range filter
                        if 'min' in filter_value:
                            filtered_data = filtered_data[filtered_data[filter_key] >= filter_value['min']]
                        if 'max' in filter_value:
                            filtered_data = filtered_data[filtered_data[filter_key] <= filter_value['max']]
                    else:
                        filtered_data = filtered_data[filtered_data[filter_key] == filter_value]

            # Apply sorting
            if job.sort_by and job.sort_by in filtered_data.columns:
                filtered_data = filtered_data.sort_values(by=job.sort_by)

            # Apply limit
            if job.limit and len(filtered_data) > job.limit:
                filtered_data = filtered_data.head(job.limit)

            return filtered_data

        except Exception as e:
            self.logger.error(f"Error applying filters and sorting: {e}")
            return data

    async def _generate_export_file(self, data: pd.DataFrame, job: ExportJob) -> Tuple[str, int]:
        """Generate export file based on format"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{job.name}_{timestamp}.{job.export_format}"
            file_path = self.export_dir / filename

            if job.export_format == 'csv':
                file_path = await self._generate_csv_export(data, file_path)
            elif job.export_format == 'json':
                file_path = await self._generate_json_export(data, file_path)
            elif job.export_format == 'excel':
                file_path = await self._generate_excel_export(data, file_path)
            elif job.export_format == 'pdf':
                file_path = await self._generate_pdf_export(data, file_path)
            else:
                raise ValueError(f"Unsupported export format: {job.export_format}")

            # Get file size
            file_size = file_path.stat().st_size

            return str(file_path), file_size

        except Exception as e:
            self.logger.error(f"Error generating export file: {e}")
            raise

    async def _generate_csv_export(self, data: pd.DataFrame, file_path: Path) -> Path:
        """Generate CSV export file"""
        try:
            # Convert datetime columns to string format
            data_copy = data.copy()
            for col in data_copy.columns:
                if data_copy[col].dtype == 'datetime64[ns]':
                    data_copy[col] = data_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')

            data_copy.to_csv(file_path, index=False)
            return file_path

        except Exception as e:
            self.logger.error(f"Error generating CSV export: {e}")
            raise

    async def _generate_json_export(self, data: pd.DataFrame, file_path: Path) -> Path:
        """Generate JSON export file"""
        try:
            # Convert DataFrame to JSON
            data_dict = data.to_dict('records')

            # Handle datetime serialization
            for record in data_dict:
                for key, value in record.items():
                    if isinstance(value, pd.Timestamp):
                        record[key] = value.isoformat()

            with open(file_path, 'w') as f:
                json.dump(data_dict, f, indent=2, default=str)

            return file_path

        except Exception as e:
            self.logger.error(f"Error generating JSON export: {e}")
            raise

    async def _generate_excel_export(self, data: pd.DataFrame, file_path: Path) -> Path:
        """Generate Excel export file"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name='Data', index=False)

                # Add summary sheet
                summary_data = {
                    'Metric': ['Total Records', 'Columns', 'Export Date'],
                    'Value': [len(data), len(data.columns), datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

            return file_path

        except Exception as e:
            self.logger.error(f"Error generating Excel export: {e}")
            raise

    async def _generate_pdf_export(self, data: pd.DataFrame, file_path: Path) -> Path:
        """Generate PDF export file (simplified)"""
        try:
            # Mock PDF generation - in practice would use reportlab or similar
            with open(file_path, 'w') as f:
                f.write(f"PDF Export Report\n")
                f.write(f"Generated: {datetime.utcnow()}\n")
                f.write(f"Total Records: {len(data)}\n")
                f.write(f"Columns: {', '.join(data.columns)}\n\n")
                f.write("Data Preview:\n")
                f.write(data.head().to_string())

            # Rename with .txt extension since we're not actually generating PDF
            txt_path = file_path.with_suffix('.txt')
            file_path.unlink()
            file_path = txt_path

            return file_path

        except Exception as e:
            self.logger.error(f"Error generating PDF export: {e}")
            raise

    async def _store_export_result(self, result: ExportResult):
        """Store export result in database"""
        try:
            query = text("""
                INSERT INTO export_results (
                    job_id, status, file_path, file_size, records_count,
                    download_url, expires_at, created_at, error_message
                ) VALUES (
                    :job_id, :status, :file_path, :file_size, :records_count,
                    :download_url, :expires_at, :created_at, :error_message
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'job_id': result.job_id,
                    'status': result.status,
                    'file_path': result.file_path,
                    'file_size': result.file_size,
                    'records_count': result.records_count,
                    'download_url': result.download_url,
                    'expires_at': result.expires_at,
                    'created_at': result.created_at,
                    'error_message': result.error_message
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing export result: {e}")

    async def _update_job_status(self, job_id: str, status: str):
        """Update job status in database"""
        try:
            query = text("""
                UPDATE export_jobs
                SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = :job_id
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {'job_id': job_id, 'status': status})
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")

    async def _load_job_from_db(self, job_id: str) -> Optional[ExportJob]:
        """Load export job from database"""
        try:
            query = text("""
                SELECT * FROM export_jobs WHERE job_id = :job_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'job_id': job_id})
                row = result.fetchone()

                if row:
                    return ExportJob(
                        job_id=row.job_id,
                        name=row.name,
                        data_source=row.data_source,
                        query_params=json.loads(row.query_params),
                        export_format=row.export_format,
                        filters=json.loads(row.filters),
                        columns=json.loads(row.columns) if row.columns else None,
                        sort_by=row.sort_by,
                        limit=row.limit,
                        scheduled=row.scheduled,
                        recipients=json.loads(row.recipients) if row.recipients else None,
                        status=row.status
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error loading job from database: {e}")
            return None

    async def _send_export_notification(self, job: ExportJob, result: ExportResult):
        """Send export completion notification"""
        try:
            # Mock notification sending
            self.logger.info(f"Sending export notification for job {job.name} to recipients: {job.recipients}")
            # In practice, would send email/Slack notification
        except Exception as e:
            self.logger.error(f"Error sending export notification: {e}")

    async def get_export_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an export job"""
        try:
            query = text("""
                SELECT j.*, r.file_path, r.file_size, r.records_count,
                       r.download_url, r.expires_at, r.error_message
                FROM export_jobs j
                LEFT JOIN export_results r ON j.job_id = r.job_id
                WHERE j.job_id = :job_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'job_id': job_id})
                row = result.fetchone()

                if row:
                    return {
                        'job_id': row.job_id,
                        'name': row.name,
                        'status': row.status,
                        'data_source': row.data_source,
                        'export_format': row.export_format,
                        'file_path': row.file_path,
                        'file_size': row.file_size,
                        'records_count': row.records_count,
                        'download_url': row.download_url,
                        'expires_at': row.expires_at.isoformat() if row.expires_at else None,
                        'error_message': row.error_message,
                        'created_at': row.created_at.isoformat()
                    }
                return None

        except Exception as e:
            self.logger.error(f"Error getting export status: {e}")
            return None

    async def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of export jobs"""
        try:
            query = text("""
                SELECT j.*, r.file_size, r.records_count, r.status as result_status
                FROM export_jobs j
                LEFT JOIN export_results r ON j.job_id = r.job_id
                ORDER BY j.created_at DESC
                LIMIT :limit
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'limit': limit})
                rows = result.fetchall()

            exports = []
            for row in rows:
                exports.append({
                    'job_id': row.job_id,
                    'name': row.name,
                    'data_source': row.data_source,
                    'export_format': row.export_format,
                    'status': row.result_status or row.status,
                    'records_count': row.records_count,
                    'file_size': row.file_size,
                    'created_at': row.created_at.isoformat()
                })

            return exports

        except Exception as e:
            self.logger.error(f"Error getting export history: {e}")
            return []

    async def cleanup_expired_exports(self):
        """Clean up expired export files"""
        try:
            cutoff_time = datetime.utcnow()

            query = text("""
                SELECT job_id, file_path FROM export_results
                WHERE expires_at <= :cutoff_time
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'cutoff_time': cutoff_time})
                expired_files = result.fetchall()

                deleted_count = 0
                for row in expired_files:
                    try:
                        file_path = Path(row.file_path)
                        if file_path.exists():
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Error deleting file {row.file_path}: {e}")

                # Remove expired records from database
                delete_query = text("""
                    DELETE FROM export_results
                    WHERE expires_at <= :cutoff_time
                """)
                conn.execute(delete_query, {'cutoff_time': cutoff_time})
                conn.commit()

            self.logger.info(f"Cleaned up {deleted_count} expired export files")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired exports: {e}")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return ['csv', 'json', 'excel', 'pdf']

    def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get list of available data sources for export"""
        return [
            {'id': 'users', 'name': 'Users', 'description': 'User accounts and profiles'},
            {'id': 'sessions', 'name': 'Sessions', 'description': 'User session data'},
            {'id': 'events', 'name': 'Events', 'description': 'Analytics events and interactions'},
            {'id': 'revenue', 'name': 'Revenue', 'description': 'Financial transactions and revenue'},
            {'id': 'engagement', 'name': 'Engagement', 'description': 'User engagement metrics'},
            {'id': 'churn_predictions', 'name': 'Churn Predictions', 'description': 'Churn risk predictions'},
            {'id': 'user_segments', 'name': 'User Segments', 'description': 'User segmentation data'}
        ]