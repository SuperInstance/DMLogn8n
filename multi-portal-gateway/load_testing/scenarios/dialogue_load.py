#!/usr/bin/env python3
"""
Dialogue Load Test Scenario
Tests the dialogue system under high-conversation load
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
class DialogueCharacter:
    """Represents a character in dialogue"""
    character_id: str
    name: str
    personality: str
    background: str
    relationship_level: int  # 1-10
    dialogue_patterns: List[str]
    response_complexity: int  # 1-10

@dataclass
class DialogueSession:
    """Represents a dialogue session"""
    session_id: str
    participants: List[str]
    topic: str
    context: Dict[str, Any]
    created_at: datetime
    messages: List[Dict[str, Any]]
    status: str

class DialogueLoadScenario:
    """Tests the dialogue system with high conversation load"""

    def __init__(self, config: LoadTestConfig, metrics_collector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.total_requests = 0
        self.successful_requests = 0
        self.dialogue_sessions: Dict[str, DialogueSession] = {}
        self.characters: List[DialogueCharacter] = []

        # Dialogue topics
        self.dialogue_topics = [
            "quest_discussion", "personal_story", "world_lore", "combat_strategy",
            "character_relationship", "mystery_investigation", "merchant_negotiation",
            "tavern_social", "campfire_stories", "political_discussion", "magical_research",
            "religious_debate", "personal_conflict", "group_planning", "emergency_situation"
        ]

        # Personality types
        self.personalities = [
            "friendly", "aggressive", "mysterious", "scholarly", "humorous",
            "serious", "cunning", "noble", "rugged", "eccentric"
        ]

        # Dialogue patterns
        self.dialogue_patterns = [
            "question_response", "statement_reaction", "emotion_expression",
            "information_sharing", "request_negotiation", "conflict_resolution",
            "storytelling", "joke_telling", "advice_giving", "compliment_exchanging"
        ]

    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=150,
            limit_per_host=75,
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

    def _generate_character(self) -> DialogueCharacter:
        """Generate a dialogue character"""
        character_id = str(uuid.uuid4())
        personality = random.choice(self.personalities)
        background = random.choice([
            "noble", "merchant", "scholar", "soldier", "artisan", "farmer",
            "mage", "cleric", "rogue", "bard", "wanderer", "mystic"
        ])

        # Select dialogue patterns based on personality
        personality_patterns = {
            "friendly": ["question_response", "compliment_exchanging", "emotion_expression"],
            "aggressive": ["conflict_resolution", "request_negotiation", "statement_reaction"],
            "mysterious": ["storytelling", "information_sharing", "question_response"],
            "scholarly": ["information_sharing", "advice_giving", "question_response"],
            "humorous": ["joke_telling", "emotion_expression", "storytelling"],
            "serious": ["conflict_resolution", "advice_giving", "statement_reaction"],
            "cunning": ["request_negotiation", "information_sharing", "question_response"],
            "noble": ["advice_giving", "storytelling", "compliment_exchanging"],
            "rugged": ["statement_reaction", "information_sharing", "conflict_resolution"],
            "eccentric": ["storytelling", "joke_telling", "emotion_expression"]
        }

        patterns = personality_patterns.get(personality, self.dialogue_patterns[:5])

        return DialogueCharacter(
            character_id=character_id,
            name=f"{background.title()}_{character_id[:8]}",
            personality=personality,
            background=background,
            relationship_level=random.randint(1, 10),
            dialogue_patterns=patterns,
            response_complexity=random.randint(3, 9)
        )

    async def _create_dialogue_session(self, participants: List[DialogueCharacter]) -> str:
        """Create a new dialogue session"""
        session_id = str(uuid.uuid4())
        topic = random.choice(self.dialogue_topics)

        session_data = {
            "session_id": session_id,
            "participants": [c.character_id for c in participants],
            "topic": topic,
            "context": {
                "location": random.choice(["tavern", "castle", "forest", "dungeon", "market", "temple"]),
                "time_of_day": random.choice(["morning", "afternoon", "evening", "night"]),
                "weather": random.choice(["clear", "rainy", "cloudy", "stormy"]),
                "urgency": random.choice(["casual", "important", "urgent"])
            },
            "session_type": random.choice(["conversation", "negotiation", "interrogation", "social"]),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/dialogue/session",
                json=session_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "dialogue_create_session", response_time, response.status, True
                    )
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "dialogue_create_session",
                        "status": response.status,
                        "error": error_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "dialogue_create_session", response_time, response.status, False
                    )

                self.total_requests += 1

        except Exception as e:
            self.errors.append({
                "endpoint": "dialogue_create_session",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            logger.error(f"Failed to create dialogue session: {e}")

        # Store session
        self.dialogue_sessions[session_id] = DialogueSession(
            session_id=session_id,
            participants=[c.character_id for c in participants],
            topic=topic,
            context=session_data["context"],
            created_at=datetime.now(timezone.utc),
            messages=[],
            status="active"
        )

        return session_id

    async def _send_dialogue_message(self, session_id: str, character: DialogueCharacter, message: str) -> Optional[Dict[str, Any]]:
        """Send a dialogue message"""
        message_data = {
            "session_id": session_id,
            "character_id": character.character_id,
            "message": message,
            "message_type": random.choice(["statement", "question", "emotion", "action"]),
            "tone": random.choice(["friendly", "neutral", "hostile", "curious", "concerned"]),
            "language": "common",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "complexity": character.response_complexity,
                "personality": character.personality,
                "relationship_level": character.relationship_level
            }
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/dialogue/message",
                json=message_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "dialogue_send_message", response_time, response.status, True
                    )

                    # Store message in session
                    if session_id in self.dialogue_sessions:
                        self.dialogue_sessions[session_id].messages.append({
                            "character_id": character.character_id,
                            "message": message,
                            "timestamp": message_data["timestamp"],
                            "response_time": response_time
                        })

                    return result
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "dialogue_send_message",
                        "status": response.status,
                        "error": error_data,
                        "character_id": character.character_id,
                        "session_id": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "dialogue_send_message", response_time, response.status, False
                    )

                self.total_requests += 1
                return None

        except Exception as e:
            self.errors.append({
                "endpoint": "dialogue_send_message",
                "error": str(e),
                "character_id": character.character_id,
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            return None

    async def _get_dialogue_response(self, session_id: str, character: DialogueCharacter) -> Optional[str]:
        """Get an AI-generated dialogue response"""
        request_data = {
            "session_id": session_id,
            "character_id": character.character_id,
            "context": {
                "personality": character.personality,
                "background": character.background,
                "relationship_level": character.relationship_level,
                "complexity": character.response_complexity,
                "recent_messages": self.dialogue_sessions[session_id].messages[-3:] if session_id in self.dialogue_sessions else []
            },
            "prompt_type": random.choice(["response", "initiation", "reaction", "follow_up"])
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/dialogue/generate",
                json=request_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 200:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "dialogue_generate_response", response_time, response.status, True
                    )
                    return result.get("response", "")
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "dialogue_generate_response",
                        "status": response.status,
                        "error": error_data,
                        "character_id": character.character_id,
                        "session_id": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "dialogue_generate_response", response_time, response.status, False
                    )

                self.total_requests += 1
                return None

        except Exception as e:
            self.errors.append({
                "endpoint": "dialogue_generate_response",
                "error": str(e),
                "character_id": character.character_id,
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            return None

    def _generate_message_content(self, character: DialogueCharacter, context: Dict[str, Any]) -> str:
        """Generate realistic message content based on character and context"""
        message_templates = {
            "friendly": [
                "That's an interesting point! What do you think about {topic}?",
                "I really enjoy our conversations. Tell me more about {topic}.",
                "You always have such fascinating insights!",
                "I feel like we're becoming good friends.",
                "This place reminds me of a story I once heard..."
            ],
            "aggressive": [
                "What's your point? Get to the matter at hand.",
                "I don't have time for pleasantries.",
                "Are you questioning my authority?",
                "Let's settle this like adults - no games.",
                "I demand answers, not more questions."
            ],
            "mysterious": [
                "There are things you don't understand...",
                "The truth is often hidden in plain sight.",
                "I could tell you, but then...",
                "Some doors are better left unopened.",
                "What if nothing is as it seems?"
            ],
            "scholarly": [
                "According to ancient texts on {topic}...",
                "The historical context suggests...",
                "Let me consult my notes on this matter.",
                "Fascinating! This requires further study.",
                "The implications are quite profound."
            ],
            "humorous": [
                "Well, that's a funny story! Speaking of which...",
                "Have you heard the one about the {topic}?",
                "Life's too short to be serious all the time!",
                "I've got a joke that might lighten the mood.",
                "You know what they say about {topic}..."
            ]
        }

        templates = message_templates.get(character.personality, message_templates["friendly"])
        template = random.choice(templates)

        # Replace placeholders
        if "{topic}" in template:
            template = template.replace("{topic}", context.get("topic", "this matter"))

        # Add personality-specific elements
        if character.background == "mage":
            template += " By the way, have you studied any magic lately?"
        elif character.background == "soldier":
            template += " This reminds me of my time in the army."
        elif character.background == "merchant":
            template += " Speaking of which, have you seen the market prices lately?"

        return template

    async def _run_dialogue_conversation(self, session_id: str, participants: List[DialogueCharacter]):
        """Run a complete dialogue conversation"""
        session = self.dialogue_sessions[session_id]
        start_time = time.time()
        current_speaker_index = 0
        message_count = 0
        max_messages = random.randint(10, 30)

        # Start conversation with first speaker
        while (time.time() - start_time < self.config.duration and
               message_count < max_messages):

            current_speaker = participants[current_speaker_index]

            # Generate and send message
            if random.random() < 0.7:  # 70% chance to generate new content
                response = await self._get_dialogue_response(session_id, current_speaker)
                if response:
                    await self._send_dialogue_message(session_id, current_speaker, response)
                    message_count += 1
            else:
                # Use pre-generated message
                message = self._generate_message_content(current_speaker, session.context)
                await self._send_dialogue_message(session_id, current_speaker, message)
                message_count += 1

            # Rotate speakers with some randomness
            if random.random() < 0.8:  # 80% chance to move to next speaker
                current_speaker_index = (current_speaker_index + 1) % len(participants)
            else:
                # Random speaker
                current_speaker_index = random.randint(0, len(participants) - 1)

            # Delay between messages based on complexity
            delay = 1.0 + (current_speaker.response_complexity * 0.2)
            delay *= random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)

        # Update session status
        session.status = "completed"
        session.messages_count = message_count

        logger.info(f"Dialogue session {session_id} completed with {message_count} messages")

    async def _setup_dialogue_sessions(self):
        """Setup dialogue sessions"""
        num_sessions = min(self.config.users // 2, 15)  # 2 participants per session minimum
        characters_per_session = random.randint(2, 5)

        for i in range(num_sessions):
            # Generate participants for this session
            participants = []
            for j in range(characters_per_session):
                character = self._generate_character()
                self.characters.append(character)
                participants.append(character)

            # Create dialogue session
            session_id = await self._create_dialogue_session(participants)

            # Brief delay between session creation
            await asyncio.sleep(0.1)

        logger.info(f"Created {len(self.dialogue_sessions)} dialogue sessions with {len(self.characters)} characters")

    async def execute(self) -> TestResult:
        """Execute the dialogue load test"""
        logger.info(f"Starting dialogue load test with {self.config.users} simulated users")

        try:
            await self._initialize_session()
            await self._setup_dialogue_sessions()

            if not self.dialogue_sessions:
                raise RuntimeError("No dialogue sessions were created")

            # Run dialogue conversations concurrently
            conversation_tasks = []
            for session_id, session in self.dialogue_sessions.items():
                # Get participants for this session
                participants = [c for c in self.characters if c.character_id in session.participants]
                if participants:
                    task = asyncio.create_task(self._run_dialogue_conversation(session_id, participants))
                    conversation_tasks.append(task)

            # Wait for all conversations to complete
            await asyncio.gather(*conversation_tasks, return_exceptions=True)

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
                scenario="dialogue_load",
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
        avg_response_size = 512  # bytes (dialogue responses are typically text-heavy)
        throughput = (requests_per_second * avg_response_size) / (1024 * 1024)  # MB/s

        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 100

        # Additional dialogue-specific metrics
        total_messages = sum(len(session.messages) for session in self.dialogue_sessions.values())
        avg_messages_per_session = total_messages / len(self.dialogue_sessions) if self.dialogue_sessions else 0
        avg_messages_per_character = total_messages / len(self.characters) if self.characters else 0

        metrics = {
            "dialogue_sessions_simulated": len(self.dialogue_sessions),
            "characters_simulated": len(self.characters),
            "total_messages_exchanged": total_messages,
            "avg_messages_per_session": avg_messages_per_session,
            "avg_messages_per_character": avg_messages_per_character,
            "personality_distribution": {
                personality: sum(1 for c in self.characters if c.personality == personality)
                for personality in set(c.personality for c in self.characters)
            },
            "background_distribution": {
                background: sum(1 for c in self.characters if c.background == background)
                for background in set(c.background for c in self.characters)
            },
            "topic_distribution": {
                topic: sum(1 for s in self.dialogue_sessions.values() if s.topic == topic)
                for topic in set(s.topic for s in self.dialogue_sessions.values())
            },
            "avg_complexity_level": sum(c.response_complexity for c in self.characters) / len(self.characters) if self.characters else 0,
            "completed_sessions": sum(1 for s in self.dialogue_sessions.values() if s.status == "completed"),
            "avg_relationship_level": sum(c.relationship_level for c in self.characters) / len(self.characters) if self.characters else 0
        }

        return TestResult(
            test_name=self.config.name,
            scenario="dialogue_load",
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