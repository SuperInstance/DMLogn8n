"""
Main Health Check Orchestration Service

Coordinates all health check operations, scheduling, and automated healing procedures.
Provides centralized health monitoring for the DMLogn8n multi-agent platform.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .checks.component_checks import ComponentChecker
from .checks.service_checks import ServiceChecker
from .checks.system_checks import SystemChecker
from .checks.business_checks import BusinessChecker
from .healers.service_healer import ServiceHealer
from .healers.resource_healer import ResourceHealer
from .healers.data_healer import DataHealer
from .scoring import HealthScorer
from .utils.dependency_graph import DependencyGraph
from .utils.config import HealthConfig
from .utils.storage import HealthStorage
from .utils.alerting import AlertManager

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class CheckLevel(Enum):
    """Health check levels"""
    COMPONENT = "component"
    SERVICE = "service"
    SYSTEM = "system"
    BUSINESS = "business"

@dataclass
class HealthCheckResult:
    """Individual health check result"""
    check_id: str
    check_name: str
    level: CheckLevel
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    healing_actions: List[str] = field(default_factory=list)

@dataclass
class SystemHealthReport:
    """Complete system health report"""
    overall_status: HealthStatus
    overall_score: float
    timestamp: datetime
    check_results: List[HealthCheckResult]
    dependency_issues: List[Dict[str, Any]]
    healing_actions_taken: List[Dict[str, Any]]
    trends: Dict[str, Any]
    sla_compliance: Dict[str, Any]
    recommendations: List[str]

class HealthService:
    """Main health check orchestration service"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize health service"""
        self.logger = logging.getLogger(__name__)
        self.config = HealthConfig(config_path)
        self.storage = HealthStorage(self.config.storage)
        self.alert_manager = AlertManager(self.config.alerting)
        self.dependency_graph = DependencyGraph()
        self.health_scorer = HealthScorer(self.config.scoring)

        # Initialize checkers
        self.component_checker = ComponentChecker(self.config.checks.component)
        self.service_checker = ServiceChecker(self.config.checks.service)
        self.system_checker = SystemChecker(self.config.checks.system)
        self.business_checker = BusinessChecker(self.config.checks.business)

        # Initialize healers
        self.service_healer = ServiceHealer(self.config.healing.service)
        self.resource_healer = ResourceHealer(self.config.healing.resource)
        self.data_healer = DataHealer(self.config.healing.data)

        # Scheduling and execution
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.active_checks: Dict[str, asyncio.Task] = {}

        # Health history and trends
        self.health_history: List[Dict[str, Any]] = []
        self.trend_data: Dict[str, List[Dict[str, Any]]] = {}

        # Service registry
        self.registered_services: Dict[str, Dict[str, Any]] = {}
        self.service_dependencies: Dict[str, List[str]] = {}

        self.logger.info("Health service initialized")

    async def start(self) -> None:
        """Start health service"""
        if self.scheduler_running:
            return

        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        # Load service registry and dependencies
        await self._load_service_registry()
        self._build_dependency_graph()

        # Perform initial health check
        await self.run_full_health_check()

        self.logger.info("Health service started")

    async def stop(self) -> None:
        """Stop health service"""
        self.scheduler_running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)

        # Cancel active checks
        for task in self.active_checks.values():
            task.cancel()

        self.executor.shutdown(wait=True)
        self.logger.info("Health service stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduling loop"""
        while self.scheduler_running:
            try:
                # Run different check types on different schedules
                current_time = datetime.now()

                # Component checks (every 30 seconds)
                if self._should_run_check("component", current_time, 30):
                    asyncio.run(self.run_component_checks())

                # Service checks (every 1 minute)
                if self._should_run_check("service", current_time, 60):
                    asyncio.run(self.run_service_checks())

                # System checks (every 2 minutes)
                if self._should_run_check("system", current_time, 120):
                    asyncio.run(self.run_system_checks())

                # Business checks (every 5 minutes)
                if self._should_run_check("business", current_time, 300):
                    asyncio.run(self.run_business_checks())

                # Full health check (every 10 minutes)
                if self._should_run_check("full", current_time, 600):
                    asyncio.run(self.run_full_health_check())

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(30)  # Wait longer on error

    def _should_run_check(self, check_type: str, current_time: datetime, interval_seconds: int) -> bool:
        """Check if a specific check type should run"""
        last_run_key = f"last_run_{check_type}"
        last_run = getattr(self, last_run_key, None)

        if not last_run:
            setattr(self, last_run_key, current_time)
            return True

        if (current_time - last_run).total_seconds() >= interval_seconds:
            setattr(self, last_run_key, current_time)
            return True

        return False

    async def run_component_checks(self) -> List[HealthCheckResult]:
        """Run component-level health checks"""
        self.logger.debug("Running component health checks")

        tasks = []
        for component_id, component_config in self.config.checks.component.items():
            task = asyncio.create_task(
                self._run_single_check(
                    self.component_checker,
                    component_id,
                    CheckLevel.COMPONENT
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and trigger healing if needed
        processed_results = []
        for result in results:
            if isinstance(result, HealthCheckResult):
                processed_results.append(result)
                await self._handle_check_result(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Component check error: {result}")

        return processed_results

    async def run_service_checks(self) -> List[HealthCheckResult]:
        """Run service-level health checks"""
        self.logger.debug("Running service health checks")

        tasks = []
        for service_id in self.registered_services.keys():
            task = asyncio.create_task(
                self._run_single_check(
                    self.service_checker,
                    service_id,
                    CheckLevel.SERVICE
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, HealthCheckResult):
                processed_results.append(result)
                await self._handle_check_result(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Service check error: {result}")

        return processed_results

    async def run_system_checks(self) -> List[HealthCheckResult]:
        """Run system-level health checks"""
        self.logger.debug("Running system health checks")

        tasks = []
        for check_id, check_config in self.config.checks.system.items():
            task = asyncio.create_task(
                self._run_single_check(
                    self.system_checker,
                    check_id,
                    CheckLevel.SYSTEM
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, HealthCheckResult):
                processed_results.append(result)
                await self._handle_check_result(result)
            elif isinstance(result, Exception):
                self.logger.error(f"System check error: {result}")

        return processed_results

    async def run_business_checks(self) -> List[HealthCheckResult]:
        """Run business logic health checks"""
        self.logger.debug("Running business health checks")

        tasks = []
        for check_id, check_config in self.config.checks.business.items():
            task = asyncio.create_task(
                self._run_single_check(
                    self.business_checker,
                    check_id,
                    CheckLevel.BUSINESS
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, HealthCheckResult):
                processed_results.append(result)
                await self._handle_check_result(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Business check error: {result}")

        return processed_results

    async def run_full_health_check(self) -> SystemHealthReport:
        """Run comprehensive health check"""
        self.logger.info("Running full health check")

        start_time = time.time()

        # Run all check types
        component_results = await self.run_component_checks()
        service_results = await self.run_service_checks()
        system_results = await self.run_system_checks()
        business_results = await self.run_business_checks()

        all_results = component_results + service_results + system_results + business_results

        # Check for dependency issues
        dependency_issues = self._check_dependency_health(all_results)

        # Calculate overall health
        overall_status, overall_score = self.health_scorer.calculate_overall_health(all_results)

        # Generate trends
        trends = self._generate_health_trends()

        # Check SLA compliance
        sla_compliance = self._check_sla_compliance(all_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(all_results, dependency_issues)

        # Create report
        report = SystemHealthReport(
            overall_status=overall_status,
            overall_score=overall_score,
            timestamp=datetime.now(),
            check_results=all_results,
            dependency_issues=dependency_issues,
            healing_actions_taken=self._get_recent_healing_actions(),
            trends=trends,
            sla_compliance=sla_compliance,
            recommendations=recommendations
        )

        # Store report
        await self.storage.store_health_report(report)

        # Store in history
        self.health_history.append({
            "timestamp": report.timestamp.isoformat(),
            "status": overall_status.value,
            "score": overall_score,
            "check_count": len(all_results),
            "critical_issues": len([r for r in all_results if r.status == HealthStatus.CRITICAL])
        })

        # Keep history size manageable
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-500:]

        # Send alerts if needed
        await self._send_alerts(report)

        duration = time.time() - start_time
        self.logger.info(f"Full health check completed in {duration:.2f}s - Status: {overall_status.value}")

        return report

    async def _run_single_check(self, checker, check_id: str, level: CheckLevel) -> HealthCheckResult:
        """Run a single health check"""
        start_time = time.time()

        try:
            # Get dependencies for this check
            dependencies = self.dependency_graph.get_dependencies(check_id)

            # Check if dependencies are healthy
            if dependencies:
                dep_status = await self._check_dependencies_health(dependencies)
                if dep_status != HealthStatus.HEALTHY:
                    return HealthCheckResult(
                        check_id=check_id,
                        check_name=f"{level.value.title()} Check: {check_id}",
                        level=level,
                        status=HealthStatus.DEGRADED,
                        message=f"Dependencies not healthy: {', '.join(dependencies)}",
                        dependencies=dependencies,
                        duration_ms=(time.time() - start_time) * 1000
                    )

            # Run the actual check
            result = await checker.check_health(check_id)
            result.duration_ms = (time.time() - start_time) * 1000
            result.dependencies = dependencies

            return result

        except Exception as e:
            self.logger.error(f"Check {check_id} failed: {e}")
            return HealthCheckResult(
                check_id=check_id,
                check_name=f"{level.value.title()} Check: {check_id}",
                level=level,
                status=HealthStatus.CRITICAL,
                message=f"Check execution failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )

    async def _handle_check_result(self, result: HealthCheckResult) -> None:
        """Handle individual check result and trigger healing if needed"""
        # Store result
        await self.storage.store_check_result(result)

        # Update trend data
        if result.check_id not in self.trend_data:
            self.trend_data[result.check_id] = []

        self.trend_data[result.check_id].append({
            "timestamp": result.timestamp.isoformat(),
            "status": result.status.value,
            "score": result.metrics.get("score", 0.0),
            "duration_ms": result.duration_ms
        })

        # Keep trend data size manageable
        if len(self.trend_data[result.check_id]) > 100:
            self.trend_data[result.check_id] = self.trend_data[result.check_id][-50:]

        # Trigger healing if needed
        if result.status in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]:
            await self._trigger_healing(result)

    async def _trigger_healing(self, result: HealthCheckResult) -> None:
        """Trigger automated healing based on check result"""
        try:
            healing_actions = []

            # Service-level healing
            if result.level == CheckLevel.SERVICE:
                actions = await self.service_healer.heal_service(result)
                healing_actions.extend(actions)

            # Resource-level healing
            if result.level == CheckLevel.SYSTEM:
                actions = await self.resource_healer.heal_system(result)
                healing_actions.extend(actions)

            # Data-level healing
            if "data" in result.check_id.lower() or "database" in result.check_id.lower():
                actions = await self.data_healer.heal_data(result)
                healing_actions.extend(actions)

            # Store healing actions
            for action in healing_actions:
                await self.storage.store_healing_action(action)

            self.logger.info(f"Triggered {len(healing_actions)} healing actions for {result.check_id}")

        except Exception as e:
            self.logger.error(f"Healing failed for {result.check_id}: {e}")

    def _check_dependency_health(self, dependencies: List[str]) -> HealthStatus:
        """Check health of dependencies"""
        if not dependencies:
            return HealthStatus.HEALTHY

        # Get latest results for dependencies
        dependency_statuses = []
        for dep_id in dependencies:
            latest_result = self._get_latest_check_result(dep_id)
            if latest_result:
                dependency_statuses.append(latest_result.status)
            else:
                dependency_statuses.append(HealthStatus.UNKNOWN)

        # Determine overall dependency health
        if any(status == HealthStatus.CRITICAL for status in dependency_statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.DEGRADED for status in dependency_statuses):
            return HealthStatus.DEGRADED
        elif any(status == HealthStatus.WARNING for status in dependency_statuses):
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in dependency_statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def _get_latest_check_result(self, check_id: str) -> Optional[HealthCheckResult]:
        """Get latest check result for a specific check"""
        # This would typically query the storage
        # For now, return None as placeholder
        return None

    def _check_dependency_health(self, all_results: List[HealthCheckResult]) -> List[Dict[str, Any]]:
        """Check for dependency-related issues"""
        issues = []

        for result in all_results:
            if result.dependencies:
                for dep_id in result.dependencies:
                    dep_result = next((r for r in all_results if r.check_id == dep_id), None)
                    if dep_result and dep_result.status != HealthStatus.HEALTHY:
                        issues.append({
                            "check_id": result.check_id,
                            "dependency": dep_id,
                            "dependency_status": dep_result.status.value,
                            "impact": "Dependent service may be affected",
                            "severity": "high" if dep_result.status == HealthStatus.CRITICAL else "medium"
                        })

        return issues

    def _generate_health_trends(self) -> Dict[str, Any]:
        """Generate health trend analysis"""
        trends = {}

        for check_id, history in self.trend_data.items():
            if len(history) < 2:
                continue

            # Calculate trend direction
            recent_scores = [h["score"] for h in history[-10:]]
            older_scores = [h["score"] for h in history[-20:-10]] if len(history) >= 20 else recent_scores

            if recent_scores and older_scores:
                recent_avg = sum(recent_scores) / len(recent_scores)
                older_avg = sum(older_scores) / len(older_scores)

                trend_direction = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"

                trends[check_id] = {
                    "direction": trend_direction,
                    "recent_score": recent_avg,
                    "change_percentage": ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0,
                    "data_points": len(history)
                }

        return trends

    def _check_sla_compliance(self, all_results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Check SLA compliance"""
        compliance = {
            "overall_compliant": True,
            "uptime_percentage": 0.0,
            "response_time_compliant": True,
            "error_rate_compliant": True,
            "violations": []
        }

        # Calculate uptime based on healthy services
        total_checks = len(all_results)
        healthy_checks = len([r for r in all_results if r.status == HealthStatus.HEALTHY])

        if total_checks > 0:
            compliance["uptime_percentage"] = (healthy_checks / total_checks) * 100

        # Check SLA thresholds
        if compliance["uptime_percentage"] < self.config.sla.min_uptime_percentage:
            compliance["overall_compliant"] = False
            compliance["violations"].append({
                "type": "uptime",
                "threshold": self.config.sla.min_uptime_percentage,
                "actual": compliance["uptime_percentage"]
            })

        # Check response times
        response_times = [r.duration_ms for r in all_results if r.duration_ms > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time > self.config.sla.max_response_time_ms:
                compliance["response_time_compliant"] = False
                compliance["overall_compliant"] = False
                compliance["violations"].append({
                    "type": "response_time",
                    "threshold": self.config.sla.max_response_time_ms,
                    "actual": avg_response_time
                })

        # Check error rates
        error_count = len([r for r in all_results if r.status in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]])
        error_rate = (error_count / total_checks) * 100 if total_checks > 0 else 0

        if error_rate > self.config.sla.max_error_rate_percentage:
            compliance["error_rate_compliant"] = False
            compliance["overall_compliant"] = False
            compliance["violations"].append({
                "type": "error_rate",
                "threshold": self.config.sla.max_error_rate_percentage,
                "actual": error_rate
            })

        return compliance

    def _generate_recommendations(self, all_results: List[HealthCheckResult], dependency_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        # Critical issues
        critical_issues = [r for r in all_results if r.status == HealthStatus.CRITICAL]
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical issues immediately")

        # Performance issues
        slow_checks = [r for r in all_results if r.duration_ms > self.config.performance.thresholds.slow_response_ms]
        if slow_checks:
            recommendations.append(f"Optimize {len(slow_checks)} slow-performing checks")

        # Dependency issues
        if dependency_issues:
            recommendations.append(f"Resolve {len(dependency_issues)} dependency issues")

        # Resource utilization
        high_resource_checks = [r for r in all_results if r.metrics.get("cpu_usage", 0) > 80 or r.metrics.get("memory_usage", 0) > 80]
        if high_resource_checks:
            recommendations.append("Monitor and optimize high resource utilization")

        # Trending issues
        declining_trends = [k for k, v in self._generate_health_trends().items() if v["direction"] == "declining"]
        if declining_trends:
            recommendations.append(f"Investigate declining health trends in {len(declining_trends)} components")

        return recommendations

    def _get_recent_healing_actions(self) -> List[Dict[str, Any]]:
        """Get recent healing actions"""
        # This would typically query the storage for recent actions
        # For now, return empty list as placeholder
        return []

    async def _send_alerts(self, report: SystemHealthReport) -> None:
        """Send alerts based on health report"""
        try:
            # Critical alerts
            if report.overall_status == HealthStatus.CRITICAL:
                await self.alert_manager.send_critical_alert(
                    "System Critical Health Alert",
                    f"System health is critical. Score: {report.overall_score:.1f}",
                    {"report": report}
                )

            # Warning alerts
            elif report.overall_status == HealthStatus.WARNING:
                await self.alert_manager.send_warning_alert(
                    "System Health Warning",
                    f"System health degraded. Score: {report.overall_score:.1f}",
                    {"report": report}
                )

            # SLA violation alerts
            if not report.sla_compliance["overall_compliant"]:
                await self.alert_manager.send_warning_alert(
                    "SLA Violation Alert",
                    f"SLA violations detected: {len(report.sla_compliance['violations'])}",
                    {"sla_compliance": report.sla_compliance}
                )

        except Exception as e:
            self.logger.error(f"Failed to send alerts: {e}")

    async def _load_service_registry(self) -> None:
        """Load service registry and dependencies"""
        try:
            # Load from configuration or discovery service
            services = await self._discover_services()
            self.registered_services = {s["id"]: s for s in services}

            # Load dependencies
            dependencies = await self._load_dependencies()
            self.service_dependencies = dependencies

        except Exception as e:
            self.logger.error(f"Failed to load service registry: {e}")

    async def _discover_services(self) -> List[Dict[str, Any]]:
        """Discover available services"""
        # This would integrate with service discovery
        # For now, return default services
        return [
            {
                "id": "api-gateway",
                "name": "API Gateway",
                "type": "gateway",
                "endpoint": "http://localhost:8080/health",
                "critical": True
            },
            {
                "id": "character-portal",
                "name": "Character Portal Service",
                "type": "service",
                "endpoint": "http://localhost:8081/health",
                "critical": True
            },
            {
                "id": "dialogue-service",
                "name": "Dialogue Service",
                "type": "service",
                "endpoint": "http://localhost:8082/health",
                "critical": True
            },
            {
                "id": "n8n-workflow",
                "name": "N8N Workflow Engine",
                "type": "workflow",
                "endpoint": "http://localhost:5678/healthz",
                "critical": True
            },
            {
                "id": "database",
                "name": "Database Service",
                "type": "database",
                "endpoint": None,
                "critical": True
            },
            {
                "id": "message-queue",
                "name": "Message Queue",
                "type": "queue",
                "endpoint": "http://localhost:15672/api/healthchecks/node",
                "critical": True
            },
            {
                "id": "cache",
                "name": "Cache Service",
                "type": "cache",
                "endpoint": "http://localhost:6379",
                "critical": False
            }
        ]

    async def _load_dependencies(self) -> Dict[str, List[str]]:
        """Load service dependencies"""
        # Define service dependencies
        return {
            "character-portal": ["database", "cache"],
            "dialogue-service": ["database", "cache", "message-queue"],
            "n8n-workflow": ["database", "message-queue"],
            "api-gateway": ["character-portal", "dialogue-service", "n8n-workflow"]
        }

    def _build_dependency_graph(self) -> None:
        """Build dependency graph"""
        for service_id, dependencies in self.service_dependencies.items():
            for dep_id in dependencies:
                self.dependency_graph.add_dependency(service_id, dep_id)

    # API Methods

    async def get_health_status(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current health status"""
        if service_id:
            # Get specific service health
            report = await self.run_full_health_check()
            service_result = next((r for r in report.check_results if r.check_id == service_id), None)

            if service_result:
                return {
                    "service_id": service_id,
                    "status": service_result.status.value,
                    "score": service_result.metrics.get("score", 0.0),
                    "message": service_result.message,
                    "details": service_result.details,
                    "timestamp": service_result.timestamp.isoformat()
                }
            else:
                return {"service_id": service_id, "status": "unknown", "message": "Service not found"}
        else:
            # Get overall system health
            report = await self.run_full_health_check()
            return {
                "overall_status": report.overall_status.value,
                "overall_score": report.overall_score,
                "timestamp": report.timestamp.isoformat(),
                "services": {
                    r.check_id: {
                        "status": r.status.value,
                        "score": r.metrics.get("score", 0.0),
                        "message": r.message
                    }
                    for r in report.check_results
                },
                "dependency_issues": report.dependency_issues,
                "recommendations": report.recommendations
            }

    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
        ]

    async def trigger_manual_check(self, check_id: Optional[str] = None) -> Dict[str, Any]:
        """Trigger manual health check"""
        if check_id:
            # Run specific check
            # Determine check level and run appropriate checker
            if check_id in self.registered_services:
                result = await self._run_single_check(
                    self.service_checker,
                    check_id,
                    CheckLevel.SERVICE
                )
            else:
                result = await self._run_single_check(
                    self.system_checker,
                    check_id,
                    CheckLevel.SYSTEM
                )

            await self._handle_check_result(result)

            return {
                "check_id": check_id,
                "status": result.status.value,
                "message": result.message,
                "timestamp": result.timestamp.isoformat()
            }
        else:
            # Run full health check
            report = await self.run_full_health_check()

            return {
                "overall_status": report.overall_status.value,
                "overall_score": report.overall_score,
                "check_count": len(report.check_results),
                "timestamp": report.timestamp.isoformat()
            }

    async def register_service(self, service_config: Dict[str, Any]) -> bool:
        """Register a new service for health monitoring"""
        try:
            service_id = service_config["id"]
            self.registered_services[service_id] = service_config

            # Update dependencies if provided
            if "dependencies" in service_config:
                self.service_dependencies[service_id] = service_config["dependencies"]
                for dep_id in service_config["dependencies"]:
                    self.dependency_graph.add_dependency(service_id, dep_id)

            self.logger.info(f"Registered service: {service_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register service: {e}")
            return False

    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from health monitoring"""
        try:
            if service_id in self.registered_services:
                del self.registered_services[service_id]

            if service_id in self.service_dependencies:
                del self.service_dependencies[service_id]
                self.dependency_graph.remove_service(service_id)

            self.logger.info(f"Unregistered service: {service_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister service: {e}")
            return False