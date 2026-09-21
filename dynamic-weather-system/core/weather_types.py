"""
Weather Types and Enumerations

Defines the fundamental types and categories for the weather system.
"""

from enum import Enum, auto
from typing import Dict, List, Optional
import json

class WeatherType(Enum):
    """Primary weather types for the simulation system."""

    # Clear conditions
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"

    # Precipitation
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    DRIZZLE = "drizzle"

    # Snow conditions
    LIGHT_SNOW = "light_snow"
    MODERATE_SNOW = "moderate_snow"
    HEAVY_SNOW = "heavy_snow"
    BLIZZARD = "blizzard"
    SLEET = "sleet"

    # Storm conditions
    THUNDERSTORM = "thunderstorm"
    SEVERE_THUNDERSTORM = "severe_thunderstorm"
    HAILSTORM = "hailstorm"

    # Wind conditions
    LIGHT_WIND = "light_wind"
    MODERATE_WIND = "moderate_wind"
    STRONG_WIND = "strong_wind"
    GALE_FORCE = "gale_force"
    HURRICANE = "hurricane"

    # Fog conditions
    LIGHT_FOG = "light_fog"
    MODERATE_FOG = "moderate_fog"
    DENSE_FOG = "dense_fog"

    # Special conditions
    DUST_STORM = "dust_storm"
    SANDSTORM = "sandstorm"
    WILDFIRE_SMOKE = "wildfire_smoke"
    VOLCANIC_ASH = "volcanic_ash"

    # Magical weather
    MAGICAL_STORM = "magical_storm"
    FAE_MIST = "fae_mist"
    UNDEAD_FOG = "undead_fog"
    CELESTIAL_SHOWER = "celestial_shower"
    ELEMENTAL_RIFT = "elemental_rift"
    DIVINE_INTERVENTION = "divine_intervention"

class WeatherSeverity(Enum):
    """Severity levels for weather conditions."""

    CALM = 0      # No significant weather effects
    MILD = 1      # Minor visual effects
    MODERATE = 2  # Noticeable gameplay impact
    SEVERE = 3    # Significant impact and danger
    EXTREME = 4   # Life-threatening conditions
    CATASTROPHIC = 5  # World-altering events

class Season(Enum):
    """Seasonal variations for climate modeling."""

    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

class ClimateZone(Enum):
    """Climate zones for regional weather patterns."""

    # Temperature-based zones
    TROPICAL = "tropical"
    SUBTROPICAL = "subtropical"
    TEMPERATE = "temperate"
    SUBARCTIC = "subarctic"
    ARCTIC = "arctic"

    # Precipitation-based zones
    DESERT = "desert"
    SEMI_ARID = "semi_arid"
    MEDITERRANEAN = "mediterranean"
    MONSOON = "monsoon"

    # Special zones
    MOUNTAINOUS = "mountainous"
    COASTAL = "coastal"
    OCEANIC = "oceanic"
    CONTINENTAL = "continental"

    # Magical zones
    FAE_WILDS = "fae_wilds"
    SHADOW_FELL = "shadow_fell"
    ELEMENTAL_PLANE = "elemental_plane"
    DIVINE_REALM = "divine_realm"
    CURSED_LANDS = "cursed_lands"

class WindDirection(Enum):
    """Wind directions for atmospheric modeling."""

    N = "north"
    NE = "northeast"
    E = "east"
    SE = "southeast"
    S = "south"
    SW = "southwest"
    W = "west"
    NW = "northwest"
    VARIABLE = "variable"

class CloudCover(Enum):
    """Cloud coverage levels."""

    CLEAR = 0      # 0-10%
    SCATTERED = 1  # 10-25%
    BROKEN = 2     # 25-50%
    OVERCAST = 3   # 50-75%
    COMPLETE = 4   # 75-100%

class PrecipitationType(Enum):
    """Types of precipitation."""

    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    FREEZING_RAIN = "freezing_rain"
    MAGICAL = "magical"

class MagicalWeatherSource(Enum):
    """Sources of magical weather phenomena."""

    ARCANE_ENERGY = "arcane_energy"
    DIVINE_POWER = "divine_power"
    ELEMENTAL_FORCE = "elemental_force"
    FAE_MAGIC = "fae_magic"
    SHADOW_MAGIC = "shadow_magic"
    NATURE_MAGIC = "nature_magic"
    TIME_DISTORTION = "time_distortion"
    PLANETARY_ALIGNMENT = "planetary_alignment"
    ANCIENT_CURSE = "ancient_curse"
    RIFT_ENERGY = "rift_energy"

