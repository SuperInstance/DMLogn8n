#!/usr/bin/env python3
"""
Alien Civilizations System - Procedural Alien Species and Cultures
Generates diverse alien civilizations with unique characteristics and behaviors
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import random
import math

# Physical Constants
EARTH_MASS = 5.972e24  # kg
EARTH_RADIUS = 6.371e6  # meters
SOLAR_MASS = 1.989e30  # kg
AU = 1.496e11  # meters
G = 6.67430e-11  # Gravitational constant

class BiologyType(Enum):
    CARBON_BASED = "carbon_based"
    SILICON_BASED = "silicon_based"
    NITROGEN_BASED = "nitrogen_based"
    SULFUR_BASED = "sulfur_based"
    METHANE_BASED = "methane_based"
    AMMONIA_BASED = "ammonia_based"
    PLASMA_BASED = "plasma_based"
    CRYSTALLINE = "crystalline"
    GASEOUS = "gaseous"
    ENERGY_BASED = "energy_based"

class BodyPlan(Enum):
    HUMANOID = "humanoid"
    INSECTOID = "insectoid"
    REPTILIAN = "reptilian"
    AVIAN = "avian"
    AQUATIC = "aquatic"
    ARTHROPOD = "arthropod"
    MOLLUSCOID = "molluscoid"
    FUNGAL = "fungal"
    BOTANICAL = "botanical"
    MINERAL = "mineral"
    AMORPHOUS = "amorphous"
    MULTIFORM = "multiform"

class GovernmentType(Enum):
    DIRECT_DEMOCRACY = "direct_democracy"
    REPRESENTATIVE_DEMOCRACY = "representative_democracy"
    REPUBLIC = "republic"
    CONSTITUTIONAL_MONARCHY = "constitutional_monarchy"
    ABSOLUTE_MONARCHY = "absolute_monarchy"
    DICTATORSHIP = "dictatorship"
    MILITARY_JUNTA = "military_junta"
    THEOCRACY = "theocracy"
    MERITOCRACY = "meritocracy"
    TECHNOCRACY = "technocracy"
    CORPORATE_STATE = "corporate_state"
    ANARCHY = "anarchy"
    HIVE_MIND = "hive_mind"
    AI_GOVERNED = "ai_governed"

class CulturalTrait(Enum):
    EXPLORATORY = "exploratory"
    AGGRESSIVE = "aggressive"
    PEACEFUL = "peaceful"
    ISOLATIONIST = "isolationist"
    DIPLOMATIC = "diplomatic"
    TRADING = "trading"
    SCIENTIFIC = "scientific"
    RELIGIOUS = "religious"
    ARTISTIC = "artistic"
    MILITARISTIC = "militaristic"
    INDUSTRIAL = "industrial"
    ENVIRONMENTAL = "environmental"
    EXPANSIONIST = "expansionist"
    COLLECTIVIST = "collectivist"
    INDIVIDUALIST = "individualist"

class TechnologyFocus(Enum):
    BIOLOGICAL = "biological"
    MECHANICAL = "mechanical"
    ENERGY = "energy"
    QUANTUM = "quantum"
    GRAVITATIONAL = "gravitational"
    TEMPORAL = "temporal"
    PSIONIC = "psionic"
    NANOTECHNOLOGY = "nanotechnology"
    ARTIFICIAL_INTELLIGENCE = "artificial_intelligence"
    DIMENSIONAL = "dimensional"

class CommunicationMethod(Enum):
    VERBAL_LANGUAGE = "verbal_language"
    TELEPATHIC = "telepathic"
    CHEMICAL_SIGNALS = "chemical_signals"
    BIOLUMINESCENCE = "bioluminescence"
    ELECTROMAGNETIC = "electromagnetic"
    QUANTUM_ENTANGLEMENT = "quantum_entanglement"
    MATHEMATICAL = "mathematical"
    MUSICAL = "musical"
    PATTERN_BASED = "pattern_based"

@dataclass
class PhysicalCharacteristics:
    """Physical characteristics of an alien species"""
    biology_type: BiologyType
    body_plan: BodyPlan
    average_height: float  # meters
    average_mass: float  # kg
    lifespan: float  # years
    reproduction_rate: float  # offspring per year
    intelligence_factor: float  # 0-1 scale
    physical_strength: float  # 0-1 scale relative to humans
    speed_factor: float  # 0-1 scale relative to humans
    environmental_tolerance: Dict[str, Tuple[float, float]]  # Min/max for various factors
    special_abilities: List[str]
    vulnerabilities: List[str]
    dietary_requirements: List[str]

@dataclass
class CulturalCharacteristics:
    """Cultural characteristics of an alien civilization"""
    primary_language: str
    communication_method: CommunicationMethod
    social_structure: str  # How society is organized
    family_structure: str  # Family and kinship patterns
    art_forms: List[str]
    religious_beliefs: List[str]
    philosophical_systems: List[str]
    values: List[str]  # Core cultural values
    taboos: List[str]  # Cultural taboos
    traditions: List[str]
    social_customs: List[str]

@dataclass
class TechnologicalLevel:
    """Technological development of an alien civilization"""
    overall_level: float  # 0-1 scale
    specializations: List[TechnologyFocus]
    energy_production: float  # 0-1 scale
    ftl_capability: bool
    terraforming_capability: bool
    artificial_intelligence_level: float  # 0-1 scale
    biotechnology_level: float  # 0-1 scale
    materials_science_level: float  # 0-1 scale
    computing_power: float  # 0-1 scale
    weaponization_level: float  # 0-1 scale
    medical_advancement: float  # 0-1 scale
    known_technologies: List[str]
    research_priorities: List[str]

@dataclass
class AlienCivilization:
    """Represents an entire alien civilization"""
    id: str
    name: str
    species_name: str
    home_system: str
    home_planet: str
    population: int
    age: float  # years since civilization began
    expansion_radius: float  # light-years
    controlled_systems: Set[str]
    physical_characteristics: PhysicalCharacteristics
    cultural_characteristics: CulturalCharacteristics
    technological_level: TechnologicalLevel
    government_type: GovernmentType
    cultural_traits: Set[CulturalTrait]
    diplomatic_stance: Dict[str, str]  # Stance toward other civilizations
    resource_priorities: Dict[str, float]
    foreign_policy: str
    galactic_reputation: float  # 0-1 scale
    threat_level: float  # 0-1 scale
    trade_partners: Set[str]
    enemies: Set[str]
    allies: Set[str]

class AlienCivilizationGenerator:
    """Generates procedural alien civilizations"""

    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
            self.seed = seed
        else:
            self.seed = random.randint(0, 2**31 - 1)
            random.seed(self.seed)
            np.random.seed(self.seed)

        # Biology type probabilities based on environmental conditions
        self.biology_probabilities = {
            'temperate_planet': {
                BiologyType.CARBON_BASED: 0.7,
                BiologyType.NITROGEN_BASED: 0.1,
                BiologyType.SILICON_BASED: 0.05,
                BiologyType.SULFUR_BASED: 0.05,
                BiologyType.AMMONIA_BASED: 0.05,
                BiologyType.METHANE_BASED: 0.05
            },
            'desert_planet': {
                BiologyType.SILICON_BASED: 0.3,
                BiologyType.CARBON_BASED: 0.3,
                BiologyType.SULFUR_BASED: 0.2,
                BiologyType.METHANE_BASED: 0.1,
                BiologyType.AMMONIA_BASED: 0.1
            },
            'ocean_planet': {
                BiologyType.CARBON_BASED: 0.5,
                BiologyType.AMMONIA_BASED: 0.2,
                BiologyType.METHANE_BASED: 0.2,
                BiologyType.AQUATIC_SPECIALIZED: 0.1
            },
            'ice_planet': {
                BiologyType.METHANE_BASED: 0.4,
                BiologyType.AMMONIA_BASED: 0.3,
                BiologyType.CARBON_BASED: 0.2,
                BiologyType.SILICON_BASED: 0.1
            },
            'volcanic_planet': {
                BiologyType.SILICON_BASED: 0.4,
                BiologyType.SULFUR_BASED: 0.3,
                BiologyType.PLASMA_BASED: 0.2,
                BiologyType.CARBON_BASED: 0.1
            },
            'gas_giant': {
                BiologyType.GASEOUS: 0.4,
                BiologyType.ENERGY_BASED: 0.3,
                BiologyType.AMMONIA_BASED: 0.2,
                BiologyType.METHANE_BASED: 0.1
            }
        }

        # Name generation components
        self.name_prefixes = ['Xyl', 'Zor', 'Kryl', 'Vor', 'Nex', 'Quar', 'Myth', 'Syn', 'Chron', 'Astro', 'Bio', 'Geo', 'Helio', 'Cosmo', 'Stell']
        self.name_suffixes = ['ax', 'on', 'an', 'or', 'us', 'ex', 'is', 'ar', 'el', 'id', 'ium', 'on', 'os', 'ar', 'ix']
        self.name_middles = ['thar', 'gon', 'dor', 'lar', 'mor', 'nar', 'kor', 'vor', 'zar', 'par']

    def generate_alien_civilization(self, system_data: Dict, civilization_id: str) -> AlienCivilization:
        """Generate a complete alien civilization based on system data"""

        # Extract planetary data
        planet_data = system_data.get('home_planet', {})
        planet_type = planet_data.get('type', 'temperate_planet')
        gravity = planet_data.get('gravity', 1.0)
        temperature = planet_data.get('temperature', 288)
        atmosphere = planet_data.get('atmosphere', {})
        has_water = planet_data.get('has_water', False)

        # Generate physical characteristics
        physical = self.generate_physical_characteristics(planet_type, gravity, temperature, atmosphere, has_water)

        # Generate cultural characteristics
        cultural = self.generate_cultural_characteristics(physical)

        # Generate technological level
        technological = self.generate_technological_level(physical, planet_data)

        # Generate government type
        government = self.generate_government_type(physical, cultural, technological)

        # Generate cultural traits
        traits = self.generate_cultural_traits(physical, cultural, technological, government)

        # Generate civilization name
        civ_name = self.generate_civilization_name(physical, cultural)
        species_name = self.generate_species_name(physical)

        # Create the civilization
        civilization = AlienCivilization(
            id=civilization_id,
            name=civ_name,
            species_name=species_name,
            home_system=system_data.get('system_id', 'unknown'),
            home_planet=system_data.get('planet_id', 'unknown'),
            population=self.calculate_population(physical, technological),
            age=random.uniform(1000, 100000),  # years
            expansion_radius=random.uniform(0, 100) * technological.overall_level,
            controlled_systems=set([system_data.get('system_id', 'unknown')]),
            physical_characteristics=physical,
            cultural_characteristics=cultural,
            technological_level=technological,
            government_type=government,
            cultural_traits=traits,
            diplomatic_stance={},
            resource_priorities=self.generate_resource_priorities(traits, technological),
            foreign_policy=self.generate_foreign_policy(traits, government),
            galactic_reputation=random.uniform(0.1, 0.9),
            threat_level=self.calculate_threat_level(traits, technological),
            trade_partners=set(),
            enemies=set(),
            allies=set()
        )

        return civilization

    def generate_physical_characteristics(self, planet_type: str, gravity: float,
                                        temperature: float, atmosphere: Dict,
                                        has_water: bool) -> PhysicalCharacteristics:
        """Generate physical characteristics based on planetary conditions"""

        # Determine biology type
        biology_type = self.determine_biology_type(planet_type, temperature, atmosphere, has_water)

        # Determine body plan
        body_plan = self.determine_body_plan(biology_type, gravity, has_water)

        # Calculate physical parameters
        average_height = self.calculate_height(biology_type, body_plan, gravity)
        average_mass = self.calculate_mass(body_plan, average_height, gravity)
        lifespan = self.calculate_lifespan(biology_type, body_plan)
        reproduction_rate = self.calculate_reproduction_rate(biology_type, planet_type)
        intelligence_factor = self.calculate_intelligence(biology_type, body_plan)
        physical_strength = self.calculate_physical_strength(biology_type, gravity)
        speed_factor = self.calculate_speed(biology_type, body_plan, gravity)

        # Environmental tolerance
        environmental_tolerance = self.calculate_environmental_tolerance(biology_type, temperature, atmosphere)

        # Special abilities and vulnerabilities
        special_abilities = self.generate_special_abilities(biology_type, body_plan)
        vulnerabilities = self.generate_vulnerabilities(biology_type, body_plan)

        # Dietary requirements
        dietary_requirements = self.generate_dietary_requirements(biology_type, atmosphere)

        return PhysicalCharacteristics(
            biology_type=biology_type,
            body_plan=body_plan,
            average_height=average_height,
            average_mass=average_mass,
            lifespan=lifespan,
            reproduction_rate=reproduction_rate,
            intelligence_factor=intelligence_factor,
            physical_strength=physical_strength,
            speed_factor=speed_factor,
            environmental_tolerance=environmental_tolerance,
            special_abilities=special_abilities,
            vulnerabilities=vulnerabilities,
            dietary_requirements=dietary_requirements
        )

    def determine_biology_type(self, planet_type: str, temperature: float,
                            atmosphere: Dict, has_water: bool) -> BiologyType:
        """Determine the most likely biology type"""

        probabilities = self.biology_probabilities.get(planet_type,
                                                    self.biology_probabilities['temperate_planet'])

        # Adjust for temperature
        if temperature < 200:  # Very cold
            if BiologyType.METHANE_BASED in probabilities:
                probabilities[BiologyType.METHANE_BASED] *= 2
            if BiologyType.AMMONIA_BASED in probabilities:
                probabilities[BiologyType.AMMONIA_BASED] *= 1.5
        elif temperature > 400:  # Very hot
            if BiologyType.SILICON_BASED in probabilities:
                probabilities[BiologyType.SILICON_BASED] *= 2
            if BiologyType.SULFUR_BASED in probabilities:
                probabilities[BiologyType.SULFUR_BASED] *= 1.5

        # Adjust for atmosphere
        if atmosphere.get('CH4', 0) > 0.1:  # Methane-rich
            if BiologyType.METHANE_BASED in probabilities:
                probabilities[BiologyType.METHANE_BASED] *= 2
        if atmosphere.get('NH3', 0) > 0.1:  # Ammonia-rich
            if BiologyType.AMMONIA_BASED in probabilities:
                probabilities[BiologyType.AMMONIA_BASED] *= 2
        if atmosphere.get('SiH4', 0) > 0.01:  # Silane present
            if BiologyType.SILICON_BASED in probabilities:
                probabilities[BiologyType.SILICON_BASED] *= 2

        # Normalize probabilities
        total = sum(probabilities.values())
        if total > 0:
            for key in probabilities:
                probabilities[key] /= total

        # Choose biology type
        rand = random.random()
        cumulative = 0
        for bio_type, prob in probabilities.items():
            cumulative += prob
            if rand < cumulative:
                return bio_type

        return BiologyType.CARBON_BASED  # Default

    def determine_body_plan(self, biology_type: BiologyType, gravity: float, has_water: bool) -> BodyPlan:
        """Determine body plan based on biology and environment"""

        if has_water and random.random() < 0.4:
            return BodyPlan.AQUATIC

        if gravity > 2.0:  # High gravity
            if random.random() < 0.3:
                return BodyPlan.ARTHROPOD  # Exoskeleton for support
            elif random.random() < 0.5:
                return BodyPlan.MINERAL  # Crystalline structure
        elif gravity < 0.5:  # Low gravity
            if random.random() < 0.4:
                return BodyPlan.AVIAN  # Light bodies suitable for flight
            elif random.random() < 0.3:
                return BodyPlan.GASEOUS

        # Biology-specific tendencies
        if biology_type == BiologyType.INSECTOID:
            return BodyPlan.INSECTOID
        elif biology_type == BiologyType.CRYSTALLINE:
            return BodyPlan.MINERAL
        elif biology_type == BiologyType.PLASMA_BASED:
            return BodyPlan.AMORPHOUS
        elif biology_type == BiologyType.ENERGY_BASED:
            return BodyPlan.AMORPHOUS

        # Random selection with preferences
        body_plans = [
            BodyPlan.HUMANOID, BodyPlan.REPTILIAN, BodyPlan.AVIAN,
            BodyPlan.INSECTOID, BodyPlan.MOLLUSCOID, BodyPlan.FUNGAL
        ]

        weights = [0.3, 0.2, 0.15, 0.15, 0.1, 0.1]  # Humanoid is most common

        return random.choices(body_plans, weights=weights)[0]

    def calculate_height(self, biology_type: BiologyType, body_plan: BodyPlan, gravity: float) -> float:
        """Calculate average height based on biology and gravity"""

        base_heights = {
            BodyPlan.HUMANOID: 1.7,
            BodyPlan.REPTILIAN: 2.0,
            BodyPlan.AVIAN: 1.2,
            BodyPlan.INSECTOID: 1.5,
            BodyPlan.AQUATIC: 2.5,
            BodyPlan.ARTHROPOD: 1.0,
            BodyPlan.MOLLUSCOID: 1.8,
            BodyPlan.FUNGAL: 0.8,
            BodyPlan.MINERAL: 2.2,
            BodyPlan.AMORPHOUS: 1.5,
            BodyPlan.BOTANICAL: 3.0,
            BodyPlan.GASEOUS: 5.0
        }

        base_height = base_heights.get(body_plan, 1.7)

        # Gravity adjustment
        gravity_factor = 1.0 / (gravity ** 0.25)  # Inverse relationship with gravity

        # Biology adjustment
        if biology_type == BiologyType.SILICON_BASED:
            base_height *= 0.8  # Silicon life tends to be shorter/denser
        elif biology_type == BiologyType.GASEOUS:
            base_height *= 2.0  # Gaseous life can be larger

        return base_height * gravity_factor * random.uniform(0.8, 1.2)

    def calculate_mass(self, body_plan: BodyPlan, height: float, gravity: float) -> float:
        """Calculate average mass"""

        base_densities = {
            BodyPlan.HUMANOID: 1000,  # kg/m³ (human-like)
            BodyPlan.REPTILIAN: 1200,
            BodyPlan.AVIAN: 600,
            BodyPlan.INSECTOID: 800,
            BodyPlan.AQUATIC: 1100,
            BodyPlan.ARTHROPOD: 900,
            BodyPlan.MOLLUSCOID: 1050,
            BodyPlan.FUNGAL: 700,
            BodyPlan.MINERAL: 3000,
            BodyPlan.AMORPHOUS: 500,
            BodyPlan.BOTANICAL: 600,
            BodyPlan.GASEOUS: 100
        }

        density = base_densities.get(body_plan, 1000) * random.uniform(0.9, 1.1)

        # Estimate volume (simplified as cylinder)
        volume = np.pi * (height * 0.15) ** 2 * height  # Rough approximation

        # Gravity affects density (higher gravity = denser)
        gravity_factor = gravity ** 0.1

        return volume * density * gravity_factor

    def calculate_lifespan(self, biology_type: BiologyType, body_plan: BodyPlan) -> float:
        """Calculate average lifespan"""

        base_lifespans = {
            BodyPlan.HUMANOID: 80,
            BodyPlan.REPTILIAN: 150,
            BodyPlan.AVIAN: 40,
            BodyPlan.INSECTOID: 25,
            BodyPlan.AQUATIC: 120,
            BodyPlan.ARTHROPOD: 30,
            BodyPlan.MOLLUSCOID: 60,
            BodyPlan.FUNGAL: 200,
            BodyPlan.MINERAL: 500,
            BodyPlan.AMORPHOUS: 100,
            BodyPlan.BOTANICAL: 300,
            BodyPlan.GASEOUS: 50
        }

        base_lifespan = base_lifespans.get(body_plan, 80)

        # Biology adjustments
        if biology_type == BiologyType.SILICON_BASED:
            base_lifespan *= 2  # Silicon life tends to be longer-lived
        elif biology_type == BiologyType.PLASMA_BASED:
            base_lifespan *= 0.1  # Plasma life is short-lived
        elif biology_type == BiologyType.ENERGY_BASED:
            base_lifespan *= 10  # Energy beings can be very long-lived

        return base_lifespan * random.uniform(0.8, 1.2)

    def calculate_reproduction_rate(self, biology_type: BiologyType, planet_type: str) -> float:
        """Calculate reproduction rate (offspring per year)"""

        base_rates = {
            BiologyType.CARBON_BASED: 0.1,
            BiologyType.SILICON_BASED: 0.02,
            BiologyType.NITROGEN_BASED: 0.08,
            BiologyType.SULFUR_BASED: 0.05,
            BiologyType.METHANE_BASED: 0.03,
            BiologyType.AMMONIA_BASED: 0.04,
            BiologyType.PLASMA_BASED: 0.5,
            BiologyType.CRYSTALLINE: 0.01,
            BiologyType.GASEOUS: 0.8,
            BiologyType.ENERGY_BASED: 0.001
        }

        base_rate = base_rates.get(biology_type, 0.1)

        # Environmental adjustment
        if planet_type in ['ocean_planet', 'temperate_planet']:
            base_rate *= 1.5  # Good environments support higher reproduction
        elif planet_type in ['desert_planet', 'ice_planet']:
            base_rate *= 0.5  # Harsh environments reduce reproduction

        return base_rate * random.uniform(0.5, 2.0)

    def calculate_intelligence(self, biology_type: BiologyType, body_plan: BodyPlan) -> float:
        """Calculate intelligence factor (0-1 scale)"""

        # Base intelligence by body plan
        base_intelligence = {
            BodyPlan.HUMANOID: 0.8,
            BodyPlan.REPTILIAN: 0.6,
            BodyPlan.AVIAN: 0.7,
            BodyPlan.INSECTOID: 0.4,  # Individual intelligence, hive intelligence could be higher
            BodyPlan.AQUATIC: 0.75,
            BodyPlan.ARTHROPOD: 0.5,
            BodyPlan.MOLLUSCOID: 0.65,
            BodyPlan.FUNGAL: 0.3,  # Network intelligence
            BodyPlan.MINERAL: 0.2,
            BodyPlan.AMORPHOUS: 0.6,
            BodyPlan.BOTANICAL: 0.4,
            BodyPlan.GASEOUS: 0.3
        }

        intelligence = base_intelligence.get(body_plan, 0.5)

        # Biology adjustments
        if biology_type in [BiologyType.ENERGY_BASED, BiologyType.PLASMA_BASED]:
            intelligence *= 1.2  # Energy-based life can have unique intelligence
        elif biology_type == BiologyType.CRYSTALLINE:
            intelligence *= 0.8  # Slower thinking

        return min(1.0, intelligence * random.uniform(0.8, 1.2))

    def calculate_physical_strength(self, biology_type: BiologyType, gravity: float) -> float:
        """Calculate physical strength relative to humans"""

        base_strength = {
            BiologyType.CARBON_BASED: 1.0,
            BiologyType.SILICON_BASED: 1.5,
            BiologyType.NITROGEN_BASED: 0.8,
            BiologyType.SULFUR_BASED: 1.2,
            BiologyType.METHANE_BASED: 0.6,
            BiologyType.AMMONIA_BASED: 0.7,
            BiologyType.PLASMA_BASED: 0.1,
            BiologyType.CRYSTALLINE: 2.0,
            BiologyType.GASEOUS: 0.05,
            BiologyType.ENERGY_BASED: 0.2
        }

        strength = base_strength.get(biology_type, 1.0)

        # Gravity adaptation
        gravity_factor = gravity ** 0.5

        return strength * gravity_factor * random.uniform(0.8, 1.2)

    def calculate_speed(self, biology_type: BiologyType, body_plan: BodyPlan, gravity: float) -> float:
        """Calculate speed factor relative to humans"""

        base_speed = {
            BodyPlan.HUMANOID: 1.0,
            BodyPlan.REPTILIAN: 0.9,
            BodyPlan.AVIAN: 1.5,
            BodyPlan.INSECTOID: 1.2,
            BodyPlan.AQUATIC: 0.3,  # On land
            BodyPlan.ARTHROPOD: 1.1,
            BodyPlan.MOLLUSCOID: 0.5,
            BodyPlan.FUNGAL: 0.2,
            BodyPlan.MINERAL: 0.1,
            BodyPlan.AMORPHOUS: 0.8,
            BodyPlan.BOTANICAL: 0.1,
            BodyPlan.GASEOUS: 0.6
        }

        speed = base_speed.get(body_plan, 1.0)

        # Gravity effect
        gravity_factor = 1.0 / (gravity ** 0.3)

        return speed * gravity_factor * random.uniform(0.8, 1.2)

    def calculate_environmental_tolerance(self, biology_type: BiologyType,
                                        temperature: float, atmosphere: Dict) -> Dict[str, Tuple[float, float]]:
        """Calculate environmental tolerance ranges"""

        # Temperature tolerance (Kelvin)
        if biology_type == BiologyType.METHANE_BASED:
            temp_tolerance = (90, 120)  # Methane liquid range
        elif biology_type == BiologyType.AMMONIA_BASED:
            temp_tolerance = (195, 240)  # Ammonia liquid range
        elif biology_type == BiologyType.SILICON_BASED:
            temp_tolerance = (300, 1500)  # Wide tolerance
        elif biology_type == BiologyType.PLASMA_BASED:
            temp_tolerance = (1000, 10000)  # Very hot
        else:  # Carbon-based and others
            temp_tolerance = (273, 373)  # Water liquid range

        # Pressure tolerance (relative to Earth)
        if biology_type in [BiologyType.GASEOUS, BiologyType.ENERGY_BASED]:
            pressure_tolerance = (0.1, 10)
        else:
            pressure_tolerance = (0.5, 3)

        # Gravity tolerance
        gravity_tolerance = (0.3, 3.0)

        # Radiation tolerance
        if biology_type in [BiologyType.ENERGY_BASED, BiologyType.CRYSTALLINE]:
            radiation_tolerance = (0, 1000)  # High tolerance
        else:
            radiation_tolerance = (0, 10)  # Lower tolerance

        return {
            'temperature': temp_tolerance,
            'pressure': pressure_tolerance,
            'gravity': gravity_tolerance,
            'radiation': radiation_tolerance
        }

    def generate_special_abilities(self, biology_type: BiologyType, body_plan: BodyPlan) -> List[str]:
        """Generate special abilities based on biology"""

        abilities = []

        if biology_type == BiologyType.ENERGY_BASED:
            abilities.extend(['electromagnetic_manipulation', 'energy_projection', 'phase_shift'])
        elif biology_type == BiologyType.PLASMA_BASED:
            abilities.extend(['heat_resistance', 'electrical_discharge'])
        elif biology_type == BiologyType.TELEPATHIC:
            abilities.extend(['telepathy', 'mind_reading'])
        elif biology_type == BiologyType.CRYSTALLINE:
            abilities.extend(['energy_absorption', 'crystalline_growth'])
        elif body_plan == BodyPlan.AVIAN:
            abilities.extend(['flight', 'enhanced_vision'])
        elif body_plan == BodyPlan.AQUATIC:
            abilities.extend(['underwater_breathing', 'pressure_resistance'])
        elif body_plan == BodyPlan.INSECTOID:
            abilities.extend(['exoskeleton_armor', 'wall_climbing'])

        # Random additional abilities
        possible_abilities = [
            'regeneration', 'camouflage', 'bioluminescence', 'hivemind_connection',
            'photosynthesis', 'electroreception', 'magnetoreception', 'venom',
            'acid_spray', 'sonar', 'invisibility', 'teleportation'
        ]

        num_abilities = random.randint(0, 2)
        abilities.extend(random.sample(possible_abilities, min(num_abilities, len(possible_abilities))))

        return abilities

    def generate_vulnerabilities(self, biology_type: BiologyType, body_plan: BodyPlan) -> List[str]:
        """Generate vulnerabilities based on biology"""

        vulnerabilities = []

        if biology_type == BiologyType.ENERGY_BASED:
            vulnerabilities.extend(['electromagnetic_pulses', 'energy_drains'])
        elif biology_type == BiologyType.SILICON_BASED:
            vulnerabilities.extend(['extreme_cold', 'certain_acids'])
        elif biology_type == BiologyType.METHANE_BASED:
            vulnerabilities.extend(['high_temperatures', 'oxygen_toxicity'])
        elif biology_type == BiologyType.AMMONIA_BASED:
            vulnerabilities.extend(['heat', 'low_pressure'])
        elif body_plan == BodyPlan.AQUATIC:
            vulnerabilities.extend(['dehydration', 'low_pressure'])
        elif body_plan == BodyPlan.AVIAN:
            vulnerabilities.extend(['wing_damage', 'high_altitude_sickness'])

        # Common vulnerabilities
        possible_vulnerabilities = [
            'radiation', 'toxins', 'disease', 'extreme_temperatures',
            'pressure_changes', 'starvation', 'dehydration', 'sensory_overload'
        ]

        num_vulnerabilities = random.randint(1, 3)
        vulnerabilities.extend(random.sample(possible_vulnerabilities, min(num_vulnerabilities, len(possible_vulnerabilities))))

        return vulnerabilities

    def generate_dietary_requirements(self, biology_type: BiologyType, atmosphere: Dict) -> List[str]:
        """Generate dietary requirements"""

        if biology_type == BiologyType.ENERGY_BASED:
            return ['electromagnetic_energy', 'radiation']
        elif biology_type == BiologyType.PLASMA_BASED:
            return ['high_energy_plasma', 'ionized_gases']
        elif biology_type == BiologyType.PHOTOSYNTHETIC:
            return ['light_energy', 'carbon_dioxide', 'water']
        elif biology_type == BiologyType.CHEMOSYNTHETIC:
            return ['chemical_compounds', 'minerals']
        elif atmosphere.get('CH4', 0) > 0.1:
            return ['methane', 'hydrocarbons']
        elif atmosphere.get('NH3', 0) > 0.1:
            return ['ammonia', 'nitrogen_compounds']
        else:
            # Default to carbon-based requirements
            requirements = ['carbon_compounds']
            if atmosphere.get('O2', 0) > 0.1:
                requirements.append('oxygen')
            else:
                requirements.append('alternative_electron_acceptor')
            return requirements

    def generate_cultural_characteristics(self, physical: PhysicalCharacteristics) -> CulturalCharacteristics:
        """Generate cultural characteristics based on physical traits"""

        # Communication method influenced by biology
        if 'telepathy' in physical.special_abilities:
            communication = CommunicationMethod.TELEPATHIC
        elif physical.biology_type in [BiologyType.GASEOUS, BiologyType.ENERGY_BASED]:
            communication = random.choice([CommunicationMethod.ELECTROMAGNETIC, CommunicationMethod.QUANTUM_ENTANGLEMENT])
        elif physical.body_plan == BodyPlan.INSECTOID:
            communication = random.choice([CommunicationMethod.CHEMICAL_SIGNALS, CommunicationMethod.BIOLUMINESCENCE])
        else:
            communication = CommunicationMethod.VERBAL_LANGUAGE

        # Generate language name
        language = self.generate_language_name(physical, communication)

        # Social structure based on abilities and biology
        if 'hivemind_connection' in physical.special_abilities:
            social_structure = 'collective_consciousness'
        elif physical.body_plan in [BodyPlan.INSECTOID, BodyPlan.FUNGAL]:
            social_structure = 'caste_based_hierarchy'
        elif communication == CommunicationMethod.TELEPATHIC:
            social_structure = 'telepathic_network'
        else:
            social_structure = random.choice(['tribal_clans', 'city_states', 'feudal_system', 'individualistic'])

        # Family structure
        if physical.reproduction_rate > 0.5:
            family_structure = 'collective_raising'
        elif social_structure == 'collective_consciousness':
            family_structure = 'no_family_units'
        else:
            family_structure = random.choice(['nuclear_family', 'extended_family', 'clan_based', 'egg_communities'])

        # Art forms influenced by biology
        art_forms = []
        if 'bioluminescence' in physical.special_abilities:
            art_forms.append('light_patterns')
        if communication == CommunicationMethod.TELEPATHIC:
            art_forms.append('thought sculptures')
        if physical.body_plan == BodyPlan.AVIAN:
            art_forms.append('aerial_dance')
        elif physical.body_plan == BodyPlan.AQUATIC:
            art_forms.append('water_currents')
        else:
            art_forms.extend(random.sample(['sound_harmonies', 'sculpture', 'storytelling', 'architecture', 'ritual_dance'], 2))

        # Religious and philosophical systems
        if 'energy_manipulation' in physical.special_abilities:
            religious_beliefs = ['energy_worship', 'cosmic_consciousness']
        elif physical.biology_type == BiologyType.MINERAL:
            religious_beliefs = ['crystal_spirits', 'earth_worship']
        else:
            religious_beliefs = random.sample(['ancestor_worship', 'nature_spirits', 'cosmic_order', 'scientific_rationalism', 'chaos_reverence'], 2)

        philosophical_systems = random.sample(['collectivism', 'individualism', 'utilitarianism', 'deontology', 'virtue_ethics', 'nihilism'], 2)

        # Values based on abilities and environment
        possible_values = ['knowledge', 'strength', 'harmony', 'tradition', 'innovation', 'community', 'individuality', 'honor', 'survival', 'exploration']
        values = random.sample(possible_values, random.randint(2, 4))

        # Taboos
        if 'telepathy' in physical.special_abilities:
            taboos = ['thought_secrets', 'mental_violation']
        else:
            taboos = random.sample(['dishonesty', 'cowardice', 'waste', 'violence', 'isolation'], 2)

        # Traditions
        traditions = random.sample(['coming_of_age_rituals', 'seasonal_festivals', 'story_circles', 'honor_duels', 'meditation_practices'], 2)

        return CulturalCharacteristics(
            primary_language=language,
            communication_method=communication,
            social_structure=social_structure,
            family_structure=family_structure,
            art_forms=art_forms,
            religious_beliefs=religious_beliefs,
            philosophical_systems=philosophical_systems,
            values=values,
            taboos=taboos,
            traditions=traditions,
            social_customs=random.sample(['gift_giving', 'hospitality', 'challenge_rituals', 'sharing_circles'], 2)
        )

    def generate_technological_level(self, physical: PhysicalCharacteristics, planet_data: Dict) -> TechnologicalLevel:
        """Generate technological level based on physical characteristics and environment"""

        # Base technological level influenced by intelligence
        base_level = physical.intelligence_factor * random.uniform(0.3, 1.0)

        # Environmental challenges drive technological development
        if planet_data.get('hostility_level', 0) > 0.7:
            base_level *= 1.2  # Harsh environments drive innovation

        # Special abilities influence technology focus
        specializations = []
        if 'energy_manipulation' in physical.special_abilities:
            specializations.append(TechnologyFocus.ENERGY)
        if 'hivemind_connection' in physical.special_abilities:
            specializations.append(TechnologyFocus.BIOLOGICAL)
        if physical.biology_type in [BiologyType.SILICON_BASED, BiologyType.CRYSTALLINE]:
            specializations.append(TechnologyFocus.MATERIALS_SCIENCE)

        # Add random specializations
        all_specializations = list(TechnologyFocus)
        remaining = [s for s in all_specializations if s not in specializations]
        specializations.extend(random.sample(remaining, min(2, len(remaining))))

        # Calculate specific tech levels
        energy_production = base_level * random.uniform(0.8, 1.2)
        if TechnologyFocus.ENERGY in specializations:
            energy_production *= 1.3

        ftl_capability = base_level > 0.7 and random.random() < 0.6
        terraforming_capability = base_level > 0.8 and random.random() < 0.5

        ai_level = base_level * random.uniform(0.7, 1.0)
        if TechnologyFocus.ARTIFICIAL_INTELLIGENCE in specializations:
            ai_level *= 1.4

        biotech_level = base_level * random.uniform(0.6, 1.1)
        if TechnologyFocus.BIOLOGICAL in specializations:
            biotech_level *= 1.5

        materials_level = base_level * random.uniform(0.7, 1.1)
        if TechnologyFocus.MATERIALS_SCIENCE in specializations:
            materials_level *= 1.3

        computing_power = base_level * random.uniform(0.8, 1.2)
        weaponization_level = base_level * random.uniform(0.5, 1.0)
        medical_advancement = base_level * random.uniform(0.6, 1.1)

        # Generate known technologies
        known_techs = []
        if base_level > 0.3:
            known_techs.extend(['basic_electronics', 'nuclear_power'])
        if base_level > 0.5:
            known_techs.extend(['fusion_power', 'genetic_engineering'])
        if base_level > 0.7:
            known_techs.extend(['ai_consciousness', 'nanotechnology'])
        if base_level > 0.9:
            known_techs.extend(['quantum_computing', 'reality_manipulation'])

        return TechnologicalLevel(
            overall_level=base_level,
            specializations=specializations,
            energy_production=energy_production,
            ftl_capability=ftl_capability,
            terraforming_capability=terraforming_capability,
            artificial_intelligence_level=ai_level,
            biotechnology_level=biotech_level,
            materials_science_level=materials_level,
            computing_power=computing_power,
            weaponization_level=weaponization_level,
            medical_advancement=medical_advancement,
            known_technologies=known_techs,
            research_priorities=random.sample(['space_exploration', 'biological_enhancement', 'energy_efficiency', 'weapon_development'], 2)
        )

    def generate_government_type(self, physical: PhysicalCharacteristics,
                               cultural: CulturalCharacteristics,
                               technological: TechnologicalLevel) -> GovernmentType:
        """Generate government type based on physical, cultural, and technological factors"""

        # Hive-minded species tend toward collective governments
        if cultural.social_structure == 'collective_consciousness':
            return GovernmentType.HIVE_MIND

        # High tech level allows for advanced governments
        if technological.overall_level > 0.8:
            if technological.artificial_intelligence_level > 0.9:
                return GovernmentType.AI_GOVERNED
            else:
                return random.choice([GovernmentType.TECHNOCRACY, GovernmentType.MERITOCRACY])

        # Cultural influences
        if 'honor' in cultural.values:
            if technological.weaponization_level > 0.7:
                return GovernmentType.MILITARY_JUNTA
            else:
                return GovernmentType.REPUBLIC

        if 'harmony' in cultural.values or 'community' in cultural.values:
            return random.choice([GovernmentType.DIRECT_DEMOCRACY, GovernmentType.REPRESENTATIVE_DEMOCRACY])

        if 'tradition' in cultural.values:
            return random.choice([GovernmentType.CONSTITUTIONAL_MONARCHY, GovernmentType.THEOCRACY])

        # High intelligence tends toward democratic or meritocratic systems
        if physical.intelligence_factor > 0.8:
            return random.choice([GovernmentType.REPRESENTATIVE_DEMOCRACY, GovernmentType.MERITOCRACY])

        # Default weighted selection
        governments = [
            GovernmentType.REPRESENTATIVE_DEMOCRACY,
            GovernmentType.REPUBLIC,
            GovernmentType.CORPORATE_STATE,
            GovernmentType.CONSTITUTIONAL_MONARCHY,
            GovernmentType.DICTATORSHIP
        ]

        weights = [0.3, 0.2, 0.2, 0.15, 0.15]

        return random.choices(governments, weights=weights)[0]

    def generate_cultural_traits(self, physical: PhysicalCharacteristics,
                               cultural: CulturalCharacteristics,
                               technological: TechnologicalLevel,
                               government: GovernmentType) -> Set[CulturalTrait]:
        """Generate cultural traits"""

        traits = set()

        # Physical influences
        if 'exploration' in physical.special_abilities or 'flight' in physical.special_abilities:
            traits.add(CulturalTrait.EXPLORATORY)

        if physical.intelligence_factor > 0.8:
            traits.add(CulturalTrait.SCIENTIFIC)

        # Cultural influences
        if 'individuality' in cultural.values:
            traits.add(CulturalTrait.INDIVIDUALIST)
        elif 'community' in cultural.values:
            traits.add(CulturalTrait.COLLECTIVIST)

        if 'harmony' in cultural.values:
            traits.add(CulturalTrait.PEACEFUL)

        if 'honor' in cultural.values:
            traits.add(CulturalTrait.MILITARISTIC)

        # Technological influences
        if technological.ftl_capability:
            traits.add(CulturalTrait.EXPANSIONIST)

        if technological.biotechnology_level > 0.8:
            traits.add(CulturalTrait.ENVIRONMENTAL)

        if technological.weaponization_level > 0.8:
            traits.add(CulturalTrait.AGGRESSIVE)
        elif technological.weaponization_level < 0.3:
            traits.add(CulturalTrait.PEACEFUL)

        # Government influences
        if government == GovernmentType.CORPORATE_STATE:
            traits.add(CulturalTrait.TRADING)
        elif government == GovernmentType.THEOCRACY:
            traits.add(CulturalTrait.RELIGIOUS)

        # Add some random traits
        all_traits = list(CulturalTrait)
        remaining = [t for t in all_traits if t not in traits]
        traits.update(random.sample(remaining, min(2, len(remaining))))

        return traits

    def generate_resource_priorities(self, traits: Set[CulturalTrait],
                                   technological: TechnologicalLevel) -> Dict[str, float]:
        """Generate resource priorities based on traits and technology"""

        priorities = {
            'energy': 0.5,
            'metals': 0.3,
            'food': 0.4,
            'water': 0.3,
            'technology': 0.6,
            'medicine': 0.3
        }

        if CulturalTrait.INDUSTRIAL in traits:
            priorities['metals'] *= 1.5
            priorities['energy'] *= 1.3

        if CulturalTrait.SCIENTIFIC in traits:
            priorities['technology'] *= 1.5

        if CulturalTrait.TRADING in traits:
            priorities['technology'] *= 1.2
            priorities['luxury_goods'] = 0.7

        if CulturalTrait.MILITARISTIC in traits:
            priorities['weapons'] = 0.8
            priorities['energy'] *= 1.2

        if technological.ftl_capability:
            priorities['exotic_materials'] = 0.6
            priorities['energy'] *= 1.4

        # Normalize
        total = sum(priorities.values())
        for key in priorities:
            priorities[key] /= total

        return priorities

    def generate_foreign_policy(self, traits: Set[CulturalTrait], government: GovernmentType) -> str:
        """Generate foreign policy approach"""

        if CulturalTrait.ISOLATIONIST in traits:
            return 'non_interventionist'
        elif CulturalTrait.EXPANSIONIST in traits:
            return 'imperialistic'
        elif CulturalTrait.DIPLOMATIC in traits:
            return 'diplomatic_engagement'
        elif CulturalTrait.AGGRESSIVE in traits:
            return 'militaristic'
        elif CulturalTrait.TRADING in traits:
            return 'commercial_focus'
        else:
            return 'balanced'

    def calculate_threat_level(self, traits: Set[CulturalTrait], technological: TechnologicalLevel) -> float:
        """Calculate threat level to other civilizations"""

        threat = 0.0

        if CulturalTrait.AGGRESSIVE in traits:
            threat += 0.3
        if CulturalTrait.EXPANSIONIST in traits:
            threat += 0.2
        if CulturalTrait.MILITARISTIC in traits:
            threat += 0.25

        threat += technological.weaponization_level * 0.15
        threat += technological.overall_level * 0.1

        return min(1.0, threat)

    def calculate_population(self, physical: PhysicalCharacteristics, technological: TechnologicalLevel) -> int:
        """Calculate starting population"""

        base_population = 1000000  # 1 million base

        # Reproduction rate affects population
        reproduction_factor = 1 + physical.reproduction_rate * 10

        # Technology affects carrying capacity
        tech_factor = 1 + technological.overall_level * 5

        # Intelligence affects organization
        intelligence_factor = 1 + physical.intelligence_factor * 2

        return int(base_population * reproduction_factor * tech_factor * intelligence_factor * random.uniform(0.5, 2.0))

    def generate_civilization_name(self, physical: PhysicalCharacteristics,
                                 cultural: CulturalCharacteristics) -> str:
        """Generate a civilization name"""

        prefixes = ['Stellar', 'Cosmic', 'Galactic', 'Quantum', 'Void', 'Star', 'Nebula', 'Nova', 'Pulsar', 'Quasar']
        middles = ['Dweller', 'Walker', 'Born', 'Child', 'Guardian', 'Keeper', 'Seeker', 'Traveler', 'Builder', 'Destroyer']
        suffixes = ['Empire', 'Federation', 'Collective', 'Commonwealth', 'Dominion', 'Union', 'Alliance', 'Hegemony', 'Consensus', 'Network']

        if cultural.social_structure == 'collective_consciousness':
            return random.choice(['The Great Mind', 'The Unified Consciousness', 'The Collective', 'The Network'])
        elif cultural.communication_method == CommunicationMethod.TELEPATHIC:
            return f"The {random.choice(prefixes)} {random.choice(middles)}s"
        else:
            return f"The {random.choice(prefixes)} {random.choice(middles)} {random.choice(suffixes)}"

    def generate_species_name(self, physical: PhysicalCharacteristics) -> str:
        """Generate a species name"""

        # Biology-based name component
        biology_prefixes = {
            BiologyType.CARBON_BASED: ['Carbo', 'Orga', 'Vita', 'Bio'],
            BiologyType.SILICON_BASED: ['Silico', 'Crystal', 'Geode', 'Miner'],
            BiologyType.ENERGY_BASED: ['Lumi', 'Volta', 'Plasma', 'Quantum'],
            BiologyType.GASEOUS: ['Nebu', 'Gaso', 'Aero', 'Atmo'],
            BiologyType.CRYSTALLINE: ['Crysta', 'Shard', 'Gem', 'Prism']
        }

        prefixes = biology_prefixes.get(physical.biology_type, ['Xeno', 'Alien', 'Unknown'])
        prefix = random.choice(prefixes)

        # Body plan component
        body_suffixes = {
            BodyPlan.HUMANOID: ['nos', 'sapien', 'human', 'biped'],
            BodyPlan.AVIAN: ['avis', 'alatus', 'wing', 'sky'],
            BodyPlan.AQUATIC: ['aqua', 'mare', 'ocean', 'depth'],
            BodyPlan.INSECTOID: ['insecta', 'arachna', 'exo', 'chitin'],
            BodyPlan.REPTILIAN: ['saurus', 'reptil', 'scale', 'cold'],
            BodyPlan.FUNGAL: ['fungi', 'spora', 'myce', 'mold']
        }

        suffixes = body_suffixes.get(physical.body_plan, ['morph', 'form', 'being', 'creature'])
        suffix = random.choice(suffixes)

        return f"{prefix}{suffix}".title()

    def generate_language_name(self, physical: PhysicalCharacteristics,
                             communication: CommunicationMethod) -> str:
        """Generate a language name"""

        if communication == CommunicationMethod.TELEPATHIC:
            return "Thought-Speak"
        elif communication == CommunicationMethod.BIOLUMINESCENCE:
            return "Light-Language"
        elif communication == CommunicationMethod.CHEMICAL_SIGNALS:
            return "Scent-Speech"
        elif physical.body_plan == BodyPlan.INSECTOID:
            return "Chitter-Tongue"
        else:
            # Generate alien-sounding name
            syllables = ['xyl', 'zor', 'kree', 'vex', 'nax', 'quar', 'myth', 'syn']
            num_syllables = random.randint(2, 4)
            return ''.join(random.sample(syllables, num_syllables)).title() + 'ese'

# Example usage and testing
if __name__ == "__main__":
    # Create alien civilization generator
    generator = AlienCivilizationGenerator(seed=42)

    print("Alien Civilization Generator Initialized")
    print(f"Seed: {generator.seed}")

    # Generate sample civilizations for different planet types
    print("\n" + "="*50)
    print("GENERATING ALIEN CIVILIZATIONS")
    print("="*50)

    planet_types = [
        {
            'type': 'temperate_planet',
            'system_id': 'alpha_system',
            'planet_id': 'alpha_prime',
            'home_planet': {
                'type': 'temperate_planet',
                'gravity': 1.0,
                'temperature': 288,
                'atmosphere': {'N2': 0.78, 'O2': 0.21},
                'has_water': True,
                'hostility_level': 0.2
            }
        },
        {
            'type': 'desert_planet',
            'system_id': 'beta_system',
            'planet_id': 'beta_desert',
            'home_planet': {
                'type': 'desert_planet',
                'gravity': 1.2,
                'temperature': 350,
                'atmosphere': {'CO2': 0.95, 'N2': 0.05},
                'has_water': False,
                'hostility_level': 0.8
            }
        },
        {
            'type': 'ocean_planet',
            'system_id': 'gamma_system',
            'planet_id': 'gamma_ocean',
            'home_planet': {
                'type': 'ocean_planet',
                'gravity': 0.9,
                'temperature': 280,
                'atmosphere': {'N2': 0.7, 'O2': 0.3},
                'has_water': True,
                'hostility_level': 0.3
            }
        },
        {
            'type': 'gas_giant_moons',
            'system_id': 'delta_system',
            'planet_id': 'delta_moon',
            'home_planet': {
                'type': 'temperate_planet',
                'gravity': 0.7,
                'temperature': 200,
                'atmosphere': {'H2': 0.8, 'He': 0.2},
                'has_water': False,
                'hostility_level': 0.6
            }
        }
    ]

    civilizations = []

    for i, planet_data in enumerate(planet_types):
        print(f"\nGenerating Civilization {i+1}: {planet_data['type']}")

        civ = generator.generate_alien_civilization(planet_data, f"alien_civ_{i+1}")
        civilizations.append(civ)

        print(f"  Civilization Name: {civ.name}")
        print(f"  Species Name: {civ.species_name}")
        print(f"  Home System: {civ.home_system}")
        print(f"  Population: {civ.population:,}")
        print(f"  Age: {civ.age:,.0f} years")
        print(f"  Biology Type: {civ.physical_characteristics.biology_type.value}")
        print(f"  Body Plan: {civ.physical_characteristics.body_plan.value}")
        print(f"  Average Height: {civ.physical_characteristics.average_height:.2f} meters")
        print(f"  Average Mass: {civ.physical_characteristics.average_mass:.1f} kg")
        print(f"  Lifespan: {civ.physical_characteristics.lifespan:.0f} years")
        print(f"  Intelligence: {civ.physical_characteristics.intelligence_factor:.2f}")
        print(f"  Communication: {civ.cultural_characteristics.communication_method.value}")
        print(f"  Government: {civ.government_type.value}")
        print(f"  Tech Level: {civ.technological_level.overall_level:.2f}")
        print(f"  FTL Capability: {civ.technological_level.ftl_capability}")
        print(f"  Cultural Traits: {[trait.value for trait in list(civ.cultural_traits)[:4]]}")
        print(f"  Special Abilities: {civ.physical_characteristics.special_abilities[:3]}")
        print(f"  Threat Level: {civ.threat_level:.2f}")

    # Display detailed information about one civilization
    print("\n" + "="*50)
    print("DETAILED CIVILIZATION PROFILE")
    print("="*50)

    if civilizations:
        sample_civ = civilizations[0]
        print(f"\n{sample_civ.name} - Detailed Profile")
        print(f"Species: {sample_civ.species_name}")

        print(f"\nPhysical Characteristics:")
        print(f"  Biology: {sample_civ.physical_characteristics.biology_type.value}")
        print(f"  Body Plan: {sample_civ.physical_characteristics.body_plan.value}")
        print(f"  Height: {sample_civ.physical_characteristics.average_height:.2f}m")
        print(f"  Mass: {sample_civ.physical_characteristics.average_mass:.1f}kg")
        print(f"  Lifespan: {sample_civ.physical_characteristics.lifespan:.0f} years")
        print(f"  Intelligence: {sample_civ.physical_characteristics.intelligence_factor:.2f}")
        print(f"  Strength: {sample_civ.physical_characteristics.physical_strength:.2f}")
        print(f"  Speed: {sample_civ.physical_characteristics.speed_factor:.2f}")
        print(f"  Special Abilities: {', '.join(sample_civ.physical_characteristics.special_abilities)}")
        print(f"  Vulnerabilities: {', '.join(sample_civ.physical_characteristics.vulnerabilities)}")
        print(f"  Dietary Requirements: {', '.join(sample_civ.physical_characteristics.dietary_requirements)}")

        print(f"\nCultural Characteristics:")
        print(f"  Language: {sample_civ.cultural_characteristics.primary_language}")
        print(f"  Communication: {sample_civ.cultural_characteristics.communication_method.value}")
        print(f"  Social Structure: {sample_civ.cultural_characteristics.social_structure}")
        print(f"  Family Structure: {sample_civ.cultural_characteristics.family_structure}")
        print(f"  Art Forms: {', '.join(sample_civ.cultural_characteristics.art_forms)}")
        print(f"  Values: {', '.join(sample_civ.cultural_characteristics.values)}")
        print(f"  Taboos: {', '.join(sample_civ.cultural_characteristics.taboos)}")

        print(f"\nTechnological Level:")
        print(f"  Overall: {sample_civ.technological_level.overall_level:.2f}")
        print(f"  Specializations: {[spec.value for spec in sample_civ.technological_level.specializations]}")
        print(f"  Energy Production: {sample_civ.technological_level.energy_production:.2f}")
        print(f"  AI Level: {sample_civ.technological_level.artificial_intelligence_level:.2f}")
        print(f"  Biotechnology: {sample_civ.technological_level.biotechnology_level:.2f}")
        print(f"  Known Technologies: {', '.join(sample_civ.technological_level.known_technologies)}")

        print(f"\nPolitical Information:")
        print(f"  Government: {sample_civ.government_type.value}")
        print(f"  Cultural Traits: {[trait.value for trait in sample_civ.cultural_traits]}")
        print(f"  Foreign Policy: {sample_civ.foreign_policy}")
        print(f"  Galactic Reputation: {sample_civ.galactic_reputation:.2f}")
        print(f"  Resource Priorities: {dict(list(sample_civ.resource_priorities.items())[:4])}")

    print("\n" + "="*50)
    print("ALIEN DIVERSITY SUMMARY")
    print("="*50)

    biology_types = {}
    body_plans = {}
    governments = {}
    communication_methods = {}

    for civ in civilizations:
        # Biology types
        bio = civ.physical_characteristics.biology_type.value
        biology_types[bio] = biology_types.get(bio, 0) + 1

        # Body plans
        body = civ.physical_characteristics.body_plan.value
        body_plans[body] = body_plans.get(body, 0) + 1

        # Governments
        gov = civ.government_type.value
        governments[gov] = governments.get(gov, 0) + 1

        # Communication methods
        comm = civ.cultural_characteristics.communication_method.value
        communication_methods[comm] = communication_methods.get(comm, 0) + 1

    print(f"Biology Types Distribution:")
    for bio, count in biology_types.items():
        print(f"  {bio}: {count}")

    print(f"\nBody Plans Distribution:")
    for body, count in body_plans.items():
        print(f"  {body}: {count}")

    print(f"\nGovernment Types Distribution:")
    for gov, count in governments.items():
        print(f"  {gov}: {count}")

    print(f"\nCommunication Methods Distribution:")
    for comm, count in communication_methods.items():
        print(f"  {comm}: {count}")

    print("\nAlien Civilization Features:")
    print("- Procedurally generated species with diverse biology")
    print("- Unique body plans adapted to planetary conditions")
    print("- Cultural characteristics linked to physical traits")
    print("- Technological development influenced by environment")
    print("- Government types based on social structure")
    print("- Communication methods suited to biology")
    print("- Special abilities and vulnerabilities")
    print("- Resource priorities and foreign policies")
    print("- Threat assessment and galactic reputation")

    print("\nAlien civilizations system test completed successfully!")
    print(f"Generated {len(civilizations)} diverse alien civilizations with unique characteristics!")