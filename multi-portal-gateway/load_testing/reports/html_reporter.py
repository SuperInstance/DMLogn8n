#!/usr/bin/env python3
"""
HTML Report Generator
Generates comprehensive HTML performance reports
"""

import asyncio
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
import plotly.utils
from io import BytesIO

from ..load_test_runner import TestResult
from ..metrics.collector import MetricsCollector
from ..metrics.analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class HTMLReporter:
    """Generates HTML performance reports with interactive charts"""

    def __init__(self):
        self.template = self._load_template()
        self.charts_cache = {}

    def _load_template(self) -> Template:
        """Load the HTML report template"""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMLogn8n Load Test Report - {{ report_data.generated_at }}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .metric-card { transition: all 0.3s ease; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .status-good { border-left: 4px solid #10b981; }
        .status-warning { border-left: 4px solid #f59e0b; }
        .status-critical { border-left: 4px solid #ef4444; }
        .chart-container { height: 400px; margin: 20px 0; }
        .insight-card { transition: all 0.3s ease; }
        .insight-card:hover { transform: scale(1.02); }
        .progress-bar { transition: width 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .fade-in { animation: fadeIn 0.5s ease; }
        .table-hover tbody tr:hover { background-color: rgba(0,0,0,0.05); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-chart-line text-2xl"></i>
                    <div>
                        <h1 class="text-2xl font-bold">DMLogn8n Load Test Report</h1>
                        <p class="text-blue-100">Generated on {{ report_data.generated_at }}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="bg-white/20 px-3 py-1 rounded-full text-sm">
                        {{ report_data.test_results|length }} Tests
                    </span>
                    <span class="bg-white/20 px-3 py-1 rounded-full text-sm">
                        {{ "%.1f"|format(report_data.overall_health_score) }} Health Score
                    </span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-6 py-8">
        <!-- Executive Summary -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-chart-pie mr-2"></i>Executive Summary
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="metric-card bg-white rounded-lg shadow p-6 status-{{ report_data.summary.total_requests.status }}">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Total Requests</p>
                            <p class="text-2xl font-bold text-gray-800">{{ "{:,}".format(report_data.summary.total_requests.value) }}</p>
                        </div>
                        <i class="fas fa-exchange-alt text-3xl text-blue-500"></i>
                    </div>
                    <div class="mt-2">
                        <span class="text-sm text-gray-600">{{ report_data.summary.total_requests.description }}</span>
                    </div>
                </div>

                <div class="metric-card bg-white rounded-lg shadow p-6 status-{{ report_data.summary.avg_response_time.status }}">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Avg Response Time</p>
                            <p class="text-2xl font-bold text-gray-800">{{ "%.1f"|format(report_data.summary.avg_response_time.value) }}ms</p>
                        </div>
                        <i class="fas fa-clock text-3xl text-green-500"></i>
                    </div>
                    <div class="mt-2">
                        <span class="text-sm text-gray-600">{{ report_data.summary.avg_response_time.description }}</span>
                    </div>
                </div>

                <div class="metric-card bg-white rounded-lg shadow p-6 status-{{ report_data.summary.error_rate.status }}">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Error Rate</p>
                            <p class="text-2xl font-bold text-gray-800">{{ "%.2f"|format(report_data.summary.error_rate.value) }}%</p>
                        </div>
                        <i class="fas fa-exclamation-triangle text-3xl text-red-500"></i>
                    </div>
                    <div class="mt-2">
                        <span class="text-sm text-gray-600">{{ report_data.summary.error_rate.description }}</span>
                    </div>
                </div>

                <div class="metric-card bg-white rounded-lg shadow p-6 status-{{ report_data.summary.throughput.status }}">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Throughput</p>
                            <p class="text-2xl font-bold text-gray-800">{{ "%.1f"|format(report_data.summary.throughput.value) }} req/s</p>
                        </div>
                        <i class="fas fa-tachometer-alt text-3xl text-purple-500"></i>
                    </div>
                    <div class="mt-2">
                        <span class="text-sm text-gray-600">{{ report_data.summary.throughput.description }}</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Performance Overview Chart -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-chart-bar mr-2"></i>Performance Overview
            </h2>
            <div class="bg-white rounded-lg shadow p-6">
                <div id="performanceOverviewChart" class="chart-container"></div>
            </div>
        </section>

        <!-- Test Results Table -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-table mr-2"></i>Test Results
            </h2>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full table-hover">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test Name</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scenario</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Response</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">95th Percentile</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {% for test in report_data.test_results %}
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ test.test_name }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ test.scenario }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ "%.1f"|format(test.duration) }}s</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ "{:,}".format(test.total_requests) }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm">
                                    {% if test.error_rate < 1 %}
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                        {{ "%.1f"|format((1 - test.error_rate/100) * 100) }}%
                                    </span>
                                    {% elif test.error_rate < 5 %}
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                        {{ "%.1f"|format((1 - test.error_rate/100) * 100) }}%
                                    </span>
                                    {% else %}
                                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                        {{ "%.1f"|format((1 - test.error_rate/100) * 100) }}%
                                    </span>
                                    {% endif %}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ "%.1f"|format(test.avg_response_time) }}ms</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ "%.1f"|format(test.p95_response_time) }}ms</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm">
                                    {% if test.error_rate < 1 and test.avg_response_time < 500 %}
                                    <span class="text-green-600"><i class="fas fa-check-circle"></i> Good</span>
                                    {% elif test.error_rate < 5 and test.avg_response_time < 1000 %}
                                    <span class="text-yellow-600"><i class="fas fa-exclamation-circle"></i> Fair</span>
                                    {% else %}
                                    <span class="text-red-600"><i class="fas fa-times-circle"></i> Poor</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- Response Time Distribution -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-chart-area mr-2"></i>Response Time Distribution
            </h2>
            <div class="bg-white rounded-lg shadow p-6">
                <div id="responseTimeChart" class="chart-container"></div>
            </div>
        </section>

        <!-- Performance Insights -->
        {% if report_data.insights %}
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-lightbulb mr-2"></i>Performance Insights
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {% for insight in report_data.insights %}
                <div class="insight-card bg-white rounded-lg shadow p-6 border-l-4
                    {% if insight.severity == 'critical' %}border-red-500{% endif %}
                    {% if insight.severity == 'high' %}border-orange-500{% endif %}
                    {% if insight.severity == 'medium' %}border-yellow-500{% endif %}
                    {% if insight.severity == 'low' %}border-blue-500{% endif %}">
                    <div class="flex items-start justify-between mb-2">
                        <h3 class="font-semibold text-gray-800">{{ insight.title }}</h3>
                        <span class="px-2 py-1 text-xs rounded-full
                            {% if insight.severity == 'critical' %}bg-red-100 text-red-800{% endif %}
                            {% if insight.severity == 'high' %}bg-orange-100 text-orange-800{% endif %}
                            {% if insight.severity == 'medium' %}bg-yellow-100 text-yellow-800{% endif %}
                            {% if insight.severity == 'low' %}bg-blue-100 text-blue-800{% endif %}">
                            {{ insight.severity }}
                        </span>
                    </div>
                    <p class="text-gray-600 text-sm mb-3">{{ insight.description }}</p>
                    <div class="bg-gray-50 rounded p-2 text-xs text-gray-500">
                        <strong>Recommendation:</strong> {{ insight.recommendation }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
        {% endif %}

        <!-- Resource Utilization -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-server mr-2"></i>Resource Utilization
            </h2>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-semibold text-gray-800 mb-4">CPU Usage</h3>
                    <div id="cpuUsageChart" class="chart-container"></div>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-semibold text-gray-800 mb-4">Memory Usage</h3>
                    <div id="memoryUsageChart" class="chart-container"></div>
                </div>
            </div>
        </section>

        <!-- Detailed Metrics -->
        <section class="mb-8 fade-in">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
                <i class="fas fa-chart-line mr-2"></i>Detailed Metrics
            </h2>
            <div class="bg-white rounded-lg shadow p-6">
                <div id="detailedMetricsChart" class="chart-container"></div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-6">
        <div class="container mx-auto px-6 text-center">
            <p class="text-gray-400">
                DMLogn8n Load Testing Framework - Report generated on {{ report_data.generated_at }}
            </p>
        </div>
    </footer>

    <script>
        // Performance Overview Chart
        const performanceData = {{ report_data.charts.performance_overview|tojson }};
        const performanceLayout = {
            title: 'Test Performance Comparison',
            xaxis: { title: 'Test Name' },
            yaxis: { title: 'Response Time (ms)' },
            showlegend: true,
            height: 400
        };
        Plotly.newPlot('performanceOverviewChart', performanceData.data, performanceData.layout);

        // Response Time Distribution Chart
        const responseTimeData = {{ report_data.charts.response_time_distribution|tojson }};
        Plotly.newPlot('responseTimeChart', responseTimeData.data, responseTimeData.layout);

        // CPU Usage Chart
        const cpuData = {{ report_data.charts.cpu_usage|tojson }};
        Plotly.newPlot('cpuUsageChart', cpuData.data, cpuData.layout);

        // Memory Usage Chart
        const memoryData = {{ report_data.charts.memory_usage|tojson }};
        Plotly.newPlot('memoryUsageChart', memoryData.data, memoryData.layout);

        // Detailed Metrics Chart
        const detailedData = {{ report_data.charts.detailed_metrics|tojson }};
        Plotly.newPlot('detailedMetricsChart', detailedData.data, detailedData.layout);

        // Add interactive features
        document.addEventListener('DOMContentLoaded', function() {
            // Animate metrics on load
            const cards = document.querySelectorAll('.metric-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    card.style.transition = 'all 0.5s ease';
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 50);
                }, index * 100);
            });

            // Add click handlers for table rows
            const tableRows = document.querySelectorAll('tbody tr');
            tableRows.forEach(row => {
                row.addEventListener('click', function() {
                    // Highlight selected row
                    tableRows.forEach(r => r.classList.remove('bg-blue-50'));
                    this.classList.add('bg-blue-50');
                });
            });
        });

        // Print functionality
        function printReport() {
            window.print();
        }

        // Export functionality
        function exportToJSON() {
            const dataStr = JSON.stringify({{ report_data|tojson }}, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            const exportFileDefaultName = 'load_test_report_{{ report_data.generated_at|replace(" ", "_")|replace(":", "") }}.json';

            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
        }
    </script>
</body>
</html>
        """
        return Template(template_content)

    async def generate_report(self, test_results: List[TestResult], output_path: str, metrics_collector: Optional[MetricsCollector] = None):
        """Generate comprehensive HTML report"""
        logger.info(f"Generating HTML report: {output_path}")

        try:
            # Prepare report data
            report_data = await self._prepare_report_data(test_results, metrics_collector)

            # Generate charts
            charts = await self._generate_charts(test_results, metrics_collector)
            report_data['charts'] = charts

            # Render HTML
            html_content = self.template.render(report_data=report_data)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML report generated successfully: {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise

    async def _prepare_report_data(self, test_results: List[TestResult], metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Prepare data for report generation"""
        if not test_results:
            return {
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "overall_health_score": 0,
                "test_results": [],
                "summary": {},
                "insights": []
            }

        # Calculate summary statistics
        total_requests = sum(r.total_requests for r in test_results)
        total_successful = sum(r.successful_requests for r in test_results)
        total_errors = sum(r.failed_requests for r in test_results)

        avg_response_time = sum(r.avg_response_time for r in test_results) / len(test_results)
        avg_error_rate = sum(r.error_rate for r in test_results) / len(test_results)
        avg_throughput = sum(r.requests_per_second for r in test_results) / len(test_results)

        # Determine status for summary metrics
        def get_status(value, metric_type):
            if metric_type == "response_time":
                return "good" if value < 500 else "warning" if value < 1000 else "critical"
            elif metric_type == "error_rate":
                return "good" if value < 1 else "warning" if value < 5 else "critical"
            elif metric_type == "throughput":
                return "good" if value > 100 else "warning" if value > 50 else "critical"
            else:
                return "good"

        # Generate insights
        insights = self._generate_insights(test_results)

        return {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "overall_health_score": self._calculate_health_score(test_results),
            "test_results": [asdict(result) for result in test_results],
            "summary": {
                "total_requests": {
                    "value": total_requests,
                    "description": f"Across {len(test_results)} test scenarios",
                    "status": "good"
                },
                "avg_response_time": {
                    "value": avg_response_time,
                    "description": f"Average across all tests",
                    "status": get_status(avg_response_time, "response_time")
                },
                "error_rate": {
                    "value": avg_error_rate,
                    "description": f"Total errors: {total_errors:,}",
                    "status": get_status(avg_error_rate, "error_rate")
                },
                "throughput": {
                    "value": avg_throughput,
                    "description": f"Average requests per second",
                    "status": get_status(avg_throughput, "throughput")
                }
            },
            "insights": insights
        }

    def _generate_insights(self, test_results: List[TestResult]) -> List[Dict[str, Any]]:
        """Generate performance insights from test results"""
        insights = []

        # Identify slowest tests
        slow_tests = sorted(test_results, key=lambda x: x.avg_response_time, reverse=True)[:3]
        for test in slow_tests:
            if test.avg_response_time > 1000:
                insights.append({
                    "title": f"Slow Response Time: {test.test_name}",
                    "description": f"Test {test.test_name} shows average response time of {test.avg_response_time:.1f}ms, which may impact user experience.",
                    "severity": "high" if test.avg_response_time > 2000 else "medium",
                    "recommendation": "Investigate performance bottlenecks in this test scenario and optimize critical paths."
                })

        # Identify tests with high error rates
        error_tests = [t for t in test_results if t.error_rate > 5]
        for test in error_tests:
            insights.append({
                "title": f"High Error Rate: {test.test_name}",
                "description": f"Test {test.test_name} has an error rate of {test.error_rate:.2f}%, indicating stability issues.",
                "severity": "critical" if test.error_rate > 10 else "high",
                "recommendation": "Review error logs and fix underlying issues causing test failures."
            })

        # Identify throughput issues
        low_throughput_tests = [t for t in test_results if t.requests_per_second < 50]
        for test in low_throughput_tests:
            insights.append({
                "title": f"Low Throughput: {test.test_name}",
                "description": f"Test {test.test_name} achieves only {test.requests_per_second:.1f} requests per second.",
                "severity": "medium",
                "recommendation": "Consider optimizing the test scenario or scaling resources to improve throughput."
            })

        # Add positive insights for good performance
        good_tests = [t for t in test_results if t.error_rate < 1 and t.avg_response_time < 500]
        if good_tests:
            insights.append({
                "title": "Excellent Performance Detected",
                "description": f"{len(good_tests)} test(s) show excellent performance with low error rates and fast response times.",
                "severity": "low",
                "recommendation": "Document successful optimization strategies and apply them to other scenarios."
            })

        return insights[:6]  # Limit to top 6 insights

    def _calculate_health_score(self, test_results: List[TestResult]) -> float:
        """Calculate overall health score"""
        if not test_results:
            return 0

        scores = []
        for result in test_results:
            # Response time score (0-100)
            response_score = max(0, 100 - (result.avg_response_time / 50))  # 50ms = perfect

            # Error rate score (0-100)
            error_score = max(0, 100 - (result.error_rate * 10))  # 10% errors = 0

            # Throughput score (0-100)
            throughput_score = min(100, result.requests_per_second / 10)  # 1000 req/s = perfect

            # Average the scores
            test_score = (response_score + error_score + throughput_score) / 3
            scores.append(test_score)

        return round(sum(scores) / len(scores), 1)

    async def _generate_charts(self, test_results: List[TestResult], metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Generate chart configurations"""
        charts = {}

        # Performance Overview Chart
        performance_data = {
            "data": [
                {
                    "x": [r.test_name for r in test_results],
                    "y": [r.avg_response_time for r in test_results],
                    "type": "bar",
                    "name": "Avg Response Time (ms)",
                    "marker": {"color": "#3b82f6"}
                },
                {
                    "x": [r.test_name for r in test_results],
                    "y": [r.p95_response_time for r in test_results],
                    "type": "bar",
                    "name": "95th Percentile (ms)",
                    "marker": {"color": "#ef4444"}
                }
            ],
            "layout": {
                "title": "Response Time Comparison",
                "xaxis": {"title": "Test Scenario"},
                "yaxis": {"title": "Response Time (ms)"},
                "barmode": "group",
                "height": 400
            }
        }
        charts["performance_overview"] = performance_data

        # Response Time Distribution
        response_time_data = {
            "data": [
                {
                    "x": list(range(len(test_results))),
                    "y": [r.avg_response_time for r in test_results],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Average Response Time",
                    "line": {"color": "#3b82f6"}
                },
                {
                    "x": list(range(len(test_results))),
                    "y": [r.p95_response_time for r in test_results],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "95th Percentile",
                    "line": {"color": "#ef4444"}
                }
            ],
            "layout": {
                "title": "Response Time Trends",
                "xaxis": {"title": "Test Index"},
                "yaxis": {"title": "Response Time (ms)"},
                "height": 400
            }
        }
        charts["response_time_distribution"] = response_time_data

        # Mock system metrics (would come from metrics_collector in real implementation)
        timestamps = [f"Point {i}" for i in range(20)]
        cpu_values = [45 + (i % 10) + (i * 0.5) % 20 for i in range(20)]
        memory_values = [60 + (i % 8) + (i * 0.3) % 15 for i in range(20)]

        cpu_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": cpu_values,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "CPU Usage (%)",
                    "line": {"color": "#10b981"}
                }
            ],
            "layout": {
                "title": "CPU Usage Over Time",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "CPU Usage (%)"},
                "height": 350
            }
        }
        charts["cpu_usage"] = cpu_data

        memory_data = {
            "data": [
                {
                    "x": timestamps,
                    "y": memory_values,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Memory Usage (%)",
                    "line": {"color": "#f59e0b"}
                }
            ],
            "layout": {
                "title": "Memory Usage Over Time",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Memory Usage (%)"},
                "height": 350
            }
        }
        charts["memory_usage"] = memory_data

        # Detailed Metrics Comparison
        detailed_data = {
            "data": [
                {
                    "x": [r.test_name for r in test_results],
                    "y": [r.requests_per_second for r in test_results],
                    "type": "bar",
                    "name": "Requests/sec",
                    "marker": {"color": "#8b5cf6"}
                }
            ],
            "layout": {
                "title": "Throughput Comparison",
                "xaxis": {"title": "Test Scenario"},
                "yaxis": {"title": "Requests per Second"},
                "height": 400
            }
        }
        charts["detailed_metrics"] = detailed_data

        return charts

# Example usage
async def test_html_reporter():
    """Test the HTML reporter"""
    from ..load_test_runner import TestResult

    # Create sample test results
    sample_results = [
        TestResult(
            test_name="Agent Load Test",
            scenario="agent_simulation",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=60,
            total_requests=1000,
            successful_requests=950,
            failed_requests=50,
            avg_response_time=450,
            min_response_time=100,
            max_response_time=2000,
            p95_response_time=800,
            p99_response_time=1200,
            requests_per_second=16.7,
            throughput=1.5,
            error_rate=5.0,
            errors=[],
            metrics={},
            system_metrics={},
            baseline_comparison=None
        ),
        TestResult(
            test_name="User Journey Test",
            scenario="user_journey",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=120,
            total_requests=2000,
            successful_requests=1980,
            failed_requests=20,
            avg_response_time=350,
            min_response_time=50,
            max_response_time=1500,
            p95_response_time=600,
            p99_response_time=900,
            requests_per_second=16.7,
            throughput=2.0,
            error_rate=1.0,
            errors=[],
            metrics={},
            system_metrics={},
            baseline_comparison=None
        )
    ]

    reporter = HTMLReporter()
    await reporter.generate_report(sample_results, "test_report.html")
    print("HTML report generated: test_report.html")

if __name__ == "__main__":
    asyncio.run(test_html_reporter())