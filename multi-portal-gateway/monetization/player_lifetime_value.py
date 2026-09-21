"""
DMLogn8n Player Lifetime Value (LTV) - LTV Calculation and Optimization

This module calculates and optimizes player lifetime value through behavioral analysis,
personalized offers, and retention strategies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import redis
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class PlayerSegment(Enum):
    """Player segmentation categories"""
    NEW = "new"
    ACTIVE = "active"
    DORMANT = "dormant"
    CHURNED = "churned"
    VIP = "vip"
    PREMIUM = "premium"
    CASUAL = "casual"
    WHALE = "whale"
    MINNOW = "minnow"

class EngagementLevel(Enum):
    """Player engagement levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class LTVModel(Enum):
    """LTV calculation models"""
    HISTORICAL = "historical"
    PREDICTIVE = "predictive"
    COHORT_BASED = "cohort_based"
    RFM = "rfm"  # Recency, Frequency, Monetary
    CLTV = "cltv"  # Customer Lifetime Value
@dataclass
class PlayerProfile:
    """Player profile with LTV data"""
    player_id: str
    signup_date: datetime
    first_purchase_date: Optional[datetime]
    last_active_date: datetime
    total_revenue: Decimal = Decimal('0.00')
    total_sessions: int = 0
    total_playtime: int = 0  # in seconds
    total_purchases: int = 0
    average_session_duration: float = 0.0
    days_active: int = 0
    days_since_last_activity: int = 0
    segment: PlayerSegment = PlayerSegment.NEW
    engagement_level: EngagementLevel = EngagementLevel.MEDIUM
    predicted_ltv: Decimal = Decimal('0.00')
    actual_ltv: Decimal = Decimal('0.00')
    ltv_confidence: float = 0.0
    acquisition_channel: str = ""
    acquisition_cost: Decimal = Decimal('0.00')
    subscription_tier: str = ""
    churn_probability: float = 0.0
    preferences: Dict[str, Any] = field(default_factory=dict)
    behaviors: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LTVPrediction:
    """LTV prediction result"""
    player_id: str
    predicted_ltv_30d: Decimal
    predicted_ltv_90d: Decimal
    predicted_ltv_180d: Decimal
    predicted_ltv_365d: Decimal
    total_predicted_ltv: Decimal
    model_used: LTVModel
    confidence_score: float
    key_factors: List[str]
    prediction_date: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PersonalizedOffer:
    """Personalized offer for player"""
    id: str
    player_id: str
    offer_type: str  # discount, bonus, content, upgrade
    title: str
    description: str
    value: Decimal
    currency: str
    conditions: Dict[str, Any]
    expiration_date: datetime
    priority: int = 1
    auto_apply: bool = False
    redemption_rate: float = 0.0
    revenue_impact: Decimal = Decimal('0.00')
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RetentionAction:
    """Retention action for at-risk players"""
    id: str
    player_id: str
    action_type: str  # email, push, in_game, discount, support
    trigger_condition: str
    content: Dict[str, Any]
    scheduled_date: datetime
    executed: bool = False
    result: Dict[str, Any] = field(default_factory=dict)
    effectiveness_score: float = 0.0

