"""
Advanced Terrain Generation System
Implements realistic terrain generation with erosion simulation, multiple noise algorithms,
and geological processes for creating natural, believable landscapes.
"""

import numpy as np
import random
from scipy import ndimage
from scipy.spatial import Voronoi, voronoi_plot_2d
from collections import deque
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
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

@dataclass
class TerrainFeature:
    """Represents a terrain feature with properties"""
    feature_type: str
    position: Tuple[int, int]
    size: float
    intensity: float
    direction: Optional[float] = None

class NoiseGenerator:
    """Advanced noise generation with multiple algorithms"""

    @staticmethod
    def perlin_noise_2d(width: int, height: int, scale: float, octaves: int = 4,
                       persistence: float = 0.5, lacunarity: float = 2.0,
                       seed: Optional[int] = None) -> np.ndarray:
        """Generate 2D Perlin noise with multiple octaves"""
        if seed is not None:
            np.random.seed(seed)

        noise = np.zeros((height, width))
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0

        for _ in range(octaves):
            # Generate single octave of noise
            y_coords = np.linspace(0, frequency * height, height)[:, np.newaxis]
            x_coords = np.linspace(0, frequency * width, width)[np.newaxis, :]

            # Simple noise approximation using sine waves
            octave = (np.sin(x_coords * np.pi) * np.cos(y_coords * np.pi) +
                     np.sin(x_coords * np.pi * 2.3) * np.cos(y_coords * np.pi * 1.7))

            noise += octave * amplitude
            max_value += amplitude
            frequency *= lacunarity
            amplitude *= persistence

        # Normalize to [0, 1]
        noise = (noise + max_value) / (2 * max_value)
        return np.clip(noise, 0, 1)

    @staticmethod
    def simplex_noise_2d(width: int, height: int, scale: float, seed: Optional[int] = None) -> np.ndarray:
        """Generate simplex-like noise using gradient interpolation"""
        if seed is not None:
            np.random.seed(seed)

        # Create gradient grid
        grid_size = int(max(width, height) / scale) + 2
        gradients = np.random.randn(grid_size, grid_size, 2)

        noise = np.zeros((height, width))

        for y in range(height):
            for x in range(width):
                # Grid coordinates
                x0 = int(x / scale)
                x1 = x0 + 1
                y0 = int(y / scale)
                y1 = y0 + 1

                # Interpolation weights
                dx = (x / scale) - x0
                dy = (y / scale) - y0

                # Fade function for smooth interpolation
                def fade(t):
                    return t * t * t * (t * (t * 6 - 15) + 10)

                u = fade(dx)
                v = fade(dy)

                # Dot products with gradients
                n00 = np.dot([dx, dy], gradients[y0, x0])
                n10 = np.dot([dx - 1, dy], gradients[y0, x1])
                n01 = np.dot([dx, dy - 1], gradients[y1, x0])
                n11 = np.dot([dx - 1, dy - 1], gradients[y1, x1])

                # Bilinear interpolation
                nx0 = n00 * (1 - u) + n10 * u
                nx1 = n01 * (1 - u) + n11 * u
                noise[y, x] = nx0 * (1 - v) + nx1 * v

        # Normalize
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        return noise

    @staticmethod
    def ridged_noise(width: int, height: int, scale: float, octaves: int = 4) -> np.ndarray:
        """Generate ridged noise for mountain ranges"""
        base_noise = NoiseGenerator.perlin_noise_2d(width, height, scale, octaves)
        # Create ridges by taking absolute value and inverting
        ridged = 1.0 - np.abs(2.0 * base_noise - 1.0)
        return ridged

