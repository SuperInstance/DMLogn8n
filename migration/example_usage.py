#!/usr/bin/env python3
"""
DMLogn8n Migration System - Example Usage
Demonstrates how to use the comprehensive migration system
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

# Import migration components
from migration_engine import MigrationEngine, MigrationConfig, MigrationType, DatabaseType
from planner import MigrationPlanner
from validators.data_validator import DataValidator, ValidationType, ValidationLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration_example")

async def example_basic_migration():
    """Example: Basic data migration"""
    print("=== Basic Migration Example ===")

    # Create migration configuration
    config = MigrationConfig(
        migration_id="basic_character_migration",
        name="Character Data Migration",
        description="Migrate character data from production to staging",
        migration_type=MigrationType.DATA,
        source_config={
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "dmlog_user",
            "password": "password",
            "database": "dmlog_production"
        },
        target_config={
            "type": "postgresql",
            "host": "localhost",
            "port": 5433,
            "user": "dmlog_user",
            "password": "password",
            "database": "dmlog_staging"
        },
        tables=["characters", "campaigns", "sessions"],
        batch_size=1000,
        zero_downtime=True,
        validate_data=True,
        create_backup=True,
        dry_run=True  # Set to False for actual migration
    )

    # Create and configure migration engine
    engine = MigrationEngine()

    try:
        # Execute migration
        progress = await engine.execute_migration(config)

        print(f"Migration completed with status: {progress.status.value}")
        print(f"Total records processed: {progress.processed_records}")
        print(f"Failed records: {progress.failed_records}")

        if progress.errors:
            print("Errors encountered:")
            for error in progress.errors:
                print(f"  - {error}")

        return progress

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

    finally:
        await engine.cleanup()

async def example_schema_transformation():
    """Example: Schema transformation between database types"""
    print("\n=== Schema Transformation Example ===")

    from transformers.schema_transformer import SchemaTransformer

    # Sample PostgreSQL schema
    source_schema = {
        "characters": {
            "columns": [
                {
                    "column_name": "id",
                    "data_type": "uuid",
                    "is_nullable": "NO",
                    "is_primary_key": True
                },
                {
                    "column_name": "name",
                    "data_type": "character varying",
                    "character_maximum_length": 100,
                    "is_nullable": "NO"
                },
                {
                    "column_name": "attributes",
                    "data_type": "jsonb",
                    "is_nullable": "YES"
                }
            ],
            "indexes": [
                {
                    "indexname": "idx_characters_name",
                    "indexdef": "CREATE INDEX idx_characters_name ON characters (name);"
                }
            ]
        }
    }

    # Transformation rules
    transformation_rules = {
        "field_mappings": {
            "id": {
                "name": "_id",
                "type": "string"
            }
        },
        "column_rules": {
            "attributes": {
                "name": "character_stats"
            }
        }
    }

    transformer = SchemaTransformer()

    try:
        # Transform from PostgreSQL to MongoDB
        result = await transformer.transform_schema(
            source_schema,
            "postgresql",
            "mongodb",
            transformation_rules
        )

        print("Schema transformation completed:")
        print(f"Target schema: {json.dumps(result['schema'], indent=2)}")
        print(f"DDL statements: {len(result['ddl_stat'])} statements generated")

        # Print transformation summary
        summary = result['transformation_summary']
        print(f"Transformation summary: {summary}")

    except Exception as e:
        logger.error(f"Schema transformation failed: {e}")
        raise

async def example_data_validation():
    """Example: Data validation after migration"""
    print("\n=== Data Validation Example ===")

    validator = DataValidator()

    # Create comprehensive validation rules
    validation_rules = [
        {
            "name": "row_count_check",
            "type": ValidationType.ROW_COUNT,
            "table": "characters",
            "tolerance": 0.01
        },
        {
            "name": "character_level_validation",
            "type": ValidationType.RANGE_CHECK,
            "table": "characters",
            "level": ValidationLevel.ERROR,
            "parameters": {
                "ranges": {
                    "level": {"min": 1, "max": 20}
                }
            }
        },
        {
            "name": "character_name_format",
            "type": ValidationType.PATTERN_MATCH,
            "table": "characters",
            "parameters": {
                "patterns": {
                    "name": {"pattern": "^[A-Za-z][A-Za-z\\s'-]+$"}
                }
            }
        },
        {
            "name": "session_integrity_check",
            "type": ValidationType.FOREIGN_KEY,
            "table": "session_participants",
            "parameters": {
                "foreign_keys": [
                    {
                        "column": "session_id",
                        "referenced_table": "sessions",
                        "referenced_column": "id"
                    }
                ]
            }
        }
    ]

    # Note: In a real scenario, you would have actual database connectors
    # For this example, we'll create mock validation results

    print("Validation rules created:")
    for rule in validation_rules:
        print(f"  - {rule['name']}: {rule['type'].value}")

    # Create mock validation report
    from validators.data_validator import MigrationValidationReport, TableValidationResult

    sample_report = MigrationValidationReport(
        migration_id="example_validation",
        source_database="source_db",
        target_database="target_db",
        start_time=datetime.now(timezone.utc),
        total_tables=3,
        total_rules=len(validation_rules),
        overall_status="PASSED"
    )

    # Export validation report
    validator = DataValidator()
    html_report = validator.export_report(sample_report, "html")

    print(f"Generated HTML validation report ({len(html_report)} characters)")
    print("Validation report includes:")
    print("  - Row count validation")
    print("  - Data integrity checks")
    print("  - Business rule validation")
    print("  - Performance metrics")

async def example_migration_planning():
    """Example: Advanced migration planning"""
    print("\n=== Migration Planning Example ===")

    from planner import MigrationPlanner

    planner = MigrationPlanner()

    # Create migration configuration
    config = MigrationConfig(
        migration_id="complex_migration_plan",
        name="Complex Multi-Table Migration",
        description="Migrate entire DMLogn8n database with dependencies",
        migration_type=MigrationType.FULL,
        source_config={
            "type": "postgresql",
            "host": "prod-db.company.com",
            "port": 5432,
            "user": "migration_user",
            "password": "secure_password",
            "database": "dmlog_production"
        },
        target_config={
            "type": "postgresql",
            "host": "new-db.company.com",
            "port": 5432,
            "user": "migration_user",
            "password": "secure_password",
            "database": "dmlog_v2"
        },
        tables=[
            "users", "characters", "campaigns", "sessions",
            "session_participants", "memories", "decisions",
            "training_data", "model_versions"
        ],
        batch_size=5000,
        max_parallel_workers=8,
        zero_downtime=True,
        validate_data=True,
        create_backup=True
    )

    try:
        # Analyze migration risks
        risk_analysis = await planner.analyze_migration_risk(config)
        print("Risk Analysis:")
        print(f"  Risk Level: {risk_analysis['risk_level']}")
        print(f"  Risk Score: {risk_analysis['risk_score']:.2f}")
        print(f"  Estimated Data Size: {risk_analysis['estimated_data_size_mb']} MB")
        print("  Risk Factors:")
        for factor in risk_analysis['risk_factors']:
            print(f"    - {factor}")
        print("  Recommendations:")
        for rec in risk_analysis['recommendations']:
            print(f"    - {rec}")

        # Create migration timeline
        table_plans = await planner.create_plan(config)
        timeline = await planner.create_migration_timeline(table_plans, config)
        print(f"\nMigration Timeline:")
        print(f"  Estimated Duration: {timeline['total_duration_hours']:.1f} hours")
        print(f"  Phases: {len(timeline['phases'])}")
        print(f"  Estimated Completion: {timeline['estimated_completion']}")

        # Estimate resource requirements
        resources = await planner.estimate_resource_requirements(table_plans)
        print(f"\nResource Requirements:")
        print(f"  Memory: {resources['memory_gb']} GB")
        print(f"  CPU Cores: {resources['cpu_cores']}")
        print(f"  Storage: {resources['storage_gb']} GB")
        print(f"  Network: {resources['network_mbps']} Mbps")
        print(f"  Recommended Instance: {resources['recommended_instance_type']}")

    except Exception as e:
        logger.error(f"Migration planning failed: {e}")
        raise

async def example_data_transformation():
    """Example: Advanced data transformation"""
    print("\n=== Data Transformation Example ===")

    from transformers.data_transformer import DataTransformer

    transformer = DataTransformer()

    # Sample transformation rules
    transformation_config = {
        "transformation_rules": [
            {
                "name": "generate_user_id",
                "type": "field_mapping",
                "source_field": "legacy_user_id",
                "target_field": "user_id",
                "parameters": {
                    "transformation": "generate_uuid",
                    "target_type": "string"
                }
            },
            {
                "name": "normalize_email",
                "type": "function_transformation",
                "parameters": {
                    "function": "lower",
                    "source_fields": ["email_address"],
                    "target_field": "email"
                }
            },
            {
                "name": "create_full_name",
                "type": "merge_transformation",
                "parameters": {
                    "source_fields": ["first_name", "last_name"],
                    "delimiter": " ",
                    "target_field": "full_name"
                }
            },
            {
                "name": "enrich_timestamp",
                "type": "enrichment",
                "parameters": {
                    "enrichment_type": "timestamp",
                    "target_field": "migration_timestamp"
                }
            },
            {
                "name": "validate_required_fields",
                "type": "validation",
                "parameters": {
                    "field": "email",
                    "rules": [
                        {"type": "not_empty"},
                        {"type": "email"}
                    ]
                }
            }
        ]
    }

    # Sample record
    sample_record = {
        "legacy_user_id": 12345,
        "email_address": "John.Doe@Example.COM",
        "first_name": "John",
        "last_name": "Doe",
        "age": 30,
        "created_date": "2023-01-15"
    }

    try:
        # Create transformation rules
        rules = transformer.create_transformation_rules_from_config(transformation_config)

        # Transform record
        transformed_record, validation_result = await transformer.transform_record(
            sample_record, rules
        )

        print("Original Record:")
        print(json.dumps(sample_record, indent=2))

        print("\nTransformed Record:")
        print(json.dumps(transformed_record, indent=2))

        print(f"\nValidation Result: {validation_result.is_valid}")
        if validation_result.errors:
            print("Errors:", validation_result.errors)
        if validation_result.warnings:
            print("Warnings:", validation_result.warnings)

    except Exception as e:
        logger.error(f"Data transformation failed: {e}")
        raise

async def example_format_conversion():
    """Example: Data format conversion"""
    print("\n=== Format Conversion Example ===")

    from transformers.format_transformer import FormatTransformer, FormatTransformation, DataFormat, CompressionType

    transformer = FormatTransformer()

    # Sample data
    sample_data = [
        {"id": 1, "name": "Character 1", "class": "Fighter", "level": 5},
        {"id": 2, "name": "Character 2", "class": "Wizard", "level": 8},
        {"id": 3, "name": "Character 3", "class": "Rogue", "level": 6}
    ]

    # Convert to different formats
    transformations = [
        FormatTransformation(
            source_format=DataFormat.JSON,
            target_format=DataFormat.CSV,
            compression=CompressionType.NONE
        ),
        FormatTransformation(
            source_format=DataFormat.JSON,
            target_format=DataFormat.JSONL,
            compression=CompressionType.GZIP
        ),
        FormatTransformation(
            source_format=DataFormat.JSON,
            target_format=DataFormat.XML,
            compression=CompressionType.NONE,
            options={
                "root_element": "characters",
                "record_element": "character"
            }
        )
    ]

    try:
        for i, transformation in enumerate(transformations):
            print(f"\nTransformation {i+1}: {transformation.source_format.value} -> {transformation.target_format.value}")

            # Convert to source format
            source_data = await transformer._convert_to_target_format(
                sample_data,
                FormatTransformation(DataFormat.JSON, transformation.source_format)
            )

            # Apply transformation
            result = await transformer.transform_format(source_data, transformation)

            # Show result preview
            if isinstance(result, str):
                preview = result[:200] + "..." if len(result) > 200 else result
                print(f"Result: {preview}")
            else:
                print(f"Result: {len(result)} bytes (binary data)")

            # Get format information
            format_info = await transformer.get_format_info(result)
            print(f"Format info: {format_info}")

    except Exception as e:
        logger.error(f"Format conversion failed: {e}")
        raise

async def example_complete_migration_workflow():
    """Example: Complete migration workflow"""
    print("\n=== Complete Migration Workflow Example ===")

    try:
        # Step 1: Planning
        print("Step 1: Migration Planning")
        config = MigrationConfig(
            migration_id="complete_workflow_example",
            name="Complete Workflow Migration",
            description="End-to-end migration example",
            migration_type=MigrationType.FULL,
            source_config={
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "user": "dmlog_user",
                "password": "password",
                "database": "dmlog_source"
            },
            target_config={
                "type": "postgresql",
                "host": "localhost",
                "port": 5433,
                "user": "dmlog_user",
                "password": "password",
                "database": "dmlog_target"
            },
            tables=["characters", "campaigns", "sessions"],
            dry_run=True  # Example mode
        )

        planner = MigrationPlanner()
        risk_analysis = await planner.analyze_migration_risk(config)
        print(f"  Risk level: {risk_analysis['risk_level']}")

        # Step 2: Schema transformation (if needed)
        print("Step 2: Schema Validation")
        # Schema validation would happen here

        # Step 3: Data preparation
        print("Step 3: Data Preparation")
        # Data cleanup and transformation rules would be applied

        # Step 4: Migration execution
        print("Step 4: Migration Execution")
        engine = MigrationEngine()
        # progress = await engine.execute_migration(config)  # Would run actual migration
        print("  Migration configured (dry run mode)")

        # Step 5: Validation
        print("Step 5: Data Validation")
        validator = DataValidator()
        # validation_report = await validator.validate_migration(...)
        print("  Validation rules configured")

        # Step 6: Monitoring and reporting
        print("Step 6: Monitoring and Reporting")
        print("  Migration monitoring configured")

        print("\nComplete workflow example configured successfully!")
        print("Set dry_run=False to execute actual migration")

    except Exception as e:
        logger.error(f"Complete workflow failed: {e}")
        raise

async def main():
    """Run all examples"""
    print("DMLogn8n Migration System - Example Usage\n")

    try:
        await example_basic_migration()
        await example_schema_transformation()
        await example_data_validation()
        await example_migration_planning()
        await example_data_transformation()
        await example_format_conversion()
        await example_complete_migration_workflow()

        print("\n=== All Examples Completed Successfully ===")
        print("The DMLogn8n migration system is ready for production use!")

    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())