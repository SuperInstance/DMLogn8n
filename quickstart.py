#!/usr/bin/env python3
"""
DMLog Quick Start Script
Automated project initialization and deployment script for DMLog Week 1

This script handles:
- Environment validation
- Dependency installation
- Database migration
- Admin user creation
- Sample data generation
- Health checks

Usage:
    python quickstart.py [--skip-deps] [--skip-db] [--skip-seed] [--dev|--prod]

Author: DMLog Development Team
Version: 1.0.0
"""

import asyncio
import argparse
import os
import sys
import subprocess
import json
import time
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
    import psycopg2
    import redis
    import yaml
    from rich.console import Console
    from rich.progress import Progress, TaskID
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    import structlog
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please run: pip install requests psycopg2-binary redis pyyaml rich structlog")
    sys.exit(1)

# Initialize rich console and structured logging
console = Console()
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class QuickStartConfig:
    """Configuration for quick start script"""
    environment: Environment
    skip_dependencies: bool = False
    skip_database: bool = False
    skip_seeding: bool = False
    skip_health_check: bool = False
    project_root: Path = PROJECT_ROOT
    venv_name: str = "dmlog_env"
    requirements_file: str = "requirements.txt"
    env_file: str = ".env"
    docker_compose_file: str = "docker-compose.yml"


class QuickStartError(Exception):
    """Custom exception for quick start errors"""
    pass


