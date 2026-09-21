#!/usr/bin/env python3
"""
DMLogn8n Multi-Agent Platform Monitoring Dashboard Service
Real-time monitoring and metrics visualization for agents, system health, and business metrics
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
from aiohttp import web, WSMsgType
import aiofiles
import redis
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest
import psutil
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: str
    agent_type: str
    status: str
    response_time: float
    throughput: float
    error_rate: float
    memory_usage: float
    cpu_usage: float
    last_active: datetime
    total_requests: int
    successful_requests: int
    avg_processing_time: float

@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    gpu_usage: float
    active_connections: int
    system_load: List[float]

@dataclass
class BusinessMetrics:
    """Business KPIs"""
    timestamp: datetime
    active_users: int
    active_sessions: int
    total_games: int
    completed_games: int
    user_satisfaction: float
    revenue: float
    conversion_rate: float

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    timestamp: datetime
    connection_pool_size: int
    active_connections: int
    query_response_time: float
    query_rate: float
    error_rate: float
    slow_queries: int
    cache_hit_rate: float

class MetricsCollector:
    """Central metrics collection coordinator"""

    def __init__(self):
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.business_metrics: List[BusinessMetrics] = []
        self.database_metrics: List[DatabaseMetrics] = []
        self.websocket_clients = set()

        # Initialize Prometheus metrics
        self.registry = CollectorRegistry()

        # Agent metrics
        self.agent_response_time = Histogram('agent_response_time_seconds', 'Agent response time', ['agent_type'], registry=self.registry)
        self.agent_throughput = Counter('agent_throughput_total', 'Agent throughput', ['agent_id'], registry=self.registry)
        self.agent_error_rate = Gauge('agent_error_rate', 'Agent error rate', ['agent_id'], registry=self.registry)

        # System metrics
        self.system_cpu_usage = Gauge('system_cpu_usage_percent', 'System CPU usage', registry=self.registry)
        self.system_memory_usage = Gauge('system_memory_usage_percent', 'System memory usage', registry=self.registry)
        self.system_disk_usage = Gauge('system_disk_usage_percent', 'System disk usage', registry=self.registry)

        # Business metrics
        self.active_users = Gauge('active_users_total', 'Active users', registry=self.registry)
        self.active_sessions = Gauge('active_sessions_total', 'Active game sessions', registry=self.registry)
        self.revenue = Counter('revenue_total', 'Total revenue', registry=self.registry)

    async def collect_agent_metrics(self):
        """Collect metrics from all active agents"""
        try:
            # Simulate agent metrics collection
            # In production, this would query actual agent endpoints
            agent_types = ['dungeon_master', 'character_manager', 'dialogue_engine', 'world_builder', 'narrative_coordinator']

            for i, agent_type in enumerate(agent_types):
                agent_id = f"{agent_type}_{i+1}"

                # Simulate varying metrics
                response_time = np.random.normal(0.5, 0.1)
                throughput = np.random.normal(100, 20)
                error_rate = np.random.uniform(0.01, 0.05)
                memory_usage = np.random.uniform(100, 500)
                cpu_usage = np.random.uniform(10, 80)

                metrics = AgentMetrics(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status=np.random.choice(['active', 'idle', 'busy'], p=[0.7, 0.2, 0.1]),
                    response_time=response_time,
                    throughput=throughput,
                    error_rate=error_rate,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    last_active=datetime.now(),
                    total_requests=int(np.random.normal(1000, 200)),
                    successful_requests=int(np.random.normal(950, 150)),
                    avg_processing_time=response_time
                )

                self.agent_metrics[agent_id] = metrics

                # Update Prometheus metrics
                self.agent_response_time.labels(agent_type=agent_type).observe(response_time)
                self.agent_throughput.labels(agent_id=agent_id).inc(int(throughput))
                self.agent_error_rate.labels(agent_id=agent_id).set(error_rate)

        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")

    async def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                gpu_usage=np.random.uniform(0, 100),  # Simulated GPU usage
                active_connections=len(psutil.net_connections()),
                system_load=list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            )

            self.system_metrics.append(metrics)

            # Keep only last 1000 entries
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]

            # Update Prometheus metrics
            self.system_cpu_usage.set(cpu_percent)
            self.system_memory_usage.set(memory.percent)
            self.system_disk_usage.set(disk.percent)

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def collect_business_metrics(self):
        """Collect business KPIs"""
        try:
            metrics = BusinessMetrics(
                timestamp=datetime.now(),
                active_users=int(np.random.normal(150, 30)),
                active_sessions=int(np.random.normal(45, 10)),
                total_games=int(np.random.normal(1000, 100)),
                completed_games=int(np.random.normal(850, 80)),
                user_satisfaction=np.random.uniform(4.0, 5.0),
                revenue=np.random.normal(1000, 200),
                conversion_rate=np.random.uniform(0.05, 0.15)
            )

            self.business_metrics.append(metrics)

            # Keep only last 1000 entries
            if len(self.business_metrics) > 1000:
                self.business_metrics = self.business_metrics[-1000:]

            # Update Prometheus metrics
            self.active_users.set(metrics.active_users)
            self.active_sessions.set(metrics.active_sessions)
            self.revenue.inc(np.random.normal(10, 2))

        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")

    async def collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            metrics = DatabaseMetrics(
                timestamp=datetime.now(),
                connection_pool_size=20,
                active_connections=int(np.random.normal(15, 5)),
                query_response_time=np.random.normal(0.05, 0.01),
                query_rate=np.random.normal(1000, 200),
                error_rate=np.random.uniform(0.001, 0.01),
                slow_queries=int(np.random.normal(5, 2)),
                cache_hit_rate=np.random.uniform(0.8, 0.95)
            )

            self.database_metrics.append(metrics)

            # Keep only last 1000 entries
            if len(self.database_metrics) > 1000:
                self.database_metrics = self.database_metrics[-1000:]

        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")

    async def start_collection(self):
        """Start continuous metrics collection"""
        while True:
            try:
                await asyncio.gather(
                    self.collect_agent_metrics(),
                    self.collect_system_metrics(),
                    self.collect_business_metrics(),
                    self.collect_database_metrics()
                )

                # Broadcast updates to WebSocket clients
                await self.broadcast_metrics_update()

                await asyncio.sleep(10)  # Collect every 10 seconds

            except Exception as e:
                logger.error(f"Error in metrics collection cycle: {e}")
                await asyncio.sleep(5)

    async def broadcast_metrics_update(self):
        """Broadcast metrics updates to all WebSocket clients"""
        if not self.websocket_clients:
            return

        update = {
            'type': 'metrics_update',
            'timestamp': datetime.now().isoformat(),
            'agent_metrics': {k: asdict(v) for k, v in self.agent_metrics.items()},
            'system_metrics': asdict(self.system_metrics[-1]) if self.system_metrics else None,
            'business_metrics': asdict(self.business_metrics[-1]) if self.business_metrics else None,
            'database_metrics': asdict(self.database_metrics[-1]) if self.database_metrics else None
        }

        # Convert datetime objects to ISO strings
        for metric_type in ['agent_metrics', 'system_metrics', 'business_metrics', 'database_metrics']:
            if metric_type in update and update[metric_type]:
                if isinstance(update[metric_type], dict):
                    for key, value in update[metric_type].items():
                        if isinstance(value, datetime):
                            update[metric_type][key] = value.isoformat()

        message = json.dumps(update)

        # Send to all connected clients
        disconnected_clients = set()
        for ws in self.websocket_clients:
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.warning(f"Failed to send update to WebSocket client: {e}")
                disconnected_clients.add(ws)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

class DashboardAPI:
    """REST API for dashboard data"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    async def get_agent_metrics(self, request):
        """Get agent performance metrics"""
        agent_id = request.query.get('agent_id')

        if agent_id:
            metrics = self.metrics_collector.agent_metrics.get(agent_id)
            if metrics:
                return web.json_response(asdict(metrics))
            else:
                return web.json_response({'error': 'Agent not found'}, status=404)
        else:
            # Return all agent metrics
            return web.json_response({
                k: asdict(v) for k, v in self.metrics_collector.agent_metrics.items()
            })

    async def get_system_metrics(self, request):
        """Get system metrics history"""
        limit = int(request.query.get('limit', 100))

        metrics = self.metrics_collector.system_metrics[-limit:]
        return web.json_response([asdict(m) for m in metrics])

    async def get_business_metrics(self, request):
        """Get business metrics history"""
        limit = int(request.query.get('limit', 100))

        metrics = self.metrics_collector.business_metrics[-limit:]
        return web.json_response([asdict(m) for m in metrics])

    async def get_database_metrics(self, request):
        """Get database metrics history"""
        limit = int(request.query.get('limit', 100))

        metrics = self.metrics_collector.database_metrics[-limit:]
        return web.json_response([asdict(m) for m in metrics])

    async def get_prometheus_metrics(self, request):
        """Get Prometheus metrics"""
        metrics_data = generate_latest(self.metrics_collector.registry)
        return web.Response(body=metrics_data, content_type='text/plain')

    async def get_dashboard_summary(self, request):
        """Get dashboard summary statistics"""
        latest_system = self.metrics_collector.system_metrics[-1] if self.metrics_collector.system_metrics else None
        latest_business = self.metrics_collector.business_metrics[-1] if self.metrics_collector.business_metrics else None

        summary = {
            'timestamp': datetime.now().isoformat(),
            'agents': {
                'total': len(self.metrics_collector.agent_metrics),
                'active': sum(1 for m in self.metrics_collector.agent_metrics.values() if m.status == 'active'),
                'busy': sum(1 for m in self.metrics_collector.agent_metrics.values() if m.status == 'busy'),
                'idle': sum(1 for m in self.metrics_collector.agent_metrics.values() if m.status == 'idle')
            },
            'system': {
                'cpu_usage': latest_system.cpu_usage if latest_system else 0,
                'memory_usage': latest_system.memory_usage if latest_system else 0,
                'disk_usage': latest_system.disk_usage if latest_system else 0
            },
            'business': {
                'active_users': latest_business.active_users if latest_business else 0,
                'active_sessions': latest_business.active_sessions if latest_business else 0,
                'user_satisfaction': latest_business.user_satisfaction if latest_business else 0
            }
        }

        return web.json_response(summary)

