#!/usr/bin/env python3
"""
Dashboard API Endpoints for DMLogn8n Monitoring
Provides REST API for metrics, alerts, and dashboard data
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from aiohttp import web, WSMsgType
from aiohttp.web import middleware
import aiohttp_cors
from .metrics_storage import MetricsStorage, MetricPoint
from .alerting import AlertManager, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)

class DashboardAPI:
    """REST API for dashboard data and operations"""

    def __init__(self, metrics_storage: MetricsStorage, alert_manager: AlertManager):
        self.metrics_storage = metrics_storage
        self.alert_manager = alert_manager
        self.websocket_clients = set()

    def setup_routes(self, app: web.Application):
        """Setup API routes"""
        # Add CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # Metrics endpoints
        metrics_router = app.router.add_resource('/api/metrics')
        cors.add(metrics_router.add_route('GET', self.get_metrics))
        cors.add(metrics_router.add_route('POST', self.store_metrics))

        # Specific metric endpoints
        cors.add(app.router.add_get('/api/metrics/{metric_name}', self.get_metric))
        cors.add(app.router.add_get('/api/metrics/{metric_name}/latest', self.get_latest_metric))
        cors.add(app.router.add_get('/api/metrics/{metric_name}/aggregate', self.get_aggregated_metrics))

        # Metric names endpoint
        cors.add(app.router.add_get('/api/metrics', self.list_metrics))

        # Alerts endpoints
        alerts_router = app.router.add_resource('/api/alerts')
        cors.add(alerts_router.add_route('GET', self.get_alerts))
        cors.add(alerts_router.add_route('POST', self.create_alert_rule))

        cors.add(app.router.add_get('/api/alerts/active', self.get_active_alerts))
        cors.add(app.router.add_get('/api/alerts/history', self.get_alert_history))
        cors.add(app.router.add_post('/api/alerts/{alert_id}/acknowledge', self.acknowledge_alert))
        cors.add(app.router.add_post('/api/alerts/{alert_id}/suppress', self.suppress_alert))

        # Dashboard endpoints
        cors.add(app.router.add_get('/api/dashboard/summary', self.get_dashboard_summary))
        cors.add(app.router.add_get('/api/dashboard/system', self.get_system_dashboard))
        cors.add(app.router.add_get('/api/dashboard/agents', self.get_agents_dashboard))
        cors.add(app.router.add_get('/api/dashboard/business', self.get_business_dashboard))

        # Export endpoints
        cors.add(app.router.add_get('/api/export/metrics/{metric_name}', self.export_metrics))

        # Health endpoint
        cors.add(app.router.add_get('/api/health', self.health_check))

        # WebSocket endpoint
        cors.add(app.router.add_get('/ws', self.websocket_handler))

    @middleware
    async def error_middleware(self, request: web.Request, handler):
        """Error handling middleware"""
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled error in {request.path}: {e}")
            return web.json_response(
                {"error": "Internal server error", "message": str(e)},
                status=500
            )

    @middleware
    async def logging_middleware(self, request: web.Request, handler):
        """Request logging middleware"""
        start_time = datetime.now()
        try:
            response = await handler(request)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{request.method} {request.path} - {response.status} - {duration:.3f}s")
            return response
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{request.method} {request.path} - ERROR - {duration:.3f}s - {e}")
            raise

    async def get_metrics(self, request: web.Request) -> web.Response:
        """Get multiple metrics with optional filtering"""
        try:
            # Parse query parameters
            metric_names = request.query.get('names', '').split(',') if request.query.get('names') else None
            start_time = self._parse_datetime(request.query.get('start_time'))
            end_time = self._parse_datetime(request.query.get('end_time'))
            limit = int(request.query.get('limit', 1000))
            labels = self._parse_labels(request.query.get('labels', ''))

            if metric_names:
                # Get specific metrics
                all_metrics = {}
                for metric_name in metric_names:
                    if metric_name.strip():
                        metrics = await self.metrics_storage.get_metrics(
                            metric_name.strip(), start_time, end_time, labels, limit
                        )
                        all_metrics[metric_name.strip()] = [asdict(m) for m in metrics]
                return web.json_response(all_metrics)
            else:
                # Get all recent metrics (limited)
                metric_names = await self.metrics_storage.get_metric_names()
                recent_metrics = {}
                for metric_name in metric_names[:20]:  # Limit to 20 metrics
                    latest = await self.metrics_storage.get_latest_value(metric_name, labels)
                    if latest:
                        recent_metrics[metric_name] = asdict(latest)
                return web.json_response(recent_metrics)

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def store_metrics(self, request: web.Request) -> web.Response:
        """Store multiple metrics"""
        try:
            data = await request.json()

            if not isinstance(data, list):
                data = [data]

            metrics = []
            for item in data:
                metric = MetricPoint(
                    timestamp=datetime.fromisoformat(item['timestamp']) if 'timestamp' in item else datetime.now(),
                    metric_name=item['metric_name'],
                    value=item['value'],
                    labels=item.get('labels', {}),
                    tags=item.get('tags', {})
                )
                metrics.append(metric)

            await self.metrics_storage.store_metrics_batch(metrics)

            return web.json_response({"status": "success", "stored": len(metrics)})

        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_metric(self, request: web.Request) -> web.Response:
        """Get specific metric data"""
        try:
            metric_name = request.match_info['metric_name']
            start_time = self._parse_datetime(request.query.get('start_time'))
            end_time = self._parse_datetime(request.query.get('end_time'))
            limit = int(request.query.get('limit', 1000))
            labels = self._parse_labels(request.query.get('labels', ''))

            metrics = await self.metrics_storage.get_metrics(
                metric_name, start_time, end_time, labels, limit
            )

            return web.json_response([asdict(m) for m in metrics])

        except Exception as e:
            logger.error(f"Error getting metric {metric_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_latest_metric(self, request: web.Request) -> web.Response:
        """Get latest value for a metric"""
        try:
            metric_name = request.match_info['metric_name']
            labels = self._parse_labels(request.query.get('labels', ''))

            latest = await self.metrics_storage.get_latest_value(metric_name, labels)

            if latest:
                return web.json_response(asdict(latest))
            else:
                return web.json_response({"error": "Metric not found"}, status=404)

        except Exception as e:
            logger.error(f"Error getting latest metric {metric_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_aggregated_metrics(self, request: web.Request) -> web.Response:
        """Get aggregated metrics"""
        try:
            metric_name = request.match_info['metric_name']
            aggregation_type = request.query.get('type', 'avg')
            time_bucket = request.query.get('bucket', '5m')
            start_time = self._parse_datetime(request.query.get('start_time'))
            end_time = self._parse_datetime(request.query.get('end_time'))

            metrics = await self.metrics_storage.aggregate_metrics(
                metric_name, aggregation_type, time_bucket, start_time, end_time
            )

            return web.json_response([asdict(m) for m in metrics])

        except Exception as e:
            logger.error(f"Error getting aggregated metrics {metric_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def list_metrics(self, request: web.Request) -> web.Response:
        """List all available metric names"""
        try:
            metric_names = await self.metrics_storage.get_metric_names()
            return web.json_response(metric_names)

        except Exception as e:
            logger.error(f"Error listing metrics: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_alerts(self, request: web.Request) -> web.Response:
        """Get alerts with optional filtering"""
        try:
            status_filter = request.query.get('status')
            severity_filter = request.query.get('severity')
            limit = int(request.query.get('limit', 100))

            alerts = self.alert_manager.get_alert_history(limit)

            # Apply filters
            if status_filter:
                alerts = [a for a in alerts if a.status.value == status_filter]

            if severity_filter:
                alerts = [a for a in alerts if a.severity.value == severity_filter]

            return web.json_response([asdict(a) for a in alerts])

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_active_alerts(self, request: web.Request) -> web.Response:
        """Get all active alerts"""
        try:
            alerts = self.alert_manager.get_active_alerts()
            return web.json_response([asdict(a) for a in alerts])

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_alert_history(self, request: web.Request) -> web.Response:
        """Get alert history"""
        try:
            limit = int(request.query.get('limit', 100))
            alerts = self.alert_manager.get_alert_history(limit)
            return web.json_response([asdict(a) for a in alerts])

        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def acknowledge_alert(self, request: web.Request) -> web.Response:
        """Acknowledge an alert"""
        try:
            alert_id = request.match_info['alert_id']
            data = await request.json()
            acknowledged_by = data.get('acknowledged_by', 'unknown')

            self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)

            return web.json_response({"status": "acknowledged"})

        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def suppress_alert(self, request: web.Request) -> web.Response:
        """Suppress an alert"""
        try:
            alert_id = request.match_info['alert_id']
            self.alert_manager.suppress_alert(alert_id)

            return web.json_response({"status": "suppressed"})

        except Exception as e:
            logger.error(f"Error suppressing alert {alert_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_alert_rule(self, request: web.Request) -> web.Response:
        """Create a new alert rule"""
        try:
            data = await request.json()
            # Implementation would create a new alert rule
            # For now, return success
            return web.json_response({"status": "created", "rule_id": "new_rule_id"})

        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_dashboard_summary(self, request: web.Request) -> web.Response:
        """Get dashboard summary data"""
        try:
            # Get latest system metrics
            system_metrics = {}
            system_metric_names = [
                'system_cpu_usage_percent',
                'system_memory_usage_percent',
                'system_disk_usage_percent',
                'active_users_total',
                'active_sessions_total'
            ]

            for metric_name in system_metric_names:
                latest = await self.metrics_storage.get_latest_value(metric_name)
                if latest:
                    system_metrics[metric_name] = latest.value

            # Get alert summary
            alert_summary = self.alert_manager.get_alert_summary()

            # Get storage stats
            storage_stats = await self.metrics_storage.get_storage_stats()

            summary = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": system_metrics,
                "alerts": alert_summary,
                "storage": storage_stats
            }

            return web.json_response(summary)

        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_system_dashboard(self, request: web.Request) -> web.Response:
        """Get system dashboard data"""
        try:
            # Get system metrics for the last hour
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            system_metrics = {}
            metric_names = [
                'system_cpu_usage_percent',
                'system_memory_usage_percent',
                'system_disk_usage_percent',
                'system_network_bytes_sent',
                'system_network_bytes_recv'
            ]

            for metric_name in metric_names:
                metrics = await self.metrics_storage.get_metrics(
                    metric_name, start_time, end_time, None, 100
                )
                system_metrics[metric_name] = [asdict(m) for m in metrics]

            return web.json_response({
                "timestamp": datetime.now().isoformat(),
                "metrics": system_metrics
            })

        except Exception as e:
            logger.error(f"Error getting system dashboard: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_agents_dashboard(self, request: web.Request) -> web.Response:
        """Get agents dashboard data"""
        try:
            # Get agent metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            agent_metrics = {}
            metric_names = [
                'agent_throughput_total',
                'agent_response_time_p95',
                'agent_error_rate',
                'agent_memory_usage_bytes',
                'agent_cpu_usage_percent'
            ]

            for metric_name in metric_names:
                metrics = await self.metrics_storage.get_metrics(
                    metric_name, start_time, end_time, None, 100
                )
                agent_metrics[metric_name] = [asdict(m) for m in metrics]

            return web.json_response({
                "timestamp": datetime.now().isoformat(),
                "metrics": agent_metrics
            })

        except Exception as e:
            logger.error(f"Error getting agents dashboard: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_business_dashboard(self, request: web.Request) -> web.Response:
        """Get business dashboard data"""
        try:
            # Get business metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours

            business_metrics = {}
            metric_names = [
                'active_users_total',
                'active_sessions_total',
                'user_satisfaction_score',
                'daily_revenue',
                'conversion_rate_percent'
            ]

            for metric_name in metric_names:
                metrics = await self.metrics_storage.get_metrics(
                    metric_name, start_time, end_time, None, 100
                )
                business_metrics[metric_name] = [asdict(m) for m in metrics]

            return web.json_response({
                "timestamp": datetime.now().isoformat(),
                "metrics": business_metrics
            })

        except Exception as e:
            logger.error(f"Error getting business dashboard: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def export_metrics(self, request: web.Request) -> web.Response:
        """Export metrics data"""
        try:
            metric_name = request.match_info['metric_name']
            start_time = self._parse_datetime(request.query.get('start_time'))
            end_time = self._parse_datetime(request.query.get('end_time'))
            format_type = request.query.get('format', 'json')

            data = await self.metrics_storage.export_metrics(
                metric_name, start_time, end_time, format_type
            )

            # Set appropriate content type
            if format_type.lower() == 'json':
                content_type = 'application/json'
                filename = f"{metric_name}_metrics.json"
            elif format_type.lower() == 'csv':
                content_type = 'text/csv'
                filename = f"{metric_name}_metrics.csv"
            else:
                content_type = 'application/octet-stream'
                filename = f"{metric_name}_metrics.txt"

            return web.Response(
                body=data,
                content_type=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )

        except Exception as e:
            logger.error(f"Error exporting metrics {metric_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        try:
            # Check database connectivity
            storage_stats = await self.metrics_storage.get_storage_stats()

            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "storage": storage_stats.get("sqlite", {}),
                "active_websockets": len(self.websocket_clients)
            }

            return web.json_response(health_data)

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {"status": "unhealthy", "error": str(e)},
                status=503
            )

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websocket_clients.add(ws)
        logger.info(f"WebSocket client connected. Total: {len(self.websocket_clients)}")

        try:
            # Send initial data
            await self.send_initial_data(ws)

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if data.get('type') == 'ping':
                        await ws.send_str(json.dumps({'type': 'pong'}))
                    elif data.get('type') == 'subscribe':
                        await self.handle_subscription(ws, data)
                    elif data.get('type') == 'unsubscribe':
                        await self.handle_unsubscription(ws, data)

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_clients.discard(ws)
            logger.info(f"WebSocket client disconnected. Total: {len(self.websocket_clients)}")

        return ws

    async def send_initial_data(self, ws: web.WebSocketResponse):
        """Send initial data to WebSocket client"""
        try:
            # Send dashboard summary
            summary = await self.get_dashboard_summary(None)
            await ws.send_str(json.dumps({
                'type': 'initial_data',
                'data': summary.body
            }))

        except Exception as e:
            logger.error(f"Error sending initial data: {e}")

    async def handle_subscription(self, ws: web.WebSocketResponse, data: Dict[str, Any]):
        """Handle subscription to specific metrics"""
        # Implementation would handle real-time metric subscriptions
        await ws.send_str(json.dumps({
            'type': 'subscribed',
            'subscription': data.get('subscription', 'all')
        }))

    async def handle_unsubscription(self, ws: web.WebSocketResponse, data: Dict[str, Any]):
        """Handle unsubscription from metrics"""
        # Implementation would handle metric unsubscriptions
        await ws.send_str(json.dumps({
            'type': 'unsubscribed',
            'subscription': data.get('subscription', 'all')
        }))

    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast update to all WebSocket clients"""
        if not self.websocket_clients:
            return

        message = json.dumps({
            'type': update_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })

        disconnected_clients = set()
        for ws in self.websocket_clients:
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.warning(f"Failed to send update to WebSocket client: {e}")
                disconnected_clients.add(ws)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            return None

    def _parse_labels(self, labels_str: str) -> Dict[str, str]:
        """Parse labels from query string"""
        if not labels_str:
            return {}

        labels = {}
        try:
            for pair in labels_str.split(','):
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    labels[key.strip()] = value.strip()
        except Exception:
            pass

        return labels

async def create_api_app(metrics_storage: MetricsStorage, alert_manager: AlertManager) -> web.Application:
    """Create and configure the API application"""
    api = DashboardAPI(metrics_storage, alert_manager)

    app = web.Application(middlewares=[api.logging_middleware, api.error_middleware])
    api.setup_routes(app)

    return app