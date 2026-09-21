#!/usr/bin/env python3
"""
Environment Setup for DMLogn8n
Automated environment configuration and dependency management
"""

import os
import sys
import json
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PackageType(Enum):
    APT = "apt"
    YUM = "yum"
    PIP = "pip"
    NPM = "npm"
    DOCKER = "docker"
    COMPOSE = "docker-compose"


@dataclass
class PackageRequirement:
    name: str
    package_type: PackageType
    version: Optional[str] = None
    required: bool = True


class EnvironmentSetup:
    """Automated environment setup and dependency management"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # System information
        self.os_info = self.get_os_info()
        self.python_version = sys.version_info

        # Paths
        self.install_dir = Path("/opt/dmlogn8n")
        self.config_dir = Path("/etc/dmlogn8n")
        self.data_dir = Path("/var/lib/dmlogn8n")
        self.log_dir = Path("/var/log/dmlogn8n")

        # Package requirements
        self.packages = self.get_package_requirements()

    def get_os_info(self) -> Dict[str, str]:
        """Get operating system information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "distro": platform.platform(),
            "architecture": platform.architecture()[0]
        }

    def get_package_requirements(self) -> List[PackageRequirement]:
        """Get package requirements based on environment"""
        base_packages = [
            PackageRequirement("curl", PackageType.APT),
            PackageRequirement("wget", PackageType.APT),
            PackageRequirement("git", PackageType.APT),
            PackageRequirement("nginx", PackageType.APT),
            PackageRequirement("redis-server", PackageType.APT),
            PackageRequirement("mysql-server", PackageType.APT),
            PackageRequirement("python3", PackageType.APT),
            PackageRequirement("python3-pip", PackageType.APT),
            PackageRequirement("python3-venv", PackageType.APT),
            PackageRequirement("docker.io", PackageType.DOCKER),
            PackageRequirement("docker-compose", PackageType.COMPOSE),
        ]

        python_packages = [
            PackageRequirement("flask", PackageType.PIP, "2.3.3"),
            PackageRequirement("sqlalchemy", PackageType.PIP, "2.0.21"),
            PackageRequirement("redis", PackageType.PIP, "4.6.0"),
            PackageRequirement("pymysql", PackageType.PIP, "1.1.0"),
            PackageRequirement("celery", PackageType.PIP, "5.3.1"),
            PackageRequirement("gunicorn", PackageType.PIP, "21.2.0"),
            PackageRequirement("prometheus-client", PackageType.PIP, "0.17.1"),
            PackageRequirement("structlog", PackageType.PIP, "23.1.0"),
            PackageRequirement("click", PackageType.PIP, "8.1.7"),
            PackageRequirement("pyyaml", PackageType.PIP, "6.0.1"),
            PackageRequirement("requests", PackageType.PIP, "2.31.0"),
            PackageRequirement("websockets", PackageType.PIP, "11.0.3"),
            PackageRequirement("aiofiles", PackageType.PIP, "23.2.1"),
            PackageRequirement("jinja2", PackageType.PIP, "3.1.2"),
            PackageRequirement("python-dotenv", PackageType.PIP, "1.0.0"),
        ]

        node_packages = [
            PackageRequirement("node", PackageType.NPM),
            PackageRequirement("npm", PackageType.NPM),
        ]

        all_packages = base_packages + python_packages + node_packages

        # Environment-specific packages
        if self.environment == "production":
            all_packages.extend([
                PackageRequirement("certbot", PackageType.APT),
                PackageRequirement("certbot-nginx", PackageType.APT),
                PackageRequirement("fail2ban", PackageType.APT),
                PackageRequirement("ufw", PackageType.APT),
            ])

        return all_packages

    def check_root_privileges(self) -> bool:
        """Check if running with root privileges"""
        return os.geteuid() == 0

    def update_package_cache(self) -> bool:
        """Update package cache"""
        try:
            self.logger.info("Updating package cache...")
            subprocess.run(["apt", "update"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to update package cache: {e}")
            return False

    def install_package(self, package: PackageRequirement) -> bool:
        """Install a single package"""
        try:
            if package.package_type == PackageType.APT:
                cmd = ["apt", "install", "-y", package.name]
                if package.version:
                    cmd[-1] = f"{package.name}={package.version}"

            elif package.package_type == PackageType.PIP:
                cmd = ["pip3", "install", package.name]
                if package.version:
                    cmd[-1] = f"{package.name}=={package.version}"

            elif package.package_type == PackageType.DOCKER:
                return self.setup_docker()

            elif package.package_type == PackageType.COMPOSE:
                return self.setup_docker_compose()

            else:
                self.logger.warning(f"Unsupported package type: {package.package_type}")
                return True

            self.logger.info(f"Installing {package.name}...")
            subprocess.run(cmd, check=True)
            return True

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install {package.name}: {e}"
            if package.required:
                self.logger.error(error_msg)
                return False
            else:
                self.logger.warning(error_msg)
                return True

    def setup_docker(self) -> bool:
        """Setup Docker installation"""
        try:
            self.logger.info("Setting up Docker...")

            # Add Docker's official GPG key
            subprocess.run([
                "curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg"
            ], check=True, stdout=open("/tmp/docker.gpg", "w"))

            subprocess.run([
                "gpg", "--dearmor", "-o", "/etc/apt/keyrings/docker.gpg", "/tmp/docker.gpg"
            ], check=True)

            # Add Docker repository
            subprocess.run([
                "echo", "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
            ], check=True, stdout=open("/etc/apt/sources.list.d/docker.list", "w"))

            # Update and install Docker
            subprocess.run(["apt", "update"], check=True)
            subprocess.run([
                "apt", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"
            ], check=True)

            # Add user to docker group
            subprocess.run(["usermod", "-aG", "docker", "ubuntu"], check=True)

            # Start and enable Docker
            subprocess.run(["systemctl", "start", "docker"], check=True)
            subprocess.run(["systemctl", "enable", "docker"], check=True)

            return True

        except Exception as e:
            self.logger.error(f"Docker setup failed: {e}")
            return False

    def setup_docker_compose(self) -> bool:
        """Setup Docker Compose"""
        try:
            self.logger.info("Setting up Docker Compose...")

            # Install docker-compose as plugin (comes with Docker installation)
            return True

        except Exception as e:
            self.logger.error(f"Docker Compose setup failed: {e}")
            return False

    def create_directories(self) -> bool:
        """Create necessary directories"""
        try:
            directories = [
                self.install_dir,
                self.config_dir,
                self.data_dir,
                self.log_dir,
                self.config_dir / "ssl",
                self.config_dir / "nginx",
                self.config_dir / "supervisor",
                self.data_dir / "mysql",
                self.data_dir / "redis",
                self.data_dir / "uploads",
                self.log_dir / "nginx",
                self.log_dir / "mysql",
                self.log_dir / "redis",
                self.log_dir / "app",
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                # Set proper permissions
                os.chmod(directory, 0o755)

            self.logger.info("Created all necessary directories")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            return False

    def setup_python_environment(self) -> bool:
        """Setup Python virtual environment"""
        try:
            self.logger.info("Setting up Python virtual environment...")

            venv_path = self.install_dir / "venv"

            # Create virtual environment
            subprocess.run([
                "python3", "-m", "venv", str(venv_path)
            ], check=True)

            # Activate and install requirements
            pip_path = venv_path / "bin" / "pip"

            # Upgrade pip
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)

            # Install Python packages
            python_packages = [p for p in self.packages if p.package_type == PackageType.PIP]
            for package in python_packages:
                package_name = package.name
                if package.version:
                    package_name = f"{package.name}=={package.version}"

                subprocess.run([str(pip_path), "install", package_name], check=True)

            self.logger.info("Python environment setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Python environment setup failed: {e}")
            return False

    def configure_firewall(self) -> bool:
        """Configure firewall settings"""
        if self.environment != "production":
            return True

        try:
            self.logger.info("Configuring firewall...")

            # Configure UFW
            subprocess.run(["ufw", "--force", "reset"], check=True)
            subprocess.run(["ufw", "default", "deny", "incoming"], check=True)
            subprocess.run(["ufw", "default", "allow", "outgoing"], check=True)

            # Allow SSH
            subprocess.run(["ufw", "allow", "22"], check=True)

            # Allow HTTP/HTTPS
            subprocess.run(["ufw", "allow", "80"], check=True)
            subprocess.run(["ufw", "allow", "443"], check=True)

            # Allow application ports
            subprocess.run(["ufw", "allow", "3000"], check=True)  # N8N
            subprocess.run(["ufw", "allow", "5678"], check=True)  # N8N alternative
            subprocess.run(["ufw", "allow", "8000"], check=True)  # API

            # Enable firewall
            subprocess.run(["ufw", "--force", "enable"], check=True)

            self.logger.info("Firewall configured successfully")
            return True

        except Exception as e:
            self.logger.error(f"Firewall configuration failed: {e}")
            return False

    def setup_services(self) -> bool:
        """Setup and configure system services"""
        try:
            self.logger.info("Setting up system services...")

            # Configure MySQL
            subprocess.run(["systemctl", "start", "mysql"], check=True)
            subprocess.run(["systemctl", "enable", "mysql"], check=True)

            # Configure Redis
            subprocess.run(["systemctl", "start", "redis-server"], check=True)
            subprocess.run(["systemctl", "enable", "redis-server"], check=True)

            # Configure Nginx
            subprocess.run(["systemctl", "start", "nginx"], check=True)
            subprocess.run(["systemctl", "enable", "nginx"], check=True)

            self.logger.info("System services configured")
            return True

        except Exception as e:
            self.logger.error(f"Service setup failed: {e}")
            return False

    def validate_environment(self) -> bool:
        """Validate that environment is properly setup"""
        try:
            self.logger.info("Validating environment setup...")

            # Check critical services
            services = ["mysql", "redis-server", "nginx", "docker"]
            for service in services:
                result = subprocess.run(["systemctl", "is-active", service],
                                      capture_output=True, text=True)
                if result.stdout.strip() != "active":
                    self.logger.error(f"Service {service} is not active")
                    return False

            # Check Python packages
            venv_python = self.install_dir / "venv" / "bin" / "python3"
            if venv_python.exists():
                result = subprocess.run([
                    str(venv_python), "-c", "import flask, sqlalchemy, redis, pymysql"
                ], capture_output=True)
                if result.returncode != 0:
                    self.logger.error("Python packages validation failed")
                    return False

            # Check directories
            required_dirs = [self.install_dir, self.config_dir, self.data_dir, self.log_dir]
            for directory in required_dirs:
                if not directory.exists():
                    self.logger.error(f"Required directory missing: {directory}")
                    return False

            self.logger.info("Environment validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            return False

    def setup_environment(self) -> bool:
        """Execute complete environment setup"""
        self.logger.info(f"Setting up {self.environment} environment...")

        if not self.check_root_privileges():
            self.logger.error("Root privileges required for environment setup")
            return False

        # Update package cache
        if not self.update_package_cache():
            return False

        # Create directories
        if not self.create_directories():
            return False

        # Install packages
        failed_packages = []
        for package in self.packages:
            if not self.install_package(package):
                if package.required:
                    failed_packages.append(package.name)

        if failed_packages:
            self.logger.error(f"Failed to install required packages: {failed_packages}")
            return False

        # Setup Python environment
        if not self.setup_python_environment():
            return False

        # Setup services
        if not self.setup_services():
            return False

        # Configure firewall for production
        if self.environment == "production":
            if not self.configure_firewall():
                return False

        # Validate setup
        if not self.validate_environment():
            return False

        self.logger.info(f"{self.environment.capitalize()} environment setup completed successfully")
        return True


def main():
    """Main entry point for environment setup"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Environment Setup")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize and run environment setup
    env_setup = EnvironmentSetup(args.environment)
    success = env_setup.setup_environment()

    if success:
        print("✅ Environment setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Environment setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()