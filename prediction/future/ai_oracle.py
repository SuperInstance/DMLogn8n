#!/usr/bin/env python3
"""
AI Oracle - AI-powered future insights and recommendations system
Synthesizes predictions from all systems to provide actionable insights
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

try:
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import cross_val_score
    from scipy import stats
    from scipy.optimize import minimize
except ImportError:
    print("Warning: scikit-learn/scipy not available. Using simplified AI oracle")

# Import other prediction modules
from predictive_engine import Prediction, get_predictive_engine
from pattern_analyzer import Pattern, get_pattern_analyzer
from future_simulator import SimulationResult, get_future_simulator
from market_predictor import MarketPrediction, get_market_predictor
from behavioral_analytics import BehaviorPrediction, get_behavioral_analytics
from event_forecaster import EventPrediction, get_event_forecaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights the oracle can provide"""
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    WARNING = "warning"
    OPPORTUNITY = "opportunity"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATION = "recommendation"
    FORECAST = "forecast"
    TREND_ANALYSIS = "trend_analysis"
    SYNTHESIS = "synthesis"


class ConfidenceLevel(Enum):
    """Confidence levels for insights"""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class ActionType(Enum):
    """Types of recommended actions"""
    MONITOR = "monitor"
    PREPARE = "prepare"
    ACT = "act"
    INVEST = "invest"
    DIVERGE = "diverge"
    CONVERGE = "converge"
    STRENGTHEN = "strengthen"
    WEAKEN = "weaken"
    ESCALATE = "escalate"
    DE_ESCALATE = "de_escalate"


