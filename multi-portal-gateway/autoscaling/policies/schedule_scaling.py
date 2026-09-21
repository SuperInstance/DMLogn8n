#!/usr/bin/env python3
"""
Schedule-based Scaling for DMLogn8n Auto-Scaling
Handles time-based scaling according to schedules
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import redis
import pytz
from croniter import croniter

from ..autoscaler import ScalingDecision, ScaleDirection

class ScheduleType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"
    EVENT = "event"

class ScheduleAction(Enum):
    SCALE_TO = "scale_to"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"

@dataclass
class ScheduleRule:
    rule_id: str
    name: str
    service_id: str
    schedule_type: ScheduleType
    schedule_expression: str  # cron expression, time, etc.
    action: ScheduleAction
    target_instances: Optional[int]
    timezone: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    description: str = ""

@dataclass
class ScheduleExecution:
    execution_id: str
    rule_id: str
    service_id: str
    scheduled_time: datetime
    executed_time: Optional[datetime]
    action: ScheduleAction
    target_instances: Optional[int]
    status: str  # scheduled, executed, failed, skipped
    error_message: Optional[str]

class ScheduleScalingManager:
    """
    Manages schedule-based auto-scaling
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('schedule_scaling')

        # Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Schedule storage
        self.schedule_rules: Dict[str, ScheduleRule] = {}
        self.schedule_executions: List[ScheduleExecution] = []

        # Default timezone
        self.default_timezone = pytz.timezone(config.get('default_timezone', 'UTC'))

        # Load default schedules
        self._load_default_schedules()
        self._load_schedules_from_redis()

    def _load_default_schedules(self):
        """Load default schedule-based scaling rules"""
        try:
            default_schedules = [
                # Business hours scaling for API Gateway
                ScheduleRule(
                    rule_id="api-gateway-business-hours",
                    name="API Gateway Business Hours Scaling",
                    service_id="api-gateway",
                    schedule_type=ScheduleType.DAILY,
                    schedule_expression="08:00",
                    action=ScheduleAction.SCALE_TO,
                    target_instances=6,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up for business hours"
                ),
                ScheduleRule(
                    rule_id="api-gateway-after-hours",
                    name="API Gateway After Hours Scaling",
                    service_id="api-gateway",
                    schedule_type=ScheduleType.DAILY,
                    schedule_expression="18:00",
                    action=ScheduleAction.SCALE_TO,
                    target_instances=3,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale down after business hours"
                ),

                # Weekend scaling for Character Portal
                ScheduleRule(
                    rule_id="character-portal-weekend-up",
                    name="Character Portal Weekend Scale Up",
                    service_id="character-portal",
                    schedule_type=ScheduleType.WEEKLY,
                    schedule_expression="0 9 * * 6",  # Saturday 9 AM
                    action=ScheduleAction.SCALE_TO,
                    target_instances=8,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up for weekend traffic"
                ),
                ScheduleRule(
                    rule_id="character-portal-weekend-down",
                    name="Character Portal Weekend Scale Down",
                    service_id="character-portal",
                    schedule_type=ScheduleType.WEEKLY,
                    schedule_expression="0 22 * * 0",  # Sunday 10 PM
                    action=ScheduleAction.SCALE_TO,
                    target_instances=4,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale down after weekend"
                ),

                # Peak hours for AI Model Pool
                ScheduleRule(
                    rule_id="ai-model-peak-hours",
                    name="AI Model Pool Peak Hours",
                    service_id="ai-model-pool",
                    schedule_type=ScheduleType.CRON,
                    schedule_expression="0 */4 * * *",  # Every 4 hours
                    action=ScheduleAction.SCALE_UP,
                    target_instances=None,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up during peak usage periods"
                ),

                # Night time cost optimization
                ScheduleRule(
                    rule_id="night-cost-optimization",
                    name="Night Time Cost Optimization",
                    service_id="world-simulation",
                    schedule_type=ScheduleType.DAILY,
                    schedule_expression="02:00",
                    action=ScheduleAction.MINIMIZE,
                    target_instances=None,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Minimize instances during low usage night hours"
                ),

                # Monthly maintenance window
                ScheduleRule(
                    rule_id="monthly-maintenance",
                    name="Monthly Maintenance Scaling",
                    service_id="combat-engine",
                    schedule_type=ScheduleType.MONTHLY,
                    schedule_expression="0 2 1 * *",  # 1st of month 2 AM
                    action=ScheduleAction.SCALE_TO,
                    target_instances=1,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale down for monthly maintenance window"
                ),

                # Event-based scaling (example for game events)
                ScheduleRule(
                    rule_id="game-event-scaling",
                    name="Game Event Scaling",
                    service_id="dialogue-system",
                    schedule_type=ScheduleType.EVENT,
                    schedule_expression="game_event_start",
                    action=ScheduleAction.MAXIMIZE,
                    target_instances=None,
                    timezone="UTC",
                    enabled=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by="system",
                    description="Scale up for game events"
                )
            ]

            for rule in default_schedules:
                self.schedule_rules[rule.rule_id] = rule

            self.logger.info(f"Loaded {len(default_schedules)} default schedule rules")

        except Exception as e:
            self.logger.error(f"Error loading default schedules: {e}")

    def _load_schedules_from_redis(self):
        """Load schedule rules from Redis"""
        try:
            rule_keys = self.redis_client.keys('schedule_rule:*')
            for key in rule_keys:
                rule_data = json.loads(self.redis_client.get(key))
                rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                rule_data['updated_at'] = datetime.fromisoformat(rule_data['updated_at'])
                rule_data['schedule_type'] = ScheduleType(rule_data['schedule_type'])
                rule_data['action'] = ScheduleAction(rule_data['action'])

                rule = ScheduleRule(**rule_data)
                self.schedule_rules[rule.rule_id] = rule

            self.logger.info(f"Loaded {len(rule_keys)} schedule rules from Redis")

        except Exception as e:
            self.logger.error(f"Error loading schedules from Redis: {e}")

    async def start_scheduler(self):
        """Start the schedule evaluation loop"""
        self.logger.info("Starting schedule-based scaling manager...")

        while True:
            try:
                await self._evaluate_schedules()
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in schedule evaluation: {e}")
                await asyncio.sleep(30)

    async def _evaluate_schedules(self):
        """Evaluate all enabled schedule rules"""
        current_time = datetime.now(pytz.UTC)

        for rule in self.schedule_rules.values():
            if not rule.enabled:
                continue

            try:
                # Check if rule should be triggered now
                if await self._should_trigger_rule(rule, current_time):
                    await self._execute_schedule_rule(rule, current_time)

            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

    async def _should_trigger_rule(self, rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if a schedule rule should be triggered"""
        try:
            # Convert timezone
            tz = pytz.timezone(rule.timezone)
            current_time_tz = current_time.astimezone(tz)

            if rule.schedule_type == ScheduleType.DAILY:
                # Check if current time matches the scheduled time
                scheduled_time = datetime.strptime(rule.schedule_expression, "%H:%M").time()
                current_time_only = current_time_tz.time()

                # Check if within 1 minute window
                scheduled_datetime = current_time_tz.replace(
                    hour=scheduled_time.hour,
                    minute=scheduled_time.minute,
                    second=0,
                    microsecond=0
                )
                time_diff = abs((current_time_tz - scheduled_datetime).total_seconds())
                return time_diff <= 60  # Within 1 minute

            elif rule.schedule_type == ScheduleType.WEEKLY:
                # Use croniter for weekly schedules
                cron = croniter(rule.schedule_expression, current_time_tz)
                next_run = cron.get_next(datetime)
                time_diff = (next_run - current_time_tz).total_seconds()
                return 0 <= time_diff <= 60

            elif rule.schedule_type == ScheduleType.MONTHLY:
                # Use croniter for monthly schedules
                cron = croniter(rule.schedule_expression, current_time_tz)
                next_run = cron.get_next(datetime)
                time_diff = (next_run - current_time_tz).total_seconds()
                return 0 <= time_diff <= 60

            elif rule.schedule_type == ScheduleType.CRON:
                # Use croniter for cron expressions
                cron = croniter(rule.schedule_expression, current_time_tz)
                next_run = cron.get_next(datetime)
                time_diff = (next_run - current_time_tz).total_seconds()
                return 0 <= time_diff <= 60

            elif rule.schedule_type == ScheduleType.EVENT:
                # Check for event triggers
                return await self._check_event_trigger(rule)

            return False

        except Exception as e:
            self.logger.error(f"Error checking rule trigger for {rule.rule_id}: {e}")
            return False

    async def _check_event_trigger(self, rule: ScheduleRule) -> bool:
        """Check for event-based triggers"""
        try:
            # Check Redis for event triggers
            event_key = f"event:{rule.schedule_expression}"
            if self.redis_client.exists(event_key):
                event_data = json.loads(self.redis_client.get(event_key))

                # Check if event is active and not recently processed
                if event_data.get('active', False):
                    last_processed = self.redis_client.get(f"schedule_processed:{rule.rule_id}")
                    if not last_processed or (datetime.now().isoformat() > last_processed):
                        # Mark as processed
                        self.redis_client.setex(
                            f"schedule_processed:{rule.rule_id}",
                            3600,  # 1 hour cooldown
                            datetime.now().isoformat()
                        )
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking event trigger: {e}")
            return False

    async def _execute_schedule_rule(self, rule: ScheduleRule, current_time: datetime):
        """Execute a schedule rule"""
        try:
            execution_id = f"{rule.rule_id}-{int(current_time.timestamp())}"

            execution = ScheduleExecution(
                execution_id=execution_id,
                rule_id=rule.rule_id,
                service_id=rule.service_id,
                scheduled_time=current_time,
                executed_time=None,
                action=rule.action,
                target_instances=rule.target_instances,
                status="executing",
                error_message=None
            )

            try:
                # Get current instance count
                current_instances = await self._get_current_instances(rule.service_id)

                # Determine target instances based on action
                if rule.action == ScheduleAction.SCALE_TO:
                    target_instances = rule.target_instances
                elif rule.action == ScheduleAction.SCALE_UP:
                    target_instances = current_instances + 1
                elif rule.action == ScheduleAction.SCALE_DOWN:
                    target_instances = max(1, current_instances - 1)
                elif rule.action == ScheduleAction.MINIMIZE:
                    target_instances = 1
                elif rule.action == ScheduleAction.MAXIMIZE:
                    target_instances = await self._get_max_instances(rule.service_id)
                else:
                    target_instances = current_instances

                if target_instances != current_instances:
                    # Execute scaling action
                    success = await self._execute_scaling_action(
                        rule.service_id, current_instances, target_instances
                    )

                    if success:
                        execution.status = "executed"
                        execution.executed_time = datetime.now()
                        self.logger.info(
                            f"Executed scheduled scaling for {rule.service_id}: "
                            f"{current_instances} -> {target_instances} ({rule.name})"
                        )
                    else:
                        execution.status = "failed"
                        execution.error_message = "Scaling action failed"
                else:
                    execution.status = "skipped"
                    execution.error_message = "No scaling needed"

            except Exception as e:
                execution.status = "failed"
                execution.error_message = str(e)
                self.logger.error(f"Failed to execute schedule rule {rule.rule_id}: {e}")

            # Store execution record
            self.schedule_executions.append(execution)
            await self._save_execution_to_redis(execution)

        except Exception as e:
            self.logger.error(f"Error executing schedule rule {rule.rule_id}: {e}")

    async def _get_current_instances(self, service_id: str) -> int:
        """Get current instance count for a service"""
        try:
            # This would typically query the service controller
            # For now, return a mock value
            return 3
        except Exception as e:
            self.logger.error(f"Error getting current instances for {service_id}: {e}")
            return 1

    async def _get_max_instances(self, service_id: str) -> int:
        """Get maximum allowed instances for a service"""
        try:
            # This would typically get from scaling policy
            # For now, return a default
            return 10
        except Exception as e:
            self.logger.error(f"Error getting max instances for {service_id}: {e}")
            return 5

    async def _execute_scaling_action(self, service_id: str, current_instances: int, target_instances: int) -> bool:
        """Execute scaling action"""
        try:
            # This would integrate with the autoscaler to execute scaling
            # For now, simulate success
            self.logger.info(f"Scaling {service_id} from {current_instances} to {target_instances}")
            return True
        except Exception as e:
            self.logger.error(f"Error executing scaling action: {e}")
            return False

    async def _save_execution_to_redis(self, execution: ScheduleExecution):
        """Save execution record to Redis"""
        try:
            execution_data = {
                'execution_id': execution.execution_id,
                'rule_id': execution.rule_id,
                'service_id': execution.service_id,
                'scheduled_time': execution.scheduled_time.isoformat(),
                'executed_time': execution.executed_time.isoformat() if execution.executed_time else None,
                'action': execution.action.value,
                'target_instances': execution.target_instances,
                'status': execution.status,
                'error_message': execution.error_message
            }

            self.redis_client.lpush(
                f'schedule_executions:{execution.service_id}',
                json.dumps(execution_data)
            )
            self.redis_client.ltrim(
                f'schedule_executions:{execution.service_id}',
                0, 99
            )  # Keep last 100 executions per service

        except Exception as e:
            self.logger.error(f"Error saving execution to Redis: {e}")

    async def create_schedule_rule(self, rule_data: Dict[str, Any], created_by: str = 'user') -> Optional[str]:
        """Create a new schedule rule"""
        try:
            rule_id = f"schedule-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            rule = ScheduleRule(
                rule_id=rule_id,
                name=rule_data['name'],
                service_id=rule_data['service_id'],
                schedule_type=ScheduleType(rule_data['schedule_type']),
                schedule_expression=rule_data['schedule_expression'],
                action=ScheduleAction(rule_data['action']),
                target_instances=rule_data.get('target_instances'),
                timezone=rule_data.get('timezone', 'UTC'),
                enabled=rule_data.get('enabled', True),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by=created_by,
                description=rule_data.get('description', '')
            )

            self.schedule_rules[rule_id] = rule
            await self._save_rule_to_redis(rule)

            self.logger.info(f"Created schedule rule: {rule_id}")
            return rule_id

        except Exception as e:
            self.logger.error(f"Error creating schedule rule: {e}")
            return None

    async def _save_rule_to_redis(self, rule: ScheduleRule):
        """Save schedule rule to Redis"""
        try:
            rule_data = {
                'rule_id': rule.rule_id,
                'name': rule.name,
                'service_id': rule.service_id,
                'schedule_type': rule.schedule_type.value,
                'schedule_expression': rule.schedule_expression,
                'action': rule.action.value,
                'target_instances': rule.target_instances,
                'timezone': rule.timezone,
                'enabled': rule.enabled,
                'created_at': rule.created_at.isoformat(),
                'updated_at': rule.updated_at.isoformat(),
                'created_by': rule.created_by,
                'description': rule.description
            }

            self.redis_client.set(f'schedule_rule:{rule.rule_id}', json.dumps(rule_data))

        except Exception as e:
            self.logger.error(f"Error saving rule to Redis: {e}")

    async def trigger_event(self, event_name: str, event_data: Dict[str, Any]):
        """Trigger an event-based scaling rule"""
        try:
            event_key = f"event:{event_name}"
            event_payload = {
                'name': event_name,
                'data': event_data,
                'active': True,
                'timestamp': datetime.now().isoformat()
            }

            self.redis_client.setex(event_key, 3600, json.dumps(event_payload))  # 1 hour TTL
            self.logger.info(f"Triggered event: {event_name}")

        except Exception as e:
            self.logger.error(f"Error triggering event {event_name}: {e}")

    def get_next_scheduled_executions(self, service_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get next scheduled executions"""
        try:
            executions = []
            current_time = datetime.now(pytz.UTC)

            for rule in self.schedule_rules.values():
                if not rule.enabled:
                    continue
                if service_id and rule.service_id != service_id:
                    continue

                # Calculate next execution time
                next_execution = self._calculate_next_execution(rule, current_time)
                if next_execution:
                    executions.append({
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'service_id': rule.service_id,
                        'next_execution': next_execution.isoformat(),
                        'action': rule.action.value,
                        'target_instances': rule.target_instances
                    })

            # Sort by next execution time
            executions.sort(key=lambda x: x['next_execution'])
            return executions[:limit]

        except Exception as e:
            self.logger.error(f"Error getting next scheduled executions: {e}")
            return []

    def _calculate_next_execution(self, rule: ScheduleRule, current_time: datetime) -> Optional[datetime]:
        """Calculate next execution time for a rule"""
        try:
            tz = pytz.timezone(rule.timezone)
            current_time_tz = current_time.astimezone(tz)

            if rule.schedule_type == ScheduleType.DAILY:
                scheduled_time = datetime.strptime(rule.schedule_expression, "%H:%M").time()
                next_execution = current_time_tz.replace(
                    hour=scheduled_time.hour,
                    minute=scheduled_time.minute,
                    second=0,
                    microsecond=0
                )

                if next_execution <= current_time_tz:
                    next_execution += timedelta(days=1)

                return next_execution

            elif rule.schedule_type in [ScheduleType.WEEKLY, ScheduleType.MONTHLY, ScheduleType.CRON]:
                cron = croniter(rule.schedule_expression, current_time_tz)
                return cron.get_next(datetime)

            return None

        except Exception as e:
            self.logger.error(f"Error calculating next execution: {e}")
            return None

    def get_execution_history(self, service_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get schedule execution history"""
        try:
            history = []

            for execution in self.schedule_executions:
                if service_id and execution.service_id != service_id:
                    continue

                history.append({
                    'execution_id': execution.execution_id,
                    'rule_id': execution.rule_id,
                    'service_id': execution.service_id,
                    'scheduled_time': execution.scheduled_time.isoformat(),
                    'executed_time': execution.executed_time.isoformat() if execution.executed_time else None,
                    'action': execution.action.value,
                    'target_instances': execution.target_instances,
                    'status': execution.status,
                    'error_message': execution.error_message
                })

            # Sort by scheduled time descending
            history.sort(key=lambda x: x['scheduled_time'], reverse=True)
            return history[:limit]

        except Exception as e:
            self.logger.error(f"Error getting execution history: {e}")
            return []