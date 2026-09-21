"""
Atmospheric Conditions Module

Handles detailed atmospheric modeling including air quality, pressure systems,
and other meteorological phenomena.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

from .weather_types import WeatherType, WeatherSeverity, ClimateZone, MagicalWeatherSource

@dataclass
class PressureSystem:
    """Represents an atmospheric pressure system."""

    pressure_type: str  # "high", "low", "ridge", "trough"
    center_pressure: float  # millibars
    strength: float  # 0-1
    movement_speed: float  # km/h
    movement_direction: float  # degrees
    radius: float  # kilometers
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AirQuality:
    """Represents air quality conditions."""

    aqi: int  # Air Quality Index (0-500)
    pm25: float  # PM2.5 concentration (μg/m³)
    pm10: float  # PM10 concentration (μg/m³)
    ozone: float  # Ozone concentration (ppb)
    nitrogen_dioxide: float  # NO2 concentration (ppb)
    sulfur_dioxide: float  # SO2 concentration (ppb)
    carbon_monoxide: float  # CO concentration (ppm)
    visibility_factor: float  # 0-1, affects visibility
    health_impact: str  # "good", "moderate", "unhealthy_sensitive", "unhealthy", "very_unhealthy", "hazardous"

@dataclass
class AtmosphericLayer:
    """Represents a layer of the atmosphere."""

    altitude: float  # meters
    temperature: float  # Celsius
    humidity: float  # 0-1
    pressure: float  # millibars
    wind_speed: float  # km/h
    wind_direction: float  # degrees
    stability: str  # "stable", "unstable", "neutral"
    cloud_type: Optional[str] = None  # stratus, cumulus, cirrus, etc.
    turbulence: float = 0.0  # 0-1

@dataclass
class MagicalAtmosphere:
    """Represents magical atmospheric conditions."""

    arcane_energy: float  # 0-1, ambient magical energy
    elemental_resonance: Dict[str, float]  # element -> resonance level
    planar_influence: Dict[str, float]  # plane -> influence strength
    divine_presence: Dict[str, float]  # deity -> presence level
    curse_strength: float  # 0-1
    blessing_strength: float  # 0-1
    magical_stability: float  # 0-1, atmospheric magical stability
    rift_activity: float  # 0-1, dimensional rift activity

@dataclass
class AtmosphericConditions:
    """Comprehensive atmospheric conditions data."""

    # Air masses and pressure systems
    air_mass_type: str = "continental_tropical"  # maritime/continental, tropical/polar/arctic
    pressure_systems: List[PressureSystem] = field(default_factory=list)
    frontal_boundaries: List[Dict[str, float]] = field(default_factory=list)  # front_type, position, strength

    # Atmospheric layers
    layers: List[AtmosphericLayer] = field(default_factory=list)
    boundary_layer_height: float = 1000.0  # meters
    tropopause_height: float = 11000.0  # meters

    # Air quality and pollutants
    air_quality: AirQuality = field(default_factory=lambda: AirQuality(
        aqi=50, pm25=12.0, pm10=20.0, ozone=30.0,
        nitrogen_dioxide=20.0, sulfur_dioxide=5.0,
        carbon_monoxide=1.0, visibility_factor=1.0, health_impact="good"
    ))

    # Magical atmospheric conditions
    magical_atmosphere: MagicalAtmosphere = field(default_factory=lambda: MagicalAtmosphere(
        arcane_energy=0.1,
        elemental_resonance={"fire": 0.0, "water": 0.0, "earth": 0.0, "air": 0.0},
        planar_influence={},
        divine_presence={},
        curse_strength=0.0,
        blessing_strength=0.0,
        magical_stability=0.8,
        rift_activity=0.0
    ))

    # Solar and lunar conditions
    solar_radiation: float = 800.0  # W/m²
    uv_index: float = 5.0  # 0-11+
    lunar_phase: float = 0.0  # 0-1 (new to full moon)
    lunar_illumination: float = 0.0  # 0-1

    # Advanced meteorological data
    vorticity: float = 0.0  # 1/s
    divergence: float = 0.0  # 1/s
    helicity: float = 0.0  # m²/s²
    cape: float = 0.0  # Convective Available Potential Energy (J/kg)
    cin: float = 0.0  # Convective Inhibition (J/kg)
    lifted_index: float = 0.0  # °C
    wind_shear: float = 0.0  # 1/s

    # Environmental factors
    pollen_count: int = 0  # grains/m³
    mold_spores: int = 0  # spores/m³
    volcanic_ash: float = 0.0  # μg/m³
    wildfire_smoke: float = 0.0  # μg/m³

    def __post_init__(self):
        """Initialize atmospheric layers if not provided."""
        if not self.layers:
            self._create_standard_atmosphere()

    def _create_standard_atmosphere(self):
        """Create a standard atmospheric profile."""

        # Standard atmosphere layers (simplified)
        layer_data = [
            {"altitude": 0, "temp": 15.0, "humidity": 0.5, "pressure": 1013.25, "wind_speed": 5.0},
            {"altitude": 1000, "temp": 8.5, "humidity": 0.6, "pressure": 900.0, "wind_speed": 10.0},
            {"altitude": 2000, "temp": 2.0, "humidity": 0.4, "pressure": 800.0, "wind_speed": 15.0},
            {"altitude": 5000, "temp": -17.5, "humidity": 0.2, "pressure": 540.0, "wind_speed": 25.0},
            {"altitude": 8000, "temp": -37.0, "humidity": 0.1, "pressure": 356.0, "wind_speed": 35.0},
            {"altitude": 11000, "temp": -56.5, "humidity": 0.0, "pressure": 226.0, "wind_speed": 40.0},
        ]

        for i, data in enumerate(layer_data):
            stability = "stable" if i < 2 else "neutral" if i < 4 else "unstable"

            self.layers.append(AtmosphericLayer(
                altitude=data["altitude"],
                temperature=data["temp"],
                humidity=data["humidity"],
                pressure=data["pressure"],
                wind_speed=data["wind_speed"],
                wind_direction=270.0,  # Prevailing westerlies
                stability=stability,
                turbulence=0.1 if stability == "stable" else 0.5
            ))

    def calculate_lapse_rate(self, bottom_layer: int, top_layer: int) -> float:
        """Calculate temperature lapse rate between layers."""

        if bottom_layer >= len(self.layers) or top_layer >= len(self.layers):
            return 6.5  # Standard lapse rate

        bottom = self.layers[bottom_layer]
        top = self.layers[top_layer]

        altitude_diff = top.altitude - bottom.altitude
        temp_diff = top.temperature - bottom.temperature

        return (temp_diff / altitude_diff) * 1000  # °C per 1000m

    def is_stable_atmosphere(self) -> bool:
        """Determine if atmosphere is stable based on lapse rates."""

        # Check environmental lapse rate
        if len(self.layers) >= 2:
            lapse_rate = self.calculate_lapse_rate(0, len(self.layers) - 1)
            # Stable if lapse rate < environmental lapse rate
            return abs(lapse_rate) < 6.5

        return True

    def get_storm_potential(self) -> float:
        """Calculate storm formation potential (0-1)."""

        potential = 0.0

        # CAPE contribution
        if self.cape > 1000:
            potential += 0.3
        elif self.cape > 500:
            potential += 0.2
        elif self.cape > 250:
            potential += 0.1

        # Lifted index contribution
        if self.lifted_index < -5:
            potential += 0.3
        elif self.lifted_index < -3:
            potential += 0.2
        elif self.lifted_index < 0:
            potential += 0.1

        # Wind shear contribution
        if self.wind_shear > 0.02:
            potential += 0.2
        elif self.wind_shear > 0.01:
            potential += 0.1

        # Humidity contribution
        if len(self.layers) > 0 and self.layers[0].humidity > 0.7:
            potential += 0.2

        # Magical contribution
        potential += self.magical_atmosphere.arcane_energy * 0.3

        return min(1.0, potential)

    def update_air_quality(self, weather_type: WeatherType, severity: WeatherSeverity):
        """Update air quality based on weather conditions."""

        base_aqi = self.air_quality.aqi

        # Weather impacts on air quality
        weather_impacts = {
            WeatherType.CLEAR: -10,  # Clearing improves air quality
            WeatherType.RAIN: -15,   # Rain cleans air
            WeatherType.HEAVY_RAIN: -25,
            WeatherType.THUNDERSTORM: -20,
            WeatherType.WIND: -5,    # Wind disperses pollutants
            WeatherType.DUST_STORM: 50,   # Dust storms worsen air quality
            WeatherType.WILDFIRE_SMOKE: 80,
            WeatherType.VOLCANIC_ASH: 100,
        }

        impact = weather_impacts.get(weather_type, 0) * (severity.value / 4.0)
        self.air_quality.aqi = max(0, min(500, base_aqi + impact))

        # Update health impact based on AQI
        if self.air_quality.aqi <= 50:
            self.air_quality.health_impact = "good"
        elif self.air_quality.aqi <= 100:
            self.air_quality.health_impact = "moderate"
        elif self.air_quality.aqi <= 150:
            self.air_quality.health_impact = "unhealthy_sensitive"
        elif self.air_quality.aqi <= 200:
            self.air_quality.health_impact = "unhealthy"
        elif self.air_quality.aqi <= 300:
            self.air_quality.health_impact = "very_unhealthy"
        else:
            self.air_quality.health_impact = "hazardous"

        # Update visibility factor
        if self.air_quality.aqi > 150:
            self.air_quality.visibility_factor = max(0.3, 1.0 - (self.air_quality.aqi - 150) / 350)

    def apply_magical_influence(self, source: MagicalWeatherSource, intensity: float):
        """Apply magical influence to atmospheric conditions."""

        self.magical_atmosphere.arcane_energy = min(1.0, self.magical_atmosphere.arcane_energy + intensity * 0.3)

        if source == MagicalWeatherSource.ELEMENTAL_FORCE:
            # Boost elemental resonance
            for element in self.magical_atmosphere.elemental_resonance:
                self.magical_atmosphere.elemental_resonance[element] = min(1.0,
                    self.magical_atmosphere.elemental_resonance[element] + intensity * 0.2)

        elif source == MagicalWeatherSource.SHADOW_MAGIC:
            # Create cold, stable conditions
            for layer in self.layers:
                layer.temperature -= intensity * 5
                layer.stability = "stable"
            self.magical_atmosphere.curse_strength = min(1.0,
                self.magical_atmosphere.curse_strength + intensity * 0.4)

        elif source == MagicalWeatherSource.DIVINE_POWER:
            # Create benevolent conditions
            self.magical_atmosphere.blessing_strength = min(1.0,
                self.magical_atmosphere.blessing_strength + intensity * 0.4)
            self.magical_atmosphere.magical_stability = min(1.0,
                self.magical_atmosphere.magical_stability + intensity * 0.3)

        elif source == MagicalWeatherSource.RIFT_ENERGY:
            # Create chaotic, unstable conditions
            self.magical_atmosphere.rift_activity = min(1.0,
                self.magical_atmosphere.rift_activity + intensity * 0.5)
            self.magical_atmosphere.magical_stability = max(0.0,
                self.magical_atmosphere.magical_stability - intensity * 0.4)
            for layer in self.layers:
                layer.turbulence = min(1.0, layer.turbulence + intensity * 0.3)

    def get_layer_at_altitude(self, altitude: float) -> Optional[AtmosphericLayer]:
        """Get atmospheric layer at specific altitude."""

        # Find the layer containing this altitude
        for i, layer in enumerate(self.layers):
            if i == len(self.layers) - 1 or altitude < self.layers[i + 1].altitude:
                # Interpolate between layers
                if i < len(self.layers) - 1 and altitude > layer.altitude:
                    return self._interpolate_layers(layer, self.layers[i + 1], altitude)
                return layer

        return None

    def _interpolate_layers(self, lower_layer: AtmosphericLayer, upper_layer: AtmosphericLayer, altitude: float) -> AtmosphericLayer:
        """Interpolate between two atmospheric layers."""

        ratio = (altitude - lower_layer.altitude) / (upper_layer.altitude - lower_layer.altitude)

        return AtmosphericLayer(
            altitude=altitude,
            temperature=lower_layer.temperature + ratio * (upper_layer.temperature - lower_layer.temperature),
            humidity=lower_layer.humidity + ratio * (upper_layer.humidity - lower_layer.humidity),
            pressure=lower_layer.pressure + ratio * (upper_layer.pressure - lower_layer.pressure),
            wind_speed=lower_layer.wind_speed + ratio * (upper_layer.wind_speed - lower_layer.wind_speed),
            wind_direction=lower_layer.wind_direction + ratio * (upper_layer.wind_direction - lower_layer.wind_direction),
            stability=lower_layer.stability if ratio < 0.5 else upper_layer.stability,
            turbulence=lower_layer.turbulence + ratio * (upper_layer.turbulence - lower_layer.turbulence)
        )

    def to_dict(self) -> Dict:
        """Convert atmospheric conditions to dictionary."""

        return {
            'air_mass_type': self.air_mass_type,
            'pressure_systems': [
                {
                    'pressure_type': ps.pressure_type,
                    'center_pressure': ps.center_pressure,
                    'strength': ps.strength,
                    'movement_speed': ps.movement_speed,
                    'movement_direction': ps.movement_direction,
                    'radius': ps.radius,
                    'timestamp': ps.timestamp.isoformat()
                } for ps in self.pressure_systems
            ],
            'frontal_boundaries': self.frontal_boundaries,
            'layers': [
                {
                    'altitude': layer.altitude,
                    'temperature': layer.temperature,
                    'humidity': layer.humidity,
                    'pressure': layer.pressure,
                    'wind_speed': layer.wind_speed,
                    'wind_direction': layer.wind_direction,
                    'stability': layer.stability,
                    'cloud_type': layer.cloud_type,
                    'turbulence': layer.turbulence
                } for layer in self.layers
            ],
            'boundary_layer_height': self.boundary_layer_height,
            'tropopause_height': self.tropopause_height,
            'air_quality': {
                'aqi': self.air_quality.aqi,
                'pm25': self.air_quality.pm25,
                'pm10': self.air_quality.pm10,
                'ozone': self.air_quality.ozone,
                'nitrogen_dioxide': self.air_quality.nitrogen_dioxide,
                'sulfur_dioxide': self.air_quality.sulfur_dioxide,
                'carbon_monoxide': self.air_quality.carbon_monoxide,
                'visibility_factor': self.air_quality.visibility_factor,
                'health_impact': self.air_quality.health_impact
            },
            'magical_atmosphere': {
                'arcane_energy': self.magical_atmosphere.arcane_energy,
                'elemental_resonance': self.magical_atmosphere.elemental_resonance,
                'planar_influence': self.magical_atmosphere.planar_influence,
                'divine_presence': self.magical_atmosphere.divine_presence,
                'curse_strength': self.magical_atmosphere.curse_strength,
                'blessing_strength': self.magical_atmosphere.blessing_strength,
                'magical_stability': self.magical_atmosphere.magical_stability,
                'rift_activity': self.magical_atmosphere.rift_activity
            },
            'solar_radiation': self.solar_radiation,
            'uv_index': self.uv_index,
            'lunar_phase': self.lunar_phase,
            'lunar_illumination': self.lunar_illumination,
            'vorticity': self.vorticity,
            'divergence': self.divergence,
            'helicity': self.helicity,
            'cape': self.cape,
            'cin': self.cin,
            'lifted_index': self.lifted_index,
            'wind_shear': self.wind_shear,
            'pollen_count': self.pollen_count,
            'mold_spores': self.mold_spores,
            'volcanic_ash': self.volcanic_ash,
            'wildfire_smoke': self.wildfire_smoke
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AtmosphericConditions':
        """Create atmospheric conditions from dictionary."""

        conditions = cls()

        # Basic properties
        conditions.air_mass_type = data.get('air_mass_type', 'continental_tropical')
        conditions.boundary_layer_height = data.get('boundary_layer_height', 1000.0)
        conditions.tropopause_height = data.get('tropopause_height', 11000.0)

        # Pressure systems
        conditions.pressure_systems = [
            PressureSystem(
                pressure_type=ps['pressure_type'],
                center_pressure=ps['center_pressure'],
                strength=ps['strength'],
                movement_speed=ps['movement_speed'],
                movement_direction=ps['movement_direction'],
                radius=ps['radius'],
                timestamp=datetime.fromisoformat(ps['timestamp'])
            ) for ps in data.get('pressure_systems', [])
        ]

        # Frontal boundaries
        conditions.frontal_boundaries = data.get('frontal_boundaries', [])

        # Atmospheric layers
        conditions.layers = [
            AtmosphericLayer(
                altitude=layer['altitude'],
                temperature=layer['temperature'],
                humidity=layer['humidity'],
                pressure=layer['pressure'],
                wind_speed=layer['wind_speed'],
                wind_direction=layer['wind_direction'],
                stability=layer['stability'],
                cloud_type=layer.get('cloud_type'),
                turbulence=layer.get('turbulence', 0.0)
            ) for layer in data.get('layers', [])
        ]

        # Air quality
        aq_data = data.get('air_quality', {})
        conditions.air_quality = AirQuality(
            aqi=aq_data.get('aqi', 50),
            pm25=aq_data.get('pm25', 12.0),
            pm10=aq_data.get('pm10', 20.0),
            ozone=aq_data.get('ozone', 30.0),
            nitrogen_dioxide=aq_data.get('nitrogen_dioxide', 20.0),
            sulfur_dioxide=aq_data.get('sulfur_dioxide', 5.0),
            carbon_monoxide=aq_data.get('carbon_monoxide', 1.0),
            visibility_factor=aq_data.get('visibility_factor', 1.0),
            health_impact=aq_data.get('health_impact', 'good')
        )

        # Magical atmosphere
        mag_data = data.get('magical_atmosphere', {})
        conditions.magical_atmosphere = MagicalAtmosphere(
            arcane_energy=mag_data.get('arcane_energy', 0.1),
            elemental_resonance=mag_data.get('elemental_resonance', {"fire": 0.0, "water": 0.0, "earth": 0.0, "air": 0.0}),
            planar_influence=mag_data.get('planar_influence', {}),
            divine_presence=mag_data.get('divine_presence', {}),
            curse_strength=mag_data.get('curse_strength', 0.0),
            blessing_strength=mag_data.get('blessing_strength', 0.0),
            magical_stability=mag_data.get('magical_stability', 0.8),
            rift_activity=mag_data.get('rift_activity', 0.0)
        )

        # Solar and lunar
        conditions.solar_radiation = data.get('solar_radiation', 800.0)
        conditions.uv_index = data.get('uv_index', 5.0)
        conditions.lunar_phase = data.get('lunar_phase', 0.0)
        conditions.lunar_illumination = data.get('lunar_illumination', 0.0)

        # Advanced meteorological data
        conditions.vorticity = data.get('vorticity', 0.0)
        conditions.divergence = data.get('divergence', 0.0)
        conditions.helicity = data.get('helicity', 0.0)
        conditions.cape = data.get('cape', 0.0)
        conditions.cin = data.get('cin', 0.0)
        conditions.lifted_index = data.get('lifted_index', 0.0)
        conditions.wind_shear = data.get('wind_shear', 0.0)

        # Environmental factors
        conditions.pollen_count = data.get('pollen_count', 0)
        conditions.mold_spores = data.get('mold_spores', 0)
        conditions.volcanic_ash = data.get('volcanic_ash', 0.0)
        conditions.wildfire_smoke = data.get('wildfire_smoke', 0.0)

        return conditions