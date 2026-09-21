#!/usr/bin/env python3
"""
DMLog Quick Start Script
Quickly initialize and start the DMLog development environment
"""

import os
import sys
import subprocess
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")

def log_warning(message: str):
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")

def log_error(message: str):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")

def log_header(message: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def run_command(command: str, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {command}")
        log_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

class DMLogQuickStart:
    """DMLog Quick Start Manager"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "source_code" / "backend"
        self.docker_dir = self.project_root / "production_env" / "docker"
        self.env_file = self.backend_dir / ".env.development"

    def validate_environment(self) -> bool:
        """Validate the development environment"""
        log_header("Validating Environment")

        all_valid = True

        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 11:
            log_success(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            log_error(f"Python 3.11+ required, found {python_version.major}.{python_version.minor}.{python_version.micro}")
            all_valid = False

        # Check if directories exist
        required_dirs = [
            self.project_root,
            self.backend_dir,
            self.docker_dir
        ]

        for dir_path in required_dirs:
            if dir_path.exists():
                log_success(f"Directory exists: {dir_path.relative_to(self.project_root)}")
            else:
                log_error(f"Directory missing: {dir_path}")
                all_valid = False

        # Check Docker
        try:
            result = run_command("docker --version")
            log_success(f"Docker: {result.stdout.strip()}")
        except:
            log_error("Docker not found. Please install Docker.")
            all_valid = False

        # Check Docker Compose
        try:
            result = run_command("docker compose version")
            log_success(f"Docker Compose: {result.stdout.strip()}")
        except:
            try:
                result = run_command("docker-compose --version")
                log_success(f"Docker Compose: {result.stdout.strip()}")
            except:
                log_error("Docker Compose not found. Please install Docker Compose.")
                all_valid = False

        # Check if virtual environment exists
        venv_dir = self.backend_dir / "venv"
        if venv_dir.exists():
            log_success("Python virtual environment exists")
        else:
            log_warning("Virtual environment not found. Will create one.")

        return all_valid

    def setup_environment(self):
        """Set up the development environment"""
        log_header("Setting Up Environment")

        # Run the setup script
        setup_script = self.project_root / "scripts" / "setup.sh"
        if setup_script.exists():
            log_info("Running setup script...")
            result = run_command(f"bash {setup_script}")
            log_success("Setup script completed")
        else:
            log_warning("Setup script not found. Creating minimal setup...")
            self.create_minimal_setup()

    def create_minimal_setup(self):
        """Create minimal setup if setup script is not available"""
        # Create necessary directories
        dirs_to_create = [
            self.backend_dir / "scripts",
            self.backend_dir / "logs",
            self.project_root / "data",
            self.project_root / "tests"
        ]

        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            log_success(f"Created directory: {dir_path}")

        # Create minimal .env file if it doesn't exist
        if not self.env_file.exists():
            env_template = """# DMLog Development Environment
APP_NAME=DMLog API
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://dmlog_user:dmlog_password@localhost:5432/dmlog_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=dev-secret-key-change-in-production

# API Keys (REQUIRED - add your keys here)
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Logging
LOG_LEVEL=debug
"""
            with open(self.env_file, 'w') as f:
                f.write(env_template)
            log_success("Created .env.development file")

            log_warning("⚠️  Please edit .env.development and add your API keys!")

    def check_api_keys(self) -> bool:
        """Check if API keys are configured"""
        log_header("Checking API Keys")

        if not self.env_file.exists():
            log_error("Environment file not found")
            return False

        # Read environment file
        with open(self.env_file, 'r') as f:
            content = f.read()

        required_keys = {
            'OPENAI_API_KEY': 'OpenAI',
            'ANTHROPIC_API_KEY': 'Anthropic'
        }

        all_keys_configured = True

        for key, provider in required_keys.items():
            if f"{key}=your-" in content or f"{key}=" in content and "your-" in content.split(f"{key}=")[1][:10]:
                log_error(f"{provider} API key not configured")
                all_keys_configured = False
            elif f"{key}=sk-" in content or len(content.split(f"{key}=")[1].strip()) > 20:
                log_success(f"{provider} API key configured")

        if not all_keys_configured:
            log_warning("Please configure your API keys in .env.development")
            log_info(f"Edit file: {self.env_file}")

        return all_keys_configured

    def start_services(self) -> bool:
        """Start Docker services"""
        log_header("Starting Docker Services")

        # Check if docker-compose file exists
        compose_file = self.docker_dir / "docker-compose.dev.yml"
        if not compose_file.exists():
            log_error("Docker compose file not found")
            return False

        # Start services
        log_info("Starting Docker services...")
        try:
            result = run_command(
                f"docker-compose -f {compose_file} up -d",
                cwd=self.docker_dir
            )
            log_success("Docker services started")

            # Wait for services to be ready
            log_info("Waiting for services to be ready...")
            time.sleep(10)

            # Check service health
            services = ["postgres", "redis", "qdrant"]
            all_healthy = True

            for service in services:
                try:
                    result = run_command(
                        f"docker-compose -f {compose_file} exec {service} echo 'healthy'",
                        cwd=self.docker_dir,
                        check=False
                    )
                    if result.returncode == 0:
                        log_success(f"✓ {service} is healthy")
                    else:
                        log_warning(f"⚠ {service} may not be ready yet")
                        all_healthy = False
                except:
                    log_warning(f"⚠ {service} health check failed")
                    all_healthy = False

            return all_healthy

        except Exception as e:
            log_error(f"Failed to start Docker services: {e}")
            return False

    def initialize_database(self) -> bool:
        """Initialize the database"""
        log_header("Initializing Database")

        # Activate virtual environment and run init script
        venv_python = self.backend_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = "python3"  # Fallback to system python

        init_script = self.backend_dir / "scripts" / "init_db.py"

        if not init_script.exists():
            log_warning("Database initialization script not found")
            log_info("Creating database tables manually...")
            return self.create_database_tables()

        try:
            log_info("Running database initialization...")
            result = run_command(
                f"{venv_python} {init_script}",
                cwd=self.backend_dir
            )
            log_success("Database initialized successfully")
            return True
        except Exception as e:
            log_error(f"Database initialization failed: {e}")
            return False

    def create_database_tables(self) -> bool:
        """Create database tables manually"""
        try:
            # Create a simple initialization script
            init_code = '''
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

async def create_tables():
    """Create database tables"""
    try:
        from database.connection import get_database
        from database.models import Base

        database = get_database()
        database.initialize()

        async with database._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)
'''

            init_script = self.backend_dir / "scripts" / "create_tables.py"
            with open(init_script, 'w') as f:
                f.write(init_code)

            # Run the script
            venv_python = self.backend_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = "python3"

            result = run_command(
                f"{venv_python} {init_script}",
                cwd=self.backend_dir
            )

            return result.returncode == 0

        except Exception as e:
            log_error(f"Failed to create database tables: {e}")
            return False

    def create_sample_data(self) -> bool:
        """Create sample data"""
        log_header("Creating Sample Data")

        sample_script = self.backend_dir / "scripts" / "create_sample_data.py"

        if not sample_script.exists():
            log_warning("Sample data script not found")
            return False

        try:
            venv_python = self.backend_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = "python3"

            log_info("Creating sample D&D data...")
            result = run_command(
                f"{venv_python} {sample_script}",
                cwd=self.backend_dir
            )
            log_success("Sample data created successfully")
            return True
        except Exception as e:
            log_error(f"Failed to create sample data: {e}")
            return False

    def start_api_server(self) -> bool:
        """Start the API server"""
        log_header("Starting API Server")

        # Check if API is already running
        try:
            result = run_command("curl -s http://localhost:8000/health", check=False)
            if result.returncode == 0:
                log_info("API server is already running")
                return True
        except:
            pass

        # Start API server
        venv_python = self.backend_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            log_error("Virtual environment not found")
            return False

        log_info("Starting API server in background...")

        # Create a script to start the server
        start_script = self.backend_dir / "scripts" / "start_api.py"
        start_code = '''
import subprocess
import sys
import os
from pathlib import Path

# Add to path
sys.path.append(str(Path(__file__).parent))

# Set environment
os.environ.setdefault('ENVIRONMENT', 'development')

# Start server
try:
    subprocess.run([
        sys.executable,
        "-m", "uvicorn", "api_server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
except KeyboardInterrupt:
    print("\\n👋 Server stopped")
except Exception as e:
    print(f"❌ Failed to start server: {e}")
    sys.exit(1)
'''

        with open(start_script, 'w') as f:
            f.write(start_code)

        # Start in background
        try:
            subprocess.Popen(
                [str(venv_python), str(start_script)],
                cwd=self.backend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for server to start
            log_info("Waiting for API server to start...")
            time.sleep(5)

            # Check if server is running
            try:
                result = run_command("curl -s http://localhost:8000/health", check=False)
                if result.returncode == 0:
                    log_success("✅ API server is running at http://localhost:8000")
                    return True
                else:
                    log_error("API server failed to start")
                    return False
            except:
                log_error("API server not responding")
                return False

        except Exception as e:
            log_error(f"Failed to start API server: {e}")
            return False

    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        log_header("Running Health Checks")

        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "overall": "healthy"
        }

        # Check API
        try:
            result = run_command("curl -s http://localhost:8000/health", check=False)
            if result.returncode == 0:
                health_data = json.loads(result.stdout)
                health_status["services"]["api"] = {
                    "status": "healthy",
                    "details": health_data
                }
                log_success("✅ API is healthy")
            else:
                health_status["services"]["api"] = {"status": "unhealthy"}
                health_status["overall"] = "degraded"
                log_error("❌ API is not responding")
        except:
            health_status["services"]["api"] = {"status": "unhealthy"}
            health_status["overall"] = "degraded"
            log_error("❌ API check failed")

        # Check Docker services
        try:
            result = run_command(
                "docker-compose -f docker-compose.dev.yml ps",
                cwd=self.docker_dir,
                check=False
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]  # Skip header lines
                running_services = 0
                total_services = 0

                for line in lines:
                    if line.strip():
                        total_services += 1
                        if "Up" in line:
                            running_services += 1

                if running_services == total_services and total_services > 0:
                    health_status["services"]["docker"] = {
                        "status": "healthy",
                        "running": running_services,
                        "total": total_services
                    }
                    log_success(f"✅ Docker services: {running_services}/{total_services} running")
                else:
                    health_status["services"]["docker"] = {
                        "status": "degraded",
                        "running": running_services,
                        "total": total_services
                    }
                    health_status["overall"] = "degraded"
                    log_warning(f"⚠ Docker services: {running_services}/{total_services} running")
            else:
                health_status["services"]["docker"] = {"status": "unhealthy"}
                health_status["overall"] = "degraded"
                log_error("❌ Docker services check failed")
        except:
            health_status["services"]["docker"] = {"status": "unhealthy"}
            health_status["overall"] = "degraded"
            log_error("❌ Docker check failed")

        # Save health status
        health_file = self.project_root / "health_status.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)

        return health_status

    def print_summary(self):
        """Print completion summary"""
        log_header("🎉 DMLog Quick Start Complete!")

        print(f"""
{Colors.GREEN}Your DMLog development environment is ready!{Colors.ENDC}

{Colors.CYAN}📚 Resources:{Colors.ENDC}
• API Documentation: http://localhost:8000/docs
• Interactive API: http://localhost:8000/redoc
• Health Check: http://localhost:8000/api/v1/health

{Colors.CYAN}🛠 Development Commands:{Colors.ENDC}
• Run tests: cd source_code/backend && pytest
• View logs: docker-compose -f production_env/docker/docker-compose.dev.yml logs -f
• Stop services: docker-compose -f production_env/docker/docker-compose.dev.yml down

{Colors.CYAN}📁 Important Files:{Colors.ENDC}
• Configuration: source_code/backend/.env.development
• Database scripts: source_code/backend/scripts/
• Docker config: production_env/docker/docker-compose.dev.yml

{Colors.CYAN}🚀 Next Steps:{Colors.ENDC}
1. Open the API documentation in your browser
2. Try the sample endpoints with the sample data
3. Run the test suite to verify everything works
4. Start building your D&D AI features!

{Colors.WARNING}⚠ Remember to configure your API keys in .env.development{Colors.ENDC}
        """)

    def full_setup(self):
        """Run complete setup process"""
        print(f"""
{Colors.BOLD}{Colors.HEADER}
██████╗ ██╗████████╗ ██████╗ ██████╗ ██╗███╗   ██╗    ██╗  ██╗ █████╗ ██╗     ███████╗
██╔══██╗██║╚══██╔══╝██╔════╝██╔═══██╗██║████╗  ██║    ██║  ██║██╔══██╗██║     ██╔════╝
██████╔╝██║   ██║   ██║     ██║   ██║██║██╔██╗ ██║    ███████║███████║██║     █████╗
██╔══██╗██║   ██║   ██║     ██║   ██║██║██║╚██╗██║    ██╔══██║██╔══██║██║     ██╔══╝
██║  ██║██║   ██║   ╚██████╗╚██████╔╝██║██║ ╚████║    ██║  ██║██║  ██║███████╗███████╗
╚═╝  ╚═╝╚═╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
{Colors.ENDC}
{Colors.BLUE}AI-Powered D&D Character Learning System - Quick Start{Colors.ENDC}
        """)

        # Validate environment
        if not self.validate_environment():
            log_error("Environment validation failed. Please fix the issues above.")
            return

        # Setup environment if needed
        if not self.backend_dir.exists() or not (self.backend_dir / "venv").exists():
            self.setup_environment()

        # Check API keys
        if not self.check_api_keys():
            log_error("Please configure your API keys before continuing.")
            log_info(f"Edit: {self.env_file}")
            return

        # Start services
        if not self.start_services():
            log_error("Failed to start Docker services")
            return

        # Initialize database
        if not self.initialize_database():
            log_error("Failed to initialize database")
            return

        # Create sample data
        if not self.create_sample_data():
            log_warning("Failed to create sample data (continuing anyway)")

        # Start API server
        if not self.start_api_server():
            log_error("Failed to start API server")
            return

        # Run health checks
        health = self.run_health_checks()

        # Print summary
        self.print_summary()

        # Save status
        status_file = self.project_root / "quickstart_status.json"
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": health["overall"] == "healthy",
            "health": health
        }
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DMLog Quick Start Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quickstart.py              # Full setup
  python quickstart.py --check      # Check environment only
  python quickstart.py --services   # Start services only
  python quickstart.py --api        # Start API server only
  python quickstart.py --health     # Run health checks
        """
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate environment only"
    )
    parser.add_argument(
        "--services",
        action="store_true",
        help="Start Docker services only"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start API server only"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health checks only"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run environment setup only"
    )

    args = parser.parse_args()

    quickstart = DMLogQuickStart()

    if args.check:
        quickstart.validate_environment()
    elif args.setup:
        quickstart.setup_environment()
    elif args.services:
        quickstart.start_services()
    elif args.api:
        quickstart.start_api_server()
    elif args.health:
        quickstart.run_health_checks()
    else:
        quickstart.full_setup()

if __name__ == "__main__":
    main()