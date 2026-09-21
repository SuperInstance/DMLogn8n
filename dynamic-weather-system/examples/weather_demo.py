#!/usr/bin/env python3
"""
Dynamic Weather System Demo

This script demonstrates the complete functionality of the Dynamic Weather System
for DMlogn8n, including weather simulation, environmental impacts, and rendering.
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add the weather system to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.weather_engine import WeatherEngine
from core.weather_types import ClimateZone, Season, WeatherType, WeatherSeverity
from environmental.impact_calculator import EnvironmentalImpactCalculator
from prediction.forecast_engine import ForecastEngine
from rendering.particle_system import ParticleSystem

class WeatherDemo:
    """Demonstration of the Dynamic Weather System."""

    def __init__(self):
        print("🌦️  Initializing Dynamic Weather System for DMlogn8n...")

        # Initialize core components
        self.weather_engine = WeatherEngine(
            location="Northern Mountains",
            climate_zone=ClimateZone.MOUNTAINOUS,
            altitude=1500,  # meters
            season=Season.AUTUMN,
            config_path="config/weather_config.json"
        )

        # Initialize supporting systems
        self.impact_calculator = EnvironmentalImpactCalculator()
        self.forecast_engine = ForecastEngine()
        self.particle_system = ParticleSystem()

        print("✅ Weather System initialized successfully!")
        print(f"📍 Location: {self.weather_engine.location}")
        print(f"🏔️  Climate Zone: {self.weather_engine.climate_zone.value}")
        print(f"📏 Altitude: {self.weather_engine.altitude}m")
        print(f"🍂 Season: {self.weather_engine.season.value}")
        print()

    def display_current_weather(self):
        """Display current weather conditions."""
        weather = self.weather_engine.get_current_weather()

        print("🌤️  CURRENT WEATHER CONDITIONS")
        print("=" * 50)
        print(f"📅 Time: {weather.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"☁️  Weather: {weather.weather_type.value.replace('_', ' ').title()}")
        print(f"🌡️  Temperature: {weather.temperature:.1f}°C (feels like {weather.get_feels_like_temperature():.1f}°C)")
        print(f"💧 Humidity: {weather.humidity:.1%}")
        print(f"🌀 Wind: {weather.wind_speed:.1f} km/h {weather.wind_direction.value}")
        print(f"👁️  Visibility: {weather.visibility:.1f} km")
        print(f"📊 Pressure: {weather.pressure:.1f} mbar")

        if weather.magical_intensity > 0:
            print(f"✨ Magical Influence: {weather.magical_source.value} (intensity: {weather.magical_intensity:.2f})")

        print(f"⚡ Severity: {weather.severity.value}")
        print()

    def display_environmental_impacts(self):
        """Display environmental impacts on gameplay."""
        weather = self.weather_engine.get_current_weather()
        impacts = self.impact_calculator.calculate_impact(weather, "mountains")

        print("🎮 ENVIRONMENTAL IMPACTS")
        print("=" * 50)

        print("🚶 Movement Effects:")
        print(f"   Speed Modifier: {impacts.movement_speed_modifier:.1%}")
        print(f"   Endurance Cost: {impacts.endurance_cost_modifier:.1%}")
        print(f"   Navigation Difficulty: {impacts.navigation_difficulty_modifier:.1%}")

        print("\n⚔️ Combat Effects:")
        print(f"   Ranged Attack: {impacts.ranged_attack_modifier:+d}")
        print(f"   Melee Attack: {impacts.melee_attack_modifier:+d}")
        print(f"   Defense: {impacts.defense_modifier:+d}")
        print(f"   Initiative: {impacts.initiative_modifier:+d}")
        print(f"   Concentration DC: {10 + impacts.concentration_dc_modifier}")

        print("\n🔮 Spell Effects:")
        print(f"   Save DC Modifier: {impacts.spell_save_dc_modifier:+d}")
        print(f"   Attack Modifier: {impacts.spell_attack_modifier:+d}")
        print(f"   Damage Modifier: {impacts.spell_damage_modifier:.1%}")
        print(f"   Duration Modifier: {impacts.spell_duration_modifier:.1%}")

        print("\n👁️ Sensory Effects:")
        print(f"   Visibility Range: {impacts.visibility_range_modifier:.1%}")
        print(f"   Perception Check: {impacts.perception_modifier:+d}")
        print(f"   Stealth Check: {impacts.stealth_modifier:+d}")

        if impacts.damage_per_time:
            print(f"\n⚠️ Environmental Damage:")
            for damage_type, damage in impacts.damage_per_time.items():
                print(f"   {damage_type.title()}: {damage} per hour")

        if impacts.special_conditions:
            print(f"\n🌟 Special Conditions: {', '.join(impacts.special_conditions)}")

        print()

    def display_forecast(self, hours=12):
        """Display weather forecast."""
        print(f"🔮 WEATHER FORECAST ({hours} hours)")
        print("=" * 50)

        forecast = self.weather_engine.forecast(hours)

        for i, weather in enumerate(forecast):
            time_str = weather.timestamp.strftime('%H:%M')
            temp_range = f"{weather.temperature_min:.1f}°-{weather.temperature_max:.1f}°"
            precip = f"{weather.precipitation_probability:.0%}" if weather.precipitation_probability > 0 else "0%"

            print(f"{time_str} | {weather.weather_type.value[:15]:15} | {temp_range:12} | Rain: {precip:5}")

            if weather.hazards:
                print(f"        ⚠️ Hazards: {', '.join(weather.hazards)}")

        print()

    def display_particle_effects(self):
        """Display particle system information."""
        print("✨ PARTICLE EFFECTS")
        print("=" * 50)

        weather = self.weather_engine.get_current_weather()

        # Update particle system
        wind_data = {'x': weather.wind_speed, 'y': 0, 'z': 0}
        self.particle_system.update(weather, 0.016, wind_data)  # 60 FPS

        # Get particle statistics
        stats = self.particle_system.get_performance_stats()
        render_data = self.particle_system.get_render_data()

        print(f"Total Particles: {stats['total_particles']:,}")
        print(f"Active Emitters: {stats['active_emitters']}")
        print(f"Memory Usage: {stats['memory_usage_mb']:.2f} MB")

        if render_data['particle_groups']:
            print("\nParticle Types:")
            for particle_type, particles in render_data['particle_groups'].items():
                print(f"   {particle_type}: {len(particles)} particles")

        print()

    def simulate_weather_events(self):
        """Simulate and display weather events."""
        print("🎲 SIMULATING WEATHER EVENTS")
        print("=" * 50)

        # Advance time and look for interesting weather
        for hour in range(8):
            self.weather_engine.advance_time(60)  # 1 hour
            weather = self.weather_engine.get_current_weather()

            if weather.severity.value >= 3:  # Severe or worse
                print(f"⚠️ HOUR {hour + 1}: SEVERE WEATHER DETECTED!")
                print(f"   Type: {weather.weather_type.value}")
                print(f"   Severity: {weather.severity.value}")

                impacts = self.impact_calculator.calculate_impact(weather, "mountains")
                description = self.impact_calculator.get_description(impacts)
                print(f"   Impact: {description}")

                if weather.active_events:
                    print(f"   Active Events: {', '.join(weather.active_events)}")
                print()

                # Simulate particle effects for this weather
                wind_data = {'x': weather.wind_speed, 'y': 0, 'z': 0}
                self.particle_system.update(weather, 1.0, wind_data)
                particle_stats = self.particle_system.get_performance_stats()
                print(f"   Particle Count: {particle_stats['total_particles']:,}")
                print()

    def demonstrate_magical_weather(self):
        """Demonstrate magical weather phenomena."""
        print("🔮 MAGICAL WEATHER DEMONSTRATION")
        print("=" * 50)

        # Apply magical weather control
        print("Casting 'Arcane Storm' spell...")
        self.weather_engine.apply_weather_control(
            WeatherType.MAGICAL_STORM,
            intensity=0.8,
            duration_hours=2
        )

        weather = self.weather_engine.get_current_weather()

        print(f"✨ Weather Type: {weather.weather_type.value}")
        print(f"✨ Magical Source: {weather.magical_source.value}")
        print(f"✨ Magical Intensity: {weather.magical_intensity:.2f}")
        print(f"✨ Magical Effects: {', '.join(weather.magical_effects)}")

        # Show magical impacts
        impacts = self.impact_calculator.calculate_impact(weather, "mountains")

        print("\nMagical Combat Effects:")
        print(f"   Spell Damage Modifier: {impacts.spell_damage_modifier:.1%}")
        print(f"   Concentration DC: {10 + impacts.concentration_dc_modifier}")

        if impacts.magical_auras:
            print(f"   Magical Auras: {', '.join(impacts.magical_auras)}")

        print()

    def run_simulation_cycle(self, cycles=4):
        """Run a complete simulation cycle."""
        print(f"🔄 RUNNING {cycles}-CYCLE SIMULATION")
        print("=" * 50)

        for cycle in range(cycles):
            print(f"\n--- CYCLE {cycle + 1} ---")

            # Advance time
            self.weather_engine.advance_time(180)  # 3 hours

            # Display current conditions
            self.display_current_weather()

            # Display impacts
            self.display_environmental_impacts()

            # Brief pause for readability
            time.sleep(1)

    def generate_weather_report(self):
        """Generate a comprehensive weather report."""
        print("📊 COMPREHENSIVE WEATHER REPORT")
        print("=" * 50)

        # Get statistics
        stats = self.weather_engine.get_statistics()

        if stats:
            print("Temperature Statistics:")
            print(f"   Average: {stats['temperature']['average']:.1f}°C")
            print(f"   Range: {stats['temperature']['minimum']:.1f}°C to {stats['temperature']['maximum']:.1f}°C")

            print("\nWind Statistics:")
            print(f"   Average: {stats['wind_speed']['average']:.1f} km/h")
            print(f"   Maximum: {stats['wind_speed']['maximum']:.1f} km/h")

            print("\nWeather Distribution:")
            for weather_type, count in stats['weather_distribution'].items():
                percentage = (count / stats['period_hours']) * 100
                print(f"   {weather_type}: {percentage:.1f}%")

            print(f"\nExtreme Events: {stats['extreme_events_count']}")
            print(f"Magical Events: {stats['magical_events_count']}")

        print()

    def main(self):
        """Main demonstration function."""
        print("🎮 DYNAMIC WEATHER SYSTEM DEMO FOR DMLOGN8N")
        print("=" * 60)
        print()

        # Initial weather display
        self.display_current_weather()
        self.display_environmental_impacts()

        # Show forecast
        self.display_forecast(12)

        # Demonstrate particle effects
        self.display_particle_effects()

        # Simulate weather events
        print("Simulating 8 hours to find interesting weather...")
        self.simulate_weather_events()

        # Demonstrate magical weather
        self.demonstrate_magical_weather()

        # Run simulation cycles
        print("Running normal weather simulation...")
        self.run_simulation_cycle(3)

        # Generate final report
        self.generate_weather_report()

        print("🎉 Demo completed! The Dynamic Weather System is ready for integration.")
        print()
        print("Next steps:")
        print("1. Integrate with your game engine")
        print("2. Set up n8n workflows for automation")
        print("3. Configure regional weather patterns")
        print("4. Add magical weather phenomena to your world")
        print("5. Test with your player group!")

if __name__ == "__main__":
    demo = WeatherDemo()
    demo.main()