#!/usr/bin/env python3
"""
Neural Evolution and Architecture Optimization
Implements evolutionary strategies for neural network optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
import copy
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from collections import defaultdict
import math
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GenomeConfig:
    """Configuration for neural genome"""
    input_size: int
    output_size: int
    max_hidden_layers: int = 5
    max_neurons_per_layer: int = 512
    min_neurons_per_layer: int = 16
    activation_functions: List[str] = None
    use_batch_norm: bool = True
    use_dropout: bool = True
    dropout_rate_range: Tuple[float, float] = (0.0, 0.5)
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_fraction: float = 0.2

    def __post_init__(self):
        if self.activation_functions is None:
            self.activation_functions = ['relu', 'tanh', 'sigmoid', 'gelu', 'swish']

class NeuralGene:
    """Represents a single gene in neural network architecture"""

    def __init__(self, gene_type: str, **params):
        self.gene_type = gene_type
        self.params = params
        self.enabled = True
        self.innovation_number = None  # For NEAT-style tracking

    def mutate(self, mutation_rate: float):
        """Mutate gene parameters"""
        if random.random() < mutation_rate:
            # Random parameter mutation
            for key, value in self.params.items():
                if isinstance(value, (int, float)):
                    # Gaussian mutation
                    if key == 'neurons':
                        self.params[key] = max(1, int(np.random.normal(value, value * 0.2)))
                    elif key == 'dropout_rate':
                        self.params[key] = np.clip(np.random.normal(value, 0.1), 0.0, 0.9)
                    else:
                        self.params[key] = value * np.random.normal(1.0, 0.1)

    def crossover(self, other: 'NeuralGene') -> 'NeuralGene':
        """Crossover with another gene"""
        if random.random() < 0.5:
            return copy.deepcopy(self)
        else:
            return copy.deepcopy(other)

    def __str__(self):
        return f"{self.gene_type}: {self.params}"

class NeuralGenome:
    """Represents a complete neural network architecture"""

    def __init__(self, config: GenomeConfig):
        self.config = config
        self.genes = []
        self.fitness = None
        self.age = 0
        self.generation = 0

        # Initialize random architecture
        self._initialize_random_architecture()

    def _initialize_random_architecture(self):
        """Initialize random neural network architecture"""
        self.genes = []

        # Number of hidden layers
        num_layers = random.randint(1, self.config.max_hidden_layers)

        # Layer genes
        current_size = self.config.input_size
        for i in range(num_layers):
            # Random number of neurons
            neurons = random.randint(
                self.config.min_neurons_per_layer,
                self.config.max_neurons_per_layer
            )

            # Random activation function
            activation = random.choice(self.config.activation_functions)

            # Batch normalization
            use_batch_norm = self.config.use_batch_norm and random.random() < 0.5

            # Dropout
            use_dropout = self.config.use_dropout and random.random() < 0.5
            dropout_rate = 0.0
            if use_dropout:
                dropout_rate = random.uniform(*self.config.dropout_rate_range)

            # Create layer gene
            layer_gene = NeuralGene(
                'layer',
                layer_index=i,
                input_size=current_size,
                output_size=neurons,
                activation=activation,
                use_batch_norm=use_batch_norm,
                use_dropout=use_dropout,
                dropout_rate=dropout_rate
            )

            self.genes.append(layer_gene)
            current_size = neurons

        # Output layer
        output_gene = NeuralGene(
            'output',
            input_size=current_size,
            output_size=self.config.output_size,
            activation='linear'  # Typically linear for regression or softmax handled separately
        )
        self.genes.append(output_gene)

    def mutate(self):
        """Mutate the genome"""
        for gene in self.genes:
            if random.random() < self.config.mutation_rate:
                gene.mutate(self.config.mutation_rate)

        # Structural mutations
        if random.random() < self.config.mutation_rate:
            self._structural_mutation()

    def _structural_mutation(self):
        """Perform structural mutations"""
        mutation_type = random.choice(['add_layer', 'remove_layer', 'modify_layer'])

        if mutation_type == 'add_layer' and len(self.genes) < self.config.max_hidden_layers + 1:
            self._add_layer_mutation()
        elif mutation_type == 'remove_layer' and len(self.genes) > 2:  # Keep at least input and output
            self._remove_layer_mutation()
        elif mutation_type == 'modify_layer':
            self._modify_layer_mutation()

    def _add_layer_mutation(self):
        """Add a new hidden layer"""
        # Find position to insert (not before output layer)
        insert_pos = random.randint(1, len(self.genes) - 1)

        # Get input size for new layer
        if insert_pos == 0:
            input_size = self.config.input_size
        else:
            input_size = self.genes[insert_pos - 1].params['output_size']

        # Get output size for new layer
        output_size = self.genes[insert_pos].params['input_size']

        # Create new layer
        new_layer = NeuralGene(
            'layer',
            layer_index=insert_pos,
            input_size=input_size,
            output_size=output_size,
            activation=random.choice(self.config.activation_functions),
            use_batch_norm=self.config.use_batch_norm and random.random() < 0.5,
            use_dropout=self.config.use_dropout and random.random() < 0.5,
            dropout_rate=random.uniform(*self.config.dropout_rate_range) if self.config.use_dropout else 0.0
        )

        # Update subsequent layer input sizes
        self.genes.insert(insert_pos, new_layer)
        for i in range(insert_pos + 1, len(self.genes)):
            self.genes[i].params['input_size'] = self.genes[i - 1].params['output_size']
            if 'layer_index' in self.genes[i].params:
                self.genes[i].params['layer_index'] = i

    def _remove_layer_mutation(self):
        """Remove a hidden layer"""
        # Don't remove input or output layer
        if len(self.genes) <= 2:
            return

        # Choose a hidden layer to remove
        remove_pos = random.randint(1, len(self.genes) - 2)

        # Update previous layer output size
        if remove_pos > 0:
            self.genes[remove_pos - 1].params['output_size'] = self.genes[remove_pos + 1].params['input_size']

        # Remove the layer
        self.genes.pop(remove_pos)

        # Update layer indices
        for i in range(remove_pos, len(self.genes)):
            if 'layer_index' in self.genes[i].params:
                self.genes[i].params['layer_index'] = i

    def _modify_layer_mutation(self):
        """Modify an existing layer"""
        if len(self.genes) <= 2:
            return

        # Choose a hidden layer to modify
        modify_pos = random.randint(1, len(self.genes) - 2)
        gene = self.genes[modify_pos]

        # Modify one parameter
        modifications = ['neurons', 'activation', 'batch_norm', 'dropout']
        modification = random.choice(modifications)

        if modification == 'neurons':
            new_neurons = random.randint(
                self.config.min_neurons_per_layer,
                self.config.max_neurons_per_layer
            )
            gene.params['output_size'] = new_neurons
            # Update next layer input size
            if modify_pos < len(self.genes) - 1:
                self.genes[modify_pos + 1].params['input_size'] = new_neurons

        elif modification == 'activation':
            gene.params['activation'] = random.choice(self.config.activation_functions)

        elif modification == 'batch_norm':
            gene.params['use_batch_norm'] = not gene.params.get('use_batch_norm', False)

        elif modification == 'dropout':
            gene.params['use_dropout'] = not gene.params.get('use_dropout', False)
            if gene.params['use_dropout']:
                gene.params['dropout_rate'] = random.uniform(*self.config.dropout_rate_range)

    def crossover(self, other: 'NeuralGenome') -> 'NeuralGenome':
        """Crossover with another genome"""
        child = NeuralGenome(self.config)
        child.genes = []

        # Perform crossover for each gene position
        max_genes = max(len(self.genes), len(other.genes))

        for i in range(max_genes):
            if i < len(self.genes) and i < len(other.genes):
                # Both parents have gene at this position
                if random.random() < self.config.crossover_rate:
                    child.genes.append(self.genes[i].crossover(other.genes[i]))
                else:
                    child.genes.append(copy.deepcopy(self.genes[i]))
            elif i < len(self.genes):
                # Only self has gene
                child.genes.append(copy.deepcopy(self.genes[i]))
            elif i < len(other.genes):
                # Only other has gene
                child.genes.append(copy.deepcopy(other.genes[i]))

        # Fix layer connections
        child._fix_layer_connections()

        return child

    def _fix_layer_connections(self):
        """Fix layer input/output sizes after structural changes"""
        for i in range(len(self.genes)):
            if i == 0:
                self.genes[i].params['input_size'] = self.config.input_size
            else:
                self.genes[i].params['input_size'] = self.genes[i - 1].params['output_size']

            if i < len(self.genes) - 1:
                # Not output layer, ensure output size matches next layer input
                self.genes[i].params['output_size'] = self.genes[i + 1].params['input_size']
            else:
                # Output layer
                self.genes[i].params['output_size'] = self.config.output_size

    def build_network(self) -> nn.Module:
        """Build PyTorch network from genome"""
        return EvolvableNetwork(self)

    def get_complexity(self) -> int:
        """Calculate network complexity (number of parameters)"""
        total_params = 0
        for i, gene in enumerate(self.genes):
            if gene.gene_type in ['layer', 'output']:
                input_size = gene.params['input_size']
                output_size = gene.params['output_size']
                total_params += input_size * output_size + output_size  # weights + bias
        return total_params

    def to_dict(self) -> Dict[str, Any]:
        """Convert genome to dictionary for serialization"""
        return {
            'genes': [
                {
                    'gene_type': gene.gene_type,
                    'params': gene.params,
                    'enabled': gene.enabled,
                    'innovation_number': gene.innovation_number
                }
                for gene in self.genes
            ],
            'fitness': self.fitness,
            'age': self.age,
            'generation': self.generation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config: GenomeConfig) -> 'NeuralGenome':
        """Create genome from dictionary"""
        genome = cls(config)
        genome.genes = []

        for gene_data in data['genes']:
            gene = NeuralGene(gene_data['gene_type'], **gene_data['params'])
            gene.enabled = gene_data['enabled']
            gene.innovation_number = gene_data['innovation_number']
            genome.genes.append(gene)

        genome.fitness = data.get('fitness')
        genome.age = data.get('age', 0)
        genome.generation = data.get('generation', 0)

        return genome

class EvolvableNetwork(nn.Module):
    """PyTorch network built from genome"""

    def __init__(self, genome: NeuralGenome):
        super().__init__()
        self.genome = genome
        self.layers = nn.ModuleList()

        self._build_layers()

    def _build_layers(self):
        """Build network layers from genome"""
        for gene in self.genome.genes:
            if not gene.enabled:
                continue

            if gene.gene_type in ['layer', 'output']:
                # Linear layer
                layer = nn.Linear(
                    gene.params['input_size'],
                    gene.params['output_size']
                )
                self.layers.append(layer)

                # Batch normalization
                if gene.params.get('use_batch_norm', False):
                    self.layers.append(nn.BatchNorm1d(gene.params['output_size']))

                # Activation function
                activation = self._get_activation(gene.params['activation'])
                if activation:
                    self.layers.append(activation)

                # Dropout
                if gene.params.get('use_dropout', False):
                    dropout_rate = gene.params.get('dropout_rate', 0.0)
                    self.layers.append(nn.Dropout(dropout_rate))

    def _get_activation(self, activation_name: str) -> Optional[nn.Module]:
        """Get activation function by name"""
        activations = {
            'relu': nn.ReLU(),
            'tanh': nn.Tanh(),
            'sigmoid': nn.Sigmoid(),
            'gelu': nn.GELU(),
            'swish': nn.SiLU(),
            'leaky_relu': nn.LeakyReLU(0.2),
            'elu': nn.ELU(),
            'selu': nn.SELU()
        }
        return activations.get(activation_name.lower())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        for layer in self.layers:
            x = layer(x)
        return x

class EvolutionStrategy:
    """Evolution strategy for optimizing genomes"""

    def __init__(self, config: GenomeConfig, population_size: int = 50):
        self.config = config
        self.population_size = population_size
        self.population = []
        self.generation = 0
        self.best_genome = None
        self.fitness_history = []

        # Initialize population
        self._initialize_population()

    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        for _ in range(self.population_size):
            genome = NeuralGenome(self.config)
            self.population.append(genome)

    def evaluate_population(self, fitness_function: Callable[[nn.Module], float]) -> List[float]:
        """Evaluate fitness of entire population"""
        fitness_scores = []

        for genome in self.population:
            network = genome.build_network()
            fitness = fitness_function(network)
            genome.fitness = fitness
            fitness_scores.append(fitness)

        # Sort population by fitness (descending)
        self.population.sort(key=lambda g: g.fitness or 0, reverse=True)

        # Update best genome
        if self.best_genome is None or self.population[0].fitness > self.best_genome.fitness:
            self.best_genome = copy.deepcopy(self.population[0])

        # Record statistics
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        self.fitness_history.append({
            'generation': self.generation,
            'avg_fitness': avg_fitness,
            'max_fitness': max_fitness,
            'min_fitness': np.min(fitness_scores)
        })

        return fitness_scores

    def evolve_generation(self) -> List[NeuralGenome]:
        """Evolve to next generation"""
        self.generation += 1

        # Select elite individuals
        elite_size = int(self.population_size * self.config.elite_fraction)
        new_population = [copy.deepcopy(genome) for genome in self.population[:elite_size]]

        # Generate offspring through crossover and mutation
        while len(new_population) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            # Crossover
            if random.random() < self.config.crossover_rate:
                child = parent1.crossover(parent2)
            else:
                child = copy.deepcopy(parent1)

            # Mutation
            child.mutate()
            child.generation = self.generation

            new_population.append(child)

        self.population = new_population[:self.population_size]

        # Update age
        for genome in self.population:
            genome.age += 1

        return self.population

    def _tournament_selection(self, tournament_size: int = 3) -> NeuralGenome:
        """Tournament selection"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda g: g.fitness or 0)

    def get_best_network(self) -> nn.Module:
        """Get best network from current population"""
        if self.best_genome:
            return self.best_genome.build_network()
        return self.population[0].build_network()

    def get_diversity(self) -> float:
        """Calculate population diversity"""
        if len(self.population) < 2:
            return 0.0

        # Calculate average pairwise distance
        distances = []
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                distance = self._genome_distance(self.population[i], self.population[j])
                distances.append(distance)

        return np.mean(distances) if distances else 0.0

    def _genome_distance(self, genome1: NeuralGenome, genome2: NeuralGenome) -> float:
        """Calculate distance between two genomes"""
        # Simple distance based on structure differences
        distance = 0.0

        # Layer count difference
        distance += abs(len(genome1.genes) - len(genome2.genes)) * 0.1

        # Parameter differences
        min_genes = min(len(genome1.genes), len(genome2.genes))
        for i in range(min_genes):
            gene1, gene2 = genome1.genes[i], genome2.genes[i]

            # Output size difference
            distance += abs(gene1.params['output_size'] - gene2.params['output_size']) * 0.01

            # Activation function difference
            if gene1.params['activation'] != gene2.params['activation']:
                distance += 0.1

        return distance

