#!/usr/bin/env python3
"""
Integrity Validator - Backup validation and integrity checking

This validator provides comprehensive backup integrity verification including
checksum validation, data consistency checks, corruption detection, and
validation reports for the DMLogn8n backup system.
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
import pydicom
import pandas as pd
import yaml
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ValidationStatus(Enum):
    """Validation status types"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"

class ValidationType(Enum):
    """Validation types"""
    CHECKSUM = "checksum"
    SIZE = "size"
    FORMAT = "format"
    STRUCTURE = "structure"
    CONTENT = "content"
    CONSISTENCY = "consistency"
    CORRUPTION = "corruption"
    ENCRYPTION = "encryption"

class SeverityLevel(Enum):
    """Issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Validation issue information"""
    type: str
    severity: str
    description: str
    details: Dict[str, Any]
    file_path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None

@dataclass
class ValidationResult:
    """Validation operation result"""
    backup_id: str
    validation_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: float
    total_files: int
    validated_files: int
    failed_files: int
    issues: List[ValidationIssue]
    metrics: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]

@dataclass
class ValidationConfig:
    """Validation configuration"""
    enabled_validations: List[str]
    checksum_algorithms: List[str]
    deep_validation_enabled: bool = True
    content_validation_enabled: bool = True
    corruption_detection_enabled: bool = True
    parallel_validation: bool = True
    max_concurrent_validations: int = 5
    timeout_seconds: int = 1800
    retry_failed_validations: bool = True
    max_retries: int = 3
    generate_reports: bool = True
    alert_on_failures: bool = True
    alert_threshold_severity: str = "error"

