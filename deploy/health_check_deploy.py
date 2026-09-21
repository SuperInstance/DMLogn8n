#!/usr/bin/env python3
"""
Health Check Deploy for DMLogn8n
Verifies deployment health and service functionality
"""

import os
import sys
import json
import time
import logging
import requests
import socket
import subprocess
import pymysql
import redis
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import docker


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"


class CheckType(Enum):
    HTTP = "http"
    TCP = "tcp"
    DATABASE = "database"
    DOCKER = "docker"
    DISK_SPACE = "disk_space"
    MEMORY = "memory"
    CPU = "cpu"


@dataclass
class HealthCheck:
    name: str
    check_type: CheckType
    target: str
    timeout: int = 30
    expected_status: int = 200
    critical: bool = True
    description: str = ""


@dataclass
class HealthResult:
    name: str
    status: HealthStatus
    message: str
    response_time: float
    details: Dict[str, Any] = None


class HealthChecker:
    """Deployment health verification system"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self.load_configuration()

        # Initialize Docker client
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker client not available: {e}")

        # Define health checks
        self.health_checks = self.get_health_checks()

    def load_configuration(self) -> Dict[str, Any]:
        """Load environment configuration"""
        config_file = Path(__file__).parent / "configs" / f"{self.environment}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def get_health_checks(self) -> List[HealthCheck]:
        """Get health checks for the environment"""
        checks = []

        # Web application health checks
        checks.extend([
            HealthCheck(
                name="player_portal_http",
                check_type=CheckType.HTTP,
                target=f"http://{self.config['web']['host']}:{self.config['web']['port']}/",
                description="Player Portal Web Application"
            ),
            HealthCheck(
                name="api_http",
                check_type=CheckType.HTTP,
                target=f"http://{self.config['api']['host']}:{self.config['api']['port']}/health",
                description="API Health Endpoint"
            ),
            HealthCheck(
                name="character_coder_http",
                check_type=CheckType.HTTP,
                target=f"http://localhost:3001/health",
                description="Character Coder Service"
            ),
            HealthCheck(
                name="n8n_http",
                check_type=CheckType.HTTP,
                target=f"http://{self.config['n8n']['host']}:{self.config['n8n']['port']}/",
                description="N8N Workflow Automation"
            ),
        ])

        # Database health checks
        checks.extend([
            HealthCheck(
                name="mysql_connection",
                check_type=CheckType.DATABASE,
                target="mysql",
                description="MySQL Database Connection"
            ),
            HealthCheck(
                name="redis_connection",
                check_type=CheckType.DATABASE,
                target="redis",
                description="Redis Cache Connection"
            ),
        ])

        # TCP port checks
        if self.environment != "development":
            checks.extend([
                HealthCheck(
                    name="nginx_tcp",
                    check_type=CheckType.TCP,
                    target=f"{self.config['web']['host']}:80",
                    description="Nginx HTTP Port"
                ),
            ])

            if self.config.get('web', {}).get('ssl_enabled', False):
                checks.append(
                    HealthCheck(
                        name="nginx_ssl_tcp",
                        check_type=CheckType.TCP,
                        target=f"{self.config['web']['host']}:443",
                        description="Nginx HTTPS Port"
                    )
                )

        # Docker container health checks
        if self.docker_client:
            checks.extend([
                HealthCheck(
                    name="mysql_container",
                    check_type=CheckType.DOCKER,
                    target="dmlogn8n-mysql",
                    description="MySQL Container Health"
                ),
                HealthCheck(
                    name="redis_container",
                    check_type=CheckType.DOCKER,
                    target="dmlogn8n-redis",
                    description="Redis Container Health"
                ),
                HealthCheck(
                    name="n8n_container",
                    check_type=CheckType.DOCKER,
                    target="dmlogn8n-n8n",
                    description="N8N Container Health"
                ),
                HealthCheck(
                    name="api_container",
                    check_type=CheckType.DOCKER,
                    target="dmlogn8n-dmlogn8n-api",
                    description="API Container Health"
                ),
            ])

        # System resource checks
        checks.extend([
            HealthCheck(
                name="disk_space",
                check_type=CheckType.DISK_SPACE,
                target="/",
                description="Disk Space Usage"
            ),
            HealthCheck(
                name="memory_usage",
                check_type=CheckType.MEMORY,
                target="system",
                description="System Memory Usage"
            ),
            HealthCheck(
                name="cpu_usage",
                check_type=CheckType.CPU,
                target="system",
                description="System CPU Usage"
            ),
        ])

        return checks

    def check_http_health(self, check: HealthCheck) -> HealthResult:
        """Check HTTP endpoint health"""
        try:
            start_time = time.time()

            response = requests.get(
                check.target,
                timeout=check.timeout,
                verify=False  # Ignore SSL certs for health checks
            )

            response_time = time.time() - start_time

            if response.status_code == check.expected_status:
                status = HealthStatus.HEALTHY
                message = f"HTTP {response.status_code} - OK"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"HTTP {response.status_code} - Expected {check.expected_status}"

            details = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "url": check.target
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except requests.exceptions.Timeout:
            return HealthResult(
                name=check.name,
                status=HealthStatus.TIMEOUT,
                message=f"Request timeout after {check.timeout}s",
                response_time=check.timeout
            )

        except requests.exceptions.ConnectionError:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message="Connection refused",
                response_time=0
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def check_tcp_health(self, check: HealthCheck) -> HealthResult:
        """Check TCP port connectivity"""
        try:
            start_time = time.time()

            host, port = check.target.split(':')
            port = int(port)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(check.timeout)

            result = sock.connect_ex((host, port))
            response_time = time.time() - start_time

            sock.close()

            if result == 0:
                status = HealthStatus.HEALTHY
                message = f"Port {port} is open"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Port {port} is closed"

            details = {
                "host": host,
                "port": port,
                "response_time": response_time
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def check_database_health(self, check: HealthCheck) -> HealthResult:
        """Check database connectivity"""
        try:
            start_time = time.time()

            if check.target == "mysql":
                # Check MySQL connection
                connection = pymysql.connect(
                    host=self.config['database']['host'],
                    port=self.config['database']['port'],
                    user=self.config['database']['username'],
                    password=self.config['database']['password'],
                    database=self.config['database']['database'],
                    connect_timeout=check.timeout
                )

                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                connection.close()

                message = "MySQL connection successful"
                response_time = time.time() - start_time
                status = HealthStatus.HEALTHY

                details = {
                    "host": self.config['database']['host'],
                    "port": self.config['database']['port'],
                    "database": self.config['database']['database']
                }

            elif check.target == "redis":
                # Check Redis connection
                r = redis.Redis(
                    host=self.config['redis']['host'],
                    port=self.config['redis']['port'],
                    password=self.config['redis']['password'],
                    socket_timeout=check.timeout,
                    decode_responses=True
                )

                r.ping()
                info = r.info()

                message = "Redis connection successful"
                response_time = time.time() - start_time
                status = HealthStatus.HEALTHY

                details = {
                    "host": self.config['redis']['host'],
                    "port": self.config['redis']['port'],
                    "redis_version": info.get('redis_version'),
                    "connected_clients": info.get('connected_clients')
                }

            else:
                raise ValueError(f"Unknown database target: {check.target}")

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time=0
            )

    def check_docker_health(self, check: HealthCheck) -> HealthResult:
        """Check Docker container health"""
        try:
            if not self.docker_client:
                return HealthResult(
                    name=check.name,
                    status=HealthStatus.UNKNOWN,
                    message="Docker client not available",
                    response_time=0
                )

            start_time = time.time()

            container = self.docker_client.containers.get(check.target)
            container.reload()

            response_time = time.time() - start_time

            status_info = container.attrs.get("State", {})
            health_info = status_info.get("Health", {})

            container_status = status_info.get("Status", "unknown")
            health_status = health_info.get("Status", "unknown")

            if container_status == "running" and health_status == "healthy":
                status = HealthStatus.HEALTHY
                message = f"Container is running and healthy"
            elif container_status == "running":
                status = HealthStatus.WARNING
                message = f"Container is running but health check: {health_status}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Container status: {container_status}"

            details = {
                "container_status": container_status,
                "health_status": health_status,
                "image": container.attrs.get("Config", {}).get("Image"),
                "created": container.attrs.get("Created"),
                "ports": container.attrs.get("NetworkSettings", {}).get("Ports")
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except docker.errors.NotFound:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message="Container not found",
                response_time=0
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def check_disk_space(self, check: HealthCheck) -> HealthResult:
        """Check disk space usage"""
        try:
            start_time = time.time()

            # Get disk usage
            stat = os.statvfs(check.target)
            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bavail
            used = total - free
            usage_percent = (used / total) * 100

            response_time = time.time() - start_time

            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Disk usage: {usage_percent:.1f}%"
            elif usage_percent < 90:
                status = HealthStatus.WARNING
                message = f"Disk usage: {usage_percent:.1f}% (high)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage: {usage_percent:.1f}% (critical)"

            details = {
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
                "usage_percent": usage_percent,
                "mount_point": check.target
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def check_memory_usage(self, check: HealthCheck) -> HealthResult:
        """Check system memory usage"""
        try:
            start_time = time.time()

            # Read memory info from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()

            mem_total = 0
            mem_available = 0

            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_total = int(line.split()[1])
                elif 'MemAvailable:' in line:
                    mem_available = int(line.split()[1])

            mem_used = mem_total - mem_available
            usage_percent = (mem_used / mem_total) * 100

            response_time = time.time() - start_time

            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {usage_percent:.1f}%"
            elif usage_percent < 90:
                status = HealthStatus.WARNING
                message = f"Memory usage: {usage_percent:.1f}% (high)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage: {usage_percent:.1f}% (critical)"

            details = {
                "total_mb": mem_total // 1024,
                "used_mb": mem_used // 1024,
                "available_mb": mem_available // 1024,
                "usage_percent": usage_percent
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def check_cpu_usage(self, check: HealthCheck) -> HealthResult:
        """Check system CPU usage"""
        try:
            start_time = time.time()

            # Get CPU usage from /proc/stat
            with open('/proc/stat', 'r') as f:
                cpu_line = f.readline()

            cpu_times = list(map(int, cpu_line.split()[1:]))
            idle_time = cpu_times[3]
            total_time = sum(cpu_times)
            usage_percent = ((total_time - idle_time) / total_time) * 100

            response_time = time.time() - start_time

            if usage_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"CPU usage: {usage_percent:.1f}%"
            elif usage_percent < 85:
                status = HealthStatus.WARNING
                message = f"CPU usage: {usage_percent:.1f}% (high)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"CPU usage: {usage_percent:.1f}% (critical)"

            details = {
                "usage_percent": usage_percent,
                "cpu_count": os.cpu_count()
            }

            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                response_time=response_time,
                details=details
            )

        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                response_time=0
            )

    def execute_health_check(self, check: HealthCheck) -> HealthResult:
        """Execute a single health check"""
        self.logger.debug(f"Running health check: {check.name}")

        if check.check_type == CheckType.HTTP:
            return self.check_http_health(check)
        elif check.check_type == CheckType.TCP:
            return self.check_tcp_health(check)
        elif check.check_type == CheckType.DATABASE:
            return self.check_database_health(check)
        elif check.check_type == CheckType.DOCKER:
            return self.check_docker_health(check)
        elif check.check_type == CheckType.DISK_SPACE:
            return self.check_disk_space(check)
        elif check.check_type == CheckType.MEMORY:
            return self.check_memory_usage(check)
        elif check.check_type == CheckType.CPU:
            return self.check_cpu_usage(check)
        else:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown check type: {check.check_type}",
                response_time=0
            )

    def run_health_checks(self) -> bool:
        """Run all health checks"""
        self.logger.info(f"Running health checks for {self.environment} environment...")

        results = []
        critical_failures = []

        # Execute all health checks
        for check in self.health_checks:
            result = self.execute_health_check(check)
            results.append(result)

            # Log result
            if result.status == HealthStatus.HEALTHY:
                self.logger.info(f"✅ {check.name}: {result.message}")
            elif result.status == HealthStatus.WARNING:
                self.logger.warning(f"⚠️  {check.name}: {result.message}")
            else:
                self.logger.error(f"❌ {check.name}: {result.message}")
                if check.critical:
                    critical_failures.append(check.name)

        # Generate health report
        self.generate_health_report(results)

        # Check if any critical services failed
        if critical_failures:
            self.logger.error(f"Critical services failed: {', '.join(critical_failures)}")
            return False

        # Check overall health
        unhealthy_count = sum(1 for r in results if r.status in [HealthStatus.UNHEALTHY, HealthStatus.TIMEOUT])
        warning_count = sum(1 for r in results if r.status == HealthStatus.WARNING)

        if unhealthy_count == 0:
            self.logger.info("🎉 All health checks passed!")
            if warning_count > 0:
                self.logger.warning(f"⚠️  {warning_count} warnings detected")
            return True
        else:
            self.logger.error(f"❌ {unhealthy_count} health checks failed")
            return False

    def generate_health_report(self, results: List[HealthResult]):
        """Generate health report"""
        report_dir = Path("/var/log/dmlogn8n/health")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"health_report_{int(time.time())}.json"

        report = {
            "timestamp": time.time(),
            "environment": self.environment,
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
                "warnings": sum(1 for r in results if r.status == HealthStatus.WARNING),
                "unhealthy": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for r in results if r.status == HealthStatus.UNKNOWN),
                "timeouts": sum(1 for r in results if r.status == HealthStatus.TIMEOUT)
            },
            "checks": []
        }

        for result in results:
            report["checks"].append({
                "name": result.name,
                "status": result.status.value,
                "message": result.message,
                "response_time": result.response_time,
                "details": result.details
            })

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Health report generated: {report_file}")


def main():
    """Main entry point for health checks"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Health Check")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--check", help="Run specific health check")
    parser.add_argument("--continuous", action="store_true",
                       help="Run health checks continuously")
    parser.add_argument("--interval", type=int, default=60,
                       help="Interval between checks in seconds")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize health checker
    checker = HealthChecker(args.environment)

    try:
        if args.continuous:
            # Run health checks continuously
            while True:
                success = checker.run_health_checks()
                time.sleep(args.interval)
        else:
            # Run health checks once
            if args.check:
                # Run specific check
                check = next((c for c in checker.health_checks if c.name == args.check), None)
                if check:
                    result = checker.execute_health_check(check)
                    print(f"{result.name}: {result.status.value} - {result.message}")
                    success = result.status == HealthStatus.HEALTHY
                else:
                    print(f"Health check not found: {args.check}")
                    success = False
            else:
                # Run all health checks
                success = checker.run_health_checks()

        if success:
            print("✅ Health checks completed successfully!")
            sys.exit(0)
        else:
            print("❌ Health checks failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Health checks interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()