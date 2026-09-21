#!/usr/bin/env python3
"""
Event Forecaster - World event prediction and probability modeling system
Predicts future events, calculates probabilities, and models event chains
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import random
import logging

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    from sklearn.model_selection import train_test_split
    from scipy import stats
    from scipy.stats import poisson, expon, weibull_min
    import networkx as nx
except ImportError:
    print("Warning: scikit-learn/scipy/networkx not available. Using simplified event forecasting")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of world events"""
    NATURAL_DISASTER = "natural_disaster"
    POLITICAL_EVENT = "political_event"
    ECONOMIC_CRISIS = "economic_crisis"
    TECHNOLOGICAL_BREAKTHROUGH = "technological_breakthrough"
    SOCIAL_MOVEMENT = "social_movement"
    MILITARY_CONFLICT = "military_conflict"
    PANDEMIC = "pandemic"
    ENVIRONMENTAL_CHANGE = "environmental_change"
    DISCOVERY = "discovery"
    CELEBRATION = "celebration"
    MARKET_CRASH = "market_crash"
    MARKET_BOOM = "market_boom"
    PLAYER_REBELLION = "player_rebellion"
    NPC_UPRISING = "npc_uprising"
    MAGICAL_EVENT = "magical_event"
    ALIEN_ENCOUNTER = "alien_encounter"
    DIMENSIONAL_RIFT = "dimensional_rift"


class EventSeverity(Enum):
    """Severity levels for events"""
    TRIVIAL = 1
    MINOR = 2
    MODERATE = 3
    MAJOR = 4
    SEVERE = 5
    CATASTROPHIC = 6
    EXTINCTION = 7


class EventLikelihood(Enum):
    """Likelihood categories"""
    IMPOSSIBLE = 0.0
    EXTREMELY_UNLIKELY = 0.1
    VERY_UNLIKELY = 0.25
    UNLIKELY = 0.35
    POSSIBLE = 0.5
    LIKELY = 0.65
    VERY_LIKELY = 0.8
    ALMOST_CERTAIN = 0.95
    CERTAIN = 1.0


@dataclass
class Event:
    """Represents a world event"""
    event_id: str
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime
    location: str
    description: str
    duration: float  # in hours
    impact_radius: float  # in game units
    participants: List[str]
    triggers: List[str]
    consequences: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventPrediction:
    """Prediction of a future event"""
    prediction_id: str
    event_type: EventType
    predicted_timestamp: datetime
    probability: float
    confidence: float
    location: str
    estimated_severity: EventSeverity
    contributing_factors: Dict[str, float]
    potential_triggers: List[str]
    time_horizon: int  # hours
    scenario_id: Optional[str] = None
    chain_position: Optional[int] = None


@dataclass
class EventChain:
    """Chain of related events"""
    chain_id: str
    events: List[EventPrediction]
    chain_probability: float
    trigger_event: Optional[str] = None
    propagation_model: str = "linear"
    total_duration: Optional[float] = None


@dataclass
class EventTrigger:
    """Represents a trigger that can cause events"""
    trigger_id: str
    trigger_type: str
    condition: str
    threshold: float
    affected_events: List[EventType]
    weight: float = 1.0
    is_active: bool = True


class ProbabilityModel:
    """Base class for probability modeling"""

    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        self.parameters = {}

    def calculate_probability(self, context: Dict[str, Any]) -> float:
        """Calculate event probability given context"""
        raise NotImplementedError

    def update_parameters(self, new_data: Dict[str, Any]):
        """Update model parameters with new data"""
        raise NotImplementedError


