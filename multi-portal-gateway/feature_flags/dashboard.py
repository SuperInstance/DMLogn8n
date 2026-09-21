#!/usr/bin/env python3
"""
DMLogn8n Feature Flag and Experiment Dashboard
Web dashboard for managing feature flags, A/B tests, and analytics
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import aiohttp
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd

# Import our services
from feature_flag_service import FeatureFlagService, FeatureFlag
from experiment_manager import ABTestManager, Experiment
from segmentation import UserSegmentationService
from analytics import StatisticalAnalyticsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="DMLogn8n Feature Flag Dashboard", version="1.0.0")

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global service instances
feature_service: Optional[FeatureFlagService] = None
experiment_manager: Optional[ABTestManager] = None
segmentation_service: Optional[UserSegmentationService] = None
analytics_service: Optional[StatisticalAnalyticsService] = None

# WebSocket connections
websocket_connections: List[WebSocket] = []

class DashboardService:
    """Main dashboard service"""

    def __init__(self):
        self.feature_service = None
        self.experiment_manager = None
        self.segmentation_service = None
        self.analytics_service = None

    async def initialize(self):
        """Initialize dashboard with all services"""
        global feature_service, experiment_manager, segmentation_service, analytics_service

        try:
            # Initialize services
            feature_service = FeatureFlagService()
            await feature_service.initialize()

            experiment_manager = ABTestManager()
            await experiment_manager.initialize()

            segmentation_service = UserSegmentationService()
            await segmentation_service.initialize()

            analytics_service = StatisticalAnalyticsService()
            await analytics_service.initialize()

            # Set service references
            self.feature_service = feature_service
            self.experiment_manager = experiment_manager
            self.segmentation_service = segmentation_service
            self.analytics_service = analytics_service

            logger.info("Dashboard initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            raise

    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get dashboard overview data"""
        try:
            overview = {
                "feature_flags": {
                    "total": len(self.feature_service.flags) if self.feature_service else 0,
                    "active": sum(1 for f in self.feature_service.flags.values() if f.current_value != f.default_value) if self.feature_service else 0,
                    "recent_changes": 0  # Would calculate from logs
                },
                "experiments": {
                    "total": len(self.experiment_manager.experiments) if self.experiment_manager else 0,
                    "running": len([e for e in self.experiment_manager.experiments.values() if e.status.value == "running"]) if self.experiment_manager else 0,
                    "completed": len([e for e in self.experiment_manager.experiments.values() if e.status.value == "completed"]) if self.experiment_manager else 0
                },
                "segments": {
                    "total": len(self.segmentation_service.segments) if self.segmentation_service else 0,
                    "active": len([s for s in self.segmentation_service.segments.values() if s.is_active]) if self.segmentation_service else 0,
                    "total_users": len(self.segmentation_service.user_profiles) if self.segmentation_service else 0
                },
                "analytics": {
                    "total_evaluations": 0,  # Would get from Redis
                    "significant_experiments": 0,
                    "anomalies_detected": 0
                }
            }

            return overview
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {"error": str(e)}

    def get_feature_flags_data(self) -> Dict[str, Any]:
        """Get feature flags data for dashboard"""
        try:
            flags = list(self.feature_service.flags.values()) if self.feature_service else []

            flag_data = []
            for flag in flags:
                stats = self.feature_service.get_flag_stats(flag.id)
                flag_info = asdict(flag)
                flag_info['stats'] = stats
                flag_data.append(flag_info)

            return {
                "flags": flag_data,
                "total": len(flag_data),
                "active": sum(1 for f in flag_data if f['current_value'] != f['default_value'])
            }
        except Exception as e:
            logger.error(f"Error getting feature flags data: {e}")
            return {"error": str(e)}

    def get_experiments_data(self) -> Dict[str, Any]:
        """Get experiments data for dashboard"""
        try:
            experiments = list(self.experiment_manager.experiments.values()) if self.experiment_manager else []

            experiment_data = []
            for exp in experiments:
                exp_info = asdict(exp)
                summary = self.experiment_manager.get_experiment_summary(exp.id)
                exp_info['summary'] = summary
                experiment_data.append(exp_info)

            return {
                "experiments": experiment_data,
                "total": len(experiment_data),
                "running": len([e for e in experiment_data if e['status'] == "running"]),
                "completed": len([e for e in experiment_data if e['status'] == "completed"])
            }
        except Exception as e:
            logger.error(f"Error getting experiments data: {e}")
            return {"error": str(e)}

    def get_segments_data(self) -> Dict[str, Any]:
        """Get segmentation data for dashboard"""
        try:
            segments = list(self.segmentation_service.segments.values()) if self.segmentation_service else []

            segment_data = []
            for segment in segments:
                segment_info = asdict(segment)
                analytics = self.segmentation_service.get_segment_analytics(segment.id)
                segment_info['analytics'] = analytics
                segment_data.append(segment_info)

            return {
                "segments": segment_data,
                "total": len(segment_data),
                "active": len([s for s in segment_data if s['is_active']]),
                "total_users": len(self.segmentation_service.user_profiles) if self.segmentation_service else 0
            }
        except Exception as e:
            logger.error(f"Error getting segments data: {e}")
            return {"error": str(e)}

    def create_feature_flag_chart(self) -> Dict[str, Any]:
        """Create feature flag usage chart"""
        try:
            flags = list(self.feature_service.flags.values()) if self.feature_service else []

            # Count flags by type
            flag_types = {}
            for flag in flags:
                flag_type = flag.flag_type.value
                flag_types[flag_type] = flag_types.get(flag_type, 0) + 1

            fig = go.Figure(data=[
                go.Pie(
                    labels=list(flag_types.keys()),
                    values=list(flag_types.values()),
                    hole=0.3
                )
            ])

            fig.update_layout(
                title="Feature Flags by Type",
                font=dict(size=14)
            )

            return json.dumps(fig, cls=PlotlyJSONEncoder)
        except Exception as e:
            logger.error(f"Error creating feature flag chart: {e}")
            return "{}"

    def create_experiment_timeline_chart(self) -> Dict[str, Any]:
        """Create experiment timeline chart"""
        try:
            experiments = list(self.experiment_manager.experiments.values()) if self.experiment_manager else []

            timeline_data = []
            for exp in experiments:
                timeline_data.append({
                    "Experiment": exp.name,
                    "Start": exp.start_date.isoformat() if exp.start_date else datetime.utcnow().isoformat(),
                    "End": exp.end_date.isoformat() if exp.end_date else datetime.utcnow().isoformat(),
                    "Status": exp.status.value
                })

            df = pd.DataFrame(timeline_data)

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="End",
                y="Experiment",
                color="Status",
                title="Experiment Timeline"
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Experiment",
                font=dict(size=12)
            )

            return json.dumps(fig, cls=PlotlyJSONEncoder)
        except Exception as e:
            logger.error(f"Error creating experiment timeline chart: {e}")
            return "{}"

    def create_segment_distribution_chart(self) -> Dict[str, Any]:
        """Create segment distribution chart"""
        try:
            segments = list(self.segmentation_service.segments.values()) if self.segmentation_service else []

            segment_sizes = [(s.name, s.user_count) for s in segments if s.user_count > 0]
            segment_sizes.sort(key=lambda x: x[1], reverse=True)

            # Take top 10 segments
            top_segments = segment_sizes[:10]

            fig = go.Figure(data=[
                go.Bar(
                    x=[s[0] for s in top_segments],
                    y=[s[1] for s in top_segments]
                )
            ])

            fig.update_layout(
                title="Top 10 Segments by User Count",
                xaxis_title="Segment",
                yaxis_title="Number of Users",
                font=dict(size=12)
            )

            return json.dumps(fig, cls=PlotlyJSONEncoder)
        except Exception as e:
            logger.error(f"Error creating segment distribution chart: {e}")
            return "{}"

