#!/usr/bin/env python3
"""
DMLogn8n Load Testing Framework - Main Runner
Comprehensive load testing orchestration for multi-agent platform
"""

import asyncio
import logging
import signal
import sys
import time
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

# Import our modules
from scenarios.agent_simulation import AgentSimulationScenario
from scenarios.user_journey import UserJourneyScenario
from scenarios.combat_stress import CombatStressScenario
from scenarios.dialogue_load import DialogueLoadScenario
from generators.agent_generator import AgentLoadGenerator
from generators.user_generator import UserLoadGenerator
from generators.data_generator import TestDataGenerator
from metrics.collector import MetricsCollector
from metrics.analyzer import PerformanceAnalyzer
from metrics.comparator import BaselineComparator
from reports.html_reporter import HTMLReporter
from reports.json_reporter import JSONReporter
from reports.dashboard import PerformanceDashboard

console = Console()

@dataclass
class LoadTestConfig:
    """Configuration for load test execution"""
    name: str
    scenario: str
    target_url: str
    duration: int  # seconds
    users: int
    spawn_rate: int
    ramp_up: int
    ramp_down: int
    think_time: float
    timeout: int
    headers: Dict[str, str]
    auth: Optional[Dict[str, str]]
    test_data: Dict[str, Any]
    monitoring: Dict[str, Any]
    reporting: Dict[str, Any]

@dataclass
class TestResult:
    """Results from a load test execution"""
    test_name: str
    scenario: str
    start_time: datetime
    end_time: datetime
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    throughput: float
    error_rate: float
    errors: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
    baseline_comparison: Optional[Dict[str, Any]]

class LoadTestRunner:
    """Main load testing orchestration system"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = self._setup_logging()
        self.metrics_collector = MetricsCollector()
        self.performance_analyzer = PerformanceAnalyzer()
        self.baseline_comparator = BaselineComparator()
        self.test_results: List[TestResult] = []
        self.running_tests: Dict[str, asyncio.Task] = {}
        self.shutdown_event = asyncio.Event()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger("LoadTestRunner")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()

    async def load_config(self) -> List[LoadTestConfig]:
        """Load test configurations from YAML files"""
        configs = []

        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            for test_config in config_data.get('tests', []):
                config = LoadTestConfig(**test_config)
                configs.append(config)

        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise

        return configs

    def get_scenario_class(self, scenario_name: str):
        """Get scenario class by name"""
        scenarios = {
            'agent_simulation': AgentSimulationScenario,
            'user_journey': UserJourneyScenario,
            'combat_stress': CombatStressScenario,
            'dialogue_load': DialogueLoadScenario
        }

        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        return scenarios[scenario_name]

    async def run_single_test(self, config: LoadTestConfig) -> TestResult:
        """Run a single load test"""
        self.logger.info(f"Starting load test: {config.name}")

        try:
            # Initialize scenario
            scenario_class = self.get_scenario_class(config.scenario)
            scenario = scenario_class(config, self.metrics_collector)

            # Start metrics collection
            await self.metrics_collector.start_collection(config)

            # Start system monitoring
            system_monitor_task = asyncio.create_task(
                self._monitor_system_resources(config)
            )

            # Execute the test
            start_time = datetime.now(timezone.utc)

            test_result = await scenario.execute()

            end_time = datetime.now(timezone.utc)

            # Stop monitoring
            system_monitor_task.cancel()
            try:
                await system_monitor_task
            except asyncio.CancelledError:
                pass

            await self.metrics_collector.stop_collection()

            # Analyze results
            test_result.start_time = start_time
            test_result.end_time = end_time
            test_result.duration = (end_time - start_time).total_seconds()
            test_result.system_metrics = await self.metrics_collector.get_system_metrics()

            # Compare with baseline if available
            test_result.baseline_comparison = await self.baseline_comparator.compare(
                config.name, test_result
            )

            self.logger.info(f"Completed load test: {config.name}")
            return test_result

        except Exception as e:
            self.logger.error(f"Failed to run test {config.name}: {e}")
            # Return failed result
            return TestResult(
                test_name=config.name,
                scenario=config.scenario,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration=0,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                throughput=0,
                error_rate=100.0,
                errors=[{"error": str(e), "type": type(e).__name__}],
                metrics={},
                system_metrics={},
                baseline_comparison=None
            )

    async def _monitor_system_resources(self, config: LoadTestConfig):
        """Monitor system resources during test"""
        import psutil

        while not self.shutdown_event.is_set():
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)

                # Memory usage
                memory = psutil.virtual_memory()

                # Disk usage
                disk = psutil.disk_usage('/')

                # Network I/O
                network = psutil.net_io_counters()

                # Process information
                process = psutil.Process()

                system_metrics = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100,
                    'disk_used_gb': disk.used / (1024**3),
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv,
                    'process_cpu_percent': process.cpu_percent(),
                    'process_memory_mb': process.memory_info().rss / (1024**2),
                    'process_threads': process.num_threads(),
                    'process_fds': process.num_fds()
                }

                await self.metrics_collector.record_system_metric(system_metrics)

                # Check if we should stop due to resource limits
                if cpu_percent > 95 or memory.percent > 95:
                    self.logger.warning(
                        f"High resource usage - CPU: {cpu_percent}%, Memory: {memory.percent}%"
                    )

                await asyncio.sleep(5)  # Collect every 5 seconds

            except Exception as e:
                self.logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(10)

    async def run_concurrent_tests(self, configs: List[LoadTestConfig], max_concurrent: int = 3):
        """Run multiple tests concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(config):
            async with semaphore:
                return await self.run_single_test(config)

        tasks = [run_with_semaphore(config) for config in configs]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:

            task_progress = progress.add_task(
                f"Running {len(configs)} load tests...", total=len(configs)
            )

            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    self.test_results.append(result)
                    progress.advance(task_progress)

                    # Display summary
                    self._display_test_summary(result)

                except Exception as e:
                    self.logger.error(f"Test execution failed: {e}")
                    progress.advance(task_progress)

    def _display_test_summary(self, result: TestResult):
        """Display a summary of test results"""
        table = Table(title=f"Test Summary: {result.test_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Duration", f"{result.duration:.2f}s")
        table.add_row("Total Requests", str(result.total_requests))
        table.add_row("Success Rate", f"{(1 - result.error_rate) * 100:.2f}%")
        table.add_row("Avg Response Time", f"{result.avg_response_time:.2f}ms")
        table.add_row("95th Percentile", f"{result.p95_response_time:.2f}ms")
        table.add_row("Requests/sec", f"{result.requests_per_second:.2f}")
        table.add_row("Throughput", f"{result.throughput:.2f} MB/s")

        console.print(table)

    async def generate_reports(self):
        """Generate comprehensive reports"""
        if not self.test_results:
            self.logger.warning("No test results to generate reports from")
            return

        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate HTML report
        html_reporter = HTMLReporter()
        await html_reporter.generate_report(self.test_results, reports_dir / f"load_test_report_{timestamp}.html")

        # Generate JSON report
        json_reporter = JSONReporter()
        await json_reporter.generate_report(self.test_results, reports_dir / f"load_test_data_{timestamp}.json")

        # Generate performance dashboard
        dashboard = PerformanceDashboard()
        await dashboard.generate_dashboard(self.test_results, reports_dir / f"dashboard_{timestamp}.html")

        self.logger.info(f"Reports generated in {reports_dir}")

    def display_final_summary(self):
        """Display final summary of all tests"""
        if not self.test_results:
            console.print("[red]No tests were completed successfully[/red]")
            return

        table = Table(title="Load Test Execution Summary")
        table.add_column("Test Name", style="cyan")
        table.add_column("Scenario", style="magenta")
        table.add_column("Duration", style="blue")
        table.add_column("Requests", style="green")
        table.add_column("Success Rate", style="yellow")
        table.add_column("Avg Response", style="red")
        table.add_column("95th Percentile", style="purple")

        for result in self.test_results:
            success_rate = (1 - result.error_rate) * 100
            table.add_row(
                result.test_name,
                result.scenario,
                f"{result.duration:.1f}s",
                str(result.total_requests),
                f"{success_rate:.1f}%",
                f"{result.avg_response_time:.1f}ms",
                f"{result.p95_response_time:.1f}ms"
            )

        console.print(table)

        # Performance insights
        console.print("\n[bold green]Performance Insights:[/bold green]")

        # Best performing test
        best_test = min(self.test_results, key=lambda x: x.avg_response_time)
        console.print(f"• Best Performance: {best_test.test_name} "
                     f"(Avg: {best_test.avg_response_time:.1f}ms)")

        # Highest throughput
        throughput_test = max(self.test_results, key=lambda x: x.requests_per_second)
        console.print(f"• Highest Throughput: {throughput_test.test_name} "
                     f"({throughput_test.requests_per_second:.1f} req/s)")

        # Issues detected
        failed_tests = [r for r in self.test_results if r.error_rate > 5]
        if failed_tests:
            console.print(f"[red]• {len(failed_tests)} tests had error rates above 5%[/red]")

        slow_tests = [r for r in self.test_results if r.p95_response_time > 5000]
        if slow_tests:
            console.print(f"[yellow]• {len(slow_tests)} tests had 95th percentile above 5s[/yellow]")

    async def run(self, concurrent: bool = False, max_concurrent: int = 3):
        """Main execution method"""
        try:
            # Load configurations
            configs = await self.load_config()

            if not configs:
                console.print("[red]No test configurations found[/red]")
                return

            console.print(f"[green]Loaded {len(configs)} test configurations[/green]")

            # Run tests
            if concurrent:
                await self.run_concurrent_tests(configs, max_concurrent)
            else:
                for config in configs:
                    if self.shutdown_event.is_set():
                        break

                    result = await self.run_single_test(config)
                    self.test_results.append(result)
                    self._display_test_summary(result)

            # Generate reports
            await self.generate_reports()

            # Display final summary
            self.display_final_summary()

        except KeyboardInterrupt:
            console.print("\n[yellow]Load testing interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Load testing failed: {e}[/red]")
            self.logger.error(f"Load testing failed: {e}", exc_info=True)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DMLogn8n Load Testing Framework")
    parser.add_argument("config", help="Path to test configuration file")
    parser.add_argument("--concurrent", action="store_true",
                       help="Run tests concurrently")
    parser.add_argument("--max-concurrent", type=int, default=3,
                       help="Maximum concurrent tests (default: 3)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run load test runner
    runner = LoadTestRunner(args.config)

    try:
        asyncio.run(runner.run(args.concurrent, args.max_concurrent))
    except KeyboardInterrupt:
        console.print("\n[yellow]Load testing stopped by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()