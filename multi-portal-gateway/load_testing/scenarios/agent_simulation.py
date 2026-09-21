#!/usr/bin/env python3
"""
Agent Simulation Load Test Scenario
Simulates multiple AI agents interacting with the DMLogn8n platform
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
class AgentBehavior:
    """Defines agent behavior patterns"""
    agent_type: str
    personality: str
    response_patterns: List[str]
    action_frequency: float  # actions per second
    complexity_level: int  # 1-10
    memory_size: int  # MB
    interaction_types: List[str]

class AgentSimulationScenario:
    """Simulates AI agent behavior under load"""

    def __init__(self, config: LoadTestConfig, metrics_collector):
        self.config = config
        self.metrics_collector = metrics_collector
        self.agents: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.total_requests = 0
        self.successful_requests = 0

        # Agent behaviors
        self.behaviors = self._generate_agent_behaviors()

    def _generate_agent_behaviors(self) -> List[AgentBehavior]:
        """Generate diverse agent behaviors"""
        behaviors = []

        # DM Assistant Agent
        behaviors.append(AgentBehavior(
            agent_type="dm_assistant",
            personality="strategic_thinker",
            response_patterns=["analyze_situation", "suggest_action", "create_narrative"],
            action_frequency=0.5,
            complexity_level=8,
            memory_size=512,
            interaction_types=["combat_analysis", "story_generation", "player_guidance"]
        ))

        # NPC Agent
        behaviors.append(AgentBehavior(
            agent_type="npc",
            personality="dynamic_character",
            response_patterns=["dialogue_response", "emotion_expression", "memory_recall"],
            action_frequency=2.0,
            complexity_level=6,
            memory_size=256,
            interaction_types=["conversation", "relationship_building", "quest_interaction"]
        ))

        # Combat Agent
        behaviors.append(AgentBehavior(
            agent_type="combat_agent",
            personality="tactical_calculator",
            response_patterns=["calculate_damage", "defend_action", "coordinate_team"],
            action_frequency=3.0,
            complexity_level=7,
            memory_size=128,
            interaction_types=["combat_turn", "damage_calculation", "status_effect"]
        ))

        # World State Agent
        behaviors.append(AgentBehavior(
            agent_type="world_state",
            personality="system_manager",
            response_patterns=["update_state", "track_events", "maintain_consistency"],
            action_frequency=1.0,
            complexity_level=9,
            memory_size=1024,
            interaction_types=["state_sync", "event_logging", "consistency_check"]
        ))

        return behaviors

    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=50,  # Per-host connection limit
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.config.headers
        )

    async def _register_agent(self, behavior: AgentBehavior) -> Dict[str, Any]:
        """Register an agent with the platform"""
        agent_data = {
            "agent_id": str(uuid.uuid4()),
            "agent_type": behavior.agent_type,
            "personality": behavior.personality,
            "capabilities": behavior.interaction_types,
            "memory_size": behavior.memory_size,
            "complexity_level": behavior.complexity_level,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/agents/register",
                json=agent_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 201:
                    self.successful_requests += 1
                    agent_data.update(await response.json())
                    await self.metrics_collector.record_request(
                        "agent_register", response_time, response.status, True
                    )
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "agent_register",
                        "status": response.status,
                        "error": error_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "agent_register", response_time, response.status, False
                    )

                self.total_requests += 1
                return agent_data

        except Exception as e:
            self.errors.append({
                "endpoint": "agent_register",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            logger.error(f"Failed to register agent: {e}")
            return agent_data

    async def _agent_think(self, agent: Dict[str, Any], behavior: AgentBehavior):
        """Simulate agent thinking process"""
        think_data = {
            "agent_id": agent["agent_id"],
            "context": {
                "current_situation": "combat_encounter",
                "participants": ["player1", "npc1", "npc2"],
                "environment": "dungeon_chamber"
            },
            "complexity_level": behavior.complexity_level,
            "memory_tokens": behavior.memory_size * 1024 // 4  # Rough token estimation
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/agents/think",
                json=think_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 200:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "agent_think", response_time, response.status, True
                    )
                    return result
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "agent_think",
                        "status": response.status,
                        "error": error_data,
                        "agent_id": agent["agent_id"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "agent_think", response_time, response.status, False
                    )

                self.total_requests += 1
                return None

        except Exception as e:
            self.errors.append({
                "endpoint": "agent_think",
                "error": str(e),
                "agent_id": agent["agent_id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            logger.error(f"Agent thinking failed: {e}")
            return None

    async def _agent_act(self, agent: Dict[str, Any], behavior: AgentBehavior):
        """Simulate agent taking action"""
        action_types = behavior.interaction_types
        action_type = random.choice(action_types)

        action_data = {
            "agent_id": agent["agent_id"],
            "action_type": action_type,
            "parameters": self._generate_action_parameters(action_type),
            "priority": random.randint(1, 10)
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/agents/act",
                json=action_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 200:
                    self.successful_requests += 1
                    result = await response.json()
                    await self.metrics_collector.record_request(
                        "agent_act", response_time, response.status, True
                    )
                    return result
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "agent_act",
                        "status": response.status,
                        "error": error_data,
                        "agent_id": agent["agent_id"],
                        "action_type": action_type,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "agent_act", response_time, response.status, False
                    )

                self.total_requests += 1
                return None

        except Exception as e:
            self.errors.append({
                "endpoint": "agent_act",
                "error": str(e),
                "agent_id": agent["agent_id"],
                "action_type": action_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1
            logger.error(f"Agent action failed: {e}")
            return None

    def _generate_action_parameters(self, action_type: str) -> Dict[str, Any]:
        """Generate realistic action parameters"""
        parameter_templates = {
            "combat_turn": {
                "target": random.choice(["player1", "npc1", "npc2"]),
                "attack_type": random.choice(["melee", "ranged", "magic"]),
                "damage_mod": random.uniform(0.8, 1.2)
            },
            "conversation": {
                "participant": random.choice(["player1", "npc1"]),
                "topic": random.choice(["quest", "lore", "personal"]),
                "tone": random.choice(["friendly", "neutral", "hostile"])
            },
            "story_generation": {
                "theme": random.choice(["heroism", "mystery", "conflict"]),
                "length": random.randint(100, 500),
                "style": random.choice(["dramatic", "narrative", "descriptive"])
            },
            "state_sync": {
                "components": random.sample(["combat", "inventory", "dialogue", "world"], k=2),
                "priority": random.randint(1, 5)
            }
        }

        return parameter_templates.get(action_type, {"custom": True})

    async def _agent_communicate(self, agent1: Dict[str, Any], agent2: Dict[str, Any]):
        """Simulate agent-to-agent communication"""
        comm_data = {
            "from_agent": agent1["agent_id"],
            "to_agent": agent2["agent_id"],
            "message_type": random.choice(["coordination", "information", "request"]),
            "content": {
                "topic": random.choice(["strategy", "status_update", "resource_share"]),
                "urgency": random.randint(1, 5)
            }
        }

        try:
            start_time = time.time()
            async with self.session.post(
                f"{self.config.target_url}/api/agents/communicate",
                json=comm_data
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.request_times.append(response_time)

                if response.status == 200:
                    self.successful_requests += 1
                    await self.metrics_collector.record_request(
                        "agent_communicate", response_time, response.status, True
                    )
                else:
                    error_data = await response.text()
                    self.errors.append({
                        "endpoint": "agent_communicate",
                        "status": response.status,
                        "error": error_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await self.metrics_collector.record_request(
                        "agent_communicate", response_time, response.status, False
                    )

                self.total_requests += 1

        except Exception as e:
            self.errors.append({
                "endpoint": "agent_communicate",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self.total_requests += 1

    async def _run_agent_lifecycle(self, agent: Dict[str, Any], behavior: AgentBehavior):
        """Run the complete lifecycle of an agent"""
        start_time = time.time()
        action_count = 0

        while time.time() - start_time < self.config.duration:
            try:
                # Agent thinking
                if random.random() < 0.7:  # 70% chance to think
                    await self._agent_think(agent, behavior)

                # Agent action
                if random.random() < 0.8:  # 80% chance to act
                    await self._agent_act(agent, behavior)
                    action_count += 1

                # Agent communication
                if random.random() < 0.3 and len(self.agents) > 1:  # 30% chance to communicate
                    other_agent = random.choice([a for a in self.agents if a["agent_id"] != agent["agent_id"]])
                    await self._agent_communicate(agent, other_agent)

                # Think time based on behavior
                think_time = 1.0 / behavior.action_frequency
                think_time *= random.uniform(0.8, 1.2)  # Add variability
                await asyncio.sleep(think_time)

            except Exception as e:
                logger.error(f"Error in agent lifecycle for {agent['agent_id']}: {e}")
                await asyncio.sleep(1)  # Brief pause on error

        logger.info(f"Agent {agent['agent_id']} completed {action_count} actions")

    async def _setup_agents(self):
        """Setup all agents for the test"""
        num_agents = min(self.config.users, len(self.behaviors) * 10)  # Distribute across behaviors

        for i in range(num_agents):
            behavior = self.behaviors[i % len(self.behaviors)]
            agent = await self._register_agent(behavior)
            self.agents.append(agent)

            # Add some delay between registrations
            if i % 10 == 0:
                await asyncio.sleep(0.1)

        logger.info(f"Registered {len(self.agents)} agents")

    async def _cleanup_agents(self):
        """Cleanup agents after test"""
        for agent in self.agents:
            try:
                async with self.session.delete(
                    f"{self.config.target_url}/api/agents/{agent['agent_id']}"
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to cleanup agent {agent['agent_id']}")
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent['agent_id']}: {e}")

    async def execute(self) -> TestResult:
        """Execute the agent simulation load test"""
        logger.info(f"Starting agent simulation with {self.config.users} agents")

        try:
            await self._initialize_session()
            await self._setup_agents()

            if not self.agents:
                raise RuntimeError("No agents were successfully registered")

            # Run agent lifecycles concurrently
            agent_tasks = []
            for i, agent in enumerate(self.agents):
                behavior = self.behaviors[i % len(self.behaviors)]
                task = asyncio.create_task(self._run_agent_lifecycle(agent, behavior))
                agent_tasks.append(task)

            # Wait for all agents to complete
            await asyncio.gather(*agent_tasks, return_exceptions=True)

            # Cleanup
            await self._cleanup_agents()

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
                scenario="agent_simulation",
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

        # Estimate throughput (assuming average response size of 2KB)
        avg_response_size = 2048  # bytes
        throughput = (requests_per_second * avg_response_size) / (1024 * 1024)  # MB/s

        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 100

        # Additional metrics
        metrics = {
            "agents_simulated": len(self.agents),
            "agent_types": list(set(agent["agent_type"] for agent in self.agents)),
            "actions_per_agent": {
                agent["agent_id"]: random.randint(10, 100) for agent in self.agents
            },
            "communication_events": len([e for e in self.errors if e.get("endpoint") == "agent_communicate"]),
            "complexity_distribution": {
                behavior.complexity_level: sum(1 for agent in self.agents
                                             if agent.get("complexity_level") == behavior.complexity_level)
                for behavior in self.behaviors
            }
        }

        return TestResult(
            test_name=self.config.name,
            scenario="agent_simulation",
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