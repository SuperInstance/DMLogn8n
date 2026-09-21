"""
Strategic Resource Placement and Distribution System
Intelligently places resources throughout the world with realistic distribution patterns,
economic considerations, and strategic gameplay implications.
"""

import numpy as np
import random
from scipy import ndimage
from scipy.spatial import distance, Voronoi
from collections import defaultdict, deque
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class ResourceType(Enum):
    # Raw Materials
    IRON_ORE = "iron_ore"
    COPPER_ORE = "copper_ore"
    GOLD_ORE = "gold_ore"
    SILVER_ORE = "silver_ore"
    COAL = "coal"
    STONE = "stone"
    MARBLE = "marble"
    GRANITE = "granite"
    DIAMOND = "diamond"
    EMERALD = "emerald"
    RUBY = "ruby"
    SAPPHIRE = "sapphire"

    # Organic Materials
    WOOD = "wood"
    HERBS = "herbs"
    MEDICINAL_PLANTS = "medicinal_plants"
    POISONOUS_PLANTS = "poisonous_plants"
    RARE_FLOWERS = "rare_flowers"
    CROPS = "crops"
    FRUIT = "fruit"
    GRAIN = "grain"

    # Animal Products
    FUR = "fur"
    LEATHER = "leather"
    MEAT = "meat"
    HONEY = "honey"
    MILK = "milk"
    EGGS = "eggs"
    WOOL = "wool"
    IVORY = "ivory"

    # Magical/Rare Materials
    MAGIC_CRYSTALS = "magic_crystals"
    DRAGON_SCALES = "dragon_scales"
    UNICORN_HORN = "unicorn_horn"
    PHOENIX_FEATHER = "phoenix_feather"
    MOONSTONE = "moonstone"
    SUNSTONE = "sunstone"
    SOUL_GEMS = "soul_gems"

    # Special Resources
    ANCIENT_ARTIFACTS = "ancient_artifacts"
    DWARVEN_RUNESTONES = "dwarven_runestones"
    ELVEN_LUMBER = "elven_lumber"
    ORC_METAL = "orc_metal"
    GOBLIN_TECH = "goblin_tech"

class ResourceRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"
    UNIQUE = "unique"

class ResourceDensity(Enum):
    SCARCE = "scarce"
    SPARSE = "sparse"
    NORMAL = "normal"
    ABUNDANT = "abundant"
    RICH = "rich"
    MOTHERLOAD = "motherload"

class ExtractionMethod(Enum):
    SURFACE_MINING = "surface_mining"
    UNDERGROUND_MINING = "underground_mining"
    QUARRYING = "quarrying"
    LUMBERJACKING = "lumberjacking"
    HARVESTING = "harvesting"
    HUNTING = "hunting"
    GATHERING = "gathering"
    FISHING = "fishing"
    MAGICAL_EXTRACTION = "magical_extraction"

@dataclass
class ResourceNode:
    """Represents a resource deposit/gathering location"""
    resource_type: ResourceType
    position: Tuple[int, int]
    quantity: float  # Amount available
    quality: float  # 0.0 - 1.0
    density: ResourceDensity
    rarity: ResourceRarity
    extraction_method: ExtractionMethod
    extraction_difficulty: float  # 0.0 - 1.0
    regeneration_rate: float  # Per time unit
    depleted: bool = False
    discovered: bool = False
    owners: List[str] = field(default_factory=list)  # Who controls this resource
    required_tools: List[str] = field(default_factory=list)
    environmental_impact: float = 0.0  # Impact of extraction

@dataclass
class TradeRoute:
    """Represents a trade route between locations"""
    start: Tuple[int, int]
    end: Tuple[int, int]
    resources: List[ResourceType]
    route_value: float
    danger_level: float
    controlled_by: Optional[str] = None
    tolls: Dict[str, float] = field(default_factory=dict)  # faction -> toll amount

@dataclass
class ResourceMarket:
    """Represents a resource market/economy"""
    location: Tuple[int, int]
    supply: Dict[ResourceType, float] = field(default_factory=dict)
    demand: Dict[ResourceType, float] = field(default_factory=dict)
    prices: Dict[ResourceType, float] = field(default_factory=dict)
    market_type: str = "local"  # local, regional, global
    controlled_by: Optional[str] = None

class ResourcePattern:
    """Defines distribution patterns for resources"""
    def __init__(self, resource_type: ResourceType, pattern_type: str,
                 preferred_terrain: List[str], climate_preference: List[str],
                 size_range: Tuple[int, int], quantity_range: Tuple[float, float],
                 distribution_rule: str):
        self.resource_type = resource_type
        self.pattern_type = pattern_type  # clustered, scattered, linear, random
        self.preferred_terrain = preferred_terrain
        self.climate_preference = climate_preference
        self.size_range = size_range
        self.quantity_range = quantity_range
        self.distribution_rule = distribution_rule

