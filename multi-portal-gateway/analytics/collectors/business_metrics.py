#!/usr/bin/env python3
"""
Business Metrics Collector
Collects and calculates business KPIs and metrics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import redis
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np

from ..analytics_engine import AnalyticsConfig


@dataclass
class AcquisitionMetrics:
    """User acquisition metrics"""
    new_users: int
    returning_users: int
    user_growth_rate: float
    acquisition_cost: float
    conversion_rate: float
    lead_to_user_rate: float
    source_breakdown: Dict[str, int]


@dataclass
class EngagementMetrics:
    """User engagement metrics"""
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    session_duration: float
    pages_per_session: float
    bounce_rate: float
    retention_rate: float
    churn_rate: float


@dataclass
class RevenueMetrics:
    """Revenue and monetization metrics"""
    total_revenue: float
    average_revenue_per_user: float
    average_revenue_per_paying_user: float
    subscription_revenue: float
    one_time_revenue: float
    conversion_to_paying: float
    lifetime_value: float


@dataclass
class ProductMetrics:
    """Product usage metrics"""
    characters_created: int
    sessions_completed: int
    dialogue_interactions: int
    combat_participations: int
    social_interactions: int
    feature_adoption_rates: Dict[str, float]
    user_satisfaction_score: float


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    avg_response_time: float
    error_rate: float
    uptime: float
    throughput: float
    server_load: float
    database_performance: Dict[str, float]


@dataclass
class BusinessKPIs:
    """Comprehensive business KPIs"""
    period_start: datetime
    period_end: datetime
    acquisition: AcquisitionMetrics
    engagement: EngagementMetrics
    revenue: RevenueMetrics
    product: ProductMetrics
    performance: PerformanceMetrics
    overall_health_score: float


class BusinessMetricsCollector:
    """Collects and calculates business metrics"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Initialize database tables
        self._initialize_tables()

    def _setup_logging(self) -> logging.Logger:
        """Setup business metrics logging"""
        logger = logging.getLogger("business_metrics")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for business metrics"""
        try:
            # Create business_metrics table
            create_metrics_table = """
            CREATE TABLE IF NOT EXISTS business_metrics (
                id SERIAL PRIMARY KEY,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(15,4),
                metric_metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create daily_snapshots table
            create_snapshots_table = """
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id SERIAL PRIMARY KEY,
                snapshot_date DATE NOT NULL,
                new_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                sessions INTEGER DEFAULT 0,
                revenue DECIMAL(15,2) DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(snapshot_date)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_metrics_period ON business_metrics(period_start, period_end);",
                "CREATE INDEX IF NOT EXISTS idx_metrics_type_name ON business_metrics(metric_type, metric_name);",
                "CREATE INDEX IF NOT EXISTS idx_snapshots_date ON daily_snapshots(snapshot_date);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_metrics_table))
                conn.execute(text(create_snapshots_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Business metrics tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing business metrics tables: {e}")

    async def get_business_metrics(self, start_time: datetime, end_time: datetime) -> BusinessKPIs:
        """Get comprehensive business metrics for a time period"""
        try:
            self.logger.info(f"Calculating business metrics for {start_time} to {end_time}")

            # Calculate all metric categories
            acquisition = await self._calculate_acquisition_metrics(start_time, end_time)
            engagement = await self._calculate_engagement_metrics(start_time, end_time)
            revenue = await self._calculate_revenue_metrics(start_time, end_time)
            product = await self._calculate_product_metrics(start_time, end_time)
            performance = await self._calculate_performance_metrics(start_time, end_time)

            # Calculate overall health score
            overall_health_score = self._calculate_health_score(
                acquisition, engagement, revenue, product, performance
            )

            kpis = BusinessKPIs(
                period_start=start_time,
                period_end=end_time,
                acquisition=acquisition,
                engagement=engagement,
                revenue=revenue,
                product=product,
                performance=performance,
                overall_health_score=overall_health_score
            )

            # Store metrics
            await self._store_metrics(kpis)

            return kpis

        except Exception as e:
            self.logger.error(f"Error calculating business metrics: {e}")
            raise

    async def _calculate_acquisition_metrics(self, start_time: datetime, end_time: datetime) -> AcquisitionMetrics:
        """Calculate user acquisition metrics"""
        try:
            # Get new users in period
            new_users_query = text("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
                AND user_id NOT IN (
                    SELECT DISTINCT user_id
                    FROM user_sessions
                    WHERE start_time < :start_time
                )
            """)

            # Get returning users
            returning_users_query = text("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
                AND user_id IN (
                    SELECT DISTINCT user_id
                    FROM user_sessions
                    WHERE start_time < :start_time
                )
            """)

            with self.db_engine.connect() as conn:
                new_users_result = conn.execute(new_users_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                new_users = new_users_result.scalar() or 0

                returning_users_result = conn.execute(returning_users_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                returning_users = returning_users_result.scalar() or 0

            # Get previous period for growth rate calculation
            period_length = (end_time - start_time).days
            prev_start = start_time - timedelta(days=period_length)
            prev_end = start_time

            with self.db_engine.connect() as conn:
                prev_users_result = conn.execute(new_users_query, {
                    'start_time': prev_start,
                    'end_time': prev_end
                })
                prev_new_users = prev_users_result.scalar() or 0

            # Calculate growth rate
            user_growth_rate = ((new_users - prev_new_users) / prev_new_users) if prev_new_users > 0 else 0

            # Get acquisition sources (if tracked)
            source_breakdown = await self._get_acquisition_sources(start_time, end_time)

            # Calculate conversion rates (mock data for now)
            acquisition_cost = 25.50  # Average cost per acquisition
            conversion_rate = 0.12  # 12% conversion from visitor to user
            lead_to_user_rate = 0.35  # 35% conversion from lead to user

            return AcquisitionMetrics(
                new_users=new_users,
                returning_users=returning_users,
                user_growth_rate=user_growth_rate,
                acquisition_cost=acquisition_cost,
                conversion_rate=conversion_rate,
                lead_to_user_rate=lead_to_user_rate,
                source_breakdown=source_breakdown
            )

        except Exception as e:
            self.logger.error(f"Error calculating acquisition metrics: {e}")
            return AcquisitionMetrics(0, 0, 0, 0, 0, 0, {})

    async def _calculate_engagement_metrics(self, start_time: datetime, end_time: datetime) -> EngagementMetrics:
        """Calculate user engagement metrics"""
        try:
            # Daily Active Users (DAU)
            dau = await self._get_active_users_count(start_time, end_time, 'daily')

            # Weekly Active Users (WAU)
            wau = await self._get_active_users_count(start_time, end_time, 'weekly')

            # Monthly Active Users (MAU)
            mau = await self._get_active_users_count(start_time, end_time, 'monthly')

            # Session metrics
            session_metrics = await self._get_session_metrics(start_time, end_time)
            avg_session_duration = session_metrics.get('avg_duration', 0)
            pages_per_session = session_metrics.get('avg_pages', 0)
            bounce_rate = session_metrics.get('bounce_rate', 0)

            # Retention metrics
            retention_rate = await self._calculate_retention_rate(start_time, end_time)
            churn_rate = 1 - retention_rate

            return EngagementMetrics(
                daily_active_users=dau,
                weekly_active_users=wau,
                monthly_active_users=mau,
                session_duration=avg_session_duration,
                pages_per_session=pages_per_session,
                bounce_rate=bounce_rate,
                retention_rate=retention_rate,
                churn_rate=churn_rate
            )

        except Exception as e:
            self.logger.error(f"Error calculating engagement metrics: {e}")
            return EngagementMetrics(0, 0, 0, 0, 0, 0, 0, 0)

    async def _calculate_revenue_metrics(self, start_time: datetime, end_time: datetime) -> RevenueMetrics:
        """Calculate revenue and monetization metrics"""
        try:
            # Get revenue data (mock implementation)
            revenue_data = await self._get_revenue_data(start_time, end_time)

            total_revenue = revenue_data.get('total', 0)
            subscription_revenue = revenue_data.get('subscription', 0)
            one_time_revenue = revenue_data.get('one_time', 0)
            paying_users = revenue_data.get('paying_users', 0)

            # Get total active users for ARPU calculation
            total_users = await self._get_active_users_count(start_time, end_time, 'monthly')

            # Calculate revenue metrics
            arpu = total_revenue / total_users if total_users > 0 else 0
            arppu = total_revenue / paying_users if paying_users > 0 else 0
            conversion_to_paying = paying_users / total_users if total_users > 0 else 0

            # Calculate lifetime value (simplified)
            lifetime_value = arpu * 12  # Assuming 12-month average lifetime

            return RevenueMetrics(
                total_revenue=total_revenue,
                average_revenue_per_user=arpu,
                average_revenue_per_paying_user=arppu,
                subscription_revenue=subscription_revenue,
                one_time_revenue=one_time_revenue,
                conversion_to_paying=conversion_to_paying,
                lifetime_value=lifetime_value
            )

        except Exception as e:
            self.logger.error(f"Error calculating revenue metrics: {e}")
            return RevenueMetrics(0, 0, 0, 0, 0, 0, 0)

    async def _calculate_product_metrics(self, start_time: datetime, end_time: datetime) -> ProductMetrics:
        """Calculate product usage metrics"""
        try:
            # Get product usage data from events
            product_events = await self._get_product_events(start_time, end_time)

            characters_created = product_events.get('character_created', 0)
            sessions_completed = product_events.get('session_completed', 0)
            dialogue_interactions = product_events.get('dialogue_interaction', 0)
            combat_participations = product_events.get('combat_participation', 0)
            social_interactions = product_events.get('social_interaction', 0)

            # Calculate feature adoption rates
            feature_adoption_rates = await self._calculate_feature_adoption(start_time, end_time)

            # Get user satisfaction score
            user_satisfaction_score = await self._get_satisfaction_score(start_time, end_time)

            return ProductMetrics(
                characters_created=characters_created,
                sessions_completed=sessions_completed,
                dialogue_interactions=dialogue_interactions,
                combat_participations=combat_participations,
                social_interactions=social_interactions,
                feature_adoption_rates=feature_adoption_rates,
                user_satisfaction_score=user_satisfaction_score
            )

        except Exception as e:
            self.logger.error(f"Error calculating product metrics: {e}")
            return ProductMetrics(0, 0, 0, 0, 0, {}, 0)

    async def _calculate_performance_metrics(self, start_time: datetime, end_time: datetime) -> PerformanceMetrics:
        """Calculate system performance metrics"""
        try:
            # Get performance data from monitoring systems
            performance_data = await self._get_performance_data(start_time, end_time)

            avg_response_time = performance_data.get('avg_response_time', 150)
            error_rate = performance_data.get('error_rate', 0.01)
            uptime = performance_data.get('uptime', 0.999)
            throughput = performance_data.get('throughput', 1000)
            server_load = performance_data.get('server_load', 0.65)
            database_performance = performance_data.get('database', {})

            return PerformanceMetrics(
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                uptime=uptime,
                throughput=throughput,
                server_load=server_load,
                database_performance=database_performance
            )

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(0, 0, 0, 0, 0, {})

    def _calculate_health_score(self, acquisition: AcquisitionMetrics,
                              engagement: EngagementMetrics,
                              revenue: RevenueMetrics,
                              product: ProductMetrics,
                              performance: PerformanceMetrics) -> float:
        """Calculate overall business health score"""
        try:
            # Weight different components
            weights = {
                'growth': 0.2,
                'engagement': 0.25,
                'revenue': 0.25,
                'product': 0.2,
                'performance': 0.1
            }

            # Calculate component scores (0-1 scale)
            growth_score = min(acquisition.user_growth_rate / 0.2, 1.0) if acquisition.user_growth_rate > 0 else 0
            engagement_score = (engagement.retention_rate + (1 - engagement.churn_rate)) / 2
            revenue_score = min(revenue.conversion_to_paying * 5, 1.0)  # 20% conversion is perfect
            product_score = product.user_satisfaction_score / 5.0 if product.user_satisfaction_score else 0
            performance_score = performance.uptime

            # Calculate weighted average
            health_score = (
                growth_score * weights['growth'] +
                engagement_score * weights['engagement'] +
                revenue_score * weights['revenue'] +
                product_score * weights['product'] +
                performance_score * weights['performance']
            )

            return round(health_score, 3)

        except Exception as e:
            self.logger.error(f"Error calculating health score: {e}")
            return 0.0

    async def _store_metrics(self, kpis: BusinessKPIs):
        """Store calculated metrics in database"""
        try:
            metrics_data = [
                # Acquisition metrics
                ('acquisition', 'new_users', kpis.acquisition.new_users),
                ('acquisition', 'returning_users', kpis.acquisition.returning_users),
                ('acquisition', 'user_growth_rate', kpis.acquisition.user_growth_rate),
                ('acquisition', 'acquisition_cost', kpis.acquisition.acquisition_cost),
                ('acquisition', 'conversion_rate', kpis.acquisition.conversion_rate),

                # Engagement metrics
                ('engagement', 'daily_active_users', kpis.engagement.daily_active_users),
                ('engagement', 'weekly_active_users', kpis.engagement.weekly_active_users),
                ('engagement', 'monthly_active_users', kpis.engagement.monthly_active_users),
                ('engagement', 'session_duration', kpis.engagement.session_duration),
                ('engagement', 'bounce_rate', kpis.engagement.bounce_rate),
                ('engagement', 'retention_rate', kpis.engagement.retention_rate),

                # Revenue metrics
                ('revenue', 'total_revenue', kpis.revenue.total_revenue),
                ('revenue', 'average_revenue_per_user', kpis.revenue.average_revenue_per_user),
                ('revenue', 'conversion_to_paying', kpis.revenue.conversion_to_paying),
                ('revenue', 'lifetime_value', kpis.revenue.lifetime_value),

                # Product metrics
                ('product', 'characters_created', kpis.product.characters_created),
                ('product', 'sessions_completed', kpis.product.sessions_completed),
                ('product', 'user_satisfaction_score', kpis.product.user_satisfaction_score),

                # Performance metrics
                ('performance', 'avg_response_time', kpis.performance.avg_response_time),
                ('performance', 'error_rate', kpis.performance.error_rate),
                ('performance', 'uptime', kpis.performance.uptime),

                # Overall health
                ('overall', 'health_score', kpis.overall_health_score)
            ]

            query = text("""
                INSERT INTO business_metrics (
                    period_start, period_end, metric_type, metric_name, metric_value
                ) VALUES (
                    :period_start, :period_end, :metric_type, :metric_name, :metric_value
                )
            """)

            with self.db_engine.connect() as conn:
                for metric_type, metric_name, metric_value in metrics_data:
                    conn.execute(query, {
                        'period_start': kpis.period_start,
                        'period_end': kpis.period_end,
                        'metric_type': metric_type,
                        'metric_name': metric_name,
                        'metric_value': metric_value
                    })
                conn.commit()

            self.logger.info("Business metrics stored successfully")

        except Exception as e:
            self.logger.error(f"Error storing business metrics: {e}")

    # Helper methods

    async def _get_active_users_count(self, start_time: datetime, end_time: datetime, period: str) -> int:
        """Get active users count for specified period"""
        try:
            if period == 'daily':
                # Get unique users per day and average
                query = text("""
                    SELECT AVG(daily_count) as avg_daily_users
                    FROM (
                        SELECT DATE(start_time) as date, COUNT(DISTINCT user_id) as daily_count
                        FROM user_sessions
                        WHERE start_time >= :start_time AND start_time <= :end_time
                        GROUP BY DATE(start_time)
                    ) daily_counts
                """)
            elif period == 'weekly':
                # Get unique users per week and average
                query = text("""
                    SELECT AVG(weekly_count) as avg_weekly_users
                    FROM (
                        SELECT DATE_TRUNC('week', start_time) as week, COUNT(DISTINCT user_id) as weekly_count
                        FROM user_sessions
                        WHERE start_time >= :start_time AND start_time <= :end_time
                        GROUP BY DATE_TRUNC('week', start_time)
                    ) weekly_counts
                """)
            else:  # monthly
                # Get unique users in the period
                query = text("""
                    SELECT COUNT(DISTINCT user_id) as monthly_users
                    FROM user_sessions
                    WHERE start_time >= :start_time AND start_time <= :end_time
                """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                count = result.scalar()
                return int(count) if count else 0

        except Exception as e:
            self.logger.error(f"Error getting active users count: {e}")
            return 0

    async def _get_session_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get session-related metrics"""
        try:
            query = text("""
                SELECT
                    AVG(duration) as avg_duration,
                    AVG(page_views) as avg_pages,
                    SUM(CASE WHEN page_views <= 1 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as bounce_rate
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
                AND duration IS NOT NULL
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                row = result.fetchone()

                return {
                    'avg_duration': row.avg_duration or 0,
                    'avg_pages': row.avg_pages or 0,
                    'bounce_rate': row.bounce_rate or 0
                }

        except Exception as e:
            self.logger.error(f"Error getting session metrics: {e}")
            return {'avg_duration': 0, 'avg_pages': 0, 'bounce_rate': 0}

    async def _calculate_retention_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate user retention rate"""
        try:
            # Get users from previous period
            prev_period_start = start_time - timedelta(days=30)
            prev_period_end = start_time

            prev_users_query = text("""
                SELECT DISTINCT user_id
                FROM user_sessions
                WHERE start_time >= :prev_start AND start_time <= :prev_end
            """)

            current_users_query = text("""
                SELECT DISTINCT user_id
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
            """)

            with self.db_engine.connect() as conn:
                prev_users_result = conn.execute(prev_users_query, {
                    'prev_start': prev_period_start,
                    'prev_end': prev_period_end
                })
                prev_users = {row.user_id for row in prev_users_result}

                current_users_result = conn.execute(current_users_query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                current_users = {row.user_id for row in current_users_result}

                # Calculate retention rate
                retained_users = prev_users.intersection(current_users)
                retention_rate = len(retained_users) / len(prev_users) if prev_users else 0

                return retention_rate

        except Exception as e:
            self.logger.error(f"Error calculating retention rate: {e}")
            return 0.0

    async def _get_acquisition_sources(self, start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """Get breakdown of user acquisition sources"""
        # Mock implementation - would typically track UTM parameters or referral sources
        return {
            'organic': 45,
            'social_media': 23,
            'referral': 18,
            'paid_ads': 12,
            'direct': 8
        }

    async def _get_revenue_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get revenue data for the period"""
        # Mock implementation - would typically query payment/subscription tables
        return {
            'total': 15420.50,
            'subscription': 12350.00,
            'one_time': 3070.50,
            'paying_users': 156
        }

    async def _get_product_events(self, start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """Get product usage event counts"""
        # Mock implementation - would typically query events table
        return {
            'character_created': 342,
            'session_completed': 189,
            'dialogue_interaction': 15234,
            'combat_participation': 456,
            'social_interaction': 892
        }

    async def _calculate_feature_adoption(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calculate feature adoption rates"""
        # Mock implementation
        return {
            'character_creation': 0.85,
            'dialogue_system': 0.92,
            'combat_system': 0.67,
            'social_features': 0.43,
            'marketplace': 0.28
        }

    async def _get_satisfaction_score(self, start_time: datetime, end_time: datetime) -> float:
        """Get user satisfaction score"""
        # Mock implementation - would typically aggregate survey responses or ratings
        return 4.2  # Out of 5

    async def _get_performance_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get system performance data"""
        # Mock implementation - would typically query monitoring systems
        return {
            'avg_response_time': 145,
            'error_rate': 0.008,
            'uptime': 0.9992,
            'throughput': 1250,
            'server_load': 0.68,
            'database': {
                'query_time': 25,
                'connections': 45,
                'cache_hit_rate': 0.94
            }
        }

    async def create_daily_snapshot(self, date: datetime):
        """Create daily snapshot of key metrics"""
        try:
            start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)

            # Get key metrics for the day
            new_users = await self._get_new_users_count(start_time, end_time)
            active_users = await self._get_active_users_count(start_time, end_time, 'daily')
            sessions = await self._get_sessions_count(start_time, end_time)
            revenue_data = await self._get_revenue_data(start_time, end_time)
            revenue = revenue_data.get('total', 0)
            conversions = int(new_users * 0.12)  # Mock conversion calculation

            # Store in daily snapshots
            query = text("""
                INSERT INTO daily_snapshots (
                    snapshot_date, new_users, active_users, sessions, revenue, conversions
                ) VALUES (
                    :snapshot_date, :new_users, :active_users, :sessions, :revenue, :conversions
                )
                ON CONFLICT (snapshot_date) DO UPDATE SET
                    new_users = EXCLUDED.new_users,
                    active_users = EXCLUDED.active_users,
                    sessions = EXCLUDED.sessions,
                    revenue = EXCLUDED.revenue,
                    conversions = EXCLUDED.conversions
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'snapshot_date': date.date(),
                    'new_users': new_users,
                    'active_users': active_users,
                    'sessions': sessions,
                    'revenue': revenue,
                    'conversions': conversions
                })
                conn.commit()

            self.logger.info(f"Daily snapshot created for {date.date()}")

        except Exception as e:
            self.logger.error(f"Error creating daily snapshot: {e}")

    async def _get_new_users_count(self, start_time: datetime, end_time: datetime) -> int:
        """Get new users count for period"""
        try:
            query = text("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
                AND user_id NOT IN (
                    SELECT DISTINCT user_id
                    FROM user_sessions
                    WHERE start_time < :start_time
                )
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                count = result.scalar()
                return int(count) if count else 0

        except Exception as e:
            self.logger.error(f"Error getting new users count: {e}")
            return 0

    async def _get_sessions_count(self, start_time: datetime, end_time: datetime) -> int:
        """Get sessions count for period"""
        try:
            query = text("""
                SELECT COUNT(*) as count
                FROM user_sessions
                WHERE start_time >= :start_time AND start_time <= :end_time
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'start_time': start_time,
                    'end_time': end_time
                })
                count = result.scalar()
                return int(count) if count else 0

        except Exception as e:
            self.logger.error(f"Error getting sessions count: {e}")
            return 0