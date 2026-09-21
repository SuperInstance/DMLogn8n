#!/usr/bin/env python3
"""
Synthetic Ecosystem - Balanced Artificial Life Communities
Create balanced artificial ecosystems with complex predator-prey relationships

This system provides:
- Multi-species ecosystem design and simulation
- Complex food web creation and management
- Environmental parameter control and evolution
- Population dynamics with carrying capacity
- Resource competition and niche partitioning
- Symbiotic relationships and mutualism
- Environmental feedback loops
- Ecosystem stability analysis
"""

import numpy as np
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.optimize import minimize

class TrophicLevel(Enum):
    """Trophic levels in ecosystem"""
    PRODUCER = "producer"  # Photosynthetic organisms
    PRIMARY_CONSUMER = "primary_consumer"  # Herbivores
    SECONDARY_CONSUMER = "secondary_consumer"  # Carnivores
    TERTIARY_CONSUMER = "tertiary_consumer"  # Top predators
    DECOMPOSER = "decomposer"  # Decomposers
    SYMBIONT = "symbiont"  # Symbiotic organisms

class MetabolismType(Enum):
    """Metabolic types"""
    PHOTOSYNTHESIS = "photosynthesis"
    CHEMOSYNTHESIS = "chemosynthesis"
    AEROBIC_RESPIRATION = "aerobic_respiration"
    ANAEROBIC_RESPIRATION = "anaerobic_respiration"
    FERMENTATION = "fermentation"
    QUANTUM_METABOLISM = "quantum_metabolism"

class ReproductionStrategy(Enum):
    """Reproduction strategies"""
    ASEXUAL = "asexual"
    SEXUAL = "sexual"
    BUDDING = "budding"
    SPORE_FORMATION = "spore_formation"
    BINARY_FISSION = "binary_fission"
    CONJUGATION = "conjugation"

@dataclass
class EnvironmentalParameters:
    """Environmental conditions"""
    temperature: float  # Celsius
    ph: float
    oxygen_level: float  # percentage
    carbon_dioxide: float  # percentage
    nitrogen: float  # percentage
    phosphorus: float  # percentage
    water_availability: float  # 0-1
    light_intensity: float  # W/m²
    pressure: float  # atm
    radiation_level: float  # mSv/h
    toxic_compounds: Dict[str, float]  # compound -> concentration

@dataclass
class SpeciesTraits:
    """Species characteristics"""
    name: str
    trophic_level: TrophicLevel
    metabolism_type: MetabolismType
    reproduction_strategy: ReproductionStrategy
    size_class: float  # 0-10 (microscopic to large)
    reproduction_rate: float  # per day
    death_rate: float  # per day
    metabolic_efficiency: float  # 0-1
    optimal_temperature: float  # Celsius
    optimal_ph: float
    tolerance_range: float  # environmental tolerance
    resource_requirements: Dict[str, float]
    carrying_capacity_factor: float
    mobility: float  # 0-1
    intelligence: float  # 0-1

@dataclass
class Species:
    """Species in ecosystem"""
    traits: SpeciesTraits
    population: float
    biomass: float  # kg
    age_distribution: List[float]  # age classes
    genetic_diversity: float  # 0-1
    adaptation_score: float  # 0-1
    niche: Set[str]  # ecological niche components

@dataclass
class Interaction:
    """Species interaction"""
    species1: str
    species2: str
    interaction_type: str  # predation, competition, mutualism, commensalism
    strength: float  # 0-1
    direction: str  # bidirectional, species1_to_species2, species2_to_species1
    conditions: Dict[str, float]  # environmental conditions affecting interaction

@dataclass
class EcosystemState:
    """Current state of ecosystem"""
    timestamp: float
    species_populations: Dict[str, float]
    total_biomass: float
    biodiversity_index: float
    stability_index: float
    resource_levels: Dict[str, float]
    environmental_conditions: EnvironmentalParameters

