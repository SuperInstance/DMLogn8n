#!/usr/bin/env python3
"""
Example usage of the DMLogn8n Configuration Management System.

This script demonstrates how to use the configuration management system
for various common tasks including loading configurations, watching for changes,
validating configurations, and managing secrets.
"""

import os
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the configuration management system
from config import (
    config_manager,
    config_watcher,
    secret_manager,
    get_config,
    get_database_config,
    get_model_config,
    get_monitoring_config,
    set_config,
    reload_configuration,
    validate_configuration,
    start_config_watcher,
    stop_config_watcher,
    get_environment,
    get_secret,
    set_secret
)


def demonstrate_basic_usage():
    """Demonstrate basic configuration usage."""
    print("\n" + "="*60)
    print("BASIC CONFIGURATION USAGE")
    print("="*60)

    # Get current environment
    env = get_environment()
    print(f"Current environment: {env}")

    # Get basic configuration values
    app_name = get_config('app', 'name', 'DMLogn8n')
    app_version = get_config('app', 'version', '1.0.0')
    debug_mode = get_config('debug', False)

    print(f"Application name: {app_name}")
    print(f"Application version: {app_version}")
    print(f"Debug mode: {debug_mode}")

    # Get database configuration
    try:
        db_config = get_database_config()
        print(f"Database type: {db_config.type}")
        print(f"Database name: {db_config.name}")
        print(f"Connection pool size: {db_config.pool.max_connections}")
    except Exception as e:
        print(f"Database configuration error: {e}")

    # Get AI model configuration
    try:
        model_configs = get_config('ai_models', 'models', {})
        if model_configs:
            print(f"Available models: {list(model_configs.keys())}")

            # Get specific model configuration
            if 'gpt4_dev' in model_configs:
                gpt4_config = get_model_config('gpt4_dev')
                print(f"GPT-4 provider: {gpt4_config.provider}")
                print(f"GPT-4 model ID: {gpt4_config.model_id}")
                print(f"Temperature: {gpt4_config.parameters.temperature}")
    except Exception as e:
        print(f"Model configuration error: {e}")

    # Get monitoring configuration
    try:
        monitoring_config = get_monitoring_config()
        print(f"Monitoring enabled: {monitoring_config.enabled}")
        print(f"Monitoring backend: {monitoring_config.backend}")
        print(f"Log level: {monitoring_config.logging.level}")
    except Exception as e:
        print(f"Monitoring configuration error: {e}")


def demonstrate_configuration_updates():
    """Demonstrate dynamic configuration updates."""
    print("\n" + "="*60)
    print("DYNAMIC CONFIGURATION UPDATES")
    print("="*60)

    # Set a configuration value
    print("Setting custom configuration value...")
    set_config('app', 'custom_setting', 'test_value', source='example_script')

    # Read it back
    custom_value = get_config('app', 'custom_setting')
    print(f"Custom setting value: {custom_value}")

    # Update model configuration
    print("Updating model configuration...")
    set_config('ai_models', 'models.gpt4_dev.parameters.temperature', 0.8, source='example_script')

    # Verify the change
    try:
        gpt4_config = get_model_config('gpt4_dev')
        print(f"Updated temperature: {gpt4_config.parameters.temperature}")
    except Exception as e:
        print(f"Error reading updated config: {e}")


def demonstrate_configuration_validation():
    """Demonstrate configuration validation."""
    print("\n" + "="*60)
    print("CONFIGURATION VALIDATION")
    print("="*60)

    # Validate current configuration
    print("Validating current configuration...")
    results = validate_configuration()

    print(f"Validation results for {len(results)} configuration types:")
    for config_type, result in results.items():
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"  {config_type}: {status}")

        if result.errors:
            print(f"    Errors ({len(result.errors)}):")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"      - {error.field}: {error.message}")

        if result.warnings:
            print(f"    Warnings ({len(result.warnings)}):")
            for warning in result.warnings[:3]:  # Show first 3 warnings
                print(f"      - {warning.field}: {warning.message}")


def demonstrate_secret_management():
    """Demonstrate secret management."""
    print("\n" + "="*60)
    print("SECRET MANAGEMENT")
    print("="*60)

    # Check available backends
    backend_names = secret_manager.get_backend_names()
    primary_backend = secret_manager.get_primary_backend_name()

    print(f"Available backends: {backend_names}")
    print(f"Primary backend: {primary_backend}")

    # Health check
    print("Checking backend health...")
    health_status = secret_manager.health_check()
    for backend, healthy in health_status.items():
        status = "✓ HEALTHY" if healthy else "✗ UNHEALTHY"
        print(f"  {backend}: {status}")

    # Get existing secrets
    print("Getting existing secrets...")
    api_key = get_secret('OPENAI_API_KEY')
    if api_key:
        print(f"OpenAI API Key: {'*' * 20}{api_key[-4:] if len(api_key) > 4 else ''}")
    else:
        print("OpenAI API Key not found")

    db_password = get_secret('DB_PASSWORD')
    if db_password:
        print(f"Database Password: {'*' * len(db_password)}")
    else:
        print("Database password not found")

    # Set a test secret (only in development)
    if get_environment() == 'development':
        print("Setting test secret...")
        success = set_secret('TEST_SECRET', 'test_value_123')
        print(f"Secret set successfully: {success}")

        # Read it back
        test_value = get_secret('TEST_SECRET')
        print(f"Test secret value: {test_value}")


