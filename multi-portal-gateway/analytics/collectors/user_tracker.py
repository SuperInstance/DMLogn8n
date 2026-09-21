#!/usr/bin/env python3
"""
User Tracker
Tracks user behavior, sessions, and engagement metrics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np

from ..analytics_engine import AnalyticsEvent, AnalyticsConfig


@dataclass
class UserSession:
    """User session information"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    page_views: int = 0
    events_count: int = 0
    pages_visited: List[str] = None
    device_info: Dict[str, Any] = None
    ip_address: str = None
    user_agent: str = None
    is_active: bool = True

    def __post_init__(self):
        if self.pages_visited is None:
            self.pages_visited = []
        if self.device_info is None:
            self.device_info = {}


@dataclass
class UserBehavior:
    """User behavior metrics"""
    user_id: str
    total_sessions: int
    total_session_time: int  # seconds
    avg_session_duration: float  # seconds
    pages_per_session: float
    bounce_rate: float
    return_rate: float
    last_active: datetime
    engagement_score: float
    preferred_features: List[str]
    behavior_patterns: Dict[str, Any]


@dataclass
class UserJourney:
    """User journey through the application"""
    user_id: str
    journey_steps: List[Dict[str, Any]]
    conversion_events: List[str]
    drop_off_points: List[str]
    time_to_conversion: Optional[int] = None  # seconds
    completed_onboarding: bool = False
    created_character: bool = False
    participated_in_session: bool = False
    social_interactions: int = 0


