"""
Dynamic Weather System - Core Module

This module provides the core weather simulation engine for DMlogn8n.
"""

from .weather_engine import WeatherEngine
from .weather_types import WeatherType, WeatherSeverity, Season, ClimateZone
from .weather_state import WeatherState
from .weather_events import WeatherEvent, ExtremeWeatherEvent, MagicalWeatherEvent
from .atmospheric_conditions import AtmosphericConditions
from .climate_patterns import ClimatePatterns

__version__ = "1.0.0"
__author__ = "DMlogn8n Dynamic Weather System"

__all__ = [
    "WeatherEngine",
    "WeatherType",
    "WeatherSeverity",
    "Season",
    "ClimateZone",
    "WeatherState",
    "WeatherEvent",
    "ExtremeWeatherEvent",
    "MagicalWeatherEvent",
    "AtmosphericConditions",
    "ClimatePatterns"
]