@dataclass
class Insight:
    """Represents an AI-generated insight"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence: ConfidenceLevel
    timestamp: datetime
    time_horizon: int  # hours
    impact_level: int  # 1-10
    affected_domains: List[str]
    supporting_evidence: List[str]
    data_sources: List[str]
    probability: float
    urgency: int  # 1-10
    actionability: int  # 1-10


@dataclass
class Recommendation:
    """Represents an actionable recommendation"""
    recommendation_id: str
    insight_id: str
    action_type: ActionType
    title: str
    description: str
    expected_outcome: str
    confidence: float
    resource_requirements: Dict[str, Any]
    timeline: str
    risk_level: int  # 1-10
    reward_potential: int  # 1-10
    prerequisites: List[str]
    success_metrics: List[str]


@dataclass
class OracleSession:
    """Represents a consultation session with the oracle"""
    session_id: str
    timestamp: datetime
    query: str
    insights: List[Insight]
    recommendations: List[Recommendation]
    confidence_score: float
    processing_time: float
    model_versions: Dict[str, str]


class InsightGenerator:
    """Generates insights from various prediction sources"""

    def __init__(self):
        self.insight_templates = self._initialize_templates()
        self.domain_weights = {
            "market": 0.25,
            "behavioral": 0.20,
            "events": 0.20,
            "patterns": 0.15,
            "simulation": 0.20
        }

    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize insight generation templates"""
        return {
            "market_opportunity": {
                "type": InsightType.OPPORTUNITY,
                "impact_range": (6, 9),
                "urgency_range": (4, 7),
                "triggers": ["bullish_trend", "low_volatility", "high_volume"],
                "evidence_required": 2
            },
            "market_risk": {
                "type": InsightType.WARNING,
                "impact_range": (7, 10),
                "urgency_range": (6, 9),
                "triggers": ["bearish_trend", "high_volatility", "low_confidence"],
                "evidence_required": 2
            },
            "player_retention": {
                "type": InsightType.STRATEGIC,
                "impact_range": (5, 8),
                "urgency_range": (3, 6),
                "triggers": ["churn_risk", "low_engagement", "inactivity"],
                "evidence_required": 2
            },
            "event_cascade": {
                "type": InsightType.WARNING,
                "impact_range": (8, 10),
                "urgency_range": (8, 10),
                "triggers": ["high_probability_events", "dependency_chain"],
                "evidence_required": 1
            },
            "pattern_shift": {
                "type": InsightType.TREND_ANALYSIS,
                "impact_range": (4, 7),
                "urgency_range": (2, 5),
                "triggers": ["new_pattern", "pattern_break", "anomaly"],
                "evidence_required": 1
            },
            "strategic_opportunity": {
                "type": InsightType.STRATEGIC,
                "impact_range": (7, 10),
                "urgency_range": (3, 6),
                "triggers": ["convergence", "market_gap", "competitive_advantage"],
                "evidence_required": 3
            }
        }

    def generate_insights(self, prediction_data: Dict[str, Any]) -> List[Insight]:
        """Generate insights from prediction data"""
        insights = []

        try:
            # Market insights
            market_insights = self._generate_market_insights(prediction_data.get("market", []))
            insights.extend(market_insights)

            # Behavioral insights
            behavioral_insights = self._generate_behavioral_insights(prediction_data.get("behavioral", []))
            insights.extend(behavioral_insights)

            # Event insights
            event_insights = self._generate_event_insights(prediction_data.get("events", []))
            insights.extend(event_insights)

            # Pattern insights
            pattern_insights = self._generate_pattern_insights(prediction_data.get("patterns", []))
            insights.extend(pattern_insights)

            # Simulation insights
            simulation_insights = self._generate_simulation_insights(prediction_data.get("simulation"))
            insights.extend(simulation_insights)

            # Synthesis insights
            synthesis_insights = self._generate_synthesis_insights(insights)
            insights.extend(synthesis_insights)

            # Rank insights by impact and urgency
            insights.sort(key=lambda i: (i.impact_level * i.urgency), reverse=True)

            return insights[:20]  # Return top 20 insights

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []

    def _generate_market_insights(self, market_predictions: List[MarketPrediction]) -> List[Insight]:
        """Generate insights from market predictions"""
        insights = []

        if not market_predictions:
            return insights

        # Analyze market trends
        bullish_signals = [p for p in market_predictions if p.risk_metrics.get("expected_return", 0) > 0.05]
        bearish_signals = [p for p in market_predictions if p.risk_metrics.get("expected_return", 0) < -0.05]

        if len(bullish_signals) >= 3:
            insight = Insight(
                insight_id=f"market_bullish_{datetime.now().timestamp()}",
                insight_type=InsightType.OPPORTUNITY,
                title="Bullish Market Trend Detected",
                description=f"Strong upward momentum across {len(bullish_signals)} markets suggests favorable investment conditions",
                confidence=ConfidenceLevel.HIGH,
                timestamp=datetime.now(),
                time_horizon=72,
                impact_level=7,
                affected_domains=["economy", "trading"],
                supporting_evidence=[f"Positive returns in {', '.join([p.symbol for p in bullish_signals[:3]])}"],
                data_sources=["market_predictor"],
                probability=sum(p.confidence for p in bullish_signals) / len(bullish_signals),
                urgency=5,
                actionability=8
            )
            insights.append(insight)

        if len(bearish_signals) >= 2:
            insight = Insight(
                insight_id=f"market_bearish_{datetime.now().timestamp()}",
                insight_type=InsightType.WARNING,
                title="Market Downtrend Warning",
                description=f"Declining prices across {len(bearish_signals)} markets indicate potential market correction",
                confidence=ConfidenceLevel.MODERATE,
                timestamp=datetime.now(),
                time_horizon=48,
                impact_level=8,
                affected_domains=["economy", "investments"],
                supporting_evidence=[f"Negative returns in {', '.join([p.symbol for p in bearish_signals])}"],
                data_sources=["market_predictor"],
                probability=sum(p.confidence for p in bearish_signals) / len(bearish_signals),
                urgency=7,
                actionability=8
            )
            insights.append(insight)

        return insights

    def _generate_behavioral_insights(self, behavioral_predictions: List[BehaviorPrediction]) -> List[Insight]:
        """Generate insights from behavioral predictions"""
        insights = []

        if not behavioral_predictions:
            return insights

        # Analyze churn risk
        high_risk_players = [p for p in behavioral_predictions
                           if p.prediction_type.value == "churn_prediction" and p.confidence > 0.7]

        if high_risk_players:
            insight = Insight(
                insight_id=f"churn_risk_{datetime.now().timestamp()}",
                insight_type=InsightType.WARNING,
                title="Player Churn Risk Alert",
                description=f"{len(high_risk_players)} players show high churn risk in next 24 hours",
                confidence=ConfidenceLevel.HIGH,
                timestamp=datetime.now(),
                time_horizon=24,
                impact_level=6,
                affected_domains=["player_retention", "engagement"],
                supporting_evidence=[f"High risk players: {', '.join([p.player_id for p in high_risk_players[:5]])}"],
                data_sources=["behavioral_analytics"],
                probability=sum(p.confidence for p in high_risk_players) / len(high_risk_players),
                urgency=8,
                actionability=9
            )
            insights.append(insight)

        # Analyze engagement opportunities
        engagement_predictions = [p for p in behavioral_predictions
                                if p.prediction_type.value == "retention_risk" and p.predicted_behavior == "high_retention"]

        if len(engagement_predictions) >= 5:
            insight = Insight(
                insight_id=f"engagement_opportunity_{datetime.now().timestamp()}",
                insight_type=InsightType.OPPORTUNITY,
                title="High Engagement Opportunity",
                description=f"{len(engagement_predictions)} players show high retention potential",
                confidence=ConfidenceLevel.MODERATE,
                timestamp=datetime.now(),
                time_horizon=48,
                impact_level=5,
                affected_domains=["player_engagement", "monetization"],
                supporting_evidence=[f"High retention players: {len(engagement_predictions)}"],
                data_sources=["behavioral_analytics"],
                probability=sum(p.confidence for p in engagement_predictions) / len(engagement_predictions),
                urgency=4,
                actionability=7
            )
            insights.append(insight)

        return insights

    def _generate_event_insights(self, event_predictions: List[EventPrediction]) -> List[Insight]:
        """Generate insights from event predictions"""
        insights = []

        if not event_predictions:
            return insights

        # High probability events
        high_prob_events = [e for e in event_predictions if e.probability > 0.7]

        if high_prob_events:
            for event in high_prob_events[:3]:  # Top 3 high-probability events
                insight = Insight(
                    insight_id=f"event_{event.event_type.value}_{datetime.now().timestamp()}",
                    insight_type=InsightType.WARNING if event.estimated_severity.value >= 4 else InsightType.FORECAST,
                    title=f"Upcoming {event.event_type.value.replace('_', ' ').title()}",
                    description=f"{event.event_type.value.replace('_', ' ').title()} predicted with {event.probability:.1%} probability",
                    confidence=ConfidenceLevel.HIGH if event.confidence > 0.7 else ConfidenceLevel.MODERATE,
                    timestamp=datetime.now(),
                    time_horizon=event.time_horizon,
                    impact_level=event.estimated_severity.value,
                    affected_domains=["world_events", event.location],
                    supporting_evidence=[f"Location: {event.location}", f"Severity: {event.estimated_severity.name}"],
                    data_sources=["event_forecaster"],
                    probability=event.probability,
                    urgency=min(10, event.estimated_severity.value * 2),
                    actionability=6
                )
                insights.append(insight)

        # Event cascades
        cascade_events = [e for e in event_predictions if e.chain_position is not None]

        if len(cascade_events) >= 2:
            insight = Insight(
                insight_id=f"event_cascade_{datetime.now().timestamp()}",
                insight_type=InsightType.WARNING,
                title="Event Cascade Risk",
                description=f"Multiple related events may trigger a cascade effect",
                confidence=ConfidenceLevel.HIGH,
                timestamp=datetime.now(),
                time_horizon=max(e.time_horizon for e in cascade_events),
                impact_level=8,
                affected_domains=["world_stability", "crisis_management"],
                supporting_evidence=[f"Cascade events: {len(cascade_events)}"],
                data_sources=["event_forecaster"],
                probability=sum(e.probability for e in cascade_events) / len(cascade_events),
                urgency=9,
                actionability=8
            )
            insights.append(insight)

        return insights

    def _generate_pattern_insights(self, patterns: List[Pattern]) -> List[Insight]:
        """Generate insights from pattern analysis"""
        insights = []

        if not patterns:
            return insights

        # Strong patterns
        strong_patterns = [p for p in patterns if p.confidence > 0.8 and p.strength > 0.7]

        for pattern in strong_patterns[:3]:
            insight = Insight(
                insight_id=f"pattern_{pattern.pattern_type.value}_{datetime.now().timestamp()}",
                insight_type=InsightType.TREND_ANALYSIS,
                title=f"Strong {pattern.pattern_type.value.replace('_', ' ').title()} Pattern Detected",
                description=f"Reliable {pattern.pattern_type.value} pattern identified in {pattern.data_source}",
                confidence=ConfidenceLevel.VERY_HIGH,
                timestamp=datetime.now(),
                time_horizon=int(pattern.duration or 24),
                impact_level=5,
                affected_domains=[pattern.data_source, "predictive_analytics"],
                supporting_evidence=[f"Strength: {pattern.strength:.2f}", f"Duration: {pattern.duration:.1f}h"],
                data_sources=["pattern_analyzer"],
                probability=pattern.confidence,
                urgency=3,
                actionability=6
            )
            insights.append(insight)

        # Anomalies
        anomaly_patterns = [p for p in patterns if p.pattern_type == PatternType.ANOMALY]

        if anomaly_patterns:
            insight = Insight(
                insight_id=f"anomaly_cluster_{datetime.now().timestamp()}",
                insight_type=InsightType.WARNING,
                title="Anomaly Cluster Detected",
                description=f"{len(anomaly_patterns)} unusual patterns detected across systems",
                confidence=ConfidenceLevel.MODERATE,
                timestamp=datetime.now(),
                time_horizon=12,
                impact_level=6,
                affected_domains=["system_health", "anomaly_detection"],
                supporting_evidence=[f"Anomalies in: {', '.join(set([p.data_source for p in anomaly_patterns]))}"],
                data_sources=["pattern_analyzer"],
                probability=sum(p.confidence for p in anomaly_patterns) / len(anomaly_patterns),
                urgency=6,
                actionability=7
            )
            insights.append(insight)

        return insights

    def _generate_simulation_insights(self, simulation_result: Optional[SimulationResult]) -> List[Insight]:
        """Generate insights from simulation results"""
        insights = []

        if not simulation_result:
            return insights

        # Risk assessment
        high_risk_scenarios = [s for s in simulation_result.scenarios if s.scenario_type.value in ["pessimistic", "black_swan"]]

        if high_risk_scenarios:
            worst_case = max(high_risk_scenarios, key=lambda s: min(s.outcomes.get("value", [0])))
            insight = Insight(
                insight_id=f"simulation_risk_{datetime.now().timestamp()}",
                insight_type=InsightType.RISK_ASSESSMENT,
                title="Worst-Case Scenario Analysis",
                description=f"Simulation indicates {worst_case.scenario_type.value} scenario with {worst_case.probability:.1%} probability",
                confidence=ConfidenceLevel.HIGH,
                timestamp=datetime.now(),
                time_horizon=simulation_result.parameters.time_horizon * 24,
                impact_level=8,
                affected_domains=["risk_management", "strategic_planning"],
                supporting_evidence=[f"Scenario probability: {worst_case.probability:.1%}"],
                data_sources=["future_simulator"],
                probability=worst_case.probability,
                urgency=5,
                actionability=7
            )
            insights.append(insight)

        # Opportunity scenarios
        opportunity_scenarios = [s for s in simulation_result.scenarios if s.scenario_type.value == "optimistic"]

        if opportunity_scenarios:
            best_case = max(opportunity_scenarios, key=lambda s: max(s.outcomes.get("value", [0])))
            insight = Insight(
                insight_id=f"simulation_opportunity_{datetime.now().timestamp()}",
                insight_type=InsightType.OPPORTUNITY,
                title="Optimistic Scenario Potential",
                description=f"Simulation shows potential for favorable outcomes with {best_case.probability:.1%} probability",
                confidence=ConfidenceLevel.MODERATE,
                timestamp=datetime.now(),
                time_horizon=simulation_result.parameters.time_horizon * 24,
                impact_level=7,
                affected_domains=["strategic_planning", "growth_opportunities"],
                supporting_evidence=[f"Opportunity probability: {best_case.probability:.1%}"],
                data_sources=["future_simulator"],
                probability=best_case.probability,
                urgency=4,
                actionability=8
            )
            insights.append(insight)

        return insights

    def _generate_synthesis_insights(self, existing_insights: List[Insight]) -> List[Insight]:
        """Generate higher-level synthesis insights"""
        insights = []

        if len(existing_insights) < 2:
            return insights

        # Convergence analysis
        domain_distribution = defaultdict(int)
        for insight in existing_insights:
            for domain in insight.affected_domains:
                domain_distribution[domain] += 1

        # Look for cross-domain patterns
        high_activity_domains = [d for d, count in domain_distribution.items() if count >= 3]

        if high_activity_domains:
            insight = Insight(
                insight_id=f"cross_domain_{datetime.now().timestamp()}",
                insight_type=InsightType.SYNTHESIS,
                title=f"Cross-Domain Pattern in {', '.join(high_activity_domains[:2])}",
                description=f"Multiple indicators suggest coordinated activity across {len(high_activity_domains)} domains",
                confidence=ConfidenceLevel.MODERATE,
                timestamp=datetime.now(),
                time_horizon=48,
                impact_level=6,
                affected_domains=high_activity_domains,
                supporting_evidence=[f"{count} insights in {domain}" for domain, count in domain_distribution.items() if count >= 2],
                data_sources=["synthesis_engine"],
                probability=min(0.9, sum(i.probability for i in existing_insights) / len(existing_insights)),
                urgency=5,
                actionability=7
            )
            insights.append(insight)

        return insights


