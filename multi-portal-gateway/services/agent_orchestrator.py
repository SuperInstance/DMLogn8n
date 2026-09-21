"""
Parallel Agent Orchestrator - Manages Multiple AI Agents Concurrently
Scales to thousands of agents with load balancing and coordination
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Manager
import threading
import time
from enum import Enum
import uuid
from dataclasses import dataclass
from collections import deque
import heapq

logger = logging.getLogger(__name__)

class AgentType(Enum):
    CHARACTER = "character"
    NPC = "npc"
    DM = "dm"
    CODER = "coder"
    OBSERVER = "observer"

@dataclass
class AgentTask:
    """Task for agent processing"""
    id: str
    agent_id: str
    task_type: str
    data: Dict
    priority: int
    created_at: datetime
    timeout: float = 30.0
    callback: Optional[str] = None

@dataclass
class AgentCluster:
    """Cluster of related agents"""
    id: str
    region: str
    agents: Set[str]
    leader: Optional[str] = None
    shared_context: Dict = None
    max_agents: int = 50

class ParallelAgentOrchestrator:
    """Manages multiple AI agents in parallel"""

    def __init__(self, max_workers: int = 50, max_processes: int = 10):
        self.max_workers = max_workers
        self.max_processes = max_processes

        # Execution pools for different workloads
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_processes=max_processes)

        # Agent management
        self.active_agents: Dict[str, Dict] = {}
        self.agent_clusters: Dict[str, AgentCluster] = {}
        self.agent_tasks: Dict[str, Dict] = {}  # agent_id -> {task_id: task}

        # Task queues with priorities
        self.task_queues = {
            "urgent": [],
            "high": [],
            "normal": [],
            "low": []
        }
        self.task_queue_lock = threading.Lock()

        # Coordination and communication
        self.communication_channels = Manager().dict()
        self.shared_memory = Manager().dict()

        # Load balancing
        self.agent_loads: Dict[str, int] = {}  # agent_id -> active tasks
        self.load_balancer = AgentLoadBalancer()

        # Event processing
        self.event_handlers = {}
        self.event_queue = asyncio.Queue(maxsize=10000)

        # Performance tracking
        self.metrics = AgentMetrics()

        # AI model managers for parallel processing
        self.ai_models = {
            "fast": FastAIModelPool(max_concurrent=100),
            "medium": MediumAIModelPool(max_concurrent=50),
            "slow": SlowAIModelPool(max_concurrent=20)
        }

        # Memory consolidation system
        self.memory_consolidator = ParallelMemoryConsolidator()

        # Start background tasks
        self.running = True
        self.task_scheduler = asyncio.create_task(self.schedule_tasks())
        self.event_processor = asyncio.create_task(self.process_events())
        self.load_balancer_task = asyncio.create_task(self.balance_loads())
        self.metrics_task = asyncio.create_task(self.update_metrics())

    async def register_agent(self, agent_config: Dict) -> str:
        """Register a new agent in the system"""
        agent_id = str(uuid.uuid4())

        agent = {
            "id": agent_id,
            "type": agent_config.get("type", AgentType.CHARACTER),
            "name": agent_config.get("name", f"Agent_{agent_id[:8]}"),
            "personality": agent_config.get("personality", {}),
            "capabilities": agent_config.get("capabilities", []),
            "state": "initializing",
            "last_activity": time.time(),
            "tasks_active": 0,
            "tasks_completed": 0,
            "created_at": datetime.utcnow()
        }

        # Add to active agents
        self.active_agents[agent_id] = agent
        self.agent_loads[agent_id] = 0

        # Create communication channel
        self.communication_channels[agent_id] = Manager().list()

        # Create shared memory space
        self.shared_memory[agent_id] = Manager().dict()

        # Initialize agent
        await self.initialize_agent(agent_id, agent_config)

        # Add to appropriate cluster
        if agent_config.get("cluster_id"):
            cluster_id = agent_config["cluster_id"]
            if cluster_id not in self.agent_clusters:
                await self.create_cluster(cluster_id, agent_config.get("region", "default"))
            self.agent_clusters[cluster_id].agents.add(agent_id)

        logger.info(f"Registered agent {agent_id} of type {agent['type']}")
        return agent_id

    async def initialize_agent(self, agent_id: str, config: Dict):
        """Initialize agent's AI systems"""
        # Initialize memory system for this agent
        memory_system = await self.memory_consolidator.create_memory(agent_id)
        self.shared_memory[agent_id]["memory"] = memory_system

        # Set up personality traits
        personality = config.get("personality", {})
        self.shared_memory[agent_id]["personality"] = {
            "aggression": personality.get("aggression", 0.5),
            "curiosity": personality.get("curiosity", 0.5),
            "risk_tolerance": personality.get("risk_tolerance", 0.5),
            "sociality": personality.get("sociality", 0.5),
            "creativity": personality.get("creativity", 0.5)
        }

        # Mark as ready
        self.active_agents[agent_id]["state"] = "ready"
        self.active_agents[agent_id]["initialized_at"] = datetime.utcnow()

    async def submit_task(self, task: AgentTask) -> str:
        """Submit task to agent for parallel processing"""
        # Add to appropriate queue based on priority
        with self.task_queue_lock:
            if task.priority >= 9:
                heapq.heappush(self.task_queues["urgent"], (task.priority, task.created_at, task))
            elif task.priority >= 7:
                heapq.heappush(self.task_queues["high"], (task.priority, task.created_at, task))
            elif task.priority >= 5:
                heapq.heappush(self.task_queues["normal"], (task.priority, task.created_at, task))
            else:
                heapq.heappush(self.task_queues["low"], (task.priority, task.created_at, task))

        # Track task
        if task.agent_id not in self.agent_tasks:
            self.agent_tasks[agent_id] = {}
        self.agent_tasks[agent_id][task.id] = task

        # Update agent load
        self.agent_loads[task.agent_id] += 1
        self.active_agents[task.agent_id]["tasks_active"] += 1

        # Log task submission
        logger.info(f"Submitted task {task.id} to agent {task.agent_id} with priority {task.priority}")
        return task.id

    async def schedule_tasks(self):
        """Schedule tasks from queues to available agents"""
        while self.running:
            # Get highest priority task
            next_task = None
            queue_name = None

            with self.task_queue_lock:
                for queue in ["urgent", "high", "normal", "low"]:
                    if self.task_queues[queue]:
                        _, _, task = heapq.heappop(self.task_queues[queue])
                        next_task = task
                        queue_name = queue
                        break

            if not next_task:
                await asyncio.sleep(0.1)
                continue

            # Find available agent
            available_agent = await self.load_balancer.find_available_agent(
                next_task, self.active_agents, self.agent_loads
            )

            if available_agent:
                # Assign task to agent
                await self.execute_task(available_agent, next_task, queue_name)
            else:
                # No available agent, try again
                await asyncio.sleep(0.5)

    async def execute_task(self, agent_id: str, task: AgentTask, queue_name: str):
        """Execute task on agent in parallel"""
        try:
            # Update agent state
            self.active_agents[agent_id]["state"] = "processing"
            self.active_agents[agent_id]["current_task"] = task.id
            self.active_agents[agent_id]["last_activity"] = time.time()

            # Select appropriate AI model based on task complexity
            ai_model = await self.select_ai_model(task)

            # Execute in thread pool for I/O or process pool for CPU intensive
            if task.task_type in ["text_generation", "dialogue", "reasoning"]:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.execute_ai_task,
                    (agent_id, task, ai_model)
                )
            else:
                result = await self.execute_ai_task(agent_id, task, ai_model)

            # Update task status
            task.result = result
            task.completed_at = datetime.utcnow()

            # Update agent metrics
            self.agent_loads[agent_id] -= 1
            self.active_agents[agent_id]["tasks_completed"] += 1
            self.active_agents[agent_id]["tasks_active"] -= 1
            self.active_agents[agent_id]["state"] = "ready"

            # Handle callback
            if task.callback:
                await self.handle_task_callback(task, result)

            # Log completion
            logger.info(f"Task {task.id} completed by agent {agent_id} in "
                        f"{(task.completed_at - task.created_at).total_seconds():.2f}s")

            # Update metrics
            self.metrics.record_task_completion(task)

        except Exception as e:
            logger.error(f"Task {task.id} failed on agent {agent_id}: {e}")
            # Handle task failure
            await self.handle_task_failure(agent_id, task, e)

    async def select_ai_model(self, task: AgentTask):
        """Select appropriate AI model based on task complexity"""
        complexity = self.assess_task_complexity(task)

        if complexity < 3:
            return self.ai_models["fast"].get_model()
        elif complexity < 7:
            return self.ai_models["medium"].get_model()
        else:
            return self.ai_models["slow"].get_model()

    def assess_task_complexity(self, task: AgentTask) -> float:
        """Assess complexity of task on scale 1-10"""
        complexity = 5.0  # Base complexity

        # Adjust based on task type
        if task.task_type == "combat_decision":
            complexity += 2.0
        elif task.task_type == "dialogue":
            complexity += 1.5
        elif task.task_type == "quest_planning":
            complexity += 3.0
        elif task.task_type == "world_editing":
            complexity += 4.0

        # Adjust based on data size
        data_size = len(str(task.data))
        if data_size > 1000:
            complexity += 1.0
        elif data_size > 5000:
            complexity += 2.0

        return min(10.0, complexity)

    def execute_ai_task(self, agent_id: str, task: AgentTask, ai_model):
        """Execute AI task using specified model"""
        # Get agent's context
        agent_context = self.get_agent_context(agent_id)

        # Execute with AI model
        result = ai_model.process_task(agent_id, task, agent_context)

        # Store result in shared memory
        self.shared_memory[agent_id]["last_result"] = result

        return result

    def get_agent_context(self, agent_id: str) -> Dict:
        """Get current context for agent"""
        agent = self.active_agents.get(agent_id, {})

        return {
            "agent_type": agent.get("type"),
            "personality": self.shared_memory[agent_id].get("personality", {}),
            "memory": self.shared_memory[agent_id].get("memory"),
            "location": agent.get("location", "unknown"),
            "recent_actions": agent.get("recent_actions", []),
            "cluster_members": self.get_cluster_members(agent_id)
        }

    def get_cluster_members(self, agent_id: str) -> List[str]:
        """Get members of agent's cluster"""
        for cluster in self.agent_clusters.values():
            if agent_id in cluster.agents:
                return list(cluster.agents)
        return []

    async def handle_task_callback(self, task: AgentTask, result: Any):
        """Handle callback after task completion"""
        if task.callback in self.event_handlers:
            await self.event_handlers[task.callback](task, result)

    async def handle_task_failure(self, agent_id: str, task: AgentTask, error: Exception):
        """Handle task failure and recovery"""
        # Try to reschedule task if it timed out
        if "timeout" in str(error).lower():
            task.priority = max(1, task.priority - 1)
            await self.submit_task(task)
        else:
            # Log error for debugging
            logger.error(f"Task {task.id} failed permanently: {error}")

    async def create_cluster(self, cluster_id: str, region: str):
        """Create new agent cluster"""
        cluster = AgentCluster(
            id=cluster_id,
            region=region,
            agents=set(),
            shared_context={},
            max_agents=50
        )
        self.agent_clusters[cluster_id] = cluster
        logger.info(f"Created cluster {cluster_id} in region {region}")

    async def process_events(self):
        """Process events from agent communication"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self.handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def handle_event(self, event: Dict):
        """Handle inter-agent events"""
        event_type = event.get("type")
        source = event.get("source")
        target = event.get("target")

        if event_type == "communication":
            # Handle inter-agent communication
            if target and target in self.communication_channels:
                self.communication_channels[target].append(event)
        elif event_type == "cluster_broadcast":
            # Broadcast to cluster members
            cluster = self.get_agent_cluster(source)
            if cluster:
                for member_id in cluster.agents:
                    if member_id in self.communication_channels:
                        self.communication_channels[member_id].append(event)

    def get_agent_cluster(self, agent_id: str) -> Optional[AgentCluster]:
        """Get cluster that agent belongs to"""
        for cluster in self.agent_clusters.values():
            if agent_id in cluster.agents:
                return cluster
        return None

    async def balance_loads(self):
        """Balance agent loads for optimal performance"""
        while self.running:
            await asyncio.sleep(5)

            # Move agents between load levels
            for agent_id, load in self.agent_loads.items():
                if load > 10:  # Overloaded agent
                    # Find lighter loaded agent
                    for other_id, other_load in self.agent_loads.items():
                        if other_load < 5 and other_id != agent_id:
                            # Rebalance
                            await self.rebalance_tasks(agent_id, other_id)
                            break

    async def rebalance_tasks(self, overloaded_agent: str, underloaded_agent: str):
        """Rebalance tasks between agents"""
        # Move some tasks from overloaded to underloaded
        tasks_to_move = min(3, self.agent_loads[overloaded_agent] // 2)

        for i in range(tasks_to_move):
            # Find oldest task that can be moved
            for task_id, task in list(self.agent_tasks[overloaded_agent].items()):
                if task.task_type in ["dialogue", "exploration", "social"]:
                    # Can move this task
                    task.agent_id = underloaded_agent
                    self.agent_tasks[overloaded_agent].pop(task_id)
                    self.agent_tasks[underloaded_agent][task_id] = task
                    break

    async def update_metrics(self):
        """Update system metrics"""
        while self.running:
            await asyncio.sleep(10)

            # Calculate system metrics
            total_agents = len(self.active_agents)
            total_tasks = sum(len(tasks) for tasks in self.agent_tasks.values())
            avg_load = sum(self.agent_loads.values()) / max(1, len(self.agent_loads))

            # Update metrics
            self.metrics.update({
                "total_agents": total_agents,
                "total_tasks": total_tasks,
                "average_load": avg_load,
                "clusters": len(self.agent_clusters),
                "timestamp": datetime.utcnow()
            })

    async def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "agents": {
                "total": len(self.active_agents),
                "by_type": self.count_agents_by_type(),
                "active_tasks": sum(len(tasks) for tasks in self.agent_tasks.values()),
                "average_load": sum(self.agent_loads.values()) / max(1, len(self.agent_loads))
            },
            "clusters": {
                "total": len(self.agent_clusters),
                "agents_per_cluster": [len(c.agents) for c in self.agent_clusters.values()]
            },
            "queues": {
                name: len(queue) for name, queue in self.task_queues.items()
            },
            "pools": {
                "threads": self.thread_pool._max_workers,
                "processes": self.process_pool._max_workers
            },
            "models": {
                name: model.pool_size for name, model in self.ai_models.items()
            }
        }

    def count_agents_by_type(self) -> Dict[str, int]:
        """Count agents by type"""
        counts = {}
        for agent in self.active_agents.values():
            agent_type = agent.get("type", "unknown")
            counts[agent_type] = counts.get(agent_type, 0) + 1
        return counts

    async def shutdown(self):
        """Gracefully shutdown orchestrator"""
        logger.info("Shutting down parallel agent orchestrator")
        self.running = False

        # Cancel background tasks
        self.task_scheduler.cancel()
        self.event_processor.cancel()
        self.load_balancer_task.cancel()
        self.metrics_task.cancel()

        # Wait for all tasks to complete
        await self.thread_pool.shutdown(wait=True)
        await self.process_pool.shutdown(wait=True)

        logger.info("Parallel agent orchestrator shutdown complete")

class AgentLoadBalancer:
    """Balances load across agents efficiently"""

    def __init__(self):
        self.agent_capabilities = {}

    async def find_available_agent(self, task: AgentTask, agents: Dict, loads: Dict) -> Optional[str]:
        """Find best agent for task"""
        best_agent = None
        best_score = -1

        for agent_id, agent in agents.items():
            if agent["state"] != "ready":
                continue

            # Calculate suitability score
            score = self.calculate_suitability_score(agent, task, loads[agent_id])

            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    def calculate_suitability_score(self, agent: Dict, task: AgentTask, current_load: int) -> float:
        """Calculate how suitable agent is for task"""
        score = 10.0

        # Penalize agents with high load
        score -= min(5.0, current_load * 0.5)

        # Bonus for agent capabilities
        if task.task_type in agent.get("capabilities", []):
            score += 2.0

        # Personality-based scoring
        if agent.get("type") == AgentType.CHARACTER:
            if task.task_type == "dialogue" and agent.get("personality", {}).get("sociality", 0.5) > 0.7:
                score += 1.0

        return max(0, score)

class ParallelMemoryConsolidator:
    """Manages memory consolidation for multiple agents in parallel"""

    def __init__(self):
        self.consolidation_queue = asyncio.Queue(maxsize=100)
        self.consolidation_pool = ThreadPoolExecutor(max_workers=5)
        self.memory_systems: Dict[str, Any] = {}

    async def create_memory(self, agent_id: str):
        """Create memory system for agent"""
        # In real implementation, this would connect to Qdrant or similar
        memory_system = f"MemorySystem-{agent_id}"
        self.memory_systems[agent_id] = memory_system
        return memory_system

    async def schedule_consolidation(self, agent_id: str):
        """Schedule memory consolidation for agent"""
        await self.consolidation_queue.put(agent_id)

    async def process_consolidations(self):
        """Process memory consolidations in parallel"""
        while True:
            try:
                agent_id = await asyncio.wait_for(
                    self.consolidation_queue.get(),
                    timeout=1.0
                )

                # Process in parallel
                await asyncio.get_event_loop().run_in_executor(
                    self.consolidate_memory,
                    (agent_id,)
                )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Memory consolidation failed for {agent_id}: {e}")

    def consolidate_memory(self, agent_id: str):
        """Consolidate agent's memory"""
        # In real implementation, this would:
        # 1. Consolidate working memory to episodic
        # 2. Summarize episodic to semantic
        # 3. Update personality traits
        # 4. Clean up old memories
        pass

class AgentMetrics:
    """Tracks performance metrics for agent system"""

    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.current_metrics = {}

    def record_task_completion(self, task: AgentTask):
        """Record completed task metrics"""
        self.current_metrics["task"] = {
            "completed_at": datetime.utcnow(),
            "processing_time": (task.completed_at - task.created_at).total_seconds(),
            "task_type": task.task_type,
            "priority": task.priority
        }

        self.metrics_history.append(dict(self.current_metrics))

    def update(self, metrics: Dict):
        """Update current metrics"""
        self.current_metrics.update(metrics)