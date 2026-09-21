#!/usr/bin/env python3
"""
Service Deployer for DMLogn8n
Deploys all services with proper orchestration and startup sequences
"""

import os
import sys
import json
import time
import logging
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import docker
from docker.models.services import Service


class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DeploymentType(Enum):
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    NATIVE = "native"


@dataclass
class ServiceConfig:
    name: str
    image: str
    port: int
    environment: Dict[str, str]
    volumes: List[str]
    depends_on: List[str]
    health_check: Optional[Dict[str, Any]]
    restart_policy: str = "unless-stopped"
    deployment_type: DeploymentType = DeploymentType.DOCKER_COMPOSE


class ServiceDeployer:
    """Service deployment and orchestration manager"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Paths
        self.deploy_dir = Path(__file__).parent
        self.docker_dir = self.deploy_dir / "docker"
        self.k8s_dir = self.deploy_dir / "k8s"
        self.config_dir = Path("/etc/dmlogn8n")
        self.compose_file = self.docker_dir / "docker-compose.yml"

        # Docker client
        self.docker_client = None

        # Service configurations
        self.services = self.get_service_configurations()

        # Deployment order and dependencies
        self.deployment_order = [
            "mysql",
            "redis",
            "n8n",
            "character-coder",
            "dmlogn8n-api",
            "player-portal",
            "nginx"
        ]

    def get_service_configurations(self) -> List[ServiceConfig]:
        """Get service configurations based on environment"""
        base_env_vars = {
            "ENVIRONMENT": self.environment,
            "TZ": "UTC",
            "LOG_LEVEL": "INFO" if self.environment == "production" else "DEBUG"
        }

        services = [
            ServiceConfig(
                name="mysql",
                image="mysql:8.0",
                port=3306,
                environment={
                    **base_env_vars,
                    "MYSQL_ROOT_PASSWORD": "dmlogn8n_root_password",
                    "MYSQL_DATABASE": "dmlogn8n",
                    "MYSQL_USER": "dmlogn8n_user",
                    "MYSQL_PASSWORD": "dmlogn8n_password"
                },
                volumes=[
                    "mysql_data:/var/lib/mysql",
                    f"{self.config_dir}/mysql/my.cnf:/etc/mysql/conf.d/my.cnf"
                ],
                depends_on=[],
                health_check={
                    "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="redis",
                image="redis:7-alpine",
                port=6379,
                environment={**base_env_vars},
                volumes=[
                    "redis_data:/data",
                    f"{self.config_dir}/redis/redis.conf:/etc/redis/redis.conf"
                ],
                depends_on=[],
                health_check={
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="n8n",
                image="n8nio/n8n:latest",
                port=5678,
                environment={
                    **base_env_vars,
                    "N8N_BASIC_AUTH_ACTIVE": "true",
                    "N8N_BASIC_AUTH_USER": "admin",
                    "N8N_BASIC_AUTH_PASSWORD": "n8n_admin_password",
                    "N8N_HOST": "localhost",
                    "N8N_PORT": "5678",
                    "N8N_PROTOCOL": "http",
                    "WEBHOOK_URL": "http://localhost:5678/",
                    "DB_TYPE": "mysql",
                    "DB_MYSQLDB_HOST": "mysql",
                    "DB_MYSQLDB_PORT": "3306",
                    "DB_MYSQLDB_DATABASE": "n8n",
                    "DB_MYSQLDB_USER": "n8n_user",
                    "DB_MYSQLDB_PASSWORD": "n8n_password",
                    "QUEUE_BULL_REDIS_HOST": "redis",
                    "QUEUE_BULL_REDIS_PORT": "6379"
                },
                volumes=[
                    "n8n_data:/home/node/.n8n",
                    f"{self.config_dir}/n8n:/etc/n8n"
                ],
                depends_on=["mysql", "redis"],
                health_check={
                    "test": ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:5678/healthz"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="character-coder",
                image="dmlogn8n/character-coder:latest",
                port=3001,
                environment={
                    **base_env_vars,
                    "DATABASE_URL": "mysql://dmlogn8n_user:dmlogn8n_password@mysql:3306/dmlogn8n",
                    "REDIS_URL": "redis://redis:6379",
                    "N8N_WEBHOOK_URL": "http://n8n:5678/webhook",
                    "FLASK_ENV": self.environment,
                    "SECRET_KEY": "character_coder_secret_key"
                },
                volumes=[
                    f"{self.config_dir}/character-coder:/app/config",
                    f"/var/log/dmlogn8n:/app/logs"
                ],
                depends_on=["mysql", "redis", "n8n"],
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:3001/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="dmlogn8n-api",
                image="dmlogn8n/api:latest",
                port=8000,
                environment={
                    **base_env_vars,
                    "DATABASE_URL": "mysql://dmlogn8n_user:dmlogn8n_password@mysql:3306/dmlogn8n",
                    "REDIS_URL": "redis://redis:6379",
                    "JWT_SECRET_KEY": "jwt_secret_key",
                    "CORS_ORIGINS": "*",
                    "RATE_LIMIT": "100/hour"
                },
                volumes=[
                    f"{self.config_dir}/api:/app/config",
                    f"/var/log/dmlogn8n:/app/logs"
                ],
                depends_on=["mysql", "redis"],
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="player-portal",
                image="dmlogn8n/player-portal:latest",
                port=3000,
                environment={
                    **base_env_vars,
                    "REACT_APP_API_URL": "http://localhost:8000",
                    "REACT_APP_N8N_URL": "http://localhost:5678",
                    "REACT_APP_WS_URL": "ws://localhost:8000"
                },
                volumes=[],
                depends_on=["dmlogn8n-api", "n8n"],
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost:3000"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            ),
            ServiceConfig(
                name="nginx",
                image="nginx:alpine",
                port=80,
                environment={**base_env_vars},
                volumes=[
                    f"{self.config_dir}/nginx/nginx.conf:/etc/nginx/nginx.conf",
                    f"{self.config_dir}/nginx/conf.d:/etc/nginx/conf.d",
                    f"{self.config_dir}/ssl:/etc/nginx/ssl",
                    "/var/log/nginx:/var/log/nginx"
                ],
                depends_on=["player-portal", "dmlogn8n-api", "character-coder"],
                health_check={
                    "test": ["CMD", "curl", "-f", "http://localhost/health"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            )
        ]

        # Environment-specific modifications
        if self.environment == "production":
            # Add production-specific services and configurations
            for service in services:
                if service.name == "nginx":
                    service.port = 443  # HTTPS
                    service.environment["SSL_ENABLED"] = "true"

        return {service.name: service for service in services}

    def initialize_docker_client(self) -> bool:
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            return False

    def generate_docker_compose(self) -> bool:
        """Generate docker-compose.yml file"""
        try:
            self.logger.info("Generating docker-compose configuration...")

            compose_config = {
                "version": "3.8",
                "services": {},
                "volumes": {},
                "networks": {
                    "dmlogn8n-network": {
                        "driver": "bridge"
                    }
                }
            }

            # Add services
            for service_name, service_config in self.services.items():
                service_definition = {
                    "image": service_config.image,
                    "container_name": f"dmlogn8n-{service_name}",
                    "environment": service_config.environment,
                    "volumes": service_config.volumes,
                    "depends_on": service_config.depends_on,
                    "restart": service_config.restart_policy,
                    "networks": ["dmlogn8n-network"],
                    "logging": {
                        "driver": "json-file",
                        "options": {
                            "max-size": "10m",
                            "max-file": "3"
                        }
                    }
                }

                # Add port mapping
                if service_name != "mysql" and service_name != "redis":
                    service_definition["ports"] = [f"{service_config.port}:{service_config.port}"]

                # Add health check
                if service_config.health_check:
                    service_definition["healthcheck"] = service_config.health_check

                compose_config["services"][service_name] = service_definition

            # Add volumes
            compose_config["volumes"] = {
                "mysql_data": {},
                "redis_data": {},
                "n8n_data": {}
            }

            # Write docker-compose file
            self.docker_dir.mkdir(parents=True, exist_ok=True)
            with open(self.compose_file, 'w') as f:
                yaml.dump(compose_config, f, default_flow_style=False)

            self.logger.info(f"Docker Compose configuration generated: {self.compose_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate docker-compose: {e}")
            return False

    def deploy_services_docker_compose(self) -> bool:
        """Deploy services using Docker Compose"""
        try:
            self.logger.info("Deploying services with Docker Compose...")

            # Change to docker directory
            original_cwd = os.getcwd()
            os.chdir(self.docker_dir)

            # Pull latest images
            self.logger.info("Pulling Docker images...")
            subprocess.run(["docker-compose", "pull"], check=True)

            # Stop existing services
            subprocess.run(["docker-compose", "down"], check=False)

            # Start services in dependency order
            for service_name in self.deployment_order:
                if service_name in self.services:
                    self.logger.info(f"Starting service: {service_name}")
                    subprocess.run([
                        "docker-compose", "up", "-d", service_name
                    ], check=True)

                    # Wait for service to be healthy
                    if not self.wait_for_service_health(service_name):
                        self.logger.error(f"Service {service_name} failed to become healthy")
                        return False

                    time.sleep(5)  # Brief pause between services

            # Change back to original directory
            os.chdir(original_cwd)

            self.logger.info("All services deployed successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Docker Compose deployment failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Deployment error: {e}")
            return False

    def wait_for_service_health(self, service_name: str, timeout: int = 300) -> bool:
        """Wait for service to become healthy"""
        try:
            self.logger.info(f"Waiting for {service_name} to become healthy...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    container = self.docker_client.containers.get(f"dmlogn8n-{service_name}")
                    health = container.attrs.get("State", {}).get("Health", {})

                    if health.get("Status") == "healthy":
                        self.logger.info(f"{service_name} is healthy")
                        return True

                except docker.errors.NotFound:
                    pass

                time.sleep(5)

            self.logger.error(f"{service_name} did not become healthy within {timeout} seconds")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for {service_name} health: {e}")
            return False

    def deploy_services_kubernetes(self) -> bool:
        """Deploy services using Kubernetes"""
        try:
            self.logger.info("Deploying services with Kubernetes...")

            # Apply Kubernetes manifests in dependency order
            manifests = [
                "namespace.yaml",
                "configmaps.yaml",
                "secrets.yaml",
                "persistent-volumes.yaml",
                "mysql-deployment.yaml",
                "redis-deployment.yaml",
                "n8n-deployment.yaml",
                "services.yaml",
                "ingress.yaml"
            ]

            for manifest in manifests:
                manifest_path = self.k8s_dir / manifest
                if manifest_path.exists():
                    self.logger.info(f"Applying {manifest}...")
                    subprocess.run([
                        "kubectl", "apply", "-f", str(manifest_path)
                    ], check=True)

            # Wait for deployments to be ready
            self.logger.info("Waiting for deployments to be ready...")
            subprocess.run([
                "kubectl", "wait", "--for=condition=available", "deployment", "--all",
                "--namespace=dmlogn8n", "--timeout=600s"
            ], check=True)

            self.logger.info("Kubernetes deployment completed")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Kubernetes deployment failed: {e}")
            return False

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """Get status of a specific service"""
        try:
            container = self.docker_client.containers.get(f"dmlogn8n-{service_name}")
            container.reload()

            status = container.status

            if status == "running":
                health = container.attrs.get("State", {}).get("Health", {})
                if health.get("Status") == "healthy":
                    return ServiceStatus.RUNNING
                else:
                    return ServiceStatus.STARTING
            elif status == "exited":
                return ServiceStatus.FAILED
            else:
                return ServiceStatus.STOPPED

        except docker.errors.NotFound:
            return ServiceStatus.STOPPED
        except Exception:
            return ServiceStatus.UNKNOWN

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        try:
            container = self.docker_client.containers.get(f"dmlogn8n-{service_name}")
            container.stop()
            self.logger.info(f"Service {service_name} stopped")
            return True
        except docker.errors.NotFound:
            self.logger.warning(f"Service {service_name} not found")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop {service_name}: {e}")
            return False

    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        try:
            container = self.docker_client.containers.get(f"dmlogn8n-{service_name}")
            container.start()
            self.logger.info(f"Service {service_name} started")
            return True
        except docker.errors.NotFound:
            self.logger.error(f"Service {service_name} not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            container = self.docker_client.containers.get(f"dmlogn8n-{service_name}")
            container.restart()
            self.logger.info(f"Service {service_name} restarted")
            return True
        except docker.errors.NotFound:
            self.logger.error(f"Service {service_name} not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to restart {service_name}: {e}")
            return False

    def get_all_services_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services"""
        status = {}
        for service_name in self.services.keys():
            status[service_name] = self.get_service_status(service_name)
        return status

    def deploy_services(self) -> bool:
        """Deploy all services"""
        self.logger.info(f"Starting service deployment for {self.environment} environment...")

        # Initialize Docker client
        if not self.initialize_docker_client():
            return False

        # Generate docker-compose configuration
        if not self.generate_docker_compose():
            return False

        # Choose deployment method based on environment
        if self.environment == "production" and self.kubernetes_available():
            return self.deploy_services_kubernetes()
        else:
            return self.deploy_services_docker_compose()

    def kubernetes_available(self) -> bool:
        """Check if Kubernetes is available"""
        try:
            subprocess.run(["kubectl", "cluster-info"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def main():
    """Main entry point for service deployment"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Service Deployer")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--action", choices=["deploy", "status", "start", "stop", "restart"],
                       default="deploy", help="Action to perform")
    parser.add_argument("--service", help="Specific service to target")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize service deployer
    deployer = ServiceDeployer(args.environment)

    if args.action == "deploy":
        success = deployer.deploy_services()
    elif args.action == "status":
        status = deployer.get_all_services_status()
        for service, state in status.items():
            print(f"{service}: {state.value}")
        success = True
    elif args.action == "start" and args.service:
        success = deployer.start_service(args.service)
    elif args.action == "stop" and args.service:
        success = deployer.stop_service(args.service)
    elif args.action == "restart" and args.service:
        success = deployer.restart_service(args.service)
    else:
        print("Invalid action or missing service parameter")
        success = False

    if success:
        print("✅ Service operation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Service operation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()