class IntegrityValidator:
    """Main backup integrity validator"""

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/validation_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db_manager = ValidationDatabaseManager()
        self.validator_plugins = {}
        self.active_validations = {}

        # Initialize validator plugins
        self.init_validator_plugins()

        # Start background tasks
        self.start_background_tasks()

        logger.info("Integrity validator initialized")

    def load_config(self) -> Dict[str, Any]:
        """Load validation configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load validation config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration"""
        return {
            'validation_config': ValidationConfig(
                enabled_validations=[
                    ValidationType.CHECKSUM.value,
                    ValidationType.SIZE.value,
                    ValidationType.FORMAT.value,
                    ValidationType.STRUCTURE.value,
                    ValidationType.CORRUPTION.value
                ],
                checksum_algorithms=['md5', 'sha256'],
                deep_validation_enabled=True,
                content_validation_enabled=True,
                corruption_detection_enabled=True,
                parallel_validation=True,
                max_concurrent_validations=5,
                timeout_seconds=1800,
                retry_failed_validations=True,
                max_retries=3,
                generate_reports=True,
                alert_on_failures=True,
                alert_threshold_severity=SeverityLevel.ERROR.value
            ),
            'file_validators': {
                'database_dumps': {
                    'enabled': True,
                    'formats': ['.sql', '.dump', '.backup'],
                    'validations': ['sql_syntax', 'table_structure', 'data_consistency']
                },
                'configuration_files': {
                    'enabled': True,
                    'formats': ['.yaml', '.yml', '.json', '.xml', '.ini', '.env'],
                    'validations': ['syntax_check', 'schema_validation', 'required_fields']
                },
                'archive_files': {
                    'enabled': True,
                    'formats': ['.tar', '.tar.gz', '.tar.bz2', '.zip'],
                    'validations': ['archive_integrity', 'file_list_verification', 'extraction_test']
                },
                'binary_files': {
                    'enabled': True,
                    'formats': ['.bin', '.dat', '.pkl', '.model'],
                    'validations': ['header_check', 'magic_number', 'structure_validation']
                },
                'log_files': {
                    'enabled': True,
                    'formats': ['.log', '.out', '.txt'],
                    'validations': ['log_format', 'timestamp_continuity', 'corruption_detection']
                }
            },
            'content_validators': {
                'image_files': {
                    'enabled': True,
                    'formats': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
                    'validations': ['image_header', 'dimensions', 'corruption_check']
                },
                'document_files': {
                    'enabled': True,
                    'formats': ['.pdf', '.docx', '.xlsx', '.txt', '.md'],
                    'validations': ['file_header', 'readability_check', 'content_structure']
                }
            },
            'reporting': {
                'output_directory': '/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/reports',
                'report_formats': ['json', 'html', 'csv'],
                'include_recommendations': True,
                'include_metrics': True,
                'auto_cleanup_days': 90
            }
        }

    def init_validator_plugins(self):
        """Initialize validator plugins"""
        self.validator_plugins = {
            'checksum_validator': ChecksumValidator(self.config),
            'size_validator': SizeValidator(self.config),
            'format_validator': FormatValidator(self.config),
            'structure_validator': StructureValidator(self.config),
            'content_validator': ContentValidator(self.config),
            'corruption_validator': CorruptionValidator(self.config),
            'encryption_validator': EncryptionValidator(self.config)
        }

    def start_background_tasks(self):
        """Start background validation tasks"""
        # This would start periodic validation tasks
        pass

    async def validate_backup(self, backup_id: str, validation_types: Optional[List[str]] = None) -> ValidationResult:
        """Validate a backup with specified validation types"""
        logger.info(f"Starting validation for backup: {backup_id}")

        start_time = time.time()
        validation_id = f"validation_{backup_id}_{int(start_time)}"

        # Use default validation types if not specified
        if not validation_types:
            validation_types = self.config['validation_config'].enabled_validations

        try:
            # Get backup metadata
            backup_metadata = self.get_backup_metadata(backup_id)
            if not backup_metadata:
                raise Exception(f"Backup metadata not found: {backup_id}")

            # Initialize validation result
            result = ValidationResult(
                backup_id=backup_id,
                validation_type="comprehensive",
                status=ValidationStatus.RUNNING.value,
                started_at=datetime.now(timezone.utc),
                completed_at=None,
                duration_seconds=0,
                total_files=0,
                validated_files=0,
                failed_files=0,
                issues=[],
                metrics={},
                summary={},
                recommendations=[]
            )

            # Save initial validation status
            self.db_manager.save_validation_result(result)

            # Download backup for validation
            backup_path = await self.download_backup_for_validation(backup_metadata)

            # Extract backup if needed
            extracted_path = await self.extract_backup_if_needed(backup_path, backup_metadata)

            # Get list of files to validate
            files_to_validate = self.get_files_for_validation(extracted_path, backup_metadata)
            result.total_files = len(files_to_validate)

            # Run validations
            if self.config['validation_config'].parallel_validation:
                issues = await self.run_parallel_validations(
                    files_to_validate, validation_types, backup_metadata
                )
            else:
                issues = await self.run_sequential_validations(
                    files_to_validate, validation_types, backup_metadata
                )

            result.issues.extend(issues)

            # Calculate metrics
            result.metrics = await self.calculate_validation_metrics(
                files_to_validate, result.issues, backup_metadata
            )

            # Generate summary
            result.summary = self.generate_validation_summary(result)

            # Generate recommendations
            result.recommendations = self.generate_recommendations(result.issues)

            # Update final status
            result.status = self.determine_final_status(result.issues)
            result.completed_at = datetime.now(timezone.utc)
            result.duration_seconds = time.time() - start_time
            result.validated_files = result.total_files - len([i for i in result.issues if i.severity == SeverityLevel.CRITICAL.value])
            result.failed_files = len([i for i in result.issues if i.severity in [SeverityLevel.ERROR.value, SeverityLevel.CRITICAL.value]])

            # Save final validation result
            self.db_manager.save_validation_result(result)

            # Generate report if enabled
            if self.config['validation_config'].generate_reports:
                await self.generate_validation_report(result)

            # Send alert if needed
            if self.config['validation_config'].alert_on_failures:
                await self.send_validation_alert(result)

            # Cleanup temporary files
            await self.cleanup_validation_files(backup_path, extracted_path)

            logger.info(f"Validation completed for backup {backup_id}: {result.status} ({result.duration_seconds:.2f}s)")
            return result

        except Exception as e:
            logger.error(f"Validation failed for backup {backup_id}: {e}")

            # Create error result
            error_result = ValidationResult(
                backup_id=backup_id,
                validation_type="comprehensive",
                status=ValidationStatus.ERROR.value,
                started_at=datetime.fromtimestamp(start_time, timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_seconds=time.time() - start_time,
                total_files=0,
                validated_files=0,
                failed_files=1,
                issues=[ValidationIssue(
                    type=ValidationType.CORRUPTION.value,
                    severity=SeverityLevel.CRITICAL.value,
                    description=f"Validation failed: {str(e)}",
                    details={'error': str(e)}
                )],
                metrics={},
                summary={'status': 'error', 'error': str(e)},
                recommendations=['Retry validation', 'Check backup integrity', 'Verify backup source']
            )

            self.db_manager.save_validation_result(error_result)
            return error_result

    async def run_parallel_validations(self, files_to_validate: List[str],
                                    validation_types: List[str],
                                    backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Run validations in parallel"""
        max_concurrent = self.config['validation_config'].max_concurrent_validations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_single_file(file_path: str):
            async with semaphore:
                return await self.validate_file(file_path, validation_types, backup_metadata)

        tasks = [validate_single_file(file_path) for file_path in files_to_validate]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and filter out exceptions
        all_issues = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"File validation error: {result}")
            elif isinstance(result, list):
                all_issues.extend(result)

        return all_issues

    async def run_sequential_validations(self, files_to_validate: List[str],
                                       validation_types: List[str],
                                       backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Run validations sequentially"""
        all_issues = []

        for file_path in files_to_validate:
            try:
                issues = await self.validate_file(file_path, validation_types, backup_metadata)
                all_issues.extend(issues)
            except Exception as e:
                logger.error(f"File validation error for {file_path}: {e}")
                all_issues.append(ValidationIssue(
                    type=ValidationType.CORRUPTION.value,
                    severity=SeverityLevel.ERROR.value,
                    description=f"Validation error: {str(e)}",
                    details={'file_path': file_path, 'error': str(e)},
                    file_path=file_path
                ))

        return all_issues

    async def validate_file(self, file_path: str, validation_types: List[str],
                         backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a single file"""
        issues = []

        for validation_type in validation_types:
            try:
                if validation_type == ValidationType.CHECKSUM.value:
                    validator = self.validator_plugins['checksum_validator']
                elif validation_type == ValidationType.SIZE.value:
                    validator = self.validator_plugins['size_validator']
                elif validation_type == ValidationType.FORMAT.value:
                    validator = self.validator_plugins['format_validator']
                elif validation_type == ValidationType.STRUCTURE.value:
                    validator = self.validator_plugins['structure_validator']
                elif validation_type == ValidationType.CONTENT.value:
                    validator = self.validator_plugins['content_validator']
                elif validation_type == ValidationType.CORRUPTION.value:
                    validator = self.validator_plugins['corruption_validator']
                elif validation_type == ValidationType.ENCRYPTION.value:
                    validator = self.validator_plugins['encryption_validator']
                else:
                    logger.warning(f"Unknown validation type: {validation_type}")
                    continue

                file_issues = await validator.validate_file(file_path, backup_metadata)
                issues.extend(file_issues)

            except Exception as e:
                logger.error(f"Validation error for {validation_type} on {file_path}: {e}")
                issues.append(ValidationIssue(
                    type=validation_type,
                    severity=SeverityLevel.ERROR.value,
                    description=f"Validation error: {str(e)}",
                    details={'file_path': file_path, 'validation_type': validation_type, 'error': str(e)},
                    file_path=file_path
                ))

        return issues

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

    async def download_backup_for_validation(self, backup_metadata: Dict[str, Any]) -> str:
        """Download backup for validation"""
        # This would integrate with storage backends to download the backup
        # For now, assume backup is accessible locally
        temp_dir = tempfile.mkdtemp(prefix=f"validation_{backup_metadata['backup_id']}_")

        # Return the path where backup would be downloaded
        return temp_dir

    async def extract_backup_if_needed(self, backup_path: str, backup_metadata: Dict[str, Any]) -> str:
        """Extract backup if it's an archive"""
        extracted_path = backup_path  # Default to same path

        # Check if backup is an archive and extract if needed
        for file in os.listdir(backup_path):
            file_path = os.path.join(backup_path, file)
            if file.endswith(('.tar.gz', '.tar.bz2', '.tar', '.zip')):
                extraction_dir = os.path.join(backup_path, 'extracted')
                os.makedirs(extraction_dir, exist_ok=True)

                if file.endswith('.tar.gz') or file.endswith('.tgz'):
                    with tarfile.open(file_path, 'r:gz') as tar:
                        tar.extractall(extraction_dir)
                elif file.endswith('.tar.bz2'):
                    with tarfile.open(file_path, 'r:bz2') as tar:
                        tar.extractall(extraction_dir)
                elif file.endswith('.tar'):
                    with tarfile.open(file_path, 'r') as tar:
                        tar.extractall(extraction_dir)
                elif file.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extraction_dir)

                extracted_path = extraction_dir
                break

        return extracted_path

    def get_files_for_validation(self, path: str, backup_metadata: Dict[str, Any]) -> List[str]:
        """Get list of files to validate"""
        files_to_validate = []

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)

                # Skip hidden files and temporary files
                if file.startswith('.') or file.endswith('.tmp'):
                    continue

                # Check file size (skip very large files for content validation)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 100 * 1024 * 1024:  # 100MB
                        logger.info(f"Skipping large file for content validation: {file_path}")
                        continue
                except OSError:
                    continue

                files_to_validate.append(file_path)

        return files_to_validate

    async def calculate_validation_metrics(self, files: List[str], issues: List[ValidationIssue],
                                        backup_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate validation metrics"""
        total_files = len(files)
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i.severity == SeverityLevel.CRITICAL.value])
        error_issues = len([i for i in issues if i.severity == SeverityLevel.ERROR.value])
        warning_issues = len([i for i in issues if i.severity == SeverityLevel.WARNING.value])

        # Calculate issue counts by type
        issues_by_type = {}
        for issue in issues:
            issues_by_type[issue.type] = issues_by_type.get(issue.type, 0) + 1

        # Calculate backup size
        total_size = 0
        for file_path in files:
            try:
                total_size += os.path.getsize(file_path)
            except OSError:
                pass

        return {
            'total_files': total_files,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'error_issues': error_issues,
            'warning_issues': warning_issues,
            'issues_by_type': issues_by_type,
            'total_size_bytes': total_size,
            'validation_success_rate': ((total_files - critical_issues - error_issues) / total_files * 100) if total_files > 0 else 0,
            'backup_size_mb': total_size / (1024 * 1024)
        }

    def generate_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """Generate validation summary"""
        status = "passed"
        if result.issues:
            max_severity = max([SeverityLevel[i.severity].value for i in result.issues])
            if max_severity >= SeverityLevel.CRITICAL.value:
                status = "failed"
            elif max_severity >= SeverityLevel.ERROR.value:
                status = "warning"

        return {
            'status': status,
            'total_files': result.total_files,
            'validated_files': result.validated_files,
            'failed_files': result.failed_files,
            'total_issues': len(result.issues),
            'critical_issues': len([i for i in result.issues if i.severity == SeverityLevel.CRITICAL.value]),
            'error_issues': len([i for i in result.issues if i.severity == SeverityLevel.ERROR.value]),
            'warning_issues': len([i for i in result.issues if i.severity == SeverityLevel.WARNING.value]),
            'validation_rate': (result.validated_files / result.total_files * 100) if result.total_files > 0 else 0,
            'duration_seconds': result.duration_seconds
        }

    def generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations based on validation issues"""
        recommendations = []

        critical_count = len([i for i in issues if i.severity == SeverityLevel.CRITICAL.value])
        error_count = len([i for i in issues if i.severity == SeverityLevel.ERROR.value])
        warning_count = len([i for i in issues if i.severity == SeverityLevel.WARNING.value])

        if critical_count > 0:
            recommendations.append("Critical issues found - backup is unreliable and should be recreated")
            recommendations.append("Investigate backup source and process for corruption")

        if error_count > 0:
            recommendations.append("Errors detected - consider creating a new backup")
            recommendations.append("Review backup configuration and storage integrity")

        if warning_count > error_count * 2:
            recommendations.append("High number of warnings - review backup process")

        # Specific recommendations based on issue types
        checksum_issues = [i for i in issues if i.type == ValidationType.CHECKSUM.value]
        if checksum_issues:
            recommendations.append("Checksum mismatches detected - verify data integrity")
            recommendations.append("Check storage backend for data corruption")

        corruption_issues = [i for i in issues if i.type == ValidationType.CORRUPTION.value]
        if corruption_issues:
            recommendations.append("File corruption detected - investigate storage media")
            recommendations.append("Consider implementing additional redundancy")

        size_issues = [i for i in issues if i.type == ValidationType.SIZE.value]
        if size_issues:
            recommendations.append("Size inconsistencies detected - verify backup completeness")

        if not recommendations:
            recommendations.append("Backup validation passed successfully")

        return recommendations

    def determine_final_status(self, issues: List[ValidationIssue]) -> str:
        """Determine final validation status based on issues"""
        if not issues:
            return ValidationStatus.PASSED.value

        max_severity = 0
        for issue in issues:
            severity_value = SeverityLevel[issue.severity].value
            severity_rank = list(SeverityLevel).index(SeverityLevel[issue.severity])
            if severity_rank > max_severity:
                max_severity = severity_rank

        if max_severity >= list(SeverityLevel).index(SeverityLevel.CRITICAL):
            return ValidationStatus.FAILED.value
        elif max_severity >= list(SeverityLevel).index(SeverityLevel.ERROR):
            return ValidationStatus.WARNING.value
        else:
            return ValidationStatus.PASSED.value

    async def generate_validation_report(self, result: ValidationResult):
        """Generate validation report"""
        report_dir = Path(self.config['reporting']['output_directory'])
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        report_base = f"validation_report_{result.backup_id}_{timestamp}"

        # Generate JSON report
        if 'json' in self.config['reporting']['report_formats']:
            json_path = report_dir / f"{report_base}.json"
            with open(json_path, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)

        # Generate HTML report
        if 'html' in self.config['reporting']['report_formats']:
            html_path = report_dir / f"{report_base}.html"
            await self.generate_html_report(result, html_path)

        # Generate CSV report
        if 'csv' in self.config['reporting']['report_formats']:
            csv_path = report_dir / f"{report_base}.csv"
            await self.generate_csv_report(result, csv_path)

        logger.info(f"Validation reports generated for {result.backup_id}")

    async def generate_html_report(self, result: ValidationResult, output_path: Path):
        """Generate HTML validation report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backup Validation Report - {result.backup_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .issues {{ margin: 20px 0; }}
                .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .critical {{ border-left-color: #d32f2f; background-color: #ffebee; }}
                .error {{ border-left-color: #f57c00; background-color: #fff3e0; }}
                .warning {{ border-left-color: #fbc02d; background-color: #fffde7; }}
                .info {{ border-left-color: #1976d2; background-color: #e3f2fd; }}
                .metrics {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .metric {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Backup Validation Report</h1>
                <p><strong>Backup ID:</strong> {result.backup_id}</p>
                <p><strong>Status:</strong> <span style="color: {'red' if result.status == 'failed' else 'orange' if result.status == 'warning' else 'green'}">{result.status.upper()}</span></p>
                <p><strong>Validation Date:</strong> {result.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Duration:</strong> {result.duration_seconds:.2f} seconds</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>Total Files</h3>
                        <p style="font-size: 24px;">{result.summary.get('total_files', 0)}</p>
                    </div>
                    <div class="metric">
                        <h3>Validated Files</h3>
                        <p style="font-size: 24px;">{result.summary.get('validated_files', 0)}</p>
                    </div>
                    <div class="metric">
                        <h3>Failed Files</h3>
                        <p style="font-size: 24px; color: red;">{result.summary.get('failed_files', 0)}</p>
                    </div>
                    <div class="metric">
                        <h3>Total Issues</h3>
                        <p style="font-size: 24px; color: orange;">{result.summary.get('total_issues', 0)}</p>
                    </div>
                </div>
            </div>

            <div class="issues">
                <h2>Issues Found</h2>
        """

        for issue in result.issues:
            html_content += f"""
                <div class="issue {issue.severity}">
                    <h4>{issue.type.replace('_', ' ').title()} - {issue.severity.upper()}</h4>
                    <p><strong>Description:</strong> {issue.description}</p>
                    {f'<p><strong>File:</strong> {issue.file_path}</p>' if issue.file_path else ''}
                    {f'<p><strong>Expected:</strong> {issue.expected_value}</p>' if issue.expected_value else ''}
                    {f'<p><strong>Actual:</strong> {issue.actual_value}</p>' if issue.actual_value else ''}
                    {f'<details><summary>Details</summary><pre>{json.dumps(issue.details, indent=2, default=str)}</pre></details>' if issue.details else ''}
                </div>
            """

        if result.recommendations:
            html_content += """
                <div class="recommendations">
                    <h2>Recommendations</h2>
                    <ul>
            """
            for rec in result.recommendations:
                html_content += f"<li>{rec}</li>"
            html_content += "</ul></div>"

        html_content += """
            </body>
            </html>
        """

        with open(output_path, 'w') as f:
            f.write(html_content)

    async def generate_csv_report(self, result: ValidationResult, output_path: Path):
        """Generate CSV validation report"""
        import csv

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['backup_id', 'validation_type', 'file_path', 'issue_type', 'severity', 'description', 'expected_value', 'actual_value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for issue in result.issues:
                writer.writerow({
                    'backup_id': result.backup_id,
                    'validation_type': result.validation_type,
                    'file_path': issue.file_path or '',
                    'issue_type': issue.type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'expected_value': str(issue.expected_value) if issue.expected_value else '',
                    'actual_value': str(issue.actual_value) if issue.actual_value else ''
                })

    async def send_validation_alert(self, result: ValidationResult):
        """Send validation alert if needed"""
        threshold = self.config['validation_config'].alert_threshold_severity
        threshold_rank = list(SeverityLevel).index(SeverityLevel[threshold])

        # Check if any issues meet or exceed threshold
        for issue in result.issues:
            issue_rank = list(SeverityLevel).index(SeverityLevel[issue.severity])
            if issue_rank >= threshold_rank:
                # Send alert (implementation would depend on alerting system)
                logger.warning(f"Validation alert triggered for backup {result.backup_id}: {issue.description}")
                break

    async def cleanup_validation_files(self, backup_path: str, extracted_path: str):
        """Clean up temporary validation files"""
        try:
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            if os.path.exists(extracted_path) and extracted_path != backup_path:
                shutil.rmtree(extracted_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup validation files: {e}")

    def get_validation_history(self, backup_id: str, limit: int = 10) -> List[ValidationResult]:
        """Get validation history for a backup"""
        return self.db_manager.get_validation_history(backup_id, limit)

    def get_recent_validations(self, hours: int = 24, limit: int = 50) -> List[ValidationResult]:
        """Get recent validations"""
        return self.db_manager.get_recent_validations(hours, limit)


class ValidationDatabaseManager:
    """Manages validation metadata database"""

    def __init__(self, db_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize validation database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    validation_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    validation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    duration_seconds REAL,
                    total_files INTEGER,
                    validated_files INTEGER,
                    failed_files INTEGER,
                    issues TEXT,
                    metrics TEXT,
                    summary TEXT,
                    recommendations TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_validation_backup_id ON validation_results(backup_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_validation_started_at ON validation_results(started_at)
            """)

    def save_validation_result(self, result: ValidationResult):
        """Save validation result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO validation_results
                (validation_id, backup_id, validation_type, status, started_at, completed_at,
                 duration_seconds, total_files, validated_files, failed_files, issues,
                 metrics, summary, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"validation_{result.backup_id}_{int(result.started_at.timestamp())}",
                result.backup_id,
                result.validation_type,
                result.status,
                result.started_at,
                result.completed_at,
                result.duration_seconds,
                result.total_files,
                result.validated_files,
                result.failed_files,
                json.dumps([asdict(issue) for issue in result.issues], default=str),
                json.dumps(result.metrics, default=str),
                json.dumps(result.summary, default=str),
                json.dumps(result.recommendations)
            ))

    def get_validation_history(self, backup_id: str, limit: int = 10) -> List[ValidationResult]:
        """Get validation history for a backup"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM validation_results
                WHERE backup_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (backup_id, limit))

            results = []
            for row in cursor.fetchall():
                # Convert row to ValidationResult object
                # Implementation would need to deserialize JSON fields
                pass

            return results

    def get_recent_validations(self, hours: int = 24, limit: int = 50) -> List[ValidationResult]:
        """Get recent validations"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM validation_results
                WHERE started_at > ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (cutoff_time, limit))

            results = []
            for row in cursor.fetchall():
                # Convert row to ValidationResult object
                pass

            return results


# Base validator class
class BaseValidator:
    """Base class for all validators"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a single file - to be implemented by subclasses"""
        raise NotImplementedError


class ChecksumValidator(BaseValidator):
    """Checksum validation for files"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file checksum"""
        issues = []

        try:
            # Calculate current checksums
            algorithms = self.config['validation_config'].checksum_algorithms
            current_checksums = {}

            for algorithm in algorithms:
                if algorithm == 'md5':
                    current_checksums['md5'] = self.calculate_md5(file_path)
                elif algorithm == 'sha256':
                    current_checksums['sha256'] = self.calculate_sha256(file_path)

            # Compare with expected checksums if available
            expected_checksum = backup_metadata.get('checksum')
            if expected_checksum:
                if 'md5' in current_checksums and current_checksums['md5'] != expected_checksum:
                    issues.append(ValidationIssue(
                        type=ValidationType.CHECKSUM.value,
                        severity=SeverityLevel.CRITICAL.value,
                        description="MD5 checksum mismatch",
                        details={'algorithm': 'md5'},
                        file_path=file_path,
                        expected_value=expected_checksum,
                        actual_value=current_checksums['md5']
                    ))

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.CHECKSUM.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Checksum validation error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    def calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 checksum"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 checksum"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class SizeValidator(BaseValidator):
    """File size validation"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file size"""
        issues = []

        try:
            actual_size = os.path.getsize(file_path)

            # Check for empty files that shouldn't be empty
            if actual_size == 0:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext not in ['.log', '.tmp', '.lock']:
                    issues.append(ValidationIssue(
                        type=ValidationType.SIZE.value,
                        severity=SeverityLevel.WARNING.value,
                        description="File is empty but expected to contain data",
                        details={'file_extension': file_ext},
                        file_path=file_path,
                        actual_size=actual_size
                    ))

            # Check for suspiciously large files
            if actual_size > 5 * 1024 * 1024 * 1024:  # 5GB
                issues.append(ValidationIssue(
                    type=ValidationType.SIZE.value,
                    severity=SeverityLevel.INFO.value,
                    description="Large file detected",
                    details={'size_gb': actual_size / (1024**3)},
                    file_path=file_path,
                    actual_size=actual_size
                ))

        except OSError as e:
            issues.append(ValidationIssue(
                type=ValidationType.SIZE.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Cannot read file size: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues


class FormatValidator(BaseValidator):
    """File format validation"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file format"""
        issues = []

        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            # Validate common formats
            if file_ext in ['.yaml', '.yml']:
                self.validate_yaml_file(file_path, issues)
            elif file_ext == '.json':
                self.validate_json_file(file_path, issues)
            elif file_ext == '.xml':
                self.validate_xml_file(file_path, issues)
            elif file_ext in ['.tar.gz', '.tgz']:
                self.validate_tar_gz_file(file_path, issues)
            elif file_ext == '.zip':
                self.validate_zip_file(file_path, issues)

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Format validation error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    def validate_yaml_file(self, file_path: str, issues: List[ValidationIssue]):
        """Validate YAML file format"""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description="Invalid YAML format",
                details={'yaml_error': str(e)},
                file_path=file_path
            ))

    def validate_json_file(self, file_path: str, issues: List[ValidationIssue]):
        """Validate JSON file format"""
        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description="Invalid JSON format",
                details={'json_error': str(e), 'line': e.lineno, 'column': e.colno},
                file_path=file_path
            ))

    def validate_xml_file(self, file_path: str, issues: List[ValidationIssue]):
        """Validate XML file format"""
        try:
            ET.parse(file_path)
        except ET.ParseError as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description="Invalid XML format",
                details={'xml_error': str(e)},
                file_path=file_path
            ))

    def validate_tar_gz_file(self, file_path: str, issues: List[ValidationIssue]):
        """Validate tar.gz archive format"""
        try:
            with tarfile.open(file_path, 'r:gz') as tar:
                # Just try to read the archive structure
                tar.getnames()
        except (tarfile.TarError, gzip.BadGzipFile) as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description="Invalid tar.gz archive format",
                details={'archive_error': str(e)},
                file_path=file_path
            ))

    def validate_zip_file(self, file_path: str, issues: List[ValidationIssue]):
        """Validate ZIP archive format"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Test archive integrity
                bad_files = zip_ref.testzip()
                if bad_files:
                    issues.append(ValidationIssue(
                        type=ValidationType.FORMAT.value,
                        severity=SeverityLevel.ERROR.value,
                        description="ZIP archive contains corrupted files",
                        details={'corrupted_files': bad_files},
                        file_path=file_path
                    ))
        except zipfile.BadZipFile as e:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT.value,
                severity=SeverityLevel.ERROR.value,
                description="Invalid ZIP archive format",
                details={'zip_error': str(e)},
                file_path=file_path
            ))


class StructureValidator(BaseValidator):
    """File structure validation"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file structure"""
        issues = []

        try:
            # Check for expected files/directories in backup
            backup_name = backup_metadata.get('name', '')

            # Example: database backups should contain specific files
            if 'database' in backup_name.lower():
                self.validate_database_structure(file_path, issues)

            # Example: configuration backups should contain specific files
            elif 'config' in backup_name.lower():
                self.validate_config_structure(file_path, issues)

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.STRUCTURE.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Structure validation error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    def validate_database_structure(self, file_path: str, issues: List[ValidationIssue]):
        """Validate database backup structure"""
        # Implementation would check for expected database backup structure
        pass

    def validate_config_structure(self, file_path: str, issues: List[ValidationIssue]):
        """Validate configuration backup structure"""
        # Implementation would check for expected configuration files
        pass


class ContentValidator(BaseValidator):
    """File content validation"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file content"""
        issues = []

        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            # Validate content based on file type
            if file_ext == '.sql':
                self.validate_sql_content(file_path, issues)
            elif file_ext in ['.log', '.out']:
                self.validate_log_content(file_path, issues)

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.CONTENT.value,
                severity=SeverityLevel.WARNING.value,
                description=f"Content validation error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    def validate_sql_content(self, file_path: str, issues: List[ValidationIssue]):
        """Validate SQL file content"""
        try:
            # Read first few lines to check if it looks like SQL
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(5)]

            sql_keywords = ['CREATE', 'INSERT', 'UPDATE', 'DELETE', 'SELECT', 'DROP', 'ALTER']
            content = ' '.join(first_lines).upper()

            if not any(keyword in content for keyword in sql_keywords):
                issues.append(ValidationIssue(
                    type=ValidationType.CONTENT.value,
                    severity=SeverityLevel.WARNING.value,
                    description="SQL file may not contain valid SQL statements",
                    details={},
                    file_path=file_path
                ))

        except Exception:
            # If we can't read the file, skip content validation
            pass

    def validate_log_content(self, file_path: str, issues: List[ValidationIssue]):
        """Validate log file content"""
        try:
            # Check for common log patterns
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(10)]

            # Look for timestamp patterns
            import re
            timestamp_pattern = r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}'

            timestamp_count = sum(1 for line in first_lines if re.search(timestamp_pattern, line))

            if timestamp_count < len(first_lines) * 0.5:
                issues.append(ValidationIssue(
                    type=ValidationType.CONTENT.value,
                    severity=SeverityLevel.INFO.value,
                    description="Log file may not follow standard timestamp format",
                    details={'timestamp_lines': timestamp_count, 'total_lines': len(first_lines)},
                    file_path=file_path
                ))

        except Exception:
            pass


