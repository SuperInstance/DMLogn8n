# Dynamic Weather System Integration Guide

This guide provides comprehensive instructions for integrating the Dynamic Weather System into your DMlogn8n project.

## Table of Contents

1. [Installation](#installation)
2. [Basic Setup](#basic-setup)
3. [Configuration](#configuration)
4. [API Integration](#api-integration)
5. [Gameplay Integration](#gameplay-integration)
6. [Rendering Integration](#rendering-integration)
7. [n8n Workflow Setup](#n8n-workflow-setup)
8. [Testing and Validation](#testing-and-validation)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- n8n workflow automation platform
- Compatible game engine (Unity, Godot, etc.) for rendering
- Database for weather data persistence

### File Structure

Copy the Dynamic Weather System files to your project:

```
your-project/
├── weather-system/
│   ├── core/
│   ├── algorithms/
│   ├── environmental/
│   ├── rendering/
│   ├── prediction/
│   ├── world-integration/
│   ├── n8n-workflows/
│   ├── config/
│   └── docs/
└── your-game-files/
```

### Dependencies

Install required Python packages:

```bash
pip install numpy scipy matplotlib dataclasses typing-extensions
```

For n8n integration, ensure you have the n8n nodes:
- HTTP Request node
- Code node
- Schedule Trigger node
- If node for conditional logic

## Basic Setup

### 1. Initialize the Weather Engine

```python
from weather_system.core.weather_engine import WeatherEngine
from weather_system.core.weather_types import ClimateZone, Season

# Initialize weather engine
weather_engine = WeatherEngine(
    location="your_region",
    climate_zone=ClimateZone.TEMPERATE,
    altitude=500,  # meters
    season=Season.SUMMER,
    config_path="weather-system/config/weather_config.json"
)
```

### 2. Start Weather Simulation

```python
# Set up real-time updates
import time

def update_weather():
    while True:
        weather_engine.advance_time(15)  # 15-minute intervals
        current_weather = weather_engine.get_current_weather()
        print(current_weather.get_description())
        time.sleep(900)  # Wait 15 minutes (or faster for testing)

# Start simulation in background thread
import threading
weather_thread = threading.Thread(target=update_weather, daemon=True)
weather_thread.start()
```

### 3. Get Weather Data

```python
# Current weather
current = weather_engine.get_current_weather()
print(f"Temperature: {current.temperature}°C")
print(f"Weather: {current.weather_type.value}")
print(f"Wind: {current.wind_speed} km/h {current.wind_direction.value}")

# Weather forecast
forecast = weather_engine.forecast(hours=24)
for hour_forecast in forecast:
    print(f"{hour_forecast.timestamp}: {hour_forecast.weather_type.value}")
```

## Configuration

### Core Configuration

Edit `config/weather_config.json` to customize the system:

```json
{
  "simulation": {
    "time_step_minutes": 15,
    "stability_factor": 0.7,
    "transition_smoothness": 0.8
  },
  "events": {
    "enabled": true,
    "extreme_weather_probability": 0.1,
    "magical_phenomena_probability": 0.05
  },
  "rendering": {
    "sky_boxes": true,
    "particle_effects": true,
    "dynamic_lighting": true
  }
}
```

### Regional Configuration

Define specific locations:

```python
# Set up different regions
weather_engine.set_location(
    location="northern_mountains",
    climate_zone=ClimateZone.MOUNTAINOUS,
    altitude=2000
)

# Change seasons dynamically
weather_engine.set_season(Season.WINTER)
```

## API Integration

### REST API Endpoints

Set up HTTP endpoints for external access:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/weather/current')
def get_current_weather():
    weather = weather_engine.get_current_weather()
    return jsonify(weather.to_dict())

@app.route('/api/weather/forecast/<int:hours>')
def get_forecast(hours):
    forecast = weather_engine.forecast(hours)
    return jsonify([f.to_dict() for f in forecast])

@app.route('/api/weather/impact')
def get_environmental_impact():
    from weather_system.environmental.impact_calculator import EnvironmentalImpactCalculator
    calculator = EnvironmentalImpactCalculator()
    impact = calculator.calculate_impact(weather_engine.get_current_weather())
    return jsonify(impact.__dict__)
```

### WebSocket Integration

For real-time updates:

```python
import socketio

sio = socketio.Server()

@sio.event
def connect(sid, environ):
    # Send current weather on connection
    weather = weather_engine.get_current_weather()
    sio.emit('weather_update', weather.to_dict(), room=sid)

# Emit weather updates
def broadcast_weather_update():
    weather = weather_engine.get_current_weather()
    sio.emit('weather_update', weather.to_dict())
```

## Gameplay Integration

### Movement Effects

```python
from weather_system.environmental.movement_effects import MovementEffects

movement_effects = MovementEffects()

def calculate_travel_time(distance_km, terrain_type="plains"):
    weather = weather_engine.get_current_weather()
    impact = movement_effects.calculate_movement_impact(weather, terrain_type)

    base_time = distance_km / 5  # 5 km/h base speed
    modified_time = base_time / impact['speed_modifier']

    return {
        'base_time_hours': base_time,
        'modified_time_hours': modified_time,
        'endurance_modifier': impact['endurance_modifier'],
        'navigation_difficulty': impact['navigation_modifier']
    }
```

### Combat Modifiers

```python
from weather_system.environmental.combat_modifiers import CombatModifiers

combat_mods = CombatModifiers()

def get_combat_modifiers():
    weather = weather_engine.get_current_weather()
    modifiers = combat_mods.calculate_combat_impact(weather)

    return {
        'ranged_attack_penalty': modifiers['ranged_modifier'],
        'melee_attack_penalty': modifiers['melee_modifier'],
        'concentration_dc': 10 + modifiers['concentration_dc'],
        'initiative_modifier': modifiers['initiative_modifier']
    }
```

### Spell Effects

```python
from weather_system.environmental.spell_effects import SpellEffects

spell_effects = SpellEffects()

def calculate_spell_effects(spell_school, spell_level):
    weather = weather_engine.get_current_weather()
    effects = spell_effects.calculate_spell_impact(weather, spell_level)

    return {
        'damage_modifier': effects['damage_modifier'],
        'save_dc_modifier': effects['save_dc_modifier'],
        'duration_modifier': effects['duration_modifier'],
        'components_difficulty': effects['components_difficulty']
    }
```

## Rendering Integration

### Particle System

```python
from weather_system.rendering.particle_system import ParticleSystem

particle_system = ParticleSystem()

def update_particles(delta_time, wind_data):
    weather = weather_engine.get_current_weather()
    particle_system.update(weather, delta_time, wind_data)

    # Get render data
    render_data = particle_system.get_render_data()
    return render_data

# Example integration with game engine
def game_loop():
    while True:
        delta_time = get_delta_time()
        wind_data = get_wind_data()  # From your physics system

        particle_data = update_particles(delta_time, wind_data)
        render_particles(particle_data)  # Your rendering function
```

### Sky and Lighting

```python
from weather_system.rendering.sky_renderer import SkyRenderer
from weather_system.rendering.lighting_engine import LightingEngine

sky_renderer = SkyRenderer()
lighting_engine = LightingEngine()

def update_rendering():
    weather = weather_engine.get_current_weather()

    # Update sky
    sky_data = sky_renderer.render_sky(weather)
    set_skybox(sky_data.texture, sky_data.color)

    # Update lighting
    lighting_data = lighting_engine.calculate_lighting(weather)
    set_ambient_light(lighting_data.ambient)
    set_sun_light(lighting_data.sun_direction, lighting_data.sun_color)
    update_fog(lighting_data.fog_density, lighting_data.fog_color)
```

## n8n Workflow Setup

### Import the Workflow

1. Open n8n interface
2. Click "Import from file"
3. Select `n8n-workflows/weather-simulation-workflow.json`
4. Configure webhook URLs to match your API endpoints

### Configure Webhooks

Update the webhook IDs in the workflow to match your system:

```json
{
  "webhookId": "your-weather-system-current",
  "webhookId": "your-weather-system-simulate",
  "webhookId": "your-weather-system-events"
}
```

### Test the Workflow

1. Manually trigger the workflow
2. Check each node's output
3. Verify API endpoints are responding correctly
4. Monitor error handling

## Testing and Validation

### Unit Tests

```python
import unittest
from weather_system.core.weather_engine import WeatherEngine

class TestWeatherSystem(unittest.TestCase):
    def setUp(self):
        self.weather_engine = WeatherEngine()

    def test_weather_advance(self):
        initial_temp = self.weather_engine.get_current_weather().temperature
        self.weather_engine.advance_time(60)  # 1 hour
        new_temp = self.weather_engine.get_current_weather().temperature
        self.assertNotEqual(initial_temp, new_temp)

    def test_forecast_generation(self):
        forecast = self.weather_engine.forecast(24)
        self.assertEqual(len(forecast), 24)  # 24 hourly forecasts

    def test_environmental_impact(self):
        from weather_system.environmental.impact_calculator import EnvironmentalImpactCalculator
        calculator = EnvironmentalImpactCalculator()
        impact = calculator.calculate_impact(self.weather_engine.get_current_weather())
        self.assertIsInstance(impact.movement_speed_modifier, float)

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
def test_full_integration():
    # Test complete workflow
    weather_engine = WeatherEngine()

    # Simulate weather changes
    for hour in range(24):
        weather_engine.advance_time(60)
        current = weather_engine.get_current_weather()

        # Test environmental impacts
        from weather_system.environmental.impact_calculator import EnvironmentalImpactCalculator
        calculator = EnvironmentalImpactCalculator()
        impact = calculator.calculate_impact(current)

        # Validate reasonable values
        assert 0.05 <= impact.movement_speed_modifier <= 2.0
        assert -10 <= impact.ranged_attack_modifier <= 5

        # Test rendering data
        from weather_system.rendering.particle_system import ParticleSystem
        particles = ParticleSystem()
        particles.update(current, 0.016)  # 60 FPS
        render_data = particles.get_render_data()
        assert isinstance(render_data['particle_count'], int)
```

## Performance Optimization

### Caching

```python
from functools import lru_cache

class CachedWeatherEngine(WeatherEngine):
    @lru_cache(maxsize=1000)
    def get_cached_impact(self, weather_hash):
        # Cache environmental impacts
        return super().calculate_environmental_impact()
```

### Level of Detail (LOD)

```python
def update_with_lod(player_position, weather):
    distance = calculate_distance(player_position, weather.location)

    if distance > 1000:
        # Low detail - update less frequently
        return update_simple_weather(weather)
    elif distance > 500:
        # Medium detail
        return update_medium_weather(weather)
    else:
        # High detail - full simulation
        return update_full_weather(weather)
```

### Database Optimization

```sql
-- Index weather data for fast queries
CREATE INDEX idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX idx_weather_location ON weather_data(location);
CREATE INDEX idx_weather_type ON weather_data(weather_type);

-- Archive old data
CREATE TABLE weather_data_archive AS
SELECT * FROM weather_data
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

## Troubleshooting

### Common Issues

1. **Weather Not Updating**
   - Check if simulation thread is running
   - Verify time advancement is being called
   - Check configuration file syntax

2. **Performance Issues**
   - Reduce particle count in config
   - Increase update intervals
   - Enable LOD system

3. **Inaccurate Forecasts**
   - Check historical data availability
   - Verify climate zone settings
   - Adjust accuracy decay rate

4. **Rendering Problems**
   - Verify particle system initialization
   - Check shader compatibility
   - Validate texture paths

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('weather_system')

# Log weather changes
def log_weather_change(previous, current):
    logger.debug(f"Weather changed from {previous.weather_type} to {current.weather_type}")
    logger.debug(f"Temperature: {previous.temperature}°C -> {current.temperature}°C")
```

### Health Monitoring

```python
def check_system_health():
    try:
        weather = weather_engine.get_current_weather()
        forecast = weather_engine.forecast(1)

        return {
            'status': 'healthy',
            'last_update': weather.timestamp,
            'forecast_available': len(forecast) > 0,
            'particle_count': particle_system.get_particle_count()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
```

## Support and Contributing

For issues, questions, or contributions:

1. Check existing documentation
2. Review test cases
3. Create detailed bug reports
4. Include system specifications
5. Provide error logs and configuration

## Next Steps

After successful integration:

1. Customize weather patterns for your world
2. Add region-specific events
3. Implement player weather control spells
4. Create magical weather phenomena
5. Develop weather-based storylines
6. Add seasonal campaign events

This Dynamic Weather System provides a foundation for immersive, realistic weather that enhances your tabletop RPG experience.