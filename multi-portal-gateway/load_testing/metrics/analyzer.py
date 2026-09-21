#!/usr/bin/env python3
"""
Performance Analysis and Reporting System
Analyzes collected metrics and generates insights
"""

import asyncio
import json
import statistics
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import logging
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

from .collector import MetricsCollector, RequestMetric, SystemMetric

logger = logging.getLogger(__name__)

@dataclass
class PerformanceInsight:
    """Performance insight or recommendation"""
    insight_type: str  # bottleneck, optimization, warning, info
    severity: str  # low, medium, high, critical
    title: str
    description: str
    affected_components: List[str]
    metrics_evidence: Dict[str, Any]
    recommendation: str
    priority_score: float  # 0-100

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_name: str
    time_period: str
    trend_direction: str  # improving, degrading, stable
    trend_strength: float  # 0-1
    change_rate: float  # change per time unit
    significance: float  # statistical significance
    forecast: List[Tuple[datetime, float]]  # (timestamp, predicted_value)

@dataclass
class AnomalyDetection:
    """Anomaly detection results"""
    timestamp: datetime
    metric_name: str
    observed_value: float
    expected_range: Tuple[float, float]
    anomaly_score: float  # 0-1
    anomaly_type: str  # spike, drop, pattern_change
    confidence: float  # 0-1

