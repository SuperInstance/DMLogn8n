#!/usr/bin/env python3
"""
Agent Coordinator for DMLogn8n Multi-Agent Platform

This module provides specialized coordination for AI agents including:
- Agent lifecycle management
- Agent communication routing
- Agent capability discovery and matching
- Agent workload distribution
- Agent health monitoring and recovery
- Agent collaboration and coordination
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import consul.aio
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """AI agent types"""
    CHARACTER_AGENT = "character_agent"
    DIALOGUE_AGENT = "dialogue_agent"
    WORLD_SIMULATION_AGENT = "world_simulation_agent"
    COMBAT_ENGINE_AGENT = "combat_engine_agent"
    STORY_GENERATOR_AGENT = "story_generator_agent"
    CONTENT_CREATOR_AGENT = "content_creator_agent"
    MODERATOR_AGENT = "moderator_agent"
    ANALYTICS_AGENT = "analytics_agent"
    TRANSLATOR_AGENT = "translator_agent"
    PERSONALITY_AGENT = "personality_agent"

class AgentStatus(Enum):
    """Agent status values"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PROCESSING = "processing"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5

@dataclass
class AgentCapability:
    """Agent capability definition"""
    capability_id: str
    name: str
    description: str
    category: str
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    supported_languages: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentDefinition:
    """Agent definition and metadata"""
    agent_id: str
    name: str
    agent_type: AgentType
    version: str
    description: str
    capabilities: List[AgentCapability]
    personality_traits: Dict[str, Any] = field(default_factory=dict)
    knowledge_domains: List[str] = field(default_factory=list)
    communication_protocols: List[str] = field(default_factory=list)
    supported_tasks: List[str] = field(default_factory=list)
    max_workload: int = 10
    current_workload: int = 0
    performance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentTask:
    """Agent task definition"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    requirements: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    assigned_agent_id: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_task_duration: float = 0
    success_rate: float = 1.0
    cpu_usage: float = 0
    memory_usage: float = 0
    response_time: float = 0
    last_activity: datetime = field(default_factory=datetime.now)
    uptime: float = 0
    collaboration_count: int = 0

class AgentCoordinator:
    """
    Specialized coordinator for AI agents in DMLogn8n platform
    """

    def __init__(self, consul_manager):
        self.consul_manager = consul_manager
        self.consul = consul_manager.consul
        self.registered_agents = {}
        self.agent_capabilities = {}
        self.agent_tasks = {}
        self.agent_metrics = {}
        self.agent_collaborations = {}
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.collaboration_sessions = {}
        self._shutdown = False
        self._task_processor_task = None
        self._health_monitor_task = None

    async def initialize(self) -> bool:
        """Initialize agent coordinator"""
        try:
            # Start background tasks
            self._task_processor_task = asyncio.create_task(self._process_task_queue())
            self._health_monitor_task = asyncio.create_task(self._monitor_agent_health())

            # Initialize default agent types and capabilities
            await self._initialize_default_capabilities()

            logger.info("Agent coordinator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent coordinator: {e}")
            return False

    async def register_agent(self, agent_def: AgentDefinition) -> bool:
        """Register a new AI agent"""
        try:
            agent_id = agent_def.agent_id

            # Validate agent definition
            if not await self._validate_agent_definition(agent_def):
                logger.error(f"Invalid agent definition: {agent_id}")
                return False

            # Store agent definition
            self.registered_agents[agent_id] = agent_def

            # Store capabilities
            self.agent_capabilities[agent_id] = agent_def.capabilities

            # Initialize metrics
            self.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

            # Register with Consul
            await self._register_agent_with_consul(agent_def)

            # Start monitoring agent
            asyncio.create_task(self._monitor_agent(agent_id))

            logger.info(f"Agent registered: {agent_id} ({agent_def.name})")
            return True

        except Exception as e:
            logger.error(f"Agent registration error: {e}")
            return False

    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an AI agent"""
        try:
            # Cancel active tasks
            if agent_id in self.active_tasks:
                for task_id in list(self.active_tasks[agent_id]):
                    await self.cancel_task(task_id)

            # Remove from registries
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]

            if agent_id in self.agent_capabilities:
                del self.agent_capabilities[agent_id]

            if agent_id in self.agent_metrics:
                del self.agent_metrics[agent_id]

            # Deregister from Consul
            await self.consul.agent.service.deregister(f"agent-{agent_id}")

            logger.info(f"Agent deregistered: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Agent deregistration error: {e}")
            return False

    async def submit_task(self, task: AgentTask) -> str:
        """Submit a task to the agent pool"""
        try:
            # Validate task
            if not await self._validate_task(task):
                logger.error(f"Invalid task: {task.task_id}")
                return ""

            # Add to task queue
            await self.task_queue.put(task)
            self.agent_tasks[task.task_id] = task

            logger.info(f"Task submitted: {task.task_id}")
            return task.task_id

        except Exception as e:
            logger.error(f"Task submission error: {e}")
            return ""

    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Manually assign a task to a specific agent"""
        try:
            if task_id not in self.agent_tasks:
                logger.error(f"Task not found: {task_id}")
                return False

            if agent_id not in self.registered_agents:
                logger.error(f"Agent not found: {agent_id}")
                return False

            task = self.agent_tasks[task_id]
            agent = self.registered_agents[agent_id]

            # Check if agent can handle task
            if not await self._can_agent_handle_task(agent, task):
                logger.error(f"Agent {agent_id} cannot handle task {task_id}")
                return False

            # Assign task
            task.assigned_agent_id = agent_id
            task.status = "assigned"

            # Add to agent's active tasks
            if agent_id not in self.active_tasks:
                self.active_tasks[agent_id] = set()
            self.active_tasks[agent_id].add(task_id)

            # Send task to agent
            await self._send_task_to_agent(agent_id, task)

            logger.info(f"Task {task_id} assigned to agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Task assignment error: {e}")
            return False

    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Mark a task as completed"""
        try:
            if task_id not in self.agent_tasks:
                logger.error(f"Task not found: {task_id}")
                return False

            task = self.agent_tasks[task_id]
            task.status = "completed"
            task.result = result

            # Update agent metrics
            if task.assigned_agent_id:
                await self._update_agent_metrics(task.assigned_agent_id, True, task)

            # Remove from active tasks
            if task.assigned_agent_id and task.assigned_agent_id in self.active_tasks:
                self.active_tasks[task.assigned_agent_id].discard(task_id)

            logger.info(f"Task completed: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Task completion error: {e}")
            return False

    async def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed"""
        try:
            if task_id not in self.agent_tasks:
                logger.error(f"Task not found: {task_id}")
                return False

            task = self.agent_tasks[task_id]
            task.status = "failed"
            task.error_message = error_message
            task.retry_count += 1

            # Update agent metrics
            if task.assigned_agent_id:
                await self._update_agent_metrics(task.assigned_agent_id, False, task)

            # Remove from active tasks
            if task.assigned_agent_id and task.assigned_agent_id in self.active_tasks:
                self.active_tasks[task.assigned_agent_id].discard(task_id)

            # Retry task if retries available
            if task.retry_count < task.max_retries:
                task.status = "pending"
                task.assigned_agent_id = None
                await self.task_queue.put(task)
                logger.info(f"Task retry scheduled: {task_id} (attempt {task.retry_count + 1})")

            logger.warning(f"Task failed: {task_id} - {error_message}")
            return True

        except Exception as e:
            logger.error(f"Task failure error: {e}")
            return False

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        try:
            if task_id not in self.agent_tasks:
                logger.error(f"Task not found: {task_id}")
                return False

            task = self.agent_tasks[task_id]
            task.status = "cancelled"

            # Remove from active tasks
            if task.assigned_agent_id and task.assigned_agent_id in self.active_tasks:
                self.active_tasks[task.assigned_agent_id].discard(task_id)

            # Send cancellation to agent
            if task.assigned_agent_id:
                await self._cancel_agent_task(task.assigned_agent_id, task_id)

            logger.info(f"Task cancelled: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Task cancellation error: {e}")
            return False

    async def find_agents_by_capability(self, capability_name: str, requirements: Optional[Dict[str, Any]] = None) -> List[str]:
        """Find agents with specific capability"""
        try:
            matching_agents = []

            for agent_id, capabilities in self.agent_capabilities.items():
                for capability in capabilities:
                    if capability.name == capability_name:
                        # Check requirements if provided
                        if requirements:
                            if self._check_capability_requirements(capability, requirements):
                                matching_agents.append(agent_id)
                        else:
                            matching_agents.append(agent_id)
                        break

            return matching_agents

        except Exception as e:
            logger.error(f"Agent search error: {e}")
            return []

    async def get_best_agent_for_task(self, task: AgentTask) -> Optional[str]:
        """Find the best agent for a specific task"""
        try:
            candidate_agents = []

            for agent_id, agent in self.registered_agents.items():
                if await self._can_agent_handle_task(agent, task):
                    score = await self._calculate_agent_score(agent_id, task)
                    candidate_agents.append((agent_id, score))

            if not candidate_agents:
                return None

            # Sort by score (highest first)
            candidate_agents.sort(key=lambda x: x[1], reverse=True)
            return candidate_agents[0][0]

        except Exception as e:
            logger.error(f"Best agent selection error: {e}")
            return None

    async def start_collaboration(self, agents: List[str], collaboration_type: str, context: Dict[str, Any]) -> str:
        """Start agent collaboration session"""
        try:
            session_id = str(uuid.uuid4())

            # Validate agents
            for agent_id in agents:
                if agent_id not in self.registered_agents:
                    logger.error(f"Agent not found: {agent_id}")
                    return ""

            # Create collaboration session
            collaboration = {
                'session_id': session_id,
                'agents': agents,
                'type': collaboration_type,
                'context': context,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'messages': [],
                'shared_data': {}
            }

            self.collaboration_sessions[session_id] = collaboration

            # Notify agents
            for agent_id in agents:
                await self._notify_agent_collaboration(agent_id, session_id, 'start')

            logger.info(f"Collaboration started: {session_id} with agents: {agents}")
            return session_id

        except Exception as e:
            logger.error(f"Collaboration start error: {e}")
            return ""

    async def send_collaboration_message(self, session_id: str, sender_agent_id: str, message: Dict[str, Any]) -> bool:
        """Send message in collaboration session"""
        try:
            if session_id not in self.collaboration_sessions:
                logger.error(f"Collaboration session not found: {session_id}")
                return False

            session = self.collaboration_sessions[session_id]
            if sender_agent_id not in session['agents']:
                logger.error(f"Agent not in collaboration session: {sender_agent_id}")
                return False

            # Add message to session
            message_data = {
                'sender': sender_agent_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            session['messages'].append(message_data)

            # Notify other agents
            for agent_id in session['agents']:
                if agent_id != sender_agent_id:
                    await self._notify_agent_message(agent_id, session_id, message_data)

            logger.info(f"Collaboration message sent: {session_id} from {sender_agent_id}")
            return True

        except Exception as e:
            logger.error(f"Collaboration message error: {e}")
            return False

    async def end_collaboration(self, session_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """End collaboration session"""
        try:
            if session_id not in self.collaboration_sessions:
                logger.error(f"Collaboration session not found: {session_id}")
                return False

            session = self.collaboration_sessions[session_id]
            session['status'] = 'ended'
            session['ended_at'] = datetime.now().isoformat()
            if result:
                session['result'] = result

            # Notify agents
            for agent_id in session['agents']:
                await self._notify_agent_collaboration(agent_id, session_id, 'end')

            # Clean up after delay
            asyncio.create_task(self._cleanup_collaboration(session_id))

            logger.info(f"Collaboration ended: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Collaboration end error: {e}")
            return False

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        try:
            if agent_id not in self.registered_agents:
                return {}

            agent = self.registered_agents[agent_id]
            metrics = self.agent_metrics.get(agent_id)
            active_tasks = len(self.active_tasks.get(agent_id, set()))

            status = {
                'agent_id': agent_id,
                'name': agent.name,
                'type': agent.agent_type.value,
                'version': agent.version,
                'status': 'offline',  # Would be updated by health monitoring
                'current_workload': agent.current_workload,
                'max_workload': agent.max_workload,
                'active_tasks': active_tasks,
                'capabilities': [cap.name for cap in agent.capabilities],
                'performance_score': agent.performance_score
            }

            if metrics:
                status['metrics'] = asdict(metrics)

            return status

        except Exception as e:
            logger.error(f"Agent status error: {e}")
            return {}

    async def get_coordinator_metrics(self) -> Dict[str, Any]:
        """Get coordinator metrics"""
        try:
            return {
                'total_agents': len(self.registered_agents),
                'agents_by_type': {
                    agent_type.value: len([a for a in self.registered_agents.values() if a.agent_type == agent_type])
                    for agent_type in AgentType
                },
                'total_tasks': len(self.agent_tasks),
                'tasks_by_status': self._get_task_status_counts(),
                'active_collaborations': len([s for s in self.collaboration_sessions.values() if s['status'] == 'active']),
                'queue_size': self.task_queue.qsize(),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Coordinator metrics error: {e}")
            return {}

    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while not self._shutdown:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Find best agent for task
                best_agent = await self.get_best_agent_for_task(task)
                if best_agent:
                    await self.assign_task(task.task_id, best_agent)
                else:
                    # No suitable agent, put back in queue
                    await asyncio.sleep(5)  # Wait before retrying
                    await self.task_queue.put(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error: {e}")

    async def _monitor_agent_health(self):
        """Monitor agent health"""
        while not self._shutdown:
            try:
                for agent_id in list(self.registered_agents.keys()):
                    await self._check_agent_health(agent_id)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(10)

    async def _monitor_agent(self, agent_id: str):
        """Monitor individual agent"""
        while not self._shutdown and agent_id in self.registered_agents:
            try:
                # Get agent health status
                health = await self._get_agent_health(agent_id)

                # Update agent metrics
                if agent_id in self.agent_metrics:
                    self.agent_metrics[agent_id].last_activity = datetime.now()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Agent monitoring error for {agent_id}: {e}")
                await asyncio.sleep(30)

    async def _validate_agent_definition(self, agent_def: AgentDefinition) -> bool:
        """Validate agent definition"""
        try:
            # Check required fields
            if not agent_def.agent_id or not agent_def.name:
                return False

            if not agent_def.capabilities:
                return False

            # Validate capabilities
            for capability in agent_def.capabilities:
                if not capability.name or not capability.capability_id:
                    return False

            return True

        except Exception:
            return False

    async def _validate_task(self, task: AgentTask) -> bool:
        """Validate task definition"""
        try:
            return bool(task.task_id and task.task_type and task.payload)

        except Exception:
            return False

    async def _register_agent_with_consul(self, agent_def: AgentDefinition):
        """Register agent with Consul"""
        try:
            service_id = f"agent-{agent_def.agent_id}"

            service_data = {
                'ID': service_id,
                'Name': 'dmlogn8n-agent',
                'Tags': [
                    f"agent-type:{agent_def.agent_type.value}",
                    f"version:{agent_def.version}",
                    f"capabilities:{','.join([cap.name for cap in agent_def.capabilities])}"
                ],
                'Address': 'localhost',  # Would be actual agent address
                'Port': 8000,  # Would be actual agent port
                'Meta': {
                    'agent_id': agent_def.agent_id,
                    'agent_name': agent_def.name,
                    'agent_type': agent_def.agent_type.value,
                    'max_workload': str(agent_def.max_workload)
                }
            }

            await self.consul.agent.service.register(**service_data)

        except Exception as e:
            logger.error(f"Consul registration error: {e}")

    async def _can_agent_handle_task(self, agent: AgentDefinition, task: AgentTask) -> bool:
        """Check if agent can handle a task"""
        try:
            # Check workload
            if agent.current_workload >= agent.max_workload:
                return False

            # Check task requirements
            for requirement in task.requirements:
                capability_found = False
                for capability in agent.capabilities:
                    if capability.name == requirement:
                        capability_found = True
                        break
                if not capability_found:
                    return False

            # Check if task type is supported
            if agent.supported_tasks and task.task_type not in agent.supported_tasks:
                return False

            return True

        except Exception:
            return False

    async def _calculate_agent_score(self, agent_id: str, task: AgentTask) -> float:
        """Calculate agent suitability score for task"""
        try:
            agent = self.registered_agents[agent_id]
            metrics = self.agent_metrics.get(agent_id)

            score = 0.0

            # Workload factor (40%)
            workload_factor = 1 - (agent.current_workload / agent.max_workload)
            score += workload_factor * 0.4

            # Performance score (30%)
            score += agent.performance_score * 0.3

            # Success rate (20%)
            if metrics:
                score += metrics.success_rate * 0.2

            # Capability match (10%)
            capability_match = 0
            for requirement in task.requirements:
                for capability in agent.capabilities:
                    if capability.name == requirement:
                        capability_match += 1
                        break
            if task.requirements:
                capability_score = capability_match / len(task.requirements)
                score += capability_score * 0.1

            return score

        except Exception:
            return 0.0

    async def _send_task_to_agent(self, agent_id: str, task: AgentTask):
        """Send task to agent"""
        try:
            # This would involve actual communication with the agent
            # For now, we'll just update status
            task.status = "processing"

            # Store in active tasks
            if agent_id not in self.active_tasks:
                self.active_tasks[agent_id] = set()
            self.active_tasks[agent_id].add(task.task_id)

            # Update agent workload
            self.registered_agents[agent_id].current_workload += 1

        except Exception as e:
            logger.error(f"Task sending error: {e}")

    async def _cancel_agent_task(self, agent_id: str, task_id: str):
        """Cancel task on agent"""
        try:
            # This would involve actual communication with the agent
            # For now, we'll just update state
            pass

        except Exception as e:
            logger.error(f"Agent task cancellation error: {e}")

    async def _update_agent_metrics(self, agent_id: str, success: bool, task: AgentTask):
        """Update agent performance metrics"""
        try:
            if agent_id not in self.agent_metrics:
                return

            metrics = self.agent_metrics[agent_id]

            if success:
                metrics.tasks_completed += 1
            else:
                metrics.tasks_failed += 1

            # Update success rate
            total_tasks = metrics.tasks_completed + metrics.tasks_failed
            if total_tasks > 0:
                metrics.success_rate = metrics.tasks_completed / total_tasks

            # Update workload
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].current_workload = max(
                    0, self.registered_agents[agent_id].current_workload - 1
                )

        except Exception as e:
            logger.error(f"Metrics update error: {e}")

    async def _check_agent_health(self, agent_id: str):
        """Check agent health status"""
        try:
            # This would involve actual health check with the agent
            # For now, we'll simulate health checking
            pass

        except Exception as e:
            logger.error(f"Agent health check error: {e}")

    async def _get_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Get agent health information"""
        try:
            # This would involve actual health check with the agent
            # For now, we'll return default health
            return {
                'status': 'healthy',
                'cpu_usage': 50.0,
                'memory_usage': 60.0,
                'last_heartbeat': datetime.now().isoformat()
            }

        except Exception:
            return {
                'status': 'unknown',
                'cpu_usage': 0,
                'memory_usage': 0,
                'last_heartbeat': None
            }

    async def _notify_agent_collaboration(self, agent_id: str, session_id: str, action: str):
        """Notify agent about collaboration event"""
        try:
            # This would involve actual communication with the agent
            logger.info(f"Agent {agent_id} notified of collaboration {action}: {session_id}")

        except Exception as e:
            logger.error(f"Collaboration notification error: {e}")

    async def _notify_agent_message(self, agent_id: str, session_id: str, message: Dict[str, Any]):
        """Notify agent about collaboration message"""
        try:
            # This would involve actual communication with the agent
            logger.info(f"Agent {agent_id} notified of message in session {session_id}")

        except Exception as e:
            logger.error(f"Message notification error: {e}")

    async def _cleanup_collaboration(self, session_id: str):
        """Clean up collaboration session after delay"""
        try:
            await asyncio.sleep(300)  # Keep for 5 minutes
            if session_id in self.collaboration_sessions:
                del self.collaboration_sessions[session_id]

        except Exception as e:
            logger.error(f"Collaboration cleanup error: {e}")

    def _check_capability_requirements(self, capability: AgentCapability, requirements: Dict[str, Any]) -> bool:
        """Check if capability meets requirements"""
        try:
            for key, value in requirements.items():
                if key not in capability.parameters:
                    return False
                if capability.parameters[key] != value:
                    return False
            return True

        except Exception:
            return False

    def _get_task_status_counts(self) -> Dict[str, int]:
        """Get counts of tasks by status"""
        counts = {}
        for task in self.agent_tasks.values():
            status = task.status
            counts[status] = counts.get(status, 0) + 1
        return counts

    async def _initialize_default_capabilities(self):
        """Initialize default agent capabilities"""
        try:
            # This would set up default capability definitions
            logger.info("Default agent capabilities initialized")

        except Exception as e:
            logger.error(f"Default capabilities initialization error: {e}")

    async def shutdown(self):
        """Shutdown agent coordinator"""
        self._shutdown = True

        # Cancel background tasks
        if self._task_processor_task:
            self._task_processor_task.cancel()

        if self._health_monitor_task:
            self._health_monitor_task.cancel()

        # Wait for tasks to complete
        tasks = [self._task_processor_task, self._health_monitor_task]
        if any(t for t in tasks if t):
            await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)

        logger.info("Agent coordinator shutdown completed")

# Export main classes
__all__ = [
    'AgentCoordinator',
    'AgentDefinition',
    'AgentCapability',
    'AgentTask',
    'AgentMetrics',
    'AgentType',
    'AgentStatus',
    'TaskPriority'
]