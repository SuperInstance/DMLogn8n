"""
Climate Patterns System

Manages long-term climate patterns, seasonal variations, and regional
weather characteristics that influence daily weather simulation.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .weather_types import WeatherType, WeatherSeverity, Season, ClimateZone
from .weather_state import WeatherState

@dataclass
class SeasonalPattern:
    """Defines seasonal weather patterns for a climate zone."""

    season: Season
    base_temperature: float  # Average temperature
    temperature_variation: float  # Standard deviation
    base_humidity: float  # Average humidity (0-1)
    precipitation_frequency: float  # Probability of precipitation
    precipitation_intensity: float  # Average precipitation when it occurs
    wind_speed_average: float  # Average wind speed
    weather_type_probabilities: Dict[WeatherType, float]
    special_events: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DiurnalPattern:
    """Defines daily temperature and weather variations."""

    sunrise_time: int  # Hour (0-23)
    sunset_time: int   # Hour (0-23)
    temperature_amplitude: float  # Daily temperature range
    humidity_cycle_amplitude: float  # Daily humidity variation
    wind_patterns: Dict[int, float]  # Hour -> wind multiplier
    precipitation_tendencies: Dict[str, float]  # Time of day -> probability

@dataclass
class RegionalModifier:
    """Regional climate modifiers for specific locations."""

    region_name: str
    climate_zone: ClimateZone
    temperature_offset: float
    humidity_offset: float
    wind_modifier: float
    precipitation_modifier: float
    special_conditions: List[str]  # Mountain effects, coastal patterns, etc.
    unique_events: List[Dict[str, Any]] = field(default_factory=list)

class ClimatePatterns:
    """Manages climate patterns and their influence on weather."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.seasonal_variation = config.get('seasonal_variation', 0.3)
        self.diurnal_variation = config.get('diurnal_variation', 0.15)

        # Initialize climate patterns
        self.seasonal_patterns = self._create_seasonal_patterns()
        self.diurnal_patterns = self._create_diurnal_patterns()
        self.regional_modifiers = self._create_regional_modifiers()

        # Climate data
        self.historical_patterns: Dict[str, List[WeatherState]] = {}
        self.climate_cycles: Dict[str, float] = {
            'el_nino': 0.0,  # El Niño/Southern Oscillation
            'solar_cycle': 0.5,  # Solar activity cycle
            'volcanic_activity': 0.0,  # Volcanic ash effects
            'magical_resonance': 0.0  # Long-term magical patterns
        }

    def _create_seasonal_patterns(self) -> Dict[ClimateZone, Dict[Season, SeasonalPattern]]:
        """Create seasonal patterns for all climate zones."""

        patterns = {}

        # Tropical patterns
        patterns[ClimateZone.TROPICAL] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=28.0,
                temperature_variation=2.0,
                base_humidity=0.8,
                precipitation_frequency=0.4,
                precipitation_intensity=15.0,
                wind_speed_average=10.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.3,
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.MODERATE_RAIN: 0.2,
                    WeatherType.THUNDERSTORM: 0.15,
                    WeatherType.LIGHT_WIND: 0.05
                },
                special_events=[
                    {'name': 'Monsoon Season', 'probability': 0.1, 'start_month': 6, 'duration_months': 3}
                ]
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=32.0,
                temperature_variation=3.0,
                base_humidity=0.85,
                precipitation_frequency=0.3,
                precipitation_intensity=20.0,
                wind_speed_average=8.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.25,
                    WeatherType.PARTLY_CLOUDY: 0.25,
                    WeatherType.THUNDERSTORM: 0.3,
                    WeatherType.HEAVY_RAIN: 0.15,
                    WeatherType.LIGHT_WIND: 0.05
                }
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=26.0,
                temperature_variation=2.5,
                base_humidity=0.75,
                precipitation_frequency=0.35,
                precipitation_intensity=12.0,
                wind_speed_average=12.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.35,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.CLEAR: 0.2,
                    WeatherType.THUNDERSTORM: 0.15,
                    WeatherType.LIGHT_WIND: 0.05
                }
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=24.0,
                temperature_variation=2.0,
                base_humidity=0.7,
                precipitation_frequency=0.25,
                precipitation_intensity=10.0,
                wind_speed_average=15.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.4,
                    WeatherType.MODERATE_RAIN: 0.3,
                    WeatherType.CLEAR: 0.2,
                    WeatherType.THUNDERSTORM: 0.1
                }
            )
        }

        # Temperate patterns
        patterns[ClimateZone.TEMPERATE] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=15.0,
                temperature_variation=8.0,
                base_humidity=0.6,
                precipitation_frequency=0.35,
                precipitation_intensity=8.0,
                wind_speed_average=15.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.CLEAR: 0.2,
                    WeatherType.OVERCAST: 0.15,
                    WeatherType.LIGHT_WIND: 0.1
                },
                special_events=[
                    {'name': 'Spring Showers', 'probability': 0.15, 'start_month': 4, 'duration_months': 1}
                ]
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=25.0,
                temperature_variation=5.0,
                base_humidity=0.5,
                precipitation_frequency=0.25,
                precipitation_intensity=10.0,
                wind_speed_average=10.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.4,
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.MODERATE_RAIN: 0.15,
                    WeatherType.THUNDERSTORM: 0.1,
                    WeatherType.LIGHT_WIND: 0.05
                }
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=12.0,
                temperature_variation=7.0,
                base_humidity=0.65,
                precipitation_frequency=0.3,
                precipitation_intensity=7.0,
                wind_speed_average=18.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.3,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.PARTLY_CLOUDY: 0.2,
                    WeatherType.LIGHT_FOG: 0.15,
                    WeatherType.MODERATE_WIND: 0.1
                },
                special_events=[
                    {'name': 'Fall Fog Season', 'probability': 0.2, 'start_month': 10, 'duration_months': 1}
                ]
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=2.0,
                temperature_variation=6.0,
                base_humidity=0.7,
                precipitation_frequency=0.3,
                precipitation_intensity=5.0,
                wind_speed_average=20.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.35,
                    WeatherType.LIGHT_SNOW: 0.25,
                    WeatherType.MODERATE_SNOW: 0.15,
                    WeatherType.CLEAR: 0.15,
                    WeatherType.STRONG_WIND: 0.1
                },
                special_events=[
                    {'name': 'Winter Storms', 'probability': 0.1, 'start_month': 12, 'duration_months': 2}
                ]
            )
        }

        # Arctic patterns
        patterns[ClimateZone.ARCTIC] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=-10.0,
                temperature_variation=10.0,
                base_humidity=0.3,
                precipitation_frequency=0.2,
                precipitation_intensity=3.0,
                wind_speed_average=25.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.4,
                    WeatherType.LIGHT_SNOW: 0.3,
                    WeatherType.CLEAR: 0.2,
                    WeatherType.STRONG_WIND: 0.1
                }
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=5.0,
                temperature_variation=8.0,
                base_humidity=0.4,
                precipitation_frequency=0.25,
                precipitation_intensity=4.0,
                wind_speed_average=20.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.3,
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.LIGHT_SNOW: 0.2,
                    WeatherType.OVERCAST: 0.15,
                    WeatherType.MODERATE_WIND: 0.05
                }
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=-5.0,
                temperature_variation=8.0,
                base_humidity=0.35,
                precipitation_frequency=0.3,
                precipitation_intensity=5.0,
                wind_speed_average=30.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.35,
                    WeatherType.MODERATE_SNOW: 0.3,
                    WeatherType.STRONG_WIND: 0.2,
                    WeatherType.CLEAR: 0.15
                }
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=-25.0,
                temperature_variation=8.0,
                base_humidity=0.2,
                precipitation_frequency=0.15,
                precipitation_intensity=2.0,
                wind_speed_average=35.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.3,
                    WeatherType.OVERCAST: 0.25,
                    WeatherType.LIGHT_SNOW: 0.2,
                    WeatherType.BLIZZARD: 0.15,
                    WeatherType.GALE_FORCE: 0.1
                },
                special_events=[
                    {'name': 'Polar Night', 'probability': 0.3, 'start_month': 11, 'duration_months': 3}
                ]
            )
        }

        # Desert patterns
        patterns[ClimateZone.DESERT] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=25.0,
                temperature_variation=15.0,
                base_humidity=0.2,
                precipitation_frequency=0.05,
                precipitation_intensity=5.0,
                wind_speed_average=12.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.6,
                    WeatherType.PARTLY_CLOUDY: 0.2,
                    WeatherType.LIGHT_WIND: 0.15,
                    WeatherType.DUST_STORM: 0.05
                }
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=40.0,
                temperature_variation=10.0,
                base_humidity=0.1,
                precipitation_frequency=0.02,
                precipitation_intensity=8.0,
                wind_speed_average=8.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.8,
                    WeatherType.PARTLY_CLOUDY: 0.1,
                    WeatherType.LIGHT_WIND: 0.08,
                    WeatherType.DUST_STORM: 0.02
                },
                special_events=[
                    {'name': 'Heat Wave', 'probability': 0.2, 'start_month': 7, 'duration_months': 2}
                ]
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=20.0,
                temperature_variation=12.0,
                base_humidity=0.25,
                precipitation_frequency=0.08,
                precipitation_intensity=6.0,
                wind_speed_average=15.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.5,
                    WeatherType.PARTLY_CLOUDY: 0.25,
                    WeatherType.LIGHT_WIND: 0.15,
                    WeatherType.DUST_STORM: 0.1
                }
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=10.0,
                temperature_variation=8.0,
                base_humidity=0.3,
                precipitation_frequency=0.1,
                precipitation_intensity=4.0,
                wind_speed_average=18.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.4,
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.LIGHT_WIND: 0.2,
                    WeatherType.MODERATE_RAIN: 0.1
                }
            )
        }

        # Mountainous patterns
        patterns[ClimateZone.MOUNTAINOUS] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=8.0,
                temperature_variation=10.0,
                base_humidity=0.5,
                precipitation_frequency=0.4,
                precipitation_intensity=10.0,
                wind_speed_average=25.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.OVERCAST: 0.2,
                    WeatherType.LIGHT_SNOW: 0.15,
                    WeatherType.STRONG_WIND: 0.1
                }
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=18.0,
                temperature_variation=8.0,
                base_humidity=0.4,
                precipitation_frequency=0.3,
                precipitation_intensity=12.0,
                wind_speed_average=20.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.35,
                    WeatherType.MODERATE_RAIN: 0.2,
                    WeatherType.THUNDERSTORM: 0.2,
                    WeatherType.CLEAR: 0.15,
                    WeatherType.MODERATE_WIND: 0.1
                }
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=5.0,
                temperature_variation=8.0,
                base_humidity=0.55,
                precipitation_frequency=0.35,
                precipitation_intensity=8.0,
                wind_speed_average=30.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.3,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.LIGHT_SNOW: 0.2,
                    WeatherType.STRONG_WIND: 0.15,
                    WeatherType.CLEAR: 0.1
                }
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=-8.0,
                temperature_variation=8.0,
                base_humidity=0.4,
                precipitation_frequency=0.3,
                precipitation_intensity=6.0,
                wind_speed_average=35.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.3,
                    WeatherType.HEAVY_SNOW: 0.25,
                    WeatherType.BLIZZARD: 0.2,
                    WeatherType.GALE_FORCE: 0.15,
                    WeatherType.CLEAR: 0.1
                },
                special_events=[
                    {'name': 'Avalanche Season', 'probability': 0.15, 'start_month': 1, 'duration_months': 2}
                ]
            )
        }

        # Coastal patterns
        patterns[ClimateZone.COASTAL] = {
            Season.SPRING: SeasonalPattern(
                season=Season.SPRING,
                base_temperature=12.0,
                temperature_variation=6.0,
                base_humidity=0.7,
                precipitation_frequency=0.3,
                precipitation_intensity=8.0,
                wind_speed_average=18.0,
                weather_type_probabilities={
                    WeatherType.PARTLY_CLOUDY: 0.35,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.LIGHT_FOG: 0.2,
                    WeatherType.CLEAR: 0.15,
                    WeatherType.MODERATE_WIND: 0.05
                }
            ),
            Season.SUMMER: SeasonalPattern(
                season=Season.SUMMER,
                base_temperature=22.0,
                temperature_variation=4.0,
                base_humidity=0.75,
                precipitation_frequency=0.25,
                precipitation_intensity=10.0,
                wind_speed_average=12.0,
                weather_type_probabilities={
                    WeatherType.CLEAR: 0.3,
                    WeatherType.PARTLY_CLOUDY: 0.3,
                    WeatherType.MODERATE_RAIN: 0.2,
                    WeatherType.LIGHT_FOG: 0.15,
                    WeatherType.LIGHT_WIND: 0.05
                }
            ),
            Season.AUTUMN: SeasonalPattern(
                season=Season.AUTUMN,
                base_temperature=10.0,
                temperature_variation=6.0,
                base_humidity=0.8,
                precipitation_frequency=0.35,
                precipitation_intensity=12.0,
                wind_speed_average=22.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.3,
                    WeatherType.MODERATE_RAIN: 0.3,
                    WeatherType.LIGHT_FOG: 0.2,
                    WeatherType.STRONG_WIND: 0.15,
                    WeatherType.CLEAR: 0.05
                },
                special_events=[
                    {'name': 'Coastal Storms', 'probability': 0.15, 'start_month': 10, 'duration_months': 2}
                ]
            ),
            Season.WINTER: SeasonalPattern(
                season=Season.WINTER,
                base_temperature=3.0,
                temperature_variation=5.0,
                base_humidity=0.75,
                precipitation_frequency=0.3,
                precipitation_intensity=6.0,
                wind_speed_average=25.0,
                weather_type_probabilities={
                    WeatherType.OVERCAST: 0.35,
                    WeatherType.MODERATE_RAIN: 0.25,
                    WeatherType.LIGHT_SNOW: 0.15,
                    WeatherType.STRONG_WIND: 0.2,
                    WeatherType.LIGHT_FOG: 0.05
                }
            )
        }

        return patterns

    def _create_diurnal_patterns(self) -> Dict[ClimateZone, DiurnalPattern]:
        """Create diurnal (daily) patterns for different climate zones."""

        patterns = {}

        # Default pattern for most climates
        default_pattern = DiurnalPattern(
            sunrise_time=6,
            sunset_time=18,
            temperature_amplitude=10.0,
            humidity_cycle_amplitude=0.2,
            wind_patterns={
                0: 0.6, 1: 0.5, 2: 0.5, 3: 0.5, 4: 0.6, 5: 0.8, 6: 1.0,
                7: 1.2, 8: 1.3, 9: 1.4, 10: 1.4, 11: 1.3, 12: 1.2,
                13: 1.1, 14: 1.1, 15: 1.2, 16: 1.3, 17: 1.4, 18: 1.3,
                19: 1.1, 20: 0.9, 21: 0.8, 22: 0.7, 23: 0.6
            },
            precipitation_tendencies={
                'morning': 0.3, 'afternoon': 0.4, 'evening': 0.2, 'night': 0.1
            }
        )

        # Climate zone specific patterns
        patterns[ClimateZone.TEMPERATE] = default_pattern

        patterns[ClimateZone.TROPICAL] = DiurnalPattern(
            sunrise_time=6,
            sunset_time=18,
            temperature_amplitude=8.0,
            humidity_cycle_amplitude=0.15,
            wind_patterns=default_pattern.wind_patterns,
            precipitation_tendencies={
                'morning': 0.2, 'afternoon': 0.6, 'evening': 0.15, 'night': 0.05
            }
        )

        patterns[ClimateZone.DESERT] = DiurnalPattern(
            sunrise_time=6,
            sunset_time=19,
            temperature_amplitude=20.0,
            humidity_cycle_amplitude=0.3,
            wind_patterns=default_pattern.wind_patterns,
            precipitation_tendencies={
                'morning': 0.1, 'afternoon': 0.1, 'evening': 0.4, 'night': 0.4
            }
        )

        patterns[ClimateZone.COASTAL] = DiurnalPattern(
            sunrise_time=5,
            sunset_time=19,
            temperature_amplitude=6.0,
            humidity_cycle_amplitude=0.1,
            wind_patterns=default_pattern.wind_patterns,
            precipitation_tendencies={
                'morning': 0.4, 'afternoon': 0.3, 'evening': 0.2, 'night': 0.1
            }
        )

        # Use default for others
        for climate_zone in ClimateZone:
            if climate_zone not in patterns:
                patterns[climate_zone] = default_pattern

        return patterns

    def _create_regional_modifiers(self) -> Dict[str, RegionalModifier]:
        """Create regional climate modifiers for specific locations."""

        return {
            'northern_mountains': RegionalModifier(
                region_name='Northern Mountains',
                climate_zone=ClimateZone.MOUNTAINOUS,
                temperature_offset=-8.0,
                humidity_offset=-0.1,
                wind_modifier=1.5,
                precipitation_modifier=1.2,
                special_conditions=['high_altitude', 'rain_shadow', 'avalanche_risk'],
                unique_events=[
                    {'name': 'Mountain Blizzard', 'probability': 0.08, 'duration_hours': 24},
                    {'name': 'Rockslide', 'probability': 0.05, 'duration_hours': 2}
                ]
            ),
            'eastern_coast': RegionalModifier(
                region_name='Eastern Coast',
                climate_zone=ClimateZone.COASTAL,
                temperature_offset=2.0,
                humidity_offset=0.15,
                wind_modifier=1.3,
                precipitation_modifier=1.4,
                special_conditions=['sea_breeze', 'coastal_fog', 'tropical_storms'],
                unique_events=[
                    {'name': 'Hurricane', 'probability': 0.03, 'duration_hours': 48},
                    {'name': 'Sea Fog', 'probability': 0.1, 'duration_hours': 6}
                ]
            ),
            'western_desert': RegionalModifier(
                region_name='Western Desert',
                climate_zone=ClimateZone.DESERT,
                temperature_offset=5.0,
                humidity_offset=-0.2,
                wind_modifier=1.2,
                precipitation_modifier=0.3,
                special_conditions=['extreme_heat', 'sandstorms', 'oasis_mirages'],
                unique_events=[
                    {'name': 'Sandstorm', 'probability': 0.08, 'duration_hours': 8},
                    {'name': 'Mirage Field', 'probability': 0.12, 'duration_hours': 4}
                ]
            ),
            'central_plains': RegionalModifier(
                region_name='Central Plains',
                climate_zone=ClimateZone.TEMPERATE,
                temperature_offset=0.0,
                humidity_offset=0.0,
                wind_modifier=1.4,
                precipitation_modifier=1.0,
                special_conditions=['tornado_alley', 'open_exposure'],
                unique_events=[
                    {'name': 'Tornado', 'probability': 0.02, 'duration_hours': 1},
                    {'name': 'Hailstorm', 'probability': 0.06, 'duration_hours': 3}
                ]
            ),
            'southern_swamp': RegionalModifier(
                region_name='Southern Swamp',
                climate_zone=ClimateZone.TEMPERATE,
                temperature_offset=3.0,
                humidity_offset=0.25,
                wind_modifier=0.7,
                precipitation_modifier=1.5,
                special_conditions['standing_water', 'insect_swarms', 'disease_risk'],
                unique_events=[
                    {'name': 'Swamp Gas Explosion', 'probability': 0.01, 'duration_hours': 1},
                    {'name': 'Insect Swarm', 'probability': 0.15, 'duration_hours': 12}
                ]
            )
        }

    def get_seasonal_pattern(self, climate_zone: ClimateZone, season: Season) -> Optional[SeasonalPattern]:
        """Get seasonal pattern for specific climate zone and season."""

        if climate_zone in self.seasonal_patterns and season in self.seasonal_patterns[climate_zone]:
            return self.seasonal_patterns[climate_zone][season]
        return None

    def get_diurnal_pattern(self, climate_zone: ClimateZone) -> Optional[DiurnalPattern]:
        """Get diurnal pattern for climate zone."""

        return self.diurnal_patterns.get(climate_zone)

    def get_regional_modifier(self, region_name: str) -> Optional[RegionalModifier]:
        """Get regional modifier for specific location."""

        return self.regional_modifiers.get(region_name)

    def calculate_seasonal_influence(self, climate_zone: ClimateZone, season: Season,
                                   date: datetime) -> Dict[str, float]:
        """Calculate seasonal weather influences for given date."""

        pattern = self.get_seasonal_pattern(climate_zone, season)
        if not pattern:
            return {}

        # Calculate day of year progression
        day_of_year = date.timetuple().tm_yday
        season_days = self._get_season_length(date.year)
        season_progress = (day_of_year % season_days) / season_days

        # Base seasonal values
        influences = {
            'temperature_modifier': pattern.base_temperature,
            'humidity_modifier': pattern.base_humidity,
            'wind_modifier': pattern.wind_speed_average,
            'precipitation_probability': pattern.precipitation_frequency,
            'precipitation_intensity': pattern.precipitation_intensity
        }

        # Apply seasonal progression
        temp_variation = math.sin(season_progress * 2 * math.pi) * pattern.temperature_variation
        influences['temperature_modifier'] += temp_variation

        # Add seasonal transition effects
        if 0.1 < season_progress < 0.2 or 0.8 < season_progress < 0.9:
            influences['weather_instability'] = 0.3  # Seasonal transition period

        # Check for special seasonal events
        for event in pattern.special_events:
            if self._is_special_event_active(event, date):
                influences['special_event'] = event
                influences['event_probability'] = event['probability']

        return influences

    def calculate_diurnal_influence(self, climate_zone: ClimateZone,
                                  time: datetime) -> Dict[str, float]:
        """Calculate daily weather influences."""

        pattern = self.get_diurnal_pattern(climate_zone)
        if not pattern:
            return {}

        hour = time.hour + time.minute / 60.0

        influences = {}

        # Temperature variation
        if pattern.sunrise_time <= hour <= pattern.sunset_time:
            # Daytime
            day_progress = (hour - pattern.sunrise_time) / (pattern.sunset_time - pattern.sunrise_time)
            temp_factor = math.sin(day_progress * math.pi)
            influences['temperature_modifier'] = temp_factor * pattern.temperature_amplitude / 2
        else:
            # Nighttime
            if hour < pattern.sunrise_time:
                night_progress = hour + 24 - pattern.sunset_time
            else:
                night_progress = hour - pattern.sunset_time
            night_duration = 24 - (pattern.sunset_time - pattern.sunrise_time)
            night_progress /= night_duration
            temp_factor = -math.sin(night_progress * math.pi) * 0.3
            influences['temperature_modifier'] = temp_factor * pattern.temperature_amplitude / 2

        # Humidity variation (inverse of temperature)
        influences['humidity_modifier'] = -influences.get('temperature_modifier', 0) * 0.02

        # Wind patterns
        wind_hour = int(hour)
        influences['wind_modifier'] = pattern.wind_patterns.get(wind_hour, 1.0)

        # Precipitation tendencies
        if 6 <= hour < 12:
            influences['precipitation_modifier'] = pattern.precipitation_tendencies['morning']
        elif 12 <= hour < 18:
            influences['precipitation_modifier'] = pattern.precipitation_tendencies['afternoon']
        elif 18 <= hour < 24:
            influences['precipitation_modifier'] = pattern.precipitation_tendencies['evening']
        else:
            influences['precipitation_modifier'] = pattern.precipitation_tendencies['night']

        return influences

    def apply_regional_modifiers(self, region_name: str, base_influences: Dict[str, float]) -> Dict[str, float]:
        """Apply regional modifiers to base weather influences."""

        modifier = self.get_regional_modifier(region_name)
        if not modifier:
            return base_influences

        modified_influences = base_influences.copy()

        # Apply temperature offset
        if 'temperature_modifier' in modified_influences:
            modified_influences['temperature_modifier'] += modifier.temperature_offset

        # Apply humidity offset
        if 'humidity_modifier' in modified_influences:
            modified_influences['humidity_modifier'] = max(0, min(1,
                modified_influences['humidity_modifier'] + modifier.humidity_offset))

        # Apply wind modifier
        if 'wind_modifier' in modified_influences:
            modified_influences['wind_modifier'] *= modifier.wind_modifier

        # Apply precipitation modifier
        if 'precipitation_probability' in modified_influences:
            modified_influences['precipitation_probability'] *= modifier.precipitation_modifier
            modified_influences['precipitation_probability'] = max(0, min(1,
                modified_influences['precipitation_probability']))

        # Add special conditions
        modified_influences['special_conditions'] = modifier.special_conditions

        return modified_influences

    def update_climate_cycles(self, current_date: datetime):
        """Update long-term climate cycles."""

        # El Niño/Southern Oscillation (3-7 year cycle)
        enso_phase = (current_date.year % 6) / 6.0 * 2 * math.pi
        self.climate_cycles['el_nino'] = math.sin(enso_phase)

        # Solar activity cycle (11 year cycle)
        solar_phase = (current_date.year % 11) / 11.0 * 2 * math.pi
        self.climate_cycles['solar_cycle'] = (math.sin(solar_phase) + 1) / 2

        # Volcanic activity (random events)
        if random.random() < 0.001:  # Very rare volcanic events
            self.climate_cycles['volcanic_activity'] = random.uniform(0.5, 1.0)
        else:
            # Decay existing volcanic activity
            self.climate_cycles['volcanic_activity'] *= 0.99

        # Magical resonance (influenced by lunar cycles)
        lunar_phase = self._calculate_lunar_phase(current_date)
        self.climate_cycles['magical_resonance'] = (math.sin(lunar_phase * 2 * math.pi) + 1) / 2

    def _get_season_length(self, year: int) -> int:
        """Get approximate length of seasons in days."""

        # Simplified - using 90 days per season
        return 90

    def _is_special_event_active(self, event: Dict[str, Any], date: datetime) -> bool:
        """Check if a special seasonal event is active."""

        if 'start_month' not in event or 'duration_months' not in event:
            return False

        start_month = event['start_month']
        duration = event['duration_months']

        current_month = date.month

        # Handle year wrap-around
        if start_month + duration <= 12:
            return start_month <= current_month < start_month + duration
        else:
            return current_month >= start_month or current_month < (start_month + duration - 12)

    def _calculate_lunar_phase(self, date: datetime) -> float:
        """Calculate lunar phase (0-1, new moon to full moon)."""

        # Simplified lunar phase calculation
        year = date.year
        month = date.month
        day = date.day

        # Approximate lunar cycle
        julian_date = (367 * year - 7 * (year + (month + 9) // 12) // 4 +
                      275 * month // 9 + day + 1721013.5)

        lunar_cycle = (julian_date - 2451549.5) % 29.53058867
        phase = lunar_cycle / 29.53058867

        return phase

    def get_climate_summary(self, climate_zone: ClimateZone) -> Dict[str, Any]:
        """Get summary of climate characteristics."""

        if climate_zone not in self.seasonal_patterns:
            return {}

        zone_patterns = self.seasonal_patterns[climate_zone]

        # Calculate annual averages
        all_temps = []
        all_humidity = []
        all_precip_prob = []
        all_wind_speed = []

        for pattern in zone_patterns.values():
            all_temps.append(pattern.base_temperature)
            all_humidity.append(pattern.base_humidity)
            all_precip_prob.append(pattern.precipitation_frequency)
            all_wind_speed.append(pattern.wind_speed_average)

        # Get most common weather types
        weather_type_counts = {}
        for pattern in zone_patterns.values():
            for wtype, prob in pattern.weather_type_probabilities.items():
                weather_type_counts[wtype.value] = weather_type_counts.get(wtype.value, 0) + prob

        return {
            'climate_zone': climate_zone.value,
            'annual_average_temperature': sum(all_temps) / len(all_temps),
            'annual_average_humidity': sum(all_humidity) / len(all_humidity),
            'annual_precipitation_frequency': sum(all_precip_prob) / len(all_precip_prob),
            'annual_average_wind_speed': sum(all_wind_speed) / len(all_wind_speed),
            'temperature_range': (min(all_temps), max(all_temps)),
            'most_common_weather_types': sorted(weather_type_counts.items(),
                                               key=lambda x: x[1], reverse=True)[:3],
            'special_events': self._get_all_special_events(climate_zone)
        }

    def _get_all_special_events(self, climate_zone: ClimateZone) -> List[Dict[str, Any]]:
        """Get all special events for a climate zone."""

        events = []
        if climate_zone in self.seasonal_patterns:
            for pattern in self.seasonal_patterns[climate_zone].values():
                events.extend(pattern.special_events)
        return events