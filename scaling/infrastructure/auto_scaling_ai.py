#!/usr/bin/env python3
"""
AI-Powered Predictive Auto-Scaling System for DMLogn8n
Advanced machine learning models for demand prediction and intelligent scaling
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import boto3
import aiohttp
import redis
from sqlalchemy import create_engine
import plotly.graph_objects as go
import plotly.express as px

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScalingMetrics:
    """Real-time scaling metrics data structure"""
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    active_connections: int
    request_rate: float
    response_time: float
    error_rate: float
    queue_length: int
    database_connections: int
    cache_hit_rate: float
    current_instances: int
    region: str

@dataclass
class ScalingPrediction:
    """AI scaling prediction results"""
    predicted_load: float
    confidence_score: float
    time_horizon: timedelta
    recommended_instances: int
    scaling_action: str
    cost_estimate: float
    risk_factors: List[str]

@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration"""
    name: str
    service_name: str
    min_instances: int
    max_instances: int
    target_cpu: float
    target_memory: float
    scale_up_cooldown: int
    scale_down_cooldown: int
    prediction_weight: float
    cost_threshold: float
    priority: int

class PredictiveScalingModel:
    """Machine learning model for demand prediction"""

    def __init__(self, model_path: str = "models/scaling_model.pkl"):
        self.model_path = model_path
        self.scaler = StandardScaler()
        self.models = {
            'short_term': RandomForestRegressor(n_estimators=100, random_state=42),
            'medium_term': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'long_term': RandomForestRegressor(n_estimators=200, random_state=42)
        }
        self.feature_columns = [
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_holiday',
            'cpu_lag_1', 'cpu_lag_2', 'cpu_lag_6', 'cpu_lag_12',
            'memory_lag_1', 'request_rate_lag_1', 'response_time_lag_1',
            'active_connections_lag_1', 'queue_length_lag_1'
        ]

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML model"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_holiday'] = 0  # TODO: Implement holiday detection

        # Create lag features
        for lag in [1, 2, 6, 12]:
            df[f'cpu_lag_{lag}'] = df['cpu_utilization'].shift(lag)

        df['memory_lag_1'] = df['memory_utilization'].shift(1)
        df['request_rate_lag_1'] = df['request_rate'].shift(1)
        df['response_time_lag_1'] = df['response_time'].shift(1)
        df['active_connections_lag_1'] = df['active_connections'].shift(1)
        df['queue_length_lag_1'] = df['queue_length'].shift(1)

        return df.fillna(method='bfill').fillna(0)

    def train(self, historical_data: List[ScalingMetrics]) -> Dict[str, float]:
        """Train predictive models on historical data"""
        df = pd.DataFrame([asdict(m) for m in historical_data])
        df = self.prepare_features(df)

        X = df[self.feature_columns]
        y = df['cpu_utilization']

        # Split data for different time horizons
        results = {}
        for horizon, model in self.models.items():
            if horizon == 'short_term':
                # Predict 15 minutes ahead
                y_target = y.shift(-3).fillna(method='ffill')
            elif horizon == 'medium_term':
                # Predict 2 hours ahead
                y_target = y.shift(-24).fillna(method='ffill')
            else:  # long_term
                # Predict 24 hours ahead
                y_target = y.shift(-288).fillna(method='ffill')

            X_train, X_test, y_train, y_test = train_test_split(
                X, y_target, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            model.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            results[horizon] = {'mae': mae, 'rmse': rmse}
            logger.info(f"{horizon} model trained - MAE: {mae:.4f}, RMSE: {rmse:.4f}")

        # Save models
        self.save_models()
        return results

    def predict(self, current_metrics: ScalingMetrics, horizon: str = 'medium_term') -> ScalingPrediction:
        """Predict future load and recommend scaling"""
        # Convert to DataFrame and prepare features
        df = pd.DataFrame([asdict(current_metrics)])
        features_df = self.prepare_features(df)
        X = features_df[self.feature_columns]
        X_scaled = self.scaler.transform(X)

        # Get prediction
        model = self.models[horizon]
        predicted_load = model.predict(X_scaled)[0]

        # Calculate confidence based on prediction variance
        confidence = max(0.5, min(0.95, 1.0 - abs(predicted_load - 50) / 100))

        # Calculate recommended instances
        recommended_instances = max(1, int(predicted_load / 60))  # Target 60% CPU

        # Determine scaling action
        if predicted_load > 80:
            scaling_action = 'scale_up_aggressive'
        elif predicted_load > 70:
            scaling_action = 'scale_up_moderate'
        elif predicted_load < 30:
            scaling_action = 'scale_down'
        else:
            scaling_action = 'maintain'

        # Estimate cost
        cost_estimate = recommended_instances * 0.05  # $0.05 per instance per hour

        # Identify risk factors
        risk_factors = []
        if predicted_load > 90:
            risk_factors.append('High CPU utilization predicted')
        if current_metrics.memory_utilization > 85:
            risk_factors.append('Memory pressure detected')
        if current_metrics.error_rate > 5:
            risk_factors.append('High error rate observed')
        if current_metrics.response_time > 1000:
            risk_factors.append('Response time degradation')

        time_horizons = {
            'short_term': timedelta(minutes=15),
            'medium_term': timedelta(hours=2),
            'long_term': timedelta(hours=24)
        }

        return ScalingPrediction(
            predicted_load=predicted_load,
            confidence_score=confidence,
            time_horizon=time_horizons[horizon],
            recommended_instances=recommended_instances,
            scaling_action=scaling_action,
            cost_estimate=cost_estimate,
            risk_factors=risk_factors
        )

    def save_models(self):
        """Save trained models to disk"""
        import os
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns
        }
        joblib.dump(model_data, self.model_path)
        logger.info(f"Models saved to {self.model_path}")

    def load_models(self):
        """Load trained models from disk"""
        try:
            model_data = joblib.load(self.model_path)
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            logger.info(f"Models loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"No saved models found at {self.model_path}")
            return False

class AutoScalingAI:
    """Main AI-powered auto-scaling system"""

    def __init__(self, config_path: str = "config/scaling_config.json"):
        self.config = self._load_config(config_path)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.db_engine = create_engine(self.config['database_url'])
        self.prediction_model = PredictiveScalingModel()
        self.prediction_model.load_models()

        # Cloud provider clients
        self.aws_client = boto3.client('autoscaling',
                                      aws_access_key_id=self.config['aws_access_key'],
                                      aws_secret_access_key=self.config['aws_secret_key'])
        self.azure_client = None  # TODO: Initialize Azure client
        self.gcp_client = None  # TODO: Initialize GCP client

        self.scaling_policies = self._load_scaling_policies()
        self.last_scaling_actions = {}

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                'database_url': 'postgresql://user:pass@localhost/dmlogn8n',
                'aws_access_key': '',
                'aws_secret_key': '',
                'redis_host': 'localhost',
                'redis_port': 6379,
                'prediction_interval': 300,  # 5 minutes
                'metrics_retention_days': 30
            }

    def _load_scaling_policies(self) -> List[ScalingPolicy]:
        """Load scaling policies from configuration"""
        policies = []

        # Default policies for different services
        default_policies = [
            {
                'name': 'web_servers',
                'service_name': 'web-server',
                'min_instances': 2,
                'max_instances': 50,
                'target_cpu': 60.0,
                'target_memory': 70.0,
                'scale_up_cooldown': 300,
                'scale_down_cooldown': 600,
                'prediction_weight': 0.7,
                'cost_threshold': 100.0,
                'priority': 1
            },
            {
                'name': 'api_servers',
                'service_name': 'api-server',
                'min_instances': 3,
                'max_instances': 100,
                'target_cpu': 55.0,
                'target_memory': 65.0,
                'scale_up_cooldown': 180,
                'scale_down_cooldown': 300,
                'prediction_weight': 0.8,
                'cost_threshold': 200.0,
                'priority': 2
            },
            {
                'name': 'worker_nodes',
                'service_name': 'worker-node',
                'min_instances': 1,
                'max_instances': 200,
                'target_cpu': 75.0,
                'target_memory': 80.0,
                'scale_up_cooldown': 120,
                'scale_down_cooldown': 600,
                'prediction_weight': 0.6,
                'cost_threshold': 150.0,
                'priority': 3
            }
        ]

        for policy_data in default_policies:
            policies.append(ScalingPolicy(**policy_data))

        return policies

    async def collect_metrics(self, service_name: str) -> Optional[ScalingMetrics]:
        """Collect real-time metrics for a service"""
        try:
            # Collect from various sources
            metrics = await asyncio.gather(
                self._get_system_metrics(service_name),
                self._get_application_metrics(service_name),
                self._get_database_metrics(service_name),
                self._get_network_metrics(service_name)
            )

            # Aggregate metrics
            system_metrics, app_metrics, db_metrics, network_metrics = metrics

            return ScalingMetrics(
                timestamp=datetime.utcnow(),
                cpu_utilization=system_metrics['cpu'],
                memory_utilization=system_metrics['memory'],
                active_connections=app_metrics['active_connections'],
                request_rate=app_metrics['request_rate'],
                response_time=app_metrics['response_time'],
                error_rate=app_metrics['error_rate'],
                queue_length=app_metrics['queue_length'],
                database_connections=db_metrics['connections'],
                cache_hit_rate=db_metrics['cache_hit_rate'],
                current_instances=system_metrics['instances'],
                region=system_metrics['region']
            )
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            return None

    async def _get_system_metrics(self, service_name: str) -> Dict:
        """Get system-level metrics"""
        # Mock implementation - replace with actual cloud provider APIs
        return {
            'cpu': np.random.uniform(20, 80),
            'memory': np.random.uniform(30, 70),
            'instances': np.random.randint(2, 10),
            'region': 'us-east-1'
        }

    async def _get_application_metrics(self, service_name: str) -> Dict:
        """Get application-level metrics"""
        # Mock implementation - replace with actual monitoring
        return {
            'active_connections': np.random.randint(100, 1000),
            'request_rate': np.random.uniform(50, 500),
            'response_time': np.random.uniform(100, 500),
            'error_rate': np.random.uniform(0, 5),
            'queue_length': np.random.randint(0, 50)
        }

    async def _get_database_metrics(self, service_name: str) -> Dict:
        """Get database metrics"""
        # Mock implementation - replace with actual database monitoring
        return {
            'connections': np.random.randint(10, 50),
            'cache_hit_rate': np.random.uniform(0.7, 0.95)
        }

    async def _get_network_metrics(self, service_name: str) -> Dict:
        """Get network metrics"""
        # Mock implementation - replace with actual network monitoring
        return {}

    async def predict_scaling_needs(self, service_name: str, metrics: ScalingMetrics) -> List[ScalingPrediction]:
        """Generate scaling predictions for different time horizons"""
        predictions = []

        for horizon in ['short_term', 'medium_term', 'long_term']:
            prediction = self.prediction_model.predict(metrics, horizon)
            predictions.append(prediction)

        return predictions

    async def execute_scaling_action(self, service_name: str, prediction: ScalingPrediction, policy: ScalingPolicy) -> bool:
        """Execute scaling action based on prediction"""
        # Check cooldown period
        last_action = self.last_scaling_actions.get(service_name)
        if last_action:
            time_since_last = datetime.utcnow() - last_action['timestamp']
            cooldown = policy.scale_up_cooldown if prediction.scaling_action.startswith('scale_up') else policy.scale_down_cooldown

            if time_since_last.total_seconds() < cooldown:
                logger.info(f"Scaling action for {service_name} blocked by cooldown")
                return False

        try:
            # Calculate target instances
            current_instances = await self._get_current_instances(service_name)
            target_instances = max(policy.min_instances,
                                 min(policy.max_instances, prediction.recommended_instances))

            # Execute scaling
            if prediction.scaling_action.startswith('scale_up') and target_instances > current_instances:
                success = await self._scale_up(service_name, current_instances, target_instances)
            elif prediction.scaling_action == 'scale_down' and target_instances < current_instances:
                success = await self._scale_down(service_name, current_instances, target_instances)
            else:
                success = True  # No action needed

            if success:
                self.last_scaling_actions[service_name] = {
                    'timestamp': datetime.utcnow(),
                    'action': prediction.scaling_action,
                    'instances_before': current_instances,
                    'instances_after': target_instances
                }

                # Log scaling action
                await self._log_scaling_event(service_name, prediction, current_instances, target_instances)

            return success

        except Exception as e:
            logger.error(f"Error executing scaling action for {service_name}: {e}")
            return False

    async def _get_current_instances(self, service_name: str) -> int:
        """Get current number of instances for a service"""
        # Mock implementation - replace with actual cloud provider API
        return np.random.randint(2, 10)

    async def _scale_up(self, service_name: str, current: int, target: int) -> bool:
        """Scale up service instances"""
        logger.info(f"Scaling up {service_name} from {current} to {target} instances")
        # TODO: Implement actual cloud provider scaling
        return True

    async def _scale_down(self, service_name: str, current: int, target: int) -> bool:
        """Scale down service instances"""
        logger.info(f"Scaling down {service_name} from {current} to {target} instances")
        # TODO: Implement actual cloud provider scaling
        return True

    async def _log_scaling_event(self, service_name: str, prediction: ScalingPrediction,
                                before: int, after: int) -> None:
        """Log scaling event to database"""
        try:
            # Store in Redis for real-time monitoring
            event_data = {
                'service_name': service_name,
                'timestamp': datetime.utcnow().isoformat(),
                'scaling_action': prediction.scaling_action,
                'predicted_load': prediction.predicted_load,
                'confidence_score': prediction.confidence_score,
                'instances_before': before,
                'instances_after': after,
                'cost_estimate': prediction.cost_estimate,
                'risk_factors': prediction.risk_factors
            }

            self.redis_client.lpush(f'scaling_events:{service_name}', json.dumps(event_data))
            self.redis_client.expire(f'scaling_events:{service_name}', 86400)  # Keep for 24 hours

            # Store in database for historical analysis
            # TODO: Implement database logging

        except Exception as e:
            logger.error(f"Error logging scaling event: {e}")

    async def run_predictive_scaling(self):
        """Main predictive scaling loop"""
        logger.info("Starting predictive scaling system")

        while True:
            try:
                for policy in self.scaling_policies:
                    # Collect metrics
                    metrics = await self.collect_metrics(policy.service_name)
                    if not metrics:
                        continue

                    # Generate predictions
                    predictions = await self.predict_scaling_needs(policy.service_name, metrics)

                    # Use medium-term prediction for scaling decisions
                    medium_term_prediction = predictions[1]

                    # Check if scaling is needed
                    if medium_term_prediction.confidence_score > 0.7:
                        await self.execute_scaling_action(
                            policy.service_name,
                            medium_term_prediction,
                            policy
                        )

                    # Store metrics for model training
                    await self._store_metrics(policy.service_name, metrics)

                # Wait for next iteration
                await asyncio.sleep(self.config['prediction_interval'])

            except Exception as e:
                logger.error(f"Error in predictive scaling loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _store_metrics(self, service_name: str, metrics: ScalingMetrics) -> None:
        """Store metrics for historical analysis and model training"""
        try:
            metrics_data = asdict(metrics)
            metrics_data['timestamp'] = metrics_data['timestamp'].isoformat()

            # Store in Redis time series
            self.redis_client.lpush(f'metrics:{service_name}', json.dumps(metrics_data))
            self.redis_client.ltrim(f'metrics:{service_name}', 0, 10000)  # Keep last 10k records

            # TODO: Store in database for long-term retention

        except Exception as e:
            logger.error(f"Error storing metrics: {e}")

    async def train_models_periodically(self):
        """Periodically retrain prediction models with new data"""
        logger.info("Starting periodic model training")

        while True:
            try:
                # Collect historical data for all services
                all_metrics = []

                for policy in self.scaling_policies:
                    service_metrics = await self._get_historical_metrics(policy.service_name)
                    all_metrics.extend(service_metrics)

                if len(all_metrics) > 1000:  # Need minimum data for training
                    # Retrain models
                    results = self.prediction_model.train(all_metrics)
                    logger.info(f"Model retraining completed: {results}")

                # Wait for next training (daily)
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error(f"Error in periodic model training: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying

    async def _get_historical_metrics(self, service_name: str) -> List[ScalingMetrics]:
        """Get historical metrics for a service"""
        try:
            # Get from Redis
            metrics_data = self.redis_client.lrange(f'metrics:{service_name}', 0, -1)

            metrics = []
            for data in metrics_data:
                data_dict = json.loads(data)
                data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
                metrics.append(ScalingMetrics(**data_dict))

            return metrics

        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []

    async def get_scaling_dashboard_data(self) -> Dict:
        """Get data for scaling dashboard"""
        dashboard_data = {
            'services': [],
            'recent_events': [],
            'predictions': []
        }

        for policy in self.scaling_policies:
            # Get current metrics
            metrics = await self.collect_metrics(policy.service_name)
            if metrics:
                service_data = {
                    'name': policy.service_name,
                    'current_instances': metrics.current_instances,
                    'cpu_utilization': metrics.cpu_utilization,
                    'memory_utilization': metrics.memory_utilization,
                    'request_rate': metrics.request_rate,
                    'response_time': metrics.response_time,
                    'error_rate': metrics.error_rate
                }

                # Get predictions
                predictions = await self.predict_scaling_needs(policy.service_name, metrics)
                service_data['predictions'] = [
                    {
                        'horizon': p.time_horizon.total_seconds() / 3600,
                        'predicted_load': p.predicted_load,
                        'confidence': p.confidence_score,
                        'recommended_instances': p.recommended_instances,
                        'action': p.scaling_action
                    }
                    for p in predictions
                ]

                dashboard_data['services'].append(service_data)

            # Get recent scaling events
            events = self.redis_client.lrange(f'scaling_events:{policy.service_name}', 0, 9)
            for event in events:
                event_data = json.loads(event)
                dashboard_data['recent_events'].append(event_data)

        return dashboard_data

async def main():
    """Main entry point"""
    scaling_system = AutoScalingAI()

    # Start concurrent tasks
    tasks = [
        asyncio.create_task(scaling_system.run_predictive_scaling()),
        asyncio.create_task(scaling_system.train_models_periodically())
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down auto-scaling system")
        for task in tasks:
            task.cancel()

if __name__ == "__main__":
    asyncio.run(main())