# Weather type compatibility mappings
WEATHER_COMPATIBILITY: Dict[WeatherType, List[WeatherType]] = {
    WeatherType.CLEAR: [WeatherType.PARTLY_CLOUDY, WeatherType.LIGHT_WIND],
    WeatherType.PARTLY_CLOUDY: [WeatherType.CLEAR, WeatherType.OVERCAST, WeatherType.LIGHT_RAIN],
    WeatherType.OVERCAST: [WeatherType.PARTLY_CLOUDY, WeatherType.MODERATE_RAIN, WeatherType.LIGHT_SNOW],
    WeatherType.LIGHT_RAIN: [WeatherType.DRIZZLE, WeatherType.MODERATE_RAIN, WeatherType.OVERCAST],
    WeatherType.MODERATE_RAIN: [WeatherType.LIGHT_RAIN, WeatherType.HEAVY_RAIN, WeatherType.THUNDERSTORM],
    WeatherType.HEAVY_RAIN: [WeatherType.MODERATE_RAIN, WeatherType.THUNDERSTORM, WeatherType.HAILSTORM],
    WeatherType.LIGHT_SNOW: [WeatherType.DRIZZLE, WeatherType.MODERATE_SNOW, WeatherType.OVERCAST],
    WeatherType.MODERATE_SNOW: [WeatherType.LIGHT_SNOW, WeatherType.HEAVY_SNOW, WeatherType.BLIZZARD],
    WeatherType.HEAVY_SNOW: [WeatherType.MODERATE_SNOW, WeatherType.BLIZZARD, WeatherType.SLEET],
    WeatherType.THUNDERSTORM: [WeatherType.HEAVY_RAIN, WeatherType.SEVERE_THUNDERSTORM, WeatherType.HAILSTORM],
    WeatherType.LIGHT_FOG: [WeatherType.MODERATE_FOG, WeatherType.OVERCAST],
    WeatherType.MODERATE_FOG: [WeatherType.LIGHT_FOG, WeatherType.DENSE_FOG],
    WeatherType.LIGHT_WIND: [WeatherType.MODERATE_WIND, WeatherType.DUST_STORM],
    WeatherType.MODERATE_WIND: [WeatherType.LIGHT_WIND, WeatherType.STRONG_WIND],
    WeatherType.STRONG_WIND: [WeatherType.MODERATE_WIND, WeatherType.GALE_FORCE],
    WeatherType.GALE_FORCE: [WeatherType.STRONG_WIND, WeatherType.HURRICANE],
}

# Seasonal probability distributions
SEASONAL_PROBABILITIES: Dict[Season, Dict[WeatherType, float]] = {
    Season.SPRING: {
        WeatherType.CLEAR: 0.15,
        WeatherType.PARTLY_CLOUDY: 0.25,
        WeatherType.OVERCAST: 0.20,
        WeatherType.LIGHT_RAIN: 0.15,
        WeatherType.MODERATE_RAIN: 0.10,
        WeatherType.THUNDERSTORM: 0.08,
        WeatherType.LIGHT_WIND: 0.05,
        WeatherType.LIGHT_FOG: 0.02,
    },
    Season.SUMMER: {
        WeatherType.CLEAR: 0.30,
        WeatherType.PARTLY_CLOUDY: 0.25,
        WeatherType.OVERCAST: 0.15,
        WeatherType.LIGHT_RAIN: 0.08,
        WeatherType.THUNDERSTORM: 0.10,
        WeatherType.HEAVY_RAIN: 0.05,
        WeatherType.HEAT_WAVE: 0.05,
        WeatherType.LIGHT_WIND: 0.02,
    },
    Season.AUTUMN: {
        WeatherType.CLEAR: 0.12,
        WeatherType.PARTLY_CLOUDY: 0.20,
        WeatherType.OVERCAST: 0.25,
        WeatherType.LIGHT_RAIN: 0.15,
        WeatherType.MODERATE_RAIN: 0.12,
        WeatherType.FOG: 0.10,
        WeatherType.LIGHT_WIND: 0.04,
        WeatherType.MODERATE_WIND: 0.02,
    },
    Season.WINTER: {
        WeatherType.CLEAR: 0.10,
        WeatherType.OVERCAST: 0.30,
        WeatherType.LIGHT_SNOW: 0.15,
        WeatherType.MODERATE_SNOW: 0.12,
        WeatherType.HEAVY_SNOW: 0.08,
        WeatherType.BLIZZARD: 0.05,
        WeatherType.SLEET: 0.10,
        WeatherType.STRONG_WIND: 0.05,
        WeatherType.DENSE_FOG: 0.05,
    },
}