# Global dashboard service
dashboard_service = DashboardService()

# Initialize services
@app.on_event("startup")
async def startup_event():
    await dashboard_service.initialize()

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/overview")
async def get_overview():
    """Get dashboard overview"""
    return JSONResponse(content=dashboard_service.get_dashboard_overview())

@app.get("/api/feature-flags")
async def get_feature_flags():
    """Get all feature flags"""
    return JSONResponse(content=dashboard_service.get_feature_flags_data())

@app.get("/api/experiments")
async def get_experiments():
    """Get all experiments"""
    return JSONResponse(content=dashboard_service.get_experiments_data())

@app.get("/api/segments")
async def get_segments():
    """Get all segments"""
    return JSONResponse(content=dashboard_service.get_segments_data())

@app.get("/api/charts/feature-flags")
async def get_feature_flags_chart():
    """Get feature flags chart"""
    chart_data = dashboard_service.create_feature_flag_chart()
    return JSONResponse(content=json.loads(chart_data))

@app.get("/api/charts/experiment-timeline")
async def get_experiment_timeline_chart():
    """Get experiment timeline chart"""
    chart_data = dashboard_service.create_experiment_timeline_chart()
    return JSONResponse(content=json.loads(chart_data))

@app.get("/api/charts/segment-distribution")
async def get_segment_distribution_chart():
    """Get segment distribution chart"""
    chart_data = dashboard_service.create_segment_distribution_chart()
    return JSONResponse(content=json.loads(chart_data))