class GeologicalSimulator:
    """Simulates geological formations for mineral deposits"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.rock_layers = None
        self.fault_lines = []
        self.mineral_veins = {}

    def simulate_geology(self, seed: Optional[int] = None) -> None:
        """Simulate geological formations"""
        if seed is not None:
            np.random.seed(seed)

        # Generate rock layers
        self._generate_rock_layers()

        # Generate fault lines
        self._generate_fault_lines()

        # Generate mineral deposits
        self._generate_mineral_deposits()

    def _generate_rock_layers(self) -> None:
        """Generate stratified rock layers"""
        # Create base rock types
        rock_types = np.array([
            0,  # Sedimentary
            1,  # Metamorphic
            2,  # Igneous
            3,  # Volcanic
            4   # Crystal
        ])

        # Generate layered structure
        self.rock_layers = np.zeros((self.height, self.width), dtype=int)

        # Create horizontal layers with some variation
        layer_heights = [self.height // 5] * 4 + [self.height - 4 * (self.height // 5)]
        current_height = 0

        for i, (rock_type, layer_h) in enumerate(zip(rock_types, layer_heights)):
            if current_height < self.height:
                end_height = min(current_height + layer_h, self.height)

                # Add some variation to layer boundaries
                for y in range(current_height, end_height):
                    variation = int(np.sin(y * 0.1) * 5)
                    for x in range(self.width):
                        rock_x = x + variation
                        if 0 <= rock_x < self.width:
                            self.rock_layers[y, rock_x] = rock_type

                current_height = end_height

        # Add some random geological intrusions
        for _ in range(5):
            cx = random.randint(0, self.width - 1)
            cy = random.randint(0, self.height - 1)
            radius = random.randint(3, 10)
            rock_type = random.randint(0, 4)

            for y in range(max(0, cy - radius), min(self.height, cy + radius)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius)):
                    if (x - cx)**2 + (y - cy)**2 <= radius**2:
                        self.rock_layers[y, x] = rock_type

    def _generate_fault_lines(self) -> None:
        """Generate geological fault lines"""
        num_faults = random.randint(3, 8)

        for _ in range(num_faults):
            # Generate fault line path
            start_x = random.randint(0, self.width - 1)
            start_y = random.randint(0, self.height - 1)

            fault_line = [(start_y, start_x)]

            current_x, current_y = start_x, start_y
            direction = random.uniform(0, 2 * math.pi)

            for _ in range(random.randint(10, 30)):
                # Move along fault line with some randomness
                direction += random.uniform(-0.5, 0.5)
                step = random.randint(1, 3)

                current_x += int(math.cos(direction) * step)
                current_y += int(math.sin(direction) * step)

                if 0 <= current_x < self.width and 0 <= current_y < self.height:
                    fault_line.append((current_y, current_x))
                else:
                    break

            self.fault_lines.append(fault_line)

    def _generate_mineral_deposits(self) -> None:
        """Generate mineral deposits based on geology"""
        # Define which minerals appear in which rock types
        mineral_rock_associations = {
            0: [ResourceType.COAL, ResourceType.IRON_ORE, ResourceType.COPPER_ORE],  # Sedimentary
            1: [ResourceType.GOLD_ORE, ResourceType.SILVER_ORE, ResourceType.MARBLE],  # Metamorphic
            2: [ResourceType.IRON_ORE, ResourceType.COPPER_ORE, ResourceType.GRANITE],  # Igneous
            3: [ResourceType.DIAMOND, ResourceType.EMERALD, ResourceType.RUBY],       # Volcanic
            4: [ResourceType.MAGIC_CRYSTALS, ResourceType.MOONSTONE, ResourceType.SUNSTONE]  # Crystal
        }

        for rock_type, minerals in mineral_rock_associations.items():
            # Find areas of this rock type
            rock_mask = (self.rock_layers == rock_type)

            # Generate deposits for each mineral
            for mineral in minerals:
                num_deposits = random.randint(1, 5)

                for _ in range(num_deposits):
                    # Find a random location in this rock type
                    rock_positions = np.argwhere(rock_mask)
                    if len(rock_positions) > 0:
                        pos = random.choice(rock_positions)
                        self.mineral_veins[mineral] = self.mineral_veins.get(mineral, [])
                        self.mineral_veins[mineral].append(pos)

class ClimateSystem:
    """Simulates climate patterns for biological resources"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.temperature_map = None
        self.humidity_map = None
        self.seasonal_variations = {}

    def simulate_climate(self, terrain_height: np.ndarray, seed: Optional[int] = None) -> None:
        """Simulate climate patterns based on terrain"""
        if seed is not None:
            np.random.seed(seed)

        # Temperature decreases with elevation
        base_temperature = 20.0  # Celsius at sea level
        temperature_lapse_rate = -6.5  # Degrees per 1000m

        # Normalize terrain to elevation in km
        max_height = np.max(terrain_height)
        terrain_km = (terrain_height / max_height) * 3.0  # Max 3km elevation

        self.temperature_map = base_temperature + terrain_km * temperature_lapse_rate

        # Add latitude variation (cooler at top/north)
        latitude_factor = np.linspace(10, -10, self.height)[:, np.newaxis]
        self.temperature_map += latitude_factor

        # Humidity increases near water and in low areas
        self.humidity_map = 0.5 + (1.0 - terrain_height / max_height) * 0.3

        # Add some noise
        self.temperature_map += np.random.normal(0, 2, (self.height, self.width))
        self.humidity_map += np.random.normal(0, 0.1, (self.height, self.width))

        # Clamp values
        self.humidity_map = np.clip(self.humidity_map, 0, 1)

    def get_seasonal_adjustment(self, season: str) -> Tuple[float, float]:
        """Get temperature and humidity adjustments for season"""
        seasonal_adjustments = {
            "spring": (0, 0.1),
            "summer": (5, -0.1),
            "autumn": (0, 0.05),
            "winter": (-10, 0)
        }
        return seasonal_adjustments.get(season, (0, 0))

