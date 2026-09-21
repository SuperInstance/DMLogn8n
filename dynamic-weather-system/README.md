# Dynamic Weather System for DMlogn8n

A comprehensive, immersive weather simulation system that creates dynamic atmospheric conditions for your tabletop RPG world.

## Overview

The Dynamic Weather System provides:
- Multi-layered weather patterns with realistic physics
- Seasonal variations and climate zones
- Extreme weather events and magical phenomena
- Environmental impacts on gameplay
- Atmospheric rendering with particle effects
- Weather prediction and forecasting
- Deep world integration

## Architecture

### Core Components

1. **Weather Engine** - Core simulation and state management
2. **Environmental System** - Gameplay impact calculations
3. **Rendering Engine** - Visual and atmospheric effects
4. **Prediction System** - Forecasting and divination
5. **World Integration** - Regional and biome-specific patterns
6. **n8n Workflows** - Automation and event processing

## Installation

Copy the entire dynamic-weather-system directory into your DMlogn8n project and integrate with your existing systems.

## Quick Start

```python
from core.weather_engine import WeatherEngine
from core.weather_types import WeatherType

# Initialize weather system
weather = WeatherEngine(
    region="northern_mountains",
    season="winter",
    altitude=2000
)

# Get current weather
current_weather = weather.get_current_weather()
print(f"Current: {current_weather.description}")

# Simulate next hour
weather.advance_time(1)  # 1 hour
```

## Features

### Realistic Weather Simulation
- Temperature, humidity, pressure modeling
- Seasonal and climate zone variations
- Extreme weather events
- Magical weather phenomena
- Long-term climate cycles

### Environmental Impact
- Visibility effects on exploration and combat
- Movement speed modifications
- Spell effectiveness variations
- Creature behavior changes
- Terrain interaction effects

### Atmospheric Rendering
- Dynamic sky boxes and lighting
- Particle effects (rain, snow, fog)
- Real-time shadow updates
- Wind physics simulation
- Adaptive sound environments

### Weather Prediction
- NPC predictions and folklore
- Magical divination integration
- Almanac and calendar systems
- Player pattern recognition
- Long-range forecasting

### World Integration
- Region-specific patterns
- Altitude and biome effects
- Magical area influences
- Divine intervention events
- Player weather control spells

## Configuration

See `config/weather_config.json` for detailed configuration options.

## Documentation

- [Core Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Integration Guide](docs/integration.md)
- [Configuration Guide](docs/configuration.md)

## License

© 2024 DMlogn8n Dynamic Weather System