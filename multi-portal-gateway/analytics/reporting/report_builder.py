#!/usr/bin/env python3
"""
Report Builder
Automated report building and generation system
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
from io import BytesIO
import base64

from ..analytics_engine import AnalyticsConfig


@dataclass
class ReportSection:
    """Report section configuration"""
    section_id: str
    title: str
    section_type: str  # 'summary', 'chart', 'table', 'text', 'insights'
    data_source: str
    query_params: Dict[str, Any]
    visualization_config: Dict[str, Any]
    order: int = 0


@dataclass
class ReportTemplate:
    """Report template configuration"""
    template_id: str
    name: str
    description: str
    category: str
    sections: List[ReportSection]
    layout: Dict[str, Any]
    schedule: Optional[str] = None  # cron expression
    recipients: List[str] = None
    format: str = "pdf"  # 'pdf', 'html', 'json', 'csv'
    auto_generate: bool = False


@dataclass
class GeneratedReport:
    """Generated report instance"""
    report_id: str
    template_id: str
    title: str
    format: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime
    file_path: Optional[str] = None


class ReportBuilder:
    """Automated report building engine"""

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.logger = self._setup_logging()

        # Database connections
        self.redis_client = redis.from_url(config.redis_url)
        self.db_engine = create_engine(config.database_url)
        self.db_session = sessionmaker(bind=self.db_engine)()

        # Report templates and cache
        self.report_templates = {}
        self.report_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Initialize database tables
        self._initialize_tables()

        # Initialize default report templates
        self._initialize_default_templates()

    def _setup_logging(self) -> logging.Logger:
        """Setup report builder logging"""
        logger = logging.getLogger("report_builder")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _initialize_tables(self):
        """Initialize database tables for reports"""
        try:
            # Create report_templates table
            create_templates_table = """
            CREATE TABLE IF NOT EXISTS report_templates (
                template_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                sections TEXT,
                layout TEXT,
                schedule VARCHAR(100),
                recipients TEXT,
                format VARCHAR(20) DEFAULT 'pdf',
                auto_generate BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create generated_reports table
            create_reports_table = """
            CREATE TABLE IF NOT EXISTS generated_reports (
                report_id VARCHAR(100) PRIMARY KEY,
                template_id VARCHAR(100) NOT NULL,
                title VARCHAR(200) NOT NULL,
                format VARCHAR(20) NOT NULL,
                content TEXT,
                metadata TEXT,
                file_path TEXT,
                generated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (template_id) REFERENCES report_templates(template_id)
            );
            """

            # Create report_schedules table
            create_schedules_table = """
            CREATE TABLE IF NOT EXISTS report_schedules (
                id SERIAL PRIMARY KEY,
                template_id VARCHAR(100) NOT NULL,
                schedule_expression VARCHAR(100) NOT NULL,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES report_templates(template_id)
            );
            """

            # Create indexes
            create_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_templates_category ON report_templates(category);",
                "CREATE INDEX IF NOT EXISTS idx_reports_template_id ON generated_reports(template_id);",
                "CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON generated_reports(generated_at);",
                "CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON report_schedules(next_run);"
            ]

            with self.db_engine.connect() as conn:
                conn.execute(text(create_templates_table))
                conn.execute(text(create_reports_table))
                conn.execute(text(create_schedules_table))
                for index_sql in create_indexes:
                    conn.execute(text(index_sql))
                conn.commit()

            self.logger.info("Report tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing report tables: {e}")

    def _initialize_default_templates(self):
        """Initialize default report templates"""
        default_templates = [
            # Weekly Business Report
            ReportTemplate(
                template_id="weekly_business_report",
                name="Weekly Business Report",
                description="Comprehensive weekly business performance report",
                category="business",
                sections=[
                    ReportSection(
                        section_id="executive_summary",
                        title="Executive Summary",
                        section_type="summary",
                        data_source="business_metrics",
                        query_params={"period": "7d", "metrics": ["users", "revenue", "engagement"]},
                        visualization_config={"style": "compact"},
                        order=1
                    ),
                    ReportSection(
                        section_id="user_analytics",
                        title="User Analytics",
                        section_type="chart",
                        data_source="user_metrics",
                        query_params={"period": "7d", "granularity": "daily"},
                        visualization_config={
                            "chart_type": "line",
                            "metrics": ["new_users", "active_users", "retention_rate"]
                        },
                        order=2
                    ),
                    ReportSection(
                        section_id="revenue_breakdown",
                        title="Revenue Breakdown",
                        section_type="chart",
                        data_source="revenue_metrics",
                        query_params={"period": "7d"},
                        visualization_config={
                            "chart_type": "mixed",
                            "show_trend": True
                        },
                        order=3
                    ),
                    ReportSection(
                        section_id="top_features",
                        title="Top Performing Features",
                        section_type="table",
                        data_source="feature_metrics",
                        query_params={"period": "7d", "limit": 10},
                        visualization_config={
                            "columns": ["feature", "adoption_rate", "usage_frequency", "satisfaction_score"]
                        },
                        order=4
                    ),
                    ReportSection(
                        section_id="insights",
                        title="Key Insights & Recommendations",
                        section_type="insights",
                        data_source="ai_insights",
                        query_params={"period": "7d", "focus_areas": ["growth", "retention", "engagement"]},
                        visualization_config={"style": "bulleted"},
                        order=5
                    )
                ],
                layout={"page_size": "A4", "orientation": "portrait"},
                schedule="0 9 * * 1",  # Monday 9 AM
                recipients=["executives@company.com", "product@company.com"],
                format="pdf",
                auto_generate=True
            ),

            # Monthly Product Performance Report
            ReportTemplate(
                template_id="monthly_product_report",
                name="Monthly Product Performance Report",
                description="Detailed product usage and performance analysis",
                category="product",
                sections=[
                    ReportSection(
                        section_id="product_overview",
                        title="Product Overview",
                        section_type="summary",
                        data_source="product_metrics",
                        query_params={"period": "30d"},
                        visualization_config={"include_kpis": True},
                        order=1
                    ),
                    ReportSection(
                        section_id="feature_adoption",
                        title="Feature Adoption Analysis",
                        section_type="chart",
                        data_source="feature_adoption",
                        query_params={"period": "30d"},
                        visualization_config={
                            "chart_type": "horizontal_bar",
                            "show_growth": True
                        },
                        order=2
                    ),
                    ReportSection(
                        section_id="user_segments",
                        title="User Segment Analysis",
                        section_type="chart",
                        data_source="user_segments",
                        query_params={"period": "30d"},
                        visualization_config={
                            "chart_type": "pie",
                            "include_details": True
                        },
                        order=3
                    ),
                    ReportSection(
                        section_id="conversion_funnel",
                        title="Conversion Funnel Analysis",
                        section_type="funnel",
                        data_source="conversion_metrics",
                        query_params={"period": "30d"},
                        visualization_config={
                            "show_dropoff": True,
                            "include_recommendations": True
                        },
                        order=4
                    ),
                    ReportSection(
                        section_id="usage_patterns",
                        title="Usage Patterns",
                        section_type="heatmap",
                        data_source="usage_patterns",
                        query_params={"period": "30d"},
                        visualization_config={
                            "time_analysis": True,
                            "device_breakdown": True
                        },
                        order=5
                    )
                ],
                layout={"page_size": "A4", "orientation": "landscape"},
                schedule="0 8 1 * *",  # 1st of month 8 AM
                recipients=["product@company.com", "engineering@company.com"],
                format="pdf",
                auto_generate=True
            ),

            # User Engagement Report
            ReportTemplate(
                template_id="user_engagement_report",
                name="User Engagement Report",
                description="User engagement and behavior analysis",
                category="engagement",
                sections=[
                    ReportSection(
                        section_id="engagement_summary",
                        title="Engagement Summary",
                        section_type="summary",
                        data_source="engagement_metrics",
                        query_params={"period": "14d"},
                        visualization_config={"include_trends": True},
                        order=1
                    ),
                    ReportSection(
                        section_id="daily_activity",
                        title="Daily Activity Patterns",
                        section_type="chart",
                        data_source="activity_patterns",
                        query_params={"period": "14d", "granularity": "hourly"},
                        visualization_config={
                            "chart_type": "area",
                            "show_peaks": True
                        },
                        order=2
                    ),
                    ReportSection(
                        section_id="session_analysis",
                        title="Session Analysis",
                        section_type="table",
                        data_source="session_metrics",
                        query_params={"period": "14d"},
                        visualization_config={
                            "columns": ["metric", "value", "change_vs_previous"],
                            "include_percentiles": True
                        },
                        order=3
                    ),
                    ReportSection(
                        section_id="cohort_retention",
                        title="Cohort Retention Analysis",
                        section_type="chart",
                        data_source="cohort_metrics",
                        query_params={"period": "90d"},
                        visualization_config={
                            "chart_type": "heatmap",
                            "cohort_analysis": True
                        },
                        order=4
                    )
                ],
                layout={"page_size": "A4", "orientation": "portrait"},
                schedule=None,  # On-demand only
                recipients=["growth@company.com"],
                format="html",
                auto_generate=False
            ),

            # Real-time Dashboard Report
            ReportTemplate(
                template_id="realtime_dashboard",
                name="Real-time Dashboard Snapshot",
                description="Real-time system and user activity snapshot",
                category="operations",
                sections=[
                    ReportSection(
                        section_id="current_metrics",
                        title="Current Metrics",
                        section_type="summary",
                        data_source="realtime_metrics",
                        query_params={},
                        visualization_config={"realtime": True},
                        order=1
                    ),
                    ReportSection(
                        section_id="system_health",
                        title="System Health",
                        section_type="chart",
                        data_source="system_metrics",
                        query_params={"period": "1h"},
                        visualization_config={
                            "chart_type": "gauge",
                            "include_alerts": True
                        },
                        order=2
                    ),
                    ReportSection(
                        section_id="active_users",
                        title="Active Users Breakdown",
                        section_type="chart",
                        data_source="active_users",
                        query_params={},
                        visualization_config={
                            "chart_type": "donut",
                            "realtime": True
                        },
                        order=3
                    )
                ],
                layout={"page_size": "A4", "orientation": "portrait"},
                schedule="*/15 * * * *",  # Every 15 minutes
                recipients=["ops@company.com", "support@company.com"],
                format="html",
                auto_generate=True
            )
        ]

        for template in default_templates:
            self.add_template(template)

    def add_template(self, template: ReportTemplate):
        """Add a report template"""
        try:
            # Store in database
            query = text("""
                INSERT INTO report_templates (
                    template_id, name, description, category, sections, layout,
                    schedule, recipients, format, auto_generate
                ) VALUES (
                    :template_id, :name, :description, :category, :sections, :layout,
                    :schedule, :recipients, :format, :auto_generate
                )
                ON CONFLICT (template_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    sections = EXCLUDED.sections,
                    layout = EXCLUDED.layout,
                    schedule = EXCLUDED.schedule,
                    recipients = EXCLUDED.recipients,
                    format = EXCLUDED.format,
                    auto_generate = EXCLUDED.auto_generate,
                    updated_at = CURRENT_TIMESTAMP
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'template_id': template.template_id,
                    'name': template.name,
                    'description': template.description,
                    'category': template.category,
                    'sections': json.dumps([asdict(section) for section in template.sections]),
                    'layout': json.dumps(template.layout),
                    'schedule': template.schedule,
                    'recipients': json.dumps(template.recipients or []),
                    'format': template.format,
                    'auto_generate': template.auto_generate
                })
                conn.commit()

            self.report_templates[template.template_id] = template
            self.logger.info(f"Added report template: {template.name}")

        except Exception as e:
            self.logger.error(f"Error adding report template: {e}")

    async def build_report(self, template_id: str,
                         time_range: timedelta = None,
                         format: str = None,
                         filters: Dict[str, Any] = None) -> GeneratedReport:
        """Build a report from template"""
        try:
            template = self.report_templates.get(template_id)
            if not template:
                # Load from database
                template = await self._load_template_from_db(template_id)
                if not template:
                    raise ValueError(f"Template not found: {template_id}")

            self.logger.info(f"Building report: {template.name}")

            # Set default time range
            if time_range is None:
                time_range = timedelta(days=7)

            # Override format if specified
            report_format = format or template.format

            # Generate content for each section
            sections_content = {}
            for section in template.sections:
                try:
                    section_content = await self._generate_section_content(
                        section, time_range, filters or {}
                    )
                    sections_content[section.section_id] = section_content
                except Exception as e:
                    self.logger.error(f"Error generating section {section.section_id}: {e}")
                    sections_content[section.section_id] = {
                        "error": str(e),
                        "section_type": section.section_type
                    }

            # Assemble complete report
            report_content = {
                "title": template.name,
                "description": template.description,
                "generated_at": datetime.utcnow().isoformat(),
                "period": {
                    "start": (datetime.utcnow() - time_range).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                    "duration_days": time_range.days
                },
                "sections": sections_content,
                "layout": template.layout,
                "metadata": {
                    "template_id": template_id,
                    "format": report_format,
                    "total_sections": len(template.sections),
                    "generated_sections": len([s for s in sections_content.values() if "error" not in s])
                }
            }

            # Create report instance
            report = GeneratedReport(
                report_id=f"{template_id}_{int(datetime.utcnow().timestamp())}",
                template_id=template_id,
                title=template.name,
                format=report_format,
                content=report_content,
                metadata={
                    "template_name": template.name,
                    "category": template.category,
                    "generation_time": datetime.utcnow().isoformat(),
                    "filters": filters or {}
                },
                generated_at=datetime.utcnow()
            )

            # Store report
            await self._store_report(report)

            # Generate file if needed
            if report_format in ["pdf", "html"]:
                file_path = await self._generate_report_file(report)
                report.file_path = file_path

            self.logger.info(f"Report built successfully: {report.report_id}")
            return report

        except Exception as e:
            self.logger.error(f"Error building report: {e}")
            raise

    async def _generate_section_content(self, section: ReportSection,
                                      time_range: timedelta,
                                      filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for a specific section"""
        try:
            if section.section_type == "summary":
                return await self._generate_summary_section(section, time_range, filters)
            elif section.section_type == "chart":
                return await self._generate_chart_section(section, time_range, filters)
            elif section.section_type == "table":
                return await self._generate_table_section(section, time_range, filters)
            elif section.section_type == "funnel":
                return await self._generate_funnel_section(section, time_range, filters)
            elif section.section_type == "heatmap":
                return await self._generate_heatmap_section(section, time_range, filters)
            elif section.section_type == "insights":
                return await self._generate_insights_section(section, time_range, filters)
            else:
                raise ValueError(f"Unknown section type: {section.section_type}")

        except Exception as e:
            self.logger.error(f"Error generating section content: {e}")
            raise

    async def _generate_summary_section(self, section: ReportSection,
                                      time_range: timedelta,
                                      filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary section content"""
        try:
            # Get summary metrics
            if section.data_source == "business_metrics":
                metrics = await self._get_business_summary(time_range, filters)
            elif section.data_source == "product_metrics":
                metrics = await self._get_product_summary(time_range, filters)
            elif section.data_source == "engagement_metrics":
                metrics = await self._get_engagement_summary(time_range, filters)
            else:
                metrics = {}

            viz_config = section.visualization_config

            return {
                "section_type": "summary",
                "title": section.title,
                "metrics": metrics,
                "visualization_config": viz_config,
                "insights": self._generate_summary_insights(metrics)
            }

        except Exception as e:
            self.logger.error(f"Error generating summary section: {e}")
            return {"error": str(e), "section_type": "summary"}

    async def _generate_chart_section(self, section: ReportSection,
                                    time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart section content"""
        try:
            # Get chart data
            if section.data_source == "user_metrics":
                data = await self._get_user_chart_data(section.query_params, time_range, filters)
            elif section.data_source == "revenue_metrics":
                data = await self._get_revenue_chart_data(section.query_params, time_range, filters)
            elif section.data_source == "feature_adoption":
                data = await self._get_feature_adoption_chart_data(section.query_params, time_range, filters)
            else:
                data = {"labels": [], "datasets": []}

            viz_config = section.visualization_config

            return {
                "section_type": "chart",
                "title": section.title,
                "data": data,
                "visualization_config": viz_config,
                "analysis": self._analyze_chart_data(data, viz_config)
            }

        except Exception as e:
            self.logger.error(f"Error generating chart section: {e}")
            return {"error": str(e), "section_type": "chart"}

    async def _generate_table_section(self, section: ReportSection,
                                    time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate table section content"""
        try:
            # Get table data
            if section.data_source == "feature_metrics":
                data = await self._get_feature_table_data(section.query_params, time_range, filters)
            elif section.data_source == "session_metrics":
                data = await self._get_session_table_data(section.query_params, time_range, filters)
            else:
                data = {"columns": [], "rows": []}

            viz_config = section.visualization_config

            return {
                "section_type": "table",
                "title": section.title,
                "data": data,
                "visualization_config": viz_config,
                "summary": self._generate_table_summary(data)
            }

        except Exception as e:
            self.logger.error(f"Error generating table section: {e}")
            return {"error": str(e), "section_type": "table"}

    async def _generate_funnel_section(self, section: ReportSection,
                                     time_range: timedelta,
                                     filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate funnel section content"""
        try:
            # Get funnel data
            if section.data_source == "conversion_metrics":
                data = await self._get_conversion_funnel_data(section.query_params, time_range, filters)
            else:
                data = {"steps": []}

            viz_config = section.visualization_config

            return {
                "section_type": "funnel",
                "title": section.title,
                "data": data,
                "visualization_config": viz_config,
                "analysis": self._analyze_funnel_data(data)
            }

        except Exception as e:
            self.logger.error(f"Error generating funnel section: {e}")
            return {"error": str(e), "section_type": "funnel"}

    async def _generate_heatmap_section(self, section: ReportSection,
                                      time_range: timedelta,
                                      filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate heatmap section content"""
        try:
            # Get heatmap data
            if section.data_source == "usage_patterns":
                data = await self._get_usage_heatmap_data(section.query_params, time_range, filters)
            elif section.data_source == "cohort_metrics":
                data = await self._get_cohort_heatmap_data(section.query_params, time_range, filters)
            else:
                data = {"x_labels": [], "y_labels": [], "data": []}

            viz_config = section.visualization_config

            return {
                "section_type": "heatmap",
                "title": section.title,
                "data": data,
                "visualization_config": viz_config,
                "patterns": self._identify_heatmap_patterns(data)
            }

        except Exception as e:
            self.logger.error(f"Error generating heatmap section: {e}")
            return {"error": str(e), "section_type": "heatmap"}

    async def _generate_insights_section(self, section: ReportSection,
                                       time_range: timedelta,
                                       filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights section"""
        try:
            # Get insights from data
            focus_areas = section.query_params.get("focus_areas", [])
            insights = await self._generate_ai_insights(time_range, focus_areas, filters)

            viz_config = section.visualization_config

            return {
                "section_type": "insights",
                "title": section.title,
                "insights": insights,
                "visualization_config": viz_config,
                "recommendations": self._generate_recommendations(insights)
            }

        except Exception as e:
            self.logger.error(f"Error generating insights section: {e}")
            return {"error": str(e), "section_type": "insights"}

    # Data source methods

    async def _get_business_summary(self, time_range: timedelta, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get business summary metrics"""
        try:
            # Mock business metrics
            return {
                "total_users": 15420,
                "new_users": 2340,
                "active_users": 8950,
                "revenue": 45230.50,
                "engagement_rate": 0.73,
                "retention_rate": 0.82,
                "churn_rate": 0.05,
                "avg_session_duration": 1245,
                "conversion_rate": 0.12
            }

        except Exception as e:
            self.logger.error(f"Error getting business summary: {e}")
            return {}

    async def _get_product_summary(self, time_range: timedelta, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get product summary metrics"""
        try:
            return {
                "feature_adoption_rate": 0.68,
                "most_used_feature": "Character Creation",
                "feature_satisfaction": 4.2,
                "bug_reports": 45,
                "feature_requests": 128,
                "user_feedback_score": 4.1
            }

        except Exception as e:
            self.logger.error(f"Error getting product summary: {e}")
            return {}

    async def _get_engagement_summary(self, time_range: timedelta, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get engagement summary metrics"""
        try:
            return {
                "daily_active_users": 3240,
                "avg_session_length": 1245,
                "pages_per_session": 8.3,
                "bounce_rate": 0.23,
                "return_user_rate": 0.76,
                "social_interactions": 4520,
                "content_created": 890
            }

        except Exception as e:
            self.logger.error(f"Error getting engagement summary: {e}")
            return {}

    async def _get_user_chart_data(self, params: Dict[str, Any], time_range: timedelta,
                                 filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user chart data"""
        try:
            # Mock time series data
            import random
            dates = pd.date_range(end=datetime.utcnow(), periods=time_range.days, freq='D')

            metrics = params.get("metrics", ["new_users", "active_users"])
            datasets = []

            for metric in metrics:
                if metric == "new_users":
                    values = [random.randint(50, 150) for _ in range(len(dates))]
                    color = "#007bff"
                elif metric == "active_users":
                    values = [random.randint(800, 1200) for _ in range(len(dates))]
                    color = "#28a745"
                elif metric == "retention_rate":
                    values = [random.uniform(0.7, 0.9) for _ in range(len(dates))]
                    color = "#ffc107"
                else:
                    values = [random.uniform(0, 100) for _ in range(len(dates))]
                    color = "#6c757d"

                datasets.append({
                    "label": metric.replace("_", " ").title(),
                    "data": values,
                    "borderColor": color,
                    "backgroundColor": color + "20"  # Add transparency
                })

            return {
                "labels": [date.strftime('%Y-%m-%d') for date in dates],
                "datasets": datasets
            }

        except Exception as e:
            self.logger.error(f"Error getting user chart data: {e}")
            return {"labels": [], "datasets": []}

    async def _get_revenue_chart_data(self, params: Dict[str, Any], time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get revenue chart data"""
        # Mock revenue data
        dates = pd.date_range(end=datetime.utcnow(), periods=time_range.days, freq='D')
        values = [random.uniform(1000, 2000) for _ in range(len(dates))]

        return {
            "labels": [date.strftime('%Y-%m-%d') for date in dates],
            "datasets": [{
                "label": "Revenue",
                "data": values,
                "borderColor": "#28a745",
                "backgroundColor": "rgba(40, 167, 69, 0.1)"
            }]
        }

    async def _get_feature_adoption_chart_data(self, params: Dict[str, Any], time_range: timedelta,
                                            filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get feature adoption chart data"""
        features = [
            {"name": "Character Creation", "adoption": 0.85, "growth": 0.12},
            {"name": "Dialogue System", "adoption": 0.92, "growth": 0.08},
            {"name": "Combat System", "adoption": 0.67, "growth": 0.15},
            {"name": "Social Features", "adoption": 0.43, "growth": 0.25},
            {"name": "Marketplace", "adoption": 0.28, "growth": 0.35}
        ]

        return {
            "labels": [f["name"] for f in features],
            "datasets": [{
                "label": "Adoption Rate",
                "data": [f["adoption"] * 100 for f in features],
                "backgroundColor": "#007bff"
            }]
        }

    async def _get_feature_table_data(self, params: Dict[str, Any], time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get feature table data"""
        limit = params.get("limit", 10)

        rows = [
            {"feature": "Character Creation", "adoption_rate": 0.85, "usage_frequency": 4.2, "satisfaction_score": 4.5},
            {"feature": "Dialogue System", "adoption_rate": 0.92, "usage_frequency": 8.1, "satisfaction_score": 4.3},
            {"feature": "Combat System", "adoption_rate": 0.67, "usage_frequency": 2.8, "satisfaction_score": 4.1},
            {"feature": "Social Features", "adoption_rate": 0.43, "usage_frequency": 1.5, "satisfaction_score": 3.8},
            {"feature": "Marketplace", "adoption_rate": 0.28, "usage_frequency": 0.8, "satisfaction_score": 3.9}
        ]

        return {
            "columns": ["feature", "adoption_rate", "usage_frequency", "satisfaction_score"],
            "rows": rows[:limit]
        }

    async def _get_session_table_data(self, params: Dict[str, Any], time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get session table data"""
        rows = [
            {"metric": "Avg Session Duration", "value": "1245s", "change_vs_previous": "+5.2%"},
            {"metric": "Pages per Session", "value": 8.3, "change_vs_previous": "+2.1%"},
            {"metric": "Bounce Rate", "value": "23%", "change_vs_previous": "-3.4%"},
            {"metric": "Session Frequency", "value": 3.2/week, "change_vs_previous": "+8.7%"}
        ]

        return {
            "columns": ["metric", "value", "change_vs_previous"],
            "rows": rows
        }

    async def _get_conversion_funnel_data(self, params: Dict[str, Any], time_range: timedelta,
                                        filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversion funnel data"""
        steps = [
            {"name": "Visit", "users": 10000, "conversion_rate": 1.0},
            {"name": "Sign Up", "users": 3500, "conversion_rate": 0.35},
            {"name": "Character Creation", "users": 2800, "conversion_rate": 0.28},
            {"name": "First Session", "users": 2100, "conversion_rate": 0.21},
            {"name": "Return Visit", "users": 1500, "conversion_rate": 0.15}
        ]

        return {"steps": steps}

    async def _get_usage_heatmap_data(self, params: Dict[str, Any], time_range: timedelta,
                                    filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get usage heatmap data"""
        hours = list(range(24))
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Generate random usage data
        import random
        data = []
        for day in range(7):
            row = []
            for hour in range(24):
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

    async def _get_cohort_heatmap_data(self, params: Dict[str, Any], time_range: timedelta,
                                     filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get cohort heatmap data"""
        # Mock cohort retention data
        cohorts = ["Week 1", "Week 2", "Week 3", "Week 4"]
        periods = ["Day 1", "Day 7", "Day 14", "Day 21", "Day 28"]

        data = []
        for cohort in cohorts:
            row = []
            base_retention = random.uniform(0.8, 0.95)
            for period in periods:
                row.append(max(base_retention - random.uniform(0, 0.3), 0.1))
            data.append(row)

        return {
            "x_labels": periods,
            "y_labels": cohorts,
            "data": data
        }

    async def _generate_ai_insights(self, time_range: timedelta,
                                  focus_areas: List[str],
                                  filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights"""
        # Mock AI insights
        insights = []

        if "growth" in focus_areas:
            insights.append({
                "type": "growth",
                "title": "Strong User Acquisition Trend",
                "description": "User acquisition increased by 23% compared to previous period, driven by improved onboarding flow.",
                "confidence": 0.85,
                "impact": "high",
                "recommendation": "Continue investing in onboarding optimization to maintain growth momentum."
            })

        if "retention" in focus_areas:
            insights.append({
                "type": "retention",
                "title": "Retention Improvement Opportunity",
                "description": "Day 7 retention dropped by 5% for users acquired through social media channels.",
                "confidence": 0.78,
                "impact": "medium",
                "recommendation": "Implement targeted retention campaigns for social media acquired users."
            })

        if "engagement" in focus_areas:
            insights.append({
                "type": "engagement",
                "title": "Feature Engagement Patterns Identified",
                "description": "Users who engage with social features within first 24 hours show 40% higher long-term retention.",
                "confidence": 0.92,
                "impact": "high",
                "recommendation": "Promote social features more prominently in user onboarding."
            })

        return insights

    # Helper methods

    def _generate_summary_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate insights from summary metrics"""
        insights = []

        if metrics.get("growth_rate", 0) > 0.1:
            insights.append("Strong growth trajectory with double-digit percentage increase")

        if metrics.get("retention_rate", 0) > 0.8:
            insights.append("Excellent user retention indicating strong product-market fit")

        if metrics.get("engagement_rate", 0) > 0.7:
            insights.append("High user engagement suggesting valuable user experience")

        return insights

    def _analyze_chart_data(self, data: Dict[str, Any], viz_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chart data and provide insights"""
        analysis = {
            "trends": [],
            "patterns": [],
            "anomalies": []
        }

        # Mock analysis
        if data.get("datasets"):
            for dataset in data["datasets"]:
                values = dataset.get("data", [])
                if len(values) > 1:
                    # Simple trend calculation
                    trend = (values[-1] - values[0]) / values[0] if values[0] != 0 else 0
                    if trend > 0.1:
                        analysis["trends"].append(f"{dataset['label']} shows upward trend")
                    elif trend < -0.1:
                        analysis["trends"].append(f"{dataset['label']} shows downward trend")

        return analysis

    def _generate_table_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for table data"""
        rows = data.get("rows", [])
        if not rows:
            return {}

        return {
            "total_rows": len(rows),
            "key_findings": f"Table contains {len(rows)} data points with detailed metrics"
        }

    def _analyze_funnel_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze funnel conversion data"""
        steps = data.get("steps", [])
        if len(steps) < 2:
            return {}

        overall_conversion = steps[-1]["conversion_rate"]
        biggest_dropoff = 0
        dropoff_step = ""

        for i in range(len(steps) - 1):
            dropoff = steps[i]["conversion_rate"] - steps[i + 1]["conversion_rate"]
            if dropoff > biggest_dropoff:
                biggest_dropoff = dropoff
                dropoff_step = steps[i]["name"]

        return {
            "overall_conversion": overall_conversion,
            "biggest_dropoff": {
                "step": dropoff_step,
                "percentage": biggest_dropoff
            },
            "recommendation": f"Focus optimization efforts on {dropoff_step} step"
        }

    def _identify_heatmap_patterns(self, data: Dict[str, Any]) -> List[str]:
        """Identify patterns in heatmap data"""
        patterns = []

        # Mock pattern identification
        if data.get("data"):
            patterns.append("Peak activity observed during business hours (9 AM - 6 PM)")
            patterns.append("Weekend usage shows different pattern compared to weekdays")

        return patterns

    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations from insights"""
        recommendations = []

        for insight in insights:
            if insight.get("recommendation"):
                recommendations.append(insight["recommendation"])

        return recommendations

    async def _store_report(self, report: GeneratedReport):
        """Store generated report in database"""
        try:
            query = text("""
                INSERT INTO generated_reports (
                    report_id, template_id, title, format, content, metadata, file_path, generated_at
                ) VALUES (
                    :report_id, :template_id, :title, :format, :content, :metadata, :file_path, :generated_at
                )
            """)

            with self.db_engine.connect() as conn:
                conn.execute(query, {
                    'report_id': report.report_id,
                    'template_id': report.template_id,
                    'title': report.title,
                    'format': report.format,
                    'content': json.dumps(report.content, default=str),
                    'metadata': json.dumps(report.metadata, default=str),
                    'file_path': report.file_path,
                    'generated_at': report.generated_at
                })
                conn.commit()

        except Exception as e:
            self.logger.error(f"Error storing report: {e}")

    async def _generate_report_file(self, report: GeneratedReport) -> Optional[str]:
        """Generate report file (PDF/HTML)"""
        try:
            # Mock file generation
            file_path = f"/tmp/reports/{report.report_id}.{report.format}"

            # In practice, would use proper PDF/HTML generation libraries
            with open(file_path, 'w') as f:
                f.write(f"<html><body><h1>{report.title}</h1>")
                f.write(f"<p>Generated at: {report.generated_at}</p>")
                f.write("</body></html>")

            return file_path

        except Exception as e:
            self.logger.error(f"Error generating report file: {e}")
            return None

    async def _load_template_from_db(self, template_id: str) -> Optional[ReportTemplate]:
        """Load report template from database"""
        try:
            query = text("""
                SELECT * FROM report_templates WHERE template_id = :template_id
            """)

            with self.db_engine.connect() as conn:
                result = conn.execute(query, {'template_id': template_id})
                row = result.fetchone()

                if row:
                    sections_data = json.loads(row.sections)
                    sections = [ReportSection(**section_data) for section_data in sections_data]

                    return ReportTemplate(
                        template_id=row.template_id,
                        name=row.name,
                        description=row.description,
                        category=row.category,
                        sections=sections,
                        layout=json.loads(row.layout),
                        schedule=row.schedule,
                        recipients=json.loads(row.recipients) if row.recipients else [],
                        format=row.format,
                        auto_generate=row.auto_generate
                    )
                return None

        except Exception as e:
            self.logger.error(f"Error loading template from database: {e}")
            return None

    def get_template_list(self, category: str = None) -> List[Dict[str, Any]]:
        """Get list of available report templates"""
        try:
            templates = []
            for template_id, template in self.report_templates.items():
                if category is None or template.category == category:
                    templates.append({
                        "template_id": template_id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "format": template.format,
                        "auto_generate": template.auto_generate,
                        "section_count": len(template.sections)
                    })

            return templates

        except Exception as e:
            self.logger.error(f"Error getting template list: {e}")
            return []

    async def get_report_history(self, template_id: str = None,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of generated reports"""
        try:
            where_clause = ""
            params = {"limit": limit}

            if template_id:
                where_clause = "WHERE template_id = :template_id"
                params["template_id"] = template_id

            query = f"""
                SELECT * FROM generated_reports
                {where_clause}
                ORDER BY generated_at DESC
                LIMIT :limit
            """

            with self.db_engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()

            reports = []
            for row in rows:
                reports.append({
                    "report_id": row.report_id,
                    "template_id": row.template_id,
                    "title": row.title,
                    "format": row.format,
                    "generated_at": row.generated_at.isoformat(),
                    "file_path": row.file_path
                })

            return reports

        except Exception as e:
            self.logger.error(f"Error getting report history: {e}")
            return []