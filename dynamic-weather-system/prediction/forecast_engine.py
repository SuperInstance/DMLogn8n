"""
Weather Forecast Engine

Core forecasting system that generates weather predictions using
meteorological models, historical data, and pattern recognition.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from ..core.weather_state import WeatherState
from ..core.weather_types import WeatherType, WeatherSeverity, Season, ClimateZone
from ..core.climate_patterns import ClimatePatterns
from ..algorithms.weather_simulation import WeatherSimulation

@dataclass
class WeatherForecast:
    """Represents a weather forecast for a specific time period."""

    forecast_time: datetime
    weather_type: WeatherType
    severity: WeatherSeverity
    temperature_min: float
    temperature_max: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation_probability: float
    precipitation_amount: float
    visibility: float
    pressure: float
    confidence: float  # 0-1
    special_conditions: List[str] = field(default_factory=list)
    hazards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert forecast to dictionary."""

        return {
            'forecast_time': self.forecast_time.isoformat(),
            'weather_type': self.weather_type.value,
            'severity': self.severity.value,
            'temperature_min': self.temperature_min,
            'temperature_max': self.temperature_max,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'precipitation_probability': self.precipitation_probability,
            'precipitation_amount': self.precipitation_amount,
            'visibility': self.visibility,
            'pressure': self.pressure,
            'confidence': self.confidence,
            'special_conditions': self.special_conditions,
            'hazards': self.hazards
        }

@dataclass
class ForecastTrend:
    """Represents weather trend analysis."""

    trend_type: str  # "improving", "worsening", "stable", "changing"
    temperature_trend: str  # "warming", "cooling", "stable"
    precipitation_trend: str  # "increasing", "decreasing", "stable"
    pressure_trend: str  # "rising", "falling", "stable"
    confidence: float
    description: str

