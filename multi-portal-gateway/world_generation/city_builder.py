"""
Intelligent City Builder System
Generates realistic cities and settlements with logical layouts, districts,
infrastructure, and organic growth patterns using agent-based modeling and
urban planning principles.
"""

import numpy as np
import random
from scipy import ndimage
from scipy.spatial import Voronoi, distance
from collections import deque, defaultdict
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class BuildingType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    GOVERNMENT = "government"
    RELIGIOUS = "religious"
    EDUCATIONAL = "educational"
    MEDICAL = "medical"
    MILITARY = "military"
    ENTERTAINMENT = "entertainment"
    MARKET = "market"
    FARM = "farm"
    MINE = "mine"
    LUMBER = "lumber"

class DistrictType(Enum):
    CITY_CENTER = "city_center"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    MILITARY = "military"
    RELIGIOUS = "religious"
    ADMINISTRATIVE = "administrative"
    ENTERTAINMENT = "entertainment"
    SLUMS = "slums"
    NOBLE = "noble"

class RoadType(Enum):
    MAIN_ROAD = "main_road"
    SECONDARY_ROAD = "secondary_road"
    STREET = "street"
    ALLEY = "alley"
    PLAZA = "plaza"

@dataclass
class Building:
    """Represents a building with properties"""
    building_type: BuildingType
    position: Tuple[int, int]
    size: Tuple[int, int]  # width, height
    quality: float  # 0.0 - 1.0
    age: int
    wealth_level: float
    orientation: float = 0.0
    district_id: Optional[int] = None

@dataclass
class District:
    """Represents a city district"""
    district_type: DistrictType
    center: Tuple[int, int]
    bounds: Tuple[int, int, int, int]  # min_x, min_y, max_x, max_y
    buildings: List[Building] = field(default_factory=list)
    roads: List[List[Tuple[int, int]]] = field(default_factory=list)
    population: int = 0
    wealth_level: float = 0.5
    development_level: float = 0.5

@dataclass
class Road:
    """Represents a road segment"""
    road_type: RoadType
    path: List[Tuple[int, int]]
    width: int
    traffic_level: float = 0.5
    maintenance_level: float = 0.8

@dataclass
class City:
    """Complete city representation"""
    name: str
    center: Tuple[int, int]
    districts: List[District] = field(default_factory=list)
    buildings: List[Building] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    walls: Optional[List[Tuple[int, int]]] = None
    population: int = 0
    founding_year: int = 0
    city_type: str = "town"
    trade_routes: List[Tuple[str, float]] = field(default_factory=list)

