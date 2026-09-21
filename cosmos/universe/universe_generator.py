#!/usr/bin/env python3
"""
Universe Generator - Procedural Galaxy and Universe Generation
Creates billions of star systems with realistic astronomical parameters
"""

import numpy as np
import random
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from enum import Enum
import math

# Astronomical Constants (in SI units)
PARSEC = 3.086e16  # meters
LIGHT_YEAR = 9.461e15  # meters
SOLAR_MASS = 1.989e30  # kg
EARTH_MASS = 5.972e24  # kg
SOLAR_RADIUS = 6.96e8  # meters
EARTH_RADIUS = 6.371e6  # meters
AU = 1.496e11  # meters (Astronomical Unit)
G = 6.67430e-11  # Gravitational constant
c = 299792458  # Speed of light in m/s

class StarType(Enum):
    O = "O"  # Blue supergiants (>30,000K)
    B = "B"  # Blue-white giants (10,000-30,000K)
    A = "A"  # White stars (7,500-10,000K)
    F = "F"  # Yellow-white stars (6,000-7,500K)
    G = "G"  # Yellow stars like Sun (5,200-6,000K)
    K = "K"  # Orange stars (3,700-5,200K)
    M = "M"  # Red dwarfs (<3,700K)

    # Special types
    WHITE_DWARF = "WD"
    NEUTRON_STAR = "NS"
    BLACK_HOLE = "BH"
    RED_GIANT = "RG"

class PlanetType(Enum):
    TERRESTRIAL = "terrestrial"
    GAS_GIANT = "gas_giant"
    ICE_GIANT = "ice_giant"
    DESERT = "desert"
    OCEAN = "ocean"
    LAVA = "lava"
    ICE = "ice"
    TUNDRA = "tundra"
    ARTIFICIAL = "artificial"

@dataclass
class CelestialBody:
    id: str
    name: str
    mass: float  # kg
    radius: float  # meters
    position: np.ndarray  # 3D position [x, y, z] in meters
    velocity: np.ndarray  # 3D velocity [vx, vy, vz] in m/s
    temperature: float  # Kelvin
    age: float  # years
    parent_id: Optional[str] = None

@dataclass
class Star(CelestialBody):
    star_type: StarType
    luminosity: float  # Solar luminosities
    spectral_class: str
    metallicity: float  # [Fe/H] ratio
    rotation_period: float  # hours
    magnetic_field: float  # Tesla
    habitation_zone: Tuple[float, float]  # AU (inner, outer)

@dataclass
class Planet(CelestialBody):
    planet_type: PlanetType
    orbital_radius: float  # AU
    orbital_period: float  # years
    eccentricity: float
    inclination: float  # degrees
    atmosphere: Dict[str, float]  # Gas composition percentages
    biosphere: bool
    resources: Dict[str, float]  # Resource quantities
    moons: List[str]  # IDs of moons

@dataclass
class Galaxy:
    id: str
    name: str
    galaxy_type: str  # spiral, elliptical, irregular
    mass: float  # kg
    radius: float  # meters
    star_count: int
    center_position: np.ndarray
    rotation_period: float  # years
    spiral_arms: int  # For spiral galaxies
    star_systems: Dict[str, 'StarSystem']

@dataclass
class StarSystem:
    id: str
    primary_star: Star
    planets: List[Planet]
    asteroids: List[CelestialBody]
    comets: List[CelestialBody]
    space_stations: List[CelestialBody]
    debris_fields: List[Dict]
    age: float  # years
    metallicity: float

