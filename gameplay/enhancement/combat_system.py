#!/usr/bin/env python3
"""
Enhanced Tactical Combat System for DMLogn8n
Provides strategic, position-based combat with tactical depth
"""

import json
import math
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import asyncio

class CombatState(Enum):
    IDLE = "idle"
    INITIATIVE = "initiative"
    ACTION = "action"
    RESOLUTION = "resolution"
    VICTORY = "victory"
    DEFEAT = "defeat"

class ActionType(Enum):
    ATTACK = "attack"
    DEFEND = "defend"
    SKILL = "skill"
    ITEM = "item"
    MOVE = "move"
    COOPERATE = "cooperate"
    RETREAT = "retreat"

class Position(Enum):
    FRONT = "front"
    BACK = "back"
    FLANK = "flank"
    SUPPORT = "support"
    STEALTH = "stealth"

class DamageType(Enum):
    PHYSICAL = "physical"
    MAGICAL = "magical"
    PSYCHIC = "psychic"
    ELEMENTAL = "elemental"
    TRUE = "true"

class StatusEffect(Enum):
    STUNNED = "stunned"
    POISONED = "poisoned"
    BLESSED = "blessed"
    CURSED = "cursed"
    ENRAGED = "enraged"
    FRIGHTENED = "frightened"
    REGENERATING = "regenerating"
    SHIELDED = "shielded"

@dataclass
class CombatStats:
    """Combat statistics for entities"""
    health: int = 100
    max_health: int = 100
    attack: int = 10
    defense: int = 8
    speed: int = 10
    accuracy: float = 0.85
    critical_chance: float = 0.05
    critical_multiplier: float = 2.0
    dodge_chance: float = 0.10
    resistances: Dict[DamageType, float] = field(default_factory=dict)
    position_bonuses: Dict[Position, Dict[str, float]] = field(default_factory=dict)

@dataclass
class CombatEntity:
    """Entity participating in combat"""
    id: str
    name: str
    stats: CombatStats
    position: Position = Position.BACK
    team: str = "player"
    status_effects: Set[StatusEffect] = field(default_factory=set)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    action_points: int = 3
    max_action_points: int = 3
    initiative: int = 0
    alive: bool = True

@dataclass
class CombatAction:
    """Represents a combat action"""
    actor_id: str
    action_type: ActionType
    target_id: Optional[str] = None
    skill_id: Optional[str] = None
    position: Optional[Position] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CombatResult:
    """Result of a combat action"""
    success: bool
    damage: int = 0
    healing: int = 0
    status_effects: List[StatusEffect] = field(default_factory=list)
    position_change: Optional[Position] = None
    description: str = ""
    critical: bool = False
    dodge: bool = False

class CombatGrid:
    """Tactical combat grid for positioning"""

    def __init__(self, width: int = 8, height: int = 6):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.position_bonuses = self._generate_position_bonuses()

    def _generate_position_bonuses(self) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Generate position-based bonuses"""
        bonuses = {}
        for y in range(self.height):
            for x in range(self.width):
                bonus = {}
                # Front line gets defense bonus
                if y == self.height - 1:
                    bonus["defense"] = 1.2
                # Back line gets accuracy bonus
                elif y == 0:
                    bonus["accuracy"] = 1.15
                # Flanks get speed bonus
                elif x == 0 or x == self.width - 1:
                    bonus["speed"] = 1.1
                # Center gets balanced bonus
                else:
                    bonus["balanced"] = 1.05
                bonuses[(x, y)] = bonus
        return bonuses

    def get_position_bonus(self, x: int, y: int, stat: str) -> float:
        """Get bonus for specific position and stat"""
        if (x, y) in self.position_bonuses:
            return self.position_bonuses[(x, y)].get(stat, 1.0)
        return 1.0

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid"""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate distance between two positions"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

