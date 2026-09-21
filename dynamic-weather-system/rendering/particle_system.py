"""
Particle System for Weather Effects

Manages particle effects for rain, snow, fog, dust, and other atmospheric
phenomena with realistic physics and rendering.
"""

import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.weather_state import WeatherState
from ..core.weather_types import WeatherType, WeatherSeverity

class ParticleType(Enum):
    """Types of particles for weather effects."""

    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    DUST = "dust"
    SAND = "sand"
    ASH = "ash"
    FOG = "fog"
    MIST = "mist"
    SMOKE = "smoke"
    LEAVES = "leaves"
    PETALS = "petals"
    EMBERS = "embers"
    SPARKS = "sparks"
    MAGIC_ORB = "magic_orb"
    MAGIC_DUST = "magic_dust"

@dataclass
class Particle:
    """Individual particle in the system."""

    # Position and movement
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0  # Velocity x
    vy: float = 0.0  # Velocity y
    vz: float = 0.0  # Velocity z

    # Physical properties
    size: float = 1.0
    mass: float = 1.0
    opacity: float = 1.0
    color: Tuple[int, int, int] = (255, 255, 255)

    # Lifecycle
    lifetime: float = 1.0
    age: float = 0.0
    active: bool = True

    # Particle-specific data
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParticleEmitter:
    """Particle emitter configuration."""

    particle_type: ParticleType
    emission_rate: float  # Particles per second
    emission_area: Tuple[float, float, float]  # Width, height, depth
    emission_direction: Tuple[float, float, float]  # Direction vector
    spread_angle: float = 30.0  # Spread angle in degrees
    initial_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity_variation: float = 0.5

    # Particle properties
    size_range: Tuple[float, float] = (1.0, 3.0)
    opacity_range: Tuple[float, float] = (0.5, 1.0)
    lifetime_range: Tuple[float, float] = (1.0, 5.0)
    colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [(255, 255, 255)])

    # Physics properties
    affected_by_wind: bool = True
    affected_by_gravity: bool = True
    bounce_factor: float = 0.0
    drag_coefficient: float = 0.1

    # Emission control
    enabled: bool = True
    max_particles: int = 1000
    burst_mode: bool = False
    burst_count: int = 10

