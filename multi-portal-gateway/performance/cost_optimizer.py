#!/usr/bin/env python3
"""
Advanced Cost Optimizer for DMLogn8n Platform
Cloud cost optimization, resource allocation, auto-scaling, and budget management
"""

import asyncio
import json
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import numpy as np
import pandas as pd

# Cloud provider libraries (optional)
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import google.cloud.monitoring_v3
    import google.cloud.billing_v1
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    """Cloud service providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    MULTI_CLOUD = "multi_cloud"
    ON_PREMISE = "on_premise"

class ResourceType(Enum):
    """Resource types for cost tracking"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    AI_ML = "ai_ml"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    BANDWIDTH = "bandwidth"

class CostOptimizationStrategy(Enum):
    """Cost optimization strategies"""
    RIGHTSIZING = "rightsizing"
    SCHEDULED_SCALING = "scheduled_scaling"
    SPOT_INSTANCES = "spot_instances"
    RESERVED_INSTANCES = "reserved_instances"
    SAVINGS_PLANS = "savings_plans"
    AUTO_SCALING = "auto_scaling"
    STORAGE_OPTIMIZATION = "storage_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"

class PricingModel(Enum):
    """Pricing models"""
    ON_DEMAND = "on_demand"
    RESERVED = "reserved"
    SPOT = "spot"
    SAVINGS_PLAN = "savings_plan"
    PAY_AS_YOU_GO = "pay_as_you_go"

@dataclass
class ResourceCost:
    """Resource cost information"""
    resource_id: str
    resource_type: ResourceType
    provider: CloudProvider
    region: str
    hourly_cost: float
    monthly_cost: float
    yearly_cost: float
    pricing_model: PricingModel
    utilization_rate: float
    efficiency_score: float
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class BudgetAlert:
    """Budget alert configuration"""
    budget_id: str
    name: str
    amount: float
    period: str  # daily, weekly, monthly, yearly
    threshold_percent: float
    notification_emails: List[str]
    alert_types: List[str]
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CostOptimization:
    """Cost optimization recommendation"""
    optimization_id: str
    resource_id: str
    optimization_type: CostOptimizationStrategy
    current_monthly_cost: float
    projected_monthly_cost: float
    savings_amount: float
    savings_percent: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    description: str
    steps: List[str]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CostMetrics:
    """Cost metrics over time"""
    timestamp: datetime
    total_cost: float
    compute_cost: float
    storage_cost: float
    network_cost: float
    database_cost: float
    ai_ml_cost: float
    other_cost: float
    resource_count: int
    utilization_score: float

