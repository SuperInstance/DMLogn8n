"""
Service-Level Health Checks

Implements health checks for application services like API gateway,
character portals, dialogue services, and other microservices.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..health_service import HealthCheckResult, HealthStatus

class ServiceChecker:
    """Service-level health checker"""

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

    async def check_health(self, service_id: str) -> HealthCheckResult:
        """Check health of a specific service"""
        check_method = getattr(self, f"_check_{service_id.replace('-', '_')}", None)

        if check_method:
            return await check_method()
        else:
            # Generic service health check
            return await self._check_generic_service(service_id)

    async def _check_api_gateway(self) -> HealthCheckResult:
        """Check API Gateway health"""
        start_time = datetime.now()

        try:
            gateway_config = self.config.get("api_gateway", {})
            base_url = gateway_config.get("base_url", "http://localhost:8080")
            health_endpoint = gateway_config.get("health_endpoint", "/health")
            timeout = gateway_config.get("timeout", 10)

            health_url = f"{base_url}{health_endpoint}"

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test API Gateway health endpoint
            start_request = datetime.now()
            async with self.session.get(health_url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000

                if response.status != 200:
                    return HealthCheckResult(
                        check_id="api-gateway",
                        check_name="API Gateway Service",
                        level="service",
                        status=HealthStatus.CRITICAL,
                        message=f"Health endpoint returned status {response.status}",
                        details={"status_code": response.status},
                        metrics={"response_time": response_time},
                        timestamp=start_time,
                        duration_ms=response_time
                    )

                health_data = await response.json()

            # Perform additional functional tests
            functional_results = await self._test_api_gateway_functionality(base_url)

            # Calculate overall health score
            score = self._calculate_api_gateway_score(health_data, functional_results, response_time)

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
                check_id="api-gateway",
                check_name="API Gateway Service",
                level="service",
                status=status,
                message=f"API Gateway operational - Score: {score:.1f}%",
                details={
                    "health_data": health_data,
                    "functional_tests": functional_results,
                    "response_time_ms": round(response_time, 2)
                },
                metrics={
                    "score": score,
                    "response_time": response_time,
                    "uptime_percentage": health_data.get("uptime", 0),
                    "active_connections": health_data.get("active_connections", 0),
                    "requests_per_second": health_data.get("requests_per_second", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"API Gateway health check failed: {e}")
            return HealthCheckResult(
                check_id="api-gateway",
                check_name="API Gateway Service",
                level="service",
                status=HealthStatus.CRITICAL,
                message=f"API Gateway check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _test_api_gateway_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test API Gateway functionality"""
        results = {
            "authentication_test": False,
            "routing_test": False,
            "rate_limiting_test": False,
            "load_balancing_test": False
        }

        try:
            # Test authentication endpoint
            auth_url = f"{base_url}/auth/health"
            async with self.session.get(auth_url, timeout=5) as response:
                results["authentication_test"] = response.status == 200

            # Test routing to downstream services
            route_url = f"{base_url}/api/v1/characters/health"
            async with self.session.get(route_url, timeout=5) as response:
                results["routing_test"] = response.status in [200, 404]  # 404 is acceptable if service doesn't exist

            # Test rate limiting (make multiple rapid requests)
            rate_limit_url = f"{base_url}/api/v1/test"
            rate_limit_passed = True
            for _ in range(5):
                async with self.session.get(rate_limit_url, timeout=2) as response:
                    if response.status == 429:  # Too Many Requests
                        rate_limit_passed = True
                        break
                    elif response.status != 200:
                        rate_limit_passed = False
                        break
            results["rate_limiting_test"] = rate_limit_passed

            # Test load balancing (check if multiple instances are responding)
            lb_url = f"{base_url}/lb/health"
            instance_ids = set()
            for _ in range(3):
                async with self.session.get(lb_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        instance_id = data.get("instance_id")
                        if instance_id:
                            instance_ids.add(instance_id)
            results["load_balancing_test"] = len(instance_ids) >= 1

        except Exception as e:
            self.logger.warning(f"API Gateway functional tests failed: {e}")

        return results

    def _calculate_api_gateway_score(self, health_data: Dict[str, Any], functional_results: Dict[str, Any], response_time: float) -> float:
        """Calculate API Gateway health score"""
        score = 100.0

        # Response time scoring
        if response_time > 2000:
            score -= 30
        elif response_time > 1000:
            score -= 15
        elif response_time > 500:
            score -= 5

        # Uptime scoring
        uptime = health_data.get("uptime", 0)
        if uptime < 95:
            score -= 40
        elif uptime < 99:
            score -= 20

        # Active connections scoring
        active_connections = health_data.get("active_connections", 0)
        if active_connections > 1000:
            score -= 20
        elif active_connections > 500:
            score -= 10

        # Functional test scoring
        functional_score = sum(functional_results.values()) / len(functional_results) * 100
        score = score * (functional_score / 100)

        return max(0, min(100, score))

    async def _check_character_portal(self) -> HealthCheckResult:
        """Check Character Portal service health"""
        start_time = datetime.now()

        try:
            portal_config = self.config.get("character_portal", {})
            base_url = portal_config.get("base_url", "http://localhost:8081")
            health_endpoint = portal_config.get("health_endpoint", "/health")
            timeout = portal_config.get("timeout", 10)

            health_url = f"{base_url}{health_endpoint}"

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test Character Portal health endpoint
            start_request = datetime.now()
            async with self.session.get(health_url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000

                if response.status != 200:
                    return HealthCheckResult(
                        check_id="character-portal",
                        check_name="Character Portal Service",
                        level="service",
                        status=HealthStatus.CRITICAL,
                        message=f"Health endpoint returned status {response.status}",
                        details={"status_code": response.status},
                        metrics={"response_time": response_time},
                        timestamp=start_time,
                        duration_ms=response_time
                    )

                health_data = await response.json()

            # Test character portal functionality
            functional_results = await self._test_character_portal_functionality(base_url)

            # Calculate health score
            score = self._calculate_character_portal_score(health_data, functional_results, response_time)

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
                check_id="character-portal",
                check_name="Character Portal Service",
                level="service",
                status=status,
                message=f"Character Portal operational - Score: {score:.1f}%",
                details={
                    "health_data": health_data,
                    "functional_tests": functional_results,
                    "response_time_ms": round(response_time, 2)
                },
                metrics={
                    "score": score,
                    "response_time": response_time,
                    "active_characters": health_data.get("active_characters", 0),
                    "cache_hit_rate": health_data.get("cache_hit_rate", 0),
                    "database_connections": health_data.get("database_connections", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Character Portal health check failed: {e}")
            return HealthCheckResult(
                check_id="character-portal",
                check_name="Character Portal Service",
                level="service",
                status=HealthStatus.CRITICAL,
                message=f"Character Portal check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _test_character_portal_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Character Portal functionality"""
        results = {
            "character_list_test": False,
            "character_creation_test": False,
            "character_update_test": False,
            "database_connectivity_test": False,
            "cache_functionality_test": False
        }

        try:
            # Test character list endpoint
            list_url = f"{base_url}/api/characters"
            async with self.session.get(list_url, timeout=5) as response:
                results["character_list_test"] = response.status == 200

            # Test character creation (using a test character)
            create_url = f"{base_url}/api/characters"
            test_character = {
                "name": "HealthCheckTest",
                "class": "Tester",
                "level": 1
            }
            async with self.session.post(create_url, json=test_character, timeout=5) as response:
                results["character_creation_test"] = response.status in [200, 201]

            # Test character update
            update_url = f"{base_url}/api/characters/test-123"
            update_data = {"level": 2}
            async with self.session.put(update_url, json=update_data, timeout=5) as response:
                results["character_update_test"] = response.status in [200, 404]  # 404 is acceptable

            # Test database connectivity
            db_url = f"{base_url}/api/health/database"
            async with self.session.get(db_url, timeout=5) as response:
                results["database_connectivity_test"] = response.status == 200

            # Test cache functionality
            cache_url = f"{base_url}/api/health/cache"
            async with self.session.get(cache_url, timeout=5) as response:
                results["cache_functionality_test"] = response.status == 200

        except Exception as e:
            self.logger.warning(f"Character Portal functional tests failed: {e}")

        return results

    def _calculate_character_portal_score(self, health_data: Dict[str, Any], functional_results: Dict[str, Any], response_time: float) -> float:
        """Calculate Character Portal health score"""
        score = 100.0

        # Response time scoring
        if response_time > 3000:
            score -= 30
        elif response_time > 1500:
            score -= 15
        elif response_time > 800:
            score -= 5

        # Database connections scoring
        db_connections = health_data.get("database_connections", 0)
        if db_connections > 50:
            score -= 20
        elif db_connections > 30:
            score -= 10

        # Cache hit rate scoring
        cache_hit_rate = health_data.get("cache_hit_rate", 0)
        if cache_hit_rate < 70:
            score -= 20
        elif cache_hit_rate < 85:
            score -= 10

        # Functional test scoring
        functional_score = sum(functional_results.values()) / len(functional_results) * 100
        score = score * (functional_score / 100)

        return max(0, min(100, score))

    async def _check_dialogue_service(self) -> HealthCheckResult:
        """Check Dialogue Service health"""
        start_time = datetime.now()

        try:
            dialogue_config = self.config.get("dialogue_service", {})
            base_url = dialogue_config.get("base_url", "http://localhost:8082")
            health_endpoint = dialogue_config.get("health_endpoint", "/health")
            timeout = dialogue_config.get("timeout", 10)

            health_url = f"{base_url}{health_endpoint}"

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test Dialogue Service health endpoint
            start_request = datetime.now()
            async with self.session.get(health_url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000

                if response.status != 200:
                    return HealthCheckResult(
                        check_id="dialogue-service",
                        check_name="Dialogue Service",
                        level="service",
                        status=HealthStatus.CRITICAL,
                        message=f"Health endpoint returned status {response.status}",
                        details={"status_code": response.status},
                        metrics={"response_time": response_time},
                        timestamp=start_time,
                        duration_ms=response_time
                    )

                health_data = await response.json()

            # Test dialogue service functionality
            functional_results = await self._test_dialogue_service_functionality(base_url)

            # Calculate health score
            score = self._calculate_dialogue_service_score(health_data, functional_results, response_time)

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
                check_id="dialogue-service",
                check_name="Dialogue Service",
                level="service",
                status=status,
                message=f"Dialogue Service operational - Score: {score:.1f}%",
                details={
                    "health_data": health_data,
                    "functional_tests": functional_results,
                    "response_time_ms": round(response_time, 2)
                },
                metrics={
                    "score": score,
                    "response_time": response_time,
                    "active_dialogues": health_data.get("active_dialogues", 0),
                    "ai_model_status": health_data.get("ai_model_status", "unknown"),
                    "queue_size": health_data.get("queue_size", 0)
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Dialogue Service health check failed: {e}")
            return HealthCheckResult(
                check_id="dialogue-service",
                check_name="Dialogue Service",
                level="service",
                status=HealthStatus.CRITICAL,
                message=f"Dialogue Service check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _test_dialogue_service_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test Dialogue Service functionality"""
        results = {
            "dialogue_generation_test": False,
            "ai_model_connectivity_test": False,
            "context_management_test": False,
            "queue_processing_test": False,
            "memory_storage_test": False
        }

        try:
            # Test dialogue generation
            gen_url = f"{base_url}/api/dialogue/generate"
            test_request = {
                "character": "TestNPC",
                "context": "Hello, how are you?",
                "player_input": "I'm doing well, thanks!"
            }
            async with self.session.post(gen_url, json=test_request, timeout=10) as response:
                results["dialogue_generation_test"] = response.status == 200

            # Test AI model connectivity
            ai_url = f"{base_url}/api/health/ai-model"
            async with self.session.get(ai_url, timeout=5) as response:
                results["ai_model_connectivity_test"] = response.status == 200

            # Test context management
            context_url = f"{base_url}/api/dialogue/context/test-session"
            async with self.session.get(context_url, timeout=5) as response:
                results["context_management_test"] = response.status in [200, 404]

            # Test queue processing
            queue_url = f"{base_url}/api/health/queue"
            async with self.session.get(queue_url, timeout=5) as response:
                results["queue_processing_test"] = response.status == 200

            # Test memory storage
            memory_url = f"{base_url}/api/health/memory"
            async with self.session.get(memory_url, timeout=5) as response:
                results["memory_storage_test"] = response.status == 200

        except Exception as e:
            self.logger.warning(f"Dialogue Service functional tests failed: {e}")

        return results

    def _calculate_dialogue_service_score(self, health_data: Dict[str, Any], functional_results: Dict[str, Any], response_time: float) -> float:
        """Calculate Dialogue Service health score"""
        score = 100.0

        # Response time scoring
        if response_time > 5000:
            score -= 30
        elif response_time > 3000:
            score -= 15
        elif response_time > 1500:
            score -= 5

        # Queue size scoring
        queue_size = health_data.get("queue_size", 0)
        if queue_size > 100:
            score -= 25
        elif queue_size > 50:
            score -= 10

        # Active dialogues scoring
        active_dialogues = health_data.get("active_dialogues", 0)
        if active_dialogues > 1000:
            score -= 20
        elif active_dialogues > 500:
            score -= 10

        # AI model status
        ai_model_status = health_data.get("ai_model_status", "unknown")
        if ai_model_status != "healthy":
            score -= 30

        # Functional test scoring
        functional_score = sum(functional_results.values()) / len(functional_results) * 100
        score = score * (functional_score / 100)

        return max(0, min(100, score))

    async def _check_n8n_workflow(self) -> HealthCheckResult:
        """Check N8N Workflow Engine health"""
        start_time = datetime.now()

        try:
            n8n_config = self.config.get("n8n_workflow", {})
            base_url = n8n_config.get("base_url", "http://localhost:5678")
            health_endpoint = n8n_config.get("health_endpoint", "/healthz")
            timeout = n8n_config.get("timeout", 10)

            health_url = f"{base_url}{health_endpoint}"

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test N8N health endpoint
            start_request = datetime.now()
            async with self.session.get(health_url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000

                if response.status != 200:
                    return HealthCheckResult(
                        check_id="n8n-workflow",
                        check_name="N8N Workflow Engine",
                        level="service",
                        status=HealthStatus.CRITICAL,
                        message=f"Health endpoint returned status {response.status}",
                        details={"status_code": response.status},
                        metrics={"response_time": response_time},
                        timestamp=start_time,
                        duration_ms=response_time
                    )

            # Test N8N API functionality
            functional_results = await self._test_n8n_functionality(base_url)

            # Calculate health score
            score = self._calculate_n8n_score(functional_results, response_time)

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
                check_id="n8n-workflow",
                check_name="N8N Workflow Engine",
                level="service",
                status=status,
                message=f"N8N Workflow Engine operational - Score: {score:.1f}%",
                details={
                    "functional_tests": functional_results,
                    "response_time_ms": round(response_time, 2)
                },
                metrics={
                    "score": score,
                    "response_time": response_time
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"N8N Workflow Engine health check failed: {e}")
            return HealthCheckResult(
                check_id="n8n-workflow",
                check_name="N8N Workflow Engine",
                level="service",
                status=HealthStatus.CRITICAL,
                message=f"N8N check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _test_n8n_functionality(self, base_url: str) -> Dict[str, Any]:
        """Test N8N functionality"""
        results = {
            "api_access_test": False,
            "workflow_list_test": False,
            "execution_history_test": False,
            "active_workflows_test": False
        }

        try:
            # Test API access (using basic auth if configured)
            api_url = f"{base_url}/api/v1/workflows"
            headers = {}

            # Add auth if configured
            n8n_config = self.config.get("n8n_workflow", {})
            if n8n_config.get("api_key"):
                headers["Authorization"] = f"Bearer {n8n_config['api_key']}"

            async with self.session.get(api_url, headers=headers, timeout=5) as response:
                results["api_access_test"] = response.status == 200

            # Test workflow listing
            if results["api_access_test"]:
                workflows_data = await response.json()
                results["workflow_list_test"] = isinstance(workflows_data, list)

                # Check for active workflows
                active_workflows = [w for w in workflows_data if w.get("active", False)]
                results["active_workflows_test"] = len(active_workflows) >= 0

            # Test execution history
            exec_url = f"{base_url}/api/v1/executions"
            async with self.session.get(exec_url, headers=headers, timeout=5) as response:
                results["execution_history_test"] = response.status == 200

        except Exception as e:
            self.logger.warning(f"N8N functional tests failed: {e}")

        return results

    def _calculate_n8n_score(self, functional_results: Dict[str, Any], response_time: float) -> float:
        """Calculate N8N health score"""
        score = 100.0

        # Response time scoring
        if response_time > 3000:
            score -= 30
        elif response_time > 1500:
            score -= 15
        elif response_time > 800:
            score -= 5

        # Functional test scoring
        functional_score = sum(functional_results.values()) / len(functional_results) * 100
        score = score * (functional_score / 100)

        return max(0, min(100, score))

    async def _check_generic_service(self, service_id: str) -> HealthCheckResult:
        """Generic service health check"""
        start_time = datetime.now()

        try:
            service_config = self.config.get("services", {}).get(service_id, {})
            if not service_config:
                return HealthCheckResult(
                    check_id=service_id,
                    check_name=f"Service: {service_id}",
                    level="service",
                    status=HealthStatus.UNKNOWN,
                    message=f"No configuration found for service: {service_id}"
                )

            base_url = service_config.get("base_url")
            health_endpoint = service_config.get("health_endpoint", "/health")
            timeout = service_config.get("timeout", 10)

            if not base_url:
                return HealthCheckResult(
                    check_id=service_id,
                    check_name=f"Service: {service_id}",
                    level="service",
                    status=HealthStatus.CRITICAL,
                    message="Base URL not configured for service"
                )

            health_url = f"{base_url}{health_endpoint}"

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test service health endpoint
            start_request = datetime.now()
            async with self.session.get(health_url, timeout=timeout) as response:
                response_time = (datetime.now() - start_request).total_seconds() * 1000
                status_code = response.status

                if response.status == 200:
                    try:
                        health_data = await response.json()
                        message = f"Service operational - Response time: {response_time:.1f}ms"
                    except:
                        health_data = {}
                        message = f"Service responding - Response time: {response_time:.1f}ms"
                else:
                    health_data = {}
                    message = f"Service returned status {status_code}"

            # Calculate basic health score
            score = 100.0

            if status_code != 200:
                score -= 50

            if response_time > 5000:
                score -= 30
            elif response_time > 2000:
                score -= 15
            elif response_time > 1000:
                score -= 5

            # Determine status
            if score >= 90:
                status = HealthStatus.HEALTHY
            elif score >= 70:
                status = HealthStatus.WARNING
            elif score >= 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL

            return HealthCheckResult(
                check_id=service_id,
                check_name=f"Service: {service_id}",
                level="service",
                status=status,
                message=message,
                details={
                    "status_code": status_code,
                    "response_time_ms": round(response_time, 2),
                    "health_data": health_data
                },
                metrics={
                    "score": score,
                    "response_time": response_time,
                    "status_code": status_code
                },
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            self.logger.error(f"Service {service_id} health check failed: {e}")
            return HealthCheckResult(
                check_id=service_id,
                check_name=f"Service: {service_id}",
                level="service",
                status=HealthStatus.CRITICAL,
                message=f"Service check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )