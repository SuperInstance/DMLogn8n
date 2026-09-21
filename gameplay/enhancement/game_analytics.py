#!/usr/bin/env python3
"""
Comprehensive Analytics and Performance Monitoring System for DMLogn8n
Provides deep insights into gameplay patterns and system performance
"""

import json
import math
import random
import time
import threading
import queue
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class EventType(Enum):
    PLAYER_ACTION = "player_action"
    COMBAT = "combat"
    SOCIAL = "social"
    ECONOMY = "economy"
    QUEST = "quest"
    SYSTEM = "system"
    ERROR = "error"
    PERFORMANCE = "performance"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AggregationType(Enum):
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"

@dataclass
class MetricDefinition:
    """Definition of a metric to track"""
    name: str
    metric_type: MetricType
    description: str
    tags: Dict[str, str] = field(default_factory=dict)
    aggregation: List[AggregationType] = field(default_factory=list)
    retention_period: int = 86400 * 30  # 30 days
    alert_thresholds: Dict[str, float] = field(default_factory=dict)

@dataclass
class Event:
    """Gameplay event to track"""
    event_type: EventType
    player_id: str
    action: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Performance measurement"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    sample_rate: float = 1.0

@dataclass
class Alert:
    """Alert definition"""
    name: str
    condition: str  # metric expression
    severity: AlertSeverity
    description: str
    enabled: bool = True
    cooldown: int = 300  # seconds
    last_triggered: float = 0
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class Dashboard:
    """Analytics dashboard configuration"""
    id: str
    name: str
    description: str
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    refresh_interval: int = 60  # seconds
    time_range: str = "24h"  # 1h, 24h, 7d, 30d