class UrbanGrowthSimulator:
    """Simulates organic city growth using agent-based modeling"""

    @staticmethod
    def calculate_land_value(terrain_height: np.ndarray,
                           water_distance: np.ndarray,
                           road_distance: np.ndarray,
                           city_center: Tuple[int, int],
                           decay_factor: float = 0.01) -> np.ndarray:
        """Calculate land value based on multiple factors"""
        height, width = terrain_height.shape

        # Distance from city center
        y_coords, x_coords = np.ogrid[:height, :width]
        center_distance = np.sqrt((x_coords - city_center[0])**2 +
                                (y_coords - city_center[1])**2)

        # Combine factors with weights
        land_value = (
            0.3 * np.exp(-center_distance * decay_factor) +  # Proximity to center
            0.2 * np.exp(-water_distance * 0.005) +         # Proximity to water
            0.3 * np.exp(-road_distance * 0.01) +           # Proximity to roads
            0.2 * terrain_height                            # Elevation preference
        )

        return np.clip(land_value, 0, 1)

    @staticmethod
    def simulate_growth(center: Tuple[int, int], terrain_height: np.ndarray,
                       water_mask: np.ndarray, iterations: int = 100,
                       growth_rate: float = 0.1) -> np.ndarray:
        """Simulate organic city growth from center"""
        height, width = terrain_height.shape
        development_map = np.zeros((height, width))

        # Initialize with city center
        cy, cx = center
        development_map[cy, cx] = 1.0

        # Growth queue
        growth_queue = deque([(cx, cy, 1.0)])

        for _ in range(iterations):
            if not growth_queue:
                break

            current_queue_size = len(growth_queue)

            for _ in range(current_queue_size):
                x, y, intensity = growth_queue.popleft()

                # Try to grow to neighboring cells
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy

                    if (0 <= nx < width and 0 <= ny < height and
                        development_map[ny, nx] < 0.1 and not water_mask[ny, nx]):

                        # Growth probability based on terrain and neighbors
                        growth_prob = growth_rate * intensity

                        # Slope penalty
                        if 0 < ny < height - 1 and 0 < nx < width - 1:
                            slope = max(
                                abs(terrain_height[ny, nx] - terrain_height[ny-1, nx]),
                                abs(terrain_height[ny, nx] - terrain_height[ny+1, nx]),
                                abs(terrain_height[ny, nx] - terrain_height[ny, nx-1]),
                                abs(terrain_height[ny, nx] - terrain_height[ny, nx+1])
                            )
                            growth_prob *= max(0.1, 1 - slope * 2)

                        if random.random() < growth_prob:
                            development_map[ny, nx] = min(1.0, intensity * 0.9)
                            growth_queue.append((nx, ny, intensity * 0.9))

        return development_map

class RoadNetworkGenerator:
    """Generates realistic road networks using graph algorithms"""

    @staticmethod
    def generate_main_roads(city_center: Tuple[int, int],
                          development_map: np.ndarray,
                          num_main_roads: int = 4) -> List[List[Tuple[int, int]]]:
        """Generate main radial roads from city center"""
        height, width = development_map.shape
        roads = []

        for i in range(num_main_roads):
            angle = (2 * math.pi * i) / num_main_roads + random.uniform(-0.3, 0.3)
            road = [city_center]

            x, y = city_center
            step_size = 1

            for _ in range(100):  # Max road length
                # Move in road direction with some randomness
                x += int(math.cos(angle) * step_size)
                y += int(math.sin(angle) * step_size)

                # Add some meandering
                x += random.randint(-1, 1)
                y += random.randint(-1, 1)

                # Check boundaries and development
                if (0 <= x < width and 0 <= y < height and
                    development_map[y, x] > 0.05):
                    road.append((y, x))
                else:
                    break

                # Occasionally change direction slightly
                if random.random() < 0.1:
                    angle += random.uniform(-0.2, 0.2)

            if len(road) > 5:
                roads.append(road)

        return roads

    @staticmethod
    def generate_secondary_roads(main_roads: List[List[Tuple[int, int]]],
                               development_map: np.ndarray) -> List[List[Tuple[int, int]]]:
        """Generate secondary roads connecting main roads"""
        if not main_roads:
            return []

        height, width = development_map.shape
        secondary_roads = []

        # Find connection points on main roads
        connection_points = []
        for road in main_roads:
            for i in range(len(road) // 4, len(road) * 3 // 4, len(road) // 8):
                if i < len(road):
                    connection_points.append(road[i])

        # Connect nearby main roads
        for i, point1 in enumerate(connection_points):
            for point2 in connection_points[i+1:]:
                distance = math.sqrt((point1[0] - point2[0])**2 +
                                   (point1[1] - point2[1])**2)

                if distance < 30 and distance > 5:  # Suitable connection distance
                    # Generate connecting road using pathfinding
                    road = RoadNetworkGenerator._find_path(
                        point1, point2, development_map
                    )

                    if road and len(road) > 3:
                        secondary_roads.append(road)

        return secondary_roads

    @staticmethod
    def _find_path(start: Tuple[int, int], end: Tuple[int, int],
                   development_map: np.ndarray) -> Optional[List[Tuple[int, int]]]:
        """Find path between two points using A* algorithm"""
        height, width = development_map.shape

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def get_neighbors(pos):
            y, x = pos
            neighbors = []
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    neighbors.append((ny, nx))
            return neighbors

        # A* pathfinding
        open_set = [(start, 0)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, end)}

        while open_set:
            current, _ = min(open_set, key=lambda x: f_score.get(x[0], float('inf')))
            open_set.remove((current, _))

            if current == end:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in get_neighbors(current):
                # Prefer developed areas
                cost = 1.0 - development_map[neighbor[0], neighbor[1]] * 0.5
                tentative_g = g_score[current] + cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)

                    if (neighbor, tentative_g) not in open_set:
                        open_set.append((neighbor, tentative_g))

        return None

    @staticmethod
    def generate_local_streets(district: District, development_map: np.ndarray) -> List[List[Tuple[int, int]]]:
        """Generate local streets within a district"""
        streets = []
        min_y, min_x, max_y, max_x = district.bounds

        # Grid pattern with some irregularity
        grid_spacing = random.randint(4, 8)

        # Horizontal streets
        for y in range(min_y + grid_spacing, max_y, grid_spacing):
            street = []
            for x in range(min_x, max_x + 1):
                if (0 <= y < development_map.shape[0] and
                    0 <= x < development_map.shape[1] and
                    development_map[y, x] > 0.1):
                    street.append((y, x))
            if len(street) > 5:
                streets.append(street)

        # Vertical streets
        for x in range(min_x + grid_spacing, max_x, grid_spacing):
            street = []
            for y in range(min_y, max_y + 1):
                if (0 <= y < development_map.shape[0] and
                    0 <= x < development_map.shape[1] and
                    development_map[y, x] > 0.1):
                    street.append((y, x))
            if len(street) > 5:
                streets.append(street)

        return streets

