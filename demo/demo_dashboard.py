#!/usr/bin/env python3
"""
Demo Dashboard - Live Monitoring and Analytics
Provides real-time visualization of all DMLogn8n demo activities
"""

import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
from collections import deque, defaultdict

logger = logging.getLogger('DMLogn8n-DemoDashboard')

class MetricType(Enum):
    """Types of metrics tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class SystemStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class Alert:
    """System alert"""
    id: str
    level: str  # info, warning, critical
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    id: str
    type: str  # chart, counter, gauge, log, status
    title: str
    position: Dict[str, int]  # x, y, width, height
    data_source: str
    refresh_rate: int = 5  # seconds
    config: Dict[str, Any] = field(default_factory=dict)

class DemoDashboard:
    """Live demo monitoring and analytics dashboard"""

    def __init__(self):
        self.metrics_store = defaultdict(deque)
        self.alerts = deque(maxlen=1000)
        self.widgets = self._initialize_widgets()
        self.system_status = SystemStatus.HEALTHY
        self.start_time = datetime.now()
        self.active_sessions = {}
        self.performance_history = deque(maxlen=1000)
        self.real_time_data = {}
        self.dashboard_running = False
        self.update_thread = None

    def _initialize_widgets(self) -> Dict[str, DashboardWidget]:
        """Initialize dashboard widgets"""
        widgets = {
            'system_status': DashboardWidget(
                id='system_status',
                type='status',
                title='System Status',
                position={'x': 0, 'y': 0, 'width': 3, 'height': 2},
                data_source='system_health',
                refresh_rate=1
            ),
            'active_users': DashboardWidget(
                id='active_users',
                type='counter',
                title='Active Users',
                position={'x': 3, 'y': 0, 'width': 3, 'height': 2},
                data_source='user_count',
                refresh_rate=5
            ),
            'ai_interactions': DashboardWidget(
                id='ai_interactions',
                type='counter',
                title='AI Interactions',
                position={'x': 6, 'y': 0, 'width': 3, 'height': 2},
                data_source='ai_metrics',
                refresh_rate=2
            ),
            'real_time_events': DashboardWidget(
                id='real_time_events',
                type='counter',
                title='Real-time Events/sec',
                position={'x': 9, 'y': 0, 'width': 3, 'height': 2},
                data_source='event_rate',
                refresh_rate=1
            ),
            'performance_chart': DashboardWidget(
                id='performance_chart',
                type='chart',
                title='System Performance',
                position={'x': 0, 'y': 2, 'width': 6, 'height': 4},
                data_source='performance_metrics',
                refresh_rate=3,
                config={'chart_type': 'line', 'time_range': 300}  # 5 minutes
            ),
            'ai_conversation_quality': DashboardWidget(
                id='ai_conversation_quality',
                type='gauge',
                title='AI Conversation Quality',
                position={'x': 6, 'y': 2, 'width': 3, 'height': 2},
                data_source='ai_quality',
                refresh_rate=5
            ),
            'world_generation_health': DashboardWidget(
                id='world_generation_health',
                type='gauge',
                title='World Generation Health',
                position={'x': 9, 'y': 2, 'width': 3, 'height': 2},
                data_source='world_gen_health',
                refresh_rate=10
            ),
            'multiplayer_activity': DashboardWidget(
                id='multiplayer_activity',
                type='chart',
                title='Multiplayer Activity',
                position={'x': 0, 'y': 6, 'width': 6, 'height': 4},
                data_source='multiplayer_stats',
                refresh_rate=2,
                config={'chart_type': 'area', 'time_range': 600}  # 10 minutes
            ),
            'recent_alerts': DashboardWidget(
                id='recent_alerts',
                type='log',
                title='Recent Alerts',
                position={'x': 6, 'y': 4, 'width': 6, 'height': 6},
                data_source='alerts',
                refresh_rate=1,
                config={'max_entries': 10}
            ),
            'resource_usage': DashboardWidget(
                id='resource_usage',
                type='chart',
                title='Resource Usage',
                position={'x': 6, 'y': 6, 'width': 6, 'height': 4},
                data_source='system_resources',
                refresh_rate=2,
                config={'chart_type': 'stacked_area', 'time_range': 300}
            ),
            'demo_progress': DashboardWidget(
                id='demo_progress',
                type='progress',
                title='Demo Progress',
                position={'x': 0, 'y': 10, 'width': 12, 'height': 2},
                data_source='demo_status',
                refresh_rate=5
            )
        }

        return widgets

    async def start_dashboard(self) -> None:
        """Start the dashboard monitoring"""
        logger.info("📊 Starting DMLogn8n Demo Dashboard...")

        self.dashboard_running = True

        # Start background update thread
        self.update_thread = threading.Thread(target=self._run_background_updates, daemon=True)
        self.update_thread.start()

        # Initialize demo data simulation
        await self._initialize_demo_simulation()

        logger.info("✅ Dashboard started successfully")

    async def stop_dashboard(self) -> None:
        """Stop the dashboard monitoring"""
        logger.info("📊 Stopping dashboard...")

        self.dashboard_running = False

        if self.update_thread:
            self.update_thread.join(timeout=5)

        logger.info("✅ Dashboard stopped")

    def _run_background_updates(self) -> None:
        """Run background updates for dashboard data"""
        while self.dashboard_running:
            try:
                # Update system metrics
                self._update_system_metrics()

                # Update demo simulations
                self._update_demo_simulations()

                # Check for alerts
                self._check_system_alerts()

                # Sleep for a short interval
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                time.sleep(1)

    async def _initialize_demo_simulation(self) -> None:
        """Initialize demo data simulations"""
        logger.info("🎭 Initializing demo simulations...")

        # Start various demo simulations
        asyncio.create_task(self._simulate_user_activity())
        asyncio.create_task(self._simulate_ai_interactions())
        asyncio.create_task(self._simulate_multiplayer_activity())
        asyncio.create_task(self._simulate_world_generation())
        asyncio.create_task(self._simulate_real_time_events())

    def _update_system_metrics(self) -> None:
        """Update system performance metrics"""
        current_time = datetime.now()

        # Simulate system metrics
        cpu_usage = random.uniform(20, 80)
        memory_usage = random.uniform(30, 70)
        disk_usage = random.uniform(40, 60)
        network_io = random.uniform(10, 100)

        # Store metrics
        self._add_metric('system_cpu', MetricType.GAUGE, cpu_usage, current_time, unit='%')
        self._add_metric('system_memory', MetricType.GAUGE, memory_usage, current_time, unit='%')
        self._add_metric('system_disk', MetricType.GAUGE, disk_usage, current_time, unit='%')
        self._add_metric('system_network', MetricType.GAUGE, network_io, current_time, unit='Mbps')

        # Update system status based on metrics
        if cpu_usage > 80 or memory_usage > 80:
            self.system_status = SystemStatus.CRITICAL
        elif cpu_usage > 60 or memory_usage > 60:
            self.system_status = SystemStatus.WARNING
        else:
            self.system_status = SystemStatus.HEALTHY

    def _update_demo_simulations(self) -> None:
        """Update various demo simulations"""
        current_time = datetime.now()

        # Simulate active users
        active_users = random.randint(50, 500)
        self._add_metric('active_users', MetricType.GAUGE, active_users, current_time)

        # Simulate real-time events
        event_rate = random.uniform(10, 100)
        self._add_metric('event_rate', MetricType.GAUGE, event_rate, current_time, unit='events/sec')

        # Simulate response times
        response_time = random.uniform(20, 150)
        self._add_metric('response_time', MetricType.TIMER, response_time, current_time, unit='ms')

    async def _simulate_user_activity(self) -> None:
        """Simulate user activity patterns"""
        while self.dashboard_running:
            # Simulate user logins/logouts
            if random.random() < 0.1:  # 10% chance
                user_action = 'login' if random.random() < 0.6 else 'logout'
                user_id = f"user_{random.randint(1000, 9999)}"

                if user_action == 'login':
                    self.active_sessions[user_id] = {
                        'login_time': datetime.now(),
                        'activity': 'active'
                    }
                else:
                    # Random user logout
                    if self.active_sessions:
                        logout_user = random.choice(list(self.active_sessions.keys()))
                        del self.active_sessions[logout_user]

            await asyncio.sleep(2)

    async def _simulate_ai_interactions(self) -> None:
        """Simulate AI conversation interactions"""
        while self.dashboard_running:
            # Simulate AI conversation quality
            quality_score = random.uniform(70, 95)
            self._add_metric('ai_quality', MetricType.GAUGE, quality_score, datetime.now(), unit='%')

            # Simulate AI response times
            ai_response_time = random.uniform(100, 500)
            self._add_metric('ai_response_time', MetricType.TIMER, ai_response_time, datetime.now(), unit='ms')

            await asyncio.sleep(3)

    async def _simulate_multiplayer_activity(self) -> None:
        """Simulate multiplayer game activity"""
        while self.dashboard_running:
            # Simulate active games
            active_games = random.randint(5, 25)
            self._add_metric('active_games', MetricType.GAUGE, active_games, datetime.now())

            # Simulate player counts per game type
            game_types = ['pvp', 'pve', 'raid', 'battle_royale']
            for game_type in game_types:
                players = random.randint(10, 200)
                self._add_metric(f'players_{game_type}', MetricType.GAUGE, players, datetime.now(), tags={'game_type': game_type})

            await asyncio.sleep(4)

    async def _simulate_world_generation(self) -> None:
        """Simulate world generation activity"""
        while self.dashboard_running:
            # Simulate world generation health
            generation_health = random.uniform(80, 100)
            self._add_metric('world_gen_health', MetricType.GAUGE, generation_health, datetime.now(), unit='%')

            # Simulate active worlds
            active_worlds = random.randint(3, 15)
            self._add_metric('active_worlds', MetricType.GAUGE, active_worlds, datetime.now())

            await asyncio.sleep(5)

    async def _simulate_real_time_events(self) -> None:
        """Simulate real-time event processing"""
        while self.dashboard_running:
            # Simulate event processing rate
            events_processed = random.randint(50, 500)
            self._add_metric('events_processed', MetricType.COUNTER, events_processed, datetime.now())

            # Simulate event queue size
            queue_size = random.randint(0, 100)
            self._add_metric('event_queue_size', MetricType.GAUGE, queue_size, datetime.now())

            await asyncio.sleep(1)

    def _add_metric(self, name: str, metric_type: MetricType, value: float, timestamp: datetime, unit: str = "", tags: Dict[str, str] = None) -> None:
        """Add a metric to the store"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=timestamp,
            unit=unit,
            tags=tags or {}
        )

        self.metrics_store[name].append(metric)

        # Keep only recent metrics (last 1000 data points)
        if len(self.metrics_store[name]) > 1000:
            self.metrics_store[name].popleft()

    def _check_system_alerts(self) -> None:
        """Check for system alerts and create them if needed"""
        current_time = datetime.now()

        # Check CPU usage
        cpu_metrics = list(self.metrics_store.get('system_cpu', []))
        if cpu_metrics:
            latest_cpu = cpu_metrics[-1].value
            if latest_cpu > 80:
                self._create_alert('critical', 'High CPU Usage', f'CPU usage is at {latest_cpu:.1f}%')
            elif latest_cpu > 60:
                self._create_alert('warning', 'Elevated CPU Usage', f'CPU usage is at {latest_cpu:.1f}%')

        # Check memory usage
        memory_metrics = list(self.metrics_store.get('system_memory', []))
        if memory_metrics:
            latest_memory = memory_metrics[-1].value
            if latest_memory > 80:
                self._create_alert('critical', 'High Memory Usage', f'Memory usage is at {latest_memory:.1f}%')

        # Check response times
        response_metrics = list(self.metrics_store.get('response_time', []))
        if response_metrics:
            latest_response = response_metrics[-1].value
            if latest_response > 200:
                self._create_alert('warning', 'High Response Time', f'Response time is {latest_response:.1f}ms')

    def _create_alert(self, level: str, title: str, message: str) -> None:
        """Create a new alert"""
        # Check if similar alert already exists and is not resolved
        for alert in self.alerts:
            if not alert.resolved and alert.title == title:
                return  # Don't duplicate

        alert = Alert(
            id=f"alert_{int(time.time())}_{random.randint(1000, 9999)}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now()
        )

        self.alerts.append(alert)
        logger.warning(f"Alert created: {level.upper()} - {title}: {message}")

    def get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """Get data for a specific widget"""
        if widget_id not in self.widgets:
            return {"error": "Widget not found"}

        widget = self.widgets[widget_id]
        data_source = widget.data_source

        # Return data based on data source
        if data_source == 'system_health':
            return self._get_system_health_data()
        elif data_source == 'user_count':
            return self._get_user_count_data()
        elif data_source == 'ai_metrics':
            return self._get_ai_metrics_data()
        elif data_source == 'event_rate':
            return self._get_event_rate_data()
        elif data_source == 'performance_metrics':
            return self._get_performance_metrics_data()
        elif data_source == 'ai_quality':
            return self._get_ai_quality_data()
        elif data_source == 'world_gen_health':
            return self._get_world_gen_health_data()
        elif data_source == 'multiplayer_stats':
            return self._get_multiplayer_stats_data()
        elif data_source == 'alerts':
            return self._get_alerts_data()
        elif data_source == 'system_resources':
            return self._get_system_resources_data()
        elif data_source == 'demo_status':
            return self._get_demo_status_data()
        else:
            return {"error": f"Unknown data source: {data_source}"}

    def _get_system_health_data(self) -> Dict[str, Any]:
        """Get system health data"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'status': self.system_status.value,
            'uptime': uptime,
            'last_update': datetime.now().isoformat(),
            'active_sessions': len(self.active_sessions),
            'metrics': {
                'cpu': list(self.metrics_store.get('system_cpu', []))[-1].value if self.metrics_store.get('system_cpu') else 0,
                'memory': list(self.metrics_store.get('system_memory', []))[-1].value if self.metrics_store.get('system_memory') else 0,
                'disk': list(self.metrics_store.get('system_disk', []))[-1].value if self.metrics_store.get('system_disk') else 0
            }
        }

    def _get_user_count_data(self) -> Dict[str, Any]:
        """Get user count data"""
        current_users = list(self.metrics_store.get('active_users', []))
        current_count = current_users[-1].value if current_users else 0

        return {
            'current': int(current_count),
            'peak': max([m.value for m in current_users]) if current_users else 0,
            'trend': 'up' if len(current_users) > 1 and current_users[-1].value > current_users[-2].value else 'down',
            'last_update': datetime.now().isoformat()
        }

    def _get_ai_metrics_data(self) -> Dict[str, Any]:
        """Get AI metrics data"""
        quality_metrics = list(self.metrics_store.get('ai_quality', []))
        response_metrics = list(self.metrics_store.get('ai_response_time', []))

        current_quality = quality_metrics[-1].value if quality_metrics else 0
        current_response = response_metrics[-1].value if response_metrics else 0

        return {
            'quality_score': current_quality,
            'response_time': current_response,
            'interactions_total': random.randint(1000, 5000),
            'satisfaction_rate': random.uniform(85, 95),
            'last_update': datetime.now().isoformat()
        }

    def _get_event_rate_data(self) -> Dict[str, Any]:
        """Get real-time event rate data"""
        event_metrics = list(self.metrics_store.get('event_rate', []))
        current_rate = event_metrics[-1].value if event_metrics else 0

        return {
            'current_rate': current_rate,
            'peak_rate': max([m.value for m in event_metrics]) if event_metrics else 0,
            'total_processed': random.randint(10000, 100000),
            'queue_size': list(self.metrics_store.get('event_queue_size', []))[-1].value if self.metrics_store.get('event_queue_size') else 0,
            'last_update': datetime.now().isoformat()
        }

    def _get_performance_metrics_data(self) -> Dict[str, Any]:
        """Get performance metrics chart data"""
        # Get last 5 minutes of data
        cutoff_time = datetime.now() - timedelta(minutes=5)

        cpu_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_cpu', []) if m.timestamp > cutoff_time]
        memory_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_memory', []) if m.timestamp > cutoff_time]
        response_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('response_time', []) if m.timestamp > cutoff_time]

        return {
            'series': [
                {'name': 'CPU Usage', 'data': cpu_data, 'unit': '%'},
                {'name': 'Memory Usage', 'data': memory_data, 'unit': '%'},
                {'name': 'Response Time', 'data': response_data, 'unit': 'ms'}
            ],
            'time_range': 300,
            'last_update': datetime.now().isoformat()
        }

    def _get_ai_quality_data(self) -> Dict[str, Any]:
        """Get AI conversation quality gauge data"""
        quality_metrics = list(self.metrics_store.get('ai_quality', []))
        current_quality = quality_metrics[-1].value if quality_metrics else 0

        return {
            'current_value': current_quality,
            'min_value': 0,
            'max_value': 100,
            'thresholds': {
                'good': 80,
                'warning': 60,
                'critical': 40
            },
            'status': 'excellent' if current_quality >= 80 else 'good' if current_quality >= 60 else 'poor',
            'last_update': datetime.now().isoformat()
        }

    def _get_world_gen_health_data(self) -> Dict[str, Any]:
        """Get world generation health data"""
        health_metrics = list(self.metrics_store.get('world_gen_health', []))
        current_health = health_metrics[-1].value if health_metrics else 0
        active_worlds = list(self.metrics_store.get('active_worlds', []))
        current_worlds = active_worlds[-1].value if active_worlds else 0

        return {
            'health_score': current_health,
            'active_worlds': int(current_worlds),
            'generation_time_avg': random.uniform(1.5, 3.5),
            'success_rate': random.uniform(95, 99),
            'last_update': datetime.now().isoformat()
        }

    def _get_multiplayer_stats_data(self) -> Dict[str, Any]:
        """Get multiplayer activity statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=10)

        pvp_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('players_pvp', []) if m.timestamp > cutoff_time]
        pve_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('players_pve', []) if m.timestamp > cutoff_time]
        raid_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('players_raid', []) if m.timestamp > cutoff_time]

        active_games = list(self.metrics_store.get('active_games', []))
        current_games = active_games[-1].value if active_games else 0

        return {
            'series': [
                {'name': 'PvP Players', 'data': pvp_data},
                {'name': 'PvE Players', 'data': pve_data},
                {'name': 'Raid Players', 'data': raid_data}
            ],
            'active_games': int(current_games),
            'total_players': sum([pvp_data[-1][1] if pvp_data else 0,
                                 pve_data[-1][1] if pve_data else 0,
                                 raid_data[-1][1] if raid_data else 0]),
            'time_range': 600,
            'last_update': datetime.now().isoformat()
        }

    def _get_alerts_data(self) -> Dict[str, Any]:
        """Get recent alerts data"""
        recent_alerts = list(self.alerts)[-10:]  # Last 10 alerts

        return {
            'alerts': [
                {
                    'id': alert.id,
                    'level': alert.level,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                } for alert in recent_alerts
            ],
            'total_count': len(self.alerts),
            'unresolved_count': sum(1 for a in self.alerts if not a.resolved),
            'last_update': datetime.now().isoformat()
        }

    def _get_system_resources_data(self) -> Dict[str, Any]:
        """Get system resource usage data"""
        cutoff_time = datetime.now() - timedelta(minutes=5)

        cpu_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_cpu', []) if m.timestamp > cutoff_time]
        memory_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_memory', []) if m.timestamp > cutoff_time]
        disk_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_disk', []) if m.timestamp > cutoff_time]
        network_data = [(m.timestamp.isoformat(), m.value) for m in self.metrics_store.get('system_network', []) if m.timestamp > cutoff_time]

        return {
            'series': [
                {'name': 'CPU', 'data': cpu_data, 'unit': '%'},
                {'name': 'Memory', 'data': memory_data, 'unit': '%'},
                {'name': 'Disk', 'data': disk_data, 'unit': '%'},
                {'name': 'Network', 'data': network_data, 'unit': 'Mbps'}
            ],
            'time_range': 300,
            'last_update': datetime.now().isoformat()
        }

    def _get_demo_status_data(self) -> Dict[str, Any]:
        """Get overall demo progress status"""
        demo_components = [
            {'name': 'AI Characters', 'status': 'active', 'progress': 100},
            {'name': 'Multiplayer', 'status': 'active', 'progress': 100},
            {'name': 'World Generation', 'status': 'active', 'progress': 100},
            {'name': 'Real-time Features', 'status': 'active', 'progress': 100},
            {'name': 'Sample Data', 'status': 'completed', 'progress': 100},
            {'name': 'Demo Scenarios', 'status': 'completed', 'progress': 100},
            {'name': 'Performance Testing', 'status': 'running', 'progress': 75},
            {'name': 'Cross-platform Testing', 'status': 'pending', 'progress': 30}
        ]

        total_progress = sum(comp['progress'] for comp in demo_components) / len(demo_components)

        return {
            'components': demo_components,
            'overall_progress': total_progress,
            'status': 'running' if total_progress < 100 else 'completed',
            'estimated_completion': (datetime.now() + timedelta(minutes=15)).isoformat() if total_progress < 100 else datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }

    def get_full_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data for all widgets"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'system_status': self.system_status.value,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'widgets': {}
        }

        # Get data for each widget
        for widget_id, widget in self.widgets.items():
            dashboard_data['widgets'][widget_id] = {
                'id': widget.id,
                'type': widget.type,
                'title': widget.title,
                'position': widget.position,
                'data': self.get_widget_data(widget_id),
                'last_update': datetime.now().isoformat()
            }

        return dashboard_data

    async def display_live_dashboard(self) -> None:
        """Display a live updating dashboard in console"""
        print("\n" + "="*80)
        print("📊 DMLOGN8N LIVE DEMO DASHBOARD")
        print("="*80)
        print("Real-time monitoring of all demo activities")
        print(f"System Status: {self.system_status.value.upper()} | Uptime: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        print("="*80)

        while self.dashboard_running:
            # Clear screen (or print separator)
            print("\n" + "-"*80)
            print(f"📊 Dashboard Update: {datetime.now().strftime('%H:%M:%S')}")
            print("-"*80)

            # System Overview
            system_health = self._get_system_health_data()
            print(f"🖥️  SYSTEM STATUS: {system_health['status'].upper()}")
            print(f"   CPU: {system_health['metrics']['cpu']:.1f}% | Memory: {system_health['metrics']['memory']:.1f}% | Disk: {system_health['metrics']['disk']:.1f}%")
            print(f"   Active Sessions: {system_health['active_sessions']} | Uptime: {system_health['uptime']:.1f}s")

            # User Metrics
            user_data = self._get_user_count_data()
            print(f"\n👥 ACTIVE USERS: {user_data['current']} (Peak: {user_data['peak']}) [{user_data['trend']}]")

            # AI Metrics
            ai_data = self._get_ai_metrics_data()
            print(f"🤖 AI QUALITY: {ai_data['quality_score']:.1f}% | Response Time: {ai_data['response_time']:.1f}ms")

            # Event Rate
            event_data = self._get_event_rate_data()
            print(f"⚡ EVENT RATE: {event_data['current_rate']:.1f}/sec | Queue: {event_data['queue_size']}")

            # Multiplayer
            multiplayer_data = self._get_multiplayer_stats_data()
            print(f"⚔️  MULTIPLAYER: {multiplayer_data['active_games']} active games | {multiplayer_data['total_players']} players")

            # World Generation
            world_data = self._get_world_gen_health_data()
            print(f"🌍 WORLD GEN: {world_data['health_score']:.1f}% health | {world_data['active_worlds']} active worlds")

            # Recent Alerts
            alerts_data = self._get_alerts_data()
            if alerts_data['unresolved_count'] > 0:
                print(f"\n🚨 ALERTS ({alerts_data['unresolved_count']} unresolved):")
                for alert in alerts_data['alerts'][-3:]:  # Show last 3
                    if not alert['resolved']:
                        level_emoji = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🚨'}.get(alert['level'], '📢')
                        print(f"   {level_emoji} {alert['title']}: {alert['message']}")

            # Demo Progress
            demo_data = self._get_demo_status_data()
            print(f"\n📈 DEMO PROGRESS: {demo_data['overall_progress']:.1f}% - {demo_data['status'].upper()}")

            await asyncio.sleep(5)  # Update every 5 seconds

    async def export_dashboard_report(self, filename: str = "dashboard_report.json") -> str:
        """Export complete dashboard report"""
        report_data = {
            'report_timestamp': datetime.now().isoformat(),
            'dashboard_data': self.get_full_dashboard_data(),
            'summary': {
                'total_widgets': len(self.widgets),
                'system_status': self.system_status.value,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'total_alerts': len(self.alerts),
                'unresolved_alerts': sum(1 for a in self.alerts if not a.resolved),
                'active_sessions': len(self.active_sessions)
            },
            'metrics_summary': {}
        }

        # Add metrics summary
        for metric_name, metrics in self.metrics_store.items():
            if metrics:
                values = [m.value for m in metrics]
                report_data['metrics_summary'][metric_name] = {
                    'current': values[-1],
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'count': len(values)
                }

        # Save to file
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Dashboard report exported to {filename}")
        return filename

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a specific alert"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert.title}")
                return True
        return False

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics"""
        return {
            'system_status': self.system_status.value,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'active_widgets': len(self.widgets),
            'total_metrics': sum(len(metrics) for metrics in self.metrics_store.values()),
            'total_alerts': len(self.alerts),
            'unresolved_alerts': sum(1 for a in self.alerts if not a.resolved),
            'active_sessions': len(self.active_sessions),
            'last_update': datetime.now().isoformat()
        }