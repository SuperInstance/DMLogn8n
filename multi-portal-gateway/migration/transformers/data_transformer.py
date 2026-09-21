#!/usr/bin/env python3
"""
Data Transformer
Handles data mapping, conversion, and transformation during migration
"""

import asyncio
import json
import logging
import re
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib

logger = logging.getLogger("data_transformer")

class TransformationType(Enum):
    """Data transformation types"""
    FIELD_MAPPING = "field_mapping"
    TYPE_CONVERSION = "type_conversion"
    VALUE_MAPPING = "value_mapping"
    CONDITIONAL_TRANSFORMATION = "conditional"
    FUNCTION_TRANSFORMATION = "function"
    AGGREGATION = "aggregation"
    SPLIT = "split"
    MERGE = "merge"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    ANONYMIZATION = "anonymization"

class ValidationRule(Enum):
    """Data validation rules"""
    NOT_NULL = "not_null"
    REGEX = "regex"
    RANGE = "range"
    LENGTH = "length"
    ENUM = "enum"
    CUSTOM = "custom"

@dataclass
class TransformationRule:
    """Single transformation rule"""
    name: str
    type: TransformationType
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    error_handling: str = "skip"  # skip, default, raise

@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    transformation: Optional[str] = None
    default_value: Any = None
    required: bool = False
    validation: Optional[Dict[str, Any]] = None

