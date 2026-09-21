#!/usr/bin/env python3
"""
World Generation Demo - Showcases Procedural World Creation
Demonstrates dynamic world building, ecosystem simulation, and living environments
"""

import asyncio
import random
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger('DMLogn8n-WorldGenDemo')

class BiomeType(Enum):
    """World biome types"""
    FOREST = "forest"
    DESERT = "desert"
    MOUNTAINS = "mountains"
    OCEAN = "ocean"
    TUNDRA = "tundra"
    JUNGLE = "jungle"
    SAVANNAH = "savannah"
    SWAMP = "swamp"
    VOLCANIC = "volcanic"
    MYSTICAL = "mystical"

class LocationType(Enum):
    """Types of locations within worlds"""
    CITY = "city"
    VILLAGE = "village"
    DUNGEON = "dungeon"
    TEMPLE = "temple"
    FORTRESS = "fortress"
    CAVE = "cave"
    RUINS = "ruins"
    SHRINE = "shrine"
    CAMP = "camp"
    TOWER = "tower"

class WorldEventType(Enum):
    """Dynamic world events"""
    MONSTER_INVASION = "monster_invasion"
    MERCHANT_CARAVAN = "merchant_caravan"
    MYSTICAL_PHENOMENON = "mystical_phenomenon"
    WEATHER_EVENT = "weather_event"
    POLITICAL_EVENT = "political_event"
    DISCOVERY = "discovery"
    FESTIVAL = "festival"
    CRISIS = "crisis"

@dataclass
class WorldNode:
    """Individual node in the world grid"""
    x: int
    y: int
    biome: BiomeType
    elevation: float
    temperature: float
    humidity: float
    resources: Dict[str, float] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    discovered: bool = False

@dataclass
class Location:
    """Detailed location within a world"""
    id: str
    name: str
    type: LocationType
    position: Dict[str, float]
    size: str  # small, medium, large, massive
    population: int
    description: str
    factions: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    quests: List[str] = field(default_factory=list)
    npcs: List[Dict[str, Any]] = field(default_factory=list)
    dangers: List[Dict[str, Any]] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)

@dataclass
class World:
    """Complete generated world"""
    id: str
    name: str
    theme: str
    size: str  # small, medium, large, massive
    grid_size: int
    nodes: List[List[WorldNode]] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    factions: List[Dict[str, Any]] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    active_events: List[Dict[str, Any]] = field(default_factory=list)
    ecosystem: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorldEvent:
    """Dynamic world event"""
    id: str
    type: WorldEventType
    name: str
    description: str
    location: str
    duration: int  # in minutes
    impact: Dict[str, Any] = field(default_factory=dict)
    participants: List[str] = field(default_factory=list)
    rewards: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