class CostOptimizer:
    """Advanced cloud cost optimization and management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.resources = {}
        self.cost_history = deque(maxlen=self.config.get('history_size', 10000))
        self.budgets = {}
        self.optimizations = {}
        self.cost_alerts = []

        # Cloud provider clients
        self.cloud_clients = {}
        self._initialize_cloud_clients()

        # Optimization settings
        self.auto_optimization = self.config.get('auto_optimization', False)
        self.budget_monitoring = self.config.get('budget_monitoring', True)
        self.cost_tracking = self.config.get('cost_tracking', True)
        self.rightsizing_enabled = self.config.get('rightsizing_enabled', True)

        # Cost thresholds
        self.cost_threshold = self.config.get('cost_threshold', 1000.0)  # monthly
        self.utilization_threshold = self.config.get('utilization_threshold', 0.3)  # 30%

        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        # Currency and pricing
        self.currency = self.config.get('currency', 'USD')
        self.exchange_rates = {}

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'history_size': 10000,
            'currency': 'USD',
            'auto_optimization': False,
            'budget_monitoring': True,
            'cost_tracking': True,
            'rightsizing_enabled': True,
            'cost_threshold': 1000.0,
            'utilization_threshold': 0.3,
            'monitoring_interval': 300.0,  # 5 minutes
            'optimization_interval': 3600.0,  # 1 hour
            'budget_check_interval': 1800.0,  # 30 minutes
            'providers': {
                'aws': {
                    'enabled': False,
                    'region': 'us-east-1',
                    'access_key': '',
                    'secret_key': ''
                },
                'gcp': {
                    'enabled': False,
                    'project_id': '',
                    'credentials_path': ''
                },
                'azure': {
                    'enabled': False,
                    'subscription_id': '',
                    'resource_group': ''
                }
            },
            'optimization_rules': {
                'unused_resources_threshold': 0.05,  # 5% utilization
                'underutilized_threshold': 0.3,     # 30% utilization
                'overprovisioned_threshold': 0.7,   # 70% threshold for rightsizing
                'spot_instance_discount': 0.7,      # 70% discount target
                'reserved_commitment': 3             # 3-year commitment
            }
        }

    def _initialize_cloud_clients(self):
        """Initialize cloud provider clients"""
        providers_config = self.config.get('providers', {})

        # AWS client
        if providers_config.get('aws', {}).get('enabled', False) and AWS_AVAILABLE:
            try:
                aws_config = providers_config['aws']
                self.cloud_clients['aws'] = {
                    'ec2': boto3.client(
                        'ec2',
                        aws_region_name=aws_config.get('region', 'us-east-1'),
                        aws_access_key_id=aws_config.get('access_key'),
                        aws_secret_access_key=aws_config.get('secret_key')
                    ),
                    'cloudwatch': boto3.client(
                        'cloudwatch',
                        aws_region_name=aws_config.get('region', 'us-east-1'),
                        aws_access_key_id=aws_config.get('access_key'),
                        aws_secret_access_key=aws_config.get('secret_key')
                    ),
                    'ce': boto3.client(
                        'ce',
                        aws_region_name='us-east-1',
                        aws_access_key_id=aws_config.get('access_key'),
                        aws_secret_access_key=aws_config.get('secret_key')
                    )
                }
                logger.info("AWS client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AWS client: {e}")

        # GCP client
        if providers_config.get('gcp', {}).get('enabled', False) and GCP_AVAILABLE:
            try:
                gcp_config = providers_config['gcp']
                # GCP client initialization would go here
                logger.info("GCP client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GCP client: {e}")

        # Azure client
        if providers_config.get('azure', {}).get('enabled', False) and AZURE_AVAILABLE:
            try:
                azure_config = providers_config['azure']
                # Azure client initialization would go here
                logger.info("Azure client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure client: {e}")

    def start_monitoring(self):
        """Start cost monitoring"""
        if self.monitoring_active:
            logger.warning("Cost monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Cost monitoring started")

    def stop_monitoring(self):
        """Stop cost monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Cost monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect cost data
                if self.cost_tracking:
                    self._collect_cost_data()

                # Check budgets
                if self.budget_monitoring:
                    self._check_budgets()

                # Generate optimizations
                if self.auto_optimization:
                    self._generate_optimizations()

                time.sleep(self.config.get('monitoring_interval', 300.0))

            except Exception as e:
                logger.error(f"Error in cost monitoring loop: {e}")
                time.sleep(60)

    def _collect_cost_data(self):
        """Collect cost data from cloud providers"""
        current_time = datetime.now()

        # AWS cost data
        if 'aws' in self.cloud_clients:
            try:
                aws_costs = self._collect_aws_costs()
                if aws_costs:
                    self._update_cost_metrics(aws_costs, CloudProvider.AWS)
            except Exception as e:
                logger.error(f"Failed to collect AWS costs: {e}")

        # GCP cost data
        if 'gcp' in self.cloud_clients:
            try:
                gcp_costs = self._collect_gcp_costs()
                if gcp_costs:
                    self._update_cost_metrics(gcp_costs, CloudProvider.GCP)
            except Exception as e:
                logger.error(f"Failed to collect GCP costs: {e}")

        # Azure cost data
        if 'azure' in self.cloud_clients:
            try:
                azure_costs = self._collect_azure_costs()
                if azure_costs:
                    self._update_cost_metrics(azure_costs, CloudProvider.AZURE)
            except Exception as e:
                logger.error(f"Failed to collect Azure costs: {e}")

    def _collect_aws_costs(self) -> Dict[str, float]:
        """Collect AWS cost data"""
        try:
            ce_client = self.cloud_clients['aws']['ce']

            # Get cost and usage data for the last hour
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'End': end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                Granularity='HOURLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )

            costs = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    costs[service] = amount

            return costs

        except Exception as e:
            logger.error(f"Error collecting AWS costs: {e}")
            return {}

    def _collect_gcp_costs(self) -> Dict[str, float]:
        """Collect GCP cost data"""
        # Placeholder implementation
        # Would implement GCP Billing API integration
        return {}

    def _collect_azure_costs(self) -> Dict[str, float]:
        """Collect Azure cost data"""
        # Placeholder implementation
        # Would implement Azure Cost Management API integration
        return {}

    def _update_cost_metrics(self, costs: Dict[str, float], provider: CloudProvider):
        """Update cost metrics"""
        current_time = datetime.now()

        # Categorize costs by resource type
        compute_cost = costs.get('Amazon EC2', 0) + costs.get('Compute Engine', 0) + costs.get('Virtual Machines', 0)
        storage_cost = costs.get('Amazon S3', 0) + costs.get('Cloud Storage', 0) + costs.get('Storage', 0)
        network_cost = costs.get('Amazon CloudFront', 0) + costs.get('Network', 0)
        database_cost = costs.get('Amazon RDS', 0) + costs.get('Cloud SQL', 0) + costs.get('SQL Database', 0)
        ai_ml_cost = costs.get('Amazon SageMaker', 0) + costs.get('AI Platform', 0) + costs.get('Azure ML', 0)

        total_cost = sum(costs.values())

        metrics = CostMetrics(
            timestamp=current_time,
            total_cost=total_cost,
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=network_cost,
            database_cost=database_cost,
            ai_ml_cost=ai_ml_cost,
            other_cost=total_cost - (compute_cost + storage_cost + network_cost + database_cost + ai_ml_cost),
            resource_count=len(self.resources),
            utilization_score=self._calculate_utilization_score()
        )

        self.cost_history.append(metrics)

    def _calculate_utilization_score(self) -> float:
        """Calculate overall resource utilization score"""
        if not self.resources:
            return 0.0

        total_utilization = sum(resource.utilization_rate for resource in self.resources.values())
        return total_utilization / len(self.resources)

    def _check_budgets(self):
        """Check budget thresholds and send alerts"""
        current_time = datetime.now()
        current_month_costs = self._get_current_month_costs()

        for budget_id, budget in self.budgets.items():
            if not budget.active:
                continue

            # Calculate current period cost
            if budget.period == 'monthly':
                period_cost = current_month_costs
            else:
                # Implement other periods (daily, weekly, yearly)
                period_cost = current_month_costs

            # Check threshold
            threshold_amount = budget.amount * (budget.threshold_percent / 100)
            if period_cost >= threshold_amount:
                self._send_budget_alert(budget, period_cost)

    def _get_current_month_costs(self) -> float:
        """Get total costs for current month"""
        current_time = datetime.now()
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        month_costs = [
            metric.total_cost for metric in self.cost_history
            if metric.timestamp >= month_start
        ]

        return sum(month_costs)

    def _send_budget_alert(self, budget: BudgetAlert, current_cost: float):
        """Send budget alert"""
        alert_message = (
            f"Budget Alert: {budget.name}\n"
            f"Budget Amount: ${budget.amount:.2f}\n"
            f"Current Cost: ${current_cost:.2f}\n"
            f"Threshold: {budget.threshold_percent}%\n"
            f"Usage: {(current_cost / budget.amount * 100):.1f}%"
        )

        logger.warning(alert_message)

        # Add to cost alerts
        self.cost_alerts.append({
            'budget_id': budget.budget_id,
            'message': alert_message,
            'timestamp': datetime.now(),
            'current_cost': current_cost,
            'threshold_percent': budget.threshold_percent
        })

        # Send notifications (would integrate with email/SNS/etc.)
        for email in budget.notification_emails:
            logger.info(f"Sending budget alert to {email}")

    def _generate_optimizations(self):
        """Generate cost optimization recommendations"""
        try:
            # Rightsizing optimizations
            if self.rightsizing_enabled:
                self._generate_rightsizing_optimizations()

            # Unused resource optimizations
            self._generate_unused_resource_optimizations()

            # Storage optimizations
            self._generate_storage_optimizations()

            # Network optimizations
            self._generate_network_optimizations()

        except Exception as e:
            logger.error(f"Error generating optimizations: {e}")

    def _generate_rightsizing_optimizations(self):
        """Generate rightsizing recommendations"""
        optimization_rules = self.config.get('optimization_rules', {})
        underutilized_threshold = optimization_rules.get('underutilized_threshold', 0.3)

        for resource_id, resource in self.resources.items():
            if resource.utilization_rate < underutilized_threshold:
                # Create rightsizing recommendation
                current_size = self._get_current_resource_size(resource)
                recommended_size = self._calculate_recommended_size(resource)

                if recommended_size and recommended_size != current_size:
                    savings_percent = self._calculate_rightsizing_savings(resource, recommended_size)

                    optimization = CostOptimization(
                        optimization_id=f"rightsizing_{resource_id}_{int(time.time())}",
                        resource_id=resource_id,
                        optimization_type=CostOptimizationStrategy.RIGHTSIZING,
                        current_monthly_cost=resource.monthly_cost,
                        projected_monthly_cost=resource.monthly_cost * (1 - savings_percent),
                        savings_amount=resource.monthly_cost * savings_percent,
                        savings_percent=savings_percent,
                        implementation_effort='medium',
                        risk_level='low',
                        description=f"Rightsize {resource.resource_type.value} resource {resource_id}",
                        steps=[
                            f"Current size: {current_size}",
                            f"Recommended size: {recommended_size}",
                            f"Current utilization: {resource.utilization_rate:.1%}",
                            f"Projected savings: {savings_percent:.1%}"
                        ]
                    )

                    self.optimizations[optimization.optimization_id] = optimization

    def _generate_unused_resource_optimizations(self):
        """Generate unused resource cleanup recommendations"""
        optimization_rules = self.config.get('optimization_rules', {})
        unused_threshold = optimization_rules.get('unused_resources_threshold', 0.05)

        for resource_id, resource in self.resources.items():
            if resource.utilization_rate < unused_threshold:
                optimization = CostOptimization(
                    optimization_id=f"unused_{resource_id}_{int(time.time())}",
                    resource_id=resource_id,
                    optimization_type=CostOptimizationStrategy.SCHEDULED_SCALING,
                    current_monthly_cost=resource.monthly_cost,
                    projected_monthly_cost=0,
                    savings_amount=resource.monthly_cost,
                    savings_percent=100.0,
                    implementation_effort='low',
                    risk_level='low',
                    description=f"Terminate unused {resource.resource_type.value} resource {resource_id}",
                    steps=[
                        f"Resource utilization: {resource.utilization_rate:.1%}",
                        "Resource appears to be unused",
                        "Consider terminating or stopping the resource",
                        f"Monthly savings: ${resource.monthly_cost:.2f}"
                    ]
                )

                self.optimizations[optimization.optimization_id] = optimization

    def _generate_storage_optimizations(self):
        """Generate storage optimization recommendations"""
        # Placeholder for storage optimizations
        pass

    def _generate_network_optimizations(self):
        """Generate network optimization recommendations"""
        # Placeholder for network optimizations
        pass

    def _get_current_resource_size(self, resource: ResourceCost) -> str:
        """Get current resource size"""
        # This would implement size detection based on resource type
        return "medium"

    def _calculate_recommended_size(self, resource: ResourceCost) -> Optional[str]:
        """Calculate recommended resource size based on utilization"""
        if resource.utilization_rate < 0.2:
            return "small"
        elif resource.utilization_rate < 0.7:
            return "medium"
        else:
            return "large"

    def _calculate_rightsizing_savings(self, resource: ResourceCost, recommended_size: str) -> float:
        """Calculate potential savings from rightsizing"""
        # Simplified calculation
        if recommended_size == "small":
            return 0.6  # 60% savings
        elif recommended_size == "medium":
            return 0.3  # 30% savings
        else:
            return 0.0

    def add_resource(self, resource: ResourceCost):
        """Add resource for cost tracking"""
        self.resources[resource.resource_id] = resource
        logger.info(f"Added resource for cost tracking: {resource.resource_id}")

    def remove_resource(self, resource_id: str):
        """Remove resource from cost tracking"""
        if resource_id in self.resources:
            del self.resources[resource_id]
            logger.info(f"Removed resource from cost tracking: {resource_id}")

    def create_budget(self, budget: BudgetAlert) -> str:
        """Create budget alert"""
        self.budgets[budget.budget_id] = budget
        logger.info(f"Created budget: {budget.name} (${budget.amount:.2f})")
        return budget.budget_id

    def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> bool:
        """Update budget configuration"""
        if budget_id not in self.budgets:
            return False

        budget = self.budgets[budget_id]
        for key, value in updates.items():
            if hasattr(budget, key):
                setattr(budget, key, value)

        logger.info(f"Updated budget: {budget_id}")
        return True

    def delete_budget(self, budget_id: str) -> bool:
        """Delete budget"""
        if budget_id not in self.budgets:
            return False

        del self.budgets[budget_id]
        logger.info(f"Deleted budget: {budget_id}")
        return True

    def get_cost_report(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        if time_window is None:
            time_window = timedelta(days=30)

        cutoff_time = datetime.now() - time_window
        recent_metrics = [m for m in self.cost_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"error": "No cost data available for specified time window"}

        # Calculate cost statistics
        total_costs = [m.total_cost for m in recent_metrics]
        compute_costs = [m.compute_cost for m in recent_metrics]
        storage_costs = [m.storage_cost for m in recent_metrics]
        network_costs = [m.network_cost for m in recent_metrics]

        # Resource type breakdown
        resource_costs = defaultdict(list)
        for resource_id, resource in self.resources.items():
            resource_costs[resource.resource_type.value].append(resource.monthly_cost)

        # Provider breakdown
        provider_costs = defaultdict(float)
        for resource in self.resources.values():
            provider_costs[resource.provider.value] += resource.monthly_cost

        report = {
            'time_window': str(time_window),
            'currency': self.currency,
            'total_costs': {
                'current_month': sum(total_costs),
                'average_daily': np.mean(total_costs),
                'max_daily': np.max(total_costs),
                'min_daily': np.min(total_costs),
                'trend': self._calculate_cost_trend(recent_metrics)
            },
            'cost_breakdown': {
                'compute': {
                    'total': sum(compute_costs),
                    'percentage': (sum(compute_costs) / sum(total_costs) * 100) if total_costs else 0
                },
                'storage': {
                    'total': sum(storage_costs),
                    'percentage': (sum(storage_costs) / sum(total_costs) * 100) if total_costs else 0
                },
                'network': {
                    'total': sum(network_costs),
                    'percentage': (sum(network_costs) / sum(total_costs) * 100) if total_costs else 0
                }
            },
            'resource_costs': {
                resource_type: {
                    'total': sum(costs),
                    'count': len(costs),
                    'average': np.mean(costs) if costs else 0
                }
                for resource_type, costs in resource_costs.items()
            },
            'provider_costs': dict(provider_costs),
            'resource_summary': {
                'total_resources': len(self.resources),
                'avg_utilization': self._calculate_utilization_score(),
                'underutilized_resources': len([
                    r for r in self.resources.values() if r.utilization_rate < self.utilization_threshold
                ])
            },
            'optimizations': {
                'total_opportunities': len(self.optimizations),
                'potential_monthly_savings': sum(opt.savings_amount for opt in self.optimizations.values()),
                'high_impact_optimizations': len([
                    opt for opt in self.optimizations.values() if opt.savings_percent > 0.3
                ])
            },
            'budgets': {
                'active_budgets': len([b for b in self.budgets.values() if b.active]),
                'total_budget_amount': sum(b.amount for b in self.budgets.values() if b.active),
                'recent_alerts': len([a for a in self.cost_alerts if a['timestamp'] > datetime.now() - timedelta(days=7)])
            }
        }

        # Add recommendations
        report['recommendations'] = self._generate_cost_recommendations()

        return report

    def _calculate_cost_trend(self, metrics: List[CostMetrics]) -> str:
        """Calculate cost trend"""
        if len(metrics) < 2:
            return "insufficient_data"

        # Simple linear regression to determine trend
        x = np.arange(len(metrics))
        y = np.array([m.total_cost for m in metrics])

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _generate_cost_recommendations(self) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []

        if not self.resources:
            return ["No resources available for analysis"]

        current_month_costs = self._get_current_month_costs()

        # Budget recommendations
        if not self.budgets:
            recommendations.append("Consider setting up budgets to track and control spending")

        # Utilization recommendations
        underutilized_count = len([
            r for r in self.resources.values() if r.utilization_rate < self.utilization_threshold
        ])
        if underutilized_count > 0:
            recommendations.append(f"Found {underutilized_count} underutilized resources. Consider rightsizing or terminating")

        # Cost trend recommendations
        recent_metrics = list(self.cost_history)[-30:]  # Last 30 data points
        if len(recent_metrics) >= 7:
            trend = self._calculate_cost_trend(recent_metrics)
            if trend == "increasing":
                recommendations.append("Costs are trending upward. Review recent changes and consider optimizations")
            elif trend == "stable" and current_month_costs > self.cost_threshold:
                recommendations.append("Costs are stable but high. Focus on efficiency improvements")

        # Optimization recommendations
        if self.optimizations:
            high_savings_opts = [opt for opt in self.optimizations.values() if opt.savings_percent > 0.2]
            if high_savings_opts:
                recommendations.append(f"Found {len(high_savings_opts)} high-impact optimization opportunities")

        return recommendations

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization opportunities report"""
        optimizations_by_type = defaultdict(list)
        optimizations_by_risk = defaultdict(list)

        for optimization in self.optimizations.values():
            optimizations_by_type[optimization.optimization_type.value].append(optimization)
            optimizations_by_risk[optimization.risk_level].append(optimization)

        # Calculate potential savings
        total_monthly_savings = sum(opt.savings_amount for opt in self.optimizations.values())

        return {
            'total_optimizations': len(self.optimizations),
            'total_monthly_savings': total_monthly_savings,
            'optimizations_by_type': {
                opt_type: {
                    'count': len(opts),
                    'total_savings': sum(opt.savings_amount for opt in opts),
                    'avg_savings': np.mean([opt.savings_amount for opt in opts]) if opts else 0
                }
                for opt_type, opts in optimizations_by_type.items()
            },
            'optimizations_by_risk': {
                risk_level: {
                    'count': len(opts),
                    'total_savings': sum(opt.savings_amount for opt in opts)
                }
                for risk_level, opts in optimizations_by_risk.items()
            },
            'top_optimizations': sorted(
                self.optimizations.values(),
                key=lambda x: x.savings_amount,
                reverse=True
            )[:10],
            'quick_wins': [
                opt for opt in self.optimizations.values()
                if opt.implementation_effort == 'low' and opt.savings_percent > 0.1
            ]
        }

    def apply_optimization(self, optimization_id: str) -> bool:
        """Apply cost optimization"""
        if optimization_id not in self.optimizations:
            return False

        optimization = self.optimizations[optimization_id]

        try:
            logger.info(f"Applying optimization: {optimization.description}")

            # Implementation would depend on optimization type
            if optimization.optimization_type == CostOptimizationStrategy.RIGHTSIZING:
                # Implement rightsizing logic
                pass
            elif optimization.optimization_type == CostOptimizationStrategy.SCHEDULED_SCALING:
                # Implement scaling logic
                pass

            # Mark optimization as applied
            optimization.applied = True
            optimization.applied_at = datetime.now()

            logger.info(f"Optimization applied successfully: {optimization_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply optimization {optimization_id}: {e}")
            return False

    def cleanup(self):
        """Cleanup resources and stop monitoring"""
        self.stop_monitoring()
        self.resources.clear()
        self.budgets.clear()
        self.optimizations.clear()
        self.cost_history.clear()
        logger.info("Cost optimizer cleanup completed")

# Example usage
if __name__ == "__main__":
    def main():
        # Initialize cost optimizer
        optimizer = CostOptimizer({
            'auto_optimization': False,
            'budget_monitoring': True,
            'cost_tracking': True,
            'currency': 'USD'
        })

        # Start monitoring
        optimizer.start_monitoring()

        try:
            # Add example resources
            resource1 = ResourceCost(
                resource_id="server-001",
                resource_type=ResourceType.COMPUTE,
                provider=CloudProvider.AWS,
                region="us-east-1",
                hourly_cost=0.10,
                monthly_cost=72.0,
                yearly_cost=864.0,
                pricing_model=PricingModel.ON_DEMAND,
                utilization_rate=0.25,  # 25% utilization
                efficiency_score=0.6,
                tags={"Environment": "production", "Team": "backend"}
            )

            resource2 = ResourceCost(
                resource_id="database-001",
                resource_type=ResourceType.DATABASE,
                provider=CloudProvider.AWS,
                region="us-east-1",
                hourly_cost=0.20,
                monthly_cost=144.0,
                yearly_cost=1728.0,
                pricing_model=PricingModel.RESERVED,
                utilization_rate=0.85,  # 85% utilization
                efficiency_score=0.9,
                tags={"Environment": "production", "Team": "backend"}
            )

            optimizer.add_resource(resource1)
            optimizer.add_resource(resource2)

            # Create budget
            budget = BudgetAlert(
                budget_id="production-budget",
                name="Production Monthly Budget",
                amount=500.0,
                period="monthly",
                threshold_percent=80.0,
                notification_emails=["admin@company.com"],
                alert_types=["email", "slack"]
            )

            optimizer.create_budget(budget)

            # Get cost report
            report = optimizer.get_cost_report()
            print(f"Cost report: {json.dumps(report, indent=2, default=str)}")

            # Get optimization report
            opt_report = optimizer.get_optimization_report()
            print(f"Optimization report: {json.dumps(opt_report, indent=2, default=str)}")

            # Run for a while to collect data
            time.sleep(10)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Cleanup
            optimizer.cleanup()

    # Run example
    main()