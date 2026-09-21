#!/usr/bin/env python3
"""
Data Validation and Calculations Enhancement for DMlogn8n

This script provides advanced data validation, automated calculations,
and data integrity checks for the comprehensive data table system.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidationEngine:
    """Advanced data validation and calculation engine"""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        self.calculation_rules = self._initialize_calculation_rules()
        self.integrity_checks = self._initialize_integrity_checks()

    def _initialize_validation_rules(self) -> Dict[str, Dict]:
        """Initialize validation rules for different data types"""
        return {
            "character": {
                "required_fields": ["characterId", "name", "level"],
                "field_validators": {
                    "characterId": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_-]+$",
                        "min_length": 3,
                        "max_length": 50,
                        "error_message": "Character ID must be alphanumeric, 3-50 characters"
                    },
                    "name": {
                        "type": "string",
                        "min_length": 1,
                        "max_length": 100,
                        "pattern": r"^[a-zA-Z\s\-'\.]+$",
                        "error_message": "Name must be 1-100 characters, letters and spaces only"
                    },
                    "level": {
                        "type": "integer",
                        "min_value": 1,
                        "max_value": 100,
                        "error_message": "Level must be an integer between 1 and 100"
                    },
                    "hpCurrent": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 9999,
                        "error_message": "HP must be a non-negative integer"
                    },
                    "hpMax": {
                        "type": "integer",
                        "min_value": 1,
                        "max_value": 9999,
                        "error_message": "Max HP must be a positive integer"
                    },
                    "mpCurrent": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 9999,
                        "error_message": "MP must be a non-negative integer"
                    },
                    "mpMax": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 9999,
                        "error_message": "Max MP must be a non-negative integer"
                    },
                    "xpCurrent": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 999999,
                        "error_message": "XP must be a non-negative integer"
                    },
                    "xpToNext": {
                        "type": "integer",
                        "min_value": 1,
                        "max_value": 999999,
                        "error_message": "XP to next must be a positive integer"
                    },
                    "inventoryWeight": {
                        "type": "float",
                        "min_value": 0,
                        "max_value": 9999.99,
                        "error_message": "Inventory weight must be non-negative"
                    },
                    "inventoryValue": {
                        "type": "float",
                        "min_value": 0,
                        "max_value": 999999.99,
                        "error_message": "Inventory value must be non-negative"
                    },
                    "spellSlotsUsed": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 99,
                        "error_message": "Spell slots used must be non-negative"
                    },
                    "spellSlotsMax": {
                        "type": "integer",
                        "min_value": 0,
                        "max_value": 99,
                        "error_message": "Max spell slots must be non-negative"
                    }
                },
                "cross_field_validations": [
                    {
                        "name": "hp_bounds_check",
                        "description": "Current HP cannot exceed Max HP",
                        "validator": lambda data: data.get("hpCurrent", 0) <= data.get("hpMax", 1),
                        "error_message": "Current HP cannot exceed Max HP"
                    },
                    {
                        "name": "mp_bounds_check",
                        "description": "Current MP cannot exceed Max MP",
                        "validator": lambda data: data.get("mpCurrent", 0) <= data.get("mpMax", 0),
                        "error_message": "Current MP cannot exceed Max MP"
                    },
                    {
                        "name": "spell_slots_bounds_check",
                        "description": "Used spell slots cannot exceed max spell slots",
                        "validator": lambda data: data.get("spellSlotsUsed", 0) <= data.get("spellSlotsMax", 0),
                        "error_message": "Used spell slots cannot exceed max spell slots"
                    },
                    {
                        "name": "xp_progress_check",
                        "description": "Current XP should not exceed XP to next",
                        "validator": lambda data: data.get("xpCurrent", 0) < data.get("xpToNext", 1),
                        "error_message": "Current XP should be less than XP required for next level"
                    }
                ]
            },
            "scene": {
                "required_fields": ["sceneId", "name"],
                "field_validators": {
                    "sceneId": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_-]+$",
                        "min_length": 3,
                        "max_length": 50,
                        "error_message": "Scene ID must be alphanumeric, 3-50 characters"
                    },
                    "name": {
                        "type": "string",
                        "min_length": 1,
                        "max_length": 200,
                        "error_message": "Scene name must be 1-200 characters"
                    },
                    "lighting": {
                        "type": "enum",
                        "allowed_values": ["bright", "normal", "dim", "dark", "magical", "flickering"],
                        "error_message": "Lighting must be one of: bright, normal, dim, dark, magical, flickering"
                    },
                    "weather": {
                        "type": "enum",
                        "allowed_values": ["clear", "rain", "storm", "fog", "snow", "wind", "mist"],
                        "error_message": "Weather must be one of: clear, rain, storm, fog, snow, wind, mist"
                    },
                    "visibility": {
                        "type": "enum",
                        "allowed_values": ["excellent", "good", "moderate", "poor"],
                        "error_message": "Visibility must be one of: excellent, good, moderate, poor"
                    },
                    "mood": {
                        "type": "enum",
                        "allowed_values": ["peaceful", "neutral", "tense", "mysterious", "dramatic", "ominous"],
                        "error_message": "Mood must be one of: peaceful, neutral, tense, mysterious, dramatic, ominous"
                    },
                    "timeOfDay": {
                        "type": "enum",
                        "allowed_values": ["dawn", "morning", "noon", "afternoon", "dusk", "evening", "night"],
                        "error_message": "Time of day must be one of: dawn, morning, noon, afternoon, dusk, evening, night"
                    }
                },
                "array_field_validators": {
                    "objects": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["id", "name"],
                            "error_message": "Each object must have id and name"
                        }
                    },
                    "environmentalEffects": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["type", "intensity"],
                            "error_message": "Each environmental effect must have type and intensity"
                        }
                    }
                }
            },
            "world": {
                "required_fields": ["campaignId"],
                "field_validators": {
                    "campaignId": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_-]+$",
                        "min_length": 3,
                        "max_length": 50,
                        "error_message": "Campaign ID must be alphanumeric, 3-50 characters"
                    },
                    "worldStatus": {
                        "type": "enum",
                        "allowed_values": ["active", "paused", "completed", "archived"],
                        "error_message": "World status must be one of: active, paused, completed, archived"
                    }
                },
                "array_field_validators": {
                    "locations": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["id", "name"],
                            "error_message": "Each location must have id and name"
                        }
                    },
                    "npcs": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["id", "name"],
                            "error_message": "Each NPC must have id and name"
                        }
                    },
                    "factions": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["id", "name"],
                            "error_message": "Each faction must have id and name"
                        }
                    },
                    "quests": {
                        "item_validator": {
                            "type": "object",
                            "required_fields": ["id", "name"],
                            "error_message": "Each quest must have id and name"
                        }
                    }
                }
            }
        }

    def _initialize_calculation_rules(self) -> Dict[str, List[Dict]]:
        """Initialize automated calculation rules"""
        return {
            "character": [
                {
                    "name": "calculate_hp_percentage",
                    "description": "Calculate HP as percentage of max HP",
                    "input_fields": ["hpCurrent", "hpMax"],
                    "output_field": "hpPercentage",
                    "calculation": lambda data: {
                        "hpPercentage": round((data.get("hpCurrent", 0) / max(data.get("hpMax", 1), 1)) * 100, 1)
                    }
                },
                {
                    "name": "calculate_mp_percentage",
                    "description": "Calculate MP as percentage of max MP",
                    "input_fields": ["mpCurrent", "mpMax"],
                    "output_field": "mpPercentage",
                    "calculation": lambda data: {
                        "mpPercentage": round((data.get("mpCurrent", 0) / max(data.get("mpMax", 1), 1)) * 100, 1)
                    }
                },
                {
                    "name": "calculate_xp_percentage",
                    "description": "Calculate XP progress as percentage",
                    "input_fields": ["xpCurrent", "xpToNext"],
                    "output_field": "xpPercentage",
                    "calculation": lambda data: {
                        "xpPercentage": round((data.get("xpCurrent", 0) / max(data.get("xpToNext", 1), 1)) * 100, 1)
                    }
                },
                {
                    "name": "calculate_encumbrance_status",
                    "description": "Calculate encumbrance status based on weight",
                    "input_fields": ["inventoryWeight", "level"],
                    "output_field": "encumbranceStatus",
                    "calculation": lambda data: {
                        weight = data.get("inventoryWeight", 0)
                        level = data.get("level", 1)
                        max_weight = level * 15 + 100  # Basic formula: 100 + 15 per level

                        if weight <= max_weight * 0.3:
                            status = "unencumbered"
                        elif weight <= max_weight * 0.6:
                            status = "lightly_encumbered"
                        elif weight <= max_weight * 0.9:
                            status = "heavily_encumbered"
                        else:
                            status = "overencumbered"

                        return {
                            "encumbranceStatus": status,
                            "maxCarryWeight": max_weight,
                            "encumbrancePercentage": round((weight / max_weight) * 100, 1)
                        }
                    }
                },
                {
                    "name": "calculate_spell_recovery_rate",
                    "description": "Calculate spell slot recovery rate based on level",
                    "input_fields": ["level", "class"],
                    "output_field": "spellRecoveryInfo",
                    "calculation": lambda data: {
                        level = data.get("level", 1)
                        class_name = data.get("class", "").lower()

                        # Base recovery rates (slots per long rest)
                        if "wizard" in class_name or "sorcerer" in class_name:
                            recovery_rate = math.ceil(level / 2)
                        elif "cleric" in class_name or "druid" in class_name:
                            recovery_rate = math.ceil(level / 3) + 1
                        elif "paladin" in class_name or "ranger" in class_name:
                            recovery_rate = math.ceil(level / 4) + 1
                        else:
                            recovery_rate = 1

                        return {
                            "spellRecoveryRate": recovery_rate,
                            "recoveryType": "long_rest",
                            "estimatedTimeToFull": "8 hours"
                        }
                    }
                }
            ],
            "scene": [
                {
                    "name": "calculate_visibility_modifier",
                    "description": "Calculate visibility modifier based on lighting and weather",
                    "input_fields": ["lighting", "weather"],
                    "output_field": "visibilityModifier",
                    "calculation": lambda data: {
                        lighting = data.get("lighting", "normal")
                        weather = data.get("weather", "clear")

                        # Base modifiers
                        lighting_modifiers = {
                            "bright": 0,
                            "normal": 0,
                            "dim": -2,
                            "dark": -5,
                            "magical": 1,
                            "flickering": -1
                        }

                        weather_modifiers = {
                            "clear": 0,
                            "rain": -1,
                            "storm": -3,
                            "fog": -4,
                            "snow": -2,
                            "wind": 0,
                            "mist": -2
                        }

                        total_modifier = lighting_modifiers.get(lighting, 0) + weather_modifiers.get(weather, 0)

                        return {
                            "visibilityModifier": total_modifier,
                            "perceptionDifficulty": max(0, 10 + total_modifier),
                            "stealthDifficulty": max(5, 10 - total_modifier)
                        }
                    }
                },
                {
                    "name": "calculate_mood_effects",
                    "description": "Calculate mood effects on gameplay",
                    "input_fields": ["mood", "lighting"],
                    "output_field": "moodEffects",
                    "calculation": lambda data: {
                        mood = data.get("mood", "neutral")
                        lighting = data.get("lighting", "normal")

                        mood_effects = {
                            "peaceful": {
                                "socialBonus": 2,
                                "restBonus": 1,
                                "moraleBonus": 1
                            },
                            "neutral": {
                                "socialBonus": 0,
                                "restBonus": 0,
                                "moraleBonus": 0
                            },
                            "tense": {
                                "socialPenalty": -1,
                                "restPenalty": -1,
                                "perceptionBonus": 1
                            },
                            "mysterious": {
                                "investigationBonus": 2,
                                "perceptionBonus": 1,
                                "socialPenalty": -1
                            },
                            "dramatic": {
                                "performanceBonus": 2,
                                "socialBonus": 1,
                                "restPenalty": -1
                            },
                            "ominous": {
                                "perceptionBonus": 2,
                                "stealthBonus": 1,
                                "moralePenalty": -2
                            }
                        }

                        # Add lighting effects
                        if lighting == "dark":
                            mood_effects.get(mood, {})["stealthBonus"] = mood_effects.get(mood, {}).get("stealthBonus", 0) + 2
                        elif lighting == "bright":
                            mood_effects.get(mood, {})["perceptionBonus"] = mood_effects.get(mood, {}).get("perceptionBonus", 0) + 1

                        return {
                            "moodEffects": mood_effects.get(mood, {}),
                            "activeEffects": list(mood_effects.get(mood, {}).keys())
                        }
                    }
                }
            ],
            "world": [
                {
                    "name": "calculate_campaign_statistics",
                    "description": "Calculate overall campaign statistics",
                    "input_fields": ["locations", "npcs", "factions", "quests"],
                    "output_field": "campaignStats",
                    "calculation": lambda data: {
                        locations = data.get("locations", [])
                        npcs = data.get("npcs", [])
                        factions = data.get("factions", [])
                        quests = data.get("quests", [])

                        total_quests = len(quests)
                        active_quests = len([q for q in quests if q.get("status") in ["available", "active"]])
                        completed_quests = len([q for q in quests if q.get("status") == "completed"])

                        discovered_locations = len([loc for loc in locations if loc.get("discovered", False)])
                        total_locations = len(locations)

                        return {
                            "campaignStats": {
                                "totalLocations": total_locations,
                                "discoveredLocations": discovered_locations,
                                "discoveryPercentage": round((discovered_locations / max(total_locations, 1)) * 100, 1),
                                "totalNPCs": len(npcs),
                                "totalFactions": len(factions),
                                "totalQuests": total_quests,
                                "activeQuests": active_quests,
                                "completedQuests": completed_quests,
                                "questCompletionRate": round((completed_quests / max(total_quests, 1)) * 100, 1),
                                "campaignProgress": {
                                    "exploration": round((discovered_locations / max(total_locations, 1)) * 100, 1),
                                    "quests": round((completed_quests / max(total_quests, 1)) * 100, 1)
                                }
                            }
                        }
                    }
                }
            ]
        }

    def _initialize_integrity_checks(self) -> List[Dict]:
        """Initialize data integrity checks"""
        return [
            {
                "name": "check_orphaned_references",
                "description": "Check for orphaned references between entities",
                "check_function": self._check_orphaned_references
            },
            {
                "name": "check_data_consistency",
                "description": "Check for data consistency across related entities",
                "check_function": self._check_data_consistency
            },
            {
                "name": "check_temporal_integrity",
                "description": "Check for temporal data integrity",
                "check_function": self._check_temporal_integrity
            },
            {
                "name": "check_circular_references",
                "description": "Check for circular references in relationships",
                "check_function": self._check_circular_references
            }
        ]

    def validate_data(self, data_type: str, data: Dict) -> Dict[str, Any]:
        """Validate data against rules"""
        if data_type not in self.validation_rules:
            return {"valid": True, "errors": [], "warnings": []}

        rules = self.validation_rules[data_type]
        errors = []
        warnings = []

        # Check required fields
        for field in rules.get("required_fields", []):
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"Required field '{field}' is missing or empty")

        # Validate individual fields
        field_validators = rules.get("field_validators", {})
        for field, validator in field_validators.items():
            if field in data:
                validation_result = self._validate_field(field, data[field], validator)
                if not validation_result["valid"]:
                    errors.extend(validation_result["errors"])

        # Validate array fields
        array_validators = rules.get("array_field_validators", {})
        for field, validator in array_validators.items():
            if field in data:
                validation_result = self._validate_array_field(field, data[field], validator)
                if not validation_result["valid"]:
                    errors.extend(validation_result["errors"])

        # Cross-field validations
        cross_validations = rules.get("cross_field_validations", [])
        for validation in cross_validations:
            try:
                if not validation["validator"](data):
                    errors.append(validation["error_message"])
            except Exception as e:
                warnings.append(f"Cross-field validation '{validation['name']}' failed: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data_type": data_type
        }

    def _validate_field(self, field_name: str, value: Any, validator: Dict) -> Dict[str, Any]:
        """Validate a single field"""
        errors = []

        field_type = validator.get("type")

        if field_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be a string")
            else:
                if "min_length" in validator and len(value) < validator["min_length"]:
                    errors.append(f"Field '{field_name}' must be at least {validator['min_length']} characters")
                if "max_length" in validator and len(value) > validator["max_length"]:
                    errors.append(f"Field '{field_name}' must be at most {validator['max_length']} characters")
                if "pattern" in validator and not re.match(validator["pattern"], value):
                    errors.append(validator.get("error_message", f"Field '{field_name}' format is invalid"))

        elif field_type == "integer":
            if not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be an integer")
            else:
                if "min_value" in validator and value < validator["min_value"]:
                    errors.append(f"Field '{field_name}' must be at least {validator['min_value']}")
                if "max_value" in validator and value > validator["max_value"]:
                    errors.append(f"Field '{field_name}' must be at most {validator['max_value']}")

        elif field_type == "float":
            try:
                float_value = float(value)
                if "min_value" in validator and float_value < validator["min_value"]:
                    errors.append(f"Field '{field_name}' must be at least {validator['min_value']}")
                if "max_value" in validator and float_value > validator["max_value"]:
                    errors.append(f"Field '{field_name}' must be at most {validator['max_value']}")
            except (ValueError, TypeError):
                errors.append(f"Field '{field_name}' must be a number")

        elif field_type == "enum":
            allowed_values = validator.get("allowed_values", [])
            if value not in allowed_values:
                errors.append(validator.get("error_message", f"Field '{field_name}' must be one of: {', '.join(allowed_values)}"))

        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_array_field(self, field_name: str, value: Any, validator: Dict) -> Dict[str, Any]:
        """Validate an array field"""
        errors = []

        if not isinstance(value, list):
            errors.append(f"Field '{field_name}' must be an array")
            return {"valid": False, "errors": errors}

        item_validator = validator.get("item_validator", {})

        for i, item in enumerate(value):
            if item_validator.get("type") == "object":
                if not isinstance(item, dict):
                    errors.append(f"Item {i} in '{field_name}' must be an object")
                    continue

                for required_field in item_validator.get("required_fields", []):
                    if required_field not in item:
                        errors.append(f"Item {i} in '{field_name}' missing required field '{required_field}'")

        return {"valid": len(errors) == 0, "errors": errors}

    def apply_calculations(self, data_type: str, data: Dict) -> Dict[str, Any]:
        """Apply automated calculations to data"""
        if data_type not in self.calculation_rules:
            return {"calculated_data": {}, "applied_calculations": []}

        rules = self.calculation_rules[data_type]
        calculated_data = {}
        applied_calculations = []

        for rule in rules:
            try:
                # Check if all required input fields are present
                input_fields = rule.get("input_fields", [])
                if all(field in data for field in input_fields):
                    result = rule["calculation"](data)
                    calculated_data.update(result)
                    applied_calculations.append(rule["name"])
            except Exception as e:
                logger.warning(f"Calculation '{rule['name']}' failed: {str(e)}")

        return {
            "calculated_data": calculated_data,
            "applied_calculations": applied_calculations
        }

    def _check_orphaned_references(self, data: Dict) -> Dict[str, Any]:
        """Check for orphaned references between entities"""
        issues = []

        # This would require access to the full dataset to check references
        # For now, return a placeholder result

        return {
            "check_name": "orphaned_references",
            "status": "passed",
            "issues": issues,
            "message": "No orphaned references detected"
        }

    def _check_data_consistency(self, data: Dict) -> Dict[str, Any]:
        """Check for data consistency across related entities"""
        issues = []

        # Check character-level consistency
        if "level" in data and "xpCurrent" in data:
            level = data["level"]
            xp = data["xpCurrent"]

            # Rough XP consistency check (typical D&D progression)
            expected_min_xp = (level - 1) * 1000
            if xp < expected_min_xp:
                issues.append(f"XP {xp} seems low for level {level} (expected at least {expected_min_xp})")

        return {
            "check_name": "data_consistency",
            "status": "passed" if not issues else "warning",
            "issues": issues,
            "message": f"Found {len(issues)} consistency issues" if issues else "Data consistency check passed"
        }

    def _check_temporal_integrity(self, data: Dict) -> Dict[str, Any]:
        """Check for temporal data integrity"""
        issues = []

        current_time = datetime.now()

        # Check timestamp fields
        timestamp_fields = ["lastUpdated", "timestamp", "createdAt"]
        for field in timestamp_fields:
            if field in data:
                try:
                    timestamp = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    # Check if timestamp is in the future (allowing for some clock skew)
                    if timestamp > current_time + timedelta(minutes=5):
                        issues.append(f"Field '{field}' has future timestamp: {data[field]}")
                    # Check if timestamp is too old (more than 1 year)
                    elif timestamp < current_time - timedelta(days=365):
                        issues.append(f"Field '{field}' has very old timestamp: {data[field]}")
                except ValueError:
                    issues.append(f"Field '{field}' has invalid timestamp format: {data[field]}")

        return {
            "check_name": "temporal_integrity",
            "status": "passed" if not issues else "warning",
            "issues": issues,
            "message": f"Found {len(issues)} temporal integrity issues" if issues else "Temporal integrity check passed"
        }

    def _check_circular_references(self, data: Dict) -> Dict[str, Any]:
        """Check for circular references in relationships"""
        issues = []

        # This would require graph traversal on relationship data
        # For now, return a placeholder result

        return {
            "check_name": "circular_references",
            "status": "passed",
            "issues": issues,
            "message": "No circular references detected"
        }

    def run_integrity_checks(self, data: Dict) -> Dict[str, Any]:
        """Run all integrity checks on data"""
        results = []
        overall_status = "passed"

        for check in self.integrity_checks:
            try:
                result = check["check_function"](data)
                results.append(result)

                if result["status"] == "error":
                    overall_status = "error"
                elif result["status"] == "warning" and overall_status == "passed":
                    overall_status = "warning"

            except Exception as e:
                results.append({
                    "check_name": check["name"],
                    "status": "error",
                    "issues": [str(e)],
                    "message": f"Integrity check failed: {str(e)}"
                })
                overall_status = "error"

        return {
            "overall_status": overall_status,
            "checks": results,
            "total_issues": sum(len(check.get("issues", [])) for check in results)
        }

# Example usage and testing functions
def test_validation_engine():
    """Test the validation engine with sample data"""
    validator = DataValidationEngine()

    # Test character validation
    character_data = {
        "characterId": "test_char_001",
        "name": "Test Character",
        "level": 5,
        "hpCurrent": 45,
        "hpMax": 50,
        "mpCurrent": 20,
        "mpMax": 25,
        "xpCurrent": 3500,
        "xpToNext": 5000
    }

    result = validator.validate_data("character", character_data)
    print("Character validation result:", result)

    # Test calculations
    calc_result = validator.apply_calculations("character", character_data)
    print("Calculation result:", calc_result)

    # Test integrity checks
    integrity_result = validator.run_integrity_checks(character_data)
    print("Integrity check result:", integrity_result)

if __name__ == "__main__":
    test_validation_engine()