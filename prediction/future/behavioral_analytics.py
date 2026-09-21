#!/usr/bin/env python3
"""
Behavioral Analytics - Player behavior prediction and modeling system
Analyzes player actions, predicts future behavior, and models player preferences
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque, Counter
import logging

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, classification_report, silhouette_score
    from sklearn.model_selection import train_test_split
    from scipy import stats
    from scipy.spatial.distance import cosine
except ImportError:
    print("Warning: scikit-learn/scipy not available. Using simplified behavioral analysis")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerType(Enum):
    """Player behavioral types"""
    CASUAL = "casual"
    HARDCORE = "hardcore"
    SOCIAL = "social"
    EXPLORER = "explorer"
    ACHIEVER = "achiever"
    COMPETITIVE = "competitive"
    CREATIVE = "creative"
    ECONOMIC = "economic"
    STRATEGIC = "strategic"
    NEWCOMER = "newcomer"


class BehaviorPattern(Enum):
    """Types of behavior patterns"""
    DAILY_ROUTINE = "daily_routine"
    WEEKLY_PATTERN = "weekly_pattern"
    SESSION_LENGTH = "session_length"
    PEAK_HOURS = "peak_hours"
    ACTIVITY_SWITCH = "activity_switch"
    SOCIAL_INTERACTION = "social_interaction"
    PROGRESSION_PATTERN = "progression_pattern"
    SPENDING_PATTERN = "spending_pattern"
    RETENTION_RISK = "retention_risk"
    CHURN_PREDICTION = "churn_prediction"


@dataclass
class PlayerAction:
    """Represents a single player action"""
    player_id: str
    action_type: str
    timestamp: datetime
    location: Optional[str] = None
    duration: Optional[float] = None
    value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerProfile:
    """Comprehensive player profile"""
    player_id: str
    player_type: PlayerType
    created_at: datetime
    last_active: datetime
    total_playtime: float
    level: int
    achievements: List[str]
    preferences: Dict[str, float]
    behavior_patterns: Dict[str, Any]
    social_connections: List[str]
    economic_profile: Dict[str, float]
    risk_factors: Dict[str, float]
    accuracy_score: float = 0.0


@dataclass
class BehaviorPrediction:
    """Prediction of player behavior"""
    player_id: str
    prediction_type: BehaviorPattern
    timestamp: datetime
    prediction_horizon: int  # hours
    predicted_behavior: str
    confidence: float
    probability_distribution: Dict[str, float]
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerSegment:
    """Player segment for targeted analytics"""
    segment_id: str
    name: str
    player_ids: Set[str]
    characteristics: Dict[str, Any]
    size: int
    avg_metrics: Dict[str, float]


class BehaviorFeatureExtractor:
    """Extracts features from player behavior data"""

    def __init__(self):
        self.feature_names = [
            'session_frequency', 'avg_session_length', 'total_playtime',
            'actions_per_session', 'preferred_time', 'social_engagement',
            'progression_rate', 'spending_rate', 'achievement_rate',
            'exploration_index', 'competitiveness', 'consistency_score'
        ]

    def extract_features(self, player_id: str, actions: List[PlayerAction],
                        time_window: int = 30) -> np.ndarray:
        """Extract behavioral features for a player"""
        if not actions:
            return np.zeros(len(self.feature_names))

        # Filter actions within time window
        cutoff_time = datetime.now() - timedelta(days=time_window)
        recent_actions = [a for a in actions if a.timestamp > cutoff_time]

        if not recent_actions:
            return np.zeros(len(self.feature_names))

        features = []

        # Session frequency (sessions per day)
        sessions = self._group_by_session(recent_actions)
        session_frequency = len(sessions) / time_window
        features.append(session_frequency)

        # Average session length
        session_lengths = [len(s) for s in sessions]
        avg_session_length = np.mean(session_lengths) if session_lengths else 0
        features.append(avg_session_length)

        # Total playtime (in hours)
        total_playtime = sum(a.duration or 0 for a in recent_actions) / 3600
        features.append(total_playtime)

        # Actions per session
        actions_per_session = len(recent_actions) / len(sessions) if sessions else 0
        features.append(actions_per_session)

        # Preferred time of day
        hours = [a.timestamp.hour for a in recent_actions]
        if hours:
            hour_counts = Counter(hours)
            preferred_hour = max(hour_counts, key=hour_counts.get)
            features.append(preferred_hour / 24)  # Normalize to 0-1
        else:
            features.append(0.5)

        # Social engagement
        social_actions = [a for a in recent_actions if 'social' in a.action_type.lower()]
        social_engagement = len(social_actions) / len(recent_actions)
        features.append(social_engagement)

        # Progression rate (level gains per day)
        progression_actions = [a for a in recent_actions if 'level' in a.action_type.lower() or 'progress' in a.action_type.lower()]
        progression_rate = len(progression_actions) / time_window
        features.append(progression_rate)

        # Spending rate
        spending_actions = [a for a in recent_actions if a.value and a.value > 0]
        spending_rate = sum(a.value or 0 for a in spending_actions) / time_window
        features.append(spending_rate)

        # Achievement rate
        achievement_actions = [a for a in recent_actions if 'achievement' in a.action_type.lower()]
        achievement_rate = len(achievement_actions) / time_window
        features.append(achievement_rate)

        # Exploration index (variety of locations)
        locations = set(a.location for a in recent_actions if a.location)
        exploration_index = len(locations) / 100  # Normalize
        features.append(exploration_index)

        # Competitiveness (competitive actions)
        competitive_actions = [a for a in recent_actions if 'combat' in a.action_type.lower() or 'pvp' in a.action_type.lower()]
        competitiveness = len(competitive_actions) / len(recent_actions)
        features.append(competitiveness)

        # Consistency score (how regular the activity is)
        if len(recent_actions) > 1:
            action_intervals = [(recent_actions[i+1].timestamp - recent_actions[i].timestamp).total_seconds()
                               for i in range(len(recent_actions)-1)]
            consistency = 1 - (np.std(action_intervals) / (np.mean(action_intervals) + 1e-6))
            features.append(max(0, min(1, consistency)))
        else:
            features.append(0)

        return np.array(features)

    def _group_by_session(self, actions: List[PlayerAction], session_gap: int = 30) -> List[List[PlayerAction]]:
        """Group actions into sessions based on time gaps"""
        if not actions:
            return []

        actions_sorted = sorted(actions, key=lambda a: a.timestamp)
        sessions = []
        current_session = [actions_sorted[0]]

        for action in actions_sorted[1:]:
            time_diff = (action.timestamp - current_session[-1].timestamp).total_seconds() / 60
            if time_diff <= session_gap:
                current_session.append(action)
            else:
                sessions.append(current_session)
                current_session = [action]

        if current_session:
            sessions.append(current_session)

        return sessions


class PlayerClassifier:
    """Classifies players into behavioral types"""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.class_names = [ptype.value for ptype in PlayerType]

    def train(self, features: np.ndarray, labels: List[PlayerType]) -> bool:
        """Train the player classifier"""
        try:
            if len(features) != len(labels) or len(features) < 10:
                logger.warning("Insufficient training data")
                return False

            # Encode labels
            label_values = [ptype.value for ptype in labels]
            y_encoded = self.label_encoder.fit_transform(label_values)

            # Scale features
            X_scaled = self.scaler.fit_transform(features)

            # Train model
            self.model.fit(X_scaled, y_encoded)
            self.is_trained = True

            logger.info(f"Player classifier trained with {len(features)} samples")
            return True

        except Exception as e:
            logger.error(f"Error training player classifier: {e}")
            return False

    def predict(self, features: np.ndarray) -> Tuple[PlayerType, float]:
        """Predict player type with confidence"""
        if not self.is_trained:
            raise ValueError("Model not trained")

        try:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]

            predicted_type = PlayerType(self.label_encoder.inverse_transform([prediction])[0])
            confidence = np.max(probabilities)

            return predicted_type, confidence

        except Exception as e:
            logger.error(f"Error predicting player type: {e}")
            return PlayerType.CASUAL, 0.5


class ChurnPredictor:
    """Predicts player churn risk"""

    def __init__(self):
        self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_importance = {}

    def train(self, features: np.ndarray, churn_labels: np.ndarray) -> bool:
        """Train churn prediction model"""
        try:
            if len(features) != len(churn_labels) or len(features) < 50:
                logger.warning("Insufficient training data for churn prediction")
                return False

            # Scale features
            X_scaled = self.scaler.fit_transform(features)

            # Train model
            self.model.fit(X_scaled, churn_labels)

            # Store feature importance
            feature_names = ['recency', 'frequency', 'duration', 'engagement',
                           'social_factor', 'progression_stagnation', 'spending_decline',
                           'session_irregularity', 'achievement_gap', 'warning_signs']

            self.feature_importance = dict(zip(feature_names, self.model.feature_importances_))
            self.is_trained = True

            logger.info("Churn predictor trained successfully")
            return True

        except Exception as e:
            logger.error(f"Error training churn predictor: {e}")
            return False

    def predict_churn_risk(self, features: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Predict churn probability and contributing factors"""
        if not self.is_trained:
            raise ValueError("Model not trained")

        try:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            churn_probability = self.model.predict_proba(features_scaled)[0][1]

            # Get contributing factors (simplified)
            contributing_factors = {
                "decreased_activity": max(0, features[0] - 0.5),  # recency
                "low_engagement": max(0, 0.5 - features[3]),      # engagement
                "social_isolation": max(0, 0.5 - features[4]),    # social_factor
                "stagnation": max(0, features[5] - 0.5),         # progression_stagnation
            }

            return churn_probability, contributing_factors

        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            return 0.5, {}

    def extract_churn_features(self, player_id: str, actions: List[PlayerAction],
                             current_level: int, last_achievement: datetime) -> np.ndarray:
        """Extract features specifically for churn prediction"""
        if not actions:
            return np.zeros(10)

        # Recent activity (hours since last action)
        last_action = max(actions, key=lambda a: a.timestamp)
        recency = (datetime.now() - last_action.timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - recency / 168)  # Normalize to week

        # Frequency (actions per day in last week)
        week_ago = datetime.now() - timedelta(days=7)
        recent_actions = [a for a in actions if a.timestamp > week_ago]
        frequency = len(recent_actions) / 7

        # Total playtime
        total_playtime = sum(a.duration or 0 for a in recent_actions) / 3600

        # Engagement score (combination of factors)
        engagement = min(1, (frequency + total_playtime / 10) / 2)

        # Social factor (social actions ratio)
        social_actions = [a for a in recent_actions if 'social' in a.action_type.lower()]
        social_factor = len(social_actions) / len(recent_actions) if recent_actions else 0

        # Progression stagnation (time since last level/achievement)
        time_since_achievement = (datetime.now() - last_achievement).total_seconds() / (24 * 3600)
        progression_stagnation = min(1, time_since_achievement / 30)

        # Spending decline (compared to historical average)
        spending_actions = [a for a in recent_actions if a.value and a.value > 0]
        current_spending = sum(a.value for a in spending_actions)
        spending_decline = 0.5  # Placeholder - would compare to historical

        # Session irregularity
        sessions = self._group_sessions_by_day(recent_actions)
        session_counts = [len(day_sessions) for day_sessions in sessions.values()]
        session_irregularity = np.std(session_counts) / (np.mean(session_counts) + 1e-6) if session_counts else 0

        # Achievement gap
        achievement_gap = time_since_achievement / 30

        # Warning signs (negative patterns)
        warning_actions = [a for a in recent_actions if 'error' in a.action_type.lower() or 'frustration' in a.action_type.lower()]
        warning_signs = len(warning_actions) / len(recent_actions) if recent_actions else 0

        return np.array([recency_score, frequency, total_playtime, engagement,
                        social_factor, progression_stagnation, spending_decline,
                        session_irregularity, achievement_gap, warning_signs])

    def _group_sessions_by_day(self, actions: List[PlayerAction]) -> Dict[str, List[PlayerAction]]:
        """Group actions by day for session analysis"""
        daily_sessions = defaultdict(list)
        for action in actions:
            day_key = action.timestamp.date().isoformat()
            daily_sessions[day_key].append(action)
        return daily_sessions


