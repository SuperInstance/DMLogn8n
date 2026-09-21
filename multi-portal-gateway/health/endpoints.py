"""
Health Check HTTP Endpoints

HTTP API endpoints for health monitoring, status queries, and management.
Provides RESTful interface for external monitoring systems.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .health_service import HealthService, HealthStatus, CheckLevel
from .scoring import HealthScorer
from .utils.config import HealthConfig

class HealthCheckRequest(BaseModel):
    """Request model for triggering health checks"""
    check_id: Optional[str] = None
    check_level: Optional[str] = None
    force: bool = False

class ServiceRegistrationRequest(BaseModel):
    """Request model for service registration"""
    service_id: str
    name: str
    type: str
    endpoint: str
    critical: bool = True
    dependencies: List[str] = []
    config: Dict[str, Any] = {}

class HealthEndpoints:
    """HTTP API endpoints for health monitoring"""

    def __init__(self, health_service: HealthService):
        self.health_service = health_service
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(
            title="DMLogn8n Health Monitor",
            description="Health monitoring and automated healing system",
            version="1.0.0"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Root endpoint with basic info"""
            return """
            <html>
                <head><title>DMLogn8n Health Monitor</title></head>
                <body>
                    <h1>DMLogn8n Health Monitor</h1>
                    <p>Health monitoring and automated healing system</p>
                    <ul>
                        <li><a href="/health">System Health</a></li>
                        <li><a href="/health/detailed">Detailed Health Report</a></li>
                        <li><a href="/docs">API Documentation</a></li>
                    </ul>
                </body>
            </html>
            """

        @self.app.get("/health")
        async def get_health_overview():
            """Get overall system health status"""
            try:
                health_status = await self.health_service.get_health_status()
                return JSONResponse(content=health_status)
            except Exception as e:
                self.logger.error(f"Health overview endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/detailed")
        async def get_detailed_health():
            """Get detailed health report"""
            try:
                report = await self.health_service.run_full_health_check()

                # Convert to serializable format
                detailed_report = {
                    "overall_status": report.overall_status.value,
                    "overall_score": report.overall_score,
                    "timestamp": report.timestamp.isoformat(),
                    "check_results": [
                        {
                            "check_id": r.check_id,
                            "check_name": r.check_name,
                            "level": r.level.value,
                            "status": r.status.value,
                            "message": r.message,
                            "details": r.details,
                            "metrics": r.metrics,
                            "timestamp": r.timestamp.isoformat(),
                            "duration_ms": r.duration_ms
                        }
                        for r in report.check_results
                    ],
                    "dependency_issues": report.dependency_issues,
                    "healing_actions_taken": report.healing_actions_taken,
                    "trends": report.trends,
                    "sla_compliance": report.sla_compliance,
                    "recommendations": report.recommendations
                }

                return JSONResponse(content=detailed_report)
            except Exception as e:
                self.logger.error(f"Detailed health endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/service/{service_id}")
        async def get_service_health(service_id: str = Path(..., description="Service ID")):
            """Get health status for specific service"""
            try:
                health_status = await self.health_service.get_health_status(service_id)

                if "error" in health_status and health_status.get("service_id") == service_id:
                    raise HTTPException(status_code=404, detail=health_status.get("message"))

                return JSONResponse(content=health_status)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Service health endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/level/{level}")
        async def get_health_by_level(level: str = Path(..., description="Health check level")):
            """Get health status by level (component, service, system, business)"""
            try:
                if level not in ["component", "service", "system", "business"]:
                    raise HTTPException(status_code=400, detail="Invalid level. Must be: component, service, system, or business")

                # Get full health report and filter by level
                report = await self.health_service.run_full_health_check()
                level_results = [r for r in report.check_results if r.level.value == level]

                return JSONResponse(content={
                    "level": level,
                    "timestamp": report.timestamp.isoformat(),
                    "check_count": len(level_results),
                    "results": [
                        {
                            "check_id": r.check_id,
                            "check_name": r.check_name,
                            "status": r.status.value,
                            "message": r.message,
                            "score": r.metrics.get("score", 0),
                            "details": r.details,
                            "metrics": r.metrics
                        }
                        for r in level_results
                    ]
                })
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Health level endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/health/check")
        async def trigger_health_check(request: HealthCheckRequest, background_tasks: BackgroundTasks):
            """Trigger manual health check"""
            try:
                if request.check_id:
                    result = await self.health_service.trigger_manual_check(request.check_id)
                else:
                    result = await self.health_service.trigger_manual_check()

                return JSONResponse(content={
                    "message": "Health check triggered",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Manual health check endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/history")
        async def get_health_history(
            hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve")
        ):
            """Get health history"""
            try:
                history = await self.health_service.get_health_history(hours)
                return JSONResponse(content={
                    "hours": hours,
                    "timestamp": datetime.now().isoformat(),
                    "history": history,
                    "count": len(history)
                })
            except Exception as e:
                self.logger.error(f"Health history endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/score")
        async def get_health_scores():
            """Get current health scores"""
            try:
                report = await self.health_service.run_full_health_check()
                scorer = HealthScorer(self.health_service.config.scoring)

                # Calculate scores for each level
                component_score = scorer.calculate_component_score(report.check_results)
                service_score = scorer.calculate_service_score(report.check_results)
                system_score = scorer.calculate_system_score(report.check_results)
                business_score = scorer.calculate_business_score(report.check_results)

                return JSONResponse(content={
                    "overall": {
                        "score": report.overall_score,
                        "status": report.overall_status.value
                    },
                    "component": {
                        "score": component_score.score,
                        "status": component_score.status.value,
                        "trend": component_score.trend.value,
                        "confidence": component_score.confidence
                    },
                    "service": {
                        "score": service_score.score,
                        "status": service_score.status.value,
                        "trend": service_score.trend.value,
                        "confidence": service_score.confidence
                    },
                    "system": {
                        "score": system_score.score,
                        "status": system_score.status.value,
                        "trend": system_score.trend.value,
                        "confidence": system_score.confidence
                    },
                    "business": {
                        "score": business_score.score,
                        "status": business_score.status.value,
                        "trend": business_score.trend.value,
                        "confidence": business_score.confidence
                    },
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Health scores endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/trends")
        async def get_health_trends(
            hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze")
        ):
            """Get health trend analysis"""
            try:
                history = await self.health_service.get_health_history(hours)
                scorer = HealthScorer(self.health_service.config.scoring)

                # Predict trends
                prediction = scorer.predict_health_trend(history)

                # Analyze volatility
                volatility = scorer.analyze_score_volatility(history)

                return JSONResponse(content={
                    "analysis_hours": hours,
                    "prediction": prediction,
                    "volatility": volatility,
                    "data_points": len(history),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Health trends endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/dependencies")
        async def get_dependency_health():
            """Get dependency health information"""
            try:
                report = await self.health_service.run_full_health_check()

                return JSONResponse(content={
                    "timestamp": report.timestamp.isoformat(),
                    "dependency_issues": report.dependency_issues,
                    "dependency_graph": self._build_dependency_graph_info(report.check_results)
                })
            except Exception as e:
                self.logger.error(f"Dependency health endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/sla")
        async def get_sla_compliance():
            """Get SLA compliance information"""
            try:
                report = await self.health_service.run_full_health_check()

                return JSONResponse(content={
                    "timestamp": report.timestamp.isoformat(),
                    "sla_compliance": report.sla_compliance,
                    "uptime_percentage": report.sla_compliance.get("uptime_percentage", 0),
                    "response_time_compliant": report.sla_compliance.get("response_time_compliant", False),
                    "error_rate_compliant": report.sla_compliance.get("error_rate_compliant", False),
                    "violations": report.sla_compliance.get("violations", [])
                })
            except Exception as e:
                self.logger.error(f"SLA compliance endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/health/services/register")
        async def register_service(request: ServiceRegistrationRequest):
            """Register a new service for health monitoring"""
            try:
                service_config = {
                    "id": request.service_id,
                    "name": request.name,
                    "type": request.type,
                    "endpoint": request.endpoint,
                    "critical": request.critical,
                    "dependencies": request.dependencies,
                    **request.config
                }

                success = await self.health_service.register_service(service_config)

                if success:
                    return JSONResponse(content={
                        "message": f"Service {request.service_id} registered successfully",
                        "service_id": request.service_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    raise HTTPException(status_code=400, detail="Failed to register service")
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Service registration endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/health/services/{service_id}")
        async def unregister_service(service_id: str = Path(..., description="Service ID")):
            """Unregister a service from health monitoring"""
            try:
                success = await self.health_service.unregister_service(service_id)

                if success:
                    return JSONResponse(content={
                        "message": f"Service {service_id} unregistered successfully",
                        "service_id": service_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    raise HTTPException(status_code=404, detail="Service not found or failed to unregister")
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Service unregistration endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/services")
        async def get_registered_services():
            """Get list of registered services"""
            try:
                services = self.health_service.registered_services
                dependencies = self.health_service.service_dependencies

                services_info = []
                for service_id, config in services.items():
                    services_info.append({
                        "id": service_id,
                        "name": config.get("name", service_id),
                        "type": config.get("type", "unknown"),
                        "endpoint": config.get("endpoint"),
                        "critical": config.get("critical", False),
                        "dependencies": dependencies.get(service_id, [])
                    })

                return JSONResponse(content={
                    "services": services_info,
                    "count": len(services_info),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Registered services endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/recommendations")
        async def get_health_recommendations():
            """Get health improvement recommendations"""
            try:
                report = await self.health_service.run_full_health_check()
                scorer = HealthScorer(self.health_service.config.scoring)

                # Generate detailed recommendations
                recommendations = scorer.generate_health_summary(report.check_results)

                return JSONResponse(content={
                    "recommendations": recommendations["recommendations"],
                    "summary": recommendations["summary"],
                    "overall_score": recommendations["overall_score"],
                    "issue_counts": recommendations["issue_counts"],
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Health recommendations endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/metrics")
        async def get_metrics():
            """Get Prometheus-style metrics"""
            try:
                report = await self.health_service.run_full_health_check()

                # Generate Prometheus metrics format
                metrics_lines = [
                    "# HELP dmlogn8n_health_score Overall health score",
                    "# TYPE dmlogn8n_health_score gauge",
                    f"dmlogn8n_health_score {report.overall_score}",
                    "",
                    "# HELP dmlogn8n_health_status Overall health status (1=healthy, 0.75=warning, 0.5=degraded, 0=critical)",
                    "# TYPE dmlogn8n_health_status gauge",
                    f"dmlogn8n_health_status {self._status_to_metric_value(report.overall_status)}",
                    "",
                    "# HELP dmlogn8n_health_check_result Health check result by service",
                    "# TYPE dmlogn8n_health_check_result gauge"
                ]

                for result in report.check_results:
                    metrics_lines.append(
                        f'dmlogn8n_health_check_result{{service="{result.check_id}",level="{result.level.value}"}} {self._status_to_metric_value(result.status)}'
                    )

                metrics_text = "\n".join(metrics_lines)

                return JSONResponse(content={
                    "metrics": metrics_text,
                    "format": "prometheus",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Metrics endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health/summary")
        async def get_health_summary():
            """Get concise health summary"""
            try:
                report = await self.health_service.run_full_health_check()
                scorer = HealthScorer(self.health_service.config.scoring)

                summary = scorer.generate_health_summary(report.check_results)

                return JSONResponse(content=summary)
            except Exception as e:
                self.logger.error(f"Health summary endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _build_dependency_graph_info(self, check_results: List) -> Dict[str, Any]:
        """Build dependency graph information"""
        nodes = []
        edges = []

        for result in check_results:
            # Add node for each service
            nodes.append({
                "id": result.check_id,
                "name": result.check_name,
                "status": result.status.value,
                "level": result.level.value
            })

            # Add edges for dependencies
            for dep in result.dependencies:
                edges.append({
                    "from": result.check_id,
                    "to": dep,
                    "status": "healthy"  # Would need to check actual dependency health
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    def _status_to_metric_value(self, status: HealthStatus) -> float:
        """Convert health status to metric value"""
        status_map = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.WARNING: 0.75,
            HealthStatus.DEGRADED: 0.5,
            HealthStatus.CRITICAL: 0.0,
            HealthStatus.UNKNOWN: 0.25
        }
        return status_map.get(status, 0.25)

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app