class GameAnalytics:
    """Comprehensive game analytics system"""

    def __init__(self):
        self.metrics: Dict[str, MetricDefinition] = {}
        self.metric_values: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.events: deque = deque(maxlen=100000)  # Last 100k events
        self.performance_metrics: deque = deque(maxlen=50000)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.player_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.real_time_metrics: Dict[str, float] = defaultdict(float)
        self.aggregated_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.alerts: Dict[str, Alert] = {}
        self.dashboards: Dict[str, Dashboard] = {}

        # Processing queues
        self.event_queue = queue.Queue()
        self.metric_queue = queue.Queue()
        self.processing_thread = None
        self.running = False

        # Analytics parameters
        self.session_timeout = 1800  # 30 minutes
        self.batch_size = 100
        self.flush_interval = 5  # seconds
        self.retention_check_interval = 3600  # 1 hour
        self.performance_sampling_rate = 0.1  # 10% sampling

        self._initialize_default_metrics()
        self._initialize_default_alerts()
        self._initialize_default_dashboards()

    def _initialize_default_metrics(self):
        """Initialize default metrics to track"""
        default_metrics = [
            MetricDefinition(
                name="active_players",
                metric_type=MetricType.GAUGE,
                description="Number of currently active players",
                tags={"type": "engagement"},
                aggregation=[AggregationType.SUM, AggregationType.AVERAGE],
                alert_thresholds={"min": 0}
            ),
            MetricDefinition(
                name="combat_duration",
                metric_type=MetricType.HISTOGRAM,
                description="Duration of combat encounters",
                tags={"type": "combat"},
                aggregation=[AggregationType.AVERAGE, AggregationType.PERCENTILE],
                alert_thresholds={"max": 300}  # 5 minutes max
            ),
            MetricDefinition(
                name="quest_completion_rate",
                metric_type=MetricType.RATE,
                description="Rate of quest completions per hour",
                tags={"type": "quest"},
                aggregation=[AggregationType.SUM, AggregationType.AVERAGE],
                alert_thresholds={"min": 0.1}
            ),
            MetricDefinition(
                name="economy_turnover",
                metric_type=MetricType.COUNTER,
                description="Total economic transactions",
                tags={"type": "economy"},
                aggregation=[AggregationType.SUM, AggregationType.RATE]
            ),
            MetricDefinition(
                name="error_rate",
                metric_type=MetricType.RATE,
                description="Rate of errors per minute",
                tags={"type": "system"},
                aggregation=[AggregationType.SUM, AggregationType.AVERAGE],
                alert_thresholds={"max": 0.05}  # 5% max error rate
            ),
            MetricDefinition(
                name="response_time",
                metric_type=MetricType.HISTOGRAM,
                description="System response times",
                tags={"type": "performance"},
                aggregation=[AggregationType.AVERAGE, AggregationType.PERCENTILE],
                alert_thresholds={"p95": 1000}  # 95th percentile under 1 second
            ),
            MetricDefinition(
                name="social_interactions",
                metric_type=MetricType.COUNTER,
                description="Number of social interactions",
                tags={"type": "social"},
                aggregation=[AggregationType.SUM, AggregationType.RATE]
            )
        ]

        for metric in default_metrics:
            self.metrics[metric.name] = metric

    def _initialize_default_alerts(self):
        """Initialize default alerts"""
        default_alerts = [
            Alert(
                name="high_error_rate",
                condition="error_rate > 0.05",
                severity=AlertSeverity.CRITICAL,
                description="Error rate exceeds 5%",
                notification_channels=["email", "slack"]
            ),
            Alert(
                name="low_active_players",
                condition="active_players < 10",
                severity=AlertSeverity.WARNING,
                description="Active player count is unusually low",
                notification_channels=["email"]
            ),
            Alert(
                name="slow_response_times",
                condition="response_time_p95 > 2000",
                severity=AlertSeverity.ERROR,
                description="95th percentile response time exceeds 2 seconds",
                notification_channels=["slack"]
            ),
            Alert(
                name="quest_completion_issues",
                condition="quest_completion_rate < 0.05",
                severity=AlertSeverity.WARNING,
                description="Quest completion rate is very low",
                notification_channels=["email"]
            )
        ]

        for alert in default_alerts:
            self.alerts[alert.name] = alert

    def _initialize_default_dashboards(self):
        """Initialize default dashboards"""
        default_dashboards = [
            Dashboard(
                id="overview",
                name="System Overview",
                description="High-level system metrics",
                widgets=[
                    {"type": "gauge", "metric": "active_players", "title": "Active Players"},
                    {"type": "line", "metric": "quest_completion_rate", "title": "Quest Completion Rate"},
                    {"type": "histogram", "metric": "combat_duration", "title": "Combat Duration"},
                    {"type": "counter", "metric": "error_rate", "title": "Error Rate"}
                ]
            ),
            Dashboard(
                id="performance",
                name="Performance Metrics",
                description="System performance monitoring",
                widgets=[
                    {"type": "line", "metric": "response_time", "title": "Response Times"},
                    {"type": "gauge", "metric": "cpu_usage", "title": "CPU Usage"},
                    {"type": "gauge", "metric": "memory_usage", "title": "Memory Usage"},
                    {"type": "line", "metric": "throughput", "title": "System Throughput"}
                ]
            ),
            Dashboard(
                id="engagement",
                name="Player Engagement",
                description="Player activity and engagement metrics",
                widgets=[
                    {"type": "line", "metric": "daily_active_users", "title": "Daily Active Users"},
                    {"type": "line", "metric": "session_duration", "title": "Average Session Duration"},
                    {"type": "counter", "metric": "social_interactions", "title": "Social Interactions"},
                    {"type": "heatmap", "metric": "activity_by_hour", "title": "Activity by Hour"}
                ]
            )
        ]

        for dashboard in default_dashboards:
            self.dashboards[dashboard.id] = dashboard

    def start_analytics(self):
        """Start the analytics processing system"""
        if self.running:
            return

        self.running = True
        self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processing_thread.start()

        # Start periodic tasks
        threading.Thread(target=self._periodic_tasks, daemon=True).start()

        print("Game analytics system started")

    def stop_analytics(self):
        """Stop the analytics processing system"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        print("Game analytics system stopped")

    def track_event(self, event: Event):
        """Track a gameplay event"""
        try:
            self.event_queue.put(event)
        except queue.Full:
            print("Event queue full, dropping event")

    def track_metric(self, metric: PerformanceMetric):
        """Track a performance metric"""
        try:
            self.metric_queue.put(metric)
        except queue.Full:
            print("Metric queue full, dropping metric")

    def track_player_action(self, player_id: str, action: str, data: Dict[str, Any] = None, session_id: str = None):
        """Convenience method to track player actions"""
        event = Event(
            event_type=EventType.PLAYER_ACTION,
            player_id=player_id,
            action=action,
            timestamp=time.time(),
            data=data or {},
            session_id=session_id
        )
        self.track_event(event)

    def track_combat(self, player_id: str, duration: float, success: bool, data: Dict[str, Any] = None):
        """Track combat events"""
        event = Event(
            event_type=EventType.COMBAT,
            player_id=player_id,
            action="combat_encounter",
            timestamp=time.time(),
            data=data or {},
            duration=duration,
            success=success
        )
        self.track_event(event)

    def track_error(self, error_type: str, message: str, player_id: str = None, data: Dict[str, Any] = None):
        """Track error events"""
        event = Event(
            event_type=EventType.ERROR,
            player_id=player_id or "system",
            action=error_type,
            timestamp=time.time(),
            data=data or {},
            success=False,
            error_message=message
        )
        self.track_event(event)

    def start_session(self, player_id: str, session_id: str, data: Dict[str, Any] = None):
        """Start a player session"""
        self.active_sessions[session_id] = {
            "player_id": player_id,
            "start_time": time.time(),
            "last_activity": time.time(),
            "events_count": 0,
            "data": data or {}
        }

        # Update player profile
        self.player_profiles[player_id]["sessions_started"] = self.player_profiles[player_id].get("sessions_started", 0) + 1

        # Track real-time metric
        self.real_time_metrics["active_sessions"] += 1

    def end_session(self, session_id: str, data: Dict[str, Any] = None):
        """End a player session"""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        duration = time.time() - session["start_time"]

        # Update player profile
        player_id = session["player_id"]
        self.player_profiles[player_id]["total_playtime"] = self.player_profiles[player_id].get("total_playtime", 0) + duration
        self.player_profiles[player_id]["average_session_length"] = (
            self.player_profiles[player_id].get("total_playtime", 0) /
            self.player_profiles[player_id].get("sessions_started", 1)
        )

        # Remove from active sessions
        del self.active_sessions[session_id]
        self.real_time_metrics["active_sessions"] = max(0, self.real_time_metrics["active_sessions"] - 1)

        # Track session end event
        event = Event(
            event_type=EventType.SYSTEM,
            player_id=player_id,
            action="session_end",
            timestamp=time.time(),
            data={
                "duration": duration,
                "events_count": session["events_count"],
                **(data or {})
            }
        )
        self.track_event(event)

    def _process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Process batch of events
                batch = []
                for _ in range(self.batch_size):
                    try:
                        event = self.event_queue.get_nowait()
                        batch.append(event)
                    except queue.Empty:
                        break

                if batch:
                    self._process_event_batch(batch)

                # Process metrics
                metric_batch = []
                for _ in range(self.batch_size):
                    try:
                        metric = self.metric_queue.get_nowait()
                        metric_batch.append(metric)
                    except queue.Empty:
                        break

                if metric_batch:
                    self._process_metric_batch(metric_batch)

                time.sleep(self.flush_interval)

            except Exception as e:
                print(f"Error processing events: {e}")
                time.sleep(1)

    def _process_event_batch(self, events: List[Event]):
        """Process a batch of events"""
        for event in events:
            # Add to events storage
            self.events.append(event)

            # Update real-time metrics
            self._update_real_time_metrics(event)

            # Update player profiles
            self._update_player_profile(event)

            # Update session data
            self._update_session_data(event)

            # Check alerts
            self._check_alerts(event)

    def _process_metric_batch(self, metrics: List[PerformanceMetric]):
        """Process a batch of performance metrics"""
        for metric in metrics:
            # Add to metrics storage
            self.performance_metrics.append(metric)

            # Update metric values
            if metric.name in self.metrics:
                self.metric_values[metric.name].append(metric)

            # Update real-time metrics
            self.real_time_metrics[metric.name] = metric.value

    def _update_real_time_metrics(self, event: Event):
        """Update real-time metrics based on event"""
        if event.event_type == EventType.PLAYER_ACTION:
            self.real_time_metrics["player_actions_per_minute"] += 1

        elif event.event_type == EventType.COMBAT:
            if "combat_duration" in self.real_time_metrics:
                self.real_time_metrics["combat_duration"] = (
                    self.real_time_metrics["combat_duration"] * 0.9 + event.duration * 0.1
                )
            else:
                self.real_time_metrics["combat_duration"] = event.duration

        elif event.event_type == EventType.ERROR:
            self.real_time_metrics["errors_per_minute"] += 1

        # Update active players
        if event.event_type in [EventType.PLAYER_ACTION, EventType.COMBAT, EventType.SOCIAL, EventType.QUEST]:
            self.real_time_metrics["active_players"] = len(set(
                event.player_id for event in list(self.events)[-1000:]  # Last 1000 events
            ))

    def _update_player_profile(self, event: Event):
        """Update player profile based on event"""
        player_id = event.player_id
        profile = self.player_profiles[player_id]

        if event.event_type == EventType.PLAYER_ACTION:
            profile["actions_performed"] = profile.get("actions_performed", 0) + 1
            profile["last_activity"] = event.timestamp

        elif event.event_type == EventType.COMBAT:
            profile["combats_fought"] = profile.get("combats_fought", 0) + 1
            if event.success:
                profile["combats_won"] = profile.get("combats_won", 0) + 1

        elif event.event_type == EventType.QUEST:
            profile["quests_attempted"] = profile.get("quests_attempted", 0) + 1
            if event.success:
                profile["quests_completed"] = profile.get("quests_completed", 0) + 1

        elif event.event_type == EventType.SOCIAL:
            profile["social_interactions"] = profile.get("social_interactions", 0) + 1

    def _update_session_data(self, event: Event):
        """Update session data based on event"""
        if event.session_id and event.session_id in self.active_sessions:
            session = self.active_sessions[event.session_id]
            session["last_activity"] = event.timestamp
            session["events_count"] += 1

    def _check_alerts(self, event: Event):
        """Check if any alerts should be triggered"""
        current_time = time.time()

        for alert_name, alert in self.alerts.items():
            if not alert.enabled:
                continue

            # Check cooldown
            if current_time - alert.last_triggered < alert.cooldown:
                continue

            # Evaluate alert condition
            if self._evaluate_alert_condition(alert.condition):
                alert.last_triggered = current_time
                self._trigger_alert(alert, event)

    def _evaluate_alert_condition(self, condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation (in production, use a proper expression parser)
            if "active_players" in condition:
                threshold = float(condition.split("<")[1].strip())
                return self.real_time_metrics["active_players"] < threshold
            elif "error_rate" in condition:
                threshold = float(condition.split(">")[1].strip())
                return self.real_time_metrics.get("errors_per_minute", 0) / 60 > threshold
            # Add more condition evaluations as needed
        except Exception as e:
            print(f"Error evaluating alert condition: {e}")

        return False

    def _trigger_alert(self, alert: Alert, event: Event = None):
        """Trigger an alert"""
        print(f"ALERT: {alert.name} - {alert.description}")

        # In production, send to notification channels
        for channel in alert.notification_channels:
            print(f"Sending alert to {channel}: {alert.name}")

    def _periodic_tasks(self):
        """Run periodic maintenance tasks"""
        while self.running:
            try:
                # Clean up expired sessions
                self._cleanup_expired_sessions()

                # Aggregate metrics
                self._aggregate_metrics()

                # Check retention policies
                self._check_retention_policies()

                time.sleep(self.retention_check_interval)

            except Exception as e:
                print(f"Error in periodic tasks: {e}")
                time.sleep(60)

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if current_time - session["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.end_session(session_id, {"reason": "timeout"})

    def _aggregate_metrics(self):
        """Aggregate metrics for storage"""
        current_time = time.time()
        time_window = 300  # 5 minutes

        for metric_name, values in self.metric_values.items():
            if not values:
                continue

            # Filter values within time window
            recent_values = [
                v for v in values
                if current_time - v.timestamp <= time_window
            ]

            if not recent_values:
                continue

            metric_def = self.metrics.get(metric_name)
            if not metric_def:
                continue

            # Calculate aggregations
            aggregated = {}
            numeric_values = [v.value for v in recent_values]

            for agg_type in metric_def.aggregation:
                if agg_type == AggregationType.SUM:
                    aggregated["sum"] = sum(numeric_values)
                elif agg_type == AggregationType.AVERAGE:
                    aggregated["average"] = statistics.mean(numeric_values)
                elif agg_type == AggregationType.MIN:
                    aggregated["min"] = min(numeric_values)
                elif agg_type == AggregationType.MAX:
                    aggregated["max"] = max(numeric_values)
                elif agg_type == AggregationType.COUNT:
                    aggregated["count"] = len(numeric_values)
                elif agg_type == AggregationType.PERCENTILE:
                    aggregated["p50"] = statistics.median(numeric_values)
                    aggregated["p95"] = np.percentile(numeric_values, 95) if numeric_values else 0
                    aggregated["p99"] = np.percentile(numeric_values, 99) if numeric_values else 0

            self.aggregated_data[metric_name][int(current_time)] = aggregated

    def _check_retention_policies(self):
        """Check and enforce retention policies"""
        current_time = time.time()

        # Clean up old metric values
        for metric_name, metric_def in self.metrics.items():
            retention_period = metric_def.retention_period
            cutoff_time = current_time - retention_period

            # Filter old values
            if metric_name in self.metric_values:
                old_size = len(self.metric_values[metric_name])
                filtered = deque(
                    (v for v in self.metric_values[metric_name] if v.timestamp >= cutoff_time),
                    maxlen=10000
                )
                self.metric_values[metric_name] = filtered
                print(f"Cleaned {old_size - len(filtered)} old values for {metric_name}")

        # Clean up old events
        event_cutoff = current_time - (86400 * 7)  # Keep 7 days of events
        old_size = len(self.events)
        filtered_events = deque(
            (e for e in self.events if e.timestamp >= event_cutoff),
            maxlen=100000
        )
        self.events = filtered_events
        print(f"Cleaned {old_size - len(filtered_events)} old events")

    def get_dashboard_data(self, dashboard_id: str, time_range: str = "24h") -> Dict[str, Any]:
        """Get data for a dashboard"""
        if dashboard_id not in self.dashboards:
            return {"error": "Dashboard not found"}

        dashboard = self.dashboards[dashboard_id]
        current_time = time.time()

        # Calculate time range
        time_ranges = {
            "1h": 3600,
            "24h": 86400,
            "7d": 604800,
            "30d": 2592000
        }
        range_seconds = time_ranges.get(time_range, 86400)
        start_time = current_time - range_seconds

        dashboard_data = {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "description": dashboard.description,
            "timestamp": current_time,
            "time_range": time_range,
            "widgets": []
        }

        for widget in dashboard.widgets:
            widget_data = self._get_widget_data(widget, start_time, current_time)
            dashboard_data["widgets"].append(widget_data)

        return dashboard_data

    def _get_widget_data(self, widget: Dict[str, Any], start_time: float, end_time: float) -> Dict[str, Any]:
        """Get data for a specific widget"""
        metric_name = widget.get("metric")
        widget_type = widget.get("type")
        title = widget.get("title", metric_name)

        if not metric_name:
            return {"type": widget_type, "title": title, "error": "No metric specified"}

        # Get metric data
        metric_data = []
        if metric_name in self.metric_values:
            for metric in self.metric_values[metric_name]:
                if start_time <= metric.timestamp <= end_time:
                    metric_data.append({
                        "timestamp": metric.timestamp,
                        "value": metric.value,
                        "tags": metric.tags
                    })

        # Process based on widget type
        if widget_type == "gauge":
            current_value = metric_data[-1]["value"] if metric_data else 0
            return {
                "type": "gauge",
                "title": title,
                "current_value": current_value,
                "data_points": len(metric_data)
            }

        elif widget_type == "line":
            return {
                "type": "line",
                "title": title,
                "data": metric_data,
                "min_value": min(d["value"] for d in metric_data) if metric_data else 0,
                "max_value": max(d["value"] for d in metric_data) if metric_data else 0
            }

        elif widget_type == "histogram":
            values = [d["value"] for d in metric_data]
            return {
                "type": "histogram",
                "title": title,
                "values": values,
                "bins": 20,
                "statistics": {
                    "mean": statistics.mean(values) if values else 0,
                    "median": statistics.median(values) if values else 0,
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0
                }
            }

        elif widget_type == "counter":
            total = sum(d["value"] for d in metric_data)
            return {
                "type": "counter",
                "title": title,
                "total": total,
                "rate": total / ((end_time - start_time) / 3600) if end_time > start_time else 0  # per hour
            }

        return {
            "type": widget_type,
            "title": title,
            "data": metric_data
        }

    def get_player_analytics(self, player_id: str) -> Dict[str, Any]:
        """Get analytics for a specific player"""
        profile = self.player_profiles.get(player_id, {})

        # Get player events
        player_events = [e for e in self.events if e.player_id == player_id]

        # Calculate metrics
        total_sessions = profile.get("sessions_started", 0)
        total_playtime = profile.get("total_playtime", 0)
        actions_performed = profile.get("actions_performed", 0)
        combats_fought = profile.get("combats_fought", 0)
        combats_won = profile.get("combats_won", 0)
        quests_completed = profile.get("quests_completed", 0)
        social_interactions = profile.get("social_interactions", 0)

        # Calculate rates
        avg_session_length = profile.get("average_session_length", 0)
        combat_win_rate = combats_won / combats_fought if combats_fought > 0 else 0
        actions_per_hour = actions_performed / (total_playtime / 3600) if total_playtime > 0 else 0

        # Recent activity
        recent_events = [e for e in player_events if time.time() - e.timestamp <= 86400]  # Last 24 hours
        recent_activity = len(recent_events)

        return {
            "player_id": player_id,
            "total_sessions": total_sessions,
            "total_playtime_hours": total_playtime / 3600,
            "average_session_length_minutes": avg_session_length / 60,
            "actions_performed": actions_performed,
            "actions_per_hour": actions_per_hour,
            "combats_fought": combats_fought,
            "combats_won": combats_won,
            "combat_win_rate": combat_win_rate,
            "quests_completed": quests_completed,
            "social_interactions": social_interactions,
            "recent_activity_24h": recent_activity,
            "last_activity": profile.get("last_activity"),
            "first_seen": min(e.timestamp for e in player_events) if player_events else None
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        current_time = time.time()

        # Calculate error rate
        recent_errors = len([e for e in self.events if e.event_type == EventType.ERROR and current_time - e.timestamp <= 300])
        total_recent_events = len([e for e in self.events if current_time - e.timestamp <= 300])
        error_rate = recent_errors / total_recent_events if total_recent_events > 0 else 0

        # Calculate response times
        recent_metrics = [m for m in self.performance_metrics if current_time - m.timestamp <= 300]
        response_times = [m.value for m in recent_metrics if m.name == "response_time"]
        avg_response_time = statistics.mean(response_times) if response_times else 0

        # Calculate queue sizes
        event_queue_size = self.event_queue.qsize()
        metric_queue_size = self.metric_queue.qsize()

        # Memory usage (simplified)
        total_events = len(self.events)
        total_metrics = len(self.performance_metrics)
        active_sessions = len(self.active_sessions)

        return {
            "timestamp": current_time,
            "status": "healthy" if error_rate < 0.01 and avg_response_time < 1000 else "degraded",
            "error_rate": error_rate,
            "average_response_time_ms": avg_response_time,
            "event_queue_size": event_queue_size,
            "metric_queue_size": metric_queue_size,
            "active_sessions": active_sessions,
            "total_events_stored": total_events,
            "total_metrics_stored": total_metrics,
            "processing_thread_alive": self.processing_thread.is_alive() if self.processing_thread else False,
            "alerts_triggered": len([a for a in self.alerts.values() if a.last_triggered > current_time - 3600])
        }

    def export_analytics_data(self, filename: str, time_range: str = "24h") -> str:
        """Export analytics data to file"""
        current_time = time.time()
        time_ranges = {"1h": 3600, "24h": 86400, "7d": 604800, "30d": 2592000}
        range_seconds = time_ranges.get(time_range, 86400)
        start_time = current_time - range_seconds

        # Filter data
        filtered_events = [
            {
                "event_type": e.event_type.value,
                "player_id": e.player_id,
                "action": e.action,
                "timestamp": e.timestamp,
                "data": e.data,
                "success": e.success,
                "duration": e.duration
            }
            for e in self.events if start_time <= e.timestamp <= current_time
        ]

        filtered_metrics = [
            {
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp,
                "tags": m.tags
            }
            for m in self.performance_metrics if start_time <= m.timestamp <= current_time
        ]

        export_data = {
            "export_timestamp": current_time,
            "time_range": time_range,
            "start_time": start_time,
            "end_time": current_time,
            "events": filtered_events,
            "metrics": filtered_metrics,
            "real_time_metrics": dict(self.real_time_metrics),
            "active_sessions": len(self.active_sessions),
            "system_health": self.get_system_health()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return filename

# Import numpy for percentile calculations
try:
    import numpy as np
except ImportError:
    # Fallback if numpy not available
    class np:
        @staticmethod
        def percentile(data, p):
            sorted_data = sorted(data)
            index = (p / 100) * (len(sorted_data) - 1)
            if index.is_integer():
                return sorted_data[int(index)]
            else:
                lower = sorted_data[int(index)]
                upper = sorted_data[int(index) + 1]
                return lower + (upper - lower) * (index - int(index))

# Export main classes
__all__ = [
    'GameAnalytics',
    'Event',
    'PerformanceMetric',
    'MetricDefinition',
    'Alert',
    'Dashboard'
]