class UserTracker:
    """Tracks user behavior and generates insights"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Session tracking
        self.active_sessions = {}
        self.session_timeout = 30 * 60  # 30 minutes

        # Initialize database tables
        self._initialize_tables()

    def _setup_logging(self) -> logging.Logger:
        """Setup user tracker logging"""
        logger = logging.getLogger("user_tracker")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for user tracking"""
        try:
            # Create user_sessions table
            create_sessions_table = """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                page_views INTEGER DEFAULT 0,
                events_count INTEGER DEFAULT 0,
                pages_visited TEXT,
                device_info TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create user_behavior table
            create_behavior_table = """
            CREATE TABLE IF NOT EXISTS user_behavior (
                user_id VARCHAR(255) PRIMARY KEY,
                total_sessions INTEGER DEFAULT 0,
                total_session_time INTEGER DEFAULT 0,
                avg_session_duration DECIMAL(10,2),
                pages_per_session DECIMAL(10,2),
                bounce_rate DECIMAL(5,4),
                return_rate DECIMAL(5,4),
                last_active TIMESTAMP,
                engagement_score DECIMAL(10,2),
                preferred_features TEXT,
                behavior_patterns TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create user_journeys table
            create_journeys_table = """
            CREATE TABLE IF NOT EXISTS user_journeys (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                journey_steps TEXT,
                conversion_events TEXT,
                drop_off_points TEXT,
                time_to_conversion INTEGER,
                completed_onboarding BOOLEAN DEFAULT FALSE,
                created_character BOOLEAN DEFAULT FALSE,
                participated_in_session BOOLEAN DEFAULT FALSE,
                social_interactions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON user_sessions(start_time);",
                "CREATE INDEX IF NOT EXISTS idx_behavior_last_active ON user_behavior(last_active);",
                "CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON user_journeys(user_id);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_sessions_table))
                conn.execute(text(create_behavior_table))
                conn.execute(text(create_journeys_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Database tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing database tables: {e}")

    async def track_session_start(self, event: AnalyticsEvent) -> UserSession:
        """Track the start of a user session"""
        try:
            session = UserSession(
                session_id=event.session_id,
                user_id=event.user_id,
                start_time=event.timestamp,
                ip_address=event.properties.get('ip_address'),
                user_agent=event.properties.get('user_agent'),
                device_info={
                    'browser': event.properties.get('browser'),
                    'os': event.properties.get('os'),
                    'device_type': event.properties.get('device_type'),
                    'screen_resolution': event.properties.get('screen_resolution')
                }
            )

            # Store in active sessions
            self.active_sessions[event.session_id] = session

            # Store in Redis for quick access
            session_key = f"user_session:{event.session_id}"
            await self.redis_client.setex(
                session_key,
                self.session_timeout * 2,
                json.dumps(asdict(session), default=str)
            )

            # Store in database
            await self._store_session(session)

            self.logger.debug(f"Session started: {event.session_id} for user {event.user_id}")
            return session

        except Exception as e:
            self.logger.error(f"Error tracking session start: {e}")
            raise

    async def track_session_activity(self, event: AnalyticsEvent):
        """Track activity within a user session"""
        try:
            session_id = event.session_id

            # Get session from active sessions or Redis
            session = self.active_sessions.get(session_id)
            if not session:
                session = await self._get_session_from_redis(session_id)
                if session:
                    self.active_sessions[session_id] = session

            if session:
                # Update session activity
                session.events_count += 1

                if event.event_type == 'page_view':
                    session.page_views += 1
                    page_url = event.properties.get('page_url')
                    if page_url and page_url not in session.pages_visited:
                        session.pages_visited.append(page_url)

                # Update in Redis
                session_key = f"user_session:{session_id}"
                await self.redis_client.setex(
                    session_key,
                    self.session_timeout * 2,
                    json.dumps(asdict(session), default=str)
                )

                # Update in database
                await self._update_session(session)

            self.logger.debug(f"Session activity tracked: {session_id}")

        except Exception as e:
            self.logger.error(f"Error tracking session activity: {e}")

    async def track_session_end(self, session_id: str, end_time: datetime = None):
        """Track the end of a user session"""
        try:
            if end_time is None:
                end_time = datetime.utcnow()

            session = self.active_sessions.get(session_id)
            if not session:
                session = await self._get_session_from_redis(session_id)

            if session:
                session.end_time = end_time
                session.duration = int((end_time - session.start_time).total_seconds())
                session.is_active = False

                # Remove from active sessions
                self.active_sessions.pop(session_id, None)

                # Update in database
                await self._update_session(session)

                # Update user behavior metrics
                await self._update_user_behavior(session.user_id)

                self.logger.debug(f"Session ended: {session_id}, duration: {session.duration}s")

        except Exception as e:
            self.logger.error(f"Error tracking session end: {e}")

    async def get_user_behavior(self, user_id: str,
                              start_time: datetime, end_time: datetime) -> UserBehavior:
        """Get comprehensive behavior data for a user"""
        try:
            # Get user's sessions in time range
            sessions = await self._get_user_sessions(user_id, start_time, end_time)

            if not sessions:
                return UserBehavior(
                    user_id=user_id,
                    total_sessions=0,
                    total_session_time=0,
                    avg_session_duration=0,
                    pages_per_session=0,
                    bounce_rate=0,
                    return_rate=0,
                    last_active=datetime.min,
                    engagement_score=0,
                    preferred_features=[],
                    behavior_patterns={}
                )

            # Calculate metrics
            total_sessions = len(sessions)
            total_session_time = sum(s.duration or 0 for s in sessions)
            avg_session_duration = total_session_time / total_sessions if total_sessions > 0 else 0

            total_pages = sum(s.page_views for s in sessions)
            pages_per_session = total_pages / total_sessions if total_sessions > 0 else 0

            # Calculate bounce rate (sessions with only 1 page view)
            bounce_sessions = sum(1 for s in sessions if s.page_views <= 1)
            bounce_rate = bounce_sessions / total_sessions if total_sessions > 0 else 0

            # Calculate return rate (sessions after the first)
            return_rate = (total_sessions - 1) / total_sessions if total_sessions > 1 else 0

            # Get last active time
            last_active = max(s.start_time for s in sessions)

            # Calculate engagement score
            engagement_score = await self._calculate_engagement_score(user_id, sessions)

            # Get preferred features
            preferred_features = await self._get_preferred_features(user_id, start_time, end_time)

            # Analyze behavior patterns
            behavior_patterns = await self._analyze_behavior_patterns(user_id, sessions)

            return UserBehavior(
                user_id=user_id,
                total_sessions=total_sessions,
                total_session_time=total_session_time,
                avg_session_duration=avg_session_duration,
                pages_per_session=pages_per_session,
                bounce_rate=bounce_rate,
                return_rate=return_rate,
                last_active=last_active,
                engagement_score=engagement_score,
                preferred_features=preferred_features,
                behavior_patterns=behavior_patterns
            )

        except Exception as e:
            self.logger.error(f"Error getting user behavior: {e}")
            raise

    async def get_user_sessions(self, user_id: str,
                              time_range: timedelta) -> List[UserSession]:
        """Get user's sessions within time range"""
        end_time = datetime.utcnow()
        start_time = end_time - time_range
        return await self._get_user_sessions(user_id, start_time, end_time)

    async def get_user_journey(self, user_id: str) -> UserJourney:
        """Get user's journey through the application"""
        try:
            # Get user's events chronologically
            events = await self._get_user_events(user_id)

            # Build journey steps
            journey_steps = []
            conversion_events = []
            drop_off_points = []

            for event in events:
                step = {
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type,
                    'page': event.properties.get('page_url'),
                    'properties': event.properties
                }
                journey_steps.append(step)

                # Track conversion events
                if event.event_type in ['character_created', 'session_completed', 'purchase_completed']:
                    conversion_events.append(event.event_type)

                # Track potential drop-off points
                if event.event_type in ['page_exit', 'session_timeout', 'error_occurred']:
                    drop_off_points.append(event.event_type)

            # Calculate time to first conversion
            time_to_conversion = None
            if conversion_events:
                first_conversion_event = next(
                    (e for e in events if e.event_type in conversion_events),
                    None
                )
                if first_conversion_event:
                    first_event = events[0]
                    time_to_conversion = int(
                        (first_conversion_event.timestamp - first_event.timestamp).total_seconds()
                    )

            # Check key milestones
            completed_onboarding = any(e.event_type == 'onboarding_completed' for e in events)
            created_character = any(e.event_type == 'character_created' for e in events)
            participated_in_session = any(e.event_type == 'game_session_started' for e in events)
            social_interactions = sum(1 for e in events if e.event_type.startswith('social_'))

            return UserJourney(
                user_id=user_id,
                journey_steps=journey_steps,
                conversion_events=conversion_events,
                drop_off_points=drop_off_points,
                time_to_conversion=time_to_conversion,
                completed_onboarding=completed_onboarding,
                created_character=created_character,
                participated_in_session=participated_in_session,
                social_interactions=social_interactions
            )

        except Exception as e:
            self.logger.error(f"Error getting user journey: {e}")
            raise

    async def get_active_users_count(self, time_window: timedelta = timedelta(minutes=5)) -> int:
        """Get count of currently active users"""
        try:
            cutoff_time = datetime.utcnow() - time_window
            pattern = f"user_session:*"

            active_users = set()
            for key in self.redis_client.scan_iter(match=pattern):
                session_data = self.redis_client.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session.get('is_active'):
                        start_time = datetime.fromisoformat(session['start_time'])
                        if start_time > cutoff_time:
                            active_users.add(session['user_id'])

            return len(active_users)

        except Exception as e:
            self.logger.error(f"Error getting active users count: {e}")
            return 0

    async def cleanup_inactive_sessions(self):
        """Clean up inactive sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.session_timeout)
            inactive_sessions = []

            for session_id, session in list(self.active_sessions.items()):
                if session.start_time < cutoff_time:
                    inactive_sessions.append(session_id)

            for session_id in inactive_sessions:
                await self.track_session_end(session_id)

            if inactive_sessions:
                self.logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")

        except Exception as e:
            self.logger.error(f"Error cleaning up inactive sessions: {e}")

    # Private helper methods

    async def _store_session(self, session: UserSession):
        """Store session in database"""
        try:
            query = text("""
                INSERT INTO user_sessions (
                    session_id, user_id, start_time, end_time, duration,
                    page_views, events_count, pages_visited, device_info,
                    ip_address, user_agent, is_active
                ) VALUES (
                    :session_id, :user_id, :start_time, :end_time, :duration,
                    :page_views, :events_count, :pages_visited, :device_info,
                    :ip_address, :user_agent, :is_active
                )
                ON CONFLICT (session_id) DO UPDATE SET
                    end_time = EXCLUDED.end_time,
                    duration = EXCLUDED.duration,
                    page_views = EXCLUDED.page_views,
                    events_count = EXCLUDED.events_count,
                    pages_visited = EXCLUDED.pages_visited,
                    is_active = EXCLUDED.is_active
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'session_id': session.session_id,
                    'user_id': session.user_id,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'duration': session.duration,
                    'page_views': session.page_views,
                    'events_count': session.events_count,
                    'pages_visited': json.dumps(session.pages_visited),
                    'device_info': json.dumps(session.device_info),
                    'ip_address': session.ip_address,
                    'user_agent': session.user_agent,
                    'is_active': session.is_active
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing session: {e}")

    async def _update_session(self, session: UserSession):
        """Update session in database"""
        await self._store_session(session)  # Using UPSERT

    async def _get_session_from_redis(self, session_id: str) -> Optional[UserSession]:
        """Get session from Redis"""
        try:
            session_key = f"user_session:{session_id}"
            session_data = self.redis_client.get(session_key)
            if session_data:
                data = json.loads(session_data)
                return UserSession(
                    session_id=data['session_id'],
                    user_id=data['user_id'],
                    start_time=datetime.fromisoformat(data['start_time']),
                    end_time=datetime.fromisoformat(data['end_time']) if data['end_time'] else None,
                    duration=data['duration'],
                    page_views=data['page_views'],
                    events_count=data['events_count'],
                    pages_visited=data['pages_visited'],
                    device_info=data['device_info'],
                    ip_address=data['ip_address'],
                    user_agent=data['user_agent'],
                    is_active=data['is_active']
                )
        except Exception as e:
            self.logger.error(f"Error getting session from Redis: {e}")
        return None

    async def _get_user_sessions(self, user_id: str,
                               start_time: datetime, end_time: datetime) -> List[UserSession]:
        """Get user's sessions from database"""
        try:
            query = text("""
                SELECT * FROM user_sessions
                WHERE user_id = :user_id
                AND start_time >= :start_time
                AND start_time <= :end_time
                ORDER BY start_time DESC
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {
                    'user_id': user_id,
                    'start_time': start_time,
                    'end_time': end_time
                })
                rows = result.fetchall()

            sessions = []
            for row in rows:
                session = UserSession(
                    session_id=row.session_id,
                    user_id=row.user_id,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    duration=row.duration,
                    page_views=row.page_views,
                    events_count=row.events_count,
                    pages_visited=json.loads(row.pages_visited) if row.pages_visited else [],
                    device_info=json.loads(row.device_info) if row.device_info else {},
                    ip_address=row.ip_address,
                    user_agent=row.user_agent,
                    is_active=row.is_active
                )
                sessions.append(session)

            return sessions

        except Exception as e:
            self.logger.error(f"Error getting user sessions: {e}")
            return []

    async def _update_user_behavior(self, user_id: str):
        """Update user behavior metrics"""
        try:
            # Get last 90 days of sessions
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)
            sessions = await self._get_user_sessions(user_id, start_time, end_time)

            if not sessions:
                return

            # Calculate metrics
            total_sessions = len(sessions)
            total_session_time = sum(s.duration or 0 for s in sessions)
            avg_session_duration = total_session_time / total_sessions if total_sessions > 0 else 0

            total_pages = sum(s.page_views for s in sessions)
            pages_per_session = total_pages / total_sessions if total_sessions > 0 else 0

            bounce_sessions = sum(1 for s in sessions if s.page_views <= 1)
            bounce_rate = bounce_sessions / total_sessions if total_sessions > 0 else 0

            return_rate = (total_sessions - 1) / total_sessions if total_sessions > 1 else 0

            last_active = max(s.start_time for s in sessions)

            # Calculate engagement score
            engagement_score = await self._calculate_engagement_score(user_id, sessions)

            # Get preferred features
            preferred_features = await self._get_preferred_features(user_id, start_time, end_time)

            # Analyze behavior patterns
            behavior_patterns = await self._analyze_behavior_patterns(user_id, sessions)

            # Update or insert in database
            query = text("""
                INSERT INTO user_behavior (
                    user_id, total_sessions, total_session_time, avg_session_duration,
                    pages_per_session, bounce_rate, return_rate, last_active,
                    engagement_score, preferred_features, behavior_patterns
                ) VALUES (
                    :user_id, :total_sessions, :total_session_time, :avg_session_duration,
                    :pages_per_session, :bounce_rate, :return_rate, :last_active,
                    :engagement_score, :preferred_features, :behavior_patterns
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    total_sessions = EXCLUDED.total_sessions,
                    total_session_time = EXCLUDED.total_session_time,
                    avg_session_duration = EXCLUDED.avg_session_duration,
                    pages_per_session = EXCLUDED.pages_per_session,
                    bounce_rate = EXCLUDED.bounce_rate,
                    return_rate = EXCLUDED.return_rate,
                    last_active = EXCLUDED.last_active,
                    engagement_score = EXCLUDED.engagement_score,
                    preferred_features = EXCLUDED.preferred_features,
                    behavior_patterns = EXCLUDED.behavior_patterns,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'user_id': user_id,
                    'total_sessions': total_sessions,
                    'total_session_time': total_session_time,
                    'avg_session_duration': avg_session_duration,
                    'pages_per_session': pages_per_session,
                    'bounce_rate': bounce_rate,
                    'return_rate': return_rate,
                    'last_active': last_active,
                    'engagement_score': engagement_score,
                    'preferred_features': json.dumps(preferred_features),
                    'behavior_patterns': json.dumps(behavior_patterns)
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating user behavior: {e}")

    async def _calculate_engagement_score(self, user_id: str, sessions: List[UserSession]) -> float:
        """Calculate engagement score for a user"""
        try:
            if not sessions:
                return 0.0

            # Factors for engagement score
            session_frequency = len(sessions) / 30  # sessions per day (last 30 days)
            avg_duration = sum(s.duration or 0 for s in sessions) / len(sessions)
            avg_pages = sum(s.page_views for s in sessions) / len(sessions)

            # Normalize factors (0-1 scale)
            frequency_score = min(session_frequency / 2, 1.0)  # 2 sessions/day is perfect
            duration_score = min(avg_duration / 1800, 1.0)  # 30 minutes is perfect
            pages_score = min(avg_pages / 10, 1.0)  # 10 pages per session is perfect

            # Weighted average
            engagement_score = (frequency_score * 0.4 + duration_score * 0.3 + pages_score * 0.3)

            return round(engagement_score, 2)

        except Exception as e:
            self.logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    async def _get_preferred_features(self, user_id: str,
                                    start_time: datetime, end_time: datetime) -> List[str]:
        """Get user's preferred features based on usage"""
        try:
            # Get user's events in time range
            events = await self._get_user_events(user_id, start_time, end_time)

            # Count feature usage
            feature_counts = defaultdict(int)
            for event in events:
                if 'feature' in event.properties:
                    feature = event.properties['feature']
                    feature_counts[feature] += 1

            # Sort by usage and return top features
            sorted_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)
            return [feature for feature, count in sorted_features[:10]]

        except Exception as e:
            self.logger.error(f"Error getting preferred features: {e}")
            return []

    async def _analyze_behavior_patterns(self, user_id: str, sessions: List[UserSession]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        try:
            patterns = {}

            if not sessions:
                return patterns

            # Time of day patterns
            hours = [s.start_time.hour for s in sessions]
            hour_counts = defaultdict(int)
            for hour in hours:
                hour_counts[hour] += 1
            patterns['most_active_hours'] = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            # Day of week patterns
            weekdays = [s.start_time.weekday() for s in sessions]
            day_counts = defaultdict(int)
            for day in weekdays:
                day_counts[day] += 1
            patterns['most_active_days'] = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            # Device patterns
            device_types = [s.device_info.get('device_type', 'unknown') for s in sessions]
            device_counts = defaultdict(int)
            for device in device_types:
                device_counts[device] += 1
            patterns['preferred_devices'] = dict(device_counts)

            # Session length patterns
            durations = [s.duration or 0 for s in sessions if s.duration]
            if durations:
                patterns['avg_session_length'] = sum(durations) / len(durations)
                patterns['median_session_length'] = sorted(durations)[len(durations) // 2]

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing behavior patterns: {e}")
            return {}

    async def _get_user_events(self, user_id: str,
                             start_time: datetime = None, end_time: datetime = None) -> List[AnalyticsEvent]:
        """Get user's events from database"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(days=90)
            if end_time is None:
                end_time = datetime.utcnow()

            # This would typically query from your events table
            # For now, return empty list
            return []

        except Exception as e:
            self.logger.error(f"Error getting user events: {e}")
            return []