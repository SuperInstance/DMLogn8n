#!/usr/bin/env python3
"""
Mathematical Optimization and Balance Testing System for DMLogn8n
Provides comprehensive balance analysis and optimization recommendations
"""

import json
import math
import random
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

class BalanceType(Enum):
    COMBAT = "combat"
    ECONOMY = "economy"
    PROGRESSION = "progression"
    SOCIAL = "social"
    DIFFICULTY = "difficulty"
    REWARDS = "rewards"
    TIME = "time"
    RESOURCE = "resource"

class TestType(Enum):
    MONTE_CARLO = "monte_carlo"
    DETERMINISTIC = "deterministic"
    STRESS = "stress"
    EDGE_CASE = "edge_case"
    REGRESSION = "regression"
    PERFORMANCE = "performance"

class OptimizationMethod(Enum):
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    GRADIENT_DESCENT = "gradient_descent"
    PARTICLE_SWARM = "particle_swarm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    BRUTE_FORCE = "brute_force"

@dataclass
class BalanceParameter:
    """Parameter to be balanced"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    weight: float = 1.0
    parameter_type: str = "linear"  # linear, exponential, logarithmic
    category: BalanceType = BalanceType.COMBAT

@dataclass
class BalanceMetric:
    """Metric to measure balance"""
    name: str
    target_value: float
    tolerance: float = 0.1
    weight: float = 1.0
    measurement_function: Optional[Callable] = None

@dataclass
class TestScenario:
    """Test scenario for balance testing"""
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    test_type: TestType
    iterations: int = 1000
    timeout: float = 30.0

@dataclass
class OptimizationResult:
    """Result of optimization process"""
    best_parameters: Dict[str, float]
    best_fitness: float
    iterations: int
    convergence_time: float
    improvement_percentage: float
    recommendations: List[str] = field(default_factory=list)

@dataclass
class BalanceReport:
    """Comprehensive balance analysis report"""
    timestamp: float
    system_name: str
    overall_score: float
    category_scores: Dict[BalanceType, float]
    identified_issues: List[Dict[str, Any]]
    recommendations: List[str]
    test_results: Dict[str, Any]
    optimization_suggestions: Dict[str, Any]

class BalanceOptimizer:
    """Main balance optimization system"""

    def __init__(self):
        self.parameters: Dict[str, BalanceParameter] = {}
        self.metrics: Dict[str, BalanceMetric] = {}
        self.test_scenarios: Dict[str, TestScenario] = {}
        self.baseline_data: Dict[str, Any] = {}
        self.optimization_history: List[OptimizationResult] = []
        self.current_simulation_data: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.analytics = BalanceAnalytics()

        # Optimization parameters
        self.population_size = 100
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elite_ratio = 0.2
        self.max_iterations = 1000
        self.convergence_threshold = 0.001
        self.simulation_runs = 1000

        self._initialize_default_parameters()
        self._initialize_default_metrics()
        self._initialize_test_scenarios()

    def _initialize_default_parameters(self):
        """Initialize default balance parameters"""
        parameters = [
            # Combat parameters
            BalanceParameter("base_damage", 10, 1, 100, weight=2.0, category=BalanceType.COMBAT),
            BalanceParameter("critical_chance", 0.05, 0.0, 1.0, weight=1.5, category=BalanceType.COMBAT),
            BalanceParameter("defense_scaling", 0.8, 0.1, 2.0, weight=1.0, category=BalanceType.COMBAT),
            BalanceParameter("health_scaling", 1.2, 0.5, 3.0, weight=1.5, category=BalanceType.COMBAT),

            # Economy parameters
            BalanceParameter("gold_drop_rate", 1.0, 0.1, 5.0, weight=1.0, category=BalanceType.ECONOMY),
            BalanceParameter("item_value_multiplier", 1.0, 0.5, 3.0, weight=1.0, category=BalanceType.ECONOMY),
            BalanceParameter("repair_cost_factor", 0.1, 0.01, 0.5, weight=0.8, category=BalanceType.ECONOMY),

            # Progression parameters
            BalanceParameter("experience_multiplier", 1.0, 0.5, 2.0, weight=1.5, category=BalanceType.PROGRESSION),
            BalanceParameter("level_up_threshold", 100, 50, 500, weight=1.2, category=BalanceType.PROGRESSION),
            BalanceParameter("skill_point_rate", 1, 1, 5, weight=1.0, category=BalanceType.PROGRESSION),

            # Difficulty parameters
            BalanceParameter("enemy_health_multiplier", 1.0, 0.5, 3.0, weight=1.0, category=BalanceType.DIFFICULTY),
            BalanceParameter("enemy_damage_multiplier", 1.0, 0.5, 3.0, weight=1.2, category=BalanceType.DIFFICULTY),
            BalanceParameter("difficulty_scaling", 1.15, 1.05, 1.5, weight=1.5, category=BalanceType.DIFFICULTY),

            # Reward parameters
            BalanceParameter("quest_reward_multiplier", 1.0, 0.5, 2.0, weight=1.0, category=BalanceType.REWARDS),
            BalanceParameter("rarity_drop_chance", 0.05, 0.01, 0.2, weight=1.2, category=BalanceType.REWARDS),
        ]

        for param in parameters:
            self.parameters[param.name] = param

    def _initialize_default_metrics(self):
        """Initialize default balance metrics"""
        metrics = [
            BalanceMetric("combat_duration", 30, tolerance=10, weight=2.0),
            BalanceMetric("win_rate", 0.7, tolerance=0.2, weight=3.0),
            BalanceMetric("player_satisfaction", 0.8, tolerance=0.15, weight=2.5),
            BalanceMetric("economy_stability", 0.9, tolerance=0.1, weight=2.0),
            BalanceMetric("progression_speed", 1.0, tolerance=0.3, weight=1.5),
            BalanceMetric("difficulty_curve", 1.0, tolerance=0.2, weight=2.0),
            BalanceMetric("reward_satisfaction", 0.75, tolerance=0.15, weight=1.8),
            BalanceMetric("player_retention", 0.8, tolerance=0.1, weight=3.0),
        ]

        for metric in metrics:
            self.metrics[metric.name] = metric

    def _initialize_test_scenarios(self):
        """Initialize test scenarios"""
        scenarios = [
            TestScenario(
                id="low_level_combat",
                name="Low Level Combat Balance",
                description="Test combat balance for levels 1-10",
                parameters={
                    "player_level": 5,
                    "enemy_level": 5,
                    "gear_quality": "common"
                },
                expected_outcomes={
                    "combat_duration": 15,
                    "win_rate": 0.8,
                    "resource_usage": 0.3
                },
                test_type=TestType.MONTE_CARLO,
                iterations=5000
            ),
            TestScenario(
                id="high_level_raid",
                name="High Level Raid Balance",
                description="Test raid balance for max level players",
                parameters={
                    "player_level": 50,
                    "raid_difficulty": "hard",
                    "group_size": 10
                },
                expected_outcomes={
                    "combat_duration": 600,
                    "success_rate": 0.3,
                    "coordination_requirement": 0.8
                },
                test_type=TestType.STRESS,
                iterations=1000
            ),
            TestScenario(
                id="economy_simulation",
                name="Economy Stability Test",
                description="Test economic balance over extended play",
                parameters={
                    "simulation_days": 30,
                    "player_count": 1000,
                    "activity_level": "normal"
                },
                expected_outcomes={
                    "inflation_rate": 0.05,
                    "wealth_distribution": "normal",
                    "market_stability": 0.9
                },
                test_type=TestType.DETERMINISTIC,
                iterations=100
            )
        ]

        for scenario in scenarios:
            self.test_scenarios[scenario.id] = scenario

    def run_comprehensive_balance_test(self) -> BalanceReport:
        """Run comprehensive balance analysis"""
        start_time = time.time()
        print("Starting comprehensive balance test...")

        # Run all test scenarios
        test_results = {}
        for scenario_id, scenario in self.test_scenarios.items():
            print(f"Running test scenario: {scenario.name}")
            result = self.run_test_scenario(scenario)
            test_results[scenario_id] = result

        # Analyze category balance
        category_scores = self.analyze_category_balance()

        # Identify issues
        identified_issues = self.identify_balance_issues(test_results, category_scores)

        # Generate recommendations
        recommendations = self.generate_balance_recommendations(identified_issues, category_scores)

        # Calculate overall score
        overall_score = sum(category_scores.values()) / len(category_scores) if category_scores else 0

        # Generate optimization suggestions
        optimization_suggestions = self.generate_optimization_suggestions()

        report = BalanceReport(
            timestamp=time.time(),
            system_name="DMLogn8n Game Balance",
            overall_score=overall_score,
            category_scores=category_scores,
            identified_issues=identified_issues,
            recommendations=recommendations,
            test_results=test_results,
            optimization_suggestions=optimization_suggestions
        )

        self.analytics.record_balance_test(report)
        print(f"Comprehensive balance test completed in {time.time() - start_time:.2f} seconds")

        return report

    def run_test_scenario(self, scenario: TestScenario) -> Dict[str, Any]:
        """Run a specific test scenario"""
        results = {
            "scenario_id": scenario.id,
            "iterations_completed": 0,
            "outcomes": defaultdict(list),
            "performance_metrics": {},
            "issues_found": []
        }

        try:
            if scenario.test_type == TestType.MONTE_CARLO:
                results.update(self.run_monte_carlo_test(scenario))
            elif scenario.test_type == TestType.DETERMINISTIC:
                results.update(self.run_deterministic_test(scenario))
            elif scenario.test_type == TestType.STRESS:
                results.update(self.run_stress_test(scenario))
            elif scenario.test_type == TestType.EDGE_CASE:
                results.update(self.run_edge_case_test(scenario))

        except Exception as e:
            results["error"] = str(e)
            results["issues_found"].append(f"Test execution error: {e}")

        return results

    def run_monte_carlo_test(self, scenario: TestScenario) -> Dict[str, Any]:
        """Run Monte Carlo simulation"""
        outcomes = defaultdict(list)
        start_time = time.time()

        for iteration in range(scenario.iterations):
            # Simulate with random variations in parameters
            simulated_params = self.simulate_parameter_variations(scenario.parameters)
            result = self.simulate_gameplay(scenario, simulated_params)

            for metric, value in result.items():
                outcomes[metric].append(value)

            # Check timeout
            if time.time() - start_time > scenario.timeout:
                break

        # Calculate statistics
        statistics_results = {}
        for metric, values in outcomes.items():
            if values:
                statistics_results[metric] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }

        return {
            "outcomes": dict(outcomes),
            "statistics": statistics_results,
            "iterations_completed": len(outcomes.get(list(outcomes.keys())[0], []))
        }

    def run_deterministic_test(self, scenario: TestScenario) -> Dict[str, Any]:
        """Run deterministic test with fixed parameters"""
        results = self.simulate_gameplay(scenario, scenario.parameters)
        return {"outcomes": results, "deterministic": True}

    def run_stress_test(self, scenario: TestScenario) -> Dict[str, Any]:
        """Run stress test with extreme parameter values"""
        stress_results = []

        # Test with minimum parameters
        min_params = {k: v * 0.1 for k, v in scenario.parameters.items() if isinstance(v, (int, float))}
        min_result = self.simulate_gameplay(scenario, min_params)
        stress_results.append(("minimum", min_result))

        # Test with maximum parameters
        max_params = {k: v * 10 for k, v in scenario.parameters.items() if isinstance(v, (int, float))}
        max_result = self.simulate_gameplay(scenario, max_params)
        stress_results.append(("maximum", max_result))

        return {"stress_results": stress_results}

    def run_edge_case_test(self, scenario: TestScenario) -> Dict[str, Any]:
        """Run edge case tests"""
        edge_cases = [
            ("zero_values", {k: 0 for k, v in scenario.parameters.items() if isinstance(v, (int, float))}),
            ("max_values", {k: 1000 for k, v in scenario.parameters.items() if isinstance(v, (int, float))}),
            ("negative_values", {k: -v for k, v in scenario.parameters.items() if isinstance(v, (int, float))})
        ]

        results = {}
        for case_name, params in edge_cases:
            try:
                result = self.simulate_gameplay(scenario, params)
                results[case_name] = result
            except Exception as e:
                results[case_name] = {"error": str(e)}

        return {"edge_cases": results}

    def simulate_parameter_variations(self, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate random variations in parameters"""
        varied_params = base_params.copy()

        for param_name, param_obj in self.parameters.items():
            if param_name in varied_params:
                # Add random variation within bounds
                variation_range = (param_obj.max_value - param_obj.min_value) * 0.1
                variation = random.uniform(-variation_range, variation_range)
                varied_params[param_name] = max(param_obj.min_value,
                                              min(param_obj.max_value,
                                                  varied_params[param_name] + variation))

        return varied_params

    def simulate_gameplay(self, scenario: TestScenario, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate gameplay with given parameters"""
        # This is a simplified simulation - in a real system, this would
        # integrate with the actual game systems

        results = {}

        if "combat_duration" in scenario.expected_outcomes:
            # Simulate combat duration based on damage and health parameters
            base_damage = parameters.get("base_damage", self.parameters["base_damage"].current_value)
            defense_scaling = parameters.get("defense_scaling", self.parameters["defense_scaling"].current_value)

            # Simplified combat calculation
            effective_damage = base_damage * (1 - defense_scaling * 0.3)
            combat_duration = max(1, 100 / effective_damage)  # Simplified formula
            results["combat_duration"] = combat_duration + random.gauss(0, combat_duration * 0.1)

        if "win_rate" in scenario.expected_outcomes:
            # Simulate win rate based on various parameters
            power_ratio = parameters.get("base_damage", 10) / (parameters.get("enemy_health_multiplier", 1) * 50)
            win_rate = max(0, min(1, 0.5 + power_ratio * 0.3 + random.gauss(0, 0.1)))
            results["win_rate"] = win_rate

        if "economy_stability" in scenario.expected_outcomes:
            # Simulate economy based on gold and value parameters
            gold_rate = parameters.get("gold_drop_rate", 1.0)
            value_mult = parameters.get("item_value_multiplier", 1.0)
            stability = max(0, min(1, 1 - abs(gold_rate * value_mult - 1) * 0.5))
            results["economy_stability"] = stability

        if "player_satisfaction" in scenario.expected_outcomes:
            # Simulate player satisfaction based on multiple factors
            reward_mult = parameters.get("quest_reward_multiplier", 1.0)
            difficulty_mult = parameters.get("enemy_damage_multiplier", 1.0)
            satisfaction = max(0, min(1, 0.7 + reward_mult * 0.2 - difficulty_mult * 0.1 + random.gauss(0, 0.05)))
            results["player_satisfaction"] = satisfaction

        return results

    def analyze_category_balance(self) -> Dict[BalanceType, float]:
        """Analyze balance for each category"""
        category_scores = {}

        for category in BalanceType:
            category_params = [p for p in self.parameters.values() if p.category == category]
            if not category_params:
                continue

            # Calculate category-specific metrics
            score = self.calculate_category_score(category, category_params)
            category_scores[category] = score

        return category_scores

    def calculate_category_score(self, category: BalanceType, parameters: List[BalanceParameter]) -> float:
        """Calculate balance score for a category"""
        if category == BalanceType.COMBAT:
            # Combat balance: damage vs health vs defense
            damage = self.parameters["base_damage"].current_value
            defense = self.parameters["defense_scaling"].current_value
            health = self.parameters["health_scaling"].current_value

            # Ideal ratio: damage should overcome defense at reasonable rate
            balance_score = 1.0 - abs(damage * (1 - defense * 0.3) - health * 0.1) / (damage + health)
            return max(0, min(1, balance_score))

        elif category == BalanceType.ECONOMY:
            # Economy balance: income vs expenses
            gold_rate = self.parameters["gold_drop_rate"].current_value
            repair_cost = self.parameters["repair_cost_factor"].current_value

            # Ideal: gold income should exceed repair costs
            balance_score = min(1.0, gold_rate / (repair_cost * 10))
            return max(0, balance_score)

        elif category == BalanceType.DIFFICULTY:
            # Difficulty balance: challenge vs frustration
            enemy_health = self.parameters["enemy_health_multiplier"].current_value
            enemy_damage = self.parameters["enemy_damage_multiplier"].current_value

            # Ideal: challenging but not impossible
            balance_score = 1.0 - abs((enemy_health + enemy_damage) / 2 - 1.5) / 1.5
            return max(0, min(1, balance_score))

        # Default calculation for other categories
        total_weight = sum(p.weight for p in parameters)
        weighted_sum = sum(p.weight * (p.current_value - p.min_value) / (p.max_value - p.min_value) for p in parameters)
        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def identify_balance_issues(self, test_results: Dict[str, Any], category_scores: Dict[BalanceType, float]) -> List[Dict[str, Any]]:
        """Identify balance issues from test results"""
        issues = []

        # Check category scores
        for category, score in category_scores.items():
            if score < 0.3:
                issues.append({
                    "type": "category_imbalance",
                    "category": category.value,
                    "severity": "high",
                    "score": score,
                    "description": f"{category.value} category is severely imbalanced (score: {score:.2f})"
                })
            elif score < 0.6:
                issues.append({
                    "type": "category_imbalance",
                    "category": category.value,
                    "severity": "medium",
                    "score": score,
                    "description": f"{category.value} category needs adjustment (score: {score:.2f})"
                })

        # Check test results against expected outcomes
        for scenario_id, result in test_results.items():
            if "statistics" in result:
                scenario = self.test_scenarios[scenario_id]
                for metric, expected in scenario.expected_outcomes.items():
                    if metric in result["statistics"]:
                        actual_mean = result["statistics"][metric]["mean"]
                        deviation = abs(actual_mean - expected) / expected if expected != 0 else 1

                        if deviation > 0.5:  # 50% deviation
                            issues.append({
                                "type": "metric_deviation",
                                "scenario": scenario_id,
                                "metric": metric,
                                "expected": expected,
                                "actual": actual_mean,
                                "deviation": deviation,
                                "severity": "high" if deviation > 1.0 else "medium"
                            })

        return issues

    def generate_balance_recommendations(self, issues: List[Dict[str, Any]], category_scores: Dict[BalanceType, float]) -> List[str]:
        """Generate balance improvement recommendations"""
        recommendations = []

        for issue in issues:
            if issue["type"] == "category_imbalance":
                category = issue["category"]
                score = issue["score"]

                if category == "combat":
                    if score < 0.5:
                        recommendations.append("Adjust base_damage and defense_scaling to improve combat balance")
                        recommendations.append("Consider tweaking critical_chance for more varied combat")
                elif category == "economy":
                    if score < 0.5:
                        recommendations.append("Balance gold_drop_rate against repair_cost_factor")
                        recommendations.append("Review item_value_multiplier to prevent inflation")
                elif category == "difficulty":
                    if score < 0.5:
                        recommendations.append("Adjust enemy_health_multiplier and enemy_damage_multiplier")
                        recommendations.append("Consider scaling difficulty more gradually")

            elif issue["type"] == "metric_deviation":
                metric = issue["metric"]
                scenario = issue["scenario"]

                if metric == "combat_duration":
                    if issue["actual"] > issue["expected"]:
                        recommendations.append(f"Increase base_damage or reduce enemy health in {scenario}")
                    else:
                        recommendations.append(f"Decrease base_damage or increase enemy health in {scenario}")
                elif metric == "win_rate":
                    if issue["actual"] < issue["expected"]:
                        recommendations.append(f"Reduce difficulty parameters in {scenario}")
                    else:
                        recommendations.append(f"Increase difficulty parameters in {scenario}")

        # General recommendations
        low_scoring_categories = [cat for cat, score in category_scores.items() if score < 0.6]
        if low_scoring_categories:
            recommendations.append(f"Focus improvements on: {', '.join(cat.value for cat in low_scoring_categories)}")

        return recommendations

    def optimize_parameters(self, target_metrics: Dict[str, float], method: OptimizationMethod = OptimizationMethod.GENETIC_ALGORITHM) -> OptimizationResult:
        """Optimize parameters to achieve target metrics"""
        print(f"Starting parameter optimization using {method.value}...")

        if method == OptimizationMethod.GENETIC_ALGORITHM:
            result = self.genetic_algorithm_optimization(target_metrics)
        elif method == OptimizationMethod.SIMULATED_ANNEALING:
            result = self.simulated_annealing_optimization(target_metrics)
        elif method == OptimizationMethod.GRADIENT_DESCENT:
            result = self.gradient_descent_optimization(target_metrics)
        else:
            result = self.genetic_algorithm_optimization(target_metrics)  # Default

        self.optimization_history.append(result)
        print(f"Optimization completed. Best fitness: {result.best_fitness:.4f}")

        return result

    def genetic_algorithm_optimization(self, target_metrics: Dict[str, float]) -> OptimizationResult:
        """Genetic algorithm optimization"""
        start_time = time.time()

        # Initialize population
        population = self.initialize_population()
        best_fitness = float('inf')
        best_individual = None

        for generation in range(self.max_iterations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                fitness = self.calculate_fitness(individual, target_metrics)
                fitness_scores.append(fitness)

                if fitness < best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()

            # Check convergence
            if best_fitness < self.convergence_threshold:
                break

            # Selection, crossover, and mutation
            population = self.evolve_population(population, fitness_scores)

        # Calculate improvement
        baseline_fitness = self.calculate_fitness(
            {name: param.current_value for name, param in self.parameters.items()},
            target_metrics
        )
        improvement = ((baseline_fitness - best_fitness) / baseline_fitness) * 100 if baseline_fitness > 0 else 0

        return OptimizationResult(
            best_parameters=best_individual,
            best_fitness=best_fitness,
            iterations=generation + 1,
            convergence_time=time.time() - start_time,
            improvement_percentage=improvement,
            recommendations=self.generate_optimization_recommendations(best_individual)
        )

    def initialize_population(self) -> List[Dict[str, float]]:
        """Initialize genetic algorithm population"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for name, param in self.parameters.items():
                individual[name] = random.uniform(param.min_value, param.max_value)
            population.append(individual)
        return population

    def evolve_population(self, population: List[Dict[str, float]], fitness_scores: List[float]) -> List[Dict[str, float]]:
        """Evolve population through selection, crossover, and mutation"""
        # Elitism: keep best individuals
        elite_count = int(self.population_size * self.elite_ratio)
        sorted_population = [x for _, x in sorted(zip(fitness_scores, population), key=lambda pair: pair[0])]
        new_population = sorted_population[:elite_count]

        # Generate new individuals
        while len(new_population) < self.population_size:
            # Selection
            parent1, parent2 = self.tournament_selection(population, fitness_scores), \
                             self.tournament_selection(population, fitness_scores)

            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self.crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # Mutation
            self.mutate(child1)
            self.mutate(child2)

            new_population.extend([child1, child2])

        return new_population[:self.population_size]

    def tournament_selection(self, population: List[Dict[str, float]], fitness_scores: List[float], tournament_size: int = 3) -> Dict[str, float]:
        """Tournament selection for genetic algorithm"""
        tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[tournament_fitness.index(min(tournament_fitness))]
        return population[winner_index].copy()

    def crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Crossover operation for genetic algorithm"""
        child1, child2 = {}, {}
        for name in self.parameters.keys():
            if random.random() < 0.5:
                child1[name] = parent1[name]
                child2[name] = parent2[name]
            else:
                child1[name] = parent2[name]
                child2[name] = parent1[name]
        return child1, child2

    def mutate(self, individual: Dict[str, float]):
        """Mutation operation for genetic algorithm"""
        for name, param in self.parameters.items():
            if random.random() < self.mutation_rate:
                mutation_range = (param.max_value - param.min_value) * 0.1
                individual[name] = max(param.min_value,
                                      min(param.max_value,
                                          individual[name] + random.uniform(-mutation_range, mutation_range)))

    def calculate_fitness(self, individual: Dict[str, float], target_metrics: Dict[str, float]) -> float:
        """Calculate fitness function for optimization"""
        total_error = 0

        # Simulate with the individual's parameters
        for scenario_id, scenario in self.test_scenarios.items():
            # Override parameters with individual's values
            test_params = scenario.parameters.copy()
            for name, value in individual.items():
                if name in test_params:
                    test_params[name] = value

            result = self.simulate_gameplay(scenario, test_params)

            # Calculate error against target metrics
            for metric, target_value in target_metrics.items():
                if metric in result:
                    error = abs(result[metric] - target_value)
                    if metric in self.metrics:
                        weight = self.metrics[metric].weight
                        total_error += error * weight

        return total_error

    def generate_optimization_suggestions(self) -> Dict[str, Any]:
        """Generate optimization suggestions based on current state"""
        suggestions = {
            "priority_adjustments": [],
            "parameter_correlations": [],
            "sensitivity_analysis": {}
        }

        # Identify parameters that need most adjustment
        for name, param in self.parameters.items():
            current = param.current_value
            optimal = (param.min_value + param.max_value) / 2  # Simplified optimal
            deviation = abs(current - optimal) / (param.max_value - param.min_value)

            if deviation > 0.3:
                suggestions["priority_adjustments"].append({
                    "parameter": name,
                    "current_value": current,
                    "suggested_range": (optimal * 0.9, optimal * 1.1),
                    "priority": "high" if deviation > 0.5 else "medium"
                })

        # Sensitivity analysis
        for param_name in self.parameters.keys():
            sensitivity = self.calculate_parameter_sensitivity(param_name)
            suggestions["sensitivity_analysis"][param_name] = sensitivity

        return suggestions

    def calculate_parameter_sensitivity(self, param_name: str) -> float:
        """Calculate sensitivity of a parameter"""
        if param_name not in self.parameters:
            return 0.0

        base_value = self.parameters[param_name].current_value
        test_range = (self.parameters[param_name].max_value - self.parameters[param_name].min_value) * 0.1

        # Test small variations
        variations = [-test_range, 0, test_range]
        results = []

        for variation in variations:
            test_params = {name: param.current_value for name, param in self.parameters.items()}
            test_params[param_name] = base_value + variation

            # Run quick test
            total_result = 0
            for scenario in list(self.test_scenarios.values())[:2]:  # Test first 2 scenarios
                result = self.simulate_gameplay(scenario, test_params)
                total_result += sum(result.values()) if result else 0

            results.append(total_result)

        # Calculate sensitivity as rate of change
        if len(results) >= 3:
            sensitivity = abs(results[2] - results[0]) / (2 * test_range) if test_range != 0 else 0
            return sensitivity

        return 0.0

    def generate_optimization_recommendations(self, best_parameters: Dict[str, float]) -> List[str]:
        """Generate recommendations based on optimization results"""
        recommendations = []

        for name, optimal_value in best_parameters.items():
            if name in self.parameters:
                current_value = self.parameters[name].current_value
                change_percent = abs(optimal_value - current_value) / current_value * 100 if current_value != 0 else 0

                if change_percent > 10:
                    direction = "increase" if optimal_value > current_value else "decrease"
                    recommendations.append(f"{direction} {name} from {current_value:.2f} to {optimal_value:.2f} ({change_percent:.1f}% change)")

        return recommendations

    def simulated_annealing_optimization(self, target_metrics: Dict[str, float]) -> OptimizationResult:
        """Simulated annealing optimization"""
        # Simplified implementation
        start_time = time.time()
        current_solution = {name: param.current_value for name, param in self.parameters.items()}
        current_fitness = self.calculate_fitness(current_solution, target_metrics)
        best_solution = current_solution.copy()
        best_fitness = current_fitness

        temperature = 100.0
        cooling_rate = 0.95

        for iteration in range(self.max_iterations):
            # Generate neighbor solution
            neighbor = current_solution.copy()
            param_to_modify = random.choice(list(self.parameters.keys()))
            param = self.parameters[param_to_modify]
            neighbor[param_to_modify] = random.uniform(param.min_value, param.max_value)

            neighbor_fitness = self.calculate_fitness(neighbor, target_metrics)

            # Accept or reject
            if neighbor_fitness < current_fitness or random.random() < math.exp((current_fitness - neighbor_fitness) / temperature):
                current_solution = neighbor
                current_fitness = neighbor_fitness

                if current_fitness < best_fitness:
                    best_solution = current_solution.copy()
                    best_fitness = current_fitness

            temperature *= cooling_rate

            if temperature < 0.001:
                break

        baseline_fitness = self.calculate_fitness(
            {name: param.current_value for name, param in self.parameters.items()},
            target_metrics
        )
        improvement = ((baseline_fitness - best_fitness) / baseline_fitness) * 100 if baseline_fitness > 0 else 0

        return OptimizationResult(
            best_parameters=best_solution,
            best_fitness=best_fitness,
            iterations=iteration + 1,
            convergence_time=time.time() - start_time,
            improvement_percentage=improvement
        )

    def gradient_descent_optimization(self, target_metrics: Dict[str, float]) -> OptimizationResult:
        """Gradient descent optimization"""
        # Simplified implementation
        start_time = time.time()
        current_solution = {name: param.current_value for name, param in self.parameters.items()}
        learning_rate = 0.01

        for iteration in range(self.max_iterations):
            gradient = self.calculate_gradient(current_solution, target_metrics)

            for name, grad_value in gradient.items():
                if name in current_solution:
                    param = self.parameters[name]
                    current_solution[name] = max(param.min_value,
                                              min(param.max_value,
                                                  current_solution[name] - learning_rate * grad_value))

            if iteration % 100 == 0:
                fitness = self.calculate_fitness(current_solution, target_metrics)
                if fitness < self.convergence_threshold:
                    break

        final_fitness = self.calculate_fitness(current_solution, target_metrics)
        baseline_fitness = self.calculate_fitness(
            {name: param.current_value for name, param in self.parameters.items()},
            target_metrics
        )
        improvement = ((baseline_fitness - final_fitness) / baseline_fitness) * 100 if baseline_fitness > 0 else 0

        return OptimizationResult(
            best_parameters=current_solution,
            best_fitness=final_fitness,
            iterations=iteration + 1,
            convergence_time=time.time() - start_time,
            improvement_percentage=improvement
        )

    def calculate_gradient(self, solution: Dict[str, float], target_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate gradient for gradient descent optimization"""
        gradient = {}
        epsilon = 0.001

        for name in self.parameters.keys():
            if name in solution:
                # Calculate numerical gradient
                original_value = solution[name]

                # Forward difference
                solution[name] = original_value + epsilon
                fitness_plus = self.calculate_fitness(solution, target_metrics)

                # Backward difference
                solution[name] = original_value - epsilon
                fitness_minus = self.calculate_fitness(solution, target_metrics)

                # Restore original value
                solution[name] = original_value

                gradient[name] = (fitness_plus - fitness_minus) / (2 * epsilon)

        return gradient

    def export_balance_report(self, report: BalanceReport, filename: str = None) -> str:
        """Export balance report to file"""
        if filename is None:
            filename = f"balance_report_{int(report.timestamp)}.json"

        report_data = {
            "timestamp": report.timestamp,
            "system_name": report.system_name,
            "overall_score": report.overall_score,
            "category_scores": {cat.value: score for cat, score in report.category_scores.items()},
            "identified_issues": report.identified_issues,
            "recommendations": report.recommendations,
            "test_results": report.test_results,
            "optimization_suggestions": report.optimization_suggestions
        }

        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        return filename

class BalanceAnalytics:
    """Analytics for balance optimization system"""

    def __init__(self):
        self.test_history = []
        self.optimization_history = []
        self.performance_metrics = defaultdict(list)

    def record_balance_test(self, report: BalanceReport):
        """Record balance test results"""
        self.test_history.append({
            "timestamp": report.timestamp,
            "overall_score": report.overall_score,
            "issues_count": len(report.identified_issues),
            "category_scores": {cat.value: score for cat, score in report.category_scores.items()}
        })

    def record_optimization(self, result: OptimizationResult):
        """Record optimization results"""
        self.optimization_history.append({
            "timestamp": time.time(),
            "best_fitness": result.best_fitness,
            "iterations": result.iterations,
            "convergence_time": result.convergence_time,
            "improvement_percentage": result.improvement_percentage
        })

    def get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends over time"""
        if not self.test_history:
            return {"message": "No test history available"}

        scores_over_time = [test["overall_score"] for test in self.test_history]

        return {
            "total_tests": len(self.test_history),
            "average_score": sum(scores_over_time) / len(scores_over_time),
            "score_trend": "improving" if len(scores_over_time) > 1 and scores_over_time[-1] > scores_over_time[0] else "stable",
            "best_score": max(scores_over_time),
            "worst_score": min(scores_over_time),
            "recent_tests": scores_over_time[-10:]  # Last 10 tests
        }

# Export main classes
__all__ = [
    'BalanceOptimizer',
    'BalanceParameter',
    'BalanceMetric',
    'TestScenario',
    'OptimizationResult',
    'BalanceReport',
    'BalanceAnalytics'
]