class ErosionSimulator:
    """Simulates hydraulic and thermal erosion for realistic terrain"""

    @staticmethod
    def hydraulic_erosion(heightmap: np.ndarray, iterations: int = 500,
                         rain_amount: float = 0.01, erosion_rate: float = 0.1,
                         deposition_rate: float = 0.1) -> np.ndarray:
        """Simulate water erosion on terrain"""
        terrain = heightmap.copy()
        height, width = terrain.shape

        for _ in range(iterations):
            # Random rain droplet placement
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            # Droplet properties
            water = rain_amount
            sediment = 0.0
            velocity = 0.0

            for _ in range(30):  # Max path length
                # Calculate gradients
                if 0 < x < width - 1 and 0 < y < height - 1:
                    grad_x = (terrain[y, x + 1] - terrain[y, x - 1]) * 0.5
                    grad_y = (terrain[y + 1, x] - terrain[y - 1, x]) * 0.5
                else:
                    break

                # Update velocity
                velocity += math.sqrt(grad_x**2 + grad_y**2)
                velocity *= 0.9  # Friction

                # Calculate carrying capacity
                capacity = max(0, velocity * water * erosion_rate)

                # Erosion or deposition
                if sediment > capacity:
                    # Deposition
                    amount = (sediment - capacity) * deposition_rate
                    terrain[y, x] += amount
                    sediment -= amount
                else:
                    # Erosion
                    amount = min((capacity - sediment) * erosion_rate, terrain[y, x] * 0.1)
                    terrain[y, x] -= amount
                    sediment += amount

                # Move droplet
                if abs(grad_x) > abs(grad_y):
                    x += 1 if grad_x > 0 else -1
                else:
                    y += 1 if grad_y > 0 else -1

                # Check boundaries
                if x < 0 or x >= width or y < 0 or y >= height:
                    break

                # Evaporation
                water *= 0.99

        return terrain

    @staticmethod
    def thermal_erosion(heightmap: np.ndarray, iterations: int = 10,
                       talus_angle: float = 0.1) -> np.ndarray:
        """Simulate thermal erosion (material slippage)"""
        terrain = heightmap.copy()
        height, width = terrain.shape

        for _ in range(iterations):
            new_terrain = terrain.copy()

            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    # Check height differences with neighbors
                    neighbors = [
                        (y-1, x-1), (y-1, x), (y-1, x+1),
                        (y, x-1),             (y, x+1),
                        (y+1, x-1), (y+1, x), (y+1, x+1)
                    ]

                    for ny, nx in neighbors:
                        height_diff = terrain[y, x] - terrain[ny, nx]
                        if height_diff > talus_angle:
                            # Transfer material
                            transfer = height_diff * 0.5
                            new_terrain[y, x] -= transfer
                            new_terrain[ny, nx] += transfer

            terrain = new_terrain

        return terrain

class RiverGenerator:
    """Generates realistic river networks using flow accumulation"""

    @staticmethod
    def generate_rivers(heightmap: np.ndarray, num_rivers: int = 5,
                       min_length: int = 50) -> List[List[Tuple[int, int]]]:
        """Generate river networks from high points to low points"""
        rivers = []
        height, width = heightmap.shape

        # Calculate flow direction map
        flow_direction = np.zeros((height, width), dtype=int)

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Find steepest descent
                min_height = heightmap[y, x]
                best_dir = -1

                directions = [
                    (-1, -1, 0), (-1, 0, 1), (-1, 1, 2),
                    (0, -1, 3),              (0, 1, 4),
                    (1, -1, 5), (1, 0, 6),  (1, 1, 7)
                ]

                for dy, dx, dir_idx in directions:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if heightmap[ny, nx] < min_height:
                            min_height = heightmap[ny, nx]
                            best_dir = dir_idx

                flow_direction[y, x] = best_dir

        # Generate rivers from random high points
        high_points = []
        for y in range(height):
            for x in range(width):
                if heightmap[y, x] > np.percentile(heightmap, 80):
                    high_points.append((y, x))

        random.shuffle(high_points)

        for i in range(min(num_rivers, len(high_points))):
            start_y, start_x = high_points[i]
            river = [(start_y, start_x)]
            current_y, current_x = start_y, start_x

            # Trace river path
            for _ in range(min_length * 2):  # Max path length
                if flow_direction[current_y, current_x] == -1:
                    break

                # Convert flow direction to coordinate change
                dir_map = {
                    0: (-1, -1), 1: (-1, 0), 2: (-1, 1),
                    3: (0, -1), 4: (0, 1),
                    5: (1, -1), 6: (1, 0), 7: (1, 1)
                }

                dy, dx = dir_map[flow_direction[current_y, current_x]]
                current_y += dy
                current_x += dx

                if (0 <= current_y < height and 0 <= current_x < width and
                    len(river) < min_length):
                    river.append((current_y, current_x))
                else:
                    break

            if len(river) >= min_length:
                rivers.append(river)

        return rivers