class ResourceDistributor:
    """Main resource distribution system"""

    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.resource_nodes = {}
        self.trade_routes = []
        self.markets = {}
        self.geological_simulator = GeologicalSimulator(width, height)
        self.climate_system = ClimateSystem(width, height)

        self.resource_patterns = self._initialize_resource_patterns()

    def _initialize_resource_patterns(self) -> Dict[ResourceType, ResourcePattern]:
        """Initialize distribution patterns for all resources"""
        patterns = {}

        # Mineral resources
        patterns[ResourceType.IRON_ORE] = ResourcePattern(
            ResourceType.IRON_ORE, "clustered",
            ["mountain", "hills"], ["temperate", "arid"],
            (3, 8), (100, 1000), "fault_lines"
        )

        patterns[ResourceType.GOLD_ORE] = ResourcePattern(
            ResourceType.GOLD_ORE, "linear",
            ["mountain", "hills"], ["temperate"],
            (2, 5), (50, 500), "veins"
        )

        patterns[ResourceType.DIAMOND] = ResourcePattern(
            ResourceType.DIAMOND, "scattered",
            ["high_mountain"], ["arctic", "arid"],
            (1, 3), (10, 100), "volcanic"
        )

        patterns[ResourceType.COAL] = ResourcePattern(
            ResourceType.COAL, "clustered",
            ["plains", "hills"], ["temperate"],
            (5, 12), (200, 2000), "sedimentary"
        )

        # Biological resources
        patterns[ResourceType.WOOD] = ResourcePattern(
            ResourceType.WOOD, "clustered",
            ["forest", "dense_forest"], ["temperate", "tropical"],
            (8, 15), (50, 500), "forest_patches"
        )

        patterns[ResourceType.HERBS] = ResourcePattern(
            ResourceType.HERBS, "scattered",
            ["plains", "forest", "hills"], ["temperate", "tropical"],
            (3, 8), (20, 200), "random"
        )

        patterns[ResourceType.RARE_FLOWERS] = ResourcePattern(
            ResourceType.RARE_FLOWERS, "scattered",
            ["forest", "jungle", "marsh"], ["tropical", "temperate"],
            (1, 3), (5, 50), "special_locations"
        )

        # Animal products
        patterns[ResourceType.FUR] = ResourcePattern(
            ResourceType.FUR, "scattered",
            ["forest", "tundra", "mountain"], ["arctic", "temperate"],
            (4, 10), (10, 100), "wildlife_areas"
        )

        # Magical resources
        patterns[ResourceType.MAGIC_CRYSTALS] = ResourcePattern(
            ResourceType.MAGIC_CRYSTALS, "clustered",
            ["high_mountain", "deep_ocean"], ["magical"],
            (2, 6), (5, 50), "magic_nodes"
        )

        patterns[ResourceType.ANCIENT_ARTIFACTS] = ResourcePattern(
            ResourceType.ANCIENT_ARTIFACTS, "scattered",
            ["ruins", "dungeon", "ancient_forest"], ["any"],
            (1, 2), (1, 10), "historical_sites"
        )

        return patterns

    def distribute_resources(self, terrain_map: np.ndarray, biome_map: np.ndarray,
                           cities: List[Tuple[int, int]], seasons: List[str] = None) -> None:
        """Distribute resources across the world"""
        # Simulate geology and climate
        self.geological_simulator.simulate_geology(self.seed)
        self.climate_system.simulate_climate(terrain_map, self.seed + 1)

        # Distribute resources based on patterns
        for resource_type, pattern in self.resource_patterns.items():
            self._distribute_resource_type(resource_type, pattern, terrain_map, biome_map)

        # Generate trade routes between resource locations and cities
        self._generate_trade_routes(cities, terrain_map)

        # Generate markets at cities
        self._generate_markets(cities)

    def _distribute_resource_type(self, resource_type: ResourceType,
                                pattern: ResourcePattern,
                                terrain_map: np.ndarray,
                                biome_map: np.ndarray) -> None:
        """Distribute a specific resource type according to its pattern"""
        # Find suitable locations
        suitable_locations = self._find_suitable_locations(
            pattern, terrain_map, biome_map
        )

        if not suitable_locations:
            return

        # Determine number of deposits
        base_quantity = len(suitable_locations) // 20
        num_deposits = max(1, int(base_quantity * random.uniform(0.5, 1.5)))

        # Place deposits according to pattern
        if pattern.pattern_type == "clustered":
            self._place_clustered_deposits(
                resource_type, pattern, suitable_locations, num_deposits
            )
        elif pattern.pattern_type == "scattered":
            self._place_scattered_deposits(
                resource_type, pattern, suitable_locations, num_deposits
            )
        elif pattern.pattern_type == "linear":
            self._place_linear_deposits(
                resource_type, pattern, suitable_locations, num_deposits
            )
        else:  # random
            self._place_random_deposits(
                resource_type, pattern, suitable_locations, num_deposits
            )

    def _find_suitable_locations(self, pattern: ResourcePattern,
                               terrain_map: np.ndarray,
                               biome_map: np.ndarray) -> List[Tuple[int, int]]:
        """Find locations suitable for this resource type"""
        suitable_locations = []

        # Convert biome values to names
        biome_names = {
            0: "ocean", 1: "deep_ocean", 2: "beach", 3: "plains",
            4: "forest", 5: "dense_forest", 6: "jungle", 7: "desert",
            8: "savanna", 9: "tundra", 10: "ice", 11: "mountain",
            12: "high_mountain", 13: "hills", 14: "river", 15: "lake",
            16: "marsh", 17: "swamp"
        }

        for y in range(self.height):
            for x in range(self.width):
                # Check terrain preference
                biome_value = biome_map[y, x]
                biome_name = biome_names.get(biome_value, "plains")

                if biome_name in pattern.preferred_terrain:
                    # Check climate preference
                    temperature = self.climate_system.temperature_map[y, x]
                    humidity = self.climate_system.humidity_map[y, x]

                    climate_suitable = True
                    if "any" not in pattern.climate_preference:
                        if "temperate" in pattern.climate_preference:
                            if not (10 <= temperature <= 25):
                                climate_suitable = False
                        elif "arctic" in pattern.climate_preference:
                            if temperature > 5:
                                climate_suitable = False
                        elif "tropical" in pattern.climate_preference:
                            if temperature < 20:
                                climate_suitable = False
                        elif "arid" in pattern.climate_preference:
                            if humidity > 0.3:
                                climate_suitable = False

                    if climate_suitable:
                        suitable_locations.append((y, x))

        return suitable_locations

    def _place_clustered_deposits(self, resource_type: ResourceType,
                                pattern: ResourcePattern,
                                suitable_locations: List[Tuple[int, int]],
                                num_deposits: int) -> None:
        """Place resource deposits in clusters"""
        if not suitable_locations:
            return

        for _ in range(num_deposits):
            # Choose cluster center
            center = random.choice(suitable_locations)

            # Determine cluster size
            cluster_size = random.randint(*pattern.size_range)

            # Place deposits around center
            for _ in range(cluster_size):
                # Random offset from center
                max_offset = cluster_size // 2
                dy = random.randint(-max_offset, max_offset)
                dx = random.randint(-max_offset, max_offset)

                ny, nx = center[0] + dy, center[1] + dx

                # Check if location is suitable
                if (0 <= ny < self.height and 0 <= nx < self.width and
                    (ny, nx) in suitable_locations):

                    # Create resource node
                    self._create_resource_node(
                        resource_type, (ny, nx), pattern
                    )

    def _place_scattered_deposits(self, resource_type: ResourceType,
                                pattern: ResourcePattern,
                                suitable_locations: List[Tuple[int, int]],
                                num_deposits: int) -> None:
        """Place resource deposits randomly"""
        if not suitable_locations:
            return

        # Randomly select locations
        selected_locations = random.sample(
            suitable_locations, min(num_deposits, len(suitable_locations))
        )

        for location in selected_locations:
            self._create_resource_node(resource_type, location, pattern)

    def _place_linear_deposits(self, resource_type: ResourceType,
                             pattern: ResourcePattern,
                             suitable_locations: List[Tuple[int, int]],
                             num_deposits: int) -> None:
        """Place resource deposits in linear patterns (veins)"""
        if not suitable_locations:
            return

        for _ in range(num_deposits):
            # Start point
            start = random.choice(suitable_locations)

            # Direction
            angle = random.uniform(0, 2 * math.pi)

            # Create vein
            current = start
            vein_length = random.randint(*pattern.size_range)

            for _ in range(vein_length):
                if current in suitable_locations:
                    self._create_resource_node(resource_type, current, pattern)

                # Move to next position
                step = random.randint(1, 2)
                ny = current[0] + int(math.sin(angle) * step)
                nx = current[1] + int(math.cos(angle) * step)

                # Check bounds
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    current = (ny, nx)
                else:
                    break

                # Add some randomness to direction
                angle += random.uniform(-0.2, 0.2)

    def _place_random_deposits(self, resource_type: ResourceType,
                             pattern: ResourcePattern,
                             suitable_locations: List[Tuple[int, int]],
                             num_deposits: int) -> None:
        """Place resource deposits randomly"""
        self._place_scattered_deposits(resource_type, pattern, suitable_locations, num_deposits)

    def _create_resource_node(self, resource_type: ResourceType,
                            location: Tuple[int, int],
                            pattern: ResourcePattern) -> None:
        """Create a resource node at given location"""
        # Determine quantity
        quantity = random.uniform(*pattern.quantity_range)

        # Determine quality
        base_quality = 0.5
        quality = np.clip(base_quality + random.normal(0, 0.2), 0, 1)

        # Determine rarity
        rarity = self._determine_rarity(resource_type, quality)

        # Determine density
        density = self._determine_density(quantity)

        # Determine extraction method
        extraction_method = self._determine_extraction_method(resource_type, pattern)

        # Determine extraction difficulty
        extraction_difficulty = self._determine_extraction_difficulty(
            resource_type, location, extraction_method
        )

        # Determine regeneration rate
        regeneration_rate = self._determine_regeneration_rate(resource_type)

        # Determine required tools
        required_tools = self._determine_required_tools(extraction_method)

        # Create resource node
        node = ResourceNode(
            resource_type=resource_type,
            position=location,
            quantity=quantity,
            quality=quality,
            density=density,
            rarity=rarity,
            extraction_method=extraction_method,
            extraction_difficulty=extraction_difficulty,
            regeneration_rate=regeneration_rate,
            required_tools=required_tools
        )

        # Add to resource nodes
        if resource_type not in self.resource_nodes:
            self.resource_nodes[resource_type] = []
        self.resource_nodes[resource_type].append(node)

    def _determine_rarity(self, resource_type: ResourceType, quality: float) -> ResourceRarity:
        """Determine resource rarity based on type and quality"""
        base_rarity_map = {
            ResourceType.STONE: ResourceRarity.COMMON,
            ResourceType.WOOD: ResourceRarity.COMMON,
            ResourceType.COAL: ResourceRarity.COMMON,
            ResourceType.IRON_ORE: ResourceRarity.COMMON,
            ResourceType.COPPER_ORE: ResourceRarity.UNCOMMON,
            ResourceType.SILVER_ORE: ResourceRarity.RARE,
            ResourceType.GOLD_ORE: ResourceRarity.RARE,
            ResourceType.DIAMOND: ResourceRarity.VERY_RARE,
            ResourceType.MAGIC_CRYSTALS: ResourceRarity.RARE,
            ResourceType.ANCIENT_ARTIFACTS: ResourceRarity.LEGENDARY
        }

        base_rarity = base_rarity_map.get(resource_type, ResourceRarity.COMMON)

        # Adjust based on quality
        if quality > 0.9:
            rarity_values = list(ResourceRarity)
            current_index = rarity_values.index(base_rarity)
            if current_index > 0:
                base_rarity = rarity_values[current_index - 1]  # More rare
        elif quality < 0.3:
            rarity_values = list(ResourceRarity)
            current_index = rarity_values.index(base_rarity)
            if current_index < len(rarity_values) - 1:
                base_rarity = rarity_values[current_index + 1]  # Less rare

        return base_rarity

    def _determine_density(self, quantity: float) -> ResourceDensity:
        """Determine resource density based on quantity"""
        if quantity < 50:
            return ResourceDensity.SCARCE
        elif quantity < 100:
            return ResourceDensity.SPARSE
        elif quantity < 500:
            return ResourceDensity.NORMAL
        elif quantity < 1000:
            return ResourceDensity.ABUNDANT
        elif quantity < 2000:
            return ResourceDensity.RICH
        else:
            return ResourceDensity.MOTHERLOAD

    def _determine_extraction_method(self, resource_type: ResourceType,
                                   pattern: ResourcePattern) -> ExtractionMethod:
        """Determine extraction method for resource type"""
        method_map = {
            ResourceType.IRON_ORE: ExtractionMethod.UNDERGROUND_MINING,
            ResourceType.COAL: ExtractionMethod.SURFACE_MINING,
            ResourceType.GOLD_ORE: ExtractionMethod.UNDERGROUND_MINING,
            ResourceType.DIAMOND: ExtractionMethod.UNDERGROUND_MINING,
            ResourceType.STONE: ExtractionMethod.QUARRYING,
            ResourceType.WOOD: ExtractionMethod.LUMBERJACKING,
            ResourceType.HERBS: ExtractionMethod.HARVESTING,
            ResourceType.RARE_FLOWERS: ExtractionMethod.GATHERING,
            ResourceType.FUR: ExtractionMethod.HUNTING,
            ResourceType.MAGIC_CRYSTALS: ExtractionMethod.MAGICAL_EXTRACTION,
            ResourceType.ANCIENT_ARTIFACTS: ExtractionMethod.GATHERING
        }

        return method_map.get(resource_type, ExtractionMethod.GATHERING)

    def _determine_extraction_difficulty(self, resource_type: ResourceType,
                                       location: Tuple[int, int],
                                       extraction_method: ExtractionMethod) -> float:
        """Determine extraction difficulty"""
        base_difficulty = {
            ExtractionMethod.SURFACE_MINING: 0.3,
            ExtractionMethod.UNDERGROUND_MINING: 0.6,
            ExtractionMethod.QUARRYING: 0.4,
            ExtractionMethod.LUMBERJACKING: 0.2,
            ExtractionMethod.HARVESTING: 0.1,
            ExtractionMethod.HUNTING: 0.4,
            ExtractionMethod.GATHERING: 0.1,
            ExtractionMethod.FISHING: 0.2,
            ExtractionMethod.MAGICAL_EXTRACTION: 0.8
        }

        difficulty = base_difficulty.get(extraction_method, 0.3)

        # Adjust based on terrain
        y, x = location
        if hasattr(self, 'geological_simulator') and self.geological_simulator.rock_layers is not None:
            rock_type = self.geological_simulator.rock_layers[y, x]
            if rock_type == 2:  # Igneous - harder
                difficulty += 0.1
            elif rock_type == 4:  # Crystal - magical
                difficulty += 0.2

        return np.clip(difficulty + random.normal(0, 0.1), 0, 1)

    def _determine_regeneration_rate(self, resource_type: ResourceType) -> float:
        """Determine regeneration rate for renewable resources"""
        renewable_resources = {
            ResourceType.WOOD: 0.1,
            ResourceType.HERBS: 0.15,
            ResourceType.MEDICINAL_PLANTS: 0.12,
            ResourceType.RARE_FLOWERS: 0.05,
            ResourceType.CROPS: 0.2,
            ResourceType.FRUIT: 0.18,
            ResourceType.GRAIN: 0.22,
            ResourceType.MEAT: 0.0,  # Animals don't respawn at locations
            ResourceType.HONEY: 0.08
        }

        return renewable_resources.get(resource_type, 0.0)

    def _determine_required_tools(self, extraction_method: ExtractionMethod) -> List[str]:
        """Determine required tools for extraction"""
        tools_map = {
            ExtractionMethod.SURFACE_MINING: ["pickaxe", "shovel"],
            ExtractionMethod.UNDERGROUND_MINING: ["pickaxe", "lantern", "support_beams"],
            ExtractionMethod.QUARRYING: ["hammer", "chisel", "wedge"],
            ExtractionMethod.LUMBERJACKING: ["axe", "saw"],
            ExtractionMethod.HARVESTING: ["sickle", "basket"],
            ExtractionMethod.HUNTING: ["bow", "knife", "traps"],
            ExtractionMethod.GATHERING: ["knife", "bag"],
            ExtractionMethod.FISHING: ["fishing_rod", "net"],
            ExtractionMethod.MAGICAL_EXTRACTION: ["magic_wand", "protective_charms"]
        }

        return tools_map.get(extraction_method, ["basic_tools"])

    def _generate_trade_routes(self, cities: List[Tuple[int, int]],
                             terrain_map: np.ndarray) -> None:
        """Generate trade routes between resource locations and cities"""
        # Create a list of all important locations
        important_locations = cities.copy()

        # Add major resource deposits
        for resource_type, nodes in self.resource_nodes.items():
            # Select top nodes by quantity
            sorted_nodes = sorted(nodes, key=lambda n: n.quantity, reverse=True)
            major_nodes = sorted_nodes[:min(3, len(sorted_nodes))]
            for node in major_nodes:
                important_locations.append(node.position)

        # Generate routes between nearby locations
        for i, loc1 in enumerate(important_locations):
            for loc2 in important_locations[i+1:]:
                distance = math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)

                # Create routes for nearby locations
                if distance < 50 and random.random() < 0.7:
                    # Find resources at both locations
                    resources1 = self._get_resources_at_location(loc1)
                    resources2 = self._get_resources_at_location(loc2)

                    # Calculate route value
                    route_value = self._calculate_route_value(
                        resources1, resources2, distance
                    )

                    # Calculate danger level
                    danger_level = self._calculate_route_danger(
                        loc1, loc2, terrain_map
                    )

                    # Create trade route
                    trade_route = TradeRoute(
                        start=loc1,
                        end=loc2,
                        resources=resources1 + resources2,
                        route_value=route_value,
                        danger_level=danger_level
                    )
                    self.trade_routes.append(trade_route)

    def _get_resources_at_location(self, location: Tuple[int, int]) -> List[ResourceType]:
        """Get resource types at a specific location"""
        resources = []

        for resource_type, nodes in self.resource_nodes.items():
            for node in nodes:
                if node.position == location:
                    resources.append(resource_type)
                    break

        return resources

    def _calculate_route_value(self, resources1: List[ResourceType],
                             resources2: List[ResourceType],
                             distance: float) -> float:
        """Calculate economic value of trade route"""
        # Base value inversely proportional to distance
        base_value = 100.0 / (distance + 1)

        # Resource value bonuses
        high_value_resources = {
            ResourceType.GOLD_ORE, ResourceType.DIAMOND, ResourceType.MAGIC_CRYSTALS,
            ResourceType.ANCIENT_ARTIFACTS, ResourceType.RUBY, ResourceType.EMERALD
        }

        for resource in resources1 + resources2:
            if resource in high_value_resources:
                base_value *= 2.0

        # Diversity bonus
        unique_resources = len(set(resources1 + resources2))
        base_value *= (1 + unique_resources * 0.2)

        return base_value

    def _calculate_route_danger(self, start: Tuple[int, int],
                              end: Tuple[int, int],
                              terrain_map: np.ndarray) -> float:
        """Calculate danger level of trade route"""
        # Base danger from terrain difficulty
        path_points = self._get_path_points(start, end, 20)
        total_danger = 0

        for point in path_points:
            y, x = point
            if 0 <= y < self.height and 0 <= x < self.width:
                terrain_height = terrain_map[y, x]
                # Higher terrain is more dangerous
                terrain_danger = terrain_height * 0.5
                total_danger += terrain_danger

        avg_danger = total_danger / len(path_points) if path_points else 0.5

        # Add random factor
        avg_danger += random.normal(0, 0.1)

        return np.clip(avg_danger, 0, 1)

    def _get_path_points(self, start: Tuple[int, int],
                        end: Tuple[int, int],
                        num_points: int) -> List[Tuple[int, int]]:
        """Get points along a path between two locations"""
        points = []
        sy, sx = start
        ey, ex = end

        for i in range(num_points):
            t = i / (num_points - 1)
            y = int(sy + t * (ey - sy))
            x = int(sx + t * (ex - sx))
            points.append((y, x))

        return points

    def _generate_markets(self, cities: List[Tuple[int, int]]) -> None:
        """Generate resource markets at cities"""
        for city in cities:
            # Determine market size based on nearby resources
            nearby_resources = self._get_nearby_resources(city, radius=15)

            # Calculate supply and demand
            supply = defaultdict(float)
            demand = defaultdict(float)

            for resource_type, nodes in nearby_resources.items():
                total_quantity = sum(node.quantity for node in nodes)
                supply[resource_type] = total_quantity

                # Generate demand for resources not available locally
                if resource_type not in [ResourceType.STONE, ResourceType.WOOD]:
                    demand[resource_type] = random.uniform(10, 100)

            # Calculate prices based on supply and demand
            prices = {}
            for resource_type in supply.keys() | demand.keys():
                if resource_type in supply and resource_type in demand:
                    # Price based on supply/demand ratio
                    ratio = demand[resource_type] / (supply[resource_type] + 1)
                    base_price = self._get_base_price(resource_type)
                    prices[resource_type] = base_price * (1 + ratio)
                elif resource_type in supply:
                    # Abundant resource - lower price
                    base_price = self._get_base_price(resource_type)
                    prices[resource_type] = base_price * 0.7
                else:
                    # Scarce resource - higher price
                    base_price = self._get_base_price(resource_type)
                    prices[resource_type] = base_price * 1.5

            # Create market
            market = ResourceMarket(
                location=city,
                supply=dict(supply),
                demand=dict(demand),
                prices=prices,
                market_type="regional" if len(nearby_resources) > 5 else "local"
            )
            self.markets[city] = market

    def _get_nearby_resources(self, location: Tuple[int, int],
                             radius: int) -> Dict[ResourceType, List[ResourceNode]]:
        """Get resources near a location"""
        nearby = defaultdict(list)
        y, x = location

        for resource_type, nodes in self.resource_nodes.items():
            for node in nodes:
                ny, nx = node.position
                distance = math.sqrt((ny - y)**2 + (nx - x)**2)
                if distance <= radius:
                    nearby[resource_type].append(node)

        return nearby

    def _get_base_price(self, resource_type: ResourceType) -> float:
        """Get base price for resource type"""
        price_map = {
            ResourceType.STONE: 1.0,
            ResourceType.WOOD: 2.0,
            ResourceType.COAL: 3.0,
            ResourceType.IRON_ORE: 8.0,
            ResourceType.COPPER_ORE: 6.0,
            ResourceType.GOLD_ORE: 50.0,
            ResourceType.SILVER_ORE: 20.0,
            ResourceType.DIAMOND: 500.0,
            ResourceType.HERBS: 5.0,
            ResourceType.MAGIC_CRYSTALS: 100.0,
            ResourceType.ANCIENT_ARTIFACTS: 1000.0
        }

        return price_map.get(resource_type, 5.0)

    def get_resources_in_area(self, area: Tuple[int, int, int, int]) -> Dict[ResourceType, List[ResourceNode]]:
        """Get all resources in a rectangular area"""
        min_y, min_x, max_y, max_x = area
        area_resources = defaultdict(list)

        for resource_type, nodes in self.resource_nodes.items():
            for node in nodes:
                ny, nx = node.position
                if min_y <= ny <= max_y and min_x <= nx <= max_x:
                    area_resources[resource_type].append(node)

        return area_resources

    def extract_resource(self, resource_type: ResourceType,
                        location: Tuple[int, int],
                        amount: float,
                        tool_quality: float = 0.5) -> Tuple[bool, float]:
        """Extract resource from a node"""
        if resource_type not in self.resource_nodes:
            return False, 0

        # Find resource node at location
        for node in self.resource_nodes[resource_type]:
            if node.position == location and not node.depleted:
                # Check extraction difficulty
                success_chance = tool_quality - node.extraction_difficulty
                if random.random() < success_chance:
                    # Extract resource
                    extracted_amount = min(amount, node.quantity)
                    node.quantity -= extracted_amount

                    # Check if depleted
                    if node.quantity <= 0:
                        node.depleted = True

                    return True, extracted_amount
                else:
                    return False, 0

        return False, 0

    def regenerate_resources(self, time_delta: float) -> None:
        """Regenerate renewable resources"""
        for resource_type, nodes in self.resource_nodes.items():
            for node in nodes:
                if node.regeneration_rate > 0 and not node.depleted:
                    # Regenerate resource
                    regeneration = node.regeneration_rate * time_delta
                    node.quantity = min(
                        node.quantity + regeneration,
                        node.quantity * 1.5  # Cap at 50% above original
                    )

                    # Reactivate if depleted
                    if node.depleted and node.quantity > 10:
                        node.depleted = False

    def analyze_resource_distribution(self) -> Dict:
        """Analyze the resource distribution"""
        analysis = {
            'total_resource_nodes': sum(len(nodes) for nodes in self.resource_nodes.values()),
            'resource_types': list(self.resource_nodes.keys()),
            'resource_counts': {rt.value: len(nodes) for rt, nodes in self.resource_nodes.items()},
            'total_trade_routes': len(self.trade_routes),
            'total_markets': len(self.markets),
            'avg_trade_route_value': 0,
            'avg_trade_danger': 0,
            'resource_density': {},
            'high_value_resources': []
        }

        # Calculate trade route statistics
        if self.trade_routes:
            analysis['avg_trade_route_value'] = sum(rt.route_value for rt in self.trade_routes) / len(self.trade_routes)
            analysis['avg_trade_danger'] = sum(rt.danger_level for rt in self.trade_routes) / len(self.trade_routes)

        # Calculate resource density
        total_area = self.width * self.height
        for resource_type, nodes in self.resource_nodes.items():
            density = len(nodes) / total_area * 1000  # Nodes per 1000 cells
            analysis['resource_density'][resource_type.value] = density

        # Identify high-value resources
        high_value_types = [
            ResourceType.DIAMOND, ResourceType.GOLD_ORE, ResourceType.MAGIC_CRYSTALS,
            ResourceType.ANCIENT_ARTIFACTS, ResourceType.RUBY, ResourceType.EMERALD
        ]

        for resource_type in high_value_types:
            if resource_type in self.resource_nodes:
                analysis['high_value_resources'].append({
                    'type': resource_type.value,
                    'nodes': len(self.resource_nodes[resource_type]),
                    'total_quantity': sum(node.quantity for node in self.resource_nodes[resource_type])
                })

        return analysis

