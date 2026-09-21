#!/usr/bin/env python3
"""
DMLogn8n Integration Testing - Example Usage
This file demonstrates how to use the integration testing system
"""

import asyncio
import json
import logging
from datetime import datetime

# Import test modules
from integration_test_suite import IntegrationTestSuite
from system_integration import SystemIntegrationTests
from api_integration import APIIntegrationTests
from ai_system_integration import AISystemIntegrationTests
from database_integration import DatabaseIntegrationTests
from real_time_testing import RealTimeTesting
from load_integration import LoadIntegrationTests
from debug_tools import DebugTools

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

async def example_basic_usage():
    """Example: Basic usage of the integration test suite"""
    print_separator("BASIC INTEGRATION TEST SUITE USAGE")

    # Initialize the test suite
    test_suite = IntegrationTestSuite()

    # Run a specific test suite
    logger.info("Running smoke tests...")
    results = await test_suite.run_test_suite("smoke")

    # Print results
    print(f"Smoke test results: {len(results)} tests executed")
    for result in results:
        print(f"  - {result.name}: {result.status.value} ({result.duration:.2f}s)")
        if result.status.value == "failed":
            print(f"    Error: {result.message}")

    # Cleanup
    test_suite.cleanup()

async def example_system_integration():
    """Example: System integration testing"""
    print_separator("SYSTEM INTEGRATION TESTING")

    config = {
        'base_url': 'http://localhost:8000',
        'headless': True,
        'browser_timeout': 30
    }

    system_tests = SystemIntegrationTests(config)

    # Test complete user journey
    logger.info("Testing complete user journey...")
    result = await system_tests.test_complete_user_journey()

    print(f"User journey test: {result.status.value}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Message: {result.message}")

    if result.details:
        print("Journey steps:")
        for step, step_result in result.details.items():
            status = "✓" if step_result else "✗"
            print(f"  {status} {step}")

    system_tests.cleanup()

async def example_api_testing():
    """Example: API integration testing"""
    print_separator("API INTEGRATION TESTING")

    config = {
        'base_url': 'http://localhost:8000',
        'api_key': 'test_api_key'
    }

    api_tests = APIIntegrationTests(config)

    # Test authentication endpoints
    logger.info("Testing authentication endpoints...")
    result = await api_tests.test_authentication_endpoints()

    print(f"Authentication test: {result.status.value}")
    print(f"Success rate: {result.details.get('success_rate', 0):.1%}")

    if result.details:
        print("Auth endpoints tested:")
        for endpoint, endpoint_result in result.details.items():
            status = "✓" if endpoint_result.get('success') else "✗"
            print(f"  {status} {endpoint}")

async def example_ai_testing():
    """Example: AI system integration testing"""
    print_separator("AI SYSTEM INTEGRATION TESTING")

    config = {
        'base_url': 'http://localhost:8000',
        'ai_service_url': 'http://localhost:8080'
    }

    ai_tests = AISystemIntegrationTests(config)

    # Test AI integration
    logger.info("Testing AI integration...")
    result = await ai_tests.test_ai_integration()

    print(f"AI integration test: {result.status.value}")
    print(f"Success rate: {result.details.get('success_rate', 0):.1%}")

    if result.details and 'tests' in result.details:
        print("AI components tested:")
        for component, comp_result in result.details['tests'].items():
            status = "✓" if comp_result.get('success') else "✗"
            print(f"  {status} {component}")

async def example_database_testing():
    """Example: Database integration testing"""
    print_separator("DATABASE INTEGRATION TESTING")

    config = {
        'database_url': 'postgresql://dmlog:password@localhost:5432/dmlog_test',
        'redis_url': 'redis://localhost:6379/1'
    }

    db_tests = DatabaseIntegrationTests(config)

    # Test database connections
    logger.info("Testing database connections...")
    result = await db_tests.test_database_connection()

    print(f"Database connection test: {result.status.value}")

    if result.details:
        print("Databases tested:")
        for db_name, db_result in result.details.items():
            status = "✓" if db_result.get('connected') else "✗"
            print(f"  {status} {db_name}")

    # Cleanup test data
    db_tests.cleanup_test_data()

async def example_realtime_testing():
    """Example: Real-time features testing"""
    print_separator("REAL-TIME FEATURES TESTING")

    config = {
        'base_url': 'http://localhost:8000',
        'websocket_url': 'ws://localhost:8001'
    }

    realtime_tests = RealTimeTesting(config)

    # Test WebSocket connectivity
    logger.info("Testing WebSocket connectivity...")
    result = await realtime_tests.test_websocket_connectivity()

    print(f"WebSocket test: {result.status.value}")
    print(f"Success rate: {result.details.get('success_rate', 0):.1%}")

    # Test message broadcasting
    logger.info("Testing message broadcasting...")
    result = await realtime_tests.test_message_broadcast()

    print(f"Message broadcasting: {result.status.value}")
    print(f"Clients successful: {result.details.get('successful_clients', 0)}/{result.details.get('num_clients', 0)}")

    realtime_tests.cleanup()