class VoronoiTerrainGenerator:
    """Uses Voronoi diagrams for biome and territory generation"""

    @staticmethod
    def generate_voronoi_biomes(width: int, height: int, num_points: int = 50,
                               seed: Optional[int] = None) -> np.ndarray:
        """Generate biome map using Voronoi diagram"""
        if seed is not None:
            np.random.seed(seed)

        # Generate random points
        points = []
        for _ in range(num_points):
            x = random.uniform(0, width)
            y = random.uniform(0, height)
            points.append([x, y])

        points = np.array(points)

        # Create Voronoi diagram
        vor = Voronoi(points)

        # Assign biome types to regions
        biome_map = np.zeros((height, width), dtype=int)

        for y in range(height):
            for x in range(width):
                # Find nearest Voronoi point
                distances = np.sqrt((points[:, 0] - x)**2 + (points[:, 1] - y)**2)
                nearest_region = np.argmin(distances)
                biome_map[y, x] = nearest_region

        return biome_map, points

class TerrainGenerator:
    """Main terrain generation system combining all algorithms"""

    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.heightmap = None
        self.biome_map = None
        self.rivers = []
        self.features = []

    def generate_base_terrain(self, continent_scale: float = 0.01,
                            detail_scale: float = 0.05,
                            roughness_scale: float = 0.1) -> np.ndarray:
        """Generate base terrain using multiple noise layers"""
        # Continental scale (large landmasses)
        continent = NoiseGenerator.perlin_noise_2d(
            self.width, self.height, continent_scale,
            octaves=4, persistence=0.6, seed=self.seed
        )

        # Regional detail (mountains, valleys)
        detail = NoiseGenerator.perlin_noise_2d(
            self.width, self.height, detail_scale,
            octaves=6, persistence=0.5, seed=self.seed + 1
        )

        # Fine roughness (small features)
        roughness = NoiseGenerator.perlin_noise_2d(
            self.width, self.height, roughness_scale,
            octaves=3, persistence=0.3, seed=self.seed + 2
        )

        # Mountain ridges
        ridges = NoiseGenerator.ridged_noise(
            self.width, self.height, detail_scale * 2,
            octaves=4
        )

        # Combine layers with different weights
        terrain = (continent * 0.4 +
                  detail * 0.3 +
                  roughness * 0.1 +
                  ridges * 0.2)

        # Apply power law for more dramatic terrain
        terrain = np.power(terrain, 1.2)

        self.heightmap = terrain
        return terrain

    def apply_erosion(self, hydraulic_iterations: int = 500,
                     thermal_iterations: int = 10) -> np.ndarray:
        """Apply erosion processes to terrain"""
        if self.heightmap is None:
            raise ValueError("Must generate base terrain first")

        # Hydraulic erosion
        eroded = ErosionSimulator.hydraulic_erosion(
            self.heightmap, iterations=hydraulic_iterations
        )

        # Thermal erosion
        final_terrain = ErosionSimulator.thermal_erosion(
            eroded, iterations=thermal_iterations
        )

        self.heightmap = final_terrain
        return final_terrain

    def generate_water_features(self, sea_level: float = 0.4,
                              num_rivers: int = 5) -> None:
        """Generate oceans, lakes, and rivers"""
        if self.heightmap is None:
            raise ValueError("Must generate terrain first")

        # Create water mask
        water_mask = self.heightmap < sea_level

        # Generate rivers
        land_heightmap = self.heightmap.copy()
        land_heightmap[water_mask] = 1.0  # Raise sea level to prevent rivers

        self.rivers = RiverGenerator.generate_rivers(
            land_heightmap, num_rivers=num_rivers
        )

        # Carve river beds
        for river in self.rivers:
            for y, x in river:
                if 0 <= y < self.height and 0 <= x < self.width:
                    # Lower terrain for river
                    river_width = 1
                    for dy in range(-river_width, river_width + 1):
                        for dx in range(-river_width, river_width + 1):
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < self.height and 0 <= nx < self.width):
                                distance = math.sqrt(dy**2 + dx**2)
                                if distance <= river_width:
                                    self.heightmap[ny, nx] = min(
                                        self.heightmap[ny, nx],
                                        sea_level - 0.1 * (1 - distance / river_width)
                                    )

    def generate_biomes(self, temperature_variation: float = 0.3,
                       moisture_variation: float = 0.3) -> np.ndarray:
        """Generate biome map based on elevation, temperature, and moisture"""
        if self.heightmap is None:
            raise ValueError("Must generate terrain first")

        # Generate temperature map (latitudinal variation)
        temp_noise = NoiseGenerator.perlin_noise_2d(
            self.width, self.height, 0.02,
            octaves=2, seed=self.seed + 10
        )
        latitude_factor = np.linspace(1, -1, self.height)[:, np.newaxis]
        temperature = (latitude_factor * 0.5 + temp_noise * temperature_variation + 0.5)
        temperature = np.clip(temperature, 0, 1)

        # Generate moisture map
        moisture = NoiseGenerator.perlin_noise_2d(
            self.width, self.height, 0.03,
            octaves=3, persistence=0.7, seed=self.seed + 11
        )

        # Add moisture near rivers and coasts
        river_influence = np.zeros_like(self.heightmap)
        for river in self.rivers:
            for y, x in river:
                if 0 <= y < self.height and 0 <= x < self.width:
                    for dy in range(-5, 6):
                        for dx in range(-5, 6):
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < self.height and 0 <= nx < self.width):
                                distance = math.sqrt(dy**2 + dx**2)
                                if distance <= 5:
                                    river_influence[ny, nx] = max(
                                        river_influence[ny, nx],
                                        1 - distance / 5
                                    )

        moisture = np.clip(moisture + river_influence * 0.3, 0, 1)

        # Determine biomes based on elevation, temperature, and moisture
        biome_map = np.zeros((self.height, self.width), dtype=object)

        for y in range(self.height):
            for x in range(self.width):
                elevation = self.heightmap[y, x]
                temp = temperature[y, x]
                moist = moisture[y, x]

                # Determine biome
                if elevation < 0.4:
                    if elevation < 0.3:
                        biome_map[y, x] = BiomeType.DEEP_OCEAN
                    else:
                        biome_map[y, x] = BiomeType.OCEAN
                elif elevation < 0.45:
                    biome_map[y, x] = BiomeType.BEACH
                elif elevation < 0.7:
                    if temp > 0.7:
                        if moist > 0.6:
                            biome_map[y, x] = BiomeType.JUNGLE
                        elif moist > 0.3:
                            biome_map[y, x] = BiomeType.SAVANNA
                        else:
                            biome_map[y, x] = BiomeType.DESERT
                    elif temp > 0.4:
                        if moist > 0.5:
                            biome_map[y, x] = BiomeType.FOREST
                        elif moist > 0.7:
                            biome_map[y, x] = BiomeType.DENSE_FOREST
                        else:
                            biome_map[y, x] = BiomeType.PLAINS
                    else:
                        if moist > 0.6:
                            biome_map[y, x] = BiomeType.MARSH
                        else:
                            biome_map[y, x] = BiomeType.TUNDRA
                elif elevation < 0.85:
                    if temp < 0.3:
                        biome_map[y, x] = BiomeType.ICE
                    else:
                        biome_map[y, x] = BiomeType.MOUNTAIN
                else:
                    if temp < 0.4:
                        biome_map[y, x] = BiomeType.ICE
                    else:
                        biome_map[y, x] = BiomeType.HIGH_MOUNTAIN

        self.biome_map = biome_map
        return biome_map

    def add_special_features(self, num_features: int = 20) -> None:
        """Add special terrain features like volcanoes, canyons, etc."""
        if self.heightmap is None:
            raise ValueError("Must generate terrain first")

        self.features = []

        for _ in range(num_features):
            feature_type = random.choice([
                'volcano', 'canyon', 'mesa', 'crater', 'archipelago'
            ])

            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)
            size = random.uniform(5, 20)
            intensity = random.uniform(0.3, 0.8)

            feature = TerrainFeature(feature_type, (x, y), size, intensity)
            self.features.append(feature)

            # Apply feature to heightmap
            if feature_type == 'volcano':
                self._add_volcano(x, y, size, intensity)
            elif feature_type == 'canyon':
                self._add_canyon(x, y, size, intensity)
            elif feature_type == 'mesa':
                self._add_mesa(x, y, size, intensity)
            elif feature_type == 'crater':
                self._add_crater(x, y, size, intensity)
            elif feature_type == 'archipelago':
                self._add_archipelago(x, y, size, intensity)

    def _add_volcano(self, cx: int, cy: int, size: float, intensity: float):
        """Add volcanic cone to terrain"""
        for y in range(max(0, int(cy - size * 2)), min(self.height, int(cy + size * 2))):
            for x in range(max(0, int(cx - size * 2)), min(self.width, int(cx + size * 2))):
                distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                if distance < size * 2:
                    # Conical shape
                    height_increase = intensity * (1 - distance / (size * 2))
                    # Add caldera at top
                    if distance < size * 0.3:
                        height_increase *= 0.3
                    self.heightmap[y, x] = min(1.0, self.heightmap[y, x] + height_increase)

    def _add_canyon(self, cx: int, cy: int, size: float, intensity: float):
        """Add canyon to terrain"""
        # Random canyon direction
        angle = random.uniform(0, 2 * math.pi)
        length = int(size * 3)

        for i in range(length):
            x = int(cx + i * math.cos(angle))
            y = int(cy + i * math.sin(angle))

            if 0 <= x < self.width and 0 <= y < self.height:
                # Carve canyon
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            distance = math.sqrt(dy**2 + dx**2)
                            if distance <= 2:
                                depth = intensity * (1 - distance / 2)
                                self.heightmap[ny, nx] = max(0, self.heightmap[ny, nx] - depth)

    def _add_mesa(self, cx: int, cy: int, size: float, intensity: float):
        """Add flat-topped mesa"""
        for y in range(max(0, int(cy - size)), min(self.height, int(cy + size))):
            for x in range(max(0, int(cx - size)), min(self.width, int(cx + size))):
                distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                if distance < size:
                    # Flat top with steep sides
                    if distance < size * 0.6:
                        height_increase = intensity
                    else:
                        height_increase = intensity * (1 - (distance - size * 0.6) / (size * 0.4))
                    self.heightmap[y, x] = min(1.0, self.heightmap[y, x] + height_increase)

    def _add_crater(self, cx: int, cy: int, size: float, intensity: float):
        """Add impact crater"""
        for y in range(max(0, int(cy - size)), min(self.height, int(cy + size))):
            for x in range(max(0, int(cx - size)), min(self.width, int(cx + size))):
                distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                if distance < size:
                    # Bowl-shaped depression
                    depth = intensity * (1 - distance / size)
                    # Raised rim
                    if distance > size * 0.8:
                        depth = -depth * 0.3
                    self.heightmap[y, x] = np.clip(
                        self.heightmap[y, x] - depth, 0, 1
                    )

    def _add_archipelago(self, cx: int, cy: int, size: float, intensity: float):
        """Add cluster of small islands"""
        num_islands = int(size)
        for _ in range(num_islands):
            island_x = cx + random.randint(-int(size), int(size))
            island_y = cy + random.randint(-int(size), int(size))
            island_size = random.uniform(2, 5)

            for y in range(max(0, int(island_y - island_size)),
                         min(self.height, int(island_y + island_size))):
                for x in range(max(0, int(island_x - island_size)),
                             min(self.width, int(island_x + island_size))):
                    distance = math.sqrt((x - island_x)**2 + (y - island_y)**2)
                    if distance < island_size:
                        height_increase = intensity * (1 - distance / island_size)
                        self.heightmap[y, x] = min(0.5, self.heightmap[y, x] + height_increase)

    def generate_complete_world(self) -> Dict:
        """Generate complete world with all features"""
        # Generate base terrain
        self.generate_base_terrain()

        # Apply erosion
        self.apply_erosion()

        # Generate water features
        self.generate_water_features()

        # Generate biomes
        self.generate_biomes()

        # Add special features
        self.add_special_features()

        return {
            'heightmap': self.heightmap,
            'biome_map': self.biome_map,
            'rivers': self.rivers,
            'features': self.features,
            'seed': self.seed,
            'dimensions': (self.width, self.height)
        }

