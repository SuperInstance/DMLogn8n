#!/usr/bin/env python3
"""
DMLog Test Runner

A comprehensive test runner script that can execute different test suites
with various configurations and generate reports.
"""

import argparse
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil


class DMLogTestRunner:
    """Comprehensive test runner for DMLog"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.source_dir = self.project_root / "source_code"
        self.results_dir = self.project_root / "test_results"
        self.coverage_dir = self.project_root / "htmlcov"

        # Create results directories
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd or self.project_root,
            capture_output=True,
            text=True
        )
        return result

    def run_unit_tests(self, coverage: bool = True, verbose: bool = False) -> bool:
        """Run unit tests"""
        print("\n=== Running Unit Tests ===")

        cmd = ["python", "-m", "pytest", "tests/unit/"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend([
                "--cov=source_code",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=xml",
                f"--cov-fail-under={os.getenv('COVERAGE_THRESHOLD', '85')}"
            ])

        cmd.extend([
            "--junitxml=test_results/unit_tests.xml",
            "--tb=short"
        ])

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests"""
        print("\n=== Running Integration Tests ===")

        cmd = [
            "python", "-m", "pytest", "tests/integration/",
            "-v" if verbose else "",
            "--junitxml=test_results/integration_tests.xml",
            "--tb=short"
        ]

        # Filter out empty arguments
        cmd = [arg for arg in cmd if arg]

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def run_e2e_tests(self, browser: str = "chromium", headless: bool = True) -> bool:
        """Run end-to-end tests"""
        print("\n=== Running E2E Tests ===")

        # Check if Playwright is available
        try:
            result = self.run_command(["python", "-c", "import playwright"])
            if result.returncode != 0:
                print("Playwright not installed. Install with: pip install playwright")
                return False
        except:
            print("Playwright not available. Skipping E2E tests.")
            return False

        cmd = [
            "python", "-m", "pytest", "tests/e2e/",
            "--browser", browser,
            "--junitxml=test_results/e2e_tests.xml",
            "--tb=short"
        ]

        if headless:
            cmd.append("--headed=False")

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def run_security_tests(self) -> bool:
        """Run security tests"""
        print("\n=== Running Security Tests ===")

        cmd = [
            "python", "-m", "pytest", "tests/security/",
            "-v",
            "--junitxml=test_results/security_tests.xml",
            "--tb=short"
        ]

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def run_load_tests(self, scenario: str = "moderate", duration: int = 300) -> bool:
        """Run load tests"""
        print(f"\n=== Running Load Tests: {scenario} ===")

        # Check if Locust is available
        try:
            result = self.run_command(["python", "-c", "import locust"])
            if result.returncode != 0:
                print("Locust not installed. Install with: pip install locust")
                return False
        except:
            print("Locust not available. Skipping load tests.")
            return False

        locust_file = self.tests_dir / "load" / "locustfile.py"
        if not locust_file.exists():
            print(f"Locust file not found: {locust_file}")
            return False

        cmd = [
            "python", "-m", "locust",
            "-f", str(locust_file),
            "--headless",
            "--users", self._get_user_count(scenario),
            "--spawn-rate", self._get_spawn_rate(scenario),
            "--run-time", f"{duration}s",
            "--html", f"test_results/load_test_{scenario}.html",
            "--csv", f"test_results/load_test_{scenario}"
        ]

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def _get_user_count(self, scenario: str) -> str:
        """Get user count for load test scenario"""
        scenario_counts = {
            "light": "10",
            "moderate": "50",
            "heavy": "200",
            "stress": "500"
        }
        return scenario_counts.get(scenario, "50")

    def _get_spawn_rate(self, scenario: str) -> str:
        """Get spawn rate for load test scenario"""
        scenario_rates = {
            "light": "2",
            "moderate": "5",
            "heavy": "10",
            "stress": "50"
        }
        return scenario_rates.get(scenario, "5")

    def run_performance_tests(self) -> bool:
        """Run performance benchmarks"""
        print("\n=== Running Performance Tests ===")

        cmd = [
            "python", "-m", "pytest", "tests/performance/",
            "--benchmark-only",
            "--benchmark-json=test_results/performance.json",
            "--benchmark-html=test_results/performance.html"
        ]

        result = self.run_command(cmd)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n=== Generating Test Report ===")

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "coverage": {},
            "test_suites": {}
        }

        # Parse JUnit XML files
        junit_files = [
            "test_results/unit_tests.xml",
            "test_results/integration_tests.xml",
            "test_results/security_tests.xml",
            "test_results/e2e_tests.xml"
        ]

        for junit_file in junit_files:
            if (self.project_root / junit_file).exists():
                suite_results = self._parse_junit_xml(self.project_root / junit_file)
                report["test_suites"][junit_file] = suite_results
                report["total_tests"] += suite_results["total"]
                report["passed_tests"] += suite_results["passed"]
                report["failed_tests"] += suite_results["failed"]

        # Parse coverage report
        coverage_file = self.project_root / "coverage.xml"
        if coverage_file.exists():
            report["coverage"] = self._parse_coverage_xml(coverage_file)

        # Save report
        report_file = self.results_dir / "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate HTML report
        self._generate_html_report(report)

        return report

    def _parse_junit_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML file"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(xml_file)
            root = tree.getroot()

            total = int(root.get("tests", 0))
            failures = int(root.get("failures", 0))
            errors = int(root.get("errors", 0))
            skipped = int(root.get("skipped", 0))

            return {
                "total": total,
                "passed": total - failures - errors - skipped,
                "failed": failures + errors,
                "skipped": skipped,
                "time": float(root.get("time", 0))
            }
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "time": 0}

    def _parse_coverage_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse coverage XML file"""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(xml_file)
            root = tree.getroot()

            coverage_data = {}
            for package in root.findall(".//package"):
                package_name = package.get("name")
                line_rate = float(package.get("line-rate", 0))
                branch_rate = float(package.get("branch-rate", 0))

                coverage_data[package_name] = {
                    "line_coverage": line_rate * 100,
                    "branch_coverage": branch_rate * 100
                }

            return coverage_data
        except Exception as e:
            print(f"Error parsing coverage report: {e}")
            return {}

    def _generate_html_report(self, report: Dict[str, Any]) -> None:
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>DMLog Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric h3 {{ margin: 0; }}
        .metric .value {{ font-size: 2em; font-weight: bold; color: #2c5282; }}
        .passed {{ color: #38a169; }}
        .failed {{ color: #e53e3e; }}
        .coverage {{ margin: 20px 0; }}
        .test-suite {{ margin: 10px 0; padding: 10px; border-left: 4px solid #cbd5e0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #e2e8f0; }}
        th {{ background-color: #f7fafc; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>DMLog Test Report</h1>
        <p>Generated on: {report['timestamp']}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div class="value">{report['total_tests']}</div>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <div class="value passed">{report['passed_tests']}</div>
        </div>
        <div class="metric">
            <h3>Failed</h3>
            <div class="value failed">{report['failed_tests']}</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div class="value">{(report['passed_tests']/max(report['total_tests'], 1)*100):.1f}%</div>
        </div>
    </div>

    <div class="coverage">
        <h2>Code Coverage</h2>
        {self._format_coverage_html(report.get('coverage', {}))}
    </div>

    <div class="test-suites">
        <h2>Test Suite Results</h2>
        {self._format_test_suites_html(report.get('test_suites', {}))}
    </div>
</body>
</html>
        """

        html_file = self.results_dir / "test_report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)

        print(f"HTML report generated: {html_file}")

    def _format_coverage_html(self, coverage_data: Dict[str, Any]) -> str:
        """Format coverage data for HTML"""
        if not coverage_data:
            return "<p>No coverage data available</p>"

        html = "<table><tr><th>Package</th><th>Line Coverage</th><th>Branch Coverage</th></tr>"
        for package, data in coverage_data.items():
            html += f"""
            <tr>
                <td>{package}</td>
                <td>{data['line_coverage']:.1f}%</td>
                <td>{data['branch_coverage']:.1f}%</td>
            </tr>
            """
        html += "</table>"
        return html

    def _format_test_suites_html(self, test_suites: Dict[str, Any]) -> str:
        """Format test suite results for HTML"""
        if not test_suites:
            return "<p>No test suite data available</p>"

        html = ""
        for suite_file, results in test_suites.items():
            suite_name = suite_file.replace("test_results/", "").replace(".xml", "")
            html += f"""
            <div class="test-suite">
                <h3>{suite_name}</h3>
                <p>Total: {results['total']},
                   Passed: {results['passed']},
                   Failed: {results['failed']},
                   Time: {results['time']:.2f}s</p>
            </div>
            """
        return html

    def cleanup_test_results(self) -> None:
        """Clean up old test results"""
        print("\n=== Cleaning up old test results ===")

        # Remove old test result files
        patterns = [
            "test_results/*.xml",
            "test_results/*.html",
            "test_results/*.json",
            "test_results/*.csv",
            ".coverage",
            "htmlcov/"
        ]

        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    print(f"Removed: {file_path}")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")

    def run_all_tests(self,
                     include_unit: bool = True,
                     include_integration: bool = True,
                     include_e2e: bool = False,
                     include_security: bool = True,
                     include_load: bool = False,
                     verbose: bool = False) -> bool:
        """Run all specified test suites"""
        print("=== Running DMLog Test Suite ===")
        print(f"Project root: {self.project_root}")

        results = {
            "unit": True,
            "integration": True,
            "e2e": True,
            "security": True,
            "load": True
        }

        if include_unit:
            results["unit"] = self.run_unit_tests(verbose=verbose)

        if include_integration:
            results["integration"] = self.run_integration_tests(verbose=verbose)

        if include_e2e:
            results["e2e"] = self.run_e2e_tests(headless=True)

        if include_security:
            results["security"] = self.run_security_tests()

        if include_load:
            results["load"] = self.run_load_tests()

        # Generate report
        self.generate_test_report()

        # Print summary
        print("\n=== Test Results Summary ===")
        for suite, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{suite.title()} Tests: {status}")

        all_passed = all(results.values())
        print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        return all_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DMLog Test Runner")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--unit", action="store_true", default=True, help="Run unit tests")
    parser.add_argument("--integration", action="store_true", default=True, help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--security", action="store_true", default=True, help="Run security tests")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--load-scenario", choices=["light", "moderate", "heavy", "stress"],
                       default="moderate", help="Load test scenario")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"],
                       default="chromium", help="Browser for E2E tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old test results")
    parser.add_argument("--generate-report-only", action="store_true", help="Generate report from existing results")

    args = parser.parse_args()

    runner = DMLogTestRunner(args.project_root)

    if args.cleanup:
        runner.cleanup_test_results()
        return

    if args.generate_report_only:
        runner.generate_test_report()
        return

    # Configure test execution
    include_e2e = args.e2e
    include_load = args.load
    include_coverage = not args.no_coverage

    # Run tests
    success = runner.run_all_tests(
        include_unit=args.unit,
        include_integration=args.integration,
        include_e2e=include_e2e,
        include_security=args.security,
        include_load=include_load,
        verbose=args.verbose
    )

    # Run additional tests if requested
    if include_load:
        runner.run_load_tests(args.load_scenario)

    if include_e2e:
        runner.run_e2e_tests(browser=args.browser)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()