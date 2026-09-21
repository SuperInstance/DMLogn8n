#!/usr/bin/env python3
"""
Star System Simulator - Dynamic Star System Evolution
Simulates stellar evolution, planetary dynamics, and cosmic events
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import random
import math

# Physical Constants
G = 6.67430e-11  # Gravitational constant
c = 299792458  # Speed of light (m/s)
STEFAN_BOLTZMANN = 5.67e-8  # Stefan-Boltzmann constant
SOLAR_MASS = 1.989e30  # kg
SOLAR_RADIUS = 6.96e8  # meters
SOLAR_LUMINOSITY = 3.828e26  # Watts
EARTH_MASS = 5.972e24  # kg
AU = 1.496e11  # meters
YEAR = 365.25 * 24 * 3600  # seconds

class StellarPhase(Enum):
    MAIN_SEQUENCE = "main_sequence"
    SUBGIANT = "subgiant"
    RED_GIANT = "red_giant"
    HORIZONTAL_BRANCH = "horizontal_branch"
    ASYMPTOTIC_GIANT = "asymptotic_giant"
    PLANETARY_NEBULA = "planetary_nebula"
    WHITE_DWARF = "white_dwarf"
    NEUTRON_STAR = "neutron_star"
    BLACK_HOLE = "black_hole"
    SUPERNOVA = "supernova"

class CosmicEventType(Enum):
    SOLAR_FLARE = "solar_flare"
    CORONAL_MASS_EJECTION = "coronal_mass_ejection"
    SUPERNOVA = "supernova"
    GAMMA_RAY_BURST = "gamma_ray_burst"
    ASTEROID_IMPACT = "asteroid_impact"
    COMET_IMPACT = "comet_impact"
    MAGNETIC_REVERSAL = "magnetic_reversal"
    STELLAR_WIND = "stellar_wind"
    PLANETARY_COLLISION = "planetary_collision"
    MOON_CAPTURE = "moon_capture"

@dataclass
class CosmicEvent:
    """Represents a cosmic event in the star system"""
    event_type: CosmicEventType
    time: float  # seconds since simulation start
    duration: float  # seconds
    location: np.ndarray  # 3D position
    intensity: float  # 0-1 scale
    affected_objects: List[str]  # Object IDs affected
    description: str

@dataclass
class StellarEvolutionTrack:
    """Tracks a star's evolution over time"""
    current_phase: StellarPhase
    age: float  # seconds
    initial_mass: float  # kg
    current_mass: float  # kg
    current_radius: float  # meters
    current_temperature: float  # Kelvin
    current_luminosity: float  # Watts
    lifetime_remaining: float  # seconds
    metallicity: float
    rotation_period: float  # seconds
    magnetic_field_strength: float  # Tesla

@dataclass
class PlanetaryEvolution:
    """Tracks a planet's evolution over time"""
    age: float  # seconds
    mass: float  # kg
    radius: float  # meters
    atmospheric_pressure: float  # Pascals
    surface_temperature: float  # Kelvin
    water_coverage: float  # 0-1 fraction
    biosphere_complexity: float  # 0-1 scale
    tectonic_activity: float  # 0-1 scale
    magnetic_field_strength: float  # Tesla
    orbital_drift_rate: float  # meters per second
    atmosphere_composition: Dict[str, float]

