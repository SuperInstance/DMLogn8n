#!/usr/bin/env python3
"""
Predictive Analytics
Machine learning models for predictive analytics and forecasting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import joblib
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..analytics_engine import AnalyticsConfig


@dataclass
class PredictionModel:
    """Prediction model configuration"""
    model_id: str
    name: str
    model_type: str  # 'regression', 'classification', 'time_series'
    target_variable: str
    features: List[str]
    algorithm: str
    hyperparameters: Dict[str, Any]
    training_frequency: str  # 'daily', 'weekly', 'monthly'
    enabled: bool = True
    last_trained: Optional[datetime] = None
    performance_metrics: Dict[str, float] = None


@dataclass
class PredictionResult:
    """Result of a prediction"""
    model_id: str
    prediction_id: str
    target_value: Union[float, int, str]
    confidence_score: float
    feature_importance: Dict[str, float]
    timestamp: datetime
    metadata: Dict[str, Any]


class PredictiveAnalytics:
    """Predictive analytics engine"""

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

        # Initialize default prediction models
        self._initialize_default_models()

    def _setup_logging(self) -> logging.Logger:
        """Setup predictive analytics logging"""
        logger = logging.getLogger("predictive_analytics")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for predictive analytics"""
        try:
            # Create prediction_models table
            create_models_table = """
            CREATE TABLE IF NOT EXISTS prediction_models (
                model_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                target_variable VARCHAR(100) NOT NULL,
                features TEXT,
                algorithm VARCHAR(50) NOT NULL,
                hyperparameters TEXT,
                training_frequency VARCHAR(20),
                enabled BOOLEAN DEFAULT TRUE,
                last_trained TIMESTAMP,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create predictions table
            create_predictions_table = """
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id VARCHAR(100) PRIMARY KEY,
                model_id VARCHAR(100) NOT NULL,
                user_id VARCHAR(100),
                target_value DECIMAL(20,4),
                confidence_score DECIMAL(5,4),
                feature_importance TEXT,
                timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES prediction_models(model_id)
            );
            """

            # Create model_features table
            create_features_table = """
            CREATE TABLE IF NOT EXISTS model_features (
                id SERIAL PRIMARY KEY,
                model_id VARCHAR(100) NOT NULL,
                feature_name VARCHAR(100) NOT NULL,
                importance DECIMAL(10,6),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES prediction_models(model_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);",
                "CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_features_model_id ON model_features(model_id);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_models_table))
                conn.execute(text(create_predictions_table))
                conn.execute(text(create_features_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Predictive analytics tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing predictive analytics tables: {e}")

    def _initialize_default_models(self):
        """Initialize default prediction models"""
        default_models = [
            PredictionModel(
                model_id="user_lifetime_value",
                name="User Lifetime Value Prediction",
                model_type="regression",
                target_variable="lifetime_value",
                features=[
                    "session_count", "avg_session_duration", "pages_per_session",
                    "days_since_first_session", "total_revenue", "last_activity_days",
                    "device_type", "acquisition_source", "engagement_score"
                ],
                algorithm="random_forest_regressor",
                hyperparameters={"n_estimators": 100, "max_depth": 10, "random_state": 42},
                training_frequency="weekly"
            ),
            PredictionModel(
                model_id="user_churn_risk",
                name="User Churn Risk Prediction",
                model_type="classification",
                target_variable="will_churn",
                features=[
                    "days_since_last_session", "session_frequency", "avg_session_duration",
                    "support_tickets", "feature_adoption", "social_interactions",
                    "payment_issues", "device_changes"
                ],
                algorithm="random_forest_classifier",
                hyperparameters={"n_estimators": 100, "max_depth": 8, "random_state": 42},
                training_frequency="weekly"
            ),
            PredictionModel(
                model_id="revenue_forecast",
                name="Revenue Forecasting",
                model_type="time_series",
                target_variable="daily_revenue",
                features=[
                    "day_of_week", "month", "quarter", "is_holiday", "marketing_spend",
                    "active_users", "new_users", "conversion_rate", "avg_order_value"
                ],
                algorithm="linear_regression",
                hyperparameters={},  # Default parameters
                training_frequency="daily"
            ),
            PredictionModel(
                model_id="conversion_probability",
                name="User Conversion Probability",
                model_type="classification",
                target_variable="will_convert",
                features=[
                    "session_duration", "pages_visited", "feature_interactions",
                    "time_on_site", "device_type", "traffic_source", "referral_type",
                    "previous_purchases", "cart_value"
                ],
                algorithm="logistic_regression",
                hyperparameters={"random_state": 42, "max_iter": 1000},
                training_frequency="daily"
            ),
            PredictionModel(
                model_id="engagement_score",
                name="User Engagement Score Prediction",
                model_type="regression",
                target_variable="engagement_score",
                features=[
                    "login_frequency", "session_duration", "feature_usage",
                    "social_activity", "content_creation", "peer_interactions",
                    "time_since_last_activity", "achievement_progress"
                ],
                algorithm="random_forest_regressor",
                hyperparameters={"n_estimators": 50, "max_depth": 6, "random_state": 42},
                training_frequency="weekly"
            )
        ]

        for model in default_models:
            self.add_model(model)

    def add_model(self, model: PredictionModel):
        """Add a prediction model"""
        try:
            # Store in database
            query = text("""
                INSERT INTO prediction_models (
                    model_id, name, model_type, target_variable, features,
                    algorithm, hyperparameters, training_frequency, enabled
                ) VALUES (
                    :model_id, :name, :model_type, :target_variable, :features,
                    :algorithm, :hyperparameters, :training_frequency, :enabled
                )
                ON CONFLICT (model_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    model_type = EXCLUDED.model_type,
                    target_variable = EXCLUDED.target_variable,
                    features = EXCLUDED.features,
                    algorithm = EXCLUDED.algorithm,
                    hyperparameters = EXCLUDED.hyperparameters,
                    training_frequency = EXCLUDED.training_frequency,
                    enabled = EXCLUDED.enabled,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'model_id': model.model_id,
                    'name': model.name,
                    'model_type': model.model_type,
                    'target_variable': model.target_variable,
                    'features': json.dumps(model.features),
                    'algorithm': model.algorithm,
                    'hyperparameters': json.dumps(model.hyperparameters),
                    'training_frequency': model.training_frequency,
                    'enabled': model.enabled
                })
                conn.commit()

            self.models[model.model_id] = model
            self.logger.info(f"Added prediction model: {model.name}")

        except Exception as e:
            self.logger.error(f"Error adding prediction model: {e}")

    async def train_model(self, model_id: str, force_retrain: bool = False) -> Dict[str, Any]:
        """Train a prediction model"""
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

            self.logger.info(f"Training model: {model.name}")

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
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model based on algorithm
            trained_model = self._train_algorithm(model, X_train_scaled, y_train)

            # Evaluate model
            predictions = trained_model.predict(X_test_scaled)
            performance_metrics = self._evaluate_model(model, y_test, predictions)

            # Save model and preprocessing objects
            model_path = f"/tmp/analytics_models/{model_id}.joblib"
            scaler_path = f"/tmp/analytics_models/{model_id}_scaler.joblib"

            joblib.dump(trained_model, model_path)
            joblib.store(scaler, scaler_path)

            self.models[model_id] = trained_model
            self.scalers[model_id] = scaler

            # Update feature importance
            if hasattr(trained_model, 'feature_importances_'):
                importance_dict = dict(zip(model.features, trained_model.feature_importances_))
                self.feature_importance[model_id] = importance_dict
                await self._store_feature_importance(model_id, importance_dict)

            # Update model metadata
            model.last_trained = datetime.utcnow()
            model.performance_metrics = performance_metrics

            await self._update_model_metadata(model)

            # Cache model in Redis
            await self._cache_model(model_id, trained_model, scaler)

            self.logger.info(f"Model trained successfully: {model.name}")

            return {
                'status': 'success',
                'model_id': model_id,
                'performance_metrics': performance_metrics,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }

        except Exception as e:
            self.logger.error(f"Error training model {model_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def predict(self, model_id: str, features: Dict[str, Any],
                     user_id: str = None) -> PredictionResult:
        """Make a prediction using a trained model"""
        try:
            model = self.models.get(model_id)
            if not isinstance(model, PredictionModel):
                # Check if we have a trained model object
                if model_id not in self.models:
                    raise ValueError(f"Model not found: {model_id}")
                trained_model = self.models[model_id]
                model_config = None
                # Get model config from database
                model_config = await self._get_model_config(model_id)
            else:
                trained_model = self.models.get(f"{model_id}_trained")
                if not trained_model:
                    # Try to load from cache
                    trained_model = await self._load_cached_model(model_id)
                    if not trained_model:
                        raise ValueError(f"Model not trained: {model_id}")
                model_config = model

            # Get scaler
            scaler = self.scalers.get(model_id)
            if not scaler:
                scaler = await self._load_cached_scaler(model_id)

            # Prepare features
            feature_vector = self._prepare_prediction_features(features, model_config.features)
            feature_df = pd.DataFrame([feature_vector])

            # Scale features
            if scaler:
                feature_scaled = scaler.transform(feature_df)
            else:
                feature_scaled = feature_df.values

            # Make prediction
            prediction = trained_model.predict(feature_scaled)[0]

            # Get confidence score if available
            confidence_score = self._get_confidence_score(trained_model, feature_scaled)

            # Get feature importance
            feature_importance = self.feature_importance.get(model_id, {})

            # Create prediction result
            result = PredictionResult(
                model_id=model_id,
                prediction_id=f"{model_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                target_value=prediction,
                confidence_score=confidence_score,
                feature_importance=feature_importance,
                timestamp=datetime.utcnow(),
                metadata={
                    'features_used': list(features.keys()),
                    'model_version': model_config.last_trained.isoformat() if model_config else None
                }
            )

            # Store prediction
            await self._store_prediction(result, user_id)

            return result

        except Exception as e:
            self.logger.error(f"Error making prediction with model {model_id}: {e}")
            raise

    async def get_user_predictions(self, user_id: str,
                                 model_ids: List[str] = None) -> Dict[str, PredictionResult]:
        """Get all predictions for a user"""
        try:
            if model_ids is None:
                model_ids = list(self.models.keys())

            predictions = {}

            # Get user features
            user_features = await self._get_user_features(user_id)

            for model_id in model_ids:
                try:
                    prediction = await self.predict(model_id, user_features, user_id)
                    predictions[model_id] = prediction
                except Exception as e:
                    self.logger.error(f"Error getting prediction for user {user_id}, model {model_id}: {e}")

            return predictions

        except Exception as e:
            self.logger.error(f"Error getting user predictions: {e}")
            return {}

    async def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get model performance metrics"""
        try:
            model = self.models.get(model_id)
            if not model:
                raise ValueError(f"Model not found: {model_id}")

            return {
                'model_id': model_id,
                'model_name': model.name,
                'last_trained': model.last_trained.isoformat() if model.last_trained else None,
                'performance_metrics': model.performance_metrics or {},
                'feature_importance': self.feature_importance.get(model_id, {}),
                'training_frequency': model.training_frequency
            }

        except Exception as e:
            self.logger.error(f"Error getting model performance: {e}")
            return {}

    async def update_models(self):
        """Update all models that need training"""
        try:
            self.logger.info("Updating prediction models...")

            results = {}
            for model_id, model in self.models.items():
                if isinstance(model, PredictionModel) and model.enabled:
                    try:
                        result = await self.train_model(model_id)
                        results[model_id] = result
                    except Exception as e:
                        self.logger.error(f"Error updating model {model_id}: {e}")
                        results[model_id] = {'status': 'error', 'error': str(e)}

            successful = sum(1 for r in results.values() if r.get('status') == 'success')
            self.logger.info(f"Model updates completed: {successful} successful, {len(results) - successful} failed")

            return results

        except Exception as e:
            self.logger.error(f"Error updating models: {e}")
            raise

    # Private methods

    async def _get_training_data(self, model: PredictionModel) -> pd.DataFrame:
        """Get training data for a model"""
        try:
            # This would typically query from your analytics database
            # For now, return mock data
            np.random.seed(42)
            n_samples = 1000

            data = {}
            for feature in model.features:
                if feature in ['session_count', 'pages_per_session', 'days_since_first_session']:
                    data[feature] = np.random.randint(1, 100, n_samples)
                elif feature in ['avg_session_duration', 'total_revenue', 'engagement_score']:
                    data[feature] = np.random.uniform(0, 1000, n_samples)
                elif feature in ['device_type', 'acquisition_source']:
                    data[feature] = np.random.choice(['mobile', 'desktop', 'tablet'], n_samples)
                else:
                    data[feature] = np.random.uniform(0, 1, n_samples)

            # Generate target variable
            if model.model_type == 'regression':
                if model.target_variable == 'lifetime_value':
                    # Simulate LTV based on features
                    data[model.target_variable] = (
                        data['total_revenue'] * 2 +
                        data['session_count'] * 5 +
                        data['avg_session_duration'] * 0.1 +
                        np.random.normal(0, 50, n_samples)
                    )
                elif model.target_variable == 'engagement_score':
                    data[model.target_variable] = (
                        data['session_count'] * 0.3 +
                        data['avg_session_duration'] * 0.001 +
                        np.random.normal(50, 20, n_samples)
                    )
                else:
                    data[model.target_variable] = np.random.uniform(0, 100, n_samples)

            elif model.model_type == 'classification':
                if model.target_variable == 'will_churn':
                    # Simulate churn probability
                    churn_prob = 1 / (1 + np.exp(-(
                        -data['days_since_last_session'] * 0.01 +
                        data['session_frequency'] * 0.05 -
                        2
                    )))
                    data[model.target_variable] = (np.random.random(n_samples) < churn_prob).astype(int)
                elif model.target_variable == 'will_convert':
                    convert_prob = 1 / (1 + np.exp(-(
                        data['session_duration'] * 0.001 +
                        data['pages_visited'] * 0.1 -
                        1
                    )))
                    data[model.target_variable] = (np.random.random(n_samples) < convert_prob).astype(int)
                else:
                    data[model.target_variable] = np.random.randint(0, 2, n_samples)

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()

    def _prepare_features_and_target(self, data: pd.DataFrame,
                                   model: PredictionModel) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target variables"""
        try:
            # Handle categorical variables
            features_data = data.copy()

            for feature in model.features:
                if feature in features_data.columns:
                    if features_data[feature].dtype == 'object':
                        # Encode categorical variables
                        if feature not in self.encoders:
                            encoder = LabelEncoder()
                            features_data[feature] = encoder.fit_transform(features_data[feature].astype(str))
                            self.encoders[feature] = encoder
                        else:
                            features_data[feature] = self.encoders[feature].transform(features_data[feature].astype(str))

            # Extract features and target
            X = features_data[model.features].copy()
            y = features_data[model.target_variable].copy()

            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean() if model.model_type == 'regression' else 0)

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing features and target: {e}")
            return pd.DataFrame(), pd.Series()

    def _train_algorithm(self, model: PredictionModel, X_train: np.ndarray, y_train: np.ndarray):
        """Train model based on algorithm"""
        try:
            hyperparameters = model.hyperparameters or {}

            if model.algorithm == "random_forest_regressor":
                return RandomForestRegressor(**hyperparameters)
            elif model.algorithm == "random_forest_classifier":
                return RandomForestClassifier(**hyperparameters)
            elif model.algorithm == "linear_regression":
                return LinearRegression(**hyperparameters)
            elif model.algorithm == "logistic_regression":
                return LogisticRegression(**hyperparameters)
            else:
                raise ValueError(f"Unknown algorithm: {model.algorithm}")

        except Exception as e:
            self.logger.error(f"Error training algorithm: {e}")
            raise

    def _evaluate_model(self, model: PredictionModel, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        try:
            if model.model_type == 'regression':
                mse = mean_squared_error(y_true, y_pred)
                rmse = np.sqrt(mse)
                r2 = 1 - (np.sum((y_true - y_pred) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2))

                return {
                    'mse': mse,
                    'rmse': rmse,
                    'r2': r2,
                    'mae': np.mean(np.abs(y_true - y_pred))
                }

            elif model.model_type == 'classification':
                accuracy = accuracy_score(y_true, y_pred)

                # Cross-validation score
                # Note: This is simplified - in practice you'd use proper CV
                cv_scores = [accuracy]  # Placeholder

                return {
                    'accuracy': accuracy,
                    'cv_mean': np.mean(cv_scores),
                    'cv_std': np.std(cv_scores)
                }

            return {}

        except Exception as e:
            self.logger.error(f"Error evaluating model: {e}")
            return {}

    def _prepare_prediction_features(self, features: Dict[str, Any], required_features: List[str]) -> Dict[str, Any]:
        """Prepare features for prediction"""
        try:
            prepared_features = {}

            for feature in required_features:
                if feature in features:
                    value = features[feature]
                else:
                    # Use default values for missing features
                    if feature in ['session_count', 'pages_per_session']:
                        value = 1
                    elif feature in ['avg_session_duration', 'total_revenue']:
                        value = 0.0
                    elif feature in ['device_type', 'acquisition_source']:
                        value = 'unknown'
                    else:
                        value = 0.0

                # Handle categorical encoding
                if feature in self.encoders:
                    try:
                        value = self.encoders[feature].transform([str(value)])[0]
                    except ValueError:
                        # Handle unseen categories
                        value = 0

                prepared_features[feature] = value

            return prepared_features

        except Exception as e:
            self.logger.error(f"Error preparing prediction features: {e}")
            return {}

    def _get_confidence_score(self, model, X: np.ndarray) -> float:
        """Get confidence score for prediction"""
        try:
            if hasattr(model, 'predict_proba'):
                # For classification models
                probabilities = model.predict_proba(X)
                return np.max(probabilities[0])
            elif hasattr(model, 'decision_function'):
                # For models with decision function
                decision = model.decision_function(X)
                return 1 / (1 + np.exp(-decision[0]))  # Convert to probability
            else:
                # For regression models, use prediction uncertainty
                # This is simplified - in practice you'd use prediction intervals
                return 0.8  # Default confidence

        except Exception:
            return 0.5  # Default confidence on error

    async def _store_prediction(self, prediction: PredictionResult, user_id: str = None):
        """Store prediction in database"""
        try:
            query = text("""
                INSERT INTO predictions (
                    prediction_id, model_id, user_id, target_value, confidence_score,
                    feature_importance, timestamp, metadata
                ) VALUES (
                    :prediction_id, :model_id, :user_id, :target_value, :confidence_score,
                    :feature_importance, :timestamp, :metadata
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'prediction_id': prediction.prediction_id,
                    'model_id': prediction.model_id,
                    'user_id': user_id,
                    'target_value': prediction.target_value,
                    'confidence_score': prediction.confidence_score,
                    'feature_importance': json.dumps(prediction.feature_importance),
                    'timestamp': prediction.timestamp,
                    'metadata': json.dumps(prediction.metadata)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing prediction: {e}")

    async def _store_feature_importance(self, model_id: str, importance: Dict[str, float]):
        """Store feature importance in database"""
        try:
            # Clear existing importance records
            delete_query = text("DELETE FROM model_features WHERE model_id = :model_id")

            # Insert new importance records
            insert_query = text("""
                INSERT INTO model_features (model_id, feature_name, importance)
                VALUES (:model_id, :feature_name, :importance)
            """)

            with self.db_engine.connect() as conn:
                conn.execute(delete_query, {'model_id': model_id})

                for feature, importance_score in importance.items():
                    conn.execute(insert_query, {
                        'model_id': model_id,
                        'feature_name': feature,
                        'importance': importance_score
                    })

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing feature importance: {e}")

    async def _update_model_metadata(self, model: PredictionModel):
        """Update model metadata in database"""
        try:
            query = text("""
                UPDATE prediction_models
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
            # Serialize model (simplified - in practice you'd use proper serialization)
            model_data = {
                'model_type': type(model).__name__,
                'features': list(self.feature_importance.get(model_id, {}).keys()),
                'cached_at': datetime.utcnow().isoformat()
            }

            await self.redis_client.setex(
                f"model:{model_id}",
                86400,  # 24 hours TTL
                json.dumps(model_data)
            )

        except Exception as e:
            self.logger.error(f"Error caching model: {e}")

    async def _load_cached_model(self, model_id: str):
        """Load model from cache"""
        try:
            cached_data = await self.redis_client.get(f"model:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                # In practice, you'd deserialize and return the actual model
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached model: {e}")
            return None

    async def _load_cached_scaler(self, model_id: str):
        """Load scaler from cache"""
        try:
            cached_data = await self.redis_client.get(f"scaler:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                # In practice, you'd deserialize and return the actual scaler
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached scaler: {e}")
            return None

    async def _get_model_config(self, model_id: str) -> PredictionModel:
        """Get model configuration from database"""
        try:
            query = text("""
                SELECT * FROM prediction_models WHERE model_id = :model_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'model_id': model_id})
                row = result.fetchone()

                if row:
                    return PredictionModel(
                        model_id=row.model_id,
                        name=row.name,
                        model_type=row.model_type,
                        target_variable=row.target_variable,
                        features=json.loads(row.features),
                        algorithm=row.algorithm,
                        hyperparameters=json.loads(row.hyperparameters),
                        training_frequency=row.training_frequency,
                        enabled=row.enabled,
                        last_trained=row.last_trained,
                        performance_metrics=json.loads(row.performance_metrics) if row.performance_metrics else None
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error getting model config: {e}")
            return None

    async def _get_user_features(self, user_id: str) -> Dict[str, Any]:
        """Get features for a specific user"""
        try:
            # Mock implementation - would typically query user analytics data
            return {
                'session_count': 25,
                'avg_session_duration': 1200,
                'pages_per_session': 8,
                'days_since_first_session': 45,
                'total_revenue': 150.0,
                'last_activity_days': 2,
                'device_type': 'desktop',
                'acquisition_source': 'organic',
                'engagement_score': 75.5
            }

        except Exception as e:
            self.logger.error(f"Error getting user features: {e}")
            return {}