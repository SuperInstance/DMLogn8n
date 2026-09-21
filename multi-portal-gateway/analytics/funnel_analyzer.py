#!/usr/bin/env python3
"""
Funnel Analyzer
Conversion funnel analysis and optimization insights
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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis

from .analytics_engine import AnalyticsConfig


@dataclass
class FunnelStep:
    """Funnel step definition"""
    step_id: str
    step_name: str
    event_type: str
    description: str
    required_conditions: Dict[str, Any] = None
    time_window: Optional[int] = None  # seconds within which step must be completed


@dataclass
class FunnelDefinition:
    """Complete funnel definition"""
    funnel_id: str
    name: str
    description: str
    category: str
    steps: List[FunnelStep]
    time_window: Optional[int] = None  # Overall time window for funnel completion
    enabled: bool = True


@dataclass
class FunnelAnalysis:
    """Results of funnel analysis"""
    funnel_id: str
    period_start: datetime
    period_end: datetime
    total_users: int
    step_metrics: List[Dict[str, Any]]
    overall_conversion_rate: float
    dropoff_analysis: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    analyzed_at: datetime


@dataclass
class UserFunnelJourney:
    """Individual user's journey through funnel"""
    user_id: str
    funnel_id: str
    completed_steps: List[str]
    current_step: Optional[str]
    step_timings: Dict[str, datetime]
    conversion_time: Optional[datetime]
    dropoff_point: Optional[str]
    journey_status: str  # 'completed', 'in_progress', 'abandoned'


