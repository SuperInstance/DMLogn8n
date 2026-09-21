"""
DMLogn8n Growth System - Growth Analytics and Performance Tracking
Comprehensive analytics system for measuring and optimizing growth
"""

import asyncio
import json
import logging
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import uuid
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GrowthMetric:
    """Represents a growth metric"""
    id: str
    name: str
    category: str  # acquisition, activation, retention, revenue, referral
    metric_type: str  # absolute, percentage, rate, ratio
    value: float
    previous_value: float
    change_percentage: float
    target_value: float
    achievement_rate: float
    date_range: Dict[str, datetime]
    data_source: str
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.data_range is None:
            self.data_range = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FunnelAnalysis:
    """Represents conversion funnel analysis"""
    id: str
    funnel_name: str
    steps: List[Dict[str, Any]]
    conversion_rates: Dict[str, float]
    drop_off_rates: Dict[str, float]
    bottlenecks: List[Dict[str, Any]]
    optimization_suggestions: List[Dict[str, Any]]
    date_range: Dict[str, datetime]
    total_users: int
    final_conversions: int
    overall_conversion_rate: float

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.conversion_rates is None:
            self.conversion_rates = {}
        if self.drop_off_rates is None:
            self.drop_off_rates = {}
        if self.bottlenecks is None:
            self.bottlenecks = []
        if self.optimization_suggestions is None:
            self.optimization_suggestions = []
        if self.date_range is None:
            self.date_range = {}

@dataclass
class CohortAnalysis:
    """Represents cohort analysis for retention"""
    id: str
    cohort_type: str  # monthly, weekly, daily
    cohort_date: datetime
    cohort_size: int
    retention_rates: Dict[int, float]  # period -> retention_rate
    ltv_projection: float
    churn_prediction: Dict[str, float]
    segment_performance: Dict[str, Any]

    def __post_init__(self):
        if self.retention_rates is None:
            self.retention_rates = {}
        if self.churn_prediction is None:
            self.churn_prediction = {}
        if self.segment_performance is None:
            self.segment_performance = {}

@dataclass
class AttributionModel:
    """Represents marketing attribution model"""
    id: str
    model_type: str  # first_touch, last_touch, linear, time_decay, position_based
    channels: Dict[str, Any]
    attribution_weights: Dict[str, float]
    conversion_paths: List[Dict[str, Any]]
    touchpoint_analysis: Dict[str, Any]
    date_range: Dict[str, datetime]

    def __post_init__(self):
        if self.channels is None:
            self.channels = {}
        if self.attribution_weights is None:
            self.attribution_weights = {}
        if self.conversion_paths is None:
            self.conversion_paths = []
        if self.touchpoint_analysis is None:
            self.touchpoint_analysis = {}
        if self.date_range is None:
            self.date_range = {}

