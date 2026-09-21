#!/usr/bin/env python3
"""
Scaling Policy Management for DMLogn8n Auto-Scaling
Manages scaling policies and rules
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from pathlib import Path

from ..autoscaler import ScalingPolicy, ServiceType

class PolicyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class PolicyType(Enum):
    METRIC_BASED = "metric_based"
    SCHEDULE_BASED = "schedule_based"
    EVENT_BASED = "event_based"
    PREDICTIVE = "predictive"
    COST_BASED = "cost_based"

@dataclass
class PolicyRule:
    name: str
    metric: str
    operator: str  # >, <, >=, <=, ==, !=
    threshold: float
    duration: int  # seconds
    action: str  # scale_up, scale_down, scale_to
    value: Optional[int] = None
    cooldown: int = 300

@dataclass
class ScalingPolicyConfig:
    policy_id: str
    name: str
    description: str
    service_id: str
    service_type: ServiceType
    policy_type: PolicyType
    status: PolicyStatus
    rules: List[PolicyRule]
    min_instances: int
    max_instances: int
    target_metrics: Dict[str, float]
    cooldown_period: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    tags: List[str]
    version: int = 1

class ScalePolicyManager:
    """
    Manages scaling policies and rules
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('scale_policy_manager')

        # Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Policy storage
        self.policies: Dict[str, ScalingPolicyConfig] = {}
        self.default_cooldown = config.get('default_cooldown', 300)

        # Policy directories
        self.policy_dir = Path("/home/activeloguser/DMLogn8n/autoscaling/policies")
        self.policy_dir.mkdir(parents=True, exist_ok=True)

        # Load existing policies
        self._load_default_policies()
        self._load_policies_from_redis()

    def _load_default_policies(self):
        """Load default scaling policies"""
        try:
            default_policies = [
                {
                    'policy_id': 'api-gateway-default',
                    'name': 'API Gateway Default Policy',
                    'description': 'Default scaling policy for API Gateway',
                    'service_id': 'api-gateway',
                    'service_type': ServiceType.API_GATEWAY,
                    'policy_type': PolicyType.METRIC_BASED,
                    'status': PolicyStatus.ACTIVE,
                    'min_instances': 2,
                    'max_instances': 10,
                    'target_metrics': {'cpu': 60, 'memory': 70},
                    'cooldown_period': 300,
                    'rules': [
                        PolicyRule(
                            name='CPU Scale Up',
                            metric='cpu_usage',
                            operator='>',
                            threshold=70,
                            duration=60,
                            action='scale_up',
                            value=1,
                            cooldown=300
                        ),
                        PolicyRule(
                            name='CPU Scale Down',
                            metric='cpu_usage',
                            operator='<',
                            threshold=30,
                            duration=120,
                            action='scale_down',
                            value=1,
                            cooldown=300
                        ),
                        PolicyRule(
                            name='Memory Scale Up',
                            metric='memory_usage',
                            operator='>',
                            threshold=80,
                            duration=60,
                            action='scale_up',
                            value=1,
                            cooldown=300
                        )
                    ],
                    'created_by': 'system',
                    'tags': ['default', 'api']
                },
                {
                    'policy_id': 'character-portal-default',
                    'name': 'Character Portal Default Policy',
                    'description': 'Default scaling policy for Character Portal',
                    'service_id': 'character-portal',
                    'service_type': ServiceType.CHARACTER_PORTAL,
                    'policy_type': PolicyType.METRIC_BASED,
                    'status': PolicyStatus.ACTIVE,
                    'min_instances': 3,
                    'max_instances': 15,
                    'target_metrics': {'cpu': 50, 'memory': 60, 'active_sessions': 1000},
                    'cooldown_period': 240,
                    'rules': [
                        PolicyRule(
                            name='Active Sessions Scale Up',
                            metric='active_sessions',
                            operator='>',
                            threshold=800,
                            duration=30,
                            action='scale_up',
                            value=2,
                            cooldown=180
                        ),
                        PolicyRule(
                            name='Character Interactions Scale Up',
                            metric='character_interactions_per_second',
                            operator='>',
                            threshold=100,
                            duration=60,
                            action='scale_up',
                            value=1,
                            cooldown=240
                        ),
                        PolicyRule(
                            name='Memory Scale Down',
                            metric='memory_usage',
                            operator='<',
                            threshold="40",
                            duration=300,
                            action='scale_down',
                            value=1,
                            cooldown=600
                        )
                    ],
                    'created_by': 'system',
                    'tags': ['default', 'character', 'portal']
                },
                {
                    'policy_id': 'ai-model-pool-default',
                    'name': 'AI Model Pool Default Policy',
                    'description': 'Default scaling policy for AI Model Pool',
                    'service_id': 'ai-model-pool',
                    'service_type': ServiceType.AI_MODEL_POOL,
                    'policy_type': PolicyType.PREDICTIVE,
                    'status': PolicyStatus.ACTIVE,
                    'min_instances': 2,
                    'max_instances': 8,
                    'target_metrics': {'gpu_utilization': 75, 'inference_queue': 10},
                    'cooldown_period': 600,
                    'rules': [
                        PolicyRule(
                            name='GPU Utilization Scale Up',
                            metric='gpu_utilization_percent',
                            operator='>',
                            threshold=80,
                            duration=60,
                            action='scale_up',
                            value=1,
                            cooldown=600
                        ),
                        PolicyRule(
                            name='Inference Queue Scale Up',
                            metric='model_inference_queue_length',
                            operator='>',
                            threshold=15,
                            duration=30,
                            action='scale_up',
                            value=1,
                            cooldown=300
                        ),
                        PolicyRule(
                            name='Cost Optimization Scale Down',
                            metric='gpu_utilization_percent',
                            operator='<',
                            threshold=30,
                            duration=600,
                            action='scale_down',
                            value=1,
                            cooldown=900
                        )
                    ],
                    'created_by': 'system',
                    'tags': ['default', 'ai', 'gpu']
                },
                {
                    'policy_id': 'combat-engine-default',
                    'name': 'Combat Engine Default Policy',
                    'description': 'Default scaling policy for Combat Engine',
                    'service_id': 'combat-engine',
                    'service_type': ServiceType.COMBAT_ENGINE,
                    'policy_type': PolicyType.EVENT_BASED,
                    'status': PolicyStatus.ACTIVE,
                    'min_instances': 1,
                    'max_instances': 6,
                    'target_metrics': {'combat_calculations': 300, 'active_combats': 20},
                    'cooldown_period': 180,
                    'rules': [
                        PolicyRule(
                            name='Combat Calculations Scale Up',
                            metric='combat_calculations_per_second',
                            operator='>',
                            threshold=400,
                            duration=30,
                            action='scale_up',
                            value=1,
                            cooldown=180
                        ),
                        PolicyRule(
                            name='Active Combats Scale Up',
                            metric='active_combats',
                            operator='>',
                            threshold=15,
                            duration=60,
                            action='scale_up',
                            value=1,
                            cooldown=300
                        ),
                        PolicyRule(
                            name='Low Load Scale Down',
                            metric='combat_calculations_per_second',
                            operator='<',
                            threshold=50,
                            duration=300,
                            action='scale_down',
                            value=1,
                            cooldown=600
                        )
                    ],
                    'created_by': 'system',
                    'tags': ['default', 'combat', 'engine']
                }
            ]

            for policy_data in default_policies:
                policy = ScalingPolicyConfig(
                    **policy_data,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.policies[policy.policy_id] = policy

            self.logger.info(f"Loaded {len(default_policies)} default policies")

        except Exception as e:
            self.logger.error(f"Error loading default policies: {e}")

    def _load_policies_from_redis(self):
        """Load policies from Redis cache"""
        try:
            policy_keys = self.redis_client.keys('policy:*')
            for key in policy_keys:
                policy_data = json.loads(self.redis_client.get(key))
                # Convert string timestamps back to datetime
                policy_data['created_at'] = datetime.fromisoformat(policy_data['created_at'])
                policy_data['updated_at'] = datetime.fromisoformat(policy_data['updated_at'])
                policy_data['service_type'] = ServiceType(policy_data['service_type'])
                policy_data['policy_type'] = PolicyType(policy_data['policy_type'])
                policy_data['status'] = PolicyStatus(policy_data['status'])

                # Convert rules
                rules = []
                for rule_data in policy_data['rules']:
                    rules.append(PolicyRule(**rule_data))
                policy_data['rules'] = rules

                policy = ScalingPolicyConfig(**policy_data)
                self.policies[policy.policy_id] = policy

            self.logger.info(f"Loaded {len(policy_keys)} policies from Redis")

        except Exception as e:
            self.logger.error(f"Error loading policies from Redis: {e}")

    async def get_policy(self, service_id: str) -> Optional[ScalingPolicy]:
        """Get active scaling policy for a service"""
        try:
            # Find active policy for service
            for policy in self.policies.values():
                if (policy.service_id == service_id and
                    policy.status == PolicyStatus.ACTIVE):

                    # Convert to legacy ScalingPolicy format
                    return ScalingPolicy(
                        service_id=policy.service_id,
                        service_type=policy.service_type,
                        min_instances=policy.min_instances,
                        max_instances=policy.max_instances,
                        target_cpu=policy.target_metrics.get('cpu', 60),
                        target_memory=policy.target_metrics.get('memory', 70),
                        scale_up_threshold=policy.target_metrics.get('cpu', 60) + 10,
                        scale_down_threshold=policy.target_metrics.get('cpu', 60) - 20,
                        cooldown_period=policy.cooldown_period,
                        predictive_enabled=policy.policy_type == PolicyType.PREDICTIVE,
                        cost_optimization='cost' in policy.tags
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error getting policy for {service_id}: {e}")
            return None

    async def create_policy(self, policy_data: Dict[str, Any], created_by: str = 'user') -> Optional[str]:
        """Create a new scaling policy"""
        try:
            # Validate required fields
            required_fields = ['name', 'service_id', 'service_type', 'policy_type']
            for field in required_fields:
                if field not in policy_data:
                    raise ValueError(f"Missing required field: {field}")

            # Generate policy ID
            policy_id = f"{policy_data['service_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Convert rules
            rules = []
            if 'rules' in policy_data:
                for rule_data in policy_data['rules']:
                    rules.append(PolicyRule(**rule_data))

            policy = ScalingPolicyConfig(
                policy_id=policy_id,
                name=policy_data['name'],
                description=policy_data.get('description', ''),
                service_id=policy_data['service_id'],
                service_type=ServiceType(policy_data['service_type']),
                policy_type=PolicyType(policy_data['policy_type']),
                status=PolicyStatus(policy_data.get('status', 'draft')),
                rules=rules,
                min_instances=policy_data.get('min_instances', 1),
                max_instances=policy_data.get('max_instances', 10),
                target_metrics=policy_data.get('target_metrics', {}),
                cooldown_period=policy_data.get('cooldown_period', self.default_cooldown),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by=created_by,
                tags=policy_data.get('tags', []),
                version=1
            )

            # Store policy
            self.policies[policy_id] = policy
            await self._save_policy_to_redis(policy)

            self.logger.info(f"Created policy: {policy_id}")
            return policy_id

        except Exception as e:
            self.logger.error(f"Error creating policy: {e}")
            return None

    async def update_policy(self, policy_id: str, updates: Dict[str, Any], updated_by: str = 'user') -> bool:
        """Update an existing scaling policy"""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")

            policy = self.policies[policy_id]

            # Update fields
            for key, value in updates.items():
                if hasattr(policy, key) and key not in ['policy_id', 'created_at', 'created_by']:
                    setattr(policy, key, value)

            # Update timestamps and version
            policy.updated_at = datetime.now()
            policy.version += 1

            # Convert rules if provided
            if 'rules' in updates:
                rules = []
                for rule_data in updates['rules']:
                    rules.append(PolicyRule(**rule_data))
                policy.rules = rules

            # Save updated policy
            await self._save_policy_to_redis(policy)

            self.logger.info(f"Updated policy: {policy_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating policy {policy_id}: {e}")
            return False

    async def delete_policy(self, policy_id: str) -> bool:
        """Delete a scaling policy"""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")

            # Archive instead of delete
            policy = self.policies[policy_id]
            policy.status = PolicyStatus.ARCHIVED
            policy.updated_at = datetime.now()

            await self._save_policy_to_redis(policy)

            # Remove from active policies
            del self.policies[policy_id]

            self.logger.info(f"Archived policy: {policy_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting policy {policy_id}: {e}")
            return False

    async def activate_policy(self, policy_id: str) -> bool:
        """Activate a scaling policy"""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")

            # Deactivate other policies for the same service
            service_id = self.policies[policy_id].service_id
            for pid, policy in self.policies.items():
                if policy.service_id == service_id and policy.status == PolicyStatus.ACTIVE:
                    policy.status = PolicyStatus.INACTIVE
                    policy.updated_at = datetime.now()
                    await self._save_policy_to_redis(policy)

            # Activate the requested policy
            self.policies[policy_id].status = PolicyStatus.ACTIVE
            self.policies[policy_id].updated_at = datetime.now()
            await self._save_policy_to_redis(self.policies[policy_id])

            self.logger.info(f"Activated policy: {policy_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error activating policy {policy_id}: {e}")
            return False

    async def deactivate_policy(self, policy_id: str) -> bool:
        """Deactivate a scaling policy"""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")

            self.policies[policy_id].status = PolicyStatus.INACTIVE
            self.policies[policy_id].updated_at = datetime.now()
            await self._save_policy_to_redis(self.policies[policy_id])

            self.logger.info(f"Deactivated policy: {policy_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deactivating policy {policy_id}: {e}")
            return False

    async def _save_policy_to_redis(self, policy: ScalingPolicyConfig):
        """Save policy to Redis"""
        try:
            policy_data = asdict(policy)
            # Convert datetime objects to strings
            policy_data['created_at'] = policy.created_at.isoformat()
            policy_data['updated_at'] = policy.updated_at.isoformat()
            # Convert enums to strings
            policy_data['service_type'] = policy.service_type.value
            policy_data['policy_type'] = policy.policy_type.value
            policy_data['status'] = policy.status.value

            self.redis_client.set(f'policy:{policy.policy_id}', json.dumps(policy_data))

        except Exception as e:
            self.logger.error(f"Error saving policy to Redis: {e}")

    def list_policies(self, service_id: Optional[str] = None, status: Optional[PolicyStatus] = None) -> List[Dict[str, Any]]:
        """List scaling policies"""
        try:
            policies = []

            for policy in self.policies.values():
                # Apply filters
                if service_id and policy.service_id != service_id:
                    continue
                if status and policy.status != status:
                    continue

                policy_dict = asdict(policy)
                policy_dict['created_at'] = policy.created_at.isoformat()
                policy_dict['updated_at'] = policy.updated_at.isoformat()
                policy_dict['service_type'] = policy.service_type.value
                policy_dict['policy_type'] = policy.policy_type.value
                policy_dict['status'] = policy.status.value

                policies.append(policy_dict)

            return policies

        except Exception as e:
            self.logger.error(f"Error listing policies: {e}")
            return []

    def get_policy_history(self, policy_id: str) -> List[Dict[str, Any]]:
        """Get policy change history"""
        try:
            # This would typically query a database or audit log
            # For now, return basic history from Redis
            history = []

            history_key = f'policy_history:{policy_id}'
            if self.redis_client.exists(history_key):
                history_data = self.redis_client.lrange(history_key, 0, -1)
                for item in history_data:
                    history.append(json.loads(item))

            return history

        except Exception as e:
            self.logger.error(f"Error getting policy history: {e}")
            return []

    async def validate_policy(self, policy_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate policy configuration"""
        try:
            errors = []

            # Validate required fields
            required_fields = ['name', 'service_id', 'service_type', 'policy_type']
            for field in required_fields:
                if field not in policy_data:
                    errors.append(f"Missing required field: {field}")

            # Validate service type
            if 'service_type' in policy_data:
                try:
                    ServiceType(policy_data['service_type'])
                except ValueError:
                    errors.append(f"Invalid service type: {policy_data['service_type']}")

            # Validate policy type
            if 'policy_type' in policy_data:
                try:
                    PolicyType(policy_data['policy_type'])
                except ValueError:
                    errors.append(f"Invalid policy type: {policy_data['policy_type']}")

            # Validate min/max instances
            if 'min_instances' in policy_data and 'max_instances' in policy_data:
                if policy_data['min_instances'] >= policy_data['max_instances']:
                    errors.append("min_instances must be less than max_instances")
                if policy_data['min_instances'] < 0:
                    errors.append("min_instances must be non-negative")

            # Validate rules
            if 'rules' in policy_data:
                for i, rule in enumerate(policy_data['rules']):
                    if 'metric' not in rule:
                        errors.append(f"Rule {i}: missing metric")
                    if 'operator' not in rule:
                        errors.append(f"Rule {i}: missing operator")
                    if 'threshold' not in rule:
                        errors.append(f"Rule {i}: missing threshold")
                    if 'action' not in rule:
                        errors.append(f"Rule {i}: missing action")

            return len(errors) == 0, errors

        except Exception as e:
            self.logger.error(f"Error validating policy: {e}")
            return False, [f"Validation error: {str(e)}"]

    async def export_policy(self, policy_id: str, format: str = 'yaml') -> Optional[str]:
        """Export policy to file format"""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")

            policy = self.policies[policy_id]
            policy_dict = asdict(policy)

            # Convert datetime objects to strings
            policy_dict['created_at'] = policy.created_at.isoformat()
            policy_dict['updated_at'] = policy.updated_at.isoformat()
            # Convert enums to strings
            policy_dict['service_type'] = policy.service_type.value
            policy_dict['policy_type'] = policy.policy_type.value
            policy_dict['status'] = policy.status.value

            if format.lower() == 'yaml':
                return yaml.dump(policy_dict, default_flow_style=False)
            elif format.lower() == 'json':
                return json.dumps(policy_dict, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            self.logger.error(f"Error exporting policy {policy_id}: {e}")
            return None

    async def import_policy(self, policy_content: str, format: str = 'yaml', created_by: str = 'user') -> Optional[str]:
        """Import policy from file content"""
        try:
            if format.lower() == 'yaml':
                policy_data = yaml.safe_load(policy_content)
            elif format.lower() == 'json':
                policy_data = json.loads(policy_content)
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Validate policy
            is_valid, errors = await self.validate_policy(policy_data)
            if not is_valid:
                self.logger.error(f"Invalid policy: {errors}")
                return None

            # Create policy
            policy_id = await self.create_policy(policy_data, created_by)
            return policy_id

        except Exception as e:
            self.logger.error(f"Error importing policy: {e}")
            return None