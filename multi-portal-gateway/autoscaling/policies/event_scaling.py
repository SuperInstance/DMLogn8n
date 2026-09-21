#!/usr/bin/env python3
"""
Event-driven Scaling for DMLogn8n Auto-Scaling
Handles scaling based on system events and triggers
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import redis
import aiohttp
from collections import defaultdict

from ..autoscaler import ScalingDecision, ScaleDirection

class EventType(Enum):
    TRAFFIC_SPIKE = "traffic_spike"
    SERVICE_FAILURE = "service_failure"
    DATABASE_OVERLOAD = "database_overload"
    QUEUE_OVERFLOW = "queue_overflow"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_PRESSURE = "cpu_pressure"
    DISK_SPACE = "disk_space"
    NETWORK_LATENCY = "network_latency"
    GAME_EVENT = "game_event"
    MAINTENANCE_MODE = "maintenance_mode"
    EMERGENCY_SCALE = "emergency_scale"
    COST_ALERT = "cost_alert"
    USER_SURGE = "user_surge"

class EventSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ScalingAction(Enum):
    SCALE_UP_IMMEDIATE = "scale_up_immediate"
    SCALE_UP_GRADUAL = "scale_up_gradual"
    SCALE_DOWN_SAFE = "scale_down_safe"
    SCALE_DOWN_IMMEDIATE = "scale_down_immediate"
    SCALE_TO_MAX = "scale_to_max"
    SCALE_TO_MIN = "scale_to_min"
    CANCEL_SCALING = "cancel_scaling"
    PAUSE_SCALING = "pause_scaling"
    RESUME_SCALING = "resume_scaling"

@dataclass
class EventTrigger:
    trigger_id: str
    name: str
    event_type: EventType
    severity: EventSeverity
    condition: str  # Python expression to evaluate
    action: ScalingAction
    target_services: List[str]
    scale_factor: Optional[float]
    target_instances: Optional[int]
    cooldown_seconds: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    description: str = ""

@dataclass
class SystemEvent:
    event_id: str
    event_type: EventType
    severity: EventSeverity
    source_service: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    triggered_actions: List[str] = None

@dataclass
class EventScalingExecution:
    execution_id: str
    trigger_id: str
    event_id: str
    service_id: str
    action: ScalingAction
    original_instances: int
    target_instances: int
    executed_at: datetime
    status: str
    duration_seconds: float
    error_message: Optional[str] = None

class EventScalingManager:
    """
    Manages event-driven auto-scaling
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('event_scaling')

        # Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Event storage
        self.event_triggers: Dict[str, EventTrigger] = {}
        self.system_events: List[SystemEvent] = []
        self.executions: List[EventScalingExecution] = []

        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.condition_evaluators: Dict[str, Callable] = {}

        # Event streams
        self.event_streams: Dict[str, Any] = {}

        # Load default triggers and setup handlers
        self._load_default_triggers()
        self._setup_event_handlers()
        self._load_triggers_from_redis()

    def _load_default_triggers(self):
        """Load default event-driven scaling triggers"""
        try:
            default_triggers = [
                # Traffic spike handling
                EventTrigger(
                    trigger_id="traffic-spike-response",
                    name="Traffic Spike Response",
                    event_type=EventType.TRAFFIC_SPIKE,
                    severity=EventSeverity.HIGH,
                    condition="event_data.get('requests_per_second', 0) > 1000",
                    action=ScalingAction.SCALE_UP_IMMEDIATE,
                    target_services=["api-gateway", "character-portal"],
                    scale_factor=1.5,
                    target_instances=None,
                    cooldown_seconds=300,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Immediate scale up for traffic spikes"
                ),

                # Service failure handling
                EventTrigger(
                    trigger_id="service-failure-recovery",
                    name="Service Failure Recovery",
                    event_type=EventType.SERVICE_FAILURE,
                    severity=EventSeverity.CRITICAL,
                    condition="event_data.get('failure_rate', 0) > 50",
                    action=ScalingAction.SCALE_UP_IMMEDIATE,
                    target_services=["api-gateway", "character-portal"],
                    scale_factor=2.0,
                    target_instances=None,
                    cooldown_seconds=600,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up to compensate for service failures"
                ),

                # Database overload
                EventTrigger(
                    trigger_id="database-overload-response",
                    name="Database Overload Response",
                    event_type=EventType.DATABASE_OVERLOAD,
                    severity=EventSeverity.HIGH,
                    condition="event_data.get('connection_pool_usage', 0) > 90",
                    action=ScalingAction.SCALE_UP_GRADUAL,
                    target_services=["database"],
                    scale_factor=1.2,
                    target_instances=None,
                    cooldown_seconds=900,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Gradual scale up for database overload"
                ),

                # Queue overflow handling
                EventTrigger(
                    trigger_id="queue-overflow-response",
                    name="Message Queue Overflow Response",
                    event_type=EventType.QUEUE_OVERFLOW,
                    severity=EventSeverity.MEDIUM,
                    condition="event_data.get('queue_depth', 0) > 1000",
                    action=ScalingAction.SCALE_UP_GRADUAL,
                    target_services=["dialogue-system", "combat-engine"],
                    scale_factor=1.3,
                    target_instances=None,
                    cooldown_seconds=300,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up consumers for queue overflow"
                ),

                # Memory pressure emergency
                EventTrigger(
                    trigger_id="memory-pressure-emergency",
                    name="Memory Pressure Emergency",
                    event_type=EventType.MEMORY_PRESSURE,
                    severity=EventSeverity.CRITICAL,
                    condition="event_data.get('memory_usage', 0) > 95",
                    action=ScalingAction.SCALE_TO_MAX,
                    target_services=["character-portal", "world-simulation"],
                    scale_factor=None,
                    target_instances=None,
                    cooldown_seconds=180,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Emergency scale to max for memory pressure"
                ),

                # Game event scaling
                EventTrigger(
                    trigger_id="game-event-scaling",
                    name="Game Event Scaling",
                    event_type=EventType.GAME_EVENT,
                    severity=EventSeverity.MEDIUM,
                    condition="event_data.get('event_type') == 'boss_battle'",
                    action=ScalingAction.SCALE_TO_MAX,
                    target_services=["combat-engine", "dialogue-system"],
                    scale_factor=None,
                    target_instances=None,
                    cooldown_seconds=1200,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale to max for special game events"
                ),

                # Maintenance mode
                EventTrigger(
                    trigger_id="maintenance-mode-scaling",
                    name="Maintenance Mode Scaling",
                    event_type=EventType.MAINTENANCE_MODE,
                    severity=EventSeverity.LOW,
                    condition="event_data.get('maintenance') == True",
                    action=ScalingAction.SCALE_TO_MIN,
                    target_services=["api-gateway", "character-portal"],
                    scale_factor=None,
                    target_instances=1,
                    cooldown_seconds=3600,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale to minimum during maintenance"
                ),

                # Emergency scale down
                EventTrigger(
                    trigger_id="emergency-scale-down",
                    name="Emergency Scale Down",
                    event_type=EventType.EMERGENCY_SCALE,
                    severity=EventSeverity.CRITICAL,
                    condition="event_data.get('emergency_type') == 'cost_crisis'",
                    action=ScalingAction.SCALE_TO_MIN,
                    target_services=["world-simulation", "combat-engine"],
                    scale_factor=None,
                    target_instances=1,
                    cooldown_seconds=1800,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Emergency scale down for cost crisis"
                ),

                # Cost alert response
                EventTrigger(
                    trigger_id="cost-alert-response",
                    name="Cost Alert Response",
                    event_type=EventType.COST_ALERT,
                    severity=EventSeverity.MEDIUM,
                    condition="event_data.get('hourly_cost', 0) > 500",
                    action=ScalingAction.SCALE_DOWN_SAFE,
                    target_services=["ai-model-pool", "world-simulation"],
                    scale_factor=0.8,
                    target_instances=None,
                    cooldown_seconds=1800,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale down when cost threshold exceeded"
                ),

                # User surge response
                EventTrigger(
                    trigger_id="user-surge-response",
                    name="User Surge Response",
                    event_type=EventType.USER_SURGE,
                    severity=EventSeverity.HIGH,
                    condition="event_data.get('active_users', 0) > 10000",
                    action=ScalingAction.SCALE_UP_IMMEDIATE,
                    target_services=["api-gateway", "character-portal", "dialogue-system"],
                    scale_factor=2.0,
                    target_instances=None,
                    cooldown_seconds=600,
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Immediate scale up for user surge"
                )
            ]

            for trigger in default_triggers:
                self.event_triggers[trigger.trigger_id] = trigger

            self.logger.info(f"Loaded {len(default_triggers)} default event triggers")

        except Exception as e:
            self.logger.error(f"Error loading default triggers: {e}")

    def _setup_event_handlers(self):
        """Setup event handlers for different event types"""
        try:
            # Register condition evaluators
            self.condition_evaluators['traffic_spike'] = self._evaluate_traffic_spike
            self.condition_evaluators['service_failure'] = self._evaluate_service_failure
            self.condition_evaluators['database_overload'] = self._evaluate_database_overload
            self.condition_evaluators['queue_overflow'] = self._evaluate_queue_overflow
            self.condition_evaluators['memory_pressure'] = self._evaluate_memory_pressure
            self.condition_evaluators['game_event'] = self._evaluate_game_event
            self.condition_evaluators['maintenance_mode'] = self._evaluate_maintenance_mode
            self.condition_evaluators['emergency_scale'] = self._evaluate_emergency_scale
            self.condition_evaluators['cost_alert'] = self._evaluate_cost_alert
            self.condition_evaluators['user_surge'] = self._evaluate_user_surge

            self.logger.info("Setup event handlers and condition evaluators")

        except Exception as e:
            self.logger.error(f"Error setting up event handlers: {e}")

    def _load_triggers_from_redis(self):
        """Load event triggers from Redis"""
        try:
            trigger_keys = self.redis_client.keys('event_trigger:*')
            for key in trigger_keys:
                trigger_data = json.loads(self.redis_client.get(key))
                trigger_data['created_at'] = datetime.fromisoformat(trigger_data['created_at'])
                trigger_data['updated_at'] = datetime.fromisoformat(trigger_data['updated_at'])
                trigger_data['event_type'] = EventType(trigger_data['event_type'])
                trigger_data['severity'] = EventSeverity(trigger_data['severity'])
                trigger_data['action'] = ScalingAction(trigger_data['action'])

                trigger = EventTrigger(**trigger_data)
                self.event_triggers[trigger.trigger_id] = trigger

            self.logger.info(f"Loaded {len(trigger_keys)} event triggers from Redis")

        except Exception as e:
            self.logger.error(f"Error loading triggers from Redis: {e}")

    async def start_event_processor(self):
        """Start the event processing loop"""
        self.logger.info("Starting event-driven scaling manager...")

        # Start event listener tasks
        tasks = [
            asyncio.create_task(self._monitor_system_events()),
            asyncio.create_task(self._process_event_queue()),
            asyncio.create_task(self._monitor_external_events()),
            asyncio.create_task(self._cleanup_old_events())
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in event processor: {e}")

    async def _monitor_system_events(self):
        """Monitor system for events"""
        while True:
            try:
                # Check various system metrics for event conditions
                await self._check_system_metrics()
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring system events: {e}")
                await asyncio.sleep(10)

    async def _process_event_queue(self):
        """Process events from Redis queue"""
        while True:
            try:
                # Get event from Redis queue
                event_data = self.redis_client.brpop('event_queue', timeout=5)
                if event_data:
                    event_json = event_data[1]
                    event_dict = json.loads(event_json)

                    event = SystemEvent(
                        event_id=event_dict['event_id'],
                        event_type=EventType(event_dict['event_type']),
                        severity=EventSeverity(event_dict['severity']),
                        source_service=event_dict['source_service'],
                        message=event_dict['message'],
                        data=event_dict['data'],
                        timestamp=datetime.fromisoformat(event_dict['timestamp']),
                        processed=event_dict.get('processed', False),
                        triggered_actions=event_dict.get('triggered_actions', [])
                    )

                    await self._process_event(event)

            except Exception as e:
                self.logger.error(f"Error processing event queue: {e}")
                await asyncio.sleep(5)

    async def _monitor_external_events(self):
        """Monitor external event sources"""
        while True:
            try:
                # Monitor external services for events
                await self._check_webhook_events()
                await self._check_alert_manager_events()
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error monitoring external events: {e}")
                await asyncio.sleep(30)

    async def _cleanup_old_events(self):
        """Clean up old events and executions"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)

                # Clean old events
                self.system_events = [
                    event for event in self.system_events
                    if event.timestamp > cutoff_time
                ]

                # Clean old executions
                self.executions = [
                    execution for execution in self.executions
                    if execution.executed_at > cutoff_time
                ]

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                self.logger.error(f"Error cleaning up old events: {e}")
                await asyncio.sleep(300)

    async def _check_system_metrics(self):
        """Check system metrics for event conditions"""
        try:
            # This would typically monitor actual system metrics
            # For demonstration, we'll simulate some metric checks

            # Simulate traffic spike detection
            if await self._detect_traffic_spike():
                await self._create_event(
                    EventType.TRAFFIC_SPIKE,
                    EventSeverity.HIGH,
                    "system-monitor",
                    "Traffic spike detected",
                    {"requests_per_second": 1500, "source": "api-gateway"}
                )

            # Simulate memory pressure detection
            if await self._detect_memory_pressure():
                await self._create_event(
                    EventType.MEMORY_PRESSURE,
                    EventSeverity.CRITICAL,
                    "system-monitor",
                    "Memory pressure detected",
                    {"memory_usage": 96, "service": "character-portal"}
                )

        except Exception as e:
            self.logger.error(f"Error checking system metrics: {e}")

    async def _detect_traffic_spike(self) -> bool:
        """Detect traffic spike conditions"""
        # This would check actual metrics
        # For demo, return False (no spike detected)
        return False

    async def _detect_memory_pressure(self) -> bool:
        """Detect memory pressure conditions"""
        # This would check actual memory metrics
        # For demo, return False (no pressure detected)
        return False

    async def _check_webhook_events(self):
        """Check for webhook events"""
        try:
            # Check Redis for webhook events
            webhook_events = self.redis_client.lrange('webhook_events', 0, -1)
            for event_json in webhook_events:
                event_data = json.loads(event_json)
                await self._create_event(
                    EventType(event_data['type']),
                    EventSeverity(event_data['severity']),
                    event_data['source'],
                    event_data['message'],
                    event_data.get('data', {})
                )

            # Clear processed webhook events
            if webhook_events:
                self.redis_client.ltrim('webhook_events', 0, -len(webhook_events) - 1)

        except Exception as e:
            self.logger.error(f"Error checking webhook events: {e}")

    async def _check_alert_manager_events(self):
        """Check alert manager for events"""
        try:
            # This would integrate with alert manager like Prometheus Alertmanager
            # For now, check Redis for alerts
            alerts = self.redis_client.keys('alert:*')
            for alert_key in alerts:
                alert_data = json.loads(self.redis_client.get(alert_key))
                if alert_data.get('status') == 'firing':
                    await self._create_event(
                        EventType.TRAFFIC_SPIKE if 'traffic' in alert_key else EventType.SERVICE_FAILURE,
                        EventSeverity.HIGH,
                        alert_data['labels'].get('service', 'unknown'),
                        alert_data['annotations'].get('summary', 'Alert fired'),
                        {'alert_data': alert_data}
                    )

        except Exception as e:
            self.logger.error(f"Error checking alert manager events: {e}")

    async def _create_event(self, event_type: EventType, severity: EventSeverity, source: str, message: str, data: Dict[str, Any]):
        """Create a new system event"""
        try:
            event = SystemEvent(
                event_id=f"event-{int(datetime.now().timestamp())}",
                event_type=event_type,
                severity=severity,
                source_service=source,
                message=message,
                data=data,
                timestamp=datetime.now(),
                processed=False,
                triggered_actions=[]
            )

            # Store event
            self.system_events.append(event)

            # Add to Redis queue for processing
            event_dict = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'severity': event.severity.value,
                'source_service': event.source_service,
                'message': event.message,
                'data': event.data,
                'timestamp': event.timestamp.isoformat(),
                'processed': event.processed,
                'triggered_actions': event.triggered_actions
            }

            self.redis_client.lpush('event_queue', json.dumps(event_dict))

            self.logger.info(f"Created event: {event.event_type.value} - {message}")

        except Exception as e:
            self.logger.error(f"Error creating event: {e}")

    async def _process_event(self, event: SystemEvent):
        """Process a system event and trigger actions"""
        try:
            self.logger.info(f"Processing event: {event.event_id} - {event.message}")

            # Find matching triggers
            matching_triggers = []
            for trigger in self.event_triggers.values():
                if not trigger.enabled:
                    continue

                if (trigger.event_type == event.event_type and
                    await self._evaluate_trigger_condition(trigger, event)):
                    matching_triggers.append(trigger)

            # Execute triggered actions
            for trigger in matching_triggers:
                # Check cooldown
                if await self._is_trigger_in_cooldown(trigger):
                    continue

                # Execute scaling actions
                for service_id in trigger.target_services:
                    await self._execute_event_scaling_action(trigger, service_id, event)

                # Update event
                event.triggered_actions.append(trigger.trigger_id)

            # Mark event as processed
            event.processed = True

            # Store in Redis
            await self._store_processed_event(event)

        except Exception as e:
            self.logger.error(f"Error processing event {event.event_id}: {e}")

    async def _evaluate_trigger_condition(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate if trigger condition matches event"""
        try:
            # Use custom condition evaluator if available
            if trigger.event_type.value in self.condition_evaluators:
                evaluator = self.condition_evaluators[trigger.event_type.value]
                return await evaluator(trigger, event)

            # Default evaluation using Python expression
            event_data = event.data
            return eval(trigger.condition, {"event_data": event_data})

        except Exception as e:
            self.logger.error(f"Error evaluating trigger condition: {e}")
            return False

    # Condition evaluator implementations
    async def _evaluate_traffic_spike(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate traffic spike condition"""
        requests_per_sec = event.data.get('requests_per_second', 0)
        return requests_per_sec > 1000

    async def _evaluate_service_failure(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate service failure condition"""
        failure_rate = event.data.get('failure_rate', 0)
        return failure_rate > 50

    async def _evaluate_database_overload(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate database overload condition"""
        connection_usage = event.data.get('connection_pool_usage', 0)
        return connection_usage > 90

    async def _evaluate_queue_overflow(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate queue overflow condition"""
        queue_depth = event.data.get('queue_depth', 0)
        return queue_depth > 1000

    async def _evaluate_memory_pressure(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate memory pressure condition"""
        memory_usage = event.data.get('memory_usage', 0)
        return memory_usage > 95

    async def _evaluate_game_event(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate game event condition"""
        event_type = event.data.get('event_type', '')
        return event_type == 'boss_battle'

    async def _evaluate_maintenance_mode(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate maintenance mode condition"""
        return event.data.get('maintenance', False)

    async def _evaluate_emergency_scale(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate emergency scale condition"""
        emergency_type = event.data.get('emergency_type', '')
        return emergency_type == 'cost_crisis'

    async def _evaluate_cost_alert(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate cost alert condition"""
        hourly_cost = event.data.get('hourly_cost', 0)
        return hourly_cost > 500

    async def _evaluate_user_surge(self, trigger: EventTrigger, event: SystemEvent) -> bool:
        """Evaluate user surge condition"""
        active_users = event.data.get('active_users', 0)
        return active_users > 10000

    async def _is_trigger_in_cooldown(self, trigger: EventTrigger) -> bool:
        """Check if trigger is in cooldown period"""
        try:
            cooldown_key = f"trigger_cooldown:{trigger.trigger_id}"
            return self.redis_client.exists(cooldown_key)

        except Exception as e:
            self.logger.error(f"Error checking trigger cooldown: {e}")
            return False

    async def _execute_event_scaling_action(self, trigger: EventTrigger, service_id: str, event: SystemEvent):
        """Execute scaling action triggered by event"""
        try:
            execution_id = f"exec-{int(datetime.now().timestamp())}"
            start_time = datetime.now()

            # Get current instances
            current_instances = await self._get_current_instances(service_id)

            # Calculate target instances based on action
            target_instances = await self._calculate_target_instances(
                trigger.action, current_instances, trigger.scale_factor, trigger.target_instances
            )

            # Execute scaling
            success = await self._perform_scaling(service_id, current_instances, target_instances)

            execution_time = (datetime.now() - start_time).total_seconds()

            execution = EventScalingExecution(
                execution_id=execution_id,
                trigger_id=trigger.trigger_id,
                event_id=event.event_id,
                service_id=service_id,
                action=trigger.action,
                original_instances=current_instances,
                target_instances=target_instances,
                executed_at=start_time,
                status="success" if success else "failed",
                duration_seconds=execution_time,
                error_message=None if success else "Scaling failed"
            )

            self.executions.append(execution)
            await self._store_execution(execution)

            # Set cooldown
            cooldown_key = f"trigger_cooldown:{trigger.trigger_id}"
            self.redis_client.setex(cooldown_key, trigger.cooldown_seconds, "1")

            self.logger.info(
                f"Event scaling executed: {service_id} {current_instances}->{target_instances} "
                f"by trigger {trigger.trigger_id}"
            )

        except Exception as e:
            self.logger.error(f"Error executing event scaling action: {e}")

    async def _calculate_target_instances(self, action: ScalingAction, current: int, scale_factor: Optional[float], target: Optional[int]) -> int:
        """Calculate target instances based on action"""
        try:
            if action == ScalingAction.SCALE_UP_IMMEDIATE:
                return current + 2
            elif action == ScalingAction.SCALE_UP_GRADUAL:
                return current + 1
            elif action == ScalingAction.SCALE_DOWN_SAFE:
                return max(1, current - 1)
            elif action == ScalingAction.SCALE_DOWN_IMMEDIATE:
                return max(1, current - 2)
            elif action == ScalingAction.SCALE_TO_MAX:
                return await self._get_max_instances("unknown")  # Would need service_id
            elif action == ScalingAction.SCALE_TO_MIN:
                return 1
            elif scale_factor:
                return max(1, int(current * scale_factor))
            elif target:
                return target
            else:
                return current

        except Exception as e:
            self.logger.error(f"Error calculating target instances: {e}")
            return current

    async def _get_current_instances(self, service_id: str) -> int:
        """Get current instance count for service"""
        # This would integrate with service controllers
        return 3  # Mock value

    async def _get_max_instances(self, service_id: str) -> int:
        """Get maximum allowed instances for service"""
        return 10  # Mock value

    async def _perform_scaling(self, service_id: str, current: int, target: int) -> bool:
        """Perform actual scaling operation"""
        # This would integrate with the autoscaler
        self.logger.info(f"Performing scaling: {service_id} {current} -> {target}")
        return True  # Mock success

    async def _store_processed_event(self, event: SystemEvent):
        """Store processed event in Redis"""
        try:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'severity': event.severity.value,
                'source_service': event.source_service,
                'message': event.message,
                'data': event.data,
                'timestamp': event.timestamp.isoformat(),
                'processed': event.processed,
                'triggered_actions': event.triggered_actions
            }

            self.redis_client.lpush('processed_events', json.dumps(event_data))
            self.redis_client.ltrim('processed_events', 0, 999)  # Keep last 1000

        except Exception as e:
            self.logger.error(f"Error storing processed event: {e}")

    async def _store_execution(self, execution: EventScalingExecution):
        """Store execution record in Redis"""
        try:
            execution_data = {
                'execution_id': execution.execution_id,
                'trigger_id': execution.trigger_id,
                'event_id': execution.event_id,
                'service_id': execution.service_id,
                'action': execution.action.value,
                'original_instances': execution.original_instances,
                'target_instances': execution.target_instances,
                'executed_at': execution.executed_at.isoformat(),
                'status': execution.status,
                'duration_seconds': execution.duration_seconds,
                'error_message': execution.error_message
            }

            self.redis_client.lpush('event_executions', json.dumps(execution_data))
            self.redis_client.ltrim('event_executions', 0, 999)  # Keep last 1000

        except Exception as e:
            self.logger.error(f"Error storing execution: {e}")

    async def trigger_manual_event(self, event_type: str, severity: str, source: str, message: str, data: Dict[str, Any] = None):
        """Manually trigger an event"""
        try:
            await self._create_event(
                EventType(event_type),
                EventSeverity(severity),
                source,
                message,
                data or {}
            )
        except Exception as e:
            self.logger.error(f"Error triggering manual event: {e}")

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent system events"""
        try:
            events = []
            for event in sorted(self.system_events, key=lambda x: x.timestamp, reverse=True)[:limit]:
                events.append({
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'severity': event.severity.value,
                    'source_service': event.source_service,
                    'message': event.message,
                    'timestamp': event.timestamp.isoformat(),
                    'processed': event.processed,
                    'triggered_actions': event.triggered_actions,
                    'data': event.data
                })
            return events

        except Exception as e:
            self.logger.error(f"Error getting recent events: {e}")
            return []

    def get_recent_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scaling executions"""
        try:
            executions = []
            for execution in sorted(self.executions, key=lambda x: x.executed_at, reverse=True)[:limit]:
                executions.append({
                    'execution_id': execution.execution_id,
                    'trigger_id': execution.trigger_id,
                    'event_id': execution.event_id,
                    'service_id': execution.service_id,
                    'action': execution.action.value,
                    'original_instances': execution.original_instances,
                    'target_instances': execution.target_instances,
                    'executed_at': execution.executed_at.isoformat(),
                    'status': execution.status,
                    'duration_seconds': execution.duration_seconds,
                    'error_message': execution.error_message
                })
            return executions

        except Exception as e:
            self.logger.error(f"Error getting recent executions: {e}")
            return []