class ParticleSystem:
    """Advanced particle system for weather effects."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Particle storage
        self.particles: List[Particle] = []
        self.emitters: Dict[str, ParticleEmitter] = {}
        self.max_total_particles = self.config.get('max_particles', 10000)

        # Physics parameters
        self.gravity = self.config.get('gravity', 9.81)
        self.wind_force = self.config.get('wind_force', 1.0)
        self.air_density = self.config.get('air_density', 1.225)

        # Performance optimization
        self.update_distance = self.config.get('update_distance', 500.0)  # meters
        self.lod_levels = self.config.get('lod_levels', 3)  # Levels of detail

        # Initialize weather-specific emitters
        self._initialize_weather_emitters()

    def _initialize_weather_emitters(self):
        """Initialize default emitters for different weather types."""

        # Rain emitter
        self.emitters['rain'] = ParticleEmitter(
            particle_type=ParticleType.RAIN,
            emission_rate=100,
            emission_area=(100, 1, 100),  # Wide area, thin height
            emission_direction=(0, -1, 0),  # Falling down
            spread_angle=10.0,
            initial_velocity=(0, -5, 0),
            velocity_variation=0.3,
            size_range=(0.1, 0.3),
            opacity_range=(0.3, 0.7),
            lifetime_range=(2.0, 4.0),
            colors=[(200, 200, 255, 128)],  # Semi-transparent blue-white
            affected_by_wind=True,
            affected_by_gravity=True,
            drag_coefficient=0.2
        )

        # Snow emitter
        self.emitters['snow'] = ParticleEmitter(
            particle_type=ParticleType.SNOW,
            emission_rate=50,
            emission_area=(100, 5, 100),
            emission_direction=(0, -1, 0),
            spread_angle=25.0,
            initial_velocity=(0, -1, 0),
            velocity_variation=0.5,
            size_range=(0.5, 3.0),
            opacity_range=(0.7, 1.0),
            lifetime_range=(5.0, 10.0),
            colors=[(255, 255, 255)],
            affected_by_wind=True,
            affected_by_gravity=True,
            drag_coefficient=0.5
        )

        # Fog emitter
        self.emitters['fog'] = ParticleEmitter(
            particle_type=ParticleType.FOG,
            emission_rate=20,
            emission_area=(50, 2, 50),
            emission_direction=(0.1, 0, 0.1),  # Slow drift
            spread_angle=90.0,
            initial_velocity=(0.2, 0, 0.2),
            velocity_variation=0.8,
            size_range=(5.0, 15.0),
            opacity_range=(0.1, 0.3),
            lifetime_range=(10.0, 20.0),
            colors=[(200, 200, 200, 64)],  # Very transparent gray
            affected_by_wind=True,
            affected_by_gravity=False,
            drag_coefficient=0.8
        )

        # Dust emitter
        self.emitters['dust'] = ParticleEmitter(
            particle_type=ParticleType.DUST,
            emission_rate=30,
            emission_area=(80, 3, 80),
            emission_direction=(0.2, -0.1, 0.2),
            spread_angle=60.0,
            initial_velocity=(1.0, -0.2, 1.0),
            velocity_variation=0.7,
            size_range=(0.2, 1.0),
            opacity_range=(0.2, 0.6),
            lifetime_range=(3.0, 8.0),
            colors=[(194, 178, 128)],  # Dusty brown
            affected_by_wind=True,
            affected_by_gravity=False,
            drag_coefficient=0.3
        )

        # Lightning sparks emitter
        self.emitters['lightning_sparks'] = ParticleEmitter(
            particle_type=ParticleType.SPARKS,
            emission_rate=200,
            emission_area=(5, 20, 5),
            emission_direction=(0.3, -0.8, 0.3),
            spread_angle=120.0,
            initial_velocity=(10.0, -20.0, 10.0),
            velocity_variation=0.8,
            size_range=(0.05, 0.2),
            opacity_range=(0.8, 1.0),
            lifetime_range=(0.1, 0.5),
            colors=[(255, 255, 200), (200, 200, 255)],
            affected_by_wind=False,
            affected_by_gravity=False,
            drag_coefficient=0.05,
            burst_mode=True,
            burst_count=50
        )

        # Magic dust emitter
        self.emitters['magic_dust'] = ParticleEmitter(
            particle_type=ParticleType.MAGIC_DUST,
            emission_rate=40,
            emission_area=(60, 10, 60),
            emission_direction=(0.1, -0.1, 0.1),
            spread_angle=45.0,
            initial_velocity=(0.5, -0.2, 0.5),
            velocity_variation=0.6,
            size_range=(0.3, 1.5),
            opacity_range=(0.4, 0.9),
            lifetime_range=(4.0, 12.0),
            colors=[(200, 100, 255), (100, 200, 255), (255, 200, 100)],  # Magical colors
            affected_by_wind=True,
            affected_by_gravity=False,
            drag_coefficient=0.6
        )

    def update(self, weather_state: WeatherState, delta_time: float, wind_data: Dict[str, Any] = None):
        """Update particle system based on weather conditions."""

        # Update active emitters based on weather
        self._update_emitters(weather_state)

        # Emit new particles
        self._emit_particles(delta_time)

        # Update existing particles
        self._update_particles(weather_state, delta_time, wind_data)

        # Remove dead particles
        self._cleanup_particles()

        # Limit total particle count
        self._limit_particle_count()

    def _update_emitters(self, weather_state: WeatherState):
        """Update emitter settings based on weather conditions."""

        # Disable all emitters first
        for emitter in self.emitters.values():
            emitter.enabled = False

        # Enable and configure emitters based on weather type
        if weather_state.weather_type in [WeatherType.LIGHT_RAIN, WeatherType.MODERATE_RAIN, WeatherType.HEAVY_RAIN]:
            emitter = self.emitters['rain']
            emitter.enabled = True

            # Adjust emission rate based on intensity
            if weather_state.weather_type == WeatherType.LIGHT_RAIN:
                emitter.emission_rate = 50
            elif weather_state.weather_type == WeatherType.MODERATE_RAIN:
                emitter.emission_rate = 150
            else:  # HEAVY_RAIN
                emitter.emission_rate = 300

            # Adjust initial velocity based on severity
            velocity_factor = 1.0 + (weather_state.severity.value / 5.0)
            emitter.initial_velocity = (0, -5 * velocity_factor, 0)

        elif weather_state.weather_type in [WeatherType.LIGHT_SNOW, WeatherType.MODERATE_SNOW, WeatherType.HEAVY_SNOW]:
            emitter = self.emitters['snow']
            emitter.enabled = True

            # Adjust emission rate
            if weather_state.weather_type == WeatherType.LIGHT_SNOW:
                emitter.emission_rate = 30
            elif weather_state.weather_type == WeatherType.MODERATE_SNOW:
                emitter.emission_rate = 80
            else:  # HEAVY_SNOW
                emitter.emission_rate = 150

            # Snow falls slower
            emitter.initial_velocity = (0, -0.5, 0)

        elif weather_state.weather_type in [WeatherType.LIGHT_FOG, WeatherType.MODERATE_FOG, WeatherType.DENSE_FOG]:
            emitter = self.emitters['fog']
            emitter.enabled = True

            # Fog density
            if weather_state.weather_type == WeatherType.LIGHT_FOG:
                emitter.emission_rate = 10
                emitter.opacity_range = (0.05, 0.15)
            elif weather_state.weather_type == WeatherType.MODERATE_FOG:
                emitter.emission_rate = 20
                emitter.opacity_range = (0.1, 0.25)
            else:  # DENSE_FOG
                emitter.emission_rate = 40
                emitter.opacity_range = (0.2, 0.4)

        elif weather_state.weather_type in [WeatherType.DUST_STORM, WeatherType.SANDSTORM]:
            emitter = self.emitters['dust']
            emitter.enabled = True

            # Dust storm intensity
            emitter.emission_rate = 100 if weather_state.weather_type == WeatherType.DUST_STORM else 150

            # Adjust colors for sand
            if weather_state.weather_type == WeatherType.SANDSTORM:
                emitter.colors = [(238, 203, 173)]  # Sandy color

        elif weather_state.weather_type == WeatherType.THUNDERSTORM:
            # Enable rain and lightning
            self.emitters['rain'].enabled = True
            self.emitters['rain'].emission_rate = 200

            # Lightning sparks (burst mode)
            if random.random() < 0.02:  # 2% chance per frame
                emitter = self.emitters['lightning_sparks']
                emitter.enabled = True
                emitter.burst_mode = True

        # Magical weather effects
        if weather_state.magical_intensity > 0.3:
            emitter = self.emitters['magic_dust']
            emitter.enabled = True
            emitter.emission_rate = int(30 * weather_state.magical_intensity)

            # Adjust colors based on magical source
            if weather_state.magical_source:
                if 'shadow' in weather_state.magical_source.value:
                    emitter.colors = [(128, 0, 128), (64, 0, 64)]  # Purple/black
                elif 'fire' in weather_state.magical_source.value:
                    emitter.colors = [(255, 100, 0), (255, 200, 0)]  # Orange/yellow
                elif 'divine' in weather_state.magical_source.value:
                    emitter.colors = [(255, 255, 200), (200, 200, 255)]  # Gold/blue

    def _emit_particles(self, delta_time: float):
        """Emit new particles from active emitters."""

        for emitter_name, emitter in self.emitters.items():
            if not emitter.enabled or len(self.particles) >= self.max_total_particles:
                continue

            # Calculate number of particles to emit
            if emitter.burst_mode:
                particles_to_emit = emitter.burst_count
                emitter.burst_mode = False  # Reset burst mode
            else:
                particles_to_emit = int(emitter.emission_rate * delta_time)

            # Limit by max particles
            particles_to_emit = min(particles_to_emit,
                                   emitter.max_particles - self.count_particles_by_type(emitter.particle_type),
                                   self.max_total_particles - len(self.particles))

            # Emit particles
            for _ in range(particles_to_emit):
                particle = self._create_particle(emitter)
                self.particles.append(particle)

    def _create_particle(self, emitter: ParticleEmitter) -> Particle:
        """Create a new particle from emitter."""

        # Random position within emission area
        x = random.uniform(-emitter.emission_area[0] / 2, emitter.emission_area[0] / 2)
        y = random.uniform(-emitter.emission_area[1] / 2, emitter.emission_area[1] / 2)
        z = random.uniform(-emitter.emission_area[2] / 2, emitter.emission_area[2] / 2)

        # Random velocity with spread
        base_vx, base_vy, base_vz = emitter.initial_velocity
        spread_rad = math.radians(emitter.spread_angle)

        vx = base_vx + random.uniform(-emitter.velocity_variation, emitter.velocity_variation)
        vy = base_vy + random.uniform(-emitter.velocity_variation, emitter.velocity_variation)
        vz = base_vz + random.uniform(-emitter.velocity_variation, emitter.velocity_variation)

        # Apply spread
        if spread_rad > 0:
            angle_h = random.uniform(0, 2 * math.pi)
            angle_v = random.uniform(-spread_rad / 2, spread_rad / 2)

            vx += math.cos(angle_h) * math.sin(angle_v) * abs(base_vy)
            vz += math.sin(angle_h) * math.sin(angle_v) * abs(base_vy)
            vy += math.cos(angle_v) * abs(base_vy) - abs(base_vy)

        # Random properties
        size = random.uniform(*emitter.size_range)
        opacity = random.uniform(*emitter.opacity_range)
        lifetime = random.uniform(*emitter.lifetime_range)
        color = random.choice(emitter.colors)

        # Calculate mass based on size and particle type
        mass = self._calculate_particle_mass(emitter.particle_type, size)

        return Particle(
            x=x, y=y, z=z,
            vx=vx, vy=vy, vz=vz,
            size=size,
            mass=mass,
            opacity=opacity,
            color=color[:3] if len(color) == 3 else color[:3],
            lifetime=lifetime,
            data={'type': emitter.particle_type.value}
        )

    def _calculate_particle_mass(self, particle_type: ParticleType, size: float) -> float:
        """Calculate particle mass based on type and size."""

        # Density values (kg/m³)
        densities = {
            ParticleType.RAIN: 1000.0,    # Water
            ParticleType.SNOW: 100.0,     # Snow (less dense)
            ParticleType.SLEET: 900.0,    # Ice
            ParticleType.HAIL: 800.0,     # Ice (with air pockets)
            ParticleType.DUST: 2650.0,    # Sand/rock
            ParticleType.SAND: 2650.0,
            ParticleType.ASH: 700.0,      # Volcanic ash
            ParticleType.FOG: 1.2,        # Water vapor
            ParticleType.MAGIC_ORB: 10.0, # Magical (variable)
        }

        density = densities.get(particle_type, 1.0)
        volume = (4/3) * math.pi * (size/1000) ** 3  # Convert mm to m
        return density * volume

    def _update_particles(self, weather_state: WeatherState, delta_time: float, wind_data: Dict[str, Any] = None):
        """Update particle positions and properties."""

        wind_velocity = wind_data or {'x': 0, 'y': 0, 'z': 0}

        for particle in self.particles:
            if not particle.active:
                continue

            # Apply forces
            ax, ay, az = 0, 0, 0

            # Gravity
            particle_type = ParticleType(particle.data.get('type', 'rain'))
            emitter = self.emitters.get(particle_type.value)
            if emitter and emitter.affected_by_gravity:
                ay -= self.gravity

            # Wind force
            if emitter and emitter.affected_by_wind:
                wind_effect = self._calculate_wind_force(particle, wind_velocity, weather_state)
                ax += wind_effect[0]
                ay += wind_effect[1]
                az += wind_effect[2]

            # Drag
            if emitter:
                drag_force = self._calculate_drag_force(particle, emitter)
                ax -= drag_force[0]
                ay -= drag_force[1]
                az -= drag_force[2]

            # Update velocity
            particle.vx += ax * delta_time
            particle.vy += ay * delta_time
            particle.vz += az * delta_time

            # Update position
            particle.x += particle.vx * delta_time
            particle.y += particle.vy * delta_time
            particle.z += particle.vz * delta_time

            # Update age and opacity
            particle.age += delta_time
            if particle.lifetime > 0:
                life_ratio = particle.age / particle.lifetime
                particle.opacity *= max(0, 1 - life_ratio)

            # Deactivate old particles
            if particle.age >= particle.lifetime or particle.opacity <= 0.01:
                particle.active = False

            # Deactivate particles that are too far away
            distance = math.sqrt(particle.x**2 + particle.y**2 + particle.z**2)
            if distance > self.update_distance:
                particle.active = False

    def _calculate_wind_force(self, particle: Particle, wind_velocity: Dict[str, float],
                            weather_state: WeatherState) -> Tuple[float, float, float]:
        """Calculate wind force on particle."""

        # Wind force proportional to relative velocity and particle cross-section
        relative_vx = wind_velocity['x'] - particle.vx
        relative_vy = wind_velocity['y'] - particle.vy
        relative_vz = wind_velocity['z'] - particle.vz

        # Simplified drag equation for wind
        cross_section = math.pi * (particle.size / 1000) ** 2
        wind_force_factor = 0.5 * self.air_density * cross_section * self.wind_force

        fx = relative_vx * wind_force_factor
        fy = relative_vy * wind_force_factor
        fz = relative_vz * wind_force_factor

        return (fx, fy, fz)

    def _calculate_drag_force(self, particle: Particle, emitter: ParticleEmitter) -> Tuple[float, float, float]:
        """Calculate drag force on particle."""

        # Drag equation: F = 0.5 * ρ * v² * Cd * A
        velocity_magnitude = math.sqrt(particle.vx**2 + particle.vy**2 + particle.vz**2)

        if velocity_magnitude < 0.01:
            return (0, 0, 0)

        cross_section = math.pi * (particle.size / 1000) ** 2
        drag_magnitude = 0.5 * self.air_density * velocity_magnitude**2 * emitter.drag_coefficient * cross_section

        # Apply drag in opposite direction of velocity
        fx = -drag_magnitude * (particle.vx / velocity_magnitude) / particle.mass
        fy = -drag_magnitude * (particle.vy / velocity_magnitude) / particle.mass
        fz = -drag_magnitude * (particle.vz / velocity_magnitude) / particle.mass

        return (fx, fy, fz)

    def _cleanup_particles(self):
        """Remove inactive particles."""

        self.particles = [p for p in self.particles if p.active]

    def _limit_particle_count(self):
        """Limit total particle count to maintain performance."""

        if len(self.particles) > self.max_total_particles:
            # Remove oldest particles
            self.particles.sort(key=lambda p: p.age, reverse=True)
            self.particles = self.particles[:self.max_total_particles]

    def count_particles_by_type(self, particle_type: ParticleType) -> int:
        """Count active particles of specific type."""

        return sum(1 for p in self.particles
                  if p.active and p.data.get('type') == particle_type.value)

    def get_particle_count(self) -> int:
        """Get total active particle count."""

        return len([p for p in self.particles if p.active])

    def get_render_data(self) -> Dict[str, Any]:
        """Get particle data for rendering."""

        active_particles = [p for p in self.particles if p.active]

        # Group particles by type for efficient rendering
        particle_groups = {}
        for particle in active_particles:
            particle_type = particle.data.get('type', 'unknown')
            if particle_type not in particle_groups:
                particle_groups[particle_type] = []
            particle_groups[particle_type].append({
                'position': (particle.x, particle.y, particle.z),
                'velocity': (particle.vx, particle.vy, particle.vz),
                'size': particle.size,
                'opacity': particle.opacity,
                'color': particle.color,
                'age': particle.age,
                'lifetime': particle.lifetime
            })

        return {
            'particle_count': len(active_particles),
            'particle_groups': particle_groups,
            'active_emitters': [name for name, emitter in self.emitters.items() if emitter.enabled]
        }

    def clear_all_particles(self):
        """Clear all particles."""

        self.particles.clear()

    def set_emitter_property(self, emitter_name: str, property_name: str, value: Any):
        """Set emitter property."""

        if emitter_name in self.emitters:
            setattr(self.emitters[emitter_name], property_name, value)

    def trigger_burst(self, emitter_name: str, count: int = None):
        """Trigger burst emission for specific emitter."""

        if emitter_name in self.emitters:
            emitter = self.emitters[emitter_name]
            emitter.burst_mode = True
            if count is not None:
                emitter.burst_count = count

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""

        active_particles = len([p for p in self.particles if p.active])
        active_emitters = len([e for e in self.emitters.values() if e.enabled])

        particle_type_counts = {}
        for particle in self.particles:
            if particle.active:
                particle_type = particle.data.get('type', 'unknown')
                particle_type_counts[particle_type] = particle_type_counts.get(particle_type, 0) + 1

        return {
            'total_particles': active_particles,
            'max_particles': self.max_total_particles,
            'active_emitters': active_emitters,
            'particle_type_distribution': particle_type_counts,
            'memory_usage_mb': active_particles * 64 / 1024 / 1024  # Rough estimate
        }