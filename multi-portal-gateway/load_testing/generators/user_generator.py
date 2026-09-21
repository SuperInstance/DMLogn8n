#!/usr/bin/env python3
"""
User Behavior Load Generator
Generates realistic user behavior patterns for load testing
"""

import asyncio
import random
import time
import uuid
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import logging
import numpy as np
from faker import Faker

logger = logging.getLogger(__name__)

@dataclass
class UserPersona:
    """Defines a user persona"""
    user_id: str
    username: str
    email: str
    age_group: str
    experience_level: str  # beginner, intermediate, advanced
    device_type: str  # mobile, tablet, desktop
    network_speed: str  # slow, average, fast
    session_duration: int  # minutes
    activity_pattern: str  # regular, burst, evening, weekend
    preferred_features: List[str]
    interaction_speed: float  # interactions per minute
    error_tolerance: float  # 0-1

@dataclass
class UserSession:
    """Defines a user session"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    device_info: Dict[str, Any]
    location: Dict[str, str]
    actions: List[Dict[str, Any]]
    status: str  # active, completed, abandoned, error

@dataclass
class UserAction:
    """Defines a user action"""
    action_id: str
    action_type: str
    endpoint: str
    method: str
    parameters: Dict[str, Any]
    timestamp: datetime
    response_time: float
    success: bool
    error_message: Optional[str]

class UserLoadGenerator:
    """Generates realistic user behavior patterns for testing"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fake = Faker()
        self.personas: List[UserPersona] = []
        self.sessions: Dict[str, UserSession] = []
        self.active_sessions: Dict[str, asyncio.Task] = {}
        self.metrics_callback: Optional[Callable] = None
        self.running = False

        # User behavior data
        self.action_types = self._define_action_types()
        self.user_journeys = self._define_user_journeys()

    def register_metrics_callback(self, callback: Callable):
        """Register callback for metrics collection"""
        self.metrics_callback = callback

    def _define_action_types(self) -> Dict[str, Dict[str, Any]]:
        """Define available user actions with their characteristics"""
        return {
            "login": {
                "endpoint": "/api/auth/login",
                "method": "POST",
                "frequency": 0.1,
                "critical": True,
                "avg_response_time": 500,
                "timeout": 5000
            },
            "logout": {
                "endpoint": "/api/auth/logout",
                "method": "POST",
                "frequency": 0.05,
                "critical": True,
                "avg_response_time": 200,
                "timeout": 2000
            },
            "view_dashboard": {
                "endpoint": "/api/dashboard",
                "method": "GET",
                "frequency": 0.3,
                "critical": False,
                "avg_response_time": 1000,
                "timeout": 5000
            },
            "view_character": {
                "endpoint": "/api/characters/{id}",
                "method": "GET",
                "frequency": 0.25,
                "critical": False,
                "avg_response_time": 800,
                "timeout": 3000
            },
            "create_character": {
                "endpoint": "/api/characters",
                "method": "POST",
                "frequency": 0.15,
                "critical": False,
                "avg_response_time": 1500,
                "timeout": 8000
            },
            "update_character": {
                "endpoint": "/api/characters/{id}",
                "method": "PUT",
                "frequency": 0.2,
                "critical": False,
                "avg_response_time": 1200,
                "timeout": 6000
            },
            "start_combat": {
                "endpoint": "/api/combat/session",
                "method": "POST",
                "frequency": 0.18,
                "critical": False,
                "avg_response_time": 2000,
                "timeout": 10000
            },
            "combat_action": {
                "endpoint": "/api/combat/action",
                "method": "POST",
                "frequency": 0.4,
                "critical": True,
                "avg_response_time": 500,
                "timeout": 3000
            },
            "send_message": {
                "endpoint": "/api/chat/message",
                "method": "POST",
                "frequency": 0.35,
                "critical": False,
                "avg_response_time": 300,
                "timeout": 2000
            },
            "join_session": {
                "endpoint": "/api/sessions/join",
                "method": "POST",
                "frequency": 0.12,
                "critical": True,
                "avg_response_time": 1000,
                "timeout": 5000
            },
            "browse_campaigns": {
                "endpoint": "/api/campaigns",
                "method": "GET",
                "frequency": 0.22,
                "critical": False,
                "avg_response_time": 1200,
                "timeout": 6000
            },
            "dialogue_choice": {
                "endpoint": "/api/dialogue/choice",
                "method": "POST",
                "frequency": 0.38,
                "critical": True,
                "avg_response_time": 600,
                "timeout": 3000
            },
            "view_inventory": {
                "endpoint": "/api/inventory/{id}",
                "method": "GET",
                "frequency": 0.28,
                "critical": False,
                "avg_response_time": 700,
                "timeout": 3000
            },
            "use_item": {
                "endpoint": "/api/inventory/use",
                "method": "POST",
                "frequency": 0.16,
                "critical": False,
                "avg_response_time": 900,
                "timeout": 4000
            },
            "trade_items": {
                "endpoint": "/api/trade/execute",
                "method": "POST",
                "frequency": 0.08,
                "critical": False,
                "avg_response_time": 1800,
                "timeout": 8000
            }
        }

    def _define_user_journeys(self) -> Dict[str, List[str]]:
        """Define typical user journeys"""
        return {
            "new_player": [
                "login", "create_character", "view_character", "start_combat", "combat_action", "logout"
            ],
            "regular_player": [
                "login", "view_dashboard", "view_character", "join_session", "combat_action", "send_message", "logout"
            ],
            "social_player": [
                "login", "view_dashboard", "send_message", "join_session", "dialogue_choice", "send_message", "logout"
            ],
            "explorer": [
                "login", "browse_campaigns", "join_session", "view_character", "dialogue_choice", "view_inventory", "logout"
            ],
            "combat_focused": [
                "login", "view_character", "start_combat", "combat_action", "combat_action", "use_item", "logout"
            ],
            "trader": [
                "login", "view_inventory", "browse_campaigns", "trade_items", "view_inventory", "logout"
            ],
            "story_seeker": [
                "login", "join_session", "dialogue_choice", "dialogue_choice", "send_message", "dialogue_choice", "logout"
            ],
            "power_user": [
                "login", "view_dashboard", "view_character", "start_combat", "combat_action", "dialogue_choice", "use_item", "send_message", "logout"
            ]
        }

    def generate_user_personas(self, count: int) -> List[UserPersona]:
        """Generate diverse user personas"""
        personas = []

        age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
        experience_levels = ["beginner", "intermediate", "advanced"]
        device_types = ["mobile", "tablet", "desktop"]
        network_speeds = ["slow", "average", "fast"]
        activity_patterns = ["regular", "burst", "evening", "weekend"]

        feature_sets = {
            "beginner": ["create_character", "view_character", "start_combat", "dialogue_choice"],
            "intermediate": ["view_dashboard", "combat_action", "send_message", "join_session"],
            "advanced": ["start_combat", "combat_action", "dialogue_choice", "trade_items", "use_item"]
        }

        for i in range(count):
            # Distribute experience levels realistically
            exp_weights = [0.3, 0.5, 0.2]  # 30% beginners, 50% intermediate, 20% advanced
            experience_level = random.choices(experience_levels, weights=exp_weights)[0]

            # Device distribution
            device_weights = [0.4, 0.2, 0.4]  # 40% mobile, 20% tablet, 40% desktop
            device_type = random.choices(device_types, weights=device_weights)[0]

            # Network speed distribution
            network_weights = [0.15, 0.7, 0.15]  # 15% slow, 70% average, 15% fast
            network_speed = random.choices(network_speeds, weights=network_weights)[0]

            # Session duration based on experience and device
            base_duration = {
                "beginner": 30,
                "intermediate": 45,
                "advanced": 60
            }[experience_level]

            device_multiplier = {
                "mobile": 0.7,
                "tablet": 0.9,
                "desktop": 1.2
            }[device_type]

            session_duration = int(base_duration * device_multiplier * random.uniform(0.8, 1.5))

            # Interaction speed based on experience and network
            base_speed = {
                "beginner": 2.0,
                "intermediate": 4.0,
                "advanced": 6.0
            }[experience_level]

            network_multiplier = {
                "slow": 0.6,
                "average": 1.0,
                "fast": 1.3
            }[network_speed]

            interaction_speed = base_speed * network_multiplier * random.uniform(0.8, 1.2)

            # Error tolerance based on experience
            error_tolerance = {
                "beginner": 0.15,
                "intermediate": 0.08,
                "advanced": 0.03
            }[experience_level]

            # Activity pattern
            activity_pattern = random.choice(activity_patterns)

            # Preferred features based on experience
            preferred_features = random.sample(feature_sets[experience_level], k=random.randint(2, 4))

            persona = UserPersona(
                user_id=str(uuid.uuid4()),
                username=self.fake.user_name(),
                email=self.fake.email(),
                age_group=random.choice(age_groups),
                experience_level=experience_level,
                device_type=device_type,
                network_speed=network_speed,
                session_duration=session_duration,
                activity_pattern=activity_pattern,
                preferred_features=preferred_features,
                interaction_speed=interaction_speed,
                error_tolerance=error_tolerance
            )

            personas.append(persona)

        return personas

    def calculate_activity_probability(self, persona: UserPersona, current_time: datetime) -> float:
        """Calculate probability of user activity based on persona and time"""
        base_probability = 0.7  # 70% base activity rate

        # Adjust based on activity pattern
        hour = current_time.hour
        day_of_week = current_time.weekday()

        if persona.activity_pattern == "regular":
            # Regular users are active during typical hours
            if 9 <= hour <= 17 and day_of_week < 5:
                multiplier = 1.2
            elif 18 <= hour <= 22:
                multiplier = 1.0
            else:
                multiplier = 0.5

        elif persona.activity_pattern == "evening":
            # Evening users are more active in the evening
            if 18 <= hour <= 23:
                multiplier = 1.5
            else:
                multiplier = 0.3

        elif persona.activity_pattern == "weekend":
            # Weekend users are more active on weekends
            if day_of_week >= 5:
                multiplier = 1.3
            else:
                multiplier = 0.6

        else:  # burst
            # Burst users have random activity spikes
            if random.random() < 0.1:  # 10% chance of burst
                multiplier = 2.0
            else:
                multiplier = 0.4

        # Adjust based on experience level
        experience_multiplier = {
            "beginner": 0.8,
            "intermediate": 1.0,
            "advanced": 1.2
        }[persona.experience_level]

        return min(1.0, base_probability * multiplier * experience_multiplier)

    def select_action(self, persona: UserPersona, journey: List[str]) -> str:
        """Select next action based on persona preferences and journey"""
        # Weight actions by persona preferences
        preferred_actions = set(persona.preferred_features)
        available_actions = set(journey)

        # Filter to preferred actions that are available
        preferred_available = list(preferred_actions & available_actions)

        if preferred_available and random.random() < 0.7:  # 70% chance to choose preferred
            return random.choice(preferred_available)
        elif available_actions:
            return random.choice(list(available_actions))
        else:
            # Fallback to random action
            return random.choice(list(self.action_types.keys()))

    async def execute_user_action(self, persona: UserPersona, action_type: str, session_id: str) -> UserAction:
        """Execute a single user action"""
        start_time = time.time()
        action_id = str(uuid.uuid4())

        action_info = self.action_types.get(action_type, self.action_types["view_dashboard"])

        # Simulate network delay based on network speed
        network_delay = {
            "slow": random.uniform(1.5, 3.0),
            "average": random.uniform(0.5, 1.5),
            "fast": random.uniform(0.1, 0.5)
        }[persona.network_speed]

        # Simulate processing time based on action
        processing_time = random.gauss(action_info["avg_response_time"] / 1000, 0.2)
        processing_time = max(0.1, processing_time)  # Ensure positive

        total_time = network_delay + processing_time
        await asyncio.sleep(total_time)

        # Determine success based on error tolerance and action criticality
        error_chance = persona.error_tolerance
        if action_info["critical"]:
            error_chance *= 0.5  # Critical actions have lower error chance

        success = random.random() > error_chance

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        action = UserAction(
            action_id=action_id,
            action_type=action_type,
            endpoint=action_info["endpoint"],
            method=action_info["method"],
            parameters=self._generate_action_parameters(action_type, persona),
            timestamp=datetime.now(timezone.utc),
            response_time=response_time,
            success=success,
            error_message=None if success else random.choice([
                "Network timeout", "Server error", "Invalid input", "Permission denied"
            ])
        )

        # Record metrics
        if self.metrics_callback:
            status_code = 200 if success else random.choice([400, 401, 404, 500])
            await self.metrics_callback("user_action", response_time, status_code, success)

        return action

    def _generate_action_parameters(self, action_type: str, persona: UserPersona) -> Dict[str, Any]:
        """Generate realistic parameters for different action types"""
        base_params = {
            "user_id": persona.user_id,
            "device_type": persona.device_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if action_type == "login":
            base_params.update({
                "username": persona.username,
                "password": "password123",
                "remember_me": random.choice([True, False])
            })

        elif action_type == "create_character":
            base_params.update({
                "name": f"Character_{self.fake.first_name()}",
                "class": random.choice(["fighter", "wizard", "rogue", "cleric"]),
                "race": random.choice(["human", "elf", "dwarf", "halfling"]),
                "background": random.choice(["soldier", "scholar", "merchant", "noble"])
            })

        elif action_type in ["view_character", "view_inventory"]:
            base_params["character_id"] = str(uuid.uuid4())

        elif action_type == "combat_action":
            base_params.update({
                "action_type": random.choice(["attack", "defend", "spell", "skill"]),
                "target_id": str(uuid.uuid4()),
                "dice_roll": random.randint(1, 20)
            })

        elif action_type == "send_message":
            base_params.update({
                "message": self.fake.sentence(),
                "channel": random.choice(["general", "combat", "dialogue"]),
                "session_id": str(uuid.uuid4())
            })

        elif action_type == "dialogue_choice":
            base_params.update({
                "choice_id": random.randint(1, 5),
                "conversation_id": str(uuid.uuid4()),
                "character_id": str(uuid.uuid4())
            })

        elif action_type == "use_item":
            base_params.update({
                "item_id": str(uuid.uuid4()),
                "character_id": str(uuid.uuid4()),
                "target_id": str(uuid.uuid4())
            })

        return base_params

    async def user_session_worker(self, persona: UserPersona, session_duration: int):
        """Worker function for a single user session"""
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=persona.user_id,
            start_time=start_time,
            end_time=None,
            device_info={
                "type": persona.device_type,
                "user_agent": self.fake.user_agent(),
                "screen_resolution": f"{random.choice([1920, 1366, 1440])}x{random.choice([1080, 768, 900])}"
            },
            location={
                "country": self.fake.country(),
                "city": self.fake.city(),
                "ip_address": self.fake.ipv4()
            },
            actions=[],
            status="active"
        )

        self.sessions.append(session)

        # Select user journey based on experience
        journey_options = list(self.user_journeys.keys())
        journey = random.choice(journey_options)

        # Run session
        session_end_time = start_time + timedelta(seconds=session_duration)
        actions_completed = 0
        max_actions = int(persona.interaction_speed * session_duration / 60)

        while datetime.now(timezone.utc) < session_end_time and actions_completed < max_actions:
            # Check if user should be active
            if random.random() < self.calculate_activity_probability(persona, datetime.now(timezone.utc)):
                # Select and execute action
                action_type = self.select_action(persona, self.user_journeys[journey])
                action = await self.execute_user_action(persona, action_type, session_id)

                session.actions.append(action)
                actions_completed += 1

                # Think time based on interaction speed
                think_time = 60.0 / persona.interaction_speed  # Convert to seconds
                think_time *= random.uniform(0.5, 1.5)  # Add variability
                await asyncio.sleep(think_time)
            else:
                # User is idle
                await asyncio.sleep(random.uniform(5, 15))

        # Complete session
        session.end_time = datetime.now(timezone.utc)
        session.status = "completed"

        logger.info(f"User {persona.user_id} completed session with {actions_completed} actions")

    async def start_load_generation(self, num_users: int, duration: int):
        """Start generating load from multiple users"""
        logger.info(f"Starting user load generation with {num_users} users for {duration} seconds")

        # Generate user personas
        self.personas = self.generate_user_personas(num_users)
        self.running = True

        # Stagger user session starts
        start_delays = [random.uniform(0, min(60, duration / 4)) for _ in range(num_users)]
        start_delays.sort()

        for i, persona in enumerate(self.personas):
            if not self.running:
                break

            # Calculate individual session duration
            session_duration = min(persona.session_duration * 60, duration - int(start_delays[i]))

            if session_duration > 30:  # Only start sessions longer than 30 seconds
                # Start session after delay
                task = asyncio.create_task(
                    self._delayed_session_start(start_delays[i], persona, session_duration)
                )
                self.active_sessions[persona.user_id] = task

        # Wait for all sessions to complete
        try:
            await asyncio.gather(*self.active_sessions.values(), return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in user load generation: {e}")

        self.running = False
        logger.info("User load generation completed")

    async def _delayed_session_start(self, delay: float, persona: UserPersona, duration: int):
        """Start a user session after a delay"""
        await asyncio.sleep(delay)
        if self.running:
            await self.user_session_worker(persona, duration)

    async def stop_load_generation(self):
        """Stop load generation"""
        logger.info("Stopping user load generation")
        self.running = False

        # Cancel all active sessions
        for task in self.active_sessions.values():
            task.cancel()

        # Wait for tasks to complete cancellation
        try:
            await asyncio.gather(*self.active_sessions.values(), return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping user sessions: {e}")

        self.active_sessions.clear()

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated users and sessions"""
        if not self.personas:
            return {}

        stats = {
            "total_users": len(self.personas),
            "total_sessions": len(self.sessions),
            "completed_sessions": len([s for s in self.sessions if s.status == "completed"]),
            "age_distribution": {},
            "experience_distribution": {},
            "device_distribution": {},
            "network_distribution": {},
            "activity_patterns": {},
            "avg_session_duration": 0,
            "total_actions": 0,
            "avg_actions_per_session": 0,
            "success_rate": 0
        }

        total_duration = 0
        total_actions = 0
        successful_actions = 0

        for persona in self.personas:
            # Distribution statistics
            stats["age_distribution"][persona.age_group] = stats["age_distribution"].get(persona.age_group, 0) + 1
            stats["experience_distribution"][persona.experience_level] = stats["experience_distribution"].get(persona.experience_level, 0) + 1
            stats["device_distribution"][persona.device_type] = stats["device_distribution"].get(persona.device_type, 0) + 1
            stats["network_distribution"][persona.network_speed] = stats["network_distribution"].get(persona.network_speed, 0) + 1
            stats["activity_patterns"][persona.activity_pattern] = stats["activity_patterns"].get(persona.activity_pattern, 0) + 1

        for session in self.sessions:
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                total_duration += duration

            session_actions = len(session.actions)
            total_actions += session_actions

            for action in session.actions:
                if action.success:
                    successful_actions += 1

        # Calculate averages
        completed_sessions = len([s for s in self.sessions if s.status == "completed"])
        if completed_sessions > 0:
            stats["avg_session_duration"] = total_duration / completed_sessions
            stats["avg_actions_per_session"] = total_actions / completed_sessions

        stats["total_actions"] = total_actions
        stats["success_rate"] = (successful_actions / total_actions * 100) if total_actions > 0 else 0

        return stats

    def export_user_data(self, filename: str):
        """Export user data to file"""
        personas_data = [asdict(persona) for persona in self.personas]
        sessions_data = []
        for session in self.sessions:
            session_dict = asdict(session)
            session_dict["actions"] = [asdict(action) for action in session.actions]
            sessions_data.append(session_dict)

        export_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_users": len(self.personas),
            "total_sessions": len(self.sessions),
            "user_personas": personas_data,
            "user_sessions": sessions_data,
            "statistics": self.get_user_statistics()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"User data exported to {filename}")

# Example usage and test functions
async def test_user_generator():
    """Test the user load generator"""
    config = {
        "target_url": "http://localhost:8000",
        "timeout": 30
    }

    generator = UserLoadGenerator(config)

    # Generate test users
    personas = generator.generate_user_personas(10)
    print(f"Generated {len(personas)} user personas")

    # Print statistics
    stats = generator.get_user_statistics()
    print("\nUser Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Export user data
    generator.export_user_data("test_user_personas.json")

    # Start load generation for a short test
    print("\nStarting 15-second load generation test...")
    await generator.start_load_generation(5, 15)

if __name__ == "__main__":
    asyncio.run(test_user_generator())