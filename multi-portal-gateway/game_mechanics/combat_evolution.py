"""
Advanced Combat Evolution System for DMLogn8n
Implements tactical combat with positioning, teamwork, and environmental factors
"""

import random
import math
import uuid
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

class CombatRole(Enum):
    """Combat roles with different tactical advantages"""
    TANK = "tank"
    DAMAGE_DEALER = "damage_dealer"
    SUPPORT = "support"
    CONTROLLER = "controller"
    ASSASSIN = "assassin"
    RANGED = "ranged"
    MELEE = "melee"
    HEALER = "healer"
    DEBUFFER = "debuffer"
    BUFFER = "buffer"

class DamageType(Enum):
    """Damage types with different effectiveness against targets"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    DARK = "dark"
    PSYCHIC = "psychic"
    FORCE = "force"

class StatusEffect(Enum):
    """Status effects that can affect combatants"""
    STUNNED = "stunned"
    POISONED = "poisoned"
    BURNING = "burning"
    FROZEN = "frozen"
    BLEEDING = "bleeding"
    BLINDED = "blinded"
    SILENCED = "silenced"
    SLOWED = "slowed"
    HASTED = "hasted"
    REGENERATING = "regenerating"
    BLESSED = "blessed"
    CURSED = "cursed"
    WEAKENED = "weakened"
    STRENGTHENED = "strengthened"
    PROTECTED = "protected"
    VULNERABLE = "vulnerable"

class ActionType(Enum):
    """Types of actions in combat"""
    ATTACK = "attack"
    DEFEND = "defend"
    SKILL = "skill"
    SPELL = "spell"
    ITEM = "item"
    MOVE = "move"
    WAIT = "wait"
    SPECIAL = "special"

class TerrainType(Enum):
    """Terrain types affecting combat"""
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    SWAMP = "swamp"
    DESERT = "desert"
    WATER = "water"
    URBAN = "urban"
    DUNGEON = "dungeon"
    CAVE = "cave"
    RUINS = "ruins"

class WeatherType(Enum):
    """Weather conditions affecting combat"""
    CLEAR = "clear"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"
    WIND = "wind"
    EXTREME_HEAT = "extreme_heat"
    EXTREME_COLD = "extreme_cold"

@dataclass
class Position:
    """Position on combat grid"""
    x: int
    y: int

    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def is_adjacent(self, other: 'Position') -> bool:
        """Check if position is adjacent"""
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1

    def get_neighbors(self) -> List['Position']:
        """Get all adjacent positions"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbors.append(Position(self.x + dx, self.y + dy))
        return neighbors

