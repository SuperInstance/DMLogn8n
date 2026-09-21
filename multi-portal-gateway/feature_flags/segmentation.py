#!/usr/bin/env python3
"""
DMLogn8n User Segmentation Service
Provides advanced user segmentation and targeting capabilities for feature flags and experiments
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import redis
import aioredis
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import yaml
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SegmentType(Enum):
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    GEOGRAPHIC = "geographic"
    PSYCHOGRAPHIC = "psychographic"
    TECHNICAL = "technical"
    CUSTOM = "custom"
    MACHINE_LEARNING = "machine_learning"

class Operator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    BETWEEN = "between"

class LogicOperator(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"

@dataclass
class SegmentRule:
    field: str
    operator: Operator
    value: Any
    weight: float = 1.0

@dataclass
class SegmentCondition:
    rules: List[SegmentRule]
    logic_operator: LogicOperator = LogicOperator.AND

@dataclass
class UserSegment:
    id: str
    name: str
    description: str
    segment_type: SegmentType
    conditions: List[SegmentCondition]
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    user_count: int = 0
    last_calculated: Optional[datetime] = None

@dataclass
class UserProfile:
    user_id: str
    demographics: Dict[str, Any] = field(default_factory=dict)
    behavior: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    technical: Dict[str, Any] = field(default_factory=dict)
    geographic: Dict[str, Any] = field(default_factory=dict)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    segments: Set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    calculated_features: Dict[str, float] = field(default_factory=dict)

@dataclass
class BehavioralMetric:
    name: str
    value: float
    trend: str  # "increasing", "decreasing", "stable"
    confidence: float
    last_updated: datetime

class SegmentationRequest(BaseModel):
    user_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    include_ml_segments: bool = True
    recalculate: bool = False

class SegmentationResponse(BaseModel):
    user_id: str
    segments: List[str]
    profile: Dict[str, Any]
    confidence_scores: Dict[str, float]
    timestamp: datetime

class UserSegmentationService:
    """Advanced user segmentation service"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.segments: Dict[str, UserSegment] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.ml_models: Dict[str, Any] = {}
        self.segment_cache: Dict[str, Set[str]] = {}
        self.cache_ttl = 3600  # 1 hour

        # Event handlers
        self.segment_change_handlers: List[Callable] = []
        self.profile_update_handlers: List[Callable] = []

        # Load default segments
        self._load_default_segments()

    async def initialize(self):
        """Initialize the segmentation service"""
        try:
            # Initialize Redis clients
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.async_redis_client = aioredis.from_url(self.redis_url, decode_responses=True)

            # Load data from Redis
            await self._load_segments_from_redis()
            await self._load_user_profiles_from_redis()

            # Initialize ML models
            await self._initialize_ml_models()

            # Start background tasks
            asyncio.create_task(self._segment_calculation_task())
            asyncio.create_task(self._profile_update_task())
            asyncio.create_task(self._cache_cleanup_task())

            logger.info("User segmentation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize segmentation service: {e}")
            raise

    def _load_default_segments(self):
        """Load default user segments"""

        # Premium Users Segment
        premium_segment = UserSegment(
            id="premium_users",
            name="Premium Users",
            description="Users with active premium subscriptions",
            segment_type=SegmentType.DEMOGRAPHIC,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("is_premium", Operator.EQUALS, True)
                    ]
                )
            ],
            tags=["premium", "subscription"],
            priority=100
        )

        # Power Users Segment
        power_users_segment = UserSegment(
            id="power_users",
            name="Power Users",
            description="Highly active users with frequent engagement",
            segment_type=SegmentType.BEHAVIORAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("sessions_per_week", Operator.GREATER_THAN, 10),
                        SegmentRule("avg_session_duration", Operator.GREATER_THAN, 30),
                        SegmentRule("feature_usage_count", Operator.GREATER_THAN, 15)
                    ]
                )
            ],
            tags=["engagement", "activity"],
            priority=90
        )

        # New Users Segment
        new_users_segment = UserSegment(
            id="new_users",
            name="New Users",
            description="Users who joined in the last 7 days",
            segment_type=SegmentType.BEHAVIORAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("account_age_days", Operator.LESS_THAN, 7),
                        SegmentRule("completed_tutorial", Operator.EQUALS, True)
                    ]
                )
            ],
            tags=["onboarding", "new"],
            priority=80
        )

        # Mobile Users Segment
        mobile_users_segment = UserSegment(
            id="mobile_users",
            name="Mobile Users",
            description="Users primarily accessing from mobile devices",
            segment_type=SegmentType.TECHNICAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("primary_platform", Operator.EQUALS, "mobile"),
                        SegmentRule("mobile_app_installed", Operator.EQUALS, True)
                    ]
                )
            ],
            tags=["mobile", "platform"],
            priority=70
        )

        # Combat Enthusiasts Segment
        combat_enthusiasts = UserSegment(
            id="combat_enthusiasts",
            name="Combat Enthusiasts",
            description="Users who frequently engage in combat activities",
            segment_type=SegmentType.BEHAVIORAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("combat_sessions_per_week", Operator.GREATER_THAN, 5),
                        SegmentRule("combat_win_rate", Operator.GREATER_THAN, 0.6),
                        SegmentRule("preferred_gameplay_style", Operator.IN, ["combat", "mixed"])
                    ]
                )
            ],
            tags=["combat", "gameplay"],
            priority=85
        )

        # Story Lovers Segment
        story_lovers = UserSegment(
            id="story_lovers",
            name="Story Lovers",
            description="Users who prefer narrative-driven content",
            segment_type=SegmentType.PSYCHOGRAPHIC,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("dialogue_interactions", Operator.GREATER_THAN, 20),
                        SegmentRule("story_completion_rate", Operator.GREATER_THAN, 0.8),
                        SegmentRule("preferred_gameplay_style", Operator.IN, ["story", "exploration"])
                    ]
                )
            ],
            tags=["story", "narrative"],
            priority=75
        )

        # Beta Testers Segment
        beta_testers = UserSegment(
            id="beta_testers",
            name="Beta Testers",
            description="Users enrolled in beta testing program",
            segment_type=SegmentType.CUSTOM,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("is_beta_tester", Operator.EQUALS, True),
                        SegmentRule("bug_reports_submitted", Operator.GREATER_THAN, 0)
                    ]
                )
            ],
            tags=["beta", "testing"],
            priority=95
        )

        # High Spenders Segment
        high_spenders = UserSegment(
            id="high_spenders",
            name="High Spenders",
            description="Users with high monetary engagement",
            segment_type=SegmentType.BEHAVIORAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("total_spent", Operator.GREATER_THAN, 100),
                        SegmentRule("purchases_per_month", Operator.GREATER_THAN, 2),
                        SegmentRule("avg_purchase_value", Operator.GREATER_THAN, 25)
                    ]
                )
            ],
            tags=["monetization", "spending"],
            priority=88
        )

        # Technical Users Segment
        technical_users = UserSegment(
            id="technical_users",
            name="Technical Users",
            description="Users with technical background or preferences",
            segment_type=SegmentType.TECHNICAL,
            conditions=[
                SegmentCondition(
                    rules=[
                        SegmentRule("uses_advanced_features", Operator.EQUALS, True),
                        SegmentRule("custom_settings_count", Operator.GREATER_THAN, 10),
                        SegmentRule("technical_feedback_given", Operator.GREATER_THAN, 2)
                    ]
                )
            ],
            tags=["technical", "advanced"],
            priority=65
        )

        self.segments.update({
            premium_segment.id: premium_segment,
            power_users_segment.id: power_users_segment,
            new_users_segment.id: new_users_segment,
            mobile_users_segment.id: mobile_users_segment,
            combat_enthusiasts.id: combat_enthusiasts,
            story_lovers.id: story_lovers,
            beta_testers.id: beta_testers,
            high_spenders.id: high_spenders,
            technical_users.id: technical_users
        })

    async def _load_segments_from_redis(self):
        """Load segments from Redis"""
        try:
            segment_data = await self.async_redis_client.hgetall("segments")
            for seg_id, seg_json in segment_data.items():
                seg_dict = json.loads(seg_json)
                segment = self._dict_to_segment(seg_dict)
                self.segments[seg_id] = segment

            logger.info(f"Loaded {len(self.segments)} segments from Redis")
        except Exception as e:
            logger.warning(f"Failed to load segments from Redis: {e}")

    async def _load_user_profiles_from_redis(self):
        """Load user profiles from Redis"""
        try:
            # Load profiles in batches to avoid memory issues
            cursor = 0
            batch_size = 100
            profile_count = 0

            while True:
                cursor, keys = await self.async_redis_client.scan(
                    cursor, match="user_profile:*", count=batch_size
                )

                if keys:
                    profiles_data = await self.async_redis_client.mget(keys)
                    for profile_json in profiles_data:
                        if profile_json:
                            profile_dict = json.loads(profile_json)
                            profile = self._dict_to_profile(profile_dict)
                            self.user_profiles[profile.user_id] = profile
                            profile_count += 1

                if cursor == 0:
                    break

            logger.info(f"Loaded {profile_count} user profiles from Redis")
        except Exception as e:
            logger.warning(f"Failed to load user profiles from Redis: {e}")

    def _dict_to_segment(self, seg_dict: Dict[str, Any]) -> UserSegment:
        """Convert dictionary to UserSegment object"""
        conditions = []
        for cond_dict in seg_dict['conditions']:
            rules = [SegmentRule(**rule) for rule in cond_dict['rules']]
            conditions.append(SegmentCondition(
                rules=rules,
                logic_operator=LogicOperator(cond_dict.get('logic_operator', 'and'))
            ))

        return UserSegment(
            id=seg_dict['id'],
            name=seg_dict['name'],
            description=seg_dict['description'],
            segment_type=SegmentType(seg_dict['segment_type']),
            conditions=conditions,
            tags=seg_dict.get('tags', []),
            is_active=seg_dict.get('is_active', True),
            priority=seg_dict.get('priority', 0),
            created_at=datetime.fromisoformat(seg_dict['created_at']),
            updated_at=datetime.fromisoformat(seg_dict['updated_at']),
            created_by=seg_dict.get('created_by', 'system'),
            user_count=seg_dict.get('user_count', 0),
            last_calculated=datetime.fromisoformat(seg_dict['last_calculated']) if seg_dict.get('last_calculated') else None
        )

    def _dict_to_profile(self, profile_dict: Dict[str, Any]) -> UserProfile:
        """Convert dictionary to UserProfile object"""
        return UserProfile(
            user_id=profile_dict['user_id'],
            demographics=profile_dict.get('demographics', {}),
            behavior=profile_dict.get('behavior', {}),
            preferences=profile_dict.get('preferences', {}),
            technical=profile_dict.get('technical', {}),
            geographic=profile_dict.get('geographic', {}),
            custom_attributes=profile_dict.get('custom_attributes', {}),
            segments=set(profile_dict.get('segments', [])),
            last_updated=datetime.fromisoformat(profile_dict['last_updated']),
            calculated_features=profile_dict.get('calculated_features', {})
        )

    async def calculate_user_segments(self, user_id: str, context: Dict[str, Any] = None, force_recalculate: bool = False) -> UserProfile:
        """Calculate segments for a user"""
        if context is None:
            context = {}

        # Get or create user profile
        profile = self.user_profiles.get(user_id)
        if not profile or force_recalculate:
            profile = UserProfile(user_id=user_id)
            self.user_profiles[user_id] = profile

        # Update profile with new context data
        self._update_profile_from_context(profile, context)

        # Calculate segments
        user_segments = set()
        confidence_scores = {}

        for segment in self.segments.values():
            if not segment.is_active:
                continue

            confidence = self._evaluate_segment_conditions(profile, segment)
            confidence_scores[segment.id] = confidence

            # Add to segment if confidence meets threshold
            if confidence >= 0.7:  # 70% confidence threshold
                user_segments.add(segment.id)

        # Calculate ML-based segments
        ml_segments = await self._calculate_ml_segments(profile)
        user_segments.update(ml_segments)

        # Update profile
        profile.segments = user_segments
        profile.last_updated = datetime.utcnow()

        # Save to Redis
        await self._save_user_profile(profile)

        # Update segment counts
        await self._update_segment_counts(user_id, profile.segments)

        # Call handlers
        for handler in self.profile_update_handlers:
            try:
                handler(profile)
            except Exception as e:
                logger.error(f"Error in profile update handler: {e}")

        return profile

    def _update_profile_from_context(self, profile: UserProfile, context: Dict[str, Any]):
        """Update user profile with context data"""
        # Update demographics
        if 'demographics' in context:
            profile.demographics.update(context['demographics'])

        # Update behavior
        if 'behavior' in context:
            profile.behavior.update(context['behavior'])

        # Update preferences
        if 'preferences' in context:
            profile.preferences.update(context['preferences'])

        # Update technical
        if 'technical' in context:
            profile.technical.update(context['technical'])

        # Update geographic
        if 'geographic' in context:
            profile.geographic.update(context['geographic'])

        # Update custom attributes
        if 'custom_attributes' in context:
            profile.custom_attributes.update(context['custom_attributes'])

        # Calculate derived features
        self._calculate_derived_features(profile)

    def _calculate_derived_features(self, profile: UserProfile):
        """Calculate derived features from profile data"""
        # Account age
        if 'join_date' in profile.demographics:
            join_date = datetime.fromisoformat(profile.demographics['join_date'])
            profile.calculated_features['account_age_days'] = (datetime.utcnow() - join_date).days

        # Activity level
        sessions_per_week = profile.behavior.get('sessions_per_week', 0)
        avg_session_duration = profile.behavior.get('avg_session_duration', 0)
        profile.calculated_features['activity_score'] = sessions_per_week * (avg_session_duration / 60)

        # Engagement score
        feature_usage = profile.behavior.get('feature_usage_count', 0)
        dialogue_interactions = profile.behavior.get('dialogue_interactions', 0)
        combat_sessions = profile.behavior.get('combat_sessions_per_week', 0)
        profile.calculated_features['engagement_score'] = (
            feature_usage * 0.3 +
            dialogue_interactions * 0.4 +
            combat_sessions * 2.0
        )

        # Loyalty score
        account_age = profile.calculated_features.get('account_age_days', 0)
        total_sessions = profile.behavior.get('total_sessions', 0)
        profile.calculated_features['loyalty_score'] = (
            (account_age / 365) * 0.4 +
            min(total_sessions / 100, 1) * 0.6
        )

        # Spending level
        total_spent = profile.behavior.get('total_spent', 0)
        purchases_per_month = profile.behavior.get('purchases_per_month', 0)
        profile.calculated_features['spending_level'] = (
            min(total_spent / 500, 1) * 0.7 +
            min(purchases_per_month / 10, 1) * 0.3
        )

    def _evaluate_segment_conditions(self, profile: UserProfile, segment: UserSegment) -> float:
        """Evaluate segment conditions and return confidence score"""
        total_confidence = 0.0
        condition_count = len(segment.conditions)

        if condition_count == 0:
            return 0.0

        for condition in segment.conditions:
            condition_confidence = self._evaluate_condition(profile, condition)
            total_confidence += condition_confidence

        # Average confidence across all conditions
        return total_confidence / condition_count

    def _evaluate_condition(self, profile: UserProfile, condition: SegmentCondition) -> float:
        """Evaluate a single condition and return confidence score"""
        rule_confidences = []

        for rule in condition.rules:
            confidence = self._evaluate_rule(profile, rule)
            rule_confidences.append(confidence * rule.weight)

        if not rule_confidences:
            return 0.0

        if condition.logic_operator == LogicOperator.AND:
            # All rules must pass - use minimum confidence
            return min(rule_confidences)
        elif condition.logic_operator == LogicOperator.OR:
            # Any rule can pass - use maximum confidence
            return max(rule_confidences)
        elif condition.logic_operator == LogicOperator.NOT:
            # Negate the condition
            return 1.0 - max(rule_confidences)
        else:
            return 0.0

    def _evaluate_rule(self, profile: UserProfile, rule: SegmentRule) -> float:
        """Evaluate a single rule and return confidence score"""
        # Get the field value from profile
        field_value = self._get_field_value(profile, rule.field)

        if field_value is None:
            return 0.0

        try:
            if rule.operator == Operator.EQUALS:
                return 1.0 if field_value == rule.value else 0.0
            elif rule.operator == Operator.NOT_EQUALS:
                return 1.0 if field_value != rule.value else 0.0
            elif rule.operator == Operator.GREATER_THAN:
                return 1.0 if field_value > rule.value else 0.0
            elif rule.operator == Operator.LESS_THAN:
                return 1.0 if field_value < rule.value else 0.0
            elif rule.operator == Operator.GREATER_EQUAL:
                return 1.0 if field_value >= rule.value else 0.0
            elif rule.operator == Operator.LESS_EQUAL:
                return 1.0 if field_value <= rule.value else 0.0
            elif rule.operator == Operator.IN:
                return 1.0 if field_value in rule.value else 0.0
            elif rule.operator == Operator.NOT_IN:
                return 1.0 if field_value not in rule.value else 0.0
            elif rule.operator == Operator.CONTAINS:
                return 1.0 if rule.value in str(field_value) else 0.0
            elif rule.operator == Operator.NOT_CONTAINS:
                return 1.0 if rule.value not in str(field_value) else 0.0
            elif rule.operator == Operator.STARTS_WITH:
                return 1.0 if str(field_value).startswith(str(rule.value)) else 0.0
            elif rule.operator == Operator.ENDS_WITH:
                return 1.0 if str(field_value).endswith(str(rule.value)) else 0.0
            elif rule.operator == Operator.BETWEEN:
                min_val, max_val = rule.value
                return 1.0 if min_val <= field_value <= max_val else 0.0
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.field} {rule.operator} {rule.value}: {e}")
            return 0.0

    def _get_field_value(self, profile: UserProfile, field_path: str) -> Any:
        """Get field value from profile using dot notation"""
        parts = field_path.split('.')
        current = profile

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return None

            return current
        except Exception:
            return None

    async def _calculate_ml_segments(self, profile: UserProfile) -> Set[str]:
        """Calculate ML-based segments"""
        ml_segments = set()

        try:
            # Get user features for ML models
            features = self._extract_ml_features(profile)

            # Apply clustering model
            if 'kmeans_model' in self.ml_models:
                cluster_label = self.ml_models['kmeans_model'].predict([features])[0]
                ml_segments.add(f"cluster_{cluster_label}")

            # Apply other ML models
            # Add more ML-based segmentation as needed

        except Exception as e:
            logger.error(f"Error calculating ML segments: {e}")

        return ml_segments

    def _extract_ml_features(self, profile: UserProfile) -> List[float]:
        """Extract features for ML models"""
        features = []

        # Demographic features
        features.append(profile.demographics.get('age', 0))
        features.append(1 if profile.demographics.get('is_premium', False) else 0)

        # Behavioral features
        features.append(profile.behavior.get('sessions_per_week', 0))
        features.append(profile.behavior.get('avg_session_duration', 0))
        features.append(profile.behavior.get('combat_sessions_per_week', 0))
        features.append(profile.behavior.get('dialogue_interactions', 0))

        # Calculated features
        features.append(profile.calculated_features.get('activity_score', 0))
        features.append(profile.calculated_features.get('engagement_score', 0))
        features.append(profile.calculated_features.get('loyalty_score', 0))
        features.append(profile.calculated_features.get('spending_level', 0))

        return features

    async def _initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            # Initialize K-means clustering model
            if len(self.user_profiles) > 50:  # Need minimum users for clustering
                features = []
                user_ids = []

                for user_id, profile in list(self.user_profiles.items())[:1000]:  # Limit to 1000 users
                    user_ids.append(user_id)
                    features.append(self._extract_ml_features(profile))

                if features:
                    # Normalize features
                    scaler = StandardScaler()
                    features_normalized = scaler.fit_transform(features)

                    # Train K-means
                    kmeans = KMeans(n_clusters=5, random_state=42)
                    kmeans.fit(features_normalized)

                    self.ml_models['kmeans_model'] = kmeans
                    self.ml_models['feature_scaler'] = scaler

                    logger.info("Initialized K-means clustering model")

        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")

    async def create_segment(self, segment_data: Dict[str, Any]) -> UserSegment:
        """Create a new user segment"""
        segment_id = str(uuid.uuid4())

        conditions = []
        for cond_dict in segment_data['conditions']:
            rules = [SegmentRule(**rule) for rule in cond_dict['rules']]
            conditions.append(SegmentCondition(
                rules=rules,
                logic_operator=LogicOperator(cond_dict.get('logic_operator', 'and'))
            ))

        segment = UserSegment(
            id=segment_id,
            name=segment_data['name'],
            description=segment_data['description'],
            segment_type=SegmentType(segment_data['segment_type']),
            conditions=conditions,
            tags=segment_data.get('tags', []),
            is_active=segment_data.get('is_active', True),
            priority=segment_data.get('priority', 0),
            created_by=segment_data.get('created_by', 'system')
        )

        self.segments[segment_id] = segment
        await self._save_segment(segment)

        logger.info(f"Created user segment: {segment.name}")
        return segment

    async def update_segment(self, segment_id: str, updates: Dict[str, Any]) -> UserSegment:
        """Update an existing user segment"""
        if segment_id not in self.segments:
            raise ValueError(f"Segment {segment_id} not found")

        segment = self.segments[segment_id]

        # Update fields
        for field, value in updates.items():
            if hasattr(segment, field) and field not in ['id', 'created_at', 'created_by']:
                if field == 'segment_type':
                    setattr(segment, field, SegmentType(value))
                elif field == 'conditions':
                    conditions = []
                    for cond_dict in value:
                        rules = [SegmentRule(**rule) for rule in cond_dict['rules']]
                        conditions.append(SegmentCondition(
                            rules=rules,
                            logic_operator=LogicOperator(cond_dict.get('logic_operator', 'and'))
                        ))
                    setattr(segment, field, conditions)
                else:
                    setattr(segment, field, value)

        segment.updated_at = datetime.utcnow()

        await self._save_segment(segment)

        # Invalidate segment cache
        if segment_id in self.segment_cache:
            del self.segment_cache[segment_id]

        logger.info(f"Updated user segment: {segment.name}")
        return segment

    async def delete_segment(self, segment_id: str) -> bool:
        """Delete a user segment"""
        if segment_id not in self.segments:
            raise ValueError(f"Segment {segment_id} not found")

        segment = self.segments.pop(segment_id)

        # Remove from Redis
        await self.async_redis_client.hdel("segments", segment_id)

        # Invalidate cache
        if segment_id in self.segment_cache:
            del self.segment_cache[segment_id]

        logger.info(f"Deleted user segment: {segment.name}")
        return True

    async def _save_segment(self, segment: UserSegment):
        """Save segment to Redis"""
        try:
            seg_dict = asdict(segment)
            seg_dict['segment_type'] = segment.segment_type.value

            await self.async_redis_client.hset(
                "segments",
                segment.id,
                json.dumps(seg_dict)
            )

        except Exception as e:
            logger.error(f"Failed to save segment {segment.id}: {e}")
            raise

    async def _save_user_profile(self, profile: UserProfile):
        """Save user profile to Redis"""
        try:
            profile_dict = asdict(profile)
            profile_dict['segments'] = list(profile.segments)
            profile_dict['last_updated'] = profile.last_updated.isoformat()

            await self.async_redis_client.set(
                f"user_profile:{profile.user_id}",
                json.dumps(profile_dict),
                ex=86400 * 30  # 30 days TTL
            )

        except Exception as e:
            logger.error(f"Failed to save user profile {profile.user_id}: {e}")

    async def _update_segment_counts(self, user_id: str, segments: Set[str]):
        """Update segment user counts"""
        try:
            # Remove user from old segments
            old_profile = self.user_profiles.get(user_id)
            if old_profile:
                for old_segment in old_profile.segments - segments:
                    if old_segment in self.segments:
                        self.segments[old_segment].user_count = max(0, self.segments[old_segment].user_count - 1)

            # Add user to new segments
            for segment_id in segments:
                if segment_id in self.segments:
                    self.segments[segment_id].user_count += 1
                    self.segments[segment_id].last_calculated = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating segment counts: {e}")

    async def get_users_in_segment(self, segment_id: str, limit: int = 1000) -> List[str]:
        """Get users in a specific segment"""
        if segment_id not in self.segments:
            return []

        # Check cache first
        if segment_id in self.segment_cache:
            cache_time = datetime.utcnow().timestamp()
            if cache_time - self.segment_cache[segment_id].get('_cache_time', 0) < self.cache_ttl:
                users = [u for u in self.segment_cache[segment_id] if u != '_cache_time']
                return users[:limit]

        # Calculate users in segment
        users = []
        for user_id, profile in self.user_profiles.items():
            if segment_id in profile.segments:
                users.append(user_id)

        # Cache result
        cache_entry = users.copy()
        cache_entry.append('_cache_time')
        self.segment_cache[segment_id] = cache_entry

        return users[:limit]

    def get_segment_analytics(self, segment_id: str) -> Dict[str, Any]:
        """Get analytics for a segment"""
        if segment_id not in self.segments:
            return {"error": "Segment not found"}

        segment = self.segments[segment_id]

        # Get users in segment
        segment_users = [user_id for user_id, profile in self.user_profiles.items()
                        if segment_id in profile.segments]

        if not segment_users:
            return {
                "segment": asdict(segment),
                "user_count": 0,
                "analytics": {}
            }

        # Calculate analytics
        analytics = {
            "demographics": self._calculate_demographic_analytics(segment_users),
            "behavior": self._calculate_behavioral_analytics(segment_users),
            "engagement": self._calculate_engagement_analytics(segment_users),
            "monetization": self._calculate_monetization_analytics(segment_users)
        }

        return {
            "segment": asdict(segment),
            "user_count": len(segment_users),
            "analytics": analytics
        }

    def _calculate_demographic_analytics(self, user_ids: List[str]) -> Dict[str, Any]:
        """Calculate demographic analytics for segment"""
        ages = []
        premium_count = 0
        platforms = {}

        for user_id in user_ids:
            profile = self.user_profiles.get(user_id)
            if profile:
                if 'age' in profile.demographics:
                    ages.append(profile.demographics['age'])
                if profile.demographics.get('is_premium', False):
                    premium_count += 1
                platform = profile.technical.get('primary_platform', 'unknown')
                platforms[platform] = platforms.get(platform, 0) + 1

        return {
            "avg_age": sum(ages) / len(ages) if ages else 0,
            "premium_percentage": (premium_count / len(user_ids) * 100) if user_ids else 0,
            "platform_distribution": platforms
        }

    def _calculate_behavioral_analytics(self, user_ids: List[str]) -> Dict[str, Any]:
        """Calculate behavioral analytics for segment"""
        session_counts = []
        session_durations = []
        combat_sessions = []

        for user_id in user_ids:
            profile = self.user_profiles.get(user_id)
            if profile:
                session_counts.append(profile.behavior.get('sessions_per_week', 0))
                session_durations.append(profile.behavior.get('avg_session_duration', 0))
                combat_sessions.append(profile.behavior.get('combat_sessions_per_week', 0))

        return {
            "avg_sessions_per_week": sum(session_counts) / len(session_counts) if session_counts else 0,
            "avg_session_duration": sum(session_durations) / len(session_durations) if session_durations else 0,
            "avg_combat_sessions": sum(combat_sessions) / len(combat_sessions) if combat_sessions else 0
        }

    def _calculate_engagement_analytics(self, user_ids: List[str]) -> Dict[str, Any]:
        """Calculate engagement analytics for segment"""
        engagement_scores = []
        feature_usage = []

        for user_id in user_ids:
            profile = self.user_profiles.get(user_id)
            if profile:
                engagement_scores.append(profile.calculated_features.get('engagement_score', 0))
                feature_usage.append(profile.behavior.get('feature_usage_count', 0))

        return {
            "avg_engagement_score": sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0,
            "avg_feature_usage": sum(feature_usage) / len(feature_usage) if feature_usage else 0
        }

    def _calculate_monetization_analytics(self, user_ids: List[str]) -> Dict[str, Any]:
        """Calculate monetization analytics for segment"""
        total_spent = []
        purchases_count = []

        for user_id in user_ids:
            profile = self.user_profiles.get(user_id)
            if profile:
                total_spent.append(profile.behavior.get('total_spent', 0))
                purchases_count.append(profile.behavior.get('purchases_per_month', 0))

        return {
            "avg_total_spent": sum(total_spent) / len(total_spent) if total_spent else 0,
            "avg_purchases_per_month": sum(purchases_count) / len(purchases_count) if purchases_count else 0,
            "total_revenue": sum(total_spent)
        }

    async def _segment_calculation_task(self):
        """Background task to calculate segments for all users"""
        while True:
            try:
                # Recalculate segments for recently active users
                active_users = await self._get_recently_active_users()

                for user_id in active_users:
                    try:
                        await self.calculate_user_segments(user_id, recalculate=True)
                    except Exception as e:
                        logger.error(f"Error calculating segments for user {user_id}: {e}")

                await asyncio.sleep(3600)  # Calculate every hour
            except Exception as e:
                logger.error(f"Error in segment calculation task: {e}")
                await asyncio.sleep(300)

    async def _profile_update_task(self):
        """Background task to update user profiles"""
        while True:
            try:
                # Update profiles with recent activity data
                # This would integrate with activity tracking systems
                await asyncio.sleep(1800)  # Update every 30 minutes
            except Exception as e:
                logger.error(f"Error in profile update task: {e}")
                await asyncio.sleep(300)

    async def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                current_time = datetime.utcnow().timestamp()

                # Clean segment cache
                expired_segments = []
                for segment_id, cache_entry in self.segment_cache.items():
                    if current_time - cache_entry.get('_cache_time', 0) > self.cache_ttl:
                        expired_segments.append(segment_id)

                for segment_id in expired_segments:
                    del self.segment_cache[segment_id]

                await asyncio.sleep(1800)  # Clean every 30 minutes
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(300)

    async def _get_recently_active_users(self) -> List[str]:
        """Get list of recently active users"""
        try:
            # This would integrate with user activity tracking
            # For now, return a sample of users
            return list(self.user_profiles.keys())[:100]
        except Exception as e:
            logger.error(f"Error getting recently active users: {e}")
            return []

    def get_all_segments(self) -> List[Dict[str, Any]]:
        """Get all segments"""
        return [asdict(segment) for segment in self.segments.values()]

    def get_segment(self, segment_id: str) -> Optional[UserSegment]:
        """Get a specific segment"""
        return self.segments.get(segment_id)

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return self.user_profiles.get(user_id)

    def add_segment_change_handler(self, handler: Callable):
        """Add handler for segment changes"""
        self.segment_change_handlers.append(handler)

    def add_profile_update_handler(self, handler: Callable):
        """Add handler for profile updates"""
        self.profile_update_handlers.append(handler)

# Global segmentation service instance
segmentation_service = UserSegmentationService()