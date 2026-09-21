#!/usr/bin/env python3
"""
Data Validator
Comprehensive data integrity validation during migration
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict
import statistics

logger = logging.getLogger("data_validator")

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationType(Enum):
    """Types of data validation"""
    ROW_COUNT = "row_count"
    CHECKSUM = "checksum"
    DATA_TYPE = "data_type"
    NULL_CONSTRAINT = "null_constraint"
    UNIQUE_CONSTRAINT = "unique_constraint"
    FOREIGN_KEY = "foreign_key"
    RANGE_CHECK = "range_check"
    PATTERN_MATCH = "pattern_match"
    BUSINESS_RULE = "business_rule"
    CUSTOM_SQL = "custom_sql"
    PERFORMANCE = "performance"

@dataclass
class ValidationRule:
    """Single validation rule definition"""
    name: str
    type: ValidationType
    description: str
    level: ValidationLevel = ValidationLevel.ERROR
    table: Optional[str] = None
    column: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    sql_query: Optional[str] = None
    expected_result: Any = None
    tolerance: float = 0.0
    enabled: bool = True

@dataclass
class ValidationResult:
    """Result of a validation check"""
    rule_name: str
    status: str  # PASSED, FAILED, SKIPPED
    level: ValidationLevel
    message: str
    expected_value: Any = None
    actual_value: Any = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TableValidationResult:
    """Validation results for a single table"""
    table_name: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int
    warnings: List[ValidationResult] = field(default_factory=list)
    errors: List[ValidationResult] = field(default_factory=list)
    critical_issues: List[ValidationResult] = field(default_factory=list)
    execution_time_seconds: float = 0.0

@dataclass
class MigrationValidationReport:
    """Complete migration validation report"""
    migration_id: str
    source_database: str
    target_database: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tables: int = 0
    total_rules: int = 0
    overall_status: str = "IN_PROGRESS"
    table_results: Dict[str, TableValidationResult] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

class DataValidator:
    """Comprehensive data validation engine"""

    def __init__(self):
        self.validation_functions = self._initialize_validation_functions()
        self.checksum_algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256
        }
        self.performance_thresholds = self._load_performance_thresholds()

    def _initialize_validation_functions(self) -> Dict[ValidationType, callable]:
        """Initialize validation function handlers"""
        return {
            ValidationType.ROW_COUNT: self._validate_row_count,
            ValidationType.CHECKSUM: self._validate_checksum,
            ValidationType.DATA_TYPE: self._validate_data_types,
            ValidationType.NULL_CONSTRAINT: self._validate_null_constraints,
            ValidationType.UNIQUE_CONSTRAINT: self._validate_unique_constraints,
            ValidationType.FOREIGN_KEY: self._validate_foreign_keys,
            ValidationType.RANGE_CHECK: self._validate_range_checks,
            ValidationType.PATTERN_MATCH: self._validate_pattern_matches,
            ValidationType.BUSINESS_RULE: self._validate_business_rules,
            ValidationType.CUSTOM_SQL: self._validate_custom_sql,
            ValidationType.PERFORMANCE: self._validate_performance,
        }

    def _load_performance_thresholds(self) -> Dict[str, float]:
        """Load performance validation thresholds"""
        return {
            "max_validation_time_seconds": 300,  # 5 minutes per table
            "max_row_count_diff_percentage": 0.01,  # 1%
            "max_null_percentage": 0.05,  # 5%
            "max_duplicate_percentage": 0.001,  # 0.1%
            "max_query_time_seconds": 30,  # 30 seconds per query
        }

    async def validate_migration(self, migration_id: str, source_connector, target_connector,
                               validation_rules: List[ValidationRule],
                               tables: List[str] = None) -> MigrationValidationReport:
        """Perform comprehensive migration validation"""
        logger.info(f"Starting migration validation for {migration_id}")

        report = MigrationValidationReport(
            migration_id=migration_id,
            source_database=getattr(source_connector, 'database', 'unknown'),
            target_database=getattr(target_connector, 'database', 'unknown'),
            start_time=datetime.now(timezone.utc),
            total_tables=len(tables) if tables else 0,
            total_rules=len(validation_rules)
        )

        try:
            # Get table list if not provided
            if not tables:
                tables = await self._get_table_list(source_connector, target_connector)

            # Validate each table
            for table_name in tables:
                table_result = await self._validate_table(
                    table_name, source_connector, target_connector, validation_rules
                )
                report.table_results[table_name] = table_result

                # Update counters
                report.total_rules += table_result.total_rules

            # Generate summary and recommendations
            await self._generate_summary(report)
            await self._generate_recommendations(report)

            report.end_time = datetime.now(timezone.utc)
            duration = (report.end_time - report.start_time).total_seconds()

            # Determine overall status
            if any(result.critical_issues for result in report.table_results.values()):
                report.overall_status = "CRITICAL_ISSUES"
            elif any(result.errors for result in report.table_results.values()):
                report.overall_status = "FAILED"
            else:
                report.overall_status = "PASSED"

            logger.info(f"Migration validation completed in {duration:.2f}s: {report.overall_status}")
            return report

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            report.overall_status = "ERROR"
            report.end_time = datetime.now(timezone.utc)
            return report

    async def _get_table_list(self, source_connector, target_connector) -> List[str]:
        """Get list of tables to validate"""
        try:
            # Get tables from source database
            source_tables = await self._get_tables_from_connector(source_connector)
            target_tables = await self._get_tables_from_connector(target_connector)

            # Return intersection of tables
            common_tables = set(source_tables) & set(target_tables)
            return list(common_tables)

        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []

    async def _get_tables_from_connector(self, connector) -> List[str]:
        """Get table list from database connector"""
        try:
            if hasattr(connector, 'get_table_list'):
                return await connector.get_table_list()

            # Fallback: try common information schema queries
            if hasattr(connector, 'connection'):
                if hasattr(connector.connection, 'fetch'):  # asyncpg
                    query = """
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    """
                    result = await connector.connection.fetch(query)
                    return [row['table_name'] for row in result]

            return []

        except Exception as e:
            logger.warning(f"Failed to get tables from connector: {e}")
            return []

    async def _validate_table(self, table_name: str, source_connector, target_connector,
                            validation_rules: List[ValidationRule]) -> TableValidationResult:
        """Validate a single table"""
        start_time = datetime.now(timezone.utc)

        table_result = TableValidationResult(
            table_name=table_name,
            total_rules=0,
            passed_rules=0,
            failed_rules=0,
            skipped_rules=0
        )

        # Filter rules for this table
        table_rules = [rule for rule in validation_rules if rule.table is None or rule.table == table_name]

        logger.info(f"Validating table {table_name} with {len(table_rules)} rules")

        try:
            for rule in table_rules:
                if not rule.enabled:
                    table_result.skipped_rules += 1
                    continue

                table_result.total_rules += 1

                try:
                    validation_result = await self._execute_validation_rule(
                        rule, table_name, source_connector, target_connector
                    )

                    # Categorize result
                    if validation_result.status == "PASSED":
                        table_result.passed_rules += 1
                    elif validation_result.status == "FAILED":
                        table_result.failed_rules += 1

                        if validation_result.level == ValidationLevel.CRITICAL:
                            table_result.critical_issues.append(validation_result)
                        elif validation_result.level == ValidationLevel.ERROR:
                            table_result.errors.append(validation_result)
                        elif validation_result.level == ValidationLevel.WARNING:
                            table_result.warnings.append(validation_result)

                except Exception as e:
                    logger.error(f"Validation rule {rule.name} failed: {e}")
                    error_result = ValidationResult(
                        rule_name=rule.name,
                        status="FAILED",
                        level=ValidationLevel.ERROR,
                        message=f"Validation execution failed: {str(e)}"
                    )
                    table_result.failed_rules += 1
                    table_result.errors.append(error_result)

        except Exception as e:
            logger.error(f"Table validation failed for {table_name}: {e}")
            table_result.failed_rules = table_result.total_rules

        finally:
            end_time = datetime.now(timezone.utc)
            table_result.execution_time_seconds = (end_time - start_time).total_seconds()

        logger.info(f"Table {table_name} validation completed: "
                   f"{table_result.passed_rules}/{table_result.total_rules} passed")

        return table_result

    async def _execute_validation_rule(self, rule: ValidationRule, table_name: str,
                                     source_connector, target_connector) -> ValidationResult:
        """Execute a single validation rule"""
        validation_func = self.validation_functions.get(rule.type)
        if not validation_func:
            return ValidationResult(
                rule_name=rule.name,
                status="SKIPPED",
                level=ValidationLevel.WARNING,
                message=f"Unknown validation type: {rule.type}"
            )

        return await validation_func(rule, table_name, source_connector, target_connector)

    # Validation implementations
    async def _validate_row_count(self, rule: ValidationRule, table_name: str,
                                source_connector, target_connector) -> ValidationResult:
        """Validate row count consistency"""
        try:
            source_count = await source_connector.get_row_count(table_name)
            target_count = await target_connector.get_row_count(table_name)

            tolerance = rule.parameters.get("tolerance", self.performance_thresholds["max_row_count_diff_percentage"])
            max_diff = int(source_count * tolerance)

            diff = abs(source_count - target_count)
            passed = diff <= max_diff

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Row count difference: {diff} (tolerance: {max_diff})",
                expected_value=source_count,
                actual_value=target_count,
                details={
                    "source_count": source_count,
                    "target_count": target_count,
                    "difference": diff,
                    "tolerance": max_diff,
                    "percentage_diff": (diff / source_count * 100) if source_count > 0 else 0
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Row count validation failed: {str(e)}"
            )

    async def _validate_checksum(self, rule: ValidationRule, table_name: str,
                               source_connector, target_connector) -> ValidationResult:
        """Validate data integrity using checksums"""
        try:
            algorithm = rule.parameters.get("algorithm", "md5")
            columns = rule.parameters.get("columns", ["id"])

            if algorithm not in self.checksum_algorithms:
                raise ValueError(f"Unsupported checksum algorithm: {algorithm}")

            # Get checksums from both databases
            source_checksum = await self._calculate_table_checksum(
                source_connector, table_name, columns, algorithm
            )
            target_checksum = await self._calculate_table_checksum(
                target_connector, table_name, columns, algorithm
            )

            passed = source_checksum == target_checksum

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Checksum {algorithm} {'match' if passed else 'mismatch'}",
                expected_value=source_checksum,
                actual_value=target_checksum,
                details={
                    "algorithm": algorithm,
                    "columns": columns,
                    "source_checksum": source_checksum,
                    "target_checksum": target_checksum
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Checksum validation failed: {str(e)}"
            )

    async def _calculate_table_checksum(self, connector, table_name: str,
                                      columns: List[str], algorithm: str) -> str:
        """Calculate checksum for table data"""
        try:
            # Get all data sorted by key columns
            columns_str = ", ".join(columns)
            order_by_str = ", ".join(columns)

            query = f"SELECT {columns_str} FROM {table_name} ORDER BY {order_by_str}"
            data = await connector.execute_query(query)

            # Calculate checksum
            hash_func = self.checksum_algorithms[algorithm]()
            for row in data:
                # Create deterministic string representation
                row_str = json.dumps(row, sort_keys=True, default=str)
                hash_func.update(row_str.encode('utf-8'))

            return hash_func.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate checksum for {table_name}: {e}")
            raise

    async def _validate_data_types(self, rule: ValidationRule, table_name: str,
                                 source_connector, target_connector) -> ValidationResult:
        """Validate data type consistency"""
        try:
            # Get schema information from both databases
            source_schema = await source_connector.get_table_info(table_name)
            target_schema = await target_connector.get_table_info(table_name)

            source_columns = {col['column_name']: col for col in source_schema.get('columns', [])}
            target_columns = {col['column_name']: col for col in target_schema.get('columns', [])}

            issues = []

            # Check each column
            for column_name in source_columns:
                if column_name not in target_columns:
                    issues.append(f"Column {column_name} missing in target")
                    continue

                source_col = source_columns[column_name]
                target_col = target_columns[column_name]

                # Compare data types (simplified)
                if source_col['data_type'] != target_col['data_type']:
                    issues.append(f"Column {column_name} type mismatch: "
                                f"{source_col['data_type']} -> {target_col['data_type']}")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Data type validation: {len(issues)} issues found",
                details={
                    "source_columns": len(source_columns),
                    "target_columns": len(target_columns),
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Data type validation failed: {str(e)}"
            )

    async def _validate_null_constraints(self, rule: ValidationRule, table_name: str,
                                       source_connector, target_connector) -> ValidationResult:
        """Validate NOT NULL constraints"""
        try:
            # Get columns that should not be null
            non_nullable_columns = rule.parameters.get("columns", [])

            if not non_nullable_columns:
                # Auto-detect from schema
                schema = await source_connector.get_table_info(table_name)
                non_nullable_columns = [
                    col['column_name'] for col in schema.get('columns', [])
                    if col.get('is_nullable') == 'NO'
                ]

            issues = []

            for column in non_nullable_columns:
                # Check null counts
                source_nulls = await self._count_null_values(source_connector, table_name, column)
                target_nulls = await self._count_null_values(target_connector, table_name, column)

                if source_nulls != target_nulls:
                    issues.append(f"Column {column}: source nulls={source_nulls}, target nulls={target_nulls}")
                elif target_nulls > 0:
                    issues.append(f"Column {column}: {target_nulls} null values found")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"NULL constraint validation: {len(issues)} issues found",
                details={
                    "validated_columns": non_nullable_columns,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"NULL constraint validation failed: {str(e)}"
            )

    async def _count_null_values(self, connector, table_name: str, column: str) -> int:
        """Count null values in a column"""
        query = f"SELECT COUNT(*) as null_count FROM {table_name} WHERE {column} IS NULL"
        result = await connector.execute_query(query)
        return result[0]['null_count'] if result else 0

    async def _validate_unique_constraints(self, rule: ValidationRule, table_name: str,
                                         source_connector, target_connector) -> ValidationResult:
        """Validate unique constraints"""
        try:
            unique_columns = rule.parameters.get("columns", [])

            if not unique_columns:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No unique columns specified for validation"
                )

            issues = []

            for column_set in unique_columns:
                if isinstance(column_set, str):
                    column_set = [column_set]

                # Check duplicate counts
                source_duplicates = await self._count_duplicates(
                    source_connector, table_name, column_set
                )
                target_duplicates = await self._count_duplicates(
                    target_connector, table_name, column_set
                )

                if source_duplicates != target_duplicates:
                    issues.append(f"Columns {column_set}: "
                                f"source duplicates={source_duplicates}, target duplicates={target_duplicates}")
                elif target_duplicates > 0:
                    issues.append(f"Columns {column_set}: {target_duplicates} duplicates found")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Unique constraint validation: {len(issues)} issues found",
                details={
                    "validated_column_sets": unique_columns,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Unique constraint validation failed: {str(e)}"
            )

    async def _count_duplicates(self, connector, table_name: str, columns: List[str]) -> int:
        """Count duplicate values for a set of columns"""
        columns_str = ", ".join(columns)
        query = f"""
            SELECT COUNT(*) - COUNT(DISTINCT {columns_str}) as duplicate_count
            FROM {table_name}
        """
        result = await connector.execute_query(query)
        return result[0]['duplicate_count'] if result else 0

    async def _validate_foreign_keys(self, rule: ValidationRule, table_name: str,
                                   source_connector, target_connector) -> ValidationResult:
        """Validate foreign key constraints"""
        try:
            fk_definitions = rule.parameters.get("foreign_keys", [])

            if not fk_definitions:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No foreign keys specified for validation"
                )

            issues = []

            for fk in fk_definitions:
                fk_column = fk["column"]
                referenced_table = fk["referenced_table"]
                referenced_column = fk.get("referenced_column", "id")

                # Check orphaned records
                orphaned_count = await self._count_orphaned_records(
                    target_connector, table_name, fk_column,
                    referenced_table, referenced_column
                )

                if orphaned_count > 0:
                    issues.append(f"Foreign key {fk_column} -> {referenced_table}.{referenced_column}: "
                                f"{orphaned_count} orphaned records")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Foreign key validation: {len(issues)} issues found",
                details={
                    "validated_foreign_keys": fk_definitions,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Foreign key validation failed: {str(e)}"
            )

    async def _count_orphaned_records(self, connector, table_name: str, fk_column: str,
                                    referenced_table: str, referenced_column: str) -> int:
        """Count orphaned records (records with invalid foreign keys)"""
        query = f"""
            SELECT COUNT(*) as orphaned_count
            FROM {table_name} t
            LEFT JOIN {referenced_table} r ON t.{fk_column} = r.{referenced_column}
            WHERE r.{referenced_column} IS NULL AND t.{fk_column} IS NOT NULL
        """
        result = await connector.execute_query(query)
        return result[0]['orphaned_count'] if result else 0

    async def _validate_range_checks(self, rule: ValidationRule, table_name: str,
                                   source_connector, target_connector) -> ValidationResult:
        """Validate value ranges"""
        try:
            range_checks = rule.parameters.get("ranges", {})

            if not range_checks:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No range checks specified"
                )

            issues = []

            for column, range_def in range_checks.items():
                min_val = range_def.get("min")
                max_val = range_def.get("max")

                if min_val is not None:
                    violations = await self._count_range_violations(
                        target_connector, table_name, column, min_val, "less_than"
                    )
                    if violations > 0:
                        issues.append(f"Column {column}: {violations} values < {min_val}")

                if max_val is not None:
                    violations = await self._count_range_violations(
                        target_connector, table_name, column, max_val, "greater_than"
                    )
                    if violations > 0:
                        issues.append(f"Column {column}: {violations} values > {max_val}")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Range check validation: {len(issues)} issues found",
                details={
                    "validated_ranges": range_checks,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Range check validation failed: {str(e)}"
            )

    async def _count_range_violations(self, connector, table_name: str, column: str,
                                    threshold: float, comparison: str) -> int:
        """Count values that violate range constraints"""
        if comparison == "less_than":
            query = f"SELECT COUNT(*) as violation_count FROM {table_name} WHERE {column} < {threshold}"
        else:  # greater_than
            query = f"SELECT COUNT(*) as violation_count FROM {table_name} WHERE {column} > {threshold}"

        result = await connector.execute_query(query)
        return result[0]['violation_count'] if result else 0

    async def _validate_pattern_matches(self, rule: ValidationRule, table_name: str,
                                      source_connector, target_connector) -> ValidationResult:
        """Validate pattern matches (regex, email, phone, etc.)"""
        try:
            pattern_checks = rule.parameters.get("patterns", {})

            if not pattern_checks:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No pattern checks specified"
                )

            issues = []

            for column, pattern_def in pattern_checks.items():
                pattern = pattern_def.get("pattern")
                pattern_type = pattern_def.get("type", "regex")

                if pattern_type == "regex":
                    violations = await self._count_pattern_violations(
                        target_connector, table_name, column, pattern
                    )
                    if violations > 0:
                        issues.append(f"Column {column}: {violations} values don't match pattern {pattern}")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Pattern validation: {len(issues)} issues found",
                details={
                    "validated_patterns": pattern_checks,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Pattern validation failed: {str(e)}"
            )

    async def _count_pattern_violations(self, connector, table_name: str,
                                      column: str, pattern: str) -> int:
        """Count values that don't match the pattern"""
        query = f"""
            SELECT COUNT(*) as violation_count
            FROM {table_name}
            WHERE {column} IS NOT NULL AND {column} !~ '{pattern}'
        """
        result = await connector.execute_query(query)
        return result[0]['violation_count'] if result else 0

    async def _validate_business_rules(self, rule: ValidationRule, table_name: str,
                                     source_connector, target_connector) -> ValidationResult:
        """Validate custom business rules"""
        try:
            business_rules = rule.parameters.get("rules", [])

            if not business_rules:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No business rules specified"
                )

            issues = []

            for business_rule in business_rules:
                rule_name = business_rule.get("name", "unnamed")
                sql_query = business_rule.get("query")
                expected_result = business_rule.get("expected_result", 0)

                if not sql_query:
                    continue

                try:
                    result = await target_connector.execute_query(sql_query)
                    actual_result = result[0]['count'] if result else 0

                    if actual_result != expected_result:
                        issues.append(f"Rule {rule_name}: expected {expected_result}, got {actual_result}")

                except Exception as e:
                    issues.append(f"Rule {rule_name}: query failed - {str(e)}")

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Business rule validation: {len(issues)} issues found",
                details={
                    "validated_rules": [rule.get("name", "unnamed") for rule in business_rules],
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Business rule validation failed: {str(e)}"
            )

    async def _validate_custom_sql(self, rule: ValidationRule, table_name: str,
                                 source_connector, target_connector) -> ValidationResult:
        """Validate using custom SQL queries"""
        try:
            sql_query = rule.sql_query or rule.parameters.get("query")
            expected_result = rule.expected_result or rule.parameters.get("expected_result")

            if not sql_query:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No SQL query specified"
                )

            # Execute query on both databases
            source_result = await source_connector.execute_query(sql_query)
            target_result = await target_connector.execute_query(sql_query)

            # Compare results
            source_value = source_result[0]['result'] if source_result else None
            target_value = target_result[0]['result'] if target_result else None

            if expected_result is not None:
                source_passed = source_value == expected_result
                target_passed = target_value == expected_result
                passed = source_passed and target_passed
            else:
                passed = source_value == target_value

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Custom SQL validation: {'passed' if passed else 'failed'}",
                expected_value=expected_result or source_value,
                actual_value=target_value,
                details={
                    "query": sql_query,
                    "source_result": source_value,
                    "target_result": target_value,
                    "expected_result": expected_result
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Custom SQL validation failed: {str(e)}"
            )

    async def _validate_performance(self, rule: ValidationRule, table_name: str,
                                  source_connector, target_connector) -> ValidationResult:
        """Validate performance metrics"""
        try:
            performance_checks = rule.parameters.get("checks", {})

            if not performance_checks:
                return ValidationResult(
                    rule_name=rule.name,
                    status="SKIPPED",
                    level=ValidationLevel.INFO,
                    message="No performance checks specified"
                )

            issues = []

            # Check query performance
            if "max_query_time" in performance_checks:
                query = performance_checks.get("test_query", f"SELECT COUNT(*) FROM {table_name}")
                max_time = performance_checks["max_query_time"]

                start_time = datetime.now()
                await target_connector.execute_query(query)
                query_time = (datetime.now() - start_time).total_seconds()

                if query_time > max_time:
                    issues.append(f"Query time {query_time:.2f}s exceeds limit {max_time}s")

            # Check table size
            if "max_table_size_mb" in performance_checks:
                # This would require additional logic to calculate table size
                pass

            passed = len(issues) == 0

            return ValidationResult(
                rule_name=rule.name,
                status="PASSED" if passed else "FAILED",
                level=rule.level,
                message=f"Performance validation: {len(issues)} issues found",
                details={
                    "performance_checks": performance_checks,
                    "issues": issues
                }
            )

        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                status="FAILED",
                level=ValidationLevel.ERROR,
                message=f"Performance validation failed: {str(e)}"
            )

    async def _generate_summary(self, report: MigrationValidationReport):
        """Generate validation summary"""
        total_rules = sum(result.total_rules for result in report.table_results.values())
        total_passed = sum(result.passed_rules for result in report.table_results.values())
        total_failed = sum(result.failed_rules for result in report.table_results.values())
        total_skipped = sum(result.skipped_rules for result in report.table_results.values())

        total_critical = sum(len(result.critical_issues) for result in report.table_results.values())
        total_errors = sum(len(result.errors) for result in report.table_results.values())
        total_warnings = sum(len(result.warnings) for result in report.table_results.values())

        total_execution_time = sum(result.execution_time_seconds for result in report.table_results.values())

        report.summary = {
            "total_rules": total_rules,
            "passed_rules": total_passed,
            "failed_rules": total_failed,
            "skipped_rules": total_skipped,
            "critical_issues": total_critical,
            "error_issues": total_errors,
            "warning_issues": total_warnings,
            "success_rate": (total_passed / total_rules * 100) if total_rules > 0 else 0,
            "total_execution_time_seconds": total_execution_time,
            "average_execution_time_per_table": (
                total_execution_time / len(report.table_results) if report.table_results else 0
            )
        }

    async def _generate_recommendations(self, report: MigrationValidationReport):
        """Generate recommendations based on validation results"""
        recommendations = []

        # Check for critical issues
        critical_count = sum(len(result.critical_issues) for result in report.table_results.values())
        if critical_count > 0:
            recommendations.append(
                f"URGENT: {critical_count} critical issues found. Address these before proceeding."
            )

        # Check for failed rules
        error_count = sum(len(result.errors) for result in report.table_results.values())
        if error_count > 0:
            recommendations.append(
                f"{error_count} validation errors detected. Review and fix these issues."
            )

        # Check for performance issues
        slow_tables = [
            table_name for table_name, result in report.table_results.items()
            if result.execution_time_seconds > self.performance_thresholds["max_validation_time_seconds"]
        ]
        if slow_tables:
            recommendations.append(
                f"Consider optimizing validation for slow tables: {', '.join(slow_tables)}"
            )

        # Check data consistency
        row_count_issues = []
        for table_name, result in report.table_results.items():
            for error in result.errors:
                if "row count" in error.message.lower():
                    row_count_issues.append(table_name)
                    break

        if row_count_issues:
            recommendations.append(
                f"Row count mismatches detected in tables: {', '.join(row_count_issues)}"
            )

        # Add positive recommendations if validation passed
        if report.overall_status == "PASSED":
            recommendations.append(
                "All validations passed successfully. Migration data integrity confirmed."
            )

        report.recommendations = recommendations

    def create_default_validation_rules(self, table_name: str = None) -> List[ValidationRule]:
        """Create default validation rules for common scenarios"""
        rules = [
            ValidationRule(
                name="row_count_check",
                type=ValidationType.ROW_COUNT,
                description="Verify row count consistency between source and target",
                level=ValidationLevel.ERROR,
                table=table_name,
                parameters={"tolerance": 0.01}
            ),
            ValidationRule(
                name="checksum_validation",
                type=ValidationType.CHECKSUM,
                description="Verify data integrity using checksums",
                level=ValidationLevel.ERROR,
                table=table_name,
                parameters={"algorithm": "md5", "columns": ["id"]}
            ),
            ValidationRule(
                name="null_constraint_check",
                type=ValidationType.NULL_CONSTRAINT,
                description="Verify NOT NULL constraints",
                level=ValidationLevel.ERROR,
                table=table_name
            ),
            ValidationRule(
                name="unique_constraint_check",
                type=ValidationType.UNIQUE_CONSTRAINT,
                description="Verify unique constraints",
                level=ValidationLevel.ERROR,
                table=table_name,
                parameters={"columns": [["id"]]}
            ),
            ValidationRule(
                name="data_type_validation",
                type=ValidationType.DATA_TYPE,
                description="Verify data type consistency",
                level=ValidationLevel.WARNING,
                table=table_name
            )
        ]

        # Add table-specific rules
        if table_name:
            if "characters" in table_name:
                rules.extend([
                    ValidationRule(
                        name="character_level_range",
                        type=ValidationType.RANGE_CHECK,
                        description="Verify character level is in valid range",
                        level=ValidationLevel.ERROR,
                        table=table_name,
                        parameters={
                            "ranges": {
                                "level": {"min": 1, "max": 20}
                            }
                        }
                    )
                ])
            elif "users" in table_name:
                rules.extend([
                    ValidationRule(
                        name="email_format_check",
                        type=ValidationType.PATTERN_MATCH,
                        description="Verify email format",
                        level=ValidationLevel.ERROR,
                        table=table_name,
                        parameters={
                            "patterns": {
                                "email": {"pattern": "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"}
                            }
                        }
                    )
                ])

        return rules

    def export_report(self, report: MigrationValidationReport, format: str = "json") -> str:
        """Export validation report in specified format"""
        if format.lower() == "json":
            return self._export_json_report(report)
        elif format.lower() == "html":
            return self._export_html_report(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json_report(self, report: MigrationValidationReport) -> str:
        """Export report as JSON"""
        # Convert dataclasses to dictionaries
        report_dict = {
            "migration_id": report.migration_id,
            "source_database": report.source_database,
            "target_database": report.target_database,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat() if report.end_time else None,
            "total_tables": report.total_tables,
            "total_rules": report.total_rules,
            "overall_status": report.overall_status,
            "summary": report.summary,
            "recommendations": report.recommendations,
            "table_results": {}
        }

        for table_name, result in report.table_results.items():
            report_dict["table_results"][table_name] = {
                "table_name": result.table_name,
                "total_rules": result.total_rules,
                "passed_rules": result.passed_rules,
                "failed_rules": result.failed_rules,
                "skipped_rules": result.skipped_rules,
                "execution_time_seconds": result.execution_time_seconds,
                "critical_issues": [
                    {
                        "rule_name": issue.rule_name,
                        "status": issue.status,
                        "level": issue.level.value,
                        "message": issue.message,
                        "details": issue.details
                    } for issue in result.critical_issues
                ],
                "errors": [
                    {
                        "rule_name": error.rule_name,
                        "status": error.status,
                        "level": error.level.value,
                        "message": error.message,
                        "details": error.details
                    } for error in result.errors
                ],
                "warnings": [
                    {
                        "rule_name": warning.rule_name,
                        "status": warning.status,
                        "level": warning.level.value,
                        "message": warning.message,
                        "details": warning.details
                    } for warning in result.warnings
                ]
            }

        return json.dumps(report_dict, indent=2)

    def _export_html_report(self, report: MigrationValidationReport) -> str:
        """Export report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Migration Validation Report - {report.migration_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .table-result {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
                .table-header {{ background-color: #e8e8e8; padding: 15px; font-weight: bold; }}
                .table-content {{ padding: 15px; }}
                .issue {{ margin: 5px 0; padding: 5px; border-radius: 3px; }}
                .critical {{ background-color: #ffebee; color: #c62828; }}
                .error {{ background-color: #fff3e0; color: #ef6c00; }}
                .warning {{ background-color: #fff8e1; color: #f57f17; }}
                .passed {{ background-color: #e8f5e8; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Migration Validation Report</h1>
                <p><strong>Migration ID:</strong> {report.migration_id}</p>
                <p><strong>Source Database:</strong> {report.source_database}</p>
                <p><strong>Target Database:</strong> {report.target_database}</p>
                <p><strong>Status:</strong> {report.overall_status}</p>
                <p><strong>Generated:</strong> {report.end_time or datetime.now(timezone.utc)}</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Tables:</strong> {report.total_tables}</p>
                <p><strong>Total Rules:</strong> {report.summary.get('total_rules', 0)}</p>
                <p><strong>Passed:</strong> {report.summary.get('passed_rules', 0)}</p>
                <p><strong>Failed:</strong> {report.summary.get('failed_rules', 0)}</p>
                <p><strong>Success Rate:</strong> {report.summary.get('success_rate', 0):.1f}%</p>
            </div>

            <div>
                <h2>Recommendations</h2>
                <ul>
        """

        for recommendation in report.recommendations:
            html += f"                    <li>{recommendation}</li>\n"

        html += """
                </ul>
            </div>

            <div>
                <h2>Table Results</h2>
        """

        for table_name, result in report.table_results.items():
            status_class = "passed" if result.failed_rules == 0 else "error" if not result.critical_issues else "critical"

            html += f"""
                <div class="table-result">
                    <div class="table-header {status_class}">
                        {table_name} - {result.passed_rules}/{result.total_rules} rules passed
                    </div>
                    <div class="table-content">
                        <p><strong>Execution Time:</strong> {result.execution_time_seconds:.2f}s</p>
            """

            # Critical issues
            if result.critical_issues:
                html += "<h3>Critical Issues</h3>\n"
                for issue in result.critical_issues:
                    html += f'<div class="issue critical">{issue.message}</div>\n'

            # Errors
            if result.errors:
                html += "<h3>Errors</h3>\n"
                for error in result.errors:
                    html += f'<div class="issue error">{error.message}</div>\n'

            # Warnings
            if result.warnings:
                html += "<h3>Warnings</h3>\n"
                for warning in result.warnings:
                    html += f'<div class="issue warning">{warning.message}</div>\n'

            html += """
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

# Example usage
async def test_data_validator():
    """Test data validation"""
    # This would require actual database connectors to test
    validator = DataValidator()

    # Create sample validation rules
    rules = validator.create_default_validation_rules("characters")

    print(f"Created {len(rules)} validation rules for characters table:")
    for rule in rules:
        print(f"  - {rule.name}: {rule.description}")

    # Test report export
    sample_report = MigrationValidationReport(
        migration_id="test_migration",
        source_database="source_db",
        target_database="target_db",
        start_time=datetime.now(timezone.utc),
        total_tables=1,
        total_rules=len(rules),
        overall_status="PASSED"
    )

    # Export to JSON
    json_report = validator.export_report(sample_report, "json")
    print(f"\nJSON Report Length: {len(json_report)} characters")

    # Export to HTML
    html_report = validator.export_report(sample_report, "html")
    print(f"HTML Report Length: {len(html_report)} characters")

if __name__ == "__main__":
    asyncio.run(test_data_validator())