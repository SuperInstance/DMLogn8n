#!/usr/bin/env python3
"""
DMLogn8n Startup Sequencer - Intelligent Service Startup Orchestration
Manages proper startup sequences with dependency resolution and health checks
"""

import asyncio
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import aiofiles
from pathlib import Path
import networkx as nx  # For dependency graph analysis

class StartupPhase(Enum):
    INITIALIZATION = "initialization"
    DEPENDENCY_CHECK = "dependency_check"
    PRE_STARTUP = "pre_startup"
    STARTUP = "startup"
    POST_STARTUP = "post_startup"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"

class ServiceStartupStatus(Enum):
    PENDING = "pending"
    DEPENDENCIES_CHECKING = "dependencies_checking"
    DEPENDENCIES_READY = "dependencies_ready"
    STARTING = "starting"
    HEALTH_CHECKING = "health_checking"
    READY = "ready"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StartupDependency:
    service_name: str
    required: bool = True  # False means optional dependency
    min_version: Optional[str] = None
    health_check_required: bool = True
    timeout: int = 60

@dataclass
class ServiceStartupConfig:
    name: str
    version: str
    startup_order: int = 0
    dependencies: List[StartupDependency] = field(default_factory=list)
    startup_timeout: int = 120
    health_check_timeout: int = 30
    health_check_interval: int = 5
    max_health_checks: int = 12  # 60 seconds with 5-second intervals
    pre_startup_commands: List[str] = field(default_factory=list)
    post_startup_commands: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    required_ports: List[int] = field(default_factory=list)
    startup_script: Optional[str] = None
    startup_class: Optional[str] = None
    auto_restart: bool = True
    max_restart_attempts: int = 3
    restart_delay: int = 10
    skip_on_failure: bool = False
    custom_health_check: Optional[str] = None

@dataclass
class StartupState:
    config: ServiceStartupConfig
    status: ServiceStartupStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attempts: int = 0
    error_message: Optional[str] = None
    health_check_results: List[bool] = field(default_factory=list)
    dependencies_satisfied: bool = False
    process_id: Optional[int] = None
    logs: List[str] = field(default_factory=list)

class StartupSequencer:
    """
    Intelligent startup sequencer with dependency resolution and health monitoring
    """

    def __init__(self, event_bus=None, service_registry=None):
        self.event_bus = event_bus
        self.service_registry = service_registry
        self.logger = logging.getLogger('StartupSequencer')

        # Configuration
        self.startup_configs: Dict[str, ServiceStartupConfig] = {}
        self.startup_states: Dict[str, StartupState] = {}
        self.dependency_graph = nx.DiGraph()

        # Startup orchestration
        self.current_phase = StartupPhase.INITIALIZATION
        self.startup_start_time: Optional[float] = None
        self.startup_end_time: Optional[float] = None
        self.startup_complete = asyncio.Event()

        # Parallel execution control
        self.max_parallel_startups = 5
        self.current_startups: Set[str] = set()
        self.startup_semaphore = asyncio.Semaphore(self.max_parallel_startups)

        # Configuration files
        self.config_file = "/home/activeloguser/DMLogn8n/master/startup_config.json"
        self.state_file = "/home/activeloguser/DMLogn8n/data/startup_state.json"

        # Startup metrics
        self.startup_metrics = {
            'total_services': 0,
            'successful_startups': 0,
            'failed_startups': 0,
            'skipped_startups': 0,
            'total_startup_time': 0,
            'average_service_startup_time': 0,
            'dependency_checks_performed': 0,
            'health_checks_performed': 0,
            'restarts_performed': 0
        }

        # Startup hooks
        self.phase_hooks: Dict[StartupPhase, List[Callable]] = {
            phase: [] for phase in StartupPhase
        }

    async def initialize(self):
        """Initialize the startup sequencer"""
        self.logger.info("Initializing Startup Sequencer...")

        # Ensure data directory exists
        await aiofiles.os.makedirs(Path(self.state_file).parent, exist_ok=True)

        # Load startup configuration
        await self._load_startup_config()

        # Build dependency graph
        self._build_dependency_graph()

        # Validate configuration
        self._validate_configuration()

        self.logger.info(f"Startup Sequencer initialized with {len(self.startup_configs)} services")

    async def execute_startup(self) -> bool:
        """Execute the complete startup sequence"""
        self.logger.info("Starting DMLogn8n platform startup sequence...")
        self.startup_start_time = time.time()

        try:
            # Phase 1: Initialization
            await self._execute_phase(StartupPhase.INITIALIZATION)

            # Phase 2: Dependency Check
            await self._execute_phase(StartupPhase.DEPENDENCY_CHECK)

            # Phase 3: Pre-startup
            await self._execute_phase(StartupPhase.PRE_STARTUP)

            # Phase 4: Startup (main phase)
            await self._execute_phase(StartupPhase.STARTUP)

            # Phase 5: Post-startup
            await self._execute_phase(StartupPhase.POST_STARTUP)

            # Phase 6: Verification
            await self._execute_phase(StartupPhase.VERIFICATION)

            # Mark as completed
            self.current_phase = StartupPhase.COMPLETED
            self.startup_end_time = time.time()
            self.startup_complete.set()

            # Calculate final metrics
            self._calculate_final_metrics()

            self.logger.info("DMLogn8n platform startup completed successfully!")

            # Publish completion event
            if self.event_bus:
                await self.event_bus.publish("startup.completed", {
                    'startup_time': self.startup_end_time - self.startup_start_time,
                    'successful_services': self.startup_metrics['successful_startups'],
                    'failed_services': self.startup_metrics['failed_startups']
                })

            return True

        except Exception as e:
            self.logger.error(f"Startup sequence failed: {e}")
            self.current_phase = StartupPhase.FAILED
            await self._handle_startup_failure(e)
            return False

    async def _execute_phase(self, phase: StartupPhase):
        """Execute a specific startup phase"""
        self.logger.info(f"Executing startup phase: {phase.value}")
        self.current_phase = phase

        # Execute phase hooks
        await self._execute_phase_hooks(phase)

        # Phase-specific logic
        if phase == StartupPhase.INITIALIZATION:
            await self._phase_initialization()
        elif phase == StartupPhase.DEPENDENCY_CHECK:
            await self._phase_dependency_check()
        elif phase == StartupPhase.PRE_STARTUP:
            await self._phase_pre_startup()
        elif phase == StartupPhase.STARTUP:
            await self._phase_startup()
        elif phase == StartupPhase.POST_STARTUP:
            await self._phase_post_startup()
        elif phase == StartupPhase.VERIFICATION:
            await self._phase_verification()

        self.logger.info(f"Completed startup phase: {phase.value}")

    async def _phase_initialization(self):
        """Initialize startup environment"""
        self.logger.info("Initializing startup environment...")

        # Reset startup states
        for service_name, config in self.startup_configs.items():
            self.startup_states[service_name] = StartupState(
                config=config,
                status=ServiceStartupStatus.PENDING
            )

        # Check system requirements
        await self._check_system_requirements()

        # Initialize service states
        self.startup_metrics['total_services'] = len(self.startup_configs)

    async def _phase_dependency_check(self):
        """Check all service dependencies"""
        self.logger.info("Checking service dependencies...")

        # Create dependency graph and validate
        if not self._validate_dependencies():
            raise ValueError("Dependency validation failed")

        # Check if all dependencies can be satisfied
        for service_name in nx.topological_sort(self.dependency_graph):
            await self._check_service_dependencies(service_name)

        self.logger.info("Dependency check completed")

    async def _phase_pre_startup(self):
        """Execute pre-startup commands and preparations"""
        self.logger.info("Executing pre-startup tasks...")

        tasks = []
        for service_name, state in self.startup_states.items():
            if state.config.pre_startup_commands:
                task = asyncio.create_task(self._execute_pre_startup_commands(service_name))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _phase_startup(self):
        """Start all services in dependency order"""
        self.logger.info("Starting services...")

        # Get services in dependency order
        startup_order = list(nx.topological_sort(self.dependency_graph))

        # Start services with parallel execution where possible
        for service_name in startup_order:
            async with self.startup_semaphore:
                await self._startup_service(service_name)

    async def _phase_post_startup(self):
        """Execute post-startup commands"""
        self.logger.info("Executing post-startup tasks...")

        for service_name, state in self.startup_states.items():
            if state.status == ServiceStartupStatus.READY and state.config.post_startup_commands:
                try:
                    await self._execute_post_startup_commands(service_name)
                except Exception as e:
                    self.logger.error(f"Post-startup commands failed for {service_name}: {e}")

    async def _phase_verification(self):
        """Verify all services are running correctly"""
        self.logger.info("Verifying service health...")

        verification_results = {}
        for service_name, state in self.startup_states.items():
            if state.status == ServiceStartupStatus.READY:
                healthy = await self._verify_service_health(service_name)
                verification_results[service_name] = healthy

                if not healthy:
                    state.status = ServiceStartupStatus.FAILED
                    state.error_message = "Post-startup health check failed"
                    self.startup_metrics['failed_startups'] += 1
                    self.startup_metrics['successful_startups'] -= 1

        # Report verification results
        successful_verifications = sum(1 for result in verification_results.values() if result)
        self.logger.info(f"Verification completed: {successful_verifications}/{len(verification_results)} services healthy")

    async def _startup_service(self, service_name: str):
        """Start a single service"""
        state = self.startup_states[service_name]
        config = state.config

        if state.status != ServiceStartupStatus.PENDING:
            return

        self.logger.info(f"Starting service: {service_name}")
        state.status = ServiceStartupStatus.STARTING
        state.start_time = time.time()
        state.attempts += 1

        try:
            # Check dependencies
            if not await self._ensure_dependencies_ready(service_name):
                if config.skip_on_failure:
                    state.status = ServiceStartupStatus.SKIPPED
                    self.startup_metrics['skipped_startups'] += 1
                    self.logger.warning(f"Skipping {service_name} due to unsatisfied dependencies")
                    return
                else:
                    raise RuntimeError(f"Dependencies not ready for {service_name}")

            # Start the service
            await self._start_service_process(service_name)

            # Wait for service to be ready
            await self._wait_for_service_ready(service_name)

            state.status = ServiceStartupStatus.READY
            state.end_time = time.time()
            self.startup_metrics['successful_startups'] += 1

            self.logger.info(f"Service {service_name} started successfully")

            # Publish startup event
            if self.event_bus:
                await self.event_bus.publish("service.started", {
                    'service_name': service_name,
                    'startup_time': state.end_time - state.start_time,
                    'attempt': state.attempts
                })

        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            state.status = ServiceStartupStatus.FAILED
            state.error_message = str(e)
            state.end_time = time.time()
            self.startup_metrics['failed_startups'] += 1

            # Attempt restart if configured
            if config.auto_restart and state.attempts < config.max_restart_attempts:
                self.logger.info(f"Restarting {service_name} (attempt {state.attempts + 1})")
                await asyncio.sleep(config.restart_delay)
                await self._startup_service(service_name)
                self.startup_metrics['restarts_performed'] += 1

    async def _start_service_process(self, service_name: str):
        """Start the actual service process"""
        state = self.startup_states[service_name]
        config = state.config

        if config.startup_script:
            # Start using script
            await self._start_script_service(service_name)
        elif config.startup_class:
            # Start using Python class
            await self._start_class_service(service_name)
        else:
            raise ValueError(f"No startup method configured for {service_name}")

    async def _start_script_service(self, service_name: str):
        """Start service using shell script"""
        state = self.startup_states[service_name]
        config = state.config

        import subprocess
        import os

        # Prepare environment
        env = os.environ.copy()
        env.update(config.environment_variables)

        # Start the process
        process = await asyncio.create_subprocess_shell(
            config.startup_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        state.process_id = process.pid
        self.current_startups.add(service_name)

        # Monitor process
        asyncio.create_task(self._monitor_process(service_name, process))

    async def _start_class_service(self, service_name: str):
        """Start service using Python class"""
        state = self.startup_states[service_name]
        config = state.class_service

        # Import and instantiate the class
        module_name, class_name = config.startup_class.rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        service_class = getattr(module, class_name)

        # Create and start service
        service_instance = service_class()

        if hasattr(service_instance, 'start'):
            if asyncio.iscoroutinefunction(service_instance.start):
                await service_instance.start()
            else:
                await asyncio.get_event_loop().run_in_executor(None, service_instance.start)

        # Store instance for monitoring
        state.service_instance = service_instance
        self.current_startups.add(service_name)

    async def _monitor_process(self, service_name: str, process):
        """Monitor a running process"""
        state = self.startup_states[service_name]

        try:
            return_code = await process.wait()

            if return_code != 0:
                error_output = await process.stderr.read()
                state.error_message = f"Process exited with code {return_code}: {error_output.decode()}"
                self.logger.error(f"Process for {service_name} failed: {state.error_message}")

        except Exception as e:
            self.logger.error(f"Error monitoring process for {service_name}: {e}")
        finally:
            self.current_startups.discard(service_name)

    async def _wait_for_service_ready(self, service_name: str):
        """Wait for service to be ready with health checks"""
        state = self.startup_states[service_name]
        config = state.config

        self.logger.info(f"Waiting for {service_name} to be ready...")

        for attempt in range(config.max_health_checks):
            try:
                if await self._check_service_health(service_name):
                    state.health_check_results.append(True)
                    self.logger.info(f"{service_name} is ready after {attempt + 1} health checks")
                    return
                else:
                    state.health_check_results.append(False)

            except Exception as e:
                self.logger.debug(f"Health check {attempt + 1} failed for {service_name}: {e}")

            await asyncio.sleep(config.health_check_interval)

        raise TimeoutError(f"Service {service_name} did not become ready within timeout")

    async def _check_service_health(self, service_name: str) -> bool:
        """Check health of a specific service"""
        state = self.startup_states[service_name]
        config = state.config

        try:
            if config.custom_health_check:
                # Custom health check
                return await self._execute_custom_health_check(service_name)
            else:
                # Default health checks
                return await self._execute_default_health_checks(service_name)

        except Exception as e:
            self.logger.debug(f"Health check error for {service_name}: {e}")
            return False

    async def _execute_default_health_checks(self, service_name: str) -> bool:
        """Execute default health checks"""
        state = self.startup_states[service_name]
        config = state.config

        # Check if process is running
        if hasattr(state, 'process_id') and state.process_id:
            if not await self._is_process_running(state.process_id):
                return False

        # Check ports
        for port in config.required_ports:
            if not await self._is_port_available(port, check_listening=True):
                return False

        # Check service registry if available
        if self.service_registry:
            services = await self.service_registry.discover_services(
                name=service_name,
                healthy_only=True
            )
            if not services:
                return False

        return True

    async def _execute_custom_health_check(self, service_name: str) -> bool:
        """Execute custom health check"""
        state = self.startup_states[service_name]
        config = state.config

        # Import and execute custom health check
        module_name, function_name = config.custom_health_check.rsplit('.', 1)
        module = __import__(module_name, fromlist=[function_name])
        health_check_func = getattr(module, function_name)

        if asyncio.iscoroutinefunction(health_check_func):
            return await health_check_func(service_name)
        else:
            return await asyncio.get_event_loop().run_in_executor(
                None, health_check_func, service_name
            )

    async def _is_process_running(self, pid: int) -> bool:
        """Check if process is running"""
        import psutil
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False

    async def _is_port_available(self, port: int, check_listening: bool = False) -> bool:
        """Check if port is available or listening"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0 if check_listening else result != 0
        except:
            return False

    def _build_dependency_graph(self):
        """Build dependency graph from service configurations"""
        self.dependency_graph.clear()

        # Add nodes
        for service_name in self.startup_configs:
            self.dependency_graph.add_node(service_name)

        # Add edges
        for service_name, config in self.startup_configs.items():
            for dep in config.dependencies:
                if dep.service_name in self.startup_configs:
                    self.dependency_graph.add_edge(dep.service_name, service_name)

    def _validate_dependencies(self) -> bool:
        """Validate dependency graph for circular dependencies"""
        try:
            # Check for circular dependencies
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                self.logger.error(f"Circular dependencies detected: {cycles}")
                return False

            # Check if all dependencies exist
            for service_name, config in self.startup_configs.items():
                for dep in config.dependencies:
                    if dep.service_name not in self.startup_configs:
                        self.logger.error(f"Dependency {dep.service_name} not found for {service_name}")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return False

    async def _check_service_dependencies(self, service_name: str):
        """Check if service dependencies are satisfied"""
        state = self.startup_states[service_name]
        config = state.config

        for dep in config.dependencies:
            if dep.service_name in self.startup_states:
                dep_state = self.startup_states[dep.service_name]
                if dep.required and dep_state.status not in [ServiceStartupStatus.READY]:
                    state.dependencies_satisfied = False
                    return

        state.dependencies_satisfied = True
        self.startup_metrics['dependency_checks_performed'] += 1

    async def _ensure_dependencies_ready(self, service_name: str) -> bool:
        """Ensure all dependencies are ready"""
        state = self.startup_states[service_name]
        config = state.config

        for dep in config.dependencies:
            if dep.service_name in self.startup_states:
                dep_state = self.startup_states[dep.service_name]

                if dep.required:
                    # Wait for dependency to be ready
                    timeout = time.time() + dep.timeout
                    while time.time() < timeout:
                        if dep_state.status == ServiceStartupStatus.READY:
                            break
                        await asyncio.sleep(1)
                    else:
                        return False

                elif dep.health_check_required:
                    # Check health of optional dependency
                    if dep_state.status == ServiceStartupStatus.READY:
                        if not await self._check_service_health(dep.service_name):
                            if dep.required:
                                return False

        return True

    async def _execute_pre_startup_commands(self, service_name: str):
        """Execute pre-startup commands for a service"""
        state = self.startup_states[service_name]
        config = state.config

        for command in config.pre_startup_commands:
            self.logger.info(f"Executing pre-startup command for {service_name}: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Pre-startup command failed: {stderr.decode()}")

            state.logs.append(f"Pre-startup: {command} -> {stdout.decode().strip()}")

    async def _execute_post_startup_commands(self, service_name: str):
        """Execute post-startup commands for a service"""
        state = self.startup_states[service_name]
        config = state.config

        for command in config.post_startup_commands:
            self.logger.info(f"Executing post-startup command for {service_name}: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                self.logger.error(f"Post-startup command failed: {stderr.decode()}")
                continue

            state.logs.append(f"Post-startup: {command} -> {stdout.decode().strip()}")

    async def _verify_service_health(self, service_name: str) -> bool:
        """Final verification of service health"""
        try:
            return await self._check_service_health(service_name)
        except:
            return False

    async def _check_system_requirements(self):
        """Check system requirements"""
        self.logger.info("Checking system requirements...")

        # Check Python version
        import sys
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8 or higher required")

        # Check available memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.available < 1024 * 1024 * 1024:  # 1GB
                self.logger.warning("Low memory available")
        except ImportError:
            self.logger.warning("psutil not available, skipping memory check")

    async def _execute_phase_hooks(self, phase: StartupPhase):
        """Execute hooks for a specific phase"""
        for hook in self.phase_hooks[phase]:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    await asyncio.get_event_loop().run_in_executor(None, hook)
            except Exception as e:
                self.logger.error(f"Phase hook failed for {phase}: {e}")

    async def _handle_startup_failure(self, error: Exception):
        """Handle startup failure"""
        self.logger.error(f"Startup failed: {error}")

        # Publish failure event
        if self.event_bus:
            await self.event_bus.publish("startup.failed", {
                'error': str(error),
                'phase': self.current_phase.value,
                'successful_services': self.startup_metrics['successful_startups'],
                'failed_services': self.startup_metrics['failed_startups']
            })

    def _calculate_final_metrics(self):
        """Calculate final startup metrics"""
        if self.startup_start_time and self.startup_end_time:
            self.startup_metrics['total_startup_time'] = (
                self.startup_end_time - self.startup_start_time
            )

        if self.startup_metrics['successful_startups'] > 0:
            total_service_time = sum(
                state.end_time - state.start_time
                for state in self.startup_states.values()
                if state.start_time and state.end_time and state.status == ServiceStartupStatus.READY
            )
            self.startup_metrics['average_service_startup_time'] = (
                total_service_time / self.startup_metrics['successful_startups']
            )

    async def _load_startup_config(self):
        """Load startup configuration from file"""
        try:
            if await aiofiles.os.path.exists(self.config_file):
                async with aiofiles.open(self.config_file, 'r') as f:
                    data = json.loads(await f.read())

                for service_config in data.get('services', []):
                    # Convert dependencies
                    deps = []
                    for dep_data in service_config.get('dependencies', []):
                        deps.append(StartupDependency(**dep_data))

                    config = ServiceStartupConfig(
                        **{k: v for k, v in service_config.items() if k != 'dependencies'},
                        dependencies=deps
                    )
                    self.startup_configs[config.name] = config

                self.logger.info(f"Loaded {len(self.startup_configs)} service configurations")

        except Exception as e:
            self.logger.error(f"Error loading startup configuration: {e}")
            raise

    def _validate_configuration(self):
        """Validate startup configuration"""
        for service_name, config in self.startup_configs.items():
            if not config.startup_script and not config.startup_class:
                raise ValueError(f"Service {service_name} has no startup method configured")

    def add_phase_hook(self, phase: StartupPhase, hook: Callable):
        """Add a hook for a specific startup phase"""
        self.phase_hooks[phase].append(hook)

    def get_startup_status(self) -> Dict[str, Any]:
        """Get comprehensive startup status"""
        return {
            'current_phase': self.current_phase.value,
            'startup_complete': self.startup_complete.is_set(),
            'metrics': self.startup_metrics,
            'services': {
                name: {
                    'status': state.status.value,
                    'attempts': state.attempts,
                    'start_time': state.start_time,
                    'end_time': state.end_time,
                    'error_message': state.error_message,
                    'dependencies_satisfied': state.dependencies_satisfied
                }
                for name, state in self.startup_states.items()
            },
            'current_startups': list(self.current_startups),
            'dependency_graph_size': len(self.dependency_graph.nodes()),
            'dependency_edges': len(self.dependency_graph.edges())
        }