#!/usr/bin/env python3
"""
Stream Processor
Real-time event processing and analytics pipeline
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import aiohttp
import pandas as pd
import numpy as np
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import time

from ..analytics_engine import AnalyticsEvent, AnalyticsConfig


@dataclass
class StreamWindow:
    """Time window for stream processing"""
    window_id: str
    start_time: datetime
    end_time: datetime
    events: List[AnalyticsEvent]
    aggregates: Dict[str, Any]


@dataclass
class ProcessingRule:
    """Stream processing rule"""
    rule_id: str
    name: str
    condition: Callable[[AnalyticsEvent], bool]
    action: Callable[[AnalyticsEvent], Any]
    enabled: bool = True


class StreamProcessor:
    """Real-time stream processing engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Redis connections
        self.redis_client = redis.from_url(config.redis_url)
        self.redis_streams = redis.from_url(config.redis_url, decode_responses=False)

        # Processing state
        self.is_running = False
        self.processing_rules = {}
        self.active_windows = {}
        self.event_buffers = defaultdict(deque)
        self.metrics_cache = {}

        # Window configurations
        self.window_sizes = {
            '1m': timedelta(minutes=1),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '1d': timedelta(days=1)
        }

        # Initialize processing rules
        self._initialize_default_rules()

        # Initialize Kafka if available
        self.kafka_producer = None
        self.kafka_consumer = None
        self._setup_kafka()

    def _setup_logging(self) -> logging.Logger:
        """Setup stream processor logging"""
        logger = logging.getLogger("stream_processor")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _setup_kafka(self):
        """Setup Kafka producer and consumer"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            self.logger.info("Kafka producer initialized")
        except Exception as e:
            self.logger.warning(f"Kafka producer setup failed: {e}")

    def _initialize_default_rules(self):
        """Initialize default stream processing rules"""
        # Rule: Track page views in real-time
        self.add_rule(ProcessingRule(
            rule_id="page_view_counter",
            name="Real-time page view counting",
            condition=lambda event: event.event_type == "page_view",
            action=self._process_page_view
        ))

        # Rule: Track user engagement
        self.add_rule(ProcessingRule(
            rule_id="engagement_tracker",
            name="User engagement tracking",
            condition=lambda event: event.event_type in ["page_view", "dialogue_interaction", "combat_participation"],
            action=self._process_engagement_event
        ))

        # Rule: Detect anomalies
        self.add_rule(ProcessingRule(
            rule_id="anomaly_detector",
            name="Anomaly detection",
            condition=lambda event: True,  # Process all events
            action=self._detect_anomalies
        ))

        # Rule: Real-time metrics calculation
        self.add_rule(ProcessingRule(
            rule_id="metrics_calculator",
            name="Real-time metrics calculation",
            condition=lambda event: True,  # Process all events
            action=self._calculate_real_time_metrics
        ))

        # Rule: Alert on important events
        self.add_rule(ProcessingRule(
            rule_id="alert_generator",
            name="Important event alerts",
            condition=lambda event: event.event_type in ["user_signup", "purchase_completed", "error_occurred"],
            action=self._generate_alerts
        ))

    def add_rule(self, rule: ProcessingRule):
        """Add a processing rule"""
        self.processing_rules[rule.rule_id] = rule
        self.logger.info(f"Added processing rule: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove a processing rule"""
        if rule_id in self.processing_rules:
            del self.processing_rules[rule_id]
            self.logger.info(f"Removed processing rule: {rule_id}")

    async def process_events(self, events: List[AnalyticsEvent]):
        """Process a batch of events"""
        try:
            self.logger.debug(f"Processing {len(events)} events")

            for event in events:
                await self._process_single_event(event)

            # Update windows
            await self._update_time_windows()

            # Emit processed events to downstream systems
            await self._emit_processed_events(events)

        except Exception as e:
            self.logger.error(f"Error processing events: {e}")
            raise

    async def _process_single_event(self, event: AnalyticsEvent):
        """Process a single event through all applicable rules"""
        try:
            # Add event to buffers
            self.event_buffers['all'].append(event)
            self.event_buffers[event.event_type].append(event)

            # Apply processing rules
            for rule in self.processing_rules.values():
                if rule.enabled and rule.condition(event):
                    try:
                        await rule.action(event)
                    except Exception as e:
                        self.logger.error(f"Error in rule {rule.rule_id}: {e}")

            # Update real-time counters
            await self._update_real_time_counters(event)

        except Exception as e:
            self.logger.error(f"Error processing single event: {e}")

    async def _process_page_view(self, event: AnalyticsEvent):
        """Process page view events"""
        try:
            # Update page counters
            page_url = event.properties.get('page_url', 'unknown')
            timestamp_key = event.timestamp.strftime('%Y%m%d%H%M')

            # Update per-page counters
            page_key = f"analytics:pages:{page_url}:{timestamp_key}"
            await self.redis_client.incr(page_key)
            await self.redis_client.expire(page_key, 3600)  # 1 hour TTL

            # Update user page history
            user_pages_key = f"analytics:user:{event.user_id}:pages"
            await self.redis_client.lpush(user_pages_key, json.dumps({
                'page': page_url,
                'timestamp': event.timestamp.isoformat()
            }))
            await self.redis_client.ltrim(user_pages_key, 0, 100)  # Keep last 100 pages
            await self.redis_client.expire(user_pages_key, 86400)  # 24 hour TTL

            # Track landing pages
            referrer = event.properties.get('referrer')
            if not referrer:  # No referrer = landing page
                landing_key = f"analytics:landing_pages:{timestamp_key}"
                await self.redis_client.hincrby(landing_key, page_url, 1)
                await self.redis_client.expire(landing_key, 3600)

        except Exception as e:
            self.logger.error(f"Error processing page view: {e}")

    async def _process_engagement_event(self, event: AnalyticsEvent):
        """Process engagement-related events"""
        try:
            # Update user engagement score
            user_key = f"analytics:user:{event.user_id}:engagement"
            engagement_score = await self.redis_client.get(user_key)
            current_score = float(engagement_score) if engagement_score else 0

            # Calculate engagement delta based on event type
            engagement_delta = {
                'page_view': 1,
                'dialogue_interaction': 3,
                'combat_participation': 5,
                'social_interaction': 4,
                'character_creation': 10,
                'session_completed': 8
            }.get(event.event_type, 0.5)

            new_score = min(current_score + engagement_delta, 100)  # Cap at 100
            await self.redis_client.setex(user_key, 86400, str(new_score))

            # Track engagement events in time windows
            window_key = f"analytics:engagement:{event.timestamp.strftime('%Y%m%d%H%M')}"
            await self.redis_client.lpush(window_key, json.dumps({
                'user_id': event.user_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat()
            }))
            await self.redis_client.expire(window_key, 3600)

        except Exception as e:
            self.logger.error(f"Error processing engagement event: {e}")

    async def _detect_anomalies(self, event: AnalyticsEvent):
        """Detect anomalies in event patterns"""
        try:
            # Check for unusual activity patterns
            current_minute = event.timestamp.strftime('%Y%m%d%H%M')
            user_events_key = f"analytics:user:{event.user_id}:events:{current_minute}"
            event_count = await self.redis_client.incr(user_events_key)
            await self.redis_client.expire(user_events_key, 300)  # 5 minute TTL

            # Alert if user has too many events in a minute
            if event_count > 100:  # Threshold for anomaly
                await self._send_alert("high_activity", {
                    'user_id': event.user_id,
                    'event_count': event_count,
                    'time_window': '1 minute',
                    'event_type': event.event_type
                })

            # Check for system-wide anomalies
            total_events_key = f"analytics:system:events:{current_minute}"
            total_events = await self.redis_client.incr(total_events_key)
            await self.redis_client.expire(total_events_key, 300)

            # Alert if system event rate is unusual
            if total_events > 10000:  # System threshold
                await self._send_alert("system_high_load", {
                    'total_events': total_events,
                    'time_window': '1 minute'
                })

        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")

    async def _calculate_real_time_metrics(self, event: AnalyticsEvent):
        """Calculate real-time metrics"""
        try:
            current_minute = event.timestamp.strftime('%Y%m%d%H%M')
            metrics_key = f"analytics:metrics:{current_minute}"

            # Update various counters
            await self.redis_client.hincrby(metrics_key, 'total_events', 1)
            await self.redis_client.hincrby(metrics_key, f'event_type:{event.event_type}', 1)
            await self.redis_client.hincrby(metrics_key, 'active_users', 1)

            # Update user activity
            active_users_key = f"analytics:active_users:{current_minute}"
            await self.redis_client.sadd(active_users_key, event.user_id)
            await self.redis_client.expire(active_users_key, 300)

            # Calculate derived metrics
            active_users_count = await self.redis_client.scard(active_users_key)
            await self.redis_client.hset(metrics_key, 'unique_active_users', active_users_count)

            # Set TTL for metrics
            await self.redis_client.expire(metrics_key, 3600)

        except Exception as e:
            self.logger.error(f"Error calculating real-time metrics: {e}")

    async def _generate_alerts(self, event: AnalyticsEvent):
        """Generate alerts for important events"""
        try:
            alert_data = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'user_id': event.user_id,
                'timestamp': event.timestamp.isoformat(),
                'properties': event.properties
            }

            if event.event_type == 'user_signup':
                await self._send_alert("new_user_signup", alert_data)

            elif event.event_type == 'purchase_completed':
                await self._send_alert("purchase_completed", alert_data)

            elif event.event_type == 'error_occurred':
                await self._send_alert("error_occurred", alert_data)

        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")

    async def _update_real_time_counters(self, event: AnalyticsEvent):
        """Update real-time counters for various metrics"""
        try:
            # Global counters
            await self.redis_client.incr(f"analytics:counters:total_events")
            await self.redis_client.incr(f"analytics:counters:event_type:{event.event_type}")

            # Time-based counters
            time_keys = [
                event.timestamp.strftime('%Y%m%d%H%M'),  # minute
                event.timestamp.strftime('%Y%m%d%H'),     # hour
                event.timestamp.strftime('%Y%m%d'),       # day
            ]

            for time_key in time_keys:
                await self.redis_client.incr(f"analytics:counters:events:{time_key}")
                await self.redis_client.expire(f"analytics:counters:events:{time_key}", 86400 * 7)  # 7 days TTL

            # User-specific counters
            await self.redis_client.incr(f"analytics:user:{event.user_id}:total_events")
            await self.redis_client.expire(f"analytics:user:{event.user_id}:total_events", 86400 * 30)  # 30 days TTL

        except Exception as e:
            self.logger.error(f"Error updating real-time counters: {e}")

    async def _update_time_windows(self):
        """Update time windows for aggregation"""
        try:
            current_time = datetime.utcnow()

            for window_name, window_size in self.window_sizes.items():
                window_id = self._get_window_id(current_time, window_size, window_name)

                if window_id not in self.active_windows:
                    # Create new window
                    window_start = self._get_window_start(current_time, window_size)
                    window_end = window_start + window_size

                    window = StreamWindow(
                        window_id=window_id,
                        start_time=window_start,
                        end_time=window_end,
                        events=[],
                        aggregates={}
                    )

                    self.active_windows[window_id] = window
                    self.logger.debug(f"Created new time window: {window_id}")

                # Clean up old windows
                await self._cleanup_old_windows(current_time)

        except Exception as e:
            self.logger.error(f"Error updating time windows: {e}")

    async def _cleanup_old_windows(self, current_time: datetime):
        """Clean up expired time windows"""
        try:
            expired_windows = []

            for window_id, window in self.active_windows.items():
                if current_time > window.end_time:
                    expired_windows.append(window_id)

                    # Finalize window aggregates
                    await self._finalize_window(window)

            for window_id in expired_windows:
                del self.active_windows[window_id]

            if expired_windows:
                self.logger.debug(f"Cleaned up {len(expired_windows)} expired windows")

        except Exception as e:
            self.logger.error(f"Error cleaning up windows: {e}")

    async def _finalize_window(self, window: StreamWindow):
        """Finalize a time window with aggregates"""
        try:
            # Calculate aggregates
            aggregates = {
                'event_count': len(window.events),
                'unique_users': len(set(event.user_id for event in window.events)),
                'event_types': defaultdict(int),
                'avg_events_per_user': 0
            }

            # Count event types
            for event in window.events:
                aggregates['event_types'][event.event_type] += 1

            # Calculate average events per user
            if aggregates['unique_users'] > 0:
                aggregates['avg_events_per_user'] = aggregates['event_count'] / aggregates['unique_users']

            # Store window data
            window_data = {
                'window_id': window.window_id,
                'start_time': window.start_time.isoformat(),
                'end_time': window.end_time.isoformat(),
                'event_count': aggregates['event_count'],
                'unique_users': aggregates['unique_users'],
                'event_types': dict(aggregates['event_types']),
                'avg_events_per_user': aggregates['avg_events_per_user'],
                'created_at': datetime.utcnow().isoformat()
            }

            # Store in Redis
            window_key = f"analytics:windows:{window.window_id}"
            await self.redis_client.setex(window_key, 86400 * 7, json.dumps(window_data))  # 7 days TTL

            # Store in time series
            ts_key = f"analytics:timeseries:{window.window_id.split(':')[0]}"
            await self.redis_client.lpush(ts_key, json.dumps(window_data))
            await self.redis_client.ltrim(ts_key, 0, 1000)  # Keep last 1000 windows
            await self.redis_client.expire(ts_key, 86400 * 30)  # 30 days TTL

            self.logger.debug(f"Finalized window: {window.window_id}")

        except Exception as e:
            self.logger.error(f"Error finalizing window: {e}")

    async def _emit_processed_events(self, events: List[AnalyticsEvent]):
        """Emit processed events to downstream systems"""
        try:
            # Send to Kafka if available
            if self.kafka_producer:
                for event in events:
                    try:
                        self.kafka_producer.send(
                            'analytics_processed',
                            value=asdict(event),
                            key=event.user_id.encode('utf-8')
                        )
                    except Exception as e:
                        self.logger.error(f"Error sending to Kafka: {e}")

            # Store in Redis streams
            for event in events:
                try:
                    await self.redis_streams.xadd(
                        'analytics_events',
                        {
                            'event_id': event.event_id,
                            'event_type': event.event_type,
                            'user_id': event.user_id,
                            'session_id': event.session_id,
                            'timestamp': event.timestamp.isoformat(),
                            'properties': json.dumps(event.properties),
                            'source': event.source,
                            'version': event.version
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error adding to Redis stream: {e}")

        except Exception as e:
            self.logger.error(f"Error emitting processed events: {e}")

    async def _send_alert(self, alert_type: str, data: Dict[str, Any]):
        """Send alert to monitoring system"""
        try:
            alert = {
                'alert_type': alert_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data,
                'severity': self._get_alert_severity(alert_type)
            }

            # Store alert in Redis
            alert_key = f"analytics:alerts:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            await self.redis_client.setex(alert_key, 86400, json.dumps(alert))  # 24 hours TTL

            # Send to alert system (webhook, Slack, etc.)
            if alert['severity'] in ['high', 'critical']:
                await self._send_webhook_alert(alert)

            self.logger.warning(f"Alert generated: {alert_type}")

        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")

    async def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send alert via webhook"""
        try:
            # Mock webhook implementation
            webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=alert) as response:
                    if response.status == 200:
                        self.logger.info("Alert webhook sent successfully")
                    else:
                        self.logger.warning(f"Webhook failed with status {response.status}")

        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")

    def _get_alert_severity(self, alert_type: str) -> str:
        """Get alert severity level"""
        severity_map = {
            'new_user_signup': 'info',
            'purchase_completed': 'info',
            'error_occurred': 'medium',
            'high_activity': 'high',
            'system_high_load': 'critical'
        }
        return severity_map.get(alert_type, 'info')

    def _get_window_id(self, current_time: datetime, window_size: timedelta, window_name: str) -> str:
        """Generate window ID"""
        window_start = self._get_window_start(current_time, window_size)
        return f"{window_name}:{window_start.strftime('%Y%m%d%H%M')}"

    def _get_window_start(self, current_time: datetime, window_size: timedelta) -> datetime:
        """Get window start time"""
        if window_size.total_seconds() <= 300:  # 5 minutes or less
            return current_time.replace(second=0, microsecond=0)
        elif window_size.total_seconds() <= 3600:  # 1 hour or less
            return current_time.replace(minute=0, second=0, microsecond=0)
        else:  # More than 1 hour
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    async def get_real_time_metrics(self, time_window: timedelta = timedelta(minutes=5)) -> Dict[str, Any]:
        """Get current real-time metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_window

            # Get metrics from Redis
            metrics = {
                'time_window': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'duration_minutes': int(time_window.total_seconds() / 60)
                },
                'events': {
                    'total': 0,
                    'per_minute': 0,
                    'by_type': {}
                },
                'users': {
                    'active': 0,
                    'new': 0,
                    'returning': 0
                },
                'pages': {
                    'top_pages': [],
                    'total_views': 0
                },
                'system': {
                    'processing_rate': 0,
                    'error_rate': 0
                }
            }

            # Collect metrics for each minute in the window
            current_time = start_time
            total_events = 0
            active_users = set()
            page_counts = defaultdict(int)

            while current_time <= end_time:
                minute_key = current_time.strftime('%Y%m%d%H%M')
                metrics_key = f"analytics:metrics:{minute_key}"

                # Get minute metrics
                minute_metrics = await self.redis_client.hgetall(metrics_key)
                if minute_metrics:
                    events_in_minute = int(minute_metrics.get(b'total_events', 0))
                    total_events += events_in_minute

                    # Get active users for this minute
                    active_users_key = f"analytics:active_users:{minute_key}"
                    minute_users = await self.redis_client.smembers(active_users_key)
                    active_users.update(minute_users)

                current_time += timedelta(minutes=1)

            # Calculate final metrics
            metrics['events']['total'] = total_events
            metrics['events']['per_minute'] = total_events / max(1, time_window.total_seconds() / 60)
            metrics['users']['active'] = len(active_users)

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {e}")
            return {}

    async def start(self):
        """Start the stream processor"""
        self.logger.info("Starting Stream Processor...")
        self.is_running = True

        # Start background tasks
        tasks = [
            self._process_redis_streams(),
            self._maintenance_loop()
        ]

        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop the stream processor"""
        self.logger.info("Stopping Stream Processor...")
        self.is_running = False

        # Close Kafka producer
        if self.kafka_producer:
            self.kafka_producer.close()

        self.logger.info("Stream Processor stopped")

    async def _process_redis_streams(self):
        """Process events from Redis streams"""
        self.logger.info("Starting Redis stream processing...")

        while self.is_running:
            try:
                # Read from analytics events stream
                streams_data = await self.redis_streams.xread(
                    {'analytics_events': '0-0'},
                    count=100,
                    block=1000
                )

                for stream, messages in streams_data:
                    for message_id, fields in messages:
                        try:
                            # Reconstruct event from stream data
                            event = AnalyticsEvent(
                                event_id=fields['event_id'].decode('utf-8'),
                                event_type=fields['event_type'].decode('utf-8'),
                                user_id=fields['user_id'].decode('utf-8'),
                                session_id=fields['session_id'].decode('utf-8'),
                                timestamp=datetime.fromisoformat(fields['timestamp'].decode('utf-8')),
                                properties=json.loads(fields['properties'].decode('utf-8')),
                                source=fields['source'].decode('utf-8'),
                                version=fields['version'].decode('utf-8')
                            )

                            await self._process_single_event(event)

                        except Exception as e:
                            self.logger.error(f"Error processing stream message: {e}")

            except Exception as e:
                self.logger.error(f"Error in Redis stream processing: {e}")
                await asyncio.sleep(5)

    async def _maintenance_loop(self):
        """Maintenance tasks"""
        self.logger.info("Starting maintenance loop...")

        while self.is_running:
            try:
                # Update time windows
                await self._update_time_windows()

                # Clean up old data
                await self._cleanup_old_data()

                # Update metrics cache
                await self._update_metrics_cache()

                await asyncio.sleep(60)  # Run every minute

            except Exception as e:
                self.logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_data(self):
        """Clean up old stream data"""
        try:
            # Trim Redis streams to prevent unlimited growth
            await self.redis_streams.xtrim('analytics_events', maxlen=100000)

            # Clean up old metrics keys
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            cutoff_key = cutoff_time.strftime('%Y%m%d%H%M')

            # This is a simplified cleanup - in practice you'd want more sophisticated cleanup
            pattern = "analytics:counters:events:*"
            for key in self.redis_client.scan_iter(match=pattern):
                key_str = key.decode('utf-8')
                if key_str.split(':')[-1] < cutoff_key:
                    self.redis_client.delete(key)

        except Exception as e:
            self.logger.error(f"Error in data cleanup: {e}")

    async def _update_metrics_cache(self):
        """Update metrics cache with latest calculations"""
        try:
            # Get real-time metrics
            metrics = await self.get_real_time_metrics()

            # Cache in Redis
            cache_key = "analytics:metrics_cache:current"
            await self.redis_client.setex(cache_key, 300, json.dumps(metrics))  # 5 minute TTL

        except Exception as e:
            self.logger.error(f"Error updating metrics cache: {e}")