class DistrictPlanner:
    """Plans city districts based on urban planning principles"""

    @staticmethod
    def create_voronoi_districts(city_center: Tuple[int, int],
                                development_map: np.ndarray,
                                num_districts: int = 6) -> List[District]:
        """Create districts using Voronoi diagram"""
        height, width = development_map.shape

        # Generate district centers
        district_centers = []
        for _ in range(num_districts):
            # Bias placement towards development
            attempts = 0
            while attempts < 100:
                y = random.randint(10, height - 10)
                x = random.randint(10, width - 10)

                if development_map[y, x] > 0.2:
                    district_centers.append((y, x))
                    break
                attempts += 1

        if len(district_centers) < 2:
            district_centers = [city_center]

        # Create Voronoi diagram
        if len(district_centers) >= 2:
            points = np.array([[x, y] for y, x in district_centers])
            vor = Voronoi(points)

            # Assign cells to districts
            district_map = np.zeros((height, width), dtype=int)

            for y in range(height):
                for x in range(width):
                    if development_map[y, x] > 0.1:
                        distances = [math.sqrt((x - cx)**2 + (y - cy)**2)
                                   for cy, cx in district_centers]
                        nearest = np.argmin(distances)
                        district_map[y, x] = nearest

            # Create district objects
            districts = []
            for i, (cy, cx) in enumerate(district_centers):
                # Find district bounds
                district_mask = (district_map == i)
                if np.any(district_mask):
                    y_indices, x_indices = np.where(district_mask)
                    min_y, max_y = y_indices.min(), y_indices.max()
                    min_x, max_x = x_indices.min(), x_indices.max()

                    # Determine district type based on location and characteristics
                    district_type = DistrictPlanner._determine_district_type(
                        (cy, cx), city_center, development_map, district_mask
                    )

                    district = District(
                        district_type=district_type,
                        center=(cy, cx),
                        bounds=(min_y, min_x, max_y, max_x)
                    )
                    districts.append(district)

            return districts

        return []

    @staticmethod
    def _determine_district_type(center: Tuple[int, int], city_center: Tuple[int, int],
                               development_map: np.ndarray, district_mask: np.ndarray) -> DistrictType:
        """Determine district type based on characteristics"""
        cy, cx = center
        distance_from_center = math.sqrt((cy - city_center[0])**2 + (cx - city_center[1])**2)

        # Average development level in district
        avg_development = np.mean(development_map[district_mask])

        # Determine type based on distance and development
        if distance_from_center < 10:
            return DistrictType.CITY_CENTER
        elif distance_from_center < 20:
            if avg_development > 0.7:
                return DistrictType.COMMERCIAL
            elif random.random() < 0.3:
                return DistrictType.ADMINISTRATIVE
            else:
                return DistrictType.RESIDENTIAL
        elif distance_from_center < 40:
            if avg_development > 0.5:
                return DistrictType.RESIDENTIAL
            elif random.random() < 0.2:
                return DistrictType.INDUSTRIAL
            else:
                return DistrictType.AGRICULTURAL
        else:
            if random.random() < 0.1:
                return DistrictType.MILITARY
            elif random.random() < 0.2:
                return DistrictType.SLUMS
            else:
                return DistrictType.AGRICULTURAL