class NeuroEvolutionTrainer:
    """Main trainer for neural evolution"""

    def __init__(self, config: GenomeConfig, population_size: int = 50):
        self.config = config
        self.es = EvolutionStrategy(config, population_size)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Training metrics
        self.training_history = []

    def train(self, fitness_function: Callable[[nn.Module], float],
              num_generations: int,
              patience: int = 10,
              target_fitness: Optional[float] = None) -> Dict[str, Any]:
        """Train neural evolution"""
        logger.info(f"Starting neuroevolution training for {num_generations} generations")

        start_time = time.time()
        best_fitness = float('-inf')
        generations_without_improvement = 0

        for generation in range(num_generations):
            # Evaluate population
            fitness_scores = self.es.evaluate_population(fitness_function)
            current_best = max(fitness_scores)

            # Check for improvement
            if current_best > best_fitness:
                best_fitness = current_best
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1

            # Log progress
            avg_fitness = np.mean(fitness_scores)
            diversity = self.es.get_diversity()

            logger.info(
                f"Generation {generation}: "
                f"Best={current_best:.4f}, "
                f"Avg={avg_fitness:.4f}, "
                f"Diversity={diversity:.4f}"
            )

            # Check early stopping
            if generations_without_improvement >= patience:
                logger.info(f"Early stopping at generation {generation} (patience: {patience})")
                break

            # Check target fitness
            if target_fitness and current_best >= target_fitness:
                logger.info(f"Target fitness {target_fitness} reached at generation {generation}")
                break

            # Evolve to next generation
            self.es.evolve_generation()

        training_time = time.time() - start_time

        # Get final results
        best_network = self.es.get_best_network()
        final_fitness = self.es.best_genome.fitness

        results = {
            'best_fitness': final_fitness,
            'best_genome': self.es.best_genome,
            'best_network': best_network,
            'generations': self.es.generation,
            'training_time': training_time,
            'fitness_history': self.es.fitness_history
        }

        logger.info(f"Neuroevolution completed: Best fitness = {final_fitness:.4f}")
        return results

    def save_evolution(self, filepath: str):
        """Save evolution state"""
        data = {
            'config': asdict(self.config),
            'population': [genome.to_dict() for genome in self.es.population],
            'generation': self.es.generation,
            'best_genome': self.es.best_genome.to_dict() if self.es.best_genome else None,
            'fitness_history': self.es.fitness_history
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Evolution state saved to {filepath}")

    def load_evolution(self, filepath: str):
        """Load evolution state"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.config = GenomeConfig(**data['config'])
        self.es.population = [
            NeuralGenome.from_dict(genome_data, self.config)
            for genome_data in data['population']
        ]
        self.es.generation = data['generation']

        if data['best_genome']:
            self.es.best_genome = NeuralGenome.from_dict(data['best_genome'], self.config)

        self.es.fitness_history = data['fitness_history']

        logger.info(f"Evolution state loaded from {filepath}")

class MultiObjectiveEvolution:
    """Multi-objective neural evolution"""

    def __init__(self, config: GenomeConfig, objectives: List[str], population_size: int = 50):
        self.config = config
        self.objectives = objectives
        self.population_size = population_size
        self.es = EvolutionStrategy(config, population_size)
        self.pareto_front = []

    def evaluate_multi_objective(self,
                                objective_functions: Dict[str, Callable[[nn.Module], float]]) -> Dict[str, float]:
        """Evaluate population on multiple objectives"""
        for genome in self.es.population:
            network = genome.build_network()
            objectives_scores = {}

            for obj_name, obj_func in objective_functions.items():
                score = obj_func(network)
                objectives_scores[obj_name] = score

            genome.objectives = objectives_scores
            genome.fitness = self._calculate_pareto_fitness(objectives_scores)

        # Update Pareto front
        self._update_pareto_front()

        return objectives_scores

    def _calculate_pareto_fitness(self, objectives: Dict[str, float]) -> float:
        """Calculate fitness based on Pareto dominance"""
        # Simple aggregation - can be replaced with more sophisticated methods
        return sum(objectives.values()) / len(objectives)

    def _update_pareto_front(self):
        """Update Pareto front"""
        self.pareto_front = []

        for genome in self.es.population:
            if self._is_pareto_optimal(genome):
                self.pareto_front.append(genome)

    def _is_pareto_optimal(self, genome: NeuralGenome) -> bool:
        """Check if genome is Pareto optimal"""
        for other in self.es.population:
            if other != genome and self._dominates(other, genome):
                return False
        return True

    def _dominates(self, genome1: NeuralGenome, genome2: NeuralGenome) -> bool:
        """Check if genome1 dominates genome2"""
        better_in_any = False

        for obj in self.objectives:
            score1 = genome1.objectives[obj]
            score2 = genome2.objectives[obj]

            if score1 < score2:  # Assuming higher is better for all objectives
                return False
            elif score1 > score2:
                better_in_any = True

        return better_in_any

# Utility functions
def create_standard_config(input_size: int, output_size: int) -> GenomeConfig:
    """Create standard configuration for neuroevolution"""
    return GenomeConfig(
        input_size=input_size,
        output_size=output_size,
        max_hidden_layers=5,
        max_neurons_per_layer=256,
        min_neurons_per_layer=16,
        activation_functions=['relu', 'tanh', 'gelu', 'swish'],
        use_batch_norm=True,
        use_dropout=True,
        dropout_rate_range=(0.0, 0.3),
        mutation_rate=0.15,
        crossover_rate=0.7,
        elite_fraction=0.2
    )

def analyze_evolution_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze evolution results"""
    analysis = {
        'final_performance': results['best_fitness'],
        'convergence_generation': None,
        'best_complexity': results['best_genome'].get_complexity(),
        'training_efficiency': results['best_fitness'] / results['generations']
    }

    # Find convergence point
    fitness_history = results['fitness_history']
    if len(fitness_history) > 10:
        # Simple convergence detection
        recent_fitness = [h['max_fitness'] for h in fitness_history[-10:]]
        if max(recent_fitness) - min(recent_fitness) < 0.01 * max(recent_fitness):
            analysis['convergence_generation'] = fitness_history[-10]['generation']

    return analysis

if __name__ == "__main__":
    # Example usage
    config = create_standard_config(input_size=10, output_size=4)

    # Create neuroevolution trainer
    trainer = NeuroEvolutionTrainer(config, population_size=20)

    # Example fitness function (replace with actual evaluation)
    def dummy_fitness_function(network: nn.Module) -> float:
        # Dummy fitness - replace with actual evaluation
        return random.random()

    print("Neural Evolution System initialized!")
    print(f"Input size: {config.input_size}")
    print(f"Output size: {config.output_size}")
    print(f"Population size: {trainer.es.population_size}")
    print(f"Available mutations: add_layer, remove_layer, modify_layer")
    print(f"Available activations: {config.activation_functions}")
    print(f"Multi-objective evolution supported: {MultiObjectiveEvolution.__name__}")