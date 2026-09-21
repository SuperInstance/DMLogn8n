"""
Configuration validation framework for DMLogn8n multi-agent platform.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

from pydantic import BaseModel, ValidationError, validator
from pydantic.fields import FieldInfo
import yaml
import json

from .schemas.database import DatabaseConfig, MultiDatabaseConfig
from .schemas.ai_models import ModelConfig, MultiModelConfig
from .schemas.monitoring import MonitoringConfig


# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Configuration validation error."""
    field: str
    message: str
    value: Any
    schema_type: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Configuration validation result."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    config_dict: Optional[Dict[str, Any]] = None
    validated_config: Optional[BaseModel] = None


class BaseConfigValidator(ABC):
    """Base class for configuration validators."""

    def __init__(self, schema_class: Type[BaseModel]):
        self.schema_class = schema_class
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate configuration data."""
        pass

    def _process_env_vars(self, config_data: Any) -> Any:
        """Process environment variable substitutions."""
        if isinstance(config_data, dict):
            processed = {}
            for key, value in config_data.items():
                processed[key] = self._process_env_vars(value)
            return processed
        elif isinstance(config_data, list):
            return [self._process_env_vars(item) for item in config_data]
        elif isinstance(config_data, str) and config_data.startswith("${") and config_data.endswith("}"):
            env_var = config_data[2:-1]
            default_value = None

            # Handle default values: ${VAR:default_value}
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)

            value = os.getenv(env_var, default_value)
            if value is None:
                raise ValueError(f"Environment variable '{env_var}' not found and no default provided")
            return value
        else:
            return config_data

    def _validate_secrets(self, config_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate secret fields."""
        secrets_errors = []
        sensitive_patterns = [
            r'password', r'api[_-]?key', r'secret', r'token', r'credential',
            r'private[_-]?key', r'auth[_-]?token', r'client[_-]?secret'
        ]

        def check_secrets(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if any(re.search(pattern, key.lower()) for pattern in sensitive_patterns):
                        if not value or (isinstance(value, str) and len(value) < 8):
                            secrets_errors.append(ValidationError(
                                field=current_path,
                                message=f"Secret field '{key}' appears to be empty or too short",
                                value=value,
                                schema_type="security",
                                severity="warning"
                            ))
                        elif isinstance(value, str) and value == "change_me":
                            secrets_errors.append(ValidationError(
                                field=current_path,
                                message=f"Secret field '{key}' still has default value",
                                value=value,
                                schema_type="security",
                                severity="error"
                            ))
                    check_secrets(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_secrets(item, f"{path}[{i}]")

        check_secrets(config_data)
        return secrets_errors


class DatabaseConfigValidator(BaseConfigValidator):
    """Database configuration validator."""

    def __init__(self):
        super().__init__(MultiDatabaseConfig)

    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate database configuration."""
        errors = []
        warnings = []

        try:
            # Process environment variables
            processed_data = self._process_env_vars(config_data)

            # Validate secrets
            secrets_errors = self._validate_secrets(processed_data)
            errors.extend([e for e in secrets_errors if e.severity == "error"])
            warnings.extend([e for e in secrets_errors if e.severity == "warning"])

            # Validate against Pydantic schema
            validated_config = self.schema_class(**processed_data)

            # Additional business logic validations
            business_warnings = self._validate_business_rules(validated_config.dict())
            warnings.extend(business_warnings)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                config_dict=processed_data,
                validated_config=validated_config
            )

        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error['loc'])
                validation_errors.append(ValidationError(
                    field=field,
                    message=error['msg'],
                    value=error.get('input'),
                    schema_type="database",
                    severity="error"
                ))

            return ValidationResult(
                is_valid=False,
                errors=validation_errors,
                warnings=warnings,
                config_dict=None
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="root",
                    message=f"Unexpected validation error: {str(e)}",
                    value=None,
                    schema_type="database",
                    severity="error"
                )],
                warnings=warnings,
                config_dict=None
            )

    def _validate_business_rules(self, config_dict: Dict[str, Any]) -> List[ValidationError]:
        """Validate business rules for database configuration."""
        warnings = []

        # Check for production-ready settings
        databases = config_dict.get('databases', {})
        for db_name, db_config in databases.items():
            if db_config.get('type') == 'postgresql':
                # Check for SSL in production
                if not db_config.get('ssl') and os.getenv('ENVIRONMENT') == 'production':
                    warnings.append(ValidationError(
                        field=f"databases.{db_name}.ssl",
                        message="SSL should be enabled for PostgreSQL in production",
                        value=None,
                        schema_type="database",
                        severity="warning"
                    ))

                # Check connection pool size
                pool = db_config.get('pool', {})
                max_connections = pool.get('max_connections', 10)
                if max_connections > 100:
                    warnings.append(ValidationError(
                        field=f"databases.{db_name}.pool.max_connections",
                        message=f"High connection pool size ({max_connections}) may impact performance",
                        value=max_connections,
                        schema_type="database",
                        severity="warning"
                    ))

            # Check for default credentials
            credentials = db_config.get('credentials', {})
            if credentials.get('username') == 'admin' or credentials.get('username') == 'root':
                warnings.append(ValidationError(
                    field=f"databases.{db_name}.credentials.username",
                    message="Default admin/root usernames should be changed in production",
                    value=credentials.get('username'),
                    schema_type="database",
                    severity="warning"
                ))

        return warnings


class AIModelConfigValidator(BaseConfigValidator):
    """AI model configuration validator."""

    def __init__(self):
        super().__init__(MultiModelConfig)

    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate AI model configuration."""
        errors = []
        warnings = []

        try:
            # Process environment variables
            processed_data = self._process_env_vars(config_data)

            # Validate secrets
            secrets_errors = self._validate_secrets(processed_data)
            errors.extend([e for e in secrets_errors if e.severity == "error"])
            warnings.extend([e for e in secrets_errors if e.severity == "warning"])

            # Validate against Pydantic schema
            validated_config = self.schema_class(**processed_data)

            # Additional business logic validations
            business_warnings = self._validate_business_rules(validated_config.dict())
            warnings.extend(business_warnings)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                config_dict=processed_data,
                validated_config=validated_config
            )

        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error['loc'])
                validation_errors.append(ValidationError(
                    field=field,
                    message=error['msg'],
                    value=error.get('input'),
                    schema_type="ai_model",
                    severity="error"
                ))

            return ValidationResult(
                is_valid=False,
                errors=validation_errors,
                warnings=warnings,
                config_dict=None
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="root",
                    message=f"Unexpected validation error: {str(e)}",
                    value=None,
                    schema_type="ai_model",
                    severity="error"
                )],
                warnings=warnings,
                config_dict=None
            )

    def _validate_business_rules(self, config_dict: Dict[str, Any]) -> List[ValidationError]:
        """Validate business rules for AI model configuration."""
        warnings = []

        models = config_dict.get('models', {})
        for model_name, model_config in models.items():
            # Check for API keys
            credentials = model_config.get('credentials', {})
            if not credentials.get('api_key'):
                warnings.append(ValidationError(
                    field=f"models.{model_name}.credentials.api_key",
                    message=f"No API key configured for model '{model_name}'",
                    value=None,
                    schema_type="ai_model",
                    severity="warning"
                ))

            # Check rate limiting
            rate_limiting = model_config.get('rate_limiting', {})
            if not rate_limiting.get('requests_per_minute'):
                warnings.append(ValidationError(
                    field=f"models.{model_name}.rate_limiting.requests_per_minute",
                    message=f"No rate limiting configured for model '{model_name}'",
                    value=None,
                    schema_type="ai_model",
                    severity="warning"
                ))

            # Check cost tracking
            if not model_config.get('cost_per_input_token'):
                warnings.append(ValidationError(
                    field=f"models.{model_name}.cost_per_input_token",
                    message=f"No cost tracking configured for model '{model_name}'",
                    value=None,
                    schema_type="ai_model",
                    severity="info"
                ))

            # Check temperature settings for different model types
            model_type = model_config.get('model_type')
            parameters = model_config.get('parameters', {})
            temperature = parameters.get('temperature', 0.7)

            if model_type == 'embedding' and temperature != 0:
                warnings.append(ValidationError(
                    field=f"models.{model_name}.parameters.temperature",
                    message="Temperature should be 0 for embedding models",
                    value=temperature,
                    schema_type="ai_model",
                    severity="warning"
                ))

        return warnings


