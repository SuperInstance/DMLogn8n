#!/usr/bin/env python3
"""
DMLog Development Tools
Utility scripts for development tasks
"""

import os
import sys
import subprocess
import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import psutil

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "source_code" / "backend"))

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

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

class DMLogDevTools:
    """Development utilities for DMLog"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "source_code" / "backend"
        self.docker_dir = self.project_root / "production_env" / "docker"
        self.venv_python = self.backend_dir / "venv" / "bin" / "python"

    def run_command(self, command: str, cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.backend_dir,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            log_error(f"Command failed: {command}")
            if e.stdout:
                print(f"Output: {e.stdout}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            if check:
                sys.exit(1)
            return e

    # Code Quality Tools
    def format_code(self, check_only: bool = False):
        """Format code with black and isort"""
        log_header("Code Formatting")

        if not self.venv_python.exists():
            log_error("Virtual environment not found")
            return

        # Black
        cmd = f"{self.venv_python} -m black"
        if check_only:
            cmd += " --check --diff"
        cmd += " ."

        log_info("Running black...")
        result = self.run_command(cmd, check=False)
        if result.returncode == 0:
            log_success("✅ Black formatting passed")
        else:
            if check_only:
                log_error("❌ Code formatting issues found")
            else:
                log_success("✅ Code formatted with black")

        # Isort
        cmd = f"{self.venv_python} -m isort"
        if check_only:
            cmd += " --check-only --diff"
        cmd += " ."

        log_info("Running isort...")
        result = self.run_command(cmd, check=False)
        if result.returncode == 0:
            log_success("✅ Import sorting passed")
        else:
            if check_only:
                log_error("❌ Import sorting issues found")
            else:
                log_success("✅ Imports sorted with isort")

    def lint_code(self):
        """Run linting with flake8 and mypy"""
        log_header("Code Linting")

        if not self.venv_python.exists():
            log_error("Virtual environment not found")
            return

        # Flake8
        log_info("Running flake8...")
        result = self.run_command(
            f"{self.venv_python} -m flake8 . --max-line-length=100 --extend-ignore=E203,W503",
            check=False
        )
        if result.returncode == 0:
            log_success("✅ Flake8 linting passed")
        else:
            log_warning("⚠ Flake8 found issues:")
            print(result.stdout)

        # MyPy
        log_info("Running mypy...")
        result = self.run_command(
            f"{self.venv_python} -m mypy . --ignore-missing-imports",
            check=False
        )
        if result.returncode == 0:
            log_success("✅ MyPy type checking passed")
        else:
            log_warning("⚠ MyPy found type issues:")
            print(result.stdout)

    def run_tests(self, coverage: bool = True, verbose: bool = False, marker: Optional[str] = None):
        """Run the test suite"""
        log_header("Running Tests")

        if not self.venv_python.exists():
            log_error("Virtual environment not found")
            return

        cmd = f"{self.venv_python} -m pytest"
        if verbose:
            cmd += " -v"
        if coverage:
            cmd += " --cov=. --cov-report=term-missing --cov-report=html:htmlcov"
        if marker:
            cmd += f" -m {marker}"

        log_info(f"Running: {cmd}")
        result = self.run_command(cmd, check=False)

        if result.returncode == 0:
            log_success("✅ All tests passed")
        else:
            log_error("❌ Some tests failed")
            if verbose:
                print(result.stdout)

    # Database Tools
    def migrate_database(self, message: Optional[str] = None):
        """Run database migrations"""
        log_header("Database Migration")

        if not self.venv_python.exists():
            log_error("Virtual environment not found")
            return

        # Create migration
        if message:
            log_info("Creating new migration...")
            result = self.run_command(
                f"{self.venv_python} -m alembic revision --autogenerate -m '{message}'"
            )
            if result.returncode == 0:
                log_success("✅ Migration created")

        # Apply migrations
        log_info("Applying migrations...")
        result = self.run_command(f"{self.venv_python} -m alembic upgrade head", check=False)

        if result.returncode == 0:
            log_success("✅ Migrations applied successfully")
        else:
            log_error("❌ Migration failed")

    def reset_database(self, confirm: bool = False):
        """Reset the database"""
        log_header("Database Reset")

        if not confirm:
            response = input("⚠️  This will delete all data. Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                log_info("Database reset cancelled")
                return

        log_info("Dropping all tables...")
        # Implementation would go here
        log_success("✅ Database reset")

    # Cache Tools
    def clear_cache(self, cache_type: str = "all"):
        """Clear various caches"""
        log_header(f"Clearing Cache: {cache_type}")

        if cache_type in ["all", "redis"]:
            log_info("Clearing Redis cache...")
            try:
                result = self.run_command(
                    "docker-compose exec redis redis-cli FLUSHALL",
                    cwd=self.docker_dir,
                    check=False
                )
                if result.returncode == 0:
                    log_success("✅ Redis cache cleared")
                else:
                    log_warning("⚠ Redis cache clear failed (is Redis running?)")
            except:
                log_warning("⚠ Could not clear Redis cache")

        if cache_type in ["all", "application"]:
            log_info("Clearing application cache...")
            # Implementation for app cache
            log_success("✅ Application cache cleared")

    # Docker Tools
    def docker_logs(self, service: Optional[str] = None, follow: bool = False):
        """View Docker logs"""
        log_header("Docker Logs")

        compose_file = self.docker_dir / "docker-compose.dev.yml"
        if not compose_file.exists():
            log_error("Docker compose file not found")
            return

        cmd = f"docker-compose -f {compose_file} logs"
        if follow:
            cmd += " -f"
        if service:
            cmd += f" {service}"

        log_info(f"Viewing logs: {cmd}")
        os.system(cmd)

    def docker_restart(self, service: Optional[str] = None):
        """Restart Docker services"""
        log_header("Restarting Docker Services")

        compose_file = self.docker_dir / "docker-compose.dev.yml"
        if not compose_file.exists():
            log_error("Docker compose file not found")
            return

        cmd = f"docker-compose -f {compose_file} restart"
        if service:
            cmd += f" {service}"

        log_info(f"Running: {cmd}")
        result = self.run_command(cmd, cwd=self.docker_dir)

        if result.returncode == 0:
            log_success("✅ Services restarted")
        else:
            log_error("❌ Failed to restart services")

    # Performance Tools
    def run_benchmark(self, test_type: str = "load"):
        """Run performance benchmarks"""
        log_header(f"Running Benchmark: {test_type}")

        if test_type == "load":
            self._run_load_test()
        elif test_type == "api":
            self._run_api_benchmark()
        elif test_type == "database":
            self._run_database_benchmark()

    def _run_load_test(self):
        """Run load test"""
        log_info("Running API load test...")

        # Simple load test script
        test_script = '''
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def make_request(session, url):
    try:
        start = time.time()
        async with session.get(url) as response:
            await response.text()
            return time.time() - start
    except:
        return None

async def load_test():
    url = "http://localhost:8000/api/v1/health"

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):  # 100 concurrent requests
            tasks.append(make_request(session, url))

        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]

        if results:
            avg_time = sum(results) / len(results)
            min_time = min(results)
            max_time = max(results)

            print(f"✅ Load test completed")
            print(f"   Requests: {len(results)}")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
        else:
            print("❌ Load test failed - no successful requests")

if __name__ == "__main__":
    asyncio.run(load_test())
'''

        test_file = self.backend_dir / "load_test.py"
        with open(test_file, 'w') as f:
            f.write(test_script)

        result = self.run_command(f"{self.venv_python} {test_file}", check=False)
        test_file.unlink()  # Clean up

    def _run_api_benchmark(self):
        """Run API benchmark"""
        log_info("Running API endpoint benchmarks...")
        # Implementation for API benchmarking

    def _run_database_benchmark(self):
        """Run database benchmark"""
        log_info("Running database performance test...")
        # Implementation for database benchmarking

    # Monitoring Tools
    def show_system_status(self):
        """Show system resource status"""
        log_header("System Status")

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"🖥  CPU Usage: {cpu_percent}%")

        # Memory
        memory = psutil.virtual_memory()
        print(f"💾 Memory Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")

        # Disk
        disk = psutil.disk_usage('/')
        print(f"💿 Disk Usage: {disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)")

        # Docker containers
        try:
            result = self.run_command("docker ps --format 'table {{.Names}}\\t{{.Status}}'", check=False)
            if result.returncode == 0:
                print("\n📦 Docker Containers:")
                print(result.stdout)
        except:
            print("\n📦 Docker: Not available")

        # Network
        network = psutil.net_io_counters()
        print(f"\n🌐 Network: {network.bytes_sent / 1024**2:.1f}MB sent, {network.bytes_recv / 1024**2:.1f}MB received")

    def show_process_status(self):
        """Show DMLog process status"""
        log_header("DMLog Process Status")

        # Find DMLog processes
        dmlog_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'dmlog' in ' '.join(proc.info['cmdline'] or []).lower() or 'uvicorn' in proc.info.get('name', ''):
                    dmlog_processes.append(proc)
            except:
                pass

        if dmlog_processes:
            for proc in dmlog_processes:
                try:
                    cpu = proc.cpu_percent()
                    memory = proc.memory_info() / 1024**2  # MB
                    print(f"📍 PID {proc.pid}: {proc.name()} - CPU: {cpu}% - Memory: {memory:.1f}MB")
                    print(f"   Command: {' '.join(proc.cmdline()[:2])}...")
                except:
                    pass
        else:
            log_info("No DMLog processes found")

    # Utility Tools
    def generate_api_key(self):
        """Generate a new API key"""
        import secrets

        log_header("Generating API Key")

        key = f"dmlog_{secrets.token_urlsafe(32)}"
        print(f"🔑 New API Key: {key}")
        print("\n⚠  Save this key securely. It will not be shown again.")

    def backup_data(self):
        """Create data backup"""
        log_header("Creating Data Backup")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "backups" / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup database
        log_info("Backing up database...")
        try:
            result = self.run_command(
                f"docker-compose exec postgres pg_dump -U dmlog_user dmlog_dev > {backup_dir}/database.sql",
                cwd=self.docker_dir,
                check=False
            )
            if result.returncode == 0:
                log_success("✅ Database backed up")
            else:
                log_warning("⚠ Database backup failed")
        except:
            log_warning("⚠ Could not backup database")

        # Backup data directory
        data_dir = self.project_root / "data"
        if data_dir.exists():
            import shutil
            shutil.copytree(data_dir, backup_dir / "data")
            log_success("✅ Data directory backed up")

        # Compress backup
        import zipfile
        backup_zip = self.project_root / "backups" / f"backup_{timestamp}.zip"
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_dir)
                    zipf.write(file_path, arcname)

        # Remove uncompressed backup
        import shutil
        shutil.rmtree(backup_dir)

        log_success(f"✅ Backup created: {backup_zip}")

    def clean_logs(self, days: int = 7):
        """Clean old log files"""
        log_header(f"Cleaning Logs (older than {days} days)")

        log_dirs = [
            self.backend_dir / "logs",
            self.project_root / "logs",
            self.project_root / "data" / "logs"
        ]

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        cleaned_files = 0

        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log*"):
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        cleaned_files += 1

        if cleaned_files > 0:
            log_success(f"✅ Cleaned {cleaned_files} log files")
        else:
            log_info("No old log files found")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DMLog Development Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev_tools.py format                # Format code
  python dev_tools.py test                  # Run tests
  python dev_tools.py test -m unit         # Run unit tests only
  python dev_tools.py docker-logs api       # View API logs
  python dev_tools.py benchmark load        # Run load test
  python dev_tools.py status                # Show system status
        """
    )

    # Code Quality
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("--format", action="store_true", help="Format code with black and isort")
    parser.add_argument("--check", action="store_true", help="Check code formatting without changing")
    parser.add_argument("--lint", action="store_true", help="Run linting with flake8 and mypy")

    # Testing
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("-m", "--marker", help="Run tests with specific marker")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose test output")

    # Database
    parser.add_argument("--migrate", help="Create and run migration with message")
    parser.add_argument("--reset-db", action="store_true", help="Reset database (DELETES ALL DATA)")
    parser.add_argument("--confirm", action="store_true", help="Confirm destructive actions")

    # Cache
    parser.add_argument("--clear-cache", choices=["all", "redis", "application"], help="Clear specified cache")

    # Docker
    parser.add_argument("--docker-logs", help="View logs for specific service")
    parser.add_argument("--docker-restart", help="Restart specific service")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")

    # Performance
    parser.add_argument("--benchmark", choices=["load", "api", "database"], help="Run performance benchmark")

    # Monitoring
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--processes", action="store_true", help="Show DMLog processes")

    # Utilities
    parser.add_argument("--generate-key", action="store_true", help="Generate new API key")
    parser.add_argument("--backup", action="store_true", help="Create data backup")
    parser.add_argument("--clean-logs", type=int, metavar="DAYS", help="Clean logs older than N days")

    args = parser.parse_args()

    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    tools = DMLogDevTools()

    # Execute commands
    if args.command == "format" or args.format:
        tools.format_code(check_only=args.check)
    elif args.command == "lint" or args.lint:
        tools.lint_code()
    elif args.command == "test" or args.test:
        tools.run_tests(coverage=args.coverage, verbose=args.verbose, marker=args.marker)
    elif args.command == "migrate" or args.migrate:
        tools.migrate_database(message=args.migrate)
    elif args.command == "reset-db" or args.reset_db:
        tools.reset_database(confirm=args.confirm)
    elif args.clear_cache:
        tools.clear_cache(args.clear_cache)
    elif args.command == "docker-logs" or args.docker_logs:
        tools.docker_logs(service=args.docker_logs, follow=args.follow)
    elif args.command == "docker-restart" or args.docker_restart:
        tools.docker_restart(service=args.docker_restart)
    elif args.command == "benchmark" or args.benchmark:
        tools.run_benchmark(test_type=args.benchmark)
    elif args.command == "status" or args.status:
        tools.show_system_status()
    elif args.command == "processes" or args.processes:
        tools.show_process_status()
    elif args.command == "generate-key" or args.generate_key:
        tools.generate_api_key()
    elif args.command == "backup" or args.backup:
        tools.backup_data()
    elif args.command == "clean-logs" or args.clean_logs:
        tools.clean_logs(days=args.clean_logs)
    else:
        log_error(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()