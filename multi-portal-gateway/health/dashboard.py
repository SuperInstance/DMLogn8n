"""
Health Monitoring Dashboard

Web-based dashboard for visualizing health monitoring data,
trends, and system status. Provides real-time monitoring interface.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

from .health_service import HealthService, HealthStatus
from .scoring import HealthScorer

class HealthDashboard:
    """Health monitoring web dashboard"""

    def __init__(self, health_service: HealthService, templates_dir: Optional[str] = None):
        self.health_service = health_service
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(title="Health Dashboard")
        self.templates = Jinja2Templates(directory=templates_dir or "templates")
        self.active_connections: List[WebSocket] = []

        # Setup routes
        self._setup_routes()

        # Start background task for real-time updates
        asyncio.create_task(self._broadcast_updates())

    def _setup_routes(self):
        """Setup dashboard routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "DMLogn8n Health Dashboard"
            })

        @self.app.get("/detailed", response_class=HTMLResponse)
        async def detailed_dashboard(request: Request):
            """Detailed dashboard page"""
            return self.templates.TemplateResponse("detailed_dashboard.html", {
                "request": request,
                "title": "Detailed Health Dashboard"
            })

        @self.app.get("/dependencies", response_class=HTMLResponse)
        async def dependencies_dashboard(request: Request):
            """Dependencies dashboard page"""
            return self.templates.TemplateResponse("dependencies.html", {
                "request": request,
                "title": "Service Dependencies"
            })

        @self.app.get("/trends", response_class=HTMLResponse)
        async def trends_dashboard(request: Request):
            """Trends dashboard page"""
            return self.templates.TemplateResponse("trends.html", {
                "request": request,
                "title": "Health Trends"
            })

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

        @self.app.get("/api/dashboard-data")
        async def get_dashboard_data():
            """Get data for dashboard"""
            try:
                # Get comprehensive health data
                report = await self.health_service.run_full_health_check()
                scorer = HealthScorer(self.health_service.config.scoring)

                # Calculate scores
                component_score = scorer.calculate_component_score(report.check_results)
                service_score = scorer.calculate_service_score(report.check_results)
                system_score = scorer.calculate_system_score(report.check_results)
                business_score = scorer.calculate_business_score(report.check_results)

                # Get historical data for charts
                history = await self.health_service.get_health_history(24)  # Last 24 hours

                # Prepare dashboard data
                dashboard_data = {
                    "timestamp": datetime.now().isoformat(),
                    "overall": {
                        "status": report.overall_status.value,
                        "score": report.overall_score,
                        "color": self._get_status_color(report.overall_status)
                    },
                    "scores": {
                        "component": {
                            "score": component_score.score,
                            "status": component_score.status.value,
                            "trend": component_score.trend.value,
                            "color": self._get_status_color(component_score.status)
                        },
                        "service": {
                            "score": service_score.score,
                            "status": service_score.status.value,
                            "trend": service_score.trend.value,
                            "color": self._get_status_color(service_score.status)
                        },
                        "system": {
                            "score": system_score.score,
                            "status": system_score.status.value,
                            "trend": system_score.trend.value,
                            "color": self._get_status_color(system_score.status)
                        },
                        "business": {
                            "score": business_score.score,
                            "status": business_score.status.value,
                            "trend": business_score.trend.value,
                            "color": self._get_status_color(business_score.status)
                        }
                    },
                    "services": [
                        {
                            "id": r.check_id,
                            "name": r.check_name,
                            "status": r.status.value,
                            "score": r.metrics.get("score", 0),
                            "message": r.message,
                            "duration": r.duration_ms,
                            "color": self._get_status_color(r.status)
                        }
                        for r in report.check_results if r.level.value == "service"
                    ],
                    "components": [
                        {
                            "id": r.check_id,
                            "name": r.check_name,
                            "status": r.status.value,
                            "score": r.metrics.get("score", 0),
                            "message": r.message,
                            "color": self._get_status_color(r.status)
                        }
                        for r in report.check_results if r.level.value == "component"
                    ],
                    "issues": {
                        "critical": len([r for r in report.check_results if r.status == HealthStatus.CRITICAL]),
                        "degraded": len([r for r in report.check_results if r.status == HealthStatus.DEGRADED]),
                        "warning": len([r for r in report.check_results if r.status == HealthStatus.WARNING])
                    },
                    "history": history[-24:],  # Last 24 data points
                    "recommendations": report.recommendations[:5],  # Top 5 recommendations
                    "sla_compliance": report.sla_compliance
                }

                return dashboard_data

            except Exception as e:
                self.logger.error(f"Dashboard data endpoint error: {e}")
                return {"error": str(e)}

        @self.app.get("/api/chart-data")
        async def get_chart_data(
            metric: str = "overall_score",
            hours: int = 24
        ):
            """Get chart data for visualization"""
            try:
                history = await self.health_service.get_health_history(hours)

                # Format data for charts
                chart_data = {
                    "labels": [entry["timestamp"] for entry in history],
                    "datasets": [
                        {
                            "label": "Health Score",
                            "data": [entry.get("score", 0) for entry in history],
                            "borderColor": "rgb(75, 192, 192)",
                            "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        }
                    ]
                }

                return chart_data

            except Exception as e:
                self.logger.error(f"Chart data endpoint error: {e}")
                return {"error": str(e)}

    async def _broadcast_updates(self):
        """Broadcast real-time updates to connected WebSocket clients"""
        while True:
            try:
                if self.active_connections:
                    # Get current health data
                    dashboard_data = await self.get_dashboard_data()

                    # Broadcast to all connected clients
                    disconnected = []
                    for connection in self.active_connections:
                        try:
                            await connection.send_text(json.dumps({
                                "type": "health_update",
                                "data": dashboard_data
                            }))
                        except:
                            disconnected.append(connection)

                    # Remove disconnected clients
                    for connection in disconnected:
                        self.active_connections.remove(connection)

                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Broadcast update error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def _get_status_color(self, status: HealthStatus) -> str:
        """Get color for health status"""
        color_map = {
            HealthStatus.HEALTHY: "#28a745",  # Green
            HealthStatus.WARNING: "#ffc107",  # Yellow
            HealthStatus.DEGRADED: "#fd7e14",  # Orange
            HealthStatus.CRITICAL: "#dc3545",  # Red
            HealthStatus.UNKNOWN: "#6c757d"   # Gray
        }
        return color_map.get(status, "#6c757d")

    def create_templates(self):
        """Create HTML templates for the dashboard"""
        templates = {
            "dashboard.html": self._get_dashboard_template(),
            "detailed_dashboard.html": self._get_detailed_dashboard_template(),
            "dependencies.html": self._get_dependencies_template(),
            "trends.html": self._get_trends_template()
        }
        return templates

    def _get_dashboard_template(self) -> str:
        """Get main dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .status-healthy { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-degraded { background-color: #fd7e14; }
        .status-critical { background-color: #dc3545; }
        .status-unknown { background-color: #6c757d; }
    </style>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">DMLogn8n Health Monitor</h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/detailed" class="hover:text-blue-200">Detailed</a>
                <a href="/dependencies" class="hover:text-blue-200">Dependencies</a>
                <a href="/trends" class="hover:text-blue-200">Trends</a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto p-4">
        <!-- Overall Status -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex justify-between items-center">
                <div>
                    <h2 class="text-xl font-semibold mb-2">System Health</h2>
                    <div class="flex items-center space-x-4">
                        <div id="overall-status" class="px-4 py-2 rounded text-white font-bold">
                            Loading...
                        </div>
                        <div id="overall-score" class="text-2xl font-bold">
                            --
                        </div>
                    </div>
                </div>
                <div class="text-right text-gray-500">
                    <div id="last-update">Last update: --</div>
                </div>
            </div>
        </div>

        <!-- Score Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold mb-2">Components</h3>
                <div id="component-score" class="text-2xl font-bold">--</div>
                <div id="component-status" class="text-sm mt-1">--</div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold mb-2">Services</h3>
                <div id="service-score" class="text-2xl font-bold">--</div>
                <div id="service-status" class="text-sm mt-1">--</div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold mb-2">System</h3>
                <div id="system-score" class="text-2xl font-bold">--</div>
                <div id="system-status" class="text-sm mt-1">--</div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="font-semibold mb-2">Business</h3>
                <div id="business-score" class="text-2xl font-bold">--</div>
                <div id="business-status" class="text-sm mt-1">--</div>
            </div>
        </div>

        <!-- Charts and Issues -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Health Trend Chart -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Health Trend (24h)</h3>
                <canvas id="healthChart" width="400" height="200"></canvas>
            </div>

            <!-- Issues Summary -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Current Issues</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-red-600 font-medium">Critical Issues</span>
                        <span id="critical-count" class="text-xl font-bold text-red-600">0</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-orange-600 font-medium">Degraded Services</span>
                        <span id="degraded-count" class="text-xl font-bold text-orange-600">0</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-yellow-600 font-medium">Warnings</span>
                        <span id="warning-count" class="text-xl font-bold text-yellow-600">0</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Service Status -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold mb-4">Service Status</h3>
            <div id="services-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Services will be populated here -->
            </div>
        </div>

        <!-- Recommendations -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold mb-4">Recommendations</h3>
            <ul id="recommendations" class="space-y-2">
                <!-- Recommendations will be populated here -->
            </ul>
        </div>
    </div>

    <script>
        let healthChart;
        let ws;

        function initChart() {
            const ctx = document.getElementById('healthChart').getContext('2d');
            healthChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Health Score',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        function updateDashboard(data) {
            // Update overall status
            const overallStatus = document.getElementById('overall-status');
            const overallScore = document.getElementById('overall-score');
            const lastUpdate = document.getElementById('last-update');

            overallStatus.textContent = data.overall.status.toUpperCase();
            overallStatus.className = `px-4 py-2 rounded text-white font-bold status-${data.overall.status}`;
            overallScore.textContent = `${data.overall.score.toFixed(1)}%`;
            lastUpdate.textContent = `Last update: ${new Date().toLocaleTimeString()}`;

            // Update score cards
            updateScoreCard('component', data.scores.component);
            updateScoreCard('service', data.scores.service);
            updateScoreCard('system', data.scores.system);
            updateScoreCard('business', data.scores.business);

            // Update issues
            document.getElementById('critical-count').textContent = data.issues.critical;
            document.getElementById('degraded-count').textContent = data.issues.degraded;
            document.getElementById('warning-count').textContent = data.issues.warning;

            // Update services
            updateServices(data.services);

            // Update recommendations
            updateRecommendations(data.recommendations);

            // Update chart
            updateChart(data.history);
        }

        function updateScoreCard(type, scoreData) {
            document.getElementById(`${type}-score`).textContent = `${scoreData.score.toFixed(1)}%`;
            document.getElementById(`${type}-status`).textContent =
                `${scoreData.status} (${scoreData.trend})`;
        }

        function updateServices(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = services.map(service => `
                <div class="border rounded-lg p-4 ${service.status === 'healthy' ? 'border-green-200' : 'border-red-200'}">
                    <div class="flex justify-between items-center mb-2">
                        <h4 class="font-medium">${service.name}</h4>
                        <span class="px-2 py-1 rounded text-xs text-white status-${service.status}">
                            ${service.status}
                        </span>
                    </div>
                    <div class="text-sm text-gray-600">
                        <div>Score: ${service.score.toFixed(1)}%</div>
                        <div>${service.message}</div>
                    </div>
                </div>
            `).join('');
        }

        function updateRecommendations(recommendations) {
            const list = document.getElementById('recommendations');
            if (recommendations.length === 0) {
                list.innerHTML = '<li class="text-gray-500">No recommendations at this time</li>';
            } else {
                list.innerHTML = recommendations.map(rec =>
                    `<li class="flex items-start">
                        <span class="text-blue-500 mr-2">•</span>
                        <span>${rec}</span>
                    </li>`
                ).join('');
            }
        }

        function updateChart(history) {
            if (!healthChart) return;

            const labels = history.map(entry => new Date(entry.timestamp).toLocaleTimeString());
            const data = history.map(entry => entry.score || 0);

            healthChart.data.labels = labels.slice(-20); // Last 20 points
            healthChart.data.datasets[0].data = data.slice(-20);
            healthChart.update();
        }

        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'health_update') {
                    updateDashboard(message.data);
                }
            };

            ws.onclose = function() {
                setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
            };
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            connectWebSocket();

            // Load initial data
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error loading dashboard data:', error));
        });
    </script>
</body>
</html>
        """

    def _get_detailed_dashboard_template(self) -> str:
        """Get detailed dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">DMLogn8n Detailed Health Monitor</h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/detailed" class="hover:text-blue-200">Detailed</a>
                <a href="/dependencies" class="hover:text-blue-200">Dependencies</a>
                <a href="/trends" class="hover:text-blue-200">Trends</a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto p-4">
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Detailed Health Information</h2>
            <p class="text-gray-600">Comprehensive health monitoring with detailed metrics and analysis.</p>

            <div class="mt-6">
                <h3 class="text-lg font-medium mb-3">Features</h3>
                <ul class="list-disc list-inside space-y-2 text-gray-700">
                    <li>Real-time health monitoring of all system components</li>
                    <li>Detailed performance metrics and trending</li>
                    <li>Automated healing and recovery procedures</li>
                    <li>SLA compliance tracking and reporting</li>
                    <li>Dependency visualization and impact analysis</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
        """

    def _get_dependencies_template(self) -> str:
        """Get dependencies dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">Service Dependencies</h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/detailed" class="hover:text-blue-200">Detailed</a>
                <a href="/dependencies" class="hover:text-blue-200">Dependencies</a>
                <a href="/trends" class="hover:text-blue-200">Trends</a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto p-4">
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Service Dependency Graph</h2>
            <div id="dependency-graph" class="border rounded-lg" style="height: 600px;">
                <!-- Dependency graph will be rendered here -->
            </div>
        </div>
    </div>
</body>
</html>
        """

    def _get_trends_template(self) -> str:
        """Get trends dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">Health Trends</h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/detailed" class="hover:text-blue-200">Detailed</a>
                <a href="/dependencies" class="hover:text-blue-200">Dependencies</a>
                <a href="/trends" class="hover:text-blue-200">Trends</a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto p-4">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Health Score Trend</h3>
                <canvas id="trendChart"></canvas>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">Component Performance</h3>
                <canvas id="componentChart"></canvas>
            </div>
        </div>
    </div>
</body>
</html>
        """

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app