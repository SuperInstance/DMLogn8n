#!/usr/bin/env python3
"""
Performance Dashboard Generator
Creates interactive performance monitoring dashboards
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
from jinja2 import Template

from ..load_test_runner import TestResult
from ..metrics.collector import MetricsCollector
from ..metrics.analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class PerformanceDashboard:
    """Creates interactive performance monitoring dashboards"""

    def __init__(self):
        self.template = self._load_dashboard_template()
        self.chart_configs = {}

    def _load_dashboard_template(self) -> Template:
        """Load the dashboard HTML template"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMLogn8n Performance Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .metric-card { transition: all 0.3s ease; }
        .metric-card:hover { transform: translateY(-2px); }
        .chart-container { height: 350px; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .status-good { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-critical { background-color: #ef4444; }
        .refresh-btn { transition: all 0.3s ease; }
        .refresh-btn:hover { transform: rotate(180deg); }
        .sidebar-link { transition: all 0.2s ease; }
        .sidebar-link:hover { background-color: rgba(59, 130, 246, 0.1); }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body class="bg-gray-100">
    <div class="flex h-screen">
        <!-- Sidebar -->
        <aside class="w-64 bg-white shadow-lg">
            <div class="p-6">
                <h2 class="text-xl font-bold text-gray-800 flex items-center">
                    <i class="fas fa-tachometer-alt mr-2"></i>
                    Performance Dashboard
                </h2>
            </div>
            <nav class="mt-6">
                <a href="#overview" class="sidebar-link block px-6 py-3 text-gray-700 hover:text-blue-600">
                    <i class="fas fa-chart-line mr-3"></i>Overview
                </a>
                <a href="#metrics" class="sidebar-link block px-6 py-3 text-gray-700 hover:text-blue-600">
                    <i class="fas fa-chart-bar mr-3"></i>Live Metrics
                </a>
                <a href="#tests" class="sidebar-link block px-6 py-3 text-gray-700 hover:text-blue-600">
                    <i class="fas fa-vial mr-3"></i>Test Results
                </a>
                <a href="#alerts" class="sidebar-link block px-6 py-3 text-gray-700 hover:text-blue-600">
                    <i class="fas fa-exclamation-triangle mr-3"></i>Alerts
                </a>
                <a href="#trends" class="sidebar-link block px-6 py-3 text-gray-700 hover:text-blue-600">
                    <i class="fas fa-chart-area mr-3"></i>Trends
                </a>
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 overflow-y-auto">
            <!-- Header -->
            <header class="bg-white shadow-sm border-b">
                <div class="px-6 py-4 flex justify-between items-center">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-800">Real-time Performance Monitoring</h1>
                        <p class="text-gray-600">Last updated: <span id="lastUpdate">{{ dashboard_data.last_updated }}</span></p>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button onclick="refreshDashboard()" class="refresh-btn bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">
                            <i class="fas fa-sync-alt mr-2"></i>Refresh
                        </button>
                        <select id="timeRange" onchange="updateTimeRange()" class="border rounded px-3 py-2">
                            <option value="1h">Last Hour</option>
                            <option value="6h">Last 6 Hours</option>
                            <option value="24h" selected>Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                        </select>
                    </div>
                </div>
            </header>

            <!-- Overview Section -->
            <section id="overview" class="p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-gauge-high mr-2"></i>System Overview
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <!-- Health Score -->
                    <div class="metric-card bg-white rounded-lg shadow p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-gray-600 text-sm">Health Score</h3>
                            <span class="status-indicator status-{{ dashboard_data.health_status }}"></span>
                        </div>
                        <div class="text-3xl font-bold text-gray-800">{{ "%.1f"|format(dashboard_data.health_score) }}</div>
                        <div class="text-sm text-gray-600 mt-1">{{ dashboard_data.health_description }}</div>
                        <div class="mt-3 bg-gray-200 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full" style="width: {{ dashboard_data.health_score }}%"></div>
                        </div>
                    </div>

                    <!-- Active Tests -->
                    <div class="metric-card bg-white rounded-lg shadow p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-gray-600 text-sm">Active Tests</h3>
                            <i class="fas fa-flask text-blue-500"></i>
                        </div>
                        <div class="text-3xl font-bold text-gray-800">{{ dashboard_data.active_tests }}</div>
                        <div class="text-sm text-gray-600 mt-1">{{ dashboard_data.running_tests }} running</div>
                        <div class="mt-3 flex space-x-2">
                            {% if dashboard_data.running_tests > 0 %}
                            <span class="pulse inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                            <span class="text-sm text-green-600">Tests Running</span>
                            {% else %}
                            <span class="inline-block w-2 h-2 bg-gray-400 rounded-full"></span>
                            <span class="text-sm text-gray-600">No Active Tests</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Response Time -->
                    <div class="metric-card bg-white rounded-lg shadow p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-gray-600 text-sm">Avg Response Time</h3>
                            <i class="fas fa-clock text-green-500"></i>
                        </div>
                        <div class="text-3xl font-bold text-gray-800">{{ "%.0f"|format(dashboard_data.avg_response_time) }}ms</div>
                        <div class="text-sm text-gray-600 mt-1">{{ dashboard_data.response_time_trend }}</div>
                        <div class="mt-3 text-sm">
                            {% if dashboard_data.response_time_change > 0 %}
                            <span class="text-red-600"><i class="fas fa-arrow-up"></i> +{{ "%.1f"|format(dashboard_data.response_time_change) }}%</span>
                            {% else %}
                            <span class="text-green-600"><i class="fas fa-arrow-down"></i> {{ "%.1f"|format(dashboard_data.response_time_change) }}%</span>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Error Rate -->
                    <div class="metric-card bg-white rounded-lg shadow p-6">
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-gray-600 text-sm">Error Rate</h3>
                            <i class="fas fa-exclamation-triangle text-red-500"></i>
                        </div>
                        <div class="text-3xl font-bold text-gray-800">{{ "%.2f"|format(dashboard_data.error_rate) }}%</div>
                        <div class="text-sm text-gray-600 mt-1">{{ dashboard_data.error_trend }}</div>
                        <div class="mt-3 text-sm">
                            {% if dashboard_data.error_rate_change > 0 %}
                            <span class="text-red-600"><i class="fas fa-arrow-up"></i> +{{ "%.2f"|format(dashboard_data.error_rate_change) }}%</span>
                            {% else %}
                            <span class="text-green-600"><i class="fas fa-arrow-down"></i> {{ "%.2f"|format(dashboard_data.error_rate_change) }}%</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </section>

            <!-- Live Metrics Section -->
            <section id="metrics" class="p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-chart-line mr-2"></i>Live Metrics
                </h2>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Request Rate Chart -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="font-semibold text-gray-800 mb-4">Request Rate</h3>
                        <div id="requestRateChart" class="chart-container"></div>
                    </div>

                    <!-- Response Time Chart -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="font-semibold text-gray-800 mb-4">Response Time</h3>
                        <div id="responseTimeChart" class="chart-container"></div>
                    </div>

                    <!-- Error Rate Chart -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="font-semibold text-gray-800 mb-4">Error Rate</h3>
                        <div id="errorRateChart" class="chart-container"></div>
                    </div>

                    <!-- System Resources Chart -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="font-semibold text-gray-800 mb-4">System Resources</h3>
                        <div id="systemResourcesChart" class="chart-container"></div>
                    </div>
                </div>
            </section>

            <!-- Test Results Section -->
            <section id="tests" class="p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-vial mr-2"></i>Recent Test Results
                </h2>
                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test Name</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scenario</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Response Time</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error Rate</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-200">
                                {% for test in dashboard_data.recent_tests %}
                                <tr>
                                    <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ test.name }}</td>
                                    <td class="px-6 py-4 text-sm text-gray-500">{{ test.scenario }}</td>
                                    <td class="px-6 py-4 text-sm text-gray-500">{{ "%.1f"|format(test.duration) }}s</td>
                                    <td class="px-6 py-4 text-sm">
                                        {% if test.status == 'passed' %}
                                        <span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                                            <i class="fas fa-check-circle"></i> Passed
                                        </span>
                                        {% else %}
                                        <span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                                            <i class="fas fa-times-circle"></i> Failed
                                        </span>
                                        {% endif %}
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-500">{{ "%.0f"|format(test.response_time) }}ms</td>
                                    <td class="px-6 py-4 text-sm text-gray-500">{{ "%.2f"|format(test.error_rate) }}%</td>
                                    <td class="px-6 py-4 text-sm">
                                        <button onclick="viewTestDetails('{{ test.id }}')" class="text-blue-600 hover:text-blue-800">
                                            <i class="fas fa-eye"></i> View
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- Alerts Section -->
            <section id="alerts" class="p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-bell mr-2"></i>Active Alerts
                </h2>
                <div class="space-y-4">
                    {% for alert in dashboard_data.active_alerts %}
                    <div class="bg-white rounded-lg shadow p-4 border-l-4
                        {% if alert.severity == 'critical' %}border-red-500{% endif %}
                        {% if alert.severity == 'high' %}border-orange-500{% endif %}
                        {% if alert.severity == 'medium' %}border-yellow-500{% endif %}
                        {% if alert.severity == 'low' %}border-blue-500{% endif %}">
                        <div class="flex items-start justify-between">
                            <div class="flex items-start">
                                <i class="fas fa-exclamation-triangle mt-1 mr-3
                                    {% if alert.severity == 'critical' %}text-red-500{% endif %}
                                    {% if alert.severity == 'high' %}text-orange-500{% endif %}
                                    {% if alert.severity == 'medium' %}text-yellow-500{% endif %}
                                    {% if alert.severity == 'low' %}text-blue-500{% endif %}"></i>
                                <div>
                                    <h4 class="font-semibold text-gray-800">{{ alert.title }}</h4>
                                    <p class="text-gray-600 text-sm mt-1">{{ alert.description }}</p>
                                    <p class="text-gray-500 text-xs mt-2">{{ alert.timestamp }}</p>
                                </div>
                            </div>
                            <span class="px-2 py-1 text-xs rounded-full
                                {% if alert.severity == 'critical' %}bg-red-100 text-red-800{% endif %}
                                {% if alert.severity == 'high' %}bg-orange-100 text-orange-800{% endif %}
                                {% if alert.severity == 'medium' %}bg-yellow-100 text-yellow-800{% endif %}
                                {% if alert.severity == 'low' %}bg-blue-100 text-blue-800{% endif %}">
                                {{ alert.severity }}
                            </span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
        </main>
    </div>

    <script>
        // Dashboard data
        const dashboardData = {{ dashboard_data|tojson }};

        // Initialize charts
        function initializeCharts() {
            // Request Rate Chart
            const requestRateData = dashboardData.charts.request_rate;
            Plotly.newPlot('requestRateChart', requestRateData.data, requestRateData.layout, {responsive: true});

            // Response Time Chart
            const responseTimeData = dashboardData.charts.response_time;
            Plotly.newPlot('responseTimeChart', responseTimeData.data, responseTimeData.layout, {responsive: true});

            // Error Rate Chart
            const errorRateData = dashboardData.charts.error_rate;
            Plotly.newPlot('errorRateChart', errorRateData.data, errorRateData.layout, {responsive: true});

            // System Resources Chart
            const systemResourcesData = dashboardData.charts.system_resources;
            Plotly.newPlot('systemResourcesChart', systemResourcesData.data, systemResourcesData.layout, {responsive: true});
        }

        // Refresh dashboard
        function refreshDashboard() {
            location.reload();
        }

        // Update time range
        function updateTimeRange() {
            const range = document.getElementById('timeRange').value;
            // In a real implementation, this would fetch new data for the selected time range
            console.log('Updating time range to:', range);
            refreshDashboard();
        }

        // View test details
        function viewTestDetails(testId) {
            // In a real implementation, this would show detailed test information
            console.log('Viewing test details for:', testId);
            alert('Test details would be shown here');
        }

        // Auto-refresh every 30 seconds
        setInterval(() => {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }, 30000);

        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();

            // Smooth scrolling for navigation links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            });
        });
    </script>