class RecommendationEngine:
    """Generates actionable recommendations from insights"""

    def __init__(self):
        self.action_templates = self._initialize_action_templates()

    def _initialize_action_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize recommendation templates"""
        return {
            "market_opportunity": {
                "action_type": ActionType.INVEST,
                "timeline": "immediate to 1 week",
                "resource_requirements": {"capital": "variable", "analysis": "medium"},
                "risk_level": 4,
                "reward_potential": 8,
                "success_metrics": ["ROI", "market_share", "profit_margin"]
            },
            "market_risk": {
                "action_type": ActionType.DIVERGE,
                "timeline": "immediate",
                "resource_requirements": {"capital": "low", "monitoring": "high"},
                "risk_level": 7,
                "reward_potential": 3,
                "success_metrics": ["capital_preservation", "risk_exposure"]
            },
            "player_retention": {
                "action_type": ActionType.ACT,
                "timeline": "24-48 hours",
                "resource_requirements": {"personnel": "medium", "incentives": "variable"},
                "risk_level": 3,
                "reward_potential": 7,
                "success_metrics": ["retention_rate", "player_satisfaction", "LTV"]
            },
            "strategic_opportunity": {
                "action_type": ActionType.STRENGTHEN,
                "timeline": "1-4 weeks",
                "resource_requirements": {"investment": "high", "planning": "high"},
                "risk_level": 6,
                "reward_potential": 9,
                "success_metrics": ["market_position", "competitive_advantage", "growth_rate"]
            }
        }

    def generate_recommendations(self, insights: List[Insight]) -> List[Recommendation]:
        """Generate recommendations from insights"""
        recommendations = []

        for insight in insights[:10]:  # Top 10 insights
            recommendation = self._create_recommendation(insight)
            if recommendation:
                recommendations.append(recommendation)

        # Sort by reward/risk ratio
        recommendations.sort(key=lambda r: (r.reward_potential / (r.risk_level + 1)), reverse=True)

        return recommendations[:15]  # Return top 15 recommendations

    def _create_recommendation(self, insight: Insight) -> Optional[Recommendation]:
        """Create a recommendation from an insight"""
        try:
            # Determine action type based on insight
            if insight.insight_type == InsightType.OPPORTUNITY:
                if "market" in insight.affected_domains:
                    action_type = ActionType.INVEST
                else:
                    action_type = ActionType.ACT
            elif insight.insight_type == InsightType.WARNING:
                if "market" in insight.affected_domains:
                    action_type = ActionType.DIVERGE
                else:
                    action_type = ActionType.PREPARE
            elif insight.insight_type == InsightType.STRATEGIC:
                action_type = ActionType.STRENGTHEN
            else:
                action_type = ActionType.MONITOR

            # Get template for this action type
            template_key = None
            for key, template in self.action_templates.items():
                if any(keyword in insight.title.lower() for keyword in key.split('_')):
                    template_key = key
                    break

            if not template_key:
                template_key = "strategic_opportunity"  # Default

            template = self.action_templates[template_key]

            recommendation = Recommendation(
                recommendation_id=f"rec_{insight.insight_id}",
                insight_id=insight.insight_id,
                action_type=action_type,
                title=f"{action_type.value.title()}: {insight.title}",
                description=self._generate_recommendation_description(insight, action_type),
                expected_outcome=self._generate_expected_outcome(insight, action_type),
                confidence=insight.probability,
                resource_requirements=template["resource_requirements"],
                timeline=template["timeline"],
                risk_level=template["risk_level"],
                reward_potential=template["reward_potential"],
                prerequisites=self._generate_prerequisites(insight),
                success_metrics=template["success_metrics"]
            )

            return recommendation

        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            return None

    def _generate_recommendation_description(self, insight: Insight, action_type: ActionType) -> str:
        """Generate detailed recommendation description"""
        descriptions = {
            ActionType.INVEST: f"Based on the {insight.insight_type.value.lower()} identified, consider allocating resources to capitalize on this opportunity. The expected return potential justifies the investment risk.",
            ActionType.DIVERGE: f"In response to the {insight.insight_type.value.lower()}, diversify your holdings to minimize exposure. Consider defensive positions and reduce risk across affected domains.",
            ActionType.ACT: f"The {insight.insight_type.value.lower()} requires immediate attention. Implement targeted interventions to address the situation before it escalates.",
            ActionType.PREPARE: f"Prepare contingency plans for the {insight.insight_type.value.lower()}. Establish protocols and allocate resources to respond effectively if the situation materializes.",
            ActionType.MONITOR: f"Continuously monitor the {insight.insight_type.value.lower()}. Set up alerting systems and review protocols to track developments.",
            ActionType.STRENGTHEN: f"Strengthen your position in light of this {insight.insight_type.value.lower()}. Invest resources to build competitive advantages and solidify market presence."
        }

        return descriptions.get(action_type, f"Take appropriate action regarding the {insight.insight_type.value.lower()}.")

    def _generate_expected_outcome(self, insight: Insight, action_type: ActionType) -> str:
        """Generate expected outcome description"""
        outcomes = {
            ActionType.INVEST: "Positive returns and increased market position if trends continue as predicted.",
            ActionType.DIVERGE: "Preservation of capital and reduced exposure to downside risks.",
            ActionType.ACT: "Mitigation of negative impacts and maintenance of system stability.",
            ActionType.PREPARE: "Rapid response capability and minimized disruption if events materialize.",
            ActionType.MONITOR: "Early warning system and timely decision-making based on observed changes.",
            ActionType.STRENGTHEN: "Enhanced competitive position and improved long-term prospects."
        }

        return outcomes.get(action_type, "Improved outcomes based on proactive management.")

    def _generate_prerequisites(self, insight: Insight) -> List[str]:
        """Generate list of prerequisites for the recommendation"""
        prerequisites = []

        # Common prerequisites
        if insight.confidence.value >= 4:
            prerequisites.append("High confidence in predictive models")

        if insight.urgency >= 7:
            prerequisites.append("Rapid decision-making capability")

        if "market" in insight.affected_domains:
            prerequisites.append("Market access and trading infrastructure")

        if "player" in insight.affected_domains:
            prerequisites.append("Player communication channels")

        if insight.impact_level >= 7:
            prerequisites.append("Adequate resource allocation")

        return prerequisites if prerequisites else ["Basic operational capabilities"]


class AIOracle:
    """Main AI Oracle system for synthesizing predictions and providing insights"""

    def __init__(self):
        self.insight_generator = InsightGenerator()
        self.recommendation_engine = RecommendationEngine()
        self.sessions: List[OracleSession] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.model_versions = {
            "predictive_engine": "1.0.0",
            "pattern_analyzer": "1.0.0",
            "market_predictor": "1.0.0",
            "behavioral_analytics": "1.0.0",
            "event_forecaster": "1.0.0",
            "future_simulator": "1.0.0"
        }

    async def consult(self, query: str, context: Optional[Dict[str, Any]] = None) -> OracleSession:
        """Main consultation method - query the oracle for insights"""
        start_time = datetime.now()

        try:
            logger.info(f"Oracle consultation started: {query}")

            # Gather prediction data from all systems
            prediction_data = await self._gather_prediction_data()

            # Generate insights
            insights = self.insight_generator.generate_insights(prediction_data)

            # Generate recommendations
            recommendations = self.recommendation_engine.generate_recommendations(insights)

            # Filter insights based on query context
            filtered_insights = self._filter_insights_by_query(insights, query, context)

            # Filter recommendations based on filtered insights
            filtered_recommendations = [r for r in recommendations
                                      if r.insight_id in [i.insight_id for i in filtered_insights]]

            # Calculate confidence score
            confidence_score = self._calculate_overall_confidence(filtered_insights)

            # Create session
            session = OracleSession(
                session_id=f"oracle_{datetime.now().timestamp()}",
                timestamp=start_time,
                query=query,
                insights=filtered_insights,
                recommendations=filtered_recommendations,
                confidence_score=confidence_score,
                processing_time=(datetime.now() - start_time).total_seconds(),
                model_versions=self.model_versions.copy()
            )

            self.sessions.append(session)

            # Keep session history manageable
            if len(self.sessions) > 100:
                self.sessions = self.sessions[-50:]

            logger.info(f"Oracle consultation completed in {session.processing_time:.2f}s: "
                       f"{len(filtered_insights)} insights, {len(filtered_recommendations)} recommendations")

            return session

        except Exception as e:
            logger.error(f"Error during oracle consultation: {e}")
            # Return empty session on error
            return OracleSession(
                session_id=f"oracle_error_{datetime.now().timestamp()}",
                timestamp=start_time,
                query=query,
                insights=[],
                recommendations=[],
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                model_versions=self.model_versions.copy()
            )

    async def _gather_prediction_data(self) -> Dict[str, Any]:
        """Gather prediction data from all systems"""
        data = {
            "market": [],
            "behavioral": [],
            "events": [],
            "patterns": [],
            "simulation": None
        }

        try:
            # Market predictions (sample data)
            market_predictor = get_market_predictor()
            # In a real implementation, would get actual predictions
            # For now, return empty list

            # Behavioral predictions (sample data)
            behavioral_analytics = get_behavioral_analytics()
            # In a real implementation, would get actual predictions

            # Event predictions (sample data)
            event_forecaster = get_event_forecaster()
            # In a real implementation, would get actual predictions

            # Pattern analysis (sample data)
            pattern_analyzer = get_pattern_analyzer()
            # In a real implementation, would get actual patterns

            # Simulation results (sample data)
            future_simulator = get_future_simulator()
            # In a real implementation, would get latest simulation

        except Exception as e:
            logger.error(f"Error gathering prediction data: {e}")

        return data

    def _filter_insights_by_query(self, insights: List[Insight], query: str,
                                 context: Optional[Dict[str, Any]]) -> List[Insight]:
        """Filter insights based on query relevance"""
        if not query and not context:
            return insights[:10]  # Return top 10 if no query

        filtered_insights = []
        query_lower = query.lower()

        # Keywords for different domains
        domain_keywords = {
            "market": ["market", "economy", "price", "trade", "invest", "financial"],
            "player": ["player", "user", "customer", "retention", "engagement", "behavior"],
            "event": ["event", "disaster", "crisis", "opportunity", "happening"],
            "risk": ["risk", "danger", "threat", "warning", "caution"],
            "opportunity": ["opportunity", "growth", "potential", "profit", "gain"]
        }

        # Determine relevant domains from query
        relevant_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                relevant_domains.append(domain)

        # Add context domains
        if context:
            for domain in context.keys():
                if domain in domain_keywords:
                    relevant_domains.append(domain)

        # Filter insights
        for insight in insights:
            # Check domain relevance
            domain_relevant = any(domain in " ".join(insight.affected_domains).lower()
                                for domain in relevant_domains)

            # Check keyword relevance
            keyword_relevant = any(keyword in insight.title.lower() or keyword in insight.description.lower()
                                  for keyword in query_lower.split() if len(keyword) > 2)

            if domain_relevant or keyword_relevant or not query:  # Include if no query specified
                filtered_insights.append(insight)

        return filtered_insights[:15]  # Return top 15 relevant insights

    def _calculate_overall_confidence(self, insights: List[Insight]) -> float:
        """Calculate overall confidence score for the session"""
        if not insights:
            return 0.0

        # Weight by insight impact and confidence
        total_weight = 0
        weighted_confidence = 0

        for insight in insights:
            weight = insight.impact_level * insight.confidence.value
            weighted_confidence += weight * insight.probability
            total_weight += weight

        if total_weight > 0:
            return weighted_confidence / total_weight
        else:
            return sum(i.probability for i in insights) / len(insights)

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a specific oracle session"""
        for session in self.sessions:
            if session.session_id == session_id:
                return {
                    "session_id": session.session_id,
                    "timestamp": session.timestamp.isoformat(),
                    "query": session.query,
                    "insights_count": len(session.insights),
                    "recommendations_count": len(session.recommendations),
                    "confidence_score": session.confidence_score,
                    "processing_time": session.processing_time,
                    "top_insight": session.insights[0].title if session.insights else None,
                    "top_recommendation": session.recommendations[0].title if session.recommendations else None
                }
        return None

    def get_recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent oracle activity"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_sessions = [s for s in self.sessions if s.timestamp > cutoff_time]

        if not recent_sessions:
            return {"sessions": [], "total_insights": 0, "total_recommendations": 0}

        # Aggregate statistics
        total_insights = sum(len(s.insights) for s in recent_sessions)
        total_recommendations = sum(len(s.recommendations) for s in recent_sessions)
        avg_confidence = sum(s.confidence_score for s in recent_sessions) / len(recent_sessions)

        # Common insight types
        insight_types = defaultdict(int)
        for session in recent_sessions:
            for insight in session.insights:
                insight_types[insight.insight_type.value] += 1

        return {
            "sessions": len(recent_sessions),
            "total_insights": total_insights,
            "total_recommendations": total_recommendations,
            "avg_confidence": avg_confidence,
            "insight_types": dict(insight_types),
            "recent_queries": [s.query for s in recent_sessions[-5:]]
        }


