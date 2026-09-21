#!/usr/bin/env python3
"""
Dashboard Generator
Dynamic dashboard generation for analytics visualization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import redis

from ..analytics_engine import AnalyticsConfig


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str  # 'metric', 'chart', 'table', 'funnel', 'heatmap'
    title: str
    data_source: str
    query_params: Dict[str, Any]
    visualization_config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: int = 300  # seconds


@dataclass
class Dashboard:
    """Dashboard configuration"""
    dashboard_id: str
    name: str
    description: str
    category: str
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    filters: List[Dict[str, Any]]
    permissions: Dict[str, List[str]]  # role-based access
    auto_refresh: bool = True
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class DashboardData:
    """Dashboard data response"""
    dashboard_id: str
    widget_data: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime
    cache_ttl: int


class DashboardGenerator:
    """Dynamic dashboard generation engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Dashboard templates and configurations
        self.dashboard_templates = {}
        self.widget_cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Initialize database tables
        self._initialize_tables()

        # Initialize default dashboards
        self._initialize_default_dashboards()

    def _setup_logging(self) -> logging.Logger:
        """Setup dashboard generator logging"""
        logger = logging.getLogger("dashboard_generator")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for dashboards"""
        try:
            # Create dashboards table
            create_dashboards_table = """
            CREATE TABLE IF NOT EXISTS dashboards (
                dashboard_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                widgets TEXT,
                layout TEXT,
                filters TEXT,
                permissions TEXT,
                auto_refresh BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create dashboard_cache table
            create_cache_table = """
            CREATE TABLE IF NOT EXISTS dashboard_cache (
                dashboard_id VARCHAR(100) NOT NULL,
                widget_id VARCHAR(100),
                data TEXT,
                generated_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                PRIMARY KEY (dashboard_id, widget_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_dashboards_category ON dashboards(category);",
                "CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON dashboard_cache(expires_at);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_dashboards_table))
                conn.execute(text(create_cache_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Dashboard tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing dashboard tables: {e}")

    def _initialize_default_dashboards(self):
        """Initialize default dashboard configurations"""
        default_dashboards = [
            # Executive Dashboard
            Dashboard(
                dashboard_id="executive_overview",
                name="Executive Overview",
                description="High-level business metrics and KPIs for executives",
                category="executive",
                widgets=[
                    DashboardWidget(
                        widget_id="total_users",
                        widget_type="metric",
                        title="Total Users",
                        data_source="user_metrics",
                        query_params={"metric": "total_users", "period": "30d"},
                        visualization_config={"format": "number", "trend": True},
                        position={"x": 0, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="revenue_chart",
                        widget_type="chart",
                        title="Revenue Trend",
                        data_source="revenue_metrics",
                        query_params={"period": "90d", "granularity": "daily"},
                        visualization_config={
                            "chart_type": "line",
                            "x_axis": "date",
                            "y_axis": "revenue",
                            "trend_line": True
                        },
                        position={"x": 3, "y": 0, "width": 6, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="user_segments",
                        widget_type="chart",
                        title="User Segments",
                        data_source="user_segments",
                        query_params={"model_id": "engagement_based"},
                        visualization_config={
                            "chart_type": "pie",
                            "show_labels": True,
                            "show_legend": True
                        },
                        position={"x": 9, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="conversion_funnel",
                        widget_type="funnel",
                        title="Conversion Funnel",
                        data_source="conversion_metrics",
                        query_params={"funnel_id": "user_onboarding"},
                        visualization_config={
                            "show_percentages": True,
                            "show_dropoff": True
                        },
                        position={"x": 0, "y": 2, "width": 6, "height": 3}
                    ),
                    DashboardWidget(
                        widget_id="churn_risk",
                        widget_type="chart",
                        title="Churn Risk Distribution",
                        data_source="churn_predictions",
                        query_params={"period": "30d"},
                        visualization_config={
                            "chart_type": "bar",
                            "x_axis": "risk_level",
                            "y_axis": "user_count"
                        },
                        position={"x": 6, "y": 2, "width": 6, "height": 3}
                    )
                ],
                layout={"columns": 12, "row_height": 100},
                filters=[
                    {"field": "date_range", "type": "daterange", "default": "30d"},
                    {"field": "user_segment", "type": "multiselect", "source": "user_segments"}
                ],
                permissions={"admin": ["view", "edit"], "executive": ["view"], "manager": ["view"]}
            ),

            # Product Dashboard
            Dashboard(
                dashboard_id="product_analytics",
                name="Product Analytics",
                description="Detailed product usage and feature adoption metrics",
                category="product",
                widgets=[
                    DashboardWidget(
                        widget_id="feature_adoption",
                        widget_type="chart",
                        title="Feature Adoption Rates",
                        data_source="feature_metrics",
                        query_params={"period": "30d"},
                        visualization_config={
                            "chart_type": "horizontal_bar",
                            "show_percentages": True
                        },
                        position={"x": 0, "y": 0, "width": 6, "height": 3}
                    ),
                    DashboardWidget(
                        widget_id="user_journeys",
                        widget_type="table",
                        title="Top User Journeys",
                        data_source="user_journeys",
                        query_params={"limit": 10},
                        visualization_config={
                            "columns": ["journey_name", "user_count", "conversion_rate", "avg_duration"],
                            "sortable": True,
                            "paginated": True
                        },
                        position={"x": 6, "y": 0, "width": 6, "height": 3}
                    ),
                    DashboardWidget(
                        widget_id="engagement_heatmap",
                        widget_type="heatmap",
                        title="User Engagement Heatmap",
                        data_source="engagement_metrics",
                        query_params={"period": "7d", "granularity": "hourly"},
                        visualization_config={
                            "x_axis": "hour_of_day",
                            "y_axis": "day_of_week",
                            "color_scale": "viridis"
                        },
                        position={"x": 0, "y": 3, "width": 12, "height": 4}
                    )
                ],
                layout={"columns": 12, "row_height": 100},
                filters=[
                    {"field": "date_range", "type": "daterange", "default": "7d"},
                    {"field": "feature_category", "type": "select", "source": "feature_categories"}
                ],
                permissions={"admin": ["view", "edit"], "product": ["view", "edit"], "analyst": ["view"]}
            ),

            # Real-time Dashboard
            Dashboard(
                dashboard_id="realtime_monitoring",
                name="Real-time Monitoring",
                description="Live system performance and user activity monitoring",
                category="operations",
                widgets=[
                    DashboardWidget(
                        widget_id="active_users",
                        widget_type="metric",
                        title="Active Users (Now)",
                        data_source="realtime_metrics",
                        query_params={"metric": "active_users"},
                        visualization_config={
                            "format": "number",
                            "realtime": True,
                            "threshold": {"warning": 1000, "critical": 500}
                        },
                        position={"x": 0, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="response_time",
                        widget_type="metric",
                        title="Avg Response Time",
                        data_source="realtime_metrics",
                        query_params={"metric": "response_time"},
                        visualization_config={
                            "format": "duration",
                            "realtime": True,
                            "unit": "ms",
                            "threshold": {"warning": 500, "critical": 1000}
                        },
                        position={"x": 3, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="error_rate",
                        widget_type="metric",
                        title="Error Rate",
                        data_source="realtime_metrics",
                        query_params={"metric": "error_rate"},
                        visualization_config={
                            "format": "percentage",
                            "realtime": True,
                            "threshold": {"warning": 0.05, "critical": 0.1}
                        },
                        position={"x": 6, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="throughput",
                        widget_type="metric",
                        title="Events/Second",
                        data_source="realtime_metrics",
                        query_params={"metric": "throughput"},
                        visualization_config={
                            "format": "number",
                            "realtime": True,
                            "threshold": {"warning": 500, "critical": 200}
                        },
                        position={"x": 9, "y": 0, "width": 3, "height": 2}
                    ),
                    DashboardWidget(
                        widget_id="live_events",
                        widget_type="chart",
                        title="Live Event Stream",
                        data_source="event_stream",
                        query_params={"limit": 100},
                        visualization_config={
                            "chart_type": "stream",
                            "auto_scroll": True,
                            "max_points": 100
                        },
                        position={"x": 0, "y": 2, "width": 12, "height": 4}
                    )
                ],
                layout={"columns": 12, "row_height": 100},
                filters=[
                    {"field": "auto_refresh", "type": "toggle", "default": True}
                ],
                permissions={"admin": ["view", "edit"], "ops": ["view"], "support": ["view"]},
                auto_refresh=True
            )
        ]

        for dashboard in default_dashboards:
            self.add_dashboard(dashboard)

    def add_dashboard(self, dashboard: Dashboard):
        """Add a dashboard configuration"""
        try:
            # Store in database
            query = text("""
                INSERT INTO dashboards (
                    dashboard_id, name, description, category, widgets, layout,
                    filters, permissions, auto_refresh
                ) VALUES (
                    :dashboard_id, :name, :description, :category, :widgets, :layout,
                    :filters, :permissions, :auto_refresh
                )
                ON CONFLICT (dashboard_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    widgets = EXCLUDED.widgets,
                    layout = EXCLUDED.layout,
                    filters = EXCLUDED.filters,
                    permissions = EXCLUDED.permissions,
                    auto_refresh = EXCLUDED.auto_refresh,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'dashboard_id': dashboard.dashboard_id,
                    'name': dashboard.name,
                    'description': dashboard.description,
                    'category': dashboard.category,
                    'widgets': json.dumps([asdict(widget) for widget in dashboard.widgets]),
                    'layout': json.dumps(dashboard.layout),
                    'filters': json.dumps(dashboard.filters),
                    'permissions': json.dumps(dashboard.permissions),
                    'auto_refresh': dashboard.auto_refresh
                })
                conn.commit()

            self.dashboard_templates[dashboard.dashboard_id] = dashboard
            self.logger.info(f"Added dashboard: {dashboard.name}")

        except Exception as e:
            self.logger.error(f"Error adding dashboard: {e}")

    async def generate_dashboard(self, dashboard_id: str,
                                filters: Dict[str, Any] = None,
                                force_refresh: bool = False) -> DashboardData:
        """Generate dashboard with current data"""
        try:
            dashboard = self.dashboard_templates.get(dashboard_id)
            if not dashboard:
                # Load from database
                dashboard = await self._load_dashboard_from_db(dashboard_id)
                if not dashboard:
                    raise ValueError(f"Dashboard not found: {dashboard_id}")

            self.logger.info(f"Generating dashboard: {dashboard.name}")

            # Apply filters
            applied_filters = filters or {}

            # Generate data for each widget
            widget_data = {}
            for widget in dashboard.widgets:
                try:
                    widget_key = f"{dashboard_id}:{widget.widget_id}"

                    # Check cache first
                    if not force_refresh:
                        cached_data = await self._get_cached_widget_data(widget_key)
                        if cached_data:
                            widget_data[widget.widget_id] = cached_data
                            continue

                    # Generate fresh data
                    data = await self._generate_widget_data(widget, applied_filters)
                    widget_data[widget.widget_id] = data

                    # Cache the data
                    await self._cache_widget_data(widget_key, data, widget.refresh_interval)

                except Exception as e:
                    self.logger.error(f"Error generating data for widget {widget.widget_id}: {e}")
                    widget_data[widget.widget_id] = {
                        "error": str(e),
                        "widget_type": widget.widget_type
                    }

            # Create dashboard data response
            dashboard_data = DashboardData(
                dashboard_id=dashboard_id,
                widget_data=widget_data,
                metadata={
                    "dashboard_name": dashboard.name,
                    "description": dashboard.description,
                    "category": dashboard.category,
                    "layout": dashboard.layout,
                    "filters": dashboard.filters,
                    "generated_at": datetime.utcnow().isoformat(),
                    "auto_refresh": dashboard.auto_refresh
                },
                generated_at=datetime.utcnow(),
                cache_ttl=dashboard.widgets[0].refresh_interval if dashboard.widgets else 300
            )

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Error generating dashboard {dashboard_id}: {e}")
            raise

    async def _generate_widget_data(self, widget: DashboardWidget,
                                  filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for a specific widget"""
        try:
            if widget.widget_type == "metric":
                return await self._generate_metric_data(widget, filters)
            elif widget.widget_type == "chart":
                return await self._generate_chart_data(widget, filters)
            elif widget.widget_type == "table":
                return await self._generate_table_data(widget, filters)
            elif widget.widget_type == "funnel":
                return await self._generate_funnel_data(widget, filters)
            elif widget.widget_type == "heatmap":
                return await self._generate_heatmap_data(widget, filters)
            else:
                raise ValueError(f"Unknown widget type: {widget.widget_type}")

        except Exception as e:
            self.logger.error(f"Error generating widget data: {e}")
            raise

    async def _generate_metric_data(self, widget: DashboardWidget,
                                  filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for metric widget"""
        try:
            # Get metric data based on data source
            if widget.data_source == "user_metrics":
                data = await self._get_user_metric(widget.query_params, filters)
            elif widget.data_source == "realtime_metrics":
                data = await self._get_realtime_metric(widget.query_params, filters)
            elif widget.data_source == "revenue_metrics":
                data = await self._get_revenue_metric(widget.query_params, filters)
            else:
                data = {"value": 0, "trend": 0}

            # Apply visualization config
            viz_config = widget.visualization_config
            formatted_value = self._format_metric_value(data.get("value", 0), viz_config)

            result = {
                "value": formatted_value,
                "raw_value": data.get("value", 0),
                "trend": data.get("trend", 0),
                "previous_value": data.get("previous_value"),
                "widget_type": "metric",
                "visualization_config": viz_config
            }

            # Add threshold alerts if configured
            if "threshold" in viz_config:
                threshold = viz_config["threshold"]
                result["alert"] = self._check_threshold(data.get("value", 0), threshold)

            return result

        except Exception as e:
            self.logger.error(f"Error generating metric data: {e}")
            return {"error": str(e), "widget_type": "metric"}

    async def _generate_chart_data(self, widget: DashboardWidget,
                                 filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for chart widget"""
        try:
            # Get chart data based on data source
            if widget.data_source == "revenue_metrics":
                data = await self._get_revenue_chart_data(widget.query_params, filters)
            elif widget.data_source == "user_segments":
                data = await self._get_user_segments_data(widget.query_params, filters)
            elif widget.data_source == "churn_predictions":
                data = await self._get_churn_chart_data(widget.query_params, filters)
            elif widget.data_source == "feature_metrics":
                data = await self._get_feature_chart_data(widget.query_params, filters)
            else:
                data = {"labels": [], "datasets": []}

            viz_config = widget.visualization_config

            result = {
                "labels": data.get("labels", []),
                "datasets": data.get("datasets", []),
                "widget_type": "chart",
                "chart_type": viz_config.get("chart_type", "line"),
                "visualization_config": viz_config
            }

            return result

        except Exception as e:
            self.logger.error(f"Error generating chart data: {e}")
            return {"error": str(e), "widget_type": "chart"}

    async def _generate_table_data(self, widget: DashboardWidget,
                                 filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for table widget"""
        try:
            # Get table data based on data source
            if widget.data_source == "user_journeys":
                data = await self._get_user_journeys_table(widget.query_params, filters)
            else:
                data = {"columns": [], "rows": []}

            viz_config = widget.visualization_config

            result = {
                "columns": data.get("columns", []),
                "rows": data.get("rows", []),
                "total_rows": len(data.get("rows", [])),
                "widget_type": "table",
                "visualization_config": viz_config
            }

            return result

        except Exception as e:
            self.logger.error(f"Error generating table data: {e}")
            return {"error": str(e), "widget_type": "table"}

    async def _generate_funnel_data(self, widget: DashboardWidget,
                                  filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for funnel widget"""
        try:
            # Get funnel data
            if widget.data_source == "conversion_metrics":
                data = await self._get_conversion_funnel_data(widget.query_params, filters)
            else:
                data = {"steps": []}

            viz_config = widget.visualization_config

            result = {
                "steps": data.get("steps", []),
                "widget_type": "funnel",
                "visualization_config": viz_config
            }

            return result

        except Exception as e:
            self.logger.error(f"Error generating funnel data: {e}")
            return {"error": str(e), "widget_type": "funnel"}

    async def _generate_heatmap_data(self, widget: DashboardWidget,
                                   filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for heatmap widget"""
        try:
            # Get heatmap data
            if widget.data_source == "engagement_metrics":
                data = await self._get_engagement_heatmap_data(widget.query_params, filters)
            else:
                data = {"x_labels": [], "y_labels": [], "data": []}

            viz_config = widget.visualization_config

            result = {
                "x_labels": data.get("x_labels", []),
                "y_labels": data.get("y_labels", []),
                "data": data.get("data", []),
                "widget_type": "heatmap",
                "visualization_config": viz_config
            }

            return result

        except Exception as e:
            self.logger.error(f"Error generating heatmap data: {e}")
            return {"error": str(e), "widget_type": "heatmap"}

    # Data source methods

    async def _get_user_metric(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user metric data"""
        try:
            # Mock implementation - would typically query database
            metric = params.get("metric", "total_users")
            period = params.get("period", "30d")

            if metric == "total_users":
                current_value = 15420
                previous_value = 14200
                trend = ((current_value - previous_value) / previous_value) * 100
            else:
                current_value = 8500
                previous_value = 8200
                trend = ((current_value - previous_value) / previous_value) * 100

            return {
                "value": current_value,
                "previous_value": previous_value,
                "trend": trend
            }

        except Exception as e:
            self.logger.error(f"Error getting user metric: {e}")
            return {"value": 0, "trend": 0}

    async def _get_realtime_metric(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time metric from Redis"""
        try:
            metric = params.get("metric", "active_users")

            # Get from Redis cache
            cache_key = f"analytics:realtime:{metric}"
            cached_value = await self.redis_client.get(cache_key)

            if cached_value:
                value = float(cached_value)
            else:
                # Mock data if not in cache
                if metric == "active_users":
                    value = 1247
                elif metric == "response_time":
                    value = 145
                elif metric == "error_rate":
                    value = 0.008
                elif metric == "throughput":
                    value = 1250
                else:
                    value = 0

            return {"value": value}

        except Exception as e:
            self.logger.error(f"Error getting realtime metric: {e}")
            return {"value": 0}

    async def _get_revenue_metric(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get revenue metric data"""
        # Mock implementation
        return {
            "value": 45230.50,
            "previous_value": 42100.00,
            "trend": 7.4
        }

    async def _get_revenue_chart_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get revenue chart data"""
        try:
            # Mock time series data
            import random
            dates = pd.date_range(end=datetime.utcnow(), periods=30, freq='D')
            values = [random.uniform(1000, 2000) for _ in range(30)]

            return {
                "labels": [date.strftime('%Y-%m-%d') for date in dates],
                "datasets": [{
                    "label": "Revenue",
                    "data": values,
                    "borderColor": "#007bff",
                    "backgroundColor": "rgba(0, 123, 255, 0.1)"
                }]
            }

        except Exception as e:
            self.logger.error(f"Error getting revenue chart data: {e}")
            return {"labels": [], "datasets": []}

    async def _get_user_segments_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user segments data for pie chart"""
        try:
            # Mock segment data
            segments = [
                {"name": "Highly Engaged", "value": 3200, "color": "#28a745"},
                {"name": "Moderately Engaged", "value": 5800, "color": "#ffc107"},
                {"name": "Low Engagement", "value": 4200, "color": "#dc3545"},
                {"name": "New Users", "value": 2220, "color": "#17a2b8"}
            ]

            return {
                "labels": [s["name"] for s in segments],
                "datasets": [{
                    "data": [s["value"] for s in segments],
                    "backgroundColor": [s["color"] for s in segments]
                }]
            }

        except Exception as e:
            self.logger.error(f"Error getting user segments data: {e}")
            return {"labels": [], "datasets": []}

    async def _get_churn_chart_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get churn risk distribution data"""
        try:
            # Mock churn data
            risk_levels = ["Low", "Medium", "High", "Critical"]
            user_counts = [8500, 3200, 1200, 300]

            return {
                "labels": risk_levels,
                "datasets": [{
                    "label": "Users at Risk",
                    "data": user_counts,
                    "backgroundColor": ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]
                }]
            }

        except Exception as e:
            self.logger.error(f"Error getting churn chart data: {e}")
            return {"labels": [], "datasets": []}

    async def _get_feature_chart_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get feature adoption data"""
        try:
            # Mock feature data
            features = [
                {"name": "Character Creation", "adoption": 0.85},
                {"name": "Dialogue System", "adoption": 0.92},
                {"name": "Combat System", "adoption": 0.67},
                {"name": "Social Features", "adoption": 0.43},
                {"name": "Marketplace", "adoption": 0.28}
            ]

            return {
                "labels": [f["name"] for f in features],
                "datasets": [{
                    "label": "Adoption Rate",
                    "data": [f["adoption"] * 100 for f in features],
                    "backgroundColor": "#007bff"
                }]
            }

        except Exception as e:
            self.logger.error(f"Error getting feature chart data: {e}")
            return {"labels": [], "datasets": []}

    async def _get_user_journeys_table(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user journeys table data"""
        try:
            # Mock table data
            rows = [
                {"journey_name": "Quick Onboarding", "user_count": 5420, "conversion_rate": 0.78, "avg_duration": 15},
                {"journey_name": "Deep Exploration", "user_count": 3210, "conversion_rate": 0.65, "avg_duration": 45},
                {"journey_name": "Social Integration", "user_count": 2890, "conversion_rate": 0.82, "avg_duration": 25},
                {"journey_name": "Power User Path", "user_count": 1560, "conversion_rate": 0.91, "avg_duration": 60}
            ]

            return {
                "columns": ["journey_name", "user_count", "conversion_rate", "avg_duration"],
                "rows": rows
            }

        except Exception as e:
            self.logger.error(f"Error getting user journeys table: {e}")
            return {"columns": [], "rows": []}

    async def _get_conversion_funnel_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversion funnel data"""
        try:
            # Mock funnel data
            steps = [
                {"name": "Visit", "users": 10000, "conversion_rate": 1.0},
                {"name": "Sign Up", "users": 3500, "conversion_rate": 0.35},
                {"name": "Character Creation", "users": 2800, "conversion_rate": 0.28},
                {"name": "First Session", "users": 2100, "conversion_rate": 0.21},
                {"name": "Return Visit", "users": 1500, "conversion_rate": 0.15}
            ]

            return {"steps": steps}

        except Exception as e:
            self.logger.error(f"Error getting conversion funnel data: {e}")
            return {"steps": []}

    async def _get_engagement_heatmap_data(self, params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get engagement heatmap data"""
        try:
            # Mock heatmap data
            hours = list(range(24))
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            # Generate random engagement data
            import random
            data = []
            for day in range(7):
                row = []
                for hour in range(24):
                    # Higher engagement during typical hours
                    if 9 <= hour <= 21:
                        value = random.uniform(0.6, 1.0)
                    else:
                        value = random.uniform(0.1, 0.4)
                    row.append(value)
                data.append(row)

            return {
                "x_labels": [f"{h:02d}:00" for h in hours],
                "y_labels": days,
                "data": data
            }

        except Exception as e:
            self.logger.error(f"Error getting engagement heatmap data: {e}")
            return {"x_labels": [], "y_labels": [], "data": []}

    # Helper methods

    def _format_metric_value(self, value: float, viz_config: Dict[str, Any]) -> str:
        """Format metric value based on visualization config"""
        try:
            format_type = viz_config.get("format", "number")

            if format_type == "number":
                if value >= 1000000:
                    return f"{value/1000000:.1f}M"
                elif value >= 1000:
                    return f"{value/1000:.1f}K"
                else:
                    return f"{int(value):,}"
            elif format_type == "percentage":
                return f"{value*100:.1f}%"
            elif format_type == "duration":
                unit = viz_config.get("unit", "seconds")
                if unit == "ms":
                    return f"{int(value)}ms"
                else:
                    return f"{int(value)}s"
            elif format_type == "currency":
                return f"${value:,.2f}"
            else:
                return str(value)

        except Exception:
            return str(value)

    def _check_threshold(self, value: float, threshold: Dict[str, float]) -> Dict[str, Any]:
        """Check if value exceeds thresholds"""
        try:
            if "critical" in threshold and value >= threshold["critical"]:
                return {"level": "critical", "message": "Critical threshold exceeded"}
            elif "warning" in threshold and value >= threshold["warning"]:
                return {"level": "warning", "message": "Warning threshold exceeded"}
            else:
                return {"level": "normal", "message": "Within normal range"}

        except Exception:
            return {"level": "unknown", "message": "Unable to check threshold"}

    async def _cache_widget_data(self, widget_key: str, data: Dict[str, Any], ttl: int):
        """Cache widget data in Redis"""
        try:
            await self.redis_client.setex(
                f"dashboard_widget:{widget_key}",
                ttl,
                json.dumps(data, default=str)
            )

        except Exception as e:
            self.logger.error(f"Error caching widget data: {e}")

    async def _get_cached_widget_data(self, widget_key: str) -> Optional[Dict[str, Any]]:
        """Get cached widget data"""
        try:
            cached_data = await self.redis_client.get(f"dashboard_widget:{widget_key}")
            if cached_data:
                return json.loads(cached_data)
            return None

        except Exception as e:
            self.logger.error(f"Error getting cached widget data: {e}")
            return None

    async def _load_dashboard_from_db(self, dashboard_id: str) -> Optional[Dashboard]:
        """Load dashboard configuration from database"""
        try:
            query = text("""
                SELECT * FROM dashboards WHERE dashboard_id = :dashboard_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'dashboard_id': dashboard_id})
                row = result.fetchone()

                if row:
                    widgets_data = json.loads(row.widgets)
                    widgets = [DashboardWidget(**widget_data) for widget_data in widgets_data]

                    return Dashboard(
                        dashboard_id=row.dashboard_id,
                        name=row.name,
                        description=row.description,
                        category=row.category,
                        widgets=widgets,
                        layout=json.loads(row.layout),
                        filters=json.loads(row.filters),
                        permissions=json.loads(row.permissions),
                        auto_refresh=row.auto_refresh,
                        created_at=row.created_at,
                        updated_at=row.updated_at
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error loading dashboard from database: {e}")
            return None

    async def refresh_all_dashboards(self):
        """Refresh all dashboard caches"""
        try:
            self.logger.info("Refreshing all dashboard caches...")

            for dashboard_id in self.dashboard_templates.keys():
                try:
                    await self.generate_dashboard(dashboard_id, force_refresh=True)
                except Exception as e:
                    self.logger.error(f"Error refreshing dashboard {dashboard_id}: {e}")

            self.logger.info("Dashboard refresh completed")

        except Exception as e:
            self.logger.error(f"Error refreshing dashboards: {e}")

    def get_dashboard_list(self, category: str = None) -> List[Dict[str, Any]]:
        """Get list of available dashboards"""
        try:
            dashboards = []
            for dashboard_id, dashboard in self.dashboard_templates.items():
                if category is None or dashboard.category == category:
                    dashboards.append({
                        "dashboard_id": dashboard_id,
                        "name": dashboard.name,
                        "description": dashboard.description,
                        "category": dashboard.category,
                        "widget_count": len(dashboard.widgets),
                        "auto_refresh": dashboard.auto_refresh
                    })

            return dashboards

        except Exception as e:
            self.logger.error(f"Error getting dashboard list: {e}")
            return []