class PerformanceAnalyzer:
    """Analyzes performance metrics and generates insights"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.analysis_cache: Dict[str, Any] = {}
        self.baseline_metrics: Dict[str, Any] = {}
        self.performance_thresholds = self._load_default_thresholds()

    def _load_default_thresholds(self) -> Dict[str, Any]:
        """Load default performance thresholds"""
        return {
            "response_time": {
                "excellent": 200,    # ms
                "good": 500,
                "acceptable": 1000,
                "poor": 2000,
                "critical": 5000
            },
            "error_rate": {
                "excellent": 0.1,    # %
                "good": 0.5,
                "acceptable": 2.0,
                "poor": 5.0,
                "critical": 10.0
            },
            "throughput": {
                "excellent": 1000,   # req/s
                "good": 500,
                "acceptable": 200,
                "poor": 100,
                "critical": 50
            },
            "cpu_usage": {
                "excellent": 30,     # %
                "good": 50,
                "acceptable": 70,
                "poor": 85,
                "critical": 95
            },
            "memory_usage": {
                "excellent": 40,     # %
                "good": 60,
                "acceptable": 80,
                "poor": 90,
                "critical": 95
            }
        }

    async def analyze_performance(self, time_window: timedelta = timedelta(minutes=30)) -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        logger.info(f"Starting performance analysis for time window: {time_window}")

        current_time = datetime.now(timezone.utc)
        start_time = current_time - time_window

        # Collect metrics data
        request_metrics = await self.metrics_collector.get_historical_metrics(start_time, current_time)
        system_metrics = await self._get_system_metrics(start_time, current_time)

        # Perform various analyses
        analysis_results = {
            "analysis_timestamp": current_time.isoformat(),
            "time_window": str(time_window),
            "overall_health_score": 0,
            "summary": await self._generate_summary(request_metrics, system_metrics),
            "bottleneck_analysis": await self._analyze_bottlenecks(request_metrics, system_metrics),
            "trend_analysis": await self._analyze_trends(request_metrics, system_metrics),
            "anomaly_detection": await self._detect_anomalies(request_metrics, system_metrics),
            "capacity_analysis": await self._analyze_capacity(request_metrics, system_metrics),
            "performance_insights": [],
            "recommendations": [],
            "endpoint_analysis": await self._analyze_endpoints(request_metrics),
            "resource_utilization": await self._analyze_resource_utilization(system_metrics),
            "user_experience_metrics": await self._analyze_user_experience(request_metrics)
        }

        # Generate insights and recommendations
        insights = await self._generate_insights(analysis_results)
        analysis_results["performance_insights"] = insights

        # Calculate overall health score
        analysis_results["overall_health_score"] = self._calculate_health_score(analysis_results)

        # Cache results
        self.analysis_cache[f"analysis_{current_time.isoformat()}"] = analysis_results

        logger.info("Performance analysis completed")
        return analysis_results

    async def _generate_summary(self, request_metrics: List[Dict], system_metrics: List[Dict]) -> Dict[str, Any]:
        """Generate performance summary"""
        if not request_metrics:
            return {
                "total_requests": 0,
                "error_rate": 0,
                "avg_response_time": 0,
                "throughput": 0,
                "peak_concurrent_users": 0
            }

        # Request metrics
        total_requests = len(request_metrics)
        successful_requests = sum(1 for r in request_metrics if r.get('success', True))
        error_rate = ((total_requests - successful_requests) / total_requests * 100) if total_requests > 0 else 0

        response_times = [float(r['response_time']) for r in request_metrics]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = np.percentile(response_times, 95) if response_times else 0
        p99_response_time = np.percentile(response_times, 99) if response_times else 0

        # Calculate throughput (requests per second)
        if request_metrics:
            time_span = self._calculate_time_span(request_metrics)
            throughput = total_requests / time_span.total_seconds() if time_span.total_seconds() > 0 else 0
        else:
            throughput = 0

        # System metrics
        if system_metrics:
            avg_cpu = statistics.mean([float(s['cpu_percent']) for s in system_metrics])
            avg_memory = statistics.mean([float(s['memory_percent']) for s in system_metrics])
            max_cpu = max([float(s['cpu_percent']) for s in system_metrics])
            max_memory = max([float(s['memory_percent']) for s in system_metrics])
        else:
            avg_cpu = avg_memory = max_cpu = max_memory = 0

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "throughput": throughput,
            "peak_concurrent_users": self._estimate_concurrent_users(request_metrics),
            "system_resources": {
                "avg_cpu_percent": avg_cpu,
                "max_cpu_percent": max_cpu,
                "avg_memory_percent": avg_memory,
                "max_memory_percent": max_memory
            }
        }

    async def _analyze_bottlenecks(self, request_metrics: List[Dict], system_metrics: List[Dict]) -> Dict[str, Any]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        if not request_metrics:
            return {"bottlenecks": bottlenecks, "primary_bottleneck": None}

        # Analyze response time bottlenecks
        slow_endpoints = self._find_slow_endpoints(request_metrics)
        for endpoint, stats in slow_endpoints.items():
            if stats['avg_response_time'] > self.performance_thresholds["response_time"]["poor"]:
                bottlenecks.append({
                    "type": "slow_endpoint",
                    "component": endpoint,
                    "severity": "high" if stats['avg_response_time'] > self.performance_thresholds["response_time"]["critical"] else "medium",
                    "impact": f"Average response time: {stats['avg_response_time']:.2f}ms",
                    "affected_requests": stats['count']
                })

        # Analyze error rate bottlenecks
        error_prone_endpoints = self._find_error_prone_endpoints(request_metrics)
        for endpoint, stats in error_prone_endpoints.items():
            if stats['error_rate'] > self.performance_thresholds["error_rate"]["poor"]:
                bottlenecks.append({
                    "type": "high_error_rate",
                    "component": endpoint,
                    "severity": "high" if stats['error_rate'] > self.performance_thresholds["error_rate"]["critical"] else "medium",
                    "impact": f"Error rate: {stats['error_rate']:.2f}%",
                    "affected_requests": stats['count']
                })

        # Analyze resource bottlenecks
        if system_metrics:
            avg_cpu = statistics.mean([float(s['cpu_percent']) for s in system_metrics])
            avg_memory = statistics.mean([float(s['memory_percent']) for s in system_metrics])

            if avg_cpu > self.performance_thresholds["cpu_usage"]["poor"]:
                bottlenecks.append({
                    "type": "high_cpu_usage",
                    "component": "system",
                    "severity": "high" if avg_cpu > self.performance_thresholds["cpu_usage"]["critical"] else "medium",
                    "impact": f"Average CPU usage: {avg_cpu:.2f}%",
                    "affected_requests": "all"
                })

            if avg_memory > self.performance_thresholds["memory_usage"]["poor"]:
                bottlenecks.append({
                    "type": "high_memory_usage",
                    "component": "system",
                    "severity": "high" if avg_memory > self.performance_thresholds["memory_usage"]["critical"] else "medium",
                    "impact": f"Average memory usage: {avg_memory:.2f}%",
                    "affected_requests": "all"
                })

        # Determine primary bottleneck
        primary_bottleneck = None
        if bottlenecks:
            # Sort by severity and impact
            severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            primary_bottleneck = max(bottlenecks, key=lambda x: (
                severity_weights.get(x["severity"], 0),
                x.get("affected_requests", 0)
            ))

        return {
            "bottlenecks": bottlenecks,
            "primary_bottleneck": primary_bottleneck,
            "total_bottlenecks": len(bottlenecks),
            "bottleneck_score": self._calculate_bottleneck_score(bottlenecks)
        }

    async def _analyze_trends(self, request_metrics: List[Dict], system_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        trends = []

        if not request_metrics:
            return {"trends": trends, "overall_trend": "stable"}

        # Group metrics by time intervals
        time_series_data = self._create_time_series(request_metrics)

        # Analyze response time trend
        response_time_trend = self._calculate_metric_trend(
            time_series_data, "avg_response_time"
        )
        if response_time_trend:
            trends.append(response_time_trend)

        # Analyze error rate trend
        error_rate_trend = self._calculate_metric_trend(
            time_series_data, "error_rate"
        )
        if error_rate_trend:
            trends.append(error_rate_trend)

        # Analyze throughput trend
        throughput_trend = self._calculate_metric_trend(
            time_series_data, "throughput"
        )
        if throughput_trend:
            trends.append(throughput_trend)

        # Analyze system resource trends
        if system_metrics:
            system_series = self._create_system_time_series(system_metrics)

            cpu_trend = self._calculate_metric_trend(
                system_series, "cpu_percent"
            )
            if cpu_trend:
                trends.append(cpu_trend)

            memory_trend = self._calculate_metric_trend(
                system_series, "memory_percent"
            )
            if memory_trend:
                trends.append(memory_trend)

        # Determine overall trend
        overall_trend = self._determine_overall_trend(trends)

        return {
            "trends": trends,
            "overall_trend": overall_trend,
            "trend_summary": self._summarize_trends(trends)
        }

    async def _detect_anomalies(self, request_metrics: List[Dict], system_metrics: List[Dict]) -> Dict[str, Any]:
        """Detect performance anomalies"""
        anomalies = []

        if not request_metrics:
            return {"anomalies": anomalies, "anomaly_count": 0}

        # Detect response time anomalies
        response_time_anomalies = self._detect_response_time_anomalies(request_metrics)
        anomalies.extend(response_time_anomalies)

        # Detect error rate anomalies
        error_rate_anomalies = self._detect_error_rate_anomalies(request_metrics)
        anomalies.extend(error_rate_anomalies)

        # Detect throughput anomalies
        throughput_anomalies = self._detect_throughput_anomalies(request_metrics)
        anomalies.extend(throughput_anomalies)

        # Detect system resource anomalies
        if system_metrics:
            system_anomalies = self._detect_system_anomalies(system_metrics)
            anomalies.extend(system_anomalies)

        # Sort anomalies by severity
        anomalies.sort(key=lambda x: x.anomaly_score, reverse=True)

        return {
            "anomalies": [asdict(anomaly) for anomaly in anomalies],
            "anomaly_count": len(anomalies),
            "critical_anomalies": len([a for a in anomalies if a.anomaly_score > 0.8]),
            "anomaly_summary": self._summarize_anomalies(anomalies)
        }

    async def _analyze_capacity(self, request_metrics: List[Dict], system_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze system capacity and headroom"""
        if not request_metrics or not system_metrics:
            return {
                "current_capacity_utilization": 0,
                "estimated_max_capacity": 0,
                "headroom_percentage": 0,
                "capacity_recommendations": []
            }

        # Calculate current utilization
        max_response_time = max([float(r['response_time']) for r in request_metrics])
        avg_cpu = statistics.mean([float(s['cpu_percent']) for s in system_metrics])
        avg_memory = statistics.mean([float(s['memory_percent']) for s in system_metrics])

        # Calculate throughput
        time_span = self._calculate_time_span(request_metrics)
        current_throughput = len(request_metrics) / time_span.total_seconds() if time_span.total_seconds() > 0 else 0

        # Estimate capacity based on bottlenecks
        response_time_capacity = (self.performance_thresholds["response_time"]["acceptable"] / max_response_time) * current_throughput if max_response_time > 0 else float('inf')
        cpu_capacity = (self.performance_thresholds["cpu_usage"]["acceptable"] / avg_cpu) * current_throughput if avg_cpu > 0 else float('inf')
        memory_capacity = (self.performance_thresholds["memory_usage"]["acceptable"] / avg_memory) * current_throughput if avg_memory > 0 else float('inf')

        # The actual capacity is limited by the most constrained resource
        estimated_max_capacity = min(response_time_capacity, cpu_capacity, memory_capacity)

        # Calculate headroom
        current_capacity_utilization = (current_throughput / estimated_max_capacity * 100) if estimated_max_capacity > 0 else 0
        headroom_percentage = 100 - current_capacity_utilization

        # Generate recommendations
        recommendations = []
        if headroom_percentage < 20:
            recommendations.append({
                "type": "capacity_warning",
                "message": f"System is at {current_capacity_utilization:.1f}% capacity. Consider scaling soon.",
                "priority": "high"
            })
        elif headroom_percentage < 50:
            recommendations.append({
                "type": "capacity_notice",
                "message": f"System is at {current_capacity_utilization:.1f}% capacity. Monitor usage trends.",
                "priority": "medium"
            })

        return {
            "current_capacity_utilization": current_capacity_utilization,
            "estimated_max_capacity": estimated_max_capacity,
            "headroom_percentage": headroom_percentage,
            "current_throughput": current_throughput,
            "capacity_by_resource": {
                "response_time_limited": response_time_capacity,
                "cpu_limited": cpu_capacity,
                "memory_limited": memory_capacity
            },
            "capacity_recommendations": recommendations
        }

    async def _analyze_endpoints(self, request_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze individual endpoint performance"""
        if not request_metrics:
            return {}

        # Group by endpoint
        endpoint_data = defaultdict(list)
        for metric in request_metrics:
            endpoint_data[metric['endpoint']].append(metric)

        endpoint_analysis = {}

        for endpoint, metrics in endpoint_data.items():
            response_times = [float(m['response_time']) for m in metrics]
            successful = sum(1 for m in metrics if m.get('success', True))
            total = len(metrics)

            endpoint_analysis[endpoint] = {
                "total_requests": total,
                "successful_requests": successful,
                "error_rate": ((total - successful) / total * 100) if total > 0 else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "p95_response_time": np.percentile(response_times, 95) if response_times else 0,
                "p99_response_time": np.percentile(response_times, 99) if response_times else 0,
                "throughput": total / self._calculate_time_span(metrics).total_seconds() if metrics else 0,
                "performance_grade": self._grade_performance(response_times, successful, total)
            }

        return endpoint_analysis

    async def _analyze_resource_utilization(self, system_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze system resource utilization patterns"""
        if not system_metrics:
            return {}

        cpu_values = [float(s['cpu_percent']) for s in system_metrics]
        memory_values = [float(s['memory_percent']) for s in system_metrics]

        return {
            "cpu_utilization": {
                "avg": statistics.mean(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "p95": np.percentile(cpu_values, 95),
                "std_dev": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
                "utilization_grade": self._grade_resource_utilization(cpu_values, "cpu")
            },
            "memory_utilization": {
                "avg": statistics.mean(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "p95": np.percentile(memory_values, 95),
                "std_dev": statistics.stdev(memory_values) if len(memory_values) > 1 else 0,
                "utilization_grade": self._grade_resource_utilization(memory_values, "memory")
            },
            "resource_efficiency": self._calculate_resource_efficiency(system_metrics)
        }

    async def _analyze_user_experience(self, request_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze user experience metrics"""
        if not request_metrics:
            return {
                "ux_score": 0,
                "satisfaction_estimate": "unknown",
                "pain_points": []
            }

        # Calculate user experience metrics
        response_times = [float(r['response_time']) for r in request_metrics]
        successful = sum(1 for r in request_metrics if r.get('success', True))
        total = len(request_metrics)

        # User experience score (0-100)
        avg_response_time = statistics.mean(response_times) if response_times else 0
        error_rate = ((total - successful) / total * 100) if total > 0 else 0

        # Calculate UX score based on response time and error rate
        response_time_score = max(0, 100 - (avg_response_time / 50))  # 50ms = perfect score
        error_rate_score = max(0, 100 - (error_rate * 10))  # 10% errors = 0 score
        ux_score = (response_time_score + error_rate_score) / 2

        # Estimate satisfaction
        if ux_score >= 90:
            satisfaction = "excellent"
        elif ux_score >= 75:
            satisfaction = "good"
        elif ux_score >= 60:
            satisfaction = "fair"
        elif ux_score >= 40:
            satisfaction = "poor"
        else:
            satisfaction = "terrible"

        # Identify pain points
        pain_points = []
        if avg_response_time > 1000:
            pain_points.append("Slow response times")
        if error_rate > 5:
            pain_points.append("High error rate")
        if max(response_times) > 5000:
            pain_points.append("Occasional very slow responses")

        return {
            "ux_score": ux_score,
            "satisfaction_estimate": satisfaction,
            "pain_points": pain_points,
            "avg_response_time": avg_response_time,
            "error_rate": error_rate,
            "reliability_score": error_rate_score
        }

    async def _generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance insights and recommendations"""
        insights = []

        # Generate insights from bottleneck analysis
        bottlenecks = analysis_results.get("bottleneck_analysis", {})
        if bottlenecks.get("primary_bottleneck"):
            primary = bottlenecks["primary_bottleneck"]
            insights.append(PerformanceInsight(
                insight_type="bottleneck",
                severity=primary.get("severity", "medium"),
                title=f"Primary Bottleneck: {primary.get('component', 'Unknown')}",
                description=f"The {primary.get('component', 'system')} is causing performance issues: {primary.get('impact', 'Unknown impact')}",
                affected_components=[primary.get("component", "system")],
                metrics_evidence={"bottleneck_type": primary.get("type")},
                recommendation=self._generate_bottleneck_recommendation(primary),
                priority_score=85
            ))

        # Generate insights from trend analysis
        trends = analysis_results.get("trend_analysis", {}).get("trends", [])
        for trend in trends:
            if trend.get("trend_direction") == "degrading" and trend.get("trend_strength", 0) > 0.6:
                insights.append(PerformanceInsight(
                    insight_type="trend",
                    severity="medium",
                    title=f"Degrading Performance: {trend.get('metric_name', 'Unknown')}",
                    description=f"The {trend.get('metric_name', 'metric')} is showing a degrading trend with {trend.get('change_rate', 0):.2f} change per unit time",
                    affected_components=["system"],
                    metrics_evidence={"trend_data": trend},
                    recommendation="Investigate the root cause of performance degradation and implement corrective measures",
                    priority_score=70
                ))

        # Generate insights from anomaly detection
        anomalies = analysis_results.get("anomaly_detection", {}).get("anomalies", [])
        critical_anomalies = [a for a in anomalies if a.get("anomaly_score", 0) > 0.8]
        if critical_anomalies:
            insights.append(PerformanceInsight(
                insight_type="anomaly",
                severity="high",
                title=f"Critical Anomalies Detected: {len(critical_anomalies)} anomalies",
                description=f"Multiple critical performance anomalies detected that require immediate attention",
                affected_components=list(set(a.get("metric_name", "unknown") for a in critical_anomalies)),
                metrics_evidence={"anomalies": critical_anomalies[:5]},  # Top 5 anomalies
                recommendation="Investigate and resolve critical anomalies immediately to prevent service impact",
                priority_score=90
            ))

        # Generate insights from capacity analysis
        capacity = analysis_results.get("capacity_analysis", {})
        headroom = capacity.get("headroom_percentage", 100)
        if headroom < 20:
            insights.append(PerformanceInsight(
                insight_type="capacity",
                severity="high",
                title="Low Capacity Headroom",
                description=f"System is operating at {100 - headroom:.1f}% capacity with only {headroom:.1f}% headroom remaining",
                affected_components=["system"],
                metrics_evidence={"capacity_data": capacity},
                recommendation="Scale system resources immediately to avoid performance degradation",
                priority_score=80
            ))

        # Generate insights from user experience
        ux_analysis = analysis_results.get("user_experience_metrics", {})
        ux_score = ux_analysis.get("ux_score", 100)
        if ux_score < 60:
            insights.append(PerformanceInsight(
                insight_type="user_experience",
                severity="high",
                title="Poor User Experience Detected",
                description=f"User experience score is {ux_score:.1f}/100, indicating performance issues affecting users",
                affected_components=["application"],
                metrics_evidence={"ux_data": ux_analysis},
                recommendation="Prioritize performance improvements to enhance user experience",
                priority_score=75
            ))

        # Sort insights by priority score
        insights.sort(key=lambda x: x.priority_score, reverse=True)

        return [asdict(insight) for insight in insights]

    def _calculate_health_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)"""
        scores = []

        # Response time health
        summary = analysis_results.get("summary", {})
        avg_response_time = summary.get("avg_response_time", 0)
        response_time_score = max(0, 100 - (avg_response_time / 100))  # 100ms = perfect score
        scores.append(response_time_score)

        # Error rate health
        error_rate = summary.get("error_rate", 0)
        error_rate_score = max(0, 100 - (error_rate * 5))  # 20% errors = 0 score
        scores.append(error_rate_score)

        # Resource utilization health
        system_resources = summary.get("system_resources", {})
        avg_cpu = system_resources.get("avg_cpu_percent", 0)
        avg_memory = system_resources.get("avg_memory_percent", 0)
        cpu_score = max(0, 100 - avg_cpu)
        memory_score = max(0, 100 - avg_memory)
        scores.extend([cpu_score, memory_score])

        # Bottleneck penalty
        bottlenecks = analysis_results.get("bottleneck_analysis", {})
        bottleneck_count = bottlenecks.get("total_bottlenecks", 0)
        bottleneck_penalty = min(20, bottleneck_count * 5)  # Max 20 point penalty
        scores.append(max(0, 100 - bottleneck_penalty))

        # Anomaly penalty
        anomalies = analysis_results.get("anomaly_detection", {})
        critical_anomalies = anomalies.get("critical_anomalies", 0)
        anomaly_penalty = min(15, critical_anomalies * 3)  # Max 15 point penalty
        scores.append(max(0, 100 - anomaly_penalty))

        # Calculate weighted average
        if scores:
            health_score = statistics.mean(scores)
        else:
            health_score = 50  # Default to middle score

        return round(health_score, 1)

    # Helper methods
    def _calculate_time_span(self, metrics: List[Dict]) -> timedelta:
        """Calculate time span of metrics"""
        if not metrics:
            return timedelta(0)

        timestamps = [datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')) for m in metrics]
        return max(timestamps) - min(timestamps)

    def _find_slow_endpoints(self, request_metrics: List[Dict]) -> Dict[str, Dict]:
        """Find endpoints with slow response times"""
        endpoint_data = defaultdict(list)
        for metric in request_metrics:
            endpoint_data[metric['endpoint']].append(float(metric['response_time']))

        slow_endpoints = {}
        for endpoint, times in endpoint_data.items():
            if times:
                slow_endpoints[endpoint] = {
                    "avg_response_time": statistics.mean(times),
                    "count": len(times)
                }

        return slow_endpoints

    def _find_error_prone_endpoints(self, request_metrics: List[Dict]) -> Dict[str, Dict]:
        """Find endpoints with high error rates"""
        endpoint_data = defaultdict(lambda: {"total": 0, "errors": 0})
        for metric in request_metrics:
            endpoint_data[metric['endpoint']]["total"] += 1
            if not metric.get('success', True):
                endpoint_data[metric['endpoint']]["errors"] += 1

        error_prone = {}
        for endpoint, data in endpoint_data.items():
            if data["total"] > 0:
                error_rate = (data["errors"] / data["total"]) * 100
                error_prone[endpoint] = {
                    "error_rate": error_rate,
                    "count": data["total"]
                }

        return error_prone

    def _create_time_series(self, request_metrics: List[Dict]) -> List[Dict]:
        """Create time series data from request metrics"""
        # Group by minute intervals
        time_series = defaultdict(lambda: {"response_times": [], "success_count": 0, "total_count": 0})

        for metric in request_metrics:
            timestamp = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            minute_key = timestamp.replace(second=0, microsecond=0)

            time_series[minute_key]["response_times"].append(float(metric['response_time']))
            time_series[minute_key]["total_count"] += 1
            if metric.get('success', True):
                time_series[minute_key]["success_count"] += 1

        # Convert to list format
        series_data = []
        for timestamp, data in time_series.items():
            avg_response_time = statistics.mean(data["response_times"]) if data["response_times"] else 0
            error_rate = ((data["total_count"] - data["success_count"]) / data["total_count"] * 100) if data["total_count"] > 0 else 0

            series_data.append({
                "timestamp": timestamp,
                "avg_response_time": avg_response_time,
                "error_rate": error_rate,
                "throughput": data["total_count"]  # requests per minute
            })

        return sorted(series_data, key=lambda x: x["timestamp"])

    def _calculate_metric_trend(self, time_series_data: List[Dict], metric_name: str) -> Optional[Dict]:
        """Calculate trend for a specific metric"""
        if len(time_series_data) < 3:
            return None

        values = [data[metric_name] for data in time_series_data]
        timestamps = [data["timestamp"] for data in time_series_data]

        # Simple linear regression
        n = len(values)
        x = list(range(n))

        # Calculate slope (trend)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return None

        slope = numerator / denominator

        # Determine trend direction
        if abs(slope) < 0.01:  # Very small slope
            direction = "stable"
        elif slope > 0:
            direction = "degrading" if metric_name in ["avg_response_time", "error_rate"] else "improving"
        else:
            direction = "improving" if metric_name in ["avg_response_time", "error_rate"] else "degrading"

        # Calculate trend strength (normalized slope)
        value_range = max(values) - min(values)
        trend_strength = abs(slope) / value_range if value_range > 0 else 0

        return {
            "metric_name": metric_name,
            "trend_direction": direction,
            "trend_strength": min(1.0, trend_strength * 10),  # Normalize to 0-1
            "change_rate": slope,
            "significance": min(1.0, trend_strength),  # Simplified significance
            "data_points": n
        }

    def _estimate_concurrent_users(self, request_metrics: List[Dict]) -> int:
        """Estimate number of concurrent users"""
        if not request_metrics:
            return 0

        # Group by user_id and session_id if available
        user_sessions = set()
        for metric in request_metrics:
            user_id = metric.get('user_id')
            session_id = metric.get('session_id')
            if user_id and session_id:
                user_sessions.add((user_id, session_id))

        return len(user_sessions) if user_sessions else len(set(m.get('user_id') for m in request_metrics if m.get('user_id')))

    def _grade_performance(self, response_times: List[float], successful: int, total: int) -> str:
        """Grade performance (A-F)"""
        if not response_times:
            return "N/A"

        avg_response = statistics.mean(response_times)
        error_rate = ((total - successful) / total * 100) if total > 0 else 0

        # Grade based on response time and error rate
        if avg_response < 200 and error_rate < 0.5:
            return "A"
        elif avg_response < 500 and error_rate < 2:
            return "B"
        elif avg_response < 1000 and error_rate < 5:
            return "C"
        elif avg_response < 2000 and error_rate < 10:
            return "D"
        else:
            return "F"

    def _grade_resource_utilization(self, values: List[float], resource_type: str) -> str:
        """Grade resource utilization"""
        if not values:
            return "N/A"

        avg_utilization = statistics.mean(values)
        thresholds = self.performance_thresholds[f"{resource_type}_usage"]

        if avg_utilization <= thresholds["excellent"]:
            return "A"
        elif avg_utilization <= thresholds["good"]:
            return "B"
        elif avg_utilization <= thresholds["acceptable"]:
            return "C"
        elif avg_utilization <= thresholds["poor"]:
            return "D"
        else:
            return "F"

    def _generate_bottleneck_recommendation(self, bottleneck: Dict) -> str:
        """Generate recommendation for bottleneck"""
        bottleneck_type = bottleneck.get("type", "unknown")

        recommendations = {
            "slow_endpoint": "Optimize the endpoint implementation, add caching, or consider database query optimization.",
            "high_error_rate": "Investigate error logs, fix bugs, and improve error handling.",
            "high_cpu_usage": "Optimize code, add caching layers, or scale CPU resources.",
            "high_memory_usage": "Check for memory leaks, optimize data structures, or scale memory resources."
        }

        return recommendations.get(bottleneck_type, "Investigate and optimize the identified bottleneck.")

    # Additional helper methods for anomaly detection, capacity analysis, etc.
    def _detect_response_time_anomalies(self, request_metrics: List[Dict]) -> List:
        """Detect response time anomalies using statistical methods"""
        # Placeholder implementation
        return []

    def _detect_error_rate_anomalies(self, request_metrics: List[Dict]) -> List:
        """Detect error rate anomalies"""
        # Placeholder implementation
        return []

    def _detect_throughput_anomalies(self, request_metrics: List[Dict]) -> List:
        """Detect throughput anomalies"""
        # Placeholder implementation
        return []

    def _detect_system_anomalies(self, system_metrics: List[Dict]) -> List:
        """Detect system resource anomalies"""
        # Placeholder implementation
        return []

    def _create_system_time_series(self, system_metrics: List[Dict]) -> List[Dict]:
        """Create time series for system metrics"""
        # Similar to _create_time_series but for system metrics
        return []

    def _determine_overall_trend(self, trends: List[Dict]) -> str:
        """Determine overall system trend"""
        # Analyze trends to determine overall direction
        return "stable"

    def _summarize_trends(self, trends: List[Dict]) -> Dict:
        """Summarize trend analysis"""
        return {"summary": "Trend analysis completed"}

    def _summarize_anomalies(self, anomalies: List) -> Dict:
        """Summarize anomaly detection results"""
        return {"summary": f"Detected {len(anomalies)} anomalies"}

    def _calculate_bottleneck_score(self, bottlenecks: List[Dict]) -> float:
        """Calculate overall bottleneck score"""
        # Score based on number and severity of bottlenecks
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        score = sum(severity_weights.get(b.get("severity", "low"), 1) for b in bottlenecks)
        return min(100, score * 10)

    def _calculate_resource_efficiency(self, system_metrics: List[Dict]) -> Dict:
        """Calculate resource efficiency metrics"""
        return {"efficiency_score": 85.5}  # Placeholder

# Example usage
async def test_performance_analyzer():
    """Test the performance analyzer"""
    # Create a mock metrics collector
    collector = MetricsCollector(":memory:")  # In-memory database for testing

    # Create analyzer
    analyzer = PerformanceAnalyzer(collector)

    # Run analysis
    results = await analyzer.analyze_performance(timedelta(minutes=30))

    print("Performance Analysis Results:")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_performance_analyzer())