# Singleton instance
_ai_oracle = None

def get_ai_oracle() -> AIOracle:
    """Get the singleton AI oracle instance"""
    global _ai_oracle
    if _ai_oracle is None:
        _ai_oracle = AIOracle()
    return _ai_oracle


async def main():
    """Example usage of the AI Oracle"""
    oracle = get_ai_oracle()

    # Sample queries
    queries = [
        "What are the biggest risks to our economy right now?",
        "How can we improve player retention?",
        "What market opportunities should we pursue?",
        "Are there any major events on the horizon?"
    ]

    for query in queries:
        print(f"\nOracle Query: {query}")
        print("-" * 50)

        session = await oracle.consult(query)

        print(f"Processing time: {session.processing_time:.2f}s")
        print(f"Confidence score: {session.confidence_score:.2f}")
        print(f"Insights generated: {len(session.insights)}")
        print(f"Recommendations: {len(session.recommendations)}")

        # Show top insights
        if session.insights:
            print("\nTop Insights:")
            for i, insight in enumerate(session.insights[:3]):
                print(f"{i+1}. {insight.title}")
                print(f"   {insight.description}")
                print(f"   Impact: {insight.impact_level}/10, Urgency: {insight.urgency}/10")

        # Show top recommendations
        if session.recommendations:
            print("\nTop Recommendations:")
            for i, rec in enumerate(session.recommendations[:2]):
                print(f"{i+1}. {rec.title}")
                print(f"   {rec.description}")
                print(f"   Risk: {rec.risk_level}/10, Reward: {rec.reward_potential}/10")

    # Get recent activity
    print(f"\nRecent Oracle Activity:")
    activity = oracle.get_recent_activity(24)
    print(f"Sessions: {activity['sessions']}")
    print(f"Total insights: {activity['total_insights']}")
    print(f"Total recommendations: {activity['total_recommendations']}")
    print(f"Average confidence: {activity['avg_confidence']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())