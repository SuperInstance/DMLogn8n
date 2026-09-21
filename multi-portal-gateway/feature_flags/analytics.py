#!/usr/bin/env python3
"""
DMLogn8n Analytics Service
Provides statistical analysis, significance testing, and reporting for feature flags and A/B tests
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import redis
import aioredis
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, mannwhitneyu, ttest_ind, fisher_exact
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score, precision_recall_curve
import yaml
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    PERFORMANCE = "performance"
    SATISFACTION = "satisfaction"
    CUSTOM = "custom"

class StatisticalTest(Enum):
    Z_TEST = "z_test"
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    WILCOXON = "wilcoxon"
    KRUSKAL_WALLIS = "kruskal_wallis"
    FISHER_EXACT = "fisher_exact"
    BAYESIAN_AB = "bayesian_ab"
    SEQUENTIAL_ANALYSIS = "sequential_analysis"

class EffectSizeMeasure(Enum):
    COHENS_D = "cohens_d"
    HEDGES_G = "hedges_g"
    GLASS_DELTA = "glass_delta"
    PHI_COEFFICIENT = "phi_coefficient"
    CRAMERS_V = "cramers_v"
    ODDS_RATIO = "odds_ratio"
    RISK_RATIO = "risk_ratio"
    CORRELATION = "correlation"

class ConfidenceLevel(Enum):
    NINETY = 0.90
    NINETY_FIVE = 0.95
    NINETY_NINE = 0.99

@dataclass
class MetricValue:
    metric_id: str
    variant_id: str
    user_id: str
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StatisticalResult:
    test_name: str
    statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    effect_size: float
    effect_size_measure: EffectSizeMeasure
    is_significant: bool
    confidence_level: ConfidenceLevel
    sample_size: int
    power: float = None
    interpretation: str = ""

@dataclass
class PowerAnalysis:
    sample_size: int
    effect_size: float
    alpha: float
    power: float
    test_type: StatisticalTest
    metric_type: MetricType

@dataclass
class AnomalyDetection:
    metric_id: str
    timestamp: datetime
    expected_value: float
    observed_value: float
    deviation_score: float
    is_anomaly: bool
    confidence: float

@dataclass
class TrendAnalysis:
    metric_id: str
    time_period: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float
    seasonal_pattern: bool
    forecast_values: List[float]
    confidence_intervals: List[Tuple[float, float]]

class AnalyticsRequest(BaseModel):
    experiment_id: str
    metric_ids: List[str]
    confidence_level: ConfidenceLevel = ConfidenceLevel.NINETY_FIVE
    include_effect_size: bool = True
    include_power_analysis: bool = True
    include_trend_analysis: bool = True

class AnalyticsResponse(BaseModel):
    experiment_id: str
    analysis_timestamp: datetime
    statistical_results: Dict[str, List[StatisticalResult]]
    power_analysis: Dict[str, PowerAnalysis]
    trend_analysis: Dict[str, TrendAnalysis]
    anomaly_detection: List[AnomalyDetection]
    summary: Dict[str, Any]

class StatisticalAnalyticsService:
    """Statistical analysis and significance testing service"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.metric_cache: Dict[str, List[MetricValue]] = {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour

        # Event handlers
        self.analysis_handlers: List[Callable] = []
        self.anomaly_handlers: List[Callable] = []

    async def initialize(self):
        """Initialize the analytics service"""
        try:
            # Initialize Redis clients
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)

            # Start background tasks
            asyncio.create_task(self._analytics_calculation_task())
            asyncio.create_task(self._anomaly_detection_task())
            asyncio.create_task(self._cache_cleanup_task())

            logger.info("Statistical analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize analytics service: {e}")
            raise

    async def analyze_experiment(self, request: AnalyticsRequest) -> AnalyticsResponse:
        """Perform comprehensive statistical analysis of an experiment"""
        try:
            # Load experiment data
            experiment_data = await self._load_experiment_data(request.experiment_id, request.metric_ids)

            if not experiment_data:
                return AnalyticsResponse(
                    experiment_id=request.experiment_id,
                    analysis_timestamp=datetime.utcnow(),
                    statistical_results={},
                    power_analysis={},
                    trend_analysis={},
                    anomaly_detection=[],
                    summary={"error": "No data available for analysis"}
                )

            # Perform statistical tests
            statistical_results = {}
            for metric_id in request.metric_ids:
                if metric_id in experiment_data:
                    results = await self._perform_statistical_tests(
                        experiment_data[metric_id],
                        request.confidence_level
                    )
                    statistical_results[metric_id] = results

            # Perform power analysis
            power_analysis = {}
            if request.include_power_analysis:
                for metric_id in request.metric_ids:
                    if metric_id in experiment_data:
                        power = await self._calculate_power_analysis(
                            experiment_data[metric_id],
                            request.confidence_level
                        )
                        power_analysis[metric_id] = power

            # Perform trend analysis
            trend_analysis = {}
            if request.include_trend_analysis:
                for metric_id in request.metric_ids:
                    if metric_id in experiment_data:
                        trend = await self._perform_trend_analysis(experiment_data[metric_id])
                        trend_analysis[metric_id] = trend

            # Detect anomalies
            anomaly_detection = await self._detect_anomalies(experiment_data)

            # Generate summary
            summary = await self._generate_analysis_summary(
                statistical_results,
                power_analysis,
                trend_analysis,
                anomaly_detection
            )

            response = AnalyticsResponse(
                experiment_id=request.experiment_id,
                analysis_timestamp=datetime.utcnow(),
                statistical_results=statistical_results,
                power_analysis=power_analysis,
                trend_analysis=trend_analysis,
                anomaly_detection=anomaly_detection,
                summary=summary
            )

            # Cache results
            self.analysis_cache[request.experiment_id] = asdict(response)

            # Call handlers
            for handler in self.analysis_handlers:
                try:
                    handler(response)
                except Exception as e:
                    logger.error(f"Error in analysis handler: {e}")

            return response

        except Exception as e:
            logger.error(f"Error analyzing experiment {request.experiment_id}: {e}")
            return AnalyticsResponse(
                experiment_id=request.experiment_id,
                analysis_timestamp=datetime.utcnow(),
                statistical_results={},
                power_analysis={},
                trend_analysis={},
                anomaly_detection=[],
                summary={"error": str(e)}
            )

    async def _load_experiment_data(self, experiment_id: str, metric_ids: List[str]) -> Dict[str, Dict[str, List[float]]]:
        """Load experiment data from Redis"""
        try:
            experiment_data = {}

            # Get data from experiment_metrics stream
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)

            metric_data = self.redis_client.xrange(
                "experiment_metrics",
                min=int(start_time.timestamp() * 1000),
                max=int(end_time.timestamp() * 1000)
            )

            # Group data by metric and variant
            for metric_id in metric_ids:
                experiment_data[metric_id] = {}

                for eval_id, data in metric_data:
                    if data.get('experiment_id') == experiment_id and data.get('metric_id') == metric_id:
                        variant_id = data['variant_id']
                        value = float(data['value'])

                        if variant_id not in experiment_data[metric_id]:
                            experiment_data[metric_id][variant_id] = []
                        experiment_data[metric_id][variant_id].append(value)

            return experiment_data

        except Exception as e:
            logger.error(f"Error loading experiment data: {e}")
            return {}

    async def _perform_statistical_tests(self, metric_data: Dict[str, List[float]], confidence_level: ConfidenceLevel) -> List[StatisticalResult]:
        """Perform various statistical tests on metric data"""
        results = []

        if len(metric_data) < 2:
            return results

        variant_ids = list(metric_data.keys())
        control_data = metric_data.get(variant_ids[0], [])
        treatment_data = metric_data.get(variant_ids[1] if len(variant_ids) > 1 else variant_ids[0], [])

        if not control_data or not treatment_data:
            return results

        # Determine metric type and appropriate tests
        metric_type = await self._determine_metric_type(control_data + treatment_data)

        # T-test
        if metric_type in [MetricType.REVENUE, MetricType.ENGAGEMENT, MetricType.PERFORMANCE]:
            t_stat, p_value = ttest_ind(control_data, treatment_data)
            effect_size = self._calculate_cohens_d(control_data, treatment_data)
            confidence_interval = self._calculate_confidence_interval(
                control_data, treatment_data, confidence_level
            )

            results.append(StatisticalResult(
                test_name="Two-Sample T-Test",
                statistic=t_stat,
                p_value=p_value,
                confidence_interval=confidence_interval,
                effect_size=effect_size,
                effect_size_measure=EffectSizeMeasure.COHENS_D,
                is_significant=p_value < (1 - confidence_level.value),
                confidence_level=confidence_level,
                sample_size=len(control_data) + len(treatment_data),
                power=self._calculate_test_power(effect_size, len(control_data) + len(treatment_data), confidence_level.value)
            ))

        # Mann-Whitney U test (non-parametric)
        u_stat, p_value = mannwhitneyu(control_data, treatment_data, alternative='two-sided')
        effect_size = self._calculate_rank_biserial_correlation(u_stat, len(control_data), len(treatment_data))

        results.append(StatisticalResult(
            test_name="Mann-Whitney U Test",
            statistic=u_stat,
            p_value=p_value,
            confidence_interval=(0, 0),  # Not easily calculated for non-parametric tests
            effect_size=effect_size,
            effect_size_measure=EffectSizeMeasure.CORRELATION,
            is_significant=p_value < (1 - confidence_level.value),
            confidence_level=confidence_level,
            sample_size=len(control_data) + len(treatment_data)
        ))

        # Chi-square test (for conversion/binary metrics)
        if metric_type == MetricType.CONVERSION:
            chi2_stat, p_value, dof, expected = chi2_contingency([
                [sum(1 for x in control_data if x > 0), sum(1 for x in control_data if x == 0)],
                [sum(1 for x in treatment_data if x > 0), sum(1 for x in treatment_data if x == 0)]
            ])

            effect_size = self._calculate_cramers_v(chi2_stat, len(control_data) + len(treatment_data))

            results.append(StatisticalResult(
                test_name="Chi-Square Test",
                statistic=chi2_stat,
                p_value=p_value,
                confidence_interval=(0, 0),
                effect_size=effect_size,
                effect_size_measure=EffectSizeMeasure.CRAMERS_V,
                is_significant=p_value < (1 - confidence_level.value),
                confidence_level=confidence_level,
                sample_size=len(control_data) + len(treatment_data)
            ))

        # Bayesian A/B test
        bayesian_result = self._perform_bayesian_ab_test(control_data, treatment_data, confidence_level)
        results.append(bayesian_result)

        return results

    async def _determine_metric_type(self, data: List[float]) -> MetricType:
        """Determine the type of metric based on data characteristics"""
        unique_values = set(data)

        if len(unique_values) <= 2:
            return MetricType.CONVERSION
        elif all(x >= 0 and x <= 1 for x in data):
            return MetricType.CONVERSION
        elif all(x >= 0 for x in data) and max(data) > 100:
            return MetricType.REVENUE
        elif max(data) - min(data) > 10 * np.std(data):
            return MetricType.REVENUE
        else:
            return MetricType.ENGAGEMENT

    def _calculate_cohens_d(self, control: List[float], treatment: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        n1, n2 = len(control), len(treatment)
        mean1, mean2 = np.mean(control), np.mean(treatment)
        var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)

        # Pooled standard deviation
        pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_sd == 0:
            return 0

        return (mean2 - mean1) / pooled_sd

    def _calculate_rank_biserial_correlation(self, u_stat: float, n1: int, n2: int) -> float:
        """Calculate rank-biserial correlation from Mann-Whitney U statistic"""
        return 1 - (2 * u_stat) / (n1 * n2)

    def _calculate_cramers_v(self, chi2_stat: float, n: int) -> float:
        """Calculate Cramér's V effect size for chi-square test"""
        min_dim = min(2, 2)  # For 2x2 contingency table
        return np.sqrt(chi2_stat / (n * (min_dim - 1)))

    def _calculate_confidence_interval(self, control: List[float], treatment: List[float], confidence_level: ConfidenceLevel) -> Tuple[float, float]:
        """Calculate confidence interval for the difference in means"""
        n1, n2 = len(control), len(treatment)
        mean1, mean2 = np.mean(control), np.mean(treatment)
        var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)

        # Standard error of the difference
        se = np.sqrt(var1/n1 + var2/n2)

        # Critical value
        alpha = 1 - confidence_level.value
        df = n1 + n2 - 2
        t_critical = stats.t.ppf(1 - alpha/2, df)

        # Confidence interval
        diff = mean2 - mean1
        margin_error = t_critical * se

        return (diff - margin_error, diff + margin_error)

    def _calculate_test_power(self, effect_size: float, sample_size: int, alpha: float) -> float:
        """Calculate statistical power of the test"""
        try:
            from statsmodels.stats.power import TTestIndPower

            power_analysis = TTestIndPower()
            power = power_analysis.power(
                effect_size=effect_size,
                nobs1=sample_size // 2,
                alpha=alpha,
                alternative='two-sided'
            )

            return min(power, 1.0)  # Cap at 1.0

        except ImportError:
            # Fallback calculation
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = effect_size * np.sqrt(sample_size / 4) - z_alpha
            power = stats.norm.cdf(z_beta)
            return min(max(power, 0.0), 1.0)

    def _perform_bayesian_ab_test(self, control: List[float], treatment: List[float], confidence_level: ConfidenceLevel) -> StatisticalResult:
        """Perform Bayesian A/B test analysis"""
        try:
            # Convert to binary if conversion-like data
            control_conversions = sum(1 for x in control if x > 0)
            treatment_conversions = sum(1 for x in treatment if x > 0)
            control_trials = len(control)
            treatment_trials = len(treatment)

            # Beta posterior parameters
            alpha_control = 1 + control_conversions
            beta_control = 1 + control_trials - control_conversions
            alpha_treatment = 1 + treatment_conversions
            beta_treatment = 1 + treatment_trials - treatment_conversions

            # Sample from posterior distributions
            np.random.seed(42)  # For reproducibility
            control_samples = np.random.beta(alpha_control, beta_control, 10000)
            treatment_samples = np.random.beta(alpha_treatment, beta_treatment, 10000)

            # Calculate probability that treatment is better
            prob_treatment_better = np.mean(treatment_samples > control_samples)

            # Calculate credible interval for the difference
            difference = treatment_samples - control_samples
            ci_lower = np.percentile(difference, (1 - confidence_level.value) * 50)
            ci_upper = np.percentile(difference, 100 - (1 - confidence_level.value) * 50)

            # Calculate effect size (risk ratio)
            treatment_rate = treatment_conversions / treatment_trials if treatment_trials > 0 else 0
            control_rate = control_conversions / control_trials if control_trials > 0 else 0
            risk_ratio = treatment_rate / control_rate if control_rate > 0 else 1

            return StatisticalResult(
                test_name="Bayesian A/B Test",
                statistic=prob_treatment_better,
                p_value=1 - prob_treatment_better,  # Convert to frequentist-style p-value
                confidence_interval=(ci_lower, ci_upper),
                effect_size=risk_ratio,
                effect_size_measure=EffectSizeMeasure.RISK_RATIO,
                is_significant=prob_treatment_better > confidence_level.value,
                confidence_level=confidence_level,
                sample_size=control_trials + treatment_trials,
                interpretation=f"Probability treatment is better: {prob_treatment_better:.3f}"
            )

        except Exception as e:
            logger.error(f"Error in Bayesian A/B test: {e}")
            # Return fallback result
            return StatisticalResult(
                test_name="Bayesian A/B Test",
                statistic=0.5,
                p_value=0.5,
                confidence_interval=(0, 0),
                effect_size=0,
                effect_size_measure=EffectSizeMeasure.RISK_RATIO,
                is_significant=False,
                confidence_level=confidence_level,
                sample_size=len(control) + len(treatment),
                interpretation="Error in Bayesian calculation"
            )

    async def _calculate_power_analysis(self, metric_data: Dict[str, List[float]], confidence_level: ConfidenceLevel) -> PowerAnalysis:
        """Calculate power analysis for the metric"""
        try:
            if len(metric_data) < 2:
                return None

            variant_ids = list(metric_data.keys())
            control_data = metric_data[variant_ids[0]]
            treatment_data = metric_data[variant_ids[1]]

            # Calculate observed effect size
            effect_size = self._calculate_cohens_d(control_data, treatment_data)
            total_sample_size = len(control_data) + len(treatment_data)
            alpha = 1 - confidence_level.value

            # Calculate achieved power
            power = self._calculate_test_power(effect_size, total_sample_size, alpha)

            return PowerAnalysis(
                sample_size=total_sample_size,
                effect_size=effect_size,
                alpha=alpha,
                power=power,
                test_type=StatisticalTest.T_TEST,
                metric_type=await self._determine_metric_type(control_data + treatment_data)
            )

        except Exception as e:
            logger.error(f"Error calculating power analysis: {e}")
            return None

    async def _perform_trend_analysis(self, metric_data: Dict[str, List[float]]) -> TrendAnalysis:
        """Perform trend analysis on time-series data"""
        try:
            # This would require time-series data
            # For now, return a basic analysis
            all_values = []
            for values in metric_data.values():
                all_values.extend(values)

            if len(all_values) < 10:
                return TrendAnalysis(
                    metric_id="unknown",
                    time_period="last_30_days",
                    trend_direction="stable",
                    trend_strength=0.0,
                    seasonal_pattern=False,
                    forecast_values=[],
                    confidence_intervals=[]
                )

            # Simple linear trend
            x = np.arange(len(all_values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, all_values)

            trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            trend_strength = abs(r_value)

            # Simple forecast (linear extrapolation)
            forecast_values = []
            for i in range(1, 6):  # 5-step forecast
                forecast_values.append(intercept + slope * (len(all_values) + i))

            return TrendAnalysis(
                metric_id="unknown",
                time_period="last_30_days",
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                seasonal_pattern=False,
                forecast_values=forecast_values,
                confidence_intervals=[(v - std_err, v + std_err) for v in forecast_values]
            )

        except Exception as e:
            logger.error(f"Error performing trend analysis: {e}")
            return TrendAnalysis(
                metric_id="unknown",
                time_period="unknown",
                trend_direction="stable",
                trend_strength=0.0,
                seasonal_pattern=False,
                forecast_values=[],
                confidence_intervals=[]
            )

    async def _detect_anomalies(self, experiment_data: Dict[str, Dict[str, List[float]]]) -> List[AnomalyDetection]:
        """Detect anomalies in experiment data"""
        anomalies = []

        try:
            for metric_id, variant_data in experiment_data.items():
                for variant_id, values in variant_data.items():
                    if len(values) < 10:
                        continue

                    # Calculate rolling statistics
                    window_size = min(10, len(values) // 2)
                    if window_size < 3:
                        continue

                    # Simple anomaly detection using z-score
                    mean = np.mean(values)
                    std = np.std(values)

                    for i, value in enumerate(values):
                        if std > 0:
                            z_score = abs(value - mean) / std
                            if z_score > 3:  # 3-sigma rule
                                anomalies.append(AnomalyDetection(
                                    metric_id=metric_id,
                                    timestamp=datetime.utcnow(),  # Would use actual timestamp
                                    expected_value=mean,
                                    observed_value=value,
                                    deviation_score=z_score,
                                    is_anomaly=True,
                                    confidence=min(z_score / 3, 1.0)
                                ))

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")

        return anomalies

    async def _generate_analysis_summary(self, statistical_results: Dict[str, List[StatisticalResult]],
                                       power_analysis: Dict[str, PowerAnalysis],
                                       trend_analysis: Dict[str, TrendAnalysis],
                                       anomaly_detection: List[AnomalyDetection]) -> Dict[str, Any]:
        """Generate a summary of the analysis results"""
        summary = {
            "total_metrics_analyzed": len(statistical_results),
            "significant_results": 0,
            "average_power": 0,
            "trend_directions": {},
            "anomalies_detected": len(anomaly_detection),
            "recommendations": []
        }

        # Count significant results
        for metric_id, results in statistical_results.items():
            significant_count = sum(1 for r in results if r.is_significant)
            if significant_count > 0:
                summary["significant_results"] += 1

        # Calculate average power
        if power_analysis:
            powers = [p.power for p in power_analysis.values() if p.power is not None]
            summary["average_power"] = sum(powers) / len(powers) if powers else 0

        # Count trend directions
        for metric_id, trend in trend_analysis.items():
            direction = trend.trend_direction
            summary["trend_directions"][direction] = summary["trend_directions"].get(direction, 0) + 1

        # Generate recommendations
        if summary["significant_results"] > 0:
            summary["recommendations"].append("Statistically significant results detected. Consider implementing winning variants.")

        if summary["average_power"] < 0.8:
            summary["recommendations"].append("Low statistical power detected. Consider increasing sample size.")

        if summary["anomalies_detected"] > 0:
            summary["recommendations"].append("Anomalies detected in data. Review for potential data quality issues.")

        return summary

    async def _analytics_calculation_task(self):
        """Background task to perform analytics calculations"""
        while True:
            try:
                # Perform analytics for active experiments
                # This would integrate with the experiment manager
                await asyncio.sleep(3600)  # Calculate every hour
            except Exception as e:
                logger.error(f"Error in analytics calculation task: {e}")
                await asyncio.sleep(300)

    async def _anomaly_detection_task(self):
        """Background task for continuous anomaly detection"""
        while True:
            try:
                # Perform continuous anomaly detection
                # This would monitor real-time data streams
                await asyncio.sleep(600)  # Check every 10 minutes
            except Exception as e:
                logger.error(f"Error in anomaly detection task: {e}")
                await asyncio.sleep(300)

    async def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                # Clean up expired cache entries
                self.analysis_cache.clear()
                self.metric_cache.clear()
                await asyncio.sleep(3600)  # Clean every hour
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(300)

    def add_analysis_handler(self, handler: Callable):
        """Add handler for analysis results"""
        self.analysis_handlers.append(handler)

    def add_anomaly_handler(self, handler: Callable):
        """Add handler for anomaly detection"""
        self.anomaly_handlers.append(handler)

    async def get_metric_summary(self, metric_id: str, days: int = 30) -> Dict[str, Any]:
        """Get summary statistics for a specific metric"""
        try:
            # Get metric data from Redis
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)

            metric_data = self.redis_client.xrange(
                "experiment_metrics",
                min=int(start_time.timestamp() * 1000),
                max=int(end_time.timestamp() * 1000)
            )

            # Filter by metric_id
            values = []
            timestamps = []

            for eval_id, data in metric_data:
                if data.get('metric_id') == metric_id:
                    values.append(float(data['value']))
                    timestamps.append(int(eval_id.split('-')[0]))

            if not values:
                return {"error": "No data available"}

            # Calculate summary statistics
            summary = {
                "metric_id": metric_id,
                "period_days": days,
                "total_observations": len(values),
                "mean": np.mean(values),
                "median": np.median(values),
                "std_dev": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "q25": np.percentile(values, 25),
                "q75": np.percentile(values, 75),
                "trend": "stable",  # Would calculate actual trend
                "anomalies": 0  # Would detect actual anomalies
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting metric summary: {e}")
            return {"error": str(e)}

    async def calculate_sample_size(self, effect_size: float, power: float = 0.8, alpha: float = 0.05) -> int:
        """Calculate required sample size for A/B test"""
        try:
            from statsmodels.stats.power import TTestIndPower

            power_analysis = TTestIndPower()
            sample_size = power_analysis.solve_power(
                effect_size=effect_size,
                power=power,
                alpha=alpha,
                alternative='two-sided'
            )

            return int(np.ceil(sample_size * 2))  # Total sample size for both groups

        except ImportError:
            # Fallback calculation using simplified formula
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(power)
            n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            return int(np.ceil(n_per_group * 2))

    def get_statistical_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Get statistical recommendations based on analysis results"""
        recommendations = []

        try:
            if 'statistical_results' in analysis_results:
                for metric_id, results in analysis_results['statistical_results'].items():
                    significant_results = [r for r in results if r.is_significant]

                    if significant_results:
                        best_result = max(significant_results, key=lambda x: abs(x.effect_size))
                        recommendations.append(
                            f"Metric {metric_id}: Significant effect detected "
                            f"({best_result.test_name}, effect_size: {best_result.effect_size:.3f})"
                        )
                    else:
                        recommendations.append(
                            f"Metric {metric_id}: No significant effects detected"
                        )

            if 'power_analysis' in analysis_results:
                power_values = [p.power for p in analysis_results['power_analysis'].values() if p.power]
                if power_values:
                    avg_power = sum(power_values) / len(power_values)
                    if avg_power < 0.8:
                        recommendations.append(
                            f"Low statistical power detected (avg: {avg_power:.2f}). "
                            "Consider increasing sample size or effect size."
                        )

            if 'anomaly_detection' in analysis_results:
                anomalies = analysis_results['anomaly_detection']
                if anomalies:
                    recommendations.append(f"{len(anomalies)} anomalies detected. Review data quality.")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations")

        return recommendations

# Global analytics service instance
analytics_service = StatisticalAnalyticsService()