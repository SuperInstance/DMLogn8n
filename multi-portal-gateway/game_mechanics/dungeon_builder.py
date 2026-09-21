"""
Procedural Dungeon and Encounter Generation System for DMLogn8n
Creates complex dungeons with varied layouts, encounters, and treasures
"""

import random
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class DungeonType(Enum):
    """Types of dungeons with different generation patterns"""
    CAVE = "cave"
    RUINS = "ruins"
    CASTLE = "castle"
    TEMPLE = "temple"
    TOWER = "tower"
    LABYRINTH = "labyrinth"
    CATACOMBS = "catacombs"
    DUNGEON = "dungeon"
    MINE = "mine"
    SEWER = "sewer"
    TOMB = "tomb"
    FORTRESS = "fortress"

class RoomType(Enum):
    """Types of rooms that can be generated"""
    ENTRANCE = "entrance"
    EXIT = "exit"
    CHAMBER = "chamber"
    CORRIDOR = "corridor"
    HALL = "hall"
    TREASURE = "treasure"
    SHRINE = "shrine"
    LIBRARY = "library"
    ARMORY = "armory"
    KITCHEN = "kitchen"
    BARRACKS = "barracks"
    LABORATORY = "laboratory"
    PRISON = "prison"
    THRONE_ROOM = "throne_room"
    VAULT = "vault"
    FOUNTAIN = "fountain"
    ALTAR = "altar"
    WORKSHOP = "workshop"

class EncounterType(Enum):
    """Types of encounters"""
    COMBAT = "combat"
    PUZZLE = "puzzle"
    TRAP = "trap"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    BOSS = "boss"
    TREASURE = "treasure"
    STORY = "story"
    CHALLENGE = "challenge"
    MYSTERY = "mystery"

class TileType(Enum):
    """Types of tiles in dungeon grid"""
    WALL = "wall"
    FLOOR = "floor"
    DOOR = "door"
    SECRET_DOOR = "secret_door"
    CHEST = "chest"
    TRAP = "trap"
    OBSTACLE = "obstacle"
    WATER = "water"
    LAVA = "lava"
    PIT = "pit"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"
    PORTAL = "portal"
    ALTAR = "altar"
    FOUNTAIN = "fountain"
    SPECIAL = "special"

class DifficultyLevel(Enum):
    """Dungeon difficulty levels"""
    TRIVIAL = 1
    EASY = 2
    NORMAL = 3
    CHALLENGING = 4
    HARD = 5
    EXPERT = 6
    MASTER = 7
    LEGENDARY = 8

@dataclass
class Position:
    """2D position in dungeon"""
    x: int
    y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def manhattan_distance(self, other: 'Position') -> int:
        """Calculate Manhattan distance"""
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass
class Room:
    """Room in dungeon"""
    id: str
    room_type: RoomType
    position: Position  # Top-left corner
    width: int
    height: int
    center: Position = field(init=False)

    # Room properties
    theme: str = "generic"
    description: str = ""
    ambient_effects: List[str] = field(default_factory=list)
    lighting: str = "dim"
    temperature: str = "normal"

    # Contents
    encounters: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # Connected room IDs

    # Generation properties
    min_size: Tuple[int, int] = (3, 3)
    max_size: Tuple[int, int] = (10, 10)
    required: bool = False

    def __post_init__(self):
        """Calculate center position"""
        self.center = Position(
            self.position.x + self.width // 2,
            self.position.y + self.height // 2
        )

    def contains_position(self, pos: Position) -> bool:
        """Check if position is within room"""
        return (self.position.x <= pos.x < self.position.x + self.width and
                self.position.y <= pos.y < self.position.y + self.height)

    def get_tiles(self) -> List[Position]:
        """Get all tile positions in room"""
        tiles = []
        for x in range(self.position.x, self.position.x + self.width):
            for y in range(self.position.y, self.position.y + self.height):
                tiles.append(Position(x, y))
        return tiles

    def get_perimeter_tiles(self) -> List[Position]:
        """Get tiles on room perimeter"""
        tiles = []
        for x in range(self.position.x, self.position.x + self.width):
            tiles.append(Position(x, self.position.y))  # Top wall
            tiles.append(Position(x, self.position.y + self.height - 1))  # Bottom wall

        for y in range(self.position.y + 1, self.position.y + self.height - 1):
            tiles.append(Position(self.position.x, y))  # Left wall
            tiles.append(Position(self.position.x + self.width - 1, y))  # Right wall

        return tiles

@dataclass
class Encounter:
    """Encounter in dungeon"""
    id: str
    encounter_type: EncounterType
    room_id: str
    position: Position
    difficulty: int
    description: str

    # Encounter specifics
    enemies: List[Dict[str, Any]] = field(default_factory=list)
    puzzle_type: Optional[str] = None
    trap_type: Optional[str] = None
    reward_level: int = 1
    trigger_condition: Optional[str] = None
    defeated: bool = False

    # Dynamic properties
    respawnable: bool = False
    respawn_time: Optional[int] = None
    one_time: bool = False