class ForecastEngine:
    """Advanced weather forecasting engine."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Initialize systems
        self.climate_patterns = ClimatePatterns({})
        self.weather_simulation = WeatherSimulation(self.config.get('simulation', {}))

        # Forecast parameters
        self.short_range_hours = self.config.get('short_range_hours', 24)
        self.medium_range_hours = self.config.get('medium_range_hours', 72)
        self.long_range_hours = self.config.get('long_range_hours', 168)  # 1 week

        # Forecast accuracy decay
        self.accuracy_decay_rate = self.config.get('accuracy_decay_rate', 0.05)  # 5% per hour

        # Historical data
        self.historical_forecasts: List[WeatherForecast] = []
        self.forecast_accuracy: Dict[str, float] = {}

    def generate_forecast(self, current_state: WeatherState,
                          forecast_hours: int = 24,
                          climate_zone: ClimateZone = ClimateZone.TEMPERATE) -> List[WeatherForecast]:
        """Generate weather forecast for specified period."""

        forecasts = []
        forecast_state = current_state.copy()
        base_confidence = 0.9

        # Generate forecasts in 3-hour intervals
        interval_hours = 3
        for hour in range(0, forecast_hours, interval_hours):
            forecast_time = current_state.timestamp + timedelta(hours=hour)

            # Calculate confidence decay
            confidence = max(0.1, base_confidence - (hour * self.accuracy_decay_rate / 60))

            # Simulate weather for this time point
            forecast_state = self.weather_simulation.simulate_step(
                forecast_state, interval_hours * 60,
                climate_zone, current_state.altitude, current_state.season,
                is_forecast=True
            )
            forecast_state.timestamp = forecast_time

            # Add some randomness to simulate forecast uncertainty
            forecast_state = self._add_forecast_uncertainty(forecast_state, confidence)

            # Create forecast object
            forecast = self._create_forecast_from_state(forecast_state, confidence)
            forecasts.append(forecast)

        # Apply consistency checks and smooth transitions
        forecasts = self._apply_forecast_consistency(forecasts)

        # Store for accuracy tracking
        self.historical_forecasts.extend(forecasts)

        return forecasts

    def _add_forecast_uncertainty(self, state: WeatherState, confidence: float) -> WeatherState:
        """Add uncertainty to forecast based on confidence level."""

        uncertainty_factor = 1.0 - confidence

        # Temperature uncertainty
        temp_uncertainty = random.gauss(0, uncertainty_factor * 5)
        state.temperature += temp_uncertainty

        # Humidity uncertainty
        humidity_uncertainty = random.gauss(0, uncertainty_factor * 0.2)
        state.humidity = max(0, min(1, state.humidity + humidity_uncertainty))

        # Wind speed uncertainty
        wind_uncertainty = random.gauss(0, uncertainty_factor * 10)
        state.wind_speed = max(0, state.wind_speed + wind_uncertainty)

        # Pressure uncertainty
        pressure_uncertainty = random.gauss(0, uncertainty_factor * 10)
        state.pressure += pressure_uncertainty

        # Weather type uncertainty for lower confidence
        if confidence < 0.7 and random.random() < uncertainty_factor:
            # Chance of weather type change
            state.weather_type = self._select_alternate_weather_type(state.weather_type)

        return state

    def _select_alternate_weather_type(self, current_type: WeatherType) -> WeatherType:
        """Select an alternate weather type based on current conditions."""

        # Define related weather types
        weather_families = {
            WeatherType.CLEAR: [WeatherType.PARTLY_CLOUDY, WeatherType.OVERCAST],
            WeatherType.PARTLY_CLOUDY: [WeatherType.CLEAR, WeatherType.OVERCAST, WeatherType.LIGHT_RAIN],
            WeatherType.OVERCAST: [WeatherType.PARTLY_CLOUDY, WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN],
            WeatherType.LIGHT_RAIN: [WeatherType.OVERCAST, WeatherType.MODERATE_RAIN, WeatherType.DRIZZLE],
            WeatherType.MODERATE_RAIN: [WeatherType.LIGHT_RAIN, WeatherType.HEAVY_RAIN, WeatherType.THUNDERSTORM],
            WeatherType.HEAVY_RAIN: [WeatherType.MODERATE_RAIN, WeatherType.THUNDERSTORM, WeatherType.HAILSTORM],
            WeatherType.LIGHT_SNOW: [WeatherType.OVERCAST, WeatherType.MODERATE_SNOW, WeatherType.SLEET],
            WeatherType.MODERATE_SNOW: [WeatherType.LIGHT_SNOW, WeatherType.HEAVY_SNOW, WeatherType.BLIZZARD],
            WeatherType.HEAVY_SNOW: [WeatherType.MODERATE_SNOW, WeatherType.BLIZZARD, WeatherType.SLEET],
            WeatherType.THUNDERSTORM: [WeatherType.HEAVY_RAIN, WeatherType.SEVERE_THUNDERSTORM],
            WeatherType.LIGHT_FOG: [WeatherType.MODERATE_FOG, WeatherType.OVERCAST],
            WeatherType.MODERATE_FOG: [WeatherType.LIGHT_FOG, WeatherType.DENSE_FOG, WeatherType.OVERCAST],
        }

        possible_alternates = weather_families.get(current_type, [current_type])
        return random.choice(possible_alternates)

    def _create_forecast_from_state(self, state: WeatherState, confidence: float) -> WeatherForecast:
        """Create WeatherForecast object from WeatherState."""

        # Calculate temperature range based on diurnal variation
        diurnal_range = self._calculate_diurnal_temperature_range(state)
        temp_min = state.temperature - diurnal_range / 2
        temp_max = state.temperature + diurnal_range / 2

        # Calculate precipitation probability
        precip_prob = self._calculate_precipitation_probability(state)

        # Identify special conditions and hazards
        special_conditions = self._identify_special_conditions(state)
        hazards = self._identify_hazards(state)

        return WeatherForecast(
            forecast_time=state.timestamp,
            weather_type=state.weather_type,
            severity=state.severity,
            temperature_min=temp_min,
            temperature_max=temp_max,
            humidity=state.humidity,
            wind_speed=state.wind_speed,
            wind_direction=state.wind_direction.value,
            precipitation_probability=precip_prob,
            precipitation_amount=state.precipitation_intensity,
            visibility=state.visibility,
            pressure=state.pressure,
            confidence=confidence,
            special_conditions=special_conditions,
            hazards=hazards
        )

    def _calculate_diurnal_temperature_range(self, state: WeatherState) -> float:
        """Calculate expected diurnal temperature variation."""

        base_range = 8.0  # Base 8°C daily variation

        # Climate zone adjustments
        climate_adjustments = {
            ClimateZone.TROPICAL: 0.5,    # Less variation
            ClimateZone.TEMPERATE: 1.0,   # Normal variation
            ClimateZone.DESERT: 2.0,      # More variation
            ClimateZone.ARCTIC: 0.3,      # Very little variation
            ClimateZone.MOUNTAINOUS: 1.2, # More variation
            ClimateZone.COASTAL: 0.7,     # Less variation
        }

        adjustment = climate_adjustments.get(state.climate_zone, 1.0)

        # Seasonal adjustments
        if state.season in [Season.WINTER, Season.SUMMER]:
            adjustment *= 1.2  # More variation in extreme seasons

        # Weather type adjustments
        if state.weather_type in [WeatherType.OVERCAST, WeatherType.HEAVY_RAIN, WeatherType.BLIZZARD]:
            adjustment *= 0.5  # Less variation with cloud cover

        return base_range * adjustment

    def _calculate_precipitation_probability(self, state: WeatherState) -> float:
        """Calculate probability of precipitation."""

        base_prob = 0.0

        # Weather type base probability
        if state.weather_type in [WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN, WeatherType.HEAVY_RAIN]:
            base_prob = 0.8
        elif state.weather_type in [WeatherType.LIGHT_SNOW, WeatherType.MODERATE_SNOW, WeatherType.HEAVY_SNOW]:
            base_prob = 0.8
        elif state.weather_type in [WeatherType.THUNDERSTORM, WeatherType.SEVERE_THUNDERSTORM]:
            base_prob = 0.95
        elif state.weather_type == WeatherType.DRIZZLE:
            base_prob = 0.6
        elif state.weather_type in [WeatherType.PARTLY_CLOUDY, WeatherType.OVERCAST]:
            base_prob = 0.3
        elif state.weather_type == WeatherType.CLEAR:
            base_prob = 0.05

        # Humidity adjustment
        if state.humidity > 0.8:
            base_prob = min(1.0, base_prob * 1.3)
        elif state.humidity < 0.4:
            base_prob *= 0.7

        # Pressure adjustment
        if state.pressure < 1000:  # Low pressure
            base_prob = min(1.0, base_prob * 1.4)
        elif state.pressure > 1020:  # High pressure
            base_prob *= 0.6

        return base_prob

    def _identify_special_conditions(self, state: WeatherState) -> List[str]:
        """Identify special weather conditions."""

        conditions = []

        # Temperature extremes
        if state.temperature > 35:
            conditions.append("extreme_heat")
        elif state.temperature < -20:
            conditions.append("extreme_cold")

        # Wind conditions
        if state.wind_speed > 50:
            conditions.append("strong_winds")
        elif state.wind_speed > 30:
            conditions.append("moderate_winds")

        # Visibility conditions
        if state.visibility < 1.0:
            conditions.append("severely_reduced_visibility")
        elif state.visibility < 5.0:
            conditions.append("reduced_visibility")

        # Pressure systems
        if state.pressure < 990:
            conditions.append("storm_system")
        elif state.pressure > 1030:
            conditions.append("high_pressure_system")

        # Magical conditions
        if state.magical_intensity > 0.5:
            conditions.append("magical_weather")

        return conditions

    def _identify_hazards(self, state: WeatherState) -> List[str]:
        """Identify weather-related hazards."""

        hazards = []

        # Temperature hazards
        feels_like = state.get_feels_like_temperature()
        if feels_like < -25:
            hazards.append("life-threatening_cold")
        elif feels_like < -15:
            hazards.append("dangerous_cold")
        elif feels_like > 45:
            hazards.append("life-threatening_heat")
        elif feels_like > 38:
            hazards.append("dangerous_heat")

        # Wind hazards
        if state.wind_speed > 70:
            hazards.append("hurricane_force_winds")
        elif state.wind_speed > 60:
            hazards.append("dangerous_winds")

        # Precipitation hazards
        if state.weather_type == WeatherType.BLIZZARD:
            hazards.append("whiteout_conditions")
        elif state.weather_type == WeatherType.SEVERE_THUNDERSTORM:
            hazards.append("severe_thunderstorm")
        elif state.weather_type == WeatherType.HAILSTORM:
            hazards.append("damaging_hail")

        # Visibility hazards
        if state.visibility < 0.5:
            hazards.append("near_zero_visibility")

        # Magical hazards
        if state.magical_intensity > 0.8:
            hazards.append("dangerous_magical_conditions")

        return hazards

    def _apply_forecast_consistency(self, forecasts: List[WeatherForecast]) -> List[WeatherForecast]:
        """Apply consistency checks and smooth transitions to forecasts."""

        if len(forecasts) < 2:
            return forecasts

        # Smooth temperature transitions
        for i in range(1, len(forecasts)):
            prev_forecast = forecasts[i-1]
            curr_forecast = forecasts[i]

            # Smooth temperature changes
            temp_change_limit = 8.0  # Maximum 8°C change per 3 hours
            temp_diff_min = curr_forecast.temperature_min - prev_forecast.temperature_min
            temp_diff_max = curr_forecast.temperature_max - prev_forecast.temperature_max

            if abs(temp_diff_min) > temp_change_limit:
                curr_forecast.temperature_min = prev_forecast.temperature_min + \
                    (temp_change_limit if temp_diff_min > 0 else -temp_change_limit)

            if abs(temp_diff_max) > temp_change_limit:
                curr_forecast.temperature_max = prev_forecast.temperature_max + \
                    (temp_change_limit if temp_diff_max > 0 else -temp_change_limit)

            # Smooth pressure changes
            pressure_change_limit = 15.0  # Maximum 15 mbar change per 3 hours
            pressure_diff = curr_forecast.pressure - prev_forecast.pressure

            if abs(pressure_diff) > pressure_change_limit:
                curr_forecast.pressure = prev_forecast.pressure + \
                    (pressure_change_limit if pressure_diff > 0 else -pressure_change_limit)

            # Ensure logical weather progressions
            curr_forecast = self._ensure_logical_progression(prev_forecast, curr_forecast)

        return forecasts

    def _ensure_logical_progression(self, prev: WeatherForecast, curr: WeatherForecast) -> WeatherForecast:
        """Ensure weather changes follow logical progressions."""

        # Rain shouldn't suddenly appear from clear skies without transition
        if prev.weather_type == WeatherType.CLEAR and \
           curr.weather_type in [WeatherType.HEAVY_RAIN, WeatherType.THUNDERSTORM]:
            # Insert intermediate step
            curr.weather_type = WeatherType.MODERATE_RAIN
            curr.confidence *= 0.8  # Reduced confidence due to unusual progression

        # Similar logic for other dramatic transitions
        if prev.weather_type == WeatherType.CLEAR and curr.weather_type == WeatherType.BLIZZARD:
            curr.weather_type = WeatherType.OVERCAST
            curr.confidence *= 0.7

        return curr

    def analyze_forecast_trends(self, forecasts: List[WeatherForecast]) -> ForecastTrend:
        """Analyze trends in the forecast data."""

        if len(forecasts) < 2:
            return ForecastTrend(
                trend_type="stable",
                temperature_trend="stable",
                precipitation_trend="stable",
                pressure_trend="stable",
                confidence=0.5,
                description="Insufficient data for trend analysis"
            )

        # Calculate temperature trend
        temp_changes = []
        for i in range(1, len(forecasts)):
            temp_change = forecasts[i].temperature_max - forecasts[i-1].temperature_max
            temp_changes.append(temp_change)

        avg_temp_change = sum(temp_changes) / len(temp_changes)
        if avg_temp_change > 2:
            temp_trend = "warming"
        elif avg_temp_change < -2:
            temp_trend = "cooling"
        else:
            temp_trend = "stable"

        # Calculate precipitation trend
        precip_changes = []
        for i in range(1, len(forecasts)):
            precip_change = forecasts[i].precipitation_probability - forecasts[i-1].precipitation_probability
            precip_changes.append(precip_change)

        avg_precip_change = sum(precip_changes) / len(precip_changes)
        if avg_precip_change > 0.1:
            precip_trend = "increasing"
        elif avg_precip_change < -0.1:
            precip_trend = "decreasing"
        else:
            precip_trend = "stable"

        # Calculate pressure trend
        pressure_changes = []
        for i in range(1, len(forecasts)):
            pressure_change = forecasts[i].pressure - forecasts[i-1].pressure
            pressure_changes.append(pressure_change)

        avg_pressure_change = sum(pressure_changes) / len(pressure_changes)
        if avg_pressure_change > 2:
            pressure_trend = "rising"
        elif avg_pressure_change < -2:
            pressure_trend = "falling"
        else:
            pressure_trend = "stable"

        # Determine overall trend
        if precip_trend == "increasing" and pressure_trend == "falling":
            overall_trend = "worsening"
        elif precip_trend == "decreasing" and pressure_trend == "rising":
            overall_trend = "improving"
        elif temp_trend == "stable" and precip_trend == "stable" and pressure_trend == "stable":
            overall_trend = "stable"
        else:
            overall_trend = "changing"

        # Calculate confidence
        avg_confidence = sum(f.confidence for f in forecasts) / len(forecasts)

        # Generate description
        description = self._generate_trend_description(
            overall_trend, temp_trend, precip_trend, pressure_trend
        )

        return ForecastTrend(
            trend_type=overall_trend,
            temperature_trend=temp_trend,
            precipitation_trend=precip_trend,
            pressure_trend=pressure_trend,
            confidence=avg_confidence,
            description=description
        )

    def _generate_trend_description(self, overall: str, temp: str,
                                  precip: str, pressure: str) -> str:
        """Generate human-readable trend description."""

        descriptions = []

        if overall == "worsening":
            descriptions.append("Weather conditions are expected to deteriorate")
        elif overall == "improving":
            descriptions.append("Weather conditions are expected to improve")
        elif overall == "stable":
            descriptions.append("Weather conditions expected to remain relatively stable")
        else:
            descriptions.append("Weather conditions expected to change")

        if temp == "warming":
            descriptions.append("with rising temperatures")
        elif temp == "cooling":
            descriptions.append("with falling temperatures")

        if precip == "increasing":
            descriptions.append("and increasing precipitation chances")
        elif precip == "decreasing":
            descriptions.append("and decreasing precipitation chances")

        if pressure == "falling":
            descriptions.append("as a low pressure system approaches")
        elif pressure == "rising":
            descriptions.append("as a high pressure system builds")

        return " ".join(descriptions) + "."

    def calculate_forecast_accuracy(self, forecasts: List[WeatherForecast],
                                  actual_weather: List[WeatherState]) -> Dict[str, float]:
        """Calculate accuracy of forecasts against actual weather."""

        if len(forecasts) != len(actual_weather):
            return {"error": "Forecast and actual data length mismatch"}

        accuracy_metrics = {
            "weather_type_accuracy": 0.0,
            "temperature_accuracy": 0.0,
            "wind_speed_accuracy": 0.0,
            "precipitation_accuracy": 0.0,
            "overall_accuracy": 0.0
        }

        correct_predictions = 0
        total_temp_error = 0.0
        total_wind_error = 0.0
        correct_precip = 0

        for forecast, actual in zip(forecasts, actual_weather):
            # Weather type accuracy
            if forecast.weather_type == actual.weather_type:
                correct_predictions += 1

            # Temperature accuracy (within 3°C)
            temp_error = abs(forecast.temperature_max - actual.temperature)
            if temp_error <= 3.0:
                total_temp_error += 1.0
            else:
                total_temp_error += max(0, 1.0 - (temp_error - 3.0) / 10.0)

            # Wind speed accuracy (within 10 km/h)
            wind_error = abs(forecast.wind_speed - actual.wind_speed)
            if wind_error <= 10:
                total_wind_error += 1.0
            else:
                total_wind_error += max(0, 1.0 - (wind_error - 10) / 30.0)

            # Precipitation accuracy
            precip_forecast = forecast.precipitation_probability > 0.5
            precip_actual = actual.precipitation_intensity > 0.1
            if precip_forecast == precip_actual:
                correct_precip += 1

        # Calculate percentages
        total_forecasts = len(forecasts)
        accuracy_metrics["weather_type_accuracy"] = correct_predictions / total_forecasts
        accuracy_metrics["temperature_accuracy"] = total_temp_error / total_forecasts
        accuracy_metrics["wind_speed_accuracy"] = total_wind_error / total_forecasts
        accuracy_metrics["precipitation_accuracy"] = correct_precip / total_forecasts
        accuracy_metrics["overall_accuracy"] = (
            accuracy_metrics["weather_type_accuracy"] * 0.3 +
            accuracy_metrics["temperature_accuracy"] * 0.3 +
            accuracy_metrics["wind_speed_accuracy"] * 0.2 +
            accuracy_metrics["precipitation_accuracy"] * 0.2
        )

        return accuracy_metrics

    def get_forecast_summary(self, forecasts: List[WeatherForecast]) -> Dict[str, Any]:
        """Get summary statistics for forecast period."""

        if not forecasts:
            return {"error": "No forecasts provided"}

        # Temperature statistics
        temps_min = [f.temperature_min for f in forecasts]
        temps_max = [f.temperature_max for f in forecasts]

        # Weather type frequency
        weather_counts = {}
        for f in forecasts:
            wtype = f.weather_type.value
            weather_counts[wtype] = weather_counts.get(wtype, 0) + 1

        # Hazard identification
        all_hazards = []
        for f in forecasts:
            all_hazards.extend(f.hazards)
        hazard_counts = {}
        for hazard in all_hazards:
            hazard_counts[hazard] = hazard_counts.get(hazard, 0) + 1

        # Average conditions
        avg_confidence = sum(f.confidence for f in forecasts) / len(forecasts)
        avg_wind_speed = sum(f.wind_speed for f in forecasts) / len(forecasts)
        avg_humidity = sum(f.humidity for f in forecasts) / len(forecasts)

        return {
            "period_hours": len(forecasts) * 3,
            "temperature_range": {
                "minimum": min(temps_min),
                "maximum": max(temps_max),
                "average_high": sum(temps_max) / len(temps_max),
                "average_low": sum(temps_min) / len(temps_min)
            },
            "weather_distribution": weather_counts,
            "hazard_summary": hazard_counts,
            "average_conditions": {
                "confidence": avg_confidence,
                "wind_speed": avg_wind_speed,
                "humidity": avg_humidity
            },
            "significant_events": [
                f.hazards for f in forecasts if f.hazards
            ]
        }