class SyntheticEcosystem:
    """Advanced synthetic ecosystem simulator"""

    def __init__(self):
        # Ecosystem parameters
        self.time_step = 0.1  # days
        self.max_time = 3650  # 10 years
        self.spatial_resolution = 100  # grid cells per dimension

        # Species database
        self.species_database = self._initialize_species_database()

        # Interaction matrices
        self.interaction_types = {
            'predation': {'predator_growth': 0.1, 'prey_mortality': 0.2},
            'competition': {'competition_strength': 0.05},
            'mutualism': {'mutual_benefit': 0.15},
            'commensalism': {'beneficiary_gain': 0.1},
            'amensalism': {'victim_cost': 0.05},
            'parasitism': {'parasite_gain': 0.2, 'host_cost': 0.1}
        }

        # Ecosystem models
        self.population_models = {
            'lotka_volterra': self._lotka_volterra_dynamics,
            'predator_prey': self._predator_prey_dynamics,
            'competition': self._competition_dynamics,
            'mutualism': self._mutualism_dynamics
        }

    def _initialize_species_database(self) -> Dict[str, SpeciesTraits]:
        """Initialize database of synthetic species"""
        return {
            # Producers
            'quantum_algae': SpeciesTraits(
                name='Quantum Algae',
                trophic_level=TrophicLevel.PRODUCER,
                metabolism_type=MetabolismType.PHOTOSYNTHESIS,
                reproduction_strategy=ReproductionStrategy.BINARY_FISSION,
                size_class=1.0,
                reproduction_rate=2.0,
                death_rate=0.1,
                metabolic_efficiency=0.85,
                optimal_temperature=25.0,
                optimal_ph=7.5,
                tolerance_range=3.0,
                resource_requirements={'light': 1.0, 'CO2': 0.8, 'N': 0.3, 'P': 0.05},
                carrying_capacity_factor=1.0,
                mobility=0.1,
                intelligence=0.05
            ),
            'chemo_bacteria': SpeciesTraits(
                name='Chemosynthetic Bacteria',
                trophic_level=TrophicLevel.PRODUCER,
                metabolism_type=MetabolismType.CHEMOSYNTHESIS,
                reproduction_strategy=ReproductionStrategy.BINARY_FISSION,
                size_class=0.5,
                reproduction_rate=1.5,
                death_rate=0.2,
                metabolic_efficiency=0.4,
                optimal_temperature=80.0,
                optimal_ph=2.0,
                tolerance_range=5.0,
                resource_requirements={'H2S': 1.0, 'O2': 0.5, 'CO2': 0.7},
                carrying_capacity_factor=0.8,
                mobility=0.2,
                intelligence=0.01
            ),
            'synthetic_plant': SpeciesTraits(
                name='Synthetic Plant',
                trophic_level=TrophicLevel.PRODUCER,
                metabolism_type=MetabolismType.PHOTOSYNTHESIS,
                reproduction_strategy=ReproductionStrategy.SPORE_FORMATION,
                size_class=5.0,
                reproduction_rate=0.3,
                death_rate=0.05,
                metabolic_efficiency=0.7,
                optimal_temperature=20.0,
                optimal_ph=6.5,
                tolerance_range=2.5,
                resource_requirements={'light': 1.0, 'CO2': 0.9, 'N': 0.4, 'P': 0.1},
                carrying_capacity_factor=0.6,
                mobility=0.0,
                intelligence=0.1
            ),

            # Primary consumers
            'micro_herbivore': SpeciesTraits(
                name='Micro Herbivore',
                trophic_level=TrophicLevel.PRIMARY_CONSUMER,
                metabolism_type=MetabolismType.AEROBIC_RESPIRATION,
                reproduction_strategy=ReproductionStrategy.ASEXUAL,
                size_class=1.5,
                reproduction_rate=0.8,
                death_rate=0.15,
                metabolic_efficiency=0.6,
                optimal_temperature=22.0,
                optimal_ph=7.0,
                tolerance_range=2.0,
                resource_requirements={'plant_matter': 1.0, 'O2': 0.8},
                carrying_capacity_factor=0.7,
                mobility=0.8,
                intelligence=0.2
            ),
            'quantum_grazer': SpeciesTraits(
                name='Quantum Grazer',
                trophic_level=TrophicLevel.PRIMARY_CONSUMER,
                metabolism_type=MetabolismType.QUANTUM_METABOLISM,
                reproduction_strategy=ReproductionStrategy.SEXUAL,
                size_class=3.0,
                reproduction_rate=0.4,
                death_rate=0.08,
                metabolic_efficiency=0.9,
                optimal_temperature=18.0,
                optimal_ph=7.2,
                tolerance_range=1.8,
                resource_requirements={'algae': 1.0, 'O2': 0.9},
                carrying_capacity_factor=0.5,
                mobility=0.9,
                intelligence=0.4
            ),

            # Secondary consumers
            'nano_predator': SpeciesTraits(
                name='Nano Predator',
                trophic_level=TrophicLevel.SECONDARY_CONSUMER,
                metabolism_type=MetabolismType.AEROBIC_RESPIRATION,
                reproduction_strategy=ReproductionStrategy.SEXUAL,
                size_class=2.0,
                reproduction_rate=0.5,
                death_rate=0.12,
                metabolic_efficiency=0.7,
                optimal_temperature=25.0,
                optimal_ph=7.0,
                tolerance_range=2.5,
                resource_requirements={'herbivores': 1.0, 'O2': 0.8},
                carrying_capacity_factor=0.4,
                mobility=0.95,
                intelligence=0.6
            ),
            'synthetic_spider': SpeciesTraits(
                name='Synthetic Spider',
                trophic_level=TrophicLevel.SECONDARY_CONSUMER,
                metabolism_type=MetabolismType.ANAEROBIC_RESPIRATION,
                reproduction_strategy=ReproductionStrategy.SPORE_FORMATION,
                size_class=2.5,
                reproduction_rate=0.6,
                death_rate=0.1,
                metabolic_efficiency=0.5,
                optimal_temperature=28.0,
                optimal_ph=6.8,
                tolerance_range=3.0,
                resource_requirements={'insects': 1.0, 'O2': 0.3},
                carrying_capacity_factor=0.3,
                mobility=0.7,
                intelligence=0.5
            ),

            # Tertiary consumers
            'apex_predator': SpeciesTraits(
                name='Apex Predator',
                trophic_level=TrophicLevel.TERTIARY_CONSUMER,
                metabolism_type=MetabolismType.AEROBIC_RESPIRATION,
                reproduction_strategy=ReproductionStrategy.SEXUAL,
                size_class=7.0,
                reproduction_rate=0.1,
                death_rate=0.03,
                metabolic_efficiency=0.8,
                optimal_temperature=20.0,
                optimal_ph=7.0,
                tolerance_range=2.0,
                resource_requirements={'prey': 1.0, 'O2': 0.9},
                carrying_capacity_factor=0.2,
                mobility=0.98,
                intelligence=0.8
            ),

            # Decomposers
            'quantum_decomposer': SpeciesTraits(
                name='Quantum Decomposer',
                trophic_level=TrophicLevel.DECOMPOSER,
                metabolism_type=MetabolismType.QUANTUM_METABOLISM,
                reproduction_strategy=ReproductionStrategy.BINARY_FISSION,
                size_class=0.8,
                reproduction_rate=1.2,
                death_rate=0.18,
                metabolic_efficiency=0.95,
                optimal_temperature=15.0,
                optimal_ph=6.0,
                tolerance_range=4.0,
                resource_requirements={'organic_matter': 1.0, 'O2': 0.5},
                carrying_capacity_factor=1.2,
                mobility=0.3,
                intelligence=0.1
            ),

            # Symbionts
            'nitrogen_fixer': SpeciesTraits(
                name='Nitrogen Fixing Symbiont',
                trophic_level=TrophicLevel.SYMBIONT,
                metabolism_type=MetabolismType.AEROBIC_RESPIRATION,
                reproduction_strategy=ReproductionStrategy.CONJUGATION,
                size_class=0.3,
                reproduction_rate=0.9,
                death_rate=0.2,
                metabolic_efficiency=0.3,
                optimal_temperature=22.0,
                optimal_ph=7.5,
                tolerance_range=3.5,
                resource_requirements={'N2': 1.0, 'host_carbon': 0.3},
                carrying_capacity_factor=1.5,
                mobility=0.4,
                intelligence=0.05
            )
        }

    def create_ecosystem(self, name: str, initial_conditions: EnvironmentalParameters,
                       species_selection: List[str], interactions: List[Interaction]) -> Dict:
        """Create a new synthetic ecosystem"""
        print(f"🌍 Creating synthetic ecosystem: {name}")
        print(f"   Initial temperature: {initial_conditions.temperature}°C")
        print(f"   Initial pH: {initial_conditions.ph}")
        print(f"   Species selected: {len(species_selection)}")

        # Initialize species
        ecosystem_species = {}
        total_biomass = 0.0

        for species_name in species_selection:
            if species_name in self.species_database:
                traits = self.species_database[species_name]

                # Initialize population based on carrying capacity
                initial_pop = random.uniform(100, 10000)
                biomass_per_individual = 10 ** (traits.size_class - 3)  # kg
                initial_biomass = initial_pop * biomass_per_individual

                species = Species(
                    traits=traits,
                    population=initial_pop,
                    biomass=initial_biomass,
                    age_distribution=[initial_pop] * 10,  # 10 age classes
                    genetic_diversity=random.uniform(0.7, 1.0),
                    adaptation_score=0.5,
                    niche=set(self._determine_niche(traits))
                )

                ecosystem_species[species_name] = species
                total_biomass += initial_biomass

        # Create ecosystem structure
        ecosystem = {
            'name': name,
            'species': ecosystem_species,
            'interactions': interactions,
            'environment': initial_conditions,
            'time': 0.0,
            'total_biomass': total_biomass,
            'history': [],
            'stability_metrics': []
        }

        # Calculate initial biodiversity
        biodiversity = self._calculate_biodiversity(ecosystem_species)
        ecosystem['biodiversity'] = biodiversity

        print(f"   Total initial biomass: {total_biomass:.2f} kg")
        print(f"   Biodiversity index: {biodiversity:.3f}")

        return ecosystem

    def _determine_niche(self, traits: SpeciesTraits) -> List[str]:
        """Determine ecological niche for species"""
        niche = []

        # Temperature niche
        if traits.optimal_temperature < 10:
            niche.append('psychrophilic')
        elif traits.optimal_temperature > 45:
            niche.append('thermophilic')
        else:
            niche.append('mesophilic')

        # pH niche
        if traits.optimal_ph < 5:
            niche.append('acidophilic')
        elif traits.optimal_ph > 9:
            niche.append('alkaliphilic')
        else:
            niche.append('neutral')

        # Metabolic niche
        if traits.metabolism_type == MetabolismType.PHOTOSYNTHESIS:
            niche.append('phototrophic')
        elif traits.metabolism_type == MetabolismType.CHEMOSYNTHESIS:
            niche.append('chemotrophic')

        # Habitat niche
        if traits.mobility < 0.3:
            niche.append('sessile')
        elif traits.mobility > 0.8:
            niche.append('pelagic')
        else:
            niche.append('benthic')

        # Trophic niche
        niche.append(traits.trophic_level.value)

        return niche

    def simulate_ecosystem(self, ecosystem: Dict, duration_days: float,
                          environmental_perturbations: List[Dict] = None) -> List[EcosystemState]:
        """Simulate ecosystem dynamics over time"""
        print(f"🔬 Simulating ecosystem for {duration_days} days")
        print(f"   Starting with {len(ecosystem['species'])} species")

        if environmental_perturbations is None:
            environmental_perturbations = []

        history = []
        current_ecosystem = ecosystem.copy()
        steps = int(duration_days / self.time_step)

        for step in range(steps):
            current_time = step * self.time_step

            # Apply environmental perturbations
            for perturbation in environmental_perturbations:
                if abs(current_time - perturbation['time']) < self.time_step:
                    current_ecosystem['environment'] = self._apply_perturbation(
                        current_ecosystem['environment'], perturbation
                    )
                    print(f"   Perturbation at day {current_time:.1f}: {perturbation['type']}")

            # Update populations
            self._update_populations(current_ecosystem, self.time_step)

            # Update environment
            self._update_environment(current_ecosystem, self.time_step)

            # Record state
            if step % 10 == 0:  # Record every 10 steps
                state = self._create_ecosystem_state(current_ecosystem, current_time)
                history.append(state)

                # Print progress
                if step % 100 == 0:
                    total_pop = sum(s.population for s in current_ecosystem['species'].values())
                    print(f"   Day {current_time:.1f}: Total population = {total_pop:.0f}")

        print(f"✅ Simulation complete! {len(history)} states recorded")
        return history

    def _update_populations(self, ecosystem: Dict, dt: float):
        """Update species populations based on interactions and environment"""
        species_populations = {name: sp.population for name, sp in ecosystem['species'].items()}
        environment = ecosystem['environment']
        interactions = ecosystem['interactions']

        # Calculate population changes
        population_changes = {}

        for species_name, species in ecosystem['species'].items():
            base_change = (species.traits.reproduction_rate - species.traits.death_rate) * dt

            # Environmental suitability
            env_factor = self._calculate_environmental_factor(species.traits, environment)
            base_change *= env_factor

            # Carrying capacity limitation
            carrying_capacity = self._calculate_carrying_capacity(species, environment)
            density_factor = 1.0 - (species.population / carrying_capacity) if carrying_capacity > 0 else 0
            base_change *= max(0, density_factor)

            # Interaction effects
            interaction_change = 0.0
            for interaction in interactions:
                if interaction.species1 == species_name or interaction.species2 == species_name:
                    effect = self._calculate_interaction_effect(
                        interaction, species_name, species_populations, environment
                    )
                    interaction_change += effect

            total_change = base_change + interaction_change * dt
            population_changes[species_name] = total_change

        # Apply changes
        for species_name, change in population_changes.items():
            species = ecosystem['species'][species_name]
            species.population = max(0, species.population + change)
            species.biomass = species.population * 10 ** (species.traits.size_class - 3)

            # Update genetic diversity (stochastic effects)
            if species.population > 0:
                diversity_change = random.uniform(-0.01, 0.01)
                species.genetic_diversity = max(0.1, min(1.0, species.genetic_diversity + diversity_change))

            # Update adaptation score
            species.adaptation_score = min(1.0, species.adaptation_score + env_factor * 0.001)

    def _calculate_environmental_factor(self, traits: SpeciesTraits,
                                      environment: EnvironmentalParameters) -> float:
        """Calculate environmental suitability factor for species"""
        factors = []

        # Temperature suitability
        temp_diff = abs(environment.temperature - traits.optimal_temperature)
        temp_factor = math.exp(-(temp_diff ** 2) / (2 * traits.tolerance_range ** 2))
        factors.append(temp_factor)

        # pH suitability
        ph_diff = abs(environment.ph - traits.optimal_ph)
        ph_factor = math.exp(-(ph_diff ** 2) / (2 * traits.tolerance_range ** 2))
        factors.append(ph_factor)

        # Resource availability
        for resource, requirement in traits.resource_requirements.items():
            if resource == 'light':
                availability = min(1.0, environment.light_intensity / 1000)
            elif resource == 'O2':
                availability = environment.oxygen_level / 100
            elif resource == 'CO2':
                availability = environment.carbon_dioxide / 1
            elif resource == 'N':
                availability = environment.nitrogen / 78
            elif resource == 'P':
                availability = environment.phosphorus / 0.1
            else:
                availability = 1.0

            factors.append(min(1.0, availability / requirement))

        # Water availability
        factors.append(environment.water_availability)

        # Toxicity effects
        for toxin, concentration in environment.toxic_compounds.items():
            toxicity_factor = math.exp(-concentration * 10)  # Toxicity sensitivity
            factors.append(toxicity_factor)

        return np.prod(factors)

    def _calculate_carrying_capacity(self, species: Species, environment: EnvironmentalParameters) -> float:
        """Calculate carrying capacity for species"""
        env_factor = self._calculate_environmental_factor(species.traits, environment)

        # Base carrying capacity depends on size and trophic level
        if species.traits.trophic_level == TrophicLevel.PRODUCER:
            base_capacity = 1000000  # Large for producers
        elif species.traits.trophic_level == TrophicLevel.PRIMARY_CONSUMER:
            base_capacity = 100000
        elif species.traits.trophic_level == TrophicLevel.SECONDARY_CONSUMER:
            base_capacity = 10000
        elif species.traits.trophic_level == TrophicLevel.TERTIARY_CONSUMER:
            base_capacity = 1000
        else:  # Decomposers and symbionts
            base_capacity = 500000

        # Adjust for size
        size_factor = 10 ** (3 - species.traits.size_class)
        base_capacity *= size_factor

        # Apply environmental factor and species-specific factor
        carrying_capacity = (base_capacity * env_factor *
                          species.traits.carrying_capacity_factor)

        return carrying_capacity

    def _calculate_interaction_effect(self, interaction: Interaction, target_species: str,
                                    populations: Dict[str, float],
                                    environment: EnvironmentalParameters) -> float:
        """Calculate effect of interaction on target species"""
        if interaction.interaction_type not in self.interaction_types:
            return 0.0

        interaction_params = self.interaction_types[interaction.interaction_type]

        # Determine partner species
        if interaction.species1 == target_species:
            partner_species = interaction.species2
            direction = 'species1_to_species2' if interaction.direction != 'species2_to_species1' else 'species2_to_species1'
        else:
            partner_species = interaction.species1
            direction = 'species2_to_species1' if interaction.direction != 'species1_to_species2' else 'species1_to_species2'

        if partner_species not in populations:
            return 0.0

        partner_population = populations[partner_species]
        if partner_population <= 0:
            return 0.0

        # Calculate interaction effect based on type
        if interaction.interaction_type == 'predation':
            if target_species == interaction.species1:  # Predator
                # Predator growth from eating prey
                prey_availability = min(1.0, partner_population / 1000)
                effect = interaction_params['predator_growth'] * prey_availability * interaction.strength
            else:  # Prey
                # Prey mortality from predation
                predation_pressure = min(1.0, populations[interaction.species1] / 100)
                effect = -interaction_params['prey_mortality'] * predation_pressure * interaction.strength

        elif interaction.interaction_type == 'competition':
            # Both species suffer from competition
            competition_strength = min(1.0, partner_population / populations[target_species])
            effect = -interaction_params['competition_strength'] * competition_strength * interaction.strength

        elif interaction.interaction_type == 'mutualism':
            # Both species benefit
            mutualism_factor = min(1.0, partner_population / 1000)
            effect = interaction_params['mutual_benefit'] * mutualism_factor * interaction.strength

        elif interaction.interaction_type == 'commensalism':
            # One species benefits, other unaffected
            if target_species == interaction.species1:  # Beneficiary
                benefit_factor = min(1.0, partner_population / 1000)
                effect = interaction_params['beneficiary_gain'] * benefit_factor * interaction.strength
            else:
                effect = 0.0

        elif interaction.interaction_type == 'amensalism':
            # One species harmed, other unaffected
            if target_species == interaction.species2:  # Victim
                harm_factor = min(1.0, partner_population / 1000)
                effect = -interaction_params['victim_cost'] * harm_factor * interaction.strength
            else:
                effect = 0.0

        elif interaction.interaction_type == 'parasitism':
            if target_species == interaction.species1:  # Parasite
                host_availability = min(1.0, partner_population / 1000)
                effect = interaction_params['parasite_gain'] * host_availability * interaction.strength
            else:  # Host
                parasite_load = min(1.0, populations[interaction.species1] / populations[target_species])
                effect = -interaction_params['host_cost'] * parasite_load * interaction.strength

        else:
            effect = 0.0

        # Apply environmental conditions to interaction
        for condition, threshold in interaction.conditions.items():
            if condition == 'temperature':
                env_value = environment.temperature
            elif condition == 'ph':
                env_value = environment.ph
            elif condition == 'oxygen':
                env_value = environment.oxygen_level
            else:
                env_value = 1.0

            condition_factor = 1.0 / (1.0 + abs(env_value - threshold) / 10)
            effect *= condition_factor

        return effect

    def _apply_perturbation(self, environment: EnvironmentalParameters,
                          perturbation: Dict) -> EnvironmentalParameters:
        """Apply environmental perturbation"""
        new_env = EnvironmentalParameters(
            temperature=environment.temperature,
            ph=environment.ph,
            oxygen_level=environment.oxygen_level,
            carbon_dioxide=environment.carbon_dioxide,
            nitrogen=environment.nitrogen,
            phosphorus=environment.phosphorus,
            water_availability=environment.water_availability,
            light_intensity=environment.light_intensity,
            pressure=environment.pressure,
            radiation_level=environment.radiation_level,
            toxic_compounds=environment.toxic_compounds.copy()
        )

        if perturbation['type'] == 'temperature_change':
            new_env.temperature += perturbation['magnitude']
        elif perturbation['type'] == 'ph_change':
            new_env.ph += perturbation['magnitude']
        elif perturbation['type'] == 'oxygen_depletion':
            new_env.oxygen_level *= perturbation['magnitude']
        elif perturbation['type'] == 'pollution':
            pollutant = perturbation['pollutant']
            concentration = perturbation['concentration']
            new_env.toxic_compounds[pollutant] = new_env.toxic_compounds.get(pollutant, 0) + concentration
        elif perturbation['type'] == 'drought':
            new_env.water_availability *= perturbation['severity']
        elif perturbation['type'] == 'radiation_increase':
            new_env.radiation_level += perturbation['magnitude']

        return new_env

    def _update_environment(self, ecosystem: Dict, dt: float):
        """Update environmental conditions"""
        env = ecosystem['environment']

        # Simple environmental dynamics
        # Temperature fluctuations
        temp_variation = math.sin(ecosystem['time'] * 2 * math.pi / 365) * 5  # Seasonal variation
        env.temperature += temp_variation * dt / 365

        # CO2 consumption by producers
        total_producer_biomass = sum(
            sp.biomass for sp in ecosystem['species'].values()
            if sp.traits.trophic_level == TrophicLevel.PRODUCER
        )
        co2_consumption = total_producer_biomass * 0.001 * dt
        env.carbon_dioxide = max(0.0001, env.carbon_dioxide - co2_consumption)

        # O2 production by producers
        o2_production = total_producer_biomass * 0.002 * dt
        env.oxygen_level = min(100, env.oxygen_level + o2_production)

        # Nutrient cycling by decomposers
        total_decomposer_biomass = sum(
            sp.biomass for sp in ecosystem['species'].values()
            if sp.traits.trophic_level == TrophicLevel.DECOMPOSER
        )
        nutrient_regeneration = total_decomposer_biomass * 0.001 * dt
        env.nitrogen = min(78, env.nitrogen + nutrient_regeneration * 0.8)
        env.phosphorus = min(0.1, env.phosphorus + nutrient_regeneration * 0.1)

        # Toxic compound degradation
        for toxin in list(env.toxic_compounds.keys()):
            degradation_rate = 0.1 * dt
            env.toxic_compounds[toxin] = max(0, env.toxic_compounds[toxin] - degradation_rate)
            if env.toxic_compounds[toxin] <= 0:
                del env.toxic_compounds[toxin]

    def _create_ecosystem_state(self, ecosystem: Dict, time: float) -> EcosystemState:
        """Create ecosystem state record"""
        species_populations = {name: sp.population for name, sp in ecosystem['species'].items()}
        total_biomass = sum(sp.biomass for sp in ecosystem['species'].values())
        biodiversity = self._calculate_biodiversity(ecosystem['species'])
        stability = self._calculate_stability(ecosystem['species'])

        resource_levels = {
            'CO2': ecosystem['environment'].carbon_dioxide,
            'O2': ecosystem['environment'].oxygen_level,
            'N': ecosystem['environment'].nitrogen,
            'P': ecosystem['environment'].phosphorus,
            'water': ecosystem['environment'].water_availability,
            'light': ecosystem['environment'].light_intensity
        }

        return EcosystemState(
            timestamp=time,
            species_populations=species_populations,
            total_biomass=total_biomass,
            biodiversity_index=biodiversity,
            stability_index=stability,
            resource_levels=resource_levels,
            environmental_conditions=ecosystem['environment']
        )

    def _calculate_biodiversity(self, species: Dict[str, Species]) -> float:
        """Calculate Shannon diversity index"""
        total_pop = sum(sp.population for sp in species.values())
        if total_pop == 0:
            return 0.0

        diversity = 0.0
        for sp in species.values():
            if sp.population > 0:
                proportion = sp.population / total_pop
                diversity -= proportion * math.log(proportion + 1e-10)

        return diversity

    def _calculate_stability(self, species: Dict[str, Species]) -> float:
        """Calculate ecosystem stability index"""
        if not species:
            return 0.0

        # Components of stability
        resilience = 0.0  # Ability to recover from perturbations
        resistance = 0.0  # Resistance to change
        redundancy = 0.0  # Functional redundancy

        # Resilience: based on genetic diversity and adaptation
        for sp in species.values():
            if sp.population > 0:
                resilience += sp.genetic_diversity * sp.adaptation_score * (sp.population / sum(s.population for s in species.values()))

        # Resistance: based on species diversity and trophic complexity
        trophic_levels = set(sp.traits.trophic_level for sp in species.values())
        resistance = len(trophic_levels) / len(TrophicLevel)

        # Redundancy: multiple species per functional group
        functional_groups = defaultdict(list)
        for name, sp in species.items():
            if sp.population > 0:
                group = sp.traits.trophic_level.value
                functional_groups[group].append(name)

        for group, group_species in functional_groups.items():
            if len(group_species) > 1:
                redundancy += min(1.0, len(group_species) / 3)

        redundancy /= len(TrophicLevel) if functional_groups else 1

        # Combined stability index
        stability = (resilience + resistance + redundancy) / 3
        return min(1.0, stability)

    def create_food_web(self, ecosystem: Dict) -> Dict:
        """Create food web structure from ecosystem"""
        food_web = {
            'nodes': [],
            'links': [],
            'trophic_levels': {}
        }

        # Create nodes
        for name, species in ecosystem['species'].items():
            node = {
                'id': name,
                'trophic_level': species.traits.trophic_level.value,
                'population': species.population,
                'biomass': species.biomass,
                'size_class': species.traits.size_class
            }
            food_web['nodes'].append(node)

            food_web['trophic_levels'][species.traits.trophic_level.value] = food_web['trophic_levels'].get(
                species.traits.trophic_level.value, []
            ) + [name]

        # Create links from interactions
        for interaction in ecosystem['interactions']:
            if interaction.interaction_type == 'predation':
                link = {
                    'source': interaction.species2,  # prey
                    'target': interaction.species1,  # predator
                    'type': 'predation',
                    'strength': interaction.strength
                }
                food_web['links'].append(link)

        return food_web

    def analyze_ecosystem_health(self, ecosystem: Dict, history: List[EcosystemState]) -> Dict:
        """Analyze ecosystem health and stability"""
        if not history:
            return {'health_score': 0.0, 'status': 'no_data'}

        recent_states = history[-10:] if len(history) >= 10 else history
        current_state = recent_states[-1]

        # Health indicators
        biodiversity_trend = self._calculate_trend([s.biodiversity_index for s in recent_states])
        biomass_trend = self._calculate_trend([s.total_biomass for s in recent_states])
        stability_trend = self._calculate_trend([s.stability_index for s in recent_states])

        # Resource balance
        resource_balance = self._calculate_resource_balance(current_state.resource_levels)

        # Species composition
        species_balance = self._calculate_species_balance(ecosystem['species'])

        # Overall health score
        health_score = (
            0.3 * current_state.biodiversity_index +
            0.2 * current_state.stability_index +
            0.2 * (1.0 + biodiversity_trend) / 2 +
            0.1 * (1.0 + biomass_trend) / 2 +
            0.1 * resource_balance +
            0.1 * species_balance
        )

        # Determine status
        if health_score > 0.8:
            status = 'thriving'
        elif health_score > 0.6:
            status = 'healthy'
        elif health_score > 0.4:
            status = 'stable'
        elif health_score > 0.2:
            status = 'declining'
        else:
            status = 'critical'

        return {
            'health_score': health_score,
            'status': status,
            'biodiversity': current_state.biodiversity_index,
            'stability': current_state.stability_index,
            'biomass': current_state.total_biomass,
            'biodiversity_trend': biodiversity_trend,
            'biomass_trend': biomass_trend,
            'stability_trend': stability_trend,
            'resource_balance': resource_balance,
            'species_balance': species_balance
        }

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in time series data"""
        if len(values) < 2:
            return 0.0

        # Simple linear trend
        x = list(range(len(values)))
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            slope = 0.0

        # Normalize to [-1, 1]
        max_possible_slope = 1.0
        return max(-1.0, min(1.0, slope / max_possible_slope))

    def _calculate_resource_balance(self, resource_levels: Dict[str, float]) -> float:
        """Calculate balance of resource levels"""
        # Optimal ranges for resources
        optimal_ranges = {
            'CO2': (0.03, 0.06),
            'O2': (15, 25),
            'N': (70, 80),
            'P': (0.05, 0.15),
            'water': (0.7, 1.0),
            'light': (500, 1500)
        }

        balance_scores = []
        for resource, optimal_range in optimal_ranges.items():
            if resource in resource_levels:
                value = resource_levels[resource]
                min_opt, max_opt = optimal_range

                if min_opt <= value <= max_opt:
                    score = 1.0
                elif value < min_opt:
                    score = value / min_opt
                else:
                    score = max_opt / value

                balance_scores.append(score)

        return np.mean(balance_scores) if balance_scores else 0.0

    def _calculate_species_balance(self, species: Dict[str, Species]) -> float:
        """Calculate balance of species composition"""
        trophic_distribution = defaultdict(int)
        total_population = sum(sp.population for sp in species.values())

        if total_population == 0:
            return 0.0

        for sp in species.values():
            if sp.population > 0:
                trophic_distribution[sp.traits.trophic_level] += sp.population

        # Ideal distribution (rough pyramid)
        ideal_distribution = {
            TrophicLevel.PRODUCER: 0.5,
            TrophicLevel.PRIMARY_CONSUMER: 0.3,
            TrophicLevel.SECONDARY_CONSUMER: 0.15,
            TrophicLevel.TERTIARY_CONSUMER: 0.03,
            TrophicLevel.DECOMPOSER: 0.02
        }

        balance_score = 0.0
        for level, ideal_ratio in ideal_distribution.items():
            actual_ratio = trophic_distribution.get(level, 0) / total_population
            difference = abs(actual_ratio - ideal_ratio)
            balance_score += 1.0 - difference

        return balance_score / len(ideal_distribution)

    def optimize_ecosystem(self, ecosystem: Dict, objectives: Dict[str, float]) -> Dict:
        """Optimize ecosystem parameters for specific objectives"""
        print(f"🔧 Optimizing ecosystem for objectives: {list(objectives.keys())}")

        # Define optimization parameters
        params = {
            'temperature_adjustment': ecosystem['environment'].temperature,
            'ph_adjustment': ecosystem['environment'].ph,
            'oxygen_adjustment': ecosystem['environment'].oxygen_level,
            'nutrient_enrichment': ecosystem['environment'].nitrogen,
            'species_introductions': []
        }

        # Objective function
        def objective_function(x):
            # Apply parameter changes
            test_env = EnvironmentalParameters(
                temperature=x[0],
                ph=x[1],
                oxygen_level=x[2],
                carbon_dioxide=ecosystem['environment'].carbon_dioxide,
                nitrogen=x[3],
                phosphorus=ecosystem['environment'].phosphorus,
                water_availability=ecosystem['environment'].water_availability,
                light_intensity=ecosystem['environment'].light_intensity,
                pressure=ecosystem['environment'].pressure,
                radiation_level=ecosystem['environment'].radiation_level,
                toxic_compounds=ecosystem['environment'].toxic_compounds.copy()
            )

            # Test ecosystem with new parameters
            test_ecosystem = ecosystem.copy()
            test_ecosystem['environment'] = test_env

            # Run short simulation
            test_history = self.simulate_ecosystem(test_ecosystem, 10)
            test_health = self.analyze_ecosystem_health(test_ecosystem, test_history)

            # Calculate objective score
            score = 0.0
            for objective, weight in objectives.items():
                if objective == 'biodiversity':
                    score += weight * test_health['biodiversity']
                elif objective == 'stability':
                    score += weight * test_health['stability']
                elif objective == 'biomass':
                    score += weight * (test_health['biomass'] / 1000)  # Normalize
                elif objective == 'resource_efficiency':
                    score += weight * test_health['resource_balance']

            return -score  # Minimize negative score

        # Initial parameters
        x0 = [
            ecosystem['environment'].temperature,
            ecosystem['environment'].ph,
            ecosystem['environment'].oxygen_level,
            ecosystem['environment'].nitrogen
        ]

        # Parameter bounds
        bounds = [
            (0, 50),    # Temperature
            (4, 10),    # pH
            (0, 100),   # Oxygen
            (0, 100)    # Nitrogen
        ]

        # Optimize
        try:
            result = minimize(objective_function, x0, bounds=bounds, method='L-BFGS-B')

            if result.success:
                optimal_params = {
                    'temperature': result.x[0],
                    'ph': result.x[1],
                    'oxygen': result.x[2],
                    'nitrogen': result.x[3]
                }
                print(f"   Optimization successful!")
                print(f"   Optimal temperature: {optimal_params['temperature']:.1f}°C")
                print(f"   Optimal pH: {optimal_params['ph']:.2f}")
                print(f"   Optimal oxygen: {optimal_params['oxygen']:.1f}%")
                print(f"   Optimal nitrogen: {optimal_params['nitrogen']:.1f}%")

                return optimal_params
            else:
                print(f"   Optimization failed: {result.message}")
                return params

        except Exception as e:
            print(f"   Optimization error: {str(e)}")
            return params

    def _lotka_volterra_dynamics(self, populations: List[float], t: float,
                                alpha: np.ndarray, beta: np.ndarray) -> List[float]:
        """Lotka-Volterra competition dynamics"""
        n = len(populations)
        dpdt = []

        for i in range(n):
            growth = alpha[i] * populations[i] * (1 - sum(beta[i, j] * populations[j] for j in range(n)))
            dpdt.append(growth)

        return dpdt

    def _predator_prey_dynamics(self, populations: List[float], t: float,
                               prey_params: Tuple[float, float, float],
                               predator_params: Tuple[float, float, float]) -> List[float]:
        """Predator-prey dynamics (simplified Lotka-Volterra)"""
        prey, predator = populations
        r, K, a = prey_params  # prey growth rate, carrying capacity, predation rate
        e, m, b = predator_params  # conversion efficiency, mortality, attack rate

        dprey_dt = r * prey * (1 - prey / K) - a * prey * predator
        dpredator_dt = e * a * prey * predator - m * predator

        return [dprey_dt, dpredator_dt]

    def _competition_dynamics(self, populations: List[float], t: float,
                            competition_matrix: np.ndarray,
                            growth_rates: List[float]) -> List[float]:
        """Competition dynamics"""
        n = len(populations)
        dpdt = []

        for i in range(n):
            competition_term = sum(competition_matrix[i, j] * populations[j] for j in range(n))
            growth = growth_rates[i] * populations[i] * (1 - competition_term)
            dpdt.append(growth)

        return dpdt

    def _mutualism_dynamics(self, populations: List[float], t: float,
                          mutualism_matrix: np.ndarray,
                          growth_rates: List[float]) -> List[float]:
        """Mutualism dynamics"""
        n = len(populations)
        dpdt = []

        for i in range(n):
            mutualism_term = sum(mutualism_matrix[i, j] * populations[j] / (1 + populations[j]) for j in range(n))
            growth = growth_rates[i] * populations[i] * (1 + mutualism_term)
            dpdt.append(growth)

        return dpdt

def main():
    """Demonstration of synthetic ecosystem capabilities"""
    print("🌍 Synthetic Ecosystem - Balanced Artificial Life Communities")
    print("=" * 65)

    ecosystem = SyntheticEcosystem()

    # Create environmental conditions
    initial_conditions = EnvironmentalParameters(
        temperature=25.0,
        ph=7.0,
        oxygen_level=21.0,
        carbon_dioxide=0.04,
        nitrogen=78.0,
        phosphorus=0.05,
        water_availability=0.8,
        light_intensity=1000.0,
        pressure=1.0,
        radiation_level=0.1,
        toxic_compounds={}
    )

    # Select species for ecosystem
    species_selection = [
        'quantum_algae',
        'chemo_bacteria',
        'synthetic_plant',
        'micro_herbivore',
        'quantum_grazer',
        'nano_predator',
        'apex_predator',
        'quantum_decomposer',
        'nitrogen_fixer'
    ]

    # Define interactions
    interactions = [
        Interaction('micro_herbivore', 'quantum_algae', 'predation', 0.8, 'species1_to_species2',
                   {'temperature': 25.0, 'oxygen': 20.0}),
        Interaction('quantum_grazer', 'synthetic_plant', 'predation', 0.7, 'species1_to_species2',
                   {'temperature': 20.0}),
        Interaction('nano_predator', 'micro_herbivore', 'predation', 0.6, 'species1_to_species2',
                   {'oxygen': 18.0}),
        Interaction('apex_predator', 'nano_predator', 'predation', 0.5, 'species1_to_species2',
                   {'temperature': 22.0}),
        Interaction('nano_predator', 'quantum_grazer', 'predation', 0.4, 'species1_to_species2',
                   {'temperature': 22.0}),
        Interaction('micro_herbivore', 'quantum_grazer', 'competition', 0.3, 'bidirectional',
                   {'temperature': 20.0}),
        Interaction('nitrogen_fixer', 'quantum_algae', 'mutualism', 0.6, 'bidirectional',
                   {'temperature': 25.0, 'ph': 7.5}),
        Interaction('quantum_decomposer', 'apex_predator', 'commensalism', 0.4, 'species2_to_species1',
                   {'temperature': 15.0}),
        Interaction('synthetic_plant', 'quantum_algae', 'competition', 0.5, 'bidirectional',
                   {'light': 1000.0, 'CO2': 0.04})
    ]

    # Create ecosystem
    synthetic_ecosystem = ecosystem.create_ecosystem(
        name="Quantum Terra",
        initial_conditions=initial_conditions,
        species_selection=species_selection,
        interactions=interactions
    )

    # Define environmental perturbations
    perturbations = [
        {'time': 100, 'type': 'temperature_change', 'magnitude': 5.0},
        {'time': 200, 'type': 'pollution', 'pollutant': 'heavy_metal', 'concentration': 0.5},
        {'time': 300, 'type': 'drought', 'severity': 0.5},
        {'time': 400, 'type': 'oxygen_depletion', 'magnitude': 0.7}
    ]

    # Simulate ecosystem
    history = ecosystem.simulate_ecosystem(
        ecosystem=synthetic_ecosystem,
        duration_days=500,
        environmental_perturbations=perturbations
    )

    # Analyze ecosystem health
    health_analysis = ecosystem.analyze_ecosystem_health(synthetic_ecosystem, history)
    print(f"\n📊 Ecosystem Health Analysis")
    print(f"   Health Score: {health_analysis['health_score']:.3f}")
    print(f"   Status: {health_analysis['status']}")
    print(f"   Biodiversity: {health_analysis['biodiversity']:.3f}")
    print(f"   Stability: {health_analysis['stability']:.3f}")
    print(f"   Total Biomass: {health_analysis['biomass']:.2f} kg")
    print(f"   Resource Balance: {health_analysis['resource_balance']:.3f}")
    print(f"   Species Balance: {health_analysis['species_balance']:.3f}")

    # Create food web
    food_web = ecosystem.create_food_web(synthetic_ecosystem)
    print(f"\n🕸️  Food Web Structure")
    print(f"   Total nodes: {len(food_web['nodes'])}")
    print(f"   Total links: {len(food_web['links'])}")
    for level, species_list in food_web['trophic_levels'].items():
        print(f"   {level}: {len(species_list)} species")

    # Optimize ecosystem
    optimization_objectives = {
        'biodiversity': 0.4,
        'stability': 0.3,
        'biomass': 0.2,
        'resource_efficiency': 0.1
    }

    optimal_params = ecosystem.optimize_ecosystem(synthetic_ecosystem, optimization_objectives)

    # Export results
    results = {
        'ecosystem_name': synthetic_ecosystem['name'],
        'species_count': len(synthetic_ecosystem['species']),
        'interactions_count': len(interactions),
        'simulation_duration': 500,
        'health_analysis': health_analysis,
        'food_web': food_web,
        'optimal_parameters': optimal_params,
        'perturbations_applied': len(perturbations)
    }

    with open('/home/activeloguser/DMLogn8n/biology/synthetic/ecosystem_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✨ Synthetic ecosystem simulation complete!")
    print(f"   Species simulated: {len(species_selection)}")
    print(f"   Simulation duration: 500 days")
    print(f"   Environmental perturbations: {len(perturbations)}")
    print(f"   Final ecosystem status: {health_analysis['status']}")
    print(f"   Results exported to: ecosystem_results.json")

if __name__ == "__main__":
    main()