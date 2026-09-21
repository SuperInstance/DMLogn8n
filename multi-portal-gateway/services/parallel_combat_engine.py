"""
Parallel Combat Resolution Engine
Processes hundreds of combat encounters simultaneously
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import defaultdict, deque
import uuid
import json
import random
import math
from enum import Enum
import multiprocessing as mp


class CombatActionType(Enum):
    ATTACK = "attack"
    DEFEND = "defend"
    SPELL = "spell"
    ABILITY = "ability"
    ITEM = "item"
    MOVE = "move"
    DODGE = "dodge"
    PARRY = "parry"
    COUNTER = "counter"


class DamageType(Enum):
    PHYSICAL = "physical"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    NECROTIC = "necrotic"
    FORCE = "force"
    THUNDER = "thunder"
    ACID = "acid"


class CombatStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLED = "fled"
    STALEMATE = "stalemate"


@dataclass
class Combatant:
    """Combat participant"""
    combatant_id: str
    name: str
    max_hp: int
    current_hp: int
    armor_class: int
    initiative: int
    speed: int
    team: str
    position: Tuple[float, float] = (0, 0)
    status_effects: List[Dict[str, Any]] = field(default_factory=list)
    actions_taken: int = 0
    max_actions: int = 1
    bonus_actions: int = 0
    reactions: int = 0
    is_alive: bool = True
    stats: Dict[str, int] = field(default_factory=dict)
    resistances: List[DamageType] = field(default_factory=list)
    immunities: List[DamageType] = field(default_factory=list)
    vulnerabilities: List[DamageType] = field(default_factory=list)


@dataclass
class CombatAction:
    """Combat action"""
    action_id: str
    combatant_id: str
    action_type: CombatActionType
    target_id: Optional[str] = None
    target_position: Optional[Tuple[float, float]] = None
    damage: Optional[int] = None
    damage_type: Optional[DamageType] = None
    spell_id: Optional[str] = None
    item_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_time: datetime = field(default_factory=datetime.now)


@dataclass
class CombatEvent:
    """Event in combat"""
    event_id: str
    combat_id: str
    event_type: str
    description: str
    participants: List[str] = field(default_factory=list)
    damage: Optional[int] = None
    healing: Optional[int] = None
    status_effect: Optional[Dict[str, Any]] = None
    position_change: Optional[Tuple[float, float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CombatEncounter:
    """Combat encounter"""
    encounter_id: str
    name: str
    combatants: Dict[str, Combatant] = field(default_factory=dict)
    initiative_order: List[str] = field(default_factory=list)
    current_turn: int = 0
    round_number: int = 1
    status: CombatStatus = CombatStatus.ACTIVE
    environment: Dict[str, Any] = field(default_factory=dict)
    events: List[CombatEvent] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    victory_conditions: List[Dict[str, Any]] = field(default_factory=list)
    defeat_conditions: List[Dict[str, Any]] = field(default_factory=list)
    loot: List[Dict[str, Any]] = field(default_factory=list)
    experience_reward: int = 0


class ParallelCombatEngine:
    """Parallel combat resolution engine"""

    def __init__(self,
                 max_concurrent_encounters: int = 500,
                 max_actions_per_second: int = 1000):

        self.max_concurrent_encounters = max_concurrent_encounters
        self.max_actions_per_second = max_actions_per_second

        # Active encounters
        self.active_encounters: Dict[str, CombatEncounter] = {}
        self.encounter_queue = asyncio.Queue(maxsize=1000)

        # Action processing
        self.action_queue = asyncio.Queue(maxsize=5000)
        self.reaction_queue = asyncio.Queue(maxsize=2000)
        self.damage_queue = asyncio.Queue(maxsize=3000)

        # Parallel processors
        self.thread_pool = ThreadPoolExecutor(max_workers=100)
        self.process_pool = ProcessPoolExecutor(max_processes=20)

        # Combat calculators
        self.damage_calculators = {}
        self.effect_processors = {}

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()

        # Metrics
        self.metrics = {
            "encounters_processed": 0,
            "actions_processed": 0,
            "damage_calculated": 0,
            "average_encounter_time": 0.0,
            "actions_per_second": 0.0,
            "active_encounters": 0,
            "total_damage_dealt": 0
        }

        # Combat rules
        self.critical_hit_threshold = 20
        self.critical_miss_threshold = 1
        self.advantage_bonus = 5
        self.disadvantage_penalty = -5

        # Performance optimization
        self.batch_size = 50
        self.processing_interval = 0.01  # 10ms

        self.is_running = False

    async def initialize(self):
        """Initialize the combat engine"""
        logger.info(f"Initializing parallel combat engine for {self.max_concurrent_encounters} encounters")

        # Start background processors
        await self._start_processors()

        self.is_running = True
        logger.info("Parallel combat engine initialized")

    async def _start_processors(self):
        """Start all background processors"""
        # Encounter processor
        task = asyncio.create_task(self._encounter_processor())
        self.background_tasks.add(task)

        # Action processors (multiple for parallelism)
        for i in range(10):
            task = asyncio.create_task(self._action_processor(f"action_proc_{i}"))
            self.background_tasks.add(task)

        # Damage processors
        for i in range(5):
            task = asyncio.create_task(self._damage_processor(f"damage_proc_{i}"))
            self.background_tasks.add(task)

        # Effect processors
        for i in range(3):
            task = asyncio.create_task(self._effect_processor(f"effect_proc_{i}"))
            self.background_tasks.add(task)

        # Initiative processor
        task = asyncio.create_task(self._initiative_processor())
        self.background_tasks.add(task)

        # Status checker
        task = asyncio.create_task(self._status_checker())
        self.background_tasks.add(task)

        # Metrics collector
        task = asyncio.create_task(self._metrics_collector())
        self.background_tasks.add(task)

        # Cleanup processor
        task = asyncio.create_task(self._cleanup_processor())
        self.background_tasks.add(task)

    async def create_encounter(self,
                              name: str,
                              combatants: List[Combatant],
                              environment: Optional[Dict[str, Any]] = None) -> str:
        """Create a new combat encounter"""
        encounter_id = str(uuid.uuid4())

        # Calculate initiative
        for combatant in combatants:
            initiative_roll = random.randint(1, 20) + combatant.initiative
            combatant.initiative = initiative_roll

        # Sort by initiative
        combatants.sort(key=lambda c: c.initiative, reverse=True)

        # Create encounter
        encounter = CombatEncounter(
            encounter_id=encounter_id,
            name=name,
            combatants={c.combatant_id: c for c in combatants},
            initiative_order=[c.combatant_id for c in combatants],
            environment=environment or {},
            victory_conditions=[{"type": "eliminate_all_enemies"}],
            defeat_conditions=[{"type": "all_allies_defeated"}]
        )

        self.active_encounters[encounter_id] = encounter
        self.metrics["encounters_processed"] += 1

        # Add to queue
        await self.encounter_queue.put({
            "encounter_id": encounter_id,
            "action": "start"
        })

        return encounter_id

    async def submit_action(self, encounter_id: str, action: CombatAction) -> bool:
        """Submit an action for processing"""
        encounter = self.active_encounters.get(encounter_id)
        if not encounter or encounter.status != CombatStatus.ACTIVE:
            return False

        # Validate action
        if not await self._validate_action(encounter, action):
            return False

        # Add to queue
        await self.action_queue.put({
            "encounter_id": encounter_id,
            "action": action
        })

        return True

    async def _encounter_processor(self):
        """Process combat encounters"""
        while self.is_running:
            try:
                # Get batch of encounters
                encounters_batch = []
                for _ in range(min(20, self.encounter_queue.qsize())):
                    if not self.encounter_queue.empty():
                        request = await self.encounter_queue.get()
                        encounters_batch.append(request)

                if encounters_batch:
                    # Process encounters in parallel
                    await asyncio.gather(
                        *[self._process_encounter_request(request) for request in encounters_batch],
                        return_exceptions=True
                    )

                # Process active encounters
                active_encounters = [
                    encounter for encounter in self.active_encounters.values()
                    if encounter.status == CombatStatus.ACTIVE
                ]

                if active_encounters:
                    await asyncio.gather(
                        *[self._process_encounter_tick(encounter) for encounter in active_encounters[:50]],
                        return_exceptions=True
                    )

                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"Encounter processor error: {e}")
                await asyncio.sleep(0.05)

    async def _process_encounter_request(self, request: Dict[str, Any]):
        """Process encounter request"""
        encounter_id = request.get("encounter_id")
        action = request.get("action")
        encounter = self.active_encounters.get(encounter_id)

        if not encounter:
            return

        if action == "start":
            await self._start_encounter(encounter)
        elif action == "pause":
            encounter.status = CombatStatus.PAUSED
        elif action == "resume":
            encounter.status = CombatStatus.ACTIVE

    async def _start_encounter(self, encounter: CombatEncounter):
        """Start a combat encounter"""
        # Create starting event
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="combat_start",
            description=f"Combat initiated: {encounter.name}",
            participants=list(encounter.combatants.keys())
        )

        encounter.events.append(event)
        encounter.started_at = datetime.now()
        encounter.last_activity = datetime.now()

        # Set first turn
        await self._start_next_turn(encounter)

    async def _start_next_turn(self, encounter: CombatEncounter):
        """Start the next turn in combat"""
        # Find next alive combatant
        while encounter.current_turn < len(encounter.initiative_order):
            combatant_id = encounter.initiative_order[encounter.current_turn]
            combatant = encounter.combatants[combatant_id]

            if combatant.is_alive:
                # Reset actions
                combatant.actions_taken = 0
                combatant.bonus_actions = 1
                combatant.reactions = 1

                # Create turn start event
                event = CombatEvent(
                    event_id=str(uuid.uuid4()),
                    combat_id=encounter.encounter_id,
                    event_type="turn_start",
                    description=f"{combatant.name}'s turn begins",
                    participants=[combatant_id]
                )

                encounter.events.append(event)
                encounter.last_activity = datetime.now()
                return

            encounter.current_turn += 1

        # No more combatants with turns, start new round
        encounter.current_turn = 0
        encounter.round_number += 1

        # Create new round event
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="round_start",
            description=f"Round {encounter.round_number} begins"
        )

        encounter.events.append(event)

        # Start next turn
        await self._start_next_turn(encounter)

    async def _process_encounter_tick(self, encounter: CombatEncounter):
        """Process single tick for an encounter"""
        # Check for victory/defeat conditions
        await self._check_victory_conditions(encounter)

        # Process status effects
        await self._process_status_effects(encounter)

        # Check for timeout
        if datetime.now() - encounter.last_activity > timedelta(minutes=30):
            encounter.status = CombatStatus.STALEMATE

    async def _action_processor(self, processor_id: str):
        """Process combat actions"""
        while self.is_running:
            try:
                # Get batch of actions
                actions_batch = []
                for _ in range(min(self.batch_size, self.action_queue.qsize())):
                    if not self.action_queue.empty():
                        action_request = await self.action_queue.get()
                        actions_batch.append(action_request)

                if actions_batch:
                    # Process actions in parallel
                    results = await asyncio.gather(
                        *[self._process_action(request) for request in actions_batch],
                        return_exceptions=True
                    )

                    # Handle results
                    for request, result in zip(actions_batch, results):
                        if isinstance(result, Exception):
                            logger.error(f"Action processing error: {result}")
                        else:
                            await self._handle_action_result(request, result)

                await asyncio.sleep(self.processing_interval)

            except Exception as e:
                logger.error(f"Action processor {processor_id} error: {e}")
                await asyncio.sleep(self.processing_interval)

    async def _process_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual action"""
        encounter_id = request.get("encounter_id")
        action = request.get("action")
        encounter = self.active_encounters.get(encounter_id)

        if not encounter:
            return {"error": "Encounter not found"}

        combatant = encounter.combatants.get(action.combatant_id)
        if not combatant or not combatant.is_alive:
            return {"error": "Combatant not available"}

        start_time = datetime.now()

        # Process based on action type
        if action.action_type == CombatActionType.ATTACK:
            result = await self._process_attack(encounter, action)
        elif action.action_type == CombatActionType.SPELL:
            result = await self._process_spell(encounter, action)
        elif action.action_type == CombatActionType.ABILITY:
            result = await self._process_ability(encounter, action)
        elif action.action_type == CombatActionType.MOVE:
            result = await self._process_move(encounter, action)
        elif action.action_type == CombatActionType.DEFEND:
            result = await self._process_defend(encounter, action)
        elif action.action_type == CombatActionType.DODGE:
            result = await self._process_dodge(encounter, action)
        else:
            result = {"error": f"Unknown action type: {action.action_type}"}

        # Update combatant
        combatant.actions_taken += 1

        # Check if turn should end
        if combatant.actions_taken >= combatant.max_actions:
            await self._end_turn(encounter, combatant.combatant_id)

        # Update metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics["actions_processed"] += 1

        result["processing_time"] = processing_time
        return result

    async def _process_attack(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process attack action"""
        attacker = encounter.combatants[action.combatant_id]
        target = encounter.combatants.get(action.target_id)

        if not target or not target.is_alive:
            return {"error": "Invalid target"}

        # Calculate attack roll
        attack_roll = random.randint(1, 20)
        is_critical = attack_roll >= self.critical_hit_threshold
        is_miss = attack_roll <= self.critical_miss_threshold

        # Add attacker's attack bonus
        attack_bonus = attacker.stats.get("attack_bonus", 0)
        total_attack = attack_roll + attack_bonus

        # Check against target's AC
        hit = total_attack >= target.armor_class and not is_miss

        damage = 0
        damage_type = action.damage_type or DamageType.PHYSICAL

        if hit:
            # Calculate damage
            base_damage = action.damage or random.randint(1, 8) + attacker.stats.get("strength_bonus", 0)

            if is_critical:
                base_damage *= 2

            # Apply resistances/immunities
            if damage_type in target.immunities:
                damage = 0
            elif damage_type in target.resistances:
                damage = base_damage // 2
            elif damage_type in target.vulnerabilities:
                damage = base_damage * 2
            else:
                damage = base_damage

            # Apply damage
            target.current_hp = max(0, target.current_hp - damage)

            # Check if target is defeated
            if target.current_hp <= 0:
                target.is_alive = False

            # Update metrics
            self.metrics["total_damage_dealt"] += damage

        # Create event
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="attack",
            description=f"{attacker.name} attacks {target.name}: {'Hit!' if hit else 'Miss!'}",
            participants=[action.combatant_id, action.target_id],
            damage=damage if hit else None,
            metadata={
                "attack_roll": attack_roll,
                "total_attack": total_attack,
                "target_ac": target.armor_class,
                "critical_hit": is_critical,
                "critical_miss": is_miss
            }
        )

        encounter.events.append(event)

        return {
            "success": True,
            "hit": hit,
            "damage": damage,
            "critical_hit": is_critical,
            "target_defeated": not target.is_alive
        }

    async def _process_spell(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process spell action"""
        # Simulate spell casting
        await asyncio.sleep(0.1)

        caster = encounter.combatants[action.combatant_id]

        # Create spell event
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="spell",
            description=f"{caster.name} casts {action.spell_id or 'a spell'}",
            participants=[action.combatant_id],
            metadata={"spell_id": action.spell_id}
        )

        encounter.events.append(event)

        return {"success": True, "message": "Spell cast successfully"}

    async def _process_ability(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process special ability"""
        await asyncio.sleep(0.05)

        combatant = encounter.combatants[action.combatant_id]

        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="ability",
            description=f"{combatant.name} uses a special ability",
            participants=[action.combatant_id]
        )

        encounter.events.append(event)

        return {"success": True, "message": "Ability used"}

    async def _process_move(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process movement action"""
        combatant = encounter.combatants[action.combatant_id]

        if action.target_position:
            # Calculate distance
            old_pos = combatant.position
            new_pos = action.target_position
            distance = math.sqrt((new_pos[0] - old_pos[0])**2 + (new_pos[1] - old_pos[1])**2)

            # Check if within speed limit
            if distance <= combatant.speed:
                combatant.position = new_pos

                event = CombatEvent(
                    event_id=str(uuid.uuid4()),
                    combat_id=encounter.encounter_id,
                    event_type="move",
                    description=f"{combatant.name} moves to position {new_pos}",
                    participants=[action.combatant_id],
                    position_change=new_pos
                )

                encounter.events.append(event)

                return {"success": True, "distance": distance}
            else:
                return {"error": "Movement exceeds speed limit"}

        return {"error": "No target position specified"}

    async def _process_defend(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process defend action"""
        combatant = encounter.combatants[action.combatant_id]

        # Add defense bonus
        status_effect = {
            "type": "defending",
            "duration": 1,
            "ac_bonus": 2,
            "description": "Defensive stance"
        }

        combatant.status_effects.append(status_effect)

        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="defend",
            description=f"{combatant.name} takes a defensive stance",
            participants=[action.combatant_id],
            status_effect=status_effect
        )

        encounter.events.append(event)

        return {"success": True, "ac_bonus": 2}

    async def _process_dodge(self, encounter: CombatEncounter, action: CombatAction) -> Dict[str, Any]:
        """Process dodge action"""
        combatant = encounter.combatants[action.combatant_id]

        # Add dodge effect
        status_effect = {
            "type": "dodging",
            "duration": 1,
            "description": "Dodging stance - attacks against you have disadvantage"
        }

        combatant.status_effects.append(status_effect)

        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="dodge",
            description=f"{combatant.name} dodges",
            participants=[action.combatant_id],
            status_effect=status_effect
        )

        encounter.events.append(event)

        return {"success": True, "message": "Dodge successful"}

    async def _damage_processor(self, processor_id: str):
        """Process damage calculations in parallel"""
        while self.is_running:
            try:
                # Get batch of damage calculations
                damage_batch = []
                for _ in range(min(30, self.damage_queue.qsize())):
                    if not self.damage_queue.empty():
                        damage_request = await self.damage_queue.get()
                        damage_batch.append(damage_request)

                if damage_batch:
                    # Process damage in parallel
                    await asyncio.gather(
                        *[self._calculate_damage(request) for request in damage_batch],
                        return_exceptions=True
                    )

                await asyncio.sleep(0.02)

            except Exception as e:
                logger.error(f"Damage processor {processor_id} error: {e}")
                await asyncio.sleep(0.02)

    async def _calculate_damage(self, request: Dict[str, Any]):
        """Calculate damage with all modifiers"""
        # Simulate complex damage calculation
        await asyncio.sleep(0.001)

        self.metrics["damage_calculated"] += 1

    async def _effect_processor(self, processor_id: str):
        """Process status effects"""
        while self.is_running:
            try:
                # Get all active encounters
                for encounter in list(self.active_encounters.values())[:20]:
                    await self._process_status_effects(encounter)

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Effect processor {processor_id} error: {e}")
                await asyncio.sleep(0.1)

    async def _process_status_effects(self, encounter: CombatEncounter):
        """Process status effects for all combatants"""
        for combatant in encounter.combatants.values():
            if not combatant.is_alive:
                continue

            # Process each status effect
            effects_to_remove = []
            for effect in combatant.status_effects:
                # Decrease duration
                effect["duration"] = max(0, effect["duration"] - 1)

                # Apply effect
                if effect["type"] == "poison":
                    damage = random.randint(1, 6)
                    combatant.current_hp = max(0, combatant.current_hp - damage)

                elif effect["type"] == "regeneration":
                    healing = random.randint(1, 4)
                    combatant.current_hp = min(combatant.max_hp, combatant.current_hp + healing)

                # Mark for removal if expired
                if effect["duration"] <= 0:
                    effects_to_remove.append(effect)

            # Remove expired effects
            for effect in effects_to_remove:
                combatant.status_effects.remove(effect)

    async def _initiative_processor(self):
        """Process initiative tracking"""
        while self.is_running:
            try:
                # Check for encounters needing next turn
                for encounter in list(self.active_encounters.values()):
                    if encounter.status == CombatStatus.ACTIVE:
                        # Check if current combatant has acted
                        current_combatant_id = encounter.initiative_order[encounter.current_turn]
                        current_combatant = encounter.combatants[current_combatant_id]

                        if current_combatant.actions_taken >= current_combatant.max_actions:
                            # Auto-end turn after timeout
                            if datetime.now() - encounter.last_activity > timedelta(seconds=30):
                                await self._end_turn(encounter, current_combatant_id)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Initiative processor error: {e}")
                await asyncio.sleep(1)

    async def _end_turn(self, encounter: CombatEncounter, combatant_id: str):
        """End current combatant's turn"""
        # Create turn end event
        combatant = encounter.combatants[combatant_id]
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="turn_end",
            description=f"{combatant.name}'s turn ends",
            participants=[combatant_id]
        )

        encounter.events.append(event)

        # Move to next combatant
        encounter.current_turn += 1

        # Start next turn or new round
        if encounter.current_turn >= len(encounter.initiative_order):
            encounter.current_turn = 0
            encounter.round_number += 1

        # Start next turn if combat is active
        if encounter.status == CombatStatus.ACTIVE:
            await self._start_next_turn(encounter)

    async def _status_checker(self):
        """Check encounter status"""
        while self.is_running:
            try:
                for encounter in list(self.active_encounters.values()):
                    if encounter.status == CombatStatus.ACTIVE:
                        await self._check_victory_conditions(encounter)

                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Status checker error: {e}")
                await asyncio.sleep(0.5)

    async def _check_victory_conditions(self, encounter: CombatEncounter):
        """Check if encounter should end"""
        # Check for total victory
        teams_alive = defaultdict(int)
        for combatant in encounter.combatants.values():
            if combatant.is_alive:
                teams_alive[combatant.team] += 1

        # Check victory conditions
        for condition in encounter.victory_conditions:
            if condition["type"] == "eliminate_all_enemies":
                player_team = "player"  # Assuming player team
                enemy_teams = [team for team in teams_alive if team != player_team]

                if len(enemy_teams) == 0 or all(teams_alive[team] == 0 for team in enemy_teams):
                    encounter.status = CombatStatus.VICTORY
                    await self._end_encounter(encounter, "victory")

        # Check defeat conditions
        for condition in encounter.defeat_conditions:
            if condition["type"] == "all_allies_defeated":
                if teams_alive.get("player", 0) == 0:
                    encounter.status = CombatStatus.DEFEAT
                    await self._end_encounter(encounter, "defeat")

    async def _end_encounter(self, encounter: CombatEncounter, result: str):
        """End combat encounter"""
        # Create end event
        event = CombatEvent(
            event_id=str(uuid.uuid4()),
            combat_id=encounter.encounter_id,
            event_type="combat_end",
            description=f"Combat ended: {result}",
            metadata={"result": result, "rounds": encounter.round_number}
        )

        encounter.events.append(event)

        # Calculate encounter duration
        duration = datetime.now() - encounter.started_at
        self.metrics["average_encounter_time"] = (
            (self.metrics["average_encounter_time"] * (self.metrics["encounters_processed"] - 1) +
             duration.total_seconds()) / self.metrics["encounters_processed"]
        )

        # Award experience and loot
        if result == "victory":
            await self._award_rewards(encounter)

    async def _award_rewards(self, encounter: CombatEncounter):
        """Award experience and loot"""
        # Calculate experience
        total_exp = encounter.experience_reward

        # Distribute to surviving players
        for combatant in encounter.combatants.values():
            if combatant.is_alive and combatant.team == "player":
                # Award experience (would normally save to character)
                pass

    async def _validate_action(self, encounter: CombatEncounter, action: CombatAction) -> bool:
        """Validate if action is legal"""
        combatant = encounter.combatants.get(action.combatant_id)

        if not combatant or not combatant.is_alive:
            return False

        # Check if it's combatant's turn
        if encounter.initiative_order[encounter.current_turn] != action.combatant_id:
            return False

        # Check action availability
        if combatant.actions_taken >= combatant.max_actions:
            return False

        return True

    async def _handle_action_result(self, request: Dict[str, Any], result: Dict[str, Any]):
        """Handle action result"""
        encounter_id = request.get("encounter_id")
        encounter = self.active_encounters.get(encounter_id)

        if not encounter:
            return

        # Update last activity
        encounter.last_activity = datetime.now()

    async def _metrics_collector(self):
        """Collect combat metrics"""
        while self.is_running:
            try:
                # Calculate actions per second
                self.metrics["actions_per_second"] = (
                    self.metrics["actions_processed"] / max(1, time.time())
                )

                # Update active encounters
                self.metrics["active_encounters"] = len(
                    [e for e in self.active_encounters.values() if e.status == CombatStatus.ACTIVE]
                )

                # Log metrics
                logger.info(f"Combat metrics: {self.metrics}")

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_processor(self):
        """Clean up completed encounters"""
        while self.is_running:
            try:
                # Remove completed encounters older than 5 minutes
                cutoff = datetime.now() - timedelta(minutes=5)

                to_remove = []
                for encounter_id, encounter in self.active_encounters.items():
                    if (encounter.status in [CombatStatus.VICTORY, CombatStatus.DEFEAT, CombatStatus.STALEMATE] and
                        encounter.last_activity < cutoff):
                        to_remove.append(encounter_id)

                for encounter_id in to_remove:
                    del self.active_encounters[encounter_id]

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"Cleanup processor error: {e}")
                await asyncio.sleep(300)

    async def get_encounter_state(self, encounter_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an encounter"""
        encounter = self.active_encounters.get(encounter_id)
        if not encounter:
            return None

        return {
            "encounter_id": encounter.encounter_id,
            "name": encounter.name,
            "status": encounter.status.value,
            "round": encounter.round_number,
            "current_turn": encounter.current_turn,
            "combatants": {
                cid: {
                    "name": c.name,
                    "hp": c.current_hp,
                    "max_hp": c.max_hp,
                    "ac": c.armor_class,
                    "alive": c.is_alive,
                    "position": c.position,
                    "team": c.team
                }
                for cid, c in encounter.combatants.items()
            },
            "events": [
                {
                    "type": e.event_type,
                    "description": e.description,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in encounter.events[-10:]  # Last 10 events
            ]
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get combat engine metrics"""
        return self.metrics.copy()

    async def shutdown(self):
        """Shutdown the combat engine"""
        logger.info("Shutting down parallel combat engine")

        self.is_running = False

        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Shutdown executors
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        logger.info("Parallel combat engine shutdown complete")


# Test function
async def test_combat_engine():
    """Test the combat engine"""
    engine = ParallelCombatEngine(
        max_concurrent_encounters=100,
        max_actions_per_second=500
    )

    await engine.initialize()

    # Create test combatants
    player = Combatant(
        combatant_id="player_1",
        name="Hero",
        max_hp=50,
        current_hp=50,
        armor_class=16,
        initiative=3,
        speed=30,
        team="player",
        stats={"attack_bonus": 5, "strength_bonus": 3}
    )

    goblin = Combatant(
        combatant_id="goblin_1",
        name="Goblin",
        max_hp=15,
        current_hp=15,
        armor_class=12,
        initiative=1,
        speed=25,
        team="enemy",
        stats={"attack_bonus": 2, "strength_bonus": 0}
    )

    # Create encounter
    encounter_id = await engine.create_encounter(
        name="Test Combat",
        combatants=[player, goblin]
    )

    # Submit some actions
    await engine.submit_action(encounter_id, CombatAction(
        action_id="action_1",
        combatant_id="player_1",
        action_type=CombatActionType.ATTACK,
        target_id="goblin_1",
        damage_type=DamageType.PHYSICAL
    ))

    # Wait for processing
    await asyncio.sleep(2)

    # Get encounter state
    state = await engine.get_encounter_state(encounter_id)
    print(f"Encounter status: {state['status']}")
    print(f"Current round: {state['round']}")

    # Get metrics
    metrics = await engine.get_metrics()
    print(f"Actions processed: {metrics['actions_processed']}")
    print(f"Damage dealt: {metrics['total_damage_dealt']}")

    await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(test_combat_engine())