@dataclass
class DungeonTheme:
    """Theme for dungeon generation"""
    name: str
    description: str
    tile_palette: Dict[TileType, List[str]] = field(default_factory=dict)
    room_types: List[RoomType] = field(default_factory=list)
    encounter_types: List[EncounterType] = field(default_factory=list)
    environmental_effects: List[str] = field(default_factory=list)
    treasure_multiplier: float = 1.0
    danger_multiplier: float = 1.0

@dataclass
class Dungeon:
    """Complete dungeon with all components"""
    id: str
    name: str
    dungeon_type: DungeonType
    theme: DungeonTheme
    difficulty: DifficultyLevel
    size: str  # small, medium, large, huge

    # Layout
    width: int
    height: int
    grid: List[List[TileType]]
    rooms: Dict[str, Room]
    encounters: Dict[str, Encounter]
    items: List[Dict[str, Any]]
    features: List[Dict[str, Any]]

    # Properties
    entrance_position: Position
    exit_position: Position
    boss_room_id: Optional[str] = None
    treasure_rooms: List[str] = field(default_factory=list)
    secret_rooms: List[str] = field(default_factory=list)

    # Generation metadata
    seed: int
    created_at: datetime = field(default_factory=datetime.now)
    estimated_playtime: int = 0  # Minutes
    recommended_level: int = 1

