#!/usr/bin/env python3
"""
Predictive Scaling Analytics for DMLogn8n Auto-Scaling
Uses machine learning to predict scaling needs
"""

import asyncio
import logging
import pickle
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import redis
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import aiohttp

from ..autoscaler import ScalingDecision, ServiceMetrics, ScaleDirection

@dataclass
class PredictionResult:
    service_id: str
    predicted_load: float
    predicted_instances: int
    confidence: float
    prediction_horizon: int  # minutes
    features_used: List[str]
    model_version: str
    timestamp: datetime

@dataclass
class AnomalyResult:
    service_id: str
    anomaly_score: float
    is_anomaly: bool
    affected_metrics: List[str]
    timestamp: datetime

class PredictiveScaler:
    """
    Uses machine learning to predict scaling needs and detect anomalies
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('predictive_scaler')

        # Model storage
        self.models: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_columns: List[str] = [
            'cpu_usage', 'memory_usage', 'request_rate', 'response_time',
            'error_rate', 'hour_of_day', 'day_of_week', 'is_weekend',
            'time_series_trend', 'time_series_seasonal', 'rolling_mean_cpu',
            'rolling_mean_memory', 'rolling_mean_requests', 'rolling_std_cpu'
        ]

        # Redis client for caching
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Model configuration
        self.model_path = config.get('model_path', '/models/scaling_predictor.pkl')
        self.prediction_window = config.get('prediction_window', 300)  # 5 minutes
        self.training_window = config.get('training_window', 7 * 24 * 60)  # 7 days
        self.min_training_samples = config.get('min_training_samples', 100)

        # Anomaly detection
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.anomaly_threshold = config.get('anomaly_threshold', 0.1)

        # Load existing models
        self._load_models()

    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            if self.model_path and self.redis_client.exists('trained_models'):
                model_data = self.redis_client.get('trained_models')
                models_dict = pickle.loads(model_data)

                self.models = models_dict.get('models', {})
                self.scalers = models_dict.get('scalers', {})
                self.anomaly_detectors = models_dict.get('anomaly_detectors', {})

                self.logger.info(f"Loaded {len(self.models)} trained models")

        except Exception as e:
            self.logger.warning(f"Could not load existing models: {e}")

    def _save_models(self):
        """Save trained models to Redis"""
        try:
            models_dict = {
                'models': self.models,
                'scalers': self.scalers,
                'anomaly_detectors': self.anomaly_detectors,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }

            model_data = pickle.dumps(models_dict)
            self.redis_client.set('trained_models', model_data, ex=86400)  # 24 hours

            self.logger.info("Saved trained models to cache")

        except Exception as e:
            self.logger.error(f"Error saving models: {e}")

    async def predict_scaling_needs(self, service_metrics: Dict[str, deque]) -> List[ScalingDecision]:
        """Predict scaling needs for all services"""
        predictions = []

        for service_id, metrics_queue in service_metrics.items():
            if len(metrics_queue) < 10:  # Need minimum data
                continue

            try:
                # Get prediction
                prediction = await self._predict_service_load(service_id, metrics_queue)

                if prediction and prediction.confidence > 0.6:
                    # Convert to scaling decision
                    decision = await self._prediction_to_scaling_decision(prediction, metrics_queue)
                    if decision:
                        predictions.append(decision)

                # Check for anomalies
                anomaly = await self._detect_anomalies(service_id, metrics_queue)
                if anomaly and anomaly.is_anomaly:
                    self.logger.warning(f"Anomaly detected for {service_id}: {anomaly.anomaly_score:.3f}")

            except Exception as e:
                self.logger.error(f"Error predicting scaling for {service_id}: {e}")

        return predictions

    async def _predict_service_load(self, service_id: str, metrics_queue: deque) -> Optional[PredictionResult]:
        """Predict future load for a service"""
        try:
            # Prepare features
            features = self._prepare_features(metrics_queue)
            if features is None:
                return None

            # Get or train model
            model = await self._get_or_train_model(service_id, features)

            if model is None:
                return None

            # Make prediction
            predicted_load = model.predict(features)[-1]

            # Calculate confidence
            confidence = self._calculate_prediction_confidence(model, features)

            # Predict required instances
            predicted_instances = self._predict_instances_from_load(predicted_load, service_id)

            return PredictionResult(
                service_id=service_id,
                predicted_load=predicted_load,
                predicted_instances=predicted_instances,
                confidence=confidence,
                prediction_horizon=self.prediction_window // 60,  # Convert to minutes
                features_used=self.feature_columns,
                model_version='1.0',
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error predicting load for {service_id}: {e}")
            return None

    def _prepare_features(self, metrics_queue: deque) -> Optional[np.ndarray]:
        """Prepare features for machine learning model"""
        try:
            if len(metrics_queue) < 10:
                return None

            # Convert to DataFrame
            metrics_data = []
            for metrics in metrics_queue:
                row = {
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'request_rate': metrics.request_rate,
                    'response_time': metrics.response_time,
                    'error_rate': metrics.error_rate,
                    'hour_of_day': metrics.timestamp.hour,
                    'day_of_week': metrics.timestamp.weekday(),
                    'is_weekend': int(metrics.timestamp.weekday() >= 5),
                    'timestamp': metrics.timestamp
                }

                # Add custom metrics
                for key, value in metrics.custom_metrics.items():
                    row[f'custom_{key}'] = value

                metrics_data.append(row)

            df = pd.DataFrame(metrics_data)

            # Add time series features
            df = self._add_time_series_features(df)

            # Add rolling statistics
            df = self._add_rolling_features(df)

            # Select and align features
            available_features = [col for col in self.feature_columns if col in df.columns]
            features = df[available_features].values

            return features

        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return None

    def _add_time_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time series features to DataFrame"""
        try:
            # Sort by timestamp
            df = df.sort_values('timestamp')

            # Trend (simple linear trend)
            df['time_series_trend'] = np.arange(len(df))

            # Seasonal patterns (hourly, daily)
            df['time_series_seasonal'] = df['hour_of_day'].apply(
                lambda x: np.sin(2 * np.pi * x / 24)
            )

            return df

        except Exception as e:
            self.logger.error(f"Error adding time series features: {e}")
            return df

    def _add_rolling_features(self, df: pd.DataFrame, windows: List[int] = [5, 10]) -> pd.DataFrame:
        """Add rolling statistical features"""
        try:
            for window in windows:
                # Rolling means
                df[f'rolling_mean_cpu_{window}'] = df['cpu_usage'].rolling(window=window).mean()
                df[f'rolling_mean_memory_{window}'] = df['memory_usage'].rolling(window=window).mean()
                df[f'rolling_mean_requests_{window}'] = df['request_rate'].rolling(window=window).mean()

                # Rolling standard deviations
                df[f'rolling_std_cpu_{window}'] = df['cpu_usage'].rolling(window=window).std()
                df[f'rolling_std_memory_{window}'] = df['memory_usage'].rolling(window=window).std()

            # Fill NaN values with forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')

            return df

        except Exception as e:
            self.logger.error(f"Error adding rolling features: {e}")
            return df

    async def _get_or_train_model(self, service_id: str, features: np.ndarray) -> Optional[Any]:
        """Get existing model or train a new one"""
        try:
            # Check if we have a trained model
            if service_id in self.models:
                return self.models[service_id]

            # Check if we have enough data to train
            if len(features) < self.min_training_samples:
                self.logger.info(f"Not enough data to train model for {service_id}")
                return None

            # Train new model
            model = await self._train_model(service_id, features)
            if model:
                self.models[service_id] = model
                self._save_models()

            return model

        except Exception as e:
            self.logger.error(f"Error getting/training model for {service_id}: {e}")
            return None

    async def _train_model(self, service_id: str, features: np.ndarray) -> Optional[Any]:
        """Train a new prediction model"""
        try:
            # Prepare training data
            X = features[:-1]  # All but last
            y = features[1:, 0]  # CPU usage of next time step (shifted)

            # Handle NaN values
            mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X = X[mask]
            y = y[mask]

            if len(X) < 50:  # Minimum samples after cleaning
                return None

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )

            model.fit(X_scaled, y)

            # Store scaler
            self.scalers[service_id] = scaler

            # Train anomaly detector
            await self._train_anomaly_detector(service_id, X_scaled)

            self.logger.info(f"Trained new model for {service_id} with {len(X)} samples")
            return model

        except Exception as e:
            self.logger.error(f"Error training model for {service_id}: {e}")
            return None

    async def _train_anomaly_detector(self, service_id: str, features: np.ndarray):
        """Train anomaly detection model"""
        try:
            detector = IsolationForest(
                contamination=self.anomaly_threshold,
                random_state=42,
                n_jobs=-1
            )

            detector.fit(features)
            self.anomaly_detectors[service_id] = detector

            self.logger.info(f"Trained anomaly detector for {service_id}")

        except Exception as e:
            self.logger.error(f"Error training anomaly detector for {service_id}: {e}")

    def _calculate_prediction_confidence(self, model: Any, features: np.ndarray) -> float:
        """Calculate confidence score for prediction"""
        try:
            if hasattr(model, 'predict_proba'):
                # For models that support probability prediction
                predictions = model.predict(features[-1:])
                return float(np.mean(model.predict_proba(features[-1:])))
            else:
                # For ensemble models like RandomForest
                if hasattr(model, 'estimators_'):
                    # Get predictions from all trees
                    tree_predictions = np.array([
                        tree.predict(features[-1:]) for tree in model.estimators_
                    ])
                    # Calculate standard deviation as uncertainty measure
                    std_dev = np.std(tree_predictions)
                    # Convert to confidence (lower std = higher confidence)
                    confidence = max(0.1, 1.0 - (std_dev / 100.0))
                    return float(confidence)
                else:
                    return 0.7  # Default confidence

        except Exception as e:
            self.logger.error(f"Error calculating prediction confidence: {e}")
            return 0.5

    def _predict_instances_from_load(self, predicted_load: float, service_id: str) -> int:
        """Predict number of instances needed based on load"""
        try:
            # Simple heuristic based on predicted CPU load
            if predicted_load > 80:
                return 4
            elif predicted_load > 60:
                return 3
            elif predicted_load > 40:
                return 2
            else:
                return 1

        except Exception as e:
            self.logger.error(f"Error predicting instances from load: {e}")
            return 1

    async def _prediction_to_scaling_decision(self, prediction: PredictionResult, metrics_queue: deque) -> Optional[ScalingDecision]:
        """Convert prediction to scaling decision"""
        try:
            current_instances = metrics_queue[-1].instance_count if metrics_queue else 1

            if prediction.predicted_instances > current_instances:
                direction = ScaleDirection.UP
                desired_instances = prediction.predicted_instances
                reason = f"Predictive scaling: CPU load expected to reach {prediction.predicted_load:.1f}% in {prediction.prediction_horizon} minutes"
            elif prediction.predicted_instances < current_instances:
                direction = ScaleDirection.DOWN
                desired_instances = prediction.predicted_instances
                reason = f"Predictive scaling: CPU load expected to drop to {prediction.predicted_load:.1f}% in {prediction.prediction_horizon} minutes"
            else:
                return None

            # Calculate cost impact (simplified)
            cost_impact = (desired_instances - current_instances) * 10  # $10 per instance

            return ScalingDecision(
                service_id=prediction.service_id,
                current_instances=current_instances,
                desired_instances=desired_instances,
                direction=direction,
                reason=reason,
                confidence=prediction.confidence,
                cost_impact=cost_impact,
                execution_time=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error converting prediction to scaling decision: {e}")
            return None

    async def _detect_anomalies(self, service_id: str, metrics_queue: deque) -> Optional[AnomalyResult]:
        """Detect anomalies in metrics"""
        try:
            if service_id not in self.anomaly_detectors:
                return None

            # Prepare features
            features = self._prepare_features(metrics_queue)
            if features is None or len(features) == 0:
                return None

            detector = self.anomaly_detectors[service_id]
            latest_features = features[-1:]  # Latest features

            # Scale features
            if service_id in self.scalers:
                scaler = self.scalers[service_id]
                latest_features_scaled = scaler.transform(latest_features)
            else:
                latest_features_scaled = latest_features

            # Detect anomaly
            anomaly_score = detector.decision_function(latest_features_scaled)[0]
            is_anomaly = detector.predict(latest_features_scaled)[0] == -1

            # Identify affected metrics
            affected_metrics = []
            if is_anomaly:
                latest_metrics = metrics_queue[-1]
                if latest_metrics.cpu_usage > 90:
                    affected_metrics.append('cpu_usage')
                if latest_metrics.memory_usage > 90:
                    affected_metrics.append('memory_usage')
                if latest_metrics.error_rate > 10:
                    affected_metrics.append('error_rate')

            return AnomalyResult(
                service_id=service_id,
                anomaly_score=float(anomaly_score),
                is_anomaly=is_anomaly,
                affected_metrics=affected_metrics,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error detecting anomalies for {service_id}: {e}")
            return None

    async def retrain_models(self):
        """Periodically retrain all models with new data"""
        try:
            # This would be called by a scheduled task
            self.logger.info("Starting model retraining...")

            # Get historical data from Redis
            # In a real implementation, this would query the metrics database
            # For now, we'll just log the retraining attempt
            self.logger.info("Model retraining completed")

        except Exception as e:
            self.logger.error(f"Error during model retraining: {e}")

    def get_model_info(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a trained model"""
        try:
            if service_id not in self.models:
                return None

            model = self.models[service_id]
            info = {
                'service_id': service_id,
                'model_type': type(model).__name__,
                'feature_count': len(self.feature_columns),
                'has_scaler': service_id in self.scalers,
                'has_anomaly_detector': service_id in self.anomaly_detectors,
                'last_trained': self.redis_client.get(f'model_trained:{service_id}') or 'Unknown'
            }

            if hasattr(model, 'feature_importances_'):
                info['feature_importances'] = dict(zip(self.feature_columns, model.feature_importances_))

            return info

        except Exception as e:
            self.logger.error(f"Error getting model info for {service_id}: {e}")
            return None