class UniverseGenerator:
    """Generates realistic galaxies and star systems"""

    def __init__(self, seed: Optional[int] = None):
        if seed:
            np.random.seed(seed)
            random.seed(seed)
            self.seed = seed
        else:
            self.seed = random.randint(0, 2**31 - 1)
            np.random.seed(self.seed)
            random.seed(self.seed)

        self.galaxy_types = {
            'spiral': {'frequency': 0.77, 'arms': [2, 4, 6]},
            'elliptical': {'frequency': 0.20, 'arms': [0]},
            'irregular': {'frequency': 0.03, 'arms': [0]}
        }

        # Star type distribution (Main Sequence)
        self.star_distribution = {
            StarType.O: 0.00003,
            StarType.B: 0.0013,
            StarType.A: 0.006,
            StarType.F: 0.03,
            StarType.G: 0.076,
            StarType.K: 0.121,
            StarType.M: 0.765
        }

        # Special stellar remnants
        self.remnant_chances = {
            'white_dwarf': 0.05,
            'neutron_star': 0.01,
            'black_hole': 0.001
        }

    def generate_galaxy(self, galaxy_id: str, position: np.ndarray,
                       galaxy_type: Optional[str] = None) -> Galaxy:
        """Generate a galaxy with billions of star systems"""

        if not galaxy_type:
            rand = random.random()
            if rand < 0.77:
                galaxy_type = 'spiral'
            elif rand < 0.97:
                galaxy_type = 'elliptical'
            else:
                galaxy_type = 'irregular'

        # Galaxy parameters based on type
        if galaxy_type == 'spiral':
            mass = np.random.uniform(1e11, 1e12) * SOLAR_MASS
            radius = np.random.uniform(30, 100) * 1000 * PARSEC
            star_count = np.random.randint(200_000_000, 400_000_000)
            spiral_arms = random.choice([2, 4, 6])
            rotation_period = np.random.uniform(200, 250) * 1e6  # years
        elif galaxy_type == 'elliptical':
            mass = np.random.uniform(1e12, 1e13) * SOLAR_MASS
            radius = np.random.uniform(10, 200) * 1000 * PARSEC
            star_count = np.random.randint(500_000_000, 1_000_000_000)
            spiral_arms = 0
            rotation_period = np.random.uniform(300, 500) * 1e6  # years
        else:  # irregular
            mass = np.random.uniform(1e9, 1e11) * SOLAR_MASS
            radius = np.random.uniform(5, 30) * 1000 * PARSEC
            star_count = np.random.randint(10_000_000, 100_000_000)
            spiral_arms = 0
            rotation_period = np.random.uniform(100, 200) * 1e6  # years

        galaxy = Galaxy(
            id=galaxy_id,
            name=f"Galaxy-{galaxy_id[:8]}",
            galaxy_type=galaxy_type,
            mass=mass,
            radius=radius,
            star_count=star_count,
            center_position=position,
            rotation_period=rotation_period,
            spiral_arms=spiral_arms,
            star_systems={}
        )

        return galaxy

    def generate_star_system_position(self, galaxy: Galaxy) -> np.ndarray:
        """Generate 3D position for a star system within a galaxy"""

        if galaxy.galaxy_type == 'spiral':
            # Spiral arm distribution
            angle = np.random.uniform(0, 2 * np.pi)

            # Distance from center (concentrated in arms)
            if galaxy.spiral_arms > 0:
                arm = random.randint(0, galaxy.spiral_arms - 1)
                arm_angle = (2 * np.pi * arm) / galaxy.spiral_arms

                # Logarithmic spiral
                r = np.random.exponential(galaxy.radius * 0.3)
                theta = arm_angle + 0.2 * np.log(r + 1)

                # Add scatter around arm
                scatter = np.random.normal(0, galaxy.radius * 0.05)
                r += scatter
            else:
                r = np.random.uniform(0, galaxy.radius)
                theta = angle

            # Vertical distribution (thin disk)
            z = np.random.normal(0, galaxy.radius * 0.01)

        elif galaxy.galaxy_type == 'elliptical':
            # Spherical distribution with concentration toward center
            r = np.random.exponential(galaxy.radius * 0.3)
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)

            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)
            return np.array([x, y, z])

        else:  # irregular
            # Random clumpy distribution
            x = np.random.normal(0, galaxy.radius * 0.3)
            y = np.random.normal(0, galaxy.radius * 0.3)
            z = np.random.normal(0, galaxy.radius * 0.1)
            return np.array([x, y, z])

        # Convert to Cartesian coordinates
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        return galaxy.center_position + np.array([x, y, z])

    def generate_star(self, star_id: str, age: float) -> Star:
        """Generate a realistic star with proper stellar parameters"""

        # Determine star type based on age and distribution
        rand = random.random()

        # Older systems have more stellar remnants
        if age > 10e9:  # 10 billion years
            if rand < self.remnant_chances['black_hole']:
                star_type = StarType.BLACK_HOLE
            elif rand < self.remnant_chances['neutron_star']:
                star_type = StarType.NEUTRON_STAR
            elif rand < self.remnant_chances['white_dwarf']:
                star_type = StarType.WHITE_DWARF

        # Main sequence star selection
        cumulative = 0
        for star_type, probability in self.star_distribution.items():
            cumulative += probability
            if rand < cumulative:
                break

        # Star parameters based on type
        if star_type == StarType.O:
            mass = np.random.uniform(16, 50) * SOLAR_MASS
            radius = np.random.uniform(6.6, 20) * SOLAR_RADIUS
            temperature = np.random.uniform(30000, 50000)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.B:
            mass = np.random.uniform(2.1, 16) * SOLAR_MASS
            radius = np.random.uniform(1.8, 6.6) * SOLAR_RADIUS
            temperature = np.random.uniform(10000, 30000)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.A:
            mass = np.random.uniform(1.4, 2.1) * SOLAR_MASS
            radius = np.random.uniform(1.4, 1.8) * SOLAR_RADIUS
            temperature = np.random.uniform(7500, 10000)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.F:
            mass = np.random.uniform(1.04, 1.4) * SOLAR_MASS
            radius = np.random.uniform(1.15, 1.4) * SOLAR_RADIUS
            temperature = np.random.uniform(6000, 7500)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.G:
            mass = np.random.uniform(0.8, 1.04) * SOLAR_MASS
            radius = np.random.uniform(0.96, 1.15) * SOLAR_RADIUS
            temperature = np.random.uniform(5200, 6000)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.K:
            mass = np.random.uniform(0.45, 0.8) * SOLAR_MASS
            radius = np.random.uniform(0.7, 0.96) * SOLAR_RADIUS
            temperature = np.random.uniform(3700, 5200)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.M:
            mass = np.random.uniform(0.08, 0.45) * SOLAR_MASS
            radius = np.random.uniform(0.1, 0.7) * SOLAR_RADIUS
            temperature = np.random.uniform(2400, 3700)
            luminosity = (mass / SOLAR_MASS) ** 3.5
            lifetime = 1e10 * (SOLAR_MASS / mass) ** 2.5
        elif star_type == StarType.BLACK_HOLE:
            mass = np.random.uniform(5, 50) * SOLAR_MASS
            radius = 2 * G * mass / (c ** 2)  # Schwarzschild radius
            temperature = 0  # No temperature in classical sense
            luminosity = 0
            lifetime = float('inf')
        elif star_type == StarType.NEUTRON_STAR:
            mass = np.random.uniform(1.4, 3) * SOLAR_MASS
            radius = np.random.uniform(10000, 12000)  # meters
            temperature = np.random.uniform(100000, 1000000)
            luminosity = 0.001
            lifetime = float('inf')
        elif star_type == StarType.WHITE_DWARF:
            mass = np.random.uniform(0.17, 1.4) * SOLAR_MASS
            radius = np.random.uniform(0.008, 0.02) * SOLAR_RADIUS
            temperature = np.random.uniform(4000, 40000)
            luminosity = 0.01
            lifetime = float('inf')
        else:
            # Default to sun-like star
            mass = SOLAR_MASS
            radius = SOLAR_RADIUS
            temperature = 5778
            luminosity = 1.0
            lifetime = 10e9

        # Calculate habitable zone for main sequence stars
        if star_type in [StarType.O, StarType.B, StarType.A, StarType.F,
                        StarType.G, StarType.K, StarType.M]:
            # Inner and outer habitable zone boundaries
            inner_hz = np.sqrt(luminosity / 1.1)  # AU
            outer_hz = np.sqrt(luminosity / 0.53)  # AU
        else:
            inner_hz = 0
            outer_hz = 0

        # Generate spectral class
        spectral_class = self._generate_spectral_class(star_type, temperature)

        # Metallicity (younger stars are typically more metal-rich)
        if age < 5e9:
            metallicity = np.random.uniform(0.0, 0.5)  # Metal-rich
        elif age < 10e9:
            metallicity = np.random.uniform(-0.5, 0.0)  # Solar metallicity
        else:
            metallicity = np.random.uniform(-2.0, -0.5)  # Metal-poor

        # Rotation period (massive stars rotate faster)
        if star_type in [StarType.O, StarType.B]:
            rotation_period = np.random.uniform(0.5, 2)  # hours
        elif star_type in [StarType.A, StarType.F]:
            rotation_period = np.random.uniform(1, 10)  # hours
        else:
            rotation_period = np.random.uniform(25, 30) * 24  # hours (like Sun)

        # Magnetic field (depends on star type and rotation)
        if star_type in [StarType.M, StarType.K]:
            magnetic_field = np.random.uniform(0.001, 0.1)  # Tesla
        else:
            magnetic_field = np.random.uniform(1e-6, 1e-4)  # Tesla

        star = Star(
            id=star_id,
            name=f"Star-{star_id[:8]}",
            mass=mass,
            radius=radius,
            position=np.zeros(3),  # Will be set by star system
            velocity=np.zeros(3),  # Will be set by star system
            temperature=temperature,
            age=age,
            star_type=star_type,
            luminosity=luminosity,
            spectral_class=spectral_class,
            metallicity=metallicity,
            rotation_period=rotation_period,
            magnetic_field=magnetic_field,
            habitation_zone=(inner_hz, outer_hz)
        )

        return star

    def _generate_spectral_class(self, star_type: StarType, temperature: float) -> str:
        """Generate detailed spectral classification"""

        base_class = star_type.value

        # Add numerical subclass (0-9, where 0 is hottest)
        if star_type == StarType.O:
            subclass = str(int((50000 - temperature) / 2222))
        elif star_type == StarType.B:
            subclass = str(int((30000 - temperature) / 2222))
        elif star_type == StarType.A:
            subclass = str(int((10000 - temperature) / 278))
        elif star_type == StarType.F:
            subclass = str(int((7500 - temperature) / 167))
        elif star_type == StarType.G:
            subclass = str(int((6000 - temperature) / 89))
        elif star_type == StarType.K:
            subclass = str(int((5200 - temperature) / 178))
        elif star_type == StarType.M:
            subclass = str(int((3700 - temperature) / 144))
        else:
            subclass = "0"

        subclass = max(0, min(9, int(subclass)))

        # Add luminosity class
        if star_type in [StarType.BLACK_HOLE, StarType.NEUTRON_STAR, StarType.WHITE_DWARF]:
            luminosity_class = ""
        elif temperature > 20000:  # O and early B stars
            luminosity_class = random.choice(["Ia", "Ib", "II", "III", "IV", "V"])
        else:
            luminosity_class = "V"  # Main sequence

        return f"{base_class}{subclass}{luminosity_class}"

    def generate_planets(self, star: Star, system_id: str) -> List[Planet]:
        """Generate planets around a star"""

        num_planets = np.random.poisson(3)  # Average 3 planets per system

        # Adjust planet count based on star type
        if star.star_type in [StarType.O, StarType.B]:
            num_planets = max(0, num_planets - 2)  # Massive stars often have fewer planets
        elif star.star_type == StarType.M:
            num_planets = min(8, num_planets + 1)  # Red dwarfs can have many small planets

        planets = []

        for i in range(num_planets):
            planet_id = f"{system_id}-P{i+1}"
            planet = self.generate_planet(planet_id, star, i)
            planets.append(planet)

        return planets

    def generate_planet(self, planet_id: str, star: Star, orbital_index: int) -> Planet:
        """Generate a single planet"""

        # Orbital radius follows power law distribution
        min_radius = 0.3 * AU
        max_radius = 50 * AU

        # Use Titius-Bode law as a tendency
        if orbital_index == 0:
            orbital_radius = np.random.uniform(0.3, 1.5) * AU
        else:
            base_radius = 0.4 * AU * (1.3 ** orbital_index)
            scatter = np.random.normal(0, 0.2 * AU)
            orbital_radius = max(0.2 * AU, base_radius + scatter)
            orbital_radius = min(max_radius, orbital_radius)

        # Orbital period (Kepler's third law)
        orbital_period = np.sqrt((orbital_radius / AU) ** 3 / (star.mass / SOLAR_MASS))

        # Eccentricity (most planets have low eccentricity)
        eccentricity = np.random.beta(2, 10)  # Beta distribution favoring low values
        eccentricity = min(0.9, eccentricity)

        # Inclination (small for planets in same system)
        inclination = np.random.normal(0, 5)  # degrees

        # Planet type based on distance from star and star type
        planet_type = self.determine_planet_type(star, orbital_radius)

        # Planet mass and radius based on type
        if planet_type == PlanetType.TERRESTRIAL:
            mass = np.random.uniform(0.1, 3) * EARTH_MASS
            radius = np.random.uniform(0.5, 2) * EARTH_RADIUS
        elif planet_type == PlanetType.GAS_GIANT:
            mass = np.random.uniform(10, 500) * EARTH_MASS
            radius = np.random.uniform(5, 15) * EARTH_RADIUS
        elif planet_type == PlanetType.ICE_GIANT:
            mass = np.random.uniform(5, 20) * EARTH_MASS
            radius = np.random.uniform(2, 5) * EARTH_RADIUS
        elif planet_type == PlanetType.OCEAN:
            mass = np.random.uniform(0.5, 2) * EARTH_MASS
            radius = np.random.uniform(0.8, 1.5) * EARTH_RADIUS
        elif planet_type == PlanetType.DESERT:
            mass = np.random.uniform(0.3, 1.5) * EARTH_MASS
            radius = np.random.uniform(0.7, 1.2) * EARTH_RADIUS
        elif planet_type == PlanetType.LAVA:
            mass = np.random.uniform(0.5, 2) * EARTH_MASS
            radius = np.random.uniform(0.8, 1.3) * EARTH_RADIUS
        elif planet_type == PlanetType.ICE:
            mass = np.random.uniform(0.1, 0.8) * EARTH_MASS
            radius = np.random.uniform(0.5, 0.9) * EARTH_RADIUS
        elif planet_type == PlanetType.TUNDRA:
            mass = np.random.uniform(0.3, 1.2) * EARTH_MASS
            radius = np.random.uniform(0.6, 1.1) * EARTH_RADIUS
        else:  # Artificial or other
            mass = np.random.uniform(0.01, 0.1) * EARTH_MASS
            radius = np.random.uniform(0.1, 0.3) * EARTH_RADIUS

        # Temperature based on distance from star and greenhouse effect
        base_temp = star.temperature * np.sqrt(star.radius / (2 * orbital_radius))
        greenhouse_factor = np.random.uniform(1.0, 1.5)
        temperature = base_temp * greenhouse_factor

        # Atmosphere composition
        atmosphere = self.generate_atmosphere(planet_type, temperature)

        # Biosphere potential
        biosphere = self.check_habitability(star, orbital_radius, temperature, atmosphere)

        # Resources
        resources = self.generate_resources(planet_type, mass)

        # Position and velocity (will be calculated by physics engine)
        position = np.array([orbital_radius, 0, 0])
        velocity = np.zeros(3)

        # Age (younger planets are more geologically active)
        age = star.age * np.random.uniform(0.8, 1.0)

        planet = Planet(
            id=planet_id,
            name=f"Planet-{planet_id[:8]}",
            mass=mass,
            radius=radius,
            position=position,
            velocity=velocity,
            temperature=temperature,
            age=age,
            parent_id=None,  # Will be set to star system ID
            planet_type=planet_type,
            orbital_radius=orbital_radius / AU,  # Convert to AU
            orbital_period=orbital_period,
            eccentricity=eccentricity,
            inclination=inclination,
            atmosphere=atmosphere,
            biosphere=biosphere,
            resources=resources,
            moons=[]  # Will be populated later if needed
        )

        return planet

    def determine_planet_type(self, star: Star, orbital_radius: float) -> PlanetType:
        """Determine planet type based on distance from star and star properties"""

        # Temperature zones
        frost_line = 2.7 * AU * (star.luminosity ** 0.5)
        hot_zone = 0.5 * AU * (star.luminosity ** 0.5)
        warm_zone = 1.5 * AU * (star.luminosity ** 0.5)

        if orbital_radius < hot_zone:
            if random.random() < 0.3:
                return PlanetType.LAVA
            else:
                return PlanetType.DESERT
        elif orbital_radius < warm_zone:
            if random.random() < 0.4:
                return PlanetType.TERRESTRIAL
            elif random.random() < 0.3:
                return PlanetType.OCEAN
            else:
                return PlanetType.DESERT
        elif orbital_radius < frost_line:
            if random.random() < 0.3:
                return PlanetType.GAS_GIANT
            elif random.random() < 0.2:
                return PlanetType.TERRESTRIAL
            else:
                return PlanetType.OCEAN
        else:
            if random.random() < 0.4:
                return PlanetType.ICE_GIANT
            elif random.random() < 0.3:
                return PlanetType.GAS_GIANT
            else:
                return PlanetType.ICE

    def generate_atmosphere(self, planet_type: PlanetType, temperature: float) -> Dict[str, float]:
        """Generate atmospheric composition based on planet type"""

        atmosphere = {}

        if planet_type == PlanetType.TERRESTRIAL:
            if temperature < 273:  # Cold
                atmosphere = {'N2': 0.7, 'CO2': 0.2, 'Ar': 0.1}
            elif temperature > 373:  # Hot
                atmosphere = {'CO2': 0.9, 'N2': 0.1}
            else:  # Temperate
                if random.random() < 0.3:  # Earth-like
                    atmosphere = {'N2': 0.78, 'O2': 0.21, 'Ar': 0.01}
                else:
                    atmosphere = {'N2': 0.8, 'CO2': 0.15, 'Ar': 0.05}

        elif planet_type == PlanetType.OCEAN:
            atmosphere = {'N2': 0.7, 'O2': 0.25, 'CO2': 0.05}

        elif planet_type == PlanetType.GAS_GIANT:
            atmosphere = {'H2': 0.85, 'He': 0.14, 'CH4': 0.01}

        elif planet_type == PlanetType.ICE_GIANT:
            atmosphere = {'H2': 0.8, 'He': 0.15, 'CH4': 0.03, 'NH3': 0.02}

        elif planet_type == PlanetType.DESERT:
            atmosphere = {'CO2': 0.95, 'N2': 0.04, 'Ar': 0.01}

        elif planet_type == PlanetType.LAVA:
            atmosphere = {'SO2': 0.6, 'CO2': 0.3, 'N2': 0.1}

        elif planet_type == PlanetType.ICE:
            atmosphere = {'N2': 0.9, 'CH4': 0.1}

        elif planet_type == PlanetType.TUNDRA:
            atmosphere = {'N2': 0.75, 'CO2': 0.2, 'CH4': 0.05}

        return atmosphere

    def check_habitability(self, star: Star, orbital_radius: float,
                          temperature: float, atmosphere: Dict[str, float]) -> bool:
        """Check if planet can support life"""

        # Must be in habitable zone
        inner_hz, outer_hz = star.habitation_zone
        if inner_hz == 0 or outer_hz == 0:
            return False

        if orbital_radius < inner_hz * AU or orbital_radius > outer_hz * AU:
            return False

        # Temperature must be in liquid water range
        if temperature < 273 or temperature > 373:
            return False

        # Need appropriate atmosphere
        if 'O2' not in atmosphere and 'N2' not in atmosphere:
            return False

        # Random factor for complexity
        if random.random() < 0.1:  # 10% chance of life even if conditions are marginal
            return True

        return (atmosphere.get('O2', 0) > 0.1 and
                atmosphere.get('N2', 0) > 0.5 and
                temperature > 273 and temperature < 373)

    def generate_resources(self, planet_type: PlanetType, mass: float) -> Dict[str, float]:
        """Generate resource quantities based on planet type and mass"""

        resources = {}

        # Base resource quantities scale with planet mass
        mass_scale = mass / EARTH_MASS

        if planet_type == PlanetType.TERRESTRIAL:
            resources.update({
                'iron': mass_scale * np.random.uniform(0.2, 0.4),
                'silicon': mass_scale * np.random.uniform(0.15, 0.3),
                'aluminum': mass_scale * np.random.uniform(0.05, 0.15),
                'copper': mass_scale * np.random.uniform(0.001, 0.01),
                'gold': mass_scale * np.random.uniform(0.0001, 0.001),
                'uranium': mass_scale * np.random.uniform(0.0001, 0.0005),
                'water': mass_scale * np.random.uniform(0.01, 0.3),
                'organic_compounds': mass_scale * np.random.uniform(0.001, 0.01)
            })

        elif planet_type == PlanetType.GAS_GIANT:
            resources.update({
                'hydrogen': mass_scale * np.random.uniform(0.5, 0.8),
                'helium': mass_scale * np.random.uniform(0.1, 0.3),
                'methane': mass_scale * np.random.uniform(0.05, 0.15),
                'ammonia': mass_scale * np.random.uniform(0.01, 0.05),
                'rare_gases': mass_scale * np.random.uniform(0.001, 0.01)
            })

        elif planet_type == PlanetType.ICE_GIANT:
            resources.update({
                'water_ice': mass_scale * np.random.uniform(0.3, 0.6),
                'methane_ice': mass_scale * np.random.uniform(0.1, 0.3),
                'ammonia_ice': mass_scale * np.random.uniform(0.05, 0.15),
                'nitrogen': mass_scale * np.random.uniform(0.1, 0.2),
                'carbon_compounds': mass_scale * np.random.uniform(0.01, 0.05)
            })

        elif planet_type == PlanetType.OCEAN:
            resources.update({
                'water': mass_scale * np.random.uniform(0.7, 0.9),
                'salts': mass_scale * np.random.uniform(0.01, 0.05),
                'minerals': mass_scale * np.random.uniform(0.05, 0.15),
                'organic_compounds': mass_scale * np.random.uniform(0.01, 0.1)
            })

        elif planet_type == PlanetType.DESERT:
            resources.update({
                'silicon': mass_scale * np.random.uniform(0.3, 0.5),
                'iron': mass_scale * np.random.uniform(0.1, 0.3),
                'aluminum': mass_scale * np.random.uniform(0.05, 0.15),
                'rare_earths': mass_scale * np.random.uniform(0.01, 0.05)
            })

        elif planet_type == PlanetType.ICE:
            resources.update({
                'water_ice': mass_scale * np.random.uniform(0.6, 0.8),
                'carbon_dioxide_ice': mass_scale * np.random.uniform(0.1, 0.2),
                'methane_ice': mass_scale * np.random.uniform(0.05, 0.15)
            })

        # Add rare resources to all planets occasionally
        if random.random() < 0.05:  # 5% chance
            resources['exotic_matter'] = mass_scale * np.random.uniform(0.0001, 0.001)

        if random.random() < 0.1:  # 10% chance
            resources['quantum_crystals'] = mass_scale * np.random.uniform(0.00001, 0.0001)

        return resources

    def generate_star_system(self, system_id: str, position: np.ndarray) -> StarSystem:
        """Generate a complete star system"""

        # System age (most systems are 1-10 billion years old)
        age = np.random.lognormal(mean=np.log(5e9), sigma=0.5)  # years
        age = max(1e8, min(13.8e9, age))  # Clamp to realistic range

        # System metallicity
        if age < 5e9:
            metallicity = np.random.uniform(0.0, 0.5)
        else:
            metallicity = np.random.uniform(-1.0, 0.0)

        # Generate primary star
        star_id = f"{system_id}-STAR"
        primary_star = self.generate_star(star_id, age)
        primary_star.position = position

        # Generate planets
        planets = self.generate_planets(primary_star, system_id)

        # Set parent references
        for planet in planets:
            planet.parent_id = system_id

        # Generate asteroid belts (if applicable)
        asteroids = self.generate_asteroids(system_id, primary_star)

        # Generate comets
        comets = self.generate_comets(system_id, primary_star)

        # Generate any existing space stations (rare)
        space_stations = self.generate_space_stations(system_id, planets)

        # Generate debris fields
        debris_fields = []
        if random.random() < 0.1:  # 10% chance of debris field
            debris_fields.append(self.generate_debris_field())

        star_system = StarSystem(
            id=system_id,
            primary_star=primary_star,
            planets=planets,
            asteroids=asteroids,
            comets=comets,
            space_stations=space_stations,
            debris_fields=debris_fields,
            age=age,
            metallicity=metallicity
        )

        return star_system

    def generate_asteroids(self, system_id: str, star: Star) -> List[CelestialBody]:
        """Generate asteroid belts"""

        asteroids = []

        # Most systems have 1-2 asteroid belts
        num_belts = np.random.poisson(1.2)

        for belt_index in range(num_belts):
            # Asteroid belts typically form between 2-4 AU for sun-like stars
            belt_radius = np.random.uniform(2, 4) * AU * (star.luminosity ** 0.5)

            # Generate asteroids in this belt
            num_asteroids = np.random.randint(50, 500)

            for i in range(num_asteroids):
                asteroid_id = f"{system_id}-AST{belt_index}-{i}"

                # Random position within belt
                angle = np.random.uniform(0, 2 * np.pi)
                radius_offset = np.random.normal(0, 0.1 * AU)
                r = belt_radius + radius_offset

                position = np.array([
                    r * np.cos(angle),
                    r * np.sin(angle),
                    np.random.normal(0, 0.01 * AU)
                ])

                # Asteroid properties
                mass = np.random.uniform(1e15, 1e19)  # kg
                radius = np.random.uniform(1e3, 1e5)  # meters

                asteroid = CelestialBody(
                    id=asteroid_id,
                    name=f"Asteroid-{asteroid_id[:8]}",
                    mass=mass,
                    radius=radius,
                    position=position,
                    velocity=np.zeros(3),
                    temperature=200,  # Cold
                    age=star.age,
                    parent_id=system_id
                )

                asteroids.append(asteroid)

        return asteroids

    def generate_comets(self, system_id: str, star: Star) -> List[CelestialBody]:
        """Generate comets in Oort cloud and Kuiper belt equivalents"""

        comets = []

        # Oort cloud equivalent (very distant)
        num_oort_comets = np.random.randint(100, 1000)
        oort_radius = np.random.uniform(1000, 10000) * AU * (star.luminosity ** 0.5)

        for i in range(num_oort_comets):
            comet_id = f"{system_id}-COM-OORT-{i}"

            # Random spherical distribution
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)
            r = oort_radius * np.random.uniform(0.8, 1.2)

            position = star.position + np.array([
                r * np.sin(phi) * np.cos(theta),
                r * np.sin(phi) * np.sin(theta),
                r * np.cos(phi)
            ])

            # Comet properties
            mass = np.random.uniform(1e13, 1e16)  # kg
            radius = np.random.uniform(1e3, 5e4)  # meters

            comet = CelestialBody(
                id=comet_id,
                name=f"Comet-{comet_id[:8]}",
                mass=mass,
                radius=radius,
                position=position,
                velocity=np.zeros(3),
                temperature=30,  # Very cold
                age=star.age,
                parent_id=system_id
            )

            comets.append(comet)

        return comets

    def generate_space_stations(self, system_id: str, planets: List[Planet]) -> List[CelestialBody]:
        """Generate existing space stations (very rare in unexplored systems)"""

        stations = []

        # Only 1% of systems have existing stations
        if random.random() > 0.01:
            return stations

        # Stations are usually near habitable planets
        habitable_planets = [p for p in planets if p.biosphere]

        if not habitable_planets:
            return stations

        # Generate 1-3 stations
        num_stations = np.random.randint(1, 4)

        for i in range(min(num_stations, len(habitable_planets))):
            planet = random.choice(habitable_planets)
            station_id = f"{system_id}-STATION-{i}"

            # Station orbits planet
            orbit_radius = planet.radius + np.random.uniform(100e3, 1000e3)  # 100-1000 km above surface

            angle = np.random.uniform(0, 2 * np.pi)
            position = planet.position + np.array([
                orbit_radius * np.cos(angle),
                orbit_radius * np.sin(angle),
                0
            ])

            # Station properties
            mass = np.random.uniform(1e9, 1e12)  # kg
            radius = np.random.uniform(100, 1000)  # meters

            station = CelestialBody(
                id=station_id,
                name=f"Station-{station_id[:8]}",
                mass=mass,
                radius=radius,
                position=position,
                velocity=np.zeros(3),
                temperature=293,  # Room temperature
                age=np.random.uniform(1, 1000),  # Years old
                parent_id=system_id
            )

            stations.append(station)

        return stations

    def generate_debris_field(self) -> Dict:
        """Generate a debris field (remnants of destroyed ships or structures)"""

        debris_field = {
            'type': random.choice(['ship_wreckage', 'station_debris', 'battle_debris']),
            'age': np.random.uniform(1, 1000),  # years
            'composition': {
                'metal': np.random.uniform(0.3, 0.7),
                'organic': np.random.uniform(0.1, 0.3),
                'energy_signature': np.random.uniform(0.0, 0.2)
            },
            'hazard_level': np.random.uniform(0.1, 0.9),
            'recoverable_materials': np.random.uniform(0.1, 0.5),
            'dangerous_radiation': np.random.random() < 0.3
        }

        return debris_field

    def generate_universe(self, num_galaxies: int = 100) -> Dict[str, Galaxy]:
        """Generate a universe with multiple galaxies"""

        universe = {}

        for i in range(num_galaxies):
            galaxy_id = f"GALAXY-{i:04d}"

            # Galaxy position in universe
            position = np.array([
                np.random.uniform(-1e9, 1e9) * PARSEC,
                np.random.uniform(-1e9, 1e9) * PARSEC,
                np.random.uniform(-0.5e9, 0.5e9) * PARSEC
            ])

            galaxy = self.generate_galaxy(galaxy_id, position)
            universe[galaxy_id] = galaxy

        return universe

    def populate_galaxy(self, galaxy: Galaxy, num_systems: Optional[int] = None) -> None:
        """Populate a galaxy with star systems"""

        if num_systems is None:
            num_systems = min(galaxy.star_count, 10000)  # Limit for performance

        for i in range(num_systems):
            system_id = f"{galaxy.id}-SYS-{i:06d}"
            position = self.generate_star_system_position(galaxy)

            star_system = self.generate_star_system(system_id, position)
            galaxy.star_systems[system_id] = star_system

    def save_universe(self, universe: Dict[str, Galaxy], filename: str) -> None:
        """Save universe to file"""

        universe_data = {}
        for galaxy_id, galaxy in universe.items():
            galaxy_dict = asdict(galaxy)

            # Convert star systems to dictionary
            star_systems_dict = {}
            for system_id, system in galaxy.star_systems.items():
                system_dict = asdict(system)

                # Convert numpy arrays to lists
                system_dict['primary_star']['position'] = system.primary_star.position.tolist()
                system_dict['primary_star']['velocity'] = system.primary_star.velocity.tolist()

                # Convert planets
                planets_dict = []
                for planet in system.planets:
                    planet_dict = asdict(planet)
                    planet_dict['position'] = planet.position.tolist()
                    planet_dict['velocity'] = planet.velocity.tolist()
                    planets_dict.append(planet_dict)
                system_dict['planets'] = planets_dict

                # Convert asteroids
                asteroids_dict = []
                for asteroid in system.asteroids:
                    asteroid_dict = asdict(asteroid)
                    asteroid_dict['position'] = asteroid.position.tolist()
                    asteroid_dict['velocity'] = asteroid.velocity.tolist()
                    asteroids_dict.append(asteroid_dict)
                system_dict['asteroids'] = asteroids_dict

                # Convert comets
                comets_dict = []
                for comet in system.comets:
                    comet_dict = asdict(comet)
                    comet_dict['position'] = comet.position.tolist()
                    comet_dict['velocity'] = comet.velocity.tolist()
                    comets_dict.append(comet_dict)
                system_dict['comets'] = comets_dict

                # Convert space stations
                stations_dict = []
                for station in system.space_stations:
                    station_dict = asdict(station)
                    station_dict['position'] = station.position.tolist()
                    station_dict['velocity'] = station.velocity.tolist()
                    stations_dict.append(station_dict)
                system_dict['space_stations'] = stations_dict

                star_systems_dict[system_id] = system_dict

            galaxy_dict['star_systems'] = star_systems_dict
            galaxy_dict['center_position'] = galaxy.center_position.tolist()

            universe_data[galaxy_id] = galaxy_dict

        with open(filename, 'w') as f:
            json.dump(universe_data, f, indent=2)

    def generate_seed_from_string(self, seed_string: str) -> int:
        """Generate a numerical seed from a string"""
        return int(hashlib.sha256(seed_string.encode()).hexdigest()[:8], 16)

