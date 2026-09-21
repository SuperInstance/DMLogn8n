"""
Weather Engine - Core Simulation System

The main weather simulation engine that orchestrates all weather components
and provides the primary interface for weather management.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
import json
from dataclasses import asdict

from .weather_state import WeatherState
from .weather_types import (
    WeatherType, WeatherSeverity, Season, ClimateZone,
    WindDirection, CloudCover, get_weather_description,
    get_severity_from_intensity, SEASONAL_PROBABILITIES, CLIMATE_ZONE_MODIFIERS
)
from .weather_events import WeatherEventManager
from .climate_patterns import ClimatePatterns
from .atmospheric_conditions import AtmosphericConditions
from ..algorithms.weather_simulation import WeatherSimulation
from ..algorithms.particle_physics import ParticlePhysics
from ..algorithms.wind_simulation import WindSimulation

class WeatherEngine:
    """Main weather simulation engine."""

    def __init__(self,
                 location: str = "default",
                 climate_zone: ClimateZone = ClimateZone.TEMPERATE,
                 altitude: float = 0.0,
                 season: Season = Season.SUMMER,
                 initial_time: Optional[datetime] = None,
                 config_path: Optional[str] = None):

        self.location = location
        self.climate_zone = climate_zone
        self.altitude = altitude
        self.season = season
        self.current_time = initial_time or datetime.now()

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize core components
        self.current_state = self._create_initial_state()
        self.event_manager = WeatherEventManager(self.config.get('events', {}))
        self.climate_patterns = ClimatePatterns(self.config.get('climate', {}))
        self.simulation = WeatherSimulation(self.config.get('simulation', {}))
        self.particle_physics = ParticlePhysics(self.config.get('particles', {}))
        self.wind_simulation = WindSimulation(self.config.get('wind', {}))

        # History tracking
        self.state_history: List[WeatherState] = []
        self.forecast_history: List[Dict[str, Any]] = []

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'weather_change': [],
            'extreme_event': [],
            'magical_phenomenon': [],
            'season_change': [],
            'climate_event': []
        }

        # Simulation parameters
        self.simulation_speed = 1.0  # Real-time multiplier
        self.forecast_hours = 72  # Default forecast range
        self.max_history_hours = 168  # Keep 7 days of history

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""

        default_config = {
            'simulation': {
                'time_step_minutes': 15,
                'stability_factor': 0.7,
                'transition_smoothness': 0.8,
                'extreme_event_frequency': 0.05,
                'magical_event_frequency': 0.02
            },
            'climate': {
                'seasonal_variation': 0.3,
                'diurnal_variation': 0.15,
                'altitude_effect': 0.0065,  # Temperature lapse rate
                'regional_modifiers': True
            },
            'events': {
                'enabled': True,
                'extreme_weather_probability': 0.1,
                'magical_phenomena_probability': 0.05,
                'max_concurrent_events': 3
            },
            'particles': {
                'enabled': True,
                'max_particles': 10000,
                'physics_accuracy': 'high',
                'render_distance': 500
            },
            'wind': {
                'complexity': 'medium',
                'turbulence_enabled': True,
                'thermal_effects': True,
                'orographic_effects': True
            }
        }

        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                for section in default_config:
                    if section in user_config:
                        default_config[section].update(user_config[section])
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")

        return default_config

    def _create_initial_state(self) -> WeatherState:
        """Create initial weather state based on location and climate."""

        # Get base weather for climate and season
        base_weather = self._get_seasonal_weather()

        # Apply climate zone modifiers
        temperature = base_weather['temperature']
        temperature += CLIMATE_ZONE_MODIFIERS.get(self.climate_zone, {}).get('temperature_modifier', 0)

        # Altitude adjustment
        temperature -= self.config['climate']['altitude_effect'] * (self.altitude / 100)

        # Create initial state
        state = WeatherState(
            weather_type=base_weather['type'],
            severity=base_weather['severity'],
            temperature=temperature,
            humidity=base_weather['humidity'],
            pressure=1013.25 - (self.altitude * 0.12),  # Standard pressure altitude formula
            wind_speed=base_weather['wind_speed'],
            wind_direction=base_weather['wind_direction'],
            location=self.location,
            altitude=self.altitude,
            climate_zone=self.climate_zone,
            season=self.season,
            timestamp=self.current_time
        )

        return state

    def _get_seasonal_weather(self) -> Dict[str, Any]:
        """Get weather probabilities for current season and climate."""

        # Base seasonal probabilities
        seasonal_probs = SEASONAL_PROBABILITIES.get(self.season, SEASONAL_PROBABILITIES[Season.SUMMER])

        # Apply climate zone modifiers
        climate_mods = CLIMATE_ZONE_MODIFIERS.get(self.climate_zone, {})

        # Weighted random selection
        weather_types = list(seasonal_probs.keys())
        probabilities = list(seasonal_probs.values())

        # Adjust probabilities based on climate
        if 'precipitation_frequency' in climate_mods:
            precip_adjustment = climate_mods['precipitation_frequency']
            for i, wtype in enumerate(weather_types):
                if 'rain' in wtype.value or 'snow' in wtype.value:
                    probabilities[i] = max(0.01, probabilities[i] + precip_adjustment)

        # Normalize probabilities
        total_prob = sum(probabilities)
        probabilities = [p / total_prob for p in probabilities]

        # Select weather type
        selected_weather = random.choices(weather_types, weights=probabilities)[0]

        # Generate weather parameters
        severity = random.choices(
            list(WeatherSeverity),
            weights=[0.3, 0.3, 0.2, 0.15, 0.04, 0.01]
        )[0]

        # Temperature range based on climate
        temp_ranges = {
            ClimateZone.TROPICAL: (20, 35),
            ClimateZone.DESERT: (15, 45),
            ClimateZone.TEMPERATE: (0, 25),
            ClimateZone.ARCTIC: (-30, -5),
            ClimateZone.MOUNTAINOUS: (-10, 15),
            ClimateZone.COASTAL: (5, 20),
        }

        temp_range = temp_ranges.get(self.climate_zone, (0, 25))
        temperature = random.uniform(*temp_range)

        return {
            'type': selected_weather,
            'severity': severity,
            'temperature': temperature,
            'humidity': random.uniform(0.3, 0.8),
            'wind_speed': random.uniform(0, 20),
            'wind_direction': random.choice(list(WindDirection))
        }

    def advance_time(self, minutes: float = 15.0):
        """Advance simulation time and update weather."""

        # Update time
        self.current_time += timedelta(minutes=minutes * self.simulation_speed)

        # Store previous state
        previous_state = self.current_state.copy()

        # Update weather simulation
        self._update_weather_simulation(minutes)

        # Process events
        self._process_weather_events(minutes)

        # Update atmospheric conditions
        self._update_atmospheric_conditions()

        # Check for significant changes
        if self._is_significant_change(previous_state, self.current_state):
            self._trigger_event_callbacks('weather_change', {
                'previous_state': previous_state,
                'new_state': self.current_state,
                'change_type': self._classify_change(previous_state, self.current_state)
            })

        # Update history
        self._update_history()

        # Check for seasonal changes
        self._check_seasonal_change()

    def _update_weather_simulation(self, time_minutes: float):
        """Update weather using simulation algorithms."""

        # Use advanced weather simulation
        new_state = self.simulation.simulate_step(
            current_state=self.current_state,
            time_step_minutes=time_minutes,
            climate_zone=self.climate_zone,
            altitude=self.altitude,
            season=self.season
        )

        # Apply wind simulation
        wind_data = self.wind_simulation.simulate_wind(
            current_wind_speed=self.current_state.wind_speed,
            current_wind_direction=self.current_state.wind_direction,
            weather_type=new_state.weather_type,
            terrain_type=self._get_terrain_type(),
            time_step_minutes=time_minutes
        )

        new_state.wind_speed = wind_data['speed']
        new_state.wind_direction = wind_data['direction']
        new_state.atmospheric_conditions.wind_shear = wind_data['shear']

        # Apply particle physics for atmospheric effects
        if self.config['particles']['enabled']:
            particle_effects = self.particle_physics.simulate_particles(
                weather_type=new_state.weather_type,
                wind_speed=new_state.wind_speed,
                temperature=new_state.temperature,
                humidity=new_state.humidity
            )
            new_state.atmospheric_conditions.air_quality.visibility_factor *= particle_effects['visibility_factor']

        # Validate new state
        new_state = self._validate_weather_state(new_state)

        # Update current state
        self.current_state = new_state
        self.current_state.timestamp = self.current_time

    def _process_weather_events(self, time_minutes: float):
        """Process weather events and phenomena."""

        # Check for extreme weather events
        if self.config['events']['enabled']:
            extreme_event = self.event_manager.check_extreme_event(
                current_state=self.current_state,
                climate_zone=self.climate_zone,
                time_step_minutes=time_minutes
            )

            if extreme_event:
                self.current_state.active_events.append(extreme_event.event_id)
                self._apply_weather_event(extreme_event)
                self._trigger_event_callbacks('extreme_event', {'event': extreme_event})

            # Check for magical phenomena
            magical_event = self.event_manager.check_magical_phenomenon(
                current_state=self.current_state,
                location=self.location,
                time_step_minutes=time_minutes
            )

            if magical_event:
                self.current_state.active_events.append(magical_event.event_id)
                self.current_state.magical_source = magical_event.source
                self.current_state.magical_intensity = magical_event.intensity
                self.current_state.magical_effects = magical_event.effects

                self.current_state.atmospheric_conditions.apply_magical_influence(
                    magical_event.source, magical_event.intensity
                )

                self._trigger_event_callbacks('magical_phenomenon', {'event': magical_event})

    def _apply_weather_event(self, event):
        """Apply weather event effects to current state."""

        event_effects = event.get_effects()

        # Apply weather type changes
        if 'weather_type' in event_effects:
            self.current_state.weather_type = event_effects['weather_type']

        # Apply severity changes
        if 'severity' in event_effects:
            self.current_state.severity = event_effects['severity']

        # Apply temperature changes
        if 'temperature_change' in event_effects:
            self.current_state.temperature += event_effects['temperature_change']

        # Apply wind changes
        if 'wind_speed_change' in event_effects:
            self.current_state.wind_speed = max(0, self.current_state.wind_speed + event_effects['wind_speed_change'])

        # Apply visibility changes
        if 'visibility_change' in event_effects:
            self.current_state.visibility = max(0.1, self.current_state.visibility + event_effects['visibility_change'])

    def _update_atmospheric_conditions(self):
        """Update detailed atmospheric conditions."""

        # Update air quality based on weather
        self.current_state.atmospheric_conditions.update_air_quality(
            self.current_state.weather_type,
            self.current_state.severity
        )

        # Update solar radiation based on weather and time
        self.current_state.atmospheric_conditions.solar_radiation = self._calculate_solar_radiation()

        # Update UV index
        self.current_state.atmospheric_conditions.uv_index = self._calculate_uv_index()

        # Update lunar conditions
        self.current_state.atmospheric_conditions.lunar_phase = self._calculate_lunar_phase()
        self.current_state.atmospheric_conditions.lunar_illumination = self._calculate_lunar_illumination()

        # Update atmospheric stability
        if len(self.current_state.atmospheric_conditions.layers) > 1:
            lapse_rate = self.current_state.atmospheric_conditions.calculate_lapse_rate(0, 1)
            self.current_state.atmospheric_conditions.layers[0].stability = (
                "stable" if lapse_rate > 9.8 else "unstable" if lapse_rate < 4.0 else "neutral"
            )

    def _calculate_solar_radiation(self) -> float:
        """Calculate current solar radiation based on time and weather."""

        # Time-based calculation (simplified)
        hour = self.current_time.hour
        minute = self.current_time.minute

        # Solar angle
        solar_angle = max(0, 90 - abs(12 - (hour + minute/60)) * 7.5)
        base_radiation = 800 * math.sin(math.radians(solar_angle))

        # Weather attenuation
        attenuation_factors = {
            WeatherType.CLEAR: 1.0,
            WeatherType.PARTLY_CLOUDY: 0.8,
            WeatherType.OVERCAST: 0.4,
            WeatherType.LIGHT_RAIN: 0.3,
            WeatherType.MODERATE_RAIN: 0.2,
            WeatherType.HEAVY_RAIN: 0.1,
            WeatherType.THUNDERSTORM: 0.1,
            WeatherType.LIGHT_SNOW: 0.4,
            WeatherType.HEAVY_SNOW: 0.2,
            WeatherType.BLIZZARD: 0.05,
            WeatherType.DENSE_FOG: 0.2,
        }

        attenuation = attenuation_factors.get(self.current_state.weather_type, 0.5)
        return base_radiation * attenuation

    def _calculate_uv_index(self) -> float:
        """Calculate UV index based on solar radiation and conditions."""

        radiation = self.current_state.atmospheric_conditions.solar_radiation
        base_uv = radiation / 100  # Rough conversion

        # Altitude effect
        altitude_factor = 1 + (self.altitude / 1000) * 0.1

        # Cloud cover effect
        cloud_factor = 1.0
        if self.current_state.cloud_cover == CloudCover.OVERCAST:
            cloud_factor = 0.3
        elif self.current_state.cloud_cover == CloudCover.COMPLETE:
            cloud_factor = 0.1

        # Ozone layer effect (simplified)
        ozone_factor = 0.9 if self.current_state.atmospheric_conditions.air_quality.ozone > 50 else 1.0

        uv_index = base_uv * altitude_factor * cloud_factor * ozone_factor
        return max(0, min(11, uv_index))

    def _calculate_lunar_phase(self) -> float:
        """Calculate lunar phase (0-1, new moon to full moon)."""

        # Simplified lunar phase calculation
        year = self.current_time.year
        month = self.current_time.month
        day = self.current_time.day

        # Approximate lunar cycle
        julian_date = (367 * year - 7 * (year + (month + 9) // 12) // 4 +
                      275 * month // 9 + day + 1721013.5)

        lunar_cycle = (julian_date - 2451549.5) % 29.53058867  # Synodic month
        phase = lunar_cycle / 29.53058867

        return phase

    def _calculate_lunar_illumination(self) -> float:
        """Calculate lunar illumination percentage (0-1)."""

        phase = self.current_state.atmospheric_conditions.lunar_phase
        # Simplified illumination calculation
        if phase <= 0.5:
            illumination = phase * 2
        else:
            illumination = 2 * (1 - phase)

        return illumination

    def _get_terrain_type(self) -> str:
        """Get terrain type for wind simulation."""

        # Simple terrain classification based on altitude and climate
        if self.altitude > 2000:
            return "mountain"
        elif self.climate_zone in [ClimateZone.COASTAL, ClimateZone.OCEANIC]:
            return "coastal"
        elif self.climate_zone == ClimateZone.DESERT:
            return "desert"
        elif self.altitude > 1000:
            return "hills"
        else:
            return "plains"

    def _validate_weather_state(self, state: WeatherState) -> WeatherState:
        """Validate and correct weather state values."""

        # Temperature validation
        state.temperature = max(-60, min(60, state.temperature))

        # Humidity validation
        state.humidity = max(0.0, min(1.0, state.humidity))

        # Pressure validation
        state.pressure = max(800, min(1100, state.pressure))

        # Wind speed validation
        state.wind_speed = max(0.0, min(200, state.wind_speed))

        # Visibility validation
        state.visibility = max(0.0, min(50, state.visibility))

        # Precipitation validation
        state.precipitation_intensity = max(0.0, min(100, state.precipitation_intensity))

        # Magical intensity validation
        state.magical_intensity = max(0.0, min(1.0, state.magical_intensity))

        return state

    def _is_significant_change(self, previous: WeatherState, current: WeatherState) -> bool:
        """Check if weather change is significant enough to trigger events."""

        changes = []

        # Weather type change
        if previous.weather_type != current.weather_type:
            changes.append('type')

        # Severity change
        if abs(previous.severity.value - current.severity.value) >= 2:
            changes.append('severity')

        # Temperature change
        if abs(previous.temperature - current.temperature) >= 5:
            changes.append('temperature')

        # Wind speed change
        if abs(previous.wind_speed - current.wind_speed) >= 15:
            changes.append('wind')

        # Visibility change
        if abs(previous.visibility - current.visibility) >= 3:
            changes.append('visibility')

        return len(changes) > 0

    def _classify_change(self, previous: WeatherState, current: WeatherState) -> str:
        """Classify the type of weather change."""

        if current.weather_type in [WeatherType.THUNDERSTORM, WeatherType.BLIZZARD, WeatherType.HURRICANE]:
            return 'extreme_weather'
        elif current.magical_intensity > 0.5:
            return 'magical_phenomenon'
        elif abs(current.temperature - previous.temperature) >= 10:
            return 'temperature_extreme'
        elif current.wind_speed > 50:
            return 'wind_event'
        else:
            return 'normal_transition'

    def _update_history(self):
        """Update historical records."""

        # Add current state to history
        self.state_history.append(self.current_state.copy())

        # Trim history if too long
        cutoff_time = self.current_time - timedelta(hours=self.max_history_hours)
        self.state_history = [state for state in self.state_history if state.timestamp > cutoff_time]

    def _check_seasonal_change(self):
        """Check for and handle seasonal changes."""

        month = self.current_time.month
        new_season = self._get_season_from_month(month)

        if new_season != self.season:
            old_season = self.season
            self.season = new_season
            self.current_state.season = new_season

            self._trigger_event_callbacks('season_change', {
                'previous_season': old_season,
                'new_season': new_season,
                'transition_date': self.current_time
            })

    def _get_season_from_month(self, month: int) -> Season:
        """Get season from month number."""

        if month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        elif month in [9, 10, 11]:
            return Season.AUTUMN
        else:
            return Season.WINTER

    def _trigger_event_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event callbacks."""

        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event callback: {e}")

    # Public API methods

    def get_current_weather(self) -> WeatherState:
        """Get current weather state."""

        return self.current_state

    def get_weather_description(self) -> str:
        """Get human-readable weather description."""

        return self.current_state.get_description()

    def forecast(self, hours: int = 24) -> List[WeatherState]:
        """Generate weather forecast for specified hours."""

        forecast = []
        temp_state = self.current_state.copy()
        temp_time = self.current_time

        # Simple forecast algorithm
        for i in range(hours):
            temp_time += timedelta(hours=1)

            # Use simulation for forecast
            forecast_state = self.simulation.simulate_step(
                current_state=temp_state,
                time_step_minutes=60,
                climate_zone=self.climate_zone,
                altitude=self.altitude,
                season=self.season,
                is_forecast=True
            )

            forecast_state.timestamp = temp_time
            forecast.append(forecast_state)
            temp_state = forecast_state

        return forecast

    def set_location(self, location: str, climate_zone: ClimateZone, altitude: float = 0.0):
        """Update location parameters."""

        self.location = location
        self.climate_zone = climate_zone
        self.altitude = altitude

        # Update current state
        self.current_state.location = location
        self.current_state.climate_zone = climate_zone
        self.current_state.altitude = altitude

        # Revalidate state
        self.current_state = self._validate_weather_state(self.current_state)

    def set_season(self, season: Season):
        """Set current season."""

        self.season = season
        self.current_state.season = season

    def apply_weather_control(self, weather_type: WeatherType, intensity: float, duration_hours: float = 1.0):
        """Apply player-controlled weather modification."""

        self.current_state.weather_type = weather_type
        self.current_state.severity = get_severity_from_intensity(intensity)

        # Create magical weather event for player control
        magical_event = {
            'event_id': f"player_control_{datetime.now().timestamp()}",
            'type': 'weather_control',
            'source': 'player_magic',
            'intensity': intensity,
            'duration': duration_hours,
            'effects': {
                'weather_type': weather_type,
                'severity': self.current_state.severity,
                'confidence': 0.9
            }
        }

        self.current_state.active_events.append(magical_event['event_id'])

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for weather events."""

        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def get_historical_data(self, hours: int = 24) -> List[WeatherState]:
        """Get historical weather data."""

        cutoff_time = self.current_time - timedelta(hours=hours)
        return [state for state in self.state_history if state.timestamp > cutoff_time]

    def save_state(self, file_path: str):
        """Save current weather state to file."""

        data = {
            'current_state': self.current_state.to_dict(),
            'location': self.location,
            'climate_zone': self.climate_zone.value,
            'altitude': self.altitude,
            'season': self.season.value,
            'current_time': self.current_time.isoformat(),
            'config': self.config
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_state(self, file_path: str):
        """Load weather state from file."""

        with open(file_path, 'r') as f:
            data = json.load(f)

        self.location = data['location']
        self.climate_zone = ClimateZone(data['climate_zone'])
        self.altitude = data['altitude']
        self.season = Season(data['season'])
        self.current_time = datetime.fromisoformat(data['current_time'])
        self.config = data.get('config', self.config)

        self.current_state = WeatherState.from_dict(data['current_state'])

    def get_statistics(self) -> Dict[str, Any]:
        """Get weather statistics for current location."""

        if len(self.state_history) < 2:
            return {}

        temperatures = [state.temperature for state in self.state_history]
        wind_speeds = [state.wind_speed for state in self.state_history]
        visibilities = [state.visibility for state in self.state_history]

        weather_type_counts = {}
        for state in self.state_history:
            wtype = state.weather_type.value
            weather_type_counts[wtype] = weather_type_counts.get(wtype, 0) + 1

        return {
            'period_hours': len(self.state_history),
            'temperature': {
                'average': sum(temperatures) / len(temperatures),
                'minimum': min(temperatures),
                'maximum': max(temperatures),
                'range': max(temperatures) - min(temperatures)
            },
            'wind_speed': {
                'average': sum(wind_speeds) / len(wind_speeds),
                'maximum': max(wind_speeds),
                'minimum': min(wind_speeds)
            },
            'visibility': {
                'average': sum(visibilities) / len(visibilities),
                'minimum': min(visibilities)
            },
            'weather_distribution': weather_type_counts,
            'extreme_events_count': len([s for s in self.state_history if s.is_hazardous()]),
            'magical_events_count': len([s for s in self.state_history if s.magical_intensity > 0.5])
        }