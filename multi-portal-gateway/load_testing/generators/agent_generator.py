#!/usr/bin/env python3
"""
AI Agent Load Generator
Generates realistic AI agent behavior patterns for load testing
"""

import asyncio
import random
import time
import uuid
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
import numpy as np
from faker import Faker

logger = logging.getLogger(__name__)

@dataclass
class AgentProfile:
    """Defines an AI agent profile"""
    agent_id: str
    agent_type: str
    personality: str
    capabilities: List[str]
    complexity_level: int
    memory_size: int
    processing_speed: float  # operations per second
    response_time_range: tuple  # (min, max) in milliseconds
    error_rate: float  # 0-1
    workload_pattern: str  # constant, burst, random, wave

@dataclass
class AgentWorkload:
    """Defines agent workload patterns"""
    tasks_per_second: float
    burst_interval: int  # seconds
    burst_duration: int  # seconds
    peak_load_multiplier: float
    wave_period: int  # seconds
    idle_ratio: float  # 0-1

class AgentLoadGenerator:
    """Generates AI agent load patterns for testing"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fake = Faker()
        self.agents: List[AgentProfile] = []
        self.workloads: Dict[str, AgentWorkload] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.metrics_callback: Optional[Callable] = None
        self.running = False

    def register_metrics_callback(self, callback: Callable):
        """Register callback for metrics collection"""
        self.metrics_callback = callback

    def generate_agent_profiles(self, count: int) -> List[AgentProfile]:
        """Generate diverse AI agent profiles"""
        profiles = []

        agent_types = [
            "dm_assistant", "npc", "combat_agent", "world_state",
            "dialogue_manager", "quest_giver", "merchant", "guardian",
            "storyteller", "combat_logician", "emotion_engine", "memory_keeper"
        ]

        personalities = [
            "strategic_thinker", "creative_storyteller", "tactical_calculator",
            "empathetic_listener", "logical_analyzer", "chaotic_improviser",
            "methodical_planner", "intuitive_feeler", "detail_oriented",
            "big_picture_thinker", "cautious_observer", "bold_leader"
        ]

        capabilities_pools = {
            "dm_assistant": ["narrative_generation", "combat_analysis", "player_guidance", "world_building"],
            "npc": ["dialogue_response", "emotion_expression", "memory_recall", "relationship_building"],
            "combat_agent": ["damage_calculation", "tactical_planning", "coordination", "status_tracking"],
            "world_state": ["state_sync", "event_logging", "consistency_check", "persistence"],
            "dialogue_manager": ["conversation_flow", "emotion_tracking", "context_maintenance", "response_generation"],
            "quest_giver": ["quest_creation", "progress_tracking", "reward_calculation", "story_integration"],
            "merchant": ["inventory_management", "price_calculation", "bargaining", "trade_logic"],
            "guardian": ["threat_assessment", "protection_logic", "alert_system", "access_control"],
            "storyteller": ["narrative_weaving", "plot_development", "character_development", "pacing_control"],
            "combat_logician": ["rule_enforcement", "action_validation", "effect_calculation", "turn_management"],
            "emotion_engine": ["emotion_simulation", "mood_tracking", "relationship_dynamics", "personality_expression"],
            "memory_keeper": ["data_storage", "memory_retrieval", "context_maintenance", "history_tracking"]
        }

        workload_patterns = ["constant", "burst", "random", "wave"]

        for i in range(count):
            agent_type = random.choice(agent_types)
            personality = random.choice(personalities)
            capabilities = random.sample(capabilities_pools[agent_type], k=random.randint(2, 4))
            complexity_level = random.randint(3, 10)
            memory_size = random.choice([128, 256, 512, 1024, 2048])  # MB

            # Processing speed based on complexity
            base_speed = 10.0  # operations per second
            processing_speed = base_speed * (11 - complexity_level) / 2  # Higher complexity = slower processing

            # Response time based on complexity and processing speed
            min_response = 50 + (complexity_level * 20)  # ms
            max_response = min_response * 3
            response_time_range = (min_response, max_response)

            # Error rate inversely proportional to complexity and processing speed
            error_rate = max(0.001, 0.1 - (complexity_level * 0.01) - (processing_speed * 0.001))

            workload_pattern = random.choice(workload_patterns)

            profile = AgentProfile(
                agent_id=str(uuid.uuid4()),
                agent_type=agent_type,
                personality=personality,
                capabilities=capabilities,
                complexity_level=complexity_level,
                memory_size=memory_size,
                processing_speed=processing_speed,
                response_time_range=response_time_range,
                error_rate=error_rate,
                workload_pattern=workload_pattern
            )

            profiles.append(profile)

        return profiles

    def generate_workload_patterns(self, profiles: List[AgentProfile]) -> Dict[str, AgentWorkload]:
        """Generate workload patterns for agents"""
        workloads = {}

        for profile in profiles:
            # Base workload on agent type and complexity
            base_tasks_per_second = {
                "dm_assistant": 0.5,
                "npc": 2.0,
                "combat_agent": 3.0,
                "world_state": 1.0,
                "dialogue_manager": 2.5,
                "quest_giver": 0.8,
                "merchant": 1.2,
                "guardian": 1.5,
                "storyteller": 0.3,
                "combat_logician": 4.0,
                "emotion_engine": 1.8,
                "memory_keeper": 0.7
            }.get(profile.agent_type, 1.0)

            # Adjust for complexity
            tasks_per_second = base_tasks_per_second * (profile.complexity_level / 5.0)

            # Generate workload parameters
            if profile.workload_pattern == "constant":
                workload = AgentWorkload(
                    tasks_per_second=tasks_per_second,
                    burst_interval=0,
                    burst_duration=0,
                    peak_load_multiplier=1.0,
                    wave_period=0,
                    idle_ratio=0.1
                )
            elif profile.workload_pattern == "burst":
                workload = AgentWorkload(
                    tasks_per_second=tasks_per_second * 0.3,  # Base load
                    burst_interval=random.randint(30, 120),  # Burst every 30-120 seconds
                    burst_duration=random.randint(5, 15),  # Burst lasts 5-15 seconds
                    peak_load_multiplier=random.uniform(3.0, 5.0),
                    wave_period=0,
                    idle_ratio=0.05
                )
            elif profile.workload_pattern == "wave":
                workload = AgentWorkload(
                    tasks_per_second=tasks_per_second,
                    burst_interval=0,
                    burst_duration=0,
                    peak_load_multiplier=2.0,
                    wave_period=random.randint(60, 180),  # Wave period
                    idle_ratio=0.2
                )
            else:  # random
                workload = AgentWorkload(
                    tasks_per_second=tasks_per_second * random.uniform(0.5, 2.0),
                    burst_interval=0,
                    burst_duration=0,
                    peak_load_multiplier=1.0,
                    wave_period=0,
                    idle_ratio=random.uniform(0.1, 0.4)
                )

            workloads[profile.agent_id] = workload

        return workloads

    def calculate_task_rate(self, agent_id: str, current_time: float) -> float:
        """Calculate current task rate for an agent"""
        if agent_id not in self.workloads:
            return 0.0

        workload = self.workloads[agent_id]
        base_rate = workload.tasks_per_second

        if workload.wave_period > 0:
            # Wave pattern
            phase = (current_time % workload.wave_period) / workload.wave_period
            multiplier = 1.0 + (workload.peak_load_multiplier - 1.0) * (0.5 + 0.5 * np.sin(2 * np.pi * phase))
            return base_rate * multiplier
        elif workload.burst_interval > 0:
            # Burst pattern
            time_in_cycle = current_time % workload.burst_interval
            if time_in_cycle < workload.burst_duration:
                return base_rate * workload.peak_load_multiplier
            else:
                return base_rate
        else:
            # Constant or random
            if random.random() > workload.idle_ratio:
                return base_rate * random.uniform(0.8, 1.2)
            else:
                return 0.0

    async def execute_agent_task(self, agent: AgentProfile, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent task"""
        start_time = time.time()

        # Simulate processing time based on agent capabilities
        min_time, max_time = agent.response_time_range
        processing_time = random.uniform(min_time, max_time) / 1000.0  # Convert to seconds

        # Adjust processing time based on task complexity
        complexity_factor = parameters.get("complexity", 1.0)
        processing_time *= complexity_factor

        # Simulate processing
        await asyncio.sleep(processing_time)

        # Determine success based on error rate
        success = random.random() > agent.error_rate

        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        result = {
            "agent_id": agent.agent_id,
            "task_type": task_type,
            "parameters": parameters,
            "success": success,
            "execution_time": execution_time,
            "processing_time": processing_time * 1000,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capabilities_used": random.sample(agent.capabilities, k=min(2, len(agent.capabilities)))
        }

        if not success:
            result["error"] = random.choice([
                "timeout", "resource_exhausted", "logic_error", "data_corruption",
                "network_error", "authentication_failed", "permission_denied"
            ])

        # Record metrics
        if self.metrics_callback:
            await self.metrics_callback("agent_task", execution_time, 200 if success else 500, success)

        return result

    async def agent_worker(self, agent: AgentProfile, duration: int):
        """Worker function for a single agent"""
        start_time = time.time()
        last_task_time = start_time

        while time.time() - start_time < duration and self.running:
            current_time = time.time()
            task_rate = self.calculate_task_rate(agent.agent_id, current_time - start_time)

            if task_rate > 0:
                # Determine if it's time for a new task
                time_since_last_task = current_time - last_task_time
                if time_since_last_task >= (1.0 / task_rate):
                    # Generate task
                    task_type = random.choice(agent.capabilities)
                    parameters = {
                        "complexity": agent.complexity_level / 10.0,
                        "memory_required": agent.memory_size,
                        "processing_speed": agent.processing_speed,
                        "context": {
                            "personality": agent.personality,
                            "current_time": current_time,
                            "task_count": random.randint(1, 100)
                        }
                    }

                    # Execute task
                    await self.execute_agent_task(agent, task_type, parameters)
                    last_task_time = current_time

            # Brief sleep to prevent busy waiting
            await asyncio.sleep(0.01)

    async def start_load_generation(self, num_agents: int, duration: int):
        """Start generating load from multiple agents"""
        logger.info(f"Starting agent load generation with {num_agents} agents for {duration} seconds")

        # Generate agent profiles
        self.agents = self.generate_agent_profiles(num_agents)
        self.workloads = self.generate_workload_patterns(self.agents)

        self.running = True

        # Start worker tasks for each agent
        for agent in self.agents:
            task = asyncio.create_task(self.agent_worker(agent, duration))
            self.active_tasks[agent.agent_id] = task

        # Wait for all tasks to complete
        try:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in agent load generation: {e}")

        self.running = False
        logger.info("Agent load generation completed")

    async def stop_load_generation(self):
        """Stop load generation"""
        logger.info("Stopping agent load generation")
        self.running = False

        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()

        # Wait for tasks to complete cancellation
        try:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping agent tasks: {e}")

        self.active_tasks.clear()

    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated agents"""
        if not self.agents:
            return {}

        stats = {
            "total_agents": len(self.agents),
            "agent_types": {},
            "personalities": {},
            "complexity_distribution": {},
            "memory_distribution": {},
            "workload_patterns": {},
            "avg_processing_speed": 0,
            "avg_response_time": 0,
            "total_error_rate": 0
        }

        total_processing_speed = 0
        total_min_response = 0
        total_max_response = 0
        total_error_rate = 0

        for agent in self.agents:
            # Agent type distribution
            stats["agent_types"][agent.agent_type] = stats["agent_types"].get(agent.agent_type, 0) + 1

            # Personality distribution
            stats["personalities"][agent.personality] = stats["personalities"].get(agent.personality, 0) + 1

            # Complexity distribution
            complexity_range = f"{agent.complexity_level}-{min(agent.complexity_level + 2, 10)}"
            stats["complexity_distribution"][complexity_range] = stats["complexity_distribution"].get(complexity_range, 0) + 1

            # Memory distribution
            memory_range = f"{agent.memory_size}MB"
            stats["memory_distribution"][memory_range] = stats["memory_distribution"].get(memory_range, 0) + 1

            # Workload pattern distribution
            stats["workload_patterns"][agent.workload_pattern] = stats["workload_patterns"].get(agent.workload_pattern, 0) + 1

            # Totals for averages
            total_processing_speed += agent.processing_speed
            total_min_response += agent.response_time_range[0]
            total_max_response += agent.response_time_range[1]
            total_error_rate += agent.error_rate

        # Calculate averages
        stats["avg_processing_speed"] = total_processing_speed / len(self.agents)
        stats["avg_response_time"] = (total_min_response + total_max_response) / (2 * len(self.agents))
        stats["total_error_rate"] = total_error_rate / len(self.agents)

        return stats

    def export_agent_profiles(self, filename: str):
        """Export agent profiles to file"""
        profiles_data = [asdict(agent) for agent in self.agents]
        workloads_data = {agent_id: asdict(workload) for agent_id, workload in self.workloads.items()}

        export_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_agents": len(self.agents),
            "agent_profiles": profiles_data,
            "workload_patterns": workloads_data,
            "statistics": self.get_agent_statistics()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Agent profiles exported to {filename}")

# Example usage and test functions
async def test_agent_generator():
    """Test the agent load generator"""
    config = {
        "target_url": "http://localhost:8000",
        "timeout": 30
    }

    generator = AgentLoadGenerator(config)

    # Generate test agents
    profiles = generator.generate_agent_profiles(10)
    workloads = generator.generate_workload_patterns(profiles)

    print(f"Generated {len(profiles)} agent profiles")
    print(f"Generated {len(workloads)} workload patterns")

    # Print statistics
    stats = generator.get_agent_statistics()
    print("\nAgent Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Export profiles
    generator.export_agent_profiles("test_agent_profiles.json")

    # Start load generation for a short test
    print("\nStarting 10-second load generation test...")
    await generator.start_load_generation(5, 10)

if __name__ == "__main__":
    asyncio.run(test_agent_generator())