class MonitoringConfigValidator(BaseConfigValidator):
    """Monitoring configuration validator."""

    def __init__(self):
        super().__init__(MonitoringConfig)

    def validate(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate monitoring configuration."""
        errors = []
        warnings = []

        try:
            # Process environment variables
            processed_data = self._process_env_vars(config_data)

            # Validate secrets
            secrets_errors = self._validate_secrets(processed_data)
            errors.extend([e for e in secrets_errors if e.severity == "error"])
            warnings.extend([e for e in secrets_errors if e.severity == "warning"])

            # Validate against Pydantic schema
            validated_config = self.schema_class(**processed_data)

            # Additional business logic validations
            business_warnings = self._validate_business_rules(validated_config.dict())
            warnings.extend(business_warnings)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                config_dict=processed_data,
                validated_config=validated_config
            )

        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error['loc'])
                validation_errors.append(ValidationError(
                    field=field,
                    message=error['msg'],
                    value=error.get('input'),
                    schema_type="monitoring",
                    severity="error"
                ))

            return ValidationResult(
                is_valid=False,
                errors=validation_errors,
                warnings=warnings,
                config_dict=None
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="root",
                    message=f"Unexpected validation error: {str(e)}",
                    value=None,
                    schema_type="monitoring",
                    severity="error"
                )],
                warnings=warnings,
                config_dict=None
            )

    def _validate_business_rules(self, config_dict: Dict[str, Any]) -> List[ValidationError]:
        """Validate business rules for monitoring configuration."""
        warnings = []

        # Check for monitoring in production
        if os.getenv('ENVIRONMENT') == 'production':
            if not config_dict.get('enabled'):
                warnings.append(ValidationError(
                    field="enabled",
                    message="Monitoring should be enabled in production",
                    value=False,
                    schema_type="monitoring",
                    severity="warning"
                ))

            # Check log level for production
            logging_config = config_dict.get('logging', {})
            log_level = logging_config.get('level')
            if log_level in ['DEBUG', 'TRACE']:
                warnings.append(ValidationError(
                    field="logging.level",
                    message="Debug/trace logging should be disabled in production",
                    value=log_level,
                    schema_type="monitoring",
                    severity="warning"
                ))

            # Check for file logging in production
            if not logging_config.get('file_path'):
                warnings.append(ValidationError(
                    field="logging.file_path",
                    message="File logging should be configured in production",
                    value=None,
                    schema_type="monitoring",
                    severity="warning"
                ))

        # Check alert rules
        alert_rules = config_dict.get('alert_rules', {})
        if not alert_rules:
            warnings.append(ValidationError(
                field="alert_rules",
                message="No alert rules configured",
                value=None,
                schema_type="monitoring",
                severity="info"
            ))

        # Check notification channels
        notification_channels = config_dict.get('notification_channels', {})
        if not notification_channels:
            warnings.append(ValidationError(
                field="notification_channels",
                message="No notification channels configured",
                value=None,
                schema_type="monitoring",
                severity="warning"
            ))

        return warnings


class ConfigValidator:
    """Main configuration validator orchestrator."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validators = {
            'database': DatabaseConfigValidator(),
            'ai_models': AIModelConfigValidator(),
            'monitoring': MonitoringConfigValidator()
        }

    def validate_config_file(self, file_path: Union[str, Path]) -> Dict[str, ValidationResult]:
        """Validate a configuration file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

            return self.validate_config_data(config_data)

        except Exception as e:
            self.logger.error(f"Error reading configuration file {file_path}: {str(e)}")
            raise

    def validate_config_data(self, config_data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """Validate configuration data."""
        results = {}

        for config_type, validator in self.validators.items():
            if config_type in config_data:
                try:
                    results[config_type] = validator.validate(config_data[config_type])
                except Exception as e:
                    self.logger.error(f"Error validating {config_type} configuration: {str(e)}")
                    results[config_type] = ValidationResult(
                        is_valid=False,
                        errors=[ValidationError(
                            field="root",
                            message=f"Validation failed: {str(e)}",
                            value=None,
                            schema_type=config_type,
                            severity="error"
                        )],
                        warnings=[],
                        config_dict=None
                    )
            else:
                self.logger.warning(f"No configuration found for {config_type}")

        return results

    def validate_environment_config(self, environment: str) -> Dict[str, ValidationResult]:
        """Validate environment-specific configuration."""
        config_file = Path(__file__).parent / "environments" / f"{environment}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Environment configuration not found: {config_file}")

        return self.validate_config_file(config_file)

    def get_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get validation summary."""
        total_errors = sum(len(result.errors) for result in results.values())
        total_warnings = sum(len(result.warnings) for result in results.values())
        total_valid = sum(1 for result in results.values() if result.is_valid)

        return {
            'total_configurations': len(results),
            'valid_configurations': total_valid,
            'invalid_configurations': len(results) - total_valid,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'overall_valid': total_errors == 0,
            'results': {config_type: {
                'is_valid': result.is_valid,
                'error_count': len(result.errors),
                'warning_count': len(result.warnings)
            } for config_type, result in results.items()}
        }

    def print_validation_report(self, results: Dict[str, ValidationResult]) -> None:
        """Print detailed validation report."""
        summary = self.get_summary(results)

        print("\n" + "="*60)
        print("CONFIGURATION VALIDATION REPORT")
        print("="*60)

        print(f"Overall Status: {'✓ VALID' if summary['overall_valid'] else '✗ INVALID'}")
        print(f"Valid Configurations: {summary['valid_configurations']}/{summary['total_configurations']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Total Warnings: {summary['total_warnings']}")
        print()

        for config_type, result in results.items():
            print(f"{config_type.upper()} CONFIGURATION:")
            print(f"  Status: {'✓ VALID' if result.is_valid else '✗ INVALID'}")

            if result.errors:
                print(f"  Errors ({len(result.errors)}):")
                for error in result.errors:
                    print(f"    ✗ {error.field}: {error.message}")
                    if error.value is not None:
                        print(f"      Value: {error.value}")

            if result.warnings:
                print(f"  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"    ⚠ {warning.field}: {warning.message}")
                    if warning.value is not None:
                        print(f"      Value: {warning.value}")

            print()

        print("="*60)