#!/usr/bin/env python3
"""
Discovery API for DMLogn8n Multi-Agent Platform

This module provides REST API endpoints for service discovery operations including:
- Service registration and discovery endpoints
- Health check management endpoints
- Configuration management endpoints
- Load balancing endpoints
- Agent coordination endpoints
- Metrics and monitoring endpoints
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Query, Body, Path, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import discovery modules
from .consul_manager import ConsulManager, ConsulConfig
from .service_registry import ServiceRegistry, ServiceRegistration, ServiceMetadata, ServiceEndpoint, HealthCheck, ServiceType
from .health_checker import HealthChecker, HealthCheckDefinition, CheckType, HealthStatus
from .config_distributor import ConfigDistributor, ConfigEntry, ConfigScope, ConfigFormat
from .load_balancer import LoadBalancer, LoadBalancerConfig, LoadBalancingAlgorithm
from .agent_coordinator import AgentCoordinator, AgentDefinition, AgentTask, AgentCapability, AgentType, TaskPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ServiceRegistrationRequest(BaseModel):
    service_name: str
    service_type: str
    version: str
    description: str
    host: str
    port: int
    health_endpoint: str = "/health"
    owner: str = "system"
    team: str = "platform"
    environment: str = "production"
    region: str = "us-east-1"
    capabilities: List[str] = []
    dependencies: List[str] = []
    tags: List[str] = []
    custom_attributes: Dict[str, Any] = {}

class ServiceDiscoveryRequest(BaseModel):
    service_name: Optional[str] = None
    service_type: Optional[str] = None
    tags: Optional[List[str]] = None
    healthy_only: bool = True
    passing_only: bool = True

class HealthCheckRequest(BaseModel):
    check_id: str
    name: str
    service_id: str
    check_type: str
    target: str
    interval: int = 10
    timeout: int = 3
    headers: Optional[Dict[str, str]] = None
    expected_status: int = 200

class ConfigRequest(BaseModel):
    key: str
    value: Any
    scope: str = "service"
    format: str = "json"
    schema_id: Optional[str] = None
    encrypted: bool = False
    metadata: Optional[Dict[str, Any]] = None

class LoadBalancerRequest(BaseModel):
    service_name: str
    algorithm: str
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 5
    enable_sticky_sessions: bool = False

class AgentRegistrationRequest(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    version: str
    description: str
    capabilities: List[Dict[str, Any]]
    max_workload: int = 10
    personality_traits: Dict[str, Any] = {}
    knowledge_domains: List[str] = []

class TaskSubmissionRequest(BaseModel):
    task_type: str
    priority: int = 2
    payload: Dict[str, Any]
    requirements: List[str] = []
    timeout: int = 300
    max_retries: int = 3

class DiscoveryAPI:
    """
    REST API for DMLogn8n service discovery operations
    """

    def __init__(self):
        self.app = FastAPI(
            title="DMLogn8n Service Discovery API",
            description="Comprehensive service discovery and management API",
            version="1.0.0"
        )

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize discovery components
        self.consul_manager = None
        self.service_registry = None
        self.health_checker = None
        self.config_distributor = None
        self.load_balancer = None
        self.agent_coordinator = None

        # Setup routes
        self._setup_routes()

    async def initialize(self, consul_config: ConsulConfig, encryption_key: Optional[str] = None) -> bool:
        """Initialize discovery components"""
        try:
            # Initialize Consul manager
            self.consul_manager = ConsulManager(consul_config)
            if not await self.consul_manager.initialize():
                logger.error("Failed to initialize Consul manager")
                return False

            # Initialize components
            self.service_registry = ServiceRegistry(self.consul_manager)
            self.health_checker = HealthChecker(self.consul_manager)
            self.config_distributor = ConfigDistributor(self.consul_manager, encryption_key)
            self.load_balancer = LoadBalancer(self.consul_manager)
            self.agent_coordinator = AgentCoordinator(self.consul_manager)

            # Initialize agent coordinator
            if not await self.agent_coordinator.initialize():
                logger.error("Failed to initialize agent coordinator")
                return False

            # Create default schemas
            await self.config_distributor.create_default_schemas()

            # Create system health check
            await self.health_checker.create_system_health_check()

            logger.info("Discovery API initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Discovery API initialization failed: {e}")
            return False

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "DMLogn8n Service Discovery API", "version": "1.0.0"}

        @self.app.get("/health")
        async def api_health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # Service Registry Routes
        @self.app.post("/services/register")
        async def register_service(request: ServiceRegistrationRequest):
            try:
                # Create service metadata
                metadata = ServiceMetadata(
                    service_id=f"{request.service_name}-{request.host}:{request.port}",
                    service_name=request.service_name,
                    service_type=ServiceType(request.service_type),
                    version=request.version,
                    description=request.description,
                    owner=request.owner,
                    team=request.team,
                    environment=request.environment,
                    region=request.region,
                    capabilities=request.capabilities,
                    dependencies=request.dependencies,
                    tags=request.tags,
                    custom_attributes=request.custom_attributes
                )

                # Create service endpoint
                endpoint = ServiceEndpoint(
                    host=request.host,
                    port=request.port,
                    health_endpoint=request.health_endpoint
                )

                # Create health check
                health_check = HealthCheck()

                # Create service registration
                registration = ServiceRegistration(
                    metadata=metadata,
                    endpoint=endpoint,
                    health_check=health_check
                )

                success = await self.service_registry.register_service(registration)
                if success:
                    return {"message": "Service registered successfully", "service_id": metadata.service_id}
                else:
                    raise HTTPException(status_code=500, detail="Failed to register service")

            except Exception as e:
                logger.error(f"Service registration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/services/discover")
        async def discover_services(request: ServiceDiscoveryRequest):
            try:
                service_type = ServiceType(request.service_type) if request.service_type else None

                services = await self.service_registry.discover_services(
                    service_name=request.service_name,
                    service_type=service_type,
                    tags=request.tags,
                    healthy_only=request.healthy_only,
                    passing_only=request.passing_only
                )

                return {"services": services, "count": len(services)}

            except Exception as e:
                logger.error(f"Service discovery error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/services/{service_id}")
        async def get_service_details(service_id: str):
            try:
                service = await self.service_registry.get_service_details(service_id)
                if service:
                    return service
                else:
                    raise HTTPException(status_code=404, detail="Service not found")

            except Exception as e:
                logger.error(f"Service details error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.delete("/services/{service_id}")
        async def deregister_service(service_id: str):
            try:
                success = await self.service_registry.deregister_service(service_id)
                if success:
                    return {"message": "Service deregistered successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to deregister service")

            except Exception as e:
                logger.error(f"Service deregistration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/services/topology")
        async def get_service_topology():
            try:
                topology = await self.service_registry.get_service_topology()
                return topology

            except Exception as e:
                logger.error(f"Service topology error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Health Check Routes
        @self.app.post("/health/checks")
        async def register_health_check(request: HealthCheckRequest):
            try:
                check_def = HealthCheckDefinition(
                    check_id=request.check_id,
                    name=request.name,
                    service_id=request.service_id,
                    check_type=CheckType(request.check_type),
                    target=request.target,
                    interval=request.interval,
                    timeout=request.timeout,
                    headers=request.headers,
                    expected_status=request.expected_status
                )

                success = await self.health_checker.register_check(check_def)
                if success:
                    return {"message": "Health check registered successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to register health check")

            except Exception as e:
                logger.error(f"Health check registration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/health/services/{service_id}")
        async def get_service_health(service_id: str):
            try:
                health = await self.health_checker.get_service_health(service_id)
                return health

            except Exception as e:
                logger.error(f"Service health error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/health/cluster")
        async def get_cluster_health():
            try:
                health = await self.health_checker.get_cluster_health()
                return health

            except Exception as e:
                logger.error(f"Cluster health error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/health/checks/{check_id}/execute")
        async def execute_health_check(check_id: str):
            try:
                result = await self.health_checker.execute_check(check_id)
                return asdict(result)

            except Exception as e:
                logger.error(f"Health check execution error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Configuration Routes
        @self.app.post("/config")
        async def store_config(request: ConfigRequest):
            try:
                success = await self.config_distributor.store_config(
                    key=request.key,
                    value=request.value,
                    scope=ConfigScope(request.scope),
                    format=ConfigFormat(request.format),
                    schema_id=request.schema_id,
                    encrypted=request.encrypted,
                    metadata=request.metadata
                )

                if success:
                    return {"message": "Configuration stored successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to store configuration")

            except Exception as e:
                logger.error(f"Config store error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/config/{key}")
        async def get_config(key: str, scope: Optional[str] = None):
            try:
                config_scope = ConfigScope(scope) if scope else None
                config = await self.config_distributor.get_config(key, config_scope)

                if config:
                    return asdict(config)
                else:
                    raise HTTPException(status_code=404, detail="Configuration not found")

            except Exception as e:
                logger.error(f"Config retrieval error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/config/{key}/value")
        async def get_config_value(key: str, default: Any = None, scope: Optional[str] = None):
            try:
                config_scope = ConfigScope(scope) if scope else None
                value = await self.config_distributor.get_config_value(key, default, config_scope)
                return {"key": key, "value": value}

            except Exception as e:
                logger.error(f"Config value error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.put("/config/{key}")
        async def update_config(key: str, value: Any = Body(...)):
            try:
                success = await self.config_distributor.update_config(key, value)
                if success:
                    return {"message": "Configuration updated successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update configuration")

            except Exception as e:
                logger.error(f"Config update error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.delete("/config/{key}")
        async def delete_config(key: str, scope: Optional[str] = None):
            try:
                config_scope = ConfigScope(scope) if scope else None
                success = await self.config_distributor.delete_config(key, config_scope)
                if success:
                    return {"message": "Configuration deleted successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to delete configuration")

            except Exception as e:
                logger.error(f"Config delete error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/config/{key}/history")
        async def get_config_history(key: str, limit: int = 10):
            try:
                history = await self.config_distributor.get_config_history(key, limit)
                return {"key": key, "history": [asdict(v) for v in history]}

            except Exception as e:
                logger.error(f"Config history error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Load Balancer Routes
        @self.app.post("/loadbalancer")
        async def register_load_balancer(request: LoadBalancerRequest):
            try:
                config = LoadBalancerConfig(
                    algorithm=LoadBalancingAlgorithm(request.algorithm),
                    service_name=request.service_name,
                    health_check_interval=request.health_check_interval,
                    circuit_breaker_threshold=request.circuit_breaker_threshold,
                    enable_sticky_sessions=request.enable_sticky_sessions
                )

                success = await self.load_balancer.register_load_balancer(config)
                if success:
                    return {"message": "Load balancer registered successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to register load balancer")

            except Exception as e:
                logger.error(f"Load balancer registration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/loadbalancer/{service_name}/select")
        async def select_instance(service_name: str, client_ip: Optional[str] = None, session_id: Optional[str] = None):
            try:
                instance = await self.load_balancer.select_instance(service_name, client_ip, session_id)
                if instance:
                    return asdict(instance)
                else:
                    raise HTTPException(status_code=404, detail="No healthy instances available")

            except Exception as e:
                logger.error(f"Instance selection error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/loadbalancer/{service_name}/route")
        async def route_request(service_name: str, request_path: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[str] = None, client_ip: Optional[str] = None, session_id: Optional[str] = None):
            try:
                success, response_data, error = await self.load_balancer.route_request(
                    service_name=service_name,
                    request_path=request_path,
                    method=method,
                    headers=headers,
                    body=body,
                    client_ip=client_ip,
                    session_id=session_id
                )

                return {
                    "success": success,
                    "response": response_data,
                    "error": error
                }

            except Exception as e:
                logger.error(f"Request routing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/loadbalancer/{service_name}/metrics")
        async def get_load_balancer_metrics(service_name: str):
            try:
                metrics = await self.load_balancer.get_load_balancer_metrics(service_name)
                return metrics

            except Exception as e:
                logger.error(f"Load balancer metrics error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Agent Coordinator Routes
        @self.app.post("/agents")
        async def register_agent(request: AgentRegistrationRequest):
            try:
                # Create capabilities
                capabilities = []
                for cap_data in request.capabilities:
                    capability = AgentCapability(
                        capability_id=cap_data.get('capability_id', f"cap_{len(capabilities)}"),
                        name=cap_data['name'],
                        description=cap_data.get('description', ''),
                        category=cap_data.get('category', 'general'),
                        version=cap_data.get('version', '1.0.0'),
                        parameters=cap_data.get('parameters', {}),
                        performance_metrics=cap_data.get('performance_metrics', {}),
                        supported_languages=cap_data.get('supported_languages', []),
                        max_concurrent_tasks=cap_data.get('max_concurrent_tasks', 1),
                        resource_requirements=cap_data.get('resource_requirements', {})
                    )
                    capabilities.append(capability)

                # Create agent definition
                agent_def = AgentDefinition(
                    agent_id=request.agent_id,
                    name=request.name,
                    agent_type=AgentType(request.agent_type),
                    version=request.version,
                    description=request.description,
                    capabilities=capabilities,
                    personality_traits=request.personality_traits,
                    knowledge_domains=request.knowledge_domains,
                    max_workload=request.max_workload
                )

                success = await self.agent_coordinator.register_agent(agent_def)
                if success:
                    return {"message": "Agent registered successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to register agent")

            except Exception as e:
                logger.error(f"Agent registration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agents/tasks")
        async def submit_task(request: TaskSubmissionRequest):
            try:
                task = AgentTask(
                    task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.agent_coordinator.agent_tasks)}",
                    task_type=request.task_type,
                    priority=TaskPriority(request.priority),
                    payload=request.payload,
                    requirements=request.requirements,
                    timeout=request.timeout,
                    max_retries=request.max_retries
                )

                task_id = await self.agent_coordinator.submit_task(task)
                if task_id:
                    return {"message": "Task submitted successfully", "task_id": task_id}
                else:
                    raise HTTPException(status_code=500, detail="Failed to submit task")

            except Exception as e:
                logger.error(f"Task submission error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/agents/{agent_id}")
        async def get_agent_status(agent_id: str):
            try:
                status = await self.agent_coordinator.get_agent_status(agent_id)
                if status:
                    return status
                else:
                    raise HTTPException(status_code=404, detail="Agent not found")

            except Exception as e:
                logger.error(f"Agent status error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/agents")
        async def list_agents(agent_type: Optional[str] = None):
            try:
                agents = []
                for agent_id, agent in self.agent_coordinator.registered_agents.items():
                    if not agent_type or agent.agent_type.value == agent_type:
                        status = await self.agent_coordinator.get_agent_status(agent_id)
                        agents.append(status)

                return {"agents": agents, "count": len(agents)}

            except Exception as e:
                logger.error(f"Agent listing error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agents/{capability}")
        async def find_agents_by_capability(capability: str, requirements: Optional[Dict[str, Any]] = None):
            try:
                agents = await self.agent_coordinator.find_agents_by_capability(capability, requirements)
                return {"capability": capability, "agents": agents, "count": len(agents)}

            except Exception as e:
                logger.error(f"Agent search error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agents/collaboration")
        async def start_collaboration(agents: List[str], collaboration_type: str, context: Dict[str, Any]):
            try:
                session_id = await self.agent_coordinator.start_collaboration(agents, collaboration_type, context)
                if session_id:
                    return {"message": "Collaboration started successfully", "session_id": session_id}
                else:
                    raise HTTPException(status_code=500, detail="Failed to start collaboration")

            except Exception as e:
                logger.error(f"Collaboration start error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agents/collaboration/{session_id}/message")
        async def send_collaboration_message(session_id: str, sender_agent_id: str, message: Dict[str, Any]):
            try:
                success = await self.agent_coordinator.send_collaboration_message(session_id, sender_agent_id, message)
                if success:
                    return {"message": "Message sent successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to send message")

            except Exception as e:
                logger.error(f"Collaboration message error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agents/collaboration/{session_id}/end")
        async def end_collaboration(session_id: str, result: Optional[Dict[str, Any]] = None):
            try:
                success = await self.agent_coordinator.end_collaboration(session_id, result)
                if success:
                    return {"message": "Collaboration ended successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to end collaboration")

            except Exception as e:
                logger.error(f"Collaboration end error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Metrics and Monitoring Routes
        @self.app.get("/metrics/coordinator")
        async def get_coordinator_metrics():
            try:
                metrics = await self.agent_coordinator.get_coordinator_metrics()
                return metrics

            except Exception as e:
                logger.error(f"Coordinator metrics error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/metrics/cluster")
        async def get_cluster_metrics():
            try:
                # Get cluster status from Consul manager
                cluster_status = await self.consul_manager.get_cluster_status()
                return cluster_status

            except Exception as e:
                logger.error(f"Cluster metrics error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Error handlers
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
            )

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance"""
        return self.app

    async def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the API server"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()

        except Exception as e:
            logger.error(f"API server error: {e}")
            raise

    async def shutdown(self):
        """Shutdown the API and all components"""
        try:
            if self.agent_coordinator:
                await self.agent_coordinator.shutdown()

            if self.load_balancer:
                await self.load_balancer.shutdown()

            if self.health_checker:
                await self.health_checker.shutdown()

            if self.config_distributor:
                await self.config_distributor.shutdown()

            if self.service_registry:
                await self.service_registry.shutdown()

            if self.consul_manager:
                await self.consul_manager.cleanup()

            logger.info("Discovery API shutdown completed")

        except Exception as e:
            logger.error(f"API shutdown error: {e}")

# Create global API instance
api = DiscoveryAPI()

# Export main functions
__all__ = [
    'DiscoveryAPI',
    'api'
]

if __name__ == "__main__":
    # Example usage
    async def main():
        # Initialize with default Consul config
        consul_config = ConsulConfig(
            host="localhost",
            port=8500
        )

        if await api.initialize(consul_config):
            await api.run(host="0.0.0.0", port=8080)

    asyncio.run(main())