class WebSocketHandler:
    """WebSocket handler for real-time updates"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    async def handle_websocket(self, request):
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Add to connected clients
        self.metrics_collector.websocket_clients.add(ws)
        logger.info(f"WebSocket client connected. Total clients: {len(self.metrics_collector.websocket_clients)}")

        try:
            # Send initial data
            initial_data = {
                'type': 'initial_data',
                'timestamp': datetime.now().isoformat(),
                'agent_metrics': {k: asdict(v) for k, v in self.metrics_collector.agent_metrics.items()},
                'system_metrics': asdict(self.metrics_collector.system_metrics[-1]) if self.metrics_collector.system_metrics else None,
                'business_metrics': asdict(self.metrics_collector.business_metrics[-1]) if self.metrics_collector.business_metrics else None,
                'database_metrics': asdict(self.metrics_collector.database_metrics[-1]) if self.metrics_collector.database_metrics else None
            }

            # Convert datetime objects to ISO strings
            for metric_type in ['agent_metrics', 'system_metrics', 'business_metrics', 'database_metrics']:
                if metric_type in initial_data and initial_data[metric_type]:
                    if isinstance(initial_data[metric_type], dict):
                        for key, value in initial_data[metric_type].items():
                            if isinstance(value, datetime):
                                initial_data[metric_type][key] = value.isoformat()

            await ws.send_str(json.dumps(initial_data))

            # Keep connection alive
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if data.get('type') == 'ping':
                        await ws.send_str(json.dumps({'type': 'pong'}))
                    elif data.get('type') == 'subscribe':
                        # Handle subscription to specific metrics
                        await ws.send_str(json.dumps({'type': 'subscribed'}))

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Remove from connected clients
            self.metrics_collector.websocket_clients.discard(ws)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.metrics_collector.websocket_clients)}")

        return ws

async def serve_dashboard(request):
    """Serve the main dashboard HTML page"""
    try:
        async with aiofiles.open('/home/activeloguser/DMLogn8n/multi-portal-gateway/monitoring/templates/dashboard.html', 'r') as f:
            content = await f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text="Dashboard template not found", status=404)

async def create_app():
    """Create the dashboard web application"""
    metrics_collector = MetricsCollector()
    dashboard_api = DashboardAPI(metrics_collector)
    websocket_handler = WebSocketHandler(metrics_collector)

    app = web.Application()

    # API routes
    app.router.add_get('/api/agents', dashboard_api.get_agent_metrics)
    app.router.add_get('/api/system', dashboard_api.get_system_metrics)
    app.router.add_get('/api/business', dashboard_api.get_business_metrics)
    app.router.add_get('/api/database', dashboard_api.get_database_metrics)
    app.router.add_get('/api/summary', dashboard_api.get_dashboard_summary)
    app.router.add_get('/api/prometheus', dashboard_api.get_prometheus_metrics)

    # WebSocket route
    app.router.add_get('/ws', websocket_handler.handle_websocket)

    # Static files
    app.router.add_get('/', serve_dashboard)
    app.router.add_static('/static/', path='/home/activeloguser/DMLogn8n/multi-portal-gateway/monitoring/static', name='static')

    # Start metrics collection in background
    asyncio.create_task(metrics_collector.start_collection())

    return app

async def main():
    """Main application entry point"""
    app = await create_app()

    # Configure web server
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    logger.info("Dashboard service started on http://0.0.0.0:8080")
    logger.info("WebSocket endpoint: ws://0.0.0.0:8080/ws")
    logger.info("API documentation:")
    logger.info("  - GET /api/agents - Agent metrics")
    logger.info("  - GET /api/system - System metrics")
    logger.info("  - GET /api/business - Business metrics")
    logger.info("  - GET /api/database - Database metrics")
    logger.info("  - GET /api/summary - Dashboard summary")
    logger.info("  - GET /api/prometheus - Prometheus metrics")

    # Keep the application running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard service...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())