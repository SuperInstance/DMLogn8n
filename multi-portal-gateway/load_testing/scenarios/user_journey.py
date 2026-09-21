#!/usr/bin/env python3
"""
User Journey Load Test Scenario
Simulates realistic user behavior patterns in the DMLogn8n platform
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
class UserPersona:
    """Defines user persona characteristics"""
    name: str
    experience_level: str  # beginner, intermediate, advanced
    session_duration: int  # minutes
    actions_per_session: int
    preferred_features: List[str]
    device_type: str
    network_speed: str  # slow, average, fast

@dataclass
class UserAction:
    """Defines a user action"""
    action_type: str
    endpoint: str
    method: str
    payload_template: Dict[str, Any]
    expected_status: int
    weight: float  # Probability weight

class UserJourneyScenario:
    """Simulates realistic user journey patterns"""

    def __init__(self, config: LoadTestConfig, metrics_collector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.users: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.total_requests = 0
        self.successful_requests = 0

        # User personas
        self.personas = self._generate_personas()
        self.user_actions = self._define_user_actions()

    def _generate_personas(self) -> List[UserPersona]:
        """Generate diverse user personas"""
        personas = [
            # Casual Gamer
            UserPersona(
                name="casual_gamer",
                experience_level="beginner",
                session_duration=30,
                actions_per_session=20,
                preferred_features=["character_creation", "simple_combat", "dialogue"],
                device_type="mobile",
                network_speed="average"
            ),

            # Dungeon Master
            UserPersona(
                name="dungeon_master",
                experience_level="advanced",
                session_duration=120,
                actions_per_session=100,
                preferred_features=["world_building", "npc_management", "story_crafting"],
                device_type="desktop",
                network_speed="fast"
            ),

            # Power Player
            UserPersona(
                name="power_player",
                experience_level="advanced",
                session_duration=90,
                actions_per_session=80,
                preferred_features=["complex_combat", "character_optimization", "strategy"],
                device_type="desktop",
                network_speed="fast"
            ),

            # Story Explorer
            UserPersona(
                name="story_explorer",
                experience_level="intermediate",
                session_duration=60,
                actions_per_session=40,
                preferred_features=["dialogue", "lore_discovery", "quest_progression"],
                device_type="tablet",
                network_speed="average"
            ),

            # Social Player
            UserPersona(
                name="social_player",
                experience_level="intermediate",
                session_duration=45,
                actions_per_session=30,
                preferred_features=["multiplayer", "chat", "group_activities"],
                device_type="mobile",
                network_speed="slow"
            )
        ]
        return personas

    def _define_user_actions(self) -> List[UserAction]:
        """Define available user actions"""
        return [
            # Authentication actions
            UserAction(
                action_type="login",
                endpoint="/api/auth/login",
                method="POST",
                payload_template={"username": "{user_id}", "password": "password123"},
                expected_status=200,
                weight=0.1
            ),

            UserAction(
                action_type="logout",
                endpoint="/api/auth/logout",
                method="POST",
                payload_template={},
                expected_status=200,
                weight=0.05
            ),

            # Character actions
            UserAction(
                action_type="create_character",
                endpoint="/api/characters",
                method="POST",
                payload_template={
                    "name": "Character_{random}",
                    "class": "{random_class}",
                    "race": "{random_race}",
                    "background": "{random_background}"
                },
                expected_status=201,
                weight=0.15
            ),

            UserAction(
                action_type="view_character",
                endpoint="/api/characters/{character_id}",
                method="GET",
                payload_template={},
                expected_status=200,
                weight=0.2
            ),

            UserAction(
                action_type="update_character",
                endpoint="/api/characters/{character_id}",
                method="PUT",
                payload_template={
                    "level": "{random_level}",
                    "experience": "{random_xp}",
                    "health": "{random_health}"
                },
                expected_status=200,
                weight=0.1
            ),

            # Game actions
            UserAction(
                action_type="start_session",
                endpoint="/api/sessions",
                method="POST",
                payload_template={
                    "campaign_id": "{campaign_id}",
                    "players": ["{player_id}"],
                    "scenario": "dungeon_crawl"
                },
                expected_status=201,
                weight=0.05
            ),

            UserAction(
                action_type="combat_action",
                endpoint="/api/combat/action",
                method="POST",
                payload_template={
                    "character_id": "{character_id}",
                    "action_type": "{combat_action}",
                    "target": "{target_id}",
                    "dice_roll": "{random_dice}"
                },
                expected_status=200,
                weight=0.25
            ),

            UserAction(
                action_type="dialogue_choice",
                endpoint="/api/dialogue/choice",
                method="POST",
                payload_template={
                    "conversation_id": "{conversation_id}",
                    "choice_id": "{choice_id}",
                    "character_id": "{character_id}"
                },
                expected_status=200,
                weight=0.3
            ),

            # Social actions
            UserAction(
                action_type="send_message",
                endpoint="/api/chat/message",
                method="POST",
                payload_template={
                    "session_id": "{session_id}",
                    "message": "Hello, this is a test message!",
                    "type": "text"
                },
                expected_status=201,
                weight=0.15
            ),

            UserAction(
                action_type="join_group",
                endpoint="/api/groups/join",
                method="POST",
                payload_template={
                    "group_id": "{group_id}",
                    "character_id": "{character_id}"
                },
                expected_status=200,
                weight=0.1
            ),

            # Content actions
            UserAction(
                action_type="browse_campaigns",
                endpoint="/api/campaigns",
                method="GET",
                payload_template={"page": "{random_page}", "limit": 10},
                expected_status=200,
                weight=0.2
            ),

            UserAction(
                action_type="view_campaign",
                endpoint="/api/campaigns/{campaign_id}",
                method="GET",
                payload_template={},
                expected_status=200,
                weight=0.15
            ),

            # World state actions
            UserAction(
                action_type="get_world_state",
                endpoint="/api/world/state",
                method="GET",
                payload_template={"session_id": "{session_id}"},
                expected_status=200,
                weight=0.1
            ),

            UserAction(
                action_type="update_world_state",
                endpoint="/api/world/update",
                method="POST",
                payload_template={
                    "session_id": "{session_id}",
                    "changes": {"location": "new_area"}
                },
                expected_status=200,
                weight=0.05
            )
        ]

    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=25,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.config.headers
        )

    async def _create_user(self, persona: UserPersona) -> Dict[str, Any]:
        """Create a new user"""
        user_data = {
            "user_id": str(uuid.uuid4()),
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "persona": persona.name,
            "experience_level": persona.experience_level,
            "device_type": persona.device_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Register user
        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/users/register",
                json=user_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    user_data.update(await response.json())
                    await self.metrics_collector.record_request(
                        "user_register", response_time, response.status, True
                    )
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "user_register",
                        "status": response.status,
                        "error": error_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "user_register", response_time, response.status, False
                    )

                self.total_requests += 1

        except Exception as e:
            self.errors.append({
                "endpoint": "user_register",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1

        # Add persona-specific data
        user_data["persona_data"] = {
            "session_duration": persona.session_duration,
            "actions_per_session": persona.actions_per_session,
            "preferred_features": persona.preferred_features,
            "network_speed": persona.network_speed
        }

        return user_data

    def _get_random_action(self, persona: UserPersona) -> UserAction:
        """Get a random action weighted by persona preferences"""
        # Filter actions by persona preferences
        preferred_actions = [
            action for action in self.user_actions
            if any(pref in action.action_type for pref in persona.preferred_features)
        ]

        # If no preferred actions, use all actions
        if not preferred_actions:
            preferred_actions = self.user_actions

        # Weight selection by action weight and persona match
        weights = []
        for action in preferred_actions:
            base_weight = action.weight
            # Boost weight for preferred features
            if any(pref in action.action_type for pref in persona.preferred_features):
                base_weight *= 2.0
            weights.append(base_weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        return random.choices(preferred_actions, weights=weights)[0]

    def _prepare_payload(self, action: UserAction, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload with dynamic data"""
        payload = action.payload_template.copy()

        # Replace placeholders
        for key, value in payload.items():
            if isinstance(value, str):
                # User-specific placeholders
                value = value.replace("{user_id}", user_data["user_id"])
                value = value.replace("{username}", user_data["username"])

                # Random placeholders
                if "{random}" in value:
                    value = value.replace("{random}", str(uuid.uuid4().hex[:8]))
                if "{random_class}" in value:
                    value = value.replace("{random_class}", random.choice(["fighter", "wizard", "rogue", "cleric"]))
                if "{random_race}" in value:
                    value = value.replace("{random_race}", random.choice(["human", "elf", "dwarf", "halfling"]))
                if "{random_background}" in value:
                    value = value.replace("{random_background}", random.choice(["soldier", "scholar", "merchant", "noble"]))
                if "{random_level}" in value:
                    value = value.replace("{random_level}", str(random.randint(1, 20)))
                if "{random_xp}" in value:
                    value = value.replace("{random_xp}", str(random.randint(0, 10000)))
                if "{random_health}" in value:
                    value = value.replace("{random_health}", str(random.randint(1, 100)))
                if "{combat_action}" in value:
                    value = value.replace("{combat_action}", random.choice(["attack", "defend", "spell", "skill"]))
                if "{random_dice}" in value:
                    value = value.replace("{random_dice}", str(random.randint(1, 20)))
                if "{random_page}" in value:
                    value = value.replace("{random_page}", str(random.randint(1, 10)))

                # ID placeholders (simulate existing data)
                if "{character_id}" in value:
                    user_data.setdefault("character_id", str(uuid.uuid4()))
                    value = value.replace("{character_id}", user_data["character_id"])
                if "{campaign_id}" in value:
                    user_data.setdefault("campaign_id", str(uuid.uuid4()))
                    value = value.replace("{campaign_id}", user_data["campaign_id"])
                if "{session_id}" in value:
                    user_data.setdefault("session_id", str(uuid.uuid4()))
                    value = value.replace("{session_id}", user_data["session_id"])
                if "{conversation_id}" in value:
                    user_data.setdefault("conversation_id", str(uuid.uuid4()))
                    value = value.replace("{conversation_id}", user_data["conversation_id"])
                if "{choice_id}" in value:
                    value = value.replace("{choice_id}", str(random.randint(1, 5)))
                if "{target_id}" in value:
                    value = value.replace("{target_id}", str(uuid.uuid4()))
                if "{player_id}" in value:
                    value = value.replace("{player_id}", user_data["user_id"])
                if "{group_id}" in value:
                    user_data.setdefault("group_id", str(uuid.uuid4()))
                    value = value.replace("{group_id}", user_data["group_id"])

                payload[key] = value

        return payload

    async def _execute_action(self, action: UserAction, user_data: Dict[str, Any]) -> bool:
        """Execute a user action"""
        payload = self._prepare_payload(action, user_data)

        try:
            start_time = time.time()

            # Prepare request
            url = f"{self.config.target_url}{action.endpoint}"
            if action.method == "GET":
                # For GET, put payload in query params
                params = {k: v for k, v in payload.items() if k != "page"}
                async with self.session.get(url, params=params) as response:
                    response_time = (time.time() - start_time) * 1000
            else:
                async with self.session.request(action.method, url, json=payload) as response:
                    response_time = (time.time() - start_time) * 1000

            self.request_times.append(response_time)

            if response.status == action.expected_status:
                self.successful_requests += 1
                await self.metrics_collector.record_request(
                    action.action_type, response_time, response.status, True
                )
                return True
            else:
                error_data = await response.text()
                self.errors.append({
                    "endpoint": action.endpoint,
                    "action": action.action_type,
                    "status": response.status,
                    "expected": action.expected_status,
                    "error": error_data,
                    "user_id": user_data["user_id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await self.metrics_collector.record_request(
                    action.action_type, response_time, response.status, False
                )
                return False

        except Exception as e:
            self.errors.append({
                "endpoint": action.endpoint,
                "action": action.action_type,
                "error": str(e),
                "user_id": user_data["user_id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return False

        finally:
            self.total_requests += 1

    async def _simulate_user_session(self, user_data: Dict[str, Any], persona: UserPersona):
        """Simulate a complete user session"""
        session_start = time.time()
        session_duration = persona.session_duration * 60  # Convert to seconds
        actions_completed = 0

        # Login
        await self._execute_action(
            next(a for a in self.user_actions if a.action_type == "login"),
            user_data
        )

        # Main session loop
        while (time.time() - session_start < session_duration and
               actions_completed < persona.actions_per_session):

            # Select and execute action
            action = self._get_random_action(persona)
            success = await self._execute_action(action, user_data)

            if success:
                actions_completed += 1

            # Think time based on experience level
            base_think_time = {
                "beginner": 3.0,
                "intermediate": 2.0,
                "advanced": 1.0
            }.get(persona.experience_level, 2.0)

            # Adjust for network speed
            network_multiplier = {
                "slow": 1.5,
                "average": 1.0,
                "fast": 0.8
            }.get(persona.network_speed, 1.0)

            think_time = base_think_time * network_multiplier * random.uniform(0.5, 1.5)
            await asyncio.sleep(think_time)

        # Logout
        await self._execute_action(
            next(a for a in self.user_actions if a.action_type == "logout"),
            user_data
        )

        logger.info(f"User {user_data['user_id']} completed {actions_completed} actions")

    async def _setup_users(self):
        """Setup all users for the test"""
        for i in range(self.config.users):
            persona = self.personas[i % len(self.personas)]
            user = await self._create_user(persona)
            self.users.append(user)

            # Stagger user creation
            if i % 5 == 0:
                await asyncio.sleep(0.1)

        logger.info(f"Created {len(self.users)} users")

    async def execute(self) -> TestResult:
        """Execute the user journey load test"""
        logger.info(f"Starting user journey simulation with {self.config.users} users")

        try:
            await self._initialize_session()
            await self._setup_users()

            if not self.users:
                raise RuntimeError("No users were successfully created")

            # Run user sessions concurrently
            user_tasks = []
            for user in self.users:
                persona = next(p for p in self.personas if p.name == user["persona"])
                task = asyncio.create_task(self._simulate_user_session(user, persona))
                user_tasks.append(task)

            # Wait for all users to complete their sessions
            await asyncio.gather(*user_tasks, return_exceptions=True)

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
                scenario="user_journey",
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
        avg_response_size = 1536  # bytes
        throughput = (requests_per_second * avg_response_size) / (1024 * 1024)  # MB/s

        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 100

        # Additional metrics
        metrics = {
            "users_simulated": len(self.users),
            "persona_distribution": {
                persona.name: sum(1 for user in self.users if user["persona"] == persona.name)
                for persona in self.personas
            },
            "device_distribution": {
                device: sum(1 for user in self.users if user["device_type"] == device)
                for device in set(user["device_type"] for user in self.users)
            },
            "experience_distribution": {
                level: sum(1 for user in self.users if user["experience_level"] == level)
                for level in set(user["experience_level"] for user in self.users)
            },
            "avg_actions_per_user": successful_requests / len(self.users) if self.users else 0,
            "action_type_distribution": {
                action.action_type: len([e for e in self.errors if e.get("action") == action.action_type])
                for action in self.user_actions
            }
        }

        return TestResult(
            test_name=self.config.name,
            scenario="user_journey",
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