class PlayerSegmenter:
    """Segments players into behavioral groups"""

    def __init__(self):
        self.kmeans_model = KMeans(n_clusters=8, random_state=42)
        self.scaler = StandardScaler()
        self.segment_profiles: Dict[int, Dict[str, Any]] = {}
        self.is_fitted = False

    def fit(self, features: np.ndarray, player_ids: List[str]) -> bool:
        """Fit the segmentation model"""
        try:
            if len(features) < 20:
                logger.warning("Insufficient data for segmentation")
                return False

            # Scale features
            X_scaled = self.scaler.fit_transform(features)

            # Fit K-means
            cluster_labels = self.kmeans_model.fit_predict(X_scaled)

            # Create segment profiles
            self.segment_profiles = {}
            for cluster_id in range(self.kmeans_model.n_clusters):
                mask = cluster_labels == cluster_id
                segment_players = [player_ids[i] for i in range(len(player_ids)) if mask[i]]
                segment_features = features[mask]

                self.segment_profiles[cluster_id] = {
                    'size': len(segment_players),
                    'players': segment_players,
                    'centroid': self.kmeans_model.cluster_centers_[cluster_id],
                    'characteristics': self._describe_segment(segment_features)
                }

            self.is_fitted = True
            logger.info(f"Player segmentation completed with {self.kmeans_model.n_clusters} segments")
            return True

        except Exception as e:
            logger.error(f"Error fitting segmentation model: {e}")
            return False

    def predict_segment(self, features: np.ndarray) -> int:
        """Predict segment for a player"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        return self.kmeans_model.predict(features_scaled)[0]

    def _describe_segment(self, features: np.ndarray) -> Dict[str, float]:
        """Describe segment characteristics"""
        feature_names = ['session_frequency', 'avg_session_length', 'total_playtime',
                        'actions_per_session', 'preferred_time', 'social_engagement',
                        'progression_rate', 'spending_rate', 'achievement_rate',
                        'exploration_index', 'competitiveness', 'consistency_score']

        characteristics = {}
        for i, name in enumerate(feature_names):
            if i < features.shape[1]:
                characteristics[name] = float(np.mean(features[:, i]))

        return characteristics


class BehavioralAnalytics:
    """Main behavioral analytics system"""

    def __init__(self):
        self.player_actions: Dict[str, List[PlayerAction]] = defaultdict(list)
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.feature_extractor = BehaviorFeatureExtractor()
        self.classifier = PlayerClassifier()
        self.churn_predictor = ChurnPredictor()
        self.segmenter = PlayerSegmenter()
        self.predictions: List[BehaviorPrediction] = []
        self.segments: Dict[str, PlayerSegment] = {}

    def add_player_action(self, action: PlayerAction):
        """Add a new player action"""
        self.player_actions[action.player_id].append(action)

        # Keep only recent actions (last 1000 per player)
        if len(self.player_actions[action.player_id]) > 1000:
            self.player_actions[action.player_id] = self.player_actions[action.player_id][-1000:]

    async def create_player_profile(self, player_id: str,
                                  created_at: datetime,
                                  current_level: int = 1,
                                  last_achievement: Optional[datetime] = None) -> PlayerProfile:
        """Create or update a player profile"""
        actions = self.player_actions.get(player_id, [])

        # Extract features
        features = self.feature_extractor.extract_features(player_id, actions)

        # Predict player type
        if self.classifier.is_trained:
            player_type, confidence = self.classifier.predict(features)
        else:
            player_type = PlayerType.NEWCOMER
            confidence = 0.5

        # Calculate behavioral patterns
        behavior_patterns = self._analyze_behavior_patterns(actions)

        # Calculate risk factors
        churn_features = self.churn_predictor.extract_churn_features(
            player_id, actions, current_level,
            last_achievement or datetime.now() - timedelta(days=30)
        )

        if self.churn_predictor.is_trained:
            churn_risk, risk_factors = self.churn_predictor.predict_churn_risk(churn_features)
        else:
            churn_risk = 0.1  # Default low risk
            risk_factors = {}

        # Create profile
        profile = PlayerProfile(
            player_id=player_id,
            player_type=player_type,
            created_at=created_at,
            last_active=datetime.now(),
            total_playtime=sum(a.duration or 0 for a in actions) / 3600,
            level=current_level,
            achievements=[],  # Would be populated from game data
            preferences=self._extract_preferences(actions),
            behavior_patterns=behavior_patterns,
            social_connections=self._extract_social_connections(actions),
            economic_profile=self._extract_economic_profile(actions),
            risk_factors={"churn_risk": churn_risk, **risk_factors},
            accuracy_score=confidence
        )

        self.player_profiles[player_id] = profile
        return profile

    async def predict_player_behavior(self, player_id: str,
                                    prediction_type: BehaviorPattern,
                                    horizon: int = 24) -> Optional[BehaviorPrediction]:
        """Predict future player behavior"""
        if player_id not in self.player_actions:
            return None

        actions = self.player_actions[player_id]
        if not actions:
            return None

        try:
            # Extract features
            features = self.feature_extractor.extract_features(player_id, actions)

            # Make prediction based on type
            if prediction_type == BehaviorPattern.SESSION_LENGTH:
                prediction, confidence = self._predict_session_length(features)
            elif prediction_type == BehaviorPattern.RETENTION_RISK:
                prediction, confidence = self._predict_retention(features, actions)
            elif prediction_type == BehaviorPattern.CHURN_PREDICTION:
                prediction, confidence = self._predict_churn(features, actions)
            elif prediction_type == BehaviorPattern.PEAK_HOURS:
                prediction, confidence = self._predict_peak_hours(actions)
            else:
                prediction, confidence = "unknown", 0.5

            behavior_prediction = BehaviorPrediction(
                player_id=player_id,
                prediction_type=prediction_type,
                timestamp=datetime.now(),
                prediction_horizon=horizon,
                predicted_behavior=prediction,
                confidence=confidence,
                probability_distribution=self._calculate_probability_distribution(features),
                context={"features": features.tolist(), "recent_actions": len(actions[-10:])}
            )

            self.predictions.append(behavior_prediction)
            return behavior_prediction

        except Exception as e:
            logger.error(f"Error predicting behavior for {player_id}: {e}")
            return None

    def segment_players(self) -> Dict[str, PlayerSegment]:
        """Segment all players into behavioral groups"""
        if not self.player_profiles:
            return {}

        try:
            # Extract features for all players
            player_ids = list(self.player_profiles.keys())
            all_features = []

            for player_id in player_ids:
                actions = self.player_actions.get(player_id, [])
                features = self.feature_extractor.extract_features(player_id, actions)
                all_features.append(features)

            features_array = np.array(all_features)

            # Fit segmentation model
            if self.segmenter.fit(features_array, player_ids):
                # Create segment objects
                self.segments = {}
                for segment_id, profile in self.segmenter.segment_profiles.items():
                    segment = PlayerSegment(
                        segment_id=f"segment_{segment_id}",
                        name=f"Player Group {segment_id + 1}",
                        player_ids=set(profile['players']),
                        characteristics=profile['characteristics'],
                        size=profile['size'],
                        avg_metrics=profile['characteristics']
                    )
                    self.segments[segment.segment_id] = segment

                logger.info(f"Created {len(self.segments)} player segments")
                return self.segments

        except Exception as e:
            logger.error(f"Error segmenting players: {e}")

        return {}

    def get_player_insights(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive insights for a player"""
        if player_id not in self.player_profiles:
            return {}

        profile = self.player_profiles[player_id]
        actions = self.player_actions.get(player_id, [])

        insights = {
            "player_type": profile.player_type.value,
            "accuracy_score": profile.accuracy_score,
            "total_playtime": profile.total_playtime,
            "last_active": profile.last_active.isoformat(),
            "risk_factors": profile.risk_factors,
            "behavior_patterns": profile.behavior_patterns,
            "recent_predictions": [
                {
                    "type": p.prediction_type.value,
                    "prediction": p.predicted_behavior,
                    "confidence": p.confidence,
                    "timestamp": p.timestamp.isoformat()
                }
                for p in self.predictions[-5:] if p.player_id == player_id
            ]
        }

        # Add segment information if available
        if self.segments:
            features = self.feature_extractor.extract_features(player_id, actions)
            segment_id = self.segmenter.predict_segment(features)
            if segment_id in self.segmenter.segment_profiles:
                insights["segment"] = f"segment_{segment_id}"
                insights["segment_characteristics"] = self.segmenter.segment_profiles[segment_id]["characteristics"]

        return insights

    def _analyze_behavior_patterns(self, actions: List[PlayerAction]) -> Dict[str, Any]:
        """Analyze behavioral patterns from actions"""
        if not actions:
            return {}

        patterns = {}

        # Time-based patterns
        hours = [a.timestamp.hour for a in actions]
        if hours:
            hour_counts = Counter(hours)
            patterns["most_active_hour"] = max(hour_counts, key=hour_counts.get)
            patterns["activity_distribution"] = dict(hour_counts)

        # Session patterns
        sessions = self._group_sessions(actions)
        if sessions:
            session_lengths = [len(s) for s in sessions]
            patterns["avg_session_length"] = np.mean(session_lengths)
            patterns["session_frequency"] = len(sessions) / 30  # Assuming 30-day window

        # Action type patterns
        action_types = [a.action_type for a in actions]
        type_counts = Counter(action_types)
        patterns["action_preferences"] = dict(type_counts.most_common(5))

        return patterns

    def _predict_session_length(self, features: np.ndarray) -> Tuple[str, float]:
        """Predict next session length"""
        # Simplified prediction based on historical patterns
        avg_session_length = features[1]  # Average session length feature
        confidence = 0.7

        if avg_session_length > 50:
            return "long_session", confidence
        elif avg_session_length > 20:
            return "medium_session", confidence
        else:
            return "short_session", confidence

    def _predict_retention(self, features: np.ndarray, actions: List[PlayerAction]) -> Tuple[str, float]:
        """Predict player retention"""
        # Use multiple features for retention prediction
        engagement_score = features[3]  # Engagement feature
        social_factor = features[4]     # Social engagement
        consistency = features[11]      # Consistency score

        retention_score = (engagement_score + social_factor + consistency) / 3

        if retention_score > 0.7:
            return "high_retention", retention_score
        elif retention_score > 0.4:
            return "medium_retention", retention_score
        else:
            return "low_retention", retention_score

    def _predict_churn(self, features: np.ndarray, actions: List[PlayerAction]) -> Tuple[str, float]:
        """Predict churn probability"""
        # Use churn predictor if available
        if self.churn_predictor.is_trained:
            churn_features = self.churn_predictor.extract_churn_features(
                "unknown", actions, 1, datetime.now() - timedelta(days=30)
            )
            churn_prob, _ = self.churn_predictor.predict_churn_risk(churn_features)

            if churn_prob > 0.7:
                return "high_churn_risk", churn_prob
            elif churn_prob > 0.3:
                return "medium_churn_risk", churn_prob
            else:
                return "low_churn_risk", 1 - churn_prob

        return "unknown", 0.5

    def _predict_peak_hours(self, actions: List[PlayerAction]) -> Tuple[str, float]:
        """Predict player's peak activity hours"""
        hours = [a.timestamp.hour for a in actions[-50:]]  # Last 50 actions
        if hours:
            hour_counts = Counter(hours)
            peak_hour = max(hour_counts, key=hour_counts.get)
            confidence = hour_counts[peak_hour] / len(hours)
            return f"peak_hour_{peak_hour}", confidence

        return "peak_hour_unknown", 0.5

    def _calculate_probability_distribution(self, features: np.ndarray) -> Dict[str, float]:
        """Calculate probability distribution for different behaviors"""
        # Simplified probability distribution
        return {
            "active": features[3],  # Engagement score
            "social": features[4],  # Social factor
            "competitive": features[9],  # Competitiveness
            "exploratory": features[8]   # Exploration index
        }

    def _extract_preferences(self, actions: List[PlayerAction]) -> Dict[str, float]:
        """Extract player preferences from actions"""
        preferences = defaultdict(int)
        total_actions = len(actions)

        for action in actions:
            preferences[action.action_type] += 1

        # Normalize to 0-1
        for key in preferences:
            preferences[key] /= total_actions

        return dict(preferences)

    def _extract_social_connections(self, actions: List[PlayerAction]) -> List[str]:
        """Extract social connections from actions"""
        connections = set()
        for action in actions:
            if 'with' in action.metadata:
                connections.add(action.metadata['with'])
        return list(connections)

    def _extract_economic_profile(self, actions: List[PlayerAction]) -> Dict[str, float]:
        """Extract economic behavior profile"""
        spending_actions = [a for a in actions if a.value and a.value > 0]
        earning_actions = [a for a in actions if a.value and a.value < 0]

        total_spent = sum(a.value for a in spending_actions)
        total_earned = abs(sum(a.value for a in earning_actions))

        return {
            "total_spent": total_spent,
            "total_earned": total_earned,
            "net_balance": total_earned - total_spent,
            "spending_frequency": len(spending_actions),
            "earning_frequency": len(earning_actions)
        }

    def _group_sessions(self, actions: List[PlayerAction], gap_minutes: int = 30) -> List[List[PlayerAction]]:
        """Group actions into sessions"""
        if not actions:
            return []

        actions_sorted = sorted(actions, key=lambda a: a.timestamp)
        sessions = []
        current_session = [actions_sorted[0]]

        for action in actions_sorted[1:]:
            time_diff = (action.timestamp - current_session[-1].timestamp).total_seconds() / 60
            if time_diff <= gap_minutes:
                current_session.append(action)
            else:
                sessions.append(current_session)
                current_session = [action]

        if current_session:
            sessions.append(current_session)

        return sessions