@dataclass
class ValidationResult:
    """Data validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    transformed_value: Any = None

class DataTransformer:
    """Advanced data transformation engine"""

    def __init__(self):
        self.transformation_functions = self._initialize_transformation_functions()
        self.validation_functions = self._initialize_validation_functions()
        self.type_converters = self._initialize_type_converters()
        self.cache = {}  # Transformation cache for performance

    def _initialize_transformation_functions(self) -> Dict[str, Callable]:
        """Initialize built-in transformation functions"""
        return {
            # String transformations
            "upper": lambda x: str(x).upper() if x is not None else None,
            "lower": lambda x: str(x).lower() if x is not None else None,
            "title": lambda x: str(x).title() if x is not None else None,
            "trim": lambda x: str(x).strip() if x is not None else None,
            "ltrim": lambda x: str(x).lstrip() if x is not None else None,
            "rtrim": lambda x: str(x).rstrip() if x is not None else None,
            "replace": lambda x, old, new: str(x).replace(old, new) if x is not None else None,
            "substring": lambda x, start, length: str(x)[start:start+length] if x is not None else None,
            "pad_left": lambda x, length, char: str(x).rjust(length, char) if x is not None else None,
            "pad_right": lambda x, length, char: str(x).ljust(length, char) if x is not None else None,

            # Numeric transformations
            "abs": lambda x: abs(float(x)) if x is not None else None,
            "round": lambda x, digits=0: round(float(x), digits) if x is not None else None,
            "ceil": lambda x: int(float(x).ceil()) if x is not None else None,
            "floor": lambda x: int(float(x).floor()) if x is not None else None,
            "add": lambda x, y: float(x) + float(y) if x is not None and y is not None else None,
            "subtract": lambda x, y: float(x) - float(y) if x is not None and y is not None else None,
            "multiply": lambda x, y: float(x) * float(y) if x is not None and y is not None else None,
            "divide": lambda x, y: float(x) / float(y) if x is not None and y is not None and y != 0 else None,

            # Date transformations
            "now": lambda: datetime.now(timezone.utc),
            "today": lambda: date.today(),
            "format_date": lambda x, fmt: x.strftime(fmt) if x is not None else None,
            "parse_date": lambda x, fmt: datetime.strptime(x, fmt) if x is not None else None,
            "extract_year": lambda x: x.year if x is not None else None,
            "extract_month": lambda x: x.month if x is not None else None,
            "extract_day": lambda x: x.day if x is not None else None,

            # UUID transformations
            "generate_uuid": lambda: str(uuid.uuid4()),
            "generate_short_uuid": lambda: str(uuid.uuid4())[:8],

            # Hash transformations
            "md5": lambda x: hashlib.md5(str(x).encode()).hexdigest() if x is not None else None,
            "sha1": lambda x: hashlib.sha1(str(x).encode()).hexdigest() if x is not None else None,
            "sha256": lambda x: hashlib.sha256(str(x).encode()).hexdigest() if x is not None else None,

            # JSON transformations
            "parse_json": lambda x: json.loads(x) if x is not None else None,
            "stringify_json": lambda x: json.dumps(x) if x is not None else None,
            "extract_json_field": lambda x, field: x.get(field) if isinstance(x, dict) and x is not None else None,

            # Array transformations
            "split": lambda x, delimiter: str(x).split(delimiter) if x is not None else None,
            "join": lambda x, delimiter: delimiter.join(str(item) for item in x) if x is not None else None,
            "array_length": lambda x: len(x) if isinstance(x, list) else None,
            "array_contains": lambda x, item: item in x if isinstance(x, list) else False,

            # Conditional transformations
            "coalesce": lambda *args: next((arg for arg in args if arg is not None), None),
            "if_null": lambda x, default: x if x is not None else default,
            "if_empty": lambda x, default: x if x not in [None, ""] else default,
        }

    def _initialize_validation_functions(self) -> Dict[str, Callable]:
        """Initialize validation functions"""
        return {
            "not_null": lambda x: x is not None,
            "not_empty": lambda x: x is not None and str(x).strip() != "",
            "email": lambda x: re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(x)) if x else False,
            "url": lambda x: re.match(r'^https?://[^\s/$.?#].[^\s]*$', str(x)) if x else False,
            "phone": lambda x: re.match(r'^\+?1?\-?\.?\s?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})$', str(x)) if x else False,
            "numeric": lambda x: str(x).replace('.', '').replace('-', '').isdigit() if x else False,
            "integer": lambda x: str(x).lstrip('-').isdigit() if x else False,
            "float": lambda x: self._is_float(x) if x else False,
            "alpha": lambda x: str(x).isalpha() if x else False,
            "alphanumeric": lambda x: str(x).isalnum() if x else False,
            "min_length": lambda x, min_len: len(str(x)) >= min_len if x else False,
            "max_length": lambda x, max_len: len(str(x)) <= max_len if x else False,
            "range": lambda x, min_val, max_val: min_val <= float(x) <= max_val if x else False,
            "positive": lambda x: float(x) > 0 if x else False,
            "negative": lambda x: float(x) < 0 if x else False,
            "uuid": lambda x: re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', str(x), re.I) if x else False,
            "json": lambda x: self._is_valid_json(x) if x else False,
        }

    def _initialize_type_converters(self) -> Dict[str, Callable]:
        """Initialize type conversion functions"""
        return {
            "string": lambda x: str(x) if x is not None else None,
            "integer": lambda x: int(x) if x is not None else None,
            "float": lambda x: float(x) if x is not None else None,
            "decimal": lambda x: Decimal(str(x)) if x is not None else None,
            "boolean": lambda x: self._to_boolean(x),
            "date": lambda x: self._to_date(x),
            "datetime": lambda x: self._to_datetime(x),
            "json": lambda x: x if isinstance(x, (dict, list)) else json.loads(x) if x else None,
            "uuid": lambda x: str(uuid.UUID(str(x))) if x else None,
        }

    def _is_float(self, value: Any) -> bool:
        """Check if value can be converted to float"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _is_valid_json(self, value: Any) -> bool:
        """Check if value is valid JSON"""
        try:
            json.loads(str(value))
            return True
        except (ValueError, TypeError):
            return False

    def _to_boolean(self, value: Any) -> Optional[bool]:
        """Convert value to boolean"""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on', 't', 'y']
        return bool(value)

    def _to_date(self, value: Any) -> Optional[date]:
        """Convert value to date"""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    pass
        return None

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        """Convert value to datetime"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
        return None

    async def transform_record(self, record: Dict[str, Any], rules: List[TransformationRule],
                             context: Dict[str, Any] = None) -> Tuple[Dict[str, Any], ValidationResult]:
        """Transform a single record according to rules"""
        if context is None:
            context = {}

        transformed_record = {}
        all_errors = []
        all_warnings = []

        try:
            # Apply field mappings first
            field_mappings = [rule for rule in rules if rule.type == TransformationType.FIELD_MAPPING]
            for rule in field_mappings:
                result = await self._apply_field_mapping(record, rule, context)
                if result.is_valid:
                    if result.transformed_value is not None:
                        transformed_record[rule.target_field or rule.source_field] = result.transformed_value
                else:
                    all_errors.extend([f"Field {rule.source_field}: {error}" for error in result.errors])

            # Apply other transformations
            other_rules = [rule for rule in rules if rule.type != TransformationType.FIELD_MAPPING]
            for rule in other_rules:
                result = await self._apply_transformation(record, transformed_record, rule, context)
                if not result.is_valid:
                    all_errors.extend([f"Transformation {rule.name}: {error}" for error in result.errors])
                all_warnings.extend(result.warnings)

            # Apply validation rules
            validation_rules = [rule for rule in rules if rule.type == TransformationType.VALIDATION]
            for rule in validation_rules:
                result = await self._apply_validation(transformed_record, rule, context)
                if not result.is_valid:
                    all_errors.extend([f"Validation {rule.name}: {error}" for error in result.errors])

            validation_result = ValidationResult(
                is_valid=len(all_errors) == 0,
                errors=all_errors,
                warnings=all_warnings,
                transformed_value=transformed_record
            )

            return transformed_record, validation_result

        except Exception as e:
            logger.error(f"Record transformation failed: {e}")
            return transformed_record, ValidationResult(
                is_valid=False,
                errors=[f"Transformation failed: {str(e)}"],
                transformed_value=transformed_record
            )

    async def transform_batch(self, batch: List[Dict[str, Any]], rules: List[TransformationRule],
                            context: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], List[ValidationResult]]:
        """Transform a batch of records"""
        if context is None:
            context = {}

        transformed_batch = []
        validation_results = []

        for i, record in enumerate(batch):
            record_context = {**context, "batch_index": i, "batch_size": len(batch)}
            transformed_record, validation_result = await self.transform_record(record, rules, record_context)
            transformed_batch.append(transformed_record)
            validation_results.append(validation_result)

        return transformed_batch, validation_results

    async def _apply_field_mapping(self, record: Dict[str, Any], rule: TransformationRule,
                                 context: Dict[str, Any]) -> ValidationResult:
        """Apply field mapping transformation"""
        source_field = rule.source_field
        target_field = rule.target_field or source_field

        # Get source value
        if source_field in record:
            value = record[source_field]
        elif "." in source_field:
            # Handle nested field access
            value = self._get_nested_value(record, source_field)
        else:
            value = None

        # Apply default value if needed
        if value is None and "default_value" in rule.parameters:
            value = rule.parameters["default_value"]

        # Check if field is required
        if rule.parameters.get("required", False) and value is None:
            return ValidationResult(
                is_valid=False,
                errors=[f"Required field {source_field} is missing or null"]
            )

        # Apply transformation if specified
        if rule.parameters.get("transformation"):
            transformation_name = rule.parameters["transformation"]
            if transformation_name in self.transformation_functions:
                transformation_func = self.transformation_functions[transformation_name]
                try:
                    if transformation_name in ["replace", "substring", "pad_left", "pad_right"]:
                        # Functions with parameters
                        params = rule.parameters.get("transformation_params", {})
                        value = transformation_func(value, **params)
                    else:
                        value = transformation_func(value)
                except Exception as e:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Transformation {transformation_name} failed: {str(e)}"]
                    )

        # Apply type conversion
        if "target_type" in rule.parameters:
            target_type = rule.parameters["target_type"]
            if target_type in self.type_converters:
                try:
                    value = self.type_converters[target_type](value)
                except Exception as e:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Type conversion to {target_type} failed: {str(e)}"]
                    )

        # Apply validation
        if rule.validation_rules:
            for validation_rule in rule.validation_rules:
                validation_result = await self._validate_value(value, validation_rule, context)
                if not validation_result.is_valid:
                    return validation_result

        return ValidationResult(
            is_valid=True,
            transformed_value=value
        )

    async def _apply_transformation(self, original_record: Dict[str, Any],
                                  current_record: Dict[str, Any], rule: TransformationRule,
                                  context: Dict[str, Any]) -> ValidationResult:
        """Apply general transformation rule"""
        try:
            # Check condition
            if rule.condition:
                if not self._evaluate_condition(rule.condition, original_record, context):
                    return ValidationResult(is_valid=True, transformed_value=current_record)

            if rule.type == TransformationType.TYPE_CONVERSION:
                return await self._apply_type_conversion(current_record, rule, context)
            elif rule.type == TransformationType.VALUE_MAPPING:
                return await self._apply_value_mapping(current_record, rule, context)
            elif rule.type == TransformationType.FUNCTION_TRANSFORMATION:
                return await self._apply_function_transformation(current_record, rule, context)
            elif rule.type == TransformationType.CONDITIONAL_TRANSFORMATION:
                return await self._apply_conditional_transformation(current_record, rule, context)
            elif rule.type == TransformationType.AGGREGATION:
                return await self._apply_aggregation(current_record, rule, context)
            elif rule.type == TransformationType.SPLIT:
                return await self._apply_split_transformation(current_record, rule, context)
            elif rule.type == TransformationType.MERGE:
                return await self._apply_merge_transformation(current_record, rule, context)
            elif rule.type == TransformationType.ENRICHMENT:
                return await self._apply_enrichment(current_record, rule, context)
            elif rule.type == TransformationType.ANONYMIZATION:
                return await self._apply_anonymization(current_record, rule, context)
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Unsupported transformation type: {rule.type}"]
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Transformation {rule.name} failed: {str(e)}"]
            )

    async def _apply_type_conversion(self, record: Dict[str, Any], rule: TransformationRule,
                                   context: Dict[str, Any]) -> ValidationResult:
        """Apply type conversion transformation"""
        field_name = rule.parameters.get("field", rule.source_field)
        target_type = rule.parameters.get("target_type")

        if field_name not in record:
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field_name} not found for type conversion"]
            )

        value = record[field_name]

        if target_type in self.type_converters:
            try:
                converted_value = self.type_converters[target_type](value)
                record[field_name] = converted_value
                return ValidationResult(is_valid=True, transformed_value=converted_value)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Type conversion failed: {str(e)}"]
                )
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported target type: {target_type}"]
            )

    async def _apply_value_mapping(self, record: Dict[str, Any], rule: TransformationRule,
                                 context: Dict[str, Any]) -> ValidationResult:
        """Apply value mapping transformation"""
        field_name = rule.parameters.get("field", rule.source_field)
        mapping = rule.parameters.get("mapping", {})

        if field_name not in record:
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field_name} not found for value mapping"]
            )

        value = record[field_name]
        mapped_value = mapping.get(value, rule.parameters.get("default_value", value))

        record[field_name] = mapped_value
        return ValidationResult(is_valid=True, transformed_value=mapped_value)

    async def _apply_function_transformation(self, record: Dict[str, Any], rule: TransformationRule,
                                           context: Dict[str, Any]) -> ValidationResult:
        """Apply function transformation"""
        function_name = rule.parameters.get("function")
        target_field = rule.parameters.get("target_field", rule.source_field)
        source_fields = rule.parameters.get("source_fields", [rule.source_field])

        if function_name not in self.transformation_functions:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown transformation function: {function_name}"]
            )

        # Get source values
        source_values = []
        for field in source_fields:
            if field in record:
                source_values.append(record[field])
            elif "." in field:
                source_values.append(self._get_nested_value(record, field))
            else:
                source_values.append(None)

        # Apply function
        try:
            function = self.transformation_functions[function_name]
            if function_name in ["replace", "substring", "pad_left", "pad_right", "split", "join"]:
                # Functions with parameters
                params = rule.parameters.get("function_params", {})
                result = function(*source_values, **params)
            else:
                result = function(*source_values)

            record[target_field] = result
            return ValidationResult(is_valid=True, transformed_value=result)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Function transformation failed: {str(e)}"]
            )

    async def _apply_conditional_transformation(self, record: Dict[str, Any], rule: TransformationRule,
                                               context: Dict[str, Any]) -> ValidationResult:
        """Apply conditional transformation"""
        conditions = rule.parameters.get("conditions", [])
        default_value = rule.parameters.get("default_value")
        target_field = rule.parameters.get("target_field", rule.source_field)

        for condition in conditions:
            condition_expr = condition.get("condition")
            value = condition.get("value")

            if self._evaluate_condition(condition_expr, record, context):
                record[target_field] = value
                return ValidationResult(is_valid=True, transformed_value=value)

        # Apply default if no conditions matched
        if default_value is not None:
            record[target_field] = default_value
            return ValidationResult(is_valid=True, transformed_value=default_value)

        return ValidationResult(
            is_valid=False,
            errors=["No conditions matched and no default value provided"]
        )

    async def _apply_aggregation(self, record: Dict[str, Any], rule: TransformationRule,
                               context: Dict[str, Any]) -> ValidationResult:
        """Apply aggregation transformation"""
        # This would typically work across multiple records
        # For single record, we can aggregate multiple fields
        source_fields = rule.parameters.get("source_fields", [])
        aggregation_type = rule.parameters.get("aggregation", "sum")
        target_field = rule.parameters.get("target_field")

        values = []
        for field in source_fields:
            if field in record and record[field] is not None:
                try:
                    values.append(float(record[field]))
                except (ValueError, TypeError):
                    pass

        if not values:
            return ValidationResult(
                is_valid=False,
                errors=["No numeric values found for aggregation"]
            )

        if aggregation_type == "sum":
            result = sum(values)
        elif aggregation_type == "avg":
            result = sum(values) / len(values)
        elif aggregation_type == "min":
            result = min(values)
        elif aggregation_type == "max":
            result = max(values)
        elif aggregation_type == "count":
            result = len(values)
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported aggregation type: {aggregation_type}"]
            )

        record[target_field] = result
        return ValidationResult(is_valid=True, transformed_value=result)

    async def _apply_split_transformation(self, record: Dict[str, Any], rule: TransformationRule,
                                        context: Dict[str, Any]) -> ValidationResult:
        """Apply split transformation"""
        source_field = rule.parameters.get("source_field", rule.source_field)
        delimiter = rule.parameters.get("delimiter", ",")
        target_fields = rule.parameters.get("target_fields", [])

        if source_field not in record:
            return ValidationResult(
                is_valid=False,
                errors=[f"Source field {source_field} not found"]
            )

        value = record[source_field]
        if value is None:
            return ValidationResult(is_valid=True, transformed_value=None)

        parts = str(value).split(delimiter)

        # Assign parts to target fields
        for i, target_field in enumerate(target_fields):
            if i < len(parts):
                record[target_field] = parts[i].strip()
            else:
                record[target_field] = None

        return ValidationResult(is_valid=True, transformed_value=parts)

    async def _apply_merge_transformation(self, record: Dict[str, Any], rule: TransformationRule,
                                       context: Dict[str, Any]) -> ValidationResult:
        """Apply merge transformation"""
        source_fields = rule.parameters.get("source_fields", [])
        delimiter = rule.parameters.get("delimiter", " ")
        target_field = rule.parameters.get("target_field")

        values = []
        for field in source_fields:
            if field in record and record[field] is not None:
                values.append(str(record[field]))

        merged_value = delimiter.join(values)
        record[target_field] = merged_value

        return ValidationResult(is_valid=True, transformed_value=merged_value)

    async def _apply_enrichment(self, record: Dict[str, Any], rule: TransformationRule,
                              context: Dict[str, Any]) -> ValidationResult:
        """Apply data enrichment transformation"""
        enrichment_type = rule.parameters.get("enrichment_type")
        target_field = rule.parameters.get("target_field")

        if enrichment_type == "timestamp":
            record[target_field] = datetime.now(timezone.utc).isoformat()
        elif enrichment_type == "uuid":
            record[target_field] = str(uuid.uuid4())
        elif enrichment_type == "record_hash":
            record_data = json.dumps(record, sort_keys=True)
            record[target_field] = hashlib.sha256(record_data.encode()).hexdigest()
        elif enrichment_type == "batch_sequence":
            if "batch_index" in context:
                record[target_field] = context["batch_index"]
            else:
                record[target_field] = 0
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported enrichment type: {enrichment_type}"]
            )

        return ValidationResult(is_valid=True, transformed_value=record[target_field])

    async def _apply_anonymization(self, record: Dict[str, Any], rule: TransformationRule,
                                 context: Dict[str, Any]) -> ValidationResult:
        """Apply data anonymization transformation"""
        anonymization_type = rule.parameters.get("anonymization_type")
        field_name = rule.parameters.get("field", rule.source_field)

        if field_name not in record:
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field_name} not found for anonymization"]
            )

        value = record[field_name]

        if anonymization_type == "hash":
            record[field_name] = hashlib.sha256(str(value).encode()).hexdigest()
        elif anonymization_type == "mask":
            # Show first and last characters, mask the middle
            str_value = str(value)
            if len(str_value) > 4:
                record[field_name] = str_value[0] + "*" * (len(str_value) - 2) + str_value[-1]
            else:
                record[field_name] = "*" * len(str_value)
        elif anonymization_type == "null":
            record[field_name] = None
        elif anonymization_type == "replace":
            record[field_name] = rule.parameters.get("replacement_value", "[REDACTED]")
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported anonymization type: {anonymization_type}"]
            )

        return ValidationResult(is_valid=True, transformed_value=record[field_name])

    async def _apply_validation(self, record: Dict[str, Any], rule: TransformationRule,
                              context: Dict[str, Any]) -> ValidationResult:
        """Apply validation rule"""
        field_name = rule.parameters.get("field", rule.source_field)
        validation_rules = rule.parameters.get("rules", [])

        if field_name not in record:
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field_name} not found for validation"]
            )

        value = record[field_name]
        all_errors = []
        all_warnings = []

        for validation_rule in validation_rules:
            result = await self._validate_value(value, validation_rule, context)
            if not result.is_valid:
                all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )

    async def _validate_value(self, value: Any, validation_rule: Dict[str, Any],
                            context: Dict[str, Any]) -> ValidationResult:
        """Validate a single value against a rule"""
        rule_type = validation_rule.get("type")
        params = validation_rule.get("params", {})

        if rule_type in self.validation_functions:
            try:
                validation_func = self.validation_functions[rule_type]
                if rule_type in ["min_length", "max_length", "range"]:
                    # Functions with parameters
                    is_valid = validation_func(value, **params)
                else:
                    is_valid = validation_func(value)

                if is_valid:
                    return ValidationResult(is_valid=True)
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Validation failed for {rule_type} with value {value}"]
                    )

            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"]
                )
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown validation rule: {rule_type}"]
            )

    def _get_nested_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path"""
        keys = field_path.split(".")
        current_value = record

        for key in keys:
            if isinstance(current_value, dict) and key in current_value:
                current_value = current_value[key]
            else:
                return None

        return current_value

    def _evaluate_condition(self, condition: str, record: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate conditional expression"""
        # Simple condition evaluation - in practice, this would use a safer expression evaluator
        try:
            # Replace field references with actual values
            for field_name, field_value in record.items():
                condition = condition.replace(f"${field_name}", repr(field_value))

            # Add context variables
            for context_key, context_value in context.items():
                condition = condition.replace(f"${context_key}", repr(context_value))

            # Evaluate condition (simplified - would use ast.literal_eval in production)
            return eval(condition)  # noqa: S307 - This is a simplified example
        except Exception:
            return False

    def create_transformation_rules_from_config(self, config: Dict[str, Any]) -> List[TransformationRule]:
        """Create transformation rules from configuration"""
        rules = []

        for rule_config in config.get("transformation_rules", []):
            rule = TransformationRule(
                name=rule_config["name"],
                type=TransformationType(rule_config["type"]),
                source_field=rule_config.get("source_field"),
                target_field=rule_config.get("target_field"),
                parameters=rule_config.get("parameters", {}),
                condition=rule_config.get("condition"),
                validation_rules=rule_config.get("validation_rules", []),
                error_handling=rule_config.get("error_handling", "skip")
            )
            rules.append(rule)

        return rules

# Example usage and testing
async def test_data_transformer():
    """Test data transformation"""
    transformer = DataTransformer()

    # Sample transformation rules
    rules_config = [
        {
            "name": "map_user_fields",
            "type": "field_mapping",
            "source_field": "user_id",
            "target_field": "id",
            "parameters": {
                "transformation": "generate_uuid",
                "target_type": "string"
            }
        },
        {
            "name": "normalize_email",
            "type": "function_transformation",
            "source_field": "email_address",
            "parameters": {
                "function": "lower",
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
            "name": "add_timestamp",
            "type": "enrichment",
            "parameters": {
                "enrichment_type": "timestamp",
                "target_field": "migrated_at"
            }
        }
    ]

    rules = transformer.create_transformation_rules_from_config({"transformation_rules": rules_config})

    # Sample record
    sample_record = {
        "user_id": 123,
        "email_address": "John.Doe@Example.COM",
        "first_name": "John",
        "last_name": "Doe",
        "age": 30
    }

    try:
        transformed_record, validation_result = await transformer.transform_record(sample_record, rules)

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
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_transformer())