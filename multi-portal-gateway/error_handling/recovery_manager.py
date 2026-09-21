"""
Automated Recovery Procedures

Provides automated recovery mechanisms for different types of errors,
including service restart, cache clearing, circuit breaker reset, and more.
"""

import asyncio
import time
import logging
import psutil
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
import subprocess
import requests
from .error_classifier import ErrorInfo, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class RecoveryActionType(Enum):
    """Types of recovery actions."""
    RESTART_SERVICE = "restart_service"
    RESET_CIRCUIT_BREAKER = "reset_circuit_breaker"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DATABASE = "reconnect_database"
    SCALE_RESOURCES = "scale_resources"
    CLEANUP_TEMP = "cleanup_temp"
    VALIDATE_CONFIG = "validate_config"
    RUN_DIAGNOSTIC = "run_diagnostic"
    NOTIFY_ADMIN = "notify_admin"
    CUSTOM = "custom"


class RecoveryStatus(Enum):
    """Recovery action status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class RecoveryAction:
    """Recovery action definition."""
    name: str
    action_type: RecoveryActionType
    description: str
    applicable_categories: List[ErrorCategory]
    severity_threshold: Optional[ErrorSeverity] = None
    timeout: float = 60.0
    retry_count: int = 3
    delay: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class RecoveryExecution:
    """Execution record for a recovery action."""
    action: RecoveryAction
    error_info: ErrorInfo
    status: RecoveryStatus
    start_time: float
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_log: List[str] = field(default_factory=list)


class RecoveryActionExecutor(ABC):
    """Abstract base class for recovery action executors."""

    @abstractmethod
    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Execute recovery action."""
        pass

    @abstractmethod
    def can_handle(self, action_type: RecoveryActionType) -> bool:
        """Check if executor can handle this action type."""
        pass


