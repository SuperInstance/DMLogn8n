"""
Health Data Storage

Storage backend for health monitoring data, metrics, and reports.
Supports file-based and database storage.
"""

import json
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from ..health_service import HealthCheckResult, SystemHealthReport, HealingAction

class HealthStorage:
    """Health monitoring data storage"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.storage_type = config.get('type', 'file')

        if self.storage_type == 'file':
            self._init_file_storage()
        elif self.storage_type == 'database':
            self._init_database_storage()

    def _init_file_storage(self):
        """Initialize file-based storage"""
        self.storage_path = self.config.get('file', {}).get('path', '/tmp/health_data')
        self.retention_days = self.config.get('file', {}).get('retention_days', 30)

        # Create storage directories
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, 'checks'), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, 'reports'), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, 'healing'), exist_ok=True)

    def _init_database_storage(self):
        """Initialize database storage"""
        self.db_path = self.config.get('database', {}).get('connection_string')
        if not self.db_path:
            raise ValueError("Database connection string required for database storage")

        # Initialize database tables
        self._create_database_tables()

    def _create_database_tables(self):
        """Create database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create check_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS check_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id TEXT NOT NULL,
                    check_name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    metrics TEXT,
                    timestamp TEXT NOT NULL,
                    duration_ms REAL,
                    dependencies TEXT,
                    healing_actions TEXT
                )
            ''')

            # Create health_reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    overall_status TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    check_results_count INTEGER,
                    dependency_issues_count INTEGER,
                    healing_actions_count INTEGER,
                    trends TEXT,
                    sla_compliance TEXT,
                    recommendations TEXT
                )
            ''')

            # Create healing_actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS healing_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_service TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    duration_seconds REAL
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_check_results_timestamp ON check_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_check_results_check_id ON check_results(check_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_reports_timestamp ON health_reports(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_healing_actions_timestamp ON healing_actions(timestamp)')

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise

    async def store_check_result(self, result: HealthCheckResult) -> bool:
        """Store individual health check result"""
        try:
            if self.storage_type == 'file':
                return self._store_check_result_file(result)
            elif self.storage_type == 'database':
                return self._store_check_result_db(result)
            else:
                self.logger.error(f"Unknown storage type: {self.storage_type}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to store check result: {e}")
            return False

    def _store_check_result_file(self, result: HealthCheckResult) -> bool:
        """Store check result to file"""
        try:
            # Create filename based on date and check ID
            date_str = result.timestamp.strftime('%Y-%m-%d')
            filename = f"{result.check_id}_{result.timestamp.strftime('%H%M%S')}.json"
            filepath = os.path.join(self.storage_path, 'checks', date_str, filename)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert result to dict and store
            result_dict = {
                'check_id': result.check_id,
                'check_name': result.check_name,
                'level': result.level.value,
                'status': result.status.value,
                'message': result.message,
                'details': result.details,
                'metrics': result.metrics,
                'timestamp': result.timestamp.isoformat(),
                'duration_ms': result.duration_ms,
                'dependencies': result.dependencies,
                'healing_actions': result.healing_actions
            }

            with open(filepath, 'w') as f:
                json.dump(result_dict, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to store check result to file: {e}")
            return False

    def _store_check_result_db(self, result: HealthCheckResult) -> bool:
        """Store check result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO check_results (
                    check_id, check_name, level, status, message, details, metrics,
                    timestamp, duration_ms, dependencies, healing_actions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.check_id,
                result.check_name,
                result.level.value,
                result.status.value,
                result.message,
                json.dumps(result.details),
                json.dumps(result.metrics),
                result.timestamp.isoformat(),
                result.duration_ms,
                json.dumps(result.dependencies),
                json.dumps(result.healing_actions)
            ))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Failed to store check result to database: {e}")
            return False

    async def store_health_report(self, report: SystemHealthReport) -> bool:
        """Store comprehensive health report"""
        try:
            if self.storage_type == 'file':
                return self._store_health_report_file(report)
            elif self.storage_type == 'database':
                return self._store_health_report_db(report)
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to store health report: {e}")
            return False

    def _store_health_report_file(self, report: SystemHealthReport) -> bool:
        """Store health report to file"""
        try:
            date_str = report.timestamp.strftime('%Y-%m-%d')
            filename = f"health_report_{report.timestamp.strftime('%H%M%S')}.json"
            filepath = os.path.join(self.storage_path, 'reports', date_str, filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            report_dict = {
                'overall_status': report.overall_status.value,
                'overall_score': report.overall_score,
                'timestamp': report.timestamp.isoformat(),
                'check_results_count': len(report.check_results),
                'dependency_issues_count': len(report.dependency_issues),
                'healing_actions_count': len(report.healing_actions_taken),
                'trends': report.trends,
                'sla_compliance': report.sla_compliance,
                'recommendations': report.recommendations
            }

            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to store health report to file: {e}")
            return False

    def _store_health_report_db(self, report: SystemHealthReport) -> bool:
        """Store health report to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO health_reports (
                    overall_status, overall_score, timestamp, check_results_count,
                    dependency_issues_count, healing_actions_count, trends,
                    sla_compliance, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.overall_status.value,
                report.overall_score,
                report.timestamp.isoformat(),
                len(report.check_results),
                len(report.dependency_issues),
                len(report.healing_actions_taken),
                json.dumps(report.trends),
                json.dumps(report.sla_compliance),
                json.dumps(report.recommendations)
            ))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Failed to store health report to database: {e}")
            return False

    async def store_healing_action(self, action: HealingAction) -> bool:
        """Store healing action record"""
        try:
            if self.storage_type == 'file':
                return self._store_healing_action_file(action)
            elif self.storage_type == 'database':
                return self._store_healing_action_db(action)
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to store healing action: {e}")
            return False

    def _store_healing_action_file(self, action: HealingAction) -> bool:
        """Store healing action to file"""
        try:
            date_str = action.timestamp.strftime('%Y-%m-%d')
            filename = f"healing_{action.target_service}_{action.timestamp.strftime('%H%M%S')}.json"
            filepath = os.path.join(self.storage_path, 'healing', date_str, filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            action_dict = {
                'action_id': action.action_id,
                'action_type': action.action_type,
                'target_service': action.target_service,
                'description': action.description,
                'timestamp': action.timestamp.isoformat(),
                'success': action.success,
                'details': action.details,
                'duration_seconds': action.duration_seconds
            }

            with open(filepath, 'w') as f:
                json.dump(action_dict, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Failed to store healing action to file: {e}")
            return False

    def _store_healing_action_db(self, action: HealingAction) -> bool:
        """Store healing action to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO healing_actions (
                    action_id, action_type, target_service, description,
                    timestamp, success, details, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                action.action_id,
                action.action_type,
                action.target_service,
                action.description,
                action.timestamp.isoformat(),
                action.success,
                json.dumps(action.details),
                action.duration_seconds
            ))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Failed to store healing action to database: {e}")
            return False

    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            if self.storage_type == 'file':
                return self._get_health_history_file(cutoff_time)
            elif self.storage_type == 'database':
                return self._get_health_history_db(cutoff_time)
            else:
                return []

        except Exception as e:
            self.logger.error(f"Failed to get health history: {e}")
            return []

    def _get_health_history_file(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get health history from files"""
        history = []

        try:
            # Iterate through date directories within the retention period
            current_date = cutoff_time.date()
            end_date = datetime.now().date()

            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                reports_dir = os.path.join(self.storage_path, 'reports', date_str)

                if os.path.exists(reports_dir):
                    for filename in os.listdir(reports_dir):
                        if filename.endswith('.json'):
                            filepath = os.path.join(reports_dir, filename)

                            try:
                                with open(filepath, 'r') as f:
                                    report_data = json.load(f)

                                report_time = datetime.fromisoformat(report_data['timestamp'])
                                if report_time >= cutoff_time:
                                    history.append(report_data)

                            except Exception as e:
                                self.logger.warning(f"Failed to read report file {filepath}: {e}")

                current_date += timedelta(days=1)

            # Sort by timestamp
            history.sort(key=lambda x: x['timestamp'])

        except Exception as e:
            self.logger.error(f"Failed to get health history from files: {e}")

        return history

    def _get_health_history_db(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get health history from database"""
        history = []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT overall_status, overall_score, timestamp,
                       check_results_count, dependency_issues_count,
                       healing_actions_count, trends, sla_compliance, recommendations
                FROM health_reports
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (cutoff_time.isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                history.append({
                    'status': row[0],
                    'score': row[1],
                    'timestamp': row[2],
                    'check_count': row[3],
                    'dependency_issues': row[4],
                    'healing_actions': row[5],
                    'trends': json.loads(row[6]) if row[6] else {},
                    'sla_compliance': json.loads(row[7]) if row[7] else {},
                    'recommendations': json.loads(row[8]) if row[8] else []
                })

        except Exception as e:
            self.logger.error(f"Failed to get health history from database: {e}")

        return history

    async def cleanup_old_data(self) -> bool:
        """Clean up old data based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            if self.storage_type == 'file':
                return self._cleanup_old_data_file(cutoff_date)
            elif self.storage_type == 'database':
                return self._cleanup_old_data_db(cutoff_date)
            else:
                return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False

    def _cleanup_old_data_file(self, cutoff_date: datetime) -> bool:
        """Clean up old files"""
        try:
            # Remove old directories
            for root, dirs, files in os.walk(self.storage_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)

                    # Try to parse directory name as date
                    try:
                        dir_date = datetime.strptime(dir_name, '%Y-%m-%d').date()
                        if dir_date < cutoff_date.date():
                            import shutil
                            shutil.rmtree(dir_path)
                            self.logger.info(f"Removed old data directory: {dir_path}")
                    except ValueError:
                        # Not a date directory, skip
                        continue

            return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup old file data: {e}")
            return False

    def _cleanup_old_data_db(self, cutoff_date: datetime) -> bool:
        """Clean up old database records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_timestamp = cutoff_date.isoformat()

            # Delete old check results
            cursor.execute('DELETE FROM check_results WHERE timestamp < ?', (cutoff_timestamp,))

            # Delete old health reports
            cursor.execute('DELETE FROM health_reports WHERE timestamp < ?', (cutoff_timestamp,))

            # Delete old healing actions
            cursor.execute('DELETE FROM healing_actions WHERE timestamp < ?', (cutoff_timestamp,))

            conn.commit()
            conn.close()

            self.logger.info(f"Cleaned up data older than {cutoff_timestamp}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup old database data: {e}")
            return False

    async def get_service_metrics(self, service_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics for specific service"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            if self.storage_type == 'database':
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT status, message, details, metrics, timestamp, duration_ms
                    FROM check_results
                    WHERE check_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (service_id, cutoff_time.isoformat()))

                rows = cursor.fetchall()
                conn.close()

                return [
                    {
                        'status': row[0],
                        'message': row[1],
                        'details': json.loads(row[2]) if row[2] else {},
                        'metrics': json.loads(row[3]) if row[3] else {},
                        'timestamp': row[4],
                        'duration_ms': row[5]
                    }
                    for row in rows
                ]

            else:
                # File-based implementation would be more complex
                return []

        except Exception as e:
            self.logger.error(f"Failed to get service metrics: {e}")
            return []