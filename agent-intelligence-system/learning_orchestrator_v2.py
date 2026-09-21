#!/usr/bin/env python3
"""
DMlogn8n Advanced Learning Orchestrator v2.0
===========================================

Production-grade orchestration system implementing advanced patterns for coordinating
AI learning processes. Based on AgentDnDengine3.txt research and modern distributed systems patterns.

Key Features:
- Event-driven architecture with message queuing
- Adaptive learning rate scheduling
- Intelligent resource management
- Fault tolerance and graceful degradation
- Real-time performance monitoring
- Predictive scaling and optimization

Author: DMlogn8n Development Team
Version: 2.0.0 Production Ready
"""

import asyncio
import logging
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import weakref
import gc

# External dependencies
import numpy as np
import psutil
import aioredis
from asyncpg import create_pool
import websockets
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Internal imports
from .event_bus import EventBus, Event
from .resource_manager import ResourceManager
from .learning_scheduler import LearningScheduler
from .performance_monitor import PerformanceMonitor
from .fault_tolerance import CircuitBreaker, RetryPolicy

# Configure structured logging
logger = logging.getLogger(__name__)

class LearningMode(Enum):
    """Learning operation modes."""
    NORMAL = "normal"
    INTENSIVE = "intensive"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"

class Priority(Enum):
    """Experience processing priorities."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class Experience:
    """Structured experience data with enhanced metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance tracking
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    processing_duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class LearningTask:
    """Learning task with scheduling and resource requirements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    task_type: str = ""
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Task configuration
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    # Resource requirements
    cpu_required: float = 0.1
    memory_required: int = 100  # MB
    gpu_required: bool = False

    # Status tracking
    status: str = "pending"  # pending, running, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class AdvancedLearningOrchestrator:
    """
    Advanced Learning Orchestrator implementing production-grade patterns.

    This orchestrator uses:
    - Event-driven architecture for loose coupling
    - Priority queues for experience processing
    - Adaptive resource management
    - Circuit breakers for fault tolerance
    - Real-time performance monitoring
    - Predictive scaling based on load patterns
    """

    def __init__(self, config_path: str = "config/orchestrator_v2_config.json"):
        """Initialize the advanced orchestrator."""
        self.config = self._load_config(config_path)
        self.mode = LearningMode.ADAPTIVE

        # Core components
        self.event_bus = EventBus()
        self.resource_manager = ResourceManager(self.config.get('resources', {}))
        self.scheduler = LearningScheduler(self.config.get('scheduling', {}))
        self.performance_monitor = PerformanceMonitor()

        # State management
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_sessions: Dict[str, str] = {}  # agent_id -> session_id
        self.experience_queues: Dict[Priority, asyncio.Queue] = {
            p: asyncio.Queue(maxsize=self.config.get('queue_sizes', {}).get(p.name.lower(), 1000))
            for p in Priority
        }

        # Learning subsystems with circuit breakers
        self.subsystems = {}
        self.circuit_breakers = {}

        # Performance metrics
        self.metrics = {
            'experiences_processed': Counter('dmlogn8n_experiences_processed_total', 'Total experiences processed', ['agent_id', 'type']),
            'processing_duration': Histogram('dmlogn8n_experience_processing_seconds', 'Experience processing duration'),
            'learning_velocity': Gauge('dmlogn8n_learning_velocity', 'Current learning velocity per agent', ['agent_id']),
            'system_load': Gauge('dmlogn8n_system_load_percent', 'Current system load percentage'),
            'active_sessions': Gauge('dmlogn8n_active_sessions', 'Number of active learning sessions'),
        }

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False

        # Optimization data
        self.load_history = deque(maxlen=1000)
        self.performance_patterns = defaultdict(list)
        self.adaptive_thresholds = {
            'consolidation': 10,
            'lora_training': 50,
            'intelligence_update': 100,
        }

        logger.info("Advanced Learning Orchestrator v2.0 initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load enhanced configuration with production defaults."""
        default_config = {
            "mode": "adaptive",
            "max_concurrent_experiences": 100,
            "queue_sizes": {
                "critical": 100,
                "high": 500,
                "normal": 1000,
                "low": 2000,
                "background": 5000
            },
            "processing": {
                "batch_size": 10,
                "batch_timeout": 1.0,
                "max_batch_size": 50,
                "adaptive_batching": True
            },
            "resources": {
                "max_cpu_usage": 80.0,
                "max_memory_usage": 85.0,
                "max_gpu_memory": 90.0,
                "resource_check_interval": 5.0
            },
            "scheduling": {
                "algorithm": "priority_weighted",
                "time_slice_ms": 100,
                "fairness_enabled": True,
                "predictive_scheduling": True
            },
            "fault_tolerance": {
                "circuit_breaker_threshold": 5,
                "circuit_breaker_timeout": 60.0,
                "retry_policy": "exponential_backoff",
                "max_retries": 3
            },
            "monitoring": {
                "prometheus_port": 8090,
                "health_check_interval": 30.0,
                "performance_report_interval": 300.0
            },
            "optimization": {
                "load_prediction_enabled": True,
                "auto_scaling_enabled": True,
                "learning_rate_adaptation": True,
                "memory_optimization": True
            },
            "dashboard": {
                "websocket_url": "ws://localhost:8001/ws",
                "real_time_updates": True,
                "update_buffer_size": 100
            }
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                return self._deep_merge(default_config, config)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Create default config
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def initialize(self):
        """Initialize all components and subsystems."""
        try:
            logger.info("Initializing Advanced Learning Orchestrator...")

            # Start Prometheus metrics server
            start_http_server(self.config["monitoring"]["prometheus_port"])
            logger.info(f"✓ Prometheus metrics server started on port {self.config['monitoring']['prometheus_port']}")

            # Initialize Redis for distributed coordination
            self.redis = await aioredis.create_redis_pool(
                self.config.get('redis_url', 'redis://localhost')
            )
            logger.info("✓ Redis connection established")

            # Initialize PostgreSQL for persistent storage
            self.db_pool = await create_pool(
                self.config.get('database_url', 'postgresql://localhost/dmlogn8n')
            )
            logger.info("✓ Database connection pool created")

            # Initialize learning subsystems with circuit breakers
            await self._initialize_subsystems()

            # Start background processing tasks
            await self._start_background_tasks()

            # Load existing agent states
            await self._load_agent_states()

            self.is_running = True
            logger.info("✅ Advanced Learning Orchestrator fully initialized and running!")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def _initialize_subsystems(self):
        """Initialize all learning subsystems with fault tolerance."""
        subsystem_configs = {
            'memory_manager': {
                'module': 'memory_architecture.memory_manager',
                'class': 'MemoryManager',
                'circuit_breaker_threshold': 3
            },
            'skill_system': {
                'module': 'skill_development.skill_system',
                'class': 'SkillSystem',
                'circuit_breaker_threshold': 5
            },
            'lora_trainer': {
                'module': 'lora_adaptation.personalized_model_manager',
                'class': 'PersonalizedModelManager',
                'circuit_breaker_threshold': 2,
                'resource_intensive': True
            },
            'intelligence_analyzer': {
                'module': 'intelligence_analyzer',
                'class': 'IntelligenceAnalyzer',
                'circuit_breaker_threshold': 3
            }
        }

        for name, config in subsystem_configs.items():
            try:
                # Import subsystem
                module = __import__(config['module'], fromlist=[config['class']])
                subsystem_class = getattr(module, config['class'])

                # Initialize with resource allocation
                if config.get('resource_intensive'):
                    await self.resource_manager.allocate_resources(
                        name, cpu=0.5, memory=2048, gpu=True
                    )

                # Create subsystem instance
                self.subsystems[name] = subsystem_class()

                # Create circuit breaker
                self.circuit_breakers[name] = CircuitBreaker(
                    failure_threshold=config['circuit_breaker_threshold'],
                    timeout=self.config['fault_tolerance']['circuit_breaker_timeout']
                )

                logger.info(f"✓ {name} initialized with circuit breaker")

            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                # Continue without this subsystem - graceful degradation

    async def _start_background_tasks(self):
        """Start all background processing tasks."""
        tasks = [
            self._process_experiences(),
            self._schedule_learning_tasks(),
            self._monitor_system_performance(),
            self._optimize_resources(),
            self._generate_performance_reports(),
            self._handle_events(),
            self._cleanup_resources(),
            self._predictive_scaling()
        ]

        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

    async def start_agent_session(self, agent_id: str, context: Dict[str, Any]) -> str:
        """Start a learning session with enhanced initialization."""
        session_id = str(uuid.uuid4())

        # Initialize or update agent state
        if agent_id not in self.active_agents:
            self.active_agents[agent_id] = {
                'session_id': session_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'total_experiences': 0,
                'learning_velocity': 0.0,
                'intelligence_score': 100.0,
                'specializations': [],
                'performance_metrics': {},
                'adaptive_thresholds': self.adaptive_thresholds.copy(),
                'context': context
            }

        self.agent_sessions[agent_id] = session_id

        # Publish event
        await self.event_bus.publish(Event(
            type='session_started',
            data={
                'agent_id': agent_id,
                'session_id': session_id,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
        ))

        # Update metrics
        self.metrics['active_sessions'].inc()

        logger.info(f"Started learning session for agent {agent_id}: {session_id}")
        return session_id

    async def process_experience(self, experience_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process experience with advanced queuing and priority handling.
        """
        # Create structured experience
        experience = Experience(
            agent_id=experience_data.get('agent_id', ''),
            type=experience_data.get('type', 'unknown'),
            data=experience_data,
            context=experience_data.get('context', {}),
            priority=self._determine_priority(experience_data)
        )

        # Add to appropriate priority queue
        try:
            queue = self.experience_queues[experience.priority]
            queue.put_nowait(experience)
        except asyncio.QueueFull:
            # Handle queue overflow
            await self._handle_queue_overflow(experience)

        # Return acknowledgment
        return {
            'experience_id': experience.id,
            'status': 'queued',
            'priority': experience.priority.name,
            'queue_size': queue.qsize()
        }

    def _determine_priority(self, experience_data: Dict[str, Any]) -> Priority:
        """Determine experience priority based on content and context."""
        importance = experience_data.get('importance', 0.5)
        is_critical = experience_data.get('type') in ['critical_event', 'level_up', 'death']
        is_combat = experience_data.get('type') == 'combat'
        is_social = experience_data.get('type') == 'dialogue'

        if is_critical or importance > 0.9:
            return Priority.CRITICAL
        elif is_combat or importance > 0.7:
            return Priority.HIGH
        elif is_social or importance > 0.5:
            return Priority.NORMAL
        elif importance > 0.3:
            return Priority.LOW
        else:
            return Priority.BACKGROUND

    async def _process_experiences(self):
        """Main experience processing loop with adaptive batching."""
        while self.is_running:
            try:
                # Check system resources
                if not await self.resource_manager.check_availability():
                    await asyncio.sleep(0.1)
                    continue

                # Collect batch from priority queues
                batch = []
                batch_start_time = time.time()

                # Process queues in priority order
                for priority in Priority:
                    queue = self.experience_queues[priority]
                    batch_size = self._calculate_adaptive_batch_size()

                    while len(batch) < batch_size and not queue.empty():
                        try:
                            experience = queue.get_nowait()
                            experience.processing_started = datetime.now()
                            batch.append(experience)
                        except asyncio.QueueEmpty:
                            break

                    if len(batch) >= batch_size:
                        break

                # Process batch if we have items
                if batch:
                    await self._process_experience_batch(batch)

                # Adaptive sleep based on load
                await self._adaptive_sleep(time.time() - batch_start_time)

            except Exception as e:
                logger.error(f"Error in experience processing loop: {e}")
                await asyncio.sleep(1.0)

    async def _process_experience_batch(self, batch: List[Experience]):
        """Process a batch of experiences concurrently."""
        start_time = time.time()

        # Group experiences by agent for efficiency
        agent_batches = defaultdict(list)
        for exp in batch:
            agent_batches[exp.agent_id].append(exp)

        # Process each agent's experiences
        tasks = []
        for agent_id, experiences in agent_batches.items():
            task = asyncio.create_task(
                self._process_agent_experiences(agent_id, experiences)
            )
            tasks.append(task)

        # Wait for all processing to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update metrics
        processing_time = time.time() - start_time
        self.metrics['processing_duration'].observe(processing_time)

        for exp in batch:
            exp.processing_completed = datetime.now()
            exp.processing_duration = (
                exp.processing_completed - exp.processing_started
            ).total_seconds()

            if exp.success:
                self.metrics['experiences_processed'].labels(
                    agent_id=exp.agent_id,
                    type=exp.type
                ).inc()

        logger.debug(f"Processed batch of {len(batch)} experiences in {processing_time:.3f}s")

    async def _process_agent_experiences(self, agent_id: str, experiences: List[Experience]) -> Dict[str, Any]:
        """Process experiences for a single agent through all subsystems."""
        agent_state = self.active_agents.get(agent_id, {})
        results = {
            'agent_id': agent_id,
            'experiences_count': len(experiences),
            'memory_effects': [],
            'skill_effects': [],
            'lora_effects': None,
            'intelligence_delta': 0.0,
            'errors': []
        }

        # Update agent activity
        agent_state['last_activity'] = datetime.now()
        agent_state['total_experiences'] += len(experiences)

        try:
            # Process through memory system
            if 'memory_manager' in self.subsystems:
                async with self.circuit_breakers['memory_manager'].protect():
                    memory_results = await self._process_memory_experiences(agent_id, experiences)
                    results['memory_effects'] = memory_results

            # Process through skill system
            if 'skill_system' in self.subsystems:
                async with self.circuit_breakers['skill_system'].protect():
                    skill_results = await self._process_skill_experiences(agent_id, experiences)
                    results['skill_effects'] = skill_results

            # Check for LoRA training trigger
            if self._should_trigger_lora_training(agent_id, experiences):
                await self._schedule_lora_training(agent_id, experiences)

            # Check for consolidation trigger
            if self._should_trigger_consolidation(agent_id, experiences):
                await self._schedule_memory_consolidation(agent_id)

            # Update intelligence metrics
            intelligence_delta = await self._update_intelligence_metrics(agent_id, experiences)
            results['intelligence_delta'] = intelligence_delta

            # Update learning velocity
            self._update_learning_velocity(agent_id, intelligence_delta)

            # Publish completion event
            await self.event_bus.publish(Event(
                type='experiences_processed',
                data=results
            ))

        except Exception as e:
            logger.error(f"Error processing experiences for agent {agent_id}: {e}")
            results['errors'].append(str(e))

            # Mark experiences as failed
            for exp in experiences:
                exp.success = False
                exp.error_message = str(e)

        return results

    async def _process_memory_experiences(self, agent_id: str, experiences: List[Experience]) -> List[Dict[str, Any]]:
        """Process experiences through memory system."""
        results = []
        memory_manager = self.subsystems['memory_manager']

        for exp in experiences:
            try:
                memory_data = {
                    'experience_id': exp.id,
                    'type': exp.type,
                    'data': exp.data,
                    'context': exp.context,
                    'importance': exp.data.get('importance', 0.5),
                    'timestamp': exp.timestamp
                }

                # Store in working memory
                memory_id = await memory_manager.store_memory(agent_id, memory_data, 'working')

                results.append({
                    'experience_id': exp.id,
                    'memory_id': memory_id,
                    'memory_type': 'working',
                    'status': 'stored'
                })

            except Exception as e:
                logger.warning(f"Failed to store memory for {exp.id}: {e}")
                results.append({
                    'experience_id': exp.id,
                    'error': str(e),
                    'status': 'failed'
                })

        return results

    async def _process_skill_experiences(self, agent_id: str, experiences: List[Experience]) -> List[Dict[str, Any]]:
        """Process experiences through skill system."""
        results = []
        skill_system = self.subsystems['skill_system']

        for exp in experiences:
            try:
                skills_used = exp.data.get('skills_used', [])
                success = exp.data.get('success', False)
                difficulty = exp.data.get('difficulty', 0.5)

                for skill_name in skills_used:
                    # Calculate XP with context bonuses
                    xp_gained = skill_system.calculate_xp(
                        base_xp=10,
                        success_multiplier=2.0 if success else 0.5,
                        difficulty_multiplier=1.0 + difficulty,
                        context_bonus=self._calculate_context_bonus(exp.context)
                    )

                    # Award XP
                    result = await skill_system.award_xp(agent_id, skill_name, xp_gained)
                    results.append(result)

            except Exception as e:
                logger.warning(f"Failed to process skills for {exp.id}: {e}")
                results.append({
                    'experience_id': exp.id,
                    'error': str(e),
                    'status': 'failed'
                })

        return results

    def _calculate_adaptive_batch_size(self) -> int:
        """Calculate adaptive batch size based on system load."""
        if not self.config['processing']['adaptive_batching']:
            return self.config['processing']['batch_size']

        # Get current system load
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        # Adjust batch size based on load
        base_size = self.config['processing']['batch_size']
        max_size = self.config['processing']['max_batch_size']

        if cpu_percent < 50 and memory_percent < 70:
            # Low load - increase batch size
            return min(max_size, base_size * 2)
        elif cpu_percent > 80 or memory_percent > 85:
            # High load - decrease batch size
            return max(1, base_size // 2)
        else:
            # Medium load - use base size
            return base_size

    async def _adaptive_sleep(self, processing_time: float):
        """Adaptive sleep based on processing time and queue sizes."""
        # Check queue pressure
        total_queued = sum(q.qsize() for q in self.experience_queues.values())

        if total_queued > 1000:
            # High pressure - minimal sleep
            await asyncio.sleep(0.01)
        elif processing_time > 1.0:
            # Slow processing - give system time to recover
            await asyncio.sleep(0.1)
        else:
            # Normal operation
            await asyncio.sleep(0.05)

    async def _monitor_system_performance(self):
        """Monitor system performance and adjust parameters."""
        interval = self.config['monitoring']['health_check_interval']

        while self.is_running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent

                # Update Prometheus metrics
                self.metrics['system_load'].set(cpu_percent)

                # Store in history for pattern analysis
                self.load_history.append({
                    'timestamp': time.time(),
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'queue_sizes': {p.name: q.qsize() for p, q in self.experience_queues.items()}
                })

                # Detect performance patterns
                await self._analyze_performance_patterns()

                # Trigger alerts if needed
                if cpu_percent > 90:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                    await self._handle_high_load('cpu', cpu_percent)

                if memory_percent > 90:
                    logger.warning(f"High memory usage: {memory_percent}%")
                    await self._handle_high_load('memory', memory_percent)

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(interval)

    async def _optimize_resources(self):
        """Optimize resource allocation and cleanup."""
        while self.is_running:
            try:
                # Garbage collection
                if self.config['optimization']['memory_optimization']:
                    gc.collect()

                # Optimize Redis memory
                await self.redis.execute_command('MEMORY', 'PURGE')

                # Close idle database connections
                # (Handled by connection pool)

                # Adjust adaptive thresholds based on performance
                await self._adjust_adaptive_thresholds()

                await asyncio.sleep(60)  # Run every minute

            except Exception as e:
                logger.error(f"Error in resource optimization: {e}")
                await asyncio.sleep(60)

    async def shutdown(self):
        """Gracefully shutdown the orchestrator."""
        logger.info("Shutting down Advanced Learning Orchestrator...")

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close subsystems
        for name, subsystem in self.subsystems.items():
            try:
                if hasattr(subsystem, 'shutdown'):
                    await subsystem.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name}: {e}")

        # Close connections
        if hasattr(self, 'redis'):
            self.redis.close()
            await self.redis.wait_closed()

        if hasattr(self, 'db_pool'):
            await self.db_pool.close()

        logger.info("✅ Advanced Learning Orchestrator shutdown complete")

# Additional utility classes and functions
class EventBus:
    """Event bus for loose coupling between components."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue = asyncio.Queue(maxsize=10000)
        self._running = False

    async def publish(self, event: Event):
        """Publish an event to all subscribers."""
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")

    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to events of a specific type."""
        self._subscribers[event_type].append(handler)

    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                handlers = self._subscribers.get(event.type, [])

                # Notify all handlers concurrently
                tasks = [handler(event) for handler in handlers]
                await asyncio.gather(*tasks, return_exceptions=True)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

@dataclass
class Event:
    """Event data structure."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

# Main execution
async def main():
    """Main execution function."""
    orchestrator = AdvancedLearningOrchestrator()

    try:
        await orchestrator.initialize()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())