class StarSystemSimulator:
    """Simulates dynamic evolution of star systems"""

    def __init__(self, time_step: float = 1000 * YEAR):  # 1000 years per step
        self.time = 0.0
        self.time_step = time_step
        self.stars: Dict[str, StellarEvolutionTrack] = {}
        self.planets: Dict[str, PlanetaryEvolution] = {}
        self.cosmic_events: List[CosmicEvent] = []
        self.event_history: List[CosmicEvent] = []
        self.active_events: List[CosmicEvent] = []

        # Stellar evolution parameters
        self.main_sequence_lifetimes = {
            'O': 1e6 * YEAR,
            'B': 10e6 * YEAR,
            'A': 1e9 * YEAR,
            'F': 3e9 * YEAR,
            'G': 10e9 * YEAR,
            'K': 20e9 * YEAR,
            'M': 100e9 * YEAR
        }

        # Planetary evolution rates
        self.cooling_rate = 1e-15  # Temperature decay per second
        self.atmospheric_escape_rate = 1e-18  # Atmosphere loss rate
        self.tectonic_decay_rate = 1e-17  # Tectonic activity decay
        self.biosphere_growth_rate = 1e-16  # Biosphere development rate

    def add_star(self, star_id: str, initial_mass: float, initial_radius: float,
                 initial_temperature: float, metallicity: float) -> None:
        """Add a star to the simulation"""

        # Calculate initial luminosity using Stefan-Boltzmann law
        initial_luminosity = 4 * np.pi * initial_radius**2 * STEFAN_BOLTZMANN * initial_temperature**4

        # Determine main sequence lifetime based on mass
        lifetime = self.calculate_main_sequence_lifetime(initial_mass)

        # Initial rotation period (massive stars rotate faster)
        if initial_mass > 10 * SOLAR_MASS:
            rotation_period = np.random.uniform(0.5, 2) * 24 * 3600  # 0.5-2 days
        elif initial_mass > 2 * SOLAR_MASS:
            rotation_period = np.random.uniform(1, 10) * 24 * 3600  # 1-10 days
        else:
            rotation_period = np.random.uniform(20, 30) * 24 * 3600  # 20-30 days

        # Initial magnetic field (depends on rotation and mass)
        magnetic_field = np.random.uniform(1e-4, 1e-2) * (initial_mass / SOLAR_MASS) * (86400 / rotation_period)

        star_track = StellarEvolutionTrack(
            current_phase=StellarPhase.MAIN_SEQUENCE,
            age=0.0,
            initial_mass=initial_mass,
            current_mass=initial_mass,
            current_radius=initial_radius,
            current_temperature=initial_temperature,
            current_luminosity=initial_luminosity,
            lifetime_remaining=lifetime,
            metallicity=metallicity,
            rotation_period=rotation_period,
            magnetic_field_strength=magnetic_field
        )

        self.stars[star_id] = star_track

    def add_planet(self, planet_id: str, initial_mass: float, initial_radius: float,
                   initial_temperature: float, initial_atmosphere: Dict[str, float]) -> None:
        """Add a planet to the simulation"""

        # Calculate initial atmospheric pressure
        surface_gravity = G * initial_mass / initial_radius**2
        atmospheric_pressure = surface_gravity * sum(initial_atmosphere.values()) * 1e4  # Simplified

        # Initial water coverage based on temperature
        if 273 < initial_temperature < 373:
            water_coverage = np.random.uniform(0.3, 0.8)
        elif initial_temperature < 273:
            water_coverage = 0.1  # Mostly ice
        else:
            water_coverage = 0.01  # Too hot for liquid water

        # Initial biosphere (small chance of life)
        if 273 < initial_temperature < 373 and water_coverage > 0.1:
            biosphere_complexity = np.random.uniform(0.01, 0.1) * np.random.choice([0, 1], p=[0.9, 0.1])
        else:
            biosphere_complexity = 0.0

        # Initial tectonic activity (depends on mass and age)
        tectonic_activity = min(1.0, (initial_mass / EARTH_MASS) * np.exp(-self.time / (5e9 * YEAR)))

        # Initial magnetic field (depends on rotation and core composition)
        magnetic_field = np.random.uniform(1e-7, 1e-5) * (initial_mass / EARTH_MASS)

        # Orbital drift (very slow)
        orbital_drift_rate = np.random.uniform(-1e-10, 1e-10) * AU  # meters per second

        planet_evolution = PlanetaryEvolution(
            age=0.0,
            mass=initial_mass,
            radius=initial_radius,
            atmospheric_pressure=atmospheric_pressure,
            surface_temperature=initial_temperature,
            water_coverage=water_coverage,
            biosphere_complexity=biosphere_complexity,
            tectonic_activity=tectonic_activity,
            magnetic_field_strength=magnetic_field,
            orbital_drift_rate=orbital_drift_rate,
            atmosphere_composition=initial_atmosphere.copy()
        )

        self.planets[planet_id] = planet_evolution

    def calculate_main_sequence_lifetime(self, mass: float) -> float:
        """Calculate main sequence lifetime based on stellar mass"""

        mass_solar = mass / SOLAR_MASS

        if mass_solar < 0.5:
            # Low mass stars live longer than simple scaling
            lifetime = 10e9 * YEAR * (mass_solar ** -2.5)
        elif mass_solar < 2:
            # Sun-like stars
            lifetime = 10e9 * YEAR * (mass_solar ** -3.5)
        elif mass_solar < 20:
            # Intermediate mass stars
            lifetime = 10e9 * YEAR * (mass_solar ** -3)
        else:
            # Very massive stars
            lifetime = 10e9 * YEAR * (mass_solar ** -2.5)

        return lifetime

    def evolve_star(self, star_id: str, dt: float) -> None:
        """Evolve a star over time step dt"""

        if star_id not in self.stars:
            return

        star = self.stars[star_id]
        star.age += dt

        # Mass loss through stellar wind
        if star.current_phase in [StellarPhase.RED_GIANT, StellarPhase.ASYMPTOTIC_GIANT]:
            mass_loss_rate = 1e-7 * SOLAR_MASS / YEAR  # Higher for giants
        elif star.current_phase == StellarPhase.MAIN_SEQUENCE:
            mass_loss_rate = 1e-14 * SOLAR_MASS / YEAR * (star.current_mass / SOLAR_MASS) ** 2
        else:
            mass_loss_rate = 1e-16 * SOLAR_MASS / YEAR

        star.current_mass -= mass_loss_rate * dt

        # Update stellar parameters based on phase
        if star.current_phase == StellarPhase.MAIN_SEQUENCE:
            self.evolve_main_sequence(star, dt)
        elif star.current_phase == StellarPhase.SUBGIANT:
            self.evolve_subgiant(star, dt)
        elif star.current_phase == StellarPhase.RED_GIANT:
            self.evolve_red_giant(star, dt)
        elif star.current_phase == StellarPhase.HORIZONTAL_BRANCH:
            self.evolve_horizontal_branch(star, dt)
        elif star.current_phase == StellarPhase.ASYMPTOTIC_GIANT:
            self.evolve_asymptotic_giant(star, dt)
        elif star.current_phase == StellarPhase.WHITE_DWARF:
            self.evolve_white_dwarf(star, dt)
        elif star.current_phase == StellarPhase.NEUTRON_STAR:
            self.evolve_neutron_star(star, dt)
        elif star.current_phase == StellarPhase.BLACK_HOLE:
            self.evolve_black_hole(star, dt)

        # Update rotation (stars slow down over time)
        star.rotation_period *= (1 + 1e-16 * dt / YEAR)

        # Update magnetic field
        star.magnetic_field_strength *= (1 - 1e-17 * dt / YEAR)

        # Check for stellar events
        self.check_stellar_events(star)

    def evolve_main_sequence(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a main sequence star"""

        # Gradual brightening over main sequence lifetime
        age_fraction = star.age / (star.age + star.lifetime_remaining)
        luminosity_increase = 1 + 0.3 * age_fraction  # Stars brighten by ~30% on main sequence

        star.current_luminosity *= luminosity_increase ** (dt / (star.age + star.lifetime_remaining))

        # Temperature changes slightly
        mass_solar = star.current_mass / SOLAR_MASS
        if mass_solar > 1:
            star.current_temperature *= 1 + 1e-10 * dt / YEAR  # Massive stars heat up
        else:
            star.current_temperature *= 1 - 1e-11 * dt / YEAR  # Low mass stars cool slightly

        # Radius changes to maintain luminosity
        star.current_radius = np.sqrt(star.current_luminosity / (4 * np.pi * STEFAN_BOLTZMANN * star.current_temperature**4))

        # Update lifetime remaining
        star.lifetime_remaining -= dt

        # Check if star should leave main sequence
        if star.lifetime_remaining <= 0:
            if star.initial_mass > 8 * SOLAR_MASS:
                # Massive star -> supergiant -> supernova
                star.current_phase = StellarPhase.SUPERNOVA
                self.create_cosmic_event(CosmicEventType.SUPERNOVA,
                                       "Core collapse supernova",
                                       intensity=1.0,
                                       location=np.array([0, 0, 0]))
            else:
                # Low/intermediate mass -> red giant
                star.current_phase = StellarPhase.SUBGIANT
                star.lifetime_remaining = 0.1e9 * YEAR  # Subgiant phase lasts ~100 million years

    def evolve_subgiant(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a subgiant star"""

        # Rapid expansion and cooling
        star.current_radius *= 1 + 1e-14 * dt / YEAR
        star.current_temperature *= 1 - 1e-14 * dt / YEAR

        # Luminosity increases
        star.current_luminosity *= 1 + 1e-13 * dt / YEAR

        star.lifetime_remaining -= dt

        if star.lifetime_remaining <= 0:
            star.current_phase = StellarPhase.RED_GIANT
            star.lifetime_remaining = 1e9 * YEAR  # Red giant phase

    def evolve_red_giant(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a red giant star"""

        # Continue expansion
        expansion_rate = 1e-13 * (star.initial_mass / SOLAR_MASS)
        star.current_radius *= 1 + expansion_rate * dt / YEAR

        # Temperature drops
        star.current_temperature *= 1 - 5e-15 * dt / YEAR

        # High mass loss
        mass_loss_rate = 1e-7 * SOLAR_MASS / YEAR * (star.current_radius / SOLAR_RADIUS)
        star.current_mass -= mass_loss_rate * dt

        star.lifetime_remaining -= dt

        if star.lifetime_remaining <= 0:
            if star.initial_mass > 0.8 * SOLAR_MASS:
                star.current_phase = StellarPhase.ASYMPTOTIC_GIANT
                star.lifetime_remaining = 0.01e9 * YEAR  # AGB phase
            else:
                star.current_phase = StellarPhase.WHITE_DWARF
                star.current_radius = 0.01 * SOLAR_RADIUS  # Earth-sized
                star.current_temperature = 10000  # Hot white dwarf

    def evolve_horizontal_branch(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a horizontal branch star"""

        # Relatively stable phase
        star.current_radius *= 1 + 1e-16 * dt / YEAR
        star.current_temperature *= 1 + 1e-16 * dt / YEAR

        star.lifetime_remaining -= dt

        if star.lifetime_remaining <= 0:
            star.current_phase = StellarPhase.ASYMPTOTIC_GIANT
            star.lifetime_remaining = 0.01e9 * YEAR

    def evolve_asymptotic_giant(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve an asymptotic giant branch star"""

        # Pulsations and heavy mass loss
        pulsation_period = 100 * 24 * 3600  # 100 days
        mass_loss_rate = 1e-5 * SOLAR_MASS / YEAR

        star.current_mass -= mass_loss_rate * dt
        star.current_radius *= 1 + 1e-12 * dt / YEAR * np.sin(2 * np.pi * star.age / pulsation_period)

        star.lifetime_remaining -= dt

        if star.lifetime_remaining <= 0:
            star.current_phase = StellarPhase.PLANETARY_NEBULA
            self.create_cosmic_event(CosmicEventType.PLANETARY_NEBULA,
                                   "Planetary nebula ejection",
                                   intensity=0.5,
                                   location=np.array([0, 0, 0]))
            star.lifetime_remaining = 10000 * YEAR  # Planetary nebula phase

    def evolve_white_dwarf(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a white dwarf"""

        # Cooling white dwarf
        star.current_temperature *= 1 - 1e-15 * dt / YEAR

        # Radius remains constant (degenerate matter)
        star.current_radius = 0.01 * SOLAR_RADIUS

        # Luminosity decreases with temperature
        star.current_luminosity = 4 * np.pi * star.current_radius**2 * STEFAN_BOLTZMANN * star.current_temperature**4

        # Magnetic field decays very slowly
        star.magnetic_field_strength *= 1 - 1e-18 * dt / YEAR

    def evolve_neutron_star(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a neutron star"""

        # Neutron stars cool very slowly
        star.current_temperature *= 1 - 1e-16 * dt / YEAR

        # Very small radius (10 km)
        star.current_radius = 10000

        # Rotation slows down (magnetic braking)
        star.rotation_period *= 1 + 1e-15 * dt / YEAR

        # Strong magnetic field that decays slowly
        star.magnetic_field_strength *= 1 - 1e-17 * dt / YEAR

        # Can produce pulsar flashes
        if random.random() < 1e-12 * dt / YEAR:
            self.create_cosmic_event(CosmicEventType.GAMMA_RAY_BURST,
                                   "Pulsar emission burst",
                                   intensity=0.3,
                                   location=np.array([0, 0, 0]))

    def evolve_black_hole(self, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve a black hole"""

        # Schwarzschild radius
        star.current_radius = 2 * G * star.current_mass / c**2

        # Hawking radiation (extremely slow)
        hawking_power = 3.56e-32 * (star.current_mass / SOLAR_MASS) ** -2  # Watts
        mass_loss = hawking_power * dt / c**2
        star.current_mass -= mass_loss

        # No temperature in classical sense
        star.current_temperature = 0

        # Accretion disk effects if there's material nearby
        # This would be handled by the larger system dynamics

    def evolve_planet(self, planet_id: str, star_id: str, dt: float) -> None:
        """Evolve a planet over time"""

        if planet_id not in self.planets or star_id not in self.stars:
            return

        planet = self.planets[planet_id]
        star = self.stars[star_id]
        planet.age += dt

        # Thermal evolution (cooling)
        cooling_factor = np.exp(-planet.age / (5e9 * YEAR))
        planet.surface_temperature = max(2.7, planet.surface_temperature * (1 - self.cooling_rate * dt))

        # Stellar heating
        orbital_radius = 1.0 * AU  # This would come from orbital mechanics
        stellar_flux = star.current_luminosity / (4 * np.pi * orbital_radius**2)
        equilibrium_temp = (stellar_flux / (4 * STEFAN_BOLTZMANN)) ** 0.25
        planet.surface_temperature = 0.7 * planet.surface_temperature + 0.3 * equilibrium_temp

        # Atmospheric evolution
        self.evolve_atmosphere(planet, star, dt)

        # Water cycle evolution
        self.evolve_water_cycle(planet, dt)

        # Biosphere evolution
        self.evolve_biosphere(planet, dt)

        # Tectonic evolution
        planet.tectonic_activity *= 1 - self.tectonic_decay_rate * dt

        # Magnetic field evolution
        planet.magnetic_field_strength *= 1 - 1e-16 * dt / YEAR

        # Orbital evolution
        # This would be handled by the orbital mechanics engine
        # planet.orbital_radius += planet.orbital_drift_rate * dt

        # Check for planetary events
        self.check_planetary_events(planet)

    def evolve_atmosphere(self, planet: PlanetaryEvolution, star: StellarEvolutionTrack, dt: float) -> None:
        """Evolve planetary atmosphere"""

        # Atmospheric escape (especially for low gravity planets)
        escape_velocity = np.sqrt(2 * G * planet.mass / planet.radius)
        if escape_velocity < 10000:  # 10 km/s threshold
            escape_rate = self.atmospheric_escape_rate * (10000 / escape_velocity) ** 2
        else:
            escape_rate = self.atmospheric_escape_rate * 0.1

        # Stellar wind stripping
        stellar_wind_pressure = star.current_luminosity / (4 * np.pi * AU**2 * c**2)
        wind_stripping_rate = stellar_wind_pressure * 1e-20 * dt

        # Update atmospheric pressure
        planet.atmospheric_pressure *= (1 - escape_rate * dt - wind_stripping_rate)

        # Atmospheric composition changes
        if planet.surface_temperature > 373:  # Too hot - water vapor escapes
            planet.atmosphere_composition['H2O'] *= 0.999

        # Volcanic outgassing (if tectonically active)
        if planet.tectonic_activity > 0.1:
            outgassing_rate = planet.tectonic_activity * 1e-18 * dt
            planet.atmosphere_composition['CO2'] += outgassing_rate
            planet.atmosphere_composition['H2O'] += outgassing_rate * 0.5

    def evolve_water_cycle(self, planet: PlanetaryEvolution, dt: float) -> None:
        """Evolve planetary water cycle"""

        # Ice formation/melting
        if planet.surface_temperature < 273:
            ice_formation_rate = (273 - planet.surface_temperature) / 273 * 1e-15
            planet.water_coverage *= 1 - ice_formation_rate * dt
        elif planet.surface_temperature > 373:
            evaporation_rate = (planet.surface_temperature - 373) / 373 * 1e-14
            planet.water_coverage *= 1 - evaporation_rate * dt
        else:
            # Liquid water stability
            if planet.atmospheric_pressure > 1e4:  # Sufficient pressure
                precipitation_rate = 1e-16 * planet.water_coverage
                planet.water_coverage += precipitation_rate * dt

        # Atmospheric water vapor
        if planet.surface_temperature > 273:
            vapor_pressure = 611 * np.exp(17.27 * (planet.surface_temperature - 273) / (planet.surface_temperature - 273 + 237.3))
            if 'H2O' in planet.atmosphere_composition:
                planet.atmosphere_composition['H2O'] = min(0.1, vapor_pressure / planet.atmospheric_pressure)

        planet.water_coverage = max(0, min(1, planet.water_coverage))

    def evolve_biosphere(self, planet: PlanetaryEvolution, dt: float) -> None:
        """Evolve planetary biosphere"""

        # Biosphere can only develop in suitable conditions
        if 273 < planet.surface_temperature < 373 and planet.water_coverage > 0.1 and planet.atmospheric_pressure > 1e4:
            # Growth phase
            if planet.biosphere_complexity < 0.01:  # Abiogenesis chance
                if random.random() < 1e-16 * dt:  # Very small chance
                    planet.biosphere_complexity = 0.01
            else:
                # Evolution and growth
                growth_rate = self.biosphere_growth_rate * planet.water_coverage
                planet.biosphere_complexity *= 1 + growth_rate * dt

                # Biosphere affects atmosphere
                if planet.biosphere_complexity > 0.1:
                    # Photosynthesis produces oxygen
                    if 'O2' in planet.atmosphere_composition:
                        planet.atmosphere_composition['O2'] += 1e-18 * planet.biosphere_complexity * dt
                        planet.atmosphere_composition['CO2'] -= 5e-19 * planet.biosphere_complexity * dt
        else:
            # Biosphere decline in harsh conditions
            decline_rate = 1e-15 * dt
            planet.biosphere_complexity *= 1 - decline_rate

        planet.biosphere_complexity = max(0, min(1, planet.biosphere_complexity))

    def check_stellar_events(self, star: StellarEvolutionTrack) -> None:
        """Check for and create stellar events"""

        # Solar flares (more common for active stars)
        if star.current_phase == StellarPhase.MAIN_SEQUENCE and star.magnetic_field_strength > 1e-3:
            if random.random() < 1e-14 * (star.magnetic_field_strength / 1e-2):
                intensity = min(1.0, star.magnetic_field_strength / 1e-2)
                self.create_cosmic_event(CosmicEventType.SOLAR_FLARE,
                                       "Solar flare eruption",
                                       intensity=intensity,
                                       location=np.array([0, 0, 0]))

        # Coronal mass ejections
        if star.current_phase in [StellarPhase.MAIN_SEQUENCE, StellarPhase.RED_GIANT]:
            if random.random() < 1e-15:
                self.create_cosmic_event(CosmicEventType.CORONAL_MASS_EJECTION,
                                       "Coronal mass ejection",
                                       intensity=0.5,
                                       location=np.array([0, 0, 0]))

        # Magnetic field reversals
        if star.magnetic_field_strength > 1e-4:
            if random.random() < 1e-16:
                star.magnetic_field_strength *= -1  # Reverse polarity
                self.create_cosmic_event(CosmicEventType.MAGNETIC_REVERSAL,
                                       "Stellar magnetic field reversal",
                                       intensity=0.3,
                                       location=np.array([0, 0, 0]))

    def check_planetary_events(self, planet: PlanetaryEvolution) -> None:
        """Check for and create planetary events"""

        # Large impacts (rare)
        if random.random() < 1e-17:
            impact_type = random.choice([CosmicEventType.ASTEROID_IMPACT, CosmicEventType.COMET_IMPACT])
            self.create_cosmic_event(impact_type,
                                   f"Large {impact_type.value.replace('_', ' ')} impact",
                                   intensity=0.8,
                                   location=np.array([0, 0, 0]))

            # Impact effects
            planet.surface_temperature += 100  # Temporary heating
            planet.atmospheric_pressure *= 1.1  # Atmospheric injection
            if planet.biosphere_complexity > 0.1:
                planet.biosphere_complexity *= 0.5  # Biosphere damage

    def create_cosmic_event(self, event_type: CosmicEventType, description: str,
                          intensity: float, location: np.ndarray,
                          duration: float = 1e6) -> None:
        """Create a cosmic event"""

        event = CosmicEvent(
            event_type=event_type,
            time=self.time,
            duration=duration,
            location=location,
            intensity=intensity,
            affected_objects=[],  # Would be populated based on proximity
            description=description
        )

        self.cosmic_events.append(event)
        self.active_events.append(event)

    def update_events(self, dt: float) -> None:
        """Update active cosmic events"""

        # Remove expired events
        self.active_events = [event for event in self.active_events
                            if self.time - event.time < event.duration]

        # Move expired events to history
        for event in self.cosmic_events:
            if self.time - event.time > event.duration and event not in self.event_history:
                self.event_history.append(event)

        # Apply ongoing event effects
        for event in self.active_events:
            self.apply_event_effects(event, dt)

    def apply_event_effects(self, event: CosmicEvent, dt: float) -> None:
        """Apply effects of ongoing cosmic events"""

        if event.event_type == CosmicEventType.SOLAR_FLARE:
            # Increase stellar radiation
            for star_id, star in self.stars.items():
                star.current_luminosity *= (1 + 0.1 * event.intensity)
                star.magnetic_field_strength *= (1 + 0.2 * event.intensity)

        elif event.event_type == CosmicEventType.CORONAL_MASS_EJECTION:
            # Strip planetary atmospheres
            for planet_id, planet in self.planets.items():
                planet.atmospheric_pressure *= (1 - 0.1 * event.intensity * dt / event.duration)

        elif event.event_type == CosmicEventType.SUPERNOVA:
            # Devastating effects on nearby planets
            for planet_id, planet in self.planets.items():
                planet.biosphere_complexity = 0  # Sterilize
                planet.atmosphere_composition = {}  # Strip atmosphere
                planet.surface_temperature += 1000 * event.intensity

        elif event.event_type == CosmicEventType.GAMMA_RAY_BURST:
            # Radiation damage to biospheres
            for planet_id, planet in self.planets.items():
                if planet.biosphere_complexity > 0:
                    planet.biosphere_complexity *= (1 - 0.5 * event.intensity)

    def step(self) -> None:
        """Advance simulation by one time step"""

        # Evolve all stars
        for star_id in list(self.stars.keys()):
            self.evolve_star(star_id, self.time_step)

        # Evolve all planets
        # In a real implementation, we'd need to know which star each planet orbits
        for planet_id in list(self.planets.keys()):
            # Assume first star for simplicity
            if self.stars:
                star_id = list(self.stars.keys())[0]
                self.evolve_planet(planet_id, star_id, self.time_step)

        # Update cosmic events
        self.update_events(self.time_step)

        # Advance time
        self.time += self.time_step

    def get_system_status(self) -> Dict:
        """Get current status of the simulated system"""

        status = {
            'time_years': self.time / YEAR,
            'time_steps': self.time / self.time_step,
            'stars': {},
            'planets': {},
            'active_events': len(self.active_events),
            'total_events': len(self.event_history)
        }

        for star_id, star in self.stars.items():
            status['stars'][star_id] = {
                'phase': star.current_phase.value,
                'age_gyr': star.age / (1e9 * YEAR),
                'mass_solar': star.current_mass / SOLAR_MASS,
                'radius_solar': star.current_radius / SOLAR_RADIUS,
                'temperature_k': star.current_temperature,
                'luminosity_solar': star.current_luminosity / SOLAR_LUMINOSITY
            }

        for planet_id, planet in self.planets.items():
            status['planets'][planet_id] = {
                'age_gyr': planet.age / (1e9 * YEAR),
                'mass_earth': planet.mass / EARTH_MASS,
                'radius_earth': planet.radius / (6.371e6),
                'temperature_k': planet.surface_temperature,
                'atmosphere_pressure_bar': planet.atmospheric_pressure / 1e5,
                'water_coverage': planet.water_coverage,
                'biosphere_complexity': planet.biosphere_complexity,
                'tectonic_activity': planet.tectonic_activity
            }

        return status

    def run_simulation(self, num_steps: int) -> Dict:
        """Run simulation for specified number of steps"""

        print(f"Starting star system simulation for {num_steps} steps...")
        print(f"Time step: {self.time_step / YEAR:.1f} years")
        print(f"Total simulation time: {num_steps * self.time_step / YEAR:.1f} years")

        for step in range(num_steps):
            self.step()

            if step % max(1, num_steps // 10) == 0:
                progress = step / num_steps * 100
                current_time_gyr = self.time / (1e9 * YEAR)
                print(f"Progress: {progress:.0f}%, Time: {current_time_gyr:.2f} Gyr")

        print("\nSimulation completed!")
        return self.get_system_status()

# Example usage and testing
if __name__ == "__main__":
    # Create simulator
    simulator = StarSystemSimulator(time_step=1e6 * YEAR)  # 1 million years per step

    # Add a sun-like star
    simulator.add_star(
        star_id="sun",
        initial_mass=SOLAR_MASS,
        initial_radius=SOLAR_RADIUS,
        initial_temperature=5778,
        metallicity=0.02
    )

    # Add Earth-like planet
    earth_atmosphere = {
        'N2': 0.78,
        'O2': 0.21,
        'Ar': 0.01,
        'CO2': 0.0004
    }

    simulator.add_planet(
        planet_id="earth",
        initial_mass=EARTH_MASS,
        initial_radius=6.371e6,
        initial_temperature=288,
        initial_atmosphere=earth_atmosphere
    )

    # Add Mars-like planet
    mars_atmosphere = {
        'CO2': 0.95,
        'N2': 0.027,
        'Ar': 0.016,
        'O2': 0.013
    }

    simulator.add_planet(
        planet_id="mars",
        initial_mass=0.107 * EARTH_MASS,
        initial_radius=3.390e6,
        initial_temperature=210,
        initial_atmosphere=mars_atmosphere
    )

    # Run simulation for 5 billion years
    status = simulator.run_simulation(num_steps=5000)  # 5 billion years

    # Print final status
    print("\n" + "="*50)
    print("FINAL SYSTEM STATUS")
    print("="*50)

    for star_id, star_info in status['stars'].items():
        print(f"\n{star_id.upper()}:")
        print(f"  Phase: {star_info['phase']}")
        print(f"  Age: {star_info['age_gyr']:.2f} Gyr")
        print(f"  Mass: {star_info['mass_solar']:.3f} M☉")
        print(f"  Radius: {star_info['radius_solar']:.3f} R☉")
        print(f"  Temperature: {star_info['temperature_k']:.0f} K")
        print(f"  Luminosity: {star_info['luminosity_solar']:.3f} L☉")

    for planet_id, planet_info in status['planets'].items():
        print(f"\n{planet_id.upper()}:")
        print(f"  Age: {planet_info['age_gyr']:.2f} Gyr")
        print(f"  Mass: {planet_info['mass_earth']:.3f} M⊕")
        print(f"  Radius: {planet_info['radius_earth']:.3f} R⊕")
        print(f"  Temperature: {planet_info['temperature_k']:.1f} K")
        print(f"  Atmosphere: {planet_info['atmosphere_pressure_bar']:.3f} bar")
        print(f"  Water Coverage: {planet_info['water_coverage']:.1%}")
        print(f"  Biosphere: {planet_info['biosphere_complexity']:.3f}")
        print(f"  Tectonic Activity: {planet_info['tectonic_activity']:.3f}")

    print(f"\nCosmic Events: {status['total_events']} total, {status['active_events']} active")

    if simulator.event_history:
        print("\nMajor Cosmic Events:")
        for event in simulator.event_history[-5:]:  # Show last 5 events
            print(f"  {event.time/YEAR/1e6:.1f} Myr: {event.description} (Intensity: {event.intensity:.2f})")

    print("\nStar system simulation completed successfully!")