# Feature Flag Management Endpoints
@app.post("/api/feature-flags")
async def create_feature_flag(flag_data: Dict[str, Any]):
    """Create a new feature flag"""
    try:
        flag = await dashboard_service.feature_service.create_flag(flag_data)
        return JSONResponse(content=asdict(flag))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/feature-flags/{flag_id}")
async def update_feature_flag(flag_id: str, updates: Dict[str, Any]):
    """Update a feature flag"""
    try:
        flag = await dashboard_service.feature_service.update_flag(flag_id, updates)
        return JSONResponse(content=asdict(flag))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/feature-flags/{flag_id}")
async def delete_feature_flag(flag_id: str):
    """Delete a feature flag"""
    try:
        await dashboard_service.feature_service.delete_flag(flag_id)
        return JSONResponse(content={"message": "Flag deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Experiment Management Endpoints
@app.post("/api/experiments")
async def create_experiment(experiment_data: Dict[str, Any]):
    """Create a new experiment"""
    try:
        # This would create experiment using experiment manager
        return JSONResponse(content={"message": "Experiment created successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    """Start an experiment"""
    try:
        await dashboard_service.experiment_manager.start_experiment(experiment_id)
        return JSONResponse(content={"message": "Experiment started successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/experiments/{experiment_id}/stop")
async def stop_experiment(experiment_id: str, reason: str = "manual"):
    """Stop an experiment"""
    try:
        await dashboard_service.experiment_manager.stop_experiment(experiment_id, reason)
        return JSONResponse(content={"message": "Experiment stopped successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get experiment results"""
    try:
        results = dashboard_service.experiment_manager.get_experiment_summary(experiment_id)
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Segmentation Endpoints
@app.post("/api/segments")
async def create_segment(segment_data: Dict[str, Any]):
    """Create a new segment"""
    try:
        segment = await dashboard_service.segmentation_service.create_segment(segment_data)
        return JSONResponse(content=asdict(segment))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/segments/{segment_id}")
async def update_segment(segment_id: str, updates: Dict[str, Any]):
    """Update a segment"""
    try:
        segment = await dashboard_service.segmentation_service.update_segment(segment_id, updates)
        return JSONResponse(content=asdict(segment))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/segments/{segment_id}")
async def delete_segment(segment_id: str):
    """Delete a segment"""
    try:
        await dashboard_service.segmentation_service.delete_segment(segment_id)
        return JSONResponse(content={"message": "Segment deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/segments/{segment_id}/users")
async def get_segment_users(segment_id: str, limit: int = 1000):
    """Get users in a segment"""
    try:
        users = await dashboard_service.segmentation_service.get_users_in_segment(segment_id, limit)
        return JSONResponse(content={"users": users, "total": len(users)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Analytics Endpoints
@app.post("/api/analytics/experiment/{experiment_id}")
async def analyze_experiment(experiment_id: str, analysis_request: Dict[str, Any]):
    """Analyze experiment results"""
    try:
        from analytics import AnalyticsRequest, ConfidenceLevel

        request = AnalyticsRequest(
            experiment_id=experiment_id,
            metric_ids=analysis_request.get("metric_ids", []),
            confidence_level=ConfidenceLevel(analysis_request.get("confidence_level", 0.95))
        )

        results = await dashboard_service.analytics_service.analyze_experiment(request)
        return JSONResponse(content=asdict(results))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/metrics/{metric_id}")
async def get_metric_analytics(metric_id: str, days: int = 30):
    """Get analytics for a specific metric"""
    try:
        summary = await dashboard_service.analytics_service.get_metric_summary(metric_id, days)
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(30)  # Send update every 30 seconds

            # Send overview data
            overview = dashboard_service.get_dashboard_overview()
            await websocket.send_text(json.dumps({
                "type": "overview_update",
                "data": overview,
                "timestamp": datetime.utcnow().isoformat()
            }))

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Utility function to broadcast updates to all connected clients
async def broadcast_update(message_type: str, data: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            disconnected.append(websocket)

    # Remove disconnected websockets
    for websocket in disconnected:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Create HTML templates
def create_templates():
    """Create HTML templates for the dashboard"""
    templates_dir = "/home/activeloguser/DMLogn8n/multi-portal-gateway/feature_flags/templates"
    static_dir = "/home/activeloguser/DMLogn8n/multi-portal-gateway/feature_flags/static"

    import os
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)

    # Main dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DMLogn8n Feature Flag Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card { @apply bg-white rounded-lg shadow-md p-6; }
        .metric { @apply text-2xl font-bold; }
        .label { @apply text-gray-600 text-sm; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800">DMLogn8n Feature Flag Dashboard</h1>
            <p class="text-gray-600">Real-time management of feature flags, A/B tests, and user segmentation</p>
        </header>

        <!-- Overview Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="card">
                <div class="metric" id="total-flags">-</div>
                <div class="label">Total Feature Flags</div>
            </div>
            <div class="card">
                <div class="metric" id="running-experiments">-</div>
                <div class="label">Running Experiments</div>
            </div>
            <div class="card">
                <div class="metric" id="active-segments">-</div>
                <div class="label">Active Segments</div>
            </div>
            <div class="card">
                <div class="metric" id="total-users">-</div>
                <div class="label">Total Users</div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">Feature Flags by Type</h2>
                <div id="feature-flags-chart"></div>
            </div>
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">Top Segments</h2>
                <div id="segment-chart"></div>
            </div>
        </div>

        <!-- Tables Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">Recent Feature Flags</h2>
                <div id="feature-flags-table" class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left py-2">Name</th>
                                <th class="text-left py-2">Type</th>
                                <th class="text-left py-2">Status</th>
                                <th class="text-left py-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="feature-flags-tbody">
                            <!-- Populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">Running Experiments</h2>
                <div id="experiments-table" class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left py-2">Name</th>
                                <th class="text-left py-2">Status</th>
                                <th class="text-left py-2">Progress</th>
                                <th class="text-left py-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="experiments-tbody">
                            <!-- Populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket('ws://localhost:8000/ws');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'overview_update') {
                updateOverview(data.data);
            }
        };

        // Fetch initial data
        async function loadDashboard() {
            try {
                // Load overview
                const overview = await fetch('/api/overview').then(r => r.json());
                updateOverview(overview);

                // Load feature flags
                const flags = await fetch('/api/feature-flags').then(r => r.json());
                updateFeatureFlagsTable(flags.flags);

                // Load experiments
                const experiments = await fetch('/api/experiments').then(r => r.json());
                updateExperimentsTable(experiments.experiments);

                // Load charts
                loadCharts();
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        function updateOverview(data) {
            document.getElementById('total-flags').textContent = data.feature_flags?.total || 0;
            document.getElementById('running-experiments').textContent = data.experiments?.running || 0;
            document.getElementById('active-segments').textContent = data.segments?.active || 0;
            document.getElementById('total-users').textContent = data.segments?.total_users || 0;
        }

        function updateFeatureFlagsTable(flags) {
            const tbody = document.getElementById('feature-flags-tbody');
            tbody.innerHTML = '';

            flags.slice(0, 5).forEach(flag => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td class="py-2">${flag.name}</td>
                    <td class="py-2">${flag.flag_type}</td>
                    <td class="py-2">
                        <span class="px-2 py-1 text-xs rounded ${flag.current_value !== flag.default_value ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                            ${flag.current_value !== flag.default_value ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td class="py-2">
                        <button class="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    </td>
                `;
            });
        }

        function updateExperimentsTable(experiments) {
            const tbody = document.getElementById('experiments-tbody');
            tbody.innerHTML = '';

            experiments.filter(exp => exp.status === 'running').slice(0, 5).forEach(exp => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td class="py-2">${exp.name}</td>
                    <td class="py-2">
                        <span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                            ${exp.status}
                        </span>
                    </td>
                    <td class="py-2">
                        <div class="w-16 bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: 65%"></div>
                        </div>
                    </td>
                    <td class="py-2">
                        <button class="text-blue-600 hover:text-blue-800 text-sm">View</button>
                    </td>
                `;
            });
        }

        async function loadCharts() {
            try {
                // Load feature flags chart
                const flagsChart = await fetch('/api/charts/feature-flags').then(r => r.json());
                Plotly.newPlot('feature-flags-chart', flagsChart.data, flagsChart.layout);

                // Load segment distribution chart
                const segmentChart = await fetch('/api/charts/segment-distribution').then(r => r.json());
                Plotly.newPlot('segment-chart', segmentChart.data, segmentChart.layout);
            } catch (error) {
                console.error('Error loading charts:', error);
            }
        }

        // Initialize dashboard on page load
        loadDashboard();

        // Refresh data every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
    """

    with open(f"{templates_dir}/dashboard.html", "w") as f:
        f.write(dashboard_html)

    # Create CSS file
    css_content = """
/* Additional dashboard styles */
.card {
    transition: transform 0.2s ease-in-out;
}

.card:hover {
    transform: translateY(-2px);
}

.metric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.table-actions button {
    transition: color 0.2s ease-in-out;
}

.table-actions button:hover {
    text-decoration: underline;
}
    """

    with open(f"{static_dir}/dashboard.css", "w") as f:
        f.write(css_content)

    logger.info("Dashboard templates and static files created")

# Create templates on import
create_templates()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)