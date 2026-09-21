"""
Movement Effects System

Calculates weather effects on movement, exploration, and navigation.
"""

import math
from typing import Dict, Any

from ..core.weather_state import WeatherState
from ..core.weather_types import WeatherType, ClimateZone

class MovementEffects:
    """Handles weather effects on movement and exploration."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Terrain movement multipliers
        self.terrain_multipliers = {
            "plains": 1.0,
            "forest": 0.8,
            "hills": 0.7,
            "mountains": 0.5,
            "swamp": 0.6,
            "desert": 0.8,
            "snow": 0.4,
            "ice": 0.3,
            "urban": 0.9,
            "dungeon": 0.8,
            "coastal": 0.9,
            "river": 0.7,
            "lake": 0.6
        }

        # Weather movement penalties
        self.weather_penalties = {
            WeatherType.CLEAR: {"speed": 1.0, "endurance": 1.0, "navigation": 1.0},
            WeatherType.PARTLY_CLOUDY: {"speed": 0.95, "endurance": 1.0, "navigation": 1.0},
            WeatherType.OVERCAST: {"speed": 0.9, "endurance": 1.05, "navigation": 1.0},
            WeatherType.LIGHT_RAIN: {"speed": 0.8, "endurance": 1.1, "navigation": 1.1},
            WeatherType.MODERATE_RAIN: {"speed": 0.6, "endurance": 1.2, "navigation": 1.2},
            WeatherType.HEAVY_RAIN: {"speed": 0.4, "endurance": 1.4, "navigation": 1.4},
            WeatherType.LIGHT_SNOW: {"speed": 0.7, "endurance": 1.15, "navigation": 1.1},
            WeatherType.MODERATE_SNOW: {"speed": 0.5, "endurance": 1.3, "navigation": 1.3},
            WeatherType.HEAVY_SNOW: {"speed": 0.3, "endurance": 1.5, "navigation": 1.5},
            WeatherType.BLIZZARD: {"speed": 0.1, "endurance": 2.0, "navigation": 2.5},
            WeatherType.LIGHT_FOG: {"speed": 0.9, "endurance": 1.05, "navigation": 1.3},
            WeatherType.MODERATE_FOG: {"speed": 0.7, "endurance": 1.1, "navigation": 1.8},
            WeatherType.DENSE_FOG: {"speed": 0.5, "endurance": 1.2, "navigation": 2.5},
            WeatherType.LIGHT_WIND: {"speed": 0.95, "endurance": 1.05, "navigation": 1.0},
            WeatherType.MODERATE_WIND: {"speed": 0.85, "endurance": 1.15, "navigation": 1.1},
            WeatherType.STRONG_WIND: {"speed": 0.6, "endurance": 1.3, "navigation": 1.2},
            WeatherType.GALE_FORCE: {"speed": 0.3, "endurance": 1.6, "navigation": 1.5},
            WeatherType.DUST_STORM: {"speed": 0.4, "endurance": 1.5, "navigation": 2.0},
            WeatherType.SANDSTORM: {"speed": 0.2, "endurance": 1.8, "navigation": 2.5},
        }

    def calculate_movement_impact(self, weather_state: WeatherState,
                                  terrain_type: str = "plains") -> Dict[str, float]:
        """Calculate comprehensive movement impact."""

        # Get base terrain multiplier
        terrain_multiplier = self.terrain_multipliers.get(terrain_type, 1.0)

        # Get weather penalties
        weather_penalty = self.weather_penalties.get(
            weather_state.weather_type,
            {"speed": 1.0, "endurance": 1.0, "navigation": 1.0}
        )

        # Calculate final modifiers
        speed_modifier = terrain_multiplier * weather_penalty["speed"]
        endurance_modifier = weather_penalty["endurance"]
        navigation_modifier = weather_penalty["navigation"]

        # Apply wind effects
        wind_effect = self._calculate_wind_effect(weather_state)
        speed_modifier *= wind_effect["speed"]
        endurance_modifier *= wind_effect["endurance"]

        # Apply temperature effects
        temp_effect = self._calculate_temperature_effect(weather_state)
        speed_modifier *= temp_effect["speed"]
        endurance_modifier *= temp_effect["endurance"]

        # Apply visibility effects
        visibility_effect = self._calculate_visibility_effect(weather_state)
        navigation_modifier *= visibility_effect["navigation"]

        # Apply precipitation effects
        if weather_state.precipitation_intensity > 0:
            precip_effect = self._calculate_precipitation_effect(weather_state, terrain_type)
            speed_modifier *= precip_effect["speed"]
            endurance_modifier *= precip_effect["endurance"]
            navigation_modifier *= precip_effect["navigation"]

        # Apply magical effects
        if weather_state.magical_intensity > 0:
            magic_effect = self._calculate_magical_movement_effect(weather_state)
            speed_modifier *= magic_effect["speed"]
            endurance_modifier *= magic_effect["endurance"]
            navigation_modifier *= magic_effect["navigation"]

        # Ensure minimum values
        speed_modifier = max(0.05, speed_modifier)
        endurance_modifier = max(0.5, endurance_modifier)
        navigation_modifier = max(0.1, navigation_modifier)

        return {
            "speed_modifier": speed_modifier,
            "endurance_modifier": endurance_modifier,
            "navigation_modifier": navigation_modifier,
            "terrain_modifier": terrain_multiplier
        }

    def _calculate_wind_effect(self, weather_state: WeatherState) -> Dict[str, float]:
        """Calculate wind effects on movement."""

        effect = {"speed": 1.0, "endurance": 1.0}

        if weather_state.wind_speed > 15:
            # Significant wind affects movement
            wind_factor = math.exp(-weather_state.wind_speed / 50)
            effect["speed"] = max(0.3, wind_factor)
            effect["endurance"] = 1.0 + (weather_state.wind_speed / 100)

            # Headwind vs tailwind effect (simplified)
            if weather_state.wind_speed > 30:
                effect["endurance"] += 0.5  # Additional fatigue

        return effect

    def _calculate_temperature_effect(self, weather_state: WeatherState) -> Dict[str, float]:
        """Calculate temperature effects on movement."""

        effect = {"speed": 1.0, "endurance": 1.0}

        feels_like = weather_state.get_feels_like_temperature()

        if feels_like < -20:
            # Extreme cold
            effect["speed"] = 0.5
            effect["endurance"] = 1.8
        elif feels_like < -10:
            # Severe cold
            effect["speed"] = 0.7
            effect["endurance"] = 1.4
        elif feels_like < 0:
            # Cold
            effect["speed"] = 0.85
            effect["endurance"] = 1.2
        elif feels_like > 40:
            # Extreme heat
            effect["speed"] = 0.6
            effect["endurance"] = 1.6
        elif feels_like > 35:
            # Severe heat
            effect["speed"] = 0.8
            effect["endurance"] = 1.3
        elif feels_like > 30:
            # Hot
            effect["speed"] = 0.9
            effect["endurance"] = 1.15

        return effect

    def _calculate_visibility_effect(self, weather_state: WeatherState) -> Dict[str, float]:
        """Calculate visibility effects on navigation."""

        effect = {"navigation": 1.0}

        if weather_state.visibility < 1.0:
            # Very poor visibility
            effect["navigation"] = 3.0
        elif weather_state.visibility < 3.0:
            # Poor visibility
            effect["navigation"] = 2.0
        elif weather_state.visibility < 5.0:
            # Reduced visibility
            effect["navigation"] = 1.5
        elif weather_state.visibility < 8.0:
            # Slightly reduced visibility
            effect["navigation"] = 1.2

        return effect

    def _calculate_precipitation_effect(self, weather_state: WeatherState,
                                       terrain_type: str) -> Dict[str, float]:
        """Calculate precipitation effects on movement."""

        effect = {"speed": 1.0, "endurance": 1.0, "navigation": 1.0}

        if weather_state.precipitation_intensity > 30:
            # Heavy precipitation
            effect["speed"] = 0.7
            effect["endurance"] = 1.3
            effect["navigation"] = 1.4
        elif weather_state.precipitation_intensity > 15:
            # Moderate precipitation
            effect["speed"] = 0.85
            effect["endurance"] = 1.15
            effect["navigation"] = 1.2
        elif weather_state.precipitation_intensity > 5:
            # Light precipitation
            effect["speed"] = 0.95
            effect["endurance"] = 1.05

        # Terrain-specific precipitation effects
        if terrain_type == "swamp" and weather_state.precipitation_intensity > 10:
            effect["speed"] *= 0.7  # Swamp becomes very muddy
            effect["endurance"] *= 1.4
        elif terrain_type == "snow" and weather_state.temperature > 2:
            # Snow melting creates slush
            effect["speed"] *= 0.6
            effect["endurance"] *= 1.3
        elif terrain_type == "desert" and weather_state.precipitation_intensity > 5:
            # Rain creates mud in desert
            effect["speed"] *= 0.5
            effect["endurance"] *= 1.5

        return effect

    def _calculate_magical_movement_effect(self, weather_state: WeatherState) -> Dict[str, float]:
        """Calculate magical weather effects on movement."""

        effect = {"speed": 1.0, "endurance": 1.0, "navigation": 1.0}

        if weather_state.magical_intensity > 0.5:
            if weather_state.magical_source and "shadow" in weather_state.magical_source.value:
                # Shadow magic slows movement
                effect["speed"] = 0.7
                effect["endurance"] = 1.4
                effect["navigation"] = 1.5
            elif weather_state.magical_source and "fae" in weather_state.magical_source.value:
                # Fae magic disorients
                effect["navigation"] = 2.0
                effect["endurance"] = 1.2
            elif weather_state.weather_type == WeatherType.UNDEAD_FOG:
                # Undead fog drains energy
                effect["speed"] = 0.6
                effect["endurance"] = 1.6
            elif weather_state.weather_type == WeatherType.MAGICAL_STORM:
                # Magical storm creates chaos
                effect["speed"] = 0.5
                effect["endurance"] = 1.8
                effect["navigation"] = 2.5

        return effect

    def calculate_exhaustion_rate(self, weather_state: WeatherState,
                                  terrain_type: str = "plains",
                                  movement_speed: float = 1.0) -> float:
        """Calculate exhaustion rate per hour of travel."""

        base_exhaustion = 1.0  # Base exhaustion rate

        # Get movement impact
        movement_impact = self.calculate_movement_impact(weather_state, terrain_type)

        # Calculate exhaustion based on effort
        effort_factor = (2.0 - movement_impact["speed_modifier"])  # Inverse of speed
        endurance_factor = movement_impact["endurance_modifier"]

        # Weather severity effect
        severity_factor = 1.0 + (weather_state.severity.value / 5.0)

        # Temperature effect
        feels_like = weather_state.get_feels_like_temperature()
        if feels_like < -10 or feels_like > 35:
            temp_factor = 1.5
        elif feels_like < 0 or feels_like > 30:
            temp_factor = 1.2
        else:
            temp_factor = 1.0

        # Altitude effect
        if weather_state.altitude > 2000:
            altitude_factor = 1.0 + (weather_state.altitude - 2000) / 4000
        else:
            altitude_factor = 1.0

        # Calculate final exhaustion rate
        exhaustion_rate = (base_exhaustion * effort_factor * endurance_factor *
                          severity_factor * temp_factor * altitude_factor)

        return exhaustion_rate

    def calculate_rest_requirements(self, weather_state: WeatherState,
                                   terrain_type: str = "plains") -> Dict[str, Any]:
        """Calculate rest requirements under current conditions."""

        movement_impact = self.calculate_movement_impact(weather_state, terrain_type)
        exhaustion_rate = self.calculate_exhaustion_rate(weather_state, terrain_type)

        # Base rest requirements
        base_rest_per_hour = 10  # minutes of rest per hour of travel
        base_long_rest = 8  # hours for long rest

        # Adjust for conditions
        rest_multiplier = movement_impact["endurance_modifier"]
        if weather_state.severity.value >= 3:  # Severe or worse
            rest_multiplier *= 1.5

        # Temperature effects on rest
        feels_like = weather_state.get_feels_like_temperature()
        if feels_like < -15 or feels_like > 38:
            rest_multiplier *= 1.3  # More rest needed in extreme conditions

        # Calculate final requirements
        short_rest_frequency = 60 / (base_rest_per_hour * rest_multiplier)  # minutes between rests
        short_rest_duration = base_rest_per_hour * rest_multiplier
        long_rest_duration = base_long_rest * rest_multiplier

        return {
            "short_rest_frequency_minutes": short_rest_frequency,
            "short_rest_duration_minutes": short_rest_duration,
            "long_rest_duration_hours": long_rest_duration,
            "exhaustion_rate_per_hour": exhaustion_rate
        }

    def can_travel_at_night(self, weather_state: WeatherState,
                           terrain_type: str = "plains") -> Dict[str, Any]:
        """Determine if night travel is possible and its effects."""

        base_night_penalty = {
            "speed": 0.7,
            "endurance": 1.2,
            "navigation": 1.5
        }

        # Check weather conditions for night travel
        if weather_state.visibility < 2.0:
            return {
                "possible": False,
                "reason": "Visibility too poor for safe night travel"
            }

        if weather_state.weather_type in [WeatherType.BLIZZARD, WeatherType.SEVERE_THUNDERSTORM]:
            return {
                "possible": False,
                "reason": "Extreme weather makes night travel too dangerous"
            }

        # Calculate night travel effects
        movement_impact = self.calculate_movement_impact(weather_state, terrain_type)

        night_impact = {
            "speed_modifier": movement_impact["speed_modifier"] * base_night_penalty["speed"],
            "endurance_modifier": movement_impact["endurance_modifier"] * base_night_penalty["endurance"],
            "navigation_modifier": movement_impact["navigation_modifier"] * base_night_penalty["navigation"]
        }

        # Moonlight helps with visibility
        if weather_state.atmospheric_conditions.lunar_illumination > 0.7:
            night_impact["navigation_modifier"] *= 0.8  # Better navigation with full moon

        # Magical light sources
        if weather_state.magical_intensity > 0.3:
            if weather_state.magical_source and "divine" in weather_state.magical_source.value:
                night_impact["navigation_modifier"] *= 0.7  # Divine light helps

        return {
            "possible": True,
            "impact": night_impact,
            "additional_risks": self._get_night_travel_risks(weather_state)
        }

    def _get_night_travel_risks(self, weather_state: WeatherState) -> List[str]:
        """Get additional risks for night travel."""

        risks = []

        if weather_state.visibility < 5.0:
            risks.append("Getting lost")

        if weather_state.temperature < 5:
            risks.append("Hypothermia")

        if weather_state.weather_type in [WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN]:
            risks.append("Slipping and falling")

        if weather_state.wind_speed > 25:
            risks.append("Being blown off course")

        if weather_state.magical_intensity > 0.4:
            risks.append("Magical disorientation")

        return risks