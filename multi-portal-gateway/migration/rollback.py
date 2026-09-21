#!/usr/bin/env python3
"""
Migration Rollback and Recovery System
Provides automated rollback capabilities and point-in-time recovery
"""

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import sqlite3

from migration_engine import MigrationProgress, MigrationStatus, MigrationConfig

logger = logging.getLogger("migration_rollback")

class RollbackType(Enum):
    """Types of rollback operations"""
    FULL = "full"
    PARTIAL = "partial"
    POINT_IN_TIME = "point_in_time"
    TABLE_LEVEL = "table_level"
    TRANSACTIONS = "transactions"

class RollbackStatus(Enum):
    """Rollback operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class RollbackPoint:
    """Rollback checkpoint information"""
    id: str
    migration_id: str
    timestamp: datetime
    description: str
    backup_path: str
    tables: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    size_bytes: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class RollbackPlan:
    """Rollback execution plan"""
    rollback_id: str
    migration_id: str
    rollback_type: RollbackType
    rollback_points: List[RollbackPoint]
    target_tables: List[str]
    estimated_duration_minutes: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    prerequisites: List[str] = field(default_factory=list)
    validation_steps: List[str] = field(default_factory=list)
    approval_required: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

@dataclass
class RollbackResult:
    """Rollback execution result"""
    rollback_id: str
    status: RollbackStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    tables_rolled_back: List[str] = field(default_factory=list)
    tables_failed: List[str] = field(default_factory=list)
    records_affected: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_results: Dict[str, bool] = field(default_factory=dict)

class RollbackManager:
    """Manages migration rollback operations"""

    def __init__(self, backup_directory: str = "/tmp/migration_backups"):
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)

        # Initialize rollback database
        self.db_path = self.backup_directory / "rollback_registry.db"
        self._init_rollback_db()

        self.active_rollbacks: Dict[str, RollbackResult] = {}
        self.rollback_strategies = self._initialize_strategies()

    def _init_rollback_db(self):
        """Initialize rollback registry database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create rollback points table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rollback_points (
                id TEXT PRIMARY KEY,
                migration_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT,
                backup_path TEXT NOT NULL,
                tables TEXT NOT NULL,
                metadata TEXT,
                checksum TEXT,
                size_bytes INTEGER,
                created_at TEXT NOT NULL
            )
        ''')

        # Create rollback plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rollback_plans (
                rollback_id TEXT PRIMARY KEY,
                migration_id TEXT NOT NULL,
                rollback_type TEXT NOT NULL,
                rollback_points TEXT NOT NULL,
                target_tables TEXT NOT NULL,
                estimated_duration REAL,
                risk_level TEXT,
                prerequisites TEXT,
                validation_steps TEXT,
                approval_required BOOLEAN DEFAULT FALSE,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                executed_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        # Create rollback results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rollback_results (
                rollback_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                tables_rolled_back TEXT,
                tables_failed TEXT,
                records_affected TEXT,
                errors TEXT,
                warnings TEXT,
                validation_results TEXT,
                FOREIGN KEY (rollback_id) REFERENCES rollback_plans (rollback_id)
            )
        ''')

        conn.commit()
        conn.close()

    def _initialize_strategies(self) -> Dict[RollbackType, callable]:
        """Initialize rollback strategies"""
        return {
            RollbackType.FULL: self._execute_full_rollback,
            RollbackType.PARTIAL: self._execute_partial_rollback,
            RollbackType.POINT_IN_TIME: self._execute_point_in_time_rollback,
            RollbackType.TABLE_LEVEL: self._execute_table_level_rollback,
            RollbackType.TRANSACTIONS: self._execute_transaction_rollback,
        }

    async def create_rollback_point(self, migration_id: str, tables: List[str],
                                  description: str = "", metadata: Dict[str, Any] = None) -> RollbackPoint:
        """Create a rollback checkpoint"""
        logger.info(f"Creating rollback point for migration {migration_id}")

        rollback_id = f"rb_{migration_id}_{int(datetime.now().timestamp())}"
        backup_path = self.backup_directory / rollback_id
        backup_path.mkdir(exist_ok=True)

        try:
            # Create backups for each table
            backup_files = {}
            total_size = 0

            for table in tables:
                backup_file = await self._backup_table(table, backup_path)
                backup_files[table] = backup_file
                total_size += backup_file.stat().st_size if backup_file.exists() else 0

            # Create backup manifest
            manifest = {
                "rollback_id": rollback_id,
                "migration_id": migration_id,
                "tables": backup_files,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "description": description,
                "metadata": metadata or {}
            }

            manifest_path = backup_path / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)

            # Calculate checksum
            checksum = await self._calculate_backup_checksum(backup_path)

            # Create rollback point object
            rollback_point = RollbackPoint(
                id=rollback_id,
                migration_id=migration_id,
                timestamp=datetime.now(timezone.utc),
                description=description or f"Rollback point for {migration_id}",
                backup_path=str(backup_path),
                tables=tables,
                metadata=metadata or {},
                checksum=checksum,
                size_bytes=total_size
            )

            # Save to database
            await self._save_rollback_point(rollback_point)

            logger.info(f"Rollback point created: {rollback_id}")
            return rollback_point

        except Exception as e:
            logger.error(f"Failed to create rollback point: {e}")
            # Cleanup on failure
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise

    async def _backup_table(self, table_name: str, backup_path: Path) -> Path:
        """Backup a single table"""
        backup_file = backup_path / f"{table_name}.csv"

        # This would be implemented with actual database connections
        # For now, create a placeholder file
        backup_file.write_text(f"# Backup of table {table_name}\n")

        logger.debug(f"Backed up table {table_name} to {backup_file}")
        return backup_file

    async def _calculate_backup_checksum(self, backup_path: Path) -> str:
        """Calculate checksum for backup directory"""
        checksum = hashlib.sha256()

        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        checksum.update(chunk)

        return checksum.hexdigest()

    async def _save_rollback_point(self, rollback_point: RollbackPoint):
        """Save rollback point to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO rollback_points (
                id, migration_id, timestamp, description, backup_path,
                tables, metadata, checksum, size_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rollback_point.id,
            rollback_point.migration_id,
            rollback_point.timestamp.isoformat(),
            rollback_point.description,
            rollback_point.backup_path,
            json.dumps(rollback_point.tables),
            json.dumps(rollback_point.metadata),
            rollback_point.checksum,
            rollback_point.size_bytes,
            rollback_point.created_at.isoformat()
        ))

        conn.commit()
        conn.close()

    async def create_rollback_plan(self, migration_id: str, rollback_type: RollbackType,
                                 target_tables: List[str] = None,
                                 rollback_point_id: str = None) -> RollbackPlan:
        """Create a rollback plan"""
        logger.info(f"Creating rollback plan for migration {migration_id}")

        rollback_id = f"plan_{migration_id}_{int(datetime.now().timestamp())}"

        # Get available rollback points
        rollback_points = await self._get_rollback_points(migration_id)

        if not rollback_points:
            raise ValueError(f"No rollback points found for migration {migration_id}")

        # Select rollback point
        selected_point = None
        if rollback_point_id:
            selected_point = next((rp for rp in rollback_points if rp.id == rollback_point_id), None)
            if not selected_point:
                raise ValueError(f"Rollback point {rollback_point_id} not found")
        else:
            # Use the most recent rollback point
            selected_point = max(rollback_points, key=lambda rp: rp.timestamp)

        # Determine target tables
        if not target_tables:
            target_tables = selected_point.tables

        # Estimate duration and risk
        estimated_duration = len(target_tables) * 2.0  # 2 minutes per table
        risk_level = self._assess_rollback_risk(rollback_type, target_tables, selected_point)

        # Create rollback plan
        plan = RollbackPlan(
            rollback_id=rollback_id,
            migration_id=migration_id,
            rollback_type=rollback_type,
            rollback_points=[selected_point],
            target_tables=target_tables,
            estimated_duration_minutes=estimated_duration,
            risk_level=risk_level,
            prerequisites=self._determine_prerequisites(rollback_type, target_tables),
            validation_steps=self._determine_validation_steps(target_tables),
            approval_required=risk_level in ['HIGH', 'CRITICAL']
        )

        # Save plan to database
        await self._save_rollback_plan(plan)

        logger.info(f"Rollback plan created: {rollback_id}")
        return plan

    async def _get_rollback_points(self, migration_id: str) -> List[RollbackPoint]:
        """Get rollback points for a migration"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, migration_id, timestamp, description, backup_path,
                   tables, metadata, checksum, size_bytes, created_at
            FROM rollback_points
            WHERE migration_id = ?
            ORDER BY timestamp DESC
        ''', (migration_id,))

        rows = cursor.fetchall()
        conn.close()

        rollback_points = []
        for row in rows:
            rollback_point = RollbackPoint(
                id=row[0],
                migration_id=row[1],
                timestamp=datetime.fromisoformat(row[2]),
                description=row[3],
                backup_path=row[4],
                tables=json.loads(row[5]),
                metadata=json.loads(row[6]),
                checksum=row[7],
                size_bytes=row[8],
                created_at=datetime.fromisoformat(row[9])
            )
            rollback_points.append(rollback_point)

        return rollback_points

    def _assess_rollback_risk(self, rollback_type: RollbackType,
                            target_tables: List[str], rollback_point: RollbackPoint) -> str:
        """Assess rollback risk level"""
        risk_score = 0

        # Base risk by type
        type_risk = {
            RollbackType.FULL: 3,
            RollbackType.PARTIAL: 2,
            RollbackType.POINT_IN_TIME: 4,
            RollbackType.TABLE_LEVEL: 1,
            RollbackType.TRANSACTIONS: 2
        }
        risk_score += type_risk.get(rollback_type, 2)

        # Table count risk
        if len(target_tables) > 10:
            risk_score += 2
        elif len(target_tables) > 5:
            risk_score += 1

        # Age of rollback point
        age_hours = (datetime.now(timezone.utc) - rollback_point.timestamp).total_seconds() / 3600
        if age_hours > 24:
            risk_score += 2
        elif age_hours > 12:
            risk_score += 1

        # Convert score to risk level
        if risk_score <= 2:
            return "LOW"
        elif risk_score <= 4:
            return "MEDIUM"
        elif risk_score <= 6:
            return "HIGH"
        else:
            return "CRITICAL"

    def _determine_prerequisites(self, rollback_type: RollbackType,
                                target_tables: List[str]) -> List[str]:
        """Determine rollback prerequisites"""
        prerequisites = []

        prerequisites.append("Database connectivity verified")
        prerequisites.append("Backup integrity validated")

        if rollback_type in [RollbackType.FULL, RollbackType.PARTIAL]:
            prerequisites.append("Sufficient disk space for rollback")
            prerequisites.append("Database maintenance window scheduled")

        if len(target_tables) > 5:
            prerequisites.append("Performance impact assessment completed")

        return prerequisites

    def _determine_validation_steps(self, target_tables: List[str]) -> List[str]:
        """Determine validation steps"""
        steps = []

        for table in target_tables:
            steps.append(f"Validate {table} row count")
            steps.append(f"Verify {table} data integrity")
            steps.append(f"Check {table} foreign key constraints")

        steps.append("Validate overall database consistency")
        steps.append("Verify application functionality")

        return steps

    async def _save_rollback_plan(self, plan: RollbackPlan):
        """Save rollback plan to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO rollback_plans (
                rollback_id, migration_id, rollback_type, rollback_points,
                target_tables, estimated_duration, risk_level, prerequisites,
                validation_steps, approval_required, approved_by, approved_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plan.rollback_id,
            plan.migration_id,
            plan.rollback_type.value,
            json.dumps([rp.id for rp in plan.rollback_points]),
            json.dumps(plan.target_tables),
            plan.estimated_duration_minutes,
            plan.risk_level,
            json.dumps(plan.prerequisites),
            json.dumps(plan.validation_steps),
            plan.approval_required,
            plan.approved_by,
            plan.approved_at.isoformat() if plan.approved_at else None,
            datetime.now(timezone.utc).isoformat()
        ))

        conn.commit()
        conn.close()

    async def execute_rollback(self, rollback_id: str, force: bool = False) -> RollbackResult:
        """Execute a rollback plan"""
        logger.info(f"Executing rollback: {rollback_id}")

        # Get rollback plan
        plan = await self._get_rollback_plan(rollback_id)
        if not plan:
            raise ValueError(f"Rollback plan {rollback_id} not found")

        # Check approval if required
        if plan.approval_required and not force:
            raise ValueError(f"Rollback {rollback_id} requires approval")

        # Initialize result
        result = RollbackResult(
            rollback_id=rollback_id,
            status=RollbackStatus.IN_PROGRESS,
            start_time=datetime.now(timezone.utc)
        )

        self.active_rollbacks[rollback_id] = result

        try:
            # Update plan status
            await self._update_plan_status(rollback_id, "executed")

            # Execute rollback strategy
            strategy_func = self.rollback_strategies.get(plan.rollback_type)
            if not strategy_func:
                raise ValueError(f"Unknown rollback type: {plan.rollback_type}")

            await strategy_func(plan, result)

            # Mark as completed
            result.status = RollbackStatus.COMPLETED
            result.end_time = datetime.now(timezone.utc)

            logger.info(f"Rollback {rollback_id} completed successfully")

        except Exception as e:
            logger.error(f"Rollback {rollback_id} failed: {e}")
            result.status = RollbackStatus.FAILED
            result.end_time = datetime.now(timezone.utc)
            result.errors.append(str(e))

        finally:
            # Save result
            await self._save_rollback_result(result)
            await self._update_plan_status(rollback_id, "completed")

            # Remove from active rollbacks
            if rollback_id in self.active_rollbacks:
                del self.active_rollbacks[rollback_id]

        return result

    async def _get_rollback_plan(self, rollback_id: str) -> Optional[RollbackPlan]:
        """Get rollback plan from database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rollback_id, migration_id, rollback_type, rollback_points,
                   target_tables, estimated_duration, risk_level, prerequisites,
                   validation_steps, approval_required, approved_by, approved_at,
                   created_at, executed_at, completed_at, status
            FROM rollback_plans
            WHERE rollback_id = ?
        ''', (rollback_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Get rollback points
        rollback_point_ids = json.loads(row[3])
        rollback_points = []
        for rp_id in rollback_point_ids:
            rp = await self._get_rollback_point_by_id(rp_id)
            if rp:
                rollback_points.append(rp)

        return RollbackPlan(
            rollback_id=row[0],
            migration_id=row[1],
            rollback_type=RollbackType(row[2]),
            rollback_points=rollback_points,
            target_tables=json.loads(row[4]),
            estimated_duration_minutes=row[5],
            risk_level=row[6],
            prerequisites=json.loads(row[7]),
            validation_steps=json.loads(row[8]),
            approval_required=bool(row[9]),
            approved_by=row[10],
            approved_at=datetime.fromisoformat(row[11]) if row[11] else None
        )

    async def _get_rollback_point_by_id(self, rollback_point_id: str) -> Optional[RollbackPoint]:
        """Get rollback point by ID"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, migration_id, timestamp, description, backup_path,
                   tables, metadata, checksum, size_bytes, created_at
            FROM rollback_points
            WHERE id = ?
        ''', (rollback_point_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return RollbackPoint(
            id=row[0],
            migration_id=row[1],
            timestamp=datetime.fromisoformat(row[2]),
            description=row[3],
            backup_path=row[4],
            tables=json.loads(row[5]),
            metadata=json.loads(row[6]),
            checksum=row[7],
            size_bytes=row[8],
            created_at=datetime.fromisoformat(row[9])
        )

    async def _update_plan_status(self, rollback_id: str, status: str):
        """Update rollback plan status"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        update_field = "executed_at"
        if status == "completed":
            update_field = "completed_at"

        cursor.execute(f'''
            UPDATE rollback_plans
            SET status = ?, {update_field} = ?
            WHERE rollback_id = ?
        ''', (status, datetime.now(timezone.utc).isoformat(), rollback_id))

        conn.commit()
        conn.close()

    async def _save_rollback_result(self, result: RollbackResult):
        """Save rollback result to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO rollback_results (
                rollback_id, status, start_time, end_time, tables_rolled_back,
                tables_failed, records_affected, errors, warnings, validation_results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.rollback_id,
            result.status.value,
            result.start_time.isoformat(),
            result.end_time.isoformat() if result.end_time else None,
            json.dumps(result.tables_rolled_back),
            json.dumps(result.tables_failed),
            json.dumps(result.records_affected),
            json.dumps(result.errors),
            json.dumps(result.warnings),
            json.dumps(result.validation_results)
        ))

        conn.commit()
        conn.close()

    # Rollback strategy implementations
    async def _execute_full_rollback(self, plan: RollbackPlan, result: RollbackResult):
        """Execute full database rollback"""
        logger.info(f"Executing full rollback for {plan.migration_id}")

        for rollback_point in plan.rollback_points:
            backup_path = Path(rollback_point.backup_path)

            # Restore all tables from backup
            for table in plan.target_tables:
                try:
                    await self._restore_table(table, backup_path)
                    result.tables_rolled_back.append(table)

                    # Record affected rows
                    row_count = await self._count_table_rows(table)
                    result.records_affected[table] = row_count

                except Exception as e:
                    logger.error(f"Failed to restore table {table}: {e}")
                    result.tables_failed.append(table)
                    result.errors.append(f"Table {table}: {str(e)}")

    async def _execute_partial_rollback(self, plan: RollbackPlan, result: RollbackResult):
        """Execute partial rollback"""
        logger.info(f"Executing partial rollback for {plan.migration_id}")

        # Similar to full rollback but with additional checks
        await self._execute_full_rollback(plan, result)

    async def _execute_point_in_time_rollback(self, plan: RollbackPlan, result: RollbackResult):
        """Execute point-in-time rollback"""
        logger.info(f"Executing point-in-time rollback for {plan.migration_id}")

        # This would require database-specific point-in-time recovery
        # For now, fall back to full rollback
        await self._execute_full_rollback(plan, result)

    async def _execute_table_level_rollback(self, plan: RollbackPlan, result: RollbackResult):
        """Execute table-level rollback"""
        logger.info(f"Executing table-level rollback for {plan.migration_id}")

        for rollback_point in plan.rollback_points:
            backup_path = Path(rollback_point.backup_path)

            # Restore specific tables
            for table in plan.target_tables:
                try:
                    await self._restore_table(table, backup_path)
                    result.tables_rolled_back.append(table)

                    row_count = await self._count_table_rows(table)
                    result.records_affected[table] = row_count

                except Exception as e:
                    logger.error(f"Failed to restore table {table}: {e}")
                    result.tables_failed.append(table)
                    result.errors.append(f"Table {table}: {str(e)}")

    async def _execute_transaction_rollback(self, plan: RollbackPlan, result: RollbackResult):
        """Execute transaction-based rollback"""
        logger.info(f"Executing transaction rollback for {plan.migration_id}")

        # This would require transaction logs to be maintained
        # For now, fall back to table-level rollback
        await self._execute_table_level_rollback(plan, result)

    async def _restore_table(self, table_name: str, backup_path: Path):
        """Restore a table from backup"""
        backup_file = backup_path / f"{table_name}.csv"

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        # This would be implemented with actual database restore logic
        logger.info(f"Restoring table {table_name} from {backup_file}")

    async def _count_table_rows(self, table_name: str) -> int:
        """Count rows in a table"""
        # This would be implemented with actual database query
        return 0  # Placeholder

    async def approve_rollback(self, rollback_id: str, approved_by: str) -> bool:
        """Approve a rollback plan"""
        plan = await self._get_rollback_plan(rollback_id)
        if not plan:
            return False

        if not plan.approval_required:
            return True  # No approval needed

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE rollback_plans
            SET approved_by = ?, approved_at = ?
            WHERE rollback_id = ?
        ''', (approved_by, datetime.now(timezone.utc).isoformat(), rollback_id))

        conn.commit()
        conn.close()

        logger.info(f"Rollback {rollback_id} approved by {approved_by}")
        return True

    async def get_rollback_history(self, migration_id: str = None) -> List[Dict[str, Any]]:
        """Get rollback history"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        if migration_id:
            cursor.execute('''
                SELECT rp.*, pl.rollback_type, pl.status as plan_status
                FROM rollback_points rp
                LEFT JOIN rollback_plans pl ON rp.migration_id = pl.migration_id
                WHERE rp.migration_id = ?
                ORDER BY rp.timestamp DESC
            ''', (migration_id,))
        else:
            cursor.execute('''
                SELECT rp.*, pl.rollback_type, pl.status as plan_status
                FROM rollback_points rp
                LEFT JOIN rollback_plans pl ON rp.migration_id = pl.migration_id
                ORDER BY rp.timestamp DESC
                LIMIT 50
            ''')

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "rollback_point_id": row[0],
                "migration_id": row[1],
                "timestamp": row[2],
                "description": row[3],
                "tables": json.loads(row[5]),
                "size_bytes": row[7],
                "rollback_type": row[10],
                "status": row[11]
            })

        return history

    async def validate_rollback_point(self, rollback_point_id: str) -> Dict[str, Any]:
        """Validate a rollback point"""
        rollback_point = await self._get_rollback_point_by_id(rollback_point_id)
        if not rollback_point:
            return {"valid": False, "error": "Rollback point not found"}

        backup_path = Path(rollback_point.backup_path)

        validation_result = {
            "valid": True,
            "rollback_point_id": rollback_point_id,
            "checks": {}
        }

        # Check backup directory exists
        if not backup_path.exists():
            validation_result["valid"] = False
            validation_result["checks"]["backup_exists"] = False
            return validation_result

        validation_result["checks"]["backup_exists"] = True

        # Check manifest file
        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            validation_result["valid"] = False
            validation_result["checks"]["manifest_exists"] = False
            return validation_result

        validation_result["checks"]["manifest_exists"] = True

        # Validate checksum
        current_checksum = await self._calculate_backup_checksum(backup_path)
        if current_checksum != rollback_point.checksum:
            validation_result["valid"] = False
            validation_result["checks"]["checksum_valid"] = False
            validation_result["checks"]["expected_checksum"] = rollback_point.checksum
            validation_result["checks"]["actual_checksum"] = current_checksum
        else:
            validation_result["checks"]["checksum_valid"] = True

        # Check backup files for each table
        missing_files = []
        for table in rollback_point.tables:
            backup_file = backup_path / f"{table}.csv"
            if not backup_file.exists():
                missing_files.append(table)

        if missing_files:
            validation_result["valid"] = False
            validation_result["checks"]["all_files_present"] = False
            validation_result["checks"]["missing_files"] = missing_files
        else:
            validation_result["checks"]["all_files_present"] = True

        return validation_result

# Example usage
async def test_rollback_system():
    """Test rollback system functionality"""
    rollback_manager = RollbackManager("/tmp/test_rollback")

    try:
        # Create rollback point
        rollback_point = await rollback_manager.create_rollback_point(
            migration_id="test_migration",
            tables=["characters", "campaigns", "sessions"],
            description="Test rollback point"
        )

        print(f"Created rollback point: {rollback_point.id}")

        # Create rollback plan
        plan = await rollback_manager.create_rollback_plan(
            migration_id="test_migration",
            rollback_type=RollbackType.TABLE_LEVEL,
            target_tables=["characters"]
        )

        print(f"Created rollback plan: {plan.rollback_id}")
        print(f"Risk level: {plan.risk_level}")
        print(f"Estimated duration: {plan.estimated_duration_minutes} minutes")

        # Validate rollback point
        validation = await rollback_manager.validate_rollback_point(rollback_point.id)
        print(f"Rollback point validation: {validation}")

        # Get rollback history
        history = await rollback_manager.get_rollback_history()
        print(f"Rollback history: {len(history)} entries")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rollback_system())