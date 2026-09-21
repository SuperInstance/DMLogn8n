#!/usr/bin/env python3
"""
Combat Stress Load Test Scenario
Stress tests the combat engine with high-frequency combat actions
"""

import asyncio
import random
import time
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import aiohttp
import logging

from ..load_test_runner import LoadTestConfig, TestResult

logger = logging.getLogger(__name__)

@dataclass
class CombatCharacter:
    """Represents a character in combat"""
    character_id: str
    name: str
    class_type: str
    level: int
    health: int
    max_health: int
    armor_class: int
    initiative: int
    speed: int
    abilities: List[str]

@dataclass
class CombatAction:
    """Represents a combat action"""
    action_type: str
    character_id: str
    target_id: Optional[str]
    parameters: Dict[str, Any]
    execution_time: float  # seconds

class CombatStressScenario:
    """Stress tests the combat engine with intense combat scenarios"""

    def __init__(self, config: LoadTestConfig, metrics_collector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.total_requests = 0
        self.successful_requests = 0
        self.active_combats: Dict[str, Dict[str, Any]] = {}
        self.characters: List[CombatCharacter] = []

        # Combat action types
        self.action_types = [
            "attack", "spell_cast", "skill_use", "defend", "move", "dash",
            "disengage", "hide", "ready_action", "opportunity_attack",
            "grapple", "shove", "trip", "disarm", "special_ability"
        ]

        # Character classes
        self.character_classes = [
            "fighter", "wizard", "rogue", "cleric", "ranger", "paladin",
            "barbarian", "monk", "bard", "druid", "warlock", "sorcerer"
        ]

    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=200,  # High limit for combat stress
            limit_per_host=100,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.config.headers
        )

    def _generate_character(self, combat_id: str) -> CombatCharacter:
        """Generate a combat character"""
        character_id = str(uuid.uuid4())
        class_type = random.choice(self.character_classes)
        level = random.randint(1, 20)

        # Generate stats based on class and level
        base_health = {
            "fighter": 10, "wizard": 6, "rogue": 8, "cleric": 8,
            "ranger": 10, "paladin": 10, "barbarian": 12, "monk": 8,
            "bard": 8, "druid": 8, "warlock": 8, "sorcerer": 6
        }.get(class_type, 8)

        max_health = base_health + (level * random.randint(5, 10))
        armor_class = 10 + level // 2 + random.randint(-2, 5)
        initiative = random.randint(1, 20) + (level // 4)
        speed = random.randint(25, 35)

        # Generate abilities based on class
        class_abilities = {
            "fighter": ["attack", "defend", "special_ability"],
            "wizard": ["spell_cast", "skill_use", "ready_action"],
            "rogue": ["attack", "hide", "disengage", "opportunity_attack"],
            "cleric": ["spell_cast", "defend", "special_ability"],
            "ranger": ["attack", "skill_use", "dash"],
            "paladin": ["attack", "defend", "special_ability"],
            "barbarian": ["attack", "special_ability", "shove"],
            "monk": ["attack", "defend", "disarm", "trip"],
            "bard": ["skill_use", "special_ability"],
            "druid": ["spell_cast", "special_ability"],
            "warlock": ["spell_cast", "attack"],
            "sorcerer": ["spell_cast", "skill_use"]
        }.get(class_type, ["attack", "defend", "move"])

        return CombatCharacter(
            character_id=character_id,
            name=f"{class_type.title()}_{character_id[:8]}",
            class_type=class_type,
            level=level,
            health=max_health,
            max_health=max_health,
            armor_class=armor_class,
            initiative=initiative,
            speed=speed,
            abilities=class_abilities
        )

    async def _create_combat_session(self) -> str:
        """Create a new combat session"""
        combat_id = str(uuid.uuid4())
        combat_data = {
            "combat_id": combat_id,
            "scenario": random.choice(["dungeon_encounter", "outdoor_battle", "boss_fight"]),
            "environment": random.choice(["indoor", "outdoor", "mixed"]),
            "difficulty": random.choice(["easy", "normal", "hard", "deadly"]),
            "max_participants": random.randint(4, 12),
            "turn_time_limit": random.choice([30, 60, 120]),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/combat/session",
                json=combat_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "combat_create", response_time, response.status, True
                    )
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "combat_create",
                        "status": response.status,
                        "error": error_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "combat_create", response_time, response.status, False
                    )

                self.total_requests += 1

        except Exception as e:
            self.errors.append({
                "endpoint": "combat_create",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            logger.error(f"Failed to create combat session: {e}")

        # Store combat session
        self.active_combats[combat_id] = {
            "combat_data": combat_data,
            "participants": [],
            "current_turn": 0,
            "turn_order": [],
            "status": "active"
        }

        return combat_id

    async def _add_character_to_combat(self, combat_id: str, character: CombatCharacter):
        """Add a character to a combat session"""
        character_data = {
            "combat_id": combat_id,
            "character_id": character.character_id,
            "name": character.name,
            "class": character.class_type,
            "level": character.level,
            "health": character.health,
            "max_health": character.max_health,
            "armor_class": character.armor_class,
            "initiative": character.initiative,
            "speed": character.speed,
            "position": {"x": random.randint(0, 50), "y": random.randint(0, 50)},
            "status": "active"
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/combat/participant",
                json=character_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    await self.metrics_collector.record_request(
                        "combat_add_participant", response_time, response.status, True
                    )
                    self.active_combats[combat_id]["participants"].append(character)
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "combat_add_participant",
                        "status": response.status,
                        "error": error_data,
                        "character_id": character.character_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "combat_add_participant", response_time, response.status, False
                    )

                self.total_requests += 1

        except Exception as e:
            self.errors.append({
                "endpoint": "combat_add_participant",
                "error": str(e),
                "character_id": character.character_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1

    async def _execute_combat_action(self, combat_id: str, character: CombatCharacter) -> Optional[Dict[str, Any]]:
        """Execute a combat action"""
        # Select action based on character abilities
        action_type = random.choice(character.abilities)

        # Select target
        combat = self.active_combats[combat_id]
        available_targets = [c for c in combat["participants"] if c.character_id != character.character_id]
        target_id = random.choice(available_targets).character_id if available_targets else None

        # Generate action parameters
        action_params = self._generate_action_parameters(action_type, character, target_id)

        action_data = {
            "combat_id": combat_id,
            "character_id": character.character_id,
            "action_type": action_type,
            "target_id": target_id,
            "parameters": action_params,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/combat/action",
                json=action_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 200:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "combat_action", response_time, response.status, True
                    )

                    # Update character state based on result
                    if "damage" in result and target_id:
                        target_char = next((c for c in combat["participants"] if c.character_id == target_id), None)
                        if target_char:
                            target_char.health = max(0, target_char.health - result.get("damage", 0))

                    return result
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "combat_action",
                        "status": response.status,
                        "error": error_data,
                        "character_id": character.character_id,
                        "action_type": action_type,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "combat_action", response_time, response.status, False
                    )

                self.total_requests += 1
                return None

        except Exception as e:
            self.errors.append({
                "endpoint": "combat_action",
                "error": str(e),
                "character_id": character.character_id,
                "action_type": action_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            return None

    def _generate_action_parameters(self, action_type: str, character: CombatCharacter, target_id: Optional[str]) -> Dict[str, Any]:
        """Generate parameters for different action types"""
        params = {}

        if action_type == "attack":
            params.update({
                "attack_type": random.choice(["melee", "ranged"]),
                "damage_dice": f"{random.randint(1, 6)}d{random.choice([4, 6, 8, 10, 12])}",
                "attack_bonus": random.randint(1, 15),
                "damage_bonus": random.randint(0, 10)
            })

        elif action_type == "spell_cast":
            params.update({
                "spell_level": random.randint(1, min(9, character.level // 2)),
                "spell_type": random.choice(["damage", "healing", "buff", "debuff", "utility"]),
                "spell_school": random.choice(["evocation", "conjuration", "illusion", "necromancy"]),
                "damage_type": random.choice(["fire", "cold", "lightning", "poison", "psychic", "force"])
            })

        elif action_type == "skill_use":
            params.update({
                "skill_type": random.choice(["athletics", "acrobatics", "stealth", "perception", "investigation"]),
                "dc": random.randint(10, 25),
                "skill_bonus": random.randint(1, 12)
            })

        elif action_type == "defend":
            params.update({
                "defense_type": random.choice(["dodge", "block", "parry"]),
                "bonus_ac": random.randint(1, 5)
            })

        elif action_type == "move":
            params.update({
                "movement_type": random.choice(["walk", "run", "climb", "swim"]),
                "distance": random.randint(5, min(60, character.speed)),
                "destination": {"x": random.randint(0, 50), "y": random.randint(0, 50)}
            })

        elif action_type == "special_ability":
            params.update({
                "ability_name": f"special_{random.randint(1, 100)}",
                "ability_type": random.choice(["passive", "active", "reaction"]),
                "cooldown": random.randint(1, 10),
                "resource_cost": random.randint(0, 5)
            })

        return params

    async def _run_combat_simulation(self, combat_id: str):
        """Run a complete combat simulation"""
        combat = self.active_combats[combat_id]
        start_time = time.time()

        # Initialize turn order
        combat["turn_order"] = sorted(combat["participants"], key=lambda c: c.initiative, reverse=True)
        combat["current_turn"] = 0

        # Run combat rounds
        round_number = 1
        while (time.time() - start_time < self.config.duration and
               any(c.health > 0 for c in combat["participants"])):

            logger.debug(f"Combat {combat_id} - Round {round_number}")

            # Process each character's turn
            for character in combat["turn_order"]:
                if character.health <= 0:
                    continue

                # Execute action
                result = await self._execute_combat_action(combat_id, character)

                # Brief delay between actions
                await asyncio.sleep(random.uniform(0.1, 0.5))

            round_number += 1

            # Check if combat should end (most characters defeated)
            alive_characters = sum(1 for c in combat["participants"] if c.health > 0)
            if alive_characters <= 2:  # End combat when only 2 or fewer characters remain
                break

        # Update combat status
        combat["status"] = "completed"
        combat["rounds_completed"] = round_number

        logger.info(f"Combat {combat_id} completed after {round_number} rounds")

    async def _setup_combats(self):
        """Setup combat sessions"""
        num_combats = min(self.config.users // 4, 20)  # 4 participants per combat minimum

        for i in range(num_combats):
            combat_id = await self._create_combat_session()

            # Add participants to combat
            combat = self.active_combats[combat_id]
            num_participants = min(4, self.config.users - len(self.characters))

            for j in range(num_participants):
                character = self._generate_character(combat_id)
                self.characters.append(character)
                await self._add_character_to_combat(combat_id, character)

            # Brief delay between combat setup
            await asyncio.sleep(0.1)

        logger.info(f"Created {len(self.active_combats)} combat sessions with {len(self.characters)} characters")

    async def execute(self) -> TestResult:
        """Execute the combat stress test"""
        logger.info(f"Starting combat stress test with {self.config.users} simulated users")

        try:
            await self._initialize_session()
            await self._setup_combats()

            if not self.active_combats:
                raise RuntimeError("No combat sessions were created")

            # Run combat simulations concurrently
            combat_tasks = []
            for combat_id in self.active_combats.keys():
                task = asyncio.create_task(self._run_combat_simulation(combat_id))
                combat_tasks.append(task)

            # Wait for all combats to complete
            await asyncio.gather(*combat_tasks, return_exceptions=True)

        finally:
            if self.session:
                await self.session.close()

        # Calculate test results
        return self._calculate_results()

    def _calculate_results(self) -> TestResult:
        """Calculate test results from collected metrics"""
        if not self.request_times:
            return TestResult(
                test_name=self.config.name,
                scenario="combat_stress",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration=0,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                throughput=0,
                error_rate=100.0,
                errors=self.errors,
                metrics={},
                system_metrics={},
                baseline_comparison=None
            )

        # Calculate statistics
        self.request_times.sort()
        total_requests = len(self.request_times)
        successful_requests = self.successful_requests
        failed_requests = total_requests - successful_requests

        avg_response_time = sum(self.request_times) / total_requests
        min_response_time = min(self.request_times)
        max_response_time = max(self.request_times)

        p95_index = int(0.95 * total_requests)
        p99_index = int(0.99 * total_requests)
        p95_response_time = self.request_times[p95_index] if p95_index < total_requests else max_response_time
        p99_response_time = self.request_times[p99_index] if p99_index < total_requests else max_response_time

        duration = self.config.duration
        requests_per_second = total_requests / duration if duration > 0 else 0

        # Estimate throughput
        avg_response_size = 1024  # bytes
        throughput = (requests_per_second * avg_response_size) / (1024 * 1024)  # MB/s

        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 100

        # Additional combat-specific metrics
        total_rounds = sum(combat.get("rounds_completed", 0) for combat in self.active_combats.values())
        avg_rounds_per_combat = total_rounds / len(self.active_combats) if self.active_combats else 0

        metrics = {
            "combats_simulated": len(self.active_combats),
            "characters_simulated": len(self.characters),
            "total_combat_rounds": total_rounds,
            "avg_rounds_per_combat": avg_rounds_per_combat,
            "class_distribution": {
                class_type: sum(1 for c in self.characters if c.class_type == class_type)
                for class_type in set(c.class_type for c in self.characters)
            },
            "avg_level": sum(c.level for c in self.characters) / len(self.characters) if self.characters else 0,
            "action_type_distribution": {
                action_type: len([e for e in self.errors if e.get("action_type") == action_type])
                for action_type in self.action_types
            },
            "avg_participants_per_combat": sum(len(combat["participants"]) for combat in self.active_combats.values()) / len(self.active_combats) if self.active_combats else 0,
            "completed_combats": sum(1 for combat in self.active_combats.values() if combat.get("status") == "completed")
        }

        return TestResult(
            test_name=self.config.name,
            scenario="combat_stress",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            throughput=throughput,
            error_rate=error_rate,
            errors=self.errors,
            metrics=metrics,
            system_metrics={},
            baseline_comparison=None
        )