async def example_load_testing():
    """Example: Load testing"""
    print_separator("LOAD TESTING")

    config = {
        'base_url': 'http://localhost:8000',
        'websocket_url': 'ws://localhost:8001'
    }

    load_tests = LoadIntegrationTests(config)

    # Test light load
    logger.info("Testing system under light load...")
    result = await load_tests.test_light_load()

    print(f"Light load test: {result.status.value}")
    if result.details and 'performance' in result.details:
        perf = result.details['performance']
        print(f"  Requests: {perf.get('total_requests', 0)}")
        print(f"  Avg response time: {perf.get('avg_response_time', 0):.3f}s")
        print(f"  Error rate: {perf.get('error_rate', 0):.2%}")
        print(f"  Throughput: {perf.get('throughput', 0):.1f} req/s")

async def example_debug_tools():
    """Example: Debug tools usage"""
    print_separator("DEBUG TOOLS")

    config = {
        'base_url': 'http://localhost:8000',
        'database_url': 'postgresql://dmlog:password@localhost:5432/dmlog_test',
        'redis_url': 'redis://localhost:6379/1'
    }

    debug_tools = DebugTools(config)

    # Generate system overview
    logger.info("Collecting system overview...")
    overview = await debug_tools.collect_system_overview()

    print(f"System status: {overview.get('status', 'unknown')}")
    if overview.get('system'):
        sys_info = overview['system']
        print(f"  Hostname: {sys_info.get('hostname', 'Unknown')}")
        print(f"  Platform: {sys_info.get('platform', 'Unknown')}")

    if overview.get('cpu'):
        cpu_info = overview['cpu']
        print(f"  CPU usage: {cpu_info.get('usage_percent', 0)}%")

    if overview.get('memory'):
        mem_info = overview['memory']
        print(f"  Memory usage: {mem_info.get('percent', 0)}%")

    # Check service status
    logger.info("Checking service status...")
    service_status = await debug_tools.check_service_status()

    print(f"Overall health: {service_status['summary'].get('overall_health', 'unknown')}")
    if 'services' in service_status:
        for service_name, service_info in service_status['services'].items():
            status = service_info.get('status', 'unknown')
            print(f"  {service_name}: {status}")

async def example_custom_test():
    """Example: Creating a custom test"""
    print_separator("CUSTOM TEST EXAMPLE")

    # This example shows how to create a custom integration test
    from integration_test_suite import TestResult, TestStatus

    async def test_custom_feature():
        """Custom test example"""
        result = TestResult(
            name="custom_feature_test",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            # Your custom test logic here
            logger.info("Running custom feature test...")

            # Example: Test a custom API endpoint
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/custom", timeout=10) as response:
                    if response.status == 200:
                        result.status = TestStatus.PASSED
                        result.message = "Custom feature test passed"
                    else:
                        result.status = TestStatus.FAILED
                        result.message = f"Custom feature test failed: HTTP {response.status}"

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Custom feature test error: {str(e)}"
            logger.error(f"Custom test failed: {e}")

        return result

    # Run the custom test
    result = await test_custom_feature()
    print(f"Custom test result: {result.status.value}")
    print(f"Message: {result.message}")

async def example_comprehensive_test():
    """Example: Running a comprehensive test suite"""
    print_separator("COMPREHENSIVE TEST SUITE")

    # Initialize the main test suite
    test_suite = IntegrationTestSuite()

    # Run all test suites
    logger.info("Running comprehensive test suite...")
    all_results = await test_suite.run_all_tests(parallel=False)

    # Print summary
    print("\nTest Suite Summary:")
    print("-" * 30)

    total_passed = 0
    total_failed = 0
    total_errors = 0

    for suite_name, results in all_results.items():
        suite_passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        suite_failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        suite_errors = sum(1 for r in results if r.status == TestStatus.ERROR)

        total_passed += suite_passed
        total_failed += suite_failed
        total_errors += suite_errors

        print(f"{suite_name}:")
        print(f"  Passed: {suite_passed}")
        print(f"  Failed: {suite_failed}")
        print(f"  Errors:  {suite_errors}")

    print("-" * 30)
    print(f"TOTAL: {len(all_results)} suites")
    print(f"Passed: {total_passed} tests")
    print(f"Failed: {total_failed} tests")
    print(f"Errors: {total_errors} tests")

    # Generate reports
    await test_suite.generate_reports(all_results)

    # Cleanup
    test_suite.cleanup()

async def main():
    """Main example function"""
    print_separator("DMLOGN8N INTEGRATION TESTING EXAMPLES")
    print("This file demonstrates various ways to use the integration testing system.")
    print("Note: Some examples may fail if required services are not running.")
    print()

    try:
        # Run examples (comment out those you don't want to run)
        await example_basic_usage()
        await example_system_integration()
        await example_api_testing()
        await example_ai_testing()
        await example_database_testing()
        await example_realtime_testing()
        await example_load_testing()
        await example_debug_tools()
        await example_custom_test()
        await example_comprehensive_test()

    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")
        logger.exception("Error in examples")

if __name__ == "__main__":
    print("DMLogn8n Integration Testing Examples")
    print("Make sure you have run './setup.sh' first!")
    print()

    # Run the examples
    asyncio.run(main())