class BuildingGenerator:
    """Generates buildings within districts"""

    @staticmethod
    def generate_buildings(district: District, development_map: np.ndarray,
                          building_density: float = 0.7) -> List[Building]:
        """Generate buildings for a district"""
        buildings = []
        min_y, min_x, max_y, max_x = district.bounds

        # Calculate building density based on district type
        density_multiplier = BuildingGenerator._get_density_multiplier(district.district_type)
        actual_density = building_density * density_multiplier

        # Generate buildings in a grid pattern with variations
        for y in range(min_y + 1, max_y, 3):
            for x in range(min_x + 1, max_x, 3):
                if (y < development_map.shape[0] and x < development_map.shape[1] and
                    random.random() < actual_density and
                    development_map[y, x] > 0.2):

                    # Determine building type
                    building_type = BuildingGenerator._determine_building_type(
                        district.district_type, district.wealth_level
                    )

                    # Building properties
                    size = BuildingGenerator._get_building_size(building_type)
                    quality = random.uniform(0.3, 1.0) * district.development_level
                    age = random.randint(0, 200)
                    wealth_level = district.wealth_level * random.uniform(0.5, 1.5)
                    wealth_level = np.clip(wealth_level, 0, 1)

                    building = Building(
                        building_type=building_type,
                        position=(y, x),
                        size=size,
                        quality=quality,
                        age=age,
                        wealth_level=wealth_level,
                        orientation=random.uniform(0, 360),
                        district_id=id(district)
                    )
                    buildings.append(building)

        return buildings

    @staticmethod
    def _get_density_multiplier(district_type: DistrictType) -> float:
        """Get building density multiplier for district type"""
        multipliers = {
            DistrictType.CITY_CENTER: 1.5,
            DistrictType.COMMERCIAL: 1.2,
            DistrictType.RESIDENTIAL: 1.0,
            DistrictType.INDUSTRIAL: 0.8,
            DistrictType.AGRICULTURAL: 0.3,
            DistrictType.MILITARY: 0.6,
            DistrictType.SLUMS: 1.3,
            DistrictType.NOBLE: 0.5
        }
        return multipliers.get(district_type, 1.0)

    @staticmethod
    def _determine_building_type(district_type: DistrictType, wealth_level: float) -> BuildingType:
        """Determine building type based on district and wealth"""
        building_options = {
            DistrictType.CITY_CENTER: [BuildingType.GOVERNMENT, BuildingType.COMMERCIAL,
                                      BuildingType.MARKET, BuildingType.RELIGIOUS],
            DistrictType.COMMERCIAL: [BuildingType.COMMERCIAL, BuildingType.MARKET,
                                     BuildingType.ENTERTAINMENT],
            DistrictType.RESIDENTIAL: [BuildingType.RESIDENTIAL],
            DistrictType.INDUSTRIAL: [BuildingType.INDUSTRIAL, BuildingType.WAREHOUSE],
            DistrictType.AGRICULTURAL: [BuildingType.FARM, BuildingType.RESIDENTIAL],
            DistrictType.MILITARY: [BuildingType.MILITARY],
            DistrictType.RELIGIOUS: [BuildingType.RELIGIOUS, BuildingType.EDUCATIONAL],
            DistrictType.ADMINISTRATIVE: [BuildingType.GOVERNMENT, BuildingType.EDUCATIONAL],
            DistrictType.ENTERTAINMENT: [BuildingType.ENTERTAINMENT, BuildingType.COMMERCIAL],
            DistrictType.SLUMS: [BuildingType.RESIDENTIAL],
            DistrictType.NOBLE: [BuildingType.RESIDENTIAL, BuildingType.GOVERNMENT]
        }

        options = building_options.get(district_type, [BuildingType.RESIDENTIAL])
        return random.choice(options)

    @staticmethod
    def _get_building_size(building_type: BuildingType) -> Tuple[int, int]:
        """Get building size based on type"""
        size_ranges = {
            BuildingType.RESIDENTIAL: [(1, 1), (2, 1), (1, 2), (2, 2)],
            BuildingType.COMMERCIAL: [(2, 2), (3, 2), (2, 3), (3, 3)],
            BuildingType.INDUSTRIAL: [(3, 3), (4, 3), (3, 4), (4, 4)],
            BuildingType.GOVERNMENT: [(3, 3), (4, 4), (5, 4)],
            BuildingType.RELIGIOUS: [(3, 3), (4, 4), (5, 5)],
            BuildingType.EDUCATIONAL: [(3, 3), (4, 3), (3, 4)],
            BuildingType.MEDICAL: [(2, 2), (3, 3)],
            BuildingType.MILITARY: [(3, 3), (4, 4), (5, 4)],
            BuildingType.MARKET: [(4, 4), (5, 5), (6, 4)],
            BuildingType.FARM: [(3, 3), (4, 4), (5, 5)],
            BuildingType.ENTERTAINMENT: [(2, 2), (3, 3), (4, 3)]
        }

        sizes = size_ranges.get(building_type, [(2, 2)])
        return random.choice(sizes)

