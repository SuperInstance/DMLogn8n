#!/usr/bin/env python3
"""
DMLogn8n A/B Testing Experiment Manager
Manages A/B testing experiments with statistical analysis and automatic optimization
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import redis
import aioredis
import numpy as np
import pandas as pd
from scipy import stats
import yaml
from pydantic import BaseModel, Field
import asyncio_mqtt as aiomqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED_EARLY = "stopped_early"

class TrafficAllocationType(Enum):
    UNIFORM = "uniform"
    WEIGHTED = "weighted"
    THOMPSON_SAMPLING = "thompson_sampling"
    MULTI_ARMED_BANDIT = "multi_armed_bandit"

class MetricType(Enum):
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    PERFORMANCE = "performance"
    CUSTOM = "custom"

class StatisticalTest(Enum):
    Z_TEST = "z_test"
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    BAYESIAN = "bayesian"

@dataclass
class ExperimentVariant:
    id: str
    name: str
    description: str
    traffic_percentage: float
    config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False

@dataclass
class ExperimentMetric:
    id: str
    name: str
    description: str
    metric_type: MetricType
    target_value: str  # "higher", "lower", or specific value
    statistical_test: StatisticalTest
    significance_level: float = 0.05
    minimum_effect_size: float = 0.01
    custom_formula: Optional[str] = None

@dataclass
class ExperimentHypothesis:
    primary_metric: str
    expected_effect: str  # "increase", "decrease", "no_change"
    expected_magnitude: float  # Expected effect size
    confidence_level: float = 0.95

@dataclass
class ExperimentResult:
    variant_id: str
    metric_id: str
    value: float
    sample_size: int
    standard_error: float
    confidence_interval: Tuple[float, float]
    p_value: float
    is_statistically_significant: bool
    effect_size: float

@dataclass
class Experiment:
    id: str
    name: str
    description: str
    hypothesis: ExperimentHypothesis
    variants: List[ExperimentVariant]
    metrics: List[ExperimentMetric]
    traffic_allocation_type: TrafficAllocationType
    target_audience: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    minimum_sample_size: int = 1000
    duration_days: int = 14
    auto_stop_enabled: bool = True
    early_stopping_threshold: float = 0.95
    tags: List[str] = field(default_factory=list)

class ExperimentRequest(BaseModel):
    user_id: str
    experiment_id: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ExperimentResponse(BaseModel):
    experiment_id: str
    variant_id: str
    variant_name: str
    config: Dict[str, Any]
    is_control: bool
    timestamp: datetime

class ABTestManager:
    """Main A/B testing experiment manager"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> experiment_id -> variant_id
        self.experiment_results: Dict[str, List[ExperimentResult]] = {}

        # Event handlers
        self.experiment_handlers: Dict[str, List[Callable]] = []
        self.metric_handlers: List[Callable] = []

        # Load default experiments
        self._load_default_experiments()

    async def initialize(self):
        """Initialize the experiment manager"""
        try:
            # Initialize Redis clients
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)

            # Load experiments from Redis
            await self._load_experiments_from_redis()

            # Start background tasks
            asyncio.create_task(self._experiment_monitor_task())
            asyncio.create_task(self._results_analysis_task())

            logger.info("A/B testing experiment manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize experiment manager: {e}")
            raise

    def _load_default_experiments(self):
        """Load default A/B testing experiments"""
        # AI Model Comparison Experiment
        ai_model_experiment = Experiment(
            id="exp_ai_model_comparison",
            name="AI Model Comparison Test",
            description="Compare different AI models for dialogue generation quality",
            hypothesis=ExperimentHypothesis(
                primary_metric="dialogue_quality_score",
                expected_effect="increase",
                expected_magnitude=0.15,
                confidence_level=0.95
            ),
            variants=[
                ExperimentVariant(
                    id="control_gpt4",
                    name="GPT-4 (Control)",
                    description="Standard GPT-4 model",
                    traffic_percentage=50.0,
                    is_control=True,
                    config={"model": "gpt-4", "temperature": 0.7, "max_tokens": 150}
                ),
                ExperimentVariant(
                    id="variant_claude",
                    name="Claude (Variant)",
                    description="Claude AI model",
                    traffic_percentage=50.0,
                    config={"model": "claude-3-sonnet", "temperature": 0.8, "max_tokens": 150}
                )
            ],
            metrics=[
                ExperimentMetric(
                    id="dialogue_quality_score",
                    name="Dialogue Quality Score",
                    description="User-rated dialogue quality (1-10)",
                    metric_type=MetricType.ENGAGEMENT,
                    target_value="higher",
                    statistical_test=StatisticalTest.T_TEST,
                    significance_level=0.05,
                    minimum_effect_size=0.1
                ),
                ExperimentMetric(
                    id="response_time",
                    name="AI Response Time",
                    description="Time to generate AI response (seconds)",
                    metric_type=MetricType.PERFORMANCE,
                    target_value="lower",
                    statistical_test=StatisticalTest.MANN_WHITNEY,
                    significance_level=0.05,
                    minimum_effect_size=0.2
                )
            ],
            traffic_allocation_type=TrafficAllocationType.UNIFORM,
            target_audience={"all_users": True},
            minimum_sample_size=2000,
            duration_days=21,
            tags=["ai", "dialogue", "model_comparison"]
        )

        # Combat Mechanics Experiment
        combat_experiment = Experiment(
            id="exp_combat_damage_variance",
            name="Combat Damage Variance Test",
            description="Test different damage calculation methods for combat",
            hypothesis=ExperimentHypothesis(
                primary_metric="combat_satisfaction",
                expected_effect="increase",
                expected_magnitude=0.1,
                confidence_level=0.9
            ),
            variants=[
                ExperimentVariant(
                    id="control_standard",
                    name="Standard Damage (Control)",
                    description="Standard damage calculation",
                    traffic_percentage=33.3,
                    is_control=True,
                    config={"method": "standard", "variance": 0.1}
                ),
                ExperimentVariant(
                    id="variant_critical",
                    name="Critical Hit System",
                    description="Enhanced critical hit system",
                    traffic_percentage=33.3,
                    config={"method": "critical", "critical_chance": 0.15, "critical_multiplier": 2.0}
                ),
                ExperimentVariant(
                    id="variant_adaptive",
                    name="Adaptive Damage",
                    description="Adaptive damage based on player skill",
                    traffic_percentage=33.4,
                    config={"method": "adaptive", "skill_factor": 0.2}
                )
            ],
            metrics=[
                ExperimentMetric(
                    id="combat_satisfaction",
                    name="Combat Satisfaction",
                    description="Player satisfaction with combat mechanics",
                    metric_type=MetricType.ENGAGEMENT,
                    target_value="higher",
                    statistical_test=StatisticalTest.Z_TEST
                ),
                ExperimentMetric(
                    id="combat_duration",
                    name="Combat Duration",
                    description="Average combat duration in seconds",
                    metric_type=MetricType.ENGAGEMENT,
                    target_value="lower",
                    statistical_test=StatisticalTest.T_TEST
                )
            ],
            traffic_allocation_type=TrafficAllocationType.UNIFORM,
            target_audience={"level_range": [5, 50]},
            minimum_sample_size=1500,
            duration_days=14,
            tags=["combat", "gameplay", "mechanics"]
        )

        # UI Animations Experiment
        ui_experiment = Experiment(
            id="exp_ui_animations",
            name="UI Animations Performance Test",
            description="Test impact of UI animations on user engagement",
            hypothesis=ExperimentHypothesis(
                primary_metric="session_duration",
                expected_effect="increase",
                expected_magnitude=0.05,
                confidence_level=0.9
            ),
            variants=[
                ExperimentVariant(
                    id="control_minimal",
                    name="Minimal Animations (Control)",
                    description="Basic UI animations",
                    traffic_percentage=50.0,
                    is_control=True,
                    config={"animation_level": "minimal", "transition_speed": 0.2}
                ),
                ExperimentVariant(
                    id="variant_enhanced",
                    name="Enhanced Animations",
                    description="Rich UI animations and transitions",
                    traffic_percentage=50.0,
                    config={"animation_level": "enhanced", "transition_speed": 0.3, "particle_effects": True}
                )
            ],
            metrics=[
                ExperimentMetric(
                    id="session_duration",
                    name="Session Duration",
                    description="Average session duration in minutes",
                    metric_type=MetricType.ENGAGEMENT,
                    target_value="higher",
                    statistical_test=StatisticalTest.Z_TEST
                ),
                ExperimentMetric(
                    id="ui_responsiveness",
                    name="UI Responsiveness Score",
                    description="User-rated UI responsiveness",
                    metric_type=MetricType.ENGAGEMENT,
                    target_value="higher",
                    statistical_test=StatisticalTest.T_TEST
                )
            ],
            traffic_allocation_type=TrafficAllocationType.UNIFORM,
            target_audience={"platform": ["web", "desktop"]},
            minimum_sample_size=3000,
            duration_days=7,
            tags=["ui", "ux", "performance"]
        )

        self.experiments[ai_model_experiment.id] = ai_model_experiment
        self.experiments[combat_experiment.id] = combat_experiment
        self.experiments[ui_experiment.id] = ui_experiment

    async def _load_experiments_from_redis(self):
        """Load experiments from Redis"""
        try:
            experiment_data = await self.async_redis_client.hgetall("experiments")
            for exp_id, exp_json in experiment_data.items():
                exp_dict = json.loads(exp_json)
                # Reconstruct experiment object
                experiment = self._dict_to_experiment(exp_dict)
                self.experiments[exp_id] = experiment

            # Load user assignments
            assignment_data = await self.async_redis_client.hgetall("user_assignments")
            for user_id, assignments_json in assignment_data.items():
                self.user_assignments[user_id] = json.loads(assignments_json)

            logger.info(f"Loaded {len(self.experiments)} experiments from Redis")
        except Exception as e:
            logger.warning(f"Failed to load experiments from Redis: {e}")

    def _dict_to_experiment(self, exp_dict: Dict[str, Any]) -> Experiment:
        """Convert dictionary to Experiment object"""
        variants = [
            ExperimentVariant(**variant) for variant in exp_dict['variants']
        ]
        metrics = [
            ExperimentMetric(**metric) for metric in exp_dict['metrics']
        ]
        hypothesis = ExperimentHypothesis(**exp_dict['hypothesis'])

        return Experiment(
            id=exp_dict['id'],
            name=exp_dict['name'],
            description=exp_dict['description'],
            hypothesis=hypothesis,
            variants=variants,
            metrics=metrics,
            traffic_allocation_type=TrafficAllocationType(exp_dict['traffic_allocation_type']),
            target_audience=exp_dict['target_audience'],
            start_date=datetime.fromisoformat(exp_dict['start_date']) if exp_dict.get('start_date') else None,
            end_date=datetime.fromisoformat(exp_dict['end_date']) if exp_dict.get('end_date') else None,
            status=ExperimentStatus(exp_dict['status']),
            created_at=datetime.fromisoformat(exp_dict['created_at']),
            updated_at=datetime.fromisoformat(exp_dict['updated_at']),
            created_by=exp_dict.get('created_by', 'system'),
            minimum_sample_size=exp_dict.get('minimum_sample_size', 1000),
            duration_days=exp_dict.get('duration_days', 14),
            auto_stop_enabled=exp_dict.get('auto_stop_enabled', True),
            early_stopping_threshold=exp_dict.get('early_stopping_threshold', 0.95),
            tags=exp_dict.get('tags', [])
        )

    def assign_user_to_variant(self, user_id: str, experiment_id: str, context: Dict[str, Any] = None) -> Optional[ExperimentVariant]:
        """Assign a user to a variant for an experiment"""
        if context is None:
            context = {}

        experiment = self.experiments.get(experiment_id)
        if not experiment:
            logger.warning(f"Experiment {experiment_id} not found")
            return None

        if experiment.status != ExperimentStatus.RUNNING:
            logger.warning(f"Experiment {experiment_id} is not running")
            return None

        # Check if user is in target audience
        if not self._user_in_target_audience(user_id, experiment, context):
            return None

        # Check if user is already assigned
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}

        if experiment_id in self.user_assignments[user_id]:
            variant_id = self.user_assignments[user_id][experiment_id]
            for variant in experiment.variants:
                if variant.id == variant_id:
                    return variant

        # Assign to variant
        variant = self._select_variant(user_id, experiment)
        if variant:
            self.user_assignments[user_id][experiment_id] = variant.id

            # Save assignment to Redis
            asyncio.create_task(self._save_user_assignment(user_id, experiment_id, variant.id))

            # Log assignment
            self._log_assignment(user_id, experiment_id, variant.id, context)

        return variant

    def _user_in_target_audience(self, user_id: str, experiment: Experiment, context: Dict[str, Any]) -> bool:
        """Check if user belongs to experiment's target audience"""
        target = experiment.target_audience

        if target.get("all_users", False):
            return True

        # Check level range
        if "level_range" in target:
            user_level = context.get("level", 0)
            min_level, max_level = target["level_range"]
            if not (min_level <= user_level <= max_level):
                return False

        # Check platform
        if "platform" in target:
            user_platform = context.get("platform", "unknown")
            if user_platform not in target["platform"]:
                return False

        # Check premium status
        if "is_premium" in target:
            user_premium = context.get("is_premium", False)
            if user_premium != target["is_premium"]:
                return False

        # Check account age
        if "account_age_days" in target:
            account_age = context.get("account_age_days", 0)
            min_age, max_age = target["account_age_days"]
            if not (min_age <= account_age <= max_age):
                return False

        return True

    def _select_variant(self, user_id: str, experiment: Experiment) -> Optional[ExperimentVariant]:
        """Select a variant for a user based on traffic allocation type"""
        if experiment.traffic_allocation_type == TrafficAllocationType.UNIFORM:
            return self._select_uniform_variant(user_id, experiment.variants)
        elif experiment.traffic_allocation_type == TrafficAllocationType.WEIGHTED:
            return self._select_weighted_variant(user_id, experiment.variants)
        elif experiment.traffic_allocation_type == TrafficAllocationType.THOMPSON_SAMPLING:
            return self._select_thompson_sampling_variant(user_id, experiment)
        elif experiment.traffic_allocation_type == TrafficAllocationType.MULTI_ARMED_BANDIT:
            return self._select_multi_armed_bandit_variant(user_id, experiment)
        else:
            return self._select_uniform_variant(user_id, experiment.variants)

    def _select_uniform_variant(self, user_id: str, variants: List[ExperimentVariant]) -> ExperimentVariant:
        """Select variant using uniform random distribution"""
        import hashlib
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        index = hash_value % len(variants)
        return variants[index]

    def _select_weighted_variant(self, user_id: str, variants: List[ExperimentVariant]) -> ExperimentVariant:
        """Select variant using weighted traffic allocation"""
        import random
        weights = [variant.traffic_percentage for variant in variants]
        return random.choices(variants, weights=weights)[0]

    def _select_thompson_sampling_variant(self, user_id: str, experiment: Experiment) -> ExperimentVariant:
        """Select variant using Thompson sampling (requires existing results)"""
        if experiment.id not in self.experiment_results:
            return self._select_uniform_variant(user_id, experiment.variants)

        # Simplified Thompson sampling for binary conversion metrics
        best_variant = None
        best_sample = float('-inf')

        for variant in experiment.variants:
            # Get results for primary metric
            results = [r for r in self.experiment_results[experiment.id]
                      if r.variant_id == variant.id and r.metric_id == experiment.hypothesis.primary_metric]

            if results:
                result = results[0]
                # Beta distribution parameters (simplified)
                alpha = result.value * result.sample_size + 1
                beta = (1 - result.value) * result.sample_size + 1
                sample = np.random.beta(alpha, beta)
            else:
                sample = np.random.beta(1, 1)  # Uniform prior

            if sample > best_sample:
                best_sample = sample
                best_variant = variant

        return best_variant or self._select_uniform_variant(user_id, experiment.variants)

    def _select_multi_armed_bandit_variant(self, user_id: str, experiment: Experiment) -> ExperimentVariant:
        """Select variant using UCB (Upper Confidence Bound) algorithm"""
        if experiment.id not in self.experiment_results:
            return self._select_uniform_variant(user_id, experiment.variants)

        total_users = sum(len(set([r for r in self.experiment_results[experiment.id] if r.variant_id == variant.id])))
                         for variant in experiment.variants)

        best_variant = None
        best_ucb = float('-inf')

        for variant in experiment.variants:
            # Get results for primary metric
            results = [r for r in self.experiment_results[experiment.id]
                      if r.variant_id == variant.id and r.metric_id == experiment.hypothesis.primary_metric]

            if results and total_users > 0:
                result = results[0]
                variant_users = len([r for r in self.experiment_results[experiment.id] if r.variant_id == variant.id])

                # UCB formula
                if variant_users > 0:
                    exploitation = result.value
                    exploration = np.sqrt(2 * np.log(total_users) / variant_users)
                    ucb = exploitation + exploration
                else:
                    ucb = float('inf')  # Explore untested variants
            else:
                ucb = float('inf')

            if ucb > best_ucb:
                best_ucb = ucb
                best_variant = variant

        return best_variant or self._select_uniform_variant(user_id, experiment.variants)

    def record_metric(self, experiment_id: str, variant_id: str, metric_id: str, value: float, user_id: str = None):
        """Record a metric value for an experiment variant"""
        try:
            # Store in Redis stream
            metric_data = {
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "metric_id": metric_id,
                "value": value,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            if self.redis_client:
                self.redis_client.xadd(
                    "experiment_metrics",
                    metric_data,
                    maxlen=100000
                )

            # Call metric handlers
            for handler in self.metric_handlers:
                try:
                    handler(experiment_id, variant_id, metric_id, value, user_id)
                except Exception as e:
                    logger.error(f"Error in metric handler: {e}")

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")

    async def analyze_results(self, experiment_id: str) -> Dict[str, List[ExperimentResult]]:
        """Analyze experiment results and calculate statistical significance"""
        try:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            results = {}

            # Get metric data from Redis
            end_time = datetime.utcnow()
            if experiment.start_date:
                start_time = experiment.start_date
            else:
                start_time = end_time - timedelta(days=30)

            metric_data = self.redis_client.xrange(
                "experiment_metrics",
                min=int(start_time.timestamp() * 1000),
                max=int(end_time.timestamp() * 1000)
            )

            # Group data by variant and metric
            data_groups = {}
            for metric_id in [m.id for m in experiment.metrics]:
                data_groups[metric_id] = {}
                for variant in experiment.variants:
                    data_groups[metric_id][variant.id] = []

            for eval_id, data in metric_data:
                if data.get('experiment_id') == experiment_id:
                    metric_id = data['metric_id']
                    variant_id = data['variant_id']
                    value = float(data['value'])
                    if metric_id in data_groups and variant_id in data_groups[metric_id]:
                        data_groups[metric_id][variant_id].append(value)

            # Analyze each metric
            for metric in experiment.metrics:
                metric_results = []
                control_data = []
                control_variant = None

                # Find control variant
                for variant in experiment.variants:
                    if variant.is_control:
                        control_variant = variant
                        control_data = data_groups[metric.id][variant.id]
                        break

                # Calculate results for each variant
                for variant in experiment.variants:
                    variant_data = data_groups[metric.id][variant.id]

                    if len(variant_data) < experiment.minimum_sample_size:
                        continue

                    # Calculate statistics
                    mean_value = np.mean(variant_data)
                    sample_size = len(variant_data)
                    standard_error = np.std(variant_data) / np.sqrt(sample_size)

                    # Calculate confidence interval
                    confidence_level = 1 - metric.significance_level
                    if metric.statistical_test in [StatisticalTest.Z_TEST, StatisticalTest.T_TEST]:
                        t_value = stats.t.ppf((1 + confidence_level) / 2, sample_size - 1)
                        margin_error = t_value * standard_error
                    else:
                        margin_error = 1.96 * standard_error  # Normal approximation

                    confidence_interval = (
                        mean_value - margin_error,
                        mean_value + margin_error
                    )

                    # Calculate p-value and effect size
                    p_value = 1.0
                    effect_size = 0.0

                    if control_data and len(control_data) >= experiment.minimum_sample_size:
                        if metric.statistical_test == StatisticalTest.T_TEST:
                            t_stat, p_value = stats.ttest_ind(variant_data, control_data)
                            effect_size = (mean_value - np.mean(control_data)) / np.std(control_data)
                        elif metric.statistical_test == StatisticalTest.Z_TEST:
                            # Z-test for proportions or large samples
                            z_stat = (mean_value - np.mean(control_data)) / np.sqrt(
                                standard_error**2 + (np.std(control_data) / np.sqrt(len(control_data)))**2
                            )
                            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
                            effect_size = (mean_value - np.mean(control_data)) / np.mean(control_data)
                        elif metric.statistical_test == StatisticalTest.MANN_WHITNEY:
                            u_stat, p_value = stats.mannwhitneyu(variant_data, control_data, alternative='two-sided')
                            effect_size = (mean_value - np.mean(control_data)) / np.std(control_data)
                        elif metric.statistical_test == StatisticalTest.CHI_SQUARE:
                            # Chi-square test for categorical data
                            # Simplified implementation
                            p_value = 0.5  # Placeholder

                    is_significant = p_value < metric.significance_level

                    result = ExperimentResult(
                        variant_id=variant.id,
                        metric_id=metric.id,
                        value=mean_value,
                        sample_size=sample_size,
                        standard_error=standard_error,
                        confidence_interval=confidence_interval,
                        p_value=p_value,
                        is_statistically_significant=is_significant,
                        effect_size=effect_size
                    )

                    metric_results.append(result)

                results[metric.id] = metric_results

            # Store results
            self.experiment_results[experiment_id] = [r for metric_results in results.values() for r in metric_results]

            # Check for early stopping
            if experiment.auto_stop_enabled:
                await self._check_early_stopping(experiment, results)

            return results

        except Exception as e:
            logger.error(f"Error analyzing results for experiment {experiment_id}: {e}")
            return {}

    async def _check_early_stopping(self, experiment: Experiment, results: Dict[str, List[ExperimentResult]]):
        """Check if experiment should be stopped early"""
        try:
            primary_results = results.get(experiment.hypothesis.primary_metric, [])
            if not primary_results:
                return

            # Find control and best variant
            control_result = None
            best_result = None

            for result in primary_results:
                variant = next(v for v in experiment.variants if v.id == result.variant_id)
                if variant.is_control:
                    control_result = result
                elif best_result is None or result.effect_size > best_result.effect_size:
                    best_result = result

            if control_result and best_result:
                # Check if we have strong evidence
                if best_result.is_statistically_significant:
                    confidence = 1 - best_result.p_value
                    if confidence >= experiment.early_stopping_threshold:
                        # Stop experiment
                        await self.stop_experiment(experiment.id, "early_stopping", f"Strong evidence detected (confidence: {confidence:.3f})")

        except Exception as e:
            logger.error(f"Error checking early stopping: {e}")

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.utcnow()
        experiment.updated_at = datetime.utcnow()

        await self._save_experiment(experiment)
        logger.info(f"Started experiment: {experiment.name}")
        return True

    async def stop_experiment(self, experiment_id: str, reason: str = "manual", notes: str = "") -> bool:
        """Stop an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = ExperimentStatus.STOPPED_EARLY if reason == "early_stopping" else ExperimentStatus.COMPLETED
        experiment.end_date = datetime.utcnow()
        experiment.updated_at = datetime.utcnow()

        await self._save_experiment(experiment)
        logger.info(f"Stopped experiment {experiment.name} - Reason: {reason}")
        return True

    async def _save_experiment(self, experiment: Experiment):
        """Save experiment to Redis"""
        try:
            exp_dict = asdict(experiment)
            exp_dict['traffic_allocation_type'] = experiment.traffic_allocation_type.value
            exp_dict['status'] = experiment.status.value
            exp_dict['created_at'] = experiment.created_at.isoformat()
            exp_dict['updated_at'] = experiment.updated_at.isoformat()
            if experiment.start_date:
                exp_dict['start_date'] = experiment.start_date.isoformat()
            if experiment.end_date:
                exp_dict['end_date'] = experiment.end_date.isoformat()

            await self.async_redis_client.hset(
                "experiments",
                experiment.id,
                json.dumps(exp_dict)
            )

        except Exception as e:
            logger.error(f"Failed to save experiment {experiment.id}: {e}")
            raise

    async def _save_user_assignment(self, user_id: str, experiment_id: str, variant_id: str):
        """Save user assignment to Redis"""
        try:
            assignment_data = {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "timestamp": datetime.utcnow().isoformat()
            }

            await self.async_redis_client.hset(
                "user_assignments",
                user_id,
                json.dumps(self.user_assignments[user_id])
            )

            # Also store in stream for analysis
            await self.async_redis_client.xadd(
                "experiment_assignments",
                assignment_data,
                maxlen=50000
            )

        except Exception as e:
            logger.error(f"Failed to save user assignment: {e}")

    def _log_assignment(self, user_id: str, experiment_id: str, variant_id: str, context: Dict[str, Any]):
        """Log experiment assignment"""
        try:
            log_entry = {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }

            if self.redis_client:
                self.redis_client.xadd(
                    "experiment_assignments",
                    log_entry,
                    maxlen=50000
                )

        except Exception as e:
            logger.error(f"Failed to log assignment: {e}")

    async def _experiment_monitor_task(self):
        """Background task to monitor experiments"""
        while True:
            try:
                current_time = datetime.utcnow()

                for experiment in self.experiments.values():
                    if experiment.status == ExperimentStatus.RUNNING:
                        # Check if experiment should end
                        if experiment.end_date and current_time >= experiment.end_date:
                            await self.stop_experiment(experiment.id, "duration_completed")
                        elif experiment.start_date and experiment.duration_days:
                            duration = (current_time - experiment.start_date).days
                            if duration >= experiment.duration_days:
                                await self.stop_experiment(experiment.id, "duration_completed")

                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in experiment monitor task: {e}")
                await asyncio.sleep(60)

    async def _results_analysis_task(self):
        """Background task to analyze experiment results"""
        while True:
            try:
                for experiment in self.experiments.values():
                    if experiment.status == ExperimentStatus.RUNNING:
                        await self.analyze_results(experiment.id)

                await asyncio.sleep(3600)  # Analyze every hour
            except Exception as e:
                logger.error(f"Error in results analysis task: {e}")
                await asyncio.sleep(300)

    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get a summary of experiment results"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}

        results = self.experiment_results.get(experiment_id, [])
        if not results:
            return {
                "experiment": asdict(experiment),
                "status": "no_results",
                "message": "No results available yet"
            }

        # Group results by metric
        metric_results = {}
        for result in results:
            if result.metric_id not in metric_results:
                metric_results[result.metric_id] = []
            metric_results[result.metric_id].append(result)

        # Calculate summary statistics
        summary = {
            "experiment": asdict(experiment),
            "total_results": len(results),
            "metrics_summary": {}
        }

        for metric_id, metric_result_list in metric_results.items():
            metric = next(m for m in experiment.metrics if m.id == metric_id)

            variant_results = {}
            for result in metric_result_list:
                variant = next(v for v in experiment.variants if v.id == result.variant_id)
                variant_results[result.variant_id] = {
                    "variant_name": variant.name,
                    "is_control": variant.is_control,
                    "value": result.value,
                    "sample_size": result.sample_size,
                    "confidence_interval": result.confidence_interval,
                    "p_value": result.p_value,
                    "is_significant": result.is_statistically_significant,
                    "effect_size": result.effect_size
                }

            summary["metrics_summary"][metric_id] = {
                "metric_name": metric.name,
                "target_value": metric.target_value,
                "statistical_test": metric.statistical_test.value,
                "significance_level": metric.significance_level,
                "variants": variant_results
            }

        return summary

    def get_all_experiments(self) -> List[Dict[str, Any]]:
        """Get all experiments with their current status"""
        return [asdict(experiment) for experiment in self.experiments.values()]

    def get_running_experiments(self) -> List[Experiment]:
        """Get currently running experiments"""
        return [exp for exp in self.experiments.values() if exp.status == ExperimentStatus.RUNNING]

# Global experiment manager instance
experiment_manager = ABTestManager()