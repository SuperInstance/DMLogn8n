"""
DMLogn8n Load Testing Framework
Comprehensive load testing for multi-agent platforms
"""

from .load_test_runner import LoadTestRunner, LoadTestConfig, TestResult
from .scenarios import AgentSimulationScenario, UserJourneyScenario, CombatStressScenario, DialogueLoadScenario
from .generators import AgentLoadGenerator, UserLoadGenerator, TestDataGenerator
from .metrics import MetricsCollector, PerformanceAnalyzer, BaselineComparator
from .reports import HTMLReporter, JSONReporter, PerformanceDashboard

__version__ = "1.0.0"
__author__ = "DMLogn8n Team"
__description__ = "Comprehensive load testing framework for multi-agent platforms"

__all__ = [
    # Core components
    'LoadTestRunner',
    'LoadTestConfig',
    'TestResult',

    # Scenarios
    'AgentSimulationScenario',
    'UserJourneyScenario',
    'CombatStressScenario',
    'DialogueLoadScenario',

    # Generators
    'AgentLoadGenerator',
    'UserLoadGenerator',
    'TestDataGenerator',

    # Metrics
    'MetricsCollector',
    'PerformanceAnalyzer',
    'BaselineComparator',

    # Reports
    'HTMLReporter',
    'JSONReporter',
    'PerformanceDashboard'
]

def get_version():
    """Get the current version of the load testing framework"""
    return __version__

def get_description():
    """Get the description of the load testing framework"""
    return __description__