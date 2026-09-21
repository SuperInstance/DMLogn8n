#!/usr/bin/env python3
"""
DMLogn8n Auto-Scaling Engine
Comprehensive auto-scaling system for multi-agent platform
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
import statistics
from collections import defaultdict, deque
import aiohttp
import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Import modules
from metrics.custom_metrics import CustomMetricsCollector
from metrics.predictor import PredictiveScaler
from metrics.cost_optimizer import CostOptimizer
from policies.scale_policies import ScalePolicyManager
from controllers.k8s_controller import KubernetesController
from controllers.docker_controller import DockerController
from controllers.cloud_controller import CloudController

class ScaleDirection(Enum):
    UP = "scale_up"
    DOWN = "scale_down"
    NONE = "no_scale"

class ServiceType(Enum):
    API_GATEWAY = "api_gateway"
    CHARACTER_PORTAL = "character_portal"
    AI_MODEL_POOL = "ai_model_pool"
    DIALOGUE_SYSTEM = "dialogue_system"
    COMBAT_ENGINE = "combat_engine"
    WORLD_SIMULATION = "world_simulation"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FRONTEND = "frontend"

@dataclass
class ServiceMetrics:
    service_id: str
    service_type: ServiceType
    cpu_usage: float
    memory_usage: float
    request_rate: float
    response_time: float
    error_rate: float
    custom_metrics: Dict[str, float]
    timestamp: datetime
    instance_count: int

@dataclass
class ScalingDecision:
    service_id: str
    current_instances: int
    desired_instances: int
    direction: ScaleDirection
    reason: str
    confidence: float
    cost_impact: float
    execution_time: Optional[datetime] = None

@dataclass
class ScalingPolicy:
    service_id: str
    service_type: ServiceType
    min_instances: int
    max_instances: int
    target_cpu: float
    target_memory: float
    scale_up_threshold: float
    scale_down_threshold: float
    cooldown_period: int
    predictive_enabled: bool
    cost_optimization: bool

class AutoScalingEngine:
    """
    Main auto-scaling engine for DMLogn8n platform
    """

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/autoscaling/config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Initialize components
        self.metrics_collector = CustomMetricsCollector(self.config.get('metrics', {}))
        self.predictive_scaler = PredictiveScaler(self.config.get('prediction', {}))
        self.cost_optimizer = CostOptimizer(self.config.get('cost', {}))
        self.policy_manager = ScalePolicyManager(self.config.get('policies', {}))

        # Initialize controllers
        self.k8s_controller = KubernetesController(self.config.get('kubernetes', {}))
        self.docker_controller = DockerController(self.config.get('docker', {}))
        self.cloud_controller = CloudController(self.config.get('cloud', {}))

        # Redis for caching and coordination
        self.redis_client = redis.Redis(
            host=self.config.get('redis', {}).get('host', 'localhost'),
            port=self.config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # State management
        self.service_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.scaling_history: List[ScalingDecision] = []
        self.cooldown_timers: Dict[str, datetime] = {}
        self.last_scale_time: Dict[str, datetime] = {}

        # Metrics
        self.scaling_events_total = Counter('autoscaling_events_total', 'Total scaling events', ['service', 'direction'])
        self.scaling_duration = Histogram('autoscaling_duration_seconds', 'Scaling operation duration')
        self.active_services = Gauge('autoscaling_active_services', 'Number of services being monitored')
        self.current_instances = Gauge('autoscaling_current_instances', 'Current instance count', ['service'])

        self.logger.info("AutoScaling Engine initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'metrics': {
                'collection_interval': 30,
                'retention_period': 3600
            },
            'prediction': {
                'enabled': True,
                'model_path': '/models/scaling_predictor.pkl',
                'prediction_window': 300
            },
            'cost': {
                'enabled': True,
                'cost_threshold': 100,
                'optimization_interval': 300
            },
            'policies': {
                'default_cooldown': 300,
                'evaluation_interval': 60
            },
            'kubernetes': {
                'enabled': True,
                'namespace': 'dmlogn8n'
            },
            'docker': {
                'enabled': True,
                'compose_file': '/docker-compose.yml'
            },
            'cloud': {
                'enabled': True,
                'provider': 'aws',
                'region': 'us-west-2'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('autoscaling_engine')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def start(self):
        """Start the auto-scaling engine"""
        self.logger.info("Starting AutoScaling Engine...")

        # Start Prometheus metrics server
        start_http_server(8080)

        # Start background tasks
        tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._scaling_evaluation_loop()),
            asyncio.create_task(self._cost_optimization_loop()),
            asyncio.create_task(self._predictive_scaling_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in auto-scaling engine: {e}")
            raise

    async def _metrics_collection_loop(self):
        """Continuous metrics collection loop"""
        interval = self.config['metrics']['collection_interval']

        while True:
            try:
                # Get all monitored services
                services = await self._get_monitored_services()

                # Collect metrics for each service
                for service in services:
                    metrics = await self._collect_service_metrics(service)
                    if metrics:
                        self.service_metrics[service.service_id].append(metrics)
                        self.current_instances.labels(service=service.service_id).set(metrics.instance_count)

                self.active_services.set(len(services))
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(10)

    async def _scaling_evaluation_loop(self):
        """Main scaling evaluation loop"""
        interval = self.config['policies']['evaluation_interval']

        while True:
            try:
                scaling_decisions = await self._evaluate_scaling_needs()

                for decision in scaling_decisions:
                    await self._execute_scaling_decision(decision)

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in scaling evaluation: {e}")
                await asyncio.sleep(10)

    async def _cost_optimization_loop(self):
        """Cost optimization evaluation loop"""
        interval = self.config['cost']['optimization_interval']

        while True:
            try:
                cost_decisions = await self.cost_optimizer.optimize_costs(self.service_metrics)

                for decision in cost_decisions:
                    if self._should_apply_cost_optimization(decision):
                        await self._execute_scaling_decision(decision)

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in cost optimization: {e}")
                await asyncio.sleep(30)

    async def _predictive_scaling_loop(self):
        """Predictive scaling evaluation loop"""
        if not self.config['prediction']['enabled']:
            return

        interval = self.config['prediction']['prediction_window']

        while True:
            try:
                predictions = await self.predictive_scaler.predict_scaling_needs(self.service_metrics)

                for prediction in predictions:
                    if prediction.confidence > 0.7:  # High confidence threshold
                        await self._execute_scaling_decision(prediction)

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in predictive scaling: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Cleanup and maintenance loop"""
        while True:
            try:
                # Clean old metrics
                cutoff_time = datetime.now() - timedelta(hours=1)
                for service_id, metrics_queue in self.service_metrics.items():
                    while metrics_queue and metrics_queue[0].timestamp < cutoff_time:
                        metrics_queue.popleft()

                # Clean old cooldown timers
                current_time = datetime.now()
                expired_cooldowns = [
                    service_id for service_id, cooldown_time in self.cooldown_timers.items()
                    if current_time > cooldown_time
                ]
                for service_id in expired_cooldowns:
                    del self.cooldown_timers[service_id]

                await asyncio.sleep(300)  # Run every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _get_monitored_services(self) -> List[Dict[str, Any]]:
        """Get list of services to monitor"""
        # This would typically query your service discovery or config
        services = [
            {
                'service_id': 'api-gateway',
                'service_type': ServiceType.API_GATEWAY,
                'controller': 'kubernetes'
            },
            {
                'service_id': 'character-portal',
                'service_type': ServiceType.CHARACTER_PORTAL,
                'controller': 'kubernetes'
            },
            {
                'service_id': 'ai-model-pool',
                'service_type': ServiceType.AI_MODEL_POOL,
                'controller': 'cloud'
            },
            {
                'service_id': 'dialogue-system',
                'service_type': ServiceType.DIALOGUE_SYSTEM,
                'controller': 'kubernetes'
            },
            {
                'service_id': 'combat-engine',
                'service_type': ServiceType.COMBAT_ENGINE,
                'controller': 'docker'
            },
            {
                'service_id': 'world-simulation',
                'service_type': ServiceType.WORLD_SIMULATION,
                'controller': 'kubernetes'
            }
        ]

        return services

    async def _collect_service_metrics(self, service: Dict[str, Any]) -> Optional[ServiceMetrics]:
        """Collect metrics for a specific service"""
        try:
            # Get basic metrics
            basic_metrics = await self.metrics_collector.collect_basic_metrics(service['service_id'])

            # Get custom metrics
            custom_metrics = await self.metrics_collector.collect_custom_metrics(service['service_id'])

            # Get current instance count
            controller = self._get_controller(service['controller'])
            instance_count = await controller.get_instance_count(service['service_id'])

            metrics = ServiceMetrics(
                service_id=service['service_id'],
                service_type=service['service_type'],
                cpu_usage=basic_metrics.get('cpu_usage', 0),
                memory_usage=basic_metrics.get('memory_usage', 0),
                request_rate=basic_metrics.get('request_rate', 0),
                response_time=basic_metrics.get('response_time', 0),
                error_rate=basic_metrics.get('error_rate', 0),
                custom_metrics=custom_metrics,
                timestamp=datetime.now(),
                instance_count=instance_count
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting metrics for {service['service_id']}: {e}")
            return None

    async def _evaluate_scaling_needs(self) -> List[ScalingDecision]:
        """Evaluate scaling needs for all services"""
        decisions = []

        for service_id, metrics_queue in self.service_metrics.items():
            if not metrics_queue:
                continue

            # Get latest metrics
            latest_metrics = metrics_queue[-1]

            # Get scaling policy
            policy = await self.policy_manager.get_policy(service_id)
            if not policy:
                continue

            # Check cooldown
            if self._is_in_cooldown(service_id, policy):
                continue

            # Evaluate scaling decision
            decision = await self._evaluate_service_scaling(latest_metrics, policy)
            if decision.direction != ScaleDirection.NONE:
                decisions.append(decision)

        return decisions

    async def _evaluate_service_scaling(self, metrics: ServiceMetrics, policy: ScalingPolicy) -> ScalingDecision:
        """Evaluate scaling decision for a single service"""
        scale_up_score = 0
        scale_down_score = 0
        reasons = []

        # CPU-based scaling
        if metrics.cpu_usage > policy.scale_up_threshold:
            scale_up_score += 0.3
            reasons.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        elif metrics.cpu_usage < policy.scale_down_threshold:
            scale_down_score += 0.3
            reasons.append(f"Low CPU usage: {metrics.cpu_usage:.1f}%")

        # Memory-based scaling
        if metrics.memory_usage > policy.scale_up_threshold:
            scale_up_score += 0.3
            reasons.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        elif metrics.memory_usage < policy.scale_down_threshold:
            scale_down_score += 0.3
            reasons.append(f"Low memory usage: {metrics.memory_usage:.1f}%")

        # Request rate scaling
        if metrics.custom_metrics.get('requests_per_second', 0) > 1000:
            scale_up_score += 0.2
            reasons.append("High request rate")
        elif metrics.custom_metrics.get('requests_per_second', 0) < 100:
            scale_down_score += 0.2
            reasons.append("Low request rate")

        # Response time scaling
        if metrics.response_time > 1000:  # 1 second
            scale_up_score += 0.2
            reasons.append(f"High response time: {metrics.response_time:.0f}ms")

        # Error rate scaling
        if metrics.error_rate > 5:  # 5% error rate
            scale_up_score += 0.2
            reasons.append(f"High error rate: {metrics.error_rate:.1f}%")

        # Determine scaling direction
        if scale_up_score > 0.6 and metrics.instance_count < policy.max_instances:
            direction = ScaleDirection.UP
            desired_instances = min(metrics.instance_count + 1, policy.max_instances)
            confidence = scale_up_score
        elif scale_down_score > 0.6 and metrics.instance_count > policy.min_instances:
            direction = ScaleDirection.DOWN
            desired_instances = max(metrics.instance_count - 1, policy.min_instances)
            confidence = scale_down_score
        else:
            direction = ScaleDirection.NONE
            desired_instances = metrics.instance_count
            confidence = 0

        # Calculate cost impact
        cost_impact = await self.cost_optimizer.calculate_scaling_cost(
            metrics.service_id, metrics.instance_count, desired_instances
        )

        return ScalingDecision(
            service_id=metrics.service_id,
            current_instances=metrics.instance_count,
            desired_instances=desired_instances,
            direction=direction,
            reason=", ".join(reasons) if reasons else "No scaling needed",
            confidence=confidence,
            cost_impact=cost_impact
        )

    def _is_in_cooldown(self, service_id: str, policy: ScalingPolicy) -> bool:
        """Check if service is in cooldown period"""
        if service_id not in self.last_scale_time:
            return False

        time_since_scale = datetime.now() - self.last_scale_time[service_id]
        return time_since_scale.total_seconds() < policy.cooldown_period

    async def _execute_scaling_decision(self, decision: ScalingDecision):
        """Execute a scaling decision"""
        if decision.direction == ScaleDirection.NONE:
            return

        try:
            start_time = time.time()

            # Get service info
            service_info = await self._get_service_info(decision.service_id)
            controller = self._get_controller(service_info['controller'])

            # Execute scaling
            if decision.direction == ScaleDirection.UP:
                await controller.scale_up(decision.service_id, decision.desired_instances)
            else:
                await controller.scale_down(decision.service_id, decision.desired_instances)

            # Update state
            self.last_scale_time[decision.service_id] = datetime.now()
            decision.execution_time = datetime.now()
            self.scaling_history.append(decision)

            # Update metrics
            self.scaling_events_total.labels(
                service=decision.service_id,
                direction=decision.direction.value
            ).inc()
            self.scaling_duration.observe(time.time() - start_time)

            # Log scaling event
            self.logger.info(
                f"Executed scaling decision for {decision.service_id}: "
                f"{decision.current_instances} -> {decision.desired_instances} "
                f"({decision.reason})"
            )

            # Store in Redis for audit
            await self._store_scaling_event(decision)

        except Exception as e:
            self.logger.error(f"Error executing scaling decision for {decision.service_id}: {e}")

    def _get_controller(self, controller_type: str):
        """Get the appropriate controller"""
        if controller_type == 'kubernetes':
            return self.k8s_controller
        elif controller_type == 'docker':
            return self.docker_controller
        elif controller_type == 'cloud':
            return self.cloud_controller
        else:
            raise ValueError(f"Unknown controller type: {controller_type}")

    async def _get_service_info(self, service_id: str) -> Dict[str, Any]:
        """Get service information"""
        # This would typically query your service registry
        services = await self._get_monitored_services()
        for service in services:
            if service['service_id'] == service_id:
                return service
        raise ValueError(f"Service not found: {service_id}")

    def _should_apply_cost_optimization(self, decision: ScalingDecision) -> bool:
        """Determine if cost optimization should be applied"""
        # Only apply if confidence is high and cost savings are significant
        return (decision.confidence > 0.8 and
                abs(decision.cost_impact) > 10 and
                decision.direction == ScaleDirection.DOWN)

    async def _store_scaling_event(self, decision: ScalingDecision):
        """Store scaling event in Redis for audit"""
        event_data = {
            'service_id': decision.service_id,
            'current_instances': decision.current_instances,
            'desired_instances': decision.desired_instances,
            'direction': decision.direction.value,
            'reason': decision.reason,
            'confidence': decision.confidence,
            'cost_impact': decision.cost_impact,
            'timestamp': decision.execution_time.isoformat() if decision.execution_time else datetime.now().isoformat()
        }

        # Store in Redis list for recent events
        self.redis_client.lpush('scaling_events', json.dumps(event_data))
        self.redis_client.ltrim('scaling_events', 0, 999)  # Keep last 1000 events

        # Store in service-specific history
        self.redis_client.lpush(
            f'scaling_history:{decision.service_id}',
            json.dumps(event_data)
        )
        self.redis_client.ltrim(
            f'scaling_history:{decision.service_id}',
            0, 99
        )  # Keep last 100 events per service

    def get_scaling_history(self, service_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scaling history"""
        if service_id:
            return [asdict(d) for d in self.scaling_history if d.service_id == service_id][-limit:]
        return [asdict(d) for d in self.scaling_history][-limit:]

    def get_current_metrics(self, service_id: str) -> Optional[ServiceMetrics]:
        """Get current metrics for a service"""
        if service_id in self.service_metrics and self.service_metrics[service_id]:
            return self.service_metrics[service_id][-1]
        return None

    async def force_scale(self, service_id: str, desired_instances: int, reason: str = "Manual scaling") -> bool:
        """Force scaling of a service"""
        try:
            service_info = await self._get_service_info(service_id)
            controller = self._get_controller(service_info['controller'])

            current_instances = await controller.get_instance_count(service_id)

            decision = ScalingDecision(
                service_id=service_id,
                current_instances=current_instances,
                desired_instances=desired_instances,
                direction=ScaleDirection.UP if desired_instances > current_instances else ScaleDirection.DOWN,
                reason=reason,
                confidence=1.0,
                cost_impact=0.0,
                execution_time=datetime.now()
            )

            await self._execute_scaling_decision(decision)
            return True

        except Exception as e:
            self.logger.error(f"Error force scaling {service_id}: {e}")
            return False

# CLI interface
async def main():
    """Main entry point"""
    autoscaler = AutoScalingEngine()
    await autoscaler.start()

if __name__ == "__main__":
    asyncio.run(main())