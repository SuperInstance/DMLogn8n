"""
DMLogn8n Monetization Dashboard - Revenue Analytics and Optimization Tools

This module provides a comprehensive dashboard for monitoring revenue streams,
analyzing monetization performance, and optimization tools.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict
import redis
import aiohttp
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeRange(Enum):
    """Time range options for dashboard"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"

class MetricCategory(Enum):
    """Metric categories"""
    REVENUE = "revenue"
    USERS = "users"
    SUBSCRIPTIONS = "subscriptions"
    VIRTUAL_ECONOMY = "virtual_economy"
    ADVERTISING = "advertising"
    LIFETIME_VALUE = "lifetime_value"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class DashboardMetric:
    """Dashboard metric definition"""
    id: str
    name: str
    category: MetricCategory
    value: float
    previous_value: float
    change_percentage: float
    trend: str  # up, down, stable
    unit: str = ""
    format: str = "number"  # number, currency, percentage
    target: Optional[float] = None
    description: str = ""

@dataclass
class RevenueStream:
    """Revenue stream data for dashboard"""
    id: str
    name: str
    revenue: float
    revenue_percentage: float
    growth_rate: float
    transactions: int
    average_transaction_value: float
    projected_revenue: float
    status: str = "healthy"

@dataclass
class UserSegment:
    """User segment data"""
    name: str
    user_count: int
    percentage: float
    revenue: float
    ltv: float
    churn_rate: float
    growth_rate: float

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""
    id: str
    title: str
    description: str
    category: str
    priority: str  # high, medium, low
    expected_impact: str
    implementation_effort: str
    potential_revenue: float
    confidence_score: float