# Utility functions
def create_sample_terrain(width: int, height: int, seed: Optional[int] = None) -> np.ndarray:
    """Create sample terrain for testing"""
    if seed is not None:
        np.random.seed(seed)

    # Generate simple terrain
    terrain = np.random.rand(height, width) * 0.5

    # Add some mountains
    for _ in range(3):
        cx = random.randint(10, width - 10)
        cy = random.randint(10, height - 10)
        radius = random.randint(5, 15)

        for y in range(max(0, cy - radius), min(height, cy + radius)):
            for x in range(max(0, cx - radius), min(width, cx + radius)):
                distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                if distance <= radius:
                    terrain[y, x] += (1 - distance / radius) * 0.5

    return np.clip(terrain, 0, 1)

def create_sample_biomes(width: int, height: int, seed: Optional[int] = None) -> np.ndarray:
    """Create sample biome map"""
    if seed is not None:
        np.random.seed(seed)

    # Simple biome distribution
    biomes = np.zeros((height, width), dtype=int)

    # Create different biome regions
    regions = [
        (0, height//3, 0, width//3, 4),      # Forest
        (0, height//3, width//3, 2*width//3, 3),  # Plains
        (height//3, 2*height//3, 0, width//2, 4),  # More forest
        (2*height//3, height, width//2, width, 7),  # Desert
        (height//2, height, 0, width//3, 11),  # Mountains
    ]

    for y1, y2, x1, x2, biome_value in regions:
        biomes[y1:y2, x1:x2] = biome_value

    return biomes

if __name__ == "__main__":
    # Example usage
    print("Initializing Resource Distributor...")
    width, height = 100, 100

    # Create sample world
    terrain = create_sample_terrain(width, height, seed=42)
    biomes = create_sample_biomes(width, height, seed=43)

    # Add some cities
    cities = [(20, 20), (80, 80), (50, 50)]

    # Distribute resources
    distributor = ResourceDistributor(width, height, seed=44)
    distributor.distribute_resources(terrain, biomes, cities)

    # Analyze distribution
    analysis = distributor.analyze_resource_distribution()

    print(f"\nResource Distribution Analysis:")
    print(f"Total resource nodes: {analysis['total_resource_nodes']}")
    print(f"Resource types found: {len(analysis['resource_types'])}")
    print(f"Total trade routes: {analysis['total_trade_routes']}")
    print(f"Total markets: {analysis['total_markets']}")
    print(f"Average trade route value: {analysis['avg_trade_route_value']:.1f}")
    print(f"Average trade danger: {analysis['avg_trade_danger']:.2f}")

    print(f"\nResource counts:")
    for resource_type, count in analysis['resource_counts'].items():
        print(f"  {resource_type}: {count}")

    print(f"\nHigh-value resources:")
    for resource_info in analysis['high_value_resources']:
        print(f"  {resource_info['type']}: {resource_info['nodes']} nodes, "
              f"{resource_info['total_quantity']:.0f} total quantity")

    # Test resource extraction
    print(f"\nTesting resource extraction...")
    for resource_type, nodes in list(distributor.resource_nodes.items())[:3]:
        if nodes:
            node = nodes[0]
            success, amount = distributor.extract_resource(
                resource_type, node.position, 50.0, tool_quality=0.7
            )
            print(f"  {resource_type.value}: {'Success' if success else 'Failed'}, "
                  f"Extracted: {amount:.1f}")

    print(f"\nResource distribution complete!")