class DMLogQuickStart:
    """Main quick start class"""

    def __init__(self, config: QuickStartConfig):
        self.config = config
        self.console = console
        self.logger = logger.bind(environment=config.environment.value)

    async def run(self) -> bool:
        """Run the complete quick start process"""
        try:
            self._display_banner()

            with Progress() as progress:
                tasks = self._create_progress_tasks(progress)

                # Environment validation
                if not await self._validate_environment(progress, tasks["validation"]):
                    raise QuickStartError("Environment validation failed")

                # Dependency installation
                if not self.config.skip_dependencies:
                    if not await self._install_dependencies(progress, tasks["dependencies"]):
                        raise QuickStartError("Dependency installation failed")
                else:
                    progress.update(tasks["dependencies"], completed=100)
                    self.logger.info("Skipping dependency installation")

                # Database setup
                if not self.config.skip_database:
                    if not await self._setup_database(progress, tasks["database"]):
                        raise QuickStartError("Database setup failed")
                else:
                    progress.update(tasks["database"], completed=100)
                    self.logger.info("Skipping database setup")

                # Sample data seeding
                if not self.config.skip_seeding:
                    if not await self._seed_sample_data(progress, tasks["seeding"]):
                        raise QuickStartError("Sample data seeding failed")
                else:
                    progress.update(tasks["seeding"], completed=100)
                    self.logger.info("Skipping sample data seeding")

                # Health checks
                if not self.config.skip_health_check:
                    if not await self._perform_health_checks(progress, tasks["health_check"]):
                        raise QuickStartError("Health checks failed")
                else:
                    progress.update(tasks["health_check"], completed=100)
                    self.logger.info("Skipping health checks")

            await self._display_completion_summary()
            return True

        except Exception as e:
            self.logger.error("Quick start failed", error=str(e), exc_info=True)
            self.console.print(f"[red]Quick start failed: {e}[/red]")
            return False

    def _display_banner(self):
        """Display application banner"""
        banner_text = Text.from_markup("""
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                    DMLog Quick Start                         ║[/bold cyan]
[bold cyan]║          Advanced D&D Campaign Management System           ║[/bold cyan]
[bold cyan]║                                                              ║[/bold cyan]
[bold cyan]║  Initializing your DMLog environment...                     ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]
        """)

        panel = Panel(
            banner_text,
            title="[bold green]DMLog v1.0.0[/bold green]",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()

    def _create_progress_tasks(self, progress: Progress) -> Dict[str, TaskID]:
        """Create progress bar tasks"""
        tasks = {
            "validation": progress.add_task("Validating environment...", total=100),
            "dependencies": progress.add_task("Installing dependencies...", total=100),
            "database": progress.add_task("Setting up database...", total=100),
            "seeding": progress.add_task("Seeding sample data...", total=100),
            "health_check": progress.add_task("Performing health checks...", total=100)
        }
        return tasks

    async def _validate_environment(self, progress: Progress, task_id: TaskID) -> bool:
        """Validate the development environment"""
        try:
            self.logger.info("Starting environment validation")

            # Check Python version
            progress.update(task_id, advance=20)
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 9:
                raise QuickStartError(f"Python 3.9+ required. Found: {python_version.major}.{python_version.minor}")

            self.logger.info("Python version check passed", version=f"{python_version.major}.{python_version.minor}")

            # Check virtual environment
            progress.update(task_id, advance=20)
            venv_path = self.config.project_root / self.config.venv_name
            if not venv_path.exists():
                raise QuickStartError(f"Virtual environment not found: {venv_path}")

            self.logger.info("Virtual environment check passed")

            # Check required files
            progress.update(task_id, advance=20)
            required_files = [
                self.config.requirements_file,
                "docker-compose.yml",
                "app/main.py"
            ]

            for file_name in required_files:
                file_path = self.config.project_root / file_name
                if not file_path.exists():
                    raise QuickStartError(f"Required file not found: {file_name}")

            self.logger.info("Required files check passed")

            # Check Docker
            progress.update(task_id, advance=20)
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    raise QuickStartError("Docker is not available")

                self.logger.info("Docker check passed", version=result.stdout.strip())
            except subprocess.TimeoutExpired:
                raise QuickStartError("Docker command timed out")
            except FileNotFoundError:
                raise QuickStartError("Docker is not installed")

            # Check Docker Compose
            progress.update(task_id, advance=20)
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    raise QuickStartError("Docker Compose is not available")

                self.logger.info("Docker Compose check passed", version=result.stdout.strip())
            except subprocess.TimeoutExpired:
                raise QuickStartError("Docker Compose command timed out")
            except FileNotFoundError:
                raise QuickStartError("Docker Compose is not installed")

            progress.update(task_id, completed=100)
            self.logger.info("Environment validation completed successfully")
            return True

        except Exception as e:
            self.logger.error("Environment validation failed", error=str(e))
            return False

    async def _install_dependencies(self, progress: Progress, task_id: TaskID) -> bool:
        """Install Python dependencies"""
        try:
            self.logger.info("Starting dependency installation")

            # Activate virtual environment and install dependencies
            venv_python = self.config.project_root / self.config.venv_name / "bin" / "python"
            requirements_path = self.config.project_root / self.config.requirements_file

            progress.update(task_id, advance=30)

            # Upgrade pip
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise QuickStartError(f"Failed to upgrade pip: {result.stderr}")

            self.logger.info("Pip upgrade completed")

            progress.update(task_id, advance=40)

            # Install requirements
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                raise QuickStartError(f"Failed to install requirements: {result.stderr}")

            self.logger.info("Dependencies installed successfully")

            progress.update(task_id, advance=30)

            # Verify installation
            critical_packages = ["fastapi", "uvicorn", "sqlalchemy", "alembic", "pydantic"]
            for package in critical_packages:
                result = subprocess.run(
                    [str(venv_python), "-c", f"import {package}"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    raise QuickStartError(f"Failed to import critical package: {package}")

            self.logger.info("Critical packages verification passed")

            progress.update(task_id, completed=100)
            return True

        except Exception as e:
            self.logger.error("Dependency installation failed", error=str(e))
            return False

    async def _setup_database(self, progress: Progress, task_id: TaskID) -> bool:
        """Set up the database"""
        try:
            self.logger.info("Starting database setup")

            # Start database services
            progress.update(task_id, advance=20)

            os.chdir(self.config.project_root)
            result = subprocess.run(
                ["docker-compose", "up", "-d", "postgres", "redis"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise QuickStartError(f"Failed to start database services: {result.stderr}")

            self.logger.info("Database services started")

            progress.update(task_id, advance=20)

            # Wait for database to be ready
            await self._wait_for_database()

            progress.update(task_id, advance=30)

            # Run database migrations
            venv_python = self.config.project_root / self.config.venv_name / "bin" / "python"

            # Initialize Alembic if not already done
            alembic_ini = self.config.project_root / "alembic.ini"
            if not alembic_ini.exists():
                result = subprocess.run(
                    [str(venv_python), "-m", "alembic", "init", "alembic"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    self.logger.warning("Alembic initialization failed", error=result.stderr)

            progress.update(task_id, advance=30)

            # Create initial migration
            result = subprocess.run(
                [str(venv_python), "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Apply migration
            result = subprocess.run(
                [str(venv_python), "-m", "alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                # Fallback to direct SQL execution
                await self._execute_database_schema()

            self.logger.info("Database migration completed")

            progress.update(task_id, completed=100)
            return True

        except Exception as e:
            self.logger.error("Database setup failed", error=str(e))
            return False

    async def _wait_for_database(self, timeout: int = 60) -> bool:
        """Wait for database to be ready"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check PostgreSQL
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="dmlog_db",
                    user="dmlog_user",
                    password="dmlog_password",
                    connect_timeout=5
                )
                conn.close()

                self.logger.info("PostgreSQL is ready")
                break

            except psycopg2.OperationalError:
                await asyncio.sleep(2)
                continue

        # Check Redis
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                r = redis.Redis(host="localhost", port=6379, db=0)
                r.ping()

                self.logger.info("Redis is ready")
                break

            except redis.ConnectionError:
                await asyncio.sleep(1)
                continue

        return True

    async def _execute_database_schema(self):
        """Execute database schema directly"""
        schema_sql = """
        -- Create extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";

        -- Create users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create game_sessions table
        CREATE TABLE IF NOT EXISTS game_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create audit_logs table
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id UUID,
            details JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="dmlog_db",
            user="dmlog_user",
            password="dmlog_password"
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()
            self.logger.info("Database schema created successfully")
        finally:
            conn.close()

    async def _seed_sample_data(self, progress: Progress, task_id: TaskID) -> bool:
        """Seed sample data into the database"""
        try:
            self.logger.info("Starting sample data seeding")

            progress.update(task_id, advance=25)

            # Create admin user
            await self._create_admin_user()

            progress.update(task_id, advance=25)

            # Create sample users
            await self._create_sample_users()

            progress.update(task_id, advance=25)

            # Create sample game sessions
            await self._create_sample_game_sessions()

            progress.update(task_id, advance=25)

            self.logger.info("Sample data seeding completed")
            progress.update(task_id, completed=100)
            return True

        except Exception as e:
            self.logger.error("Sample data seeding failed", error=str(e))
            return False

    async def _create_admin_user(self):
        """Create admin user"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin_password = pwd_context.hash("admin123")

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="dmlog_db",
            user="dmlog_user",
            password="dmlog_password"
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, ("admin", "admin@dmlog.local", admin_password, True))
            conn.commit()
            self.logger.info("Admin user created/updated")
        finally:
            conn.close()

    async def _create_sample_users(self):
        """Create sample users"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        sample_users = [
            ("game_master", "gm@dmlog.local", "gm123", False),
            ("player1", "player1@dmlog.local", "player123", False),
            ("spectator", "spectator@dmlog.local", "spec123", False)
        ]

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="dmlog_db",
            user="dmlog_user",
            password="dmlog_password"
        )

        try:
            with conn.cursor() as cursor:
                for username, email, password, is_admin in sample_users:
                    password_hash = pwd_context.hash(password)
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, is_admin)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (username) DO NOTHING
                    """, (username, email, password_hash, is_admin))
            conn.commit()
            self.logger.info("Sample users created")
        finally:
            conn.close()

    async def _create_sample_game_sessions(self):
        """Create sample game sessions"""
        sample_sessions = [
            ("The Dragon's Lair", "A thrilling adventure through dangerous caves", "active"),
            ("Mystery of the Ancient Temple", "Explore forgotten ruins and uncover ancient secrets", "planning"),
            ("City Intrigue", "Political maneuvering in the capital city", "completed")
        ]

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="dmlog_db",
            user="dmlog_user",
            password="dmlog_password"
        )

        try:
            with conn.cursor() as cursor:
                # Get a user ID for the sessions
                cursor.execute("SELECT id FROM users WHERE username = 'game_master' LIMIT 1")
                result = cursor.fetchone()
                user_id = result[0] if result else None

                if user_id:
                    for title, description, status in sample_sessions:
                        cursor.execute("""
                            INSERT INTO game_sessions (user_id, title, description, status)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, title, description, status))
            conn.commit()
            self.logger.info("Sample game sessions created")
        finally:
            conn.close()

    async def _perform_health_checks(self, progress: Progress, task_id: TaskID) -> bool:
        """Perform comprehensive health checks"""
        try:
            self.logger.info("Starting health checks")

            # Database health check
            progress.update(task_id, advance=25)
            if not await self._check_database_health():
                raise QuickStartError("Database health check failed")

            # Redis health check
            progress.update(task_id, advance=25)
            if not await self._check_redis_health():
                raise QuickStartError("Redis health check failed")

            # Application health check
            progress.update(task_id, advance=25)
            if not await self._check_application_health():
                raise QuickStartError("Application health check failed")

            # Services health check
            progress.update(task_id, advance=25)
            if not await self._check_services_health():
                raise QuickStartError("Services health check failed")

            progress.update(task_id, completed=100)
            self.logger.info("All health checks passed")
            return True

        except Exception as e:
            self.logger.error("Health checks failed", error=str(e))
            return False

    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="dmlog_db",
                user="dmlog_user",
                password="dmlog_password",
                connect_timeout=5
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            conn.close()
            return result[0] == 1

        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False

    async def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            result = r.ping()
            return result

        except Exception as e:
            self.logger.error("Redis health check failed", error=str(e))
            return False

    async def _check_application_health(self) -> bool:
        """Check application health"""
        try:
            # Start the application in the background
            venv_python = self.config.project_root / self.config.venv_name / "bin" / "python"

            # Check if app is already running
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass

            # Start application
            app_process = subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for application to start
            await asyncio.sleep(5)

            # Check health endpoint
            response = requests.get("http://localhost:8000/health", timeout=5)

            # Clean up
            app_process.terminate()
            app_process.wait(timeout=10)

            return response.status_code == 200

        except Exception as e:
            self.logger.error("Application health check failed", error=str(e))
            return False

    async def _check_services_health(self) -> bool:
        """Check Docker services health"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return False

            # Parse output to check if services are running
            lines = result.stdout.strip().split('\n')
            running_services = 0

            for line in lines[1:]:  # Skip header
                if "Up" in line:
                    running_services += 1

            # At least postgres and redis should be running
            return running_services >= 2

        except Exception as e:
            self.logger.error("Services health check failed", error=str(e))
            return False

    async def _display_completion_summary(self):
        """Display completion summary"""
        # Create summary table
        table = Table(title="DMLog Quick Start Summary")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        components = [
            ("Environment", "✅ Ready", f"Python {sys.version.major}.{sys.version.minor}"),
            ("Dependencies", "✅ Installed", f"Virtual env: {self.config.venv_name}"),
            ("Database", "✅ Running", "PostgreSQL & Redis"),
            ("Sample Data", "✅ Seeded", "Admin & sample users created"),
            ("Application", "✅ Ready", "FastAPI server configured"),
            ("Health Checks", "✅ Passed", "All systems operational"),
        ]

        for component, status, details in components:
            table.add_row(component, status, details)

        self.console.print(table)
        self.console.print()

        # Access information
        access_panel = Panel(
            Text.from_markup("""
[bold cyan]🚀 DMLog is ready to use![/bold cyan]

[bold]Access URLs:[/bold]
• API: http://localhost:8000
• Documentation: http://localhost:8000/docs
• Health Check: http://localhost:8000/health

[bold]Default Credentials:[/bold]
• Username: [yellow]admin[/yellow]
• Password: [yellow]admin123[/yellow]

[bold]Next Steps:[/bold]
1. Visit the API documentation
2. Change the default admin password
3. Explore the sample data
4. Start building your campaigns!

[bold red]⚠️  Security Note:[/bold red]
Remember to change default passwords and update
environment variables before production use.
            """),
            title="[bold green]Deployment Complete![/bold green]",
            border_style="green"
        )

        self.console.print(access_panel)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="DMLog Quick Start Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python quickstart.py                    # Full setup with all components
    python quickstart.py --skip-deps        # Skip dependency installation
    python quickstart.py --skip-db          # Skip database setup
    python quickstart.py --skip-seed        # Skip sample data seeding
    python quickstart.py --dev              # Development environment setup
    python quickstart.py --prod             # Production environment setup
        """
    )

    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation"
    )

    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database setup and migrations"
    )

    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip sample data seeding"
    )

    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip final health checks"
    )

    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument(
        "--dev",
        action="store_true",
        help="Set up development environment (default)"
    )

    env_group.add_argument(
        "--staging",
        action="store_true",
        help="Set up staging environment"
    )

    env_group.add_argument(
        "--prod",
        action="store_true",
        help="Set up production environment"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser


async def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Determine environment
    if args.prod:
        environment = Environment.PRODUCTION
    elif args.staging:
        environment = Environment.STAGING
    else:
        environment = Environment.DEVELOPMENT

    # Create configuration
    config = QuickStartConfig(
        environment=environment,
        skip_dependencies=args.skip_deps,
        skip_database=args.skip_db,
        skip_seeding=args.skip_seed,
        skip_health_check=args.skip_health_check
    )

    # Configure logging level
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Run quick start
    quickstart = DMLogQuickStart(config)
    success = await quickstart.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())