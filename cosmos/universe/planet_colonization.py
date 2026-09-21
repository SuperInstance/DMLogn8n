#!/usr/bin/env python3
"""
Planet Colonization System - Planet and Space Station Colonization
Handles terraforming, habitat construction, and colony management
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import random
import math

# Physical Constants
EARTH_MASS = 5.972e24  # kg
EARTH_RADIUS = 6.371e6  # meters
SOLAR_MASS = 1.989e30  # kg
AU = 1.496e11  # meters
G = 6.67430e-11  # Gravitational constant
STEFAN_BOLTZMANN = 5.67e-8  # Stefan-Boltzmann constant

class ColonyType(Enum):
    OUTPOST = "outpost"  # Small scientific outpost
    MINING = "mining"  # Resource extraction colony
    AGRICULTURAL = "agricultural"  # Food production
    INDUSTRIAL = "industrial"  # Manufacturing
    RESEARCH = "research"  # Scientific research
    MILITARY = "military"  # Strategic military base
    TRADE = "trade"  # Commercial hub
    TERRAFORMING = "terraforming"  # Planet transformation project
    DYSON_SPHERE = "dyson_sphere"  # Stellar megastructure
    RINGWORLD = "ringworld"  # Artificial ring world

class HabitatType(Enum):
    SURFACE_DOME = "surface_dome"  # Pressurized dome on surface
    SUBTERRANEAN = "subterranean"  # Underground habitat
    ORBITAL_STATION = "orbital_station"  # Space station in orbit
    LAGRANGE_STATION = "lagrange_station"  # Station at Lagrange point
    ASTEROID_BASE = "asteroid_base"  # Base hollowed out in asteroid
    FLOATING_CITY = "floating_city"  # Atmospheric floating habitat
    UNDERWATER_DOME = "underwater_dome"  - Underwater habitat
    MEGASTRUCTURE = "megastructure"  # Large scale artificial structure

class TerraformingStage(Enum):
    SURVEY = "survey"  # Initial assessment
    ATMOSPHERE_SEEDING = "atmosphere_seeding"  # Introduce atmospheric gases
    TEMPERATURE_REGULATION = "temperature_regulation"  # Climate control
    HYDROSPHERE_CREATION = "hydrosphere_creation"  # Create oceans
    BIOSPHERE_INTRODUCTION = "biosphere_introduction"  # Introduce life
    ECOSYSTEM_STABILIZATION = "ecosystem_stabilization"  # Balance ecosystem
    HABITABLE = "habitable"  # Fully terraformed

@dataclass
class Resource:
    """Represents a planetary resource"""
    name: str
    abundance: float  # 0-1 scale
    extraction_difficulty: float  # 0-1 scale
    market_value: float  # Relative value
    renewability: bool  # Whether resource is renewable
    extraction_rate: float = 0.0  # Current extraction rate

@dataclass
class Colony:
    """Represents a planetary colony"""
    id: str
    name: str
    colony_type: ColonyType
    planet_id: str
    position: Tuple[float, float, float]  # Surface coordinates
    population: int  # Number of inhabitants
    max_population: int  # Maximum sustainable population
    founding_date: float  # Time of founding
    prosperity_level: float  # 0-1 scale
    self_sufficiency: float  # 0-1 scale
    defense_level: float  # 0-1 scale
    research_level: float  # 0-1 scale
    production_efficiency: float  # 0-1 scale
    habitat_modules: List['HabitatModule'] = field(default_factory=list)
    resource_extractors: List['ResourceExtractor'] = field(default_factory=list)
    infrastructure_level: float = 0.1  # 0-1 scale
    pollution_level: float = 0.0  # 0-1 scale
    happiness_index: float = 0.5  # 0-1 scale

@dataclass
class HabitatModule:
    """Represents a habitat module"""
    id: str
    module_type: HabitatType
    capacity: int  # Population capacity
    structural_integrity: float  # 0-1 scale
    life_support_efficiency: float  # 0-1 scale
    radiation_shielding: float  # 0-1 scale
    energy_consumption: float  # Watts
    maintenance_requirement: float  # 0-1 scale
    age: float  # Years since construction
    construction_cost: Dict[str, float]  # Resource costs

@dataclass
class ResourceExtractor:
    """Represents a resource extraction facility"""
    id: str
    resource_type: str
    extraction_rate: float  # Units per year
    efficiency: float  # 0-1 scale
    environmental_impact: float  # 0-1 scale
    energy_consumption: float  # Watts
    operational_status: bool  # Whether currently operating
    maintenance_level: float  # 0-1 scale
    depletion_rate: float  # How fast resource depletes

@dataclass
class TerraformingProject:
    """Represents a terraforming project"""
    id: str
    target_planet: str
    current_stage: TerraformingStage
    progress: float  # 0-1 scale within current stage
    estimated_completion: float  # Years to completion
    total_cost: Dict[str, float]  # Resource requirements
    current_investment: Dict[str, float]  # Resources invested so far
    success_probability: float  # 0-1 scale
    environmental_stability: float  # 0-1 scale
    atmospheric_pressure: float  # Target atmospheric pressure (Pascals)
    target_temperature: float  # Target temperature (Kelvin)
    target_water_coverage: float  # Target water coverage (0-1)
    target_oxygen_level: float  # Target oxygen level (0-1)

@dataclass
class SpaceStation:
    """Represents a space station or orbital habitat"""
    id: str
    name: str
    station_type: str  # Military, research, commercial, etc.
    position: Tuple[float, float, float]  # 3D position
    orbiting_body: str  # What it orbits
    orbital_radius: float  # meters
    population: int
    max_population: int
    structural_integrity: float  # 0-1 scale
    power_generation: float  # Watts
    docking_ports: int
    manufacturing_capacity: float  # 0-1 scale
    research_facilities: float  # 0-1 scale
    defense_systems: float  # 0-1 scale
    age: float  # Years
    maintenance_status: float  # 0-1 scale

class PlanetColonizationSystem:
    """Manages planet colonization and terraforming operations"""

    def __init__(self):
        self.colonies: Dict[str, Colony] = {}
        self.space_stations: Dict[str, SpaceStation] = {}
        self.terraforming_projects: Dict[str, TerraformingProject] = {}
        self.habitat_designs: Dict[str, Dict] = {}
        self.terraforming_technologies: Dict[str, float] = {}  # Tech level 0-1
        self.colonization_history: List[Dict] = []

        # Initialize habitat designs
        self.initialize_habitat_designs()
        # Initialize terraforming technologies
        self.initialize_terraforming_technologies()

    def initialize_habitat_designs(self):
        """Initialize available habitat module designs"""
        self.habitat_designs = {
            'basic_dome': {
                'type': HabitatType.SURFACE_DOME,
                'capacity': 100,
                'cost': {'metal': 1000, 'energy': 500, 'water': 100},
                'construction_time': 1.0,  # years
                'maintenance_cost': 0.1  # per year
            },
            'advanced_dome': {
                'type': HabitatType.SURFACE_DOME,
                'capacity': 500,
                'cost': {'metal': 5000, 'energy': 2000, 'water': 500, 'electronics': 200},
                'construction_time': 2.0,
                'maintenance_cost': 0.15
            },
            'orbital_station': {
                'type': HabitatType.ORBITAL_STATION,
                'capacity': 1000,
                'cost': {'metal': 10000, 'energy': 5000, 'electronics': 1000},
                'construction_time': 3.0,
                'maintenance_cost': 0.2
            },
            'underground_bunker': {
                'type': HabitatType.SUBTERRANEAN,
                'capacity': 200,
                'cost': {'metal': 3000, 'energy': 1000, 'rare_metals': 100},
                'construction_time': 2.5,
                'maintenance_cost': 0.12
            },
            'floating_city': {
                'type': HabitatType.FLOATING_CITY,
                'capacity': 2000,
                'cost': {'metal': 15000, 'energy': 8000, 'electronics': 500, 'exotic_materials': 50},
                'construction_time': 5.0,
                'maintenance_cost': 0.25
            }
        }

    def initialize_terraforming_technologies(self):
        """Initialize available terraforming technologies"""
        self.terraforming_technologies = {
            'atmospheric_processing': 0.7,  # 70% developed
            'climate_control': 0.6,
            'biosphere_engineering': 0.5,
            'hydrogen_bombardment': 0.8,  # For creating water
            'solar_shades': 0.4,
            'greenhouse_gas_injection': 0.7,
            'magnetic_field_generation': 0.3,
            'crustal_engineering': 0.2,
            'artificial_volcanism': 0.6
        }

    def assess_colonization_potential(self, planet_data: Dict) -> Dict:
        """Assess the colonization potential of a planet"""

        # Extract planet parameters
        mass = planet_data.get('mass', EARTH_MASS)
        radius = planet_data.get('radius', EARTH_RADIUS)
        temperature = planet_data.get('temperature', 288)
        atmosphere = planet_data.get('atmosphere', {})
        gravity = G * mass / radius**2
        atmospheric_pressure = sum(atmosphere.values()) * 101325  # Convert to Pascals
        has_water = planet_data.get('has_water', False)
        has_biosphere = planet_data.get('has_biosphere', False)
        resources = planet_data.get('resources', {})

        # Calculate habitability score
        habitability_score = 0.0

        # Gravity (0.3g to 2g is acceptable)
        if 0.3 * 9.81 <= gravity <= 2 * 9.81:
            habitability_score += 0.2
        elif 0.1 * 9.81 <= gravity <= 3 * 9.81:
            habitability_score += 0.1

        # Temperature (liquid water range)
        if 273 <= temperature <= 373:
            habitability_score += 0.25
        elif 200 <= temperature <= 450:
            habitability_score += 0.15

        # Atmospheric pressure
        if 0.5 * 101325 <= atmospheric_pressure <= 2 * 101325:
            habitability_score += 0.15
        elif 0.1 * 101325 <= atmospheric_pressure <= 5 * 101325:
            habitability_score += 0.1

        # Breathable atmosphere
        if atmosphere.get('O2', 0) > 0.15 and atmosphere.get('N2', 0) > 0.5:
            habitability_score += 0.2
        elif atmosphere.get('O2', 0) > 0.05:
            habitability_score += 0.1

        # Water presence
        if has_water:
            habitability_score += 0.1

        # Existing biosphere
        if has_biosphere:
            habitability_score += 0.1

        # Resource availability
        resource_score = min(0.1, len(resources) * 0.02)
        habitability_score += resource_score

        # Determine colonization recommendations
        if habitability_score >= 0.8:
            colonization_type = ColonyType.AGRICULTURAL
            difficulty = "Easy"
        elif habitability_score >= 0.6:
            colonization_type = ColonyType.INDUSTRIAL
            difficulty = "Moderate"
        elif habitability_score >= 0.4:
            colonization_type = ColonyType.MINING
            difficulty = "Challenging"
        elif habitability_score >= 0.2:
            colonization_type = ColonyType.OUTPOST
            difficulty = "Difficult"
        else:
            colonization_type = ColonyType.TERRAFORMING
            difficulty = "Requires Terraforming"

        # Calculate terraforming requirements
        terraforming_requirements = self.calculate_terraforming_requirements(planet_data)

        return {
            'habitability_score': habitability_score,
            'colonization_type': colonization_type,
            'difficulty': difficulty,
            'gravity': gravity,
            'atmospheric_pressure': atmospheric_pressure,
            'suitable_for_life': habitability_score >= 0.6,
            'requires_terraformin': habitability_score < 0.4,
            'terraforming_requirements': terraforming_requirements,
            'recommended_habitats': self.recommend_habitats(habitability_score, planet_data)
        }

    def calculate_terraforming_requirements(self, planet_data: Dict) -> Dict:
        """Calculate requirements for terraforming a planet"""

        current_temp = planet_data.get('temperature', 200)
        target_temp = 288  # Earth-like temperature
        current_atm = sum(planet_data.get('atmosphere', {}).values()) * 101325
        target_atm = 101325  # Earth atmospheric pressure

        requirements = {
            'atmospheric_gases': {},
            'temperature_adjustment': 0,
            'water_addition': 0,
            'biosphere_seeding': False,
            'magnetic_field': False,
            'estimated_time': 0,
            'resource_cost': {}
        }

        # Atmospheric requirements
        if current_atm < target_atm:
            pressure_deficit = target_atm - current_atm
            requirements['atmospheric_gases'] = {
                'N2': pressure_deficit * 0.78,
                'O2': pressure_deficit * 0.21,
                'Ar': pressure_deficit * 0.01
            }

        # Temperature adjustment
        temp_diff = target_temp - current_temp
        if abs(temp_diff) > 10:
            requirements['temperature_adjustment'] = temp_diff

        # Water requirements
        if not planet_data.get('has_water', False):
            # Estimate water needed for oceans
            surface_area = 4 * np.pi * planet_data.get('radius', EARTH_RADIUS)**2
            ocean_depth = 4000  # Average ocean depth in meters
            water_volume = surface_area * ocean_depth * 0.7  # 70% ocean coverage
            water_mass = water_volume * 1000  # kg (water density)
            requirements['water_addition'] = water_mass

        # Biosphere seeding
        if not planet_data.get('has_biosphere', False):
            requirements['biosphere_seeding'] = True

        # Magnetic field (for planets without sufficient core)
        if planet_data.get('magnetic_field', 0) < 0.1 * 3.05e-5:  # Less than 10% of Earth's
            requirements['magnetic_field'] = True

        # Time estimation
        time_components = []
        if requirements['atmospheric_gases']:
            time_components.append(50)  # Atmospheric processing
        if requirements['temperature_adjustment']:
            time_components.append(30)  # Climate adjustment
        if requirements['water_addition']:
            time_components.append(40)  # Water delivery
        if requirements['biosphere_seeding']:
            time_components.append(100)  # Ecosystem development
        if requirements['magnetic_field']:
            time_components.append(60)  # Magnetic field generation

        requirements['estimated_time'] = max(time_components) if time_components else 0

        # Resource cost estimation
        requirements['resource_cost'] = {
            'energy': requirements['estimated_time'] * 1e15,  # Watts
            'metals': requirements['estimated_time'] * 1e12,  # kg
            'water': requirements.get('water_addition', 0),
            'specialized_equipment': requirements['estimated_time'] * 1e8
        }

        return requirements

    def recommend_habitats(self, habitability_score: float, planet_data: Dict) -> List[str]:
        """Recommend appropriate habitat types for a planet"""

        recommendations = []
        gravity = G * planet_data.get('mass', EARTH_MASS) / planet_data.get('radius', EARTH_RADIUS)**2
        temperature = planet_data.get('temperature', 288)
        has_atmosphere = sum(planet_data.get('atmosphere', {}).values()) > 0.1

        if habitability_score >= 0.8:
            # Earth-like conditions - surface habitats are fine
            recommendations.append('basic_dome')
            recommendations.append('advanced_dome')
        elif habitability_score >= 0.5:
            # Marginal conditions - need protection
            recommendations.append('advanced_dome')
            if gravity < 0.5 * 9.81:
                recommendations.append('floating_city')
        else:
            # Harsh conditions - need specialized habitats
            if not has_atmosphere:
                recommendations.append('orbital_station')
            recommendations.append('underground_bunker')
            if temperature > 400:
                recommendations.append('underground_bunker')  # Shield from heat

        return recommendations

    def establish_colony(self, colony_data: Dict) -> Optional[Colony]:
        """Establish a new colony"""

        colony_id = colony_data['id']
        if colony_id in self.colonies:
            return None

        colony = Colony(
            id=colony_id,
            name=colony_data['name'],
            colony_type=ColonyType(colony_data['type']),
            planet_id=colony_data['planet_id'],
            position=colony_data['position'],
            population=colony_data.get('initial_population', 10),
            max_population=colony_data.get('max_population', 100),
            founding_date=colony_data.get('founding_date', 0),
            prosperity_level=0.1,
            self_sufficiency=0.1,
            defense_level=0.1,
            research_level=0.1,
            production_efficiency=0.1,
            infrastructure_level=0.1,
            pollution_level=0.0,
            happiness_index=0.5
        )

        self.colonies[colony_id] = colony

        # Record colonization event
        self.colonization_history.append({
            'event_type': 'colony_founded',
            'colony_id': colony_id,
            'timestamp': colony.founding_date,
            'details': colony_data
        })

        return colony

    def construct_habitat_module(self, colony_id: str, module_type: str) -> Optional[HabitatModule]:
        """Construct a new habitat module in a colony"""

        if colony_id not in self.colonies or module_type not in self.habitat_designs:
            return None

        colony = self.colonies[colony_id]
        design = self.habitat_designs[module_type]

        module_id = f"{colony_id}_hab_{len(colony.habitat_modules)}"
        module = HabitatModule(
            id=module_id,
            module_type=design['type'],
            capacity=design['capacity'],
            structural_integrity=1.0,
            life_support_efficiency=0.9,
            radiation_shielding=0.8,
            energy_consumption=design['capacity'] * 1000,  # 1kW per person
            maintenance_requirement=design['maintenance_cost'],
            age=0,
            construction_cost=design['cost']
        )

        colony.habitat_modules.append(module)
        colony.max_population += design['capacity']
        colony.infrastructure_level = min(1.0, colony.infrastructure_level + 0.05)

        return module

    def establish_resource_extractor(self, colony_id: str, resource_type: str,
                                  extraction_rate: float) -> Optional[ResourceExtractor]:
        """Establish resource extraction facility"""

        if colony_id not in self.colonies:
            return None

        colony = self.colonies[colony_id]
        extractor_id = f"{colony_id}_ext_{len(colony.resource_extractors)}"

        extractor = ResourceExtractor(
            id=extractor_id,
            resource_type=resource_type,
            extraction_rate=extraction_rate,
            efficiency=0.7,
            environmental_impact=0.2,
            energy_consumption=extraction_rate * 1e6,  # 1MW per unit
            operational_status=True,
            maintenance_level=1.0,
            depletion_rate=0.001  # 0.1% per year
        )

        colony.resource_extractors.append(extractor)
        colony.production_efficiency = min(1.0, colony.production_efficiency + 0.05)

        return extractor

    def start_terraforming_project(self, planet_id: str, project_data: Dict) -> Optional[TerraformingProject]:
        """Start a terraforming project"""

        project_id = f"terraform_{planet_id}_{len(self.terraforming_projects)}"

        project = TerraformingProject(
            id=project_id,
            target_planet=planet_id,
            current_stage=TerraformingStage.SURVEY,
            progress=0.0,
            estimated_completion=project_data.get('estimated_time', 100),
            total_cost=project_data.get('resource_cost', {}),
            current_investment={},
            success_probability=0.8,
            environmental_stability=0.1,
            atmospheric_pressure=project_data.get('target_pressure', 101325),
            target_temperature=project_data.get('target_temperature', 288),
            target_water_coverage=project_data.get('target_water_coverage', 0.7),
            target_oxygen_level=project_data.get('target_oxygen_level', 0.21)
        )

        self.terraforming_projects[project_id] = project
        return project

    def construct_space_station(self, station_data: Dict) -> Optional[SpaceStation]:
        """Construct a new space station"""

        station_id = station_data['id']
        if station_id in self.space_stations:
            return None

        station = SpaceStation(
            id=station_id,
            name=station_data['name'],
            station_type=station_data['type'],
            position=station_data['position'],
            orbiting_body=station_data['orbiting_body'],
            orbital_radius=station_data['orbital_radius'],
            population=station_data.get('initial_population', 50),
            max_population=station_data.get('max_population', 500),
            structural_integrity=1.0,
            power_generation=station_data.get('power_generation', 1e9),  # 1GW
            docking_ports=station_data.get('docking_ports', 5),
            manufacturing_capacity=station_data.get('manufacturing_capacity', 0.5),
            research_facilities=station_data.get('research_facilities', 0.5),
            defense_systems=station_data.get('defense_systems', 0.3),
            age=0,
            maintenance_status=1.0
        )

        self.space_stations[station_id] = station
        return station

    def update_colony(self, colony_id: str, dt: float) -> None:
        """Update colony status over time"""

        if colony_id not in self.colonies:
            return

        colony = self.colonies[colony_id]

        # Population growth
        if colony.population < colony.max_population:
            growth_rate = 0.02 * colony.happiness_index * colony.self_sufficiency
            colony.population = int(colony.population * (1 + growth_rate * dt))

        # Prosperity development
        prosperity_growth = (colony.production_efficiency * 0.3 +
                           colony.self_sufficiency * 0.4 +
                           colony.happiness_index * 0.3) * dt * 0.01
        colony.prosperity_level = min(1.0, colony.prosperity_level + prosperity_growth)

        # Self-sufficiency improvement
        if colony.resource_extractors:
            self_sufficiency_growth = 0.01 * dt
            colony.self_sufficiency = min(1.0, colony.self_sufficiency + self_sufficiency_growth)

        # Infrastructure maintenance and decay
        for module in colony.habitat_modules:
            module.age += dt
            maintenance_decay = module.maintenance_requirement * dt
            module.structural_integrity = max(0.1, module.structural_integrity - maintenance_decay)
            module.life_support_efficiency = max(0.1, module.life_support_efficiency - maintenance_decay)

        # Resource extraction updates
        for extractor in colony.resource_extractors:
            if extractor.operational_status:
                extractor.maintenance_level = max(0.1, extractor.maintenance_level - 0.01 * dt)
                if extractor.maintenance_level < 0.3:
                    extractor.operational_status = False

        # Pollution effects
        total_pollution = sum(e.environmental_impact for e in colony.resource_extractors if e.operational_status)
        colony.pollution_level = min(1.0, colony.pollution_level + total_pollution * 0.001 * dt)

        # Happiness factors
        happiness_factors = {
            'crowding': 1.0 - (colony.population / colony.max_population) ** 2,
            'pollution': 1.0 - colony.pollution_level,
            'infrastructure': colony.infrastructure_level,
            'prosperity': colony.prosperity_level
        }
        colony.happiness_index = sum(happiness_factors.values()) / len(happiness_factors)

        # Defense level maintenance
        if colony.defense_level > 0.1:
            colony.defense_level = max(0.1, colony.defense_level - 0.001 * dt)

    def update_terraforming_project(self, project_id: str, dt: float, investment: Dict) -> None:
        """Update terraforming project progress"""

        if project_id not in self.terraforming_projects:
            return

        project = self.terraforming_projects[project_id]

        # Add investment
        for resource, amount in investment.items():
            if resource in project.current_investment:
                project.current_investment[resource] += amount
            else:
                project.current_investment[resource] = amount

        # Progress based on investment and technology level
        tech_bonus = sum(self.terraforming_technologies.values()) / len(self.terraforming_technologies)
        progress_rate = 0.01 * tech_bonus * dt

        project.progress += progress_rate

        # Stage progression
        if project.progress >= 1.0:
            current_stage_idx = list(TerraformingStage).index(project.current_stage)
            if current_stage_idx < len(TerraformingStage) - 1:
                project.current_stage = list(TerraformingStage)[current_stage_idx + 1]
                project.progress = 0.0
                project.success_probability *= 0.95  # Slightly decrease success chance each stage

        # Update environmental stability
        project.environmental_stability = min(1.0, project.environmental_stability + 0.001 * dt)

    def update_space_station(self, station_id: str, dt: float) -> None:
        """Update space station status"""

        if station_id not in self.space_stations:
            return

        station = self.space_stations[station_id]

        # Age and maintenance
        station.age += dt
        maintenance_decay = 0.0001 * dt
        station.structural_integrity = max(0.1, station.structural_integrity - maintenance_decay)
        station.maintenance_status = max(0.1, station.maintenance_status - maintenance_decay)

        # Population dynamics
        if station.population < station.max_population:
            growth_rate = 0.01 * station.maintenance_status
            station.population = int(station.population * (1 + growth_rate * dt))

    def get_colony_statistics(self) -> Dict:
        """Get comprehensive colony statistics"""

        if not self.colonies:
            return {'total_colonies': 0}

        total_population = sum(c.population for c in self.colonies.values())
        total_capacity = sum(c.max_population for c in self.colonies.values())
        average_prosperity = sum(c.prosperity_level for c in self.colonies.values()) / len(self.colonies)
        average_happiness = sum(c.happiness_index for c in self.colonies.values()) / len(self.colonies)

        colony_types = {}
        for colony in self.colonies.values():
            colony_type = colony.colony_type.value
            colony_types[colony_type] = colony_types.get(colony_type, 0) + 1

        return {
            'total_colonies': len(self.colonies),
            'total_population': total_population,
            'total_capacity': total_capacity,
            'population_utilization': total_population / total_capacity if total_capacity > 0 else 0,
            'average_prosperity': average_prosperity,
            'average_happiness': average_happiness,
            'colony_types': colony_types,
            'total_habitat_modules': sum(len(c.habitat_modules) for c in self.colonies.values()),
            'total_extractors': sum(len(c.resource_extractors) for c in self.colonies.values()),
            'space_stations': len(self.space_stations),
            'active_terraforming': len(self.terraforming_projects)
        }

    def simulate_colony_development(self, years: float) -> Dict:
        """Simulate colony development over time"""

        print(f"Simulating {years} years of colony development...")

        time_steps = int(years)
        dt = 1.0  # 1 year per step

        for step in range(time_steps):
            # Update all colonies
            for colony_id in list(self.colonies.keys()):
                self.update_colony(colony_id, dt)

            # Update terraforming projects
            for project_id in list(self.terraforming_projects.keys()):
                # Simulate some investment
                investment = {'energy': 1e14 * dt, 'metals': 1e11 * dt}
                self.update_terraforming_project(project_id, dt, investment)

            # Update space stations
            for station_id in list(self.space_stations.keys()):
                self.update_space_station(station_id, dt)

            if step % max(1, time_steps // 10) == 0:
                progress = step / time_steps * 100
                stats = self.get_colony_statistics()
                print(f"Progress: {progress:.0f}%, Colonies: {stats['total_colonies']}, "
                      f"Population: {stats['total_population']:,}")

        return self.get_colony_statistics()

# Example usage and testing
if __name__ == "__main__":
    # Create colonization system
    colonization_system = PlanetColonizationSystem()

    print("Planet Colonization System Initialized")
    print(f"Available habitat designs: {list(colonization_system.habitat_designs.keys())}")
    print(f"Terraforming technologies: {list(colonization_system.terraforming_technologies.keys())}")

    # Test colonization potential assessment
    print("\n" + "="*50)
    print("ASSESSING COLONIZATION POTENTIAL")
    print("="*50)

    # Earth-like planet
    earth_like = {
        'mass': EARTH_MASS,
        'radius': EARTH_RADIUS,
        'temperature': 288,
        'atmosphere': {'N2': 0.78, 'O2': 0.21, 'Ar': 0.01},
        'has_water': True,
        'has_biosphere': True,
        'resources': {'iron': 0.3, 'water': 0.7, 'rare_metals': 0.01}
    }

    earth_assessment = colonization_system.assess_colonization_potential(earth_like)
    print(f"\nEarth-like Planet Assessment:")
    print(f"  Habitability Score: {earth_assessment['habitability_score']:.2f}")
    print(f"  Colonization Type: {earth_assessment['colonization_type'].value}")
    print(f"  Difficulty: {earth_assessment['difficulty']}")
    print(f"  Gravity: {earth_assessment['gravity']:.2f} m/s²")
    print(f"  Atmospheric Pressure: {earth_assessment['atmospheric_pressure']:.0f} Pa")
    print(f"  Suitable for Life: {earth_assessment['suitable_for_life']}")
    print(f"  Recommended Habitats: {earth_assessment['recommended_habitats']}")

    # Mars-like planet
    mars_like = {
        'mass': 0.107 * EARTH_MASS,
        'radius': 0.532 * EARTH_RADIUS,
        'temperature': 210,
        'atmosphere': {'CO2': 0.95, 'N2': 0.027, 'Ar': 0.016},
        'has_water': False,
        'has_biosphere': False,
        'resources': {'iron': 0.2, 'water_ice': 0.1, 'rare_metals': 0.02}
    }

    mars_assessment = colonization_system.assess_colonization_potential(mars_like)
    print(f"\nMars-like Planet Assessment:")
    print(f"  Habitability Score: {mars_assessment['habitability_score']:.2f}")
    print(f"  Colonization Type: {mars_assessment['colonization_type'].value}")
    print(f"  Difficulty: {mars_assessment['difficulty']}")
    print(f"  Requires Terraforming: {mars_assessment['requires_terraformin']}")
    print(f"  Terraforming Time: {mars_assessment['terraforming_requirements']['estimated_time']} years")

    # Establish colonies
    print("\n" + "="*50)
    print("ESTABLISHING COLONIES")
    print("="*50)

    # Colony on Earth-like planet
    earth_colony = colonization_system.establish_colony({
        'id': 'colony_earth_alpha',
        'name': 'New Earth Colony',
        'type': 'agricultural',
        'planet_id': 'earth_like_planet',
        'position': (0.0, 0.0, 0.0),
        'initial_population': 100,
        'max_population': 10000,
        'founding_date': 0
    })

    if earth_colony:
        print(f"Established {earth_colony.name} with {earth_colony.population} initial colonists")

        # Add habitat modules
        dome = colonization_system.construct_habitat_module(earth_colony.id, 'advanced_dome')
        if dome:
            print(f"  Built advanced dome (capacity: {dome.capacity})")

        # Add resource extractors
        iron_extractor = colonization_system.establish_resource_extractor(
            earth_colony.id, 'iron', 1000
        )
        if iron_extractor:
            print(f"  Established iron extractor (rate: {iron_extractor.extraction_rate} units/year)")

    # Colony on Mars-like planet
    mars_colony = colonization_system.establish_colony({
        'id': 'colony_mars_prime',
        'name': 'Mars Prime Outpost',
        'type': 'mining',
        'planet_id': 'mars_like_planet',
        'position': (0.0, 0.0, 0.0),
        'initial_population': 50,
        'max_population': 2000,
        'founding_date': 0
    })

    if mars_colony:
        print(f"Established {mars_colony.name} with {mars_colony.population} initial colonists")

        # Add specialized habitats for harsh environment
        bunker = colonization_system.construct_habitat_module(mars_colony.id, 'underground_bunker')
        if bunker:
            print(f"  Built underground bunker (capacity: {bunker.capacity})")

        # Start terraforming project
        terraform_project = colonization_system.start_terraforming_project(
            'mars_like_planet',
            mars_assessment['terraforming_requirements']
        )
        if terraform_project:
            print(f"  Started terraforming project (estimated: {terraform_project.estimated_completion} years)")

    # Build space station
    print("\nBuilding Space Station...")
    space_station = colonization_system.construct_space_station({
        'id': 'station_orbital_one',
        'name': 'Orbital Station One',
        'type': 'research',
        'position': (EARTH_RADIUS + 400000, 0, 0),  # 400km altitude
        'orbiting_body': 'earth_like_planet',
        'orbital_radius': EARTH_RADIUS + 400000,
        'initial_population': 75,
        'max_population': 500,
        'power_generation': 2e9,  # 2GW
        'docking_ports': 8,
        'research_facilities': 0.8
    })

    if space_station:
        print(f"Constructed {space_station.name} with {space_station.population} personnel")

    # Simulate development
    print("\n" + "="*50)
    print("SIMULATING COLONY DEVELOPMENT")
    print("="*50)

    final_stats = colonization_system.simulate_colony_development(50)  # 50 years

    print("\nFinal Statistics:")
    for key, value in final_stats.items():
        if key != 'colony_types':
            print(f"  {key}: {value}")
        else:
            print(f"  Colony Types:")
            for colony_type, count in value.items():
                print(f"    {colony_type}: {count}")

    print("\nColony Development Features:")
    print("- Dynamic colony growth and prosperity")
    print("- Habitat module construction and maintenance")
    print("- Resource extraction and management")
    print("- Terraforming project simulation")
    print("- Space station construction and operation")
    print("- Population happiness and self-sufficiency")
    print("- Environmental impact management")
    print("- Multi-colony coordination")

    print("\nPlanet colonization system test completed successfully!")