#!/usr/bin/env python3
"""
Cost Optimization for DMLogn8n Auto-Scaling
Optimizes scaling decisions based on cost considerations
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import redis
import aiohttp

from ..autoscaler import ScalingDecision, ServiceMetrics, ScaleDirection, ServiceType

@dataclass
class CostMetrics:
    service_id: str
    service_type: ServiceType
    instance_cost_per_hour: float
    current_hourly_cost: float
    daily_cost: float
    monthly_cost_estimate: float
    cost_efficiency_score: float
    utilization_vs_cost_ratio: float

@dataclass
class CostOptimizationRecommendation:
    service_id: str
    current_instances: int
    recommended_instances: int
    cost_savings_per_hour: float
    cost_savings_per_month: float
    performance_impact: float
    confidence: float
    reasoning: str
    implementation_time: str

class CostOptimizer:
    """
    Optimizes auto-scaling decisions based on cost considerations
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('cost_optimizer')

        # Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Cost configuration
        self.cost_threshold = config.get('cost_threshold', 100)  # $100 per hour
        self.optimization_interval = config.get('optimization_interval', 300)  # 5 minutes
        self.cost_history_retention = config.get('cost_history_retention', 7 * 24 * 60)  # 7 days

        # Instance cost configurations (per hour)
        self.instance_costs = {
            ServiceType.API_GATEWAY: {
                'small': {'cpu': 0.5, 'memory': 1, 'cost': 0.025},
                'medium': {'cpu': 1, 'memory': 2, 'cost': 0.05},
                'large': {'cpu': 2, 'memory': 4, 'cost': 0.10}
            },
            ServiceType.CHARACTER_PORTAL: {
                'small': {'cpu': 0.5, 'memory': 1, 'cost': 0.03},
                'medium': {'cpu': 1, 'memory': 2, 'cost': 0.06},
                'large': {'cpu': 2, 'memory': 4, 'cost': 0.12}
            },
            ServiceType.AI_MODEL_POOL: {
                'gpu_small': {'cpu': 2, 'memory': 8, 'gpu': 1, 'cost': 0.75},
                'gpu_medium': {'cpu': 4, 'memory': 16, 'gpu': 1, 'cost': 1.25},
                'gpu_large': {'cpu': 8, 'memory': 32, 'gpu': 2, 'cost': 2.50}
            },
            ServiceType.DIALOGUE_SYSTEM: {
                'small': {'cpu': 1, 'memory': 2, 'cost': 0.04},
                'medium': {'cpu': 2, 'memory': 4, 'cost': 0.08},
                'large': {'cpu': 4, 'memory': 8, 'cost': 0.16}
            },
            ServiceType.COMBAT_ENGINE: {
                'small': {'cpu': 1, 'memory': 2, 'cost': 0.035},
                'medium': {'cpu': 2, 'memory': 4, 'cost': 0.07},
                'large': {'cpu': 4, 'memory': 8, 'cost': 0.14}
            },
            ServiceType.WORLD_SIMULATION: {
                'small': {'cpu': 2, 'memory': 4, 'cost': 0.08},
                'medium': {'cpu': 4, 'memory': 8, 'cost': 0.16},
                'large': {'cpu': 8, 'memory': 16, 'cost': 0.32}
            },
            ServiceType.DATABASE: {
                'small': {'cpu': 1, 'memory': 2, 'storage': 20, 'cost': 0.05},
                'medium': {'cpu': 2, 'memory': 4, 'storage': 50, 'cost': 0.10},
                'large': {'cpu': 4, 'memory': 8, 'storage': 100, 'cost': 0.20}
            },
            ServiceType.MESSAGE_QUEUE: {
                'small': {'cpu': 0.5, 'memory': 1, 'cost': 0.02},
                'medium': {'cpu': 1, 'memory': 2, 'cost': 0.04},
                'large': {'cpu': 2, 'memory': 4, 'cost': 0.08}
            },
            ServiceType.FRONTEND: {
                'small': {'cpu': 0.25, 'memory': 0.5, 'cost': 0.015},
                'medium': {'cpu': 0.5, 'memory': 1, 'cost': 0.03},
                'large': {'cpu': 1, 'memory': 2, 'cost': 0.06}
            }
        }

        # Cost optimization strategies
        self.strategies = {
            'aggressive_cost_cutting': {'performance_threshold': 70, 'min_savings': 5},
            'balanced': {'performance_threshold': 85, 'min_savings': 2},
            'performance_priority': {'performance_threshold': 95, 'min_savings': 0.5}
        }

        # Cost history
        self.cost_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Cloud provider pricing APIs
        self.pricing_apis = {
            'aws': 'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json',
            'azure': 'https://prices.azure.com/api/retail/prices',
            'gcp': 'https://cloudbilling.googleapis.com/v1/services/6F81-5844-456A/skus'
        }

    async def optimize_costs(self, service_metrics: Dict[str, deque]) -> List[ScalingDecision]:
        """Main cost optimization function"""
        decisions = []

        for service_id, metrics_queue in service_metrics.items():
            if not metrics_queue:
                continue

            try:
                # Calculate current cost metrics
                cost_metrics = await self._calculate_cost_metrics(service_id, metrics_queue)
                if cost_metrics:
                    # Store cost history
                    self.cost_history[service_id].append(cost_metrics)

                    # Get optimization recommendations
                    recommendations = await self._get_cost_optimization_recommendations(
                        service_id, metrics_queue, cost_metrics
                    )

                    # Convert recommendations to scaling decisions
                    for rec in recommendations:
                        if rec.confidence > 0.7 and rec.cost_savings_per_hour > 1:
                            decision = await self._recommendation_to_scaling_decision(rec, metrics_queue)
                            if decision:
                                decisions.append(decision)

            except Exception as e:
                self.logger.error(f"Error optimizing costs for {service_id}: {e}")

        return decisions

    async def _calculate_cost_metrics(self, service_id: str, metrics_queue: deque) -> Optional[CostMetrics]:
        """Calculate cost metrics for a service"""
        try:
            latest_metrics = metrics_queue[-1]
            service_type = latest_metrics.service_type

            # Get instance type and cost
            instance_config = self._get_instance_config(service_type, 'medium')
            instance_cost = instance_config['cost']

            # Calculate costs
            current_hourly_cost = latest_metrics.instance_count * instance_cost
            daily_cost = current_hourly_cost * 24
            monthly_cost_estimate = daily_cost * 30

            # Calculate efficiency metrics
            avg_cpu = np.mean([m.cpu_usage for m in list(metrics_queue)[-10:]])
            avg_memory = np.mean([m.memory_usage for m in list(metrics_queue)[-10:]])
            utilization_vs_cost = (avg_cpu + avg_memory) / 2 / current_hourly_cost if current_hourly_cost > 0 else 0

            cost_efficiency_score = self._calculate_cost_efficiency_score(
                avg_cpu, avg_memory, current_hourly_cost, service_type
            )

            return CostMetrics(
                service_id=service_id,
                service_type=service_type,
                instance_cost_per_hour=instance_cost,
                current_hourly_cost=current_hourly_cost,
                daily_cost=daily_cost,
                monthly_cost_estimate=monthly_cost_estimate,
                cost_efficiency_score=cost_efficiency_score,
                utilization_vs_cost_ratio=utilization_vs_cost
            )

        except Exception as e:
            self.logger.error(f"Error calculating cost metrics for {service_id}: {e}")
            return None

    def _get_instance_config(self, service_type: ServiceType, size: str = 'medium') -> Dict[str, float]:
        """Get instance configuration for a service type"""
        if service_type in self.instance_costs:
            return self.instance_costs[service_type].get(size, self.instance_costs[service_type]['medium'])
        return {'cpu': 1, 'memory': 2, 'cost': 0.05}

    def _calculate_cost_efficiency_score(self, cpu_usage: float, memory_usage: float, hourly_cost: float, service_type: ServiceType) -> float:
        """Calculate cost efficiency score (0-100)"""
        try:
            # Base efficiency from utilization
            utilization_efficiency = (cpu_usage + memory_usage) / 2

            # Cost factor (higher cost requires higher efficiency)
            cost_factor = min(1.0, 50 / hourly_cost) if hourly_cost > 0 else 1.0

            # Service type efficiency expectations
            service_efficiency_weights = {
                ServiceType.AI_MODEL_POOL: 0.8,  # Higher cost, lower efficiency acceptable
                ServiceType.API_GATEWAY: 1.0,
                ServiceType.CHARACTER_PORTAL: 0.9,
                ServiceType.DIALOGUE_SYSTEM: 0.85,
                ServiceType.COMBAT_ENGINE: 0.9,
                ServiceType.WORLD_SIMULATION: 0.8,
                ServiceType.DATABASE: 0.95,
                ServiceType.MESSAGE_QUEUE: 1.0,
                ServiceType.FRONTEND: 1.0
            }

            service_weight = service_efficiency_weights.get(service_type, 1.0)

            # Final efficiency score
            efficiency_score = utilization_efficiency * cost_factor * service_weight * 100
            return min(100.0, max(0.0, efficiency_score))

        except Exception as e:
            self.logger.error(f"Error calculating cost efficiency score: {e}")
            return 50.0

    async def _get_cost_optimization_recommendations(self, service_id: str, metrics_queue: deque, cost_metrics: CostMetrics) -> List[CostOptimizationRecommendation]:
        """Get cost optimization recommendations"""
        recommendations = []

        try:
            latest_metrics = metrics_queue[-1]
            current_instances = latest_metrics.instance_count

            # Analyze different optimization strategies
            for strategy_name, strategy_config in self.strategies.items():
                rec = await self._analyze_optimization_strategy(
                    service_id, metrics_queue, cost_metrics, strategy_name, strategy_config
                )
                if rec:
                    recommendations.append(rec)

            # Sort by potential savings
            recommendations.sort(key=lambda x: x.cost_savings_per_hour, reverse=True)

            return recommendations[:3]  # Return top 3 recommendations

        except Exception as e:
            self.logger.error(f"Error getting cost optimization recommendations for {service_id}: {e}")
            return []

    async def _analyze_optimization_strategy(self, service_id: str, metrics_queue: deque, cost_metrics: CostMetrics, strategy_name: str, strategy_config: Dict[str, Any]) -> Optional[CostOptimizationRecommendation]:
        """Analyze a specific optimization strategy"""
        try:
            latest_metrics = metrics_queue[-1]
            current_instances = latest_metrics.instance_count
            performance_threshold = strategy_config['performance_threshold']
            min_savings = strategy_config['min_savings']

            # Calculate optimal instance count
            avg_cpu = np.mean([m.cpu_usage for m in list(metrics_queue)[-20:]])
            avg_memory = np.mean([m.memory_usage for m in list(metrics_queue)[-20:]])
            avg_request_rate = np.mean([m.request_rate for m in list(metrics_queue)[-20:]])

            # Find minimum instances that meet performance threshold
            recommended_instances = current_instances
            for instances in range(max(1, current_instances - 3), current_instances + 1):
                projected_cpu = avg_cpu * (current_instances / instances)
                projected_memory = avg_memory * (current_instances / instances)
                projected_requests = avg_request_rate * (current_instances / instances)

                if (projected_cpu <= performance_threshold and
                    projected_memory <= performance_threshold and
                    projected_requests <= 1000):  # Request threshold
                    recommended_instances = instances
                else:
                    break

            # Calculate savings
            if recommended_instances < current_instances:
                hourly_savings = (current_instances - recommended_instances) * cost_metrics.instance_cost_per_hour
                monthly_savings = hourly_savings * 24 * 30

                if hourly_savings >= min_savings:
                    # Calculate performance impact
                    performance_impact = max(0, performance_threshold - avg_cpu)

                    # Calculate confidence
                    confidence = self._calculate_optimization_confidence(
                        metrics_queue, current_instances, recommended_instances, performance_threshold
                    )

                    reasoning = f"Strategy: {strategy_name}. Can reduce from {current_instances} to {recommended_instances} instances while maintaining {performance_threshold}% performance threshold."

                    return CostOptimizationRecommendation(
                        service_id=service_id,
                        current_instances=current_instances,
                        recommended_instances=recommended_instances,
                        cost_savings_per_hour=hourly_savings,
                        cost_savings_per_month=monthly_savings,
                        performance_impact=performance_impact,
                        confidence=confidence,
                        reasoning=reasoning,
                        implementation_time="Immediate"
                    )

        except Exception as e:
            self.logger.error(f"Error analyzing optimization strategy {strategy_name}: {e}")

        return None

    def _calculate_optimization_confidence(self, metrics_queue: deque, current_instances: int, recommended_instances: int, performance_threshold: float) -> float:
        """Calculate confidence in optimization recommendation"""
        try:
            if len(metrics_queue) < 10:
                return 0.3

            # Calculate stability of metrics
            cpu_values = [m.cpu_usage for m in list(metrics_queue)[-20:]]
            cpu_stability = 1.0 - (np.std(cpu_values) / np.mean(cpu_values)) if np.mean(cpu_values) > 0 else 0

            # Check if we're well above threshold
            avg_cpu = np.mean(cpu_values)
            headroom = (avg_cpu - performance_threshold) / performance_threshold if performance_threshold > 0 else 0

            # Consider instance reduction size
            reduction_ratio = (current_instances - recommended_instances) / current_instances
            size_confidence = 1.0 - (reduction_ratio * 0.3)  # Reduce confidence for larger reductions

            # Combine factors
            confidence = cpu_stability * 0.4 + min(1.0, headroom) * 0.4 + size_confidence * 0.2

            return max(0.1, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating optimization confidence: {e}")
            return 0.5

    async def _recommendation_to_scaling_decision(self, recommendation: CostOptimizationRecommendation, metrics_queue: deque) -> Optional[ScalingDecision]:
        """Convert cost optimization recommendation to scaling decision"""
        try:
            if recommendation.recommended_instances < recommendation.current_instances:
                direction = ScaleDirection.DOWN
                reason = f"Cost optimization: {recommendation.reasoning} Savings: ${recommendation.cost_savings_per_hour:.2f}/hour"
            else:
                return None

            return ScalingDecision(
                service_id=recommendation.service_id,
                current_instances=recommendation.current_instances,
                desired_instances=recommendation.recommended_instances,
                direction=direction,
                reason=reason,
                confidence=recommendation.confidence,
                cost_impact=-recommendation.cost_savings_per_hour,  # Negative because it's savings
                execution_time=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error converting recommendation to scaling decision: {e}")
            return None

    async def calculate_scaling_cost(self, service_id: str, current_instances: int, desired_instances: int) -> float:
        """Calculate cost impact of scaling decision"""
        try:
            # Get service type from Redis or metrics
            service_type = await self._get_service_type(service_id)
            if not service_type:
                return 0.0

            instance_config = self._get_instance_config(service_type, 'medium')
            instance_cost = instance_config['cost']

            # Calculate hourly cost difference
            current_cost = current_instances * instance_cost
            new_cost = desired_instances * instance_cost
            cost_impact = new_cost - current_cost

            return cost_impact

        except Exception as e:
            self.logger.error(f"Error calculating scaling cost: {e}")
            return 0.0

    async def _get_service_type(self, service_id: str) -> Optional[ServiceType]:
        """Get service type for a service ID"""
        try:
            # This would typically come from service registry or config
            service_types = {
                'api-gateway': ServiceType.API_GATEWAY,
                'character-portal': ServiceType.CHARACTER_PORTAL,
                'ai-model-pool': ServiceType.AI_MODEL_POOL,
                'dialogue-system': ServiceType.DIALOGUE_SYSTEM,
                'combat-engine': ServiceType.COMBAT_ENGINE,
                'world-simulation': ServiceType.WORLD_SIMULATION
            }

            return service_types.get(service_id)

        except Exception as e:
            self.logger.error(f"Error getting service type for {service_id}: {e}")
            return None

    async def get_cost_report(self, duration_hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'duration_hours': duration_hours,
                'total_cost': 0,
                'services': {},
                'recommendations': [],
                'cost_trends': {},
                'efficiency_scores': {}
            }

            total_cost = 0
            service_costs = {}

            # Calculate costs for each service
            for service_id, cost_history in self.cost_history.items():
                if not cost_history:
                    continue

                latest_cost = cost_history[-1]
                service_costs[service_id] = {
                    'current_hourly_cost': latest_cost.current_hourly_cost,
                    'daily_cost': latest_cost.daily_cost,
                    'monthly_estimate': latest_cost.monthly_cost_estimate,
                    'efficiency_score': latest_cost.cost_efficiency_score,
                    'instance_count': 0  # Would need to be tracked separately
                }

                total_cost += latest_cost.current_hourly_cost

            report['total_cost'] = total_cost
            report['services'] = service_costs

            # Get cost trends
            for service_id in service_costs.keys():
                if service_id in self.cost_history and len(self.cost_history[service_id]) > 1:
                    costs = [c.current_hourly_cost for c in list(self.cost_history[service_id])[-24:]]  # Last 24 hours
                    if costs:
                        trend = np.polyfit(range(len(costs)), costs, 1)[0]
                        report['cost_trends'][service_id] = {
                            'trend': float(trend),
                            'direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                            'average_cost': float(np.mean(costs))
                        }

            return report

        except Exception as e:
            self.logger.error(f"Error generating cost report: {e}")
            return {}

    async def set_budget_alerts(self, service_id: str, hourly_budget: float):
        """Set budget alerts for a service"""
        try:
            alert_config = {
                'service_id': service_id,
                'hourly_budget': hourly_budget,
                'alert_threshold': 0.9,  # Alert at 90% of budget
                'created_at': datetime.now().isoformat()
            }

            self.redis_client.set(f'budget_alert:{service_id}', json.dumps(alert_config))
            self.logger.info(f"Set budget alert for {service_id}: ${hourly_budget}/hour")

        except Exception as e:
            self.logger.error(f"Error setting budget alert: {e}")

    async def check_budget_alerts(self) -> List[Dict[str, Any]]:
        """Check and trigger budget alerts"""
        try:
            alerts = []

            # Get all budget alert configurations
            for key in self.redis_client.scan_iter(match='budget_alert:*'):
                service_id = key.split(':')[1]
                alert_config = json.loads(self.redis_client.get(key))

                if service_id in self.cost_history and self.cost_history[service_id]:
                    current_cost = self.cost_history[service_id][-1].current_hourly_cost
                    budget_threshold = alert_config['hourly_budget'] * alert_config['alert_threshold']

                    if current_cost > budget_threshold:
                        alerts.append({
                            'service_id': service_id,
                            'current_cost': current_cost,
                            'budget': alert_config['hourly_budget'],
                            'threshold': budget_threshold,
                            'over_budget_by': current_cost - alert_config['hourly_budget'],
                            'timestamp': datetime.now().isoformat()
                        })

            return alerts

        except Exception as e:
            self.logger.error(f"Error checking budget alerts: {e}")
            return []