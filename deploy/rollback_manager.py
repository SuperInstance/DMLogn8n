#!/usr/bin/env python3
"""
Rollback Manager for DMLogn8n
Automated rollback capabilities for failed deployments
"""

import os
import sys
import json
import time
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import docker


class RollbackStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class RollbackType(Enum):
    FULL = "full"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    SERVICES = "services"
    CONTAINERS = "containers"


@dataclass
class RollbackPoint:
    id: str
    timestamp: datetime
    deployment_id: str
    environment: str
    backup_path: str
    description: str
    config_files: List[str]
    database_backups: List[str]
    container_images: Dict[str, str]
    services_status: Dict[str, str]


@dataclass
class RollbackOperation:
    id: str
    timestamp: datetime
    rollback_point_id: str
    rollback_type: RollbackType
    status: RollbackStatus
    steps_completed: List[str]
    steps_failed: List[str]
    error_message: Optional[str] = None


class RollbackManager:
    """Automated rollback management system"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Paths
        self.backup_dir = Path("/var/backups/dmlogn8n")
        self.rollback_dir = self.backup_dir / "rollbacks"
        self.config_dir = Path("/etc/dmlogn8n")
        self.deploy_dir = Path(__file__).parent

        # Initialize Docker client
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker client not available: {e}")

        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

    def create_rollback_point(self, deployment_id: str, description: str = "") -> bool:
        """Create a rollback point before deployment"""
        try:
            self.logger.info(f"Creating rollback point for deployment {deployment_id}")

            rollback_id = f"rollback_{int(time.time())}"
            rollback_point_path = self.rollback_dir / rollback_id
            rollback_point_path.mkdir(parents=True, exist_ok=True)

            # Backup configurations
            config_backup_path = rollback_point_path / "configs"
            shutil.copytree(self.config_dir, config_backup_path, dirs_exist_ok=True)

            # Get list of config files
            config_files = []
            for root, dirs, files in os.walk(config_backup_path):
                for file in files:
                    config_files.append(str(Path(root) / file))

            # Backup databases
            database_backups = []
            db_backup_path = rollback_point_path / "databases"
            db_backup_path.mkdir(exist_ok=True)

            # MySQL backups
            databases = ["dmlogn8n", "n8n"]
            for db_name in databases:
                backup_file = db_backup_path / f"{db_name}.sql"
                try:
                    subprocess.run([
                        "mysqldump", "--single-transaction",
                        f"{db_name}"
                    ], stdout=open(backup_file, 'w'), check=True)
                    database_backups.append(str(backup_file))
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"Failed to backup database {db_name}: {e}")

            # Get container image information
            container_images = {}
            if self.docker_client:
                containers = [
                    "dmlogn8n-mysql",
                    "dmlogn8n-redis",
                    "dmlogn8n-n8n",
                    "dmlogn8n-dmlogn8n-api",
                    "dmlogn8n-character-coder",
                    "dmlogn8n-player-portal",
                    "dmlogn8n-nginx"
                ]

                for container_name in containers:
                    try:
                        container = self.docker_client.containers.get(container_name)
                        image = container.image
                        container_images[container_name] = {
                            "image_id": image.id,
                            "tags": image.tags,
                            "short_id": image.short_id
                        }
                    except docker.errors.NotFound:
                        self.logger.warning(f"Container {container_name} not found")
                    except Exception as e:
                        self.logger.warning(f"Failed to get container info for {container_name}: {e}")

            # Get services status
            services_status = {}
            if self.docker_client:
                for container_name in container_images.keys():
                    try:
                        container = self.docker_client.containers.get(container_name)
                        container.reload()
                        services_status[container_name] = container.status
                    except Exception as e:
                        self.logger.warning(f"Failed to get status for {container_name}: {e}")
                        services_status[container_name] = "unknown"

            # Create rollback point object
            rollback_point = RollbackPoint(
                id=rollback_id,
                timestamp=datetime.now(),
                deployment_id=deployment_id,
                environment=self.environment,
                backup_path=str(rollback_point_path),
                description=description,
                config_files=config_files,
                database_backups=database_backups,
                container_images=container_images,
                services_status=services_status
            )

            # Save rollback point metadata
            metadata_file = rollback_point_path / "rollback_point.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(rollback_point), f, indent=2, default=str)

            self.logger.info(f"Rollback point created: {rollback_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create rollback point: {e}")
            return False

    def get_latest_rollback_point(self) -> Optional[RollbackPoint]:
        """Get the latest rollback point for the environment"""
        try:
            rollback_points = []

            for rollback_dir in self.rollback_dir.iterdir():
                if rollback_dir.is_dir():
                    metadata_file = rollback_dir / "rollback_point.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            if data.get("environment") == self.environment:
                                # Convert timestamp back to datetime
                                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                                rollback_points.append(RollbackPoint(**data))

            if not rollback_points:
                return None

            # Return the most recent rollback point
            return max(rollback_points, key=lambda x: x.timestamp)

        except Exception as e:
            self.logger.error(f"Failed to get latest rollback point: {e}")
            return None

    def restore_configurations(self, rollback_point: RollbackPoint) -> bool:
        """Restore configurations from rollback point"""
        try:
            self.logger.info("Restoring configurations...")

            backup_config_path = Path(rollback_point.backup_path) / "configs"

            # Backup current configs before restoring
            current_config_backup = self.config_dir.parent / f"dmlogn8n_config_backup_{int(time.time())}"
            if self.config_dir.exists():
                shutil.move(str(self.config_dir), str(current_config_backup))

            # Restore configurations
            if backup_config_path.exists():
                shutil.copytree(backup_config_path, self.config_dir)
                self.logger.info("Configurations restored successfully")
            else:
                self.logger.warning("No configuration backup found in rollback point")

            return True

        except Exception as e:
            self.logger.error(f"Failed to restore configurations: {e}")
            return False

    def restore_databases(self, rollback_point: RollbackPoint) -> bool:
        """Restore databases from rollback point"""
        try:
            self.logger.info("Restoring databases...")

            backup_db_path = Path(rollback_point.backup_path) / "databases"

            if not backup_db_path.exists():
                self.logger.warning("No database backups found in rollback point")
                return True

            # Restore MySQL databases
            database_files = list(backup_db_path.glob("*.sql"))
            for db_file in database_files:
                db_name = db_file.stem
                self.logger.info(f"Restoring database: {db_name}")

                try:
                    subprocess.run([
                        "mysql", db_name
                    ], stdin=open(db_file, 'r'), check=True)
                    self.logger.info(f"Database {db_name} restored successfully")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to restore database {db_name}: {e}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to restore databases: {e}")
            return False

    def restore_containers(self, rollback_point: RollbackPoint) -> bool:
        """Restore containers to their previous state"""
        try:
            self.logger.info("Restoring containers...")

            if not self.docker_client:
                self.logger.warning("Docker client not available, skipping container restoration")
                return True

            # Stop and remove current containers
            current_containers = [
                "dmlogn8n-mysql",
                "dmlogn8n-redis",
                "dmlogn8n-n8n",
                "dmlogn8n-dmlogn8n-api",
                "dmlogn8n-character-coder",
                "dmlogn8n-player-portal",
                "dmlogn8n-nginx"
            ]

            for container_name in current_containers:
                try:
                    container = self.docker_client.containers.get(container_name)
                    container.stop()
                    container.remove()
                    self.logger.info(f"Removed container: {container_name}")
                except docker.errors.NotFound:
                    self.logger.info(f"Container {container_name} not found")
                except Exception as e:
                    self.logger.warning(f"Failed to remove container {container_name}: {e}")

            # Note: Container image restoration would require storing the actual images
            # For now, we'll restart containers with current images using restored configs
            self.logger.info("Container restoration completed (using current images with restored configs)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore containers: {e}")
            return False

    def restore_services(self, rollback_point: RollbackPoint) -> bool:
        """Restore services to their previous state"""
        try:
            self.logger.info("Restoring services...")

            # Restart services using docker-compose with restored configurations
            compose_file = self.deploy_dir / "docker" / "docker-compose.yml"

            if compose_file.exists():
                # Change to docker directory
                original_cwd = os.getcwd()
                os.chdir(self.deploy_dir / "docker")

                try:
                    # Start services
                    subprocess.run(["docker-compose", "up", "-d"], check=True)
                    self.logger.info("Services restarted successfully")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to restart services: {e}")
                    return False
                finally:
                    os.chdir(original_cwd)
            else:
                self.logger.warning("Docker Compose file not found, skipping service restoration")

            return True

        except Exception as e:
            self.logger.error(f"Failed to restore services: {e}")
            return False

    def execute_rollback(self, deployment_id: str = None, rollback_type: RollbackType = RollbackType.FULL) -> bool:
        """Execute rollback for a deployment"""
        try:
            self.logger.info(f"Starting rollback for deployment {deployment_id}")

            # Create rollback operation
            rollback_op_id = f"rollback_op_{int(time.time())}"
            rollback_operation = RollbackOperation(
                id=rollback_op_id,
                timestamp=datetime.now(),
                rollback_point_id="",
                rollback_type=rollback_type,
                status=RollbackStatus.IN_PROGRESS,
                steps_completed=[],
                steps_failed=[]
            )

            # Get rollback point
            if deployment_id:
                # Find rollback point for specific deployment
                rollback_point = None
                for rollback_dir in self.rollback_dir.iterdir():
                    if rollback_dir.is_dir():
                        metadata_file = rollback_dir / "rollback_point.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r') as f:
                                data = json.load(f)
                                if data.get("deployment_id") == deployment_id:
                                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                                    rollback_point = RollbackPoint(**data)
                                    break
            else:
                # Get latest rollback point
                rollback_point = self.get_latest_rollback_point()

            if not rollback_point:
                self.logger.error("No rollback point found")
                rollback_operation.status = RollbackStatus.FAILED
                rollback_operation.error_message = "No rollback point found"
                return False

            rollback_operation.rollback_point_id = rollback_point.id
            self.logger.info(f"Using rollback point: {rollback_point.id}")

            # Execute rollback steps based on type
            success = True

            if rollback_type in [RollbackType.FULL, RollbackType.CONFIGURATION]:
                if self.restore_configurations(rollback_point):
                    rollback_operation.steps_completed.append("configurations")
                else:
                    rollback_operation.steps_failed.append("configurations")
                    success = False

            if rollback_type in [RollbackType.FULL, RollbackType.DATABASE]:
                if self.restore_databases(rollback_point):
                    rollback_operation.steps_completed.append("databases")
                else:
                    rollback_operation.steps_failed.append("databases")
                    success = False

            if rollback_type in [RollbackType.FULL, RollbackType.CONTAINERS]:
                if self.restore_containers(rollback_point):
                    rollback_operation.steps_completed.append("containers")
                else:
                    rollback_operation.steps_failed.append("containers")
                    success = False

            if rollback_type in [RollbackType.FULL, RollbackType.SERVICES]:
                if self.restore_services(rollback_point):
                    rollback_operation.steps_completed.append("services")
                else:
                    rollback_operation.steps_failed.append("services")
                    success = False

            # Update rollback operation status
            if success:
                rollback_operation.status = RollbackStatus.SUCCESS
                self.logger.info("Rollback completed successfully")
            else:
                if rollback_operation.steps_completed:
                    rollback_operation.status = RollbackStatus.PARTIAL
                    self.logger.warning("Rollback partially completed")
                else:
                    rollback_operation.status = RollbackStatus.FAILED
                    self.logger.error("Rollback failed")

            # Save rollback operation metadata
            op_metadata_file = self.rollback_dir / f"{rollback_op_id}.json"
            with open(op_metadata_file, 'w') as f:
                json.dump(asdict(rollback_operation), f, indent=2, default=str)

            return success

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def list_rollback_points(self) -> List[Dict[str, Any]]:
        """List available rollback points"""
        try:
            rollback_points = []

            for rollback_dir in self.rollback_dir.iterdir():
                if rollback_dir.is_dir():
                    metadata_file = rollback_dir / "rollback_point.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            data = json.load(f)
                            if data.get("environment") == self.environment:
                                rollback_points.append({
                                    "id": data["id"],
                                    "timestamp": data["timestamp"],
                                    "deployment_id": data["deployment_id"],
                                    "description": data["description"],
                                    "config_files_count": len(data.get("config_files", [])),
                                    "database_backups_count": len(data.get("database_backups", [])),
                                    "container_images_count": len(data.get("container_images", {}))
                                })

            # Sort by timestamp (newest first)
            rollback_points.sort(key=lambda x: x["timestamp"], reverse=True)
            return rollback_points

        except Exception as e:
            self.logger.error(f"Failed to list rollback points: {e}")
            return []

    def cleanup_old_rollbacks(self, keep_count: int = 10) -> bool:
        """Clean up old rollback points"""
        try:
            rollback_points = self.list_rollback_points()

            if len(rollback_points) <= keep_count:
                return True

            # Remove oldest rollback points
            rollback_points_to_remove = rollback_points[keep_count:]

            for rollback_point in rollback_points_to_remove:
                rollback_path = self.rollback_dir / rollback_point["id"]
                if rollback_path.exists():
                    shutil.rmtree(rollback_path)
                    self.logger.info(f"Removed old rollback point: {rollback_point['id']}")

            self.logger.info(f"Cleanup completed. Kept {keep_count} most recent rollback points")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cleanup old rollbacks: {e}")
            return False


def main():
    """Main entry point for rollback operations"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Rollback Manager")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--action", choices=["list", "rollback", "cleanup"],
                       default="list", help="Action to perform")
    parser.add_argument("--deployment-id", help="Specific deployment ID to rollback")
    parser.add_argument("--rollback-type", choices=["full", "configuration", "database", "services", "containers"],
                       default="full", help="Type of rollback to perform")
    parser.add_argument("--create-point", help="Create rollback point for deployment")
    parser.add_argument("--description", help="Description for rollback point")
    parser.add_argument("--keep-count", type=int, default=10,
                       help="Number of rollback points to keep during cleanup")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize rollback manager
    rollback_manager = RollbackManager(args.environment)

    try:
        if args.action == "list":
            rollback_points = rollback_manager.list_rollback_points()
            if rollback_points:
                print(f"\n📋 Available Rollback Points for {args.environment}:")
                print("-" * 80)
                for rp in rollback_points:
                    print(f"ID: {rp['id']}")
                    print(f"Timestamp: {rp['timestamp']}")
                    print(f"Deployment: {rp['deployment_id']}")
                    print(f"Description: {rp['description']}")
                    print(f"Config Files: {rp['config_files_count']}")
                    print(f"Database Backups: {rp['database_backups_count']}")
                    print(f"Container Images: {rp['container_images_count']}")
                    print("-" * 80)
            else:
                print("No rollback points found")

        elif args.action == "rollback":
            if args.create_point:
                success = rollback_manager.create_rollback_point(args.create_point, args.description or "")
                if success:
                    print(f"✅ Rollback point created for deployment {args.create_point}")
                else:
                    print("❌ Failed to create rollback point")
            else:
                success = rollback_manager.execute_rollback(
                    args.deployment_id,
                    RollbackType(args.rollback_type)
                )
                if success:
                    print("✅ Rollback completed successfully!")
                else:
                    print("❌ Rollback failed!")

        elif args.action == "cleanup":
            success = rollback_manager.cleanup_old_rollbacks(args.keep_count)
            if success:
                print(f"✅ Cleanup completed. Kept {args.keep_count} rollback points.")
            else:
                print("❌ Cleanup failed!")

    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()