class TacticalCombatSystem:
    """Enhanced tactical combat system"""

    def __init__(self):
        self.state = CombatState.IDLE
        self.entities: Dict[str, CombatEntity] = {}
        self.grid = CombatGrid()
        self.current_turn = 0
        self.turn_order: List[str] = []
        self.action_queue: List[CombatAction] = []
        self.combat_log: List[Dict] = []
        self.terrain_effects: Dict[str, Any] = {}
        self.cooperation_bonuses: Dict[str, float] = defaultdict(float)
        self.analytics = CombatAnalytics()

        # Balance parameters
        self.position_flanking_bonus = 1.25
        self.teamwork_bonus_multiplier = 1.15
        self.critical_hit_threshold = 0.95
        self.combo_damage_multiplier = 1.3

    def add_entity(self, entity: CombatEntity, x: int, y: int) -> bool:
        """Add entity to combat"""
        if not self.grid.is_valid_position(x, y) or self.grid.grid[y][x] is not None:
            return False

        self.entities[entity.id] = entity
        self.grid.grid[y][x] = entity.id

        # Apply position bonuses
        self._apply_position_bonuses(entity, x, y)

        self.analytics.record_entity_join(entity)
        return True

    def _apply_position_bonuses(self, entity: CombatEntity, x: int, y: int):
        """Apply position-based stat bonuses"""
        bonuses = self.grid.position_bonuses.get((x, y), {})
        for stat, multiplier in bonuses.items():
            if stat == "defense":
                entity.stats.defense = int(entity.stats.defense * multiplier)
            elif stat == "accuracy":
                entity.stats.accuracy = min(1.0, entity.stats.accuracy * multiplier)
            elif stat == "speed":
                entity.stats.speed = int(entity.stats.speed * multiplier)

    def start_combat(self) -> bool:
        """Initialize combat and determine turn order"""
        if self.state != CombatState.IDLE:
            return False

        self.state = CombatState.INITIATIVE
        self._determine_initiative()
        self.state = CombatState.ACTION
        self.current_turn = 0

        self.analytics.record_combat_start(len(self.entities))
        return True

    def _determine_initiative(self):
        """Determine turn order based on speed and random factor"""
        initiatives = []
        for entity_id, entity in self.entities.items():
            initiative = entity.stats.speed + random.randint(1, 20)
            entity.initiative = initiative
            initiatives.append((initiative, entity_id))

        initiatives.sort(reverse=True)
        self.turn_order = [entity_id for _, entity_id in initiatives]

    def get_current_entity(self) -> Optional[CombatEntity]:
        """Get entity whose turn it is"""
        if self.current_turn >= len(self.turn_order):
            return None
        return self.entities.get(self.turn_order[self.current_turn])

    def execute_action(self, action: CombatAction) -> CombatResult:
        """Execute a combat action"""
        actor = self.entities.get(action.actor_id)
        if not actor or not actor.alive:
            return CombatResult(success=False, description="Invalid actor")

        # Check cooldowns
        if action.skill_id and action.skill_id in actor.cooldowns:
            if actor.cooldowns[action.skill_id] > 0:
                return CombatResult(success=False, description="Skill on cooldown")

        result = None

        if action.action_type == ActionType.ATTACK:
            result = self._execute_attack(actor, action.target_id)
        elif action.action_type == ActionType.DEFEND:
            result = self._execute_defend(actor)
        elif action.action_type == ActionType.SKILL:
            result = self._execute_skill(actor, action.skill_id, action.target_id)
        elif action.action_type == ActionType.MOVE:
            result = self._execute_move(actor, action.position)
        elif action.action_type == ActionType.COOPERATE:
            result = self._execute_cooperation(actor, action.target_id)

        if result:
            self.combat_log.append({
                "turn": self.current_turn,
                "actor": action.actor_id,
                "action": action.action_type.value,
                "result": result,
                "timestamp": time.time()
            })
            self.analytics.record_action(action, result)

        return result or CombatResult(success=False, description="Invalid action")

    def _execute_attack(self, attacker: CombatEntity, target_id: Optional[str]) -> CombatResult:
        """Execute attack action"""
        if not target_id or target_id not in self.entities:
            return CombatResult(success=False, description="Invalid target")

        target = self.entities[target_id]
        if not target.alive:
            return CombatResult(success=False, description="Target already defeated")

        # Calculate hit chance
        hit_chance = attacker.stats.accuracy
        distance = self._get_distance_between_entities(attacker.id, target_id)
        if distance > 2:  # Range penalty
            hit_chance *= (1.0 - (distance - 2) * 0.1)

        # Check for dodge
        if random.random() < target.stats.dodge_chance:
            return CombatResult(success=True, dodge=True, description=f"{target.name} dodged!")

        # Roll for hit
        if random.random() > hit_chance:
            return CombatResult(success=False, description="Attack missed")

        # Calculate damage
        base_damage = attacker.stats.attack
        defense = target.stats.defense
        damage = max(1, base_damage - defense)

        # Check for critical hit
        critical = random.random() < attacker.stats.critical_chance
        if critical:
            damage = int(damage * attacker.stats.critical_multiplier)

        # Apply position bonuses
        attacker_pos = self._get_entity_position(attacker.id)
        target_pos = self._get_entity_position(target_id)
        if attacker_pos and target_pos:
            damage = self._apply_position_damage_modifiers(damage, attacker_pos, target_pos)

        # Apply damage
        target.stats.health -= damage
        if target.stats.health <= 0:
            target.alive = False
            target.stats.health = 0

        description = f"{attacker.name} dealt {damage} damage to {target.name}"
        if critical:
            description += " (CRITICAL HIT!)"

        return CombatResult(
            success=True,
            damage=damage,
            critical=critical,
            description=description
        )

    def _execute_defend(self, defender: CombatEntity) -> CombatResult:
        """Execute defend action"""
        # Increase defense temporarily
        defense_boost = int(defender.stats.defense * 0.5)
        defender.stats.defense += defense_boost

        # Add shielded status effect
        defender.status_effects.add(StatusEffect.SHIELDED)

        return CombatResult(
            success=True,
            description=f"{defender.name} takes defensive stance (+{defense_boost} defense)"
        )

    def _execute_skill(self, caster: CombatEntity, skill_id: Optional[str], target_id: Optional[str]) -> CombatResult:
        """Execute skill action"""
        if not skill_id:
            return CombatResult(success=False, description="No skill specified")

        # This would integrate with the skill system
        # For now, return a placeholder
        return CombatResult(
            success=True,
            description=f"{caster.name} uses {skill_id}"
        )

    def _execute_move(self, entity: CombatEntity, new_position: Optional[Position]) -> CombatResult:
        """Execute move action"""
        if not new_position:
            return CombatResult(success=False, description="No position specified")

        old_position = entity.position
        entity.position = new_position

        return CombatResult(
            success=True,
            position_change=new_position,
            description=f"{entity.name} moved from {old_position.value} to {new_position.value}"
        )

    def _execute_cooperation(self, actor: CombatEntity, target_id: Optional[str]) -> CombatResult:
        """Execute cooperation action"""
        if not target_id or target_id not in self.entities:
            return CombatResult(success=False, description="Invalid target")

        target = self.entities[target_id]

        # Apply teamwork bonus to both entities
        self.cooperation_bonuses[actor.id] += 0.1
        self.cooperation_bonuses[target_id] += 0.1

        # Heal or buff target
        healing = int(actor.stats.attack * 0.3)
        target.stats.health = min(target.stats.max_health, target.stats.health + healing)

        return CombatResult(
            success=True,
            healing=healing,
            description=f"{actor.name} cooperates with {target.name} for {healing} healing"
        )

    def _apply_position_damage_modifiers(self, damage: int, attacker_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> int:
        """Apply position-based damage modifiers"""
        # Flanking bonus
        if abs(attacker_pos[0] - target_pos[0]) > 1:
            damage = int(damage * self.position_flanking_bonus)

        return damage

    def _get_distance_between_entities(self, entity1_id: str, entity2_id: str) -> float:
        """Get distance between two entities"""
        pos1 = self._get_entity_position(entity1_id)
        pos2 = self._get_entity_position(entity2_id)

        if pos1 and pos2:
            return self.grid.get_distance(pos1[0], pos1[1], pos2[0], pos2[1])
        return 0

    def _get_entity_position(self, entity_id: str) -> Optional[Tuple[int, int]]:
        """Get entity position on grid"""
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if self.grid.grid[y][x] == entity_id:
                    return (x, y)
        return None

    def next_turn(self) -> bool:
        """Advance to next turn"""
        self.current_turn += 1

        if self.current_turn >= len(self.turn_order):
            self.current_turn = 0
            self._process_status_effects()
            self._reduce_cooldowns()

        # Check victory conditions
        if self._check_victory_conditions():
            return False

        return True

    def _process_status_effects(self):
        """Process status effects on all entities"""
        for entity in self.entities.values():
            if not entity.alive:
                continue

            # Process each status effect
            effects_to_remove = []
            for effect in entity.status_effects:
                if effect == StatusEffect.POISONED:
                    damage = 5
                    entity.stats.health -= damage
                    if entity.stats.health <= 0:
                        entity.alive = False
                elif effect == StatusEffect.REGENERATING:
                    healing = 5
                    entity.stats.health = min(entity.stats.max_health, entity.stats.health + healing)
                elif effect == StatusEffect.STUNNED:
                    # Skip turn if stunned
                    entity.action_points = 0
                    effects_to_remove.append(effect)
                elif effect == StatusEffect.SHIELDED:
                    # Remove shield after one turn
                    entity.stats.defense = int(entity.stats.defense / 1.5)
                    effects_to_remove.append(effect)

            for effect in effects_to_remove:
                entity.status_effects.remove(effect)

    def _reduce_cooldowns(self):
        """Reduce cooldowns for all entities"""
        for entity in self.entities.values():
            for skill_id in list(entity.cooldowns.keys()):
                entity.cooldowns[skill_id] -= 1
                if entity.cooldowns[skill_id] <= 0:
                    del entity.cooldowns[skill_id]

            # Reset action points
            entity.action_points = entity.max_action_points

    def _check_victory_conditions(self) -> bool:
        """Check if combat has ended"""
        player_entities = [e for e in self.entities.values() if e.team == "player" and e.alive]
        enemy_entities = [e for e in self.entities.values() if e.team != "player" and e.alive]

        if not player_entities:
            self.state = CombatState.DEFEAT
            self.analytics.record_combat_end(False, len(self.combat_log))
            return True
        elif not enemy_entities:
            self.state = CombatState.VICTORY
            self.analytics.record_combat_end(True, len(self.combat_log))
            return True

        return False

    def get_combat_summary(self) -> Dict[str, Any]:
        """Get combat summary for display"""
        return {
            "state": self.state.value,
            "current_turn": self.current_turn,
            "total_turns": len(self.combat_log),
            "entities": {
                entity_id: {
                    "name": entity.name,
                    "health": entity.stats.health,
                    "max_health": entity.stats.max_health,
                    "alive": entity.alive,
                    "position": entity.position.value,
                    "status_effects": [e.value for e in entity.status_effects]
                }
                for entity_id, entity in self.entities.items()
            },
            "analytics": self.analytics.get_summary()
        }

class CombatAnalytics:
    """Analytics system for combat balance and optimization"""

    def __init__(self):
        self.combat_sessions = []
        self.current_session = {
            "start_time": None,
            "participants": [],
            "actions": [],
            "damage_dealt": defaultdict(int),
            "healing_done": defaultdict(int),
            "critical_hits": defaultdict(int),
            "dodges": defaultdict(int)
        }

    def record_combat_start(self, participant_count: int):
        """Record combat start"""
        self.current_session["start_time"] = time.time()
        self.current_session["participants"] = participant_count

    def record_entity_join(self, entity: CombatEntity):
        """Record entity joining combat"""
        pass

    def record_action(self, action: CombatAction, result: CombatResult):
        """Record combat action"""
        action_data = {
            "actor": action.actor_id,
            "type": action.action_type.value,
            "success": result.success,
            "damage": result.damage,
            "healing": result.healing,
            "critical": result.critical,
            "dodge": result.dodge
        }
        self.current_session["actions"].append(action_data)

        if result.success:
            if result.damage > 0:
                self.current_session["damage_dealt"][action.actor_id] += result.damage
            if result.healing > 0:
                self.current_session["healing_done"][action.actor_id] += result.healing
            if result.critical:
                self.current_session["critical_hits"][action.actor_id] += 1
            if result.dodge:
                self.current_session["dodges"][action.actor_id] += 1

    def record_combat_end(self, victory: bool, total_actions: int):
        """Record combat end"""
        if self.current_session["start_time"]:
            duration = time.time() - self.current_session["start_time"]
            session_data = {
                **self.current_session,
                "duration": duration,
                "victory": victory,
                "total_actions": total_actions,
                "actions_per_minute": (total_actions / duration) * 60 if duration > 0 else 0
            }
            self.combat_sessions.append(session_data)

    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        if not self.combat_sessions:
            return {"total_combats": 0}

        total_combats = len(self.combat_sessions)
        victories = sum(1 for s in self.combat_sessions if s["victory"])
        avg_duration = sum(s["duration"] for s in self.combat_sessions) / total_combats
        avg_actions = sum(s["total_actions"] for s in self.combat_sessions) / total_combats

        return {
            "total_combats": total_combats,
            "win_rate": victories / total_combats if total_combats > 0 else 0,
            "average_duration": avg_duration,
            "average_actions": avg_actions,
            "current_session_stats": {
                "actions": len(self.current_session["actions"]),
                "damage_dealt": dict(self.current_session["damage_dealt"]),
                "healing_done": dict(self.current_session["healing_done"])
            }
        }

# Utility functions for balance and optimization
def calculate_combat_balance(entities: List[CombatEntity]) -> Dict[str, float]:
    """Calculate combat balance metrics"""
    if len(entities) < 2:
        return {"balance": 1.0}

    teams = defaultdict(list)
    for entity in entities:
        teams[entity.team].append(entity)

    team_power = {}
    for team, team_entities in teams.items():
        power = 0
        for entity in team_entities:
            power += (
                entity.stats.attack * 1.2 +
                entity.stats.defense * 1.0 +
                entity.stats.speed * 0.8 +
                entity.stats.max_health * 0.1
            )
        team_power[team] = power

    max_power = max(team_power.values())
    min_power = min(team_power.values())

    if max_power == 0:
        return {"balance": 1.0}

    balance_ratio = min_power / max_power
    return {
        "balance": balance_ratio,
        "team_power": team_power,
        "fairness": "fair" if balance_ratio > 0.7 else "unbalanced"
    }

def generate_combat_recommendations(analytics: CombatAnalytics) -> List[str]:
    """Generate balance recommendations based on analytics"""
    recommendations = []

    if not analytics.combat_sessions:
        return recommendations

    avg_duration = sum(s["duration"] for s in analytics.combat_sessions) / len(analytics.combat_sessions)
    win_rate = sum(1 for s in analytics.combat_sessions if s["victory"]) / len(analytics.combat_sessions)

    if avg_duration > 300:  # 5 minutes
        recommendations.append("Combat duration is high - consider increasing damage output")
    elif avg_duration < 60:  # 1 minute
        recommendations.append("Combat is too short - consider increasing enemy health")

    if win_rate < 0.3:
        recommendations.append("Win rate is low - consider reducing difficulty")
    elif win_rate > 0.8:
        recommendations.append("Win rate is high - consider increasing difficulty")

    return recommendations

# Export the main classes
__all__ = [
    'TacticalCombatSystem',
    'CombatEntity',
    'CombatStats',
    'CombatAction',
    'CombatResult',
    'CombatGrid',
    'CombatAnalytics',
    'calculate_combat_balance',
    'generate_combat_recommendations'
]