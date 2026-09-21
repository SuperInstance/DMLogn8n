#!/usr/bin/env python3
"""
DMLogn8n Platform Orchestrator - Central Nervous System
Master coordinator for the entire DMLogn8n platform
"""

import asyncio
import signal
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import aiofiles
from pathlib import Path

class ServiceStatus(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"

class ServicePriority(Enum):
    CRITICAL = 1  # Core services like database, event bus
    HIGH = 2      # Essential services like API gateway
    NORMAL = 3    # Standard services
    LOW = 4       # Optional services

@dataclass
class ServiceDefinition:
    name: str
    version: str
    priority: ServicePriority
    dependencies: List[str] = field(default_factory=list)
    startup_order: int = 0
    health_check_endpoint: Optional[str] = None
    startup_timeout: int = 60
    shutdown_timeout: int = 30
    restart_on_failure: bool = True
    max_restarts: int = 3
    restart_delay: int = 5
    command: Optional[str] = None
    module_path: Optional[str] = None
    config_file: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    ports: List[int] = field(default_factory=list)

@dataclass
class ServiceState:
    definition: ServiceDefinition
    status: ServiceStatus
    process: Optional[Any] = None
    pid: Optional[int] = None
    start_time: Optional[float] = None
    last_health_check: Optional[float] = None
    restart_count: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

class PlatformOrchestrator:
    """
    Master orchestrator for the entire DMLogn8n platform
    Coordinates all services with proper dependency management
    """

    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/home/activeloguser/DMLogn8n/master/platform_config.json"
        self.logger = self._setup_logging()
        self.services: Dict[str, ServiceState] = {}
        self.service_graph: Dict[str, List[str]] = {}
        self.shutdown_event = asyncio.Event()
        self.startup_complete = asyncio.Event()
        self.platform_metrics = {
            'start_time': None,
            'uptime': 0,
            'total_services': 0,
            'running_services': 0,
            'failed_services': 0
        }

        # Core components (will be initialized)
        self.service_registry = None
        self.event_bus = None
        self.health_monitor = None
        self.config_manager = None

        # Signal handlers
        self._setup_signal_handlers()

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for the orchestrator"""
        logger = logging.getLogger('PlatformOrchestrator')
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        log_file = Path("/home/activeloguser/DMLogn8n/logs/orchestrator.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, lambda s, f: asyncio.create_task(self._shutdown_handler()))

    async def initialize(self):
        """Initialize the orchestrator and load configuration"""
        self.logger.info("Initializing Platform Orchestrator...")

        # Load configuration
        await self._load_configuration()

        # Initialize core components
        await self._initialize_core_components()

        # Register services
        await self._register_services()

        # Build dependency graph
        self._build_dependency_graph()

        self.logger.info(f"Platform Orchestrator initialized with {len(self.services)} services")

    async def _load_configuration(self):
        """Load platform configuration from file"""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                config = json.loads(await f.read())

            # Import and initialize config manager
            from .config_master import ConfigMaster
            self.config_manager = ConfigMaster(config)

            self.logger.info("Configuration loaded successfully")

        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_path}")
            self.logger.info("Creating default configuration...")
            await self._create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    async def _create_default_config(self):
        """Create default platform configuration"""
        default_config = {
            "environment": "development",
            "services": [
                {
                    "name": "database",
                    "version": "1.0.0",
                    "priority": "critical",
                    "startup_order": 1,
                    "command": "redis-server",
                    "ports": [6379],
                    "health_check_endpoint": "http://localhost:6379/ping"
                },
                {
                    "name": "event_bus",
                    "version": "1.0.0",
                    "priority": "critical",
                    "startup_order": 2,
                    "dependencies": ["database"],
                    "module_path": "event_bus",
                    "ports": [6380]
                },
                {
                    "name": "service_registry",
                    "version": "1.0.0",
                    "priority": "critical",
                    "startup_order": 3,
                    "dependencies": ["database", "event_bus"],
                    "module_path": "service_registry",
                    "ports": [6381]
                },
                {
                    "name": "health_monitor",
                    "version": "1.0.0",
                    "priority": "high",
                    "startup_order": 4,
                    "dependencies": ["service_registry"],
                    "module_path": "health_monitor_global",
                    "ports": [6382]
                },
                {
                    "name": "api_gateway",
                    "version": "1.0.0",
                    "priority": "high",
                    "startup_order": 5,
                    "dependencies": ["service_registry", "event_bus"],
                    "module_path": "api_gateway_master",
                    "ports": [8000]
                },
                {
                    "name": "n8n_instance",
                    "version": "1.0.0",
                    "priority": "normal",
                    "startup_order": 6,
                    "dependencies": ["database", "api_gateway"],
                    "command": "npm start",
                    "ports": [5678]
                }
            ],
            "global_settings": {
                "startup_timeout": 300,
                "shutdown_timeout": 60,
                "health_check_interval": 30,
                "enable_auto_recovery": True,
                "log_level": "INFO"
            }
        }

        # Write default config
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.config_path, 'w') as f:
            await f.write(json.dumps(default_config, indent=2))

        from .config_master import ConfigMaster
        self.config_manager = ConfigMaster(default_config)

        self.logger.info(f"Default configuration created at {self.config_path}")

    async def _initialize_core_components(self):
        """Initialize core platform components"""
        self.logger.info("Initializing core components...")

        # Import components
        from .service_registry import ServiceRegistry
        from .event_bus import EventBus
        from .health_monitor_global import GlobalHealthMonitor

        # Initialize event bus first
        self.event_bus = EventBus()
        await self.event_bus.initialize()

        # Initialize service registry
        self.service_registry = ServiceRegistry(self.event_bus)
        await self.service_registry.initialize()

        # Initialize health monitor
        self.health_monitor = GlobalHealthMonitor(self.event_bus)
        await self.health_monitor.initialize()

        self.logger.info("Core components initialized")

    async def _register_services(self):
        """Register all services from configuration"""
        services_config = self.config_manager.get('services', [])

        for service_config in services_config:
            definition = ServiceDefinition(**service_config)
            state = ServiceState(definition=definition, status=ServiceStatus.STOPPED)
            self.services[definition.name] = state

            # Register with service registry
            await self.service_registry.register_service(
                name=definition.name,
                service_type="platform_service",
                host="localhost",
                ports=definition.ports,
                metadata={
                    "version": definition.version,
                    "priority": definition.priority.value,
                    "dependencies": definition.dependencies,
                    "startup_order": definition.startup_order
                }
            )

        self.platform_metrics['total_services'] = len(self.services)
        self.logger.info(f"Registered {len(self.services)} services")

    def _build_dependency_graph(self):
        """Build service dependency graph"""
        for service_name, service_state in self.services.items():
            dependencies = service_state.definition.dependencies
            self.service_graph[service_name] = dependencies

            # Validate dependencies exist
            for dep in dependencies:
                if dep not in self.services:
                    self.logger.error(f"Service {service_name} depends on unknown service {dep}")
                    raise ValueError(f"Unknown dependency: {dep}")

        # Check for circular dependencies
        self._check_circular_dependencies()

        self.logger.info("Service dependency graph built successfully")

    def _check_circular_dependencies(self):
        """Check for circular dependencies using DFS"""
        def dfs(node, visited, rec_stack):
            if node in rec_stack:
                raise ValueError(f"Circular dependency detected involving {node}")
            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.service_graph.get(node, []):
                dfs(neighbor, visited, rec_stack)

            rec_stack.remove(node)

        visited = set()
        for service_name in self.services:
            if service_name not in visited:
                dfs(service_name, visited, set())

    async def start_platform(self):
        """Start the entire platform in dependency order"""
        self.logger.info("Starting DMLogn8n Platform...")
        self.platform_metrics['start_time'] = time.time()

        try:
            # Get services in startup order
            startup_order = self._calculate_startup_order()

            # Start services in order
            for service_name in startup_order:
                await self._start_service(service_name)

                # Wait for service to be healthy
                await self._wait_for_service_healthy(service_name)

            # Start health monitoring
            await self.health_monitor.start_monitoring()

            # Mark startup as complete
            self.startup_complete.set()

            self.logger.info("DMLogn8n Platform started successfully!")
            await self.event_bus.publish("platform.started", {
                "services": list(self.services.keys()),
                "startup_time": time.time() - self.platform_metrics['start_time']
            })

            # Keep running until shutdown
            await self.shutdown_event.wait()

        except Exception as e:
            self.logger.error(f"Failed to start platform: {e}")
            await self.shutdown_platform()
            raise

    def _calculate_startup_order(self) -> List[str]:
        """Calculate service startup order based on dependencies"""
        # Sort by startup_order first, then by priority
        services_by_order = {}

        for name, state in self.services.items():
            order = state.definition.startup_order
            if order not in services_by_order:
                services_by_order[order] = []
            services_by_order[order].append(name)

        # Sort order groups and then by priority within each group
        startup_order = []
        for order in sorted(services_by_order.keys()):
            services = services_by_order[order]
            services.sort(key=lambda x: self.services[x].definition.priority.value)
            startup_order.extend(services)

        return startup_order

    async def _start_service(self, service_name: str):
        """Start a single service"""
        service_state = self.services[service_name]

        if service_state.status != ServiceStatus.STOPPED:
            self.logger.warning(f"Service {service_name} is not stopped (current: {service_state.status})")
            return

        self.logger.info(f"Starting service: {service_name}")
        service_state.status = ServiceStatus.STARTING

        try:
            definition = service_state.definition

            if definition.module_path:
                # Start Python module
                await self._start_module_service(service_name)
            elif definition.command:
                # Start external command
                await self._start_command_service(service_name)
            else:
                raise ValueError(f"No startup method defined for service {service_name}")

            service_state.status = ServiceStatus.RUNNING
            service_state.start_time = time.time()
            self.platform_metrics['running_services'] += 1

            await self.event_bus.publish("service.started", {
                "service": service_name,
                "version": definition.version
            })

            self.logger.info(f"Service {service_name} started successfully")

        except Exception as e:
            service_state.status = ServiceStatus.ERROR
            service_state.error_message = str(e)
            self.platform_metrics['failed_services'] += 1

            self.logger.error(f"Failed to start service {service_name}: {e}")
            await self.event_bus.publish("service.error", {
                "service": service_name,
                "error": str(e)
            })

            if service_state.definition.priority == ServicePriority.CRITICAL:
                raise RuntimeError(f"Critical service {service_name} failed to start")

    async def _start_module_service(self, service_name: str):
        """Start a Python module service"""
        service_state = self.services[service_name]
        definition = service_state.definition

        # Import the module
        module_name = f".{definition.module_path}"
        module = __import__(module_name, fromlist=[definition.module_path])

        # Get the main class or function
        service_class = getattr(module, definition.module_path.title().replace('_', ''))

        # Start the service
        if asyncio.iscoroutinefunction(service_class):
            # It's a coroutine function
            service_task = await service_class()
        else:
            # It's a class
            service_instance = service_class()
            if hasattr(service_instance, 'start'):
                service_task = await service_instance.start()
            else:
                service_task = asyncio.create_task(service_instance.run())

        service_state.process = service_task

        self.logger.info(f"Module service {service_name} started")

    async def _start_command_service(self, service_name: str):
        """Start an external command service"""
        service_state = self.services[service_name]
        definition = service_state.definition

        # Create subprocess
        import subprocess
        process = await asyncio.create_subprocess_shell(
            definition.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **definition.environment}
        )

        service_state.process = process
        service_state.pid = process.pid

        self.logger.info(f"Command service {service_name} started with PID {process.pid}")

    async def _wait_for_service_healthy(self, service_name: str, timeout: int = 60):
        """Wait for a service to become healthy"""
        service_state = self.services[service_name]
        definition = service_state.definition

        if not definition.health_check_endpoint:
            # For services without health check, wait a bit
            await asyncio.sleep(2)
            return

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Perform health check
                healthy = await self._perform_health_check(service_name)
                if healthy:
                    service_state.last_health_check = time.time()
                    return

            except Exception as e:
                self.logger.debug(f"Health check failed for {service_name}: {e}")

            await asyncio.sleep(1)

        raise TimeoutError(f"Service {service_name} did not become healthy within {timeout} seconds")

    async def _perform_health_check(self, service_name: str) -> bool:
        """Perform health check for a service"""
        service_state = self.services[service_name]
        definition = service_state.definition

        if not definition.health_check_endpoint:
            return True

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(definition.health_check_endpoint, timeout=5) as response:
                    return response.status == 200
        except:
            return False

    async def shutdown_platform(self):
        """Gracefully shutdown the entire platform"""
        self.logger.info("Shutting down DMLogn8n Platform...")

        # Stop health monitoring
        if self.health_monitor:
            await self.health_monitor.stop_monitoring()

        # Get services in reverse startup order
        startup_order = self._calculate_startup_order()
        shutdown_order = list(reversed(startup_order))

        # Stop services in reverse order
        for service_name in shutdown_order:
            await self._stop_service(service_name)

        # Shutdown core components
        if self.service_registry:
            await self.service_registry.shutdown()

        if self.event_bus:
            await self.event_bus.shutdown()

        self.logger.info("DMLogn8n Platform shutdown complete")

    async def _stop_service(self, service_name: str):
        """Stop a single service"""
        service_state = self.services[service_name]

        if service_state.status in [ServiceStatus.STOPPED, ServiceStatus.STOPPING]:
            return

        self.logger.info(f"Stopping service: {service_name}")
        service_state.status = ServiceStatus.STOPPING

        try:
            definition = service_state.definition

            if service_state.process:
                if hasattr(service_state.process, 'terminate'):
                    # It's a subprocess
                    service_state.process.terminate()
                    try:
                        await asyncio.wait_for(service_state.process.wait(), timeout=definition.shutdown_timeout)
                    except asyncio.TimeoutError:
                        service_state.process.kill()
                        await service_state.process.wait()
                elif hasattr(service_state.process, 'cancel'):
                    # It's an asyncio task
                    service_state.process.cancel()
                    try:
                        await service_state.process
                    except asyncio.CancelledError:
                        pass
                elif hasattr(service_state.process, 'stop'):
                    # Custom stop method
                    await service_state.process.stop()

            service_state.status = ServiceStatus.STOPPED
            service_state.process = None
            service_state.pid = None
            self.platform_metrics['running_services'] -= 1

            await self.event_bus.publish("service.stopped", {"service": service_name})

            self.logger.info(f"Service {service_name} stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping service {service_name}: {e}")
            service_state.status = ServiceStatus.ERROR

    async def _shutdown_handler(self):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.shutdown_event.set()

    def get_platform_status(self) -> Dict[str, Any]:
        """Get comprehensive platform status"""
        return {
            "platform_metrics": self.platform_metrics,
            "services": {
                name: {
                    "status": state.status.value,
                    "start_time": state.start_time,
                    "last_health_check": state.last_health_check,
                    "error_message": state.error_message,
                    "restart_count": state.restart_count,
                    "metrics": state.metrics
                }
                for name, state in self.services.items()
            },
            "uptime": time.time() - (self.platform_metrics['start_time'] or time.time()),
            "startup_complete": self.startup_complete.is_set()
        }

    async def restart_service(self, service_name: str):
        """Restart a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")

        self.logger.info(f"Restarting service: {service_name}")

        await self._stop_service(service_name)
        await asyncio.sleep(2)  # Brief pause
        await self._start_service(service_name)
        await self._wait_for_service_healthy(service_name)

        self.logger.info(f"Service {service_name} restarted successfully")

async def main():
    """Main entry point for the platform orchestrator"""
    orchestrator = PlatformOrchestrator()

    try:
        await orchestrator.initialize()
        await orchestrator.start_platform()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt")
    except Exception as e:
        print(f"Platform error: {e}")
        return 1
    finally:
        await orchestrator.shutdown_platform()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))