#!/usr/bin/env python3
"""
Future Simulator - Monte Carlo simulation of future scenarios
Simulates multiple possible futures to assess probabilities and risks
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import logging

try:
    from scipy import stats
    from scipy.optimize import minimize
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    print("Warning: scipy/matplotlib not available. Using simplified simulation")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of simulation scenarios"""
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    REALISTIC = "realistic"
    BLACK_SWAN = "black_swan"
    TRANSFORMATION = "transformation"
    STAGNATION = "stagnation"
    VOLATILE = "volatile"


@dataclass
class SimulationParameters:
    """Parameters for Monte Carlo simulation"""
    num_simulations: int = 10000
    time_horizon: int = 30  # days
    time_step: float = 1.0  # hours
    random_seed: Optional[int] = None
    confidence_level: float = 0.95
    convergence_threshold: float = 0.01
    max_iterations: int = 1000


@dataclass
class Scenario:
    """Represents a simulated future scenario"""
    scenario_id: str
    scenario_type: ScenarioType
    probability: float
    outcomes: Dict[str, List[float]]
    timestamps: List[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    key_events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Results from a Monte Carlo simulation"""
    simulation_id: str
    timestamp: datetime
    parameters: SimulationParameters
    scenarios: List[Scenario]
    aggregate_statistics: Dict[str, Dict[str, float]]
    convergence_metrics: Dict[str, float]
    risk_assessment: Dict[str, Any]


class ProbabilityDistribution:
    """Represents probability distributions for simulation variables"""

    def __init__(self, distribution_type: str, **params):
        self.distribution_type = distribution_type
        self.params = params

    def sample(self, size: int = 1) -> np.ndarray:
        """Generate samples from the distribution"""
        try:
            if self.distribution_type == "normal":
                return np.random.normal(self.params["mean"], self.params["std"], size)
            elif self.distribution_type == "lognormal":
                return np.random.lognormal(self.params["mean"], self.params["sigma"], size)
            elif self.distribution_type == "uniform":
                return np.random.uniform(self.params["low"], self.params["high"], size)
            elif self.distribution_type == "exponential":
                return np.random.exponential(self.params["scale"], size)
            elif self.distribution_type == "beta":
                return np.random.beta(self.params["alpha"], self.params["beta"], size)
            elif self.distribution_type == "poisson":
                return np.random.poisson(self.params["lam"], size)
            else:
                # Default to normal distribution
                return np.random.normal(0, 1, size)
        except Exception as e:
            logger.error(f"Error sampling from distribution: {e}")
            return np.random.normal(0, 1, size)


class SystemModel:
    """Models the dynamics of a system variable over time"""

    def __init__(self, name: str, initial_value: float, distribution: ProbabilityDistribution):
        self.name = name
        self.initial_value = initial_value
        self.distribution = distribution
        self.drift = 0.0
        self.volatility = 0.1
        self.mean_reversion = 0.0
        self.external_factors = []

    def step(self, current_value: float, time_step: float, external_inputs: Dict[str, float] = None) -> float:
        """Simulate one time step"""
        # Geometric Brownian Motion with mean reversion
        random_shock = self.distribution.sample()[0]

        # Mean reversion term
        mean_reversion_term = self.mean_reversion * (self.initial_value - current_value)

        # External factors
        external_effect = 0.0
        if external_inputs:
            for factor in self.external_factors:
                if factor["name"] in external_inputs:
                    external_effect += factor["coefficient"] * external_inputs[factor["name"]]

        # Update value
        new_value = current_value * (1 + self.drift * time_step +
                                     self.volatility * np.sqrt(time_step) * random_shock) + \
                    mean_reversion_term * time_step + external_effect

        return max(0, new_value)  # Ensure non-negative values


class EventGenerator:
    """Generates random events during simulation"""

    def __init__(self):
        self.event_types = {
            "market_crash": {"probability": 0.01, "impact": -0.3, "duration": 5},
            "market_boom": {"probability": 0.02, "impact": 0.2, "duration": 3},
            "player_surge": {"probability": 0.05, "impact": 0.5, "duration": 2},
            "player_exodus": {"probability": 0.01, "impact": -0.4, "duration": 4},
            "technical_issue": {"probability": 0.03, "impact": -0.2, "duration": 1},
            "new_feature": {"probability": 0.04, "impact": 0.3, "duration": 6},
            "competitor_entry": {"probability": 0.02, "impact": -0.25, "duration": 10},
            "viral_content": {"probability": 0.01, "impact": 0.8, "duration": 3}
        }

    def generate_events(self, num_steps: int) -> List[Dict[str, Any]]:
        """Generate random events for simulation period"""
        events = []

        for step in range(num_steps):
            for event_type, event_config in self.event_types.items():
                if np.random.random() < event_config["probability"]:
                    event = {
                        "time_step": step,
                        "type": event_type,
                        "impact": event_config["impact"],
                        "duration": event_config["duration"],
                        "magnitude": np.random.uniform(0.5, 1.5) * event_config["impact"]
                    }
                    events.append(event)

        return events


class MonteCarloSimulator:
    """Core Monte Carlo simulation engine"""

    def __init__(self, parameters: SimulationParameters):
        self.parameters = parameters
        self.system_models: Dict[str, SystemModel] = {}
        self.event_generator = EventGenerator()
        self.correlation_matrix = np.eye(1)  # Default: no correlation
        self.simulation_history: List[SimulationResult] = []

    def add_system_model(self, model: SystemModel):
        """Add a system model to simulate"""
        self.system_models[model.name] = model

    def set_correlations(self, correlation_matrix: np.ndarray):
        """Set correlation matrix between variables"""
        n = len(self.system_models)
        if correlation_matrix.shape == (n, n):
            self.correlation_matrix = correlation_matrix
        else:
            logger.warning("Correlation matrix size doesn't match number of models")

    async def run_simulation(self, scenario_generators: Optional[Dict[str, Callable]] = None) -> SimulationResult:
        """Run complete Monte Carlo simulation"""
        simulation_id = f"sim_{datetime.now().timestamp()}"
        logger.info(f"Starting Monte Carlo simulation {simulation_id}")

        if self.parameters.random_seed:
            np.random.seed(self.parameters.random_seed)
            random.seed(self.parameters.random_seed)

        scenarios = []
        convergence_metrics = {}

        # Generate scenarios
        if scenario_generators:
            for scenario_name, generator in scenario_generators.items():
                scenario = await generator(self.parameters, self.system_models)
                scenarios.append(scenario)
        else:
            # Default scenarios
            scenarios = await self._generate_default_scenarios()

        # Run Monte Carlo simulation for each scenario
        for scenario in scenarios:
            await self._simulate_scenario(scenario)

        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_statistics(scenarios)

        # Assess convergence
        convergence_metrics = self._assess_convergence(scenarios)

        # Risk assessment
        risk_assessment = self._assess_risks(scenarios)

        result = SimulationResult(
            simulation_id=simulation_id,
            timestamp=datetime.now(),
            parameters=self.parameters,
            scenarios=scenarios,
            aggregate_statistics=aggregate_stats,
            convergence_metrics=convergence_metrics,
            risk_assessment=risk_assessment
        )

        self.simulation_history.append(result)
        logger.info(f"Simulation {simulation_id} completed successfully")

        return result

    async def _generate_default_scenarios(self) -> List[Scenario]:
        """Generate default scenario types"""
        scenarios = []

        # Optimistic scenario
        optimistic = Scenario(
            scenario_id="optimistic_default",
            scenario_type=ScenarioType.OPTIMISTIC,
            probability=0.2,
            outcomes={},
            timestamps=[],
            metadata={"description": "Best case scenario with favorable conditions"}
        )

        # Pessimistic scenario
        pessimistic = Scenario(
            scenario_id="pessimistic_default",
            scenario_type=ScenarioType.PESSIMISTIC,
            probability=0.2,
            outcomes={},
            timestamps=[],
            metadata={"description": "Worst case scenario with adverse conditions"}
        )

        # Realistic scenario
        realistic = Scenario(
            scenario_id="realistic_default",
            scenario_type=ScenarioType.REALISTIC,
            probability=0.6,
            outcomes={},
            timestamps=[],
            metadata={"description": "Most likely scenario based on current trends"}
        )

        scenarios = [optimistic, pessimistic, realistic]

        # Add black swan scenario occasionally
        if np.random.random() < 0.1:
            black_swan = Scenario(
                scenario_id="black_swan_default",
                scenario_type=ScenarioType.BLACK_SWAN,
                probability=0.05,
                outcomes={},
                timestamps=[],
                metadata={"description": "Rare, high-impact event scenario"}
            )
            scenarios.append(black_swan)

        return scenarios

    async def _simulate_scenario(self, scenario: Scenario):
        """Simulate a single scenario"""
        num_steps = int(self.parameters.time_horizon * 24 / self.parameters.time_step)
        timestamps = [datetime.now() + timedelta(hours=i * self.parameters.time_step)
                     for i in range(num_steps)]

        # Initialize outcomes
        scenario.outcomes = {name: [] for name in self.system_models.keys()}
        scenario.timestamps = timestamps

        # Apply scenario-specific parameters
        scenario_params = self._get_scenario_parameters(scenario.scenario_type)

        # Generate events for this scenario
        events = self.event_generator.generate_events(num_steps)
        if scenario.scenario_type == ScenarioType.BLACK_SWAN:
            # Add a major black swan event
            events.append({
                "time_step": np.random.randint(num_steps // 2, num_steps),
                "type": "black_swan",
                "impact": np.random.choice([-1, 1]) * np.random.uniform(0.5, 0.9),
                "duration": np.random.randint(5, 15),
                "magnitude": np.random.uniform(0.5, 0.9) * 2
            })

        # Run multiple simulations for this scenario
        all_simulations = {name: [] for name in self.system_models.keys()}

        for sim in range(self.parameters.num_simulations // len(scenario.outcomes)):
            simulation_result = self._run_single_simulation(
                timestamps, scenario_params, events, num_steps
            )

            for name, values in simulation_result.items():
                all_simulations[name].append(values)

        # Aggregate results
        for name in self.system_models.keys():
            if all_simulations[name]:
                # Calculate percentiles for confidence intervals
                all_values = np.array(all_simulations[name])
                scenario.outcomes[name] = np.median(all_values, axis=0).tolist()

                # Calculate confidence intervals
                lower_percentile = (1 - self.parameters.confidence_level) / 2 * 100
                upper_percentile = (1 + self.parameters.confidence_level) / 2 * 100

                scenario.confidence_intervals[name] = (
                    np.percentile(all_values, lower_percentile, axis=0).tolist(),
                    np.percentile(all_values, upper_percentile, axis=0).tolist()
                )

        # Identify key events
        scenario.key_events = self._identify_key_events(scenario.outcomes, events, timestamps)

    def _run_single_simulation(self, timestamps: List[datetime],
                             scenario_params: Dict[str, float],
                             events: List[Dict[str, Any]],
                             num_steps: int) -> Dict[str, List[float]]:
        """Run a single simulation path"""
        results = {name: [] for name in self.system_models.keys()}
        current_values = {name: model.initial_value for name, model in self.system_models.items()}

        # Apply scenario adjustments
        for name, model in self.system_models.items():
            if name in scenario_params:
                model.drift += scenario_params[name].get("drift_adjustment", 0)
                model.volatility *= scenario_params[name].get("volatility_multiplier", 1)

        active_events = {}

        for step in range(num_steps):
            # Process events
            for event in events:
                if event["time_step"] == step:
                    active_events[event["type"]] = {
                        "impact": event["magnitude"],
                        "remaining_duration": event["duration"]
                    }

            # Update active events
            completed_events = []
            for event_type, event_data in active_events.items():
                event_data["remaining_duration"] -= 1
                if event_data["remaining_duration"] <= 0:
                    completed_events.append(event_type)

            for event_type in completed_events:
                del active_events[event_type]

            # Calculate external effects from events
            external_effects = {}
            for event_type, event_data in active_events.items():
                external_effects[event_type] = event_data["impact"]

            # Simulate each system model
            for name, model in self.system_models.items():
                new_value = model.step(
                    current_values[name],
                    self.parameters.time_step,
                    external_effects
                )
                results[name].append(new_value)
                current_values[name] = new_value

        return results

    def _get_scenario_parameters(self, scenario_type: ScenarioType) -> Dict[str, Dict[str, float]]:
        """Get scenario-specific parameters"""
        base_params = {
            name: {"drift_adjustment": 0, "volatility_multiplier": 1}
            for name in self.system_models.keys()
        }

        if scenario_type == ScenarioType.OPTIMISTIC:
            for name in base_params:
                base_params[name]["drift_adjustment"] = 0.05
                base_params[name]["volatility_multiplier"] = 0.8

        elif scenario_type == ScenarioType.PESSIMISTIC:
            for name in base_params:
                base_params[name]["drift_adjustment"] = -0.03
                base_params[name]["volatility_multiplier"] = 1.5

        elif scenario_type == ScenarioType.REALISTIC:
            for name in base_params:
                base_params[name]["drift_adjustment"] = 0.01
                base_params[name]["volatility_multiplier"] = 1.0

        elif scenario_type == ScenarioType.BLACK_SWAN:
            for name in base_params:
                base_params[name]["drift_adjustment"] = np.random.choice([-0.1, 0.1])
                base_params[name]["volatility_multiplier"] = 2.0

        return base_params

    def _calculate_aggregate_statistics(self, scenarios: List[Scenario]) -> Dict[str, Dict[str, float]]:
        """Calculate aggregate statistics across all scenarios"""
        stats = {}

        for name in self.system_models.keys():
            all_values = []
            all_weights = []

            for scenario in scenarios:
                if name in scenario.outcomes:
                    all_values.extend(scenario.outcomes[name])
                    all_weights.extend([scenario.probability] * len(scenario.outcomes[name]))

            if all_values:
                weighted_mean = np.average(all_values, weights=all_weights)
                weighted_std = np.sqrt(np.average((np.array(all_values) - weighted_mean)**2, weights=all_weights))

                stats[name] = {
                    "mean": weighted_mean,
                    "std": weighted_std,
                    "min": np.min(all_values),
                    "max": np.max(all_values),
                    "median": np.median(all_values),
                    "percentile_5": np.percentile(all_values, 5),
                    "percentile_95": np.percentile(all_values, 95)
                }

        return stats

    def _assess_convergence(self, scenarios: List[Scenario]) -> Dict[str, float]:
        """Assess simulation convergence"""
        convergence = {}

        for name in self.system_models.keys():
            final_values = []
            for scenario in scenarios:
                if name in scenario.outcomes and scenario.outcomes[name]:
                    final_values.append(scenario.outcomes[name][-1])

            if len(final_values) > 1:
                # Coefficient of variation as convergence metric
                cv = np.std(final_values) / (np.mean(final_values) + 1e-6)
                convergence[name] = max(0, 1 - cv)  # Higher is better
            else:
                convergence[name] = 0.0

        return convergence

    def _assess_risks(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """Assess various risk metrics"""
        risk_assessment = {
            "value_at_risk": {},
            "expected_shortfall": {},
            "probability_of_loss": {},
            "maximum_drawdown": {},
            "volatility_risk": {}
        }

        confidence_level = 0.05  # 5% VaR

        for name in self.system_models.keys():
            all_final_values = []
            all_drawdowns = []

            for scenario in scenarios:
                if name in scenario.outcomes and scenario.outcomes[name]:
                    values = scenario.outcomes[name]
                    all_final_values.append(values[-1])

                    # Calculate drawdown
                    peak = values[0]
                    max_dd = 0
                    for value in values:
                        if value > peak:
                            peak = value
                        dd = (peak - value) / peak
                        max_dd = max(max_dd, dd)
                    all_drawdowns.append(max_dd)

            if all_final_values:
                # Value at Risk
                var = np.percentile(all_final_values, confidence_level * 100)
                risk_assessment["value_at_risk"][name] = var

                # Expected Shortfall
                shortfall_values = [v for v in all_final_values if v <= var]
                expected_shortfall = np.mean(shortfall_values) if shortfall_values else var
                risk_assessment["expected_shortfall"][name] = expected_shortfall

                # Probability of loss (assuming initial value is positive)
                initial_value = self.system_models[name].initial_value
                prob_loss = np.mean(np.array(all_final_values) < initial_value)
                risk_assessment["probability_of_loss"][name] = prob_loss

                # Maximum drawdown
                risk_assessment["maximum_drawdown"][name] = np.max(all_drawdowns) if all_drawdowns else 0

                # Volatility risk
                risk_assessment["volatility_risk"][name] = np.std(all_final_values)

        return risk_assessment

    def _identify_key_events(self, outcomes: Dict[str, List[float]],
                           events: List[Dict[str, Any]],
                           timestamps: List[datetime]) -> List[Dict[str, Any]]:
        """Identify key events and their impacts"""
        key_events = []

        for event in events:
            event_time = timestamps[event["time_step"]]

            # Calculate impact on each variable
            impacts = {}
            for name, values in outcomes.items():
                if event["time_step"] < len(values) - 1:
                    before_event = values[max(0, event["time_step"] - 5):event["time_step"]]
                    after_event = values[event["time_step"]:min(len(values), event["time_step"] + 5)]

                    if before_event and after_event:
                        before_avg = np.mean(before_event)
                        after_avg = np.mean(after_event)
                        impact = (after_avg - before_avg) / (before_avg + 1e-6)
                        impacts[name] = impact

            key_events.append({
                "timestamp": event_time,
                "type": event["type"],
                "magnitude": event["magnitude"],
                "impacts": impacts,
                "description": f"{event['type']} event with magnitude {event['magnitude']:.2f}"
            })

        return key_events


class FutureSimulator:
    """Main interface for future simulation"""

    def __init__(self):
        self.simulator: Optional[MonteCarloSimulator] = None
        self.simulation_results: List[SimulationResult] = []

    def create_simulation(self, parameters: SimulationParameters) -> MonteCarloSimulator:
        """Create a new simulation"""
        self.simulator = MonteCarloSimulator(parameters)
        return self.simulator

    def add_variable(self, name: str, initial_value: float,
                    distribution: ProbabilityDistribution, **kwargs):
        """Add a variable to simulate"""
        if self.simulator is None:
            raise RuntimeError("Create simulation first")

        model = SystemModel(name, initial_value, distribution)
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)

        self.simulator.add_system_model(model)

    async def run_simulation(self, scenario_generators: Optional[Dict[str, Callable]] = None) -> SimulationResult:
        """Run the complete simulation"""
        if self.simulator is None:
            raise RuntimeError("Create simulation first")

        result = await self.simulator.run_simulation(scenario_generators)
        self.simulation_results.append(result)
        return result

    def get_latest_results(self) -> Optional[SimulationResult]:
        """Get the most recent simulation results"""
        return self.simulation_results[-1] if self.simulation_results else None

    def generate_report(self, result: SimulationResult) -> str:
        """Generate a comprehensive simulation report"""
        report = []
        report.append(f"Monte Carlo Simulation Report")
        report.append(f"===============================")
        report.append(f"Simulation ID: {result.simulation_id}")
        report.append(f"Timestamp: {result.timestamp}")
        report.append(f"Parameters: {result.parameters.num_simulations} simulations, "
                     f"{result.parameters.time_horizon} days horizon")
        report.append(f"")

        # Scenario summary
        report.append("Scenario Summary:")
        report.append("-" * 40)
        for scenario in result.scenarios:
            report.append(f"{scenario.scenario_type.value}: {scenario.probability:.1%} probability")
            if scenario.metadata.get("description"):
                report.append(f"  {scenario.metadata['description']}")
        report.append(f"")

        # Aggregate statistics
        report.append("Aggregate Statistics:")
        report.append("-" * 40)
        for name, stats in result.aggregate_statistics.items():
            report.append(f"{name}:")
            report.append(f"  Mean: {stats['mean']:.3f}")
            report.append(f"  Std Dev: {stats['std']:.3f}")
            report.append(f"  Range: [{stats['min']:.3f}, {stats['max']:.3f}]")
            report.append(f"  95% CI: [{stats['percentile_5']:.3f}, {stats['percentile_95']:.3f}]")
        report.append(f"")

        # Risk assessment
        report.append("Risk Assessment:")
        report.append("-" * 40)
        for name in result.risk_assessment["value_at_risk"]:
            report.append(f"{name}:")
            report.append(f"  Value at Risk (5%): {result.risk_assessment['value_at_risk'][name]:.3f}")
            report.append(f"  Expected Shortfall: {result.risk_assessment['expected_shortfall'][name]:.3f}")
            report.append(f"  Probability of Loss: {result.risk_assessment['probability_of_loss'][name]:.1%}")
            report.append(f"  Max Drawdown: {result.risk_assessment['maximum_drawdown'][name]:.1%}")
        report.append(f"")

        # Key events
        report.append("Key Events:")
        report.append("-" * 40)
        for scenario in result.scenarios:
            if scenario.key_events:
                report.append(f"{scenario.scenario_type.value} scenario events:")
                for event in scenario.key_events[:3]:  # Show top 3 events
                    report.append(f"  {event['timestamp']}: {event['description']}")

        return "\n".join(report)


# Singleton instance
_future_simulator = None

def get_future_simulator() -> FutureSimulator:
    """Get the singleton future simulator instance"""
    global _future_simulator
    if _future_simulator is None:
        _future_simulator = FutureSimulator()
    return _future_simulator


async def main():
    """Example usage of the future simulator"""
    simulator = get_future_simulator()

    # Create simulation parameters
    params = SimulationParameters(
        num_simulations=1000,
        time_horizon=30,
        random_seed=42
    )

    # Create simulation
    mc_simulator = simulator.create_simulation(params)

    # Add variables to simulate
    # Player activity with normal distribution
    player_dist = ProbabilityDistribution("normal", mean=1000, std=100)
    simulator.add_variable("player_activity", 1000, player_dist, drift=0.01, volatility=0.15)

    # Market prices with lognormal distribution
    market_dist = ProbabilityDistribution("lognormal", mean=0.02, sigma=0.3)
    simulator.add_variable("market_prices", 100, market_dist, drift=0.005, volatility=0.2)

    # System events with Poisson distribution
    events_dist = ProbabilityDistribution("poisson", lam=5)
    simulator.add_variable("system_events", 5, events_dist, drift=0.0, volatility=0.1)

    print("Running Monte Carlo simulation...")
    result = await simulator.run_simulation()

    # Generate and print report
    report = simulator.generate_report(result)
    print(report)

    # Print some specific results
    print(f"\nConvergence Metrics:")
    for name, conv in result.convergence_metrics.items():
        print(f"  {name}: {conv:.3f}")

    print(f"\nScenarios Generated: {len(result.scenarios)}")
    for scenario in result.scenarios:
        print(f"  {scenario.scenario_type.value}: probability={scenario.probability:.3f}")


if __name__ == "__main__":
    asyncio.run(main())