@dataclass
class DashboardAlert:
    """Dashboard alert"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: MetricCategory
    timestamp: datetime
    acknowledged: bool = False
    action_required: bool = True

# Pydantic models for API
class MetricRequest(BaseModel):
    metric_id: str
    time_range: TimeRange
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class OptimizationRequest(BaseModel):
    category: str
    priority: Optional[str] = None
    limit: int = 10

class MonetizationDashboard:
    """Main monetization dashboard system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.app = FastAPI(
            title="DMLogn8n Monetization Dashboard",
            description="Comprehensive revenue analytics and optimization dashboard",
            version="1.0.0"
        )
        self.templates = Jinja2Templates(directory="templates")
        self.setup_routes()

    async def initialize(self):
        """Initialize dashboard system"""
        logger.info("Initializing DMLogn8n Monetization Dashboard...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize dashboard data
        await self._initialize_dashboard_data()

        logger.info("Monetization Dashboard initialized successfully")

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard page"""
            return await self._render_dashboard_template("dashboard.html")

        @self.app.get("/api/metrics")
        async def get_metrics(
            category: Optional[str] = Query(None),
            time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
        ):
            """Get dashboard metrics"""
            try:
                metrics = await self._get_dashboard_metrics(category, time_range)
                return {"metrics": metrics}
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/revenue-overview")
        async def get_revenue_overview(
            time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
        ):
            """Get revenue overview data"""
            try:
                overview = await self._get_revenue_overview(time_range)
                return overview
            except Exception as e:
                logger.error(f"Error getting revenue overview: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/revenue-streams")
        async def get_revenue_streams(
            time_range: TimeRange = Query(TimeRange.LAST_30_DAYS)
        ):
            """Get revenue streams breakdown"""
            try:
                streams = await self._get_revenue_streams(time_range)
                return {"streams": streams}
            except Exception as e:
                logger.error(f"Error getting revenue streams: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/user-segments")
        async def get_user_segments():
            """Get user segmentation data"""
            try:
                segments = await self._get_user_segments()
                return {"segments": segments}
            except Exception as e:
                logger.error(f"Error getting user segments: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/lighthouse-chart")
        async def get_lighthouse_chart():
            """Get revenue lighthouse chart data"""
            try:
                chart_data = await self._get_lighthouse_chart_data()
                return chart_data
            except Exception as e:
                logger.error(f"Error getting lighthouse chart: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/optimization-recommendations")
        async def get_optimization_recommendations(
            category: Optional[str] = Query(None),
            priority: Optional[str] = Query(None),
            limit: int = Query(10)
        ):
            """Get optimization recommendations"""
            try:
                request = OptimizationRequest(
                    category=category or "all",
                    priority=priority,
                    limit=limit
                )
                recommendations = await self._get_optimization_recommendations(request)
                return {"recommendations": recommendations}
            except Exception as e:
                logger.error(f"Error getting optimization recommendations: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/alerts")
        async def get_alerts(
            severity: Optional[AlertSeverity] = Query(None),
            acknowledged: Optional[bool] = Query(None)
        ):
            """Get dashboard alerts"""
            try:
                alerts = await self._get_alerts(severity, acknowledged)
                return {"alerts": alerts}
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str = Path(...)):
            """Acknowledge an alert"""
            try:
                success = await self._acknowledge_alert(alert_id)
                return {"success": success}
            except Exception as e:
                logger.error(f"Error acknowledging alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/forecast")
        async def get_revenue_forecast(
            days_ahead: int = Query(30)
        ):
            """Get revenue forecast"""
            try:
                forecast = await self._get_revenue_forecast(days_ahead)
                return forecast
            except Exception as e:
                logger.error(f"Error getting revenue forecast: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/ab-tests")
        async def get_ab_test_results():
            """Get A/B test results"""
            try:
                results = await self._get_ab_test_results()
                return {"tests": results}
            except Exception as e:
                logger.error(f"Error getting A/B test results: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _initialize_dashboard_data(self):
        """Initialize dashboard data structures"""
        # Initialize metric definitions
        metric_definitions = {
            "daily_revenue": {
                "name": "Daily Revenue",
                "category": MetricCategory.REVENUE,
                "unit": "$",
                "format": "currency"
            },
            "monthly_revenue": {
                "name": "Monthly Revenue",
                "category": MetricCategory.REVENUE,
                "unit": "$",
                "format": "currency"
            },
            "active_users": {
                "name": "Active Users",
                "category": MetricCategory.USERS,
                "unit": "",
                "format": "number"
            },
            "conversion_rate": {
                "name": "Conversion Rate",
                "category": MetricCategory.USERS,
                "unit": "%",
                "format": "percentage"
            },
            "subscription_revenue": {
                "name": "Subscription Revenue",
                "category": MetricCategory.SUBSCRIPTIONS,
                "unit": "$",
                "format": "currency"
            },
            "churn_rate": {
                "name": "Churn Rate",
                "category": MetricCategory.SUBSCRIPTIONS,
                "unit": "%",
                "format": "percentage"
            },
            "virtual_economy_volume": {
                "name": "Virtual Economy Volume",
                "category": MetricCategory.VIRTUAL_ECONOMY,
                "unit": "$",
                "format": "currency"
            },
            "ad_revenue": {
                "name": "Advertising Revenue",
                "category": MetricCategory.ADVERTISING,
                "unit": "$",
                "format": "currency"
            },
            "average_ltv": {
                "name": "Average LTV",
                "category": MetricCategory.LIFETIME_VALUE,
                "unit": "$",
                "format": "currency"
            }
        }

        await self.redis_client.hset(
            "metric_definitions",
            mapping={k: json.dumps(v) for k, v in metric_definitions.items()}
        )

    async def _render_dashboard_template(self, template_name: str):
        """Render dashboard template"""
        # This would return actual HTML template
        # For now, return a simple HTML structure
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DMLogn8n Monetization Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div id="app">
                <h1 class="text-3xl font-bold text-center py-8">DMLogn8n Monetization Dashboard</h1>
                <div id="metrics-container" class="grid grid-cols-4 gap-4 px-8">
                    <!-- Metrics will be loaded here -->
                </div>
                <div id="charts-container" class="grid grid-cols-2 gap-4 px-8 py-8">
                    <!-- Charts will be loaded here -->
                </div>
            </div>
            <script>
                // Load dashboard data
                fetch('/api/metrics')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Metrics:', data);
                        // Render metrics
                    });

                fetch('/api/revenue-overview')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Revenue Overview:', data);
                        // Render charts
                    });
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    async def _get_dashboard_metrics(self, category: Optional[str],
                                   time_range: TimeRange) -> List[Dict[str, Any]]:
        """Get dashboard metrics"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date, previous_start_date = self._calculate_date_ranges(time_range, end_date)

            # Get metric definitions
            all_metrics = await self.redis_client.hgetall("metric_definitions")
            metrics = []

            for metric_id_bytes, metric_def_bytes in all_metrics.items():
                metric_id = metric_id_bytes.decode()
                metric_def = json.loads(metric_def_bytes.decode())

                # Filter by category if specified
                if category and metric_def['category'] != category:
                    continue

                # Calculate current and previous values
                current_value = await self._calculate_metric_value(metric_id, start_date, end_date)
                previous_value = await self._calculate_metric_value(metric_id, previous_start_date, start_date)

                # Calculate change
                change_percentage = 0
                if previous_value > 0:
                    change_percentage = ((current_value - previous_value) / previous_value) * 100

                # Determine trend
                if change_percentage > 5:
                    trend = "up"
                elif change_percentage < -5:
                    trend = "down"
                else:
                    trend = "stable"

                metric = DashboardMetric(
                    id=metric_id,
                    name=metric_def['name'],
                    category=MetricCategory(metric_def['category']),
                    value=current_value,
                    previous_value=previous_value,
                    change_percentage=change_percentage,
                    trend=trend,
                    unit=metric_def.get('unit', ''),
                    format=metric_def.get('format', 'number'),
                    description=metric_def.get('description', '')
                )

                metrics.append({
                    'id': metric.id,
                    'name': metric.name,
                    'category': metric.category.value,
                    'value': metric.value,
                    'previous_value': metric.previous_value,
                    'change_percentage': metric.change_percentage,
                    'trend': metric.trend,
                    'unit': metric.unit,
                    'format': metric.format,
                    'description': metric.description
                })

            return metrics

        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return []

    def _calculate_date_ranges(self, time_range: TimeRange, end_date: datetime) -> Tuple[datetime, datetime]:
        """Calculate current and previous date ranges"""
        if time_range == TimeRange.TODAY:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            previous_start_date = start_date - timedelta(days=1)
        elif time_range == TimeRange.YESTERDAY:
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            previous_start_date = start_date - timedelta(days=1)
        elif time_range == TimeRange.LAST_7_DAYS:
            start_date = end_date - timedelta(days=7)
            previous_start_date = start_date - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start_date = end_date - timedelta(days=30)
            previous_start_date = start_date - timedelta(days=30)
        elif time_range == TimeRange.THIS_MONTH:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_start_date = (start_date - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date - timedelta(days=30)
            previous_start_date = start_date - timedelta(days=30)

        return start_date, previous_start_date

    async def _calculate_metric_value(self, metric_id: str, start_date: datetime, end_date: datetime) -> float:
        """Calculate metric value for date range"""
        # This would integrate with actual data sources
        # For now, return mock data based on metric type

        if "revenue" in metric_id:
            return np.random.uniform(1000, 50000)
        elif "users" in metric_id:
            return np.random.uniform(100, 5000)
        elif "rate" in metric_id:
            return np.random.uniform(0.01, 0.15)
        elif "ltv" in metric_id:
            return np.random.uniform(50, 500)
        else:
            return np.random.uniform(10, 1000)

    async def _get_revenue_overview(self, time_range: TimeRange) -> Dict[str, Any]:
        """Get revenue overview data"""
        try:
            end_date = datetime.utcnow()
            start_date, previous_start_date = self._calculate_date_ranges(time_range, end_date)

            # Get current period revenue
            current_revenue = await self._calculate_metric_value("daily_revenue", start_date, end_date)
            previous_revenue = await self._calculate_metric_value("daily_revenue", previous_start_date, start_date)

            # Calculate growth
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

            # Get revenue by category
            revenue_by_category = {
                "subscriptions": await self._calculate_metric_value("subscription_revenue", start_date, end_date),
                "virtual_economy": await self._calculate_metric_value("virtual_economy_volume", start_date, end_date),
                "advertising": await self._calculate_metric_value("ad_revenue", start_date, end_date)
            }

            # Generate daily trend data
            daily_trend = []
            current = start_date
            while current <= end_date:
                daily_value = await self._calculate_metric_value("daily_revenue", current, current + timedelta(days=1))
                daily_trend.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "revenue": daily_value
                })
                current += timedelta(days=1)

            return {
                "total_revenue": current_revenue,
                "previous_revenue": previous_revenue,
                "growth_rate": growth_rate,
                "revenue_by_category": revenue_by_category,
                "daily_trend": daily_trend,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error getting revenue overview: {e}")
            return {}

    async def _get_revenue_streams(self, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Get revenue streams breakdown"""
        try:
            # Define revenue streams
            streams_data = [
                {
                    "id": "subscriptions",
                    "name": "Subscriptions",
                    "revenue": np.random.uniform(5000, 20000),
                    "growth_rate": np.random.uniform(-10, 25),
                    "transactions": np.random.randint(100, 500)
                },
                {
                    "id": "virtual_goods",
                    "name": "Virtual Goods",
                    "revenue": np.random.uniform(2000, 10000),
                    "growth_rate": np.random.uniform(-15, 30),
                    "transactions": np.random.randint(200, 1000)
                },
                {
                    "id": "cosmetics",
                    "name": "Cosmetics",
                    "revenue": np.random.uniform(1000, 5000),
                    "growth_rate": np.random.uniform(-20, 40),
                    "transactions": np.random.randint(50, 300)
                },
                {
                    "id": "advertising",
                    "name": "Advertising",
                    "revenue": np.random.uniform(500, 3000),
                    "growth_rate": np.random.uniform(-5, 15),
                    "transactions": np.random.randint(1000, 5000)
                },
                {
                    "id": "premium_features",
                    "name": "Premium Features",
                    "revenue": np.random.uniform(800, 4000),
                    "growth_rate": np.random.uniform(-10, 20),
                    "transactions": np.random.randint(30, 150)
                }
            ]

            # Calculate percentages and additional metrics
            total_revenue = sum(stream["revenue"] for stream in streams_data)

            for stream in streams_data:
                stream["revenue_percentage"] = (stream["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
                stream["average_transaction_value"] = stream["revenue"] / stream["transactions"] if stream["transactions"] > 0 else 0
                stream["projected_revenue"] = stream["revenue"] * (1 + stream["growth_rate"] / 100)

                # Determine status
                if stream["growth_rate"] > 10:
                    stream["status"] = "excellent"
                elif stream["growth_rate"] > 0:
                    stream["status"] = "good"
                elif stream["growth_rate"] > -10:
                    stream["status"] = "stable"
                else:
                    stream["status"] = "declining"

            return streams_data

        except Exception as e:
            logger.error(f"Error getting revenue streams: {e}")
            return []

    async def _get_user_segments(self) -> List[Dict[str, Any]]:
        """Get user segmentation data"""
        try:
            segments_data = [
                {
                    "name": "New Users",
                    "user_count": np.random.randint(500, 2000),
                    "revenue": np.random.uniform(1000, 5000),
                    "ltv": np.random.uniform(20, 50),
                    "churn_rate": np.random.uniform(0.15, 0.30),
                    "growth_rate": np.random.uniform(5, 25)
                },
                {
                    "name": "Active Users",
                    "user_count": np.random.randint(2000, 8000),
                    "revenue": np.random.uniform(10000, 50000),
                    "ltv": np.random.uniform(100, 300),
                    "churn_rate": np.random.uniform(0.05, 0.15),
                    "growth_rate": np.random.uniform(-5, 15)
                },
                {
                    "name": "Premium Users",
                    "user_count": np.random.randint(200, 1000),
                    "revenue": np.random.uniform(15000, 80000),
                    "ltv": np.random.uniform(300, 800),
                    "churn_rate": np.random.uniform(0.02, 0.08),
                    "growth_rate": np.random.uniform(0, 20)
                },
                {
                    "name": "VIP Users",
                    "user_count": np.random.randint(50, 200),
                    "revenue": np.random.uniform(10000, 60000),
                    "ltv": np.random.uniform(500, 1500),
                    "churn_rate": np.random.uniform(0.01, 0.05),
                    "growth_rate": np.random.uniform(-10, 30)
                },
                {
                    "name": "Dormant Users",
                    "user_count": np.random.randint(1000, 3000),
                    "revenue": np.random.uniform(500, 2000),
                    "ltv": np.random.uniform(10, 30),
                    "churn_rate": np.random.uniform(0.40, 0.70),
                    "growth_rate": np.random.uniform(-20, 5)
                }
            ]

            # Calculate percentages
            total_users = sum(segment["user_count"] for segment in segments_data)

            for segment in segments_data:
                segment["percentage"] = (segment["user_count"] / total_users * 100) if total_users > 0 else 0

            return segments_data

        except Exception as e:
            logger.error(f"Error getting user segments: {e}")
            return []

    async def _get_lighthouse_chart_data(self) -> Dict[str, Any]:
        """Get revenue lighthouse chart data"""
        try:
            # Lighthouse chart shows revenue growth over time with different streams
            dates = []
            revenue_data = defaultdict(list)

            # Generate data for last 12 months
            for i in range(12):
                date = datetime.utcnow() - timedelta(days=30 * (11 - i))
                dates.append(date.strftime("%Y-%m"))

                # Generate revenue data for each stream
                streams = ["subscriptions", "virtual_goods", "advertising", "premium_features"]
                for stream in streams:
                    base_value = {
                        "subscriptions": 10000,
                        "virtual_goods": 5000,
                        "advertising": 2000,
                        "premium_features": 3000
                    }[stream]

                    # Add growth and randomness
                    growth_factor = 1 + (i * 0.05) + np.random.uniform(-0.1, 0.1)
                    revenue_data[stream].append(base_value * growth_factor)

            return {
                "dates": dates,
                "revenue_streams": dict(revenue_data),
                "total_revenue": [
                    sum(revenue_data[stream][i] for stream in revenue_data)
                    for i in range(len(dates))
                ]
            }

        except Exception as e:
            logger.error(f"Error getting lighthouse chart data: {e}")
            return {"dates": [], "revenue_streams": {}, "total_revenue": []}

    async def _get_optimization_recommendations(self, request: OptimizationRequest) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        try:
            recommendations = [
                {
                    "id": "price_optimization",
                    "title": "Optimize Subscription Pricing",
                    "description": "A/B testing shows 15% higher conversion at $19.99 price point",
                    "category": "pricing",
                    "priority": "high",
                    "expected_impact": "15% revenue increase",
                    "implementation_effort": "low",
                    "potential_revenue": 7500.0,
                    "confidence_score": 0.85
                },
                {
                    "id": "churn_reduction",
                    "title": "Implement Proactive Churn Reduction",
                    "description": "Target users with 70%+ churn probability with personalized offers",
                    "category": "retention",
                    "priority": "high",
                    "expected_impact": "20% churn reduction",
                    "implementation_effort": "medium",
                    "potential_revenue": 12000.0,
                    "confidence_score": 0.75
                },
                {
                    "id": "virtual_economy_expansion",
                    "title": "Expand Virtual Economy Items",
                    "description": "Add 10 new premium items with estimated $50 average purchase",
                    "category": "virtual_economy",
                    "priority": "medium",
                    "expected_impact": "25% virtual goods revenue increase",
                    "implementation_effort": "medium",
                    "potential_revenue": 5000.0,
                    "confidence_score": 0.70
                },
                {
                    "id": "ad_optimization",
                    "title": "Optimize Ad Placement",
                    "description": "Test new ad positions for 30% higher CPM",
                    "category": "advertising",
                    "priority": "medium",
                    "expected_impact": "30% ad revenue increase",
                    "implementation_effort": "low",
                    "potential_revenue": 3000.0,
                    "confidence_score": 0.80
                },
                {
                    "id": "vip_program",
                    "title": "Launch VIP Program",
                    "description": "Create exclusive VIP tier with premium benefits for $99/month",
                    "category": "subscriptions",
                    "priority": "low",
                    "expected_impact": "5% user base upgrade",
                    "implementation_effort": "high",
                    "potential_revenue": 15000.0,
                    "confidence_score": 0.60
                }
            ]

            # Filter by category if specified
            if request.category != "all":
                recommendations = [r for r in recommendations if r["category"] == request.category]

            # Filter by priority if specified
            if request.priority:
                recommendations = [r for r in recommendations if r["priority"] == request.priority]

            # Sort by potential revenue and confidence
            recommendations.sort(
                key=lambda x: x["potential_revenue"] * x["confidence_score"],
                reverse=True
            )

            return recommendations[:request.limit]

        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return []

    async def _get_alerts(self, severity: Optional[AlertSeverity] = None,
                        acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get dashboard alerts"""
        try:
            alerts = [
                {
                    "id": "revenue_decline",
                    "title": "Revenue Decline Detected",
                    "message": "Daily revenue down 15% compared to last week",
                    "severity": "warning",
                    "category": "revenue",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "acknowledged": False,
                    "action_required": True
                },
                {
                    "id": "high_churn_rate",
                    "title": "High Churn Rate Alert",
                    "message": "Churn rate increased to 12% this month",
                    "severity": "error",
                    "category": "subscriptions",
                    "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                    "acknowledged": False,
                    "action_required": True
                },
                {
                    "id": "payment_failure",
                    "title": "Payment Processing Issues",
                    "message": "5% payment failure rate detected in last hour",
                    "severity": "critical",
                    "category": "revenue",
                    "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                    "acknowledged": False,
                    "action_required": True
                },
                {
                    "id": "new_milestone",
                    "title": "Revenue Milestone Reached",
                    "message": "Monthly revenue exceeded $100,000 for the first time",
                    "severity": "info",
                    "category": "revenue",
                    "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "acknowledged": True,
                    "action_required": False
                }
            ]

            # Filter by severity if specified
            if severity:
                alerts = [a for a in alerts if a["severity"] == severity.value]

            # Filter by acknowledgment status if specified
            if acknowledged is not None:
                alerts = [a for a in alerts if a["acknowledged"] == acknowledged]

            return alerts

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []

    async def _acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            # In real implementation, would update alert status in database
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    async def _get_revenue_forecast(self, days_ahead: int) -> Dict[str, Any]:
        """Get revenue forecast"""
        try:
            # Generate forecast data
            forecast_dates = []
            forecast_values = []
            confidence_intervals = []

            base_revenue = 50000
            current_date = datetime.utcnow()

            for i in range(days_ahead):
                forecast_date = current_date + timedelta(days=i)
                forecast_dates.append(forecast_date.strftime("%Y-%m-%d"))

                # Simple growth model with seasonality
                growth_factor = 1 + (i * 0.002)  # 0.2% daily growth
                seasonality = 1 + 0.1 * np.sin(2 * np.pi * i / 30)  # Monthly seasonality
                random_factor = np.random.uniform(0.9, 1.1)

                forecast_value = base_revenue * growth_factor * seasonality * random_factor
                forecast_values.append(forecast_value)

                # Calculate confidence interval (±20%)
                confidence_lower = forecast_value * 0.8
                confidence_upper = forecast_value * 1.2
                confidence_intervals.append([confidence_lower, confidence_upper])

            total_forecast = sum(forecast_values)

            return {
                "forecast_dates": forecast_dates,
                "forecast_values": forecast_values,
                "confidence_intervals": confidence_intervals,
                "total_forecast": total_forecast,
                "forecast_period_days": days_ahead,
                "model_used": "linear_growth_with_seasonality",
                "confidence_level": 0.8
            }

        except Exception as e:
            logger.error(f"Error getting revenue forecast: {e}")
            return {}

    async def _get_ab_test_results(self) -> List[Dict[str, Any]]:
        """Get A/B test results"""
        try:
            tests = [
                {
                    "id": "pricing_test_2024",
                    "name": "Subscription Pricing Test",
                    "description": "Testing $19.99 vs $24.99 monthly pricing",
                    "status": "completed",
                    "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                    "variants": [
                        {
                            "name": "Control ($19.99)",
                            "conversion_rate": 0.045,
                            "revenue_per_user": 19.99,
                            "sample_size": 2500
                        },
                        {
                            "name": "Variant ($24.99)",
                            "conversion_rate": 0.038,
                            "revenue_per_user": 24.99,
                            "sample_size": 2500
                        }
                    ],
                    "winner": "Control ($19.99)",
                    "statistical_significance": 0.95,
                    "expected_lift": "12% higher revenue per user"
                },
                {
                    "id": "onboarding_flow_test",
                    "name": "Onboarding Flow Optimization",
                    "description": "Testing simplified vs detailed onboarding",
                    "status": "running",
                    "start_date": (datetime.utcnow() - timedelta(days=14)).isoformat(),
                    "end_date": None,
                    "variants": [
                        {
                            "name": "Detailed Onboarding",
                            "completion_rate": 0.72,
                            "time_to_completion": 12.5,
                            "sample_size": 1200
                        },
                        {
                            "name": "Simplified Onboarding",
                            "completion_rate": 0.85,
                            "time_to_completion": 8.2,
                            "sample_size": 1150
                        }
                    ],
                    "winner": None,
                    "statistical_significance": 0.87,
                    "expected_lift": "18% higher completion rate"
                }
            ]

            return tests

        except Exception as e:
            logger.error(f"Error getting A/B test results: {e}")
            return []

    async def generate_dashboard_report(self, format_type: str = "json") -> Dict[str, Any]:
        """Generate comprehensive dashboard report"""
        try:
            # Get all dashboard data
            metrics = await self._get_dashboard_metrics(None, TimeRange.LAST_30_DAYS)
            revenue_overview = await self._get_revenue_overview(TimeRange.LAST_30_DAYS)
            revenue_streams = await self._get_revenue_streams(TimeRange.LAST_30_DAYS)
            user_segments = await self._get_user_segments()
            recommendations = await self._get_optimization_recommendations(OptimizationRequest(category="all", limit=5))
            alerts = await self._get_alerts(acknowledged=False)

            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "period": "last_30_days",
                "metrics": metrics,
                "revenue_overview": revenue_overview,
                "revenue_streams": revenue_streams,
                "user_segments": user_segments,
                "optimization_recommendations": recommendations,
                "active_alerts": alerts,
                "summary": {
                    "total_revenue": revenue_overview.get("total_revenue", 0),
                    "revenue_growth": revenue_overview.get("growth_rate", 0),
                    "active_alerts_count": len(alerts),
                    "recommendations_count": len(recommendations),
                    "key_insights": self._generate_key_insights(metrics, revenue_overview, user_segments)
                }
            }

            if format_type == "pdf":
                # Would generate PDF report
                pass

            return report

        except Exception as e:
            logger.error(f"Error generating dashboard report: {e}")
            return {"error": str(e)}

    def _generate_key_insights(self, metrics: List[Dict], revenue_overview: Dict, segments: List[Dict]) -> List[str]:
        """Generate key insights from dashboard data"""
        insights = []

        # Revenue insights
        if revenue_overview.get("growth_rate", 0) > 10:
            insights.append("Strong revenue growth indicates successful monetization strategies")
        elif revenue_overview.get("growth_rate", 0) < -5:
            insights.append("Revenue decline requires immediate attention and intervention")

        # User segment insights
        premium_users = [s for s in segments if "Premium" in s["name"] or "VIP" in s["name"]]
        if premium_users:
            premium_revenue_percentage = sum(s["revenue"] for s in premium_users) / revenue_overview.get("total_revenue", 1) * 100
            if premium_revenue_percentage > 60:
                insights.append("Premium users drive majority of revenue - focus on retention")
            elif premium_revenue_percentage < 30:
                insights.append("Opportunity to increase premium user conversion")

        # Metric insights
        for metric in metrics:
            if metric["change_percentage"] < -15:
                insights.append(f"Significant decline in {metric['name']} - investigate causes")

        return insights[:5]  # Return top 5 insights

# Main application factory
def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create FastAPI application"""
    if config is None:
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_dashboard'
        }

    dashboard = MonetizationDashboard(config)
    app = dashboard.app

    @app.on_event("startup")
    async def startup_event():
        await dashboard.initialize()

    return app

if __name__ == "__main__":
    import uvicorn

    config = {
        'redis_url': 'redis://localhost:6379',
        'database_url': 'postgresql://localhost/dmlog_dashboard'
    }

    app = create_app(config)

    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )