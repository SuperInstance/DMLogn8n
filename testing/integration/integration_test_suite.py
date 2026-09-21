#!/usr/bin/env python3
"""
DMLogn8n Integration Test Suite
Main orchestration framework for comprehensive integration testing
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import importlib
import concurrent.futures
from dataclasses import dataclass, asdict
import yaml

# Add project root to path
sys.path.append('/home/activeloguser/DMLogn8n')

try:
    import pytest
    import aiohttp
    import websockets
    import psutil
    import docker
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from PIL import Image, ImageChops
    import redis
    import psycopg2
    from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install pytest aiohttp websockets psutil docker selenium pillow redis psycopg2-binary prometheus_client PyYAML")
    sys.exit(1)

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class TestPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    error: str = ""
    details: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}

@dataclass
class TestSuite:
    name: str
    description: str
    tests: List[str]
    priority: TestPriority
    timeout: int = 300
    parallel: bool = True

class IntegrationTestSuite:
    """
    Main integration test orchestrator
    """

    def __init__(self, config_path: str = None):
        self.config_path = config_path or '/home/activeloguser/DMLogn8n/testing/integration/config.yaml'
        self.config = self.load_config()
        self.logger = self.setup_logging()
        self.results: List[TestResult] = []
        self.test_suites: Dict[str, TestSuite] = {}
        self.metrics_registry = CollectorRegistry()

        # Prometheus metrics
        self.test_duration_gauge = Gauge(
            'integration_test_duration_seconds',
            'Integration test duration',
            ['test_name', 'status'],
            registry=self.metrics_registry
        )
        self.test_counter = Counter(
            'integration_tests_total',
            'Total integration tests run',
            ['status', 'suite'],
            registry=self.metrics_registry
        )

        # Test modules
        self.test_modules = {
            'system': None,
            'api': None,
            'ai': None,
            'database': None,
            'realtime': None,
            'load': None
        }

        # Environment setup
        self.setup_environment()

    def load_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        default_config = {
            'test_environment': 'development',
            'base_url': 'http://localhost:8000',
            'database_url': 'postgresql://dmlog:password@localhost:5432/dmlog_test',
            'redis_url': 'redis://localhost:6379/1',
            'ai_service_url': 'http://localhost:8080',
            'n8n_url': 'http://localhost:5678',
            'browser': 'chrome',
            'headless': True,
            'parallel_workers': 4,
            'test_data_cleanup': True,
            'reporting': {
                'html': True,
                'json': True,
                'prometheus': True,
                'prometheus_port': 9091
            },
            'suites': {
                'smoke': {
                    'priority': 'critical',
                    'timeout': 60,
                    'tests': ['basic_health', 'database_connection', 'api_availability']
                },
                'integration': {
                    'priority': 'high',
                    'timeout': 300,
                    'tests': ['user_journey', 'ai_integration', 'realtime_sync']
                },
                'performance': {
                    'priority': 'medium',
                    'timeout': 600,
                    'tests': ['load_testing', 'concurrent_users', 'response_times']
                },
                'regression': {
                    'priority': 'high',
                    'timeout': 240,
                    'tests': ['ui_regression', 'api_compatibility', 'data_integrity']
                }
            }
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        return default_config

    def setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('integration_test_suite')
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        # File handler
        os.makedirs('/home/activeloguser/DMLogn8n/testing/logs', exist_ok=True)
        file_handler = logging.FileHandler(
            '/home/activeloguser/DMLogn8n/testing/logs/integration_tests.log'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        return logger

    def setup_environment(self):
        """Setup test environment"""
        self.logger.info("Setting up test environment...")

        # Create necessary directories
        os.makedirs('/home/activeloguser/DMLogn8n/testing/screenshots', exist_ok=True)
        os.makedirs('/home/activeloguser/DMLogn8n/testing/reports', exist_ok=True)
        os.makedirs('/home/activeloguser/DMLogn8n/testing/test_data', exist_ok=True)

        # Start Prometheus metrics server if enabled
        if self.config['reporting']['prometheus']:
            try:
                start_http_server(
                    self.config['reporting']['prometheus_port'],
                    registry=self.metrics_registry
                )
                self.logger.info(f"Prometheus metrics server started on port {self.config['reporting']['prometheus_port']}")
            except Exception as e:
                self.logger.warning(f"Could not start Prometheus server: {e}")

        # Load test modules
        self.load_test_modules()

    def load_test_modules(self):
        """Dynamically load test modules"""
        module_configs = {
            'system': 'system_integration',
            'api': 'api_integration',
            'ai': 'ai_system_integration',
            'database': 'database_integration',
            'realtime': 'real_time_testing',
            'load': 'load_integration'
        }

        for key, module_name in module_configs.items():
            try:
                module_path = f'/home/activeloguser/DMLogn8n/testing/integration/{module_name}.py'
                if os.path.exists(module_path):
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.test_modules[key] = module
                    self.logger.info(f"Loaded test module: {module_name}")
                else:
                    self.logger.warning(f"Test module not found: {module_path}")
            except Exception as e:
                self.logger.error(f"Failed to load test module {module_name}: {e}")

    async def run_test_suite(self, suite_name: str) -> List[TestResult]:
        """Run a specific test suite"""
        if suite_name not in self.config['suites']:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite_config = self.config['suites'][suite_name]
        suite = TestSuite(
            name=suite_name,
            description=f"Integration test suite: {suite_name}",
            tests=suite_config['tests'],
            priority=TestPriority[suite_config['priority'].upper()],
            timeout=suite_config['timeout']
        )

        self.logger.info(f"Running test suite: {suite_name}")

        suite_results = []

        for test_name in suite.tests:
            result = await self.run_single_test(test_name, suite)
            suite_results.append(result)
            self.results.append(result)

            # Update metrics
            self.test_counter.labels(
                status=result.status.value,
                suite=suite_name
            ).inc()
            self.test_duration_gauge.labels(
                test_name=test_name,
                status=result.status.value
            ).set(result.duration)

        return suite_results

    async def run_single_test(self, test_name: str, suite: TestSuite) -> TestResult:
        """Run a single integration test"""
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )

        self.logger.info(f"Running test: {test_name}")

        start_time = time.time()

        try:
            # Find and execute the test
            test_method = self.find_test_method(test_name)
            if test_method:
                # Run test with timeout
                test_result = await asyncio.wait_for(
                    test_method(),
                    timeout=suite.timeout
                )

                if isinstance(test_result, TestResult):
                    result = test_result
                else:
                    result.status = TestStatus.PASSED
                    result.message = "Test completed successfully"
            else:
                result.status = TestStatus.SKIPPED
                result.message = f"Test method not found: {test_name}"

        except asyncio.TimeoutError:
            result.status = TestStatus.FAILED
            result.message = f"Test timed out after {suite.timeout} seconds"
            result.error = "Timeout"

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Test failed with error: {str(e)}"
            result.error = traceback.format_exc()
            self.logger.error(f"Test {test_name} failed: {e}")

        finally:
            result.duration = time.time() - start_time
            self.logger.info(f"Test {test_name} completed in {result.duration:.2f}s with status: {result.status.value}")

        return result

    def find_test_method(self, test_name: str) -> Optional[Callable]:
        """Find the appropriate test method"""
        test_mapping = {
            'basic_health': 'test_basic_health',
            'database_connection': 'test_database_connection',
            'api_availability': 'test_api_availability',
            'user_journey': 'test_complete_user_journey',
            'ai_integration': 'test_ai_integration',
            'realtime_sync': 'test_realtime_synchronization',
            'load_testing': 'test_load_scenarios',
            'concurrent_users': 'test_concurrent_users',
            'response_times': 'test_response_times',
            'ui_regression': 'test_ui_regression',
            'api_compatibility': 'test_api_compatibility',
            'data_integrity': 'test_data_integrity'
        }

        if test_name not in test_mapping:
            return None

        method_name = test_mapping[test_name]

        # Search in modules
        for module in self.test_modules.values():
            if module and hasattr(module, method_name):
                return getattr(module, method_name)

        # Check if it's a built-in method
        if hasattr(self, method_name):
            return getattr(self, method_name)

        return None

    async def test_basic_health(self) -> TestResult:
        """Basic health check of all services"""
        result = TestResult(
            name="basic_health",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            # Check main application
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config['base_url']}/health", timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"Main API health check failed: {response.status}")

            # Check database
            conn = psycopg2.connect(self.config['database_url'])
            conn.close()

            # Check Redis
            r = redis.from_url(self.config['redis_url'])
            r.ping()

            # Check N8N
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config['n8n_url']}/healthz", timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"N8N health check failed: {response.status}")

            result.status = TestStatus.PASSED
            result.message = "All services are healthy"

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Health check failed: {str(e)}"
            result.error = traceback.format_exc()

        return result

    async def run_all_tests(self, parallel: bool = True) -> Dict[str, List[TestResult]]:
        """Run all test suites"""
        self.logger.info("Starting comprehensive integration test run")

        all_results = {}

        if parallel:
            # Run suites in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['parallel_workers']) as executor:
                loop = asyncio.get_event_loop()
                futures = []

                for suite_name in self.config['suites'].keys():
                    future = loop.run_in_executor(executor, self.run_test_suite, suite_name)
                    futures.append((suite_name, future))

                for suite_name, future in futures:
                    try:
                        results = await future
                        all_results[suite_name] = results
                    except Exception as e:
                        self.logger.error(f"Test suite {suite_name} failed: {e}")
                        all_results[suite_name] = [TestResult(
                            name=suite_name,
                            status=TestStatus.ERROR,
                            duration=0.0,
                            message=f"Suite failed: {str(e)}",
                            error=traceback.format_exc()
                        )]
        else:
            # Run suites sequentially
            for suite_name in self.config['suites'].keys():
                try:
                    results = await self.run_test_suite(suite_name)
                    all_results[suite_name] = results
                except Exception as e:
                    self.logger.error(f"Test suite {suite_name} failed: {e}")
                    all_results[suite_name] = [TestResult(
                        name=suite_name,
                        status=TestStatus.ERROR,
                        duration=0.0,
                        message=f"Suite failed: {str(e)}",
                        error=traceback.format_exc()
                    )]

        # Generate reports
        await self.generate_reports(all_results)

        return all_results

    async def generate_reports(self, all_results: Dict[str, List[TestResult]]):
        """Generate comprehensive test reports"""
        self.logger.info("Generating test reports...")

        # JSON Report
        if self.config['reporting']['json']:
            await self.generate_json_report(all_results)

        # HTML Report
        if self.config['reporting']['html']:
            await self.generate_html_report(all_results)

        # Summary to console
        self.print_summary(all_results)

    async def generate_json_report(self, all_results: Dict[str, List[TestResult]]):
        """Generate JSON test report"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.config['test_environment'],
            'summary': self.calculate_summary(all_results),
            'results': {}
        }

        for suite_name, results in all_results.items():
            report_data['results'][suite_name] = [
                {
                    'name': result.name,
                    'status': result.status.value,
                    'duration': result.duration,
                    'message': result.message,
                    'error': result.error,
                    'timestamp': result.timestamp.isoformat(),
                    'details': result.details
                }
                for result in results
            ]

        report_path = f"/home/activeloguser/DMLogn8n/testing/reports/integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"JSON report generated: {report_path}")

    async def generate_html_report(self, all_results: Dict[str, List[TestResult]]):
        """Generate HTML test report"""
        summary = self.calculate_summary(all_results)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>DMLogn8n Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
        .passed {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .skipped {{ background-color: #fff3cd; }}
        .error {{ background-color: #f5c6cb; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background-color: #f8f9fa; padding: 15px; font-weight: bold; }}
        .test {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .test:last-child {{ border-bottom: none; }}
        .status {{ font-weight: bold; padding: 2px 8px; border-radius: 3px; }}
        .duration {{ color: #666; font-size: 0.9em; }}
        .error {{ background-color: #f8d7da; padding: 10px; margin: 10px 0; border-radius: 3px; font-family: monospace; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>DMLogn8n Integration Test Report</h1>
        <p><strong>Environment:</strong> {self.config['test_environment']}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="metric passed">
            <h3>{summary['passed']}</h3>
            <p>Passed</p>
        </div>
        <div class="metric failed">
            <h3>{summary['failed']}</h3>
            <p>Failed</p>
        </div>
        <div class="metric skipped">
            <h3>{summary['skipped']}</h3>
            <p>Skipped</p>
        </div>
        <div class="metric error">
            <h3>{summary['error']}</h3>
            <p>Errors</p>
        </div>
        <div class="metric">
            <h3>{summary['total_duration']:.2f}s</h3>
            <p>Total Duration</p>
        </div>
    </div>
"""

        for suite_name, results in all_results.items():
            html_content += f"""
    <div class="suite">
        <div class="suite-header">{suite_name} Test Suite</div>
"""
            for result in results:
                status_class = result.status.value
                html_content += f"""
        <div class="test">
            <span class="status {status_class}">{result.status.value.upper()}</span>
            <strong>{result.name}</strong>
            <span class="duration">({result.duration:.2f}s)</span>
            <br>
            <small>{result.message}</small>
"""
                if result.error:
                    html_content += f"""
            <div class="error">{result.error}</div>
"""
                html_content += "        </div>\n"
            html_content += "    </div>\n"

        html_content += """
</body>
</html>
"""

        report_path = f"/home/activeloguser/DMLogn8n/testing/reports/integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        with open(report_path, 'w') as f:
            f.write(html_content)

        self.logger.info(f"HTML report generated: {report_path}")

    def calculate_summary(self, all_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Calculate test summary statistics"""
        total = passed = failed = skipped = error = 0
        total_duration = 0.0

        for results in all_results.values():
            for result in results:
                total += 1
                total_duration += result.duration

                if result.status == TestStatus.PASSED:
                    passed += 1
                elif result.status == TestStatus.FAILED:
                    failed += 1
                elif result.status == TestStatus.SKIPPED:
                    skipped += 1
                elif result.status == TestStatus.ERROR:
                    error += 1

        success_rate = (passed / total * 100) if total > 0 else 0

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'error': error,
            'success_rate': success_rate,
            'total_duration': total_duration
        }

    def print_summary(self, all_results: Dict[str, List[TestResult]]):
        """Print test summary to console"""
        summary = self.calculate_summary(all_results)

        print("\n" + "="*60)
        print("DMLOGN8N INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total']}")
        print(f"Passed: {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)")
        print(f"Failed: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
        print(f"Skipped: {summary['skipped']} ({summary['skipped']/summary['total']*100:.1f}%)")
        print(f"Errors: {summary['error']} ({summary['error']/summary['total']*100:.1f}%)")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print("="*60)

        # Print failed tests
        failed_tests = []
        for suite_name, results in all_results.items():
            for result in results:
                if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    failed_tests.append((suite_name, result))

        if failed_tests:
            print("\nFAILED TESTS:")
            print("-"*60)
            for suite_name, result in failed_tests:
                print(f"[{suite_name}] {result.name}: {result.message}")

        print()

    def cleanup(self):
        """Cleanup test resources"""
        self.logger.info("Cleaning up test resources...")

        # Cleanup test data if enabled
        if self.config['test_data_cleanup']:
            try:
                # Database cleanup
                conn = psycopg2.connect(self.config['database_url'])
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM test_users WHERE created_at > NOW() - INTERVAL '1 hour'")
                    cursor.execute("DELETE FROM test_sessions WHERE created_at > NOW() - INTERVAL '1 hour'")
                conn.close()

                # Redis cleanup
                r = redis.from_url(self.config['redis_url'])
                for key in r.scan_iter("test:*"):
                    r.delete(key)

                self.logger.info("Test data cleanup completed")
            except Exception as e:
                self.logger.warning(f"Test data cleanup failed: {e}")

async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='DMLogn8n Integration Test Suite')
    parser.add_argument('--suite', choices=['smoke', 'integration', 'performance', 'regression'],
                       help='Specific test suite to run')
    parser.add_argument('--parallel', action='store_true', default=True, help='Run tests in parallel')
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--list', action='store_true', help='List available tests')

    args = parser.parse_args()

    test_suite = IntegrationTestSuite(args.config)

    if args.list:
        print("Available test suites:")
        for suite_name, suite_config in test_suite.config['suites'].items():
            print(f"  {suite_name}: {suite_config['tests']}")
        return

    try:
        if args.suite:
            results = await test_suite.run_test_suite(args.suite)
            await test_suite.generate_reports({args.suite: results})
        else:
            results = await test_suite.run_all_tests(args.parallel)
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
    except Exception as e:
        print(f"Test run failed: {e}")
        traceback.print_exc()
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main())