@dataclass
class StatusEffectInstance:
    """Active status effect instance"""
    effect: StatusEffect
    duration: int
    strength: float
    source_id: str
    start_time: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if effect has expired"""
        return self.duration <= 0

    def tick(self) -> bool:
        """Decrement duration and return if still active"""
        self.duration -= 1
        return not self.is_expired()

@dataclass
class CombatStats:
    """Combat statistics for entities"""
    health: float
    max_health: float
    mana: float
    max_mana: float
    attack: float
    defense: float
    magic: float
    resistance: float
    speed: float
    accuracy: float
    evasion: float
    critical_chance: float
    critical_damage: float
    initiative: float

    # Damage resistances
    physical_resistance: float = 0.0
    magical_resistance: float = 0.0
    fire_resistance: float = 0.0
    ice_resistance: float = 0.0
    lightning_resistance: float = 0.0
    poison_resistance: float = 0.0
    holy_resistance: float = 0.0
    dark_resistance: float = 0.0

    def get_resistance(self, damage_type: DamageType) -> float:
        """Get resistance for specific damage type"""
        resistance_map = {
            DamageType.PHYSICAL: self.physical_resistance,
            DamageType.MAGICAL: self.magical_resistance,
            DamageType.FIRE: self.fire_resistance,
            DamageType.ICE: self.ice_resistance,
            DamageType.LIGHTNING: self.lightning_resistance,
            DamageType.POISON: self.poison_resistance,
            DamageType.HOLY: self.holy_resistance,
            DamageType.DARK: self.dark_resistance,
            DamageType.PSYCHIC: self.magical_resistance,
            DamageType.FORCE: self.physical_resistance
        }
        return resistance_map.get(damage_type, 0.0)

@dataclass
class CombatAction:
    """Combat action with all details"""
    id: str
    actor_id: str
    action_type: ActionType
    target_ids: List[str]
    position: Optional[Position] = None
    skill_id: Optional[str] = None
    item_id: Optional[str] = None
    description: str = ""
    base_damage: float = 0
    damage_type: DamageType = DamageType.PHYSICAL
    effects: List[Dict[str, Any]] = field(default_factory=list)
    resource_cost: Dict[str, float] = field(default_factory=dict)
    cooldown: int = 0

@dataclass
class Combatant:
    """Combat participant with full stats and abilities"""
    id: str
    name: str
    level: int
    combat_role: CombatRole
    stats: CombatStats
    position: Position
    team: int  # 0 for player team, 1+ for enemy teams
    is_player_controlled: bool = False

    # Combat state
    current_health: float = 0
    current_mana: float = 0
    initiative: float = 0
    action_points: int = 0
    max_action_points: int = 2

    # Status effects and buffs
    status_effects: List[StatusEffectInstance] = field(default_factory=list)
    temporary_bonuses: Dict[str, float] = field(default_factory=dict)

    # Skills and abilities
    available_skills: List[str] = field(default_factory=list)
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)

    # Equipment
    weapon: Optional[Dict[str, Any]] = None
    armor: Optional[Dict[str, Any]] = None
    accessories: List[Dict[str, Any]] = field(default_factory=list)

    # AI behavior
    ai_priority: float = 1.0
    ai_behavior: str = "balanced"
    preferred_targets: List[str] = field(default_factory=list)
    avoided_targets: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize combatant state"""
        self.current_health = self.stats.health
        self.current_mana = self.stats.mana
        self.initiative = self.stats.initiative + random.uniform(-5, 5)

    def is_alive(self) -> bool:
        """Check if combatant is still alive"""
        return self.current_health > 0

    def is_stunned(self) -> bool:
        """Check if combatant is stunned"""
        return any(effect.effect == StatusEffect.STUNNED for effect in self.status_effects)

    def can_act(self) -> bool:
        """Check if combatant can take actions"""
        return self.is_alive() and not self.is_stunned() and self.action_points > 0

    def get_effective_stat(self, stat_name: str) -> float:
        """Get stat with all temporary bonuses applied"""
        base_value = getattr(self.stats, stat_name, 0)
        bonus = self.temporary_bonuses.get(stat_name, 0)

        # Apply status effect modifiers
        for effect in self.status_effects:
            if effect.effect == StatusEffect.STRENGTHENED and stat_name in ["attack", "magic"]:
                bonus += effect.strength
            elif effect.effect == StatusEffect.WEAKENED and stat_name in ["attack", "magic"]:
                bonus -= effect.strength
            elif effect.effect == StatusEffect.PROTECTED and stat_name in ["defense", "resistance"]:
                bonus += effect.strength
            elif effect.effect == StatusEffect.VULNERABLE and stat_name in ["defense", "resistance"]:
                bonus -= effect.strength

        return max(0, base_value + bonus)

    def take_damage(self, damage: float, damage_type: DamageType) -> float:
        """Apply damage to combatant"""
        if not self.is_alive():
            return 0

        # Calculate damage reduction from resistance
        resistance = self.stats.get_resistance(damage_type)
        effective_resistance = resistance + self.temporary_bonuses.get("resistance", 0)

        # Apply resistance
        damage_reduction = min(0.8, effective_resistance / 100)  # Max 80% reduction
        final_damage = damage * (1 - damage_reduction)

        # Apply defense
        defense = self.get_effective_stat("defense")
        defense_reduction = defense / (defense + 100)  # Diminishing returns
        final_damage *= (1 - defense_reduction)

        # Apply damage
        self.current_health = max(0, self.current_health - final_damage)
        return final_damage

    def heal(self, amount: float) -> float:
        """Heal combatant"""
        if not self.is_alive():
            return 0

        actual_heal = min(amount, self.stats.max_health - self.current_health)
        self.current_health += actual_heal
        return actual_heal

    def restore_mana(self, amount: float) -> float:
        """Restore mana"""
        actual_restore = min(amount, self.stats.max_mana - self.current_mana)
        self.current_mana += actual_restore
        return actual_restore

    def apply_status_effect(self, effect: StatusEffect, duration: int,
                          strength: float, source_id: str):
        """Apply status effect to combatant"""
        # Check for existing effect of same type
        existing = None
        for i, existing_effect in enumerate(self.status_effects):
            if existing_effect.effect == effect:
                existing = i
                break

        if existing is not None:
            # Refresh or strengthen existing effect
            if duration > self.status_effects[existing].duration:
                self.status_effects[existing].duration = duration
            self.status_effects[existing].strength = max(
                self.status_effects[existing].strength, strength
            )
        else:
            # Add new effect
            self.status_effects.append(StatusEffectInstance(
                effect=effect,
                duration=duration,
                strength=strength,
                source_id=source_id
            ))

    def remove_status_effect(self, effect: StatusEffect):
        """Remove status effect from combatant"""
        self.status_effects = [e for e in self.status_effects if e.effect != effect]

    def update_status_effects(self):
        """Update all status effects"""
        remaining_effects = []
        for effect in self.status_effects:
            if effect.tick():
                remaining_effects.append(effect)
                # Apply effect-specific logic
                self._process_status_effect(effect)
        self.status_effects = remaining_effects

    def _process_status_effect(self, effect: StatusEffectInstance):
        """Process individual status effect effects"""
        if effect.effect == StatusEffect.POISONED:
            self.take_damage(effect.strength, DamageType.POISON)
        elif effect.effect == StatusEffect.BURNING:
            self.take_damage(effect.strength, DamageType.FIRE)
        elif effect.effect == StatusEffect.REGENERATING:
            self.heal(effect.strength)
        elif effect.effect == StatusEffect.BLEEDING:
            self.take_damage(effect.strength, DamageType.PHYSICAL)

    def use_mana(self, amount: float) -> bool:
        """Use mana if available"""
        if self.current_mana >= amount:
            self.current_mana -= amount
            return True
        return False

    def update_cooldowns(self):
        """Update skill cooldowns"""
        for skill_id in list(self.skill_cooldowns.keys()):
            self.skill_cooldowns[skill_id] -= 1
            if self.skill_cooldowns[skill_id] <= 0:
                del self.skill_cooldowns[skill_id]

    def start_new_turn(self):
        """Initialize combatant for new turn"""
        self.action_points = self.max_action_points
        self.update_status_effects()
        self.update_cooldowns()

        # Regeneration
        self.restore_mana(self.stats.max_mana * 0.05)  # 5% mana regen

        # Status effect regeneration
        if any(e.effect == StatusEffect.REGENERATING for e in self.status_effects):
            self.heal(self.stats.max_health * 0.1)  # 10% health regen

