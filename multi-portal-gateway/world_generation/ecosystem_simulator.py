"""
Advanced Ecosystem Simulation System
Simulates realistic ecosystems with food chains, migration patterns, population dynamics,
predator-prey relationships, and environmental factors that affect wildlife behavior.
"""

import numpy as np
import random
from scipy import ndimage
from collections import defaultdict, deque
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class BiomeType(Enum):
    OCEAN = "ocean"
    DEEP_OCEAN = "deep_ocean"
    BEACH = "beach"
    PLAINS = "plains"
    FOREST = "forest"
    DENSE_FOREST = "dense_forest"
    JUNGLE = "jungle"
    DESERT = "desert"
    SAVANNA = "savanna"
    TUNDRA = "tundra"
    ICE = "ice"
    MOUNTAIN = "mountain"
    HIGH_MOUNTAIN = "high_mountain"
    HILLS = "hills"
    RIVER = "river"
    LAKE = "lake"
    MARSH = "marsh"
    SWAMP = "swamp"

class AnimalType(Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"
    AQUATIC = "aquatic"
    AERIAL = "aerial"
    BURROWING = "burrowing"
    ARBOREAL = "arboreal"

class VegetationType(Enum):
    GRASS = "grass"
    SHRUB = "shrub"
    TREE = "tree"
    FERN = "fern"
    MOSS = "moss"
    CACTUS = "cactus"
    REED = "reed"
    ALGAE = "algae"
    KELP = "kelp"
    FUNGUS = "fungus"
    FLOWER = "flower"
    CROP = "crop"

@dataclass
class Species:
    """Represents a species in the ecosystem"""
    name: str
    species_type: AnimalType
    diet: List[str]  # What they eat
    habitat_preferences: List[BiomeType]
    population: int
    birth_rate: float  # Offspring per individual per year
    death_rate: float  # Natural death rate
    migration_range: int  # How far they can migrate
    social_structure: str  # solitary, pair, pack, herd, etc.
    intelligence: float  # 0.0 - 1.0
    aggression: float  # 0.0 - 1.0
    reproduction_age: int  # Age of sexual maturity
    max_age: int  # Maximum lifespan
    size: str  # tiny, small, medium, large, huge
    speed: float  # Movement speed
    camouflage: float  # Ability to hide
    special_abilities: List[str] = field(default_factory=list)

@dataclass
class Animal:
    """Represents an individual animal"""
    species: Species
    position: Tuple[int, int]
    age: int
    health: float  # 0.0 - 1.0
    hunger: float  # 0.0 - 1.0
    thirst: float  # 0.0 - 1.0
    energy: float  # 0.0 - 1.0
    social_group: Optional[int] = None
    is_pregnant: bool = False
    gestation_period: int = 0
    offspring_count: int = 0
    home_range: Optional[Tuple[int, int, int, int]] = None  # min_y, min_x, max_y, max_x

@dataclass
class Plant:
    """Represents vegetation"""
    vegetation_type: VegetationType
    position: Tuple[int, int]
    growth_stage: int  # 0-5 (seedling to mature)
    health: float  # 0.0 - 1.0
    size: float  # Size factor
    edible: bool = True
    nutritional_value: float = 1.0
    reproduction_rate: float = 1.0

@dataclass
class EcosystemCell:
    """Represents a single cell in the ecosystem grid"""
    biome: BiomeType
    temperature: float  # Celsius
    humidity: float  # 0.0 - 1.0
    vegetation_density: float  # 0.0 - 1.0
    water_availability: float  # 0.0 - 1.0
    plants: List[Plant] = field(default_factory=list)
    animals: List[Animal] = field(default_factory=list)
    carrying_capacity: int = 0
    pollution_level: float = 0.0  # 0.0 - 1.0

class FoodWeb:
    """Manages food chain relationships and energy flow"""

    def __init__(self):
        self.predator_prey = {}  # predator -> [prey species]
       .competitors = {}  # species -> [competing species]
       .symbiotic = {}  # species -> [symbiotic partners]

    def add_predator_prey(self, predator: str, prey: str, hunting_success: float = 0.3):
        """Add predator-prey relationship"""
        if predator not in self.predator_prey:
            self.predator_prey[predator] = []
        self.predator_prey[predator].append((prey, hunting_success))

    def add_competition(self, species1: str, species2: str, competition_level: float = 0.5):
        """Add competitive relationship"""
        if species1 not in self.competitors:
            self.competitors[species1] = []
        if species2 not in self.competitors:
            self.competitors[species2] = []
        self.competitors[species1].append((species2, competition_level))
        self.competitors[species2].append((species1, competition_level))

    def get_prey_options(self, predator_species: str) -> List[Tuple[str, float]]:
        """Get available prey for a predator"""
        return self.predator_prey.get(predator_species, [])

    def get_competitors(self, species: str) -> List[Tuple[str, float]]:
        """Get competing species"""
        return self.competitors.get(species, [])

class ClimateSimulator:
    """Simulates climate patterns and seasonal changes"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.base_temperature = np.random.normal(15, 10, (height, width))  # Base temperature
        self.base_humidity = np.random.beta(2, 2, (height, width))  # Base humidity
        self.season = 0  # 0-3 (spring, summer, autumn, winter)
        self.season_length = 30  # Days per season
        self.day = 0

    def update_climate(self):
        """Update climate for current day and season"""
        self.day += 1
        if self.day >= self.season_length * 4:
            self.day = 0

        self.season = self.day // self.season_length

        # Seasonal temperature variation
        seasonal_temp_modifier = {
            0: 0,      # Spring
            1: 10,     # Summer
            2: 0,      # Autumn
            3: -10     # Winter
        }[self.season]

        # Seasonal humidity variation
        seasonal_humidity_modifier = {
            0: 0.1,    # Spring
            1: -0.1,   # Summer
            2: 0.2,    # Autumn
            3: -0.2    # Winter
        }[self.season]

        # Add daily variations
        daily_temp_variation = np.random.normal(0, 2, (self.height, self.width))
        daily_humidity_variation = np.random.normal(0, 0.05, (self.height, self.width))

        temperature = self.base_temperature + seasonal_temp_modifier + daily_temp_variation
        humidity = np.clip(self.base_humidity + seasonal_humidity_modifier + daily_humidity_variation, 0, 1)

        return temperature, humidity

    def get_season_name(self) -> str:
        """Get current season name"""
        seasons = ["Spring", "Summer", "Autumn", "Winter"]
        return seasons[self.season]

class PopulationDynamics:
    """Manages population dynamics and demographics"""

    @staticmethod
    def calculate_birth_rate(animals: List[Animal], species: Species,
                           environmental_factors: Dict) -> float:
        """Calculate birth rate based on environmental factors"""
        base_rate = species.birth_rate

        # Environmental modifiers
        temperature_modifier = PopulationDynamics._get_optimal_modifier(
            environmental_factors.get('temperature', 15),
            species.habitat_preferences, 'temperature'
        )
        food_modifier = environmental_factors.get('food_availability', 0.5)
        density_modifier = PopulationDynamics._get_density_modifier(
            len(animals), environmental_factors.get('carrying_capacity', 100)
        )

        return base_rate * temperature_modifier * food_modifier * density_modifier

    @staticmethod
    def calculate_death_rate(animals: List[Animal], species: Species,
                           environmental_factors: Dict) -> float:
        """Calculate death rate based on environmental factors"""
        base_rate = species.death_rate

        # Environmental modifiers
        temperature_modifier = PopulationDynamics._get_optimal_modifier(
            environmental_factors.get('temperature', 15),
            species.habitat_preferences, 'temperature'
        )
        food_modifier = 2.0 - environmental_factors.get('food_availability', 0.5)  # Inverse
        predation_modifier = environmental_factors.get('predation_pressure', 0.1)
        disease_modifier = environmental_factors.get('disease_pressure', 0.05)

        return base_rate * temperature_modifier * food_modifier + predation_modifier + disease_modifier

    @staticmethod
    def _get_optimal_modifier(value: float, preferences: List[BiomeType],
                            factor_type: str) -> float:
        """Get modifier based on optimal conditions"""
        # Simplified - would be more complex in reality
        if factor_type == 'temperature':
            if 10 <= value <= 25:
                return 1.0
            elif 0 <= value <= 35:
                return 0.7
            else:
                return 0.3
        return 1.0

    @staticmethod
    def _get_density_modifier(population: int, carrying_capacity: int) -> float:
        """Get modifier based on population density"""
        if population >= carrying_capacity:
            return 0.1  # Very low birth rate when overcrowded
        elif population > carrying_capacity * 0.8:
            return 0.5
        elif population < carrying_capacity * 0.3:
            return 1.5  # Higher birth rate when population is low
        else:
            return 1.0

class MigrationSimulator:
    """Simulates animal migration patterns"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.migration_routes = {}  # species -> list of routes
        self.seasonal_triggers = {}  # season -> [species that migrate]

    def generate_migration_route(self, species: Species, start_biome: BiomeType,
                               end_biome: BiomeType) -> List[Tuple[int, int]]:
        """Generate migration route between biomes"""
        # Simplified route generation
        route = []

        # Start point
        current_pos = self._find_biome_location(start_biome)
        if not current_pos:
            return route

        # End point
        end_pos = self._find_biome_location(end_biome)
        if not end_pos:
            return route

        # Generate waypoints
        route.append(current_pos)

        # Intermediate waypoints
        num_waypoints = 5
        for i in range(num_waypoints):
            t = (i + 1) / (num_waypoints + 1)
            waypoint_y = int(current_pos[0] + t * (end_pos[0] - current_pos[0]))
            waypoint_x = int(current_pos[1] + t * (end_pos[1] - current_pos[1]))
            route.append((waypoint_y, waypoint_x))

        route.append(end_pos)
        return route

    def _find_biome_location(self, biome: BiomeType) -> Optional[Tuple[int, int]]:
        """Find a random location in the specified biome"""
        # This would need access to the biome map
        # For now, return random position
        return (random.randint(0, self.height - 1), random.randint(0, self.width - 1))

    def should_migrate(self, species: Species, season: int,
                      current_conditions: Dict) -> bool:
        """Determine if species should migrate based on conditions"""
        # Seasonal migration
        if species.name in self.seasonal_triggers.get(season, []):
            return True

        # Environmental triggers
        food_scarcity = current_conditions.get('food_availability', 0.5) < 0.2
        temperature_extreme = abs(current_conditions.get('temperature', 15)) > 30

        return food_scarcity or temperature_extreme

class PlantGrowthSimulator:
    """Simulates plant growth and reproduction"""

    @staticmethod
    def grow_plants(plants: List[Plant], environmental_factors: Dict,
                   time_step: int = 1) -> None:
        """Update plant growth"""
        for plant in plants:
            # Growth rate based on conditions
            growth_rate = PlantGrowthSimulator._calculate_growth_rate(
                plant, environmental_factors
            )

            # Update growth stage
            plant.growth_stage = min(5, plant.growth_stage + growth_rate * time_step)

            # Update health
            plant.health = min(1.0, plant.health + growth_rate * 0.1 * time_step)
            plant.health = max(0.0, plant.health - 0.05 * time_step)  # Natural decay

            # Update size
            plant.size = 0.2 + (plant.growth_stage / 5.0) * 0.8

            # Update nutritional value
            plant.nutritional_value = plant.health * plant.size

    @staticmethod
    def _calculate_growth_rate(plant: Plant, environmental_factors: Dict) -> float:
        """Calculate growth rate for a plant"""
        base_rate = plant.reproduction_rate

        # Temperature factor
        temperature = environmental_factors.get('temperature', 15)
        if 15 <= temperature <= 25:
            temp_factor = 1.0
        elif 5 <= temperature <= 30:
            temp_factor = 0.7
        else:
            temp_factor = 0.3

        # Water factor
        water_factor = environmental_factors.get('water_availability', 0.5)

        # Sunlight factor
        sunlight_factor = environmental_factors.get('sunlight', 0.5)

        # Soil quality factor
        soil_factor = environmental_factors.get('soil_quality', 0.5)

        return base_rate * temp_factor * water_factor * sunlight_factor * soil_factor

    @staticmethod
    def reproduce_plants(plants: List[Plant], max_density: int = 10) -> List[Plant]:
        """Generate new plants through reproduction"""
        new_plants = []

        for plant in plants:
            if plant.growth_stage >= 3 and random.random() < plant.reproduction_rate * 0.1:
                # Create offspring near parent
                offspring = Plant(
                    vegetation_type=plant.vegetation_type,
                    position=plant.position,  # Would be near parent in full implementation
                    growth_stage=0,
                    health=0.8,
                    size=0.1,
                    nutritional_value=0.1,
                    reproduction_rate=plant.reproduction_rate * random.uniform(0.8, 1.2)
                )
                new_plants.append(offspring)

        return new_plants

class EcosystemSimulator:
    """Main ecosystem simulation system"""

    def __init__(self, width: int, height: int, biome_map: np.ndarray,
                 seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.biome_map = biome_map
        self.ecosystem_grid = [[EcosystemCell(
            biome=BiomeType(biome_map[y, x]),
            temperature=15.0,
            humidity=0.5,
            vegetation_density=0.0,
            water_availability=0.5
        ) for x in range(width)] for y in range(height)]

        self.climate_simulator = ClimateSimulator(width, height)
        self.food_web = FoodWeb()
        self.migration_simulator = MigrationSimulator(width, height)
        self.species_registry = {}
        self.all_animals = []
        self.time_step = 0

        # Initialize ecosystem
        self._initialize_food_web()
        self._initialize_species()
        self._initialize_populations()

    def _initialize_food_web(self):
        """Initialize predator-prey relationships"""
        # Define basic food web
        relationships = [
            # Predators and prey
            ("Wolf", "Deer", 0.3),
            ("Wolf", "Rabbit", 0.5),
            ("Bear", "Salmon", 0.6),
            ("Bear", "Berry", 0.8),
            ("Eagle", "Rabbit", 0.4),
            ("Eagle", "Fish", 0.7),
            ("Fox", "Rabbit", 0.4),
            ("Fox", "Mouse", 0.6),

            # Competition
            ("Wolf", "Bear", 0.3),
            ("Deer", "Rabbit", 0.4),
        ]

        for predator, prey, success_rate in relationships:
            self.food_web.add_predator_prey(predator, prey, success_rate)

        # Define competition
        competitions = [
            ("Wolf", "Bear", 0.3),
            ("Deer", "Rabbit", 0.4),
        ]

        for species1, species2, level in competitions:
            self.food_web.add_competition(species1, species2, level)

    def _initialize_species(self):
        """Initialize species registry"""
        species_data = [
            Species(
                name="Wolf",
                species_type=AnimalType.CARNIVORE,
                diet=["Deer", "Rabbit", "Mouse"],
                habitat_preferences=[BiomeType.FOREST, BiomeType.DENSE_FOREST, BiomeType.TUNDRA],
                population=50,
                birth_rate=0.15,
                death_rate=0.08,
                migration_range=20,
                social_structure="pack",
                intelligence=0.7,
                aggression=0.8,
                reproduction_age=2,
                max_age=12,
                size="large",
                speed=1.2,
                camouflage=0.6,
                special_abilities=["pack_hunting", "howling"]
            ),
            Species(
                name="Deer",
                species_type=AnimalType.HERBIVORE,
                diet=["Grass", "Shrub", "Tree_leaves"],
                habitat_preferences=[BiomeType.FOREST, BiomeType.PLAINS, BiomeType.HILLS],
                population=200,
                birth_rate=0.25,
                death_rate=0.12,
                migration_range=15,
                social_structure="herd",
                intelligence=0.5,
                aggression=0.2,
                reproduction_age=1,
                max_age=15,
                size="medium",
                speed=1.5,
                camouflage=0.7,
                special_abilities=["keen_hearing", "fast_running"]
            ),
            Species(
                name="Rabbit",
                species_type=AnimalType.HERBIVORE,
                diet=["Grass", "Flower", "Vegetable"],
                habitat_preferences=[BiomeType.PLAINS, BiomeType.FOREST, BiomeType.HILLS],
                population=500,
                birth_rate=0.8,
                death_rate=0.6,
                migration_range=5,
                social_structure="colony",
                intelligence=0.3,
                aggression=0.1,
                reproduction_age=0.5,
                max_age=8,
                size="small",
                speed=2.0,
                camouflage=0.8,
                special_abilities=["burrowing", "rapid_breeding"]
            ),
            Species(
                name="Bear",
                species_type=AnimalType.OMNIVORE,
                diet=["Salmon", "Berry", "Deer", "Honey"],
                habitat_preferences=[BiomeType.FOREST, BiomeType.DENSE_FOREST, BiomeType.MOUNTAIN],
                population=30,
                birth_rate=0.1,
                death_rate=0.05,
                migration_range=25,
                social_structure="solitary",
                intelligence=0.6,
                aggression=0.7,
                reproduction_age=3,
                max_age=25,
                size="huge",
                speed=1.0,
                camouflage=0.5,
                special_abilities=["hibernation", "strength"]
            ),
            Species(
                name="Eagle",
                species_type=AnimalType.AERIAL,
                diet=["Rabbit", "Fish", "Mouse"],
                habitat_preferences=[BiomeType.MOUNTAIN, BiomeType.HILLS, BiomeType.FOREST],
                population=40,
                birth_rate=0.2,
                death_rate=0.15,
                migration_range=50,
                social_structure="pair",
                intelligence=0.8,
                aggression=0.6,
                reproduction_age=2,
                max_age=20,
                size="medium",
                speed=3.0,
                camouflage=0.4,
                special_abilities=["flight", "keen_vision"]
            ),
            Species(
                name="Salmon",
                species_type=AnimalType.AQUATIC,
                diet=["Algae", "Insects"],
                habitat_preferences=[BiomeType.RIVER, BiomeType.LAKE, BiomeType.OCEAN],
                population=1000,
                birth_rate=0.5,
                death_rate=0.7,
                migration_range=100,
                social_structure="school",
                intelligence=0.2,
                aggression=0.1,
                reproduction_age=2,
                max_age=6,
                size="small",
                speed=2.5,
                camouflage=0.6,
                special_abilities=["swimming", "spawning_migration"]
            )
        ]

        for species in species_data:
            self.species_registry[species.name] = species

    def _initialize_populations(self):
        """Initialize animal and plant populations"""
        # Place animals in appropriate biomes
        for species_name, species in self.species_registry.items():
            for _ in range(species.population):
                # Find suitable habitat
                suitable_positions = []
                for y in range(self.height):
                    for x in range(self.width):
                        if self.ecosystem_grid[y][x].biome in species.habitat_preferences:
                            suitable_positions.append((y, x))

                if suitable_positions:
                    position = random.choice(suitable_positions)
                    animal = Animal(
                        species=species,
                        position=position,
                        age=random.randint(0, species.max_age),
                        health=random.uniform(0.7, 1.0),
                        hunger=random.uniform(0, 0.5),
                        thirst=random.uniform(0, 0.5),
                        energy=random.uniform(0.5, 1.0)
                    )
                    self.all_animals.append(animal)
                    self.ecosystem_grid[position[0]][position[1]].animals.append(animal)

        # Initialize vegetation
        self._initialize_vegetation()

    def _initialize_vegetation(self):
        """Initialize vegetation based on biomes"""
        biome_vegetation = {
            BiomeType.FOREST: [VegetationType.TREE, VegetationType.SHRUB, VegetationType.FERN],
            BiomeType.DENSE_FOREST: [VegetationType.TREE, VegetationType.MOSS, VegetationType.FERN],
            BiomeType.PLAINS: [VegetationType.GRASS, VegetationType.FLOWER],
            BiomeType.JUNGLE: [VegetationType.TREE, VegetationType.FERN, VegetationType.FUNGUS],
            BiomeType.DESERT: [VegetationType.CACTUS, VegetationType.SHRUB],
            BiomeType.SAVANNA: [VegetationType.GRASS, VegetationType.SHRUB],
            BiomeType.TUNDRA: [VegetationType.MOSS, VegetationType.FERN],
            BiomeType.MARSH: [VegetationType.REED, VegetationType.MOSS],
            BiomeType.SWAMP: [VegetationType.TREE, VegetationType.FUNGUS],
            BiomeType.RIVER: [VegetationType.REED, VegetationType.ALGAE],
            BiomeType.LAKE: [VegetationType.ALGAE],
            BiomeType.OCEAN: [VegetationType.KELP, VegetationType.ALGAE]
        }

        for y in range(self.height):
            for x in range(self.width):
                cell = self.ecosystem_grid[y][x]
                biome = cell.biome

                if biome in biome_vegetation:
                    vegetation_types = biome_vegetation[biome]

                    # Determine vegetation density based on biome
                    if biome in [BiomeType.DENSE_FOREST, BiomeType.JUNGLE]:
                        density = random.uniform(0.7, 1.0)
                    elif biome in [BiomeType.FOREST, BiomeType.SWAMP]:
                        density = random.uniform(0.5, 0.8)
                    elif biome in [BiomeType.PLAINS, BiomeType.SAVANNA]:
                        density = random.uniform(0.3, 0.6)
                    else:
                        density = random.uniform(0.1, 0.4)

                    cell.vegetation_density = density

                    # Create plants based on density
                    num_plants = int(density * 5)
                    for _ in range(num_plants):
                        veg_type = random.choice(vegetation_types)
                        plant = Plant(
                            vegetation_type=veg_type,
                            position=(y, x),
                            growth_stage=random.randint(2, 5),
                            health=random.uniform(0.6, 1.0),
                            size=random.uniform(0.4, 1.0),
                            nutritional_value=random.uniform(0.5, 1.5),
                            reproduction_rate=random.uniform(0.8, 1.2)
                        )
                        cell.plants.append(plant)

    def simulate_step(self):
        """Simulate one time step of the ecosystem"""
        self.time_step += 1

        # Update climate
        temperature, humidity = self.climate_simulator.update_climate()

        # Update environmental conditions
        self._update_environmental_conditions(temperature, humidity)

        # Update plants
        self._update_plants()

        # Update animals
        self._update_animals()

        # Process births and deaths
        self._process_population_dynamics()

        # Process migrations
        self._process_migrations()

    def _update_environmental_conditions(self, temperature: np.ndarray, humidity: np.ndarray):
        """Update environmental conditions across the grid"""
        for y in range(self.height):
            for x in range(self.width):
                cell = self.ecosystem_grid[y][x]
                cell.temperature = temperature[y, x]
                cell.humidity = humidity[y, x]

                # Update water availability based on humidity and biome
                if cell.biome in [BiomeType.RIVER, BiomeType.LAKE, BiomeType.OCEAN]:
                    cell.water_availability = 1.0
                elif cell.biome in [BiomeType.MARSH, BiomeType.SWAMP]:
                    cell.water_availability = 0.8 + cell.humidity * 0.2
                else:
                    cell.water_availability = cell.humidity * 0.6

                # Calculate carrying capacity based on conditions
                base_capacity = {
                    BiomeType.DENSE_FOREST: 100,
                    BiomeType.JUNGLE: 120,
                    BiomeType.FOREST: 80,
                    BiomeType.PLAINS: 60,
                    BiomeType.SAVANNA: 40,
                    BiomeType.MARSH: 30,
                    BiomeType.SWAMP: 25,
                    BiomeType.HILLS: 35,
                    BiomeType.MOUNTAIN: 15,
                    BiomeType.TUNDRA: 10,
                    BiomeType.DESERT: 5,
                    BiomeType.ICE: 2
                }.get(cell.biome, 20)

                # Modify based on conditions
                environmental_factor = cell.humidity * min(1.0, abs(cell.temperature - 20) / 20)
                cell.carrying_capacity = int(base_capacity * environmental_factor)

    def _update_plants(self):
        """Update plant growth and reproduction"""
        for y in range(self.height):
            for x in range(self.width):
                cell = self.ecosystem_grid[y][x]

                if cell.plants:
                    environmental_factors = {
                        'temperature': cell.temperature,
                        'water_availability': cell.water_availability,
                        'sunlight': max(0, (cell.temperature - 10) / 20),
                        'soil_quality': cell.vegetation_density
                    }

                    # Grow existing plants
                    PlantGrowthSimulator.grow_plants(cell.plants, environmental_factors)

                    # Remove dead plants
                    cell.plants = [p for p in cell.plants if p.health > 0]

                    # Reproduction
                    if len(cell.plants) < 20:  # Prevent overcrowding
                        new_plants = PlantGrowthSimulator.reproduce_plants(cell.plants)
                        cell.plants.extend(new_plants)

    def _update_animals(self):
        """Update animal states and behaviors"""
        random.shuffle(self.all_animals)  # Random order for fairness

        for animal in self.all_animals:
            if animal.health <= 0:
                continue

            # Update basic needs
            animal.hunger = min(1.0, animal.hunger + 0.05)
            animal.thirst = min(1.0, animal.thirst + 0.03)
            animal.energy = max(0, animal.energy - 0.02)

            # Age the animal
            animal.age += 0.01

            # Check for death
            if (animal.age > animal.species.max_age or
                animal.hunger > 0.9 or
                animal.thirst > 0.9 or
                animal.energy <= 0):
                animal.health = 0
                continue

            # Behavior based on needs
            if animal.hunger > 0.7:
                self._find_food(animal)
            elif animal.thirst > 0.7:
                self._find_water(animal)
            elif animal.energy < 0.3:
                self._rest(animal)
            else:
                self._wander(animal)

            # Social behaviors
            if animal.species.social_structure in ["pack", "herd", "colony"]:
                self._update_social_behavior(animal)

    def _find_food(self, animal: Animal):
        """Find food for the animal"""
        y, x = animal.position
        cell = self.ecosystem_grid[y][x]

        if animal.species.species_type == AnimalType.HERBIVORE:
            # Look for plants
            edible_plants = [p for p in cell.plants if p.edible and p.growth_stage >= 2]
            if edible_plants:
                # Eat the most nutritious plant
                best_plant = max(edible_plants, key=lambda p: p.nutritional_value)
                nutrition = best_plant.nutritional_value * 0.3
                animal.hunger = max(0, animal.hunger - nutrition)
                animal.health = min(1.0, animal.health + 0.02)

                # Reduce plant health
                best_plant.health -= 0.1
                best_plant.size *= 0.9
            else:
                # Move to find food
                self._move_towards_resource(animal, "vegetation")

        elif animal.species.species_type == AnimalType.CARNIVORE:
            # Hunt for prey
            prey_animals = [a for a in cell.animals
                          if a.species.name in animal.species.diet and a != animal]
            if prey_animals:
                # Hunt the weakest prey
                prey = min(prey_animals, key=lambda p: p.health)
                if self._attempt_hunt(animal, prey):
                    nutrition = 0.5
                    animal.hunger = max(0, animal.hunger - nutrition)
                    animal.health = min(1.0, animal.health + 0.05)
                    prey.health = 0
            else:
                # Look for prey in neighboring cells
                self._move_towards_prey(animal)

        elif animal.species.species_type == AnimalType.OMNIVORE:
            # Try plants first, then hunt
            edible_plants = [p for p in cell.plants if p.edible and p.growth_stage >= 2]
            if edible_plants and random.random() < 0.6:
                best_plant = max(edible_plants, key=lambda p: p.nutritional_value)
                nutrition = best_plant.nutritional_value * 0.2
                animal.hunger = max(0, animal.hunger - nutrition)
                animal.health = min(1.0, animal.health + 0.02)
                best_plant.health -= 0.1
            else:
                # Hunt
                prey_animals = [a for a in cell.animals
                              if a.species.name in animal.species.diet and a != animal]
                if prey_animals:
                    prey = min(prey_animals, key=lambda p: p.health)
                    if self._attempt_hunt(animal, prey):
                        nutrition = 0.4
                        animal.hunger = max(0, animal.hunger - nutrition)
                        animal.health = min(1.0, animal.health + 0.04)
                        prey.health = 0
                else:
                    self._move_towards_resource(animal, "vegetation")

    def _find_water(self, animal: Animal):
        """Find water for the animal"""
        y, x = animal.position
        cell = self.ecosystem_grid[y][x]

        if cell.water_availability > 0.5:
            # Drink water
            animal.thirst = max(0, animal.thirst - 0.3)
            animal.health = min(1.0, animal.health + 0.01)
        else:
            # Move towards water
            self._move_towards_resource(animal, "water")

    def _rest(self, animal: Animal):
        """Rest to recover energy"""
        animal.energy = min(1.0, animal.energy + 0.1)
        animal.health = min(1.0, animal.health + 0.01)

    def _wander(self, animal: Animal):
        """Random movement"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)

        for dy, dx in directions:
            new_y = animal.position[0] + dy
            new_x = animal.position[1] + dx

            if (0 <= new_y < self.height and 0 <= new_x < self.width):
                new_cell = self.ecosystem_grid[new_y][new_x]
                if new_cell.biome in animal.species.habitat_preferences:
                    self._move_animal(animal, (new_y, new_x))
                    break

    def _move_towards_resource(self, animal: Animal, resource_type: str):
        """Move towards a specific resource type"""
        best_direction = None
        best_value = -1

        for dy in range(-2, 3):
            for dx in range(-2, 3):
                new_y = animal.position[0] + dy
                new_x = animal.position[1] + dx

                if (0 <= new_y < self.height and 0 <= new_x < self.width):
                    cell = self.ecosystem_grid[new_y][new_x]

                    if resource_type == "vegetation":
                        value = cell.vegetation_density
                    elif resource_type == "water":
                        value = cell.water_availability
                    else:
                        value = 0

                    if value > best_value:
                        best_value = value
                        best_direction = (dy, dx)

        if best_direction and best_value > 0.1:
            dy, dx = best_direction
            new_y = animal.position[0] + dy
            new_x = animal.position[1] + dx
            self._move_animal(animal, (new_y, new_x))

    def _move_towards_prey(self, animal: Animal):
        """Move towards prey animals"""
        best_direction = None
        best_score = -1

        for dy in range(-3, 4):
            for dx in range(-3, 4):
                new_y = animal.position[0] + dy
                new_x = animal.position[1] + dx

                if (0 <= new_y < self.height and 0 <= new_x < self.width):
                    cell = self.ecosystem_grid[new_y][new_x]

                    # Look for prey in this cell
                    prey_count = sum(1 for a in cell.animals
                                   if a.species.name in animal.species.diet and a != animal)

                    if prey_count > 0:
                        # Score based on prey count and distance
                        distance = math.sqrt(dy**2 + dx**2)
                        score = prey_count / distance if distance > 0 else 0

                        if score > best_score:
                            best_score = score
                            best_direction = (dy, dx)

        if best_direction:
            dy, dx = best_direction
            new_y = animal.position[0] + dy
            new_x = animal.position[1] + dx
            self._move_animal(animal, (new_y, new_x))

    def _attempt_hunt(self, predator: Animal, prey: Animal) -> bool:
        """Attempt to hunt prey"""
        # Calculate hunting success based on various factors
        base_success = 0.3

        # Size advantage
        size_advantage = predator.species.size == "large" and prey.species.size == "small"
        if size_advantage:
            base_success += 0.3

        # Health advantage
        health_advantage = predator.health - prey.health
        base_success += health_advantage * 0.2

        # Camouflage vs detection
        detection_difficulty = prey.species.camouflage - predator.species.intelligence * 0.5
        base_success -= detection_difficulty * 0.2

        # Energy levels
        if predator.energy < 0.3:
            base_success -= 0.2

        success = random.random() < max(0.1, min(0.9, base_success))

        if success:
            predator.energy = max(0, predator.energy - 0.1)  # Hunting costs energy

        return success

    def _move_animal(self, animal: Animal, new_position: Tuple[int, int]):
        """Move animal to new position"""
        # Remove from old cell
        old_cell = self.ecosystem_grid[animal.position[0]][animal.position[1]]
        if animal in old_cell.animals:
            old_cell.animals.remove(animal)

        # Add to new cell
        animal.position = new_position
        new_cell = self.ecosystem_grid[new_position[0]][new_position[1]]
        new_cell.animals.append(animal)

    def _update_social_behavior(self, animal: Animal):
        """Update social behaviors for group animals"""
        y, x = animal.position
        cell = self.ecosystem_grid[y][x]

        # Find same-species animals
        same_species = [a for a in cell.animals if a.species == animal.species and a != animal]

        if same_species:
            # Move towards group members
            if random.random() < 0.3:
                self._move_towards_group(animal, same_species[0].position)

            # Share information about resources/dangers
            if random.random() < 0.1:
                self._share_information(animal, same_species)

    def _move_towards_group(self, animal: Animal, target_position: Tuple[int, int]):
        """Move towards group member"""
        dy = target_position[0] - animal.position[0]
        dx = target_position[1] - animal.position[1]

        # Normalize movement
        if dy != 0:
            dy = 1 if dy > 0 else -1
        if dx != 0:
            dx = 1 if dx > 0 else -1

        new_y = animal.position[0] + dy
        new_x = animal.position[1] + dx

        if (0 <= new_y < self.height and 0 <= new_x < self.width):
            self._move_animal(animal, (new_y, new_x))

    def _share_information(self, animal: Animal, group_members: List[Animal]):
        """Share information about resources or dangers"""
        # Simplified information sharing
        for member in group_members:
            if random.random() < 0.5:
                # Share information about food/water sources or dangers
                pass  # Would implement more complex information sharing

    def _process_population_dynamics(self):
        """Process births and deaths"""
        # Remove dead animals
        self.all_animals = [a for a in self.all_animals if a.health > 0]

        # Remove dead animals from grid
        for y in range(self.height):
            for x in range(self.width):
                cell = self.ecosystem_grid[y][x]
                cell.animals = [a for a in cell.animals if a.health > 0]

        # Process births
        new_animals = []
        for animal in self.all_animals:
            if (animal.age >= animal.species.reproduction_age and
                not animal.is_pregnant and
                random.random() < animal.species.birth_rate * 0.01):

                # Check for potential mates
                y, x = animal.position
                cell = self.ecosystem_grid[y][x]
                potential_mates = [a for a in cell.animals
                                 if (a.species == animal.species and
                                     a.age >= a.species.reproduction_age and
                                     a != animal)]

                if potential_mates:
                    # Reproduce
                    for _ in range(random.randint(1, 3)):  # Litter size
                        offspring = Animal(
                            species=animal.species,
                            position=animal.position,
                            age=0,
                            health=0.9,
                            hunger=0.2,
                            thirst=0.2,
                            energy=0.8
                        )
                        new_animals.append(offspring)
                        cell.animals.append(offspring)

        self.all_animals.extend(new_animals)

    def _process_migrations(self):
        """Process seasonal migrations"""
        season = self.climate_simulator.season

        # Check each species for migration triggers
        for species_name, species in self.species_registry.items():
            if self.migration_simulator.should_migrate(species, season, {}):
                # Find animals of this species
                species_animals = [a for a in self.all_animals if a.species.name == species_name]

                # Initiate migration
                for animal in species_animals:
                    if random.random() < 0.1:  # 10% chance per time step
                        self._migrate_animal(animal)

    def _migrate_animal(self, animal: Animal):
        """Migrate an animal to better habitat"""
        # Find best nearby habitat
        best_position = None
        best_score = -1

        search_radius = animal.species.migration_range

        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                new_y = animal.position[0] + dy
                new_x = animal.position[1] + dx

                if (0 <= new_y < self.height and 0 <= new_x < self.width):
                    cell = self.ecosystem_grid[new_y][new_x]

                    # Score habitat quality
                    if cell.biome in animal.species.habitat_preferences:
                        score = (cell.vegetation_density * 0.3 +
                               cell.water_availability * 0.4 +
                               (1.0 - abs(cell.temperature - 20) / 30) * 0.3)

                        # Consider population density
                        competition = len([a for a in cell.animals
                                        if a.species == animal.species])
                        score -= competition * 0.1

                        if score > best_score:
                            best_score = score
                            best_position = (new_y, new_x)

        if best_position and best_score > 0.5:
            # Move towards better habitat
            self._move_animal(animal, best_position)

    def get_ecosystem_statistics(self) -> Dict:
        """Get comprehensive ecosystem statistics"""
        species_populations = defaultdict(int)
        biome_animal_counts = defaultdict(lambda: defaultdict(int))
        total_plants = 0
        total_animals = len(self.all_animals)

        for animal in self.all_animals:
            species_populations[animal.species.name] += 1
            y, x = animal.position
            biome = self.ecosystem_grid[y][x].biome
            biome_animal_counts[biome][animal.species.name] += 1

        for y in range(self.height):
            for x in range(self.width):
                total_plants += len(self.ecosystem_grid[y][x].plants)

        avg_temperature = np.mean([[cell.temperature for cell in row]
                                   for row in self.ecosystem_grid])
        avg_humidity = np.mean([[cell.humidity for cell in row]
                               for row in self.ecosystem_grid])

        return {
            'time_step': self.time_step,
            'season': self.climate_simulator.get_season_name(),
            'total_animals': total_animals,
            'total_plants': total_plants,
            'species_populations': dict(species_populations),
            'biome_animal_counts': {biome.value: dict(counts)
                                  for biome, counts in biome_animal_counts.items()},
            'average_temperature': avg_temperature,
            'average_humidity': avg_humidity,
            'biodiversity_index': len(species_populations),
            'healthiest_species': max(species_populations.items(), key=lambda x: x[1])[0] if species_populations else None
        }

# Utility functions
def create_sample_biome_map(width: int, height: int, seed: Optional[int] = None) -> np.ndarray:
    """Create a sample biome map for testing"""
    if seed is not None:
        np.random.seed(seed)

    biome_map = np.zeros((height, width), dtype=int)

    # Create simple biome pattern
    for y in range(height):
        for x in range(width):
            if y < height // 4:
                if x < width // 3:
                    biome_map[y, x] = BiomeType.TUNDRA.value
                elif x < 2 * width // 3:
                    biome_map[y, x] = BiomeType.HILLS.value
                else:
                    biome_map[y, x] = BiomeType.MOUNTAIN.value
            elif y < height // 2:
                if x < width // 4:
                    biome_map[y, x] = BiomeType.PLAINS.value
                elif x < 3 * width // 4:
                    biome_map[y, x] = BiomeType.FOREST.value
                else:
                    biome_map[y, x] = BiomeType.HILLS.value
            elif y < 3 * height // 4:
                if x < width // 2:
                    biome_map[y, x] = BiomeType.FOREST.value
                else:
                    biome_map[y, x] = BiomeType.DENSE_FOREST.value
            else:
                if x < width // 3:
                    biome_map[y, x] = BiomeType.MARSH.value
                elif x < 2 * width // 3:
                    biome_map[y, x] = BiomeType.SWAMP.value
                else:
                    biome_map[y, x] = BiomeType.PLAINS.value

    return biome_map

if __name__ == "__main__":
    # Example usage
    width, height = 50, 50
    biome_map = create_sample_biome_map(width, height, seed=42)

    print("Initializing ecosystem simulator...")
    ecosystem = EcosystemSimulator(width, height, biome_map, seed=42)

    print("Running simulation...")
    for i in range(10):
        ecosystem.simulate_step()
        if i % 5 == 0:
            stats = ecosystem.get_ecosystem_statistics()
            print(f"Step {i}: {stats['total_animals']} animals, {stats['total_plants']} plants")
            print(f"  Season: {stats['season']}, Temp: {stats['average_temperature']:.1f}°C")

    final_stats = ecosystem.get_ecosystem_statistics()
    print(f"\nFinal Statistics:")
    print(f"Total animals: {final_stats['total_animals']}")
    print(f"Total plants: {final_stats['total_plants']}")
    print(f"Species: {list(final_stats['species_populations'].keys())}")
    print(f"Biodiversity index: {final_stats['biodiversity_index']}")