class PlayerLifetimeValue:
    """Main LTV calculation and optimization system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.ltv_models: Dict[LTVModel, Any] = {}
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.segment_rules: Dict[PlayerSegment, Dict] = {}
        self.offer_templates: List[Dict] = []
        self.retention_strategies: Dict[str, Dict] = {}

    async def initialize(self):
        """Initialize LTV system"""
        logger.info("Initializing DMLogn8n Player Lifetime Value System...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_ltv')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Load segment rules
        await self._load_segment_rules()

        # Load offer templates
        await self._load_offer_templates()

        # Load retention strategies
        await self._load_retention_strategies()

        # Initialize ML models
        await self._initialize_ltv_models()

        # Start background tasks
        asyncio.create_task(self._profile_updater())
        asyncio.create_task(self._ltv_calculator())
        asyncio.create_task(self._segmentation_updater())
        asyncio.create_task(self._offer_optimizer())
        asyncio.create_task(self._retention_executor())

        logger.info("LTV System initialized successfully")

    async def _load_segment_rules(self):
        """Load player segmentation rules"""
        default_rules = {
            PlayerSegment.NEW: {
                'conditions': {
                    'days_since_signup': 30,
                    'total_purchases': 0,
                    'total_revenue_max': 0
                },
                'ltv_multiplier': 1.0,
                'retention_priority': 'high'
            },
            PlayerSegment.ACTIVE: {
                'conditions': {
                    'days_since_last_activity_max': 7,
                    'days_active_min': 10,
                    'sessions_per_week_min': 3
                },
                'ltv_multiplier': 1.2,
                'retention_priority': 'medium'
            },
            PlayerSegment.DORMANT: {
                'conditions': {
                    'days_since_last_activity_min': 8,
                    'days_since_last_activity_max': 30,
                    'previous_active': True
                },
                'ltv_multiplier': 0.8,
                'retention_priority': 'high'
            },
            PlayerSegment.CHURNED: {
                'conditions': {
                    'days_since_last_activity_min': 31
                },
                'ltv_multiplier': 0.3,
                'retention_priority': 'urgent'
            },
            PlayerSegment.VIP: {
                'conditions': {
                    'total_revenue_min': 500,
                    'total_purchases_min': 10,
                    'subscription_tier': 'enterprise'
                },
                'ltv_multiplier': 2.0,
                'retention_priority': 'maximum'
            },
            PlayerSegment.PREMIUM: {
                'conditions': {
                    'subscription_tier': 'professional',
                    'total_revenue_min': 100
                },
                'ltv_multiplier': 1.5,
                'retention_priority': 'high'
            },
            PlayerSegment.WHALE: {
                'conditions': {
                    'total_revenue_min': 1000,
                    'avg_monthly_spend_min': 100
                },
                'ltv_multiplier': 3.0,
                'retention_priority': 'maximum'
            },
            PlayerSegment.CASUAL: {
                'conditions': {
                    'sessions_per_week_max': 2,
                    'avg_session_duration_max': 600,  # 10 minutes
                    'total_revenue_max': 50
                },
                'ltv_multiplier': 0.6,
                'retention_priority': 'low'
            }
        }

        for segment, rules in default_rules.items():
            self.segment_rules[segment] = rules
            await self.redis_client.setex(
                f"segment_rules:{segment.value}",
                86400 * 30,
                json.dumps(rules)
            )

    async def _load_offer_templates(self):
        """Load personalized offer templates"""
        default_templates = [
            {
                'id': 'welcome_discount',
                'name': 'Welcome Discount',
                'offer_type': 'discount',
                'segments': [PlayerSegment.NEW],
                'conditions': {'days_since_signup': 7},
                'value': 20.0,
                'currency': 'percentage',
                'description': '20% off your first purchase',
                'validity_days': 14
            },
            {
                'id': 'win_back_offer',
                'name': 'Win Back Offer',
                'offer_type': 'discount',
                'segments': [PlayerSegment.DORMANT],
                'conditions': {'days_since_last_activity': 14},
                'value': 30.0,
                'currency': 'percentage',
                'description': '30% off - We miss you!',
                'validity_days': 7
            },
            {
                'id': 'loyalty_bonus',
                'name': 'Loyalty Bonus',
                'offer_type': 'bonus',
                'segments': [PlayerSegment.ACTIVE, PlayerSegment.VIP],
                'conditions': {'days_active_min': 30},
                'value': 50.0,
                'currency': 'credits',
                'description': '50 bonus credits for your loyalty',
                'validity_days': 30
            },
            {
                'id': 'upgrade_incentive',
                'name': 'Upgrade Incentive',
                'offer_type': 'discount',
                'segments': [PlayerSegment.PREMIUM],
                'conditions': {'subscription_tier': 'professional'},
                'value': 25.0,
                'currency': 'percentage',
                'description': '25% off upgrade to Enterprise',
                'validity_days': 21
            },
            {
                'id': 'whale_perk',
                'name': 'VIP Perk',
                'offer_type': 'content',
                'segments': [PlayerSegment.WHALE, PlayerSegment.VIP],
                'conditions': {'total_revenue_min': 500},
                'value': 0,
                'currency': 'exclusive',
                'description': 'Exclusive content and early access',
                'validity_days': 90
            }
        ]

        self.offer_templates = default_templates
        await self.redis_client.setex(
            "offer_templates",
            86400 * 30,
            json.dumps(default_templates)
        )

    async def _load_retention_strategies(self):
        """Load retention strategies"""
        default_strategies = {
            'new_player_onboarding': {
                'trigger': 'player_signup',
                'actions': [
                    {'type': 'email', 'template': 'welcome_series', 'delay_hours': 0},
                    {'type': 'in_game', 'content': 'tutorial_rewards', 'delay_hours': 24},
                    {'type': 'push', 'message': 'first_campaign_tip', 'delay_hours': 48}
                ]
            },
            'dormant_reengagement': {
                'trigger': 'days_inactive_7',
                'actions': [
                    {'type': 'email', 'template': 'we_miss_you', 'delay_hours': 0},
                    {'type': 'offer', 'template': 'win_back_offer', 'delay_hours': 24},
                    {'type': 'push', 'message': 'new_features', 'delay_hours': 72}
                ]
            },
            'high_value_retention': {
                'trigger': 'ltv_decline_20',
                'actions': [
                    {'type': 'personal outreach', 'method': 'email', 'delay_hours': 0},
                    {'type': 'offer', 'template': 'vip_perk', 'delay_hours': 12},
                    {'type': 'support', 'priority': 'high', 'delay_hours': 24}
                ]
            },
            'churn_prevention': {
                'trigger': 'churn_probability_80',
                'actions': [
                    {'type': 'personal outreach', 'method': 'phone', 'delay_hours': 0},
                    {'type': 'offer', 'template': 'deep_discount', 'delay_hours': 6},
                    {'type': 'account_review', 'delay_hours': 24}
                ]
            }
        }

        self.retention_strategies = default_strategies
        await self.redis_client.setex(
            "retention_strategies",
            86400 * 30,
            json.dumps(default_strategies)
        )

    async def _initialize_ltv_models(self):
        """Initialize machine learning models for LTV prediction"""
        # Historical LTV model
        self.ltv_models[LTVModel.HISTORICAL] = None  # Simple calculation

        # Predictive LTV model
        self.ltv_models[LTVModel.PREDICTIVE] = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )

        # RFM model
        self.ltv_models[LTVModel.RFM] = KMeans(n_clusters=5, random_state=42)

        # Initialize feature scaler
        self.feature_scaler = StandardScaler()

    async def get_player_profile(self, player_id: str) -> PlayerProfile:
        """Get or create player profile"""
        try:
            # Try cache first
            cached_profile = await self.redis_client.get(f"player_profile:{player_id}")
            if cached_profile:
                data = json.loads(cached_profile)
                return PlayerProfile(
                    player_id=data['player_id'],
                    signup_date=datetime.fromisoformat(data['signup_date']),
                    first_purchase_date=datetime.fromisoformat(data['first_purchase_date']) if data['first_purchase_date'] else None,
                    last_active_date=datetime.fromisoformat(data['last_active_date']),
                    total_revenue=Decimal(str(data['total_revenue'])),
                    total_sessions=data['total_sessions'],
                    total_playtime=data['total_playtime'],
                    total_purchases=data['total_purchases'],
                    average_session_duration=data['average_session_duration'],
                    days_active=data['days_active'],
                    days_since_last_activity=data['days_since_last_activity'],
                    segment=PlayerSegment(data['segment']),
                    engagement_level=EngagementLevel(data['engagement_level']),
                    predicted_ltv=Decimal(str(data['predicted_ltv'])),
                    actual_ltv=Decimal(str(data['actual_ltv'])),
                    ltv_confidence=data['ltv_confidence'],
                    acquisition_channel=data['acquisition_channel'],
                    acquisition_cost=Decimal(str(data['acquisition_cost'])),
                    subscription_tier=data['subscription_tier'],
                    churn_probability=data['churn_probability'],
                    preferences=data['preferences'],
                    behaviors=data['behaviors'],
                    metadata=data['metadata']
                )

            # Load from database
            profile = await self._load_profile_from_db(player_id)
            if profile:
                await self._cache_profile(profile)
                return profile

            # Create new profile
            new_profile = PlayerProfile(
                player_id=player_id,
                signup_date=datetime.utcnow(),
                last_active_date=datetime.utcnow(),
                segment=PlayerSegment.NEW
            )

            await self._save_profile_to_db(new_profile)
            await self._cache_profile(new_profile)
            return new_profile

        except Exception as e:
            logger.error(f"Error getting player profile {player_id}: {e}")
            return PlayerProfile(
                player_id=player_id,
                signup_date=datetime.utcnow(),
                last_active_date=datetime.utcnow()
            )

    async def _cache_profile(self, profile: PlayerProfile):
        """Cache player profile"""
        profile_data = {
            'player_id': profile.player_id,
            'signup_date': profile.signup_date.isoformat(),
            'first_purchase_date': profile.first_purchase_date.isoformat() if profile.first_purchase_date else None,
            'last_active_date': profile.last_active_date.isoformat(),
            'total_revenue': float(profile.total_revenue),
            'total_sessions': profile.total_sessions,
            'total_playtime': profile.total_playtime,
            'total_purchases': profile.total_purchases,
            'average_session_duration': profile.average_session_duration,
            'days_active': profile.days_active,
            'days_since_last_activity': profile.days_since_last_activity,
            'segment': profile.segment.value,
            'engagement_level': profile.engagement_level.value,
            'predicted_ltv': float(profile.predicted_ltv),
            'actual_ltv': float(profile.actual_ltv),
            'ltv_confidence': profile.ltv_confidence,
            'acquisition_channel': profile.acquisition_channel,
            'acquisition_cost': float(profile.acquisition_cost),
            'subscription_tier': profile.subscription_tier,
            'churn_probability': profile.churn_probability,
            'preferences': profile.preferences,
            'behaviors': profile.behaviors,
            'metadata': profile.metadata
        }

        await self.redis_client.setex(
            f"player_profile:{profile.player_id}",
            3600,  # 1 hour cache
            json.dumps(profile_data)
        )

    async def _load_profile_from_db(self, player_id: str) -> Optional[PlayerProfile]:
        """Load player profile from database"""
        session = self.session_factory()
        try:
            # Query from database (simplified)
            # Would use proper ORM models in real implementation
            return None
        finally:
            session.close()

    async def _save_profile_to_db(self, profile: PlayerProfile):
        """Save player profile to database"""
        session = self.session_factory()
        try:
            # Save to database (simplified)
            pass
        finally:
            session.close()

    async def update_player_activity(self, player_id: str, activity_data: Dict[str, Any]) -> bool:
        """Update player activity data"""
        try:
            profile = await self.get_player_profile(player_id)

            # Update basic activity metrics
            if 'session_duration' in activity_data:
                profile.total_sessions += 1
                profile.total_playtime += activity_data['session_duration']
                profile.average_session_duration = profile.total_playtime / profile.total_sessions

            if 'revenue' in activity_data:
                profile.total_revenue += Decimal(str(activity_data['revenue']))
                profile.total_purchases += 1

                if not profile.first_purchase_date:
                    profile.first_purchase_date = datetime.utcnow()

            if 'last_active' in activity_data:
                profile.last_active_date = activity_data['last_active']

            # Update calculated fields
            profile.days_since_last_activity = (datetime.utcnow() - profile.last_active_date).days
            profile.days_active = min(365, (datetime.utcnow() - profile.signup_date).days)

            # Update behaviors
            if 'behaviors' in activity_data:
                for behavior, value in activity_data['behaviors'].items():
                    if behavior in profile.behaviors:
                        # Exponential moving average
                        profile.behaviors[behavior] = 0.8 * profile.behaviors[behavior] + 0.2 * value
                    else:
                        profile.behaviors[behavior] = value

            # Update segment
            await self._update_player_segment(profile)

            # Update engagement level
            await self._update_engagement_level(profile)

            # Cache and save
            await self._cache_profile(profile)
            await self._save_profile_to_db(profile)

            return True

        except Exception as e:
            logger.error(f"Error updating player activity: {e}")
            return False

    async def _update_player_segment(self, profile: PlayerProfile):
        """Update player segment based on current data"""
        for segment, rules in self.segment_rules.items():
            if await self._matches_segment_rules(profile, rules):
                profile.segment = segment
                break

    async def _matches_segment_rules(self, profile: PlayerProfile, rules: Dict) -> bool:
        """Check if profile matches segment rules"""
        conditions = rules.get('conditions', {})

        # Check numeric conditions
        for condition, value in conditions.items():
            if condition.endswith('_min'):
                field = condition[:-4]
                profile_value = getattr(profile, field, 0)
                if isinstance(profile_value, Decimal):
                    profile_value = float(profile_value)
                if profile_value < value:
                    return False
            elif condition.endswith('_max'):
                field = condition[:-4]
                profile_value = getattr(profile, field, float('inf'))
                if isinstance(profile_value, Decimal):
                    profile_value = float(profile_value)
                if profile_value > value:
                    return False
            elif condition == 'previous_active' and value:
                if profile.days_active < 10:
                    return False
            elif condition == 'days_since_signup':
                if profile.days_since_last_activity > value:
                    return False

        return True

    async def _update_engagement_level(self, profile: PlayerProfile):
        """Update player engagement level"""
        # Calculate engagement score
        session_frequency = profile.days_active / max(1, (datetime.utcnow() - profile.signup_date).days)
        avg_session_score = min(1.0, profile.average_session_duration / 1800)  # 30 minutes = 1.0
        revenue_score = min(1.0, float(profile.total_revenue) / 100)  # $100 = 1.0

        engagement_score = (session_frequency * 0.4 + avg_session_score * 0.3 + revenue_score * 0.3)

        if engagement_score >= 0.8:
            profile.engagement_level = EngagementLevel.VERY_HIGH
        elif engagement_score >= 0.6:
            profile.engagement_level = EngagementLevel.HIGH
        elif engagement_score >= 0.4:
            profile.engagement_level = EngagementLevel.MEDIUM
        elif engagement_score >= 0.2:
            profile.engagement_level = EngagementLevel.LOW
        else:
            profile.engagement_level = EngagementLevel.VERY_LOW

    async def calculate_ltv(self, player_id: str, model: LTVModel = LTVModel.PREDICTIVE) -> LTVPrediction:
        """Calculate LTV for a player"""
        try:
            profile = await self.get_player_profile(player_id)

            if model == LTVModel.HISTORICAL:
                prediction = await self._calculate_historical_ltv(profile)
            elif model == LTVModel.PREDICTIVE:
                prediction = await self._calculate_predictive_ltv(profile)
            elif model == LTVModel.RFM:
                prediction = await self._calculate_rfm_ltv(profile)
            else:
                prediction = await self._calculate_historical_ltv(profile)

            # Update profile with predicted LTV
            profile.predicted_ltv = prediction.total_predicted_ltv
            profile.ltv_confidence = prediction.confidence_score
            await self._cache_profile(profile)

            return prediction

        except Exception as e:
            logger.error(f"Error calculating LTV for player {player_id}: {e}")
            return LTVPrediction(
                player_id=player_id,
                predicted_ltv_30d=Decimal('0.00'),
                predicted_ltv_90d=Decimal('0.00'),
                predicted_ltv_180d=Decimal('0.00'),
                predicted_ltv_365d=Decimal('0.00'),
                total_predicted_ltv=Decimal('0.00'),
                model_used=model,
                confidence_score=0.0,
                key_factors=[]
            )

    async def _calculate_historical_ltv(self, profile: PlayerProfile) -> LTVPrediction:
        """Calculate historical LTV based on past behavior"""
        # Simple historical calculation
        days_active = max(1, profile.days_active)
        daily_revenue = float(profile.total_revenue) / days_active

        # Project based on historical patterns
        predicted_30d = Decimal(str(daily_revenue * 30))
        predicted_90d = Decimal(str(daily_revenue * 90))
        predicted_180d = Decimal(str(daily_revenue * 180))
        predicted_365d = Decimal(str(daily_revenue * 365))

        # Apply segment multiplier
        segment_multiplier = self.segment_rules.get(profile.segment, {}).get('ltv_multiplier', 1.0)

        total_predicted = (predicted_30d + predicted_90d + predicted_180d + predicted_365d) * Decimal(str(segment_multiplier))

        return LTVPrediction(
            player_id=profile.player_id,
            predicted_ltv_30d=predicted_30d,
            predicted_ltv_90d=predicted_90d,
            predicted_ltv_180d=predicted_180d,
            predicted_ltv_365d=predicted_365d,
            total_predicted_ltv=total_predicted,
            model_used=LTVModel.HISTORICAL,
            confidence_score=0.6,  # Medium confidence for historical
            key_factors=['historical_revenue', 'segment_multiplier']
        )

    async def _calculate_predictive_ltv(self, profile: PlayerProfile) -> LTVPrediction:
        """Calculate predictive LTV using machine learning"""
        try:
            # Get training data and features
            features = await self._extract_ltv_features(profile)

            # Check if model is trained
            model = self.ltv_models.get(LTVModel.PREDICTIVE)
            if not hasattr(model, 'feature_importances_'):
                # Model not trained, fallback to historical
                return await self._calculate_historical_ltv(profile)

            # Make predictions
            feature_array = np.array([features]).reshape(1, -1)
            predicted_365d = model.predict(feature_array)[0]

            # Scale for different time periods
            predicted_30d = Decimal(str(predicted_365d * 0.3))
            predicted_90d = Decimal(str(predicted_365d * 0.5))
            predicted_180d = Decimal(str(predicted_365d * 0.7))
            predicted_365d = Decimal(str(predicted_365d))

            total_predicted = predicted_30d + predicted_90d + predicted_180d + predicted_365d

            # Get key factors
            feature_names = await self._get_feature_names()
            key_factors = [feature_names[i] for i in np.argsort(model.feature_importances_)[-3:]]

            return LTVPrediction(
                player_id=profile.player_id,
                predicted_ltv_30d=predicted_30d,
                predicted_ltv_90d=predicted_90d,
                predicted_ltv_180d=predicted_180d,
                predicted_ltv_365d=predicted_365d,
                total_predicted_ltv=total_predicted,
                model_used=LTVModel.PREDICTIVE,
                confidence_score=0.8,
                key_factors=key_factors
            )

        except Exception as e:
            logger.error(f"Error in predictive LTV calculation: {e}")
            return await self._calculate_historical_ltv(profile)

    async def _calculate_rfm_ltv(self, profile: PlayerProfile) -> LTVPrediction:
        """Calculate LTV using RFM analysis"""
        # R: Recency (days since last activity)
        recency = profile.days_since_last_activity

        # F: Frequency (purchase frequency)
        frequency = profile.total_purchases

        # M: Monetary (total revenue)
        monetary = float(profile.total_revenue)

        # Normalize scores (1-5 scale)
        recency_score = max(1, 6 - min(5, recency // 30))  # Lower recency = higher score
        frequency_score = min(5, max(1, frequency // 2))
        monetary_score = min(5, max(1, int(monetary // 50)))

        # Calculate RFM score
        rfm_score = (recency_score + frequency_score + monetary_score) / 3

        # Estimate LTV based on RFM score
        base_ltv = monetary * (1 + rfm_score / 5)

        predicted_365d = Decimal(str(base_ltv))
        predicted_180d = Decimal(str(base_ltv * 0.6))
        predicted_90d = Decimal(str(base_ltv * 0.4))
        predicted_30d = Decimal(str(base_ltv * 0.2))

        total_predicted = predicted_30d + predicted_90d + predicted_180d + predicted_365d

        return LTVPrediction(
            player_id=profile.player_id,
            predicted_ltv_30d=predicted_30d,
            predicted_ltv_90d=predicted_90d,
            predicted_ltv_180d=predicted_180d,
            predicted_ltv_365d=predicted_365d,
            total_predicted_ltv=total_predicted,
            model_used=LTVModel.RFM,
            confidence_score=0.7,
            key_factors=['recency', 'frequency', 'monetary']
        )

    async def _extract_ltv_features(self, profile: PlayerProfile) -> List[float]:
        """Extract features for LTV prediction"""
        features = [
            profile.days_since_last_activity,
            profile.days_active,
            profile.total_sessions,
            profile.total_playtime,
            profile.total_purchases,
            float(profile.total_revenue),
            profile.average_session_duration,
            1.0 if profile.first_purchase_date else 0.0,
            len(profile.behaviors),
            profile.churn_probability
        ]

        # Add behavior features
        behavior_features = list(profile.behaviors.values())
        features.extend(behavior_features + [0.0] * (10 - len(behavior_features)))  # Pad to 10 features

        # Add encoded segment and engagement
        segment_encoding = {
            PlayerSegment.NEW: 1,
            PlayerSegment.ACTIVE: 2,
            PlayerSegment.DORMANT: 3,
            PlayerSegment.CHURNED: 4,
            PlayerSegment.VIP: 5,
            PlayerSegment.PREMIUM: 6,
            PlayerSegment.WHALE: 7,
            PlayerSegment.CASUAL: 8
        }

        engagement_encoding = {
            EngagementLevel.VERY_LOW: 1,
            EngagementLevel.LOW: 2,
            EngagementLevel.MEDIUM: 3,
            EngagementLevel.HIGH: 4,
            EngagementLevel.VERY_HIGH: 5
        }

        features.extend([
            segment_encoding.get(profile.segment, 0),
            engagement_encoding.get(profile.engagement_level, 0)
        ])

        return features

    async def _get_feature_names(self) -> List[str]:
        """Get feature names for model interpretation"""
        return [
            'days_since_last_activity',
            'days_active',
            'total_sessions',
            'total_playtime',
            'total_purchases',
            'total_revenue',
            'average_session_duration',
            'has_purchased',
            'behavior_count',
            'churn_probability',
            'behavior_1', 'behavior_2', 'behavior_3', 'behavior_4', 'behavior_5',
            'behavior_6', 'behavior_7', 'behavior_8', 'behavior_9', 'behavior_10',
            'segment_encoded',
            'engagement_encoded'
        ]

    async def generate_personalized_offers(self, player_id: str) -> List[PersonalizedOffer]:
        """Generate personalized offers for a player"""
        try:
            profile = await self.get_player_profile(player_id)
            ltv_prediction = await self.calculate_ltv(player_id)

            offers = []

            # Find matching offer templates
            for template in self.offer_templates:
                if await self._offer_matches_player(template, profile, ltv_prediction):
                    offer = await self._create_offer_from_template(template, profile)
                    offers.append(offer)

            # Sort by priority
            offers.sort(key=lambda x: x.priority, reverse=True)

            # Limit to top 3 offers
            return offers[:3]

        except Exception as e:
            logger.error(f"Error generating offers for player {player_id}: {e}")
            return []

    async def _offer_matches_player(self, template: Dict, profile: PlayerProfile,
                                 ltv_prediction: LTVPrediction) -> bool:
        """Check if offer template matches player"""
        # Check segment match
        target_segments = template.get('segments', [])
        if target_segments and profile.segment not in target_segments:
            return False

        # Check conditions
        conditions = template.get('conditions', {})
        for condition, value in conditions.items():
            if condition == 'days_since_signup':
                if profile.days_active > value:
                    return False
            elif condition == 'days_since_last_activity':
                if profile.days_since_last_activity != value:
                    return False
            elif condition == 'days_active_min':
                if profile.days_active < value:
                    return False
            elif condition == 'total_revenue_min':
                if float(profile.total_revenue) < value:
                    return False
            elif condition == 'subscription_tier':
                if profile.subscription_tier != value:
                    return False

        return True

    async def _create_offer_from_template(self, template: Dict, profile: PlayerProfile) -> PersonalizedOffer:
        """Create personalized offer from template"""
        offer_id = str(uuid.uuid4())

        # Calculate expiration date
        validity_days = template.get('validity_days', 7)
        expiration_date = datetime.utcnow() + timedelta(days=validity_days)

        # Personalize description
        description = template['description']
        if '{player_name}' in description:
            description = description.replace('{player_name}', f'Player {profile.player_id[-4:]}')

        # Calculate priority based on LTV and segment
        base_priority = 1
        if profile.segment in [PlayerSegment.VIP, PlayerSegment.WHALE]:
            base_priority = 5
        elif profile.segment == PlayerSegment.PREMIUM:
            base_priority = 4
        elif profile.segment in [PlayerSegment.NEW, PlayerSegment.DORMANT]:
            base_priority = 3

        return PersonalizedOffer(
            id=offer_id,
            player_id=profile.player_id,
            offer_type=template['offer_type'],
            title=template['name'],
            description=description,
            value=Decimal(str(template['value'])),
            currency=template['currency'],
            conditions=template.get('conditions', {}),
            expiration_date=expiration_date,
            priority=base_priority
        )

    async def create_retention_actions(self, player_id: str) -> List[RetentionAction]:
        """Create retention actions for at-risk players"""
        try:
            profile = await self.get_player_profile(player_id)
            actions = []

            # Check for churn risk
            if profile.churn_probability > 0.7:
                # High churn risk - immediate intervention
                strategy = self.retention_strategies.get('churn_prevention')
                if strategy:
                    for action_config in strategy['actions']:
                        action = await self._create_retention_action(
                            player_id, action_config, strategy['trigger']
                        )
                        actions.append(action)

            elif profile.churn_probability > 0.4:
                # Medium churn risk
                if profile.segment == PlayerSegment.DORMANT:
                    strategy = self.retention_strategies.get('dormant_reengagement')
                    if strategy:
                        for action_config in strategy['actions']:
                            action = await self._create_retention_action(
                                player_id, action_config, strategy['trigger']
                            )
                            actions.append(action)

            elif profile.segment == PlayerSegment.NEW:
                # New player onboarding
                strategy = self.retention_strategies.get('new_player_onboarding')
                if strategy and profile.days_active <= 7:
                    for action_config in strategy['actions']:
                        action = await self._create_retention_action(
                            player_id, action_config, strategy['trigger']
                        )
                        actions.append(action)

            # High value player retention
            if profile.segment in [PlayerSegment.VIP, PlayerSegment.WHALE]:
                strategy = self.retention_strategies.get('high_value_retention')
                if strategy:
                    for action_config in strategy['actions']:
                        action = await self._create_retention_action(
                            player_id, action_config, strategy['trigger']
                        )
                        actions.append(action)

            return actions

        except Exception as e:
            logger.error(f"Error creating retention actions for player {player_id}: {e}")
            return []

    async def _create_retention_action(self, player_id: str, action_config: Dict,
                                    trigger: str) -> RetentionAction:
        """Create retention action from configuration"""
        action_id = str(uuid.uuid4())
        scheduled_date = datetime.utcnow() + timedelta(hours=action_config.get('delay_hours', 0))

        return RetentionAction(
            id=action_id,
            player_id=player_id,
            action_type=action_config['type'],
            trigger_condition=trigger,
            content=action_config,
            scheduled_date=scheduled_date
        )

    async def get_ltv_insights(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive LTV insights for a player"""
        try:
            profile = await self.get_player_profile(player_id)
            ltv_prediction = await self.calculate_ltv(player_id)

            # Get player percentile rankings
            percentiles = await self._get_player_percentiles(profile)

            # Get recommendations
            recommendations = await self._generate_ltv_recommendations(profile, ltv_prediction)

            # Get similar players
            similar_players = await self._find_similar_players(profile)

            insights = {
                'player_id': player_id,
                'current_ltv': {
                    'predicted': float(ltv_prediction.total_predicted_ltv),
                    'actual': float(profile.actual_ltv),
                    'confidence': ltv_prediction.confidence_score,
                    'key_factors': ltv_prediction.key_factors
                },
                'player_profile': {
                    'segment': profile.segment.value,
                    'engagement_level': profile.engagement_level.value,
                    'days_active': profile.days_active,
                    'total_revenue': float(profile.total_revenue),
                    'churn_probability': profile.churn_probability
                },
                'percentile_rankings': percentiles,
                'recommendations': recommendations,
                'similar_players': similar_players[:5],  # Top 5 similar players
                'personalized_offers': await self.generate_personalized_offers(player_id),
                'retention_actions': await self.create_retention_actions(player_id),
                'generated_at': datetime.utcnow().isoformat()
            }

            return insights

        except Exception as e:
            logger.error(f"Error getting LTV insights for player {player_id}: {e}")
            return {'error': str(e)}

    async def _get_player_percentiles(self, profile: PlayerProfile) -> Dict[str, float]:
        """Get player percentile rankings"""
        # This is a simplified implementation
        # In real system, would calculate percentiles against all players
        return {
            'revenue_percentile': 0.75,
            'engagement_percentile': 0.60,
            'loyalty_percentile': 0.80,
            'potential_percentile': 0.70
        }

    async def _generate_ltv_recommendations(self, profile: PlayerProfile,
                                          ltv_prediction: LTVPrediction) -> List[str]:
        """Generate LTV optimization recommendations"""
        recommendations = []

        # Based on segment
        if profile.segment == PlayerSegment.NEW:
            recommendations.extend([
                "Focus on completing first purchase to establish value",
                "Engage with onboarding content to increase retention",
                "Consider welcome discount to accelerate conversion"
            ])
        elif profile.segment == PlayerSegment.ACTIVE:
            recommendations.extend([
                "Encourage increased session frequency",
                "Introduce premium features for upselling",
                "Leverage social features to boost engagement"
            ])
        elif profile.segment == PlayerSegment.DORMANT:
            recommendations.extend([
                "Implement re-engagement campaign with personalized offers",
                "Highlight new features or content since last visit",
                "Consider incentive for returning"
            ])
        elif profile.segment in [PlayerSegment.VIP, PlayerSegment.WHALE]:
            recommendations.extend([
                "Provide exclusive content and early access",
                "Ensure premium customer support",
                "Create community engagement opportunities"
            ])

        # Based on churn probability
        if profile.churn_probability > 0.7:
            recommendations.append("URGENT: High churn risk - immediate intervention required")
        elif profile.churn_probability > 0.4:
            recommendations.append("Moderate churn risk - proactive engagement recommended")

        # Based on engagement level
        if profile.engagement_level in [EngagementLevel.VERY_LOW, EngagementLevel.LOW]:
            recommendations.append("Low engagement - investigate barriers and friction points")

        # Based on LTV potential
        if ltv_prediction.confidence_score > 0.8 and ltv_prediction.total_predicted_ltv > Decimal('100'):
            recommendations.append("High LTV potential - prioritize retention efforts")

        return recommendations

    async def _find_similar_players(self, profile: PlayerProfile) -> List[Dict[str, Any]]:
        """Find players similar to the given player"""
        # This is a simplified implementation
        # In real system, would use clustering or similarity algorithms
        similar_players = []

        # Mock similar players
        for i in range(10):
            similar_players.append({
                'player_id': f"similar_{i}",
                'similarity_score': 0.8 - (i * 0.05),
                'segment': PlayerSegment.ACTIVE.value,
                'ltv': 150.0 + (i * 25),
                'days_active': profile.days_active + (i * 5)
            })

        return similar_players

    async def get_ltv_cohort_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get cohort-based LTV analysis"""
        try:
            # Get cohorts by signup month
            cohorts = await self._get_ltv_cohorts(start_date, end_date)

            # Calculate LTV trends for each cohort
            cohort_analysis = {}
            for cohort_name, cohort_data in cohorts.items():
                ltv_trends = await self._calculate_cohort_ltv_trends(cohort_data)
                cohort_analysis[cohort_name] = {
                    'cohort_size': len(cohort_data),
                    'avg_initial_ltv': np.mean([p.total_revenue for p in cohort_data]),
                    'ltv_trends': ltv_trends,
                    'retention_rates': await self._calculate_cohort_retention(cohort_data)
                }

            return {
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'cohorts': cohort_analysis,
                'insights': self._generate_cohort_insights(cohort_analysis)
            }

        except Exception as e:
            logger.error(f"Error in cohort LTV analysis: {e}")
            return {'error': str(e)}

    async def _get_ltv_cohorts(self, start_date: datetime, end_date: datetime) -> Dict[str, List[PlayerProfile]]:
        """Get player cohorts by signup period"""
        cohorts = defaultdict(list)

        # This would query database for players in date range
        # Simplified implementation
        for month_offset in range(12):
            cohort_date = start_date.replace(day=1) + timedelta(days=month_offset * 30)
            cohort_name = cohort_date.strftime('%Y-%m')

            # Mock cohort data
            for i in range(50):  # 50 players per cohort
                mock_profile = PlayerProfile(
                    player_id=f"cohort_player_{cohort_name}_{i}",
                    signup_date=cohort_date,
                    last_active_date=cohort_date + timedelta(days=np.random.randint(1, 90)),
                    total_revenue=Decimal(str(np.random.uniform(0, 200))),
                    total_sessions=np.random.randint(1, 50),
                    days_active=np.random.randint(1, 90)
                )
                cohorts[cohort_name].append(mock_profile)

        return dict(cohorts)

    async def _calculate_cohort_ltv_trends(self, cohort_data: List[PlayerProfile]) -> List[float]:
        """Calculate LTV trends for a cohort"""
        # Simplified trend calculation
        base_ltv = np.mean([float(p.total_revenue) for p in cohort_data])
        trends = []

        for month in range(12):
            # Simulate LTV growth over time
            month_ltv = base_ltv * (1 + month * 0.1) * (1 - month * 0.05)  # Growth with decay
            trends.append(max(0, month_ltv))

        return trends

    async def _calculate_cohort_retention(self, cohort_data: List[PlayerProfile]) -> List[float]:
        """Calculate retention rates for a cohort"""
        # Simplified retention calculation
        retention_rates = []

        for month in range(12):
            # Simulate retention decay
            retention_rate = 1.0 * (0.9 ** month)  # 10% decay per month
            retention_rates.append(max(0, retention_rate))

        return retention_rates

    def _generate_cohort_insights(self, cohort_analysis: Dict) -> List[str]:
        """Generate insights from cohort analysis"""
        insights = []

        # Compare cohorts
        if cohort_analysis:
            latest_cohort = list(cohort_analysis.keys())[-1]
            earliest_cohort = list(cohort_analysis.keys())[0]

            latest_ltv = cohort_analysis[latest_cohort]['avg_initial_ltv']
            earliest_ltv = cohort_analysis[earliest_cohort]['avg_initial_ltv']

            if latest_ltv > earliest_ltv * 1.2:
                insights.append("Recent cohorts show higher initial LTV - improving acquisition quality")
            elif latest_ltv < earliest_ltv * 0.8:
                insights.append("Recent cohorts show lower LTV - review acquisition strategy")

            # Retention insights
            avg_retention_12m = np.mean([
                cohort['retention_rates'][-1] if cohort['retention_rates'] else 0
                for cohort in cohort_analysis.values()
            ])

            if avg_retention_12m < 0.2:
                insights.append("Low 12-month retention across cohorts - focus on long-term engagement")

        insights.extend([
            "Analyze top-performing cohorts for common characteristics",
            "Compare LTV trends across different acquisition channels",
            "Monitor cohort evolution for early warning signs"
        ])

        return insights

    async def _profile_updater(self):
        """Background task to update player profiles"""
        while True:
            try:
                logger.info("Updating player profiles...")

                # Get recent activity events
                # This would query database for recent player activities
                # Simplified implementation

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                logger.error(f"Error in profile updater: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _ltv_calculator(self):
        """Background task to calculate LTV"""
        while True:
            try:
                logger.info("Running LTV calculations...")

                # Calculate LTV for active players
                # This would identify players needing LTV recalculation
                # Simplified implementation

                await asyncio.sleep(3600)  # Calculate every hour

            except Exception as e:
                logger.error(f"Error in LTV calculator: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _segmentation_updater(self):
        """Background task to update player segments"""
        while True:
            try:
                logger.info("Updating player segments...")

                # Update segments for all active players
                # Simplified implementation

                await asyncio.sleep(86400)  # Update daily

            except Exception as e:
                logger.error(f"Error in segmentation updater: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _offer_optimizer(self):
        """Background task to optimize offers"""
        while True:
            try:
                logger.info("Optimizing personalized offers...")

                # Analyze offer performance and optimize
                # Simplified implementation

                await asyncio.sleep(86400)  # Optimize daily

            except Exception as e:
                logger.error(f"Error in offer optimizer: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _retention_executor(self):
        """Background task to execute retention actions"""
        while True:
            try:
                logger.info("Executing retention actions...")

                # Find scheduled retention actions and execute them
                # Simplified implementation

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"Error in retention executor: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

# Database models
class PlayerProfileDB(Base):
    """Player profile database model"""
    __tablename__ = 'player_profiles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String, nullable=False, unique=True)
    signup_date = Column(DateTime, nullable=False)
    first_purchase_date = Column(DateTime)
    last_active_date = Column(DateTime, nullable=False)
    total_revenue = Column(Float, default=0.0)
    total_sessions = Column(Integer, default=0)
    total_playtime = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    average_session_duration = Column(Float, default=0.0)
    days_active = Column(Integer, default=0)
    segment = Column(String, default='new')
    engagement_level = Column(String, default='medium')
    predicted_ltv = Column(Float, default=0.0)
    actual_ltv = Column(Float, default=0.0)
    ltv_confidence = Column(Float, default=0.0)
    acquisition_channel = Column(String)
    acquisition_cost = Column(Float, default=0.0)
    subscription_tier = Column(String)
    churn_probability = Column(Float, default=0.0)
    preferences = Column(JSON)
    behaviors = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LTVPredictionDB(Base):
    """LTV prediction database model"""
    __tablename__ = 'ltv_predictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(String, nullable=False)
    predicted_ltv_30d = Column(Float, nullable=False)
    predicted_ltv_90d = Column(Float, nullable=False)
    predicted_ltv_180d = Column(Float, nullable=False)
    predicted_ltv_365d = Column(Float, nullable=False)
    total_predicted_ltv = Column(Float, nullable=False)
    model_used = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    key_factors = Column(JSON)
    prediction_date = Column(DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_ltv'
        }

        ltv_system = PlayerLifetimeValue(config)
        await ltv_system.initialize()

        # Update player activity
        result = await ltv_system.update_player_activity(
            "player_123",
            {
                'session_duration': 1800,  # 30 minutes
                'revenue': 29.99,
                'behaviors': {'campaign_creation': 0.8, 'social_interaction': 0.6}
            }
        )
        print(f"Updated activity: {result}")

        # Calculate LTV
        ltv_prediction = await ltv_system.calculate_ltv("player_123")
        print(f"LTV prediction: {ltv_prediction}")

        # Get personalized offers
        offers = await ltv_system.generate_personalized_offers("player_123")
        print(f"Generated {len(offers)} offers")

        # Get comprehensive insights
        insights = await ltv_system.get_ltv_insights("player_123")
        print(f"Insights keys: {list(insights.keys())}")

    asyncio.run(main())