class CorruptionValidator(BaseValidator):
    """File corruption detection"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Detect file corruption"""
        issues = []

        try:
            file_size = os.path.getsize(file_path)

            # Check for truncated files (if expected size is known)
            expected_size = backup_metadata.get('size_bytes')
            if expected_size and file_size != expected_size:
                issues.append(ValidationIssue(
                    type=ValidationType.CORRUPTION.value,
                    severity=SeverityLevel.ERROR.value,
                    description="File size mismatch - possible corruption",
                    details={'expected_size': expected_size, 'actual_size': file_size},
                    file_path=file_path,
                    expected_value=expected_size,
                    actual_value=file_size
                ))

            # Check for null bytes in text files
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.txt', '.log', '.json', '.yaml', '.yml', '.xml']:
                await self.check_null_bytes(file_path, issues)

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.CORRUPTION.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Corruption check error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    async def check_null_bytes(self, file_path: str, issues: List[ValidationIssue]):
        """Check for null bytes in text files"""
        try:
            with open(file_path, 'rb') as f:
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    if b'\x00' in chunk:
                        issues.append(ValidationIssue(
                            type=ValidationType.CORRUPTION.value,
                            severity=SeverityLevel.WARNING.value,
                            description="Null bytes found in text file - possible corruption",
                            details={'null_bytes_detected': True},
                            file_path=file_path
                        ))
                        break

        except Exception:
            pass


