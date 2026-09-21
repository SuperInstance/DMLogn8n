#!/usr/bin/env python3
"""
DMlogn8n Integration Testing Framework

Comprehensive testing system for validating all components of the DMlogn8n platform
work together correctly. This framework provides end-to-end testing, performance
validation, data integrity checks, AI system validation, and user experience testing.

Author: DMlogn8n Testing Framework
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import requests
import aiohttp
import pytest
from dataclasses import dataclass, asdict
import statistics
import os
import sys

# Add the DMLogn8n path for imports
sys.path.append('/home/activeloguser/DMLogn8n')
from n8n_api_client import N8nAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/tests/integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None

@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    description: str
    tests: List[str]
    setup_hooks: List[str]
    teardown_hooks: List[str]
    timeout: int = 300  # 5 minutes default

class IntegrationTestFramework:
    """Main integration testing framework"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.n8n_client = N8nAPIClient(
            self.config['n8n_base_url'],
            self.config['n8n_api_key']
        )
        self.test_results: List[TestResult] = []
        self.test_data: Dict[str, Any] = {}
        self.session_data: Dict[str, Any] = {}

    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load test configuration"""
        default_config = {
            'n8n_base_url': os.getenv('N8N_BASE_URL', 'http://localhost:5678'),
            'n8n_api_key': os.getenv('N8N_API_KEY'),
            'test_timeout': 300,
            'performance_thresholds': {
                'api_response_time': 2.0,
                'ai_decision_latency': 5.0,
                'memory_retrieval_time': 1.0,
                'websocket_latency': 0.5
            },
            'load_test_config': {
                'concurrent_sessions': 10,
                'test_duration': 300,
                'ramp_up_time': 60
            },
            'test_data_path': '/home/activeloguser/DMLogn8n/tests/test_data',
            'reports_path': '/home/activeloguser/DMLogn8n/test_reports'
        }

        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    async def run_test_suite(self, suite_name: str) -> List[TestResult]:
        """Run a complete test suite"""
        logger.info(f"Starting test suite: {suite_name}")
        suite_results = []

        try:
            # Setup test environment
            await self._setup_test_environment(suite_name)

            # Get test suite configuration
            suite = self._get_test_suite(suite_name)

            # Run setup hooks
            for hook in suite.setup_hooks:
                await self._run_hook(hook, 'setup')

            # Run individual tests
            for test_name in suite.tests:
                result = await self._run_single_test(test_name, suite.timeout)
                suite_results.append(result)
                self.test_results.append(result)

            # Run teardown hooks
            for hook in suite.teardown_hooks:
                await self._run_hook(hook, 'teardown')

        except Exception as e:
            logger.error(f"Test suite {suite_name} failed: {e}")
            # Create failure result for the entire suite
            failure_result = TestResult(
                test_name=f"{suite_name}_suite_failure",
                status='failed',
                duration=0.0,
                details={'error': str(e)},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            suite_results.append(failure_result)
            self.test_results.append(failure_result)

        finally:
            # Cleanup test environment
            await self._cleanup_test_environment(suite_name)

        logger.info(f"Completed test suite: {suite_name} - {len([r for r in suite_results if r.status == 'passed'])}/{len(suite_results)} passed")
        return suite_results

    async def _run_single_test(self, test_name: str, timeout: int) -> TestResult:
        """Run a single test with timeout"""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()

        try:
            # Execute test with timeout
            result = await asyncio.wait_for(
                self._execute_test(test_name),
                timeout=timeout
            )

            duration = time.time() - start_time

            test_result = TestResult(
                test_name=test_name,
                status='passed',
                duration=duration,
                details=result,
                timestamp=datetime.now(),
                performance_metrics=result.get('performance_metrics', {})
            )

            logger.info(f"Test {test_name} passed in {duration:.2f}s")
            return test_result

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"Test {test_name} timed out after {timeout}s"
            logger.error(error_msg)

            return TestResult(
                test_name=test_name,
                status='failed',
                duration=duration,
                details={'timeout': True},
                timestamp=datetime.now(),
                error_message=error_msg
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test {test_name} failed: {str(e)}"
            logger.error(error_msg)

            return TestResult(
                test_name=test_name,
                status='failed',
                duration=duration,
                details={'exception': str(e)},
                timestamp=datetime.now(),
                error_message=error_msg
            )

    async def _execute_test(self, test_name: str) -> Dict[str, Any]:
        """Execute a specific test"""
        test_methods = {
            # End-to-End Tests
            'test_character_creation_to_ai_decision': self._test_character_creation_to_ai_decision,
            'test_memory_acquisition_to_consolidation': self._test_memory_acquisition_to_consolidation,
            'test_multi_player_session_coordination': self._test_multi_player_session_coordination,
            'test_voice_chat_realtime_communication': self._test_voice_chat_realtime_communication,
            'test_campaign_management_to_quest_completion': self._test_campaign_management_to_quest_completion,

            # Performance Tests
            'test_concurrent_session_capacity': self._test_concurrent_session_capacity,
            'test_ai_decision_latency': self._test_ai_decision_latency,
            'test_memory_retrieval_performance': self._test_memory_retrieval_performance,
            'test_database_query_optimization': self._test_database_query_optimization,
            'test_websocket_connection_stress': self._test_websocket_connection_stress,

            # Data Integrity Tests
            'test_character_state_consistency': self._test_character_state_consistency,
            'test_memory_corruption_detection': self._test_memory_corruption_detection,
            'test_transaction_rollback_validation': self._test_transaction_rollback_validation,
            'test_cross_service_data_synchronization': self._test_cross_service_data_synchronization,
            'test_backup_and_restore_verification': self._test_backup_and_restore_verification,

            # AI System Tests
            'test_character_personality_consistency': self._test_character_personality_consistency,
            'test_decision_quality_assessment': self._test_decision_quality_assessment,
            'test_memory_consolidation_accuracy': self._test_memory_consolidation_accuracy,
            'test_learning_curve_validation': self._test_learning_curve_validation,
            'test_multi_agent_coordination': self._test_multi_agent_coordination,

            # User Experience Tests
            'test_new_player_onboarding': self._test_new_player_onboarding,
            'test_character_progression_satisfaction': self._test_character_progression_satisfaction,
            'test_combat_mechanics_accuracy': self._test_combat_mechanics_accuracy,
            'test_social_interaction_quality': self._test_social_interaction_quality,
            'test_engagement_metrics': self._test_engagement_metrics
        }

        if test_name not in test_methods:
            raise ValueError(f"Unknown test: {test_name}")

        return await test_methods[test_name]()

    def _get_test_suite(self, suite_name: str) -> TestSuite:
        """Get test suite configuration"""
        suites = {
            'end_to_end': TestSuite(
                name='end_to_end',
                description='Complete system validation tests',
                tests=[
                    'test_character_creation_to_ai_decision',
                    'test_memory_acquisition_to_consolidation',
                    'test_multi_player_session_coordination',
                    'test_voice_chat_realtime_communication',
                    'test_campaign_management_to_quest_completion'
                ],
                setup_hooks=['setup_test_data', 'setup_mock_services'],
                teardown_hooks=['cleanup_test_data', 'cleanup_mock_services'],
                timeout=600
            ),
            'performance': TestSuite(
                name='performance',
                description='System performance and load tests',
                tests=[
                    'test_concurrent_session_capacity',
                    'test_ai_decision_latency',
                    'test_memory_retrieval_performance',
                    'test_database_query_optimization',
                    'test_websocket_connection_stress'
                ],
                setup_hooks=['setup_performance_monitoring', 'setup_load_test_environment'],
                teardown_hooks=['cleanup_performance_monitoring', 'cleanup_load_test_environment'],
                timeout=900
            ),
            'data_integrity': TestSuite(
                name='data_integrity',
                description='Data integrity and reliability tests',
                tests=[
                    'test_character_state_consistency',
                    'test_memory_corruption_detection',
                    'test_transaction_rollback_validation',
                    'test_cross_service_data_synchronization',
                    'test_backup_and_restore_verification'
                ],
                setup_hooks=['setup_test_database', 'setup_data_validation'],
                teardown_hooks=['cleanup_test_database', 'cleanup_data_validation'],
                timeout=600
            ),
            'ai_systems': TestSuite(
                name='ai_systems',
                description='AI system intelligence validation tests',
                tests=[
                    'test_character_personality_consistency',
                    'test_decision_quality_assessment',
                    'test_memory_consolidation_accuracy',
                    'test_learning_curve_validation',
                    'test_multi_agent_coordination'
                ],
                setup_hooks=['setup_ai_test_environment', 'setup_mock_ai_services'],
                teardown_hooks=['cleanup_ai_test_environment', 'cleanup_mock_ai_services'],
                timeout=900
            ),
            'user_experience': TestSuite(
                name='user_experience',
                description='User experience and player journey tests',
                tests=[
                    'test_new_player_onboarding',
                    'test_character_progression_satisfaction',
                    'test_combat_mechanics_accuracy',
                    'test_social_interaction_quality',
                    'test_engagement_metrics'
                ],
                setup_hooks=['setup_ux_test_environment', 'setup_user_scenarios'],
                teardown_hooks=['cleanup_ux_test_environment', 'cleanup_user_scenarios'],
                timeout=600
            )
        }

        if suite_name not in suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        return suites[suite_name]

    async def _run_hook(self, hook_name: str, hook_type: str) -> None:
        """Run a setup/teardown hook"""
        logger.info(f"Running {hook_type} hook: {hook_name}")

        hooks = {
            'setup_test_data': self._setup_test_data,
            'setup_mock_services': self._setup_mock_services,
            'setup_performance_monitoring': self._setup_performance_monitoring,
            'setup_load_test_environment': self._setup_load_test_environment,
            'setup_test_database': self._setup_test_database,
            'setup_data_validation': self._setup_data_validation,
            'setup_ai_test_environment': self._setup_ai_test_environment,
            'setup_mock_ai_services': self._setup_mock_ai_services,
            'setup_ux_test_environment': self._setup_ux_test_environment,
            'setup_user_scenarios': self._setup_user_scenarios,

            'cleanup_test_data': self._cleanup_test_data,
            'cleanup_mock_services': self._cleanup_mock_services,
            'cleanup_performance_monitoring': self._cleanup_performance_monitoring,
            'cleanup_load_test_environment': self._cleanup_load_test_environment,
            'cleanup_test_database': self._cleanup_test_database,
            'cleanup_data_validation': self._cleanup_data_validation,
            'cleanup_ai_test_environment': self._cleanup_ai_test_environment,
            'cleanup_mock_ai_services': self._cleanup_mock_ai_services,
            'cleanup_ux_test_environment': self._cleanup_ux_test_environment,
            'cleanup_user_scenarios': self._cleanup_user_scenarios
        }

        if hook_name in hooks:
            await hooks[hook_name]()
        else:
            logger.warning(f"Unknown hook: {hook_name}")

    async def _setup_test_environment(self, suite_name: str) -> None:
        """Setup test environment for a suite"""
        logger.info(f"Setting up test environment for {suite_name}")

        # Create test directories
        Path(self.config['reports_path']).mkdir(parents=True, exist_ok=True)
        Path(self.config['test_data_path']).mkdir(parents=True, exist_ok=True)

        # Initialize test data
        self.test_data = {
            'suite_name': suite_name,
            'start_time': datetime.now().isoformat(),
            'test_id': str(uuid.uuid4()),
            'environment': 'test'
        }

        # Verify n8n connection
        if not self.n8n_client.test_connection():
            raise ConnectionError("Cannot connect to n8n instance")

        # Ensure test workflows are available
        await self._ensure_test_workflows()

    async def _cleanup_test_environment(self, suite_name: str) -> None:
        """Cleanup test environment after a suite"""
        logger.info(f"Cleaning up test environment for {suite_name}")

        # Clear session data
        self.session_data.clear()

        # Save test results
        await self._save_test_results(suite_name)

    async def _ensure_test_workflows(self) -> None:
        """Ensure required test workflows are available in n8n"""
        required_workflows = [
            'Test Data Generator',
            'Performance Monitor',
            'AI System Validator',
            'User Experience Simulator'
        ]

        existing_workflows = self.n8n_client.get_workflows()
        existing_names = {w.get('name') for w in existing_workflows}

        for workflow_name in required_workflows:
            if workflow_name not in existing_names:
                logger.warning(f"Required test workflow not found: {workflow_name}")
                # In a real implementation, this would deploy the test workflow

    async def _save_test_results(self, suite_name: str) -> None:
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{suite_name}_test_results_{timestamp}.json"
        filepath = Path(self.config['reports_path']) / filename

        results_data = {
            'suite_name': suite_name,
            'timestamp': datetime.now().isoformat(),
            'test_data': self.test_data,
            'results': [asdict(result) for result in self.test_results],
            'summary': self._generate_summary()
        }

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        logger.info(f"Test results saved to: {filepath}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary statistics"""
        if not self.test_results:
            return {}

        passed = len([r for r in self.test_results if r.status == 'passed'])
        failed = len([r for r in self.test_results if r.status == 'failed'])
        skipped = len([r for r in self.test_results if r.status == 'skipped'])
        total = len(self.test_results)

        durations = [r.duration for r in self.test_results if r.duration > 0]
        avg_duration = statistics.mean(durations) if durations else 0

        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'average_duration': avg_duration,
            'total_duration': sum(durations),
            'test_run_id': self.test_data.get('test_id')
        }

# Test implementation methods will be added in the next part
if __name__ == "__main__":
    # Example usage
    framework = IntegrationTestFramework()

    async def run_all_tests():
        """Run all test suites"""
        suites = ['end_to_end', 'performance', 'data_integrity', 'ai_systems', 'user_experience']

        for suite in suites:
            logger.info(f"Running test suite: {suite}")
            results = await framework.run_test_suite(suite)

            # Print results summary
            passed = len([r for r in results if r.status == 'passed'])
            total = len(results)
            logger.info(f"Suite {suite}: {passed}/{total} tests passed")

    # Run the tests
    asyncio.run(run_all_tests())