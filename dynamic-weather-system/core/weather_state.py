"""
Weather State Management

Manages the current state of weather conditions and provides methods for
state transitions and updates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import math

from .weather_types import (
    WeatherType, WeatherSeverity, Season, ClimateZone,
    WindDirection, CloudCover, PrecipitationType, MagicalWeatherSource
)
from .atmospheric_conditions import AtmosphericConditions

@dataclass
class WeatherState:
    """Represents the current state of weather at a specific location and time."""

    # Basic weather information
    weather_type: WeatherType = WeatherType.CLEAR
    severity: WeatherSeverity = WeatherSeverity.CALM
    temperature: float = 20.0  # Celsius
    humidity: float = 0.5  # 0-1
    pressure: float = 1013.25  # millibars
    wind_speed: float = 5.0  # km/h
    wind_direction: WindDirection = WindDirection.N
    visibility: float = 10.0  # kilometers

    # Atmospheric conditions
    cloud_cover: CloudCover = CloudCover.CLEAR
    precipitation_type: PrecipitationType = PrecipitationType.NONE
    precipitation_intensity: float = 0.0  # mm/hour
    snow_depth: float = 0.0  # cm

    # Environmental context
    location: str = "unknown"
    altitude: float = 0.0  # meters
    climate_zone: ClimateZone = ClimateZone.TEMPERATE
    season: Season = Season.SUMMER

    # Time information
    timestamp: datetime = field(default_factory=datetime.now)
    duration: timedelta = field(default_factory=lambda: timedelta(hours=1))

    # Magical conditions
    magical_source: Optional[MagicalWeatherSource] = None
    magical_intensity: float = 0.0  # 0-1
    magical_effects: List[str] = field(default_factory=list)

    # Extended atmospheric data
    atmospheric_conditions: AtmosphericConditions = field(default_factory=AtmosphericConditions)

    # Historical data
    previous_states: List['WeatherState'] = field(default_factory=list)
    transition_data: Dict[str, Any] = field(default_factory=dict)

    # Weather event tracking
    active_events: List[str] = field(default_factory=list)
    forecast_confidence: float = 0.8  # 0-1

    def __post_init__(self):
        """Initialize derived values after dataclass creation."""
        self.update_derived_values()

    def update_derived_values(self):
        """Update calculated values based on current state."""
        self.update_visibility()
        self.update_atmospheric_pressure()
        self.update_precipitation_type()

    def update_visibility(self):
        """Calculate visibility based on weather conditions."""

        base_visibility = 10.0  # Base visibility in clear conditions

        # Visibility reductions
        visibility_penalties = {
            WeatherType.DENSE_FOG: 8.5,
            WeatherType.MODERATE_FOG: 6.0,
            WeatherType.LIGHT_FOG: 2.5,
            WeatherType.HEAVY_RAIN: 4.0,
            WeatherType.MODERATE_RAIN: 2.0,
            WeatherType.HEAVY_SNOW: 7.0,
            WeatherType.BLIZZARD: 9.5,
            WeatherType.DUST_STORM: 6.5,
            WeatherType.SANDSTORM: 7.0,
            WeatherType.WILDFIRE_SMOKE: 5.0,
            WeatherType.VOLCANIC_ASH: 8.0,
            WeatherType.UNDEAD_FOG: 7.5,
        }

        # Apply weather type penalty
        if self.weather_type in visibility_penalties:
            self.visibility = max(0.1, base_visibility - visibility_penalties[self.weather_type])
        else:
            self.visibility = base_visibility

        # Additional reductions from other factors
        if self.precipitation_intensity > 0:
            self.visibility *= max(0.3, 1.0 - (self.precipitation_intensity / 50.0))

        if self.humidity > 0.8:
            self.visibility *= 0.9

        if self.magical_intensity > 0:
            self.visibility *= max(0.2, 1.0 - self.magical_intensity * 0.5)

    def update_atmospheric_pressure(self):
        """Update atmospheric pressure based on conditions."""

        base_pressure = 1013.25  # Sea level standard pressure

        # Altitude adjustment
        altitude_adjustment = -0.12 * self.altitude  # Simple barometric formula
        self.pressure = base_pressure + altitude_adjustment

        # Weather system adjustments
        pressure_adjustments = {
            WeatherType.THUNDERSTORM: -15.0,
            WeatherType.SEVERE_THUNDERSTORM: -25.0,
            WeatherType.HURRICANE: -35.0,
            WeatherType.BLIZZARD: -20.0,
            WeatherType.GALE_FORCE: -10.0,
            WeatherType.CLEAR: 2.0,
            WeatherType.OVERCAST: -5.0,
        }

        if self.weather_type in pressure_adjustments:
            self.pressure += pressure_adjustments[self.weather_type]

        # Magical pressure effects
        if self.magical_intensity > 0:
            self.pressure += self.magical_intensity * 20.0 * (1 if self.magical_source == MagicalWeatherSource.DIVINE_POWER else -1)

    def update_precipitation_type(self):
        """Determine precipitation type based on temperature and conditions."""

        if self.weather_type in [WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN, WeatherType.HEAVY_RAIN]:
            if self.temperature < 0:
                self.precipitation_type = PrecipitationType.SNOW
            elif self.temperature < 2:
                self.precipitation_type = PrecipitationType.SLEET
            elif self.temperature < 4:
                self.precipitation_type = PrecipitationType.FREEZING_RAIN
            else:
                self.precipitation_type = PrecipitationType.RAIN
        elif self.weather_type in [WeatherType.LIGHT_SNOW, WeatherType.MODERATE_SNOW, WeatherType.HEAVY_SNOW]:
            self.precipitation_type = PrecipitationType.SNOW
        elif self.weather_type == WeatherType.HAILSTORM:
            self.precipitation_type = PrecipitationType.HAIL
        elif self.magical_source is not None:
            self.precipitation_type = PrecipitationType.MAGICAL
        else:
            self.precipitation_type = PrecipitationType.NONE

        # Update precipitation intensity based on weather type and severity
        if self.precipitation_type != PrecipitationType.NONE:
            intensity_map = {
                WeatherSeverity.CALM: 0.0,
                WeatherSeverity.MILD: 0.5,
                WeatherSeverity.MODERATE: 2.0,
                WeatherSeverity.SEVERE: 8.0,
                WeatherSeverity.EXTREME: 20.0,
                WeatherSeverity.CATASTROPHIC: 50.0,
            }
            self.precipitation_intensity = intensity_map.get(self.severity, 0.0)

    def get_feels_like_temperature(self) -> float:
        """Calculate apparent temperature considering wind chill and heat index."""

        temp = self.temperature

        # Wind chill calculation
        if temp < 10 and self.wind_speed > 5:
            wind_chill = 13.12 + 0.6215 * temp - 11.37 * (self.wind_speed ** 0.16) + 0.3965 * temp * (self.wind_speed ** 0.16)
            temp = min(temp, wind_chill)

        # Heat index calculation
        if temp > 27 and self.humidity > 0.4:
            hi = (-42.379 + 2.04901523 * temp + 10.14333127 * self.humidity
                  - 0.22475541 * temp * self.humidity - 0.00683783 * temp * temp
                  - 0.05481717 * self.humidity * self.humidity + 0.00122874 * temp * temp * self.humidity
                  + 0.00085282 * temp * self.humidity * self.humidity - 0.00000199 * temp * temp * self.humidity * self.humidity)
            temp = max(temp, hi)

        # Magical temperature effects
        if self.magical_intensity > 0:
            if self.magical_source == MagicalWeatherSource.SHADOW_MAGIC:
                temp -= self.magical_intensity * 10
            elif self.magical_source == MagicalWeatherSource.FAE_MAGIC:
                temp += self.magical_intensity * 5

        return temp

    def get_dew_point(self) -> float:
        """Calculate dew point temperature."""

        a = 17.27
        b = 237.7
        alpha = ((a * self.temperature) / (b + self.temperature)) + math.log(self.humidity)
        dew_point = (b * alpha) / (a - alpha)
        return dew_point

    def get_weather_score(self) -> float:
        """Calculate overall weather severity score (0-1)."""

        base_score = self.severity.value / 5.0  # Normalize severity to 0-1

        # Temperature extremes
        temp_score = 0.0
        if self.temperature < -20 or self.temperature > 40:
            temp_score = 1.0
        elif self.temperature < -10 or self.temperature > 35:
            temp_score = 0.7
        elif self.temperature < -5 or self.temperature > 30:
            temp_score = 0.4

        # Wind speed score
        wind_score = min(1.0, self.wind_speed / 100.0)

        # Precipitation score
        precip_score = min(1.0, self.precipitation_intensity / 50.0)

        # Visibility score
        visibility_score = max(0.0, 1.0 - (self.visibility / 10.0))

        # Magical intensity
        magic_score = self.magical_intensity

        # Combine scores
        total_score = max(base_score, temp_score, wind_score, precip_score, visibility_score, magic_score)

        return min(1.0, total_score)

    def is_hazardous(self) -> bool:
        """Check if current weather conditions are hazardous."""

        hazardous_conditions = [
            self.weather_type in [WeatherType.BLIZZARD, WeatherType.HURRICANE, WeatherType.SEVERE_THUNDERSTORM],
            self.wind_speed > 60,
            self.visibility < 1.0,
            self.get_feels_like_temperature() < -20 or self.get_feels_like_temperature() > 45,
            self.weather_score() > 0.7,
            self.magical_intensity > 0.8,
        ]

        return any(hazardous_conditions)

    def add_previous_state(self, previous_state: 'WeatherState'):
        """Add a previous state to the history."""

        self.previous_states.append(previous_state)
        # Keep only last 24 hours of history
        cutoff_time = self.timestamp - timedelta(hours=24)
        self.previous_states = [state for state in self.previous_states if state.timestamp > cutoff_time]

    def to_dict(self) -> Dict[str, Any]:
        """Convert weather state to dictionary for serialization."""

        return {
            'weather_type': self.weather_type.value,
            'severity': self.severity.value,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction.value,
            'visibility': self.visibility,
            'cloud_cover': self.cloud_cover.value,
            'precipitation_type': self.precipitation_type.value,
            'precipitation_intensity': self.precipitation_intensity,
            'snow_depth': self.snow_depth,
            'location': self.location,
            'altitude': self.altitude,
            'climate_zone': self.climate_zone.value,
            'season': self.season.value,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration.total_seconds(),
            'magical_source': self.magical_source.value if self.magical_source else None,
            'magical_intensity': self.magical_intensity,
            'magical_effects': self.magical_effects,
            'atmospheric_conditions': self.atmospheric_conditions.to_dict(),
            'active_events': self.active_events,
            'forecast_confidence': self.forecast_confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherState':
        """Create weather state from dictionary."""

        # Convert enums
        weather_type = WeatherType(data['weather_type'])
        severity = WeatherSeverity(data['severity'])
        wind_direction = WindDirection(data['wind_direction'])
        cloud_cover = CloudCover(data['cloud_cover'])
        precipitation_type = PrecipitationType(data['precipitation_type'])
        climate_zone = ClimateZone(data['climate_zone'])
        season = Season(data['season'])
        magical_source = MagicalWeatherSource(data['magical_source']) if data['magical_source'] else None

        # Parse datetime
        timestamp = datetime.fromisoformat(data['timestamp'])
        duration = timedelta(seconds=data['duration'])

        # Create atmospheric conditions
        atmospheric_conditions = AtmosphericConditions.from_dict(data['atmospheric_conditions'])

        # Create weather state
        state = cls(
            weather_type=weather_type,
            severity=severity,
            temperature=data['temperature'],
            humidity=data['humidity'],
            pressure=data['pressure'],
            wind_speed=data['wind_speed'],
            wind_direction=wind_direction,
            visibility=data['visibility'],
            cloud_cover=cloud_cover,
            precipitation_type=precipitation_type,
            precipitation_intensity=data['precipitation_intensity'],
            snow_depth=data['snow_depth'],
            location=data['location'],
            altitude=data['altitude'],
            climate_zone=climate_zone,
            season=season,
            timestamp=timestamp,
            duration=duration,
            magical_source=magical_source,
            magical_intensity=data['magical_intensity'],
            magical_effects=data['magical_effects'],
            atmospheric_conditions=atmospheric_conditions,
            active_events=data['active_events'],
            forecast_confidence=data['forecast_confidence'],
        )

        return state

    def get_description(self) -> str:
        """Get human-readable description of current weather."""

        from .weather_types import get_weather_description

        description = get_weather_description(self.weather_type, self.severity)

        # Add temperature information
        feels_like = self.get_feels_like_temperature()
        if abs(feels_like - self.temperature) > 2:
            description += f", Temperature: {self.temperature:.1f}°C (feels like {feels_like:.1f}°C)"
        else:
            description += f", Temperature: {self.temperature:.1f}°C"

        # Add wind information
        if self.wind_speed > 10:
            description += f", {self.wind_speed:.1f} km/h {self.wind_direction.value} winds"

        # Add visibility information
        if self.visibility < 5:
            description += f", Visibility: {self.visibility:.1f} km"

        # Add magical information
        if self.magical_intensity > 0:
            description += f", Magical influence: {self.magical_source.value if self.magical_source else 'unknown'}"

        return description

    def copy(self) -> 'WeatherState':
        """Create a deep copy of the weather state."""

        return WeatherState.from_dict(self.to_dict())