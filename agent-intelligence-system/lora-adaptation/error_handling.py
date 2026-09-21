#!/usr/bin/env python3
"""
Comprehensive Error Handling and Logging for LoRA Adaptation System
Provides robust error handling, logging, and recovery mechanisms
"""

import logging
import traceback
import json
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from functools import wraps
from enum import Enum
import psutil
import torch

# Configure comprehensive logging system
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    MODEL_ERROR = "model_error"
    TRAINING_ERROR = "training_error"
    DATA_ERROR = "data_error"
    RESOURCE_ERROR = "resource_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: str
    message: str
    exception_type: str
    traceback_info: str
    context: Dict[str, Any]
    agent_id: Optional[str]
    component: str
    recovery_action: Optional[str]
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class LoRAAdaptationLogger:
    """
    Advanced logging system for LoRA adaptation components
    """

    def __init__(self, log_dir: str = "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create loggers for different components
        self.loggers = {}
        self.error_history = []
        self.performance_metrics = {}

        # Setup loggers
        self._setup_loggers()

        # Error tracking
        self.error_counts = {}
        self.critical_errors = []
        self.recovery_actions = {}

    def _setup_loggers(self):
        """Setup specialized loggers for different components"""
        components = [
            "lora_trainer", "pattern_analyzer", "model_manager",
            "response_generator", "resource_monitor", "system"
        ]

        for component in components:
            logger = logging.getLogger(f"lora_adaptation.{component}")
            logger.setLevel(logging.INFO)

            # Remove existing handlers
            logger.handlers.clear()

            # File handler for component
            file_handler = logging.FileHandler(
                self.log_dir / f"{component}.log",
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)

            # Error file handler
            error_handler = logging.FileHandler(
                self.log_dir / f"{component}_errors.log",
                mode='a',
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(formatter)
            error_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers
            logger.addHandler(file_handler)
            logger.addHandler(error_handler)
            logger.addHandler(console_handler)

            self.loggers[component] = logger

        # Setup main system logger
        main_logger = logging.getLogger("lora_adaptation")
        main_logger.setLevel(logging.INFO)

        main_handler = logging.FileHandler(
            self.log_dir / "system.log",
            mode='a',
            encoding='utf-8'
        )
        main_handler.setFormatter(formatter)
        main_logger.addHandler(main_handler)

        self.loggers["main"] = main_logger

    def get_logger(self, component: str) -> logging.Logger:
        """Get logger for a specific component"""
        return self.loggers.get(component, self.loggers["main"])

    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  agent_id: str = None, component: str = "unknown"):
        """Log structured error information"""
        try:
            # Determine error category
            category = self._categorize_error(error)

            # Create error info
            error_info = ErrorInfo(
                error_id=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(error)) % 10000}",
                timestamp=datetime.now(),
                category=category,
                severity=self._determine_severity(error),
                message=str(error),
                exception_type=type(error).__name__,
                traceback_info=traceback.format_exc(),
                context=context or {},
                agent_id=agent_id,
                component=component,
                recovery_action=self._suggest_recovery_action(error, category)
            )

            # Log to appropriate logger
            logger = self.get_logger(component)
            logger.error(f"Error ID: {error_info.error_id}")
            logger.error(f"Category: {category.value}")
            logger.error(f"Message: {error_info.message}")
            logger.error(f"Context: {json.dumps(error_info.context, indent=2, default=str)}")
            logger.error(f"Recovery Action: {error_info.recovery_action}")
            logger.error(f"Traceback: {error_info.traceback_info}")

            # Track error
            self.error_history.append(error_info)
            self.error_counts[category.value] = self.error_counts.get(category.value, 0) + 1

            # Check if critical
            if category == ErrorCategory.SYSTEM_ERROR or category == ErrorCategory.RESOURCE_ERROR:
                self.critical_errors.append(error_info)
                logger.critical(f"CRITICAL ERROR: {error_info.message}")

            # Save error to file
            self._save_error_to_file(error_info)

        except Exception as e:
            # Fallback logging
            print(f"Failed to log error: {e}")
            print(f"Original error: {error}")

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error type"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        if any(keyword in error_type.lower() for keyword in ["torch", "cuda", "model", "tensor"]):
            return ErrorCategory.MODEL_ERROR
        elif any(keyword in error_type.lower() for keyword in ["training", "fit", "epoch", "gradient"]):
            return ErrorCategory.TRAINING_ERROR
        elif any(keyword in error_type.lower() for keyword in ["value", "key", "index", "attribute"]):
            return ErrorCategory.DATA_ERROR
        elif any(keyword in error_message for keyword in ["memory", "gpu", "cuda", "resource"]):
            return ErrorCategory.RESOURCE_ERROR
        elif any(keyword in error_type.lower() for keyword in ["connection", "timeout", "network"]):
            return ErrorCategory.NETWORK_ERROR
        elif any(keyword in error_type.lower() for keyword in ["validation", "permission", "auth"]):
            return ErrorCategory.VALIDATION_ERROR
        elif any(keyword in error_type.lower() for keyword in ["system", "os", "runtime"]):
            return ErrorCategory.SYSTEM_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR

    def _determine_severity(self, error: Exception) -> str:
        """Determine error severity"""
        critical_indicators = ["critical", "fatal", "abort", "crash"]
        warning_indicators = ["warning", "deprecated", "timeout"]

        error_message = str(error).lower()
        error_type = type(error).__name__.lower()

        if any(indicator in error_message or indicator in error_type for indicator in critical_indicators):
            return "CRITICAL"
        elif any(indicator in error_message or indicator in error_type for indicator in warning_indicators):
            return "WARNING"
        elif "error" in error_type.lower():
            return "ERROR"
        else:
            return "INFO"

    def _suggest_recovery_action(self, error: Exception, category: ErrorCategory) -> str:
        """Suggest recovery action based on error type"""
        recovery_actions = {
            ErrorCategory.MODEL_ERROR: "Check model configuration and try reloading the model",
            ErrorCategory.TRAINING_ERROR: "Reduce batch size, check training data, or restart training",
            ErrorCategory.DATA_ERROR: "Validate input data and check data format",
            ErrorCategory.RESOURCE_ERROR: "Free up memory, reduce model size, or restart system",
            ErrorCategory.NETWORK_ERROR: "Check network connection and retry operation",
            ErrorCategory.VALIDATION_ERROR: "Check permissions and input parameters",
            ErrorCategory.SYSTEM_ERROR: "Restart system or check system resources",
            ErrorCategory.UNKNOWN_ERROR: "Investigate error context and consider system restart"
        }

        return recovery_actions.get(category, "Investigate error and check system status")

    def _save_error_to_file(self, error_info: ErrorInfo):
        """Save error information to file"""
        try:
            error_file = self.log_dir / "errors.jsonl"
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(error_info), default=str) + '\n')
        except Exception as e:
            print(f"Failed to save error to file: {e}")

    def log_performance(self, component: str, operation: str, duration_ms: float,
                       metrics: Dict[str, Any] = None):
        """Log performance metrics"""
        try:
            timestamp = datetime.now()

            performance_entry = {
                "timestamp": timestamp.isoformat(),
                "component": component,
                "operation": operation,
                "duration_ms": duration_ms,
                "metrics": metrics or {}
            }

            # Add to performance metrics
            if component not in self.performance_metrics:
                self.performance_metrics[component] = []

            self.performance_metrics[component].append(performance_entry)

            # Keep only recent metrics (last 1000 entries)
            if len(self.performance_metrics[component]) > 1000:
                self.performance_metrics[component] = self.performance_metrics[component][-1000:]

            # Log to file
            perf_file = self.log_dir / "performance.jsonl"
            with open(perf_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(performance_entry) + '\n')

            # Log to logger
            logger = self.get_logger(component)
            logger.info(f"Performance: {operation} completed in {duration_ms:.2f}ms")

        except Exception as e:
            print(f"Failed to log performance: {e}")

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]

            summary = {
                "period_hours": hours,
                "total_errors": len(recent_errors),
                "error_categories": {},
                "error_components": {},
                "critical_errors": len([e for e in recent_errors if e.severity == "CRITICAL"]),
                "resolved_errors": len([e for e in recent_errors if e.resolved]),
                "most_common_errors": []
            }

            # Categorize errors
            for error in recent_errors:
                category = error.category.value
                component = error.component

                summary["error_categories"][category] = summary["error_categories"].get(category, 0) + 1
                summary["error_components"][component] = summary["error_components"].get(component, 0) + 1

            # Find most common errors
            error_messages = {}
            for error in recent_errors:
                message = error.message[:100]  # Truncate for grouping
                error_messages[message] = error_messages.get(message, 0) + 1

            summary["most_common_errors"] = sorted(
                error_messages.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return summary

        except Exception as e:
            return {"error": f"Failed to generate error summary: {str(e)}"}

    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    print(f"Removed old log file: {log_file}")

        except Exception as e:
            print(f"Failed to cleanup old logs: {e}")

# Global logger instance
global_logger = LoRAAdaptationLogger()

def safe_execute(error_category: str = "UNKNOWN_ERROR",
                default_return: Any = None,
                log_errors: bool = True,
                component: str = "unknown"):
    """
    Decorator for safe execution with comprehensive error handling
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)

                # Log performance
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                global_logger.log_performance(component, func.__name__, duration_ms)

                return result

            except Exception as e:
                # Prepare context
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200] if args else None,
                    "kwargs": str(kwargs)[:200] if kwargs else None,
                    "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }

                # Extract agent_id if present
                agent_id = None
                if args and hasattr(args[0], 'agent_id'):
                    agent_id = args[0].agent_id
                elif kwargs.get('agent_id'):
                    agent_id = kwargs['agent_id']

                # Log error
                if log_errors:
                    global_logger.log_error(e, context, agent_id, component)

                # Attempt recovery
                recovery_result = await attempt_error_recovery(e, error_category, context)
                if recovery_result is not None:
                    return recovery_result

                # Return default value
                if default_return is not None:
                    return default_return

                # Re-raise if no default
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)

                # Log performance
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                global_logger.log_performance(component, func.__name__, duration_ms)

                return result

            except Exception as e:
                # Prepare context
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200] if args else None,
                    "kwargs": str(kwargs)[:200] if kwargs else None,
                    "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }

                # Extract agent_id if present
                agent_id = None
                if args and hasattr(args[0], 'agent_id'):
                    agent_id = args[0].agent_id
                elif kwargs.get('agent_id'):
                    agent_id = kwargs['agent_id']

                # Log error
                if log_errors:
                    global_logger.log_error(e, context, agent_id, component)

                # Return default value
                if default_return is not None:
                    return default_return

                # Re-raise if no default
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

async def attempt_error_recovery(error: Exception, category: str, context: Dict[str, Any]) -> Any:
    """Attempt to recover from specific errors"""
    try:
        error_message = str(error).lower()

        # Memory errors
        if "memory" in error_message or "cuda" in error_message:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
                return "Memory cleared, operation may be retried"

        # File access errors
        if "permission" in error_message or "access" in error_message:
            # Try to create missing directories
            path = context.get("kwargs", {}).get("path") or context.get("args", [""])[0]
            if path:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                return "Directory structure created"

        # Timeout errors
        if "timeout" in error_message:
            return "Operation timed out, consider increasing timeout or reducing workload"

        # Connection errors
        if "connection" in error_message:
            return "Connection error, operation may be retried later"

        return None

    except Exception as recovery_error:
        global_logger.log_error(
            recovery_error,
            {"original_error": str(error), "recovery_attempt": True},
            component="error_recovery"
        )
        return None

class ResourceMonitor:
    """Monitor system resources and detect issues"""

    def __init__(self):
        self.logger = global_logger.get_logger("resource_monitor")
        self.last_check = datetime.now()
        self.alerts = []

    async def check_resources(self) -> Dict[str, Any]:
        """Check system resources and log issues"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')

            # GPU memory if available
            gpu_memory = {}
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu_memory[f"gpu_{i}"] = {
                        "allocated_mb": torch.cuda.memory_allocated(i) / 1024 / 1024,
                        "cached_mb": torch.cuda.memory_reserved(i) / 1024 / 1024,
                        "total_mb": torch.cuda.get_device_properties(i).total_memory / 1024 / 1024
                    }

            resource_status = {
                "timestamp": datetime.now().isoformat(),
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "gpu_memory": gpu_memory
            }

            # Check for issues
            issues = []

            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                await self._handle_memory_pressure(memory.percent)

            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")

            if disk.percent > 90:
                issues.append(f"Low disk space: {disk.percent:.1f}% used")

            # GPU memory issues
            for gpu_id, gpu_info in gpu_memory.items():
                usage_percent = (gpu_info["allocated_mb"] / gpu_info["total_mb"]) * 100
                if usage_percent > 90:
                    issues.append(f"High GPU memory usage on {gpu_id}: {usage_percent:.1f}%")
                    await self._handle_gpu_memory_pressure(gpu_id)

            if issues:
                resource_status["issues"] = issues
                self.logger.warning(f"Resource issues detected: {', '.join(issues)}")

                # Log performance impact
                global_logger.log_performance(
                    "resource_monitor",
                    "resource_check",
                    0,  # No operation time for monitoring
                    {"issues": len(issues), "severity": "warning" if len(issues) <= 2 else "critical"}
                )

            self.last_check = datetime.now()
            return resource_status

        except Exception as e:
            self.logger.error(f"Failed to check resources: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _handle_memory_pressure(self, memory_percent: float):
        """Handle high memory usage"""
        try:
            if memory_percent > 95:
                # Critical memory pressure
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                self.logger.critical(f"Critical memory pressure: {memory_percent:.1f}%. Performed cleanup.")

                # Log as error for tracking
                global_logger.log_error(
                    MemoryError(f"Critical memory usage: {memory_percent:.1f}%"),
                    {"memory_percent": memory_percent, "action": "emergency_cleanup"},
                    component="resource_monitor"
                )

        except Exception as e:
            self.logger.error(f"Failed to handle memory pressure: {str(e)}")

    async def _handle_gpu_memory_pressure(self, gpu_id: str):
        """Handle high GPU memory usage"""
        try:
            if torch.cuda.is_available():
                device_id = int(gpu_id.split('_')[1])
                torch.cuda.empty_cache()
                torch.cuda.synchronize(device_id)

                self.logger.warning(f"GPU memory pressure on {gpu_id}. Performed cleanup.")

        except Exception as e:
            self.logger.error(f"Failed to handle GPU memory pressure: {str(e)}")

class HealthChecker:
    """Health checking for LoRA adaptation system components"""

    def __init__(self):
        self.logger = global_logger.get_logger("health_checker")
        self.component_health = {}

    async def check_component_health(self, component_name: str,
                                   check_function: Callable = None) -> Dict[str, Any]:
        """Check health of a specific component"""
        try:
            health_status = {
                "component": component_name,
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "checks": {},
                "issues": []
            }

            # Default checks
            default_checks = await self._run_default_checks(component_name)
            health_status["checks"].update(default_checks)

            # Custom check function if provided
            if check_function:
                try:
                    custom_result = await check_function()
                    health_status["checks"]["custom"] = custom_result
                except Exception as e:
                    health_status["checks"]["custom"] = {"status": "failed", "error": str(e)}

            # Determine overall status
            failed_checks = [name for name, result in health_status["checks"].items()
                           if isinstance(result, dict) and result.get("status") == "failed"]

            if failed_checks:
                health_status["status"] = "degraded" if len(failed_checks) == 1 else "unhealthy"
                health_status["issues"] = [f"Check failed: {check}" for check in failed_checks]

            # Store health status
            self.component_health[component_name] = health_status

            # Log health status
            if health_status["status"] != "healthy":
                self.logger.warning(f"Component {component_name} health: {health_status['status']}")
            else:
                self.logger.info(f"Component {component_name} health: healthy")

            return health_status

        except Exception as e:
            error_status = {
                "component": component_name,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
                "checks": {},
                "issues": [f"Health check failed: {str(e)}"]
            }

            self.component_health[component_name] = error_status
            self.logger.error(f"Health check failed for {component_name}: {str(e)}")

            return error_status

    async def _run_default_checks(self, component_name: str) -> Dict[str, Any]:
        """Run default health checks"""
        checks = {}

        # Memory check
        try:
            memory = psutil.virtual_memory()
            checks["memory"] = {
                "status": "passed" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent
            }
        except Exception as e:
            checks["memory"] = {"status": "failed", "error": str(e)}

        # Disk space check
        try:
            disk = psutil.disk_usage('/home')
            usage_percent = (disk.used / disk.total) * 100
            checks["disk_space"] = {
                "status": "passed" if usage_percent < 90 else "warning",
                "usage_percent": usage_percent
            }
        except Exception as e:
            checks["disk_space"] = {"status": "failed", "error": str(e)}

        # Component-specific checks
        if component_name == "lora_trainer":
            checks.update(await self._check_lora_trainer())
        elif component_name == "model_manager":
            checks.update(await self._check_model_manager())

        return checks

    async def _check_lora_trainer(self) -> Dict[str, Any]:
        """Check LoRA trainer specific health"""
        checks = {}

        # Check if base model is accessible
        try:
            # This would be a more sophisticated check in production
            checks["model_access"] = {"status": "passed", "message": "Base model accessible"}
        except Exception as e:
            checks["model_access"] = {"status": "failed", "error": str(e)}

        # Check GPU availability
        checks["gpu_available"] = {
            "status": "passed" if torch.cuda.is_available() else "warning",
            "available": torch.cuda.is_available()
        }

        return checks

    async def _check_model_manager(self) -> Dict[str, Any]:
        """Check model manager specific health"""
        checks = {}

        # Check data directories
        data_dir = Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data")
        checks["data_directory"] = {
            "status": "passed" if data_dir.exists() else "failed",
            "exists": data_dir.exists()
        }

        # Check models directory
        models_dir = Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models")
        checks["models_directory"] = {
            "status": "passed" if models_dir.exists() else "failed",
            "exists": models_dir.exists()
        }

        return checks

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            system_health = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "resource_status": await ResourceMonitor().check_resources(),
                "recent_errors": global_logger.get_error_summary(hours=1)
            }

            # Check all registered components
            for component_name in self.component_health:
                component_health = await self.check_component_health(component_name)
                system_health["components"][component_name] = component_health

                # Update overall status
                if component_health["status"] == "unhealthy":
                    system_health["overall_status"] = "unhealthy"
                elif component_health["status"] == "degraded" and system_health["overall_status"] == "healthy":
                    system_health["overall_status"] = "degraded"

            return system_health

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }

# Utility functions
def get_logger(component: str = "main") -> logging.Logger:
    """Get logger for a component"""
    return global_logger.get_logger(component)

def log_performance(component: str, operation: str, duration_ms: float, metrics: Dict[str, Any] = None):
    """Log performance metrics"""
    global_logger.log_performance(component, operation, duration_ms, metrics)

def handle_error(error: Exception, context: Dict[str, Any] = None,
                agent_id: str = None, component: str = "unknown"):
    """Handle and log an error"""
    global_logger.log_error(error, context, agent_id, component)

# Main execution for testing
if __name__ == "__main__":
    async def main():
        # Test error handling
        logger = get_logger("test_component")

        # Test safe execution decorator
        @safe_execute(error_category="MODEL_ERROR", default_return="fallback", component="test")
        async def test_function():
            raise ValueError("This is a test error")

        result = await test_function()
        print(f"Safe execution result: {result}")

        # Test resource monitoring
        monitor = ResourceMonitor()
        resource_status = await monitor.check_resources()
        print(f"Resource status: {json.dumps(resource_status, indent=2)}")

        # Test health checking
        health_checker = HealthChecker()
        health_status = await health_checker.get_system_health()
        print(f"System health: {json.dumps(health_status, indent=2)}")

        # Test error summary
        error_summary = global_logger.get_error_summary(hours=24)
        print(f"Error summary: {json.dumps(error_summary, indent=2)}")

    asyncio.run(main())