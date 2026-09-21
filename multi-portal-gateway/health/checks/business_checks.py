"""
Business-Level Health Checks

Implements health checks for business logic and application metrics like
user activity, game sessions, error rates, and revenue metrics.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..health_service import HealthCheckResult, HealthStatus

class BusinessChecker:
    """Business-level health checker"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_health(self, check_id: str) -> HealthCheckResult:
        """Check health of a specific business metric"""
        check_method = getattr(self, f"_check_{check_id.replace('-', '_')}", None)

        if check_method:
            return await check_method()
        else:
            return HealthCheckResult(
                check_id=check_id,
                check_name=f"Business Check: {check_id}",
                level="business",
                status=HealthStatus.UNKNOWN,
                message=f"Unknown business check: {check_id}"
            )

    async def _check_user_activity(self) -> HealthCheckResult:
        """Check user activity metrics"""
        start_time = datetime.now()

        try:
            activity_config = self.config.get("user_activity", {})
            api_endpoint = activity_config.get("api_endpoint")
            timeout = activity_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_user_activity_metrics()
            else:
                metrics = await self._fetch_user_activity_metrics(api_endpoint, timeout)

            # Calculate health score based on user activity
            score = self._calculate_user_activity_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="user-activity",
                check_name="User Activity Check",
                level="business",
                status=status,
                message=f"User activity check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "active_users": metrics.get("active_users_24h", 0),
                    "new_users_today": metrics.get("new_users_today", 0),
                    "user_engagement_rate": metrics.get("engagement_rate", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"User activity check failed: {e}")
            return HealthCheckResult(
                check_id="user-activity",
                check_name="User Activity Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"User activity check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_game_sessions(self) -> HealthCheckResult:
        """Check active game sessions"""
        start_time = datetime.now()

        try:
            sessions_config = self.config.get("game_sessions", {})
            api_endpoint = sessions_config.get("api_endpoint")
            timeout = sessions_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_game_sessions_metrics()
            else:
                metrics = await self._fetch_game_sessions_metrics(api_endpoint, timeout)

            # Calculate health score based on game sessions
            score = self._calculate_game_sessions_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="game-sessions",
                check_name="Game Sessions Check",
                level="business",
                status=status,
                message=f"Game sessions check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "active_sessions": metrics.get("active_sessions", 0),
                    "average_session_duration": metrics.get("average_session_duration_minutes", 0),
                    "sessions_per_hour": metrics.get("sessions_per_hour", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Game sessions check failed: {e}")
            return HealthCheckResult(
                check_id="game-sessions",
                check_name="Game Sessions Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Game sessions check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_error_rates(self) -> HealthCheckResult:
        """Check application error rates"""
        start_time = datetime.now()

        try:
            error_config = self.config.get("error_rates", {})
            api_endpoint = error_config.get("api_endpoint")
            timeout = error_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_error_metrics()
            else:
                metrics = await self._fetch_error_metrics(api_endpoint, timeout)

            # Calculate health score based on error rates
            score = self._calculate_error_score(metrics)

            # Determine status
            if score >= 90:
                status = HealthStatus.HEALTHY
            elif score >= 75:
                status = HealthStatus.WARNING
            elif score >= 60:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="error-rates",
                check_name="Error Rates Check",
                level="business",
                status=status,
                message=f"Error rates check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "error_rate_5xx": metrics.get("error_rate_5xx", 0),
                    "error_rate_4xx": metrics.get("error_rate_4xx", 0),
                    "total_errors_per_hour": metrics.get("total_errors_per_hour", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Error rates check failed: {e}")
            return HealthCheckResult(
                check_id="error-rates",
                check_name="Error Rates Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Error rates check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_response_times(self) -> HealthCheckResult:
        """Check application response times"""
        start_time = datetime.now()

        try:
            response_config = self.config.get("response_times", {})
            api_endpoint = response_config.get("api_endpoint")
            timeout = response_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_response_time_metrics()
            else:
                metrics = await self._fetch_response_time_metrics(api_endpoint, timeout)

            # Calculate health score based on response times
            score = self._calculate_response_time_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="response-times",
                check_name="Response Times Check",
                level="business",
                status=status,
                message=f"Response times check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "p50_response_time": metrics.get("p50_response_time_ms", 0),
                    "p95_response_time": metrics.get("p95_response_time_ms", 0),
                    "p99_response_time": metrics.get("p99_response_time_ms", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Response times check failed: {e}")
            return HealthCheckResult(
                check_id="response-times",
                check_name="Response Times Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Response times check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_character_generation(self) -> HealthCheckResult:
        """Check character generation service health"""
        start_time = datetime.now()

        try:
            char_config = self.config.get("character_generation", {})
            api_endpoint = char_config.get("api_endpoint")
            timeout = char_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_character_generation_metrics()
            else:
                metrics = await self._fetch_character_generation_metrics(api_endpoint, timeout)

            # Calculate health score based on character generation
            score = self._calculate_character_generation_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="character-generation",
                check_name="Character Generation Check",
                level="business",
                status=status,
                message=f"Character generation check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "characters_generated_today": metrics.get("characters_generated_today", 0),
                    "generation_success_rate": metrics.get("generation_success_rate", 0),
                    "average_generation_time": metrics.get("average_generation_time_seconds", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Character generation check failed: {e}")
            return HealthCheckResult(
                check_id="character-generation",
                check_name="Character Generation Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Character generation check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_dialogue_generation(self) -> HealthCheckResult:
        """Check dialogue generation service health"""
        start_time = datetime.now()

        try:
            dialogue_config = self.config.get("dialogue_generation", {})
            api_endpoint = dialogue_config.get("api_endpoint")
            timeout = dialogue_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_dialogue_generation_metrics()
            else:
                metrics = await self._fetch_dialogue_generation_metrics(api_endpoint, timeout)

            # Calculate health score based on dialogue generation
            score = self._calculate_dialogue_generation_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="dialogue-generation",
                check_name="Dialogue Generation Check",
                level="business",
                status=status,
                message=f"Dialogue generation check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "dialogues_generated_today": metrics.get("dialogues_generated_today", 0),
                    "generation_success_rate": metrics.get("generation_success_rate", 0),
                    "average_generation_time": metrics.get("average_generation_time_seconds", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Dialogue generation check failed: {e}")
            return HealthCheckResult(
                check_id="dialogue-generation",
                check_name="Dialogue Generation Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Dialogue generation check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _check_workflow_execution(self) -> HealthCheckResult:
        """Check N8N workflow execution health"""
        start_time = datetime.now()

        try:
            workflow_config = self.config.get("workflow_execution", {})
            api_endpoint = workflow_config.get("api_endpoint")
            timeout = workflow_config.get("timeout", 10)

            if not api_endpoint:
                # Simulate metrics if no API endpoint configured
                metrics = self._simulate_workflow_metrics()
            else:
                metrics = await self._fetch_workflow_metrics(api_endpoint, timeout)

            # Calculate health score based on workflow execution
            score = self._calculate_workflow_score(metrics)

            # Determine status
            if score >= 85:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id="workflow-execution",
                check_name="Workflow Execution Check",
                level="business",
                status=status,
                message=f"Workflow execution check completed - Score: {score:.1f}%",
                details=metrics,
                metrics={
                    "score": score,
                    "workflows_executed_today": metrics.get("workflows_executed_today", 0),
                    "execution_success_rate": metrics.get("execution_success_rate", 0),
                    "average_execution_time": metrics.get("average_execution_time_seconds", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Workflow execution check failed: {e}")
            return HealthCheckResult(
                check_id="workflow-execution",
                check_name="Workflow Execution Check",
                level="business",
                status=HealthStatus.CRITICAL,
                message=f"Workflow execution check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    # Helper methods for fetching metrics

    async def _fetch_user_activity_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch user activity metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch user activity metrics: {e}")
            return self._simulate_user_activity_metrics()

    async def _fetch_game_sessions_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch game sessions metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch game sessions metrics: {e}")
            return self._simulate_game_sessions_metrics()

    async def _fetch_error_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch error metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch error metrics: {e}")
            return self._simulate_error_metrics()

    async def _fetch_response_time_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch response time metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch response time metrics: {e}")
            return self._simulate_response_time_metrics()

    async def _fetch_character_generation_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch character generation metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch character generation metrics: {e}")
            return self._simulate_character_generation_metrics()

    async def _fetch_dialogue_generation_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch dialogue generation metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch dialogue generation metrics: {e}")
            return self._simulate_dialogue_generation_metrics()

    async def _fetch_workflow_metrics(self, api_endpoint: str, timeout: int) -> Dict[str, Any]:
        """Fetch workflow metrics from API"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(api_endpoint, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        except Exception as e:
            self.logger.warning(f"Failed to fetch workflow metrics: {e}")
            return self._simulate_workflow_metrics()

    # Simulation methods for when APIs are not available

    def _simulate_user_activity_metrics(self) -> Dict[str, Any]:
        """Simulate user activity metrics"""
        import random
        return {
            "active_users_24h": random.randint(150, 300),
            "active_users_1h": random.randint(20, 50),
            "new_users_today": random.randint(5, 20),
            "new_users_this_week": random.randint(30, 80),
            "engagement_rate": random.uniform(60, 95),
            "average_session_duration_minutes": random.uniform(15, 45),
            "user_retention_rate_7d": random.uniform(40, 80),
            "user_retention_rate_30d": random.uniform(20, 60)
        }

    def _simulate_game_sessions_metrics(self) -> Dict[str, Any]:
        """Simulate game sessions metrics"""
        import random
        return {
            "active_sessions": random.randint(10, 30),
            "sessions_today": random.randint(50, 150),
            "sessions_this_week": random.randint(300, 800),
            "average_session_duration_minutes": random.uniform(20, 60),
            "sessions_per_hour": random.randint(5, 15),
            "completion_rate": random.uniform(70, 95),
            "average_players_per_session": random.uniform(2, 6)
        }

    def _simulate_error_metrics(self) -> Dict[str, Any]:
        """Simulate error metrics"""
        import random
        return {
            "error_rate_5xx": random.uniform(0.1, 2.0),
            "error_rate_4xx": random.uniform(1.0, 5.0),
            "total_errors_per_hour": random.randint(5, 50),
            "total_errors_today": random.randint(100, 500),
            "most_common_error": random.choice(["TimeoutError", "ValidationError", "DatabaseError"]),
            "critical_errors_today": random.randint(0, 10)
        }

    def _simulate_response_time_metrics(self) -> Dict[str, Any]:
        """Simulate response time metrics"""
        import random
        return {
            "p50_response_time_ms": random.randint(100, 300),
            "p95_response_time_ms": random.randint(500, 1500),
            "p99_response_time_ms": random.randint(1000, 3000),
            "average_response_time_ms": random.randint(200, 500),
            "slow_requests_per_hour": random.randint(5, 30),
            "timeout_rate": random.uniform(0.1, 1.0)
        }

    def _simulate_character_generation_metrics(self) -> Dict[str, Any]:
        """Simulate character generation metrics"""
        import random
        return {
            "characters_generated_today": random.randint(20, 100),
            "characters_generated_this_week": random.randint(150, 500),
            "generation_success_rate": random.uniform(85, 98),
            "average_generation_time_seconds": random.uniform(2, 8),
            "failed_generations_today": random.randint(0, 10),
            "queue_depth": random.randint(0, 20)
        }

    def _simulate_dialogue_generation_metrics(self) -> Dict[str, Any]:
        """Simulate dialogue generation metrics"""
        import random
        return {
            "dialogues_generated_today": random.randint(100, 500),
            "dialogues_generated_this_week": random.randint(700, 2000),
            "generation_success_rate": random.uniform(90, 99),
            "average_generation_time_seconds": random.uniform(1, 5),
            "failed_generations_today": random.randint(0, 20),
            "queue_depth": random.randint(0, 50)
        }

    def _simulate_workflow_metrics(self) -> Dict[str, Any]:
        """Simulate workflow metrics"""
        import random
        return {
            "workflows_executed_today": random.randint(50, 200),
            "workflows_executed_this_week": random.randint(300, 1000),
            "execution_success_rate": random.uniform(85, 98),
            "average_execution_time_seconds": random.uniform(5, 30),
            "failed_executions_today": random.randint(0, 15),
            "active_workflows": random.randint(10, 25)
        }

    # Score calculation methods

    def _calculate_user_activity_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate user activity health score"""
        score = 100.0

        # Check active users
        active_users = metrics.get("active_users_24h", 0)
        if active_users < 50:
            score -= 30
        elif active_users < 100:
            score -= 15
        elif active_users < 200:
            score -= 5

        # Check engagement rate
        engagement_rate = metrics.get("engagement_rate", 0)
        if engagement_rate < 50:
            score -= 25
        elif engagement_rate < 70:
            score -= 10

        # Check new users
        new_users = metrics.get("new_users_today", 0)
        if new_users < 5:
            score -= 20
        elif new_users < 10:
            score -= 10

        return max(0, min(100, score))

    def _calculate_game_sessions_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate game sessions health score"""
        score = 100.0

        # Check active sessions
        active_sessions = metrics.get("active_sessions", 0)
        if active_sessions < 5:
            score -= 25
        elif active_sessions < 15:
            score -= 10

        # Check completion rate
        completion_rate = metrics.get("completion_rate", 0)
        if completion_rate < 60:
            score -= 30
        elif completion_rate < 80:
            score -= 15

        # Check session duration
        avg_duration = metrics.get("average_session_duration_minutes", 0)
        if avg_duration < 15:
            score -= 20
        elif avg_duration < 25:
            score -= 10

        return max(0, min(100, score))

    def _calculate_error_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate error rate health score"""
        score = 100.0

        # Check 5xx error rate
        error_rate_5xx = metrics.get("error_rate_5xx", 0)
        if error_rate_5xx > 5:
            score -= 50
        elif error_rate_5xx > 2:
            score -= 30
        elif error_rate_5xx > 1:
            score -= 15
        elif error_rate_5xx > 0.5:
            score -= 5

        # Check 4xx error rate
        error_rate_4xx = metrics.get("error_rate_4xx", 0)
        if error_rate_4xx > 10:
            score -= 25
        elif error_rate_4xx > 5:
            score -= 10
        elif error_rate_4xx > 2:
            score -= 5

        # Check critical errors
        critical_errors = metrics.get("critical_errors_today", 0)
        if critical_errors > 10:
            score -= 30
        elif critical_errors > 5:
            score -= 15
        elif critical_errors > 0:
            score -= 5

        return max(0, min(100, score))

    def _calculate_response_time_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate response time health score"""
        score = 100.0

        # Check P95 response time
        p95_response = metrics.get("p95_response_time_ms", 0)
        if p95_response > 3000:
            score -= 40
        elif p95_response > 2000:
            score -= 25
        elif p95_response > 1000:
            score -= 10
        elif p95_response > 500:
            score -= 5

        # Check P99 response time
        p99_response = metrics.get("p99_response_time_ms", 0)
        if p99_response > 5000:
            score -= 30
        elif p99_response > 3000:
            score -= 15

        # Check timeout rate
        timeout_rate = metrics.get("timeout_rate", 0)
        if timeout_rate > 2:
            score -= 30
        elif timeout_rate > 1:
            score -= 15
        elif timeout_rate > 0.5:
            score -= 5

        return max(0, min(100, score))

    def _calculate_character_generation_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate character generation health score"""
        score = 100.0

        # Check success rate
        success_rate = metrics.get("generation_success_rate", 0)
        if success_rate < 80:
            score -= 40
        elif success_rate < 90:
            score -= 20
        elif success_rate < 95:
            score -= 10

        # Check generation time
        avg_time = metrics.get("average_generation_time_seconds", 0)
        if avg_time > 10:
            score -= 25
        elif avg_time > 6:
            score -= 10
        elif avg_time > 4:
            score -= 5

        # Check queue depth
        queue_depth = metrics.get("queue_depth", 0)
        if queue_depth > 50:
            score -= 30
        elif queue_depth > 20:
            score -= 15
        elif queue_depth > 10:
            score -= 5

        return max(0, min(100, score))

    def _calculate_dialogue_generation_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate dialogue generation health score"""
        score = 100.0

        # Check success rate
        success_rate = metrics.get("generation_success_rate", 0)
        if success_rate < 85:
            score -= 35
        elif success_rate < 92:
            score -= 15
        elif success_rate < 96:
            score -= 5

        # Check generation time
        avg_time = metrics.get("average_generation_time_seconds", 0)
        if avg_time > 8:
            score -= 20
        elif avg_time > 4:
            score -= 10
        elif avg_time > 2:
            score -= 5

        # Check queue depth
        queue_depth = metrics.get("queue_depth", 0)
        if queue_depth > 100:
            score -= 25
        elif queue_depth > 50:
            score -= 10
        elif queue_depth > 20:
            score -= 5

        return max(0, min(100, score))

    def _calculate_workflow_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate workflow execution health score"""
        score = 100.0

        # Check success rate
        success_rate = metrics.get("execution_success_rate", 0)
        if success_rate < 80:
            score -= 40
        elif success_rate < 90:
            score -= 20
        elif success_rate < 95:
            score -= 10

        # Check execution time
        avg_time = metrics.get("average_execution_time_seconds", 0)
        if avg_time > 60:
            score -= 25
        elif avg_time > 30:
            score -= 15
        elif avg_time > 15:
            score -= 5

        # Check failed executions
        failed_executions = metrics.get("failed_executions_today", 0)
        if failed_executions > 20:
            score -= 30
        elif failed_executions > 10:
            score -= 15
        elif failed_executions > 5:
            score -= 5

        return max(0, min(100, score))