class RoomGenerator:
    """Generates individual rooms"""

    def __init__(self):
        self.room_templates = self._load_room_templates()

    def _load_room_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined room templates"""
        return {
            "square_chamber": {
                "min_size": (4, 4),
                "max_size": (8, 8),
                "shape": "rectangle",
                "features": ["pillars", "torch_sconces", "rugs"]
            },
            "large_hall": {
                "min_size": (8, 6),
                "max_size": (15, 10),
                "shape": "rectangle",
                "features": ["columns", "statues", "fountain"]
            },
            "circular_room": {
                "min_size": (5, 5),
                "max_size": (10, 10),
                "shape": "circle",
                "features": ["altars", "mosaic_floor", "candles"]
            },
            "corridor": {
                "min_size": (2, 4),
                "max_size": (4, 12),
                "shape": "rectangle",
                "features": ["torches", "cobwebs"]
            },
            "treasure_vault": {
                "min_size": (3, 3),
                "max_size": (6, 6),
                "shape": "rectangle",
                "features": ["chests", "pedestals", "traps"]
            },
            "laboratory": {
                "min_size": (5, 5),
                "max_size": (10, 8),
                "shape": "rectangle",
                "features": ["alchemy_tables", "bookshelves", "cauldrons"]
            },
            "prison_cell": {
                "min_size": (3, 3),
                "max_size": (5, 5),
                "shape": "rectangle",
                "features": ["bars", "chains", "straw"]
            },
            "throne_room": {
                "min_size": (10, 8),
                "max_size": (20, 15),
                "shape": "rectangle",
                "features": ["throne", "banners", "guards"]
            }
        }

    def generate_room(self, room_type: RoomType, position: Position,
                     constraints: Optional[Dict[str, Any]] = None) -> Room:
        """Generate a room of specified type"""
        constraints = constraints or {}

        # Select template based on room type
        template_name = self._select_template(room_type)
        template = self.room_templates.get(template_name, self.room_templates["square_chamber"])

        # Determine room size
        min_width, min_height = template["min_size"]
        max_width, max_height = template["max_size"]

        width = random.randint(min_width, max_width)
        height = random.randint(min_height, max_height)

        # Apply constraints
        if "max_width" in constraints:
            width = min(width, constraints["max_width"])
        if "max_height" in constraints:
            height = min(height, constraints["max_height"])

        # Create room
        room = Room(
            id=str(uuid.uuid4()),
            room_type=room_type,
            position=position,
            width=width,
            height=height,
            theme=template_name,
            description=f"A {room_type.value} with {template['shape']} shape"
        )

        # Add features
        room.features = random.sample(template["features"],
                                    min(len(template["features"]), random.randint(1, 3)))

        return room

    def _select_template(self, room_type: RoomType) -> str:
        """Select appropriate template for room type"""
        template_map = {
            RoomType.ENTRANCE: "square_chamber",
            RoomType.EXIT: "square_chamber",
            RoomType.CHAMBER: "square_chamber",
            RoomType.HALL: "large_hall",
            RoomType.TREASURE: "treasure_vault",
            RoomType.LIBRARY: "large_hall",
            RoomType.ARMORY: "large_hall",
            RoomType.BARRACKS: "square_chamber",
            RoomType.LABORATORY: "laboratory",
            RoomType.PRISON: "prison_cell",
            RoomType.THRONE_ROOM: "throne_room",
            RoomType.VAULT: "treasure_vault",
            RoomType.SHRINE: "circular_room",
            RoomType.ALTAR: "circular_room",
            RoomType.CORRIDOR: "corridor"
        }

        return template_map.get(room_type, "square_chamber")

class EncounterGenerator:
    """Generates encounters for rooms"""

    def __init__(self):
        self.enemy_templates = self._load_enemy_templates()
        self.trap_templates = self._load_trap_templates()
        self.puzzle_templates = self._load_puzzle_templates()

    def _load_enemy_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load enemy templates for encounters"""
        return {
            "goblin": {"level": 1, "threat": "low", "count": (2, 4)},
            "orc": {"level": 3, "threat": "medium", "count": (1, 3)},
            "skeleton": {"level": 2, "threat": "low", "count": (3, 6)},
            "zombie": {"level": 2, "threat": "low", "count": (2, 5)},
            "giant_spider": {"level": 4, "threat": "medium", "count": (1, 2)},
            "dark_mage": {"level": 5, "threat": "high", "count": 1},
            "minotaur": {"level": 7, "threat": "high", "count": 1},
            "dragon": {"level": 10, "threat": "boss", "count": 1},
            "bandit": {"level": 2, "threat": "low", "count": (2, 4)},
            "ghost": {"level": 4, "threat": "medium", "count": (1, 3)}
        }

    def _load_trap_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load trap templates"""
        return {
            "spike_pit": {"damage": "high", "detect_difficulty": 2, "disarm_difficulty": 3},
            "poison_dart": {"damage": "medium", "detect_difficulty": 3, "disarm_difficulty": 4},
            "pressure_plate": {"damage": "medium", "detect_difficulty": 2, "disarm_difficulty": 3},
            "magic_mine": {"damage": "high", "detect_difficulty": 4, "disarm_difficulty": 5},
            "falling_rocks": {"damage": "high", "detect_difficulty": 3, "disarm_difficulty": 2},
            "gas_trap": {"damage": "medium", "detect_difficulty": 3, "disarm_difficulty": 4},
            "teleport_trap": {"damage": "none", "detect_difficulty": 5, "disarm_difficulty": 5}
        }

    def _load_puzzle_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load puzzle templates"""
        return {
            "riddle_door": {"difficulty": 3, "type": "intellectual", "time_limit": 300},
            "lever_puzzle": {"difficulty": 2, "type": "mechanical", "time_limit": 600},
            "symbol_sequence": {"difficulty": 4, "type": "pattern", "time_limit": 180},
            "mirror_puzzle": {"difficulty": 5, "type": "spatial", "time_limit": 420},
            "weight_balance": {"difficulty": 3, "type": "mathematical", "time_limit": 300},
            "color_matching": {"difficulty": 2, "type": "pattern", "time_limit": 240},
            "maze_puzzle": {"difficulty": 4, "type": "navigation", "time_limit": 900}
        }

    def generate_encounter(self, room_type: RoomType, difficulty: DifficultyLevel,
                          room_id: str, position: Position) -> Optional[Encounter]:
        """Generate encounter for a room"""
        # Determine encounter type based on room type and difficulty
        encounter_type = self._select_encounter_type(room_type, difficulty)

        # Skip encounters in certain rooms
        if room_type in [RoomType.ENTRANCE, RoomType.CORRIDOR]:
            if random.random() < 0.7:  # 70% chance of no encounter
                return None

        encounter = Encounter(
            id=str(uuid.uuid4()),
            encounter_type=encounter_type,
            room_id=room_id,
            position=position,
            difficulty=difficulty.value,
            description=f"A {encounter_type.value} challenge"
        )

        # Generate encounter details
        if encounter_type == EncounterType.COMBAT:
            self._generate_combat_encounter(encounter, difficulty)
        elif encounter_type == EncounterType.TRAP:
            self._generate_trap_encounter(encounter, difficulty)
        elif encounter_type == EncounterType.PUZZLE:
            self._generate_puzzle_encounter(encounter, difficulty)
        elif encounter_type == EncounterType.BOSS:
            self._generate_boss_encounter(encounter, difficulty)
        elif encounter_type == EncounterType.TREASURE:
            self._generate_treasure_encounter(encounter, difficulty)

        return encounter

    def _select_encounter_type(self, room_type: RoomType,
                              difficulty: DifficultyLevel) -> EncounterType:
        """Select appropriate encounter type"""
        type_weights = {
            EncounterType.COMBAT: 0.4,
            EncounterType.TRAP: 0.2,
            EncounterType.PUZZLE: 0.15,
            EncounterType.TREASURE: 0.1,
            EncounterType.SOCIAL: 0.05,
            EncounterType.EXPLORATION: 0.05,
            EncounterType.STORY: 0.03,
            EncounterType.BOSS: 0.02
        }

        # Adjust weights based on room type
        if room_type == RoomType.TREASURE:
            type_weights[EncounterType.TRAP] = 0.4
            type_weights[EncounterType.COMBAT] = 0.3
            type_weights[EncounterType.TREASURE] = 0.2
        elif room_type == RoomType.LIBRARY:
            type_weights[EncounterType.PUZZLE] = 0.4
            type_weights[EncounterType.STORY] = 0.3
        elif room_type == RoomType.PRISON:
            type_weights[EncounterType.COMBAT] = 0.5
            type_weights[EncounterType.SOCIAL] = 0.2
        elif room_type == RoomType.THRONE_ROOM:
            type_weights[EncounterType.BOSS] = 0.5
            type_weights[EncounterType.COMBAT] = 0.3

        # Adjust for difficulty
        if difficulty.value >= 5:
            type_weights[EncounterType.COMBAT] *= 1.5
            type_weights[EncounterType.BOSS] *= 1.2
        elif difficulty.value <= 2:
            type_weights[EncounterType.TREASURE] *= 1.5
            type_weights[EncounterType.EXPLORATION] *= 1.3

        # Normalize weights
        total_weight = sum(type_weights.values())
        for key in type_weights:
            type_weights[key] /= total_weight

        # Select encounter type
        rand = random.random()
        cumulative = 0
        for encounter_type, weight in type_weights.items():
            cumulative += weight
            if rand <= cumulative:
                return encounter_type

        return EncounterType.COMBAT

    def _generate_combat_encounter(self, encounter: Encounter,
                                  difficulty: DifficultyLevel):
        """Generate combat encounter"""
        # Select enemies based on difficulty
        suitable_enemies = []
        for enemy_name, enemy_data in self.enemy_templates.items():
            if abs(enemy_data["level"] - difficulty.value) <= 2:
                suitable_enemies.append((enemy_name, enemy_data))

        if not suitable_enemies:
            suitable_enemies = list(self.enemy_templates.items())

        # Select 1-3 enemy types
        num_enemy_types = min(3, random.randint(1, difficulty.value // 2 + 1))
        selected_enemies = random.sample(suitable_enemies, num_enemy_types)

        # Generate enemy count
        for enemy_name, enemy_data in selected_enemies:
            min_count, max_count = enemy_data["count"]
            if isinstance(max_count, int):
                count = random.randint(min_count, max_count)
            else:
                count = random.randint(min_count, int(max_count))

            for _ in range(count):
                encounter.enemies.append({
                    "type": enemy_name,
                    "level": enemy_data["level"],
                    "hp": enemy_data["level"] * 10,
                    "attack": enemy_data["level"] * 2,
                    "loot": self._generate_enemy_loot(enemy_data["level"])
                })

        encounter.description = f"A group of {' and '.join([e[0] for e in selected_enemies])}"

    def _generate_trap_encounter(self, encounter: Encounter,
                                difficulty: DifficultyLevel):
        """Generate trap encounter"""
        # Select trap based on difficulty
        suitable_traps = []
        for trap_name, trap_data in self.trap_templates.items():
            trap_level = trap_data["disarm_difficulty"]
            if abs(trap_level - difficulty.value) <= 2:
                suitable_traps.append((trap_name, trap_data))

        if not suitable_traps:
            suitable_traps = list(self.trap_templates.items())

        trap_name, trap_data = random.choice(suitable_traps)
        encounter.trap_type = trap_name
        encounter.description = f"A {trap_name.replace('_', ' ')} trap"

    def _generate_puzzle_encounter(self, encounter: Encounter,
                                  difficulty: DifficultyLevel):
        """Generate puzzle encounter"""
        # Select puzzle based on difficulty
        suitable_puzzles = []
        for puzzle_name, puzzle_data in self.puzzle_templates.items():
            puzzle_level = puzzle_data["difficulty"]
            if abs(puzzle_level - difficulty.value) <= 2:
                suitable_puzzles.append((puzzle_name, puzzle_data))

        if not suitable_puzzles:
            suitable_puzzles = list(self.puzzle_templates.items())

        puzzle_name, puzzle_data = random.choice(suitable_puzzles)
        encounter.puzzle_type = puzzle_name
        encounter.description = f"A {puzzle_name.replace('_', ' ')} puzzle"

    def _generate_boss_encounter(self, encounter: Encounter,
                                difficulty: DifficultyLevel):
        """Generate boss encounter"""
        # Select boss enemy
        boss_enemies = [e for e in self.enemy_templates.items()
                       if e[1]["threat"] == "boss" or e[1]["level"] >= difficulty.value + 2]

        if boss_enemies:
            boss_name, boss_data = random.choice(boss_enemies)
            encounter.enemies.append({
                "type": boss_name,
                "level": boss_data["level"],
                "hp": boss_data["level"] * 20,
                "attack": boss_data["level"] * 3,
                "boss": True,
                "loot": self._generate_enemy_loot(boss_data["level"] * 2)
            })
            encounter.description = f"A formidable {boss_name} boss"
        else:
            # Generate mini-boss from regular enemies
            self._generate_combat_encounter(encounter, DifficultyLevel(difficulty.value + 2))
            if encounter.enemies:
                encounter.enemies[0]["boss"] = True
                encounter.description = f"A powerful {encounter.enemies[0]['type']} leader"

    def _generate_treasure_encounter(self, encounter: Encounter,
                                    difficulty: DifficultyLevel):
        """Generate treasure encounter"""
        encounter.reward_level = difficulty.value
        encounter.description = "A cache of valuable treasures"

    def _generate_enemy_loot(self, enemy_level: int) -> List[Dict[str, Any]]:
        """Generate loot for an enemy"""
        loot = []
        num_items = random.randint(0, enemy_level // 3 + 1)

        for _ in range(num_items):
            loot.append({
                "type": random.choice(["weapon", "armor", "consumable", "material"]),
                "value": enemy_level * random.randint(5, 15),
                "rarity": random.choice(["common", "uncommon", "rare"])
            })

        return loot

class DungeonBuilder:
    """Main dungeon builder that orchestrates generation"""

    def __init__(self):
        self.room_generator = RoomGenerator()
        self.encounter_generator = EncounterGenerator()
        self.themes = self._load_themes()

    def _load_themes(self) -> Dict[str, DungeonTheme]:
        """Load dungeon themes"""
        return {
            "abandoned_mine": DungeonTheme(
                name="Abandoned Mine",
                description="Dark tunnels filled with mining equipment and dangers",
                room_types=[RoomType.CHAMBER, RoomType.CORRIDOR, RoomType.TREASURE],
                encounter_types=[EncounterType.COMBAT, EncounterType.TRAP],
                environmental_effects=["darkness", "dust", "unstable_rocks"],
                treasure_multiplier=1.2,
                danger_multiplier=1.3
            ),
            "ancient_temple": DungeonTheme(
                name="Ancient Temple",
                description="Sacred ruins filled with divine magic and puzzles",
                room_types=[RoomType.SHRINE, RoomType.ALTAR, RoomType.CHAMBER, RoomType.HALL],
                encounter_types=[EncounterType.PUZZLE, EncounterType.SOCIAL, EncounterType.COMBAT],
                environmental_effects=["divine_aura", "ancient_wards", "mysterious_light"],
                treasure_multiplier=1.5,
                danger_multiplier=1.0
            ),
            "dark_fortress": DungeonTheme(
                name="Dark Fortress",
                description="Military structure filled with armed defenders",
                room_types=[RoomType.BARRACKS, RoomType.ARMORY, RoomType.THRONE_ROOM],
                encounter_types=[EncounterType.COMBAT, EncounterType.TRAP],
                environmental_effects=["torches", "weapon_racks", "guard_patrols"],
                treasure_multiplier=1.0,
                danger_multiplier=1.4
            ),
            "wizard_tower": DungeonTheme(
                name="Wizard Tower",
                description="Magical laboratory filled with arcane experiments",
                room_types=[RoomType.LIBRARY, RoomType.LABORATORY, RoomType.CHAMBER],
                encounter_types=[EncounterType.PUZZLE, EncounterType.COMBAT, EncounterType.MYSTERY],
                environmental_effects=["magical_auras", "floating_objects", "strange_creatures"],
                treasure_multiplier=1.8,
                danger_multiplier=1.2
            ),
            "monster_lair": DungeonTheme(
                name="Monster Lair",
                description="Natural caves inhabited by dangerous creatures",
                room_types=[RoomType.CHAMBER, RoomType.CORRIDOR, RoomType.TREASURE],
                encounter_types=[EncounterType.COMBAT, EncounterType.TRAP],
                environmental_effects=["bones", "nesting_materials", "territorial_marks"],
                treasure_multiplier=0.8,
                danger_multiplier=1.6
            )
        }

    def generate_dungeon(self, dungeon_type: DungeonType, difficulty: DifficultyLevel,
                        size: str = "medium", theme_name: Optional[str] = None,
                        custom_params: Optional[Dict[str, Any]] = None) -> Dungeon:
        """Generate a complete dungeon"""
        seed = random.randint(0, 1000000)
        random.seed(seed)

        custom_params = custom_params or {}

        # Select theme
        theme = self._select_theme(dungeon_type, theme_name)

        # Determine dungeon dimensions
        width, height = self._get_dungeon_dimensions(size)

        # Create dungeon structure
        dungeon = Dungeon(
            id=str(uuid.uuid4()),
            name=f"{theme.name} ({dungeon_type.value.title()})",
            dungeon_type=dungeon_type,
            theme=theme,
            difficulty=difficulty,
            size=size,
            width=width,
            height=height,
            grid=[[TileType.WALL for _ in range(width)] for _ in range(height)],
            rooms={},
            encounters={},
            items=[],
            features=[],
            entrance_position=Position(1, 1),
            exit_position=Position(width - 2, height - 2),
            seed=seed,
            recommended_level=difficulty.value * 3
        )

        # Generate dungeon layout
        self._generate_dungeon_layout(dungeon)

        # Place rooms
        self._place_rooms(dungeon)

        # Create connections between rooms
        self._create_room_connections(dungeon)

        # Generate encounters
        self._generate_encounters(dungeon)

        # Place special features
        self._place_special_features(dungeon)

        # Calculate estimated playtime
        dungeon.estimated_playtime = len(dungeon.rooms) * 15 + len(dungeon.encounters) * 10

        random.seed()  # Reset seed

        return dungeon

    def _select_theme(self, dungeon_type: DungeonType,
                     theme_name: Optional[str] = None) -> DungeonTheme:
        """Select appropriate theme for dungeon"""
        if theme_name and theme_name in self.themes:
            return self.themes[theme_name]

        # Select theme based on dungeon type
        theme_map = {
            DungeonType.MINE: "abandoned_mine",
            DungeonType.TEMPLE: "ancient_temple",
            DungeonType.CASTLE: "dark_fortress",
            DungeonType.TOWER: "wizard_tower",
            DungeonType.CAVE: "monster_lair",
            DungeonType.RUINS: "ancient_temple",
            DungeonType.FORTRESS: "dark_fortress",
            DungeonType.DUNGEON: "dark_fortress",
            DungeonType.CATACOMBS: "ancient_temple",
            DungeonType.TOMB: "ancient_temple"
        }

        theme_name = theme_map.get(dungeon_type, "dark_fortress")
        return self.themes[theme_name]

    def _get_dungeon_dimensions(self, size: str) -> Tuple[int, int]:
        """Get dungeon dimensions based on size"""
        size_map = {
            "small": (30, 30),
            "medium": (50, 50),
            "large": (80, 80),
            "huge": (120, 120)
        }

        return size_map.get(size, (50, 50))

    def _generate_dungeon_layout(self, dungeon: Dungeon):
        """Generate basic dungeon layout"""
        # Start with all walls
        dungeon.grid = [[TileType.WALL for _ in range(dungeon.width)]
                       for _ in range(dungeon.height)]

        # Generate room count based on size
        room_counts = {
            "small": (5, 8),
            "medium": (8, 15),
            "large": (15, 25),
            "huge": (25, 40)
        }

        min_rooms, max_rooms = room_counts[dungeon.size]
        dungeon.target_room_count = random.randint(min_rooms, max_rooms)

    def _place_rooms(self, dungeon: Dungeon):
        """Place rooms in dungeon"""
        rooms_needed = dungeon.target_room_count
        placed_rooms = []
        max_attempts = rooms_needed * 10
        attempts = 0

        # Place entrance room first
        entrance_room = self.room_generator.generate_room(
            RoomType.ENTRANCE,
            Position(2, 2)
        )
        dungeon.rooms[entrance_room.id] = entrance_room
        placed_rooms.append(entrance_room)
        self._carve_room(dungeon, entrance_room)

        # Place exit room last
        exit_placed = False

        while len(placed_rooms) < rooms_needed and attempts < max_attempts:
            attempts += 1

            # Select room type
            room_type = self._select_room_type(dungeon, placed_rooms, exit_placed)

            # Find valid position
            room = self._find_room_position(dungeon, room_type, placed_rooms)
            if not room:
                continue

            # Check for overlaps
            if self._check_room_overlap(room, placed_rooms):
                continue

            # Place room
            dungeon.rooms[room.id] = room
            placed_rooms.append(room)
            self._carve_room(dungeon, room)

            # Check if we should place exit
            if not exit_placed and len(placed_rooms) >= rooms_needed - 2:
                exit_room = self._generate_exit_room(dungeon, placed_rooms)
                if exit_room:
                    dungeon.rooms[exit_room.id] = exit_room
                    placed_rooms.append(exit_room)
                    self._carve_room(dungeon, exit_room)
                    dungeon.exit_position = exit_room.center
                    dungeon.boss_room_id = exit_room.id
                    exit_placed = True

        # Ensure we have minimum required rooms
        if len(placed_rooms) < 3:
            # Add more basic rooms
            for _ in range(3 - len(placed_rooms)):
                room = self._find_room_position(dungeon, RoomType.CHAMBER, placed_rooms)
                if room:
                    dungeon.rooms[room.id] = room
                    placed_rooms.append(room)
                    self._carve_room(dungeon, room)

    def _select_room_type(self, dungeon: Dungeon, placed_rooms: List[Room],
                         exit_placed: bool) -> RoomType:
        """Select appropriate room type"""
        # Weighted random selection
        weights = {
            RoomType.CHAMBER: 0.3,
            RoomType.CORRIDOR: 0.25,
            RoomType.HALL: 0.15,
            RoomType.TREASURE: 0.1,
            RoomType.SHRINE: 0.08,
            RoomType.LIBRARY: 0.05,
            RoomType.ARMORY: 0.05,
            RoomType.BARRACKS: 0.02
        }

        # Adjust based on theme
        if dungeon.theme.name == "ancient_temple":
            weights[RoomType.SHRINE] = 0.2
            weights[RoomType.ALTAR] = 0.15
        elif dungeon.theme.name == "dark_fortress":
            weights[RoomType.BARRACKS] = 0.15
            weights[RoomType.ARMORY] = 0.1
        elif dungeon.theme.name == "wizard_tower":
            weights[RoomType.LIBRARY] = 0.2
            weights[RoomType.LABORATORY] = 0.15

        # Normalize weights
        total_weight = sum(weights.values())
        for key in weights:
            weights[key] /= total_weight

        # Select room type
        rand = random.random()
        cumulative = 0
        for room_type, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return room_type

        return RoomType.CHAMBER

    def _find_room_position(self, dungeon: Dungeon, room_type: RoomType,
                           placed_rooms: List[Room]) -> Optional[Room]:
        """Find valid position for a new room"""
        max_attempts = 50

        for _ in range(max_attempts):
            # Random position
            if placed_rooms:
                # Place near existing rooms
                reference_room = random.choice(placed_rooms)
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                position = Position(
                    max(1, min(dungeon.width - 10, reference_room.position.x + offset_x)),
                    max(1, min(dungeon.height - 10, reference_room.position.y + offset_y))
                )
            else:
                position = Position(
                    random.randint(1, dungeon.width - 10),
                    random.randint(1, dungeon.height - 10)
                )

            # Generate room
            constraints = {
                "max_width": min(10, dungeon.width - position.x - 1),
                "max_height": min(10, dungeon.height - position.y - 1)
            }

            room = self.room_generator.generate_room(room_type, position, constraints)

            # Check if room fits in bounds
            if (room.position.x + room.width >= dungeon.width or
                room.position.y + room.height >= dungeon.height):
                continue

            return room

        return None

    def _check_room_overlap(self, room: Room, placed_rooms: List[Room]) -> bool:
        """Check if room overlaps with existing rooms"""
        for existing_room in placed_rooms:
            # Check bounding box overlap
            if not (room.position.x + room.width < existing_room.position.x or
                    existing_room.position.x + existing_room.width < room.position.x or
                    room.position.y + room.height < existing_room.position.y or
                    existing_room.position.y + existing_room.height < room.position.y):
                # Check actual tile overlap
                room_tiles = set(room.get_tiles())
                existing_tiles = set(existing_room.get_tiles())
                if room_tiles & existing_tiles:
                    return True

        return False

    def _carve_room(self, dungeon: Dungeon, room: Room):
        """Carve room into dungeon grid"""
        for x in range(room.position.x, room.position.x + room.width):
            for y in range(room.position.y, room.position.y + room.height):
                if 0 <= x < dungeon.width and 0 <= y < dungeon.height:
                    dungeon.grid[y][x] = TileType.FLOOR

    def _generate_exit_room(self, dungeon: Dungeon, placed_rooms: List[Room]) -> Optional[Room]:
        """Generate exit room"""
        # Find farthest position from entrance
        entrance = dungeon.rooms[list(dungeon.rooms.keys())[0]]
        max_distance = 0
        best_position = Position(dungeon.width // 2, dungeon.height // 2)

        for x in range(5, dungeon.width - 5):
            for y in range(5, dungeon.height - 5):
                if dungeon.grid[y][x] == TileType.FLOOR:
                    pos = Position(x, y)
                    distance = pos.distance_to(entrance.center)
                    if distance > max_distance:
                        max_distance = distance
                        best_position = pos

        # Create exit room
        exit_room = self.room_generator.generate_room(
            RoomType.EXIT,
            Position(max(1, best_position.x - 3), max(1, best_position.y - 3))
        )

        return exit_room

    def _create_room_connections(self, dungeon: Dungeon):
        """Create connections between rooms"""
        rooms = list(dungeon.rooms.values())

        # Create minimum spanning tree to ensure all rooms are connected
        connected = {rooms[0].id}
        unconnected = {room.id for room in rooms[1:]}

        while unconnected:
            # Find closest connection
            min_distance = float('inf')
            best_connection = None

            for connected_id in connected:
                connected_room = dungeon.rooms[connected_id]
                for unconnected_id in unconnected:
                    unconnected_room = dungeon.rooms[unconnected_id]
                    distance = connected_room.center.distance_to(unconnected_room.center)
                    if distance < min_distance:
                        min_distance = distance
                        best_connection = (connected_room, unconnected_room)

            if best_connection:
                # Create corridor
                self._create_corridor(dungeon, best_connection[0], best_connection[1])
                best_connection[0].connections.append(best_connection[1].id)
                best_connection[1].connections.append(best_connection[0].id)
                connected.add(best_connection[1].id)
                unconnected.remove(best_connection[1].id)

        # Add some additional connections for loops
        num_extra_connections = min(3, len(rooms) // 4)
        for _ in range(num_extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice([r for r in rooms if r.id != room1.id and r.id not in room1.connections])
            if room2:
                self._create_corridor(dungeon, room1, room2)
                room1.connections.append(room2.id)
                room2.connections.append(room1.id)

    def _create_corridor(self, dungeon: Dungeon, room1: Room, room2: Room):
        """Create corridor between two rooms"""
        start = room1.center
        end = room2.center

        # Simple L-shaped corridor
        current = Position(start.x, start.y)

        # Move horizontally
        while current.x != end.x:
            current.x += 1 if current.x < end.x else -1
            if 0 <= current.x < dungeon.width and 0 <= current.y < dungeon.height:
                dungeon.grid[current.y][current.x] = TileType.FLOOR

        # Move vertically
        while current.y != end.y:
            current.y += 1 if current.y < end.y else -1
            if 0 <= current.x < dungeon.width and 0 <= current.y < dungeon.height:
                dungeon.grid[current.y][current.x] = TileType.FLOOR

    def _generate_encounters(self, dungeon: Dungeon):
        """Generate encounters for rooms"""
        for room in dungeon.rooms.values():
            # Skip entrance for no encounter
            if room.room_type == RoomType.ENTRANCE:
                continue

            # Generate encounter
            encounter = self.encounter_generator.generate_encounter(
                room.room_type, dungeon.difficulty, room.id, room.center
            )

            if encounter:
                dungeon.encounters[encounter.id] = encounter
                room.encounters.append(encounter.id)

    def _place_special_features(self, dungeon: Dungeon):
        """Place special features in dungeon"""
        # Place stairs
        if dungeon.width > 20 and dungeon.height > 20:
            # Upstairs near entrance
            entrance = dungeon.rooms[list(dungeon.rooms.keys())[0]]
            stairs_up_pos = Position(
                entrance.position.x + 1,
                entrance.position.y + 1
            )
            if 0 <= stairs_up_pos.x < dungeon.width and 0 <= stairs_up_pos.y < dungeon.height:
                dungeon.grid[stairs_up_pos.y][stairs_up_pos.x] = TileType.STAIRS_UP

        # Place fountains in certain rooms
        for room in dungeon.rooms.values():
            if room.room_type in [RoomType.SHRINE, RoomType.HALL] and random.random() < 0.3:
                fountain_pos = room.center
                if 0 <= fountain_pos.x < dungeon.width and 0 <= fountain_pos.y < dungeon.height:
                    dungeon.grid[fountain_pos.y][fountain_pos.x] = TileType.FOUNTAIN
                    room.features.append("fountain")

    def get_dungeon_summary(self, dungeon: Dungeon) -> Dict[str, Any]:
        """Get summary of generated dungeon"""
        encounter_types = {}
        for encounter in dungeon.encounters.values():
            encounter_type = encounter.encounter_type.value
            encounter_types[encounter_type] = encounter_types.get(encounter_type, 0) + 1

        room_types = {}
        for room in dungeon.rooms.values():
            room_type = room.room_type.value
            room_types[room_type] = room_types.get(room_type, 0) + 1

        return {
            "name": dungeon.name,
            "type": dungeon.dungeon_type.value,
            "theme": dungeon.theme.name,
            "difficulty": dungeon.difficulty.name,
            "size": dungeon.size,
            "dimensions": f"{dungeon.width}x{dungeon.height}",
            "room_count": len(dungeon.rooms),
            "encounter_count": len(dungeon.encounters),
            "room_types": room_types,
            "encounter_types": encounter_types,
            "estimated_playtime": f"{dungeon.estimated_playtime} minutes",
            "recommended_level": dungeon.recommended_level,
            "has_boss": dungeon.boss_room_id is not None,
            "seed": dungeon.seed
        }

# Example usage and testing
if __name__ == "__main__":
    # Create dungeon builder
    builder = DungeonBuilder()

    print("=== DUNGEON GENERATOR ===")

    # Generate different types of dungeons
    dungeons = []

    # Small mine
    mine = builder.generate_dungeon(
        DungeonType.MINE,
        DifficultyLevel.NORMAL,
        size="small"
    )
    dungeons.append(("Abandoned Mine", mine))

    # Medium temple
    temple = builder.generate_dungeon(
        DungeonType.TEMPLE,
        DifficultyLevel.CHALLENGING,
        size="medium",
        theme_name="ancient_temple"
    )
    dungeons.append(("Ancient Temple", temple))

    # Large fortress
    fortress = builder.generate_dungeon(
        DungeonType.FORTRESS,
        DifficultyLevel.HARD,
        size="large"
    )
    dungeons.append(("Dark Fortress", fortress))

    # Display summaries
    for name, dungeon in dungeons:
        print(f"\n=== {name} ===")
        summary = builder.get_dungeon_summary(dungeon)
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        # Show some room details
        print(f"\nSample Rooms:")
        sample_rooms = list(dungeon.rooms.values())[:3]
        for room in sample_rooms:
            print(f"  {room.room_type.value.title()}: {room.width}x{room.height} at ({room.position.x}, {room.position.y})")
            print(f"    Features: {', '.join(room.features)}")
            print(f"    Connections: {len(room.connections)}")
            if room.encounters:
                for enc_id in room.encounters:
                    encounter = dungeon.encounters[enc_id]
                    print(f"    Encounter: {encounter.encounter_type.value} - {encounter.description}")

        # Show encounter breakdown
        print(f"\nEncounters: {len(dungeon.encounters)} total")
        for enc_type, count in summary["encounter_types"].items():
            print(f"  {enc_type.title()}: {count}")

    print(f"\n=== GENERATION COMPLETE ===")
    print(f"Generated {len(dungeons)} dungeons with varying complexity and themes")