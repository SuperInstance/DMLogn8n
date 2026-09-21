#!/usr/bin/env python3
"""
DMLogn8n Deployment Manager
Master deployment coordinator for automated platform deployment
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Add deployment modules to path
sys.path.append(str(Path(__file__).parent))

from environment_setup import EnvironmentSetup
from service_deployer import ServiceDeployer
from database_initializer import DatabaseInitializer
from config_generator import ConfigGenerator
from health_check_deploy import HealthChecker
from rollback_manager import RollbackManager
from monitoring_deploy import MonitoringDeploy


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentConfig:
    environment: Environment
    version: str
    backup_enabled: bool = True
    monitoring_enabled: bool = True
    health_check_enabled: bool = True
    rollback_enabled: bool = True
    parallel_deploy: bool = False
    timeout_minutes: int = 30


class DeploymentManager:
    """Master deployment coordinator for DMLogn8n platform"""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.deployment_id = f"deploy_{int(time.time())}"
        self.log_dir = Path("/var/log/dmlogn8n/deployments")
        self.backup_dir = Path("/var/backups/dmlogn8n")
        self.status = DeploymentStatus.PENDING
        self.start_time = None

        # Initialize logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)

        # Initialize deployment components
        self.env_setup = EnvironmentSetup(config.environment)
        self.service_deployer = ServiceDeployer(config.environment)
        self.db_initializer = DatabaseInitializer(config.environment)
        self.config_generator = ConfigGenerator(config.environment)
        self.health_checker = HealthChecker(config.environment)
        self.rollback_manager = RollbackManager(config.environment)
        self.monitoring = MonitoringDeploy(config.environment)

        # Load environment configuration
        self.env_config = self.load_environment_config()

    def setup_logging(self):
        """Setup comprehensive logging for deployment"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        log_file = self.log_dir / f"{self.deployment_id}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        config_file = Path(__file__).parent / "configs" / f"{self.config.environment.value}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Environment config not found: {config_file}")

        with open(config_file, 'r') as f:
            return json.load(f)

    def create_backup(self) -> bool:
        """Create backup before deployment"""
        if not self.config.backup_enabled:
            return True

        self.logger.info("Creating deployment backup...")

        try:
            backup_path = self.backup_dir / f"{self.deployment_id}"
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup current configurations
            configs_backup = backup_path / "configs"
            subprocess.run([
                "cp", "-r", "/etc/dmlogn8n", str(configs_backup)
            ], check=True)

            # Backup databases
            db_backup = backup_path / "databases"
            db_backup.mkdir(exist_ok=True)

            # Create database dumps
            for db_name in self.env_config.get('databases', []):
                dump_file = db_backup / f"{db_name}.sql"
                subprocess.run([
                    "mysqldump", "--single-transaction",
                    f"{db_name}"
                ], stdout=open(dump_file, 'w'), check=True)

            self.logger.info(f"Backup created at: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False

    def deploy(self) -> bool:
        """Execute complete deployment process"""
        self.start_time = datetime.now()
        self.status = DeploymentStatus.IN_PROGRESS

        self.logger.info(f"Starting deployment {self.deployment_id} for {self.config.environment.value}")

        try:
            # Step 1: Create backup
            if not self.create_backup():
                raise Exception("Backup creation failed")

            # Step 2: Environment setup
            if not self.env_setup.setup_environment():
                raise Exception("Environment setup failed")

            # Step 3: Generate configurations
            if not self.config_generator.generate_configs():
                raise Exception("Configuration generation failed")

            # Step 4: Initialize databases
            if not self.db_initializer.initialize_databases():
                raise Exception("Database initialization failed")

            # Step 5: Deploy services
            if not self.service_deployer.deploy_services():
                raise Exception("Service deployment failed")

            # Step 6: Health checks
            if self.config.health_check_enabled:
                if not self.health_checker.run_health_checks():
                    raise Exception("Health checks failed")

            # Step 7: Setup monitoring
            if self.config.monitoring_enabled:
                if not self.monitoring.setup_monitoring():
                    raise Exception("Monitoring setup failed")

            self.status = DeploymentStatus.SUCCESS
            self.logger.info(f"Deployment {self.deployment_id} completed successfully!")
            return True

        except Exception as e:
            self.status = DeploymentStatus.FAILED
            self.logger.error(f"Deployment failed: {e}")

            # Attempt rollback if enabled
            if self.config.rollback_enabled:
                self.rollback()

            return False

    def rollback(self) -> bool:
        """Rollback deployment to previous state"""
        self.status = DeploymentStatus.ROLLING_BACK
        self.logger.info("Starting deployment rollback...")

        try:
            if self.rollback_manager.execute_rollback(self.deployment_id):
                self.status = DeploymentStatus.ROLLED_BACK
                self.logger.info("Rollback completed successfully")
                return True
            else:
                self.logger.error("Rollback failed")
                return False

        except Exception as e:
            self.logger.error(f"Rollback error: {e}")
            return False

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "deployment_id": self.deployment_id,
            "status": self.status.value,
            "environment": self.config.environment.value,
            "version": self.config.version,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0
        }

    def cleanup(self):
        """Cleanup deployment artifacts"""
        self.logger.info("Cleaning up deployment artifacts...")

        # Remove temporary files
        temp_dir = Path("/tmp/dmlogn8n_deploy")
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)


def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description="DMLogn8n Deployment Manager")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target deployment environment")
    parser.add_argument("--version", default="latest",
                       help="Version to deploy")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip backup creation")
    parser.add_argument("--no-monitoring", action="store_true",
                       help="Skip monitoring setup")
    parser.add_argument("--no-health-check", action="store_true",
                       help="Skip health checks")
    parser.add_argument("--no-rollback", action="store_true",
                       help="Disable rollback capability")
    parser.add_argument("--parallel", action="store_true",
                       help="Enable parallel deployment")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Deployment timeout in minutes")
    parser.add_argument("--rollback", action="store_true",
                       help="Rollback last deployment")

    args = parser.parse_args()

    # Create deployment configuration
    config = DeploymentConfig(
        environment=Environment(args.environment),
        version=args.version,
        backup_enabled=not args.no_backup,
        monitoring_enabled=not args.no_monitoring,
        health_check_enabled=not args.no_health_check,
        rollback_enabled=not args.no_rollback,
        parallel_deploy=args.parallel,
        timeout_minutes=args.timeout
    )

    # Initialize deployment manager
    deployer = DeploymentManager(config)

    try:
        if args.rollback:
            # Rollback last deployment
            success = deployer.rollback()
        else:
            # Execute deployment
            success = deployer.deploy()

        # Print final status
        status = deployer.get_deployment_status()
        print(f"\nDeployment Status: {status['status'].upper()}")
        print(f"Duration: {status['duration_minutes']:.2f} minutes")

        if success:
            print("✅ Deployment completed successfully!")
            sys.exit(0)
        else:
            print("❌ Deployment failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted by user")
        deployer.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        deployer.rollback()
        sys.exit(1)
    finally:
        deployer.cleanup()


if __name__ == "__main__":
    main()