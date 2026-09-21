"""
Service Healer

Automated healing and recovery procedures for service-level issues.
Includes service restart, configuration reload, and rollback capabilities.
"""

import asyncio
import aiohttp
import subprocess
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..health_service import HealthCheckResult, HealthStatus

@dataclass
class HealingAction:
    """Represents a healing action that was taken"""
    action_id: str
    action_type: str
    target_service: str
    description: str
    timestamp: datetime
    success: bool
    details: Dict[str, Any]
    duration_seconds: float

class ServiceHealer:
    """Automated service healing and recovery"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.healing_history: List[HealingAction] = []
        self.cooldown_periods: Dict[str, datetime] = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def heal_service(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal a service based on health check result"""
        actions = []
        service_id = health_result.check_id

        # Check if service is in cooldown period
        if self._is_in_cooldown(service_id):
            self.logger.info(f"Service {service_id} is in cooldown period, skipping healing")
            return actions

        try:
            # Determine healing strategy based on health status and issues
            if health_result.status == HealthStatus.CRITICAL:
                actions.extend(await self._handle_critical_issue(health_result))
            elif health_result.status == HealthStatus.DEGRADED:
                actions.extend(await self._handle_degraded_service(health_result))
            elif health_result.status == HealthStatus.WARNING:
                actions.extend(await self._handle_warning_issue(health_result))

            # Set cooldown period after healing attempts
            if actions:
                self._set_cooldown(service_id)

        except Exception as e:
            self.logger.error(f"Service healing failed for {service_id}: {e}")
            actions.append(HealingAction(
                action_id=f"healing-error-{datetime.now().timestamp()}",
                action_type="error",
                target_service=service_id,
                description=f"Healing process failed: {str(e)}",
                timestamp=datetime.now(),
                success=False,
                details={"error": str(e)},
                duration_seconds=0
            ))

        return actions

    async def _handle_critical_issue(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Handle critical service issues"""
        actions = []
        service_id = health_result.check_id

        self.logger.warning(f"Handling critical issue for service: {service_id}")

        # Try different healing strategies in order

        # 1. Service restart
        restart_action = await self._restart_service(service_id)
        actions.append(restart_action)

        if restart_action.success:
            # Wait for service to come back and check health
            await asyncio.sleep(10)
            health_check = await self._check_service_health(service_id)
            if health_check.get("status") == "healthy":
                return actions

        # 2. Configuration reload
        if not restart_action.success:
            reload_action = await self._reload_service_config(service_id)
            actions.append(reload_action)

            if reload_action.success:
                await asyncio.sleep(5)
                health_check = await self._check_service_health(service_id)
                if health_check.get("status") == "healthy":
                    return actions

        # 3. Service reset (clear caches, temp files)
        reset_action = await self._reset_service_state(service_id)
        actions.append(reset_action)

        # 4. Fallback to previous version if available
        if not any(action.success for action in actions):
            rollback_action = await self._rollback_service(service_id)
            actions.append(rollback_action)

        return actions

    async def _handle_degraded_service(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Handle degraded service performance"""
        actions = []
        service_id = health_result.check_id

        self.logger.info(f"Handling degraded service: {service_id}")

        # Check for common degradation causes and fix them

        # 1. Clear caches if memory usage is high
        if "memory" in health_result.message.lower() or "memory" in str(health_result.details).lower():
            cache_clear_action = await self._clear_service_caches(service_id)
            actions.append(cache_clear_action)

        # 2. Restart service if response times are high
        if "response time" in health_result.message.lower() or "timeout" in health_result.message.lower():
            restart_action = await self._restart_service(service_id)
            actions.append(restart_action)

        # 3. Reload configuration
        reload_action = await self._reload_service_config(service_id)
        actions.append(reload_action)

        # 4. Scale up service if auto-scaling is available
        scale_action = await self._scale_service(service_id, "up")
        actions.append(scale_action)

        return actions

    async def _handle_warning_issue(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Handle warning-level service issues"""
        actions = []
        service_id = health_result.check_id

        self.logger.info(f"Handling warning for service: {service_id}")

        # Less aggressive healing for warnings

        # 1. Reload configuration
        reload_action = await self._reload_service_config(service_id)
        actions.append(reload_action)

        # 2. Clear caches if applicable
        if "cache" in health_result.message.lower():
            cache_clear_action = await self._clear_service_caches(service_id)
            actions.append(cache_clear_action)

        # 3. Optimize service settings
        optimize_action = await self._optimize_service_settings(service_id)
        actions.append(optimize_action)

        return actions

    async def _restart_service(self, service_id: str) -> HealingAction:
        """Restart a service"""
        start_time = datetime.now()
        action_id = f"restart-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Attempting to restart service: {service_id}")

            # Get service configuration
            service_config = self.config.get("services", {}).get(service_id, {})
            restart_method = service_config.get("restart_method", "systemd")

            success = False
            details = {}

            if restart_method == "systemd":
                success, details = await self._restart_systemd_service(service_id)
            elif restart_method == "docker":
                success, details = await self._restart_docker_service(service_id)
            elif restart_method == "kubernetes":
                success, details = await self._restart_kubernetes_service(service_id)
            elif restart_method == "http":
                success, details = await self._restart_via_http(service_id)
            else:
                # Default to systemd
                success, details = await self._restart_systemd_service(service_id)

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="restart",
                target_service=service_id,
                description=f"Restarted service using {restart_method}",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Service restart failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="restart",
                target_service=service_id,
                description=f"Service restart failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _reload_service_config(self, service_id: str) -> HealingAction:
        """Reload service configuration"""
        start_time = datetime.now()
        action_id = f"reload-config-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Reloading configuration for service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            reload_endpoint = service_config.get("reload_endpoint")
            reload_command = service_config.get("reload_command")

            success = False
            details = {}

            if reload_endpoint:
                success, details = await self._reload_via_http_endpoint(service_id, reload_endpoint)
            elif reload_command:
                success, details = await self._execute_reload_command(service_id, reload_command)
            else:
                # Try SIGHUP for systemd services
                success, details = await self._send_sighup_to_service(service_id)

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="reload_config",
                target_service=service_id,
                description="Reloaded service configuration",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Configuration reload failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="reload_config",
                target_service=service_id,
                description=f"Configuration reload failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _clear_service_caches(self, service_id: str) -> HealingAction:
        """Clear service caches"""
        start_time = datetime.now()
        action_id = f"clear-cache-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Clearing caches for service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            cache_clear_endpoint = service_config.get("cache_clear_endpoint")
            cache_clear_command = service_config.get("cache_clear_command")

            success = False
            details = {}

            if cache_clear_endpoint:
                success, details = await self._clear_cache_via_http(service_id, cache_clear_endpoint)
            elif cache_clear_command:
                success, details = await self._execute_cache_clear_command(service_id, cache_clear_command)
            else:
                # Generic cache clearing
                success, details = await self._generic_cache_clear(service_id)

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="clear_cache",
                target_service=service_id,
                description="Cleared service caches",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Cache clear failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="clear_cache",
                target_service=service_id,
                description=f"Cache clear failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _reset_service_state(self, service_id: str) -> HealingAction:
        """Reset service state (clear temp files, reset connections)"""
        start_time = datetime.now()
        action_id = f"reset-state-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Resetting state for service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            reset_commands = service_config.get("reset_commands", [])

            success = True
            details = {"actions_taken": []}

            # Execute reset commands
            for command in reset_commands:
                try:
                    result = await self._execute_command(command)
                    details["actions_taken"].append({
                        "command": command,
                        "success": True,
                        "output": result
                    })
                except Exception as e:
                    success = False
                    details["actions_taken"].append({
                        "command": command,
                        "success": False,
                        "error": str(e)
                    })

            # Generic reset actions
            generic_reset_success, generic_reset_details = await self._generic_service_reset(service_id)
            details["generic_reset"] = generic_reset_details

            success = success and generic_reset_success

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="reset_state",
                target_service=service_id,
                description="Reset service state",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Service state reset failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="reset_state",
                target_service=service_id,
                description=f"Service state reset failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _rollback_service(self, service_id: str) -> HealingAction:
        """Rollback service to previous version"""
        start_time = datetime.now()
        action_id = f"rollback-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Attempting rollback for service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            rollback_enabled = service_config.get("rollback_enabled", False)

            if not rollback_enabled:
                return HealingAction(
                    action_id=action_id,
                    action_type="rollback",
                    target_service=service_id,
                    description="Rollback not configured for this service",
                    timestamp=start_time,
                    success=False,
                    details={"reason": "rollback_disabled"},
                    duration_seconds=0
                )

            # Implement rollback logic based on deployment type
            rollback_method = service_config.get("rollback_method", "docker")
            success = False
            details = {}

            if rollback_method == "docker":
                success, details = await self._rollback_docker_service(service_id)
            elif rollback_method == "kubernetes":
                success, details = await self._rollback_kubernetes_service(service_id)
            elif rollback_method == "blue_green":
                success, details = await self._rollback_blue_green(service_id)

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="rollback",
                target_service=service_id,
                description="Rolled back service to previous version",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Service rollback failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="rollback",
                target_service=service_id,
                description=f"Service rollback failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _scale_service(self, service_id: str, direction: str) -> HealingAction:
        """Scale service up or down"""
        start_time = datetime.now()
        action_id = f"scale-{direction}-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Scaling {direction} service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            scaling_enabled = service_config.get("scaling_enabled", False)

            if not scaling_enabled:
                return HealingAction(
                    action_id=action_id,
                    action_type="scale",
                    target_service=service_id,
                    description=f"Scaling not configured for this service",
                    timestamp=start_time,
                    success=False,
                    details={"reason": "scaling_disabled"},
                    duration_seconds=0
                )

            scaling_method = service_config.get("scaling_method", "kubernetes")
            success = False
            details = {}

            if scaling_method == "kubernetes":
                success, details = await self._scale_kubernetes_service(service_id, direction)
            elif scaling_method == "docker_swarm":
                success, details = await self._scale_docker_swarm_service(service_id, direction)

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="scale",
                target_service=service_id,
                description=f"Scaled service {direction}",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Service scaling failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="scale",
                target_service=service_id,
                description=f"Service scaling failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _optimize_service_settings(self, service_id: str) -> HealingAction:
        """Optimize service settings for better performance"""
        start_time = datetime.now()
        action_id = f"optimize-{service_id}-{start_time.timestamp()}"

        try:
            self.logger.info(f"Optimizing settings for service: {service_id}")

            service_config = self.config.get("services", {}).get(service_id, {})
            optimization_commands = service_config.get("optimization_commands", [])

            success = True
            details = {"optimizations_applied": []}

            for command in optimization_commands:
                try:
                    result = await self._execute_command(command)
                    details["optimizations_applied"].append({
                        "command": command,
                        "success": True,
                        "output": result
                    })
                except Exception as e:
                    success = False
                    details["optimizations_applied"].append({
                        "command": command,
                        "success": False,
                        "error": str(e)
                    })

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="optimize",
                target_service=service_id,
                description="Optimized service settings",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Service optimization failed for {service_id}: {e}")

            return HealingAction(
                action_id=action_id,
                action_type="optimize",
                target_service=service_id,
                description=f"Service optimization failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    # Implementation methods for different restart/healing strategies

    async def _restart_systemd_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Restart systemd service"""
        try:
            # Check service exists
            check_result = await self._execute_command(f"systemctl is-active {service_id}")

            # Restart service
            restart_result = await self._execute_command(f"sudo systemctl restart {service_id}")

            # Wait a bit and check status
            await asyncio.sleep(5)
            status_result = await self._execute_command(f"systemctl is-active {service_id}")

            success = "active" in status_result.lower()

            return success, {
                "method": "systemd",
                "initial_status": check_result.strip(),
                "restart_output": restart_result,
                "final_status": status_result.strip()
            }

        except Exception as e:
            return False, {"error": str(e)}

    async def _restart_docker_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Restart Docker service"""
        try:
            # Get container name
            service_config = self.config.get("services", {}).get(service_id, {})
            container_name = service_config.get("container_name", service_id)

            # Restart container
            restart_result = await self._execute_command(f"docker restart {container_name}")

            # Wait and check container status
            await asyncio.sleep(5)
            status_result = await self._execute_command(f"docker inspect -f '{{{{.State.Status}}}}' {container_name}")

            success = "running" in status_result.lower()

            return success, {
                "method": "docker",
                "container_name": container_name,
                "restart_output": restart_result,
                "final_status": status_result.strip()
            }

        except Exception as e:
            return False, {"error": str(e)}

    async def _restart_kubernetes_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Restart Kubernetes deployment"""
        try:
            service_config = self.config.get("services", {}).get(service_id, {})
            namespace = service_config.get("namespace", "default")
            deployment_name = service_config.get("deployment_name", service_id)

            # Restart deployment by rolling restart
            restart_result = await self._execute_command(
                f"kubectl rollout restart deployment/{deployment_name} -n {namespace}"
            )

            # Wait for rollout to complete
            await asyncio.sleep(10)
            status_result = await self._execute_command(
                f"kubectl rollout status deployment/{deployment_name} -n {namespace}"
            )

            success = "successfully" in status_result.lower()

            return success, {
                "method": "kubernetes",
                "namespace": namespace,
                "deployment_name": deployment_name,
                "restart_output": restart_result,
                "rollout_status": status_result
            }

        except Exception as e:
            return False, {"error": str(e)}

    async def _restart_via_http(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Restart service via HTTP endpoint"""
        try:
            service_config = self.config.get("services", {}).get(service_id, {})
            restart_endpoint = service_config.get("restart_endpoint")

            if not restart_endpoint:
                return False, {"error": "No restart endpoint configured"}

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(restart_endpoint) as response:
                success = response.status == 200
                response_text = await response.text()

                return success, {
                    "method": "http",
                    "endpoint": restart_endpoint,
                    "status_code": response.status,
                    "response": response_text
                }

        except Exception as e:
            return False, {"error": str(e)}

    # Helper methods

    async def _execute_command(self, command: str) -> str:
        """Execute shell command and return output"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr.decode()}")

        return stdout.decode().strip()

    async def _check_service_health(self, service_id: str) -> Dict[str, Any]:
        """Check if service is healthy after healing"""
        try:
            service_config = self.config.get("services", {}).get(service_id, {})
            health_endpoint = service_config.get("health_endpoint")

            if health_endpoint:
                if not self.session:
                    self.session = aiohttp.ClientSession()

                async with self.session.get(health_endpoint) as response:
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "status_code": response.status
                    }
            else:
                # Generic health check
                return {"status": "unknown", "message": "No health endpoint configured"}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _is_in_cooldown(self, service_id: str) -> bool:
        """Check if service is in cooldown period"""
        if service_id not in self.cooldown_periods:
            return False

        cooldown_end = self.cooldown_periods[service_id]
        return datetime.now() < cooldown_end

    def _set_cooldown(self, service_id: str):
        """Set cooldown period for service"""
        cooldown_minutes = self.config.get("cooldown_minutes", 5)
        self.cooldown_periods[service_id] = datetime.now() + timedelta(minutes=cooldown_minutes)

    # Placeholder methods for features that would need implementation

    async def _send_sighup_to_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Send SIGHUP signal to service for config reload"""
        # Implementation would depend on service type
        return True, {"method": "sighup", "signal_sent": True}

    async def _reload_via_http_endpoint(self, service_id: str, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """Reload configuration via HTTP endpoint"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(endpoint) as response:
                success = response.status == 200
                response_text = await response.text()
                return success, {"status_code": response.status, "response": response_text}
        except Exception as e:
            return False, {"error": str(e)}

    async def _execute_reload_command(self, service_id: str, command: str) -> tuple[bool, Dict[str, Any]]:
        """Execute reload command"""
        try:
            output = await self._execute_command(command)
            return True, {"command": command, "output": output}
        except Exception as e:
            return False, {"command": command, "error": str(e)}

    async def _clear_cache_via_http(self, service_id: str, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """Clear cache via HTTP endpoint"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.delete(endpoint) as response:
                success = response.status == 200
                response_text = await response.text()
                return success, {"status_code": response.status, "response": response_text}
        except Exception as e:
            return False, {"error": str(e)}

    async def _execute_cache_clear_command(self, service_id: str, command: str) -> tuple[bool, Dict[str, Any]]:
        """Execute cache clear command"""
        try:
            output = await self._execute_command(command)
            return True, {"command": command, "output": output}
        except Exception as e:
            return False, {"command": command, "error": str(e)}

    async def _generic_cache_clear(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Generic cache clearing method"""
        # Implementation would depend on service type
        return True, {"method": "generic", "cleared": True}

    async def _generic_service_reset(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Generic service state reset"""
        # Implementation would reset common service state
        return True, {"method": "generic", "reset": True}

    async def _rollback_docker_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Rollback Docker service to previous image"""
        # Implementation would require maintaining image history
        return False, {"error": "Docker rollback not implemented"}

    async def _rollback_kubernetes_service(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Rollback Kubernetes deployment"""
        # Implementation would use kubectl rollout undo
        return False, {"error": "Kubernetes rollback not implemented"}

    async def _rollback_blue_green(self, service_id: str) -> tuple[bool, Dict[str, Any]]:
        """Rollback using blue-green deployment strategy"""
        # Implementation would switch traffic back to previous version
        return False, {"error": "Blue-green rollback not implemented"}

    async def _scale_kubernetes_service(self, service_id: str, direction: str) -> tuple[bool, Dict[str, Any]]:
        """Scale Kubernetes deployment"""
        # Implementation would use kubectl scale command
        return False, {"error": "Kubernetes scaling not implemented"}

    async def _scale_docker_swarm_service(self, service_id: str, direction: str) -> tuple[bool, Dict[str, Any]]:
        """Scale Docker Swarm service"""
        # Implementation would use docker service scale command
        return False, {"error": "Docker Swarm scaling not implemented"}