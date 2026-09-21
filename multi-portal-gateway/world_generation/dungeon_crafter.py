"""
Advanced Dungeon Generation System
Creates complex multi-level dungeons with logical connectivity, theme-based generation,
and intelligent placement of rooms, corridors, traps, puzzles, and encounters.
"""

import numpy as np
import random
from scipy import ndimage
from collections import deque, defaultdict
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class RoomType(Enum):
    ENTRANCE = "entrance"
    EXIT = "exit"
    CHAMBER = "chamber"
    HALL = "hall"
    TREASURE = "treasure"
    TRAP = "trap"
    PUZZLE = "puzzle"
    BOSS = "boss"
    LIBRARY = "library"
    KITCHEN = "kitchen"
    BARRACKS = "barracks"
    THRONE = "throne"
    CRYPT = "crypt"
    LABORATORY = "laboratory"
    SHRINE = "shrine"
    PRISON = "prison"
    ARMORY = "armory"
    VAULT = "vault"

class CorridorType(Enum):
    STRAIGHT = "straight"
    L_SHAPED = "l_shaped"
    ZIGZAG = "zigzag"
    SPIRAL = "spiral"
    STAIRS = "stairs"
    BRIDGE = "bridge"
    SECRET = "secret"

class DungeonTheme(Enum):
    CLASSIC = "classic"
    CAVE = "cave"
    TEMPLE = "temple"
    FORTRESS = "fortress"
    TOMB = "tomb"
    LABYRINTH = "labyrinth"
    MINE = "mine"
    SEWER = "sewer"
    ICE = "ice"
    FIRE = "fire"
    ABYSS = "abyss"
    CRYSTAL = "crystal"
    FUNGAL = "fungal"
    WATER = "water"

class TrapType(Enum):
    SPIKE_PIT = "spike_pit"
    POISON_DART = "poison_dart"
    SWINGING_BLADE = "swinging_blade"
    ROLLING_BOULDER = "rolling_boulder"
    TELEPORT = "teleport"
    FIRE_TRAP = "fire_trap"
    FROST_TRAP = "frost_trap"
    GAS_TRAP = "gas_trap"
    PRESSURE_PLATE = "pressure_plate"
    MAGIC_TRAP = "magic_trap"
    FALLING_BLOCK = "falling_block"

class PuzzleType(Enum):
    LEVER_SEQUENCE = "lever_sequence"
    TILE_PUZZLE = "tile_puzzle"
    RIDDLE_DOOR = "riddle_door"
    MIRROR_PUZZLE = "mirror_puzzle"
    WATER_LEVEL = "water_level"
    MUSIC_PUZZLE = "music_puzzle"
    CHESS_PUZZLE = "chess_puzzle"
    MAZE = "maze"
    TIMED_RUN = "timed_run"
    WEIGHTED_PRESSURE = "weighted_pressure"

@dataclass
class Room:
    """Represents a dungeon room"""
    room_type: RoomType
    position: Tuple[int, int]
    size: Tuple[int, int]  # width, height
    connections: List[int] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    traps: List[TrapType] = field(default_factory=list)
    puzzles: List[PuzzleType] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    treasure_value: float = 0.0
    secret_doors: List[Tuple[int, int]] = field(default_factory=list)
    lighting_level: float = 0.5
    difficulty: float = 0.5

@dataclass
class Corridor:
    """Represents a dungeon corridor"""
    corridor_type: CorridorType
    start: Tuple[int, int]
    end: Tuple[int, int]
    path: List[Tuple[int, int]]
    width: int = 1
    features: List[str] = field(default_factory=list)
    traps: List[TrapType] = field(default_factory=list)
    secret: bool = False

@dataclass
class DungeonLevel:
    """Represents a single dungeon level"""
    level_number: int
    theme: DungeonTheme
    grid: np.ndarray
    rooms: List[Room] = field(default_factory=list)
    corridors: List[Corridor] = field(default_factory=list)
    entrance: Optional[Tuple[int, int]] = None
    exit: Optional[Tuple[int, int]] = None
    special_features: List[str] = field(default_factory=list)
    ambient_effects: List[str] = field(default_factory=list)

@dataclass
class Dungeon:
    """Complete multi-level dungeon"""
    name: str
    theme: DungeonTheme
    levels: List[DungeonLevel] = field(default_factory=list)
    total_depth: int = 0
    difficulty_progression: float = 1.0
    lore_description: str = ""
    required_keys: List[str] = field(default_factory=list)
    boss_encounters: List[str] = field(default_factory=list)

class CellularAutomataGenerator:
    """Uses cellular automata for cave-like dungeon generation"""

    @staticmethod
    def generate_cave(width: int, height: int, iterations: int = 5,
                     birth_limit: int = 3, death_limit: int = 4,
                     initial_density: float = 0.45,
                     seed: Optional[int] = None) -> np.ndarray:
        """Generate cave using cellular automata"""
        if seed is not None:
            np.random.seed(seed)

        # Initialize random grid
        grid = np.random.choice([0, 1], size=(height, width),
                              p=[1 - initial_density, initial_density])

        # Apply cellular automata rules
        for _ in range(iterations):
            new_grid = grid.copy()

            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    # Count neighbors
                    neighbors = (grid[y-1:y+2, x-1:x+2].sum() - grid[y, x])

                    if grid[y, x] == 1:  # Currently wall
                        if neighbors < death_limit:
                            new_grid[y, x] = 0  # Become floor
                    else:  # Currently floor
                        if neighbors > birth_limit:
                            new_grid[y, x] = 1  # Become wall

            grid = new_grid

        return grid

    @staticmethod
    def connect_caves(grid: np.ndarray) -> np.ndarray:
        """Connect separate cave regions"""
        # Find all floor regions
        labeled_grid, num_regions = ndimage.label(grid == 0)

        if num_regions <= 1:
            return grid

        # Find largest region (main cave)
        region_sizes = [(i, np.sum(labeled_grid == i)) for i in range(1, num_regions + 1)]
        main_region = max(region_sizes, key=lambda x: x[1])[0]

        # Connect other regions to main region
        connected_grid = grid.copy()

        for region_id in range(1, num_regions + 1):
            if region_id != main_region:
                # Find closest points between regions
                region_mask = (labeled_grid == region_id)
                main_mask = (labeled_grid == main_region)

                # Find border points
                region_border = CellularAutomataGenerator._find_border(region_mask)
                main_border = CellularAutomataGenerator._find_border(main_mask)

                if region_border and main_border:
                    # Find closest pair
                    min_dist = float('inf')
                    best_pair = None

                    for r_point in region_border:
                        for m_point in main_border:
                            dist = abs(r_point[0] - m_point[0]) + abs(r_point[1] - m_point[1])
                            if dist < min_dist:
                                min_dist = dist
                                best_pair = (r_point, m_point)

                    if best_pair:
                        # Carve tunnel between regions
                        CellularAutomataGenerator._carve_tunnel(
                            connected_grid, best_pair[0], best_pair[1]
                        )

        return connected_grid

    @staticmethod
    def _find_border(mask: np.ndarray) -> List[Tuple[int, int]]:
        """Find border points of a region"""
        border = []
        height, width = mask.shape

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if mask[y, x]:
                    # Check if any neighbor is not in region
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if not mask[y + dy, x + dx]:
                            border.append((y, x))
                            break

        return border

    @staticmethod
    def _carve_tunnel(grid: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """Carve tunnel between two points"""
        sy, sx = start
        ey, ex = end

        # Simple straight tunnel
        y, x = sy, sx

        while y != ey or x != ex:
            grid[y, x] = 0  # Make floor

            if y < ey:
                y += 1
            elif y > ey:
                y -= 1

            if x < ex:
                x += 1
            elif x > ex:
                x -= 1

        grid[ey, ex] = 0

class RoomAndCorridorGenerator:
    """Generates traditional room-and-corridor dungeons"""

    @staticmethod
    def generate_rooms(width: int, height: int, num_rooms: int,
                      min_size: Tuple[int, int], max_size: Tuple[int, int],
                      separation: int = 2, seed: Optional[int] = None) -> List[Room]:
        """Generate random rooms"""
        if seed is not None:
            random.seed(seed)

        rooms = []
        max_attempts = num_rooms * 10
        attempts = 0

        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1

            # Random room properties
            room_width = random.randint(min_size[0], max_size[0])
            room_height = random.randint(min_size[1], max_size[1])

            # Random position
            x = random.randint(separation, width - room_width - separation)
            y = random.randint(separation, height - room_height - separation)

            # Check for overlaps
            new_room_rect = (x, y, x + room_width, y + room_height)
            overlaps = False

            for room in rooms:
                rx, ry = room.position
                rw, rh = room.size
                existing_rect = (rx - separation, ry - separation,
                               rx + rw + separation, ry + rh + separation)

                if (new_room_rect[0] < existing_rect[2] and
                    new_room_rect[2] > existing_rect[0] and
                    new_room_rect[1] < existing_rect[3] and
                    new_room_rect[3] > existing_rect[1]):
                    overlaps = True
                    break

            if not overlaps:
                # Determine room type
                room_type = RoomAndCorridorGenerator._determine_room_type(
                    len(rooms), num_rooms
                )

                room = Room(
                    room_type=room_type,
                    position=(y, x),
                    size=(room_width, room_height)
                )
                rooms.append(room)

        return rooms

    @staticmethod
    def _determine_room_type(index: int, total_rooms: int) -> RoomType:
        """Determine room type based on position"""
        if index == 0:
            return RoomType.ENTRANCE
        elif index == total_rooms - 1:
            return RoomType.EXIT
        elif index == total_rooms // 2:
            return random.choice([RoomType.BOSS, RoomType.TREASURE, RoomType.SHRINE])
        else:
            # Weighted random selection
            weights = {
                RoomType.CHAMBER: 30,
                RoomType.HALL: 20,
                RoomType.TREASURE: 10,
                RoomType.TRAP: 15,
                RoomType.PUZZLE: 10,
                RoomType.LIBRARY: 5,
                RoomType.KITCHEN: 5,
                RoomType.BARRACKS: 8,
                RoomType.CRYPT: 7,
                RoomType.LABORATORY: 5
            }

            room_types = list(weights.keys())
            probabilities = [weights[rt] for rt in room_types]
            total = sum(probabilities)
            probabilities = [p / total for p in probabilities]

            return np.random.choice(room_types, p=probabilities)

    @staticmethod
    def connect_rooms(rooms: List[Room], width: int, height: int,
                     connection_style: str = "nearest") -> List[Corridor]:
        """Connect rooms with corridors"""
        if len(rooms) < 2:
            return []

        corridors = []

        if connection_style == "nearest":
            # Connect each room to nearest unconnected room
            connected = {0}
            unconnected = set(range(1, len(rooms)))

            while unconnected:
                min_dist = float('inf')
                best_pair = None

                for c_idx in connected:
                    for u_idx in unconnected:
                        room1 = rooms[c_idx]
                        room2 = rooms[u_idx]

                        # Calculate distance between room centers
                        c1 = (room1.position[0] + room1.size[1] // 2,
                              room1.position[1] + room1.size[0] // 2)
                        c2 = (room2.position[0] + room2.size[1] // 2,
                              room2.position[1] + room2.size[0] // 2)

                        dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])

                        if dist < min_dist:
                            min_dist = dist
                            best_pair = (c_idx, u_idx)

                if best_pair:
                    # Create corridor
                    room1 = rooms[best_pair[0]]
                    room2 = rooms[best_pair[1]]

                    # Room centers
                    c1 = (room1.position[0] + room1.size[1] // 2,
                          room1.position[1] + room1.size[0] // 2)
                    c2 = (room2.position[0] + room2.size[1] // 2,
                          room2.position[1] + room2.size[0] // 2)

                    # Generate corridor path
                    path = RoomAndCorridorGenerator._generate_corridor_path(
                        c1, c2, width, height
                    )

                    if path:
                        corridor = Corridor(
                            corridor_type=CorridorType.STRAIGHT,
                            start=c1,
                            end=c2,
                            path=path
                        )
                        corridors.append(corridor)

                        # Update room connections
                        rooms[best_pair[0]].connections.append(best_pair[1])
                        rooms[best_pair[1]].connections.append(best_pair[0])

                        connected.add(best_pair[1])
                        unconnected.remove(best_pair[1])

        elif connection_style == "spanning_tree":
            # Create minimum spanning tree of rooms
            pass  # Implementation would use MST algorithm

        return corridors

    @staticmethod
    def _generate_corridor_path(start: Tuple[int, int], end: Tuple[int, int],
                              width: int, height: int) -> List[Tuple[int, int]]:
        """Generate corridor path between two points"""
        sy, sx = start
        ey, ex = end
        path = []

        # L-shaped corridor (horizontal then vertical or vice versa)
        if random.random() < 0.5:
            # Horizontal first
            for x in range(min(sx, ex), max(sx, ex) + 1):
                path.append((sy, x))
            for y in range(min(sy, ey) + 1, max(sy, ey) + 1):
                path.append((y, ex))
        else:
            # Vertical first
            for y in range(min(sy, ey), max(sy, ey) + 1):
                path.append((y, sx))
            for x in range(min(sx, ex) + 1, max(sx, ex) + 1):
                path.append((ey, x))

        return path

class MazeGenerator:
    """Generates maze-like dungeons using recursive backtracking"""

    @staticmethod
    def generate_maze(width: int, height: int, cell_size: int = 2,
                     seed: Optional[int] = None) -> np.ndarray:
        """Generate maze using recursive backtracking"""
        if seed is not None:
            random.seed(seed)

        # Ensure odd dimensions for proper maze generation
        maze_width = (width // cell_size) * 2 + 1
        maze_height = (height // cell_size) * 2 + 1

        # Initialize maze with all walls
        maze = np.ones((maze_height, maze_width), dtype=int)

        # Recursive backtracking
        def carve_path(y, x):
            maze[y, x] = 0  # Carve current cell

            # Randomize directions
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)

            for dy, dx in directions:
                ny, nx = y + dy, x + dx

                if (0 < ny < maze_height - 1 and 0 < nx < maze_width - 1 and
                    maze[ny, nx] == 1):  # Unvisited
                    # Carve path to neighbor
                    maze[y + dy // 2, x + dx // 2] = 0
                    carve_path(ny, nx)

        # Start from random odd position
        start_y = 1
        start_x = 1
        carve_path(start_y, start_x)

        # Scale up to original dimensions
        scaled_maze = np.zeros((height, width), dtype=int)
        for y in range(maze_height):
            for x in range(maze_width):
                for dy in range(cell_size):
                    for dx in range(cell_size):
                        orig_y = y * cell_size + dy
                        orig_x = x * cell_size + dx
                        if (orig_y < height and orig_x < width):
                            scaled_maze[orig_y, orig_x] = maze[y, x]

        return scaled_maze

class FeaturePlacer:
    """Places dungeon features like traps, puzzles, and treasure"""

    @staticmethod
    def place_traps(rooms: List[Room], corridors: List[Corridor],
                   trap_density: float = 0.3, theme: DungeonTheme = DungeonTheme.CLASSIC) -> None:
        """Place traps in rooms and corridors"""
        theme_traps = FeaturePlacer._get_theme_traps(theme)

        # Place traps in rooms
        for room in rooms:
            if random.random() < trap_density:
                num_traps = random.randint(1, 3)
                for _ in range(num_traps):
                    trap_type = random.choice(theme_traps)
                    room.traps.append(trap_type)

        # Place traps in corridors
        for corridor in corridors:
            if random.random() < trap_density * 0.5:  # Fewer traps in corridors
                trap_type = random.choice(theme_traps)
                corridor.traps.append(trap_type)

    @staticmethod
    def place_puzzles(rooms: List[Room], puzzle_density: float = 0.2,
                     theme: DungeonTheme = DungeonTheme.CLASSIC) -> None:
        """Place puzzles in appropriate rooms"""
        puzzle_rooms = [RoomType.PUZZLE, RoomType.LIBRARY, RoomType.LABORATORY,
                       RoomType.SHRINE, RoomType.THRONE]

        for room in rooms:
            if (room.room_type in puzzle_rooms and
                random.random() < puzzle_density):
                puzzle_type = random.choice(list(PuzzleType))
                room.puzzles.append(puzzle_type)

    @staticmethod
    def place_treasure(rooms: List[Room], treasure_rooms: List[RoomType],
                      avg_value: float = 100.0) -> None:
        """Place treasure in appropriate rooms"""
        for room in rooms:
            if room.room_type in treasure_rooms:
                # Treasure value based on room type and difficulty
                base_value = avg_value

                if room.room_type == RoomType.TREASURE:
                    base_value *= 3.0
                elif room.room_type == RoomType.VAULT:
                    base_value *= 5.0
                elif room.room_type == RoomType.BOSS:
                    base_value *= 2.0

                # Add randomness
                room.treasure_value = base_value * random.uniform(0.5, 2.0)

    @staticmethod
    def place_secret_doors(rooms: List[Room], secret_density: float = 0.1) -> None:
        """Place secret doors in rooms"""
        for room in rooms:
            if random.random() < secret_density:
                # Add 1-2 secret doors
                num_secrets = random.randint(1, 2)
                for _ in range(num_secrets):
                    # Random position on room wall
                    wall = random.choice(['north', 'south', 'east', 'west'])
                    y, x = room.position
                    w, h = room.size

                    if wall == 'north':
                        secret_pos = (y, x + random.randint(0, w - 1))
                    elif wall == 'south':
                        secret_pos = (y + h - 1, x + random.randint(0, w - 1))
                    elif wall == 'east':
                        secret_pos = (y + random.randint(0, h - 1), x + w - 1)
                    else:  # west
                        secret_pos = (y + random.randint(0, h - 1), x)

                    room.secret_doors.append(secret_pos)

    @staticmethod
    def _get_theme_traps(theme: DungeonTheme) -> List[TrapType]:
        """Get trap types appropriate for theme"""
        theme_trap_map = {
            DungeonTheme.CLASSIC: [TrapType.SPIKE_PIT, TrapType.POISON_DART,
                                 TrapType.SWINGING_BLADE, TrapType.PRESSURE_PLATE],
            DungeonTheme.TEMPLE: [TrapType.POISON_DART, TrapType.PRESSURE_PLATE,
                                TrapType.MAGIC_TRAP],
            DungeonTheme.FORTRESS: [TrapType.SWINGING_BLADE, TrapType.ROLLING_BOULDER,
                                  TrapType.FALLING_BLOCK],
            DungeonTheme.TOMB: [TrapType.POISON_DART, TrapType.GAS_TRAP,
                              TrapType.MAGIC_TRAP, TrapType.FALLING_BLOCK],
            DungeonTheme.ICE: [TrapType.FROST_TRAP, TrapType.SPIKE_PIT],
            DungeonTheme.FIRE: [TrapType.FIRE_TRAP, TrapType.ROLLING_BOULDER],
            DungeonTheme.ABYSS: [TrapType.TELEPORT, TrapType.MAGIC_TRAP,
                               TrapType.FALLING_BLOCK]
        }

        return theme_trap_map.get(theme, list(TrapType))

class DungeonCrafter:
    """Main dungeon generation system"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

    def generate_dungeon_level(self, width: int, height: int,
                              level_number: int = 1,
                              theme: DungeonTheme = DungeonTheme.CLASSIC,
                              generation_type: str = "room_corridor") -> DungeonLevel:
        """Generate a single dungeon level"""
        if generation_type == "room_corridor":
            return self._generate_room_corridor_level(
                width, height, level_number, theme
            )
        elif generation_type == "cave":
            return self._generate_cave_level(
                width, height, level_number, theme
            )
        elif generation_type == "maze":
            return self._generate_maze_level(
                width, height, level_number, theme
            )
        else:
            # Hybrid approach
            return self._generate_hybrid_level(
                width, height, level_number, theme
            )

    def _generate_room_corridor_level(self, width: int, height: int,
                                    level_number: int, theme: DungeonTheme) -> DungeonLevel:
        """Generate traditional room-and-corridor dungeon"""
        # Determine parameters based on level
        num_rooms = min(15, 5 + level_number * 2)
        min_size = (3, 3)
        max_size = (8, 8)

        # Generate rooms
        rooms = RoomAndCorridorGenerator.generate_rooms(
            width, height, num_rooms, min_size, max_size,
            seed=self.seed + level_number
        )

        # Connect rooms
        corridors = RoomAndCorridorGenerator.connect_rooms(
            rooms, width, height
        )

        # Create grid
        grid = np.ones((height, width), dtype=int)

        # Carve rooms
        for room in rooms:
            y, x = room.position
            w, h = room.size
            grid[y:y+h, x:x+w] = 0

        # Carve corridors
        for corridor in corridors:
            for cy, cx in corridor.path:
                if 0 <= cy < height and 0 <= cx < width:
                    grid[cy, cx] = 0
                    # Make corridors wider
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = cy + dy, cx + dx
                        if (0 <= ny < height and 0 <= nx < width):
                            grid[ny, nx] = 0

        # Place features
        FeaturePlacer.place_traps(rooms, corridors, theme=theme)
        FeaturePlacer.place_puzzles(rooms, theme=theme)
        FeaturePlacer.place_treasure(
            rooms, [RoomType.TREASURE, RoomType.VAULT, RoomType.BOSS]
        )
        FeaturePlacer.place_secret_doors(rooms)

        # Set entrance and exit
        if rooms:
            entrance_room = rooms[0]
            exit_room = rooms[-1]

            entrance = (entrance_room.position[0] + entrance_room.size[1] // 2,
                       entrance_room.position[1] + entrance_room.size[0] // 2)
            exit_pos = (exit_room.position[0] + exit_room.size[1] // 2,
                       exit_room.position[1] + exit_room.size[0] // 2)
        else:
            entrance = (height // 2, width // 4)
            exit_pos = (height // 2, 3 * width // 4)

        # Add theme-specific features
        special_features = self._get_theme_features(theme)
        ambient_effects = self._get_ambient_effects(theme)

        return DungeonLevel(
            level_number=level_number,
            theme=theme,
            grid=grid,
            rooms=rooms,
            corridors=corridors,
            entrance=entrance,
            exit=exit_pos,
            special_features=special_features,
            ambient_effects=ambient_effects
        )

    def _generate_cave_level(self, width: int, height: int,
                           level_number: int, theme: DungeonTheme) -> DungeonLevel:
        """Generate cave-like dungeon"""
        # Adjust cave parameters based on level
        initial_density = max(0.4, 0.5 - level_number * 0.05)
        iterations = min(8, 4 + level_number)

        # Generate cave
        cave_grid = CellularAutomataGenerator.generate_cave(
            width, height, iterations=iterations,
            initial_density=initial_density,
            seed=self.seed + level_number
        )

        # Connect separate regions
        connected_grid = CellularAutomataGenerator.connect_caves(cave_grid)

        # Identify potential room locations (large open areas)
        rooms = self._identify_cave_rooms(connected_grid)

        # Add entrance and exit
        floor_positions = np.argwhere(connected_grid == 0)
        if len(floor_positions) > 0:
            entrance_pos = tuple(floor_positions[len(floor_positions) // 4])
            exit_pos = tuple(floor_positions[3 * len(floor_positions) // 4])
        else:
            entrance_pos = (height // 2, width // 4)
            exit_pos = (height // 2, 3 * width // 4)

        special_features = self._get_theme_features(theme)
        ambient_effects = self._get_ambient_effects(theme)

        return DungeonLevel(
            level_number=level_number,
            theme=theme,
            grid=connected_grid,
            rooms=rooms,
            corridors=[],  # No explicit corridors in caves
            entrance=entrance_pos,
            exit=exit_pos,
            special_features=special_features,
            ambient_effects=ambient_effects
        )

    def _generate_maze_level(self, width: int, height: int,
                           level_number: int, theme: DungeonTheme) -> DungeonLevel:
        """Generate maze-like dungeon"""
        cell_size = max(1, 4 - level_number // 2)  # Larger cells for deeper levels

        maze_grid = MazeGenerator.generate_maze(
            width, height, cell_size=cell_size,
            seed=self.seed + level_number
        )

        # Add some rooms to break up the maze
        rooms = self._add_maze_rooms(maze_grid, level_number)

        # Set entrance and exit
        floor_positions = np.argwhere(maze_grid == 0)
        if len(floor_positions) > 0:
            entrance_pos = tuple(floor_positions[0])
            exit_pos = tuple(floor_positions[-1])
        else:
            entrance_pos = (1, 1)
            exit_pos = (height - 2, width - 2)

        special_features = self._get_theme_features(theme)
        ambient_effects = self._get_ambient_effects(theme)

        return DungeonLevel(
            level_number=level_number,
            theme=theme,
            grid=maze_grid,
            rooms=rooms,
            corridors=[],
            entrance=entrance_pos,
            exit=exit_pos,
            special_features=special_features,
            ambient_effects=ambient_effects
        )

    def _generate_hybrid_level(self, width: int, height: int,
                             level_number: int, theme: DungeonTheme) -> DungeonLevel:
        """Generate hybrid dungeon with multiple generation types"""
        # Split the level into sections
        section_width = width // 3

        # Generate different section types
        room_section = self._generate_room_corridor_level(
            section_width, height, level_number, theme
        )

        cave_section = self._generate_cave_level(
            section_width, height, level_number, theme
        )

        maze_section = self._generate_maze_level(
            width - 2 * section_width, height, level_number, theme
        )

        # Combine sections
        combined_grid = np.hstack([room_section.grid, cave_section.grid, maze_section.grid])

        # Offset room and corridor positions
        for room in cave_section.rooms:
            y, x = room.position
            room.position = (y, x + section_width)

        for room in maze_section.rooms:
            y, x = room.position
            room.position = (y, x + 2 * section_width)

        # Combine all rooms
        all_rooms = room_section.rooms + cave_section.rooms + maze_section.rooms

        # Create connections between sections
        # Implementation would add connecting corridors

        special_features = self._get_theme_features(theme)
        ambient_effects = self._get_ambient_effects(theme)

        return DungeonLevel(
            level_number=level_number,
            theme=theme,
            grid=combined_grid,
            rooms=all_rooms,
            corridors=room_section.corridors + cave_section.corridors + maze_section.corridors,
            entrance=room_section.entrance,
            exit=maze_section.exit,
            special_features=special_features,
            ambient_effects=ambient_effects
        )

    def _identify_cave_rooms(self, grid: np.ndarray) -> List[Room]:
        """Identify large open areas in cave as rooms"""
        labeled_grid, num_regions = ndimage.label(grid == 0)
        rooms = []

        for region_id in range(1, num_regions + 1):
            region_mask = (labeled_grid == region_id)
            region_size = np.sum(region_mask)

            if region_size > 20:  # Minimum size for a room
                # Find region bounds
                y_indices, x_indices = np.where(region_mask)
                min_y, max_y = y_indices.min(), y_indices.max()
                min_x, max_x = x_indices.min(), x_indices.max()

                room = Room(
                    room_type=RoomType.CHAMBER,
                    position=(min_y, min_x),
                    size=(max_x - min_x + 1, max_y - min_y + 1)
                )
                rooms.append(room)

        return rooms

    def _add_maze_rooms(self, maze_grid: np.ndarray, level_number: int) -> List[Room]:
        """Add rooms to break up maze"""
        rooms = []
        height, width = maze_grid.shape
        num_rooms = min(3, 1 + level_number // 2)

        for _ in range(num_rooms):
            # Find suitable location
            attempts = 0
            while attempts < 50:
                room_size = random.randint(3, 6)
                y = random.randint(room_size, height - room_size - 1)
                x = random.randint(room_size, width - room_size - 1)

                # Check if area is mostly walls
                area = maze_grid[y-room_size:y+room_size+1, x-room_size:x+room_size+1]
                if np.sum(area == 1) > area.size * 0.7:
                    # Carve room
                    maze_grid[y-room_size//2:y+room_size//2+1,
                             x-room_size//2:x+room_size//2+1] = 0

                    room = Room(
                        room_type=RoomType.CHAMBER,
                        position=(y - room_size//2, x - room_size//2),
                        size=(room_size, room_size)
                    )
                    rooms.append(room)
                    break

                attempts += 1

        return rooms

    def _get_theme_features(self, theme: DungeonTheme) -> List[str]:
        """Get special features for theme"""
        theme_features = {
            DungeonTheme.CLASSIC: ["stone pillars", "ancient inscriptions", "cobwebs"],
            DungeonTheme.CAVE: ["stalactites", "underground river", "glowing fungi"],
            DungeonTheme.TEMPLE: ["altars", "religious symbols", "incense burners"],
            DungeonTheme.FORTRESS: ["barricades", "weapon racks", "guard posts"],
            DungeonTheme.TOMB: ["sarcophagi", "ancient murals", "cursed treasures"],
            DungeonTheme.ICE: ["ice sculptures", "frozen treasures", "frost patterns"],
            DungeonTheme.FIRE: ["lava pools", "heat vents", "burning runes"],
            DungeonTheme.ABYSS: ["void portals", "reality distortions", "whispering shadows"]
        }

        return theme_features.get(theme, ["stone walls", "dust", "darkness"])

    def _get_ambient_effects(self, theme: DungeonTheme) -> List[str]:
        """Get ambient effects for theme"""
        ambient_effects = {
            DungeonTheme.CLASSIC: ["dripping water", "distant echoes", "cold drafts"],
            DungeonTheme.CAVE: ["water droplets", "wind howling", "creature calls"],
            DungeonTheme.TEMPLE: ["chanting", "bell chimes", "mystical humming"],
            DungeonTheme.FORTRESS: ["metal clanking", "distant shouts", "torch crackling"],
            DungeonTheme.TOMB: ["spirit whispers", "cold spots", "ancient curses"],
            DungeonTheme.ICE: ["ice cracking", "freezing winds", "magical aurora"],
            DungeonTheme.FIRE: ["flame roaring", "heat waves", "ember crackling"],
            DungeonTheme.ABYSS: ["void whispers", "reality shifting", "madness murmurs"]
        }

        return ambient_effects.get(theme, ["silence", "darkness", "unease"])

    def generate_multi_level_dungeon(self, width: int, height: int,
                                   num_levels: int = 5,
                                   theme: DungeonTheme = DungeonTheme.CLASSIC,
                                   name: Optional[str] = None) -> Dungeon:
        """Generate complete multi-level dungeon"""
        if name is None:
            name = self._generate_dungeon_name(theme)

        levels = []

        for level_num in range(1, num_levels + 1):
            # Vary generation type by level
            generation_types = ["room_corridor", "cave", "maze", "hybrid"]
            gen_type = generation_types[(level_num - 1) % len(generation_types)]

            # Generate level
            level = self.generate_dungeon_level(
                width, height, level_num, theme, gen_type
            )
            levels.append(level)

        # Create boss encounters
        boss_encounters = self._generate_boss_encounters(theme, num_levels)

        # Generate lore
        lore = self._generate_dungeon_lore(theme, num_levels)

        return Dungeon(
            name=name,
            theme=theme,
            levels=levels,
            total_depth=num_levels,
            difficulty_progression=1.0 + num_levels * 0.2,
            lore_description=lore,
            boss_encounters=boss_encounters
        )

    def _generate_dungeon_name(self, theme: DungeonTheme) -> str:
        """Generate procedural dungeon name"""
        prefixes = {
            DungeonTheme.CLASSIC: ["Ancient", "Forgotten", "Lost", "Hidden"],
            DungeonTheme.CAVE: ["Subterranean", "Underground", "Deep", "Abyssal"],
            DungeonTheme.TEMPLE: ["Sacred", "Holy", "Divine", "Blessed"],
            DungeonTheme.FORTRESS: ["Fortified", "Bastion", "Stronghold", "Citadel"],
            DungeonTheme.TOMB: ["Cursed", "Haunted", "Eternal", "Restless"],
            DungeonTheme.ICE: ["Frozen", "Glacial", "Arctic", "Cryo"],
            DungeonTheme.FIRE: ["Burning", "Infernal", "Fiery", "Scorched"],
            DungeonTheme.ABYSS: ["Shadowy", "Dark", "Void", "Eldritch"]
        }

        suffixes = ["Dungeon", "Labyrinth", "Depths", "Crypt", "Tunnels",
                   "Underground", "Catacombs", "Vaults", "Chambers", "Realms"]

        theme_prefixes = prefixes.get(theme, ["Ancient", "Lost"])
        prefix = random.choice(theme_prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix} {suffix}"

    def _generate_boss_encounters(self, theme: DungeonTheme, num_levels: int) -> List[str]:
        """Generate boss encounters for dungeon"""
        boss_templates = {
            DungeonTheme.CLASSIC: ["Ancient Dragon", "Lich Lord", "Demon Prince"],
            DungeonTheme.CAVE: ["Cave Behemoth", "Fungal Queen", "Rock Titan"],
            DungeonTheme.TEMPLE: ["Corrupted High Priest", "Divine Guardian", "Avatar"],
            DungeonTheme.FORTRESS: ["Warlord General", "Siege Commander", "Fortress Warden"],
            DungeonTheme.TOMB: ["Mummy Lord", "Vampire King", "Undead Emperor"],
            DungeonTheme.ICE: ["Frost Giant", "Ice Elemental", "Winter Witch"],
            DungeonTheme.FIRE: ["Fire Giant", "Lava Dragon", "Infernal Behemoth"],
            DungeonTheme.ABYSS: ["Void Lord", "Madness Incarnate", "Shadow Demon"]
        }

        theme_bosses = boss_templates.get(theme, ["Ancient Evil"])
        bosses = []

        # Place bosses at key levels
        boss_levels = [num_levels // 2, num_levels]
        for i, level in enumerate(boss_levels):
            if i < len(theme_bosses):
                bosses.append(f"Level {level}: {theme_bosses[i]}")

        return bosses

    def _generate_dungeon_lore(self, theme: DungeonTheme, num_levels: int) -> str:
        """Generate lore description for dungeon"""
        lore_templates = {
            DungeonTheme.CLASSIC: "This ancient dungeon was built centuries ago by a forgotten civilization, its halls filled with treasures and dangers beyond imagination.",
            DungeonTheme.CAVE: "Deep beneath the earth, these natural caverns have been shaped by both nature and dark forces that dwell in the darkness.",
            DungeonTheme.TEMPLE: "Once a place of worship, this sacred temple has been corrupted by dark forces, its halls now home to twisted guardians and ancient curses.",
            DungeonTheme.FORTRESS: "This mighty fortress once stood as a bastion of defense, now abandoned and filled with the restless spirits of its former defenders.",
            DungeonTheme.TOMB: "The eternal resting place of an ancient ruler, this tomb has been disturbed by grave robbers and dark magic.",
            DungeonTheme.ICE: "Frozen in time by an ancient magical catastrophe, these icy halls preserve the remnants of a lost civilization.",
            DungeonTheme.FIRE: "Forged in the heart of a volcano, this infernal dungeon burns with eternal flames and houses creatures of fire and shadow.",
            DungeonTheme.ABYSS: "A tear in reality itself, this abyssal dungeon connects to realms beyond mortal comprehension."
        }

        base_lore = lore_templates.get(theme, "A mysterious place filled with unknown dangers and treasures.")

        return f"{base_lore} With {num_levels} levels of increasing danger, only the bravest adventurers dare to explore its depths."

# Utility functions
def analyze_dungeon(dungeon: Dungeon) -> Dict:
    """Analyze dungeon characteristics"""
    total_rooms = sum(len(level.rooms) for level in dungeon.levels)
    total_corridors = sum(len(level.corridors) for level in dungeon.levels)

    room_types = defaultdict(int)
    trap_types = defaultdict(int)
    puzzle_types = defaultdict(int)

    for level in dungeon.levels:
        for room in level.rooms:
            room_types[room.room_type.value] += 1
            for trap in room.traps:
                trap_types[trap.value] += 1
            for puzzle in room.puzzles:
                puzzle_types[puzzle.value] += 1

    return {
        'name': dungeon.name,
        'theme': dungeon.theme.value,
        'num_levels': len(dungeon.levels),
        'total_rooms': total_rooms,
        'total_corridors': total_corridors,
        'room_types': dict(room_types),
        'trap_types': dict(trap_types),
        'puzzle_types': dict(puzzle_types),
        'boss_encounters': dungeon.boss_encounters,
        'difficulty_progression': dungeon.difficulty_progression
    }

def export_dungeon_map(level: DungeonLevel, filename: str) -> None:
    """Export dungeon level as image (requires PIL)"""
    try:
        from PIL import Image

        # Create image from grid
        # 0 = floor (white), 1 = wall (black)
        img_array = (1 - level.grid) * 255
        img = Image.fromarray(img_array.astype(np.uint8), mode='L')
        img.save(filename)
    except ImportError:
        print("PIL not available. Install with: pip install Pillow")

if __name__ == "__main__":
    # Example usage
    crafter = DungeonCrafter(seed=42)

    print("Generating multi-level dungeon...")
    dungeon = crafter.generate_multi_level_dungeon(
        width=80, height=60,
        num_levels=5,
        theme=DungeonTheme.CLASSIC
    )

    analysis = analyze_dungeon(dungeon)
    print(f"Generated dungeon: {analysis['name']}")
    print(f"Theme: {analysis['theme']}")
    print(f"Levels: {analysis['num_levels']}")
    print(f"Total rooms: {analysis['total_rooms']}")
    print(f"Total corridors: {analysis['total_corridors']}")
    print(f"Boss encounters: {analysis['boss_encounters']}")

    # Export first level if PIL is available
    try:
        export_dungeon_map(dungeon.levels[0], 'dungeon_level_1.png')
        print("Exported first level as PNG file")
    except:
        print("Could not export dungeon map (PIL not available)")