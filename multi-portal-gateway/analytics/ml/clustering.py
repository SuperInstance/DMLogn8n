#!/usr/bin/env python3
"""
User Clustering
Machine learning models for user segmentation and clustering
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
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import joblib
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..analytics_engine import AnalyticsConfig


@dataclass
class ClusterModel:
    """Clustering model configuration"""
    model_id: str
    name: str
    algorithm: str  # 'kmeans', 'dbscan', 'hierarchical'
    features: List[str]
    n_clusters: Optional[int] = None
    hyperparameters: Dict[str, Any] = None
    training_frequency: str = 'weekly'
    enabled: bool = True
    last_trained: Optional[datetime] = None
    performance_metrics: Dict[str, float] = None


@dataclass
class UserSegment:
    """User segment definition"""
    segment_id: str
    segment_name: str
    cluster_id: int
    size: int
    percentage: float
    characteristics: Dict[str, Any]
    behavior_patterns: Dict[str, Any]
    recommended_actions: List[str]


@dataclass
class UserClusterAssignment:
    """User's cluster assignment"""
    user_id: str
    model_id: str
    cluster_id: int
    confidence_score: float
    assigned_at: datetime
    features: Dict[str, Any]


class UserClustering:
    """User segmentation and clustering engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Clustering models and preprocessors
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.cluster_labels = {}
        self.user_assignments = {}

        # Initialize database tables
        self._initialize_tables()

        # Initialize default clustering models
        self._initialize_default_models()

    def _setup_logging(self) -> logging.Logger:
        """Setup user clustering logging"""
        logger = logging.getLogger("user_clustering")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for user clustering"""
        try:
            # Create cluster_models table
            create_models_table = """
            CREATE TABLE IF NOT EXISTS cluster_models (
                model_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                algorithm VARCHAR(50) NOT NULL,
                features TEXT,
                n_clusters INTEGER,
                hyperparameters TEXT,
                training_frequency VARCHAR(20),
                enabled BOOLEAN DEFAULT TRUE,
                last_trained TIMESTAMP,
                performance_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create user_segments table
            create_segments_table = """
            CREATE TABLE IF NOT EXISTS user_segments (
                segment_id VARCHAR(100) PRIMARY KEY,
                model_id VARCHAR(100) NOT NULL,
                cluster_id INTEGER NOT NULL,
                segment_name VARCHAR(200) NOT NULL,
                size INTEGER DEFAULT 0,
                percentage DECIMAL(5,4),
                characteristics TEXT,
                behavior_patterns TEXT,
                recommended_actions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES cluster_models(model_id)
            );
            """

            # Create user_cluster_assignments table
            create_assignments_table = """
            CREATE TABLE IF NOT EXISTS user_cluster_assignments (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                model_id VARCHAR(100) NOT NULL,
                cluster_id INTEGER NOT NULL,
                confidence_score DECIMAL(5,4),
                assigned_at TIMESTAMP NOT NULL,
                features TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES cluster_models(model_id),
                UNIQUE(user_id, model_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_assignments_user_id ON user_cluster_assignments(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_assignments_model_id ON user_cluster_assignments(model_id);",
                "CREATE INDEX IF NOT EXISTS idx_assignments_cluster_id ON user_cluster_assignments(cluster_id);",
                "CREATE INDEX IF NOT EXISTS idx_segments_model_id ON user_segments(model_id);",
                "CREATE INDEX IF NOT EXISTS idx_segments_cluster_id ON user_segments(cluster_id);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_models_table))
                conn.execute(text(create_segments_table))
                conn.execute(text(create_assignments_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("User clustering tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing user clustering tables: {e}")

    def _initialize_default_models(self):
        """Initialize default clustering models"""
        default_models = [
            ClusterModel(
                model_id="engagement_based",
                name="Engagement-Based User Segmentation",
                algorithm="kmeans",
                features=[
                    "session_frequency", "avg_session_duration", "pages_per_session",
                    "days_since_last_session", "feature_adoption_rate", "social_interactions",
                    "engagement_score", "retention_probability"
                ],
                n_clusters=5,
                hyperparameters={"n_init": 10, "max_iter": 300, "random_state": 42},
                training_frequency="weekly"
            ),
            ClusterModel(
                model_id="value_based",
                name="Value-Based User Segmentation",
                algorithm="kmeans",
                features=[
                    "lifetime_value", "total_revenue", "avg_order_value",
                    "purchase_frequency", "days_since_first_purchase", "product_categories",
                    "return_rate", "support_interactions"
                ],
                n_clusters=4,
                hyperparameters={"n_init": 15, "max_iter": 500, "random_state": 42},
                training_frequency="weekly"
            ),
            ClusterModel(
                model_id="behavioral",
                name="Behavioral User Segmentation",
                algorithm="dbscan",
                features=[
                    "login_pattern_regularity", "preferred_features", "content_consumption",
                    "peer_interactions", "achievement_progress", "time_of_day_activity",
                    "device_preference", "session_length_variance"
                ],
                n_clusters=None,  # DBSCAN determines clusters automatically
                hyperparameters={"eps": 0.5, "min_samples": 5},
                training_frequency="monthly"
            ),
            ClusterModel(
                model_id="lifecycle",
                name="Customer Lifecycle Segmentation",
                algorithm="hierarchical",
                features=[
                    "account_age", "days_since_first_session", "activity_trend",
                    "feature_adoption_over_time", "support_tickets", "upgrade_events",
                    "referral_count", "churn_risk_score"
                ],
                n_clusters=6,
                hyperparameters={"n_clusters": 6, "linkage": "ward"},
                training_frequency="monthly"
            )
        ]

        for model in default_models:
            self.add_model(model)

    def add_model(self, model: ClusterModel):
        """Add a clustering model"""
        try:
            # Store in database
            query = text("""
                INSERT INTO cluster_models (
                    model_id, name, algorithm, features, n_clusters,
                    hyperparameters, training_frequency, enabled
                ) VALUES (
                    :model_id, :name, :algorithm, :features, :n_clusters,
                    :hyperparameters, :training_frequency, :enabled
                )
                ON CONFLICT (model_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    algorithm = EXCLUDED.algorithm,
                    features = EXCLUDED.features,
                    n_clusters = EXCLUDED.n_clusters,
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
                    'n_clusters': model.n_clusters,
                    'hyperparameters': json.dumps(model.hyperparameters),
                    'training_frequency': model.training_frequency,
                    'enabled': model.enabled
                })
                conn.commit()

            self.models[model.model_id] = model
            self.logger.info(f"Added clustering model: {model.name}")

        except Exception as e:
            self.logger.error(f"Error adding clustering model: {e}")

    async def train_clustering_model(self, model_id: str, force_retrain: bool = False) -> Dict[str, Any]:
        """Train a clustering model"""
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

            self.logger.info(f"Training clustering model: {model.name}")

            # Get user data for clustering
            user_data = await self._get_user_data_for_clustering(model)
            if user_data.empty:
                raise ValueError(f"No user data available for clustering model {model_id}")

            # Prepare features
            features_matrix = self._prepare_clustering_features(user_data, model)

            if features_matrix.shape[0] < model.n_clusters:
                raise ValueError(f"Insufficient data for {model.n_clusters} clusters")

            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features_matrix)

            # Determine optimal number of clusters if not specified
            if model.n_clusters is None:
                optimal_k = await self._find_optimal_clusters(features_scaled, model.algorithm)
                model.n_clusters = optimal_k

            # Train clustering algorithm
            clustering_model = self._train_clustering_algorithm(model, features_scaled)

            # Evaluate clustering
            performance_metrics = self._evaluate_clustering(features_scaled, clustering_model.labels_)

            # Assign clusters to users
            cluster_assignments = self._assign_users_to_clusters(
                user_data.index.tolist(), clustering_model.labels_
            )

            # Create user segments
            segments = await self._create_user_segments(model, cluster_assignments, user_data)

            # Store results
            await self._store_clustering_results(model_id, clustering_model, scaler, segments, cluster_assignments)

            # Update model metadata
            model.last_trained = datetime.utcnow()
            model.performance_metrics = performance_metrics
            await self._update_model_metadata(model)

            # Cache model
            await self._cache_clustering_model(model_id, clustering_model, scaler)

            self.logger.info(f"Clustering model trained successfully: {model.name}")

            return {
                'status': 'success',
                'model_id': model_id,
                'n_clusters': model.n_clusters,
                'performance_metrics': performance_metrics,
                'users_clustered': len(cluster_assignments),
                'segments_created': len(segments)
            }

        except Exception as e:
            self.logger.error(f"Error training clustering model {model_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def assign_user_to_cluster(self, user_id: str, model_id: str) -> Optional[UserClusterAssignment]:
        """Assign a user to a cluster"""
        try:
            # Get clustering model
            clustering_model = self.models.get(f"{model_id}_trained")
            if not clustering_model:
                clustering_model = await self._load_cached_clustering_model(model_id)
                if not clustering_model:
                    raise ValueError(f"Model not trained: {model_id}")

            # Get user features
            user_features = await self._get_user_features(user_id)
            model_config = self.models.get(model_id)
            if not model_config:
                raise ValueError(f"Model configuration not found: {model_id}")

            # Prepare features
            feature_vector = self._prepare_user_features(user_features, model_config.features)
            feature_df = pd.DataFrame([feature_vector])

            # Scale features
            scaler = self.scalers.get(model_id)
            if not scaler:
                scaler = await self._load_cached_scaler(model_id)

            if scaler:
                feature_scaled = scaler.transform(feature_df)
            else:
                feature_scaled = feature_df.values

            # Predict cluster
            cluster_id = clustering_model.predict(feature_scaled)[0]

            # Calculate confidence score
            confidence_score = self._calculate_cluster_confidence(
                feature_scaled, clustering_model, cluster_id
            )

            # Create assignment
            assignment = UserClusterAssignment(
                user_id=user_id,
                model_id=model_id,
                cluster_id=int(cluster_id),
                confidence_score=confidence_score,
                assigned_at=datetime.utcnow(),
                features=user_features
            )

            # Store assignment
            await self._store_user_assignment(assignment)

            return assignment

        except Exception as e:
            self.logger.error(f"Error assigning user {user_id} to cluster: {e}")
            return None

    async def get_user_segment(self, user_id: str, model_id: str = None) -> Optional[UserSegment]:
        """Get user's segment information"""
        try:
            if model_id is None:
                # Get from most recent model
                model_id = list(self.models.keys())[0]

            # Get user's cluster assignment
            assignment = await self._get_user_assignment(user_id, model_id)
            if not assignment:
                return None

            # Get segment information
            segment = await self._get_segment_info(model_id, assignment.cluster_id)
            return segment

        except Exception as e:
            self.logger.error(f"Error getting user segment: {e}")
            return None

    async def get_segment_analysis(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive segment analysis"""
        try:
            # Get all segments for the model
            segments = await self._get_model_segments(model_id)

            analysis = {
                'model_id': model_id,
                'total_segments': len(segments),
                'segments': [],
                'segment_comparison': {}
            }

            total_users = sum(segment.size for segment in segments)

            for segment in segments:
                segment_data = {
                    'segment_id': segment.segment_id,
                    'segment_name': segment.segment_name,
                    'cluster_id': segment.cluster_id,
                    'size': segment.size,
                    'percentage': (segment.size / total_users) * 100 if total_users > 0 else 0,
                    'characteristics': segment.characteristics,
                    'behavior_patterns': segment.behavior_patterns,
                    'recommended_actions': segment.recommended_actions
                }
                analysis['segments'].append(segment_data)

            # Compare segments
            analysis['segment_comparison'] = await self._compare_segments(segments)

            return analysis

        except Exception as e:
            self.logger.error(f"Error getting segment analysis: {e}")
            return {}

    async def update_clusters(self):
        """Update all clustering models"""
        try:
            self.logger.info("Updating clustering models...")

            results = {}
            for model_id, model in self.models.items():
                if isinstance(model, ClusterModel) and model.enabled:
                    try:
                        result = await self.train_clustering_model(model_id)
                        results[model_id] = result
                    except Exception as e:
                        self.logger.error(f"Error updating clustering model {model_id}: {e}")
                        results[model_id] = {'status': 'error', 'error': str(e)}

            successful = sum(1 for r in results.values() if r.get('status') == 'success')
            self.logger.info(f"Clustering updates completed: {successful} successful, {len(results) - successful} failed")

            return results

        except Exception as e:
            self.logger.error(f"Error updating clusters: {e}")
            raise

    # Private methods

    async def _get_user_data_for_clustering(self, model: ClusterModel) -> pd.DataFrame:
        """Get user data for clustering"""
        try:
            # Mock implementation - would typically query user analytics database
            np.random.seed(42)
            n_users = 5000

            data = {}
            for feature in model.features:
                if feature.endswith('_frequency') or feature.endswith('_count'):
                    data[feature] = np.random.randint(1, 100, n_users)
                elif feature.endswith('_duration') or feature.endswith('_value'):
                    data[feature] = np.random.uniform(0, 1000, n_users)
                elif feature.endswith('_rate') or feature.endswith('_probability') or feature.endswith('_score'):
                    data[feature] = np.random.uniform(0, 1, n_users)
                elif feature.endswith('_days') or feature.endswith('_age'):
                    data[feature] = np.random.randint(1, 365, n_users)
                else:
                    data[feature] = np.random.uniform(0, 100, n_users)

            # Create user IDs
            user_ids = [f"user_{i:06d}" for i in range(n_users)]
            df = pd.DataFrame(data, index=user_ids)

            return df

        except Exception as e:
            self.logger.error(f"Error getting user data for clustering: {e}")
            return pd.DataFrame()

    def _prepare_clustering_features(self, data: pd.DataFrame, model: ClusterModel) -> np.ndarray:
        """Prepare features for clustering"""
        try:
            # Select features
            features_data = data[model.features].copy()

            # Handle missing values
            features_data = features_data.fillna(features_data.mean())

            # Handle categorical variables
            for column in features_data.columns:
                if features_data[column].dtype == 'object':
                    if column not in self.encoders:
                        encoder = LabelEncoder()
                        features_data[column] = encoder.fit_transform(features_data[column].astype(str))
                        self.encoders[column] = encoder
                    else:
                        features_data[column] = self.encoders[column].transform(features_data[column].astype(str))

            return features_data.values

        except Exception as e:
            self.logger.error(f"Error preparing clustering features: {e}")
            return np.array([])

    async def _find_optimal_clusters(self, features: np.ndarray, algorithm: str) -> int:
        """Find optimal number of clusters"""
        try:
            if algorithm == 'dbscan':
                # DBSCAN determines clusters automatically
                return None

            # Test range of cluster numbers
            k_range = range(2, 11)
            silhouette_scores = []
            calinski_scores = []

            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(features)

                if len(set(labels)) > 1:  # Avoid single cluster
                    sil_score = silhouette_score(features, labels)
                    ch_score = calinski_harabasz_score(features, labels)
                    silhouette_scores.append(sil_score)
                    calinski_scores.append(ch_score)
                else:
                    silhouette_scores.append(0)
                    calinski_scores.append(0)

            # Find optimal k based on silhouette score
            optimal_k = k_range[np.argmax(silhouette_scores)]
            return optimal_k

        except Exception as e:
            self.logger.error(f"Error finding optimal clusters: {e}")
            return 5  # Default to 5 clusters

    def _train_clustering_algorithm(self, model: ClusterModel, features: np.ndarray):
        """Train clustering algorithm"""
        try:
            hyperparameters = model.hyperparameters or {}

            if model.algorithm == "kmeans":
                return KMeans(n_clusters=model.n_clusters, **hyperparameters)
            elif model.algorithm == "dbscan":
                return DBSCAN(**hyperparameters)
            elif model.algorithm == "hierarchical":
                return AgglomerativeClustering(n_clusters=model.n_clusters, **hyperparameters)
            else:
                raise ValueError(f"Unknown clustering algorithm: {model.algorithm}")

        except Exception as e:
            self.logger.error(f"Error training clustering algorithm: {e}")
            raise

    def _evaluate_clustering(self, features: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """Evaluate clustering performance"""
        try:
            if len(set(labels)) <= 1:
                return {'silhouette_score': 0, 'calinski_harabasz_score': 0, 'inertia': 0}

            silhouette_avg = silhouette_score(features, labels)
            ch_score = calinski_harabasz_score(features, labels)

            metrics = {
                'silhouette_score': silhouette_avg,
                'calinski_harabasz_score': ch_score
            }

            # Add inertia for K-means
            if hasattr(self, '_current_model') and hasattr(self._current_model, 'inertia_'):
                metrics['inertia'] = self._current_model.inertia_

            return metrics

        except Exception as e:
            self.logger.error(f"Error evaluating clustering: {e}")
            return {}

    def _assign_users_to_clusters(self, user_ids: List[str], labels: np.ndarray) -> Dict[int, List[str]]:
        """Assign users to clusters"""
        try:
            assignments = defaultdict(list)
            for user_id, label in zip(user_ids, labels):
                assignments[int(label)].append(user_id)
            return dict(assignments)

        except Exception as e:
            self.logger.error(f"Error assigning users to clusters: {e}")
            return {}

    async def _create_user_segments(self, model: ClusterModel,
                                 cluster_assignments: Dict[int, List[str]],
                                 user_data: pd.DataFrame) -> List[UserSegment]:
        """Create user segments from clusters"""
        try:
            segments = []

            for cluster_id, user_ids in cluster_assignments.items():
                # Get user data for this cluster
                cluster_data = user_data.loc[user_ids]

                # Calculate segment characteristics
                characteristics = self._calculate_segment_characteristics(cluster_data, model.features)

                # Analyze behavior patterns
                behavior_patterns = self._analyze_behavior_patterns(cluster_data)

                # Generate recommended actions
                recommended_actions = self._generate_recommended_actions(characteristics, behavior_patterns)

                # Create segment
                segment = UserSegment(
                    segment_id=f"{model.model_id}_cluster_{cluster_id}",
                    segment_name=self._generate_segment_name(characteristics),
                    cluster_id=cluster_id,
                    size=len(user_ids),
                    percentage=0,  # Will be calculated later
                    characteristics=characteristics,
                    behavior_patterns=behavior_patterns,
                    recommended_actions=recommended_actions
                )

                segments.append(segment)

            # Calculate percentages
            total_users = sum(segment.size for segment in segments)
            for segment in segments:
                segment.percentage = (segment.size / total_users) * 100 if total_users > 0 else 0

            return segments

        except Exception as e:
            self.logger.error(f"Error creating user segments: {e}")
            return []

    def _calculate_segment_characteristics(self, cluster_data: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
        """Calculate segment characteristics"""
        try:
            characteristics = {}

            for feature in features:
                if feature in cluster_data.columns:
                    feature_data = cluster_data[feature]

                    if feature_data.dtype in ['float64', 'int64']:
                        characteristics[feature] = {
                            'mean': float(feature_data.mean()),
                            'median': float(feature_data.median()),
                            'std': float(feature_data.std()),
                            'min': float(feature_data.min()),
                            'max': float(feature_data.max())
                        }
                    else:
                        value_counts = feature_data.value_counts()
                        characteristics[feature] = {
                            'top_values': value_counts.head().to_dict(),
                            'distribution': (value_counts / len(feature_data)).to_dict()
                        }

            return characteristics

        except Exception as e:
            self.logger.error(f"Error calculating segment characteristics: {e}")
            return {}

    def _analyze_behavior_patterns(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze behavior patterns for a segment"""
        try:
            patterns = {}

            # Engagement patterns
            if 'engagement_score' in cluster_data.columns:
                engagement = cluster_data['engagement_score']
                patterns['engagement_level'] = 'high' if engagement.mean() > 0.7 else 'medium' if engagement.mean() > 0.4 else 'low'

            # Activity patterns
            if 'session_frequency' in cluster_data.columns:
                frequency = cluster_data['session_frequency']
                patterns['activity_level'] = 'high' if frequency.mean() > 50 else 'medium' if frequency.mean() > 20 else 'low'

            # Value patterns
            if 'lifetime_value' in cluster_data.columns:
                ltv = cluster_data['lifetime_value']
                patterns['value_level'] = 'high' if ltv.mean() > 500 else 'medium' if ltv.mean() > 100 else 'low'

            # Churn risk patterns
            if 'churn_risk_score' in cluster_data.columns:
                churn_risk = cluster_data['churn_risk_score']
                patterns['churn_risk'] = 'high' if churn_risk.mean() > 0.7 else 'medium' if churn_risk.mean() > 0.4 else 'low'

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing behavior patterns: {e}")
            return {}

    def _generate_recommended_actions(self, characteristics: Dict[str, Any],
                                    behavior_patterns: Dict[str, Any]) -> List[str]:
        """Generate recommended actions for a segment"""
        try:
            actions = []

            # Based on engagement level
            engagement = behavior_patterns.get('engagement_level', 'medium')
            if engagement == 'low':
                actions.extend([
                    "Send re-engagement campaigns",
                    "Offer personalized content recommendations",
                    "Provide onboarding assistance"
                ])
            elif engagement == 'high':
                actions.extend([
                    "Offer premium features",
                    "Encourage social sharing",
                    "Provide early access to new features"
                ])

            # Based on value level
            value = behavior_patterns.get('value_level', 'medium')
            if value == 'high':
                actions.extend([
                    "Provide VIP support",
                    "Offer exclusive benefits",
                    "Create loyalty programs"
                ])
            elif value == 'low':
                actions.extend([
                    "Send special offers",
                    "Provide product education",
                    "Improve onboarding experience"
                ])

            # Based on churn risk
            churn_risk = behavior_patterns.get('churn_risk', 'medium')
            if churn_risk == 'high':
                actions.extend([
                    "Immediate retention interventions",
                    "Personal outreach from success team",
                    "Offer retention incentives"
                ])

            return actions[:5]  # Limit to top 5 actions

        except Exception as e:
            self.logger.error(f"Error generating recommended actions: {e}")
            return []

    def _generate_segment_name(self, characteristics: Dict[str, Any]) -> str:
        """Generate a descriptive name for the segment"""
        try:
            # Simple naming logic based on key characteristics
            if 'engagement_score' in characteristics:
                engagement = characteristics['engagement_score']['mean']
                if engagement > 0.7:
                    return "Highly Engaged Users"
                elif engagement < 0.3:
                    return "Low Engagement Users"

            if 'lifetime_value' in characteristics:
                ltv = characteristics['lifetime_value']['mean']
                if ltv > 500:
                    return "High Value Customers"
                elif ltv < 100:
                    return "Low Value Customers"

            if 'session_frequency' in characteristics:
                freq = characteristics['session_frequency']['mean']
                if freq > 50:
                    return "Power Users"
                elif freq < 10:
                    return "Casual Users"

            return "General Users"

        except Exception:
            return "Unnamed Segment"

    def _prepare_user_features(self, user_features: Dict[str, Any], required_features: List[str]) -> Dict[str, Any]:
        """Prepare user features for clustering"""
        try:
            prepared_features = {}

            for feature in required_features:
                if feature in user_features:
                    value = user_features[feature]
                else:
                    # Use default values for missing features
                    if feature.endswith('_frequency') or feature.endswith('_count'):
                        value = 1
                    elif feature.endswith('_duration') or feature.endswith('_value'):
                        value = 0.0
                    elif feature.endswith('_rate') or feature.endswith('_probability') or feature.endswith('_score'):
                        value = 0.5
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
            self.logger.error(f"Error preparing user features: {e}")
            return {}

    def _calculate_cluster_confidence(self, features: np.ndarray, model, cluster_id: int) -> float:
        """Calculate confidence score for cluster assignment"""
        try:
            if hasattr(model, 'transform'):  # For K-means
                distances = model.transform(features)
                distance_to_assigned = distances[0][cluster_id]
                distance_to_closest = np.min(distances[0])

                if distance_to_assigned == distance_to_closest:
                    return 1.0
                else:
                    return 1.0 / (1.0 + (distance_to_assigned - distance_to_closest))
            else:
                return 0.8  # Default confidence

        except Exception:
            return 0.5  # Default confidence on error

    async def _store_clustering_results(self, model_id: str, model, scaler,
                                      segments: List[UserSegment],
                                      cluster_assignments: Dict[int, List[str]]):
        """Store clustering results"""
        try:
            # Store model and scaler
            self.models[f"{model_id}_trained"] = model
            self.scalers[model_id] = scaler

            # Store segments
            for segment in segments:
                await self._store_segment(segment)

            # Store user assignments
            for cluster_id, user_ids in cluster_assignments.items():
                for user_id in user_ids:
                    assignment = UserClusterAssignment(
                        user_id=user_id,
                        model_id=model_id,
                        cluster_id=cluster_id,
                        confidence_score=0.8,  # Default confidence
                        assigned_at=datetime.utcnow(),
                        features={}  # Would include actual features
                    )
                    await self._store_user_assignment(assignment)

        except Exception as e:
            self.logger.error(f"Error storing clustering results: {e}")

    async def _store_segment(self, segment: UserSegment):
        """Store segment in database"""
        try:
            query = text("""
                INSERT INTO user_segments (
                    segment_id, model_id, cluster_id, segment_name, size, percentage,
                    characteristics, behavior_patterns, recommended_actions
                ) VALUES (
                    :segment_id, :model_id, :cluster_id, :segment_name, :size, :percentage,
                    :characteristics, :behavior_patterns, :recommended_actions
                )
                ON CONFLICT (segment_id) DO UPDATE SET
                    segment_name = EXCLUDED.segment_name,
                    size = EXCLUDED.size,
                    percentage = EXCLUDED.percentage,
                    characteristics = EXCLUDED.characteristics,
                    behavior_patterns = EXCLUDED.behavior_patterns,
                    recommended_actions = EXCLUDED.recommended_actions,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'segment_id': segment.segment_id,
                    'model_id': segment.segment_id.split('_cluster_')[0],
                    'cluster_id': segment.cluster_id,
                    'segment_name': segment.segment_name,
                    'size': segment.size,
                    'percentage': segment.percentage,
                    'characteristics': json.dumps(segment.characteristics),
                    'behavior_patterns': json.dumps(segment.behavior_patterns),
                    'recommended_actions': json.dumps(segment.recommended_actions)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing segment: {e}")

    async def _store_user_assignment(self, assignment: UserClusterAssignment):
        """Store user cluster assignment"""
        try:
            query = text("""
                INSERT INTO user_cluster_assignments (
                    user_id, model_id, cluster_id, confidence_score, assigned_at, features
                ) VALUES (
                    :user_id, :model_id, :cluster_id, :confidence_score, :assigned_at, :features
                )
                ON CONFLICT (user_id, model_id) DO UPDATE SET
                    cluster_id = EXCLUDED.cluster_id,
                    confidence_score = EXCLUDED.confidence_score,
                    assigned_at = EXCLUDED.assigned_at,
                    features = EXCLUDED.features
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'user_id': assignment.user_id,
                    'model_id': assignment.model_id,
                    'cluster_id': assignment.cluster_id,
                    'confidence_score': assignment.confidence_score,
                    'assigned_at': assignment.assigned_at,
                    'features': json.dumps(assignment.features)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing user assignment: {e}")

    async def _update_model_metadata(self, model: ClusterModel):
        """Update model metadata in database"""
        try:
            query = text("""
                UPDATE cluster_models
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

    async def _cache_clustering_model(self, model_id: str, model, scaler):
        """Cache clustering model in Redis"""
        try:
            model_data = {
                'model_type': type(model).__name__,
                'n_clusters': getattr(model, 'n_clusters', None),
                'cached_at': datetime.utcnow().isoformat()
            }

            await self.redis_client.setex(
                f"clustering_model:{model_id}",
                86400,  # 24 hours TTL
                json.dumps(model_data)
            )

        except Exception as e:
            self.logger.error(f"Error caching clustering model: {e}")

    async def _load_cached_clustering_model(self, model_id: str):
        """Load clustering model from cache"""
        try:
            cached_data = await self.redis_client.get(f"clustering_model:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached clustering model: {e}")
            return None

    async def _load_cached_scaler(self, model_id: str):
        """Load scaler from cache"""
        try:
            cached_data = await self.redis_client.get(f"scaler:{model_id}")
            if cached_data:
                data = json.loads(cached_data)
                return data
            return None

        except Exception as e:
            self.logger.error(f"Error loading cached scaler: {e}")
            return None

    async def _get_user_assignment(self, user_id: str, model_id: str) -> Optional[UserClusterAssignment]:
        """Get user's cluster assignment"""
        try:
            query = text("""
                SELECT * FROM user_cluster_assignments
                WHERE user_id = :user_id AND model_id = :model_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'user_id': user_id,
                    'model_id': model_id
                })
                row = result.fetchone()

                if row:
                    return UserClusterAssignment(
                        user_id=row.user_id,
                        model_id=row.model_id,
                        cluster_id=row.cluster_id,
                        confidence_score=row.confidence_score,
                        assigned_at=row.assigned_at,
                        features=json.loads(row.features) if row.features else {}
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error getting user assignment: {e}")
            return None

    async def _get_segment_info(self, model_id: str, cluster_id: int) -> Optional[UserSegment]:
        """Get segment information"""
        try:
            query = text("""
                SELECT * FROM user_segments
                WHERE model_id = :model_id AND cluster_id = :cluster_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'model_id': model_id,
                    'cluster_id': cluster_id
                })
                row = result.fetchone()

                if row:
                    return UserSegment(
                        segment_id=row.segment_id,
                        segment_name=row.segment_name,
                        cluster_id=row.cluster_id,
                        size=row.size,
                        percentage=row.percentage,
                        characteristics=json.loads(row.characteristics) if row.characteristics else {},
                        behavior_patterns=json.loads(row.behavior_patterns) if row.behavior_patterns else {},
                        recommended_actions=json.loads(row.recommended_actions) if row.recommended_actions else []
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error getting segment info: {e}")
            return None

    async def _get_model_segments(self, model_id: str) -> List[UserSegment]:
        """Get all segments for a model"""
        try:
            query = text("""
                SELECT * FROM user_segments WHERE model_id = :model_id
                ORDER BY size DESC
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'model_id': model_id})
                rows = result.fetchall()

            segments = []
            for row in rows:
                segment = UserSegment(
                    segment_id=row.segment_id,
                    segment_name=row.segment_name,
                    cluster_id=row.cluster_id,
                    size=row.size,
                    percentage=row.percentage,
                    characteristics=json.loads(row.characteristics) if row.characteristics else {},
                    behavior_patterns=json.loads(row.behavior_patterns) if row.behavior_patterns else {},
                    recommended_actions=json.loads(row.recommended_actions) if row.recommended_actions else []
                )
                segments.append(segment)

            return segments

        except Exception as e:
            self.logger.error(f"Error getting model segments: {e}")
            return []

    async def _compare_segments(self, segments: List[UserSegment]) -> Dict[str, Any]:
        """Compare segments across different dimensions"""
        try:
            comparison = {
                'size_distribution': {},
                'key_differences': [],
                'common_characteristics': {}
            }

            # Size distribution
            total_size = sum(segment.size for segment in segments)
            for segment in segments:
                comparison['size_distribution'][segment.segment_name] = segment.percentage

            # Find key differences (simplified)
            if len(segments) >= 2:
                largest = max(segments, key=lambda s: s.size)
                smallest = min(segments, key=lambda s: s.size)

                comparison['key_differences'] = [
                    f"Largest segment '{largest.segment_name}' has {largest.size} users ({largest.percentage:.1f}%)",
                    f"Smallest segment '{smallest.segment_name}' has {smallest.size} users ({smallest.percentage:.1f}%)"
                ]

            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing segments: {e}")
            return {}

    async def _get_user_features(self, user_id: str) -> Dict[str, Any]:
        """Get features for a specific user"""
        try:
            # Mock implementation - would typically query user analytics data
            return {
                'session_frequency': 25,
                'avg_session_duration': 1200,
                'pages_per_session': 8,
                'days_since_last_session': 2,
                'feature_adoption_rate': 0.75,
                'social_interactions': 15,
                'engagement_score': 0.8,
                'lifetime_value': 250.0,
                'total_revenue': 180.0,
                'avg_order_value': 45.0,
                'purchase_frequency': 4,
                'days_since_first_purchase': 30,
                'return_rate': 0.1,
                'support_interactions': 2
            }

        except Exception as e:
            self.logger.error(f"Error getting user features: {e}")
            return {}