#!/usr/bin/env python3
"""
DMLog Development Tools Script
Comprehensive development utilities for DMLog project management

Features:
- Code formatting and linting
- Test runner with coverage
- Database operations
- Cache management
- Log viewing and analysis
- Performance monitoring
- Development server management

Usage:
    python dev_tools.py [COMMAND] [OPTIONS]

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
import signal
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import webbrowser

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import watchdog.observers
    import watchdog.events
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, TaskID, BarColumn, TextColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.tree import Tree
    import structlog
    import requests
    import psycopg2
    import redis
    import yaml
    import coverage
    import pytest
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please run: pip install rich watchdog structlog requests psycopg2-binary redis pyyaml coverage pytest")
    sys.exit(1)

# Initialize rich console
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
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class DevToolsError(Exception):
    """Custom exception for dev tools errors"""
    pass


@dataclass
class DevToolsConfig:
    """Configuration for dev tools"""
    project_root: Path = PROJECT_ROOT
    venv_name: str = "dmlog_env"
    app_module: str = "app.main"
    test_dir: str = "tests"
    source_dirs: List[str] = field(default_factory=lambda: ["app", "scripts"])
    log_dirs: List[str] = field(default_factory=lambda: ["logs"])
    config_file: str = "pyproject.toml"
    requirements_file: str = "requirements.txt"
    docker_compose_file: str = "docker-compose.yml"


class LogLevel(Enum):
    """Log levels for filtering"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CodeFormatter:
    """Handles code formatting and linting"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.venv_python = config.project_root / config.venv_name / "bin" / "python"

    async def format_code(self, check_only: bool = False) -> bool:
        """Format code using black and isort"""
        try:
            console.print("[bold cyan]Formatting code...[/bold cyan]")

            # Format with black
            black_cmd = [str(self.venv_python), "-m", "black"]
            if check_only:
                black_cmd.append("--check")
            black_cmd.extend(self.config.source_dirs)

            result = subprocess.run(black_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                console.print(f"[red]Black formatting failed:[/red]\n{result.stderr}")
                return False

            # Sort imports with isort
            isort_cmd = [str(self.venv_python), "-m", "isort"]
            if check_only:
                isort_cmd.append("--check-only")
            isort_cmd.extend(self.config.source_dirs)

            result = subprocess.run(isort_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                console.print(f"[red]Isort formatting failed:[/red]\n{result.stderr}")
                return False

            action = "checked" if check_only else "formatted"
            console.print(f"[green]Code {action} successfully![/green]")
            return True

        except subprocess.TimeoutExpired:
            console.print("[red]Code formatting timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Code formatting error:[/red] {e}")
            return False

    async def lint_code(self, fix: bool = False) -> bool:
        """Lint code using flake8 and mypy"""
        try:
            console.print("[bold cyan]Linting code...[/bold cyan]")

            # Run flake8
            flake8_cmd = [str(self.venv_python), "-m", "flake8"]
            flake8_cmd.extend(self.config.source_dirs)

            result = subprocess.run(flake8_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                console.print("[yellow]Flake8 found issues:[/yellow]")
                console.print(result.stdout)
            else:
                console.print("[green]Flake8: No issues found[/green]")

            # Run mypy
            mypy_cmd = [str(self.venv_python), "-m", "mypy"]
            mypy_cmd.extend(self.config.source_dirs)

            result = subprocess.run(mypy_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                console.print("[yellow]MyPy found type issues:[/yellow]")
                console.print(result.stdout)
            else:
                console.print("[green]MyPy: No type issues found[/green]")

            return True

        except subprocess.TimeoutExpired:
            console.print("[red]Code linting timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Code linting error:[/red] {e}")
            return False


class TestRunner:
    """Handles test execution and coverage"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.venv_python = config.project_root / config.venv_name / "bin" / "python"

    async def run_tests(self, coverage_enabled: bool = True, verbose: bool = False,
                       test_file: Optional[str] = None) -> bool:
        """Run tests with optional coverage"""
        try:
            console.print("[bold cyan]Running tests...[/bold cyan]")

            # Prepare pytest command
            pytest_cmd = [str(self.venv_python), "-m", "pytest"]

            if coverage_enabled:
                pytest_cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])

            if verbose:
                pytest_cmd.append("-v")

            if test_file:
                pytest_cmd.append(test_file)
            else:
                pytest_cmd.append(self.config.test_dir)

            # Run tests
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task("Running tests...", total=100)

                result = subprocess.run(
                    pytest_cmd,
                    cwd=self.config.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                progress.update(task, completed=100)

            # Display results
            if result.returncode == 0:
                console.print("[green]✅ All tests passed![/green]")

                if coverage_enabled:
                    # Display coverage summary
                    self._display_coverage_summary()

                return True
            else:
                console.print("[red]❌ Some tests failed:[/red]")
                console.print(result.stdout)
                if result.stderr:
                    console.print("[red]Errors:[/red]")
                    console.print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            console.print("[red]Tests timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Test execution error:[/red] {e}")
            return False

    def _display_coverage_summary(self):
        """Display coverage report summary"""
        try:
            coverage_file = self.config.project_root / "htmlcov" / "index.html"
            if coverage_file.exists():
                console.print(f"\n[green]Coverage report generated:[/green] {coverage_file}")
                console.print("Open the HTML file in your browser for detailed coverage information.")
        except Exception:
            pass


class DatabaseManager:
    """Handles database operations"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.venv_python = config.project_root / config.venv_name / "bin" / "python"

    async def create_migration(self, message: str) -> bool:
        """Create new database migration"""
        try:
            console.print(f"[bold cyan]Creating migration: {message}[/bold cyan]")

            alembic_cmd = [
                str(self.venv_python), "-m", "alembic",
                "revision", "--autogenerate", "-m", message
            ]

            result = subprocess.run(
                alembic_cmd,
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                console.print("[green]✅ Migration created successfully![/green]")
                return True
            else:
                console.print(f"[red]❌ Migration creation failed:[/red]\n{result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            console.print("[red]Migration creation timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Migration creation error:[/red] {e}")
            return False

    async def migrate_database(self, revision: str = "head") -> bool:
        """Apply database migrations"""
        try:
            console.print(f"[bold cyan]Migrating database to {revision}...[/bold cyan]")

            alembic_cmd = [
                str(self.venv_python), "-m", "alembic",
                "upgrade", revision
            ]

            result = subprocess.run(
                alembic_cmd,
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                console.print("[green]✅ Database migrated successfully![/green]")
                return True
            else:
                console.print(f"[red]❌ Database migration failed:[/red]\n{result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            console.print("[red]Database migration timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Database migration error:[/red] {e}")
            return False

    async def reset_database(self) -> bool:
        """Reset database to initial state"""
        try:
            console.print("[bold red]⚠️  Resetting database...[/bold red]")

            # Confirm reset
            if not console.input("[yellow]Are you sure you want to reset the database? (y/N): [/yellow]").lower() == 'y':
                console.print("[yellow]Database reset cancelled[/yellow]")
                return False

            # Stop database services
            await self._stop_database_services()

            # Remove volumes
            subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Start services again
            subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                cwd=self.config.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Wait for database
            await asyncio.sleep(10)

            # Run migrations
            await self.migrate_database()

            console.print("[green]✅ Database reset successfully![/green]")
            return True

        except Exception as e:
            console.print(f"[red]Database reset error:[/red] {e}")
            return False

    async def _stop_database_services(self):
        """Stop database services"""
        subprocess.run(
            ["docker-compose", "stop", "postgres"],
            cwd=self.config.project_root,
            capture_output=True,
            text=True,
            timeout=60
        )


class CacheManager:
    """Handles cache management operations"""

    def __init__(self, config: DevToolsConfig):
        self.config = config

    async def clear_redis_cache(self, pattern: str = "*") -> bool:
        """Clear Redis cache"""
        try:
            console.print(f"[bold cyan]Clearing Redis cache (pattern: {pattern})...[/bold cyan]")

            r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

            # Get keys matching pattern
            keys = r.keys(pattern)

            if keys:
                deleted_count = r.delete(*keys)
                console.print(f"[green]✅ Cleared {deleted_count} cache entries[/green]")
            else:
                console.print("[yellow]No cache entries found[/yellow]")

            return True

        except redis.ConnectionError:
            console.print("[red]❌ Redis connection failed[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Cache clearing error:[/red] {e}")
            return False

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis cache information"""
        try:
            r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

            info = r.info()
            keys_count = r.dbsize()

            cache_info = {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": keys_count,
                "uptime_seconds": info.get("uptime_in_seconds")
            }

            return cache_info

        except Exception as e:
            console.print(f"[red]Cache info error:[/red] {e}")
            return {}

    async def display_cache_info(self):
        """Display cache information in a formatted table"""
        cache_info = await self.get_cache_info()

        if cache_info:
            table = Table(title="Redis Cache Information")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            for key, value in cache_info.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
        else:
            console.print("[red]Unable to retrieve cache information[/red]")


class LogViewer:
    """Handles log viewing and analysis"""

    def __init__(self, config: DevToolsConfig):
        self.config = config

    async def tail_logs(self, log_file: str = "app.log", lines: int = 50,
                       level: Optional[LogLevel] = None) -> None:
        """Tail log files with optional filtering"""
        try:
            log_path = None

            # Find log file
            for log_dir in self.config.log_dirs:
                potential_path = self.config.project_root / log_dir / log_file
                if potential_path.exists():
                    log_path = potential_path
                    break

            if not log_path:
                console.print(f"[red]Log file not found: {log_file}[/red]")
                return

            console.print(f"[bold cyan]Tailing log file: {log_path}[/bold cyan]")

            # Use tail command to read lines
            tail_cmd = ["tail", "-n", str(lines), str(log_path)]

            result = subprocess.run(tail_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                log_lines = result.stdout.strip().split('\n')

                # Filter by level if specified
                if level:
                    log_lines = [line for line in log_lines if level.value in line]

                # Display logs
                for line in log_lines:
                    if "ERROR" in line or "CRITICAL" in line:
                        console.print(f"[red]{line}[/red]")
                    elif "WARNING" in line:
                        console.print(f"[yellow]{line}[/yellow]")
                    elif "INFO" in line:
                        console.print(f"[green]{line}[/green]")
                    else:
                        console.print(line)
            else:
                console.print(f"[red]Failed to read log file: {result.stderr}[/red]")

        except subprocess.TimeoutExpired:
            console.print("[red]Log reading timed out[/red]")
        except Exception as e:
            console.print(f"[red]Log viewing error:[/red] {e}")

    async def analyze_logs(self, log_file: str = "app.log",
                          time_range: Optional[str] = None) -> Dict[str, Any]:
        """Analyze log files for statistics"""
        try:
            log_path = self.config.project_root / "logs" / "app" / log_file

            if not log_path.exists():
                console.print(f"[red]Log file not found: {log_path}[/red]")
                return {}

            console.print(f"[bold cyan]Analyzing log file: {log_path}[/bold cyan]")

            # Basic log statistics
            with open(log_path, 'r') as f:
                lines = f.readlines()

            stats = {
                "total_lines": len(lines),
                "error_count": sum(1 for line in lines if "ERROR" in line),
                "warning_count": sum(1 for line in lines if "WARNING" in line),
                "info_count": sum(1 for line in lines if "INFO" in line),
                "debug_count": sum(1 for line in lines if "DEBUG" in line),
            }

            # Display statistics
            table = Table(title="Log Analysis Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            for key, value in stats.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
            return stats

        except Exception as e:
            console.print(f"[red]Log analysis error:[/red] {e}")
            return {}


class PerformanceMonitor:
    """Handles performance monitoring"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.monitoring = False

    async def start_monitoring(self, interval: int = 5) -> None:
        """Start performance monitoring"""
        self.monitoring = True
        console.print(f"[bold cyan]Starting performance monitoring (interval: {interval}s)...[/bold cyan]")
        console.print("Press Ctrl+C to stop monitoring")

        try:
            while self.monitoring:
                await self._display_performance_metrics()
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Performance monitoring stopped[/yellow]")
        finally:
            self.monitoring = False

    async def _display_performance_metrics(self):
        """Display current performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Application metrics (if running)
            app_metrics = await self._get_app_metrics()

            # Create metrics table
            table = Table(title=f"Performance Metrics - {time.strftime('%H:%M:%S')}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Status", style="yellow")

            # System metrics
            table.add_row("CPU Usage", f"{cpu_percent}%",
                         "🟢" if cpu_percent < 80 else "🔴")
            table.add_row("Memory Usage", f"{memory.percent}%",
                         f"{memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB",
                         "🟢" if memory.percent < 80 else "🔴")
            table.add_row("Disk Usage", f"{disk.percent}%",
                         f"{disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB",
                         "🟢" if disk.percent < 90 else "🔴")

            # Add application metrics if available
            if app_metrics:
                table.add_row("", "", "")  # Separator
                for key, value in app_metrics.items():
                    table.add_row(key, str(value), "🟢")

            # Clear screen and display table
            os.system('clear' if os.name == 'posix' else 'cls')
            console.print(table)

        except Exception as e:
            console.print(f"[red]Performance monitoring error:[/red] {e}")

    async def _get_app_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        try:
            # Check if app is running
            response = requests.get("http://localhost:8000/health", timeout=2)

            if response.status_code == 200:
                health_data = response.json()
                return {
                    "App Status": "Running",
                    "Response Time": f"{response.elapsed.total_seconds():.3f}s",
                    "Uptime": health_data.get("uptime", "N/A")
                }
        except requests.RequestException:
            return {"App Status": "Not Running"}

        return {}

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False


class DevelopmentServer:
    """Manages development server"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.server_process = None

    async def start_server(self, host: str = "0.0.0.0", port: int = 8000,
                          reload: bool = True, open_browser: bool = True) -> bool:
        """Start development server"""
        try:
            if self.server_process and self.server_process.poll() is None:
                console.print("[yellow]Server is already running[/yellow]")
                return True

            console.print(f"[bold cyan]Starting development server on {host}:{port}...[/bold cyan]")

            venv_python = self.config.project_root / self.config.venv_name / "bin" / "python"

            cmd = [
                str(venv_python), "-m", "uvicorn",
                self.config.app_module + ":app",
                "--host", host,
                "--port", str(port)
            ]

            if reload:
                cmd.append("--reload")

            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.config.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            await asyncio.sleep(3)

            # Check if server started successfully
            if self.server_process.poll() is None:
                console.print(f"[green]✅ Development server started successfully![/green]")
                console.print(f"Server URL: http://{host}:{port}")
                console.print(f"API Docs: http://{host}:{port}/docs")

                if open_browser:
                    webbrowser.open(f"http://{host}:{port}/docs")

                return True
            else:
                console.print("[red]❌ Failed to start development server[/red]")
                return False

        except Exception as e:
            console.print(f"[red]Server start error:[/red] {e}")
            return False

    async def stop_server(self) -> bool:
        """Stop development server"""
        try:
            if not self.server_process:
                console.print("[yellow]No server is running[/yellow]")
                return True

            console.print("[bold cyan]Stopping development server...[/bold cyan]")

            self.server_process.terminate()

            # Wait for process to terminate
            try:
                self.server_process.wait(timeout=10)
                console.print("[green]✅ Development server stopped successfully![/green]")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                console.print("[yellow]Server forcefully terminated[/yellow]")

            self.server_process = None
            return True

        except Exception as e:
            console.print(f"[red]Server stop error:[/red] {e}")
            return False

    async def restart_server(self, **kwargs) -> bool:
        """Restart development server"""
        await self.stop_server()
        await asyncio.sleep(2)
        return await self.start_server(**kwargs)


class DMLogDevTools:
    """Main dev tools orchestrator"""

    def __init__(self, config: DevToolsConfig):
        self.config = config
        self.formatter = CodeFormatter(config)
        self.test_runner = TestRunner(config)
        self.db_manager = DatabaseManager(config)
        self.cache_manager = CacheManager(config)
        self.log_viewer = LogViewer(config)
        self.perf_monitor = PerformanceMonitor(config)
        self.dev_server = DevelopmentServer(config)

    async def format_command(self, args) -> bool:
        """Handle format command"""
        check_only = args.check
        return await self.formatter.format_code(check_only=check_only)

    async def lint_command(self, args) -> bool:
        """Handle lint command"""
        fix = args.fix
        return await self.formatter.lint_code(fix=fix)

    async def test_command(self, args) -> bool:
        """Handle test command"""
        return await self.test_runner.run_tests(
            coverage_enabled=args.coverage,
            verbose=args.verbose,
            test_file=args.file
        )

    async def migrate_command(self, args) -> bool:
        """Handle migrate command"""
        if args.create:
            return await self.db_manager.create_migration(args.create)
        elif args.reset:
            return await self.db_manager.reset_database()
        else:
            return await self.db_manager.migrate_database(args.revision)

    async def cache_command(self, args) -> bool:
        """Handle cache command"""
        if args.clear:
            return await self.cache_manager.clear_redis_cache(args.pattern)
        elif args.info:
            await self.cache_manager.display_cache_info()
            return True
        return False

    async def logs_command(self, args) -> None:
        """Handle logs command"""
        if args.tail:
            level = LogLevel(args.level) if args.level else None
            await self.log_viewer.tail_logs(
                log_file=args.file,
                lines=args.lines,
                level=level
            )
        elif args.analyze:
            await self.log_viewer.analyze_logs(log_file=args.file)

    async def monitor_command(self, args) -> None:
        """Handle monitor command"""
        await self.perf_monitor.start_monitoring(interval=args.interval)

    async def server_command(self, args) -> bool:
        """Handle server command"""
        if args.action == "start":
            return await self.dev_server.start_server(
                host=args.host,
                port=args.port,
                reload=not args.no_reload,
                open_browser=not args.no_browser
            )
        elif args.action == "stop":
            return await self.dev_server.stop_server()
        elif args.action == "restart":
            return await self.dev_server.restart_server(
                host=args.host,
                port=args.port,
                reload=not args.no_reload,
                open_browser=not args.no_browser
            )
        return False

    async def status_command(self, args) -> None:
        """Handle status command"""
        table = Table(title="DMLog Development Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        # Check virtual environment
        venv_path = self.config.project_root / self.config.venv_name
        venv_status = "🟢 Ready" if venv_path.exists() else "🔴 Missing"
        table.add_row("Virtual Environment", venv_status, str(venv_path))

        # Check database
        try:
            conn = psycopg2.connect(
                host="localhost", port=5432,
                database="dmlog_db", user="dmlog_user",
                password="dmlog_password", connect_timeout=2
            )
            conn.close()
            db_status = "🟢 Connected"
        except:
            db_status = "🔴 Disconnected"
        table.add_row("Database", db_status, "PostgreSQL")

        # Check Redis
        try:
            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            redis_status = "🟢 Connected"
        except:
            redis_status = "🔴 Disconnected"
        table.add_row("Redis", redis_status, "Cache")

        # Check application server
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                app_status = "🟢 Running"
            else:
                app_status = "🟡 Error"
        except:
            app_status = "🔴 Stopped"
        table.add_row("Application", app_status, "FastAPI Server")

        # Check Docker services
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                docker_status = "🟢 Running"
            else:
                docker_status = "🔴 Error"
        except:
            docker_status = "🔴 Not Available"
        table.add_row("Docker Services", docker_status, "Containers")

        console.print(table)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="DMLog Development Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python dev_tools.py format                    # Format all code
    python dev_tools.py lint --fix               # Lint and fix code
    python dev_tools.py test --coverage          # Run tests with coverage
    python dev_tools.py migrate --create "Add users table"
    python dev_tools.py cache --clear            # Clear Redis cache
    python dev_tools.py logs --tail --lines 100  # Tail logs
    python dev_tools.py monitor                  # Start performance monitoring
    python dev_tools.py server start             # Start development server
    python dev_tools.py status                   # Show development status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Format command
    format_parser = subparsers.add_parser("format", help="Format code")
    format_parser.add_argument("--check", action="store_true", help="Check formatting without making changes")

    # Lint command
    lint_parser = subparsers.add_parser("lint", help="Lint code")
    lint_parser.add_argument("--fix", action="store_true", help="Automatically fix linting issues")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--coverage", action="store_true", default=True, help="Run with coverage")
    test_parser.add_argument("--no-coverage", dest="coverage", action="store_false", help="Run without coverage")
    test_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    test_parser.add_argument("--file", "-f", help="Run specific test file")

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Database migrations")
    migrate_group = migrate_parser.add_mutually_exclusive_group(required=True)
    migrate_group.add_argument("--create", help="Create new migration with message")
    migrate_group.add_argument("--revision", default="head", help="Migrate to specific revision")
    migrate_group.add_argument("--reset", action="store_true", help="Reset database")

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Cache management")
    cache_group = cache_parser.add_mutually_exclusive_group(required=True)
    cache_group.add_argument("--clear", action="store_true", help="Clear cache")
    cache_group.add_argument("--info", action="store_true", help="Show cache info")
    cache_parser.add_argument("--pattern", default="*", help="Cache key pattern to clear")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Log management")
    logs_group = logs_parser.add_mutually_exclusive_group(required=True)
    logs_group.add_argument("--tail", action="store_true", help="Tail log file")
    logs_group.add_argument("--analyze", action="store_true", help="Analyze log file")
    logs_parser.add_argument("--file", default="app.log", help="Log file name")
    logs_parser.add_argument("--lines", type=int, default=50, help="Number of lines to tail")
    logs_parser.add_argument("--level", choices=[level.value for level in LogLevel], help="Filter by log level")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Performance monitoring")
    monitor_parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in seconds")

    # Server command
    server_parser = subparsers.add_parser("server", help="Development server management")
    server_parser.add_argument("action", choices=["start", "stop", "restart"], help="Server action")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    server_parser.add_argument("--no-browser", action="store_true", help="Don't open browser")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show development status")

    return parser


async def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create configuration and dev tools
    config = DevToolsConfig()
    dev_tools = DMLogDevTools(config)

    # Handle commands
    try:
        if args.command == "format":
            success = await dev_tools.format_command(args)
        elif args.command == "lint":
            success = await dev_tools.lint_command(args)
        elif args.command == "test":
            success = await dev_tools.test_command(args)
        elif args.command == "migrate":
            success = await dev_tools.migrate_command(args)
        elif args.command == "cache":
            success = await dev_tools.cache_command(args)
        elif args.command == "logs":
            await dev_tools.logs_command(args)
            return
        elif args.command == "monitor":
            await dev_tools.monitor_command(args)
            return
        elif args.command == "server":
            success = await dev_tools.server_command(args)
        elif args.command == "status":
            await dev_tools.status_command(args)
            return
        else:
            console.print(f"[red]Unknown command: {args.command}[/red]")
            return

        if 'success' in locals() and not success:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())