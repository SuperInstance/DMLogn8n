#!/usr/bin/env python3
"""
Churn Prediction
Machine learning models for predicting customer churn
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..analytics_engine import AnalyticsConfig


@dataclass
class ChurnModel:
    """Churn prediction model configuration"""
    model_id: str
    name: str
    algorithm: str  # 'random_forest', 'gradient_boosting', 'logistic_regression'
    features: List[str]
    prediction_horizon: int  # days into future
    hyperparameters: Dict[str, Any]
    training_frequency: str = 'weekly'
    enabled: bool = True
    last_trained: Optional[datetime] = None
    performance_metrics: Dict[str, float] = None


@dataclass
class ChurnPrediction:
    """Churn prediction result"""
    user_id: str
    model_id: str
    churn_probability: float
    churn_risk_level: str  # 'low', 'medium', 'high', 'critical'
    confidence_score: float
    key_factors: Dict[str, float]
    predicted_churn_date: Optional[datetime]
    intervention_recommendations: List[str]
    created_at: datetime


@dataclass
class ChurnIntervention:
    """Churn intervention strategy"""
    intervention_id: str
    name: str
    target_risk_levels: List[str]
    actions: List[str]
    expected_effectiveness: float
    cost_estimate: float
    automated: bool = False


class ChurnPredictor:
    """Churn prediction engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # ML models and preprocessors
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}

        # Initialize database tables
        self._initialize_tables()

        # Initialize default churn models
        self._initialize_default_models()

        # Initialize intervention strategies
        self._initialize_interventions()

    def _setup_logging(self) -> logging.Logger:
        """Setup churn prediction logging"""
        logger = logging.getLogger("churn_predictor")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for churn prediction"""
        try:
            # Create churn_models table
            create_models_table = """
            CREATE TABLE IF NOT EXISTS churn_models (
                model_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                algorithm VARCHAR(50) NOT NULL,
                features TEXT,
                prediction_horizon INTEGER,
                hyperparameters TEXT,
                training_frequency VARCHAR(20),
                enabled BOOLEAN DEFAULT TRUE,
                last_trained TIMESTAMP,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create churn_predictions table
            create_predictions_table = """
            CREATE TABLE IF NOT EXISTS churn_predictions (
                prediction_id VARCHAR(100) PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                model_id VARCHAR(100) NOT NULL,
                churn_probability DECIMAL(5,4),
                churn_risk_level VARCHAR(20),
                confidence_score DECIMAL(5,4),
                key_factors TEXT,
                predicted_churn_date TIMESTAMP,
                intervention_recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES churn_models(model_id)
            );
            """

            # Create churn_interventions table
            create_interventions_table = """
            CREATE TABLE IF NOT EXISTS churn_interventions (
                intervention_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                target_risk_levels TEXT,
                actions TEXT,
                expected_effectiveness DECIMAL(5,4),
                cost_estimate DECIMAL(10,2),
                automated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create user_intervention_history table
            create_intervention_history_table = """
            CREATE TABLE IF NOT EXISTS user_intervention_history (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                intervention_id VARCHAR(100) NOT NULL,
                prediction_id VARCHAR(100),
                applied_at TIMESTAMP NOT NULL,
                outcome TEXT,
                effectiveness_measured_at TIMESTAMP,
                effectiveness_score DECIMAL(5,4),
                FOREIGN KEY (intervention_id) REFERENCES churn_interventions(intervention_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_churn_predictions_user_id ON churn_predictions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_churn_predictions_model_id ON churn_predictions(model_id);",
                "CREATE INDEX IF NOT EXISTS idx_churn_predictions_risk_level ON churn_predictions(churn_risk_level);",
                "CREATE INDEX IF NOT EXISTS idx_intervention_history_user_id ON user_intervention_history(user_id);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_models_table))
                conn.execute(text(create_predictions_table))
                conn.execute(text(create_interventions_table))
                conn.execute(text(create_intervention_history_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Churn prediction tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing churn prediction tables: {e}")

    def _initialize_default_models(self):
        """Initialize default churn prediction models"""
        default_models = [
            ChurnModel(
                model_id="short_term_churn",
                name="Short-term Churn Prediction (7 days)",
                algorithm="random_forest",
                features=[
                    "days_since_last_session", "session_frequency", "avg_session_duration",
                    "session_duration_variance", "login_pattern_regularity", "feature_usage_decline",
                    "support_tickets", "error_rate", "payment_failures", "social_activity_decline"
                ],
                prediction_horizon=7,
                hyperparameters={"n_estimators": 100, "max_depth": 8, "random_state": 42},
                training_frequency="daily"
            ),
            ChurnModel(
                model_id="medium_term_churn",
                name="Medium-term Churn Prediction (30 days)",
                algorithm="gradient_boosting",
                features=[
                    "engagement_trend", "feature_adoption_rate", "retention_history",
                    "purchase_frequency", "support_interactions", "peer_connections",
                    "achievement_progress", "content_consumption_rate", "device_changes"
                ],
                prediction_horizon=30,
                hyperparameters={"n_estimators": 100, "learning_rate": 0.1, "max_depth": 6, "random_state": 42},
                training_frequency="weekly"
            ),
            ChurnModel(
                model_id="long_term_churn",
                name="Long-term Churn Prediction (90 days)",
                algorithm="logistic_regression",
                features=[
                    "lifetime_value", "account_age", "loyalty_score", "referral_count",
                    "upgrade_history", "community_participation", "feedback_sentiment",
                    "contract_type", "billing_issues"
                ],
                prediction_horizon=90,
                hyperparameters={"random_state": 42, "max_iter": 1000},
                training_frequency="monthly"
            )
        ]

        for model in default_models:
            self.add_model(model)

    def _initialize_interventions(self):
        """Initialize churn intervention strategies"""
        default_interventions = [
            ChurnIntervention(
                intervention_id="high_risk_immediate",
                name="High Risk Immediate Intervention",
                target_risk_levels=["critical", "high"],
                actions=[
                    "Personal outreach from customer success",
                    "Special discount offer",
                    "Premium feature trial",
                    "Schedule success call"
                ],
                expected_effectiveness=0.75,
                cost_estimate=150.0,
                automated=False
            ),
            ChurnIntervention(
                intervention_id="medium_risk_automated",
                name="Medium Risk Automated Campaign",
                target_risk_levels=["medium"],
                actions=[
                    "Personalized email campaign",
                    "In-app targeted messages",
                    "Tutorial recommendations",
                    "Community invitation"
                ],
                expected_effectiveness=0.45,
                cost_estimate=15.0,
                automated=True
            ),
            ChurnIntervention(
                intervention_id="low_risk_nurturing",
                name="Low Risk Nurturing",
                target_risk_levels=["low"],
                actions=[
                    "Educational content",
                    "Product updates",
                    "Community highlights",
                    "Feature tips"
                ],
                expected_effectiveness=0.25,
                cost_estimate=5.0,
                automated=True
            )
        ]

        for intervention in default_interventions:
            self.add_intervention(intervention)

    def add_model(self, model: ChurnModel):
        """Add a churn prediction model"""
        try:
            # Store in database
            query = text("""
                INSERT INTO churn_models (
                    model_id, name, algorithm, features, prediction_horizon,
                    hyperparameters, training_frequency, enabled
                ) VALUES (
                    :model_id, :name, :algorithm, :features, :prediction_horizon,
                    :hyperparameters, :training_frequency, :enabled
                )
                ON CONFLICT (model_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    algorithm = EXCLUDED.algorithm,
                    features = EXCLUDED.features,
                    prediction_horizon = EXCLUDED.prediction_horizon,
                    hyperparameters = EXCLUDED.hyperparameters,
                    training_frequency = EXCLUDED.training_frequency,
                    enabled = EXCLUDED.enabled,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'model_id': model.model_id,
                    'name': model.name,
                    'algorithm': model.algorithm,
                    'features': json.dumps(model.features),
                    'prediction_horizon': model.prediction_horizon,
                    'hyperparameters': json.dumps(model.hyperparameters),
                    'training_frequency': model.training_frequency,
                    'enabled': model.enabled
                })
                conn.commit()

            self.models[model.model_id] = model
            self.logger.info(f"Added churn prediction model: {model.name}")

        except Exception as e:
            self.logger.error(f"Error adding churn prediction model: {e}")

    def add_intervention(self, intervention: ChurnIntervention):
        """Add a churn intervention strategy"""
        try:
            query = text("""
                INSERT INTO churn_interventions (
                    intervention_id, name, target_risk_levels, actions,
                    expected_effectiveness, cost_estimate, automated
                ) VALUES (
                    :intervention_id, :name, :target_risk_levels, :actions,
                    :expected_effectiveness, :cost_estimate, :automated
                )
                ON CONFLICT (intervention_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    target_risk_levels = EXCLUDED.target_risk_levels,
                    actions = EXCLUDED.actions,
                    expected_effectiveness = EXCLUDED.expected_effectiveness,
                    cost_estimate = EXCLUDED.cost_estimate,
                    automated = EXCLUDED.automated
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'intervention_id': intervention.intervention_id,
                    'name': intervention.name,
                    'target_risk_levels': json.dumps(intervention.target_risk_levels),
                    'actions': json.dumps(intervention.actions),
                    'expected_effectiveness': intervention.expected_effectiveness,
                    'cost_estimate': intervention.cost_estimate,
                    'automated': intervention.automated
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error adding churn intervention: {e}")

    async def train_model(self, model_id: str, force_retrain: bool = False) -> Dict[str, Any]:
        """Train a churn prediction model"""
        try:
            model = self.models.get(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")

            # Check if retraining is needed
            if not force_retrain and model.last_trained:
                time_since_training = datetime.utcnow() - model.last_trained
                if model.training_frequency == 'daily' and time_since_training.days < 1:
                    return {'status': 'skipped', 'reason': 'Recently trained'}
                elif model.training_frequency == 'weekly' and time_since_training.days < 7:
                    return {'status': 'skipped', 'reason': 'Recently trained'}
                elif model.training_frequency == 'monthly' and time_since_training.days < 30:
                    return {'status': 'skipped', 'reason': 'Recently trained'}

            self.logger.info(f"Training churn model: {model.name}")

            # Get training data
            training_data = await self._get_training_data(model)
            if training_data.empty:
                raise ValueError(f"No training data available for model {model_id}")

            # Prepare features and target
            X, y = self._prepare_features_and_target(training_data, model)

            if X.empty or len(y) == 0:
                raise ValueError(f"Invalid training data for model {model_id}")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Handle class imbalance
            if len(np.unique(y_train)) > 1:
                # Calculate class weights
                class_weights = dict(zip(
                    np.unique(y_train),
                    len(y_train) / (len(np.unique(y_train)) * np.bincount(y_train))
                ))
            else:
                class_weights = None

            # Train model
            trained_model = self._train_algorithm(model, X_train_scaled, y_train, class_weights)

            # Evaluate model
            predictions = trained_model.predict(X_test_scaled)
            probabilities = trained_model.predict_proba(X_test_scaled)[:, 1]

            performance_metrics = self._evaluate_churn_model(y_test, predictions, probabilities)

            # Save model and preprocessing objects
            self.models[f"{model_id}_trained"] = trained_model
            self.scalers[model_id] = scaler

            # Update feature importance
            if hasattr(trained_model, 'feature_importances_'):
                importance_dict = dict(zip(model.features, trained_model.feature_importances_))
                self.feature_importance[model_id] = importance_dict

            # Update model metadata
            model.last_trained = datetime.utcnow()
            model.performance_metrics = performance_metrics

            await self._update_model_metadata(model)

            # Cache model
            await self._cache_model(model_id, trained_model, scaler)

            self.logger.info(f"Churn model trained successfully: {model.name}")

            return {
                'status': 'success',
                'model_id': model_id,
                'performance_metrics': performance_metrics,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'churn_rate': float(np.mean(y_test))
            }

        except Exception as e:
            self.logger.error(f"Error training churn model {model_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def predict_churn_risk(self, user_id: str, model_id: str = None) -> Optional[ChurnPrediction]:
        """Predict churn risk for a user"""
        try:
            if model_id is None:
                model_id = "short_term_churn"  # Default model

            model = self.models.get(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")

            # Get trained model
            trained_model = self.models.get(f"{model_id}_trained")
            if not trained_model:
                trained_model = await self._load_cached_model(model_id)
                if not trained_model:
                    raise ValueError(f"Model not trained: {model_id}")

            # Get user features
            user_features = await self._get_user_churn_features(user_id)

            # Prepare features
            feature_vector = self._prepare_prediction_features(user_features, model.features)
            feature_df = pd.DataFrame([feature_vector])

            # Scale features
            scaler = self.scalers.get(model_id)
            if not scaler:
                scaler = await self._load_cached_scaler(model_id)

            if scaler:
                feature_scaled = scaler.transform(feature_df)
            else:
                feature_scaled = feature_df.values

            # Make prediction
            churn_probability = trained_model.predict_proba(feature_scaled)[0, 1]

            # Determine risk level
            churn_risk_level = self._determine_risk_level(churn_probability)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(trained_model, feature_scaled)

            # Get key factors
            key_factors = self._get_key_factors(user_features, model_id)

            # Predict churn date
            predicted_churn_date = self._predict_churn_date(churn_probability, model.prediction_horizon)

            # Get intervention recommendations
            intervention_recommendations = await self._get_intervention_recommendations(churn_risk_level)

            # Create prediction
            prediction = ChurnPrediction(
                user_id=user_id,
                model_id=model_id,
                churn_probability=churn_probability,
                churn_risk_level=churn_risk_level,
                confidence_score=confidence_score,
                key_factors=key_factors,
                predicted_churn_date=predicted_churn_date,
                intervention_recommendations=intervention_recommendations,
                created_at=datetime.utcnow()
            )

            # Store prediction
            await self._store_churn_prediction(prediction)

            return prediction

        except Exception as e:
            self.logger.error(f"Error predicting churn risk for user {user_id}: {e}")
            return None

    async def get_users_at_risk(self, risk_level: str = None,
                              limit: int = 100) -> List[ChurnPrediction]:
        """Get users at risk of churn"""
        try:
            where_conditions = []
            params = {}

            if risk_level:
                where_conditions.append("churn_risk_level = :risk_level")
                params['risk_level'] = risk_level

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            query = f"""
                SELECT * FROM churn_predictions
                {where_clause}
                ORDER BY churn_probability DESC
                LIMIT :limit
            """

            params['limit'] = limit

            with self.db_engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()

            predictions = []
            for row in rows:
                prediction = ChurnPrediction(
                    user_id=row.user_id,
                    model_id=row.model_id,
                    churn_probability=row.churn_probability,
                    churn_risk_level=row.churn_risk_level,
                    confidence_score=row.confidence_score,
                    key_factors=json.loads(row.key_factors) if row.key_factors else {},
                    predicted_churn_date=row.predicted_churn_date,
                    intervention_recommendations=json.loads(row.intervention_recommendations) if row.intervention_recommendations else [],
                    created_at=row.created_at
                )
                predictions.append(prediction)

            return predictions

        except Exception as e:
            self.logger.error(f"Error getting users at risk: {e}")
            return []

    async def apply_intervention(self, user_id: str, intervention_id: str,
                               prediction_id: str = None) -> bool:
        """Apply churn intervention to a user"""
        try:
            # Record intervention application
            query = text("""
                INSERT INTO user_intervention_history (
                    user_id, intervention_id, prediction_id, applied_at
                ) VALUES (
                    :user_id, :intervention_id, :prediction_id, :applied_at
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'user_id': user_id,
                    'intervention_id': intervention_id,
                    'prediction_id': prediction_id,
                    'applied_at': datetime.utcnow()
                })
                conn.commit()

            self.logger.info(f"Applied intervention {intervention_id} to user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error applying intervention: {e}")
            return False

    async def update_model(self) -> Dict[str, Any]:
        """Update churn prediction models"""
        try:
            self.logger.info("Updating churn prediction models...")

            results = {}
            for model_id, model in self.models.items():
                if isinstance(model, ChurnModel) and model.enabled:
                    try:
                        result = await self.train_model(model_id)
                        results[model_id] = result
                    except Exception as e:
                        self.logger.error(f"Error updating churn model {model_id}: {e}")
                        results[model_id] = {'status': 'error', 'error': str(e)}

            successful = sum(1 for r in results.values() if r.get('status') == 'success')
            self.logger.info(f"Churn model updates completed: {successful} successful, {len(results) - successful} failed")

            return results

        except Exception as e:
            self.logger.error(f"Error updating churn models: {e}")
            raise

    # Private methods

    async def _get_training_data(self, model: ChurnModel) -> pd.DataFrame:
        """Get training data for churn model"""
        try:
            # Mock implementation - would typically query historical user data
            np.random.seed(42)
            n_samples = 5000

            data = {}
            for feature in model.features:
                if feature.endswith('_frequency') or feature.endswith('_rate'):
                    data[feature] = np.random.uniform(0, 1, n_samples)
                elif feature.endswith('_days') or feature.endswith('_duration'):
                    data[feature] = np.random.randint(1, 365, n_samples)
                elif feature.endswith('_decline'):
                    data[feature] = np.random.uniform(-0.5, 0.5, n_samples)
                elif feature.endswith('_count') or feature.endswith('_tickets'):
                    data[feature] = np.random.randint(0, 20, n_samples)
                else:
                    data[feature] = np.random.uniform(0, 100, n_samples)

            # Generate churn target variable
            # Create realistic churn patterns based on features
            churn_prob = 1 / (1 + np.exp(-(
                -data['days_since_last_session'] * 0.01 -
                data['support_tickets'] * 0.1 +
                data['engagement_trend'] * 0.5 -
                2
            )))

            data['churned'] = (np.random.random(n_samples) < churn_prob).astype(int)

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()

    def _prepare_features_and_target(self, data: pd.DataFrame, model: ChurnModel) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target variables"""
        try:
            # Handle categorical variables
            features_data = data.copy()

            for feature in model.features:
                if feature in features_data.columns and features_data[feature].dtype == 'object':
                    if feature not in self.encoders:
                        encoder = LabelEncoder()
                        features_data[feature] = encoder.fit_transform(features_data[feature].astype(str))
                        self.encoders[feature] = encoder
                    else:
                        features_data[feature] = self.encoders[feature].transform(features_data[feature].astype(str))

            # Extract features and target
            X = features_data[model.features].copy()
            y = features_data['churned'].copy()

            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(0)

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing features and target: {e}")
            return pd.DataFrame(), pd.Series()

    def _train_algorithm(self, model: ChurnModel, X_train: np.ndarray, y_train: np.ndarray,
                        class_weights: Optional[Dict] = None):
        """Train model based on algorithm"""
        try:
            hyperparameters = model.hyperparameters or {}

            if model.algorithm == "random_forest":
                if class_weights:
                    hyperparameters['class_weight'] = class_weights
                return RandomForestClassifier(**hyperparameters)
            elif model.algorithm == "gradient_boosting":
                return GradientBoostingClassifier(**hyperparameters)
            elif model.algorithm == "logistic_regression":
                if class_weights:
                    hyperparameters['class_weight'] = class_weights
                return LogisticRegression(**hyperparameters)
            else:
                raise ValueError(f"Unknown algorithm: {model.algorithm}")

        except Exception as e:
            self.logger.error(f"Error training algorithm: {e}")
            raise

    def _evaluate_churn_model(self, y_true: np.ndarray, y_pred: np.ndarray,
                            y_prob: np.ndarray) -> Dict[str, float]:
        """Evaluate churn prediction model performance"""
        try:
            return {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred, average='binary'),
                'recall': recall_score(y_true, y_pred, average='binary'),
                'f1_score': f1_score(y_true, y_pred, average='binary'),
                'roc_auc': roc_auc_score(y_true, y_prob)
            }

        except Exception as e:
            self.logger.error(f"Error evaluating churn model: {e}")
            return {}

    def _determine_risk_level(self, churn_probability: float) -> str:
        """Determine churn risk level from probability"""
        if churn_probability >= 0.8:
            return "critical"
        elif churn_probability >= 0.6:
            return "high"
        elif churn_probability >= 0.3:
            return "medium"
        else:
            return "low"

    def _calculate_confidence_score(self, model, X: np.ndarray) -> float:
        """Calculate confidence score for prediction"""
        try:
            probabilities = model.predict_proba(X)
            max_prob = np.max(probabilities[0])
            return max_prob

        except Exception:
            return 0.5  # Default confidence

    def _get_key_factors(self, user_features: Dict[str, Any], model_id: str) -> Dict[str, float]:
        """Get key factors contributing to churn prediction"""
        try:
            feature_importance = self.feature_importance.get(model_id, {})

            # Sort features by importance
            key_factors = {}
            for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
                if feature in user_features:
                    key_factors[feature] = importance

            return dict(list(key_factors.items())[:5])  # Top 5 factors

        except Exception as e:
            self.logger.error(f"Error getting key factors: {e}")
            return {}

    def _predict_churn_date(self, churn_probability: float, horizon_days: int) -> Optional[datetime]:
        """Predict likely churn date"""
        try:
            if churn_probability > 0.5:
                # Higher probability = sooner churn
                expected_days = int(horizon_days * (1.5 - churn_probability))
                return datetime.utcnow() + timedelta(days=expected_days)
            return None

        except Exception:
            return None

    async def _get_intervention_recommendations(self, risk_level: str) -> List[str]:
        """Get intervention recommendations based on risk level"""
        try:
            query = text("""
                SELECT actions FROM churn_interventions
                WHERE :risk_level = ANY(target_risk_levels)
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'risk_level': risk_level})
                rows = result.fetchall()

            recommendations = []
            for row in rows:
                actions = json.loads(row.actions)
                recommendations.extend(actions)

            return recommendations[:5]  # Limit to top 5

        except Exception as e:
            self.logger.error(f"Error getting intervention recommendations: {e}")
            return []

    def _prepare_prediction_features(self, user_features: Dict[str, Any], required_features: List[str]) -> Dict[str, Any]:
        """Prepare features for prediction"""
        try:
            prepared_features = {}

            for feature in required_features:
                if feature in user_features:
                    value = user_features[feature]
                else:
                    # Use default values for missing features
                    if feature.endswith('_frequency') or feature.endswith('_rate'):
                        value = 0.5
                    elif feature.endswith('_days') or feature.endswith('_duration'):
                        value = 30
                    elif feature.endswith('_decline'):
                        value = 0.0
                    else:
                        value = 0.0

                # Handle categorical encoding
                if feature in self.encoders:
                    try:
                        value = self.encoders[feature].transform([str(value)])[0]
                    except ValueError:
                        value = 0

                prepared_features[feature] = value

            return prepared_features

        except Exception as e:
            self.logger.error(f"Error preparing prediction features: {e}")
            return {}

    async def _store_churn_prediction(self, prediction: ChurnPrediction):
        """Store churn prediction in database"""
        try:
            query = text("""
                INSERT INTO churn_predictions (
                    prediction_id, user_id, model_id, churn_probability, churn_risk_level,
                    confidence_score, key_factors, predicted_churn_date, intervention_recommendations
                ) VALUES (
                    :prediction_id, :user_id, :model_id, :churn_probability, :churn_risk_level,
                    :confidence_score, :key_factors, :predicted_churn_date, :intervention_recommendations
                )
                ON CONFLICT (user_id, model_id) DO UPDATE SET
                    churn_probability = EXCLUDED.churn_probability,
                    churn_risk_level = EXCLUDED.churn_risk_level,
                    confidence_score = EXCLUDED.confidence_score,
                    key_factors = EXCLUDED.key_factors,
                    predicted_churn_date = EXCLUDED.predicted_churn_date,
                    intervention_recommendations = EXCLUDED.intervention_recommendations,
                    created_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'prediction_id': f"{prediction.user_id}_{prediction.model_id}_{int(datetime.utcnow().timestamp())}",
                    'user_id': prediction.user_id,
                    'model_id': prediction.model_id,
                    'churn_probability': prediction.churn_probability,
                    'churn_risk_level': prediction.churn_risk_level,
                    'confidence_score': prediction.confidence_score,
                    'key_factors': json.dumps(prediction.key_factors),
                    'predicted_churn_date': prediction.predicted_churn_date,
                    'intervention_recommendations': json.dumps(prediction.intervention_recommendations)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing churn prediction: {e}")

    async def _update_model_metadata(self, model: ChurnModel):
        """Update model metadata in database"""
        try:
            query = text("""
                UPDATE churn_models
                SET last_trained = :last_trained,
                    performance_metrics = :performance_metrics,
                    updated_at = CURRENT_TIMESTAMP
                WHERE model_id = :model_id
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'model_id': model.model_id,
                    'last_trained': model.last_trained,
                    'performance_metrics': json.dumps(model.performance_metrics)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating model metadata: {e}")

    async def _cache_model(self, model_id: str, model, scaler):
        """Cache model in Redis"""
        try:
            model_data = {
                'model_type': type(model).__name__,
                'features': list(self.feature_importance.get(model_id, {}).keys()),
                'cached_at': datetime.utcnow().isoformat()
            }

            await self.redis_client.setex(
                f"churn_model:{model_id}",
                86400,  # 24 hours TTL
                json.dumps(model_data)
            )

        except Exception as e:
            self.logger.error(f"Error caching churn model: {e}")

    async def _load_cached_model(self, model_id: str):
        """Load model from cache"""
        try:
            cached_data = await self.redis_client.get(f"churn_model:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached churn model: {e}")
            return None

    async def _load_cached_scaler(self, model_id: str):
        """Load scaler from cache"""
        try:
            cached_data = await self.redis_client.get(f"churn_scaler:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached scaler: {e}")
            return None

    async def _get_user_churn_features(self, user_id: str) -> Dict[str, Any]:
        """Get churn-related features for a user"""
        try:
            # Mock implementation - would typically query user analytics data
            return {
                'days_since_last_session': 5,
                'session_frequency': 0.8,
                'avg_session_duration': 1200,
                'session_duration_variance': 300,
                'login_pattern_regularity': 0.9,
                'feature_usage_decline': -0.1,
                'support_tickets': 1,
                'error_rate': 0.02,
                'payment_failures': 0,
                'social_activity_decline': -0.05,
                'engagement_trend': 0.1,
                'feature_adoption_rate': 0.75,
                'retention_history': 0.85,
                'purchase_frequency': 0.3,
                'support_interactions': 2,
                'peer_connections': 15,
                'achievement_progress': 0.6,
                'content_consumption_rate': 0.8,
                'device_changes': 0,
                'lifetime_value': 250.0,
                'account_age': 180,
                'loyalty_score': 0.7,
                'referral_count': 2,
                'upgrade_history': 1,
                'community_participation': 0.6,
                'feedback_sentiment': 0.8,
                'contract_type': 'premium',
                'billing_issues': 0
            }

        except Exception as e:
            self.logger.error(f"Error getting user churn features: {e}")
            return {}