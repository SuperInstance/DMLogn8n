#!/usr/bin/env python3
"""
Run Complete Parallel Multi-Agent D&D System
Starts all parallel services with maximum concurrency
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import json
from datetime import datetime

# Add the multi-portal-gateway to path
sys.path.insert(0, str(Path(__file__).parent / "multi-portal-gateway"))

# Import all parallel services
from services.massive_parallel_orchestrator import MassiveParallelOrchestrator
from services.parallel_world_simulation import ParallelWorldSimulation
from services.parallel_dialogue_system import ParallelDialogueSystem
from services.parallel_combat_engine import ParallelCombatEngine
from services.parallel_metrics_system import ParallelMetricsSystem
from services.ai_model_pools import ModelManager
from services.memory_system import CharacterMemorySystem
from services.living_world import LivingWorld
from services.coder_bot import CoderBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ParallelSystemRunner:
    """Runs the complete parallel system"""

    def __init__(self):
        self.services = {}
        self.is_running = False
        self.startup_time = None

    async def initialize(self):
        """Initialize all parallel services"""
        logger.info("🚀 Initializing Complete Parallel Multi-Agent D&D System")
        self.startup_time = datetime.now()

        # Initialize metrics first (to monitor startup)
        logger.info("📊 Starting Metrics System...")
        self.services["metrics"] = ParallelMetricsSystem(
            collection_interval=0.1,  # 100ms collection
            retention_hours=24,
            enable_prometheus=True,
            enable_influxdb=True,
            enable_redis=True
        )
        await self.services["metrics"].initialize()

        # Initialize AI Model Pools
        logger.info("🧠 Starting AI Model Pools...")
        model_manager = create_default_model_manager()
        await model_manager.initialize()
        self.services["ai_models"] = model_manager

        # Initialize Massive Parallel Orchestrator
        logger.info("⚡ Starting Massive Parallel Orchestrator (1000 agents)...")
        self.services["orchestrator"] = MassiveParallelOrchestrator(
            max_agents=1000,
            max_workers=200,
            max_processes=50,
            enable_gpu=True
        )
        await self.services["orchestrator"].initialize()

        # Initialize World Simulation
        logger.info("🌍 Starting Parallel World Simulation (100 regions)...")
        self.services["world"] = ParallelWorldSimulation(
            num_regions=100,
            tick_rate=20,  # 20 ticks per second
            simulation_speed=3600  # 1 second = 1 hour game time
        )
        await self.services["world"].initialize()

        # Initialize Dialogue System
        logger.info("💬 Starting Parallel Dialogue System (1000 concurrent)...")
        self.services["dialogue"] = ParallelDialogueSystem(
            max_concurrent_dialogues=1000
        )
        await self.services["dialogue"].initialize()

        # Initialize Combat Engine
        logger.info("⚔️ Starting Parallel Combat Engine (500 encounters)...")
        self.services["combat"] = ParallelCombatEngine(
            max_concurrent_encounters=500,
            max_actions_per_second=1000
        )
        await self.services["combat"].initialize()

        # Initialize Memory System
        logger.info("💾 Starting Vector Memory System...")
        self.services["memory"] = CharacterMemorySystem(
            character_id="system",
            vector_db_host="localhost",
            port=6333,
            api_key="local"
        )
        await self.services["memory"].initialize()

        # Initialize Living World
        logger.info("🌿 Starting Living World System...")
        self.services["living_world"] = LivingWorld()
        await self.services["living_world"].initialize()

        # Initialize Coder Bot
        logger.info("🤖 Starting GLM-4.6 Coder Bot...")
        self.services["coder"] = CoderBot(
            model_endpoint="http://localhost:11434/api/generate",
            api_key="local"
        )
        await self.services["coder"].initialize()

        logger.info("✅ All services initialized successfully!")

    async def start_parallel_workload(self):
        """Start massive parallel workload"""
        logger.info("🎯 Starting Parallel Workload Simulation...")

        # Start 500 parallel agents
        agent_tasks = []
        for i in range(500):
            task = asyncio.create_task(
                self._run_parallel_agent(f"agent_{i}")
            )
            agent_tasks.append(task)

        # Start 100 parallel dialogues
        dialogue_tasks = []
        for i in range(100):
            task = asyncio.create_task(
                self._run_parallel_dialogue(f"dialogue_{i}")
            )
            dialogue_tasks.append(task)

        # Start 50 parallel combats
        combat_tasks = []
        for i in range(50):
            task = asyncio.create_task(
                self._run_parallel_combat(f"combat_{i}")
            )
            combat_tasks.append(task)

        # Start parallel world events
        world_tasks = []
        for i in range(20):
            task = asyncio.create_task(
                self._run_world_events(f"world_event_{i}")
            )
            world_tasks.append(task)

        # Start parallel code generation
        code_tasks = []
        for i in range(10):
            task = asyncio.create_task(
                self._run_code_generation(f"code_task_{i}")
            )
            code_tasks.append(task)

        # Start metrics collection
        metrics_task = asyncio.create_task(
            self._collect_system_metrics()
        )

        # Store all tasks
        self.service_tasks = {
            "agents": agent_tasks,
            "dialogues": dialogue_tasks,
            "combats": combat_tasks,
            "world": world_tasks,
            "code": code_tasks,
            "metrics": metrics_task
        }

        logger.info(f"🔥 Started {len(agent_tasks)} agents, {len(dialogue_tasks)} dialogues, "
                   f"{len(combat_tasks)} combats, {len(world_tasks)} world events, and {len(code_tasks)} code tasks")

    async def _run_parallel_agent(self, agent_id: str):
        """Run a parallel agent"""
        while self.is_running:
            try:
                # Make decisions
                decision_tasks = [
                    self._make_agent_decision(agent_id, "reflex"),
                    self._make_agent_decision(agent_id, "tactical"),
                    self._make_agent_decision(agent_id, "strategic")
                ]

                await asyncio.gather(*decision_tasks, return_exceptions=True)

                # Update memory
                await self._update_agent_memory(agent_id)

                # Communicate with other agents
                await self._agent_communication(agent_id)

                await asyncio.sleep(0.1)  # 100ms cycle

            except Exception as e:
                logger.error(f"Agent {agent_id} error: {e}")
                await asyncio.sleep(1)

    async def _run_parallel_dialogue(self, dialogue_id: str):
        """Run parallel dialogue generation"""
        while self.is_running:
            try:
                # Generate dialogue
                participants = [f"npc_{dialogue_id}_{i}" for i in range(2)]
                conv_id = await self.services["dialogue"].start_conversation(
                    participants=participants,
                    dialogue_type=random.choice(list(DialogueType)),
                    location=random.choice(["tavern", "forest", "city", "dungeon"])
                )

                # Add dialogue inputs
                for _ in range(5):
                    await self.services["dialogue"].add_dialogue_input(
                        conv_id,
                        random.choice(participants),
                        f"Hello from {dialogue_id}!"
                    )
                    await asyncio.sleep(0.5)

                await asyncio.sleep(2)  # Wait between dialogues

            except Exception as e:
                logger.error(f"Dialogue {dialogue_id} error: {e}")
                await asyncio.sleep(5)

    async def _run_parallel_combat(self, combat_id: str):
        """Run parallel combat encounters"""
        while self.is_running:
            try:
                # Create combat encounter
                encounter_id = await self.services["combat"].create_encounter(
                    name=f"Combat {combat_id}",
                    combatants=[
                        create_test_combatant(f"hero_{combat_id}", "player"),
                        create_test_combatant(f"monster_{combat_id}", "enemy")
                    ]
                )

                # Submit actions
                for _ in range(10):
                    await self.services["combat"].submit_action(
                        encounter_id,
                        CombatAction(
                            action_id=f"action_{combat_id}_{_}",
                            combatant_id=f"hero_{combat_id}",
                            action_type=random.choice(list(CombatActionType)),
                            target_id=f"monster_{combat_id}"
                        )
                    )
                    await asyncio.sleep(0.2)

                await asyncio.sleep(5)  # Wait between combats

            except Exception as e:
                logger.error(f"Combat {combat_id} error: {e}")
                await asyncio.sleep(10)

    async def _run_world_events(self, event_id: str):
        """Generate parallel world events"""
        while self.is_running:
            try:
                # Generate world events
                event = WorldEvent(
                    event_id=event_id,
                    region_id=random.choice(list(self.services["world"].regions.keys())),
                    event_type=random.choice(["monster_attack", "merchant_arrival", "festival"]),
                    description=f"World event {event_id}",
                    impact={"economy": random.uniform(-10, 10)}
                )

                await self.services["world"].add_world_event(event)

                await asyncio.sleep(1)  # Generate events every second

            except Exception as e:
                logger.error(f"World event {event_id} error: {e}")
                await asyncio.sleep(5)

    async def _run_code_generation(self, task_id: str):
        """Run parallel code generation"""
        while self.is_running:
            try:
                # Generate code
                request = CodeGenerationRequest(
                    request_id=f"code_{task_id}",
                    requester_id="system",
                    request_type="automation",
                    parameters={"task": f"Generate automation for {task_id}"}
                )

                await self.services["coder"].process_request(request)

                await asyncio.sleep(2)  # Generate code every 2 seconds

            except Exception as e:
                logger.error(f"Code generation {task_id} error: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self):
        """Collect and display system metrics"""
        while self.is_running:
            try:
                # Get metrics from all services
                orchestrator_metrics = await self.services["orchestrator"].get_metrics()
                world_metrics = await self.services["world"].get_world_state()
                dialogue_metrics = await self.services["dialogue"].get_metrics()
                combat_metrics = await self.services["combat"].get_metrics()
                system_metrics = await self.services["metrics"].get_system_status()

                # Display summary
                logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║                    PARALLEL SYSTEM METRICS                      ║
╠════════════════════════════════════════════════════════════════╣
║ System CPU: {system_metrics['system']['cpu_percent']:.1f}%
║ System Memory: {system_metrics['system']['memory_percent']:.1f}%
║ Active Agents: {orchestrator_metrics['task_counts']['active']}
║ Tasks Processed: {orchestrator_metrics['task_counts']['completed']}
║ Dialogues Generated: {dialogue_metrics['dialogues_generated']}
║ Active Combats: {combat_metrics['active_encounters']}
║ World Regions: {len(world_metrics['regions'])}
║ Current Game Time: {world_metrics['current_time']}
║ System Uptime: {(datetime.now() - self.startup_time).total_seconds():.1f}s
╚════════════════════════════════════════════════════════════════╝
                """)

                await asyncio.sleep(10)  # Display every 10 seconds

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)

    async def _make_agent_decision(self, agent_id: str, decision_type: str):
        """Make agent decision"""
        request = AIRequest(
            request_id=f"{agent_id}_{decision_type}_{int(time.time())}",
            tier=ModelTier.FAST if decision_type == "reflex" else ModelTier.MEDIUM,
            prompt=f"Decision for {agent_id}: {decision_type}",
            character_id=agent_id
        )

        await self.services["ai_models"].generate(request)

    async def _update_agent_memory(self, agent_id: str):
        """Update agent memory"""
        memory = Memory(
            memory_id=f"{agent_id}_mem_{int(time.time())}",
            character_id=agent_id,
            memory_type="episodic",
            content=f"Agent {agent_id} performed action",
            importance=random.uniform(0.5, 1.0)
        )

        await self.services["memory"].store_memory(memory)

    async def _agent_communication(self, agent_id: str):
        """Handle agent communication"""
        # Send message to random agent
        target_agent = f"agent_{random.randint(0, 499)}"
        message = {
            "from": agent_id,
            "to": target_agent,
            "content": f"Hello from {agent_id}",
            "timestamp": datetime.now()
        }

        # Process communication
        await self.services["orchestrator"].submit_task(
            ParallelTask(
                task_id=f"comm_{agent_id}_{target_agent}_{int(time.time())}",
                task_type="agent_communication",
                priority=500,
                data=message
            )
        )

    async def run(self):
        """Run the complete parallel system"""
        self.is_running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize all services
        await self.initialize()

        # Start parallel workload
        await self.start_parallel_workload()

        logger.info("🎮 Parallel Multi-Agent D&D System is running!")
        logger.info("Access points:")
        logger.info("  - Prometheus Metrics: http://localhost:9091")
        logger.info("  - System API: http://localhost:8001/docs")
        logger.info("  - AI Transparency: http://localhost:3001")
        logger.info("  - Player Dashboard: http://localhost:3000")
        logger.info("\nPress Ctrl+C to stop...")

        # Keep running
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            await self.shutdown()

    async def shutdown(self):
        """Shutdown all services"""
        self.is_running = False

        logger.info("Stopping all parallel tasks...")

        # Cancel all service tasks
        if hasattr(self, 'service_tasks'):
            for task_group in self.service_tasks.values():
                for task in task_group:
                    task.cancel()

            # Wait for tasks to complete
            all_tasks = []
            for task_group in self.service_tasks.values():
                all_tasks.extend(task_group)

            if all_tasks:
                await asyncio.gather(*all_tasks, return_exceptions=True)

        # Shutdown services in reverse order
        shutdown_order = ["coder", "living_world", "memory", "combat", "dialogue",
                         "world", "orchestrator", "ai_models", "metrics"]

        for service_name in shutdown_order:
            if service_name in self.services:
                logger.info(f"Shutting down {service_name}...")
                try:
                    await self.services[service_name].shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {service_name}: {e}")

        logger.info("🏁 Parallel Multi-Agent D&D System stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.is_running = False


# Helper functions
def create_test_combatant(combatant_id: str, team: str) -> Combatant:
    """Create test combatant"""
    return Combatant(
        combatant_id=combatant_id,
        name=combatant_id.replace("_", " ").title(),
        max_hp=random.randint(20, 100),
        current_hp=random.randint(20, 100),
        armor_class=random.randint(10, 20),
        initiative=random.randint(1, 10),
        speed=random.randint(20, 40),
        team=team,
        stats={
            "attack_bonus": random.randint(1, 10),
            "strength_bonus": random.randint(0, 5)
        }
    )


async def main():
    """Main entry point"""
    # Set process start method for Windows compatibility
    if sys.platform == "win32":
        mp.set_start_method("spawn", force=True)

    # Create and run system
    runner = ParallelSystemRunner()
    await runner.run()


if __name__ == "__main__":
    # Run the parallel system
    asyncio.run(main())