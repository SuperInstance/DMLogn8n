#!/usr/bin/env python3
"""
API Endpoints for DMLogn8n Auto-Scaling
RESTful API for managing autoscaling configuration and monitoring
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import aiohttp
from aiohttp import web, WSMsgType
from aiohttp.web import middleware
import jwt
import hashlib
import secrets
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .autoscaler import AutoScalingEngine
from .monitoring import MonitoringSystem, AlertSeverity, HealthStatus
from .policies.scale_policies import ScalePolicyManager, PolicyType, PolicyStatus
from .policies.schedule_scaling import ScheduleScalingManager
from .policies.event_scaling import EventScalingManager
from .metrics.cost_optimizer import CostOptimizer
from .metrics.predictor import PredictiveScaler

# JWT Secret for authentication
JWT_SECRET = secrets.token_urlsafe(32)
JWT_ALGORITHM = 'HS256'

# CORS middleware
@middleware
async def cors_middleware(request, handler):
    """CORS middleware"""
    response = await handler(request)

    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '86400'

    return response

# Authentication middleware
@middleware
async def auth_middleware(request, handler):
    """Authentication middleware"""
    # Skip auth for health check and metrics endpoints
    if request.path in ['/health', '/metrics', '/api/docs']:
        return await handler(request)

    # Skip auth for login endpoint
    if request.path == '/api/auth/login':
        return await handler(request)

    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return web.json_response({'error': 'Missing or invalid authorization header'}, status=401)

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        request['user'] = payload
        return await handler(request)
    except jwt.ExpiredSignatureError:
        return web.json_response({'error': 'Token has expired'}, status=401)
    except jwt.InvalidTokenError:
        return web.json_response({'error': 'Invalid token'}, status=401)

class AutoScalingAPI:
    """
    RESTful API for DMLogn8n Auto-Scaling system
    """

    def __init__(self, autoscaling_engine: AutoScalingEngine, monitoring_system: MonitoringSystem):
        self.autoscaling_engine = autoscaling_engine
        self.monitoring_system = monitoring_system

        # Get component managers
        self.policy_manager = autoscaling_engine.policy_manager
        self.schedule_manager = None  # Would be initialized separately
        self.event_manager = None     # Would be initialized separately
        self.cost_optimizer = autoscaling_engine.cost_optimizer
        self.predictive_scaler = autoscaling_engine.predictive_scaler

        self.logger = logging.getLogger('autoscaling_api')

        # API configuration
        self.api_config = {
            'host': '0.0.0.0',
            'port': 8090,
            'debug': False
        }

        # Initialize sessions
        self.active_sessions = {}
        self.websocket_connections = set()

    def create_app(self) -> web.Application:
        """Create aiohttp application"""
        app = web.Application(middlewares=[cors_middleware, auth_middleware])

        # Add routes
        self._setup_routes(app)

        # Add WebSocket handler
        app.on_shutdown.append(self._on_shutdown)

        return app

    def _setup_routes(self, app: web.Application):
        """Setup API routes"""
        # Authentication routes
        app.router.add_post('/api/auth/login', self.login)
        app.router.add_post('/api/auth/logout', self.logout)
        app.router.add_post('/api/auth/refresh', self.refresh_token)

        # Health and metrics
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/metrics', self.prometheus_metrics)

        # Auto-scaling operations
        app.router.add_get('/api/autoscaling/services', self.get_services)
        app.router.add_get('/api/autoscaling/services/{service_id}', self.get_service)
        app.router.add_post('/api/autoscaling/services/{service_id}/scale', self.scale_service)
        app.router.add_get('/api/autoscaling/services/{service_id}/metrics', self.get_service_metrics)
        app.router.add_get('/api/autoscaling/services/{service_id}/history', self.get_service_history)

        # Scaling policies
        app.router.add_get('/api/policies', self.list_policies)
        app.router.add_post('/api/policies', self.create_policy)
        app.router.add_get('/api/policies/{policy_id}', self.get_policy)
        app.router.add_put('/api/policies/{policy_id}', self.update_policy)
        app.router.add_delete('/api/policies/{policy_id}', self.delete_policy)
        app.router.add_post('/api/policies/{policy_id}/activate', self.activate_policy)
        app.router.add_post('/api/policies/{policy_id}/deactivate', self.deactivate_policy)

        # Schedule-based scaling
        app.router.add_get('/api/schedules', self.list_schedules)
        app.router.add_post('/api/schedules', self.create_schedule)
        app.router.add_get('/api/schedules/{schedule_id}', self.get_schedule)
        app.router.add_put('/api/schedules/{schedule_id}', self.update_schedule)
        app.router.add_delete('/api/schedules/{schedule_id}', self.delete_schedule)
        app.router.add_get('/api/schedules/next', self.get_next_scheduled_executions)

        # Event-driven scaling
        app.router.add_get('/api/events', self.list_events)
        app.router.add_post('/api/events', self.trigger_event)
        app.router.add_get('/api/events/executions', self.get_event_executions)
        app.router.add_get('/api/events/triggers', self.list_event_triggers)
        app.router.add_post('/api/events/triggers', self.create_event_trigger)

        # Monitoring and alerts
        app.router.add_get('/api/monitoring/health', self.get_health_status)
        app.router.add_get('/api/monitoring/alerts', self.get_alerts)
        app.router.add_post('/api/monitoring/alerts/{alert_id}/acknowledge', self.acknowledge_alert)
        app.router.add_post('/api/monitoring/alerts/manual', self.create_manual_alert)
        app.router.add_get('/api/monitoring/metrics', self.get_metrics)

        # Cost optimization
        app.router.add_get('/api/costs/report', self.get_cost_report)
        app.router.add_get('/api/costs/services/{service_id}', self.get_service_costs)
        app.router.add_post('/api/costs/budget/{service_id}', self.set_budget_alert)
        app.router.add_get('/api/costs/budget/alerts', self.get_budget_alerts)

        # Predictive analytics
        app.router.add_get('/api/predictions/services/{service_id}', self.get_service_predictions)
        app.router.add_get('/api/predictions/models', self.list_prediction_models)
        app.router.get('/api/predictions/models/{service_id}', self.get_prediction_model)

        # Configuration
        app.router.add_get('/api/config', self.get_config)
        app.router.put('/api/config', self.update_config)

        # WebSocket for real-time updates
        app.router.add_get('/api/ws', self.websocket_handler)

    async def login(self, request: web.Request) -> web.Response:
        """User login"""
        try:
            data = await request.json()
            username = data.get('username')
            password = data.get('password')

            # Simple authentication (in production, use proper user management)
            if username == 'admin' and password == 'admin':
                # Create JWT token
                payload = {
                    'user_id': 'admin',
                    'username': username,
                    'role': 'admin',
                    'exp': datetime.utcnow().timestamp() + 3600  # 1 hour
                }

                token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

                return web.json_response({
                    'token': token,
                    'user': {
                        'id': 'admin',
                        'username': username,
                        'role': 'admin'
                    }
                })
            else:
                return web.json_response({'error': 'Invalid credentials'}, status=401)

        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return web.json_response({'error': 'Login failed'}, status=500)

    async def logout(self, request: web.Request) -> web.Response:
        """User logout"""
        try:
            # In a real implementation, you would invalidate the token
            return web.json_response({'message': 'Logged out successfully'})
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return web.json_response({'error': 'Logout failed'}, status=500)

    async def refresh_token(self, request: web.Request) -> web.Response:
        """Refresh JWT token"""
        try:
            user = request['user']

            # Create new token
            payload = {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'exp': datetime.utcnow().timestamp() + 3600
            }

            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            return web.json_response({'token': token})

        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return web.json_response({'error': 'Token refresh failed'}, status=500)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        try:
            return web.json_response({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        except Exception as e:
            return web.json_response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=500)

    async def prometheus_metrics(self, request: web.Request) -> web.Response:
        """Prometheus metrics endpoint"""
        try:
            metrics = self.monitoring_system.get_prometheus_metrics()
            return web.Response(body=metrics, content_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            return web.Response(text=f"Error generating metrics: {e}", status=500)

    async def get_services(self, request: web.Request) -> web.Response:
        """Get all services"""
        try:
            services = await self.autoscaling_engine._get_monitored_services()

            # Add current metrics and status
            for service in services:
                service_id = service['service_id']
                service['current_instances'] = await self.autoscaling_engine._get_current_instances(service_id)
                service['current_metrics'] = asdict(self.autoscaling_engine.get_current_metrics(service_id)) if self.autoscaling_engine.get_current_metrics(service_id) else {}
                service['health_status'] = self.monitoring_system.get_health_status(service_id)

            return web.json_response({'services': services})

        except Exception as e:
            self.logger.error(f"Error getting services: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_service(self, request: web.Request) -> web.Response:
        """Get specific service details"""
        try:
            service_id = request.match_info['service_id']

            # Get service info
            service_info = await self.autoscaling_engine._get_service_info(service_id)
            if not service_info:
                return web.json_response({'error': 'Service not found'}, status=404)

            # Add additional details
            service_info['current_instances'] = await self.autoscaling_engine._get_current_instances(service_id)
            service_info['current_metrics'] = asdict(self.autoscaling_engine.get_current_metrics(service_id)) if self.autoscaling_engine.get_current_metrics(service_id) else {}
            service_info['health_status'] = self.monitoring_system.get_health_status(service_id)
            service_info['scaling_history'] = self.autoscaling_engine.get_scaling_history(service_id, limit=10)

            return web.json_response(service_info)

        except Exception as e:
            self.logger.error(f"Error getting service: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def scale_service(self, request: web.Request) -> web.Response:
        """Scale a service"""
        try:
            service_id = request.match_info['service_id']
            data = await request.json()

            desired_instances = data.get('desired_instances')
            reason = data.get('reason', 'Manual scaling via API')

            if not isinstance(desired_instances, int) or desired_instances < 0:
                return web.json_response({'error': 'Invalid desired_instances value'}, status=400)

            success = await self.autoscaling_engine.force_scale(service_id, desired_instances, reason)

            if success:
                return web.json_response({
                    'message': f'Scaling {service_id} to {desired_instances} instances initiated',
                    'service_id': service_id,
                    'desired_instances': desired_instances,
                    'reason': reason
                })
            else:
                return web.json_response({'error': 'Scaling operation failed'}, status=500)

        except Exception as e:
            self.logger.error(f"Error scaling service: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_service_metrics(self, request: web.Request) -> web.Response:
        """Get service metrics"""
        try:
            service_id = request.match_info['service_id']
            duration = int(request.query.get('duration', 3600))  # Default 1 hour

            # Get metrics from monitoring system
            metrics = {}

            # Get current metrics
            current_metrics = self.autoscaling_engine.get_current_metrics(service_id)
            if current_metrics:
                metrics['current'] = asdict(current_metrics)

            # Get metric aggregates (this would need to be implemented)
            # metrics['aggregates'] = await self.autoscaling_engine.metrics_collector.get_metric_aggregates(service_id, duration_hours=duration//3600)

            return web.json_response({
                'service_id': service_id,
                'duration_seconds': duration,
                'metrics': metrics
            })

        except Exception as e:
            self.logger.error(f"Error getting service metrics: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_service_history(self, request: web.Request) -> web.Response:
        """Get service scaling history"""
        try:
            service_id = request.match_info['service_id']
            limit = int(request.query.get('limit', 50))

            history = self.autoscaling_engine.get_scaling_history(service_id, limit)

            return web.json_response({
                'service_id': service_id,
                'history': history,
                'total': len(history)
            })

        except Exception as e:
            self.logger.error(f"Error getting service history: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_policies(self, request: web.Request) -> web.Response:
        """List scaling policies"""
        try:
            service_id = request.query.get('service_id')
            status = request.query.get('status')

            if status:
                status = PolicyStatus(status)

            policies = self.policy_manager.list_policies(service_id, status)

            return web.json_response({
                'policies': policies,
                'total': len(policies)
            })

        except Exception as e:
            self.logger.error(f"Error listing policies: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def create_policy(self, request: web.Request) -> web.Response:
        """Create scaling policy"""
        try:
            data = await request.json()
            user = request['user']

            policy_id = await self.policy_manager.create_policy(data, user['username'])

            if policy_id:
                return web.json_response({
                    'message': 'Policy created successfully',
                    'policy_id': policy_id
                }, status=201)
            else:
                return web.json_response({'error': 'Failed to create policy'}, status=500)

        except Exception as e:
            self.logger.error(f"Error creating policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_policy(self, request: web.Request) -> web.Response:
        """Get specific policy"""
        try:
            policy_id = request.match_info['policy_id']

            # Get policy details
            policies = self.policy_manager.list_policies()
            policy = next((p for p in policies if p['policy_id'] == policy_id), None)

            if not policy:
                return web.json_response({'error': 'Policy not found'}, status=404)

            # Add history
            policy['history'] = self.policy_manager.get_policy_history(policy_id)

            return web.json_response(policy)

        except Exception as e:
            self.logger.error(f"Error getting policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def update_policy(self, request: web.Request) -> web.Response:
        """Update scaling policy"""
        try:
            policy_id = request.match_info['policy_id']
            data = await request.json()
            user = request['user']

            success = await self.policy_manager.update_policy(policy_id, data, user['username'])

            if success:
                return web.json_response({'message': 'Policy updated successfully'})
            else:
                return web.json_response({'error': 'Failed to update policy'}, status=500)

        except Exception as e:
            self.logger.error(f"Error updating policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_policy(self, request: web.Request) -> web.Response:
        """Delete scaling policy"""
        try:
            policy_id = request.match_info['policy_id']

            success = await self.policy_manager.delete_policy(policy_id)

            if success:
                return web.json_response({'message': 'Policy deleted successfully'})
            else:
                return web.json_response({'error': 'Failed to delete policy'}, status=500)

        except Exception as e:
            self.logger.error(f"Error deleting policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def activate_policy(self, request: web.Request) -> web.Response:
        """Activate scaling policy"""
        try:
            policy_id = request.match_info['policy_id']

            success = await self.policy_manager.activate_policy(policy_id)

            if success:
                return web.json_response({'message': 'Policy activated successfully'})
            else:
                return web.json_response({'error': 'Failed to activate policy'}, status=500)

        except Exception as e:
            self.logger.error(f"Error activating policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def deactivate_policy(self, request: web.Request) -> web.Response:
        """Deactivate scaling policy"""
        try:
            policy_id = request.match_info['policy_id']

            success = await self.policy_manager.deactivate_policy(policy_id)

            if success:
                return web.json_response({'message': 'Policy deactivated successfully'})
            else:
                return web.json_response({'error': 'Failed to deactivate policy'}, status=500)

        except Exception as e:
            self.logger.error(f"Error deactivating policy: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_schedules(self, request: web.Request) -> web.Response:
        """List schedule rules"""
        try:
            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'schedules': [], 'total': 0})

        except Exception as e:
            self.logger.error(f"Error listing schedules: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def create_schedule(self, request: web.Request) -> web.Response:
        """Create schedule rule"""
        try:
            data = await request.json()
            user = request['user']

            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'message': 'Schedule creation not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error creating schedule: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_schedule(self, request: web.Request) -> web.Response:
        """Get specific schedule rule"""
        try:
            schedule_id = request.match_info['schedule_id']

            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'error': 'Schedule management not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error getting schedule: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def update_schedule(self, request: web.Request) -> web.Response:
        """Update schedule rule"""
        try:
            schedule_id = request.match_info['schedule_id']

            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'error': 'Schedule management not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error updating schedule: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_schedule(self, request: web.Request) -> web.Response:
        """Delete schedule rule"""
        try:
            schedule_id = request.match_info['schedule_id']

            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'error': 'Schedule management not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error deleting schedule: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_next_scheduled_executions(self, request: web.Request) -> web.Response:
        """Get next scheduled executions"""
        try:
            service_id = request.query.get('service_id')
            limit = int(request.query.get('limit', 10))

            # This would need to be implemented when ScheduleScalingManager is available
            return web.json_response({'executions': []})

        except Exception as e:
            self.logger.error(f"Error getting next scheduled executions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_events(self, request: web.Request) -> web.Response:
        """List system events"""
        try:
            # This would need to be implemented when EventScalingManager is available
            return web.json_response({'events': [], 'total': 0})

        except Exception as e:
            self.logger.error(f"Error listing events: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def trigger_event(self, request: web.Request) -> web.Response:
        """Trigger manual event"""
        try:
            data = await request.json()

            event_type = data.get('event_type')
            severity = data.get('severity')
            source = data.get('source', 'api')
            message = data.get('message')
            event_data = data.get('data', {})

            if not all([event_type, severity, source, message]):
                return web.json_response({'error': 'Missing required fields'}, status=400)

            # This would need to be implemented when EventScalingManager is available
            return web.json_response({'message': 'Event triggering not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error triggering event: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_event_executions(self, request: web.Request) -> web.Response:
        """Get event execution history"""
        try:
            # This would need to be implemented when EventScalingManager is available
            return web.json_response({'executions': []})

        except Exception as e:
            self.logger.error(f"Error getting event executions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_event_triggers(self, request: web.Request) -> web.Response:
        """List event triggers"""
        try:
            # This would need to be implemented when EventScalingManager is available
            return web.json_response({'triggers': []})

        except Exception as e:
            self.logger.error(f"Error listing event triggers: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def create_event_trigger(self, request: web.Request) -> web.Response:
        """Create event trigger"""
        try:
            data = await request.json()

            # This would need to be implemented when EventScalingManager is available
            return web.json_response({'message': 'Event trigger creation not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error creating event trigger: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_health_status(self, request: web.Request) -> web.Response:
        """Get system health status"""
        try:
            service_id = request.query.get('service_id')

            health_status = self.monitoring_system.get_health_status(service_id)

            return web.json_response(health_status)

        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_alerts(self, request: web.Request) -> web.Response:
        """Get alerts"""
        try:
            severity_str = request.query.get('severity')
            severity = AlertSeverity(severity_str) if severity_str else None

            alerts = self.monitoring_system.get_active_alerts(severity)

            return web.json_response({
                'alerts': alerts,
                'total': len(alerts)
            })

        except Exception as e:
            self.logger.error(f"Error getting alerts: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def acknowledge_alert(self, request: web.Request) -> web.Response:
        """Acknowledge alert"""
        try:
            alert_id = request.match_info['alert_id']
            data = await request.json() or {}
            user = request['user']

            acknowledged_by = data.get('acknowledged_by', user['username'])

            success = await self.monitoring_system.acknowledge_alert(alert_id, acknowledged_by)

            if success:
                return web.json_response({'message': 'Alert acknowledged successfully'})
            else:
                return web.json_response({'error': 'Alert not found'}, status=404)

        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def create_manual_alert(self, request: web.Request) -> web.Response:
        """Create manual alert"""
        try:
            data = await request.json()

            name = data.get('name')
            description = data.get('description')
            severity_str = data.get('severity')
            service_id = data.get('service_id')

            if not all([name, description, severity_str]):
                return web.json_response({'error': 'Missing required fields'}, status=400)

            severity = AlertSeverity(severity_str)

            alert_id = await self.monitoring_system.create_manual_alert(name, description, severity, service_id)

            if alert_id:
                return web.json_response({
                    'message': 'Manual alert created successfully',
                    'alert_id': alert_id
                }, status=201)
            else:
                return web.json_response({'error': 'Failed to create alert'}, status=500)

        except Exception as e:
            self.logger.error(f"Error creating manual alert: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_metrics(self, request: web.Request) -> web.Response:
        """Get metrics data"""
        try:
            # This would provide various metrics data
            return web.json_response({
                'message': 'Metrics endpoint not yet fully implemented',
                'prometheus_url': 'http://localhost:8080/metrics'
            })

        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_cost_report(self, request: web.Request) -> web.Response:
        """Get cost report"""
        try:
            duration_hours = int(request.query.get('duration', 24))

            cost_report = await self.cost_optimizer.get_cost_report(duration_hours)

            return web.json_response(cost_report)

        except Exception as e:
            self.logger.error(f"Error getting cost report: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_service_costs(self, request: web.Request) -> web.Response:
        """Get service-specific costs"""
        try:
            service_id = request.match_info['service_id']
            duration_hours = int(request.query.get('duration', 24))

            # This would need to be implemented in cost optimizer
            return web.json_response({
                'service_id': service_id,
                'duration_hours': duration_hours,
                'hourly_cost': 0,
                'daily_cost': 0,
                'monthly_estimate': 0
            })

        except Exception as e:
            self.logger.error(f"Error getting service costs: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def set_budget_alert(self, request: web.Request) -> web.Response:
        """Set budget alert for service"""
        try:
            service_id = request.match_info['service_id']
            data = await request.json()

            hourly_budget = data.get('hourly_budget')

            if not hourly_budget:
                return web.json_response({'error': 'Missing hourly_budget'}, status=400)

            await self.cost_optimizer.set_budget_alerts(service_id, hourly_budget)

            return web.json_response({'message': 'Budget alert set successfully'})

        except Exception as e:
            self.logger.error(f"Error setting budget alert: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_budget_alerts(self, request: web.Request) -> web.Response:
        """Get budget alerts"""
        try:
            alerts = await self.cost_optimizer.check_budget_alerts()

            return web.json_response({
                'alerts': alerts,
                'total': len(alerts)
            })

        except Exception as e:
            self.logger.error(f"Error getting budget alerts: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_service_predictions(self, request: web.Request) -> web.Response:
        """Get service predictions"""
        try:
            service_id = request.match_info['service_id']

            # This would need to be implemented in predictive scaler
            return web.json_response({
                'service_id': service_id,
                'predictions': [],
                'model_info': self.predictive_scaler.get_model_info(service_id)
            })

        except Exception as e:
            self.logger.error(f"Error getting service predictions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def list_prediction_models(self, request: web.Request) -> web.Response:
        """List prediction models"""
        try:
            # This would need to be implemented in predictive scaler
            return web.json_response({'models': []})

        except Exception as e:
            self.logger.error(f"Error listing prediction models: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_prediction_model(self, request: web.Request) -> web.Response:
        """Get specific prediction model"""
        try:
            service_id = request.match_info['service_id']

            model_info = self.predictive_scaler.get_model_info(service_id)

            if model_info:
                return web.json_response(model_info)
            else:
                return web.json_response({'error': 'Model not found'}, status=404)

        except Exception as e:
            self.logger.error(f"Error getting prediction model: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_config(self, request: web.Request) -> web.Response:
        """Get configuration"""
        try:
            # Return non-sensitive configuration
            config = {
                'api_version': '1.0.0',
                'features': {
                    'auto_scaling': True,
                    'predictive_scaling': True,
                    'cost_optimization': True,
                    'schedule_based_scaling': True,
                    'event_driven_scaling': True,
                    'monitoring': True,
                    'alerting': True
                },
                'controllers': {
                    'kubernetes': True,
                    'docker': True,
                    'cloud': True
                }
            }

            return web.json_response(config)

        except Exception as e:
            self.logger.error(f"Error getting config: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def update_config(self, request: web.Request) -> web.Response:
        """Update configuration"""
        try:
            data = await request.json()
            user = request['user']

            # This would update configuration in a proper way
            return web.json_response({'message': 'Configuration update not yet implemented'}, status=501)

        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def websocket_handler(self, request: web.Request):
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websocket_connections.add(ws)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Handle WebSocket messages
                    try:
                        data = json.loads(msg.data)
                        if data.get('type') == 'subscribe':
                            # Handle subscription to specific events
                            await ws.send_str(json.dumps({
                                'type': 'subscription_ack',
                                'subscription': data.get('subscription')
                            }))
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({'error': 'Invalid JSON'}))

                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f'WebSocket connection closed with exception {ws.exception()}')

        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)

        return ws

    async def _on_shutdown(self, app):
        """Cleanup on application shutdown"""
        try:
            # Close WebSocket connections
            for ws in self.websocket_connections:
                await ws.close()

            self.logger.info("API server shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def broadcast_to_websockets(self, message: dict):
        """Broadcast message to all WebSocket connections"""
        try:
            message_str = json.dumps(message)

            # Create a list of tasks to send messages concurrently
            tasks = []
            for ws in self.websocket_connections.copy():
                if not ws.closed:
                    tasks.append(self._send_to_websocket(ws, message_str))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Error broadcasting to websockets: {e}")

    async def _send_to_websocket(self, ws, message: str):
        """Send message to specific WebSocket"""
        try:
            if not ws.closed:
                await ws.send_str(message)
        except Exception as e:
            # Remove closed connections
            self.websocket_connections.discard(ws)

    async def start_server(self):
        """Start the API server"""
        app = self.create_app()

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, self.api_config['host'], self.api_config['port'])
        await site.start()

        self.logger.info(f"API server started on {self.api_config['host']}:{self.api_config['port']}")

        # Keep server running
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except asyncio.CancelledError:
            await runner.cleanup()

    async def notify_scaling_event(self, service_id: str, old_instances: int, new_instances: int, direction: str):
        """Notify clients of scaling event via WebSocket"""
        message = {
            'type': 'scaling_event',
            'service_id': service_id,
            'old_instances': old_instances,
            'new_instances': new_instances,
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        }

        await self.broadcast_to_websockets(message)

    async def notify_alert(self, alert: dict):
        """Notify clients of new alert via WebSocket"""
        message = {
            'type': 'alert',
            'alert': alert,
            'timestamp': datetime.now().isoformat()
        }

        await self.broadcast_to_websockets(message)