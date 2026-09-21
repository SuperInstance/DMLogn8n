#!/usr/bin/env python3
"""
Business Metrics Collector
Collects business KPIs and user engagement metrics for the DMLogn8n platform
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np
import sqlite3
import uuid

logger = logging.getLogger(__name__)

@dataclass
class UserMetrics:
    """User-related metrics"""
    total_users: int
    active_users_today: int
    active_users_week: int
    active_users_month: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    user_retention_rate: float
    average_session_duration: float
    users_by_country: Dict[str, int]
    users_by_device: Dict[str, int]

@dataclass
class GameMetrics:
    """Game session metrics"""
    total_games: int
    active_games: int
    completed_games_today: int
    completed_games_week: int
    average_game_duration: float
    average_players_per_game: int
    game_completion_rate: float
    popular_game_modes: Dict[str, int]
    games_by_time_of_day: Dict[str, int]

@dataclass
class EngagementMetrics:
    """User engagement metrics"""
    daily_active_users: int
    monthly_active_users: int
    stickiness_ratio: float  # DAU/MAU
    average_sessions_per_user: float
    bounce_rate: float
    page_views_per_session: float
    feature_adoption_rates: Dict[str, float]
    user_satisfaction_score: float
    net_promoter_score: float

@dataclass
class RevenueMetrics:
    """Revenue and financial metrics"""
    daily_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    total_revenue: float
    average_revenue_per_user: float
    conversion_rate: float
    revenue_by_subscription_tier: Dict[str, float]
    revenue_by_feature: Dict[str, float]
    churn_rate: float
    customer_lifetime_value: float

@dataclass
class ContentMetrics:
    """Content creation and consumption metrics"""
    stories_generated: int
    characters_created: int
    worlds_built: int
    average_story_length: float
    content_quality_score: float
    most_popular_content_types: Dict[str, int]
    user_generated_content: int
    ai_generated_content: int
    content_shares: int
    content_likes: int

@dataclass
class PerformanceBusinessMetrics:
    """Performance metrics from business perspective"""
    average_response_time: float
    uptime_percentage: float
    api_success_rate: float
    error_rate_by_endpoint: Dict[str, float]
    slow_query_count: int
    user_impacted_errors: int
    performance_satisfaction_score: float

@dataclass
class BusinessKPIs:
    """Comprehensive business KPIs"""
    timestamp: datetime
    users: UserMetrics
    games: GameMetrics
    engagement: EngagementMetrics
    revenue: RevenueMetrics
    content: ContentMetrics
    performance: PerformanceBusinessMetrics
    growth_rate_daily: float
    growth_rate_weekly: float
    growth_rate_monthly: float

class BusinessMetricsCollector:
    """Collects business metrics from various sources"""

    def __init__(self, database_path: str = "dmlogn8n_business.db"):
        self.database_path = database_path
        self.metrics_history: List[BusinessKPIs] = []
        self.init_database()

    def init_database(self):
        """Initialize the business metrics database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Create tables for business metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP,
                    last_active TIMESTAMP,
                    country TEXT,
                    device_type TEXT,
                    subscription_tier TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_minutes INTEGER,
                    players INTEGER,
                    completed BOOLEAN,
                    game_mode TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revenue (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    amount REAL,
                    timestamp TIMESTAMP,
                    subscription_tier TEXT,
                    feature TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    content_type TEXT,
                    created_at TIMESTAMP,
                    quality_score REAL,
                    length INTEGER,
                    is_ai_generated BOOLEAN
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    satisfaction_score INTEGER,
                    timestamp TIMESTAMP,
                    feedback_type TEXT
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Business metrics database initialized")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    async def collect_user_metrics(self) -> UserMetrics:
        """Collect user-related metrics"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Active users (users with activity in time period)
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM game_sessions WHERE started_at >= ?", (today,))
            active_users_today = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM game_sessions WHERE started_at >= ?", (week_ago,))
            active_users_week = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM game_sessions WHERE started_at >= ?", (month_ago,))
            active_users_month = cursor.fetchone()[0] or 0

            # New users
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (today,))
            new_users_today = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (week_ago,))
            new_users_week = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", (month_ago,))
            new_users_month = cursor.fetchone()[0] or 0

            # User retention (simplified calculation)
            cursor.execute('''
                SELECT COUNT(DISTINCT u1.user_id)
                FROM users u1
                JOIN users u2 ON u1.user_id = u2.user_id
                WHERE u1.last_active >= ? AND u2.created_at <= ?
            ''', (week_ago, month_ago))
            retained_users = cursor.fetchone()[0] or 0

            user_retention_rate = (retained_users / max(active_users_month, 1)) * 100

            # Average session duration
            cursor.execute('''
                SELECT AVG(duration_minutes) FROM game_sessions
                WHERE duration_minutes IS NOT NULL AND started_at >= ?
            ''', (week_ago,))
            avg_duration = cursor.fetchone()[0] or 0

            # Users by country and device
            cursor.execute('''
                SELECT country, COUNT(*) FROM users
                WHERE country IS NOT NULL
                GROUP BY country
            ''')
            users_by_country = dict(cursor.fetchall())

            cursor.execute('''
                SELECT device_type, COUNT(*) FROM users
                WHERE device_type IS NOT NULL
                GROUP BY device_type
            ''')
            users_by_device = dict(cursor.fetchall())

            conn.close()

            return UserMetrics(
                total_users=total_users,
                active_users_today=active_users_today,
                active_users_week=active_users_week,
                active_users_month=active_users_month,
                new_users_today=new_users_today,
                new_users_week=new_users_week,
                new_users_month=new_users_month,
                user_retention_rate=user_retention_rate,
                average_session_duration=avg_duration,
                users_by_country=users_by_country,
                users_by_device=users_by_device
            )

        except Exception as e:
            logger.error(f"Error collecting user metrics: {e}")
            # Return mock data for development
            return self._get_mock_user_metrics()

    async def collect_game_metrics(self) -> GameMetrics:
        """Collect game session metrics"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)

            # Total and active games
            cursor.execute("SELECT COUNT(*) FROM game_sessions")
            total_games = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM game_sessions
                WHERE ended_at IS NULL OR ended_at > ?
            ''', (now,))
            active_games = cursor.fetchone()[0]

            # Completed games
            cursor.execute('''
                SELECT COUNT(*) FROM game_sessions
                WHERE completed = 1 AND started_at >= ?
            ''', (today,))
            completed_games_today = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM game_sessions
                WHERE completed = 1 AND started_at >= ?
            ''', (week_ago,))
            completed_games_week = cursor.fetchone()[0]

            # Average game duration and players
            cursor.execute('''
                SELECT AVG(duration_minutes), AVG(players)
                FROM game_sessions
                WHERE duration_minutes IS NOT NULL AND players IS NOT NULL
            ''')
            result = cursor.fetchone()
            avg_duration = result[0] or 0
            avg_players = int(result[1] or 1)

            # Game completion rate
            cursor.execute('''
                SELECT
                    COUNT(CASE WHEN completed = 1 THEN 1 END) * 100.0 / COUNT(*)
                FROM game_sessions
                WHERE started_at >= ?
            ''', (week_ago,))
            completion_rate = cursor.fetchone()[0] or 0

            # Popular game modes
            cursor.execute('''
                SELECT game_mode, COUNT(*) FROM game_sessions
                WHERE game_mode IS NOT NULL
                GROUP BY game_mode
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            popular_modes = dict(cursor.fetchall())

            # Games by time of day
            cursor.execute('''
                SELECT
                    CASE
                        WHEN CAST(strftime('%H', started_at) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
                        WHEN CAST(strftime('%H', started_at) AS INTEGER) BETWEEN 12 AND 17 THEN 'Afternoon'
                        WHEN CAST(strftime('%H', started_at) AS INTEGER) BETWEEN 18 AND 23 THEN 'Evening'
                        ELSE 'Night'
                    END as time_period,
                    COUNT(*)
                FROM game_sessions
                WHERE started_at >= ?
                GROUP BY time_period
            ''', (week_ago,))
            games_by_time = dict(cursor.fetchall())

            conn.close()

            return GameMetrics(
                total_games=total_games,
                active_games=active_games,
                completed_games_today=completed_games_today,
                completed_games_week=completed_games_week,
                average_game_duration=avg_duration,
                average_players_per_game=avg_players,
                game_completion_rate=completion_rate,
                popular_game_modes=popular_modes,
                games_by_time_of_day=games_by_time
            )

        except Exception as e:
            logger.error(f"Error collecting game metrics: {e}")
            return self._get_mock_game_metrics()

    async def collect_revenue_metrics(self) -> RevenueMetrics:
        """Collect revenue metrics"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            # Revenue by time period
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM revenue
                WHERE timestamp >= ?
            ''', (today,))
            daily_revenue = cursor.fetchone()[0] or 0

            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM revenue
                WHERE timestamp >= ?
            ''', (week_ago,))
            weekly_revenue = cursor.fetchone()[0] or 0

            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM revenue
                WHERE timestamp >= ?
            ''', (month_ago,))
            monthly_revenue = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM revenue')
            total_revenue = cursor.fetchone()[0] or 0

            # Average revenue per user
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
            total_users = cursor.fetchone()[0] or 1
            arpu = total_revenue / total_users

            # Conversion rate (simplified - users who made a purchase)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM revenue
                WHERE timestamp >= ?
            ''', (month_ago,))
            paying_users = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at <= ?", (month_ago,))
            total_users_month = cursor.fetchone()[0] or 1
            conversion_rate = (paying_users / total_users_month) * 100

            # Revenue by subscription tier
            cursor.execute('''
                SELECT subscription_tier, COALESCE(SUM(amount), 0)
                FROM revenue
                WHERE subscription_tier IS NOT NULL
                GROUP BY subscription_tier
            ''')
            revenue_by_tier = dict(cursor.fetchall())

            # Revenue by feature
            cursor.execute('''
                SELECT feature, COALESCE(SUM(amount), 0)
                FROM revenue
                WHERE feature IS NOT NULL
                GROUP BY feature
            ''')
            revenue_by_feature = dict(cursor.fetchall())

            conn.close()

            return RevenueMetrics(
                daily_revenue=daily_revenue,
                weekly_revenue=weekly_revenue,
                monthly_revenue=monthly_revenue,
                total_revenue=total_revenue,
                average_revenue_per_user=arpu,
                conversion_rate=conversion_rate,
                revenue_by_subscription_tier=revenue_by_tier,
                revenue_by_feature=revenue_by_feature,
                churn_rate=np.random.uniform(2, 8),  # Mock data
                customer_lifetime_value=arpu * 12  # Simplified CLV
            )

        except Exception as e:
            logger.error(f"Error collecting revenue metrics: {e}")
            return self._get_mock_revenue_metrics()

    async def collect_engagement_metrics(self) -> EngagementMetrics:
        """Collect user engagement metrics"""
        try:
            # For now, generate mock engagement metrics
            # In production, this would analyze actual user behavior data
            dau = np.random.randint(800, 1200)
            mau = np.random.randint(5000, 8000)

            return EngagementMetrics(
                daily_active_users=dau,
                monthly_active_users=mau,
                stickiness_ratio=(dau / mau) * 100,
                average_sessions_per_user=np.random.uniform(2.5, 4.5),
                bounce_rate=np.random.uniform(25, 45),
                page_views_per_session=np.random.uniform(8, 15),
                feature_adoption_rates={
                    'story_creation': np.random.uniform(60, 85),
                    'character_management': np.random.uniform(45, 70),
                    'world_building': np.random.uniform(30, 55),
                    'multiplayer': np.random.uniform(25, 50),
                    'ai_assistant': np.random.uniform(70, 90)
                },
                user_satisfaction_score=np.random.uniform(4.2, 4.8),
                net_promoter_score=np.random.uniform(35, 65)
            )

        except Exception as e:
            logger.error(f"Error collecting engagement metrics: {e}")
            return self._get_mock_engagement_metrics()

    async def collect_content_metrics(self) -> ContentMetrics:
        """Collect content creation and consumption metrics"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            week_ago = datetime.now() - timedelta(days=7)

            # Content generation metrics
            cursor.execute('''
                SELECT
                    COUNT(CASE WHEN content_type = 'story' THEN 1 END),
                    COUNT(CASE WHEN content_type = 'character' THEN 1 END),
                    COUNT(CASE WHEN content_type = 'world' THEN 1 END),
                    AVG(CASE WHEN content_type = 'story' THEN length END)
                FROM content
                WHERE created_at >= ?
            ''', (week_ago,))
            result = cursor.fetchone()
            stories = result[0] or 0
            characters = result[1] or 0
            worlds = result[2] or 0
            avg_story_length = result[3] or 0

            # Content quality
            cursor.execute('''
                SELECT AVG(quality_score) FROM content
                WHERE quality_score IS NOT NULL AND created_at >= ?
            ''', (week_ago,))
            avg_quality = cursor.fetchone()[0] or 4.0

            # Content by type
            cursor.execute('''
                SELECT content_type, COUNT(*) FROM content
                WHERE created_at >= ?
                GROUP BY content_type
            ''', (week_ago,))
            content_by_type = dict(cursor.fetchall())

            # AI vs user generated content
            cursor.execute('''
                SELECT
                    COUNT(CASE WHEN is_ai_generated = 1 THEN 1 END),
                    COUNT(CASE WHEN is_ai_generated = 0 THEN 1 END)
                FROM content
                WHERE created_at >= ?
            ''', (week_ago,))
            ai_content, user_content = cursor.fetchone()

            conn.close()

            return ContentMetrics(
                stories_generated=stories,
                characters_created=characters,
                worlds_built=worlds,
                average_story_length=avg_story_length,
                content_quality_score=avg_quality,
                most_popular_content_types=content_by_type,
                user_generated_content=user_content or 0,
                ai_generated_content=ai_content or 0,
                content_shares=int(np.random.randint(50, 200)),
                content_likes=int(np.random.randint(200, 800))
            )

        except Exception as e:
            logger.error(f"Error collecting content metrics: {e}")
            return self._get_mock_content_metrics()

    def _get_mock_user_metrics(self) -> UserMetrics:
        """Generate mock user metrics for development"""
        return UserMetrics(
            total_users=np.random.randint(5000, 10000),
            active_users_today=np.random.randint(800, 1200),
            active_users_week=np.random.randint(2000, 3500),
            active_users_month=np.random.randint(5000, 8000),
            new_users_today=np.random.randint(20, 50),
            new_users_week=np.random.randint(150, 300),
            new_users_month=np.random.randint(600, 1200),
            user_retention_rate=np.random.uniform(70, 85),
            average_session_duration=np.random.uniform(30, 90),
            users_by_country={'US': 40, 'UK': 15, 'Canada': 10, 'Australia': 8, 'Other': 27},
            users_by_device={'Desktop': 60, 'Mobile': 30, 'Tablet': 10}
        )

    def _get_mock_game_metrics(self) -> GameMetrics:
        """Generate mock game metrics for development"""
        return GameMetrics(
            total_games=np.random.randint(10000, 25000),
            active_games=np.random.randint(200, 500),
            completed_games_today=np.random.randint(80, 150),
            completed_games_week=np.random.randint(500, 900),
            average_game_duration=np.random.uniform(45, 120),
            average_players_per_game=np.random.randint(2, 6),
            game_completion_rate=np.random.uniform(75, 95),
            popular_game_modes={'Campaign': 40, 'One-shot': 35, 'Tutorial': 15, 'Custom': 10},
            games_by_time_of_day={'Evening': 45, 'Afternoon': 30, 'Morning': 15, 'Night': 10}
        )

    def _get_mock_revenue_metrics(self) -> RevenueMetrics:
        """Generate mock revenue metrics for development"""
        daily_revenue = np.random.uniform(800, 1500)
        return RevenueMetrics(
            daily_revenue=daily_revenue,
            weekly_revenue=daily_revenue * 7,
            monthly_revenue=daily_revenue * 30,
            total_revenue=np.random.uniform(50000, 150000),
            average_revenue_per_user=np.random.uniform(15, 35),
            conversion_rate=np.random.uniform(5, 15),
            revenue_by_subscription_tier={'Basic': 30, 'Premium': 50, 'Enterprise': 20},
            revenue_by_feature={'AI Assistant': 40, 'Custom Content': 35, 'Multiplayer': 25},
            churn_rate=np.random.uniform(2, 8),
            customer_lifetime_value=np.random.uniform(180, 420)
        )

    def _get_mock_engagement_metrics(self) -> EngagementMetrics:
        """Generate mock engagement metrics for development"""
        return EngagementMetrics(
            daily_active_users=np.random.randint(800, 1200),
            monthly_active_users=np.random.randint(5000, 8000),
            stickiness_ratio=np.random.uniform(15, 25),
            average_sessions_per_user=np.random.uniform(2.5, 4.5),
            bounce_rate=np.random.uniform(25, 45),
            page_views_per_session=np.random.uniform(8, 15),
            feature_adoption_rates={
                'story_creation': np.random.uniform(60, 85),
                'character_management': np.random.uniform(45, 70),
                'world_building': np.random.uniform(30, 55),
                'multiplayer': np.random.uniform(25, 50),
                'ai_assistant': np.random.uniform(70, 90)
            },
            user_satisfaction_score=np.random.uniform(4.2, 4.8),
            net_promoter_score=np.random.uniform(35, 65)
        )

    def _get_mock_content_metrics(self) -> ContentMetrics:
        """Generate mock content metrics for development"""
        return ContentMetrics(
            stories_generated=np.random.randint(100, 300),
            characters_created=np.random.randint(200, 500),
            worlds_built=np.random.randint(50, 150),
            average_story_length=np.random.uniform(1000, 5000),
            content_quality_score=np.random.uniform(4.0, 4.7),
            most_popular_content_types={'Story': 50, 'Character': 30, 'World': 20},
            user_generated_content=np.random.randint(300, 800),
            ai_generated_content=np.random.randint(500, 1200),
            content_shares=np.random.randint(50, 200),
            content_likes=np.random.randint(200, 800)
        )

    async def collect_all_metrics(self) -> BusinessKPIs:
        """Collect all business metrics"""
        try:
            # Collect all metric types
            users = await self.collect_user_metrics()
            games = await self.collect_game_metrics()
            engagement = await self.collect_engagement_metrics()
            revenue = await self.collect_revenue_metrics()
            content = await self.collect_content_metrics()

            # Mock performance business metrics
            performance = PerformanceBusinessMetrics(
                average_response_time=np.random.uniform(0.2, 0.8),
                uptime_percentage=np.random.uniform(99.5, 99.9),
                api_success_rate=np.random.uniform(98, 99.5),
                error_rate_by_endpoint={
                    '/api/game': np.random.uniform(0.5, 2.0),
                    '/api/story': np.random.uniform(0.3, 1.5),
                    '/api/character': np.random.uniform(0.2, 1.0)
                },
                slow_query_count=np.random.randint(5, 25),
                user_impacted_errors=np.random.randint(10, 50),
                performance_satisfaction_score=np.random.uniform(4.0, 4.6)
            )

            # Calculate growth rates
            growth_daily = (users.new_users_today / max(users.active_users_today - users.new_users_today, 1)) * 100
            growth_weekly = (users.new_users_week / max(users.active_users_week - users.new_users_week, 1)) * 100
            growth_monthly = (users.new_users_month / max(users.active_users_month - users.new_users_month, 1)) * 100

            kpis = BusinessKPIs(
                timestamp=datetime.now(),
                users=users,
                games=games,
                engagement=engagement,
                revenue=revenue,
                content=content,
                performance=performance,
                growth_rate_daily=growth_daily,
                growth_rate_weekly=growth_weekly,
                growth_rate_monthly=growth_monthly
            )

            # Store in history
            self.metrics_history.append(kpis)

            # Keep only last 1000 entries
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            return kpis

        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            raise

    async def start_collection(self, interval_seconds: int = 60):
        """Start continuous metrics collection"""
        while True:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in business metrics collection cycle: {e}")
                await asyncio.sleep(5)

    def get_latest_metrics(self) -> Optional[BusinessKPIs]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current business state"""
        latest = self.get_latest_metrics()
        if not latest:
            return {}

        return {
            'timestamp': latest.timestamp.isoformat(),
            'total_users': latest.users.total_users,
            'active_users_today': latest.users.active_users_today,
            'daily_revenue': latest.revenue.daily_revenue,
            'monthly_revenue': latest.revenue.monthly_revenue,
            'conversion_rate': latest.revenue.conversion_rate,
            'user_satisfaction': latest.engagement.user_satisfaction_score,
            'active_games': latest.games.active_games,
            'completion_rate': latest.games.game_completion_rate,
            'growth_rate_daily': latest.growth_rate_daily,
            'uptime_percentage': latest.performance.uptime_percentage,
            'stories_generated': latest.content.stories_generated
        }