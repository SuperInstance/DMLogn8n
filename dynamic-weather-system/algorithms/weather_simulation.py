"""
Weather Simulation Algorithm

Core weather simulation engine using mathematical models for atmospheric
physics, thermodynamics, and fluid dynamics.
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from ..core.weather_state import WeatherState
from ..core.weather_types import (
    WeatherType, WeatherSeverity, Season, ClimateZone,
    WindDirection, CloudCover, PrecipitationType
)
from ..core.climate_patterns import ClimatePatterns
from .temperature_dynamics import TemperatureDynamics
from .pressure_systems import PressureSystemSimulation
from .precipitation_models import PrecipitationModels
from .wind_simulation import WindSimulation

class WeatherSimulation:
    """Advanced weather simulation using physical models."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.time_step_minutes = config.get('time_step_minutes', 15)
        self.stability_factor = config.get('stability_factor', 0.7)
        self.transition_smoothness = config.get('transition_smoothness', 0.8)

        # Initialize sub-systems
        self.temperature_dynamics = TemperatureDynamics(config)
        self.pressure_systems = PressureSystemSimulation(config)
        self.precipitation_models = PrecipitationModels(config)
        self.wind_simulation = WindSimulation(config)

        # Simulation state
        self.pressure_field: Dict[str, float] = {}
        self.temperature_field: Dict[str, float] = {}
        self.humidity_field: Dict[str, float] = {}
        self.wind_field: Dict[str, Tuple[float, float]] = {}  # u, v components

        # Physical constants
        self.GRAVITY = 9.81  # m/s²
        self.GAS_CONSTANT = 287.05  # J/(kg·K) for dry air
        self.SPECIFIC_HEAT_AIR = 1005  # J/(kg·K)
        self.LATENT_HEAT_VAPORIZATION = 2.5e6  # J/kg
        self.STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)

    def simulate_step(self, current_state: WeatherState, time_step_minutes: float,
                     climate_zone: ClimateZone, altitude: float, season: Season,
                     is_forecast: bool = False) -> WeatherState:
        """Perform one simulation step."""

        # Create new state based on current
        new_state = current_state.copy()
        new_state.timestamp += timedelta(minutes=time_step_minutes)

        # Update atmospheric fields
        self._update_atmospheric_fields(current_state, time_step_minutes)

        # Calculate weather transitions
        weather_transition = self._calculate_weather_transition(
            current_state, climate_zone, altitude, season, time_step_minutes
        )

        # Apply temperature dynamics
        new_state = self.temperature_dynamics.simulate_temperature_change(
            new_state, altitude, climate_zone, season, time_step_minutes
        )

        # Apply pressure system evolution
        pressure_change = self.pressure_systems.simulate_pressure_change(
            current_state, time_step_minutes, climate_zone
        )
        new_state.pressure += pressure_change

        # Update humidity and precipitation
        new_state = self._update_humidity_and_precipitation(
            new_state, time_step_minutes, climate_zone, altitude
        )

        # Update wind conditions
        wind_update = self.wind_simulation.simulate_wind_change(
            current_state, new_state, time_step_minutes
        )
        new_state.wind_speed = wind_update['speed']
        new_state.wind_direction = wind_update['direction']

        # Apply weather transition
        if weather_transition['change_type'] != 'none':
            new_state = self._apply_weather_transition(new_state, weather_transition)

        # Update cloud cover
        new_state.cloud_cover = self._calculate_cloud_cover(
            new_state, climate_zone, season
        )

        # Update visibility
        new_state.visibility = self._calculate_visibility(new_state)

        # Update precipitation type and intensity
        new_state = self._update_precipitation_details(new_state)

        # Apply stability and smoothing
        new_state = self._apply_stability_factors(current_state, new_state)

        # Validate final state
        new_state = self._validate_state(new_state)

        return new_state

    def _update_atmospheric_fields(self, state: WeatherState, time_step_minutes: float):
        """Update atmospheric field values for simulation."""

        # Simplified 2D grid simulation
        grid_size = 10  # Simple 10x10 grid

        # Initialize fields if needed
        if not self.pressure_field:
            for i in range(grid_size):
                for j in range(grid_size):
                    key = f"{i},{j}"
                    self.pressure_field[key] = state.pressure + random.uniform(-5, 5)
                    self.temperature_field[key] = state.temperature + random.uniform(-2, 2)
                    self.humidity_field[key] = state.humidity + random.uniform(-0.1, 0.1)

        # Apply diffusion and advection
        dt = time_step_minutes * 60  # Convert to seconds

        # Pressure diffusion (simplified)
        new_pressure = {}
        for i in range(grid_size):
            for j in range(grid_size):
                key = f"{i},{j}"
                neighbors = self._get_neighbors(i, j, grid_size)
                laplacian = sum(self.pressure_field[n] for n in neighbors) / len(neighbors)
                laplacian -= self.pressure_field[key]
                new_pressure[key] = self.pressure_field[key] + 0.1 * laplacian * dt / 3600

        self.pressure_field = new_pressure

        # Temperature advection (simplified)
        new_temperature = {}
        for i in range(grid_size):
            for j in range(grid_size):
                key = f"{i},{j}"
                # Simple advection with wind
                wind_u = state.wind_speed * math.cos(math.radians(state.wind_direction.value))
                wind_v = state.wind_speed * math.sin(math.radians(state.wind_direction.value))

                # Backward advection
                source_i = (i - wind_u * dt / 1000) % grid_size
                source_j = (j - wind_v * dt / 1000) % grid_size

                # Bilinear interpolation
                i0, j0 = int(source_i), int(source_j)
                i1, j1 = (i0 + 1) % grid_size, (j0 + 1) % grid_size
                s, t = source_i - i0, source_j - j0

                temp_00 = self.temperature_field[f"{i0},{j0}"]
                temp_01 = self.temperature_field[f"{i0},{j1}"]
                temp_10 = self.temperature_field[f"{i1},{j0}"]
                temp_11 = self.temperature_field[f"{i1},{j1}"]

                new_temperature[key] = (
                    (1-s) * (1-t) * temp_00 +
                    (1-s) * t * temp_01 +
                    s * (1-t) * temp_10 +
                    s * t * temp_11
                )

        self.temperature_field = new_temperature

    def _get_neighbors(self, i: int, j: int, grid_size: int) -> List[str]:
        """Get neighboring grid points."""

        neighbors = []
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni = (i + di) % grid_size
                nj = (j + dj) % grid_size
                neighbors.append(f"{ni},{nj}")
        return neighbors

    def _calculate_weather_transition(self, state: WeatherState, climate_zone: ClimateZone,
                                   altitude: float, season: Season, time_step_minutes: float) -> Dict[str, Any]:
        """Calculate weather type transitions."""

        # Get climate patterns
        from ..core.climate_patterns import ClimatePatterns
        climate = ClimatePatterns({})
        seasonal_pattern = climate.get_seasonal_pattern(climate_zone, season)

        if not seasonal_pattern:
            return {'change_type': 'none'}

        # Calculate transition probabilities
        transition_prob = self._calculate_transition_probability(state, seasonal_pattern, climate_zone)

        # Check for transition
        if random.random() < transition_prob:
            # Select new weather type
            new_weather = self._select_new_weather_type(state, seasonal_pattern, climate_zone)
            if new_weather != state.weather_type:
                return {
                    'change_type': 'weather_type',
                    'new_weather_type': new_weather,
                    'transition_probability': transition_prob
                }

        # Check for severity changes
        severity_change_prob = self._calculate_severity_change_probability(state, climate_zone)
        if random.random() < severity_change_prob:
            new_severity = self._select_new_severity(state.severity)
            if new_severity != state.severity:
                return {
                    'change_type': 'severity',
                    'new_severity': new_severity,
                    'transition_probability': severity_change_prob
                }

        return {'change_type': 'none'}

    def _calculate_transition_probability(self, state: WeatherState,
                                        seasonal_pattern, climate_zone: ClimateZone) -> float:
        """Calculate probability of weather type transition."""

        base_prob = 0.1  # Base 10% chance per time step

        # Adjust based on current weather stability
        if state.weather_type in [WeatherType.CLEAR, WeatherType.OVERCAST]:
            base_prob *= 0.5  # Stable conditions
        elif state.weather_type in [WeatherType.THUNDERSTORM, WeatherType.BLIZZARD]:
            base_prob *= 2.0  # Unstable conditions

        # Adjust based on pressure changes
        if hasattr(state, 'previous_pressure'):
            pressure_change = abs(state.pressure - state.previous_pressure)
            base_prob *= (1 + pressure_change / 10)

        # Climate zone influence
        climate_factors = {
            ClimateZone.TEMPERATE: 1.0,
            ClimateZone.TROPICAL: 1.3,  # More variable
            ClimateZone.DESERT: 0.7,    # Less variable
            ClimateZone.ARCTIC: 0.8,    # Relatively stable
            ClimateZone.MOUNTAINOUS: 1.5,  # Highly variable
            ClimateZone.COASTAL: 1.2,   # Moderately variable
        }

        base_prob *= climate_factors.get(climate_zone, 1.0)

        return min(0.8, base_prob)  # Cap at 80%

    def _select_new_weather_type(self, state: WeatherState, seasonal_pattern,
                                climate_zone: ClimateZone) -> WeatherType:
        """Select new weather type based on conditions."""

        # Get weather type probabilities from seasonal pattern
        probabilities = seasonal_pattern.weather_type_probabilities.copy()

        # Adjust probabilities based on current conditions
        if state.pressure < 1000:  # Low pressure - favor precipitation
            for wtype in probabilities:
                if 'rain' in wtype.value or 'snow' in wtype.value or 'storm' in wtype.value:
                    probabilities[wtype] *= 2.0

        elif state.pressure > 1020:  # High pressure - favor clear conditions
            for wtype in probabilities:
                if wtype == WeatherType.CLEAR or wtype == WeatherType.PARTLY_CLOUDY:
                    probabilities[wtype] *= 1.5

        # Temperature influence
        if state.temperature < 0:  # Freezing - favor snow
            for wtype in probabilities:
                if 'snow' in wtype.value:
                    probabilities[wtype] *= 3.0

        # Humidity influence
        if state.humidity > 0.8:  # High humidity - favor precipitation/fog
            for wtype in probabilities:
                if 'rain' in wtype.value or 'snow' in wtype.value or 'fog' in wtype.value:
                    probabilities[wtype] *= 2.0

        # Normalize probabilities
        total_prob = sum(probabilities.values())
        normalized_probs = {wtype: prob / total_prob for wtype, prob in probabilities.items()}

        # Select weather type
        weather_types = list(normalized_probs.keys())
        weights = list(normalized_probs.values())
        selected = random.choices(weather_types, weights=weights)[0]

        return selected

    def _calculate_severity_change_probability(self, state: WeatherState,
                                             climate_zone: ClimateZone) -> float:
        """Calculate probability of severity level change."""

        base_prob = 0.05  # 5% base chance

        # Increase probability during transitional weather
        if state.weather_type in [WeatherType.PARTLY_CLOUDY, WeatherType.OVERCAST]:
            base_prob *= 2.0

        # Increase probability during extreme conditions
        if state.pressure < 990 or state.pressure > 1030:
            base_prob *= 1.5

        if state.wind_speed > 30:
            base_prob *= 1.5

        return min(0.3, base_prob)

    def _select_new_severity(self, current_severity: WeatherSeverity) -> WeatherSeverity:
        """Select new severity level."""

        # Favor gradual changes
        if current_severity == WeatherSeverity.CALM:
            return random.choice([WeatherSeverity.CALM, WeatherSeverity.MILD])
        elif current_severity == WeatherSeverity.CATASTROPHIC:
            return random.choice([WeatherSeverity.EXTREME, WeatherSeverity.CATASTROPHIC])
        else:
            # Can go up or down one level
            options = [current_severity]
            if current_severity.value > 0:
                options.append(WeatherSeverity(current_severity.value - 1))
            if current_severity.value < 5:
                options.append(WeatherSeverity(current_severity.value + 1))
            return random.choice(options)

    def _update_humidity_and_precipitation(self, state: WeatherState,
                                         time_step_minutes: float, climate_zone: ClimateZone,
                                         altitude: float) -> WeatherState:
        """Update humidity and calculate precipitation."""

        # Evaporation/condensation balance
        evaporation_rate = self._calculate_evaporation_rate(state, climate_zone)
        condensation_rate = self._calculate_condensation_rate(state)

        # Update humidity
        dt = time_step_minutes * 60  # seconds
        humidity_change = (evaporation_rate - condensation_rate) * dt / 3600
        state.humidity = max(0.0, min(1.0, state.humidity + humidity_change))

        # Calculate precipitation
        if state.humidity > 0.8 and state.weather_type in [
            WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN, WeatherType.HEAVY_RAIN,
            WeatherType.LIGHT_SNOW, WeatherType.MODERATE_SNOW, WeatherType.HEAVY_SNOW
        ]:
            state.precipitation_intensity = self.precipitation_models.calculate_precipitation_intensity(
                state, climate_zone, altitude
            )
        else:
            state.precipitation_intensity *= 0.9  # Gradual decrease

        return state

    def _calculate_evaporation_rate(self, state: WeatherState, climate_zone: ClimateZone) -> float:
        """Calculate evaporation rate (kg/m²/s)."""

        # Simplified Penman equation
        temp_kelvin = state.temperature + 273.15

        # Saturation vapor pressure
        es = 6.112 * math.exp((17.67 * state.temperature) / (state.temperature + 243.5))

        # Actual vapor pressure
        ea = es * state.humidity

        # Wind function
        wind_function = 0.26 * (1 + state.wind_speed / 100)

        # Net radiation (simplified)
        net_radiation = state.atmospheric_conditions.solar_radiation * 0.7

        # Evaporation rate
        evaporation = (net_radiation + wind_function * (es - ea)) / (self.LATENT_HEAT_VAPORIZATION)

        return max(0, evaporation * 0.001)  # Convert to reasonable units

    def _calculate_condensation_rate(self, state: WeatherState) -> float:
        """Calculate condensation rate."""

        # Condensation occurs when air is saturated
        if state.humidity < 0.9:
            return 0.0

        # Rate proportional to supersaturation
        supersaturation = state.humidity - 0.9
        condensation_rate = supersaturation * 0.001

        return condensation_rate

    def _calculate_cloud_cover(self, state: WeatherState, climate_zone: ClimateZone,
                              season: Season) -> CloudCover:
        """Calculate cloud cover based on atmospheric conditions."""

        # Base cloud cover from humidity
        if state.humidity < 0.3:
            base_cover = CloudCover.CLEAR
        elif state.humidity < 0.5:
            base_cover = CloudCover.SCATTERED
        elif state.humidity < 0.7:
            base_cover = CloudCover.BROKEN
        elif state.humidity < 0.9:
            base_cover = CloudCover.OVERCAST
        else:
            base_cover = CloudCover.COMPLETE

        # Adjust based on pressure
        if state.pressure < 1000:  # Low pressure - more clouds
            cover_value = min(base_cover.value + 1, CloudCover.COMPLETE.value)
            base_cover = CloudCover(cover_value)
        elif state.pressure > 1020:  # High pressure - fewer clouds
            cover_value = max(base_cover.value - 1, CloudCover.CLEAR.value)
            base_cover = CloudCover(cover_value)

        # Adjust based on weather type
        if state.weather_type in [WeatherType.CLEAR, WeatherType.PARTLY_CLOUDY]:
            base_cover = CloudCover(min(base_cover.value, CloudCover.BROKEN.value))
        elif state.weather_type in [WeatherType.THUNDERSTORM, WeatherType.BLIZZARD]:
            base_cover = CloudCover.COMPLETE

        return base_cover

    def _calculate_visibility(self, state: WeatherState) -> float:
        """Calculate visibility based on conditions."""

        base_visibility = 10.0  # Base visibility in km

        # Reduction factors
        if state.weather_type == WeatherType.DENSE_FOG:
            reduction = 9.5
        elif state.weather_type == WeatherType.MODERATE_FOG:
            reduction = 6.0
        elif state.weather_type == WeatherType.LIGHT_FOG:
            reduction = 2.5
        elif state.weather_type == WeatherType.HEAVY_RAIN:
            reduction = 4.0
        elif state.weather_type == WeatherType.MODERATE_RAIN:
            reduction = 2.0
        elif state.weather_type == WeatherType.HEAVY_SNOW:
            reduction = 7.0
        elif state.weather_type == WeatherType.BLIZZARD:
            reduction = 9.8
        elif state.weather_type == WeatherType.DUST_STORM:
            reduction = 6.5
        elif state.weather_type == WeatherType.WILDFIRE_SMOKE:
            reduction = 5.0
        else:
            reduction = 0.0

        # Additional reduction from precipitation
        if state.precipitation_intensity > 0:
            reduction += state.precipitation_intensity / 10

        # Reduction from humidity
        if state.humidity > 0.8:
            reduction += 1.0

        # Magical effects
        if state.magical_intensity > 0:
            reduction += state.magical_intensity * 3.0

        visibility = max(0.1, base_visibility - reduction)
        return visibility

    def _update_precipitation_details(self, state: WeatherState) -> WeatherState:
        """Update precipitation type and details."""

        if state.precipitation_intensity > 0:
            # Determine precipitation type based on temperature
            if state.temperature < 0:
                state.precipitation_type = PrecipitationType.SNOW
                # Update snow depth
                state.snow_depth += state.precipitation_intensity * 0.1  # cm per hour
            elif state.temperature < 2:
                state.precipitation_type = PrecipitationType.SLEET
            elif state.temperature < 4:
                state.precipitation_type = PrecipitationType.FREEZING_RAIN
            else:
                state.precipitation_type = PrecipitationType.RAIN

            # Melt existing snow if temperature > 0
            if state.temperature > 0 and state.snow_depth > 0:
                melt_rate = state.temperature * 0.1  # cm per hour
                state.snow_depth = max(0, state.snow_depth - melt_rate)
        else:
            state.precipitation_type = PrecipitationType.NONE

        return state

    def _apply_weather_transition(self, state: WeatherState,
                                transition: Dict[str, Any]) -> WeatherState:
        """Apply weather type transition to state."""

        if transition['change_type'] == 'weather_type':
            state.weather_type = transition['new_weather_type']
            # Reset some properties for new weather type
            if state.weather_type == WeatherType.CLEAR:
                state.precipitation_intensity = 0
                state.precipitation_type = PrecipitationType.NONE
        elif transition['change_type'] == 'severity':
            state.severity = transition['new_severity']

        return state

    def _apply_stability_factors(self, previous_state: WeatherState,
                                new_state: WeatherState) -> WeatherState:
        """Apply stability and smoothing factors."""

        # Smooth temperature changes
        temp_diff = new_state.temperature - previous_state.temperature
        if abs(temp_diff) > 5:  # Large temperature change
            new_state.temperature = previous_state.temperature + temp_diff * self.transition_smoothness

        # Smooth humidity changes
        humidity_diff = new_state.humidity - previous_state.humidity
        if abs(humidity_diff) > 0.2:  # Large humidity change
            new_state.humidity = previous_state.humidity + humidity_diff * self.transition_smoothness

        # Smooth pressure changes
        pressure_diff = new_state.pressure - previous_state.pressure
        if abs(pressure_diff) > 10:  # Large pressure change
            new_state.pressure = previous_state.pressure + pressure_diff * self.transition_smoothness

        return new_state

    def _validate_state(self, state: WeatherState) -> WeatherState:
        """Validate and correct state values."""

        # Temperature bounds
        state.temperature = max(-60, min(60, state.temperature))

        # Humidity bounds
        state.humidity = max(0.0, min(1.0, state.humidity))

        # Pressure bounds
        state.pressure = max(800, min(1100, state.pressure))

        # Wind speed bounds
        state.wind_speed = max(0.0, min(200, state.wind_speed))

        # Visibility bounds
        state.visibility = max(0.0, min(50, state.visibility))

        # Precipitation bounds
        state.precipitation_intensity = max(0.0, min(100, state.precipitation_intensity))

        # Snow depth bounds
        state.snow_depth = max(0.0, min(1000, state.snow_depth))

        # Magical bounds
        state.magical_intensity = max(0.0, min(1.0, state.magical_intensity))

        return state

    def get_atmospheric_stability(self, state: WeatherState) -> str:
        """Calculate atmospheric stability classification."""

        # Calculate lapse rate
        if len(state.atmospheric_conditions.layers) >= 2:
            surface_layer = state.atmospheric_conditions.layers[0]
            upper_layer = state.atmospheric_conditions.layers[1]

            temp_diff = upper_layer.temperature - surface_layer.temperature
            height_diff = upper_layer.altitude - surface_layer.altitude

            if height_diff > 0:
                lapse_rate = (temp_diff / height_diff) * 1000  # °C per 1000m

                if lapse_rate > 9.8:
                    return "super_adibatic"  # Very unstable
                elif lapse_rate > 6.5:
                    return "unstable"
                elif lapse_rate > 3.0:
                    return "neutral"
                elif lapse_rate > 0:
                    return "stable"
                else:
                    return "inversion"  # Very stable

        return "neutral"