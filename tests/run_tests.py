#!/usr/bin/env python3
"""
Test runner script for DMLogn8n testing framework.
Provides convenient commands for running different test scenarios.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description="Running command"):
    """Run a command and handle the result."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="DMLogn8n Test Runner")
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "e2e", "performance", "parallel",
            "load", "stress", "soak", "spike", "all", "quick", "full"
        ],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks"
    )
    parser.add_argument(
        "--no-slow",
        action="store_true",
        help="Skip slow tests"
    )

    args = parser.parse_args()

    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]

    # Add basic options
    if args.verbose:
        pytest_cmd.append("-v")
    else:
        pytest_cmd.append("-q")

    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])

    # Add coverage
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])

    # Add HTML report
    if args.html_report:
        pytest_cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Add benchmark
    if args.benchmark:
        pytest_cmd.extend(["--benchmark-only", "--benchmark-sort=mean"])

    # Skip slow tests
    if args.no_slow:
        pytest_cmd.extend(["-m", "not slow"])

    # Determine which tests to run
    test_path = "tests"
    marker = None

    if args.test_type == "unit":
        marker = "unit"
    elif args.test_type == "integration":
        marker = "integration"
    elif args.test_type == "e2e":
        marker = "e2e"
    elif args.test_type == "performance":
        marker = "performance"
    elif args.test_type == "parallel":
        marker = "parallel"
    elif args.test_type == "load":
        marker = "load"
    elif args.test_type == "stress":
        marker = "stress"
    elif args.test_type == "soak":
        marker = "soak"
    elif args.test_type == "spike":
        marker = "spike"
    elif args.test_type == "all":
        marker = None
    elif args.test_type == "quick":
        marker = "unit and not slow"
    elif args.test_type == "full":
        marker = None
        # For full tests, don't skip anything

    if marker:
        pytest_cmd.extend(["-m", marker])

    # Add test path
    pytest_cmd.append(test_path)

    # Set environment variables for testing
    env = os.environ.copy()
    env["TEST_ENVIRONMENT"] = "testing"
    env["TEST_LOG_LEVEL"] = "INFO" if args.verbose else "WARNING"

    # Run the tests
    print(f"Running {args.test_type} tests...")
    success = run_command(pytest_cmd, f"Running {args.test_type} tests")

    if success:
        print(f"\n✅ All {args.test_type} tests passed!")

        # Show additional reports
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")

        if args.html_report:
            print("\n📄 HTML report generated in test_report.html")

        if args.benchmark:
            print("\n📈 Benchmark results available in .benchmarks/")
    else:
        print(f"\n❌ {args.test_type} tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()