# Utility functions for terrain analysis and export
def analyze_terrain(heightmap: np.ndarray) -> Dict:
    """Analyze terrain characteristics"""
    return {
        'min_elevation': float(np.min(heightmap)),
        'max_elevation': float(np.max(heightmap)),
        'mean_elevation': float(np.mean(heightmap)),
        'std_elevation': float(np.std(heightmap)),
        'land_percentage': float(np.sum(heightmap > 0.4) / heightmap.size * 100),
        'mountain_percentage': float(np.sum(heightmap > 0.7) / heightmap.size * 100)
    }

def export_heightmap_image(heightmap: np.ndarray, filename: str) -> None:
    """Export heightmap as image (requires PIL)"""
    try:
        from PIL import Image

        # Normalize to 0-255
        normalized = ((heightmap - heightmap.min()) /
                     (heightmap.max() - heightmap.min()) * 255).astype(np.uint8)

        img = Image.fromarray(normalized, mode='L')
        img.save(filename)
    except ImportError:
        print("PIL not available. Install with: pip install Pillow")

def export_biome_map(biome_map: np.ndarray, filename: str) -> None:
    """Export biome map as colored image (requires PIL)"""
    try:
        from PIL import Image

        # Color mapping for biomes
        biome_colors = {
            BiomeType.DEEP_OCEAN: (0, 0, 139),
            BiomeType.OCEAN: (0, 100, 200),
            BiomeType.BEACH: (238, 203, 173),
            BiomeType.PLAINS: (124, 252, 0),
            BiomeType.FOREST: (34, 139, 34),
            BiomeType.DENSE_FOREST: (0, 100, 0),
            BiomeType.JUNGLE: (0, 128, 0),
            BiomeType.DESERT: (238, 203, 173),
            BiomeType.SAVANNA: (255, 228, 196),
            BiomeType.TUNDRA: (176, 224, 230),
            BiomeType.ICE: (240, 248, 255),
            BiomeType.MOUNTAIN: (139, 69, 19),
            BiomeType.HIGH_MOUNTAIN: (105, 105, 105),
            BiomeType.HILLS: (154, 205, 50),
            BiomeType.MARSH: (95, 158, 160),
            BiomeType.SWAMP: (47, 79, 79)
        }

        # Create RGB image
        rgb_image = np.zeros((biome_map.shape[0], biome_map.shape[1], 3), dtype=np.uint8)

        for y in range(biome_map.shape[0]):
            for x in range(biome_map.shape[1]):
                biome = biome_map[y, x]
                if biome in biome_colors:
                    rgb_image[y, x] = biome_colors[biome]

        img = Image.fromarray(rgb_image, mode='RGB')
        img.save(filename)
    except ImportError:
        print("PIL not available. Install with: pip install Pillow")

if __name__ == "__main__":
    # Example usage
    generator = TerrainGenerator(width=512, height=512, seed=42)

    print("Generating terrain...")
    world = generator.generate_complete_world()

    print("Analyzing terrain...")
    analysis = analyze_terrain(world['heightmap'])
    print(f"Terrain Analysis: {analysis}")

    print(f"Generated world with {len(world['rivers'])} rivers and {len(world['features'])} features")

    # Export if PIL is available
    try:
        export_heightmap_image(world['heightmap'], 'heightmap.png')
        export_biome_map(world['biome_map'], 'biome_map.png')
        print("Exported heightmap and biome map as PNG files")
    except:
        print("Could not export images (PIL not available)")