class EncryptionValidator(BaseValidator):
    """Encryption validation"""

    async def validate_file(self, file_path: str, backup_metadata: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate file encryption"""
        issues = []

        try:
            # Check if file is expected to be encrypted
            is_encrypted = backup_metadata.get('encryption_enabled', False)

            if is_encrypted:
                # Validate that file appears to be encrypted
                if not await self.check_file_encryption(file_path):
                    issues.append(ValidationIssue(
                        type=ValidationType.ENCRYPTION.value,
                        severity=SeverityLevel.WARNING.value,
                        description="File expected to be encrypted but doesn't appear to be",
                        details={},
                        file_path=file_path
                    ))

        except Exception as e:
            issues.append(ValidationIssue(
                type=ValidationType.ENCRYPTION.value,
                severity=SeverityLevel.ERROR.value,
                description=f"Encryption validation error: {str(e)}",
                details={'error': str(e)},
                file_path=file_path
            ))

        return issues

    async def check_file_encryption(self, file_path: str) -> bool:
        """Check if file appears to be encrypted"""
        try:
            # Simple heuristic: encrypted files should have high entropy
            with open(file_path, 'rb') as f:
                sample = f.read(1024)  # Read first 1KB

            # Calculate entropy
            if len(sample) > 0:
                byte_counts = [0] * 256
                for byte in sample:
                    byte_counts[byte] += 1

                entropy = 0
                for count in byte_counts:
                    if count > 0:
                        probability = count / len(sample)
                        entropy -= probability * (probability.bit_length() - 1)

                # High entropy (> 7.0) suggests encryption
                return entropy > 7.0

        except Exception:
            pass

        return False