class GrowthMetricsCalculator:
    """Calculate and analyze growth metrics"""

    def __init__(self):
        self.metric_definitions = self._initialize_metric_definitions()
        self.benchmarks = self._initialize_benchmarks()

    def _initialize_metric_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard growth metric definitions"""
        return {
            # Acquisition Metrics
            "new_users": {
                "category": "acquisition",
                "type": "absolute",
                "description": "Number of new users acquired",
                "calculation": "COUNT(DISTINCT user_id) WHERE first_seen IN period",
                "frequency": "daily",
                "target_direction": "increase"
            },
            "customer_acquisition_cost": {
                "category": "acquisition",
                "type": "absolute",
                "description": "Cost to acquire one new customer",
                "calculation": "total_marketing_spend / new_customers",
                "frequency": "monthly",
                "target_direction": "decrease"
            },
            "conversion_rate": {
                "category": "acquisition",
                "type": "percentage",
                "description": "Percentage of visitors who convert",
                "calculation": "conversions / visitors * 100",
                "frequency": "daily",
                "target_direction": "increase"
            },
            "traffic_sources": {
                "category": "acquisition",
                "type": "distribution",
                "description": "Distribution of traffic by source",
                "calculation": "GROUP BY source, COUNT(*)",
                "frequency": "daily",
                "target_direction": "balanced"
            },

            # Activation Metrics
            "activation_rate": {
                "category": "activation",
                "type": "percentage",
                "description": "Percentage of new users who activate",
                "calculation": "activated_users / new_users * 100",
                "frequency": "weekly",
                "target_direction": "increase"
            },
            "time_to_activate": {
                "category": "activation",
                "type": "absolute",
                "description": "Average time for user to activate",
                "calculation": "AVG(activation_date - signup_date)",
                "frequency": "weekly",
                "target_direction": "decrease"
            },
            "feature_adoption": {
                "category": "activation",
                "type": "percentage",
                "description": "Percentage of users using key features",
                "calculation": "users_using_feature / total_users * 100",
                "frequency": "monthly",
                "target_direction": "increase"
            },

            # Retention Metrics
            "retention_rate": {
                "category": "retention",
                "type": "percentage",
                "description": "Percentage of users retained over period",
                "calculation": "retained_users / cohort_size * 100",
                "frequency": "monthly",
                "target_direction": "increase"
            },
            "churn_rate": {
                "category": "retention",
                "type": "percentage",
                "description": "Percentage of users who churn",
                "calculation": "churned_users / total_users * 100",
                "frequency": "monthly",
                "target_direction": "decrease"
            },
            "daily_active_users": {
                "category": "retention",
                "type": "absolute",
                "description": "Number of active users per day",
                "calculation": "COUNT(DISTINCT user_id) WHERE activity_date = date",
                "frequency": "daily",
                "target_direction": "increase"
            },
            "stickiness": {
                "category": "retention",
                "type": "ratio",
                "description": "DAU/MAU ratio",
                "calculation": "daily_active_users / monthly_active_users",
                "frequency": "monthly",
                "target_direction": "increase"
            },

            # Revenue Metrics
            "monthly_recurring_revenue": {
                "category": "revenue",
                "type": "absolute",
                "description": "Monthly recurring revenue",
                "calculation": "SUM(active_subscriptions * monthly_price)",
                "frequency": "monthly",
                "target_direction": "increase"
            },
            "average_revenue_per_user": {
                "category": "revenue",
                "type": "absolute",
                "description": "Average revenue per user",
                "calculation": "total_revenue / total_users",
                "frequency": "monthly",
                "target_direction": "increase"
            },
            "ltv_cac_ratio": {
                "category": "revenue",
                "type": "ratio",
                "description": "Lifetime value to customer acquisition cost ratio",
                "calculation": "customer_ltv / customer_acquisition_cost",
                "frequency": "quarterly",
                "target_direction": "increase"
            },

            # Referral Metrics
            "viral_coefficient": {
                "category": "referral",
                "type": "absolute",
                "description": "Number of new users each existing user generates",
                "calculation": "referrals * conversion_rate / existing_users",
                "frequency": "monthly",
                "target_direction": "increase"
            },
            "referral_conversion_rate": {
                "category": "referral",
                "type": "percentage",
                "description": "Conversion rate of referred users",
                "calculation": "referred_conversions / total_referrals * 100",
                "frequency": "monthly",
                "target_direction": "increase"
            }
        }

    def _initialize_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Initialize industry benchmarks"""
        return {
            "saas_startup": {
                "monthly_growth_rate": 0.15,  # 15% monthly growth
                "retention_rate": 0.85,  # 85% monthly retention
                "ltv_cac_ratio": 3.0,  # 3:1 LTV:CAC ratio
                "churn_rate": 0.05,  # 5% monthly churn
                "conversion_rate": 0.03,  # 3% conversion rate
                "viral_coefficient": 0.3  # Viral coefficient
            },
            "consumer_product": {
                "monthly_growth_rate": 0.25,  # 25% monthly growth
                "retention_rate": 0.70,  # 70% monthly retention
                "ltv_cac_ratio": 2.5,  # 2.5:1 LTV:CAC ratio
                "churn_rate": 0.08,  # 8% monthly churn
                "conversion_rate": 0.05,  # 5% conversion rate
                "viral_coefficient": 0.5  # Higher viral coefficient
            }
        }

    def calculate_metric(self, metric_name: str, current_data: Dict[str, Any],
                        previous_data: Dict[str, Any] = None,
                        target_data: Dict[str, Any] = None) -> GrowthMetric:
        """Calculate specific growth metric"""
        if metric_name not in self.metric_definitions:
            raise ValueError(f"Unknown metric: {metric_name}")

        definition = self.metric_definitions[metric_name]

        # Simulate metric calculation based on definition
        if definition["type"] == "absolute":
            if metric_name == "new_users":
                value = random.randint(500, 5000)
                previous_value = random.randint(400, 4500)
            elif metric_name == "customer_acquisition_cost":
                value = random.uniform(15.0, 50.0)
                previous_value = random.uniform(18.0, 55.0)
            elif metric_name == "monthly_recurring_revenue":
                value = random.uniform(25000, 150000)
                previous_value = random.uniform(20000, 140000)
            else:
                value = random.uniform(100, 10000)
                previous_value = random.uniform(90, 9500)

        elif definition["type"] == "percentage":
            if metric_name == "conversion_rate":
                value = random.uniform(2.0, 8.0)
                previous_value = random.uniform(1.8, 7.5)
            elif metric_name == "retention_rate":
                value = random.uniform(70.0, 95.0)
                previous_value = random.uniform(68.0, 93.0)
            else:
                value = random.uniform(10.0, 90.0)
                previous_value = random.uniform(8.0, 85.0)

        elif definition["type"] == "ratio":
            if metric_name == "ltv_cac_ratio":
                value = random.uniform(2.0, 5.0)
                previous_value = random.uniform(1.8, 4.5)
            else:
                value = random.uniform(0.1, 1.0)
                previous_value = random.uniform(0.08, 0.95)

        else:  # distribution or other types
            value = random.uniform(100, 1000)
            previous_value = random.uniform(90, 950)

        # Calculate change percentage
        if previous_value and previous_value > 0:
            change_percentage = ((value - previous_value) / previous_value) * 100
        else:
            change_percentage = 0

        # Calculate achievement rate (vs target)
        target_value = target_data.get(metric_name, value * 1.2) if target_data else value * 1.2
        if target_value > 0:
            achievement_rate = (value / target_value) * 100
        else:
            achievement_rate = 100

        metric = GrowthMetric(
            id=str(uuid.uuid4()),
            name=metric_name,
            category=definition["category"],
            metric_type=definition["type"],
            value=value,
            previous_value=previous_value or 0,
            change_percentage=change_percentage,
            target_value=target_value,
            achievement_rate=achievement_rate,
            date_range={
                "start": datetime.utcnow() - timedelta(days=30),
                "end": datetime.utcnow()
            },
            data_source="simulated",
            metadata={
                "description": definition["description"],
                "calculation": definition["calculation"],
                "frequency": definition["frequency"]
            }
        )

        return metric

    def calculate_growth_score(self, metrics: List[GrowthMetric]) -> Dict[str, Any]:
        """Calculate overall growth score from metrics"""
        # Weight different categories
        category_weights = {
            "acquisition": 0.25,
            "activation": 0.20,
            "retention": 0.30,
            "revenue": 0.15,
            "referral": 0.10
        }

        category_scores = {}
        weighted_scores = []

        for category, weight in category_weights.items():
            category_metrics = [m for m in metrics if m.category == category]
            if category_metrics:
                # Average achievement rate for category
                category_score = sum(m.achievement_rate for m in category_metrics) / len(category_metrics)
                category_scores[category] = category_score
                weighted_scores.append(category_score * weight)

        # Calculate overall score
        overall_score = sum(weighted_scores) if weighted_scores else 0

        # Determine performance rating
        if overall_score >= 90:
            rating = "Excellent"
        elif overall_score >= 75:
            rating = "Good"
        elif overall_score >= 60:
            rating = "Average"
        elif overall_score >= 40:
            rating = "Below Average"
        else:
            rating = "Poor"

        return {
            "overall_score": overall_score,
            "rating": rating,
            "category_scores": category_scores,
            "weights": category_weights,
            "metrics_analyzed": len(metrics),
            "recommendations": self._generate_growth_recommendations(category_scores)
        }

    def _generate_growth_recommendations(self, category_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on category scores"""
        recommendations = []

        for category, score in category_scores.items():
            if score < 70:  # Below target
                if category == "acquisition":
                    recommendations.append("Focus on optimizing conversion rates and reducing acquisition costs")
                elif category == "activation":
                    recommendations.append("Improve onboarding flow and feature adoption")
                elif category == "retention":
                    recommendations.append("Implement retention campaigns and reduce churn")
                elif category == "revenue":
                    recommendations.append("Optimize pricing and increase user lifetime value")
                elif category == "referral":
                    recommendations.append("Enhance referral programs and viral mechanics")

        if not recommendations:
            recommendations.append("Maintain current performance and focus on incremental improvements")

        return recommendations

class FunnelAnalyzer:
    """Analyze conversion funnels and identify optimization opportunities"""

    def __init__(self):
        self.funnel_templates = self._initialize_funnel_templates()

    def _initialize_funnel_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard funnel templates"""
        return {
            "user_acquisition": {
                "steps": [
                    {"name": "website_visit", "description": "User visits website"},
                    {"name": "landing_page_view", "description": "User views landing page"},
                    {"name": "signup_click", "description": "User clicks signup"},
                    {"name": "signup_complete", "description": "User completes signup"},
                    {"name": "email_verify", "description": "User verifies email"},
                    {"name": "profile_complete", "description": "User completes profile"}
                ]
            },
            "trial_conversion": {
                "steps": [
                    {"name": "trial_start", "description": "User starts trial"},
                    {"name": "feature_explore", "description": "User explores features"},
                    {"name": "workflow_create", "description": "User creates first workflow"},
                    {"name": "value_realization", "description": "User realizes value"},
                    {"name": "upgrade_intent", "description": "User shows upgrade intent"},
                    {"name": "purchase_complete", "description": "User completes purchase"}
                ]
            },
            "feature_adoption": {
                "steps": [
                    {"name": "feature_discover", "description": "User discovers feature"},
                    {"name": "feature_learn", "description": "User learns about feature"},
                    {"name": "feature_try", "description": "User tries feature"},
                    {"name": "feature_use", "description": "User uses feature regularly"},
                    {"name": "feature_mastery", "description": "User masters feature"}
                ]
            }
        }

    def analyze_funnel(self, funnel_type: str, data: Dict[str, Any],
                       date_range: Dict[str, datetime]) -> FunnelAnalysis:
        """Analyze conversion funnel performance"""
        if funnel_type not in self.funnel_templates:
            raise ValueError(f"Unknown funnel type: {funnel_type}")

        template = self.funnel_templates[funnel_type]
        steps = template["steps"].copy()

        # Simulate user counts for each step
        total_users = random.randint(10000, 50000)
        current_users = total_users

        conversion_rates = {}
        drop_off_rates = {}
        bottlenecks = []
        optimization_suggestions = []

        for i, step in enumerate(steps):
            # Generate conversion rate for this step
            if i == 0:
                # First step has no previous step
                conversion_rate = 1.0
                step_users = total_users
            else:
                # Later steps have conversion rates
                conversion_rate = random.uniform(0.6, 0.95)
                step_users = int(current_users * conversion_rate)

            # Calculate drop-off rate
            drop_off_rate = 1 - conversion_rate
            drop_off_rates[step["name"]] = drop_off_rate

            # Update step data
            step["users"] = step_users
            step["conversion_rate"] = conversion_rate
            step["drop_off_rate"] = drop_off_rate

            conversion_rates[step["name"]] = conversion_rate

            # Identify bottlenecks (high drop-off rates)
            if drop_off_rate > 0.4:  # More than 40% drop-off
                bottlenecks.append({
                    "step": step["name"],
                    "drop_off_rate": drop_off_rate,
                    "users_lost": current_users - step_users,
                    "severity": "high" if drop_off_rate > 0.6 else "medium"
                })

                # Generate optimization suggestions
                if step["name"] == "signup_complete":
                    optimization_suggestions.append({
                        "step": step["name"],
                        "suggestion": "Simplify signup form and reduce required fields",
                        "expected_improvement": "15-25% increase in completion rate"
                    })
                elif step["name"] == "workflow_create":
                    optimization_suggestions.append({
                        "step": step["name"],
                        "suggestion": "Provide interactive tutorials and templates",
                        "expected_improvement": "20-30% increase in adoption"
                    })
                else:
                    optimization_suggestions.append({
                        "step": step["name"],
                        "suggestion": "Improve user guidance and reduce friction",
                        "expected_improvement": "10-20% improvement"
                    })

            current_users = step_users

        # Calculate final conversion rate
        final_conversions = current_users
        overall_conversion_rate = final_conversions / total_users if total_users > 0 else 0

        funnel_analysis = FunnelAnalysis(
            id=str(uuid.uuid4()),
            funnel_name=funnel_type,
            steps=steps,
            conversion_rates=conversion_rates,
            drop_off_rates=drop_off_rates,
            bottlenecks=bottlenecks,
            optimization_suggestions=optimization_suggestions,
            date_range=date_range,
            total_users=total_users,
            final_conversions=final_conversions,
            overall_conversion_rate=overall_conversion_rate
        )

        return funnel_analysis

    def compare_funnels(self, baseline_funnel: FunnelAnalysis,
                       comparison_funnel: FunnelAnalysis) -> Dict[str, Any]:
        """Compare two funnel analyses"""
        comparison = {
            "overall_comparison": {
                "baseline_conversion": baseline_funnel.overall_conversion_rate,
                "comparison_conversion": comparison_funnel.overall_conversion_rate,
                "improvement": ((comparison_funnel.overall_conversion_rate - baseline_funnel.overall_conversion_rate) / baseline_funnel.overall_conversion_rate * 100) if baseline_funnel.overall_conversion_rate > 0 else 0
            },
            "step_comparison": [],
            "bottleneck_analysis": {},
            "recommendations": []
        }

        # Compare each step
        for baseline_step in baseline_funnel.steps:
            step_name = baseline_step["name"]

            # Find corresponding step in comparison
            comparison_step = next((s for s in comparison_funnel.steps if s["name"] == step_name), None)

            if comparison_step:
                step_comparison = {
                    "step": step_name,
                    "baseline_rate": baseline_step["conversion_rate"],
                    "comparison_rate": comparison_step["conversion_rate"],
                    "improvement": ((comparison_step["conversion_rate"] - baseline_step["conversion_rate"]) / baseline_step["conversion_rate"] * 100) if baseline_step["conversion_rate"] > 0 else 0,
                    "impact": "high" if abs(comparison_step["conversion_rate"] - baseline_step["conversion_rate"]) > 0.1 else "medium"
                }
                comparison["step_comparison"].append(step_comparison)

        # Analyze bottlenecks
        comparison["bottleneck_analysis"] = {
            "baseline_bottlenecks": len(baseline_funnel.bottlenecks),
            "comparison_bottlenecks": len(comparison_funnel.bottlenecks),
            "improvement": len(baseline_funnel.bottlenecks) - len(comparison_funnel.bottlenecks)
        }

        # Generate recommendations
        if comparison["overall_comparison"]["improvement"] > 10:
            comparison["recommendations"].append("Changes show significant positive impact - scale up successful interventions")
        elif comparison["overall_comparison"]["improvement"] < -5:
            comparison["recommendations"].append("Performance declined - review changes and consider rollback")
        else:
            comparison["recommendations"].append("Minimal impact - consider alternative optimization strategies")

        return comparison

class CohortAnalyzer:
    """Analyze user cohorts for retention and LTV insights"""

    def __init__(self):
        self.cohort_types = ["daily", "weekly", "monthly"]

    def analyze_cohort(self, cohort_type: str, cohort_date: datetime,
                      user_data: List[Dict[str, Any]]) -> CohortAnalysis:
        """Analyze specific user cohort"""
        if cohort_type not in self.cohort_types:
            raise ValueError(f"Invalid cohort type: {cohort_type}")

        # Simulate cohort data
        cohort_size = random.randint(500, 2000)

        # Generate retention rates for different periods
        retention_rates = {}
        periods = [1, 7, 14, 30, 60, 90] if cohort_type == "daily" else [1, 2, 3, 6, 9, 12]  # days or months

        base_retention = 0.85 if cohort_type == "daily" else 0.70
        for period in periods:
            # Retention decreases over time
            retention_decay = math.exp(-period * 0.05)
            retention_rates[period] = base_retention * retention_decay + random.uniform(-0.05, 0.05)
            retention_rates[period] = max(0, min(1, retention_rates[period]))  # Clamp between 0 and 1

        # Calculate LTV projection
        monthly_revenue_per_user = random.uniform(20, 50)
        avg_lifetime_months = 12  # Simplified calculation
        ltv_projection = monthly_revenue_per_user * avg_lifetime_months * sum(retention_rates.values()) / len(retention_rates)

        # Generate churn prediction
        churn_prediction = {
            "high_risk": random.uniform(0.1, 0.3),  # % of cohort at high risk
            "medium_risk": random.uniform(0.2, 0.4),  # % at medium risk
            "low_risk": random.uniform(0.3, 0.7),  # % at low risk
            "predicted_churn_rate": random.uniform(0.15, 0.35)
        }

        # Segment performance analysis
        segment_performance = {
            "by_acquisition_channel": {
                "organic": {"retention": random.uniform(0.7, 0.9), "ltv": ltv_projection * 1.2},
                "paid": {"retention": random.uniform(0.6, 0.8), "ltv": ltv_projection * 0.9},
                "referral": {"retention": random.uniform(0.8, 0.95), "ltv": ltv_projection * 1.5}
            },
            "by_user_type": {
                "dungeon_master": {"retention": random.uniform(0.8, 0.95), "ltv": ltv_projection * 1.3},
                "player": {"retention": random.uniform(0.6, 0.8), "ltv": ltv_projection * 0.8},
                "content_creator": {"retention": random.uniform(0.85, 0.98), "ltv": ltv_projection * 1.8}
            }
        }

        cohort_analysis = CohortAnalysis(
            id=str(uuid.uuid4()),
            cohort_type=cohort_type,
            cohort_date=cohort_date,
            cohort_size=cohort_size,
            retention_rates=retention_rates,
            ltv_projection=ltv_projection,
            churn_prediction=churn_prediction,
            segment_performance=segment_performance
        )

        return cohort_analysis

    def generate_cohort_matrix(self, cohort_analyses: List[CohortAnalysis]) -> Dict[str, Any]:
        """Generate cohort retention matrix"""
        if not cohort_analyses:
            return {"error": "No cohort data provided"}

        # Create matrix
        cohorts = sorted(cohort_analyses, key=lambda x: x.cohort_date)
        max_periods = max(len(cohort.retention_rates) for cohort in cohorts)

        matrix = {
            "cohort_headers": [],
            "period_headers": [],
            "retention_matrix": [],
            "average_retention": {},
            "insights": []
        }

        # Generate headers
        for cohort in cohorts:
            matrix["cohort_headers"].append(cohort.cohort_date.strftime("%Y-%m-%d"))

        if cohorts:
            max_periods = max(len(cohort.retention_rates) for cohort in cohorts)
            for i in range(max_periods):
                period_label = f"Period {i+1}"
                matrix["period_headers"].append(period_label)

                # Calculate average retention for this period
                period_retentions = []
                for cohort in cohorts:
                    periods = sorted(cohort.retention_rates.keys())
                    if i < len(periods):
                        period_key = periods[i]
                        period_retentions.append(cohort.retention_rates[period_key])

                if period_retentions:
                    matrix["average_retention"][period_label] = statistics.mean(period_retentions)

        # Generate matrix rows
        for cohort in cohorts:
            row = {
                "cohort_date": cohort.cohort_date.strftime("%Y-%m-%d"),
                "cohort_size": cohort.cohort_size,
                "retention_rates": []
            }

            # Fill retention rates for each period
            periods = sorted(cohort.retention_rates.keys())
            for i in range(max_periods):
                if i < len(periods):
                    period_key = periods[i]
                    row["retention_rates"].append(cohort.retention_rates[period_key])
                else:
                    row["retention_rates"].append(None)  # No data for this period

            matrix["retention_matrix"].append(row)

        # Generate insights
        insights = []
        if matrix["average_retention"]:
            first_period_avg = matrix["average_retention"].get("Period 1", 0)
            if first_period_avg < 0.7:
                insights.append("Low initial retention - focus on onboarding improvement")
            elif first_period_avg > 0.9:
                insights.append("Excellent initial retention - maintain onboarding quality")

            # Trend analysis
            if len(matrix["average_retention"]) > 1:
                retention_values = list(matrix["average_retention"].values())
                if retention_values[-1] < retention_values[0] * 0.5:
                    insights.append("Significant retention drop-off - investigate long-term engagement")
                elif retention_values[-1] > retention_values[0] * 0.8:
                    insights.append("Strong long-term retention - users find lasting value")

        matrix["insights"] = insights

        return matrix

class AttributionAnalyzer:
    """Analyze marketing attribution and channel performance"""

    def __init__(self):
        self.attribution_models = ["first_touch", "last_touch", "linear", "time_decay", "position_based"]
        self.touchpoint_types = ["awareness", "consideration", "decision", "purchase"]

    def analyze_attribution(self, model_type: str, conversion_data: List[Dict[str, Any]],
                           date_range: Dict[str, datetime]) -> AttributionModel:
        """Analyze marketing attribution using specified model"""
        if model_type not in self.attribution_models:
            raise ValueError(f"Unknown attribution model: {model_type}")

        # Simulate channel data
        channels = {
            "organic_search": {"conversions": random.randint(50, 200), "revenue": random.uniform(5000, 25000)},
            "paid_search": {"conversions": random.randint(80, 300), "revenue": random.uniform(8000, 35000)},
            "social_media": {"conversions": random.randint(30, 150), "revenue": random.uniform(3000, 18000)},
            "email_marketing": {"conversions": random.randint(40, 180), "revenue": random.uniform(4000, 22000)},
            "referral": {"conversions": random.randint(20, 100), "revenue": random.uniform(2000, 15000)},
            "direct": {"conversions": random.randint(60, 250), "revenue": random.uniform(6000, 30000)},
            "content_marketing": {"conversions": random.randint(25, 120), "revenue": random.uniform(2500, 16000)}
        }

        # Calculate attribution weights based on model
        attribution_weights = self._calculate_attribution_weights(model_type, channels)

        # Generate sample conversion paths
        conversion_paths = []
        for _ in range(random.randint(20, 100)):
            path = self._generate_conversion_path(channels)
            conversion_paths.append(path)

        # Analyze touchpoints
        touchpoint_analysis = self._analyze_touchpoints(conversion_paths, model_type)

        attribution_model = AttributionModel(
            id=str(uuid.uuid4()),
            model_type=model_type,
            channels=channels,
            attribution_weights=attribution_weights,
            conversion_paths=conversion_paths,
            touchpoint_analysis=touchpoint_analysis,
            date_range=date_range
        )

        return attribution_model

    def _calculate_attribution_weights(self, model_type: str, channels: Dict[str, Any]) -> Dict[str, float]:
        """Calculate attribution weights for different models"""
        total_conversions = sum(data["conversions"] for data in channels.values())
        weights = {}

        for channel, data in channels.items():
            base_weight = data["conversions"] / total_conversions if total_conversions > 0 else 0

            if model_type == "first_touch":
                # First touch gets 100% credit
                weights[channel] = base_weight
            elif model_type == "last_touch":
                # Last touch gets 100% credit
                weights[channel] = base_weight
            elif model_type == "linear":
                # All touchpoints get equal credit
                weights[channel] = base_weight
            elif model_type == "time_decay":
                # More recent touchpoints get more credit
                decay_factor = random.uniform(0.8, 1.2)
                weights[channel] = base_weight * decay_factor
            elif model_type == "position_based":
                # First and last touch get 40% each, middle gets 20%
                position_factor = random.uniform(0.7, 1.3)
                weights[channel] = base_weight * position_factor

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _generate_conversion_path(self, channels: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample conversion path"""
        path_length = random.randint(1, 5)
        selected_channels = random.sample(list(channels.keys()), min(path_length, len(channels)))

        path = {
            "conversion_id": str(uuid.uuid4()),
            "path": selected_channels,
            "touchpoints": [],
            "conversion_value": random.uniform(50, 500)
        }

        # Generate touchpoint details
        for i, channel in enumerate(selected_channels):
            touchpoint = {
                "channel": channel,
                "position": i + 1,
                "timestamp": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "touchpoint_type": random.choice(self.touchpoint_types)
            }
            path["touchpoints"].append(touchpoint)

        return path

    def _analyze_touchpoints(self, conversion_paths: List[Dict[str, Any]], model_type: str) -> Dict[str, Any]:
        """Analyze touchpoint effectiveness"""
        touchpoint_analysis = {
            "average_path_length": 0,
            "most_common_channels": {},
            "channel_position_performance": {},
            "touchpoint_type_effectiveness": {}
        }

        if not conversion_paths:
            return touchpoint_analysis

        # Calculate average path length
        total_length = sum(len(path["path"]) for path in conversion_paths)
        touchpoint_analysis["average_path_length"] = total_length / len(conversion_paths)

        # Most common channels
        channel_frequency = {}
        for path in conversion_paths:
            for channel in path["path"]:
                channel_frequency[channel] = channel_frequency.get(channel, 0) + 1

        # Sort by frequency
        sorted_channels = sorted(channel_frequency.items(), key=lambda x: x[1], reverse=True)
        touchpoint_analysis["most_common_channels"] = dict(sorted_channels[:5])

        # Channel position performance
        position_performance = {}
        for path in conversion_paths:
            for touchpoint in path["touchpoints"]:
                channel = touchpoint["channel"]
                position = touchpoint["position"]

                if channel not in position_performance:
                    position_performance[channel] = {"positions": [], "conversion_values": []}

                position_performance[channel]["positions"].append(position)
                position_performance[channel]["conversion_values"].append(path["conversion_value"])

        # Calculate average position and value per channel
        for channel, data in position_performance.items():
            avg_position = sum(data["positions"]) / len(data["positions"]) if data["positions"] else 0
            avg_value = sum(data["conversion_values"]) / len(data["conversion_values"]) if data["conversion_values"] else 0

            touchpoint_analysis["channel_position_performance"][channel] = {
                "average_position": avg_position,
                "average_conversion_value": avg_value,
                "total_touchpoints": len(data["positions"])
            }

        return touchpoint_analysis

class GrowthAnalytics:
    """Main growth analytics orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_calculator = GrowthMetricsCalculator()
        self.funnel_analyzer = FunnelAnalyzer()
        self.cohort_analyzer = CohortAnalyzer()
        self.attribution_analyzer = AttributionAnalyzer()
        self.reports = {}
        self.alerts = []

    def generate_growth_dashboard(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate comprehensive growth dashboard"""
        dashboard = {
            "date_range": date_range,
            "generated_at": datetime.utcnow(),
            "summary_metrics": {},
            "funnel_analyses": {},
            "cohort_analyses": {},
            "attribution_analyses": {},
            "growth_score": {},
            "alerts": [],
            "recommendations": []
        }

        # Calculate key metrics
        metric_names = [
            "new_users", "customer_acquisition_cost", "conversion_rate",
            "activation_rate", "retention_rate", "monthly_recurring_revenue",
            "ltv_cac_ratio", "viral_coefficient"
        ]

        metrics = []
        for metric_name in metric_names:
            metric = self.metrics_calculator.calculate_metric(metric_name, {}, {})
            metrics.append(metric)

        dashboard["summary_metrics"] = {m.name: asdict(m) for m in metrics}

        # Calculate growth score
        growth_score = self.metrics_calculator.calculate_growth_score(metrics)
        dashboard["growth_score"] = growth_score

        # Analyze funnels
        user_funnel = self.funnel_analyzer.analyze_funnel("user_acquisition", {}, date_range)
        trial_funnel = self.funnel_analyzer.analyze_funnel("trial_conversion", {}, date_range)

        dashboard["funnel_analyses"] = {
            "user_acquisition": asdict(user_funnel),
            "trial_conversion": asdict(trial_funnel)
        }

        # Analyze cohorts
        recent_cohorts = []
        for i in range(3):  # Last 3 months
            cohort_date = date_range["start"] + timedelta(days=i*30)
            cohort = self.cohort_analyzer.analyze_cohort("monthly", cohort_date, [])
            recent_cohorts.append(cohort)

        cohort_matrix = self.cohort_analyzer.generate_cohort_matrix(recent_cohorts)
        dashboard["cohort_analyses"] = {
            "recent_cohorts": [asdict(cohort) for cohort in recent_cohorts],
            "cohort_matrix": cohort_matrix
        }

        # Analyze attribution
        attribution_model = self.attribution_analyzer.analyze_attribution("linear", [], date_range)
        dashboard["attribution_analyses"] = {
            "primary_model": asdict(attribution_model)
        }

        # Generate alerts
        alerts = self._generate_alerts(metrics, growth_score)
        dashboard["alerts"] = alerts

        # Generate recommendations
        recommendations = self._generate_recommendations(dashboard)
        dashboard["recommendations"] = recommendations

        return dashboard

    def _generate_alerts(self, metrics: List[GrowthMetric], growth_score: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for concerning metrics"""
        alerts = []

        # Check overall growth score
        if growth_score["overall_score"] < 60:
            alerts.append({
                "type": "critical",
                "message": f"Overall growth score is {growth_score['overall_score']:.1f} ({growth_score['rating']})",
                "action": "Immediate attention required",
                "metrics_affected": list(growth_score["category_scores"].keys())
            })

        # Check individual metrics
        for metric in metrics:
            # Significant decline
            if metric.change_percentage < -20:
                alerts.append({
                    "type": "warning",
                    "message": f"{metric.name} declined by {abs(metric.change_percentage):.1f}%",
                    "action": "Investigate root cause and implement corrective actions",
                    "metric": metric.name
                })

            # Below target
            if metric.achievement_rate < 70:
                alerts.append({
                    "type": "info",
                    "message": f"{metric.name} is {metric.achievement_rate:.1f}% of target",
                    "action": "Review strategy and adjust tactics",
                    "metric": metric.name
                })

        # Check for critical metrics
        retention_metric = next((m for m in metrics if m.name == "retention_rate"), None)
        if retention_metric and retention_metric.value < 70:
            alerts.append({
                "type": "critical",
                "message": f"Retention rate is {retention_metric.value:.1f}% - below healthy threshold",
                "action": "Implement retention campaigns immediately",
                "metric": "retention_rate"
            })

        return alerts

    def _generate_recommendations(self, dashboard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on dashboard data"""
        recommendations = []

        # Growth score recommendations
        growth_score = dashboard["growth_score"]
        for category, score in growth_score["category_scores"].items():
            if score < 70:
                if category == "acquisition":
                    recommendations.append({
                        "priority": "high",
                        "category": "Acquisition",
                        "recommendation": "Optimize conversion rates and reduce customer acquisition costs",
                        "expected_impact": "15-25% improvement in acquisition efficiency",
                        "actions": ["A/B test landing pages", "Optimize ad targeting", "Improve value proposition"]
                    })
                elif category == "retention":
                    recommendations.append({
                        "priority": "critical",
                        "category": "Retention",
                        "recommendation": "Implement comprehensive retention strategy",
                        "expected_impact": "20-30% reduction in churn",
                        "actions": ["User onboarding optimization", "Engagement campaigns", "Support improvements"]
                    })

        # Funnel recommendations
        user_funnel = dashboard["funnel_analyses"]["user_acquisition"]
        if user_funnel["overall_conversion_rate"] < 0.05:  # Less than 5%
            recommendations.append({
                "priority": "high",
                "category": "Conversion Optimization",
                "recommendation": "Focus on improving conversion funnel efficiency",
                "expected_impact": "2-3x improvement in overall conversion rate",
                "actions": ["Simplify signup process", "Add social proof", "Optimize landing pages"]
            })

        # Cohort recommendations
        cohort_matrix = dashboard["cohort_analyses"]["cohort_matrix"]
        if cohort_matrix.get("insights"):
            for insight in cohort_matrix["insights"]:
                if "Low initial retention" in insight:
                    recommendations.append({
                        "priority": "high",
                        "category": "Onboarding",
                        "recommendation": "Improve user onboarding experience",
                        "expected_impact": "10-20% improvement in initial retention",
                        "actions": ["Interactive tutorials", "Progressive onboarding", "Quick wins"]
                    })

        # Attribution recommendations
        attribution = dashboard["attribution_analyses"]["primary_model"]
        if attribution["attribution_weights"]:
            # Find underperforming channels
            top_channel = max(attribution["attribution_weights"].items(), key=lambda x: x[1])
            recommendations.append({
                "priority": "medium",
                "category": "Marketing Mix",
                "recommendation": f"Optimize marketing channel mix - {top_channel[0]} is top performer",
                "expected_impact": "15-25% improvement in marketing ROI",
                "actions": ["Allocate more budget to top channels", "Test new channels", "Optimize underperformers"]
            })

        return recommendations

    def create_growth_report(self, report_type: str, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Create specific growth report"""
        if report_type == "weekly":
            return self._create_weekly_report(date_range)
        elif report_type == "monthly":
            return self._create_monthly_report(date_range)
        elif report_type == "quarterly":
            return self._create_quarterly_report(date_range)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _create_weekly_report(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Create weekly growth report"""
        # Focus on short-term metrics and trends
        key_metrics = [
            "new_users", "daily_active_users", "conversion_rate",
            "retention_rate", "viral_coefficient"
        ]

        metrics = []
        for metric_name in key_metrics:
            metric = self.metrics_calculator.calculate_metric(metric_name, {}, {})
            metrics.append(metric)

        return {
            "report_type": "weekly",
            "date_range": date_range,
            "key_metrics": {m.name: asdict(m) for m in metrics},
            "weekly_highlights": [
                "Top performing acquisition channels identified",
                "Conversion optimization experiments completed",
                "Community engagement activities executed"
            ],
            "focus_areas": [
                "Monitor user activity patterns",
                "Optimize high-impact funnels",
                "Address immediate bottlenecks"
            ],
            "next_week_priorities": [
                "Execute A/B test results",
                "Scale successful campaigns",
                "Address critical issues"
            ]
        }

    def _create_monthly_report(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Create monthly growth report"""
        dashboard = self.generate_growth_dashboard(date_range)

        return {
            "report_type": "monthly",
            "date_range": date_range,
            "executive_summary": {
                "growth_score": dashboard["growth_score"]["overall_score"],
                "rating": dashboard["growth_score"]["rating"],
                "key_achievements": [
                    "Strong user acquisition growth",
                    "Improved conversion rates",
                    "Successful product launches"
                ] if dashboard["growth_score"]["overall_score"] > 75 else [
                    "Areas for improvement identified",
                    "Optimization opportunities found",
                    "Strategic adjustments needed"
                ]
            },
            "detailed_metrics": dashboard["summary_metrics"],
            "funnel_performance": dashboard["funnel_analyses"],
            "cohort_insights": dashboard["cohort_analyses"],
            "attribution_analysis": dashboard["attribution_analyses"],
            "strategic_recommendations": dashboard["recommendations"],
            "next_month_focus": [
                "Implement top priority recommendations",
                "Scale successful experiments",
                "Address critical bottlenecks"
            ]
        }

    def _create_quarterly_report(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Create quarterly strategic report"""
        # Generate quarterly insights
        quarterly_metrics = {
            "quarterly_growth_rate": random.uniform(0.40, 1.20),  # 40-120% quarterly growth
            "cumulative_revenue": random.uniform(200000, 1000000),
            "customer_base_growth": random.uniform(0.50, 2.00),
            "market_expansion": random.uniform(0.10, 0.30)
        }

        return {
            "report_type": "quarterly",
            "date_range": date_range,
            "strategic_overview": {
                "quarter_performance": "strong" if quarterly_metrics["quarterly_growth_rate"] > 0.8 else "moderate",
                "key_milestones": [
                    "Product launches completed",
                    "Market expansion achieved",
                    "Strategic partnerships formed"
                ],
                "competitive_position": "gaining market share"
            },
            "growth_metrics": quarterly_metrics,
            "strategic_initiatives": [
                {
                    "initiative": "Product Innovation",
                    "status": "on_track",
                    "impact": "High",
                    "next_steps": "Continue R&D investment"
                },
                {
                    "initiative": "Market Expansion",
                    "status": "ahead_of_schedule",
                    "impact": "Medium",
                    "next_steps": "Scale successful channels"
                },
                {
                    "initiative": "Community Building",
                    "status": "needs_attention",
                    "impact": "High",
                    "next_steps": "Increase community investment"
                }
            ],
            "next_quarter_priorities": [
                "Scale successful growth channels",
                "Optimize unit economics",
                "Expand into new markets",
                "Strengthen product moat"
            ]
        }

# Example usage
async def main():
    """Example usage of the growth analytics system"""

    # Initialize growth analytics
    analytics = GrowthAnalytics({})

    # Define date range
    date_range = {
        "start": datetime.utcnow() - timedelta(days=30),
        "end": datetime.utcnow()
    }

    # Generate growth dashboard
    dashboard = analytics.generate_growth_dashboard(date_range)
    print("Growth Dashboard Generated:")
    print(f"Overall Growth Score: {dashboard['growth_score']['overall_score']:.1f}")
    print(f"Rating: {dashboard['growth_score']['rating']}")
    print(f"Total Alerts: {len(dashboard['alerts'])}")
    print(f"Recommendations: {len(dashboard['recommendations'])}")

    # Create reports
    weekly_report = analytics.create_growth_report("weekly", date_range)
    monthly_report = analytics.create_growth_report("monthly", date_range)
    quarterly_report = analytics.create_growth_report("quarterly", date_range)

    print(f"\nReports Generated:")
    print(f"  Weekly: {len(weekly_report['key_metrics'])} metrics")
    print(f"  Monthly: {len(monthly_report['detailed_metrics'])} metrics")
    print(f"  Quarterly: {len(quarterly_report['strategic_initiatives'])} initiatives")

    # Display key insights
    print(f"\nKey Insights:")
    for alert in dashboard["alerts"][:3]:
        print(f"  Alert: {alert['message']}")

    for rec in dashboard["recommendations"][:3]:
        print(f"  Recommendation: {rec['recommendation']}")

if __name__ == "__main__":
    asyncio.run(main())