class CityBuilder:
    """Main city building system"""

    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

    def generate_city(self, city_center: Tuple[int, int],
                     terrain_height: np.ndarray,
                     water_mask: np.ndarray,
                     city_size: str = "medium",
                     city_type: str = "town") -> City:
        """Generate complete city"""
        # Determine city parameters based on size
        size_params = self._get_size_parameters(city_size)

        # Simulate organic growth
        development_map = UrbanGrowthSimulator.simulate_growth(
            city_center, terrain_height, water_mask,
            iterations=size_params['growth_iterations'],
            growth_rate=size_params['growth_rate']
        )

        # Generate road network
        main_roads = RoadNetworkGenerator.generate_main_roads(
            city_center, development_map, size_params['main_roads']
        )
        secondary_roads = RoadNetworkGenerator.generate_secondary_roads(
            main_roads, development_map
        )

        # Create districts
        districts = DistrictPlanner.create_voronoi_districts(
            city_center, development_map, size_params['num_districts']
        )

        # Generate local streets and buildings for each district
        all_buildings = []
        all_roads = []

        for road in main_roads:
            all_roads.append(Road(RoadType.MAIN_ROAD, road, width=3))

        for road in secondary_roads:
            all_roads.append(Road(RoadType.SECONDARY_ROAD, road, width=2))

        for district in districts:
            # Generate local streets
            local_streets = RoadNetworkGenerator.generate_local_streets(
                district, development_map
            )

            for street in local_streets:
                all_roads.append(Road(RoadType.STREET, street, width=1))
                district.roads.append(street)

            # Generate buildings
            buildings = BuildingGenerator.generate_buildings(
                district, development_map, size_params['building_density']
            )
            district.buildings = buildings
            all_buildings.extend(buildings)

            # Calculate district population
            district.population = sum(
                self._estimate_building_population(b) for b in buildings
            )

        # Generate city walls if applicable
        walls = None
        if city_type in ["fortified_town", "castle_town"] and random.random() < 0.7:
            walls = self._generate_city_walls(city_center, development_map)

        # Calculate total population
        total_population = sum(d.population for d in districts)

        # Create city object
        city_name = self._generate_city_name()
        city = City(
            name=city_name,
            center=city_center,
            districts=districts,
            buildings=all_buildings,
            roads=all_roads,
            walls=walls,
            population=total_population,
            founding_year=random.randint(100, 1500),
            city_type=city_type
        )

        return city

    def _get_size_parameters(self, city_size: str) -> Dict:
        """Get generation parameters based on city size"""
        params = {
            "small": {
                "growth_iterations": 50,
                "growth_rate": 0.15,
                "main_roads": 3,
                "num_districts": 3,
                "building_density": 0.5
            },
            "medium": {
                "growth_iterations": 100,
                "growth_rate": 0.1,
                "main_roads": 4,
                "num_districts": 5,
                "building_density": 0.6
            },
            "large": {
                "growth_iterations": 200,
                "growth_rate": 0.08,
                "main_roads": 6,
                "num_districts": 8,
                "building_density": 0.7
            },
            "metropolis": {
                "growth_iterations": 300,
                "growth_rate": 0.06,
                "main_roads": 8,
                "num_districts": 12,
                "building_density": 0.8
            }
        }
        return params.get(city_size, params["medium"])

    def _estimate_building_population(self, building: Building) -> int:
        """Estimate population of a building"""
        base_population = {
            BuildingType.RESIDENTIAL: 4,
            BuildingType.COMMERCIAL: 2,
            BuildingType.INDUSTRIAL: 8,
            BuildingType.GOVERNMENT: 5,
            BuildingType.RELIGIOUS: 3,
            BuildingType.EDUCATIONAL: 6,
            BuildingType.MEDICAL: 10,
            BuildingType.MILITARY: 15,
            BuildingType.MARKET: 3,
            BuildingType.FARM: 6,
            BuildingType.ENTERTAINMENT: 2
        }

        base = base_population.get(building.building_type, 4)
        size_multiplier = building.size[0] * building.size[1]
        quality_multiplier = 0.5 + building.quality

        return int(base * size_multiplier * quality_multiplier)

    def _generate_city_walls(self, city_center: Tuple[int, int],
                           development_map: np.ndarray) -> List[Tuple[int, int]]:
        """Generate city walls around developed area"""
        height, width = development_map.shape

        # Find boundary of development
        boundary = []
        threshold = 0.2

        for y in range(height):
            for x in range(width):
                if development_map[y, x] > threshold:
                    # Check if on boundary
                    is_boundary = False
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if (0 <= ny < height and 0 <= nx < width and
                            development_map[ny, nx] <= threshold):
                            is_boundary = True
                            break

                    if is_boundary:
                        boundary.append((y, x))

        # Select wall points (simplified - should trace continuous boundary)
        if len(boundary) > 10:
            # Sort points by angle from center
            center_y, center_x = city_center
            boundary.sort(key=lambda p: math.atan2(p[0] - center_y, p[1] - center_x))

            # Sample points for wall
            wall_spacing = max(1, len(boundary) // 50)
            return boundary[::wall_spacing]

        return []

    def _generate_city_name(self) -> str:
        """Generate procedural city name"""
        prefixes = ["New", "Old", "Fort", "Port", "King's", "Queen's", "West", "East",
                   "North", "South", "High", "Low", "Green", "Stone", "Iron", "Silver"]
        suffixes = ["burg", "ville", "ton", "shire", "haven", "port", "cross", "bridge",
                   "ford", "ham", "wick", "stead", "field", "wood", "hill", "dale"]

        if random.random() < 0.3:
            return random.choice(prefixes) + random.choice(suffixes)
        else:
            # Generate unique name
            syllables = ["ton", "ham", "wich", "bury", "ford", "hampton", "chester"]
            return random.choice(syllables).capitalize()

# Utility functions
def analyze_city(city: City) -> Dict:
    """Analyze city characteristics"""
    building_types = defaultdict(int)
    district_types = defaultdict(int)

    for building in city.buildings:
        building_types[building.building_type.value] += 1

    for district in city.districts:
        district_types[district.district_type.value] += 1

    avg_building_quality = np.mean([b.quality for b in city.buildings]) if city.buildings else 0
    avg_wealth = np.mean([d.wealth_level for d in city.districts]) if city.districts else 0

    return {
        'name': city.name,
        'population': city.population,
        'num_districts': len(city.districts),
        'num_buildings': len(city.buildings),
        'num_roads': len(city.roads),
        'building_types': dict(building_types),
        'district_types': dict(district_types),
        'avg_building_quality': avg_building_quality,
        'avg_wealth_level': avg_wealth,
        'has_walls': city.walls is not None,
        'founding_year': city.founding_year
    }

def export_city_map(city: City, filename: str) -> None:
    """Export city map as image (requires PIL)"""
    try:
        from PIL import Image, ImageDraw

        # Create blank canvas
        img = Image.new('RGB', (500, 500), color='white')
        draw = ImageDraw.Draw(img)

        # Scale factor
        scale = min(500 / city.districts[0].bounds[2], 500 / city.districts[0].bounds[3]) if city.districts else 1

        # Draw roads
        for road in city.roads:
            color = {
                RoadType.MAIN_ROAD: (50, 50, 50),
                RoadType.SECONDARY_ROAD: (100, 100, 100),
                RoadType.STREET: (150, 150, 150)
            }.get(road.road_type, (128, 128, 128))

            if len(road.path) > 1:
                scaled_path = [(int(x * scale), int(y * scale)) for y, x in road.path]
                draw.line(scaled_path, fill=color, width=max(1, road.width))

        # Draw buildings
        for building in city.buildings:
            y, x = building.position
            w, h = building.size

            color = {
                BuildingType.RESIDENTIAL: (200, 200, 200),
                BuildingType.COMMERCIAL: (100, 100, 200),
                BuildingType.INDUSTRIAL: (150, 100, 50),
                BuildingType.GOVERNMENT: (200, 50, 50),
                BuildingType.RELIGIOUS: (200, 150, 50)
            }.get(building.building_type, (128, 128, 128))

            draw.rectangle(
                [int(x * scale), int(y * scale),
                 int((x + w) * scale), int((y + h) * scale)],
                fill=color
            )

        img.save(filename)
    except ImportError:
        print("PIL not available. Install with: pip install Pillow")

if __name__ == "__main__":
    # Example usage
    builder = CityBuilder(width=200, height=200, seed=42)

    # Create sample terrain and water mask
    terrain = np.random.rand(200, 200) * 0.3 + 0.5  # Gentle terrain
    water = np.zeros((200, 200), dtype=bool)
    water[40:60, 80:120] = True  # Add some water

    print("Generating city...")
    city = builder.generate_city(
        city_center=(100, 100),
        terrain_height=terrain,
        water_mask=water,
        city_size="medium",
        city_type="town"
    )

    analysis = analyze_city(city)
    print(f"Generated city: {analysis['name']}")
    print(f"Population: {analysis['population']}")
    print(f"Districts: {analysis['num_districts']}")
    print(f"Buildings: {analysis['num_buildings']}")

    # Export if PIL is available
    try:
        export_city_map(city, 'city_map.png')
        print("Exported city map as PNG file")
    except:
        print("Could not export city map (PIL not available)")