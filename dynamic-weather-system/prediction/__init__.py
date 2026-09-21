"""
Weather Prediction System

This module handles weather forecasting, NPC predictions, magical divination,
and pattern recognition for weather prediction.
"""

from .forecast_engine import ForecastEngine
from .npc_predictions import NPCWeatherPredictions
from .magical_divination import MagicalDivination
from .pattern_recognition import WeatherPatternRecognition
from .almanac_system import AlmanacSystem
from .long_range_forecasting import LongRangeForecasting

__all__ = [
    "ForecastEngine",
    "NPCWeatherPredictions",
    "MagicalDivination",
    "WeatherPatternRecognition",
    "AlmanacSystem",
    "LongRangeForecasting"
]