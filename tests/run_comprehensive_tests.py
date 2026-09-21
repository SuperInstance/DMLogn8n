#!/usr/bin/env python3
"""
Comprehensive Integration Testing Execution Script

This script orchestrates the complete testing suite for DMlogn8n,
including end-to-end tests, performance tests, data integrity tests,
AI system tests, and user experience tests.

Usage:
    python run_comprehensive_tests.py [--suite SUITE] [--config CONFIG] [--output OUTPUT]

Author: DMlogn8n Testing Framework
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import yaml

# Add the DMLogn8n path for imports
sys.path.append('/home/activeloguser/DMLogn8n')
from tests.integration_test_framework import IntegrationTestFramework, TestResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/tests/comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Main test runner for comprehensive testing suite"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.n8n_base_url = self.config.get('n8n_base_url', 'http://localhost:5678')
        self.n8n_api_key = self.config.get('n8n_api_key')
        self.output_dir = Path(self.config.get('output_dir', '/home/activeloguser/DMLogn8n/test_reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize test framework
        self.framework = IntegrationTestFramework(config_file)

        # Test suite configuration
        self.test_suites = {
            'end_to_end': {
                'name': 'End-to-End Test Suite',
                'description': 'Complete system validation tests',
                'workflow_file': 'end-to-end-test-suite.json',
                'timeout': 1800,  # 30 minutes
                'priority': 'high'
            },
            'performance': {
                'name': 'Performance Testing Suite',
                'description': 'System performance and load tests',
                'workflow_file': 'performance-testing-suite.json',
                'timeout': 3600,  # 60 minutes
                'priority': 'medium'
            },
            'data_integrity': {
                'name': 'Data Integrity Testing Suite',
                'description': 'Data integrity and reliability tests',
                'workflow_file': 'data-integrity-testing-suite.json',
                'timeout': 1800,  # 30 minutes
                'priority': 'high'
            },
            'ai_systems': {
                'name': 'AI System Testing Suite',
                'description': 'AI system intelligence validation tests',
                'workflow_file': 'ai-system-testing-suite.json',
                'timeout': 2700,  # 45 minutes
                'priority': 'medium'
            },
            'user_experience': {
                'name': 'User Experience Testing Suite',
                'description': 'User experience and player journey tests',
                'workflow_file': 'user-experience-testing-suite.json',
                'timeout': 1800,  # 30 minutes
                'priority': 'low'
            }
        }

    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load test configuration"""
        default_config = {
            'n8n_base_url': os.getenv('N8N_BASE_URL', 'http://localhost:5678'),
            'n8n_api_key': os.getenv('N8N_API_KEY'),
            'output_dir': '/home/activeloguser/DMLogn8n/test_reports',
            'workflows_dir': '/home/activeloguser/DMLogn8n/workflows',
            'parallel_execution': False,
            'email_notifications': True,
            'slack_notifications': True,
            'dashboard_updates': True,
            'test_data_retention': '30d'
        }

        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    async def run_suite(self, suite_name: str) -> List[TestResult]:
        """Run a specific test suite"""
        logger.info(f"Starting test suite: {suite_name}")

        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite_config = self.test_suites[suite_name]

        # Deploy the workflow if needed
        await self._ensure_workflow_deployed(suite_config['workflow_file'])

        # Run the test suite
        results = await self.framework.run_test_suite(suite_name)

        # Generate suite report
        await self._generate_suite_report(suite_name, results, suite_config)

        return results

    async def run_all_suites(self, parallel: bool = False) -> Dict[str, List[TestResult]]:
        """Run all test suites"""
        logger.info("Starting comprehensive test execution")

        all_results = {}
        start_time = time.time()

        if parallel:
            # Run suites in parallel (limited by system capacity)
            logger.info("Running test suites in parallel")

            # Define execution order based on priority and dependencies
            execution_order = [
                'end_to_end',      # Run first - basic functionality
                'data_integrity',  # Can run in parallel with end-to-end
                'performance',     # Run after basic validation
                'ai_systems',      # Run after performance is validated
                'user_experience'  # Run last - depends on other systems
            ]

            # Create task groups for parallel execution
            task_groups = [
                ['end_to_end', 'data_integrity'],  # Can run together
                ['performance'],                   # Runs alone
                ['ai_systems'],                    # Runs alone
                ['user_experience']                # Runs last
            ]

            for group in task_groups:
                group_tasks = []
                for suite_name in group:
                    if suite_name in self.test_suites:
                        task = asyncio.create_task(self.run_suite(suite_name))
                        group_tasks.append((suite_name, task))

                # Wait for all tasks in this group to complete
                for suite_name, task in group_tasks:
                    try:
                        results = await task
                        all_results[suite_name] = results
                        logger.info(f"Completed test suite: {suite_name}")
                    except Exception as e:
                        logger.error(f"Failed to run test suite {suite_name}: {e}")
                        all_results[suite_name] = []
        else:
            # Run suites sequentially
            logger.info("Running test suites sequentially")

            for suite_name in self.test_suites:
                try:
                    results = await self.run_suite(suite_name)
                    all_results[suite_name] = results
                    logger.info(f"Completed test suite: {suite_name}")
                except Exception as e:
                    logger.error(f"Failed to run test suite {suite_name}: {e}")
                    all_results[suite_name] = []

        total_duration = time.time() - start_time

        # Generate comprehensive report
        await self._generate_comprehensive_report(all_results, total_duration)

        return all_results

    async def _ensure_workflow_deployed(self, workflow_file: str) -> None:
        """Ensure the test workflow is deployed in n8n"""
        workflow_path = Path(self.config['workflows_dir']) / workflow_file

        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        # In a real implementation, this would deploy the workflow via n8n API
        logger.info(f"Ensuring workflow is deployed: {workflow_file}")

    async def _generate_suite_report(self, suite_name: str, results: List[TestResult], suite_config: Dict) -> None:
        """Generate a report for a single test suite"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"{suite_name}_report_{timestamp}.json"

        # Calculate summary statistics
        passed = len([r for r in results if r.status == 'passed'])
        failed = len([r for r in results if r.status == 'failed'])
        skipped = len([r for r in results if r.status == 'skipped'])
        total = len(results)

        durations = [r.duration for r in results if r.duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        suite_report = {
            'suite_name': suite_name,
            'suite_config': suite_config,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'success_rate': (passed / total * 100) if total > 0 else 0,
                'average_duration': avg_duration,
                'total_duration': sum(durations),
                'status': 'passed' if failed == 0 else 'failed' if passed > 0 else 'error'
            },
            'results': [self._serialize_test_result(r) for r in results],
            'performance_metrics': self._extract_performance_metrics(results),
            'recommendations': self._generate_suite_recommendations(suite_name, results)
        }

        with open(report_file, 'w') as f:
            json.dump(suite_report, f, indent=2, default=str)

        logger.info(f"Suite report saved: {report_file}")

    async def _generate_comprehensive_report(self, all_results: Dict[str, List[TestResult]], total_duration: float) -> None:
        """Generate a comprehensive report for all test suites"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"comprehensive_test_report_{timestamp}.json"

        # Aggregate all results
        all_test_results = []
        for suite_results in all_results.values():
            all_test_results.extend(suite_results)

        # Calculate overall statistics
        total_tests = len(all_test_results)
        passed_tests = len([r for r in all_test_results if r.status == 'passed'])
        failed_tests = len([r for r in all_test_results if r.status == 'failed'])
        skipped_tests = len([r for r in all_test_results if r.status == 'skipped'])

        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Suite-wise statistics
        suite_stats = {}
        for suite_name, results in all_results.items():
            passed = len([r for r in results if r.status == 'passed'])
            total = len(results)
            suite_stats[suite_name] = {
                'total': total,
                'passed': passed,
                'failed': total - passed,
                'success_rate': (passed / total * 100) if total > 0 else 0,
                'status': 'passed' if passed == total else 'failed' if passed > 0 else 'error'
            }

        # Generate overall assessment
        overall_status = 'passed'
        critical_issues = []

        if overall_success_rate < 90:
            overall_status = 'warning'

        if overall_success_rate < 70:
            overall_status = 'failed'
            critical_issues.append(f"Overall success rate ({overall_success_rate:.1f}%) is critically low")

        # Check for suite-specific issues
        for suite_name, stats in suite_stats.items():
            if stats['success_rate'] < 80:
                critical_issues.append(f"{suite_name} suite has low success rate ({stats['success_rate']:.1f}%)")

        comprehensive_report = {
            'execution_metadata': {
n                'timestamp': datetime.now().isoformat(),
                'total_duration': total_duration,
                'test_environment': 'production_test',
                'config_file': self.config.get('config_file'),
                'parallel_execution': self.config.get('parallel_execution', False)
            },
            'overall_summary': {
                'total_suites': len(self.test_suites),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests,
                'overall_success_rate': overall_success_rate,
                'overall_status': overall_status,
                'critical_issues': critical_issues
            },
            'suite_statistics': suite_stats,
            'detailed_results': {
n                suite_name: [self._serialize_test_result(r) for r in results]
                for suite_name, results in all_results.items()
            },
            'performance_analysis': self._analyze_performance_across_suites(all_results),
            'quality_metrics': self._calculate_quality_metrics(all_results),
            'recommendations': self._generate_overall_recommendations(all_results, suite_stats),
            'trend_analysis': self._analyze_trends(all_results),
            'next_steps': self._generate_next_steps(overall_status, critical_issues)
        }

        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)

        # Also generate a human-readable summary
        summary_file = self.output_dir / f"test_summary_{timestamp}.md"
        await self._generate_markdown_summary(comprehensive_report, summary_file)

        logger.info(f"Comprehensive report saved: {report_file}")
        logger.info(f"Summary report saved: {summary_file}")

    def _serialize_test_result(self, result: TestResult) -> Dict[str, Any]:
        """Serialize TestResult to dictionary"""
        return {
            'test_name': result.test_name,
            'status': result.status,
            'duration': result.duration,
            'timestamp': result.timestamp.isoformat(),
            'details': result.details,
            'error_message': result.error_message,
            'performance_metrics': result.performance_metrics
        }

    def _extract_performance_metrics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Extract performance metrics from test results"""
        metrics = {
            'total_duration': sum(r.duration for r in results),
            'average_duration': sum(r.duration for r in results) / len(results) if results else 0,
            'max_duration': max(r.duration for r in results) if results else 0,
            'min_duration': min(r.duration for r in results) if results else 0
        }

        # Extract any performance-specific metrics
        for result in results:
            if result.performance_metrics:
                for metric, value in result.performance_metrics.items():
                    if metric not in metrics:
                        metrics[metric] = []
                    metrics[metric].append(value)

        # Calculate averages for performance metrics
        for metric, values in metrics.items():
            if isinstance(values, list) and values:
                metrics[f'{metric}_average'] = sum(values) / len(values)
                metrics[f'{metric}_max'] = max(values)
                metrics[f'{metric}_min'] = min(values)

        return metrics

    def _generate_suite_recommendations(self, suite_name: str, results: List[TestResult]) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific test suite"""
        recommendations = []
        failed_tests = [r for r in results if r.status == 'failed']

        if len(failed_tests) > 0:
            recommendations.append({
                'category': 'test_stability',
                'priority': 'high' if len(failed_tests) > 3 else 'medium',
                'issue': f'{len(failed_tests)} tests failed in {suite_name} suite',
                'suggestion': 'Investigate test failures and fix underlying issues'
            })

        # Check for slow tests
        slow_tests = [r for r in results if r.duration > 300]  # 5 minutes
        if len(slow_tests) > 0:
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'issue': f'{len(slow_tests)} tests are taking longer than 5 minutes',
                'suggestion': 'Optimize test performance or consider test parallelization'
            })

        return recommendations

    def _analyze_performance_across_suites(self, all_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze performance across all test suites"""
        suite_performance = {}

        for suite_name, results in all_results.items():
            if results:
                durations = [r.duration for r in results]
                suite_performance[suite_name] = {
                    'average_duration': sum(durations) / len(durations),
                    'max_duration': max(durations),
                    'min_duration': min(durations),
                    'total_duration': sum(durations),
                    'test_count': len(results)
                }

        return {
            'suite_performance': suite_performance,
            'overall_performance': {
                'total_duration': sum(p['total_duration'] for p in suite_performance.values()),
                'average_suite_duration': sum(p['average_duration'] for p in suite_performance.values()) / len(suite_performance) if suite_performance else 0,
                'slowest_suite': max(suite_performance.items(), key=lambda x: x[1]['average_duration']) if suite_performance else None,
                'fastest_suite': min(suite_performance.items(), key=lambda x: x[1]['average_duration']) if suite_performance else None
            }
        }

    def _calculate_quality_metrics(self, all_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Calculate quality metrics for all test results"""
        all_test_results = []
        for results in all_results.values():
            all_test_results.extend(results)

        if not all_test_results:
            return {}

        return {
            'reliability_score': len([r for r in all_test_results if r.status == 'passed']) / len(all_test_results) * 100,
            'stability_score': 100 - (len([r for r in all_test_results if r.error_message]) / len(all_test_results) * 100),
            'performance_score': min(100, max(0, 100 - (sum(r.duration for r in all_test_results) / len(all_test_results) / 10))),  # Normalize to 0-100
            'overall_quality': 0  # Will be calculated below
        }

    def _generate_overall_recommendations(self, all_results: Dict[str, List[TestResult]], suite_stats: Dict) -> List[Dict[str, Any]]:
        """Generate overall recommendations based on all test results"""
        recommendations = []

        # Check for consistently failing suites
        failing_suites = [name for name, stats in suite_stats.items() if stats['success_rate'] < 80]
        if failing_suites:
            recommendations.append({
                'category': 'suite_health',
                'priority': 'high',
                'issue': f'Suites with low success rates: {", ".join(failing_suites)}',
                'suggestion': 'Prioritize fixing issues in failing test suites'
            })

        # Performance recommendations
        all_results_flat = []
        for results in all_results.values():
            all_results_flat.extend(results)

        slow_tests = [r for r in all_results_flat if r.duration > 600]  # 10 minutes
        if len(slow_tests) > 0:
            recommendations.append({
                'category': 'performance_optimization',
                'priority': 'medium',
                'issue': f'{len(slow_tests)} tests are taking longer than 10 minutes',
                'suggestion': 'Consider test optimization, parallelization, or infrastructure improvements'
            })

        return recommendations

    def _analyze_trends(self, all_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze trends in test results (placeholder for future implementation)"""
        return {
            'trend_analysis': 'Trend analysis requires historical data - not implemented yet',
            'recommendation': 'Implement trend tracking to identify patterns over time'
        }

    def _generate_next_steps(self, overall_status: str, critical_issues: List[str]) -> List[Dict[str, Any]]:
        """Generate next steps based on test results"""
        next_steps = []

        if overall_status == 'failed':
            next_steps.append({
                'action': 'immediate_attention',
                'description': 'Address critical test failures before proceeding',
                'priority': 'critical'
            })
        elif overall_status == 'warning':
            next_steps.append({
                'action': 'investigate_issues',
                'description': 'Investigate and address test warnings',
                'priority': 'high'
            })
        else:
            next_steps.append({
                'action': 'monitor_and_maintain',
                'description': 'Continue monitoring test health and address any emerging issues',
                'priority': 'medium'
            })

        # Add specific next steps based on critical issues
        for issue in critical_issues:
            next_steps.append({
                'action': 'address_critical_issue',
                'description': f'Resolve: {issue}',
                'priority': 'critical'
            })

        return next_steps

    async def _generate_markdown_summary(self, report: Dict[str, Any], summary_file: Path) -> None:
        """Generate a human-readable markdown summary"""
        summary = f"""# DMlogn8n Comprehensive Test Report

## Execution Summary

- **Timestamp**: {report['execution_metadata']['timestamp']}
- **Total Duration**: {report['execution_metadata']['total_duration']:.2f} seconds
- **Overall Status**: {report['overall_summary']['overall_status'].upper()}

## Test Results Overview

- **Total Test Suites**: {report['overall_summary']['total_suites']}
- **Total Tests**: {report['overall_summary']['total_tests']}
- **Passed**: {report['overall_summary']['passed_tests']}
- **Failed**: {report['overall_summary']['failed_tests']}
- **Skipped**: {report['overall_summary']['skipped_tests']}
- **Success Rate**: {report['overall_summary']['overall_success_rate']:.1f}%

## Suite-by-Suite Results

"""

        for suite_name, stats in report['suite_statistics'].items():
            summary += f"""### {suite_name.replace('_', ' ').title()}

- **Status**: {stats['status'].upper()}
- **Tests**: {stats['total']} (Passed: {stats['passed']}, Failed: {stats['failed']})
- **Success Rate**: {stats['success_rate']:.1f}%

"""

        if report['overall_summary']['critical_issues']:
            summary += """## Critical Issues

"""
            for issue in report['overall_summary']['critical_issues']:
                summary += f"- ❌ {issue}\n"

        if report['recommendations']:
            summary += """## Recommendations

"""
            for rec in report['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                summary += f"- {priority_icon} **{rec['category']}**: {rec['suggestion']}\n"

        summary += f"""
## Next Steps

"""
        for step in report['next_steps']:
            priority_icon = "🔴" if step['priority'] == 'critical' else "🟡" if step['priority'] == 'high' else "🟢"
            summary += f"- {priority_icon} {step['description']}\n"

        summary += f"""
---

*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(summary_file, 'w') as f:
            f.write(summary)

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Run comprehensive DMlogn8n tests')
    parser.add_argument('--suite', choices=['end_to_end', 'performance', 'data_integrity', 'ai_systems', 'user_experience'],
                       help='Run specific test suite')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output', help='Output directory', default='/home/activeloguser/DMLogn8n/test_reports')
    parser.add_argument('--parallel', action='store_true', help='Run test suites in parallel')
    parser.add_argument('--list-suites', action='store_true', help='List available test suites')

    args = parser.parse_args()

    # Override config with command line arguments
    config_overrides = {}
    if args.output:
        config_overrides['output_dir'] = args.output
    if args.parallel:
        config_overrides['parallel_execution'] = True

    # Initialize test runner
    runner = ComprehensiveTestRunner(args.config)

    # Apply config overrides
    for key, value in config_overrides.items():
        runner.config[key] = value

    if args.list_suites:
        print("Available test suites:")
        for suite_name, suite_config in runner.test_suites.items():
            print(f"  {suite_name}: {suite_config['description']}")
        return

    try:
        if args.suite:
            # Run specific suite
            logger.info(f"Running test suite: {args.suite}")
            results = await runner.run_suite(args.suite)
            print(f"Test suite '{args.suite}' completed. Results: {len([r for r in results if r.status == 'passed'])}/{len(results)} passed")
        else:
            # Run all suites
            logger.info("Running all test suites")
            all_results = await runner.run_all_suites(parallel=args.parallel)

            # Print summary
            total_tests = sum(len(results) for results in all_results.values())
            total_passed = sum(len([r for r in results if r.status == 'passed']) for results in all_results.values())

            print(f"\n{'='*60}")
            print("COMPREHENSIVE TEST EXECUTION COMPLETE")
            print(f"{'='*60}")
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {total_passed}")
            print(f"Failed: {total_tests - total_passed}")
            print(f"Success Rate: {(total_passed / total_tests * 100):.1f}%")
            print(f"Reports saved to: {runner.output_dir}")
            print(f"{'='*60}")

    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())