# Singleton instance
_behavioral_analytics = None

def get_behavioral_analytics() -> BehavioralAnalytics:
    """Get the singleton behavioral analytics instance"""
    global _behavioral_analytics
    if _behavioral_analytics is None:
        _behavioral_analytics = BehavioralAnalytics()
    return _behavioral_analytics


async def main():
    """Example usage of behavioral analytics"""
    analytics = get_behavioral_analytics()

    # Generate sample player actions
    player_id = "player_123"
    base_time = datetime.now() - timedelta(days=30)

    for day in range(30):
        for hour in range(24):
            if np.random.random() < 0.3:  # 30% chance of activity each hour
                action = PlayerAction(
                    player_id=player_id,
                    action_type=np.random.choice(["login", "quest", "social", "combat", "explore"]),
                    timestamp=base_time + timedelta(days=day, hours=hour),
                    location=np.random.choice(["forest", "city", "dungeon", "market"]),
                    duration=np.random.uniform(10, 120),
                    value=np.random.uniform(-10, 50) if np.random.random() < 0.2 else 0
                )
                analytics.add_player_action(action)

    print(f"Generated {len(analytics.player_actions[player_id])} actions for {player_id}")

    # Create player profile
    profile = await analytics.create_player_profile(
        player_id, base_time, current_level=15,
        last_achievement=datetime.now() - timedelta(days=5)
    )

    print(f"\nPlayer Profile:")
    print(f"  Type: {profile.player_type.value}")
    print(f"  Level: {profile.level}")
    print(f"  Playtime: {profile.total_playtime:.1f} hours")
    print(f"  Churn Risk: {profile.risk_factors.get('churn_risk', 'N/A')}")

    # Predict behavior
    predictions = await asyncio.gather(
        analytics.predict_player_behavior(player_id, BehaviorPattern.SESSION_LENGTH),
        analytics.predict_player_behavior(player_id, BehaviorPattern.RETENTION_RISK),
        analytics.predict_player_behavior(player_id, BehaviorPattern.CHURN_PREDICTION)
    )

    print(f"\nBehavior Predictions:")
    for pred in predictions:
        if pred:
            print(f"  {pred.prediction_type.value}: {pred.predicted_behavior} "
                  f"(confidence: {pred.confidence:.2f})")

    # Get player insights
    insights = analytics.get_player_insights(player_id)
    print(f"\nPlayer Insights:")
    for key, value in insights.items():
        if key != "recent_predictions":
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())