class PoissonEventModel(ProbabilityModel):
    """Poisson distribution model for event frequency"""

    def __init__(self, event_type: EventType, lambda_rate: float = 1.0):
        super().__init__(f"poisson_{event_type.value}")
        self.event_type = event_type
        self.lambda_rate = lambda_rate
        self.is_trained = True

    def calculate_probability(self, context: Dict[str, Any]) -> float:
        """Calculate probability of event occurring in time window"""
        time_window = context.get("time_window", 24)  # hours
        rate_adjustment = context.get("rate_adjustment", 1.0)

        adjusted_lambda = self.lambda_rate * rate_adjustment * (time_window / 24)
        probability = 1 - np.exp(-adjusted_lambda)

        return min(1.0, probability)

    def update_parameters(self, new_data: Dict[str, Any]):
        """Update lambda rate based on observed frequency"""
        observed_events = new_data.get("observed_events", 0)
        time_period = new_data.get("time_period", 24)  # hours

        if time_period > 0:
            new_lambda = observed_events / (time_period / 24)
            # Exponential moving average update
            alpha = 0.1
            self.lambda_rate = (1 - alpha) * self.lambda_rate + alpha * new_lambda


class BayesianEventModel(ProbabilityModel):
    """Bayesian model for event probability with prior knowledge"""

    def __init__(self, event_type: EventType, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        super().__init__(f"bayesian_{event_type.value}")
        self.event_type = event_type
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.posterior_alpha = prior_alpha
        self.posterior_beta = prior_beta
        self.is_trained = True

    def calculate_probability(self, context: Dict[str, Any]) -> float:
        """Calculate posterior probability given evidence"""
        evidence_weight = context.get("evidence_weight", 0)
        evidence_value = context.get("evidence_value", 0.5)

        # Combine prior with evidence
        posterior_mean = self.posterior_alpha / (self.posterior_alpha + self.posterior_beta)

        # Weighted combination
        if evidence_weight > 0:
            probability = (posterior_mean * (1 - evidence_weight) + evidence_value * evidence_weight)
        else:
            probability = posterior_mean

        return max(0.0, min(1.0, probability))

    def update_parameters(self, new_data: Dict[str, Any]):
        """Update posterior parameters with new observations"""
        success_count = new_data.get("success_count", 0)
        failure_count = new_data.get("failure_count", 0)

        self.posterior_alpha += success_count
        self.posterior_beta += failure_count


class MLEventModel(ProbabilityModel):
    """Machine learning model for complex event prediction"""

    def __init__(self, event_type: EventType):
        super().__init__(f"ml_{event_type.value}")
        self.event_type = event_type
        self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> bool:
        """Train the ML model"""
        try:
            if len(X) != len(y) or len(X) < 10:
                logger.warning("Insufficient training data")
                return False

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.feature_names = feature_names
            self.is_trained = True

            logger.info(f"ML model trained for {self.event_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return False

    def calculate_probability(self, context: Dict[str, Any]) -> float:
        """Calculate probability using trained model"""
        if not self.is_trained:
            return 0.5

        try:
            # Extract features from context
            features = []
            for feature_name in self.feature_names:
                features.append(context.get(feature_name, 0))

            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)

            # Get probability of positive class
            probability = self.model.predict_proba(features_scaled)[0][1]
            return probability

        except Exception as e:
            logger.error(f"Error calculating probability: {e}")
            return 0.5

    def update_parameters(self, new_data: Dict[str, Any]):
        """Retrain model with new data (simplified)"""
        # In practice, would implement incremental learning
        pass


class EventDependencyGraph:
    """Models dependencies between events"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.dependency_weights = {}

    def add_event(self, event_type: EventType):
        """Add event type to the graph"""
        self.graph.add_node(event_type.value)

    def add_dependency(self, source: EventType, target: EventType, weight: float = 1.0):
        """Add dependency between events"""
        self.graph.add_edge(source.value, target.value, weight=weight)
        self.dependency_weights[(source.value, target.value)] = weight

    def calculate_cascade_probability(self, initial_event: EventType,
                                    max_depth: int = 3) -> Dict[str, float]:
        """Calculate cascade probabilities for dependent events"""
        cascade_probs = {initial_event.value: 1.0}
        visited = {initial_event.value}

        def propagate(event_name: str, depth: int, current_prob: float):
            if depth >= max_depth or current_prob < 0.01:
                return

            for successor in self.graph.successors(event_name):
                if successor not in visited:
                    edge_weight = self.graph[event_name][successor]['weight']
                    cascade_prob = current_prob * edge_weight

                    if successor in cascade_probs:
                        cascade_probs[successor] = max(cascade_probs[successor], cascade_prob)
                    else:
                        cascade_probs[successor] = cascade_prob

                    visited.add(successor)
                    propagate(successor, depth + 1, cascade_prob)

        propagate(initial_event.value, 0, 1.0)
        return cascade_probs

    def get_event_predecessors(self, event_type: EventType) -> List[EventType]:
        """Get events that can trigger this event"""
        predecessors = []
        for pred in self.graph.predecessors(event_type.value):
            try:
                predecessors.append(EventType(pred))
            except ValueError:
                continue
        return predecessors


class EventForecaster:
    """Main event forecasting system"""

    def __init__(self):
        self.event_history: List[Event] = []
        self.predictions: List[EventPrediction] = []
        self.models: Dict[EventType, ProbabilityModel] = {}
        self.triggers: List[EventTrigger] = []
        self.dependency_graph = EventDependencyGraph()
        self.event_chains: List[EventChain] = []
        self.global_context: Dict[str, Any] = {}

    def initialize_default_models(self):
        """Initialize default probability models for all event types"""
        for event_type in EventType:
            # Start with Poisson models for all event types
            base_rate = self._get_base_event_rate(event_type)
            model = PoissonEventModel(event_type, base_rate)
            self.models[event_type] = model

        # Initialize dependency graph
        self._initialize_dependencies()

    def _get_base_event_rate(self, event_type: EventType) -> float:
        """Get base occurrence rate for event type"""
        rates = {
            EventType.NATURAL_DISASTER: 0.01,
            EventType.POLITICAL_EVENT: 0.05,
            EventType.ECONOMIC_CRISIS: 0.02,
            EventType.TECHNOLOGICAL_BREAKTHROUGH: 0.03,
            EventType.SOCIAL_MOVEMENT: 0.04,
            EventType.MILITARY_CONFLICT: 0.02,
            EventType.PANDEMIC: 0.005,
            EventType.ENVIRONMENTAL_CHANGE: 0.01,
            EventType.DISCOVERY: 0.02,
            EventType.CELEBRATION: 0.08,
            EventType.MARKET_CRASH: 0.03,
            EventType.MARKET_BOOM: 0.05,
            EventType.PLAYER_REBELLION: 0.02,
            EventType.NPC_UPRISING: 0.01,
            EventType.MAGICAL_EVENT: 0.02,
            EventType.ALIEN_ENCOUNTER: 0.001,
            EventType.DIMENSIONAL_RIFT: 0.001
        }
        return rates.get(event_type, 0.01)

    def _initialize_dependencies(self):
        """Initialize event dependency relationships"""
        # Add all event types to graph
        for event_type in EventType:
            self.dependency_graph.add_event(event_type)

        # Add dependencies
        dependencies = [
            (EventType.ECONOMIC_CRISIS, EventType.PLAYER_REBELLION, 0.7),
            (EventType.MILITARY_CONFLICT, EventType.ECONOMIC_CRISIS, 0.6),
            (EventType.NATURAL_DISASTER, EventType.ECONOMIC_CRISIS, 0.5),
            (EventType.TECHNOLOGICAL_BREAKTHROUGH, EventType.MARKET_BOOM, 0.8),
            (EventType.SOCIAL_MOVEMENT, EventType.POLITICAL_EVENT, 0.7),
            (EventType.PANDEMIC, EventType.ECONOMIC_CRISIS, 0.8),
            (EventType.DIMENSIONAL_RIFT, EventType.MAGICAL_EVENT, 0.9),
            (EventType.ALIEN_ENCOUNTER, EventType.TECHNOLOGICAL_BREAKTHROUGH, 0.6),
            (EventType.PLAYER_REBELLION, EventType.POLITICAL_EVENT, 0.5),
            (EventType.NPC_UPRISING, EventType.MILITARY_CONFLICT, 0.6),
        ]

        for source, target, weight in dependencies:
            self.dependency_graph.add_dependency(source, target, weight)

    def add_event(self, event: Event):
        """Add a historical event"""
        self.event_history.append(event)

        # Update models with new data
        self._update_models_with_event(event)

        # Keep history manageable
        if len(self.event_history) > 10000:
            self.event_history = self.event_history[-5000:]

    def add_trigger(self, trigger: EventTrigger):
        """Add an event trigger"""
        self.triggers.append(trigger)

    def update_context(self, context: Dict[str, Any]):
        """Update global context for predictions"""
        self.global_context.update(context)

    async def predict_events(self, time_horizon: int = 168,  # 1 week
                           location: Optional[str] = None,
                           min_probability: float = 0.1) -> List[EventPrediction]:
        """Predict events within time horizon"""
        predictions = []
        current_time = datetime.now()

        # Check active triggers
        active_triggers = self._check_active_triggers()

        for event_type, model in self.models.items():
            try:
                # Build context for this event type
                context = self._build_event_context(event_type, location, active_triggers)

                # Calculate base probability
                base_probability = model.calculate_probability(context)

                # Adjust for dependencies
                adjusted_probability = self._adjust_for_dependencies(event_type, base_probability, context)

                # Apply location modifier
                if location:
                    location_modifier = self._get_location_modifier(event_type, location)
                    adjusted_probability *= location_modifier

                # Only include predictions above threshold
                if adjusted_probability >= min_probability:
                    # Predict timing
                    predicted_time = self._predict_event_timing(event_type, adjusted_probability, time_horizon)

                    prediction = EventPrediction(
                        prediction_id=f"pred_{event_type.value}_{current_time.timestamp()}",
                        event_type=event_type,
                        predicted_timestamp=predicted_time,
                        probability=adjusted_probability,
                        confidence=self._calculate_confidence(event_type, context),
                        location=location or "global",
                        estimated_severity=self._estimate_severity(event_type, context),
                        contributing_factors=self._extract_contributing_factors(context),
                        potential_triggers=self._get_potential_triggers(event_type),
                        time_horizon=time_horizon
                    )

                    predictions.append(prediction)

            except Exception as e:
                logger.error(f"Error predicting {event_type.value}: {e}")

        # Sort by probability
        predictions.sort(key=lambda p: p.probability, reverse=True)

        # Store predictions
        self.predictions.extend(predictions)

        # Generate event chains
        await self._generate_event_chains(predictions)

        return predictions

    async def predict_event_chain(self, trigger_event: EventType,
                                max_length: int = 5) -> Optional[EventChain]:
        """Predict a chain of events starting from a trigger"""
        try:
            # Calculate cascade probabilities
            cascade_probs = self.dependency_graph.calculate_cascade_probability(trigger_event, max_length)

            if not cascade_probs:
                return None

            # Create chain predictions
            chain_predictions = []
            current_time = datetime.now()

            for event_name, prob in cascade_probs.items():
                if prob > 0.1:  # Minimum probability threshold
                    try:
                        event_type = EventType(event_name)
                        context = self._build_event_context(event_type, None, {})

                        prediction = EventPrediction(
                            prediction_id=f"chain_{event_type.value}_{current_time.timestamp()}",
                            event_type=event_type,
                            predicted_timestamp=current_time + timedelta(hours=len(chain_predictions) * 24),
                            probability=prob,
                            confidence=self._calculate_confidence(event_type, context),
                            location="global",
                            estimated_severity=self._estimate_severity(event_type, context),
                            contributing_factors=self._extract_contributing_factors(context),
                            potential_triggers=[trigger_event.value],
                            time_horizon=168,
                            chain_position=len(chain_predictions)
                        )

                        chain_predictions.append(prediction)
                    except ValueError:
                        continue

            if chain_predictions:
                chain = EventChain(
                    chain_id=f"chain_{trigger_event.value}_{current_time.timestamp()}",
                    events=chain_predictions,
                    chain_probability=cascade_probs.get(trigger_event.value, 1.0),
                    trigger_event=trigger_event.value,
                    propagation_model="cascade"
                )

                self.event_chains.append(chain)
                return chain

        except Exception as e:
            logger.error(f"Error predicting event chain: {e}")

        return None

    def get_event_risk_assessment(self, location: Optional[str] = None,
                                time_window: int = 168) -> Dict[str, Any]:
        """Get comprehensive risk assessment"""
        current_time = datetime.now()
        cutoff_time = current_time + timedelta(hours=time_window)

        # Filter relevant predictions
        relevant_predictions = [p for p in self.predictions
                              if p.predicted_timestamp <= cutoff_time and
                              (location is None or p.location == location)]

        # Calculate risk metrics
        risk_assessment = {
            "total_events_predicted": len(relevant_predictions),
            "high_risk_events": 0,
            "moderate_risk_events": 0,
            "low_risk_events": 0,
            "catastrophic_risk_events": 0,
            "event_type_distribution": defaultdict(int),
            "severity_distribution": defaultdict(int),
            "peak_risk_time": None,
            "risk_timeline": [],
            "mitigation_suggestions": []
        }

        peak_risk_time = None
        max_concurrent_risk = 0

        # Analyze predictions
        for pred in relevant_predictions:
            # Risk categorization
            if pred.probability > 0.8:
                risk_assessment["high_risk_events"] += 1
            elif pred.probability > 0.5:
                risk_assessment["moderate_risk_events"] += 1
            else:
                risk_assessment["low_risk_events"] += 1

            if pred.estimated_severity.value >= 6:
                risk_assessment["catastrophic_risk_events"] += 1

            # Distributions
            risk_assessment["event_type_distribution"][pred.event_type.value] += 1
            risk_assessment["severity_distribution"][pred.estimated_severity.name] += 1

            # Timeline analysis
            hour_slot = (pred.predicted_timestamp - current_time).total_seconds() / 3600
            risk_assessment["risk_timeline"].append({
                "time": hour_slot,
                "event_type": pred.event_type.value,
                "probability": pred.probability,
                "severity": pred.estimated_severity.value
            })

            # Find peak risk time
            concurrent_events = sum(1 for p in relevant_predictions
                                  if abs((p.predicted_timestamp - pred.predicted_timestamp).total_seconds()) < 3600)

            if concurrent_events > max_concurrent_risk:
                max_concurrent_risk = concurrent_events
                peak_risk_time = pred.predicted_timestamp

        risk_assessment["peak_risk_time"] = peak_risk_time.isoformat() if peak_risk_time else None

        # Generate mitigation suggestions
        risk_assessment["mitigation_suggestions"] = self._generate_mitigation_suggestions(relevant_predictions)

        return dict(risk_assessment)

    def _check_active_triggers(self) -> List[EventTrigger]:
        """Check which triggers are currently active"""
        active_triggers = []
        for trigger in self.triggers:
            if self._evaluate_trigger_condition(trigger):
                active_triggers.append(trigger)
        return active_triggers

    def _evaluate_trigger_condition(self, trigger: EventTrigger) -> bool:
        """Evaluate if a trigger condition is met"""
        try:
            condition_value = self.global_context.get(trigger.trigger_type, 0)
            return condition_value >= trigger.threshold
        except Exception:
            return False

    def _build_event_context(self, event_type: EventType,
                           location: Optional[str],
                           active_triggers: List[EventTrigger]) -> Dict[str, Any]:
        """Build context for event prediction"""
        context = {
            "time_window": 24,
            "location": location,
            "global_stability": self.global_context.get("stability", 0.5),
            "economic_health": self.global_context.get("economy", 0.5),
            "player_satisfaction": self.global_context.get("satisfaction", 0.5),
            "npc_happiness": self.global_context.get("npc_happiness", 0.5),
            "magical_energy": self.global_context.get("magical_energy", 0.5),
            "technological_level": self.global_context.get("tech_level", 0.5),
            "environmental_health": self.global_context.get("environment", 0.5)
        }

        # Add trigger effects
        rate_adjustment = 1.0
        for trigger in active_triggers:
            if event_type in trigger.affected_events:
                rate_adjustment *= trigger.weight

        context["rate_adjustment"] = rate_adjustment

        # Add historical frequency
        recent_events = [e for e in self.event_history[-100:]
                        if e.event_type == event_type and
                        (datetime.now() - e.timestamp).total_seconds() < 7 * 24 * 3600]
        context["recent_frequency"] = len(recent_events)

        return context

    def _adjust_for_dependencies(self, event_type: EventType,
                               base_probability: float,
                               context: Dict[str, Any]) -> float:
        """Adjust probability based on event dependencies"""
        # Get predecessor events
        predecessors = self.dependency_graph.get_event_predecessors(event_type)

        if not predecessors:
            return base_probability

        # Check if any predecessor events are likely
        dependency_factor = 1.0
        for pred_event in predecessors:
            if pred_event in self.models:
                pred_context = self._build_event_context(pred_event, None, [])
                pred_probability = self.models[pred_event].calculate_probability(pred_context)

                # Apply dependency weight
                dependency_key = (pred_event.value, event_type.value)
                weight = self.dependency_graph.dependency_weights.get(dependency_key, 0.5)

                dependency_factor += pred_probability * weight

        return min(1.0, base_probability * dependency_factor)

    def _get_location_modifier(self, event_type: EventType, location: str) -> float:
        """Get location-specific probability modifier"""
        # Simplified location modifiers
        location_modifiers = {
            "city": {
                EventType.SOCIAL_MOVEMENT: 1.5,
                EventType.POLITICAL_EVENT: 1.3,
                EventType.ECONOMIC_CRISIS: 1.2,
                EventType.CELEBRATION: 1.4
            },
            "wilderness": {
                EventType.NATURAL_DISASTER: 1.5,
                EventType.ENVIRONMENTAL_CHANGE: 1.3,
                EventType.DISCOVERY: 1.4,
                EventType.MAGICAL_EVENT: 1.2
            },
            "military_zone": {
                EventType.MILITARY_CONFLICT: 2.0,
                EventType.NPC_UPRISING: 1.5,
                EventType.PLAYER_REBELLION: 1.3
            }
        }

        return location_modifiers.get(location, {}).get(event_type, 1.0)

    def _predict_event_timing(self, event_type: EventType, probability: float,
                            time_horizon: int) -> datetime:
        """Predict when event is most likely to occur"""
        # Simplified timing prediction based on probability
        if probability > 0.8:
            # High probability - sooner
            expected_hours = np.random.exponential(time_horizon * 0.2)
        elif probability > 0.5:
            # Medium probability - middle of horizon
            expected_hours = time_horizon * 0.5 + np.random.normal(0, time_horizon * 0.1)
        else:
            # Low probability - later in horizon
            expected_hours = time_horizon * 0.8 + np.random.exponential(time_horizon * 0.2)

        expected_hours = max(1, min(time_horizon, expected_hours))
        return datetime.now() + timedelta(hours=expected_hours)

    def _calculate_confidence(self, event_type: EventType, context: Dict[str, Any]) -> float:
        """Calculate confidence in prediction"""
        # Base confidence on model type and data availability
        model = self.models.get(event_type)
        if not model:
            return 0.3

        if isinstance(model, PoissonEventModel):
            base_confidence = 0.6
        elif isinstance(model, BayesianEventModel):
            base_confidence = 0.7
        elif isinstance(model, MLEventModel) and model.is_trained:
            base_confidence = 0.8
        else:
            base_confidence = 0.5

        # Adjust based on context completeness
        context_completeness = sum(1 for v in context.values() if v is not None) / len(context)
        confidence = base_confidence * (0.5 + 0.5 * context_completeness)

        return max(0.1, min(1.0, confidence))

    def _estimate_severity(self, event_type: EventType, context: Dict[str, Any]) -> EventSeverity:
        """Estimate event severity based on context"""
        # Base severity for event type
        base_severities = {
            EventType.NATURAL_DISASTER: EventSeverity.MAJOR,
            EventType.POLITICAL_EVENT: EventSeverity.MODERATE,
            EventType.ECONOMIC_CRISIS: EventSeverity.MAJOR,
            EventType.TECHNOLOGICAL_BREAKTHROUGH: EventSeverity.MODERATE,
            EventType.SOCIAL_MOVEMENT: EventSeverity.MODERATE,
            EventType.MILITARY_CONFLICT: EventSeverity.SEVERE,
            EventType.PANDEMIC: EventSeverity.SEVERE,
            EventType.ENVIRONMENTAL_CHANGE: EventSeverity.MAJOR,
            EventType.DISCOVERY: EventSeverity.MINOR,
            EventType.CELEBRATION: EventSeverity.TRIVIAL,
            EventType.MARKET_CRASH: EventSeverity.MAJOR,
            EventType.MARKET_BOOM: EventSeverity.MINOR,
            EventType.PLAYER_REBELLION: EventSeverity.MAJOR,
            EventType.NPC_UPRISING: EventSeverity.MODERATE,
            EventType.MAGICAL_EVENT: EventSeverity.MODERATE,
            EventType.ALIEN_ENCOUNTER: EventSeverity.SEVERE,
            EventType.DIMENSIONAL_RIFT: EventSeverity.CATASTROPHIC
        }

        base_severity = base_severities.get(event_type, EventSeverity.MODERATE)

        # Adjust based on context
        instability = 1.0 - context.get("global_stability", 0.5)
        if instability > 0.7:
            # Increase severity in unstable conditions
            severity_value = min(7, base_severity.value + 1)
        elif instability < 0.3:
            # Decrease severity in stable conditions
            severity_value = max(1, base_severity.value - 1)
        else:
            severity_value = base_severity.value

        return EventSeverity(severity_value)

    def _extract_contributing_factors(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract factors contributing to the prediction"""
        contributing_factors = {}
        for key, value in context.items():
            if isinstance(value, (int, float)) and key != "rate_adjustment":
                contributing_factors[key] = abs(value - 0.5) * 2  # Normalize to 0-1

        return contributing_factors

    def _get_potential_triggers(self, event_type: EventType) -> List[str]:
        """Get potential triggers for this event type"""
        potential_triggers = []
        for trigger in self.triggers:
            if event_type in trigger.affected_events:
                potential_triggers.append(trigger.trigger_type)
        return potential_triggers

    async def _generate_event_chains(self, predictions: List[EventPrediction]):
        """Generate event chains from predictions"""
        # Find high-probability events that could trigger chains
        high_prob_predictions = [p for p in predictions if p.probability > 0.7]

        for pred in high_prob_predictions[:5]:  # Limit to prevent explosion
            chain = await self.predict_event_chain(pred.event_type, max_length=3)
            if chain:
                self.event_chains.append(chain)

    def _generate_mitigation_suggestions(self, predictions: List[EventPrediction]) -> List[str]:
        """Generate suggestions to mitigate high-risk events"""
        suggestions = []
        high_risk_events = [p for p in predictions if p.probability > 0.7 and p.estimated_severity.value >= 4]

        if not high_risk_events:
            return ["Current risk levels are manageable"]

        for pred in high_risk_events[:3]:  # Top 3 high-risk events
            if pred.event_type == EventType.ECONOMIC_CRISIS:
                suggestions.append("Increase economic stimulus packages and monitor market stability")
            elif pred.event_type == EventType.PLAYER_REBELLION:
                suggestions.append("Engage with player community and address grievances proactively")
            elif pred.event_type == EventType.NATURAL_DISASTER:
                suggestions.append("Prepare emergency response systems and evacuation plans")
            elif pred.event_type == EventType.MILITARY_CONFLICT:
                suggestions.append("Strengthen diplomatic efforts and peacekeeping forces")
            elif pred.event_type == EventType.PANDEMIC:
                suggestions.append("Implement health monitoring and quarantine protocols")

        if len(suggestions) == 0:
            suggestions.append("Monitor situation closely and prepare contingency plans")

        return suggestions

    def _update_models_with_event(self, event: Event):
        """Update probability models with new event data"""
        # Update Poisson models
        if event.event_type in self.models:
            model = self.models[event.event_type]
            if isinstance(model, PoissonEventModel):
                model.update_parameters({
                    "observed_events": 1,
                    "time_period": 24
                })

        # Update Bayesian models
        for event_type in EventType:
            if event_type in self.models:
                model = self.models[event_type]
                if isinstance(model, BayesianEventModel):
                    success = 1 if event.event_type == event_type else 0
                    failure = 1 - success
                    model.update_parameters({
                        "success_count": success,
                        "failure_count": failure
                    })


# Singleton instance
_event_forecaster = None

def get_event_forecaster() -> EventForecaster:
    """Get the singleton event forecaster instance"""
    global _event_forecaster
    if _event_forecaster is None:
        _event_forecaster = EventForecaster()
        _event_forecaster.initialize_default_models()
    return _event_forecaster


async def main():
    """Example usage of the event forecaster"""
    forecaster = get_event_forecaster()

    # Update global context
    forecaster.update_context({
        "stability": 0.3,  # Low stability
        "economy": 0.4,    # Struggling economy
        "satisfaction": 0.6,
        "magical_energy": 0.8  # High magical activity
    })

    # Add some triggers
    rebellion_trigger = EventTrigger(
        trigger_id="eco_crisis_trigger",
        trigger_type="economic_health",
        condition="economic_health < 0.3",
        threshold=0.3,
        affected_events=[EventType.PLAYER_REBELLION, EventType.ECONOMIC_CRISIS],
        weight=1.5
    )
    forecaster.add_trigger(rebellion_trigger)

    # Add historical events
    historical_events = [
        Event(
            event_id="hist_001",
            event_type=EventType.ECONOMIC_CRISIS,
            severity=EventSeverity.MAJOR,
            timestamp=datetime.now() - timedelta(days=10),
            location="capital_city",
            description="Market crash due to speculation",
            duration=48,
            impact_radius=100,
            participants=["traders", "merchants"],
            triggers=["market_speculation"],
            consequences=["unemployment", "civil_unrest"]
        )
    ]

    for event in historical_events:
        forecaster.add_event(event)

    print("Predicting future events...")
    predictions = await forecaster.predict_events(time_horizon=168, min_probability=0.1)

    print(f"\nPredicted {len(predictions)} events in the next week:")
    for pred in predictions[:10]:  # Show top 10
        print(f"{pred.event_type.value}: {pred.probability:.2f} probability, "
              f"severity {pred.estimated_severity.name}, "
              f"at {pred.predicted_timestamp.strftime('%Y-%m-%d %H:%M')}")

    # Event chain prediction
    print("\nPredicting event chains...")
    chain = await forecaster.predict_event_chain(EventType.ECONOMIC_CRISIS)
    if chain:
        print(f"Event chain starting with {chain.trigger_event}:")
        for event_pred in chain.events:
            print(f"  -> {event_pred.event_type.value} (prob: {event_pred.probability:.2f})")

    # Risk assessment
    print("\nRisk Assessment:")
    risk_assessment = forecaster.get_event_risk_assessment()
    print(f"High risk events: {risk_assessment['high_risk_events']}")
    print(f"Catastrophic risk events: {risk_assessment['catastrophic_risk_events']}")
    print(f"Peak risk time: {risk_assessment['peak_risk_time']}")
    print(f"Mitigation suggestions: {risk_assessment['mitigation_suggestions']}")


if __name__ == "__main__":
    asyncio.run(main())