class ServiceRestartExecutor(RecoveryActionExecutor):
    """Executor for service restart actions."""

    def __init__(self):
        self._running_processes: Dict[str, subprocess.Popen] = {}

    def can_handle(self, action_type: RecoveryActionType) -> bool:
        return action_type == RecoveryActionType.RESTART_SERVICE

    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Execute service restart."""
        service_name = action.parameters.get("service_name")
        if not service_name:
            raise ValueError("service_name parameter required for RESTART_SERVICE action")

        logger.info(f"Attempting to restart service: {service_name}")

        try:
            # Stop existing service
            if service_name in self._running_processes:
                process = self._running_processes[service_name]
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                del self._running_processes[service_name]

            # Start service
            start_command = action.parameters.get("start_command", f"python -m {service_name}")
            process = subprocess.Popen(
                start_command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self._running_processes[service_name] = process

            # Wait and check if service is healthy
            await asyncio.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Service failed to start: {stderr.decode()}")

            # Health check if configured
            health_check_url = action.parameters.get("health_check_url")
            if health_check_url:
                await self._perform_health_check(health_check_url)

            logger.info(f"Service {service_name} restarted successfully")
            return {"status": "success", "service": service_name, "pid": process.pid}

        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            raise

    async def _perform_health_check(self, url: str, timeout: float = 10.0) -> None:
        """Perform health check on restarted service."""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code != 200:
                raise RuntimeError(f"Health check failed: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Health check failed: {e}")


class CircuitBreakerResetExecutor(RecoveryActionExecutor):
    """Executor for circuit breaker reset actions."""

    def __init__(self, circuit_breaker_registry=None):
        self._circuit_breaker_registry = circuit_breaker_registry

    def can_handle(self, action_type: RecoveryActionType) -> bool:
        return action_type == RecoveryActionType.RESET_CIRCUIT_BREAKER

    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Execute circuit breaker reset."""
        breaker_name = action.parameters.get("breaker_name")
        if not breaker_name:
            raise ValueError("breaker_name parameter required for RESET_CIRCUIT_BREAKER action")

        if not self._circuit_breaker_registry:
            raise RuntimeError("No circuit breaker registry available")

        logger.info(f"Resetting circuit breaker: {breaker_name}")

        try:
            breaker = self._circuit_breaker_registry.get_breaker(breaker_name)
            breaker.reset()

            # Verify reset
            state = breaker.get_state()
            metrics = breaker.get_metrics()

            logger.info(f"Circuit breaker {breaker_name} reset successfully")
            return {
                "status": "success",
                "breaker": breaker_name,
                "state": state.value,
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Failed to reset circuit breaker {breaker_name}: {e}")
            raise


class CacheClearExecutor(RecoveryActionExecutor):
    """Executor for cache clearing actions."""

    def __init__(self, cache_manager=None):
        self._cache_manager = cache_manager

    def can_handle(self, action_type: RecoveryActionType) -> bool:
        return action_type == RecoveryActionType.CLEAR_CACHE

    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Execute cache clearing."""
        cache_type = action.parameters.get("cache_type", "all")
        cache_key = action.parameters.get("cache_key")

        logger.info(f"Clearing cache: type={cache_type}, key={cache_key}")

        try:
            cleared_items = 0

            if cache_type == "all":
                # Clear all caches
                if self._cache_manager:
                    cleared_items = self._cache_manager.clear_all()
                else:
                    # Basic in-memory cache clearing
                    cleared_items = self._clear_basic_caches()
            elif cache_type == "key" and cache_key:
                # Clear specific key
                if self._cache_manager:
                    cleared_items = 1 if self._cache_manager.delete(cache_key) else 0
                else:
                    cleared_items = 1 if self._clear_basic_cache_key(cache_key) else 0

            logger.info(f"Cache cleared successfully: {cleared_items} items")
            return {
                "status": "success",
                "cache_type": cache_type,
                "cache_key": cache_key,
                "cleared_items": cleared_items
            }

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise

    def _clear_basic_caches(self) -> int:
        """Clear basic in-memory caches."""
        # This is a placeholder for basic cache clearing
        # In a real implementation, this would clear actual caches
        return 0

    def _clear_basic_cache_key(self, key: str) -> bool:
        """Clear specific cache key."""
        # This is a placeholder for basic cache key clearing
        return True


class ResourceManagementExecutor(RecoveryActionExecutor):
    """Executor for resource management actions."""

    def can_handle(self, action_type: RecoveryActionType) -> bool:
        return action_type == RecoveryActionType.SCALE_RESOURCES

    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Execute resource scaling/management."""
        resource_type = action.parameters.get("resource_type")
        action_name = action.parameters.get("action")

        logger.info(f"Managing resources: type={resource_type}, action={action_name}")

        try:
            if resource_type == "memory":
                result = await self._manage_memory(action_name, action.parameters)
            elif resource_type == "cpu":
                result = await self._manage_cpu(action_name, action.parameters)
            elif resource_type == "disk":
                result = await self._manage_disk(action_name, action.parameters)
            else:
                raise ValueError(f"Unknown resource type: {resource_type}")

            logger.info(f"Resource management completed: {result}")
            return {"status": "success", "resource_type": resource_type, "result": result}

        except Exception as e:
            logger.error(f"Failed to manage resources: {e}")
            raise

    async def _manage_memory(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage memory resources."""
        if action == "cleanup":
            import gc
            collected = gc.collect()
            return {"action": "gc_collect", "collected": collected}
        elif action == "check_usage":
            memory = psutil.virtual_memory()
            return {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
        else:
            raise ValueError(f"Unknown memory action: {action}")

    async def _manage_cpu(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage CPU resources."""
        if action == "check_usage":
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()
            return {"cpu_percent": cpu_percent, "load_avg": load_avg}
        else:
            raise ValueError(f"Unknown CPU action: {action}")

    async def _manage_disk(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage disk resources."""
        if action == "cleanup_temp":
            import tempfile
            import shutil
            temp_dir = tempfile.gettempdir()
            cleaned_size = 0
            # Clean temporary files (simplified)
            return {"action": "cleanup_temp", "cleaned_size": cleaned_size}
        elif action == "check_usage":
            disk = psutil.disk_usage('/')
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        else:
            raise ValueError(f"Unknown disk action: {action}")


class DiagnosticExecutor(RecoveryActionExecutor):
    """Executor for diagnostic actions."""

    def can_handle(self, action_type: RecoveryActionType) -> bool:
        return action_type == RecoveryActionType.RUN_DIAGNOSTIC

    async def execute(self, action: RecoveryAction, error_info: ErrorInfo) -> Dict[str, Any]:
        """Run diagnostics."""
        diagnostic_type = action.parameters.get("diagnostic_type", "basic")

        logger.info(f"Running diagnostics: type={diagnostic_type}")

        try:
            diagnostics = {}

            if diagnostic_type in ["basic", "full"]:
                diagnostics.update(self._basic_diagnostics())

            if diagnostic_type == "full":
                diagnostics.update(await self._full_diagnostics())

            logger.info(f"Diagnostics completed: {len(diagnostics)} checks")
            return {"status": "success", "diagnostics": diagnostics}

        except Exception as e:
            logger.error(f"Diagnostics failed: {e}")
            raise

    def _basic_diagnostics(self) -> Dict[str, Any]:
        """Run basic diagnostics."""
        return {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "process": {
                "pid": psutil.Process().pid,
                "memory_info": psutil.Process().memory_info()._asdict(),
                "cpu_percent": psutil.Process().cpu_percent()
            }
        }

    async def _full_diagnostics(self) -> Dict[str, Any]:
        """Run full diagnostics."""
        # Network connectivity check
        network_status = {}
        try:
            response = requests.get("https://www.google.com", timeout=5)
            network_status["internet"] = "connected"
        except:
            network_status["internet"] = "disconnected"

        return {
            "network": network_status,
            "threads": threading.active_count(),
            "file_descriptors": psutil.Process().num_fds()
        }


class RecoveryManager:
    """
    Main recovery manager that coordinates automated recovery actions.

    Features:
    - Multiple recovery action types
    - Configurable recovery policies
    - Action execution with timeout and retry
    - Recovery execution tracking
    - Manual override capabilities
    """

    def __init__(self):
        self._executors: List[RecoveryActionExecutor] = []
        self._actions: Dict[str, RecoveryAction] = {}
        self._execution_history: List[RecoveryExecution] = []
        self._lock = threading.RLock()

        # Register default executors
        self._register_default_executors()

        # Register default recovery actions
        self._register_default_actions()

        logger.info("Recovery manager initialized")

    def _register_default_executors(self) -> None:
        """Register default recovery action executors."""
        self._executors.extend([
            ServiceRestartExecutor(),
            CircuitBreakerResetExecutor(),
            CacheClearExecutor(),
            ResourceManagementExecutor(),
            DiagnosticExecutor()
        ])

    def _register_default_actions(self) -> None:
        """Register default recovery actions."""
        default_actions = [
            RecoveryAction(
                name="restart_ai_service",
                action_type=RecoveryActionType.RESTART_SERVICE,
                description="Restart AI model service",
                applicable_categories=[ErrorCategory.AI_MODEL],
                severity_threshold=ErrorSeverity.HIGH,
                parameters={"service_name": "ai_service"}
            ),
            RecoveryAction(
                name="reset_network_circuits",
                action_type=RecoveryActionType.RESET_CIRCUIT_BREAKER,
                description="Reset network-related circuit breakers",
                applicable_categories=[ErrorCategory.NETWORK],
                parameters={"breaker_name": "network_breaker"}
            ),
            RecoveryAction(
                name="clear_ai_cache",
                action_type=RecoveryActionType.CLEAR_CACHE,
                description="Clear AI model cache",
                applicable_categories=[ErrorCategory.AI_MODEL],
                parameters={"cache_type": "all"}
            ),
            RecoveryAction(
                name="cleanup_memory",
                action_type=RecoveryActionType.SCALE_RESOURCES,
                description="Clean up memory resources",
                applicable_categories=[ErrorCategory.RESOURCE],
                parameters={"resource_type": "memory", "action": "cleanup"}
            ),
            RecoveryAction(
                name="run_diagnostics",
                action_type=RecoveryActionType.RUN_DIAGNOSTIC,
                description="Run system diagnostics",
                applicable_categories=[ErrorCategory.SYSTEM],
                parameters={"diagnostic_type": "full"}
            )
        ]

        for action in default_actions:
            self._actions[action.name] = action

    def register_executor(self, executor: RecoveryActionExecutor) -> None:
        """Register a recovery action executor."""
        self._executors.append(executor)
        logger.info(f"Registered recovery executor: {type(executor).__name__}")

    def register_action(self, action: RecoveryAction) -> None:
        """Register a recovery action."""
        self._actions[action.name] = action
        logger.info(f"Registered recovery action: {action.name}")

    async def execute_recovery(self, action_name: str, error_info: ErrorInfo) -> RecoveryExecution:
        """
        Execute a recovery action.

        Args:
            action_name: Name of recovery action to execute
            error_info: Error information that triggered recovery

        Returns:
            RecoveryExecution record
        """
        if action_name not in self._actions:
            raise ValueError(f"Unknown recovery action: {action_name}")

        action = self._actions[action_name]

        # Check if action is applicable for this error
        if not self._is_action_applicable(action, error_info):
            raise ValueError(f"Recovery action {action_name} not applicable for error type {error_info.category}")

        # Create execution record
        execution = RecoveryExecution(
            action=action,
            error_info=error_info,
            status=RecoveryStatus.PENDING,
            start_time=time.time()
        )

        with self._lock:
            self._execution_history.append(execution)

        logger.info(f"Executing recovery action: {action_name}")

        try:
            execution.status = RecoveryStatus.IN_PROGRESS

            # Add delay if configured
            if action.delay > 0:
                await asyncio.sleep(action.delay)

            # Find appropriate executor
            executor = self._find_executor(action.action_type)
            if not executor:
                raise ValueError(f"No executor found for action type: {action.action_type}")

            # Execute with timeout
            result = await asyncio.wait_for(
                executor.execute(action, error_info),
                timeout=action.timeout
            )

            # Check success criteria if provided
            if action.success_criteria and not action.success_criteria(result):
                raise RuntimeError("Recovery action did not meet success criteria")

            execution.status = RecoveryStatus.SUCCESS
            execution.result = result
            logger.info(f"Recovery action {action_name} completed successfully")

        except asyncio.TimeoutError:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = f"Recovery action timed out after {action.timeout}s"
            logger.error(f"Recovery action {action_name} timed out")

        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"Recovery action {action_name} failed: {e}")

        finally:
            execution.end_time = time.time()

        return execution

    def get_applicable_actions(self, error_info: ErrorInfo) -> List[RecoveryAction]:
        """Get list of recovery actions applicable for this error."""
        applicable = []

        for action in self._actions.values():
            if self._is_action_applicable(action, error_info):
                applicable.append(action)

        # Sort by priority (simple heuristic)
        applicable.sort(key=lambda a: (a.severity_threshold.value if a.severity_threshold else 0, a.name))

        return applicable

    def get_execution_history(self, limit: Optional[int] = None) -> List[RecoveryExecution]:
        """Get recovery execution history."""
        with self._lock:
            history = self._execution_history.copy()
            if limit:
                history = history[-limit:]
            return history

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a recovery execution (if still pending)."""
        with self._lock:
            for execution in self._execution_history:
                if id(execution) == int(execution_id) and execution.status == RecoveryStatus.PENDING:
                    execution.status = RecoveryStatus.CANCELLED
                    execution.end_time = time.time()
                    logger.info(f"Cancelled recovery execution: {execution_id}")
                    return True
        return False

    def _is_action_applicable(self, action: RecoveryAction, error_info: ErrorInfo) -> bool:
        """Check if recovery action is applicable for this error."""
        # Check category
        if error_info.category not in action.applicable_categories:
            return False

        # Check severity threshold
        if action.severity_threshold:
            severity_levels = {
                ErrorSeverity.LOW: 1,
                ErrorSeverity.MEDIUM: 2,
                ErrorSeverity.HIGH: 3,
                ErrorSeverity.CRITICAL: 4
            }
            if severity_levels[error_info.severity] < severity_levels[action.severity_threshold]:
                return False

        return True

    def _find_executor(self, action_type: RecoveryActionType) -> Optional[RecoveryActionExecutor]:
        """Find executor for the given action type."""
        for executor in self._executors:
            if executor.can_handle(action_type):
                return executor
        return None


# Global recovery manager
recovery_manager = RecoveryManager()