class FunnelAnalyzer:
    """Advanced funnel analysis engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Funnel definitions and cache
        self.funnels = {}
        self.funnel_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Initialize database tables
        self._initialize_tables()

        # Initialize default funnels
        self._initialize_default_funnels()

    def _setup_logging(self) -> logging.Logger:
        """Setup funnel analyzer logging"""
        logger = logging.getLogger("funnel_analyzer")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for funnel analysis"""
        try:
            # Create funnel_definitions table
            create_funnels_table = """
            CREATE TABLE IF NOT EXISTS funnel_definitions (
                funnel_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                steps TEXT,
                time_window INTEGER,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create funnel_analyses table
            create_analyses_table = """
            CREATE TABLE IF NOT EXISTS funnel_analyses (
                id SERIAL PRIMARY KEY,
                funnel_id VARCHAR(100) NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                total_users INTEGER,
                step_metrics TEXT,
                overall_conversion_rate DECIMAL(5,4),
                dropoff_analysis TEXT,
                insights TEXT,
                recommendations TEXT,
                analyzed_at TIMESTAMP NOT NULL,
                FOREIGN KEY (funnel_id) REFERENCES funnel_definitions(funnel_id)
            );
            """

            # Create user_funnel_journeys table
            create_journeys_table = """
            CREATE TABLE IF NOT EXISTS user_funnel_journeys (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                funnel_id VARCHAR(100) NOT NULL,
                completed_steps TEXT,
                current_step VARCHAR(100),
                step_timings TEXT,
                conversion_time TIMESTAMP,
                dropoff_point VARCHAR(100),
                journey_status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (funnel_id) REFERENCES funnel_definitions(funnel_id),
                UNIQUE(user_id, funnel_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_funnels_category ON funnel_definitions(category);",
                "CREATE INDEX IF NOT EXISTS idx_analyses_funnel_period ON funnel_analyses(funnel_id, period_start, period_end);",
                "CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON user_funnel_journeys(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_journeys_funnel_id ON user_funnel_journeys(funnel_id);",
                "CREATE INDEX IF NOT EXISTS idx_journeys_status ON user_funnel_journeys(journey_status);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_funnels_table))
                conn.execute(text(create_analyses_table))
                conn.execute(text(create_journeys_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Funnel analyzer tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing funnel analyzer tables: {e}")

    def _initialize_default_funnels(self):
        """Initialize default funnel definitions"""
        default_funnels = [
            # User Onboarding Funnel
            FunnelDefinition(
                funnel_id="user_onboarding",
                name="User Onboarding Funnel",
                description="Tracks user journey from signup to first meaningful interaction",
                category="onboarding",
                steps=[
                    FunnelStep(
                        step_id="visit",
                        step_name="Site Visit",
                        event_type="page_view",
                        description="User visits the website",
                        required_conditions={"page_url": ["/home", "/landing", "/"]},
                        time_window=None
                    ),
                    FunnelStep(
                        step_id="signup",
                        step_name="Account Signup",
                        event_type="user_signup",
                        description="User creates an account",
                        required_conditions={},
                        time_window=3600  # 1 hour after visit
                    ),
                    FunnelStep(
                        step_id="verification",
                        step_name="Email Verification",
                        event_type="email_verified",
                        description="User verifies their email address",
                        required_conditions={},
                        time_window=86400  # 24 hours after signup
                    ),
                    FunnelStep(
                        step_id="profile_completion",
                        step_name="Profile Completion",
                        event_type="profile_completed",
                        description="User completes their profile",
                        required_conditions={"completion_percentage": 100},
                        time_window=172800  # 48 hours after verification
                    ),
                    FunnelStep(
                        step_id="character_creation",
                        step_name="First Character Creation",
                        event_type="character_created",
                        description="User creates their first character",
                        required_conditions={},
                        time_window=604800  # 7 days after profile completion
                    ),
                    FunnelStep(
                        step_id="first_session",
                        step_name="First Game Session",
                        event_type="game_session_started",
                        description="User starts their first game session",
                        required_conditions={},
                        time_window=86400  # 24 hours after character creation
                    )
                ],
                time_window=1209600  # 14 days total
            ),

            # Purchase Funnel
            FunnelDefinition(
                funnel_id="purchase_conversion",
                name="Purchase Conversion Funnel",
                description="E-commerce conversion funnel from product view to purchase",
                category="commerce",
                steps=[
                    FunnelStep(
                        step_id="product_view",
                        step_name="Product View",
                        event_type="product_viewed",
                        description="User views a product",
                        required_conditions={},
                        time_window=None
                    ),
                    FunnelStep(
                        step_id="add_to_cart",
                        step_name="Add to Cart",
                        event_type="added_to_cart",
                        description="User adds product to cart",
                        required_conditions={},
                        time_window=3600  # 1 hour after product view
                    ),
                    FunnelStep(
                        step_id="checkout_start",
                        step_name="Checkout Started",
                        event_type="checkout_started",
                        description="User begins checkout process",
                        required_conditions={},
                        time_window=1800  # 30 minutes after add to cart
                    ),
                    FunnelStep(
                        step_id="payment_info",
                        step_name="Payment Information",
                        event_type="payment_info_added",
                        description="User adds payment information",
                        required_conditions={},
                        time_window=900  # 15 minutes after checkout start
                    ),
                    FunnelStep(
                        step_id="purchase_complete",
                        step_name="Purchase Completed",
                        event_type="purchase_completed",
                        description="User completes purchase",
                        required_conditions={"status": "completed"},
                        time_window=600  # 10 minutes after payment info
                    )
                ],
                time_window=7200  # 2 hours total
            ),

            # Feature Adoption Funnel
            FunnelDefinition(
                funnel_id="feature_adoption",
                name="Feature Adoption Funnel",
                description="Tracks user adoption of key features",
                category="engagement",
                steps=[
                    FunnelStep(
                        step_id="feature_discovery",
                        step_name="Feature Discovery",
                        event_type="feature_discovered",
                        description="User discovers a feature",
                        required_conditions={},
                        time_window=None
                    ),
                    FunnelStep(
                        step_id="feature_first_use",
                        step_name="First Feature Use",
                        event_type="feature_used",
                        description="User uses feature for the first time",
                        required_conditions={"first_time": True},
                        time_window=86400  # 24 hours after discovery
                    ),
                    FunnelStep(
                        step_id="feature_repeat_use",
                        step_name="Repeat Feature Use",
                        event_type="feature_used",
                        description="User uses feature again within 7 days",
                        required_conditions={"repeat_use": True},
                        time_window=604800  # 7 days after first use
                    ),
                    FunnelStep(
                        step_id="feature_mastery",
                        step_name="Feature Mastery",
                        event_type="feature_mastered",
                        description="User demonstrates advanced feature usage",
                        required_conditions={"proficiency_level": "advanced"},
                        time_window=1209600  # 14 days after repeat use
                    )
                ],
                time_window=2419200  # 28 days total
            ),

            # Social Engagement Funnel
            FunnelDefinition(
                funnel_id="social_engagement",
                name="Social Engagement Funnel",
                description="Tracks user progression through social features",
                category="social",
                steps=[
                    FunnelStep(
                        step_id="profile_view",
                        step_name="Profile View",
                        event_type="profile_viewed",
                        description="User views another user's profile",
                        required_conditions={},
                        time_window=None
                    ),
                    FunnelStep(
                        step_id="connection_request",
                        step_name="Connection Request",
                        event_type="connection_requested",
                        description="User sends a connection request",
                        required_conditions={},
                        time_window=3600  # 1 hour after profile view
                    ),
                    FunnelStep(
                        step_id="connection_accepted",
                        step_name="Connection Accepted",
                        event_type="connection_accepted",
                        description="User's connection request is accepted",
                        required_conditions={},
                        time_window=604800  # 7 days after request
                    ),
                    FunnelStep(
                        step_id="social_interaction",
                        step_name="Social Interaction",
                        event_type="social_interaction",
                        description="User engages in social interaction",
                        required_conditions={"interaction_type": ["message", "comment", "like"]},
                        time_window=86400  # 24 hours after connection
                    ),
                    FunnelStep(
                        step_id="community_contribution",
                        step_name="Community Contribution",
                        event_type="community_contribution",
                        description="User contributes to community content",
                        required_requirements={"contribution_type": ["post", "share", "create"]},
                        time_window=604800  # 7 days after interaction
                    )
                ],
                time_window=1209600  # 14 days total
            )
        ]

        for funnel in default_funnels:
            self.add_funnel(funnel)

    def add_funnel(self, funnel: FunnelDefinition):
        """Add a funnel definition"""
        try:
            # Store in database
            query = text("""
                INSERT INTO funnel_definitions (
                    funnel_id, name, description, category, steps, time_window, enabled
                ) VALUES (
                    :funnel_id, :name, :description, :category, :steps, :time_window, :enabled
                )
                ON CONFLICT (funnel_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    steps = EXCLUDED.steps,
                    time_window = EXCLUDED.time_window,
                    enabled = EXCLUDED.enabled,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'funnel_id': funnel.funnel_id,
                    'name': funnel.name,
                    'description': funnel.description,
                    'category': funnel.category,
                    'steps': json.dumps([asdict(step) for step in funnel.steps]),
                    'time_window': funnel.time_window,
                    'enabled': funnel.enabled
                })
                conn.commit()

            self.funnels[funnel.funnel_id] = funnel
            self.logger.info(f"Added funnel: {funnel.name}")

        except Exception as e:
            self.logger.error(f"Error adding funnel: {e}")

    async def analyze_funnel(self, funnel_id: str,
                           start_time: datetime = None,
                           end_time: datetime = None) -> FunnelAnalysis:
        """Analyze a conversion funnel"""
        try:
            funnel = self.funnels.get(funnel_id)
            if not funnel:
                # Load from database
                funnel = await self._load_funnel_from_db(funnel_id)
                if not funnel:
                    raise ValueError(f"Funnel not found: {funnel_id}")

            # Set default time range
            if end_time is None:
                end_time = datetime.utcnow()
            if start_time is None:
                start_time = end_time - timedelta(days=30)

            self.logger.info(f"Analyzing funnel: {funnel.name} from {start_time} to {end_time}")

            # Get users who entered the funnel
            entry_users = await self._get_funnel_entry_users(funnel, start_time, end_time)
            total_users = len(entry_users)

            if total_users == 0:
                return self._create_empty_analysis(funnel, start_time, end_time)

            # Analyze each step
            step_metrics = []
            for i, step in enumerate(funnel.steps):
                step_metric = await self._analyze_step(
                    funnel, step, entry_users, start_time, end_time, i
                )
                step_metrics.append(step_metric)

            # Calculate overall metrics
            overall_conversion_rate = self._calculate_overall_conversion_rate(step_metrics)

            # Analyze dropoffs
            dropoff_analysis = self._analyze_dropoffs(step_metrics)

            # Generate insights and recommendations
            insights = self._generate_funnel_insights(step_metrics, dropoff_analysis)
            recommendations = self._generate_recommendations(insights, dropoff_analysis)

            # Create analysis result
            analysis = FunnelAnalysis(
                funnel_id=funnel_id,
                period_start=start_time,
                period_end=end_time,
                total_users=total_users,
                step_metrics=step_metrics,
                overall_conversion_rate=overall_conversion_rate,
                dropoff_analysis=dropoff_analysis,
                insights=insights,
                recommendations=recommendations,
                analyzed_at=datetime.utcnow()
            )

            # Store analysis
            await self._store_funnel_analysis(analysis)

            self.logger.info(f"Funnel analysis completed: {funnel.name}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing funnel {funnel_id}: {e}")
            raise

    async def _get_funnel_entry_users(self, funnel: FunnelDefinition,
                                    start_time: datetime, end_time: datetime) -> List[str]:
        """Get users who entered the funnel"""
        try:
            first_step = funnel.steps[0]

            # Mock implementation - would typically query events table
            # For now, return mock user IDs
            np.random.seed(42)
            n_users = np.random.randint(500, 2000)

            return [f"user_{i:06d}" for i in range(n_users)]

        except Exception as e:
            self.logger.error(f"Error getting funnel entry users: {e}")
            return []

    async def _analyze_step(self, funnel: FunnelDefinition, step: FunnelStep,
                          entry_users: List[str], start_time: datetime, end_time: datetime,
                          step_index: int) -> Dict[str, Any]:
        """Analyze a specific funnel step"""
        try:
            # Get users who completed this step
            completed_users = await self._get_step_completed_users(
                step, entry_users, start_time, end_time
            )

            # Calculate conversion rates
            step_conversion_rate = len(completed_users) / len(entry_users) if entry_users else 0

            if step_index > 0:
                # Calculate step-to-step conversion
                previous_step_users = await self._get_step_completed_users(
                    funnel.steps[step_index - 1], entry_users, start_time, end_time
                )
                step_to_step_conversion = len(completed_users) / len(previous_step_users) if previous_step_users else 0
            else:
                step_to_step_conversion = step_conversion_rate

            # Calculate time metrics
            time_metrics = await self._calculate_step_time_metrics(step, completed_users)

            return {
                'step_id': step.step_id,
                'step_name': step.step_name,
                'step_index': step_index,
                'entry_users': len(entry_users),
                'completed_users': len(completed_users),
                'step_conversion_rate': step_conversion_rate,
                'step_to_step_conversion': step_to_step_conversion,
                'cumulative_conversion_rate': step_conversion_rate,  # Will be updated later
                'dropoff_rate': 1 - step_conversion_rate,
                'time_metrics': time_metrics,
                'user_details': {
                    'completed': completed_users[:10],  # Sample of 10 users
                    'dropoff': list(set(entry_users) - set(completed_users))[:10]  # Sample of 10 dropoff users
                }
            }

        except Exception as e:
            self.logger.error(f"Error analyzing step {step.step_id}: {e}")
            return {
                'step_id': step.step_id,
                'step_name': step.step_name,
                'error': str(e)
            }

    async def _get_step_completed_users(self, step: FunnelStep,
                                     entry_users: List[str],
                                     start_time: datetime, end_time: datetime) -> List[str]:
        """Get users who completed a specific step"""
        try:
            # Mock implementation - simulate completion based on probabilities
            completion_probabilities = {
                'visit': 1.0,
                'signup': 0.45,
                'verification': 0.38,
                'profile_completion': 0.32,
                'character_creation': 0.28,
                'first_session': 0.22,
                'product_view': 1.0,
                'add_to_cart': 0.35,
                'checkout_start': 0.28,
                'payment_info': 0.22,
                'purchase_complete': 0.18,
                'feature_discovery': 0.65,
                'feature_first_use': 0.42,
                'feature_repeat_use': 0.28,
                'feature_mastery': 0.15,
                'profile_view': 0.78,
                'connection_request': 0.35,
                'connection_accepted': 0.28,
                'social_interaction': 0.22,
                'community_contribution': 0.12
            }

            probability = completion_probabilities.get(step.step_id, 0.5)
            n_completed = int(len(entry_users) * probability)

            np.random.seed(hash(step.step_id) % 1000)
            completed_indices = np.random.choice(len(entry_users), n_completed, replace=False)

            return [entry_users[i] for i in completed_indices]

        except Exception as e:
            self.logger.error(f"Error getting step completed users: {e}")
            return []

    async def _calculate_step_time_metrics(self, step: FunnelStep,
                                        completed_users: List[str]) -> Dict[str, Any]:
        """Calculate time-related metrics for a step"""
        try:
            # Mock time metrics
            if not completed_users:
                return {
                    'avg_time_to_complete': 0,
                    'median_time_to_complete': 0,
                    'p95_time_to_complete': 0
                }

            # Generate mock time data
            np.random.seed(42)
            base_times = {
                'visit': 0,
                'signup': 300,  # 5 minutes
                'verification': 1800,  # 30 minutes
                'profile_completion': 900,  # 15 minutes
                'character_creation': 1200,  # 20 minutes
                'first_session': 600,  # 10 minutes
                'product_view': 30,
                'add_to_cart': 180,  # 3 minutes
                'checkout_start': 240,  # 4 minutes
                'payment_info': 120,  # 2 minutes
                'purchase_complete': 60,  # 1 minute
                'feature_discovery': 0,
                'feature_first_use': 120,  # 2 minutes
                'feature_repeat_use': 86400,  # 1 day
                'feature_mastery': 604800,  # 1 week
                'profile_view': 30,
                'connection_request': 120,  # 2 minutes
                'connection_accepted': 43200,  # 12 hours
                'social_interaction': 600,  # 10 minutes
                'community_contribution': 1800  # 30 minutes
            }

            base_time = base_times.get(step.step_id, 300)
            times = [base_time + np.random.normal(0, base_time * 0.3) for _ in completed_users]
            times = [max(0, t) for t in times]  # Ensure non-negative

            return {
                'avg_time_to_complete': np.mean(times),
                'median_time_to_complete': np.median(times),
                'p95_time_to_complete': np.percentile(times, 95),
                'time_unit': 'seconds'
            }

        except Exception as e:
            self.logger.error(f"Error calculating step time metrics: {e}")
            return {}

    def _calculate_overall_conversion_rate(self, step_metrics: List[Dict[str, Any]]) -> float:
        """Calculate overall funnel conversion rate"""
        try:
            if not step_metrics:
                return 0.0

            # Overall conversion is the conversion rate of the last step
            last_step = step_metrics[-1]
            return last_step.get('cumulative_conversion_rate', 0.0)

        except Exception as e:
            self.logger.error(f"Error calculating overall conversion rate: {e}")
            return 0.0

    def _analyze_dropoffs(self, step_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze dropoff points in the funnel"""
        try:
            dropoffs = []

            for i in range(len(step_metrics)):
                step = step_metrics[i]
                dropoff_rate = step.get('dropoff_rate', 0)

                if dropoff_rate > 0:
                    dropoff_analysis = {
                        'step_id': step['step_id'],
                        'step_name': step['step_name'],
                        'dropoff_rate': dropoff_rate,
                        'dropoff_users': step.get('entry_users', 0) - step.get('completed_users', 0),
                        'severity': self._assess_dropoff_severity(dropoff_rate),
                        'potential_causes': self._identify_dropoff_causes(step),
                        'priority': self._calculate_dropoff_priority(dropoff_rate, i)
                    }
                    dropoffs.append(dropoff_analysis)

            # Sort by priority
            dropoffs.sort(key=lambda x: x['priority'], reverse=True)
            return dropoffs

        except Exception as e:
            self.logger.error(f"Error analyzing dropoffs: {e}")
            return []

    def _assess_dropoff_severity(self, dropoff_rate: float) -> str:
        """Assess the severity of dropoff"""
        if dropoff_rate > 0.7:
            return 'critical'
        elif dropoff_rate > 0.5:
            return 'high'
        elif dropoff_rate > 0.3:
            return 'medium'
        else:
            return 'low'

    def _identify_dropoff_causes(self, step: Dict[str, Any]) -> List[str]:
        """Identify potential causes for dropoff"""
        causes = []

        step_name = step.get('step_name', '').lower()
        dropoff_rate = step.get('dropoff_rate', 0)

        if 'signup' in step_name and dropoff_rate > 0.5:
            causes.extend([
                'Complex registration form',
                'Too many required fields',
                'Lack of value proposition clarity'
            ])

        if 'payment' in step_name and dropoff_rate > 0.4:
            causes.extend([
                'Payment security concerns',
                'Limited payment options',
                'Unexpected costs'
            ])

        if 'verification' in step_name and dropoff_rate > 0.6:
            causes.extend([
                'Email delivery issues',
                'Complicated verification process',
                'User confusion about verification necessity'
            ])

        if 'profile' in step_name and dropoff_rate > 0.3:
            causes.extend([
                'Too much information required',
                'Lack of immediate benefit',
                'Privacy concerns'
            ])

        if not causes:
            causes.append('Unknown - requires further investigation')

        return causes

    def _calculate_dropoff_priority(self, dropoff_rate: float, step_index: int) -> float:
        """Calculate priority for addressing dropoff"""
        # Earlier steps and higher dropoff rates get higher priority
        step_weight = 1.0 / (step_index + 1)  # Earlier steps have higher weight
        dropoff_weight = dropoff_rate

        return step_weight * dropoff_weight

    def _generate_funnel_insights(self, step_metrics: List[Dict[str, Any]],
                                dropoff_analysis: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from funnel analysis"""
        insights = []

        try:
            # Overall performance insight
            if step_metrics:
                overall_conversion = step_metrics[-1].get('cumulative_conversion_rate', 0)
                if overall_conversion > 0.2:
                    insights.append(f"Strong overall conversion rate of {overall_conversion:.1%}")
                elif overall_conversion < 0.05:
                    insights.append(f"Low overall conversion rate of {overall_conversion:.1%} requires immediate attention")
                else:
                    insights.append(f"Moderate conversion rate of {overall_conversion:.1%} with room for improvement")

            # Dropoff insights
            high_dropoffs = [d for d in dropoff_analysis if d['severity'] in ['critical', 'high']]
            if high_dropoffs:
                worst_dropoff = high_dropoffs[0]
                insights.append(
                    f"Major dropoff at '{worst_dropoff['step_name']}' with {worst_dropoff['dropoff_rate']:.1%} of users leaving"
                )

            # Time-based insights
            slow_steps = []
            for step in step_metrics:
                time_metrics = step.get('time_metrics', {})
                avg_time = time_metrics.get('avg_time_to_complete', 0)
                if avg_time > 600:  # More than 10 minutes
                    slow_steps.append(step['step_name'])

            if slow_steps:
                insights.append(f"Steps taking longer than expected: {', '.join(slow_steps)}")

            # Volume insights
            if step_metrics:
                total_entry = step_metrics[0].get('entry_users', 0)
                if total_entry < 100:
                    insights.append("Low funnel entry volume suggests top-of-funnel issues")
                elif total_entry > 10000:
                    insights.append("High funnel volume provides good optimization opportunities")

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")

        return insights[:5]  # Limit to top 5 insights

    def _generate_recommendations(self, insights: List[str],
                                dropoff_analysis: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        try:
            # Recommendations based on dropoffs
            for dropoff in dropoff_analysis[:3]:  # Top 3 dropoffs
                step_name = dropoff['step_name']
                causes = dropoff.get('potential_causes', [])

                if 'signup' in step_name.lower():
                    recommendations.extend([
                        "Simplify registration form by reducing required fields",
                        "Add social login options",
                        "Improve value proposition clarity on signup page"
                    ])

                elif 'payment' in step_name.lower():
                    recommendations.extend([
                        "Add multiple payment options",
                        "Display security badges prominently",
                        "Implement guest checkout option"
                    ])

                elif 'profile' in step_name.lower():
                    recommendations.extend([
                        "Make profile completion optional or progressive",
                        "Show immediate benefits of profile completion",
                        "Reduce required profile information"
                    ])

                elif 'verification' in step_name.lower():
                    recommendations.extend([
                        "Simplify email verification process",
                        "Add alternative verification methods",
                        "Send reminder emails for unverified accounts"
                    ])

            # General recommendations
            if not recommendations:
                recommendations.extend([
                    "Implement A/B testing on problematic steps",
                    "Add user feedback mechanisms at dropoff points",
                    "Monitor user behavior patterns more closely"
                ])

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")

        return recommendations[:8]  # Limit to top 8 recommendations

    async def track_user_journey(self, user_id: str, funnel_id: str) -> UserFunnelJourney:
        """Track a specific user's journey through a funnel"""
        try:
            funnel = self.funnels.get(funnel_id)
            if not funnel:
                raise ValueError(f"Funnel not found: {funnel_id}")

            # Get user's events for the funnel period
            user_events = await self._get_user_funnel_events(user_id, funnel)

            # Analyze journey
            completed_steps = []
            current_step = None
            step_timings = {}
            dropoff_point = None

            for step in funnel.steps:
                step_events = [e for e in user_events if e['event_type'] == step.event_type]
                if step_events:
                    completed_steps.append(step.step_id)
                    step_timings[step.step_id] = step_events[0]['timestamp']
                else:
                    current_step = step.step_id
                    dropoff_point = step.step_id
                    break

            journey_status = 'completed' if len(completed_steps) == len(funnel.steps) else 'abandoned' if dropoff_point else 'in_progress'

            journey = UserFunnelJourney(
                user_id=user_id,
                funnel_id=funnel_id,
                completed_steps=completed_steps,
                current_step=current_step,
                step_timings=step_timings,
                conversion_time=step_timings.get(funnel.steps[-1].step_id) if journey_status == 'completed' else None,
                dropoff_point=dropoff_point,
                journey_status=journey_status
            )

            # Store journey
            await self._store_user_journey(journey)

            return journey

        except Exception as e:
            self.logger.error(f"Error tracking user journey: {e}")
            raise

    async def _get_user_funnel_events(self, user_id: str, funnel: FunnelDefinition) -> List[Dict[str, Any]]:
        """Get user's events relevant to the funnel"""
        # Mock implementation
        return []

    # Helper methods

    def _create_empty_analysis(self, funnel: FunnelDefinition,
                             start_time: datetime, end_time: datetime) -> FunnelAnalysis:
        """Create empty analysis when no data available"""
        return FunnelAnalysis(
            funnel_id=funnel.funnel_id,
            period_start=start_time,
            period_end=end_time,
            total_users=0,
            step_metrics=[],
            overall_conversion_rate=0.0,
            dropoff_analysis=[],
            insights=["No data available for the specified time period"],
            recommendations=["Increase top-of-funnel traffic to generate meaningful analysis"],
            analyzed_at=datetime.utcnow()
        )

    async def _store_funnel_analysis(self, analysis: FunnelAnalysis):
        """Store funnel analysis in database"""
        try:
            query = text("""
                INSERT INTO funnel_analyses (
                    funnel_id, period_start, period_end, total_users, step_metrics,
                    overall_conversion_rate, dropoff_analysis, insights, recommendations, analyzed_at
                ) VALUES (
                    :funnel_id, :period_start, :period_end, :total_users, :step_metrics,
                    :overall_conversion_rate, :dropoff_analysis, :insights, :recommendations, :analyzed_at
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'funnel_id': analysis.funnel_id,
                    'period_start': analysis.period_start,
                    'period_end': analysis.period_end,
                    'total_users': analysis.total_users,
                    'step_metrics': json.dumps(analysis.step_metrics),
                    'overall_conversion_rate': analysis.overall_conversion_rate,
                    'dropoff_analysis': json.dumps(analysis.dropoff_analysis),
                    'insights': json.dumps(analysis.insights),
                    'recommendations': json.dumps(analysis.recommendations),
                    'analyzed_at': analysis.analyzed_at
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing funnel analysis: {e}")

    async def _store_user_journey(self, journey: UserFunnelJourney):
        """Store user journey in database"""
        try:
            query = text("""
                INSERT INTO user_funnel_journeys (
                    user_id, funnel_id, completed_steps, current_step, step_timings,
                    conversion_time, dropoff_point, journey_status
                ) VALUES (
                    :user_id, :funnel_id, :completed_steps, :current_step, :step_timings,
                    :conversion_time, :dropoff_point, :journey_status
                )
                ON CONFLICT (user_id, funnel_id) DO UPDATE SET
                    completed_steps = EXCLUDED.completed_steps,
                    current_step = EXCLUDED.current_step,
                    step_timings = EXCLUDED.step_timings,
                    conversion_time = EXCLUDED.conversion_time,
                    dropoff_point = EXCLUDED.dropoff_point,
                    journey_status = EXCLUDED.journey_status,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'user_id': journey.user_id,
                    'funnel_id': journey.funnel_id,
                    'completed_steps': json.dumps(journey.completed_steps),
                    'current_step': journey.current_step,
                    'step_timings': json.dumps(journey.step_timings, default=str),
                    'conversion_time': journey.conversion_time,
                    'dropoff_point': journey.dropoff_point,
                    'journey_status': journey.journey_status
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing user journey: {e}")

    async def _load_funnel_from_db(self, funnel_id: str) -> Optional[FunnelDefinition]:
        """Load funnel definition from database"""
        try:
            query = text("""
                SELECT * FROM funnel_definitions WHERE funnel_id = :funnel_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'funnel_id': funnel_id})
                row = result.fetchone()

                if row:
                    steps_data = json.loads(row.steps)
                    steps = [FunnelStep(**step_data) for step_data in steps_data]

                    return FunnelDefinition(
                        funnel_id=row.funnel_id,
                        name=row.name,
                        description=row.description,
                        category=row.category,
                        steps=steps,
                        time_window=row.time_window,
                        enabled=row.enabled
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error loading funnel from database: {e}")
            return None

    async def get_funnel_analysis(self, funnel_id: str,
                               start_time: datetime = None,
                               end_time: datetime = None) -> Optional[FunnelAnalysis]:
        """Get existing funnel analysis"""
        try:
            if end_time is None:
                end_time = datetime.utcnow()
            if start_time is None:
                start_time = end_time - timedelta(days=30)

            query = text("""
                SELECT * FROM funnel_analyses
                WHERE funnel_id = :funnel_id
                AND period_start = :start_time
                AND period_end = :end_time
                ORDER BY analyzed_at DESC
                LIMIT 1
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'funnel_id': funnel_id,
                    'start_time': start_time,
                    'end_time': end_time
                })
                row = result.fetchone()

                if row:
                    return FunnelAnalysis(
                        funnel_id=row.funnel_id,
                        period_start=row.period_start,
                        period_end=row.period_end,
                        total_users=row.total_users,
                        step_metrics=json.loads(row.step_metrics),
                        overall_conversion_rate=row.overall_conversion_rate,
                        dropoff_analysis=json.loads(row.dropoff_analysis),
                        insights=json.loads(row.insights),
                        recommendations=json.loads(row.recommendations),
                        analyzed_at=row.analyzed_at
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error getting funnel analysis: {e}")
            return None

    def get_funnel_list(self, category: str = None) -> List[Dict[str, Any]]:
        """Get list of available funnels"""
        try:
            funnels = []
            for funnel_id, funnel in self.funnels.items():
                if category is None or funnel.category == category:
                    funnels.append({
                        'funnel_id': funnel.funnel_id,
                        'name': funnel.name,
                        'description': funnel.description,
                        'category': funnel.category,
                        'step_count': len(funnel.steps),
                        'enabled': funnel.enabled
                    })

            return funnels

        except Exception as e:
            self.logger.error(f"Error getting funnel list: {e}")
            return []

    def get_funnel_comparison(self, funnel_ids: List[str],
                           start_time: datetime = None,
                           end_time: datetime = None) -> Dict[str, Any]:
        """Compare multiple funnels"""
        try:
            if end_time is None:
                end_time = datetime.utcnow()
            if start_time is None:
                start_time = end_time - timedelta(days=30)

            comparison = {
                'period': {'start': start_time.isoformat(), 'end': end_time.isoformat()},
                'funnels': []
            }

            for funnel_id in funnel_ids:
                funnel = self.funnels.get(funnel_id)
                if funnel:
                    comparison['funnels'].append({
                        'funnel_id': funnel_id,
                        'name': funnel.name,
                        'category': funnel.category,
                        'step_count': len(funnel.steps)
                    })

            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing funnels: {e}")
            return {}