</body>
</html>
        """
        return Template(template_content)

    async def generate_dashboard(self, test_results: List[TestResult], output_path: str,
                               metrics_collector: Optional[MetricsCollector] = None) -> str:
        """Generate interactive performance dashboard"""
        logger.info(f"Generating performance dashboard: {output_path}")

        try:
            # Prepare dashboard data
            dashboard_data = await self._prepare_dashboard_data(test_results, metrics_collector)

            # Generate charts
            charts = await self._generate_dashboard_charts(test_results, metrics_collector)
            dashboard_data['charts'] = charts

            # Render HTML
            html_content = self.template.render(dashboard_data=dashboard_data)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Performance dashboard generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate dashboard: {e}")
            raise

    async def _prepare_dashboard_data(self, test_results: List[TestResult],
                                   metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Prepare data for dashboard"""
        if not test_results:
            return {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "health_score": 0,
                "health_status": "critical",
                "health_description": "No data available",
                "active_tests": 0,
                "running_tests": 0,
                "avg_response_time": 0,
                "response_time_trend": "stable",
                "response_time_change": 0,
                "error_rate": 0,
                "error_trend": "stable",
                "error_rate_change": 0,
                "recent_tests": [],
                "active_alerts": []
            }

        # Calculate health score
        health_score = self._calculate_health_score(test_results)
        health_status = self._get_health_status(health_score)

        # Calculate averages
        avg_response_time = sum(r.avg_response_time for r in test_results) / len(test_results)
        avg_error_rate = sum(r.error_rate for r in test_results) / len(test_results)

        # Generate recent tests (latest 10)
        recent_tests = []
        for i, result in enumerate(test_results[-10:]):
            recent_tests.append({
                "id": f"test_{i}",
                "name": result.test_name,
                "scenario": result.scenario,
                "duration": result.duration,
                "status": "passed" if result.error_rate < 5 else "failed",
                "response_time": result.avg_response_time,
                "error_rate": result.error_rate,
                "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        # Generate alerts
        alerts = self._generate_alerts(test_results)

        return {
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "health_score": health_score,
            "health_status": health_status,
            "health_description": self._get_health_description(health_score),
            "active_tests": len(test_results),
            "running_tests": 0,  # Would be determined from actual running tests
            "avg_response_time": avg_response_time,
            "response_time_trend": "stable",  # Would be calculated from historical data
            "response_time_change": 0,
            "error_rate": avg_error_rate,
            "error_trend": "stable",  # Would be calculated from historical data
            "error_rate_change": 0,
            "recent_tests": recent_tests,
            "active_alerts": alerts
        }

    async def _generate_dashboard_charts(self, test_results: List[TestResult],
                                      metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Generate chart configurations for dashboard"""
        charts = {}

        # Generate time series data (mock data - would come from metrics_collector)
        timestamps = [f"T{i:02d}:00" for i in range(24)]

        # Request Rate Chart
        request_rate_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": [100 + (i % 10) * 20 + (i * 5) % 50 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Requests/min",
                    "line": {"color": "#3b82f6", "width": 2}
                }
            ],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Requests/min"},
                "margin": {"t": 20, "r": 20, "b": 40, "l": 50},
                "showlegend": False
            }
        }
        charts["request_rate"] = request_rate_data

        # Response Time Chart
        response_time_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": [200 + (i % 8) * 30 + (i * 3) % 100 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Avg Response Time",
                    "line": {"color": "#10b981", "width": 2}
                },
                {
                    "x": timestamps,
                    "y": [400 + (i % 10) * 40 + (i * 4) % 120 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "95th Percentile",
                    "line": {"color": "#f59e0b", "width": 2}
                }
            ],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Response Time (ms)"},
                "margin": {"t": 20, "r": 20, "b": 40, "l": 50},
                "legend": {"orientation": "h", "y": -0.2}
            }
        }
        charts["response_time"] = response_time_data

        # Error Rate Chart
        error_rate_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": [0.5 + (i % 5) * 0.5 + (i * 0.1) % 2 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Error Rate (%)",
                    "line": {"color": "#ef4444", "width": 2}
                }
            ],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Error Rate (%)"},
                "margin": {"t": 20, "r": 20, "b": 40, "l": 50},
                "showlegend": False
            }
        }
        charts["error_rate"] = error_rate_data

        # System Resources Chart
        system_resources_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": [45 + (i % 15) + (i * 0.5) % 20 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "CPU %",
                    "line": {"color": "#8b5cf6", "width": 2}
                },
                {
                    "x": timestamps,
                    "y": [60 + (i % 12) + (i * 0.4) % 15 for i in range(24)],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Memory %",
                    "line": {"color": "#ec4899", "width": 2}
                }
            ],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Usage (%)"},
                "margin": {"t": 20, "r": 20, "b": 40, "l": 50},
                "legend": {"orientation": "h", "y": -0.2}
            }
        }
        charts["system_resources"] = system_resources_data

        return charts

    def _calculate_health_score(self, test_results: List[TestResult]) -> float:
        """Calculate overall health score"""
        if not test_results:
            return 0

        scores = []
        for result in test_results:
            # Response time score
            response_score = max(0, 100 - (result.avg_response_time / 50))

            # Error rate score
            error_score = max(0, 100 - (result.error_rate * 10))

            # Throughput score
            throughput_score = min(100, result.requests_per_second / 10)

            # Average the scores
            test_score = (response_score + error_score + throughput_score) / 3
            scores.append(test_score)

        return round(sum(scores) / len(scores), 1)

    def _get_health_status(self, health_score: float) -> str:
        """Get health status from score"""
        if health_score >= 90:
            return "good"
        elif health_score >= 70:
            return "warning"
        else:
            return "critical"

    def _get_health_description(self, health_score: float) -> str:
        """Get health description from score"""
        if health_score >= 90:
            return "Excellent performance"
        elif health_score >= 70:
            return "Good performance"
        elif health_score >= 50:
            return "Acceptable performance"
        else:
            return "Poor performance - attention needed"

    def _generate_alerts(self, test_results: List[TestResult]) -> List[Dict[str, Any]]:
        """Generate active alerts from test results"""
        alerts = []

        for result in test_results:
            # High error rate alert
            if result.error_rate > 10:
                alerts.append({
                    "title": f"High Error Rate in {result.test_name}",
                    "description": f"Error rate is {result.error_rate:.2f}%, exceeding the 10% threshold",
                    "severity": "critical",
                    "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
                })
            elif result.error_rate > 5:
                alerts.append({
                    "title": f"Elevated Error Rate in {result.test_name}",
                    "description": f"Error rate is {result.error_rate:.2f}%, exceeding the 5% warning threshold",
                    "severity": "high",
                    "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
                })

            # Slow response time alert
            if result.avg_response_time > 2000:
                alerts.append({
                    "title": f"Slow Response Time in {result.test_name}",
                    "description": f"Average response time is {result.avg_response_time:.0f}ms, exceeding the 2000ms threshold",
                    "severity": "critical",
                    "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
                })
            elif result.avg_response_time > 1000:
                alerts.append({
                    "title": f"Slow Response Time in {result.test_name}",
                    "description": f"Average response time is {result.avg_response_time:.0f}ms, exceeding the 1000ms warning threshold",
                    "severity": "high",
                    "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
                })

            # Low throughput alert
            if result.requests_per_second < 10:
                alerts.append({
                    "title": f"Low Throughput in {result.test_name}",
                    "description": f"Throughput is {result.requests_per_second:.1f} req/s, below the 10 req/s minimum",
                    "severity": "medium",
                    "timestamp": result.end_time.strftime("%Y-%m-%d %H:%M:%S")
                })

        # Sort alerts by severity and limit to top 10
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return alerts[:10]

    async def update_dashboard_data(self, dashboard_path: str, test_results: List[TestResult],
                                  metrics_collector: Optional[MetricsCollector] = None):
        """Update existing dashboard with new data"""
        logger.info(f"Updating dashboard data: {dashboard_path}")

        try:
            # Prepare new data
            dashboard_data = await self._prepare_dashboard_data(test_results, metrics_collector)
            charts = await self._generate_dashboard_charts(test_results, metrics_collector)
            dashboard_data['charts'] = charts

            # Generate updated HTML
            html_content = self.template.render(dashboard_data=dashboard_data)

            # Write to file
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Dashboard updated: {dashboard_path}")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
            raise

# Example usage
async def test_performance_dashboard():
    """Test the performance dashboard"""
    from ..load_test_runner import TestResult

    # Create sample test results
    sample_results = [
        TestResult(
            test_name="API Load Test",
            scenario="agent_simulation",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=60,
            total_requests=1000,
            successful_requests=980,
            failed_requests=20,
            avg_response_time=250,
            min_response_time=50,
            max_response_time=1200,
            p95_response_time=450,
            p99_response_time=800,
            requests_per_second=16.7,
            throughput=2.0,
            error_rate=2.0,
            errors=[],
            metrics={},
            system_metrics={},
            baseline_comparison=None
        )
    ]

    dashboard = PerformanceDashboard()
    await dashboard.generate_dashboard(sample_results, "dashboard.html")
    print("Performance dashboard generated: dashboard.html")

if __name__ == "__main__":
    asyncio.run(test_performance_dashboard())