class CombatEnvironment:
    """Combat environment with terrain and weather effects"""

    def __init__(self, width: int, height: int, terrain: TerrainType, weather: WeatherType):
        self.width = width
        self.height = height
        self.terrain = terrain
        self.weather = weather
        self.obstacles: Set[Tuple[int, int]] = set()
        self.hazardous_areas: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self.beneficial_areas: Dict[Tuple[int, int], Dict[str, Any]] = {}

        self._generate_environment_features()

    def _generate_environment_features(self):
        """Generate terrain-specific features"""
        if self.terrain == TerrainType.FOREST:
            # Add trees as obstacles
            for _ in range(self.width * self.height // 20):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                self.obstacles.add((x, y))

        elif self.terrain == TerrainType.MOUNTAINS:
            # Add rocky obstacles
            for _ in range(self.width * self.height // 15):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                self.obstacles.add((x, y))

        elif self.terrain == TerrainType.SWAMP:
            # Add hazardous swamp areas
            for _ in range(self.width * self.height // 25):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                self.hazardous_areas[(x, y)] = {
                    "type": "poison",
                    "damage": 5,
                    "effect": StatusEffect.SLOWED,
                    "duration": 2
                }

        elif self.terrain == TerrainType.DUNGEON:
            # Add pillars and obstacles
            for _ in range(self.width * self.height // 30):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                self.obstacles.add((x, y))

    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid and not blocked"""
        if (position.x < 0 or position.x >= self.width or
            position.y < 0 or position.y >= self.height):
            return False
        return (position.x, position.y) not in self.obstacles

    def get_movement_cost(self, from_pos: Position, to_pos: Position) -> float:
        """Get movement cost between positions"""
        if not self.is_valid_position(to_pos):
            return float('inf')

        base_cost = 1.0

        # Terrain modifiers
        if self.terrain == TerrainType.FOREST:
            base_cost *= 1.5
        elif self.terrain == TerrainType.MOUNTAINS:
            base_cost *= 2.0
        elif self.terrain == TerrainType.SWAMP:
            base_cost *= 2.5
        elif self.terrain == TerrainType.WATER:
            base_cost *= 3.0

        # Weather modifiers
        if self.weather == WeatherType.RAIN:
            base_cost *= 1.2
        elif self.weather == WeatherType.SNOW:
            base_cost *= 1.5
        elif self.weather == WeatherType.STORM:
            base_cost *= 1.8
        elif self.weather == WeatherType.FOG:
            base_cost *= 1.3

        return base_cost

    def apply_environmental_effects(self, combatant: Combatant):
        """Apply environmental effects to combatant"""
        pos_tuple = (combatant.position.x, combatant.position.y)

        # Hazardous areas
        if pos_tuple in self.hazardous_areas:
            hazard = self.hazardous_areas[pos_tuple]
            if hazard["type"] == "poison":
                combatant.take_damage(hazard["damage"], DamageType.POISON)
            elif hazard["type"] == "fire":
                combatant.take_damage(hazard["damage"], DamageType.FIRE)

            if hazard.get("effect"):
                combatant.apply_status_effect(
                    hazard["effect"], hazard["duration"], 1.0, "environment"
                )

        # Beneficial areas
        if pos_tuple in self.beneficial_areas:
            benefit = self.beneficial_areas[pos_tuple]
            if benefit["type"] == "healing":
                combatant.heal(benefit["amount"])
            elif benefit["type"] == "mana":
                combatant.restore_mana(benefit["amount"])

class CombatAI:
    """AI system for NPC combatants"""

    def __init__(self):
        self.difficulty_level = 1.0
        self.teamwork_bonus = 1.0

    def select_action(self, combatant: Combatant, combat_state: 'CombatState') -> Optional[CombatAction]:
        """Select best action for AI combatant"""
        if not combatant.can_act():
            return None

        # Evaluate possible actions
        possible_actions = self._generate_possible_actions(combatant, combat_state)
        if not possible_actions:
            return None

        # Score actions based on AI behavior
        scored_actions = []
        for action in possible_actions:
            score = self._score_action(action, combatant, combat_state)
            scored_actions.append((score, action))

        # Select best action
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        return scored_actions[0][1] if scored_actions else None

    def _generate_possible_actions(self, combatant: Combatant,
                                 combat_state: 'CombatState') -> List[CombatAction]:
        """Generate all possible actions for combatant"""
        actions = []

        # Basic attacks
        enemies = combat_state.get_enemies_of(combatant)
        for enemy in enemies:
            if self._can_attack(combatant, enemy, combat_state):
                damage = combatant.get_effective_stat("attack")
                action = CombatAction(
                    id=str(uuid.uuid4()),
                    actor_id=combatant.id,
                    action_type=ActionType.ATTACK,
                    target_ids=[enemy.id],
                    base_damage=damage,
                    damage_type=DamageType.PHYSICAL
                )
                actions.append(action)

        # Skills
        for skill_id in combatant.available_skills:
            if skill_id not in combatant.skill_cooldowns:
                skill_action = self._create_skill_action(combatant, skill_id, combat_state)
                if skill_action:
                    actions.append(skill_action)

        # Movement
        if combatant.action_points > 0:
            best_position = self._find_best_position(combatant, combat_state)
            if best_position and best_position != combatant.position:
                action = CombatAction(
                    id=str(uuid.uuid4()),
                    actor_id=combatant.id,
                    action_type=ActionType.MOVE,
                    target_ids=[],
                    position=best_position
                )
                actions.append(action)

        return actions

    def _can_attack(self, attacker: Combatant, target: Combatant,
                   combat_state: 'CombatState') -> bool:
        """Check if attacker can reach target"""
        distance = attacker.position.distance_to(target.position)

        # Ranged attackers can attack from distance
        if attacker.combat_role in [CombatRole.RANGED, CombatRole.MAGE]:
            max_range = 8
        else:
            max_range = 1

        return distance <= max_range

    def _create_skill_action(self, combatant: Combatant, skill_id: str,
                           combat_state: 'CombatState') -> Optional[CombatAction]:
        """Create skill action"""
        # This would interface with skill system
        # For now, return a basic skill action
        skill_data = self._get_skill_data(skill_id)
        if not skill_data:
            return None

        # Check mana cost
        if combatant.use_mana(skill_data.get("mana_cost", 0)):
            return CombatAction(
                id=str(uuid.uuid4()),
                actor_id=combatant.id,
                action_type=ActionType.SKILL,
                target_ids=self._select_skill_targets(combatant, skill_data, combat_state),
                skill_id=skill_id,
                base_damage=skill_data.get("damage", 0),
                damage_type=DamageType(skill_data.get("damage_type", "physical")),
                effects=skill_data.get("effects", []),
                resource_cost={"mana": skill_data.get("mana_cost", 0)},
                cooldown=skill_data.get("cooldown", 0)
            )
        return None

    def _get_skill_data(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill data"""
        # This would interface with skill system
        skills = {
            "fireball": {
                "mana_cost": 20,
                "damage": 40,
                "damage_type": "fire",
                "effects": [{"type": "burning", "duration": 3, "strength": 10}],
                "cooldown": 2,
                "range": 8,
                "target_type": "single"
            },
            "heal": {
                "mana_cost": 15,
                "damage": -30,  # Negative damage means healing
                "damage_type": "holy",
                "effects": [],
                "cooldown": 1,
                "range": 5,
                "target_type": "ally"
            },
            "power_attack": {
                "mana_cost": 10,
                "damage": 60,
                "damage_type": "physical",
                "effects": [],
                "cooldown": 3,
                "range": 1,
                "target_type": "enemy"
            }
        }
        return skills.get(skill_id)

    def _select_skill_targets(self, combatant: Combatant, skill_data: Dict[str, Any],
                            combat_state: 'CombatState') -> List[str]:
        """Select appropriate targets for skill"""
        target_type = skill_data.get("target_type", "enemy")
        max_range = skill_data.get("range", 1)

        if target_type == "enemy":
            targets = combat_state.get_enemies_in_range(combatant, max_range)
        elif target_type == "ally":
            targets = combat_state.get_allies_in_range(combatant, max_range)
        elif target_type == "self":
            targets = [combatant]
        else:
            targets = []

        # Select best target based on priority
        if targets:
            if target_type == "enemy":
                # Target lowest health enemy
                targets.sort(key=lambda t: t.current_health)
            elif target_type == "ally":
                # Target lowest health ally
                targets.sort(key=lambda t: t.current_health)
            return [targets[0].id]

        return []

    def _find_best_position(self, combatant: Combatant,
                          combat_state: 'CombatState') -> Optional[Position]:
        """Find best position for combatant to move to"""
        best_position = None
        best_score = -float('inf')

        # Check positions in movement range
        movement_range = combatant.get_effective_stat("speed") // 2
        for dx in range(-movement_range, movement_range + 1):
            for dy in range(-movement_range, movement_range + 1):
                new_pos = Position(combatant.position.x + dx, combatant.position.y + dy)

                if not combat_state.environment.is_valid_position(new_pos):
                    continue

                # Calculate position score
                score = self._score_position(combatant, new_pos, combat_state)
                if score > best_score:
                    best_score = score
                    best_position = new_pos

        return best_position

    def _score_position(self, combatant: Combatant, position: Position,
                       combat_state: 'CombatState') -> float:
        """Score a position for tactical value"""
        score = 0.0

        # Distance to enemies
        enemies = combat_state.get_enemies_of(combatant)
        if enemies:
            avg_distance = sum(position.distance_to(e.position) for e in enemies) / len(enemies)

            # Prefer optimal range based on combat role
            if combatant.combat_role in [CombatRole.RANGED, CombatRole.MAGE]:
                optimal_range = 6
            elif combatant.combat_role == CombatRole.TANK:
                optimal_range = 1
            else:
                optimal_range = 3

            distance_score = 10 - abs(avg_distance - optimal_range)
            score += distance_score

        # Distance to allies
        allies = combat_state.get_allies_of(combatant)
        if allies:
            avg_ally_distance = sum(position.distance_to(a.position) for a in allies) / len(allies)

            # Prefer staying somewhat close to allies
            if avg_ally_distance > 5:
                score -= 5

        # Environmental considerations
        pos_tuple = (position.x, position.y)
        if pos_tuple in combat_state.environment.hazardous_areas:
            score -= 20  # Avoid hazards

        if pos_tuple in combat_state.environment.beneficial_areas:
            score += 10  # Seek beneficial areas

        return score

    def _score_action(self, action: CombatAction, combatant: Combatant,
                     combat_state: 'CombatState') -> float:
        """Score action based on tactical value"""
        score = 0.0

        if action.action_type == ActionType.ATTACK:
            # Score based on damage and target priority
            for target_id in action.target_ids:
                target = combat_state.get_combatant(target_id)
                if target:
                    damage = action.base_damage
                    # Prefer targets with low health
                    health_factor = 1.0 + (1.0 - target.current_health / target.stats.max_health)
                    score += damage * health_factor

        elif action.action_type == ActionType.SKILL:
            # Score based on skill effectiveness
            base_score = action.base_damage or 0

            # Add effects score
            for effect in action.effects:
                if effect["type"] in ["stunned", "silenced"]:
                    base_score += 20  # High value for control effects
                elif effect["type"] in ["weakened", "vulnerable"]:
                    base_score += 10

            score += base_score

        elif action.action_type == ActionType.MOVE:
            # Score based on tactical positioning
            if action.position:
                score = self._score_position(combatant, action.position, combat_state)

        # Apply AI behavior modifiers
        if combatant.ai_behavior == "aggressive":
            if action.action_type in [ActionType.ATTACK, ActionType.SKILL]:
                score *= 1.5
        elif combatant.ai_behavior == "defensive":
            if action.action_type == ActionType.DEFEND:
                score *= 1.5
        elif combatant.ai_behavior == "supportive":
            if action.action_type == ActionType.SKILL:
                # Check if skill is supportive
                if action.skill_id and "heal" in action.skill_id:
                    score *= 2.0

        # Apply difficulty bonus
        score *= self.difficulty_level

        return score

class CombatState:
    """Manages overall combat state"""

    def __init__(self, environment: CombatEnvironment):
        self.environment = environment
        self.combatants: Dict[str, Combatant] = {}
        self.turn_order: List[str] = []
        self.current_turn_index = 0
        self.current_round = 1
        self.action_history: List[CombatAction] = []
        self.combat_log: List[str] = []
        self.victory_conditions: Dict[int, Any] = {}
        self.combat_ai = CombatAI()

    def add_combatant(self, combatant: Combatant):
        """Add combatant to battle"""
        self.combatants[combatant.id] = combatant
        self._update_turn_order()

    def remove_combatant(self, combatant_id: str):
        """Remove combatant from battle"""
        if combatant_id in self.combatants:
            del self.combatants[combatant_id]
            if combatant_id in self.turn_order:
                self.turn_order.remove(combatant_id)
            self._update_turn_order()

    def _update_turn_order(self):
        """Update turn order based on initiative"""
        self.turn_order = sorted(
            self.combatants.keys(),
            key=lambda cid: self.combatants[cid].initiative,
            reverse=True
        )

    def get_combatant(self, combatant_id: str) -> Optional[Combatant]:
        """Get combatant by ID"""
        return self.combatants.get(combatant_id)

    def get_current_combatant(self) -> Optional[Combatant]:
        """Get combatant whose turn it is"""
        if self.turn_order and self.current_turn_index < len(self.turn_order):
            current_id = self.turn_order[self.current_turn_index]
            return self.combatants.get(current_id)
        return None

    def get_enemies_of(self, combatant: Combatant) -> List[Combatant]:
        """Get all enemies of combatant"""
        return [c for c in self.combatants.values()
                if c.team != combatant.team and c.is_alive()]

    def get_allies_of(self, combatant: Combatant) -> List[Combatant]:
        """Get all allies of combatant"""
        return [c for c in self.combatants.values()
                if c.team == combatant.team and c.id != combatant.id and c.is_alive()]

    def get_enemies_in_range(self, combatant: Combatant, max_range: float) -> List[Combatant]:
        """Get enemies within range"""
        enemies = self.get_enemies_of(combatant)
        return [e for e in enemies if combatant.position.distance_to(e.position) <= max_range]

    def get_allies_in_range(self, combatant: Combatant, max_range: float) -> List[Combatant]:
        """Get allies within range"""
        allies = self.get_allies_of(combatant)
        return [a for a in allies if combatant.position.distance_to(a.position) <= max_range]

    def execute_action(self, action: CombatAction) -> bool:
        """Execute a combat action"""
        actor = self.get_combatant(action.actor_id)
        if not actor or not actor.can_act():
            return False

        success = False

        if action.action_type == ActionType.ATTACK:
            success = self._execute_attack(actor, action)
        elif action.action_type == ActionType.SKILL:
            success = self._execute_skill(actor, action)
        elif action.action_type == ActionType.MOVE:
            success = self._execute_move(actor, action)
        elif action.action_type == ActionType.DEFEND:
            success = self._execute_defend(actor, action)

        if success:
            self.action_history.append(action)
            actor.action_points -= 1

            # Add skill to cooldowns
            if action.skill_id and action.cooldown > 0:
                actor.skill_cooldowns[action.skill_id] = action.cooldown

            # Log action
            self.combat_log.append(f"{actor.name}: {action.description or action.action_type.value}")

        return success

    def _execute_attack(self, attacker: Combatant, action: CombatAction) -> bool:
        """Execute attack action"""
        for target_id in action.target_ids:
            target = self.get_combatant(target_id)
            if target and target.is_alive():
                # Calculate hit chance
                accuracy = attacker.get_effective_stat("accuracy")
                evasion = target.get_effective_stat("evasion")
                hit_chance = max(0.1, min(0.95, (accuracy - evasion + 50) / 100))

                if random.random() < hit_chance:
                    # Calculate damage
                    damage = action.base_damage + random.uniform(-5, 5)

                    # Critical hit chance
                    crit_chance = attacker.get_effective_stat("critical_chance") / 100
                    if random.random() < crit_chance:
                        crit_damage = attacker.get_effective_stat("critical_damage") / 100
                        damage *= (1 + crit_damage)
                        self.combat_log.append(f"Critical hit! {damage:.1f} damage")

                    # Apply damage
                    actual_damage = target.take_damage(damage, action.damage_type)
                    action.description = f"Attacked {target.name} for {actual_damage:.1f} damage"
                else:
                    action.description = f"Missed {target.name}"
                    self.combat_log.append(f"{attacker.name} missed {target.name}!")

        return True

    def _execute_skill(self, caster: Combatant, action: CombatAction) -> bool:
        """Execute skill action"""
        # Apply skill effects to targets
        for target_id in action.target_ids:
            target = self.get_combatant(target_id)
            if target:
                if action.base_damage < 0:  # Healing
                    actual_heal = target.heal(abs(action.base_damage))
                    action.description = f"Healed {target.name} for {actual_heal:.1f} health"
                else:  # Damage
                    actual_damage = target.take_damage(action.base_damage, action.damage_type)
                    action.description = f"Dealt {actual_damage:.1f} damage to {target.name}"

                # Apply status effects
                for effect in action.effects:
                    target.apply_status_effect(
                        StatusEffect(effect["type"]),
                        effect["duration"],
                        effect["strength"],
                        caster.id
                    )

        return True

    def _execute_move(self, combatant: Combatant, action: CombatAction) -> bool:
        """Execute movement action"""
        if action.position and self.environment.is_valid_position(action.position):
            old_pos = combatant.position
            combatant.position = action.position
            action.description = f"Moved from ({old_pos.x}, {old_pos.y}) to ({action.position.x}, {action.position.y})"

            # Apply environmental effects at new position
            self.environment.apply_environmental_effects(combatant)
            return True
        return False

    def _execute_defend(self, combatant: Combatant, action: CombatAction) -> bool:
        """Execute defend action"""
        # Apply defensive bonuses
        combatant.temporary_bonuses["defense"] = combatant.temporary_bonuses.get("defense", 0) + 10
        combatant.temporary_bonuses["resistance"] = combatant.temporary_bonuses.get("resistance", 0) + 10
        action.description = "Took a defensive stance"
        return True

    def next_turn(self) -> bool:
        """Advance to next turn"""
        # End current combatant's turn
        current = self.get_current_combatant()
        if current:
            # Reset temporary bonuses at end of turn
            current.temporary_bonuses.clear()

        # Move to next combatant
        self.current_turn_index += 1

        # Check if round is complete
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.current_round += 1

            # Start new round
            for combatant in self.combatants.values():
                combatant.start_new_turn()

        # Skip dead or stunned combatants
        current = self.get_current_combatant()
        if current and (not current.is_alive() or current.is_stunned()):
            return self.next_turn()

        # Handle AI turns
        if current and not current.is_player_controlled:
            ai_action = self.combat_ai.select_action(current, self)
            if ai_action:
                self.execute_action(ai_action)
                if current.action_points > 0:
                    return self.next_turn()  # Continue AI turn if actions remain

        return True

    def is_combat_over(self) -> Optional[int]:
        """Check if combat is over and return winning team"""
        teams_alive = set()
        for combatant in self.combatants.values():
            if combatant.is_alive():
                teams_alive.add(combatant.team)

        if len(teams_alive) <= 1:
            return teams_alive.pop() if teams_alive else -1
        return None

    def get_combat_summary(self) -> Dict[str, Any]:
        """Get summary of combat state"""
        team_stats = {}
        for combatant in self.combatants.values():
            if combatant.team not in team_stats:
                team_stats[combatant.team] = {
                    "alive": 0,
                    "dead": 0,
                    "total_health": 0,
                    "max_health": 0
                }

            if combatant.is_alive():
                team_stats[combatant.team]["alive"] += 1
                team_stats[combatant.team]["total_health"] += combatant.current_health
            else:
                team_stats[combatant.team]["dead"] += 1

            team_stats[combatant.team]["max_health"] += combatant.stats.max_health

        return {
            "round": self.current_round,
            "current_turn": self.turn_order[self.current_turn_index] if self.turn_order else None,
            "total_combatants": len(self.combatants),
            "team_stats": team_stats,
            "environment": {
                "terrain": self.terrain.value,
                "weather": self.weather.value
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Create combat environment
    environment = CombatEnvironment(10, 10, TerrainType.FOREST, WeatherType.CLEAR)
    combat = CombatState(environment)

    # Create player team
    player1 = Combatant(
        id="player1",
        name="Hero",
        level=10,
        combat_role=CombatRole.DAMAGE_DEALER,
        stats=CombatStats(
            health=100, max_health=100,
            mana=50, max_mana=50,
            attack=25, defense=15,
            magic=20, resistance=10,
            speed=30, accuracy=80,
            evasion=20, critical_chance=10,
            critical_damage=50, initiative=70
        ),
        position=Position(2, 5),
        team=0,
        is_player_controlled=True,
        available_skills=["power_attack", "heal"]
    )

    # Create enemy team
    enemy1 = Combatant(
        id="enemy1",
        name="Goblin Warrior",
        level=8,
        combat_role=CombatRole.TANK,
        stats=CombatStats(
            health=80, max_health=80,
            mana=20, max_mana=20,
            attack=20, defense=20,
            magic=10, resistance=15,
            speed=20, accuracy=70,
            evasion=15, critical_chance=5,
            critical_damage=30, initiative=60
        ),
        position=Position(8, 5),
        team=1,
        available_skills=["power_attack"]
    )

    # Add combatants
    combat.add_combatant(player1)
    combat.add_combatant(enemy1)

    # Simulate a few turns
    print("=== COMBAT SIMULATION ===")
    for round_num in range(1, 4):
        print(f"\n--- Round {round_num} ---")

        while combat.current_round == round_num:
            current = combat.get_current_combatant()
            if current:
                print(f"\n{current.name}'s turn (Team {current.team})")
                print(f"Position: ({current.position.x}, {current.position.y})")
                print(f"Health: {current.current_health:.1f}/{current.stats.max_health}")
                print(f"Action Points: {current.action_points}")

                if current.is_player_controlled:
                    # Simple AI for demo
                    enemies = combat.get_enemies_of(current)
                    if enemies and current.action_points > 0:
                        target = enemies[0]
                        action = CombatAction(
                            id=str(uuid.uuid4()),
                            actor_id=current.id,
                            action_type=ActionType.ATTACK,
                            target_ids=[target.id],
                            base_damage=current.get_effective_stat("attack"),
                            damage_type=DamageType.PHYSICAL
                        )
                        combat.execute_action(action)
                        print(f"Action: {action.description}")
                else:
                    # AI will handle automatically
                    combat.next_turn()
                    continue

            combat.next_turn()

        # Check if combat is over
        winner = combat.is_combat_over()
        if winner is not None:
            print(f"\nCombat Over! Team {winner} wins!")
            break

    # Print combat summary
    summary = combat.get_combat_summary()
    print(f"\n=== COMBAT SUMMARY ===")
    print(f"Total Rounds: {summary['round']}")
    print(f"Team Stats: {summary['team_stats']}")