"""
DMLogn8n Analytics Engine - Business Analytics and KPI Tracking

This module provides comprehensive business analytics including funnel analysis,
cohort analysis, predictive modeling, and real-time KPI tracking.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import redis
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class MetricType(Enum):
    """Types of metrics to track"""
    REVENUE = "revenue"
    USERS = "users"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    LIFETIME_VALUE = "lifetime_value"
    ACQUISITION = "acquisition"
    CHURN = "churn"
    PERFORMANCE = "performance"

class TimeGranularity(Enum):
    """Time granularity for analytics"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class FunnelStage(Enum):
    """Funnel stages for user journey"""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    PURCHASE = "purchase"
    RETENTION = "retention"
    ADVOCACY = "advocacy"

class CohortType(Enum):
    """Types of cohorts for analysis"""
    SIGNUP_DATE = "signup_date"
    FIRST_PURCHASE = "first_purchase"
    ACQUISITION_CHANNEL = "acquisition_channel"
    USER_SEGMENT = "user_segment"
    SUBSCRIPTION_TIER = "subscription_tier"
    GEOGRAPHIC = "geographic"

@dataclass
class KPIDefinition:
    """KPI definition and configuration"""
    id: str
    name: str
    description: str
    metric_type: MetricType
    calculation_method: str  # sum, avg, count, rate, ratio
    target_value: Optional[float] = None
    alert_threshold_min: Optional[float] = None
    alert_threshold_max: Optional[float] = None
    time_granularity: TimeGranularity = TimeGranularity.DAILY
    dimensions: List[str] = field(default_factory=list)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FunnelEvent:
    """Funnel event definition"""
    id: str
    name: str
    stage: FunnelStage
    description: str
    event_type: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    time_window_hours: int = 24
    required: bool = True

@dataclass
class AnalyticsEvent:
    """Raw analytics event"""
    event_id: str
    user_id: str
    event_type: str
    event_name: str
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    platform: Optional[str] = None
    country: Optional[str] = None

@dataclass
class PredictionModel:
    """Machine learning model for predictions"""
    id: str
    name: str
    model_type: str  # regression, classification, clustering
    target_variable: str
    features: List[str]
    model: Any = None
    accuracy: float = 0.0
    last_trained: Optional[datetime] = None
    training_data_period_days: int = 90
    active: bool = True

class AnalyticsEngine:
    """Main analytics engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.kpis: Dict[str, KPIDefinition] = {}
        self.funnels: Dict[str, List[FunnelEvent]] = {}
        self.prediction_models: Dict[str, PredictionModel] = {}
        self.real_time_metrics = defaultdict(float)
        self.cohort_cache = {}

    async def initialize(self):
        """Initialize analytics engine"""
        logger.info("Initializing DMLogn8n Analytics Engine...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_analytics')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Load KPI definitions
        await self._load_kpi_definitions()

        # Load funnel definitions
        await self._load_funnel_definitions()

        # Initialize prediction models
        await self._initialize_prediction_models()

        # Start background tasks
        asyncio.create_task(self._metric_collector())
        asyncio.create_task(self._kpi_calculator())
        asyncio.create_task(self._cohort_analyzer())
        asyncio.create_task(self._prediction_trainer())
        asyncio.create_task(self._alert_monitor())

        logger.info("Analytics Engine initialized successfully")

    async def _load_kpi_definitions(self):
        """Load KPI definitions"""
        default_kpis = [
            KPIDefinition(
                id="daily_revenue",
                name="Daily Revenue",
                description="Total revenue generated per day",
                metric_type=MetricType.REVENUE,
                calculation_method="sum",
                target_value=1000.0,
                alert_threshold_min=500.0,
                time_granularity=TimeGranularity.DAILY,
                dimensions=["currency", "revenue_stream"]
            ),
            KPIDefinition(
                id="monthly_active_users",
                name="Monthly Active Users",
                description="Number of unique active users per month",
                metric_type=MetricType.USERS,
                calculation_method="count",
                target_value=10000.0,
                alert_threshold_min=5000.0,
                time_granularity=TimeGranularity.MONTHLY,
                dimensions=["platform", "country"]
            ),
            KPIDefinition(
                id="conversion_rate",
                name="Conversion Rate",
                description="Percentage of users who make a purchase",
                metric_type=MetricType.CONVERSION,
                calculation_method="rate",
                target_value=0.05,
                alert_threshold_min=0.02,
                time_granularity=TimeGranularity.DAILY,
                dimensions=["campaign", "user_segment"]
            ),
            KPIDefinition(
                id="customer_lifetime_value",
                name="Customer Lifetime Value",
                description="Average revenue per customer over their lifetime",
                metric_type=MetricType.LIFETIME_VALUE,
                calculation_method="avg",
                target_value=100.0,
                time_granularity=TimeGranularity.MONTHLY,
                dimensions=["acquisition_channel", "subscription_tier"]
            ),
            KPIDefinition(
                id="churn_rate",
                name="Monthly Churn Rate",
                description="Percentage of customers who cancel each month",
                metric_type=MetricType.CHURN,
                calculation_method="rate",
                target_value=0.05,
                alert_threshold_max=0.10,
                time_granularity=TimeGranularity.MONTHLY,
                dimensions=["subscription_tier", "usage_level"]
            ),
            KPIDefinition(
                id="average_revenue_per_user",
                name="Average Revenue Per User",
                description="Average revenue generated per user",
                metric_type=MetricType.REVENUE,
                calculation_method="avg",
                target_value=10.0,
                time_granularity=TimeGranularity.DAILY,
                dimensions=["user_type", "platform"]
            ),
            KPIDefinition(
                id="session_duration",
                name="Average Session Duration",
                description="Average time users spend per session",
                metric_type=MetricType.ENGAGEMENT,
                calculation_method="avg",
                target_value=1800.0,  # 30 minutes in seconds
                time_granularity=TimeGranularity.DAILY,
                dimensions=["platform", "device_type"]
            ),
            KPIDefinition(
                id="retention_rate_7d",
                name="7-Day Retention Rate",
                description="Percentage of users who return after 7 days",
                metric_type=MetricType.RETENTION,
                calculation_method="rate",
                target_value=0.40,
                alert_threshold_min=0.25,
                time_granularity=TimeGranularity.WEEKLY,
                dimensions=["user_segment", "acquisition_channel"]
            )
        ]

        for kpi in default_kpis:
            self.kpis[kpi.id] = kpi
            await self._cache_kpi(kpi)

    async def _cache_kpi(self, kpi: KPIDefinition):
        """Cache KPI definition"""
        kpi_data = {
            'id': kpi.id,
            'name': kpi.name,
            'description': kpi.description,
            'metric_type': kpi.metric_type.value,
            'calculation_method': kpi.calculation_method,
            'target_value': kpi.target_value,
            'alert_threshold_min': kpi.alert_threshold_min,
            'alert_threshold_max': kpi.alert_threshold_max,
            'time_granularity': kpi.time_granularity.value,
            'dimensions': kpi.dimensions,
            'active': kpi.active
        }

        await self.redis_client.setex(
            f"kpi:{kpi.id}",
            86400 * 30,  # 30 days
            json.dumps(kpi_data)
        )

    async def _load_funnel_definitions(self):
        """Load funnel definitions"""
        default_funnels = {
            "user_acquisition": [
                FunnelEvent(
                    id="visit_landing",
                    name="Visit Landing Page",
                    stage=FunnelStage.AWARENESS,
                    description="User visits the landing page",
                    event_type="page_view",
                    conditions={"page": "/landing"}
                ),
                FunnelEvent(
                    id="signup_init",
                    name="Start Sign Up",
                    stage=FunnelStage.INTEREST,
                    description="User begins sign-up process",
                    event_type="form_start",
                    conditions={"form": "signup"}
                ),
                FunnelEvent(
                    id="signup_complete",
                    name="Complete Sign Up",
                    stage=FunnelStage.CONSIDERATION,
                    description="User completes sign-up",
                    event_type="form_complete",
                    conditions={"form": "signup"},
                    required=True
                ),
                FunnelEvent(
                    id="first_campaign",
                    name="Create First Campaign",
                    stage=FunnelStage.INTENT,
                    description="User creates their first campaign",
                    event_type="campaign_create",
                    conditions={"first": True}
                ),
                FunnelEvent(
                    id="first_purchase",
                    name="First Purchase",
                    stage=FunnelStage.PURCHASE,
                    description="User makes their first purchase",
                    event_type="purchase",
                    conditions={"first_purchase": True},
                    required=True
                )
            ],
            "subscription_upgrade": [
                FunnelEvent(
                    id="visit_pricing",
                    name="Visit Pricing Page",
                    stage=FunnelStage.INTEREST,
                    description="User views pricing options",
                    event_type="page_view",
                    conditions={"page": "/pricing"}
                ),
                FunnelEvent(
                    id="compare_plans",
                    name="Compare Plans",
                    stage=FunnelStage.CONSIDERATION,
                    description="User compares subscription plans",
                    event_type="plan_compare",
                    conditions={}
                ),
                FunnelEvent(
                    id="start_upgrade",
                    name="Start Upgrade Process",
                    stage=FunnelStage.INTENT,
                    description="User begins upgrade process",
                    event_type="upgrade_start",
                    conditions={}
                ),
                FunnelEvent(
                    id="complete_upgrade",
                    name="Complete Upgrade",
                    stage=FunnelStage.PURCHASE,
                    description="User completes subscription upgrade",
                    event_type="upgrade_complete",
                    conditions={},
                    required=True
                )
            ]
        }

        for funnel_name, events in default_funnels.items():
            self.funnels[funnel_name] = events
            await self._cache_funnel(funnel_name, events)

    async def _cache_funnel(self, funnel_name: str, events: List[FunnelEvent]):
        """Cache funnel definition"""
        funnel_data = []
        for event in events:
            event_data = {
                'id': event.id,
                'name': event.name,
                'stage': event.stage.value,
                'description': event.description,
                'event_type': event.event_type,
                'conditions': event.conditions,
                'time_window_hours': event.time_window_hours,
                'required': event.required
            }
            funnel_data.append(event_data)

        await self.redis_client.setex(
            f"funnel:{funnel_name}",
            86400 * 30,
            json.dumps(funnel_data)
        )

    async def _initialize_prediction_models(self):
        """Initialize machine learning models"""
        default_models = [
            PredictionModel(
                id="revenue_prediction",
                name="Revenue Prediction Model",
                model_type="regression",
                target_variable="revenue_30d",
                features=["active_users", "session_duration", "conversion_rate", "avg_order_value"],
                training_data_period_days=90
            ),
            PredictionModel(
                id="churn_prediction",
                name="Customer Churn Prediction",
                model_type="classification",
                target_variable="will_churn_30d",
                features=["session_frequency", "last_login_days", "purchase_count", "support_tickets"],
                training_data_period_days=180
            ),
            PredictionModel(
                id="ltv_prediction",
                name="Lifetime Value Prediction",
                model_type="regression",
                target_variable="ltv_180d",
                features=["first_purchase_amount", "acquisition_channel", "device_type", "geography"],
                training_data_period_days=365
            )
        ]

        for model in default_models:
            self.prediction_models[model.id] = model

    async def track_event(self, event: AnalyticsEvent) -> bool:
        """Track an analytics event"""
        try:
            # Store event
            event_data = {
                'event_id': event.event_id,
                'user_id': event.user_id,
                'event_type': event.event_type,
                'event_name': event.event_name,
                'timestamp': event.timestamp.isoformat(),
                'properties': event.properties,
                'session_id': event.session_id,
                'platform': event.platform,
                'country': event.country
            }

            # Store in Redis for real-time processing
            await self.redis_client.lpush("events_stream", json.dumps(event_data))

            # Update real-time metrics
            await self._update_real_time_metrics(event)

            # Store in database for historical analysis
            await self._store_event_in_db(event)

            return True

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False

    async def _update_real_time_metrics(self, event: AnalyticsEvent):
        """Update real-time metrics based on event"""
        # Update event counters
        await self.redis_client.hincrby(
            "real_time:events",
            f"{event.event_type}:{event.event_name}",
            1
        )

        # Update active users (if within last 5 minutes)
        now = datetime.utcnow()
        key = f"active_users:{event.user_id}"
        await self.redis_client.setex(key, 300, "1")  # 5 minutes

        # Update session metrics
        if event.session_id:
            session_key = f"session:{event.session_id}"
            session_data = await self.redis_client.hgetall(session_key)
            if session_data:
                # Update session duration
                start_time = datetime.fromisoformat(session_data[b'start_time'].decode())
                duration = (now - start_time).total_seconds()
                await self.redis_client.hset(session_key, "duration", str(duration))
            else:
                # New session
                await self.redis_client.hset(
                    session_key,
                    mapping={
                        'user_id': event.user_id,
                        'start_time': event.timestamp.isoformat(),
                        'platform': event.platform or 'unknown'
                    }
                )
                await self.redis_client.expire(session_key, 3600)  # 1 hour

    async def _store_event_in_db(self, event: AnalyticsEvent):
        """Store event in database for historical analysis"""
        session = self.session_factory()
        try:
            # Create database record (simplified)
            db_event = AnalyticsEventDB(
                event_id=event.event_id,
                user_id=event.user_id,
                event_type=event.event_type,
                event_name=event.event_name,
                timestamp=event.timestamp,
                properties=event.properties,
                session_id=event.session_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                platform=event.platform,
                country=event.country
            )
            session.add(db_event)
            session.commit()
        finally:
            session.close()

    async def calculate_kpi(self, kpi_id: str, start_date: datetime,
                          end_date: datetime, dimensions: Dict[str, str] = None) -> Dict[str, Any]:
        """Calculate KPI value for specified period"""
        try:
            kpi = self.kpis.get(kpi_id)
            if not kpi:
                return {'error': 'KPI not found'}

            # Get relevant events
            events = await self._get_events_for_kpi(kpi, start_date, end_date, dimensions)

            # Calculate based on method
            if kpi.calculation_method == "sum":
                value = await self._calculate_sum(kpi, events)
            elif kpi.calculation_method == "count":
                value = await self._calculate_count(kpi, events)
            elif kpi.calculation_method == "avg":
                value = await self._calculate_average(kpi, events)
            elif kpi.calculation_method == "rate":
                value = await self._calculate_rate(kpi, events)
            elif kpi.calculation_method == "ratio":
                value = await self._calculate_ratio(kpi, events)
            else:
                value = 0

            result = {
                'kpi_id': kpi_id,
                'kpi_name': kpi.name,
                'value': value,
                'target': kpi.target_value,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'dimensions': dimensions or {},
                'performance': self._evaluate_kpi_performance(kpi, value)
            }

            # Cache result
            cache_key = f"kpi_result:{kpi_id}:{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
            await self.redis_client.setex(cache_key, 3600, json.dumps(result))

            return result

        except Exception as e:
            logger.error(f"Error calculating KPI {kpi_id}: {e}")
            return {'error': str(e)}

    async def _get_events_for_kpi(self, kpi: KPIDefinition, start_date: datetime,
                               end_date: datetime, dimensions: Dict[str, str] = None) -> List[AnalyticsEvent]:
        """Get events relevant to KPI calculation"""
        # This is a simplified implementation
        # In real system, would query database with appropriate filters

        session = self.session_factory()
        try:
            # Query events from database
            query = session.query(AnalyticsEventDB).filter(
                AnalyticsEventDB.timestamp >= start_date,
                AnalyticsEventDB.timestamp <= end_date
            )

            # Apply dimension filters
            if dimensions:
                for dim_name, dim_value in dimensions.items():
                    if dim_name == "platform":
                        query = query.filter(AnalyticsEventDB.platform == dim_value)
                    elif dim_name == "country":
                        query = query.filter(AnalyticsEventDB.country == dim_value)

            events = query.limit(10000).all()  # Limit for performance

            # Convert to AnalyticsEvent objects
            analytics_events = []
            for db_event in events:
                analytics_event = AnalyticsEvent(
                    event_id=db_event.event_id,
                    user_id=db_event.user_id,
                    event_type=db_event.event_type,
                    event_name=db_event.event_name,
                    timestamp=db_event.timestamp,
                    properties=db_event.properties or {},
                    session_id=db_event.session_id,
                    platform=db_event.platform,
                    country=db_event.country
                )
                analytics_events.append(analytics_event)

            return analytics_events

        finally:
            session.close()

    async def _calculate_sum(self, kpi: KPIDefinition, events: List[AnalyticsEvent]) -> float:
        """Calculate sum KPI"""
        if kpi.metric_type == MetricType.REVENUE:
            total = 0.0
            for event in events:
                if event.event_type == "purchase":
                    amount = event.properties.get('amount', 0)
                    total += float(amount)
            return total
        else:
            # For other types, just count events
            return len(events)

    async def _calculate_count(self, kpi: KPIDefinition, events: List[AnalyticsEvent]) -> float:
        """Calculate count KPI"""
        if kpi.metric_type == MetricType.USERS:
            # Count unique users
            unique_users = set()
            for event in events:
                unique_users.add(event.user_id)
            return len(unique_users)
        else:
            return len(events)

    async def _calculate_average(self, kpi: KPIDefinition, events: List[AnalyticsEvent]) -> float:
        """Calculate average KPI"""
        if kpi.metric_type == MetricType.LIFETIME_VALUE:
            # Average revenue per user
            user_revenue = defaultdict(float)
            for event in events:
                if event.event_type == "purchase":
                    amount = event.properties.get('amount', 0)
                    user_revenue[event.user_id] += float(amount)

            if user_revenue:
                return sum(user_revenue.values()) / len(user_revenue)
            else:
                return 0.0
        elif kpi.metric_type == MetricType.ENGAGEMENT and "session_duration" in kpi.id:
            # Average session duration
            durations = []
            for event in events:
                if event.event_type == "session_end":
                    duration = event.properties.get('duration', 0)
                    durations.append(float(duration))

            return sum(durations) / len(durations) if durations else 0.0
        else:
            return 0.0

    async def _calculate_rate(self, kpi: KPIDefinition, events: List[AnalyticsEvent]) -> float:
        """Calculate rate KPI"""
        if kpi.metric_type == MetricType.CONVERSION:
            # Conversion rate = purchases / total users
            unique_users = set()
            purchasers = set()

            for event in events:
                unique_users.add(event.user_id)
                if event.event_type == "purchase":
                    purchasers.add(event.user_id)

            return len(purchasers) / len(unique_users) if unique_users else 0.0

        elif kpi.metric_type == MetricType.CHURN:
            # Churn rate = cancelled subscriptions / total subscriptions
            total_subscriptions = set()
            cancelled_subscriptions = set()

            for event in events:
                if event.event_type == "subscription_start":
                    total_subscriptions.add(event.user_id)
                elif event.event_type == "subscription_cancel":
                    cancelled_subscriptions.add(event.user_id)

            return len(cancelled_subscriptions) / len(total_subscriptions) if total_subscriptions else 0.0

        elif kpi.metric_type == MetricType.RETENTION and "7d" in kpi.id:
            # 7-day retention rate
            # This is simplified - would need cohort analysis in real implementation
            return 0.4  # Placeholder

        return 0.0

    async def _calculate_ratio(self, kpi: KPIDefinition, events: List[AnalyticsEvent]) -> float:
        """Calculate ratio KPI"""
        # Generic ratio calculation
        # Would need specific implementation based on KPI definition
        return 0.0

    def _evaluate_kpi_performance(self, kpi: KPIDefinition, value: float) -> str:
        """Evaluate KPI performance against targets"""
        if kpi.target_value is None:
            return "no_target"

        ratio = value / kpi.target_value if kpi.target_value != 0 else 0

        if ratio >= 1.2:
            return "excellent"
        elif ratio >= 1.0:
            return "good"
        elif ratio >= 0.8:
            return "fair"
        else:
            return "poor"

    async def analyze_funnel(self, funnel_name: str, start_date: datetime,
                           end_date: datetime) -> Dict[str, Any]:
        """Analyze conversion funnel"""
        try:
            funnel_events = self.funnels.get(funnel_name)
            if not funnel_events:
                return {'error': 'Funnel not found'}

            # Get funnel analysis data
            funnel_data = await self._get_funnel_data(funnel_events, start_date, end_date)

            # Calculate conversion rates between stages
            conversion_rates = []
            for i in range(len(funnel_data) - 1):
                current_count = funnel_data[i]['count']
                next_count = funnel_data[i + 1]['count']
                rate = next_count / current_count if current_count > 0 else 0
                conversion_rates.append(rate)

            # Calculate overall conversion rate
            overall_rate = funnel_data[-1]['count'] / funnel_data[0]['count'] if funnel_data[0]['count'] > 0 else 0

            # Identify drop-off points
            drop_offs = []
            for i, rate in enumerate(conversion_rates):
                if rate < 0.5:  # Less than 50% conversion
                    drop_offs.append({
                        'stage': funnel_events[i].name,
                        'drop_off_rate': 1 - rate,
                        'users_lost': funnel_data[i]['count'] - funnel_data[i + 1]['count']
                    })

            return {
                'funnel_name': funnel_name,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'stages': [
                    {
                        'name': stage.name,
                        'stage': stage.stage.value,
                        'count': data['count'],
                        'conversion_rate': data['count'] / funnel_data[0]['count'] if funnel_data[0]['count'] > 0 else 0
                    }
                    for stage, data in zip(funnel_events, funnel_data)
                ],
                'conversion_rates': conversion_rates,
                'overall_conversion_rate': overall_rate,
                'drop_offs': drop_offs,
                'recommendations': self._generate_funnel_recommendations(drop_offs, conversion_rates)
            }

        except Exception as e:
            logger.error(f"Error analyzing funnel {funnel_name}: {e}")
            return {'error': str(e)}

    async def _get_funnel_data(self, funnel_events: List[FunnelEvent],
                             start_date: datetime, end_date: datetime) -> List[Dict[str, int]]:
        """Get funnel data for analysis"""
        funnel_data = []

        for event in funnel_events:
            # Get event count for this stage
            count = await self._count_funnel_events(event, start_date, end_date)
            funnel_data.append({'count': count})

        return funnel_data

    async def _count_funnel_events(self, funnel_event: FunnelEvent,
                                 start_date: datetime, end_date: datetime) -> int:
        """Count events for funnel stage"""
        session = self.session_factory()
        try:
            query = session.query(AnalyticsEventDB).filter(
                AnalyticsEventDB.timestamp >= start_date,
                AnalyticsEventDB.timestamp <= end_date,
                AnalyticsEventDB.event_type == funnel_event.event_type
            )

            # Apply event-specific conditions
            if funnel_event.conditions:
                for condition_key, condition_value in funnel_event.conditions.items():
                    if condition_key == "page":
                        query = query.filter(AnalyticsEventDB.properties.contains({"page": condition_value}))
                    elif condition_key == "form":
                        query = query.filter(AnalyticsEventDB.properties.contains({"form": condition_value}))
                    elif condition_key == "first":
                        if condition_value:
                            # Get first events per user
                            subquery = session.query(
                                AnalyticsEventDB.user_id,
                                func.min(AnalyticsEventDB.timestamp).label('first_time')
                            ).filter(
                                AnalyticsEventDB.event_type == funnel_event.event_type
                            ).group_by(AnalyticsEventDB.user_id).subquery()

                            query = query.join(
                                subquery,
                                (AnalyticsEventDB.user_id == subquery.c.user_id) &
                                (AnalyticsEventDB.timestamp == subquery.c.first_time)
                            )

            return query.count()

        finally:
            session.close()

    def _generate_funnel_recommendations(self, drop_offs: List[Dict], conversion_rates: List[float]) -> List[str]:
        """Generate recommendations based on funnel analysis"""
        recommendations = []

        if drop_offs:
            worst_drop_off = max(drop_offs, key=lambda x: x['drop_off_rate'])
            recommendations.append(f"Focus on optimizing {worst_drop_off['stage']} - {worst_drop_off['drop_off_rate']:.1%} drop-off rate")

        if conversion_rates and min(conversion_rates) < 0.3:
            recommendations.append("Consider simplifying the user journey to reduce friction")

        if conversion_rates and conversion_rates[-1] < 0.1:
            recommendations.append("Review final conversion steps - low completion rate")

        recommendations.append("Implement A/B testing on high drop-off stages")
        recommendations.append("Add user feedback collection at critical funnel points")

        return recommendations

    async def cohort_analysis(self, cohort_type: CohortType, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Perform cohort analysis"""
        try:
            # Get cohort data
            cohorts = await self._get_cohort_data(cohort_type, start_date, end_date)

            # Calculate retention matrix
            retention_matrix = await self._calculate_retention_matrix(cohorts)

            # Calculate cohort metrics
            cohort_metrics = await self._calculate_cohort_metrics(cohorts)

            return {
                'cohort_type': cohort_type.value,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'cohorts': cohorts,
                'retention_matrix': retention_matrix,
                'metrics': cohort_metrics,
                'insights': self._generate_cohort_insights(retention_matrix, cohort_metrics)
            }

        except Exception as e:
            logger.error(f"Error in cohort analysis: {e}")
            return {'error': str(e)}

    async def _get_cohort_data(self, cohort_type: CohortType, start_date: datetime,
                             end_date: datetime) -> List[Dict]:
        """Get cohort data based on type"""
        session = self.session_factory()
        try:
            cohorts = []

            if cohort_type == CohortType.SIGNUP_DATE:
                # Group users by signup date
                query = session.query(
                    func.date(AnalyticsEventDB.timestamp).label('cohort_date'),
                    func.count(func.distinct(AnalyticsEventDB.user_id)).label('cohort_size')
                ).filter(
                    AnalyticsEventDB.event_type == "signup",
                    AnalyticsEventDB.timestamp >= start_date,
                    AnalyticsEventDB.timestamp <= end_date
                ).group_by(func.date(AnalyticsEventDB.timestamp))

                for row in query:
                    cohorts.append({
                        'cohort_date': row.cohort_date.isoformat(),
                        'cohort_size': row.cohort_size,
                        'users': []  # Would populate with actual user IDs
                    })

            elif cohort_type == CohortType.ACQUISITION_CHANNEL:
                # Group users by acquisition channel
                query = session.query(
                    AnalyticsEventDB.properties['acquisition_channel'].label('channel'),
                    func.count(func.distinct(AnalyticsEventDB.user_id)).label('cohort_size')
                ).filter(
                    AnalyticsEventDB.event_type == "signup",
                    AnalyticsEventDB.timestamp >= start_date,
                    AnalyticsEventDB.timestamp <= end_date
                ).group_by(AnalyticsEventDB.properties['acquisition_channel'])

                for row in query:
                    cohorts.append({
                        'cohort_identifier': row.channel,
                        'cohort_size': row.cohort_size,
                        'users': []
                    })

            return cohorts

        finally:
            session.close()

    async def _calculate_retention_matrix(self, cohorts: List[Dict]) -> Dict[str, List[float]]:
        """Calculate retention matrix for cohorts"""
        retention_matrix = {}

        for cohort in cohorts:
            retention_rates = []
            cohort_identifier = cohort.get('cohort_date', cohort.get('cohort_identifier'))
            cohort_users = set(cohort.get('users', []))

            # Calculate retention for each period (day/week/month)
            for period in range(0, 12):  # 12 periods
                active_users = await self._get_active_users_in_period(cohort_users, period)
                retention_rate = len(active_users) / len(cohort_users) if cohort_users else 0
                retention_rates.append(retention_rate)

            retention_matrix[cohort_identifier] = retention_rates

        return retention_matrix

    async def _get_active_users_in_period(self, users: set, period: int) -> set:
        """Get active users for a cohort in a specific period"""
        # Simplified implementation
        # In real system, would query activity logs for specific time periods
        return set()  # Placeholder

    async def _calculate_cohort_metrics(self, cohorts: List[Dict]) -> Dict[str, float]:
        """Calculate overall cohort metrics"""
        if not cohorts:
            return {}

        total_users = sum(cohort['cohort_size'] for cohort in cohorts)
        avg_cohort_size = total_users / len(cohorts)

        return {
            'total_cohorts': len(cohorts),
            'total_users': total_users,
            'average_cohort_size': avg_cohort_size,
            'retention_period_1': 0.7,  # Placeholder
            'retention_period_7': 0.4,  # Placeholder
            'retention_period_30': 0.2   # Placeholder
        }

    def _generate_cohort_insights(self, retention_matrix: Dict, metrics: Dict) -> List[str]:
        """Generate insights from cohort analysis"""
        insights = []

        if metrics.get('retention_period_7', 0) < 0.3:
            insights.append("Low 7-day retention indicates onboarding issues")

        if metrics.get('retention_period_30', 0) < 0.1:
            insights.append("Poor long-term engagement - consider retention strategies")

        insights.append("Analyze top-performing cohorts for successful patterns")
        insights.append("Compare acquisition channels for retention differences")

        return insights

    async def predict_revenue(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Predict future revenue using ML models"""
        try:
            model = self.prediction_models.get("revenue_prediction")
            if not model or not model.model:
                return await self._simple_revenue_prediction(days_ahead)

            # Get features for prediction
            features = await self._get_revenue_features()

            # Make prediction
            predicted_revenue = model.model.predict([features])[0]

            return {
                'prediction_period_days': days_ahead,
                'predicted_revenue': float(predicted_revenue),
                'model_used': model.name,
                'accuracy': model.accuracy,
                'features_used': features,
                'confidence_interval': self._calculate_confidence_interval(predicted_revenue, model.accuracy)
            }

        except Exception as e:
            logger.error(f"Error predicting revenue: {e}")
            return {'error': str(e)}

    async def _simple_revenue_prediction(self, days_ahead: int) -> Dict[str, Any]:
        """Simple revenue prediction without ML"""
        # Get historical revenue data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        historical_data = []
        current_date = start_date
        while current_date <= end_date:
            # Get daily revenue (simplified)
            daily_revenue = await self._get_daily_revenue(current_date)
            historical_data.append(daily_revenue)
            current_date += timedelta(days=1)

        # Simple linear regression
        if len(historical_data) < 7:
            return {
                'prediction_period_days': days_ahead,
                'predicted_revenue': sum(historical_data) / len(historical_data) if historical_data else 0,
                'method': 'simple_average',
                'confidence': 'low'
            }

        x = np.arange(len(historical_data)).reshape(-1, 1)
        y = np.array(historical_data)

        model = LinearRegression()
        model.fit(x, y)

        # Predict future
        future_x = np.arange(len(historical_data), len(historical_data) + days_ahead).reshape(-1, 1)
        predictions = model.predict(future_x)

        return {
            'prediction_period_days': days_ahead,
            'predicted_revenue': float(np.sum(predictions)),
            'method': 'linear_regression',
            'confidence': 'medium',
            'daily_predictions': predictions.tolist()
        }

    async def _get_revenue_features(self) -> List[float]:
        """Get features for revenue prediction model"""
        # Get current metrics
        active_users = await self.redis_client.hget("real_time:metrics", "active_users") or 0
        avg_session_duration = await self.redis_client.hget("real_time:metrics", "avg_session_duration") or 0
        conversion_rate = await self.redis_client.hget("real_time:metrics", "conversion_rate") or 0

        return [
            float(active_users),
            float(avg_session_duration),
            float(conversion_rate),
            50.0  # Placeholder avg_order_value
        ]

    def _calculate_confidence_interval(self, prediction: float, accuracy: float) -> Dict[str, float]:
        """Calculate confidence interval for prediction"""
        margin = prediction * (1 - accuracy)
        return {
            'lower_bound': max(0, prediction - margin),
            'upper_bound': prediction + margin,
            'confidence_level': accuracy
        }

    async def predict_churn(self, user_id: str) -> Dict[str, Any]:
        """Predict churn probability for a specific user"""
        try:
            model = self.prediction_models.get("churn_prediction")
            if not model or not model.model:
                return {'churn_probability': 0.5, 'method': 'baseline'}

            # Get user features
            features = await self._get_user_churn_features(user_id)

            # Make prediction
            churn_probability = model.model.predict_proba([features])[0][1]

            # Get feature importance
            if hasattr(model.model, 'feature_importances_'):
                feature_importance = dict(zip(model.features, model.model.feature_importances_))
            else:
                feature_importance = {}

            return {
                'user_id': user_id,
                'churn_probability': float(churn_probability),
                'risk_level': self._categorize_churn_risk(churn_probability),
                'features': features,
                'feature_importance': feature_importance,
                'recommendations': self._generate_churn_recommendations(churn_probability)
            }

        except Exception as e:
            logger.error(f"Error predicting churn for user {user_id}: {e}")
            return {'error': str(e)}

    async def _get_user_churn_features(self, user_id: str) -> List[float]:
        """Get features for churn prediction"""
        # Get user activity data
        session_count = await self.redis_client.get(f"user_sessions:{user_id}") or 0
        last_login = await self.redis_client.get(f"last_login:{user_id}")
        days_since_login = 30  # Default

        if last_login:
            last_login_date = datetime.fromisoformat(last_login.decode())
            days_since_login = (datetime.utcnow() - last_login_date).days

        purchase_count = await self.redis_client.get(f"user_purchases:{user_id}") or 0
        support_tickets = await self.redis_client.get(f"user_support_tickets:{user_id}") or 0

        return [
            float(session_count),
            float(days_since_login),
            float(purchase_count),
            float(support_tickets),
            1800.0  # Placeholder avg_session_duration
        ]

    def _categorize_churn_risk(self, probability: float) -> str:
        """Categorize churn risk level"""
        if probability >= 0.8:
            return "very_high"
        elif probability >= 0.6:
            return "high"
        elif probability >= 0.4:
            return "medium"
        elif probability >= 0.2:
            return "low"
        else:
            return "very_low"

    def _generate_churn_recommendations(self, churn_probability: float) -> List[str]:
        """Generate recommendations based on churn risk"""
        recommendations = []

        if churn_probability >= 0.8:
            recommendations.extend([
                "Immediate intervention required - contact user",
                "Offer significant discount or incentive",
                "Assign customer success manager"
            ])
        elif churn_probability >= 0.6:
            recommendations.extend([
                "Send personalized re-engagement campaign",
                "Offer targeted promotions",
                "Schedule outreach call"
            ])
        elif churn_probability >= 0.4:
            recommendations.extend([
                "Send educational content",
                "Highlight unused features",
                "Request feedback"
            ])

        return recommendations

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            last_month = today - timedelta(days=30)

            dashboard_data = {
                'timestamp': now.isoformat(),
                'kpis': {},
                'real_time_metrics': {},
                'funnel_analysis': {},
                'revenue_prediction': {},
                'alerts': []
            }

            # Calculate key KPIs
            key_kpis = ["daily_revenue", "monthly_active_users", "conversion_rate", "churn_rate"]
            for kpi_id in key_kpis:
                kpi_data = await self.calculate_kpi(kpi_id, last_month, today)
                dashboard_data['kpis'][kpi_id] = kpi_data

            # Get real-time metrics
            dashboard_data['real_time_metrics'] = await self._get_real_time_dashboard_metrics()

            # Get funnel analysis
            funnel_analysis = await self.analyze_funnel("user_acquisition", last_month, today)
            dashboard_data['funnel_analysis'] = funnel_analysis

            # Get revenue prediction
            revenue_prediction = await self.predict_revenue(7)
            dashboard_data['revenue_prediction'] = revenue_prediction

            # Check for alerts
            dashboard_data['alerts'] = await self._check_alerts()

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}

    async def _get_real_time_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        # Get active users
        active_user_keys = await self.redis_client.keys("active_users:*")
        active_users = len(active_user_keys)

        # Get session metrics
        session_keys = await self.redis_client.keys("session:*")
        active_sessions = len(session_keys)

        # Get event counts
        event_counts = await self.redis_client.hgetall("real_time:events")
        events = {k.decode(): int(v) for k, v in event_counts.items()}

        return {
            'active_users': active_users,
            'active_sessions': active_sessions,
            'events_last_hour': events,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for KPI alerts"""
        alerts = []

        for kpi_id, kpi in self.kpis.items():
            if not kpi.active:
                continue

            # Get latest KPI value
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            kpi_result = await self.calculate_kpi(kpi_id, today - timedelta(days=1), today)
            if 'value' in kpi_result:
                value = kpi_result['value']

                # Check thresholds
                if kpi.alert_threshold_min and value < kpi.alert_threshold_min:
                    alerts.append({
                        'type': 'kpi_alert_low',
                        'kpi_id': kpi_id,
                        'kpi_name': kpi.name,
                        'current_value': value,
                        'threshold': kpi.alert_threshold_min,
                        'severity': 'warning',
                        'message': f"{kpi.name} is below minimum threshold"
                    })

                if kpi.alert_threshold_max and value > kpi.alert_threshold_max:
                    alerts.append({
                        'type': 'kpi_alert_high',
                        'kpi_id': kpi_id,
                        'kpi_name': kpi.name,
                        'current_value': value,
                        'threshold': kpi.alert_threshold_max,
                        'severity': 'warning',
                        'message': f"{kpi.name} is above maximum threshold"
                    })

        return alerts

    async def _metric_collector(self):
        """Background task to collect and process metrics"""
        while True:
            try:
                logger.info("Running metric collection...")

                # Process events from stream
                events = await self.redis_client.lrange("events_stream", 0, 1000)
                if events:
                    for event_bytes in events:
                        event_data = json.loads(event_bytes)
                        # Process event (already handled in track_event)

                    # Remove processed events
                    await self.redis_client.ltrim("events_stream", 1000, -1)

                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                logger.error(f"Error in metric collector: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error

    async def _kpi_calculator(self):
        """Background task to calculate KPIs"""
        while True:
            try:
                logger.info("Calculating KPIs...")

                now = datetime.utcnow()
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)

                # Calculate daily KPIs
                for kpi_id, kpi in self.kpis.items():
                    if kpi.active and kpi.time_granularity in [TimeGranularity.DAILY, TimeGranularity.REAL_TIME]:
                        await self.calculate_kpi(kpi_id, today - timedelta(days=1), today)

                # Calculate hourly KPIs
                for kpi_id, kpi in self.kpis.items():
                    if kpi.active and kpi.time_granularity == TimeGranularity.HOURLY:
                        hour_ago = now - timedelta(hours=1)
                        await self.calculate_kpi(kpi_id, hour_ago, now)

                await asyncio.sleep(3600)  # Calculate every hour

            except Exception as e:
                logger.error(f"Error in KPI calculator: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _cohort_analyzer(self):
        """Background task to analyze cohorts"""
        while True:
            try:
                logger.info("Running cohort analysis...")

                # Run weekly cohort analysis
                if datetime.utcnow().weekday() == 0:  # Monday
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=90)

                    for cohort_type in [CohortType.SIGNUP_DATE, CohortType.ACQUISITION_CHANNEL]:
                        await self.cohort_analysis(cohort_type, start_date, end_date)

                await asyncio.sleep(86400)  # Run daily

            except Exception as e:
                logger.error(f"Error in cohort analyzer: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _prediction_trainer(self):
        """Background task to train ML models"""
        while True:
            try:
                logger.info("Training prediction models...")

                # Train models weekly
                for model_id, model in self.prediction_models.items():
                    if model.active:
                        await self._train_model(model)

                await asyncio.sleep(86400 * 7)  # Train weekly

            except Exception as e:
                logger.error(f"Error in prediction trainer: {e}")
                await asyncio.sleep(86400)  # Wait 1 day on error

    async def _train_model(self, model: PredictionModel):
        """Train a specific ML model"""
        try:
            # Get training data
            X, y = await self._get_training_data(model)

            if len(X) < 10:  # Need minimum data
                logger.warning(f"Insufficient data for model {model.name}")
                return

            # Train model
            if model.model_type == "regression":
                model.model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model.model_type == "classification":
                model.model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                return

            model.model.fit(X, y)
            model.accuracy = model.model.score(X, y)
            model.last_trained = datetime.utcnow()

            logger.info(f"Trained model {model.name} with accuracy {model.accuracy:.3f}")

        except Exception as e:
            logger.error(f"Error training model {model.name}: {e}")

    async def _get_training_data(self, model: PredictionModel) -> Tuple[List, List]:
        """Get training data for model"""
        # This is a simplified implementation
        # In real system, would query database and prepare features properly
        X = [[1, 2, 3, 4] for _ in range(100)]  # Placeholder features
        y = [10, 20, 30, 40] * 25  # Placeholder targets
        return X, y

    async def _alert_monitor(self):
        """Background task to monitor alerts"""
        while True:
            try:
                logger.info("Checking alerts...")

                alerts = await self._check_alerts()

                if alerts:
                    logger.warning(f"Found {len(alerts)} alerts")
                    # Would send notifications here

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in alert monitor: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def get_daily_revenue(self, date: datetime) -> float:
        """Get daily revenue for specific date"""
        # Simplified implementation
        # In real system, would query revenue transactions
        return 1000.0  # Placeholder

# Database models
class AnalyticsEventDB(Base):
    """Analytics event database model"""
    __tablename__ = 'analytics_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String, nullable=False, unique=True)
    user_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    properties = Column(JSON)
    session_id = Column(String)
    ip_address = Column(String)
    user_agent = Column(Text)
    platform = Column(String)
    country = Column(String)

class KPIDataDB(Base):
    """KPI data database model"""
    __tablename__ = 'kpi_data'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_id = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    dimensions = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_analytics'
        }

        analytics = AnalyticsEngine(config)
        await analytics.initialize()

        # Track some events
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id="user_123",
            event_type="purchase",
            event_name="completed_purchase",
            timestamp=datetime.utcnow(),
            properties={"amount": 29.99, "item": "premium_subscription"},
            platform="web"
        )

        result = await analytics.track_event(event)
        print(f"Tracked event: {result}")

        # Calculate KPI
        kpi_result = await analytics.calculate_kpi(
            "daily_revenue",
            datetime.utcnow() - timedelta(days=7),
            datetime.utcnow()
        )
        print(f"KPI result: {kpi_result}")

        # Get dashboard data
        dashboard = await analytics.get_dashboard_data()
        print(f"Dashboard data keys: {list(dashboard.keys())}")

        # Predict revenue
        prediction = await analytics.predict_revenue(7)
        print(f"Revenue prediction: {prediction}")

    asyncio.run(main())