# Climate zone modifiers
CLIMATE_ZONE_MODIFIERS: Dict[ClimateZone, Dict[str, float]] = {
    ClimateZone.TROPICAL: {
        "temperature_modifier": 15.0,
        "humidity_modifier": 0.3,
        "precipitation_frequency": 0.4,
        "storm_frequency": 0.15,
    },
    ClimateZone.DESERT: {
        "temperature_modifier": 20.0,
        "humidity_modifier": -0.5,
        "precipitation_frequency": -0.4,
        "dust_storm_frequency": 0.2,
    },
    ClimateZone.TEMPERATE: {
        "temperature_modifier": 0.0,
        "humidity_modifier": 0.0,
        "precipitation_frequency": 0.0,
        "variability": 0.3,
    },
    ClimateZone.ARCTIC: {
        "temperature_modifier": -25.0,
        "humidity_modifier": -0.2,
        "precipitation_frequency": -0.2,
        "snow_frequency": 0.6,
    },
    ClimateZone.MOUNTAINOUS: {
        "temperature_modifier": -8.0,
        "humidity_modifier": -0.1,
        "wind_frequency": 0.3,
        "storm_frequency": 0.15,
    },
    ClimateZone.COASTAL: {
        "temperature_modifier": 2.0,
        "humidity_modifier": 0.2,
        "fog_frequency": 0.15,
        "wind_frequency": 0.2,
    },
}

def get_weather_description(weather_type: WeatherType, severity: WeatherSeverity) -> str:
    """Generate human-readable weather description."""

    descriptions = {
        (WeatherType.CLEAR, WeatherSeverity.CALM): "Perfectly clear skies with calm conditions",
        (WeatherType.PARTLY_CLOUDY, WeatherSeverity.MILD): "Partly cloudy with comfortable temperatures",
        (WeatherType.OVERCAST, WeatherSeverity.MODERATE): "Completely overcast with gray skies",
        (WeatherType.LIGHT_RAIN, WeatherSeverity.MODERATE): "Light rain falling steadily",
        (WeatherType.MODERATE_RAIN, WeatherSeverity.MODERATE): "Moderate rainfall making surfaces wet",
        (WeatherType.HEAVY_RAIN, WeatherSeverity.SEVERE): "Heavy downpour with reduced visibility",
        (WeatherType.THUNDERSTORM, WeatherSeverity.SEVERE): "Thunderstorm with lightning and heavy rain",
        (WeatherType.LIGHT_SNOW, WeatherSeverity.MODERATE): "Light snow dusting the landscape",
        (WeatherType.MODERATE_SNOW, WeatherSeverity.MODERATE): "Moderate snowfall accumulating on surfaces",
        (WeatherType.HEAVY_SNOW, WeatherSeverity.SEVERE): "Heavy snowfall creating deep accumulations",
        (WeatherType.BLIZZARD, WeatherSeverity.EXTREME): "Blizzard conditions with zero visibility",
        (WeatherType.LIGHT_FOG, WeatherSeverity.MILD): "Light fog slightly reducing visibility",
        (WeatherType.DENSE_FOG, WeatherSeverity.SEVERE): "Dense fog severely limiting visibility",
        (WeatherType.LIGHT_WIND, WeatherSeverity.MILD): "Light breeze rustling leaves",
        (WeatherType.STRONG_WIND, WeatherSeverity.MODERATE): "Strong winds making travel difficult",
        (WeatherType.GALE_FORCE, WeatherSeverity.SEVERE): "Gale force winds creating hazardous conditions",
        (WeatherType.MAGICAL_STORM, WeatherSeverity.EXTREME): "Arcane storm crackling with magical energy",
        (WeatherType.FAE_MIST, WeatherSeverity.MODERATE): "Ethereal mist shimmering with fae magic",
        (WeatherType.UNDEAD_FOG, WeatherSeverity.SEVERE): "Chilling fog that drains warmth and life",
    }

    return descriptions.get((weather_type, severity), f"{weather_type.value.replace('_', ' ').title()} conditions")

def get_severity_from_intensity(intensity: float) -> WeatherSeverity:
    """Convert intensity value (0-1) to weather severity."""

    if intensity < 0.1:
        return WeatherSeverity.CALM
    elif intensity < 0.3:
        return WeatherSeverity.MILD
    elif intensity < 0.5:
        return WeatherSeverity.MODERATE
    elif intensity < 0.7:
        return WeatherSeverity.SEVERE
    elif intensity < 0.9:
        return WeatherSeverity.EXTREME
    else:
        return WeatherSeverity.CATASTROPHIC