def demonstrate_file_watching():
    """Demonstrate configuration file watching."""
    print("\n" + "="*60)
    print("CONFIGURATION FILE WATCHING")
    print("="*60)

    # Add a change listener
    def on_config_change(event):
        print(f"Configuration changed: {event.config_type}")
        print(f"  Source: {event.source}")
        print(f"  Timestamp: {event.timestamp}")
        print(f"  Version: {event.version}")

    config_manager.add_change_listener('*', on_config_change)

    # Start the file watcher
    print("Starting configuration file watcher...")
    start_config_watcher()

    # Simulate some configuration changes
    print("Simulating configuration changes...")
    for i in range(3):
        set_config('app', f'test_value_{i}', f'value_{i}_{int(time.time())}', source='file_watcher_demo')
        time.sleep(1)

    # Stop the file watcher
    print("Stopping configuration file watcher...")
    stop_config_watcher()


def demonstrate_configuration_export():
    """Demonstrate configuration export."""
    print("\n" + "="*60)
    print("CONFIGURATION EXPORT")
    print("="*60)

    # Export current configuration (without secrets)
    export_file = Path("/tmp/dmlogn8n_config_export.yaml")
    print(f"Exporting configuration to {export_file}...")

    try:
        config_manager.export_configuration(export_file, include_secrets=False)
        print("Configuration exported successfully")

        # Show file size
        if export_file.exists():
            file_size = export_file.stat().st_size
            print(f"Export file size: {file_size} bytes")

    except Exception as e:
        print(f"Export failed: {e}")


def demonstrate_environment_specific_configs():
    """Demonstrate environment-specific configuration handling."""
    print("\n" + "="*60)
    print("ENVIRONMENT-SPECIFIC CONFIGURATIONS")
    print("="*60)

    current_env = get_environment()
    print(f"Current environment: {current_env}")

    # Show environment-specific settings
    debug_mode = get_config('debug', False)
    log_level = get_config('log_level', 'INFO')
    monitoring_enabled = get_config('monitoring.enabled', True)

    print(f"Debug mode: {debug_mode}")
    print(f"Log level: {log_level}")
    print(f"Monitoring enabled: {monitoring_enabled}")

    # Show environment-specific database settings
    try:
        db_config = get_database_config()
        print(f"Database type: {db_config.type}")
        print(f"Database pool size: {db_config.pool.max_connections}")
        print(f"Database SSL enabled: {db_config.ssl is not None}")
    except Exception as e:
        print(f"Could not read database config: {e}")

    # Show environment-specific model settings
    try:
        model_configs = get_config('ai_models.models', {})
        for model_name, model_data in model_configs.items():
            if model_data.get('enabled'):
                print(f"Enabled model: {model_name}")
                print(f"  Provider: {model_data.get('provider')}")
                print(f"  Priority: {model_data.get('priority')}")
    except Exception as e:
        print(f"Could not read model configs: {e}")


def demonstrate_error_handling():
    """Demonstrate error handling in the configuration system."""
    print("\n" + "="*60)
    print("ERROR HANDLING")
    print("="*60)

    # Try to get non-existent configuration
    print("Getting non-existent configuration...")
    value = get_config('non_existent_section', 'non_existent_key', 'default_value')
    print(f"Value: {value}")

    # Try to get non-existent model configuration
    print("Getting non-existent model configuration...")
    try:
        model_config = get_model_config('non_existent_model')
        print(f"Model config: {model_config}")
    except Exception as e:
        print(f"Expected error: {e}")

    # Try to set invalid configuration
    print("Attempting to set invalid configuration...")
    try:
        # This should trigger validation
        set_config('database', 'databases.invalid.type', 'invalid_db_type', source='error_demo')
        print("Configuration set (no validation error)")
    except Exception as e:
        print(f"Expected validation error: {e}")


def main():
    """Main demonstration function."""
    print("DMLogn8n Configuration Management System Demo")
    print("=" * 60)

    try:
        # Run all demonstrations
        demonstrate_basic_usage()
        demonstrate_configuration_updates()
        demonstrate_configuration_validation()
        demonstrate_secret_management()
        demonstrate_file_watching()
        demonstrate_configuration_export()
        demonstrate_environment_specific_configs()
        demonstrate_error_handling()

        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)

    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user")
    except Exception as e:
        print(f"\nDemonstration failed with error: {e}")
        logger.exception("Demo failed")
    finally:
        # Cleanup
        try:
            stop_config_watcher()
        except Exception:
            pass


if __name__ == "__main__":
    main()