class WorldGenerationDemo:
    """Showcases procedural world generation capabilities"""

    def __init__(self):
        self.worlds = {}
        self.generation_algorithms = self._initialize_algorithms()
        self.biome_templates = self._load_biome_templates()
        self.location_templates = self._load_location_templates()
        self.event_templates = self._load_event_templates()
        self.ecosystem_rules = self._load_ecosystem_rules()

    def _initialize_algorithms(self) -> Dict[str, Any]:
        """Initialize world generation algorithms"""
        return {
            'perlin_noise': self._perlin_noise_generator,
            'cellular_automata': self._cellular_automata_generator,
            'voronoi': self._voronoi_generator,
            'diamond_square': self._diamond_square_generator
        }

    def _load_biome_templates(self) -> Dict[BiomeType, Dict[str, Any]]:
        """Load biome generation templates"""
        return {
            BiomeType.FOREST: {
                'elevation_range': (0.2, 0.7),
                'temperature_range': (0.3, 0.8),
                'humidity_range': (0.5, 0.9),
                'resources': {'wood': 0.8, 'herbs': 0.6, 'animals': 0.7},
                'features': ['trees', 'streams', 'clearings', 'wildlife'],
                'color': '#228B22'
            },
            BiomeType.DESERT: {
                'elevation_range': (0.1, 0.5),
                'temperature_range': (0.7, 1.0),
                'humidity_range': (0.0, 0.3),
                'resources': {'sand': 0.9, 'ores': 0.4, 'oasis': 0.1},
                'features': ['dunes', 'oasis', 'rock_formations', 'ancient_ruins'],
                'color': '#F4A460'
            },
            BiomeType.MOUNTAINS: {
                'elevation_range': (0.6, 1.0),
                'temperature_range': (0.1, 0.6),
                'humidity_range': (0.2, 0.6),
                'resources': {'stone': 0.9, 'ores': 0.8, 'crystals': 0.3},
                'features': ['peaks', 'valleys', 'caves', 'waterfalls'],
                'color': '#8B7355'
            },
            BiomeType.OCEAN: {
                'elevation_range': (0.0, 0.3),
                'temperature_range': (0.4, 0.9),
                'humidity_range': (0.8, 1.0),
                'resources': {'fish': 0.8, 'pearls': 0.2, 'coral': 0.5},
                'features': ['waves', 'islands', 'reefs', 'depths'],
                'color': '#4682B4'
            },
            BiomeType.TUNDRA: {
                'elevation_range': (0.3, 0.8),
                'temperature_range': (0.0, 0.3),
                'humidity_range': (0.3, 0.7),
                'resources': {'ice': 0.9, 'fur': 0.6, 'rare_minerals': 0.4},
                'features': ['ice_fields', 'frozen_lakes', 'snow_forests', 'aurora'],
                'color': '#B0E0E6'
            },
            BiomeType.JUNGLE: {
                'elevation_range': (0.2, 0.6),
                'temperature_range': (0.8, 1.0),
                'humidity_range': (0.8, 1.0),
                'resources': {'exotic_wood': 0.9, 'rare_herbs': 0.7, 'fruits': 0.8},
                'features': ['canopy', 'ruins', 'waterfalls', 'exotic_wildlife'],
                'color': '#006400'
            },
            BiomeType.VOLCANIC: {
                'elevation_range': (0.5, 0.9),
                'temperature_range': (0.8, 1.0),
                'humidity_range': (0.0, 0.4),
                'resources': {'lava_crystals': 0.8, 'obsidian': 0.9, 'rare_metals': 0.6},
                'features': ['volcanoes', 'lava_flows', 'ash_clouds', 'mineral_veins'],
                'color': '#8B0000'
            },
            BiomeType.MYSTICAL: {
                'elevation_range': (0.1, 0.9),
                'temperature_range': (0.2, 0.8),
                'humidity_range': (0.4, 0.8),
                'resources': {'magical_energy': 0.9, 'essence': 0.7, 'ancient_knowledge': 0.5},
                'features': ['floating_islands', 'magical_auras', 'ancient_structures', 'portals'],
                'color': '#9400D3'
            }
        }

    def _load_location_templates(self) -> Dict[LocationType, Dict[str, Any]]:
        """Load location generation templates"""
        return {
            LocationType.CITY: {
                'size_range': ('large', 'massive'),
                'population_range': (5000, 50000),
                'services': ['market', 'tavern', 'forge', 'temple', 'guild_hall', 'bank'],
                'features': ['walls', 'districts', 'landmarks', 'sewers'],
                'biome_preference': [BiomeType.FOREST, BiomeType.SAVANNAH, BiomeType.MYSTICAL]
            },
            LocationType.VILLAGE: {
                'size_range': ('small', 'medium'),
                'population_range': (100, 2000),
                'services': ['tavern', 'general_store', 'blacksmith'],
                'features': ['well', 'farms', 'meeting_hall', 'shrine'],
                'biome_preference': [BiomeType.FOREST, BiomeType.SAVANNAH, BiomeType.MOUNTAINS]
            },
            LocationType.DUNGEON: {
                'size_range': ('small', 'medium'),
                'population_range': (0, 50),
                'services': [],
                'features': ['traps', 'puzzles', 'treasure', 'monsters', 'secrets'],
                'biome_preference': [BiomeType.MOUNTAINS, BiomeType.VOLCANIC, BiomeType.MYSTICAL]
            },
            LocationType.TEMPLE: {
                'size_range': ('medium', 'large'),
                'population_range': (10, 100),
                'services': ['blessings', 'training', 'quests'],
                'features': ['altars', 'relics', 'guardians', 'sacred_texts'],
                'biome_preference': [BiomeType.MOUNTAINS, BiomeType.JUNGLE, BiomeType.MYSTICAL]
            },
            LocationType.RUINS: {
                'size_range': ('small', 'large'),
                'population_range': (0, 20),
                'services': ['lore', 'exploration'],
                'features': ['ancient_artifacts', 'secrets', 'dangers', 'history'],
                'biome_preference': list(BiomeType)  # Can appear anywhere
            },
            LocationType.FORTRESS: {
                'size_range': ('medium', 'large'),
                'population_range': (50, 500),
                'services': ['training', 'equipment', 'tactics'],
                'features': ['walls', 'garrison', 'armory', 'command_center'],
                'biome_preference': [BiomeType.MOUNTAINS, BiomeType.DESERT, BiomeType.TUNDRA]
            }
        }

    def _load_event_templates(self) -> Dict[WorldEventType, Dict[str, Any]]:
        """Load world event templates"""
        return {
            WorldEventType.MONSTER_INVASION: {
                'duration_range': (30, 180),
                'impact': {'danger': 0.8, 'opportunity': 0.6},
                'locations': ['village', 'city', 'fortress'],
                'description': 'Monsters are attacking nearby settlements!'
            },
            WorldEventType.MERCHANT_CARAVAN: {
                'duration_range': (60, 240),
                'impact': {'economy': 0.7, 'opportunity': 0.8},
                'locations': ['city', 'village'],
                'description': 'A merchant caravan has arrived with rare goods!'
            },
            WorldEventType.MYSTICAL_PHENOMENON: {
                'duration_range': (15, 90),
                'impact': ['magic', 'discovery'],
                'locations': ['temple', 'ruins', 'mystical_area'],
                'description': 'Strange magical energies are affecting the area!'
            },
            WorldEventType.WEATHER_EVENT: {
                'duration_range': (20, 120),
                'impact': ['environment', 'movement'],
                'locations': ['outdoors', 'wilderness'],
                'description': 'Extreme weather conditions are affecting travel!'
            }
        }

    def _load_ecosystem_rules(self) -> Dict[str, Any]:
        """Load ecosystem simulation rules"""
        return {
            'predator_prey': {
                'balance_factor': 0.1,
                'migration_threshold': 0.7,
                'reproduction_rate': 0.05
            },
            'resource_regeneration': {
                'base_rate': 0.02,
                'biome_modifiers': {
                    BiomeType.FOREST: 1.5,
                    BiomeType.DESERT: 0.3,
                    BiomeType.OCEAN: 1.2,
                    BiomeType.VOLCANIC: 0.5
                }
            },
            'npc_behavior': {
                'daily_routines': True,
                'social_interactions': True,
                'response_to_events': True,
                'learning_rate': 0.01
            }
        }

    async def generate_world(self, world_theme: str, size: str = "medium") -> Dict[str, Any]:
        """Generate a complete procedural world"""
        logger.info(f"🌍 Generating {size} {world_theme} world...")

        world_id = f"world_{len(self.worlds) + 1:04d}"
        grid_size = self._get_grid_size(size)

        # Generate base world
        world = World(
            id=world_id,
            name=self._generate_world_name(world_theme),
            theme=world_theme,
            size=size,
            grid_size=grid_size
        )

        # Generate world grid
        print(f"  🗺️  Generating world grid ({grid_size}x{grid_size})...")
        await self._generate_world_grid(world)

        # Generate locations
        print(f"  🏘️  Generating locations...")
        await self._generate_world_locations(world)

        # Generate factions
        print(f"  ⚔️  Generating factions...")
        await self._generate_world_factions(world)

        # Generate ecosystem
        print(f"  🦋 Generating ecosystem...")
        await self._generate_ecosystem(world)

        # Generate initial events
        print(f"  🎭 Initializing world events...")
        await self._initialize_world_events(world)

        # Store world
        self.worlds[world_id] = world

        # Display world summary
        total_locations = len(world.locations)
        biome_distribution = self._calculate_biome_distribution(world)

        print(f"    ✅ World '{world.name}' generated successfully!")
        print(f"    📊 {total_locations} locations across {len(set(b for row in world.nodes for b in [node.biome]))} biomes")
        print(f"    🏰 {len([l for l in world.locations if l.type == LocationType.CITY])} cities")
        print(f"    🏘️  {len([l for l in world.locations if l.type == LocationType.VILLAGE])} villages")
        print(f"    ⚔️  {len(world.factions)} active factions")
        print(f"    🎭 {len(world.active_events)} current events")

        return {
            'world_id': world_id,
            'name': world.name,
            'theme': world_theme,
            'size': size,
            'grid_size': grid_size,
            'locations': total_locations,
            'biomes': biome_distribution,
            'factions': len(world.factions),
            'events': len(world.active_events),
            'summary': f"Generated {size} {world_theme} world with {total_locations} locations"
        }

    def _get_grid_size(self, size: str) -> int:
        """Get grid size based on world size"""
        size_map = {
            'small': 32,
            'medium': 64,
            'large': 128,
            'massive': 256
        }
        return size_map.get(size, 64)

    def _generate_world_name(self, theme: str) -> str:
        """Generate world name based on theme"""
        prefixes = {
            'fantasy': ['Ancient', 'Mystical', 'Forgotten', 'Legendary', 'Enchanted'],
            'sci_fi': ['Quantum', 'Cyber', 'Neural', 'Stellar', 'Quantum'],
            'post_apocalyptic': ['Broken', 'Scorched', 'Fallen', 'Wasted', 'Ravaged'],
            'steampunk': ['Clockwork', 'Steam', 'Mechanical', 'Industrial', 'Victorian']
        }

        suffixes = [
            'Realm', 'World', 'Lands', 'Kingdom', 'Empire',
            'Dominion', 'Territory', 'Province', 'Nation', 'Domain'
        ]

        theme_prefixes = prefixes.get(theme, ['Mysterious', 'Unknown'])
        prefix = random.choice(theme_prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix} {suffix}"

    async def _generate_world_grid(self, world: World) -> None:
        """Generate world grid with biomes and features"""
        grid_size = world.grid_size
        algorithm = random.choice(list(self.generation_algorithms.keys()))

        # Generate height map using selected algorithm
        height_map = await self.generation_algorithms[algorithm](grid_size, grid_size)

        # Generate temperature map
        temp_map = await self._perlin_noise_generator(grid_size, grid_size, frequency=0.05)

        # Generate humidity map
        humidity_map = await self._perlin_noise_generator(grid_size, grid_size, frequency=0.08)

        # Generate nodes
        world.nodes = []
        for y in range(grid_size):
            row = []
            for x in range(grid_size):
                # Determine biome based on conditions
                elevation = height_map[y][x]
                temperature = temp_map[y][x]
                humidity = humidity_map[y][x]

                biome = self._determine_biome(elevation, temperature, humidity, world.theme)

                # Generate resources for this node
                resources = self._generate_node_resources(biome, elevation)

                # Generate features
                features = self._generate_node_features(biome, elevation)

                node = WorldNode(
                    x=x, y=y,
                    biome=biome,
                    elevation=elevation,
                    temperature=temperature,
                    humidity=humidity,
                    resources=resources,
                    features=features
                )

                row.append(node)
            world.nodes.append(row)

    def _determine_biome(self, elevation: float, temperature: float, humidity: float, theme: str) -> BiomeType:
        """Determine biome based on environmental conditions"""
        # Special handling for theme
        if theme == 'mystical' and random.random() < 0.15:
            return BiomeType.MYSTICAL

        # Standard biome determination
        if elevation < 0.3:
            return BiomeType.OCEAN
        elif elevation > 0.8:
            if temperature > 0.7:
                return BiomeType.VOLCANIC
            else:
                return BiomeType.MOUNTAINS
        elif temperature < 0.3:
            if humidity < 0.4:
                return BiomeType.TUNDRA
            else:
                return BiomeType.MOUNTAINS
        elif temperature > 0.8:
            if humidity > 0.7:
                return BiomeType.JUNGLE
            else:
                return BiomeType.DESERT
        elif humidity > 0.7:
            return BiomeType.FOREST
        elif humidity < 0.3:
            return BiomeType.DESERT
        else:
            return BiomeType.SAVANNAH

    def _generate_node_resources(self, biome: BiomeType, elevation: float) -> Dict[str, float]:
        """Generate resources for a world node"""
        biome_template = self.biome_templates[biome]
        resources = {}

        for resource, base_chance in biome_template['resources'].items():
            # Modify chance based on elevation
            elevation_modifier = 1.0 + (elevation - 0.5) * 0.5
            final_chance = base_chance * elevation_modifier
            final_chance = max(0.0, min(1.0, final_chance))

            if random.random() < final_chance:
                quantity = random.uniform(0.3, 1.0)
                resources[resource] = quantity

        return resources

    def _generate_node_features(self, biome: BiomeType, elevation: float) -> List[str]:
        """Generate features for a world node"""
        biome_template = self.biome_templates[biome]
        available_features = biome_template['features']

        # Select 1-3 features based on probability
        num_features = random.randint(1, min(3, len(available_features)))
        selected_features = random.sample(available_features, num_features)

        return selected_features

    async def _generate_world_locations(self, world: World) -> None:
        """Generate locations within the world"""
        grid_size = world.grid_size
        num_locations = self._calculate_num_locations(world.size)

        for i in range(num_locations):
            location_type = self._select_location_type(world.theme)
            location = await self._generate_single_location(world, location_type, i)
            world.locations.append(location)

    def _calculate_num_locations(self, size: str) -> int:
        """Calculate number of locations based on world size"""
        location_counts = {
            'small': random.randint(8, 15),
            'medium': random.randint(15, 30),
            'large': random.randint(30, 60),
            'massive': random.randint(60, 120)
        }
        return location_counts.get(size, 20)

    def _select_location_type(self, theme: str) -> LocationType:
        """Select location type based on theme and probability"""
        # Theme-based weights
        weights = {
            'fantasy': {
                LocationType.CITY: 0.2, LocationType.VILLAGE: 0.3, LocationType.DUNGEON: 0.2,
                LocationType.TEMPLE: 0.15, LocationType.RUINS: 0.1, LocationType.FORTRESS: 0.05
            },
            'sci_fi': {
                LocationType.CITY: 0.3, LocationType.VILLAGE: 0.2, LocationType.DUNGEON: 0.15,
                LocationType.TEMPLE: 0.1, LocationType.RUINS: 0.15, LocationType.FORTRESS: 0.1
            },
            'post_apocalyptic': {
                LocationType.CITY: 0.1, LocationType.VILLAGE: 0.25, LocationType.DUNGEON: 0.1,
                LocationType.TEMPLE: 0.05, LocationType.RUINS: 0.35, LocationType.FORTRESS: 0.15
            },
            'steampunk': {
                LocationType.CITY: 0.25, LocationType.VILLAGE: 0.25, LocationType.DUNGEON: 0.15,
                LocationType.TEMPLE: 0.1, LocationType.RUINS: 0.15, LocationType.FORTRESS: 0.1
            }
        }

        theme_weights = weights.get(theme, weights['fantasy'])
        location_types = list(theme_weights.keys())
        probabilities = list(theme_weights.values())

        return random.choices(location_types, weights=probabilities)[0]

    async def _generate_single_location(self, world: World, location_type: LocationType, index: int) -> Location:
        """Generate a single location"""
        template = self.location_templates[location_type]

        # Find suitable position
        position = self._find_suitable_location_position(world, location_type)

        # Generate location properties
        size = random.choice(template['size_range'])
        population = random.randint(*template['population_range'])
        services = template['services'].copy()

        # Add random additional services
        additional_services = ['stables', 'library', 'arena', 'market', 'inn', 'training_grounds']
        for _ in range(random.randint(0, 2)):
            if random.random() < 0.3:
                services.append(random.choice(additional_services))

        # Generate name
        name = self._generate_location_name(location_type, position, world.theme)

        # Generate description
        description = self._generate_location_description(location_type, size, world.theme)

        # Generate NPCs
        npcs = await self._generate_location_npcs(location_type, population, world.theme)

        # Generate dangers
        dangers = await self._generate_location_dangers(location_type, world.theme)

        # Generate secrets
        secrets = self._generate_location_secrets(location_type, size)

        return Location(
            id=f"loc_{index+1:04d}",
            name=name,
            type=location_type,
            position=position,
            size=size,
            population=population,
            description=description,
            services=services,
            npcs=npcs,
            dangers=dangers,
            secrets=secrets
        )

    def _find_suitable_location_position(self, world: World, location_type: LocationType) -> Dict[str, float]:
        """Find suitable position for a location"""
        grid_size = world.grid_size
        template = self.location_templates[location_type]
        preferred_biomes = template.get('biome_preference', list(BiomeType))

        # Try to find position in preferred biome
        for _ in range(100):  # Max attempts
            x = random.randint(2, grid_size - 3)
            y = random.randint(2, grid_size - 3)
            node = world.nodes[y][x]

            if node.biome in preferred_biomes:
                return {'x': float(x), 'y': float(y), 'z': node.elevation * 100}

        # Fallback to any position
        x = random.randint(2, grid_size - 3)
        y = random.randint(2, grid_size - 3)
        node = world.nodes[y][x]

        return {'x': float(x), 'y': float(y), 'z': node.elevation * 100}

    def _generate_location_name(self, location_type: LocationType, position: Dict[str, float], theme: str) -> str:
        """Generate location name"""
        prefixes = {
            LocationType.CITY: ['Grand', 'Royal', 'Capital', 'Crown', 'Golden'],
            LocationType.VILLAGE: ['Peaceful', 'Quiet', 'Small', 'Humble', 'Green'],
            LocationType.DUNGEON: ['Dark', 'Forgotten', 'Ancient', 'Cursed', 'Shadow'],
            LocationType.TEMPLE: ['Sacred', 'Holy', 'Divine', 'Blessed', 'Ancient'],
            LocationType.RUINS: ['Fallen', 'Broken', 'Lost', 'Ancient', 'Abandoned'],
            LocationType.FORTRESS: ['Strong', 'Mighty', 'Iron', 'Stone', 'Guardian']
        }

        suffixes = {
            LocationType.CITY: ['City', 'Town', 'Metropolis', 'Capital', 'Haven'],
            LocationType.VILLAGE: ['Village', 'Hamlet', 'Settlement', 'Crossroads', 'Outpost'],
            LocationType.DUNGEON: ['Dungeon', 'Labyrinth', 'Depths', 'Underground', 'Maze'],
            LocationType.TEMPLE: ['Temple', 'Shrine', 'Sanctuary', 'Altar', 'Monastery'],
            LocationType.RUINS: ['Ruins', 'Remains', 'Wreckage', 'Remnants', 'Relics'],
            LocationType.FORTRESS: ['Fortress', 'Keep', 'Castle', 'Stronghold', 'Citadel']
        }

        location_prefixes = prefixes.get(location_type, ['Mysterious'])
        location_suffixes = suffixes.get(location_type, ['Place'])

        prefix = random.choice(location_prefixes)
        suffix = random.choice(location_suffixes)

        # Add descriptor based on position
        descriptor = ""
        if position['x'] < world.grid_size * 0.3:
            descriptor = "Western "
        elif position['x'] > world.grid_size * 0.7:
            descriptor = "Eastern "
        if position['y'] < world.grid_size * 0.3:
            descriptor = "Northern " + descriptor
        elif position['y'] > world.grid_size * 0.7:
            descriptor = "Southern " + descriptor

        return f"{descriptor}{prefix} {suffix}"

    def _generate_location_description(self, location_type: LocationType, size: str, theme: str) -> str:
        """Generate location description"""
        size_descriptors = {
            'small': 'A quaint',
            'medium': 'A bustling',
            'large': 'A magnificent',
            'massive': 'An enormous'
        }

        type_descriptors = {
            LocationType.CITY: 'urban center filled with merchants, adventurers, and opportunities',
            LocationType.VILLAGE: 'peaceful settlement where everyone knows their neighbors',
            LocationType.DUNGEON: 'dangerous underground complex filled with monsters and treasure',
            LocationType.TEMPLE: 'sacred place of worship and contemplation',
            LocationType.RUINS: 'mysterious remnant of a forgotten civilization',
            LocationType.FORTRESS: 'heavily defended military installation'
        }

        size_desc = size_descriptors.get(size, 'A unique')
        type_desc = type_descriptors.get(location_type, 'interesting location')

        return f"{size_desc} {type_desc}. This place holds many secrets and adventures for those brave enough to explore."

    async def _generate_location_npcs(self, location_type: LocationType, population: int, theme: str) -> List[Dict[str, Any]]:
        """Generate NPCs for a location"""
        num_npcs = min(population // 10, 20)  # 10% of population, max 20
        npcs = []

        npc_roles = {
            LocationType.CITY: ['merchant', 'guard', 'noble', 'scholar', 'artisan', 'priest'],
            LocationType.VILLAGE: ['farmer', 'blacksmith', 'innkeeper', 'elder', 'hunter'],
            LocationType.DUNGEON: ['monster', 'guardian', 'trapped_soul', 'ancient_spirit'],
            LocationType.TEMPLE: ['priest', 'monk', 'pilgrim', 'guardian', 'oracle'],
            LocationType.RUINS: ['ghost', 'treasure_hunter', 'scholar', 'monster'],
            LocationType.FORTRESS: ['soldier', 'commander', 'blacksmith', 'scout', 'tactical_officer']
        }

        available_roles = npc_roles.get(location_type, ['wanderer'])

        for i in range(num_npcs):
            npc = {
                'id': f"npc_{i+1:04d}",
                'name': f"NPC {i+1}",
                'role': random.choice(available_roles),
                'personality': random.choice(['friendly', 'grumpy', 'mysterious', 'helpful', 'suspicious']),
                'dialogue_available': random.choice([True, False]),
                'quests_available': random.randint(0, 2),
                'trading_possible': location_type in [LocationType.CITY, LocationType.VILLAGE]
            }
            npcs.append(npc)

        return npcs

    async def _generate_location_dangers(self, location_type: LocationType, theme: str) -> List[Dict[str, Any]]:
        """Generate dangers for a location"""
        danger_types = {
            LocationType.CITY: ['thieves', 'political_intrigue', 'overcrowding', 'disease'],
            LocationType.VILLAGE: ['monsters', 'bandits', 'harsh_weather', 'resource_shortage'],
            LocationType.DUNGEON: ['monsters', 'traps', 'curses', 'environmental_hazards'],
            LocationType.TEMPLE: ['guardians', 'cursed_artifacts', 'divine_trials', 'heretics'],
            LocationType.RUINS: ['structural_collapse', 'ancient_curses', 'monsters', 'traps'],
            LocationType.FORTRESS: ['siege', 'betrayal', 'equipment_failure', 'enemy_infiltration']
        }

        available_dangers = danger_types.get(location_type, ['unknown_dangers'])
        num_dangers = random.randint(0, 3)

        dangers = []
        for i in range(num_dangers):
            danger = {
                'type': random.choice(available_dangers),
                'severity': random.choice(['minor', 'moderate', 'major', 'deadly']),
                'description': f"A dangerous situation that requires attention",
                'mitigation_available': random.choice([True, False])
            }
            dangers.append(danger)

        return dangers

    def _generate_location_secrets(self, location_type: LocationType, size: str) -> List[str]:
        """Generate secrets for a location"""
        secret_templates = [
            "Hidden treasure chamber beneath the main building",
            "Ancient prophecy written in the walls",
            "Secret passage leading to unknown destinations",
            "Powerful artifact hidden in plain sight",
            "Underground resistance movement operating from here",
            "Portal to another realm that opens under specific conditions",
            "Cursed item that influences the location's fate",
            "Hidden society meeting in secret"
        ]

        num_secrets = {
            'small': random.randint(0, 1),
            'medium': random.randint(0, 2),
            'large': random.randint(1, 3),
            'massive': random.randint(2, 4)
        }

        return random.sample(secret_templates, num_secrets.get(size, 1))

    async def _generate_world_factions(self, world: World) -> None:
        """Generate factions for the world"""
        num_factions = random.randint(3, 8)

        faction_types = ['military', 'religious', 'merchant', 'scholarly', 'criminal', 'mystical']

        for i in range(num_factions):
            faction_type = random.choice(faction_types)
            faction = {
                'id': f"faction_{i+1:04d}",
                'name': self._generate_faction_name(faction_type, world.theme),
                'type': faction_type,
                'influence': random.randint(10, 100),
                'members': random.randint(50, 5000),
                'goals': self._generate_faction_goals(faction_type),
                'relations': {},  # Will be filled after all factions created
                'headquarters': random.choice(world.locations).id if world.locations else None,
                'resources': {
                    'wealth': random.randint(1000, 100000),
                    'military': random.randint(100, 10000),
                    'influence': random.randint(10, 100),
                    'knowledge': random.randint(0, 100)
                }
            }
            world.factions.append(faction)

        # Generate faction relationships
        for i, faction in enumerate(world.factions):
            for j, other_faction in enumerate(world.factions):
                if i != j:
                    relationship = random.randint(-100, 100)
                    faction['relations'][other_faction['id']] = relationship

    def _generate_faction_name(self, faction_type: str, theme: str) -> str:
        """Generate faction name"""
        prefixes = {
            'military': ['Iron', 'Steel', 'Warrior', 'Battle', 'Storm'],
            'religious': ['Holy', 'Sacred', 'Divine', 'Blessed', 'Righteous'],
            'merchant': ['Golden', 'Silver', 'Trade', 'Commerce', 'Wealth'],
            'scholarly': ['Learned', 'Wise', 'Knowledge', 'Ancient', 'Scholar'],
            'criminal': ['Shadow', 'Dark', 'Silent', 'Hidden', 'Thieves'],
            'mystical': ['Mystic', 'Arcane', 'Magical', 'Ethereal', 'Cosmic']
        }

        suffixes = ['Brotherhood', 'Guild', 'Order', 'League', 'Alliance', 'Syndicate', 'Circle']

        faction_prefixes = prefixes.get(faction_type, ['Mysterious'])
        prefix = random.choice(faction_prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix} {suffix}"

    def _generate_faction_goals(self, faction_type: str) -> List[str]:
        """Generate faction goals based on type"""
        goal_templates = {
            'military': ['Control territory', 'Eliminate rivals', 'Establish dominance'],
            'religious': ['Spread faith', 'Protect holy sites', 'Convert followers'],
            'merchant': ['Control trade routes', 'Accumulate wealth', 'Establish markets'],
            'scholarly': ['Discover ancient knowledge', 'Preserve history', 'Advance learning'],
            'criminal': ['Control underworld', 'Profit from illegal activities', 'Avoid authorities'],
            'mystical': ['Uncover magical secrets', 'Harness magical power', 'Protect magical artifacts']
        }

        available_goals = goal_templates.get(faction_type, ['Survive and prosper'])
        return random.sample(available_goals, random.randint(1, 3))

    async def _generate_ecosystem(self, world: World) -> None:
        """Generate world ecosystem"""
        ecosystem = {
            'wildlife_populations': {},
            'resource_levels': {},
            'weather_patterns': {},
            'migration_routes': [],
            'predator_prey_balance': 0.5,
            'seasonal_changes': True
        }

        # Generate wildlife populations for each biome
        biome_counts = {}
        for row in world.nodes:
            for node in row:
                biome_counts[node.biome] = biome_counts.get(node.biome, 0) + 1

        for biome, count in biome_counts.items():
            if biome != BiomeType.OCEAN:
                population = int(count * random.uniform(10, 100))
                ecosystem['wildlife_populations'][biome.value] = population

        # Generate resource levels
        for biome_type in BiomeType:
            if biome_type != BiomeType.OCEAN:
                ecosystem['resource_levels'][biome_type.value] = random.uniform(0.3, 1.0)

        # Generate weather patterns
        ecosystem['weather_patterns'] = {
            'temperature_variation': random.uniform(0.1, 0.3),
            'humidity_variation': random.uniform(0.1, 0.4),
            'storm_frequency': random.uniform(0.05, 0.2),
            'seasonal_intensity': random.uniform(0.3, 0.8)
        }

        world.ecosystem = ecosystem

    async def _initialize_world_events(self, world: World) -> None:
        """Initialize world events"""
        num_events = random.randint(2, 5)

        for i in range(num_events):
            event_type = random.choice(list(WorldEventType))
            event = await self._generate_world_event(event_type, world)
            world.active_events.append(event)

    async def _generate_world_event(self, event_type: WorldEventType, world: World) -> WorldEvent:
        """Generate a single world event"""
        template = self.event_templates[event_type]

        # Select location for event
        if world.locations:
            location = random.choice(world.locations)
            location_name = location.name
        else:
            location_name = "Unknown Location"

        event = WorldEvent(
            id=f"event_{len(world.active_events) + 1:04d}",
            type=event_type,
            name=self._generate_event_name(event_type),
            description=template['description'],
            location=location_name,
            duration=random.randint(*template['duration_range']),
            impact=template['impact']
        )

        return event

    def _generate_event_name(self, event_type: WorldEventType) -> str:
        """Generate event name based on type"""
        name_templates = {
            WorldEventType.MONSTER_INVASION: ['Goblin Raid', 'Orc Attack', 'Dragon Sightings', 'Undead Uprising'],
            WorldEventType.MERCHANT_CARAVAN: ['Rare Goods Arrival', 'Exotic Trade', 'Luxury Convoy', 'Market Day'],
            WorldEventType.MYSTICAL_PHENOMENON: ['Aurora Borealis', 'Magical Surge', 'Spirit Awakening', 'Portal Opening'],
            WorldEventType.WEATHER_EVENT: ['Great Storm', 'Heat Wave', 'Blizzard', 'Flood Warning'],
            WorldEventType.POLITICAL_EVENT: ['Royal Decree', 'Treaty Signing', 'Rebellion', 'Alliance Formation'],
            WorldEventType.DISCOVERY: ['Ancient Ruins Found', 'New Trade Route', 'Hidden Valley', 'Lost Technology'],
            WorldEventType.FESTIVAL: ['Harvest Festival', 'New Year Celebration', 'Victory Day', 'Religious Holiday'],
            WorldEventType.CRISIS: ['Plague Outbreak', 'Famine Warning', 'Economic Collapse', 'Military Defeat']
        }

        available_names = name_templates.get(event_type, ['Mysterious Event'])
        return random.choice(available_names)

    def _calculate_biome_distribution(self, world: World) -> Dict[str, int]:
        """Calculate distribution of biomes in the world"""
        biome_counts = {}
        for row in world.nodes:
            for node in row:
                biome_counts[node.biome.value] = biome_counts.get(node.biome.value, 0) + 1
        return biome_counts

    # Noise generation algorithms
    async def _perlin_noise_generator(self, width: int, height: int, frequency: float = 0.1) -> List[List[float]]:
        """Generate Perlin noise map"""
        noise_map = []
        for y in range(height):
            row = []
            for x in range(width):
                # Simple pseudo-Perlin noise using sine waves
                value = (math.sin(x * frequency) + math.sin(y * frequency) +
                        math.sin((x + y) * frequency * 0.5)) / 3
                # Normalize to 0-1
                value = (value + 1) / 2
                row.append(value)
            noise_map.append(row)
        return noise_map

    async def _cellular_automata_generator(self, width: int, height: int) -> List[List[float]]:
        """Generate map using cellular automata"""
        # Initialize random map
        grid = [[random.random() for _ in range(width)] for _ in range(height)]

        # Apply cellular automata rules
        for _ in range(5):
            new_grid = [[0 for _ in range(width)] for _ in range(height)]
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    # Count neighbors
                    neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            if grid[y + dy][x + dx] > 0.5:
                                neighbors += 1

                    # Apply rule
                    if grid[y][x] > 0.5:
                        new_grid[y][x] = 0.8 if neighbors >= 4 else 0.3
                    else:
                        new_grid[y][x] = 0.7 if neighbors >= 5 else 0.2

            grid = new_grid

        return grid

    async def _voronoi_generator(self, width: int, height: int) -> List[List[float]]:
        """Generate Voronoi diagram-based map"""
        # Generate random points
        num_points = random.randint(10, 20)
        points = []
        for _ in range(num_points):
            points.append({
                'x': random.randint(0, width - 1),
                'y': random.randint(0, height - 1),
                'value': random.random()
            })

        # Generate Voronoi map
        voronoi_map = []
        for y in range(height):
            row = []
            for x in range(width):
                # Find nearest point
                min_dist = float('inf')
                nearest_value = 0

                for point in points:
                    dist = math.sqrt((x - point['x'])**2 + (y - point['y'])**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_value = point['value']

                row.append(nearest_value)
            voronoi_map.append(row)

        return voronoi_map

    async def _diamond_square_generator(self, width: int, height: int) -> List[List[float]]:
        """Generate Diamond-Square algorithm map"""
        # Ensure dimensions are power of 2 + 1
        size = 1
        while size < max(width, height):
            size *= 2

        # Initialize corners
        grid = [[0 for _ in range(size + 1)] for _ in range(size + 1)]
        grid[0][0] = random.random()
        grid[0][size] = random.random()
        grid[size][0] = random.random()
        grid[size][size] = random.random()

        # Diamond-Square algorithm
        step_size = size
        roughness = 0.7

        while step_size > 1:
            half_step = step_size // 2

            # Diamond step
            for y in range(half_step, size, step_size):
                for x in range(half_step, size, step_size):
                    average = (grid[y - half_step][x - half_step] +
                              grid[y - half_step][x + half_step] +
                              grid[y + half_step][x - half_step] +
                              grid[y + half_step][x + half_step]) / 4
                    grid[y][x] = average + (random.random() - 0.5) * roughness

            # Square step
            for y in range(0, size + 1, half_step):
                for x in range((y + half_step) % step_size, size + 1, step_size):
                    average = 0
                    count = 0

                    if y - half_step >= 0:
                        average += grid[y - half_step][x]
                        count += 1
                    if y + half_step <= size:
                        average += grid[y + half_step][x]
                        count += 1
                    if x - half_step >= 0:
                        average += grid[y][x - half_step]
                        count += 1
                    if x + half_step <= size:
                        average += grid[y][x + half_step]
                        count += 1

                    if count > 0:
                        grid[y][x] = (average / count) + (random.random() - 0.5) * roughness

            step_size = half_step
            roughness *= 0.5

        # Crop to desired size and normalize
        result = []
        for y in range(height):
            row = []
            for x in range(width):
                value = grid[y][x]
                # Normalize to 0-1 range
                row.append(max(0, min(1, value)))
            result.append(row)

        return result

    async def demonstrate_world_evolution(self, world_id: str, steps: int = 10) -> Dict[str, Any]:
        """Demonstrate world evolution over time"""
        if world_id not in self.worlds:
            return {"error": "World not found"}

        world = self.worlds[world_id]
        print(f"🌍 Demonstrating world evolution for '{world.name}'...")

        evolution_log = []
        initial_state = self._capture_world_state(world)

        for step in range(steps):
            print(f"  ⏰ Time Step {step + 1}/{steps}")

            # Update ecosystem
            await self._update_ecosystem(world)

            # Process events
            await self._process_world_events(world)

            # Generate new events
            if random.random() < 0.3:  # 30% chance of new event
                new_event = await self._generate_world_event(random.choice(list(WorldEventType)), world)
                world.active_events.append(new_event)
                print(f"    🎭 New event: {new_event.name}")

            # Update factions
            await self._update_faction_dynamics(world)

            # Capture state
            current_state = self._capture_world_state(world)
            evolution_log.append({
                'step': step + 1,
                'timestamp': datetime.now().isoformat(),
                'changes': self._calculate_state_changes(initial_state, current_state),
                'active_events': len(world.active_events)
            })

            await asyncio.sleep(0.5)

        return {
            'world_id': world_id,
            'evolution_steps': steps,
            'evolution_log': evolution_log,
            'final_state': self._capture_world_state(world),
            'summary': f"World evolved over {steps} time steps with dynamic changes"
        }

    def _capture_world_state(self, world: World) -> Dict[str, Any]:
        """Capture current world state"""
        return {
            'wildlife_populations': world.ecosystem.get('wildlife_populations', {}).copy(),
            'resource_levels': world.ecosystem.get('resource_levels', {}).copy(),
            'active_events_count': len(world.active_events),
            'faction_count': len(world.factions),
            'location_count': len(world.locations)
        }

    def _calculate_state_changes(self, initial: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between world states"""
        changes = {}

        # Wildlife population changes
        if 'wildlife_populations' in initial and 'wildlife_populations' in current:
            wildlife_changes = {}
            for biome in current['wildlife_populations']:
                initial_pop = initial['wildlife_populations'].get(biome, 0)
                current_pop = current['wildlife_populations'][biome]
                wildlife_changes[biome] = current_pop - initial_pop
            changes['wildlife_changes'] = wildlife_changes

        # Resource level changes
        if 'resource_levels' in initial and 'resource_levels' in current:
            resource_changes = {}
            for biome in current['resource_levels']:
                initial_level = initial['resource_levels'].get(biome, 0.5)
                current_level = current['resource_levels'][biome]
                resource_changes[biome] = current_level - initial_level
            changes['resource_changes'] = resource_changes

        return changes

    async def _update_ecosystem(self, world: World) -> None:
        """Update world ecosystem"""
        ecosystem = world.ecosystem
        rules = self.ecosystem_rules

        # Update wildlife populations
        if 'wildlife_populations' in ecosystem:
            for biome, population in ecosystem['wildlife_populations'].items():
                # Population growth/decline
                growth_rate = rules['predator_prey']['reproduction_rate']
                ecosystem['wildlife_populations'][biome] = int(population * (1 + growth_rate))

        # Update resource levels
        if 'resource_levels' in ecosystem:
            biome_type_map = {b.value: b for b in BiomeType}
            for biome_str, level in ecosystem['resource_levels'].items():
                if biome_str in biome_type_map:
                    biome_type = biome_type_map[biome_str]
                    regeneration = rules['resource_regeneration']['base_rate']
                    biome_modifier = rules['resource_regeneration']['biome_modifiers'].get(biome_type, 1.0)
                    new_level = level + (regeneration * biome_modifier)
                    ecosystem['resource_levels'][biome_str] = min(1.0, new_level)

    async def _process_world_events(self, world: World) -> None:
        """Process active world events"""
        completed_events = []

        for event in world.active_events:
            event.duration -= 1

            if event.duration <= 0:
                completed_events.append(event)
                print(f"    ✅ Event completed: {event.name}")

        # Remove completed events
        for event in completed_events:
            world.active_events.remove(event)

    async def _update_faction_dynamics(self, world: World) -> None:
        """Update faction dynamics and relationships"""
        # Random faction relationship changes
        for faction in world.factions:
            for other_faction_id, relationship in faction['relations'].items():
                if random.random() < 0.1:  # 10% chance of relationship change
                    change = random.randint(-10, 10)
                    new_relationship = max(-100, min(100, relationship + change))
                    faction['relations'][other_faction_id] = new_relationship

    def get_world_summary(self, world_id: str) -> Dict[str, Any]:
        """Get comprehensive world summary"""
        if world_id not in self.worlds:
            return {"error": "World not found"}

        world = self.worlds[world_id]

        return {
            'world_info': {
                'id': world.id,
                'name': world.name,
                'theme': world.theme,
                'size': world.size,
                'grid_size': world.grid_size,
                'created_at': world.created_at.isoformat()
            },
            'statistics': {
                'total_locations': len(world.locations),
                'biome_distribution': self._calculate_biome_distribution(world),
                'faction_count': len(world.factions),
                'active_events': len(world.active_events)
            },
            'locations': [
                {
                    'name': loc.name,
                    'type': loc.type.value,
                    'size': loc.size,
                    'population': loc.population,
                    'services': loc.services
                } for loc in world.locations[:10]  # First 10 locations
            ],
            'factions': [
                {
                    'name': f['name'],
                    'type': f['type'],
                    'influence': f['influence'],
                    'members': f['members']
                } for f in world.factions
            ],
            'events': [
                {
                    'name': event.name,
                    'type': event.type.value,
                    'location': event.location,
                    'duration': event.duration,
                    'description': event.description
                } for event in world.active_events
            ],
            'ecosystem': world.ecosystem
        }