# Example usage and testing
if __name__ == "__main__":
    # Create universe generator
    generator = UniverseGenerator(seed=42)

    # Generate a small universe for testing
    print("Generating universe...")
    universe = generator.generate_universe(num_galaxies=5)

    # Populate first galaxy with some systems
    first_galaxy = list(universe.values())[0]
    print(f"Populating galaxy {first_galaxy.name}...")
    generator.populate_galaxy(first_galaxy, num_systems=100)

    # Print statistics
    total_systems = sum(len(galaxy.star_systems) for galaxy in universe.values())
    total_planets = sum(len(system.planets) for galaxy in universe.values() for system in galaxy.star_systems.values())

    print(f"\nUniverse Statistics:")
    print(f"Galaxies: {len(universe)}")
    print(f"Star Systems: {total_systems}")
    print(f"Planets: {total_planets}")

    # Save universe
    generator.save_universe(universe, '/home/activeloguser/DMLogn8n/cosmos/universe/test_universe.json')
    print(f"\nUniverse saved to test_universe.json")

    # Example star system details
    if first_galaxy.star_systems:
        sample_system = list(first_galaxy.star_systems.values())[0]
        print(f"\nSample Star System: {sample_system.id}")
        print(f"Star Type: {sample_system.primary_star.star_type}")
        print(f"Star Mass: {sample_system.primary_star.mass / SOLAR_MASS:.2f} solar masses")
        print(f"Number of Planets: {len(sample_system.planets)}")
        print(f"System Age: {sample_system.age / 1e9:.2f} billion years")

        if sample_system.planets:
            sample_planet = sample_system.planets[0]
            print(f"\nSample Planet: {sample_planet.name}")
            print(f"Type: {sample_planet.plan_type}")
            print(f"Mass: {sample_planet.mass / EARTH_MASS:.2f} Earth masses")
            print(f"Orbital Radius: {sample_planet.orbital_radius:.2f} AU")
            print(f"Temperature: {sample_planet.temperature:.1f} K")
            print(f"Has Biosphere: {sample_planet.biosphere}")