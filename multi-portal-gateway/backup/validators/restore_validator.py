#!/usr/bin/env python3
"""
Restore Validator - Backup validation for restore operations

This validator provides comprehensive backup validation specifically for restore
operations including backup integrity, compatibility checks, dependency validation,
and restore feasibility assessment for the DMLogn8n backup system.
"""

import asyncio
import logging
import os
import json
import hashlib
import time
import sqlite3
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import tarfile
import gzip
import zipfile
import yaml
import xml.etree.ElementTree as ET
import psycopg2
import redis

logger = logging.getLogger(__name__)

class RestoreValidationStatus(Enum):
    """Restore validation status types"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"

class RestoreValidationType(Enum):
    """Restore validation types"""
    BACKUP_INTEGRITY = "backup_integrity"
    COMPATIBILITY_CHECK = "compatibility_check"
    DEPENDENCY_VALIDATION = "dependency_validation"
    RESOURCE_REQUIREMENTS = "resource_requirements"
    VERSION_COMPATIBILITY = "version_compatibility"
    CONFIGURATION_COMPATIBILITY = "configuration_compatibility"
    DATA_CONSISTENCY = "data_consistency"
    RESTORE_FEASIBILITY = "restore_feasibility"

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    BLOCKER = "blocker"

@dataclass
class RestoreValidationIssue:
    """Restore validation issue information"""
    type: str
    severity: str
    description: str
    details: Dict[str, Any]
    recommendation: str
    blocking: bool = False
    component: Optional[str] = None

@dataclass
class RestoreValidationResult:
    """Restore validation operation result"""
    backup_id: str
    restore_id: Optional[str]
    validation_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    is_restorable: bool
    compatibility_score: float
    issues: List[RestoreValidationIssue]
    system_requirements: Dict[str, Any]
    restore_steps: List[str]
    prerequisites: List[str]
    risks: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

@dataclass
class RestoreValidationConfig:
    """Restore validation configuration"""
    enabled_validations: List[str]
    strict_mode: bool = True
    compatibility_threshold: float = 0.8
    version_compatibility_check: bool = True
    dependency_validation: bool = True
    resource_validation: bool = True
    test_restore_enabled: bool = False
    parallel_validation: bool = True
    max_concurrent_validations: int = 3
    timeout_seconds: int = 1800
    generate_restore_plan: bool = True
    risk_assessment: bool = True

class RestoreValidator:
    """Main backup restore validator"""

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/restore_validation_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db_manager = RestoreValidationDatabaseManager()
        self.validation_plugins = {}
        self.system_info = {}
        self.active_validations = {}

        # Initialize validation plugins
        self.init_validation_plugins()

        # Load system information
        self.load_system_info()

        logger.info("Restore validator initialized")

    def load_config(self) -> Dict[str, Any]:
        """Load restore validation configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load restore validation config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default restore validation configuration"""
        return {
            'validation_config': RestoreValidationConfig(
                enabled_validations=[
                    RestoreValidationType.BACKUP_INTEGRITY.value,
                    RestoreValidationType.COMPATIBILITY_CHECK.value,
                    RestoreValidationType.DEPENDENCY_VALIDATION.value,
                    RestoreValidationType.VERSION_COMPATIBILITY.value,
                    RestoreValidationType.RESOURCE_REQUIREMENTS.value,
                    RestoreValidationType.RESTORE_FEASIBILITY.value
                ],
                strict_mode=True,
                compatibility_threshold=0.8,
                version_compatibility_check=True,
                dependency_validation=True,
                resource_validation=True,
                test_restore_enabled=False,
                parallel_validation=True,
                max_concurrent_validations=3,
                timeout_seconds=1800,
                generate_restore_plan=True,
                risk_assessment=True
            ),
            'compatibility_matrix': {
                'postgresql_versions': {
                    '12': ['12', '13', '14', '15'],
                    '13': ['13', '14', '15'],
                    '14': ['14', '15'],
                    '15': ['15']
                },
                'python_versions': {
                    '3.8': ['3.8', '3.9', '3.10', '3.11'],
                    '3.9': ['3.9', '3.10', '3.11'],
                    '3.10': ['3.10', '3.11'],
                    '3.11': ['3.11']
                },
                'dmlogn8n_versions': {
                    '1.0': ['1.0', '1.1', '1.2'],
                    '1.1': ['1.1', '1.2', '1.3'],
                    '1.2': ['1.2', '1.3', '1.4'],
                    '1.3': ['1.3', '1.4'],
                    '1.4': ['1.4']
                }
            },
            'system_requirements': {
                'minimum_disk_space_gb': 50,
                'minimum_memory_gb': 8,
                'minimum_cpu_cores': 2,
                'supported_platforms': ['linux', 'darwin', 'win32'],
                'required_services': ['postgresql', 'redis', 'nginx'],
                'optional_services': ['elasticsearch', 'kibana', 'grafana']
            },
            'risk_factors': {
                'version_mismatch_penalty': 0.2,
                'missing_dependency_penalty': 0.3,
                'insufficient_resources_penalty': 0.4,
                'backup_age_penalty_days': 30,
                'configuration_drift_penalty': 0.1
            }
        }

    def init_validation_plugins(self):
        """Initialize validation plugins"""
        self.validation_plugins = {
            'integrity_validator': BackupIntegrityValidator(self.config),
            'compatibility_validator': CompatibilityValidator(self.config),
            'dependency_validator': DependencyValidator(self.config),
            'resource_validator': ResourceValidator(self.config),
            'version_validator': VersionValidator(self.config),
            'configuration_validator': ConfigurationValidator(self.config),
            'feasibility_validator': RestoreFeasibilityValidator(self.config)
        }

    def load_system_info(self):
        """Load current system information"""
        try:
            import platform
            import psutil

            self.system_info = {
                'platform': platform.system().lower(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_free_gb': psutil.disk_usage('/').free / (1024**3),
                'python_version': platform.python_version(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Check for required services
            self.system_info['services'] = self.check_service_status()

        except Exception as e:
            logger.error(f"Failed to load system info: {e}")
            self.system_info = {}

    def check_service_status(self) -> Dict[str, bool]:
        """Check status of required services"""
        services = {}

        # Check PostgreSQL
        try:
            conn = psycopg2.connect(
                host='localhost',
                user='postgres',
                database='postgres',
                connect_timeout=5
            )
            conn.close()
            services['postgresql'] = True
        except:
            services['postgresql'] = False

        # Check Redis
        try:
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
            r.ping()
            services['redis'] = True
        except:
            services['redis'] = False

        # Check other services
        services['nginx'] = self.check_service_running('nginx')
        services['docker'] = self.check_service_running('docker')

        return services

    def check_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    async def validate_backup_for_restore(self, backup_id: str, restore_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate backup for restore operation"""
        logger.info(f"Starting restore validation for backup: {backup_id}")

        start_time = time.time()
        validation_id = f"restore_validation_{backup_id}_{int(start_time)}"

        try:
            # Get backup metadata
            backup_metadata = self.get_backup_metadata(backup_id)
            if not backup_metadata:
                raise Exception(f"Backup metadata not found: {backup_id}")

            # Initialize validation result
            result = RestoreValidationResult(
                backup_id=backup_id,
                restore_id=restore_id,
                validation_type="comprehensive",
                status=RestoreValidationStatus.RUNNING.value,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                duration_seconds=0,
                is_restorable=False,
                compatibility_score=0.0,
                issues=[],
                system_requirements={},
                restore_steps=[],
                prerequisites=[],
                risks=[],
                recommendations=[],
                metadata={}
            )

            # Save initial validation status
            self.db_manager.save_validation_result(result)

            # Get enabled validation types
            validation_types = self.config['validation_config'].enabled_validations

            # Run validations
            if self.config['validation_config'].parallel_validation:
                issues = await self.run_parallel_validations(
                    validation_types, backup_metadata, result
                )
            else:
                issues = await self.run_sequential_validations(
                    validation_types, backup_metadata, result
                )

            result.issues.extend(issues)

            # Calculate compatibility score
            result.compatibility_score = self.calculate_compatibility_score(
                result.issues, backup_metadata
            )

            # Determine if backup is restorable
            result.is_restorable = self.determine_restorability(result)

            # Generate system requirements
            result.system_requirements = self.generate_system_requirements(backup_metadata)

            # Generate restore steps
            if self.config['validation_config'].generate_restore_plan:
                result.restore_steps = self.generate_restore_steps(backup_metadata, result.issues)

            # Generate prerequisites
            result.prerequisites = self.generate_prerequisites(result.issues)

            # Generate risk assessment
            if self.config['validation_config'].risk_assessment:
                result.risks = self.generate_risk_assessment(result.issues, backup_metadata)

            # Generate recommendations
            result.recommendations = self.generate_recommendations(result.issues)

            # Update final status
            result.status = self.determine_final_status(result.issues, result.is_restorable)
            result.completed_at = datetime.now(timezone.utc)
            result.duration_seconds = time.time() - start_time

            # Save final validation result
            self.db_manager.save_validation_result(result)

            logger.info(f"Restore validation completed for {backup_id}: {result.status} (score: {result.compatibility_score:.2f})")
            return {
                'valid': result.is_restorable,
                'compatibility_score': result.compatibility_score,
                'issues': [asdict(issue) for issue in result.issues],
                'recommendations': result.recommendations,
                'restore_steps': result.restore_steps,
                'prerequisites': result.prerequisites,
                'risks': result.risks,
                'system_requirements': result.system_requirements
            }

        except Exception as e:
            logger.error(f"Restore validation failed for backup {backup_id}: {e}")

            # Create error result
            error_result = {
                'valid': False,
                'compatibility_score': 0.0,
                'issues': [{
                    'type': 'validation_error',
                    'severity': 'critical',
                    'description': f"Validation failed: {str(e)}",
                    'details': {'error': str(e)},
                    'recommendation': 'Check backup metadata and system configuration',
                    'blocking': True
                }],
                'recommendations': ['Retry validation', 'Check backup integrity', 'Verify system requirements'],
                'restore_steps': [],
                'prerequisites': [],
                'risks': ['Backup may be corrupted', 'System may not meet requirements'],
                'system_requirements': {}
            }

            return error_result

    async def run_parallel_validations(self, validation_types: List[str],
                                    backup_metadata: Dict[str, Any],
                                    result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Run validations in parallel"""
        max_concurrent = self.config['validation_config'].max_concurrent_validations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_single_type(validation_type: str):
            async with semaphore:
                return await self.validate_by_type(validation_type, backup_metadata, result)

        tasks = [validate_single_type(vtype) for vtype in validation_types]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and filter out exceptions
        all_issues = []
        for validation_result in results:
            if isinstance(validation_result, Exception):
                logger.error(f"Validation error: {validation_result}")
            elif isinstance(validation_result, list):
                all_issues.extend(validation_result)

        return all_issues

    async def run_sequential_validations(self, validation_types: List[str],
                                      backup_metadata: Dict[str, Any],
                                      result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Run validations sequentially"""
        all_issues = []

        for validation_type in validation_types:
            try:
                issues = await self.validate_by_type(validation_type, backup_metadata, result)
                all_issues.extend(issues)

                # Stop early if critical issues found
                if any(issue.blocking for issue in issues):
                    logger.warning(f"Critical blocking issues found in {validation_type}, stopping further validation")
                    break

            except Exception as e:
                logger.error(f"Validation error for {validation_type}: {e}")
                all_issues.append(RestoreValidationIssue(
                    type=validation_type,
                    severity=ValidationSeverity.CRITICAL.value,
                    description=f"Validation error: {str(e)}",
                    details={'validation_type': validation_type, 'error': str(e)},
                    recommendation='Check system configuration and retry',
                    blocking=True
                ))

        return all_issues

    async def validate_by_type(self, validation_type: str, backup_metadata: Dict[str, Any],
                             result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate backup by specific type"""
        try:
            if validation_type == RestoreValidationType.BACKUP_INTEGRITY.value:
                validator = self.validation_plugins['integrity_validator']
            elif validation_type == RestoreValidationType.COMPATIBILITY_CHECK.value:
                validator = self.validation_plugins['compatibility_validator']
            elif validation_type == RestoreValidationType.DEPENDENCY_VALIDATION.value:
                validator = self.validation_plugins['dependency_validator']
            elif validation_type == RestoreValidationType.RESOURCE_REQUIREMENTS.value:
                validator = self.validation_plugins['resource_validator']
            elif validation_type == RestoreValidationType.VERSION_COMPATIBILITY.value:
                validator = self.validation_plugins['version_validator']
            elif validation_type == RestoreValidationType.CONFIGURATION_COMPATIBILITY.value:
                validator = self.validation_plugins['configuration_validator']
            elif validation_type == RestoreValidationType.RESTORE_FEASIBILITY.value:
                validator = self.validation_plugins['feasibility_validator']
            else:
                logger.warning(f"Unknown validation type: {validation_type}")
                return []

            issues = await validator.validate(backup_metadata, self.system_info, result)
            return issues

        except Exception as e:
            logger.error(f"Validation error for {validation_type}: {e}")
            return [RestoreValidationIssue(
                type=validation_type,
                severity=ValidationSeverity.ERROR.value,
                description=f"Validation error: {str(e)}",
                details={'validation_type': validation_type, 'error': str(e)},
                recommendation='Retry validation',
                blocking=False
            )]

    def get_backup_metadata(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get backup metadata from database"""
        try:
            with sqlite3.connect('/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db') as conn:
                cursor = conn.execute("""
                    SELECT * FROM backups WHERE backup_id = ?
                """, (backup_id,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Failed to get backup metadata: {e}")
            return None

    def calculate_compatibility_score(self, issues: List[RestoreValidationIssue],
                                   backup_metadata: Dict[str, Any]) -> float:
        """Calculate compatibility score based on issues"""
        score = 1.0

        # Apply penalties for different issue types
        for issue in issues:
            if issue.severity == ValidationSeverity.BLOCKER.value:
                score = 0.0
                break
            elif issue.severity == ValidationSeverity.CRITICAL.value:
                score -= 0.3
            elif issue.severity == ValidationSeverity.ERROR.value:
                score -= 0.2
            elif issue.severity == ValidationSeverity.WARNING.value:
                score -= 0.1

        # Apply age penalty
        if backup_metadata.get('created_at'):
            backup_age = datetime.now(timezone.utc) - datetime.fromisoformat(backup_metadata['created_at'])
            age_days = backup_age.days
            age_penalty = min(age_days / self.config['risk_factors']['backup_age_penalty_days'], 0.2)
            score -= age_penalty

        # Ensure score doesn't go below 0
        return max(0.0, score)

    def determine_restorability(self, result: RestoreValidationResult) -> bool:
        """Determine if backup is restorable"""
        # Check for blocking issues
        if any(issue.blocking for issue in result.issues):
            return False

        # Check compatibility score
        threshold = self.config['validation_config'].compatibility_threshold
        if result.compatibility_score < threshold:
            return False

        # Check for critical issues in strict mode
        if self.config['validation_config'].strict_mode:
            if any(issue.severity in [ValidationSeverity.CRITICAL.value, ValidationSeverity.ERROR.value]
                   for issue in result.issues):
                return False

        return True

    def generate_system_requirements(self, backup_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system requirements for restore"""
        # Get requirements from backup metadata
        backup_size = backup_metadata.get('size_bytes', 0)
        backup_type = backup_metadata.get('backup_type', 'full')

        # Calculate space requirements (backup size + 50% overhead)
        required_space_gb = (backup_size * 1.5) / (1024**3)

        requirements = {
            'disk_space_gb': max(required_space_gb, self.config['system_requirements']['minimum_disk_space_gb']),
            'memory_gb': self.config['system_requirements']['minimum_memory_gb'],
            'cpu_cores': self.config['system_requirements']['minimum_cpu_cores'],
            'platform': self.system_info.get('platform', 'unknown'),
            'services': self.config['system_requirements']['required_services'],
            'estimated_restore_time_minutes': self.estimate_restore_time(backup_size, backup_type)
        }

        # Add specific requirements based on backup content
        if backup_metadata.get('name', '').startswith('database'):
            requirements['services'].append('postgresql')
            requirements['memory_gb'] = max(requirements['memory_gb'], 16)

        return requirements

    def estimate_restore_time(self, backup_size_bytes: int, backup_type: str) -> int:
        """Estimate restore time in minutes"""
        # Base restore rate: 100MB per minute
        base_rate = 100 * 1024 * 1024  # bytes per minute

        # Adjust based on backup type
        if backup_type == 'full':
            base_rate *= 0.8  # Full restores are slower
        elif backup_type == 'incremental':
            base_rate *= 1.2  # Incremental restores are faster

        # Calculate estimated time
        estimated_minutes = backup_size_bytes / base_rate

        # Add overhead time
        estimated_minutes += 10  # 10 minutes overhead

        return int(estimated_minutes)

    def generate_restore_steps(self, backup_metadata: Dict[str, Any],
                             issues: List[RestoreValidationIssue]) -> List[str]:
        """Generate step-by-step restore plan"""
        steps = []

        backup_name = backup_metadata.get('name', 'unknown')

        # Pre-restore steps
        steps.extend([
            "1. Stop all running DMLogn8n services",
            "2. Verify system requirements are met",
            "3. Create current system backup for rollback",
            "4. Download backup from storage",
            "5. Verify backup integrity"
        ])

        # Specific steps based on backup type
        if backup_name.startswith('database'):
            steps.extend([
                "6. Stop PostgreSQL service",
                "7. Backup current database",
                "8. Restore database from backup",
                "9. Verify database integrity",
                "10. Restart PostgreSQL service"
            ])
        elif backup_name.startswith('files'):
            steps.extend([
                "6. Backup current application files",
                "7. Restore application files from backup",
                "8. Verify file permissions and ownership",
                "9. Update configuration if needed"
            ])
        elif backup_name.startswith('config'):
            steps.extend([
                "6. Backup current configuration files",
                "7. Restore configuration files from backup",
                "8. Validate configuration syntax",
                "9. Update service configurations"
            ])

        # Post-restore steps
        steps.extend([
            "11. Start DMLogn8n services",
            "12. Verify service health",
            "13. Run system tests",
            "14. Monitor system performance",
            "15. Validate application functionality"
        ])

        # Add issue-specific steps
        for issue in issues:
            if issue.severity == ValidationSeverity.WARNING.value:
                steps.append(f"⚠️  Address: {issue.description}")

        return steps

    def generate_prerequisites(self, issues: List[RestoreValidationIssue]) -> List[str]:
        """Generate list of prerequisites for restore"""
        prerequisites = [
            "Sufficient disk space for restore operation",
            "All required services installed and configured",
            "Valid backup storage credentials",
            "Administrative/system privileges",
            "Network connectivity to backup storage"
        ]

        # Add prerequisites based on issues
        for issue in issues:
            if 'service' in issue.type.lower():
                prerequisites.append(f"Service '{issue.component}' must be available")
            elif 'dependency' in issue.type.lower():
                prerequisites.append(f"Dependency '{issue.component}' must be installed")
            elif 'resource' in issue.type.lower():
                prerequisites.append(f"Additional {issue.component} resources required")

        return list(set(prerequisites))  # Remove duplicates

    def generate_risk_assessment(self, issues: List[RestoreValidationIssue],
                               backup_metadata: Dict[str, Any]) -> List[str]:
        """Generate risk assessment"""
        risks = []

        # Age-related risks
        if backup_metadata.get('created_at'):
            backup_age = datetime.now(timezone.utc) - datetime.fromisoformat(backup_metadata['created_at'])
            if backup_age.days > 30:
                risks.append(f"Backup is {backup_age.days} days old - may contain outdated data")

        # Issue-based risks
        critical_issues = [i for i in issues if i.severity in [ValidationSeverity.CRITICAL.value, ValidationSeverity.ERROR.value]]
        if critical_issues:
            risks.append(f"{len(critical_issues)} critical issues found - restore may fail")

        # System compatibility risks
        platform_mismatch = self.system_info.get('platform') != backup_metadata.get('platform')
        if platform_mismatch:
            risks.append("Platform mismatch detected - compatibility issues may occur")

        # Size-related risks
        backup_size = backup_metadata.get('size_bytes', 0)
        if backup_size > 10 * 1024**3:  # 10GB
            risks.append("Large backup size - restore operation will be time-consuming")

        return risks

    def generate_recommendations(self, issues: List[RestoreValidationIssue]) -> List[str]:
        """Generate recommendations based on validation issues"""
        recommendations = []

        # Group issues by severity
        critical_issues = [i for i in issues if i.severity in [ValidationSeverity.BLOCKER.value, ValidationSeverity.CRITICAL.value]]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR.value]
        warning_issues = [i for i in issues if i.severity == ValidationSeverity.WARNING.value]

        if critical_issues:
            recommendations.append("Address critical issues before attempting restore")
            recommendations.append("Consider creating a new backup if current one has critical issues")

        if error_issues:
            recommendations.append("Resolve error conditions to ensure successful restore")
            recommendations.append("Test restore in non-production environment first")

        if warning_issues:
            recommendations.append("Review and address warnings for optimal restore results")

        # Add specific recommendations from issues
        for issue in issues:
            if issue.recommendation:
                recommendations.append(issue.recommendation)

        # General recommendations
        if not issues:
            recommendations.append("Backup appears suitable for restore")
            recommendations.append("Proceed with standard restore procedures")
            recommendations.append("Monitor restore process closely")
        else:
            recommendations.append("Consider creating a new backup after addressing issues")
            recommendations.append("Document all issues and resolutions for future reference")

        return list(set(recommendations))  # Remove duplicates

    def determine_final_status(self, issues: List[RestoreValidationIssue], is_restorable: bool) -> str:
        """Determine final validation status"""
        if not is_restorable:
            if any(issue.blocking for issue in issues):
                return RestoreValidationStatus.FAILED.value
            else:
                return RestoreValidationStatus.INCOMPATIBLE.value

        if any(issue.severity in [ValidationSeverity.CRITICAL.value, ValidationSeverity.ERROR.value] for issue in issues):
            return RestoreValidationStatus.WARNING.value

        return RestoreValidationStatus.PASSED.value


class RestoreValidationDatabaseManager:
    """Manages restore validation metadata database"""

    def __init__(self, db_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize restore validation database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restore_validations (
                    validation_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    restore_id TEXT,
                    validation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    duration_seconds REAL,
                    is_restorable BOOLEAN,
                    compatibility_score REAL,
                    issues TEXT,
                    system_requirements TEXT,
                    restore_steps TEXT,
                    prerequisites TEXT,
                    risks TEXT,
                    recommendations TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_restore_validation_backup_id ON restore_validations(backup_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_restore_validation_started_at ON restore_validations(started_at)
            """)

    def save_validation_result(self, result: RestoreValidationResult):
        """Save validation result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO restore_validations
                (validation_id, backup_id, restore_id, validation_type, status, started_at,
                 completed_at, duration_seconds, is_restorable, compatibility_score,
                 issues, system_requirements, restore_steps, prerequisites,
                 risks, recommendations, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"restore_validation_{result.backup_id}_{int(result.started_at.timestamp())}",
                result.backup_id,
                result.restore_id,
                result.validation_type,
                result.status,
                result.started_at,
                result.completed_at,
                result.duration_seconds,
                result.is_restorable,
                result.compatibility_score,
                json.dumps([asdict(issue) for issue in result.issues], default=str),
                json.dumps(result.system_requirements, default=str),
                json.dumps(result.restore_steps),
                json.dumps(result.prerequisites),
                json.dumps(result.risks),
                json.dumps(result.recommendations),
                json.dumps(result.metadata, default=str)
            ))


# Base validator class for restore validation
class BaseRestoreValidator:
    """Base class for all restore validators"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate backup for restore - to be implemented by subclasses"""
        raise NotImplementedError


class BackupIntegrityValidator(BaseRestoreValidator):
    """Backup integrity validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate backup integrity"""
        issues = []

        # Check backup status
        if backup_metadata.get('status') != 'completed':
            issues.append(RestoreValidationIssue(
                type="backup_status",
                severity=ValidationSeverity.CRITICAL.value,
                description=f"Backup status is '{backup_metadata.get('status')}' not 'completed'",
                details={'backup_status': backup_metadata.get('status')},
                recommendation="Use a completed backup for restore",
                blocking=True
            ))

        # Check backup age
        if backup_metadata.get('created_at'):
            backup_age = datetime.now(timezone.utc) - datetime.fromisoformat(backup_metadata['created_at'])
            if backup_age.days > 180:  # 6 months
                issues.append(RestoreValidationIssue(
                    type="backup_age",
                    severity=ValidationSeverity.WARNING.value,
                    description=f"Backup is {backup_age.days} days old",
                    details={'age_days': backup_age.days, 'created_at': backup_metadata['created_at']},
                    recommendation="Consider using a more recent backup if available"
                ))

        # Check validation status
        if backup_metadata.get('validation_status') == 'failed':
            issues.append(RestoreValidationIssue(
                type="backup_validation",
                severity=ValidationSeverity.ERROR.value,
                description="Backup validation previously failed",
                details={'validation_status': backup_metadata.get('validation_status')},
                recommendation="Verify backup integrity before restore",
                blocking=False
            ))

        return issues


class CompatibilityValidator(BaseRestoreValidator):
    """System compatibility validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate system compatibility"""
        issues = []

        # Check platform compatibility
        backup_platform = backup_metadata.get('platform', system_info.get('platform'))
        current_platform = system_info.get('platform')

        if backup_platform and current_platform and backup_platform != current_platform:
            issues.append(RestoreValidationIssue(
                type="platform_compatibility",
                severity=ValidationSeverity.WARNING.value,
                description=f"Platform mismatch: backup from {backup_platform}, current system {current_platform}",
                details={'backup_platform': backup_platform, 'current_platform': current_platform},
                recommendation="Verify cross-platform compatibility",
                component="platform"
            ))

        # Check architecture compatibility
        backup_arch = backup_metadata.get('architecture')
        current_arch = system_info.get('architecture')

        if backup_arch and current_arch and backup_arch != current_arch:
            issues.append(RestoreValidationIssue(
                type="architecture_compatibility",
                severity=ValidationSeverity.WARNING.value,
                description=f"Architecture mismatch: backup from {backup_arch}, current system {current_arch}",
                details={'backup_arch': backup_arch, 'current_arch': current_arch},
                recommendation="Verify architecture compatibility",
                component="architecture"
            ))

        return issues


class DependencyValidator(BaseRestoreValidator):
    """Dependency validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate system dependencies"""
        issues = []

        required_services = self.config['system_requirements']['required_services']
        services_status = system_info.get('services', {})

        for service in required_services:
            if not services_status.get(service, False):
                severity = ValidationSeverity.CRITICAL.value if service in ['postgresql', 'redis'] else ValidationSeverity.ERROR.value
                issues.append(RestoreValidationIssue(
                    type="service_dependency",
                    severity=severity,
                    description=f"Required service '{service}' is not running",
                    details={'service': service, 'status': services_status.get(service)},
                    recommendation=f"Start and configure {service} before restore",
                    blocking=service in ['postgresql', 'redis'],
                    component=service
                ))

        # Check Python version compatibility
        backup_python = backup_metadata.get('python_version')
        current_python = system_info.get('python_version')

        if backup_python and current_python:
            compatibility_matrix = self.config['compatibility_matrix']['python_versions']
            compatible_versions = compatibility_matrix.get(backup_python.split('.')[0] + '.' + backup_python.split('.')[1], [])

            if not any(current_python.startswith(v) for v in compatible_versions):
                issues.append(RestoreValidationIssue(
                    type="python_compatibility",
                    severity=ValidationSeverity.WARNING.value,
                    description=f"Python version compatibility issue: backup {backup_python}, current {current_python}",
                    details={'backup_python': backup_python, 'current_python': current_python},
                    recommendation="Consider Python version upgrade or downgrade",
                    component="python"
                ))

        return issues


class ResourceValidator(BaseRestoreValidator):
    """Resource requirements validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate system resources"""
        issues = []

        # Check disk space
        backup_size = backup_metadata.get('size_bytes', 0)
        required_space = backup_size * 1.5  # 50% overhead
        available_space = system_info.get('disk_free_gb', 0) * 1024**3

        if available_space < required_space:
            issues.append(RestoreValidationIssue(
                type="disk_space",
                severity=ValidationSeverity.CRITICAL.value,
                description=f"Insufficient disk space: required {required_space/(1024**3):.1f}GB, available {available_space/(1024**3):.1f}GB",
                details={'required_bytes': required_space, 'available_bytes': available_space},
                recommendation="Free up disk space or use larger storage",
                blocking=True,
                component="disk"
            ))

        # Check memory
        required_memory = self.config['system_requirements']['minimum_memory_gb']
        available_memory = system_info.get('memory_total_gb', 0)

        if available_memory < required_memory:
            issues.append(RestoreValidationIssue(
                type="memory",
                severity=ValidationSeverity.ERROR.value,
                description=f"Insufficient memory: required {required_memory}GB, available {available_memory:.1f}GB",
                details={'required_gb': required_memory, 'available_gb': available_memory},
                recommendation="Add more memory or use system with more RAM",
                component="memory"
            ))

        # Check CPU cores
        required_cores = self.config['system_requirements']['minimum_cpu_cores']
        available_cores = system_info.get('cpu_count', 0)

        if available_cores < required_cores:
            issues.append(RestoreValidationIssue(
                type="cpu_cores",
                severity=ValidationSeverity.WARNING.value,
                description=f"Insufficient CPU cores: required {required_cores}, available {available_cores}",
                details={'required_cores': required_cores, 'available_cores': available_cores},
                recommendation="More CPU cores recommended for optimal performance",
                component="cpu"
            ))

        return issues


class VersionValidator(BaseRestoreValidator):
    """Version compatibility validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate version compatibility"""
        issues = []

        # Check DMLogn8n version compatibility
        backup_version = backup_metadata.get('dmlogn8n_version')
        if backup_version:
            # Get current version (this would come from application metadata)
            current_version = "1.4.0"  # Placeholder

            compatibility_matrix = self.config['compatibility_matrix']['dmlogn8n_versions']
            compatible_versions = compatibility_matrix.get(backup_version, [])

            if current_version not in compatible_versions:
                issues.append(RestoreValidationIssue(
                    type="dmlogn8n_version_compatibility",
                    severity=ValidationSeverity.ERROR.value,
                    description=f"DMLogn8n version incompatibility: backup {backup_version}, current {current_version}",
                    details={'backup_version': backup_version, 'current_version': current_version},
                    recommendation="Upgrade application version or use compatible backup",
                    component="dmlogn8n"
                ))

        return issues


class ConfigurationValidator(BaseRestoreValidator):
    """Configuration compatibility validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate configuration compatibility"""
        issues = []

        # This would check configuration compatibility
        # Implementation depends on specific configuration formats and requirements

        backup_config_version = backup_metadata.get('config_version')
        if backup_config_version:
            # Check if configuration schema is compatible
            current_config_version = "2.0"  # Placeholder

            if backup_config_version != current_config_version:
                issues.append(RestoreValidationIssue(
                    type="configuration_compatibility",
                    severity=ValidationSeverity.WARNING.value,
                    description=f"Configuration version mismatch: backup {backup_config_version}, current {current_config_version}",
                    details={'backup_config_version': backup_config_version, 'current_config_version': current_config_version},
                    recommendation="Review configuration changes and migrate if necessary",
                    component="configuration"
                ))

        return issues


class RestoreFeasibilityValidator(BaseRestoreValidator):
    """Restore feasibility validator"""

    async def validate(self, backup_metadata: Dict[str, Any], system_info: Dict[str, Any],
                     result: RestoreValidationResult) -> List[RestoreValidationIssue]:
        """Validate overall restore feasibility"""
        issues = []

        # Check if backup is accessible
        if not backup_metadata.get('storage_path'):
            issues.append(RestoreValidationIssue(
                type="backup_accessibility",
                severity=ValidationSeverity.CRITICAL.value,
                description="Backup storage path not available",
                details={},
                recommendation="Verify backup storage accessibility",
                blocking=True
            ))

        # Check for required restore tools
        missing_tools = self.check_restore_tools()
        if missing_tools:
            issues.append(RestoreValidationIssue(
                type="restore_tools",
                severity=ValidationSeverity.ERROR.value,
                description=f"Missing required restore tools: {', '.join(missing_tools)}",
                details={'missing_tools': missing_tools},
                recommendation="Install required restore tools before proceeding",
                component="tools"
            ))

        return issues

    def check_restore_tools(self) -> List[str]:
        """Check for required restore tools"""
        missing_tools = []
        required_tools = ['tar', 'gzip', 'psql', 'redis-cli']

        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)

        return missing_tools